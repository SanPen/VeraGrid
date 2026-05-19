# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

import VeraGridEngine.Devices as gcdev
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.cim.cgmes.CgmestoVeraGrid.ncp_availability import (
    apply_ncp_availability_profiles,
    collect_ncp_availability_timestamps,
)
from VeraGridEngine.IO.cim.cgmes.CgmestoVeraGrid.ncp_contingencies import build_contingency_device_lookup
from VeraGridEngine.IO.cim.cgmes.CgmestoVeraGrid.ncp_remedials import (
    collect_grid_state_range_constraints,
    normalize_property_reference_text,
)
from VeraGridEngine.IO.cim.cgmes.cgmes_circuit import CgmesCircuit
from VeraGridEngine.IO.cim.cgmes.cgmes_typing import CGMES_ASSETS
from VeraGridEngine.data_logger import DataLogger
from VeraGridEngine.enumerations import CGMESVersions


def parse_ncp_time_to_utc_timestamp(raw_time: str | None,
                                    logger: DataLogger,
                                    source_object: CGMES_ASSETS | None = None) -> pd.Timestamp | None:
    """
    Parse one NCP timestamp string into a UTC pandas timestamp.

    :param raw_time: Serialized datetime text.
    :param logger: Data logger.
    :param source_object: Source CGMES object for diagnostics.
    :return: Parsed UTC timestamp or ``None``.
    """
    if raw_time is None:
        return None
    else:
        pass

    parsed_time: pd.Timestamp | None = None
    parsed_candidate = pd.to_datetime(raw_time, utc=True, errors='coerce')
    if pd.isna(parsed_candidate):
        if source_object is None:
            logger.add_warning(
                msg='Invalid NCP time point ignored',
                device_class='NCP',
                device_property='atTime',
                value=raw_time
            )
        else:
            logger.add_warning(
                msg='Invalid NCP time point ignored',
                device=source_object.rdfid,
                device_class=source_object.tpe,
                device_property='atTime',
                value=raw_time
            )
    else:
        parsed_time = pd.Timestamp(parsed_candidate)

    return parsed_time


def collect_ncp_ps_sis_timestamps(cgmes_model: CgmesCircuit,
                                  logger: DataLogger) -> List[pd.Timestamp]:
    """
    Collect every PS/SIS schedule timestamp used for profile initialization.

    :param cgmes_model: CGMES model.
    :param logger: Data logger.
    :return: List of parsed UTC timestamps.
    """
    collected_timestamps: List[pd.Timestamp] = list()

    for power_time_point in cgmes_model.cgmes_assets.PowerTimePoint_list:
        parsed_time: pd.Timestamp | None = parse_ncp_time_to_utc_timestamp(
            raw_time=power_time_point.atTime,
            logger=logger,
            source_object=power_time_point
        )
        if parsed_time is None:
            pass
        else:
            collected_timestamps.append(parsed_time)

    for grid_state_time_point in cgmes_model.cgmes_assets.GridStateAlterationTimePoint_list:
        parsed_time = parse_ncp_time_to_utc_timestamp(
            raw_time=grid_state_time_point.atTime,
            logger=logger,
            source_object=grid_state_time_point
        )
        if parsed_time is None:
            pass
        else:
            collected_timestamps.append(parsed_time)

    return collected_timestamps


def build_time_index_lookup_from_profile(time_profile: pd.DatetimeIndex) -> Dict[int, int]:
    """
    Build nanosecond-timestamp to profile-index lookup for one time profile.

    :param time_profile: Grid time profile.
    :return: Mapping from nanoseconds since epoch to profile index.
    """
    time_lookup: Dict[int, int] = dict()
    for time_index, timestamp in enumerate(time_profile):
        timestamp_ns: int = int(pd.Timestamp(timestamp).value)
        if timestamp_ns in time_lookup:
            pass
        else:
            time_lookup[timestamp_ns] = int(time_index)
    return time_lookup


