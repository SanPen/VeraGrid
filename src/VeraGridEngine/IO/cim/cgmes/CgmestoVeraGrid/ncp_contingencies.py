# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Dict, List, Set

import VeraGridEngine.Devices as gcdev
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.cim.cgmes.cgmes_circuit import CgmesCircuit
from VeraGridEngine.IO.cim.cgmes.cgmes_typing import CGMES_ASSETS
from VeraGridEngine.IO.cim.cgmes.cgmes_utils import normalize_cgmes_reference_uuid
from VeraGridEngine.data_logger import DataLogger
from VeraGridEngine.enumerations import ContingencyOperationTypes


def parse_contingency_equipment_status(contingent_status: str | None,
                                       logger: DataLogger,
                                       contingency_equipment: CGMES_ASSETS) -> float | None:
    """
    Convert NCP ``contingentStatus`` into VeraGrid contingency ``Active`` value.

    :param contingent_status: NCP contingent status URI/text.
    :param logger: Data logger.
    :param contingency_equipment: Source NCP ContingencyEquipment object.
    :return: Target ``Active`` value:
             - 0.0 means outage (outOfService)
             - 1.0 means explicit in-service
             - None means unsupported status
    """
    if contingent_status is None:
        return 0.0
    else:
        pass

    status_text: str = str(contingent_status).lower()
    if "outofservice" in status_text:
        return 0.0
    elif "inservice" in status_text:
        return 1.0
    else:
        logger.add_warning(
            msg='Unsupported contingency equipment status',
            device=contingency_equipment.rdfid,
            device_class=contingency_equipment.tpe,
            device_property='contingentStatus',
            value=contingent_status,
            expected_value='outOfService or inService'
        )
        return None


def build_contingency_device_lookup(gcdev_model: MultiCircuit) -> Dict[str, object]:
    """
    Build lookup table for devices that can be targeted by contingencies.

    :param gcdev_model: VeraGrid model.
    :return: Dictionary keyed by canonical/normalized device idtag.
    """
    contingency_device_lookup: Dict[str, object] = dict()
    contingency_devices: List[object] = list()

    for branch_device in gcdev_model.get_branches(add_vsc=True, add_hvdc=True, add_switch=True):
        contingency_devices.append(branch_device)
    for injection_device in gcdev_model.get_injection_devices():
        contingency_devices.append(injection_device)

    for contingency_device in contingency_devices:
        contingency_device_idtag: str = contingency_device.idtag
        if len(contingency_device_idtag) > 0:
            if contingency_device_idtag in contingency_device_lookup:
                pass
            else:
                contingency_device_lookup[contingency_device_idtag] = contingency_device

            normalized_idtag: str | None = normalize_cgmes_reference_uuid(contingency_device_idtag)
            if normalized_idtag is not None:
                if normalized_idtag in contingency_device_lookup:
                    pass
                else:
                    contingency_device_lookup[normalized_idtag] = contingency_device
            else:
                pass
        else:
            pass

    return contingency_device_lookup


def get_ncp_contingency_objects(cgmes_model: CgmesCircuit) -> List[CGMES_ASSETS]:
    """
    Collect NCP contingency objects from all supported contingency subclasses.

    :param cgmes_model: CGMES model.
    :return: De-duplicated contingency object list.
    """
    contingency_objects: List[CGMES_ASSETS] = list()
    contingency_by_uuid: Dict[str, CGMES_ASSETS] = dict()
    contingency_lists: List[List[CGMES_ASSETS]] = list()

    contingency_lists.append(cgmes_model.cgmes_assets.Contingency_list)
    contingency_lists.append(cgmes_model.cgmes_assets.OrdinaryContingency_list)
    contingency_lists.append(cgmes_model.cgmes_assets.ExceptionalContingency_list)
    contingency_lists.append(cgmes_model.cgmes_assets.OutOfRangeContingency_list)

    for contingency_list in contingency_lists:
        for contingency_obj in contingency_list:
            contingency_uuid: str = contingency_obj.uuid
            if contingency_uuid in contingency_by_uuid:
                pass
            else:
                contingency_by_uuid[contingency_uuid] = contingency_obj

    for contingency_obj in contingency_by_uuid.values():
        contingency_objects.append(contingency_obj)

    return contingency_objects


