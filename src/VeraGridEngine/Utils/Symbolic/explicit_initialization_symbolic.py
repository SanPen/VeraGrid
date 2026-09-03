# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Callable, Dict, List, Tuple, Union, Optional
import numpy as np
import numba as nb
import math
import time
import hashlib
import os
import pickle
from pathlib import Path
import warnings
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from collections import defaultdict, deque

from VeraGridEngine.enumerations import EmtInitializationMethod, EmtInitializationStatus
from VeraGridEngine.Utils.Symbolic.compiled_functions import SymbolicJacobian, SymbolicVector
from VeraGridEngine.Utils.Symbolic.jit_compiler import RMSCompiler
from VeraGridEngine.Utils.Symbolic.symbolic import expression2numba, get_expression_vars
from VeraGridEngine.Utils.Symbolic.block import Block, normalize_event_parameter_initialization
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, Comparison, Var, Const, Expr, find_vars_order
from VeraGridEngine.Utils.procedural_logic import SampledValueLogic


def build_uid_bindings(
        eq: Union[Expr, Const],
        event_params_array: np.ndarray,
        x: np.ndarray,
        params_array: np.ndarray,
        dx: np.ndarray,
        uid2idx_event_params: Dict[int, int],
        uid2idx_vars: Dict[int, int],
        uid2idx_params: Dict[int, int],
        uid2idx_diff: Dict[int, int],
        init_guess: Optional[Dict[int, float]] = None,
        diff_init_guess: Optional[Dict[int, float]] = None,
        external_uid_values: Optional[Dict[int, float]] = None,
) -> Dict[int, float]:
    """
    Build the UID-to-value bindings needed to evaluate one symbolic expression.

    :param eq: Symbolic expression to analyze.
    :type eq: Union[Expr, Const]
    :param event_params_array: Runtime parameter values.
    :type event_params_array: np.ndarray
    :param x: Algebraic or state vector.
    :type x: np.ndarray
    :param params_array: Constant parameter vector.
    :type params_array: np.ndarray
    :param dx: Differential initialization vector.
    :type dx: np.ndarray
    :param uid2idx_event_params: Runtime parameter index map.
    :type uid2idx_event_params: Dict[int, int]
    :param uid2idx_vars: Variable index map.
    :type uid2idx_vars: Dict[int, int]
    :param uid2idx_params: Constant parameter index map.
    :type uid2idx_params: Dict[int, int]
    :param uid2idx_diff: Differential variable index map.
    :type uid2idx_diff: Dict[int, int]
    :param init_guess: Previously resolved state and algebraic values.
    :param diff_init_guess: Previously resolved differential values.
    :param external_uid_values: Explicit values for variables owned outside the symbolic block.
    :return: Numeric bindings for the expression variables.
    :rtype: Dict[int, float]
    """
    uid_bindings: Dict[int, float] = dict()
    vars_list: List[Var] = find_vars_order(eq)

    for vr in vars_list:
        resolved_value: Optional[float] = None
        event_idx: Optional[int] = uid2idx_event_params.get(vr.uid, None)
        state_idx: Optional[int] = uid2idx_vars.get(vr.uid, None)
        param_idx: Optional[int] = uid2idx_params.get(vr.uid, None)
        diff_idx: Optional[int] = uid2idx_diff.get(vr.uid, None)

        if event_idx is None:
            if state_idx is None:
                if param_idx is None:
                    if diff_idx is None:
                        if external_uid_values is not None and vr.uid in external_uid_values:
                            resolved_value = float(external_uid_values[vr.uid])
                        elif init_guess is not None and vr.uid in init_guess:
                            resolved_value = float(init_guess[vr.uid])
                        elif diff_init_guess is not None and vr.uid in diff_init_guess:
                            resolved_value = float(diff_init_guess[vr.uid])
                        else:
                            resolved_value = None
                    else:
                        resolved_value = float(dx[diff_idx])
                else:
                    resolved_value = float(params_array[param_idx])
            else:
                resolved_value = float(x[state_idx])
        else:
            resolved_value = float(event_params_array[event_idx])

        if resolved_value is None:
            uid_bindings = uid_bindings
        else:
            uid_bindings[vr.uid] = resolved_value

    return uid_bindings

"""
This function initializes the parameters, variables and derivatives of symbolic blocks. 
Works for both RMS and EMT simulations since the symbolic block is the same.
"""




