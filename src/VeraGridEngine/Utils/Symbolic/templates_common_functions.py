# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
#
from typing import Any, List, Dict, NamedTuple
#
from VeraGridEngine.enumerations import VarPowerFlowReferenceType
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory

from VeraGridEngine.Utils.Symbolic.block import (Block,
                                                 Var,
                                                 Const,
                                                 DynamicConnectionIntentOrigin,
                                                 build_dynamic_connection_intent_record,
                                                 find_matching_dynamic_connection_intent,
                                                 normalize_dynamic_connection_intents,
                                                 rehash_block_tree_var_keyed_dicts)
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Utils.Symbolic.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.bus_emt_template import (BusEmtTemplate,
                                                           get_bus_emt_template,
                                                           get_bus_mask,
                                                           get_bus_emt_algebraic_vars)
from VeraGridEngine.Devices.Parents.dynamic_bus_parent import EmtBusConnectionSide, EmtBusConnectedModelRecord


def _find_block_by_uid(root_block: Block,
                       block_uid: int) -> Block | None:
    """
    Return one child block by UID from one symbolic block tree.

    :param root_block: Root block to inspect.
    :param block_uid: Block UID to locate.
    :return: Matching block or ``None``.
    """
    candidate_block: Block

    for candidate_block in root_block.get_all_blocks():
        if candidate_block.uid == block_uid:
            return candidate_block
        else:
            pass

    return None


def _find_root_var_by_ref(root_block: Block,
                          reference: VarPowerFlowReferenceType,
                          direction: str) -> Var | None:
    """
    Return one root interface variable by semantic reference and direction.

    :param root_block: Root block to inspect.
    :param reference: Desired root reference.
    :param direction: ``input`` or ``output``.
    :return: Matching variable or ``None``.
    """
    candidate_var: Var

    if direction == "input":
        for candidate_var in root_block.in_vars:
            if candidate_var.ref == reference:
                return candidate_var
            else:
                pass
    else:
        if direction == "output":
            for candidate_var in root_block.out_vars:
                if candidate_var.ref == reference:
                    return candidate_var
                else:
                    pass
        else:
            pass

    return None


def _is_branch_like_device(device: Any) -> bool:
    """
    Return whether one device uses two-terminal EMT branch semantics.

    :param device: Device to classify.
    :return: ``True`` when the device is branch-like.
    """
    branch_device_types: List[DeviceType] = list([DeviceType.BranchDevice,
                                                  DeviceType.LineDevice,
                                                  DeviceType.Transformer2WDevice,
                                                  DeviceType.Transformer3WDevice,
                                                  DeviceType.DCLineDevice,
                                                  DeviceType.HVDCLineDevice,
                                                  DeviceType.SwitchDevice,
                                                  DeviceType.SeriesReactanceDevice,
                                                  DeviceType.UpfcDevice,
                                                  DeviceType.VscDevice])

    if device.device_type in branch_device_types:
        return True
    else:
        return False


def _build_supported_root_intent_refs_for_device(device: Any) -> tuple[List[VarPowerFlowReferenceType], List[VarPowerFlowReferenceType]]:
    """
    Return the supported root input/output references for one EMT device.

    :param device: Device whose root EMT contract is being inspected.
    :return: ``(input_refs, output_refs)``.
    """
    input_refs: List[VarPowerFlowReferenceType] = list()
    output_refs: List[VarPowerFlowReferenceType] = list()

    if _is_branch_like_device(device):
        input_refs = list([
            VarPowerFlowReferenceType.Vf_dc,
            VarPowerFlowReferenceType.vf_N,
            VarPowerFlowReferenceType.vf_A,
            VarPowerFlowReferenceType.vf_B,
            VarPowerFlowReferenceType.vf_C,
            VarPowerFlowReferenceType.Vt_dc,
            VarPowerFlowReferenceType.vt_N,
            VarPowerFlowReferenceType.vt_A,
            VarPowerFlowReferenceType.vt_B,
            VarPowerFlowReferenceType.vt_C,
        ])
        output_refs = list([
            VarPowerFlowReferenceType.If_dc,
            VarPowerFlowReferenceType.if_N,
            VarPowerFlowReferenceType.if_A,
            VarPowerFlowReferenceType.if_B,
            VarPowerFlowReferenceType.if_C,
            VarPowerFlowReferenceType.It_dc,
            VarPowerFlowReferenceType.it_N,
            VarPowerFlowReferenceType.it_A,
            VarPowerFlowReferenceType.it_B,
            VarPowerFlowReferenceType.it_C,
        ])
    else:
        if device.bus.is_dc:
            input_refs = list([VarPowerFlowReferenceType.Vdc])
            output_refs = list([VarPowerFlowReferenceType.Idc])
        else:
            input_refs = list([
                VarPowerFlowReferenceType.v_N,
                VarPowerFlowReferenceType.v_A,
                VarPowerFlowReferenceType.v_B,
                VarPowerFlowReferenceType.v_C,
            ])
            output_refs = list([
                VarPowerFlowReferenceType.i_N,
                VarPowerFlowReferenceType.i_A,
                VarPowerFlowReferenceType.i_B,
                VarPowerFlowReferenceType.i_C,
            ])

    return input_refs, output_refs


def _prune_saved_root_io_vars_to_supported_contract(device: Any) -> None:
    """
    Remove saved root IO vars that are no longer part of the live device contract.

    The persisted saved model can retain stale branch-side root variables after a
    topology shrink because connection intent is meant to survive even when one
    endpoint becomes unavailable. The authoritative saved root contract,
    however, must only expose currently available root endpoints. Dormant intent
    stays in ``connection_intents`` and is rematerialized later when the root
    endpoint becomes valid again.

    :param device: Device whose saved root contract must be pruned.
    :return: None.
    """
    model: Block = device.emt_model
    supported_input_refs: List[VarPowerFlowReferenceType]
    supported_output_refs: List[VarPowerFlowReferenceType]
    pruned_in_vars: List[Var] = list()
    pruned_out_vars: List[Var] = list()
    io_var: Var

    if model.empty():
        return
    else:
        pass

    if _is_branch_like_device(device):
        supported_input_refs = list()
        supported_output_refs = list()
        from_input_refs: List[VarPowerFlowReferenceType]
        from_output_refs: List[VarPowerFlowReferenceType]
        to_input_refs: List[VarPowerFlowReferenceType]
        to_output_refs: List[VarPowerFlowReferenceType]
        from_input_refs, from_output_refs = _build_live_branch_side_root_contract_refs(device=device,
                                                                                        side=EmtBusConnectionSide.FROM)
        to_input_refs, to_output_refs = _build_live_branch_side_root_contract_refs(device=device,
                                                                                    side=EmtBusConnectionSide.TO)
        supported_input_refs.extend(from_input_refs)
        supported_input_refs.extend(to_input_refs)
        supported_output_refs.extend(from_output_refs)
        supported_output_refs.extend(to_output_refs)
    else:
        supported_input_refs, supported_output_refs = _build_live_root_contract_refs(device=device)

    for io_var in model.in_vars:
        if io_var.ref is None:
            pruned_in_vars.append(io_var)
        else:
            if io_var.ref in supported_input_refs:
                pruned_in_vars.append(io_var)
            else:
                pass

    for io_var in model.out_vars:
        if io_var.ref is None:
            pruned_out_vars.append(io_var)
        else:
            if io_var.ref in supported_output_refs:
                pruned_out_vars.append(io_var)
            else:
                pass

    model.in_vars = pruned_in_vars
    model.out_vars = pruned_out_vars


def _prune_saved_branch_root_contract_side(device: Any,
                                           side: EmtBusConnectionSide) -> None:
    """
    Prune one saved branch root contract side against its live bus shell.

    :param device: Branch-like device whose side contract must be pruned.
    :param side: Side to prune.
    :return: None.
    """
    model: Block = device.emt_model
    side_input_refs: List[VarPowerFlowReferenceType]
    side_output_refs: List[VarPowerFlowReferenceType]
    side_input_ref_set: set[VarPowerFlowReferenceType]
    side_output_ref_set: set[VarPowerFlowReferenceType]
    kept_in_vars: List[Var] = list()
    kept_out_vars: List[Var] = list()
    io_var: Var
    side_input_ref: VarPowerFlowReferenceType
    side_output_ref: VarPowerFlowReferenceType

    if model.empty():
        return
    else:
        pass

    side_input_refs, side_output_refs = _build_live_branch_side_root_contract_refs(device=device,
                                                                                    side=side)
    side_input_ref_set = set(side_input_refs)
    side_output_ref_set = set(side_output_refs)

    for io_var in model.in_vars:
        if io_var.ref is None:
            kept_in_vars.append(io_var)
        else:
            if side == EmtBusConnectionSide.FROM:
                if io_var.ref in list([VarPowerFlowReferenceType.vf_N,
                                       VarPowerFlowReferenceType.vf_A,
                                       VarPowerFlowReferenceType.vf_B,
                                       VarPowerFlowReferenceType.vf_C,
                                       VarPowerFlowReferenceType.Vf_dc]):
                    if io_var.ref in side_input_ref_set:
                        kept_in_vars.append(io_var)
                    else:
                        pass
                else:
                    kept_in_vars.append(io_var)
            else:
                if side == EmtBusConnectionSide.TO:
                    if io_var.ref in list([VarPowerFlowReferenceType.vt_N,
                                           VarPowerFlowReferenceType.vt_A,
                                           VarPowerFlowReferenceType.vt_B,
                                           VarPowerFlowReferenceType.vt_C,
                                           VarPowerFlowReferenceType.Vt_dc]):
                        if io_var.ref in side_input_ref_set:
                            kept_in_vars.append(io_var)
                        else:
                            pass
                    else:
                        kept_in_vars.append(io_var)
                else:
                    kept_in_vars.append(io_var)

    for io_var in model.out_vars:
        if io_var.ref is None:
            kept_out_vars.append(io_var)
        else:
            if side == EmtBusConnectionSide.FROM:
                if io_var.ref in list([VarPowerFlowReferenceType.if_N,
                                       VarPowerFlowReferenceType.if_A,
                                       VarPowerFlowReferenceType.if_B,
                                       VarPowerFlowReferenceType.if_C,
                                       VarPowerFlowReferenceType.If_dc]):
                    if io_var.ref in side_output_ref_set:
                        kept_out_vars.append(io_var)
                    else:
                        pass
                else:
                    kept_out_vars.append(io_var)
            else:
                if side == EmtBusConnectionSide.TO:
                    if io_var.ref in list([VarPowerFlowReferenceType.it_N,
                                           VarPowerFlowReferenceType.it_A,
                                           VarPowerFlowReferenceType.it_B,
                                           VarPowerFlowReferenceType.it_C,
                                           VarPowerFlowReferenceType.It_dc]):
                        if io_var.ref in side_output_ref_set:
                            kept_out_vars.append(io_var)
                        else:
                            pass
                    else:
                        kept_out_vars.append(io_var)
                else:
                    kept_out_vars.append(io_var)

    model.in_vars = kept_in_vars
    model.out_vars = kept_out_vars

    for side_input_ref in list([VarPowerFlowReferenceType.vf_N,
                                VarPowerFlowReferenceType.vf_A,
                                VarPowerFlowReferenceType.vf_B,
                                VarPowerFlowReferenceType.vf_C,
                                VarPowerFlowReferenceType.Vf_dc]) if side == EmtBusConnectionSide.FROM else list([
                                    VarPowerFlowReferenceType.vt_N,
                                    VarPowerFlowReferenceType.vt_A,
                                    VarPowerFlowReferenceType.vt_B,
                                    VarPowerFlowReferenceType.vt_C,
                                    VarPowerFlowReferenceType.Vt_dc,
                                ]):
        if side_input_ref in side_input_ref_set:
            pass
        else:
            model.external_mapping[side_input_ref] = None

    for side_output_ref in list([VarPowerFlowReferenceType.if_N,
                                 VarPowerFlowReferenceType.if_A,
                                 VarPowerFlowReferenceType.if_B,
                                 VarPowerFlowReferenceType.if_C,
                                 VarPowerFlowReferenceType.If_dc]) if side == EmtBusConnectionSide.FROM else list([
                                     VarPowerFlowReferenceType.it_N,
                                     VarPowerFlowReferenceType.it_A,
                                     VarPowerFlowReferenceType.it_B,
                                     VarPowerFlowReferenceType.it_C,
                                     VarPowerFlowReferenceType.It_dc,
                                 ]):
        if side_output_ref in side_output_ref_set:
            pass
        else:
            model.external_mapping[side_output_ref] = None


