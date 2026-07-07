# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Callable, Dict, List, Tuple

import numpy as np
import pandas as pd

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.cim.cgmes.cgmes_circuit import CgmesCircuit
from VeraGridEngine.IO.cim.cgmes.cgmes_typing import CGMES_ASSETS
from VeraGridEngine.IO.cim.cgmes.cgmes_utils import normalize_cgmes_reference_uuid
from VeraGridEngine.data_logger import DataLogger


def parse_ncp_bool(raw_value: object) -> bool | None:
    """
    Parse one NCP boolean candidate value.

    The parser accepts canonical bool values and common string encodings.

    :param raw_value: Raw boolean candidate.
    :return: Parsed bool or ``None`` when not parseable.
    """
    if isinstance(raw_value, bool):
        return raw_value
    elif isinstance(raw_value, str):
        normalized_value: str = raw_value.strip().lower()
        if normalized_value in ("true", "1", "yes"):
            return True
        elif normalized_value in ("false", "0", "no"):
            return False
        else:
            return None
    else:
        return None


def get_resolved_cgmes_reference_list(reference: object) -> List[object]:
    """
    Resolve every object reference from one CGMES relation field.

    CGMES relation fields can contain one object, a list of objects, unresolved
    strings, or ``None``. This helper returns only resolved object references and
    keeps deterministic order for stable conversion behavior.

    :param reference: Raw CGMES relation value.
    :return: List of resolved object references.
    """
    resolved_references: List[object] = list()
    if reference is None:
        return resolved_references
    elif isinstance(reference, str):
        return resolved_references
    elif isinstance(reference, list):
        for reference_item in reference:
            if reference_item is None:
                pass
            elif isinstance(reference_item, str):
                pass
            else:
                resolved_references.append(reference_item)
        return resolved_references
    else:
        resolved_references.append(reference)
        return resolved_references


def collect_ncp_availability_timestamps(cgmes_model: CgmesCircuit,
                                        logger: DataLogger,
                                        parse_time_to_utc_timestamp: Callable[
                                            [str | None, DataLogger, CGMES_ASSETS | None], pd.Timestamp | None]) -> \
        List[pd.Timestamp]:
    """
    Collect availability schedule timestamps from NCP EventTimePoint objects.

    :param cgmes_model: CGMES model.
    :param logger: Data logger.
    :param parse_time_to_utc_timestamp: Shared NCP timestamp parser callback.
    :return: List of parsed UTC timestamps.
    """
    collected_timestamps: List[pd.Timestamp] = list()
    for event_time_point in cgmes_model.cgmes_assets.EventTimePoint_list:
        parsed_time: pd.Timestamp | None = parse_time_to_utc_timestamp(
            event_time_point.atTime,
            logger,
            event_time_point
        )
        if parsed_time is None:
            pass
        else:
            collected_timestamps.append(parsed_time)
    return collected_timestamps


def get_event_time_point_sort_key(event_point: Tuple[pd.Timestamp, bool]) -> int:
    """
    Get sorting key for one event time point tuple.

    :param event_point: Tuple with timestamp and active state.
    :return: Nanoseconds since epoch used for chronological sorting.
    """
    return int(event_point[0].value)


def build_event_schedule_timepoints_lookup(
        cgmes_model: CgmesCircuit,
        get_first_resolved_reference: Callable[[object], object | None]) -> Dict[str, List[CGMES_ASSETS]]:
    """
    Build EventSchedule UUID to EventTimePoint list mapping.

    :param cgmes_model: CGMES model.
    :param get_first_resolved_reference: Shared CGMES reference resolver callback.
    :return: Dictionary keyed by EventSchedule UUID.
    """
    schedule_timepoints_lookup: Dict[str, List[CGMES_ASSETS]] = dict()
    for event_time_point in cgmes_model.cgmes_assets.EventTimePoint_list:
        schedule_reference: object = event_time_point.EventSchedule
        resolved_schedule: object | None = get_first_resolved_reference(schedule_reference)
        if resolved_schedule is None:
            pass
        else:
            schedule_uuid: str = resolved_schedule.uuid
            existing_points: List[CGMES_ASSETS] | None = schedule_timepoints_lookup.get(schedule_uuid, None)
            if existing_points is None:
                new_points: List[CGMES_ASSETS] = list()
                new_points.append(event_time_point)
                schedule_timepoints_lookup[schedule_uuid] = new_points
            else:
                existing_points.append(event_time_point)
    return schedule_timepoints_lookup


