# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from . import compat
from .config import ExportConfig
from .profile import assert_block_supported_for_me

Const = compat.Const
_expr_to_dict = compat._expr_to_dict


class VariableCategory(str, Enum):
    STATE = "state"
    DERIVATIVE = "derivative"
    ALGEBRAIC = "algebraic"
    INPUT = "input"
    CONST_PARAM = "const_param"
    RUNTIME_PARAM = "runtime_param"


class RuntimeGroup(str, Enum):
    EVENT = "event"
    MODE = "mode"


class EquationGroup(str, Enum):
    DERIVATIVE = "derivative"
    ALGEBRAIC = "algebraic"
    RUNTIME_INIT = "runtime_init"
    INIT = "init"
    DIFF_INIT = "diff_init"


class StorageSegment(str, Enum):
    STATES = "states"
    DERIVATIVES = "derivatives"
    ALGEBRAICS = "algebraics"
    INPUTS = "inputs"
    CONST_PARAMS = "const_params"
    RUNTIME_PARAMS = "runtime_params"


@dataclass(frozen=True, slots=True)
class ExportLogicEntry:
    index: int
    logic_type: str
    name: str
    data: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ExportEventIndicator:
    index: int
    name: str
    source_logic_index: int
    expr_data: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ExportVariable:
    name: str
    uid: int
    category: VariableCategory
    storage_segment: StorageSegment
    storage_index: int
    fmi_type: str
    causality: str
    variability: str
    initial: str | None
    start: float | None
    nominal: float | None
    value_reference: int
    derivative_of_uid: int | None = None
    runtime_group: RuntimeGroup | None = None


@dataclass(frozen=True, slots=True)
class ExportEquation:
    group: EquationGroup
    index: int
    target_uid: int | None
    target_name: str | None
    expression: Any


@dataclass(frozen=True, slots=True)
class ExportModel:
    schema_version: int
    model_name: str
    model_identifier: str
    guid: str
    relative_tolerance: float
    default_step_size: float
    variables: tuple[ExportVariable, ...]
    equations: tuple[ExportEquation, ...]
    logic_entries: tuple[ExportLogicEntry, ...]
    event_indicators: tuple[ExportEventIndicator, ...]
    source_snapshot: dict[str, Any]
    counts: dict[str, int] = field(default_factory=dict)

    def variable_by_uid(self, uid: int) -> ExportVariable:
        for variable in self.variables:
            if variable.uid == uid:
                return variable
        raise KeyError(uid)

    def xml_variables(self) -> tuple[ExportVariable, ...]:
        return self.variables

    def output_variables(self) -> tuple[ExportVariable, ...]:
        return tuple(variable for variable in self.variables if variable.causality == "output")

    def state_variables(self) -> tuple[ExportVariable, ...]:
        return tuple(variable for variable in self.variables if variable.category == VariableCategory.STATE)

    def derivative_variables(self) -> tuple[ExportVariable, ...]:
        return tuple(variable for variable in self.variables if variable.category == VariableCategory.DERIVATIVE)

    def initial_unknown_variables(self) -> tuple[ExportVariable, ...]:
        result: list[ExportVariable] = []
        for variable in self.variables:
            if variable.causality == "output" and variable.initial in {"approx", "calculated"}:
                result.append(variable)
        for variable in self.derivative_variables():
            if variable.initial in {"approx", "calculated"}:
                result.append(variable)
            state = self.variable_by_uid(variable.derivative_of_uid) if variable.derivative_of_uid is not None else None
            if state is not None and state.initial in {"approx", "calculated"}:
                result.append(state)
        unique: list[ExportVariable] = []
        seen: set[int] = set()
        for variable in result:
            if variable.uid not in seen:
                unique.append(variable)
                seen.add(variable.uid)
        return tuple(unique)

    def needs_completed_integrator_step(self) -> bool:
        return any(entry.logic_type == "sampled_value" for entry in self.logic_entries)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "model_name": self.model_name,
            "model_identifier": self.model_identifier,
            "guid": self.guid,
            "relative_tolerance": self.relative_tolerance,
            "default_step_size": self.default_step_size,
            "variables": [
                {
                    "name": variable.name,
                    "uid": variable.uid,
                    "category": variable.category.value,
                    "storage_segment": variable.storage_segment.value,
                    "storage_index": variable.storage_index,
                    "fmi_type": variable.fmi_type,
                    "causality": variable.causality,
                    "variability": variable.variability,
                    "initial": variable.initial,
                    "start": variable.start,
                    "nominal": variable.nominal,
                    "value_reference": variable.value_reference,
                    "derivative_of_uid": variable.derivative_of_uid,
                    "runtime_group": None if variable.runtime_group is None else variable.runtime_group.value,
                }
                for variable in self.variables
            ],
            "equations": [
                {
                    "group": equation.group.value,
                    "index": equation.index,
                    "target_uid": equation.target_uid,
                    "target_name": equation.target_name,
                    "expression": _expr_to_dict(equation.expression),
                }
                for equation in self.equations
            ],
            "logic_entries": [dict(entry.data) for entry in self.logic_entries],
            "event_indicators": [
                {
                    "index": indicator.index,
                    "name": indicator.name,
                    "source_logic_index": indicator.source_logic_index,
                    "expr_data": indicator.expr_data,
                }
                for indicator in self.event_indicators
            ],
            "counts": dict(self.counts),
            "source_snapshot": self.source_snapshot,
        }


