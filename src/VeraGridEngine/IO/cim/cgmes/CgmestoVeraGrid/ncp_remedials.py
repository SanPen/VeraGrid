# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Dict, List

import VeraGridEngine.Devices as gcdev
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.cim.cgmes.CgmestoVeraGrid.ncp_contingencies import build_contingency_device_lookup
from VeraGridEngine.IO.cim.cgmes.cgmes_circuit import CgmesCircuit
from VeraGridEngine.IO.cim.cgmes.cgmes_typing import CGMES_ASSETS
from VeraGridEngine.data_logger import DataLogger
from VeraGridEngine.enumerations import ContingencyOperationTypes


def get_ncp_remedial_action_objects(cgmes_model: CgmesCircuit) -> List[CGMES_ASSETS]:
    """
    Collect NCP remedial action objects from supported remedial subclasses.

    :param cgmes_model: CGMES model.
    :return: De-duplicated remedial action object list.
    """
    remedial_objects: List[CGMES_ASSETS] = list()
    remedial_by_uuid: Dict[str, CGMES_ASSETS] = dict()
    remedial_lists: List[List[CGMES_ASSETS]] = list()

    remedial_lists.append(cgmes_model.cgmes_assets.RemedialAction_list)
    remedial_lists.append(cgmes_model.cgmes_assets.GridStateAlterationRemedialAction_list)
    remedial_lists.append(cgmes_model.cgmes_assets.SchemeRemedialAction_list)
    remedial_lists.append(cgmes_model.cgmes_assets.PowerRemedialAction_list)
    remedial_lists.append(cgmes_model.cgmes_assets.CountertradeRemedialAction_list)
    remedial_lists.append(cgmes_model.cgmes_assets.RedispatchRemedialAction_list)
    remedial_lists.append(cgmes_model.cgmes_assets.AvailabilityRemedialAction_list)

    for remedial_list in remedial_lists:
        for remedial_action in remedial_list:
            remedial_uuid: str = remedial_action.uuid
            if remedial_uuid in remedial_by_uuid:
                pass
            else:
                remedial_by_uuid[remedial_uuid] = remedial_action

    for remedial_action in remedial_by_uuid.values():
        remedial_objects.append(remedial_action)

    return remedial_objects


def build_remedial_action_to_contingency_lookup(cgmes_model: CgmesCircuit,
                                                logger: DataLogger) -> Dict[str, str]:
    """
    Build a map from remedial-action UUID to contingency UUID.

    :param cgmes_model: CGMES model.
    :param logger: Data logger.
    :return: Dictionary keyed by remedial action UUID with contingency UUID values.
    """
    remedial_to_contingency: Dict[str, str] = dict()

    for remedial_schedule in cgmes_model.cgmes_assets.RemedialActionSchedule_list:
        remedial_action_ref: object = remedial_schedule.RemedialAction
        contingency_ref: object = remedial_schedule.Contingency

        if remedial_action_ref is None or isinstance(remedial_action_ref, str):
            pass
        else:
            if contingency_ref is None or isinstance(contingency_ref, str):
                pass
            else:
                remedial_uuid: str = remedial_action_ref.uuid
                contingency_uuid: str = contingency_ref.uuid
                mapped_contingency_uuid: str | None = remedial_to_contingency.get(remedial_uuid, None)
                if mapped_contingency_uuid is None:
                    remedial_to_contingency[remedial_uuid] = contingency_uuid
                elif mapped_contingency_uuid == contingency_uuid:
                    pass
                else:
                    logger.add_warning(
                        msg='Conflicting contingency links for remedial action',
                        device=remedial_schedule.rdfid,
                        device_class=remedial_schedule.tpe,
                        device_property='RemedialActionSchedule.Contingency',
                        value=contingency_uuid,
                        expected_value=mapped_contingency_uuid
                    )

    for contingency_with_remedial in cgmes_model.cgmes_assets.ContingencyWithRemedialAction_list:
        remedial_action_ref = contingency_with_remedial.RemedialAction
        contingency_ref = contingency_with_remedial.Contingency

        if remedial_action_ref is None or isinstance(remedial_action_ref, str):
            pass
        else:
            if contingency_ref is None or isinstance(contingency_ref, str):
                pass
            else:
                remedial_uuid = remedial_action_ref.uuid
                contingency_uuid = contingency_ref.uuid
                mapped_contingency_uuid = remedial_to_contingency.get(remedial_uuid, None)
                if mapped_contingency_uuid is None:
                    remedial_to_contingency[remedial_uuid] = contingency_uuid
                elif mapped_contingency_uuid == contingency_uuid:
                    pass
                else:
                    logger.add_warning(
                        msg='Conflicting contingency links for remedial action',
                        device=contingency_with_remedial.rdfid,
                        device_class=contingency_with_remedial.tpe,
                        device_property='ContingencyWithRemedialAction.Contingency',
                        value=contingency_uuid,
                        expected_value=mapped_contingency_uuid
                    )

    return remedial_to_contingency