def evaluate_explicit_init_equation(
        eq: Union[Expr, Const],
        event_params_array: np.ndarray,
        x: np.ndarray,
        params_array: np.ndarray,
        dx: np.ndarray,
        uid2idx_event_params: Dict[int, int],
        uid2idx_vars: Dict[int, int],
        uid2idx_params: Dict[int, int],
        uid2idx_diff: Dict[int, int],
        init_guess: Optional[Dict[int, float]] = None,
        diff_init_guess: Optional[Dict[int, float]] = None,
        external_uid_values: Optional[Dict[int, float]] = None,
) -> float | int | complex | None:
    """
    Evaluate one explicit initialization equation using the shared bindings.

    :param eq: Symbolic expression or constant.
    :type eq: Union[Expr, Const]
    :param event_params_array: Runtime parameter values.
    :type event_params_array: np.ndarray
    :param x: Algebraic or state vector.
    :type x: np.ndarray
    :param params_array: Constant parameter vector.
    :type params_array: np.ndarray
    :param dx: Differential initialization vector.
    :type dx: np.ndarray
    :param uid2idx_event_params: Event parameter index map.
    :type uid2idx_event_params: Dict[int, int]
    :param uid2idx_vars: Variable index map.
    :type uid2idx_vars: Dict[int, int]
    :param uid2idx_params: Constant parameter index map.
    :type uid2idx_params: Dict[int, int]
    :param uid2idx_diff: Differential variable index map.
    :type uid2idx_diff: Dict[int, int]
    :param init_guess: Previously resolved state and algebraic values.
    :param diff_init_guess: Previously resolved differential values.
    :param external_uid_values: Explicit values for variables owned outside the symbolic block.
    :return: Evaluated scalar value.
    :rtype: float
    :raises RuntimeError: If a constant equation has no concrete value.
    """
    if isinstance(eq, Const):
        return eq.value
    else:
        uid_bindings: Dict[int, float] = build_uid_bindings(
            eq=eq,
            event_params_array=event_params_array,
            x=x,
            params_array=params_array,
            dx=dx,
            uid2idx_event_params=uid2idx_event_params,
            uid2idx_vars=uid2idx_vars,
            uid2idx_params=uid2idx_params,
            uid2idx_diff=uid2idx_diff,
            init_guess=init_guess,
            diff_init_guess=diff_init_guess,
            external_uid_values=external_uid_values,
        )
        try:
            return eq.eval_uid(uid_bindings)
        except ValueError as exc:
            unresolved: List[Var] = [vr for vr in find_vars_order(eq) if vr.uid not in uid_bindings]
            unresolved_desc = ", ".join(f"{vr.name} (uid={vr.uid})" for vr in unresolved)
            raise ValueError(
                f"Failed to evaluate explicit init equation '{eq}' with unresolved vars: {unresolved_desc}"
            ) from exc


def evaluate_single_equation_fn(
        eq_fn: Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray], Union[np.ndarray, float]],
        x: np.ndarray,
        dx: np.ndarray,
        event_params_array: np.ndarray,
        params_array: np.ndarray,
) -> float:
    """
    Evaluate one compiled single-equation callable and normalize its scalar output.

    The backend callable may return a length-one numpy vector or a scalar-like
    numeric value. The common initializer always consumes it as a float.

    :param eq_fn: Compiled single-equation callable.
    :type eq_fn: Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray], Union[np.ndarray, float]]
    :param x: Algebraic or state vector.
    :type x: np.ndarray
    :param dx: Differential initialization vector.
    :type dx: np.ndarray
    :param event_params_array: Runtime parameter values.
    :type event_params_array: np.ndarray
    :param params_array: Constant parameter vector.
    :type params_array: np.ndarray
    :return: Evaluated scalar value.
    :rtype: float
    """
    result: Union[np.ndarray, float] = eq_fn(x, dx, event_params_array, params_array)

    if isinstance(result, np.ndarray):
        return float(result[0])
    else:
        return float(result)


def store_resolved_event_parameter(
        event_param: Var,
        event_params_init_dict: Dict[int, float | int | complex | None],
        event_parameters_eqs: List[Union[Expr, Const]],
        event_eq_idx: int,
        result: float | int | complex | None,
) -> None:
    """
  Store the calculated value in the equations array

    :param event_param:
    :type event_param:
    :param event_params_init_dict:
    :type event_params_init_dict:
    :param event_parameters_eqs: Global runtime-parameter equation list.
    :type event_parameters_eqs: List[Union[Expr, Const]]
    :param event_eq_idx: Index of the runtime parameter in the global list.
    :type event_eq_idx: int
    :param result: Resolved scalar value.
    :type result: float
    :return: None
    :rtype: None
    """
    resolved_event_eq: Const = Const(result)

    event_parameters_eqs[event_eq_idx] = resolved_event_eq

    event_params_init_dict[event_param.uid] = result