def _const_value(expr: Any) -> float | None:
    if isinstance(expr, Const):
        value = expr.value
        if value is not None:
            return float(value)
    return None


def _sorted_param_items(mapping: Any) -> list[tuple[Any, Any]]:
    return sorted(mapping.items(), key=lambda item: (item[0].name, item[0].uid))


def _get_param_start_value(var: Any, block: Any) -> float | None:
    """Get the start value of a parameter variable from event_dict or parameters."""
    for mapping in [block.event_dict, block.parameters]:
        for param_var, value in mapping.items():
            if param_var.uid == var.uid and isinstance(value, Const) and value.value is not None:
                return float(value.value)
    return None


def _state_start_map(block: Any) -> dict[int, float]:
    """Get start values for state variables from init_values or init_eqs."""
    result: dict[int, float] = {}
    
    # First, get explicit start values from init_values
    for var, value in block.init_values.items():
        if isinstance(value, Const) and value.value is not None:
            result[var.uid] = float(value.value)
    
    # Then, evaluate init_eqs for simple equations like vdc_state = Vdc_ref
    if hasattr(block, 'init_eqs') and block.init_eqs:
        for state_var, expr in block.init_eqs.items():
            if state_var.uid in result:
                continue  # Already has explicit start value
            
            # Check if expression is a simple Var reference (e.g., vdc_state = Vdc_ref)
            if hasattr(expr, 'name') and hasattr(expr, 'base_var') and expr.base_var is None:
                # This is a simple Var reference
                param_start = _get_param_start_value(expr, block)
                if param_start is not None:
                    result[state_var.uid] = param_start
    
    return result


def _known_internal_uids(block: Any) -> set[int]:
    known = {var.uid for var in block.state_vars + block.algebraic_vars + block.diff_vars}
    known.update(var.uid for var in block.parameters.keys())
    known.update(var.uid for var in block.event_dict.keys())
    known.update(var.uid for var in block.mode_dict.keys())
    return known


def _collect_output_vars(flat_block: Any) -> list[Any]:
    outputs: list[Any] = []
    seen: set[int] = set()
    for var in getattr(flat_block, "out_vars", []) or []:
        uid = int(var.uid)
        if uid not in seen:
            outputs.append(var)
            seen.add(uid)
    input_uids = {int(var.uid) for var in getattr(flat_block, "in_vars", []) or []}
    external_mapping = getattr(flat_block, "external_mapping", {}) or {}
    for _, var in sorted(external_mapping.items(), key=lambda item: str(item[0])):
        if not hasattr(var, "uid"):
            continue
        uid = int(var.uid)
        if uid in seen or uid in input_uids:
            continue
        outputs.append(var)
        seen.add(uid)
    return sorted(outputs, key=lambda item: (item.name, item.uid))


def _root_base_uid(var: Any) -> int | None:
    base = getattr(var, "base_var", None)
    if base is None:
        return None
    while getattr(base, "base_var", None) is not None:
        base = base.base_var
    return int(base.uid)


def _next_vr(counter: list[int]) -> int:
    value = counter[0]
    counter[0] += 1
    return value


