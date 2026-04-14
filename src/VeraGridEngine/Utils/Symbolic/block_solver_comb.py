# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import pdb

import numpy as np
import uuid
import numba as nb
import math
import scipy.sparse as sp
import time
import matplotlib.pyplot as plt
from typing import Optional

from scipy.sparse import csr_matrix, csc_matrix, lil_matrix

from VeraGridEngine.Devices.Dynamic.events import RmsEvents
from VeraGridEngine.Devices import MultiCircuit
from VeraGridEngine.Utils.Symbolic.block import Block, DiffBlock
from VeraGridEngine.Utils.Symbolic.block_solver import BlockSolver, _compile_parameters_equations, _compile_equations
from VeraGridEngine.Utils.Symbolic.symbolic import Var, LagVar, DiffVar, Const, Expr, Func, cos, sin, _emit, _heaviside, _emit_params_eq
from VeraGridEngine.enumerations import VarPowerFlowRefferenceType

from dataclasses import dataclass, field
from typing import Any, Callable, ClassVar, Dict, Mapping, Union, List, Sequence, Tuple, Set, Literal
from scipy.sparse.linalg import gmres, spilu, LinearOperator, MatrixRankWarning
from VeraGridEngine.Utils.Sparse.csc import pack_4_by_4_scipy
from VeraGridEngine.basic_structures import Vec


NUMBER = Union[int, float]
NAME = 'name'


# -----------------------------------------------------------------------------
# UUID helper
# -----------------------------------------------------------------------------

class SymbolicJacobian:
    """
    Class to store and evaluate a symbolic jacobian
    """

    def __init__(self,
                 eqs: List[Expr],
                 variables: List[Var],
                 diff_variables: List[DiffVar],
                 lag_variables: List[LagVar],
                 lag_vars_set,
                 uid2sym_vars: Dict[int, str],
                 uid2sym_params: Dict[int, str],
                 uid2idx_vars,
                 uid2idx_lag,
                 dt: Const = Const(0.001),
                 delta: Const = Const(1),
                 substitute: bool = True,
                 use_jit: bool = True,
                 add_delta: bool = True):

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

        if not substitute:
            _ = 0
            # diff_vars = []
        ## check if there are repeated variables, this is done befor in block solver
        check_set = set()
        for v in variables:
            if v in check_set:
                raise ValueError(f"Repeated var {v.name} in the variables' list :(")
            else:
                check_set.add(v)
        ############################################################################

        triplets: List[Tuple[int, int, Callable]] = []  # (col, row, fn)

        for row, eq in enumerate(eqs):
            # substitude lag_var for lag_var.base_var
            for lag_var in lag_variables:
                if lag_var.lag == 0:
                    eq = eq.subs({lag_var: lag_var.base_var})

            for col, var in enumerate(variables):

                d_expression = eq.diff(var).simplify()

                # We substitute the remaining diff vars in d_expression
                for diff_var in diff_variables:
                    deriv = d_expression.diff(diff_var)
                    if getattr(deriv, 'value', 1) != 0:
                        if not substitute:
                            d_expression = d_expression.subs({diff_var: diff_var / delta})
                        else:
                            dx_dt, lag = diff_var.approximation_expr(dt=dt, lag_can_be_0=False)
                            d_expression = d_expression.subs({diff_var: dx_dt / delta})
                            new_lag = LagVar.get_or_create(diff_var.origin_var.name + '_lag_' + str(lag),
                                                           base_var=diff_var.origin_var, lag=lag)
                            ## add new lag
                            i = len(uid2idx_vars)
                            l = len(uid2idx_lag)
                            if new_lag not in lag_vars_set:
                                uid2sym_vars[new_lag.uid] = f"vars[{i}]"
                                uid2idx_vars[new_lag.uid] = i
                                uid2idx_lag[new_lag.uid] = l
                                lag_variables.append(new_lag)
                                lag_vars_set.add(new_lag)
                                i += 1
                                l += 1

                if isinstance(d_expression, Const) and d_expression.value == 0:
                    continue  # structural zero

                triplets.append((col, row, d_expression))
                if not substitute:
                    _ = 0
        # Sort by column, then row for CSC layout
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
        # assert len(values) >= self.nvar

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

    def __call__(self, glob_time: Vec) -> Vec:
        """
        Call the compiled function
        :param glob_time:
        :return:
        """
        if self.func is not None:
            self.func(glob_time, self.data)
        return self.data



def _new_uid() -> int:
    """Generate a fresh UUID‑v4 string."""
    return uuid.uuid4().int


def find_name_in_block(name: str, block: Block):
    for var in block.algebraic_vars + block.state_vars:
        if name == var.name:
            return var

    for block_child in block.children:
        result = find_name_in_block(name, block_child)
        if result is not None:  # found in a child
            return result

    return None


def pack_blocks_scipy(blocks: dict, n_batches: int):
    """
    Pack an n_batches x n_batches dict of sparse submatrices into one big csc_matrix.
    blocks[(i,j)] = submatrix
    """
    # row blocks per i
    row_blocks = []
    # print(blocks.keys())
    for i in range(n_batches):
        col_blocks = [blocks[i, j] for j in range(n_batches)]
        row_blocks.append(sp.hstack(col_blocks, format="csc"))
    return sp.vstack(row_blocks, format="csc")


def delete_vars_from_block(block: Block, deleted_vars: List[Var]):
    deleted_vars_uid = set(var.uid for var in deleted_vars)
    for b in block.get_all_blocks():
        algebraic_vars_copy = b.algebraic_vars.copy()
        b.algebraic_vars = []
        for var in algebraic_vars_copy:
            if var.uid not in deleted_vars_uid:
                b.algebraic_vars.append(var)
            else:
                # print(f'Deleting var {var.name} from block {b.name}')
                _ = 0


class SolverError(Exception):
    """Base class for all solver-related errors."""
    pass


class ConvergenceError(SolverError):
    """Raised when solver fails to converge within max iterations."""
    pass


class SingularJacobianError(SolverError):
    """Raised when Jacobian is singular or ill-conditioned."""
    pass


class NaNError(SolverError):
    """Raised when NaNs or Infs appear in the solution."""
    pass

