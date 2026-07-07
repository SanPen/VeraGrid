# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
#
from typing import Any, List
#
from VeraGridEngine.enumerations import VarPowerFlowReferenceType
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory

from VeraGridEngine.Utils.Symbolic.block import Block, Var
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Utils.Symbolic.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.bus_emt_template import BusEmtTemplate
from VeraGridEngine.Devices.Parents.dynamic_bus_parent import EmtBusConnectionSide, EmtBusConnectedModelRecord


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
                                            var_factory: VarFactory) -> None:
    """
    Reconnect every live registered EMT endpoint for one rebuilt bus shell.

    Rebuilding the bus shell changes the symbolic voltage variables. The bus must
    therefore rebind each registered EMT endpoint using the same connection rule
    that was used during the original device-to-bus attachment.

    :param bus: Bus whose connected EMT endpoints must be rebound.
    :param var_factory: Shared variable factory.
    :return: None.
    """
    cleanup_connected_emt_models_for_bus(bus=bus)

    record: EmtBusConnectedModelRecord
    for record in bus.get_emt_models_connected():
        device: Any = record.get_device()
        model: Block = record.get_model()
        side: EmtBusConnectionSide = record.get_side()
        device_tpe: DeviceType = record.get_device_tpe()

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
                pass

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
                pass
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
                pass
            else:
                if device_var is None:
                    pass
                else:
                    device_var.uid = bus_var.uid
                    device_var.name = bus_var.name
    else:
        phase_map = dict([
            (VarPowerFlowReferenceType.Vdc, VarPowerFlowReferenceType.Vdc),
            (VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.v_N),
            (VarPowerFlowReferenceType.v_A, VarPowerFlowReferenceType.v_A),
            (VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.v_B),
            (VarPowerFlowReferenceType.v_C, VarPowerFlowReferenceType.v_C),
        ])
        for bus_reference, device_reference in phase_map.items():
            bus_var = device.bus.emt_model.external_mapping.get(bus_reference, None)
            device_var = model.external_mapping.get(device_reference, None)

            if bus_var is None:
                pass
            else:
                if device_var is None:
                    pass
                else:
                    device_var.uid = bus_var.uid
                    device_var.name = bus_var.name


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

    if device.device_type in [DeviceType.BranchDevice, DeviceType.LineDevice, DeviceType.Transformer2WDevice, DeviceType.Transformer3WDevice]:
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


def build_emt_bus_mask_from_existing_model(bus_model: Block) -> list[bool]:
    """
    Build the AC phase mask already materialized in one EMT bus model.

    The shared EMT attachment flow must preserve the phases that already exist on
    one bus because other connected EMT devices may already depend on them. This
    helper reads the current bus external mapping and converts it into the
    canonical ``[N, A, B, C]`` phase mask used by the bus-shell ensure logic.

    :param bus_model: Existing EMT bus block.
    :return: Phase mask ordered as ``[N, A, B, C]``.
    """
    external_mapping: dict[Any, Var | None] = bus_model.external_mapping
    mask: list[bool] = list([False, False, False, False])

    mask[0] = external_mapping.get(VarPowerFlowReferenceType.v_N, None) is not None
    mask[1] = external_mapping.get(VarPowerFlowReferenceType.v_A, None) is not None
    mask[2] = external_mapping.get(VarPowerFlowReferenceType.v_B, None) is not None
    mask[3] = external_mapping.get(VarPowerFlowReferenceType.v_C, None) is not None

    return mask