def _make_variable(
    *,
    var: Any,
    category: VariableCategory,
    storage_segment: StorageSegment,
    storage_index: int,
    causality: str,
    variability: str,
    initial: str | None,
    start: float | None,
    nominal: float | None,
    value_reference: int,
    derivative_of_uid: int | None = None,
    runtime_group: RuntimeGroup | None = None,
) -> ExportVariable:
    return ExportVariable(
        name=var.name,
        uid=var.uid,
        category=category,
        storage_segment=storage_segment,
        storage_index=storage_index,
        fmi_type="Real",
        causality=causality,
        variability=variability,
        initial=initial,
        start=start,
        nominal=nominal,
        value_reference=value_reference,
        derivative_of_uid=derivative_of_uid,
        runtime_group=runtime_group,
    )


def _build_event_indicators(logic_entries: tuple[ExportLogicEntry, ...]) -> tuple[ExportEventIndicator, ...]:
    indicators: list[ExportEventIndicator] = []
    next_index = 0
    for entry in logic_entries:
        if entry.logic_type == "flipflop":
            indicators.append(
                ExportEventIndicator(
                    index=next_index,
                    name=f"{entry.name or 'flipflop'}_set",
                    source_logic_index=entry.index,
                    expr_data=dict(entry.data["set_expr"]),
                )
            )
            next_index += 1
            indicators.append(
                ExportEventIndicator(
                    index=next_index,
                    name=f"{entry.name or 'flipflop'}_reset",
                    source_logic_index=entry.index,
                    expr_data=dict(entry.data["reset_expr"]),
                )
            )
            next_index += 1
    return tuple(indicators)


