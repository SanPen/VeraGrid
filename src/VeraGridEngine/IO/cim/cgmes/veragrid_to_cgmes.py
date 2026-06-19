# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Union, List, Dict

import numpy as np

import VeraGridEngine.Devices as gcdev
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.Devices import MultiCircuit
from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGridEngine.IO.cim.cgmes.base import get_new_rdfid, form_rdfid
import VeraGridEngine.IO.cim.cgmes.cgmes_assets.cgmes_2_4_15_assets as cgmes24
import VeraGridEngine.IO.cim.cgmes.cgmes_assets.cgmes_3_0_0_assets as cgmes30
from VeraGridEngine.IO.cim.cgmes.cgmes_circuit import CgmesCircuit
from VeraGridEngine.IO.cim.cgmes.cgmes_typing import CGMES_ASSETS, CGMES_POWER_TRANSFORMER_END, is_term
from VeraGridEngine.IO.cim.cgmes.cgmes_create_instances import (create_cgmes_dc_tp_node, create_cgmes_terminal,
                                                                create_cgmes_load_response_char,
                                                                create_cgmes_current_limit,
                                                                create_cgmes_location, create_cgmes_generating_unit,
                                                                create_cgmes_regulating_control,
                                                                create_cgmes_tap_changer_control,
                                                                create_sv_power_flow, create_cgmes_vsc_converter,
                                                                create_cgmes_dc_line_segment, create_cgmes_dc_line,
                                                                create_cgmes_dc_node,
                                                                create_cgmes_acdc_converter_terminal,
                                                                create_cgmes_conform_load_group,
                                                                create_cgmes_operational_limit_type,
                                                                create_cgmes_sub_load_area,
                                                                create_cgmes_non_conform_load_group,
                                                                create_cgmes_nonlinear_sc_point,
                                                                create_sv_shunt_compensator_sections,
                                                                create_sv_status)
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import (RegulatingControlModeKind,
                                                     TransformerControlMode)
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import (SynchronousMachineOperatingMode,
                                                     SynchronousMachineKind,
                                                     LimitTypeKind, OperationalLimitDirectionKind)
from VeraGridEngine.IO.cim.cgmes.cgmes_utils import (find_object_by_uuid,
                                                     find_object_by_vnom,
                                                     find_object_by_cond_eq_uuid,
                                                     get_ohm_values_power_transformer,
                                                     find_object_by_attribute,
                                                     get_voltage_terminal)
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions import compute_zip_power
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import PowerFlowResults
from VeraGridEngine.data_logger import DataLogger
from VeraGridEngine.enumerations import (TapChangerTypes, TapPhaseControl, TapModuleControl, CGMESVersions,
                                         ExternalGridMode, ShuntControlMode, ConverterControlType,
                                         ContingencyOperationTypes, GeneratorControlMode)


def set_declared_cgmes_property(cgmes_object: CGMES_ASSETS,
                                property_name: str,
                                property_value: object,
                                logger: DataLogger,
                                context: str) -> None:
    """
    Assign a CGMES property only when the concrete CGMES object declares it.

    The exporter historically relied on dynamic attribute creation, which hid
    schema mismatches. With slotted CGMES classes, every property write must be
    checked against the declared CIM schema of the concrete class.

    :param cgmes_object: Target CGMES object.
    :param property_name: CIM property name.
    :param property_value: Value to assign.
    :param logger: Data logger for diagnostics.
    :param context: Export context string.
    :return: Nothing.
    :rtype: None
    """
    if property_name in cgmes_object.declared_properties:
        try:
            setattr(cgmes_object, property_name, property_value)
        except AttributeError:
            logger.add_error(msg='Declared CGMES property has no storage',
                             device=cgmes_object.rdfid,
                             device_class=cgmes_object.tpe,
                             device_property=property_name,
                             value=context,
                             expected_value='backed CGMES property storage')
    else:
        logger.add_error(msg='Cannot assign undeclared CGMES property',
                         device=cgmes_object.rdfid,
                         device_class=cgmes_object.tpe,
                         device_property=property_name,
                         value=context,
                         expected_value='declared CGMES property')


def append_cgmes_relation_value(cgmes_object: CGMES_ASSETS,
                                property_name: str,
                                relation_value: CGMES_ASSETS,
                                logger: DataLogger,
                                context: str) -> None:
    """
    Append a relation value while supporting list/scalar relation storage.

    :param cgmes_object: Target CGMES object.
    :param property_name: Relation property name.
    :param relation_value: Relation target object.
    :param logger: Data logger for diagnostics.
    :param context: Export context string.
    :return: Nothing.
    :rtype: None
    """
    if property_name in cgmes_object.declared_properties:
        current_value: object = object.__getattribute__(cgmes_object, property_name)
        if isinstance(current_value, list):
            current_value.append(relation_value)
        else:
            set_declared_cgmes_property(cgmes_object=cgmes_object,
                                        property_name=property_name,
                                        property_value=relation_value,
                                        logger=logger,
                                        context=context)
    else:
        logger.add_error(msg='Cannot append undeclared CGMES relation',
                         device=cgmes_object.rdfid,
                         device_class=cgmes_object.tpe,
                         device_property=property_name,
                         value=context,
                         expected_value='declared CGMES relation')


def create_limits_for_terminal(termnl: CGMES_ASSETS,
                               rate_and_type: List[tuple[float, CGMES_ASSETS]],
                               cgmes_model: CgmesCircuit,
                               ver: CGMESVersions,
                               logger: DataLogger) -> None:
    """
    Create current limits for one terminal.

    :param termnl: Terminal object.
    :param rate_and_type: Sequence of (rate_mw, op_limit_type).
    :param cgmes_model: CGMES model.
    :param ver: CGMES version.
    :param logger: DataLogger
    :return: None
    """
    for rate_mw, op_limit_type in rate_and_type:
        if rate_mw != 0.0:
            create_cgmes_current_limit(terminal=termnl,
                                       rate_mw=rate_mw,
                                       op_limit_type=op_limit_type,
                                       cgmes_model=cgmes_model,
                                       ver=ver,
                                       logger=logger)
        else:
            pass


def find_fallback_voltage_level_for_bus(cgmes_model: CgmesCircuit,
                                        bus: gcdev.Bus,
                                        logger: DataLogger) -> CGMES_ASSETS | None:
    """
    Find a fallback VoltageLevel for buses without a direct VoltageLevel link.

    This keeps boundary buses serializable in TP by ensuring they can be
    assigned to a ConnectivityNodeContainer.

    :param cgmes_model: CgmesModel
    :param bus: gcdev Bus
    :param logger: DataLogger
    :return: VoltageLevel object or None
    """
    if len(cgmes_model.cgmes_assets.VoltageLevel_list) == 0:
        return None

    # Prefer a voltage level with matching nominal voltage to keep topology coherent.
    for voltage_level in cgmes_model.cgmes_assets.VoltageLevel_list:
        if voltage_level.BaseVoltage is not None:
            if np.isclose(voltage_level.BaseVoltage.nominalVoltage, bus.Vnom):
                return voltage_level

    fallback_voltage_level = cgmes_model.cgmes_assets.VoltageLevel_list[0]
    logger.add_warning(
        msg='No VoltageLevel matched bus nominal voltage; using first VoltageLevel as fallback',
        device=bus.idtag,
        device_class=bus.device_type.value,
        value=bus.Vnom,
        expected_value=fallback_voltage_level.BaseVoltage.nominalVoltage
        if fallback_voltage_level.BaseVoltage is not None else None,
        comment="find_fallback_voltage_level_for_bus()"
    )
    return fallback_voltage_level


def purge_connectivity_nodes_for_cgmes_v3(cgmes_model: CgmesCircuit,
                                          logger: DataLogger) -> None:
    """
    Remove ConnectivityNode objects from CGMES v3 export model.

    This prevents RDFID collisions between TopologicalNode and ConnectivityNode
    during roundtrip parsing, which can otherwise break deterministic bus IDs.

    :param cgmes_model: Target CGMES model.
    :param logger: Data logger.
    :return: Nothing.
    :rtype: None
    """
    connectivity_nodes: list[CGMES_ASSETS] = list(cgmes_model.cgmes_assets.ConnectivityNode_list)
    if len(connectivity_nodes) == 0:
        return
    else:
        pass

    removed_count: int = 0
    connectivity_node: CGMES_ASSETS
    for connectivity_node in connectivity_nodes:
        if connectivity_node.rdfid in cgmes_model.all_objects_dict:
            del cgmes_model.all_objects_dict[connectivity_node.rdfid]
        else:
            pass
        removed_count += 1

    cgmes_model.cgmes_assets.ConnectivityNode_list = list()
    if "ConnectivityNode" in cgmes_model.elements_by_type:
        cgmes_model.elements_by_type["ConnectivityNode"] = list()
    else:
        pass

    logger.add_warning(
        msg='Purged ConnectivityNode objects for CGMES v3 deterministic TP export',
        value=removed_count,
        comment="purge_connectivity_nodes_for_cgmes_v3()"
    )


def populate_cgmes_load_response_characteristic(load_response: CGMES_ASSETS,
                                                active_power: float,
                                                active_current: float,
                                                active_impedance: float,
                                                reactive_power: float,
                                                reactive_current: float,
                                                reactive_impedance: float) -> None:
    """
    Populate one CGMES LoadResponseCharacteristic from selected export values.

    :param load_response: Target load-response object.
    :param active_power: Constant-power active component.
    :param active_current: Constant-current active component.
    :param active_impedance: Constant-impedance active component.
    :param reactive_power: Constant-power reactive component.
    :param reactive_current: Constant-current reactive component.
    :param reactive_impedance: Constant-impedance reactive component.
    :return: Nothing.
    :rtype: None
    """
    total_active: float = float(active_power + active_current + active_impedance)
    total_reactive: float = float(reactive_power + reactive_current + reactive_impedance)

    if total_active != 0.0:
        load_response.pConstantPower = np.round(active_power / total_active, 4)
        load_response.pConstantCurrent = np.round(active_current / total_active, 4)
        load_response.pConstantImpedance = np.round(active_impedance / total_active, 4)
    else:
        load_response.pConstantPower = 1.0
        load_response.pConstantCurrent = 0.0
        load_response.pConstantImpedance = 0.0

    if total_reactive != 0.0:
        load_response.qConstantPower = np.round(reactive_power / total_reactive, 4)
        load_response.qConstantCurrent = np.round(reactive_current / total_reactive, 4)
        load_response.qConstantImpedance = np.round(reactive_impedance / total_reactive, 4)
    else:
        load_response.qConstantPower = 1.0
        load_response.qConstantCurrent = 0.0
        load_response.qConstantImpedance = 0.0


def apply_time_index_to_tap_changer_control(tap_changer: CGMES_ASSETS,
                                            mc_elm: gcdev.Transformer2W | gcdev.Winding,
                                            logger: DataLogger,
                                            t_idx: int | None) -> None:
    """
    Overwrite TapChangerControl targets using the selected export time index.

    :param tap_changer: CGMES tap changer.
    :param mc_elm: Source VeraGrid transformer or winding.
    :param logger: Data logger.
    :param t_idx: Optional profile index.
    :return: Nothing.
    :rtype: None
    """
    tap_changer_control: CGMES_ASSETS | None = tap_changer.TapChangerControl
    if tap_changer_control is None:
        return
    else:
        pass

    if tap_changer_control.mode == RegulatingControlModeKind.voltage:
        voltage: float | None = get_voltage_terminal(tap_changer_control.Terminal, logger)
        if voltage is None:
            return
        else:
            tap_changer_control.targetValue = mc_elm.get_vset_at(t_idx) * voltage
    elif tap_changer_control.mode == RegulatingControlModeKind.activePower:
        tap_changer_control.targetValue = mc_elm.get_Pset_at(t_idx)
    else:
        pass


def get_transformer_tap_values_for_cgmes_export(mc_elm: gcdev.Transformer2W | gcdev.Winding,
                                                logger: DataLogger,
                                                t_idx: int | None = None) -> tuple[int, int, int, int, float, int]:
    """
    Return TapChanger values for CGMES export while preserving fixed tap modules.

    For fixed non-regulating transformers with off-nominal tap modules, this
    temporarily computes tap position using VoltageRegulation mode so exported
    RatioTapChanger step encodes the actual ratio.

    :param mc_elm: Transformer2W or Winding
    :param logger: DataLogger
    :return: lowStep, highStep, normalStep, neutralStep, stepVoltageIncrement, step
    """
    tap_changer = mc_elm.tap_changer
    original_type = tap_changer.tc_type
    original_position = tap_changer.tap_position

    low, high, normal, neutral, step_voltage_increment, step = tap_changer.get_cgmes_values()

    if original_type in (TapChangerTypes.NoRegulation, TapChangerTypes.VoltageRegulation):
        target_tap_module = float(mc_elm.get_tap_module_at(t_idx))
        if np.isclose(target_tap_module, 1.0):
            return low, high, normal, neutral, step_voltage_increment, step

        if original_type == TapChangerTypes.NoRegulation:
            tap_changer.tc_type = TapChangerTypes.VoltageRegulation
        exported_tap_module = tap_changer.set_tap_module(tap_module=target_tap_module)
        low, high, normal, neutral, step_voltage_increment, step = tap_changer.get_cgmes_values()

        step_delta = int(step - neutral)
        if step_delta == 0:
            if target_tap_module > 1.0 and step < high:
                step = int(step + 1)
            elif target_tap_module < 1.0 and step > low:
                step = int(step - 1)
            elif step < high:
                step = int(step + 1)
            elif step > low:
                step = int(step - 1)
            else:
                step = int(step)
            step_delta = int(step - neutral)

        if step_delta != 0:
            target_dv = (1.0 - (1.0 / target_tap_module)) / float(step_delta)
            if target_dv > 0.0:
                step_voltage_increment = round(target_dv * 100.0, 6)
            else:
                logger.add_warning(
                    msg='Computed non-positive tap increment for fixed tap export; keeping original increment',
                    device=mc_elm.idtag,
                    device_class=mc_elm.device_type.value,
                    value=target_dv,
                    expected_value='> 0.0'
                )
        else:
            logger.add_warning(
                msg='Fixed tap module could not be encoded in CGMES step space',
                device=mc_elm.idtag,
                device_class=mc_elm.device_type.value,
                value=target_tap_module,
                expected_value='non-neutral step'
            )

        if not np.isclose(exported_tap_module, target_tap_module, atol=1e-4):
            logger.add_warning(
                msg='Fixed tap module was discretized for CGMES export',
                device=mc_elm.idtag,
                device_class=mc_elm.device_type.value,
                value=exported_tap_module,
                expected_value=target_tap_module
            )

    # Restore original object state.
    tap_changer.tc_type = original_type
    tap_changer.tap_position = original_position

    return low, high, normal, neutral, step_voltage_increment, step


def should_export_tap_changer(mc_elm: gcdev.Transformer2W | gcdev.Winding,
                              t_idx: int | None = None) -> bool:
    """
    Determine if a transformer or winding tap changer should be exported.

    Default fixed taps (tap module == 1 and tap phase == 0) with no regulation
    can be omitted to reduce file size and export overhead. Any non-default or
    regulating tap state must be exported for roundtrip fidelity.

    :param mc_elm: MultiCircuit Transformer2W or Winding
    :return: True when tap changer data should be exported
    """
    if mc_elm.tap_changer.tc_type != TapChangerTypes.NoRegulation:
        return True
    else:
        if not np.isclose(float(mc_elm.get_tap_module_at(t_idx)), 1.0):
            return True
        else:
            if not np.isclose(float(mc_elm.get_tap_phase_at(t_idx)), 0.0):
                return True
            else:
                return False


