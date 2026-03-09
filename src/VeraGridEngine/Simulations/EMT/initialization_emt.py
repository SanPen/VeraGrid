# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Dict, List, Tuple, Union, Optional
import numpy as np
from enum import Enum, auto

from VeraGridEngine.Utils.Symbolic.compiled_functions import SymbolicVector
from VeraGridEngine.Utils.Symbolic.symbolic import get_expression_vars
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Const, Expr, find_vars_order


class InitializationStatus(Enum):
    """Enumeration to track the progress of the initialization solver."""
    PENDING = auto()
    RESOLVED = auto()
    FAILED = auto()


def build_uid_bindings(
        eq: Union[Expr, Const],
        event_params_array: np.ndarray,
        x: np.ndarray,
        params_array: np.ndarray,
        dx: np.ndarray,
        uid2idx_event_params: Dict[int, int],
        uid2idx_vars: Dict[int, int],
        uid2idx_params: Dict[int, int],
        uid2idx_diff: Dict[int, int]
) -> Dict[int, float]:
    """
    Builds a mapping of Unique Identifiers (UIDs) to their current numeric values.

    :param eq: The symbolic expression to analyze.
    :param event_params_array: Array containing resolved event parameters.
    :param x: Array containing state and algebraic variables.
    :param params_array: Array containing constant model parameters.
    :param dx: Array containing derivative values.
    :param uid2idx_event_params: Mapping of UID to index for event parameters.
    :param uid2idx_vars: Mapping of UID to index for variables.
    :param uid2idx_params: Mapping of UID to index for constants.
    :param uid2idx_diff: Mapping of UID to index for derivatives.
    :return: A dictionary mapping UIDs to their float values.
    """
    uid_bindings: Dict[int, float] = dict()
    vars_list: List[Var] = find_vars_order(eq)

    for vr in vars_list:
        if vr.uid in uid2idx_event_params:
            uid_bindings[vr.uid] = float(event_params_array[uid2idx_event_params[vr.uid]])
        elif vr.uid in uid2idx_vars:
            uid_bindings[vr.uid] = float(x[uid2idx_vars[vr.uid]])
        elif vr.uid in uid2idx_params:
            uid_bindings[vr.uid] = float(params_array[uid2idx_params[vr.uid]])
        elif vr.uid in uid2idx_diff:
            uid_bindings[vr.uid] = float(dx[uid2idx_diff[vr.uid]])
        else:
            # If the variable is not found in any registry, it remains unassigned.
            # This is handled by the calling logic's solvability check.
            pass

    return uid_bindings


def event_param_is_resolved(v: Var, mdl: Block) -> bool:
    """
    Checks if an event parameter has been assigned a concrete value.

    :param v: The variable representing the event parameter.
    :param mdl: The symbolic model block.
    :return: True if resolved, False otherwise.
    """
    if v in mdl.event_dict:
        eqv: Union[Expr, Const] = mdl.event_dict[v]
        if isinstance(eqv, Const):
            if eqv.value is None:
                return False
            else:
                return True
        else:
            return True
    else:
        return True


def can_compute_init(
        var: Var,
        eq: Union[Expr, Const],
        mdl: Block,
        init_guess: Dict[int, float],
        diff_init_guess: Dict[int, float],
        uid2idx_diff: Dict[int, int],
        uid2idx_vars: Dict[int, int]
) -> bool:
    """
    Determines if an initialization equation is computable based on current knowns.

    :param var: Target variable.
    :param eq: The expression to evaluate.
    :param mdl: The model block.
    :param init_guess: Current variable guesses.
    :param diff_init_guess: Current derivative guesses.
    :param uid2idx_diff: UID map for derivatives.
    :param uid2idx_vars: UID map for variables.
    :return: Boolean indicating if all dependencies are met.
    """
    vars_needed: List[Var] = get_expression_vars(eq)
    for v_dep in vars_needed:
        # Self-dependency is allowed for fixed-point iteration
        if v_dep.uid == var.uid:
            continue
        else:
            # Check event parameter resolution
            if v_dep in mdl.event_dict:
                if not event_param_is_resolved(v_dep, mdl):
                    return False
                else:
                    pass
            else:
                # Check if derivative or variable dependency is missing
                if v_dep.uid in uid2idx_diff:
                    if v_dep.uid not in diff_init_guess:
                        return False
                    else:
                        pass
                elif v_dep.uid in uid2idx_vars:
                    if v_dep.uid not in init_guess:
                        return False
                    else:
                        pass
                else:
                    pass
    return True