def build_converter_to_dcline_lookup(cgmes_model: CgmesCircuit) -> Dict[str, str]:
    """
    Build a mapping from CGMES converter UUID to paired DCLineSegment UUID.

    The mapping is inferred through DC nodes:
    ``CsConverter -> ACDCConverterDCTerminal -> DCNode <- DCTerminal <- DCLineSegment``.

    :param cgmes_model: CGMES model.
    :return: Dictionary keyed by converter UUID with value DCLineSegment UUID.
    """
    converter_to_dcnode_uuid: Dict[str, str] = dict()
    dcnode_to_dcline_uuid_list: Dict[str, List[str]] = dict()
    converter_to_dcline_uuid: Dict[str, str] = dict()

    for converter_terminal in cgmes_model.cgmes_assets.ACDCConverterDCTerminal_list:
        converter_equipment: object = converter_terminal.DCConductingEquipment
        converter_dcnode: object = converter_terminal.DCNode
        if converter_equipment is None or isinstance(converter_equipment, str):
            pass
        else:
            if converter_dcnode is None or isinstance(converter_dcnode, str):
                pass
            else:
                converter_uuid: str = converter_equipment.uuid
                dcnode_uuid: str = converter_dcnode.uuid
                converter_to_dcnode_uuid[converter_uuid] = dcnode_uuid

    for dc_terminal in cgmes_model.cgmes_assets.DCTerminal_list:
        line_equipment: object = dc_terminal.DCConductingEquipment
        line_dcnode: object = dc_terminal.DCNode
        if line_equipment is None or isinstance(line_equipment, str):
            pass
        else:
            if line_dcnode is None or isinstance(line_dcnode, str):
                pass
            else:
                if line_equipment.tpe == "DCLineSegment":
                    dcnode_uuid = line_dcnode.uuid
                    line_uuid = line_equipment.uuid
                    line_list: List[str] | None = dcnode_to_dcline_uuid_list.get(dcnode_uuid, None)
                    if line_list is None:
                        dcnode_to_dcline_uuid_list[dcnode_uuid] = [line_uuid]
                    else:
                        line_list.append(line_uuid)
                else:
                    pass

    for converter_uuid, dcnode_uuid in converter_to_dcnode_uuid.items():
        candidate_lines: List[str] | None = dcnode_to_dcline_uuid_list.get(dcnode_uuid, None)
        if candidate_lines is None:
            pass
        else:
            unique_line_ids: Set[str] = set(candidate_lines)
            if len(unique_line_ids) > 0:
                converter_to_dcline_uuid[converter_uuid] = candidate_lines[0]
            else:
                pass

    return converter_to_dcline_uuid


