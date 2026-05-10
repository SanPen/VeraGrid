# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import math
import os

from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

import numpy as np

from VeraGridEngine.Utils.emt_boundary_update_wrapper import BoundaryUpdateWrapper
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import CmpOp, Comparison, Const, Expr, Var, expression2numba
from VeraGridEngine.basic_structures import Vec
from VeraGridEngine.enumerations import ProceduralLogicType

if TYPE_CHECKING:
    from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
else:
    pass


ProceduralLogicData = Dict[str, Any]
VarRemap = Dict[Expr | str, Expr]


def _expr_like_to_dict(expr: Expr | Comparison | float | int | bool) -> ProceduralLogicData:
    """
    Serialize a symbolic expression or comparison used by procedural logic.

    :param expr: Procedural expression to serialize.
    :return: Dictionary with enough information to rebuild the expression later.
    """
    if isinstance(expr, Comparison):
        rhs: Expr | float | int = expr.rhs
        if isinstance(rhs, Expr):
            rhs_expr: Expr = rhs
            rhs_data: Any = rhs_expr.to_dict()
        else:
            rhs_data = rhs
        return {
            "kind": "Comparison",
            "lhs": expr.lhs.to_dict(),
            "op": expr.op.value,
            "rhs": rhs_data,
            "rhs_is_expr": isinstance(rhs, Expr),
        }
    if isinstance(expr, Expr):
        return {
            "kind": "Expr",
            "expr": expr.to_dict(),
        }
    return {
        "kind": "Scalar",
        "value": float(expr),
    }


def _expr_like_from_dict(data: ProceduralLogicData) -> Expr | Comparison:
    """
    Deserialize a symbolic expression or comparison used by procedural logic.

    :param data: Serialized expression dictionary.
    :return: Reconstructed symbolic expression or comparison.
    """
    kind: str = str(data.get("kind", "Expr"))
    if kind == "Expr":
        return Expr.from_dict(data["expr"])

    if kind == "Scalar":
        return Const(float(data["value"]))

    if kind == "Comparison":
        rhs_raw: Any = data["rhs"]
        rhs: Expr | float | int = Expr.from_dict(rhs_raw) if bool(data.get("rhs_is_expr", False)) else rhs_raw
        op_text: str = str(data["op"])

        return Comparison(
            lhs=Expr.from_dict(data["lhs"]),
            op=CmpOp(op_text),
            rhs=rhs,
        )

    raise ValueError(f"Unsupported procedural expression kind '{kind}'")


def _subs_expr_like(expr: Expr | Comparison | float | int | bool, mapping: VarRemap) -> Expr | Comparison:
    """
    Apply a variable substitution to a procedural expression.

    :param expr: Expression or comparison to remap.
    :param mapping: Variable substitution map.
    :return: Remapped expression.
    """
    if isinstance(expr, Comparison):
        rhs: Expr | float | int = expr.rhs.subs(mapping) if isinstance(expr.rhs, Expr) else expr.rhs
        return Comparison(lhs=expr.lhs.subs(mapping), op=expr.op, rhs=rhs)
    if isinstance(expr, Expr):
        return expr.subs(mapping)
    return Const(float(expr))


def _build_name_mapping(var_mapping: VarRemap) -> Dict[str, str]:
    """
    Build a name-to-name remapping from a generic variable substitution map.

    :param var_mapping: Mapping used to substitute symbolic variables.
    :return: Mapping from old variable names to new variable names.
    """
    mapping: Dict[str, str] = dict()
    for old, new in var_mapping.items():
        if isinstance(old, Var) and isinstance(new, Var):
            old_var: Var = old
            new_var: Var = new
            mapping[old_var.name] = new_var.name
        elif isinstance(old, str) and isinstance(new, Var):
            new_var = new
            mapping[old] = new_var.name
    return mapping


def _get_expr_like_field(data: ProceduralLogicData, key: str) -> ProceduralLogicData:
    """
    Return one serialized procedural-expression field as a dictionary.

    :param data: Serialized procedural logic dictionary.
    :param key: Field name containing one serialized expression.
    :return: Serialized expression dictionary.
    """
    field_data: ProceduralLogicData = data[key]
    return field_data


def _coerce_var_name(var_or_name: Var | str) -> str:
    """
    Normalize a variable reference to its string name.

    :param var_or_name: Symbolic variable or plain string name.
    :return: Variable name.
    """
    if isinstance(var_or_name, Var):
        symbolic_var: Var = var_or_name
        return symbolic_var.name
    else:
        name_text: str = str(var_or_name)
        return name_text


def _append_history_sample(history: List[Tuple[float, float]], sample_time: float, value: float) -> None:
    """
    Append or overwrite one time-stamped sample in a monotonic history buffer.

    :param history: In-place sample buffer.
    :param sample_time: Accepted sample time.
    :param value: Sampled value.
    :return: None.
    """
    if len(history) > 0 and abs(history[-1][0] - sample_time) <= 1e-12:
        history[-1] = (sample_time, value)
    else:
        history.append((sample_time, value))


def _history_sample_at_or_before(history: List[Tuple[float, float]], target_time: float) -> float:
    """
    Return the latest history sample not newer than ``target_time``.

    :param history: Monotonic time-stamped samples.
    :param target_time: Requested delayed lookup time.
    :return: Sampled value.
    """
    if len(history) == 0:
        return 0.0

    selected_value: float = history[0][1]
    for sample_time, sample_value in history:
        if sample_time <= target_time:
            selected_value = sample_value
        else:
            break
    return selected_value


def _prune_history_keep_last_before(history: List[Tuple[float, float]], cutoff_time: float) -> None:
    """
    Drop stale history samples while keeping the last one before ``cutoff_time``.

    :param history: Monotonic time-stamped samples.
    :param cutoff_time: Oldest time worth keeping for future delayed lookups.
    :return: None.
    """
    if len(history) <= 2:
        return

    keep_from: int = 0
    for idx, (sample_time, _sample_value) in enumerate(history):
        if sample_time <= cutoff_time:
            keep_from = idx
        else:
            break

    if keep_from > 0:
        del history[:keep_from]


def _bool_expr(expr: Expr | Comparison | float | int) -> Expr:
    """
    Convert a boolean-like procedural input into a symbolic expression.

    :param expr: Comparison, expression, or scalar encoded as 0/1.
    :return: Symbolic expression representing the boolean quantity.
    """
    if isinstance(expr, Comparison):
        comparison_expr: Comparison = expr
        return comparison_expr.to_expression()
    elif isinstance(expr, Expr):
        symbolic_expr: Expr = expr
        return symbolic_expr
    else:
        scalar_value: float = float(expr)
        return Const(scalar_value)


def _value_expr(expr: Expr | Comparison | float | int) -> Expr:
    """
    Convert a procedural scalar input into a symbolic expression.

    :param expr: Comparison, expression, or scalar value.
    :return: Symbolic expression representing the input value.
    """
    if isinstance(expr, Comparison):
        comparison_expr: Comparison = expr
        return comparison_expr.to_expression()
    elif isinstance(expr, Expr):
        symbolic_expr: Expr = expr
        return symbolic_expr
    else:
        scalar_value: float = float(expr)
        return Const(scalar_value)


def bool_and(*args: Expr | Comparison | float | int) -> Expr:
    """
    Build the boolean AND of one or more procedural expressions.

    :param args: Boolean-like expressions encoded as 0/1 values.
    :return: Expression equal to 1.0 only when all inputs are true.
    """
    if len(args) == 0:
        return Const(1.0)

    result = _bool_expr(args[0])
    for arg in args[1:]:
        result = result * _bool_expr(arg)
    return result


def bool_or(*args: Expr | Comparison | float | int) -> Expr:
    """
    Build the boolean OR of one or more procedural expressions.

    :param args: Boolean-like expressions encoded as 0/1 values.
    :return: Expression equal to 1.0 when at least one input is true.
    """
    if len(args) == 0:
        return Const(0.0)

    result = _bool_expr(args[0])
    for arg in args[1:]:
        arg_expr = _bool_expr(arg)
        result = Const(1.0) - (Const(1.0) - result) * (Const(1.0) - arg_expr)
    return result


def bool_not(arg: Expr | Comparison | float | int) -> Expr:
    """
    Build the boolean NOT of one procedural expression.

    :param arg: Boolean-like expression encoded as 0/1.
    :return: Expression equal to 1.0 when the input is false.
    """
    return Const(1.0) - _bool_expr(arg)


def bool_nand(*args: Expr | Comparison | float | int) -> Expr:
    """
    Build the boolean NAND of one or more procedural expressions.

    :param args: Boolean-like expressions encoded as 0/1 values.
    :return: Expression equal to the negated AND of the inputs.
    """
    return bool_not(bool_and(*args))


def bool_nor(*args: Expr | Comparison | float | int) -> Expr:
    """
    Build the boolean NOR of one or more procedural expressions.

    :param args: Boolean-like expressions encoded as 0/1 values.
    :return: Expression equal to the negated OR of the inputs.
    """
    return bool_not(bool_or(*args))


def bool_eor(left: Expr | Comparison | float | int, right: Expr | Comparison | float | int) -> Expr:
    """
    Build the exclusive-OR of two procedural expressions.

    :param left: Left boolean-like expression.
    :param right: Right boolean-like expression.
    :return: Expression equal to 1.0 only when exactly one input is true.
    """
    left_expr = _bool_expr(left)
    right_expr = _bool_expr(right)
    return left_expr + right_expr - Const(2.0) * left_expr * right_expr


def select(
    boolexpr: Expr | Comparison | float | int,
    when_true: Expr | Comparison | float | int,
    when_false: Expr | Comparison | float | int,
) -> Expr:
    """
    Reject equation-level select usage in the public procedural API.

    :param boolexpr: Switching condition.
    :param when_true: Value chosen for the true branch.
    :param when_false: Value chosen for the false branch.
    :return: Never returns because public equation-level selection is blocked.
    """
    _unused = (boolexpr, when_true, when_false)
    raise RuntimeError(
        "`select()` is blocked in equation expressions. Move the switching decision to "
        "`block.procedural_logic` and consume the resulting mode/flag inside the equations."
    )


def ifelse(
    boolexpr: Expr | Comparison | float | int,
    when_true: Expr | Comparison | float | int,
    when_false: Expr | Comparison | float | int,
) -> Expr:
    """
    Reject equation-level ifelse usage in the public procedural API.

    :param boolexpr: Switching condition.
    :param when_true: Value chosen for the true branch.
    :param when_false: Value chosen for the false branch.
    :return: Never returns because public equation-level selection is blocked.
    """
    _unused = (boolexpr, when_true, when_false)
    raise RuntimeError(
        "`ifelse()` is blocked in equation expressions. Move the switching decision to "
        "`block.procedural_logic` and consume the resulting mode/flag inside the equations."
    )


