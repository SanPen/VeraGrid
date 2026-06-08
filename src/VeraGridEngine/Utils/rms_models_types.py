# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Dict, List, Tuple

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Utils.Symbolic.block import compare_n_blocks_structurally, _get_var_attribute_mapping
from VeraGridEngine.enumerations import (
    ConverterControlType,
    DeviceType,
    ExternalGridMode,
    ParamPowerFlowReferenceType,
    ShuntConnectionType,
    ShuntControlMode,
    WindingType,
)

def build_equivalence_classes_dict(grid:MultiCircuit)-> Tuple[Dict[int, List[int]], Dict[int, List[List[int]]], Dict[int, List[int]]]:
    """
    this functions receives the grid and return a dictionary with clases of equivalence of the dynamic models
    and a dictionary with clases of equivalence of their variables.
    :param grid:
    :type grid:
    :return: Tuple of:
        - Dict with new uid as keys and lists of equivalent block uids as values
        - Dict with representative uid as keys and lists of lists of equivalent variable uids as values
        - Dict with representative uid as keys and lists of all block uids composing that model (including children)
    :rtype:
    """

    class_equivalence_dict = {}
    block_composition_dict = {}
    all_model_lists = [
        [], [], [], [], [], [], [], [], [], [],
        [], [], [], [], [], [], [], []
    ]
    BUS, LOAD, STATIC_GEN, EXT_GRID, SHUNT, CTRL_SHUNT, CURR_INJ = range(7)
    GEN, BATTERY, VSC, DC_LINE, TRANSFORMER, WINDING, LINE = range(7, 14)
    HVDC, SERIES_REACT, SWITCH, UPFC = range(14, 18)

    # for elm in grid.buses:
    #     all_model_lists[BUS].append(elm.rms_model)

    for elm in grid.get_branches_iter():
        if elm.device_type == DeviceType.LoadDevice:
            all_model_lists[LOAD].append(elm.rms_model)
        elif elm.device_type == DeviceType.StaticGeneratorDevice:
            all_model_lists[STATIC_GEN].append(elm.rms_model)
        elif elm.device_type == DeviceType.ExternalGridDevice:
            all_model_lists[EXT_GRID].append(elm.rms_model)
        elif elm.device_type == DeviceType.ShuntDevice:
            all_model_lists[SHUNT].append(elm.rms_model)
        elif elm.device_type == DeviceType.ControllableShuntDevice:
            all_model_lists[CTRL_SHUNT].append(elm.rms_model)
        elif elm.device_type == DeviceType.CurrentInjectionDevice:
            all_model_lists[CURR_INJ].append(elm.rms_model)
        elif elm.device_type == DeviceType.GeneratorDevice:
            all_model_lists[GEN].append(elm.rms_model)
        elif elm.device_type == DeviceType.BatteryDevice:
            all_model_lists[BATTERY].append(elm.rms_model)
        elif elm.device_type == DeviceType.VscDevice:
            all_model_lists[VSC].append(elm.rms_model)
        elif elm.device_type == DeviceType.DCLineDevice:
            all_model_lists[DC_LINE].append(elm.rms_model)
        elif elm.device_type == DeviceType.Transformer2WDevice:
            all_model_lists[TRANSFORMER].append(elm.rms_model)
        elif elm.device_type == DeviceType.WindingDevice:
            all_model_lists[WINDING].append(elm.rms_model)
        elif elm.device_type == DeviceType.LineDevice:
            all_model_lists[LINE].append(elm.rms_model)
        elif elm.device_type == DeviceType.HVDCLineDevice:
            all_model_lists[HVDC].append(elm.rms_model)
        elif elm.device_type == DeviceType.SeriesReactanceDevice:
            all_model_lists[SERIES_REACT].append(elm.rms_model)
        elif elm.device_type == DeviceType.SwitchDevice:
            all_model_lists[SWITCH].append(elm.rms_model)
        elif elm.device_type == DeviceType.UpfcDevice:
            all_model_lists[UPFC].append(elm.rms_model)

    for elm in grid.get_injection_devices_iter():
        if elm.device_type == DeviceType.LoadDevice:
            all_model_lists[LOAD].append(elm.rms_model)
        elif elm.device_type == DeviceType.StaticGeneratorDevice:
            all_model_lists[STATIC_GEN].append(elm.rms_model)
        elif elm.device_type == DeviceType.ExternalGridDevice:
            all_model_lists[EXT_GRID].append(elm.rms_model)
        elif elm.device_type == DeviceType.ShuntDevice:
            all_model_lists[SHUNT].append(elm.rms_model)
        elif elm.device_type == DeviceType.ControllableShuntDevice:
            all_model_lists[CTRL_SHUNT].append(elm.rms_model)
        elif elm.device_type == DeviceType.CurrentInjectionDevice:
            all_model_lists[CURR_INJ].append(elm.rms_model)
        elif elm.device_type == DeviceType.GeneratorDevice:
            all_model_lists[GEN].append(elm.rms_model)
        elif elm.device_type == DeviceType.BatteryDevice:
            all_model_lists[BATTERY].append(elm.rms_model)
        elif elm.device_type == DeviceType.VscDevice:
            all_model_lists[VSC].append(elm.rms_model)
        elif elm.device_type == DeviceType.DCLineDevice:
            all_model_lists[DC_LINE].append(elm.rms_model)
        elif elm.device_type == DeviceType.Transformer2WDevice:
            all_model_lists[TRANSFORMER].append(elm.rms_model)
        elif elm.device_type == DeviceType.WindingDevice:
            all_model_lists[WINDING].append(elm.rms_model)
        elif elm.device_type == DeviceType.LineDevice:
            all_model_lists[LINE].append(elm.rms_model)
        elif elm.device_type == DeviceType.HVDCLineDevice:
            all_model_lists[HVDC].append(elm.rms_model)
        elif elm.device_type == DeviceType.SeriesReactanceDevice:
            all_model_lists[SERIES_REACT].append(elm.rms_model)
        elif elm.device_type == DeviceType.SwitchDevice:
            all_model_lists[SWITCH].append(elm.rms_model)
        elif elm.device_type == DeviceType.UpfcDevice:
            all_model_lists[UPFC].append(elm.rms_model)

    uid_to_block = {}
    for block_list in all_model_lists:
        for block in block_list:
            uid_to_block[block.uid] = block

    variables_equivalence_dict: Dict[int, List[List[int]]] = {}

    for model_list in all_model_lists:
        if model_list:
            model_result, var_result = compare_n_blocks_structurally(model_list)
            class_equivalence_dict.update(model_result)
            for rep_uid in model_result:
                rep_block = uid_to_block[rep_uid]
                rep_var_uids = set()
                for b in rep_block.get_all_blocks():
                    rep_var_uids.update(_get_var_attribute_mapping(b).keys())
                var_lists = []
                for ref_var_uid, equiv_uids in var_result.items():
                    if ref_var_uid in rep_var_uids:
                        var_lists.append([ref_var_uid] + equiv_uids)
                if var_lists:
                    variables_equivalence_dict[rep_uid] = var_lists

    for rep_uid in class_equivalence_dict:
        if rep_uid not in block_composition_dict and rep_uid in uid_to_block:
            block_composition_dict[rep_uid] = [b.uid for b in uid_to_block[rep_uid].get_all_blocks()]

    return class_equivalence_dict, variables_equivalence_dict, block_composition_dict