def get_gcdev_contingencies(cgmes_model: CgmesCircuit,
                            gcdev_model: MultiCircuit,
                            logger: DataLogger) -> None:
    """
    Convert NCP contingencies to VeraGrid ContingencyGroup/Contingency objects.

    :param cgmes_model: CGMES model.
    :param gcdev_model: VeraGrid model.
    :param logger: Data logger.
    :return: Nothing.
    """
    contingency_objects: List[CGMES_ASSETS] = get_ncp_contingency_objects(cgmes_model=cgmes_model)
    contingency_equipment_list: List[CGMES_ASSETS] = cgmes_model.cgmes_assets.ContingencyEquipment_list

    if len(contingency_objects) == 0:
        return
    else:
        pass

    contingency_device_lookup: Dict[str, object] = build_contingency_device_lookup(gcdev_model=gcdev_model)
    converter_to_dcline_uuid_lookup: Dict[str, str] = build_converter_to_dcline_lookup(cgmes_model=cgmes_model)
    contingency_group_lookup: Dict[str, gcdev.ContingencyGroup] = dict()
    contingency_equipment_by_contingency: Dict[str, List[CGMES_ASSETS]] = dict()
    imported_contingency_count: int = 0
    skipped_contingency_count: int = 0
    skipped_empty_group_count: int = 0

    for contingency_equipment in contingency_equipment_list:
        contingency_obj: object = contingency_equipment.Contingency
        if contingency_obj is None or isinstance(contingency_obj, str):
            logger.add_warning(
                msg='ContingencyEquipment without resolved Contingency reference',
                device=contingency_equipment.rdfid,
                device_class=contingency_equipment.tpe,
                device_property='Contingency',
                value=contingency_obj,
                expected_value='resolved object'
            )
        else:
            contingency_uuid: str = contingency_obj.uuid
            lst: List[CGMES_ASSETS] | None = contingency_equipment_by_contingency.get(contingency_uuid, None)
            if lst is None:
                contingency_equipment_by_contingency[contingency_uuid] = [contingency_equipment]
            else:
                lst.append(contingency_equipment)

    for contingency_obj in contingency_objects:
        contingency_uuid: str = contingency_obj.uuid
        contingency_elements: List[CGMES_ASSETS] | None = contingency_equipment_by_contingency.get(contingency_uuid, None)
        if contingency_elements is None:
            pass
        else:
            contingency_name_obj: object = contingency_obj.name
            if isinstance(contingency_name_obj, str):
                contingency_name: str = contingency_name_obj
            else:
                contingency_name = ""
            if len(contingency_name) > 0:
                pass
            else:
                contingency_name = contingency_uuid

            normal_must_study: bool | None = contingency_obj.normalMustStudy
            must_study: bool | None = contingency_obj.mustStudy
            if isinstance(normal_must_study, bool):
                contingency_group_active: bool = normal_must_study
            elif isinstance(must_study, bool):
                contingency_group_active = must_study
            else:
                contingency_group_active = True

            # Defer group creation until we import at least one valid contingency element.
            # This avoids orphan groups that later break contingency analyses expecting group->contingency mapping.
            contingency_imported_for_group: bool = False

            for contingency_equipment in contingency_elements:
                equipment_obj: object = contingency_equipment.Equipment
                target_device: object | None = None
                equipment_uuid: str = ""
                equipment_tpe: str = ""

                if equipment_obj is None:
                    skipped_contingency_count += 1
                    logger.add_warning(
                        msg='ContingencyEquipment without resolved Equipment reference',
                        device=contingency_equipment.rdfid,
                        device_class=contingency_equipment.tpe,
                        device_property='Equipment',
                        value=equipment_obj,
                        expected_value='resolved object or UUID reference'
                    )
                else:
                    if isinstance(equipment_obj, str):
                        normalized_equipment_uuid: str | None = normalize_cgmes_reference_uuid(equipment_obj)
                        if normalized_equipment_uuid is None:
                            equipment_uuid = ""
                        else:
                            equipment_uuid = normalized_equipment_uuid
                        equipment_tpe = ""
                    else:
                        equipment_uuid = equipment_obj.uuid
                        equipment_tpe = equipment_obj.tpe

                    if len(equipment_uuid) > 0:
                        target_device = contingency_device_lookup.get(equipment_uuid, None)
                    else:
                        pass

                    # Fallback mapping for simplified HVDC conversion:
                    # CsConverter contingencies should target the merged DC/HVDC line device.
                    if target_device is None:
                        mapped_dcline_uuid: str | None = converter_to_dcline_uuid_lookup.get(equipment_uuid, None)
                        if mapped_dcline_uuid is None:
                            pass
                        else:
                            target_device = contingency_device_lookup.get(mapped_dcline_uuid, None)
                            if target_device is None:
                                logger.add_warning(
                                    msg='Contingency converter mapped to DC line but mapped device is not in VeraGrid lookup',
                                    device=contingency_equipment.rdfid,
                                    device_class=contingency_equipment.tpe,
                                    device_property='Equipment.uuid',
                                    value=equipment_uuid,
                                    expected_value=mapped_dcline_uuid
                                )
                            else:
                                logger.add_info(
                                    msg='Mapped contingency converter target to merged DC/HVDC line',
                                    device=contingency_equipment.rdfid,
                                    device_class=contingency_equipment.tpe,
                                    device_property='Equipment.uuid',
                                    value=equipment_uuid,
                                    expected_value=mapped_dcline_uuid
                                )
                    else:
                        pass

                    if target_device is None:
                        skipped_contingency_count += 1
                        logger.add_warning(
                            msg='Contingency target equipment not imported as a contingency-capable VeraGrid device',
                            device=contingency_equipment.rdfid,
                            device_class=contingency_equipment.tpe,
                            device_property='Equipment.uuid',
                            value=equipment_uuid,
                            expected_value=equipment_tpe
                        )
                    else:
                        contingency_active_value: float | None = parse_contingency_equipment_status(
                            contingent_status=contingency_equipment.contingentStatus,
                            logger=logger,
                            contingency_equipment=contingency_equipment
                        )
                        if contingency_active_value is None:
                            skipped_contingency_count += 1
                        else:
                            contingency_group: gcdev.ContingencyGroup | None = contingency_group_lookup.get(
                                contingency_uuid, None
                            )
                            if contingency_group is None:
                                contingency_group = gcdev.ContingencyGroup(
                                    idtag=contingency_uuid,
                                    name=contingency_name,
                                    category=contingency_obj.tpe,
                                    active=contingency_group_active
                                )
                                gcdev_model.add_contingency_group(contingency_group)
                                contingency_group_lookup[contingency_uuid] = contingency_group
                            else:
                                pass

                            contingency_description: object = contingency_obj.description
                            if isinstance(contingency_description, str):
                                contingency_comment: str = contingency_description
                            else:
                                contingency_comment = ""

                            target_code_raw: object = target_device.code
                            if isinstance(target_code_raw, str):
                                target_code: str = target_code_raw
                            else:
                                target_code = ""

                            target_name_raw: str = target_device.name
                            if isinstance(target_name_raw, str):
                                target_name: str = target_name_raw
                            else:
                                target_name = "device"

                            gcdev_contingency = gcdev.Contingency(
                                device=target_device,
                                idtag=contingency_equipment.uuid,
                                name=f"{contingency_name}::{target_name}",
                                code=target_code,
                                prop=ContingencyOperationTypes.Active,
                                value=contingency_active_value,
                                group=contingency_group,
                                comment=contingency_comment
                            )
                            gcdev_model.add_contingency(gcdev_contingency)
                            imported_contingency_count += 1
                            contingency_imported_for_group = True

            if contingency_imported_for_group:
                pass
            else:
                skipped_empty_group_count += 1
                logger.add_warning(
                    msg='Skipped NCP contingency group because no valid contingency equipment could be imported',
                    device=contingency_obj.rdfid,
                    device_class=contingency_obj.tpe,
                    device_property='Contingency',
                    value=contingency_uuid
                )

    if imported_contingency_count > 0:
        logger.add_info(
            msg='Imported NCP contingencies',
            value=imported_contingency_count,
            expected_value=len(contingency_equipment_list),
            comment=f"Skipped={skipped_contingency_count}; EmptyGroups={skipped_empty_group_count}"
        )
    else:
        if skipped_empty_group_count > 0:
            logger.add_warning(
                msg='No NCP contingencies imported',
                value=skipped_contingency_count,
                expected_value=len(contingency_equipment_list),
                comment=f"EmptyGroups={skipped_empty_group_count}"
            )
        else:
            pass
