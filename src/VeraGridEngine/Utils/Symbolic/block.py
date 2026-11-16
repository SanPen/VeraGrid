# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import copy
import math
import uuid
from typing import List, Dict, Any, Tuple, TYPE_CHECKING
from typing import Iterable, Mapping, Sequence

from VeraGridEngine.Utils.Symbolic.symbolic import Var, Const, Expr, BinOp, _expr_to_dict, Comparison
from VeraGridEngine.Devices.Diagrams.block_diagram import BlockDiagram
from VeraGridEngine.enumerations import (
    ParamPowerFlowReferenceType,
    RmsPhysicalMeterKind,
    RmsTerminalSide,
    VarPowerFlowReferenceType,
)
from VeraGridEngine.Utils.Symbolic.compare_expressions_structure import equivalent_systems, structural_hash
from VeraGridEngine.Utils.Symbolic.dynamic_connection_intent import (DynamicConnectionIntent,
                                                                     DynamicConnectionIntentDirection,
                                                                     DynamicConnectionIntentOrigin,
                                                                     dynamic_connection_intent_to_dict,
                                                                     reconcile_dynamic_connection_intent_target)
from VeraGridEngine.Utils.Symbolic.variable_alignment_engine import align_variables, VariableAlignmentData
from VeraGridEngine.Utils.procedural_logic_contract import ProceduralLogicData

if TYPE_CHECKING:
    from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_bundle import JMartiFitBundle
    from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_runtime_data import JMartiRuntimeData
    from VeraGridEngine.Utils.procedural_logic import ProceduralLogicBase, ProceduralLogicCodec
else:
    pass

PersistedScalar = str | int | float | bool | None
PersistedRecord = Dict[str, "PersistedValue"]
PersistedRecordMap = Dict[str, PersistedRecord]
PersistedValue = PersistedScalar | List["PersistedValue"] | PersistedRecord | PersistedRecordMap


def normalize_event_parameter_initialization(block: "Block") -> None:
    """Move legacy event-parameter initialization into ``event_dict``.

    Older templates represented one runtime parameter twice: ``event_dict``
    contained ``Const(None)`` while ``init_eqs`` contained the actual initial
    expression. Event parameters now own their scalar value or initialization
    expression directly in ``event_dict``. If a legacy entry already contains
    a concrete event expression, that expression remains authoritative, matching
    the precedence historically used by explicit initialization.

    Variable UIDs are used for matching because loaded or reconstructed blocks
    can contain distinct Python objects representing the same symbolic identity.

    :param block: Root block whose complete child tree is normalized in place.
    :return: None.
    """
    pending_blocks: List[Block] = list((block,))
    pending_index: int = 0
    while pending_index < len(pending_blocks):
        current_block: Block = pending_blocks[pending_index]
        pending_index += 1

        event_variables_by_uid: Dict[int, Var] = dict()
        event_variable: Var
        for event_variable in current_block.event_dict:
            event_variables_by_uid[event_variable.uid] = event_variable

        init_variables_to_remove: List[Var] = list()
        init_variable: Var
        init_expression: Expr
        for init_variable, init_expression in current_block.init_eqs.items():
            matching_event_variable: Var | None = event_variables_by_uid.get(init_variable.uid, None)
            if matching_event_variable is None:
                pass
            else:
                event_expression: Expr | Const = current_block.event_dict[matching_event_variable]
                if isinstance(event_expression, Const) and event_expression.value is None:
                    current_block.event_dict[matching_event_variable] = init_expression
                else:
                    # A concrete event expression already had precedence in the
                    # unified explicit-initialization dependency graph.
                    pass
                init_variables_to_remove.append(init_variable)

        for init_variable in init_variables_to_remove:
            del current_block.init_eqs[init_variable]

        child_block: Block
        for child_block in current_block.children:
            pending_blocks.append(child_block)


class RmsTerminalPowerContribution:
    """Declare one device power flow consumed by the RMS nodal assembler.

    ``FROM`` and ``TO`` references use the branch convention: a positive value
    flows from the connected bus into the device, so the network assembler
    contributes its negative to the bus injection. ``BUS`` references already
    use the device-to-network injection convention and retain their sign. The
    declaration stores semantic references only and never retains a second
    symbolic variable graph.
    """

    __slots__ = (
        "_terminal_side",
        "_active_power_reference",
        "_reactive_power_reference",
    )

    def __init__(
            self,
            terminal_side: RmsTerminalSide,
            active_power_reference: VarPowerFlowReferenceType,
            reactive_power_reference: VarPowerFlowReferenceType | None,
    ) -> None:
        """Create one typed terminal power declaration.

        :param terminal_side: Physical device terminal resolved by topology.
        :param active_power_reference: Active-power variable in the owning block.
        :param reactive_power_reference: Reactive-power variable, or None for a DC terminal.
        :return: None.
        """
        if terminal_side is RmsTerminalSide.BUS:
            if active_power_reference is VarPowerFlowReferenceType.P:
                pass
            else:
                raise ValueError("RMS bus-terminal active power must use P")
            if reactive_power_reference in (None, VarPowerFlowReferenceType.Q):
                pass
            else:
                raise ValueError("RMS bus-terminal reactive power must use Q or null")
        else:
            if terminal_side is RmsTerminalSide.FROM:
                if active_power_reference is VarPowerFlowReferenceType.Pf:
                    pass
                else:
                    raise ValueError("RMS from-terminal active power must use Pf")
                if reactive_power_reference in (None, VarPowerFlowReferenceType.Qf):
                    pass
                else:
                    raise ValueError("RMS from-terminal reactive power must use Qf or null")
            else:
                if terminal_side is RmsTerminalSide.TO:
                    if active_power_reference is VarPowerFlowReferenceType.Pt:
                        pass
                    else:
                        raise ValueError("RMS to-terminal active power must use Pt")
                    if reactive_power_reference in (None, VarPowerFlowReferenceType.Qt):
                        pass
                    else:
                        raise ValueError("RMS to-terminal reactive power must use Qt or null")
                else:
                    raise TypeError("RMS terminal side must be a RmsTerminalSide")

        self._terminal_side: RmsTerminalSide = terminal_side
        self._active_power_reference: VarPowerFlowReferenceType = active_power_reference
        self._reactive_power_reference: VarPowerFlowReferenceType | None = reactive_power_reference

    def get_terminal_side(self) -> RmsTerminalSide:
        """Return the physical terminal selected by network topology.

        :return: Declared terminal side.
        """
        return self._terminal_side

    def get_active_power_reference(self) -> VarPowerFlowReferenceType:
        """Return the active-power reference owned by the symbolic block.

        :return: Active-power reference.
        """
        return self._active_power_reference

    def get_reactive_power_reference(self) -> VarPowerFlowReferenceType | None:
        """Return the reactive-power reference for an AC terminal.

        :return: Reactive-power reference, or None for a DC terminal.
        """
        return self._reactive_power_reference

    def to_data(self) -> PersistedRecord:
        """Return a declarative representation without symbolic objects.

        :return: Version-owned terminal power data.
        """
        reactive_reference: str | None
        if self._reactive_power_reference is None:
            reactive_reference = None
        else:
            reactive_reference = self._reactive_power_reference.value
        return {
            "terminal_side": self._terminal_side.value,
            "active_power_reference": self._active_power_reference.value,
            "reactive_power_reference": reactive_reference,
        }


def rms_terminal_power_contribution_from_data(
        data: PersistedRecord,
) -> RmsTerminalPowerContribution:
    """Reconstruct one fail-closed terminal power declaration.

    :param data: Declarative terminal power data.
    :return: Reconstructed typed declaration.
    """
    expected_keys: set[str] = {"terminal_side", "active_power_reference", "reactive_power_reference"}
    actual_keys: set[str] = set(data.keys())
    if actual_keys == expected_keys:
        pass
    else:
        raise KeyError(
            "RMS terminal power keys do not match the contract: "
            f"missing={sorted(expected_keys - actual_keys)}, "
            f"extra={sorted(actual_keys - expected_keys)}"
        )

    raw_terminal_side: PersistedValue = data["terminal_side"]
    raw_active_reference: PersistedValue = data["active_power_reference"]
    raw_reactive_reference: PersistedValue = data["reactive_power_reference"]
    if isinstance(raw_terminal_side, str):
        terminal_side: RmsTerminalSide = RmsTerminalSide(raw_terminal_side)
    else:
        raise TypeError("RMS terminal side must be a string")

    if isinstance(raw_active_reference, str):
        active_reference: VarPowerFlowReferenceType = VarPowerFlowReferenceType(raw_active_reference)
    else:
        raise TypeError("RMS terminal active-power reference must be a string")

    if raw_reactive_reference is None:
        reactive_reference: VarPowerFlowReferenceType | None = None
    else:
        if isinstance(raw_reactive_reference, str):
            reactive_reference = VarPowerFlowReferenceType(raw_reactive_reference)
        else:
            raise TypeError("RMS terminal reactive-power reference must be a string or null")

    return RmsTerminalPowerContribution(
        terminal_side=terminal_side,
        active_power_reference=active_reference,
        reactive_power_reference=reactive_reference,
    )


class DynamicModelContract:
    """Store typed dynamic-behavior declarations owned by one symbolic block.

    The contract contains semantic references, scalar flags, symbolic UIDs and
    serializable template selections. It therefore preserves the canonical
    ``Block`` object graph instead of retaining import parser objects or
    references to a second dynamic-model representation. Physical declarations
    state quantity ownership while ``MultiCircuit`` remains the only source of
    bus topology.
    """

    __slots__ = (
        'modal_template_config',
        'modal_template_kind',
    )

    def __init__(self) -> None:
        """
        Initialize an empty fail-closed dynamic-model contract.

        :return: None.
        """
        self.modal_template_kind: str | None = None
        self.modal_template_config: Dict[str, str | int | float | bool | None] | None = None

    def to_data(self) -> PersistedRecord:
        """Return the versioned declarative dynamic-model contract.

        :return: Data-only contract suitable for canonical block persistence.
        """
        return {
            "version": 15,
            "modal_template_kind": self.modal_template_kind,
            "modal_template_config": (
                None
                if self.modal_template_config is None
                else dict(self.modal_template_config)
            ),
        }


def _read_required_dynamic_contract_field(
        data: Mapping[str, PersistedValue],
        field_name: str,
) -> PersistedValue:
    """Read one required field from a present versioned contract.

    :param data: Versioned dynamic-model contract data.
    :param field_name: Exact required field name.
    :return: Stored field value, including an explicit ``None``.
    """
    if field_name in data:
        return data[field_name]
    else:
        raise KeyError(
            f"Dynamic-model contract field '{field_name}' is missing"
        )


def _read_nullable_dynamic_contract_boolean(
        data: PersistedRecord,
        field_name: str,
) -> bool | None:
    """Read one required field whose declared value may be boolean or null.

    :param data: Versioned dynamic-model contract data.
    :param field_name: Exact required field whose value may be nullable.
    :return: Declared boolean, or ``None`` for the explicit inapplicable state.
    """
    value: PersistedValue = _read_required_dynamic_contract_field(data, field_name)
    if value is None:
        return None
    else:
        if isinstance(value, bool):
            return value
        else:
            raise TypeError(
                f"Dynamic-model contract field '{field_name}' must be boolean or null"
            )


def _read_nullable_dynamic_contract_symbolic_uid(
        data: PersistedRecord,
        field_name: str,
) -> int | None:
    """Read one required symbolic-UID field whose value may be null.

    :param data: Versioned dynamic-model contract data.
    :param field_name: Exact required field containing a symbolic UID.
    :return: Integer symbolic UID, or ``None`` when no variable is declared.
    """
    value: PersistedValue = _read_required_dynamic_contract_field(data, field_name)
    if value is None:
        return None
    else:
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        else:
            raise TypeError(
                f"Dynamic-model contract field '{field_name}' must be an integer or null"
            )