class ProceduralLogicBase:
    """
    Base class for procedural logic objects attached to symbolic blocks.

    Procedural logic is evaluated outside the compiled residual kernels and is intended
    to drive runtime modes, retained flags, timers, or event scheduling in a structured way.
    """

    __slots__ = [
        "name",
        "_problem",
        "_sample_time",
        "_expr_plan_cache",
        "_comparison_expr_cache",
        "_expr_compiled_cache",
    ]
    logic_tpe = ProceduralLogicType.Base

    def __init__(self, name: str = "") -> None:
        self.name = name
        self._problem: Optional[EmtProblemTemplate] = None
        self._sample_time: Optional[float] = None
        self._expr_plan_cache: Dict[int, List[Tuple[int, int, int]]] = dict()
        self._comparison_expr_cache: Dict[int, Expr] = dict()
        self._expr_compiled_cache: Dict[int, Any] = dict()

    def bind(self, problem: EmtProblemTemplate) -> None:
        """
        Bind the logic to a concrete EMT problem.

        :param problem: EMT problem owning the block and variable maps.
        :return: None
        """
        self._problem = problem
        self._sample_time = None
        self._expr_plan_cache = dict()
        self._comparison_expr_cache = dict()
        self._expr_compiled_cache = dict()

    def _get_normalized_expr(self, expr: Expr | Comparison) -> Expr:
        if isinstance(expr, Comparison):
            key = id(expr)
            if key in self._comparison_expr_cache:
                return self._comparison_expr_cache[key]

            expr_eval = expr.to_expression()
            self._comparison_expr_cache[key] = expr_eval
            return expr_eval

        return expr

    def _build_expr_plan(self, expr_eval: Expr, problem: EmtProblemTemplate) -> List[Tuple[int, int, int]]:
        # Plan tuple layout: (uid, source_kind, source_idx)
        # source_kind: 0 -> x/state-algebraic vars, 1 -> runtime params, 2 -> const params, 3 -> time
        refs_by_uid: Dict[int, Tuple[int, int, int]] = dict()

        for var in expr_eval.get_vars():
            if var.name in {"time", "glob_time"} or var.uid == problem.glob_time.uid:
                refs_by_uid[var.uid] = (var.uid, 3, -1)
                continue

            idx_var = problem.uid2idx_vars.get(var.uid, None)
            if idx_var is not None:
                refs_by_uid[var.uid] = (var.uid, 0, int(idx_var))
                continue

            idx_runtime = problem.uid2idx_event_params.get(var.uid, None)
            if idx_runtime is not None:
                refs_by_uid[var.uid] = (var.uid, 1, int(idx_runtime))
                continue

            idx_const = problem.uid2idx_params.get(var.uid, None)
            if idx_const is not None:
                refs_by_uid[var.uid] = (var.uid, 2, int(idx_const))
                continue

            raise KeyError(f"Unknown procedural variable '{var.name}'")

        return list(refs_by_uid.values())

    def _get_expr_plan(self, expr_eval: Expr, problem: EmtProblemTemplate) -> List[Tuple[int, int, int]]:
        key = id(expr_eval)
        if key in self._expr_plan_cache:
            return self._expr_plan_cache[key]

        plan = self._build_expr_plan(expr_eval, problem)
        self._expr_plan_cache[key] = plan
        return plan

    @staticmethod
    def _heaviside_numeric(x: float) -> float:
        return 1.0 if x > 0.0 else 0.0

    def _report_expr_compile_failure(self, expr_eval: Expr, exc: Exception) -> None:
        if os.getenv("VERAGRID_PROCLOGIC_DEBUG_COMPILE", "0") != "1":
            return

        logic_name = self.name if self.name else self.__class__.__name__
        print(
            "[proc-logic] Expression compile fallback "
            f"(logic='{logic_name}', expr_type='{type(expr_eval).__name__}'): {exc}"
        )

    def _get_compiled_expr_fn(self, expr_eval: Expr, problem: EmtProblemTemplate):
        key = id(expr_eval)
        cached = self._expr_compiled_cache.get(key, None)
        if cached is not None:
            return cached

        plan = self._get_expr_plan(expr_eval=expr_eval, problem=problem)
        compiler_names_dict: Dict[int, str] = dict()
        for pos, (uid, _source_kind, _source_idx) in enumerate(plan):
            compiler_names_dict[uid] = f"_a[{pos}]"

        try:
            expr_code = expression2numba(expr_eval, compiler_names_dict)
            fn_globals = {
                "np": np,
                "_heaviside": self._heaviside_numeric,
            }
            fn_locals: Dict[str, Any] = dict()
            exec(f"def _compiled_proc_expr(_a):\n    return {expr_code}", fn_globals, fn_locals)
            fn = fn_locals["_compiled_proc_expr"]
            self._expr_compiled_cache[key] = (plan, fn)
        except Exception as exc:
            self._report_expr_compile_failure(expr_eval=expr_eval, exc=exc)
            self._expr_compiled_cache[key] = (plan, None)

        return self._expr_compiled_cache[key]

    def update(self, t: float, x: Vec, params: Vec) -> None:
        """
        Update mode or event parameters before the Newton step.

        :param t: Current solver time.
        :param x: Current accepted state.
        :param params: Runtime parameter vector to mutate in place.
        :return: None
        """
        _unused = (t, x, params)

    def get_next_forced_event_time(self, t_prev: float, t_target: float) -> Optional[float]:
        """
        Return the next exact event time inside the interval if known.

        :param t_prev: Previous solver time.
        :param t_target: Nominal target time.
        :return: Event time or None.
        """
        self._sample_time = float(t_prev)
        _unused = t_target
        return None

    def remap(self, var_mapping: VarRemap) -> "ProceduralLogicBase":
        """
        Clone one logic entry under a variable remapping.

        :param var_mapping: Variable substitution map.
        :return: Remapped procedural logic entry.
        """
        _unused = var_mapping
        return build_procedural_logic_entry(procedural_logic_entry_to_dict(self))

    def _get_problem(self) -> EmtProblemTemplate:
        """
        Return the bound EMT problem.

        :return: Bound EMT problem.
        """
        if self._problem is None:
            raise RuntimeError("Procedural logic must be bound to an EMT problem before runtime evaluation")
        return self._problem

    def _get_sample_time(self, t: float) -> float:
        """
        Return the accepted sample time associated with the current update.

        :param t: Current solver time.
        :return: Accepted sample time.
        """
        return float(t if self._sample_time is None else self._sample_time)

    def _eval_numeric(self, expr: Expr | Comparison, t: float, x: Vec, params: Vec) -> float:
        """
        Evaluate a procedural expression against the accepted EMT state.

        :param expr: Expression or comparison to evaluate.
        :param t: Current solver time.
        :param x: Accepted state vector.
        :param params: Runtime parameter vector.
        :return: Numeric value of the expression.
        """
        # The evaluator always resolves symbols against the accepted state, not the Newton iterate.
        problem = self._get_problem()
        sample_time = self._get_sample_time(t)

        if isinstance(expr, (float, int)):
            return float(expr)

        expr_eval: Expr = self._get_normalized_expr(expr)

        if isinstance(expr_eval, Const):
            return 0.0 if expr_eval.value is None else float(expr_eval.value)

        if isinstance(expr_eval, Var):
            # Fast-path single variables because they dominate the procedural runtime workload.
            if expr_eval.name in {"time", "glob_time"}:
                return sample_time

            idx_var = problem.uid2idx_vars.get(expr_eval.uid, None)
            if idx_var is not None:
                return float(x[idx_var])

            idx_runtime = problem.uid2idx_event_params.get(expr_eval.uid, None)
            if idx_runtime is not None:
                return float(params[idx_runtime])

            idx_const = problem.uid2idx_params.get(expr_eval.uid, None)
            if idx_const is not None:
                n_runtime = problem.get_variable_parameter_number()
                if len(params) >= n_runtime + len(problem.get_parameters_values()):
                    return float(params[n_runtime + idx_const])
                return float(problem.get_parameters_values()[idx_const].value)

            raise KeyError(f"Unknown procedural variable '{expr_eval.name}'")

        plan, compiled_fn = self._get_compiled_expr_fn(expr_eval=expr_eval, problem=problem)
        n_runtime = problem.get_variable_parameter_number()
        const_values = problem.get_parameters_values()
        params_has_consts = len(params) >= n_runtime + len(const_values)

        compiled_input = np.empty(len(plan), dtype=np.float64)

        for pos, (_uid, source_kind, source_idx) in enumerate(plan):
            if source_kind == 0:
                compiled_input[pos] = float(x[source_idx])
            elif source_kind == 1:
                compiled_input[pos] = float(params[source_idx])
            elif source_kind == 2:
                if params_has_consts:
                    compiled_input[pos] = float(params[n_runtime + source_idx])
                else:
                    compiled_input[pos] = float(const_values[source_idx].value)
            else:
                compiled_input[pos] = sample_time

        if compiled_fn is not None:
            return float(compiled_fn(compiled_input))

        uid_bindings: Dict[int, float] = dict()
        for pos, (uid, _source_kind, _source_idx) in enumerate(plan):
            uid_bindings[uid] = float(compiled_input[pos])

        uid_bindings[problem.glob_time.uid] = sample_time

        return float(expr_eval.eval_uid(uid_bindings))

    def _eval_bool(self, expr: Expr | Comparison, t: float, x: Vec, params: Vec) -> bool:
        """
        Evaluate one procedural condition using the accepted EMT state.

        :param expr: Expression or comparison to evaluate.
        :param t: Current solver time.
        :param x: Accepted state vector.
        :param params: Runtime parameter vector.
        :return: True when the expression evaluates above 0.5.
        """
        return self._eval_numeric(expr, t, x, params) > 0.5

    def _build_numeric_evaluator(self, expr: Expr | Comparison | float | int | bool) -> Callable[[float, Vec, Vec], float]:
        problem = self._get_problem()

        if isinstance(expr, (float, int, bool)):
            const_value = float(expr)
            return lambda _t, _x, _p: const_value

        expr_eval: Expr = self._get_normalized_expr(expr)

        if isinstance(expr_eval, Const):
            const_value = 0.0 if expr_eval.value is None else float(expr_eval.value)
            return lambda _t, _x, _p: const_value

        if isinstance(expr_eval, Var):
            if expr_eval.name in {"time", "glob_time"}:
                return lambda t, _x, _p: self._get_sample_time(t)

            idx_var = problem.uid2idx_vars.get(expr_eval.uid, None)
            if idx_var is not None:
                i = int(idx_var)
                return lambda _t, x, _p: float(x[i])

            idx_runtime = problem.uid2idx_event_params.get(expr_eval.uid, None)
            if idx_runtime is not None:
                i = int(idx_runtime)
                return lambda _t, _x, p: float(p[i])

            idx_const = problem.uid2idx_params.get(expr_eval.uid, None)
            if idx_const is not None:
                i = int(idx_const)
                n_runtime = problem.get_variable_parameter_number()
                const_values = problem.get_parameters_values()

                def eval_const(_t, _x, p):
                    if len(p) >= n_runtime + len(const_values):
                        return float(p[n_runtime + i])
                    return float(const_values[i].value)

                return eval_const

            raise KeyError(f"Unknown procedural variable '{expr_eval.name}'")

        plan, compiled_fn = self._get_compiled_expr_fn(expr_eval=expr_eval, problem=problem)
        n_runtime = problem.get_variable_parameter_number()
        const_values = problem.get_parameters_values()

        if compiled_fn is None:
            return lambda t, x, p: self._eval_numeric(expr_eval, t, x, p)

        compiled_input = np.empty(len(plan), dtype=np.float64)

        def eval_compiled(t, x, p):
            sample_time = self._get_sample_time(t)
            params_has_consts = len(p) >= n_runtime + len(const_values)

            for pos, (_uid, source_kind, source_idx) in enumerate(plan):
                if source_kind == 0:
                    compiled_input[pos] = float(x[source_idx])
                elif source_kind == 1:
                    compiled_input[pos] = float(p[source_idx])
                elif source_kind == 2:
                    if params_has_consts:
                        compiled_input[pos] = float(p[n_runtime + source_idx])
                    else:
                        compiled_input[pos] = float(const_values[source_idx].value)
                else:
                    compiled_input[pos] = sample_time

            return float(compiled_fn(compiled_input))

        return eval_compiled


class FixedSampleLogic(ProceduralLogicBase):
    """
    Retain the initial truth value of one condition in a runtime mode variable.
    """

    __slots__ = ["output_var_name", "condition_expr", "output_idx", "initialized"]
    logic_tpe = ProceduralLogicType.FixedSample

    def __init__(self, output_var_name: str, condition_expr: Expr | Comparison, name: str = "") -> None:
        super().__init__(name=name)
        self.output_var_name = output_var_name
        self.condition_expr = condition_expr
        self.output_idx = -1
        self.initialized = False

    def bind(self, problem: EmtProblemTemplate) -> None:
        """
        Resolve the runtime output slot for this logic entry.

        :param problem: Bound EMT problem.
        :return: None
        """
        super().bind(problem)
        output_var = _find_var_by_name(problem.sys_block, self.output_var_name)
        self.output_idx = int(problem.uid2idx_event_params[output_var.uid])
        self.initialized = False

    def update(self, t: float, x: Vec, params: Vec) -> None:
        """
        Sample the condition once and keep it fixed afterwards.

        :param t: Current solver time.
        :param x: Accepted state vector.
        :param params: Runtime parameter vector.
        :return: None
        """
        if self.initialized:
            return

        params[self.output_idx] = 1.0 if self._eval_bool(self.condition_expr, t, x, params) else 0.0
        self.initialized = True

    def remap(self, var_mapping: VarRemap) -> "FixedSampleLogic":
        """
        Clone the logic under a variable remapping.

        :param var_mapping: Variable substitution map.
        :return: Remapped fixed-sample logic.
        """
        name_mapping = _build_name_mapping(var_mapping)
        return FixedSampleLogic(
            output_var_name=name_mapping.get(self.output_var_name, self.output_var_name),
            condition_expr=_subs_expr_like(self.condition_expr, var_mapping),
            name=self.name,
        )


class SampledValueLogic(ProceduralLogicBase):
    """
    Sample one expression at each accepted step and store it in a runtime mode variable.
    """

    __slots__ = ["output_var_name", "source_expr", "output_idx", "_source_eval"]
    logic_tpe = ProceduralLogicType.SampledValue

    def __init__(self, output_var_name: str, source_expr: Expr | Comparison, name: str = "") -> None:
        super().__init__(name=name)
        self.output_var_name = output_var_name
        self.source_expr = source_expr
        self.output_idx = -1
        self._source_eval: Callable[[float, Vec, Vec], float] | None = None

    def bind(self, problem: EmtProblemTemplate) -> None:
        """
        Resolve the runtime output slot for this sampled value.

        :param problem: Bound EMT problem.
        :return: None
        """
        super().bind(problem)
        output_var = _find_var_by_name(problem.sys_block, self.output_var_name)
        self.output_idx = int(problem.uid2idx_event_params[output_var.uid])
        self._source_eval = self._build_numeric_evaluator(self.source_expr)

    def update(self, t: float, x: Vec, params: Vec) -> None:
        """
        Refresh the sampled value using the accepted state.

        :param t: Current solver time.
        :param x: Accepted state vector.
        :param params: Runtime parameter vector.
        :return: None
        """
        if self._source_eval is None:
            self._source_eval = self._build_numeric_evaluator(self.source_expr)

        params[self.output_idx] = self._source_eval(t, x, params)

    def remap(self, var_mapping: VarRemap) -> "SampledValueLogic":
        """
        Clone the logic under a variable remapping.

        :param var_mapping: Variable substitution map.
        :return: Remapped sampled-value logic.
        """
        name_mapping = _build_name_mapping(var_mapping)
        return SampledValueLogic(
            output_var_name=name_mapping.get(self.output_var_name, self.output_var_name),
            source_expr=_subs_expr_like(self.source_expr, var_mapping),
            name=self.name,
        )


class HardSaturationLogic(ProceduralLogicBase):
    """
    Sample one input and apply hard saturation to a runtime mode variable.
    """

    __slots__ = ["output_var_name", "u_expr", "u_min_expr", "u_max_expr", "output_idx", "_u_eval", "_u_min_eval", "_u_max_eval"]
    logic_tpe = ProceduralLogicType.HardSaturation

    def __init__(
        self,
        output_var_name: str,
        u_expr: Expr | Comparison,
        u_min_expr: Expr | Comparison,
        u_max_expr: Expr | Comparison,
        name: str = "",
    ) -> None:
        super().__init__(name=name)
        self.output_var_name = output_var_name
        self.u_expr = u_expr
        self.u_min_expr = u_min_expr
        self.u_max_expr = u_max_expr
        self.output_idx = -1
        self._u_eval: Callable[[float, Vec, Vec], float] | None = None
        self._u_min_eval: Callable[[float, Vec, Vec], float] | None = None
        self._u_max_eval: Callable[[float, Vec, Vec], float] | None = None

    def bind(self, problem: EmtProblemTemplate) -> None:
        super().bind(problem)
        output_var = _find_var_by_name(problem.sys_block, self.output_var_name)
        self.output_idx = int(problem.uid2idx_event_params[output_var.uid])
        self._u_eval = self._build_numeric_evaluator(self.u_expr)
        self._u_min_eval = self._build_numeric_evaluator(self.u_min_expr)
        self._u_max_eval = self._build_numeric_evaluator(self.u_max_expr)

    def update(self, t: float, x: Vec, params: Vec) -> None:
        if self._u_eval is None:
            self._u_eval = self._build_numeric_evaluator(self.u_expr)
        if self._u_min_eval is None:
            self._u_min_eval = self._build_numeric_evaluator(self.u_min_expr)
        if self._u_max_eval is None:
            self._u_max_eval = self._build_numeric_evaluator(self.u_max_expr)

        assert self._u_eval is not None
        assert self._u_min_eval is not None
        assert self._u_max_eval is not None

        u_val: float = float(self._u_eval(t, x, params))
        u_min_val: float = float(self._u_min_eval(t, x, params))
        u_max_val: float = float(self._u_max_eval(t, x, params))
        if u_min_val <= u_max_val:
            params[self.output_idx] = min(max(u_val, u_min_val), u_max_val)
        else:
            params[self.output_idx] = min(max(u_val, u_max_val), u_min_val)

    def remap(self, var_mapping: VarRemap) -> "HardSaturationLogic":
        name_mapping = _build_name_mapping(var_mapping)
        return HardSaturationLogic(
            output_var_name=name_mapping.get(self.output_var_name, self.output_var_name),
            u_expr=_subs_expr_like(self.u_expr, var_mapping),
            u_min_expr=_subs_expr_like(self.u_min_expr, var_mapping),
            u_max_expr=_subs_expr_like(self.u_max_expr, var_mapping),
            name=self.name,
        )


