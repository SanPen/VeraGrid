from __future__ import annotations

import copy
import math
from typing import Dict, Iterable, List, Mapping, Sequence, Set, Tuple

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.IO.dgs.dgs_to_blocks import (
    DgsDirectRootBuildResult,
    DgsSlotSignalDirection,
    ElmCompInstanceEntry,
)
from VeraGridEngine.IO.dgs.dynamic_models.dgs_elmsym_runtime_adapter import (
    install_unconnected_dgs_control_input_defaults,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, Comparison, Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import (
    DeviceType,
    ParamPowerFlowReferenceType,
    VarPowerFlowReferenceType,
)




def _remove_child_post_init_seed_targets(
        block: Block,
        target_vars: Sequence[Var],
) -> None:
    """Remove child-owned late seeds for adapter-owned boundary variables.

    The physical ``ElmGenstat`` wrapper is the sole startup owner of its
    current commands. Imported graphical equations remain active at runtime,
    while their generic late seeds must not overwrite the current references
    reconstructed from the solved load-flow operating point.

    :param block: Imported controller root whose children are inspected.
    :param target_vars: Exact physical command variables owned by the adapter.
    :return: None.
    """
    target_uids: Set[int] = set()
    target_var: Var
    candidate_block: Block
    seed_var: Var
    seed_expression: Expr | Const
    retained_seeds: Dict[Var, Expr | Const]

    # UID ownership remains unambiguous after graphical cable substitution,
    # whereas display names may legitimately repeat across nested blocks.
    for target_var in target_vars:
        target_uids.add(target_var.uid)
    else:
        pass

    for candidate_block in block.get_all_blocks():
        retained_seeds = dict()
        for seed_var, seed_expression in candidate_block.post_init_seed_eqs.items():
            if seed_var.uid in target_uids:
                pass
            else:
                retained_seeds[seed_var] = seed_expression
        else:
            pass
        candidate_block.post_init_seed_eqs = retained_seeds
    else:
        pass


def _find_root_initialization_var_by_alias(
        block: Block,
        candidate_aliases: Sequence[str],
) -> Var | None:
    """Find one adapter-root initialized variable by stable DGS alias.

    Humanized persisted templates suffix symbolic names with the template
    identity. Accepting only the exact alias or its generated underscore suffix
    distinguishes those variables without searching unrelated child diagrams.

    :param block: Physical adapter root.
    :param candidate_aliases: Ordered stable PowerFactory aliases.
    :return: Matching initialized root variable, or ``None``.
    """
    candidate_alias: str
    initialized_var: Var

    for candidate_alias in candidate_aliases:
        for initialized_var in block.init_eqs.keys():
            alias_matches: bool = (
                initialized_var.name == candidate_alias
                or initialized_var.name.startswith(candidate_alias + "_")
            )
            if alias_matches:
                return initialized_var
            else:
                pass
        else:
            pass
    else:
        pass
    return None


def _retain_first_algebraic_assignment_for_target(
        block: Block,
        target_var: Var,
) -> None:
    """Keep one physical writer for an adapter-owned algebraic target.

    Wrapper equations precede imported controller equations in both hierarchical
    and flattened templates. Retaining the first exact-UID assignment removes
    obsolete graphical meter writers while preserving every consumer equation.

    :param block: Adapted physical wrapper, possibly already flattened.
    :param target_var: Exact equipment-owned target variable.
    :return: None.
    """
    assignment_seen: bool = False
    candidate_block: Block
    equation: Expr
    retained_equations: List[Expr]
    candidate_kept_assignment: bool
    candidate_removed_assignment: bool

    for candidate_block in block.get_all_blocks():
        retained_equations = list()
        candidate_kept_assignment = False
        candidate_removed_assignment = False
        for equation in candidate_block.algebraic_eqs:
            writes_target: bool = (
                isinstance(equation, BinOp)
                and isinstance(equation.left, Var)
                and equation.left.uid == target_var.uid
            )
            if writes_target:
                if assignment_seen:
                    candidate_removed_assignment = True
                else:
                    retained_equations.append(equation)
                    assignment_seen = True
                    candidate_kept_assignment = True
            else:
                retained_equations.append(equation)
        else:
            pass
        candidate_block.algebraic_eqs = retained_equations

        if candidate_removed_assignment and not candidate_kept_assignment:
            candidate_block.algebraic_vars = list(
                variable
                for variable in candidate_block.algebraic_vars
                if variable.uid != target_var.uid
            )
            candidate_block.out_vars = list(
                variable
                for variable in candidate_block.out_vars
                if variable.uid != target_var.uid
            )
        else:
            pass
    else:
        pass




def is_dgs_elmgenstat_direct_slot_contract(
        direct_result: DgsDirectRootBuildResult,
) -> bool:
    """Validate one static-generator boundary from transient DGS entries.

    :param direct_result: Direct root and exact source-slot relations.
    :return: ``True`` for one complete resolved ElmGenstat equipment slot.
    """
    matching_count: int = 0
    direct_entry: ElmCompInstanceEntry
    required_inputs: Set[str] = set(["id_ref", "iq_ref"])

    for direct_entry in direct_result.direct_entries:
        if (
                direct_entry.element_reference_is_resolved
                and direct_entry.element_kind == "ElmGenstat"
                and required_inputs.issubset(set(
                    direct_entry.get_slot_signal_components(
                        direction=DgsSlotSignalDirection.Input,
                    )
                ))
        ):
            matching_count += 1
        else:
            pass
    else:
        pass
    return matching_count == 1


def _find_direct_elmgenstat_current_reference_pair(
        direct_result: DgsDirectRootBuildResult,
) -> Tuple[Var | None, Var | None]:
    """Resolve current commands from one exact transient controller slot.

    :param direct_result: Direct root with slot-to-child lookup.
    :return: Active and reactive command variables, or two ``None`` values.
    """
    direct_entry: ElmCompInstanceEntry
    child_block: Block | None
    active_reference: Var | None = None
    reactive_reference: Var | None = None
    child_output: Var

    for direct_entry in direct_result.direct_entries:
        if (
                direct_entry.element_kind == "ElmGenstat"
                or direct_entry.slot_id is None
                or not set(["id_ref", "iq_ref"]).issubset(
                    set(direct_entry.get_slot_signal_components(
                        direction=DgsSlotSignalDirection.Output,
                    ))
                )
        ):
            pass
        else:
            child_block = direct_result.child_block_by_slot_id.get(
                direct_entry.slot_id,
                None,
            )
            if child_block is None:
                pass
            else:
                for child_output in child_block.out_vars:
                    if child_output.name in ("id_ref", "idref"):
                        if active_reference is None:
                            active_reference = child_output
                        else:
                            return None, None
                    else:
                        if child_output.name in ("iq_ref", "iqref"):
                            if reactive_reference is None:
                                reactive_reference = child_output
                            else:
                                return None, None
                        else:
                            pass
                else:
                    pass
    else:
        pass
    return active_reference, reactive_reference


def _is_dgs_elmgenstat_runtime_adapter_contract(block: Block) -> bool:
    """Detect an already materialized ElmGenstat physical wrapper.

    Human-readable catalogue emitters intentionally preserve executable
    symbolic structure ahead of incidental Python metadata. Detection must
    therefore use the stable device interface instead of relying only on one
    non-symbolic marker that an older catalogue may not have emitted.

    :param block: Candidate imported RMS root.
    :return: ``True`` when the complete physical wrapper contract is present.
    """
    required_external_references: Set[VarPowerFlowReferenceType] = set([
        VarPowerFlowReferenceType.P,
        VarPowerFlowReferenceType.Q,
        VarPowerFlowReferenceType.Vm,
        VarPowerFlowReferenceType.Va,
    ])
    required_parameter_references: Set[ParamPowerFlowReferenceType] = set([
        ParamPowerFlowReferenceType.Sbase,
        ParamPowerFlowReferenceType.generator_snom_mva,
    ])
    has_external_contract: bool = required_external_references.issubset(
        set(block.external_mapping.keys())
    )
    has_parameter_contract: bool = required_parameter_references.issubset(
        set(block.api_obj_mapping.keys())
    )
    if block.dynamic_model_contract.dgs_elmgenstat_runtime_adapter:
        return True
    else:
        return has_external_contract and has_parameter_contract


def _upgrade_dgs_elmgenstat_runtime_adapter(block: Block) -> None:
    """Upgrade one persisted ElmGenstat wrapper to the current contract.

    :param block: Already adapted runtime root updated in place.
    :return: None.
    """
    mapped_parameter: Var
    mapped_parameter_value: Expr | Const | None
    event_parameter: Var
    event_parameter_value: Expr | Const
    active_current_command: Var | None
    reactive_current_command: Var | None
    measurement_aliases: List[Sequence[str]]
    measurement_alias_group: Sequence[str]
    measurement_var: Var | None
    runtime_equipment_shell_names: List[str] = list()
    runtime_equipment_shell_uids: List[int] = list()
    measurement_vars_by_name: Dict[str, Var] = dict()
    authoritative_initialization_uids: Set[int] = set()
    initialized_var: Var
    active_power_equipment: Var | None
    reactive_power_equipment: Var | None
    terminal_voltage: Var
    power_factor_angle_reference: Var
    active_power_reference: Var
    reactive_power_reference: Var
    voltage_reference: Var
    power_factor_angle_connections: int
    active_power_reference_connections: int
    reactive_power_reference_connections: int
    voltage_reference_connections: int
    physical_command_seeds: Dict[Var, Expr]
    physical_command_var: Var
    physical_command_expression: Expr

    # Older humanized catalogues represented immutable equipment bases as
    # events. Move only the exact statically mapped parameters, preserving all
    # genuine tunable controller parameters in their original classification.
    for mapped_parameter in block.api_obj_mapping.values():
        mapped_parameter_value = block.event_dict.get(mapped_parameter, None)
        if isinstance(mapped_parameter_value, Const):
            block.parameters[mapped_parameter] = mapped_parameter_value
            block.event_dict.pop(mapped_parameter, None)
        else:
            pass

    # The numerical guard is also immutable and belongs beside the physical
    # bases. Locate it by its emitted symbolic name for catalogue compatibility.
    for event_parameter, event_parameter_value in list(block.event_dict.items()):
        if (
                event_parameter.name == "elmgenstat_epsilon"
                and isinstance(event_parameter_value, Const)
        ):
            block.parameters[event_parameter] = event_parameter_value
            block.event_dict.pop(event_parameter, None)
        else:
            pass
    else:
        pass

    # Root initialization equations are precisely the non-cyclic physical
    # boundary seeds created by the adapter. Replaying them late keeps older
    # persisted catalogues equivalent to newly generated templates.
    block.post_init_seed_eqs = dict(block.init_eqs)
    for initialized_var in block.init_eqs.keys():
        authoritative_initialization_uids.add(initialized_var.uid)
    else:
        pass
    block.dynamic_model_contract.dgs_explicit_initialization_uids = (
        authoritative_initialization_uids
    )
    active_current_command = _find_root_initialization_var_by_alias(
        block=block,
        candidate_aliases=list(["id_ref", "idref"]),
    )
    reactive_current_command = _find_root_initialization_var_by_alias(
        block=block,
        candidate_aliases=list(["iq_ref", "iqref"]),
    )
    if active_current_command is None or reactive_current_command is None:
        pass
    else:
        # Persisted catalogues already contain the physical wrapper. Strip
        # duplicate seeds only below that root so its solved-P/Q seeds remain
        # the final startup authority.
        child_block: Block
        for child_block in block.children:
            _remove_child_post_init_seed_targets(
                block=child_block,
                target_vars=list([
                    active_current_command,
                    reactive_current_command,
                ]),
            )
        else:
            pass

    measurement_aliases = list([
        list(["Pe"]),
        list(["Qgen"]),
        list(["Vt_r"]),
        list(["Vt_i"]),
        list(["It_r"]),
        list(["It_i"]),
    ])
    for measurement_alias_group in measurement_aliases:
        measurement_var = _find_root_initialization_var_by_alias(
            block=block,
            candidate_aliases=measurement_alias_group,
        )
        if measurement_var is None:
            pass
        else:
            runtime_equipment_shell_names.append(measurement_var.name)
            runtime_equipment_shell_uids.append(measurement_var.uid)
            measurement_vars_by_name[
                measurement_alias_group[0]
            ] = measurement_var
            # Older adapted catalogues can retain a child meter equation that
            # writes the same UID as the physical wrapper. Remove only that
            # exact target below the wrapper; consumers remain connected.
            child_block = block
            for child_block in block.children:
                _remove_connected_controller_signal_ownership(
                    block=child_block,
                    signal_name=measurement_alias_group[0],
                    input_var=measurement_var,
                )
            else:
                pass
            _retain_first_algebraic_assignment_for_target(
                block=block,
                target_var=measurement_var,
            )
    else:
        pass

    # Older humanized wrappers can preserve the ElmComp reference receivers as
    # collision-safe identifiers such as ``Pref_1`` while losing the wrapper
    # event expressions that held them at the solved operating point. Rebuild
    # the same reference contract used for a freshly adapted DGS.
    active_power_equipment = measurement_vars_by_name.get("Pe", None)
    reactive_power_equipment = measurement_vars_by_name.get("Qgen", None)
    terminal_voltage = block.external_mapping[
        VarPowerFlowReferenceType.Vm
    ]
    if (
            active_current_command is None
            or reactive_current_command is None
            or len(block.children) == 0
    ):
        physical_command_seeds = dict()
    else:
        physical_command_seeds = _build_regc_physical_startup_seeds(
            block=block.children[0],
            active_current_reference=active_current_command,
            reactive_current_reference=reactive_current_command,
            terminal_voltage=terminal_voltage,
        )
    for physical_command_var, physical_command_expression in (
            physical_command_seeds.items()
    ):
        # Upgrade an older humanized catalogue to the same explicit physical
        # startup ownership emitted by a newly parsed DGS.
        block.init_eqs[physical_command_var] = physical_command_expression
        block.post_init_seed_eqs[physical_command_var] = (
            physical_command_expression
        )
        authoritative_initialization_uids.add(physical_command_var.uid)
    else:
        pass
    block.dynamic_model_contract.dgs_explicit_initialization_uids = (
        authoritative_initialization_uids
    )
    if active_power_equipment is None or reactive_power_equipment is None:
        pass
    else:
        power_factor_angle_reference = Var(name="PFAref")
        active_power_reference = Var(name="Pref_in")
        reactive_power_reference = Var(name="Qext")
        voltage_reference = Var(name="Vref1")
        power_factor_angle_connections = _connect_named_controller_inputs(
            block=block,
            signal_name="PFAref",
            equipment_var=power_factor_angle_reference,
        )
        active_power_reference_connections = _connect_named_controller_inputs(
            block=block,
            signal_name="Pref_in",
            equipment_var=active_power_reference,
        )
        active_power_reference_connections += _connect_named_controller_inputs(
            block=block,
            signal_name="Pref",
            equipment_var=active_power_reference,
        )
        reactive_power_reference_connections = _connect_named_controller_inputs(
            block=block,
            signal_name="Qext",
            equipment_var=reactive_power_reference,
        )
        voltage_reference_connections = _connect_named_controller_inputs(
            block=block,
            signal_name="Vref1",
            equipment_var=voltage_reference,
        )

        if power_factor_angle_connections > 0:
            block.event_dict[power_factor_angle_reference] = sym.atan2(
                reactive_power_equipment,
                active_power_equipment,
            )
        else:
            pass
        if active_power_reference_connections > 0:
            block.event_dict[active_power_reference] = active_power_equipment
        else:
            pass
        if reactive_power_reference_connections > 0:
            block.event_dict[reactive_power_reference] = reactive_power_equipment
        else:
            pass
        if voltage_reference_connections > 0:
            block.event_dict[voltage_reference] = terminal_voltage
        else:
            pass
    block.dynamic_model_contract.dgs_elmgenstat_runtime_adapter = True
    block.dynamic_model_contract.dgs_equipment_owned_signal_names = list([
        "Pe",
        "Qgen",
        "Vt_r",
        "Vt_i",
        "It_r",
        "It_i",
        "PFAref",
        "Pref_in",
        "Qext",
        "Vref1",
    ])
    block.dynamic_model_contract.runtime_equipment_shell_sync_names = (
        runtime_equipment_shell_names
    )
    block.dynamic_model_contract.runtime_equipment_shell_sync_var_uids = (
        runtime_equipment_shell_uids
    )
    active_power_var: Var = block.external_mapping[
        VarPowerFlowReferenceType.P
    ]
    reactive_power_var: Var = block.external_mapping[
        VarPowerFlowReferenceType.Q
    ]
    block.dynamic_model_contract.explicit_init_excluded_var_names = list([
        active_power_var.name,
        reactive_power_var.name,
    ])


def _find_first_produced_var_recursive(
        block: Block,
        candidate_names: Sequence[str],
) -> Var | None:
    """Find the first computed variable matching an ordered alias set.

    :param block: Root block searched depth first.
    :param candidate_names: Ordered exact PowerFactory aliases.
    :return: First state/algebraic variable, or ``None``.
    """
    candidate_name: str
    variable_group: Iterable[Var]
    variable: Var
    child_block: Block
    child_result: Var | None
    variable_groups: List[Iterable[Var]] = list([
        block.algebraic_vars,
        block.state_vars,
    ])

    for candidate_name in candidate_names:
        for variable_group in variable_groups:
            for variable in variable_group:
                if variable.name == candidate_name:
                    return variable
                else:
                    pass
            else:
                pass
        else:
            pass
        for child_block in block.children:
            child_result = _find_first_produced_var_recursive(
                block=child_block,
                candidate_names=list([candidate_name]),
            )
            if child_result is None:
                pass
            else:
                return child_result
        else:
            pass
    else:
        pass
    return None




def _collect_unowned_named_references(
        block: Block,
        signal_name: str,
        identifier_by_uid: Mapping[int, str] | None = None,
) -> List[Var]:
    """Collect dangling equation references for one equipment signal.

    Graphical DGS composites can repeat a parent connector as a distinct
    symbolic object inside a child initialization equation. Such a reference
    is still an equipment input even when it is absent from the child's
    ``in_vars`` surface. A variable owned as a state, algebraic value,
    parameter, event, mode or explicit initialization target is excluded so
    an internal controller quantity with the same human name is preserved.

    :param block: Imported controller hierarchy.
    :param signal_name: Exact exported equipment signal name.
    :param identifier_by_uid: Optional persisted DGS identifier lookup.
    :return: Distinct unowned references in deterministic traversal order.
    """
    owned_uids: Set[int] = set()
    referenced_vars: List[Var] = list()
    referenced_uids: Set[int] = set()
    candidate_block: Block
    owned_group: Iterable[Var]
    owned_var: Var
    input_var: Var
    equation_groups: List[Iterable[Expr | Comparison]]
    equation_group: Iterable[Expr | Comparison]
    equation: Expr | Comparison
    equation_var: Var

    # First identify every value produced or configured inside the composite.
    # Name equality alone is not sufficient because PowerFactory diagrams may
    # legally reuse labels for unrelated internal signals.
    for candidate_block in block.get_all_blocks():
        owned_groups: List[Iterable[Var]] = list([
            candidate_block.state_vars,
            candidate_block.algebraic_vars,
            candidate_block.diff_vars,
            candidate_block.reformulated_vars,
            candidate_block.parameters.keys(),
            candidate_block.event_dict.keys(),
            candidate_block.mode_dict.keys(),
            candidate_block.init_eqs.keys(),
            candidate_block.diff_init_eqs.keys(),
            candidate_block.discrete_eqs.keys(),
        ])
        for owned_group in owned_groups:
            for owned_var in owned_group:
                owned_uids.add(owned_var.uid)
            else:
                pass
        else:
            pass
    else:
        pass

    # Formal inputs remain authoritative, while equation scanning recovers a
    # duplicated graphical connector whose UID was not propagated to in_vars.
    for candidate_block in block.get_all_blocks():
        for input_var in candidate_block.in_vars:
            if (
                    _variable_matches_local_signal(
                        variable=input_var,
                        signal_name=signal_name,
                        identifier_by_uid=identifier_by_uid,
                    )
                    and input_var.uid not in referenced_uids
            ):
                referenced_vars.append(input_var)
                referenced_uids.add(input_var.uid)
            else:
                pass
        else:
            pass

        # A native DGS measurement shell may declare its receiver as an
        # algebraic output as well as exposing it through a slot. Once the
        # physical adapter owns that signal, include the exact directed target
        # so its obsolete local assignment is removed before cable rewiring.
        for equation in candidate_block.algebraic_eqs:
            if (
                    isinstance(equation, BinOp)
                    and isinstance(equation.left, Var)
                    and _variable_matches_local_signal(
                        variable=equation.left,
                        signal_name=signal_name,
                        identifier_by_uid=identifier_by_uid,
                    )
                    and equation.left.uid not in referenced_uids
            ):
                referenced_vars.append(equation.left)
                referenced_uids.add(equation.left.uid)
            else:
                pass
        else:
            pass

        equation_groups = list([
            candidate_block.state_eqs,
            candidate_block.algebraic_eqs,
            candidate_block.differential_eqs,
            candidate_block.inequalities,
            candidate_block.init_eqs.values(),
            candidate_block.diff_init_eqs.values(),
            candidate_block.discrete_eqs.values(),
            candidate_block.post_init_seed_eqs.values(),
            candidate_block.boolean_guards.values(),
        ])
        for equation_group in equation_groups:
            for equation in equation_group:
                for equation_var in equation.get_vars():
                    if (
                            _variable_matches_local_signal(
                                variable=equation_var,
                                signal_name=signal_name,
                                identifier_by_uid=identifier_by_uid,
                            )
                            and equation_var.uid not in owned_uids
                            and equation_var.uid not in referenced_uids
                    ):
                        referenced_vars.append(equation_var)
                        referenced_uids.add(equation_var.uid)
                    else:
                        pass
                else:
                    pass
            else:
                pass
        else:
            pass
    else:
        pass
    return referenced_vars


def _connect_named_controller_inputs(
        block: Block,
        signal_name: str,
        equipment_var: Var,
) -> int:
    """Connect every exact controller input to one physical signal.

    :param block: Imported controller hierarchy updated in place.
    :param signal_name: Exact exported measurement name.
    :param equipment_var: Canonical physical signal.
    :return: Number of distinct input UIDs replaced.
    """
    matching_inputs: List[Var] = _collect_unowned_named_references(
        block=block,
        signal_name=signal_name,
        identifier_by_uid=None,
    )
    input_var: Var

    for input_var in matching_inputs:
        # A native DGS meter initially owns its graphical receiver and may have
        # attached an ``inc()`` equation plus a runtime synchronization rule.
        # Once the receiver is cabled to the equipment wrapper, that ownership
        # must be removed before substitution. Otherwise the old MW/MVAr meter
        # equation is remapped onto the equipment-base per-unit signal and
        # overwrites the physical adapter after explicit initialization.
        _remove_connected_controller_signal_ownership(
            block=block,
            signal_name=signal_name,
            input_var=input_var,
        )
        block.update_model(input_var, equipment_var)
    else:
        pass
    return len(matching_inputs)


def _remove_connected_controller_signal_ownership(
        block: Block,
        signal_name: str,
        input_var: Var,
) -> None:
    """Remove obsolete local ownership from one newly connected input.

    The DGS measurement binder deliberately materializes meter outputs before
    the physical device type is known. The ElmGenstat adapter later provides
    the authoritative equipment-base signal. At that point only assignments
    targeting the connected input are obsolete; equations consuming the input
    remain untouched and are subsequently rewired to the equipment variable.

    :param block: Imported controller hierarchy updated in place.
    :param signal_name: Exact connected signal name.
    :param input_var: Graphical receiver being connected.
    :return: None.
    """
    candidate_block: Block
    equation: Expr
    retained_equations: List[Expr]
    owns_local_assignment: bool
    raw_explicit_uids: object | None
    raw_sync_names: object | None
    sync_attribute_name: str
    retained_sync_names: List[str]

    for candidate_block in block.get_all_blocks():
        retained_equations = list()
        owns_local_assignment = False

        # Remove only equations whose left-hand shell is the receiver. All
        # controller equations that read this signal remain part of the model.
        for equation in candidate_block.algebraic_eqs:
            if (
                    isinstance(equation, BinOp)
                    and isinstance(equation.left, Var)
                    and equation.left.uid == input_var.uid
            ):
                owns_local_assignment = True
            else:
                retained_equations.append(equation)
        else:
            pass
        candidate_block.algebraic_eqs = retained_equations

        if owns_local_assignment:
            # A meter output ceases to be a locally owned algebraic/output
            # variable, while the formal input remains available for rewiring.
            candidate_block.algebraic_vars = list(
                variable
                for variable in candidate_block.algebraic_vars
                if variable.uid != input_var.uid
            )
            candidate_block.out_vars = list(
                variable
                for variable in candidate_block.out_vars
                if variable.uid != input_var.uid
            )
        else:
            pass

        if input_var in candidate_block.init_eqs:
            candidate_block.init_eqs.pop(input_var, None)
        else:
            pass
        if input_var in candidate_block.diff_init_eqs:
            candidate_block.diff_init_eqs.pop(input_var, None)
        else:
            pass
        if input_var in candidate_block.post_init_seed_eqs:
            candidate_block.post_init_seed_eqs.pop(input_var, None)
        else:
            pass
        if input_var in candidate_block.init_values:
            candidate_block.init_values.pop(input_var, None)
        else:
            pass
        if input_var in candidate_block.event_dict:
            candidate_block.event_dict.pop(input_var, None)
        else:
            pass

        candidate_block.dynamic_model_contract.dgs_explicit_initialization_uids.discard(
            input_var.uid
        )

        # Runtime and startup shell declarations use names because they are
        # persisted in human-readable templates. Remove the connected name
        # from both supported ownership lists to prevent a late meter replay.
        retained_runtime_names: List[str] = list()
        runtime_name: str
        for runtime_name in (
                candidate_block.dynamic_model_contract.runtime_measurement_shell_sync_names
        ):
            if runtime_name != signal_name:
                retained_runtime_names.append(runtime_name)
            else:
                pass
        else:
            pass
        candidate_block.dynamic_model_contract.runtime_measurement_shell_sync_names = (
            retained_runtime_names
        )

        retained_startup_names: List[str] = list()
        startup_name: str
        for startup_name in (
                candidate_block.dynamic_model_contract.startup_ordered_shell_sync_names
        ):
            if startup_name != signal_name:
                retained_startup_names.append(startup_name)
            else:
                pass
        else:
            pass
        candidate_block.dynamic_model_contract.startup_ordered_shell_sync_names = (
            retained_startup_names
        )
    else:
        pass


def _append_unique_var(variables: List[Var], variable: Var) -> None:
    """Append one variable when its UID is not already present.

    :param variables: Mutable ordered variable list.
    :param variable: Candidate variable.
    :return: None.
    """
    existing_variable: Var

    for existing_variable in variables:
        if existing_variable.uid == variable.uid:
            return
        else:
            pass
    else:
        pass
    variables.append(variable)


def _variable_matches_local_signal(
        variable: Var,
        signal_name: str,
        identifier_by_uid: Mapping[int, str] | None,
) -> bool:
    """Match a runtime variable to its stable humanized DGS identifier.

    Persisted templates suffix runtime names with the template identity and
    retain the exact collision-safe Python identifier at their root. Matching
    through that identifier prevents ``id`` from being confused with
    ``id_ref`` while still accepting a freshly parsed unsuffixed DGS variable.

    :param variable: Candidate symbolic variable.
    :param signal_name: Exact local PowerFactory signal name.
    :param identifier_by_uid: Optional persisted identifier lookup.
    :return: ``True`` only for the exact local signal.
    """
    persisted_identifier: str | None
    if identifier_by_uid is None:
        persisted_identifier = None
    else:
        persisted_identifier = identifier_by_uid.get(variable.uid, None)
    if isinstance(persisted_identifier, str):
        candidate_identifier: str = persisted_identifier
    else:
        candidate_identifier = variable.name

    if candidate_identifier == signal_name:
        return True
    else:
        pass
    if candidate_identifier.endswith("__" + signal_name):
        return True
    else:
        pass
    if candidate_identifier.endswith("_" + signal_name):
        return True
    else:
        pass
    collision_prefix: str = signal_name + "_"
    if candidate_identifier.startswith(collision_prefix):
        collision_suffix: str = candidate_identifier[len(collision_prefix):]
        if collision_suffix.isdigit():
            return True
        else:
            pass
    else:
        pass
    return False


def _all_local_signals_present(
        variables: Iterable[Var],
        required_signal_names: Set[str],
        identifier_by_uid: Mapping[int, str] | None,
) -> bool:
    """Check that a variable surface contains every exact local signal.

    :param variables: Candidate symbolic surface.
    :param required_signal_names: Exact required PowerFactory names.
    :param identifier_by_uid: Optional persisted identifier lookup.
    :return: ``True`` when every required signal is represented.
    """
    variable_list: List[Var] = list(variables)
    required_signal_name: str
    variable: Var
    signal_found: bool

    for required_signal_name in required_signal_names:
        signal_found = False
        for variable in variable_list:
            if _variable_matches_local_signal(
                    variable=variable,
                    signal_name=required_signal_name,
                    identifier_by_uid=identifier_by_uid,
            ):
                signal_found = True
            else:
                pass
        else:
            pass
        if signal_found:
            pass
        else:
            return False
    else:
        pass
    return True


def _find_local_named_var(
        block: Block,
        signal_name: str,
        identifier_by_uid: Mapping[int, str] | None = None,
) -> Var | None:
    """Find one unique local variable by its exact exported DGS name.

    :param block: Candidate protected standard-model block.
    :param signal_name: Exact DGS variable name.
    :param identifier_by_uid: Optional persisted identifier lookup.
    :return: Unique matching variable, or ``None`` when absent or ambiguous.
    """
    matching_vars: List[Var] = list()
    matching_uids: Set[int] = set()
    variable_groups: List[Iterable[Var]] = list([
        block.state_vars,
        block.algebraic_vars,
        block.diff_vars,
        block.reformulated_vars,
        block.in_vars,
        block.out_vars,
        block.parameters.keys(),
        block.event_dict.keys(),
        block.mode_dict.keys(),
        block.init_eqs.keys(),
        block.diff_init_eqs.keys(),
    ])
    variable_group: Iterable[Var]
    variable: Var

    for variable_group in variable_groups:
        for variable in variable_group:
            if (
                    _variable_matches_local_signal(
                        variable=variable,
                        signal_name=signal_name,
                        identifier_by_uid=identifier_by_uid,
                    )
                    and variable.uid not in matching_uids
            ):
                matching_vars.append(variable)
                matching_uids.add(variable.uid)
            else:
                pass
        else:
            pass
    else:
        pass

    if len(matching_vars) == 1:
        result: Var | None = matching_vars[0]
    else:
        result = None
    return result


def _build_regc_physical_startup_seeds(
        block: Block,
        active_current_reference: Var,
        reactive_current_reference: Var,
        terminal_voltage: Var,
) -> Dict[Var, Expr]:
    """Build native REGC command projections from the physical boundary.

    PowerFactory initializes the controlled ``ElmGenstat`` first and then
    propagates its solved current references backwards through the connected
    ``REGC`` block. The exported controller equations retain that dependency
    but represent it as a circular ``inc()`` chain. Reconstructing the command
    seeds closes the same loop using only physical variables and DGS topology.

    ``REGC_A`` receives direct current commands from its connected electrical
    controller. ``REGC_C`` additionally uses ``RateFlag`` to select whether
    the active input is interpreted as current or power. Its exported equation is
    ``xp = selfix(RateFlag > 0.5, Ipcmd * Vt, Ipcmd)``.  The physical startup
    projection must therefore provide ``id_ref`` when the flag is disabled and
    ``id_ref * V`` when it is enabled.  The reactive command follows
    PowerFactory's negative q-axis convention.

    :param block: Imported graphical controller hierarchy.
    :param active_current_reference: Physical ElmGenstat direct-axis current.
    :param reactive_current_reference: Physical ElmGenstat q-axis current.
    :param terminal_voltage: Solved terminal-voltage magnitude.
    :return: Exact controller-command initialization expressions.
    """
    result: Dict[Var, Expr] = dict()
    candidate_block: Block
    active_command: Var | None
    reactive_command: Var | None
    rate_flag: Var | None
    candidate_output_uids: Set[int]
    local_active_reference: Var | None
    local_reactive_reference: Var | None
    active_reference_is_output: bool
    reactive_reference_is_output: bool

    # Select the structural REGC instance that produces the exact physical
    # current pair consumed by this ElmGenstat wrapper. The graphical DGS
    # connector has already unified its Ipcmd/Iqcmd inputs with the upstream
    # electrical-control outputs, so seeding those exact UIDs closes REGC_A and
    # REGC_C without relying on composite, equipment or instance names.
    for candidate_block in block.get_all_blocks():
        active_command = _find_unique_local_var_by_alias(
            block=candidate_block,
            candidate_alias="Ipcmd",
        )
        reactive_command = _find_unique_local_var_by_alias(
            block=candidate_block,
            candidate_alias="Iqcmd",
        )
        rate_flag = _find_unique_local_var_by_alias(
            block=candidate_block,
            candidate_alias="RateFlag",
        )
        candidate_output_uids = set()
        output_var: Var
        for output_var in candidate_block.out_vars:
            candidate_output_uids.add(output_var.uid)
        else:
            pass
        local_active_reference = _find_unique_local_var_by_alias(
            block=candidate_block,
            candidate_alias="idref",
        )
        local_reactive_reference = _find_unique_local_var_by_alias(
            block=candidate_block,
            candidate_alias="iqref",
        )
        active_reference_is_output = (
            active_current_reference.uid in candidate_output_uids
        )
        reactive_reference_is_output = (
            reactive_current_reference.uid in candidate_output_uids
        )
        contract_matches: bool = (
            active_command is not None
            and reactive_command is not None
            and local_active_reference is not None
            and local_reactive_reference is not None
            and local_active_reference.uid == active_current_reference.uid
            and local_reactive_reference.uid == reactive_current_reference.uid
            and active_reference_is_output
            and reactive_reference_is_output
        )
        if contract_matches:
            if rate_flag is None:
                # REGC_A defines Ipcmd directly on the equipment current base.
                active_command_gain: Expr = Const(1.0)
            else:
                # Match the exact retained REGC_C RateFlag mode. The active
                # filter consumes current in mode zero and power in mode one,
                # so only the latter needs the terminal-voltage multiplier.
                rate_selection: Expr = sym.heaviside(
                    (rate_flag - Const(0.5)) - Const(1.0e-6)
                )
                active_command_gain = (
                    rate_selection * terminal_voltage
                    + (Const(1.0) - rate_selection)
                )
            result[active_command] = (
                active_current_reference * active_command_gain
            )
            result[reactive_command] = -reactive_current_reference

            # The wrapper owns these final t=0 commands.  Child ``inc()``
            # seeds remain useful as dependencies but must not overwrite the
            # physical projection after the final ordered startup pass.
            _remove_child_post_init_seed_targets(
                block=block,
                target_vars=list([active_command, reactive_command]),
            )
            return result
        else:
            pass
    else:
        pass
    return result


def _find_unique_local_var_by_alias(
        block: Block,
        candidate_alias: str,
) -> Var | None:
    """Find one local variable by an exact or humanized alias prefix.

    :param block: Candidate imported standard-model block.
    :param candidate_alias: Stable PowerFactory variable alias.
    :return: Unique local match, or ``None`` when absent or ambiguous.
    """
    matching_vars: List[Var] = list()
    matching_uids: Set[int] = set()
    variable_groups: List[Iterable[Var]] = list([
        block.state_vars,
        block.algebraic_vars,
        block.diff_vars,
        block.reformulated_vars,
        block.in_vars,
        block.out_vars,
        block.parameters.keys(),
        block.event_dict.keys(),
        block.mode_dict.keys(),
        block.init_eqs.keys(),
        block.diff_init_eqs.keys(),
    ])
    variable_group: Iterable[Var]
    variable: Var

    # Humanized catalogue variables append the template identity after one
    # underscore.  Within one local standard block the alias remains unique.
    for variable_group in variable_groups:
        for variable in variable_group:
            alias_matches: bool = (
                variable.name == candidate_alias
                or variable.name.startswith(candidate_alias + "_")
                or variable.name.endswith("__" + candidate_alias)
                or ("__" + candidate_alias + "_") in variable.name
            )
            if alias_matches and variable.uid not in matching_uids:
                matching_vars.append(variable)
                matching_uids.add(variable.uid)
            else:
                pass
        else:
            pass
    else:
        pass

    if len(matching_vars) == 1:
        result: Var | None = matching_vars[0]
    else:
        result = None
    return result


def _install_regc_voltage_source_equations(block: Block) -> bool:
    """Restore one protected standard REGC voltage-source submodel.

    PowerFactory may export this standard block with its complete typed port,
    state and parameter surface while omitting the protected runtime formulas.
    The structural contract identifies the WECC voltage-behind-impedance model
    independently of instance names. ``Te`` selects its standard dynamic or
    zero-delay algebraic realization.

    :param block: Candidate DGS block updated in place.
    :return: ``True`` when the exact protected contract was restored.
    """
    required_output_names: Set[str] = set(["ui_ref", "ur_ref"])
    required_parameter_names: Set[str] = set(["Te", "re", "xe"])
    required_state_names: Set[str] = set(["x_lpf_d", "x_lpf_q"])
    input_names: Set[str] = set(
        variable.name.rsplit("__", 1)[-1] for variable in block.in_vars
    )
    output_names: Set[str] = set(
        variable.name.rsplit("__", 1)[-1] for variable in block.out_vars
    )
    parameter_names: Set[str] = set(
        variable.name.rsplit("__", 1)[-1]
        for variable in block.event_dict.keys()
    )
    initialization_names: Set[str] = set(
        variable.name.rsplit("__", 1)[-1]
        for variable in block.init_eqs.keys()
    )
    contract_matches: bool = (
        len(block.state_eqs) == 0
        and len(block.algebraic_eqs) == 0
        and len(input_names) >= 5
        and required_output_names.issubset(output_names)
        and required_parameter_names.issubset(parameter_names)
        and required_state_names.issubset(initialization_names)
    )
    if contract_matches:
        pass
    else:
        return False

    terminal_real: Var | None = _find_local_named_var(block, "ur")
    if terminal_real is None:
        terminal_real = _find_local_named_var(block, "Vt_r")
    else:
        pass
    terminal_imaginary: Var | None = _find_local_named_var(block, "ui")
    if terminal_imaginary is None:
        terminal_imaginary = _find_local_named_var(block, "Vt_i")
    else:
        pass
    current_direct: Var | None = _find_local_named_var(block, "id_ref")
    if current_direct is None:
        current_direct = _find_local_named_var(block, "idref")
    else:
        pass
    current_quadrature: Var | None = _find_local_named_var(block, "iq_ref")
    if current_quadrature is None:
        current_quadrature = _find_local_named_var(block, "iqref")
    else:
        pass
    blocked: Var | None = _find_local_named_var(block, "is_blocked")
    source_real: Var | None = _find_local_named_var(block, "ur_ref")
    source_imaginary: Var | None = _find_local_named_var(block, "ui_ref")
    state_direct: Var | None = _find_local_named_var(block, "x_lpf_d")
    state_quadrature: Var | None = _find_local_named_var(block, "x_lpf_q")
    source_resistance: Var | None = _find_local_named_var(block, "re")
    source_reactance: Var | None = _find_local_named_var(block, "xe")
    delay_parameter: Var | None = _find_local_named_var(block, "Te")
    required_vars: List[Var | None] = list([
        terminal_real,
        terminal_imaginary,
        current_direct,
        current_quadrature,
        blocked,
        source_real,
        source_imaginary,
        state_direct,
        state_quadrature,
        source_resistance,
        source_reactance,
        delay_parameter,
    ])
    if any(variable is None for variable in required_vars):
        return False
    else:
        pass
    if (
            terminal_real is None
            or terminal_imaginary is None
            or current_direct is None
            or current_quadrature is None
            or blocked is None
            or source_real is None
            or source_imaginary is None
            or state_direct is None
            or state_quadrature is None
            or source_resistance is None
            or source_reactance is None
            or delay_parameter is None
    ):
        return False
    else:
        pass

    delay_expression: Expr | Const = block.event_dict[delay_parameter]
    if (
            isinstance(delay_expression, Const)
            and isinstance(delay_expression.value, (int, float))
            and not isinstance(delay_expression.value, bool)
            and math.isfinite(float(delay_expression.value))
            and float(delay_expression.value) >= 0.0
    ):
        delay_value: float = float(delay_expression.value)
    else:
        return False

    # Apply the documented complex voltage drop E = V + (r + jX) I in the
    # exported real/quadrature reference frame before the optional Te lag.
    unfiltered_direct: Expr = (
        terminal_real
        + source_resistance * current_direct
        - source_reactance * current_quadrature
    )
    unfiltered_quadrature: Expr = (
        terminal_imaginary
        + source_resistance * current_quadrature
        + source_reactance * current_direct
    )
    not_blocked: Expr = Const(1.0) - blocked
    source_real_expression: Expr = (
        not_blocked * state_direct + blocked * terminal_real
    )
    source_imaginary_expression: Expr = (
        not_blocked * state_quadrature + blocked * terminal_imaginary
    )

    block.algebraic_vars = list([source_real, source_imaginary])
    block.algebraic_eqs = list([
        source_real - source_real_expression,
        source_imaginary - source_imaginary_expression,
    ])
    if delay_value > 0.0:
        derivative_direct: Var = Var(
            name="d" + state_direct.name + "_dt",
            base_var=state_direct,
        )
        derivative_quadrature: Var = Var(
            name="d" + state_quadrature.name + "_dt",
            base_var=state_quadrature,
        )
        block.state_vars = list([state_direct, state_quadrature])
        block.state_eqs = list([
            (unfiltered_direct - state_direct) / delay_parameter,
            (unfiltered_quadrature - state_quadrature) / delay_parameter,
        ])
        block.diff_vars = list([derivative_direct, derivative_quadrature])
    else:
        # A zero Te is the exact algebraic limit of the two first-order lags;
        # retaining the named x_lpf variables preserves the DGS init surface.
        block.algebraic_vars.extend(list([state_direct, state_quadrature]))
        block.algebraic_eqs.extend(list([
            state_direct - unfiltered_direct,
            state_quadrature - unfiltered_quadrature,
        ]))
        block.state_vars = list()
        block.state_eqs = list()
        block.diff_vars = list()

    # The protected DGS surface seeds each lag state from the corresponding
    # output because PowerFactory evaluates hidden code before ``inc()``. Once
    # the open equations are restored, initialize from the physical complex
    # voltage drop first and derive the outputs second. This removes the hidden
    # evaluation dependency while preserving the exact steady-state contract.
    block.init_eqs[state_direct] = unfiltered_direct
    block.init_eqs[state_quadrature] = unfiltered_quadrature
    block.init_eqs[source_real] = source_real_expression
    block.init_eqs[source_imaginary] = source_imaginary_expression
    # The controller-wide explicit initializer may visit this protected child
    # before the physical wrapper has published id/iq and terminal-voltage
    # seeds. Replay the restored open-standard dependency chain after those
    # boundary values are available so every instance, independent of graph
    # traversal order, starts with zero derivative as PowerFactory does.
    block.post_init_seed_eqs[state_direct] = unfiltered_direct
    block.post_init_seed_eqs[state_quadrature] = unfiltered_quadrature
    block.post_init_seed_eqs[source_real] = source_real_expression
    block.post_init_seed_eqs[source_imaginary] = source_imaginary_expression
    block.dynamic_model_contract.dgs_open_standard_regc_voltage_source = True
    block.dynamic_model_contract.startup_final_init_replay_var_names = list([
        state_direct.name,
        state_quadrature.name,
        source_real.name,
        source_imaginary.name,
    ])
    return True


def _install_regc_current_pll_equations(
        block: Block,
        identifier_by_uid: Mapping[int, str] | None = None,
) -> bool:
    """Restore one protected WECC REGC current-frame PLL.

    PowerFactory can export the complete public contract of the WECC PLL while
    withholding its standard equations. The exported ``x0`` and ``x1``
    initialization targets are respectively the PI integrator and the tracked
    electrical angle. The block rotates the stationary terminal current into
    that angle and freezes both PLL states below ``Vpllfrz``.

    :param block: Candidate DGS block updated in place.
    :param identifier_by_uid: Optional persisted identifier lookup.
    :return: ``True`` when the exact protected contract was restored.
    """
    required_input_names: Set[str] = set(["ir", "ii", "ur", "ui"])
    required_output_names: Set[str] = set(["id", "iq"])
    required_parameter_names: Set[str] = set([
        "Kppll",
        "Kipll",
        "Vpllfrz",
        "wmax",
        "wmin",
    ])
    required_initialization_names: Set[str] = set(["x0", "x1"])
    voltage_magnitude_present: bool = (
        _all_local_signals_present(
            variables=block.in_vars,
            required_signal_names=set(["u"]),
            identifier_by_uid=identifier_by_uid,
        )
        or _all_local_signals_present(
            variables=block.in_vars,
            required_signal_names=set(["Vt"]),
            identifier_by_uid=identifier_by_uid,
        )
    )
    contract_matches: bool = (
        len(block.state_eqs) == 0
        and len(block.algebraic_eqs) == 0
        and voltage_magnitude_present
        and _all_local_signals_present(
            variables=block.in_vars,
            required_signal_names=required_input_names,
            identifier_by_uid=identifier_by_uid,
        )
        and _all_local_signals_present(
            variables=block.out_vars,
            required_signal_names=required_output_names,
            identifier_by_uid=identifier_by_uid,
        )
        and _all_local_signals_present(
            variables=block.event_dict.keys(),
            required_signal_names=required_parameter_names,
            identifier_by_uid=identifier_by_uid,
        )
        and _all_local_signals_present(
            variables=block.init_eqs.keys(),
            required_signal_names=required_initialization_names,
            identifier_by_uid=identifier_by_uid,
        )
    )
    if contract_matches:
        pass
    else:
        return False

    current_real: Var | None = _find_local_named_var(
        block, "ir", identifier_by_uid
    )
    current_imaginary: Var | None = _find_local_named_var(
        block, "ii", identifier_by_uid
    )
    voltage_real: Var | None = _find_local_named_var(
        block, "ur", identifier_by_uid
    )
    voltage_imaginary: Var | None = _find_local_named_var(
        block, "ui", identifier_by_uid
    )
    voltage_magnitude: Var | None = _find_local_named_var(
        block, "u", identifier_by_uid
    )
    if voltage_magnitude is None:
        # Graph normalization can replace the native ``u`` receiver with the
        # exact upstream station-voltage cable ``Vt`` before adaptation.
        voltage_magnitude = _find_local_named_var(
            block, "Vt", identifier_by_uid
        )
    else:
        pass
    current_direct: Var | None = _find_local_named_var(
        block, "id", identifier_by_uid
    )
    current_quadrature: Var | None = _find_local_named_var(
        block, "iq", identifier_by_uid
    )
    integrator_state: Var | None = _find_local_named_var(
        block, "x0", identifier_by_uid
    )
    angle_state: Var | None = _find_local_named_var(
        block, "x1", identifier_by_uid
    )
    proportional_gain: Var | None = _find_local_named_var(
        block, "Kppll", identifier_by_uid
    )
    integral_gain: Var | None = _find_local_named_var(
        block, "Kipll", identifier_by_uid
    )
    freeze_voltage: Var | None = _find_local_named_var(
        block, "Vpllfrz", identifier_by_uid
    )
    maximum_speed: Var | None = _find_local_named_var(
        block, "wmax", identifier_by_uid
    )
    minimum_speed: Var | None = _find_local_named_var(
        block, "wmin", identifier_by_uid
    )
    required_vars: List[Var | None] = list([
        current_real,
        current_imaginary,
        voltage_real,
        voltage_imaginary,
        voltage_magnitude,
        current_direct,
        current_quadrature,
        integrator_state,
        angle_state,
        proportional_gain,
        integral_gain,
        freeze_voltage,
        maximum_speed,
        minimum_speed,
    ])
    if any(variable is None for variable in required_vars):
        return False
    else:
        pass
    if (
            current_real is None
            or current_imaginary is None
            or voltage_real is None
            or voltage_imaginary is None
            or voltage_magnitude is None
            or current_direct is None
            or current_quadrature is None
            or integrator_state is None
            or angle_state is None
            or proportional_gain is None
            or integral_gain is None
            or freeze_voltage is None
            or maximum_speed is None
            or minimum_speed is None
    ):
        return False
    else:
        pass

    # The q-axis voltage is the synchronous-reference PLL error. The native
    # gains use this per-unit voltage directly, matching the open WECC model.
    angle_cosine: Expr = sym.cos(angle_state)
    angle_sine: Expr = sym.sin(angle_state)
    phase_error: Expr = (
        voltage_imaginary * angle_cosine - voltage_real * angle_sine
    )
    unlimited_speed: Expr = integrator_state + proportional_gain * phase_error
    limited_speed: Expr = sym.max(
        minimum_speed,
        sym.min(unlimited_speed, maximum_speed),
    )
    pll_enabled: Expr = sym.heaviside(voltage_magnitude - freeze_voltage)
    current_direct_expression: Expr = (
        current_real * angle_cosine + current_imaginary * angle_sine
    )
    current_quadrature_expression: Expr = (
        current_imaginary * angle_cosine - current_real * angle_sine
    )
    integrator_derivative: Var = Var(
        name="d" + integrator_state.name + "_dt",
        base_var=integrator_state,
    )
    angle_derivative: Var = Var(
        name="d" + angle_state.name + "_dt",
        base_var=angle_state,
    )

    # Restore the two PLL states and the exact stationary-to-dq transform.
    # Multiplying both derivatives by the enable flag retains the last locked
    # frame during deep voltage depressions, which is the Vpllfrz contract.
    block.state_vars = list([integrator_state, angle_state])
    block.state_eqs = list([
        pll_enabled * integral_gain * phase_error,
        pll_enabled * limited_speed,
    ])
    block.diff_vars = list([integrator_derivative, angle_derivative])
    block.algebraic_vars = list([current_direct, current_quadrature])
    block.algebraic_eqs = list([
        current_direct - current_direct_expression,
        current_quadrature - current_quadrature_expression,
    ])
    block.init_eqs[integrator_state] = Const(0.0)
    block.init_eqs[angle_state] = sym.atan2(voltage_imaginary, voltage_real)
    block.init_eqs[current_direct] = current_direct_expression
    block.init_eqs[current_quadrature] = current_quadrature_expression
    block.post_init_seed_eqs[current_direct] = current_direct_expression
    block.post_init_seed_eqs[current_quadrature] = current_quadrature_expression
    block.dynamic_model_contract.dgs_open_standard_regc_current_pll = True
    block.dynamic_model_contract.startup_final_init_replay_var_names = list([
        current_direct.name,
        current_quadrature.name,
    ])
    return True


def _install_protected_open_standard_equations(block: Block) -> int:
    """Restore every recognized protected open-standard child recursively.

    :param block: Imported DGS controller hierarchy.
    :return: Number of exact standard blocks restored.
    """
    restored_count: int = 0
    candidate_block: Block
    identifier_by_uid: Dict[int, str] = dict()

    for candidate_block in block.get_all_blocks():
        if _install_regc_current_pll_equations(
                block=candidate_block,
                identifier_by_uid=identifier_by_uid,
        ):
            restored_count += 1
        else:
            pass
        if _install_regc_voltage_source_equations(block=candidate_block):
            restored_count += 1
        else:
            pass
    else:
        pass
    return restored_count


def _has_closed_explicit_initialization_contract(block: Block) -> bool:
    """Check that every initialization dependency has a runtime owner.

    Protected PowerFactory models can export an ``inc()`` equation whose
    right-hand side is calculated only by hidden compiled code. Such a model
    must remain partial until it is matched to an open standard model; treating
    the missing signal as zero would silently change its operating point.

    :param block: Adapted controller hierarchy after physical input binding.
    :return: ``True`` when every explicit dependency is resolvable.
    """
    resolvable_uids: Set[int] = set()
    candidate_block: Block
    resolvable_group: Iterable[Var]
    resolvable_var: Var
    initialization_groups: List[Iterable[Expr]]
    initialization_group: Iterable[Expr]
    initialization_expr: Expr
    dependency_var: Var

    for candidate_block in block.get_all_blocks():
        resolvable_groups: List[Iterable[Var]] = list([
            candidate_block.state_vars,
            candidate_block.algebraic_vars,
            candidate_block.diff_vars,
            candidate_block.out_vars,
            candidate_block.reformulated_vars,
            candidate_block.in_vars,
            candidate_block.parameters.keys(),
            candidate_block.event_dict.keys(),
            candidate_block.mode_dict.keys(),
            candidate_block.init_eqs.keys(),
            candidate_block.diff_init_eqs.keys(),
        ])
        for resolvable_group in resolvable_groups:
            for resolvable_var in resolvable_group:
                resolvable_uids.add(resolvable_var.uid)
            else:
                pass
        else:
            pass
    else:
        pass

    for candidate_block in block.get_all_blocks():
        initialization_groups = list([
            candidate_block.init_eqs.values(),
            candidate_block.diff_init_eqs.values(),
        ])
        for initialization_group in initialization_groups:
            for initialization_expr in initialization_group:
                for dependency_var in initialization_expr.get_vars():
                    if dependency_var.uid in resolvable_uids:
                        pass
                    else:
                        return False
                else:
                    pass
            else:
                pass
        else:
            pass
    else:
        pass
    return True


def build_dgs_elmgenstat_rms_runtime_template(
        control_template: RmsModelTemplate,
        clone_control_block: bool = True,
        direct_result: DgsDirectRootBuildResult | None = None,
) -> RmsModelTemplate | None:
    """Wrap an imported controller with the native ElmGenstat injection.

    PowerFactory's controlled static generator consumes ``id_ref`` and
    ``iq_ref`` on its own MVA base. The adapter converts those exact commands
    to VeraGrid system-base P/Q injections and feeds the controller with the
    terminal P/Q, voltage and current measurements declared by its DGS slots.

    :param control_template: Imported DGS composite template.
    :param clone_control_block: Clone reusable GUI input before adaptation.
    :param direct_result: Optional transient direct-root conversion context.
    :return: Assignable Generator RMS template, or ``None`` if incomplete.
    """
    control_block: Block
    runtime_template: RmsModelTemplate

    # A persisted humanized catalogue can already contain the physical
    # ElmGenstat wrapper. Upgrade that wrapper in place (or on its requested
    # clone) instead of nesting a second adapter around the same controller.
    if _is_dgs_elmgenstat_runtime_adapter_contract(
            block=control_template.block,
    ):
        if clone_control_block:
            control_block = copy.deepcopy(control_template.block)
        else:
            control_block = control_template.block
        _upgrade_dgs_elmgenstat_runtime_adapter(block=control_block)
        runtime_template = RmsModelTemplate(name=control_template.name)
        runtime_template.tpe = DeviceType.GeneratorDevice
        runtime_template.block = control_block
        return runtime_template
    else:
        pass

    if clone_control_block:
        control_block = copy.deepcopy(control_template.block)
    else:
        control_block = control_template.block
    if direct_result is None:
        return None
    else:
        pass
    if not is_dgs_elmgenstat_direct_slot_contract(direct_result=direct_result):
        return None
    else:
        pass

    # Restore only structurally identified open standards whose runtime
    # formulas PowerFactory omitted from the otherwise complete DGS surface.
    _install_protected_open_standard_equations(block=control_block)

    # Resolve only the exact converter outputs cabled to the physical slot.
    active_current_command: Var | None
    reactive_current_command: Var | None
    active_current_command, reactive_current_command = (
        _find_direct_elmgenstat_current_reference_pair(
            direct_result=direct_result,
        )
    )
    if active_current_command is None or reactive_current_command is None:
        return None
    else:
        id_ref: Var = active_current_command
        iq_ref: Var = reactive_current_command

    # The wrapper reconstructs these exact commands from the solved P/Q
    # operating point. Remove generic imported late seeds so a nested control
    # equation cannot replace that physical boundary after initialization.
    _remove_child_post_init_seed_targets(
        block=control_block,
        target_vars=list([id_ref, iq_ref]),
    )

    # Network-facing values use VeraGrid's ordinary generator RMS contract.
    terminal_voltage: Var = Var(
        name="Vm",
        reference=VarPowerFlowReferenceType.Vm,
    )
    terminal_angle: Var = Var(
        name="Va",
        reference=VarPowerFlowReferenceType.Va,
    )
    active_power_system: Var = Var(
        name="Pg",
        reference=VarPowerFlowReferenceType.P,
    )
    reactive_power_system: Var = Var(
        name="Qg",
        reference=VarPowerFlowReferenceType.Q,
    )

    # Controller measurements remain on the equipment base, matching the
    # current commands and the parameter units exported by PowerFactory.
    active_power_equipment: Var = Var(name="Pe")
    reactive_power_equipment: Var = Var(name="Qgen")
    terminal_voltage_real: Var = Var(name="Vt_r")
    terminal_voltage_imaginary: Var = Var(name="Vt_i")
    terminal_current_real: Var = Var(name="It_r")
    terminal_current_imaginary: Var = Var(name="It_i")
    power_factor_angle_reference: Var = Var(name="PFAref")
    active_power_reference: Var = Var(name="Pref_in")
    reactive_power_reference: Var = Var(name="Qext")
    voltage_reference: Var = Var(name="Vref1")
    system_power_base: Var = Var(name="Sbase")
    equipment_power_base: Var = Var(name="Snom")
    epsilon: Var = Var(name="elmgenstat_epsilon")
    dq_angle_delay_enabled: Var = Var(name="dq_angle_delay_enabled")
    dq_angle_delay_time_constant: Var = Var(name="dq_angle_delay_time_constant")
    delayed_angle_cosine: Var = Var(name="dq_angle_cosine_delayed")
    delayed_angle_sine: Var = Var(name="dq_angle_sine_delayed")

    equipment_to_system_gain: Expr = equipment_power_base / system_power_base
    instantaneous_angle_cosine: Expr = sym.cos(terminal_angle)
    instantaneous_angle_sine: Expr = sym.sin(terminal_angle)
    voltage_real_expression: Expr = (
        terminal_voltage * instantaneous_angle_cosine
    )
    voltage_imaginary_expression: Expr = (
        terminal_voltage * instantaneous_angle_sine
    )
    # PowerFactory optionally filters the internally calculated terminal-angle
    # sine and cosine before transforming dq current references to the network
    # phasor. The disabled branch keeps the historical instantaneous frame,
    # while its two preallocated states remain constant and zero-overhead in
    # the current injection equations.
    delay_disabled: Expr = Const(1.0) - dq_angle_delay_enabled
    safe_delay_time_constant: Expr = (
        dq_angle_delay_time_constant + delay_disabled
    )
    reference_angle_cosine: Expr = (
        dq_angle_delay_enabled * delayed_angle_cosine
        + delay_disabled * instantaneous_angle_cosine
    )
    reference_angle_sine: Expr = (
        dq_angle_delay_enabled * delayed_angle_sine
        + delay_disabled * instantaneous_angle_sine
    )
    current_real_expression: Expr = (
        id_ref * reference_angle_cosine
        - iq_ref * reference_angle_sine
    )
    current_imaginary_expression: Expr = (
        id_ref * reference_angle_sine
        + iq_ref * reference_angle_cosine
    )
    relative_angle_cosine: Expr = (
        reference_angle_cosine * instantaneous_angle_cosine
        + reference_angle_sine * instantaneous_angle_sine
    )
    relative_angle_sine: Expr = (
        reference_angle_sine * instantaneous_angle_cosine
        - reference_angle_cosine * instantaneous_angle_sine
    )
    terminal_active_current: Expr = (
        id_ref * relative_angle_cosine
        - iq_ref * relative_angle_sine
    )
    terminal_reactive_current: Expr = (
        id_ref * relative_angle_sine
        + iq_ref * relative_angle_cosine
    )
    power_factor_angle_expression: Expr = sym.atan2(
        reactive_power_equipment,
        active_power_equipment,
    )

    # Connect every exported measurement occurrence before the wrapper is
    # assembled. Missing optional slots remain explicit controller inputs.
    _connect_named_controller_inputs(control_block, "Vt", terminal_voltage)
    _connect_named_controller_inputs(control_block, "u", terminal_voltage)
    _connect_named_controller_inputs(control_block, "Vt_r", terminal_voltage_real)
    _connect_named_controller_inputs(control_block, "ur", terminal_voltage_real)
    _connect_named_controller_inputs(control_block, "Vt_i", terminal_voltage_imaginary)
    _connect_named_controller_inputs(control_block, "ui", terminal_voltage_imaginary)
    _connect_named_controller_inputs(control_block, "Pe", active_power_equipment)
    _connect_named_controller_inputs(control_block, "Qgen", reactive_power_equipment)
    # REGC_A exports Qgen0 as the operating-point seed used by its first
    # gradient-limiter mode decision. It is the same physical terminal Q
    # measurement at t=0, not an independent controller setting.
    _connect_named_controller_inputs(control_block, "Qgen0", reactive_power_equipment)
    _connect_named_controller_inputs(control_block, "ir", terminal_current_real)
    _connect_named_controller_inputs(control_block, "It_r", terminal_current_real)
    _connect_named_controller_inputs(control_block, "ii", terminal_current_imaginary)
    _connect_named_controller_inputs(control_block, "It_i", terminal_current_imaginary)
    power_factor_angle_connections: int = _connect_named_controller_inputs(
        control_block,
        "PFAref",
        power_factor_angle_reference,
    )
    active_power_reference_connections: int = _connect_named_controller_inputs(
        control_block,
        "Pref_in",
        active_power_reference,
    )
    reactive_power_reference_connections: int = _connect_named_controller_inputs(
        control_block,
        "Qext",
        reactive_power_reference,
    )
    voltage_reference_connections: int = _connect_named_controller_inputs(
        control_block,
        "Vref1",
        voltage_reference,
    )

    equipment_signals: Dict[str, Var] = dict([
        ("Vm", terminal_voltage),
        ("Va", terminal_angle),
        ("Pe", active_power_equipment),
        ("Qgen", reactive_power_equipment),
        ("Vt_r", terminal_voltage_real),
        ("ur", terminal_voltage_real),
        ("Vt_i", terminal_voltage_imaginary),
        ("ui", terminal_voltage_imaginary),
        ("It_r", terminal_current_real),
        ("It_i", terminal_current_imaginary),
        ("PFAref", power_factor_angle_reference),
        ("Pref_in", active_power_reference),
        ("Qext", reactive_power_reference),
        ("Vref1", voltage_reference),
    ])
    # PowerFactory defines every genuinely disconnected graphical DSL input as
    # zero. Preserve that native baseline only after all physical measurements
    # have been bound, so optional freeze/protection/plant slots remain
    # executable without overriding any connected cable.
    install_unconnected_dgs_control_input_defaults(
        block=control_block,
        equipment_signals=equipment_signals,
    )
    if _has_closed_explicit_initialization_contract(block=control_block):
        pass
    else:
        # The DGS identifies this controller structurally but does not contain
        # enough executable information to initialize it without a hidden
        # PowerFactory implementation. Keep the device on the explicit partial
        # fixed-injection path rather than manufacturing a dynamic equivalent.
        return None

    wrapper_inputs: List[Var] = list([terminal_voltage, terminal_angle])
    wrapper_outputs: List[Var] = list([active_power_system, reactive_power_system])
    controller_output: Var
    for controller_output in control_block.out_vars:
        _append_unique_var(wrapper_outputs, controller_output)
    else:
        pass
    _append_unique_var(wrapper_outputs, id_ref)
    _append_unique_var(wrapper_outputs, iq_ref)

    initial_values: Dict[Var, Expr] = dict()
    initial_values[id_ref] = (
        active_power_system
        / (equipment_to_system_gain * terminal_voltage + epsilon)
    )
    initial_values[iq_ref] = (
        -reactive_power_system
        / (equipment_to_system_gain * terminal_voltage + epsilon)
    )
    initial_values[active_power_equipment] = (
        active_power_system / (equipment_to_system_gain + epsilon)
    )
    initial_values[reactive_power_equipment] = (
        reactive_power_system / (equipment_to_system_gain + epsilon)
    )
    initial_values[terminal_voltage_real] = voltage_real_expression
    initial_values[terminal_voltage_imaginary] = voltage_imaginary_expression
    initial_values[terminal_current_real] = current_real_expression
    initial_values[terminal_current_imaginary] = current_imaginary_expression
    initial_values[delayed_angle_cosine] = instantaneous_angle_cosine
    initial_values[delayed_angle_sine] = instantaneous_angle_sine
    physical_command_seeds: Dict[Var, Expr] = (
        _build_regc_physical_startup_seeds(
            block=control_block,
            active_current_reference=id_ref,
            reactive_current_reference=iq_ref,
            terminal_voltage=terminal_voltage,
        )
    )
    physical_command_var: Var
    physical_command_expression: Expr
    for physical_command_var, physical_command_expression in (
            physical_command_seeds.items()
    ):
        initial_values[physical_command_var] = physical_command_expression
    else:
        pass

    # ElmComp exports operating-point references that remain constant until a
    # user event changes them. Register only ports present in this DGS frame;
    # their expressions are evaluated after the physical P/Q/V startup values
    # are known and then retained as the normal runtime event baselines.
    equipment_reference_values: Dict[Var, Expr] = dict()
    if power_factor_angle_connections > 0:
        equipment_reference_values[power_factor_angle_reference] = (
            power_factor_angle_expression
        )
    else:
        pass
    if active_power_reference_connections > 0:
        equipment_reference_values[active_power_reference] = active_power_equipment
    else:
        pass
    if reactive_power_reference_connections > 0:
        equipment_reference_values[reactive_power_reference] = (
            reactive_power_equipment
        )
    else:
        pass
    if voltage_reference_connections > 0:
        equipment_reference_values[voltage_reference] = terminal_voltage
    else:
        pass

    api_mapping: Dict[ParamPowerFlowReferenceType, Var] = dict()
    api_mapping[ParamPowerFlowReferenceType.Sbase] = system_power_base
    api_mapping[ParamPowerFlowReferenceType.generator_snom_mva] = equipment_power_base
    api_mapping[
        ParamPowerFlowReferenceType.generator_rms_dq_reference_angle_delay_enabled
    ] = dq_angle_delay_enabled
    api_mapping[
        ParamPowerFlowReferenceType
        .generator_rms_dq_reference_angle_delay_time_constant
    ] = dq_angle_delay_time_constant

    wrapper_block: Block = Block(
        name=control_template.name,
        children=list([control_block]),
        in_vars=wrapper_inputs,
        out_vars=wrapper_outputs,
        state_vars=list([delayed_angle_cosine, delayed_angle_sine]),
        state_eqs=list([
            dq_angle_delay_enabled
            * (instantaneous_angle_cosine - delayed_angle_cosine)
            / safe_delay_time_constant,
            dq_angle_delay_enabled
            * (instantaneous_angle_sine - delayed_angle_sine)
            / safe_delay_time_constant,
        ]),
        algebraic_vars=list([
            active_power_system,
            reactive_power_system,
            active_power_equipment,
            reactive_power_equipment,
            terminal_voltage_real,
            terminal_voltage_imaginary,
            terminal_current_real,
            terminal_current_imaginary,
        ]),
        algebraic_eqs=list([
            active_power_system
            - terminal_voltage
            * terminal_active_current
            * equipment_to_system_gain,
            reactive_power_system
            + terminal_voltage
            * terminal_reactive_current
            * equipment_to_system_gain,
            active_power_equipment
            - active_power_system / (equipment_to_system_gain + epsilon),
            reactive_power_equipment
            - reactive_power_system / (equipment_to_system_gain + epsilon),
            terminal_voltage_real - voltage_real_expression,
            terminal_voltage_imaginary - voltage_imaginary_expression,
            terminal_current_real - current_real_expression,
            terminal_current_imaginary - current_imaginary_expression,
        ]),
        init_eqs=initial_values,
        # Equipment measurements and current references are the physical
        # startup boundary of the graphical controller. Re-evaluate these
        # non-cyclic expressions after imported ``inc()`` and meter passes so
        # every RMS solver receives the same equipment-base operating point.
        post_init_seed_eqs=dict(initial_values),
        event_dict=equipment_reference_values,
        parameters=dict([
            (system_power_base, Const(100.0)),
            (equipment_power_base, Const(100.0)),
            (epsilon, Const(1.0e-12)),
            (dq_angle_delay_enabled, Const(0.0)),
            (dq_angle_delay_time_constant, Const(0.0)),
        ]),
        external_mapping=dict([
            (VarPowerFlowReferenceType.P, active_power_system),
            (VarPowerFlowReferenceType.Q, reactive_power_system),
            (VarPowerFlowReferenceType.Vm, terminal_voltage),
            (VarPowerFlowReferenceType.Va, terminal_angle),
        ]),
        api_obj_mapping=api_mapping,
    )
    wrapper_block.dynamic_model_contract.dgs_elmgenstat_runtime_adapter = True
    # The physical ElmGenstat boundary owns these solved operating-point
    # values. Mark the exact UIDs as authoritative so a nested graphical
    # controller ``inc()`` helper cannot replace the P/Q-derived current
    # commands when the final dependency cone is replayed at t=0.
    authoritative_initialization_uids: Set[int] = set()
    initialized_var: Var
    for initialized_var in initial_values.keys():
        authoritative_initialization_uids.add(initialized_var.uid)
    else:
        pass
    wrapper_block.dynamic_model_contract.dgs_explicit_initialization_uids = (
        authoritative_initialization_uids
    )
    # These aliases are physical equipment-base boundaries supplied by this
    # adapter. The later generic DGS meter pass must not rematerialize its raw
    # MW/MVAr expressions on the already converted per-unit variables.
    wrapper_block.dynamic_model_contract.dgs_equipment_owned_signal_names = list([
        "Pe",
        "Qgen",
        "Vt_r",
        "Vt_i",
        "It_r",
        "It_i",
        "PFAref",
        "Pref_in",
        "Qext",
        "Vref1",
    ])
    # These direct algebraic shells are derived measurements, not independent
    # Newton guesses. Refresh them from their canonical wrapper equations after
    # every physical boundary update so the controller sees one coherent
    # terminal snapshot at startup and during RMS events.
    wrapper_block.dynamic_model_contract.runtime_equipment_shell_sync_names = list([
        active_power_equipment.name,
        reactive_power_equipment.name,
        terminal_voltage_real.name,
        terminal_voltage_imaginary.name,
        terminal_current_real.name,
        terminal_current_imaginary.name,
    ])
    wrapper_block.dynamic_model_contract.runtime_equipment_shell_sync_var_uids = list([
        active_power_equipment.uid,
        reactive_power_equipment.uid,
        terminal_voltage_real.uid,
        terminal_voltage_imaginary.uid,
        terminal_current_real.uid,
        terminal_current_imaginary.uid,
    ])
    equipment_measurement_var: Var
    for equipment_measurement_var in list([
        active_power_equipment,
        reactive_power_equipment,
        terminal_voltage_real,
        terminal_voltage_imaginary,
        terminal_current_real,
        terminal_current_imaginary,
    ]):
        _retain_first_algebraic_assignment_for_target(
            block=wrapper_block,
            target_var=equipment_measurement_var,
        )
    else:
        pass
    wrapper_block.dynamic_model_contract.explicit_init_excluded_var_names = list([
        active_power_system.name,
        reactive_power_system.name,
    ])

    runtime_template = RmsModelTemplate(
        name=control_template.name,
    )
    runtime_template.tpe = DeviceType.GeneratorDevice
    runtime_template.block = wrapper_block
    return runtime_template