def get_first_resolved_cgmes_reference(reference: object) -> object | None:
    """
    Resolve the first object reference from a CGMES property.

    :param reference: Raw CGMES relation value.
    :return: First resolved object reference or ``None``.
    """
    if reference is None:
        return None
    elif isinstance(reference, str):
        return None
    elif isinstance(reference, list):
        for reference_item in reference:
            if reference_item is None:
                pass
            elif isinstance(reference_item, str):
                pass
            else:
                return reference_item
        return None
    else:
        return reference


def get_first_resolved_cgmes_reference_uuid(reference: object) -> str | None:
    """
    Resolve the first object UUID from a CGMES property.

    :param reference: Raw CGMES relation value.
    :return: UUID of the first resolved object or ``None``.
    """
    resolved_reference: object | None = get_first_resolved_cgmes_reference(reference=reference)
    if resolved_reference is None:
        return None
    else:
        return resolved_reference.uuid


def ensure_ncp_instruction_time_profile(gcdev_model: MultiCircuit,
                                        timestamps: List[pd.Timestamp],
                                        logger: DataLogger) -> Dict[int, int]:
    """
    Ensure VeraGrid time profile exists for PS/SIS instructions and return index lookup.

    :param gcdev_model: VeraGrid model.
    :param timestamps: Collected PS/SIS timestamps.
    :param logger: Data logger.
    :return: Nanosecond-timestamp to profile-index mapping.
    """
    if len(timestamps) == 0:
        return dict()
    else:
        pass

    timestamp_ns_set: set[int] = set()
    for timestamp in timestamps:
        timestamp_ns_set.add(int(timestamp.value))

    normalized_ns_values: List[int] = sorted(list(timestamp_ns_set))
    normalized_new_index: pd.DatetimeIndex = pd.to_datetime(
        np.array(normalized_ns_values, dtype=np.int64),
        utc=True
    )

    existing_time_profile: pd.DatetimeIndex | None = gcdev_model.time_profile
    if existing_time_profile is None:
        combined_index: pd.DatetimeIndex = normalized_new_index
    elif len(existing_time_profile) == 0:
        combined_index = normalized_new_index
    else:
        merged_ns_set: set[int] = set()
        for timestamp in existing_time_profile:
            merged_ns_set.add(int(pd.Timestamp(timestamp).value))
        for timestamp in normalized_new_index:
            merged_ns_set.add(int(pd.Timestamp(timestamp).value))

        merged_ns_values: List[int] = sorted(list(merged_ns_set))
        combined_index = pd.to_datetime(np.array(merged_ns_values, dtype=np.int64), utc=True)

    gcdev_model.format_profiles(index=combined_index)

    logger.add_info(
        msg='Initialized VeraGrid profiles for NCP PS/SIS instructions',
        value=len(normalized_new_index),
        expected_value=len(combined_index)
    )

    return build_time_index_lookup_from_profile(time_profile=combined_index)


