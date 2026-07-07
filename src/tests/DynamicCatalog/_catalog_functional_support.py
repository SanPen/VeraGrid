from __future__ import annotations

import math
import unittest
from typing import Dict

import numpy as np

from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Utils.procedural_logic import AnalogFlipFlopLogic, FixedSampleLogic, FlipFlopLogic, GradientLimiterLogic, MovingAverageLogic, PickupDropoffLogic, ResetOnRisingEdgeLogic, SampledValueLogic, TimeDelayLogic
from VeraGridEngine.Utils.Symbolic.symbolic import Comparison, Expr

from DynamicCatalog._catalog_support import (
    build_template,
)


class FunctionalContract:
    """Light container describing one static functional contract for one typ_id."""

    __slots__ = ["label", "typ_id", "inputs", "params", "outputs", "states", "internals", "init_eqs", "state_derivatives", "tol"]

    def __init__(
        self,
        label: str,
        typ_id: str,
        inputs: Dict[str, float],
        params: Dict[str, float],
        outputs: Dict[str, float],
        states: Dict[str, float] | None = None,
        internals: Dict[str, float] | None = None,
        init_eqs: Dict[str, float] | None = None,
        state_derivatives: Dict[str, float] | None = None,
        tol: float = 1e-9,
    ) -> None:
        """
        Build one static functional contract.

        :param label: Human-readable test label.
        :param typ_id: DGS type identifier.
        :param inputs: Input values by logical name.
        :param params: Parameter values by logical name.
        :param outputs: Expected output values by logical name.
        :param states: Expected state values by logical name.
        :param internals: Expected internal values by logical name.
        :param init_eqs: Expected initialization equations by logical name.
        :param state_derivatives: Expected derivatives by state logical name.
        :param tol: Numeric assertion tolerance.
        :return: None.
        """
        self.label = label
        self.typ_id = typ_id
        self.inputs = inputs
        self.params = params
        self.outputs = outputs
        self.states = states
        self.internals = internals
        self.init_eqs = init_eqs
        self.state_derivatives = state_derivatives
        self.tol = tol


class DynamicFunctionalContract:
    """Light container describing one dynamic functional contract for one typ_id."""

    __slots__ = ["label", "typ_id", "t_end", "dt", "params", "inputs", "outputs", "tol"]

    def __init__(
        self,
        label: str,
        typ_id: str,
        t_end: float,
        dt: float,
        params: Dict[str, float],
        inputs: Dict[str, float],
        outputs: Dict[str, float],
        tol: float = 1e-6,
    ) -> None:
        """
        Build one dynamic functional contract.

        :param label: Human-readable test label.
        :param typ_id: DGS type identifier.
        :param t_end: Final simulation time.
        :param dt: Time step used by the mini-stepper.
        :param params: Parameter values by logical name.
        :param inputs: Input values by logical name.
        :param outputs: Expected output values at ``t_end``.
        :param tol: Numeric assertion tolerance.
        :return: None.
        """
        self.label = label
        self.typ_id = typ_id
        self.t_end = t_end
        self.dt = dt
        self.params = params
        self.inputs = inputs
        self.outputs = outputs
        self.tol = tol


class FunctionalRuntimeProblem:
    """Minimal EMT runtime problem used by the catalog functional harness."""

    __slots__ = ["sys_block", "glob_time", "uid2idx_vars", "vars_by_uid", "uid2idx_event_params", "uid2idx_params", "_params_values"]

    def __init__(self, block: Block, glob_time_var: Var) -> None:
        """
        Build the lightweight runtime object needed by procedural logic entries.

        :param block: Symbolic block under test.
        :param glob_time_var: Global time variable used by the runtime expressions.
        :return: None.
        """
        self.sys_block = block
        self.glob_time = glob_time_var

        ordered_vars: list[Var] = list()
        runtime_vars: list[Var] = list(block.event_dict.keys()) + list(block.mode_dict.keys())
        runtime_uids: set[int] = set(var.uid for var in runtime_vars)
        group_vars: list[list[Var]] = [block.state_vars, block.algebraic_vars, block.in_vars, list(block.init_eqs.keys()), list(block.diff_init_eqs.keys())]
        group_var_list: list[Var]
        candidate_var: Var
        for group_var_list in group_vars:
            for candidate_var in group_var_list:
                append_unique_var(ordered_vars, candidate_var)

        expr_list: list[Expr | Comparison | float | int | bool] = list(block.state_eqs) + list(block.algebraic_eqs) + list(block.init_eqs.values()) + list(block.diff_init_eqs.values())
        for logic in block.procedural_logic:
            append_logic_exprs(expr_list, logic)

        expr_item: Expr | Comparison | float | int | bool
        for expr_item in expr_list:
            expr_vars: list[Var] = list()
            expr_var: Var
            append_expr_vars(expr_vars, expr_item)
            for expr_var in expr_vars:
                if expr_var.uid not in runtime_uids:
                    append_unique_var(ordered_vars, expr_var)
                else:
                    pass

        self.uid2idx_vars = {var.uid: idx for idx, var in enumerate(ordered_vars)}
        self.vars_by_uid = {var.uid: var for var in ordered_vars}

        dedup_runtime: list[Var] = list()
        runtime_var: Var
        for runtime_var in runtime_vars:
            append_unique_var(dedup_runtime, runtime_var)

        self.uid2idx_event_params = {var.uid: idx for idx, var in enumerate(dedup_runtime)}
        self.uid2idx_params = dict()
        self._params_values = list()

    def get_variable_parameter_number(self) -> int:
        """
        Return the runtime parameter vector length expected by procedural logic.

        :return: Runtime parameter count.
        """
        return len(self.uid2idx_event_params)

    def get_parameters_values(self) -> list[float]:
        """
        Return the stored runtime parameter values.

        :return: Runtime parameter values.
        """
        return self._params_values


def evaluate_expr_like(expr_like: Expr | Comparison | float | int | bool, uid_bindings: Dict[int, float]) -> float:
    """
    Evaluate one expression-like object against one uid-value binding map.

    :param expr_like: Expression-like object.
    :param uid_bindings: Numeric values by variable uid.
    :return: Evaluated scalar result.
    """
    expr_value = expr_like.to_expression() if isinstance(expr_like, Comparison) else expr_like
    if isinstance(expr_value, (float, int, bool)):
        return float(expr_value)
    else:
        pass
    return float(expr_value.eval_uid(uid_bindings))


def solve_static_algebraics(block: Block, uid_bindings: Dict[int, float], iterations: int = 6) -> None:
    """
    Solve algebraic equations by fixed-point correction over the current uid bindings.

    :param block: Symbolic block under test.
    :param uid_bindings: Numeric values by variable uid.
    :param iterations: Maximum fixed-point iterations.
    :return: None.
    """
    for _ in range(iterations):
        changed: bool = False
        var = None
        eq = None
        for var, eq in zip(block.algebraic_vars, block.algebraic_eqs):
            current: float = float(uid_bindings.get(var.uid, 0.0))
            try:
                residual: float = float(eq.eval_uid(uid_bindings))
            except ZeroDivisionError:
                residual = current

            updated: float = current - residual
            if math.isfinite(updated):
                if abs(updated - current) > 1e-12:
                    uid_bindings[var.uid] = updated
                    changed = True
                else:
                    pass
            else:
                pass

        if changed:
            pass
        else:
            break


def evaluate_runtime_expr(problem: FunctionalRuntimeProblem, expr_like: Expr | Comparison | float | int | bool, x: np.ndarray, params: np.ndarray, t: float) -> float:
    """
    Evaluate one runtime expression using the lightweight EMT runtime state.

    :param problem: Lightweight runtime object.
    :param expr_like: Expression-like object.
    :param x: Runtime state/algebraic vector.
    :param params: Runtime parameter vector.
    :param t: Current time.
    :return: Evaluated scalar result.
    """
    expr_value = expr_like.to_expression() if isinstance(expr_like, Comparison) else expr_like
    if isinstance(expr_value, (float, int, bool)):
        return float(expr_value)
    elif isinstance(expr_value, Var) and is_time_var_name(expr_value.name):
        return float(t)
    else:
        pass

    uid_bindings: dict[int, float] = {problem.glob_time.uid: float(t)}
    uid: int
    idx: int
    for uid, idx in problem.uid2idx_vars.items():
        uid_bindings[uid] = float(x[idx])
    for uid, idx in problem.uid2idx_event_params.items():
        uid_bindings[uid] = float(params[idx])

    expr_var: Var
    for expr_var in expr_value.get_vars():
        if is_time_var_name(expr_var.name):
            uid_bindings[expr_var.uid] = float(t)
        else:
            pass
    return float(expr_value.eval_uid(uid_bindings))


def bind_internal_surface_values(uid_bindings: Dict[int, float], contract_values: Dict[str, float] | None, vars_list: list[Var]) -> None:
    """
    Assign expected internal values into the current uid binding map.

    :param uid_bindings: Numeric values by variable uid.
    :param contract_values: Expected internal values by logical name.
    :param vars_list: Candidate internal variables.
    :return: None.
    """
    if contract_values is None:
        return
    else:
        pass

    logical_name: str
    value: float
    for logical_name, value in contract_values.items():
        matches: dict[int, Var] = dict()
        var: Var
        for var in vars_list:
            if matches_internal_name(var, logical_name):
                matches[var.uid] = var
            else:
                pass

        if len(matches) == 1:
            uid_bindings[next(iter(matches.values())).uid] = value
        else:
            raise KeyError(f"Could not bind internal surface '{logical_name}' uniquely")


def is_time_var_name(var_name: str) -> bool:
    """
    Check whether one variable name corresponds to the global simulation time.

    :param var_name: Variable name to inspect.
    :return: ``True`` if the variable is the global time signal.
    """
    if var_name in {"glob_time", "time"}:
        return True
    elif var_name.startswith("glob_time_") or var_name.startswith("time_"):
        return True
    else:
        return False


def append_unique_var(target_vars: list[Var], candidate_var: Var) -> None:
    """
    Append one variable only if its uid is not present yet.

    :param target_vars: Ordered destination variables.
    :param candidate_var: Candidate variable.
    :return: None.
    """
    existing_var: Var
    for existing_var in target_vars:
        if existing_var.uid == candidate_var.uid:
            return
        else:
            pass
    target_vars.append(candidate_var)


def append_expr_vars(target_vars: list[Var], expr_like: Expr | Comparison | float | int | bool) -> None:
    """
    Append every variable referenced by one expression-like object.

    :param target_vars: Ordered destination variables.
    :param expr_like: Expression-like input.
    :return: None.
    """
    expr_value = expr_like.to_expression() if isinstance(expr_like, Comparison) else expr_like
    if isinstance(expr_value, Expr):
        expr_var: Var
        for expr_var in expr_value.get_vars():
            append_unique_var(target_vars, expr_var)
    elif isinstance(expr_value, Var):
        append_unique_var(target_vars, expr_value)
    else:
        pass


def append_logic_exprs(target_exprs: list[Expr | Comparison | float | int | bool], logic) -> None:
    """
    Append all relevant expression-like fields from one supported procedural logic object.

    :param target_exprs: Destination expression list.
    :param logic: Procedural logic entry.
    :return: None.
    """
    if isinstance(logic, SampledValueLogic):
        target_exprs.append(logic.source_expr)
    elif isinstance(logic, FixedSampleLogic):
        target_exprs.append(logic.condition_expr)
    elif isinstance(logic, ResetOnRisingEdgeLogic):
        target_exprs.append(logic.reset_expr)
        target_exprs.append(logic.value_expr)
    elif isinstance(logic, PickupDropoffLogic):
        target_exprs.append(logic.bool_expr)
        target_exprs.append(logic.pickup_delay_expr)
        target_exprs.append(logic.drop_delay_expr)
    elif isinstance(logic, FlipFlopLogic):
        target_exprs.append(logic.set_expr)
        target_exprs.append(logic.reset_expr)
    elif isinstance(logic, AnalogFlipFlopLogic):
        target_exprs.append(logic.set_expr)
        target_exprs.append(logic.reset_expr)
        target_exprs.append(logic.input_expr)
    elif isinstance(logic, TimeDelayLogic):
        target_exprs.append(logic.source_expr)
        target_exprs.append(logic.delay_expr)
    elif isinstance(logic, MovingAverageLogic):
        target_exprs.append(logic.source_expr)
        target_exprs.append(logic.delay_expr)
        target_exprs.append(logic.window_expr)
    elif isinstance(logic, GradientLimiterLogic):
        target_exprs.append(logic.source_expr)
        target_exprs.append(logic.lower_rate_expr)
        target_exprs.append(logic.upper_rate_expr)
    else:
        raise TypeError(f"Unsupported procedural logic class for catalog harness: {type(logic).__name__}")


def get_logical_name(var_name: str) -> str:
    """
    Recover one stable logical signal name from one exported template variable name.

    :param var_name: Raw exported variable name.
    :return: Logical signal name.
    """
    prefix: str = var_name.split("_", 1)[0]
    if prefix.isidentifier():
        return prefix
    else:
        pass

    if "__" in var_name:
        tail: str = var_name.split("__", 1)[1]
        return tail.split("_", 1)[0]
    else:
        pass

    return var_name.split("_", 1)[0]


def matches_surface_name(var: Var, logical_name: str) -> bool:
    """
    Check whether one variable belongs to one logical surface name.

    :param var: Candidate variable.
    :param logical_name: Expected logical name.
    :return: ``True`` if the variable matches the logical surface name.
    """
    return var.name == logical_name or var.name.startswith(logical_name + "_")


def matches_param_name(var: Var, logical_name: str) -> bool:
    """
    Check whether one parameter variable matches a logical parameter name.

    :param var: Candidate parameter variable.
    :param logical_name: Expected logical parameter name.
    :return: ``True`` if the variable matches the logical parameter.
    """
    normalized_var_name: str = var.name.replace("_", "")
    normalized_logical_name: str = logical_name.replace("_", "")
    if var.name == logical_name:
        return True
    elif f"__{logical_name}_" in var.name:
        return True
    elif f"__{normalized_logical_name}_" in normalized_var_name:
        return True
    else:
        return False


def matches_internal_name(var: Var, logical_name: str) -> bool:
    """
    Check whether one internal variable matches a logical internal/state helper name.

    :param var: Candidate variable.
    :param logical_name: Expected logical internal name.
    :return: ``True`` if the internal name matches.
    """
    if matches_surface_name(var, logical_name):
        return True
    elif matches_param_name(var, logical_name):
        return True
    elif f"_{logical_name}_" in var.name:
        return True
    else:
        return False


def find_event_parameter_name(parameter_var: Var, parameter_ref: Expr) -> str:
    """
    Resolve the logical parameter name for one ``event_dict`` entry.

    :param parameter_var: Template parameter variable.
    :param parameter_ref: Parameter reference expression.
    :return: Logical parameter name.
    """
    if isinstance(parameter_ref, Expr):
        if isinstance(parameter_ref.name, str) and parameter_ref.name != "":
            return parameter_ref.name
        else:
            return get_logical_name(parameter_var.name)
    else:
        return get_logical_name(parameter_var.name)


def set_event_parameter_value(block: Block, uid_bindings: Dict[int, float], assigned_uids: set[int], logical_name: str, value: float) -> None:
    """
    Assign one logical parameter value into one block ``event_dict``.

    :param block: Symbolic block under test.
    :param uid_bindings: Current value bindings by uid.
    :param assigned_uids: Explicitly assigned uids.
    :param logical_name: Logical parameter name.
    :param value: Value to assign.
    :return: None.
    :raises KeyError: If no parameter matches the requested logical name.
    """
    normalized_logical_name: str = logical_name.replace("_", "")
    touched: bool = False
    parameter_var: Var
    parameter_ref: Var
    for parameter_var, parameter_ref in block.event_dict.items():
        candidate_name: str = find_event_parameter_name(parameter_var, parameter_ref)
        normalized_candidate_name: str = candidate_name.replace("_", "")
        if logical_name == candidate_name or normalized_logical_name == normalized_candidate_name:
            uid_bindings[parameter_var.uid] = value
            assigned_uids.add(parameter_var.uid)
            touched = True
        else:
            pass
    if touched:
        pass
    else:
        raise KeyError(f"Could not bind parameter '{logical_name}' in template event_dict")


def set_surface_values(vars_list: list[Var], uid_bindings: Dict[int, float], assigned_uids: set[int], logical_name: str, value: float, matcher) -> None:
    """
    Assign one logical value into a list-based variable surface.

    :param vars_list: Candidate variables.
    :param uid_bindings: Current value bindings by uid.
    :param assigned_uids: Explicitly assigned uids.
    :param logical_name: Logical variable name.
    :param value: Value to assign.
    :param matcher: Matching function.
    :return: None.
    :raises KeyError: If no variable matches the requested logical name.
    """
    touched: bool = False
    seen_uids: set[int] = set()
    candidate_var: Var
    for candidate_var in vars_list:
        if candidate_var.uid not in seen_uids:
            seen_uids.add(candidate_var.uid)
            if matcher(candidate_var, logical_name):
                uid_bindings[candidate_var.uid] = value
                assigned_uids.add(candidate_var.uid)
                touched = True
            else:
                pass
        else:
            pass
    if touched:
        pass
    else:
        raise KeyError(f"Could not bind '{logical_name}' anywhere in template surface")


def collect_internal_surface_vars(block: Block) -> list[Var]:
    """
    Collect the internal algebraic/state/helper surface needed by the static harness.

    :param block: Symbolic block under test.
    :return: Internal candidate variables.
    """
    internal_vars: list[Var] = list(block.algebraic_vars) + list(block.state_vars) + list(block.out_vars)
    for eq in block.algebraic_eqs:
        append_expr_vars(internal_vars, eq)
    for eq in block.state_eqs:
        append_expr_vars(internal_vars, eq)
    init_var: Var
    for init_var in list(block.init_eqs.keys()) + list(block.diff_init_eqs.keys()):
        append_unique_var(internal_vars, init_var)
    init_expr: Expr | Comparison | float | int | bool
    for init_expr in list(block.init_eqs.values()) + list(block.diff_init_eqs.values()):
        append_expr_vars(internal_vars, init_expr)
    for logic in block.procedural_logic:
        expr_values: list[Expr | Comparison | float | int | bool] = list()
        append_logic_exprs(expr_values, logic)
        expr_value: Expr | Comparison | float | int | bool
        for expr_value in expr_values:
            append_expr_vars(internal_vars, expr_value)
    return internal_vars


class FunctionalRuntimeProblem:
    """Minimal EMT runtime problem used by the dynamic catalog harness."""

    __slots__ = ["sys_block", "glob_time", "uid2idx_vars", "vars_by_uid", "uid2idx_event_params", "uid2idx_params", "_params_values"]

    def __init__(self, block, glob_time_var: Var) -> None:
        """
        Build the lightweight runtime state required by retained procedural logic.

        :param block: Symbolic block under test.
        :param glob_time_var: Global time variable used by runtime expressions.
        :return: None.
        """
        self.sys_block = block
        self.glob_time = glob_time_var

        ordered_vars: list[Var] = list()
        runtime_vars: list[Var] = list(block.event_dict.keys()) + list(block.mode_dict.keys())
        runtime_uids: set[int] = set(var.uid for var in runtime_vars)
        group_vars: list[list[Var]] = [block.state_vars, block.algebraic_vars, block.in_vars, list(block.init_eqs.keys()), list(block.diff_init_eqs.keys())]
        group_var_list: list[Var]
        candidate_var: Var
        for group_var_list in group_vars:
            for candidate_var in group_var_list:
                append_unique_var(ordered_vars, candidate_var)

        expr_list: list[Expr | Comparison | float | int | bool] = list(block.state_eqs) + list(block.algebraic_eqs) + list(block.init_eqs.values()) + list(block.diff_init_eqs.values())
        logic_entry = None
        for logic_entry in block.procedural_logic:
            append_logic_exprs(expr_list, logic_entry)

        expr_item: Expr | Comparison | float | int | bool
        for expr_item in expr_list:
            expr_vars: list[Var] = list()
            expr_var: Var
            append_expr_vars(expr_vars, expr_item)
            for expr_var in expr_vars:
                if expr_var.uid not in runtime_uids:
                    append_unique_var(ordered_vars, expr_var)
                else:
                    pass

        self.uid2idx_vars = {var.uid: idx for idx, var in enumerate(ordered_vars)}
        self.vars_by_uid = {var.uid: var for var in ordered_vars}

        dedup_runtime: list[Var] = list()
        runtime_var: Var
        for runtime_var in runtime_vars:
            append_unique_var(dedup_runtime, runtime_var)

        self.uid2idx_event_params = {var.uid: idx for idx, var in enumerate(dedup_runtime)}
        self.uid2idx_params = dict()
        self._params_values = list()

    def get_variable_parameter_number(self) -> int:
        """
        Return the runtime parameter vector length expected by procedural logic.

        :return: Runtime parameter count.
        """
        return len(self.uid2idx_event_params)

    def get_parameters_values(self) -> list[float]:
        """
        Return the stored runtime parameter values.

        :return: Runtime parameter values.
        """
        return self._params_values


def find_named_var(vars_list: list[Var], logical_name: str, matcher) -> Var:
    """
    Return the single variable matching one logical name from one variable list.

    :param vars_list: Candidate variables.
    :param logical_name: Expected logical name.
    :param matcher: Matching function.
    :return: Matching variable.
    :raises KeyError: If no variable matches.
    """
    candidate_var: Var
    for candidate_var in vars_list:
        if matcher(candidate_var, logical_name):
            return candidate_var
        else:
            pass
    raise KeyError(f"Could not locate '{logical_name}' in template surface")