def _build_live_root_contract_refs(device: Any) -> tuple[List[VarPowerFlowReferenceType], List[VarPowerFlowReferenceType]]:
    """
    Build the exact currently available root refs for one live device contract.

    :param device: Device whose live root contract must be derived.
    :return: ``(input_refs, output_refs)``.
    """
    input_refs: List[VarPowerFlowReferenceType] = list()
    output_refs: List[VarPowerFlowReferenceType] = list()
    available_bus_ref: VarPowerFlowReferenceType
    available_bus_var: Var | None
    from_voltage_map: dict[VarPowerFlowReferenceType, VarPowerFlowReferenceType] = dict([
        (VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.vf_N),
        (VarPowerFlowReferenceType.v_A, VarPowerFlowReferenceType.vf_A),
        (VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.vf_B),
        (VarPowerFlowReferenceType.v_C, VarPowerFlowReferenceType.vf_C),
        (VarPowerFlowReferenceType.Vdc, VarPowerFlowReferenceType.Vf_dc),
    ])
    to_voltage_map: dict[VarPowerFlowReferenceType, VarPowerFlowReferenceType] = dict([
        (VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.vt_N),
        (VarPowerFlowReferenceType.v_A, VarPowerFlowReferenceType.vt_A),
        (VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.vt_B),
        (VarPowerFlowReferenceType.v_C, VarPowerFlowReferenceType.vt_C),
        (VarPowerFlowReferenceType.Vdc, VarPowerFlowReferenceType.Vt_dc),
    ])
    from_current_map: dict[VarPowerFlowReferenceType, VarPowerFlowReferenceType] = dict([
        (VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.if_N),
        (VarPowerFlowReferenceType.v_A, VarPowerFlowReferenceType.if_A),
        (VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.if_B),
        (VarPowerFlowReferenceType.v_C, VarPowerFlowReferenceType.if_C),
        (VarPowerFlowReferenceType.Vdc, VarPowerFlowReferenceType.If_dc),
    ])
    to_current_map: dict[VarPowerFlowReferenceType, VarPowerFlowReferenceType] = dict([
        (VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.it_N),
        (VarPowerFlowReferenceType.v_A, VarPowerFlowReferenceType.it_A),
        (VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.it_B),
        (VarPowerFlowReferenceType.v_C, VarPowerFlowReferenceType.it_C),
        (VarPowerFlowReferenceType.Vdc, VarPowerFlowReferenceType.It_dc),
    ])

    if _is_branch_like_device(device):
        for available_bus_ref, available_bus_var in device.bus_from.emt_model.external_mapping.items():
            if available_bus_var is None:
                pass
            else:
                if available_bus_ref in from_voltage_map:
                    input_refs.append(from_voltage_map[available_bus_ref])
                    output_refs.append(from_current_map[available_bus_ref])
                else:
                    pass

        for available_bus_ref, available_bus_var in device.bus_to.emt_model.external_mapping.items():
            if available_bus_var is None:
                pass
            else:
                if available_bus_ref in to_voltage_map:
                    input_refs.append(to_voltage_map[available_bus_ref])
                    output_refs.append(to_current_map[available_bus_ref])
                else:
                    pass
    else:
        if device.bus.is_dc:
            if device.bus.emt_model.external_mapping.get(VarPowerFlowReferenceType.Vdc, None) is not None:
                input_refs.append(VarPowerFlowReferenceType.Vdc)
                output_refs.append(VarPowerFlowReferenceType.Idc)
            else:
                pass
        else:
            injection_current_map: dict[VarPowerFlowReferenceType, VarPowerFlowReferenceType] = dict([
                (VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.i_N),
                (VarPowerFlowReferenceType.v_A, VarPowerFlowReferenceType.i_A),
                (VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.i_B),
                (VarPowerFlowReferenceType.v_C, VarPowerFlowReferenceType.i_C),
            ])
            injection_voltage_ref: VarPowerFlowReferenceType

            for injection_voltage_ref in injection_current_map:
                if device.bus.emt_model.external_mapping.get(injection_voltage_ref, None) is not None:
                    input_refs.append(injection_voltage_ref)
                    output_refs.append(injection_current_map[injection_voltage_ref])
                else:
                    pass

    return input_refs, output_refs


def _build_live_branch_side_root_contract_refs(device: Any,
                                               side: EmtBusConnectionSide) -> tuple[List[VarPowerFlowReferenceType], List[VarPowerFlowReferenceType]]:
    """
    Build the exact currently available root refs for one branch side.

    :param device: Branch-like device whose side contract must be derived.
    :param side: Branch side to inspect.
    :return: ``(input_refs, output_refs)``.
    """
    input_refs: List[VarPowerFlowReferenceType] = list()
    output_refs: List[VarPowerFlowReferenceType] = list()
    available_bus_ref: VarPowerFlowReferenceType
    available_bus_var: Var | None
    voltage_map: Dict[VarPowerFlowReferenceType, VarPowerFlowReferenceType]
    current_map: Dict[VarPowerFlowReferenceType, VarPowerFlowReferenceType]
    bus_model: Block

    if side == EmtBusConnectionSide.FROM:
        bus_model = device.bus_from.emt_model
        voltage_map = dict([
            (VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.vf_N),
            (VarPowerFlowReferenceType.v_A, VarPowerFlowReferenceType.vf_A),
            (VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.vf_B),
            (VarPowerFlowReferenceType.v_C, VarPowerFlowReferenceType.vf_C),
            (VarPowerFlowReferenceType.Vdc, VarPowerFlowReferenceType.Vf_dc),
        ])
        current_map = dict([
            (VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.if_N),
            (VarPowerFlowReferenceType.v_A, VarPowerFlowReferenceType.if_A),
            (VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.if_B),
            (VarPowerFlowReferenceType.v_C, VarPowerFlowReferenceType.if_C),
            (VarPowerFlowReferenceType.Vdc, VarPowerFlowReferenceType.If_dc),
        ])
    else:
        if side == EmtBusConnectionSide.TO:
            bus_model = device.bus_to.emt_model
            voltage_map = dict([
                (VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.vt_N),
                (VarPowerFlowReferenceType.v_A, VarPowerFlowReferenceType.vt_A),
                (VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.vt_B),
                (VarPowerFlowReferenceType.v_C, VarPowerFlowReferenceType.vt_C),
                (VarPowerFlowReferenceType.Vdc, VarPowerFlowReferenceType.Vt_dc),
            ])
            current_map = dict([
                (VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.it_N),
                (VarPowerFlowReferenceType.v_A, VarPowerFlowReferenceType.it_A),
                (VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.it_B),
                (VarPowerFlowReferenceType.v_C, VarPowerFlowReferenceType.it_C),
                (VarPowerFlowReferenceType.Vdc, VarPowerFlowReferenceType.It_dc),
            ])
        else:
            return input_refs, output_refs

    for available_bus_ref, available_bus_var in bus_model.external_mapping.items():
        if available_bus_var is None:
            pass
        else:
            if available_bus_ref in voltage_map:
                input_refs.append(voltage_map[available_bus_ref])
                output_refs.append(current_map[available_bus_ref])
            else:
                pass

    return input_refs, output_refs


def _ensure_saved_root_io_vars_for_live_contract(device: Any,
                                                 var_factory: VarFactory) -> None:
    """
    Recreate missing saved root IO vars required by the current live contract.

    :param device: Device whose saved root contract must be completed.
    :param var_factory: Shared variable factory used to create replacement vars.
    :return: None.
    """
    model: Block = device.emt_model
    input_refs: List[VarPowerFlowReferenceType]
    output_refs: List[VarPowerFlowReferenceType]
    existing_input_refs: set[VarPowerFlowReferenceType] = set()
    existing_output_refs: set[VarPowerFlowReferenceType] = set()
    io_var: Var
    root_ref: VarPowerFlowReferenceType
    new_var: Var

    if model.empty():
        return
    else:
        pass

    if _is_branch_like_device(device):
        input_refs = list()
        output_refs = list()
        from_input_refs: List[VarPowerFlowReferenceType]
        from_output_refs: List[VarPowerFlowReferenceType]
        to_input_refs: List[VarPowerFlowReferenceType]
        to_output_refs: List[VarPowerFlowReferenceType]
        from_input_refs, from_output_refs = _build_live_branch_side_root_contract_refs(device=device,
                                                                                        side=EmtBusConnectionSide.FROM)
        to_input_refs, to_output_refs = _build_live_branch_side_root_contract_refs(device=device,
                                                                                    side=EmtBusConnectionSide.TO)
        input_refs.extend(from_input_refs)
        input_refs.extend(to_input_refs)
        output_refs.extend(from_output_refs)
        output_refs.extend(to_output_refs)
    else:
        input_refs, output_refs = _build_live_root_contract_refs(device=device)

    for io_var in model.in_vars:
        if io_var.ref is None:
            pass
        else:
            existing_input_refs.add(io_var.ref)

    for io_var in model.out_vars:
        if io_var.ref is None:
            pass
        else:
            existing_output_refs.add(io_var.ref)

    for root_ref in input_refs:
        if root_ref in existing_input_refs:
            pass
        else:
            new_var = var_factory.add_var(name=root_ref.value,
                                          reference=root_ref)
            model.in_vars.append(new_var)
            model.external_mapping[root_ref] = new_var

    for root_ref in output_refs:
        if root_ref in existing_output_refs:
            pass
        else:
            new_var = var_factory.add_var(name=root_ref.value,
                                          reference=root_ref)
            model.out_vars.append(new_var)
            model.external_mapping[root_ref] = new_var


def _ensure_saved_branch_root_contract_side(device: Any,
                                            side: EmtBusConnectionSide,
                                            var_factory: VarFactory) -> None:
    """
    Recreate missing saved root IO vars for one branch side only.

    :param device: Branch-like device whose side contract must be completed.
    :param side: Side to complete.
    :param var_factory: Shared variable factory.
    :return: None.
    """
    model: Block = device.emt_model
    input_refs: List[VarPowerFlowReferenceType]
    output_refs: List[VarPowerFlowReferenceType]
    existing_input_refs: set[VarPowerFlowReferenceType] = set()
    existing_output_refs: set[VarPowerFlowReferenceType] = set()
    io_var: Var
    root_ref: VarPowerFlowReferenceType
    new_var: Var

    if model.empty():
        return
    else:
        pass

    input_refs, output_refs = _build_live_branch_side_root_contract_refs(device=device,
                                                                         side=side)

    if side == EmtBusConnectionSide.TO:
        if VarPowerFlowReferenceType.vt_C in input_refs:
            pass
        else:
            pass

    for io_var in model.in_vars:
        if io_var.ref is None:
            pass
        else:
            existing_input_refs.add(io_var.ref)

    for io_var in model.out_vars:
        if io_var.ref is None:
            pass
        else:
            existing_output_refs.add(io_var.ref)

    for root_ref in input_refs:
        if root_ref in existing_input_refs:
            pass
        else:
            new_var = var_factory.add_var(name=root_ref.value,
                                          reference=root_ref)
            model.in_vars.append(new_var)
            model.external_mapping[root_ref] = new_var


def _rebuild_saved_branch_root_contract_from_live_sides(device: Any,
                                                        var_factory: VarFactory) -> None:
    """
    Rebuild the saved branch root IO contract directly from the current live side contracts.

    :param device: Branch-like device whose saved root contract must be rebuilt.
    :param var_factory: Shared variable factory.
    :return: None.
    """
    model: Block = device.emt_model
    from_input_refs: List[VarPowerFlowReferenceType]
    from_output_refs: List[VarPowerFlowReferenceType]
    to_input_refs: List[VarPowerFlowReferenceType]
    to_output_refs: List[VarPowerFlowReferenceType]
    ordered_input_refs: List[VarPowerFlowReferenceType] = list()
    ordered_output_refs: List[VarPowerFlowReferenceType] = list()
    rebuilt_in_vars: List[Var] = list()
    rebuilt_out_vars: List[Var] = list()
    existing_input_by_ref: Dict[VarPowerFlowReferenceType, Var] = dict()
    existing_output_by_ref: Dict[VarPowerFlowReferenceType, Var] = dict()
    io_var: Var
    root_ref: VarPowerFlowReferenceType
    new_var: Var

    if model.empty():
        return
    else:
        pass

    from_input_refs, from_output_refs = _build_live_branch_side_root_contract_refs(device=device,
                                                                                    side=EmtBusConnectionSide.FROM)
    to_input_refs, to_output_refs = _build_live_branch_side_root_contract_refs(device=device,
                                                                                side=EmtBusConnectionSide.TO)
    ordered_input_refs.extend(from_input_refs)
    ordered_input_refs.extend(to_input_refs)
    ordered_output_refs.extend(from_output_refs)
    ordered_output_refs.extend(to_output_refs)

    for io_var in model.in_vars:
        if io_var.ref is None:
            pass
        elif io_var.ref in existing_input_by_ref:
            pass
        else:
            existing_input_by_ref[io_var.ref] = io_var

    for io_var in model.out_vars:
        if io_var.ref is None:
            pass
        elif io_var.ref in existing_output_by_ref:
            pass
        else:
            existing_output_by_ref[io_var.ref] = io_var

    for root_ref in ordered_input_refs:
        if root_ref in existing_input_by_ref:
            rebuilt_in_vars.append(existing_input_by_ref[root_ref])
        else:
            new_var = var_factory.add_var(name=root_ref.value,
                                          reference=root_ref)
            rebuilt_in_vars.append(new_var)

    for root_ref in ordered_output_refs:
        if root_ref in existing_output_by_ref:
            existing_output_by_ref[root_ref]._network_conn = True
            rebuilt_out_vars.append(existing_output_by_ref[root_ref])
        else:
            new_var = var_factory.add_var(name=root_ref.value,
                                          reference=root_ref,
                                          network_conn=True)
            rebuilt_out_vars.append(new_var)

    model.in_vars = rebuilt_in_vars
    model.out_vars = rebuilt_out_vars
    _normalize_saved_branch_root_contract_from_live_sides(device=device)


def _clear_saved_branch_root_external_mapping(device: Any) -> None:
    """
    Clear every branch root external-mapping entry before rebuilding the live contract.

    :param device: Branch-like device whose saved root mapping must be cleared.
    :return: None.
    """
    model: Block = device.emt_model
    mapping_ref: VarPowerFlowReferenceType

    if model.empty():
        return
    else:
        pass

    for mapping_ref in list([
        VarPowerFlowReferenceType.vf_N,
        VarPowerFlowReferenceType.vf_A,
        VarPowerFlowReferenceType.vf_B,
        VarPowerFlowReferenceType.vf_C,
        VarPowerFlowReferenceType.Vf_dc,
        VarPowerFlowReferenceType.vt_N,
        VarPowerFlowReferenceType.vt_A,
        VarPowerFlowReferenceType.vt_B,
        VarPowerFlowReferenceType.vt_C,
        VarPowerFlowReferenceType.Vt_dc,
        VarPowerFlowReferenceType.if_N,
        VarPowerFlowReferenceType.if_A,
        VarPowerFlowReferenceType.if_B,
        VarPowerFlowReferenceType.if_C,
        VarPowerFlowReferenceType.If_dc,
        VarPowerFlowReferenceType.it_N,
        VarPowerFlowReferenceType.it_A,
        VarPowerFlowReferenceType.it_B,
        VarPowerFlowReferenceType.it_C,
        VarPowerFlowReferenceType.It_dc,
    ]):
        model.external_mapping[mapping_ref] = None