class TimeDelayLogic(ProceduralLogicBase):
    """
    Sample one input and expose its delayed value through a runtime mode variable.
    """

    __slots__ = ["output_var_name", "source_expr", "delay_expr", "output_idx", "history"]
    logic_tpe = ProceduralLogicType.TimeDelay

    def __init__(
        self,
        output_var_name: str,
        source_expr: Expr | Comparison | float | int | bool,
        delay_expr: Expr | Comparison | float | int | bool,
        name: str = "",
    ) -> None:
        super().__init__(name=name)
        self.output_var_name = output_var_name
        self.source_expr = source_expr
        self.delay_expr = delay_expr
        self.output_idx = -1
        self.history: List[Tuple[float, float]] = list()

    def bind(self, problem: EmtProblemTemplate) -> None:
        super().bind(problem)
        output_var = _find_var_by_name(problem.sys_block, self.output_var_name)
        self.output_idx = int(problem.uid2idx_event_params[output_var.uid])
        self.history = list()

    def update(self, t: float, x: Vec, params: Vec) -> None:
        sample_time = self._get_sample_time(t)
        source_value = self._eval_numeric(self.source_expr, t, x, params)
        delay_value = max(0.0, self._eval_numeric(self.delay_expr, t, x, params))

        _append_history_sample(self.history, sample_time, source_value)

        if delay_value <= 0.0:
            params[self.output_idx] = source_value
            return

        target_time = sample_time - delay_value
        params[self.output_idx] = _history_sample_at_or_before(self.history, target_time)
        _prune_history_keep_last_before(self.history, target_time)

    def remap(self, var_mapping: VarRemap) -> "TimeDelayLogic":
        name_mapping = _build_name_mapping(var_mapping)
        return TimeDelayLogic(
            output_var_name=name_mapping.get(self.output_var_name, self.output_var_name),
            source_expr=_subs_expr_like(self.source_expr, var_mapping),
            delay_expr=_subs_expr_like(self.delay_expr, var_mapping),
            name=self.name,
        )


class MovingAverageLogic(ProceduralLogicBase):
    """
    Buffer-based moving average with optional delay before the averaging window.
    """

    __slots__ = ["output_var_name", "source_expr", "delay_expr", "window_expr", "output_idx", "history"]
    logic_tpe = ProceduralLogicType.MovingAverage

    def __init__(
        self,
        output_var_name: str,
        source_expr: Expr | Comparison | float | int | bool,
        delay_expr: Expr | Comparison | float | int | bool,
        window_expr: Expr | Comparison | float | int | bool,
        name: str = "",
    ) -> None:
        super().__init__(name=name)
        self.output_var_name = output_var_name
        self.source_expr = source_expr
        self.delay_expr = delay_expr
        self.window_expr = window_expr
        self.output_idx = -1
        self.history: List[Tuple[float, float]] = list()

    def bind(self, problem: EmtProblemTemplate) -> None:
        super().bind(problem)
        output_var = _find_var_by_name(problem.sys_block, self.output_var_name)
        self.output_idx = int(problem.uid2idx_event_params[output_var.uid])
        self.history = list()

    def update(self, t: float, x: Vec, params: Vec) -> None:
        sample_time = self._get_sample_time(t)
        source_value = self._eval_numeric(self.source_expr, t, x, params)
        delay_value = max(0.0, self._eval_numeric(self.delay_expr, t, x, params))
        window_value = max(0.0, self._eval_numeric(self.window_expr, t, x, params))

        _append_history_sample(self.history, sample_time, source_value)

        target_end = sample_time - delay_value
        if window_value <= 0.0:
            params[self.output_idx] = _history_sample_at_or_before(self.history, target_end)
            _prune_history_keep_last_before(self.history, target_end)
            return

        target_start = target_end - window_value
        values_in_window: List[float] = [value for ts, value in self.history if target_start <= ts <= target_end]
        if len(values_in_window) == 0:
            params[self.output_idx] = _history_sample_at_or_before(self.history, target_end)
        else:
            params[self.output_idx] = float(sum(values_in_window) / len(values_in_window))
        _prune_history_keep_last_before(self.history, target_start)

    def remap(self, var_mapping: VarRemap) -> "MovingAverageLogic":
        name_mapping = _build_name_mapping(var_mapping)
        return MovingAverageLogic(
            output_var_name=name_mapping.get(self.output_var_name, self.output_var_name),
            source_expr=_subs_expr_like(self.source_expr, var_mapping),
            delay_expr=_subs_expr_like(self.delay_expr, var_mapping),
            window_expr=_subs_expr_like(self.window_expr, var_mapping),
            name=self.name,
        )


class GradientLimiterLogic(ProceduralLogicBase):
    """
    Clamp the rate of change of one procedural value between lower and upper slopes.
    """

    __slots__ = ["output_var_name", "source_expr", "lower_rate_expr", "upper_rate_expr", "output_idx", "last_time", "held_value", "initialized"]
    logic_tpe = ProceduralLogicType.GradientLimiter

    def __init__(
        self,
        output_var_name: str,
        source_expr: Expr | Comparison | float | int | bool,
        lower_rate_expr: Expr | Comparison | float | int | bool,
        upper_rate_expr: Expr | Comparison | float | int | bool,
        name: str = "",
    ) -> None:
        super().__init__(name=name)
        self.output_var_name = output_var_name
        self.source_expr = source_expr
        self.lower_rate_expr = lower_rate_expr
        self.upper_rate_expr = upper_rate_expr
        self.output_idx = -1
        self.last_time: Optional[float] = None
        self.held_value = 0.0
        self.initialized = False

    def bind(self, problem: EmtProblemTemplate) -> None:
        super().bind(problem)
        output_var = _find_var_by_name(problem.sys_block, self.output_var_name)
        self.output_idx = int(problem.uid2idx_event_params[output_var.uid])
        self.last_time = None
        self.held_value = 0.0
        self.initialized = False

    def update(self, t: float, x: Vec, params: Vec) -> None:
        sample_time = self._get_sample_time(t)
        source_value = self._eval_numeric(self.source_expr, t, x, params)
        lower_rate = self._eval_numeric(self.lower_rate_expr, t, x, params)
        upper_rate = self._eval_numeric(self.upper_rate_expr, t, x, params)

        if not self.initialized or self.last_time is None:
            self.held_value = source_value
            self.last_time = sample_time
            self.initialized = True
            params[self.output_idx] = self.held_value
            return

        dt = max(0.0, sample_time - self.last_time)
        lower_bound = self.held_value + lower_rate * dt
        upper_bound = self.held_value + upper_rate * dt
        if lower_bound > upper_bound:
            lower_bound, upper_bound = upper_bound, lower_bound

        self.held_value = min(max(source_value, lower_bound), upper_bound)
        self.last_time = sample_time
        params[self.output_idx] = self.held_value

    def remap(self, var_mapping: VarRemap) -> "GradientLimiterLogic":
        name_mapping = _build_name_mapping(var_mapping)
        return GradientLimiterLogic(
            output_var_name=name_mapping.get(self.output_var_name, self.output_var_name),
            source_expr=_subs_expr_like(self.source_expr, var_mapping),
            lower_rate_expr=_subs_expr_like(self.lower_rate_expr, var_mapping),
            upper_rate_expr=_subs_expr_like(self.upper_rate_expr, var_mapping),
            name=self.name,
        )


class FlipFlopLogic(ProceduralLogicBase):
    """
    Store a binary set/reset latch in a runtime mode variable.
    """

    __slots__ = ["output_var_name", "set_expr", "reset_expr", "output_idx", "state", "initialized"]
    logic_tpe = ProceduralLogicType.FlipFlop

    def __init__(
        self,
        output_var_name: str,
        set_expr: Expr | Comparison,
        reset_expr: Expr | Comparison,
        name: str = "",
    ) -> None:
        super().__init__(name=name)
        self.output_var_name = output_var_name
        self.set_expr = set_expr
        self.reset_expr = reset_expr
        self.output_idx = -1
        self.state = 0.0
        self.initialized = False

    def bind(self, problem: EmtProblemTemplate) -> None:
        """
        Resolve the runtime output slot for the latch state.

        :param problem: Bound EMT problem.
        :return: None
        """
        super().bind(problem)
        output_var = _find_var_by_name(problem.sys_block, self.output_var_name)
        self.output_idx = int(problem.uid2idx_event_params[output_var.uid])
        self.state = 0.0
        self.initialized = False

    def update(self, t: float, x: Vec, params: Vec) -> None:
        """
        Apply set/reset semantics and write the resulting latch state.

        :param t: Current solver time.
        :param x: Accepted state vector.
        :param params: Runtime parameter vector.
        :return: None
        """
        # First evaluate the two boolean inputs at the accepted sample state.
        set_on = self._eval_bool(self.set_expr, t, x, params)
        reset_on = self._eval_bool(self.reset_expr, t, x, params)

        if not self.initialized:
            # The initial state follows the SET input, but conflicting SET/RESET is invalid.
            if set_on and reset_on:
                raise ValueError(f"flipflop '{self.name or self.output_var_name}' cannot initialize with set=1 and reset=1")
            self.state = 1.0 if set_on else 0.0
            self.initialized = True
        elif set_on and not reset_on:
            # A pure SET edge drives the latched state high.
            self.state = 1.0
        elif (not set_on) and reset_on:
            # A pure RESET edge drives the latched state low.
            self.state = 0.0

        # The runtime parameter vector always exposes the latest latch state.
        params[self.output_idx] = self.state

    def remap(self, var_mapping: VarRemap) -> "FlipFlopLogic":
        """
        Clone the logic under a variable remapping.

        :param var_mapping: Variable substitution map.
        :return: Remapped flip-flop logic.
        """
        name_mapping = _build_name_mapping(var_mapping)
        return FlipFlopLogic(
            output_var_name=name_mapping.get(self.output_var_name, self.output_var_name),
            set_expr=_subs_expr_like(self.set_expr, var_mapping),
            reset_expr=_subs_expr_like(self.reset_expr, var_mapping),
            name=self.name,
        )


class AnalogFlipFlopLogic(ProceduralLogicBase):
    """
    Store an analog value when a set/reset latch enters the high state.
    """

    __slots__ = [
        "output_var_name",
        "input_expr",
        "set_expr",
        "reset_expr",
        "output_idx",
        "state",
        "initialized",
        "held_value",
    ]
    logic_tpe = ProceduralLogicType.AnalogFlipFlop

    def __init__(
        self,
        output_var_name: str,
        input_expr: Expr | Comparison,
        set_expr: Expr | Comparison,
        reset_expr: Expr | Comparison,
        name: str = "",
    ) -> None:
        super().__init__(name=name)
        self.output_var_name = output_var_name
        self.input_expr = input_expr
        self.set_expr = set_expr
        self.reset_expr = reset_expr
        self.output_idx = -1
        self.state = 0.0
        self.initialized = False
        self.held_value = 0.0

    def bind(self, problem: EmtProblemTemplate) -> None:
        """
        Resolve the runtime output slot and reset the analog latch state.

        :param problem: Bound EMT problem.
        :return: None
        """
        super().bind(problem)
        output_var = _find_var_by_name(problem.sys_block, self.output_var_name)
        self.output_idx = int(problem.uid2idx_event_params[output_var.uid])
        self.state = 0.0
        self.initialized = False
        self.held_value = 0.0

    def update(self, t: float, x: Vec, params: Vec) -> None:
        """
        Apply analog set/reset semantics and update the held value.

        :param t: Current solver time.
        :param x: Accepted state vector.
        :param params: Runtime parameter vector.
        :return: None
        """
        # Evaluate the analog input and the set/reset conditions first.
        input_value = self._eval_numeric(self.input_expr, t, x, params)
        set_on = self._eval_bool(self.set_expr, t, x, params)
        reset_on = self._eval_bool(self.reset_expr, t, x, params)

        if not self.initialized:
            # Initialization captures the current analog value only if the latch starts set.
            if set_on and reset_on:
                raise ValueError(f"aflipflop '{self.name or self.output_var_name}' cannot initialize with set=1 and reset=1")
            self.state = 1.0 if set_on else 0.0
            self.held_value = input_value
            self.initialized = True
        elif set_on and not reset_on and self.state < 0.5:
            # The analog value is captured only on the transition from 0 -> 1.
            self.state = 1.0
            self.held_value = input_value
        elif (not set_on) and reset_on and self.state > 0.5:
            # Reset releases the latch and the output follows the live input again.
            self.state = 0.0

        # Expose the held value when latched high, otherwise expose the live input.
        params[self.output_idx] = self.held_value if self.state > 0.5 else input_value

    def remap(self, var_mapping: VarRemap) -> "AnalogFlipFlopLogic":
        """
        Clone the logic under a variable remapping.

        :param var_mapping: Variable substitution map.
        :return: Remapped analog flip-flop logic.
        """
        name_mapping = _build_name_mapping(var_mapping)
        return AnalogFlipFlopLogic(
            output_var_name=name_mapping.get(self.output_var_name, self.output_var_name),
            input_expr=_subs_expr_like(self.input_expr, var_mapping),
            set_expr=_subs_expr_like(self.set_expr, var_mapping),
            reset_expr=_subs_expr_like(self.reset_expr, var_mapping),
            name=self.name,
        )


class PickupDropoffLogic(ProceduralLogicBase):
    """
    Implement a delayed pickup/dropoff relay with retained binary state.
    """

    __slots__ = [
        "output_var_name",
        "bool_expr",
        "pickup_delay_expr",
        "drop_delay_expr",
        "output_idx",
        "state",
        "initialized",
        "pickup_started_at",
        "drop_started_at",
        "pending_pickup_time",
        "pending_drop_time",
    ]
    logic_tpe = ProceduralLogicType.PickupDropoff

    def __init__(
        self,
        output_var_name: str,
        bool_expr: Expr | Comparison,
        pickup_delay_expr: Expr | Comparison,
        drop_delay_expr: Expr | Comparison,
        name: str = "",
    ) -> None:
        super().__init__(name=name)
        self.output_var_name = output_var_name
        self.bool_expr = bool_expr
        self.pickup_delay_expr = pickup_delay_expr
        self.drop_delay_expr = drop_delay_expr
        self.output_idx = -1
        self.state = 0.0
        self.initialized = False
        self.pickup_started_at: Optional[float] = None
        self.drop_started_at: Optional[float] = None
        self.pending_pickup_time: Optional[float] = None
        self.pending_drop_time: Optional[float] = None

    def bind(self, problem: EmtProblemTemplate) -> None:
        """
        Resolve the runtime output slot and clear the relay timers.

        :param problem: Bound EMT problem.
        :return: None
        """
        super().bind(problem)
        output_var = _find_var_by_name(problem.sys_block, self.output_var_name)
        self.output_idx = int(problem.uid2idx_event_params[output_var.uid])
        self.state = 0.0
        self.initialized = False
        self.pickup_started_at = None
        self.drop_started_at = None
        self.pending_pickup_time = None
        self.pending_drop_time = None

    def get_next_forced_event_time(self, t_prev: float, t_target: float) -> Optional[float]:
        """
        Return the next exact pickup or dropoff event inside one step.

        :param t_prev: Previous solver time.
        :param t_target: Nominal target time.
        :return: First pending relay event in the interval, if any.
        """
        super().get_next_forced_event_time(t_prev, t_target)
        candidates: List[float] = list()
        if self.pending_pickup_time is not None and t_prev < self.pending_pickup_time <= t_target:
            candidates.append(float(self.pending_pickup_time))
        if self.pending_drop_time is not None and t_prev < self.pending_drop_time <= t_target:
            candidates.append(float(self.pending_drop_time))
        if len(candidates) == 0:
            return None
        return min(candidates)

    def _eval_delay(self, expr: Expr | Comparison, t: float, x: Vec, params: Vec) -> float:
        """
        Evaluate one relay delay expression and clamp it to a non-negative value.

        :param expr: Delay expression.
        :param t: Current solver time.
        :param x: Accepted state vector.
        :param params: Runtime parameter vector.
        :return: Non-negative evaluated delay.
        """
        return max(0.0, self._eval_numeric(expr, t, x, params))

    def update(self, t: float, x: Vec, params: Vec) -> None:
        """
        Advance the relay timers and binary state.

        :param t: Current solver time.
        :param x: Accepted state vector.
        :param params: Runtime parameter vector.
        :return: None
        """
        tol = 1.0e-15
        sample_time = self._get_sample_time(t)
        bool_on = self._eval_bool(self.bool_expr, t, x, params)

        if not self.initialized:
            # Initialization can trigger immediate pickup when the delay is zero.
            self.initialized = True
            if bool_on:
                pickup_delay = self._eval_delay(self.pickup_delay_expr, t, x, params)
                if pickup_delay <= tol:
                    self.state = 1.0
                else:
                    self.pickup_started_at = sample_time
                    self.pending_pickup_time = sample_time + pickup_delay

        if self.state < 0.5:
            # While the relay is low, only the pickup path can arm a pending event.
            self.drop_started_at = None
            self.pending_drop_time = None

            if bool_on:
                if self.pickup_started_at is None:
                    self.pickup_started_at = sample_time
                self.pending_pickup_time = self.pickup_started_at + self._eval_delay(self.pickup_delay_expr, t, x, params)
            else:
                self.pickup_started_at = None
                self.pending_pickup_time = None

            if self.pending_pickup_time is not None and t >= (self.pending_pickup_time - tol):
                self.state = 1.0
                self.pickup_started_at = None
                self.pending_pickup_time = None

        else:
            # While the relay is high, only the dropoff path can arm a pending event.
            self.pickup_started_at = None
            self.pending_pickup_time = None

            if not bool_on:
                if self.drop_started_at is None:
                    self.drop_started_at = sample_time
                self.pending_drop_time = self.drop_started_at + self._eval_delay(self.drop_delay_expr, t, x, params)
            else:
                self.drop_started_at = None
                self.pending_drop_time = None

            if self.pending_drop_time is not None and t >= (self.pending_drop_time - tol):
                self.state = 0.0
                self.drop_started_at = None
                self.pending_drop_time = None

        params[self.output_idx] = self.state

    def remap(self, var_mapping: VarRemap) -> "PickupDropoffLogic":
        """
        Clone the logic under a variable remapping.

        :param var_mapping: Variable substitution map.
        :return: Remapped pickup/dropoff logic.
        """
        name_mapping = _build_name_mapping(var_mapping)
        return PickupDropoffLogic(
            output_var_name=name_mapping.get(self.output_var_name, self.output_var_name),
            bool_expr=_subs_expr_like(self.bool_expr, var_mapping),
            pickup_delay_expr=_subs_expr_like(self.pickup_delay_expr, var_mapping),
            drop_delay_expr=_subs_expr_like(self.drop_delay_expr, var_mapping),
            name=self.name,
        )