def create_cgmes_tap_changer_for_transformer_end(mc_elm: gcdev.Transformer2W | gcdev.Winding,
                                                 pte: CGMES_POWER_TRANSFORMER_END,
                                                 cgmes_model: CgmesCircuit,
                                                 ver: CGMESVersions,
                                                 logger: DataLogger,
                                                 t_idx: int | None = None) -> None:
    """
    Create and add tap changer objects for a transformer end.

    The helper supports both two-winding transformer objects and individual
    three-winding transformer windings. It exports the tap changer in EQ/SSH/SV
    so import can rebuild off-nominal fixed taps and regulation data.

    :param mc_elm: MultiCircuit Transformer2W or Winding
    :param pte: CGMES PowerTransformerEnd associated with the tap changer
    :param cgmes_model: CGMES model
    :param ver: CGMES version
    :param logger: logger
    :return: None
    """
    if not should_export_tap_changer(mc_elm=mc_elm, t_idx=t_idx):
        return
    else:
        tcc_mode = RegulatingControlModeKind.voltage
        tcc_enabled = False

    if mc_elm.tap_changer.tc_type == TapChangerTypes.NoRegulation:
        if ver == CGMESVersions.v2_4_15:
            tap_changer = cgmes24.RatioTapChanger(rdfid=get_new_rdfid())
        elif ver == CGMESVersions.v3_0_0:
            tap_changer = cgmes30.RatioTapChanger(rdfid=get_new_rdfid())
        else:
            raise NotImplemented()

    elif mc_elm.tap_changer.tc_type == TapChangerTypes.VoltageRegulation:
        if ver == CGMESVersions.v2_4_15:
            tap_changer = cgmes24.RatioTapChanger(rdfid=get_new_rdfid())
        elif ver == CGMESVersions.v3_0_0:
            tap_changer = cgmes30.RatioTapChanger(rdfid=get_new_rdfid())
        else:
            raise NotImplemented()

        if mc_elm.get_tap_module_control_mode_at(t_idx) != TapModuleControl.fixed:
            tcc_enabled = True
        else:
            tcc_enabled = False

    elif mc_elm.tap_changer.tc_type == TapChangerTypes.Symmetrical:
        if ver == CGMESVersions.v2_4_15:
            tap_changer = cgmes24.PhaseTapChangerSymmetrical(rdfid=get_new_rdfid())
        elif ver == CGMESVersions.v3_0_0:
            tap_changer = cgmes30.PhaseTapChangerSymmetrical(rdfid=get_new_rdfid())
        else:
            raise NotImplemented()

        if mc_elm.get_tap_phase_control_mode_at(t_idx) != TapPhaseControl.fixed:
            tcc_enabled = True
        else:
            tcc_enabled = False
        tcc_mode = RegulatingControlModeKind.activePower

    elif mc_elm.tap_changer.tc_type == TapChangerTypes.Asymmetrical:
        if ver == CGMESVersions.v2_4_15:
            tap_changer = cgmes24.PhaseTapChangerAsymmetrical(rdfid=get_new_rdfid())
        elif ver == CGMESVersions.v3_0_0:
            tap_changer = cgmes30.PhaseTapChangerAsymmetrical(rdfid=get_new_rdfid())
        else:
            raise NotImplemented()

        if (mc_elm.get_tap_module_control_mode_at(t_idx) != TapModuleControl.fixed
                or mc_elm.get_tap_phase_control_mode_at(t_idx) != TapPhaseControl.fixed):
            tcc_enabled = True
        else:
            tcc_enabled = False
        tcc_mode = RegulatingControlModeKind.activePower

    else:
        logger.add_error(msg='No TapChangerType found for TapChanger',
                         device=mc_elm.tap_changer,
                         device_class=mc_elm.device_type.value,
                         value=mc_elm.tap_changer)
        return

    tap_changer.name = f'_tc_{mc_elm.name}'
    tap_changer.shortName = f'_tc_{mc_elm.name}'
    tap_changer.neutralU = pte.ratedU
    tap_changer.TransformerEnd = pte

    (tap_changer.lowStep,
     tap_changer.highStep,
     tap_changer.normalStep,
     tap_changer.neutralStep,
     voltage_incr,
     tap_changer.step) = get_transformer_tap_values_for_cgmes_export(
        mc_elm=mc_elm,
        logger=logger,
        t_idx=t_idx
    )

    if isinstance(tap_changer, (cgmes24.RatioTapChanger, cgmes30.RatioTapChanger)):
        tap_changer.stepVoltageIncrement = voltage_incr
    elif isinstance(tap_changer, (cgmes24.PhaseTapChangerSymmetrical,
                                  cgmes30.PhaseTapChangerSymmetrical,
                                  cgmes24.PhaseTapChangerAsymmetrical,
                                  cgmes30.PhaseTapChangerAsymmetrical,
                                  cgmes24.PhaseTapChangerNonLinear,
                                  cgmes30.PhaseTapChangerNonLinear)):
        tap_changer.voltageStepIncrement = voltage_incr
        tap_changer.xMin = mc_elm.X
        tap_changer.xMax = mc_elm.X
    else:
        logger.add_error(msg='stepVoltageIncrement cannot be filled for TapChanger',
                         device=mc_elm,
                         device_class=mc_elm.device_type.value,
                         value=mc_elm.idtag,
                         comment='create_cgmes_tap_changer_for_transformer_end()')

    if isinstance(tap_changer, (cgmes24.PhaseTapChangerAsymmetrical, cgmes30.PhaseTapChangerAsymmetrical)):
        tap_changer.windingConnectionAngle = mc_elm.tap_changer.asymmetry_angle
    else:
        pass

    tap_changer.ltcFlag = True
    tap_changer.TapChangerControl = create_cgmes_tap_changer_control(
        tap_changer=tap_changer,
        tcc_mode=tcc_mode,
        tcc_enabled=tcc_enabled,
        mc_trafo=mc_elm,
        cgmes_model=cgmes_model,
        ver=ver,
        logger=logger
    )
    apply_time_index_to_tap_changer_control(
        tap_changer=tap_changer,
        mc_elm=mc_elm,
        logger=logger,
        t_idx=t_idx
    )
    tap_changer.tculControlMode = TransformerControlMode.volt
    tap_changer.controlEnabled = tcc_enabled

    if ver == CGMESVersions.v2_4_15:
        sv_tap_step = cgmes24.SvTapStep(rdfid=get_new_rdfid(), tpe='SvTapStep')
    elif ver == CGMESVersions.v3_0_0:
        sv_tap_step = cgmes30.SvTapStep(rdfid=get_new_rdfid(), tpe='SvTapStep')
    else:
        raise NotImplemented()

    sv_tap_step.position = tap_changer.step
    sv_tap_step.TapChanger = tap_changer

    cgmes_model.add(tap_changer)
    cgmes_model.add(sv_tap_step)


def find_terminals_by_conducting_equipment_uuid(cgmes_model: CgmesCircuit,
                                                cond_eq_target_uuid: str) -> list:
    """
    Return every terminal associated to the given conducting-equipment UUID.
    """
    terminals = []
    for terminal in cgmes_model.cgmes_assets.Terminal_list:
        cond_eq = getattr(terminal, "ConductingEquipment", None)
        if cond_eq is not None and getattr(cond_eq, "uuid", None) == cond_eq_target_uuid:
            terminals.append(terminal)
    return terminals


def get_vsc_voltage_target(gc_vsc: gcdev.VSC, t_idx: int | None = None) -> float:
    """
    Derive the VSC AC-side target voltage in per unit from the VeraGrid controls.
    """
    if gc_vsc.get_control1_at(t_idx) in (ConverterControlType.Vm_ac, ConverterControlType.Vm_dc):
        return float(gc_vsc.get_control1_val_at(t_idx))
    if gc_vsc.get_control2_at(t_idx) in (ConverterControlType.Vm_ac, ConverterControlType.Vm_dc):
        return float(gc_vsc.get_control2_val_at(t_idx))
    if gc_vsc.bus_to is not None and gc_vsc.bus_to.Vnom > 0.0:
        return 1.0
    return 1.0


def get_vsc_power_target(gc_vsc: gcdev.VSC, t_idx: int | None = None) -> float:
    """
    Derive the VSC active-power target in MW from the VeraGrid controls.
    """
    if gc_vsc.get_control1_at(t_idx) in (ConverterControlType.Pac, ConverterControlType.Pdc):
        return float(gc_vsc.get_control1_val_at(t_idx))
    if gc_vsc.get_control2_at(t_idx) in (ConverterControlType.Pac, ConverterControlType.Pdc):
        return float(gc_vsc.get_control2_val_at(t_idx))
    return 0.0


def get_or_create_dc_topological_node(cgmes_model: CgmesCircuit,
                                      dc_bus: gcdev.Bus,
                                      ver: CGMESVersions,
                                      logger: DataLogger):
    """
    Reuse the exported DC topological node for a DC bus or create it if missing.
    """
    for dc_tp in cgmes_model.cgmes_assets.DCTopologicalNode_list:
        if dc_tp.name == dc_bus.name and dc_tp.description == dc_bus.code:
            return dc_tp

    return create_cgmes_dc_tp_node(
        tp_name=dc_bus.name,
        tp_description=dc_bus.code,
        cgmes_model=cgmes_model,
        ver=ver,
        logger=logger
    )


def get_or_create_dc_node(cgmes_model: CgmesCircuit,
                          dc_bus: gcdev.Bus,
                          dc_tp,
                          dc_equipment_container,
                          ver: CGMESVersions,
                          logger: DataLogger):
    """
    Reuse the exported DC node for a DC bus or create it if missing.
    """
    for dc_node in cgmes_model.cgmes_assets.DCNode_list:
        if dc_node.name == dc_bus.name and dc_node.description == dc_bus.code:
            return dc_node

    return create_cgmes_dc_node(
        cn_name=dc_bus.name,
        cn_description=dc_bus.code,
        cgmes_model=cgmes_model,
        dc_tp=dc_tp,
        dc_ec=dc_equipment_container,
        ver=ver,
        logger=logger
    )


def get_or_create_external_network_injection(multicircuit_model: MultiCircuit,
                                             cgmes_model: CgmesCircuit,
                                             ver: CGMESVersions,
                                             logger: DataLogger,
                                             t_idx: int | None = None):
    """
    Export every VeraGrid external grid as an ExternalNetworkInjection.
    """
    for mc_elm in multicircuit_model.external_grids:
        if ver == CGMESVersions.v2_4_15:
            eni = cgmes24.ExternalNetworkInjection(rdfid=form_rdfid(mc_elm.idtag))
        elif ver == CGMESVersions.v3_0_0:
            eni = cgmes30.ExternalNetworkInjection(rdfid=form_rdfid(mc_elm.idtag))
        else:
            raise NotImplemented()

        eni.description = mc_elm.code
        eni.name = mc_elm.name
        eni.p = mc_elm.get_P_at(t_idx)
        eni.q = mc_elm.get_Q_at(t_idx)
        eni.maxP = mc_elm.get_P_at(t_idx)
        eni.minP = mc_elm.get_P_at(t_idx)
        eni.maxQ = mc_elm.get_Q_at(t_idx)
        eni.minQ = mc_elm.get_Q_at(t_idx)
        set_declared_cgmes_property(
            cgmes_object=eni,
            property_name="BaseVoltage",
            property_value=find_object_by_vnom(cgmes_model=cgmes_model,
                                               object_list=cgmes_model.cgmes_assets.BaseVoltage_list,
                                               target_vnom=mc_elm.bus.Vnom),
            logger=logger,
            context="get_cgmes_external_network_injections()"
        )
        eni.Terminals = create_cgmes_terminal(mc_elm.bus, None, eni, cgmes_model, ver, logger)

        if mc_elm.mode == ExternalGridMode.VD:
            raise RuntimeError(
                "ExternalGrid VD control export requires a dedicated path; "
                "Generator-style RegulatingControl expects Vset and is not valid for ExternalGrid."
            )
        else:
            eni.controlEnabled = False
            eni.referencePriority = 0

        cgmes_model.add(eni)


def convert_vsc_devices_to_cgmes(multicircuit_model: MultiCircuit,
                                 cgmes_model: CgmesCircuit,
                                 ver: CGMESVersions,
                                 logger: DataLogger,
                                 t_idx: int | None = None) -> None:
    """
    Export native VeraGrid VSC devices to CGMES VsConverter objects.
    """
    for gc_vsc in multicircuit_model.vsc_devices:
        if gc_vsc.bus_from is None or gc_vsc.bus_to is None:
            logger.add_error(msg='VSC export skipped due missing AC/DC buses',
                             device=gc_vsc.idtag,
                             device_class=gc_vsc.device_type.value)
            continue

        p_set = get_vsc_power_target(gc_vsc=gc_vsc, t_idx=t_idx)
        v_set = get_vsc_voltage_target(gc_vsc=gc_vsc, t_idx=t_idx)
        vs_converter, dc_conv_unit = create_cgmes_vsc_converter(
            cgmes_model=cgmes_model,
            gc_vsc=gc_vsc,
            p_set=p_set,
            v_set=v_set,
            target_upcc_base_voltage=(gc_vsc.bus_to.Vnom
                                      if gc_vsc.bus_to is not None and gc_vsc.bus_to.Vnom > 0.0
                                      else None),
            ver=ver,
            logger=logger
        )

        if gc_vsc.bus_to.substation is not None:
            substation = find_object_by_uuid(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.Substation_list,
                target_uuid=gc_vsc.bus_to.substation.idtag
            )
            if isinstance(substation, cgmes_model.assets.Substation):
                dc_conv_unit.Substation = substation

        dc_tp = get_or_create_dc_topological_node(cgmes_model, gc_vsc.bus_from, ver, logger)
        dc_node = get_or_create_dc_node(cgmes_model, gc_vsc.bus_from, dc_tp, dc_conv_unit, ver, logger)

        create_cgmes_acdc_converter_terminal(
            cgmes_model=cgmes_model,
            mc_dc_bus=gc_vsc.bus_from,
            seq_num=2,
            dc_node=dc_node,
            dc_cond_eq=vs_converter,
            ver=ver,
            logger=logger
        )
        create_cgmes_terminal(
            cgmes_model=cgmes_model,
            mc_bus=gc_vsc.bus_to,
            seq_num=None,
            cond_eq=vs_converter,
            ver=ver,
            logger=logger
        )

        if gc_vsc.bus_dc_n is not None:
            logger.add_warning(
                msg='Native VSC export currently uses one DC pole; negative DC pole is not exported separately',
                device=gc_vsc.idtag,
                device_class=gc_vsc.device_type.value,
                value=gc_vsc.bus_dc_n.idtag
            )


def convert_dc_lines_to_cgmes(multicircuit_model: MultiCircuit,
                              cgmes_model: CgmesCircuit,
                              ver: CGMESVersions,
                              logger: DataLogger) -> None:
    """
    Export native VeraGrid DC lines to CGMES DCLine/DCLineSegment objects.
    """
    for dc_line_model in multicircuit_model.dc_lines:
        if dc_line_model.bus_from is None or dc_line_model.bus_to is None:
            logger.add_error(msg='DC line export skipped due missing buses',
                             device=dc_line_model.idtag,
                             device_class=dc_line_model.device_type.value)
            continue

        dc_line = create_cgmes_dc_line(cgmes_model=cgmes_model, ver=ver, logger=logger)
        dc_line.name = dc_line_model.name
        dc_line.description = dc_line_model.code

        dc_tp_1 = get_or_create_dc_topological_node(cgmes_model, dc_line_model.bus_from, ver, logger)
        dc_tp_2 = get_or_create_dc_topological_node(cgmes_model, dc_line_model.bus_to, ver, logger)
        dc_node_1 = get_or_create_dc_node(cgmes_model, dc_line_model.bus_from, dc_tp_1, dc_line, ver, logger)
        dc_node_2 = get_or_create_dc_node(cgmes_model, dc_line_model.bus_to, dc_tp_2, dc_line, ver, logger)

        create_cgmes_dc_line_segment(cgmes_model=cgmes_model,
                                     mc_elm=dc_line_model,
                                     dc_tp_1=dc_tp_1,
                                     dc_node_1=dc_node_1,
                                     dc_tp_2=dc_tp_2,
                                     dc_node_2=dc_node_2,
                                     eq_cont=dc_line,
                                     ver=ver,
                                     logger=logger)


def export_sv_statuses(gc_model: MultiCircuit,
                       cgmes_model: CgmesCircuit,
                       ver: CGMESVersions,
                       t_idx: int | None = None) -> None:
    """
    Export SvStatus for every source object that maps directly to a CGMES conducting equipment.
    """
    devices = []
    devices.extend(gc_model.lines)
    devices.extend(gc_model.transformers2w)
    devices.extend(gc_model.transformers3w)
    devices.extend(gc_model.vsc_devices)
    devices.extend(gc_model.dc_lines)
    devices.extend(gc_model.hvdc_lines)
    devices.extend(gc_model.generators)
    devices.extend(gc_model.loads)
    devices.extend(gc_model.external_grids)
    devices.extend(gc_model.shunts)
    devices.extend(gc_model.controllable_shunts)
    devices.extend(gc_model.switch_devices)

    exported_ids = set()
    for device in devices:
        if device.idtag in exported_ids:
            continue
        exported_ids.add(device.idtag)
        cgmes_obj = cgmes_model.all_objects_dict.get(form_rdfid(device.idtag))
        if cgmes_obj is None:
            continue
        create_sv_status(
            cgmes_model=cgmes_model,
            in_service=int(bool(device.get_active_at(t_idx))),
            cgmes_conducting_equipment=cgmes_obj,
            ver=ver
        )
    return