def build_export_model(
    flat_block: Any,
    cfg: ExportConfig,
    snapshot: dict[str, Any],
    logic_entries: tuple[ExportLogicEntry, ...],
) -> ExportModel:
    assert_block_supported_for_me(flat_block)

    init_starts = _state_start_map(flat_block)
    output_vars = _collect_output_vars(flat_block)
    output_uids = {var.uid for var in output_vars}
    known_internal_uids = _known_internal_uids(flat_block)
    input_vars = sorted([var for var in flat_block.in_vars if var.uid not in known_internal_uids], key=lambda item: (item.name, item.uid))
    event_indicators = _build_event_indicators(logic_entries)

    state_by_uid = {int(var.uid): var for var in flat_block.state_vars}
    derivative_var_by_base_uid: dict[int, Any] = {}
    for diff_var in flat_block.diff_vars:
        base_uid = _root_base_uid(diff_var)
        if base_uid is None or base_uid not in state_by_uid:
            raise ValueError(f"Differential variable {diff_var.name!r} does not reference an exported state variable")
        if base_uid in derivative_var_by_base_uid:
            raise ValueError(f"Multiple differential variables reference the same state UID {base_uid}")
        derivative_var_by_base_uid[base_uid] = diff_var

    for state_var in flat_block.state_vars:
        if state_var.uid in derivative_var_by_base_uid:
            continue
        derivative_var_by_base_uid[state_var.uid] = compat.Var(name=f"d_{state_var.name}", base_var=state_var)

    variables: list[ExportVariable] = []
    equations: list[ExportEquation] = []
    next_vr = [0]

    for index, var in enumerate(input_vars):
        variables.append(
            _make_variable(
                var=var,
                category=VariableCategory.INPUT,
                storage_segment=StorageSegment.INPUTS,
                storage_index=index,
                causality="input",
                variability="continuous",
                initial="exact",
                start=0.0,
                nominal=1.0,
                value_reference=_next_vr(next_vr),
            )
        )

    for index, (var, value) in enumerate(_sorted_param_items(flat_block.parameters)):
        start = _const_value(value)
        if start is None:
            raise ValueError(f"Constant parameter {var.name!r} requires a concrete numeric value")
        variables.append(
            _make_variable(
                var=var,
                category=VariableCategory.CONST_PARAM,
                storage_segment=StorageSegment.CONST_PARAMS,
                storage_index=index,
                causality="parameter",
                variability="fixed",
                initial="exact",
                start=start,
                nominal=1.0,
                value_reference=_next_vr(next_vr),
            )
        )

    runtime_index = 0
    for runtime_group, mapping in ((RuntimeGroup.EVENT, flat_block.event_dict), (RuntimeGroup.MODE, flat_block.mode_dict)):
        for var, value in _sorted_param_items(mapping):
            start = _const_value(value) if isinstance(value, Const) else 0.0
            if start is None:
                start = 0.0
            variables.append(
                _make_variable(
                    var=var,
                    category=VariableCategory.RUNTIME_PARAM,
                    storage_segment=StorageSegment.RUNTIME_PARAMS,
                    storage_index=runtime_index,
                    causality="parameter",
                    variability="tunable",
                    initial="exact",
                    start=start,
                    nominal=1.0,
                    value_reference=_next_vr(next_vr),
                    runtime_group=runtime_group,
                )
            )
            equations.append(
                ExportEquation(
                    group=EquationGroup.RUNTIME_INIT,
                    index=runtime_index,
                    target_uid=var.uid,
                    target_name=var.name,
                    expression=value if isinstance(value, compat.Expr) else Const(float(value.value) if value.value is not None else 0.0),
                )
            )
            runtime_index += 1

    for index, var in enumerate(flat_block.state_vars):
        variables.append(
            _make_variable(
                var=var,
                category=VariableCategory.STATE,
                storage_segment=StorageSegment.STATES,
                storage_index=index,
                causality="output" if var.uid in output_uids else "local",
                variability="continuous",
                initial="exact",
                start=init_starts.get(var.uid, 0.0),
                nominal=1.0,
                value_reference=_next_vr(next_vr),
            )
        )

    for index, state_var in enumerate(flat_block.state_vars):
        diff_var = derivative_var_by_base_uid[state_var.uid]
        variables.append(
            _make_variable(
                var=diff_var,
                category=VariableCategory.DERIVATIVE,
                storage_segment=StorageSegment.DERIVATIVES,
                storage_index=index,
                causality="local",
                variability="continuous",
                initial="calculated",
                start=None,
                nominal=1.0,
                value_reference=_next_vr(next_vr),
                derivative_of_uid=state_var.uid,
            )
        )
        equations.append(
            ExportEquation(
                group=EquationGroup.DERIVATIVE,
                index=index,
                target_uid=diff_var.uid,
                target_name=diff_var.name,
                expression=flat_block.state_eqs[index],
            )
        )

    for index, var in enumerate(flat_block.algebraic_vars):
        variables.append(
            _make_variable(
                var=var,
                category=VariableCategory.ALGEBRAIC,
                storage_segment=StorageSegment.ALGEBRAICS,
                storage_index=index,
                causality="output" if var.uid in output_uids else "local",
                variability="continuous",
                initial="calculated",
                start=None,
                nominal=1.0,
                value_reference=_next_vr(next_vr),
            )
        )
        equations.append(
            ExportEquation(
                group=EquationGroup.ALGEBRAIC,
                index=index,
                target_uid=var.uid,
                target_name=var.name,
                expression=flat_block.algebraic_eqs[index],
            )
        )

    for index, (var, expr) in enumerate(sorted(flat_block.init_eqs.items(), key=lambda item: (item[0].name, item[0].uid))):
        equations.append(
            ExportEquation(
                group=EquationGroup.INIT,
                index=index,
                target_uid=var.uid,
                target_name=var.name,
                expression=expr,
            )
        )

    for index, (var, expr) in enumerate(sorted(flat_block.diff_init_eqs.items(), key=lambda item: (item[0].name, item[0].uid))):
        equations.append(
            ExportEquation(
                group=EquationGroup.DIFF_INIT,
                index=index,
                target_uid=var.uid,
                target_name=var.name,
                expression=expr,
            )
        )

    return ExportModel(
        schema_version=1,
        model_name=cfg.model_name,
        model_identifier=cfg.model_identifier or cfg.model_name,
        guid=cfg.guid,
        relative_tolerance=cfg.relative_tolerance,
        default_step_size=cfg.fixed_step,
        variables=tuple(variables),
        equations=tuple(equations),
        logic_entries=logic_entries,
        event_indicators=event_indicators,
        source_snapshot=snapshot,
        counts={
            "states": len(flat_block.state_vars),
            "derivatives": len(flat_block.state_vars),
            "algebraics": len(flat_block.algebraic_vars),
            "inputs": len(input_vars),
            "const_params": len(flat_block.parameters),
            "runtime_params": len(flat_block.event_dict) + len(flat_block.mode_dict),
            "outputs": len(output_vars),
            "event_indicators": len(event_indicators),
        },
    )