class SymbolicVectorSingleEquationCompiler:
    """
    Compile one self-implicit equation using the EMT symbolic-vector backend.
    """

    __slots__ = ("_compiler_names_dict", "_alias_names_dict", "_vars_name", "_diff_name", "_event_params_name", "_params_name")

    def __init__(
            self,
            compiler_names_dict: Dict[int, str],
            alias_names_dict: Dict[int, str],
            vars_name: str,
            diff_name: str,
            event_params_name: str,
            params_name: str,
    ) -> None:
        """
        Build the EMT single-equation compiler wrapper.

        :param compiler_names_dict: Compiler variable name map.
        :type compiler_names_dict: Dict[int, str]
        :param alias_names_dict: Compiler alias name map.
        :type alias_names_dict: Dict[int, str]
        :param vars_name: Symbolic-vector variable array name.
        :type vars_name: str
        :param diff_name: Symbolic-vector differential array name.
        :type diff_name: str
        :param event_params_name: Symbolic-vector runtime-parameter array name.
        :type event_params_name: str
        :param params_name: Symbolic-vector constant-parameter array name.
        :type params_name: str
        :return: None
        :rtype: None
        """
        self._compiler_names_dict: Dict[int, str] = compiler_names_dict
        self._alias_names_dict: Dict[int, str] = alias_names_dict
        self._vars_name: str = vars_name
        self._diff_name: str = diff_name
        self._event_params_name: str = event_params_name
        self._params_name: str = params_name

    def compile_equation(
            self,
            eq: Union[Expr, Const],
    ) -> Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray], np.ndarray]:
        """
        Compile one symbolic equation with the EMT symbolic-vector backend.

        :param eq: Equation to compile.
        :type eq: Union[Expr, Const]
        :return: Evaluator with signature ``(x, dx, event_params, params)``.
        :rtype: Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray], np.ndarray]
        :raises TypeError: If the equation is not symbolic.
        """
        if isinstance(eq, Const):
            raise TypeError("Self-implicit initialization requires a symbolic expression, not a constant")
        else:
            compiled_eq: SymbolicVector = SymbolicVector(
                [eq],
                self._compiler_names_dict,
                self._alias_names_dict,
                self._vars_name,
                self._diff_name,
                self._event_params_name,
                self._params_name,
            )
            return compiled_eq


class RmsSingleEquationCompiler:
    """
    Compile one self-implicit equation using the RMS JIT backend.
    """

    __slots__ = ("_rms_compiler", "_func_name_prefix", "_counter")

    def __init__(
            self,
            rms_compiler: RMSCompiler,
            func_name_prefix: str = "equation",
    ) -> None:
        """
        Build the RMS single-equation compiler wrapper.

        :param rms_compiler: Configured RMS compiler instance.
        :type rms_compiler: RMSCompiler
        :param func_name_prefix: Prefix used for generated callable names.
        :type func_name_prefix: str
        :return: None
        :rtype: None
        """
        self._rms_compiler: RMSCompiler = rms_compiler
        self._func_name_prefix: str = func_name_prefix
        self._counter: int = 0

    def compile_equation(
            self,
            eq: Union[Expr, Const],
    ) -> Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray], np.ndarray]:
        """
        Compile one symbolic equation with the RMS JIT backend.

        :param eq: Equation to compile.
        :type eq: Union[Expr, Const]
        :return: Evaluator with signature ``(x, dx, event_params, params)``.
        :rtype: Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray], np.ndarray]
        :raises TypeError: If the equation is not symbolic.
        """
        if isinstance(eq, Const):
            raise TypeError("Self-implicit initialization requires a symbolic expression, not a constant")
        else:
            func_name: str = f"{self._func_name_prefix}_{self._counter}"
            self._counter += 1
            compiled_eq: Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray], np.ndarray] = self._rms_compiler.compile_rhs([eq], func_name)
            return compiled_eq


def compile_single_explicit_equation(
        compile_single_equation: Union[SymbolicVectorSingleEquationCompiler, RmsSingleEquationCompiler],
        eq: Union[Expr, Const],
) -> Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray], Union[np.ndarray, float]]:
    """
    Compile one equation through the explicit wrapper object.

    :param compile_single_equation: Wrapper object selecting the backend.
    :type compile_single_equation: Union[SymbolicVectorSingleEquationCompiler, RmsSingleEquationCompiler]
    :param eq: Equation to compile.
    :type eq: Union[Expr, Const]
    :return: Evaluator with signature ``(x, dx, event_params, params)``.
    :rtype: Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray], Union[np.ndarray, float]]
    :raises TypeError: If the wrapper object type is unsupported.
    """
    if isinstance(compile_single_equation, SymbolicVectorSingleEquationCompiler):
        compiled_eq: Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray], np.ndarray] = (
            compile_single_equation.compile_equation(eq))
        return compiled_eq
    elif isinstance(compile_single_equation, RmsSingleEquationCompiler):
        compiled_eq = compile_single_equation.compile_equation(eq)
        return compiled_eq
    else:
        raise TypeError("Unsupported explicit initialization single-equation compiler wrapper")