def get_cgmes_geograpical_regions(multi_circuit_model: MultiCircuit,
                                  cgmes_model: CgmesCircuit,
                                  ver: CGMESVersions,
                                  logger: DataLogger):
    """

    :param multi_circuit_model:
    :param cgmes_model:
    :param ver:
    :param logger:
    :return:
    """
    for mc_class in [multi_circuit_model.countries, multi_circuit_model.areas]:
        for mc_elm in mc_class:

            if ver == CGMESVersions.v2_4_15:
                geo_region = cgmes24.GeographicalRegion(rdfid=form_rdfid(mc_elm.idtag))
            elif ver == CGMESVersions.v3_0_0:
                geo_region = cgmes30.GeographicalRegion(rdfid=form_rdfid(mc_elm.idtag))
            else:
                raise NotImplemented()

            geo_region.name = mc_elm.name
            geo_region.description = mc_elm.code
            cgmes_model.add(geo_region)

    if len(cgmes_model.cgmes_assets.GeographicalRegion_list) == 0:
        logger.add_error(
            msg='Country or Area is not defined and GeographicalRegion cannot be exported',
            device_class="GeographicalRegion",
            comment="The CGMES export will not be valid!")


def get_cgmes_sub_geographical_regions(multi_circuit_model: MultiCircuit,
                                       cgmes_model: CgmesCircuit,
                                       ver: CGMESVersions,
                                       logger: DataLogger):
    """

    :param multi_circuit_model:
    :param cgmes_model:
    :param ver:
    :param logger:
    :return:
    """

    for mc_class in [multi_circuit_model.communities,
                     multi_circuit_model.zones]:
        for mc_elm in mc_class:
            # object_template = cgmes_model.get_class_type("SubGeographicalRegion")
            # sub_geo_region = object_template(rdfid=form_rdfid(mc_elm.idtag))

            if ver == CGMESVersions.v2_4_15:
                sub_geo_region = cgmes24.SubGeographicalRegion(rdfid=form_rdfid(mc_elm.idtag))
            elif ver == CGMESVersions.v3_0_0:
                sub_geo_region = cgmes30.SubGeographicalRegion(rdfid=form_rdfid(mc_elm.idtag))
            else:
                raise NotImplemented()

            sub_geo_region.name = mc_elm.name
            sub_geo_region.description = mc_elm.code

            region_id = ""
            if hasattr(mc_elm, "country"):
                if mc_elm.country:
                    region_id = mc_elm.country.idtag
            elif hasattr(mc_elm, "area"):
                if mc_elm.area:
                    region_id = mc_elm.area.idtag

            region = find_object_by_uuid(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.GeographicalRegion_list,
                target_uuid=region_id
            )
            if isinstance(region, cgmes_model.assets.GeographicalRegion):
                sub_geo_region.Region = region
            else:
                if len(cgmes_model.cgmes_assets.GeographicalRegion_list) > 0:
                    sub_geo_region.Region = cgmes_model.cgmes_assets.GeographicalRegion_list[0]
                else:
                    sub_geo_region.Region = None

                logger.add_warning(msg='GeographicalRegion not found for SubGeographicalRegion',
                                   device_class="SubGeographicalRegion")

            cgmes_model.add(sub_geo_region)

    if len(cgmes_model.cgmes_assets.SubGeographicalRegion_list) == 0:
        logger.add_error(
            msg='Community or Zone is not defined and SubGeographicalRegion cannot be exported',
            device_class="SubGeographicalRegion",
            comment="The CGMES export will not be valid!")


def get_base_voltage_from_boundary(cgmes_model: CgmesCircuit,
                                   vnom: float,
                                   ver: CGMESVersions, ):
    """

    :param cgmes_model:
    :param vnom:
    :param ver:
    :return:
    """
    bv_list = cgmes_model.elements_by_type_boundary.get("BaseVoltage")
    if bv_list is not None:
        for bv in bv_list:
            if bv.nominalVoltage == vnom:
                return bv
    return None


def get_cgmes_base_voltages(multi_circuit_model: MultiCircuit,
                            cgmes_model: CgmesCircuit,
                            ver: CGMESVersions,
                            logger: DataLogger) -> None:
    """

    :param multi_circuit_model:
    :param cgmes_model:
    :param ver:
    :param logger:
    :return:
    """
    base_volt_set = set()
    for bus in multi_circuit_model.buses:

        if bus.Vnom <= 0.0:
            logger.add_info(
                msg='Skipping BaseVoltage export for non-positive nominal voltage bus',
                device=bus.idtag,
                device_class=bus.device_type.value,
                value=bus.Vnom
            )
            continue

        if bus.Vnom not in base_volt_set and get_base_voltage_from_boundary(cgmes_model, bus.Vnom, ver) is None:
            base_volt_set.add(bus.Vnom)

            new_rdf_id = get_new_rdfid()
            # object_template = cgmes_model.get_class_type("BaseVoltage")
            # base_volt = object_template(rdfid=new_rdf_id)

            if ver == CGMESVersions.v2_4_15:
                base_volt = cgmes24.BaseVoltage(rdfid=new_rdf_id)
            elif ver == CGMESVersions.v3_0_0:
                base_volt = cgmes30.BaseVoltage(rdfid=new_rdf_id)
            else:
                raise NotImplemented()

            base_volt.name = f'_BV_{int(bus.Vnom)}'
            base_volt.nominalVoltage = bus.Vnom

            cgmes_model.add(base_volt)
    return


def get_cgmes_substations(multi_circuit_model: MultiCircuit,
                          cgmes_model: CgmesCircuit,
                          ver: CGMESVersions,
                          logger: DataLogger) -> None:
    """

    :param multi_circuit_model:
    :param cgmes_model:
    :param ver:
    :param logger:
    :return:
    """
    for mc_elm in multi_circuit_model.substations:
        # object_template = cgmes_model.get_class_type("Substation")
        # substation = object_template(rdfid=form_rdfid(mc_elm.idtag))

        if ver == CGMESVersions.v2_4_15:
            substation = cgmes24.Substation(rdfid=form_rdfid(mc_elm.idtag))
        elif ver == CGMESVersions.v3_0_0:
            substation = cgmes30.Substation(rdfid=form_rdfid(mc_elm.idtag))
        else:
            raise NotImplemented()

        substation.name = mc_elm.name
        region = find_object_by_uuid(
            cgmes_model=cgmes_model,
            object_list=cgmes_model.cgmes_assets.SubGeographicalRegion_list,
            target_uuid=mc_elm.community.idtag if mc_elm.community is not None else ""
            # TODO Community.idtag!
        )

        if isinstance(region, cgmes_model.assets.GeographicalRegion):
            substation.Region = region
        else:
            if len(cgmes_model.cgmes_assets.SubGeographicalRegion_list) > 0:
                substation.Region = cgmes_model.cgmes_assets.SubGeographicalRegion_list[0]
            else:
                substation.Region = None
                logger.add_warning(msg='Region not found for Substation',
                                   device_class="SubGeographicalRegion")

        create_cgmes_location(cgmes_model=cgmes_model,
                              device=substation,
                              longitude=mc_elm.longitude,
                              latitude=mc_elm.latitude,
                              ver=ver,
                              logger=logger)

        cgmes_model.add(substation)


def get_cgmes_voltage_levels(multi_circuit_model: MultiCircuit,
                             cgmes_model: CgmesCircuit,
                             ver: CGMESVersions,
                             logger: DataLogger) -> None:
    """

    :param multi_circuit_model:
    :param cgmes_model:
    :param ver:
    :param logger:
    :return:
    """
    for mc_elm in multi_circuit_model.voltage_levels:

        # object_template = cgmes_model.get_class_type("VoltageLevel")
        # vl = object_template(rdfid=form_rdfid(mc_elm.idtag))

        if ver == CGMESVersions.v2_4_15:
            vl = cgmes24.VoltageLevel(rdfid=form_rdfid(mc_elm.idtag))
        elif ver == CGMESVersions.v3_0_0:
            vl = cgmes30.VoltageLevel(rdfid=form_rdfid(mc_elm.idtag))
        else:
            raise NotImplemented()

        vl.name = mc_elm.name
        set_declared_cgmes_property(
            cgmes_object=vl,
            property_name="BaseVoltage",
            property_value=find_object_by_vnom(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.BaseVoltage_list,
                target_vnom=mc_elm.Vnom
            ),
            logger=logger,
            context="get_cgmes_voltage_levels()"
        )
        # vl.Bays = later
        # vl.TopologicalNode added at tn_nodes func

        if mc_elm.substation is not None:
            substation = find_object_by_uuid(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.Substation_list,
                target_uuid=mc_elm.substation.idtag
            )

            if isinstance(substation, cgmes_model.assets.Substation):
                vl.Substation = substation

                # link back
                if substation.VoltageLevels is None:
                    substation.VoltageLevels = list()
                else:
                    pass
                append_cgmes_relation_value(cgmes_object=substation,
                                            property_name="VoltageLevels",
                                            relation_value=vl,
                                            logger=logger,
                                            context="get_cgmes_voltage_levels()")

            else:
                logger.add_error(
                    msg=f'Substation not found for VoltageLevel',
                    device=mc_elm.device_type.value,
                    device_class=gcdev.Bus,
                    comment=f"{vl.name}"
                )
        cgmes_model.add(vl)


def get_cgmes_tp_nodes(multi_circuit_model: MultiCircuit,
                       cgmes_model: CgmesCircuit,
                       ver: CGMESVersions,
                       logger: DataLogger) -> None:
    """
    Convert gcdev Buses to CGMES Topological Nodes

    :param multi_circuit_model:
    :param cgmes_model:
    :param ver:
    :param logger:
    :return:
    """
    for bus in multi_circuit_model.buses:

        if bus.is_dc:
            create_cgmes_dc_tp_node(tp_name=bus.name,
                                    tp_description=bus.code,
                                    cgmes_model=cgmes_model,
                                    ver=ver,
                                    logger=logger)

        else:
            if not bus.internal:

                tn = None
                for topo_node in cgmes_model.cgmes_assets.TopologicalNode_list:
                    if topo_node.uuid == bus.idtag:
                        tn = topo_node
                        break
                if tn is not None:
                    # Skipping already added buses
                    continue

                # object_template = cgmes_model.get_class_type("TopologicalNode")
                # tn = object_template(rdfid=form_rdfid(bus.idtag))
                tn_rdfid = form_rdfid(bus.idtag)
                collided_object: CGMES_ASSETS | None = cgmes_model.all_objects_dict.get(tn_rdfid, None)
                if collided_object is None:
                    pass
                else:
                    if ver == CGMESVersions.v3_0_0:
                        # Keep deterministic TP identity in CGMES v3 exports.
                        # Boundary ConnectivityNodes can share the same RDFID; remove only the
                        # boundary dictionary entry so the canonical TP node uses bus.idtag.
                        if collided_object.tpe == "ConnectivityNode":
                            del cgmes_model.all_objects_dict[tn_rdfid]
                            logger.add_warning(
                                msg='Removed ConnectivityNode RDFID collision to preserve deterministic TopologicalNode identity',
                                device=bus.idtag,
                                device_class=bus.device_type.value,
                                value=tn_rdfid,
                                comment="get_cgmes_tp_nodes()"
                            )
                        else:
                            raise RuntimeError(
                                f"Cannot preserve deterministic TopologicalNode identity for bus {bus.idtag}: "
                                f"RDFID collision with non-boundary object type {collided_object.tpe}."
                            )
                    else:
                        # Legacy behavior for CGMES v2 remains unchanged.
                        tn_rdfid = get_new_rdfid()
                        logger.add_warning(
                            msg='TopologicalNode rdfid collision detected; generated a new rdfid for export',
                            device=bus.idtag,
                            device_class=bus.device_type.value,
                            value=tn_rdfid,
                            comment="get_cgmes_tp_nodes()"
                        )

                if ver == CGMESVersions.v2_4_15:
                    tn = cgmes24.TopologicalNode(rdfid=tn_rdfid)
                elif ver == CGMESVersions.v3_0_0:
                    tn = cgmes30.TopologicalNode(rdfid=tn_rdfid)
                else:
                    raise NotImplemented()

                tn.name = bus.name
                tn.shortName = bus.name
                tn.description = bus.code
                set_declared_cgmes_property(
                    cgmes_object=tn,
                    property_name="BaseVoltage",
                    property_value=find_object_by_vnom(
                        cgmes_model=cgmes_model,
                        object_list=cgmes_model.cgmes_assets.BaseVoltage_list,
                        target_vnom=bus.Vnom
                    ),
                    logger=logger,
                    context="get_cgmes_tp_nodes()"
                )

                container_voltage_level = None
                if bus.voltage_level is not None and cgmes_model.cgmes_assets.VoltageLevel_list:  # VoltageLevel
                    vl = find_object_by_uuid(
                        cgmes_model=cgmes_model,
                        object_list=cgmes_model.cgmes_assets.VoltageLevel_list,
                        target_uuid=bus.voltage_level.idtag
                    )

                    if isinstance(vl, cgmes_model.assets.VoltageLevel):
                        container_voltage_level = vl
                else:
                    container_voltage_level = find_fallback_voltage_level_for_bus(
                        cgmes_model=cgmes_model,
                        bus=bus,
                        logger=logger
                    )

                if isinstance(container_voltage_level, cgmes_model.assets.VoltageLevel):
                    tn.ConnectivityNodeContainer = container_voltage_level
                    container_voltage_level.TopologicalNode = tn  # link back
                else:
                    logger.add_error(
                        msg=f'No Voltage Level found',
                        device=bus.idtag,
                        device_class=bus.device_type.value,
                        device_property="Bus.voltage_level.idtag",
                        value=bus.voltage_level,
                        comment="get_cgmes_tn_nodes()")
                create_cgmes_location(cgmes_model=cgmes_model,
                                      device=tn,
                                      longitude=bus.longitude,
                                      latitude=bus.latitude,
                                      ver=ver,
                                      logger=logger)

                cgmes_model.add(tn)

    return


def get_cgmes_cn_nodes_from_tp_nodes(multi_circuit_model: MultiCircuit,
                                     cgmes_model: CgmesCircuit,
                                     ver: CGMESVersions,
                                     logger: DataLogger) -> None:
    """
    Export one ConnectivityNode for every TopologicalNode

    :param multi_circuit_model:
    :param cgmes_model:
    :param ver:
    :param logger:
    :return:
    """
    if ver == CGMESVersions.v3_0_0:
        # For CGMES v3 roundtrip identity stability, avoid synthesizing random
        # ConnectivityNode RDFIDs from TP nodes. Re-import then keeps TP UUIDs
        # as VeraGrid bus idtags.
        return
    else:
        pass

    for tn in cgmes_model.cgmes_assets.TopologicalNode_list:
        new_rdf_id = get_new_rdfid()

        # object_template = cgmes_model.get_class_type("ConnectivityNode")
        # cn = object_template(rdfid=new_rdf_id)

        if ver == CGMESVersions.v2_4_15:
            cn = cgmes24.ConnectivityNode(rdfid=new_rdf_id)
        elif ver == CGMESVersions.v3_0_0:
            cn = cgmes30.ConnectivityNode(rdfid=new_rdf_id)
        else:
            raise NotImplemented()

        cn.name = tn.name
        cn.shortName = tn.shortName
        cn.description = tn.description
        set_declared_cgmes_property(
            cgmes_object=cn,
            property_name="BaseVoltage",
            property_value=tn.BaseVoltage,
            logger=logger,
            context="get_cgmes_cn_nodes_from_tp_nodes()"
        )

        tn.ConnectivityNodes = cn
        cn.TopologicalNode = tn

        if tn.ConnectivityNodeContainer:
            if tn.BaseVoltage is not None:
                tn.ConnectivityNodeContainer.ConnectivityNodes = cn
                cn.ConnectivityNodeContainer = tn.ConnectivityNodeContainer
            else:
                logger.add_info(
                    msg='ConnectivityNodeContainer not copied to ConnectivityNode because TopologicalNode has no BaseVoltage',
                    device=tn.rdfid,
                    device_class=tn.tpe,
                    device_property="BaseVoltage"
                )
        else:
            logger.add_error(
                msg=f'TN has no ConnectivityNodeContainer, so cannot be assigned to CN',
                device=tn.rdfid,
                device_class=tn.tpe,
                device_property="Bus.voltage_level.idtag",
                value="None",
                comment="get_cgmes_cn_nodes_from_tp_nodes()"
            )

        cgmes_model.add(cn)