def _prune_saved_root_external_mapping_to_live_contract(device: Any) -> None:
    """
    Clear saved root external-mapping entries that are not in the live contract.

    Per-terminal topology changes can leave one saved external-mapping entry
    pointing to one stale root var even after the root IO lists have been pruned.
    Validation reads ``external_mapping`` directly, so the mapping must follow
    the same live-contract pruning rule as ``in_vars`` and ``out_vars``.

    :param device: Device whose saved root external mapping must be pruned.
    :return: None.
    """
    model: Block = device.emt_model
    live_input_refs: List[VarPowerFlowReferenceType]
    live_output_refs: List[VarPowerFlowReferenceType]
    live_refs: set[VarPowerFlowReferenceType] = set()
    root_interface_refs: set[VarPowerFlowReferenceType]
    reference: VarPowerFlowReferenceType

    if model.empty():
        return
    else:
        pass

    if _is_branch_like_device(device):
        live_input_refs = list()
        live_output_refs = list()
        from_input_refs: List[VarPowerFlowReferenceType]
        from_output_refs: List[VarPowerFlowReferenceType]
        to_input_refs: List[VarPowerFlowReferenceType]
        to_output_refs: List[VarPowerFlowReferenceType]
        from_input_refs, from_output_refs = _build_live_branch_side_root_contract_refs(device=device,
                                                                                        side=EmtBusConnectionSide.FROM)
        to_input_refs, to_output_refs = _build_live_branch_side_root_contract_refs(device=device,
                                                                                    side=EmtBusConnectionSide.TO)
        live_input_refs.extend(from_input_refs)
        live_input_refs.extend(to_input_refs)
        live_output_refs.extend(from_output_refs)
        live_output_refs.extend(to_output_refs)
    else:
        live_input_refs, live_output_refs = _build_live_root_contract_refs(device=device)

    for reference in live_input_refs:
        live_refs.add(reference)

    for reference in live_output_refs:
        live_refs.add(reference)

    if _is_branch_like_device(device):
        supported_input_refs: List[VarPowerFlowReferenceType]
        supported_output_refs: List[VarPowerFlowReferenceType]
        supported_input_refs, supported_output_refs = _build_supported_root_intent_refs_for_device(device=device)
        root_interface_refs = set(supported_input_refs + supported_output_refs)
    else:
        root_interface_refs = set([
            VarPowerFlowReferenceType.Vdc,
            VarPowerFlowReferenceType.Idc,
            VarPowerFlowReferenceType.v_N,
            VarPowerFlowReferenceType.v_A,
            VarPowerFlowReferenceType.v_B,
            VarPowerFlowReferenceType.v_C,
            VarPowerFlowReferenceType.i_N,
            VarPowerFlowReferenceType.i_A,
            VarPowerFlowReferenceType.i_B,
            VarPowerFlowReferenceType.i_C,
        ])

    for reference in list(model.external_mapping.keys()):
        if reference not in root_interface_refs:
            pass
        else:
            if reference in live_refs:
                pass
            else:
                model.external_mapping[reference] = None


def _normalize_saved_branch_root_contract_from_live_sides(device: Any) -> None:
    """
    Rebuild one saved branch external mapping from currently materialized side refs.

    The generic branch normalization path can clear untouched-side mappings when
    one side has changed topology and the root IO lists are in transition. This
    helper rebuilds the saved branch external mapping directly from the current
    materialized branch root IO vars per side, preserving whichever side remains
    valid while still clearing refs that truly no longer exist.

    :param device: Branch-like device whose saved root contract must be normalized.
    :return: None.
    """
    model: Block = device.emt_model
    input_ref: VarPowerFlowReferenceType
    output_ref: VarPowerFlowReferenceType
    input_var: Var | None
    output_var: Var | None
    kept_in_vars: List[Var] = list()
    kept_out_vars: List[Var] = list()
    live_input_refs: set[VarPowerFlowReferenceType] = set()
    live_output_refs: set[VarPowerFlowReferenceType] = set()
    io_var: Var

    if model.empty():
        return
    else:
        pass

    for input_ref in list([
        VarPowerFlowReferenceType.vf_N,
        VarPowerFlowReferenceType.vf_A,
        VarPowerFlowReferenceType.vf_B,
        VarPowerFlowReferenceType.vf_C,
        VarPowerFlowReferenceType.Vf_dc,
        VarPowerFlowReferenceType.vt_N,
        VarPowerFlowReferenceType.vt_A,
        VarPowerFlowReferenceType.vt_B,
        VarPowerFlowReferenceType.vt_C,
        VarPowerFlowReferenceType.Vt_dc,
    ]):
        input_var = _find_root_var_by_ref(root_block=model,
                                          reference=input_ref,
                                          direction="input")
        if input_var is None:
            pass
        else:
            live_input_refs.add(input_ref)

    for output_ref in list([
        VarPowerFlowReferenceType.if_N,
        VarPowerFlowReferenceType.if_A,
        VarPowerFlowReferenceType.if_B,
        VarPowerFlowReferenceType.if_C,
        VarPowerFlowReferenceType.If_dc,
        VarPowerFlowReferenceType.it_N,
        VarPowerFlowReferenceType.it_A,
        VarPowerFlowReferenceType.it_B,
        VarPowerFlowReferenceType.it_C,
        VarPowerFlowReferenceType.It_dc,
    ]):
        output_var = _find_root_var_by_ref(root_block=model,
                                           reference=output_ref,
                                           direction="output")
        if output_var is None:
            pass
        else:
            live_output_refs.add(output_ref)

    for io_var in model.in_vars:
        if io_var.ref is None:
            kept_in_vars.append(io_var)
        else:
            if io_var.ref in live_input_refs:
                kept_in_vars.append(io_var)
            else:
                pass

    for io_var in model.out_vars:
        if io_var.ref is None:
            kept_out_vars.append(io_var)
        else:
            if io_var.ref in live_output_refs:
                kept_out_vars.append(io_var)
            else:
                pass

    model.in_vars = kept_in_vars
    model.out_vars = kept_out_vars

    for input_ref in list([
        VarPowerFlowReferenceType.vf_N,
        VarPowerFlowReferenceType.vf_A,
        VarPowerFlowReferenceType.vf_B,
        VarPowerFlowReferenceType.vf_C,
        VarPowerFlowReferenceType.Vf_dc,
        VarPowerFlowReferenceType.vt_N,
        VarPowerFlowReferenceType.vt_A,
        VarPowerFlowReferenceType.vt_B,
        VarPowerFlowReferenceType.vt_C,
        VarPowerFlowReferenceType.Vt_dc,
    ]):
        input_var = _find_root_var_by_ref(root_block=model,
                                          reference=input_ref,
                                          direction="input")
        if input_var is None:
            model.external_mapping[input_ref] = None
        else:
            model.external_mapping[input_ref] = input_var

    for output_ref in list([
        VarPowerFlowReferenceType.if_N,
        VarPowerFlowReferenceType.if_A,
        VarPowerFlowReferenceType.if_B,
        VarPowerFlowReferenceType.if_C,
        VarPowerFlowReferenceType.If_dc,
        VarPowerFlowReferenceType.it_N,
        VarPowerFlowReferenceType.it_A,
        VarPowerFlowReferenceType.it_B,
        VarPowerFlowReferenceType.it_C,
        VarPowerFlowReferenceType.It_dc,
    ]):
        output_var = _find_root_var_by_ref(root_block=model,
                                           reference=output_ref,
                                           direction="output")
        if output_var is None:
            model.external_mapping[output_ref] = None
        else:
            model.external_mapping[output_ref] = output_var


def _connection_exists_in_var_factory(var_factory: VarFactory,
                                      source_var: Var,
                                      target_var: Var) -> bool:
    """
    Return whether one directed symbolic connection already exists.

    :param var_factory: Shared variable factory.
    :param source_var: Source variable.
    :param target_var: Target variable.
    :return: ``True`` when the connection already exists.
    """
    existing_connection: Any

    for existing_connection in var_factory.get_connections_dict().get(source_var.non_mutable_uid, list()):
        if existing_connection.non_mutable_uid == target_var.non_mutable_uid:
            return True
        else:
            pass

    return False


def seed_template_derived_dynamic_connection_intents(device: Any) -> None:
    """
    Record template-derived root-interface intents for one template-backed EMT model.

    :param device: Device whose current EMT model originated from a template.
    :return: None.
    """
    model: Block = device.emt_model
    child_block: Block
    input_index: int
    output_index: int
    input_var: Var
    output_var: Var
    existing_intent: Dict[str, Any] | None
    new_intent: Dict[str, Any]
    supported_input_refs: List[VarPowerFlowReferenceType]
    supported_output_refs: List[VarPowerFlowReferenceType]

    if model.empty():
        return
    else:
        pass

    if device.emt_template is None:
        return
    else:
        pass

    normalize_dynamic_connection_intents(model)
    supported_input_refs, supported_output_refs = _build_supported_root_intent_refs_for_device(device)
    for child_block in model.children:
        if len(child_block.algebraic_vars) > 0 or len(child_block.state_vars) > 0 or len(child_block.diff_vars) > 0:
            for input_index, input_var in enumerate(child_block.in_vars):
                if input_var.ref is None:
                    pass
                elif input_var.ref not in supported_input_refs:
                    pass
                else:
                    existing_intent = find_matching_dynamic_connection_intent(block=model,
                                                                             origin=DynamicConnectionIntentOrigin.TEMPLATE_DERIVED,
                                                                             root_ref_value=input_var.ref.value,
                                                                             root_direction="input",
                                                                             internal_block_uid=child_block.uid,
                                                                             internal_port_direction="input",
                                                                             internal_port_index=input_index)

                    if existing_intent is None:
                        new_intent = build_dynamic_connection_intent_record(
                            origin=DynamicConnectionIntentOrigin.TEMPLATE_DERIVED,
                            root_ref=input_var.ref,
                            root_direction="input",
                            internal_block_uid=child_block.uid,
                            internal_port_direction="input",
                            internal_port_index=input_index,
                            suppressed=False,
                        )
                        model.connection_intents.append(new_intent)
                    else:
                        pass

            for output_index, output_var in enumerate(child_block.out_vars):
                if output_var.ref is None:
                    pass
                elif output_var.ref not in supported_output_refs:
                    pass
                else:
                    existing_intent = find_matching_dynamic_connection_intent(block=model,
                                                                             origin=DynamicConnectionIntentOrigin.TEMPLATE_DERIVED,
                                                                             root_ref_value=output_var.ref.value,
                                                                             root_direction="output",
                                                                             internal_block_uid=child_block.uid,
                                                                             internal_port_direction="output",
                                                                             internal_port_index=output_index)

                    if existing_intent is None:
                        new_intent = build_dynamic_connection_intent_record(
                            origin=DynamicConnectionIntentOrigin.TEMPLATE_DERIVED,
                            root_ref=output_var.ref,
                            root_direction="output",
                            internal_block_uid=child_block.uid,
                            internal_port_direction="output",
                            internal_port_index=output_index,
                            suppressed=False,
                        )
                        model.connection_intents.append(new_intent)
                    else:
                        pass
        else:
            pass

    normalize_dynamic_connection_intents(model)


def seed_branch_template_derived_dynamic_connection_intents(device: Any) -> None:
    """
    Record template-derived root-interface intents for one branch-like EMT template.

    :param device: Branch-like device whose EMT model originated from a template.
    :return: None.
    """
    if not _is_branch_like_device(device):
        return
    else:
        pass

    seed_template_derived_dynamic_connection_intents(device=device)


def rematerialize_saved_dynamic_connection_intents(device: Any,
                                                   var_factory: VarFactory) -> None:
    """
    Restore active symbolic root-interface connections from persisted intent records.

    :param device: Device whose saved model must be rematerialized.
    :param var_factory: Shared variable factory.
    :return: None.
    """
    model: Block = device.emt_model
    entry: Dict[str, Any]
    root_ref_value: str | None
    root_direction: str | None
    internal_block_uid: int | None
    internal_port_direction: str | None
    internal_port_index: int | None
    root_reference: VarPowerFlowReferenceType
    root_var: Var | None
    internal_block: Block | None
    internal_var: Var | None
    supported_input_refs: List[VarPowerFlowReferenceType]
    supported_output_refs: List[VarPowerFlowReferenceType]

    if model.empty():
        return
    else:
        pass

    normalize_dynamic_connection_intents(model)
    supported_input_refs, supported_output_refs = _build_supported_root_intent_refs_for_device(device)

    for entry in model.connection_intents:
        if not isinstance(entry, dict):
            pass
        elif entry.get("suppressed", False):
            pass
        else:
            root_ref_value = entry.get("root_ref", None)
            root_direction = entry.get("root_direction", None)
            internal_block_uid = entry.get("internal_block_uid", None)
            internal_port_direction = entry.get("internal_port_direction", None)
            internal_port_index = entry.get("internal_port_index", None)

            if root_ref_value is None or root_direction is None or internal_block_uid is None or internal_port_direction is None or internal_port_index is None:
                pass
            else:
                root_reference = VarPowerFlowReferenceType(root_ref_value)
                if root_direction == "input":
                    if root_reference in supported_input_refs:
                        pass
                    else:
                        root_reference = None  # type: ignore[assignment]
                else:
                    if root_direction == "output":
                        if root_reference in supported_output_refs:
                            pass
                        else:
                            root_reference = None  # type: ignore[assignment]
                    else:
                        root_reference = None  # type: ignore[assignment]

                if root_reference is None:
                    pass
                else:
                    root_var = _find_root_var_by_ref(model, root_reference, root_direction)
                    internal_block = _find_block_by_uid(model, internal_block_uid)

                    if root_var is None or internal_block is None:
                        pass
                    else:
                        internal_var = None
                        if internal_port_direction == "input":
                            if 0 <= internal_port_index < len(internal_block.in_vars):
                                internal_var = internal_block.in_vars[internal_port_index]
                            else:
                                pass
                        else:
                            if internal_port_direction == "output":
                                if 0 <= internal_port_index < len(internal_block.out_vars):
                                    internal_var = internal_block.out_vars[internal_port_index]
                                else:
                                    pass
                            else:
                                pass

                        if internal_var is None:
                            pass
                        else:
                            if root_direction == "input" and internal_port_direction == "input":
                                if not _connection_exists_in_var_factory(var_factory=var_factory,
                                                                         source_var=root_var,
                                                                         target_var=internal_var):
                                    var_factory.add_connections([internal_var], [root_var])
                                else:
                                    pass
                            elif root_direction == "output" and internal_port_direction == "output":
                                if not _connection_exists_in_var_factory(var_factory=var_factory,
                                                                         source_var=internal_var,
                                                                         target_var=root_var):
                                    var_factory.add_connections([root_var], [internal_var])
                                else:
                                    pass
                            else:
                                pass