def build_availability_schedule_status_map(time_profile: pd.DatetimeIndex,
                                           schedule_time_points: List[Tuple[pd.Timestamp, bool]]) -> np.ndarray:
    """
    Build one boolean availability map over the complete VeraGrid time profile.

    The resulting array is piecewise constant and starts as available. Every
    event point updates the current availability state from its timestamp
    onwards.

    :param time_profile: VeraGrid global time profile.
    :param schedule_time_points: Ordered list of (timestamp, is_active) events.
    :return: Boolean array where ``True`` means available.
    """
    profile_size: int = len(time_profile)
    availability_map: np.ndarray = np.ones(profile_size, dtype=np.bool_)
    current_status: bool = True
    event_index: int = 0
    sorted_points: List[Tuple[pd.Timestamp, bool]] = sorted(
        schedule_time_points,
        key=get_event_time_point_sort_key
    )

    for time_index, profile_timestamp in enumerate(time_profile):
        profile_time: pd.Timestamp = pd.Timestamp(profile_timestamp)
        if profile_time.tz is None:
            profile_time = profile_time.tz_localize('UTC')
        else:
            profile_time = profile_time.tz_convert('UTC')

        while event_index < len(sorted_points):
            event_time: pd.Timestamp = sorted_points[event_index][0]
            if event_time <= profile_time:
                current_status = sorted_points[event_index][1]
                event_index += 1
            else:
                break
        availability_map[time_index] = current_status

    return availability_map