def normalize_property_reference_text(property_reference: str | None) -> str:
    """
    Normalize an NCP property-reference URI/text.

    :param property_reference: Raw property-reference value.
    :return: Lower-case normalized string.
    """
    if property_reference is None:
        return ""
    else:
        return str(property_reference).strip().lower()


def collect_grid_state_range_constraints(grid_state_action: CGMES_ASSETS) -> List[CGMES_ASSETS]:
    """
    Collect RangeConstraint references linked to one GridStateAlteration action.

    :param grid_state_action: NCP GridStateAlteration-derived object.
    :return: List of linked RangeConstraint objects.
    """
    collected_constraints: List[CGMES_ASSETS] = list()
    range_constraint_ref: object = grid_state_action.RangeConstraint

    if range_constraint_ref is None:
        pass
    elif isinstance(range_constraint_ref, list):
        for constraint_item in range_constraint_ref:
            if constraint_item is None:
                pass
            elif isinstance(constraint_item, str):
                pass
            else:
                collected_constraints.append(constraint_item)
    elif isinstance(range_constraint_ref, str):
        pass
    else:
        collected_constraints.append(range_constraint_ref)

    return collected_constraints


def map_topology_action_to_active_value(topology_action: CGMES_ASSETS,
                                        logger: DataLogger) -> float | None:
    """
    Map an NCP TopologyAction to VeraGrid ``Active`` contingency/remedial value.

    :param topology_action: NCP TopologyAction object.
    :param logger: Data logger.
    :return: Active value (0.0 or 1.0) or None when unsupported.
    """
    property_reference_text: str = normalize_property_reference_text(topology_action.PropertyReference)
    if "switch.open" in property_reference_text:
        switch_open_target: bool = True
        range_constraints: List[CGMES_ASSETS] = collect_grid_state_range_constraints(
            grid_state_action=topology_action
        )

        for range_constraint in range_constraints:
            range_value_candidate: float | None = None
            if isinstance(range_constraint.value, (float, int)):
                range_value_candidate = float(range_constraint.value)
            elif isinstance(range_constraint.normalValue, (float, int)):
                range_value_candidate = float(range_constraint.normalValue)
            else:
                pass

            if range_value_candidate is None:
                pass
            elif range_value_candidate >= 0.5:
                switch_open_target = True
                break
            else:
                switch_open_target = False
                break

        if switch_open_target:
            return 0.0
        else:
            return 1.0
    else:
        logger.add_warning(
            msg='Unsupported topology action property reference',
            device=topology_action.rdfid,
            device_class=topology_action.tpe,
            device_property='PropertyReference',
            value=topology_action.PropertyReference,
            expected_value='.../Switch.open'
        )
        return None