def reconcile_saved_emt_model_against_current_topology(device: Any,
                                                       grid: Any,
                                                       var_factory: VarFactory) -> None:
    """
    Synchronize one saved EMT device model against the current static topology.

    :param device: Device whose EMT model must match the current grid topology.
    :param grid: Owning circuit used to derive bus-shell topology.
    :param var_factory: Shared symbolic variable factory.
    :return: None.
    """
    if device.emt_model.empty():
        return
    else:
        pass

    if _is_branch_like_device(device):
        # Empty and previously grid-built shells follow the current static
        # topology. A non-empty replacement shell remains authoritative for the
        # pass, which preserves explicit editor/test topology substitutions.
        from_shell_requires_grid_sync: bool = (device.bus_from.emt_model.empty()
                                                or device.bus_from.is_emt_model_grid_synchronized())
        if from_shell_requires_grid_sync:
            synchronize_emt_bus_shell_with_grid(bus=device.bus_from,
                                                grid=grid,
                                                var_factory=var_factory,
                                                device_to_skip=device)
        else:
            pass

        to_shell_requires_grid_sync: bool = (device.bus_to.emt_model.empty()
                                              or device.bus_to.is_emt_model_grid_synchronized())
        if to_shell_requires_grid_sync:
            synchronize_emt_bus_shell_with_grid(bus=device.bus_to,
                                                grid=grid,
                                                var_factory=var_factory,
                                                device_to_skip=device)
        else:
            pass
        _clear_saved_branch_root_external_mapping(device=device)
        _rebuild_saved_branch_root_contract_from_live_sides(device=device,
                                                            var_factory=var_factory)
        seed_template_derived_dynamic_connection_intents(device=device)
        rematerialize_saved_dynamic_connection_intents(device=device,
                                                       var_factory=var_factory)
        attach_emt_model_to_buses(device=device,
                                  model=device.emt_model,
                                  var_factory=var_factory)
        _normalize_saved_branch_root_contract_from_live_sides(device=device)
        synchronize_saved_emt_root_contract_from_bus(device=device)
    else:
        synchronize_emt_bus_shell_with_grid(bus=device.bus,
                                            grid=grid,
                                            var_factory=var_factory)

        _prune_saved_root_io_vars_to_supported_contract(device=device)
        _prune_saved_root_external_mapping_to_live_contract(device=device)
        _ensure_saved_root_io_vars_for_live_contract(device=device,
                                                     var_factory=var_factory)
        seed_template_derived_dynamic_connection_intents(device=device)
        attach_emt_model_to_buses(device=device,
                                  model=device.emt_model,
                                  var_factory=var_factory)

    if _is_branch_like_device(device):
        pass
    else:
        _prune_saved_root_io_vars_to_supported_contract(device=device)
        _prune_saved_root_external_mapping_to_live_contract(device=device)
        _ensure_saved_root_io_vars_for_live_contract(device=device,
                                                     var_factory=var_factory)
        seed_template_derived_dynamic_connection_intents(device=device)
        attach_emt_model_to_buses(device=device,
                                  model=device.emt_model,
                                  var_factory=var_factory)


class EmtBusShellSyncResult(NamedTuple):
    """
    Describe the outcome of one EMT bus-shell synchronization pass.

    :param changed: Whether the bus shell was replaced.
    :param old_mask: Previously detected AC phase mask, or ``None`` for DC or malformed shells.
    :param new_mask: Authoritative AC phase mask, or ``None`` for DC buses.
    :param voltage_vars: Current authoritative bus-voltage vars indexed by reference.
    """

    changed: bool
    old_mask: List[bool] | None
    new_mask: List[bool] | None
    voltage_vars: Dict[VarPowerFlowReferenceType, Var | None]


def _build_bus_shell_voltage_mapping(bus: Any) -> Dict[VarPowerFlowReferenceType, Var | None]:
    """
    Build the authoritative bus-voltage mapping for one live EMT shell.

    :param bus: Bus whose EMT shell is being inspected.
    :return: Voltage mapping keyed by bus-side power-flow reference.
    """
    voltage_mapping: Dict[VarPowerFlowReferenceType, Var | None] = dict()

    if bus.is_dc:
        voltage_mapping[VarPowerFlowReferenceType.Vdc] = bus.emt_model.external_mapping.get(VarPowerFlowReferenceType.Vdc, None)
    else:
        voltage_mapping[VarPowerFlowReferenceType.v_N] = bus.emt_model.external_mapping.get(VarPowerFlowReferenceType.v_N, None)
        voltage_mapping[VarPowerFlowReferenceType.v_A] = bus.emt_model.external_mapping.get(VarPowerFlowReferenceType.v_A, None)
        voltage_mapping[VarPowerFlowReferenceType.v_B] = bus.emt_model.external_mapping.get(VarPowerFlowReferenceType.v_B, None)
        voltage_mapping[VarPowerFlowReferenceType.v_C] = bus.emt_model.external_mapping.get(VarPowerFlowReferenceType.v_C, None)

    return voltage_mapping


def _detect_bus_shell_ac_mask(model: Block) -> List[bool] | None:
    """
    Detect the AC phase mask represented by one EMT bus shell.

    :param model: Bus EMT shell to inspect.
    :return: Mask ordered as ``[N, A, B, C]``, or ``None`` when malformed.
    """
    try:
        get_bus_emt_algebraic_vars(model)
    except (AttributeError, TypeError, ValueError):
        return None
    else:
        pass

    return list([
        model.external_mapping.get(VarPowerFlowReferenceType.v_N, None) is not None,
        model.external_mapping.get(VarPowerFlowReferenceType.v_A, None) is not None,
        model.external_mapping.get(VarPowerFlowReferenceType.v_B, None) is not None,
        model.external_mapping.get(VarPowerFlowReferenceType.v_C, None) is not None,
    ])


def _bus_shell_matches_expected_voltage_contract(bus: Any,
                                                 model: Block,
                                                 expected_mask: List[bool] | None) -> bool:
    """
    Check whether one EMT bus shell exposes the expected voltage contract.

    :param bus: Owning bus.
    :param model: EMT shell to inspect.
    :param expected_mask: Expected AC mask, or ``None`` for DC buses.
    :return: ``True`` when the shell matches the current topology/domain contract.
    """
    if bus.is_dc:
        voltage_var: Var | None = model.external_mapping.get(VarPowerFlowReferenceType.Vdc, None)
        if voltage_var is None:
            return False
        elif model.external_mapping.get(VarPowerFlowReferenceType.v_N, None) is not None:
            return False
        elif model.external_mapping.get(VarPowerFlowReferenceType.v_A, None) is not None:
            return False
        elif model.external_mapping.get(VarPowerFlowReferenceType.v_B, None) is not None:
            return False
        elif model.external_mapping.get(VarPowerFlowReferenceType.v_C, None) is not None:
            return False
        else:
            return True
    else:
        detected_mask: List[bool] | None = _detect_bus_shell_ac_mask(model=model)
        if detected_mask is None or expected_mask is None:
            return False
        elif model.external_mapping.get(VarPowerFlowReferenceType.Vdc, None) is not None:
            return False
        elif detected_mask != expected_mask:
            return False
        else:
            return True


def emt_bus_shell_matches_grid_topology(bus: Any, grid: Any) -> bool:
    """
    Check whether one existing EMT bus shell matches the current static topology.

    :param bus: Bus that owns the EMT shell.
    :param grid: Circuit used to derive the authoritative phase mask.
    :return: ``True`` when the existing shell matches the current grid contract.
    """
    expected_mask: List[bool] | None

    if bus.is_dc:
        expected_mask = None
    else:
        expected_mask = get_bus_mask(grid=grid, bus=bus)

    return _bus_shell_matches_expected_voltage_contract(bus=bus,
                                                        model=bus.emt_model,
                                                        expected_mask=expected_mask)


def _cleanup_bus_shell_var_factory_state(model: Block,
                                         var_factory: VarFactory) -> None:
    """
    Remove one discarded bus shell from the shared var-factory registries.

    :param model: Discarded bus shell.
    :param var_factory: Shared symbolic variable factory.
    :return: None.
    """
    stale_vars: List[Var] = list()
    stale_var: Var
    connected_uid: int

    stale_vars.extend(model.algebraic_vars)
    stale_vars.extend(model.out_vars)

    for stale_var in stale_vars:
        if stale_var.non_mutable_uid in var_factory.get_vars_dict():
            del var_factory.get_vars_dict()[stale_var.non_mutable_uid]
        else:
            pass

    stale_uids: set[int] = set(var.non_mutable_uid for var in stale_vars)
    connections_dict: Dict[int, List[Any]] = var_factory.get_connections_dict()
    connected_uid_list: List[int] = list(connections_dict.keys())

    for connected_uid in connected_uid_list:
        if connected_uid in stale_uids:
            del connections_dict[connected_uid]
        else:
            filtered_connections: List[Any] = list()
            connection: Any
            for connection in connections_dict[connected_uid]:
                if connection.non_mutable_uid in stale_uids:
                    pass
                else:
                    filtered_connections.append(connection)

            if len(filtered_connections) == 0:
                del connections_dict[connected_uid]
            else:
                connections_dict[connected_uid] = filtered_connections


def synchronize_emt_bus_shell_with_grid(bus: Any,
                                        grid: Any,
                                        var_factory: VarFactory,
                                        device_to_skip: Any | None = None) -> EmtBusShellSyncResult:
    """
    Synchronize one EMT bus shell with the current static topology.

    :param bus: Bus whose EMT shell must match the current topology.
    :param grid: Circuit used to derive the authoritative phase mask.
    :param var_factory: Shared symbolic variable factory.
    :param device_to_skip: Optional device currently being reconciled elsewhere.
    :return: Detailed synchronization result.
    """
    expected_mask: List[bool] | None
    old_mask: List[bool] | None = None
    rebuild_required: bool = False
    connected_devices: List[Any] = list()
    record: EmtBusConnectedModelRecord
    model: Block = bus.emt_model

    if bus.is_dc:
        expected_mask = None
    else:
        expected_mask = get_bus_mask(grid=grid, bus=bus)

    if model.empty():
        rebuild_required = True
    else:
        old_mask = _detect_bus_shell_ac_mask(model=model)
        if _bus_shell_matches_expected_voltage_contract(bus=bus,
                                                       model=model,
                                                       expected_mask=expected_mask):
            rebuild_required = False
        else:
            rebuild_required = True

    if rebuild_required:
        for record in bus.get_emt_models_connected():
            if record.get_device() in connected_devices:
                pass
            else:
                connected_devices.append(record.get_device())

        if not model.empty():
            _cleanup_bus_shell_var_factory_state(model=model, var_factory=var_factory)
        else:
            pass

        get_bus_emt_template(grid=grid, bus=bus)
        reconnect_registered_emt_models_for_bus(bus=bus,
                                                var_factory=var_factory,
                                                device_to_skip=device_to_skip)
        connect_pending_injection_bus_variables_emt(bus=bus,
                                                    var_factory=var_factory)

        for record in bus.get_emt_models_connected():
            if record.get_device() in connected_devices:
                pass
            else:
                connected_devices.append(record.get_device())

        for device in connected_devices:
            if device_to_skip is not None:
                if device is device_to_skip:
                    pass
                else:
                    if _has_materialized_emt_model(device=device):
                        unify_saved_emt_model_root_contract(device=device)
                        synchronize_saved_emt_root_contract_identity(device=device)
                        synchronize_saved_emt_root_contract_from_bus(device=device)
                    else:
                        pass
            else:
                if _has_materialized_emt_model(device=device):
                    unify_saved_emt_model_root_contract(device=device)
                    synchronize_saved_emt_root_contract_identity(device=device)
                    synchronize_saved_emt_root_contract_from_bus(device=device)
                else:
                    pass

        bus.mark_emt_model_grid_synchronized()
        return EmtBusShellSyncResult(changed=True,
                                     old_mask=old_mask,
                                     new_mask=expected_mask,
                                     voltage_vars=_build_bus_shell_voltage_mapping(bus=bus))
    else:
        bus.mark_emt_model_grid_synchronized()
        return EmtBusShellSyncResult(changed=False,
                                     old_mask=old_mask,
                                     new_mask=expected_mask,
                                     voltage_vars=_build_bus_shell_voltage_mapping(bus=bus))


def _has_materialized_emt_model(device: Any) -> bool:
    """
    Check whether one device already owns one materialized EMT model.

    The bus-resynchronisation algorithm must only reconnect devices that already
    expose a persistent EMT block. Missing or empty models cannot be rebound and
    must be ignored explicitly.

    :param device: Device to inspect.
    :return: ``True`` when the device has a non-empty EMT model.
    """
    if isinstance(device.emt_model, Block):
        if device.emt_model.empty():
            return False
        else:
            return True
    else:
        return False


def _is_entry_side_still_connected_to_bus(bus: Any,
                                          record: EmtBusConnectedModelRecord) -> bool:
    """
    Check whether one registered EMT endpoint still belongs to this bus.

    The bus registry can accumulate stale entries when one device changes model,
    clears its EMT template, or changes topology. Before reconnecting, the bus
    must verify that each record still matches the actual current bus endpoint.

    :param bus: Bus whose registry is being validated.
    :param record: Registered EMT endpoint.
    :return: ``True`` when the record still belongs to this bus.
    """
    device: Any = record.get_device()
    side: EmtBusConnectionSide = record.get_side()

    if side == EmtBusConnectionSide.BUS:
        if device.bus is bus:
            return True
        else:
            return False
    else:
        if side == EmtBusConnectionSide.FROM:
            if device.bus_from is bus:
                return True
            else:
                return False
        else:
            if side == EmtBusConnectionSide.TO:
                if device.bus_to is bus:
                    return True
                else:
                    return False
            else:
                return False


def _is_entry_model_still_current(record: EmtBusConnectedModelRecord) -> bool:
    """
    Check whether one registered EMT endpoint still points to the device current model.

    The registry must stop referencing old block instances after one device
    assigns a fresh EMT template block. Comparing against ``device.emt_model`` is
    the direct way to detect that stale state.

    :param record: Registered EMT endpoint.
    :return: ``True`` when the record still points to the live device model.
    """
    device: Any = record.get_device()
    model: Block = record.get_model()

    if isinstance(device.emt_model, Block):
        if device.emt_model is model:
            if model.empty():
                return False
            else:
                return True
        else:
            return False
    else:
        return False