def get_cgmes_loads(multicircuit_model: MultiCircuit,
                    cgmes_model: CgmesCircuit,
                    ver: CGMESVersions,
                    logger: DataLogger,
                    t_idx: int | None = None):
    """
    Converts every Multi Circuit load into CGMES ConformLoad.

    :param multicircuit_model: MultiCircuit model in VeraGrid
    :param cgmes_model:
    :param ver:
    :param logger:
    :return:
    """

    create_cgmes_sub_load_area(cgmes_model, ver, logger)
    c_load_group = create_cgmes_conform_load_group(cgmes_model, ver, logger)
    nc_load_group = create_cgmes_non_conform_load_group(cgmes_model, ver, logger)

    for mc_elm in multicircuit_model.loads:

        if mc_elm.scalable:
            # object_template = cgmes_model.get_class_type("ConformLoad")
            # load = object_template(rdfid=form_rdfid(mc_elm.idtag))

            if ver == CGMESVersions.v2_4_15:
                load = cgmes24.ConformLoad(rdfid=form_rdfid(mc_elm.idtag))
            elif ver == CGMESVersions.v3_0_0:
                load = cgmes30.ConformLoad(rdfid=form_rdfid(mc_elm.idtag))
            else:
                raise NotImplemented()


        else:
            # object_template = cgmes_model.get_class_type("NonConformLoad")
            # load = object_template(rdfid=form_rdfid(mc_elm.idtag))

            if ver == CGMESVersions.v2_4_15:
                load = cgmes24.NonConformLoad(rdfid=form_rdfid(mc_elm.idtag))
            elif ver == CGMESVersions.v3_0_0:
                load = cgmes30.NonConformLoad(rdfid=form_rdfid(mc_elm.idtag))
            else:
                raise NotImplemented()

        load.Terminals = create_cgmes_terminal(mc_elm.bus, None, load, cgmes_model, ver, logger)
        load.name = mc_elm.name

        if mc_elm.bus.voltage_level:

            vl = find_object_by_uuid(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.VoltageLevel_list,
                target_uuid=mc_elm.bus.voltage_level.idtag
            )
            if isinstance(vl, cgmes_model.assets.VoltageLevel):
                load.EquipmentContainer = vl

        set_declared_cgmes_property(
            cgmes_object=load,
            property_name="BaseVoltage",
            property_value=find_object_by_vnom(cgmes_model=cgmes_model,
                                               object_list=cgmes_model.cgmes_assets.BaseVoltage_list,
                                               target_vnom=mc_elm.bus.Vnom),
            logger=logger,
            context="get_cgmes_loads()"
        )

        active_power: float = float(mc_elm.get_P_at(t_idx))
        reactive_power: float = float(mc_elm.get_Q_at(t_idx))
        active_current: float = float(mc_elm.get_Ir_at(t_idx))
        reactive_current: float = float(mc_elm.get_Ii_at(t_idx))
        active_impedance: float = float(mc_elm.get_G_at(t_idx))
        reactive_impedance: float = float(mc_elm.get_B_at(t_idx))

        has_zip_components: bool = (
            active_current != 0.0 or
            reactive_current != 0.0 or
            active_impedance != 0.0 or
            reactive_impedance != 0.0
        )

        if has_zip_components:
            load.LoadResponse = create_cgmes_load_response_char(load=mc_elm,
                                                                cgmes_model=cgmes_model,
                                                                ver=ver)
            populate_cgmes_load_response_characteristic(
                load_response=load.LoadResponse,
                active_power=active_power,
                active_current=active_current,
                active_impedance=active_impedance,
                reactive_power=reactive_power,
                reactive_current=reactive_current,
                reactive_impedance=reactive_impedance
            )
            load.p = active_power + active_current + active_impedance
            load.q = reactive_power + reactive_current + reactive_impedance
        else:
            load.p = active_power
            load.q = reactive_power

        load.description = mc_elm.code

        if mc_elm.scalable:
            load.LoadGroup = c_load_group
            append_cgmes_relation_value(cgmes_object=c_load_group,
                                        property_name="EnergyConsumers",
                                        relation_value=load,
                                        logger=logger,
                                        context="get_cgmes_loads()")
        else:
            load.LoadGroup = nc_load_group
            append_cgmes_relation_value(cgmes_object=nc_load_group,
                                        property_name="EnergyConsumers",
                                        relation_value=load,
                                        logger=logger,
                                        context="get_cgmes_loads()")

        cgmes_model.add(load)


def get_cgmes_equivalent_injections(multicircuit_model: MultiCircuit,
                                    cgmes_model: CgmesCircuit,
                                    ver: CGMESVersions,
                                    logger: DataLogger,
                                    t_idx: int | None = None):
    """
    Converts every Multi Circuit external grid
    into CGMES equivalent injection.

    :param multicircuit_model: MultiCircuit model in VeraGrid
    :param cgmes_model:
    :param ver:
    :param logger:
    :return:
    """

    for mc_elm in multicircuit_model.external_grids:

        # object_template = cgmes_model.get_class_type("EquivalentInjection")
        # ei = object_template(rdfid=form_rdfid(mc_elm.idtag))

        if ver == CGMESVersions.v2_4_15:
            ei = cgmes24.EquivalentInjection(rdfid=form_rdfid(mc_elm.idtag))
        elif ver == CGMESVersions.v3_0_0:
            ei = cgmes30.EquivalentInjection(rdfid=form_rdfid(mc_elm.idtag))
        else:
            raise NotImplemented()

        ei.description = mc_elm.code
        ei.name = mc_elm.name
        ei.p = mc_elm.get_P_at(t_idx)
        ei.q = mc_elm.get_Q_at(t_idx)
        set_declared_cgmes_property(
            cgmes_object=ei,
            property_name="BaseVoltage",
            property_value=find_object_by_vnom(cgmes_model=cgmes_model,
                                               object_list=cgmes_model.cgmes_assets.BaseVoltage_list,
                                               target_vnom=mc_elm.bus.Vnom),
            logger=logger,
            context="get_cgmes_equivalent_injections()"
        )

        ei.Terminals = create_cgmes_terminal(mc_elm.bus, None, ei, cgmes_model, ver, logger)
        ei.regulationCapability = False

        cgmes_model.add(ei)


def get_cgmes_ac_line_segments(multicircuit_model: MultiCircuit,
                               cgmes_model: CgmesCircuit,
                               op_lim_types: List,
                               ver: CGMESVersions,
                               logger: DataLogger,
                               t_idx: int | None = None):
    """
    Converts every Multi Circuit line
    into CGMES AC line segment.

    :param multicircuit_model: MultiCircuit model in VeraGrid
    :param cgmes_model: CgmesModel
    :param op_lim_types: Operational Limit types like PATL and TATL900, TATL60
    :param ver:
    :param logger: DataLogger
    :return:
    """
    sbase = multicircuit_model.Sbase
    for mc_elm in multicircuit_model.lines:

        # object_template = cgmes_model.get_class_type("ACLineSegment")
        # line = object_template(rdfid=form_rdfid(mc_elm.idtag))

        if ver == CGMESVersions.v2_4_15:
            line = cgmes24.ACLineSegment(rdfid=form_rdfid(mc_elm.idtag))
        elif ver == CGMESVersions.v3_0_0:
            line = cgmes30.ACLineSegment(rdfid=form_rdfid(mc_elm.idtag))
        else:
            raise NotImplemented()

        line.description = mc_elm.code
        line.name = mc_elm.name
        set_declared_cgmes_property(
            cgmes_object=line,
            property_name="BaseVoltage",
            property_value=find_object_by_vnom(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.BaseVoltage_list,
                target_vnom=mc_elm.get_max_bus_nominal_voltage()
            ),
            logger=logger,
            context="get_cgmes_ac_line_segments()"
        )  # which Vnom we need?

        # Terminals
        line.Terminals = [
            create_cgmes_terminal(mc_bus=mc_elm.bus_from,
                                  seq_num=1,
                                  cond_eq=line,
                                  cgmes_model=cgmes_model,
                                  ver=ver,
                                  logger=logger),
            create_cgmes_terminal(mc_bus=mc_elm.bus_to,
                                  seq_num=2,
                                  cond_eq=line,
                                  cgmes_model=cgmes_model,
                                  ver=ver,
                                  logger=logger)
        ]
        line.length = mc_elm.length

        # RATES
        get_cgmes_current_limits(cgmes_model=cgmes_model,
                                 cgmes_elm=line,
                                 mc_elm=mc_elm,
                                 op_lim_types=op_lim_types,
                                 ver=ver,
                                 logger=logger,
                                 t_idx=t_idx)

        vnom = line.BaseVoltage.nominalVoltage

        if vnom is not None:
            # Calculate Zbase
            zbase = (vnom * vnom) / sbase
            ybase = 1.0 / zbase

            line.r = mc_elm.R * zbase
            line.x = mc_elm.X * zbase
            # line.gch = mc_elm.G * Ybase
            line.bch = mc_elm.B * ybase
            line.r0 = mc_elm.R0 * zbase
            line.x0 = mc_elm.X0 * zbase
            # line.g0ch = mc_elm.G0 * Ybase
            line.b0ch = mc_elm.B0 * ybase

        cgmes_model.add(line)


def get_cgmes_generators(multicircuit_model: MultiCircuit,
                         cgmes_model: CgmesCircuit,
                         ver: CGMESVersions,
                         logger: DataLogger,
                         t_idx: int | None = None):
    """
    Converts Multi Circuit generators
    into appropriate CGMES Generating Unit.

    :param multicircuit_model: MultiCircuit model in VeraGrid
    :param cgmes_model:
    :param ver:
    :param logger:
    :return:
    """

    for mc_elm in multicircuit_model.generators:
        # Generating Units ---------------------------------------------------
        cgmes_gen = create_cgmes_generating_unit(gen=mc_elm, cgmes_model=cgmes_model, ver=ver)
        cgmes_gen.name = mc_elm.name
        cgmes_gen.description = mc_elm.code

        # cgmes_gen.EquipmentContainer: cgmes.Substation
        if cgmes_model.cgmes_assets.Substation_list and mc_elm.bus.substation:
            subs = find_object_by_uuid(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.Substation_list,
                target_uuid=mc_elm.bus.substation.idtag
            )

            if isinstance(subs, cgmes_model.assets.Substation):

                cgmes_gen.EquipmentContainer = subs
                append_cgmes_relation_value(cgmes_object=subs,
                                            property_name="Equipments",
                                            relation_value=cgmes_gen,
                                            logger=logger,
                                            context="get_cgmes_generators()")
            else:
                logger.add_error(
                    msg=f'No substation found for generator',
                    device=mc_elm.idtag,
                    device_class=mc_elm.device_type.value,
                    device_property="Substation",
                    value=subs,
                    comment=f"get_cgmes_generators() - {mc_elm.name}")
        else:
            logger.add_error(
                msg=f'No substations in the model',
                device_property="Substation list",
                comment=f"get_cgmes_generators()")

        if ver == CGMESVersions.v2_4_15:
            set_declared_cgmes_property(cgmes_object=cgmes_gen,
                                        property_name="initialP",
                                        property_value=mc_elm.get_P_at(t_idx),
                                        logger=logger,
                                        context="get_cgmes_generators()")
        elif ver == CGMESVersions.v3_0_0:
            set_declared_cgmes_property(cgmes_object=cgmes_gen,
                                        property_name="nominalP",
                                        property_value=mc_elm.get_P_at(t_idx),
                                        logger=logger,
                                        context="get_cgmes_generators()")
        else:
            raise NotImplemented()
        cgmes_gen.maxOperatingP = mc_elm.get_Pmax_at(t_idx)
        cgmes_gen.minOperatingP = mc_elm.get_Pmin_at(t_idx)

        # Synchronous Machine ------------------------------------------------
        # object_template = cgmes_model.get_class_type("SynchronousMachine")
        # cgmes_syn = object_template(rdfid=form_rdfid(mc_elm.idtag))

        if ver == CGMESVersions.v2_4_15:
            cgmes_syn = cgmes24.SynchronousMachine(rdfid=form_rdfid(mc_elm.idtag))
        elif ver == CGMESVersions.v3_0_0:
            cgmes_syn = cgmes30.SynchronousMachine(rdfid=form_rdfid(mc_elm.idtag))
        else:
            raise NotImplemented()

        cgmes_syn.description = mc_elm.code
        cgmes_syn.name = mc_elm.name
        # cgmes_syn.aggregate is optional, not exported
        if mc_elm.bus.is_slack:
            cgmes_syn.referencePriority = 1
            cgmes_gen.normalPF = 1  # in veragrid the participation factor is the cost
        else:
            cgmes_syn.referencePriority = 0
            cgmes_gen.normalPF = 0

        # TODO cgmes_syn.EquipmentContainer: VoltageLevel

        cgmes_syn.Terminals = create_cgmes_terminal(mc_bus=mc_elm.bus,
                                                    seq_num=1,
                                                    cond_eq=cgmes_syn,
                                                    cgmes_model=cgmes_model,
                                                    ver=ver,
                                                    logger=logger)

        # CONTROL : has_control: do we have control?
        # control_type: voltage or power control, ..
        # is_controlled: enabling flag (already have)
        if mc_elm.control_mode == GeneratorControlMode.V:
            cgmes_syn.RegulatingControl = (
                create_cgmes_regulating_control(cgmes_syn, mc_elm, cgmes_model, ver, logger))
            cgmes_syn.RegulatingControl.targetValue = mc_elm.get_Vset_at(t_idx) * mc_elm.bus.Vnom
            cgmes_syn.controlEnabled = True
        else:
            cgmes_syn.controlEnabled = False

        cgmes_syn.ratedPowerFactor = max(0.0, min(1.0, mc_elm.get_Pf_at(t_idx)))
        cgmes_syn.ratedS = mc_elm.Snom
        cgmes_syn.GeneratingUnit = cgmes_gen  # linking them together
        cgmes_gen.RotatingMachine = cgmes_syn  # linking them together
        cgmes_syn.maxQ = mc_elm.get_Qmax_at(t_idx)
        cgmes_syn.minQ = mc_elm.get_Qmin_at(t_idx)
        cgmes_syn.r = mc_elm.R1 if mc_elm.R1 != 1e-20 else None  # default value not exported
        cgmes_syn.p = -mc_elm.get_P_at(t_idx)  # negative sign!
        cgmes_syn.q = -mc_elm.get_Q_at(t_idx)
        if mc_elm.Snom > 0.0:
            cgmes_syn.qPercent = (mc_elm.get_Qmax_at(t_idx) / mc_elm.Snom) * 100.0
        if mc_elm.q_curve is not None:
            pMin = mc_elm.q_curve.get_Pmin()
        else:
            pMin = mc_elm.get_Pmin_at(t_idx)
        if cgmes_syn.p < 0:
            cgmes_syn.operatingMode = SynchronousMachineOperatingMode.generator
            if pMin < 0:
                cgmes_syn.type = SynchronousMachineKind.generatorOrMotor
            elif pMin == 0:
                cgmes_syn.type = SynchronousMachineKind.generatorOrCondenser
            else:
                cgmes_syn.type = SynchronousMachineKind.generator
        elif cgmes_syn.p == 0:
            cgmes_syn.operatingMode = SynchronousMachineOperatingMode.condenser
            if pMin < 0:
                # pMin < 0 means the machine can also motor; currently condensing → all three modes possible
                cgmes_syn.type = SynchronousMachineKind.generatorOrCondenserOrMotor
            elif pMin == 0:
                cgmes_syn.type = SynchronousMachineKind.generatorOrCondenser
            else:
                cgmes_syn.type = SynchronousMachineKind.generatorOrCondenser
        else:
            cgmes_syn.operatingMode = SynchronousMachineOperatingMode.motor
            if pMin < 0:
                cgmes_syn.type = SynchronousMachineKind.generatorOrMotor
            elif pMin == 0:
                cgmes_syn.type = SynchronousMachineKind.motorOrCondenser
            else:
                cgmes_syn.type = SynchronousMachineKind.generatorOrMotor

        # generatorOrCondenser = 'generatorOrCondenser'
        # generator = 'generator'
        # generatorOrMotor = 'generatorOrMotor'
        # motor = 'motor'
        # motorOrCondenser = 'motorOrCondenser'
        # generatorOrCondenserOrMotor = 'generatorOrCondenserOrMotor'
        # condenser = 'condenser'

        if mc_elm.bus.voltage_level:
            vl = find_object_by_uuid(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.VoltageLevel_list,
                target_uuid=mc_elm.bus.voltage_level.idtag
            )
            cgmes_syn.EquipmentContainer = vl

        set_declared_cgmes_property(
            cgmes_object=cgmes_syn,
            property_name="BaseVoltage",
            property_value=find_object_by_vnom(cgmes_model=cgmes_model,
                                               object_list=cgmes_model.cgmes_assets.BaseVoltage_list,
                                               target_vnom=mc_elm.bus.Vnom),
            logger=logger,
            context="get_cgmes_generators()"
        )
        cgmes_model.add(cgmes_syn)