def add_items(blk, init_vars, init_event):
    """
    adds items from a block to the dictionary
    :param blk:
    :type blk:
    :param init_vars:
    :param init_event:
    init_dict
    :return:
    :rtype:
    """

    init_var_key: Var
    init_var_value: Union[Expr, Const]
    for init_var_key, init_var_value in blk.init_eqs.items():
        init_vars[init_var_key] = init_var_value

    diff_init_key: Var
    diff_init_value: Union[Expr, Const]
    for diff_init_key, diff_init_value in blk.diff_init_eqs.items():
        init_vars[diff_init_key] = diff_init_value

    event_key: Var
    event_value: Union[Expr, Const]
    for event_key, event_value in blk.event_dict.items():
        init_event[event_key] = event_value

    mode_key: Var
    mode_value: Union[Expr, Const]
    for mode_key, mode_value in blk.mode_dict.items():
        init_event[mode_key] = mode_value

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
    add_items(mdl, init_vars, init_event)
    for blk in mdl.children:
        build_init_dict(blk, init_vars, init_event)


def apply_sampled_procedural_initializers(
        mdl: Block,
        init_event: Dict[Var, Union[Expr, Const]],
) -> None:
    """Use sampled procedural expressions as their startup mode values.

    Generated ``select(...)`` and sampled-value blocks keep their outputs in
    ``mode_dict`` because runtime updates occur outside the Newton residual.
    Their placeholder mode defaults must not choose the branch used by
    ``inc(...)``. At startup, the declared sampled source is the authoritative
    value and participates in the same dependency graph as every other
    explicit initialization equation.

    :param mdl: Symbolic block whose procedural entries are inspected.
    :param init_event: Runtime initialization equations updated in place.
    :return: None.
    """
    event_var_by_uid: Dict[int, Var] = dict(
        (event_var.uid, event_var) for event_var in init_event
    )
    procedural_entry: object

    for procedural_entry in mdl.procedural_logic:
        if isinstance(procedural_entry, SampledValueLogic):
            output_var: Optional[Var] = None
            if procedural_entry.output_var_uid is None:
                candidate_var: Var
                for candidate_var in init_event:
                    if candidate_var.name == procedural_entry.output_var_name:
                        if output_var is None:
                            output_var = candidate_var
                        else:
                            output_var = None
                            break
                    else:
                        pass
            else:
                output_var = event_var_by_uid.get(
                    procedural_entry.output_var_uid,
                    None,
                )

            if output_var is None:
                pass
            else:
                source_expression: Expr
                if isinstance(procedural_entry.source_expr, Comparison):
                    source_expression = procedural_entry.source_expr.to_expression()
                else:
                    source_expression = procedural_entry.source_expr
                init_event[output_var] = source_expression
        else:
            pass

    child_block: Block
    for child_block in mdl.children:
        apply_sampled_procedural_initializers(
            mdl=child_block,
            init_event=init_event,
        )


def collect_direct_algebraic_initializers(
        mdl: Block,
        direct_initializers: Dict[Var, Expr],
) -> None:
    """Collect explicit ``variable - expression`` algebraic assignments.

    PowerFactory ``inc(...)`` expressions can depend on an intermediate
    algebraic assignment. Those intermediates must be evaluated before the
    initialization expression instead of retaining the generic work-vector
    seed.

    :param mdl: Symbolic block whose algebraic equations are inspected.
    :param direct_initializers: Direct assignments collected recursively.
    :return: None.
    """
    algebraic_var_uids: set[int] = set()
    state_var_uids: set[int] = set()
    all_blocks: List[Block] = mdl.get_all_blocks()
    nested_block: Block
    for nested_block in all_blocks:
        nested_state_var: Var
        for nested_state_var in nested_block.state_vars:
            state_var_uids.add(nested_state_var.uid)

    for nested_block in all_blocks:
        nested_algebraic_var: Var
        nested_algebraic_lists: Tuple[List[Var], ...] = (
            nested_block.algebraic_vars,
            nested_block.reformulated_vars,
            nested_block.in_vars,
            nested_block.out_vars,
        )
        nested_algebraic_list: List[Var]
        for nested_algebraic_list in nested_algebraic_lists:
            for nested_algebraic_var in nested_algebraic_list:
                if nested_algebraic_var.uid in state_var_uids:
                    pass
                else:
                    algebraic_var_uids.add(nested_algebraic_var.uid)
    algebraic_eq: Expr

    # Only accept the declarative residual shape produced for a direct
    # assignment. General implicit equations remain owned by the DAE solver.
    for algebraic_eq in mdl.algebraic_eqs:
        if (
                isinstance(algebraic_eq, BinOp)
                and algebraic_eq.op == "-"
                and isinstance(algebraic_eq.left, Var)
                and algebraic_eq.left.uid in algebraic_var_uids
                and not algebraic_eq.right.contains_var(algebraic_eq.left)
        ):
            direct_initializers[algebraic_eq.left] = algebraic_eq.right
        else:
            pass

    child_block: Block
    for child_block in mdl.children:
        collect_direct_algebraic_initializers(
            mdl=child_block,
            direct_initializers=direct_initializers,
        )