class ResetOnRisingEdgeLogic(ProceduralLogicBase):
    """
    Apply one value reset on the rising edge of a procedural condition.
    """

    __slots__ = [
        "target_var_name",
        "reset_expr",
        "value_expr",
        "target_state_idx",
        "target_param_idx",
        "initialized",
        "last_reset_high",
    ]
    logic_tpe = ProceduralLogicType.ResetOnRisingEdge

    def __init__(
        self,
        target_var_name: str,
        reset_expr: Expr | Comparison,
        value_expr: Expr | Comparison,
        name: str = "",
    ) -> None:
        super().__init__(name=name)
        self.target_var_name = target_var_name
        self.reset_expr = reset_expr
        self.value_expr = value_expr
        self.target_state_idx = -1
        self.target_param_idx = -1
        self.initialized = False
        self.last_reset_high = False

    def bind(self, problem: EmtProblemTemplate) -> None:
        """
        Resolve whether the reset target is a state variable or a runtime parameter.

        :param problem: Bound EMT problem.
        :return: None
        """
        super().bind(problem)
        target_var = _find_var_by_name(problem.sys_block, self.target_var_name)
        self.target_state_idx = int(problem.uid2idx_vars.get(target_var.uid, -1))
        self.target_param_idx = int(problem.uid2idx_event_params.get(target_var.uid, -1))

        if self.target_state_idx < 0 and self.target_param_idx < 0:
            raise KeyError(f"Reset target '{self.target_var_name}' is not a state/algebraic variable nor a runtime parameter")

        self.initialized = False
        self.last_reset_high = False

    def update(self, t: float, x: Vec, params: Vec) -> None:
        """
        Apply the reset value only on the rising edge of the reset condition.

        :param t: Current solver time.
        :param x: Accepted state vector.
        :param params: Runtime parameter vector.
        :return: None
        """
        reset_high = self._eval_bool(self.reset_expr, t, x, params)

        if not self.initialized:
            self.initialized = True
            self.last_reset_high = reset_high
            return

        if (not self.last_reset_high) and reset_high:
            reset_value = self._eval_numeric(self.value_expr, t, x, params)
            if self.target_state_idx >= 0:
                x[self.target_state_idx] = reset_value
            else:
                params[self.target_param_idx] = reset_value

        self.last_reset_high = reset_high

    def remap(self, var_mapping: VarRemap) -> "ResetOnRisingEdgeLogic":
        """
        Clone the logic under a variable remapping.

        :param var_mapping: Variable substitution map.
        :return: Remapped reset logic.
        """
        name_mapping = _build_name_mapping(var_mapping)
        return ResetOnRisingEdgeLogic(
            target_var_name=name_mapping.get(self.target_var_name, self.target_var_name),
            reset_expr=_subs_expr_like(self.reset_expr, var_mapping),
            value_expr=_subs_expr_like(self.value_expr, var_mapping),
            name=self.name,
        )


def fixed_sample(output: Var | str, when: Expr | Comparison, name: str = "") -> FixedSampleLogic:
    """
    Build a fixed-sample selector that stores a boolean condition at initialization.

    :param output: Runtime mode variable receiving the retained value.
    :param when: Condition sampled at initialization time.
    :param name: Optional logic name.
    :return: Fixed-sample procedural logic entry.
    """
    output_name = _coerce_var_name(output)
    return FixedSampleLogic(
        output_var_name=output_name,
        condition_expr=when,
        name=output_name if name == "" else name,
    )


def selfix(boolexpr: Expr | Comparison, output: Var | str, name: str = "") -> FixedSampleLogic:
    """
    Build the procedural equivalent of PowerFactory ``selfix``.

    :param boolexpr: Condition sampled at initialization time.
    :param output: Runtime mode variable receiving the retained value.
    :param name: Optional logic name.
    :return: Fixed-sample procedural logic entry.
    """
    return fixed_sample(output=output, when=boolexpr, name=name)


def selfix_const(boolexpr: Expr | Comparison, output: Var | str, name: str = "") -> FixedSampleLogic:
    """
    Build the procedural equivalent of PowerFactory ``selfix_const``.

    :param boolexpr: Condition sampled at initialization time.
    :param output: Runtime mode variable receiving the retained value.
    :param name: Optional logic name.
    :return: Fixed-sample procedural logic entry.
    """
    return fixed_sample(output=output, when=boolexpr, name=name)


def sampled_value(output: Var | str, source: Expr | Comparison, name: str = "") -> SampledValueLogic:
    """
    Build a sampled runtime value updated outside the Newton residual.

    :param output: Runtime mode variable receiving the sampled value.
    :param source: Source expression to be evaluated at the accepted sample time.
    :param name: Optional logic name.
    :return: Sampled-value procedural logic entry.
    """
    output_name = _coerce_var_name(output)
    return SampledValueLogic(
        output_var_name=output_name,
        source_expr=source,
        name=output_name if name == "" else name,
    )


def hard_saturation(
    output: Var | str,
    u: Expr | Comparison,
    u_min: Expr | Comparison,
    u_max: Expr | Comparison,
    name: str = "",
) -> HardSaturationLogic:
    """
    Build one procedural hard-saturation entry updated outside Newton residuals.

    :param output: Runtime mode variable receiving saturated value.
    :param u: Unsaturated input expression.
    :param u_min: Lower saturation bound.
    :param u_max: Upper saturation bound.
    :param name: Optional logic name.
    :return: Hard-saturation procedural logic entry.
    """
    output_name = _coerce_var_name(output)
    return HardSaturationLogic(
        output_var_name=output_name,
        u_expr=u,
        u_min_expr=u_min,
        u_max_expr=u_max,
        name=output_name if name == "" else name,
    )


def lastvalue(input_expr: Expr | Comparison, output: Var | str, name: str = "") -> SampledValueLogic:
    """
    Build the procedural equivalent of PowerFactory ``lastvalue``.

    :param input_expr: Source expression to be sampled.
    :param output: Runtime mode variable receiving the sampled value.
    :param name: Optional logic name.
    :return: Sampled-value procedural logic entry.
    """
    return sampled_value(output=output, source=input_expr, name=name)


def delay(
    input_expr: Expr | Comparison | float | int | bool,
    T: Expr | Comparison | float | int | bool,
    output: Var | str,
    name: str = "",
) -> TimeDelayLogic:
    """
    Build the procedural equivalent of PowerFactory ``delay``.

    :param input_expr: Source expression to be delayed.
    :param T: Delay in seconds.
    :param output: Runtime mode variable receiving the delayed value.
    :param name: Optional logic name.
    :return: Time-delay procedural logic entry.
    """
    output_name = _coerce_var_name(output)
    return TimeDelayLogic(
        output_var_name=output_name,
        source_expr=input_expr,
        delay_expr=T,
        name=output_name if name == "" else name,
    )


def movingavg(
    input_expr: Expr | Comparison | float | int | bool,
    Tdel: Expr | Comparison | float | int | bool,
    Tlength: Expr | Comparison | float | int | bool,
    output: Var | str,
    name: str = "",
) -> MovingAverageLogic:
    """
    Build the procedural equivalent of PowerFactory ``movingavg``.

    :param input_expr: Source expression to be averaged.
    :param Tdel: Delay before the averaging window.
    :param Tlength: Averaging window length in seconds.
    :param output: Runtime mode variable receiving the averaged value.
    :param name: Optional logic name.
    :return: Moving-average procedural logic entry.
    """
    output_name = _coerce_var_name(output)
    return MovingAverageLogic(
        output_var_name=output_name,
        source_expr=input_expr,
        delay_expr=Tdel,
        window_expr=Tlength,
        name=output_name if name == "" else name,
    )


def gradlim_const(
    input_expr: Expr | Comparison | float | int | bool,
    gradmin: Expr | Comparison | float | int | bool,
    gradmax: Expr | Comparison | float | int | bool,
    output: Var | str,
    name: str = "",
) -> GradientLimiterLogic:
    """
    Build the procedural equivalent of PowerFactory ``gradlim_const``.

    :param input_expr: Source expression to be rate-limited.
    :param gradmin: Lower slope limit.
    :param gradmax: Upper slope limit.
    :param output: Runtime mode variable receiving the limited value.
    :param name: Optional logic name.
    :return: Gradient-limiter procedural logic entry.
    """
    output_name = _coerce_var_name(output)
    return GradientLimiterLogic(
        output_var_name=output_name,
        source_expr=input_expr,
        lower_rate_expr=gradmin,
        upper_rate_expr=gradmax,
        name=output_name if name == "" else name,
    )


def flipflop(boolset: Expr | Comparison, boolreset: Expr | Comparison, output: Var | str, name: str = "") -> FlipFlopLogic:
    """
    Build the procedural equivalent of PowerFactory ``flipflop``.

    :param boolset: Set condition.
    :param boolreset: Reset condition.
    :param output: Runtime mode variable storing the logical state.
    :param name: Optional logic name.
    :return: Flip-flop procedural logic entry.
    """
    output_name = _coerce_var_name(output)
    return FlipFlopLogic(
        output_var_name=output_name,
        set_expr=boolset,
        reset_expr=boolreset,
        name=output_name if name == "" else name,
    )


def aflipflop(
    x: Expr | Comparison,
    boolset: Expr | Comparison,
    boolreset: Expr | Comparison,
    output: Var | str,
    name: str = "",
) -> AnalogFlipFlopLogic:
    """
    Build the procedural equivalent of PowerFactory ``aflipflop``.

    :param x: Analog expression to store while the internal state is high.
    :param boolset: Set condition.
    :param boolreset: Reset condition.
    :param output: Runtime mode variable receiving the held analog value.
    :param name: Optional logic name.
    :return: Analog flip-flop procedural logic entry.
    """
    output_name = _coerce_var_name(output)
    return AnalogFlipFlopLogic(
        output_var_name=output_name,
        input_expr=x,
        set_expr=boolset,
        reset_expr=boolreset,
        name=output_name if name == "" else name,
    )


def pickup_dropoff(
    output: Var | str,
    boolexpr: Expr | Comparison,
    Tpick: Expr | Comparison,
    Tdrop: Expr | Comparison,
    name: str = "",
) -> PickupDropoffLogic:
    """
    Build a pickup/dropoff relay-style procedural logic entry.

    :param output: Runtime mode variable storing the relay state.
    :param boolexpr: Pickup/reset driving condition.
    :param Tpick: Pickup delay.
    :param Tdrop: Dropoff delay.
    :param name: Optional logic name.
    :return: Pickup/dropoff procedural logic entry.
    """
    output_name = _coerce_var_name(output)
    return PickupDropoffLogic(
        output_var_name=output_name,
        bool_expr=boolexpr,
        pickup_delay_expr=Tpick,
        drop_delay_expr=Tdrop,
        name=output_name if name == "" else name,
    )


def picdro(
    boolexpr: Expr | Comparison,
    Tpick: Expr | Comparison,
    Tdrop: Expr | Comparison,
    output: Var | str,
    name: str = "",
) -> PickupDropoffLogic:
    """
    Build the procedural equivalent of PowerFactory ``picdro``.

    :param boolexpr: Relay driving condition.
    :param Tpick: Pickup delay.
    :param Tdrop: Dropoff delay.
    :param output: Runtime mode variable storing the relay state.
    :param name: Optional logic name.
    :return: Pickup/dropoff procedural logic entry.
    """
    return pickup_dropoff(output=output, boolexpr=boolexpr, Tpick=Tpick, Tdrop=Tdrop, name=name)


def picdro_const(
    boolexpr: Expr | Comparison,
    Tpick: Expr | Comparison,
    Tdrop: Expr | Comparison,
    output: Var | str,
    name: str = "",
) -> PickupDropoffLogic:
    """
    Build the procedural equivalent of PowerFactory ``picdro_const``.

    :param boolexpr: Relay driving condition.
    :param Tpick: Pickup delay.
    :param Tdrop: Dropoff delay.
    :param output: Runtime mode variable storing the relay state.
    :param name: Optional logic name.
    :return: Pickup/dropoff procedural logic entry.
    """
    return pickup_dropoff(output=output, boolexpr=boolexpr, Tpick=Tpick, Tdrop=Tdrop, name=name)


def reset(var: Var | str, rst: Expr | Comparison, val: Expr | Comparison, name: str = "") -> ResetOnRisingEdgeLogic:
    """
    Build the procedural equivalent of PowerFactory ``reset``.

    :param var: Target runtime/state variable name.
    :param rst: Reset trigger condition.
    :param val: Value applied on the rising edge.
    :param name: Optional logic name.
    :return: Reset-on-rising-edge procedural logic entry.
    """
    target_name = _coerce_var_name(var)
    return ResetOnRisingEdgeLogic(
        target_var_name=target_name,
        reset_expr=rst,
        value_expr=val,
        name=f"{target_name}_reset" if name == "" else name,
    )