def get_gcdev_remedial_actions(cgmes_model: CgmesCircuit,
                               gcdev_model: MultiCircuit,
                               logger: DataLogger) -> None:
    """
    Convert NCP remedial actions to VeraGrid RemedialActionGroup/RemedialAction objects.

    :param cgmes_model: CGMES model.
    :param gcdev_model: VeraGrid model.
    :param logger: Data logger.
    :return: Nothing.
    """
    remedial_objects: List[CGMES_ASSETS] = get_ncp_remedial_action_objects(cgmes_model=cgmes_model)
    topology_action_list: List[CGMES_ASSETS] = cgmes_model.cgmes_assets.TopologyAction_list

    if len(remedial_objects) == 0 or len(topology_action_list) == 0:
        return
    else:
        pass

    device_lookup: Dict[str, object] = build_contingency_device_lookup(gcdev_model=gcdev_model)
    remedial_to_contingency: Dict[str, str] = build_remedial_action_to_contingency_lookup(
        cgmes_model=cgmes_model,
        logger=logger
    )
    contingency_group_lookup: Dict[str, gcdev.ContingencyGroup] = dict()
    for contingency_group in gcdev_model.contingency_groups:
        contingency_group_lookup[contingency_group.idtag] = contingency_group

    remedial_group_lookup: Dict[str, gcdev.RemedialActionGroup] = dict()
    imported_remedial_action_count: int = 0
    skipped_remedial_action_count: int = 0
    processed_topology_action_uuid: set[str] = set()

    for topology_action in topology_action_list:
        topology_action_uuid: str = topology_action.uuid
        if topology_action_uuid in processed_topology_action_uuid:
            pass
        else:
            processed_topology_action_uuid.add(topology_action_uuid)

            remedial_action_ref: object = topology_action.GridStateAlterationRemedialAction
            if remedial_action_ref is None or isinstance(remedial_action_ref, str):
                skipped_remedial_action_count += 1
                logger.add_warning(
                    msg='TopologyAction without resolved GridStateAlterationRemedialAction reference',
                    device=topology_action.rdfid,
                    device_class=topology_action.tpe,
                    device_property='GridStateAlterationRemedialAction',
                    value=remedial_action_ref,
                    expected_value='resolved object'
                )
            else:
                switch_ref: object = topology_action.Switch
                if switch_ref is None or isinstance(switch_ref, str):
                    skipped_remedial_action_count += 1
                    logger.add_warning(
                        msg='TopologyAction without resolved Switch reference',
                        device=topology_action.rdfid,
                        device_class=topology_action.tpe,
                        device_property='Switch',
                        value=switch_ref,
                        expected_value='resolved object'
                    )
                else:
                    target_device: object | None = device_lookup.get(switch_ref.uuid, None)
                    if target_device is None:
                        skipped_remedial_action_count += 1
                        logger.add_warning(
                            msg='Remedial action target switch not imported as a contingency-capable VeraGrid device',
                            device=topology_action.rdfid,
                            device_class=topology_action.tpe,
                            device_property='Switch.uuid',
                            value=switch_ref.uuid
                        )
                    else:
                        remedial_value: float | None = map_topology_action_to_active_value(
                            topology_action=topology_action,
                            logger=logger
                        )
                        if remedial_value is None:
                            skipped_remedial_action_count += 1
                        else:
                            remedial_uuid: str = remedial_action_ref.uuid
                            remedial_group: gcdev.RemedialActionGroup | None = remedial_group_lookup.get(
                                remedial_uuid, None
                            )
                            if remedial_group is None:
                                remedial_name: str = remedial_action_ref.name
                                if len(remedial_name) > 0:
                                    pass
                                else:
                                    remedial_name = remedial_uuid

                                remedial_category: str = remedial_action_ref.tpe
                                if isinstance(remedial_action_ref.kind, str) and len(remedial_action_ref.kind) > 0:
                                    remedial_category = f"{remedial_action_ref.tpe}:{remedial_action_ref.kind}"
                                else:
                                    pass

                                contingency_uuid: str | None = remedial_to_contingency.get(remedial_uuid, None)
                                if contingency_uuid is None:
                                    linked_contingency_group: gcdev.ContingencyGroup | None = None
                                else:
                                    linked_contingency_group = contingency_group_lookup.get(contingency_uuid, None)

                                remedial_group = gcdev.RemedialActionGroup(
                                    idtag=remedial_uuid,
                                    name=remedial_name,
                                    category=remedial_category,
                                    conn_group=linked_contingency_group
                                )
                                gcdev_model.add_remedial_action_group(remedial_group)
                                remedial_group_lookup[remedial_uuid] = remedial_group
                            else:
                                pass

                            target_device_code_raw: object = target_device.code
                            if isinstance(target_device_code_raw, str):
                                target_device_code: str = target_device_code_raw
                            else:
                                target_device_code = ""

                            target_device_name_raw: object = target_device.name
                            if isinstance(target_device_name_raw, str) and len(target_device_name_raw) > 0:
                                target_device_name: str = target_device_name_raw
                            else:
                                target_device_name = "switch"

                            if isinstance(topology_action.description, str):
                                remedial_comment: str = topology_action.description
                            elif isinstance(remedial_action_ref.description, str):
                                remedial_comment = remedial_action_ref.description
                            else:
                                remedial_comment = ""

                            topology_action_name: str = topology_action.name
                            if len(topology_action_name) > 0:
                                remedial_action_name: str = topology_action_name
                            else:
                                remedial_action_name = f"{remedial_group.name}::{target_device_name}"

                            gcdev_remedial_action = gcdev.RemedialAction(
                                device=target_device,
                                idtag=topology_action_uuid,
                                name=remedial_action_name,
                                code=target_device_code,
                                prop=ContingencyOperationTypes.Active,
                                value=remedial_value,
                                group=remedial_group,
                                comment=remedial_comment
                            )
                            gcdev_model.add_remedial_action(gcdev_remedial_action)
                            imported_remedial_action_count += 1

    if imported_remedial_action_count > 0:
        logger.add_info(
            msg='Imported NCP remedial actions (TopologyAction subset)',
            value=imported_remedial_action_count,
            expected_value=len(topology_action_list),
            comment=f"Skipped={skipped_remedial_action_count}"
        )
    else:
        pass