def add_direct_algebraic_init_dependencies(
        init_vars: Dict[Var, Union[Expr, Const]],
        direct_initializers: Dict[Var, Expr],
        preserved_var_uids: set[int],
) -> None:
    """Add direct algebraic assignments required by initialization equations.

    :param init_vars: Unified explicit initialization equations, updated in place.
    :param direct_initializers: Available direct algebraic assignments.
    :param preserved_var_uids: Variables already seeded by an external operating point.
    :return: None.
    """
    dependency_added: bool = True

    # Re-scan a fixed snapshot on each pass because a newly added direct
    # assignment can itself expose another required intermediate.
    while dependency_added:
        dependency_added = False
        current_equations: List[Union[Expr, Const]] = list(init_vars.values())
        current_eq: Union[Expr, Const]
        for current_eq in current_equations:
            dependency_var: Var
            for dependency_var in get_expression_vars(current_eq):
                if dependency_var in init_vars:
                    pass
                else:
                    if dependency_var.uid in preserved_var_uids:
                        pass
                    else:
                        direct_eq: Optional[Expr] = direct_initializers.get(dependency_var, None)
                        if direct_eq is None:
                            pass
                        else:
                            init_vars[dependency_var] = direct_eq
                            dependency_added = True

def build_explicit_init_graph(
        mdl: Block,
        preserved_var_uids: Optional[set[int]] = None,
) -> Tuple[Dict[Var, Union[Expr, Const]], Dict[Var, List[Var]], List[Var], Dict[Var, Union[Expr, Const]]]:
    """
    Build the unified dependency graph used by the explicit initializer.

    :param mdl: Symbolic block containing event, init, and diff-init equations.
    :type mdl: Block
    :param preserved_var_uids: Optional externally seeded variables that direct
        algebraic assignments must consume without replacing.
    :return: Unified equation dictionary, dependency map, and topological order.
    :rtype: Tuple[Dict[Var, Union[Expr, Const]], Dict[Var, List[Var]], List[Var]]
    :raises RuntimeError: If a cross-variable cycle is detected.
    """
    normalize_event_parameter_initialization(block=mdl)

    init_vars = dict()
    init_event = dict()
    if preserved_var_uids is None:
        preserved_uids: set[int] = set()
    else:
        preserved_uids = set(preserved_var_uids)
    build_init_dict(mdl, init_vars, init_event)
    apply_sampled_procedural_initializers(
        mdl=mdl,
        init_event=init_event,
    )

    # Event parameters own their single initialization expression directly.
    # Normalization above migrates the former Const(None) + init_eqs pattern.
    for ev_var, ev_eq in init_event.items():
        init_vars[ev_var] = ev_eq

    # Resolve only direct algebraic assignments reached from the complete
    # initialization graph, including procedural startup expressions. This
    # preserves DAE ownership of general implicit algebraics while ensuring
    # ``inc(...)`` observes the same selected branch used at the first sample.
    direct_initializers: Dict[Var, Expr] = dict()
    collect_direct_algebraic_initializers(
        mdl=mdl,
        direct_initializers=direct_initializers,
    )
    direct_var: Var
    direct_eq: Expr
    for direct_var, direct_eq in direct_initializers.items():
        if direct_var in init_vars:
            pass
        else:
            if direct_var.uid in preserved_uids:
                pass
            else:
                init_vars[direct_var] = direct_eq
    add_direct_algebraic_init_dependencies(
        init_vars=init_vars,
        direct_initializers=direct_initializers,
        preserved_var_uids=preserved_uids,
    )

    graph: Dict[Var, List[Var]] = defaultdict(list)
    in_degree: Dict[Var, int] = defaultdict(int)
    dependencies: Dict[Var, List[Var]] = dict()

    for var, eq in init_vars.items():
        vars_in_eq: List[Var] = get_expression_vars(eq)
        deps: List[Var] = list()

        for dep in vars_in_eq:
            if dep in init_vars:
                deps.append(dep)
            else:
                deps = deps

        dependencies[var] = deps

        for dep in deps:
            if dep.uid != var.uid:
                graph[dep].append(var)
                in_degree[var] += 1
            else:
                in_degree[var] = in_degree[var]

        if var not in in_degree:
            in_degree[var] = 0
        else:
            in_degree[var] = in_degree[var]

    initial_queue_items: List[Var] = list()
    for var, degree in in_degree.items():
        if degree == 0:
            initial_queue_items.append(var)
        else:
            initial_queue_items = initial_queue_items

    queue: deque[Var] = deque(initial_queue_items)
    topo_order: List[Var] = list()

    while queue:
        current_var: Var = queue.popleft()
        topo_order.append(current_var)

        for downstream_var in graph[current_var]:
            in_degree[downstream_var] -= 1
            if in_degree[downstream_var] == 0:
                queue.append(downstream_var)
            else:
                queue = queue

    if len(topo_order) != len(init_vars):
        cyclic_vars: List[str] = list()
        var_key: Var
        degree_value: int
        for var_key, degree_value in in_degree.items():
            if degree_value > 0:
                cyclic_vars.append(str(var_key.name))
            else:
                cyclic_vars = cyclic_vars

        cyclic_dependencies: List[str] = list()
        cyclic_var: Var
        for cyclic_var, deps in dependencies.items():
            if in_degree.get(cyclic_var, 0) > 0:
                dep_names: List[str] = list()
                dep_var: Var
                for dep_var in deps:
                    dep_names.append(str(dep_var.name))
                cyclic_dependencies.append(f"{cyclic_var.name} <- {dep_names}")
            else:
                cyclic_dependencies = cyclic_dependencies

        raise RuntimeError(
            "Cycle detected between different variables: "
            f"vars={cyclic_vars}; deps={cyclic_dependencies}"
        )
    else:
        return init_vars, dependencies, topo_order, init_event


