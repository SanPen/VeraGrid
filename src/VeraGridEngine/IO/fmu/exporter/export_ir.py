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

Const = compat.Const
_expr_to_dict = compat._expr_to_dict


class VariableCategory(str, Enum):
    STATE = "state"
    ALGEBRAIC = "algebraic"
    DIFF = "diff"
    INPUT = "input"
    CONST_PARAM = "const_param"
    RUNTIME_PARAM = "runtime_param"


class RuntimeGroup(str, Enum):
    EVENT = "event"
    MODE = "mode"


class EquationGroup(str, Enum):
    STATE = "state"
    ALGEBRAIC = "algebraic"
    RUNTIME_INIT = "runtime_init"
    INIT = "init"
    DIFF_INIT = "diff_init"


class StorageSegment(str, Enum):
    STATES = "states"
    ALGEBRAICS = "algebraics"
    INPUTS = "inputs"
    CONST_PARAMS = "const_params"
    RUNTIME_PARAMS = "runtime_params"


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
    value_reference: int | None
    exposed: bool
    runtime_group: RuntimeGroup | None = None
    diff_base_uid: int | None = None
    history_index: int | None = None


@dataclass(frozen=True, slots=True)
class ExportEquation:
    group: EquationGroup
    index: int
    target_uid: int | None
    target_name: str | None
    expression: Any


@dataclass(frozen=True, slots=True)
class ExportOutput:
    name: str
    value_reference: int
    source_uid: int
    source_name: str
    storage_segment: StorageSegment
    storage_index: int
    start: float | None


@dataclass(frozen=True, slots=True)
class ExportLogicEntry:
    index: int
    logic_type: str
    name: str
    data: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ExportModel:
    schema_version: int
    model_name: str
    model_identifier: str
    guid: str
    fixed_step: float
    integration_method: str
    variables: tuple[ExportVariable, ...]
    outputs: tuple[ExportOutput, ...]
    equations: tuple[ExportEquation, ...]
    logic_entries: tuple[ExportLogicEntry, ...]
    source_snapshot: dict[str, Any]
    counts: dict[str, int] = field(default_factory=dict)

    def exposed_variables(self) -> tuple[ExportVariable, ...]:
        return tuple(variable for variable in self.variables if variable.exposed)

    def variable_by_uid(self, uid: int) -> ExportVariable:
        for variable in self.variables:
            if variable.uid == uid:
                return variable
        raise KeyError(uid)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "model_name": self.model_name,
            "model_identifier": self.model_identifier,
            "guid": self.guid,
            "fixed_step": self.fixed_step,
            "integration_method": self.integration_method,
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
                    "value_reference": variable.value_reference,
                    "exposed": variable.exposed,
                    "runtime_group": None if variable.runtime_group is None else variable.runtime_group.value,
                    "history_index": variable.history_index,
                }
                for variable in self.variables
            ],
            "outputs": [
                {
                    "name": output.name,
                    "value_reference": output.value_reference,
                    "source_uid": output.source_uid,
                    "source_name": output.source_name,
                    "storage_segment": output.storage_segment.value,
                    "storage_index": output.storage_index,
                    "start": output.start,
                }
                for output in self.outputs
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
            "logic_entries": [entry.data for entry in self.logic_entries],
            "counts": dict(self.counts),
            "source_snapshot": self.source_snapshot,
        }


def _const_value(expr: Any) -> float | None:
    if isinstance(expr, Const):
        value = expr.value
        if value is not None:
            return float(value)
    return None


def _state_start_map(block: Any) -> dict[int, float]:
    result: dict[int, float] = {}
    for var, value in block.init_values.items():
        if isinstance(value, Const) and value.value is not None:
            result[var.uid] = float(value.value)
    return result


def _known_internal_uids(block: Any) -> set[int]:
    known = {var.uid for var in block.state_vars + block.algebraic_vars + block.diff_vars}
    known.update(var.uid for var in block.parameters.keys())
    known.update(var.uid for var in block.event_dict.keys())
    known.update(var.uid for var in block.mode_dict.keys())
    return known


