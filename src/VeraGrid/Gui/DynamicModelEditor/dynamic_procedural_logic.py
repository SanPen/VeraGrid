# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Transactional editor models for retained modes and procedural runtime logic."""

from __future__ import annotations

import keyword
from pathlib import Path
import re
from typing import Dict, List, Mapping, Sequence

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import ProceduralFieldType, ProceduralLogicType
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import (
    CmpOp,
    Comparison,
    Const,
    Expr,
    Var,
    string_to_symbolic,
    symbolic_to_string,
)
from VeraGridEngine.Utils.procedural_logic import (
    AnalogFlipFlopLogic,
    DelayedThresholdLatchLogic,
    FixedSampleLogic,
    FlipFlopLogic,
    GradientLimiterLogic,
    HardSaturationLogic,
    MovingAverageLogic,
    PickupDropoffLogic,
    ProceduralLogicBase,
    ResetOnRisingEdgeLogic,
    SampledValueLogic,
    StartupHandoverLogic,
    ThreePhaseCarrierPwmLogic,
    ThreePhaseCarrierSampledModulationLogic,
    TimeDelayLogic,
    ValveStateLogic,
)


def comparison_operator_to_python(operator: CmpOp) -> str:
    """Return the Python token accepted by the safe symbolic parser.

    Engine comparison values are presentation symbols and may contain Unicode
    glyphs such as ``≥``. The runtime editor serializes executable Python-like
    source, so it must use parser tokens instead.

    :param operator: Engine comparison operator.
    :return: Python comparison token.
    """
    if operator == CmpOp.LE:
        result: str = "<="
    elif operator == CmpOp.GE:
        result = ">="
    elif operator == CmpOp.LT:
        result = "<"
    elif operator == CmpOp.GT:
        result = ">"
    elif operator == CmpOp.EQ:
        result = "=="
    else:
        raise ValueError(f"Unsupported comparison operator '{operator}'")
    return result


def get_symbol_replacement_sort_key(symbol_name: str) -> tuple[int, str]:
    """Return a key that replaces longer non-Python names first.

    :param symbol_name: Original engine symbol name.
    :return: Descending-length-compatible sort key.
    """
    return -len(symbol_name), symbol_name


def normalize_runtime_expression_source(source: str,
                                        namespace: Mapping[str, Expr]) -> tuple[str, Dict[str, Expr]]:
    """Replace non-Python engine names with temporary parser aliases.

    Catalogue globalization preserves human-readable block labels, which may
    include spaces, parentheses or a leading digit. Those names are valid in
    the symbolic engine but not as Python AST identifiers. Temporary aliases
    let the safe parser reconstruct the original ``Var`` identities without
    renaming the model.

    :param source: Serialized symbolic source using engine names.
    :param namespace: Canonical name-to-expression mapping.
    :return: Parser-safe source and augmented namespace.
    """
    normalized: str = source
    parser_namespace: Dict[str, Expr] = dict(namespace)
    replacement_names: List[str] = list()
    symbol_name: str
    for symbol_name in namespace.keys():
        parser_safe: bool = symbol_name.isidentifier() and not keyword.iskeyword(symbol_name)
        if not parser_safe and symbol_name in normalized:
            replacement_names.append(symbol_name)
        else:
            pass
    replacement_names.sort(key=get_symbol_replacement_sort_key)

    replacement_index: int = 0
    for symbol_name in replacement_names:
        alias: str = f"__runtime_symbol_{replacement_index}"
        while alias in parser_namespace:
            replacement_index += 1
            alias = f"__runtime_symbol_{replacement_index}"
        normalized = normalized.replace(symbol_name, alias)
        parser_namespace[alias] = namespace[symbol_name]
        replacement_index += 1
    return normalized, parser_namespace


class ProceduralFieldDraft:
    """One typed editable field belonging to a procedural entry draft."""

    __slots__ = ("_key", "_label", "_tpe", "_value", "_description", "_error")

    def __init__(self,
                 key: str,
                 label: str,
                 tpe: ProceduralFieldType,
                 value: str,
                 description: str) -> None:
        """Store one detached procedural field.

        :param key: Stable constructor/serialization field name.
        :param label: User-facing field label.
        :param tpe: Semantic editor and validation kind.
        :param value: Detached textual value.
        :param description: Contextual field explanation.
        :return: None.
        """
        self._key: str = key
        self._label: str = label
        self._tpe: ProceduralFieldType = tpe
        self._value: str = value
        self._description: str = description
        self._error: str = ""

    def get_key(self) -> str:
        """
        :return: The stable field key.
        """
        return self._key

    def get_label(self) -> str:
        """
        :return: The user-facing field label.
        """
        return self._label

    def get_tpe(self) -> ProceduralFieldType:
        """
        :return: The semantic editor kind.
        """
        return self._tpe

    def get_value(self) -> str:
        """
        :return: The detached textual value.
        """
        return self._value

    def set_value(self, value: str) -> None:
        """
        Replace the detached textual value.

        :param value: Value supplied for ``value``.
        :return: None.
        """
        self._value = value.strip()

    def get_description(self) -> str:
        """
        :return: The field help text.
        """
        return self._description

    def set_error(self, error: str) -> None:
        """
        Set the current validation error or clear it with an empty string.

        :param error: Value supplied for ``error``.
        :return: None.
        """
        self._error = error

    def get_error(self) -> str:
        """
        :return: The current validation error.
        """
        return self._error


class RuntimeModeDraft:
    """Detached retained runtime mode with an initial symbolic expression."""

    __slots__ = ("_owner", "_variable", "_name", "_initial_expression", "_removed", "_error")

    def __init__(self,
                 owner: Block,
                 variable: Var | None,
                 name: str,
                 initial_expression: str) -> None:
        """Capture one retained mode without changing its block.

        :param owner: Direct block owning ``mode_dict``.
        :param variable: Existing variable or ``None`` for a new draft.
        :param name: Symbol name.
        :param initial_expression: Python-like symbolic initialization source.
        :return: None.
        """
        self._owner: Block = owner
        self._variable: Var | None = variable
        self._name: str = name
        self._initial_expression: str = initial_expression
        self._removed: bool = False
        self._error: str = ""

    def get_owner(self) -> Block:
        """
        :return: The direct owner block.
        """
        return self._owner

    def get_variable(self) -> Var | None:
        """
        Return the existing mode variable or ``None`` for a new mode.

        :return: The existing mode variable or ``None`` for a new mode.
        """
        return self._variable

    def get_name(self) -> str:
        """
        Return the mode symbol name.

        :return: The mode symbol name.
        """
        return self._name

    def set_name(self, name: str) -> None:
        """
        Set the name of a new retained mode.

        :param name: Value supplied for ``name``.
        :return: None.
        """
        self._name = name.strip()

    def get_initial_expression(self) -> str:
        """
        Return the staged initial expression source.

        :return: The staged initial expression source.
        """
        return self._initial_expression

    def set_initial_expression(self, expression: str) -> None:
        """
        Set the staged initial expression source.

        :param expression: Value supplied for ``expression``.
        :return: None.
        """
        self._initial_expression = expression.strip()

    def is_new(self) -> bool:
        """
        Return whether Apply must create a real variable.

        :return: Whether Apply must create a real variable.
        """
        return self._variable is None

    def is_removed(self) -> bool:
        """
        Return whether deletion is staged.

        :return: Whether deletion is staged.
        """
        return self._removed

    def set_removed(self, removed: bool) -> None:
        """
        Stage or undo deletion.

        :param removed: Value supplied for ``removed``.
        :return: None.
        """
        self._removed = removed

    def set_error(self, error: str) -> None:
        """
        Set the current validation error.

        :param error: Value supplied for ``error``.
        :return: None.
        """
        self._error = error

    def get_error(self) -> str:
        """
        Return the current validation error.

        :return: The current validation error.
        """
        return self._error


class ProceduralLogicDraft:
    """Detached typed representation of one ordered procedural logic entry."""

    __slots__ = ("_owner", "_logic_tpe", "_name", "_fields", "_original", "_error")

    def __init__(self,
                 owner: Block,
                 logic_tpe: ProceduralLogicType,
                 name: str,
                 fields: Sequence[ProceduralFieldDraft],
                 original: ProceduralLogicBase | None) -> None:
        """Capture one procedural entry and its typed fields.

        :param owner: Direct block owning the ordered entry.
        :param logic_tpe: Canonical procedural type.
        :param name: User-facing entry name.
        :param fields: Typed editable fields.
        :param original: Original entry or ``None`` for a staged addition.
        :return: None.
        """
        self._owner: Block = owner
        self._logic_tpe: ProceduralLogicType = logic_tpe
        self._name: str = name
        self._fields: List[ProceduralFieldDraft] = list(fields)
        self._original: ProceduralLogicBase | None = original
        self._error: str = ""

    def get_owner(self) -> Block:
        """
        :return: The direct owner block.
        """
        return self._owner

    def get_logic_tpe(self) -> ProceduralLogicType:
        """
        :return: The canonical logic type.
        """
        return self._logic_tpe

    def get_name(self) -> str:
        """
        :return: The staged entry name.
        """
        return self._name

    def set_name(self, name: str) -> None:
        """
        Set the staged entry name.

        :param name: Value supplied for ``name``.
        :return: None.
        """
        self._name = name.strip()

    def get_fields(self) -> List[ProceduralFieldDraft]:
        """
        :return: The ordered editable fields.
        """
        return list(self._fields)

    def get_field(self, key: str) -> ProceduralFieldDraft | None:
        """Return one field by stable key.

        :param key: Requested field key.
        :return: Matching field or ``None``.
        """
        result: ProceduralFieldDraft | None = None
        field: ProceduralFieldDraft
        for field in self._fields:
            if field.get_key() == key and result is None:
                result = field
            else:
                pass
        return result

    def get_original(self) -> ProceduralLogicBase | None:
        """
        Return the original runtime entry.

        :return: The original runtime entry.
        """
        return self._original

    def set_error(self, error: str) -> None:
        """
        Set the entry-level validation error.

        :param error: Value supplied for ``error``.
        :return: None.
        """
        self._error = error

    def get_error(self) -> str:
        """
        Return the entry-level validation error.

        :return: The entry-level validation error.
        """
        return self._error

    def get_output_summary(self) -> str:
        """
        Return the first output, mode, or target reference for the entry list.

        :return: The first output, mode, or target reference for the entry list.
        """
        result: str = ""
        field: ProceduralFieldDraft
        for field in self._fields:
            if result == "" and field.get_tpe() in (
                ProceduralFieldType.MODE_REFERENCE,
                ProceduralFieldType.TARGET_REFERENCE,
            ):
                result = field.get_value()
            else:
                pass
        return result


class RuntimeLogicValidationResult:
    """Validation messages for a complete retained-mode/procedural draft."""

    __slots__ = ("_errors", "_warnings")

    def __init__(self) -> None:
        """
        Create an empty validation result.

        :return: None.
        """
        self._errors: List[str] = list()
        self._warnings: List[str] = list()

    def add_error(self, message: str) -> None:
        """
        Append one blocking error.

        :param message: Value supplied for ``message``.
        :return: None.
        """
        self._errors.append(message)

    def add_warning(self, message: str) -> None:
        """
        Append one non-blocking warning.

        :param message: Value supplied for ``message``.
        :return: None.
        """
        self._warnings.append(message)

    def get_errors(self) -> List[str]:
        """
        Return blocking errors.

        :return: Blocking errors.
        """
        return list(self._errors)

    def get_warnings(self) -> List[str]:
        """
        Return non-blocking warnings.

        :return: Non-blocking warnings.
        """
        return list(self._warnings)

    def is_valid(self) -> bool:
        """
        Return whether no blocking error was collected.

        :return: Whether no blocking error was collected.
        """
        return len(self._errors) == 0


def procedural_expression_to_text(expression: Expr | Comparison | float | int | bool) -> str:
    """Convert one procedural expression to editable Python-like source.

    :param expression: Existing procedural expression or scalar.
    :return: Readable source accepted by ``string_to_symbolic``.
    """
    if isinstance(expression, Comparison):
        left_text: str = symbolic_to_string(expression.lhs)
        if isinstance(expression.rhs, Expr):
            right_text: str = symbolic_to_string(expression.rhs)
        else:
            right_text = str(expression.rhs)
        operator_text: str = comparison_operator_to_python(expression.op)
        result: str = f"{left_text} {operator_text} {right_text}"
    elif isinstance(expression, Expr):
        result = symbolic_to_string(expression)
    else:
        result = str(float(expression))
    return result


