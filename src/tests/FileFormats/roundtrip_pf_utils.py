# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Callable, Dict, Tuple

import numpy as np

import VeraGridEngine.api as gce
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations import PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import PowerFlowResults
from VeraGridEngine.enumerations import SolverType

def create_roundtrip_power_flow_options() -> PowerFlowOptions:
    """
    Create one deterministic power-flow configuration for roundtrip checks.

    :return: Power-flow options.
    """
    return PowerFlowOptions(solver_type=SolverType.NR,
                            retry_with_other_methods=False,
                            control_q=False)


def build_bus_voltage_map(circuit: MultiCircuit,
                          power_flow_results: PowerFlowResults) -> Dict[Tuple[str, int], float]:
    """
    Build a stable bus-voltage map keyed by bus name and repeated-name index.

    :param circuit: Circuit associated with the results.
    :param power_flow_results: Power-flow results to inspect.
    :return: Mapping from stable bus key to voltage magnitude.
    """
    value_map: Dict[Tuple[str, int], float] = dict()
    repetitions_by_name: Dict[str, int] = dict()

    bus_index: int
    bus: object
    for bus_index, bus in enumerate(circuit.buses):
        bus_name: str = str(bus.name)
        repetition_index: int = repetitions_by_name.get(bus_name, 0)
        repetitions_by_name[bus_name] = repetition_index + 1
        value_map[(bus_name, repetition_index)] = float(np.abs(power_flow_results.voltage[bus_index]))

    return value_map


def build_branch_active_power_map(circuit: MultiCircuit,
                                  power_flow_results: PowerFlowResults) -> Dict[Tuple[str, str, str, int], float]:
    """
    Build a stable branch-flow map keyed by device class, unordered endpoint names, and repetition index.

    :param circuit: Circuit associated with the results.
    :param power_flow_results: Power-flow results to inspect.
    :return: Mapping from stable branch key to active power flow.
    """
    value_map: Dict[Tuple[str, str, str, int], float] = dict()
    repetitions_by_key: Dict[Tuple[str, str, str], int] = dict()

    branches = circuit.get_branches(add_vsc=False, add_hvdc=False, add_switch=False)

    branch_index: int
    branch: object
    for branch_index, branch in enumerate(branches):
        endpoint_name_1: str = str(branch.bus_from.name)
        endpoint_name_2: str = str(branch.bus_to.name)
        ordered_endpoint_names: Tuple[str, str] = tuple(sorted((endpoint_name_1, endpoint_name_2)))
        base_key: Tuple[str, str, str] = (branch.device_type.value,
                                          ordered_endpoint_names[0],
                                          ordered_endpoint_names[1])
        repetition_index: int = repetitions_by_key.get(base_key, 0)
        repetitions_by_key[base_key] = repetition_index + 1
        value_map[(base_key[0], base_key[1], base_key[2], repetition_index)] = float(
            np.abs(power_flow_results.Sf.real[branch_index])
        )

    return value_map


def run_export_roundtrip_power_flow_test(import_file_name: str,
                                         export_file_name: str,
                                         export_func: Callable[[MultiCircuit, str], None],
                                         voltage_atol: float = 1e-4,
                                         flow_atol: float = 1e-2) -> None:
    """
    Export one source case to a target file format, re-import it, and compare power-flow results.

    :param import_file_name: Source file to import before exporting.
    :param export_file_name: Target export path.
    :param export_func: Callback that writes the exported file.
    :param voltage_atol: Absolute tolerance for voltage magnitudes.
    :param flow_atol: Absolute tolerance for branch active-power flows.
    :return: None.
    """
    source_grid: MultiCircuit = gce.open_file(import_file_name)
    power_flow_options: PowerFlowOptions = create_roundtrip_power_flow_options()

    source_results: PowerFlowResults = gce.power_flow(source_grid, power_flow_options)
    assert source_results.converged

    export_func(source_grid, export_file_name)

    roundtrip_grid: MultiCircuit = gce.open_file(export_file_name)
    roundtrip_results: PowerFlowResults = gce.power_flow(roundtrip_grid, power_flow_options)
    assert roundtrip_results.converged

    source_voltage_map: Dict[Tuple[str, int], float] = build_bus_voltage_map(circuit=source_grid,
                                                                             power_flow_results=source_results)
    roundtrip_voltage_map: Dict[Tuple[str, int], float] = build_bus_voltage_map(circuit=roundtrip_grid,
                                                                                power_flow_results=roundtrip_results)

    source_branch_map: Dict[Tuple[str, str, str, int], float] = build_branch_active_power_map(
        circuit=source_grid,
        power_flow_results=source_results,
    )
    roundtrip_branch_map: Dict[Tuple[str, str, str, int], float] = build_branch_active_power_map(
        circuit=roundtrip_grid,
        power_flow_results=roundtrip_results,
    )

    assert set(source_voltage_map.keys()) == set(roundtrip_voltage_map.keys())
    assert set(source_branch_map.keys()) == set(roundtrip_branch_map.keys())

    bus_key: Tuple[str, int]
    for bus_key in source_voltage_map.keys():
        source_voltage: float = source_voltage_map[bus_key]
        roundtrip_voltage: float = roundtrip_voltage_map[bus_key]
        assert np.isclose(source_voltage,
                          roundtrip_voltage,
                          atol=voltage_atol), (
            f"Voltage mismatch at {bus_key}: {source_voltage} vs {roundtrip_voltage}"
        )

    branch_key: Tuple[str, str, str, int]
    for branch_key in source_branch_map.keys():
        source_flow: float = source_branch_map[branch_key]
        roundtrip_flow: float = roundtrip_branch_map[branch_key]
        assert np.isclose(source_flow,
                          roundtrip_flow,
                          atol=flow_atol), (
            f"Branch flow mismatch at {branch_key}: {source_flow} vs {roundtrip_flow}"
        )