def _read_nullable_dgs_open_resistance_ohm(
        data: PersistedRecord,
) -> float | None:
    """Reconstruct the DGS actuator resistance used for an open branch.

    The version-1 field is required even when no open-state resistance applies;
    that inapplicable state is represented by an explicit ``None``. Integer and
    floating-point encodings are accepted because both are losslessly converted
    to the runtime floating-point representation, while booleans and non-finite
    values are rejected to keep the electrical declaration fail-closed.

    :param data: Versioned dynamic-model contract containing the required
        ``dgs_open_resistance_ohm`` field.
    :return: Finite open-state resistance in ohms, or ``None`` when the block
        does not declare that actuator projection.
    """
    field_name: str = "dgs_open_resistance_ohm"
    value: PersistedValue = _read_required_dynamic_contract_field(data, field_name)
    if value is None:
        return None
    else:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            numeric_value: float = float(value)
            if math.isfinite(numeric_value):
                return numeric_value
            else:
                raise ValueError(
                    f"Dynamic-model contract field '{field_name}' must be finite"
                )
        else:
            raise TypeError(
                f"Dynamic-model contract field '{field_name}' must be numeric or null"
            )


def _read_nullable_dgs_logical_actuator_root_id(
        data: PersistedRecord,
) -> str | None:
    """Reconstruct the source DGS identity shared by one logical actuator.

    The field itself is mandatory in version 1. An explicit ``None`` states
    that the block is not a member of a logical-actuator group; otherwise the
    exact string is retained so imported actuator fragments can be associated
    without retaining source parser objects.

    :param data: Versioned dynamic-model contract containing the required
        ``dgs_logical_actuator_root_id`` field.
    :return: Exact DGS logical-actuator root identifier, or ``None`` when the
        block has no logical-actuator association.
    """
    field_name: str = "dgs_logical_actuator_root_id"
    value: PersistedValue = _read_required_dynamic_contract_field(data, field_name)
    if value is None:
        return None
    else:
        if isinstance(value, str):
            return value
        else:
            raise TypeError(
                f"Dynamic-model contract field '{field_name}' must be a string or null"
            )


def _read_nullable_modal_template_kind(
        data: PersistedRecord,
) -> str | None:
    """Read the optional generated-template identifier.

    :param data: Versioned dynamic-model contract data.
    :return: Persisted template identifier, or ``None`` when not applicable.
    """
    value: PersistedValue = _read_required_dynamic_contract_field(
        data,
        "modal_template_kind",
    )
    if value is None:
        return None
    else:
        if isinstance(value, str):
            return value
        else:
            raise TypeError(
                "Dynamic-model contract field 'modal_template_kind' must be a string or null"
            )


def read_nullable_modal_template_config(
        data: Mapping[str, PersistedValue],
) -> Dict[str, str | int | float | bool | None] | None:
    """Read scalar modal-template selections without interpreting their names.

    Template builders own the meaning of each field. The symbolic persistence
    layer only validates that the mapping is data-only and can be serialized
    safely without retaining GUI objects or enum instances.

    :param data: Versioned dynamic-model contract data.
    :return: Independent scalar configuration mapping, or ``None``.
    """
    value: PersistedValue = _read_required_dynamic_contract_field(
        data,
        "modal_template_config",
    )
    if value is None:
        return None
    else:
        if isinstance(value, dict):
            result: Dict[str, str | int | float | bool | None] = dict()
            raw_key: str
            raw_value: str | int | float | bool | None
            for raw_key, raw_value in value.items():
                has_valid_key: bool = isinstance(raw_key, str)
                has_valid_value: bool = (
                        raw_value is None
                        or isinstance(raw_value, (str, bool, int, float))
                )
                if has_valid_key and has_valid_value:
                    result[raw_key] = raw_value
                else:
                    raise TypeError(
                        "Dynamic-model modal template configuration must contain "
                        "string keys and scalar values"
                    )
            else:
                pass
            return result
        else:
            raise TypeError(
                "Dynamic-model contract field 'modal_template_config' must be a mapping or null"
            )


def _read_rms_terminal_power_contributions(
        data: PersistedRecord,
) -> List[RmsTerminalPowerContribution]:
    """Read the ordered terminal contributions declared by one RMS model.

    :param data: Versioned dynamic-model contract data.
    :return: Validated terminal power declarations.
    """
    field_name: str = "rms_terminal_power_contributions"
    value: PersistedValue = _read_required_dynamic_contract_field(data, field_name)
    if isinstance(value, list):
        result: List[RmsTerminalPowerContribution] = list()
        item: PersistedValue
        for item in value:
            if isinstance(item, dict):
                normalized_item: PersistedRecord = dict()
                raw_key: str
                raw_value: PersistedValue
                for raw_key, raw_value in item.items():
                    if isinstance(raw_key, str):
                        normalized_item[raw_key] = raw_value
                    else:
                        raise TypeError(
                            "RMS terminal power field names must be strings"
                        )
                else:
                    pass
                result.append(
                    rms_terminal_power_contribution_from_data(normalized_item)
                )
            else:
                raise TypeError(
                    "RMS terminal power contributions must be declarative mappings"
                )
        else:
            pass
        return result
    else:
        raise TypeError(
            f"Dynamic-model contract field '{field_name}' must be a list"
        )


def dynamic_model_contract_from_data(data: PersistedRecord) -> DynamicModelContract:
    """Reconstruct one fail-closed versioned dynamic-model contract.

    :param data: Declarative contract data.
    :return: Reconstructed contract with obsolete historical fields discarded.
    """
    version: PersistedValue = _read_required_dynamic_contract_field(data, "version")
    if isinstance(version, int) and not isinstance(version, bool):
        version_number: int = version
    else:
        raise TypeError("Dynamic-model contract version must be an integer")
    if version_number in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15):
        pass
    else:
        raise ValueError("Unsupported dynamic-model contract version")

    result: DynamicModelContract = DynamicModelContract()
    expected_keys: set[str] = set(result.to_data().keys())
    actual_keys: set[str] = set(data.keys())
    # Grounding initialization is owned by symbolic equations in current models.
    if version_number < 14:
        actual_keys.discard("emt_internal_grounding_link")
    else:
        pass
    # Legacy terminal declarations are superseded by canonical current mappings.
    if version_number < 13:
        actual_keys.discard("emt_terminal_current_contributions")
    else:
        pass
    # Historical override expressions no longer participate in initialization.
    if version_number < 12:
        actual_keys.discard("explicit_init_override_init_exprs")
    else:
        pass
    # Retired exclusions are ignored when loading historical initialization data.
    if version_number < 11:
        actual_keys.discard("explicit_init_excluded_var_names")
    else:
        pass
    # Old snapshots may carry the retired meter descriptor; it has no runtime role.
    if version_number < 10:
        actual_keys.discard("rms_physical_measurement_point")
    else:
        pass
    if version_number < 9:
        obsolete_keys: set[str] = set((
            'dgs_elmgenstat_runtime_adapter',
            'dgs_elmsvs_remote_voltage_var_uid',
            'dgs_elmsvs_runtime_adapter',
            'dgs_elmsym_active_base_factor_var_uid',
            'dgs_elmsym_angular_frequency_var_uid',
            'dgs_elmsym_excitation_gain_var_uid',
            'dgs_elmsym_network_angle_anchor',
            'dgs_elmsym_rated_field_voltage_var_uid',
            'dgs_elmsym_reference_speed_var_uid',
            'dgs_elmsym_rotor_angle_var_uid',
            'dgs_elmsym_round_rotor',
            'dgs_elmsym_runtime_adapter',
            'dgs_elmsym_runtime_adapter_pending',
            'dgs_elmsym_speed_var_uid',
            'dgs_equipment_owned_signal_names',
            'dgs_explicit_initialization_uids',
            'dgs_logical_actuator_root_id',
            'dgs_open_resistance_ohm',
            'dgs_open_standard_regc_current_pll',
            'dgs_open_standard_regc_voltage_source',
            'rms_conduction_status_var_uid',
            'rms_ideal_ac_connector',
            'rms_ideal_transformer',
            'rms_topology_constraint_status_var_uid',
            'runtime_equipment_shell_sync_names',
            'runtime_equipment_shell_sync_var_uids',
            'runtime_measurement_shell_sync_names',
            'skip_device_local_explicit_init',
            'startup_final_init_replay_var_names',
            'startup_initial_reduced_polish_var_names',
            'startup_ordered_shell_sync_names',
        ))
        actual_keys.difference_update(obsolete_keys)
    else:
        pass
    # Older declarations carry no source capability; do not infer or migrate it.
    if 7 <= version_number < 15:
        expected_keys.add("emt_finite_reciprocal_source_mode_var_uid")
    else:
        pass
    if version_number in (2, 3, 4, 5):
        expected_keys.add("rms_terminal_power_contributions")
    else:
        pass
    if version_number in (1, 2, 3, 4, 5, 6):
        expected_keys.remove("modal_template_kind")
        expected_keys.remove("modal_template_config")
    else:
        pass
    # Both parent branches wrote version 7 with different complete schemas.
    # Select only an exact parent shape before reading its typed declarations.
    if version_number == 7:
        source_keys: set[str] = expected_keys - {"modal_template_kind", "modal_template_config"}
        modal_keys: set[str] = expected_keys - {"emt_finite_reciprocal_source_mode_var_uid"}
        if actual_keys == source_keys:
            expected_keys = source_keys
        elif actual_keys == modal_keys:
            expected_keys = modal_keys
        else:
            raise KeyError("Dynamic-model contract keys do not match either version 7 schema")
    else:
        pass
    if actual_keys == expected_keys:
        pass
    else:
        missing_keys: List[str] = sorted(expected_keys - actual_keys)
        extra_keys: List[str] = sorted(actual_keys - expected_keys)
        raise KeyError(
            f"Dynamic-model contract keys do not match version {version_number}: "
            f"missing={missing_keys}, extra={extra_keys}"
        )
    if version_number in (2, 3, 4, 5):
        # Validate and discard obsolete terminal-power metadata. Runtime
        # assembly derives terminal ownership from canonical mapped references.
        _read_rms_terminal_power_contributions(data)
    else:
        pass
    # Validate historical identities here; the block parser migrates them into
    # external references after reconstructing their canonical parameter owners.
    if "emt_finite_reciprocal_source_mode_var_uid" in expected_keys:
        _read_nullable_dynamic_contract_symbolic_uid(
            data, "emt_finite_reciprocal_source_mode_var_uid"
        )
    else:
        pass
    if "modal_template_kind" in expected_keys:
        result.modal_template_kind = _read_nullable_modal_template_kind(data)
        result.modal_template_config = read_nullable_modal_template_config(data)
    else:
        result.modal_template_kind = None
        result.modal_template_config = None
    return result


def _remember_contract_var_uid(var: Var | None, reachable_uids: set[int]) -> None:
    """Collect one variable identity and its derivative chain.

    :param var: Reachable symbolic variable or ``None``.
    :param reachable_uids: Mutable UID set for one block tree.
    :return: None.
    """
    if var is None:
        pass
    else:
        if var.uid in reachable_uids:
            pass
        else:
            reachable_uids.add(var.uid)
            _remember_contract_var_uid(var.base_var, reachable_uids)
            _remember_contract_var_uid(var.diff_var, reachable_uids)


def _remember_contract_expression_uids(
        expression: Expr | Comparison,
        reachable_uids: set[int],
) -> None:
    """Collect every variable referenced by one symbolic condition.

    :param expression: Symbolic expression or comparison.
    :param reachable_uids: Mutable UID set for one block tree.
    :return: None.
    """
    if isinstance(expression, Comparison):
        _remember_contract_expression_uids(expression.lhs, reachable_uids)
        if isinstance(expression.rhs, Expr):
            _remember_contract_expression_uids(expression.rhs, reachable_uids)
        else:
            pass
    else:
        referenced_var: Var
        for referenced_var in expression.get_vars():
            _remember_contract_var_uid(referenced_var, reachable_uids)


