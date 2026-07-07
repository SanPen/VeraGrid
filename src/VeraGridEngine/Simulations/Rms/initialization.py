# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0


import os
import warnings
from copy import deepcopy
from typing import Dict, List
import numpy as np
from collections import defaultdict, deque

from VeraGridEngine.Utils.Symbolic.jit_compiler import RMSCompiler
import scipy.sparse as sp
from scipy.sparse.linalg import MatrixRankWarning

from VeraGridEngine.Utils.Symbolic.compiled_functions import SymbolicVector, SymbolicParamsVector, SymbolicDerivative, SymbolicJacobian
from VeraGridEngine.Utils.Symbolic.symbolic import eval_uid as eval_expr_uid, get_expression_vars
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Const, Expr, find_vars_order
from VeraGridEngine.enumerations import VarPowerFlowReferenceType
from VeraGridEngine.basic_structures import Vec

def build_init_dict(mdl, init_vars, init_event):
    """
    builds initialization dictionary from mdl
    :param mdl:
    :type mdl:
    :param init_vars:
    :param init_event:
    :type init_vars:
    init_dict
    :return:
    :rtype:
    """
    init_vars.update(mdl.init_eqs)
    init_event.update(mdl.event_dict)
    for blk in mdl.children:
        build_init_dict(blk, init_vars, init_event)



def solve_secant(eq_fn, x, idx, event_params_array, params_array,
                 tol=1e-8, max_iter=50, seed: float | None = None, fallback_seed: float = 10.0):
    if seed is not None and np.isfinite(seed):
        x0 = float(seed)
    elif np.isfinite(x[idx]):
        x0 = float(x[idx])
    else:
        x0 = float(fallback_seed)

    x1 = x0 + 0.1 if abs(x0) < 1e-6 else x0 * 1.1

    for _ in range(max_iter):

        x[idx] = x0
        f0 = float(eq_fn(x, np.ones(1), event_params_array, params_array)[0]) - x0
        if not np.isfinite(f0):
            x0 = float(fallback_seed)
            x1 = x0 + 0.1 if abs(x0) < 1e-6 else x0 * 1.1
            continue

        x[idx] = x1
        f1 = float(eq_fn(x, np.ones(1), event_params_array, params_array)[0]) - x1
        if not np.isfinite(f1):
            x1 = x0 + 0.1 if abs(x0) < 1e-6 else x0 * 1.1
            continue

        if abs(f1) < tol:
            return x1

        denom = (f1 - f0)
        if abs(denom) < 1e-12:
            break

        x2 = x1 - f1 * (x1 - x0) / denom
        if not np.isfinite(x2):
            raise ValueError(
                f"Secant init produced non-finite iterate at idx={idx}: x0={x0}, x1={x1}, x2={x2}"
            )

        x0, x1 = x1, x2

    if not np.isfinite(x1):
        raise ValueError(f"Secant init failed to converge to a finite value at idx={idx}")

    return x1