def build_functional_contracts() -> list[FunctionalContract]:
    """
    Build the explicit static functional contracts for the exported DGS catalog.

    :return: Static functional contracts.
    """
    functional_contracts: list[FunctionalContract] = [
    FunctionalContract(label="const_zero", typ_id="50", inputs={}, params={}, outputs={"yo": 0.0}),
    FunctionalContract(label="const_one", typ_id="51", inputs={}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="const_pi", typ_id="58", inputs={}, params={}, outputs={"yo": math.pi}),
    FunctionalContract(label="const_e", typ_id="57", inputs={}, params={}, outputs={"yo": math.e}),
    FunctionalContract(label="gain_k", typ_id="179", inputs={"yi": 2.5}, params={"K": 4.0}, outputs={"yo": 10.0}),
    FunctionalContract(label="gain_inv_k", typ_id="174", inputs={"yi": 8.0}, params={"K": 4.0}, outputs={"yo": 2.0}),
    FunctionalContract(label="gain_identity", typ_id="172", inputs={"yi": -3.25}, params={}, outputs={"yo": -3.25}),
    FunctionalContract(label="gain_pi", typ_id="184", inputs={"yi": 2.0}, params={}, outputs={"yo": 2.0 * math.pi}),
    FunctionalContract(label="gain_k1_k2", typ_id="182", inputs={"yi": 2.0}, params={"K1": 3.0, "K2": 4.0}, outputs={"yo": 24.0}),
    FunctionalContract(label="gain_k1_div_k2", typ_id="183", inputs={"yi": 8.0}, params={"K1": 6.0, "K2": 4.0}, outputs={"yo": 12.0}),
    FunctionalContract(label="gain_k1_k2_div_k3", typ_id="180", inputs={"yi": 3.0}, params={"K1": 2.0, "K2": 5.0, "K3": 2.0}, outputs={"yo": 15.0}),
    FunctionalContract(label="cmp_gt_c", typ_id="22", inputs={"yi": 1.2}, params={"C": 1.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="cmp_ge_c", typ_id="23", inputs={"yi": 1.0}, params={"C": 1.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="cmp_lt_c", typ_id="24", inputs={"yi": 0.5}, params={"C": 1.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="cmp_le_c", typ_id="25", inputs={"yi": 0.9}, params={"C": 1.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="cmp_ne_c", typ_id="26", inputs={"yi": 2.0}, params={"C": 1.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="cmp_eq_sig", typ_id="27", inputs={"yi1": 2.0, "yi2": 2.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="cmp_ge_sig", typ_id="28", inputs={"yi1": 2.0, "yi2": 2.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="cmp_gt_sig", typ_id="29", inputs={"yi1": 3.0, "yi2": 2.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="cmp_lt_sig", typ_id="31", inputs={"yi1": 1.0, "yi2": 2.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="cmp_ne_sig", typ_id="32", inputs={"yi1": 1.0, "yi2": 2.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="logic_and2", typ_id="334", inputs={"yi1": 1.0, "yi2": 1.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="logic_and3", typ_id="335", inputs={"yi1": 1.0, "yi2": 1.0, "yi3": 1.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="logic_and4", typ_id="336", inputs={"yi1": 1.0, "yi2": 1.0, "yi3": 1.0, "yi4": 1.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="logic_or2", typ_id="341", inputs={"yi1": 0.0, "yi2": 1.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="logic_or3", typ_id="342", inputs={"yi1": 0.0, "yi2": 0.0, "yi3": 1.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="logic_or4", typ_id="343", inputs={"yi1": 0.0, "yi2": 0.0, "yi3": 0.0, "yi4": 1.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="logic_eor", typ_id="337", inputs={"yi1": 1.0, "yi2": 0.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="logic_equal", typ_id="338", inputs={"yi1": 1.0, "yi2": 1.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="logic_nor", typ_id="339", inputs={"yi1": 0.0, "yi2": 0.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="logic_not", typ_id="340", inputs={"yi": 1.0}, params={}, outputs={"yo": 0.0}),
    FunctionalContract(label="math_abs", typ_id="354", inputs={"yi": -3.5}, params={}, outputs={"yo": 3.5}),
    FunctionalContract(label="math_ceil", typ_id="355", inputs={"yi": 2.2}, params={}, outputs={"yo": 3.0}),
    FunctionalContract(label="math_exp", typ_id="356", inputs={"yi": 1.0}, params={}, outputs={"yo": math.e}),
    FunctionalContract(label="math_floor", typ_id="357", inputs={"yi": 2.8}, params={}, outputs={"yo": 2.0}),
    FunctionalContract(label="math_frac", typ_id="358", inputs={"yi": 2.8}, params={}, outputs={"yo": 0.8}),
    FunctionalContract(label="math_ln", typ_id="359", inputs={"yi": math.e}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="math_log10", typ_id="360", inputs={"yi": 100.0}, params={}, outputs={"yo": 2.0}),
    FunctionalContract(label="math_max2", typ_id="361", inputs={"yi1": -3.0, "yi2": 7.0}, params={}, outputs={"yo": 7.0}),
    FunctionalContract(label="math_max3", typ_id="362", inputs={"yi1": 1.0, "yi2": 5.0, "yi3": 3.0}, params={}, outputs={"yo": 5.0}),
    FunctionalContract(label="math_max4", typ_id="363", inputs={"yi1": 1.0, "yi2": 5.0, "yi3": 3.0, "yi4": 4.0}, params={}, outputs={"yo": 5.0}),
    FunctionalContract(label="math_min2", typ_id="364", inputs={"yi1": -3.0, "yi2": 7.0}, params={}, outputs={"yo": -3.0}),
    FunctionalContract(label="math_min3", typ_id="365", inputs={"yi1": 1.0, "yi2": -5.0, "yi3": 3.0}, params={}, outputs={"yo": -5.0}),
    FunctionalContract(label="math_min4", typ_id="366", inputs={"yi1": 1.0, "yi2": -5.0, "yi3": 3.0, "yi4": -4.0}, params={}, outputs={"yo": -5.0}),
    FunctionalContract(label="math_modulo", typ_id="367", inputs={"yi": 7.0}, params={"n": 4.0}, outputs={"yo": 3.0}),
    FunctionalContract(label="math_round", typ_id="370", inputs={"yi": 2.6}, params={}, outputs={"yo": 3.0}),
    FunctionalContract(label="math_sign", typ_id="371", inputs={"yi": -2.0}, params={}, outputs={"yo": -1.0}),
    FunctionalContract(label="math_sqrt", typ_id="372", inputs={"yi": 9.0}, params={}, outputs={"yo": 3.0}),
    FunctionalContract(label="math_square", typ_id="373", inputs={"yi": -4.0}, params={}, outputs={"yo": 16.0}),
    FunctionalContract(label="math_pow", typ_id="374", inputs={"yi": 2.0}, params={"p": 3.0}, outputs={"yo": 8.0}),
    FunctionalContract(label="math_acos", typ_id="383", inputs={"yi": 1.0}, params={}, outputs={"yo": 0.0}),
    FunctionalContract(label="math_asin", typ_id="384", inputs={"yi": 1.0}, params={}, outputs={"yo": math.pi / 2.0}),
    FunctionalContract(label="math_atan", typ_id="385", inputs={"yi": 1.0}, params={}, outputs={"yo": math.pi / 4.0}),
    FunctionalContract(label="math_atan2", typ_id="386", inputs={"re": 1.0, "im": 0.0}, params={}, outputs={"yo": 0.0}),
    FunctionalContract(label="math_cos", typ_id="389", inputs={"yi": 0.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="math_cosd", typ_id="390", inputs={"yi": 60.0}, params={}, outputs={"yo": 0.5}),
    FunctionalContract(label="math_cosh", typ_id="391", inputs={"yi": 0.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="math_sin", typ_id="393", inputs={"yi": math.pi / 2.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="math_sind", typ_id="394", inputs={"yi": 30.0}, params={}, outputs={"yo": 0.5}),
    FunctionalContract(label="math_sinh", typ_id="395", inputs={"yi": 0.0}, params={}, outputs={"yo": 0.0}),
    FunctionalContract(label="math_tan", typ_id="397", inputs={"yi": math.pi / 4.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="math_tand", typ_id="398", inputs={"yi": 45.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="math_tanh", typ_id="399", inputs={"yi": 0.0}, params={}, outputs={"yo": 0.0}),
    FunctionalContract(label="unit_deg_to_rad", typ_id="556", inputs={"yi": 180.0}, params={}, outputs={"yo": math.pi}),
    FunctionalContract(label="unit_rad_to_deg", typ_id="561", inputs={"yi": math.pi / 2.0}, params={}, outputs={"yo": 90.0}),
    FunctionalContract(label="unit_abs_to_pu", typ_id="554", inputs={"yi": 230.0}, params={"base": 115.0}, outputs={"yo": 2.0}),
    FunctionalContract(label="unit_pu_to_abs", typ_id="558", inputs={"yi": 2.0}, params={"base": 115.0}, outputs={"yo": 230.0}),
    FunctionalContract(label="limit_symmetric_upper", typ_id="317", inputs={"yi": 3.0}, params={"y_lim": 2.0}, outputs={"yo": 2.0}),
    FunctionalContract(label="limit_symmetric_lower", typ_id="317", inputs={"yi": -3.0}, params={"y_lim": 2.0}, outputs={"yo": -2.0}),
    FunctionalContract(
        label="transform_clarke",
        typ_id="534",
        inputs={"a": 1.0, "b": -0.5, "c": -0.5},
        params={},
        outputs={"alpha": 1.0, "beta": 0.0, "gamma": 0.0},
    ),
    FunctionalContract(
        label="transform_inv_clarke",
        typ_id="536",
        inputs={"alpha": 1.0, "beta": 0.0, "gamma": 0.0},
        params={},
        outputs={"a": 1.0, "b": -0.5, "c": -0.5},
    ),
    FunctionalContract(
        label="transform_park_dq",
        typ_id="539",
        inputs={"alpha": 1.0, "beta": 0.0, "cosphi": 0.0, "sinphi": 1.0},
        params={},
        outputs={"d": 0.0, "q": -1.0},
    ),
    FunctionalContract(
        label="transform_inv_park_dq",
        typ_id="537",
        inputs={"d": 0.0, "q": -1.0, "cosphi": 0.0, "sinphi": 1.0},
        params={},
        outputs={"alpha": 1.0, "beta": 0.0},
    ),
    FunctionalContract(
        label="filter_low_pass",
        typ_id="138",
        inputs={"yi": 4.0},
        params={"T": 2.0},
        outputs={"yo": 2.0},
        states={"x": 2.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="filter_low_pass_bypass",
        typ_id="134",
        inputs={"yi": 4.0},
        params={"T": 0.0},
        outputs={"yo": 4.0},
        states={"x": 2.0},
    ),
    FunctionalContract(
        label="filter_one_minus_k_over_one_plus_st_bypass_active",
        typ_id="127",
        inputs={"yi": 4.0},
        params={"K": 0.25, "T": 2.0},
        outputs={"yo": 2.0},
        states={"x": 2.0},
        state_derivatives={"x": 0.5},
    ),
    FunctionalContract(
        label="filter_low_pass_state_limit_param",
        typ_id="129",
        inputs={"yi": 4.0},
        params={"T": 2.0, "y_max": 2.0},
        outputs={"yo": 2.0},
        states={"x": 3.0},
        state_derivatives={"x": 0.5},
    ),
    FunctionalContract(
        label="filter_low_pass_state_and_rate_limit_param",
        typ_id="130",
        inputs={"yi": 4.0},
        params={"T": 2.0, "y_min": -2.0, "y_max": 2.0, "r_min": -2.0, "r_max": 2.0},
        outputs={"yo": 2.0},
        states={"x": 3.0},
        state_derivatives={"x": 0.5},
    ),
    FunctionalContract(
        label="filter_low_pass_state_limit_signal",
        typ_id="131",
        inputs={"yi": 4.0, "y_max": 2.0},
        params={"T": 2.0},
        outputs={"yo": 2.0},
        states={"x": 3.0},
        state_derivatives={"x": 0.5},
    ),
    FunctionalContract(
        label="filter_low_pass_state_limits_by_signals",
        typ_id="132",
        inputs={"yi": 4.0, "y_max": 2.0, "y_min": -2.0},
        params={"T": 2.0},
        outputs={"yo": 2.0},
        states={"x": 3.0},
        state_derivatives={"x": 0.5},
    ),
    FunctionalContract(
        label="filter_low_pass_output_limits_param",
        typ_id="133",
        inputs={"yi": 4.0},
        params={"T": 2.0, "y_min": -2.0, "y_max": 2.0},
        outputs={"yo": 2.0},
        states={"x": 3.0},
        state_derivatives={"x": 0.5},
    ),
    FunctionalContract(
        label="filter_low_pass_enable_active",
        typ_id="135",
        inputs={"yi": 4.0, "enable": 1.0},
        params={"T": 2.0},
        outputs={"yo": 2.0},
        states={"x": 2.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="filter_low_pass_and_dx_surface",
        typ_id="136",
        inputs={"yi": 4.0},
        params={"T": 2.0},
        outputs={"yo": 2.0, "dx": 1.0},
        states={"x": 2.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="filter_second_order_low_pass_equilibrium",
        typ_id="200",
        inputs={"yi": 1.0},
        params={"wc": 2.0, "zeta": 0.5},
        outputs={"yo": 1.0},
        states={"x1": 1.0, "x2": 0.0},
        state_derivatives={"x1": 0.0, "x2": 0.0},
    ),
    FunctionalContract(
        label="filter_second_order_bypass_equilibrium",
        typ_id="201",
        inputs={"yi": 4.0},
        params={"T1": 2.0, "T2": 1.0},
        outputs={"yo": 4.0},
        states={"x1": 4.0, "x2": 0.0},
        state_derivatives={"x1": 0.0, "x2": 0.0},
    ),
    FunctionalContract(
        label="filter_band_pass_steady_state_zero",
        typ_id="117",
        inputs={"yi": 4.0},
        params={"Flow": 1.0, "Fhigh": 4.0, "H0": 2.0},
        outputs={"yo": 0.0},
        states={"x1": 0.025330295910584444, "x2": 0.0},
        internals={"F0": 2.0, "w0": 12.566370614359172, "Q": 0.6666666666666666},
        state_derivatives={"x1": 0.0, "x2": 0.0},
    ),
    FunctionalContract(
        label="filter_butterworth_2nd_equilibrium",
        typ_id="144",
        inputs={"yi": 4.0},
        params={"wc": 2.0},
        outputs={"yo": 4.0},
        states={"x1": 1.0, "x2": 0.0},
        internals={"wc_2": 4.0},
        state_derivatives={"x1": 0.0, "x2": 0.0},
    ),
    FunctionalContract(
        label="filter_butterworth_3rd_equilibrium",
        typ_id="145",
        inputs={"yi": 8.0},
        params={"wc": 2.0},
        outputs={"yo": 8.0},
        states={"x1": 1.0, "x2": 0.0, "x3": 0.0},
        internals={"wc_2": 4.0, "wc_3": 8.0},
        state_derivatives={"x1": 0.0, "x2": 0.0, "x3": 0.0},
    ),
    FunctionalContract(
        label="filter_low_pass_rate_limit_param",
        typ_id="137",
        inputs={"yi": 4.0},
        params={"T": 2.0, "rdown": -2.0, "rup": 2.0},
        outputs={"yo": 2.0},
        states={"x": 2.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="filter_low_pass_rst_hold_zero_equilibrium",
        typ_id="159",
        inputs={"yi": 0.0, "hold": 0.0, "rst": 0.0},
        params={"T": 1.0},
        outputs={"yo": 0.0},
        states={"x": 0.0},
        state_derivatives={"x": 0.0},
    ),
    FunctionalContract(
        label="filter_low_pass_rst_sig_hold_zero_equilibrium",
        typ_id="167",
        inputs={"yi": 0.0, "hold": 0.0, "x_rst": 0.0, "rst": 0.0},
        params={"T": 1.0},
        outputs={"yo": 0.0},
        states={"x": 0.0},
        state_derivatives={"x": 0.0},
    ),
    FunctionalContract(
        label="filter_low_pass_rst_hold_param_limit_zero_equilibrium",
        typ_id="154",
        inputs={"yi": 0.0, "hold": 0.0, "rst": 0.0},
        params={"T": 1.0, "y_max": 100.0},
        outputs={"yo": 0.0},
        states={"x": 0.0},
        state_derivatives={"x": 0.0},
    ),
    FunctionalContract(
        label="filter_low_pass_rst_sig_hold_param_limit_zero_equilibrium",
        typ_id="162",
        inputs={"yi": 0.0, "hold": 0.0, "x_rst": 0.0, "rst": 0.0},
        params={"T": 1.0, "y_max": 100.0},
        outputs={"yo": 0.0},
        states={"x": 0.0},
        state_derivatives={"x": 0.0},
    ),
    FunctionalContract(
        label="filter_low_pass_rst_hold_state_and_rate_zero_equilibrium",
        typ_id="155",
        inputs={"yi": 0.0, "hold": 0.0, "rst": 0.0},
        params={"T": 1.0, "y_min": -100.0, "y_max": 100.0, "r_min": -100.0, "r_max": 100.0},
        outputs={"yo": 0.0},
        states={"x": 0.0},
        state_derivatives={"x": 0.0},
    ),
    FunctionalContract(
        label="filter_low_pass_rst_hold_signal_limit_zero_equilibrium",
        typ_id="156",
        inputs={"yi": 0.0, "hold": 0.0, "y_max": 100.0, "rst": 0.0},
        params={"T": 1.0},
        outputs={"yo": 0.0},
        states={"x": 0.0},
        state_derivatives={"x": 0.0},
    ),
    FunctionalContract(
        label="filter_low_pass_rst_hold_signal_limits_zero_equilibrium",
        typ_id="157",
        inputs={"yi": 0.0, "hold": 0.0, "y_min": -100.0, "y_max": 100.0, "rst": 0.0},
        params={"T": 1.0},
        outputs={"yo": 0.0},
        states={"x": 0.0},
        state_derivatives={"x": 0.0},
    ),
    FunctionalContract(
        label="filter_low_pass_rst_sig_hold_state_and_rate_zero_equilibrium",
        typ_id="163",
        inputs={"yi": 0.0, "hold": 0.0, "x_rst": 0.0, "rst": 0.0},
        params={"T": 1.0, "y_min": -100.0, "y_max": 100.0, "r_min": -100.0, "r_max": 100.0},
        outputs={"yo": 0.0},
        states={"x": 0.0},
        state_derivatives={"x": 0.0},
    ),
    FunctionalContract(
        label="filter_low_pass_rst_sig_hold_signal_limit_zero_equilibrium",
        typ_id="164",
        inputs={"yi": 0.0, "hold": 0.0, "x_rst": 0.0, "y_max": 100.0, "rst": 0.0},
        params={"T": 1.0},
        outputs={"yo": 0.0},
        states={"x": 0.0},
        state_derivatives={"x": 0.0},
    ),
    FunctionalContract(
        label="filter_low_pass_rst_sig_hold_signal_limits_zero_equilibrium",
        typ_id="165",
        inputs={"yi": 0.0, "hold": 0.0, "x_rst": 0.0, "y_min": -100.0, "y_max": 100.0, "rst": 0.0},
        params={"T": 1.0},
        outputs={"yo": 0.0},
        states={"x": 0.0},
        state_derivatives={"x": 0.0},
    ),
    FunctionalContract(
        label="filter_one_minus_k_over_one_plus_st",
        typ_id="128",
        inputs={"yi": 4.0},
        params={"K": 0.25, "T": 2.0},
        outputs={"yo": 2.0},
        states={"x": 2.0},
        state_derivatives={"x": 0.5},
    ),
    FunctionalContract(
        label="integrator_1_over_sT",
        typ_id="224",
        inputs={"yi": 4.0},
        params={"T": 2.0, "y_max": 10.0},
        outputs={"yo": 3.0},
        states={"x": 3.0},
        state_derivatives={"x": 2.0},
    ),
    FunctionalContract(
        label="integrator_1_over_s",
        typ_id="214",
        inputs={"yi": 4.0},
        params={},
        outputs={"yo": 3.0},
        states={"x": 3.0},
        state_derivatives={"x": 4.0},
    ),
    FunctionalContract(
        label="integrator_k_over_s",
        typ_id="236",
        inputs={"yi": 4.0},
        params={"K": 2.0},
        outputs={"yo": 5.0},
        states={"x": 5.0},
        state_derivatives={"x": 8.0},
    ),
    FunctionalContract(
        label="integrator_1_over_s_enable_active",
        typ_id="212",
        inputs={"yi": 4.0, "hold": 0.0},
        params={},
        outputs={"yo": 3.0},
        states={"x": 3.0},
        state_derivatives={"x": 4.0},
    ),
    FunctionalContract(
        label="integrator_1_over_s_incfreeze_zero_equilibrium",
        typ_id="213",
        inputs={"yi": 0.0},
        params={"Tincfreeze": 1.0},
        outputs={"yo": 0.0},
        states={"x": 0.0},
        state_derivatives={"x": 0.0},
        internals={"t0": 0.0},
    ),
    FunctionalContract(
        label="integrator_1_over_s_state_limits_by_param",
        typ_id="206",
        inputs={"yi": 4.0},
        params={"y_min": -2.0, "y_max": 2.0},
        outputs={"yo": 2.0},
        states={"x": 3.0},
        state_derivatives={"x": 4.0},
    ),
    FunctionalContract(
        label="integrator_1_over_s_state_limits_by_signal_hold_inactive",
        typ_id="207",
        inputs={"yi": 4.0, "hold": 0.0, "y_max": 2.0, "y_min": -2.0},
        params={},
        outputs={"yo": 2.0},
        states={"x": 3.0},
        state_derivatives={"x": 4.0},
    ),
    FunctionalContract(
        label="integrator_1_over_s_output_limits_by_param",
        typ_id="208",
        inputs={"yi": 4.0},
        params={"y_min": -2.0, "y_max": 2.0},
        outputs={"yo": 2.0},
        states={"x": 3.0},
        state_derivatives={"x": 4.0},
    ),
    FunctionalContract(
        label="integrator_1_over_s_output_limits_by_signal",
        typ_id="210",
        inputs={"yi": 4.0, "y_max": 2.0, "y_min": -2.0},
        params={},
        outputs={"yo": 2.0},
        states={"x": 3.0},
        state_derivatives={"x": 4.0},
    ),
    FunctionalContract(
        label="integrator_1_over_s_symmetric_signal_limit",
        typ_id="211",
        inputs={"yi": 4.0, "y_max": 2.0},
        params={},
        outputs={"yo": 2.0},
        states={"x": 3.0},
        state_derivatives={"x": 4.0},
    ),
    FunctionalContract(
        label="integrator_1_over_s_with_output_limit",
        typ_id="209",
        inputs={"yi": 4.0},
        params={"y_max": 2.0},
        outputs={"yo": 2.0},
        states={"x": 3.0},
        state_derivatives={"x": 4.0},
    ),
    FunctionalContract(
        label="integrator_1_over_sT_fallback_hold",
        typ_id="231",
        inputs={"yi": 4.0},
        params={"T": 0.0},
        outputs={"yo": 3.0},
        states={"x": 3.0},
    ),
    FunctionalContract(
        label="integrator_1_over_sT_bypass_incfreeze_zero_equilibrium",
        typ_id="230",
        inputs={"yi": 0.0},
        params={"T": 1.0, "Tincfreeze": 1.0},
        outputs={"yo": 0.0},
        states={"x": 0.0},
        state_derivatives={"x": 0.0},
        internals={"t0": 0.0},
    ),
    FunctionalContract(
        label="integrator_1_over_sT_plain",
        typ_id="233",
        inputs={"yi": 4.0},
        params={"T": 2.0},
        outputs={"yo": 3.0},
        states={"x": 3.0},
        state_derivatives={"x": 2.0},
    ),
    FunctionalContract(
        label="integrator_1_over_s_enable_reset_inactive",
        typ_id="243",
        inputs={"yi": 4.0, "hold": 0.0, "rst": 0.0},
        params={},
        outputs={"yo": 3.0},
        states={"x": 3.0},
        state_derivatives={"x": 4.0},
        internals={"xinc": 3.0},
    ),
    FunctionalContract(
        label="integrator_1_over_s_reset_zero_equilibrium",
        typ_id="245",
        inputs={"yi": 0.0, "rst": 0.0},
        params={},
        outputs={"yo": 0.0},
        states={"x": 0.0},
        state_derivatives={"x": 0.0},
        internals={"xinc": 0.0},
    ),
    FunctionalContract(
        label="integrator_1_over_s_reset_zero_equilibrium",
        typ_id="245",
        inputs={"yi": 0.0, "rst": 0.0},
        params={},
        outputs={"yo": 0.0},
        states={"x": 0.0},
        state_derivatives={"x": 0.0},
        internals={"xinc": 0.0},
    ),
    FunctionalContract(
        label="integrator_1_over_s_enable_reset_sig_inactive",
        typ_id="271",
        inputs={"yi": 4.0, "hold": 0.0, "xrst": 9.0, "rst": 0.0},
        params={},
        outputs={"yo": 3.0},
        states={"x": 3.0},
        state_derivatives={"x": 4.0},
    ),
    FunctionalContract(
        label="integrator_1_over_sT_state_limit_param",
        typ_id="216",
        inputs={"yi": 4.0},
        params={"T": 2.0, "y_max": 2.0},
        outputs={"yo": 2.0},
        states={"x": 3.0},
        state_derivatives={"x": 2.0},
    ),
    FunctionalContract(
        label="integrator_1_over_sT_state_limit_param_fb_active",
        typ_id="215",
        inputs={"yi": 4.0},
        params={"T": 2.0, "y_max": 2.0},
        outputs={"yo": 2.0},
        states={"x": 3.0},
        state_derivatives={"x": 2.0},
    ),
    FunctionalContract(
        label="integrator_1_over_sT_lower_output_limit_fb_active",
        typ_id="228",
        inputs={"yi": 4.0},
        params={"T": 2.0, "y_min": 2.0},
        outputs={"yo": 3.0},
        states={"x": 3.0},
        state_derivatives={"x": 2.0},
    ),
    FunctionalContract(
        label="lead_lag",
        typ_id="298",
        inputs={"yi": 4.0},
        params={"Ta": 2.0, "Tb": 0.5},
        outputs={"yo": 2.5},
        states={"x": 2.0},
        internals={"dx": 1.0},
    ),
    FunctionalContract(
        label="filter_one_over_one_plus_st_half_time_constant",
        typ_id="139",
        inputs={"yi": 4.0},
        params={"T": 2.0},
        outputs={"yo": 2.0},
        states={"x": 2.0},
        state_derivatives={"x": 2.0},
    ),
    FunctionalContract(
        label="filter_one_over_k_plus_st_bypass_active",
        typ_id="140",
        inputs={"yi": 4.0},
        params={"K": 2.0, "T": 2.0},
        outputs={"yo": 1.0},
        states={"x": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="filter_one_over_k_plus_st",
        typ_id="141",
        inputs={"yi": 4.0},
        params={"K": 2.0, "T": 2.0},
        outputs={"yo": 1.0},
        states={"x": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="filter_one_over_k_times_one_over_one_plus_st_bypass_active",
        typ_id="143",
        inputs={"yi": 4.0},
        params={"K": 2.0, "T": 2.0},
        outputs={"yo": 1.0},
        states={"x": 1.0},
        state_derivatives={"x": 0.5},
    ),
    FunctionalContract(
        label="filter_k_over_one_plus_st_bypass_active",
        typ_id="150",
        inputs={"yi": 4.0},
        params={"K": 2.0, "T": 2.0},
        outputs={"yo": 3.0},
        states={"x": 3.0},
        state_derivatives={"x": 2.5},
    ),
    FunctionalContract(
        label="filter_k_over_one_plus_st",
        typ_id="151",
        inputs={"yi": 4.0},
        params={"K": 2.0, "T": 2.0},
        outputs={"yo": 3.0},
        states={"x": 3.0},
        state_derivatives={"x": 2.5},
    ),
    FunctionalContract(
        label="filter_k1_plus_k2_over_one_plus_st",
        typ_id="152",
        inputs={"yi": 4.0},
        params={"K1": 1.0, "K2": 2.0, "T": 2.0},
        outputs={"yo": 10.0},
        states={"x": 3.0},
        state_derivatives={"x": 0.5},
    ),
    FunctionalContract(
        label="filter_kt_over_one_plus_st",
        typ_id="153",
        inputs={"yi": 4.0},
        params={"K": 3.0, "T": 2.0},
        outputs={"yo": 6.0},
        states={"x": 6.0},
        state_derivatives={"x": 9.0},
    ),
    FunctionalContract(
        label="filter_k_over_one_plus_st_state_limit_param",
        typ_id="146",
        inputs={"yi": 4.0, "y_max": 10.0},
        params={"K": 2.0, "T": 2.0, "y_min": 1.0},
        outputs={"yo": 3.0},
        states={"x": 3.0},
        state_derivatives={"x": 2.5},
    ),
    FunctionalContract(
        label="filter_k_over_one_plus_st_state_limit_signal",
        typ_id="147",
        inputs={"yi": 4.0, "y_max": 10.0, "y_min": 1.0},
        params={"K": 2.0, "T": 2.0},
        outputs={"yo": 3.0},
        states={"x": 3.0},
        state_derivatives={"x": 2.5},
    ),
    FunctionalContract(
        label="filter_k_over_one_plus_st_output_limits_param",
        typ_id="149",
        inputs={"yi": 4.0},
        params={"K": 2.0, "T": 2.0, "y_min": 1.0, "y_max": 10.0},
        outputs={"yo": 3.0},
        states={"x": 3.0},
        state_derivatives={"x": 2.5},
    ),
    FunctionalContract(
        label="derivative_first_order",
        typ_id="110",
        inputs={"yi": 4.0},
        params={"T": 2.0},
        outputs={"yo": 1.0},
        states={"x": 2.0},
        internals={"dx": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="derivative_gain_first_order",
        typ_id="113",
        inputs={"yi": 4.0},
        params={"T": 2.0, "K": 3.0},
        outputs={"yo": 3.0},
        states={"x": 2.0},
        internals={"dx": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="low_pass_one_minus_k_bypass_active",
        typ_id="127",
        inputs={"yi": 4.0},
        params={"K": 0.25, "T": 2.0},
        outputs={"yo": 2.0},
        states={"x": 2.0},
        state_derivatives={"x": 0.5},
    ),
    FunctionalContract(
        label="low_pass_one_minus_k",
        typ_id="128",
        inputs={"yi": 4.0},
        params={"K": 0.25, "T": 2.0},
        outputs={"yo": 2.0},
        states={"x": 2.0},
        state_derivatives={"x": 0.5},
    ),
    FunctionalContract(
        label="low_pass_half_time_constant",
        typ_id="139",
        inputs={"yi": 4.0},
        params={"T": 2.0},
        outputs={"yo": 2.0},
        states={"x": 2.0},
        state_derivatives={"x": 2.0},
    ),
    FunctionalContract(
        label="low_pass_one_over_k_plus_st_bypass_active",
        typ_id="140",
        inputs={"yi": 4.0},
        params={"K": 2.0, "T": 2.0},
        outputs={"yo": 1.0},
        states={"x": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="low_pass_one_over_k_plus_st",
        typ_id="141",
        inputs={"yi": 4.0},
        params={"K": 2.0, "T": 2.0},
        outputs={"yo": 1.0},
        states={"x": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="low_pass_one_over_k_times_one_over_one_plus_st_bypass_active",
        typ_id="143",
        inputs={"yi": 4.0},
        params={"K": 2.0, "T": 2.0},
        outputs={"yo": 1.0},
        states={"x": 1.0},
        state_derivatives={"x": 0.5},
    ),
    FunctionalContract(
        label="low_pass_k_over_one_plus_st_bypass_active",
        typ_id="150",
        inputs={"yi": 4.0},
        params={"K": 2.0, "T": 2.0},
        outputs={"yo": 3.0},
        states={"x": 3.0},
        state_derivatives={"x": 2.5},
    ),
    FunctionalContract(
        label="low_pass_k_over_one_plus_st",
        typ_id="151",
        inputs={"yi": 4.0},
        params={"K": 2.0, "T": 2.0},
        outputs={"yo": 3.0},
        states={"x": 3.0},
        state_derivatives={"x": 2.5},
    ),
    FunctionalContract(
        label="low_pass_k1_plus_k2_over_one_plus_st",
        typ_id="152",
        inputs={"yi": 4.0},
        params={"K1": 1.0, "K2": 2.0, "T": 2.0},
        outputs={"yo": 10.0},
        states={"x": 3.0},
        state_derivatives={"x": 0.5},
    ),
    FunctionalContract(
        label="low_pass_kt_over_one_plus_st",
        typ_id="153",
        inputs={"yi": 4.0},
        params={"K": 3.0, "T": 2.0},
        outputs={"yo": 6.0},
        states={"x": 6.0},
        state_derivatives={"x": 9.0},
    ),
    FunctionalContract(
        label="filter_second_order_low_pass",
        typ_id="200",
        inputs={"yi": 1.0},
        params={"wc": 2.0, "zeta": 0.5},
        outputs={"yo": 1.0},
        states={"x1": 1.0, "x2": 0.0},
        state_derivatives={"x1": 0.0, "x2": 0.0},
    ),
    FunctionalContract(
        label="filter_second_order_bypass_active",
        typ_id="201",
        inputs={"yi": 4.0},
        params={"T1": 2.0, "T2": 1.0},
        outputs={"yo": 4.0},
        states={"x1": 4.0, "x2": 0.0},
        state_derivatives={"x1": 0.0, "x2": 0.0},
    ),
    FunctionalContract(
        label="filter_band_pass_steady_state_zero",
        typ_id="117",
        inputs={"yi": 4.0},
        params={"Flow": 1.0, "Fhigh": 4.0, "H0": 2.0},
        outputs={"yo": 0.0},
        states={"x1": 0.025330295910584444, "x2": 0.0},
        internals={"F0": 2.0, "w0": 12.566370614359172, "Q": 0.6666666666666666},
        state_derivatives={"x1": 0.0, "x2": 0.0},
    ),
    FunctionalContract(
        label="filter_butterworth_2nd_steady_state",
        typ_id="144",
        inputs={"yi": 4.0},
        params={"wc": 2.0},
        outputs={"yo": 4.0},
        states={"x1": 1.0, "x2": 0.0},
        internals={"wc_2": 4.0},
        state_derivatives={"x1": 0.0, "x2": 0.0},
    ),
    FunctionalContract(
        label="filter_butterworth_3rd_steady_state",
        typ_id="145",
        inputs={"yi": 8.0},
        params={"wc": 2.0},
        outputs={"yo": 8.0},
        states={"x1": 1.0, "x2": 0.0, "x3": 0.0},
        internals={"wc_2": 4.0, "wc_3": 8.0},
        state_derivatives={"x1": 0.0, "x2": 0.0, "x3": 0.0},
    ),
    FunctionalContract(
        label="high_pass_st_over_one_plus_st_bypass_active",
        typ_id="123",
        inputs={"yi": 4.0},
        params={"T": 2.0},
        outputs={"yo": 2.0},
        states={"x": 2.0},
        internals={"dx": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="high_pass_st_over_one_plus_st_enable_active",
        typ_id="124",
        inputs={"yi": 4.0},
        params={"T": 2.0},
        outputs={"yo": 2.0},
        states={"x": 2.0},
        internals={"dx": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="high_pass_stb_over_one_plus_sta_fb_active",
        typ_id="125",
        inputs={"yi": 4.0},
        params={"Ta": 2.0, "Tb": 3.0},
        outputs={"yo": 3.0},
        states={"x": 2.0},
        internals={"dx": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="high_pass_stld_over_one_plus_stlg_fb_active",
        typ_id="126",
        inputs={"yi": 4.0},
        params={"Tlg": 2.0, "Tld": 3.0},
        outputs={"yo": 3.0},
        states={"x": 2.0},
        internals={"dx": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="derivative_gain_first_order_fallback_active",
        typ_id="112",
        inputs={"yi": 4.0},
        params={"K": 3.0, "T": 2.0},
        outputs={"yo": 3.0},
        states={"x": 2.0},
        internals={"dx": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="derivative_gain_time_constant_first_order",
        typ_id="121",
        inputs={"yi": 4.0},
        params={"K": 3.0, "T": 2.0},
        outputs={"yo": 6.0},
        states={"x": 2.0},
        internals={"dx": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="derivative_second_order_gain",
        typ_id="205",
        inputs={"yi": 4.0},
        params={"K": 3.0, "T": 2.0},
        outputs={"yo": 0.0},
        states={"x1": 12.0, "x2": 0.0},
        internals={"dx1": 0.0, "dx2": 0.0},
        state_derivatives={"x1": 0.0, "x2": 0.0},
    ),
    FunctionalContract(
        label="high_pass_st_over_one_plus_st_bypass_active",
        typ_id="123",
        inputs={"yi": 4.0},
        params={"T": 2.0},
        outputs={"yo": 2.0},
        states={"x": 2.0},
        internals={"dx": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="high_pass_st_over_one_plus_st_enable_active",
        typ_id="124",
        inputs={"yi": 4.0},
        params={"T": 2.0},
        outputs={"yo": 2.0},
        states={"x": 2.0},
        internals={"dx": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="high_pass_stb_over_one_plus_sta_fb_active",
        typ_id="125",
        inputs={"yi": 4.0},
        params={"Ta": 2.0, "Tb": 3.0},
        outputs={"yo": 3.0},
        states={"x": 2.0},
        internals={"dx": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="high_pass_stld_over_one_plus_stlg_fb_active",
        typ_id="126",
        inputs={"yi": 4.0},
        params={"Tlg": 2.0, "Tld": 3.0},
        outputs={"yo": 3.0},
        states={"x": 2.0},
        internals={"dx": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="pi_unity_plus_k_over_st",
        typ_id="437",
        inputs={"yi": 2.0},
        params={"K": 4.0, "T": 2.0},
        outputs={"yo": 6.0},
        states={"x": 4.0},
        state_derivatives={"x": 4.0},
    ),
    FunctionalContract(
        label="pi_limited_1_plus_st_over_kst",
        typ_id="433",
        inputs={"yi": 4.0},
        params={"K": 2.0, "T": 2.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 3.0},
        states={"x": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="pi_tunable_kc_direct_tp",
        typ_id="438",
        inputs={"yi": 2.0},
        params={"K_p": 1.0, "T_p": 2.0, "theta_p": 1.0, "ControlTuning": 1.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 3.2222222222222223},
        states={"x": 1.0},
        internals={"tau_c": 0.8, "Kc": 1.1111111111111112, "Ti": 2.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="pi_tunable_kc_from_rise_time",
        typ_id="439",
        inputs={"yi": 2.0},
        params={"K_p": 1.0, "T_rise": 4.394, "theta_p": 1.0, "ControlTuning": 1.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 3.2222222222222223},
        states={"x": 1.0},
        internals={"T_p": 2.0, "tau_c": 0.8, "Kc": 1.1111111111111112, "Ti": 2.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="pi_parallel_kp_1_over_sti",
        typ_id="443",
        inputs={"yi": 2.0},
        params={"Kp": 3.0, "Ti": 2.0},
        outputs={"yo": 7.0},
        states={"x": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="pi_parallel_kp_1_over_sti_with_limits",
        typ_id="442",
        inputs={"yi": 2.0},
        params={"Kp": 3.0, "Ti": 2.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 7.0},
        states={"x": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="pi_series_kp_1_ti_plus_s_over_s",
        typ_id="441",
        inputs={"yi": 2.0},
        params={"Kp": 3.0, "Ti": 2.0},
        outputs={"yo": 7.0},
        states={"x": 1.0},
        state_derivatives={"x": 3.0},
    ),
    FunctionalContract(
        label="pi_series_kp_1_ti_plus_s_over_s_rst_hold_inactive",
        typ_id="454",
        inputs={"yi": 2.0, "hold": 0.0, "rst": 0.0},
        params={"Kp": 3.0, "Ti": 2.0},
        outputs={"yo": 7.0},
        states={"x": 1.0},
        state_derivatives={"x": 3.0},
        internals={"x_init": 1.0},
    ),
    FunctionalContract(
        label="pi_tunable_kc_direct_tp_rst_hold_inactive",
        typ_id="450",
        inputs={"yi": 2.0, "hold": 0.0, "rst": 0.0},
        params={"K_p": 1.0, "T_p": 2.0, "theta_p": 1.0, "ControlTuning": 1.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 3.2222222222222223},
        states={"x": 1.0},
        internals={"tau_c": 0.8, "Kc": 1.1111111111111112, "Ti": 2.0, "x_init": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="pi_tunable_kc_from_rise_time_rst_hold_inactive",
        typ_id="451",
        inputs={"yi": 2.0, "hold": 0.0, "rst": 0.0},
        params={"K_p": 1.0, "T_rise": 4.394, "theta_p": 1.0, "ControlTuning": 1.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 3.2222222222222223},
        states={"x": 1.0},
        internals={"T_p": 2.0, "tau_c": 0.8, "Kc": 1.1111111111111112, "Ti": 2.0, "x_init": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="pi_parallel_kp_1_over_sti_rst_hold_inactive",
        typ_id="456",
        inputs={"yi": 2.0, "hold": 0.0, "rst": 0.0},
        params={"Kp": 3.0, "Ti": 2.0},
        outputs={"yo": 7.0},
        states={"x": 1.0},
        state_derivatives={"x": 1.0},
        internals={"x_init": 1.0},
    ),
    FunctionalContract(
        label="pi_parallel",
        typ_id="449",
        inputs={"yi": 2.0},
        params={"Kp": 3.0, "Ki": 4.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        state_derivatives={"x": 8.0},
    ),
    FunctionalContract(
        label="pi_series_with_tracking_signal",
        typ_id="440",
        inputs={"yi": 2.0, "yo_lim": 7.0},
        params={"Kp": 3.0, "Ti": 2.0, "Tt": 1.0},
        outputs={"yo": 7.0},
        states={"x": 1.0},
        state_derivatives={"x": 3.0},
    ),
    FunctionalContract(
        label="pi_parallel_with_param_limits",
        typ_id="445",
        inputs={"yi": 2.0},
        params={"Kp": 3.0, "Ki": 4.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        state_derivatives={"x": 8.0},
    ),
    FunctionalContract(
        label="pi_parallel_with_signal_limits",
        typ_id="447",
        inputs={"yi": 2.0, "ymin": -100.0, "ymax": 100.0},
        params={"Kp": 3.0, "Ki": 4.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        state_derivatives={"x": 8.0},
    ),
    FunctionalContract(
        label="pi_parallel_kp_ki_over_s_rst_hold_inactive",
        typ_id="461",
        inputs={"yi": 2.0, "hold": 0.0, "rst": 0.0},
        params={"Kp": 3.0, "Ki": 4.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        state_derivatives={"x": 8.0},
        internals={"x_init": 5.0},
    ),
    FunctionalContract(
        label="pi_parallel_rst_sig_hold_inactive",
        typ_id="473",
        inputs={"yi": 2.0, "hold": 0.0, "x_rst": 5.0, "rst": 0.0},
        params={"Kp": 3.0, "Ki": 4.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        state_derivatives={"x": 8.0},
    ),
    FunctionalContract(
        label="pi_parallel_kp_1_over_sti_rst_sig_hold_inactive",
        typ_id="468",
        inputs={"yi": 2.0, "hold": 0.0, "x_rst": 1.0, "rst": 0.0},
        params={"Kp": 3.0, "Ti": 2.0},
        outputs={"yo": 7.0},
        states={"x": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="pi_tunable_kc_direct_tp_rst_sig_hold_inactive",
        typ_id="463",
        inputs={"yi": 2.0, "hold": 0.0, "x_rst": 1.0, "rst": 0.0},
        params={"K_p": 1.0, "T_p": 2.0, "theta_p": 1.0, "ControlTuning": 1.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 3.2222222222222223},
        states={"x": 1.0},
        internals={"tau_c": 0.8, "Kc": 1.1111111111111112, "Ti": 2.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="pi_tunable_kc_from_rise_time_rst_sig_hold_inactive",
        typ_id="464",
        inputs={"yi": 2.0, "hold": 0.0, "x_rst": 1.0, "rst": 0.0},
        params={"K_p": 1.0, "T_rise": 4.394, "theta_p": 1.0, "ControlTuning": 1.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 3.2222222222222223},
        states={"x": 1.0},
        internals={"T_p": 2.0, "tau_c": 0.8, "Kc": 1.1111111111111112, "Ti": 2.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="pi_parallel_kp_ki_over_s_tracking_rst_hold_inactive",
        typ_id="457",
        inputs={"yi": 2.0, "hold": 0.0, "yo_lim": 11.0, "rst": 0.0},
        params={"Kp": 3.0, "Ki": 4.0, "Tt": 1.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        state_derivatives={"x": 8.0},
        internals={"x_init": 5.0},
    ),
    FunctionalContract(
        label="pid_parallel_limited",
        typ_id="448",
        inputs={"yi": 2.0},
        params={"Kp": 3.0, "Ki": 4.0, "Kd": 5.0, "Td": 2.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 16.0},
        states={"x1": 5.0, "x2": 0.0},
        internals={"dx2": 1.0, "yk": 6.0, "yd": 5.0, "yis": 5.0},
        state_derivatives={"x1": 8.0, "x2": 1.0},
    ),
    FunctionalContract(
        label="pid_parallel_rst_sig_hold_inactive",
        typ_id="474",
        inputs={"yi": 2.0, "hold": 0.0, "x1_rst": 5.0, "rst": 0.0},
        params={"Kp": 3.0, "Ki": 4.0, "Kd": 5.0, "Td": 2.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 16.0},
        states={"x1": 5.0, "x2": 0.0},
        internals={"dx2": 1.0, "yk": 6.0, "yd": 5.0, "yis": 5.0},
        state_derivatives={"x1": 8.0, "x2": 1.0},
    ),
    FunctionalContract(
        label="time_source",
        typ_id="488",
        inputs={},
        params={},
        outputs={"t": 1.25},
        internals={"glob_time": 1.25},
    ),
    FunctionalContract(
        label="dsl_time_source",
        typ_id="87",
        inputs={},
        params={},
        outputs={"yo": 1.25},
        internals={"glob_time": 1.25},
    ),
    FunctionalContract(
        label="sine_wave_generator_peak",
        typ_id="485",
        inputs={},
        params={"a": 2.0, "f": 1.0, "phi": 90.0},
        outputs={"yo": 2.0},
        internals={"glob_time": 0.0, "t": 0.0, "two_pi": 2.0 * math.pi, "deg_to_rad": 180.0 / math.pi},
    ),
    FunctionalContract(
        label="sine_wave_generator_after_t0",
        typ_id="484",
        inputs={},
        params={"a": 2.0, "f": 1.0, "phi": 90.0, "t0": 0.25},
        outputs={"yo": 0.0},
        internals={"glob_time": 0.5, "t": 0.5, "two_pi": 2.0 * math.pi, "deg_to_rad": 180.0 / math.pi},
    ),
    FunctionalContract(
        label="sine_wave_generator_before_t0",
        typ_id="484",
        inputs={},
        params={"a": 2.0, "f": 1.0, "phi": 90.0, "t0": 0.25},
        outputs={"yo": 0.0},
        internals={"glob_time": 0.1, "t": 0.1, "two_pi": 2.0 * math.pi, "deg_to_rad": 180.0 / math.pi},
    ),
    FunctionalContract(
        label="sawtooth_wave_generator_fraction",
        typ_id="483",
        inputs={},
        params={"f": 2.0},
        outputs={"yo": 0.5},
        internals={"glob_time": 0.25, "t0": 0.0},
    ),
    FunctionalContract(
        label="sawtooth_wave_generator_ip_fraction",
        typ_id="482",
        inputs={},
        params={"f": 2.0},
        outputs={"yo": 0.5},
        internals={"glob_time": 0.25, "t0": 0.0},
    ),
    FunctionalContract(
        label="triangle_wave_generator_midpoint",
        typ_id="489",
        inputs={},
        params={"f": 1.0},
        outputs={"yo": 0.5},
        internals={"glob_time": 0.25, "toffset": 0.0},
    ),
    FunctionalContract(
        label="triangle_wave_generator_ip_midpoint",
        typ_id="490",
        inputs={},
        params={"f": 1.0},
        outputs={"yo": 0.5},
        internals={"glob_time": 0.25, "toffset": 0.0},
    ),
    FunctionalContract(
        label="square_wave_generator_high",
        typ_id="486",
        inputs={},
        params={"f": 1.0},
        outputs={"yo": 1.0},
        internals={"glob_time": 0.75, "t0": 0.0},
    ),
    FunctionalContract(
        label="square_wave_generator_low",
        typ_id="486",
        inputs={},
        params={"f": 1.0},
        outputs={"yo": 0.0},
        internals={"glob_time": 0.25, "t0": 0.0},
    ),
    FunctionalContract(
        label="square_wave_generator_ip_high",
        typ_id="487",
        inputs={},
        params={"f": 1.0},
        outputs={"yo": 1.0},
        internals={"glob_time": 0.75, "t0": 0.0},
    ),
    FunctionalContract(
        label="square_wave_generator_ip_low",
        typ_id="487",
        inputs={},
        params={"f": 1.0},
        outputs={"yo": 0.0},
        internals={"glob_time": 0.25, "t0": 0.0},
    ),
    FunctionalContract(
        label="timer_elapsed_formula",
        typ_id="531",
        inputs={"rst": 0.0},
        params={},
        outputs={"yo": 2.0},
        internals={"glob_time": 10.0, "dt": 8.0},
    ),
    FunctionalContract(
        label="enable_signal_fixed_on",
        typ_id="504",
        inputs={"yi": 4.0},
        params={"Enable": 1.0},
        outputs={"yo": 4.0},
    ),
    FunctionalContract(
        label="enable_signal_fixed_off",
        typ_id="504",
        inputs={"yi": 4.0},
        params={"Enable": 0.0},
        outputs={"yo": 0.0},
    ),
    FunctionalContract(
        label="enable_signal_dynamic_on",
        typ_id="505",
        inputs={"yi": 4.0},
        params={"Enable": 1.0},
        outputs={"yo": 4.0},
    ),
    FunctionalContract(
        label="enable_signal_dynamic_off",
        typ_id="505",
        inputs={"yi": 4.0},
        params={"Enable": 0.0},
        outputs={"yo": 0.0},
    ),
    FunctionalContract(
        label="switch_par_2_1_left",
        typ_id="510",
        inputs={},
        params={"sw": -1.0, "K1": 7.0, "K2": 9.0},
        outputs={"yo": 7.0},
    ),
    FunctionalContract(
        label="switch_par_2_1_right",
        typ_id="510",
        inputs={},
        params={"sw": 2.0, "K1": 7.0, "K2": 9.0},
        outputs={"yo": 9.0},
    ),
    FunctionalContract(
        label="switch_sig_1_1_fixed_enable",
        typ_id="512",
        inputs={"yi": 4.0, "Enable": 1.0},
        params={"p": 9.0},
        outputs={"yo": 4.0},
    ),
    FunctionalContract(
        label="switch_sig_1_1_fixed_disable",
        typ_id="512",
        inputs={"yi": 4.0, "Enable": 0.0},
        params={"p": 9.0},
        outputs={"yo": 9.0},
    ),
    FunctionalContract(
        label="switch_sig_1_2_left",
        typ_id="515",
        inputs={"yi": 5.0},
        params={"sw": 0.0},
        outputs={"yo1": 5.0, "yo2": 0.0},
    ),
    FunctionalContract(
        label="switch_sig_1_2_right",
        typ_id="515",
        inputs={"yi": 5.0},
        params={"sw": 1.0},
        outputs={"yo1": 0.0, "yo2": 5.0},
    ),
    FunctionalContract(
        label="switch_sig_2_1_by_sig_left",
        typ_id="522",
        inputs={"yi1": 7.0, "yi2": 9.0, "sw": -1.0},
        params={},
        outputs={"yo": 7.0},
    ),
    FunctionalContract(
        label="switch_sig_2_1_by_sig_right",
        typ_id="522",
        inputs={"yi1": 7.0, "yi2": 9.0, "sw": 2.0},
        params={},
        outputs={"yo": 9.0},
    ),
    FunctionalContract(
        label="switch_sig_2_1_not_eq_k_true",
        typ_id="517",
        inputs={"yi1": 7.0, "yi2": 9.0, "sw": 2.0},
        params={"K": 3.0},
        outputs={"yo": 7.0},
    ),
    FunctionalContract(
        label="switch_sig_2_1_bool_left",
        typ_id="520",
        inputs={"yi1": 7.0, "yi2": 9.0, "sw": 0.0},
        params={},
        outputs={"yo": 7.0},
    ),
    FunctionalContract(
        label="switch_sig_2_1_bool_right",
        typ_id="520",
        inputs={"yi1": 7.0, "yi2": 9.0, "sw": 1.0},
        params={},
        outputs={"yo": 9.0},
    ),
    FunctionalContract(
        label="switch_par_1_1_fixed_enable",
        typ_id="506",
        inputs={"yi": 4.0},
        params={"Enable": 1.0, "p": 9.0},
        outputs={"yo": 4.0},
    ),
    FunctionalContract(
        label="switch_par_1_1_fixed_disable",
        typ_id="506",
        inputs={"yi": 4.0},
        params={"Enable": 0.0, "p": 9.0},
        outputs={"yo": 9.0},
    ),
    FunctionalContract(
        label="switch_par_1_1_dynamic_enable",
        typ_id="507",
        inputs={"yi": 4.0},
        params={"Enable": 1.0, "p": 9.0},
        outputs={"yo": 4.0},
    ),
    FunctionalContract(
        label="switch_par_1_1_dynamic_disable",
        typ_id="507",
        inputs={"yi": 4.0},
        params={"Enable": 0.0, "p": 9.0},
        outputs={"yo": 9.0},
    ),
    FunctionalContract(
        label="switch_par_1_2_left",
        typ_id="508",
        inputs={},
        params={"sw": 0.0, "K": 7.0},
        outputs={"yo1": 7.0, "yo2": 0.0},
    ),
    FunctionalContract(
        label="switch_par_1_2_right",
        typ_id="508",
        inputs={},
        params={"sw": 1.0, "K": 7.0},
        outputs={"yo1": 0.0, "yo2": 7.0},
    ),
    FunctionalContract(
        label="switch_par_2_1_by_sig_left",
        typ_id="511",
        inputs={"sw": -1.0},
        params={"K1": 7.0, "K2": 9.0},
        outputs={"yo": 7.0},
    ),
    FunctionalContract(
        label="switch_par_2_1_by_sig_right",
        typ_id="511",
        inputs={"sw": 2.0},
        params={"K1": 7.0, "K2": 9.0},
        outputs={"yo": 9.0},
    ),
    FunctionalContract(
        label="switch_sig_1_1_dynamic_enable",
        typ_id="513",
        inputs={"yi": 4.0, "Enable": 1.0},
        params={"p": 9.0},
        outputs={"yo": 4.0},
    ),
    FunctionalContract(
        label="switch_sig_1_1_dynamic_disable",
        typ_id="513",
        inputs={"yi": 4.0, "Enable": 0.0},
        params={"p": 9.0},
        outputs={"yo": 9.0},
    ),
    FunctionalContract(
        label="switch_sig_2_1_by_par_left",
        typ_id="519",
        inputs={"yi1": 7.0, "yi2": 9.0},
        params={"sw": 0.0},
        outputs={"yo": 7.0},
    ),
    FunctionalContract(
        label="switch_sig_2_1_by_par_right",
        typ_id="519",
        inputs={"yi1": 7.0, "yi2": 9.0},
        params={"sw": 2.0},
        outputs={"yo": 9.0},
    ),
    FunctionalContract(
        label="switch_sig_2_1_by_par_bool_zero",
        typ_id="518",
        inputs={"yi1": 7.0, "yi2": 9.0},
        params={"sw": 0.0},
        outputs={"yo": 0.0},
    ),
    FunctionalContract(
        label="switch_sig_2_1_by_par_bool_first",
        typ_id="518",
        inputs={"yi1": 7.0, "yi2": 9.0},
        params={"sw": 1.0},
        outputs={"yo": 7.0},
    ),
    FunctionalContract(
        label="switch_sig_2_1_by_par_bool_second",
        typ_id="518",
        inputs={"yi1": 7.0, "yi2": 9.0},
        params={"sw": 2.0},
        outputs={"yo": 9.0},
    ),
    FunctionalContract(
        label="switch_sig_2_1_by_sig_fixed_left",
        typ_id="521",
        inputs={"yi1": 7.0, "yi2": 9.0, "sw": 0.0},
        params={},
        outputs={"yo": 7.0},
    ),
    FunctionalContract(
        label="switch_sig_2_1_by_sig_fixed_right",
        typ_id="521",
        inputs={"yi1": 7.0, "yi2": 9.0, "sw": 1.0},
        params={},
        outputs={"yo": 9.0},
    ),
    FunctionalContract(
        label="switch_sig_3_1_first",
        typ_id="523",
        inputs={"yi1": 1.0, "yi2": 2.0, "yi3": 3.0, "sw": 0.0},
        params={},
        outputs={"yo": 1.0},
    ),
    FunctionalContract(
        label="switch_sig_3_1_second",
        typ_id="523",
        inputs={"yi1": 1.0, "yi2": 2.0, "yi3": 3.0, "sw": 1.0},
        params={},
        outputs={"yo": 2.0},
    ),
    FunctionalContract(
        label="switch_sig_3_1_third",
        typ_id="523",
        inputs={"yi1": 1.0, "yi2": 2.0, "yi3": 3.0, "sw": 2.0},
        params={},
        outputs={"yo": 3.0},
    ),
    FunctionalContract(
        label="switch_sig_4_1_fourth",
        typ_id="524",
        inputs={"yi1": 1.0, "yi2": 2.0, "yi3": 3.0, "yi4": 4.0, "sw": 3.0},
        params={},
        outputs={"yo": 4.0},
    ),
    FunctionalContract(
        label="switch_sw_equal_c_2s_1s",
        typ_id="525",
        inputs={"yi1": 7.0, "sw": 3.0, "yi2": 9.0},
        params={"C": 3.0},
        outputs={"yo": 7.0},
    ),
    FunctionalContract(
        label="switch_sw_greater_than_c_2s_1s",
        typ_id="526",
        inputs={"yi1": 7.0, "sw": 4.0, "yi2": 9.0},
        params={"C": 3.0},
        outputs={"yo": 7.0},
    ),
    FunctionalContract(
        label="switch_sw_greater_or_equal_c_2s_1s",
        typ_id="527",
        inputs={"yi1": 7.0, "sw": 3.0, "yi2": 9.0},
        params={"C": 3.0},
        outputs={"yo": 7.0},
    ),
    FunctionalContract(
        label="switch_sw_not_equal_c_2s_1s",
        typ_id="528",
        inputs={"yi1": 7.0, "sw": 4.0, "yi2": 9.0},
        params={"C": 3.0},
        outputs={"yo": 7.0},
    ),
    FunctionalContract(
        label="switch_sw_smaller_than_c_2s_1s",
        typ_id="529",
        inputs={"yi1": 7.0, "sw": 2.0, "yi2": 9.0},
        params={"C": 3.0},
        outputs={"yo": 7.0},
    ),
    FunctionalContract(
        label="switch_sw_smaller_or_equal_c_2s_1s",
        typ_id="530",
        inputs={"yi1": 7.0, "sw": 3.0, "yi2": 9.0},
        params={"C": 3.0},
        outputs={"yo": 7.0},
    ),
    FunctionalContract(
        label="limit_lower_parameter",
        typ_id="323",
        inputs={"yi": -3.0},
        params={"y_min": -2.0},
        outputs={"yo": -2.0},
    ),
    FunctionalContract(
        label="limit_upper_parameter",
        typ_id="324",
        inputs={"yi": 3.0},
        params={"y_max": 2.0},
        outputs={"yo": 2.0},
    ),
    FunctionalContract(
        label="deadband_continuous_inside",
        typ_id="96",
        inputs={"yi": 0.25},
        params={"db": 1.0},
        outputs={"yo": 0.0},
    ),
    FunctionalContract(
        label="deadband_continuous_positive_outside",
        typ_id="96",
        inputs={"yi": 2.0},
        params={"db": 1.0},
        outputs={"yo": 1.0},
    ),
    FunctionalContract(
        label="deadband_bypass_disabled",
        typ_id="90",
        inputs={"yi": 2.0},
        params={"db": 0.0},
        outputs={"yo": 2.0},
    ),
    FunctionalContract(
        label="deadband_bypass_enabled_positive",
        typ_id="90",
        inputs={"yi": 2.0},
        params={"db": 1.0},
        outputs={"yo": 1.0},
    ),
    FunctionalContract(
        label="deadband_discontinuous_inside",
        typ_id="91",
        inputs={"yi": 0.25},
        params={"db": 1.0},
        outputs={"yo": 0.0},
    ),
    FunctionalContract(
        label="deadband_discontinuous_outside",
        typ_id="91",
        inputs={"yi": -2.0},
        params={"db": 1.0},
        outputs={"yo": -2.0},
    ),
    FunctionalContract(
        label="deadband_limited_upper_clip",
        typ_id="89",
        inputs={"yi": 5.0},
        params={"db": 1.0, "y_min": -2.0, "y_max": 2.0},
        outputs={"yo": 2.0},
    ),
    FunctionalContract(
        label="pi_tunable_kc_direct_tp_rst_hold_inactive",
        typ_id="450",
        inputs={"yi": 2.0, "hold": 0.0, "rst": 0.0},
        params={"K_p": 1.0, "T_p": 2.0, "theta_p": 1.0, "ControlTuning": 1.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 3.2222222222222223},
        states={"x": 1.0},
        internals={"tau_c": 0.8, "Kc": 1.1111111111111112, "Ti": 2.0, "x_init": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="pi_tunable_kc_from_rise_time_rst_hold_inactive",
        typ_id="451",
        inputs={"yi": 2.0, "hold": 0.0, "rst": 0.0},
        params={"K_p": 1.0, "T_rise": 4.394, "theta_p": 1.0, "ControlTuning": 1.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 3.2222222222222223},
        states={"x": 1.0},
        internals={"T_p": 2.0, "tau_c": 0.8, "Kc": 1.1111111111111112, "Ti": 2.0, "x_init": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="pi_parallel_kp_1_over_sti_with_limits_rst_hold_inactive",
        typ_id="455",
        inputs={"yi": 2.0, "hold": 0.0, "rst": 0.0},
        params={"Kp": 3.0, "Ti": 2.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 7.0},
        states={"x": 1.0},
        internals={"x_init": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="pi_parallel_with_param_limits_rst_hold_inactive",
        typ_id="458",
        inputs={"yi": 2.0, "hold": 0.0, "rst": 0.0},
        params={"Kp": 3.0, "Ki": 4.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        internals={"x_init": 5.0},
        state_derivatives={"x": 8.0},
    ),
    FunctionalContract(
        label="pi_parallel_with_signal_limits_rst_hold_inactive",
        typ_id="460",
        inputs={"yi": 2.0, "hold": 0.0, "ymax": 100.0, "ymin": -100.0, "rst": 0.0},
        params={"Kp": 3.0, "Ki": 4.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        internals={"x_init": 5.0},
        state_derivatives={"x": 8.0},
    ),
    FunctionalContract(
        label="pi_tunable_kc_direct_tp_rst_sig_hold_inactive",
        typ_id="463",
        inputs={"yi": 2.0, "hold": 0.0, "x_rst": 1.0, "rst": 0.0},
        params={"K_p": 1.0, "T_p": 2.0, "theta_p": 1.0, "ControlTuning": 1.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 3.2222222222222223},
        states={"x": 1.0},
        internals={"tau_c": 0.8, "Kc": 1.1111111111111112, "Ti": 2.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="pi_tunable_kc_from_rise_time_rst_sig_hold_inactive",
        typ_id="464",
        inputs={"yi": 2.0, "hold": 0.0, "x_rst": 1.0, "rst": 0.0},
        params={"K_p": 1.0, "T_rise": 4.394, "theta_p": 1.0, "ControlTuning": 1.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 3.2222222222222223},
        states={"x": 1.0},
        internals={"T_p": 2.0, "tau_c": 0.8, "Kc": 1.1111111111111112, "Ti": 2.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="pi_parallel_param_limits_rst_sig_hold_inactive",
        typ_id="470",
        inputs={"yi": 2.0, "hold": 0.0, "x_rst": 5.0, "rst": 0.0},
        params={"Kp": 3.0, "Ki": 4.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        state_derivatives={"x": 8.0},
    ),
    FunctionalContract(
        label="pi_series_tracking_signal_base",
        typ_id="444",
        inputs={"yi": 2.0, "yo_lim": 11.0},
        params={"Kp": 3.0, "Ki": 4.0, "Tt": 1.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        state_derivatives={"x": 8.0},
    ),
    FunctionalContract(
        label="pi_parallel_with_alt_param_limits",
        typ_id="446",
        inputs={"yi": 2.0},
        params={"Kp": 3.0, "Ki": 4.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        state_derivatives={"x": 8.0},
    ),
    FunctionalContract(
        label="pi_parallel_kp_1_over_sti_alt_limits_rst_sig_hold_inactive",
        typ_id="467",
        inputs={"yi": 2.0, "hold": 0.0, "x_rst": 1.0, "rst": 0.0},
        params={"Kp": 3.0, "Ti": 2.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 7.0},
        states={"x": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="pi_series_tracking_rst_variant_alt",
        typ_id="452",
        inputs={"yi": 2.0, "rst": 0.0},
        params={"Kp": 3.0, "Ti": 2.0, "Kaw": 1.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 7.0},
        states={"x": 1.0},
        internals={"PIsum": 7.0, "x_init": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="pi_series_tracking_rst_hold_inactive_alt",
        typ_id="453",
        inputs={"yi": 2.0, "hold": 0.0, "yo_lim": 7.0, "rst": 0.0},
        params={"Kp": 3.0, "Ti": 2.0, "Tt": 1.0},
        outputs={"yo": 7.0},
        states={"x": 1.0},
        state_derivatives={"x": 3.0},
        internals={"x_init": 1.0},
    ),
    FunctionalContract(
        label="pi_parallel_with_alt_param_limits_rst_hold_inactive",
        typ_id="459",
        inputs={"yi": 2.0, "hold": 0.0, "rst": 0.0},
        params={"Kp": 3.0, "Ki": 4.0, "ymin": -100.0, "ymax": 100.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        internals={"x_init": 5.0},
        state_derivatives={"x": 8.0},
    ),
    FunctionalContract(
        label="pi_series_tracking_rst_sig_hold_inactive_alt",
        typ_id="465",
        inputs={"yi": 2.0, "hold": 0.0, "x_rst": 1.0, "yo_lim": 7.0, "rst": 0.0},
        params={"Kp": 3.0, "Ti": 2.0, "Tt": 1.0},
        outputs={"yo": 7.0},
        states={"x": 1.0},
        state_derivatives={"x": 3.0},
    ),
    FunctionalContract(
        label="pi_series_rst_sig_hold_inactive_plain",
        typ_id="466",
        inputs={"yi": 2.0, "hold": 0.0, "x_rst": 1.0, "rst": 0.0},
        params={"Kp": 3.0, "Ti": 2.0},
        outputs={"yo": 7.0},
        states={"x": 1.0},
        state_derivatives={"x": 3.0},
    ),
    FunctionalContract(
        label="pi_parallel_signal_tracking_rst_sig_hold_inactive",
        typ_id="469",
        inputs={"yi": 2.0, "hold": 0.0, "x_rst": 5.0, "yo_lim": 11.0, "rst": 0.0},
        params={"Kp": 3.0, "Ki": 4.0, "Tt": 1.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        state_derivatives={"x": 8.0},
    ),
    FunctionalContract(
        label="pi_parallel_alt_param_limits_rst_sig_hold_inactive",
        typ_id="471",
        inputs={"yi": 2.0, "hold": 0.0, "x_rst": 5.0, "rst": 0.0},
        params={"Kp": 3.0, "Ki": 4.0, "ymin": -100.0, "ymax": 100.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        state_derivatives={"x": 8.0},
    ),
    FunctionalContract(
        label="pi_parallel_signal_limits_rst_sig_hold_inactive",
        typ_id="472",
        inputs={"yi": 2.0, "hold": 0.0, "x_rst": 5.0, "ymax": 100.0, "ymin": -100.0, "rst": 0.0},
        params={"Kp": 3.0, "Ki": 4.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        state_derivatives={"x": 8.0},
    ),
    FunctionalContract(
        label="pid_parallel_param_limits_rst_hold_inactive",
        typ_id="462",
        inputs={"yi": 2.0, "hold": 0.0, "rst": 0.0},
        params={"Kp": 3.0, "Ki": 4.0, "Kd": 5.0, "Td": 2.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 16.0},
        states={"x1": 5.0, "x2": 0.0},
        internals={"dx2": 1.0, "yk": 6.0, "yd": 5.0, "yis": 5.0, "x1_init": 5.0},
        state_derivatives={"x1": 8.0, "x2": 1.0},
    ),
    FunctionalContract(
        label="pi_series_tracking_signal_base",
        typ_id="444",
        inputs={"yi": 2.0, "yo_lim": 11.0},
        params={"Kp": 3.0, "Ki": 4.0, "Tt": 1.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        state_derivatives={"x": 8.0},
    ),
    FunctionalContract(
        label="pi_parallel_with_alt_param_limits",
        typ_id="446",
        inputs={"yi": 2.0},
        params={"Kp": 3.0, "Ki": 4.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        state_derivatives={"x": 8.0},
    ),
    FunctionalContract(
        label="pi_parallel_kp_1_over_sti_alt_limits_rst_sig_hold_inactive",
        typ_id="467",
        inputs={"yi": 2.0, "hold": 0.0, "x_rst": 1.0, "rst": 0.0},
        params={"Kp": 3.0, "Ti": 2.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 7.0},
        states={"x": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="pi_series_tracking_rst_variant_alt",
        typ_id="452",
        inputs={"yi": 2.0, "rst": 0.0},
        params={"Kp": 3.0, "Ti": 2.0, "Kaw": 1.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 7.0},
        states={"x": 1.0},
        internals={"PIsum": 7.0, "x_init": 1.0},
        state_derivatives={"x": 1.0},
    ),
    FunctionalContract(
        label="pi_series_tracking_rst_hold_inactive_alt",
        typ_id="453",
        inputs={"yi": 2.0, "hold": 0.0, "yo_lim": 7.0, "rst": 0.0},
        params={"Kp": 3.0, "Ti": 2.0, "Tt": 1.0},
        outputs={"yo": 7.0},
        states={"x": 1.0},
        state_derivatives={"x": 3.0},
        internals={"x_init": 1.0},
    ),
    FunctionalContract(
        label="pi_parallel_with_alt_param_limits_rst_hold_inactive",
        typ_id="459",
        inputs={"yi": 2.0, "hold": 0.0, "rst": 0.0},
        params={"Kp": 3.0, "Ki": 4.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        internals={"x_init": 5.0},
        state_derivatives={"x": 8.0},
    ),
    FunctionalContract(
        label="pi_series_tracking_rst_sig_hold_inactive_alt",
        typ_id="465",
        inputs={"yi": 2.0, "hold": 0.0, "x_rst": 1.0, "yo_lim": 7.0, "rst": 0.0},
        params={"Kp": 3.0, "Ti": 2.0, "Tt": 1.0},
        outputs={"yo": 7.0},
        states={"x": 1.0},
        state_derivatives={"x": 3.0},
    ),
    FunctionalContract(
        label="pi_series_rst_sig_hold_inactive_plain",
        typ_id="466",
        inputs={"yi": 2.0, "hold": 0.0, "x_rst": 1.0, "rst": 0.0},
        params={"Kp": 3.0, "Ti": 2.0},
        outputs={"yo": 7.0},
        states={"x": 1.0},
        state_derivatives={"x": 3.0},
    ),
    FunctionalContract(
        label="pi_parallel_signal_tracking_rst_sig_hold_inactive",
        typ_id="469",
        inputs={"yi": 2.0, "hold": 0.0, "x_rst": 5.0, "yo_lim": 11.0, "rst": 0.0},
        params={"Kp": 3.0, "Ki": 4.0, "Tt": 1.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        state_derivatives={"x": 8.0},
    ),
    FunctionalContract(
        label="pi_parallel_alt_param_limits_rst_sig_hold_inactive",
        typ_id="471",
        inputs={"yi": 2.0, "hold": 0.0, "x_rst": 5.0, "rst": 0.0},
        params={"Kp": 3.0, "Ki": 4.0, "y_min": -100.0, "y_max": 100.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        state_derivatives={"x": 8.0},
    ),
    FunctionalContract(
        label="pi_parallel_signal_limits_rst_sig_hold_inactive",
        typ_id="472",
        inputs={"yi": 2.0, "hold": 0.0, "x_rst": 5.0, "ymax": 100.0, "ymin": -100.0, "rst": 0.0},
        params={"Kp": 3.0, "Ki": 4.0},
        outputs={"yo": 11.0},
        states={"x": 5.0},
        state_derivatives={"x": 8.0},
    ),
    FunctionalContract(label="char_factorized_quadratic", typ_id="2", inputs={"yi": 5.0}, params={"a": 2.0, "c1": 1.0, "c2": 3.0}, outputs={"yo": 16.0}),
    FunctionalContract(label="char_general_quadratic", typ_id="3", inputs={"yi": 2.0}, params={"a": 2.0, "b": 3.0, "c": 4.0}, outputs={"yo": 18.0}),
    FunctionalContract(label="char_linear", typ_id="4", inputs={"yi": 2.0}, params={"m": 3.0, "n": 4.0}, outputs={"yo": 10.0}),
    FunctionalContract(label="const_negative_c", typ_id="49", inputs={}, params={"C": 3.0}, outputs={"yo": -3.0}),
    FunctionalContract(label="const_c", typ_id="55", inputs={}, params={"C": 3.0}, outputs={"yo": 3.0}),
    FunctionalContract(label="const_ratio_c1_c2", typ_id="56", inputs={}, params={"C1": 4.0, "C2": 2.0}, outputs={"yo": 2.0}, internals={"yo0": 2.0}),
    FunctionalContract(label="helper_lim", typ_id="75", inputs={"yi": 5.0, "y_min": -2.0, "y_max": 2.0}, params={}, outputs={"yo": 2.0}),
    FunctionalContract(label="helper_lim_const", typ_id="76", inputs={"yi": 5.0}, params={"y_min": -2.0, "y_max": 2.0}, outputs={"yo": 2.0}),
    FunctionalContract(label="mechanical_1_over_2hs", typ_id="401", inputs={"yi": 4.0}, params={"H": 2.0}, outputs={"yo": 3.0}, states={"x": 3.0}, state_derivatives={"x": 1.0}),
    FunctionalContract(label="convert_hz_to_pu", typ_id="552", inputs={"Freq": 50.0}, params={"freqbase": 25.0}, outputs={"fpu": 2.0}),
    FunctionalContract(label="convert_pu_to_hz", typ_id="557", inputs={"fpu": 2.0}, params={"freqbase": 25.0}, outputs={"Freq": 50.0}),
    FunctionalContract(label="convert_rad_s_to_rpm", typ_id="562", inputs={"omega": 2.0 * math.pi}, params={}, outputs={"n": 60.0}),
    FunctionalContract(label="convert_rpm_to_rad_s", typ_id="564", inputs={"n": 60.0}, params={}, outputs={"omega": 2.0 * math.pi}),
    FunctionalContract(label="convert_rpm_to_pu", typ_id="563", inputs={"n": 60.0}, params={"Zp": 2.0, "freqbase": 2.0}, outputs={"speed": 1.0}),
    FunctionalContract(label="convert_nm_to_pu", typ_id="553", inputs={"M": 1000.0 / (2.0 * math.pi)}, params={"freqbase": 1.0, "Zp": 1.0, "Pel_base": 1.0}, outputs={"m": 1.0}),
    FunctionalContract(label="const_sqrt_2_over_3", typ_id="60", inputs={}, params={}, outputs={"yo": math.sqrt(2.0 / 3.0)}, internals={"yo0": math.sqrt(2.0 / 3.0)}),
    FunctionalContract(label="const_sqrt_3_over_2", typ_id="61", inputs={}, params={}, outputs={"yo": math.sqrt(3.0 / 2.0)}, internals={"yo0": math.sqrt(3.0 / 2.0)}),
    FunctionalContract(label="const_sqrt_c1_over_c2", typ_id="62", inputs={}, params={"C1": 4.0, "C2": 1.0}, outputs={"yo": 2.0}, internals={"yo0": 2.0}),
    FunctionalContract(label="const_sqrt2", typ_id="63", inputs={}, params={}, outputs={"yo": math.sqrt(2.0)}, internals={"yo0": math.sqrt(2.0)}),
    FunctionalContract(label="const_sqrt3", typ_id="64", inputs={}, params={}, outputs={"yo": math.sqrt(3.0)}, internals={"yo0": math.sqrt(3.0)}),
    FunctionalContract(label="const_2pi_53", typ_id="53", inputs={}, params={}, outputs={"yo": 2.0 * math.pi}),
    FunctionalContract(label="const_pi_over_two", typ_id="59", inputs={}, params={}, outputs={"yo": math.pi / 2.0}),
    FunctionalContract(label="const_one_over_sqrt2_52", typ_id="52", inputs={}, params={}, outputs={"yo": 1.0 / math.sqrt(2.0)}),
    FunctionalContract(label="gain_one_over_sqrt2_176", typ_id="176", inputs={"yi": 2.0}, params={}, outputs={"yo": 2.0 / math.sqrt(2.0)}),
    FunctionalContract(label="gain_one_over_sqrt3_177", typ_id="177", inputs={"yi": math.sqrt(3.0)}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="gain_negative_one", typ_id="168", inputs={"yi": 2.0}, params={}, outputs={"yo": -2.0}),
    FunctionalContract(label="gain_negative_k", typ_id="169", inputs={"yi": 2.0}, params={"K": 3.0}, outputs={"yo": -6.0}),
    FunctionalContract(label="gain_one_minus_k", typ_id="170", inputs={"yi": 2.0}, params={"K": 0.25}, outputs={"yo": 1.5}),
    FunctionalContract(label="gain_one_minus_k1_minus_k2", typ_id="171", inputs={"yi": 2.0}, params={"K1": 0.25, "K2": 0.25}, outputs={"yo": 1.0}),
    FunctionalContract(label="gain_one_over_k_limited", typ_id="173", inputs={"yi": 8.0}, params={"K": 4.0, "y_min": -10.0, "y_max": 10.0}, outputs={"yo": 2.0}),
    FunctionalContract(label="gain_one_over_k1k2_limited", typ_id="175", inputs={"yi": 8.0}, params={"K1": 2.0, "K2": 2.0, "y_min": -10.0, "y_max": 10.0}, outputs={"yo": 2.0}),
    FunctionalContract(label="reciprocal", typ_id="369", inputs={"u": 4.0}, params={}, outputs={"yo": 0.25}),
    FunctionalContract(label="balanced_flag_emt", typ_id="66", inputs={}, params={}, outputs={"yo": 0.0}),
    FunctionalContract(label="rms_flag_emt", typ_id="80", inputs={}, params={}, outputs={"yo": 0.0}),
    FunctionalContract(label="select_true_branch", typ_id="83", inputs={"condition": 1.0, "y_true": 7.0, "y_false": 9.0}, params={}, outputs={"yo": 7.0}),
    FunctionalContract(label="select_false_branch", typ_id="83", inputs={"condition": 0.0, "y_true": 7.0, "y_false": 9.0}, params={}, outputs={"yo": 9.0}),
    FunctionalContract(label="select_const_true_branch", typ_id="84", inputs={"condition": 1.0}, params={"K_true": 7.0, "K_false": 9.0}, outputs={"yo": 7.0}),
    FunctionalContract(label="select_const_false_branch", typ_id="84", inputs={"condition": 0.0}, params={"K_true": 7.0, "K_false": 9.0}, outputs={"yo": 9.0}),
    FunctionalContract(label="const_2pi_411", typ_id="411", inputs={}, params={}, outputs={"yo": 2.0 * math.pi}),
    FunctionalContract(label="const_c_412", typ_id="412", inputs={}, params={"C": 3.0}, outputs={"yo": 3.0}),
    FunctionalContract(label="const_2pi_417", typ_id="417", inputs={}, params={}, outputs={"yo": 2.0 * math.pi}),
    FunctionalContract(label="const_c_418", typ_id="418", inputs={}, params={"C": 3.0}, outputs={"yo": 3.0}),
    FunctionalContract(label="const_2pi_423", typ_id="423", inputs={}, params={}, outputs={"yo": 2.0 * math.pi}),
    FunctionalContract(label="const_c_424", typ_id="424", inputs={}, params={"C": 3.0}, outputs={"yo": 3.0}),
    FunctionalContract(label="const_2pi_429", typ_id="429", inputs={}, params={}, outputs={"yo": 2.0 * math.pi}),
    FunctionalContract(label="const_c_430", typ_id="430", inputs={}, params={"C": 3.0}, outputs={"yo": 3.0}),
    FunctionalContract(label="accelerating_power_simple", typ_id="402", inputs={"speed": 1.0, "xmt": 3.0, "xme": 2.0}, params={}, outputs={"yo": 2.0 * math.pi}),
    FunctionalContract(label="accelerating_power_ipb_passthrough", typ_id="403", inputs={"cosn": 0.5, "speed": 1.0, "xmt": 3.0, "xme": 2.0}, params={"IPB": 1.0}, outputs={"Pa": 0.5}),
    FunctionalContract(label="gear_box_speed_to_omega", typ_id="404", inputs={"speed": 1.0}, params={"Nratio": 2.0, "RPM_syn": 60.0}, outputs={"omega": math.pi}),
    FunctionalContract(label="mass_j_torque_balance", typ_id="405", inputs={"M1": 3.0, "M2": 1.0}, params={"J": 2.0}, outputs={"omega": 1.0}, states={"xomega": 1.0}, state_derivatives={"xomega": 1.0}),
    FunctionalContract(label="power_over_omega_to_torque", typ_id="406", inputs={"Power": 1.0, "omega": 2.0}, params={}, outputs={"Torque": 500.0}),
    FunctionalContract(label="pt_pturb_no_conversion_when_pn_zero", typ_id="407", inputs={"pturb": 2.0, "sgnn": 10.0, "cosn": 0.8}, params={"PN": 0.0}, outputs={"pt": 2.0}),
    FunctionalContract(label="el_power_ipb_zero", typ_id="114", inputs={"pgt": 2.0, "cosn": 0.5}, params={"IPB": 0.0}, outputs={"pelec": 2.0}),
    FunctionalContract(label="pq_calculator", typ_id="115", inputs={"ur": 2.0, "ui": 1.0, "ir": 3.0, "ii": 4.0}, params={}, outputs={"P": 10.0, "Q": -5.0}),
    FunctionalContract(label="power_base_with_conversion", typ_id="116", inputs={"pg": 2.0, "sgnn": 10.0, "cosn": 0.8}, params={"PN": 20.0}, outputs={"pelec": 0.8}),
    FunctionalContract(label="pq_calculator", typ_id="115", inputs={"ur": 2.0, "ui": 1.0, "ir": 3.0, "ii": 4.0}, params={}, outputs={"P": 10.0, "Q": -5.0}),
    FunctionalContract(label="power_base_with_conversion", typ_id="116", inputs={"pg": 2.0, "sgnn": 10.0, "cosn": 0.8}, params={"PN": 20.0}, outputs={"pelec": 0.8}),
    FunctionalContract(label="flipflop_set", typ_id="68", inputs={"set": 1.0, "rst": 0.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="aflipflop_set_holds_input", typ_id="65", inputs={"yi": 3.0, "set": 1.0, "rst": 0.0}, params={}, outputs={"yo": 3.0}),
    FunctionalContract(label="bistable_prioritized_set", typ_id="351", inputs={"S": 1.0, "R": 1.0}, params={"PRIO_SET": 1.0}, outputs={"Q": 1.0, "not_Q": 0.0}),
    FunctionalContract(label="invert_logic_ip_true", typ_id="347", inputs={"yi": 0.0}, params={"Tpick": 0.0, "Tdrop": 0.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="complex_add", typ_id="375", inputs={"re1": 1.0, "im1": 2.0, "re2": 3.0, "im2": 4.0}, params={}, outputs={"re": 4.0, "im": 6.0}),
    FunctionalContract(label="complex_conjugate", typ_id="376", inputs={"re1": 1.0, "im1": 2.0}, params={}, outputs={"re": 1.0, "im": -2.0}),
    FunctionalContract(label="complex_division", typ_id="377", inputs={"re1": 1.0, "im1": 1.0, "re2": 1.0, "im2": -1.0}, params={}, outputs={"re": 0.0, "im": 1.0}, internals={"var1": 2.0}),
    FunctionalContract(label="complex_magnitude", typ_id="378", inputs={"re": 3.0, "im": 4.0}, params={}, outputs={"mag": 5.0}),
    FunctionalContract(label="complex_multiplication", typ_id="379", inputs={"re1": 1.0, "im1": 1.0, "re2": 1.0, "im2": -1.0}, params={}, outputs={"re": 2.0, "im": 0.0}),
    FunctionalContract(label="complex_subtraction", typ_id="380", inputs={"re1": 5.0, "im1": 4.0, "re2": 2.0, "im2": 1.0}, params={}, outputs={"re": 3.0, "im": 3.0}),
    FunctionalContract(label="complex_to_polar", typ_id="381", inputs={"re": 0.0, "im": 1.0}, params={}, outputs={"mag": 1.0, "phi": math.pi / 2.0}),
    FunctionalContract(label="complex_to_rectangular", typ_id="382", inputs={"mag": 1.0, "phi": math.pi / 2.0}, params={}, outputs={"re": 0.0, "im": 1.0}),
    FunctionalContract(label="lookup_array_1x3_linear_fixed", typ_id="10", inputs={"yi": 0.5}, params={"arr_x1": 0.0, "arr_x2": 1.0, "arr_x3": 2.0, "arr_y1": 0.0, "arr_y2": 10.0, "arr_y3": 20.0, "vClip": 1.0}, outputs={"yo": 5.0}),
    FunctionalContract(label="lookup_array_1x3_linear_variable", typ_id="11", inputs={"yi": 0.5, "arr_x1": 0.0, "arr_x2": 1.0, "arr_x3": 2.0, "arr_y1": 0.0, "arr_y2": 10.0, "arr_y3": 20.0}, params={"vClip": 1.0}, outputs={"yo": 5.0}),
    FunctionalContract(label="lookup_array_1x4_linear_fixed", typ_id="12", inputs={"yi": 2.5}, params={"arr_x1": 0.0, "arr_x2": 1.0, "arr_x3": 2.0, "arr_x4": 3.0, "arr_y1": 0.0, "arr_y2": 10.0, "arr_y3": 20.0, "arr_y4": 30.0, "vClip": 1.0}, outputs={"yo": 25.0}),
    FunctionalContract(label="lookup_array_1x4_linear_variable", typ_id="13", inputs={"yi": 2.5, "arr_x1": 0.0, "arr_x2": 1.0, "arr_x3": 2.0, "arr_x4": 3.0, "arr_y1": 0.0, "arr_y2": 10.0, "arr_y3": 20.0, "arr_y4": 30.0}, params={"vClip": 1.0}, outputs={"yo": 25.0}),
    FunctionalContract(label="lookup_array_linear_default", typ_id="7", inputs={"yi": 0.5}, params={"arr_x1": 0.0, "arr_x2": 1.0, "arr_x3": 2.0, "arr_y1": 0.0, "arr_y2": 10.0, "arr_y3": 20.0}, outputs={"yo": 5.0}),
    FunctionalContract(label="lookup_array_linear_noclipping_default", typ_id="8", inputs={"yi": 2.5}, params={"arr_x1": 0.0, "arr_x2": 1.0, "arr_x3": 2.0, "arr_y1": 0.0, "arr_y2": 10.0, "arr_y3": 20.0}, outputs={"yo": 25.0}),
    FunctionalContract(label="inverse_lookup_array_linear_default", typ_id="5", inputs={"yi": 5.0}, params={"arr_x1": 0.0, "arr_x2": 1.0, "arr_x3": 2.0, "arr_y1": 0.0, "arr_y2": 10.0, "arr_y3": 20.0}, outputs={"yo": 0.5}),
    FunctionalContract(label="inverse_lookup_array_object_linear_default", typ_id="6", inputs={"yi": 5.0}, params={"arr_x1": 0.0, "arr_x2": 1.0, "arr_x3": 2.0, "arr_y1": 0.0, "arr_y2": 10.0, "arr_y3": 20.0}, outputs={"yo": 0.5}),
    FunctionalContract(label="lookup_array_object_linear_default", typ_id="14", inputs={"yi": 0.5}, params={"arr_x1": 0.0, "arr_x2": 1.0, "arr_x3": 2.0, "arr_y1": 0.0, "arr_y2": 10.0, "arr_y3": 20.0}, outputs={"yo": 5.0}),
    FunctionalContract(label="lookup_array_object_linear_noclipping_default", typ_id="15", inputs={"yi": 2.5}, params={"arr_x1": 0.0, "arr_x2": 1.0, "arr_x3": 2.0, "arr_y1": 0.0, "arr_y2": 10.0, "arr_y3": 20.0}, outputs={"yo": 25.0}),
    FunctionalContract(label="lookup_array_spline_default", typ_id="9", inputs={"yi": 0.5}, params={"arr_x1": 0.0, "arr_x2": 1.0, "arr_x3": 2.0, "arr_y1": 0.0, "arr_y2": 10.0, "arr_y3": 20.0}, outputs={"yo": 5.0}),
    FunctionalContract(label="lookup_array_object_spline_default", typ_id="16", inputs={"yi": 0.5}, params={"arr_x1": 0.0, "arr_x2": 1.0, "arr_x3": 2.0, "arr_y1": 0.0, "arr_y2": 10.0, "arr_y3": 20.0}, outputs={"yo": 5.0}),
    FunctionalContract(label="lookup_matrix_linear_default", typ_id="17", inputs={"yi1": 0.5, "yi2": 1.0}, params={"arr_x1": 0.0, "arr_x2": 1.0, "arr_y1": 0.0, "arr_y2": 2.0, "arr_z1_1": 0.0, "arr_z1_2": 10.0, "arr_z2_1": 20.0, "arr_z2_2": 30.0}, outputs={"yo": 15.0}),
    FunctionalContract(label="lookup_matrix_spline_default", typ_id="18", inputs={"yi1": 0.5, "yi2": 1.0}, params={"arr_x1": 0.0, "arr_x2": 1.0, "arr_y1": 0.0, "arr_y2": 2.0, "arr_z1_1": 0.0, "arr_z1_2": 10.0, "arr_z2_1": 20.0, "arr_z2_2": 30.0}, outputs={"yo": 15.0}),
    FunctionalContract(label="lookup_matrix_object_linear_default", typ_id="19", inputs={"yi1": 0.5, "yi2": 1.0}, params={"arr_x1": 0.0, "arr_x2": 1.0, "arr_y1": 0.0, "arr_y2": 2.0, "arr_z1_1": 0.0, "arr_z1_2": 10.0, "arr_z2_1": 20.0, "arr_z2_2": 30.0}, outputs={"yo": 15.0}),
    FunctionalContract(label="lookup_matrix_object_spline_default", typ_id="20", inputs={"yi1": 0.5, "yi2": 1.0}, params={"arr_x1": 0.0, "arr_x2": 1.0, "arr_y1": 0.0, "arr_y2": 2.0, "arr_z1_1": 0.0, "arr_z1_2": 10.0, "arr_z2_1": 20.0, "arr_z2_2": 30.0}, outputs={"yo": 15.0}),
    FunctionalContract(label="ip_two_out_of_three_true", typ_id="344", inputs={"yi1": 1.0, "yi2": 1.0, "yi3": 0.0}, params={"Tpick": 0.0, "Tdrop": 0.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="ip_and2_true", typ_id="345", inputs={"yi1": 1.0, "yi2": 1.0}, params={"Tpick": 0.0, "Tdrop": 0.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="ip_and3_true", typ_id="346", inputs={"yi1": 1.0, "yi2": 1.0, "yi3": 1.0}, params={"Tpick": 0.0, "Tdrop": 0.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="ip_not_true", typ_id="348", inputs={"yi1": 0.0}, params={"Tpick": 0.0, "Tdrop": 0.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="ip_or2_true", typ_id="349", inputs={"yi1": 0.0, "yi2": 1.0}, params={"Tpick": 0.0, "Tdrop": 0.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="ip_or3_true", typ_id="350", inputs={"yi1": 0.0, "yi2": 0.0, "yi3": 1.0}, params={"Tpick": 0.0, "Tdrop": 0.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="ip_abs_gt_true", typ_id="33", inputs={"yi": 2.0}, params={"C": 1.0, "Tpick": 0.0, "Tdrop": 0.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="ip_abs_lt_true", typ_id="34", inputs={"yi": 0.5}, params={"C": 1.0, "Tpick": 0.0, "Tdrop": 0.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="ip_eq_c_true", typ_id="35", inputs={"yi": 1.0}, params={"C": 1.0, "Tpick": 0.0, "Tdrop": 0.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="ip_gt_c_true", typ_id="36", inputs={"yi": 2.0}, params={"C": 1.0, "Tpick": 0.0, "Tdrop": 0.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="ip_ge_c_true", typ_id="37", inputs={"yi": 1.0}, params={"C": 1.0, "Tpick": 0.0, "Tdrop": 0.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="ip_lt_c_true", typ_id="38", inputs={"yi": 0.5}, params={"C": 1.0, "Tpick": 0.0, "Tdrop": 0.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="ip_le_c_true", typ_id="39", inputs={"yi": 1.0}, params={"C": 1.0, "Tpick": 0.0, "Tdrop": 0.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="ip_eq_sig_true", typ_id="40", inputs={"yi1": 2.0, "yi2": 2.0}, params={"Tpick": 0.0, "Tdrop": 0.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="ip_ge_sig_true", typ_id="41", inputs={"yi1": 2.0, "yi2": 2.0}, params={"Tpick": 0.0, "Tdrop": 0.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="ip_gt_sig_true", typ_id="42", inputs={"yi1": 3.0, "yi2": 2.0}, params={"Tpick": 0.0, "Tdrop": 0.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="ip_le_sig_true", typ_id="43", inputs={"yi1": 1.0, "yi2": 1.0}, params={"Tpick": 0.0, "Tdrop": 0.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="ip_lt_sig_true", typ_id="44", inputs={"yi1": 1.0, "yi2": 2.0}, params={"Tpick": 0.0, "Tdrop": 0.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="enable_2_sig_on", typ_id="494", inputs={"yi1": 4.0, "yi2": 5.0, "Enable": 1.0}, params={"yi1_default": 9.0, "yi2_default": 8.0}, outputs={"yo1": 4.0, "yo2": 5.0}),
    FunctionalContract(label="enable_2_sig_hold_on", typ_id="493", inputs={"yi1": 4.0, "yi2": 5.0, "Enable": 1.0}, params={}, outputs={"yo1": 4.0, "yo2": 5.0}),
    FunctionalContract(label="enable_1_sig_on", typ_id="492", inputs={"yi": 4.0, "Enable": 1.0}, params={"yi_default": 9.0}, outputs={"yo": 4.0}),
    FunctionalContract(label="enable_1_sig_hold_on", typ_id="491", inputs={"yi": 4.0, "Enable": 1.0}, params={}, outputs={"yo": 4.0}),
    FunctionalContract(label="enable_1_sig_on", typ_id="492", inputs={"yi": 4.0, "Enable": 1.0}, params={"yi_default": 9.0}, outputs={"yo": 4.0}),
    FunctionalContract(label="enable_1_sig_hold_on", typ_id="491", inputs={"yi": 4.0, "Enable": 1.0}, params={}, outputs={"yo": 4.0}),
    FunctionalContract(label="enable_3_sig_on", typ_id="496", inputs={"yi1": 4.0, "yi2": 5.0, "yi3": 6.0, "Enable": 1.0}, params={"yi1_default": 9.0, "yi2_default": 8.0, "yi3_default": 7.0}, outputs={"yo1": 4.0, "yo2": 5.0, "yo3": 6.0}),
    FunctionalContract(label="enable_3_sig_hold_on", typ_id="495", inputs={"yi1": 4.0, "yi2": 5.0, "yi3": 6.0, "Enable": 1.0}, params={}, outputs={"yo1": 4.0, "yo2": 5.0, "yo3": 6.0}),
    FunctionalContract(label="enable_4_sig_on", typ_id="498", inputs={"yi1": 4.0, "yi2": 5.0, "yi3": 6.0, "yi4": 7.0, "Enable": 1.0}, params={"yi1_default": 9.0, "yi2_default": 8.0, "yi3_default": 7.0, "yi4_default": 6.0}, outputs={"yo1": 4.0, "yo2": 5.0, "yo3": 6.0, "yo4": 7.0}),
    FunctionalContract(label="enable_4_sig_hold_on", typ_id="497", inputs={"yi1": 4.0, "yi2": 5.0, "yi3": 6.0, "yi4": 7.0, "Enable": 1.0}, params={}, outputs={"yo1": 4.0, "yo2": 5.0, "yo3": 6.0, "yo4": 7.0}),
    FunctionalContract(label="enable_5_sig_on", typ_id="500", inputs={"yi1": 4.0, "yi2": 5.0, "yi3": 6.0, "yi4": 7.0, "yi5": 8.0, "Enable": 1.0}, params={"yi1_default": 9.0, "yi2_default": 8.0, "yi3_default": 7.0, "yi4_default": 6.0, "yi5_default": 5.0}, outputs={"yo1": 4.0, "yo2": 5.0, "yo3": 6.0, "yo4": 7.0, "yo5": 8.0}),
    FunctionalContract(label="enable_5_sig_hold_on", typ_id="499", inputs={"yi1": 4.0, "yi2": 5.0, "yi3": 6.0, "yi4": 7.0, "yi5": 8.0, "Enable": 1.0}, params={}, outputs={"yo1": 4.0, "yo2": 5.0, "yo3": 6.0, "yo4": 7.0, "yo5": 8.0}),
    FunctionalContract(label="switch_par_1_2_by_sig_right", typ_id="509", inputs={"sw": 1.0}, params={"K": 7.0}, outputs={"yo1": 0.0, "yo2": 7.0}),
    FunctionalContract(label="switch_sig_1_2_by_par_bool_second", typ_id="514", inputs={"yi": 5.0}, params={"sw": 2.0}, outputs={"yo1": 0.0, "yo2": 5.0}),
    FunctionalContract(label="switch_sig_1_2_by_sig_right", typ_id="516", inputs={"yi": 5.0, "sw": 1.0}, params={}, outputs={"yo1": 0.0, "yo2": 5.0}),
    FunctionalContract(label="limit_symmetric_using_min_max", typ_id="315", inputs={"yi": 3.0}, params={"y_lim": 2.0}, outputs={"yo": 2.0}),
    FunctionalContract(label="limit_asymmetric_signals", typ_id="321", inputs={"yi": 5.0, "y_max": 2.0, "y_min": -2.0}, params={}, outputs={"yo": 2.0}),
    FunctionalContract(label="limit_signal_param_mix", typ_id="322", inputs={"yi": 5.0, "yi_max": 2.0, "yi_min": -2.0}, params={"y_max": 2.0, "y_min": -2.0}, outputs={"yo": 2.0}),
    FunctionalContract(label="limit_upper_eps_active_expected", typ_id="310", inputs={"yi": 3.0}, params={"eps": 0.1, "y_max": 2.0}, outputs={"yo": 2.0}),
    FunctionalContract(label="limit_lower_eps_active_expected", typ_id="311", inputs={"yi": -3.0}, params={"eps": 0.1, "y_min": -2.0}, outputs={"yo": -2.0}),
    FunctionalContract(label="limit_symmetric_using_min_max", typ_id="315", inputs={"yi": 3.0}, params={"y_lim": 2.0}, outputs={"yo": 2.0}),
    FunctionalContract(label="limit_asymmetric_signals", typ_id="321", inputs={"yi": 5.0, "y_max": 2.0, "y_min": -2.0}, params={}, outputs={"yo": 2.0}),
    FunctionalContract(label="limit_signal_param_mix", typ_id="322", inputs={"yi": 5.0, "yi_max": 2.0, "yi_min": -2.0}, params={"y_max": 2.0, "y_min": -2.0}, outputs={"yo": 2.0}),
    FunctionalContract(label="convert_abs_to_pu_sig", typ_id="555", inputs={"yi": 230.0, "base": 115.0}, params={}, outputs={"yo": 2.0}),
    FunctionalContract(label="convert_pu_to_abs_sig", typ_id="559", inputs={"yi": 2.0, "base": 115.0}, params={}, outputs={"yo": 230.0}),
    FunctionalContract(label="convert_pu_to_rpm", typ_id="560", inputs={"speed": 1.0}, params={"Zp": 2.0, "freqbase": 2.0}, outputs={"n": 60.0}),
    FunctionalContract(label="enable_1_sig_on", typ_id="492", inputs={"yi": 4.0, "Enable": 1.0}, params={"yi_default": 9.0}, outputs={"yo": 4.0}),
    FunctionalContract(label="enable_1_sig_hold_on", typ_id="491", inputs={"yi": 4.0, "Enable": 1.0}, params={}, outputs={"yo": 4.0}),
    FunctionalContract(label="limit_symmetric_using_min_max", typ_id="315", inputs={"yi": 3.0}, params={"y_lim": 2.0}, outputs={"yo": 2.0}),
    FunctionalContract(label="limit_asymmetric_signals", typ_id="321", inputs={"yi": 5.0, "y_max": 2.0, "y_min": -2.0}, params={}, outputs={"yo": 2.0}),
    FunctionalContract(label="limit_signal_param_mix", typ_id="322", inputs={"yi": 5.0, "yi_max": 2.0, "yi_min": -2.0}, params={"y_max": 2.0, "y_min": -2.0}, outputs={"yo": 2.0}),
    FunctionalContract(label="deadband_offset_bypass_active", typ_id="93", inputs={"yi": 2.0}, params={"db": 1.0}, outputs={"yo": 1.0}),
    FunctionalContract(label="deadband_stepped_bypass_active", typ_id="95", inputs={"yi": 2.0}, params={"db": 1.0}, outputs={"yo": 2.0}),
    FunctionalContract(label="backlash_equilibrium", typ_id="88", inputs={"yi": 1.0}, params={"db": 1.0}, outputs={"yo": 1.0}, states={"x": 1.0}, internals={"d": 0.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="reciprocal_fb_positive", typ_id="368", inputs={"u": 4.0}, params={}, outputs={"yo": 0.25}),
    FunctionalContract(label="selfix_true_branch", typ_id="85", inputs={"condition": 1.0, "y_true": 7.0, "y_false": 9.0}, params={}, outputs={"yo": 7.0}),
    FunctionalContract(label="selfix_false_branch", typ_id="85", inputs={"condition": 0.0, "y_true": 7.0, "y_false": 9.0}, params={}, outputs={"yo": 9.0}),
    FunctionalContract(label="selfix_const_true_branch", typ_id="86", inputs={"condition": 1.0}, params={"K_true": 7.0, "K_false": 9.0}, outputs={"yo": 7.0}),
    FunctionalContract(label="selfix_const_false_branch", typ_id="86", inputs={"condition": 0.0}, params={"K_true": 7.0, "K_false": 9.0}, outputs={"yo": 9.0}),
    FunctionalContract(label="atan2d_zero", typ_id="387", inputs={"re": 1.0, "im": 0.0}, params={}, outputs={"yo": 0.0}),
    FunctionalContract(label="atand_zero", typ_id="388", inputs={"yi": 0.0}, params={}, outputs={"yo": 0.0}),
    FunctionalContract(label="coshd_zero", typ_id="392", inputs={"yi": 0.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="sinhd_zero", typ_id="396", inputs={"yi": 0.0}, params={}, outputs={"yo": 0.0}),
    FunctionalContract(label="tanhd_zero", typ_id="400", inputs={"yi": 0.0}, params={}, outputs={"yo": 0.0}),
    FunctionalContract(label="higher_order_second_order_bypass_equilibrium", typ_id="190", inputs={"yi": 0.0}, params={"A1": 2.0, "A2": 3.0, "B1": 4.0, "B2": 5.0}, outputs={"yo": 0.0}, states={"x1": 0.0, "x2": 0.0}, internals={"dx1": 0.0, "dx2": 0.0, "triv": 0.0}, state_derivatives={"x1": 0.0, "x2": 0.0}),
    FunctionalContract(label="higher_order_second_order_plain_equilibrium", typ_id="192", inputs={"yi": 0.0}, params={"a1": 2.0, "a2": 3.0, "b1": 4.0, "b2": 5.0}, outputs={"yo": 0.0}, states={"x1": 0.0, "x2": 0.0}, internals={"dx1": 0.0, "dx2": 0.0}, state_derivatives={"x1": 0.0, "x2": 0.0}),
    FunctionalContract(label="higher_order_three_pole_bypass_equilibrium", typ_id="191", inputs={"yi": 0.0}, params={"Ta": 2.0, "Tb": 3.0, "Tc": 4.0, "K": 5.0}, outputs={"yo": 0.0}, states={"xa": 0.0, "xb": 0.0, "xc": 0.0}, internals={"yxa": 0.0, "yxb": 0.0, "dxc": 0.0}, state_derivatives={"xa": 0.0, "xb": 0.0, "xc": 0.0}),
    FunctionalContract(label="higher_order_t3_t1_t2_bypass_equilibrium", typ_id="193", inputs={"yi": 0.0}, params={"T1": 2.0, "T2": 3.0, "T3": 4.0}, outputs={"yo": 0.0}, states={"x1": 0.0, "x2": 0.0}, internals={"dx1": 0.0}, state_derivatives={"x1": 0.0, "x2": 0.0}),
    FunctionalContract(label="higher_order_t3_t4_t1_t2_equilibrium", typ_id="194", inputs={"yi": 0.0}, params={"T1": 2.0, "T2": 3.0, "T3": 4.0, "T4": 5.0}, outputs={"yo": 0.0}, states={"x1": 0.0, "x2": 0.0}, internals={"dx1": 0.0, "dx2": 0.0}, state_derivatives={"x1": 0.0, "x2": 0.0}),
    FunctionalContract(label="higher_order_ss_t3_bypass_equilibrium", typ_id="196", inputs={"yi": 0.0}, params={"T1": 2.0, "T2": 3.0, "T3": 4.0}, outputs={"yo": 0.0}, states={"x1": 0.0, "x2": 0.0}, internals={"dx2": 0.0}, state_derivatives={"x1": 0.0, "x2": 0.0}),
    FunctionalContract(label="higher_order_ss_ass_bs_1_bypass_equilibrium", typ_id="198", inputs={"yi": 0.0}, params={"A": 2.0, "B": 3.0}, outputs={"yo": 0.0}, states={"x1": 0.0, "x2": 0.0}, internals={"dx1": 0.0, "dx2": 0.0, "triv": 0.0}, state_derivatives={"x1": 0.0, "x2": 0.0}),
    FunctionalContract(label="higher_order_ss_plus_ww_bypass_equilibrium", typ_id="199", inputs={"yi": 0.0}, params={"B": 2.0, "w": 3.0}, outputs={"yo": 0.0}, states={"x1": 0.0, "x2": 0.0}, internals={"triv": 0.0, "dx1": 0.0, "dx2": 0.0}, state_derivatives={"x1": 0.0, "x2": 0.0}),
    FunctionalContract(label="high_pass_negative_bypass_active", typ_id="119", inputs={"yi": 4.0}, params={"T": 2.0}, outputs={"yo": -2.0}, states={"x": 2.0}, internals={"dx": 1.0}, state_derivatives={"x": 1.0}),
    FunctionalContract(label="high_pass_negative_plain", typ_id="120", inputs={"yi": 4.0}, params={"T": 2.0}, outputs={"yo": -2.0}, states={"x": 2.0}, internals={"dx": 1.0}, state_derivatives={"x": 1.0}),
    FunctionalContract(label="higher_order_lead_lag_bypass_equilibrium", typ_id="297", inputs={"yi": 2.0}, params={"Ta": 2.0, "Tb": 3.0}, outputs={"yo": 2.0}, states={"x": 2.0}, internals={"dx": 0.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="higher_order_one_minus_st_over_one_plus_st_half_bypass", typ_id="301", inputs={"yi": 2.0}, params={"T": 4.0}, outputs={"yo": 2.0}, states={"x": 2.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="higher_order_a_plus_sbt_over_one_plus_st_bypass", typ_id="303", inputs={"yi": 2.0}, params={"a": 3.0, "b": 5.0, "T": 2.0}, outputs={"yo": 6.0}, states={"x": 2.0}, internals={"dx": 0.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="higher_order_k_1plus_stb_over_1plus_sta", typ_id="304", inputs={"yi": 2.0}, params={"K": 3.0, "Tb": 4.0, "Ta": 2.0}, outputs={"yo": 6.0}, states={"x": 6.0}, internals={"dx": 0.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="higher_order_k_1plus_stld_over_1plus_stlg_fb", typ_id="305", inputs={"yi": 2.0}, params={"K": 3.0, "Tld": 4.0, "Tlg": 2.0}, outputs={"yo": 6.0}, states={"x": 6.0}, internals={"dx": 0.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="pi_limited_rate_zero_equilibrium", typ_id="434", inputs={"yi": 0.0}, params={"K": 2.0, "T": 2.0, "ylim": 100.0, "y_min": -100.0, "y_max": 100.0}, outputs={"yo": 0.0}, states={"x": 0.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="higher_order_1plusATs_over_1plusBTs_equilibrium", typ_id="293", inputs={"yi": 2.0}, params={"A": 2.0, "B": 3.0, "T": 4.0}, outputs={"yo": 2.0}, states={"x": 2.0}, internals={"dx": 0.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="higher_order_lead_lag_param_limits_equilibrium", typ_id="294", inputs={"yi": 0.0}, params={"Ta": 1.0, "Tb": 1.0, "y_min": -100.0, "y_max": 100.0}, outputs={"yo": 0.0}, states={"x": 0.0}, internals={"yox": 0.0, "dx": 0.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="higher_order_lead_lag_fb_limits_equilibrium", typ_id="295", inputs={"yi": 0.0}, params={"Ta": 1.0, "Tb": 1.0, "y_min": -100.0, "y_max": 100.0}, outputs={"yo": 0.0}, states={"x": 0.0}, internals={"yox": 0.0, "dx": 0.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="higher_order_lead_lag_k_dependent_limits_equilibrium", typ_id="296", inputs={"yi": 0.0}, params={"Ta": 1.0, "Tb": 1.0, "K": 1.0, "y_min": -100.0, "y_max": 100.0}, outputs={"yo": 0.0}, states={"x": 0.0}, internals={"yox": 0.0, "dx": 0.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="higher_order_1minusATs_over_1plusAT2_equilibrium", typ_id="300", inputs={"yi": 2.0}, params={"A": 2.0, "T": 4.0}, outputs={"yo": 2.0}, states={"x": 2.0}, internals={"Tz": 8.0, "dx": 0.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="higher_order_k_plus_sTb_over_1_plus_sTa_equilibrium", typ_id="302", inputs={"yi": 2.0}, params={"K": 3.0, "Tb": 4.0, "Ta": 2.0}, outputs={"yo": 6.0}, states={"x": 2.0}, internals={"dx": 0.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="higher_order_second_order_bypass_equilibrium", typ_id="190", inputs={"yi": 0.0}, params={"A1": 2.0, "A2": 3.0, "B1": 4.0, "B2": 5.0}, outputs={"yo": 0.0}, states={"x1": 0.0, "x2": 0.0}, internals={"dx1": 0.0, "dx2": 0.0, "triv": 0.0}, state_derivatives={"x1": 0.0, "x2": 0.0}),
    FunctionalContract(label="higher_order_second_order_plain_equilibrium", typ_id="192", inputs={"yi": 0.0}, params={"a1": 2.0, "a2": 3.0, "b1": 4.0, "b2": 5.0}, outputs={"yo": 0.0}, states={"x1": 0.0, "x2": 0.0}, internals={"dx1": 0.0, "dx2": 0.0}, state_derivatives={"x1": 0.0, "x2": 0.0}),
    FunctionalContract(label="higher_order_three_pole_bypass_equilibrium", typ_id="191", inputs={"yi": 0.0}, params={"Ta": 2.0, "Tb": 3.0, "Tc": 4.0, "K": 5.0}, outputs={"yo": 0.0}, states={"xa": 0.0, "xb": 0.0, "xc": 0.0}, internals={"yxa": 0.0, "yxb": 0.0, "dxc": 0.0}, state_derivatives={"xa": 0.0, "xb": 0.0, "xc": 0.0}),
    FunctionalContract(label="higher_order_t3_t1_t2_bypass_equilibrium", typ_id="193", inputs={"yi": 0.0}, params={"T1": 2.0, "T2": 3.0, "T3": 4.0}, outputs={"yo": 0.0}, states={"x1": 0.0, "x2": 0.0}, internals={"dx1": 0.0}, state_derivatives={"x1": 0.0, "x2": 0.0}),
    FunctionalContract(label="higher_order_t3_t4_t1_t2_equilibrium", typ_id="194", inputs={"yi": 0.0}, params={"T1": 2.0, "T2": 3.0, "T3": 4.0, "T4": 5.0}, outputs={"yo": 0.0}, states={"x1": 0.0, "x2": 0.0}, internals={"dx1": 0.0, "dx2": 0.0}, state_derivatives={"x1": 0.0, "x2": 0.0}),
    FunctionalContract(label="higher_order_ss_t3_bypass_equilibrium", typ_id="196", inputs={"yi": 0.0}, params={"T1": 2.0, "T2": 3.0, "T3": 4.0}, outputs={"yo": 0.0}, states={"x1": 0.0, "x2": 0.0}, internals={"dx2": 0.0}, state_derivatives={"x1": 0.0, "x2": 0.0}),
    FunctionalContract(label="higher_order_ss_ass_bs_1_bypass_equilibrium", typ_id="198", inputs={"yi": 0.0}, params={"A": 2.0, "B": 3.0}, outputs={"yo": 0.0}, states={"x1": 0.0, "x2": 0.0}, internals={"dx1": 0.0, "dx2": 0.0, "triv": 0.0}, state_derivatives={"x1": 0.0, "x2": 0.0}),
    FunctionalContract(label="higher_order_ss_plus_ww_bypass_equilibrium", typ_id="199", inputs={"yi": 0.0}, params={"B": 2.0, "w": 3.0}, outputs={"yo": 0.0}, states={"x1": 0.0, "x2": 0.0}, internals={"triv": 0.0, "dx1": 0.0, "dx2": 0.0}, state_derivatives={"x1": 0.0, "x2": 0.0}),
    FunctionalContract(label="transform_abc_dq0_power_invariant_align_a_d", typ_id="544", inputs={"a": 1.0, "b": -0.5, "c": -0.5, "theta": 0.0}, params={}, outputs={"d": math.sqrt(3.0 / 2.0), "q": 0.0, "zero": 0.0}, internals={"sqrt2_3": math.sqrt(2.0 / 3.0), "one_sqrt2": 1.0 / math.sqrt(2.0), "twopi_3": 2.0 * math.pi / 3.0}),
    FunctionalContract(label="transform_abc_dq0_power_invariant_align_a_q", typ_id="545", inputs={"a": 1.0, "b": -0.5, "c": -0.5, "theta": 0.0}, params={}, outputs={"d": 0.0, "q": math.sqrt(3.0 / 2.0), "zero": 0.0}, internals={"sqrt2_3": math.sqrt(2.0 / 3.0), "one_sqrt2": 1.0 / math.sqrt(2.0), "twopi_3": 2.0 * math.pi / 3.0}),
    FunctionalContract(label="transform_abc_dq0_power_variant_align_a_d", typ_id="546", inputs={"a": 1.0, "b": -0.5, "c": -0.5, "theta": 0.0}, params={}, outputs={"d": 1.0, "q": 0.0, "zero": 0.0}, internals={"ratio2_3": 2.0 / 3.0, "twopi_3": 2.0 * math.pi / 3.0}),
    FunctionalContract(label="transform_abc_dq0_power_variant_align_a_q", typ_id="547", inputs={"a": 1.0, "b": -0.5, "c": -0.5, "theta": 0.0}, params={}, outputs={"d": 0.0, "q": 1.0, "zero": 0.0}, internals={"ratio2_3": 2.0 / 3.0, "twopi_3": 2.0 * math.pi / 3.0}),
    FunctionalContract(label="transform_dq0_abc_power_invariant_align_a_d", typ_id="548", inputs={"d": math.sqrt(3.0 / 2.0), "q": 0.0, "zero": 0.0, "theta": 0.0}, params={}, outputs={"a": 1.0, "b": -0.5, "c": -0.5}, internals={"sqrt2_3": math.sqrt(2.0 / 3.0), "one_sqrt2": 1.0 / math.sqrt(2.0), "twopi_3": 2.0 * math.pi / 3.0}),
    FunctionalContract(label="transform_dq0_abc_power_invariant_align_a_q", typ_id="549", inputs={"d": 0.0, "q": math.sqrt(3.0 / 2.0), "zero": 0.0, "theta": 0.0}, params={}, outputs={"a": 1.0, "b": -0.5, "c": -0.5}, internals={"sqrt2_3": math.sqrt(2.0 / 3.0), "one_sqrt2": 1.0 / math.sqrt(2.0), "twopi_3": 2.0 * math.pi / 3.0}),
    FunctionalContract(label="transform_dq0_abc_power_variant_align_a_d", typ_id="550", inputs={"d": 1.0, "q": 0.0, "zero": 0.0, "theta": 0.0}, params={}, outputs={"a": 1.0, "b": -0.5, "c": -0.5}, internals={"twopi_3": 2.0 * math.pi / 3.0}),
    FunctionalContract(label="transform_dq0_abc_power_variant_align_a_q", typ_id="551", inputs={"d": 0.0, "q": 1.0, "zero": 0.0, "theta": 0.0}, params={}, outputs={"a": 1.0, "b": -0.5, "c": -0.5}, internals={"twopi_3": 2.0 * math.pi / 3.0}),
    FunctionalContract(label="transform_clarke_power_invariant", typ_id="533", inputs={"a": 1.0, "b": -0.5, "c": -0.5}, params={}, outputs={"alpha": math.sqrt(3.0 / 2.0), "beta": 1.0 / math.sqrt(8.0), "gamma": 0.0}),
    FunctionalContract(label="transform_inverse_clarke_power_invariant", typ_id="535", inputs={"alpha": math.sqrt(3.0 / 2.0), "beta": 0.0, "gamma": 0.0}, params={}, outputs={"a": 1.0, "b": -0.5, "c": -0.5}),
    FunctionalContract(label="transform_inverse_park_dq0", typ_id="538", inputs={"d": 1.0, "q": 0.0, "zero": 0.0, "cosphi": 1.0, "sinphi": 0.0}, params={}, outputs={"alpha": 1.0, "beta": 0.0, "gamma": 0.0}),
    FunctionalContract(label="transform_park_dq0", typ_id="540", inputs={"alpha": 1.0, "beta": 0.0, "gamma": 0.0, "cosphi": 1.0, "sinphi": 0.0}, params={}, outputs={"d": 1.0, "q": 0.0, "zero": 0.0}),
    FunctionalContract(label="comparator_le_signal", typ_id="30", inputs={"yi1": 1.0, "yi2": 1.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="gain_sqrt_2_over_3", typ_id="185", inputs={"yi": math.sqrt(3.0 / 2.0)}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="gain_sqrt_3_over_2", typ_id="186", inputs={"yi": math.sqrt(2.0 / 3.0)}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="gain_sqrt2", typ_id="188", inputs={"yi": 1.0}, params={}, outputs={"yo": math.sqrt(2.0)}),
    FunctionalContract(label="gain_sqrt3", typ_id="189", inputs={"yi": 1.0}, params={}, outputs={"yo": math.sqrt(3.0)}),
    FunctionalContract(label="mechanical_spring_equilibrium", typ_id="432", inputs={"omega1": 2.0, "omega2": 1.0}, params={"K": 2.0, "D": 3.0}, outputs={"M": 4.0}, states={"xphi": 1.0}, internals={"dxphi": 1.0}, state_derivatives={"xphi": 2.0}),
    FunctionalContract(label="shaft_j_k_and_pin_init_equations", typ_id="408", inputs={"omega_k": 2.0, "Pin": 6.0}, params={"K_jk": 2.0, "D_jk": 0.0, "D_jj": 1.0, "H_j": 1.0, "fnom": 1.0}, outputs={"omega_j": 2.0}, init_eqs={"xdtheta_jk": 0.5, "xomega_j": 2.0}),
    FunctionalContract(label="shaft_i_j_k_and_pin_init_equations", typ_id="414", inputs={"omega_k": 2.0, "omega_i": 1.5, "torque_ij": 3.0, "Pin": 4.0}, params={"K_jk": 2.0, "D_jk": 0.0, "D_ij": 0.0, "D_jj": 1.0, "H_j": 1.0, "fnom": 1.0}, outputs={"omega_j": 2.0}, internals={"xomega_j": 2.0}, init_eqs={"xdtheta_jk": 1.5, "xomega_j": 2.0}),
    FunctionalContract(label="shaft_i_j_k_init_equations", typ_id="420", inputs={"omega_k": 2.0, "omega_i": 1.5, "torque_ij": 3.0}, params={"K_jk": 2.0, "D_jk": 0.0, "D_ij": 0.0, "D_jj": 1.0, "H_j": 1.0, "fnom": 1.0}, outputs={"omega_j": 2.0}, init_eqs={"xdtheta_jk": 0.5, "xomega_j": 2.0}),
    FunctionalContract(label="shaft_i_j_init_equations", typ_id="426", inputs={"omega_i": 2.0}, params={"K_ji": 2.0, "D_ji": 0.0, "D_jj": 1.0, "H_j": 1.0, "fnom": 1.0}, outputs={}, internals={"xomega_j": 2.0}, init_eqs={"xdtheta_ji": -1.0, "xomega_j": 2.0}),
    FunctionalContract(label="bias_initial_output", typ_id="54", inputs={}, params={}, outputs={"yo": 3.0}, init_eqs={"bias": 3.0}),
    FunctionalContract(label="resonant_filter_equilibrium", typ_id="118", inputs={"yi": 4.0}, params={"f0": 1.0}, outputs={"yo": 0.0}, states={"x1": 4.0 / ((2.0 * math.pi) ** 2), "x2": 0.0}, internals={"w0": 2.0 * math.pi}, state_derivatives={"x1": 0.0, "x2": 0.0}),
    FunctionalContract(label="higher_order_a23_equilibrium", typ_id="309", inputs={"yi": 2.0}, params={"a11": 2.0, "a13": 0.0, "a21": 0.0, "a23": 1.0, "Tw": 3.0}, outputs={"yo": 2.0}, states={"x": 2.0}, internals={"Ta": 6.0, "Tb": 6.0, "dx": 0.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="bias_initial_output", typ_id="54", inputs={}, params={}, outputs={"yo": 3.0}, init_eqs={"bias": 3.0}),
    FunctionalContract(label="resonant_filter_equilibrium", typ_id="118", inputs={"yi": 4.0}, params={"f0": 1.0}, outputs={"yo": 0.0}, states={"x1": 4.0 / ((2.0 * math.pi) ** 2), "x2": 0.0}, internals={"w0": 2.0 * math.pi}, state_derivatives={"x1": 0.0, "x2": 0.0}),
    FunctionalContract(label="higher_order_a23_equilibrium", typ_id="309", inputs={"yi": 2.0}, params={"a11": 2.0, "a13": 0.0, "a21": 0.0, "a23": 1.0, "Tw": 3.0}, outputs={"yo": 2.0}, states={"x": 2.0}, internals={"Ta": 6.0, "Tb": 6.0, "dx": 0.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="reciprocal_fb_positive", typ_id="368", inputs={"u": 4.0}, params={}, outputs={"yo": 0.25}),
    FunctionalContract(label="selfix_true_branch", typ_id="85", inputs={"condition": 1.0, "y_true": 7.0, "y_false": 9.0}, params={}, outputs={"yo": 7.0}),
    FunctionalContract(label="selfix_false_branch", typ_id="85", inputs={"condition": 0.0, "y_true": 7.0, "y_false": 9.0}, params={}, outputs={"yo": 9.0}),
    FunctionalContract(label="selfix_const_true_branch", typ_id="86", inputs={"condition": 1.0}, params={"K_true": 7.0, "K_false": 9.0}, outputs={"yo": 7.0}),
    FunctionalContract(label="selfix_const_false_branch", typ_id="86", inputs={"condition": 0.0}, params={"K_true": 7.0, "K_false": 9.0}, outputs={"yo": 9.0}),
    FunctionalContract(label="atan2d_zero", typ_id="387", inputs={"re": 1.0, "im": 0.0}, params={}, outputs={"yo": 0.0}),
    FunctionalContract(label="atand_zero", typ_id="388", inputs={"yi": 0.0}, params={}, outputs={"yo": 0.0}),
    FunctionalContract(label="coshd_zero", typ_id="392", inputs={"yi": 0.0}, params={}, outputs={"yo": 1.0}),
    FunctionalContract(label="sinhd_zero", typ_id="396", inputs={"yi": 0.0}, params={}, outputs={"yo": 0.0}),
    FunctionalContract(label="tanhd_zero", typ_id="400", inputs={"yi": 0.0}, params={}, outputs={"yo": 0.0}),
    FunctionalContract(label="enable_2_sig_on", typ_id="494", inputs={"yi1": 4.0, "yi2": 5.0, "Enable": 1.0}, params={"yi1_default": 9.0, "yi2_default": 8.0}, outputs={"yo1": 4.0, "yo2": 5.0}),
    FunctionalContract(label="enable_2_sig_hold_on", typ_id="493", inputs={"yi1": 4.0, "yi2": 5.0, "Enable": 1.0}, params={}, outputs={"yo1": 4.0, "yo2": 5.0}),
    FunctionalContract(label="enable_3_sig_on", typ_id="496", inputs={"yi1": 4.0, "yi2": 5.0, "yi3": 6.0, "Enable": 1.0}, params={"yi1_default": 9.0, "yi2_default": 8.0, "yi3_default": 7.0}, outputs={"yo1": 4.0, "yo2": 5.0, "yo3": 6.0}),
    FunctionalContract(label="enable_3_sig_hold_on", typ_id="495", inputs={"yi1": 4.0, "yi2": 5.0, "yi3": 6.0, "Enable": 1.0}, params={}, outputs={"yo1": 4.0, "yo2": 5.0, "yo3": 6.0}),
    FunctionalContract(label="enable_4_sig_on", typ_id="498", inputs={"yi1": 4.0, "yi2": 5.0, "yi3": 6.0, "yi4": 7.0, "Enable": 1.0}, params={"yi1_default": 9.0, "yi2_default": 8.0, "yi3_default": 7.0, "yi4_default": 6.0}, outputs={"yo1": 4.0, "yo2": 5.0, "yo3": 6.0, "yo4": 7.0}),
    FunctionalContract(label="enable_4_sig_hold_on", typ_id="497", inputs={"yi1": 4.0, "yi2": 5.0, "yi3": 6.0, "yi4": 7.0, "Enable": 1.0}, params={}, outputs={"yo1": 4.0, "yo2": 5.0, "yo3": 6.0, "yo4": 7.0}),
    FunctionalContract(label="enable_5_sig_on", typ_id="500", inputs={"yi1": 4.0, "yi2": 5.0, "yi3": 6.0, "yi4": 7.0, "yi5": 8.0, "Enable": 1.0}, params={"yi1_default": 9.0, "yi2_default": 8.0, "yi3_default": 7.0, "yi4_default": 6.0, "yi5_default": 5.0}, outputs={"yo1": 4.0, "yo2": 5.0, "yo3": 6.0, "yo4": 7.0, "yo5": 8.0}),
    FunctionalContract(label="enable_5_sig_hold_on", typ_id="499", inputs={"yi1": 4.0, "yi2": 5.0, "yi3": 6.0, "yi4": 7.0, "yi5": 8.0, "Enable": 1.0}, params={}, outputs={"yo1": 4.0, "yo2": 5.0, "yo3": 6.0, "yo4": 7.0, "yo5": 8.0}),
    FunctionalContract(label="enable_6_sig_hold_on", typ_id="501", inputs={"yi1": 1.0, "yi2": 2.0, "yi3": 3.0, "yi4": 4.0, "yi5": 5.0, "yi6": 6.0, "Enable": 1.0}, params={}, outputs={"yo1": 1.0, "yo2": 2.0, "yo3": 3.0, "yo4": 4.0, "yo5": 5.0, "yo6": 6.0}),
    FunctionalContract(label="enable_7_sig_hold_on", typ_id="502", inputs={"yi1": 1.0, "yi2": 2.0, "yi3": 3.0, "yi4": 4.0, "yi5": 5.0, "yi6": 6.0, "yi7": 7.0, "Enable": 1.0}, params={}, outputs={"yo1": 1.0, "yo2": 2.0, "yo3": 3.0, "yo4": 4.0, "yo5": 5.0, "yo6": 6.0, "yo7": 7.0}),
    FunctionalContract(label="enable_8_sig_hold_on", typ_id="503", inputs={"yi1": 1.0, "yi2": 2.0, "yi3": 3.0, "yi4": 4.0, "yi5": 5.0, "yi6": 6.0, "yi7": 7.0, "yi8": 8.0, "Enable": 1.0}, params={}, outputs={"yo1": 1.0, "yo2": 2.0, "yo3": 3.0, "yo4": 4.0, "yo5": 5.0, "yo6": 6.0, "yo7": 7.0, "yo8": 8.0}),
    FunctionalContract(label="switch_par_1_2_by_sig_right", typ_id="509", inputs={"sw": 1.0}, params={"K": 7.0}, outputs={"yo1": 0.0, "yo2": 7.0}),
    FunctionalContract(label="switch_sig_1_2_by_par_bool_second", typ_id="514", inputs={"yi": 5.0}, params={"sw": 2.0}, outputs={"yo1": 0.0, "yo2": 5.0}),
    FunctionalContract(label="switch_sig_1_2_by_sig_right", typ_id="516", inputs={"yi": 5.0, "sw": 1.0}, params={}, outputs={"yo1": 0.0, "yo2": 5.0}),
    FunctionalContract(label="shaft_j_k_and_pin_init_equations", typ_id="408", inputs={"omega_k": 2.0, "Pin": 6.0}, params={"K_jk": 2.0, "D_jk": 0.0, "D_jj": 1.0, "H_j": 1.0, "fnom": 1.0}, outputs={"omega_j": 2.0}, init_eqs={"xdtheta_jk": 0.5, "xomega_j": 2.0}),
    FunctionalContract(label="shaft_i_j_k_and_pin_init_equations", typ_id="414", inputs={"omega_k": 2.0, "omega_i": 1.5, "torque_ij": 3.0, "Pin": 4.0}, params={"K_jk": 2.0, "D_jk": 0.0, "D_ij": 0.0, "D_jj": 1.0, "H_j": 1.0, "fnom": 1.0}, outputs={"omega_j": 2.0}, internals={"xomega_j": 2.0}, init_eqs={"xdtheta_jk": 1.5, "xomega_j": 2.0}),
    FunctionalContract(label="shaft_i_j_k_init_equations", typ_id="420", inputs={"omega_k": 2.0, "omega_i": 1.5, "torque_ij": 3.0}, params={"K_jk": 2.0, "D_jk": 0.0, "D_ij": 0.0, "D_jj": 1.0, "H_j": 1.0, "fnom": 1.0}, outputs={"omega_j": 2.0}, init_eqs={"xdtheta_jk": 0.5, "xomega_j": 2.0}),
    FunctionalContract(label="shaft_i_j_init_equations", typ_id="426", inputs={"omega_i": 2.0}, params={"K_ji": 2.0, "D_ji": 0.0, "D_jj": 1.0, "H_j": 1.0, "fnom": 1.0}, outputs={}, internals={"xomega_j": 2.0}, init_eqs={"xdtheta_ji": -1.0, "xomega_j": 2.0}),
    FunctionalContract(label="transform_abc_dq0_power_invariant_align_a_d", typ_id="544", inputs={"a": 1.0, "b": -0.5, "c": -0.5, "theta": 0.0}, params={}, outputs={"d": math.sqrt(3.0 / 2.0), "q": 0.0, "zero": 0.0}, internals={"sqrt2_3": math.sqrt(2.0 / 3.0), "one_sqrt2": 1.0 / math.sqrt(2.0), "twopi_3": 2.0 * math.pi / 3.0}),
    FunctionalContract(label="transform_abc_dq0_power_invariant_align_a_q", typ_id="545", inputs={"a": 1.0, "b": -0.5, "c": -0.5, "theta": 0.0}, params={}, outputs={"d": 0.0, "q": math.sqrt(3.0 / 2.0), "zero": 0.0}, internals={"sqrt2_3": math.sqrt(2.0 / 3.0), "one_sqrt2": 1.0 / math.sqrt(2.0), "twopi_3": 2.0 * math.pi / 3.0}),
    FunctionalContract(label="transform_abc_dq0_power_variant_align_a_d", typ_id="546", inputs={"a": 1.0, "b": -0.5, "c": -0.5, "theta": 0.0}, params={}, outputs={"d": 1.0, "q": 0.0, "zero": 0.0}, internals={"ratio2_3": 2.0 / 3.0, "twopi_3": 2.0 * math.pi / 3.0}),
    FunctionalContract(label="transform_abc_dq0_power_variant_align_a_q", typ_id="547", inputs={"a": 1.0, "b": -0.5, "c": -0.5, "theta": 0.0}, params={}, outputs={"d": 0.0, "q": 1.0, "zero": 0.0}, internals={"ratio2_3": 2.0 / 3.0, "twopi_3": 2.0 * math.pi / 3.0}),
    FunctionalContract(label="transform_dq0_abc_power_invariant_align_a_d", typ_id="548", inputs={"d": math.sqrt(3.0 / 2.0), "q": 0.0, "zero": 0.0, "theta": 0.0}, params={}, outputs={"a": 1.0, "b": -0.5, "c": -0.5}, internals={"sqrt2_3": math.sqrt(2.0 / 3.0), "one_sqrt2": 1.0 / math.sqrt(2.0), "twopi_3": 2.0 * math.pi / 3.0}),
    FunctionalContract(label="transform_dq0_abc_power_invariant_align_a_q", typ_id="549", inputs={"d": 0.0, "q": math.sqrt(3.0 / 2.0), "zero": 0.0, "theta": 0.0}, params={}, outputs={"a": 1.0, "b": -0.5, "c": -0.5}, internals={"sqrt2_3": math.sqrt(2.0 / 3.0), "one_sqrt2": 1.0 / math.sqrt(2.0), "twopi_3": 2.0 * math.pi / 3.0}),
    FunctionalContract(label="transform_dq0_abc_power_variant_align_a_d", typ_id="550", inputs={"d": 1.0, "q": 0.0, "zero": 0.0, "theta": 0.0}, params={}, outputs={"a": 1.0, "b": -0.5, "c": -0.5}, internals={"twopi_3": 2.0 * math.pi / 3.0}),
    FunctionalContract(label="transform_dq0_abc_power_variant_align_a_q", typ_id="551", inputs={"d": 0.0, "q": 1.0, "zero": 0.0, "theta": 0.0}, params={}, outputs={"a": 1.0, "b": -0.5, "c": -0.5}, internals={"twopi_3": 2.0 * math.pi / 3.0}),
    FunctionalContract(label="filter_low_pass_rst_hold_state_and_rate_zero_equilibrium", typ_id="155", inputs={"yi": 0.0, "hold": 0.0, "rst": 0.0}, params={"T": 1.0, "y_min": -100.0, "y_max": 100.0, "r_min": -100.0, "r_max": 100.0}, outputs={"yo": 0.0}, states={"x": 0.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="filter_low_pass_rst_hold_signal_limit_zero_equilibrium", typ_id="156", inputs={"yi": 0.0, "hold": 0.0, "y_max": 100.0, "rst": 0.0}, params={"T": 1.0}, outputs={"yo": 0.0}, states={"x": 0.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="filter_low_pass_rst_hold_signal_limits_zero_equilibrium", typ_id="157", inputs={"yi": 0.0, "hold": 0.0, "y_min": -100.0, "y_max": 100.0, "rst": 0.0}, params={"T": 1.0}, outputs={"yo": 0.0}, states={"x": 0.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="filter_low_pass_rst_sig_hold_state_and_rate_zero_equilibrium", typ_id="163", inputs={"yi": 0.0, "hold": 0.0, "x_rst": 0.0, "rst": 0.0}, params={"T": 1.0, "y_min": -100.0, "y_max": 100.0, "r_min": -100.0, "r_max": 100.0}, outputs={"yo": 0.0}, states={"x": 0.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="filter_low_pass_rst_sig_hold_signal_limit_zero_equilibrium", typ_id="164", inputs={"yi": 0.0, "hold": 0.0, "x_rst": 0.0, "y_max": 100.0, "rst": 0.0}, params={"T": 1.0}, outputs={"yo": 0.0}, states={"x": 0.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="filter_low_pass_rst_sig_hold_signal_limits_zero_equilibrium", typ_id="165", inputs={"yi": 0.0, "hold": 0.0, "x_rst": 0.0, "y_min": -100.0, "y_max": 100.0, "rst": 0.0}, params={"T": 1.0}, outputs={"yo": 0.0}, states={"x": 0.0}, state_derivatives={"x": 0.0}),
    FunctionalContract(label="integrator_1_over_s_incfreeze_zero_equilibrium", typ_id="213", inputs={"yi": 0.0}, params={"Tincfreeze": 1.0}, outputs={"yo": 0.0}, states={"x": 0.0}, state_derivatives={"x": 0.0}, internals={"t0": 0.0}),
    FunctionalContract(label="integrator_1_over_sT_bypass_incfreeze_zero_equilibrium", typ_id="230", inputs={"yi": 0.0}, params={"T": 1.0, "Tincfreeze": 1.0}, outputs={"yo": 0.0}, states={"x": 0.0}, state_derivatives={"x": 0.0}, internals={"t0": 0.0}),
    FunctionalContract(label="integrator_1_over_s_reset_zero_equilibrium", typ_id="245", inputs={"yi": 0.0, "rst": 0.0}, params={}, outputs={"yo": 0.0}, states={"x": 0.0}, state_derivatives={"x": 0.0}, internals={"xinc": 0.0}),
    ]
    return functional_contracts


def build_dynamic_functional_contracts() -> list[DynamicFunctionalContract]:
    """
    Build the explicit dynamic functional contracts for the exported DGS catalog.

    :return: Dynamic functional contracts.
    """
    dynamic_functional_contracts: list[DynamicFunctionalContract] = [
    DynamicFunctionalContract(
        label="delay_fixed_10ms_after_delay",
        typ_id="101",
        t_end=0.02,
        dt=0.005,
        params={},
        inputs={"yi": 2.0},
        outputs={"yo": 2.0},
    ),
    DynamicFunctionalContract(
        label="delay_variable_bypass_after_delay",
        typ_id="102",
        t_end=0.2,
        dt=0.01,
        params={"T": 0.1},
        inputs={"yi": 2.0},
        outputs={"yo": 2.0},
    ),
    DynamicFunctionalContract(
        label="lastvalue_tracks_constant_signal_after_first_step",
        typ_id="109",
        t_end=0.02,
        dt=0.01,
        params={},
        inputs={"yi": 2.0},
        outputs={"yo": 2.0},
    ),
    DynamicFunctionalContract(
        label="clock_par_initial_low",
        typ_id="479",
        t_end=0.25,
        dt=0.01,
        params={"cFreq": 1.0},
        inputs={},
        outputs={"output": 0.0},
    ),
    DynamicFunctionalContract(
        label="clock_sig_initial_low",
        typ_id="480",
        t_end=0.25,
        dt=0.01,
        params={},
        inputs={"extfrq": 1.0},
        outputs={"output": 0.0},
    ),
    DynamicFunctionalContract(
        label="clock_t_gt_0_par_initial_low",
        typ_id="475",
        t_end=0.25,
        dt=0.01,
        params={"cFreq": 1.0},
        inputs={},
        outputs={"output": 0.0},
    ),
    DynamicFunctionalContract(
        label="clock_t_gt_0_sig_initial_low",
        typ_id="476",
        t_end=0.25,
        dt=0.01,
        params={},
        inputs={"extfrq": 1.0},
        outputs={"output": 0.0},
    ),
    DynamicFunctionalContract(
        label="clock_t_gt_t0_par_initially_low",
        typ_id="477",
        t_end=0.25,
        dt=0.01,
        params={"cFreq": 1.0},
        inputs={},
        outputs={"output": 0.0},
    ),
    DynamicFunctionalContract(
        label="clock_t_gt_t0_sig_initially_low",
        typ_id="478",
        t_end=0.25,
        dt=0.01,
        params={},
        inputs={"extfrq": 1.0},
        outputs={"output": 0.0},
    ),
    DynamicFunctionalContract(
        label="pulse_returns_low_after_delay_window",
        typ_id="481",
        t_end=0.3,
        dt=0.005,
        params={"K": 1.0, "T1": 0.2},
        inputs={"yi": 2.0},
        outputs={"yo": 0.0},
    ),
    DynamicFunctionalContract(
        label="timer_reset_hold_reset_t0_tracks_elapsed_after_start_delay",
        typ_id="532",
        t_end=0.25,
        dt=0.01,
        params={"flank": 0.0, "t_start_delay": 0.1},
        inputs={"rst": 0.0, "t0": 5.0},
        outputs={"yo": 5.14},
    ),
    DynamicFunctionalContract(
        label="movingavg_tracks_constant_input",
        typ_id="77",
        t_end=0.4,
        dt=0.01,
        params={"Tdel": 0.1, "Tlength": 0.2},
        inputs={"yi": 3.0},
        outputs={"yo": 3.0},
    ),
    DynamicFunctionalContract(
        label="delayed_second_order_zero_equilibrium",
        typ_id="204",
        t_end=0.2,
        dt=0.01,
        params={"T1": 1.0, "T2": 1.0, "Td": 0.1},
        inputs={"yi": 0.0},
        outputs={"yo": 0.0},
    ),
    DynamicFunctionalContract(
        label="delay_runtime_after_delay",
        typ_id="67",
        t_end=0.2,
        dt=0.01,
        params={"T": 0.1},
        inputs={"yi": 2.0},
        outputs={"yo": 2.0},
    ),
    DynamicFunctionalContract(
        label="gradlim_const_tracks_constant_input",
        typ_id="69",
        t_end=0.2,
        dt=0.01,
        params={"gradmin": -100.0, "gradmax": 100.0},
        inputs={"yi": 2.0},
        outputs={"yo": 2.0},
    ),
    DynamicFunctionalContract(
        label="transport_delay_backward_bypass_after_delay",
        typ_id="103",
        t_end=0.2,
        dt=0.01,
        params={"T": 0.1},
        inputs={"yi": 3.0},
        outputs={"yo": 0.0},
    ),
    DynamicFunctionalContract(
        label="transport_delay_forward_bypass_after_delay",
        typ_id="104",
        t_end=0.2,
        dt=0.01,
        params={"T": 0.1},
        inputs={"yi": 3.0},
        outputs={"yo": 3.0},
    ),
    DynamicFunctionalContract(
        label="transport_delay_backward_after_delay",
        typ_id="105",
        t_end=0.2,
        dt=0.01,
        params={"T": 0.1},
        inputs={"yi": 3.0},
        outputs={"yo": 3.0},
    ),
    DynamicFunctionalContract(
        label="transport_delay_forward_after_delay",
        typ_id="106",
        t_end=0.2,
        dt=0.01,
        params={"T": 0.1},
        inputs={"yi": 3.0},
        outputs={"yo": 3.0},
    ),
    DynamicFunctionalContract(
        label="transport_delay_gain_bypass_after_delay",
        typ_id="97",
        t_end=0.2,
        dt=0.01,
        params={"K": 2.0, "T": 0.1},
        inputs={"yi": 3.0},
        outputs={"yo": 6.0},
    ),
    DynamicFunctionalContract(
        label="transport_delay_gain_forward_after_delay",
        typ_id="98",
        t_end=0.2,
        dt=0.01,
        params={"K": 2.0, "T": 0.1},
        inputs={"yi": 3.0},
        outputs={"yo": 6.0},
    ),
    DynamicFunctionalContract(
        label="rate_limiter_tracks_constant_input",
        typ_id="325",
        t_end=0.2,
        dt=0.01,
        params={"grd_up": 100.0},
        inputs={"yi": 2.0},
        outputs={"yo": 2.0},
    ),
    DynamicFunctionalContract(
        label="rate_limiter_base_tracks_constant_input",
        typ_id="326",
        t_end=0.2,
        dt=0.01,
        params={"base": 2.0, "grd_up": 100.0},
        inputs={"yi": 4.0},
        outputs={"yo": 4.0},
    ),
    DynamicFunctionalContract(
        label="rate_limiter_lower_tracks_constant_input",
        typ_id="330",
        t_end=0.2,
        dt=0.01,
        params={"grd_down": 100.0},
        inputs={"yi": 2.0},
        outputs={"yo": 2.0},
    ),
    DynamicFunctionalContract(
        label="rate_limiter_base_lower_tracks_constant_input",
        typ_id="327",
        t_end=0.2,
        dt=0.01,
        params={"base": 2.0, "grd_down": 100.0},
        inputs={"yi": 4.0},
        outputs={"yo": 4.0},
    ),
    DynamicFunctionalContract(
        label="rate_limiter_base_asymmetric_tracks_constant_input",
        typ_id="328",
        t_end=0.2,
        dt=0.01,
        params={"base": 2.0, "grd_down": 100.0, "grd_up": 100.0},
        inputs={"yi": 4.0},
        outputs={"yo": 4.0},
    ),
    DynamicFunctionalContract(
        label="rate_limiter_asymmetric_tracks_constant_input",
        typ_id="331",
        t_end=0.2,
        dt=0.01,
        params={"grd_down": 100.0, "grd_up": 100.0},
        inputs={"yi": 2.0},
        outputs={"yo": 2.0},
    ),
    DynamicFunctionalContract(
        label="rate_limiter_base_symmetric_tracks_constant_input",
        typ_id="329",
        t_end=0.2,
        dt=0.01,
        params={"base": 2.0, "grd": 100.0},
        inputs={"yi": 4.0},
        outputs={"yo": 4.0},
    ),
    DynamicFunctionalContract(
        label="rate_limiter_symmetric_tracks_constant_input",
        typ_id="332",
        t_end=0.2,
        dt=0.01,
        params={"grd": 100.0},
        inputs={"yi": 2.0},
        outputs={"yo": 2.0},
    ),
    DynamicFunctionalContract(
        label="rms_value_constant_input",
        typ_id="542",
        t_end=0.05,
        dt=0.005,
        params={"fn": 50.0},
        inputs={"yi": 3.0},
        outputs={"yo": 3.0},
    ),
    DynamicFunctionalContract(
        label="rms_value_pu_constant_input",
        typ_id="541",
        t_end=0.05,
        dt=0.005,
        params={"fn": 50.0},
        inputs={"yi": 1.0},
        outputs={"yo": 1.41421356237},
    ),
    DynamicFunctionalContract(
        label="seq_ab0_to_abc_zero_equilibrium_after_window",
        typ_id="543",
        t_end=0.05,
        dt=0.005,
        params={"fn": 50.0},
        inputs={"u1": 0.0, "u1r": 0.0, "u1i": 0.0, "u2r": 0.0, "u2i": 0.0, "u0r": 0.0, "u0i": 0.0, "u0": 0.0},
        outputs={"ua": 0.0, "ub": 0.0, "uc": 0.0, "uab": 0.0, "ubc": 0.0, "uca": 0.0},
    ),
    DynamicFunctionalContract(
        label="monostable_rises_on_step",
        typ_id="353",
        t_end=0.05,
        dt=0.01,
        params={"T": 0.2},
        inputs={"yi": 1.0},
        outputs={"yo": 1.0},
    ),
    ]
    return dynamic_functional_contracts


class TestDevicesCatalogFunctionalContractsHarness(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        """
        Keep the class-level setup hook explicit for the shared harness.

        :return: None.
        """
        pass

    @staticmethod
    def _eval_expr_like(expr_like: Expr | Comparison | float | int | bool, uid_bindings: Dict[int, float]) -> float:
        expr = expr_like.to_expression() if isinstance(expr_like, Comparison) else expr_like
        if isinstance(expr, (float, int, bool)):
            return float(expr)
        return float(expr.eval_uid(uid_bindings))

    @staticmethod
    def _solve_static_algebraics(block, uid_bindings: Dict[int, float], iterations: int = 6) -> None:
        for _ in range(iterations):
            changed = False
            for var, eq in zip(block.algebraic_vars, block.algebraic_eqs):
                current = float(uid_bindings.get(var.uid, 0.0))
                try:
                    residual = float(eq.eval_uid(uid_bindings))
                except ZeroDivisionError:
                    residual = current
                updated = current - residual
                if math.isfinite(updated):
                    if abs(updated - current) > 1e-12:
                        uid_bindings[var.uid] = updated
                        changed = True
                    else:
                        pass
                else:
                    pass
            if not changed:
                break

    @staticmethod
    def _eval_runtime_expr(problem, expr_like: Expr | Comparison | float | int | bool, x, params, t: float) -> float:
        expr = expr_like.to_expression() if isinstance(expr_like, Comparison) else expr_like
        if isinstance(expr, (float, int, bool)):
            return float(expr)
        if isinstance(expr, Var) and (expr.name in {"glob_time", "time"} or expr.name.startswith("glob_time_") or expr.name.startswith("time_")):
            return float(t)

        uid_bindings = {problem.glob_time.uid: float(t)}
        for uid, idx in problem.uid2idx_vars.items():
            uid_bindings[uid] = float(x[idx])
        for uid, idx in problem.uid2idx_event_params.items():
            uid_bindings[uid] = float(params[idx])
        for var in expr.get_vars():
            if var.name in {"glob_time", "time"} or var.name.startswith("glob_time_") or var.name.startswith("time_"):
                uid_bindings[var.uid] = float(t)
        return float(expr.eval_uid(uid_bindings))

    def build_dynamic_runtime(self, contract: DynamicFunctionalContract) -> tuple[Block, FunctionalRuntimeProblem, np.ndarray, np.ndarray]:
        """
        Build the symbolic runtime objects required by one dynamic contract.

        :param contract: Dynamic functional contract.
        :return: Block, lightweight runtime problem, state vector and runtime parameter vector.
        """
        # Import the generated template exactly as the final menu action would do.
        templ = build_template(contract.typ_id)
        block: Block = templ.block
        hidden_runtime_vars = []
        known_surface = list(block.state_vars) + list(block.algebraic_vars) + list(block.in_vars)
        for var in list(block.init_eqs.keys()) + list(block.diff_init_eqs.keys()):
            if all(existing.uid != var.uid for existing in known_surface):
                hidden_runtime_vars.append(var)
                known_surface.append(var)
        if hidden_runtime_vars:
            block.algebraic_vars = list(block.algebraic_vars) + hidden_runtime_vars

        glob_time_var = None
        for eq in list(block.algebraic_eqs) + list(block.state_eqs):
            for var in eq.get_vars():
                if var.name in {"glob_time", "time"}:
                    glob_time_var = var
                    break
            if glob_time_var is not None:
                break
        if glob_time_var is None:
            for expr in list(block.init_eqs.values()) + list(block.diff_init_eqs.values()):
                for var in expr.get_vars():
                    if var.name in {"glob_time", "time"}:
                        glob_time_var = var
                        break
                if glob_time_var is not None:
                    break
        if glob_time_var is None:
            glob_time_var = Var("glob_time")

        problem: FunctionalRuntimeProblem = FunctionalRuntimeProblem(block, glob_time_var)
        x: np.ndarray = np.zeros(len(problem.uid2idx_vars), dtype=np.float64)
        params: np.ndarray = np.zeros(len(problem.uid2idx_event_params), dtype=np.float64)

        for var, expr in block.event_dict.items():
            idx = problem.uid2idx_event_params[var.uid]
            parameter_name: str = find_event_parameter_name(var, expr)
            value = contract.params.get(parameter_name, None)
            if value is None:
                value = contract.params.get(var.name.split("__")[-1].split("_")[0], None)
            else:
                pass
            if value is None:
                value = contract.params.get(var.name, None)
            else:
                pass
            if value is None:
                default_expr = expr
                value = evaluate_runtime_expr(problem, default_expr, x, params, 0.0)
            else:
                pass
            params[idx] = float(value)

        for var in block.mode_dict.keys():
            idx = problem.uid2idx_event_params[var.uid]
            default_expr = block.mode_dict[var]
            params[idx] = evaluate_runtime_expr(problem, default_expr, x, params, 0.0)

        for name, value in contract.inputs.items():
            input_var = next(var for var in block.in_vars if var.name.startswith(name + "_") or var.name == name)
            x[problem.uid2idx_vars[input_var.uid]] = float(value)

        for var, expr in block.init_eqs.items():
            x[problem.uid2idx_vars[var.uid]] = evaluate_runtime_expr(problem, expr, x, params, 0.0)

        for logic in block.procedural_logic:
            logic.bind(problem)

        return block, problem, x, params

    def solve_runtime_algebraics(self, block: Block, problem: FunctionalRuntimeProblem, x: np.ndarray, params: np.ndarray, t: float) -> None:
        """
        Solve the algebraic surface during the dynamic mini-stepper.

        :param block: Symbolic block under test.
        :param problem: Lightweight runtime problem.
        :param x: Runtime state/algebraic vector.
        :param params: Runtime parameter vector.
        :param t: Current simulation time.
        :return: None.
        """
        for var, eq in zip(block.algebraic_vars, block.algebraic_eqs):
            idx = problem.uid2idx_vars[var.uid]
            saved = float(x[idx])
            x[idx] = 0.0
            residual_at_zero = evaluate_runtime_expr(problem, eq, x, params, t)
            x[idx] = -residual_at_zero
            if math.isnan(x[idx]) or math.isinf(x[idx]):
                x[idx] = saved

    def simulate_dynamic_contract(self, contract: DynamicFunctionalContract) -> None:
        """
        Simulate one dynamic contract with the explicit catalog mini-stepper.

        :param contract: Dynamic functional contract.
        :return: None.
        """
        block, problem, x, params = self.build_dynamic_runtime(contract)

        # The explicit Euler loop is sufficient for the catalog blocks that only need lightweight dynamic checks.
        t = 0.0
        for uid, idx in problem.uid2idx_vars.items():
            var = problem.vars_by_uid[uid]
            if var.name in {"glob_time", "time"} or var.name.startswith("glob_time_") or var.name.startswith("time_"):
                x[idx] = t
        self.solve_runtime_algebraics(block, problem, x, params, t)
        for logic in block.procedural_logic:
            logic.update(t, x, params)
        self.solve_runtime_algebraics(block, problem, x, params, t)

        state_vars = list(block.state_vars)
        while t < contract.t_end - 1e-12:
            dt = min(contract.dt, contract.t_end - t)
            derivs = [evaluate_runtime_expr(problem, expr, x, params, t) for expr in block.state_eqs]
            for var, dx in zip(state_vars, derivs):
                x[problem.uid2idx_vars[var.uid]] += float(dx) * dt
            t += dt
            for uid, idx in problem.uid2idx_vars.items():
                var = problem.vars_by_uid[uid]
                if var.name in {"glob_time", "time"} or var.name.startswith("glob_time_") or var.name.startswith("time_"):
                    x[idx] = t
            for logic in block.procedural_logic:
                logic.update(t, x, params)
            self.solve_runtime_algebraics(block, problem, x, params, t)

        for name, expected in contract.outputs.items():
            output_var = next(var for var in block.out_vars if var.name.startswith(name + "_") or var.name == name)
            actual = float(x[problem.uid2idx_vars[output_var.uid]])
            self.assertAlmostEqual(actual, expected, delta=contract.tol)

    def evaluate_contract(self, contract: FunctionalContract) -> None:
        """
        Evaluate one static contract against the exported template equations and retained logic.

        :param contract: Static functional contract.
        :return: None.
        """
        # Import the exact generated template so the test always reflects the artifact that would reach the menu.
        templ = build_template(contract.typ_id)
        block: Block = templ.block

        # Seed the full variable surface with deterministic values before applying the explicit contract values.
        uid_bindings: Dict[int, float] = dict()
        initial_surface_vars = list(block.state_vars) + list(block.algebraic_vars) + list(block.in_vars) + list(block.out_vars)
        initial_surface_vars.extend(list(block.event_dict.keys()))
        initial_surface_vars.extend(list(block.mode_dict.keys()))
        initial_surface_vars.extend(list(block.init_eqs.keys()))
        initial_surface_vars.extend(list(block.diff_init_eqs.keys()))
        for var in initial_surface_vars:
            uid_bindings[var.uid] = 0.0
        for eq in list(block.algebraic_eqs) + list(block.state_eqs) + list(block.init_eqs.values()) + list(block.diff_init_eqs.values()):
            for var in eq.get_vars():
                uid_bindings[var.uid] = 0.0

        # Collect every internal variable that can affect the static algebraic/procedural evaluation.
        internal_surface_vars = collect_internal_surface_vars(block)

        all_surface_vars = list(internal_surface_vars) + list(block.in_vars) + list(block.out_vars) + list(block.state_vars) + list(block.event_dict.keys()) + list(block.mode_dict.keys())
        assigned_uids = set()

        for name, value in contract.inputs.items():
            set_surface_values(block.in_vars, uid_bindings, assigned_uids, name, value, matches_surface_name)
        if contract.init_eqs is not None:
            for name, value in contract.outputs.items():
                set_surface_values(block.out_vars, uid_bindings, assigned_uids, name, value, matches_surface_name)
        for name, value in contract.params.items():
            set_event_parameter_value(block, uid_bindings, assigned_uids, name, value)
        if contract.states is not None:
            for name, value in contract.states.items():
                state_var = find_named_var(block.state_vars, name, matcher=matches_internal_name)
                uid_bindings[state_var.uid] = value
                assigned_uids.add(state_var.uid)
                for diff_var in block.diff_vars:
                    if diff_var.base_var is state_var:
                        uid_bindings[diff_var.uid] = value
                        assigned_uids.add(diff_var.uid)
        bind_internal_surface_values(uid_bindings, contract.internals, internal_surface_vars)
        if contract.internals is not None:
            for logical_name in contract.internals.keys():
                for var in internal_surface_vars:
                    if matches_internal_name(var, logical_name):
                        assigned_uids.add(var.uid)
        for init_var, init_expr in block.init_eqs.items():
            if init_var.uid not in assigned_uids:
                try:
                    uid_bindings[init_var.uid] = evaluate_expr_like(init_expr, uid_bindings)
                except ZeroDivisionError:
                    pass
        if contract.init_eqs is not None:
            for logical_name, expected in contract.init_eqs.items():
                init_var = find_named_var(list(block.init_eqs.keys()), logical_name, matcher=matches_internal_name)
                actual = evaluate_expr_like(block.init_eqs[init_var], uid_bindings)
                self.assertAlmostEqual(actual, expected, delta=contract.tol)

        # Alternate algebraic resolution and procedural logic evaluation until the static surface stabilizes.
        mode_vars_by_name = {var.name: var for var in block.mode_dict.keys()}
        for _ in range(4):
            solve_static_algebraics(block, uid_bindings)
            for logic in block.procedural_logic:
                if isinstance(logic, SampledValueLogic):
                    uid_bindings[mode_vars_by_name[logic.output_var_name].uid] = evaluate_expr_like(logic.source_expr, uid_bindings)
                elif isinstance(logic, FixedSampleLogic):
                    bool_value = evaluate_expr_like(logic.condition_expr, uid_bindings) > 0.5
                    uid_bindings[mode_vars_by_name[logic.output_var_name].uid] = 1.0 if bool_value else 0.0
                elif isinstance(logic, ResetOnRisingEdgeLogic):
                    if evaluate_expr_like(logic.reset_expr, uid_bindings) > 0.5:
                        target_matches = {}
                        for var in internal_surface_vars:
                            if var.name == logic.target_var_name or logic.target_var_name in var.name:
                                target_matches[var.uid] = var
                        if len(target_matches) != 1:
                            raise KeyError(f"Could not bind reset target '{logic.target_var_name}' uniquely")
                        uid_bindings[next(iter(target_matches.values())).uid] = evaluate_expr_like(logic.value_expr, uid_bindings)
                elif isinstance(logic, PickupDropoffLogic):
                    bool_on = evaluate_expr_like(logic.bool_expr, uid_bindings) > 0.5
                    pickup_delay = evaluate_expr_like(logic.pickup_delay_expr, uid_bindings)
                    drop_delay = evaluate_expr_like(logic.drop_delay_expr, uid_bindings)
                    uid_bindings[mode_vars_by_name[logic.output_var_name].uid] = 1.0 if (bool_on and pickup_delay <= 0.0) else 0.0 if ((not bool_on) and drop_delay <= 0.0) else 0.0
                elif isinstance(logic, FlipFlopLogic):
                    set_on = evaluate_expr_like(logic.set_expr, uid_bindings) > 0.5
                    reset_on = evaluate_expr_like(logic.reset_expr, uid_bindings) > 0.5
                    prior = float(uid_bindings.get(mode_vars_by_name[logic.output_var_name].uid, 0.0))
                    uid_bindings[mode_vars_by_name[logic.output_var_name].uid] = 1.0 if set_on else 0.0 if reset_on else prior
                elif isinstance(logic, AnalogFlipFlopLogic):
                    set_on = evaluate_expr_like(logic.set_expr, uid_bindings) > 0.5
                    reset_on = evaluate_expr_like(logic.reset_expr, uid_bindings) > 0.5
                    input_value = evaluate_expr_like(logic.input_expr, uid_bindings)
                    prior = float(uid_bindings.get(mode_vars_by_name[logic.output_var_name].uid, 0.0))
                    uid_bindings[mode_vars_by_name[logic.output_var_name].uid] = input_value if set_on else 0.0 if reset_on else prior
                else:
                    raise TypeError(f"Functional contract harness does not support procedural logic {type(logic).__name__}")

        solve_static_algebraics(block, uid_bindings)

        for name, expected in contract.outputs.items():
            out_var = find_named_var(block.out_vars, name, matcher=matches_surface_name)
            actual = float(uid_bindings[out_var.uid])
            self.assertAlmostEqual(actual, expected, delta=contract.tol)

        for eq in block.algebraic_eqs:
            residual = float(eq.eval_uid(uid_bindings))
            self.assertAlmostEqual(residual, 0.0, delta=contract.tol)

        if contract.state_derivatives is not None:
            state_name: str
            expected: float
            for state_name, expected in contract.state_derivatives.items():
                state_var = find_named_var(block.state_vars, state_name, matcher=matches_internal_name)
                state_index: int = list(block.state_vars).index(state_var)
                expr = block.state_eqs[state_index]
                actual = float(expr.eval_uid(uid_bindings))
                self.assertAlmostEqual(actual, expected, delta=contract.tol)