def startup_handover(mode: Var | str, t_enable: Var | str, name: str = "") -> StartupHandoverLogic:
    """
    Build one exact-time startup-handover logic entry.

    :param mode: Retained mode variable that becomes ``1`` after the handover time.
    :param t_enable: Runtime parameter storing the switching-enable time.
    :param name: Optional logic name.
    :return: Startup-handover procedural logic entry.
    """
    mode_name: str = _coerce_var_name(mode)
    enable_name: str = _coerce_var_name(t_enable)
    return StartupHandoverLogic(
        mode_var_name=mode_name,
        enable_time_var_name=enable_name,
        name=mode_name if name == "" else name,
    )

def _iter_block_vars(block: Block) -> List[Var]:
    """
    Collect all variables reachable from one block tree.

    :param block: Root block to inspect.
    :return: Flat list of variables reachable from the tree.
    """
    vars_found: List[Var] = list()
    vars_found.extend(block.state_vars)
    vars_found.extend(block.algebraic_vars)
    vars_found.extend(block.diff_vars)
    vars_found.extend(block.in_vars)
    vars_found.extend(block.out_vars)
    vars_found.extend(list(block.event_dict.keys()))
    vars_found.extend(list(block.mode_dict.keys()))

    for child in block.children:
        vars_found.extend(_iter_block_vars(child))

    return vars_found


def _find_var_by_name(block: Block, var_name: str) -> Var:
    """
    Find one symbolic variable by name inside a block tree.

    :param block: Root block to inspect.
    :param var_name: Variable name to search.
    :return: Matching symbolic variable.
    """
    for var in _iter_block_vars(block):
        if var.name == var_name:
            return var
    raise KeyError(f"Variable '{var_name}' not found in block tree")


def _find_var_by_name_optional(block: Block, var_name: str) -> Var | None:
    """
    Return one symbolic variable by name when it exists in the block tree.

    :param block: Root block to inspect.
    :param var_name: Variable name to search.
    :return: Matching symbolic variable or ``None``.
    """
    var: Var

    for var in _iter_block_vars(block):
        if var.name == var_name:
            return var
        else:
            pass

    return None