class DiffBlockSolver(BlockSolver):

    def __init__(self, block_system: Block | DiffBlock, glob_time: Var, use_jit: bool = True):
        """
        Constructor
        :param block_system: BlockSystem
        """
        self.block_system: Block | DiffBlock = block_system

        # Flatten the block lists, preserving declaration order
        self._algebraic_vars: List[Var] = list()
        self._algebraic_eqs: List[Expr] = list()
        self._algebraic_eqs_substituted: List[Expr] = list()
        self._state_vars: List[Var] = list()
        self._state_eqs: List[Expr] = list()
        self._state_eqs_substituted: List[Expr] = list()
        self._diff_vars: List[DiffVar] = list()
        self._differential_eqs: List[Expr] = list()
        self._lag_vars: List[LagVar] = list()
        self._lag_vars_set: Set[LagVar] = set()
        self._reformulated_vars: List[Var] = list()
        self._parameters: List[Var] = list()
        self._parameters_eqs: List[Expr] = list()
        self._stability_eqs: List[Expr] = list()

        self.glob_time: Var = glob_time
        self.substitute = True

        for b in self.block_system.get_all_blocks():
            self._algebraic_vars.extend(b.algebraic_vars)
            self._algebraic_eqs.extend(b.algebraic_eqs)
            self._state_vars.extend(b.state_vars)
            self._state_eqs.extend(b.state_eqs)
            for param, eq in b.event_dict.items():
                self._parameters.extend([param])
                self._parameters_eqs.extend([eq])

            if isinstance(b, DiffBlock):
                self._diff_vars.extend(b.diff_vars)
                self._lag_vars.extend(b.lag_vars)
                self._differential_eqs.extend(b.differential_eqs)
                self._reformulated_vars.extend(b.reformulated_vars)

        self._lag_vars_set = set(self._lag_vars)
        self._state_eqs_substituted = self._state_eqs.copy()

        # We define the parameter dt and delta
        self.dt = Var(name='dt')
        self.delta = Var(name='delta')
        self._parameters.append(self.dt)
        self._parameters.append(self.delta)
        self._parameters_eqs.append(Const(1e-3))
        self._parameters_eqs.append(Const(1))

        self._n_state = len(self._state_vars)
        self._n_alg = len(self._algebraic_vars)
        self._n_vars = self._n_state + self._n_alg
        self._n_params = len(self._parameters)
        self._n_diff = len(self._diff_vars)
        n_algebraic = len(self._algebraic_eqs)

        # generate the in-code names for each variable
        # inside the compiled functions the variables are
        # going to be represented by an array called vars[]

        self.uid2sym_vars: Dict[int, str] = dict()
        self.uid2sym_params: Dict[int, str] = dict()
        self.uid2sym_diff: Dict[int, str] = dict()
        self.uid2sym_t: Dict[int, str] = dict()
        self.uid2idx_vars: Dict[int, int] = dict()
        self.uid2idx_params: Dict[int, int] = dict()
        self.uid2idx_diff: Dict[int, int] = dict()
        self.uid2idx_lag: Dict[int, int] = dict()
        self.uid2idx_t: Dict[int, int] = dict()

        i = 0
        for v in self._state_vars:
            self.uid2sym_vars[v.uid] = f"vars[{i}]"
            self.uid2idx_vars[v.uid] = i
            i += 1

        for v in self._algebraic_vars:
            self.uid2sym_vars[v.uid] = f"vars[{i}]"
            self.uid2idx_vars[v.uid] = i
            i += 1

        j = 0
        for j, ep in enumerate(self._parameters):
            self.uid2sym_params[ep.uid] = f"params[{j}]"
            self.uid2idx_params[ep.uid] = j
            j += 1

        k = 0
        for ep in self._diff_vars:
            self.uid2sym_diff[ep.uid] = f"diff[{k}]"
            self.uid2idx_diff[ep.uid] = k
            k += 1

        k = 0
        self.uid2sym_t[self.glob_time.uid] = f"glob_time"
        self.uid2idx_t[self.glob_time.uid] = k

        # We substitute the differential variable by the Forward Approximation:

        ## define parameters
        self.alpha = 1
        alpha = self.alpha
        lag_can_be_0 = False  # TODO: will this allways be False??
        if lag_can_be_0:
            lag_init = 0
        else:
            lag_init = 1

        ## Substitute in state eqs
            ## vars
        for iter, eq in enumerate(self._state_eqs_substituted):
            for var in self._algebraic_vars + self._state_vars:
                if not self.substitute:
                    continue
                deriv = eq.diff(var)
                if getattr(deriv, 'value', 1) == 0:
                    continue
                lag_var = LagVar.get_or_create(var.name + '_lag_' + str(1),
                                               base_var=var, lag=1)
                approximation = alpha * var + (1 - alpha) * lag_var
                self._lag_vars_set.add(lag_var)
                eq = eq.subs({var: approximation})
            self._state_eqs_substituted[iter] = eq
            ## find vars
        for iter, eq in enumerate(self._state_eqs_substituted):
            for var in self._diff_vars:
                deriv = eq.diff(var)
                if getattr(deriv, 'value', 1) == 0:
                    continue
                approximation, total_lag = var.approximation_expr(self.dt, lag_can_be_0=lag_can_be_0)
                eq = eq.subs({var: approximation})
                self._lag_vars_set.update(LagVar.get_or_create(var.origin_var.name + '_lag_' + str(lag),
                                                               base_var=var.origin_var, lag=lag) for lag in
                                          range(lag_init, max(2, total_lag + 1)))
            self._state_eqs_substituted[iter] = eq

        ## Substitute in algebraic eqs

        self._stability_eqs = []
        self._algebraic_eqs_substituted = self._algebraic_eqs.copy() + self._differential_eqs.copy()
        for iter, eq in enumerate(self._algebraic_eqs_substituted):

            ## vars
            for var in self._algebraic_vars + self._state_vars:
                if not self.substitute:
                    continue
                deriv = eq.diff(var)
                if getattr(deriv, 'value', 1) == 0:
                    continue
                if var not in self._reformulated_vars:
                    continue
                lag_var_0 = LagVar.get_or_create(var.name + '_lag_' + str(0),
                                                 base_var=var, lag=0)
                lag_var = LagVar.get_or_create(var.name + '_lag_' + str(1),
                                               base_var=var, lag=1)
                if iter < n_algebraic:
                    approximation = alpha * var + (1 - alpha) * lag_var
                else:
                    alpha2 = 0.5
                    approximation = alpha2 * var + (1 - alpha2) * lag_var
                self._lag_vars_set.add(lag_var)
                self._lag_vars_set.add(lag_var_0)
                eq = eq.subs({var: approximation})

            ## diff vars
            for var in self._diff_vars:
                deriv = eq.diff(var)
                if getattr(deriv, 'value', 1) == 0:
                    _ = 0
                    # continue
                approximation, total_lag = var.approximation_expr(self.dt, lag_can_be_0=lag_can_be_0, central=False)
                eq = eq.subs({var: approximation / self.delta})
                self._lag_vars_set.update(LagVar.get_or_create(var.origin_var.name + '_lag_' + str(lag),
                                                               base_var=var.origin_var, lag=lag) for lag in
                                          range(lag_init, total_lag + 1))
            self._algebraic_eqs_substituted[iter] = eq

        # fill stability equations by putting algebraic equations equal zero
        for iter, eq in enumerate(self._algebraic_eqs):
            for diff_var in self._diff_vars:
                eq = eq.subs({diff_var: Const(0)})
                eq = eq.simplify()
            self._stability_eqs.append(eq)

        i = len(self.uid2idx_vars)
        l = 0
        #create dict for lag vars
        self._lag_vars = sorted(self._lag_vars_set, key=lambda x: (x.base_var.uid, x.lag))
        for v in self._lag_vars:  # deterministic
            self.uid2sym_vars[v.uid] = f"vars[{i}]"
            self.uid2idx_vars[v.uid] = i
            self.uid2idx_lag[v.uid] = l
            i += 1
            l += 1

        # Compile RHS and Jacobian

        """
                   state Var   algeb var  
        state eq |J11        | J12       |    | ∆ state var|    | ∆ state eq |
                 |           |           |    |            |    |            |
                 ------------------------- x  |------------|  = |------------|
        algeb eq |J21        | J22       |    | ∆ algeb var|    | ∆ algeb eq |
                 |           |           |    |            |    |            |
        """
        print("Compiling...")

        self._rhs_algeb_fn = SymbolicVector(eqs=self._algebraic_eqs_substituted, uid2sym_vars=self.uid2sym_vars,
                                                uid2sym_params=self.uid2sym_params)

        self._params_fn = SymbolicParamsVector(eqs=self._parameters_eqs, uid2sym_t=self.uid2sym_t)

        if len(self._state_eqs) != 0:
            self._rhs_state_fn = SymbolicVector(eqs=self._state_eqs_substituted, uid2sym_vars=self.uid2sym_vars,
                                                    uid2sym_params=self.uid2sym_params)




            self._j11_fn =  SymbolicJacobian(eqs=self._state_eqs_substituted, variables=self._state_vars, diff_variables= self._diff_vars,
                                                    lag_variables= self._lag_vars, lag_vars_set= self._lag_vars_set,
                                                    uid2sym_vars=self.uid2sym_vars, uid2sym_params=self.uid2sym_params,
                                                    uid2idx_vars=self.uid2sym_vars, uid2idx_lag=self.uid2idx_lag, dt= self.dt)
            self._j12_fn =  SymbolicJacobian(eqs=self._state_eqs_substituted, variables=self._algebraic_vars, diff_variables= self._diff_vars,
                                                    lag_variables= self._lag_vars, lag_vars_set= self._lag_vars_set,
                                                    uid2sym_vars=self.uid2sym_vars, uid2sym_params=self.uid2sym_params,
                                                    uid2idx_vars=self.uid2sym_vars, uid2idx_lag=self.uid2idx_lag, dt= self.dt)

            self._j21_fn =  SymbolicJacobian(eqs=self._algebraic_eqs_substituted, variables=self._state_vars,diff_variables= self._diff_vars,
                                                    lag_variables= self._lag_vars, lag_vars_set= self._lag_vars_set,
                                                    uid2sym_vars=self.uid2sym_vars, uid2sym_params=self.uid2sym_params,
                                                    uid2idx_vars=self.uid2sym_vars, uid2idx_lag=self.uid2idx_lag, dt= self.dt)
            self._j22_fn =  SymbolicJacobian(eqs=self._algebraic_eqs_substituted, variables=self._algebraic_vars,diff_variables= self._diff_vars,
                                                    lag_variables= self._lag_vars, lag_vars_set= self._lag_vars_set,
                                                    uid2sym_vars=self.uid2sym_vars, uid2sym_params=self.uid2sym_params,
                                                    uid2idx_vars=self.uid2sym_vars, uid2idx_lag=self.uid2idx_lag, dt= self.dt)

        else:
            self._j22_fn =  SymbolicJacobian(eqs=self._algebraic_eqs_substituted, variables=self._algebraic_vars,diff_variables= self._diff_vars,
                                                    lag_variables= self._lag_vars, lag_vars_set= self._lag_vars_set,
                                                    uid2sym_vars=self.uid2sym_vars, uid2sym_params=self.uid2sym_params,
                                                    uid2idx_vars=self.uid2sym_vars, uid2idx_lag=self.uid2idx_lag, dt= self.dt)


        # stability equations for initialization
        self._j_stable =  SymbolicJacobian(eqs=self._stability_eqs, variables=self._algebraic_vars,diff_variables= self._diff_vars,
                                                    lag_variables= self._lag_vars, lag_vars_set= self._lag_vars_set,
                                                    uid2sym_vars=self.uid2sym_vars, uid2sym_params=self.uid2sym_params,
                                                    uid2idx_vars=self.uid2sym_vars, uid2idx_lag=self.uid2idx_lag, dt= self.dt)
        print(
            f"Model compiled with {self._n_vars} variables, {len(self._lag_vars)} lags, {len(self._algebraic_eqs_substituted)}  algebraic eqs and {len(self._state_eqs_substituted)} state eqs")


    def _get_jacobian(self,
                      eqs: List[Expr],
                      variables: List[Var],
                      uid2sym_vars: Dict[int, str],
                      uid2sym_params: Dict[int, str],
                      dt: Const = Const(0.001),
                      substitute:bool = True,
                      add_delta:bool =True):
        """
        JIT‑compile a sparse Jacobian evaluator for *equations* w.r.t *variables*.
        :param eqs: Array of equations
        :param variables: Array of variables to differentiate against
        :param uid2sym_vars: dictionary relating the uid of a var with its array name (i.e. var[0])
        :param uid2sym_params:
        :return:
                jac_fn : callable(values: np.ndarray) -> scipy.sparse.csc_matrix
                    Fast evaluator in which *values* is a 1‑D NumPy vector of length
                    ``len(variables)``.
                sparsity_pattern : tuple(np.ndarray, np.ndarray)
                    Row/col indices of structurally non‑zero entries.
        """

        # Ensure deterministic variable order
        diff_vars = self._diff_vars
        if not substitute:
            _ = 0
            #diff_vars = []
        check_set = set()
        for v in variables:
            if v in check_set:
                raise ValueError(f"Repeated var {v.name} in the variables' list :(")
            else:
                check_set.add(v)

        # Cache compiled partials by UID so duplicates are reused
        fn_cache: Dict[str, Callable] = {}
        triplets: List[Tuple[int, int, Callable]] = []  # (col, row, fn)

        for row, eq in enumerate(eqs):
            for lag_var in self._lag_vars:
                if lag_var.lag == 0:
                    eq = eq.subs({lag_var: lag_var.base_var})

            for col, var in enumerate(variables):
                diff_var = DiffVar.get_or_create(var.name + '_diff', base_var=var)
                #d_expression = eq.diff(var).simplify() + (1/self.dt)*eq.diff(diff_var).simplify()
                d_expression = eq.diff(var).simplify()
                for diff_var in diff_vars:
                    deriv = eq.diff(diff_var)
                    continue
                #We substitute the remaining diff vars in d_expression
                for diff_var in diff_vars:
                    deriv = d_expression.diff(diff_var)
                    if getattr(deriv, 'value', 1) != 0:
                        if not substitute:
                            d_expression = d_expression.subs({diff_var: diff_var/self.delta})
                        else:
                            dx_dt, lag = diff_var.approximation_expr(dt=dt, lag_can_be_0=False)
                            d_expression = d_expression.subs({diff_var: dx_dt/self.delta})
                            new_lag = LagVar.get_or_create(diff_var.origin_var.name+ '_lag_' + str(lag),
                                                    base_var = diff_var.origin_var, lag = lag)
                            i = len(self.uid2idx_vars)
                            l = len(self.uid2idx_lag)
                            if new_lag not in self._lag_vars_set:
                                uid2sym_vars[new_lag.uid] = f"vars[{i}]"
                                self.uid2idx_vars[new_lag.uid] = i
                                self.uid2idx_lag[new_lag.uid] = l
                                self._lag_vars.append(new_lag)
                                self._lag_vars_set.add(new_lag)
                                i += 1
                                l += 1

                if isinstance(d_expression, Const) and d_expression.value == 0:
                    continue  # structural zero

                triplets.append((col, row, d_expression))
                if not substitute:
                    _ = 0
        # Sort by column, then row for CSC layout
        triplets.sort(key=lambda t: (t[0], t[1]))
        cols_sorted, rows_sorted, equations_sorted = zip(*triplets) if triplets else ([], [], [])
        functions_ptr = _compile_equations(eqs=equations_sorted, uid2sym_vars=uid2sym_vars,
                                                  uid2sym_params=uid2sym_params)

        nnz = len(cols_sorted)
        indices = np.fromiter(rows_sorted, dtype=np.int32, count=nnz)

        indptr = np.zeros(len(variables) + 1, dtype=np.int32)
        for c in cols_sorted:
            indptr[c + 1] += 1
        np.cumsum(indptr, out=indptr)

        def jac_fn(values: np.ndarray, params: np.ndarray) -> sp.csc_matrix:  # noqa: D401 – simple
            assert len(values) >= len(variables)
            ##print(f'Signtures are {functions_ptr.signatures}')

            jac_values = functions_ptr(values, params)
            data = np.array(jac_values, dtype=np.float64)

            return sp.csc_matrix((data, indices, indptr), shape=(len(eqs), len(variables)))

        return jac_fn


    def rhs_pseudo_transient(self, x: np.ndarray, xn: np.ndarray, params: np.ndarray, sim_step, h: float) -> np.ndarray:
        # returns algeb rhs is there is no states, is there is states, returns states and algebs rhs

        """
        Return 𝑑x/dt given the current *state* vector.
        :param x: get the right-hand-side give a state vector
        :param xn:
        :param params: params array
        :param sim_step: simulation step
        :param h: simulation step
        :return [f_state_update, f_algeb]
        """
        # we set delta = h
        params[-1] = 1

        # we set dt = 1.0
        params[-2] = 1e50
        f_algeb = np.array(self._rhs_algeb_fn(x, params))
        x_aux = x.copy()
        dx = np.zeros(len(self.uid2sym_vars))
        params = np.r_[params, dx]
        # f_algeb = self._rhs_predictor(x_aux, params)
        sim_step = sim_step
        if self._n_state > 0:
            f_state = np.array(self._rhs_state_fn(x, params))
            f_state_update = (x[:self._n_state] - xn[:self._n_state]) / h - f_state
            return np.r_[f_state_update, f_algeb]

        else:
            return f_algeb

    def jacobian_implicit(self, x: np.ndarray, params: np.ndarray, h: float) -> sp.csc_matrix:
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

        #returns only j22 if no states, returns J if states

        if len(self._state_eqs) == 0:
            j22: sp.csc_matrix = self._j22_fn(x, params)
            return j22

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

    #### initialization

    def jacobian_pseudo_transient(self, x: np.ndarray, params: np.ndarray, h: float) -> sp.csc_matrix:
        """
        #We want to build an equivalent of the following Jacobian:
                J11 = delta^-1 * I + Jf
        """
        # We set delta = 1.0
        params[-1] = 1.0

        # We set dt = h
        params[-2] = h

        # Now we have J = -delta^-1 * I - Jf so we need to multiply J by -1.
        J = self.jacobian_implicit(x, params, h)

        flip_index = self._diff_eq_index
        J = J.tolil()
        J[flip_index, :] *= 1
        J = J.tocsr()
        return J

    def build_init_params_vector(self, mapping: dict[Var, float]) -> np.ndarray:
        """
        Helper function to build the initial vector
        :param mapping: var->initial value mapping
        :return: array matching with the mapping, matching the solver ordering
        """
        x = np.zeros(self._n_params)

        for key, val in mapping.items():
            i = self.uid2idx_event_params[key.uid]

            x[i] = val

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

    def warm_up_start(self):
        dummy_vals = np.zeros(len(self._algebraic_vars) + len(self._state_vars) + len(self._lag_vars), dtype=np.float64)
        dummy_params = np.random.rand(len(self._parameters))
        self.jacobian_implicit(dummy_vals, dummy_params, 0.001)  # triggers compilation once
        self._rhs_algeb_fn(dummy_vals, dummy_params)  # triggers compilation once

    def sort_vars(self, mapping: dict[Var, float], permissive: bool = False) -> np.ndarray:
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

    def build_init_diffvars_vector(self, mapping: dict[Var, float]) -> np.ndarray:
        """
        Helper function to build the initial vector
        :param mapping: var->initial value mapping
        :return: array matching with the mapping, matching the solver ordering
        """
        x = np.zeros(len(self._diff_vars))

        for key, val in mapping.items():
            if key.uid in self.uid2idx_diff.keys():
                i = self.uid2idx_diff[key.uid]
                x[i] = val
            else:
                raise ValueError(f"Missing variable {key} definition")

        return x

    def build_init_lagvars_vector(self, mapping: dict[Var, float]) -> np.ndarray:
        """
        Helper function to build the initial vector
        :param mapping: var->initial value mapping
        :return: array matching with the mapping, matching the solver ordering
        """
        x = np.zeros(len(self._lag_vars))

        for key, val in mapping.items():
            if key.uid in self.uid2idx_vars.keys():
                try:
                    i = self.uid2idx_vars[key.uid]
                    x[i] = val
                except:
                    _ = 0
            else:
                raise ValueError(f"Missing variable {key} definition")

        return x

    def build_initial_lag_variables(self, x0: np.ndarray, dx0: np.ndarray, h) -> np.ndarray:
        if len(self._lag_vars) == 0:
            return np.array([])

        x_lag = np.zeros(len(self._lag_vars), dtype=np.float64)
        pdb.set_trace()


        lag_registry = self._lag_vars[0]._registry
        diff_registry = self._diff_vars[0]._absolute_registry

        max_order = max(var.diff_order for var in self._diff_vars)
        max_order = max(2, max_order)
        filtered_lag_dict = {key: value for key, value in lag_registry.items() if key[1] <= max_order}
        sorted_lag_dict = sorted(filtered_lag_dict.items(), key=lambda item: (item[0][0], item[0][1]))

        for key, lag_var in sorted_lag_dict:
            base_var_uid, lag = key

            uid = lag_var.uid

            if base_var_uid not in self.uid2idx_vars or lag_var not in self._lag_vars:
                continue
            idx = self.uid2idx_lag[uid]
            x0_uid = self.uid2idx_vars[base_var_uid]
            if lag == 0:
                x_lag[idx] = x0[x0_uid]
                continue
            # Collect previous dx0 and x_lag values for this lag_var
            dx0_slice = np.zeros(lag_var.lag)
            x_lag_last = 0

            for (prev_uid, prev_lag), prev_var in lag_registry.items():
                if prev_uid == base_var_uid and prev_lag <= lag and prev_lag != 0:
                    try:
                        prev_diff = diff_registry[base_var_uid, prev_lag]
                        prev_idx_diff = self.uid2idx_diff[prev_diff.uid]
                        dx0_slice[prev_lag - 1] = dx0[prev_idx_diff]

                    except:
                        if (base_var_uid, 1) in diff_registry and diff_registry[base_var_uid, 1] in self._diff_vars:
                            prev_diff = diff_registry[base_var_uid, 1]
                            prev_idx_diff = self.uid2idx_diff[prev_diff.uid]
                            print(f'index is {prev_idx_diff} and var is {prev_diff}')
                            dx0_slice[prev_lag - 1] = dx0[prev_idx_diff]
                        else:
                            dx0_slice[prev_lag - 1] = 0

            lag_i = lag_var.populate_initial_lag(x0[x0_uid], dx0_slice, x_lag_last, self.dt, h)
            if isinstance(lag_i, Expr):
                x_lag[idx] = lag_i.eval(dt=h)
            else:
                x_lag[idx] = lag_i
            _ = 0
        return x_lag

    def build_initial_guess(self, x0: np.ndarray, dx0: np.ndarray, h) -> np.ndarray:
        res = x0.copy()
        for diff_var in self._diff_vars:
            if diff_var.diff_order > 1:
                continue
            uid = diff_var.base_var.uid
            idx = self.uid2idx_vars[uid]
            diff_idx = self.uid2idx_diff[diff_var.uid]
            res[idx] += h * dx0[diff_idx]
        return res
