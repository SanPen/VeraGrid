# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0


from __future__ import annotations

import time

import uuid

from typing import Tuple
import pandas as pd
import numpy as np
import numba as nb
from numba import float64
import math
import scipy.sparse as sp

from scipy.sparse import csr_matrix, csc_matrix, lil_matrix
from scipy.sparse.linalg import gmres, spilu, LinearOperator, spsolve, eigs
from matplotlib import pyplot as plt
from typing import Dict, List, Any, Callable, Sequence

from VeraGridEngine.Devices.Dynamic.events import RmsEvents
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Expr, Const, _emit, _emit_params_eq, _heaviside
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Sparse.csc import pack_4_by_4_scipy
from VeraGridEngine.basic_structures import Vec


def _fully_substitute(expr: Expr, mapping: Dict[Var, Expr], max_iter: int = 10) -> Expr:
    cur = expr
    for _ in range(max_iter):
        nxt = cur.subs(mapping).simplify()
        if str(nxt) == str(cur):  # no further change
            break
        cur = nxt
    return cur



def _compile_equations(eqs: Sequence[Expr],
                       uid2sym_vars: Dict[int, str],
                       uid2sym_params: Dict[int, str],
                       add_doc_string: bool = True) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
    """
    Compile the array of expressions to a function that returns an array of values for those expressions
    :param eqs: Iterable of expressions (Expr)
    :param uid2sym_vars: dictionary relating the uid of a var with its array name (i.e. var[0])
    :param uid2sym_params:
    :param add_doc_string: add the docstring?
    :return: Function pointer that returns an array
    """

    fname = f"func{uuid.uuid4().hex}"  # random name to avoid collissions

    # Build source
    # src = f"@nb.njit()\n"
    src = f"def {fname}(vars, params):\n"
    src += f"    out = np.zeros({len(eqs)})\n"
    src += "\n".join([f"    out[{i}] = {_emit(e, uid2sym_vars, uid2sym_params)}" for i, e in enumerate(eqs)]) + "\n"
    src += f"    return out"

    exec(src)
    compiled_func = locals()[fname]

    return compiled_func


def _compile_parameters_equations(eqs: Sequence[Expr],
                                  uid2sym_t: Dict[int, str],
                                  add_doc_string: bool = True) -> Callable[[float], np.ndarray]:
    """
    Compile the array of expressions to a function that returns an array of values for those expressions
    :param eqs: Iterable of expressions (Expr)
    :param uid2sym_t: dictionary relating the uid of a var with its array name (i.e. var[0])
    :param add_doc_string: add the docstring?
    :return: Function pointer that returns an array
    """
    fname = f"func{uuid.uuid4().hex}"  # random name to avoid collissions

    # Build source
    src = f"def {fname}(glob_time):\n"
    src += f"    out = np.zeros({len(eqs)})\n"
    src += "\n".join([f"    out[{i}] = {_emit_params_eq(e, uid2sym_t)}" for i, e in enumerate(eqs)]) + "\n"
    src += f"    return out"

    exec(src)
    compiled_func = locals()[fname]

    return compiled_func