class DelayedThresholdLatchLogic(ProceduralLogicBase):
    """
    Comparator + timer + latch procedural logic for runtime modes.

    The logic watches one state variable, arms a timer when a threshold is crossed,
    applies a mode change after a delay, and optionally resets after a second delay.
    """

    __slots__ = [
        "monitored_var_name",
        "mode_var_name",
        "threshold",
        "delay",
        "reset_delay",
        "mode_idx",
        "monitored_idx",
        "pickup_time",
        "pending_trip_time",
        "pending_reset_time",
        "tripped",
        "trip_applied_time",
        "trip_applied_solver_time",
        "reset_applied_time",
        "reset_applied_solver_time",
        "last_t_prev",
        "trace_t",
        "trace_measure",
        "trace_comparator",
        "trace_timer_armed",
        "trace_latched",
        "trace_mode",
    ]
    logic_tpe = ProceduralLogicType.DelayedThresholdLatch

    def __init__(
        self,
        monitored_var_name: str,
        mode_var_name: str,
        threshold: float,
        delay: float,
        reset_delay: Optional[float] = None,
        name: str = "",
    ) -> None:
        super().__init__(name=name)
        self.monitored_var_name = monitored_var_name
        self.mode_var_name = mode_var_name
        self.threshold = float(threshold)
        self.delay = float(delay)
        self.reset_delay = None if reset_delay is None else float(reset_delay)

        self.mode_idx = -1
        self.monitored_idx = -1
        self.pickup_time: Optional[float] = None
        self.pending_trip_time: Optional[float] = None
        self.pending_reset_time: Optional[float] = None
        self.tripped = False
        self.trip_applied_time: Optional[float] = None
        self.trip_applied_solver_time: Optional[float] = None
        self.reset_applied_time: Optional[float] = None
        self.reset_applied_solver_time: Optional[float] = None
        self.last_t_prev: Optional[float] = None

        self.trace_t: List[float] = list()
        self.trace_measure: List[float] = list()
        self.trace_comparator: List[float] = list()
        self.trace_timer_armed: List[float] = list()
        self.trace_latched: List[float] = list()
        self.trace_mode: List[float] = list()

    def bind(self, problem: EmtProblemTemplate) -> None:
        """
        Resolve the monitored state and runtime mode indices.

        :param problem: Bound EMT problem.
        :return: None
        """
        super().bind(problem)
        mode_var = _find_var_by_name(problem.sys_block, self.mode_var_name)
        monitored_var = _find_var_by_name(problem.sys_block, self.monitored_var_name)
        self.mode_idx = int(problem.uid2idx_event_params[mode_var.uid])
        self.monitored_idx = int(problem.get_var_idx(monitored_var))

    def _append_trace_point(
        self,
        trace_time: float,
        measured_value: float,
        comparator: float,
        timer_armed: float,
        latched: float,
        mode_value: float,
    ) -> None:
        """
        Append one point to the internal tracing arrays.

        :param trace_time: Trace time.
        :param measured_value: Monitored value.
        :param comparator: Comparator state.
        :param timer_armed: Timer state.
        :param latched: Latch state.
        :param mode_value: Runtime mode state.
        :return: None
        """
        self.trace_t.append(float(trace_time))
        self.trace_measure.append(float(measured_value))
        self.trace_comparator.append(float(comparator))
        self.trace_timer_armed.append(float(timer_armed))
        self.trace_latched.append(float(latched))
        self.trace_mode.append(float(mode_value))

    def _record_sample_trace(self, sample_time: float, measured_value: float, params: np.ndarray) -> None:
        """
        Record one trace point at the accepted physical sample time.

        :param sample_time: Accepted sample time.
        :param measured_value: Monitored value.
        :param params: Runtime parameter vector.
        :return: None
        """
        comparator = 1.0 if measured_value >= self.threshold else 0.0
        timer_armed = 1.0 if self.pending_trip_time is not None else 0.0
        latched = 1.0 if self.tripped else 0.0
        mode_value = float(params[self.mode_idx])
        self._append_trace_point(sample_time, measured_value, comparator, timer_armed, latched, mode_value)

    def get_next_forced_event_time(self, t_prev: float, t_target: float) -> Optional[float]:
        """
        Return the next exact trip or reset event inside one solver step.

        :param t_prev: Previous solver time.
        :param t_target: Nominal target time.
        :return: First pending event in the interval, if any.
        """
        super().get_next_forced_event_time(t_prev, t_target)
        self.last_t_prev = float(t_prev)
        candidates: List[float] = list()
        if self.pending_trip_time is not None and t_prev < self.pending_trip_time <= t_target:
            candidates.append(float(self.pending_trip_time))
        if self.pending_reset_time is not None and t_prev < self.pending_reset_time <= t_target:
            candidates.append(float(self.pending_reset_time))
        if len(candidates) == 0:
            return None
        return min(candidates)

    def update(self, t: float, x: Vec, params: Vec) -> None:
        """
        Advance the delayed-threshold latch logic and tracing state.

        :param t: Current solver time.
        :param x: Accepted state vector.
        :param params: Runtime parameter vector.
        :return: None
        """
        tol = 1.0e-15
        sample_time = float(self.last_t_prev if self.last_t_prev is not None else t)
        measured_value = float(x[self.monitored_idx])
        comparator_on = measured_value >= self.threshold
        comparator_value = 1.0 if comparator_on else 0.0

        if self.tripped:
            # When already tripped, only the optional delayed reset can change the state.
            params[self.mode_idx] = 0.0
            if self.pending_reset_time is not None and t >= (self.pending_reset_time - tol):
                self.tripped = False
                self.reset_applied_time = float(self.pending_reset_time)
                self.reset_applied_solver_time = float(t)
                self.pickup_time = None
                self.pending_trip_time = None
                self.pending_reset_time = None
                params[self.mode_idx] = 1.0
                self._append_trace_point(t, measured_value, comparator_value, 0.0, 0.0, 1.0)
                return
            self._record_sample_trace(sample_time, measured_value, params)
            return

        if comparator_on:
            # Arm the pickup timer only once on the first threshold crossing.
            if self.pickup_time is None:
                self.pickup_time = sample_time
                self.pending_trip_time = sample_time + self.delay
        else:
            # Clearing the comparator also clears any unfinished pickup timer.
            self.pickup_time = None
            self.pending_trip_time = None

        if self.pending_trip_time is not None and t >= (self.pending_trip_time - tol):
            self.tripped = True
            self.trip_applied_time = float(self.pending_trip_time)
            self.trip_applied_solver_time = float(t)
            params[self.mode_idx] = 0.0
            if self.reset_delay is not None:
                self.pending_reset_time = self.trip_applied_time + self.reset_delay
            self.pending_trip_time = None
            self._append_trace_point(t, measured_value, comparator_value, 0.0, 1.0, 0.0)
            return

        params[self.mode_idx] = 1.0
        self._record_sample_trace(sample_time, measured_value, params)

    def get_trace_arrays(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Return the internal trace arrays as dense numpy arrays.

        :return: Tuple with times, measurements, comparator, timer, latch, and mode traces.
        """
        return (
            np.asarray(self.trace_t, dtype=float),
            np.asarray(self.trace_measure, dtype=float),
            np.asarray(self.trace_comparator, dtype=float),
            np.asarray(self.trace_timer_armed, dtype=float),
            np.asarray(self.trace_latched, dtype=float),
            np.asarray(self.trace_mode, dtype=float),
        )

    def remap(self, var_mapping: VarRemap) -> "DelayedThresholdLatchLogic":
        """
        Clone the logic under a variable remapping.

        :param var_mapping: Variable substitution map.
        :return: Remapped delayed-threshold latch logic.
        """
        name_mapping = _build_name_mapping(var_mapping)
        return DelayedThresholdLatchLogic(
            monitored_var_name=name_mapping.get(self.monitored_var_name, self.monitored_var_name),
            mode_var_name=name_mapping.get(self.mode_var_name, self.mode_var_name),
            threshold=self.threshold,
            delay=self.delay,
            reset_delay=self.reset_delay,
            name=self.name,
        )


class StartupHandoverLogic(ProceduralLogicBase):
    """
    One-shot startup handover for hybrid EMT converter models.

    The logic keeps one retained runtime mode at ``0`` during the averaged-startup
    interval and flips it to ``1`` exactly at ``t_enable``. This lets the DAE stay
    continuous before the handover while still forcing an exact solver split when
    the switched bridge becomes electrically active.
    """

    __slots__ = [
        "mode_var_name",
        "enable_time_var_name",
        "mode_idx",
        "enable_time_idx",
    ]
    logic_tpe = ProceduralLogicType.StartupHandover

    def __init__(
            self,
            mode_var_name: str,
            enable_time_var_name: str,
            name: str = "",
    ) -> None:
        """
        Build one startup-handover procedural logic entry.

        :param mode_var_name: Retained runtime mode variable name.
        :param enable_time_var_name: Runtime parameter storing the handover time in seconds.
        :param name: Logic entry name.
        :return: None.
        """
        super().__init__(name=name)
        self.mode_var_name = mode_var_name
        self.enable_time_var_name = enable_time_var_name
        self.mode_idx = -1
        self.enable_time_idx = -1

    def bind(self, problem: EmtProblemTemplate) -> None:
        """
        Resolve the retained mode and enable-time runtime indices.

        :param problem: Bound EMT problem.
        :return: None.
        """
        mode_var: Var
        enable_time_var: Var

        super().bind(problem)
        mode_var = _find_var_by_name(problem.sys_block, self.mode_var_name)
        enable_time_var = _find_var_by_name(problem.sys_block, self.enable_time_var_name)
        self.mode_idx = int(problem.uid2idx_event_params[mode_var.uid])
        self.enable_time_idx = int(problem.uid2idx_event_params[enable_time_var.uid])

    def get_next_forced_event_time(self, t_prev: float, t_target: float) -> Optional[float]:
        """
        Return the exact startup-handover time when it falls inside one solver step.

        :param t_prev: Previous solver time.
        :param t_target: Nominal target time.
        :return: Exact handover time or ``None``.
        """
        problem: EmtProblemTemplate
        enable_time: float

        super().get_next_forced_event_time(t_prev, t_target)
        problem = self._get_problem()
        enable_time = float(problem.event_params_values[self.enable_time_idx])

        if t_prev < enable_time <= t_target:
            return enable_time
        else:
            return None

    def update(self, t: float, x: Vec, params: Vec) -> None:
        """
        Update the retained startup mode from the current solver time.

        :param t: Current solver time.
        :param x: Accepted state vector.
        :param params: Runtime parameter vector.
        :return: None.
        """
        _unused_x: Vec = x
        tol: float = 1.0e-15
        enable_time: float = float(params[self.enable_time_idx])

        if t >= (enable_time - tol):
            params[self.mode_idx] = 1.0
        else:
            params[self.mode_idx] = 0.0

    def remap(self, var_mapping: VarRemap) -> "StartupHandoverLogic":
        """
        Clone the logic under a variable remapping.

        :param var_mapping: Variable substitution map.
        :return: Remapped startup-handover logic.
        """
        name_mapping: Dict[str, str] = _build_name_mapping(var_mapping)
        return StartupHandoverLogic(
            mode_var_name=name_mapping.get(self.mode_var_name, self.mode_var_name),
            enable_time_var_name=name_mapping.get(self.enable_time_var_name, self.enable_time_var_name),
            name=self.name,
        )


class ValveStateLogic(ProceduralLogicBase):
    """
    Retained conduction-state logic for generic EMT valve blocks.

    The logic updates a single retained runtime mode that encodes the active path:

    - ``+1``: forward conduction
    - ``0``: blocked state
    - ``-1``: reverse conduction through the antiparallel path
    """

    __slots__ = [
        "mode_var_name",
        "valve_type_var_name",
        "gate_var_name",
        "antiparallel_var_name",
        "voltage_eps_var_name",
        "current_eps_var_name",
        "valve_voltage_var_name",
        "valve_current_var_name",
        "mode_idx",
        "valve_type_idx",
        "gate_idx",
        "antiparallel_idx",
        "voltage_eps_idx",
        "current_eps_idx",
        "valve_voltage_idx",
        "valve_current_idx",
    ]
    logic_tpe = ProceduralLogicType.ValveState

    def __init__(
            self,
            mode_var_name: str,
            valve_type_var_name: str,
            gate_var_name: str,
            antiparallel_var_name: str,
            voltage_eps_var_name: str,
            current_eps_var_name: str,
            valve_voltage_var_name: str,
            valve_current_var_name: str,
            name: str = "",
    ) -> None:
        """
        Build one retained valve-state procedural logic entry.

        :param mode_var_name: Retained runtime mode variable name.
        :param valve_type_var_name: Runtime parameter storing the valve type code.
        :param gate_var_name: Runtime parameter storing the gate command.
        :param antiparallel_var_name: Runtime parameter enabling the reverse path.
        :param voltage_eps_var_name: Runtime parameter with the voltage deadband.
        :param current_eps_var_name: Runtime parameter with the current deadband.
        :param valve_voltage_var_name: Algebraic valve-voltage variable name.
        :param valve_current_var_name: Algebraic valve-current variable name.
        :param name: Logic entry name.
        :return: None.
        """
        super().__init__(name=name)
        self.mode_var_name = mode_var_name
        self.valve_type_var_name = valve_type_var_name
        self.gate_var_name = gate_var_name
        self.antiparallel_var_name = antiparallel_var_name
        self.voltage_eps_var_name = voltage_eps_var_name
        self.current_eps_var_name = current_eps_var_name
        self.valve_voltage_var_name = valve_voltage_var_name
        self.valve_current_var_name = valve_current_var_name
        self.mode_idx = -1
        self.valve_type_idx = -1
        self.gate_idx = -1
        self.antiparallel_idx = -1
        self.voltage_eps_idx = -1
        self.current_eps_idx = -1
        self.valve_voltage_idx = -1
        self.valve_current_idx = -1

    def bind(self, problem: EmtProblemTemplate) -> None:
        """
        Resolve the runtime and algebraic indices required by the valve logic.

        :param problem: Bound EMT problem.
        :return: None.
        """
        mode_var: Var
        valve_type_var: Var
        gate_var: Var
        antiparallel_var: Var
        voltage_eps_var: Var
        current_eps_var: Var
        valve_voltage_var: Var
        valve_current_var: Var

        super().bind(problem)
        mode_var = _find_var_by_name(problem.sys_block, self.mode_var_name)
        valve_type_var = _find_var_by_name(problem.sys_block, self.valve_type_var_name)
        gate_var = _find_var_by_name(problem.sys_block, self.gate_var_name)
        antiparallel_var = _find_var_by_name(problem.sys_block, self.antiparallel_var_name)
        voltage_eps_var = _find_var_by_name(problem.sys_block, self.voltage_eps_var_name)
        current_eps_var = _find_var_by_name(problem.sys_block, self.current_eps_var_name)
        valve_voltage_var = _find_var_by_name(problem.sys_block, self.valve_voltage_var_name)
        valve_current_var = _find_var_by_name(problem.sys_block, self.valve_current_var_name)

        self.mode_idx = int(problem.uid2idx_event_params[mode_var.uid])
        self.valve_type_idx = int(problem.uid2idx_event_params[valve_type_var.uid])
        self.gate_idx = int(problem.uid2idx_event_params[gate_var.uid])
        self.antiparallel_idx = int(problem.uid2idx_event_params[antiparallel_var.uid])
        self.voltage_eps_idx = int(problem.uid2idx_event_params[voltage_eps_var.uid])
        self.current_eps_idx = int(problem.uid2idx_event_params[current_eps_var.uid])
        self.valve_voltage_idx = int(problem.get_var_idx(valve_voltage_var))
        self.valve_current_idx = int(problem.get_var_idx(valve_current_var))

    def _get_mode_value(self, params: Vec) -> float:
        """
        Return the retained valve path mode stored in the runtime parameter vector.

        :param params: Runtime parameter vector.
        :return: Retained conduction-path mode.
        """
        return float(params[self.mode_idx])

    def _coerce_path_mode(self, raw_mode: float) -> float:
        """
        Quantize the retained path mode to ``-1``, ``0`` or ``+1``.

        :param raw_mode: Raw runtime value.
        :return: Quantized retained mode.
        """
        if raw_mode > 0.5:
            return 1.0
        else:
            pass

        if raw_mode < -0.5:
            return -1.0
        else:
            pass

        return 0.0

    def _compute_diode_mode(
            self,
            old_mode: float,
            valve_voltage: float,
            valve_current: float,
            antiparallel_enabled: bool,
            voltage_eps: float,
            current_eps: float,
    ) -> float:
        """
        Compute the retained path mode for a diode valve.

        :param old_mode: Previous retained path mode.
        :param valve_voltage: Accepted valve voltage.
        :param valve_current: Accepted valve current.
        :param antiparallel_enabled: Reverse path enable flag.
        :param voltage_eps: Voltage deadband.
        :param current_eps: Current deadband.
        :return: Updated retained path mode.
        """
        if valve_voltage > voltage_eps:
            return 1.0
        else:
            pass

        if old_mode > 0.5 and valve_current > -current_eps:
            return 1.0
        else:
            pass

        if antiparallel_enabled:
            if valve_voltage < -voltage_eps:
                return -1.0
            else:
                pass

            if old_mode < -0.5 and valve_current < current_eps:
                return -1.0
            else:
                pass
        else:
            pass

        return 0.0

    def _compute_igbt_mode(
            self,
            old_mode: float,
            valve_voltage: float,
            valve_current: float,
            gate_fired: bool,
            antiparallel_enabled: bool,
            voltage_eps: float,
            current_eps: float,
    ) -> float:
        """
        Compute the retained path mode for an IGBT valve.

        :param old_mode: Previous retained path mode.
        :param valve_voltage: Accepted valve voltage.
        :param valve_current: Accepted valve current.
        :param gate_fired: Gate command.
        :param antiparallel_enabled: Reverse path enable flag.
        :param voltage_eps: Voltage deadband.
        :param current_eps: Current deadband.
        :return: Updated retained path mode.
        """
        if gate_fired:
            if valve_voltage > -voltage_eps:
                return 1.0
            else:
                pass

            if old_mode > 0.5 and valve_current > -current_eps:
                return 1.0
            else:
                pass
        else:
            pass

        if antiparallel_enabled:
            if valve_voltage < -voltage_eps:
                return -1.0
            else:
                pass

            if old_mode < -0.5 and valve_current < current_eps:
                return -1.0
            else:
                pass

            return 0.0
        else:
            return 0.0

    def _compute_thyristor_mode(
            self,
            old_mode: float,
            valve_voltage: float,
            valve_current: float,
            gate_fired: bool,
            antiparallel_enabled: bool,
            voltage_eps: float,
            current_eps: float,
    ) -> float:
        """
        Compute the retained path mode for a thyristor valve.

        :param old_mode: Previous retained path mode.
        :param valve_voltage: Accepted valve voltage.
        :param valve_current: Accepted valve current.
        :param gate_fired: Gate command.
        :param antiparallel_enabled: Reverse path enable flag.
        :param voltage_eps: Voltage deadband.
        :param current_eps: Current deadband.
        :return: Updated retained path mode.
        """
        if old_mode > 0.5:
            if valve_current > current_eps and valve_voltage > -voltage_eps:
                return 1.0
            else:
                pass
        else:
            pass

        if gate_fired and valve_voltage > -voltage_eps:
            return 1.0
        else:
            pass

        if antiparallel_enabled:
            if valve_voltage < -voltage_eps:
                return -1.0
            else:
                pass

            if old_mode < -0.5 and valve_current < current_eps:
                return -1.0
            else:
                pass

            return 0.0
        else:
            return 0.0

    def _compute_path_mode(
            self,
            old_mode: float,
            valve_type_code: float,
            valve_voltage: float,
            valve_current: float,
            gate_fired: bool,
            antiparallel_enabled: bool,
            voltage_eps: float,
            current_eps: float,
    ) -> float:
        """
        Compute the updated retained conduction-path mode.

        :param old_mode: Previous retained path mode.
        :param valve_type_code: Runtime code describing the valve type.
        :param valve_voltage: Accepted valve voltage.
        :param valve_current: Accepted valve current.
        :param gate_fired: Gate command.
        :param antiparallel_enabled: Reverse path enable flag.
        :param voltage_eps: Voltage deadband.
        :param current_eps: Current deadband.
        :return: Updated retained path mode.
        """
        if valve_type_code < 0.5:
            return self._compute_diode_mode(
                old_mode=old_mode,
                valve_voltage=valve_voltage,
                valve_current=valve_current,
                antiparallel_enabled=antiparallel_enabled,
                voltage_eps=voltage_eps,
                current_eps=current_eps,
            )
        else:
            pass

        if valve_type_code < 1.5:
            return self._compute_igbt_mode(
                old_mode=old_mode,
                valve_voltage=valve_voltage,
                valve_current=valve_current,
                gate_fired=gate_fired,
                antiparallel_enabled=antiparallel_enabled,
                voltage_eps=voltage_eps,
                current_eps=current_eps,
            )
        else:
            pass

        return self._compute_thyristor_mode(
            old_mode=old_mode,
            valve_voltage=valve_voltage,
            valve_current=valve_current,
            gate_fired=gate_fired,
            antiparallel_enabled=antiparallel_enabled,
            voltage_eps=voltage_eps,
            current_eps=current_eps,
        )

    def update(self, t: float, x: Vec, params: Vec) -> None:
        """
        Update the retained conduction-path mode from the accepted EMT state.

        :param t: Current solver time.
        :param x: Accepted EMT state vector.
        :param params: Flat runtime parameter vector.
        :return: None.
        """
        old_mode: float
        valve_type_code: float
        gate_fired: bool
        antiparallel_enabled: bool
        voltage_eps: float
        current_eps: float
        valve_voltage: float
        valve_current: float
        new_mode: float

        _unused_t: float = float(t)
        old_mode = self._coerce_path_mode(self._get_mode_value(params))
        valve_type_code = float(params[self.valve_type_idx])
        gate_fired = float(params[self.gate_idx]) > 0.5
        antiparallel_enabled = float(params[self.antiparallel_idx]) > 0.5
        voltage_eps = abs(float(params[self.voltage_eps_idx]))
        current_eps = abs(float(params[self.current_eps_idx]))
        valve_voltage = float(x[self.valve_voltage_idx])
        valve_current = float(x[self.valve_current_idx])

        # The conduction mode depends on the accepted electrical state and the retained latch history.
        new_mode = self._compute_path_mode(
            old_mode=old_mode,
            valve_type_code=valve_type_code,
            valve_voltage=valve_voltage,
            valve_current=valve_current,
            gate_fired=gate_fired,
            antiparallel_enabled=antiparallel_enabled,
            voltage_eps=voltage_eps,
            current_eps=current_eps,
        )
        params[self.mode_idx] = new_mode

    def remap(self, var_mapping: VarRemap) -> "ValveStateLogic":
        """
        Clone the valve logic under a variable remapping.

        :param var_mapping: Variable substitution map.
        :return: Remapped valve logic.
        """
        name_mapping: Dict[str, str] = _build_name_mapping(var_mapping)
        return ValveStateLogic(
            mode_var_name=name_mapping.get(self.mode_var_name, self.mode_var_name),
            valve_type_var_name=name_mapping.get(self.valve_type_var_name, self.valve_type_var_name),
            gate_var_name=name_mapping.get(self.gate_var_name, self.gate_var_name),
            antiparallel_var_name=name_mapping.get(self.antiparallel_var_name, self.antiparallel_var_name),
            voltage_eps_var_name=name_mapping.get(self.voltage_eps_var_name, self.voltage_eps_var_name),
            current_eps_var_name=name_mapping.get(self.current_eps_var_name, self.current_eps_var_name),
            valve_voltage_var_name=name_mapping.get(self.valve_voltage_var_name, self.valve_voltage_var_name),
            valve_current_var_name=name_mapping.get(self.valve_current_var_name, self.valve_current_var_name),
            name=self.name,
        )


class ThreePhaseCarrierPwmLogic(ProceduralLogicBase):
    """
    Regular-sampled three-phase carrier PWM logic.

    The logic samples the modulation references at each carrier half-period,
    computes the exact gate transitions inside that interval, and stores the gate
    values as retained runtime modes. The symbolic DAE therefore sees piecewise-
    constant gate parameters instead of symbolic comparator expressions.
    """

    __slots__ = [
        "mod_a_var_name",
        "mod_b_var_name",
        "mod_c_var_name",
        "gate_a_mode_var_name",
        "gate_b_mode_var_name",
        "gate_c_mode_var_name",
        "omega_sw_var_name",
        "carrier_phase_var_name",
        "mod_a_idx",
        "mod_b_idx",
        "mod_c_idx",
        "gate_a_idx",
        "gate_b_idx",
        "gate_c_idx",
        "omega_sw_idx",
        "carrier_phase_idx",
        "initialized",
        "interval_end_time",
        "pending_transition_time",
        "pending_transition_gate",
        "current_gate",
    ]
    logic_tpe = ProceduralLogicType.ThreePhaseCarrierPwm

    def __init__(
            self,
            mod_a_var_name: str,
            mod_b_var_name: str,
            mod_c_var_name: str,
            gate_a_mode_var_name: str,
            gate_b_mode_var_name: str,
            gate_c_mode_var_name: str,
            omega_sw_var_name: str,
            carrier_phase_var_name: str,
            name: str = "",
    ) -> None:
        """
        Build one three-phase PWM logic entry.

        :param mod_a_var_name: Phase-A modulation variable name.
        :param mod_b_var_name: Phase-B modulation variable name.
        :param mod_c_var_name: Phase-C modulation variable name.
        :param gate_a_mode_var_name: Retained phase-A gate mode name.
        :param gate_b_mode_var_name: Retained phase-B gate mode name.
        :param gate_c_mode_var_name: Retained phase-C gate mode name.
        :param omega_sw_var_name: Switching angular-frequency parameter name.
        :param carrier_phase_var_name: Carrier phase-shift parameter name.
        :param name: Logic entry name.
        :return: None.
        """
        super().__init__(name=name)
        self.mod_a_var_name = mod_a_var_name
        self.mod_b_var_name = mod_b_var_name
        self.mod_c_var_name = mod_c_var_name
        self.gate_a_mode_var_name = gate_a_mode_var_name
        self.gate_b_mode_var_name = gate_b_mode_var_name
        self.gate_c_mode_var_name = gate_c_mode_var_name
        self.omega_sw_var_name = omega_sw_var_name
        self.carrier_phase_var_name = carrier_phase_var_name

        self.mod_a_idx = -1
        self.mod_b_idx = -1
        self.mod_c_idx = -1
        self.gate_a_idx = -1
        self.gate_b_idx = -1
        self.gate_c_idx = -1
        self.omega_sw_idx = -1
        self.carrier_phase_idx = -1

        self.initialized = False
        self.interval_end_time: Optional[float] = None
        self.pending_transition_time = np.full(3, np.nan, dtype=float)
        self.pending_transition_gate = np.zeros(3, dtype=float)
        self.current_gate = np.zeros(3, dtype=float)

    def bind(self, problem: EmtProblemTemplate) -> None:
        """
        Resolve the variable indices and initialize the first PWM interval.

        :param problem: Bound EMT problem.
        :return: None.
        """
        mod_a_var: Var
        mod_b_var: Var
        mod_c_var: Var
        gate_a_var: Var
        gate_b_var: Var
        gate_c_var: Var
        omega_sw_var: Var
        carrier_phase_var: Var | None
        x0: Vec
        params0: Vec

        super().bind(problem)
        mod_a_var = _find_var_by_name(problem.sys_block, self.mod_a_var_name)
        mod_b_var = _find_var_by_name(problem.sys_block, self.mod_b_var_name)
        mod_c_var = _find_var_by_name(problem.sys_block, self.mod_c_var_name)
        gate_a_var = _find_var_by_name(problem.sys_block, self.gate_a_mode_var_name)
        gate_b_var = _find_var_by_name(problem.sys_block, self.gate_b_mode_var_name)
        gate_c_var = _find_var_by_name(problem.sys_block, self.gate_c_mode_var_name)
        omega_sw_var = _find_var_by_name(problem.sys_block, self.omega_sw_var_name)
        carrier_phase_var = _find_var_by_name_optional(problem.sys_block, self.carrier_phase_var_name)

        self.mod_a_idx = int(problem.get_var_idx(mod_a_var))
        self.mod_b_idx = int(problem.get_var_idx(mod_b_var))
        self.mod_c_idx = int(problem.get_var_idx(mod_c_var))
        self.gate_a_idx = int(problem.uid2idx_event_params[gate_a_var.uid])
        self.gate_b_idx = int(problem.uid2idx_event_params[gate_b_var.uid])
        self.gate_c_idx = int(problem.uid2idx_event_params[gate_c_var.uid])
        self.omega_sw_idx = int(problem.uid2idx_event_params[omega_sw_var.uid])

        if carrier_phase_var is None:
            self.carrier_phase_idx = -1
        else:
            self.carrier_phase_idx = int(problem.uid2idx_event_params[carrier_phase_var.uid])

        x0 = problem.get_x0().copy()
        params0 = problem.event_params_values

        # Binding initializes the retained gates so the very first EMT step starts from a consistent PWM state.
        self._rebuild_interval_schedule(sample_time=0.0, x=x0, params=params0)
        self._write_gate_modes(params0)
        self.initialized = True

    def _get_half_period(self, params: Vec) -> float:
        """
        Return the PWM carrier half-period.

        :param params: Runtime parameter vector.
        :return: Carrier half-period.
        """
        omega_sw: float = abs(float(params[self.omega_sw_idx]))

        if omega_sw > 1.0e-12:
            return float(np.pi / omega_sw)
        else:
            return 1.0e12

    def _get_interval_descriptor(self, sample_time: float, params: Vec) -> Tuple[float, bool]:
        """
        Return the end time and slope direction of the current carrier interval.

        :param sample_time: Accepted sample time.
        :param params: Runtime parameter vector.
        :return: Tuple ``(interval_end_time, carrier_rising)``.
        """
        omega_sw: float = float(params[self.omega_sw_idx])
        carrier_phase: float
        shifted_phase: float
        interval_index: int
        interval_start_time: float
        interval_end_time: float
        carrier_rising: bool
        half_period: float

        if abs(omega_sw) <= 1.0e-12:
            interval_end_time = sample_time + 1.0e12
            carrier_rising = True
        else:
            if self.carrier_phase_idx >= 0:
                carrier_phase = float(params[self.carrier_phase_idx])
            else:
                carrier_phase = 0.0

            half_period = self._get_half_period(params)
            shifted_phase = omega_sw * sample_time + carrier_phase + 0.5 * np.pi
            interval_index = int(math.floor(shifted_phase / np.pi))
            interval_start_time = (float(interval_index) * np.pi - carrier_phase - 0.5 * np.pi) / omega_sw
            interval_end_time = interval_start_time + half_period

            if interval_index % 2 == 0:
                carrier_rising = True
            else:
                carrier_rising = False

        return float(interval_end_time), carrier_rising

    def _read_modulation_values(self, x: Vec) -> np.ndarray:
        """
        Return the accepted per-phase modulation references.

        :param x: Accepted EMT state vector.
        :return: Three-phase modulation reference vector.
        """
        modulation_values: np.ndarray = np.zeros(3, dtype=float)
        modulation_values[0] = float(x[self.mod_a_idx])
        modulation_values[1] = float(x[self.mod_b_idx])
        modulation_values[2] = float(x[self.mod_c_idx])
        return modulation_values

    def _compute_phase_schedule(
            self,
            sample_time: float,
            interval_start_time: float,
            interval_end_time: float,
            carrier_rising: bool,
            modulation_value: float,
    ) -> Tuple[float, float, float]:
        """
        Compute the current gate and the next transition of one phase.

        :param sample_time: Accepted sample time.
        :param interval_start_time: Start time of the carrier interval.
        :param interval_end_time: End time of the carrier interval.
        :param carrier_rising: ``True`` when the carrier is rising in this interval.
        :param modulation_value: Held modulation reference.
        :return: Tuple ``(gate_now, transition_time_or_nan, gate_after_transition)``.
        """
        tol: float = 1.0e-12
        clipped_value: float
        transition_time: float
        gate_now: float
        gate_after: float
        interval_width: float = interval_end_time - interval_start_time

        if modulation_value > 1.0:
            clipped_value = 1.0
        else:
            if modulation_value < -1.0:
                clipped_value = -1.0
            else:
                clipped_value = modulation_value

        if carrier_rising:
            if clipped_value <= -1.0 + tol:
                gate_now = 0.0
                transition_time = np.nan
                gate_after = 0.0
            else:
                if clipped_value >= 1.0 - tol:
                    gate_now = 1.0
                    transition_time = np.nan
                    gate_after = 1.0
                else:
                    transition_time = interval_start_time + 0.5 * (clipped_value + 1.0) * interval_width
                    gate_after = 0.0
                    if sample_time < transition_time - tol:
                        gate_now = 1.0
                    else:
                        gate_now = 0.0
                        transition_time = np.nan
        else:
            if clipped_value <= -1.0 + tol:
                gate_now = 0.0
                transition_time = np.nan
                gate_after = 0.0
            else:
                if clipped_value >= 1.0 - tol:
                    gate_now = 1.0
                    transition_time = np.nan
                    gate_after = 1.0
                else:
                    transition_time = interval_start_time + 0.5 * (1.0 - clipped_value) * interval_width
                    gate_after = 1.0
                    if sample_time < transition_time - tol:
                        gate_now = 0.0
                    else:
                        gate_now = 1.0
                        transition_time = np.nan

        return gate_now, transition_time, gate_after

    def _write_gate_modes(self, params: Vec) -> None:
        """
        Store the retained gate values into the runtime parameter vector.

        :param params: Runtime parameter vector.
        :return: None.
        """
        params[self.gate_a_idx] = self.current_gate[0]
        params[self.gate_b_idx] = self.current_gate[1]
        params[self.gate_c_idx] = self.current_gate[2]

    def _rebuild_interval_schedule(self, sample_time: float, x: Vec, params: Vec) -> None:
        """
        Recompute the PWM switching schedule for the current carrier interval.

        :param sample_time: Accepted sample time.
        :param x: Accepted EMT state vector.
        :param params: Runtime parameter vector.
        :return: None.
        """
        interval_end_time: float
        carrier_rising: bool
        interval_start_time: float
        modulation_values: np.ndarray
        phase_idx: int
        gate_now: float
        transition_time: float
        gate_after: float
        half_period: float

        interval_end_time, carrier_rising = self._get_interval_descriptor(sample_time, params)
        half_period = self._get_half_period(params)
        interval_start_time = interval_end_time - half_period
        modulation_values = self._read_modulation_values(x)

        self.interval_end_time = float(interval_end_time)
        self.pending_transition_time.fill(np.nan)

        phase_idx = 0
        while phase_idx < 3:
            gate_now, transition_time, gate_after = self._compute_phase_schedule(
                sample_time=sample_time,
                interval_start_time=interval_start_time,
                interval_end_time=interval_end_time,
                carrier_rising=carrier_rising,
                modulation_value=float(modulation_values[phase_idx]),
            )
            self.current_gate[phase_idx] = gate_now
            self.pending_transition_time[phase_idx] = transition_time
            self.pending_transition_gate[phase_idx] = gate_after
            phase_idx += 1

    def get_next_forced_event_time(self, t_prev: float, t_target: float) -> Optional[float]:
        """
        Return the next PWM gate transition or carrier-boundary event.

        :param t_prev: Previous solver time.
        :param t_target: Nominal target time.
        :return: Earliest event in the interval, if any.
        """
        candidates: List[float] = list()
        transition_idx: int = 0

        super().get_next_forced_event_time(t_prev, t_target)

        if self.interval_end_time is not None and t_prev < self.interval_end_time <= t_target:
            candidates.append(float(self.interval_end_time))
        else:
            pass

        while transition_idx < 3:
            transition_time: float = float(self.pending_transition_time[transition_idx])
            if not np.isnan(transition_time) and t_prev < transition_time <= t_target:
                candidates.append(transition_time)
            else:
                pass
            transition_idx += 1

        if len(candidates) == 0:
            return None
        else:
            return min(candidates)

    def update(self, t: float, x: Vec, params: Vec) -> None:
        """
        Advance the PWM gate states from the accepted modulation references.

        :param t: Current solver time.
        :param x: Accepted EMT state vector.
        :param params: Runtime parameter vector.
        :return: None.
        """
        tol: float = 1.0e-12
        sample_time: float = self._get_sample_time(t)
        transition_idx: int = 0

        if not self.initialized:
            self._rebuild_interval_schedule(sample_time=sample_time, x=x, params=params)
            self.initialized = True
        else:
            if self.interval_end_time is not None and sample_time >= self.interval_end_time - tol:
                # A new carrier interval starts here, so the phase schedules are rebuilt from fresh modulation samples.
                self._rebuild_interval_schedule(sample_time=sample_time, x=x, params=params)
            else:
                while transition_idx < 3:
                    transition_time: float = float(self.pending_transition_time[transition_idx])
                    if not np.isnan(transition_time) and sample_time >= transition_time - tol:
                        # Inside the current interval, only the already scheduled edge flips the gate state.
                        self.current_gate[transition_idx] = self.pending_transition_gate[transition_idx]
                        self.pending_transition_time[transition_idx] = np.nan
                    else:
                        pass
                    transition_idx += 1

        self._write_gate_modes(params)

    def remap(self, var_mapping: VarRemap) -> "ThreePhaseCarrierPwmLogic":
        """
        Clone the PWM logic under a variable remapping.

        :param var_mapping: Variable substitution map.
        :return: Remapped PWM logic.
        """
        name_mapping: Dict[str, str] = _build_name_mapping(var_mapping)
        return ThreePhaseCarrierPwmLogic(
            mod_a_var_name=name_mapping.get(self.mod_a_var_name, self.mod_a_var_name),
            mod_b_var_name=name_mapping.get(self.mod_b_var_name, self.mod_b_var_name),
            mod_c_var_name=name_mapping.get(self.mod_c_var_name, self.mod_c_var_name),
            gate_a_mode_var_name=name_mapping.get(self.gate_a_mode_var_name, self.gate_a_mode_var_name),
            gate_b_mode_var_name=name_mapping.get(self.gate_b_mode_var_name, self.gate_b_mode_var_name),
            gate_c_mode_var_name=name_mapping.get(self.gate_c_mode_var_name, self.gate_c_mode_var_name),
            omega_sw_var_name=name_mapping.get(self.omega_sw_var_name, self.omega_sw_var_name),
            carrier_phase_var_name=name_mapping.get(self.carrier_phase_var_name, self.carrier_phase_var_name),
            name=self.name,
        )


class BlockProceduralLogicUpdater(BoundaryUpdateWrapper):
    """
    Boundary updater that delegates runtime decisions to block-attached procedural logic entries.
    """

    __slots__ = ["problem", "logic_entries"]

    def __init__(self, problem: EmtProblemTemplate, logic_entries: List[ProceduralLogicBase]) -> None:
        """
        Bind all procedural logic entries to one EMT problem.

        :param problem: Bound EMT problem.
        :param logic_entries: Procedural logic entries attached to the root block.
        :return: None
        """
        self.problem = problem
        self.logic_entries = logic_entries
        for logic in self.logic_entries:
            logic.bind(problem)

    def update(self, t: float, x: Vec, params: Vec) -> None:
        """
        Forward one runtime update to all procedural logic entries.

        :param t: Current solver time.
        :param x: Accepted state vector.
        :param params: Runtime parameter vector.
        :return: None
        """
        for logic in self.logic_entries:
            logic.update(t, x, params)

    def get_next_forced_event_time(self, t_prev: float, t_target: float) -> Optional[float]:
        """
        Return the earliest forced event requested by any procedural logic entry.

        :param t_prev: Previous solver time.
        :param t_target: Nominal target time.
        :return: Earliest event in the interval, if any.
        """
        candidates: List[float] = list()
        for logic in self.logic_entries:
            candidate = logic.get_next_forced_event_time(t_prev, t_target)
            if candidate is not None:
                candidates.append(candidate)
        if len(candidates) == 0:
            return None
        return min(candidates)


def _base_logic_data(entry: ProceduralLogicBase) -> ProceduralLogicData:
    """
    Serialize the common metadata shared by all procedural logic entries.

    :param entry: Procedural logic entry.
    :return: Serialized common metadata.
    """
    return {
        "logic_type": entry.logic_tpe.value,
        "name": entry.name,
    }


def procedural_logic_entry_to_dict(entry: ProceduralLogicBase) -> ProceduralLogicData:
    """
    Serialize one procedural logic entry.

    :param entry: Procedural logic entry.
    :return: Serialized logic dictionary.
    """
    data: ProceduralLogicData = _base_logic_data(entry)

    if isinstance(entry, FixedSampleLogic):
        data.update({
            "output_var_name": entry.output_var_name,
            "condition_expr": _expr_like_to_dict(entry.condition_expr),
        })
        return data
    elif isinstance(entry, SampledValueLogic):
        data.update({
            "output_var_name": entry.output_var_name,
            "source_expr": _expr_like_to_dict(entry.source_expr),
        })
        return data
    elif isinstance(entry, HardSaturationLogic):
        data.update({
            "output_var_name": entry.output_var_name,
            "u_expr": _expr_like_to_dict(entry.u_expr),
            "u_min_expr": _expr_like_to_dict(entry.u_min_expr),
            "u_max_expr": _expr_like_to_dict(entry.u_max_expr),
        })
        return data
    elif isinstance(entry, TimeDelayLogic):
        data.update({
            "output_var_name": entry.output_var_name,
            "source_expr": _expr_like_to_dict(entry.source_expr),
            "delay_expr": _expr_like_to_dict(entry.delay_expr),
        })
        return data
    elif isinstance(entry, MovingAverageLogic):
        data.update({
            "output_var_name": entry.output_var_name,
            "source_expr": _expr_like_to_dict(entry.source_expr),
            "delay_expr": _expr_like_to_dict(entry.delay_expr),
            "window_expr": _expr_like_to_dict(entry.window_expr),
        })
        return data
    elif isinstance(entry, GradientLimiterLogic):
        data.update({
            "output_var_name": entry.output_var_name,
            "source_expr": _expr_like_to_dict(entry.source_expr),
            "lower_rate_expr": _expr_like_to_dict(entry.lower_rate_expr),
            "upper_rate_expr": _expr_like_to_dict(entry.upper_rate_expr),
        })
        return data
    elif isinstance(entry, FlipFlopLogic):
        data.update({
            "output_var_name": entry.output_var_name,
            "set_expr": _expr_like_to_dict(entry.set_expr),
            "reset_expr": _expr_like_to_dict(entry.reset_expr),
        })
        return data
    elif isinstance(entry, AnalogFlipFlopLogic):
        data.update({
            "output_var_name": entry.output_var_name,
            "input_expr": _expr_like_to_dict(entry.input_expr),
            "set_expr": _expr_like_to_dict(entry.set_expr),
            "reset_expr": _expr_like_to_dict(entry.reset_expr),
        })
        return data
    elif isinstance(entry, PickupDropoffLogic):
        data.update({
            "output_var_name": entry.output_var_name,
            "bool_expr": _expr_like_to_dict(entry.bool_expr),
            "pickup_delay_expr": _expr_like_to_dict(entry.pickup_delay_expr),
            "drop_delay_expr": _expr_like_to_dict(entry.drop_delay_expr),
        })
        return data
    elif isinstance(entry, ResetOnRisingEdgeLogic):
        data.update({
            "target_var_name": entry.target_var_name,
            "reset_expr": _expr_like_to_dict(entry.reset_expr),
            "value_expr": _expr_like_to_dict(entry.value_expr),
        })
        return data
    elif isinstance(entry, DelayedThresholdLatchLogic):
        data.update({
            "monitored_var_name": entry.monitored_var_name,
            "mode_var_name": entry.mode_var_name,
            "threshold": entry.threshold,
            "delay": entry.delay,
            "reset_delay": entry.reset_delay,
        })
        return data
    elif isinstance(entry, StartupHandoverLogic):
        data.update({
            "mode_var_name": entry.mode_var_name,
            "enable_time_var_name": entry.enable_time_var_name,
        })
        return data
    elif isinstance(entry, ValveStateLogic):
        data.update({
            "mode_var_name": entry.mode_var_name,
            "valve_type_var_name": entry.valve_type_var_name,
            "gate_var_name": entry.gate_var_name,
            "antiparallel_var_name": entry.antiparallel_var_name,
            "voltage_eps_var_name": entry.voltage_eps_var_name,
            "current_eps_var_name": entry.current_eps_var_name,
            "valve_voltage_var_name": entry.valve_voltage_var_name,
            "valve_current_var_name": entry.valve_current_var_name,
        })
        return data
    elif isinstance(entry, ThreePhaseCarrierPwmLogic):
        data.update({
            "mod_a_var_name": entry.mod_a_var_name,
            "mod_b_var_name": entry.mod_b_var_name,
            "mod_c_var_name": entry.mod_c_var_name,
            "gate_a_mode_var_name": entry.gate_a_mode_var_name,
            "gate_b_mode_var_name": entry.gate_b_mode_var_name,
            "gate_c_mode_var_name": entry.gate_c_mode_var_name,
            "omega_sw_var_name": entry.omega_sw_var_name,
            "carrier_phase_var_name": entry.carrier_phase_var_name,
        })
        return data
    else:
        raise ValueError(f"Unsupported procedural logic entry '{type(entry).__name__}'")


def _fixed_sample_logic_from_dict(data: ProceduralLogicData) -> FixedSampleLogic:
    """
    Deserialize one fixed-sample procedural logic entry.

    :param data: Serialized logic dictionary.
    :return: Fixed-sample procedural logic entry.
    """
    return FixedSampleLogic(
        output_var_name=str(data["output_var_name"]),
        condition_expr=_expr_like_from_dict(_get_expr_like_field(data, "condition_expr")),
        name=str(data.get("name", "")),
    )


def _sampled_value_logic_from_dict(data: ProceduralLogicData) -> SampledValueLogic:
    """
    Deserialize one sampled-value procedural logic entry.

    :param data: Serialized logic dictionary.
    :return: Sampled-value procedural logic entry.
    """
    return SampledValueLogic(
        output_var_name=str(data["output_var_name"]),
        source_expr=_expr_like_from_dict(_get_expr_like_field(data, "source_expr")),
        name=str(data.get("name", "")),
    )


def _hard_saturation_logic_from_dict(data: ProceduralLogicData) -> HardSaturationLogic:
    return HardSaturationLogic(
        output_var_name=str(data["output_var_name"]),
        u_expr=_expr_like_from_dict(_get_expr_like_field(data, "u_expr")),
        u_min_expr=_expr_like_from_dict(_get_expr_like_field(data, "u_min_expr")),
        u_max_expr=_expr_like_from_dict(_get_expr_like_field(data, "u_max_expr")),
        name=str(data.get("name", "")),
    )


def _time_delay_logic_from_dict(data: ProceduralLogicData) -> TimeDelayLogic:
    return TimeDelayLogic(
        output_var_name=str(data["output_var_name"]),
        source_expr=_expr_like_from_dict(_get_expr_like_field(data, "source_expr")),
        delay_expr=_expr_like_from_dict(_get_expr_like_field(data, "delay_expr")),
        name=str(data.get("name", "")),
    )


def _moving_average_logic_from_dict(data: ProceduralLogicData) -> MovingAverageLogic:
    return MovingAverageLogic(
        output_var_name=str(data["output_var_name"]),
        source_expr=_expr_like_from_dict(_get_expr_like_field(data, "source_expr")),
        delay_expr=_expr_like_from_dict(_get_expr_like_field(data, "delay_expr")),
        window_expr=_expr_like_from_dict(_get_expr_like_field(data, "window_expr")),
        name=str(data.get("name", "")),
    )


def _gradient_limiter_logic_from_dict(data: ProceduralLogicData) -> GradientLimiterLogic:
    return GradientLimiterLogic(
        output_var_name=str(data["output_var_name"]),
        source_expr=_expr_like_from_dict(_get_expr_like_field(data, "source_expr")),
        lower_rate_expr=_expr_like_from_dict(_get_expr_like_field(data, "lower_rate_expr")),
        upper_rate_expr=_expr_like_from_dict(_get_expr_like_field(data, "upper_rate_expr")),
        name=str(data.get("name", "")),
    )


def _flipflop_logic_from_dict(data: ProceduralLogicData) -> FlipFlopLogic:
    """
    Deserialize one flip-flop procedural logic entry.

    :param data: Serialized logic dictionary.
    :return: Flip-flop procedural logic entry.
    """
    return FlipFlopLogic(
        output_var_name=str(data["output_var_name"]),
        set_expr=_expr_like_from_dict(_get_expr_like_field(data, "set_expr")),
        reset_expr=_expr_like_from_dict(_get_expr_like_field(data, "reset_expr")),
        name=str(data.get("name", "")),
    )


def _analog_flipflop_logic_from_dict(data: ProceduralLogicData) -> AnalogFlipFlopLogic:
    """
    Deserialize one analog flip-flop procedural logic entry.

    :param data: Serialized logic dictionary.
    :return: Analog flip-flop procedural logic entry.
    """
    return AnalogFlipFlopLogic(
        output_var_name=str(data["output_var_name"]),
        input_expr=_expr_like_from_dict(_get_expr_like_field(data, "input_expr")),
        set_expr=_expr_like_from_dict(_get_expr_like_field(data, "set_expr")),
        reset_expr=_expr_like_from_dict(_get_expr_like_field(data, "reset_expr")),
        name=str(data.get("name", "")),
    )


def _pickup_dropoff_logic_from_dict(data: ProceduralLogicData) -> PickupDropoffLogic:
    """
    Deserialize one pickup/dropoff procedural logic entry.

    :param data: Serialized logic dictionary.
    :return: Pickup/dropoff procedural logic entry.
    """
    return PickupDropoffLogic(
        output_var_name=str(data["output_var_name"]),
        bool_expr=_expr_like_from_dict(_get_expr_like_field(data, "bool_expr")),
        pickup_delay_expr=_expr_like_from_dict(_get_expr_like_field(data, "pickup_delay_expr")),
        drop_delay_expr=_expr_like_from_dict(_get_expr_like_field(data, "drop_delay_expr")),
        name=str(data.get("name", "")),
    )


def _reset_on_rising_edge_logic_from_dict(data: ProceduralLogicData) -> ResetOnRisingEdgeLogic:
    """
    Deserialize one reset-on-rising-edge procedural logic entry.

    :param data: Serialized logic dictionary.
    :return: Reset-on-rising-edge procedural logic entry.
    """
    return ResetOnRisingEdgeLogic(
        target_var_name=str(data["target_var_name"]),
        reset_expr=_expr_like_from_dict(_get_expr_like_field(data, "reset_expr")),
        value_expr=_expr_like_from_dict(_get_expr_like_field(data, "value_expr")),
        name=str(data.get("name", "")),
    )


def _delayed_threshold_latch_logic_from_dict(data: ProceduralLogicData) -> DelayedThresholdLatchLogic:
    """
    Deserialize one delayed-threshold-latch procedural logic entry.

    :param data: Serialized logic dictionary.
    :return: Delayed-threshold-latch procedural logic entry.
    """
    reset_delay_raw: Any = data.get("reset_delay", None)
    reset_delay_value: Optional[float] = None if reset_delay_raw is None else float(reset_delay_raw)
    threshold_value: float = float(data["threshold"])
    delay_value: float = float(data["delay"])
    return DelayedThresholdLatchLogic(
        monitored_var_name=str(data["monitored_var_name"]),
        mode_var_name=str(data["mode_var_name"]),
        threshold=threshold_value,
        delay=delay_value,
        reset_delay=reset_delay_value,
        name=str(data.get("name", "")),
    )


def _startup_handover_logic_from_dict(data: ProceduralLogicData) -> StartupHandoverLogic:
    """
    Deserialize one startup-handover procedural logic entry.

    :param data: Serialized logic dictionary.
    :return: Startup-handover procedural logic entry.
    """
    return StartupHandoverLogic(
        mode_var_name=str(data["mode_var_name"]),
        enable_time_var_name=str(data["enable_time_var_name"]),
        name=str(data.get("name", "")),
    )


def _valve_state_logic_from_dict(data: ProceduralLogicData) -> ValveStateLogic:
    """
    Deserialize one retained valve-state procedural logic entry.

    :param data: Serialized logic dictionary.
    :return: Valve-state procedural logic entry.
    """
    return ValveStateLogic(
        mode_var_name=str(data["mode_var_name"]),
        valve_type_var_name=str(data["valve_type_var_name"]),
        gate_var_name=str(data["gate_var_name"]),
        antiparallel_var_name=str(data["antiparallel_var_name"]),
        voltage_eps_var_name=str(data["voltage_eps_var_name"]),
        current_eps_var_name=str(data["current_eps_var_name"]),
        valve_voltage_var_name=str(data["valve_voltage_var_name"]),
        valve_current_var_name=str(data["valve_current_var_name"]),
        name=str(data.get("name", "")),
    )


def _three_phase_carrier_pwm_logic_from_dict(data: ProceduralLogicData) -> ThreePhaseCarrierPwmLogic:
    """
    Deserialize one three-phase carrier PWM procedural logic entry.

    :param data: Serialized logic dictionary.
    :return: Three-phase carrier PWM procedural logic entry.
    """
    return ThreePhaseCarrierPwmLogic(
        mod_a_var_name=str(data["mod_a_var_name"]),
        mod_b_var_name=str(data["mod_b_var_name"]),
        mod_c_var_name=str(data["mod_c_var_name"]),
        gate_a_mode_var_name=str(data["gate_a_mode_var_name"]),
        gate_b_mode_var_name=str(data["gate_b_mode_var_name"]),
        gate_c_mode_var_name=str(data["gate_c_mode_var_name"]),
        omega_sw_var_name=str(data["omega_sw_var_name"]),
        carrier_phase_var_name=str(data["carrier_phase_var_name"]),
        name=str(data.get("name", "")),
    )


def build_procedural_logic_entry(data: ProceduralLogicData) -> ProceduralLogicBase:
    """
    Deserialize one procedural logic entry.

    :param data: Serialized logic config.
    :return: Procedural logic object.
    """
    logic_tpe_text: str = str(data.get("logic_type", data.get("logic_tpe", "")))
    logic_tpe: ProceduralLogicType = ProceduralLogicType(logic_tpe_text)

    if logic_tpe == ProceduralLogicType.FixedSample:
        return _fixed_sample_logic_from_dict(data)
    elif logic_tpe == ProceduralLogicType.SampledValue:
        return _sampled_value_logic_from_dict(data)
    elif logic_tpe == ProceduralLogicType.HardSaturation:
        return _hard_saturation_logic_from_dict(data)
    elif logic_tpe == ProceduralLogicType.TimeDelay:
        return _time_delay_logic_from_dict(data)
    elif logic_tpe == ProceduralLogicType.MovingAverage:
        return _moving_average_logic_from_dict(data)
    elif logic_tpe == ProceduralLogicType.GradientLimiter:
        return _gradient_limiter_logic_from_dict(data)
    elif logic_tpe == ProceduralLogicType.FlipFlop:
        return _flipflop_logic_from_dict(data)
    elif logic_tpe == ProceduralLogicType.AnalogFlipFlop:
        return _analog_flipflop_logic_from_dict(data)
    elif logic_tpe == ProceduralLogicType.PickupDropoff:
        return _pickup_dropoff_logic_from_dict(data)
    elif logic_tpe == ProceduralLogicType.ResetOnRisingEdge:
        return _reset_on_rising_edge_logic_from_dict(data)
    elif logic_tpe == ProceduralLogicType.DelayedThresholdLatch:
        return _delayed_threshold_latch_logic_from_dict(data)
    elif logic_tpe == ProceduralLogicType.StartupHandover:
        return _startup_handover_logic_from_dict(data)
    elif logic_tpe == ProceduralLogicType.ValveState:
        return _valve_state_logic_from_dict(data)
    elif logic_tpe == ProceduralLogicType.ThreePhaseCarrierPwm:
        return _three_phase_carrier_pwm_logic_from_dict(data)
    else:
        raise ValueError(f"Unsupported procedural logic type '{logic_tpe_text}'")


def procedural_logic_to_dict(entries: List[ProceduralLogicBase]) -> List[ProceduralLogicData]:
    """
    Serialize a list of procedural logic entries.

    :param entries: Logic entries.
    :return: Serialized representation.
    """
    return [procedural_logic_entry_to_dict(entry) for entry in entries]


def procedural_logic_from_dict(entries: List[ProceduralLogicData]) -> List[ProceduralLogicBase]:
    """
    Deserialize a list of procedural logic entries.

    :param entries: Serialized entries.
    :return: Procedural logic objects.
    """
    normalized_entries: List[ProceduralLogicBase] = list()
    item: Any

    for item in entries:
        if isinstance(item, ProceduralLogicBase):
            normalized_entries.append(item)
        else:
            normalized_entries.append(build_procedural_logic_entry(item))

    return normalized_entries


def clone_procedural_logic_entries(entries: List[ProceduralLogicBase], var_mapping: VarRemap) -> List[ProceduralLogicBase]:
    """
    Clone procedural logic entries under a variable remapping.

    :param entries: Source procedural logic entries.
    :param var_mapping: Mapping from old variables/names to remapped expressions.
    :return: Remapped procedural logic entries.
    """
    return [entry.remap(var_mapping) for entry in entries]


def build_boundary_updater_from_block(problem: EmtProblemTemplate) -> Optional[BlockProceduralLogicUpdater]:
    """
    Build a boundary updater from the full procedural logic attached to ``problem.sys_block``.

    :param problem: EMT problem containing the root block.
    :return: Boundary updater or None.
    """
    entries: List[Any] = list()
    block: Block
    for block in problem.sys_block.get_all_blocks():
        entries.extend(block.procedural_logic)

    if len(entries) == 0:
        return None
    return BlockProceduralLogicUpdater(problem, procedural_logic_from_dict(entries))