def expression_mentions_symbol(expression: Expr | Comparison,
                               symbol_name: str) -> bool:
    """Return whether an expression reads a symbol by its complete name.

    Text matching is used because the current engine variable walker does not
    traverse ``Comparison`` nodes. Word boundaries prevent a mode such as
    ``trip`` from being confused with ``trip_delay``.

    :param expression: DAE, initialization or guard expression.
    :param symbol_name: Exact symbolic name being searched.
    :return: Whether the expression contains the requested symbol.
    """
    pattern: re.Pattern[str] = re.compile(rf"\b{re.escape(symbol_name)}\b")
    source: str = procedural_expression_to_text(expression)
    return pattern.search(source) is not None


def block_reads_symbol(block: Block, symbol_name: str) -> bool:
    """Return whether one block reads a symbol in any executable equation.

    :param block: Candidate direct equation owner.
    :param symbol_name: Exact retained-mode name.
    :return: Whether the symbol is read by the block.
    """
    reads_symbol: bool = False
    expression_groups: tuple[Sequence[Expr | Comparison], ...] = (
        block.state_eqs,
        block.algebraic_eqs,
        block.differential_eqs,
        block.inequalities,
    )
    expression_group: Sequence[Expr | Comparison]
    expression: Expr | Comparison
    for expression_group in expression_groups:
        for expression in expression_group:
            if expression_mentions_symbol(expression, symbol_name):
                reads_symbol = True
            else:
                pass

    expression_mappings: tuple[Mapping[Var, Expr | Comparison], ...] = (
        block.init_eqs,
        block.diff_init_eqs,
        block.discrete_eqs,
        block.boolean_guards,
    )
    expression_mapping: Mapping[Var, Expr | Comparison]
    for expression_mapping in expression_mappings:
        for expression in expression_mapping.values():
            if expression_mentions_symbol(expression, symbol_name):
                reads_symbol = True
            else:
                pass
    return reads_symbol


def make_procedural_field(key: str,
                          label: str,
                          tpe: ProceduralFieldType,
                          value: str,
                          description: str) -> ProceduralFieldDraft:
    """Build one non-trivial typed procedural field.

    :param key: Stable field key.
    :param label: User-facing label.
    :param tpe: Editor type.
    :param value: Initial text.
    :param description: Field help.
    :return: Configured field draft.
    """
    field: ProceduralFieldDraft = ProceduralFieldDraft(key, label, tpe, value, description)
    return field


def get_procedural_fields(entry: ProceduralLogicBase) -> List[ProceduralFieldDraft]:
    """Build typed fields from any supported runtime entry.

    :param entry: Existing procedural logic object.
    :return: Ordered field drafts.
    """
    fields: List[ProceduralFieldDraft] = list()
    expression_tpe: ProceduralFieldType = ProceduralFieldType.EXPRESSION
    mode_tpe: ProceduralFieldType = ProceduralFieldType.MODE_REFERENCE
    variable_tpe: ProceduralFieldType = ProceduralFieldType.VARIABLE_REFERENCE
    runtime_tpe: ProceduralFieldType = ProceduralFieldType.RUNTIME_REFERENCE
    target_tpe: ProceduralFieldType = ProceduralFieldType.TARGET_REFERENCE

    if isinstance(entry, FixedSampleLogic):
        fields.append(make_procedural_field("output_var_name", "Output mode", mode_tpe,
                                            entry.output_var_name, "Boolean value retained after initialization."))
        fields.append(make_procedural_field("condition_expr", "Condition", expression_tpe,
                                            procedural_expression_to_text(entry.condition_expr),
                                            "Condition sampled once during initialization."))
    elif isinstance(entry, SampledValueLogic):
        fields.append(make_procedural_field("output_var_name", "Output mode", mode_tpe,
                                            entry.output_var_name, "Retained sampled value."))
        fields.append(make_procedural_field("source_expr", "Source expression", expression_tpe,
                                            procedural_expression_to_text(entry.source_expr),
                                            "Expression sampled at every accepted step."))
    elif isinstance(entry, HardSaturationLogic):
        fields.extend(list((make_procedural_field("output_var_name", "Output mode", mode_tpe, entry.output_var_name,
                                  "Retained saturated output."), make_procedural_field("u_expr", "Input expression", expression_tpe,
                                  procedural_expression_to_text(entry.u_expr), "Value to clamp."), make_procedural_field("u_min_expr", "Minimum", expression_tpe,
                                  procedural_expression_to_text(entry.u_min_expr), "Lower saturation bound."), make_procedural_field("u_max_expr", "Maximum", expression_tpe,
                                  procedural_expression_to_text(entry.u_max_expr), "Upper saturation bound."),)))
    elif isinstance(entry, TimeDelayLogic):
        fields.extend(list((make_procedural_field("output_var_name", "Output mode", mode_tpe, entry.output_var_name,
                                  "Retained delayed value."), make_procedural_field("source_expr", "Source expression", expression_tpe,
                                  procedural_expression_to_text(entry.source_expr), "Value stored in history."), make_procedural_field("delay_expr", "Delay", expression_tpe,
                                  procedural_expression_to_text(entry.delay_expr), "Non-negative delay in seconds."),)))
    elif isinstance(entry, MovingAverageLogic):
        fields.extend(list((make_procedural_field("output_var_name", "Output mode", mode_tpe, entry.output_var_name,
                                  "Retained averaged output."), make_procedural_field("source_expr", "Source expression", expression_tpe,
                                  procedural_expression_to_text(entry.source_expr), "Value stored in history."), make_procedural_field("delay_expr", "Delay", expression_tpe,
                                  procedural_expression_to_text(entry.delay_expr), "Delay before the averaging window."), make_procedural_field("window_expr", "Window", expression_tpe,
                                  procedural_expression_to_text(entry.window_expr), "Averaging-window duration."),)))
    elif isinstance(entry, GradientLimiterLogic):
        fields.extend(list((make_procedural_field("output_var_name", "Output mode", mode_tpe, entry.output_var_name,
                                  "Retained rate-limited output."), make_procedural_field("source_expr", "Source expression", expression_tpe,
                                  procedural_expression_to_text(entry.source_expr), "Requested value."), make_procedural_field("lower_rate_expr", "Lower rate", expression_tpe,
                                  procedural_expression_to_text(entry.lower_rate_expr), "Minimum slope."), make_procedural_field("upper_rate_expr", "Upper rate", expression_tpe,
                                  procedural_expression_to_text(entry.upper_rate_expr), "Maximum slope."),)))
    elif isinstance(entry, FlipFlopLogic):
        fields.extend(list((make_procedural_field("output_var_name", "Output mode", mode_tpe, entry.output_var_name,
                                  "Retained binary latch state."), make_procedural_field("set_expr", "Set condition", expression_tpe,
                                  procedural_expression_to_text(entry.set_expr), "Condition driving the latch high."), make_procedural_field("reset_expr", "Reset condition", expression_tpe,
                                  procedural_expression_to_text(entry.reset_expr), "Condition driving the latch low."),)))
    elif isinstance(entry, AnalogFlipFlopLogic):
        fields.extend(list((make_procedural_field("output_var_name", "Output mode", mode_tpe, entry.output_var_name,
                                  "Retained analog latch output."), make_procedural_field("input_expr", "Input expression", expression_tpe,
                                  procedural_expression_to_text(entry.input_expr), "Analog value captured on Set."), make_procedural_field("set_expr", "Set condition", expression_tpe,
                                  procedural_expression_to_text(entry.set_expr), "Capture condition."), make_procedural_field("reset_expr", "Reset condition", expression_tpe,
                                  procedural_expression_to_text(entry.reset_expr), "Release condition."),)))
    elif isinstance(entry, PickupDropoffLogic):
        fields.extend(list((make_procedural_field("output_var_name", "Output mode", mode_tpe, entry.output_var_name,
                                  "Retained relay state."), make_procedural_field("bool_expr", "Condition", expression_tpe,
                                  procedural_expression_to_text(entry.bool_expr), "Relay input condition."), make_procedural_field("pickup_delay_expr", "Pickup delay", expression_tpe,
                                  procedural_expression_to_text(entry.pickup_delay_expr), "Delay before activation."), make_procedural_field("drop_delay_expr", "Dropoff delay", expression_tpe,
                                  procedural_expression_to_text(entry.drop_delay_expr), "Delay before deactivation."),)))
    elif isinstance(entry, ResetOnRisingEdgeLogic):
        fields.extend(list((make_procedural_field("target_var_name", "Target", target_tpe, entry.target_var_name,
                                  "DAE variable or runtime parameter modified on the edge."), make_procedural_field("reset_expr", "Rising-edge condition", expression_tpe,
                                  procedural_expression_to_text(entry.reset_expr), "Edge detector input."), make_procedural_field("value_expr", "Reset value", expression_tpe,
                                  procedural_expression_to_text(entry.value_expr), "Value assigned on the rising edge."),)))
    elif isinstance(entry, DelayedThresholdLatchLogic):
        fields.extend(list((make_procedural_field("monitored_var_name", "Monitored variable", variable_tpe,
                                  entry.monitored_var_name, "DAE signal compared with the threshold."), make_procedural_field("mode_var_name", "Output mode", mode_tpe, entry.mode_var_name,
                                  "Retained trip mode."), make_procedural_field("threshold", "Threshold", ProceduralFieldType.FLOAT,
                                  str(entry.threshold), "Trip threshold."), make_procedural_field("delay", "Delay", ProceduralFieldType.FLOAT,
                                  str(entry.delay), "Non-negative trip delay."), make_procedural_field("reset_delay", "Reset delay", ProceduralFieldType.OPTIONAL_FLOAT,
                                  "" if entry.reset_delay is None else str(entry.reset_delay),
                                  "Optional non-negative automatic reset delay."),)))
    elif isinstance(entry, StartupHandoverLogic):
        fields.extend(list((make_procedural_field("mode_var_name", "Output mode", mode_tpe, entry.mode_var_name,
                                  "Retained startup/handover mode."), make_procedural_field("enable_time_var_name", "Enable-time parameter", runtime_tpe,
                                  entry.enable_time_var_name, "Runtime parameter containing the handover time."),)))
    elif isinstance(entry, ValveStateLogic):
        valve_fields: tuple[tuple[str, str, ProceduralFieldType, str, str], ...] = (
            ("mode_var_name", "Output mode", mode_tpe, entry.mode_var_name, "Retained conduction path."),
            ("valve_type_var_name", "Valve type", runtime_tpe, entry.valve_type_var_name, "Runtime valve type code."),
            ("gate_var_name", "Gate command", runtime_tpe, entry.gate_var_name, "Runtime gate command."),
            ("antiparallel_var_name", "Antiparallel enabled", runtime_tpe,
             entry.antiparallel_var_name, "Runtime reverse-path flag."),
            ("voltage_eps_var_name", "Voltage deadband", runtime_tpe,
             entry.voltage_eps_var_name, "Runtime voltage deadband."),
            ("current_eps_var_name", "Current deadband", runtime_tpe,
             entry.current_eps_var_name, "Runtime current deadband."),
            ("valve_voltage_var_name", "Valve voltage", variable_tpe,
             entry.valve_voltage_var_name, "Measured valve voltage."),
            ("valve_current_var_name", "Valve current", variable_tpe,
             entry.valve_current_var_name, "Measured valve current."),
        )
        valve_field: tuple[str, str, ProceduralFieldType, str, str]
        for valve_field in valve_fields:
            fields.append(make_procedural_field(valve_field[0], valve_field[1], valve_field[2],
                                                valve_field[3], valve_field[4]))
    elif isinstance(entry, ThreePhaseCarrierPwmLogic):
        pwm_fields: tuple[tuple[str, str, ProceduralFieldType, str], ...] = (
            ("mod_a_var_name", "Modulation A", variable_tpe, entry.mod_a_var_name),
            ("mod_b_var_name", "Modulation B", variable_tpe, entry.mod_b_var_name),
            ("mod_c_var_name", "Modulation C", variable_tpe, entry.mod_c_var_name),
            ("gate_a_mode_var_name", "Gate mode A", mode_tpe, entry.gate_a_mode_var_name),
            ("gate_b_mode_var_name", "Gate mode B", mode_tpe, entry.gate_b_mode_var_name),
            ("gate_c_mode_var_name", "Gate mode C", mode_tpe, entry.gate_c_mode_var_name),
            ("omega_sw_var_name", "Switching frequency", runtime_tpe, entry.omega_sw_var_name),
            ("carrier_phase_var_name", "Carrier phase", runtime_tpe, entry.carrier_phase_var_name),
        )
        pwm_field: tuple[str, str, ProceduralFieldType, str]
        for pwm_field in pwm_fields:
            fields.append(make_procedural_field(pwm_field[0], pwm_field[1], pwm_field[2],
                                                pwm_field[3], "Three-phase carrier PWM reference."))
    elif isinstance(entry, ThreePhaseCarrierSampledModulationLogic):
        sampled_fields: tuple[tuple[str, str, ProceduralFieldType, str], ...] = (
            ("mod_a_var_name", "Modulation A", variable_tpe, entry.mod_a_var_name),
            ("mod_b_var_name", "Modulation B", variable_tpe, entry.mod_b_var_name),
            ("mod_c_var_name", "Modulation C", variable_tpe, entry.mod_c_var_name),
            ("sample_a_mode_var_name", "Sample mode A", mode_tpe, entry.sample_a_mode_var_name),
            ("sample_b_mode_var_name", "Sample mode B", mode_tpe, entry.sample_b_mode_var_name),
            ("sample_c_mode_var_name", "Sample mode C", mode_tpe, entry.sample_c_mode_var_name),
            ("omega_sw_var_name", "Switching frequency", runtime_tpe, entry.omega_sw_var_name),
            ("carrier_phase_var_name", "Carrier phase", runtime_tpe, entry.carrier_phase_var_name),
        )
        sampled_field: tuple[str, str, ProceduralFieldType, str]
        for sampled_field in sampled_fields:
            fields.append(make_procedural_field(sampled_field[0], sampled_field[1], sampled_field[2],
                                                sampled_field[3], "Carrier-synchronized sampling reference."))
    else:
        raise ValueError(f"Unsupported procedural logic entry '{entry.__class__.__name__}'")
    return fields