def build_ncp_instruction_device_lookup(cgmes_model: CgmesCircuit,
                                        gcdev_model: MultiCircuit) -> Dict[str, object]:
    """
    Build a device lookup used by PS/SIS/SSI conversions.

    :param cgmes_model: CGMES model.
    :param gcdev_model: VeraGrid model.
    :return: Device lookup dictionary.
    """
    device_lookup: Dict[str, object] = build_contingency_device_lookup(gcdev_model=gcdev_model)

    for synchronous_machine in cgmes_model.cgmes_assets.SynchronousMachine_list:
        generating_unit_uuid: str | None = get_first_resolved_cgmes_reference_uuid(
            reference=synchronous_machine.GeneratingUnit
        )
        if generating_unit_uuid is None:
            pass
        else:
            generator_device: object | None = device_lookup.get(synchronous_machine.uuid, None)
            if generator_device is None:
                pass
            else:
                if generating_unit_uuid in device_lookup:
                    pass
                else:
                    device_lookup[generating_unit_uuid] = generator_device

    for regulating_control in cgmes_model.cgmes_assets.RegulatingControl_list:
        controlled_equipment_uuid: str | None = None

        regulating_cond_eq_uuid: str | None = get_first_resolved_cgmes_reference_uuid(
            reference=regulating_control.RegulatingCondEq
        )
        if regulating_cond_eq_uuid is None:
            terminal_ref: object | None = get_first_resolved_cgmes_reference(
                reference=regulating_control.Terminal
            )
            if terminal_ref is None:
                pass
            else:
                controlled_equipment_uuid = get_first_resolved_cgmes_reference_uuid(
                    reference=terminal_ref.ConductingEquipment
                )
        else:
            controlled_equipment_uuid = regulating_cond_eq_uuid

        if controlled_equipment_uuid is None:
            pass
        else:
            controlled_device: object | None = device_lookup.get(controlled_equipment_uuid, None)
            if controlled_device is None:
                pass
            else:
                if regulating_control.uuid in device_lookup:
                    pass
                else:
                    device_lookup[regulating_control.uuid] = controlled_device

    tap_changer_lists: List[List[CGMES_ASSETS]] = list()
    if cgmes_model.cgmes_version == CGMESVersions.v3_0_0:
        tap_changer_lists.append(cgmes_model.cgmes_assets.RatioTapChanger_list)
        tap_changer_lists.append(cgmes_model.cgmes_assets.PhaseTapChanger_list)
        tap_changer_lists.append(cgmes_model.cgmes_assets.PhaseTapChangerAsymmetrical_list)
        tap_changer_lists.append(cgmes_model.cgmes_assets.PhaseTapChangerLinear_list)
        tap_changer_lists.append(cgmes_model.cgmes_assets.PhaseTapChangerNonLinear_list)
        tap_changer_lists.append(cgmes_model.cgmes_assets.PhaseTapChangerSymmetrical_list)
        tap_changer_lists.append(cgmes_model.cgmes_assets.PhaseTapChangerTabular_list)
    else:
        pass

    for tap_changer_list in tap_changer_lists:
        for tap_changer in tap_changer_list:
            transformer_uuid: str | None = None
            transformer_end_ref: object | None = get_first_resolved_cgmes_reference(
                reference=tap_changer.TransformerEnd
            )
            if transformer_end_ref is None:
                pass
            else:
                transformer_uuid = get_first_resolved_cgmes_reference_uuid(
                    reference=transformer_end_ref.PowerTransformer
                )

            if transformer_uuid is None:
                pass
            else:
                transformer_device: object | None = device_lookup.get(transformer_uuid, None)
                if transformer_device is None:
                    pass
                else:
                    if tap_changer.uuid in device_lookup:
                        pass
                    else:
                        device_lookup[tap_changer.uuid] = transformer_device

    return device_lookup


def resolve_power_schedule_target_devices(power_schedule: CGMES_ASSETS,
                                          device_lookup: Dict[str, object]) -> List[object]:
    """
    Resolve target VeraGrid devices for one PowerSchedule object.

    :param power_schedule: NCP PowerSchedule object.
    :param device_lookup: CGMES UUID to VeraGrid device lookup.
    :return: Ordered unique list of target devices.
    """
    target_devices: List[object] = list()
    seen_device_idtags: set[str] = set()

    candidate_references: List[object] = list()
    candidate_references.append(power_schedule.GeneratingUnit)
    candidate_references.append(power_schedule.EquivalentInjection)
    candidate_references.append(power_schedule.EnergyConnection)
    candidate_references.append(power_schedule.HydroPump)
    candidate_references.append(power_schedule.PowerElectronicsUnit)

    for candidate_reference in candidate_references:
        if candidate_reference is None:
            pass
        elif isinstance(candidate_reference, list):
            for candidate_reference_item in candidate_reference:
                if candidate_reference_item is None or isinstance(candidate_reference_item, str):
                    pass
                else:
                    target_device: object | None = device_lookup.get(candidate_reference_item.uuid, None)
                    if target_device is None:
                        pass
                    else:
                        target_device_idtag: str = target_device.idtag
                        if target_device_idtag in seen_device_idtags:
                            pass
                        else:
                            target_devices.append(target_device)
                            seen_device_idtags.add(target_device_idtag)
        else:
            if isinstance(candidate_reference, str):
                target_device = None
            else:
                target_device = device_lookup.get(candidate_reference.uuid, None)
            if target_device is None:
                pass
            else:
                target_device_idtag: str = target_device.idtag
                if target_device_idtag in seen_device_idtags:
                    pass
                else:
                    target_devices.append(target_device)
                    seen_device_idtags.add(target_device_idtag)

    return target_devices


