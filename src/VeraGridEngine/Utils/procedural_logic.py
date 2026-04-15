# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Simulations.EMT.solvers.jit_symbolic_solver import BoundaryUpdateWrapper
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import CmpOp, Comparison, Const, Expr, Var
from VeraGridEngine.basic_structures import Vec
from VeraGridEngine.enumerations import ProceduralLogicType


def _expr_like_to_dict(expr: Expr | Comparison) -> Dict[str, Any]:
    """
    Serialize a symbolic expression or comparison used by procedural logic.

    :param expr: Procedural expression to serialize.
    :return: Dictionary with enough information to rebuild the expression later.
    """
    if isinstance(expr, Comparison):
        rhs: Expr | float | int | complex = expr.rhs
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
    return {
        "kind": "Expr",
        "expr": expr.to_dict(),
    }


def _expr_like_from_dict(data: Dict[str, Any]) -> Expr | Comparison:
    """
    Deserialize a symbolic expression or comparison used by procedural logic.

    :param data: Serialized expression dictionary.
    :return: Reconstructed symbolic expression or comparison.
    """
    kind: str = str(data.get("kind", "Expr"))
    if kind == "Expr":
        return Expr.from_dict(data["expr"])

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


def _subs_expr_like(expr: Expr | Comparison, mapping: Dict[Expr | str, Expr]) -> Expr | Comparison:
    """
    Apply a variable substitution to a procedural expression.

    :param expr: Expression or comparison to remap.
    :param mapping: Variable substitution map.
    :return: Remapped expression.
    """
    if isinstance(expr, Comparison):
        rhs: Expr | float | int = expr.rhs.subs(mapping) if isinstance(expr.rhs, Expr) else expr.rhs
        return Comparison(lhs=expr.lhs.subs(mapping), op=expr.op, rhs=rhs)
    return expr.subs(mapping)


def _build_name_mapping(var_mapping: Dict[Expr | str, Expr]) -> Dict[str, str]:
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


def _get_expr_like_field(data: Dict[str, Any], key: str) -> Dict[str, Any]:
    """
    Return one serialized procedural-expression field as a dictionary.

    :param data: Serialized procedural logic dictionary.
    :param key: Field name containing one serialized expression.
    :return: Serialized expression dictionary.
    """
    field_data: Dict[str, Any] = data[key]
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

    __slots__ = ["name", "_problem", "_sample_time"]
    logic_tpe = ProceduralLogicType.Base  # TODO: WTF is this? remove

    def __init__(self, name: str = "") -> None:
        self.name = name
        self._problem: Optional[EmtProblemTemplate] = None
        self._sample_time: Optional[float] = None

    def bind(self, problem: EmtProblemTemplate) -> None:
        """
        Bind the logic to a concrete EMT problem.

        :param problem: EMT problem owning the block and variable maps.
        :return: None
        """
        self._problem = problem
        self._sample_time = None

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

    def remap(self, var_mapping: Dict[Expr | str, Expr]) -> "ProceduralLogicBase":
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

        expr_eval: Expr = expr.to_expression() if isinstance(expr, Comparison) else expr

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

        uid_bindings: Dict[int, float] = dict()
        # Build a full UID lookup only for composite expressions.
        for uid, idx in problem.uid2idx_vars.items():
            uid_bindings[uid] = float(x[idx])

        for uid, idx in problem.uid2idx_event_params.items():
            uid_bindings[uid] = float(params[idx])

        n_runtime = problem.get_variable_parameter_number()
        const_values = problem.get_parameters_values()
        params_has_consts = len(params) >= n_runtime + len(const_values)
        for uid, idx in problem.uid2idx_params.items():
            if params_has_consts:
                uid_bindings[uid] = float(params[n_runtime + idx])
            else:
                uid_bindings[uid] = float(const_values[idx].value)

        uid_bindings[problem.glob_time.uid] = sample_time
        for var in expr_eval.get_vars():
            if var.name in {"time", "glob_time"}:
                uid_bindings[var.uid] = sample_time

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


class FixedSampleLogic(ProceduralLogicBase):
    """
    Retain the initial truth value of one condition in a runtime mode variable.
    """

    __slots__ = ["output_var_name", "condition_expr", "output_idx", "initialized"]
    logic_tpe = ProceduralLogicType.FixedSample # TODO: Remove

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

    def remap(self, var_mapping: Dict[Expr | str, Expr]) -> "FixedSampleLogic":
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

    __slots__ = ["output_var_name", "source_expr", "output_idx"]
    logic_tpe = ProceduralLogicType.SampledValue  # TODO: remove

    def __init__(self, output_var_name: str, source_expr: Expr | Comparison, name: str = "") -> None:
        super().__init__(name=name)
        self.output_var_name = output_var_name
        self.source_expr = source_expr
        self.output_idx = -1

    def bind(self, problem: EmtProblemTemplate) -> None:
        """
        Resolve the runtime output slot for this sampled value.

        :param problem: Bound EMT problem.
        :return: None
        """
        super().bind(problem)
        output_var = _find_var_by_name(problem.sys_block, self.output_var_name)
        self.output_idx = int(problem.uid2idx_event_params[output_var.uid])

    def update(self, t: float, x: Vec, params: Vec) -> None:
        """
        Refresh the sampled value using the accepted state.

        :param t: Current solver time.
        :param x: Accepted state vector.
        :param params: Runtime parameter vector.
        :return: None
        """
        params[self.output_idx] = self._eval_numeric(self.source_expr, t, x, params)

    def remap(self, var_mapping: Dict[Expr | str, Expr]) -> "SampledValueLogic":
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


