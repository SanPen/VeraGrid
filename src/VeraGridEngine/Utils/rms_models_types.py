# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Dict, List
import uuid

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Utils.Symbolic.block import compare_n_blocks_structurally
from VeraGridEngine.enumerations import (
    ConverterControlType,
    DeviceType,
    ExternalGridMode,
    ParamPowerFlowRefferenceType,
    ShuntConnectionType,
    ShuntControlMode,
    WindingType,
)

def _new_uid() -> int:
    """
    Generate a fresh UUID‑v4 string.
    :return: UUIDv4 in integer format
    """
    return uuid.uuid4().int


def build_equivalence_classes_dict(grid:MultiCircuit)-> Dict[int, List[int]]:
    """
    this functions receives the grid and return a dictionary with clases of equivalence of the dynamic models.
    :param grid:
    :type grid:
    :return:
    :rtype:
    """

    class_equivalence_dict = {}

    bus_dyn_models_uid = list()
    for elm in grid.buses:
        bus_dyn_models_uid.append(elm.rms_model.uid)
    bus_equivalences_dict = {_new_uid(): bus_dyn_models_uid}
    class_equivalence_dict.update(bus_equivalences_dict)

    load_dyn_models = list()
    static_gen_dyn_models = list()
    external_grid_dyn_models = list()
    shunt_dyn_models = list()
    controllable_shunt_dyn_models = list()
    current_injection_dyn_models = list()
    generator_dyn_models = list()
    battery_dyn_models = list()
    vsc_dyn_models = list()
    dc_line_dyn_models = list()
    transformer2w_dyn_models = list()
    winding_dyn_models = list()
    line_dyn_models = list()
    hvdc_line_dyn_models = list()
    series_reactance_dyn_models = list()
    switch_dyn_models = list()
    upfc_dyn_models = list()

    for elm in grid.get_branches_iter():
        if elm.device_type == DeviceType.LoadDevice:
            load_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.StaticGeneratorDevice:
            static_gen_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.ExternalGridDevice:
            external_grid_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.ShuntDevice:
            shunt_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.ControllableShuntDevice:
            controllable_shunt_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.CurrentInjectionDevice:
            current_injection_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.GeneratorDevice:
            generator_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.BatteryDevice:
            battery_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.VscDevice:
            vsc_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.DCLineDevice:
            dc_line_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.Transformer2WDevice:
            transformer2w_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.WindingDevice:
            winding_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.LineDevice:
            line_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.HVDCLineDevice:
            hvdc_line_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.SeriesReactanceDevice:
            series_reactance_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.SwitchDevice:
            switch_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.UpfcDevice:
            upfc_dyn_models.append(elm.rms_model)

    for elm in grid.get_injection_devices_iter():
        if elm.device_type == DeviceType.LoadDevice:
            load_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.StaticGeneratorDevice:
            static_gen_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.ExternalGridDevice:
            external_grid_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.ShuntDevice:
            shunt_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.ControllableShuntDevice:
            controllable_shunt_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.CurrentInjectionDevice:
            current_injection_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.GeneratorDevice:
            generator_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.BatteryDevice:
            battery_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.VscDevice:
            vsc_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.DCLineDevice:
            dc_line_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.Transformer2WDevice:
            transformer2w_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.WindingDevice:
            winding_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.LineDevice:
            line_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.HVDCLineDevice:
            hvdc_line_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.SeriesReactanceDevice:
            series_reactance_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.SwitchDevice:
            switch_dyn_models.append(elm.rms_model)
        elif elm.device_type == DeviceType.UpfcDevice:
            upfc_dyn_models.append(elm.rms_model)

    if load_dyn_models:
        load_equivalences_dict = compare_n_blocks_structurally(load_dyn_models)
        class_equivalence_dict.update(load_equivalences_dict)

    if static_gen_dyn_models:
        static_gen_equivalences_dict = compare_n_blocks_structurally(static_gen_dyn_models)
        class_equivalence_dict.update(static_gen_equivalences_dict)

    if external_grid_dyn_models:
        external_grid_equivalences_dict = compare_n_blocks_structurally(external_grid_dyn_models)
        class_equivalence_dict.update(external_grid_equivalences_dict)

    if shunt_dyn_models:
        shunt_equivalences_dict = compare_n_blocks_structurally(shunt_dyn_models)
        class_equivalence_dict.update(shunt_equivalences_dict)

    if controllable_shunt_dyn_models:
        controllable_shunt_equivalences_dict = compare_n_blocks_structurally(controllable_shunt_dyn_models)
        class_equivalence_dict.update(controllable_shunt_equivalences_dict)

    if current_injection_dyn_models:
        current_injection_equivalences_dict = compare_n_blocks_structurally(current_injection_dyn_models)
        class_equivalence_dict.update(current_injection_equivalences_dict)

    if generator_dyn_models:
        generator_equivalences_dict = compare_n_blocks_structurally(generator_dyn_models)
        class_equivalence_dict.update(generator_equivalences_dict)

    if battery_dyn_models:
        battery_equivalences_dict = compare_n_blocks_structurally(battery_dyn_models)
        class_equivalence_dict.update(battery_equivalences_dict)

    if vsc_dyn_models:
        vsc_equivalences_dict = compare_n_blocks_structurally(vsc_dyn_models)
        class_equivalence_dict.update(vsc_equivalences_dict)

    if dc_line_dyn_models:
        dc_line_equivalences_dict = compare_n_blocks_structurally(dc_line_dyn_models)
        class_equivalence_dict.update(dc_line_equivalences_dict)

    if transformer2w_dyn_models:
        transformer2w_equivalences_dict = compare_n_blocks_structurally(transformer2w_dyn_models)
        class_equivalence_dict.update(transformer2w_equivalences_dict)

    if winding_dyn_models:
        winding_equivalences_dict = compare_n_blocks_structurally(winding_dyn_models)
        class_equivalence_dict.update(winding_equivalences_dict)

    if line_dyn_models:
        line_equivalences_dict = compare_n_blocks_structurally(line_dyn_models)
        class_equivalence_dict.update(line_equivalences_dict)

    if hvdc_line_dyn_models:
        hvdc_line_equivalences_dict = compare_n_blocks_structurally(hvdc_line_dyn_models)
        class_equivalence_dict.update(hvdc_line_equivalences_dict)

    if series_reactance_dyn_models:
        series_reactance_equivalences_dict = compare_n_blocks_structurally(series_reactance_dyn_models)
        class_equivalence_dict.update(series_reactance_equivalences_dict)

    if switch_dyn_models:
        switch_equivalences_dict = compare_n_blocks_structurally(switch_dyn_models)
        class_equivalence_dict.update(switch_equivalences_dict)

    if upfc_dyn_models:
        upfc_equivalences_dict = compare_n_blocks_structurally(upfc_dyn_models)
        class_equivalence_dict.update(upfc_equivalences_dict)

    return class_equivalence_dict