def get_cgmes_power_transformers(grid: MultiCircuit,
                                 cgmes_model: CgmesCircuit,
                                 op_lim_types: List,
                                 ver: CGMESVersions,
                                 logger: DataLogger,
                                 t_idx: int | None = None):
    """
    Creates all transformer related CGMES classes from VeraGrid transformer.

    :param grid: MultiCircuit model in VeraGrid
    :param cgmes_model: CgmesModel
    :param op_lim_types:
    :param ver:
    :param logger: DataLogger
    :return:
    """
    for mc_elm in grid.transformers2w:

        # object_template = cgmes_model.get_class_type("PowerTransformer")
        # cm_transformer = object_template(rdfid=form_rdfid(mc_elm.idtag))

        if ver == CGMESVersions.v2_4_15:
            cm_transformer = cgmes24.PowerTransformer(rdfid=form_rdfid(mc_elm.idtag))
        elif ver == CGMESVersions.v3_0_0:
            cm_transformer = cgmes30.PowerTransformer(rdfid=form_rdfid(mc_elm.idtag))
        else:
            raise NotImplemented()

        cm_transformer.uuid = mc_elm.idtag
        cm_transformer.description = mc_elm.code
        cm_transformer.name = mc_elm.name
        cm_transformer.Terminals = [
            create_cgmes_terminal(mc_elm.bus_from, 1, cm_transformer, cgmes_model, ver, logger),
            create_cgmes_terminal(mc_elm.bus_to, 2, cm_transformer, cgmes_model, ver, logger)
        ]
        cm_transformer.aggregate = False  # what is this?
        if mc_elm.bus_from.substation:
            substation = find_object_by_uuid(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.Substation_list,
                target_uuid=mc_elm.bus_from.substation.idtag
            )

            if isinstance(substation, cgmes_model.assets.Substation):
                cm_transformer.EquipmentContainer = substation

        cm_transformer.PowerTransformerEnd = list()
        # Winding 1 ---------------------------------------------------------

        if ver == CGMESVersions.v2_4_15:
            pte1 = cgmes24.PowerTransformerEnd()
            pte2 = cgmes24.PowerTransformerEnd()

        elif ver == CGMESVersions.v3_0_0:
            pte1 = cgmes30.PowerTransformerEnd()
            pte2 = cgmes30.PowerTransformerEnd()

        else:
            raise NotImplemented()

        pte1.name = f"Winding 1 - {mc_elm.name}"
        pte1.PowerTransformer = cm_transformer
        pte1.Terminal = cm_transformer.Terminals[0]
        set_declared_cgmes_property(
            cgmes_object=pte1,
            property_name="BaseVoltage",
            property_value=find_object_by_vnom(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.BaseVoltage_list,
                target_vnom=mc_elm.bus_from.Vnom
            ),
            logger=logger,
            context="get_cgmes_power_transformers() winding 1"
        )

        # RATES
        get_cgmes_current_limits(cgmes_model=cgmes_model,
                                 cgmes_elm=cm_transformer,
                                 mc_elm=mc_elm,
                                 op_lim_types=op_lim_types,
                                 ver=ver,
                                 logger=logger,
                                 t_idx=t_idx)

        (pte1.r,
         pte1.x,
         pte1.g,
         pte1.b,
         pte1.r0,
         pte1.x0,
         pte1.g0,
         pte1.b0) = get_ohm_values_power_transformer(r=mc_elm.R,
                                                     x=mc_elm.X,
                                                     g=mc_elm.G,
                                                     b=mc_elm.B,
                                                     r0=mc_elm.R0,
                                                     x0=mc_elm.X0,
                                                     g0=mc_elm.G0,
                                                     b0=mc_elm.B0,
                                                     nominal_power=mc_elm.Sn,
                                                     rated_voltage=mc_elm.HV,
                                                     Sbase=grid.Sbase)

        pte1.ratedU = mc_elm.HV
        pte1.ratedS = mc_elm.Sn
        pte1.endNumber = 1

        # Winding 2 ---------------------------------------------------------
        pte2.name = f"Winding 2 - {mc_elm.name}"
        pte2.PowerTransformer = cm_transformer
        pte2.Terminal = cm_transformer.Terminals[1]
        set_declared_cgmes_property(
            cgmes_object=pte2,
            property_name="BaseVoltage",
            property_value=find_object_by_vnom(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.BaseVoltage_list,
                target_vnom=mc_elm.bus_to.Vnom
            ),
            logger=logger,
            context="get_cgmes_power_transformers() winding 2"
        )

        # TODO: Shouldn't this be half?
        pte2.r = 0.0
        pte2.x = 0.0
        pte2.g = 0.0
        pte2.b = 0.0
        pte2.r0 = 0.0
        pte2.x0 = 0.0
        pte2.g0 = 0.0
        pte2.b0 = 0.0
        pte2.ratedU = mc_elm.LV
        pte2.ratedS = mc_elm.Sn
        pte2.endNumber = 2

        # -------------------- RATIO TAP  & PHASE TAP -----------------------
        # RatioTapChanger (tcc: voltage, disabled)	<--	-->	NoRegulation
        # RatioTapChanger (tcc: voltage, enabled)	<--	-->	Voltage
        # PhaseTapChangerSymmetrical	<--	-->	Symmetrical
        # PhaseTapChangerAsymmetrical	<--	-->	Asymmetrical
        #                         TAP Changer EQ

        tcc_mode = RegulatingControlModeKind.voltage
        tcc_enabled = False

        if mc_elm.tap_changer.tc_type == TapChangerTypes.NoRegulation:
            if ver == CGMESVersions.v2_4_15:
                tap_changer = cgmes24.RatioTapChanger(rdfid=get_new_rdfid())
            elif ver == CGMESVersions.v3_0_0:
                tap_changer = cgmes30.RatioTapChanger(rdfid=get_new_rdfid())
            else:
                raise NotImplemented()

        elif mc_elm.tap_changer.tc_type == TapChangerTypes.VoltageRegulation:
            if ver == CGMESVersions.v2_4_15:
                tap_changer = cgmes24.RatioTapChanger(rdfid=get_new_rdfid())
            elif ver == CGMESVersions.v3_0_0:
                tap_changer = cgmes30.RatioTapChanger(rdfid=get_new_rdfid())
            else:
                raise NotImplemented()

            if mc_elm.get_tap_module_control_mode_at(t_idx) != TapModuleControl.fixed:
                # if fixed, it should be disabled
                tcc_enabled = True

        elif mc_elm.tap_changer.tc_type == TapChangerTypes.Symmetrical:
            if ver == CGMESVersions.v2_4_15:
                tap_changer = cgmes24.PhaseTapChangerSymmetrical(rdfid=get_new_rdfid())
            elif ver == CGMESVersions.v3_0_0:
                tap_changer = cgmes30.PhaseTapChangerSymmetrical(rdfid=get_new_rdfid())
            else:
                raise NotImplemented()

            if mc_elm.get_tap_phase_control_mode_at(t_idx) != TapPhaseControl.fixed:
                # if fixed, it should be disabled
                tcc_enabled = True
            tcc_mode = RegulatingControlModeKind.activePower

        elif mc_elm.tap_changer.tc_type == TapChangerTypes.Asymmetrical:
            if ver == CGMESVersions.v2_4_15:
                tap_changer = cgmes24.PhaseTapChangerAsymmetrical(rdfid=get_new_rdfid())
            elif ver == CGMESVersions.v3_0_0:
                tap_changer = cgmes30.PhaseTapChangerAsymmetrical(rdfid=get_new_rdfid())
            else:
                raise NotImplemented()

            if (mc_elm.get_tap_module_control_mode_at(t_idx) != TapModuleControl.fixed or
                    mc_elm.get_tap_phase_control_mode_at(t_idx) != TapPhaseControl.fixed):
                # if fixed, it should be disabled
                tcc_enabled = True
            tcc_mode = RegulatingControlModeKind.activePower

        else:
            tap_changer = None
            logger.add_error(msg='No TapChangerType found for TapChanger',
                             device=mc_elm.tap_changer,
                             device_class=mc_elm.device_type.value,
                             value=mc_elm.tap_changer)

        if tap_changer is not None:
            tap_changer.name = f'_tc_{mc_elm.name}'
            tap_changer.shortName = f'_tc_{mc_elm.name}'
            tap_changer.neutralU = pte1.ratedU
            tap_changer.TransformerEnd = pte1

            # STEPs
            (tap_changer.lowStep,
             tap_changer.highStep,
             tap_changer.normalStep,
             tap_changer.neutralStep,
             voltageIncr,
             tap_changer.step) = get_transformer_tap_values_for_cgmes_export(
                mc_elm=mc_elm,
                logger=logger,
                t_idx=t_idx
            )

            if isinstance(tap_changer, (cgmes24.RatioTapChanger, cgmes30.RatioTapChanger)):

                tap_changer.stepVoltageIncrement = voltageIncr

            elif isinstance(tap_changer, (cgmes24.PhaseTapChangerNonLinear, cgmes30.PhaseTapChangerNonLinear)):

                # PhaseTapChangerSymmetrical or PhaseTapChangerAsymmetrical
                tap_changer.voltageStepIncrement = voltageIncr
                tap_changer.xMin = mc_elm.X
                k_im: np.ndarray = mc_elm.tap_changer.impedance_correction_imag_array
                max_correction: float = float(np.max(k_im))
                # xMax is the reactance at the extreme tap; scale xMin by the peak
                # impedance correction factor. When no table is set, k_im is all-ones
                # and xMax == xMin (no correction).
                tap_changer.xMax = mc_elm.X * max_correction

            else:
                logger.add_error(
                    msg='stepVoltageIncrement cannot be filled for TapChanger',
                    device=mc_elm,
                    device_class=mc_elm.device_type.value,
                    value=mc_elm.idtag,
                    comment="get_cgmes_power_transformers")

            if isinstance(tap_changer, (cgmes24.PhaseTapChangerAsymmetrical, cgmes30.PhaseTapChangerAsymmetrical)):
                tap_changer.windingConnectionAngle = mc_elm.tap_changer.asymmetry_angle

            # CONTROL
            tap_changer.ltcFlag = True  # load tap changing capability
            tap_changer.TapChangerControl = create_cgmes_tap_changer_control(
                tap_changer=tap_changer,
                tcc_mode=tcc_mode,
                tcc_enabled=tcc_enabled,
                mc_trafo=mc_elm,
                cgmes_model=cgmes_model,
                ver=ver,
                logger=logger
            )
            apply_time_index_to_tap_changer_control(
                tap_changer=tap_changer,
                mc_elm=mc_elm,
                logger=logger,
                t_idx=t_idx
            )
            # tculControlMode not used, but has to be set to something: volt/react ..
            set_declared_cgmes_property(
                cgmes_object=tap_changer,
                property_name="tculControlMode",
                property_value=TransformerControlMode.volt,
                logger=logger,
                context="get_cgmes_power_transformers()"
            )
            #                   TAP Changer SSH
            tap_changer.controlEnabled = tcc_enabled
            # Specifies the regulation status of the equipment.  True is regulating, false is not regulating.
            # why, why not?

            #                   TAP Changer SV

            # object_template = cgmes_model.get_class_type("SvTapStep")
            # sv_tap_step = object_template(rdfid=new_rdf_id, tpe="SvTapStep")
            if ver == CGMESVersions.v2_4_15:
                sv_tap_step = cgmes24.SvTapStep(rdfid=get_new_rdfid(), tpe="SvTapStep")
            elif ver == CGMESVersions.v3_0_0:
                sv_tap_step = cgmes30.SvTapStep(rdfid=get_new_rdfid(), tpe="SvTapStep")
            else:
                raise NotImplemented()

            # TODO def EA same as step? should it come from the results?
            # PowerFlowResults: tap_module, tap_angle (for SvTapStep), get the closest tap pos for the object.
            sv_tap_step.position = tap_changer.step
            sv_tap_step.TapChanger = tap_changer

            # -----------------------------------------------------------------
            cgmes_model.add(tap_changer)
            cgmes_model.add(sv_tap_step)
        else:
            # No tap changer
            pass

        cm_transformer.PowerTransformerEnd.append(pte1)
        cgmes_model.add(pte1)
        cm_transformer.PowerTransformerEnd.append(pte2)
        cgmes_model.add(pte2)
        cgmes_model.add(cm_transformer)

    # ------------------------------------------------------------------------------------------------------------------
    # Create the 3W transformers
    # ------------------------------------------------------------------------------------------------------------------

    for mc_elm in grid.transformers3w:

        # object_template = cgmes_model.get_class_type("PowerTransformer")
        # cm_transformer = object_template(rdfid=form_rdfid(mc_elm.idtag))
        if ver == CGMESVersions.v2_4_15:
            cm_transformer = cgmes24.PowerTransformer(rdfid=form_rdfid(mc_elm.idtag))
        elif ver == CGMESVersions.v3_0_0:
            cm_transformer = cgmes30.PowerTransformer(rdfid=form_rdfid(mc_elm.idtag))
        else:
            raise NotImplemented()

        cm_transformer.uuid = mc_elm.idtag
        cm_transformer.description = mc_elm.code
        cm_transformer.name = mc_elm.name
        cm_transformer.Terminals = [
            create_cgmes_terminal(mc_elm.bus1, 1, cm_transformer, cgmes_model, ver, logger),
            create_cgmes_terminal(mc_elm.bus2, 2, cm_transformer, cgmes_model, ver, logger),
            create_cgmes_terminal(mc_elm.bus3, 3, cm_transformer, cgmes_model, ver, logger)
        ]

        if mc_elm.bus1.substation:
            substation = find_object_by_uuid(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.Substation_list,
                target_uuid=mc_elm.bus1.substation.idtag
            )

            if isinstance(substation, cgmes_model.assets.Substation):
                cm_transformer.EquipmentContainer = substation

        # Current limits per winding — each winding has its own rated current
        patl, tatl_900, tatl_60 = op_lim_types
        winding_terminals: list[tuple] = [
            (cm_transformer.Terminals[0], mc_elm.winding1),
            (cm_transformer.Terminals[1], mc_elm.winding2),
            (cm_transformer.Terminals[2], mc_elm.winding3),
        ]
        for terminal, winding in winding_terminals:
            winding_rate: float = winding.get_rate_at(t_idx)
            contingency_rate: float = winding.get_contingency_factor_at(t_idx) * winding_rate
            protection_rate: float = winding.get_protection_rating_factor_at(t_idx) * winding_rate
            if winding_rate != 0.0:
                create_cgmes_current_limit(terminal, winding_rate, patl, cgmes_model, ver, logger)
            if contingency_rate != 0.0:
                create_cgmes_current_limit(terminal, contingency_rate, tatl_900, cgmes_model, ver, logger)
            if protection_rate != 0.0:
                create_cgmes_current_limit(terminal, protection_rate, tatl_60, cgmes_model, ver, logger)

        cm_transformer.PowerTransformerEnd = []
        if ver == CGMESVersions.v2_4_15:
            pte1 = cgmes24.PowerTransformerEnd()
            pte2 = cgmes24.PowerTransformerEnd()
            pte3 = cgmes24.PowerTransformerEnd()
        elif ver == CGMESVersions.v3_0_0:
            pte1 = cgmes30.PowerTransformerEnd()
            pte2 = cgmes30.PowerTransformerEnd()
            pte3 = cgmes30.PowerTransformerEnd()
        else:
            raise NotImplemented()

        # Winding 1 ---------------------------------------------------------
        pte1.name = mc_elm.name
        pte1.PowerTransformer = cm_transformer
        pte1.Terminal = cm_transformer.Terminals[0]
        set_declared_cgmes_property(
            cgmes_object=pte1,
            property_name="BaseVoltage",
            property_value=find_object_by_vnom(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.BaseVoltage_list,
                target_vnom=mc_elm.bus1.Vnom
            ),
            logger=logger,
            context="get_cgmes_power_transformers() 3W winding 1"
        )
        pte1.ratedU = mc_elm.V1
        pte1.ratedS = mc_elm.rate1
        pte1.endNumber = 1

        (pte1.r,
         pte1.x,
         pte1.g,
         pte1.b,
         pte1.r0,
         pte1.x0,
         pte1.g0,
         pte1.b0) = get_ohm_values_power_transformer(r=mc_elm.winding1.R,
                                                     x=mc_elm.winding1.X,
                                                     g=mc_elm.winding1.G,
                                                     b=mc_elm.winding1.B,
                                                     r0=mc_elm.winding1.R0,
                                                     x0=mc_elm.winding1.X0,
                                                     g0=mc_elm.winding1.G0,
                                                     b0=mc_elm.winding1.B0,
                                                     nominal_power=mc_elm.winding1.rate,
                                                     rated_voltage=mc_elm.winding1.HV,
                                                     Sbase=grid.Sbase)

        # Winding 2 ---------------------------------------------------------
        pte2.name = mc_elm.name
        pte2.PowerTransformer = cm_transformer
        pte2.Terminal = cm_transformer.Terminals[1]
        set_declared_cgmes_property(
            cgmes_object=pte2,
            property_name="BaseVoltage",
            property_value=find_object_by_vnom(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.BaseVoltage_list,
                target_vnom=mc_elm.bus2.Vnom
            ),
            logger=logger,
            context="get_cgmes_power_transformers() 3W winding 2"
        )
        pte2.ratedU = mc_elm.V2
        pte2.ratedS = mc_elm.rate2
        pte2.endNumber = 2

        (pte2.r,
         pte2.x,
         pte2.g,
         pte2.b,
         pte2.r0,
         pte2.x0,
         pte2.g0,
         pte2.b0) = get_ohm_values_power_transformer(r=mc_elm.winding2.R,
                                                     x=mc_elm.winding2.X,
                                                     g=mc_elm.winding2.G,
                                                     b=mc_elm.winding2.B,
                                                     r0=mc_elm.winding2.R0,
                                                     x0=mc_elm.winding2.X0,
                                                     g0=mc_elm.winding2.G0,
                                                     b0=mc_elm.winding2.B0,
                                                     nominal_power=mc_elm.winding2.rate,
                                                     rated_voltage=mc_elm.winding2.HV,
                                                     Sbase=grid.Sbase)

        # Winding 3 ---------------------------------------------------------
        pte3.name = mc_elm.name
        pte3.PowerTransformer = cm_transformer
        pte3.Terminal = cm_transformer.Terminals[2]
        set_declared_cgmes_property(
            cgmes_object=pte3,
            property_name="BaseVoltage",
            property_value=find_object_by_vnom(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.BaseVoltage_list,
                target_vnom=mc_elm.bus3.Vnom
            ),
            logger=logger,
            context="get_cgmes_power_transformers() 3W winding 3"
        )
        pte3.ratedU = mc_elm.V3
        pte3.ratedS = mc_elm.rate3
        pte3.endNumber = 3

        (pte3.r,
         pte3.x,
         pte3.g,
         pte3.b,
         pte3.r0,
         pte3.x0,
         pte3.g0,
         pte3.b0) = get_ohm_values_power_transformer(r=mc_elm.winding3.R,
                                                     x=mc_elm.winding3.X,
                                                     g=mc_elm.winding3.G,
                                                     b=mc_elm.winding3.B,
                                                     r0=mc_elm.winding3.R0,
                                                     x0=mc_elm.winding3.X0,
                                                     g0=mc_elm.winding3.G0,
                                                     b0=mc_elm.winding3.B0,
                                                     nominal_power=mc_elm.winding3.rate,
                                                     rated_voltage=mc_elm.winding3.HV,
                                                     Sbase=grid.Sbase)

        # Export winding taps so 3W off-nominal ratios roundtrip from CGMES.
        create_cgmes_tap_changer_for_transformer_end(
            mc_elm=mc_elm.winding1,
            pte=pte1,
            cgmes_model=cgmes_model,
            ver=ver,
            logger=logger,
            t_idx=t_idx
        )
        create_cgmes_tap_changer_for_transformer_end(
            mc_elm=mc_elm.winding2,
            pte=pte2,
            cgmes_model=cgmes_model,
            ver=ver,
            logger=logger,
            t_idx=t_idx
        )
        create_cgmes_tap_changer_for_transformer_end(
            mc_elm=mc_elm.winding3,
            pte=pte3,
            cgmes_model=cgmes_model,
            ver=ver,
            logger=logger,
            t_idx=t_idx
        )

        # compose transformer ------------------------------------------------------------------------------------------
        cm_transformer.PowerTransformerEnd.append(pte1)
        cgmes_model.add(pte1)
        cm_transformer.PowerTransformerEnd.append(pte2)
        cgmes_model.add(pte2)
        cm_transformer.PowerTransformerEnd.append(pte3)
        cgmes_model.add(pte3)

        cgmes_model.add(cm_transformer)