def get_default_procedural_fields(logic_tpe: ProceduralLogicType) -> List[ProceduralFieldDraft]:
    """Return safe empty/default fields for a newly requested logic type.

    :param logic_tpe: Type selected by the user.
    :return: Typed default field list.
    """
    mode: ProceduralFieldType = ProceduralFieldType.MODE_REFERENCE
    expr: ProceduralFieldType = ProceduralFieldType.EXPRESSION
    variable: ProceduralFieldType = ProceduralFieldType.VARIABLE_REFERENCE
    runtime: ProceduralFieldType = ProceduralFieldType.RUNTIME_REFERENCE
    target: ProceduralFieldType = ProceduralFieldType.TARGET_REFERENCE
    fields: List[ProceduralFieldDraft] = list()
    if logic_tpe == ProceduralLogicType.FixedSample:
        fields = list((make_procedural_field("output_var_name", "Output mode", mode, "", "Retained boolean output."), make_procedural_field("condition_expr", "Condition", expr, "0.0", "Condition sampled once."),))
    elif logic_tpe == ProceduralLogicType.SampledValue:
        fields = list((make_procedural_field("output_var_name", "Output mode", mode, "", "Retained sampled output."), make_procedural_field("source_expr", "Source expression", expr, "0.0", "Expression sampled each step."),))
    elif logic_tpe == ProceduralLogicType.HardSaturation:
        fields = list((make_procedural_field("output_var_name", "Output mode", mode, "", "Retained saturated output."), make_procedural_field("u_expr", "Input expression", expr, "0.0", "Value to clamp."), make_procedural_field("u_min_expr", "Minimum", expr, "-1.0", "Lower bound."), make_procedural_field("u_max_expr", "Maximum", expr, "1.0", "Upper bound."),))
    elif logic_tpe == ProceduralLogicType.TimeDelay:
        fields = list((make_procedural_field("output_var_name", "Output mode", mode, "", "Retained delayed output."), make_procedural_field("source_expr", "Source expression", expr, "0.0", "History input."), make_procedural_field("delay_expr", "Delay", expr, "0.0", "Non-negative delay."),))
    elif logic_tpe == ProceduralLogicType.MovingAverage:
        fields = list((make_procedural_field("output_var_name", "Output mode", mode, "", "Retained average."), make_procedural_field("source_expr", "Source expression", expr, "0.0", "History input."), make_procedural_field("delay_expr", "Delay", expr, "0.0", "Delay before window."), make_procedural_field("window_expr", "Window", expr, "0.01", "Average window."),))
    elif logic_tpe == ProceduralLogicType.GradientLimiter:
        fields = list((make_procedural_field("output_var_name", "Output mode", mode, "", "Retained limited output."), make_procedural_field("source_expr", "Source expression", expr, "0.0", "Requested value."), make_procedural_field("lower_rate_expr", "Lower rate", expr, "-1.0", "Minimum slope."), make_procedural_field("upper_rate_expr", "Upper rate", expr, "1.0", "Maximum slope."),))
    elif logic_tpe == ProceduralLogicType.FlipFlop:
        fields = list((make_procedural_field("output_var_name", "Output mode", mode, "", "Binary latch output."), make_procedural_field("set_expr", "Set condition", expr, "0.0", "Set condition."), make_procedural_field("reset_expr", "Reset condition", expr, "0.0", "Reset condition."),))
    elif logic_tpe == ProceduralLogicType.AnalogFlipFlop:
        fields = list((make_procedural_field("output_var_name", "Output mode", mode, "", "Analog latch output."), make_procedural_field("input_expr", "Input expression", expr, "0.0", "Captured value."), make_procedural_field("set_expr", "Set condition", expr, "0.0", "Capture condition."), make_procedural_field("reset_expr", "Reset condition", expr, "0.0", "Release condition."),))
    elif logic_tpe == ProceduralLogicType.PickupDropoff:
        fields = list((make_procedural_field("output_var_name", "Output mode", mode, "", "Relay output."), make_procedural_field("bool_expr", "Condition", expr, "0.0", "Relay condition."), make_procedural_field("pickup_delay_expr", "Pickup delay", expr, "0.0", "Activation delay."), make_procedural_field("drop_delay_expr", "Dropoff delay", expr, "0.0", "Deactivation delay."),))
    elif logic_tpe == ProceduralLogicType.ResetOnRisingEdge:
        fields = list((make_procedural_field("target_var_name", "Target", target, "", "Mutable reset target."), make_procedural_field("reset_expr", "Rising-edge condition", expr, "0.0", "Edge input."), make_procedural_field("value_expr", "Reset value", expr, "0.0", "Assigned value."),))
    elif logic_tpe == ProceduralLogicType.DelayedThresholdLatch:
        fields = list((make_procedural_field("monitored_var_name", "Monitored variable", variable, "", "Compared DAE signal."), make_procedural_field("mode_var_name", "Output mode", mode, "", "Retained trip mode."), make_procedural_field("threshold", "Threshold", ProceduralFieldType.FLOAT, "0.0", "Trip threshold."), make_procedural_field("delay", "Delay", ProceduralFieldType.FLOAT, "0.0", "Trip delay."), make_procedural_field("reset_delay", "Reset delay", ProceduralFieldType.OPTIONAL_FLOAT, "",
                                  "Optional automatic reset delay."),))
    elif logic_tpe == ProceduralLogicType.StartupHandover:
        fields = list((make_procedural_field("mode_var_name", "Output mode", mode, "", "Handover mode."), make_procedural_field("enable_time_var_name", "Enable-time parameter", runtime, "", "Handover time."),))
    elif logic_tpe == ProceduralLogicType.ValveState:
        valve_defaults: tuple[tuple[str, str, ProceduralFieldType], ...] = (
            ("mode_var_name", "Output mode", mode),
            ("valve_type_var_name", "Valve type", runtime),
            ("gate_var_name", "Gate command", runtime),
            ("antiparallel_var_name", "Antiparallel enabled", runtime),
            ("voltage_eps_var_name", "Voltage deadband", runtime),
            ("current_eps_var_name", "Current deadband", runtime),
            ("valve_voltage_var_name", "Valve voltage", variable),
            ("valve_current_var_name", "Valve current", variable),
        )
        valve_default: tuple[str, str, ProceduralFieldType]
        for valve_default in valve_defaults:
            fields.append(make_procedural_field(valve_default[0], valve_default[1], valve_default[2], "",
                                                "Required valve-state reference."))
    elif logic_tpe in (
        ProceduralLogicType.ThreePhaseCarrierPwm,
        ProceduralLogicType.ThreePhaseCarrierSampledModulation,
    ):
        sampled: bool = logic_tpe == ProceduralLogicType.ThreePhaseCarrierSampledModulation
        phase_prefix: str = "sample" if sampled else "gate"
        phase_fields: tuple[tuple[str, str, ProceduralFieldType], ...] = (
            ("mod_a_var_name", "Modulation A", variable),
            ("mod_b_var_name", "Modulation B", variable),
            ("mod_c_var_name", "Modulation C", variable),
            (f"{phase_prefix}_a_mode_var_name", f"{phase_prefix.title()} mode A", mode),
            (f"{phase_prefix}_b_mode_var_name", f"{phase_prefix.title()} mode B", mode),
            (f"{phase_prefix}_c_mode_var_name", f"{phase_prefix.title()} mode C", mode),
            ("omega_sw_var_name", "Switching frequency", runtime),
            ("carrier_phase_var_name", "Carrier phase", runtime),
        )
        phase_field: tuple[str, str, ProceduralFieldType]
        for phase_field in phase_fields:
            fields.append(make_procedural_field(phase_field[0], phase_field[1], phase_field[2], "",
                                                "Required three-phase carrier reference."))
    else:
        raise ValueError(f"Unsupported procedural logic type '{logic_tpe.value}'")
    return fields


def get_logic_type_from_entry(entry: ProceduralLogicBase) -> ProceduralLogicType:
    """Return the canonical enum exposed by one existing logic object.

    :param entry: Existing entry.
    :return: Canonical logic type.
    """
    logic_tpe: ProceduralLogicType = entry.logic_tpe
    return logic_tpe


def get_procedural_expression_variables(entry: ProceduralLogicBase) -> List[Var]:
    """Return every symbolic variable read by one runtime-logic entry.

    Runtime expressions may legitimately reference simulation-owned symbols
    that are not exposed in the block's DAE collections. The properties
    dialogue needs those exact ``Var`` identities in its parser namespace so
    opening and reapplying an existing catalogue model is lossless.

    :param entry: Existing procedural-logic entry.
    :return: Variables referenced by its symbolic expression fields.
    """
    expressions: List[Expr | Comparison | float | int] = list()
    if isinstance(entry, FixedSampleLogic):
        expressions.append(entry.condition_expr)
    elif isinstance(entry, SampledValueLogic):
        expressions.append(entry.source_expr)
    elif isinstance(entry, HardSaturationLogic):
        expressions.extend(list((entry.u_expr, entry.u_min_expr, entry.u_max_expr,)))
    elif isinstance(entry, TimeDelayLogic):
        expressions.extend(list((entry.source_expr, entry.delay_expr,)))
    elif isinstance(entry, MovingAverageLogic):
        expressions.extend(list((entry.source_expr, entry.delay_expr, entry.window_expr,)))
    elif isinstance(entry, GradientLimiterLogic):
        expressions.extend(list((entry.source_expr, entry.lower_rate_expr, entry.upper_rate_expr,)))
    elif isinstance(entry, FlipFlopLogic):
        expressions.extend(list((entry.set_expr, entry.reset_expr,)))
    elif isinstance(entry, AnalogFlipFlopLogic):
        expressions.extend(list((entry.input_expr, entry.set_expr, entry.reset_expr,)))
    elif isinstance(entry, PickupDropoffLogic):
        expressions.extend(list((entry.bool_expr, entry.pickup_delay_expr, entry.drop_delay_expr,)))
    elif isinstance(entry, ResetOnRisingEdgeLogic):
        expressions.extend(list((entry.reset_expr, entry.value_expr,)))
    else:
        # The remaining logic types store typed symbol names and numeric
        # settings instead of free symbolic expression objects.
        pass

    variables: List[Var] = list()
    known_uids: set[int] = set()
    expression: Expr | Comparison | float | int
    for expression in expressions:
        expression_vars: List[Var] = list()
        if isinstance(expression, Comparison):
            expression_vars = expression.to_expression().get_vars()
        elif isinstance(expression, Expr):
            expression_vars = expression.get_vars()
        else:
            # Numeric convenience values are accepted by the engine for
            # expression fields and introduce no symbolic dependency.
            pass
        variable: Var
        for variable in expression_vars:
            if variable.uid not in known_uids:
                variables.append(variable)
                known_uids.add(variable.uid)
            else:
                pass
    return variables


def parse_runtime_expression(source: str, namespace: Mapping[str, Expr]) -> Expr | Comparison:
    """Parse one safe procedural or mode expression.

    :param source: Python-like symbolic source.
    :param namespace: Allowed identities.
    :return: Parsed expression or comparison.
    :raises ValueError: If the expression is empty or invalid.
    """
    normalized: str = source.strip()
    if len(normalized) == 0:
        raise ValueError("Expression cannot be empty")
    else:
        parser_source: str
        parser_namespace: Dict[str, Expr]
        parser_source, parser_namespace = normalize_runtime_expression_source(normalized, namespace)
        try:
            parsed: Expr | Comparison = string_to_symbolic(parser_source, parser_namespace)
        except SyntaxError as error:
            raise ValueError(str(error)) from error
    return parsed


