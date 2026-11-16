# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Remove disconnected single-node islands from an RMS assessment."""

from copy import copy

import numpy as np

from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent
from VeraGridEngine.Devices.Branches.transformer3w import Transformer3W
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import PowerFlowResults


def _retain_injection(device: InjectionParent, buses: set[Bus]) -> bool:
    return device.bus is None or device.bus in buses


def _retain_branch(device: BranchParent, buses: set[Bus]) -> bool:
    return ((device.bus_from is None or device.bus_from in buses)
            and (device.bus_to is None or device.bus_to in buses))


def _retain_transformer3w(device: Transformer3W, buses: set[Bus]) -> bool:
    return ((device.bus1 is None or device.bus1 in buses)
            and (device.bus2 is None or device.bus2 in buses)
            and (device.bus3 is None or device.bus3 in buses))


def _branch_indices(devices, buses: set[Bus]) -> np.ndarray:
    return np.array([i for i, device in enumerate(devices)
                     if _retain_branch(device, buses)], dtype=int)


def _injection_indices(devices, buses: set[Bus]) -> np.ndarray:
    return np.array([i for i, device in enumerate(devices)
                     if _retain_injection(device, buses)], dtype=int)


def _slice_values(values, indices: np.ndarray):
    if values is None or len(values) == 0:
        return values
    return np.asarray(values)[indices].copy()


def _remap_endpoints(values, old_to_new: dict[int, int]):
    if values is None or len(values) == 0:
        return values
    return np.array([old_to_new[int(i)] for i in values], dtype=int)