def _sorted_param_items(mapping: Any) -> list[tuple[Any, Any]]:
    return sorted(mapping.items(), key=lambda item: (item[0].name, item[0].uid))


def _make_variable(
    *,
    var: Any,
    category: VariableCategory,
    storage_segment: StorageSegment,
    storage_index: int,
    exposed: bool,
    start: float | None,
    value_reference: int | None,
    causality: str,
    variability: str,
    initial: str | None,
    runtime_group: RuntimeGroup | None = None,
    diff_base_uid: int | None = None,
    history_index: int | None = None,
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
        value_reference=value_reference,
        exposed=exposed,
        runtime_group=runtime_group,
        diff_base_uid=diff_base_uid,
        history_index=history_index,
    )


def _root_base_uid(var: Any) -> int | None:
    base = getattr(var, "base_var", None)
    if base is None:
        return None
    while getattr(base, "base_var", None) is not None:
        base = base.base_var
    return int(base.uid)


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


def build_export_model(flat_block: Any, cfg: ExportConfig, snapshot: dict[str, Any], logic_entries: tuple[ExportLogicEntry, ...]) -> ExportModel:
    init_starts = _state_start_map(flat_block)
    output_vars = _collect_output_vars(flat_block)
    output_uids = {var.uid for var in output_vars}
    known_internal_uids = _known_internal_uids(flat_block)
    input_vars = [var for var in flat_block.in_vars if var.uid not in known_internal_uids]

    outputs_vr: dict[int, int] = {}
    params_vr: dict[int, int] = {}
    inputs_vr: dict[int, int] = {}
    next_vr = 0

    for var in sorted(input_vars, key=lambda item: (item.name, item.uid)):
        inputs_vr[var.uid] = next_vr
        next_vr += 1
    for var, _ in _sorted_param_items(flat_block.parameters):
        params_vr[var.uid] = next_vr
        next_vr += 1
    for var, _ in _sorted_param_items(flat_block.event_dict):
        params_vr[var.uid] = next_vr
        next_vr += 1
    for var, _ in _sorted_param_items(flat_block.mode_dict):
        params_vr[var.uid] = next_vr
        next_vr += 1
    for var in output_vars:
        outputs_vr[var.uid] = next_vr
        next_vr += 1

    variables: list[ExportVariable] = []
    equations: list[ExportEquation] = []
    outputs: list[ExportOutput] = []

    state_index_by_uid: dict[int, int] = {}
    algebraic_index_by_uid: dict[int, int] = {}
    input_index_by_uid: dict[int, int] = {}
    const_index_by_uid: dict[int, int] = {}
    runtime_index_by_uid: dict[int, int] = {}

    for index, var in enumerate(flat_block.state_vars):
        state_index_by_uid[var.uid] = index
        variables.append(
            _make_variable(
                var=var,
                category=VariableCategory.STATE,
                storage_segment=StorageSegment.STATES,
                storage_index=index,
                exposed=var.uid in output_uids,
                start=init_starts.get(var.uid, 0.0),
                value_reference=outputs_vr.get(var.uid),
                causality="output" if var.uid in output_uids else "local",
                variability="continuous",
                initial="exact" if var.uid in output_uids else "calculated",
                history_index=index,
            )
        )
        equations.append(
            ExportEquation(
                group=EquationGroup.STATE,
                index=index,
                target_uid=var.uid,
                target_name=var.name,
                expression=flat_block.state_eqs[index],
            )
        )

    for index, var in enumerate(flat_block.algebraic_vars):
        algebraic_index_by_uid[var.uid] = index
        variables.append(
            _make_variable(
                var=var,
                category=VariableCategory.ALGEBRAIC,
                storage_segment=StorageSegment.ALGEBRAICS,
                storage_index=index,
                exposed=var.uid in output_uids,
                start=None,
                value_reference=outputs_vr.get(var.uid),
                causality="output" if var.uid in output_uids else "local",
                variability="continuous",
                initial="calculated",
                history_index=len(flat_block.state_vars) + index,
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

    for index, var in enumerate(flat_block.diff_vars):
        variables.append(
            _make_variable(
                var=var,
                category=VariableCategory.DIFF,
                storage_segment=StorageSegment.STATES,
                storage_index=index,
                exposed=False,
                start=None,
                value_reference=None,
                causality="local",
                variability="continuous",
                initial=None,
                diff_base_uid=_root_base_uid(var),
            )
        )

    for index, var in enumerate(sorted(input_vars, key=lambda item: (item.name, item.uid))):
        input_index_by_uid[var.uid] = index
        variables.append(
            _make_variable(
                var=var,
                category=VariableCategory.INPUT,
                storage_segment=StorageSegment.INPUTS,
                storage_index=index,
                exposed=True,
                start=0.0,
                value_reference=inputs_vr[var.uid],
                causality="input",
                variability="continuous",
                initial=None,
            )
        )

    for index, (var, value) in enumerate(_sorted_param_items(flat_block.parameters)):
        const_index_by_uid[var.uid] = index
        variables.append(
            _make_variable(
                var=var,
                category=VariableCategory.CONST_PARAM,
                storage_segment=StorageSegment.CONST_PARAMS,
                storage_index=index,
                exposed=True,
                start=_const_value(value),
                value_reference=params_vr[var.uid],
                causality="parameter",
                variability="fixed",
                initial="exact",
            )
        )

    runtime_index = 0
    for runtime_group, mapping in ((RuntimeGroup.EVENT, flat_block.event_dict), (RuntimeGroup.MODE, flat_block.mode_dict)):
        for var, value in _sorted_param_items(mapping):
            start_value = _const_value(value) if isinstance(value, Const) else 0.0
            expose_runtime_param = start_value is not None
            runtime_index_by_uid[var.uid] = runtime_index
            variables.append(
                _make_variable(
                    var=var,
                    category=VariableCategory.RUNTIME_PARAM,
                    storage_segment=StorageSegment.RUNTIME_PARAMS,
                    storage_index=runtime_index,
                    exposed=expose_runtime_param,
                    start=start_value,
                    value_reference=params_vr[var.uid] if expose_runtime_param else None,
                    causality="parameter",
                    variability="tunable",
                    initial="exact",
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

    storage_by_uid = {
        **{uid: (StorageSegment.STATES, index) for uid, index in state_index_by_uid.items()},
        **{uid: (StorageSegment.ALGEBRAICS, index) for uid, index in algebraic_index_by_uid.items()},
        **{uid: (StorageSegment.INPUTS, index) for uid, index in input_index_by_uid.items()},
        **{uid: (StorageSegment.CONST_PARAMS, index) for uid, index in const_index_by_uid.items()},
        **{uid: (StorageSegment.RUNTIME_PARAMS, index) for uid, index in runtime_index_by_uid.items()},
    }

    for var in output_vars:
        segment, index = storage_by_uid[var.uid]
        source_variable = next(variable for variable in variables if variable.uid == var.uid)
        outputs.append(
            ExportOutput(
                name=var.name,
                value_reference=outputs_vr[var.uid],
                source_uid=var.uid,
                source_name=var.name,
                storage_segment=segment,
                storage_index=index,
                start=source_variable.start,
            )
        )

    return ExportModel(
        schema_version=1,
        model_name=cfg.model_name,
        model_identifier=cfg.model_identifier or cfg.model_name,
        guid=cfg.guid,
        fixed_step=cfg.fixed_step,
        integration_method=cfg.integration_method.value,
        variables=tuple(variables),
        outputs=tuple(outputs),
        equations=tuple(equations),
        logic_entries=logic_entries,
        source_snapshot=snapshot,
        counts={
            "states": len(flat_block.state_vars),
            "algebraics": len(flat_block.algebraic_vars),
            "diffs": len(flat_block.diff_vars),
            "inputs": len(input_vars),
            "const_params": len(flat_block.parameters),
            "runtime_params": len(flat_block.event_dict) + len(flat_block.mode_dict),
            "outputs": len(output_vars),
        },
    )