def get_required_field_value(draft: ProceduralLogicDraft, key: str) -> str:
    """Return one required field value.

    :param draft: Owning procedural entry.
    :param key: Stable field key.
    :return: Non-empty field value.
    :raises ValueError: If the field is missing or empty.
    """
    field: ProceduralFieldDraft | None = draft.get_field(key)
    if field is None or len(field.get_value()) == 0:
        raise ValueError(f"Missing procedural field '{key}'")
    else:
        return field.get_value()


def get_required_expression(draft: ProceduralLogicDraft,
                            key: str,
                            namespace: Mapping[str, Expr]) -> Expr | Comparison:
    """Parse one required procedural expression field.

    :param draft: Owning procedural entry.
    :param key: Stable expression field key.
    :param namespace: Allowed symbolic identities.
    :return: Parsed expression.
    """
    return parse_runtime_expression(get_required_field_value(draft, key), namespace)


def get_required_float(draft: ProceduralLogicDraft, key: str) -> float:
    """Parse one required finite float field.

    :param draft: Owning procedural entry.
    :param key: Stable numeric field key.
    :return: Finite numeric value.
    """
    value: float = float(get_required_field_value(draft, key))
    if value != value or value in (float("inf"), float("-inf")):
        raise ValueError(f"Procedural field '{key}' must be finite")
    else:
        return value


def get_optional_float(draft: ProceduralLogicDraft, key: str) -> float | None:
    """Parse one optional finite float field.

    :param draft: Owning procedural entry.
    :param key: Stable optional numeric field key.
    :return: Parsed number or ``None``.
    """
    field: ProceduralFieldDraft | None = draft.get_field(key)
    if field is None or len(field.get_value()) == 0:
        result: float | None = None
    else:
        result = get_required_float(draft, key)
    return result


def build_runtime_logic_entry(draft: ProceduralLogicDraft,
                              namespace: Mapping[str, Expr]) -> ProceduralLogicBase:
    """Construct one runtime entry from a fully validated draft.

    :param draft: Typed procedural draft.
    :param namespace: Authoritative symbolic identities.
    :return: Reconstructed runtime entry.
    """
    tpe: ProceduralLogicType = draft.get_logic_tpe()
    name: str = draft.get_name()
    if tpe == ProceduralLogicType.FixedSample:
        result: ProceduralLogicBase = FixedSampleLogic(
            get_required_field_value(draft, "output_var_name"),
            get_required_expression(draft, "condition_expr", namespace), name)
    elif tpe == ProceduralLogicType.SampledValue:
        result = SampledValueLogic(get_required_field_value(draft, "output_var_name"),
                                   get_required_expression(draft, "source_expr", namespace), name)
    elif tpe == ProceduralLogicType.HardSaturation:
        result = HardSaturationLogic(get_required_field_value(draft, "output_var_name"),
                                     get_required_expression(draft, "u_expr", namespace),
                                     get_required_expression(draft, "u_min_expr", namespace),
                                     get_required_expression(draft, "u_max_expr", namespace), name)
    elif tpe == ProceduralLogicType.TimeDelay:
        result = TimeDelayLogic(get_required_field_value(draft, "output_var_name"),
                                get_required_expression(draft, "source_expr", namespace),
                                get_required_expression(draft, "delay_expr", namespace), name)
    elif tpe == ProceduralLogicType.MovingAverage:
        result = MovingAverageLogic(get_required_field_value(draft, "output_var_name"),
                                    get_required_expression(draft, "source_expr", namespace),
                                    get_required_expression(draft, "delay_expr", namespace),
                                    get_required_expression(draft, "window_expr", namespace), name)
    elif tpe == ProceduralLogicType.GradientLimiter:
        result = GradientLimiterLogic(get_required_field_value(draft, "output_var_name"),
                                      get_required_expression(draft, "source_expr", namespace),
                                      get_required_expression(draft, "lower_rate_expr", namespace),
                                      get_required_expression(draft, "upper_rate_expr", namespace), name)
    elif tpe == ProceduralLogicType.FlipFlop:
        result = FlipFlopLogic(get_required_field_value(draft, "output_var_name"),
                               get_required_expression(draft, "set_expr", namespace),
                               get_required_expression(draft, "reset_expr", namespace), name)
    elif tpe == ProceduralLogicType.AnalogFlipFlop:
        result = AnalogFlipFlopLogic(get_required_field_value(draft, "output_var_name"),
                                     get_required_expression(draft, "input_expr", namespace),
                                     get_required_expression(draft, "set_expr", namespace),
                                     get_required_expression(draft, "reset_expr", namespace), name)
    elif tpe == ProceduralLogicType.PickupDropoff:
        result = PickupDropoffLogic(get_required_field_value(draft, "output_var_name"),
                                    get_required_expression(draft, "bool_expr", namespace),
                                    get_required_expression(draft, "pickup_delay_expr", namespace),
                                    get_required_expression(draft, "drop_delay_expr", namespace), name)
    elif tpe == ProceduralLogicType.ResetOnRisingEdge:
        result = ResetOnRisingEdgeLogic(get_required_field_value(draft, "target_var_name"),
                                        get_required_expression(draft, "reset_expr", namespace),
                                        get_required_expression(draft, "value_expr", namespace), name)
    elif tpe == ProceduralLogicType.DelayedThresholdLatch:
        result = DelayedThresholdLatchLogic(
            get_required_field_value(draft, "monitored_var_name"),
            get_required_field_value(draft, "mode_var_name"),
            get_required_float(draft, "threshold"),
            get_required_float(draft, "delay"),
            get_optional_float(draft, "reset_delay"), name)
    elif tpe == ProceduralLogicType.StartupHandover:
        result = StartupHandoverLogic(get_required_field_value(draft, "mode_var_name"),
                                      get_required_field_value(draft, "enable_time_var_name"), name)
    elif tpe == ProceduralLogicType.ValveState:
        result = ValveStateLogic(
            get_required_field_value(draft, "mode_var_name"),
            get_required_field_value(draft, "valve_type_var_name"),
            get_required_field_value(draft, "gate_var_name"),
            get_required_field_value(draft, "antiparallel_var_name"),
            get_required_field_value(draft, "voltage_eps_var_name"),
            get_required_field_value(draft, "current_eps_var_name"),
            get_required_field_value(draft, "valve_voltage_var_name"),
            get_required_field_value(draft, "valve_current_var_name"), name)
    elif tpe == ProceduralLogicType.ThreePhaseCarrierPwm:
        result = ThreePhaseCarrierPwmLogic(
            get_required_field_value(draft, "mod_a_var_name"),
            get_required_field_value(draft, "mod_b_var_name"),
            get_required_field_value(draft, "mod_c_var_name"),
            get_required_field_value(draft, "gate_a_mode_var_name"),
            get_required_field_value(draft, "gate_b_mode_var_name"),
            get_required_field_value(draft, "gate_c_mode_var_name"),
            get_required_field_value(draft, "omega_sw_var_name"),
            get_required_field_value(draft, "carrier_phase_var_name"), name)
    elif tpe == ProceduralLogicType.ThreePhaseCarrierSampledModulation:
        result = ThreePhaseCarrierSampledModulationLogic(
            get_required_field_value(draft, "mod_a_var_name"),
            get_required_field_value(draft, "mod_b_var_name"),
            get_required_field_value(draft, "mod_c_var_name"),
            get_required_field_value(draft, "sample_a_mode_var_name"),
            get_required_field_value(draft, "sample_b_mode_var_name"),
            get_required_field_value(draft, "sample_c_mode_var_name"),
            get_required_field_value(draft, "omega_sw_var_name"),
            get_required_field_value(draft, "carrier_phase_var_name"), name)
    else:
        raise ValueError(f"Unsupported procedural logic type '{tpe.value}'")
    return result