def build_symbolic_vector_single_equation_compiler(
        compiler_names_dict: Dict[int, str],
        alias_names_dict: Dict[int, str],
        vars_name: str,
        diff_name: str,
        event_params_name: str,
        params_name: str,
) -> SymbolicVectorSingleEquationCompiler:
    """
    Build the EMT single-equation compiler wrapper.

    :param compiler_names_dict: Compiler variable name map.
    :type compiler_names_dict: Dict[int, str]
    :param alias_names_dict: Compiler alias name map.
    :type alias_names_dict: Dict[int, str]
    :param vars_name: SymbolicVector state or algebraic array name.
    :type vars_name: str
    :param diff_name: SymbolicVector derivative array name.
    :type diff_name: str
    :param event_params_name: SymbolicVector event parameter array name.
    :type event_params_name: str
    :param params_name: SymbolicVector constant parameter array name.
    :type params_name: str
    :return: Wrapper object compiling one equation to the common four-array signature.
    :rtype: SymbolicVectorSingleEquationCompiler
    """
    compiler_wrapper: SymbolicVectorSingleEquationCompiler = SymbolicVectorSingleEquationCompiler(
        compiler_names_dict=compiler_names_dict,
        alias_names_dict=alias_names_dict,
        vars_name=vars_name,
        diff_name=diff_name,
        event_params_name=event_params_name,
        params_name=params_name,
    )
    return compiler_wrapper


def build_rms_single_equation_compiler(
        rms_compiler: RMSCompiler,
        func_name_prefix: str = "equation",
) -> RmsSingleEquationCompiler:
    """
    Build the RMS single-equation compiler wrapper.

    :param rms_compiler: Configured RMS compiler instance.
    :type rms_compiler: RMSCompiler
    :param func_name_prefix: Prefix used to name generated callables.
    :type func_name_prefix: str
    :return: Wrapper object compiling one equation to the common four-array signature.
    :rtype: RmsSingleEquationCompiler
    """
    compiler_wrapper: RmsSingleEquationCompiler = RmsSingleEquationCompiler(
        rms_compiler=rms_compiler,
        func_name_prefix=func_name_prefix,
    )
    return compiler_wrapper


def solve_self_implicit(
        eq_fn: Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray], Union[np.ndarray, float]],
        x: np.ndarray,
        dx: np.ndarray,
        target_idx: int,
        target_array: np.ndarray,
        event_params_array: np.ndarray,
        params_array: np.ndarray,
        tol: float = 1e-8,
        max_iter: int = 50,
) -> float:
    """
    Solve a scalar self-implicit initialization equation with the shared signature.

    :param eq_fn: Compiled single-equation callable.
    :type eq_fn: Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray], Union[np.ndarray, float]]
    :param x: Algebraic or state vector.
    :type x: np.ndarray
    :param dx: Differential initialization vector.
    :type dx: np.ndarray
    :param target_idx: Target index inside ``target_array``.
    :type target_idx: int
    :param target_array: Array holding the unknown being solved.
    :type target_array: np.ndarray
    :param event_params_array: Runtime parameter values.
    :type event_params_array: np.ndarray
    :param params_array: Constant parameter vector.
    :type params_array: np.ndarray
    :param tol: Secant convergence tolerance.
    :type tol: float
    :param max_iter: Maximum secant iterations.
    :type max_iter: int
    :return: Solved scalar value.
    :rtype: float
    """
    initial_guess: float = float(target_array[target_idx])
    if not np.isfinite(initial_guess):
        initial_guess = 1.0
    else:
        initial_guess = initial_guess

    x0: float = initial_guess if abs(initial_guess) > 1e-12 else 1.0
    x1: float = x0 + 0.1 if abs(x0) > 1e-12 else 1.1

    for _ in range(max_iter):
        target_array[target_idx] = x0
        f0: float = evaluate_single_equation_fn(eq_fn, x, dx, event_params_array, params_array) - x0

        target_array[target_idx] = x1
        f1: float = evaluate_single_equation_fn(eq_fn, x, dx, event_params_array, params_array) - x1

        if abs(f1) < tol:
            return x1
        else:
            denominator: float = f1 - f0
            if abs(denominator) < 1e-12:
                break
            else:
                x2: float = x1 - f1 * (x1 - x0) / denominator
                x0 = x1
                x1 = x2

    return x1