#################################################################################################3
    # TODO: call of this function in GUI needs to be updated
    def simulate(
            self,
            t0: float,
            t_end: float,
            h: float,
            x0: np.ndarray,
            dx0: np.ndarray,
            params0: np.ndarray,
            method: Literal["rk4", "euler", "implicit_euler"] = "rk4",
            newton_tol: float = 1e-8,
            newton_max_iter: int = 1000,
            followed_vars=None,
            initialized=False,
            verbose=False,

    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        :param params0:
        :param t0: start time
        :param t_end: end time
        :param h: step
        :param x0: initial values
        :param dx0
        :param method: method
        :param newton_tol:
        :param newton_max_iter:
        :param followed_vars:
        :param initialized:
        :param verbose:
        :return: 1D time array, 2D array of simulated variables
        """

        # print(f'Init simulate')
        time_start = time.time()
        if initialized:
            x0 = x0[:self._n_alg]
            lag0 = x0[self._n_alg:]
            print(f'lag0 is {lag0}')
        else:
            lag0 = self.build_initial_lag_variables(x0, dx0, h)
            x0 = self.build_initial_guess(x0, dx0, h)
        time_initialization = time.time() - time_start
        if method == "euler":
            return self._simulate_fixed(t0, t_end, h, x0, params0, stepper="euler")
        if method == "rk4":
            return self._simulate_fixed(t0, t_end, h, x0, params0, stepper="rk4")
        if method == "implicit_euler":
            # print(f'Initialization time is {time_initialization}')
            return self._simulate_implicit_euler_diff(
                t0=t0, t_end=t_end, h=h, x0=x0, dx0=dx0, lag0=lag0, params0=params0,
                tol=newton_tol, max_iter=newton_max_iter, verbose=verbose,
                followed_vars=followed_vars,
            )
        raise ValueError(f"Unknown method '{method}'")

    # TODO: this function needs to be updated with current block_solver simulate function
    def _simulate_implicit_euler_diff(self, t0, t_end, h, x0, dx0, lag0, params0: np.ndarray, time_var: Var, tol=1e-8,
                                 max_iter=1e6, followed_vars=None, verbose=False):
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
        init_time = time.time()
        steady_state = np.allclose(dx0, 0.0, atol=1e-12)
        max_iter_0 = max_iter
        # print(f'Simulation started at {init_time}')
        # print(f'x0 is {x0}')
        # print(f'lag0 is {lag0}')
        steps = int(np.ceil((t_end - t0) / h))
        t = np.empty(steps + 1)
        y = np.empty((steps + 1, self._n_vars))
        self.y = y
        self.t = t

        # timing accumulators
        timings = {
            "jacobian_time": 0.0,
            "rhs_time": 0.0,
            "lag_update_time": 0.0,
            "linear_solver_time": 0.0,
            "initial_step_time": 0.0,
        }

        params_current = params0
        t[0] = t0
        y[0] = x0.copy()
        dx = dx0.copy()
        lag = np.asarray(lag0, dtype=np.float64)
        for step_idx in range(steps):
            self.step_idx = step_idx
            params_previous = params_current.copy()
            discontinuity = np.linalg.norm(params_current - params_previous, np.inf) > 1e-10
            xn = y[step_idx]
            x_last = y[step_idx - 1] if step_idx > 0 else y[step_idx]
            x_last_lags = np.r_[x_last, lag]
            x_new = xn.copy()  # initial guess
            converged = False
            n_iter = 0
            current_time = t[step_idx]
            params_current = self._params_fn(float(current_time))
            # We compute dx for the next step
            # dx = self.compute_dx(x_new, lag, h)
            # print(f'Step {step_idx} read')
            if step_idx == 0:
                tol = 1e-3
                initial_step_start = time.time()
            else:
                tol = 1e-7
            while not converged and n_iter < 1e5:

                # ---------------- lag update ----------------
                lag_update_start = time.time()
                self._update_0_lags(x_new, lag)
                lag_update_end = time.time()
                timings["lag_update_time"] += lag_update_end - lag_update_start
                # ------------------------------------------------

                xn_lags = np.r_[xn, lag]
                xnew_lags = np.r_[x_new, lag]

                if discontinuity:
                    tol = 1e-8
                    max_iter = 5e5

                if followed_vars is not None:
                    for var in followed_vars:
                        idx = self.get_var_idx(var)

                params_current = np.asarray(params_current, dtype=np.float64)
                # ---------------- rhs calculation ----------------
                rhs_start = time.time()
                rhs = self.rhs_implicit(xnew_lags, xn_lags, params_current, step_idx + 1, h)
                # print(rhs)
                rhs_end = time.time()
                timings["rhs_time"] += rhs_end - rhs_start
                # -------------------------------------------------

                # recompute Jacobian for next iteration
                jac_start = time.time()
                # Jf = self.jacobian_implicit(xnew_lags, params_current, h)
                jac_end = time.time()
                if step_idx == 0:
                    _ = 0
                    # print(f'jacobian time is {(jac_end - jac_start)}')
                timings["jacobian_time"] += jac_end - jac_start

                residual = np.linalg.norm(rhs, np.inf)
                converged = residual < tol

                if step_idx == 0:
                    alpha_update = 1.0
                    if not steady_state:
                        print("We are in steady state")
                        alpha_update = 1.0
                    old_lag = lag
                    lag = self.build_initial_lag_variables(x_new, dx0, h)
                    lag = (1 - alpha_update) * old_lag + alpha_update * lag
                    max_iter = 5e5
                    Jf = self.jacobian_implicit(xnew_lags, params_current, h)
                    delta = sp.linalg.spsolve(Jf, -rhs)
                    if converged:
                        print("System well initialized.")
                        print(f"x is {x_new}")
                    else:
                        print(f"System bad initialized. DAE resiudal is {residual}.")
                        print(f'rhs is {rhs}')
                        non_zero_indexes = np.where(np.abs(rhs) > 1e-6)[0]
                        # eqs = [self._algebraic_eqs[i] for i in non_zero_indexes]
                        # print(f'eqs are {eqs}')
                else:
                    max_iter = max_iter_0
                    # Jf = self.jacobian_implicit(xnew_lags, params_current, h)
                    # delta = sp.linalg.spsolve(Jf, -rhs)

                if converged:
                    break

                solved = False
                linear_start = time.time()
                Jf = self.jacobian_implicit(xnew_lags, params_current, h)
                delta = sp.linalg.spsolve(Jf, -rhs)

                linear_end = time.time()
                timings["linear_solver_time"] += linear_end - linear_start
                solved = np.all(np.isfinite(delta))

                if not solved:
                    delta, *_ = sp.linalg.lsqr(Jf, -rhs)
                    solved = np.all(np.isfinite(delta))
                    u, s, vh = np.linalg.svd(Jf.toarray() if sp.issparse(Jf) else Jf)
                    singular_dirs = np.where(s < tol)[0]
                    for i in singular_dirs:
                        v = vh.T[:, i]  # variable-space vector
                        abs_v = np.abs(v)
                        dominant_idx = np.argsort(abs_v)[::-1][:5]  # top 5 vars
                        print(f"\nSingular direction {i}, σ={s[i]:.3e}")
                        for j in dominant_idx:
                            var_name = self._algebraic_vars[j].name
                            print(f"  {var_name:20s} {v[j]:+.3e}")
                    print("Using LSQR")
                    exit()

                if not solved:
                    nan_indices = np.where(np.isnan(rhs))[0]
                    # nan_indices = np.where(np.abs(rhs) > 1e-2)[0]
                    nan_eqs = [self._algebraic_eqs[i] for i in nan_indices]
                    print(f'Jf is {Jf}')
                    raise ValueError(
                        f"spsolve returned non-finite values (NaN or Inf).\n"
                        f"delta = {delta}\n"
                        f"rhs = {rhs}\n"
                        f"Jacobian shape = {Jf.shape}\n"
                        f"NaNs found at indices {nan_indices.tolist()} in equations:\n{nan_eqs}",
                    )

                if not solved:
                    raise RuntimeError("Failed to solve linear system even with regularization.")

                x_new += delta
                n_iter += 1

            if converged:
                if step_idx == 0:
                    initial_step_end = time.time()
                    timings['initial_step_time'] = initial_step_end - initial_step_end
                    print(f'diff residual is {np.linalg.norm(x0[:self._n_alg] - x_new[:self._n_alg])}')
                lag_update_start = time.time()
                print(f'converged is {converged} at step {step_idx} and iter {n_iter}')

                if verbose:
                    _ = 0

                if discontinuity:
                    _ = 0
                    y[step_idx + 1] = x_new
                else:
                    y[step_idx + 1] = x_new
                t[step_idx + 1] = t[step_idx] + h

                for i, lag_var in enumerate(self._lag_vars):
                    if lag_var.lag == 0:
                        uid = lag_var.base_var.uid
                        idx = self.uid2idx_vars[uid]
                        lag[i] = x_new[idx]
                    elif step_idx + 1 - (lag_var.lag - 1) >= 0:
                        uid = lag_var.base_var.uid
                        idx = self.uid2idx_vars[uid]
                        lag[i] = y[step_idx + 1 - (lag_var.lag - 1), idx]
                    else:
                        lag_name = lag_var.base_var.name + '_lag_' + str(lag_var.lag - 1)
                        next_lag_var = LagVar.get_or_create(lag_name, base_var=lag_var.base_var, lag=lag_var.lag - 1)
                        uid = next_lag_var.uid
                        idx = self.uid2idx_lag[uid]
                        lag[i] = lag[idx]
                lag_update_end = time.time()
                timings["lag_update_time"] += lag_update_end - lag_update_start

            else:
                print(f"Failed to converge at step {step_idx} and n_iter is {n_iter}")
                print(f'Residual is {residual}')
                break

        return t, y, timings

    def _update_0_lags(self, x_new, lag):
        for i, lag_var in enumerate(self._lag_vars):
            if lag_var.lag == 0:
                uid = lag_var.base_var.uid
                idx = self.uid2idx_vars[uid]
                lag[i] = x_new[idx]

    def compute_dx(self, x: np.ndarray, lag: np.ndarray, h: float) -> np.ndarray:
        """
        Compute the numerical derivative (dx) for all differential variables
        using symbolic approximation expressions and lagged variables.

        Parameters
        ----------
        y : np.ndarray
            State variable trajectory. `y[-1, :]` corresponds to the most recent
            values of the system variables.
        lag : np.ndarray
            Array containing lagged values of variables (delayed states).
        h : float
            Time step (dt) used in the approximation.

        Returns
        -------
        np.ndarray
            Array with computed derivatives for each differential variable,
            indexed consistently with `self._diff_vars`.
        """
        lag_uids = [uid for uid in self.uid2idx_lag.keys()]
        res = np.zeros(len(self._diff_vars), dtype=np.float64)
        for diff_var in self._diff_vars:
            uid = diff_var.uid
            idx = self.uid2idx_diff[uid]
            dx_expression, lag_number = diff_var.approximation_expr(self.dt)

            # We substitute the origin variable and dt
            lag_0 = LagVar.get_or_create(diff_var.origin_var.name + '_lag_' + str(0),
                                         base_var=diff_var.origin_var, lag=0)
            subs = {diff_var.origin_var: Const(x[self.uid2idx_vars[diff_var.origin_var.uid]])}
            subs[lag_0] = Const(x[self.uid2idx_vars[diff_var.origin_var.uid]])
            subs[self.dt] = Const(h)

            # We substitute the lag variables
            i = 1
            lag_in_expression = True
            while lag_in_expression or i <= 2:
                lag_i = LagVar.get_or_create(diff_var.origin_var.name + '_lag_' + str(i),
                                             base_var=diff_var.origin_var, lag=i)
                dx_expression = dx_expression.subs({self.dt: Const(h)})
                deriv = dx_expression.diff(lag_i)
                if getattr(deriv, 'value', 1) == 0:
                    if i > 2:
                        lag_in_expression = False
                        i = i + 1
                        break
                    i += 1
                    continue
                if lag_i.uid not in lag_uids:
                    break
                lag_idx = self.uid2idx_lag[lag_i.uid]

                subs[lag_i] = Const(lag[lag_idx])
                i += 1

            deriv_value = dx_expression.subs(subs)
            # print(dx_expression)
            # print(diff_var)
            deriv_value = deriv_value.eval()
            res[idx] = deriv_value

        return res


    def pseudo_transient(self, x0: np.ndarray, init_guess: dict[Var, float], res, grid: MultiCircuit,
                         fix='V', dtau0=1, max_iter: int = 1e3, plot: bool = False, predictor: bool = False,
                         type: str = None):
        """
        :param x0: random init guess
        :param init_guess: init_guess for power flow vars
        :param res:
        :param grid:
        :param fix:
        :param dtau0:
        :param max_iter:
        :param plot:
        :param predictor:
        :param type:

        """
        for block in self.block_system.children:
            found = False
            if getattr(block, 'pseudo_transient', False):
                bus = block.bus
                t = self.glob_time
                for child_block in block.get_all_blocks():
                    if not hasattr(child_block, 'external_mapping'):
                        continue
                    if not VarPowerFlowRefferenceType.P in child_block.external_mapping.keys():
                        continue
                    Pg = child_block.external_mapping[VarPowerFlowRefferenceType.P]
                    Qg = child_block.external_mapping[VarPowerFlowRefferenceType.Q]
                    Vm = child_block.external_mapping[VarPowerFlowRefferenceType.Vm]
                    Va = child_block.external_mapping[VarPowerFlowRefferenceType.Va]
                    found = True
                    break

                if not found:
                    continue
                bus_block = DiffBlock()

                if fix == 'P':
                    delete_vars_from_block(block, [Pg, Qg])
                    bus_block = DiffBlock(
                        algebraic_vars=[Vm, Va])
                    bus_block.event_dict= {Pg: Const(float(np.real(res.Sbus[bus] / grid.Sbase))),
                                     Qg: Const(float(np.imag(res.Sbus[bus] / grid.Sbase)))}


                elif fix == 'V':
                    delete_vars_from_block(block, [Va, Vm])
                    bus_block = DiffBlock(
                        algebraic_vars=[Pg, Qg])
                    bus_block.event_dict ={Vm: Const(float(np.abs(res.voltage[bus]))),
                                           Va: Const(float(np.angle(res.voltage[bus])))}

                elif fix == 'I':
                    Im = Var('Im')
                    Ia = Var('Ia')
                    delta = find_name_in_block('delta', block)
                    Id = find_name_in_block('Id', block)
                    Iq = find_name_in_block('Iq', block)
                    v = res.voltage[bus]
                    Sb = res.Sbus[bus] / grid.Sbase

                    # Current from power and voltage
                    i = np.conj(Sb / v)  # ī = (p - jq) / v̄*

                    bus_block = DiffBlock(
                        algebraic_eqs=[
                            Id - (-Im * sin(Ia - delta)),
                            Iq - Im * cos(Ia - delta),
                        ],
                        algebraic_vars=[Pg, Qg, Vm, Va])
                    bus_block.event_dict = {Im: Const(float(np.abs(i))),
                                               Ia: Const(float(np.angle(i)))}

                elif fix == 'P&V':
                    delete_vars_from_block(block, [Pg, Qg, Vm, Va])
                    bus_block = DiffBlock()

                    bus_block.event_dict = {Pg: Const(float(np.real(res.Sbus[bus] / grid.Sbase))),
                                            Qg: Const(float(np.imag(res.Sbus[bus] / grid.Sbase))),
                                            Vm: Const(float(np.abs(res.voltage[bus]))),
                                            Va: Const(float(np.angle(res.voltage[bus])))}


                elif fix == 'mixed':
                    delete_vars_from_block(block, [Vm, Va, Pg, Qg])
                    bus_block = DiffBlock(
                        algebraic_vars=[Va, Qg])
                    bus_block.event_dict = {Vm: Const(float(np.abs(res.voltage[bus]))),
                                             Pg: Const(float(np.real(res.Sbus[bus] / grid.Sbase)))}

                init_block = DiffBlock(
                    children=[block, bus_block]
                )
                # 2 out of [Pg, Qg, Vm, Va] need to be deleted from the algebraic vars to have a square system
                solver = DiffBlockSolver(init_block, t)

                init_guess_copy = init_guess.copy()

                init_guess_copy.update(
                    {Vm: float(np.real(res.Sbus[bus] / grid.Sbase)), Va: float(np.imag(res.Sbus[bus] / grid.Sbase))})
                x0_init_guess = solver.build_init_vars_vector(init_guess_copy, permissive=True)

                solved = False
                alpha = 0.9
                while not solved:
                    try:
                        print(f'Trying dtau0 = {dtau0} with max_iter {max_iter}')
                        if type == 'dae':
                            x0_mdl, init_guess_mdl = solver.pseudo_transient_daes(
                                x0_init_guess.copy(), dtau0=dtau0, max_iter=max_iter, max_tries=1e3, plot=plot,
                                predictor=predictor)
                        else:
                            x0_mdl, init_guess_mdl = solver.init_pseudo_transient_individual(
                                x0_init_guess.copy(), dtau0=dtau0, max_iter=max_iter, max_tries=1e3, plot=plot,
                                predictor=predictor)
                        solved = True
                    except NaNError as e:
                        msg = str(e).lower()
                        # print(msg)
                        dtau0 /= alpha
                    except ConvergenceError as e:
                        msg = str(e).lower()
                        # print(msg)
                        dtau0 *= alpha
                    except Exception as e:
                        # print(f"❌ Unexpected error: {e}")
                        raise
                for i, var in enumerate(solver._algebraic_vars):
                    x0[self.uid2idx_vars[var.uid]] = x0_mdl[solver.uid2idx_vars[var.uid]]

                init_guess.update(init_guess_mdl)

        # print('Pseudo-Transient ended')
        return x0, init_guess

    def init_pseudo_transient_individual(self, x0, init_guess= dict(), plot=True, dtau0=1e0, h=1e-3, beta=0.8, tol=1e-5,
                                         predictor=False, max_iter=8e4, max_tries=200, verbose=False):
        # Init pseudo transient method, Block only has algebraic eqs

        lag = np.zeros(len(self.uid2idx_lag))
        dtau = dtau0
        dtau_max = 1e3
        dtau_min = 1e-7
        init_guess_uid = [var.uid for var in init_guess.keys()]
        self.compile_implicit_predictor()

        for var in self._algebraic_vars:
            if not var.uid in init_guess_uid:
                continue
            idx = self.uid2idx_vars[var.uid]
            x0[idx] = init_guess[var]
        for i in range(len(x0)):
            if x0[i] == 0:
                _ = 0
                x0[i] = 0.1 + 0.5 * np.random.rand()
        for i in range(len(lag)):
            base_var = self._lag_vars[i].base_var
            try:
                lag[i] = x0[self.uid2idx_vars[base_var.uid]]
            except:
                lag[i] = 0.2
            if lag[i] == 0:
                lag[i] += 0.21 + np.random.rand()

        y = np.empty((5, self._n_vars))
        step_idx = 0
        x_new = x0.copy()
        tries = 0
        current_time = 0
        params_current = self._params_fn(float(current_time))

        # We set dt = 1
        params_current[-1] = 1
        params_outer = params_current.copy()

        dx_error = 1
        residual = 10
        old_residual = 10
        old_dx_error = 10

        # history containers
        dtau_hist = []
        dx_error_hist = []
        residual_hist = []
        x_hist = []
        dx_hist = []

        x_old_iter = np.r_[x_new, lag]
        while step_idx < max_iter:
            tries += 1
            xn = y[-1]
            params_current[-2] = 0.001

            xn_lags = np.r_[xn, lag]
            xnew_lags = np.r_[x_new, lag]
            # rhs = self.rhs_implicit(xnew_lags, xn_lags, params_current, 1, dtau)
            if verbose:
                print(f'Pseudo transient step started with max_iter {max_iter} and step idx {step_idx} and try {tries}')
            # if (tries == 1 or (tries < 10 and predictor)) and False:
            if step_idx < 2 and tries == 1 and False:
                x_predicted, x_feasible = self.predictor(x_old=x_old_iter, max_step=5e3, params=params_current)
                for i in range(0):
                    _ = 0
                    x_corrected, x_feasible = self.corrector(x_predicted, x_old_iter, x_feasible, params_current)
                    x_predicted = x_corrected

                xnew_lags[:len(x_feasible)] = x_feasible

                # 1 Handle first-order derivatives first
                for i, var in enumerate(self._diff_vars):
                    if var.diff_order != 1:
                        continue
                    base_var_uid = self.uid2idx_vars[var.base_var.uid]
                    xnew_lags[base_var_uid] = x_predicted[i]

                # 2 Sort differential variables by diff_order before building lags
                diff_vars_sorted = sorted(self._diff_vars, key=lambda v: v.diff_order)

                # 3 Build lag variables in increasing order of diff_order
                for i, var in enumerate(diff_vars_sorted):
                    if var.diff_order <= 1:
                        continue

                    origin_var = var.origin_var
                    diff_order = var.diff_order

                    # Previous lag (order-1)
                    prev_lag = LagVar.get_or_create(
                        name=f"{origin_var.name}_lag{diff_order - 1}",
                        base_var=origin_var,
                        lag=diff_order - 1,
                    )
                    prev_lag_uid = self.uid2idx_vars[prev_lag.uid]

                    # Current lag
                    lag_var = LagVar.get_or_create(
                        name=f"{origin_var.name}_lag{diff_order}",
                        base_var=origin_var,
                        lag=diff_order,
                    )
                    lag_uid = self.uid2idx_vars[lag_var.uid]

                    # Recursive lag update: x_lag_n = x_lag_(n-1) − h * x^(n)
                    xnew_lags[lag_uid] = xnew_lags[prev_lag_uid] - params_current[-1] * x_predicted[i]

                print(f'xnew_lags is {xnew_lags}')
                rhs = self.rhs_implicit(xnew_lags, xn_lags, params_current, 1, dtau)
                Jf = self.jacobian_implicit(xnew_lags, params_current, dtau)
                dx_previous = self.compute_dx(xnew_lags[:self._n_alg], lag, dtau)
                residual_dx = np.linalg.norm(dx_previous)
                residual = np.linalg.norm(rhs)
                x_new = xnew_lags[:len(x_new)]
                xnew_lags = np.r_[x_new, lag]
                print(f'xnew_lags is {xnew_lags}')

                if verbose:
                    print(f'residual is {residual}')
                if residual_dx < tol and residual < tol:
                    x_new = xnew_lags[:self._n_alg]
                    dx = self.compute_dx(xnew_lags[:self._n_alg], lag, 1e-3)
                    residual_dx = np.linalg.norm(dx)
            else:
                rhs = self.rhs_pseudo_transient(xnew_lags, xn_lags, params_current, 1, dtau)
                Jf = self.jacobian_pseudo_transient(xnew_lags, params_current, dtau)
                residual = np.linalg.norm(rhs)

                try:
                    delta = sp.linalg.spsolve(Jf, -rhs)
                except Exception as e:
                    raise SingularJacobianError(f"Linear solver failed at try {tries}: {e}")
                if not np.all(np.isfinite(delta)): #or not np.all(np.isfinite(delta)):
                    print(f'jacobian is {Jf.toarray()}')
                    print(f'delta is {delta}')
                    print(f'x_new is {x_new}')
                    print(f'rhs is {rhs}')
                    print(f'residual is {np.linalg.norm(rhs)} try is {tries} and step is {step_idx}')
                    raise NaNError(
                        f"Newton step failed at try {tries} and step {step_idx}: delta has NaN/Inf values with dtau {dtau}")
                print(f'delta shape is {delta.shape}')
                print(f'x_new shape is {x_new.shape}')
                x_new += delta
                xnew_lags = np.r_[x_new, lag]
                rhs = self.rhs_pseudo_transient(xnew_lags, xn_lags, params_current, 1, dtau)

            if step_idx == 0 and tries % 10 == 1:
                i = np.argmax(rhs)

            newton_residual = np.linalg.norm(rhs, np.inf)
            converged = (tries % 10 == 9) or (tries < 10) or True
            if verbose:
                _ = 0
                print(f'residual is {newton_residual}, step is {step_idx} try is {tries}')
                print(f'dtau is {dtau}')

            if converged:
                step_idx += 1
                tries = 0
                y = np.roll(y, shift=-1, axis=0)
                alpha = 1.0
                if step_idx > 2:
                    y[-1] = alpha * x_new + (1 - alpha) * y[-1]
                else:
                    y[-1] = alpha * x_new
                x_new = y[-1]

                dx = self.compute_dx(x_new, lag, dtau)
                dx_error = np.linalg.norm(dx)
                rhs = self.rhs_pseudo_transient(xnew_lags, xn_lags, params_current, 1, dtau)
                residual = np.linalg.norm(rhs)

                # save history
                dtau_hist.append(dtau)
                dx_error_hist.append(dx_error)
                residual_hist.append(residual)
                x_hist.append(x_new.copy())
                dx_hist.append(dx.copy())

                if residual < 1e-5 and dx_error < 1e-5:
                    break

                print(
                    f'Convergence achieved for dtau={dtau:.2e}, ||dx||={dx_error:.2e}, residual={residual:.2e}, step {step_idx}')

                eps = 1e-14
                avg_residual = 0.8 * old_residual + 0.2 * residual
                ratio = (avg_residual + eps) / residual
                ratio = (old_residual + eps) / residual

                # Default scaling factor
                beta = ratio
                if beta > 1.0:
                    beta = 2
                elif beta < 1.0:
                    beta = 0.5

                # Residual increased → reduce time step
                if dx_error < tol and residual > tol:
                    print(f"Residual too big → reducing dtau and dx_error is {dx_error}")
                    dtau = 1
                    beta = 0.8
                elif abs(1 - ratio) < 1e-5 and step_idx > 100 and False:
                    # beta = 1.5
                    print("System stalled → increasing dtau ")
                elif len(dtau_hist) > 2 and abs(1 - dtau_hist[-1] / dtau_hist[-2]) < 1e-3 and dtau_hist[
                    -1] < dtau_max and step_idx > 100 and False:
                    # beta = 1.5
                    print("System stalled → increasing dtau ")
                elif residual < tol:
                    beta = 5
                    print("Residual already small → increasing dtau ")
                else:
                    # beta = np.clip(ratio, 0.5, 2.0)
                    _ = 0

                if residual < tol and dx_error < tol:
                    beta = 2
                    if np.abs(1 - dtau / h) < 1e-1:
                        break
                    elif (dtau * beta - h) * (beta - h) < 0:
                        dtau = h
                    elif (dtau / beta - h) * (beta - h) < 0:
                        dtau = h
                    elif dtau > h:
                        dtau /= beta
                    else:
                        dtau *= beta
                    beta = 1

                # beta = ratio
                print(f'Updating dtau: {dtau} * {beta}')
                beta = min(max(0.5, beta), 2)
                if residual < tol:
                    beta = 2
                    print("Residual already small → increasing dtau ")

                print(f'Updating dtau: {dtau} * {beta}')
                if dtau > 0:
                    dtau = min(dtau_max, max(dtau_min, dtau * beta))
                else:
                    dtau = -min(dtau_max, max(dtau_min, -dtau * beta))
                print(f'Updated dtau: {dtau}')

                # update lags
                for i, lag_var in enumerate(self._lag_vars):
                    if lag_var.lag == 0:
                        uid = lag_var.base_var.uid
                        idx = self.uid2idx_vars[uid]
                        lag[i] = x_new[idx]
                    elif step_idx + 1 - (lag_var.lag - 1) >= 0:
                        uid = lag_var.base_var.uid
                        idx = self.uid2idx_vars[uid]
                        lag[i] = y[-1 - lag_var.lag, idx]
                    else:
                        lag_name = lag_var.base_var.name + '_lag_' + str(lag_var.lag - 1)
                        next_lag_var = LagVar.get_or_create(lag_name, base_var=lag_var.base_var, lag=lag_var.lag - 1)
                        uid = next_lag_var.uid
                        idx = self.uid2idx_lag[uid]
                        lag[i] = lag[idx]
                old_residual = residual
                old_dx_error = dx_error
                x_old_iter = np.r_[x_new, lag]

            elif tries > max_tries:
                print(f'failed with dtau = {dtau}')
                raise ConvergenceError(f"Max tries reached at dtau={dtau:.2e}, residual={residual:.2e}")

        init_guess = {var: x_new[self.uid2idx_vars[var.uid]] for var in self._algebraic_vars}

        if not plot:
            return x_new, init_guess
        # --- Plotting section ---
        fig, axs = plt.subplots(3, 1, figsize=(8, 10), sharex=True)

        axs[0].semilogy(dx_error_hist, label="||dx||")
        axs[0].set_ylabel("dx error (log)")
        axs[0].legend()

        axs[1].semilogy(residual_hist, label="Residual norm")
        axs[1].set_ylabel("Residual (log)")
        axs[1].legend()

        axs[2].semilogy(dtau_hist, label="dtau")
        axs[2].set_ylabel("dtau")
        axs[2].set_xlabel("Step index")
        axs[2].legend()

        # --- Plot actual variables ---
        x_hist = np.array(x_hist)  # shape: (n_steps, n_vars)
        dx_hist = np.array(dx_hist)  # shape: (n_steps, n_vars)

        nvars = len(self._algebraic_vars)
        vars_per_plot = 5
        nplots = (nvars + vars_per_plot - 1) // vars_per_plot

        fig, axs = plt.subplots(nplots, 1, figsize=(10, 2.5 * nplots), sharex=True)

        # if there’s only one subplot, axs won’t be a list
        if nplots == 1:
            axs = [axs]
        if x_hist.ndim == 1:
            # print('Pseudo Transient finished')
            return x_new, init_guess

        for i in range(nplots):
            start = i * vars_per_plot
            end = min((i + 1) * vars_per_plot, nvars)
            for var in self._algebraic_vars[start:end]:
                axs[i].plot(x_hist[:, self.uid2idx_vars[var.uid]], label=var.name)
            axs[i].set_ylabel("Value")
            axs[i].legend(loc="best", fontsize="x-small", ncol=2, frameon=False)
        axs[-1].set_xlabel("Step index")

        nvars = len(self._diff_vars)
        vars_per_plot = 5
        nplots = (nvars + vars_per_plot - 1) // vars_per_plot

        fig, axs = plt.subplots(nplots, 1, figsize=(10, 2.5 * nplots), sharex=True)
        if nplots == 1:
            axs = [axs]

        for i in range(nplots):
            start = i * vars_per_plot
            end = min((i + 1) * vars_per_plot, nvars)
            for var in self._diff_vars[start:end]:
                axs[i].plot(dx_hist[:, self.uid2idx_diff[var.uid]], label=f"d{var.base_var.name}")
            axs[i].set_ylabel("dx")
            axs[i].set_yscale("symlog")
            axs[i].legend(loc="best", fontsize="x-small", ncol=2, frameon=False)
        axs[-1].set_xlabel("Step index")
        plt.tight_layout()
        plt.show()
        # print('Pseudo Transient finished')

        return x_new, init_guess

    def pseudo_transient_daes(self, x0, init_guess= dict(), plot=True, dtau0=1e-3, h=1e-3, beta=0.8, tol=1e-5,
                              predictor=False, max_iter: float = 8e4, max_tries=200, verbose=False):
        # Init pseudo transient method, Block only has algebraic eqs
        lag = np.zeros(len(self.uid2idx_lag))
        dtau = dtau0
        init_guess_uid = [var.uid for var in init_guess.keys()]

        for var in self._algebraic_vars:
            if not var.uid in init_guess_uid:
                continue
            idx = self.uid2idx_vars[var.uid]
            x0[idx] = init_guess[var]
        for i in range(len(x0)):
            if x0[i] == 0:
                _ = 0
                x0[i] = 0.1 + 0.5 * np.random.rand()
        for i in range(len(lag)):
            base_var = self._lag_vars[i].base_var
            lag[i] = x0[self.uid2idx_vars[base_var.uid]]
            if lag[i] == 0:
                lag[i] += 0.1 + np.random.rand()

        y = np.empty((5, self._n_vars))
        step_idx = 0
        x_new = x0.copy()
        tries = 0
        current_time = 0
        params_current = self._params_fn(float(current_time))
        params_outer = params_current.copy()
        params_outer[-1] = 1e-3
        dx_error = 1
        residual = 10
        newton_residual = 10
        old_residual = 10

        # history containers
        dtau_hist = []
        dx_error_hist = []
        residual_hist = []
        x_hist = []
        dx_hist = []

        x_old_iter = np.r_[x_new, lag]
        while step_idx < max_iter:
            xn = y[-1]
            params_current[-1] = dtau

            xn_lags = np.r_[xn, lag]
            xnew_lags = np.r_[x_new, lag]
            rhs = self.rhs_implicit(xnew_lags, xn_lags, params_current, 1, dtau)
            if verbose:
                print(f'Pseudo transient step started with max_iter {max_iter} and step idx {step_idx} and try {tries}')
            if tries > 1:
                x_predicted, x_feasible = self.predictor(x_old=xnew_lags, max_step=5e3, params=params_current)
            else:
                x_predicted, x_feasible = self.predictor(x_old=x_old_iter, max_step=5e3, params=params_current)
            for i in range(1):
                _ = 0
                if tries > 1:
                    x_corrected, x_feasible = self.corrector(x_predicted, x_feasible, x_feasible, params_current)
                else:
                    x_corrected, x_feasible = self.corrector(x_predicted, x_old_iter, x_feasible, params_current)
                x_predicted = x_corrected
            xnew_lags[:len(x_feasible)] = x_feasible
            # 1 Handle first-order derivatives first
            for i, var in enumerate(self._diff_vars):
                if var.diff_order != 1:
                    continue
                base_var_uid = self.uid2idx_vars[var.base_var.uid]
                xnew_lags[base_var_uid] = x_predicted[i]

            newton_residual = np.linalg.norm(rhs)
            converged = newton_residual < tol
            if verbose:
                _ = 0
                print(f'residual is {rhs} try is {tries} and x is {x_new}')

            step_idx += 1
            y = np.roll(y, shift=-1, axis=0)
            alpha = 1.0
            if step_idx > 2:
                y[-1] = alpha * x_new + (1 - alpha) * y[-1]
            else:
                y[-1] = alpha * x_new
            x_new = y[-1]

            # save history
            rhs = self.rhs_implicit(xnew_lags, xn_lags, params_outer, 1, dtau)
            dtau_hist.append(dtau)
            dx_hist.append(self.compute_dx(x_new, lag, dtau).copy())
            dx_error_hist.append(np.linalg.norm(dx_hist[-1]))
            residual_hist.append(np.linalg.norm(rhs))
            x_hist.append(x_new.copy())
            print(
                f'Convergence achieved for dtau={dtau:.2e}, ||dx||={dx_error:.2e}, residual={residual:.2e}, step {step_idx}')

            for i, lag_var in enumerate(self._lag_vars):
                if lag_var.lag == 0:
                    uid = lag_var.base_var.uid
                    idx = self.uid2idx_vars[uid]
                    lag[i] = x_new[idx]
                elif step_idx + 1 - (lag_var.lag - 1) >= 0:
                    uid = lag_var.base_var.uid
                    idx = self.uid2idx_vars[uid]
                    lag[i] = y[-1 - lag_var.lag, idx]
                else:
                    lag_name = lag_var.base_var.name + '_lag_' + str(lag_var.lag - 1)
                    next_lag_var = LagVar.get_or_create(lag_name, base_var=lag_var.base_var, lag=lag_var.lag - 1)
                    uid = next_lag_var.uid
                    idx = self.uid2idx_lag[uid]
                    lag[i] = lag[idx]
            old_residual = residual
            x_old_iter = np.r_[x_new, lag]

            if converged:
                break
            elif tries > max_tries:
                raise ConvergenceError(f"Max tries reached at dtau={dtau:.2e}, residual={residual:.2e}")

        init_guess = {var: x_new[self.uid2idx_vars[var.uid]] for var in self._algebraic_vars}

        if not plot:
            return x_new, init_guess
        # --- Plotting section ---
        fig, axs = plt.subplots(3, 1, figsize=(8, 10), sharex=True)

        axs[0].semilogy(dx_error_hist, label="||dx||")
        axs[0].set_ylabel("dx error (log)")
        axs[0].legend()

        axs[1].semilogy(residual_hist, label="Residual norm")
        axs[1].set_ylabel("Residual (log)")
        axs[1].legend()

        axs[2].semilogy(dtau_hist, label="dtau")
        axs[2].set_ylabel("dtau")
        axs[2].set_xlabel("Step index")
        axs[2].legend()

        # --- Plot actual variables ---
        x_hist = np.array(x_hist)  # shape: (n_steps, n_vars)
        dx_hist = np.array(dx_hist)  # shape: (n_steps, n_vars)

        nvars = len(self._algebraic_vars)
        vars_per_plot = 5
        nplots = (nvars + vars_per_plot - 1) // vars_per_plot

        fig, axs = plt.subplots(nplots, 1, figsize=(10, 2.5 * nplots), sharex=True)

        # if there’s only one subplot, axs won’t be a list
        if nplots == 1:
            axs = [axs]
        if x_hist.ndim == 1:
            # print('Pseudo Transient finished')
            return x_new, init_guess

        for i in range(nplots):
            start = i * vars_per_plot
            end = min((i + 1) * vars_per_plot, nvars)
            for var in self._algebraic_vars[start:end]:
                axs[i].plot(x_hist[:, self.uid2idx_vars[var.uid]], label=var.name)
            axs[i].set_ylabel("Value")
            axs[i].legend(loc="best", fontsize="x-small", ncol=2, frameon=False)
        axs[-1].set_xlabel("Step index")

        nvars = len(self._diff_vars)
        vars_per_plot = 5
        nplots = (nvars + vars_per_plot - 1) // vars_per_plot

        fig, axs = plt.subplots(nplots, 1, figsize=(10, 2.5 * nplots), sharex=True)
        if nplots == 1:
            axs = [axs]

        for i in range(nplots):
            start = i * vars_per_plot
            end = min((i + 1) * vars_per_plot, nvars)
            for var in self._diff_vars[start:end]:
                axs[i].plot(dx_hist[:, self.uid2idx_diff[var.uid]], label=f"d{var.base_var.name}")
            axs[i].set_ylabel("dx")
            axs[i].legend(loc="best", fontsize="x-small", ncol=2, frameon=False)
        axs[-1].set_xlabel("Step index")
        plt.tight_layout()
        plt.show()
        # print('Pseudo Transient finished')

        return x_new, init_guess

    def pseudo_transient_explicit(self, x0, init_guess={}, plot=True, dtau0=1e0, h=1e-3, beta=0.8, tol=1e-5,
                                  predictor=False, max_iter=8e4, max_tries=200, verbose=False):
        # Init pseudo transient method, Block only has algebraic eqs
        if self._n_state == 0:
            raise ('System is not in explicit form')
        lag = np.zeros(len(self.uid2idx_lag))
        dtau = dtau0
        init_guess_uid = [var.uid for var in init_guess.keys()]

        for var in self._algebraic_vars:
            if not var.uid in init_guess_uid:
                continue
            idx = self.uid2idx_vars[var.uid]
            x0[idx] = init_guess[var]
        for i in range(len(x0)):
            if x0[i] == 0:
                _ = 0
                x0[i] = 0.1 + 0.5 * np.random.rand()
        for i in range(len(lag)):
            base_var = self._lag_vars[i].base_var
            lag[i] = x0[self.uid2idx_vars[base_var.uid]]
            if lag[i] == 0:
                lag[i] += 0.1 + np.random.rand()

        y = np.empty((5, self._n_vars))
        step_idx = 0
        x_new = x0.copy()
        tries = 0
        current_time = 0
        params_current = self._params_fn(float(current_time))
        params_outer = params_current.copy()
        params_outer[-1] = 1e-3
        dx_error = 1
        residual = 10
        newton_residual = 10
        old_residual = 10

        # history containers
        dtau_hist = []
        dx_error_hist = []
        residual_hist = []
        x_hist = []
        dx_hist = []

        x_old_iter = np.r_[x_new, lag]
        while step_idx < max_iter:
            xn = y[-1]
            params_current[-1] = dtau

            xn_lags = np.r_[xn, lag]
            xnew_lags = np.r_[x_new, lag]
            rhs = self.rhs_implicit(xnew_lags, xn_lags, params_current, 1, dtau)
            if verbose:
                print(f'Pseudo transient step started with max_iter {max_iter} and step idx {step_idx} and try {tries}')
            if tries > 1:
                x_predicted, x_feasible = self.predictor(x_old=xnew_lags, max_step=5e3, params=params_current)
            else:
                x_predicted, x_feasible = self.predictor(x_old=x_old_iter, max_step=5e3, params=params_current)
            for i in range(1):
                _ = 0
                if tries > 1:
                    x_corrected, x_feasible = self.corrector(x_predicted, x_feasible, x_feasible, params_current)
                else:
                    x_corrected, x_feasible = self.corrector(x_predicted, x_old_iter, x_feasible, params_current)
                x_predicted = x_corrected
            xnew_lags[:len(x_feasible)] = x_feasible
            # 1 Handle first-order derivatives first
            for i, var in enumerate(self._diff_vars):
                if var.diff_order != 1:
                    continue
                base_var_uid = self.uid2idx_vars[var.base_var.uid]
                xnew_lags[base_var_uid] = x_predicted[i]

            newton_residual = np.linalg.norm(rhs)
            converged = newton_residual < tol
            if verbose:
                _ = 0
                print(f'residual is {rhs} try is {tries} and x is {x_new}')

            step_idx += 1
            y = np.roll(y, shift=-1, axis=0)
            alpha = 1.0
            if step_idx > 2:
                y[-1] = alpha * x_new + (1 - alpha) * y[-1]
            else:
                y[-1] = alpha * x_new
            x_new = y[-1]

            # save history
            rhs = self.rhs_implicit(xnew_lags, xn_lags, params_outer, 1, dtau)
            dtau_hist.append(dtau)
            dx_hist.append(self.compute_dx(x_new, lag, dtau).copy())
            dx_error_hist.append(np.linalg.norm(dx_hist[-1]))
            residual_hist.append(np.linalg.norm(rhs))
            x_hist.append(x_new.copy())
            print(
                f'Convergence achieved for dtau={dtau:.2e}, ||dx||={dx_error:.2e}, residual={residual:.2e}, step {step_idx}')

            for i, lag_var in enumerate(self._lag_vars):
                if lag_var.lag == 0:
                    uid = lag_var.base_var.uid
                    idx = self.uid2idx_vars[uid]
                    lag[i] = x_new[idx]
                elif step_idx + 1 - (lag_var.lag - 1) >= 0:
                    uid = lag_var.base_var.uid
                    idx = self.uid2idx_vars[uid]
                    lag[i] = y[-1 - lag_var.lag, idx]
                else:
                    lag_name = lag_var.base_var.name + '_lag_' + str(lag_var.lag - 1)
                    next_lag_var = LagVar.get_or_create(lag_name, base_var=lag_var.base_var, lag=lag_var.lag - 1)
                    uid = next_lag_var.uid
                    idx = self.uid2idx_lag[uid]
                    lag[i] = lag[idx]
            old_residual = residual
            x_old_iter = np.r_[x_new, lag]

            if converged:
                break
            elif tries > max_tries:
                raise ConvergenceError(f"Max tries reached at dtau={dtau:.2e}, residual={residual:.2e}")

        init_guess = {var: x_new[self.uid2idx_vars[var.uid]] for var in self._algebraic_vars}

        if not plot:
            return x_new, init_guess
        # --- Plotting section ---
        fig, axs = plt.subplots(3, 1, figsize=(8, 10), sharex=True)

        axs[0].semilogy(dx_error_hist, label="||dx||")
        axs[0].set_ylabel("dx error (log)")
        axs[0].legend()

        axs[1].semilogy(residual_hist, label="Residual norm")
        axs[1].set_ylabel("Residual (log)")
        axs[1].legend()

        axs[2].semilogy(dtau_hist, label="dtau")
        axs[2].set_ylabel("dtau")
        axs[2].set_xlabel("Step index")
        axs[2].legend()

        # --- Plot actual variables ---
        x_hist = np.array(x_hist)  # shape: (n_steps, n_vars)
        dx_hist = np.array(dx_hist)  # shape: (n_steps, n_vars)

        nvars = len(self._algebraic_vars)
        vars_per_plot = 5
        nplots = (nvars + vars_per_plot - 1) // vars_per_plot

        fig, axs = plt.subplots(nplots, 1, figsize=(10, 2.5 * nplots), sharex=True)

        # if there’s only one subplot, axs won’t be a list
        if nplots == 1:
            axs = [axs]
        if x_hist.ndim == 1:
            # print('Pseudo Transient finished')
            return x_new, init_guess

        for i in range(nplots):
            start = i * vars_per_plot
            end = min((i + 1) * vars_per_plot, nvars)
            for var in self._algebraic_vars[start:end]:
                axs[i].plot(x_hist[:, self.uid2idx_vars[var.uid]], label=var.name)
            axs[i].set_ylabel("Value")
            axs[i].legend(loc="best", fontsize="x-small", ncol=2, frameon=False)
        axs[-1].set_xlabel("Step index")

        nvars = len(self._diff_vars)
        vars_per_plot = 5
        nplots = (nvars + vars_per_plot - 1) // vars_per_plot

        fig, axs = plt.subplots(nplots, 1, figsize=(10, 2.5 * nplots), sharex=True)
        if nplots == 1:
            axs = [axs]

        for i in range(nplots):
            start = i * vars_per_plot
            end = min((i + 1) * vars_per_plot, nvars)
            for var in self._diff_vars[start:end]:
                axs[i].plot(dx_hist[:, self.uid2idx_diff[var.uid]], label=f"d{var.base_var.name}")
            axs[i].set_ylabel("dx")
            axs[i].legend(loc="best", fontsize="x-small", ncol=2, frameon=False)
        axs[-1].set_xlabel("Step index")
        plt.tight_layout()
        plt.show()
        # print('Pseudo Transient finished')

        return x_new, init_guess

    def compile_implicit_predictor(self):

        uid2sym_diffvars = dict()
        uid2sym_vars = self.uid2sym_vars.copy()
        uid2sym_params = self.uid2sym_params.copy()
        uid2sym_params_predictor = self.uid2sym_params.copy()

        i = 0
        j = len(uid2sym_params)
        for ep in self._diff_vars:
            uid2sym_diffvars[ep.uid] = f"vars[{i}]"
            uid2sym_params[ep.uid] = f"params[{j}]"
            i += 1
            j += 1

        j = len(uid2sym_params_predictor)
        for ep in self._algebraic_vars:
            uid2sym_params_predictor[ep.uid] = f"params[{j}]"
            j += 1

        self._rhs_predictor = _compile_equations(eqs=self._algebraic_eqs, uid2sym_vars=uid2sym_vars,
                                                 uid2sym_params=uid2sym_params)

        self._Jf_predictor = self._get_jacobian(eqs=self._algebraic_eqs, variables=self._diff_vars,
                                                uid2sym_vars=uid2sym_diffvars,
                                                uid2sym_params=uid2sym_params_predictor, dt=self.dt, substitute=False)

        self._algebraic_eqs_stable = []
        self._diff_eq_index = []
        for i, eq in enumerate(self._algebraic_eqs):
            eq_save = eq
            for diff_var in self._diff_vars:
                eq = eq.subs({diff_var: Const(0)})
            if str(eq_save) != str(eq):
                continue
            eq = eq.simplify()
            self._algebraic_eqs_stable.append(eq)
            self._diff_eq_index.append(i)

        print(len(self._algebraic_eqs_stable))
        self._Jf_feasible = self._get_jacobian(eqs=self._algebraic_eqs_stable, variables=self._algebraic_vars,
                                               uid2sym_vars=self.uid2sym_vars,
                                               uid2sym_params=self.uid2sym_params, dt=self.dt, substitute=False)
        self._rhs_feasible = _compile_equations(eqs=self._algebraic_eqs_stable, uid2sym_vars=self.uid2sym_vars,
                                                uid2sym_params=self.uid2sym_params)

        def rhs_predictor(x_new, x_old, params):
            dt = params[-1]
            dx = np.zeros(len(self._diff_vars))
            x_aux = np.zeros(len(self.uid2sym_vars))
            x_aux[:len(x_old)] = x_old
            for i, var in enumerate(self._diff_vars):
                id = self.uid2idx_vars[var.origin_var.uid]
                if var.base_var.uid == var.origin_var.uid:
                    dx[i] = (x_new[i] - x_old[id]) / dt
                else:
                    xold_expression, _ = var.approximation_expr(dt, lag_can_be_0=False)
                    vars_to_substitute = [var.origin_var]
                    vars_to_substitute += [LagVar.get_or_create(name='a', base_var=var.origin_var, lag=i) for i in
                                           range(1, var.diff_order + 1)]
                    subs = {}
                    for var_to_sub in vars_to_substitute:
                        var_idx = self.uid2idx_vars[var_to_sub.uid]
                        subs[var_to_sub] = Const(x_old[var_idx])
                    xold_value = xold_expression.subs(subs).simplify().value
                    dx[i] = (x_new[i] - xold_value) / dt

            params = np.r_[params, dx]
            rhs = self._rhs_predictor(x_aux, params)
            return rhs

        def Jf_predictor(x_new, x_old, params):
            dt = params[-1]
            dx = np.zeros(len(self._diff_vars))
            for i, var in enumerate(self._diff_vars):
                id = self.uid2idx_vars[var.origin_var.uid]
                if var.base_var.uid == var.origin_var.uid:
                    dx[i] = (x_new[i] - x_old[id]) / dt
                else:
                    xold_expression, _ = var.approximation_expr(dt, lag_can_be_0=False)
                    vars_to_substitute = [var.origin_var]
                    vars_to_substitute += [LagVar.get_or_create(name='a', base_var=var.origin_var, lag=i) for i in
                                           range(1, var.diff_order + 1)]
                    subs = {}
                    for var_to_sub in vars_to_substitute:
                        var_idx = self.uid2idx_vars[var_to_sub.uid]
                        subs[var_to_sub] = Const(x_old[var_idx])
                    xold_value = xold_expression.subs(subs).simplify().value
                    dx[i] = (x_new[i] - xold_value) / dt

            x_old = x_old[:self._n_alg]
            params = np.r_[params, x_old]
            Jf = self._Jf_predictor(dx, params) * (1 / dt)
            return Jf

        def rhs_corrector(x_new, x_mid, x_old, params):
            dt = params[-1]
            dx = np.zeros(len(self._diff_vars))
            x_aux = np.zeros(len(self.uid2sym_vars))
            x_aux[:len(x_mid)] = x_mid
            for i, var in enumerate(self._diff_vars):
                id = self.uid2idx_vars[var.origin_var.uid]
                if var.base_var.uid == var.origin_var.uid:
                    dx[i] = (x_new[i] - x_old[id]) / dt
                else:
                    xold_expression = var.approximation_expr(dt)
                    vars_to_substitute = [var.origin_var]
                    vars_to_substitute += [LagVar.get_or_create(base_var=var.origin_var, lag=i) for i in
                                           range(1, var.diff_order + 1)]
                    subs = {}
                    for var_to_sub in vars_to_substitute:
                        var_idx = self.uid2idx_vars[var_to_sub.uid]
                        subs[var_to_sub] = x_old[var_idx]
                    xold_value = xold_expression.subs(subs).simplify()
                    dx[i] = (x_new[i] - xold_value) / dt

            params = np.r_[params, dx]
            rhs = self._rhs_predictor(x_aux, params)
            return rhs

        def Jf_corrector(x_new, x_mid, x_old, params):
            dt = params[-1]
            dx = np.zeros(len(self._diff_vars))
            for i, var in enumerate(self._diff_vars):
                id = self.uid2idx_vars[var.origin_var.uid]
                if var.base_var.uid == var.origin_var.uid:
                    dx[i] = (x_new[i] - x_old[id]) / dt
                else:
                    xold_expression = var.approximation_expr(dt)
                    vars_to_substitute = [var.origin_var]
                    vars_to_substitute += [LagVar.get_or_create(base_var=var.origin_var, lag=i) for i in
                                           range(1, var.diff_order + 1)]
                    subs = {}
                    for var_to_sub in vars_to_substitute:
                        var_idx = self.uid2idx_vars[var_to_sub.uid]
                        subs[var_to_sub] = x_old[var_idx]
                    xold_value = xold_expression.subs(subs).simplify()
                    dx[i] = (x_new[i] - xold_value) / dt

            x_mid = x_mid[:self._n_alg]
            params = np.r_[params, x_mid]
            Jf = self._Jf_predictor(dx, params) * (1 / dt)
            return Jf

        def Jf_feasible(x, params):
            x_aux = np.zeros(len(self.uid2sym_vars))
            x_aux[:len(x)] = x
            Jf = self._Jf_feasible(x_aux, params)
            return Jf

        def rhs_feasible(x, params):
            x_aux = np.zeros(len(self.uid2sym_vars))
            x_aux[:len(x)] = x
            rhs = self._rhs_feasible(x_aux, params)
            return rhs

        def Jf_with_fix_x(x, params, fix_idx):
            # Create an auxiliary array (same length as the full set of variables)
            fix_idx = np.array(fix_idx)
            x_aux = np.zeros(len(self.uid2sym_vars))
            x_aux[:len(x)] = x  # Fill with the given values of x

            # Compute the full Jacobian
            Jf = self._Jf_feasible(x_aux, params)

            # Sparse case → mask unwanted columns
            Jf = Jf.tocsc()
            mask = np.ones(Jf.shape[1], dtype=bool)
            mask[fix_idx] = False

            # Keep only the non-fixed columns
            Jf_reduced = Jf[:, mask]

            return Jf_reduced

        self.rhs_predictor = rhs_predictor
        self.Jf_predictor = Jf_predictor
        self.Jf_feasible = Jf_feasible
        self.rhs_feasible = rhs_feasible
        self.Jf_corrector = Jf_corrector
        self.rhs_corrector = rhs_corrector
        self.Jf_feasible_fixed_x = Jf_with_fix_x

        # print("Predictor-Corrector Compiled")
        return

    def find_feasible_point(self, xn, params, x0=None, max_steps=2e3, tol=1e-4):
        residual = 10
        h = 1e-3
        dt = params[-1]
        j = 0
        if len(xn) == self._n_diff:
            if x0 is None:
                print('xo is random.')
                xaux = np.random.rand(self._n_alg)
            else:
                xaux = x0
                # 1 Handle first-order derivatives first
                for i, var in enumerate(self._diff_vars):
                    if var.diff_order != 1:
                        continue
                    base_var_uid = self.uid2idx_vars[var.base_var.uid]
                    xaux[base_var_uid] = xn[i]

                # 2 Sort differential variables by diff_order before building lags
                diff_vars_sorted = sorted(self._diff_vars, key=lambda v: v.diff_order)

                # 3 Build lag variables in increasing order of diff_order
                for i, var in enumerate(diff_vars_sorted):
                    if var.diff_order <= 1:
                        continue

                    origin_var = var.origin_var
                    diff_order = var.diff_order

                    # Previous lag (order-1)
                    prev_lag = LagVar.get_or_create(
                        name=f"{origin_var.name}_lag{diff_order - 1}",
                        base_var=origin_var,
                        lag=diff_order - 1,
                    )
                    prev_lag_uid = self.uid2idx_vars[prev_lag.uid]

                    # Current lag
                    lag_var = LagVar.get_or_create(
                        name=f"{origin_var.name}_lag{diff_order}",
                        base_var=origin_var,
                        lag=diff_order,
                    )
                    lag_uid = self.uid2idx_vars[lag_var.uid]

                    # Recursive lag update: x_lag_n = x_lag_(n-1) − h * x^(n)
                    xaux[lag_uid] = xaux[prev_lag_uid] - params[-1] * xn[i]

                xn = xaux
        elif len(xn) == self._n_alg:
            _ = 0
        else:
            raise Exception('Length of xn is not n_diff or n_alg')

        for i in range(len(xn)):
            if xn[i] == 0:
                xn[i] += 0.2 * np.random.rand()
        if not hasattr(self, 'Jf_feasible'):
            self.compile_implicit_predictor()

        alpha = 1
        step = 0
        while residual > tol and step < max_steps:
            x_old = xn
            j += 1
            lags = np.random.rand(len(self._lag_vars))
            x = np.r_[xn, lags]
            # print(f'x is {x}')
            rhs = self.rhs_feasible(x, params)
            Jf = self.Jf_feasible(x, params)
            delta = sp.linalg.lsqr(Jf, -rhs)[0]
            # print(f'delta is {len(delta)}')
            xn += delta
            xn = alpha * xn + (1 - alpha) * x_old
            rhs = self.rhs_feasible(x, params)
            residual = np.linalg.norm(rhs)
            ##print(f'residual is {residual}, step is {step}')
            step += 1

        if residual < tol:
            print(f'Feasible point found')
        else:
            print(f'Feasible solver failed')

        xn_aux = np.zeros(self._n_vars)
        xn_aux[:len(xn)] = xn
        for i, var in enumerate(self._diff_vars):
            if var.diff_order > 1:
                continue
            id = self.uid2idx_vars[var.origin_var.uid]
            xn_aux[id] = xn[id]
        for lag_var in self._lag_vars:
            lag_id = self.uid2idx_lag[lag_var.uid]
            var_id = self.uid2idx_vars[lag_var.base_var.uid]
            lags[lag_id] = xn[var_id]

        xn_aux = np.r_[xn_aux, lags]
        rhs = self.rhs_implicit(xn_aux, xn_aux, params, 0, 1e-3)
        residual_implicit = np.linalg.norm(rhs)
        # print(f'End of feasible point residual is {residual}, implicit res is {residual_implicit} x_new_compl is of length {len(xn)}')
        return xn

    def build_x_y(self, x, y):
        diff_base_var_uids = [diff_var.base_var.uid for diff_var in self._diff_vars]
        res = np.zeros(len(x) + len(y))
        i_x = 0
        i_y = 0
        for var in self._algebraic_vars:
            var_id = self.uid2idx_vars[var.uid]
            if var.uid in diff_base_var_uids:
                res[var_id] = x[i_x]
                i_x += 1
            else:
                res[var_id] = y[i_y]
                i_y += 1

        return res

    def find_feasible_given_x(self, x, x_old, params, max_steps=5e3, tol=1e-3):
        residual = 10
        h = 1e-3
        j = 0
        diff_base_vars = [diff_var.origin_var for diff_var in self._diff_vars]
        diff_base_vars_uid = [diff_var.base_var.uid for diff_var in self._diff_vars]
        x_index = [self.uid2idx_vars[var.uid] for var in diff_base_vars]
        y_index = [i for i in range(self._n_alg) if i not in x_index]

        y = np.ones(self._n_alg - len(x))
        i_xold = 0
        for var in self._algebraic_vars:
            if var.uid in diff_base_vars_uid:
                continue
            var_id = self.uid2idx_vars[var.uid]
            y[i_xold] = x_old[var_id]
            i_xold += 1

        if not hasattr(self, 'Jf_feasible'):
            self.compile_implicit_predictor()

        alpha = 1
        step = 0
        scale = False
        regularize = False
        while residual > tol and step < max_steps:
            j += 1
            x_y = self.build_x_y(x, y)
            rhs = self.rhs_feasible(x_y, params)
            Jf = self.Jf_feasible(x_y, params)
            delta = sp.linalg.lsmr(Jf, -rhs)[0]
            x += 0.1 * delta[x_index]
            y += delta[y_index]
            residual = np.linalg.norm(rhs)

            # print(f'residual is {residual}, rhs is {rhs}, step is {step}, delta is {Jf}')
            step += 1

        if step == max_steps:
            raise Exception('Convergence algorithm failed in the allowed number of steps.')
        else:
            _ = 0
            print(f'Found feasible y(x)')
        return x_y

    def predictor(self, x_old, params, max_step=1e3, tol=1e-4):
        x_new = np.random.rand(len(self._diff_vars))
        residual = 10
        step = 0
        if not hasattr(self, 'rhs_predictor'):
            self.compile_implicit_predictor()

        x_feasible = self.find_feasible_point(x_old[:self._n_alg], params, x0=x_old[:self._n_alg])
        x_old[:len(x_feasible)] = x_feasible
        for i, var in enumerate(self._diff_vars):
            id = self.uid2idx_vars[var.origin_var.uid]
            x_new[i] = x_feasible[id]

        rhs = self.rhs_predictor(x_new, x_old, params)
        residual = np.linalg.norm(rhs)
        while residual > tol and step < max_step:
            step += 1
            rhs = self.rhs_predictor(x_new, x_old, params)
            Jf = self.Jf_predictor(x_new, x_old, params)
            delta = sp.linalg.lsqr(Jf, -rhs)[0]
            x_new += delta
            residual = np.linalg.norm(rhs)
            ##print(f'Loop Predictor residual is {residual} for step {step}')

        lags = np.zeros(len(self._lag_vars))
        lags1 = lags.copy()
        lags2 = lags.copy()
        x_aux = x_old.copy()[:self._n_alg]

        for i, var in enumerate(self._diff_vars):
            id = self.uid2idx_vars[var.origin_var.uid]
            x_feasible[id] = x_new[i]
        try:
            x_y = self.find_feasible_given_x(x_new, x_feasible, params, max_steps=1e4)
            x_y_comp = np.r_[x_y, lags]
            rhs1 = self.rhs_implicit(x_y_comp, x_y, params, 0, 1e-3)
            residual1 = np.linalg.norm(rhs1)
            # print(f'End of predictor residual is {residual1}, x_y is of length {len(x_y_comp)}')
        except:
            # print(f'Find feasible x failed')
            _ = 0

        for var in self._diff_vars:
            base_var_id = self.uid2idx_vars[var.origin_var.uid]
            diff_var_id = self.uid2idx_diff[var.uid]
            x_aux[base_var_id] = x_new[diff_var_id]
        for lag_var in self._lag_vars:
            lag_id = self.uid2idx_lag[lag_var.uid]
            var_id = self.uid2idx_vars[lag_var.base_var.uid]
            lags[lag_id] = x_old[var_id]
            lags2[lag_id] = x_aux[var_id]

        x_new_comp = np.r_[x_aux, lags]
        # x_new = x_new_comp
        # print(f'End of predictor residual is {residual2}, x_new_compl is of length {len(x_new_comp)}')
        return x_new, x_feasible

    def corrector(self, x_predicted, x_old, x_feasible, params, max_step=10, tol=1e-3):
        x_new = np.zeros(len(self._diff_vars))
        residual = 10
        x_old = x_old[:self._n_alg]
        step = 0
        x_old_limited = np.zeros(len(self._diff_vars))
        for var in self._diff_vars:
            base_var_id = self.uid2idx_vars[var.origin_var.uid]
            diff_var_id = self.uid2idx_diff[var.uid]
            x_old_limited[diff_var_id] = x_old[base_var_id]

        try:
            x_predicted = self.find_feasible_given_x(x_predicted, x_feasible, params)
        except Exception as e:
            msg = str(e)
            print(msg)
            print('given x failed')
            x_predicted = self.find_feasible_point(x_predicted, params, x0=x_feasible)
        try:
            x_old = self.find_feasible_given_x(x_old_limited, x_feasible, params)
        except:
            print('given x failed')
            x_old = self.find_feasible_point(x_old_limited, params, x0=x_feasible)
        for i, var in enumerate(self._diff_vars):
            id = self.uid2idx_vars[var.base_var.uid]
            x_new[i] = x_predicted[id]

        alpha = 1.0
        x_mid = alpha * (x_predicted) + (1 - alpha) * x_old
        lags = np.zeros(len(self._lag_vars))
        for lag_var in self._lag_vars:
            lag_id = self.uid2idx_lag[lag_var.uid]
            var_id = self.uid2idx_vars[lag_var.base_var.uid]
            lags[lag_id] = x_old[var_id]

        x_predicted_withlags = np.r_[x_predicted, lags]
        rhs = self.rhs_implicit(x_predicted_withlags, x_predicted, params, 0, 1e-3)
        residual = np.linalg.norm(rhs)

        ##print(f'x_predicted of length {len(x_predicted)}')
        # print(f'Initial corrector {residual}, x_new is of length {len(x_new)}')
        while residual > tol and step < max_step:
            rhs = self.rhs_corrector(x_new, x_mid, x_old, params)
            Jf = self.Jf_corrector(x_new, x_mid, x_old, params)
            delta = sp.linalg.lsqr(Jf, -rhs)[0]
            x_new += delta

            residual = np.linalg.norm(rhs)
            step += 1
            # print(f'Corrector Loop residual is {residual} for step {step} delta_norrm is {np.linalg.norm(delta)}, rhs is {rhs}')

        if residual > tol:
            _ = 0
            print('Corrector failed')
            return x_new, x_mid
        else:
            print('Corrector Succeeded')

        for i, var in enumerate(self._diff_vars):
            idx = self.uid2idx_vars[var.origin_var.uid]
            x_mid[idx] = x_new[i]

        return x_new, x_mid

    def fixed_point_finder(self, x0=None, tol=1e-4):
        states = set()
        states = {var.base_var for var in self._diff_vars}
        self.states = list(states)
        self.n_states = len(states)
        if x0 is None:
            xstart = np.random.rand(len(self._lag_vars))
        else:
            xstart = np.zeros(len(self._lag_vars))
            for lag in self._lag_vars:
                base_var = lag.base_var
                base_var_idx = self.uid2idx_vars[base_var.uid]
                xstart[self.uid2idx_lag[lag.uid]] = x0[base_var_idx]

        params_current = self._params_fn(float(0))
        T_operator = self.T_operator(params_current)
        residual = 10
        alpha = 0.05
        x = xstart.copy()
        while residual > tol:
            x_new = (alpha) * x + (1 - alpha) * T_operator(x)
            residual = np.linalg.norm(x_new - x)
            x = x_new
        return x

    def T_operator(self, params_current):

        def operator(lags, h=1e-3):
            residual = 10
            x_n = np.zeros(self._n_vars)
            dtau = 1e-6
            for lag in self._lag_vars:
                base_var = lag.base_var
                base_var_idx = self.uid2idx_vars[base_var.uid]
                x_n[base_var_idx] = lags[self.uid2idx_lag[lag.uid]] + 2 * np.random.rand()

            x_new = x_n.copy()

            while residual > 1e-4:
                xn_lags = np.r_[x_n, lags]
                xnew_lags = np.r_[x_new, lags]
                params_current[-1] = dtau

                rhs = self.rhs_implicit(xnew_lags, xn_lags, params_current, 1, dtau)
                Jf = self.jacobian_implicit(xnew_lags, params_current, dtau)
                delta = sp.linalg.spsolve(Jf, -rhs)

                if np.isnan(delta).any() or np.isinf(delta).any():
                    delta = sp.linalg.lsqr(Jf, -rhs)[0]

                x_new += delta
                residual = np.linalg.norm(rhs)
                # print(f'residual is {residual}')
            x_states = np.zeros(len(self._lag_vars))

            # We project onto the state variables
            # TODO: return should also be lags
            for lag in self._lag_vars:
                base_var = lag.base_var
                base_var_idx = self.uid2idx_vars[base_var.uid]
                if lag.lag == 1:
                    x_states[self.uid2idx_lag[lag.uid]] = x_new[base_var_idx]
                else:
                    lag_var = LagVar.get_or_create('name', base_var=base_var, lag=lag.lag - 1)
                    x_states[self.uid2idx_lag[lag.uid]] = lags[self.uid2idx_lag[lag_var.uid]]

            return x_states

        return operator