def apply_ncp_availability_profiles(
        cgmes_model: CgmesCircuit,
        gcdev_model: MultiCircuit,
        device_lookup: Dict[str, object],
        logger: DataLogger,
        get_first_resolved_reference: Callable[[object], object | None],
        parse_time_to_utc_timestamp: Callable[[str | None, DataLogger, CGMES_ASSETS | None], pd.Timestamp | None],
        set_device_property_at_time: Callable[[object, str, float | bool, int | None, CGMES_ASSETS,
                                               DataLogger], bool]) -> int:
    """
    Apply NCP ER/AVS availability schedules as VeraGrid ``active`` profile gates.

    Mapping policy:
        - ``AvailabilityEquipment`` is converted.
        - ``ActualSchedule`` is preferred over ``PlannedSchedule``.
        - Only unavailable states are enforced (``active=0``); available states
          do not force ``active=1`` to avoid overriding SIS/topology controls.

    :param cgmes_model: CGMES model.
    :param gcdev_model: VeraGrid model.
    :param device_lookup: CGMES UUID to VeraGrid device lookup.
    :param logger: Data logger.
    :param get_first_resolved_reference: Shared CGMES reference resolver callback.
    :param parse_time_to_utc_timestamp: Shared NCP timestamp parser callback.
    :param set_device_property_at_time: Shared VeraGrid profile assignment callback.
    :return: Number of successful ``active`` assignments.
    """
    if gcdev_model.time_profile is None:
        return 0
    elif len(gcdev_model.time_profile) == 0:
        return 0
    else:
        pass

    schedule_timepoints_lookup: Dict[str, List[CGMES_ASSETS]] = build_event_schedule_timepoints_lookup(
        cgmes_model=cgmes_model,
        get_first_resolved_reference=get_first_resolved_reference
    )
    assignment_count: int = 0

    for availability_equipment in cgmes_model.cgmes_assets.AvailabilityEquipment_list:
        equipment_references: List[object] = get_resolved_cgmes_reference_list(availability_equipment.Equipment)
        if len(equipment_references) == 0:
            logger.add_warning(
                msg='AvailabilityEquipment without resolved Equipment reference',
                device=availability_equipment.rdfid,
                device_class=availability_equipment.tpe,
                device_property='Equipment'
            )
        else:
            availability_schedule_ref: object = availability_equipment.AvailabilitySchedule
            availability_schedule: object | None = get_first_resolved_reference(availability_schedule_ref)
            if availability_schedule is None:
                logger.add_warning(
                    msg='AvailabilityEquipment without resolved AvailabilitySchedule reference',
                    device=availability_equipment.rdfid,
                    device_class=availability_equipment.tpe,
                    device_property='AvailabilitySchedule'
                )
            else:
                actual_schedule_ref: object = availability_schedule.ActualSchedule
                planned_schedule_ref: object = availability_schedule.PlannedSchedule
                selected_event_schedule: object | None = get_first_resolved_reference(actual_schedule_ref)
                if selected_event_schedule is None:
                    selected_event_schedule = get_first_resolved_reference(planned_schedule_ref)
                else:
                    pass

                if selected_event_schedule is None:
                    logger.add_warning(
                        msg='AvailabilitySchedule without resolved ActualSchedule/PlannedSchedule',
                        device=availability_schedule.rdfid,
                        device_class=availability_schedule.tpe
                    )
                else:
                    schedule_points_raw: List[CGMES_ASSETS] | None = schedule_timepoints_lookup.get(
                        selected_event_schedule.uuid, None
                    )
                    if schedule_points_raw is None:
                        logger.add_warning(
                            msg='EventSchedule has no EventTimePoint data',
                            device=selected_event_schedule.rdfid,
                            device_class=selected_event_schedule.tpe
                        )
                    elif len(schedule_points_raw) == 0:
                        logger.add_warning(
                            msg='EventSchedule has no EventTimePoint data',
                            device=selected_event_schedule.rdfid,
                            device_class=selected_event_schedule.tpe
                        )
                    else:
                        parsed_schedule_points: List[Tuple[pd.Timestamp, bool]] = list()
                        for event_time_point in schedule_points_raw:
                            parsed_time: pd.Timestamp | None = parse_time_to_utc_timestamp(
                                event_time_point.atTime,
                                logger,
                                event_time_point
                            )
                            parsed_active: bool | None = parse_ncp_bool(event_time_point.isActive)
                            if parsed_time is None:
                                pass
                            else:
                                if parsed_active is None:
                                    logger.add_warning(
                                        msg='EventTimePoint without parseable isActive state',
                                        device=event_time_point.rdfid,
                                        device_class=event_time_point.tpe,
                                        device_property='isActive',
                                        value=event_time_point.isActive
                                    )
                                else:
                                    parsed_schedule_points.append((parsed_time, parsed_active))

                        if len(parsed_schedule_points) == 0:
                            pass
                        else:
                            schedule_status_map: np.ndarray = build_availability_schedule_status_map(
                                time_profile=gcdev_model.time_profile,
                                schedule_time_points=parsed_schedule_points
                            )
                            for equipment_reference in equipment_references:
                                target_device: object | None = device_lookup.get(equipment_reference.uuid, None)
                                if target_device is None:
                                    normalized_equipment_uuid: str | None = normalize_cgmes_reference_uuid(
                                        equipment_reference.uuid
                                    )
                                    if normalized_equipment_uuid is None:
                                        target_device = None
                                    else:
                                        target_device = device_lookup.get(normalized_equipment_uuid, None)
                                else:
                                    pass

                                if target_device is None:
                                    logger.add_warning(
                                        msg='AvailabilityEquipment target not imported in VeraGrid model',
                                        device=availability_equipment.rdfid,
                                        device_class=availability_equipment.tpe,
                                        device_property='Equipment.uuid',
                                        value=equipment_reference.uuid
                                    )
                                else:
                                    for time_index, is_available in enumerate(schedule_status_map):
                                        if is_available:
                                            pass
                                        else:
                                            if set_device_property_at_time(
                                                    target_device,
                                                    'active',
                                                    0.0,
                                                    int(time_index),
                                                    availability_equipment,
                                                    logger
                                            ):
                                                assignment_count += 1
                                            else:
                                                pass

    if assignment_count > 0:
        logger.add_info(
            msg='Imported NCP ER/AVS availability gates into active profiles',
            value=assignment_count
        )
    else:
        pass

    return assignment_count