def extract_grid_state_action_setpoint_value(grid_state_action: CGMES_ASSETS) -> float | None:
    """
    Extract the first numeric setpoint candidate from action range constraints.

    :param grid_state_action: NCP GridStateAlteration-derived action.
    :return: Numeric setpoint candidate or ``None``.
    """
    resolved_value: float | None = None
    range_constraints: List[CGMES_ASSETS] = collect_grid_state_range_constraints(
        grid_state_action=grid_state_action
    )

    for range_constraint in range_constraints:
        if isinstance(range_constraint.value, (float, int)):
            resolved_value = float(range_constraint.value)
        elif isinstance(range_constraint.normalValue, (float, int)):
            resolved_value = float(range_constraint.normalValue)
        else:
            pass

        if resolved_value is None:
            pass
        else:
            break

    return resolved_value


def resolve_grid_state_action_target_device(grid_state_action: CGMES_ASSETS,
                                            device_lookup: Dict[str, object],
                                            logger: DataLogger) -> object | None:
    """
    Resolve one VeraGrid target device for a GridStateAlteration action.

    :param grid_state_action: NCP action object.
    :param device_lookup: CGMES UUID to VeraGrid device lookup.
    :param logger: Data logger.
    :return: Target device or ``None``.
    """
    target_reference: object | None = None

    if grid_state_action.tpe == 'TopologyAction':
        target_reference = grid_state_action.Switch
    elif grid_state_action.tpe == 'RotatingMachineAction':
        target_reference = grid_state_action.RotatingMachine
    elif grid_state_action.tpe == 'RegulatingControlAction':
        target_reference = grid_state_action.RegulatingControl
    elif grid_state_action.tpe == 'EquivalentInjectionAction':
        target_reference = grid_state_action.EquivalentInjection
    elif grid_state_action.tpe == 'LoadAction':
        target_reference = grid_state_action.EnergyConsumer
    elif grid_state_action.tpe == 'TapPositionAction':
        target_reference = grid_state_action.TapChanger
    elif grid_state_action.tpe == 'StaticVarCompensatorAction':
        target_reference = grid_state_action.StaticVarCompensator
    else:
        target_reference = None

    if target_reference is None:
        logger.add_warning(
            msg='Unsupported NCP action type for SIS/SSI conversion',
            device=grid_state_action.rdfid,
            device_class=grid_state_action.tpe
        )
        return None
    elif isinstance(target_reference, str):
        logger.add_warning(
            msg='NCP action target reference unresolved',
            device=grid_state_action.rdfid,
            device_class=grid_state_action.tpe,
            value=target_reference
        )
        return None
    else:
        target_device: object | None = device_lookup.get(target_reference.uuid, None)
        if target_device is None:
            logger.add_warning(
                msg='NCP action target not imported in VeraGrid model',
                device=grid_state_action.rdfid,
                device_class=grid_state_action.tpe,
                value=target_reference.uuid
            )
            return None
        else:
            return target_device