def ensure_bus_emt_shell(bus: Any,
                         required_mask: list[bool],
                         var_factory: VarFactory) -> bool:
    """
    Ensure that one bus owns one EMT shell covering the required phases.

    The EMT assignment algorithm must materialize a missing bus shell on first
    use and expand one existing AC shell only when one newly attached device
    requires additional phases.

    :param bus: Bus whose EMT shell must exist.
    :param required_mask: Required AC phase mask ordered as ``[N, A, B, C]``.
    :param var_factory: Shared symbolic variable factory.
    :return: ``True`` when the bus shell had to be rebuilt.
    """
    bus_shell_rebuilt: bool = False

    if bus.is_dc:
        if bus.emt_model.empty():
            bus.emt_model = BusEmtTemplate(vf=var_factory,
                                           mask=list([False, False, False, False]),
                                           is_dc=True,
                                           name=f"{bus.name}_emt_template").block
            bus_shell_rebuilt = True
        else:
            pass
    else:
        if bus.emt_model.empty():
            bus.emt_model = BusEmtTemplate(vf=var_factory,
                                           mask=required_mask,
                                           is_dc=False,
                                           name=f"{bus.name}_emt_template").block
            bus_shell_rebuilt = True
        else:
            existing_mask: list[bool] = build_emt_bus_mask_from_existing_model(bus.emt_model)
            merged_mask: list[bool] = list([False, False, False, False])

            merged_mask[0] = existing_mask[0] or required_mask[0]
            merged_mask[1] = existing_mask[1] or required_mask[1]
            merged_mask[2] = existing_mask[2] or required_mask[2]
            merged_mask[3] = existing_mask[3] or required_mask[3]

            if merged_mask != existing_mask:
                bus.emt_model = BusEmtTemplate(vf=var_factory,
                                               mask=merged_mask,
                                               is_dc=False,
                                               name=f"{bus.name}_emt_template").block
                bus_shell_rebuilt = True
            else:
                pass

    return bus_shell_rebuilt


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
                              var_factory: VarFactory,
                              bus_mask: list[bool] | None = None,
                              from_mask: list[bool] | None = None,
                              to_mask: list[bool] | None = None) -> None:
    """
    Attach one EMT model to its bus shells using one shared engine workflow.

    :param device: Device owning the EMT model.
    :param model: Materialized EMT model block to attach.
    :param var_factory: Shared symbolic variable factory.
    :param bus_mask: Required single-bus mask for injection devices.
    :param from_mask: Required from-side mask for branch devices.
    :param to_mask: Required to-side mask for branch devices.
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

    # The shared attachment path must materialize the current block on the
    # device first because registry cleanup and validation helpers compare live
    # entries against ``device.emt_model``.
    device.emt_model = model

    unregister_connected_emt_model_from_attached_buses(device=device)

    if device.device_type in branch_devices:
        from_required_mask: list[bool]
        to_required_mask: list[bool]
        from_bus_rebuilt: bool
        to_bus_rebuilt: bool

        if from_mask is None:
            from_required_mask = list([False, False, False, False])
        else:
            from_required_mask = from_mask

        if to_mask is None:
            to_required_mask = list([False, False, False, False])
        else:
            to_required_mask = to_mask

        from_bus_rebuilt = ensure_bus_emt_shell(bus=device.bus_from,
                                                required_mask=from_required_mask,
                                                var_factory=var_factory)
        _connect_branch_emt_model_to_bus(device=device,
                                         model=model,
                                         bus=device.bus_from,
                                         side=EmtBusConnectionSide.FROM,
                                         var_factory=var_factory)
        register_connected_emt_model(bus=device.bus_from,
                                     device=device,
                                     model=model,
                                     side=EmtBusConnectionSide.FROM)
        if from_bus_rebuilt:
            reconnect_registered_emt_models_for_bus(bus=device.bus_from,
                                                    var_factory=var_factory)
        else:
            pass
        connect_pending_injection_bus_variables_emt(device.bus_from, var_factory)

        to_bus_rebuilt = ensure_bus_emt_shell(bus=device.bus_to,
                                              required_mask=to_required_mask,
                                              var_factory=var_factory)
        _connect_branch_emt_model_to_bus(device=device,
                                         model=model,
                                         bus=device.bus_to,
                                         side=EmtBusConnectionSide.TO,
                                         var_factory=var_factory)
        register_connected_emt_model(bus=device.bus_to,
                                     device=device,
                                     model=model,
                                     side=EmtBusConnectionSide.TO)
        if to_bus_rebuilt:
            reconnect_registered_emt_models_for_bus(bus=device.bus_to,
                                                    var_factory=var_factory)
        else:
            pass
        connect_pending_injection_bus_variables_emt(device.bus_to, var_factory)

        # Non-VSC branch devices expose bus-side EMT voltage contracts through
        # root external-mapping vars such as ``vf_A`` and ``vt_A``. The symbolic
        # connection propagation updates the live root IO vars through the shared
        # VarFactory graph, but after editor save the saved root external mapping
        # can still point to pre-propagation objects. Re-normalize the saved root
        # contract after the bus connections are attached so validation reads the
        # same propagated symbolic objects that the connection helpers updated.
        if device.device_type == DeviceType.VscDevice:
            pass
        else:
            unify_saved_emt_model_root_contract(device=device)
            synchronize_saved_emt_root_contract_identity(device=device)
            synchronize_saved_emt_root_contract_from_bus(device=device)
    else:
        single_bus_required_mask: list[bool]

        if bus_mask is None:
            if device.bus.is_dc:
                single_bus_required_mask = list([False, False, False, False])
            else:
                single_bus_required_mask = list([False, True, True, True])
        else:
            single_bus_required_mask = bus_mask

        ensure_bus_emt_shell(bus=device.bus,
                             required_mask=single_bus_required_mask,
                             var_factory=var_factory)
        if device.bus.emt_model.empty():
            pass
        else:
            connect_injection_emt(device.bus.emt_model, model, var_factory)
            register_connected_emt_model(bus=device.bus,
                                         device=device,
                                         model=model,
                                         side=EmtBusConnectionSide.BUS)
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
        from_required_mask: list[bool] = list([False, False, False, False])
        to_required_mask: list[bool] = list([False, False, False, False])

        def _get_branch_ac_phase_mask(branch_device: Any) -> list[bool]:
            if branch_device.device_type == DeviceType.LineDevice and branch_device.ys is not None:
                return list([
                    bool(branch_device.ys.phN),
                    bool(branch_device.ys.phA),
                    bool(branch_device.ys.phB),
                    bool(branch_device.ys.phC),
                ])
            else:
                if branch_device.device_type in [DeviceType.Transformer2WDevice, DeviceType.WindingDevice]:
                    phase_set: set[int] = set(int(phase) for phase in branch_device.phases)
                    return list([
                        0 in phase_set,
                        1 in phase_set,
                        2 in phase_set,
                        3 in phase_set,
                    ])
                else:
                    if branch_device.device_type == DeviceType.VscDevice:
                        return list([
                            branch_device.bus_dc_n is not None,
                            True,
                            True,
                            True,
                        ])
                    else:
                        return list([False, True, True, True])

        if not device.bus_from.is_dc:
            from_required_mask = _get_branch_ac_phase_mask(device)
        else:
            pass

        if not device.bus_to.is_dc:
            to_required_mask = _get_branch_ac_phase_mask(device)
        else:
            pass

        attach_emt_model_to_buses(device=device,
                                  model=model,
                                  var_factory=var_factory,
                                  from_mask=from_required_mask,
                                  to_mask=to_required_mask)
    else:
        single_bus_required_mask: list[bool]

        if device.bus.is_dc:
            single_bus_required_mask = list([False, False, False, False])
        else:
            single_bus_required_mask = list([False, True, True, True])

        attach_emt_model_to_buses(device=device,
                                  model=model,
                                  var_factory=var_factory,
                                  bus_mask=single_bus_required_mask)


def set_rms_model(device: Any, model:Block, var_factory: VarFactory):
    """
    Set the RMS model
    :return:
    :rtype:
    """
    # connect bus variables

    if device.device_type in [DeviceType.BranchDevice, DeviceType.LineDevice, DeviceType.Transformer2WDevice, DeviceType.Transformer3WDevice]:
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

    # fill var factoru dict[Dev, List[Var]] with model variables
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
    and registers all its variables in the VarFactory.

    :param device: The power system device (Line, Transformer, Generator, etc.)
    :param model: The mathematical block model of the device
    :param var_factory: Factory to register simulation variables
    :return: None
    """
    # 1. Connect bus variables depending on the device type
    if device.device_type in [DeviceType.BranchDevice,
                              DeviceType.LineDevice,
                              DeviceType.DCLineDevice,
                              DeviceType.HVDCLineDevice,
                              DeviceType.SwitchDevice,
                              DeviceType.SeriesReactanceDevice,
                              DeviceType.UpfcDevice,
                              DeviceType.Transformer2WDevice,
                              DeviceType.Transformer3WDevice]:

        # Bus FROM connection
        bus_from_model = device.bus_from.emt_model
        if not bus_from_model.empty():
            connect_line_emt_from(bus_from_model, model, var_factory)
        else:
            raise ValueError(f"Connection Bus EMT model cannot be empty, initialize {device.bus_from.name} EMT model")

        # Bus TO connection
        bus_to_model = device.bus_to.emt_model
        if not bus_to_model.empty():
            connect_line_emt_to(bus_to_model, model, var_factory)
        else:
            raise ValueError(f"Connection Bus EMT model cannot be empty, initialize {device.bus_to.name} EMT model")

    elif device.device_type == DeviceType.VscDevice:

        # VSC: bus_from is DC, bus_to is AC
        bus_from_model = device.bus_from.emt_model
        if not bus_from_model.empty():
            connect_vsc_emt_from(bus_from_model, model, var_factory, is_dc_bus=device.bus_from.is_dc)
        else:
            raise ValueError(f"Connection Bus EMT model cannot be empty, initialize {device.bus_from.name} EMT model")

        bus_to_model = device.bus_to.emt_model
        if not bus_to_model.empty():
            connect_vsc_emt_to(bus_to_model, model, var_factory, is_dc_bus=device.bus_to.is_dc)
        else:
            raise ValueError(f"Connection Bus EMT model cannot be empty, initialize {device.bus_to.name} EMT model")

    else:
        # Generic device connection (e.g., Loads, Generators connected to a single bus)
        if not device.bus.emt_model.empty():
            connect_injection_emt(device.bus.emt_model, model, var_factory)
        else:
            raise ValueError(f"Connection Bus EMT model cannot be empty, initialize {device.bus.name} EMT model")

    # 2. Unify blocks and register all variables in the VarFactory
    model.unify_blocks()

    for vr in model.algebraic_vars:
        var_factory.register_var(device, vr)

    for vr in model.state_vars:
        var_factory.register_var(device, vr)

    # Added diff_vars for EMT simulations
    for vr in model.diff_vars:
        var_factory.register_var(device, vr)

    # 3. Assign the configured model to the device
    device.emt_model = model