def build_explicit_external_uid_values(
        mdl: Block,
        external_name_values: Dict[str, float],
) -> Dict[int, float]:
    """Resolve external symbolic inputs to their exact equation UIDs.

    Imported expressions may own external variables that are intentionally not
    part of the DAE state, derivative, or parameter vectors. The RMS wrapper
    declares their semantic names and values, while this boundary converts that
    declaration into the UID mapping consumed by the generic initializer.

    :param mdl: Symbolic block whose initialization graph consumes external inputs.
    :param external_name_values: External values keyed by declared symbolic name.
    :return: External values keyed by the exact variable UIDs used by the block.
    """
    external_uid_values: Dict[int, float] = dict()
    runtime_block: Block
    for runtime_block in mdl.get_all_blocks():
        equation_groups: List[List[Union[Expr, Const]]] = list([
            list(runtime_block.algebraic_eqs),
            list(runtime_block.state_eqs),
            list(runtime_block.differential_eqs),
            list(runtime_block.init_eqs.values()),
            list(runtime_block.diff_init_eqs.values()),
            list(runtime_block.event_dict.values()),
            list(runtime_block.mode_dict.values()),
            list(runtime_block.boolean_guards.values()),
        ])
        equation_group: List[Union[Expr, Const]]
        equation: Union[Expr, Const]
        equation_var: Var
        for equation_group in equation_groups:
            for equation in equation_group:
                for equation_var in find_vars_order(equation):
                    external_value: float | None = external_name_values.get(
                        equation_var.name,
                        None,
                    )
                    if external_value is None:
                        pass
                    else:
                        external_uid_values[equation_var.uid] = float(external_value)
                else:
                    pass
            else:
                pass
        else:
            pass
    else:
        pass

    return external_uid_values


