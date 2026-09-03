from __future__ import annotations

import copy
from typing import Dict, Iterable, List, Set, Tuple

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.IO.dgs.dgs_objects import ElmSvs
from VeraGridEngine.IO.dgs.dgs_to_blocks import (
    DgsDirectRootBuildResult,
    DgsSlotSignalDirection,
    ElmCompInstanceEntry,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var, safe_divide
from VeraGridEngine.enumerations import (
    DeviceType,
    ParamPowerFlowReferenceType,
    VarPowerFlowReferenceType,
)








def is_dgs_elmsvs_direct_slot_contract(
        direct_result: DgsDirectRootBuildResult,
) -> bool:
    """Validate one ElmSvs boundary from transient DGS slot relations.

    :param direct_result: Direct root and exact source-slot relations.
    :return: ``True`` for one complete resolved ElmSvs equipment slot.
    """
    matching_count: int = 0
    direct_entry: ElmCompInstanceEntry
    required_outputs: Set[str] = set([
        "ysvs", "qreact", "qcap", "qfixcap", "nxcap", "nfixcap",
    ])

    for direct_entry in direct_result.direct_entries:
        if (
                direct_entry.element_reference_is_resolved
                and direct_entry.element_kind == "ElmSvs"
                and set(["bsvs"]).issubset(set(
                    direct_entry.get_slot_signal_components(
                        direction=DgsSlotSignalDirection.Input,
                    )
                ))
                and required_outputs.issubset(set(
                    direct_entry.get_slot_signal_components(
                        direction=DgsSlotSignalDirection.Output,
                    )
                ))
        ):
            matching_count += 1
        else:
            pass
    else:
        pass
    return matching_count == 1


def _find_direct_elmsvs_command(
        direct_result: DgsDirectRootBuildResult,
) -> Var | None:
    """Resolve the exact controller output cabled to ElmSvs ``bsvs``.

    :param direct_result: Direct root with slot-to-child lookup.
    :return: Exact controller command variable, or ``None`` when ambiguous.
    """
    result: Var | None = None
    direct_entry: ElmCompInstanceEntry
    child_block: Block | None
    child_output: Var

    for direct_entry in direct_result.direct_entries:
        if (
                direct_entry.element_kind == "ElmSvs"
                or direct_entry.slot_id is None
                or "bsvs" not in direct_entry.get_slot_signal_components(
                    direction=DgsSlotSignalDirection.Output,
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
                    if child_output.name == "bsvs":
                        if result is None:
                            result = child_output
                        else:
                            return None
                    else:
                        pass
                else:
                    pass
    else:
        pass
    return result


def _find_produced_var_recursive(block: Block, var_name: str) -> Var | None:
    """Find one exact controller-produced variable recursively.

    :param block: Imported controller root.
    :param var_name: Exact DGS cable name.
    :return: Matching produced variable or ``None``.
    """
    produced_var: Var
    child_block: Block
    child_result: Var | None

    for produced_var in block.algebraic_vars:
        if produced_var.name == var_name:
            return produced_var
        else:
            pass
    for produced_var in block.state_vars:
        if produced_var.name == var_name:
            return produced_var
        else:
            pass
    for child_block in block.children:
        child_result = _find_produced_var_recursive(
            block=child_block,
            var_name=var_name,
        )
        if child_result is None:
            pass
        else:
            return child_result
    return None


def _connect_named_inputs(block: Block, signal_name: str, source_var: Var) -> int:
    """Connect every exact named controller input to one physical signal.

    :param block: Imported controller hierarchy updated in place.
    :param signal_name: Exact input cable name.
    :param source_var: Canonical equipment-owned signal.
    :return: Number of distinct input variables replaced.
    """
    matching_inputs: List[Var] = list()
    matching_uids: Set[int] = set()
    candidate_block: Block
    input_var: Var

    # Collect before replacing because ``update_model`` mutates interfaces.
    for candidate_block in block.get_all_blocks():
        for input_var in candidate_block.in_vars:
            if input_var.name == signal_name and input_var.uid not in matching_uids:
                matching_inputs.append(input_var)
                matching_uids.add(input_var.uid)
            else:
                pass
        else:
            pass
    else:
        pass

    for input_var in matching_inputs:
        block.update_model(input_var, source_var)
    else:
        pass
    return len(matching_inputs)


def _append_unique_var(variables: List[Var], variable: Var) -> None:
    """Append one symbolic variable exactly once by UID.

    :param variables: Ordered destination variables.
    :param variable: Candidate variable.
    :return: None.
    """
    existing_variable: Var

    for existing_variable in variables:
        if existing_variable.uid == variable.uid:
            return
        else:
            pass
    variables.append(variable)




def build_dgs_elmsvs_rms_runtime_template(
        control_template: RmsModelTemplate,
        clone_control_block: bool = True,
        direct_result: DgsDirectRootBuildResult | None = None,
        source_svs: ElmSvs | None = None,
) -> RmsModelTemplate | None:
    """Wrap one graphical ``ElmSvs`` controller in its physical RMS equations.

    The DGS contains the graphical controller but PowerFactory keeps the
    ``ElmSvs`` electrical equations built in. This adapter restores only that
    documented physical boundary: the controller command ``bsvs`` becomes the
    shunt susceptance in MVAr at 1 p.u., and its terminal reactive injection is
    converted to the VeraGrid system base.

    :param control_template: Imported exact graphical controller template.
    :param clone_control_block: Clone the controller before modifying its ports.
    :param direct_result: Optional transient direct-root conversion context.
    :param source_svs: Optional exact source equipment used during conversion.
    :return: Assignable controllable-shunt template or ``None`` if incomplete.
    """
    control_block: Block

    if clone_control_block:
        control_block = copy.deepcopy(control_template.block)
    else:
        control_block = control_template.block

    if direct_result is None or source_svs is None:
        return None
    else:
        pass
    if is_dgs_elmsvs_direct_slot_contract(direct_result=direct_result):
        pass
    else:
        return None

    bsvs: Var | None = _find_direct_elmsvs_command(direct_result=direct_result)
    if bsvs is None:
        return None
    else:
        pass

    qreact_value: float | None = float(source_svs.tcrmax)
    qcap_value: float | None = float(source_svs.qmin)
    qfixcap_value: float | None = float(source_svs.Qfixcap)
    nxcap_value: float | None = float(source_svs.nxcap)
    nfixcap_value: float | None = float(source_svs.nfixcap)
    metadata_values: List[float | None] = list([
        qreact_value,
        qcap_value,
        qfixcap_value,
        nxcap_value,
        nfixcap_value,
    ])
    metadata_is_complete: bool = True
    metadata_value: float | None
    for metadata_value in metadata_values:
        if metadata_value is None:
            metadata_is_complete = False
        else:
            pass
    else:
        pass
    if metadata_is_complete:
        pass
    else:
        return None

    # The explicit guard above narrows every physical constant to float.
    qreact_constant: float = float(qreact_value)
    qcap_constant: float = float(qcap_value)
    qfixcap_constant: float = float(qfixcap_value)
    nxcap_constant: float = float(nxcap_value)
    nfixcap_constant: float = float(nfixcap_value)

    terminal_voltage: Var = Var(
        name="Vm",
        reference=VarPowerFlowReferenceType.Vm,
    )
    terminal_angle: Var = Var(
        name="Va",
        reference=VarPowerFlowReferenceType.Va,
    )
    remote_voltage: Var = Var(name="Vm_remote")
    active_power: Var = Var(
        name="Psvs",
        reference=VarPowerFlowReferenceType.P,
    )
    reactive_power: Var = Var(
        name="Qsvs",
        reference=VarPowerFlowReferenceType.Q,
    )
    qreact: Var = Var(name="qreact")
    qcap: Var = Var(name="qcap")
    qfixcap: Var = Var(name="qfixcap")
    nxcap: Var = Var(name="nxcap")
    nfixcap: Var = Var(name="nfixcap")
    system_power_base: Var = Var(name="Sbase")

    # Restore the exact equipment/controller cables exported by the frame.
    _connect_named_inputs(control_block, "u", terminal_voltage)
    _connect_named_inputs(control_block, "uremote", remote_voltage)
    _connect_named_inputs(control_block, "ysvs", bsvs)
    _connect_named_inputs(control_block, "qreact", qreact)
    _connect_named_inputs(control_block, "qcap", qcap)
    _connect_named_inputs(control_block, "qfixcap", qfixcap)
    _connect_named_inputs(control_block, "nxcap", nxcap)
    _connect_named_inputs(control_block, "nfixcap", nfixcap)

    reactive_power_expression: Expr = (
            bsvs * terminal_voltage * terminal_voltage / system_power_base
    )
    susceptance_seed_expression: Expr = safe_divide(
        numerator=reactive_power * system_power_base,
        denominator=terminal_voltage * terminal_voltage,
        zero_denominator_value=Const(1.0e-6),
    )

    wrapper_outputs: List[Var] = list([active_power, reactive_power])
    controller_output: Var
    for controller_output in control_block.out_vars:
        _append_unique_var(wrapper_outputs, controller_output)

    _append_unique_var(wrapper_outputs, bsvs)

    api_mapping: Dict[ParamPowerFlowReferenceType, Var] = dict()
    api_mapping[ParamPowerFlowReferenceType.Sbase] = system_power_base

    wrapper_block: Block = Block(
        name=control_template.name,
        children=list([control_block]),
        in_vars=list([terminal_voltage, terminal_angle, remote_voltage]),
        out_vars=wrapper_outputs,
        algebraic_vars=list([active_power, reactive_power]),
        algebraic_eqs=list([
            active_power,
            reactive_power - reactive_power_expression,
        ]),
        init_eqs=dict([
            (active_power, Const(0.0)),
            (bsvs, susceptance_seed_expression),
            (reactive_power, reactive_power_expression),
        ]),
        post_init_seed_eqs=dict([
            (active_power, Const(0.0)),
            (bsvs, susceptance_seed_expression),
            (reactive_power, reactive_power_expression),
        ]),
        parameters=dict([
            (system_power_base, Const(100.0)),
            (qreact, Const(qreact_constant)),
            (qcap, Const(qcap_constant)),
            (qfixcap, Const(qfixcap_constant)),
            (nxcap, Const(nxcap_constant)),
            (nfixcap, Const(nfixcap_constant)),
        ]),
        external_mapping=dict([
            (VarPowerFlowReferenceType.P, active_power),
            (VarPowerFlowReferenceType.Q, reactive_power),
            (VarPowerFlowReferenceType.Vm, terminal_voltage),
            (VarPowerFlowReferenceType.Va, terminal_angle),
        ]),
        api_obj_mapping=api_mapping,
    )
    wrapper_block.dynamic_model_contract.dgs_elmsvs_runtime_adapter = True
    # The solved terminal Q is a physical initialization boundary, not another
    # controller assignment. Keep it outside the local explicit-init graph and
    # make the derived susceptance equation outrank the graphical limiter's
    # duplicate ``inc(bsvs)`` target. The remaining OEM chain then initializes
    # SV03 from that physical value exactly as declared in the source DGS.
    wrapper_block.dynamic_model_contract.explicit_init_excluded_var_names = list([
        reactive_power.name,
    ])
    wrapper_block.dynamic_model_contract.explicit_init_override_init_exprs = dict([
        (bsvs.name, susceptance_seed_expression),
    ])
    # The physical susceptance is reconstructed from the solved terminal Q at
    # t=0. Mark that equipment assignment as authoritative so graphical helper
    # closure cannot replace it with a provisional controller iterate before
    # the SVC states reach the same operating point.
    wrapper_block.dynamic_model_contract.dgs_explicit_initialization_uids = set([
        bsvs.uid,
    ])
    wrapper_block.dynamic_model_contract.dgs_elmsvs_remote_voltage_var_uid = remote_voltage.uid
    wrapper_block.dynamic_model_contract.dgs_equipment_owned_signal_names = list([
        "u",
        "uremote",
        "ysvs",
        "qreact",
        "qcap",
        "qfixcap",
        "nxcap",
        "nfixcap",
    ])

    runtime_template: RmsModelTemplate = RmsModelTemplate(
        name=control_template.name,
    )
    runtime_template.tpe = DeviceType.ControllableShuntDevice
    runtime_template.block = wrapper_block
    return runtime_template