def get_action_property_and_value(grid_state_action: CGMES_ASSETS,
                                  logger: DataLogger) -> Tuple[str | None, float | bool | None]:
    """
    Map one GridStateAlteration action to VeraGrid property/value pair.

    :param grid_state_action: NCP action object.
    :param logger: Data logger.
    :return: Tuple (property_name, property_value) where each entry may be ``None``.
    """
    property_reference_text: str = normalize_property_reference_text(grid_state_action.PropertyReference)
    setpoint_value: float | None = extract_grid_state_action_setpoint_value(grid_state_action=grid_state_action)

    if "switch.open" in property_reference_text:
        switch_open_target: bool = True
        if setpoint_value is None:
            pass
        elif setpoint_value >= 0.5:
            switch_open_target = True
        else:
            switch_open_target = False

        if switch_open_target:
            return "active", 0.0
        else:
            return "active", 1.0

    elif "rotatingmachine.p" in property_reference_text:
        return "P", setpoint_value
    elif "rotatingmachine.q" in property_reference_text:
        return "Q", setpoint_value
    elif "regulatingcontrol.targetvalue" in property_reference_text:
        return "Vset", setpoint_value
    elif "equivalentinjection.p" in property_reference_text:
        return "P", setpoint_value
    elif "equivalentinjection.q" in property_reference_text:
        return "Q", setpoint_value
    elif "energyconsumer.p" in property_reference_text:
        return "P", setpoint_value
    elif "energyconsumer.q" in property_reference_text:
        return "Q", setpoint_value
    elif "tapchanger.step" in property_reference_text:
        logger.add_warning(
            msg='TapChanger step action is not converted yet in SIS/SSI conversion',
            device=grid_state_action.rdfid,
            device_class=grid_state_action.tpe,
            device_property='PropertyReference',
            value=grid_state_action.PropertyReference
        )
        return None, None
    else:
        logger.add_warning(
            msg='Unsupported PropertyReference in SIS/SSI conversion',
            device=grid_state_action.rdfid,
            device_class=grid_state_action.tpe,
            device_property='PropertyReference',
            value=grid_state_action.PropertyReference
        )
        return None, None


def set_device_property_at_time(target_device: object,
                                property_name: str,
                                property_value: float | bool,
                                time_index: int | None,
                                source_action: CGMES_ASSETS,
                                logger: DataLogger) -> bool:
    """
    Set one VeraGrid property value for snapshot or profile time index.

    :param target_device: VeraGrid device.
    :param property_name: VeraGrid property name.
    :param property_value: Property value to set.
    :param time_index: Time index or ``None`` for snapshot.
    :param source_action: Source CGMES action.
    :param logger: Data logger.
    :return: ``True`` when assignment succeeded.
    """
    registered_property = target_device.registered_properties.get(property_name, None)
    if registered_property is None:
        logger.add_warning(
            msg='Target device does not expose requested NCP property',
            device=source_action.rdfid,
            device_class=source_action.tpe,
            device_property=property_name,
            value=target_device.idtag
        )
        return False
    else:
        target_device.set_property_value(
            prop=registered_property,
            value=property_value,
            t_idx=time_index
        )
        return True