class SymbolicJacobian:
    """
    Class to store and evaluate a symbolic jacobian
    """

    def __init__(self,
                 eqs: List[Expr],
                 variables: List[Var],
                 uid2sym_vars: Dict[int, str],
                 uid2sym_params: Dict[int, str],
                 use_jit: bool = True):
        """
        JIT‑compile a sparse Jacobian evaluator for *equations* w.r.t *variables*.
        :param eqs: Array of equations
        :param variables: Array of variables to differentiate against
        :param uid2sym_vars: dictionary relating the uid of a var with its array name (i.e. var[0])
        :param uid2sym_params:
        :param use_jit: if true, the function is compiled by numba
        :return:
                jac_fn : callable(values: np.ndarray, params: np.ndarray) -> scipy.sparse.csc_matrix
                    Fast evaluator in which *values* is a 1‑D NumPy vector of length
                    ``len(variables)``and *params* is a 1‑D NumPy vector of length
                    ``len(parameters)``
                sparsity_pattern : tuple(np.ndarray, np.ndarray)
                    Row/col indices of structurally non‑zero entries.
        """

        # compute the jacobian structure -------------------------------------------------------------------------------

        triplets: List[Tuple[int, int, Callable]] = list()  # (col, row, fn)

        for row, eq in enumerate(eqs):
            for col, var in enumerate(variables):

                fn = eq.diff(var).simplify()

                if isinstance(fn, Const) and fn.value == 0:
                    # structural zero
                    pass
                else:
                    triplets.append((col, row, fn))

        triplets.sort(key=lambda t: (t[0], t[1]))
        cols_sorted, rows_sorted, equations_sorted = zip(*triplets) if triplets else ([], [], [])

        # Assemble the jacobian structure
        nnz = len(cols_sorted)

        indices = np.fromiter(rows_sorted, dtype=np.int32, count=nnz)

        indptr = np.zeros(len(variables) + 1, dtype=np.int32)
        for c in cols_sorted:
            indptr[c + 1] += 1
        np.cumsum(indptr, out=indptr)

        self.nvar = len(variables)
        neq = len(eqs)

        self.J = sp.csc_matrix((np.zeros(nnz), indices, indptr), shape=(neq, self.nvar))

        # compilation --------------------------------------------------------------------------------------------------

        self.namespace: Dict[str, Any] = {
            "math": math,
            "np": np,
            "nb": nb,
            "_heaviside": _heaviside,
        }

        fname = f"jac"  # since we compile into a namespace, there won't be repeated names

        # Build source
        src = f"def {fname}(vars, params, out):\n"
        src += "\n".join([f"    out[{i}] = {_emit(e, uid2sym_vars, uid2sym_params)}"
                          for i, e in enumerate(equations_sorted)]) + "\n"

        # compile to python
        exec(src, self.namespace)

        if use_jit:
            # compile with numba
            self.func = nb.njit(nb.void(nb.float64[:], nb.float64[:], nb.float64[:]),
                                fastmath=True)(self.namespace[fname])
        else:
            # just pick the python pointer from the namespace
            self.func = self.namespace[fname]

    def __call__(self, values: Vec, params: Vec) -> csc_matrix:
        """
        Update the jacobian data
        :param values:
        :param params:
        :return: Updated jacobian structure
        """
        assert len(values) >= self.nvar

        # note: J.data is passed into the function and gets filled. This way we avoid new memory allocation
        self.func(values, params, self.J.data)

        return self.J


class SymbolicVector:
    """
    SymbolicFunction
    """

    def __init__(self, eqs: Sequence[Expr],
                 uid2sym_vars: Dict[int, str],
                 uid2sym_params: Dict[int, str],
                 use_jit: bool = True):
        """
        Compile the array of expressions to a function that returns an array of values for those expressions
        :param eqs: Iterable of expressions (Expr)
        :param uid2sym_vars: dictionary relating the uid of a var with its array name (i.e. var[0])
        :param uid2sym_params:
        :return: Function pointer that returns an array
        """
        if len(eqs):
            self.namespace: Dict[str, Any] = {
                "math": math,
                "np": np,
                "nb": nb,
                "_heaviside": _heaviside,
            }

            fname = f"func"  # since we compile into a namespace, there won't be repeated names

            # Build source
            src = f"def {fname}(vars, params, out):\n"
            src += "\n".join([f"    out[{i}] = {_emit(e, uid2sym_vars, uid2sym_params)}" for i, e in enumerate(eqs)]) + "\n"

            # compile in python namespace
            exec(src, self.namespace)

            # compile in numba
            if use_jit:
                self.func = nb.njit(nb.void(nb.float64[:], nb.float64[:], nb.float64[:]),
                                    fastmath=True)(self.namespace[fname])
            else:
                self.func = self.namespace[fname]
        else:
            self.func = None

        self.data = np.zeros(len(eqs))

    def __call__(self, values: Vec, params: Vec) -> Vec:
        """
        Call the compiled function
        :param values:
        :param params:
        :return:
        """
        if self.func is not None:
            self.func(values, params, self.data)
        return self.data