def get_cgmes_current_limits(cgmes_model: CgmesCircuit,
                             cgmes_elm: CGMES_ASSETS,
                             mc_elm: BranchParent,
                             op_lim_types: List,
                             ver: CGMESVersions,
                             logger: DataLogger,
                             t_idx: int | None = None):
    """
    Export Current Limits to CGMES for Branches.

    :param cgmes_model: CgmesCircuit
    :param mc_elm: GcDev Transformer 2W/3W or ACLineSegment
    :param cgmes_elm: CGMES Transformer 2W or ACLineSegment
    :param op_lim_types: list of used OperationalLimitTypes
    :param ver:
    :param logger: DataLogger
    :return: None
    """

    # Get operational limit types
    patl, tatl_900, tatl_60 = op_lim_types

    # Rate and Type Mapping
    rates = [
        (mc_elm.get_rate_at(t_idx), patl),
        # Normal rate
        (mc_elm.get_contingency_factor_at(t_idx) * mc_elm.get_rate_at(t_idx), tatl_900),
        # Contingency rate - TATL 900
        (mc_elm.get_protection_rating_factor_at(t_idx) * mc_elm.get_rate_at(t_idx), tatl_60)
        # Contingency rate - TATL 60
    ]

    # Apply current limits to each terminal: 2 for TR2W/Lines, 3 for TR3W
    for terminal in cgmes_elm.Terminals:
        if terminal is not None:  # Skip if the terminal does not exist
            create_limits_for_terminal(termnl=terminal,
                                       rate_and_type=rates,
                                       cgmes_model=cgmes_model,
                                       ver=ver,
                                       logger=logger)
        else:
            pass


def get_cgmes_operational_limit_types(cgmes_model: CgmesCircuit, ver: CGMESVersions):
    """
    Creates three kind of Operational limit type for Cgmes Export.

    :param cgmes_model: CgmesModel
    :param ver:
    :return:
    """
    # PATL      -----
    patl = create_cgmes_operational_limit_type(cgmes_model, ver)
    patl.name = "Normal rating"
    patl.shortName = "PATL"
    patl.description = "Permanent Admissible Transmission Loading"
    patl.acceptableDuration = None  # unlimited

    if ver == CGMESVersions.v2_4_15:
        patl.limitType = LimitTypeKind.patl
    elif ver == CGMESVersions.v3_0_0:
        patl.kind = LimitTypeKind.patl
    else:
        raise NotImplemented()
    patl.direction = OperationalLimitDirectionKind.absoluteValue

    # TATL 900  ------
    tatl_900 = create_cgmes_operational_limit_type(cgmes_model, ver)
    tatl_900.name = "Contingency rating in VeraGrid"
    tatl_900.shortName = "TATL"
    tatl_900.description = "Temporarily Admissible Transmission Loading"
    tatl_900.acceptableDuration = 900

    if ver == CGMESVersions.v2_4_15:
        tatl_900.limitType = LimitTypeKind.tatl
    elif ver == CGMESVersions.v3_0_0:
        tatl_900.kind = LimitTypeKind.tatl
    else:
        raise NotImplemented()
    tatl_900.direction = OperationalLimitDirectionKind.absoluteValue

    # TATL 60   ------
    tatl_60 = create_cgmes_operational_limit_type(cgmes_model, ver)
    tatl_60.name = "Protection rating in VeraGrid"
    tatl_60.shortName = "TATL"
    tatl_60.description = "Temporarily Admissible Transmission Loading"
    tatl_60.acceptableDuration = 60

    if ver == CGMESVersions.v2_4_15:
        tatl_60.limitType = LimitTypeKind.tatl
    elif ver == CGMESVersions.v3_0_0:
        tatl_60.kind = LimitTypeKind.tatl
    else:
        raise NotImplemented()
    tatl_60.direction = OperationalLimitDirectionKind.absoluteValue

    return [patl, tatl_900, tatl_60]


def get_cgmes_equivalent_shunts(multicircuit_model: MultiCircuit,
                                cgmes_model: CgmesCircuit,
                                ver: CGMESVersions,
                                logger: DataLogger,
                                t_idx: int | None = None):
    """
    Converts Multi Circuit shunts
    into CGMES EquivalentShunt.
    No control, like FixShunt in RAW.

    :param multicircuit_model: MultiCircuit model in VeraGrid
    :param cgmes_model:
    :param ver:
    :param logger:
    :return:
    """

    for mc_elm in multicircuit_model.shunts:

        if ver == CGMESVersions.v2_4_15:
            eq_shunt = cgmes24.EquivalentShunt(rdfid=form_rdfid(mc_elm.idtag))
        elif ver == CGMESVersions.v3_0_0:
            eq_shunt = cgmes30.EquivalentShunt(rdfid=form_rdfid(mc_elm.idtag))
        else:
            raise NotImplemented()

        eq_shunt.name = mc_elm.name
        eq_shunt.description = mc_elm.code

        if mc_elm.bus.voltage_level:

            vl = find_object_by_uuid(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.VoltageLevel_list,
                target_uuid=mc_elm.bus.voltage_level.idtag
            )

            if isinstance(vl, cgmes_model.assets.VoltageLevel):
                eq_shunt.EquipmentContainer = vl

        base_voltage = find_object_by_vnom(
            cgmes_model=cgmes_model,
            object_list=cgmes_model.cgmes_assets.BaseVoltage_list,
            target_vnom=mc_elm.bus.Vnom)
        if base_voltage is not None:
            set_declared_cgmes_property(
                cgmes_object=eq_shunt,
                property_name="BaseVoltage",
                property_value=base_voltage,
                logger=logger,
                context="get_cgmes_equivalent_shunts()"
            )

        eq_shunt.b = mc_elm.get_B_at(t_idx) / (mc_elm.bus.Vnom ** 2)
        eq_shunt.g = mc_elm.get_G_at(t_idx) / (mc_elm.bus.Vnom ** 2)

        create_cgmes_terminal(mc_bus=mc_elm.bus,
                              seq_num=1,
                              cond_eq=eq_shunt,
                              cgmes_model=cgmes_model,
                              ver=ver,
                              logger=logger)

        cgmes_model.add(eq_shunt)


def get_cgmes_linear_and_non_linear_shunts(multicircuit_model: MultiCircuit,
                                           cgmes_model: CgmesCircuit,
                                           ver: CGMESVersions,
                                           logger: DataLogger,
                                           t_idx: int | None = None):
    """
    Convert VeraGrid controllable shunts to CGMES NonlinearShuntCompensator.

    VeraGrid keeps the full stepped shunt characteristic. Exporting every
    controllable shunt as a nonlinear compensator preserves that complete
    section curve and avoids making a lossy linear/non-linear class decision.

    :param multicircuit_model: MultiCircuit model in VeraGrid
    :param cgmes_model: CgmesModel
    :param ver:
    :param logger: DataLogger
    :return:
    """

    for mc_elm in multicircuit_model.controllable_shunts:

        if ver == CGMESVersions.v2_4_15:
            non_lin_sc = cgmes24.NonlinearShuntCompensator(rdfid=form_rdfid(mc_elm.idtag))
        elif ver == CGMESVersions.v3_0_0:
            non_lin_sc = cgmes30.NonlinearShuntCompensator(rdfid=form_rdfid(mc_elm.idtag))
        else:
            raise NotImplemented()

        non_lin_sc.name = mc_elm.name
        non_lin_sc.description = mc_elm.code
        if mc_elm.bus.voltage_level:
            vl = find_object_by_uuid(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.VoltageLevel_list,
                target_uuid=mc_elm.bus.voltage_level.idtag
            )
            if isinstance(vl, cgmes_model.assets.VoltageLevel):
                non_lin_sc.EquipmentContainer = vl

        set_declared_cgmes_property(
            cgmes_object=non_lin_sc,
            property_name="BaseVoltage",
            property_value=find_object_by_vnom(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.BaseVoltage_list,
                target_vnom=mc_elm.bus.Vnom),
            logger=logger,
            context="get_cgmes_linear_and_non_linear_shunts()"
        )

        non_lin_sc.Terminals = (
            create_cgmes_terminal(mc_bus=mc_elm.bus,
                                  seq_num=1,
                                  cond_eq=non_lin_sc,
                                  cgmes_model=cgmes_model,
                                  ver=ver,
                                  logger=logger)
        )

        if mc_elm.control_mode != ShuntControlMode.Locked:
            non_lin_sc.RegulatingControl = (
                create_cgmes_regulating_control(non_lin_sc, mc_elm, cgmes_model, ver, logger)
            )
            non_lin_sc.RegulatingControl.targetValue = mc_elm.get_Vset_at(t_idx) * mc_elm.bus.Vnom
            non_lin_sc.controlEnabled = True
        else:
            non_lin_sc.controlEnabled = False

        non_lin_sc.nomU = mc_elm.bus.Vnom
        cumulative_b_mva = mc_elm.get_cumulative_b().astype(float)
        cumulative_g_mva = mc_elm.get_cumulative_g().astype(float)
        shunt_b: float = float(mc_elm.get_B_at(t_idx))
        shunt_g: float = float(mc_elm.get_G_at(t_idx))

        active_sections: int = 0
        if mc_elm.get_active_at(t_idx):
            if np.isclose(shunt_b, 0.0, atol=1e-9, rtol=0.0) and np.isclose(shunt_g, 0.0, atol=1e-9, rtol=0.0):
                active_sections = 0
            else:
                for section_index in range(len(cumulative_b_mva)):
                    if (np.isclose(cumulative_b_mva[section_index], shunt_b, atol=1e-9, rtol=0.0)
                            and np.isclose(cumulative_g_mva[section_index], shunt_g, atol=1e-9, rtol=0.0)):
                        active_sections = section_index + 1
                        break

                if active_sections == 0:
                    logger.add_warning(
                        msg="Controllable shunt operating point does not match the explicit stepped characteristic",
                        device=mc_elm.idtag,
                        device_class=mc_elm.device_type.value,
                        device_property="B/G",
                        value=f"B={shunt_b}, G={shunt_g}",
                        expected_value="cumulative stepped values"
                    )
                    cumulative_b_mva = np.array([shunt_b], dtype=float)
                    cumulative_g_mva = np.array([shunt_g], dtype=float)
                    active_sections = 1

        non_lin_sc.sections = active_sections
        b_points = [b / (non_lin_sc.nomU ** 2) for b in cumulative_b_mva]
        g_points = [g / (non_lin_sc.nomU ** 2) for g in cumulative_g_mva]

        for i in range(len(b_points)):
            create_cgmes_nonlinear_sc_point(
                section_num=i + 1,
                b=b_points[i],
                g=g_points[i],
                nl_sc=non_lin_sc,
                cgmes_model=cgmes_model,
                ver=ver
            )
        non_lin_sc.normalSections = non_lin_sc.sections
        non_lin_sc.maximumSections = len(b_points)
        if non_lin_sc.maximumSections < non_lin_sc.sections:
            logger.add_error(
                msg="Number or sections is out of range",
                device=non_lin_sc,
                device_class=non_lin_sc.tpe,
                value=non_lin_sc.sections,
                expected_value=non_lin_sc.maximumSections,
                comment="maxSections < sections"
            )
        non_lin_sc.aggregate = False

        cgmes_model.add(non_lin_sc)