def init_explicit_emt(
        mdl: Block,
        sys_vars: Dict[int, Var],
        sys_diff_vars: Dict[int, Var],
        variable_parameters: List[Var],
        event_parameters_eqs: List[Union[Expr, Const]],
        constant_parameters: List[Var],
        init_guess: Dict[int, float],
        diff_init_guess: Dict[int, float],
        uid2idx_vars: Dict[int, int],
        uid2idx_diff: Dict[int, int],
        uid2idx_params: Dict[int, int],
        uid2idx_event_params: Dict[int, int],
        compiler_names_dict: Dict[int, str],
        alias_names_dict: Dict[int, str],
        VARIABLE_PARAMS_NAME: str,
        TIME_NAME: str,
        VARS_NAME: str,
        DIFF_NAME: str,
        CONSTANT_PARAMS_NAME: str):
# ) -> Union[None, Tuple[Dict[int, float], Block]]:
    """
    Initializes the EMT model by solving initialization and differential equations.

    This function performs a topological-like resolution of model variables.
    It uses fixed-point iteration for self-referencing equations and handles
    dependencies between algebraic and differential states.

    :param mdl: Symbolic model block.
    :param sys_vars: Registry of system variables.
    :param sys_diff_vars: Registry of system differential variables.
    :param variable_parameters: List of parameters that change on events.
    :param event_parameters_eqs: Initial equations for event parameters.
    :param constant_parameters: List of constant parameters.
    :param init_guess: Initial guesses for variables.
    :param diff_init_guess: Initial guesses for derivatives.
    :param uid2idx_vars: Index map for variables.
    :param uid2idx_diff: Index map for derivatives.
    :param uid2idx_params: Index map for parameters.
    :param uid2idx_event_params: Index map for event parameters.
    :param compiler_names_dict: Map for variable naming in compilation.
    :param alias_names_dict: Map for variable aliases.
    :param VARIABLE_PARAMS_NAME: Name for variable parameter array.
    :param TIME_NAME: Name for time variable.
    :param VARS_NAME: Name for state variable array.
    :param DIFF_NAME: Name for derivative array.
    :param CONSTANT_PARAMS_NAME: Name for constant parameter array.
    :return: Updated initial guesses and modified model block.
    """

    # Initialize memory buffers for numerical evaluation
    # EMT solvers require flat arrays for efficient computation
    x: np.ndarray = np.ones(len(sys_vars))
    dx: np.ndarray = np.zeros(len(sys_diff_vars))

    # Hydrate buffers with existing user-provided guesses
    for uid, val in init_guess.items():
        print(f"uid from var = {uid} with val = {val}")
        x[uid2idx_vars[uid]] = val

    for uid, val in diff_init_guess.items():
        dx[uid2idx_diff[uid]] = val

    # Setup constant parameter array
    params_array: np.ndarray = np.zeros(len(constant_parameters))
    for param, const in mdl.parameters.items():
        params_array[uid2idx_params[param.uid]] = const.value

    # Primary pass: resolve basic event parameters that are constant or immediate
    event_params_array: np.ndarray = np.ones(len(variable_parameters))
    for event_param in mdl.event_dict.keys():
        eq: Union[Expr, Const] = mdl.event_dict[event_param]

        # Determine if the expression is concrete enough to evaluate
        is_concrete_const: bool = isinstance(eq, Const) and eq.value is not None
        is_expression: bool = not isinstance(eq, Const)

        if is_concrete_const or is_expression:
            vars_list: List[Var] = find_vars_order(eq)
            # Bind current values for calculation
            uid_bindings: Dict[int, float] = dict()
            for var in vars_list:
                uid_bindings[var.uid] = float(event_params_array[uid2idx_event_params[var.uid]])

            result: float = eq.eval_uid(uid_bindings)
            event_params_array[uid2idx_event_params[event_param.uid]] = result
        else:
            pass

    # Track pending equations that require dependency resolution
    init_pending: Dict[int, Tuple[Var, Union[Expr, Const]]] = dict()
    for v, e in mdl.init_eqs.items():
        init_pending[v.uid] = (v, e)

    diff_pending: Dict[int, Tuple[Var, Union[Expr, Const]]] = dict()
    for v, e in mdl.diff_init_eqs.items():
        diff_pending[v.uid] = (v, e)

    # Iterative solver loop
    while len(init_pending) > 0 or len(diff_pending) > 0:
        progress_made: bool = False

        # Solve for Algebraic/State variables
        for uid in list(init_pending.keys()):
            var, eq = init_pending[uid]
            if can_compute_init(var, eq, mdl, init_guess, diff_init_guess, uid2idx_diff, uid2idx_vars):

                # Logic for variables that are registered as event parameters
                if var in mdl.event_dict:
                    if isinstance(eq, Const) and eq.value is not None:
                        # Value already exists; skip to avoid re-init error or handle gracefully
                        pass
                    else:
                        bindings: Dict[int, float] = build_uid_bindings(
                            eq, event_params_array, x, params_array, dx,
                            uid2idx_event_params, uid2idx_vars, uid2idx_params, uid2idx_diff
                        )
                        res: float = eq.eval_uid(bindings)
                        mdl.event_dict[var] = Const(res)
                        event_params_array[uid2idx_event_params[var.uid]] = res

                        param_idx: int = variable_parameters.index(var)
                        if event_parameters_eqs[param_idx].value is None:
                            event_parameters_eqs[param_idx] = Const(res)
                        else:
                            pass

                # Logic for standard algebraic variables
                else:
                    vars_in_eqs: List[Var] = get_expression_vars(eq)
                    if var not in vars_in_eqs:
                        # Direct assignment
                        bindings = build_uid_bindings(
                            eq, event_params_array, x, params_array, dx,
                            uid2idx_event_params, uid2idx_vars, uid2idx_params, uid2idx_diff
                        )
                        res = eq.eval_uid(bindings)
                        init_guess[var.uid] = res
                        x[uid2idx_vars[var.uid]] = res
                    else:
                        # Implicit resolution using a damped fixed-point iteration
                        eq_fn: SymbolicVector = SymbolicVector(
                            [eq], compiler_names_dict, alias_names_dict,
                            VARS_NAME, DIFF_NAME, VARIABLE_PARAMS_NAME, CONSTANT_PARAMS_NAME
                        )

                        # Fixed-point parameters
                        tol: float = 1e-8
                        error: float = 1.0
                        alpha: float = 1.3
                        curr_x: float = 1.2

                        x[uid2idx_vars[var.uid]] = curr_x
                        while error > tol:
                            try:
                                # Evaluate expression with current state
                                eval_res: float = float(eq_fn(x, dx, event_params_array, params_array)[0])
                            except Exception:
                                # Fallback/Reset on numerical instability
                                x[uid2idx_vars[var.uid]] = -0.1
                                eval_res = float(eq_fn(x, dx, event_params_array, params_array)[0])

                            # Update with damping (Successive Over-Relaxation style)
                            x[uid2idx_vars[var.uid]] = (1 - alpha) * curr_x + alpha * eval_res
                            error = float(abs(eval_res - curr_x))
                            curr_x = float(x[uid2idx_vars[var.uid]])

                        init_guess[var.uid] = curr_x

                del init_pending[uid]
                progress_made = True
            else:
                pass

        # Solve for Differential variables
        for uid in list(diff_pending.keys()):
            d_var, eq = diff_pending[uid]
            # Use separate check for diff equations to ensure variables are ready
            if can_compute_init(d_var, eq, mdl, init_guess, diff_init_guess, uid2idx_diff, uid2idx_vars):
                vars_in_eqs = get_expression_vars(eq)

                if d_var not in vars_in_eqs:
                    bindings = build_uid_bindings(
                        eq, event_params_array, x, params_array, dx,
                        uid2idx_event_params, uid2idx_vars, uid2idx_params, uid2idx_diff
                    )
                    res = eq.eval_uid(bindings)
                    diff_init_guess[d_var.uid] = res
                    dx[uid2idx_diff[d_var.uid]] = res
                else:
                    # Fixed-point iteration for derivatives
                    eq_fn = SymbolicVector(
                        [eq], compiler_names_dict, alias_names_dict,
                        VARS_NAME, DIFF_NAME, VARIABLE_PARAMS_NAME, CONSTANT_PARAMS_NAME
                    )
                    tol = 1e-8
                    error = 1.0
                    alpha = 1.3
                    curr_dx: float = 1.2

                    dx[uid2idx_diff[d_var.uid]] = curr_dx
                    while error > tol:
                        try:
                            eval_res = float(eq_fn(x, dx, event_params_array, params_array)[0])
                        except Exception:
                            dx[uid2idx_diff[d_var.uid]] = -0.1
                            eval_res = float(eq_fn(x, dx, event_params_array, params_array)[0])

                        dx[uid2idx_diff[d_var.uid]] = (1 - alpha) * curr_dx + alpha * eval_res
                        error = float(abs(eval_res - curr_dx))
                        curr_dx = float(dx[uid2idx_diff[d_var.uid]])

                    diff_init_guess[d_var.uid] = curr_dx

                del diff_pending[uid]
                progress_made = True
            else:
                pass

        # If no variables were resolved in this pass, the system is unsolvable
        if not progress_made:
            # We return None to signify failure rather than raising, per directive
            return None
        else:
            pass


def init_pseudo_transient():
    """
    initialize model using pseudotransient method
    :return:
    :rtype:
    """
    raise NotImplementedError(f'pseudotransient initialization method not implemented yet')