def apply_power_schedule_profiles(cgmes_model: CgmesCircuit,
                                  gcdev_model: MultiCircuit,
                                  device_lookup: Dict[str, object],
                                  time_index_lookup: Dict[int, int],
                                  logger: DataLogger) -> int:
    """
    Apply NCP PowerSchedule (PS) setpoints into VeraGrid profiles.

    :param cgmes_model: CGMES model.
    :param gcdev_model: VeraGrid model.
    :param device_lookup: CGMES UUID to VeraGrid device lookup.
    :param time_index_lookup: Timestamp-ns to profile-index lookup.
    :param logger: Data logger.
    :return: Number of successful profile assignments.
    """
    applied_assignment_count: int = 0

    for power_time_point in cgmes_model.cgmes_assets.PowerTimePoint_list:
        parsed_time: pd.Timestamp | None = parse_ncp_time_to_utc_timestamp(
            raw_time=power_time_point.atTime,
            logger=logger,
            source_object=power_time_point
        )
        if parsed_time is None:
            pass
        else:
            time_index: int | None = time_index_lookup.get(int(parsed_time.value), None)
            if time_index is None:
                logger.add_warning(
                    msg='PowerTimePoint timestamp not found in initialized profile',
                    device=power_time_point.rdfid,
                    device_class=power_time_point.tpe,
                    device_property='atTime',
                    value=power_time_point.atTime
                )
            else:
                power_schedule_ref: object = power_time_point.PowerSchedule
                if power_schedule_ref is None or isinstance(power_schedule_ref, str):
                    logger.add_warning(
                        msg='PowerTimePoint without resolved PowerSchedule reference',
                        device=power_time_point.rdfid,
                        device_class=power_time_point.tpe,
                        device_property='PowerSchedule',
                        value=power_schedule_ref
                    )
                else:
                    target_devices: List[object] = resolve_power_schedule_target_devices(
                        power_schedule=power_schedule_ref,
                        device_lookup=device_lookup
                    )
                    if len(target_devices) == 0:
                        logger.add_warning(
                            msg='PowerSchedule target devices not imported',
                            device=power_schedule_ref.rdfid,
                            device_class=power_schedule_ref.tpe
                        )
                    else:
                        p_value_raw: float | None = None
                        if isinstance(power_time_point.activatedP, (float, int)):
                            p_value_raw = float(power_time_point.activatedP)
                        elif isinstance(power_time_point.p, (float, int)):
                            p_value_raw = float(power_time_point.p)
                        else:
                            pass

                        q_value_raw: float | None = None
                        if isinstance(power_time_point.activatedQ, (float, int)):
                            q_value_raw = float(power_time_point.activatedQ)
                        elif isinstance(power_time_point.q, (float, int)):
                            q_value_raw = float(power_time_point.q)
                        else:
                            pass

                        for target_device in target_devices:
                            if p_value_raw is None:
                                pass
                            else:
                                if isinstance(target_device, gcdev.Generator):
                                    p_value_to_apply: float = -float(p_value_raw)
                                else:
                                    p_value_to_apply = float(p_value_raw)

                                if set_device_property_at_time(
                                    target_device=target_device,
                                    property_name='P',
                                    property_value=p_value_to_apply,
                                    time_index=time_index,
                                    source_action=power_time_point,
                                    logger=logger
                                ):
                                    applied_assignment_count += 1
                                else:
                                    pass

                            if q_value_raw is None:
                                pass
                            else:
                                if set_device_property_at_time(
                                    target_device=target_device,
                                    property_name='Q',
                                    property_value=float(q_value_raw),
                                    time_index=time_index,
                                    source_action=power_time_point,
                                    logger=logger
                                ):
                                    applied_assignment_count += 1
                                else:
                                    pass

    return applied_assignment_count