class FlipFlopLogic(ProceduralLogicBase):
    """
    Store a binary set/reset latch in a runtime mode variable.
    """

    __slots__ = ["output_var_name", "set_expr", "reset_expr", "output_idx", "state", "initialized"]
    logic_tpe = ProceduralLogicType.FlipFlop  # TODO: remove

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

    def remap(self, var_mapping: Dict[Expr | str, Expr]) -> "FlipFlopLogic":
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
    logic_tpe = ProceduralLogicType.AnalogFlipFlop  # TODO: remove

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

    def remap(self, var_mapping: Dict[Expr | str, Expr]) -> "AnalogFlipFlopLogic":
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
    logic_tpe = ProceduralLogicType.PickupDropoff  # TODO: remove

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

    def remap(self, var_mapping: Dict[Expr | str, Expr]) -> "PickupDropoffLogic":
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
    logic_tpe = ProceduralLogicType.ResetOnRisingEdge  # TODO: remove

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

    def remap(self, var_mapping: Dict[Expr | str, Expr]) -> "ResetOnRisingEdgeLogic":
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


def lastvalue(input_expr: Expr | Comparison, output: Var | str, name: str = "") -> SampledValueLogic:
    """
    Build the procedural equivalent of PowerFactory ``lastvalue``.

    :param input_expr: Source expression to be sampled.
    :param output: Runtime mode variable receiving the sampled value.
    :param name: Optional logic name.
    :return: Sampled-value procedural logic entry.
    """
    return sampled_value(output=output, source=input_expr, name=name)


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

    def remap(self, var_mapping: Dict[Expr | str, Expr]) -> "DelayedThresholdLatchLogic":
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


def _base_logic_data(entry: ProceduralLogicBase) -> Dict[str, Any]:
    """
    Serialize the common metadata shared by all procedural logic entries.

    :param entry: Procedural logic entry.
    :return: Serialized common metadata.
    """
    return {
        "logic_type": entry.logic_tpe.value,
        "name": entry.name,
    }


def procedural_logic_entry_to_dict(entry: ProceduralLogicBase) -> Dict[str, Any]:
    """
    Serialize one procedural logic entry.

    :param entry: Procedural logic entry.
    :return: Serialized logic dictionary.
    """
    data: Dict[str, Any] = _base_logic_data(entry)

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
    else:
        raise ValueError(f"Unsupported procedural logic entry '{type(entry).__name__}'")


def _fixed_sample_logic_from_dict(data: Dict[str, Any]) -> FixedSampleLogic:
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


def _sampled_value_logic_from_dict(data: Dict[str, Any]) -> SampledValueLogic:
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


def _flipflop_logic_from_dict(data: Dict[str, Any]) -> FlipFlopLogic:
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


def _analog_flipflop_logic_from_dict(data: Dict[str, Any]) -> AnalogFlipFlopLogic:
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


def _pickup_dropoff_logic_from_dict(data: Dict[str, Any]) -> PickupDropoffLogic:
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


def _reset_on_rising_edge_logic_from_dict(data: Dict[str, Any]) -> ResetOnRisingEdgeLogic:
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


def _delayed_threshold_latch_logic_from_dict(data: Dict[str, Any]) -> DelayedThresholdLatchLogic:
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


def build_procedural_logic_entry(data: Dict[str, Any]) -> ProceduralLogicBase:
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
    else:
        raise ValueError(f"Unsupported procedural logic type '{logic_tpe_text}'")


def procedural_logic_to_dict(entries: List[ProceduralLogicBase]) -> List[Dict[str, Any]]:
    """
    Serialize a list of procedural logic entries.

    :param entries: Logic entries.
    :return: Serialized representation.
    """
    return [procedural_logic_entry_to_dict(entry) for entry in entries]


def procedural_logic_from_dict(entries: List[Dict[str, Any]]) -> List[ProceduralLogicBase]:
    """
    Deserialize a list of procedural logic entries.

    :param entries: Serialized entries.
    :return: Procedural logic objects.
    """
    return [build_procedural_logic_entry(item) for item in entries]


def clone_procedural_logic_entries(entries: List[ProceduralLogicBase],
                                   var_mapping: Dict[Expr | str, Expr]) -> List[ProceduralLogicBase]:
    """
    Clone procedural logic entries under a variable remapping.

    :param entries: Source procedural logic entries.
    :param var_mapping: Mapping from old variables/names to remapped expressions.
    :return: Remapped procedural logic entries.
    """
    return [entry.remap(var_mapping) for entry in entries]


def build_boundary_updater_from_block(problem: EmtProblemTemplate) -> Optional[BlockProceduralLogicUpdater]:
    """
    Build a boundary updater from ``problem.sys_block.procedural_logic``.

    :param problem: EMT problem containing the root block.
    :return: Boundary updater or None.
    """
    entries: List[ProceduralLogicBase] = problem.sys_block.procedural_logic
    if len(entries) == 0:
        return None
    return BlockProceduralLogicUpdater(problem=problem,
                                       logic_entries=entries)