def cleanup_connected_emt_models_for_bus(bus: Any) -> None:
    """
    Remove stale EMT endpoint records from one bus-local registry.

    The cleanup runs before every bus-driven reconnect so the algorithm only
    touches live endpoints that still belong to the bus and still reference the
    current device EMT model block.

    :param bus: Bus whose EMT endpoint registry must be cleaned.
    :return: None.
    """
    cleaned_records: list[EmtBusConnectedModelRecord] = list()
    record: EmtBusConnectedModelRecord

    for record in bus.get_emt_models_connected():
        side_is_valid: bool = _is_entry_side_still_connected_to_bus(bus=bus, record=record)
        model_is_valid: bool = _is_entry_model_still_current(record=record)

        if side_is_valid:
            if model_is_valid:
                cleaned_records.append(record)
            else:
                pass
        else:
            pass

    bus.clear_emt_models_connected()

    for record in cleaned_records:
        bus.add_or_replace_emt_model_connected(device=record.get_device(),
                                               emt_model=record.get_model(),
                                               side=record.get_side(),
                                               device_tpe=record.get_device_tpe())


def reconnect_registered_emt_models_for_bus(bus: Any,
                                            var_factory: VarFactory,
                                            device_to_skip: Any | None = None) -> None:
    """
    Reconnect every live registered EMT endpoint for one rebuilt bus shell.

    Rebuilding the bus shell changes the symbolic voltage variables. The bus must
    therefore rebind each registered EMT endpoint using the same connection rule
    that was used during the original device-to-bus attachment.

    :param bus: Bus whose connected EMT endpoints must be rebound.
    :param var_factory: Shared variable factory.
    :param device_to_skip: Optional device currently being reconciled elsewhere.
    :return: None.
    """
    cleanup_connected_emt_models_for_bus(bus=bus)

    record: EmtBusConnectedModelRecord
    for record in bus.get_emt_models_connected():
        device: Any = record.get_device()
        model: Block = record.get_model()
        side: EmtBusConnectionSide = record.get_side()
        device_tpe: DeviceType = record.get_device_tpe()

        if device_to_skip is not None:
            if device is device_to_skip:
                pass
                continue
            else:
                pass
        else:
            pass

        if side == EmtBusConnectionSide.BUS:
            # Single-bus EMT devices consume the bus shell directly, so the
            # reconnect rule is the one-to-one injection helper.
            connect_injection_emt(bus.emt_model, model, var_factory)
        else:
            if device_tpe == DeviceType.VscDevice:
                # VSCs use a dedicated EMT interface and therefore cannot be
                # rebound with the generic branch helper.
                if side == EmtBusConnectionSide.FROM:
                    connect_vsc_emt_from(bus.emt_model,
                                         model,
                                         var_factory,
                                         is_dc_bus=device.bus_from.is_dc)
                else:
                    if side == EmtBusConnectionSide.TO:
                        connect_vsc_emt_to(bus.emt_model,
                                           model,
                                           var_factory,
                                           is_dc_bus=device.bus_to.is_dc)
                    else:
                        pass
            else:
                if side == EmtBusConnectionSide.FROM:
                    connect_line_emt_from(bus.emt_model, model, var_factory)
                else:
                    if side == EmtBusConnectionSide.TO:
                        connect_line_emt_to(bus.emt_model, model, var_factory)
                    else:
                        pass


def register_connected_emt_model(bus: Any,
                                 device: Any,
                                 model: Block,
                                 side: EmtBusConnectionSide) -> None:
    """
    Register one live EMT endpoint on one bus.

    The registry key is maintained at the bus level so future bus-shell rebuilds
    can rebind the connected model deterministically without requiring a global
    circuit scan.

    :param bus: Bus that owns the registry.
    :param device: Owning device of the EMT model.
    :param model: Materialized EMT model block.
    :param side: Semantic bus side used by the connection.
    :return: None.
    """
    bus.add_or_replace_emt_model_connected(device=device,
                                           emt_model=model,
                                           side=side,
                                           device_tpe=device.device_type)


def unregister_connected_emt_model(bus: Any,
                                   device: Any,
                                   side: EmtBusConnectionSide | None = None) -> None:
    """
    Remove one device EMT endpoint registration from one bus.

    :param bus: Bus that owns the registry.
    :param device: Device whose registration must be removed.
    :param side: Optional side filter.
    :return: None.
    """
    if bus is None:
        return
    else:
        bus.remove_emt_model_connected_for_device(device=device, side=side)


def unregister_connected_emt_model_from_attached_buses(device: Any) -> None:
    """
    Remove stale bus endpoint registrations for one device from all its attached buses.

    This cleanup step runs before one device assigns or clears an EMT model so no
    bus registry keeps references to an obsolete block instance.

    :param device: Device whose bus registrations must be removed.
    :return: None.
    """
    branch_devices: list[DeviceType] = list([DeviceType.BranchDevice,
                                             DeviceType.LineDevice,
                                             DeviceType.Transformer2WDevice,
                                             DeviceType.Transformer3WDevice,
                                             DeviceType.DCLineDevice,
                                             DeviceType.HVDCLineDevice,
                                             DeviceType.SwitchDevice,
                                             DeviceType.SeriesReactanceDevice,
                                             DeviceType.UpfcDevice,
                                             DeviceType.VscDevice])

    if device.device_type in branch_devices:
        unregister_connected_emt_model(bus=device.bus_from,
                                       device=device,
                                       side=EmtBusConnectionSide.FROM)
        unregister_connected_emt_model(bus=device.bus_to,
                                       device=device,
                                       side=EmtBusConnectionSide.TO)
    else:
        unregister_connected_emt_model(bus=device.bus,
                                       device=device,
                                       side=EmtBusConnectionSide.BUS)


def register_saved_emt_model_vars_for_device(device: Any,
                                             var_factory: VarFactory) -> None:
    """
    Register the vars of one saved EMT model block in the shared variable factory.

    Editor-driven EMT saves replace the concrete ``device.emt_model`` block vars
    through ``copy_block_state()``. The saved block therefore contains fresh
    symbolic variables that are not automatically known by ``VarFactory``. The
    subsequent bus-side reconnect step depends on var-factory identity
    propagation, so the saved model vars must be registered first.

    :param device: Device whose saved EMT model vars must be registered.
    :param var_factory: Shared variable factory.
    :return: None.
    """
    model: Block = device.emt_model
    algebraic_var = None
    state_var = None
    diff_var = None

    if model.empty():
        return
    else:
        pass

    vars_dict = var_factory.get_vars_dict()
    diff_vars_dict = var_factory.get_diff_var_dict()

    # Overwrite the per-device vars_info entry with the final saved model vars so
    # later lookups reflect the authoritative post-editor symbolic objects.
    var_factory.vars_info[device] = list()

    for algebraic_var in model.algebraic_vars:
        # The var-factory connection propagation operates through the central var
        # registries keyed by stable ``non_mutable_uid``. Re-registering only in
        # ``vars_info`` is not enough for the saved editor-built vars to receive
        # propagated bus-side uid updates.
        vars_dict[algebraic_var.non_mutable_uid] = algebraic_var
        var_factory.register_var(device, algebraic_var)

    for state_var in model.state_vars:
        vars_dict[state_var.non_mutable_uid] = state_var
        var_factory.register_var(device, state_var)

    # Editor-built EMT models expose their bus contract through root input and
    # output vars. The bus connection helpers propagate live bus identities via
    # ``VarFactory`` using those root connection vars directly. If they are not
    # registered in the central var registry, ``add_connections()`` cannot find
    # them by ``non_mutable_uid`` and the saved editor model keeps stale bus-side
    # ``uid`` values even though the template setter path succeeds.
    io_var: Var
    for io_var in model.in_vars:
        vars_dict[io_var.non_mutable_uid] = io_var
        var_factory.register_var(device, io_var)

    for io_var in model.out_vars:
        vars_dict[io_var.non_mutable_uid] = io_var
        var_factory.register_var(device, io_var)

    for diff_var in model.diff_vars:
        diff_vars_dict[diff_var.non_mutable_uid] = diff_var
        var_factory.register_var(device, diff_var)


def unregister_saved_emt_model_var_connections_for_device(device: Any,
                                                          var_factory: VarFactory) -> None:
    """
    Remove saved EMT var-factory connection edges currently associated to one device.

    Reapplying one editor-built EMT model replaces the device symbolic vars, but
    the shared var-factory connection graph keeps old propagated edges unless the
    previous device-owned vars are detached explicitly. Those stale edges can
    later alias old and new root contract vars together and create symbolic
    cycles during bus reconnection.

    :param device: Device whose saved EMT graph edges must be removed.
    :param var_factory: Shared variable factory that owns the connection graph.
    :return: None.
    """
    previous_device_vars: list[Var] | None = var_factory.vars_info.get(device, None)
    previous_device_var_uids: set[int] = set()
    connected_uid: int
    outgoing_uid: int
    existing_connections: list[Any]
    kept_connections: list[Any]
    connection: Any

    if previous_device_vars is None:
        return
    else:
        pass

    for connection_var in previous_device_vars:
        previous_device_var_uids.add(connection_var.non_mutable_uid)

    for outgoing_uid, existing_connections in list(var_factory.get_connections_dict().items()):
        kept_connections = list()

        for connection in existing_connections:
            if connection.non_mutable_uid in previous_device_var_uids:
                pass
            else:
                kept_connections.append(connection)

        if len(kept_connections) == 0:
            del var_factory.get_connections_dict()[outgoing_uid]
        else:
            var_factory.get_connections_dict()[outgoing_uid] = kept_connections

    for connected_uid in previous_device_var_uids:
        if connected_uid in var_factory.get_connections_dict():
            del var_factory.get_connections_dict()[connected_uid]
        else:
            pass


def unify_saved_emt_model_root_contract(device: Any) -> None:
    """
    Unify one saved EMT model root external mapping with the actual root IO vars.

    Editor-driven ``copy_block_state()`` can leave the saved EMT block with one
    root ``external_mapping`` var and a different root ``in_var``/``out_var`` for
    the same power-flow reference. The EMT checker reads the external mapping,
    while the reconnect helpers operate on root IO vars. Rewriting only the
    mapping dictionary is not enough; the whole saved symbolic graph must be
    updated so the authoritative root IO var becomes the single object used by
    the saved model for that contract reference.

    :param device: Device whose saved EMT model root contract must be normalized.
    :return: None.
    """
    model: Block = device.emt_model
    ref = None

    if model.empty():
        return
    else:
        pass

    if _is_branch_like_device(device):
        _normalize_saved_branch_root_contract_from_live_sides(device=device)
        return
    else:
        pass

    refs_to_normalize: list[VarPowerFlowReferenceType] = list([
        VarPowerFlowReferenceType.Vdc,
        VarPowerFlowReferenceType.v_N,
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
        VarPowerFlowReferenceType.vf_N,
        VarPowerFlowReferenceType.vf_A,
        VarPowerFlowReferenceType.vf_B,
        VarPowerFlowReferenceType.vf_C,
        VarPowerFlowReferenceType.vt_N,
        VarPowerFlowReferenceType.vt_A,
        VarPowerFlowReferenceType.vt_B,
        VarPowerFlowReferenceType.vt_C,
        VarPowerFlowReferenceType.Vf_dc,
        VarPowerFlowReferenceType.Vt_dc,
        VarPowerFlowReferenceType.i_N,
        VarPowerFlowReferenceType.i_A,
        VarPowerFlowReferenceType.i_B,
        VarPowerFlowReferenceType.i_C,
        VarPowerFlowReferenceType.Idc,
        VarPowerFlowReferenceType.if_N,
        VarPowerFlowReferenceType.if_A,
        VarPowerFlowReferenceType.if_B,
        VarPowerFlowReferenceType.if_C,
        VarPowerFlowReferenceType.it_N,
        VarPowerFlowReferenceType.it_A,
        VarPowerFlowReferenceType.it_B,
        VarPowerFlowReferenceType.it_C,
    ])

    authoritative_input_by_ref: dict[VarPowerFlowReferenceType, Var] = dict()
    authoritative_output_by_ref: dict[VarPowerFlowReferenceType, Var] = dict()
    io_var = None

    for io_var in model.in_vars:
        if io_var.ref is None:
            pass
        else:
            if io_var.ref in authoritative_input_by_ref:
                pass
            else:
                authoritative_input_by_ref[io_var.ref] = io_var

    for io_var in model.out_vars:
        if io_var.ref is None:
            pass
        else:
            if io_var.ref in authoritative_output_by_ref:
                pass
            else:
                authoritative_output_by_ref[io_var.ref] = io_var

    # Rebuild the saved external contract from the authoritative root IO vars so
    # the checker and reconnect helpers reference the same root variables.
    for ref in refs_to_normalize:
        if ref in authoritative_input_by_ref:
            model.external_mapping[ref] = authoritative_input_by_ref[ref]
        else:
            if ref in authoritative_output_by_ref:
                model.external_mapping[ref] = authoritative_output_by_ref[ref]
            else:
                model.external_mapping[ref] = None

    # Prune duplicate root input vars that expose the same bus-contract
    # reference. The first root IO var seen for one reference is now the
    # authoritative contract variable used everywhere else.
    pruned_in_vars: list[Var] = list()
    seen_input_refs: set[VarPowerFlowReferenceType] = set()
    for io_var in model.in_vars:
        if io_var.ref is None:
            pruned_in_vars.append(io_var)
        else:
            if io_var.ref in seen_input_refs:
                pass
            else:
                pruned_in_vars.append(io_var)
                seen_input_refs.add(io_var.ref)
    model.in_vars = pruned_in_vars

    # Apply the same pruning rule to root outputs so only one authoritative root
    # contract var exists per output-side EMT reference.
    pruned_out_vars: list[Var] = list()
    seen_output_refs: set[VarPowerFlowReferenceType] = set()
    for io_var in model.out_vars:
        if io_var.ref is None:
            pruned_out_vars.append(io_var)
        else:
            if io_var.ref in seen_output_refs:
                pass
            else:
                pruned_out_vars.append(io_var)
                seen_output_refs.add(io_var.ref)
    model.out_vars = pruned_out_vars