class RuntimeLogicDraftCollection:
    """Transactional collection of recursive modes and ordered logic entries."""

    __slots__ = ("_root", "_modes", "_entries", "_changed")

    def __init__(self, root: Block) -> None:
        """Capture recursive runtime logic without mutating the source tree.

        :param root: Dialogue root block.
        :return: None.
        """
        self._root: Block = root
        self._modes: List[RuntimeModeDraft] = list()
        self._entries: List[ProceduralLogicDraft] = list()
        self._changed: bool = False
        owner: Block
        for owner in root.get_all_blocks():
            mode_variable: Var
            initial_expression: Expr
            for mode_variable, initial_expression in owner.mode_dict.items():
                self._modes.append(RuntimeModeDraft(
                    owner,
                    mode_variable,
                    mode_variable.name,
                    procedural_expression_to_text(initial_expression),
                ))
            entry: ProceduralLogicBase
            for entry in owner.procedural_logic:
                self._entries.append(ProceduralLogicDraft(
                    owner,
                    get_logic_type_from_entry(entry),
                    entry.name,
                    get_procedural_fields(entry),
                    entry,
                ))

    def get_root(self) -> Block:
        """
        :return: The dialogue root block.
        """
        return self._root

    def get_modes(self) -> List[RuntimeModeDraft]:
        """
        :return: Active and removed mode drafts.
        """
        return list(self._modes)

    def get_active_modes(self) -> List[RuntimeModeDraft]:
        """
        :return: Retained modes not staged for deletion.
        """
        result: List[RuntimeModeDraft] = list()
        mode: RuntimeModeDraft
        for mode in self._modes:
            if not mode.is_removed():
                result.append(mode)
            else:
                pass
        return result

    def get_entries(self) -> List[ProceduralLogicDraft]:
        """
        :return: Ordered procedural entry drafts.
        """
        return list(self._entries)

    def has_changes(self) -> bool:
        """
        :return: Whether the user staged a runtime-logic edit.
        """
        return self._changed

    def has_new_modes(self) -> bool:
        """
        :return: Whether Apply must create at least one retained mode.
        """
        result: bool = False
        mode: RuntimeModeDraft
        for mode in self._modes:
            if mode.is_new() and not mode.is_removed():
                result = True
            else:
                pass
        return result

    def mark_changed(self) -> None:
        """
        Mark the draft collection as edited.

        :return: None.
        """
        self._changed = True

    def add_mode(self, owner: Block, name: str, initial_expression: str) -> RuntimeModeDraft:
        """Stage one new retained mode.

        :param owner: Direct owner block.
        :param name: New symbol name.
        :param initial_expression: Initial source.
        :return: Added mode draft.
        """
        mode: RuntimeModeDraft = RuntimeModeDraft(owner, None, name, initial_expression)
        self._modes.append(mode)
        self._changed = True
        return mode

    def add_entry(self, owner: Block, logic_tpe: ProceduralLogicType, name: str) -> ProceduralLogicDraft:
        """Stage one new procedural entry at the end of its owner ordering.

        :param owner: Direct owner block.
        :param logic_tpe: Selected procedural type.
        :param name: Entry name.
        :return: Added entry draft.
        """
        entry: ProceduralLogicDraft = ProceduralLogicDraft(
            owner,
            logic_tpe,
            name,
            get_default_procedural_fields(logic_tpe),
            None,
        )
        self._entries.append(entry)
        self._changed = True
        return entry

    def remove_entry(self, row: int) -> bool:
        """Remove one staged or existing procedural entry.

        :param row: Entry row.
        :return: Whether a row was removed.
        """
        if 0 <= row < len(self._entries):
            del self._entries[row]
            self._changed = True
            result: bool = True
        else:
            result = False
        return result

    def move_entry(self, row: int, delta: int) -> int:
        """Move an entry within entries owned by the same block.

        :param row: Current global draft row.
        :param delta: ``-1`` or ``+1`` requested movement.
        :return: New row, or the unchanged row when movement is invalid.
        """
        result: int = row
        destination: int = row + delta
        if 0 <= row < len(self._entries) and 0 <= destination < len(self._entries):
            owner: Block = self._entries[row].get_owner()
            if self._entries[destination].get_owner() is owner:
                entry: ProceduralLogicDraft = self._entries.pop(row)
                self._entries.insert(destination, entry)
                self._changed = True
                result = destination
            else:
                pass
        else:
            pass
        return result

    def get_mode_writer_names(self, mode_name: str) -> List[str]:
        """Return ordered logic entry names writing one retained mode.

        :param mode_name: Mode symbol name.
        :return: Writer entry names.
        """
        writers: List[str] = list()
        entry: ProceduralLogicDraft
        field: ProceduralFieldDraft
        for entry in self._entries:
            for field in entry.get_fields():
                if field.get_tpe() == ProceduralFieldType.MODE_REFERENCE and field.get_value() == mode_name:
                    writers.append(entry.get_name())
                else:
                    pass
        return writers

    def get_mode_reader_names(self, mode_name: str) -> List[str]:
        """Return procedural, initialization and DAE readers of one mode.

        :param mode_name: Mode symbol name.
        :return: Reader entry names.
        """
        readers: List[str] = list()
        pattern: re.Pattern[str] = re.compile(rf"\b{re.escape(mode_name)}\b")
        entry: ProceduralLogicDraft
        field: ProceduralFieldDraft
        for entry in self._entries:
            found: bool = False
            for field in entry.get_fields():
                reads_mode: bool = (
                    field.get_tpe() == ProceduralFieldType.EXPRESSION
                    and pattern.search(field.get_value()) is not None
                )
                explicit_reference: bool = (
                    field.get_tpe() in (
                        ProceduralFieldType.RUNTIME_REFERENCE,
                        ProceduralFieldType.VARIABLE_REFERENCE,
                        ProceduralFieldType.TARGET_REFERENCE,
                    )
                    and field.get_value() == mode_name
                )
                if reads_mode or explicit_reference:
                    found = True
                else:
                    pass
            if found:
                readers.append(entry.get_name())
            else:
                pass

        # A mode can initialize another retained mode even when no procedural
        # entry reads it directly. This dependency must also block deletion.
        mode: RuntimeModeDraft
        for mode in self.get_active_modes():
            initialization_reads_mode: bool = (
                mode.get_name() != mode_name
                and pattern.search(mode.get_initial_expression()) is not None
            )
            if initialization_reads_mode:
                label: str = f"Mode initialization: {mode.get_owner().name} / {mode.get_name()}"
                if label not in readers:
                    readers.append(label)
                else:
                    pass
            else:
                pass

        # Existing equation trees are checked immediately. Draft DAE source is
        # validated again by the parent dialogue before Apply, covering edits
        # made after this dependency list was built.
        owner: Block
        for owner in self._root.get_all_blocks():
            if block_reads_symbol(owner, mode_name):
                label = f"DAE: {owner.name}"
                if label not in readers:
                    readers.append(label)
                else:
                    pass
            else:
                pass
        return readers

    def remove_mode(self, row: int) -> tuple[bool, str]:
        """Stage safe mode deletion only when no procedural field references it.

        :param row: Mode row.
        :return: Success flag and blocking explanation.
        """
        if not 0 <= row < len(self._modes):
            return False, "Select one retained mode."
        else:
            mode: RuntimeModeDraft = self._modes[row]
            writers: List[str] = self.get_mode_writer_names(mode.get_name())
            readers: List[str] = self.get_mode_reader_names(mode.get_name())
        if len(writers) > 0 or len(readers) > 0:
            references: List[str] = list(writers)
            reader: str
            for reader in readers:
                if reader not in references:
                    references.append(reader)
                else:
                    pass
            return False, f"Mode '{mode.get_name()}' is used by: {', '.join(references)}"
        else:
            mode.set_removed(True)
            self._changed = True
            return True, ""

    def build_validation_namespace(self, base_namespace: Mapping[str, Expr]) -> Dict[str, Expr]:
        """Add staged retained modes and exclude removed ones.

        :param base_namespace: Current complete block namespace.
        :return: Namespace used by DAE and procedural validation.
        """
        namespace: Dict[str, Expr] = dict(base_namespace)
        mode: RuntimeModeDraft
        for mode in self._modes:
            if mode.is_removed():
                namespace.pop(mode.get_name(), None)
            elif mode.is_new():
                namespace[mode.get_name()] = Var(mode.get_name())
            elif mode.get_variable() is not None:
                namespace[mode.get_name()] = mode.get_variable()
            else:
                pass
        return namespace

    def validate(self, base_namespace: Mapping[str, Expr]) -> RuntimeLogicValidationResult:
        """Validate modes, references, expressions, writers, and ordering.

        :param base_namespace: Complete symbolic namespace before staged modes.
        :return: Validation result with errors and warnings.
        """
        result: RuntimeLogicValidationResult = RuntimeLogicValidationResult()
        namespace: Dict[str, Expr] = self.build_validation_namespace(base_namespace)
        mode_names: set[str] = set()
        mode: RuntimeModeDraft
        for mode in self._modes:
            mode.set_error("")
            if not mode.is_removed():
                invalid_new_name: bool = (
                    mode.is_new()
                    and (
                        len(mode.get_name()) == 0
                        or not mode.get_name().isidentifier()
                        or keyword.iskeyword(mode.get_name())
                    )
                )
                if invalid_new_name:
                    message: str = f"Mode '{mode.get_name()}' needs a valid Python symbol name."
                    mode.set_error(message)
                    result.add_error(message)
                elif mode.get_name() in mode_names:
                    message = f"Retained mode '{mode.get_name()}' is declared more than once."
                    mode.set_error(message)
                    result.add_error(message)
                elif mode.is_new() and mode.get_name() in base_namespace:
                    message = (
                        f"Retained mode '{mode.get_name()}' conflicts with an existing DAE or parameter symbol."
                    )
                    mode.set_error(message)
                    result.add_error(message)
                else:
                    mode_names.add(mode.get_name())
                try:
                    initial_expression: Expr | Comparison = parse_runtime_expression(
                        mode.get_initial_expression(), namespace)
                    if isinstance(initial_expression, Comparison):
                        raise ValueError("initialization must be a numeric expression, not a comparison")
                    else:
                        pass
                except (KeyError, TypeError, ValueError) as error:
                    message = f"Mode '{mode.get_name()}' initialization: {error}"
                    mode.set_error(message)
                    result.add_error(message)
            else:
                pass

        entry_names: set[tuple[int, str]] = set()
        writer_rows: Dict[str, int] = dict()
        entry_index: int
        entry: ProceduralLogicDraft
        for entry_index, entry in enumerate(self._entries):
            entry.set_error("")
            entry_key: tuple[int, str] = (entry.get_owner().uid, entry.get_name())
            if len(entry.get_name()) == 0:
                if entry.get_original() is None:
                    message = f"Procedural entry #{entry_index + 1} needs a name."
                    entry.set_error(message)
                    result.add_error(message)
                else:
                    result.add_warning(
                        f"Existing procedural entry #{entry_index + 1} has no display name."
                    )
            elif entry_key in entry_names:
                message = f"Procedural entry name '{entry.get_name()}' is duplicated in '{entry.get_owner().name}'."
                if entry.get_original() is None:
                    entry.set_error(message)
                    result.add_error(message)
                else:
                    # Entry names are labels rather than runtime lookup keys.
                    # Preserve valid legacy catalogue blocks while preventing
                    # newly authored ambiguity.
                    result.add_warning(message)
            else:
                entry_names.add(entry_key)

            field: ProceduralFieldDraft
            for field in entry.get_fields():
                field.set_error("")
                field_tpe: ProceduralFieldType = field.get_tpe()
                field_value: str = field.get_value()
                try:
                    if field_tpe == ProceduralFieldType.EXPRESSION:
                        parsed_expression: Expr | Comparison = parse_runtime_expression(field_value, namespace)
                        _unused_expression: Expr | Comparison = parsed_expression
                    elif field_tpe == ProceduralFieldType.FLOAT:
                        parsed_float: float = float(field_value)
                        if parsed_float != parsed_float or parsed_float in (float("inf"), float("-inf")):
                            raise ValueError("number must be finite")
                        else:
                            pass
                    elif field_tpe == ProceduralFieldType.OPTIONAL_FLOAT:
                        if len(field_value) > 0:
                            optional_float: float = float(field_value)
                            if optional_float != optional_float or optional_float in (float("inf"), float("-inf")):
                                raise ValueError("number must be finite")
                            else:
                                pass
                        else:
                            pass
                    elif field_tpe == ProceduralFieldType.MODE_REFERENCE:
                        if field_value not in mode_names:
                            raise ValueError(f"'{field_value}' is not a retained mode")
                        elif field_value in writer_rows:
                            raise ValueError(
                                f"mode '{field_value}' is already written by entry #{writer_rows[field_value] + 1}"
                            )
                        else:
                            writer_rows[field_value] = entry_index
                    elif field_tpe in (
                        ProceduralFieldType.VARIABLE_REFERENCE,
                        ProceduralFieldType.RUNTIME_REFERENCE,
                        ProceduralFieldType.TARGET_REFERENCE,
                    ):
                        if field_value not in namespace:
                            raise ValueError(f"unknown symbol '{field_value}'")
                        else:
                            pass
                    else:
                        pass
                except (KeyError, TypeError, ValueError) as error:
                    message = f"{entry.get_name()} / {field.get_label()}: {error}"
                    field.set_error(message)
                    result.add_error(message)

        for mode in self.get_active_modes():
            writers = self.get_mode_writer_names(mode.get_name())
            if len(writers) == 0:
                result.add_warning(
                    f"Mode '{mode.get_name()}' has no procedural writer and is treated as retained/external."
                )
            else:
                pass
        self._validate_order_dependencies(result, writer_rows)
        return result

    def _validate_order_dependencies(self,
                                     result: RuntimeLogicValidationResult,
                                     writer_rows: Mapping[str, int]) -> None:
        """Warn when an expression reads a mode written later in the list.

        :param result: Validation result receiving warnings.
        :param writer_rows: Mode writer row lookup.
        :return: None.
        """
        entry_index: int
        entry: ProceduralLogicDraft
        for entry_index, entry in enumerate(self._entries):
            field: ProceduralFieldDraft
            for field in entry.get_fields():
                if field.get_tpe() == ProceduralFieldType.EXPRESSION:
                    mode_name: str
                    for mode_name, writer_index in writer_rows.items():
                        pattern: re.Pattern[str] = re.compile(rf"\b{re.escape(mode_name)}\b")
                        if writer_index > entry_index and pattern.search(field.get_value()) is not None:
                            result.add_warning(
                                f"'{entry.get_name()}' reads mode '{mode_name}' before its writer runs."
                            )
                        else:
                            pass
                else:
                    pass

    def apply_to_blocks(self, var_factory: VarFactory, base_namespace: Mapping[str, Expr]) -> Dict[str, Expr]:
        """Apply validated modes and logic entries to their direct owners.

        :param var_factory: Authoritative variable factory.
        :param base_namespace: Namespace after other symbol edits.
        :return: Namespace containing authoritative new mode variables.
        """
        validation: RuntimeLogicValidationResult = self.validate(base_namespace)
        if not validation.is_valid():
            raise ValueError(validation.get_errors()[0])
        else:
            namespace: Dict[str, Expr] = dict(base_namespace)

        mode: RuntimeModeDraft
        for mode in self._modes:
            variable: Var | None = mode.get_variable()
            if mode.is_removed():
                if variable is not None:
                    mode.get_owner().mode_dict.pop(variable, None)
                else:
                    pass
            else:
                if variable is None:
                    variable = var_factory.add_var(mode.get_name())
                else:
                    pass
                namespace[mode.get_name()] = variable

        owner: Block
        for owner in self._root.get_all_blocks():
            owner_modes: Dict[Var, Expr | Const] = dict()
            for mode in self._modes:
                if mode.get_owner() is owner and not mode.is_removed():
                    mode_variable: Expr | None = namespace.get(mode.get_name(), None)
                    if isinstance(mode_variable, Var):
                        parsed_initial: Expr | Comparison = parse_runtime_expression(
                            mode.get_initial_expression(), namespace)
                        if isinstance(parsed_initial, Expr):
                            owner_modes[mode_variable] = parsed_initial
                        else:
                            raise ValueError(
                                f"Mode '{mode.get_name()}' initialization cannot be a comparison."
                            )
                    else:
                        raise ValueError(f"Mode '{mode.get_name()}' has no authoritative variable.")
                else:
                    pass
            owner.mode_dict = owner_modes

            owner_entries: List[ProceduralLogicBase] = list()
            entry: ProceduralLogicDraft
            for entry in self._entries:
                if entry.get_owner() is owner:
                    owner_entries.append(build_runtime_logic_entry(entry, namespace))
                else:
                    pass
            owner.procedural_logic = owner_entries
        self._changed = False
        return namespace