def exclude_single_node_islands(
        grid: MultiCircuit,
        pf_results: PowerFlowResults | None,
) -> tuple[MultiCircuit, PowerFlowResults | None, int]:
    """Return a grid view and matching PF results, leaving the input untouched.

    Island sizes are measured after reducible switches have merged their buses.
    All connected islands are retained, including those smaller than the main one.
    """
    nc = compile_numerical_circuit_at(grid)
    islands = nc.split_into_islands(consider_hvdc_as_island_links=True)
    retained_representatives = {
        int(idx)
        for island in islands if island.nbus > 1
        for idx in island.bus_data.original_idx
    }
    bus_mapping = nc.get_reduction_bus_mapping()
    bus_indices = np.array([
        i for i in range(len(grid.buses))
        if int(bus_mapping[i]) in retained_representatives
    ], dtype=int)
    if len(bus_indices) == len(grid.buses):
        return grid, pf_results, 0
    if not len(bus_indices):
        raise ValueError("RMS small-signal analysis has no connected bus island")

    retained_buses = {grid.buses[i] for i in bus_indices}

    # A shallow circuit copy keeps device identity (and symbolic model bindings)
    # while giving RMS its own filtered device lists.
    filtered = copy(grid)
    filtered.buses = [grid.buses[i] for i in bus_indices]
    filtered.lines = [x for x in grid.lines if _retain_branch(x, retained_buses)]
    filtered.dc_lines = [x for x in grid.dc_lines if _retain_branch(x, retained_buses)]
    filtered.transformers2w = [x for x in grid.transformers2w if _retain_branch(x, retained_buses)]
    filtered.hvdc_lines = [x for x in grid.hvdc_lines if _retain_branch(x, retained_buses)]
    filtered.vsc_devices = [x for x in grid.vsc_devices if _retain_branch(x, retained_buses)]
    filtered.upfc_devices = [x for x in grid.upfc_devices if _retain_branch(x, retained_buses)]
    filtered.switch_devices = [x for x in grid.switch_devices if _retain_branch(x, retained_buses)]
    filtered.transformers3w = [x for x in grid.transformers3w if _retain_transformer3w(x, retained_buses)]
    filtered.windings = [x for x in grid.windings if _retain_branch(x, retained_buses)]
    filtered.series_reactances = [x for x in grid.series_reactances if _retain_branch(x, retained_buses)]
    filtered.loads = [x for x in grid.loads if _retain_injection(x, retained_buses)]
    filtered.generators = [x for x in grid.generators if _retain_injection(x, retained_buses)]
    filtered.external_grids = [x for x in grid.external_grids if _retain_injection(x, retained_buses)]
    filtered.shunts = [x for x in grid.shunts if _retain_injection(x, retained_buses)]
    filtered.batteries = [x for x in grid.batteries if _retain_injection(x, retained_buses)]
    filtered.static_generators = [x for x in grid.static_generators if _retain_injection(x, retained_buses)]
    filtered.current_injections = [x for x in grid.current_injections if _retain_injection(x, retained_buses)]
    filtered.controllable_shunts = [x for x in grid.controllable_shunts if _retain_injection(x, retained_buses)]

    if pf_results is None:
        return filtered, None, len(grid.buses) - len(bus_indices)

    branch_indices = _branch_indices(
        grid.get_branches_iter(add_vsc=False, add_hvdc=False, add_switch=True),
        retained_buses,
    )
    hvdc_indices = _branch_indices(grid.hvdc_lines, retained_buses)
    vsc_indices = _branch_indices(grid.vsc_devices, retained_buses)
    gen_indices = _injection_indices(grid.generators, retained_buses)
    batt_indices = _injection_indices(grid.batteries, retained_buses)
    shunt_indices = _injection_indices(grid.get_shunt_like_devices(), retained_buses)

    projected = copy(pf_results)

    projected.bus_names = _slice_values(pf_results.bus_names, bus_indices)
    projected.bus_types = _slice_values(pf_results.bus_types, bus_indices)
    projected.bus_area_indices = _slice_values(pf_results.bus_area_indices, bus_indices)
    projected.Sbus = _slice_values(pf_results.Sbus, bus_indices)
    projected.voltage = _slice_values(pf_results.voltage, bus_indices)

    projected.branch_names = _slice_values(pf_results.branch_names, branch_indices)
    projected.Sf = _slice_values(pf_results.Sf, branch_indices)
    projected.St = _slice_values(pf_results.St, branch_indices)
    projected.If = _slice_values(pf_results.If, branch_indices)
    projected.It = _slice_values(pf_results.It, branch_indices)
    projected.tap_module = _slice_values(pf_results.tap_module, branch_indices)
    projected.tap_angle = _slice_values(pf_results.tap_angle, branch_indices)
    projected.Vbranch = _slice_values(pf_results.Vbranch, branch_indices)
    projected.loading = _slice_values(pf_results.loading, branch_indices)
    projected.losses = _slice_values(pf_results.losses, branch_indices)
    projected.F = _slice_values(pf_results.F, branch_indices)
    projected.T = _slice_values(pf_results.T, branch_indices)

    projected.hvdc_names = _slice_values(pf_results.hvdc_names, hvdc_indices)
    projected.losses_hvdc = _slice_values(pf_results.losses_hvdc, hvdc_indices)
    projected.Pf_hvdc = _slice_values(pf_results.Pf_hvdc, hvdc_indices)
    projected.Pt_hvdc = _slice_values(pf_results.Pt_hvdc, hvdc_indices)
    projected.loading_hvdc = _slice_values(pf_results.loading_hvdc, hvdc_indices)
    projected.hvdc_F = _slice_values(pf_results.hvdc_F, hvdc_indices)
    projected.hvdc_T = _slice_values(pf_results.hvdc_T, hvdc_indices)

    projected.vsc_names = _slice_values(pf_results.vsc_names, vsc_indices)
    projected.losses_vsc = _slice_values(pf_results.losses_vsc, vsc_indices)
    projected.Pfp_vsc = _slice_values(pf_results.Pfp_vsc, vsc_indices)
    projected.Pfn_vsc = _slice_values(pf_results.Pfn_vsc, vsc_indices)
    projected.Vdc_vsc = _slice_values(pf_results.Vdc_vsc, vsc_indices)
    projected.St_vsc = _slice_values(pf_results.St_vsc, vsc_indices)
    projected.If_vsc = _slice_values(pf_results.If_vsc, vsc_indices)
    projected.It_vsc = _slice_values(pf_results.It_vsc, vsc_indices)
    projected.loading_vsc = _slice_values(pf_results.loading_vsc, vsc_indices)

    projected.gen_names = _slice_values(pf_results.gen_names, gen_indices)
    projected.gen_p = _slice_values(pf_results.gen_p, gen_indices)
    projected.gen_q = _slice_values(pf_results.gen_q, gen_indices)

    projected.batt_names = _slice_values(pf_results.batt_names, batt_indices)
    projected.battery_p = _slice_values(pf_results.battery_p, batt_indices)
    projected.battery_q = _slice_values(pf_results.battery_q, batt_indices)

    projected.sh_names = _slice_values(pf_results.sh_names, shunt_indices)
    projected.shunt_q = _slice_values(pf_results.shunt_q, shunt_indices)

    old_to_new = {old: new for new, old in enumerate(bus_indices)}
    projected.F = _remap_endpoints(projected.F, old_to_new)
    projected.T = _remap_endpoints(projected.T, old_to_new)
    projected.hvdc_F = _remap_endpoints(projected.hvdc_F, old_to_new)
    projected.hvdc_T = _remap_endpoints(projected.hvdc_T, old_to_new)
    return filtered, projected, len(grid.buses) - len(bus_indices)