def apply_sis_profiles(cgmes_model: CgmesCircuit,
                       device_lookup: Dict[str, object],
                       time_index_lookup: Dict[int, int],
                       logger: DataLogger) -> int:
    """
    Apply StateInstructionSchedule (SIS) time-point actions into VeraGrid profiles.

    :param cgmes_model: CGMES model.
    :param device_lookup: CGMES UUID to VeraGrid device lookup.
    :param time_index_lookup: Timestamp-ns to profile-index lookup.
    :param logger: Data logger.
    :return: Number of successful profile assignments.
    """
    applied_assignment_count: int = 0

    for grid_state_time_point in cgmes_model.cgmes_assets.GridStateAlterationTimePoint_list:
        parsed_time: pd.Timestamp | None = parse_ncp_time_to_utc_timestamp(
            raw_time=grid_state_time_point.atTime,
            logger=logger,
            source_object=grid_state_time_point
        )
        if parsed_time is None:
            pass
        else:
            time_index: int | None = time_index_lookup.get(int(parsed_time.value), None)
            if time_index is None:
                logger.add_warning(
                    msg='GridStateAlterationTimePoint timestamp not found in initialized profile',
                    device=grid_state_time_point.rdfid,
                    device_class=grid_state_time_point.tpe,
                    device_property='atTime',
                    value=grid_state_time_point.atTime
                )
            else:
                if grid_state_time_point.enabled:
                    grid_state_schedule_ref: object = grid_state_time_point.GridStateAlterationSchedule
                    if grid_state_schedule_ref is None or isinstance(grid_state_schedule_ref, str):
                        logger.add_warning(
                            msg='GridStateAlterationTimePoint without resolved schedule reference',
                            device=grid_state_time_point.rdfid,
                            device_class=grid_state_time_point.tpe,
                            device_property='GridStateAlterationSchedule'
                        )
                    else:
                        grid_state_action_ref: object = grid_state_schedule_ref.GridStateAlteration
                        if grid_state_action_ref is None or isinstance(grid_state_action_ref, str):
                            logger.add_warning(
                                msg='GridStateAlterationSchedule without resolved action reference',
                                device=grid_state_schedule_ref.rdfid,
                                device_class=grid_state_schedule_ref.tpe,
                                device_property='GridStateAlteration'
                            )
                        else:
                            property_name: str | None
                            property_value: float | bool | None
                            property_name, property_value = get_action_property_and_value(
                                grid_state_action=grid_state_action_ref,
                                logger=logger
                            )
                            if property_name is None or property_value is None:
                                pass
                            else:
                                target_device: object | None = resolve_grid_state_action_target_device(
                                    grid_state_action=grid_state_action_ref,
                                    device_lookup=device_lookup,
                                    logger=logger
                                )
                                if target_device is None:
                                    pass
                                else:
                                    if set_device_property_at_time(
                                        target_device=target_device,
                                        property_name=property_name,
                                        property_value=property_value,
                                        time_index=time_index,
                                        source_action=grid_state_action_ref,
                                        logger=logger
                                    ):
                                        applied_assignment_count += 1
                                    else:
                                        pass
                else:
                    pass

    return applied_assignment_count


def apply_ssi_profiles(cgmes_model: CgmesCircuit,
                       gcdev_model: MultiCircuit,
                       device_lookup: Dict[str, object],
                       logger: DataLogger) -> int:
    """
    Apply SteadyStateInstruction (SSI) actions as baseline snapshot/profile values.

    :param cgmes_model: CGMES model.
    :param gcdev_model: VeraGrid model.
    :param device_lookup: CGMES UUID to VeraGrid device lookup.
    :param logger: Data logger.
    :return: Number of successful assignments.
    """
    applied_assignment_count: int = 0
    action_lists: List[List[CGMES_ASSETS]] = list()
    action_lists.append(cgmes_model.cgmes_assets.TopologyAction_list)
    action_lists.append(cgmes_model.cgmes_assets.RotatingMachineAction_list)
    action_lists.append(cgmes_model.cgmes_assets.RegulatingControlAction_list)
    action_lists.append(cgmes_model.cgmes_assets.EquivalentInjectionAction_list)
    action_lists.append(cgmes_model.cgmes_assets.LoadAction_list)
    action_lists.append(cgmes_model.cgmes_assets.TapPositionAction_list)
    action_lists.append(cgmes_model.cgmes_assets.StaticVarCompensatorAction_list)

    deduplicated_actions: Dict[str, CGMES_ASSETS] = dict()
    for action_list in action_lists:
        for grid_state_action in action_list:
            if grid_state_action.uuid in deduplicated_actions:
                pass
            else:
                deduplicated_actions[grid_state_action.uuid] = grid_state_action

    time_indices: List[int] = list()
    if gcdev_model.time_profile is None:
        pass
    else:
        for time_index in gcdev_model.get_all_time_indices():
            time_indices.append(int(time_index))

    for grid_state_action in deduplicated_actions.values():
        if grid_state_action.enabled:
            property_name: str | None
            property_value: float | bool | None
            property_name, property_value = get_action_property_and_value(
                grid_state_action=grid_state_action,
                logger=logger
            )
            if property_name is None or property_value is None:
                pass
            else:
                target_device: object | None = resolve_grid_state_action_target_device(
                    grid_state_action=grid_state_action,
                    device_lookup=device_lookup,
                    logger=logger
                )
                if target_device is None:
                    pass
                else:
                    if set_device_property_at_time(
                        target_device=target_device,
                        property_name=property_name,
                        property_value=property_value,
                        time_index=None,
                        source_action=grid_state_action,
                        logger=logger
                    ):
                        applied_assignment_count += 1
                    else:
                        pass

                    if len(time_indices) > 0:
                        for time_index in time_indices:
                            if set_device_property_at_time(
                                target_device=target_device,
                                property_name=property_name,
                                property_value=property_value,
                                time_index=time_index,
                                source_action=grid_state_action,
                                logger=logger
                            ):
                                applied_assignment_count += 1
                            else:
                                pass
                    else:
                        pass
        else:
            pass

    return applied_assignment_count