class ProceduralEntryTableModel(QtCore.QAbstractTableModel):
    """Ordered overview model for procedural entry drafts."""

    __slots__ = ("_drafts",)

    def __init__(self,
                 drafts: RuntimeLogicDraftCollection,
                 parent: QtCore.QObject | None = None) -> None:
        """
        Create a table over one shared draft collection.

        :param drafts: Value supplied for ``drafts``.
        :param parent: Owning Qt widget.
        :return: None.
        """
        super().__init__(parent)
        self._drafts: RuntimeLogicDraftCollection = drafts

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return procedural entry count.

        :param parent: Owning Qt widget.
        :return: Procedural entry count.
        """
        return 0 if parent.isValid() else len(self._drafts.get_entries())

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return overview column count.

        :param parent: Owning Qt widget.
        :return: Overview column count.
        """
        return 0 if parent.isValid() else 6

    def data(self, index: QtCore.QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        """
        Return one overview cell.

        :param index: Value supplied for ``index``.
        :param role: Value supplied for ``role``.
        :return: One overview cell.
        """
        if not index.isValid() or index.row() >= self.rowCount():
            return None
        else:
            entry: ProceduralLogicDraft = self._drafts.get_entries()[index.row()]
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if index.column() == 0:
                return index.row() + 1
            elif index.column() == 1:
                return entry.get_owner().name
            elif index.column() == 2:
                return entry.get_name()
            elif index.column() == 3:
                return entry.get_logic_tpe().value
            elif index.column() == 4:
                return entry.get_output_summary()
            else:
                return "OK" if len(entry.get_error()) == 0 else "Error"
        elif role == Qt.ItemDataRole.ForegroundRole and len(entry.get_error()) > 0:
            return QtGui.QBrush(QtGui.QColor("#b42318"))
        elif role == Qt.ItemDataRole.ToolTipRole and len(entry.get_error()) > 0:
            return entry.get_error()
        else:
            return None

    def setData(self,
                index: QtCore.QModelIndex,
                value: object,
                role: int = Qt.ItemDataRole.EditRole) -> bool:
        """
        Edit only an entry name from the overview.

        :param index: Value supplied for ``index``.
        :param value: Value supplied for ``value``.
        :param role: Value supplied for ``role``.
        :return: True when the edited value was accepted; otherwise False.
        """
        if index.isValid() and index.column() == 2 and role == Qt.ItemDataRole.EditRole:
            entry: ProceduralLogicDraft = self._drafts.get_entries()[index.row()]
            entry.set_name(str(value))
            self._drafts.mark_changed()
            self.dataChanged.emit(index, index, list((role,)))
            return True
        else:
            return False

    def flags(self, index: QtCore.QModelIndex) -> Qt.ItemFlag:
        """
        Expose entry-name editing and row selection.

        :param index: Value supplied for ``index``.
        :return: Item flags enabling entry-name editing and row selection.
        """
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        else:
            flags: Qt.ItemFlag = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column() == 2:
            flags |= Qt.ItemFlag.ItemIsEditable
        else:
            pass
        return flags

    def headerData(self,
                   section: int,
                   orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole) -> object:
        """
        Return overview headers.

        :param section: Value supplied for ``section``.
        :param orientation: Value supplied for ``orientation``.
        :param role: Value supplied for ``role``.
        :return: Overview headers.
        """
        headers: tuple[str, ...] = ("Order", "Owner", "Name", "Type", "Output / target", "Status")
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return headers[section] if 0 <= section < len(headers) else None
        else:
            return None

    def reload(self) -> None:
        """
        Reset the overview after structural draft changes.

        :return: None.
        """
        self.beginResetModel()
        self.endResetModel()


class RuntimeModeTableModel(QtCore.QAbstractTableModel):
    """Editable retained-mode overview and dependency model."""

    __slots__ = ("_drafts",)

    def __init__(self,
                 drafts: RuntimeLogicDraftCollection,
                 parent: QtCore.QObject | None = None) -> None:
        """
        Create a mode table over the shared collection.

        :param drafts: Value supplied for ``drafts``.
        :param parent: Owning Qt widget.
        :return: None.
        """
        super().__init__(parent)
        self._drafts: RuntimeLogicDraftCollection = drafts

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return retained mode count including staged deletions.

        :param parent: Owning Qt widget.
        :return: Retained mode count including staged deletions.
        """
        return 0 if parent.isValid() else len(self._drafts.get_modes())

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return mode overview column count.

        :param parent: Owning Qt widget.
        :return: Mode overview column count.
        """
        return 0 if parent.isValid() else 6

    def data(self, index: QtCore.QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        """
        Return mode identity, initialization, dependencies, and status.

        :param index: Value supplied for ``index``.
        :param role: Value supplied for ``role``.
        :return: Mode identity, initialization, dependencies, and status.
        """
        if not index.isValid() or index.row() >= self.rowCount():
            return None
        else:
            mode: RuntimeModeDraft = self._drafts.get_modes()[index.row()]
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if index.column() == 0:
                return mode.get_owner().name
            elif index.column() == 1:
                return mode.get_name()
            elif index.column() == 2:
                return mode.get_initial_expression()
            elif index.column() == 3:
                writers: List[str] = self._drafts.get_mode_writer_names(mode.get_name())
                return ", ".join(writers) if len(writers) > 0 else "External / retained"
            elif index.column() == 4:
                return ", ".join(self._drafts.get_mode_reader_names(mode.get_name()))
            else:
                if mode.is_removed():
                    return "Removed"
                elif len(mode.get_error()) > 0:
                    return "Error"
                else:
                    return "OK"
        elif role == Qt.ItemDataRole.ForegroundRole and (mode.is_removed() or len(mode.get_error()) > 0):
            return QtGui.QBrush(QtGui.QColor("#b42318"))
        elif role == Qt.ItemDataRole.ToolTipRole and len(mode.get_error()) > 0:
            return mode.get_error()
        else:
            return None

    def setData(self,
                index: QtCore.QModelIndex,
                value: object,
                role: int = Qt.ItemDataRole.EditRole) -> bool:
        """
        Edit new mode names and all initial expressions.

        :param index: Value supplied for ``index``.
        :param value: Value supplied for ``value``.
        :param role: Value supplied for ``role``.
        :return: True when the edited value was accepted; otherwise False.
        """
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        else:
            mode: RuntimeModeDraft = self._drafts.get_modes()[index.row()]
        if index.column() == 1 and mode.is_new():
            mode.set_name(str(value))
            changed: bool = True
        elif index.column() == 2:
            mode.set_initial_expression(str(value))
            changed = True
        else:
            changed = False
        if changed:
            self._drafts.mark_changed()
            self.dataChanged.emit(index, index, list((role,)))
        else:
            pass
        return changed

    def flags(self, index: QtCore.QModelIndex) -> Qt.ItemFlag:
        """
        Expose only safe retained-mode edits.

        :param index: Value supplied for ``index``.
        :return: Item flags enabling only safe retained-mode edits.
        """
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        else:
            mode: RuntimeModeDraft = self._drafts.get_modes()[index.row()]
            flags: Qt.ItemFlag = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column() == 2 or (index.column() == 1 and mode.is_new()):
            flags |= Qt.ItemFlag.ItemIsEditable
        else:
            pass
        return flags

    def headerData(self,
                   section: int,
                   orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole) -> object:
        """
        Return retained-mode headers.

        :param section: Value supplied for ``section``.
        :param orientation: Value supplied for ``orientation``.
        :param role: Value supplied for ``role``.
        :return: Retained-mode headers.
        """
        headers: tuple[str, ...] = ("Owner", "Name", "Initial expression", "Writer", "Read by", "Status")
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return headers[section] if 0 <= section < len(headers) else None
        else:
            return None

    def reload(self) -> None:
        """
        Reset the mode overview after structural draft changes.

        :return: None.
        """
        self.beginResetModel()
        self.endResetModel()


class ProceduralFieldTableModel(QtCore.QAbstractTableModel):
    """Typed field table for the currently selected procedural entry."""

    __slots__ = ("_drafts", "_entry")

    def __init__(self,
                 drafts: RuntimeLogicDraftCollection,
                 parent: QtCore.QObject | None = None) -> None:
        """
        Create an initially empty field model.

        :param drafts: Value supplied for ``drafts``.
        :param parent: Owning Qt widget.
        :return: None.
        """
        super().__init__(parent)
        self._drafts: RuntimeLogicDraftCollection = drafts
        self._entry: ProceduralLogicDraft | None = None

    def set_entry(self, entry: ProceduralLogicDraft | None) -> None:
        """
        Replace the selected procedural entry.

        :param entry: Value supplied for ``entry``.
        :return: None.
        """
        self.beginResetModel()
        self._entry = entry
        self.endResetModel()

    def get_field(self, row: int) -> ProceduralFieldDraft | None:
        """
        Return one selected-entry field by row.

        :param row: Value supplied for ``row``.
        :return: One selected-entry field by row.
        """
        if self._entry is not None:
            fields: List[ProceduralFieldDraft] = self._entry.get_fields()
            result: ProceduralFieldDraft | None = fields[row] if 0 <= row < len(fields) else None
        else:
            result = None
        return result

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return selected entry field count.

        :param parent: Owning Qt widget.
        :return: Selected entry field count.
        """
        if parent.isValid() or self._entry is None:
            return 0
        else:
            return len(self._entry.get_fields())

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return label, type, and value columns.

        :param parent: Owning Qt widget.
        :return: Label, type, and value columns.
        """
        return 0 if parent.isValid() else 3

    def data(self, index: QtCore.QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        """
        Return one typed field cell and validation presentation.

        :param index: Value supplied for ``index``.
        :param role: Value supplied for ``role``.
        :return: One typed field cell and validation presentation.
        """
        field: ProceduralFieldDraft | None = self.get_field(index.row())
        if not index.isValid() or field is None:
            return None
        elif role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if index.column() == 0:
                return field.get_label()
            elif index.column() == 1:
                return field.get_tpe().value
            else:
                return field.get_value()
        elif role == Qt.ItemDataRole.ToolTipRole:
            if len(field.get_error()) > 0:
                return field.get_error()
            else:
                return field.get_description()
        elif role in (Qt.ItemDataRole.ForegroundRole, Qt.ItemDataRole.BackgroundRole) and len(field.get_error()) > 0:
            if role == Qt.ItemDataRole.ForegroundRole:
                return QtGui.QBrush(QtGui.QColor("#b42318"))
            else:
                return QtGui.QBrush(QtGui.QColor("#fee2e2"))
        else:
            return None

    def setData(self,
                index: QtCore.QModelIndex,
                value: object,
                role: int = Qt.ItemDataRole.EditRole) -> bool:
        """
        Stage one selected-entry field edit.

        :param index: Value supplied for ``index``.
        :param value: Value supplied for ``value``.
        :param role: Value supplied for ``role``.
        :return: True when the edited value was accepted; otherwise False.
        """
        field: ProceduralFieldDraft | None = self.get_field(index.row())
        if field is not None and index.column() == 2 and role == Qt.ItemDataRole.EditRole:
            field.set_value(str(value))
            self._drafts.mark_changed()
            self.dataChanged.emit(index, index, list((role,)))
            return True
        else:
            return False

    def flags(self, index: QtCore.QModelIndex) -> Qt.ItemFlag:
        """
        Expose only value cells as editable.

        :param index: Value supplied for ``index``.
        :return: Item flags exposing only value cells as editable.
        """
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        else:
            flags: Qt.ItemFlag = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column() == 2:
            flags |= Qt.ItemFlag.ItemIsEditable
        else:
            pass
        return flags

    def headerData(self,
                   section: int,
                   orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole) -> object:
        """
        Return typed field headers.

        :param section: Value supplied for ``section``.
        :param orientation: Value supplied for ``orientation``.
        :param role: Value supplied for ``role``.
        :return: Typed field headers.
        """
        headers: tuple[str, ...] = ("Field", "Kind", "Value")
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return headers[section] if 0 <= section < len(headers) else None
        else:
            return None

    def reload(self) -> None:
        """
        Refresh validation colors and values.

        :return: None.
        """
        self.beginResetModel()
        self.endResetModel()


class ProceduralFieldDelegate(QtWidgets.QStyledItemDelegate):
    """Typed editor delegate for procedural field values."""

    __slots__ = ("_drafts",)

    def __init__(self,
                 drafts: RuntimeLogicDraftCollection,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """
        Create a delegate sharing one draft collection.

        :param drafts: Value supplied for ``drafts``.
        :param parent: Owning Qt widget.
        :return: None.
        """
        super().__init__(parent)
        self._drafts: RuntimeLogicDraftCollection = drafts

    def createEditor(self,
                     parent: QtWidgets.QWidget,
                     option: QtWidgets.QStyleOptionViewItem,
                     index: QtCore.QModelIndex) -> QtWidgets.QWidget:
        """
        Create a line editor or constrained reference combo.

        :param parent: Owning Qt widget.
        :param option: Value supplied for ``option``.
        :param index: Value supplied for ``index``.
        :return: Line editor or constrained reference combo for the selected field.
        """
        _unused_option: QtWidgets.QStyleOptionViewItem = option
        model: QtCore.QAbstractItemModel | None = index.model()
        field: ProceduralFieldDraft | None = None
        if isinstance(model, ProceduralFieldTableModel):
            field = model.get_field(index.row())
        else:
            pass
        if field is not None and field.get_tpe() in (
            ProceduralFieldType.MODE_REFERENCE,
            ProceduralFieldType.VARIABLE_REFERENCE,
            ProceduralFieldType.RUNTIME_REFERENCE,
            ProceduralFieldType.TARGET_REFERENCE,
        ):
            combo: QtWidgets.QComboBox = QtWidgets.QComboBox(parent)
            option_item: tuple[str, str]
            for option_item in self._get_reference_options(field.get_tpe()):
                combo.addItem(option_item[0], option_item[1])
            return combo
        else:
            editor: QtWidgets.QLineEdit = QtWidgets.QLineEdit(parent)
            return editor

    def _get_reference_options(self, field_tpe: ProceduralFieldType) -> List[tuple[str, str]]:
        """
        Return qualified labels and canonical names for one reference role.

        :param field_tpe: Value supplied for ``field_tpe``.
        :return: Qualified labels and canonical names for one reference role.
        """
        options: List[tuple[str, str]] = list()
        if field_tpe == ProceduralFieldType.MODE_REFERENCE:
            mode: RuntimeModeDraft
            for mode in self._drafts.get_active_modes():
                options.append((f"{mode.get_owner().name} / {mode.get_name()}", mode.get_name()))
        else:
            owner: Block
            for owner in self._drafts.get_root().get_all_blocks():
                variables: List[Var] = list()
                if field_tpe == ProceduralFieldType.VARIABLE_REFERENCE:
                    groups: tuple[Sequence[Var], ...] = (
                        owner.in_vars, owner.state_vars, owner.algebraic_vars, owner.diff_vars, owner.out_vars)
                elif field_tpe == ProceduralFieldType.RUNTIME_REFERENCE:
                    groups = (tuple(owner.event_dict.keys()), tuple(owner.mode_dict.keys()))
                else:
                    groups = (
                        owner.state_vars,
                        owner.algebraic_vars,
                        tuple(owner.event_dict.keys()),
                        tuple(owner.mode_dict.keys()),
                    )
                group: Sequence[Var]
                variable: Var
                for group in groups:
                    for variable in group:
                        if variable not in variables:
                            variables.append(variable)
                        else:
                            pass
                for variable in variables:
                    options.append((f"{owner.name} / {variable.name}", variable.name))
        options.sort(key=get_reference_option_sort_key)
        return options

    def setEditorData(self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex) -> None:
        """
        Load the staged field value into its typed editor.

        :param editor: Value supplied for ``editor``.
        :param index: Value supplied for ``index``.
        :return: None.
        """
        current_value: str = str(index.data(Qt.ItemDataRole.EditRole))
        if isinstance(editor, QtWidgets.QComboBox):
            item_index: int = editor.findData(current_value)
            editor.setCurrentIndex(item_index)
        elif isinstance(editor, QtWidgets.QLineEdit):
            editor.setText(current_value)
        else:
            pass

    def setModelData(self,
                     editor: QtWidgets.QWidget,
                     model: QtCore.QAbstractItemModel,
                     index: QtCore.QModelIndex) -> None:
        """
        Commit the typed editor value to the field model.

        :param editor: Value supplied for ``editor``.
        :param model: Value supplied for ``model``.
        :param index: Value supplied for ``index``.
        :return: None.
        """
        if isinstance(editor, QtWidgets.QComboBox):
            selected_data: object = editor.currentData()
            model.setData(index, "" if selected_data is None else str(selected_data))
        elif isinstance(editor, QtWidgets.QLineEdit):
            model.setData(index, editor.text())
        else:
            pass


def get_reference_option_sort_key(option: tuple[str, str]) -> str:
    """
    Return a stable case-insensitive reference-option sort key.

    :param option: Value supplied for ``option``.
    :return: A stable case-insensitive reference-option sort key.
    """
    return option[0].lower()


def configure_runtime_table_header(header: QtWidgets.QHeaderView,
                                   initial_widths: Sequence[int]) -> None:
    """Allow manual resizing of every runtime-logic table column.

    :param header: Horizontal header being configured.
    :param initial_widths: Readable initial width for each available column.
    :return: None.
    """
    header.setStretchLastSection(False)
    column_index: int
    for column_index in range(header.count()):
        header.setSectionResizeMode(
            column_index,
            QtWidgets.QHeaderView.ResizeMode.Interactive,
        )
        if column_index < len(initial_widths):
            header.resizeSection(column_index, initial_widths[column_index])
        else:
            pass


class RuntimeLogicEditorWidget(QtWidgets.QWidget):
    """Complete retained-mode and procedural-logic editor tab."""

    __slots__ = (
        "_drafts",
        "_namespace",
        "_entry_model",
        "_mode_model",
        "_field_model",
        "_entry_table",
        "_mode_table",
        "_field_table",
        "_owner_combo",
        "_type_combo",
        "_new_entry_name",
        "_new_mode_owner",
        "_new_mode_name",
        "_new_mode_initial",
        "_entry_name",
        "_documentation",
        "_status",
        "_selected_entry_row",
    )

    changed = Signal()

    def __init__(self,
                 root: Block,
                 namespace: Mapping[str, Expr],
                 parent: QtWidgets.QWidget | None = None) -> None:
        """Build the runtime logic page over detached drafts.

        :param root: Dialogue root block.
        :param namespace: Current symbolic namespace.
        :param parent: Parent widget.
        :return: None.
        """
        super().__init__(parent)
        self._drafts: RuntimeLogicDraftCollection = RuntimeLogicDraftCollection(root)
        self._namespace: Dict[str, Expr] = dict(namespace)
        self._entry_model: ProceduralEntryTableModel = ProceduralEntryTableModel(self._drafts, self)
        self._mode_model: RuntimeModeTableModel = RuntimeModeTableModel(self._drafts, self)
        self._field_model: ProceduralFieldTableModel = ProceduralFieldTableModel(self._drafts, self)
        self._entry_table: QtWidgets.QTableView = QtWidgets.QTableView(self)
        self._mode_table: QtWidgets.QTableView = QtWidgets.QTableView(self)
        self._field_table: QtWidgets.QTableView = QtWidgets.QTableView(self)
        self._owner_combo: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        self._type_combo: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        self._new_entry_name: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        self._new_mode_owner: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        self._new_mode_name: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        self._new_mode_initial: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        self._entry_name: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        self._documentation: QtWidgets.QTextBrowser = QtWidgets.QTextBrowser(self)
        self._status: QtWidgets.QLabel = QtWidgets.QLabel(self)
        self._selected_entry_row: int = -1
        self._build_ui(root)
        self._connect_signals()
        if self._entry_model.rowCount() > 0:
            self._entry_table.selectRow(0)
            self.on_entry_selection_changed()
        else:
            self.update_documentation_from_type()

    def _build_ui(self, root: Block) -> None:
        """
        Build entry, mode, field, and documentation views.

        :param root: Value supplied for ``root``.
        :return: None.
        """
        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        splitter: QtWidgets.QSplitter = QtWidgets.QSplitter(Qt.Orientation.Horizontal, self)
        left_tabs: QtWidgets.QTabWidget = QtWidgets.QTabWidget(splitter)
        left_tabs.addTab(self._build_entries_page(root), self.tr("Procedural entries"))
        left_tabs.addTab(self._build_modes_page(root), self.tr("Retained modes"))
        splitter.addWidget(left_tabs)

        right_tabs: QtWidgets.QTabWidget = QtWidgets.QTabWidget(splitter)
        right_tabs.addTab(self._build_configuration_page(), self.tr("Configuration"))
        right_tabs.addTab(self._build_documentation_page(), self.tr("Documentation"))
        splitter.addWidget(right_tabs)
        splitter.setSizes(list((680, 520,)))
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        layout.addWidget(splitter, 1)
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

    def _build_entries_page(self, root: Block) -> QtWidgets.QWidget:
        """
        Build ordered entry list and add/move/delete controls.

        :param root: Value supplied for ``root``.
        :return: Page containing the ordered entry list and its editing controls.
        """
        page: QtWidgets.QWidget = QtWidgets.QWidget(self)
        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(page)
        add_layout: QtWidgets.QGridLayout = QtWidgets.QGridLayout()
        owner: Block
        for owner in root.get_all_blocks():
            self._owner_combo.addItem(owner.name, owner)
        logic_tpe: ProceduralLogicType
        for logic_tpe in ProceduralLogicType:
            if logic_tpe != ProceduralLogicType.Base:
                self._type_combo.addItem(logic_tpe.value, logic_tpe)
            else:
                pass
        self._new_entry_name.setPlaceholderText(self.tr("Entry name"))
        add_button: QtWidgets.QPushButton = QtWidgets.QPushButton(self.tr("Add entry"), page)
        add_button.setObjectName("add_runtime_logic_entry")
        add_layout.addWidget(QtWidgets.QLabel(self.tr("Owner"), page), 0, 0)
        add_layout.addWidget(self._owner_combo, 0, 1)
        add_layout.addWidget(QtWidgets.QLabel(self.tr("Type"), page), 1, 0)
        add_layout.addWidget(self._type_combo, 1, 1)
        add_layout.addWidget(self._new_entry_name, 2, 0, 1, 2)
        add_layout.addWidget(add_button, 3, 0, 1, 2)
        layout.addLayout(add_layout)

        self._entry_table.setModel(self._entry_model)
        self._entry_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self._entry_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        header: QtWidgets.QHeaderView = self._entry_table.horizontalHeader()
        configure_runtime_table_header(
            header,
            list((170, 190, 170, 100, 100, 100,)),
        )
        layout.addWidget(self._entry_table, 1)

        action_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        up_button: QtWidgets.QPushButton = QtWidgets.QPushButton(self.tr("Move up"), page)
        down_button: QtWidgets.QPushButton = QtWidgets.QPushButton(self.tr("Move down"), page)
        delete_button: QtWidgets.QPushButton = QtWidgets.QPushButton(self.tr("Delete"), page)
        validate_button: QtWidgets.QPushButton = QtWidgets.QPushButton(self.tr("Validate runtime logic"), page)
        up_button.setObjectName("move_runtime_logic_up")
        down_button.setObjectName("move_runtime_logic_down")
        delete_button.setObjectName("delete_runtime_logic_entry")
        validate_button.setObjectName("validate_runtime_logic")
        action_layout.addWidget(up_button)
        action_layout.addWidget(down_button)
        action_layout.addWidget(delete_button)
        action_layout.addStretch(1)
        action_layout.addWidget(validate_button)
        layout.addLayout(action_layout)
        return page

    def _build_modes_page(self, root: Block) -> QtWidgets.QWidget:
        """
        Build retained-mode table and safe creation/deletion controls.

        :param root: Value supplied for ``root``.
        :return: Page containing the retained-mode table and its editing controls.
        """
        page: QtWidgets.QWidget = QtWidgets.QWidget(self)
        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(page)
        add_layout: QtWidgets.QGridLayout = QtWidgets.QGridLayout()
        owner: Block
        for owner in root.get_all_blocks():
            self._new_mode_owner.addItem(owner.name, owner)
        self._new_mode_name.setPlaceholderText(self.tr("Mode symbol name"))
        self._new_mode_initial.setPlaceholderText(self.tr("Initial value or expression"))
        self._new_mode_initial.setText("0.0")
        add_mode_button: QtWidgets.QPushButton = QtWidgets.QPushButton(self.tr("Add retained mode"), page)
        add_mode_button.setObjectName("add_runtime_mode")
        add_layout.addWidget(QtWidgets.QLabel(self.tr("Owner"), page), 0, 0)
        add_layout.addWidget(self._new_mode_owner, 0, 1)
        add_layout.addWidget(self._new_mode_name, 1, 0, 1, 2)
        add_layout.addWidget(self._new_mode_initial, 2, 0, 1, 2)
        add_layout.addWidget(add_mode_button, 3, 0, 1, 2)
        layout.addLayout(add_layout)
        self._mode_table.setModel(self._mode_model)
        self._mode_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self._mode_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        mode_header: QtWidgets.QHeaderView = self._mode_table.horizontalHeader()
        configure_runtime_table_header(
            mode_header,
            list((170, 190, 170, 170, 210, 120,)),
        )
        layout.addWidget(self._mode_table, 1)
        delete_mode_button: QtWidgets.QPushButton = QtWidgets.QPushButton(self.tr("Delete retained mode"), page)
        delete_mode_button.setObjectName("delete_runtime_mode")
        layout.addWidget(delete_mode_button)
        return page

    def _build_configuration_page(self) -> QtWidgets.QWidget:
        """
        Build selected-entry name and typed field table.

        :return: Page containing the selected-entry name and typed field table.
        """
        page: QtWidgets.QWidget = QtWidgets.QWidget(self)
        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(page)
        form: QtWidgets.QFormLayout = QtWidgets.QFormLayout()
        form.addRow(self.tr("Entry name"), self._entry_name)
        layout.addLayout(form)
        self._field_table.setModel(self._field_model)
        self._field_table.setItemDelegateForColumn(2, ProceduralFieldDelegate(self._drafts, self._field_table))
        field_header: QtWidgets.QHeaderView = self._field_table.horizontalHeader()
        configure_runtime_table_header(field_header, list((190, 150, 420,)))
        layout.addWidget(self._field_table, 1)
        return page

    def _build_documentation_page(self) -> QtWidgets.QWidget:
        """
        Build contextual Markdown documentation viewer.

        :return: Page containing the contextual Markdown documentation viewer.
        """
        page: QtWidgets.QWidget = QtWidgets.QWidget(self)
        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(page)
        self._documentation.setOpenExternalLinks(True)
        layout.addWidget(self._documentation)
        return page

    def _connect_signals(self) -> None:
        """
        Connect every runtime-logic action to an explicit slot.

        :return: None.
        """
        add_entry: QtWidgets.QPushButton | None = self.findChild(QtWidgets.QPushButton, "add_runtime_logic_entry")
        move_up: QtWidgets.QPushButton | None = self.findChild(QtWidgets.QPushButton, "move_runtime_logic_up")
        move_down: QtWidgets.QPushButton | None = self.findChild(QtWidgets.QPushButton, "move_runtime_logic_down")
        delete_entry: QtWidgets.QPushButton | None = self.findChild(QtWidgets.QPushButton, "delete_runtime_logic_entry")
        validate_button: QtWidgets.QPushButton | None = self.findChild(QtWidgets.QPushButton, "validate_runtime_logic")
        add_mode: QtWidgets.QPushButton | None = self.findChild(QtWidgets.QPushButton, "add_runtime_mode")
        delete_mode: QtWidgets.QPushButton | None = self.findChild(QtWidgets.QPushButton, "delete_runtime_mode")
        if add_entry is not None:
            add_entry.clicked.connect(self.add_entry)
        else:
            pass
        if move_up is not None:
            move_up.clicked.connect(self.move_entry_up)
        else:
            pass
        if move_down is not None:
            move_down.clicked.connect(self.move_entry_down)
        else:
            pass
        if delete_entry is not None:
            delete_entry.clicked.connect(self.delete_entry)
        else:
            pass
        if validate_button is not None:
            validate_button.clicked.connect(self.validate_runtime_logic)
        else:
            pass
        if add_mode is not None:
            add_mode.clicked.connect(self.add_mode)
        else:
            pass
        if delete_mode is not None:
            delete_mode.clicked.connect(self.delete_mode)
        else:
            pass
        self._entry_table.selectionModel().selectionChanged.connect(self.on_entry_selection_changed)
        self._entry_name.editingFinished.connect(self.on_entry_name_edited)
        self._type_combo.currentIndexChanged.connect(self.update_documentation_from_type)
        self._field_model.dataChanged.connect(self.on_draft_changed)
        self._entry_model.dataChanged.connect(self.on_draft_changed)
        self._mode_model.dataChanged.connect(self.on_draft_changed)

    @QtCore.Slot()
    def add_entry(self) -> None:
        """
        Stage one entry using the selected owner and type.

        :return: None.
        """
        owner_data: object = self._owner_combo.currentData()
        type_data: object = self._type_combo.currentData()
        name: str = self._new_entry_name.text().strip()
        if not isinstance(owner_data, Block) or not isinstance(type_data, ProceduralLogicType):
            self._show_error(self.tr("Select a valid owner and procedural type."))
        elif len(name) == 0:
            self._show_error(self.tr("Enter a procedural entry name."))
        else:
            self._drafts.add_entry(owner_data, type_data, name)
            self._entry_model.reload()
            row: int = self._entry_model.rowCount() - 1
            self._entry_table.selectRow(row)
            self._new_entry_name.clear()
            self.changed.emit()

    @QtCore.Slot()
    def add_mode(self) -> None:
        """
        Stage one retained mode and its initial expression.

        :return: None.
        """
        owner_data: object = self._new_mode_owner.currentData()
        name: str = self._new_mode_name.text().strip()
        initial_expression: str = self._new_mode_initial.text().strip()
        if not isinstance(owner_data, Block):
            self._show_error(self.tr("Select a valid owner block."))
        elif len(name) == 0 or not name.isidentifier():
            self._show_error(self.tr("Enter a valid retained-mode symbol name."))
        elif len(initial_expression) == 0:
            self._show_error(self.tr("Enter an initial value or expression."))
        else:
            self._drafts.add_mode(owner_data, name, initial_expression)
            self._mode_model.reload()
            self._field_model.reload()
            self._new_mode_name.clear()
            self._new_mode_initial.setText("0.0")
            self.changed.emit()

    def _get_selected_entry_row(self) -> int:
        """
        Return the selected entry row or ``-1``.

        :return: The selected entry row or ``-1``.
        """
        selected: List[QtCore.QModelIndex] = self._entry_table.selectionModel().selectedRows()
        if len(selected) == 1:
            result: int = selected[0].row()
        else:
            result = -1
        return result

    @QtCore.Slot()
    def delete_entry(self) -> None:
        """
        Remove the selected procedural entry draft.

        :return: None.
        """
        row: int = self._get_selected_entry_row()
        if self._drafts.remove_entry(row):
            self._entry_model.reload()
            self._mode_model.reload()
            self._field_model.set_entry(None)
            self._selected_entry_row = -1
            self.changed.emit()
        else:
            self._show_error(self.tr("Select one procedural entry to delete."))

    @QtCore.Slot()
    def move_entry_up(self) -> None:
        """
        Move the selected entry one owner-local position earlier.

        :return: None.
        """
        self._move_selected_entry(-1)

    @QtCore.Slot()
    def move_entry_down(self) -> None:
        """
        Move the selected entry one owner-local position later.

        :return: None.
        """
        self._move_selected_entry(1)

    def _move_selected_entry(self, delta: int) -> None:
        """Move the selected entry and restore selection.

        :param delta: Requested movement direction.
        :return: None.
        """
        row: int = self._get_selected_entry_row()
        new_row: int = self._drafts.move_entry(row, delta)
        self._entry_model.reload()
        if new_row >= 0:
            self._entry_table.selectRow(new_row)
        else:
            pass
        if new_row != row:
            self.changed.emit()
        else:
            pass

    @QtCore.Slot()
    def delete_mode(self) -> None:
        """
        Stage deletion of an unreferenced retained mode.

        :return: None.
        """
        selected: List[QtCore.QModelIndex] = self._mode_table.selectionModel().selectedRows()
        row: int = selected[0].row() if len(selected) == 1 else -1
        removed: bool
        message: str
        removed, message = self._drafts.remove_mode(row)
        if removed:
            self._mode_model.reload()
            self._field_model.reload()
            self.changed.emit()
        else:
            self._show_error(message)

    @QtCore.Slot()
    def on_entry_selection_changed(self) -> None:
        """
        Load fields and documentation for the selected entry.

        :return: None.
        """
        row: int = self._get_selected_entry_row()
        entries: List[ProceduralLogicDraft] = self._drafts.get_entries()
        if 0 <= row < len(entries):
            entry: ProceduralLogicDraft = entries[row]
            self._selected_entry_row = row
            self._entry_name.setText(entry.get_name())
            self._entry_name.setEnabled(True)
            self._field_model.set_entry(entry)
            self._load_documentation(entry.get_logic_tpe())
        else:
            self._selected_entry_row = -1
            self._entry_name.clear()
            self._entry_name.setEnabled(False)
            self._field_model.set_entry(None)

    @QtCore.Slot()
    def on_entry_name_edited(self) -> None:
        """
        Stage the selected entry name edit.

        :return: None.
        """
        entries: List[ProceduralLogicDraft] = self._drafts.get_entries()
        if 0 <= self._selected_entry_row < len(entries):
            entries[self._selected_entry_row].set_name(self._entry_name.text())
            self._drafts.mark_changed()
            self._entry_model.reload()
            self._entry_table.selectRow(self._selected_entry_row)
            self.changed.emit()
        else:
            pass

    @QtCore.Slot()
    def on_draft_changed(self) -> None:
        """
        Refresh dependency summaries after one field edit.

        :return: None.
        """
        self._entry_model.reload()
        self._mode_model.reload()
        self.changed.emit()

    @QtCore.Slot()
    def update_documentation_from_type(self) -> None:
        """
        Show documentation for the type selected in the Add controls.

        :return: None.
        """
        selected_tpe: object = self._type_combo.currentData()
        if isinstance(selected_tpe, ProceduralLogicType):
            self._load_documentation(selected_tpe)
        else:
            self._documentation.clear()

    def _load_documentation(self, logic_tpe: ProceduralLogicType) -> None:
        """Load one procedural Markdown page.

        :param logic_tpe: Type whose documentation is requested.
        :return: None.
        """
        repository_root: Path = Path(__file__).resolve().parents[4]
        documentation_path: Path = (
            repository_root / "doc" / "md_source" / "dyn_templates" /
            "procedural_logic" / f"{logic_tpe.value}.md"
        )
        if documentation_path.is_file():
            markdown: str = documentation_path.read_text(encoding="utf-8")
            self._documentation.setMarkdown(markdown)
            self._documentation.document().setBaseUrl(
                QtCore.QUrl.fromLocalFile(str(documentation_path.parent) + "/")
            )
        else:
            self._documentation.setMarkdown(
                f"# {logic_tpe.value}\n\nNo procedural-logic documentation file was found."
            )

    @QtCore.Slot()
    def validate_runtime_logic(self) -> None:
        """
        Validate all retained modes and procedural entries and show every issue.

        :return: None.
        """
        result: RuntimeLogicValidationResult = self.validate(self._namespace)
        if result.is_valid():
            warnings: List[str] = result.get_warnings()
            self._status.setStyleSheet("color: #16825d;")
            if len(warnings) > 0:
                self._status.setText(self.tr("Valid runtime logic. Warnings: ") + " | ".join(warnings))
            else:
                self._status.setText(self.tr("Runtime logic is valid."))
        else:
            self._status.setStyleSheet("color: #b42318;")
            self._status.setText(" | ".join(result.get_errors()))

    def validate(self, namespace: Mapping[str, Expr]) -> RuntimeLogicValidationResult:
        """Validate drafts and refresh field/table error presentation.

        :param namespace: Current joint DAE namespace.
        :return: Complete validation result.
        """
        self._namespace = dict(namespace)
        result: RuntimeLogicValidationResult = self._drafts.validate(namespace)
        self._entry_model.reload()
        self._mode_model.reload()
        self._field_model.reload()
        return result

    def build_validation_namespace(self, namespace: Mapping[str, Expr]) -> Dict[str, Expr]:
        """
        :param namespace: Value supplied for ``namespace``.
        :return: A namespace including staged retained modes.
        """
        return self._drafts.build_validation_namespace(namespace)

    def has_changes(self) -> bool:
        """
        :return: Whether runtime-logic edits are staged.
        """
        return self._drafts.has_changes()

    def has_new_modes(self) -> bool:
        """
        :return: Whether new authoritative mode Vars are required.
        """
        return self._drafts.has_new_modes()

    def apply_to_blocks(self,
                        var_factory: VarFactory,
                        namespace: Mapping[str, Expr]) -> Dict[str, Expr]:
        """
        Apply validated modes and logic entries and return final namespace.

        :param var_factory: Factory that owns symbolic variables.
        :param namespace: Value supplied for ``namespace``.
        :return: Final namespace.
        """
        return self._drafts.apply_to_blocks(var_factory, namespace)

    def prepare_to_delete(self) -> None:
        """Detach view models and clear documentation before Qt destruction.

        :return: None.
        """
        self._entry_table.setModel(None)
        self._mode_table.setModel(None)
        self._field_table.setModel(None)
        self._documentation.clear()
        self._entry_name.clear()

    def _show_error(self, message: str) -> None:
        """
        Show one local runtime-logic error.

        :param message: Value supplied for ``message``.
        :return: None.
        """
        self._status.setStyleSheet("color: #b42318;")
        self._status.setText(message)