def synchronize_saved_emt_root_contract_identity(device: Any) -> None:
    """
    Copy propagated root IO identities into the saved EMT external mapping.

    After editor save, one EMT root external-mapping entry and the matching root
    IO var can still be distinct symbolic objects even when they represent the
    same power-flow reference. The bus connection helpers propagate the live bus
    identity through the root IO vars via ``VarFactory``. The EMT validation
    reads the external mapping directly, so the saved external-mapping vars must
    mirror the propagated ``uid`` and ``name`` of the authoritative root IO vars
    without replacing the saved graph structure.

    :param device: Device whose saved EMT root contract must mirror propagated identities.
    :return: None.
    """
    model: Block = device.emt_model
    io_var_by_ref: dict[VarPowerFlowReferenceType, Var] = dict()
    io_var: Var
    mapping_var: Var | None
    reference: VarPowerFlowReferenceType
    refs_to_sync: list[VarPowerFlowReferenceType] = list([
        VarPowerFlowReferenceType.Vdc,
        VarPowerFlowReferenceType.v_N,
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
        VarPowerFlowReferenceType.vf_N,
        VarPowerFlowReferenceType.vf_A,
        VarPowerFlowReferenceType.vf_B,
        VarPowerFlowReferenceType.vf_C,
        VarPowerFlowReferenceType.vt_N,
        VarPowerFlowReferenceType.vt_A,
        VarPowerFlowReferenceType.vt_B,
        VarPowerFlowReferenceType.vt_C,
        VarPowerFlowReferenceType.Vf_dc,
        VarPowerFlowReferenceType.Vt_dc,
    ])

    if model.empty():
        return
    else:
        pass

    for io_var in model.in_vars:
        if io_var.ref is None:
            pass
        else:
            if io_var.ref in io_var_by_ref:
                pass
            else:
                io_var_by_ref[io_var.ref] = io_var

    for io_var in model.out_vars:
        if io_var.ref is None:
            pass
        else:
            if io_var.ref in io_var_by_ref:
                pass
            else:
                io_var_by_ref[io_var.ref] = io_var

    for reference in refs_to_sync:
        mapping_var = model.external_mapping.get(reference, None)

        if mapping_var is None:
            pass
        else:
            if reference in io_var_by_ref:
                mapping_var.uid = io_var_by_ref[reference].uid
                mapping_var.name = io_var_by_ref[reference].name
            else:
                pass

    rehash_block_tree_var_keyed_dicts(root_block=model)


def synchronize_saved_emt_root_contract_from_bus(device: Any) -> None:
    """
    Copy live bus-shell identities into the saved EMT root contract.

    The EMT validator compares the saved device external mapping directly
    against the live bus shell external mapping. After editor save, those saved
    device root contract vars can remain one disconnected clone from the live bus
    vars even when the graph structure and references are correct. Mirror the
    live bus-shell ``uid`` and ``name`` into the saved device contract in place
    so the saved editor graph remains unchanged while its bus bindings match the
    authoritative live bus shells.

    :param device: Device whose saved EMT root contract must match the live buses.
    :return: None.
    """
    branch_devices: list[DeviceType] = list([DeviceType.BranchDevice,
                                             DeviceType.LineDevice,
                                             DeviceType.Transformer2WDevice,
                                             DeviceType.Transformer3WDevice,
                                             DeviceType.DCLineDevice,
                                             DeviceType.HVDCLineDevice,
                                             DeviceType.SwitchDevice,
                                             DeviceType.SeriesReactanceDevice,
                                             DeviceType.UpfcDevice,
                                             DeviceType.VscDevice])
    model: Block = device.emt_model
    phase_map: dict[VarPowerFlowReferenceType, VarPowerFlowReferenceType]
    bus_reference: VarPowerFlowReferenceType
    device_reference: VarPowerFlowReferenceType
    bus_var: Var | None
    device_var: Var | None

    if model.empty():
        return
    else:
        pass

    if device.device_type in branch_devices:
        phase_map = dict([
            (VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.vf_N),
            (VarPowerFlowReferenceType.v_A, VarPowerFlowReferenceType.vf_A),
            (VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.vf_B),
            (VarPowerFlowReferenceType.v_C, VarPowerFlowReferenceType.vf_C),
            (VarPowerFlowReferenceType.Vdc, VarPowerFlowReferenceType.Vf_dc),
        ])
        for bus_reference, device_reference in phase_map.items():
            bus_var = device.bus_from.emt_model.external_mapping.get(bus_reference, None)
            device_var = model.external_mapping.get(device_reference, None)

            if bus_var is None:
                model.external_mapping[device_reference] = None
            else:
                if device_var is None:
                    pass
                else:
                    device_var.uid = bus_var.uid
                    device_var.name = bus_var.name

        phase_map = dict([
            (VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.vt_N),
            (VarPowerFlowReferenceType.v_A, VarPowerFlowReferenceType.vt_A),
            (VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.vt_B),
            (VarPowerFlowReferenceType.v_C, VarPowerFlowReferenceType.vt_C),
            (VarPowerFlowReferenceType.Vdc, VarPowerFlowReferenceType.Vt_dc),
        ])
        for bus_reference, device_reference in phase_map.items():
            bus_var = device.bus_to.emt_model.external_mapping.get(bus_reference, None)
            device_var = model.external_mapping.get(device_reference, None)

            if bus_var is None:
                model.external_mapping[device_reference] = None
            else:
                if device_var is None:
                    pass
                else:
                    device_var.uid = bus_var.uid
                    device_var.name = bus_var.name

    rehash_block_tree_var_keyed_dicts(root_block=model)


def synchronize_saved_emt_root_parameters_from_children(device: Any) -> None:
    """
    Mirror child static parameters into one saved EMT root block.

    Some editor-produced EMT models keep static parameters only in child blocks.
    The EMT initialization pipeline can still compile temporary residual systems
    starting from the saved root block contract before every wrapper/child path
    has been flattened, so the saved root must expose the same constant vars as
    its children for robust GUI execution.

    :param device: Device whose saved EMT root parameters must be synchronized.
    :return: None.
    """
    model: Block = device.emt_model
    child_block: Block
    parameter_var: Var
    parameter_value: Const
    api_key: Any
    api_var: Var | None

    if model.empty():
        return
    else:
        pass

    for child_block in model.children:
        for parameter_var, parameter_value in child_block.parameters.items():
            if parameter_var in model.parameters:
                pass
            else:
                model.parameters[parameter_var] = parameter_value

        # Editor-saved wrapper roots can keep static API mappings such as
        # ``omega_base`` only on the generated child block. The EMT static
        # parameter mapper later reads the root ``api_obj_mapping`` contract, so
        # mirror missing child mappings into the root before assembly.
        for api_key, api_var in child_block.api_obj_mapping.items():
            if api_key in model.api_obj_mapping:
                pass
            else:
                model.api_obj_mapping[api_key] = api_var

            if api_var is None:
                pass
            else:
                if api_var in child_block.parameters:
                    if api_var in model.parameters:
                        pass
                    else:
                        model.parameters[api_var] = child_block.parameters[api_var]
                else:
                    pass


def ensure_bus_emt_model_matches_grid_mask(bus: Any,
                                           grid: Any,
                                           var_factory: VarFactory) -> bool:
    """
    Ensure one bus EMT shell matches the current grid-derived phase contract.

    Reopening the dynamic editor after static topology or phase changes can
    leave one previously materialized EMT bus shell exposing an obsolete phase
    contract. When that happens, the shell must be rebuilt from the current
    ``get_bus_mask()`` result and every already-registered EMT device must be
    rebound to the new bus variables.

    :param bus: Bus whose EMT shell must be validated and, if needed, rebuilt.
    :param grid: Circuit used to derive the current bus phase mask.
    :param var_factory: Shared symbolic variable factory.
    :return: ``True`` when the bus EMT shell was rebuilt, else ``False``.
    """
    sync_result: EmtBusShellSyncResult = synchronize_emt_bus_shell_with_grid(bus=bus,
                                                                             grid=grid,
                                                                             var_factory=var_factory)
    return sync_result.changed


def initialize_bus_emt_from_grid_with_fallback(bus: Any,
                                               grid: Any,
                                               var_factory: VarFactory) -> None:
    """
    Initialize one bus EMT shell from the grid using the safe fallback mask.

    Template-style EMT assignment can occur before the surrounding topology has
    materialized any EMT-aware branch mask for the bus. In that case the bus
    still needs a stable ABC shell so the device connection contract can be
    attached without raising.

    :param bus: Bus to initialize.
    :param grid: Circuit used to derive the current mask.
    :param var_factory: Shared variable factory.
    :return: None.
    """
    bus.emt_model = BusEmtTemplate(
        vf=var_factory,
        mask=get_bus_mask(grid=grid, bus=bus),
        is_dc=bus.is_dc,
        name=f"{bus.name}_emt",
    ).block


def connect_line_rms_from(mdl1: Block, mdl2: Block, var_factory:VarFactory):
    """
    This function substitutes input variables for output variables to connect two rms models
    :param mdl1:
    :param mdl2:
    :param var_factory:
    :return:
    """
    # connect Vm
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowReferenceType.Vm and inpt.ref == VarPowerFlowReferenceType.Vmf
    ]
    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

    # connect Va
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowReferenceType.Va and inpt.ref == VarPowerFlowReferenceType.Vaf
    ]
    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

    normalize_branch_rms_root_contract_from(mdl1=mdl1, mdl2=mdl2)

def connect_models_power_flow(mdl1: Block, mdl2: Block, var_factory: VarFactory):
    """
    This function substitutes input variables for output variables to connect two rms models
    :param mdl1:
    :param mdl2:
    :param var_factory:
    :return:

    """
    # connect inputs mdl2 with outputs mdl1
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == inpt.ref
    ]
    for pair in pairs:
        # Todo: change connection method to use var_factory
        var_factory.add_connections([pair[1]], [pair[0]])

    normalize_single_bus_rms_root_contract(mdl1=mdl1, mdl2=mdl2)


def connect_line_rms_to(mdl1: Block, mdl2: Block, var_factory:VarFactory):
    """
    This function substitutes input variables for output variables to connect two rms models
    :param mdl1:
    :param mdl2:
    :param var_factory:
    :return:
    """
    # connect Vm
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowReferenceType.Vm and inpt.ref == VarPowerFlowReferenceType.Vmt
    ]
    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

    # connect Va
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowReferenceType.Va and inpt.ref == VarPowerFlowReferenceType.Vat
    ]
    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

    normalize_branch_rms_root_contract_to(mdl1=mdl1, mdl2=mdl2)


def normalize_rms_root_contract(mdl2: Block,
                                var_mapping: Dict[Var, Var]) -> None:
    """
    Normalize one RMS root contract to the authoritative connected bus variables.

    The RMS templates use one root wrapper block exposing ``in_vars`` and
    ``external_mapping`` while the actual equations can live in child blocks.
    After one connection is established, the authoritative symbolic identity for
    one bus-facing contract must be the live bus variable, not the template-side
    wrapper variable. Rewriting the whole block hierarchy keeps equations,
    initialization equations and root mappings aligned on the same variable UIDs.

    :param mdl2: Device RMS model whose root contract must be normalized.
    :param var_mapping: Old-to-new variable mapping for RMS contract vars.
    :return: None.
    """
    if len(var_mapping) == 0:
        pass
    else:
        mdl2.update_model_bulk(var_mapping=var_mapping)


def normalize_branch_rms_root_contract_from(mdl1: Block, mdl2: Block) -> None:
    """
    Normalize the RMS root contract for the branch ``from`` side.

    :param mdl1: Connected bus RMS model.
    :param mdl2: Branch RMS model.
    :return: None.
    """
    vm_bus: Var | None = mdl1.external_mapping.get(VarPowerFlowReferenceType.Vm, None)
    va_bus: Var | None = mdl1.external_mapping.get(VarPowerFlowReferenceType.Va, None)
    vm_dev: Var | None = mdl2.external_mapping.get(VarPowerFlowReferenceType.Vmf, None)
    va_dev: Var | None = mdl2.external_mapping.get(VarPowerFlowReferenceType.Vaf, None)
    var_mapping: Dict[Var, Var] = dict()

    if vm_bus is None:
        pass
    else:
        if vm_dev is None:
            pass
        else:
            if vm_dev.uid == vm_bus.uid:
                pass
            else:
                var_mapping[vm_dev] = vm_bus

    if va_bus is None:
        pass
    else:
        if va_dev is None:
            pass
        else:
            if va_dev.uid == va_bus.uid:
                pass
            else:
                var_mapping[va_dev] = va_bus

    normalize_rms_root_contract(mdl2=mdl2, var_mapping=var_mapping)


def normalize_branch_rms_root_contract_to(mdl1: Block, mdl2: Block) -> None:
    """
    Normalize the RMS root contract for the branch ``to`` side.

    :param mdl1: Connected bus RMS model.
    :param mdl2: Branch RMS model.
    :return: None.
    """
    vm_bus: Var | None = mdl1.external_mapping.get(VarPowerFlowReferenceType.Vm, None)
    va_bus: Var | None = mdl1.external_mapping.get(VarPowerFlowReferenceType.Va, None)
    vm_dev: Var | None = mdl2.external_mapping.get(VarPowerFlowReferenceType.Vmt, None)
    va_dev: Var | None = mdl2.external_mapping.get(VarPowerFlowReferenceType.Vat, None)
    var_mapping: Dict[Var, Var] = dict()

    if vm_bus is None:
        pass
    else:
        if vm_dev is None:
            pass
        else:
            if vm_dev.uid == vm_bus.uid:
                pass
            else:
                var_mapping[vm_dev] = vm_bus

    if va_bus is None:
        pass
    else:
        if va_dev is None:
            pass
        else:
            if va_dev.uid == va_bus.uid:
                pass
            else:
                var_mapping[va_dev] = va_bus

    normalize_rms_root_contract(mdl2=mdl2, var_mapping=var_mapping)


def normalize_single_bus_rms_root_contract(mdl1: Block, mdl2: Block) -> None:
    """
    Normalize the RMS root contract for one single-bus injection model.

    :param mdl1: Connected bus RMS model.
    :param mdl2: Single-bus RMS model.
    :return: None.
    """
    vm_bus: Var | None = mdl1.external_mapping.get(VarPowerFlowReferenceType.Vm, None)
    va_bus: Var | None = mdl1.external_mapping.get(VarPowerFlowReferenceType.Va, None)
    vm_dev: Var | None = mdl2.external_mapping.get(VarPowerFlowReferenceType.Vm, None)
    va_dev: Var | None = mdl2.external_mapping.get(VarPowerFlowReferenceType.Va, None)
    var_mapping: Dict[Var, Var] = dict()

    if vm_bus is None:
        pass
    else:
        if vm_dev is None:
            pass
        else:
            if vm_dev.uid == vm_bus.uid:
                pass
            else:
                var_mapping[vm_dev] = vm_bus

    if va_bus is None:
        pass
    else:
        if va_dev is None:
            pass
        else:
            if va_dev.uid == va_bus.uid:
                pass
            else:
                var_mapping[va_dev] = va_bus

    normalize_rms_root_contract(mdl2=mdl2, var_mapping=var_mapping)