def get_cgmes_breakers(multicircuit_model: MultiCircuit,
                       cgmes_model: CgmesCircuit,
                       ver: CGMESVersions,
                       logger: DataLogger,
                       t_idx: int | None = None):
    """
    Converts every Multi Circuit Switch into CGMES Breaker.

    :param multicircuit_model: MultiCircuit model in VeraGrid
    :param cgmes_model:
    :param ver:
    :param logger:
    :return:
    """

    for mc_elm in multicircuit_model.switch_devices:
        if ver == CGMESVersions.v2_4_15:
            br = cgmes24.Breaker(rdfid=form_rdfid(mc_elm.idtag))
        elif ver == CGMESVersions.v3_0_0:
            br = cgmes30.Breaker(rdfid=form_rdfid(mc_elm.idtag))
        else:
            raise NotImplemented()

        br.Terminals = [
            create_cgmes_terminal(mc_elm.bus_from, None, br, cgmes_model, ver, logger),
            create_cgmes_terminal(mc_elm.bus_to, None, br, cgmes_model, ver, logger)
        ]

        br.name = mc_elm.name
        br.description = mc_elm.code
        set_declared_cgmes_property(
            cgmes_object=br,
            property_name="BaseVoltage",
            property_value=find_object_by_vnom(cgmes_model=cgmes_model,
                                               object_list=cgmes_model.cgmes_assets.BaseVoltage_list,
                                               target_vnom=mc_elm.get_max_bus_nominal_voltage()),
            logger=logger,
            context="get_cgmes_breakers()"
        )

        if mc_elm.get_voltage_level_from():
            vl = find_object_by_uuid(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.VoltageLevel_list,
                target_uuid=mc_elm.bus_from.voltage_level.idtag
            )
            br.EquipmentContainer = vl

        br.open = not mc_elm.get_active_at(t_idx)
        br.retained = mc_elm.retained
        br.normalOpen = mc_elm.normal_open
        br.aggregate = False

        # .ratedCurrent is optional attr, not sure is it in Amps or an enum
        # if br.BaseVoltage is not None:
        #     br.ratedCurrent = np.round(
        #         (mc_elm.rated_current * 1000.0) / (br.BaseVoltage.nominalVoltage * 1.73205080756888),
        #         4)
        # else:
        #     logger.add_warning(msg="Couldn't calculate rated current as BaseVoltage missing")

        cgmes_model.add(br)


def get_cgmes_sv_voltages(
        multi_circuit_model: MultiCircuit,
        cgmes_model: CgmesCircuit,
        pf_results: PowerFlowResults,
        ver: CGMESVersions,
        logger: DataLogger) -> None:
    """
    Creates a CgmesCircuit SvVoltage_list
    from PowerFlow results of the numerical circuit.

    :param multi_circuit_model:
    :param cgmes_model:
    :param pf_results:
    :param ver:
    :param logger:
    :return:
    """
    # SvVoltage: v, a, TopologicalNode

    for bus, voltage in zip(multi_circuit_model.buses, pf_results.voltage):

        if not bus.is_dc and not bus.internal:

            tp_node = find_object_by_uuid(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.TopologicalNode_list,
                target_uuid=bus.idtag
            )

            if isinstance(tp_node, cgmes_model.assets.TopologicalNode):

                if ver == CGMESVersions.v2_4_15:
                    sv_voltage = cgmes24.SvVoltage(rdfid=get_new_rdfid(), tpe='SvVoltage')
                elif ver == CGMESVersions.v3_0_0:
                    sv_voltage = cgmes30.SvVoltage(rdfid=get_new_rdfid(), tpe='SvVoltage')
                else:
                    raise NotImplemented()

                sv_voltage.TopologicalNode = tp_node

                # as the ORDER of the results is the same as the order of buses (=tn)
                bv = tp_node.BaseVoltage
                sv_voltage.v = np.abs(voltage) * bv.nominalVoltage
                sv_voltage.angle = np.angle(voltage, deg=True)

                # Add the SvVoltage instance to the SvVoltage_list
                cgmes_model.add(sv_voltage)

            else:
                logger.add_info(
                    msg="TP Node not found for bus",
                    value=tp_node,
                    expected_value=bus.idtag,
                )

        else:
            logger.add_info(
                msg="SvVoltage is not exported for internal (TR3W) buses and DC buses",
                value=voltage,
            )


def get_cgmes_sv_power_flow_1(multi_circuit: MultiCircuit,
                              nc: NumericalCircuit,
                              cgmes_model: CgmesCircuit,
                              pf_results: PowerFlowResults,
                              ver: CGMESVersions,
                              logger: DataLogger) -> None:
    """
    For single-terminal devices:
    Creates a CgmesCircuit SvPowerFlow_list from PowerFlow results of the numerical circuit.

    :param multi_circuit:
    :param nc:
    :param cgmes_model:
    :param pf_results:
    :param ver:
    :param logger:
    :return: SvVoltage_list is populated in CgmesCircuit.
    """
    # SVPowerFlow: p, q -> Terminals
    # SvPowerFlow class is required to be instantiated for the following classes:
    # subclasses of the RotatingMachine,
    # subclasses of the EnergyConsumer,
    # EquivalentInjection,
    # ShuntCompensator,
    # StaticVarCompensator and
    # EnergySource.

    # Generators ------------------------------------------------------------
    gen_objects = multi_circuit.generators

    gen_ps = nc.generator_data.p
    gen_qs = pf_results.gen_q

    for (gen, gen_p, gen_q) in zip(gen_objects, gen_ps, gen_qs):

        term = find_object_by_cond_eq_uuid(
            object_list=cgmes_model.cgmes_assets.Terminal_list,
            cond_eq_target_uuid=gen.idtag
        )

        if is_term(term):

            create_sv_power_flow(
                cgmes_model=cgmes_model,
                p=gen_p,
                q=gen_q,
                terminal=term,
                ver=ver
            )

        else:
            logger.add_error(msg='No Terminal found for Generator',
                             device=gen,
                             device_class=gen.device_type.value,
                             value=gen.idtag)

    # Load-like devices -----------------------------------------------------
    # loads, static_generators, external_grids, current_injections
    load_objects = multi_circuit.get_load_like_devices()

    load_power = compute_zip_power(
        S0=nc.load_data.S,
        I0=nc.load_data.I,
        Y0=nc.load_data.Y,
        Vm=np.abs(pf_results.voltage[nc.load_data.get_bus_indices()])
    )

    for (mc_load_like, load_power) in zip(load_objects, load_power):

        term = find_object_by_cond_eq_uuid(
            object_list=cgmes_model.cgmes_assets.Terminal_list,
            cond_eq_target_uuid=mc_load_like.idtag  # missing Load uuid
        )

        if is_term(term):

            create_sv_power_flow(
                cgmes_model=cgmes_model,
                p=load_power.real,
                q=load_power.imag,
                terminal=term,
                ver=ver
            )

        else:
            logger.add_error(msg='No Terminal found for Load-like device',
                             device=mc_load_like,
                             device_class=mc_load_like.device_type.value,
                             value=mc_load_like.idtag)

    # Shunts ----------------------------------------------------------------
    # shunts, controllable shunts
    shunt_objects = multi_circuit.get_shunt_like_devices()

    shunt_qs = pf_results.shunt_q

    for (mc_shunt_like, shunt_q) in zip(shunt_objects, shunt_qs):

        term = find_object_by_cond_eq_uuid(
            object_list=cgmes_model.cgmes_assets.Terminal_list,
            cond_eq_target_uuid=mc_shunt_like.idtag  # missing Load uuid
        )
        if is_term(term):

            create_sv_power_flow(
                cgmes_model=cgmes_model,
                p=0.0,
                q=shunt_q,
                terminal=term,
                ver=ver
            )

        else:
            logger.add_error(msg='No Terminal found for Shunt-like device',
                             device=mc_shunt_like,
                             device_class=mc_shunt_like.device_type.value,
                             value=mc_shunt_like.idtag,
                             comment="SvPowerFlow is not exported.")


def get_cgmes_sv_power_flow_2(multi_circuit: MultiCircuit,
                              nc: NumericalCircuit,
                              cgmes_model: CgmesCircuit,
                              pf_results: PowerFlowResults,
                              ver: CGMESVersions,
                              logger: DataLogger) -> None:
    """
    For Branches:
    Creates a CgmesCircuit SvPowerFlow_list from PowerFlow results of the numerical circuit.

    :param multi_circuit:
    :param nc:
    :param cgmes_model:
    :param pf_results:
    :param ver:
    :param logger:
    :return: SvVoltage_list is populated in CgmesCircuit.
    """
    # SVPowerFlow: p, q -> Terminals
    # RuleDescription:
    # 	Branches shall have cim:SvPowerFlow instantiated at its cim:Terminals for
    # 	the following branch classes:
    # 	- cim:SeriesCompensator
    # 	- cim:ACLineSegment
    # 	- cim:PowerTransformer
    # 	- cim:EquivalentBranch
    # 	- cim:Switch where cim:Switch.retained is true.

    # Branches ------------------------------------------------------------
    branch_objects = multi_circuit.get_branches(add_vsc=False, add_hvdc=False, add_switch=True)

    for (branch, pf_res_from, pf_res_to) in zip(branch_objects, pf_results.Sf, pf_results.St):

        terminals = find_terminals_by_conducting_equipment_uuid(
            cgmes_model=cgmes_model,
            cond_eq_target_uuid=branch.idtag
        )
        if len(terminals) >= 1:

            create_sv_power_flow(
                cgmes_model=cgmes_model,
                p=pf_res_from.real,
                q=pf_res_from.imag,
                terminal=terminals[0],
                ver=ver
            )

            if len(terminals) >= 2:
                create_sv_power_flow(
                    cgmes_model=cgmes_model,
                    p=pf_res_to.real,
                    q=pf_res_to.imag,
                    terminal=terminals[1],
                    ver=ver
                )
        else:
            logger.add_error(msg='No Terminal found for Branch',
                             device=branch,
                             device_class=branch.device_type.value,
                             value=branch.idtag,
                             comment="get_cgmes_sv_power_flow_2()")


def get_cgmes_sv_tap_step(multi_circuit: MultiCircuit,
                          nc: NumericalCircuit,
                          cgmes_model: CgmesCircuit,
                          pf_results: PowerFlowResults,
                          ver: CGMESVersions,
                          logger: DataLogger) -> None:
    """
    Update SvTapStep.position for every tap changer using the solved power-flow
    tap module / tap angle instead of the nominal EQ step.

    :param multi_circuit:
    :param nc:
    :param cgmes_model:
    :param pf_results:
    :param ver:
    :param logger:
    :return:
    """
    branch_objects = multi_circuit.get_branches(add_vsc=False, add_hvdc=False, add_switch=True)

    # Build a lookup: VeraGrid branch idtag → (branch_index, branch)
    trafo_idx: dict[str, tuple[int, gcdev.Transformer2W]] = {}
    for idx, branch in enumerate(branch_objects):
        if isinstance(branch, gcdev.Transformer2W):
            trafo_idx[branch.idtag] = (idx, branch)

    tap_modules = pf_results.tap_module
    tap_angles = pf_results.tap_angle

    for sv in cgmes_model.cgmes_assets.SvTapStep_list:
        cgmes_tc = sv.TapChanger
        if cgmes_tc is None:
            continue

        pte = cgmes_tc.TransformerEnd
        if pte is None:
            continue

        power_transformer = pte.PowerTransformer
        if power_transformer is None:
            continue

        entry = trafo_idx.get(power_transformer.uuid)
        if entry is None:
            continue

        branch_idx, branch = entry
        tc = branch.tap_changer

        original_pos = tc.tap_position

        is_phase = isinstance(cgmes_tc, (cgmes24.PhaseTapChanger, cgmes30.PhaseTapChanger))

        if is_phase:
            tc.set_tap_phase(float(tap_angles[branch_idx]))
        else:
            tc.set_tap_module(float(tap_modules[branch_idx]))

        _, _, _, _, _, step = tc.get_cgmes_values()
        sv.position = float(step)

        tc.tap_position = original_pos


def get_cgmes_sv_shunt_compensator_sections(cgmes_model: CgmesCircuit,
                                            ver: CGMESVersions) -> None:
    """

    :param cgmes_model:
    :param ver:
    :return:
    """

    for shunts in [cgmes_model.cgmes_assets.LinearShuntCompensator_list,
                   cgmes_model.cgmes_assets.NonlinearShuntCompensator_list]:

        for shunt in shunts:
            create_sv_shunt_compensator_sections(
                cgmes_model=cgmes_model,
                sections=shunt.sections if shunt.sections is not None else 0,
                cgmes_shunt_compensator=shunt,
                ver=ver,
            )


def get_cgmes_topological_island(multicircuit_model: MultiCircuit,
                                 nc: NumericalCircuit,
                                 cgmes_model: CgmesCircuit,
                                 ver: CGMESVersions,
                                 logger: DataLogger):
    """

    :param multicircuit_model:
    :param nc:
    :param cgmes_model:
    :param ver:
    :param logger:
    :return:
    """
    nc_islands = nc.split_into_islands()

    i = 0
    for nc_i in nc_islands:
        i = i + 1

        if ver == CGMESVersions.v2_4_15:
            new_island = cgmes24.TopologicalIsland(get_new_rdfid())
        elif ver == CGMESVersions.v3_0_0:
            new_island = cgmes30.TopologicalIsland(get_new_rdfid())
        else:
            raise NotImplemented()

        new_island.name = "TopologicalIsland" + str(i)
        new_island.TopologicalNodes = []
        bus_idtags = nc_i.bus_data.idtag
        mc_buses = []
        for tn_idtag in bus_idtags:
            tn = find_object_by_uuid(cgmes_model=cgmes_model,
                                     object_list=cgmes_model.cgmes_assets.TopologicalNode_list,
                                     target_uuid=tn_idtag)

            if isinstance(tn, cgmes_model.assets.TopologicalNode):
                append_cgmes_relation_value(cgmes_object=new_island,
                                            property_name="TopologicalNodes",
                                            relation_value=tn,
                                            logger=logger,
                                            context="get_cgmes_topological_island()")
                mc_bus = find_object_by_attribute(multicircuit_model.buses, "idtag", tn_idtag)
                mc_buses.append(mc_bus)
            else:
                logger.add_warning(msg="TopologicalNode missing from TopologicalIsland!",
                                   device=new_island.name,
                                   device_property="TopologicalNode")
        if mc_buses:
            slack_bus = find_object_by_attribute(mc_buses, "is_slack", True)
            if slack_bus:
                slack_tn = find_object_by_uuid(cgmes_model,
                                               cgmes_model.cgmes_assets.TopologicalNode_list,
                                               slack_bus.idtag)

                if isinstance(slack_tn, cgmes_model.assets.TopologicalNode):
                    new_island.AngleRefTopologicalNode = slack_tn
                    for tn in new_island.TopologicalNodes:
                        tn.AngleRefTopologicalIsland = slack_tn
            else:
                logger.add_warning(
                    msg="AngleRefTopologicalNode missing from TopologicalIsland!",
                    device=new_island.name,
                    device_property="AngleRefTopologicalNode")
        else:
            logger.add_error(
                msg="All TopologicalNodes are missing from TopologicalIsland!",
                device=new_island.name,
                device_property="TopologicalNode")
        cgmes_model.add(new_island)


def make_coordinate_system(cgmes_model: CgmesCircuit,
                           ver: CGMESVersions,
                           logger: DataLogger):
    """

    :param cgmes_model:
    :param ver:
    :param logger:
    :return:
    """
    if ver == CGMESVersions.v2_4_15:
        coo_sys = cgmes24.CoordinateSystem(rdfid=get_new_rdfid())
    elif ver == CGMESVersions.v3_0_0:
        coo_sys = cgmes30.CoordinateSystem(rdfid=get_new_rdfid())
    else:
        raise NotImplemented()

    coo_sys.name = "EPSG4326"
    coo_sys.crsUrn = "urn:ogc:def:crs:EPSG::4326"
    if "Locations" in coo_sys.declared_properties:
        coo_sys.Locations = list()
    else:
        coo_sys.Location = list()

    cgmes_model.add(coo_sys)