def get_gcdev_ncp_ps_sis_ssi_instructions(cgmes_model: CgmesCircuit,
                                          gcdev_model: MultiCircuit,
                                          logger: DataLogger) -> None:
    """
    Convert NCP PS/SIS/SSI instructions into VeraGrid time profiles and setpoints.

    :param cgmes_model: CGMES model.
    :param gcdev_model: VeraGrid model.
    :param logger: Data logger.
    :return: Nothing.
    """
    instruction_device_lookup: Dict[str, object] = build_ncp_instruction_device_lookup(
        cgmes_model=cgmes_model,
        gcdev_model=gcdev_model
    )

    ps_sis_timestamps: List[pd.Timestamp] = collect_ncp_ps_sis_timestamps(
        cgmes_model=cgmes_model,
        logger=logger
    )
    availability_timestamps: List[pd.Timestamp] = collect_ncp_availability_timestamps(
        cgmes_model=cgmes_model,
        logger=logger,
        parse_time_to_utc_timestamp=parse_ncp_time_to_utc_timestamp
    )
    all_ncp_timestamps: List[pd.Timestamp] = list()
    for timestamp in ps_sis_timestamps:
        all_ncp_timestamps.append(timestamp)
    for timestamp in availability_timestamps:
        all_ncp_timestamps.append(timestamp)

    time_index_lookup: Dict[int, int] = ensure_ncp_instruction_time_profile(
        gcdev_model=gcdev_model,
        timestamps=all_ncp_timestamps,
        logger=logger
    )

    applied_ssi_count: int = apply_ssi_profiles(
        cgmes_model=cgmes_model,
        gcdev_model=gcdev_model,
        device_lookup=instruction_device_lookup,
        logger=logger
    )
    applied_availability_count: int = apply_ncp_availability_profiles(
        cgmes_model=cgmes_model,
        gcdev_model=gcdev_model,
        device_lookup=instruction_device_lookup,
        logger=logger,
        get_first_resolved_reference=get_first_resolved_cgmes_reference,
        parse_time_to_utc_timestamp=parse_ncp_time_to_utc_timestamp,
        set_device_property_at_time=set_device_property_at_time
    )
    applied_ps_count: int = apply_power_schedule_profiles(
        cgmes_model=cgmes_model,
        gcdev_model=gcdev_model,
        device_lookup=instruction_device_lookup,
        time_index_lookup=time_index_lookup,
        logger=logger
    )
    applied_sis_count: int = apply_sis_profiles(
        cgmes_model=cgmes_model,
        device_lookup=instruction_device_lookup,
        time_index_lookup=time_index_lookup,
        logger=logger
    )

    total_assignments: int = applied_ssi_count + applied_availability_count + applied_ps_count + applied_sis_count
    if total_assignments > 0:
        logger.add_info(
            msg='Imported NCP PS/SIS/SSI instructions',
            value=total_assignments,
            expected_value=len(all_ncp_timestamps),
            comment=f"SSI={applied_ssi_count}, AVS={applied_availability_count}, PS={applied_ps_count}, SIS={applied_sis_count}"
        )
    else:
        pass