def _collect_contract_reachable_uids(
        block: "Block",
        reachable_uids: set[int] | None = None,
) -> set[int]:
    """Collect all structural and expression-reachable UIDs in a block tree.

    :param block: Root block whose declared graph is inspected.
    :param reachable_uids: Optional accumulator for child recursion.
    :return: Complete reachable UID set.
    """
    if reachable_uids is None:
        result: set[int] = set()
    else:
        result = reachable_uids

    var_list: List[Var]
    for var_list in (
            block.state_vars,
            block.algebraic_vars,
            block.diff_vars,
            block.reformulated_vars,
            block.in_vars,
            block.out_vars,
    ):
        structural_var: Var
        for structural_var in var_list:
            _remember_contract_var_uid(structural_var, result)

    var_mapping: Mapping[Var, Expr | Comparison]
    for var_mapping in (
            block.parameters,
            block.init_values,
            block.init_eqs,
            block.diff_init_eqs,
            block.post_init_seed_eqs,
            block.discrete_eqs,
            block.event_dict,
            block.mode_dict,
            block.boolean_guards,
    ):
        mapping_var: Var
        mapping_value: Expr | Comparison
        for mapping_var, mapping_value in var_mapping.items():
            _remember_contract_var_uid(mapping_var, result)
            _remember_contract_expression_uids(mapping_value, result)

    optional_var: Var | None
    for optional_var in block.external_mapping.values():
        _remember_contract_var_uid(optional_var, result)
    for optional_var in block.api_obj_mapping.values():
        _remember_contract_var_uid(optional_var, result)

    expression_list: Iterable[Expr | Comparison]
    for expression_list in (
            block.state_eqs,
            block.algebraic_eqs,
            block.differential_eqs,
            block.inequalities,
    ):
        expression: Expr | Comparison
        for expression in expression_list:
            _remember_contract_expression_uids(expression, result)

    child: Block
    for child in block.children:
        _collect_contract_reachable_uids(child, result)

    return result


def normalize_dynamic_connection_intents(block: "Block") -> None:
    """
    Keep one current reachable typed state for each connection-intent identity.

    A missing root-interface phase is not considered unreachable because it can
    return after a topology change. An internal block or port outside the owned
    block tree cannot return semantically and its obsolete intent is removed.

    :param block: Block whose intents must be normalized.
    :return: None.
    """
    normalized_entries: List[DynamicConnectionIntent] = list()
    entry: DynamicConnectionIntent
    existing_index: int
    existing_entry: DynamicConnectionIntent
    matching_index: int | None

    for entry in block.connection_intents:
        if reconcile_dynamic_connection_intent_target(intent=entry, root_block=block):
            matching_index = None
            for existing_index, existing_entry in enumerate(normalized_entries):
                if existing_entry.has_same_identity(entry):
                    matching_index = existing_index
                else:
                    pass

            # Replacing the previous value makes the list represent current
            # desired state instead of retaining an edit history.
            if matching_index is None:
                normalized_entries.append(entry)
            else:
                normalized_entries[matching_index] = entry
        else:
            pass

    block.connection_intents = normalized_entries


def find_matching_dynamic_connection_intent(block: "Block",
                                            origin: DynamicConnectionIntentOrigin,
                                            root_reference: VarPowerFlowReferenceType,
                                            direction: DynamicConnectionIntentDirection,
                                            internal_block_uid: int,
                                            internal_variable_uid: int) -> DynamicConnectionIntent | None:
    """
    Find one exact connection-intent record on one block.

    :param block: Root block that owns the persisted intents.
    :param origin: Required provenance.
    :param root_reference: Semantic root-interface reference.
    :param direction: Connection direction.
    :param internal_block_uid: Internal block UID.
    :param internal_variable_uid: Internal variable non-mutable UID.
    :return: Matching record or ``None``.
    """
    entry: DynamicConnectionIntent

    for entry in block.connection_intents:
        if entry.get_origin() != origin:
            pass
        elif entry.get_root_reference() != root_reference:
            pass
        elif entry.get_direction() != direction:
            pass
        elif entry.get_internal_block_uid() != internal_block_uid:
            pass
        elif entry.get_internal_variable_uid() != internal_variable_uid:
            pass
        else:
            return entry

    return None


def upsert_dynamic_connection_intent(block: "Block", intent: DynamicConnectionIntent) -> None:
    """
    Replace the current state of one connection intent on a block.

    :param block: Root block that owns the connection intents.
    :param intent: Current desired connection state.
    :return: None.
    """
    block.connection_intents.append(intent)
    normalize_dynamic_connection_intents(block=block)


def rehash_block_var_keyed_dicts(block_model: "Block") -> None:
    """
    Rebuild every block dictionary whose keys are mutable-UID variables.

    ``Var.__hash__`` depends on ``uid``. Identity alignment can intentionally
    update that value, so all Var-keyed containers must be rebuilt immediately
    afterward to restore valid hash buckets.

    :param block_model: Block whose variable-keyed dictionaries must be rebuilt.
    :return: None.
    """
    block_model.parameters = dict(block_model.parameters.items())
    block_model.init_values = dict(block_model.init_values.items())
    block_model.init_eqs = dict(block_model.init_eqs.items())
    block_model.diff_init_eqs = dict(block_model.diff_init_eqs.items())
    block_model.discrete_eqs = dict(block_model.discrete_eqs.items())
    block_model.event_dict = dict(block_model.event_dict.items())
    block_model.mode_dict = dict(block_model.mode_dict.items())
    block_model.boolean_guards = dict(block_model.boolean_guards.items())


def rehash_block_tree_var_keyed_dicts(root_block: "Block") -> None:
    """
    Rebuild variable-keyed dictionaries throughout one symbolic block tree.

    :param root_block: Root of the block tree to repair.
    :return: None.
    """
    block_model: Block
    for block_model in root_block.get_all_blocks():
        rehash_block_var_keyed_dicts(block_model=block_model)


def refresh_block_tree_var_name_mappings(root_block: "Block") -> None:
    """
    Rebuild algebraic-variable lookups after connected names change.

    :param root_block: Root of the block tree whose names were propagated.
    :return: None.
    """
    block_model: Block
    algebraic_var: Var

    for block_model in root_block.get_all_blocks():
        block_model.var_mapping = dict()
        for algebraic_var in block_model.algebraic_vars:
            block_model.var_mapping[algebraic_var.name] = algebraic_var


def _new_uid() -> int:
    """
    Generate a fresh UUID‑v4 string.
    :return: UUIDv4 in integer format
    """
    return uuid.uuid4().int


def require_declarative_record(
        value: PersistedValue,
        context: str,
) -> PersistedRecord:
    """Validate one persisted JSON-style record with string field names.

    :param value: Imported value expected to contain one declarative record.
    :param context: Domain path included in fail-closed validation messages.
    :return: Independent record whose field names are validated strings.
    """
    if isinstance(value, dict):
        record: PersistedRecord = dict()
        raw_key: str
        raw_value: PersistedValue
        for raw_key, raw_value in value.items():
            if isinstance(raw_key, str):
                record[raw_key] = raw_value
            else:
                raise TypeError(f"{context} field names must be strings")
        else:
            pass
        return record
    else:
        raise TypeError(f"{context} must be a declarative mapping")