def init_explicit(mdl: Block,
                  sys_vars: Dict[int, Var],
                  variable_parameters: List[Var],
                  event_parameters_eqs: List[Expr | Const],
                  constant_parameters: List[Var],
                  init_guess: Dict[int, float],
                  uid2idx_vars: Dict[int, int],
                  uid2idx_params: Dict[int, int],
                  uid2idx_event_params: Dict[int, int],
                  compiler_names_dict: Dict[int, str],
                  alias_names_dict: Dict[int, str],
                  VARIABLE_PARAMS_NAME: str,
                  TIME_NAME: str,
                  VARS_NAME: str,
                  DIFF_NAME: str,
                  CONSTANT_PARAMS_NAME: str):
    """

    initialize model using explicit equations

    :param mdl:
    :type mdl: VeraGridEngine.Utils.Symbolic.block.Block
    :param sys_vars:
    :type sys_vars: Union[List[Tuple[int, str]], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], List[Tuple[int, str]], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var], List[Tuple[int, str]], Dict[int, VeraGridEngine.Utils.Symbolic.symbolic.Var]]
    :param variable_parameters:
    :type variable_parameters: List[VeraGridEngine.Utils.Symbolic.symbolic.Var]
    :param event_parameters_eqs:
    :type event_parameters_eqs:
    :param constant_parameters:
    :type constant_parameters: List[VeraGridEngine.Utils.Symbolic.symbolic.Var]
    :param init_guess:
    :type init_guess: Dict[Tuple[int, str], float]
    :param uid2idx_vars:
    :type uid2idx_vars: Dict[int, int]
    :param uid2idx_params:
    :type uid2idx_params: Dict[int, int]
    :param uid2idx_event_params:
    :type uid2idx_event_params: Dict[int, int]
    :param compiler_names_dict:
    :type compiler_names_dict: Dict[int, str]
    :param alias_names_dict:
    :type alias_names_dict: Dict[int, str]
    :param VARIABLE_PARAMS_NAME:
    :type VARIABLE_PARAMS_NAME: str
    :param TIME_NAME:
    :type TIME_NAME: str
    :param VARS_NAME:
    :type VARS_NAME: str
    :param DIFF_NAME:
    :type DIFF_NAME: str
    :param CONSTANT_PARAMS_NAME:
    :type CONSTANT_PARAMS_NAME:
    :return:
    :rtype: Union[None, Tuple[Dict[Tuple[int, str], float], VeraGridEngine.Utils.Symbolic.block.Block]]
    """

    rms_compiler = RMSCompiler(
        variables=list(sys_vars.values()),
        diff_vars=list(),
        v_params=variable_parameters,
        c_params=constant_parameters,
        dt_var= Var("dt"),
        compiler_names_dict=compiler_names_dict
    )

    # initialize array for model variables
    x = np.ones(len(sys_vars))

    # assign initial guesses for known variables
    for uid, val in init_guess.items():
        x[uid2idx_vars[uid]] = val

    # initialize array for model params
    params_array = np.zeros(len(constant_parameters))

    # compute and assign parameters value
    for param, const in mdl.parameters.items():
        params_array[uid2idx_params[param.uid]] = const.value

    # compute and assign known event parameters value
    event_params_array = np.ones(len(variable_parameters))

    # unify event_dict and init_equations
    init_vars = dict()
    init_event = dict()
    build_init_dict(mdl, init_vars, init_event)

    for key, val in init_event.items():
        if not(isinstance(val, Const) and val.value is None):
            init_vars[key] = val
        else:
            pass

    # compute and assign missing init_vars and None event parameters

    ####################################################################################################################################

    # construct graph of dependencies
    graph = defaultdict(list)
    in_degree = defaultdict(int)

    dependencies = {}

    for var, eq in init_vars.items():

        vars_in_eq = get_expression_vars(eq)
        deps = [v for v in vars_in_eq if v in init_vars]

        dependencies[var] = deps

        for dep in deps:
            if dep.uid != var.uid:
                graph[dep].append(var)
                in_degree[var] += 1

        if var not in in_degree:
            in_degree[var] = 0

    # topological sort
    queue = deque([var for var in in_degree if in_degree[var] == 0])
    topo_order = []

    while queue:
        u = queue.popleft()
        topo_order.append(u)

        for v in graph[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    if len(topo_order) != len(init_vars):
        raise RuntimeError("Cycle detected between different variables")

    def _resolve_numeric(value):
        if isinstance(value, Var):
            if value.uid in uid2idx_event_params:
                return float(event_params_array[uid2idx_event_params[value.uid]])
            if value.uid in uid2idx_vars:
                return float(x[uid2idx_vars[value.uid]])
            if value.uid in uid2idx_params:
                return float(params_array[uid2idx_params[value.uid]])
            if value.uid in init_guess:
                return float(init_guess[value.uid])
            raise ValueError(f"Could not resolve numeric value for '{value.name}' (uid={value.uid})")

        return float(value)

    # evaluate
    for var in topo_order:
        eq = init_vars[var]
        vars_list = find_vars_order(eq)

        if var in init_event.keys():
            uid_bindings: Dict[int, float] = {}
            for vr in vars_list:
                if vr.uid in uid2idx_event_params:
                    uid_bindings.update({vr.uid: event_params_array[uid2idx_event_params[vr.uid]]})
                elif vr.uid in uid2idx_vars:
                    uid_bindings.update({vr.uid: x[uid2idx_vars[vr.uid]]})
                elif vr.uid in uid2idx_params:
                    uid_bindings.update({vr.uid: params_array[uid2idx_params[vr.uid]]})

            missing = [f"{vr.name}:{vr.uid}" for vr in vars_list if vr.uid not in uid_bindings]
            if len(missing) > 0:
                raise ValueError(
                    f"Explicit init could not evaluate event equation for '{var.name}' (uid={var.uid}). "
                    f"Missing bindings: {', '.join(missing)}"
                )

            result = eq.eval_uid(uid_bindings)
            resolved_result = _resolve_numeric(result)
            if not np.isfinite(resolved_result):
                raise ValueError(
                    f"Explicit init produced non-finite event value for '{var.name}' (uid={var.uid}): "
                    f"{resolved_result}. Equation: {eq}"
                )
            event_params_array[uid2idx_event_params[var.uid]] = resolved_result
            index = variable_parameters.index(var)
            event_parameters_eqs[index] = Const(resolved_result)
        elif var.base_var is None:
            # check if implicit equation
            is_self_implicit = var in dependencies[var]

            if not is_self_implicit:
                uid_bindings: Dict[int, float] = {}
                vars_list = find_vars_order(eq)
                for vr in vars_list:
                    if vr.uid in uid2idx_event_params:
                        uid_bindings.update({vr.uid: event_params_array[uid2idx_event_params[vr.uid]]})
                    elif vr.uid in uid2idx_vars:
                        uid_bindings.update({vr.uid: x[uid2idx_vars[vr.uid]]})
                    elif vr.uid in uid2idx_params:
                        uid_bindings.update({vr.uid: params_array[uid2idx_params[vr.uid]]})

                missing = [f"{vr.name}:{vr.uid}" for vr in vars_list if vr.uid not in uid_bindings]
                if len(missing) > 0:
                    raise ValueError(
                        f"Explicit init could not evaluate equation for '{var.name}' (uid={var.uid}). "
                        f"Missing bindings: {', '.join(missing)}"
                    )

                result = eq.eval_uid(uid_bindings)
                resolved_result = _resolve_numeric(result)
                if not np.isfinite(resolved_result):
                    raise ValueError(
                        f"Explicit init produced non-finite state/algebraic value for '{var.name}' (uid={var.uid}): "
                        f"{resolved_result}. Equation: {eq}"
                    )
                init_guess[var.uid] = resolved_result
                x[uid2idx_vars[var.uid]] = resolved_result

            else:
                # compile equations
                eq_fn = rms_compiler.compile_rhs([eq], "equation")

                idx = uid2idx_vars[var.uid]

                # solve using secant method
                init_val = solve_secant(
                    eq_fn=eq_fn,
                    x=x,
                    idx=idx,
                    event_params_array=event_params_array,
                    params_array=params_array,
                    tol=1e-8,
                    max_iter=50,
                    seed=init_guess.get(var.uid, None),
                )

                if not np.isfinite(init_val):
                    raise ValueError(
                        f"Explicit init produced non-finite implicit solve value for '{var.name}' "
                        f"(uid={var.uid}): {init_val}. Equation: {eq}"
                    )

                init_guess[var.uid] = init_val
                x[uid2idx_vars[var.uid]] = init_val

class PseudoTransientInitProblem:
    """
    Lightweight problem class for pseudo-transient initialization of a single device block.
    Similar interface to RmsProblemDae but for initialization only.
    """
    
    def __init__(self,
                 block: Block,
                 x_global: Vec,
                 compiler_names_dict: Dict[int, str],
                 alias_names_dict: Dict[int, str],
                 uid2idx_vars: Dict[int, int],
                 variable_parameters: List[Var],
                 constant_parameters: List[Var],
                 VARS_NAME: str = "vars",
                 DIFF_NAME: str = "diff",
                 VARIABLE_PARAMS_NAME: str = "vprms",
                 CONSTANT_PARAMS_NAME: str = "cprms"):
        """
        Initialize problem for pseudo-transient initialization.
        """

        self.x_global = x_global
        self.block = block
        self.compiler_names_dict = compiler_names_dict
        self.alias_names_dict = alias_names_dict
        self._uid2idx_vars_global = uid2idx_vars
        self._variable_parameters = list(variable_parameters)
        self._constant_parameters = constant_parameters
        self._event_params_fn: SymbolicParamsVector | None = None

        event_uid_map = {v.uid: eq for v, eq in block.event_dict.items()}
        mode_uid_map = {v.uid: eq for v, eq in block.mode_dict.items()}
        param_uid_map = {v.uid: c for v, c in block.parameters.items()}
        
        self.equilibrium_inputs_as_params = os.getenv(
            "VERAGRID_PSEUDO_EQUILIBRIUM_INPUTS_AS_PARAMS", "0"
        ).lower() in {"1", "true", "yes", "on"}

        equilibrium_input_uids = set()
        if self.equilibrium_inputs_as_params:
            equilibrium_input_uids = {
                v.uid for v in block.in_vars
                if isinstance(v, Var) and self._is_equilibrium_input_var(v)
            }

        # Get block's variables (state + algebraic). Generator equilibrium inputs
        # are compiled as mutable parameters, not pseudo-transient unknowns.
        self._state_vars = list(block.state_vars)
        self._algebraic_vars = [
            v for v in block.algebraic_vars
            if not (isinstance(v, Var) and v.uid in equilibrium_input_uids)
        ]

        # Ensure local init system is square whenever equations reference extra
        # free variables (commonly open controller inputs like Tm/Vf in bare
        # generator tests). Promote such vars to local algebraic unknowns.
        known_uids = {v.uid for v in self._state_vars + self._algebraic_vars if isinstance(v, Var)}
        eqs = list(block.state_eqs) + list(block.algebraic_eqs)
        for eq in eqs:
            for used_var in get_expression_vars(eq):
                if not isinstance(used_var, Var):
                    continue
                if used_var.uid in known_uids:
                    continue
                if used_var.uid in equilibrium_input_uids:
                    continue
                if used_var.uid in self.compiler_names_dict:
                    continue
                self._algebraic_vars.append(used_var)
                known_uids.add(used_var.uid)

        self._all_vars = self._state_vars + self._algebraic_vars
        self._n_vars = len(self._all_vars)
        self._n_states = len(self._state_vars)
        self._diff_vars = list(block.diff_vars)

        # Build local indexing for this block initialization problem.
        self._uid2idx_vars = {v.uid: i for i, v in enumerate(self._all_vars)}
        self._uid2idx_diff = {v.uid: i for i, v in enumerate(self._diff_vars)}

        self._compiler_names_dict_local = dict(compiler_names_dict)
        self._alias_names_dict_local = dict(alias_names_dict)

        for uid, i in self._uid2idx_vars.items():
            self._compiler_names_dict_local[uid] = f"{VARS_NAME}[{i}]"
            self._alias_names_dict_local[uid] = f"{VARS_NAME}_{i}"

        for uid, i in self._uid2idx_diff.items():
            self._compiler_names_dict_local[uid] = f"{DIFF_NAME}[{i}]"
            self._alias_names_dict_local[uid] = f"{DIFF_NAME}_{i}"

        self._equilibrium_param_indices: dict[str, int] = dict()
        for in_var in self.block.in_vars:
            if not isinstance(in_var, Var) or in_var.uid not in equilibrium_input_uids:
                continue
            pidx = self._ensure_variable_parameter(in_var)
            self._compiler_names_dict_local[in_var.uid] = f"{VARIABLE_PARAMS_NAME}[{pidx}]"
            self._alias_names_dict_local[in_var.uid] = f"{VARIABLE_PARAMS_NAME}_{pidx}"
            kind = self._equilibrium_input_kind(in_var)
            if kind is not None:
                self._equilibrium_param_indices[kind] = pidx

        # Some device-only blocks may keep open controller inputs in `in_vars`
        # (e.g. Tm/Vf for a bare generator). If those inputs are used in equations
        # but are not part of state/algebraic unknowns, ensure they still get a
        # compiler mapping by freezing them to their current numeric guess.
        for in_var in self.block.in_vars:
            if not isinstance(in_var, Var):
                continue
            if in_var.uid in self._compiler_names_dict_local:
                continue

            guessed_value = 0.0
            if in_var.uid in self._uid2idx_vars_global:
                guessed_value = float(self.x_global[self._uid2idx_vars_global[in_var.uid]])
            elif in_var in self.block.init_eqs:
                init_eq = self.block.init_eqs[in_var]
                if isinstance(init_eq, Const) and init_eq.value is not None:
                    guessed_value = float(init_eq.value)

            self._compiler_names_dict_local[in_var.uid] = repr(guessed_value)
            self._alias_names_dict_local[in_var.uid] = f"input_{in_var.uid}"
        
        # Initialize parameter arrays
        self._variable_parameters_values = np.zeros(len(self._variable_parameters), dtype=float)
        for i, p in enumerate(self._variable_parameters):
            if p.uid in event_uid_map:
                eq = event_uid_map[p.uid]
                if isinstance(eq, Const) and eq.value is not None:
                    self._variable_parameters_values[i] = float(eq.value)
            elif p.uid in mode_uid_map:
                eq = mode_uid_map[p.uid]
                if isinstance(eq, Const) and eq.value is not None:
                    self._variable_parameters_values[i] = float(eq.value)
        self._constant_params = np.array([
            (param_uid_map[p.uid].value if p.uid in param_uid_map and param_uid_map[p.uid] is not None else 0.0)
            for p in constant_parameters
        ], dtype=float)
        
        # Compile functions
        self._compile_functions(VARS_NAME, DIFF_NAME, VARIABLE_PARAMS_NAME, CONSTANT_PARAMS_NAME)
        self._compile_event_params_function(VARIABLE_PARAMS_NAME, "glob_time")
        self.update_variable_params(0.0)
        self.update_variable_params(0.0)

    @staticmethod
    def _var_name_l(var: Var) -> str:
        return var.name.lower()

    @classmethod
    def _equilibrium_input_kind(cls, var: Var) -> str | None:
        name = cls._var_name_l(var)
        if name.startswith("tm"):
            return "tm"
        if name.startswith("vf") or name.startswith("efd"):
            return "vf"
        return None

    @classmethod
    def _is_equilibrium_input_var(cls, var: Var) -> bool:
        return cls._equilibrium_input_kind(var) is not None

    def _ensure_variable_parameter(self, var: Var) -> int:
        for i, param in enumerate(self._variable_parameters):
            if isinstance(param, Var) and param.uid == var.uid:
                return i
        self._variable_parameters.append(var)
        return len(self._variable_parameters) - 1

    def _find_local_var_index(self, tokens: tuple[str, ...], *, startswith: bool = False) -> int | None:
        for i, var in enumerate(self._all_vars):
            name = self._var_name_l(var)
            if startswith:
                if any(name.startswith(tok) for tok in tokens):
                    return i
            elif any(tok in name for tok in tokens):
                return i
        return None

    def _get_parameter_value_by_name(self, names: tuple[str, ...], default: float | None = None) -> float | None:
        names_l = {n.lower() for n in names}
        for i, param in enumerate(self._constant_parameters):
            if i < len(self._constant_params) and self._var_name_l(param) in names_l:
                return float(self._constant_params[i])
        for i, param in enumerate(self._variable_parameters):
            if i < len(self._variable_parameters_values) and self._var_name_l(param) in names_l:
                return float(self._variable_parameters_values[i])
        return default

    def update_equilibrium_parameters(self, x: Vec) -> None:
        if len(self._equilibrium_param_indices) == 0 or x.size == 0:
            return

        tm_pidx = self._equilibrium_param_indices.get("tm")
        if tm_pidx is not None and tm_pidx < len(self._variable_parameters_values):
            te_idx = self._find_local_var_index(("te",), startswith=True)
            omega_idx = self._find_local_var_index(("omega",))
            d_value = self._get_parameter_value_by_name(("d",), default=0.0)
            if te_idx is not None and omega_idx is not None and te_idx < x.size and omega_idx < x.size and d_value is not None:
                self._variable_parameters_values[tm_pidx] = float(x[te_idx] + d_value * (x[omega_idx] - 1.0))

        vf_pidx = self._equilibrium_param_indices.get("vf")
        if vf_pidx is not None and vf_pidx < len(self._variable_parameters_values):
            eq1_idx = self._find_local_var_index(("eq1",))
            irpu_idx = self._find_local_var_index(("irpu",), startswith=True)
            sat_idx = self._find_local_var_index(("sat",), startswith=True)
            if irpu_idx is not None and irpu_idx < x.size:
                self._variable_parameters_values[vf_pidx] = float(x[irpu_idx])
            elif eq1_idx is not None and eq1_idx < x.size:
                sat_value = 1.0
                if sat_idx is not None and sat_idx < x.size:
                    sat_value = float(x[sat_idx])
                else:
                    sat_param = self._get_parameter_value_by_name(("sat",), default=1.0)
                    if sat_param is not None:
                        sat_value = sat_param
                self._variable_parameters_values[vf_pidx] = float(sat_value * x[eq1_idx])
    
    def _compile_functions(self, VARS_NAME: str, DIFF_NAME: str,
                           VARIABLE_PARAMS_NAME: str, CONSTANT_PARAMS_NAME: str):
        """Compile RHS and derivative functions for the block."""
        # Collect all equations
        all_eqs = list(self.block.state_eqs) + list(self.block.algebraic_eqs)
        
        # Compile RHS function
        if all_eqs:
            self._rhs_fn = SymbolicVector(
                all_eqs,
                self._compiler_names_dict_local,
                self._alias_names_dict_local,
                VARS_NAME,
                DIFF_NAME,
                VARIABLE_PARAMS_NAME,
                CONSTANT_PARAMS_NAME
            )
            self._jacobian_fn = SymbolicJacobian(
                eqs=all_eqs,
                variables=self._all_vars,
                compiler_names_dict=self._compiler_names_dict_local,
                alias_names_dict=self._alias_names_dict_local,
                VARS_NAME=VARS_NAME,
                DIFF_NAME=DIFF_NAME,
                EVENT_PARAMS_NAME=VARIABLE_PARAMS_NAME,
                PARAMS_NAME=CONSTANT_PARAMS_NAME,
                use_jit=True,
            )
        else:
            self._rhs_fn = None
            self._jacobian_fn = None
        
        # Compile derivative function
        self._derivative_fn = SymbolicDerivative(
            vars=self._all_vars,
            uid2idx_vars=self._uid2idx_vars,
            diff_vars=self._diff_vars,
            compiler_names_dict=self._compiler_names_dict_local
        )

    def _compile_event_params_function(self, VARIABLE_PARAMS_NAME: str, TIME_NAME: str) -> None:
        param_eqs: list[Expr | Const] = []
        for i, param in enumerate(self._variable_parameters):
            eq = self.block.event_dict.get(param, self.block.mode_dict.get(param))
            if eq is None:
                current = 0.0
                if i < len(self._variable_parameters_values):
                    current = float(self._variable_parameters_values[i])
                eq = Const(current)
            param_eqs.append(eq)

        self._event_params_fn = SymbolicParamsVector(
            eqs=param_eqs,
            compiler_names_dict=self._compiler_names_dict_local,
            alias_names_dict=self._alias_names_dict_local,
            EVENT_PARAMS_NAME=VARIABLE_PARAMS_NAME,
            TIME_NAME=TIME_NAME,
            use_jit=True,
        )
    
    def get_all_vars_number(self) -> int:
        return self._n_vars
    
    def get_states_number(self) -> int:
        return self._n_states
    
    def get_algebraic_var_number(self) -> int:
        return len(self._algebraic_vars)
    
    def get_diff_var_number(self) -> int:
        return len(self._diff_vars)
    
    def get_algebraic_vars(self):
        return self._algebraic_vars

    def algebraic_vars(self):
        return self._algebraic_vars

    def state_vars(self):
        return self._state_vars
    
    def rhs_algebraic(self, x: Vec, dx: Vec) -> Vec:
        """Evaluate RHS for algebraic equations."""
        if self._rhs_fn is None:
            return np.array([])

        self.update_equilibrium_parameters(x)
        full_rhs = self._rhs_fn(x, dx, self._variable_parameters_values, self._constant_params)
        # Return only algebraic part
        if self._n_states > 0:
            return full_rhs[self._n_states:]
        return full_rhs
    
    def rhs_state(self, x: Vec, dx: Vec) -> Vec:
        """Evaluate RHS for state equations."""
        if self._rhs_fn is None or self._n_states == 0:
            return np.array([])

        self.update_equilibrium_parameters(x)
        full_rhs = self._rhs_fn(x, dx, self._variable_parameters_values, self._constant_params)
        return full_rhs[:self._n_states]
    
    def get_dx(self, x: Vec, xn: Vec, dx: Vec, h: float) -> Vec:
        """Compute derivatives."""
        return self._derivative_fn(x, xn, dx, h)
    
    def update_variable_params(self, t: float):
        """Update variable parameters at time t."""
        if self._event_params_fn is None:
            return
        self._variable_parameters_values = np.array(
            self._event_params_fn(self._variable_parameters_values, float(t)),
            dtype=float,
            copy=True,
        )

    def _compute_numerical_jacobian(self, x: Vec, dx: Vec, h: float) -> sp.csc_matrix:
        """Compute Jacobian with compiled symbolic fallback to finite differences."""
        n_total = self._n_vars
        if n_total == 0:
            return sp.csc_matrix((0, 0))

        self.update_equilibrium_parameters(x)
        if self._jacobian_fn is not None:
            try:
                return self._jacobian_fn(x, dx, self._variable_parameters_values, self._constant_params, h).tocsc()
            except Exception:
                pass

        # Compute RHS at current point
        rhs = np.array(self._compute_rhs_full(x, dx, h), dtype=float, copy=True)

        # Numerical Jacobian
        base_eps = 1e-7
        J_dense = np.zeros((len(rhs), n_total))

        for j in range(n_total):
            x_perturbed = x.copy()
            step = base_eps * (1.0 + abs(float(x[j])))
            x_perturbed[j] += step
            rhs_perturbed = np.array(self._compute_rhs_full(x_perturbed, dx, h), dtype=float, copy=True)
            J_dense[:, j] = (rhs_perturbed - rhs) / step

        return sp.csc_matrix(J_dense)

    def _compute_rhs_full(self, x: Vec, dx: Vec, h: float) -> Vec:
        """Compute full RHS (state + algebraic) for Jacobian computation."""
        if self._rhs_fn is None:
            return np.array([])
        return self._rhs_fn(x, dx, self._variable_parameters_values, self._constant_params)

    def get_j11(self, x: Vec, dx: Vec, h: float) -> sp.csc_matrix:
        """Jacobian of state equations w.r.t. state variables."""
        if self._n_states == 0:
            return sp.csc_matrix((0, 0))
        J_full = self._compute_numerical_jacobian(x, dx, h)
        return J_full[:self._n_states, :self._n_states]

    def get_j12(self, x: Vec, dx: Vec, h: float) -> sp.csc_matrix:
        """Jacobian of state equations w.r.t. algebraic variables."""
        if self._n_states == 0:
            return sp.csc_matrix((0, self.get_algebraic_var_number()))
        J_full = self._compute_numerical_jacobian(x, dx, h)
        n_alg = self.get_algebraic_var_number()
        return J_full[:self._n_states, self._n_states:self._n_states + n_alg]

    def get_j21(self, x: Vec, dx: Vec, h: float) -> sp.csc_matrix:
        """Jacobian of algebraic equations w.r.t. state variables."""
        n_alg = self.get_algebraic_var_number()
        if self._n_states == 0 or n_alg == 0:
            return sp.csc_matrix((n_alg, self._n_states))
        J_full = self._compute_numerical_jacobian(x, dx, h)
        return J_full[self._n_states:, :self._n_states]

    def get_j22(self, x: Vec, dx: Vec, h: float) -> sp.csc_matrix:
        """Jacobian of algebraic equations w.r.t. algebraic variables."""
        n_alg = self.get_algebraic_var_number()
        if n_alg == 0:
            return sp.csc_matrix((0, 0))
        if self._n_states == 0:
            return self._compute_numerical_jacobian(x, dx, h)
        J_full = self._compute_numerical_jacobian(x, dx, h)
        return J_full[self._n_states:, self._n_states:self._n_states + n_alg]

    @property
    def uid2idx_vars(self):
        return self._uid2idx_vars


def init_pseudo_transient(mdl: Block,
                          sys_vars: Dict[int, Var],
                          variable_parameters: List[Var],
                          event_parameters_eqs: List[Expr | Const],
                          constant_parameters: List[Var],
                          init_guess: Dict[int, float],
                          uid2idx_vars: Dict[int, int],
                          uid2idx_params: Dict[int, int],
                          uid2idx_event_params: Dict[int, int],
                          compiler_names_dict: Dict[int, str],
                          alias_names_dict: Dict[int, str],
                          VARIABLE_PARAMS_NAME: str,
                          TIME_NAME: str,
                          VARS_NAME: str,
                          DIFF_NAME: str,
                          CONSTANT_PARAMS_NAME: str,
                          dtau0: float = 1e-3,
                          max_iter: int = 100,
                          tol: float = 1e-6,
                          verbose: bool = False):
    """
    Initialize model using pseudo-transient method.
    
    Similar interface to init_explicit but uses pseudo-transient simulation
    instead of explicit equation evaluation.
    """
    # Import here to avoid circular imports
    from VeraGridEngine.Simulations.Rms.numerical.pseudo_transient import PseudoTransient

    # Work on a copy so initialization rewrites do not alter the original model.
    mdl_work = deepcopy(mdl)
    mdl_work.unify_blocks()

    # Initialization-only stabilization: relax hard limiter bounds to avoid
    # branch-locking/flat Jacobian regions during pseudo-transient startup.
    wide_limits = {
        "Pmax": 1e3,
        "Pmin": -1e3,
        "Uo": 1e3,
        "Uc": -1e3,
        "VaMaxPu": 1e3,
        "VaMinPu": -1e3,
        "EfeMaxPu": 1e3,
        "EfeMinPu": -1e3,
        "V_oelmax": 1e3,
        "V_oelmin": -1e3,
        "V_invmax": 1e3,
        "V_invmin": -1e3,
    }

    for blk in mdl_work.get_all_blocks():
        for var, value in list(blk.event_dict.items()):
            if not isinstance(var, Var):
                continue
            if var.name not in wide_limits:
                continue
            if not isinstance(value, Const):
                continue
            blk.event_dict[var] = Const(float(wide_limits[var.name]))

    # Build global snapshot vector from current init guess.
    x_global = np.zeros(len(uid2idx_vars), dtype=float)
    for uid, val in init_guess.items():
        if uid in uid2idx_vars and val is not None:
            gidx = uid2idx_vars[uid]
            if 0 <= gidx < x_global.size:
                x_global[gidx] = float(val)

    # Force deterministic reference values across runs.
    pref_fixed = float(os.getenv("VERAGRID_INIT_PREF", "1.0316406365799007"))
    vref_fixed = float(os.getenv("VERAGRID_INIT_VREF", "1.0"))

    # Freeze PF anchors in this local model: P, Q, Vm, Va, Vdc.
    pf_var_references = [
        VarPowerFlowReferenceType.P,
        VarPowerFlowReferenceType.Q,
        VarPowerFlowReferenceType.Vm,
        VarPowerFlowReferenceType.Va,
        VarPowerFlowReferenceType.Vdc,
    ]
    for pf_ref in pf_var_references:
        if pf_ref not in mdl_work.external_mapping:
            continue
        pf_var = mdl_work.external_mapping[pf_ref]
        if not isinstance(pf_var, Var):
            continue
        if pf_var.uid not in uid2idx_vars:
            continue

        pf_val = x_global[uid2idx_vars[pf_var.uid]]

        for blk in mdl_work.get_all_blocks():
            remove_alg_idx = [i for i, v in enumerate(blk.algebraic_vars)
                              if isinstance(v, Var) and v.uid == pf_var.uid]
            for i in reversed(remove_alg_idx):
                del blk.algebraic_vars[i]

            blk.state_vars = [v for v in blk.state_vars if isinstance(v, Var) and v.uid != pf_var.uid]
            blk.diff_vars = [v for v in blk.diff_vars if isinstance(v, Var) and v.uid != pf_var.uid]

        mdl_work.update_model(pf_var, Const(pf_val))

    # Promote unresolved event parameters (Const(None)) to algebraic unknowns when init eq exists.
    for blk in mdl_work.get_all_blocks():
        unresolved = [
            var for var, value in blk.event_dict.items()
            if isinstance(var, Var) and isinstance(value, Const) and value.value is None
        ]
        for var in unresolved:
            if not any(v.uid == var.uid for v in blk.algebraic_vars):
                blk.algebraic_vars.append(var)
            del blk.event_dict[var]
    
    # Create problem for this device
    problem = PseudoTransientInitProblem(
        block=mdl_work,
        x_global=x_global,
        compiler_names_dict=compiler_names_dict,
        alias_names_dict=alias_names_dict,
        uid2idx_vars=uid2idx_vars,
        variable_parameters=variable_parameters,
        constant_parameters=constant_parameters,
        VARS_NAME=VARS_NAME,
        DIFF_NAME=DIFF_NAME,
        VARIABLE_PARAMS_NAME=VARIABLE_PARAMS_NAME,
        CONSTANT_PARAMS_NAME=CONSTANT_PARAMS_NAME
    )
    # Attach global index maps for richer diagnostics in the pseudo-transient solver.
    problem._uid2idx_params = uid2idx_params
    problem._uid2idx_event_params = uid2idx_event_params

    local_vars = list(problem._state_vars) + list(problem._algebraic_vars)
    if problem.get_all_vars_number() == 0:
        return dict(init_guess)

    # Use the existing PseudoTransient solver
    # Note: h parameter is not used for initialization, we set it to 1.0

    solver = PseudoTransient(
        problem=problem,
        h=1.0,
        dtau0=1e3,
        dtau_max=1e5,
        dtau_min=1e-5,
        tol=tol,
        max_iter=1000,
        verbose=verbose,
        reference_error_tol=-1,
        fixed_var_uids=[],
    )
    
    # Build initial guess: random baseline, then overwrite with known init_guess values.
    x0 = np.random.rand(problem.get_all_vars_number())
    for local_idx, var in enumerate(local_vars):
        if local_idx >= len(x0):
            continue
        if var.uid in init_guess and init_guess[var.uid] is not None:
            x0[local_idx] = float(init_guess[var.uid])

    # Start rotor angles close to the network reference for pseudo-transient.
    # This is only a seed; delta remains a solved state afterwards.
    delta_seed_text = os.getenv("VERAGRID_INIT_DELTA_SEED", "0.0").strip()
    delta_seed = float(delta_seed_text) if delta_seed_text != "" else None

    def _enforce_delta_seed(x_vec: np.ndarray) -> np.ndarray:
        if delta_seed is None:
            return x_vec
        x_out = np.array(x_vec, dtype=float, copy=True)
        for local_idx, var in enumerate(local_vars):
            if local_idx < len(x_out) and isinstance(var, Var) and var.name.lower().startswith("delta"):
                x_out[local_idx] = delta_seed
        return x_out

    x0 = _enforce_delta_seed(x0)

    # Seed and force freed references to deterministic constants.
    ref_fixed_values = {
        "Pm_ref": pref_fixed,
        "Pref": pref_fixed,
        "P_ref": pref_fixed,
        "UsRefPu": vref_fixed,
        "Vref": vref_fixed,
        "V_ref": vref_fixed,
        "U_ref": vref_fixed,
    }

    def _enforce_reference_values(x_vec: np.ndarray) -> np.ndarray:
        x_out = np.array(x_vec, dtype=float, copy=True)
        for local_idx, var in enumerate(local_vars):
            if local_idx >= x_out.size or not isinstance(var, Var):
                continue
            if var.name in ref_fixed_values:
                x_out[local_idx] = float(ref_fixed_values[var.name])
        return x_out

    for local_idx, var in enumerate(local_vars):
        if local_idx >= len(x0) or not isinstance(var, Var):
            continue
        if var.name == "Pm_ref":
            x0[local_idx] = pref_fixed
        elif var.name == "UsRefPu":
            x0[local_idx] = vref_fixed
    x0 = _enforce_reference_values(x0)

    # Run pseudo-transient simulation
    x0 = _enforce_reference_values(x0)
    x_solution, _ = solver.simulate(plot=bool(verbose), x0=x0)

    dx_pre = np.zeros(problem.get_diff_var_number(), dtype=float)
    rhs_pre = np.r_[problem.rhs_state(x_solution, dx_pre), problem.rhs_algebraic(x_solution, dx_pre)]
    residual_pre_inf = float(np.linalg.norm(rhs_pre, np.inf)) if rhs_pre.size > 0 else 0.0
    if verbose:
        print(f"[PseudoTransientInit] residual_inf after pseudo={residual_pre_inf:.6e}")

    # Newton-Raphson polish on f(x)=0 using pseudo-transient output as seed.
    # Here f(x) is the stacked explicit RHS [f_state(x), g_algebraic(x)] with dx=0.
    dx_newton = np.zeros(problem.get_diff_var_number(), dtype=float)
    x_nr = np.array(x_solution, dtype=float, copy=True)

    newton_max_iter = 25
    newton_tol = max(float(tol), 1e-8)
    for it in range(newton_max_iter):
        if dx_newton.size > 0:
            dx_newton = np.array(problem.get_dx(x_nr, x_nr, dx_newton, h=1.0), dtype=float, copy=True)
        rhs_nr = np.r_[problem.rhs_state(x_nr, dx_newton), problem.rhs_algebraic(x_nr, dx_newton)]
        if rhs_nr.size == 0:
            break
        if not np.all(np.isfinite(rhs_nr)):
            break

        rhs_inf = float(np.linalg.norm(rhs_nr, np.inf))
        if verbose:
            print(f"[PseudoTransientInit][Newton] iter={it} rhs_inf={rhs_inf:.6e}")
        if rhs_inf <= newton_tol:
            break

        J_nr = problem._compute_numerical_jacobian(x_nr, dx_newton, h=1.0)
        use_lsqr = False
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always", MatrixRankWarning)
                delta = sp.linalg.spsolve(J_nr, rhs_nr)
                if any(issubclass(wi.category, MatrixRankWarning) for wi in w):
                    use_lsqr = True
        except Exception:
            use_lsqr = True

        if (not use_lsqr) and (
            delta is None
            or np.size(delta) == 0
            or (not np.all(np.isfinite(delta)))
            or (float(np.linalg.norm(np.asarray(delta, dtype=float), np.inf)) == 0.0)
        ):
            use_lsqr = True

        if use_lsqr:
            lsqr_out = sp.linalg.lsqr(
                J_nr,
                rhs_nr,
                atol=1e-12,
                btol=1e-12,
                iter_lim=4 * max(1, x_nr.size),
            )
            delta = lsqr_out[0]
            if verbose:
                print(
                    "[PseudoTransientInit][Newton] spsolve fallback to lsqr: "
                    f"istop={lsqr_out[1]} itn={lsqr_out[2]} r1norm={lsqr_out[3]:.6e}"
                )

        if delta is None or np.size(delta) == 0 or not np.all(np.isfinite(delta)):
            break

        alpha = 1.0
        accepted = False
        base_inf = rhs_inf
        for _ in range(8):
            x_try = x_nr - alpha * np.asarray(delta, dtype=float)

            dx_try = dx_newton
            if dx_newton.size > 0:
                dx_try = np.array(problem.get_dx(x_try, x_try, dx_newton, h=1.0), dtype=float, copy=True)

            rhs_try = np.r_[problem.rhs_state(x_try, dx_try), problem.rhs_algebraic(x_try, dx_try)]
            if np.all(np.isfinite(rhs_try)):
                trial_inf = float(np.linalg.norm(rhs_try, np.inf))
                if trial_inf < base_inf:
                    x_nr = x_try
                    accepted = True
                    break
            alpha *= 0.5

        if not accepted:
            break

    x_solution = x_nr

    dx_post = np.zeros(problem.get_diff_var_number(), dtype=float)
    rhs_post = np.r_[problem.rhs_state(x_solution, dx_post), problem.rhs_algebraic(x_solution, dx_post)]
    residual_post_inf = float(np.linalg.norm(rhs_post, np.inf)) if rhs_post.size > 0 else 0.0
    if verbose:
        print(
            "[PseudoTransientInit] residual_inf after Newton="
            f"{residual_post_inf:.6e} (pre={residual_pre_inf:.6e})"
        )

    # Validate final residual; fail fast on poor initialization.
    dx_check = np.zeros(problem.get_diff_var_number(), dtype=float)
    rhs_state = problem.rhs_state(x_solution, dx_check)
    rhs_algeb = problem.rhs_algebraic(x_solution, dx_check)
    residual_vec = np.r_[rhs_state, rhs_algeb]

    if not np.all(np.isfinite(residual_vec)):
        bad_idx = np.where(~np.isfinite(residual_vec))[0]
        bad_vals = residual_vec[bad_idx]
        raise RuntimeError(
            f"PseudoTransient final residual has NaN/Inf: bad_idx={bad_idx.tolist()}, "
            f"bad_vals={bad_vals.tolist()}"
        )

    residual_inf = float(np.linalg.norm(residual_vec, np.inf)) if residual_vec.size > 0 else 0.0
    residual_tol = max(float(tol), 1e-6)
    if residual_inf > residual_tol:
        allow_best_effort = os.getenv("VERAGRID_ALLOW_BEST_EFFORT_INIT", "0").lower() in {"1", "true", "yes", "on"}
        if allow_best_effort:
            print(
                "[PseudoTransientInit] WARNING: returning best-effort init despite residual guard: "
                f"||r||_inf={residual_inf:.6e} > {residual_tol:.6e}"
            )
        else:
            raise RuntimeError(
                f"PseudoTransient final residual too large: "
                f"||r||_inf={residual_inf:.6e} > {residual_tol:.6e}; "
                f"pre_newton={residual_pre_inf:.6e}, post_newton={residual_post_inf:.6e}"
            )

    # Update recovered values:
    # - system variables go to init_guess
    # - promoted runtime parameters go back to event_parameters_eqs as Const
    for local_idx, var in enumerate(local_vars):
        if local_idx >= len(x_solution):
            continue

        value = float(x_solution[local_idx])

        if var.uid in uid2idx_vars:
            init_guess[var.uid] = value
        elif var.uid in uid2idx_event_params:
            ep_idx = uid2idx_event_params[var.uid]
            if 0 <= ep_idx < len(event_parameters_eqs):
                event_parameters_eqs[ep_idx] = Const(value)

    for pidx in getattr(problem, "_equilibrium_param_indices", {}).values():
        if pidx < 0 or pidx >= len(problem._variable_parameters):
            continue
        if pidx >= len(problem._variable_parameters_values):
            continue
        var = problem._variable_parameters[pidx]
        value = float(problem._variable_parameters_values[pidx])
        if var.uid in uid2idx_event_params:
            ep_idx = uid2idx_event_params[var.uid]
            if 0 <= ep_idx < len(event_parameters_eqs):
                event_parameters_eqs[ep_idx] = Const(value)

    uid_bindings: dict[int, float] = {
        uid: float(value) for uid, value in init_guess.items() if value is not None
    }
    for var in variable_parameters:
        if not isinstance(var, Var) or var.uid not in uid2idx_event_params:
            continue
        ep_idx = uid2idx_event_params[var.uid]
        if 0 <= ep_idx < len(event_parameters_eqs):
            eq = event_parameters_eqs[ep_idx]
            if isinstance(eq, Const) and eq.value is not None:
                uid_bindings[var.uid] = float(eq.value)

    for ep_idx, eq in enumerate(list(event_parameters_eqs)):
        if not isinstance(eq, Expr) or isinstance(eq, Const):
            continue
        expr_vars = get_expression_vars(eq)
        if not any(isinstance(v, Var) and v.uid in uid2idx_vars for v in expr_vars):
            continue
        if not all(isinstance(v, Var) and v.uid in uid_bindings for v in expr_vars):
            continue
        try:
            value = float(eval_expr_uid(eq, uid_bindings))
        except Exception:
            continue
        if np.isfinite(value):
            event_parameters_eqs[ep_idx] = Const(value)

    return init_guess