def convert_hvdc_line_to_cgmes(multicircuit_model: MultiCircuit,
                               cgmes_model: CgmesCircuit,
                               ver: CGMESVersions,
                               logger: DataLogger,
                               t_idx: int | None = None):
    """
    Converts simplified HVDC line to two VSConverters inside DCConverterUnits,
    connected with a DCLineSegment, contained in a DCLine
    DCGround?
    DCNodes, DCTopologicalNodes are also created here from scratch
    as there is no DC part in the simplified modelling.

    :param multicircuit_model: MultiCircuit model in VeraGrid
    :param cgmes_model:
    :param ver:
    :param logger:
    :return:
    """

    for hvdc_line in multicircuit_model.hvdc_lines:
        # FROM side
        vsc_1, dc_conv_unit_1 = create_cgmes_vsc_converter(
            cgmes_model=cgmes_model,
            gc_vsc=None,
            p_set=hvdc_line.get_Pset_at(t_idx),
            v_set=hvdc_line.get_Vset_f_at(t_idx),
            target_upcc_base_voltage=(hvdc_line.bus_from.Vnom
                                      if hvdc_line.bus_from is not None and hvdc_line.bus_from.Vnom > 0.0
                                      else None),
            ver=ver,
            logger=logger
        )
        dc_tp_1 = create_cgmes_dc_tp_node(
            tp_name=f'DC_side_{hvdc_line.bus_from.name}',
            tp_description=f'DC_for_{hvdc_line.bus_from.code}',
            cgmes_model=cgmes_model,
            ver=ver,
            logger=logger
        )
        dc_node_1 = create_cgmes_dc_node(cn_name='DC_node_name',
                                         cn_description='DC_node_VSC_1',
                                         cgmes_model=cgmes_model,
                                         dc_tp=dc_tp_1,
                                         dc_ec=dc_conv_unit_1,
                                         ver=ver,
                                         logger=logger)

        create_cgmes_acdc_converter_terminal(
            cgmes_model=cgmes_model,
            mc_dc_bus=None,
            seq_num=2,
            dc_node=dc_node_1,
            dc_cond_eq=vsc_1,
            ver=ver,
            logger=logger
        )

        create_cgmes_terminal(
            cgmes_model=cgmes_model,
            mc_bus=hvdc_line.bus_from,
            seq_num=None,
            cond_eq=vsc_1,
            ver=ver,
            logger=logger
        )

        # TO side
        vsc_2, dc_conv_unit_2 = create_cgmes_vsc_converter(
            cgmes_model=cgmes_model,
            gc_vsc=None,
            p_set=-hvdc_line.get_Pset_at(t_idx),
            v_set=hvdc_line.get_Vset_t_at(t_idx),
            target_upcc_base_voltage=(hvdc_line.bus_to.Vnom
                                      if hvdc_line.bus_to is not None and hvdc_line.bus_to.Vnom > 0.0
                                      else None),
            ver=ver,
            logger=logger
        )
        dc_tp_2 = create_cgmes_dc_tp_node(
            tp_name=f'DC_side_{hvdc_line.bus_to.name}',
            tp_description=f'DC_for_{hvdc_line.bus_to.code}',
            cgmes_model=cgmes_model,
            ver=ver,
            logger=logger
        )
        dc_node_2 = create_cgmes_dc_node(cn_name='DC_node_name_2',
                                         cn_description='DC_node_VSC_2',
                                         cgmes_model=cgmes_model,
                                         dc_tp=dc_tp_2,
                                         dc_ec=dc_conv_unit_2,
                                         ver=ver,
                                         logger=logger)

        create_cgmes_acdc_converter_terminal(
            cgmes_model=cgmes_model,
            mc_dc_bus=None,
            seq_num=2,
            dc_node=dc_node_2,
            dc_cond_eq=vsc_2,
            ver=ver,
            logger=logger
        )

        create_cgmes_terminal(
            cgmes_model=cgmes_model,
            mc_bus=hvdc_line.bus_to,
            seq_num=None,
            cond_eq=vsc_2,
            ver=ver,
            logger=logger
        )

        # DC Line
        dc_line = create_cgmes_dc_line(cgmes_model=cgmes_model, ver=ver, logger=logger)
        create_cgmes_dc_line_segment(cgmes_model=cgmes_model,
                                     mc_elm=hvdc_line,
                                     dc_tp_1=dc_tp_1,
                                     dc_node_1=dc_node_1,
                                     dc_tp_2=dc_tp_2,
                                     dc_node_2=dc_node_2,
                                     eq_cont=dc_line,
                                     ver=ver,
                                     logger=logger)

    return


def get_cgmes_busbar_sections(gc_model: MultiCircuit,
                               cgmes_model: CgmesCircuit,
                               ver: CGMESVersions,
                               logger: DataLogger) -> None:
    """
    Create one BusbarSection per VeraGrid Bus.
    Each BusbarSection is contained in the bus VoltageLevel and connected to
    its TopologicalNode via a Terminal, completing the node-breaker topology.

    :param gc_model: VeraGrid MultiCircuit
    :param cgmes_model: CgmesCircuit
    :param ver: CGMES version
    :param logger: DataLogger
    :return: None
    """
    for mc_bus in gc_model.buses:
        if ver == CGMESVersions.v2_4_15:
            bbs = cgmes24.BusbarSection(rdfid=get_new_rdfid())
        elif ver == CGMESVersions.v3_0_0:
            bbs = cgmes30.BusbarSection(rdfid=get_new_rdfid())
        else:
            raise NotImplemented()

        bbs.name = mc_bus.name
        bbs.description = mc_bus.code

        if mc_bus.voltage_level is not None:
            vl = find_object_by_uuid(
                cgmes_model=cgmes_model,
                object_list=cgmes_model.cgmes_assets.VoltageLevel_list,
                target_uuid=mc_bus.voltage_level.idtag
            )
            if isinstance(vl, cgmes_model.assets.VoltageLevel):
                bbs.EquipmentContainer = vl

        bbs.Terminals = create_cgmes_terminal(
            mc_bus=mc_bus,
            seq_num=1,
            cond_eq=bbs,
            cgmes_model=cgmes_model,
            ver=ver,
            logger=logger
        )

        cgmes_model.add(bbs)


def is_hex_uuid_token(value: str) -> bool:
    """
    Check whether a string is a 32-hex UUID token.

    :param value: Candidate token.
    :return: ``True`` when the token is 32 hexadecimal characters.
    """
    if len(value) == 32:
        try:
            int(value, 16)
            return True
        except ValueError:
            return False
    else:
        return False


def build_cgmes_rdfid_from_veragrid_idtag(veragrid_idtag: str) -> str:
    """
    Build a CGMES RDF identifier from a VeraGrid idtag.

    :param veragrid_idtag: VeraGrid object idtag.
    :return: CGMES rdfid string.
    """
    stripped_idtag: str = veragrid_idtag.strip()
    if len(stripped_idtag) == 0:
        return get_new_rdfid()
    else:
        normalized_idtag: str = stripped_idtag.replace('-', '').replace('_', '')
        if is_hex_uuid_token(normalized_idtag):
            return form_rdfid(normalized_idtag)
        else:
            return stripped_idtag


def resolve_cgmes_equipment_by_veragrid_idtag(cgmes_model: CgmesCircuit,
                                              veragrid_idtag: str) -> CGMES_ASSETS | None:
    """
    Resolve one exported CGMES equipment object by VeraGrid idtag.

    :param cgmes_model: Target CGMES model.
    :param veragrid_idtag: VeraGrid equipment idtag.
    :return: CGMES equipment object or ``None`` when not found.
    """
    stripped_idtag: str = veragrid_idtag.strip()
    if len(stripped_idtag) == 0:
        return None
    else:
        candidate_rdfid: str = build_cgmes_rdfid_from_veragrid_idtag(veragrid_idtag=stripped_idtag)
        candidate_equipment: CGMES_ASSETS | None = cgmes_model.all_objects_dict.get(candidate_rdfid, None)
        if candidate_equipment is not None:
            return candidate_equipment
        else:
            direct_equipment: CGMES_ASSETS | None = cgmes_model.all_objects_dict.get(stripped_idtag, None)
            if direct_equipment is not None:
                return direct_equipment
            else:
                normalized_idtag: str = stripped_idtag.replace('-', '').replace('_', '')
                if len(normalized_idtag) > 0:
                    for cgmes_object in cgmes_model.all_objects_dict.values():
                        if cgmes_object.uuid == normalized_idtag:
                            return cgmes_object
                        else:
                            pass
                    return None
                else:
                    return None


def map_contingency_status_uri(contingency_value: float) -> str:
    """
    Map VeraGrid contingency Active value to the NCP status URI.

    :param contingency_value: VeraGrid contingency value.
    :return: ContingencyEquipmentStatusKind URI.
    """
    if np.isclose(contingency_value, 0.0):
        return "https://cim.ucaiug.io/ns#ContingencyEquipmentStatusKind.outOfService"
    else:
        return "https://cim.ucaiug.io/ns#ContingencyEquipmentStatusKind.inService"


def get_cgmes_contingencies(multicircuit_model: MultiCircuit,
                            cgmes_model: CgmesCircuit,
                            logger: DataLogger) -> None:
    """
    Export VeraGrid contingencies to CGMES NCP contingency objects.

    Mapping strategy:
        - One VeraGrid ``ContingencyGroup`` -> one NCP ``OrdinaryContingency``.
        - One VeraGrid ``Contingency`` -> one NCP ``ContingencyEquipment``.
        - VeraGrid ``ContingencyOperationTypes.Active`` value -> NCP contingent status URI.

    :param multicircuit_model: Source VeraGrid model.
    :param cgmes_model: Target CGMES model.
    :param logger: Data logger.
    :return: Nothing.
    """
    if len(multicircuit_model.contingencies) == 0:
        return
    else:
        pass

    class_dict: Dict[str, type] = cgmes_model.cgmes_assets.class_dict
    ordinary_contingency_class: type | None = class_dict.get("OrdinaryContingency", None)
    contingency_equipment_class: type | None = class_dict.get("ContingencyEquipment", None)

    if ordinary_contingency_class is None:
        logger.add_warning(
            msg='CGMES model has no OrdinaryContingency class; skipping contingency export'
        )
        return
    else:
        if contingency_equipment_class is None:
            logger.add_warning(
                msg='CGMES model has no ContingencyEquipment class; skipping contingency export'
            )
            return
        else:
            pass

    contingencies_by_group: Dict[gcdev.ContingencyGroup, List[gcdev.Contingency]] = (
        multicircuit_model.get_contingencies_by_group()
    )
    if len(contingencies_by_group) == 0:
        return
    else:
        pass

    exported_group_count: int = 0
    exported_contingency_count: int = 0
    skipped_contingency_count: int = 0

    for group, contingency_list in contingencies_by_group.items():
        group_rdfid: str = build_cgmes_rdfid_from_veragrid_idtag(veragrid_idtag=group.idtag)
        cgmes_group: CGMES_ASSETS = ordinary_contingency_class(rdfid=group_rdfid)

        if len(group.name) > 0:
            group_name: str = group.name
        else:
            group_name = group.idtag

        cgmes_group.name = group_name
        cgmes_group.description = str(group.category)
        cgmes_group.normalMustStudy = group.active
        cgmes_group.mustStudy = group.active

        contingency_elements: List[CGMES_ASSETS] = list()

        for contingency in contingency_list:
            if contingency.prop == ContingencyOperationTypes.Active:
                target_equipment: CGMES_ASSETS | None = resolve_cgmes_equipment_by_veragrid_idtag(
                    cgmes_model=cgmes_model,
                    veragrid_idtag=contingency.device_idtag
                )
                if target_equipment is None:
                    skipped_contingency_count += 1
                    logger.add_warning(
                        msg='Could not resolve CGMES equipment for contingency export',
                        device=contingency.idtag,
                        device_class=contingency.device_type.value,
                        device_property='device_idtag',
                        value=contingency.device_idtag
                    )
                else:
                    contingency_rdfid: str = build_cgmes_rdfid_from_veragrid_idtag(
                        veragrid_idtag=contingency.idtag
                    )
                    cgmes_equipment_contingency: CGMES_ASSETS = contingency_equipment_class(rdfid=contingency_rdfid)

                    if len(contingency.device_name) > 0:
                        contingency_target_name: str = contingency.device_name
                    else:
                        contingency_target_name = contingency.device_idtag

                    cgmes_equipment_contingency.name = f"{group_name}::{contingency_target_name}"
                    cgmes_equipment_contingency.description = contingency.comment
                    cgmes_equipment_contingency.Contingency = cgmes_group
                    cgmes_equipment_contingency.Equipment = target_equipment
                    cgmes_equipment_contingency.contingentStatus = map_contingency_status_uri(
                        contingency_value=contingency.value
                    )

                    contingency_elements.append(cgmes_equipment_contingency)
                    cgmes_model.add(cgmes_equipment_contingency)
                    exported_contingency_count += 1
            else:
                skipped_contingency_count += 1
                logger.add_warning(
                    msg='Unsupported contingency operation type for CGMES export',
                    device=contingency.idtag,
                    device_class=contingency.device_type.value,
                    device_property='prop',
                    value=str(contingency.prop),
                    expected_value=str(ContingencyOperationTypes.Active)
                )

        if len(contingency_elements) > 0:
            cgmes_group.ContingencyElement = contingency_elements
            cgmes_model.add(cgmes_group)
            exported_group_count += 1
        else:
            pass

    if exported_contingency_count > 0:
        logger.add_info(
            msg='Exported NCP contingencies',
            value=exported_contingency_count,
            expected_value=len(multicircuit_model.contingencies),
            comment=f"Groups={exported_group_count}, Skipped={skipped_contingency_count}"
        )
    else:
        pass


# endregion


def veragrid_to_cgmes(gc_model: MultiCircuit,
                      num_circ: NumericalCircuit,
                      pf_results: Union[None, PowerFlowResults],
                      cgmes_model: CgmesCircuit,
                      logger: DataLogger,
                      t_idx: int | None = None) -> CgmesCircuit:
    """
    Converts the input Multi circuit to a new CGMES Circuit.

    :param gc_model: Multi circuit object
    :param num_circ: Numerical circuit complied from MC
    :param cgmes_model: CGMES circuit object
    :param pf_results: power flow results from VeraGrid
    :param logger: Logger object
    :return: CGMES circuit (as a new object)
    """
    ver = cgmes_model.cgmes_version

    get_cgmes_geograpical_regions(gc_model, cgmes_model, ver, logger)
    get_cgmes_sub_geographical_regions(gc_model, cgmes_model, ver, logger)

    make_coordinate_system(cgmes_model, ver, logger)

    get_cgmes_base_voltages(gc_model, cgmes_model, ver, logger)

    get_cgmes_substations(gc_model, cgmes_model, ver, logger)
    get_cgmes_voltage_levels(gc_model, cgmes_model, ver, logger)

    if ver == CGMESVersions.v3_0_0:
        purge_connectivity_nodes_for_cgmes_v3(cgmes_model=cgmes_model, logger=logger)
    else:
        pass

    get_cgmes_tp_nodes(gc_model, cgmes_model, ver, logger)
    get_cgmes_cn_nodes_from_tp_nodes(gc_model, cgmes_model, ver, logger)
    get_cgmes_busbar_sections(gc_model, cgmes_model, ver, logger)

    get_cgmes_loads(gc_model, cgmes_model, ver, logger, t_idx=t_idx)
    get_or_create_external_network_injection(gc_model, cgmes_model, ver, logger, t_idx=t_idx)
    get_cgmes_generators(gc_model, cgmes_model, ver, logger, t_idx=t_idx)

    # Get operational limit types
    operational_limit_type_list = get_cgmes_operational_limit_types(cgmes_model, ver)
    # patl, tatl_900, tatl_60

    # BRANCHES
    # lines
    get_cgmes_ac_line_segments(gc_model, cgmes_model, operational_limit_type_list, ver, logger, t_idx=t_idx)
    # transformers, windings
    get_cgmes_power_transformers(gc_model, cgmes_model, operational_limit_type_list, ver, logger, t_idx=t_idx)

    # SHUNTS
    get_cgmes_equivalent_shunts(gc_model, cgmes_model, ver, logger, t_idx=t_idx)
    get_cgmes_linear_and_non_linear_shunts(gc_model, cgmes_model, ver, logger, t_idx=t_idx)

    # Switches (Breakers)
    get_cgmes_breakers(gc_model, cgmes_model, ver, logger, t_idx=t_idx)

    # DC elements
    convert_hvdc_line_to_cgmes(gc_model, cgmes_model, ver, logger, t_idx=t_idx)
    convert_vsc_devices_to_cgmes(gc_model, cgmes_model, ver, logger, t_idx=t_idx)
    convert_dc_lines_to_cgmes(gc_model, cgmes_model, ver, logger)

    # NCP contingencies are exported after equipment so references are resolvable.
    get_cgmes_contingencies(multicircuit_model=gc_model,
                            cgmes_model=cgmes_model,
                            logger=logger)

    # RESULTS: sv classes
    if pf_results:
        # if converged == True...

        # SvVoltage for every TopoNode
        get_cgmes_sv_voltages(gc_model, cgmes_model, pf_results, ver, logger)

        # PowerFlow: P, Q results for every terminal
        get_cgmes_sv_power_flow_1(gc_model, num_circ, cgmes_model, pf_results, ver, logger)
        get_cgmes_sv_power_flow_2(gc_model, num_circ, cgmes_model, pf_results, ver, logger)

        # SV Status: for ConductingEquipment
        export_sv_statuses(gc_model, cgmes_model, ver, t_idx=t_idx)

        # SVTapStep: handled at transformer function
        # TODO get it from results
        get_cgmes_sv_tap_step(gc_model, num_circ, cgmes_model, pf_results, ver, logger)

        # SvShuntCompensatorSections:
        get_cgmes_sv_shunt_compensator_sections(cgmes_model, ver)

        # Topological Islands
        get_cgmes_topological_island(gc_model, num_circ, cgmes_model, ver, logger)

    else:
        logger.add_error(msg="Missing power flow result for CGMES export.")

    if logger.has_logs():
        print("\nLogger is not empty! (cgmes export)")

    return cgmes_model