class Block:
    """
    Class representing a Block
    """

    __slots__ = (
        'name',
        '_model_family_name',
        'uid',
        'is_decomposable',
        'tpe_uid',
        'vars_glob_name2uid',
        'state_vars',
        'state_eqs',
        'algebraic_vars',
        'algebraic_eqs',
        'inequalities',
        'diff_vars',
        'reformulated_vars',
        'differential_eqs',
        'parameters',
        'init_values',
        'init_eqs',
        'diff_init_eqs',
        'discrete_eqs',
        'post_init_seed_eqs',
        'children',
        'in_vars',
        'out_vars',
        'event_dict',
        'mode_dict',
        'boolean_guards',
        'procedural_logic',
        'connection_intents',
        'external_mapping',
        'api_obj_mapping',
        'var_mapping',
        '_diagram',
        'dynamic_model_contract',
        '_jmarti_fit_bundle',
        '_jmarti_runtime_data',
    )

    def __init__(self,
                 state_vars: List[Var] | None = None,
                 state_eqs: List[Expr] | None = None,
                 algebraic_vars: List[Var] | None = None,
                 algebraic_eqs: List[Expr] | None = None,
                 inequalities: List[Expr | Comparison] | None = None,
                 diff_vars: List[Var] | None = None,
                 reformulated_vars: List[Var] | None = None,
                 differential_eqs: List[Expr] | None = None,
                 parameters: Dict[Var, Const] | None = None,
                 init_values: Dict[Var, Const] | None = None,
                 init_eqs: Dict[Var, Expr] | None = None,
                 diff_init_eqs: Dict[Var, Expr] | None = None,
                 discrete_eqs: Dict[Var, Expr] | None = None,
                 post_init_seed_eqs: Dict[Var, Expr | Const] | None = None,
                 children: List["Block"] | None = None,
                 in_vars: List[Var] | None = None,
                 out_vars: List[Var] | None = None,
                 event_dict: Dict[Var, Expr] | None = None,
                 mode_dict: Dict[Var, Expr] | None = None,
                 boolean_guards: Dict[Var, Expr | Comparison] | None = None,
                 procedural_logic: Iterable["ProceduralLogicBase"] | None = None,
                 connection_intents: List[DynamicConnectionIntent] | None = None,
                 external_mapping: Dict[VarPowerFlowReferenceType, Var | None] | None = None,
                 api_obj_mapping: Dict[ParamPowerFlowReferenceType, Var | None] | None = None,
                 is_decomposable: bool = True,
                 name: str = "",
                 uid: int | None = None,
                 model_family_name: str = ""):
        """
        This represents a group of equations or a group of blocks

        :param state_vars: Differential state variables solved by the block.
        :param state_eqs: Right-hand-side equations associated with ``state_vars``.
        :param algebraic_vars: Non-differential variables solved by the block.
        :param algebraic_eqs: Residual equations associated with ``algebraic_vars``.
        :param inequalities: Inequality constraints enforced by the block.
        :param diff_vars: Explicit derivative variables associated with state variables.
        :param reformulated_vars: Auxiliary variables introduced by symbolic reformulation.
        :param differential_eqs: Legacy differential residual equations retained for compatible model loading.
        :param parameters: Static symbolic parameters and their constant values.
        :param init_values: Explicit initial values assigned to symbolic variables.
        :param init_eqs: Equations used to initialize algebraic and state variables.
        :param diff_init_eqs: Equations used to initialize state-variable derivatives.
        :param discrete_eqs: Discrete update equations keyed by their target variables.
        :param children: Nested blocks flattened with this block during compilation.
        :param in_vars: Variables consumed from outside the block.
        :param out_vars: Internal variables exposed to other blocks.
        :param event_dict: Runtime-changeable parameters and their current expressions.
        :param mode_dict: Discrete mode variables and their current expressions.
        :param boolean_guards: Boolean guard variables and the comparisons that drive them.
        :param procedural_logic: Runtime procedural-logic objects attached to the block.
        :param connection_intents: Semantic dynamic connections retained across interface reconstruction.
        :param external_mapping: Variables initialized from power-flow result references.
        :param api_obj_mapping: Device-property sources for parameter initial values. A resolved mapping overrides
            the local declaration during initialization without changing whether ``parameters`` or ``event_dict``
            owns the target's runtime role.
        :param is_decomposable: Whether the editor and compiler may expose the block's internal structure.
        :param name: Human-readable block name.
        :param uid: Stable block identifier, or ``None`` to allocate a new identifier.
        :param model_family_name: Optional user-facing family shared by structurally equivalent root models.
        """

        self.name: str = name
        # This semantic label identifies a complete model family without
        # changing the names of the root block or any of its children. Empty
        # values preserve the automatically generated comparator labels.
        self.model_family_name = model_family_name

        self.uid: int = _new_uid() if uid is None else uid

        self.is_decomposable = is_decomposable
        self.tpe_uid: int | None = None
        self.vars_glob_name2uid: Dict[str, int] = dict()

        self.state_vars: List[Var] = list() if state_vars is None else state_vars
        self.state_eqs: List[Expr] = list() if state_eqs is None else state_eqs

        self.algebraic_vars: List[Var] = list() if algebraic_vars is None else algebraic_vars
        self.algebraic_eqs: List[Expr | Comparison] = list() if algebraic_eqs is None else algebraic_eqs
        self.inequalities: List[Expr | Comparison] = list() if inequalities is None else inequalities

        self.diff_vars: List[Var] = list() if diff_vars is None else diff_vars
        self.reformulated_vars: List[Var] = list() if reformulated_vars is None else reformulated_vars
        self.differential_eqs: List[Expr] = list() if differential_eqs is None else differential_eqs

        # initialization
        self.init_eqs: Dict[Var, Expr] = dict() if init_eqs is None else init_eqs
        self.diff_init_eqs: Dict[Var, Expr] = dict() if diff_init_eqs is None else diff_init_eqs

        # vars to make this recursive
        self.children: List["Block"] = list() if children is None else children

        self.in_vars: List[Var] = list() if in_vars is None else in_vars
        self.out_vars: List[Var] = list() if out_vars is None else out_vars

        self.parameters: Dict[Var, Const] = dict() if parameters is None else parameters

        self.discrete_eqs: Dict[Var, Expr] = dict() if discrete_eqs is None else discrete_eqs
        self.post_init_seed_eqs: Dict[Var, Expr | Const] = (dict()
                                                            if post_init_seed_eqs is None
                                                            else post_init_seed_eqs)

        self.external_mapping: Dict[VarPowerFlowReferenceType, Var | None] = (dict()
                                                                              if external_mapping is None
                                                                              else external_mapping)

        self.api_obj_mapping: Dict[ParamPowerFlowReferenceType, Var | None] = (dict()
                                                                               if api_obj_mapping is None
                                                                               else api_obj_mapping)
        # initialization
        self.init_values: Dict[Var, Const] = dict() if init_values is None else init_values

        self.var_mapping = {v.name: v for v in self.algebraic_vars}

        # Dictionary of Variables and their Expressions that appear due to an event
        # this is the dictionary of "parameters" that may change and their equations
        self.event_dict: Dict[Var, Expr] = dict() if event_dict is None else event_dict
        self.mode_dict: Dict[Var, Expr | Const] = dict() if mode_dict is None else mode_dict
        self.boolean_guards: Dict[Var, Expr | Comparison] = dict() if boolean_guards is None else boolean_guards
        self.procedural_logic: List["ProceduralLogicBase"] = (list()
                                                              if procedural_logic is None
                                                              else list(procedural_logic)
        )
        # Root-interface intents are current semantic connection states. They
        # are independent of the graphical wires that happen to be visible
        # under the current network topology.
        self.connection_intents: List[DynamicConnectionIntent] = (list()
                                                                  if connection_intents is None
                                                                  else connection_intents)

        # Runtime identity belongs to the canonical block and stores only
        # scalar flags or UIDs into this block's symbolic variables.
        self.dynamic_model_contract: DynamicModelContract = DynamicModelContract()

        # TODO: What is this J-marti stuff doing here?,
        #  are we going to particularize this stuff in the block? sounds bad
        self._jmarti_fit_bundle: JMartiFitBundle | None = None
        self._jmarti_runtime_data: JMartiRuntimeData | None = None

        self._diagram: BlockDiagram = BlockDiagram()

        # Enforce one initialization owner as soon as a complete block is
        # created. Boundary normalization remains necessary for legacy objects
        # whose dictionaries are assigned after construction or deserialized.
        normalize_event_parameter_initialization(block=self)

    @property
    def diagram(self) -> BlockDiagram:
        """

        :return:
        """
        return self._diagram

    @diagram.setter
    def diagram(self, val: BlockDiagram | Dict[str, Any]):

        if isinstance(val, BlockDiagram):
            self._diagram = val
        elif isinstance(val, dict):
            diagram = BlockDiagram()

            self._diagram = diagram
        else:
            raise ValueError(f"Cannot set diagram with {val}")

    def set_name(self, name: str) -> None:
        """
        Change the block name without changing the block identity.

        :param name: New block name.
        :return: None.
        """
        # Only the display and serialization name changes here. The block
        # identity remains tied to the existing uid.
        self.name = name

    @property
    def model_family_name(self) -> str:
        """Return the optional user-defined structural model-family label.

        :return: Persisted family label or an empty string for legacy blocks.
        """
        try:
            return self._model_family_name
        except AttributeError:
            return ""

    @model_family_name.setter
    def model_family_name(self, name: str) -> None:
        """Store one model-family label without changing the block name.

        :param name: Family label, with an empty string selecting automatic naming.
        :return: None.
        """
        self._model_family_name = name

    @property
    def modal_template_kind(self) -> str | None:
        """Return the optional generated-template kind.

        :return: Template kind or ``None`` when no modal metadata is attached.
        """
        return self.dynamic_model_contract.modal_template_kind

    @modal_template_kind.setter
    def modal_template_kind(self, kind: str | None) -> None:
        """Store the optional generated-template kind.

        :param kind: Template kind, or ``None`` to clear it.
        :return: None.
        """
        self.dynamic_model_contract.modal_template_kind = kind

    @property
    def modal_template_config(self) -> Dict[str, str | int | float | bool | None] | None:
        """Return optional generated-template configuration.

        :return: Template configuration or ``None`` when it is not attached.
        """
        return self.dynamic_model_contract.modal_template_config

    @modal_template_config.setter
    def modal_template_config(self, config: Dict[str, str | int | float | bool | None] | None) -> None:
        """Store optional generated-template configuration.

        :param config: Template configuration, or ``None`` to clear it.
        :return: None.
        """
        if config is None:
            stored_config: Dict[str, str | int | float | bool | None] | None = None
        else:
            stored_config = dict(config)
        self.dynamic_model_contract.modal_template_config = stored_config

    @property
    def jmarti_fit_bundle(self) -> JMartiFitBundle | None:
        """Return the optional JMARTI fit bundle attached to this block.

        :return: Attached fit bundle or ``None``.
        """
        return self._jmarti_fit_bundle

    @jmarti_fit_bundle.setter
    def jmarti_fit_bundle(self, fit_bundle: JMartiFitBundle | None) -> None:
        """Store the optional JMARTI fit bundle.

        :param fit_bundle: Fit bundle, or ``None`` to clear it.
        :return: None.
        """
        self._jmarti_fit_bundle = fit_bundle

    @property
    def jmarti_runtime_data(self) -> JMartiRuntimeData | None:
        """Return optional JMARTI runtime data attached to this block.

        :return: Attached runtime data or ``None``.
        """
        return self._jmarti_runtime_data

    @jmarti_runtime_data.setter
    def jmarti_runtime_data(self, runtime_data: JMartiRuntimeData | None) -> None:
        """Store optional JMARTI runtime data.

        :param runtime_data: Runtime data, or ``None`` to clear it.
        :return: None.
        """
        self._jmarti_runtime_data = runtime_data

    def to_dict(self) -> Dict[str, Any]:
        """
        Get dictionary representation of this block
        :return: Dictionary
        """
        # Canonical persistence excludes historical intents whose internal
        # block or port has already been removed from this block hierarchy.
        normalize_dynamic_connection_intents(block=self)

        # Persistence is the stable boundary where a fully built in-memory
        # model must become one coherent declarative contract.
        return {
            "name": self.name,
            "model_family_name": self.model_family_name,
            "uid": self.uid,

            "state_vars": [_expr_to_dict(v) for v in self.state_vars],
            "algebraic_vars": [_expr_to_dict(v) for v in self.algebraic_vars],
            "diff_vars": [_expr_to_dict(v) for v in self.diff_vars],
            "reformulated_vars": [_expr_to_dict(v) for v in self.reformulated_vars],

            "in_vars": [_expr_to_dict(v) for v in self.in_vars],
            "out_vars": [_expr_to_dict(v) for v in self.out_vars],

            "state_eqs": [_expr_to_dict(e) for e in self.state_eqs],
            "algebraic_eqs": [_expr_to_dict(e) for e in self.algebraic_eqs],
            "inequalities": [_expr_to_dict(e) for e in self.inequalities],
            "differential_eqs": [_expr_to_dict(e) for e in self.differential_eqs],

            "init_eqs": {
                k.uid: {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.init_eqs.items()
            },

            "diff_init_eqs": {
                k.uid: {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.diff_init_eqs.items()
            },

            "event_dict": {
                k.uid: {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.event_dict.items()
            },

            "mode_dict": {
                k.uid: {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.mode_dict.items()
            },

            "boolean_guards": {
                k.uid: {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.boolean_guards.items()
            },

            "procedural_logic": self.serialize_procedural_logic_entries(),
            "connection_intents": [dynamic_connection_intent_to_dict(intent) for intent in self.connection_intents],
            "dynamic_model_contract": self.dynamic_model_contract.to_data(),

            "parameters": {
                k.uid: {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.parameters.items()
            },

            "init_values": {
                k.uid: {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.init_values.items()
            },

            "external_mapping": {
                k.value: _expr_to_dict(v) if v is not None else None
                for k, v in self.external_mapping.items()
            },

            "api_obj_mapping": {
                k.value: _expr_to_dict(v) if v is not None else None
                for k, v in self.api_obj_mapping.items()
            },

            "discrete_eqs": {
                k.uid: {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.discrete_eqs.items()
            },

            "post_init_seed_eqs": {
                k.uid: {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.post_init_seed_eqs.items()
            },

            "children": [child.to_dict() for child in self.children],

            "diagram": self.diagram.to_dict(),
        }

    def copy(self) -> "Block":
        """
        Deep-copy this block while preserving symbolic UIDs.

        :return: Copied block.
        """
        return copy.deepcopy(self)

    def serialize_procedural_logic_entries(self) -> List[ProceduralLogicData]:
        """
        Serialize block-attached procedural logic.

        :return: Serialized procedural logic entries.
        """
        return list(entry.to_data() for entry in self.procedural_logic)

    @staticmethod
    def reconstruct_procedural_logic_entries(
            data: List[ProceduralLogicData],
            procedural_logic_codec: "ProceduralLogicCodec" | None,
    ) -> List["ProceduralLogicBase"]:
        """
        Reconstruct typed block-attached procedural logic.

        :param data: Persisted declarative logic-entry collection.
        :param procedural_logic_codec: Explicit codec that reconstructs the
            validated declarative entries.
        :return: Reconstructed procedural logic entries in persisted order.
        """
        if len(data) == 0:
            return list()
        else:
            pass

        if procedural_logic_codec is None:
            raise ValueError(
                "Procedural logic data requires an explicit reconstruction codec"
            )
        else:
            pass

        return list(procedural_logic_codec.parse_entries(data))

    def __deepcopy__(self, memo: Dict[int, Any]) -> "Block":
        """
        Copy the block preserving shared symbolic references inside the block graph.

        :param memo: Standard deepcopy memo table.
        :return: Copied block.
        """
        if id(self) in memo:
            return memo[id(self)]
        else:
            result: Block = Block.__new__(Block)
            memo[id(self)] = result

            result.name = copy.deepcopy(self.name, memo)
            result.model_family_name = copy.deepcopy(self.model_family_name, memo)
            result.uid = copy.deepcopy(self.uid, memo)
            result.is_decomposable = copy.deepcopy(self.is_decomposable, memo)
            result.tpe_uid = copy.deepcopy(self.tpe_uid, memo)
            result.vars_glob_name2uid = copy.deepcopy(self.vars_glob_name2uid, memo)
            result.state_vars = copy.deepcopy(self.state_vars, memo)
            result.state_eqs = copy.deepcopy(self.state_eqs, memo)
            result.algebraic_vars = copy.deepcopy(self.algebraic_vars, memo)
            result.algebraic_eqs = copy.deepcopy(self.algebraic_eqs, memo)
            result.inequalities = copy.deepcopy(self.inequalities, memo)
            result.diff_vars = copy.deepcopy(self.diff_vars, memo)
            result.reformulated_vars = copy.deepcopy(self.reformulated_vars, memo)
            result.differential_eqs = copy.deepcopy(self.differential_eqs, memo)
            result.init_eqs = copy.deepcopy(self.init_eqs, memo)
            result.diff_init_eqs = copy.deepcopy(self.diff_init_eqs, memo)
            result.children = copy.deepcopy(self.children, memo)
            result.in_vars = copy.deepcopy(self.in_vars, memo)
            result.out_vars = copy.deepcopy(self.out_vars, memo)
            result.parameters = copy.deepcopy(self.parameters, memo)
            result.discrete_eqs = copy.deepcopy(self.discrete_eqs, memo)
            result.post_init_seed_eqs = copy.deepcopy(self.post_init_seed_eqs, memo)
            result.external_mapping = copy.deepcopy(self.external_mapping, memo)
            result.api_obj_mapping = copy.deepcopy(self.api_obj_mapping, memo)
            result.init_values = copy.deepcopy(self.init_values, memo)
            result.var_mapping = copy.deepcopy(self.var_mapping, memo)
            result.event_dict = copy.deepcopy(self.event_dict, memo)
            result.mode_dict = copy.deepcopy(self.mode_dict, memo)
            result.boolean_guards = copy.deepcopy(self.boolean_guards, memo)
            result.procedural_logic = copy.deepcopy(self.procedural_logic, memo)
            result.connection_intents = copy.deepcopy(self.connection_intents, memo)
            result.dynamic_model_contract = copy.deepcopy(self.dynamic_model_contract, memo)
            result._jmarti_fit_bundle = copy.deepcopy(self._jmarti_fit_bundle, memo)
            result._jmarti_runtime_data = None
            result._diagram = copy.deepcopy(self._diagram, memo)

            return result

    def compare(self, block2: Block) -> bool:
        """
        Compare two blocks.
        :param block2:
        :return:
        """
        dict1 = self.to_dict()
        dict2 = block2.to_dict()
        return dict1 == dict2

    def get_all_equations_list(self):
        equations_list: List[Expr] = list()
        equations_list.extend(self.state_eqs)
        equations_list.extend(self.algebraic_eqs)
        equations_list.extend(self.differential_eqs)
        return equations_list

    def __eq__(self, other: Block) -> bool:
        x = self.compare(other)
        return x

    def set_parameter_in_model(self, var_name: str, new_value: float) -> None:
        """Update every matching parameter in this block hierarchy.

        Dynamic parameters can be stored as event values, mode values, or
        ordinary model parameters. The update therefore visits every canonical
        parameter store in the current block before descending into its child
        blocks.

        :param var_name: Symbolic parameter name to update.
        :param new_value: Numeric value assigned to every matching parameter.
        :return: None.
        """
        event_var: Var
        event_expr: Expr
        for event_var, event_expr in self.event_dict.items():
            # Preserve the canonical expression object when it is already a constant.
            if event_var.name == var_name:
                if isinstance(event_expr, Const):
                    event_expr.value = new_value
                else:
                    self.event_dict[event_var] = Const(new_value)
            else:
                pass

        mode_var: Var
        mode_expr: Expr
        for mode_var, mode_expr in self.mode_dict.items():
            # Mode parameters follow the same replacement contract as event parameters.
            if mode_var.name == var_name:
                if isinstance(mode_expr, Const):
                    mode_expr.value = new_value
                else:
                    self.mode_dict[mode_var] = Const(new_value)
            else:
                pass

        parameter_var: Var
        parameter_expr: Const
        for parameter_var, parameter_expr in self.parameters.items():
            # Ordinary parameters are the final local store checked by the setter.
            if parameter_var.name == var_name:
                if isinstance(parameter_expr, Const):
                    parameter_expr.value = new_value
                else:
                    self.parameters[parameter_var] = Const(new_value)
            else:
                pass

        child_block: Block
        for child_block in self.children:
            # Apply the same semantic update to every nested model instance.
            child_block.set_parameter_in_model(var_name, new_value)

    def check_empty(self) -> bool:
        """
        check if a block is an empty block
        :return:
        :rtype: bool
        """
        return (
                not self.state_vars and
                not self.state_eqs and
                not self.algebraic_vars and
                not self.algebraic_eqs and
                not self.inequalities and
                not self.diff_vars and
                not self.reformulated_vars and
                not self.differential_eqs and
                not self.parameters and
                not self.init_values and
                not self.init_eqs and
                not self.diff_init_eqs and
                not self.post_init_seed_eqs and
                not self.children and
                not self.in_vars and
                not self.out_vars and
                not self.event_dict and
                not self.mode_dict and
                not self.boolean_guards and
                not self.procedural_logic and
                not self.external_mapping and
                not self.api_obj_mapping
        )

    def empty(self) -> bool:
        """
        check if a model is empty
        :return:
        """
        if not self.children:
            empty = self.check_empty()
            if empty:
                return empty
        else:
            empty = self.check_empty()
            if not empty:
                return empty

            for child in self.children:
                child.empty()

        return False

    def E(self, d: VarPowerFlowReferenceType) -> Var | None:
        """

        returns the value of the external mapping corresponding to the VarPowerFlowReferenceType

        :param d:
        :return:
        """
        return self.external_mapping[d]

    def V(self, d: str) -> Var:
        """

        :param d:
        :return:
        """
        return self.var_mapping[d]

    def add(self, val: Block):
        """
        Add another block to children of the model
        :param val: Block
        """
        self.children.append(val)

    def remove(self, val: Block):
        """
        Remove a block from block children
        :param val: Block
        """
        self.children.remove(val)

    def check_valid_init_method(self):

        explicit = True
        for lst in [self.state_vars, self.algebraic_vars]:
            for var in lst:
                if self.init_eqs[var] is None:
                    explicit = False
                # if self.init_values[var] is None:
                #     self.init_values[var] = Const(0)
        return explicit

    def get_all_blocks(self) -> List[Block]:
        """
        Depth-first collection of all *primitive* Blocks.
        """

        flat: List[Block] = [self]
        for el in self.children:
            flat.extend(el.get_all_blocks())

        return flat

    def get_static_mapping_keys_for_parameter(self,
                                              parameter: Var) -> List[ParamPowerFlowReferenceType]:
        """Find declared static mappings targeting a parameter across this model.

        Mapping targets may be absent; those entries are ignored. Matching uses
        the current symbolic ``uid``. Repeated matching keys are retained across
        the existing depth-first block traversal.

        :param parameter: Symbolic parameter whose source mappings are requested.
        :return: Matching mapping keys in existing depth-first model order.
        """
        mapping_keys: List[ParamPowerFlowReferenceType] = list()
        candidate_block: Block
        mapping_key: ParamPowerFlowReferenceType
        mapping_target: Var | None
        for candidate_block in self.get_all_blocks():
            for mapping_key, mapping_target in candidate_block.api_obj_mapping.items():
                if isinstance(mapping_target, Var) and mapping_target.uid == parameter.uid:
                    mapping_keys.append(mapping_key)
                else:
                    pass
        return mapping_keys

    def merge_incoming_block(self, block: Block):
        block.unify_blocks()
        self.algebraic_vars.extend(block.algebraic_vars)
        self.algebraic_eqs.extend(block.algebraic_eqs)
        self.inequalities.extend(block.inequalities)
        self.state_vars.extend(block.state_vars)
        self.state_eqs.extend(block.state_eqs)
        self.diff_vars.extend(block.diff_vars)
        self.reformulated_vars.extend(block.reformulated_vars)
        self.external_mapping.update(block.external_mapping)
        for event_param, eq in block.event_dict.items():
            self.event_dict[event_param] = eq

        for mode_param, eq in block.mode_dict.items():
            self.mode_dict[mode_param] = eq

        for bool_var, guard in block.boolean_guards.items():
            self.boolean_guards[bool_var] = guard

        for param, const in block.parameters.items():
            self.parameters[param] = const

        for var, init_eq in block.init_eqs.items():
            self.init_eqs[var] = init_eq

        for diffvar, diff_init_eq in block.diff_init_eqs.items():
            self.diff_init_eqs[diffvar] = diff_init_eq

        for seed_var, seed_expression in block.post_init_seed_eqs.items():
            self.post_init_seed_eqs[seed_var] = seed_expression

    def unify_blocks(self):
        """
        This function collects all variables and equations of a block, returns a flat block
        Returns
        -------
        Union[None, VeraGridEngine.Utils.Symbolic.block.Block]
        """
        mdl_placeholder = Block()
        for b in self.get_all_blocks():
            mdl_placeholder.algebraic_vars.extend(b.algebraic_vars)
            mdl_placeholder.algebraic_eqs.extend(b.algebraic_eqs)
            mdl_placeholder.inequalities.extend(b.inequalities)
            mdl_placeholder.state_vars.extend(b.state_vars)
            mdl_placeholder.state_eqs.extend(b.state_eqs)
            mdl_placeholder.diff_vars.extend(b.diff_vars)
            mdl_placeholder.differential_eqs.extend(b.differential_eqs)
            mdl_placeholder.reformulated_vars.extend(b.reformulated_vars)
            mdl_placeholder.external_mapping.update(b.external_mapping)
            mdl_placeholder.api_obj_mapping.update(b.api_obj_mapping)
            for event_param, eq in b.event_dict.items():
                mdl_placeholder.event_dict[event_param] = eq

            for mode_param, eq in b.mode_dict.items():
                mdl_placeholder.mode_dict[mode_param] = eq

            for bool_var, guard in b.boolean_guards.items():
                mdl_placeholder.boolean_guards[bool_var] = guard

            for param, const in b.parameters.items():
                mdl_placeholder.parameters[param] = const

            for var, init_eq in b.init_eqs.items():
                mdl_placeholder.init_eqs[var] = init_eq

            for var, init_val in b.init_values.items():
                mdl_placeholder.init_values[var] = init_val

            for diffvar, diff_init_eq in b.diff_init_eqs.items():
                mdl_placeholder.diff_init_eqs[diffvar] = diff_init_eq

            for seed_var, seed_expression in b.post_init_seed_eqs.items():
                mdl_placeholder.post_init_seed_eqs[seed_var] = seed_expression

            mdl_placeholder.procedural_logic.extend(b.procedural_logic)

        self.algebraic_vars = mdl_placeholder.algebraic_vars
        self.algebraic_eqs = mdl_placeholder.algebraic_eqs
        self.inequalities = mdl_placeholder.inequalities
        self.state_vars = mdl_placeholder.state_vars
        self.state_eqs = mdl_placeholder.state_eqs
        self.diff_vars = mdl_placeholder.diff_vars
        self.differential_eqs = mdl_placeholder.differential_eqs
        self.event_dict = mdl_placeholder.event_dict
        self.mode_dict = mdl_placeholder.mode_dict
        self.boolean_guards = mdl_placeholder.boolean_guards
        self.parameters = mdl_placeholder.parameters
        self.init_eqs = mdl_placeholder.init_eqs
        self.diff_init_eqs = mdl_placeholder.diff_init_eqs
        self.post_init_seed_eqs = mdl_placeholder.post_init_seed_eqs
        self.reformulated_vars = mdl_placeholder.reformulated_vars
        self.external_mapping = mdl_placeholder.external_mapping
        self.api_obj_mapping = mdl_placeholder.api_obj_mapping
        self.procedural_logic = mdl_placeholder.procedural_logic
        self.children = list()

    def get_vars(self) -> List[Var]:
        """
        returns variables of the flat block
        :return: List[Var]
        """
        vars_list = list()
        variables_lists = [self.algebraic_vars, self.state_vars, self.diff_vars]
        for lst in variables_lists:
            for var in lst:
                vars_list.append(var)

        return vars_list

    def get_all_vars(self):
        """
        returns all the variables of a block
        :return:
        """
        variables: List[Var] = list()
        all_blocks = self.get_all_blocks()
        for blk in all_blocks:
            variables.extend(blk.algebraic_vars)
            variables.extend(blk.state_vars)
            variables.extend(blk.diff_vars)
        return variables

    def update_variables(self, old: Var | Expr, new: Var | Expr) -> None:
        """
        this function changes the variable old for the variable new in the block variables
        :param old:
        :type old:
        :param new:
        :type new:
        :return:
        :rtype:
        """

        # Ports and solved-variable collections form one symbolic interface.
        # Replacing only the solved owner leaves inputs/outputs pointing to a
        # stale UID even though equations already consume the replacement.
        for lst in [
            self.in_vars,
            self.out_vars,
            self.state_vars,
            self.algebraic_vars,
            self.diff_vars,
        ]:
            for i, var in enumerate(lst):
                if var.uid == old.uid:
                    lst[i] = new
                else:
                    pass

        if isinstance(new, Var):
            mapped_name: str
            mapped_var: Var
            for mapped_name, mapped_var in self.var_mapping.items():
                if mapped_var.uid == old.uid:
                    self.var_mapping[mapped_name] = new
                else:
                    pass
        else:
            pass

    def update_equations(self, old: Var | Expr, new: Var | Expr) -> None:
        """
        this function changes the variable old for the variable new in the block equations
        :param old:
        :param new:
        :return:
        """
        init_eqs_new = dict()
        diff_init_eqs_new = dict()
        post_init_seed_eqs_new: Dict[Var, Expr | Const] = dict()
        event_dict_new = dict()
        mode_dict_new = dict()
        boolean_guards_new = dict()

        for i, eq in enumerate(self.algebraic_eqs):
            new_equ = eq.subs({old: new})
            self.algebraic_eqs[i] = new_equ
        for i, eq in enumerate(self.inequalities):
            new_equ = eq.subs({old: new})
            self.inequalities[i] = new_equ
        for i, eq in enumerate(self.state_eqs):
            new_equ = eq.subs({old: new})
            self.state_eqs[i] = new_equ
        for i, eq in enumerate(self.differential_eqs):
            new_equ = eq.subs({old: new})
            self.differential_eqs[i] = new_equ
        for var, expr in self.init_eqs.items():
            new_expr = expr.subs({old: new})
            if var is old:
                init_eqs_new.update({new: new_expr})
            else:
                init_eqs_new.update({var: new_expr})

        self.init_eqs = init_eqs_new

        for var, expr in self.diff_init_eqs.items():
            new_expr = expr.subs({old: new})
            if var is old:
                diff_init_eqs_new.update({new: new_expr})
            else:
                diff_init_eqs_new.update({var: new_expr})

        self.diff_init_eqs = diff_init_eqs_new

        for var, expr in self.post_init_seed_eqs.items():
            new_expr: Expr = expr.subs({old: new})
            if var is old and isinstance(new, Var):
                post_init_seed_eqs_new[new] = new_expr
            else:
                post_init_seed_eqs_new[var] = new_expr
        self.post_init_seed_eqs = post_init_seed_eqs_new

        for var, expr in self.event_dict.items():
            new_expr = expr.subs({old: new})
            if var is old:
                event_dict_new.update({new: new_expr})
            else:
                event_dict_new.update({var: new_expr})

        self.event_dict = event_dict_new

        for var, expr in self.mode_dict.items():
            new_expr = expr.subs({old: new})
            if var is old:
                mode_dict_new.update({new: new_expr})
            else:
                mode_dict_new.update({var: new_expr})
        self.mode_dict = mode_dict_new

        for var, expr in self.boolean_guards.items():
            new_expr = expr.subs({old: new})
            if var is old:
                boolean_guards_new.update({new: new_expr})
            else:
                boolean_guards_new.update({var: new_expr})
        self.boolean_guards = boolean_guards_new

        for var_pf_ref, mdl_var in self.external_mapping.items():
            if mdl_var is old:
                if isinstance(new, Var):
                    self.external_mapping[var_pf_ref] = new
                else:
                    self.external_mapping[var_pf_ref] = None
            else:
                pass

        if self.procedural_logic:
            procedural_var_mapping: Dict[Expr | str, Expr] = dict((
                (old, new),
                (old.name, new),
            ))
            self.procedural_logic = list(
                entry.remap(procedural_var_mapping)
                for entry in self.procedural_logic
            )

    def update_model(self, old: Var | Expr, new: Var | Expr) -> None:
        """
        Replace variables
        :param old:
        :param new:
        :return:
        """
        self.update_equations(old, new)
        self.update_variables(old, new)
        if self.children:
            for child in self.children:
                child.update_model(old, new)

    def update_variables_bulk(self, var_mapping: Dict[Var, Var]) -> None:
        """
        Replace several variables in the block variable lists in one pass.

        :param var_mapping: Old-to-new variable mapping.
        :return: None.
        """
        uid_mapping: Dict[int, Var] = dict((old_var.uid, new_var) for old_var, new_var in var_mapping.items())
        lst: List[Var]
        i: int
        var: Var

        for lst in [
            self.in_vars,
            self.out_vars,
            self.state_vars,
            self.algebraic_vars,
            self.diff_vars,
        ]:
            for i, var in enumerate(lst):
                if var.uid in uid_mapping:
                    lst[i] = uid_mapping[var.uid]
                else:
                    pass

        mapped_name: str
        mapped_var: Var
        mapped_replacement: Var | None
        for mapped_name, mapped_var in self.var_mapping.items():
            mapped_replacement = uid_mapping.get(mapped_var.uid, None)
            if mapped_replacement is None:
                pass
            else:
                self.var_mapping[mapped_name] = mapped_replacement

    def update_equations_bulk(self, var_mapping: Dict[Var, Var]) -> None:
        """
        Replace several variables in block equations and mappings in one pass.

        :param var_mapping: Old-to-new variable mapping.
        :return: None.
        """
        uid_mapping: Dict[int, Var] = dict((old_var.uid, new_var) for old_var, new_var in var_mapping.items())
        init_eqs_new: Dict[Var, Expr] = dict()
        diff_init_eqs_new: Dict[Var, Expr] = dict()
        post_init_seed_eqs_new: Dict[Var, Expr | Const] = dict()
        event_dict_new: Dict[Var, Expr] = dict()
        mode_dict_new: Dict[Var, Expr] = dict()
        boolean_guards_new: Dict[Var, Expr | Comparison] = dict()
        external_mapping_new: Dict[VarPowerFlowReferenceType, Var | None] = dict()
        procedural_var_mapping: Dict[Expr | str, Expr] = dict()
        i: int
        eq: Expr | Comparison
        var: Var
        expr: Expr
        new_var: Var | None
        var_pf_ref: VarPowerFlowReferenceType
        mdl_var: Var | None

        for old_var, replacement_var in var_mapping.items():
            procedural_var_mapping[old_var] = replacement_var
            procedural_var_mapping[old_var.name] = replacement_var

        for i, eq in enumerate(self.algebraic_eqs):
            self.algebraic_eqs[i] = eq.subs(var_mapping)

        for i, eq in enumerate(self.inequalities):
            self.inequalities[i] = eq.subs(var_mapping)

        for i, eq in enumerate(self.state_eqs):
            self.state_eqs[i] = eq.subs(var_mapping)

        for i, eq in enumerate(self.differential_eqs):
            self.differential_eqs[i] = eq.subs(var_mapping)

        for var, expr in self.init_eqs.items():
            new_var = uid_mapping.get(var.uid, None)
            init_eqs_new[var if new_var is None else new_var] = expr.subs(var_mapping)
        self.init_eqs = init_eqs_new

        for var, expr in self.diff_init_eqs.items():
            new_var = uid_mapping.get(var.uid, None)
            diff_init_eqs_new[var if new_var is None else new_var] = expr.subs(var_mapping)
        self.diff_init_eqs = diff_init_eqs_new

        for var, expr in self.post_init_seed_eqs.items():
            new_var = uid_mapping.get(var.uid, None)
            post_init_seed_eqs_new[
                var if new_var is None else new_var
            ] = expr.subs(var_mapping)
        self.post_init_seed_eqs = post_init_seed_eqs_new

        for var, expr in self.event_dict.items():
            new_var = uid_mapping.get(var.uid, None)
            event_dict_new[var if new_var is None else new_var] = expr.subs(var_mapping)
        self.event_dict = event_dict_new

        for var, expr in self.mode_dict.items():
            new_var = uid_mapping.get(var.uid, None)
            mode_dict_new[var if new_var is None else new_var] = expr.subs(var_mapping)
        self.mode_dict = mode_dict_new

        for var, expr in self.boolean_guards.items():
            new_var = uid_mapping.get(var.uid, None)
            boolean_guards_new[var if new_var is None else new_var] = expr.subs(var_mapping)
        self.boolean_guards = boolean_guards_new

        for var_pf_ref, mdl_var in self.external_mapping.items():
            if mdl_var is None:
                external_mapping_new[var_pf_ref] = None
            elif mdl_var.uid in uid_mapping:
                external_mapping_new[var_pf_ref] = uid_mapping[mdl_var.uid]
            else:
                external_mapping_new[var_pf_ref] = mdl_var
        self.external_mapping = external_mapping_new

        if self.procedural_logic:
            self.procedural_logic = list(
                entry.remap(procedural_var_mapping)
                for entry in self.procedural_logic
            )
        else:
            pass

    def update_model_bulk(self, var_mapping: Dict[Var, Var]) -> None:
        """
        Replace several variables across the block hierarchy in one pass.

        :param var_mapping: Old-to-new variable mapping.
        :return: None.
        """
        self.update_equations_bulk(var_mapping)
        self.update_variables_bulk(var_mapping)
        if self.children:
            for child in self.children:
                child.update_model_bulk(var_mapping)
        else:
            pass

    def connect(self, vars_to_subs: List[Var], incoming_vars: List[Var]):
        """
        Function to connect two blocks by variables sharing
        """
        # here we just change uid and name of the vars_to_subs
        pairs: List[Tuple[Var, Var]] = list(zip(vars_to_subs, incoming_vars))
        var_to_subs: Var
        incoming_var: Var

        for var_to_subs, incoming_var in pairs:
            self.update_model(var_to_subs, incoming_var)
            # var_to_subs.uid = incoming_var.uid
            # var_to_subs.name = incoming_var.name

    def find_var_in_equations(self, var: Var) -> bool:
        """
        find a var in the equations of a block
        :param var:
        :return:
        """

        equation: Expr
        equation_var: Var

        for equation in self.algebraic_eqs:
            if equation.contains_var(var):
                return True

        for equation in self.state_eqs:
            if equation.contains_var(var):
                return True

        for equation in self.differential_eqs:
            if equation.contains_var(var):
                return True

        for equation_var, equation in self.init_eqs.items():
            if equation_var.uid == var.uid or equation.contains_var(var):
                return True

        for equation_var, equation in self.diff_init_eqs.items():
            if equation_var.uid == var.uid or equation.contains_var(var):
                return True

        for equation_var, equation in self.post_init_seed_eqs.items():
            if equation_var.uid == var.uid or equation.contains_var(var):
                return True

        for equation_var, equation in self.event_dict.items():
            if equation_var.uid == var.uid or equation.contains_var(var):
                return True

        for equation_var, equation in self.mode_dict.items():
            if equation_var.uid == var.uid or equation.contains_var(var):
                return True

        for mdl_var in self.external_mapping.values():
            if mdl_var is not None and mdl_var.uid == var.uid:
                return True

        return False

        # add procedural logic here

    def find_var_in_block(self, var: Var) -> bool:
        """
        Replace variables
        :param var:
        :return:
        """
        if self.find_var_in_equations(var):
            return True
        if self.children:
            for child in self.children:
                if child.find_var_in_block(var):
                    return True

        return False

    def is_eq_decomposable(self) -> bool:

        if self.children:
            return False
        if not (bool(self.algebraic_eqs) or bool(self.state_eqs)):
            return False
        if not self.is_decomposable:
            return False
        return True


def find_connections(mdl1: Block, mdl2: Block) -> tuple[List[tuple[Var, Var]], List[tuple[Var, Var]]]:
    """
    find connections between the two blocks by vars searching
    :return:
    :rtype:
    """

    # connect inputs mdl2 with outputs mdl1
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if
        # outp.shared_ref == inpt.shared_ref and outp.shared_ref is not None and inpt.shared_ref is not None and outp.uid == inpt.uid
        outp.shared_ref == inpt.shared_ref and outp.shared_ref is not None and inpt.shared_ref is not None or outp.uid == inpt.uid
    ]

    power_flow_pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if
        # outp.ref == inpt.ref and outp.ref is not None and inpt.ref is not None and outp.uid == inpt.uid
        outp.ref == inpt.ref and outp.ref is not None and inpt.ref is not None or outp.uid == inpt.uid
    ]

    return pairs, power_flow_pairs


def find_connections_pf(mdl1: Block, mdl2: Block) -> List[tuple[Var, Var]]:
    """
    find connections between the two blocks by vars searching
    :return:
    :rtype:
    """

    power_flow_pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if
        outp.ref == inpt.ref and outp.ref is not None and inpt.ref is not None and outp.uid == inpt.uid
    ]

    return power_flow_pairs


def find_name_in_block(name: str, block: Block) -> Var | None:
    """

    :param name:
    :param block:
    :return:
    """
    for lst in [block.in_vars, block.out_vars, block.algebraic_vars, block.state_vars, block.diff_vars]:
        for var in lst:
            if name == var.name:
                return var

    for block_child in block.children:
        result = find_name_in_block(name, block_child)
        if result is not None:  # found in a child
            return result

    return None


def build_name_to_var_lookup(block: Block) -> Dict[str, Var]:
    """
    Build one variable lookup table by symbolic name for a block hierarchy.

    The first occurrence of each name is preserved, matching the effective
    search order of ``find_name_in_block()`` while avoiding repeated recursive
    scans when many variables must be resolved from the same block.

    :param block: Root block to inspect.
    :return: Name-to-variable lookup.
    """
    lookup: Dict[str, Var] = dict()
    var_lists: List[List[Var]] = list([
        block.in_vars,
        block.out_vars,
        block.algebraic_vars,
        block.state_vars,
        block.diff_vars,
    ])
    var_list: List[Var]
    var_obj: Var
    child_block: Block
    child_lookup: Dict[str, Var]

    for var_list in var_lists:
        for var_obj in var_list:
            if var_obj.name in lookup:
                pass
            else:
                lookup[var_obj.name] = var_obj

    for var_obj in block.event_dict.keys():
        if var_obj.name in lookup:
            pass
        else:
            lookup[var_obj.name] = var_obj

    for var_obj in block.mode_dict.keys():
        if var_obj.name in lookup:
            pass
        else:
            lookup[var_obj.name] = var_obj

    for var_obj in block.boolean_guards.keys():
        if var_obj.name in lookup:
            pass
        else:
            lookup[var_obj.name] = var_obj

    for child_block in block.children:
        child_lookup = build_name_to_var_lookup(child_block)
        for child_name, child_var in child_lookup.items():
            if child_name in lookup:
                pass
            else:
                lookup[child_name] = child_var

    return lookup


def _get_var_attribute_mapping(block: Block) -> Dict[int, str]:
    """Build a mapping from variable uid to attribute name for a block."""
    mapping = {}
    for var in block.state_vars:
        mapping[var.uid] = "state_vars"
    for var in block.algebraic_vars:
        mapping[var.uid] = "algebraic_vars"
    for var in block.diff_vars:
        mapping[var.uid] = "diff_vars"
    for var in block.reformulated_vars:
        mapping[var.uid] = "reformulated_vars"
    for var in block.parameters:
        mapping[var.uid] = "parameters"
    for var in block.event_dict:
        mapping[var.uid] = "event_dict"
    for var in block.in_vars:
        mapping[var.uid] = "in_vars"
    return mapping


def variables_in_corresponding_attributes(blocks: List[Block], variables_mappings: List[Dict[int, int]]) -> bool:
    """
    Check if corresponding variables are located in corresponding attributes of n blocks.

    For each pair (blocks[i], blocks[j]) with variables_mappings[k] (where k corresponds to the pair),
    and for every pair (uid1, uid2) in variables_mapping:
    - If the variable with uid1 is in blocks[i].state_vars, the variable with uid2 must be in blocks[j].state_vars
    - And so on for all attribute types

    The order of variables within each attribute does not matter.

    :param blocks: List of n blocks to check
    :param variables_mappings: List of Dict mappings from block i to block j for each pair comparison
    :return: True if all corresponding variables are in corresponding attributes for all pairs
    """
    if len(blocks) < 2:
        return True

    attr_maps = [_get_var_attribute_mapping(block) for block in blocks]

    for i in range(len(blocks)):
        for j in range(i + 1, len(blocks)):
            mapping_idx = sum(range(len(blocks) - 1, len(blocks) - 1 - (j - i), -1)) + (j - i - 1)
            if mapping_idx >= len(variables_mappings):
                continue
            variables_mapping = variables_mappings[mapping_idx]

            attr_map_i = attr_maps[i]
            attr_map_j = attr_maps[j]

            for uid_i, uid_j in variables_mapping.items():
                attr_i = attr_map_i.get(uid_i)
                attr_j = attr_map_j.get(uid_j)
                if attr_i != attr_j:
                    return False

    return True


def _get_pair_index(i: int, j: int, n: int) -> int:
    """Get the index in variables_mappings list for the pair (i, j)."""
    idx = 0
    for x in range(n):
        for y in range(x + 1, n):
            if x == i and y == j:
                return idx
            idx += 1
    return -1


class _BlockClassificationData:
    """Prepare a read-only flat model view once per classification invocation."""

    __slots__ = ("_equations", "_attributes", "_equation_key", "_alignment_data")

    def __init__(self, block: Block) -> None:
        """Collect the same equations and variable roles as copy/unify did.

        :param block: Original block hierarchy, which remains unmodified.
        :return: None.
        """
        # Only classification inputs are collected; expressions and logic are not copied.
        flat: Block = Block()
        child: Block
        for child in block.get_all_blocks():
            flat.state_vars.extend(child.state_vars)
            flat.state_eqs.extend(child.state_eqs)
            flat.algebraic_vars.extend(child.algebraic_vars)
            flat.algebraic_eqs.extend(child.algebraic_eqs)
            flat.diff_vars.extend(child.diff_vars)
            flat.differential_eqs.extend(child.differential_eqs)
            flat.reformulated_vars.extend(child.reformulated_vars)
            flat.parameters.update(child.parameters)
            flat.event_dict.update(child.event_dict)

        # unify_blocks retained the root inputs rather than collecting child inputs.
        flat.in_vars = block.in_vars
        self._equations: List[Expr] = flat.get_all_equations_list()
        self._attributes: Dict[int, str] = _get_var_attribute_mapping(flat)
        equation: Expr
        self._equation_key: Tuple[str, ...] = tuple(sorted(
            structural_hash(equation) for equation in self._equations
        ))
        self._alignment_data: VariableAlignmentData | None = None

    def get_equation_key(self) -> Tuple[str, ...]:
        """Expose the exact sorted-hash key used by equivalent_systems.

        :return: Immutable equation multiset key, retaining duplicate equations.
        """
        return self._equation_key

    def align_with(self, other: "_BlockClassificationData") -> Dict[int, int]:
        """Match same-key models while preserving the existing attribute checks.

        :param other: Candidate model prepared for the same classification run.
        :return: Accepted variable mapping, or an empty lookup on rejection.
        """
        # Signatures are only needed when an equation-compatible pair is encountered.
        if self._alignment_data is None:
            self._alignment_data = VariableAlignmentData(self._equations)
        else:
            pass
        if other._alignment_data is None:
            other._alignment_data = VariableAlignmentData(other._equations)
        else:
            pass
        alignment: Dict[int, int] = align_variables(
            self._equations, other._equations, self._alignment_data, other._alignment_data,
        )
        source_uid: int
        target_uid: int
        for source_uid, target_uid in alignment.items():
            if self._attributes.get(source_uid, None) != other._attributes.get(target_uid, None):
                return dict()
            else:
                pass
        return alignment


def _compare_n_blocks_structurally_by_class(blocks: List[Block]):
    """
    Compare n blocks structurally and group equivalent blocks by their uid.

    Two blocks are considered structurally equivalent if:
    1. Their unified equation systems are equivalent
    2. Variables can be aligned between them
    3. Corresponding variables are located in corresponding attributes

    :param blocks: List of n blocks to compare
    :param by_class: Keep variable alignments under their representative block UID.
        This is required when distinct groups share an external variable UID.
    :return: Tuple of:
        - Dict with new uid (uuid.uuid4().int) as keys and lists of equivalent block uids as values
        - Dict with variable uid as keys and lists of equivalent variable uids as values,
          or a dict of those mappings keyed by representative UID when by_class is true
    """
    if len(blocks) == 0:
        return {}, {}

    if len(blocks) == 1:
        return {blocks[0].uid: []}, {}

    n = len(blocks)
    equivalence_classes = []
    equivalence_alignments = []
    processed = [False] * n

    for i in range(n):
        if not processed[i]:
            current_group = [blocks[i].uid]
            processed[i] = True
            current_alignments = {}

            for j in range(i + 1, n):
                if not processed[j]:

                    block_i_copy = blocks[i].copy()
                    block_i_copy.unify_blocks()
                    block_j_copy = blocks[j].copy()
                    block_j_copy.unify_blocks()

                    block_i_eqs = block_i_copy.get_all_equations_list()
                    block_j_eqs = block_j_copy.get_all_equations_list()

                    if equivalent_systems(block_i_eqs, block_j_eqs):

                        variables_alignment = align_variables(block_i_eqs, block_j_eqs)
                        if variables_alignment:

                            variables_mappings = [variables_alignment]
                            if variables_in_corresponding_attributes([block_i_copy, block_j_copy], variables_mappings):
                                current_group.append(blocks[j].uid)
                                processed[j] = True
                                current_alignments[j] = variables_alignment

            equivalence_classes.append(current_group)
            equivalence_alignments.append((i, current_alignments))

    model_result = {}
    for eq_class in equivalence_classes:
        model_result[eq_class[0]] = eq_class[1:]

    var_result = {}
    var_result_by_class = {}
    for ref_idx, alignments in equivalence_alignments:
        if not alignments:
            continue
        first_alignment = next(iter(alignments.values()))
        class_vars = {}
        for ref_var_uid in first_alignment:
            equivalent_uids = []
            for alignment in alignments.values():
                equivalent_uids.append(alignment[ref_var_uid])
            var_result[ref_var_uid] = equivalent_uids
            class_vars[ref_var_uid] = equivalent_uids
        var_result_by_class[blocks[ref_idx].uid] = class_vars

    return model_result, var_result_by_class


def compare_n_blocks_structurally(blocks: List[Block], *, by_class: bool = False):
    """
    Classify models using read-only snapshots local to this invocation.

    Two blocks are considered structurally equivalent if:
    1. Their unified equation systems are equivalent
    2. Variables can be aligned between them
    3. Corresponding variables are located in corresponding attributes

    :param blocks: Ordered model roots; the first accepted root remains representative.
    :return: Representative block UIDs mapped to equivalent block UIDs, followed
        by representative variable UIDs mapped to equivalent variable UIDs.
    """
    if by_class:
        return _compare_n_blocks_structurally_by_class(blocks)

    model_result: Dict[int, List[int]] = dict()
    var_result: Dict[int, List[int]] = dict()
    var_result_by_class: Dict[int, Dict[int, List[int]]] = dict()
    count: int = len(blocks)
    if count < 2:
        if count == 1:
            model_result[blocks[0].uid] = list()
        else:
            pass
    else:
        # Bucket by the exact previous equivalence test before attempting alignments.
        block: Block
        prepared: List[_BlockClassificationData] = list(_BlockClassificationData(block) for block in blocks)
        buckets: Dict[Tuple[str, ...], List[int]] = dict()
        index: int
        candidate_index: int
        data: _BlockClassificationData
        for index, data in enumerate(prepared):
            bucket: List[int] | None = buckets.get(data.get_equation_key(), None)
            if bucket is None:
                buckets[data.get_equation_key()] = list((index,))
            else:
                bucket.append(index)

        processed: List[bool] = list((False,)) * count
        for index, data in enumerate(prepared):
            if not processed[index]:
                processed[index] = True
                equivalents: List[int] = list()
                alignments: List[Dict[int, int]] = list()
                candidates: List[int] | None = buckets.get(data.get_equation_key(), None)
                if candidates is not None:
                    for candidate_index in candidates:
                        if candidate_index > index and not processed[candidate_index]:
                            alignment: Dict[int, int] = data.align_with(prepared[candidate_index])
                            if alignment:
                                equivalents.append(blocks[candidate_index].uid)
                                alignments.append(alignment)
                                processed[candidate_index] = True
                            else:
                                pass
                        else:
                            pass
                else:
                    pass
                model_result[blocks[index].uid] = equivalents
                if alignments:
                    class_vars: Dict[int, List[int]] = dict()
                    source_uid: int
                    for source_uid in alignments[0]:
                        equivalents_for_var = list(alignment[source_uid] for alignment in alignments)
                        var_result[source_uid] = equivalents_for_var
                        class_vars[source_uid] = equivalents_for_var
                    var_result_by_class[blocks[index].uid] = class_vars
                else:
                    pass
            else:
                pass

    return model_result, var_result_by_class if by_class else var_result


#
# def compare_n_blocks_structurally(blocks: List[Block]) -> Dict[int, List[int]]:
#     """
#     Compare n blocks structurally and group equivalent blocks by their uid.
#
#     Two blocks are considered structurally equivalent if:
#     1. Their unified equation systems are equivalent
#     2. Variables can be aligned between them
#     3. Corresponding variables are located in corresponding attributes
#
#     :param blocks: List of n blocks to compare
#     :return: Dict with new uid (uuid.uuid4().int) as keys and lists of equivalent block uids as values
#     """
#     if len(blocks) == 0:
#         return {}
#
#     if len(blocks) == 1:
#         new_uid = _new_uid()
#         return {new_uid: [blocks[0].uid]}
#
#     n = len(blocks)
#     equivalence_classes = []
#     processed = [False] * n
#
#     for i in range(n):
#         if processed[i]:
#             continue
#
#         current_group = [blocks[i].uid]
#         processed[i] = True
#
#         for j in range(i + 1, n):
#             if processed[j]:
#                 continue
#
#             block_i_copy = blocks[i].copy()
#             block_i_copy.unify_blocks()
#             block_j_copy = blocks[j].copy()
#             block_j_copy.unify_blocks()
#
#             block_i_eqs = block_i_copy.get_all_equations_list()
#             block_j_eqs = block_j_copy.get_all_equations_list()
#
#             if not equivalent_systems(block_i_eqs, block_j_eqs):
#                 continue
#
#             variables_alignment = align_variables(block_i_eqs, block_j_eqs)
#             if not variables_alignment:
#                 continue
#
#             variables_mappings = [variables_alignment]
#             if not variables_in_corresponding_attributes([block_i_copy, block_j_copy], variables_mappings):
#                 continue
#
#             current_group.append(blocks[j].uid)
#             processed[j] = True
#
#         equivalence_classes.append(current_group)
#
#     result = {}
#     for eq_class in equivalence_classes:
#         new_uid = _new_uid()
#         result[new_uid] = eq_class
#
#     return result

def compare_blocks_structurally(block1: Block, block2: Block) -> bool:
    block1_compare = block1.copy().unify_blocks()
    block2_compare = block2.copy().unify_blocks()

    block1_eqs = block1.get_all_equations_list()
    block2_eqs = block2.get_all_equations_list()

    if equivalent_systems(block1_eqs, block2_eqs):
        variables_alignment = align_variables(block1_eqs, block2_eqs)
        if variables_in_corresponding_attributes([block1_compare, block2_compare], [variables_alignment]):
            print("blocks are equivalent")
            return True
    return False


def build_name_to_vars_lookup(block: Block) -> Dict[str, List[Var]]:
    """
    Build a UID-distinct variable lookup by symbolic name.

    A composite can expose the same PowerFactory port label on several direct
    instances. Callers that materialize one external signal, such as a native
    meter, must bind every matching boundary variable instead of silently
    selecting the first occurrence.

    :param block: Root block hierarchy to inspect.
    :return: Ordered variables grouped by their symbolic name.
    """
    lookup: Dict[str, List[Var]] = dict()
    seen_uids_by_name: Dict[str, set[int]] = dict()
    runtime_block: Block
    variable_groups: List[List[Var]]
    variable_group: List[Var]
    variable: Var
    expression_groups: List[Sequence[Expr]]
    expression_group: Sequence[Expr]
    expression: Expr
    algebraic_expressions: List[Expr]
    algebraic_expression: Expr | Comparison
    boolean_guard_expressions: List[Expr]
    boolean_guard: Expr | Comparison

    for runtime_block in block.get_all_blocks():
        variable_groups = list([
            runtime_block.in_vars,
            runtime_block.out_vars,
            runtime_block.algebraic_vars,
            runtime_block.state_vars,
            runtime_block.diff_vars,
            list(runtime_block.event_dict.keys()),
            list(runtime_block.mode_dict.keys()),
            list(runtime_block.boolean_guards.keys()),
        ])
        for variable_group in variable_groups:
            for variable in variable_group:
                seen_uids: set[int] | None = seen_uids_by_name.get(
                    variable.name,
                    None,
                )
                if seen_uids is None:
                    lookup[variable.name] = list([variable])
                    seen_uids_by_name[variable.name] = set([variable.uid])
                else:
                    if variable.uid in seen_uids:
                        pass
                    else:
                        lookup[variable.name].append(variable)
                        seen_uids.add(variable.uid)

        # Imported DSL initialization statements can reference a native slot
        # signal before that signal is promoted to a root interface. Include
        # those expression-only variables so the authoritative Sta*mea or
        # equipment adapter can bind them by the exported signal name.
        algebraic_expressions = list()
        boolean_guard_expressions = list()
        for algebraic_expression in runtime_block.algebraic_eqs:
            if isinstance(algebraic_expression, Comparison):
                algebraic_expressions.append(algebraic_expression.lhs)
                if isinstance(algebraic_expression.rhs, Expr):
                    algebraic_expressions.append(algebraic_expression.rhs)
                else:
                    pass
            else:
                algebraic_expressions.append(algebraic_expression)

        for boolean_guard in runtime_block.boolean_guards.values():
            if isinstance(boolean_guard, Comparison):
                boolean_guard_expressions.append(boolean_guard.lhs)
                if isinstance(boolean_guard.rhs, Expr):
                    boolean_guard_expressions.append(boolean_guard.rhs)
                else:
                    pass
            else:
                boolean_guard_expressions.append(boolean_guard)

        expression_groups = list([
            algebraic_expressions,
            runtime_block.state_eqs,
            runtime_block.differential_eqs,
            list(runtime_block.init_eqs.values()),
            list(runtime_block.diff_init_eqs.values()),
            list(runtime_block.event_dict.values()),
            list(runtime_block.mode_dict.values()),
            boolean_guard_expressions,
        ])
        for expression_group in expression_groups:
            for expression in expression_group:
                for variable in expression.get_vars():
                    seen_uids = seen_uids_by_name.get(variable.name, None)
                    if seen_uids is None:
                        lookup[variable.name] = list([variable])
                        seen_uids_by_name[variable.name] = {variable.uid}
                    else:
                        if variable.uid in seen_uids:
                            pass
                        else:
                            lookup[variable.name].append(variable)
                            seen_uids.add(variable.uid)

    return lookup


def flatten_block(block: Block) -> Block:
    """Create one flat block from a hierarchical block tree.

    The source block remains unchanged. Every primitive block is visited in
    depth-first order so declarations and equations retain the hierarchy's
    existing deterministic order while the returned block owns independent
    aggregate containers.

    :param block: Root block whose child hierarchy is to be flattened.
    :return: New block containing the declarations from the full hierarchy.
    """
    flat_block: Block = Block(name=block.name, uid=block.uid)
    flat_block.diagram = block.diagram.to_dict()
    known_input_uids: set[int] = set()
    known_output_uids: set[int] = set()

    for current_block in block.get_all_blocks():
        flat_block.state_vars.extend(current_block.state_vars)
        flat_block.state_eqs.extend(current_block.state_eqs)
        flat_block.algebraic_vars.extend(current_block.algebraic_vars)
        flat_block.algebraic_eqs.extend(current_block.algebraic_eqs)
        flat_block.inequalities.extend(current_block.inequalities)
        flat_block.diff_vars.extend(current_block.diff_vars)
        flat_block.reformulated_vars.extend(current_block.reformulated_vars)
        flat_block.differential_eqs.extend(current_block.differential_eqs)
        for variable in current_block.in_vars:
            if variable.uid not in known_input_uids:
                flat_block.in_vars.append(variable)
                known_input_uids.add(variable.uid)
        for variable in current_block.out_vars:
            if variable.uid not in known_output_uids:
                flat_block.out_vars.append(variable)
                known_output_uids.add(variable.uid)
        flat_block.parameters.update(current_block.parameters)
        flat_block.init_values.update(current_block.init_values)
        flat_block.init_eqs.update(current_block.init_eqs)
        flat_block.diff_init_eqs.update(current_block.diff_init_eqs)
        flat_block.discrete_eqs.update(current_block.discrete_eqs)
        flat_block.post_init_seed_eqs.update(current_block.post_init_seed_eqs)
        flat_block.event_dict.update(current_block.event_dict)
        flat_block.mode_dict.update(current_block.mode_dict)
        flat_block.boolean_guards.update(current_block.boolean_guards)
        flat_block.external_mapping.update(current_block.external_mapping)
        flat_block.api_obj_mapping.update(current_block.api_obj_mapping)
        flat_block.procedural_logic.extend(current_block.procedural_logic)

    flat_block.children = list()
    flat_block.var_mapping = {
        variable.name: variable
        for variable in flat_block.algebraic_vars + flat_block.state_vars + flat_block.diff_vars
    }
    return flat_block