class SymbolicParamsVector:
    """
    SymbolicFunction
    """

    def __init__(self, eqs: Sequence[Expr],
                 uid2sym_t: Dict[int, str],
                 use_jit: bool = True):
        """
        Compile the array of expressions to a function that returns an array of values for those expressions
        :param eqs: Iterable of expressions (Expr)
        :param uid2sym_t: dictionary relating the uid of a var with its array name (i.e. var[0])
        :return: Function pointer that returns an array
        """
        if len(eqs):
            self.namespace: Dict[str, Any] = {
                "math": math,
                "np": np,
                "nb": nb,
                "_heaviside": _heaviside,
            }

            fname = f"func"  # since we compile into a namespace, there won't be repeated names

            # Build source
            src = f"def {fname}(glob_time, out):\n"
            src += "\n".join([f"    out[{i}] = {_emit_params_eq(e, uid2sym_t)}" for i, e in enumerate(eqs)]) + "\n"

            # compile in python namespace
            exec(src, self.namespace)

            # compile in numba
            if use_jit:
                self.func = nb.njit(nb.void(nb.float64, nb.float64[:]),
                                    fastmath=True)(self.namespace[fname])
            else:
                self.func = self.namespace[fname]
        else:
            self.func = None

        self.data = np.zeros(len(eqs))

    def __call__(self, glob_time: float) -> Vec:
        """
        Call the compiled function
        :param glob_time:
        :return:
        """
        if self.func is not None:
            self.func(glob_time, self.data)
        return self.data