def connect_line_phasor_rms_from(mdl1: Block, mdl2: Block, var_factory:VarFactory):
    """
    Connect phasor RMS models for the 'from' end of a line.
    Connects Vr, Vi from bus to line inputs.
    """
    # connect Vr
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowReferenceType.Vr and inpt.ref == VarPowerFlowReferenceType.Vrf
    ]
    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

    # connect Vi
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowReferenceType.Vi and inpt.ref == VarPowerFlowReferenceType.Vif
    ]
    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])


def connect_line_phasor_rms_to(mdl1: Block, mdl2: Block, var_factory:VarFactory):
    """
    Connect phasor RMS models for the 'to' end of a line.
    Connects Vr, Vi from bus to line inputs.
    """
    # connect Vr
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowReferenceType.Vr and inpt.ref == VarPowerFlowReferenceType.Vrt
    ]
    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

    # connect Vi
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowReferenceType.Vi and inpt.ref == VarPowerFlowReferenceType.Vit
    ]
    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])


def connect_models(mdl1: Block, mdl2: Block, var_factory:VarFactory):
    """
    This function substitutes input variables for output variables to connect two rms models
    :param mdl1:
    :param mdl2:
    :param var_factory:
    :return:
    """
    # connect inputs mdl2 with outputs mdl1
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.shared_ref == inpt.shared_ref and outp.shared_ref is not None and inpt.shared_ref is not None
    ]

    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

    # connect inputs mdl1 with outputs mdl2
    pairs = [
        (outp, inpt)
        for outp in mdl2.out_vars
        for inpt in mdl1.in_vars
        if outp.shared_ref == inpt.shared_ref and outp.shared_ref is not None and inpt.shared_ref is not None
    ]

    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

    #print("")
def connect_bus_variables_rms(device: Any, model:Block, var_factory: VarFactory | None):
    """
    connect the bus variables of the model with the api_object bus variables
    :param device:
    :type device:
    :param model:
    :type model:
    :param var_factory:
    :type var_factory:
    :return:
    :rtype:
    """
    if device.device_type in [DeviceType.BranchDevice,
                              DeviceType.LineDevice,
                              DeviceType.Transformer2WDevice,
                              DeviceType.Transformer3WDevice,
                              DeviceType.DCLineDevice,
                              DeviceType.HVDCLineDevice,
                              DeviceType.SwitchDevice,
                              DeviceType.SeriesReactanceDevice,
                              DeviceType.UpfcDevice,
                              DeviceType.VscDevice]:
        # Check if using phasor or polar coordinates by looking at bus model outputs
        bus_model = device.bus_from.rms_model
        if bus_model.empty():
            if var_factory is not None:
                initialize_bus_rms(device.bus_from, var_factory)
            else:
                raise ValueError("var factory not associated to grid element")

        # Check if bus has Vr/Vi (phasor) or Vm/Va (polar) outputs
        has_phasor = any(v.ref == VarPowerFlowReferenceType.Vr for v in bus_model.out_vars)
        if has_phasor:
            if var_factory is not None:
                connect_line_phasor_rms_from(device.bus_from.rms_model, model, var_factory)
        else:
            if var_factory is not None:
                connect_line_rms_from(device.bus_from.rms_model, model, var_factory)


        bus_model = device.bus_to.rms_model
        if bus_model.empty():
            if var_factory is not None:
                initialize_bus_rms(device.bus_to, var_factory)
            else:
                raise ValueError("var factory not associated to grid element")
        # Check if bus has Vr/Vi (phasor) or Vm/Va (polar) outputs
        has_phasor = any(v.ref == VarPowerFlowReferenceType.Vr for v in bus_model.out_vars)
        if has_phasor:
            if var_factory is not None:
                connect_line_phasor_rms_to(device.bus_to.rms_model, model, var_factory)
        else:
            if var_factory is not None:
                connect_line_rms_to(device.bus_to.rms_model, model, var_factory)


    else:
        if device.bus.rms_model.empty():
            if var_factory is not None:
                initialize_bus_rms(device.bus, var_factory)
            else:
                raise ValueError("var factory not associated to grid element")
        if var_factory is not None:
            connect_models_power_flow(device.bus.rms_model, model, var_factory)

def connect_pending_injection_bus_variables_emt(bus: Any,
                                                var_factory: VarFactory) -> None:
    """
    Connect deferred single-bus EMT devices once one bus shell exists.

    The GUI can assign one injection EMT template before any branch template has
    created the bus EMT shell. In that case the device model is duplicated and
    queued on the bus. When one branch later materializes the bus shell, this
    helper completes the pending bus-to-device EMT connections.

    :param bus: Bus whose pending EMT injection devices must be connected.
    :param var_factory: Shared variable factory used to register rebinding connections.
    :return: None.
    """
    pending_devices = bus.get_pending_emt_devices()
    pending_device: Any

    for pending_device in pending_devices:
        if bus.emt_model.empty():
            pass
        else:
            if pending_device.emt_model.empty():
                pass
            else:
                # Deferred injection models must be rebound using the same
                # connection primitive as eagerly connected EMT injections.
                connect_injection_emt(bus.emt_model, pending_device.emt_model, var_factory)
                # Once the pending model is finally wired, the bus must retain a
                # persistent registry entry so any future bus-shell rebuild can
                # rebind it without rediscovering the circuit topology.
                register_connected_emt_model(bus=bus,
                                             device=pending_device,
                                             model=pending_device.emt_model,
                                             side=EmtBusConnectionSide.BUS)
                bus.remove_pending_emt_device(pending_device)


def initialize_bus_emt_from_local_device_context(bus: Any,
                                                 var_factory: VarFactory) -> None:
    """
    Materialize one minimal EMT bus shell from the local bus context.

    When the GUI assigns one single-bus EMT template before any branch template
    exists, there is no topology-derived phase mask available yet. In that case
    the fallback shell must still be materialized immediately so the device can
    bind its voltage inputs. The default shell matches the existing bus-mask
    fallback contract: AC buses expose ABC and DC buses expose ``Vdc``.

    :param bus: Bus whose EMT shell must be initialized.
    :param var_factory: Shared symbolic variable factory.
    :return: None.
    """
    default_mask: list[bool]

    if bus.is_dc:
        default_mask = list([False, False, False, False])
    else:
        default_mask = list([False, True, True, True])

    bus.emt_model = BusEmtTemplate(vf=var_factory,
                                   mask=default_mask,
                                   is_dc=bus.is_dc,
                                   name=f"{bus.name}_emt").block


def _connect_branch_emt_model_to_bus(device: Any,
                                     model: Block,
                                     bus: Any,
                                     side: EmtBusConnectionSide,
                                     var_factory: VarFactory) -> None:
    """
    Connect one branch EMT terminal to one bus shell using the proper helper.

    :param device: Branch-like EMT device.
    :param model: Materialized EMT model block to connect.
    :param bus: Bus shell providing the terminal voltages.
    :param side: Semantic branch side represented by the bus.
    :param var_factory: Shared symbolic variable factory.
    :return: None.
    """
    if device.device_type == DeviceType.VscDevice:
        if side == EmtBusConnectionSide.FROM:
            connect_vsc_emt_from(bus.emt_model,
                                 model,
                                 var_factory,
                                 is_dc_bus=bus.is_dc)
        else:
            if side == EmtBusConnectionSide.TO:
                connect_vsc_emt_to(bus.emt_model,
                                   model,
                                   var_factory,
                                   is_dc_bus=bus.is_dc)
            else:
                pass
    else:
        if side == EmtBusConnectionSide.FROM:
            connect_line_emt_from(bus.emt_model, model, var_factory)
        else:
            if side == EmtBusConnectionSide.TO:
                connect_line_emt_to(bus.emt_model, model, var_factory)
            else:
                pass

def attach_emt_model_to_buses(device: Any,
                              model: Block,
                              var_factory: VarFactory) -> None:
    """
    Attach one EMT model to its bus shells using one shared engine workflow.

    :param device: Device owning the EMT model.
    :param model: Materialized EMT model block to attach.
    :param var_factory: Shared symbolic variable factory.
    :return: None.
    """
    branch_devices: list[DeviceType] = list([DeviceType.BranchDevice,
                                             DeviceType.LineDevice,
                                             DeviceType.Transformer2WDevice,
                                             DeviceType.Transformer3WDevice,
                                             DeviceType.DCLineDevice,
                                             DeviceType.HVDCLineDevice,
                                             DeviceType.SwitchDevice,
                                             DeviceType.SeriesReactanceDevice,
                                             DeviceType.UpfcDevice,
                                             DeviceType.VscDevice])

    unregister_connected_emt_model_from_attached_buses(device=device)

    if device.device_type in branch_devices:
        if device.bus_from.emt_model.empty():
            raise ValueError(f"Connection Bus EMT model cannot be empty, initialize {device.bus_from.name} EMT model")
        else:
            pass

        _connect_branch_emt_model_to_bus(device=device,
                                         model=model,
                                         bus=device.bus_from,
                                         side=EmtBusConnectionSide.FROM,
                                         var_factory=var_factory)
        register_connected_emt_model(bus=device.bus_from,
                                     device=device,
                                     model=model,
                                     side=EmtBusConnectionSide.FROM)

        if device.bus_to.emt_model.empty():
            raise ValueError(f"Connection Bus EMT model cannot be empty, initialize {device.bus_to.name} EMT model")
        else:
            pass

        _connect_branch_emt_model_to_bus(device=device,
                                         model=model,
                                         bus=device.bus_to,
                                         side=EmtBusConnectionSide.TO,
                                         var_factory=var_factory)
        register_connected_emt_model(bus=device.bus_to,
                                     device=device,
                                     model=model,
                                     side=EmtBusConnectionSide.TO)

        # Non-VSC branch devices expose bus-side EMT voltage contracts through
        # root external-mapping vars such as ``vf_A`` and ``vt_A``. The symbolic
        # connection propagation updates the live root IO vars through the shared
        # VarFactory graph, but after editor save the saved root external mapping
        # can still point to pre-propagation objects. Re-normalize the saved root
        # contract after the bus connections are attached so validation reads the
        # same propagated symbolic objects that the connection helpers updated.
        seed_template_derived_dynamic_connection_intents(device=device)
        rematerialize_saved_dynamic_connection_intents(device=device,
                                                       var_factory=var_factory)
        if device.device_type == DeviceType.VscDevice:
            pass
        else:
            _normalize_saved_branch_root_contract_from_live_sides(device=device)
            synchronize_saved_emt_root_contract_identity(device=device)
            synchronize_saved_emt_root_contract_from_bus(device=device)
    else:
        if device.bus.emt_model.empty():
            raise ValueError(f"Connection Bus EMT model cannot be empty, initialize {device.bus.name} EMT model")
        else:
            connect_injection_emt(device.bus.emt_model, model, var_factory)
            register_connected_emt_model(bus=device.bus,
                                         device=device,
                                         model=model,
                                         side=EmtBusConnectionSide.BUS)
            seed_template_derived_dynamic_connection_intents(device=device)
            rematerialize_saved_dynamic_connection_intents(device=device,
                                                           var_factory=var_factory)
            # Single-bus EMT devices validate their root external mapping against
            # the live bus shell directly. Rebuild the saved root contract after
            # the connection propagation step so those root references point to
            # the propagated bus-side symbolic objects instead of stale clones.
            unify_saved_emt_model_root_contract(device=device)
            synchronize_saved_emt_root_contract_identity(device=device)
            synchronize_saved_emt_root_contract_from_bus(device=device)


def connect_bus_variables_emt(device: Any,
                              model: Block,
                              var_factory: VarFactory | None,
                              allow_deferred_connection: bool = False,
                              grid: Any | None = None) -> None:
    """
    connect the bus variables of the model with the api_object bus variables
    :param device:
    :type device:
    :param model:
    :type model:
    :param var_factory:
    :type var_factory:
    :param allow_deferred_connection:
    :type allow_deferred_connection:
    :param grid: Owning circuit used for immediate EMT rebinding after bus rebuilds.
    :type grid: Any | None
    :return:
    :rtype:
    """

    branch_devices: list[DeviceType] = list([DeviceType.BranchDevice,
                                             DeviceType.LineDevice,
                                             DeviceType.Transformer2WDevice,
                                             DeviceType.Transformer3WDevice,
                                             DeviceType.DCLineDevice,
                                             DeviceType.HVDCLineDevice,
                                             DeviceType.SwitchDevice,
                                             DeviceType.SeriesReactanceDevice,
                                             DeviceType.UpfcDevice,
                                             DeviceType.VscDevice])

    if var_factory is None:
        raise ValueError("var factory not associated to grid element")
    else:
        pass

    if device.device_type in branch_devices:
        if device.bus_from.emt_model.empty():
            if allow_deferred_connection:
                if grid is None:
                    initialize_bus_emt_from_local_device_context(bus=device.bus_from,
                                                                 var_factory=var_factory)
                else:
                    initialize_bus_emt_from_grid_with_fallback(bus=device.bus_from,
                                                               grid=grid,
                                                               var_factory=var_factory)
            else:
                raise ValueError(f"Connection Bus EMT model cannot be empty, initialize {device.bus_from.name} EMT model")
        else:
            pass

        if device.bus_to.emt_model.empty():
            if allow_deferred_connection:
                if grid is None:
                    initialize_bus_emt_from_local_device_context(bus=device.bus_to,
                                                                 var_factory=var_factory)
                else:
                    initialize_bus_emt_from_grid_with_fallback(bus=device.bus_to,
                                                               grid=grid,
                                                               var_factory=var_factory)
            else:
                raise ValueError(f"Connection Bus EMT model cannot be empty, initialize {device.bus_to.name} EMT model")
        else:
            pass

        attach_emt_model_to_buses(device=device,
                                  model=model,
                                  var_factory=var_factory)
    else:
        if device.bus.emt_model.empty():
            if allow_deferred_connection:
                if grid is not None:
                    initialize_bus_emt_from_grid_with_fallback(bus=device.bus,
                                                               grid=grid,
                                                               var_factory=var_factory)
                else:
                    initialize_bus_emt_from_local_device_context(bus=device.bus,
                                                                 var_factory=var_factory)
            else:
                raise ValueError(f"Connection Bus EMT model cannot be empty, initialize {device.bus.name} EMT model")
        else:
            pass

        attach_emt_model_to_buses(device=device,
                                  model=model,
                                  var_factory=var_factory)