def init_explicit_common(
        mdl: Block,
        sys_vars: Dict[int, Var],
        sys_diff_vars: Dict[int, Var],
        variable_parameters: List[Var],
        event_parameters_eqs: List[Union[Expr, Const]],
        constant_parameters: List[Var],
        init_guess: Dict[int, float | int | complex | None],
        event_param_init_dict: Dict[int, float | int | complex | None],
        diff_init_guess: Dict[int, float | int | complex | None],
        uid2idx_vars: Dict[int, int],
        uid2idx_diff: Dict[int, int],
        uid2idx_params: Dict[int, int],
        uid2idx_event_params: Dict[int, int],
        params_array: List[Const] | np.ndarray,
        compile_single_equation: Union[SymbolicVectorSingleEquationCompiler, RmsSingleEquationCompiler],
        external_uid_values: Optional[Dict[int, float]] = None,
        verbose: bool = False,
) -> Tuple[Dict[int, float | int | complex | None], Dict[int, float | int | complex | None]]:
    """
    Run the universal explicit initialization core shared by RMS and EMT flows.

    :param sys_diff_vars:
    :type sys_diff_vars:
    :param sys_vars:
    :type sys_vars:
    :param mdl: Symbolic model block.
    :type mdl: Block
    :param variable_parameters: Runtime or event parameters.
    :type variable_parameters: List[Var]
    :param event_parameters_eqs: Runtime parameter equations storage.
    :type event_parameters_eqs: List[Union[Expr, Const]]
    :param constant_parameters: Constant parameters list.
    :type constant_parameters: List[Var]
    :param init_guess: Initialization guesses for algebraic or state variables.
    :type init_guess: Dict[int, float]
    :param event_param_init_dict: Event parameter initialization dictionary.
    :param diff_init_guess: Initialization guesses for differential variables.
    :type diff_init_guess: Dict[int, float]
    :param uid2idx_vars: Variable index map.
    :type uid2idx_vars: Dict[int, int]
    :param uid2idx_diff: Differential variable index map.
    :type uid2idx_diff: Dict[int, int]
    :param uid2idx_params: Constant parameter index map.
    :type uid2idx_params: Dict[int, int]
    :param uid2idx_event_params: Event parameter index map.
    :type uid2idx_event_params: Dict[int, int]
    :param params_array: Constant parameter vector in symbolic storage or numeric form.
    :type params_array: List[Const] | np.ndarray
    :param compile_single_equation: Backend-specific single-equation compiler wrapper.
    :type compile_single_equation: Union[SymbolicVectorSingleEquationCompiler, RmsSingleEquationCompiler]
    :param external_uid_values: Explicit values for variables owned outside the symbolic block.
    :param verbose: Print initialization progress.
    :type verbose: bool
    :return: Updated algebraic or state and differential guesses.
    :rtype: Tuple[Dict[int, float], Dict[int, float]]
    """
    _ = constant_parameters

    # initialize array for model variables
    x: np.ndarray = np.ones(len(sys_vars))
    dx: np.ndarray = np.zeros(len(sys_diff_vars))
    event_params_array: np.ndarray = np.ones(len(variable_parameters))

    # RMS problem assembly retains Const wrappers so symbolic ownership is not
    # lost before compilation. Explicit evaluation consumes only concrete
    # scalars, therefore materialize a fixed-size numeric view at this boundary.
    if isinstance(params_array, np.ndarray):
        numeric_params_array: np.ndarray = np.asarray(params_array, dtype=float)
    else:
        numeric_params_array = np.zeros(len(params_array), dtype=float)
        parameter_index: int
        parameter_value: Const
        for parameter_index, parameter_value in enumerate(params_array):
            if parameter_value.value is None:
                parameter_name: str = constant_parameters[parameter_index].name
                raise ValueError(
                    f"Constant parameter '{parameter_name}' has no explicit initialization value"
                )
            else:
                numeric_params_array[parameter_index] = float(parameter_value.value)

    # Seed the working vectors with the guesses already assembled before the
    # explicit stage. The problem relies on those PF-driven values and on previously
    # resolved block values when evaluating downstream explicit equations.
    for uid, val in init_guess.items():
        if uid in uid2idx_vars:
            x[uid2idx_vars[uid]] = val

    for uid, val in diff_init_guess.items():
        if uid in uid2idx_diff:
            dx[uid2idx_diff[uid]] = val


    dic_total, dependencies, topo_order, init_event = build_explicit_init_graph(
        mdl=mdl,
        preserved_var_uids=set(init_guess.keys()),
    )

    for var in topo_order:
        eq: Union[Expr, Const] = dic_total[var]

        if var in init_event:
            result = evaluate_explicit_init_equation(
                eq=eq,
                event_params_array=event_params_array,
                x=x,
                params_array=numeric_params_array,
                dx=dx,
                uid2idx_event_params=uid2idx_event_params,
                uid2idx_vars=uid2idx_vars,
                uid2idx_params=uid2idx_params,
                uid2idx_diff=uid2idx_diff,
                init_guess=init_guess,
                diff_init_guess=diff_init_guess,
                external_uid_values=external_uid_values,
            )
            event_params_array[uid2idx_event_params[var.uid]] = result
            store_resolved_event_parameter(
                event_param=var,
                event_params_init_dict=event_param_init_dict,
                event_parameters_eqs=event_parameters_eqs,
                event_eq_idx=uid2idx_event_params[var.uid],
                result=result,
            )

            if verbose:
                print(f"event_param:{var.name} initialized with: {result}")

        else:
            if not var in dependencies[var]:
                result = evaluate_explicit_init_equation(
                    eq=eq,
                    event_params_array=event_params_array,
                    x=x,
                    params_array=numeric_params_array,
                    dx=dx,
                    uid2idx_event_params=uid2idx_event_params,
                    uid2idx_vars=uid2idx_vars,
                    uid2idx_params=uid2idx_params,
                    uid2idx_diff=uid2idx_diff,
                    init_guess=init_guess,
                    diff_init_guess=diff_init_guess,
                    external_uid_values=external_uid_values,
                )

                if var.uid in uid2idx_vars:
                    x[uid2idx_vars[var.uid]] = result
                    init_guess[var.uid] = result
                elif var.uid in uid2idx_diff:
                    dx[uid2idx_diff[var.uid]] = result
                    diff_init_guess[var.uid] = result
                else:
                    raise RuntimeError(f"Unable to classify explicit variable {var.name}")

            else:
                # Todo: refactor this to use compile_rhs function already built in jit_compiler
                eq_fn: Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray], Union[np.ndarray, float]] \
                    = compile_single_explicit_equation(compile_single_equation, eq)

                if var.uid in uid2idx_vars:
                    target_idx: int = uid2idx_vars[var.uid]
                    result = solve_self_implicit(
                        eq_fn=eq_fn,
                        x=x,
                        dx=dx,
                        target_idx=target_idx,
                        target_array=x,
                        event_params_array=event_params_array,
                        params_array=numeric_params_array,
                    )
                    x[target_idx] = result
                    init_guess[var.uid] = result
                elif var.uid in uid2idx_diff:
                    target_idx = uid2idx_diff[var.uid]
                    result = solve_self_implicit(
                        eq_fn=eq_fn,
                        x=x,
                        dx=dx,
                        target_idx=target_idx,
                        target_array=dx,
                        event_params_array=event_params_array,
                        params_array=numeric_params_array,
                    )
                    dx[target_idx] = result
                    diff_init_guess[var.uid] = result
                else:
                    raise RuntimeError(f"Unable to classify self-implicit variable {var.name}")

            if verbose:
                print(f"explicit_init:{var.name} = {result}")


    return init_guess, diff_init_guess