class BlockSolver:
    """
    A network of Blocks that behaves roughly like a Simulink diagram.
    """

    def __init__(self, block_system: Block,
                 glob_time: Var,
                 use_jit: bool = True):
        """
        Constructor
        :param block_system:  BlockSystem
        :param glob_time:
        :param use_jit: if true, the functions are compiled with numba
        """
        self.block_system: Block = block_system
        # TODO: uids, system vars,.. have been already processed in block_system and can be retrived from there.
        # Flatten the block lists, preserving declaration order
        self._algebraic_vars: List[Var] = list()
        self._algebraic_eqs: List[Expr] = list()
        self._state_vars: List[Var] = list()
        self._state_eqs: List[Expr] = list()
        self._event_parameters: List[Var] = list()
        self._event_parameters_eqs: List[Expr] = list()
        self.glob_time: Var = glob_time
        self.vars2device = block_system.vars2device
        self.v_glob_name2uid = block_system.vars_glob_name2uid

        for b in self.block_system.get_all_blocks():
            self._algebraic_vars.extend(b.algebraic_vars)
            self._algebraic_eqs.extend(b.algebraic_eqs)
            self._state_vars.extend(b.state_vars)
            self._state_eqs.extend(b.state_eqs)
            for param, eq in b.event_dict.items():
                self._event_parameters.append(param)
                self._event_parameters_eqs.append(eq)


        self._n_state = len(self._state_vars)
        self._n_alg = len(self._algebraic_vars)
        self._n_vars = self._n_state + self._n_alg
        self._n_event_params = len(self._event_parameters)

        # generate the in-code names for each variable
        # inside the compiled functions the variables are
        # going to be represented by an array called vars[]

        uid2sym_vars: Dict[int, str] = dict()
        uid2sym_event_params: Dict[int, str] = dict()
        uid2sym_t: Dict[int, str] = dict()
        self.uid2var: Dict[int, Var] = dict()
        self.uid2idx_vars: Dict[int, int] = dict()
        self.uid2idx_event_params: Dict[int, int] = dict()
        self.uid2idx_t: Dict[int, int] = dict()
        i = 0
        for v in self._state_vars:
            uid2sym_vars[v.uid] = f"vars[{i}]"
            self.uid2var[v.uid] = v
            self.uid2idx_vars[v.uid] = i
            i += 1

        for v in self._algebraic_vars:
            uid2sym_vars[v.uid] = f"vars[{i}]"
            self.uid2var[v.uid] = v
            self.uid2idx_vars[v.uid] = i

            i += 1

        j = 0
        for j, ep in enumerate(self._event_parameters):
            uid2sym_event_params[ep.uid] = f"params[{j}]"
            self.uid2idx_event_params[ep.uid] = j
            j += 1

        k = 0
        uid2sym_t[self.glob_time.uid] = f"glob_time"
        self.uid2idx_t[self.glob_time.uid] = k

        # Ensure deterministic variable order
        for variables in (self._state_vars, self._algebraic_vars):
            check_set = set()
            for v in variables:
                if v in check_set:
                    raise ValueError(f"Repeated var {v.name} in the variables' list :(")
                else:
                    check_set.add(v)

        # Compile RHS and Jacobian
        """
                   state Var   algeb var  
        state eq |J11        | J12       |    | ∆ state var|    | ∆ state eq |
                 |           |           |    |            |    |            |
                 ------------------------- x  |------------|  = |------------|
        algeb eq |J21        | J22       |    | ∆ algeb var|    | ∆ algeb eq |
                 |           |           |    |            |    |            |
        """
        start_compiling = time.time()
        print("Compiling...", end="")

        self._rhs_state_fn = SymbolicVector(eqs=self._state_eqs,
                                            uid2sym_vars=uid2sym_vars,
                                            uid2sym_params=uid2sym_event_params,
                                            use_jit=use_jit)

        self._rhs_algeb_fn = SymbolicVector(eqs=self._algebraic_eqs,
                                            uid2sym_vars=uid2sym_vars,
                                            uid2sym_params=uid2sym_event_params,
                                            use_jit=use_jit)

        self._params_fn = SymbolicParamsVector(eqs=self._event_parameters_eqs,
                                               uid2sym_t=uid2sym_t)

        self._j11_fn = SymbolicJacobian(eqs=self._state_eqs,
                                        variables=self._state_vars,
                                        uid2sym_vars=uid2sym_vars,
                                        uid2sym_params=uid2sym_event_params,
                                        use_jit=use_jit)

        self._j12_fn = SymbolicJacobian(eqs=self._state_eqs,
                                        variables=self._algebraic_vars,
                                        uid2sym_vars=uid2sym_vars,
                                        uid2sym_params=uid2sym_event_params,
                                        use_jit=use_jit)

        self._j21_fn = SymbolicJacobian(eqs=self._algebraic_eqs,
                                        variables=self._state_vars,
                                        uid2sym_vars=uid2sym_vars,
                                        uid2sym_params=uid2sym_event_params,
                                        use_jit=use_jit)

        self._j22_fn = SymbolicJacobian(eqs=self._algebraic_eqs,
                                        variables=self._algebraic_vars,
                                        uid2sym_vars=uid2sym_vars,
                                        uid2sym_params=uid2sym_event_params,
                                        use_jit=use_jit)

        print("done!")
        end_compiling = time.time()
        compilation_time = end_compiling - start_compiling
        print(f"all compilation time = {compilation_time:.6f} [s]")

    @property
    def params_fn(self) -> SymbolicParamsVector:
        """
        state eq / state var jacobian
        :return: SymbolicJacobian
        """
        return self._params_fn

    @property
    def j11(self) -> SymbolicJacobian:
        """
        state eq / state var jacobian
        :return: SymbolicJacobian
        """
        return self._j11_fn

    @property
    def j12(self) -> SymbolicJacobian:
        """
        state eq / algeb var
        :return: SymbolicJacobian
        """
        return self._j12_fn

    @property
    def j21(self) -> SymbolicJacobian:
        """
        algeb eq / state Var
        :return:  SymbolicJacobian
        """
        return self._j21_fn

    @property
    def j22(self) -> SymbolicJacobian:
        """
        algeb eq / algeb Var
        :return: SymbolicJacobian
        """
        return self._j22_fn

    @property
    def state_vars(self) -> List[Var]:
        """
        Get the state vars
        :return: List[Var]
        """
        return self._state_vars

    def get_var_idx(self, v: Var) -> int:
        """

        :param v:
        :return:
        """
        return self.uid2idx_vars[v.uid]

    def get_vars_idx(self, variables: Sequence[Var]) -> np.ndarray:
        """

        :param variables:
        :return:
        """
        return np.array([self.uid2idx_vars[v.uid] for v in variables])

    def sort_vars(self, mapping: dict[Var, float]) -> np.ndarray:
        """
        Helper function to build the initial vector
        :param mapping: var->initial value mapping
        :return: array matching with the mapping, matching the solver ordering
        """
        x = np.zeros(len(self._state_vars) + len(self._algebraic_vars), dtype=object)

        for key, val in mapping.items():
            i = self.uid2idx_vars[key.uid]
            x[i] = key

        return x

    def sort_vars_from_uid(self, mapping: dict[tuple[int, str], float]) -> np.ndarray:
        """
        Helper function to build the initial vector
        :param mapping: var->initial value mapping
        :return: array matching with the mapping, matching the solver ordering
        """
        x = np.zeros(len(self._state_vars) + len(self._algebraic_vars), dtype=object)

        for key, val in mapping.items():
            uid, name = key
            i = self.uid2idx_vars[uid]
            x[i] = uid

        return x

    def build_init_vars_vector(self, mapping: dict[Var, float]) -> np.ndarray:
        """
        Helper function to build the initial vector
        :param mapping: var->initial value mapping
        :return: array matching with the mapping, matching the solver ordering
        """
        x = np.zeros(len(self._state_vars) + len(self._algebraic_vars))

        for key, val in mapping.items():
            if key.uid in self.uid2idx_vars.keys():
                i = self.uid2idx_vars[key.uid]
                x[i] = val
            else:
                raise ValueError(f"Missing variable {key} definition")

        return x

    def build_init_vars_vector_from_uid(self, mapping: dict[tuple[int, str], float]) -> np.ndarray:
        """
        Helper function to build the initial vector
        :param mapping: var->initial value mapping
        :return: array matching with the mapping, matching the solver ordering
        """
        x = np.zeros(len(self._state_vars) + len(self._algebraic_vars))

        for key, val in mapping.items():
            uid, name = key
            if uid in self.uid2idx_vars.keys():
                i = self.uid2idx_vars[uid]
                x[i] = val
            else:
                raise ValueError(f"Missing uid {key} definition")

        return x

    def build_init_params_vector(self, mapping: dict[Var, float]) -> np.ndarray:
        """
        Helper function to build the initial vector
        :param mapping: var->initial value mapping
        :return: array matching with the mapping, matching the solver ordering
        """
        x = np.zeros(self._n_event_params)

        for key, val in mapping.items():
            i = self.uid2idx_event_params[key.uid]

            x[i] = val

        return x

    def rhs_fixed(self, x: Vec, params: Vec) -> np.ndarray:
        """
        Return 𝑑x/dt given the current *state* vector.
        :param x: get the right-hand-side give a state vector
        :return [f_state_update, f_algeb]
        """
        f_algeb = np.array(self._rhs_algeb_fn(x, params))

        if self._n_state > 0:
            f_state = np.array(self._rhs_state_fn(x, params))
            return np.r_[f_state, f_algeb]
        else:
            return f_algeb

    def rhs_implicit(self, x: Vec, xn: Vec, params: Vec, sim_step, h: float) -> np.ndarray:
        """
        Return 𝑑x/dt given the current *state* vector.
        :param x: get the right-hand-side give a state vector
        :param xn:
        :param params: params array
        :param sim_step: simulation step
        :param h: simulation step
        :return [f_state_update, f_algeb]
        """
        f_algeb = np.array(self._rhs_algeb_fn(x, params))

        if self._n_state > 0:
            f_state = np.array(self._rhs_state_fn(x, params))
            f_state_update = x[:self._n_state] - xn[:self._n_state] - h * f_state
            return np.r_[f_state_update, f_algeb]

        else:
            return f_algeb

    def jacobian_implicit(self, x: np.ndarray, params: np.ndarray, h: float) -> csc_matrix:
        """
        :param x: vector or variables' values
        :param params: params array
        :param h: step
        :return:
        """

        """
                  state Var    algeb var
        state eq |I - h * J11 | - h* J12  |    | ∆ state var|    | ∆ state eq |
                 |            |           |    |            |    |            |
                 -------------------------- x  |------------|  = |------------|
        algeb eq |J21         | J22       |    | ∆ algeb var|    | ∆ algeb eq |
                 |            |           |    |            |    |            |
        """

        j11_val: csc_matrix = self._j11_fn(x, params)
        j12_val: csc_matrix = self._j12_fn(x, params)
        j21_val: csc_matrix = self._j21_fn(x, params)
        j22_val: csc_matrix = self._j22_fn(x, params)

        I = sp.eye(m=self._n_state, n=self._n_state)
        j11: sp.csc_matrix = (I - h * j11_val).tocsc()
        j12: sp.csc_matrix = - h * j12_val
        j21: sp.csc_matrix = j21_val
        j22: sp.csc_matrix = j22_val

        J = pack_4_by_4_scipy(j11, j12, j21, j22)

        return J

    def residual_init(self, z: np.ndarray, params: np.ndarray):
        """

        :param z:
        :param params:
        :return:
        """
        # concatenate state & algebraic residuals
        f_s = np.array(self._rhs_state_fn(z, params))  # f_state(x)        == 0 at t=0
        f_a = np.array(self._rhs_algeb_fn(z, params))  # g_algeb(x, y)     == 0
        return np.r_[f_s, f_a]

    def jacobian_init(self, z: np.ndarray, params: np.ndarray):
        """

        :param z:
        :param params:
        :return:
        """
        J11 = self._j11_fn(z, params)  # ∂f_state/∂x
        J12 = self._j12_fn(z, params)  # ∂f_state/∂y
        J21 = self._j21_fn(z, params)  # ∂g/∂x
        J22 = self._j22_fn(z, params)  # ∂g/∂y
        return pack_4_by_4_scipy(J11, J12, J21, J22)  # → sparse 2×2 block Jacobian

    def equations(self) -> Tuple[List[Expr], List[Expr]]:
        """
        Return (algebraic_eqs, state_eqs) as *originally declared* (no substitution).
        """
        return self._algebraic_eqs, self._state_eqs

    def simulate(
            self,
            t0: float,
            t_end: float,
            h: float,
            x0: np.ndarray,
            params0: np.ndarray,
            method: str,
            newton_tol: float = 1e-8,
            newton_max_iter: int = 1000,

    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        :param params0:
        :param t0: start time
        :param t_end: end time
        :param h: step
        :param x0: initial values
        :param method: method
        :param newton_tol:
        :param newton_max_iter:
        :return: 1D time array, 2D array of simulated variables
        """
        if method == "euler":
            return self._simulate_fixed(t0, t_end, h, x0, params0, stepper="euler")
        if method == "rk4":
            return self._simulate_fixed(t0, t_end, h, x0, params0, stepper="rk4")
        if method == "implicit_euler":
            return self._simulate_implicit_euler(
                t0=t0, t_end=t_end, h=h, x0=x0, params0=params0,
                tol=newton_tol, max_iter=newton_max_iter,
            )
        raise ValueError(f"Unknown method '{method}'")

    def _simulate_fixed(self, t0, t_end, h, x0, params, stepper="euler"):
        """
        Fixed‑step helpers (Euler, RK‑4)
        :param t0:
        :param t_end:
        :param h:
        :param x0:
        :param stepper:
        :return:
        """
        steps = int(np.ceil((t_end - t0) / h))
        t = np.empty(steps + 1)
        y = np.empty((steps + 1, self._n_vars))
        t[0] = t0
        y[0, :] = x0.copy()

        for i in range(steps):
            tn = t[i]
            xn = y[i]
            if stepper == "euler":
                k1 = self.rhs_fixed(xn, params)
                y[i + 1] = xn + h * k1
            elif stepper == "rk4":
                k1 = self.rhs_fixed(xn, params)
                k2 = self.rhs_fixed(xn + 0.5 * h * k1, params)
                k3 = self.rhs_fixed(xn + 0.5 * h * k2, params)
                k4 = self.rhs_fixed(xn + h * k3, params)
                y[i + 1] = xn + (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
            else:
                raise RuntimeError("unknown stepper")
            t[i + 1] = tn + h
        return t, y

    def _simulate_implicit_euler(self, t0: float, t_end: float, h: float,
                                 x0: np.ndarray,
                                 params0: np.ndarray,
                                 tol=1e-6,
                                 max_iter=1000):
        """
        :param t0:
        :param t_end:
        :param h:
        :param x0:
        :params_matrix:
        :param tol:
        :param max_iter:
        :return:
        """
        # pr = profile.Profile()
        # pr.enable()

        steps = int(np.ceil((t_end - t0) / h))
        t = np.empty(steps + 1)
        y = np.empty((steps + 1, self._n_vars))
        t[0] = t0
        y[0] = x0.copy()
        jacobian_time = 0
        functions_time = 0
        params_time = 0
        residual_time = 0
        solv_time = 0

        for step_idx in range(steps):
            xn = y[step_idx]
            x_new = xn.copy()  # initial guess
            converged = False
            n_iter = 0
            current_time = t[step_idx]

            start_params_calculation = time.time()
            params_current = self._params_fn(float(current_time))
            end_params_calculation = time.time()
            params_calculation_time = end_params_calculation - start_params_calculation
            params_time += params_calculation_time

            while not converged and n_iter < max_iter:

                start_functions_calc = time.time()
                rhs = self.rhs_implicit(x_new, xn, params_current, step_idx, h)
                end_functions_calc = time.time()
                calc_functions_time = end_functions_calc - start_functions_calc
                functions_time += calc_functions_time

                start_residual_calc = time.time()
                residual = np.linalg.norm(rhs, np.inf)
                end_residual_calc = time.time()
                calc_residual_time = end_residual_calc - start_residual_calc
                residual_time += calc_residual_time

                converged = residual < tol

                if step_idx == 0:
                    if converged:
                        print("System well initailzed.")
                    else:
                        print(f"System bad initilaized. DAE resiudal is {residual}.")

                if converged:
                    break

                start_jac_calc = time.time()
                Jf = self.jacobian_implicit(x_new, params_current, h)  # sparse matrix
                end_jac_calc = time.time()
                calc_jac_time = end_jac_calc - start_jac_calc
                jacobian_time += calc_jac_time

                start_solv = time.time()
                delta = sp.linalg.spsolve(Jf, -rhs)
                end_solv = time.time()
                solv_time += end_solv - start_solv

                x_new += delta
                n_iter += 1

            if converged:

                y[step_idx + 1] = x_new
                t[step_idx + 1] = t[step_idx] + h

            else:
                print(f"Failed to converge at step {step_idx}")
                break

        print(f"jacobian_total_time = {jacobian_time:.6f} [s]")

        print(f"functions_total_time = {functions_time:.6f} [s]")
        print(f"params_total_time = {params_time:.6f} [s]")
        print(f"residual_total_time = {residual_time:.6f} [s]")
        print(f"solv_time = {solv_time:.6f} [s]")

        # pr.disable()
        # pr.dump_stats('implicit_euler.pstat')

        return t, y

    def save_simulation_to_csv(self, filename, t, y, csv_saving=False):
        """
        Save the simulation results to a CSV file.

        Parameters:
        ----------
        filename : str
            The path and name of the CSV file to save.
        t : np.ndarray
            Time vector.
        y : np.ndarray
            Simulation results array (rows: time steps, columns: variable values).

        Returns:
        -------
        None
        """
        # Combine state and algebraic variables
        all_vars = self._state_vars + self._algebraic_vars
        var_names = [str(var) + '_VeraGrid' for var in all_vars]

        # Create DataFrame with time and variable data
        df_simulation_results = pd.DataFrame(data=y, columns=var_names)
        df_simulation_results.insert(0, 'Time [s]', t)

        if csv_saving:
            df_simulation_results.to_csv(filename, index=False)
            print(f"Simulation results saved to: {filename}")
        return df_simulation_results