def set_rms_model(device: Any, model:Block, var_factory: VarFactory):
    """
    Set the RMS model
    :return:
    :rtype:
    """
    # connect bus variables

    if device.device_type in [DeviceType.BranchDevice,
                              DeviceType.LineDevice,
                              DeviceType.Transformer2WDevice,
                              DeviceType.Transformer3WDevice,
                              DeviceType.DCLineDevice,
                              DeviceType.HVDCLineDevice,
                              DeviceType.SwitchDevice,
                              DeviceType.SeriesReactanceDevice,
                              DeviceType.UpfcDevice,
                              DeviceType.VscDevice]:
        # Check if using phasor or polar coordinates by looking at bus model outputs
        bus_model = device.bus_from.rms_model
        if not bus_model.empty():
            # Check if bus has Vr/Vi (phasor) or Vm/Va (polar) outputs
            has_phasor = any(v.ref == VarPowerFlowReferenceType.Vr for v in bus_model.out_vars)
            if has_phasor:
                connect_line_phasor_rms_from(device.bus_from.rms_model, model, var_factory)
            else:
                connect_line_rms_from(device.bus_from.rms_model, model, var_factory)
        else:
            raise ValueError(f"Connection Bus RMS model cannot be empty, initialize {device.bus_from.name} RMS model")

        bus_model = device.bus_to.rms_model
        if not bus_model.empty():
            # Check if bus has Vr/Vi (phasor) or Vm/Va (polar) outputs
            has_phasor = any(v.ref == VarPowerFlowReferenceType.Vr for v in bus_model.out_vars)
            if has_phasor:
                connect_line_phasor_rms_to(device.bus_to.rms_model, model, var_factory)
            else:
                connect_line_rms_to(device.bus_to.rms_model, model, var_factory)
        else:
            raise ValueError(f"Connection Bus RMS model cannot be empty, initialize {device.bus_to.name} RMS model")

    else:
        if not device.bus.rms_model.empty():
            for mdl in model.get_all_blocks():
                connect_models_power_flow(device.bus.rms_model, mdl, var_factory)

        else:
            raise ValueError(f"Connection Bus RMS model cannot be empty, initialize {device.bus.name} RMS model")

    # fill var factory dict[Dev, List[Var]] with model variables
    # model.unify_blocks()
    # for vr in model.algebraic_vars:
    #     var_factory.register_var(device, vr)
    # for vr in model.state_vars:
    #     var_factory.register_var(device, vr)

    # set the model to the device
    device.rms_model = model


def connect_line_emt_from(mdl1: Block, mdl2: Block, var_factory:VarFactory):
    """
    Connects the bus voltages (mdl1) to the "from" side of the line (mdl2)
    for simulations with explicit phases (e.g., EMT).
    It only connects the phases present in both models (any NABC combination).

    :param mdl1: Bus model (Block)
    :param mdl2: Line model (Block)
    :param var_factory:
    :return: None
    """
    # Branch EMT validation later rebuilds the saved external mapping from the
    # authoritative root IO vars. The connection helper must therefore propagate
    # bus identities into those root input vars, not only into detached mapping
    # objects, otherwise the later normalization step would overwrite the saved
    # contract with stale root-input identities.
    pairs: List[tuple[Var, Var]] = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowReferenceType.v_N and inpt.ref == VarPowerFlowReferenceType.vf_N
    ]
    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowReferenceType.v_A and inpt.ref == VarPowerFlowReferenceType.vf_A
    ]
    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowReferenceType.v_B and inpt.ref == VarPowerFlowReferenceType.vf_B
    ]
    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowReferenceType.v_C and inpt.ref == VarPowerFlowReferenceType.vf_C
    ]
    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowReferenceType.Vdc and inpt.ref == VarPowerFlowReferenceType.Vf_dc
    ]
    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

    # Editor-saved EMT models can keep distinct root external-mapping vars for
    # the same branch-side references. The EMT validator reads that mapping
    # directly, so propagate the live bus identity into those mapping vars too.
    phase_map: dict[VarPowerFlowReferenceType, VarPowerFlowReferenceType] = dict([
        (VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.vf_N),
        (VarPowerFlowReferenceType.v_A, VarPowerFlowReferenceType.vf_A),
        (VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.vf_B),
        (VarPowerFlowReferenceType.v_C, VarPowerFlowReferenceType.vf_C),
        (VarPowerFlowReferenceType.Vdc, VarPowerFlowReferenceType.Vf_dc),
    ])
    bus_reference: VarPowerFlowReferenceType
    device_reference: VarPowerFlowReferenceType
    bus_var: Var | None
    device_mapping_var: Var | None
    for bus_reference, device_reference in phase_map.items():
        bus_var = mdl1.external_mapping.get(bus_reference, None)
        device_mapping_var = mdl2.external_mapping.get(device_reference, None)

        if bus_var is None:
            pass
        else:
            if device_mapping_var is None:
                pass
            else:
                var_factory.add_connections([device_mapping_var], [bus_var])

def connect_line_emt_to(mdl1: Block, mdl2: Block, var_factory:VarFactory):
    """
    Connects the bus voltages (mdl1) to the "to" side of the line (mdl2)
    for simulations with explicit phases (e.g., EMT).
    It only connects the phases present in both models (any NABC combination).

    :param mdl1: Bus model (Block)
    :param mdl2: Line model (Block)
    :param var_factory:
    :return: None
    """
    # The same authoritative-root-IO rule as the from side applies here.
    pairs: List[tuple[Var, Var]] = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowReferenceType.v_N and inpt.ref == VarPowerFlowReferenceType.vt_N
    ]
    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowReferenceType.v_A and inpt.ref == VarPowerFlowReferenceType.vt_A
    ]
    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowReferenceType.v_B and inpt.ref == VarPowerFlowReferenceType.vt_B
    ]
    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowReferenceType.v_C and inpt.ref == VarPowerFlowReferenceType.vt_C
    ]
    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowReferenceType.Vdc and inpt.ref == VarPowerFlowReferenceType.Vt_dc
    ]
    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

    phase_map: dict[VarPowerFlowReferenceType, VarPowerFlowReferenceType] = dict([
        (VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.vt_N),
        (VarPowerFlowReferenceType.v_A, VarPowerFlowReferenceType.vt_A),
        (VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.vt_B),
        (VarPowerFlowReferenceType.v_C, VarPowerFlowReferenceType.vt_C),
        (VarPowerFlowReferenceType.Vdc, VarPowerFlowReferenceType.Vt_dc),
    ])
    bus_reference: VarPowerFlowReferenceType
    device_reference: VarPowerFlowReferenceType
    bus_var: Var | None
    device_mapping_var: Var | None
    for bus_reference, device_reference in phase_map.items():
        bus_var = mdl1.external_mapping.get(bus_reference, None)
        device_mapping_var = mdl2.external_mapping.get(device_reference, None)

        if bus_var is None:
            pass
        else:
            if device_mapping_var is None:
                pass
            else:
                var_factory.add_connections([device_mapping_var], [bus_var])


def connect_injection_emt(mdl1: Block, mdl2: Block, var_factory:VarFactory) -> None:
    """
    Connect one bus EMT shell to one single-bus EMT injection model.

    The bus shell exposes EMT bus voltages as outputs. Single-bus injection
    templates consume those same voltage references directly on their inputs,
    so the connection rule is one direct reference match per supported node.

    :param mdl1: Bus EMT model.
    :param mdl2: EMT model of one single-bus injection device.
    :param var_factory:
    :return: None.
    """
    # Single-bus EMT validation also rebuilds the saved root contract from the
    # authoritative root input vars, so bus identity must be propagated through
    # those root inputs directly.
    pairs: List[tuple[Var, Var]] = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == inpt.ref
    ]

    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

    phase_refs: list[VarPowerFlowReferenceType] = list([
        VarPowerFlowReferenceType.Vdc,
        VarPowerFlowReferenceType.v_N,
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
    ])
    reference: VarPowerFlowReferenceType
    bus_var: Var | None
    device_mapping_var: Var | None
    for reference in phase_refs:
        bus_var = mdl1.external_mapping.get(reference, None)
        device_mapping_var = mdl2.external_mapping.get(reference, None)

        if bus_var is None:
            pass
        else:
            if device_mapping_var is None:
                pass
            else:
                var_factory.add_connections([device_mapping_var], [bus_var])

def connect_vsc_emt_from(mdl1: Block, mdl2: Block, var_factory:VarFactory,is_dc_bus: bool = False):
    """
    Connects the bus voltages to the "from" side of the VSC model.
    For DC buses, connects Vdc. For AC buses, connects abc voltages.

    :param mdl1: Bus model (Block)
    :param mdl2: VSC model (Block)
    :param var_factory:
    :param is_dc_bus: True if bus_from is DC
    :return: None
    """
    if is_dc_bus:
        # DC bus: connect the live bus ``Vdc`` directly to the VSC root DC input.
        # Pseudo-converter templates expose the shared DC terminal through the
        # root external mapping while the actual input variable may not carry the
        # ``VarPowerFlowReferenceType.Vdc`` reference itself. Matching only by
        # input reference would therefore miss this valid contract.
        bus_vdc_var: Var | None = mdl1.external_mapping.get(VarPowerFlowReferenceType.Vdc, None)
        vsc_vdc_var: Var | None = mdl2.external_mapping.get(VarPowerFlowReferenceType.Vf_dc, None)

        if vsc_vdc_var is None:
            # Older or single-bus-style VSC templates can still expose the DC
            # side through the generic ``Vdc`` reference. The branch editor,
            # however, materializes the DC terminal as ``Vf_dc``/``Vt_dc``.
            # Prefer the branch-side contract when present and fall back to the
            # generic reference only to preserve compatibility with legacy data.
            vsc_vdc_var = mdl2.external_mapping.get(VarPowerFlowReferenceType.Vdc, None)
        else:
            pass

        pairs: List[tuple[Var, Var]] = list()

        if bus_vdc_var is None:
            pass
        else:
            if vsc_vdc_var is None:
                pass
            else:
                pairs.append((bus_vdc_var, vsc_vdc_var))
    else:
        # AC bus: connect abc voltages.
        phase_map = {
            VarPowerFlowReferenceType.v_A: VarPowerFlowReferenceType.v_A,
            VarPowerFlowReferenceType.v_B: VarPowerFlowReferenceType.v_B,
            VarPowerFlowReferenceType.v_C: VarPowerFlowReferenceType.v_C
        }
        pairs = [
            (outp, inpt)
            for outp in mdl1.out_vars
            for inpt in mdl2.in_vars
            if outp.ref in phase_map and phase_map[outp.ref] == inpt.ref
        ]

    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])


def connect_vsc_emt_to(mdl1: Block, mdl2: Block, var_factory:VarFactory, is_dc_bus: bool = False):
    """
    Connects the bus voltages to the "to" side of the VSC model.
    For DC buses, connects Vdc. For AC buses, connects abc voltages.

    :param mdl1: Bus model (Block)
    :param mdl2: VSC model (Block)
    :param var_factory:
    :param is_dc_bus: True if bus_to is DC
    :return: None
    """
    if is_dc_bus:
        # DC bus: connect the bus ``Vdc`` to the branch-side VSC DC terminal.
        # The editor and branch EMT root contract expose the ``to``-side DC
        # voltage as ``Vt_dc``. Falling back to plain ``Vdc`` preserves support
        # for any older template that still uses the generic reference.
        bus_vdc_var: Var | None = mdl1.external_mapping.get(VarPowerFlowReferenceType.Vdc, None)
        vsc_vdc_var: Var | None = mdl2.external_mapping.get(VarPowerFlowReferenceType.Vt_dc, None)

        if vsc_vdc_var is None:
            vsc_vdc_var = mdl2.external_mapping.get(VarPowerFlowReferenceType.Vdc, None)
        else:
            pass

        pairs: List[tuple[Var, Var]] = list()

        if bus_vdc_var is None:
            pass
        else:
            if vsc_vdc_var is None:
                pass
            else:
                pairs.append((bus_vdc_var, vsc_vdc_var))
    else:
        # AC bus: connect abc voltages
        phase_map = {
            VarPowerFlowReferenceType.v_A: VarPowerFlowReferenceType.v_A,
            VarPowerFlowReferenceType.v_B: VarPowerFlowReferenceType.v_B,
            VarPowerFlowReferenceType.v_C: VarPowerFlowReferenceType.v_C
        }
        pairs = [
            (outp, inpt)
            for outp in mdl1.out_vars
            for inpt in mdl2.in_vars
            if outp.ref in phase_map and phase_map[outp.ref] == inpt.ref
        ]

    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])


def set_emt_model(device: Any, model: Block, var_factory: VarFactory):
    """
    Sets the EMT model for a given device, connects it to the bus(es),
    and stores the same hierarchical runtime shape used by GUI assignment.

    :param device: The power system device (Line, Transformer, Generator, etc.)
    :param model: The mathematical block model of the device
    :param var_factory: Factory to register simulation variables
    :return: None
    """
    # The attachment path normalizes the authoritative saved root through
    # ``device.emt_model``. Publish the incoming block first so scripting does
    # not normalize the previous (often empty) device model while connecting
    # the new block separately.
    device.emt_model = model

    # Route all callers through the shared attachment path so branch and
    # injection EMT models preserve the same root external contract used by the
    # editor-driven template setters and topology validation.
    connect_bus_variables_emt(device=device,
                              model=model,
                              var_factory=var_factory,
                              allow_deferred_connection=True)
    # EMT scripting must now preserve the same pre-build hierarchical runtime
    # shape produced by GUI template assignment. The shared EMT problem build
    # path performs the authoritative flattening stage for both workflows.
