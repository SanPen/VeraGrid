# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
#
from typing import Any
#
from VeraGridEngine.enumerations import VarPowerFlowReferenceType
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory

from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Utils.Symbolic.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.bus_emt_template import BusEmtTemplate

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

def connect_pending_injection_bus_variables_emt(bus: Any) -> None:
    """
    Connect deferred single-bus EMT devices once one bus shell exists.

    The GUI can assign one injection EMT template before any branch template has
    created the bus EMT shell. In that case the device model is duplicated and
    queued on the bus. When one branch later materializes the bus shell, this
    helper completes the pending bus-to-device EMT connections.

    :param bus: Bus whose pending EMT injection devices must be connected.
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
                connect_injection_emt(bus.emt_model, pending_device.emt_model)
                bus.remove_pending_emt_device(pending_device)


def connect_bus_variables_emt(device: Any,
                              model: Block,
                              var_factory: VarFactory | None,
                              allow_deferred_connection: bool = False) -> None:
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

    branch_devices = [DeviceType.BranchDevice, DeviceType.LineDevice, DeviceType.Transformer2WDevice,
                      DeviceType.Transformer3WDevice, DeviceType.DCLineDevice, DeviceType.VscDevice]

    if device.device_type in branch_devices:
        # Check if using phasor or polar coordinates by looking at bus model outputs
        bus_from = device.bus_from
        # create bus mask to know number of phases
        mask = [False, False, False, False]  # [N, A, B, C]
        if not bus_from.is_dc:
            ys_phase_device_types = {
                DeviceType.LineDevice,
            }
            transformer_phase_device_types = {
                DeviceType.Transformer2WDevice,
                DeviceType.WindingDevice,
            }
            abc_phase_device_types = {
                DeviceType.VscDevice,
                DeviceType.SeriesReactanceDevice,
                DeviceType.UpfcDevice,
                DeviceType.SwitchDevice,
                DeviceType.HVDCLineDevice,
                DeviceType.DCLineDevice,
            }

            if device.device_type in ys_phase_device_types and device.ys is not None:
                mask[0] |= bool(device.ys.phN)
                mask[1] |= bool(device.ys.phA)
                mask[2] |= bool(device.ys.phB)
                mask[3] |= bool(device.ys.phC)
            elif device.device_type in transformer_phase_device_types:
                mask[1] = True
                mask[2] = True
                mask[3] = True
            elif device.device_type in abc_phase_device_types:
                mask[1] = True
                mask[2] = True
                mask[3] = True
            else:
                mask[1] = True
                mask[2] = True
                mask[3] = True

        # modify/create bus block
        if var_factory is not None:
            if bus_from.emt_model.empty():
                bus_from.emt_model = BusEmtTemplate(vf=var_factory,
                                                    mask = mask,
                                                    is_dc = bus_from.is_dc).block
            else:
                if not bus_from.is_dc:
                    # Get the external mapping of the already existing bus EMT model
                    external_mapping = bus_from.emt_model.external_mapping

                    # Detect which AC phases are already present in the existing bus model
                    existing_mask = [False, False, False, False]  # [N, A, B, C]
                    existing_mask[0] = external_mapping.get(VarPowerFlowReferenceType.v_N, None) is not None
                    existing_mask[1] = external_mapping.get(VarPowerFlowReferenceType.v_A, None) is not None
                    existing_mask[2] = external_mapping.get(VarPowerFlowReferenceType.v_B, None) is not None
                    existing_mask[3] = external_mapping.get(VarPowerFlowReferenceType.v_C, None) is not None
                    # Merge the phases required by the already existing bus model and the new device
                    required_mask = [
                        existing_mask[0] or mask[0],
                        existing_mask[1] or mask[1],
                        existing_mask[2] or mask[2],
                        existing_mask[3] or mask[3],
                    ]
                    # Recreate the bus EMT model only if the required phase layout changed
                    if required_mask != existing_mask:
                        bus_from.emt_model = BusEmtTemplate(
                            vf=var_factory,
                            mask=required_mask,
                            is_dc=bus_from.is_dc
                        ).block
                    else:
                        pass

        else:
                raise ValueError("var factory not associated to grid element")

        # connect inputs and outputs
        connect_line_emt_from(device.bus_from.emt_model, model, var_factory)
        connect_pending_injection_bus_variables_emt(device.bus_from)

        # bus to
        bus_to = device.bus_to
        # create bus mask to know number of phases
        mask = [False, False, False, False]  # [N, A, B, C]
        if not bus_to.is_dc:
            ys_phase_device_types = {
                DeviceType.LineDevice,
            }
            transformer_phase_device_types = {
                DeviceType.Transformer2WDevice,
                DeviceType.WindingDevice,
            }
            abc_phase_device_types = {
                DeviceType.VscDevice,
                DeviceType.SeriesReactanceDevice,
                DeviceType.UpfcDevice,
                DeviceType.SwitchDevice,
                DeviceType.HVDCLineDevice,
                DeviceType.DCLineDevice,
            }

            if device.device_type in ys_phase_device_types and device.ys is not None:
                mask[0] |= bool(device.ys.phN)
                mask[1] |= bool(device.ys.phA)
                mask[2] |= bool(device.ys.phB)
                mask[3] |= bool(device.ys.phC)
            elif device.device_type in transformer_phase_device_types:
                mask[1] = True
                mask[2] = True
                mask[3] = True
            elif device.device_type in abc_phase_device_types:
                mask[1] = True
                mask[2] = True
                mask[3] = True
            else:
                mask[1] = True
                mask[2] = True
                mask[3] = True

        # modify/create bus block
        if var_factory is not None:
            if bus_to.emt_model.empty():
                bus_to.emt_model = BusEmtTemplate(vf=var_factory,
                                                    mask=mask,
                                                    is_dc=bus_to.is_dc).block
            else:
                if not bus_to.is_dc:
                    # Get the external mapping of the already existing bus EMT model
                    external_mapping = bus_to.emt_model.external_mapping

                    # Detect which AC phases are already present in the existing bus model
                    existing_mask = [False, False, False, False]  # [N, A, B, C]
                    existing_mask[0] = external_mapping.get(VarPowerFlowReferenceType.v_N, None) is not None
                    existing_mask[1] = external_mapping.get(VarPowerFlowReferenceType.v_A, None) is not None
                    existing_mask[2] = external_mapping.get(VarPowerFlowReferenceType.v_B, None) is not None
                    existing_mask[3] = external_mapping.get(VarPowerFlowReferenceType.v_C, None) is not None
                    # Merge the phases required by the already existing bus model and the new device
                    required_mask = [
                        existing_mask[0] or mask[0],
                        existing_mask[1] or mask[1],
                        existing_mask[2] or mask[2],
                        existing_mask[3] or mask[3],
                    ]
                    # Recreate the bus EMT model only if the required phase layout changed
                    if required_mask != existing_mask:
                        bus_to.emt_model = BusEmtTemplate(
                            vf=var_factory,
                            mask=required_mask,
                            is_dc=bus_to.is_dc
                        ).block
                    else:
                        pass

        else:
            raise ValueError("var factory not associated to grid element")

        # connect inputs and outputs
        connect_line_emt_to(device.bus_to.emt_model, model, var_factory)
        connect_pending_injection_bus_variables_emt(device.bus_to)


    else:
        if device.bus.emt_model.empty():
            if var_factory is not None:
                if device.bus.is_dc:
                    device.bus.emt_model = BusEmtTemplate(
                        vf=var_factory,
                        mask=[False, False, False, False],
                        is_dc=True,
                        name=f"{device.bus.name}_emt_template",
                    ).block
                else:
                    # Template assignment must materialize the real bus shell at
                    # assignment time so the rest of the workflow sees the same
                    # persistent EMT bus variables.
                    device.bus.emt_model = BusEmtTemplate(
                        vf=var_factory,
                        mask=[False, True, True, True],
                        is_dc=False,
                        name=f"{device.bus.name}_emt_template",
                    ).block
            else:
                raise ValueError("var factory not associated to grid element")
        if device.bus.emt_model.empty():
            pass
        else:
            if var_factory is not None:
                connect_injection_emt(device.bus.emt_model, model, var_factory)


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
    # Create a dictionary to map the bus output variable
    # to the corresponding line input variable ("from" side)
    phase_map = {
        VarPowerFlowReferenceType.v_N: VarPowerFlowReferenceType.vf_N,
        VarPowerFlowReferenceType.v_A: VarPowerFlowReferenceType.vf_A,
        VarPowerFlowReferenceType.v_B: VarPowerFlowReferenceType.vf_B,
        VarPowerFlowReferenceType.v_C: VarPowerFlowReferenceType.vf_C,
        VarPowerFlowReferenceType.Vdc: VarPowerFlowReferenceType.Vf_dc,
    }

    # Find the variable pairs that match our mapping
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref in phase_map and phase_map[outp.ref] == inpt.ref
    ]

    # Connect all found pairs
    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

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
    # Create a dictionary to map the bus output variable
    # to the corresponding line input variable ("to" side)
    phase_map = {
        VarPowerFlowReferenceType.v_N: VarPowerFlowReferenceType.vt_N,
        VarPowerFlowReferenceType.v_A: VarPowerFlowReferenceType.vt_A,
        VarPowerFlowReferenceType.v_B: VarPowerFlowReferenceType.vt_B,
        VarPowerFlowReferenceType.v_C: VarPowerFlowReferenceType.vt_C,
        VarPowerFlowReferenceType.Vdc: VarPowerFlowReferenceType.Vt_dc,
    }

    # Find the variable pairs that match our mapping
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref in phase_map and phase_map[outp.ref] == inpt.ref
    ]

    # Connect all found pairs
    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])


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
    # Single-bus EMT devices use the same enum references as the bus shell, so
    # the algorithm only needs to match equal EMT voltage references.
    phase_map = {
        VarPowerFlowReferenceType.v_N: VarPowerFlowReferenceType.v_N,
        VarPowerFlowReferenceType.v_A: VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B: VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C: VarPowerFlowReferenceType.v_C,
        VarPowerFlowReferenceType.Vdc: VarPowerFlowReferenceType.Vdc,
    }

    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref in phase_map and phase_map[outp.ref] == inpt.ref
    ]

    for outp, inpt in pairs:
        var_factory.add_connections([inpt], [outp])

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
        # DC bus: connect Vdc
        dc_map = {
            VarPowerFlowReferenceType.Vdc: VarPowerFlowReferenceType.Vdc
        }
        pairs = [
            (outp, inpt)
            for outp in mdl1.out_vars
            for inpt in mdl2.in_vars
            if outp.ref in dc_map and dc_map[outp.ref] == inpt.ref
        ]
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
        # DC bus: connect Vdc
        dc_map = {
            VarPowerFlowReferenceType.Vdc: VarPowerFlowReferenceType.Vdc
        }
        pairs = [
            (outp, inpt)
            for outp in mdl1.out_vars
            for inpt in mdl2.in_vars
            if outp.ref in dc_map and dc_map[outp.ref] == inpt.ref
        ]
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
