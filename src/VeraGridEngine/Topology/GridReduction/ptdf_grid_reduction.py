# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import numpy as np
import networkx as nx
from typing import Tuple, Sequence, Set, List, TYPE_CHECKING
from VeraGridEngine.basic_structures import IntVec, Mat, Logger, Vec
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Injections.battery import Battery
from VeraGridEngine.Devices.Injections.static_generator import StaticGenerator
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Simulations.LinearFactors.linear_analysis import LinearAnalysisTs, LinearAnalysis
from VeraGridEngine.enumerations import BusMode, GeneratorControlMode


if TYPE_CHECKING:
    from VeraGridEngine.Devices.multi_circuit import MultiCircuit
    from VeraGridEngine.Devices.Substation.bus import Bus


def get_Pgen(grid: MultiCircuit) -> Tuple[Vec, Vec]:
    """
    Get the complex bus power Injections due to the generation with and without srap
    :return: (nbus) [MW] no-srap generation, srap-generation
    """
    val = np.zeros(grid.get_bus_number(), dtype=float)
    val_srap = np.zeros(grid.get_bus_number(), dtype=float)
    bus_dict = grid.get_bus_index_dict()

    for elm in grid.generators:
        if elm.bus is not None:
            k = bus_dict[elm.bus]
            if elm.srap_enabled:
                val_srap[k] += elm.P * elm.active
            else:
                val[k] += elm.P * elm.active

    return val, val_srap


def get_Pgen_ts(grid: MultiCircuit) -> Tuple[Mat, Mat]:
    """
    Get the complex bus power Injections due to the generation with and without srap
    :return: (nbus) [MW] no-srap generation, srap-generation
    """
    n = grid.get_bus_number()
    nt = grid.get_time_number()
    val = np.zeros((nt, n), dtype=float)
    val_srap = np.zeros((nt, n), dtype=float)
    bus_dict = grid.get_bus_index_dict()

    for elm in grid.generators:
        if elm.bus is not None:
            k = bus_dict[elm.bus]
            if elm.srap_enabled:
                val_srap[:, k] += elm.P_prof.toarray() * elm.active_prof.toarray()
            else:
                val[:, k] += elm.P_prof.toarray() * elm.active_prof.toarray()

    return val, val_srap


def get_Pload(grid: MultiCircuit) -> Vec:
    """
    Get the complex bus power Injections due to the load with sign
    :return: (nbus) [MW ]
    """
    val = np.zeros(grid.get_bus_number(), dtype=float)
    bus_dict = grid.get_bus_index_dict()

    for elm in grid.loads:
        if elm.bus is not None:
            k = bus_dict[elm.bus]
            val[k] -= elm.P * elm.active

    return val


def get_Pload_ts(grid: MultiCircuit) -> Mat:
    """
    Get the complex bus power Injections due to the load with sign
    :return: (nbus) [MW ]
    """
    n = grid.get_bus_number()
    nt = grid.get_time_number()
    val = np.zeros((nt, n), dtype=float)
    bus_dict = grid.get_bus_index_dict()

    for elm in grid.loads:
        if elm.bus is not None:
            k = bus_dict[elm.bus]
            val[:, k] -= elm.P_prof.toarray() * elm.active_prof.toarray()

    return val


def relocate_injections(grid: MultiCircuit,
                        reduction_bus_indices: Sequence[int]) -> Set[str]:
    """
    Relocate injection devices (generators, loads, etc.) from external buses to internal buses
    :param grid: MultiCircuit
    :param reduction_bus_indices: array of bus indices to reduce (external set)
    :return: Set of relocated device idtags
    """
    relocated_device_ids: Set[str] = set()
    G = nx.Graph()
    bus_idx_dict = grid.get_bus_index_dict()
    external_set = set(reduction_bus_indices)
    external_gen_set = set()
    external_gen_data = list()
    internal_set = set()

    # loop through all injection devices in the external set
    # Note: we don't remove from external_set here because multiple devices can be at the same bus
    for k, elm in enumerate(grid.get_injection_devices_iter()):
        i = bus_idx_dict[elm.bus]
        if i in external_set:
            external_gen_set.add(i)
            external_gen_data.append((k, i, elm, 'injection'))
            G.add_node(i)

    # loop through the branches
    for branch in grid.get_branches(add_vsc=False, add_hvdc=False, add_switch=True):
        f = bus_idx_dict[branch.bus_from]
        t = bus_idx_dict[branch.bus_to]
        if f in external_set or t in external_set:
            # the branch belongs to the external set
            pass
        else:
            # f nor t are in the external set: both belong to the internal set
            internal_set.add(f)
            internal_set.add(t)

        G.add_node(f)
        G.add_node(t)
        w = branch.get_weight()
        G.add_edge(f, t, weight=w)

    # convert to arrays and sort
    # external = np.sort(np.array(list(external_set)))
    # purely_internal_set = np.sort(np.array(list(purely_internal_set)))

    purely_internal_set = list(internal_set - external_gen_set)

    # now, for every generator, we need to find the shortest path in the "purely internal set"
    for elm_idx, bus_idx, elm, tpe in external_gen_data:
        # Compute shortest path lengths from this source
        lengths = nx.single_source_shortest_path_length(G, bus_idx)

        # Filter only target nodes
        target_distances = {t: lengths[t] for t in purely_internal_set if t in lengths}
        if target_distances:

            # Pick the closest
            closest = min(target_distances, key=target_distances.get)

            # relocate
            if tpe == 'injection':
                elm.bus = grid.buses[closest]
                relocated_device_ids.add(elm.idtag)

    return relocated_device_ids


def _collapse_loads(loads: List[Load], bus: "Bus", has_ts: bool, nt: int) -> Load:
    """
    Sum loads into a single collapsed load with time-series support.

    :param loads: List of loads to collapse
    :param bus: Bus where the collapsed load will be placed
    :param has_ts: Whether the grid has time series
    :param nt: Number of time steps
    :return: Single collapsed Load object
    """
    total_P = 0.0
    total_Q = 0.0

    # Sum P and Q (weighted by active status)
    for load in loads:
        if load.active:
            total_P += load.P
            total_Q += load.Q

    # Create the collapsed load
    collapsed_load = Load(name=f"collapsed load @ {bus.name}", P=total_P, Q=total_Q)

    if has_ts and nt > 0:
        # Sum time-series profiles (already weighted by active status)
        P_prof = np.zeros(nt, dtype=float)
        Q_prof = np.zeros(nt, dtype=float)

        for load in loads:
            load_active = load.active_prof.toarray().flatten().astype(bool)
            P_prof += load.P_prof.toarray().flatten() * load_active
            Q_prof += load.Q_prof.toarray().flatten() * load_active

        collapsed_load.P_prof = P_prof
        collapsed_load.Q_prof = Q_prof
        # Set active_prof to all ones since effective power is already in P_prof
        collapsed_load.active_prof = np.ones(nt, dtype=float)

    return collapsed_load


def _collapse_generators(generators: List[Generator], bus: "Bus",
                         has_ts: bool, nt: int, srap_enabled: bool) -> Generator:
    """
    Sum generators into a single collapsed generator with time-series support.

    :param generators: List of generators to collapse
    :param bus: Bus where the collapsed generator will be placed
    :param has_ts: Whether the grid has time series
    :param nt: Number of time steps
    :param srap_enabled: Whether the collapsed generator should have SRAP enabled
    :return: Single collapsed Generator object
    """
    total_P = 0.0
    any_voltage_controlled = False

    # Sum P (weighted by active status)
    for gen in generators:
        if gen.active:
            total_P += gen.P
        if gen.is_controlled:
            any_voltage_controlled = True

    # Keep voltage control only if at least one collapsed generator was a real 
    # voltage-controlling unit. Otherwise just a regular PQ component
    if any_voltage_controlled:
        control_mode = GeneratorControlMode.V
    else:
        control_mode = GeneratorControlMode.Q

    # Create the collapsed generator
    if srap_enabled:
        name = f"collapsed SRAP gen @ {bus.name}"
    else:
        name = f"collapsed non-SRAP gen @ {bus.name}"
    collapsed_gen = Generator(name=name, P=total_P, srap_enabled=srap_enabled, control_mode=control_mode)

    if has_ts and nt > 0:
        # Sum time-series profiles (already weighted by active status)
        P_prof = np.zeros(nt, dtype=float)

        for gen in generators:
            gen_active = gen.active_prof.toarray().flatten().astype(bool)
            P_prof += gen.P_prof.toarray().flatten() * gen_active

        collapsed_gen.P_prof = P_prof
        # Set active_prof to all ones since effective power is already in P_prof
        collapsed_gen.active_prof = np.ones(nt, dtype=float)

    return collapsed_gen


def compact_devices_after_reduction(
    grid: MultiCircuit,
    relocated_device_ids: Set[str],
    compensation_prefix: str = "compensated"
) -> Logger:
    """
    Compact devices on each bus after PTDF reduction.

    Per bus, keeps original devices individual and collapses:
    - External + compensation loads into one collapsed load
    - External + compensation non-SRAP gens into one collapsed generator
    - External + compensation SRAP gens into one collapsed generator

    :param grid: MultiCircuit (modified in place)
    :param relocated_device_ids: Set of device idtags that were relocated from external buses
    :param compensation_prefix: Prefix used to identify compensation devices
    :return: Logger with info about collapsed devices
    """
    logger = Logger()

    has_ts = grid.has_time_series
    nt = grid.get_time_number() if has_ts else 0

    # Build bus -> devices mapping
    bus_to_loads: dict = {bus: [] for bus in grid.buses}
    bus_to_gens: dict = {bus: [] for bus in grid.buses}

    for load in grid.loads:
        if load.bus is not None:
            bus_to_loads[load.bus].append(load)

    for gen in grid.generators:
        if gen.bus is not None:
            bus_to_gens[gen.bus].append(gen)

    # Process each bus
    for bus in grid.buses:
        loads = bus_to_loads.get(bus, [])
        gens = bus_to_gens.get(bus, [])

        # Categorize loads
        loads_original: List[Load] = []
        loads_to_collapse: List[Load] = []

        for load in loads:
            is_compensation = compensation_prefix in load.name
            is_relocated = load.idtag in relocated_device_ids

            if is_compensation or is_relocated:
                loads_to_collapse.append(load)
            else:
                loads_original.append(load)

        # Categorize generators
        gens_original_srap: List[Generator] = []
        gens_original_non_srap: List[Generator] = []
        gens_to_collapse_srap: List[Generator] = []
        gens_to_collapse_non_srap: List[Generator] = []

        for gen in gens:
            is_compensation = compensation_prefix in gen.name
            is_relocated = gen.idtag in relocated_device_ids

            if is_compensation or is_relocated:
                if gen.srap_enabled:
                    gens_to_collapse_srap.append(gen)
                else:
                    gens_to_collapse_non_srap.append(gen)
            else:
                if gen.srap_enabled:
                    gens_original_srap.append(gen)
                else:
                    gens_original_non_srap.append(gen)

        # Collapse loads if there are any to collapse
        if len(loads_to_collapse) > 0:
            collapsed_load = _collapse_loads(loads_to_collapse, bus, has_ts, nt)

            # Delete old loads
            for load in loads_to_collapse:
                grid.delete_load(load)

            # Add collapsed load
            grid.add_load(bus=bus, api_obj=collapsed_load)

            logger.add_info(
                msg=f"Collapsed {len(loads_to_collapse)} loads into '{collapsed_load.name}'",
                device=bus.name
            )

        # Collapse non-SRAP generators if there are any to collapse
        if len(gens_to_collapse_non_srap) > 0:
            collapsed_gen = _collapse_generators(
                gens_to_collapse_non_srap, bus, has_ts, nt, srap_enabled=False
            )

            # Delete old generators
            for gen in gens_to_collapse_non_srap:
                grid.delete_generator(gen)

            # Add collapsed generator
            grid.add_generator(bus=bus, api_obj=collapsed_gen)

            logger.add_info(
                msg=f"Collapsed {len(gens_to_collapse_non_srap)} non-SRAP gens into '{collapsed_gen.name}'",
                device=bus.name
            )

        # Collapse SRAP generators if there are any to collapse
        if len(gens_to_collapse_srap) > 0:
            collapsed_gen = _collapse_generators(
                gens_to_collapse_srap, bus, has_ts, nt, srap_enabled=True
            )

            # Delete old generators
            for gen in gens_to_collapse_srap:
                grid.delete_generator(gen)

            # Add collapsed generator
            grid.add_generator(bus=bus, api_obj=collapsed_gen)

            logger.add_info(
                msg=f"Collapsed {len(gens_to_collapse_srap)} SRAP gens into '{collapsed_gen.name}'",
                device=bus.name
            )

    return logger


def get_reduction_sets(grid: MultiCircuit, reduction_bus_indices: Sequence[int],
                       add_vsc=False, add_hvdc=False, add_switch=True) -> Tuple[IntVec, IntVec, IntVec]:
    """
    Generate the set of bus indices for grid reduction
    :param grid: MultiCircuit
    :param reduction_bus_indices: array of bus indices to reduce (external set)
    :param add_vsc: Include the list of VSC?
    :param add_hvdc: Include the list of HvdcLine?
    :param add_switch: Include the list of Switch?
    :return: external, boundary, internal, boundary_branches
    """
    bus_idx_dict = grid.get_bus_index_dict()
    external_set = set(reduction_bus_indices)

    # Build neighbor lists to detect buses that become isolated if external_set is removed
    n_buses = grid.get_bus_number()
    neighbors = {i: set() for i in range(n_buses)}
    branches = list(grid.get_branches(add_vsc=add_vsc, add_hvdc=add_hvdc, add_switch=add_switch))
    for branch in branches:
        f = bus_idx_dict[branch.bus_from]
        t = bus_idx_dict[branch.bus_to]
        neighbors[f].add(t)
        neighbors[t].add(f)

    # Expand the external set with any bus whose neighbors are all in the external set
    # Iterate until no more buses qualify (transitive closure)
    changed = True
    while changed:
        changed = False
        to_add = set()
        for i in range(n_buses):
            # Only consider buses that have at least one neighbor (if none, they're not connected to anything and
            # should not be removed unless explicitly requested)
            if i not in external_set and len(neighbors[i]) != 0 and neighbors[i].issubset(external_set):
                to_add.add(i)
        if to_add:
            external_set.update(to_add)
            changed = True

    # All buses that will remain after reduction (including boundary buses) once floating buses are absorbed
    all_bus_indices = set(range(n_buses))
    internal_all_set = all_bus_indices - external_set

    # Branches fully contained in the remaining grid (both ends not in external)
    internal_branches = list()
    for k, branch in enumerate(grid.get_branches(add_vsc=add_vsc, add_hvdc=add_hvdc, add_switch=add_switch)):
        f = bus_idx_dict[branch.bus_from]
        t = bus_idx_dict[branch.bus_to]
        if (f in internal_all_set) and (t in internal_all_set):
            internal_branches.append(k)

    # convert to arrays and sort
    external = np.sort(np.array(list(external_set)))
    internal = np.sort(np.array(list(internal_all_set)))
    internal_branches = np.array(internal_branches)

    return external, internal, internal_branches


def ptdf_reduction(grid: MultiCircuit,
                   reduction_bus_indices: IntVec,
                   tol=1e-8) -> Tuple[MultiCircuit, Logger]:
    """
    In-place Grid reduction using the PTDF injection mirroring
    This is the same concept as the Di-Shi reduction but using the PTDF matrix instead.
    :param grid: MultiCircuit
    :param reduction_bus_indices: Bus indices of the buses to delete
    :param tol: Tolerance, any equivalent power value under this is omitted
    """
    logger = Logger()

    # find the boundary set: buses from the internal set the join to the external set
    e_buses, i_buses, i_branches = get_reduction_sets(grid=grid, reduction_bus_indices=reduction_bus_indices)

    if len(e_buses) == 0:
        logger.add_info(msg="Nothing to reduce")
        return grid, logger

    if len(i_buses) == 0:
        logger.add_info(msg="Nothing to keep (null grid as a result)")
        return grid, logger

    nc = compile_numerical_circuit_at(circuit=grid, t_idx=None)
    lin = LinearAnalysis(nc=nc)

    # base flows
    Pbus0 = grid.get_Pbus(apply_active=True)

    # flows
    Flows0 = lin.PTDF @ Pbus0

    if grid.has_time_series:
        lin_ts = LinearAnalysisTs(grid=grid)
        Pbus0_ts = grid.get_Pbus_prof(apply_active=True)
        Flows0_ts = lin_ts.get_flows_ts(P=Pbus0_ts)
    else:
        Flows0_ts = None

    # move the external injection to the boundary like in the Di-Shi method
    relocate_injections(grid=grid, reduction_bus_indices=reduction_bus_indices)

    # Eliminate the external buses
    grid.delete_buses(lst=[grid.buses[e] for e in e_buses], delete_associated=True)

    # Injections that remain
    Pbus2 = grid.get_Pbus(apply_active=True)

    # re-make the linear analysis
    nc2 = compile_numerical_circuit_at(grid)
    lin2 = LinearAnalysis(nc2)

    # reconstruct injections that should be to keep the flows the same
    Pbus3, _, _, _ = np.linalg.lstsq(lin2.PTDF, Flows0[i_branches])
    dPbus = Pbus2 - Pbus3

    if grid.has_time_series:
        lin_ts2 = LinearAnalysisTs(grid=grid)
        Pbus3_ts = lin_ts2.get_reverse_injections_ts(flows_ts=Flows0_ts[:, i_branches])
        Pbus2_ts = grid.get_Pbus_prof(apply_active=True)
        dPbus_ts = Pbus2_ts - Pbus3_ts
    else:
        dPbus_ts = None

    n2 = grid.get_bus_number()
    for i in range(n2):
        bus = grid.buses[i]
        if abs(dPbus[i]) > tol:
            elm = Load(name=f"compensation load {i}", P=dPbus[i])
            elm.comment = "Reduction compensation load"

            if dPbus_ts is not None:
                elm.P_prof = dPbus_ts[:, i]

            grid.add_load(bus=bus, api_obj=elm)

    # proof that the flows are actually the same
    # Pbus4 = grid.get_Pbus(apply_active=True)
    # Flows4 = lin2.PTDF @ Pbus4
    # diff = Flows0[i_branches] - Flows4

    return grid, logger


def ptdf_reduction_ree_bad(grid: MultiCircuit,
                           reduction_bus_indices: IntVec,
                           tol=1e-8) -> Tuple[MultiCircuit, Logger]:
    """
    In-place Grid reduction using the PTDF injection mirroring
    No theory available
    :param grid: MultiCircuit
    :param reduction_bus_indices: Bus indices of the buses to delete
    :param tol: Tolerance, any equivalent power value under this is omitted
    """
    logger = Logger()

    # find the boundary set: buses from the internal set the join to the external set
    e_buses, i_buses, i_branches = get_reduction_sets(grid=grid, reduction_bus_indices=reduction_bus_indices)

    if len(e_buses) == 0:
        logger.add_info(msg="Nothing to reduce")
        return grid, logger

    if len(i_buses) == 0:
        logger.add_info(msg="Nothing to keep (null grid as a result)")
        return grid, logger

    # base flows
    Pbus0 = grid.get_Pbus()
    Pload = get_Pload(grid)
    Pgen, Pgen_srap = get_Pgen(grid)

    nc = compile_numerical_circuit_at(circuit=grid, t_idx=None)
    lin = LinearAnalysis(nc=nc)
    PTDF = lin.PTDF

    # flows
    Flows0 = PTDF @ Pbus0
    Flow_load = PTDF @ Pload
    Flow_gen = PTDF @ Pgen
    Flow_gen_srap = PTDF @ Pgen_srap

    # move the external injection to the boundary like in the Di-Shi method
    relocate_injections(grid=grid, reduction_bus_indices=reduction_bus_indices)

    # reduce
    to_be_deleted = [grid.buses[e] for e in e_buses]
    for bus in to_be_deleted:
        grid.delete_bus(obj=bus, delete_associated=True)

    # Injections that remain
    Pload2 = Pload[i_buses]
    Pgen2 = Pgen[i_buses]
    Pgen_srap2 = Pgen_srap[i_buses]

    # re-make the linear analysis
    nc2 = compile_numerical_circuit_at(grid)
    lin2 = LinearAnalysis(nc2)

    # reconstruct injections that should be to keep the flows the same
    b = np.c_[Flow_load[i_branches], Flow_gen[i_branches], Flow_gen_srap[i_branches]]
    X, _, _, _ = np.linalg.lstsq(lin2.PTDF, b)
    Pload3, Pgen3, Pgen_srap3 = X[:, 0], X[:, 1], X[:, 2]

    dPload = Pload2 - Pload3
    dPgen = Pgen2 - Pgen3
    dPgen_srap = Pgen_srap2 - Pgen_srap3

    n2 = grid.get_bus_number()
    tol = 1e-5
    for i in range(n2):

        bus = grid.buses[i]
        if abs(dPload[i]) > tol:
            elm = Load(name=f"compensated load {i}", P=-dPload[i])
            grid.add_load(bus=bus, api_obj=elm)

        if abs(dPgen[i]) > tol:
            elm = Generator(name=f"compensated gen {i}", P=-dPgen[i], srap_enabled=False)
            grid.add_generator(bus=bus, api_obj=elm)

        if abs(dPgen_srap[i]) > tol:
            elm = Generator(name=f"compensated gen {i}", P=-dPgen_srap[i], srap_enabled=True)
            grid.add_generator(bus=bus, api_obj=elm)

    # proof that the flows are actually the same
    Pbus4 = grid.get_Pbus()
    Flows4 = lin2.PTDF @ Pbus4

    diff = Flows0[i_branches] - Flows4

    return grid, logger


def ptdf_reduction_ree_less_bad(grid: MultiCircuit,
                                reduction_bus_indices: IntVec,
                                tol=1e-8) -> Tuple[MultiCircuit, Logger]:
    """
    In-place Grid reduction using the PTDF injection mirroring
    No theory available
    :param grid: MultiCircuit
    :param reduction_bus_indices: Bus indices of the buses to delete
    :param tol: Tolerance, any equivalent power value under this is omitted
    """
    logger = Logger()

    # find the boundary set: buses from the internal set the join to the external set
    e_buses, i_buses, i_branches = get_reduction_sets(grid=grid, reduction_bus_indices=reduction_bus_indices)

    if len(e_buses) == 0:
        logger.add_info(msg="Nothing to reduce")
        return grid, logger

    if len(i_buses) == 0:
        logger.add_info(msg="Nothing to keep (null grid as a result)")
        return grid, logger

    # base flows
    Pbus0 = grid.get_Pbus()

    nc = compile_numerical_circuit_at(circuit=grid, t_idx=None)
    lin = LinearAnalysis(nc=nc)
    PTDF = lin.PTDF

    # flows
    Flows0 = PTDF @ Pbus0

    # reduce
    to_be_deleted = [grid.buses[e] for e in e_buses]
    for bus in to_be_deleted:
        grid.delete_bus(obj=bus, delete_associated=True)

    # Injections that remain
    Pbus2 = Pbus0[i_buses]

    # re-make the linear analysis
    nc2 = compile_numerical_circuit_at(grid)
    lin2 = LinearAnalysis(nc2)

    # reconstruct injections that should be to keep the flows the same
    Pbus3, _, _, _ = np.linalg.lstsq(lin2.PTDF, Flows0[i_branches])

    dPbus = Pbus2 - Pbus3

    n2 = grid.get_bus_number()
    tol = 1e-5
    for i in range(n2):

        bus = grid.buses[i]

        if abs(dPbus[i]) > tol:
            elm = Generator(name=f"compensated gen {i}", P=-dPbus[i], srap_enabled=True)
            grid.add_generator(bus=bus, api_obj=elm)

    # proof that the flows are actually the same
    Pbus4 = grid.get_Pbus()
    Flows4 = lin2.PTDF @ Pbus4

    diff = Flows0[i_branches] - Flows4

    return grid, logger


def ptdf_reduction_projected(grid: MultiCircuit,
                             reduction_bus_indices: IntVec,
                             tol=1e-8,
                             distribute_slack: bool = True,
                             compact_devices: bool = True) -> Tuple[MultiCircuit, Logger]:
    """
    In-place Grid reduction using the PTDF injection by projecting
    the generation and loads from the removed buses into the PTDF-sensitive buses
    :param grid: MultiCircuit
    :param reduction_bus_indices: Bus indices of the buses to delete
    :param tol: Tolerance, any equivalent power value under this is omitted
    :param distribute_slack: Distribute the slack?
    :param compact_devices: Collapse relocated and compensation devices after reduction
    """
    logger = Logger()

    # find the boundary set: buses from the internal set the join to the external set
    e_buses, i_buses, i_branches = get_reduction_sets(grid=grid, reduction_bus_indices=reduction_bus_indices)

    if len(e_buses) == 0:
        logger.add_info(msg="Nothing to reduce")
        return grid, logger

    if len(i_buses) == 0:
        logger.add_info(msg="Nothing to keep (null grid as a result)")
        return grid, logger

    # Check if slack bus is being removed
    original_slack_indices = [i for i, bus in enumerate(grid.buses) if bus.is_slack]
    external_set = set(e_buses)
    slack_is_removed = any(idx in external_set for idx in original_slack_indices)

    # Compute original flows BEFORE any modifications to the grid
    # This is critical: we want to preserve flows from the ORIGINAL grid topology
    nc = compile_numerical_circuit_at(circuit=grid, t_idx=None)
    lin = LinearAnalysis(nc=nc, distributed_slack=distribute_slack)

    # base flows (BEFORE relocation)
    Pload = get_Pload(grid)
    Pgen, Pgen_srap = get_Pgen(grid)

    # Get HVDC power contribution (HVDC lines inject/withdraw power at their terminals)
    if nc.hvdc_data.nelm > 0:
        _, _, Pf_hvdc_pu, _, _, _ = nc.hvdc_data.get_power(Sbase=nc.Sbase, theta=np.zeros(nc.nbus))
        Flow0_hvdc = lin.HvdcDF @ (Pf_hvdc_pu * nc.Sbase)
    else:
        Flow0_hvdc = np.zeros(nc.nbr)

    # flows (these are the ORIGINAL flows we want to preserve on internal branches)
    # Include HVDC contribution to AC branch flows
    Flow0_load = lin.get_flows(Pload)
    Flow0_gen = lin.get_flows(Pgen)
    Flow0_gen_srap = lin.get_flows(Pgen_srap)

    if grid.has_time_series:
        Pload_ts = get_Pload_ts(grid)
        Pgen_ts, Pgen_srap_ts = get_Pgen_ts(grid)

        lin_ts = LinearAnalysisTs(grid=grid, distributed_slack=distribute_slack)

        Flows0_load_ts = lin_ts.get_flows_ts(P=Pload_ts)
        Flows0_gen_ts = lin_ts.get_flows_ts(P=Pgen_ts)
        Flows0_gen_srap_ts = lin_ts.get_flows_ts(P=Pgen_srap_ts)
    else:
        Flows0_load_ts = None
        Flows0_gen_ts = None
        Flows0_gen_srap_ts = None
    
    # Now relocate injections if the slack is being removed
    # This moves devices from external buses to internal buses so they are not lost during deletion
    if slack_is_removed:
        relocated_ids = relocate_injections(grid=grid, reduction_bus_indices=reduction_bus_indices)
    else:
        relocated_ids: Set[str] = set()

    # Identify boundary buses (internal buses connected to external buses)
    bus_idx_dict = grid.get_bus_index_dict()
    external_set = set(e_buses)
    boundary_set = set()
    
    for branch in grid.get_branches(add_vsc=True, add_hvdc=True, add_switch=False):
        f = bus_idx_dict[branch.bus_from]
        t = bus_idx_dict[branch.bus_to]
        
        if f in external_set and t not in external_set:
            boundary_set.add(t)
        elif t in external_set and f not in external_set:
            boundary_set.add(f)
            
    boundary_buses = np.sort(np.array(list(boundary_set)))
    
    # Eliminate the external buses (but not relocating injections) -----------------------------------------------------
    # We rely on solving for the necessary compensation on the boundary buses
    grid.delete_buses(lst=[grid.buses[e] for e in e_buses], delete_associated=True)
    
    # If the slack was removed, assign a new slack bus
    if slack_is_removed:
        # Find the best candidate for the new slack among boundary buses
        # Prefer a boundary bus that has a generator
        new_slack_assigned = False
        bus_idx_dict_new = grid.get_bus_index_dict()
        
        # First try to find a boundary bus with a generator
        for gen in grid.generators:
            if gen.bus is not None:
                gen_bus_idx = bus_idx_dict_new.get(gen.bus, -1)
                if gen_bus_idx != -1:
                    # This bus has a generator, make it slack
                    gen.bus.is_slack = True
                    new_slack_assigned = True
                    break
        
        # If no generator found, just pick the first remaining bus
        if not new_slack_assigned and grid.get_bus_number() > 0:
            grid.buses[0].is_slack = True

    # Ensure the grid has an explicit slack bus per resulting island (only if missing)
    has_any_explicit_slack = any(b.is_slack for b in grid.buses)
    nc_tmp = compile_numerical_circuit_at(circuit=grid, t_idx=0 if grid.has_time_series else None)
    islands_tmp = nc_tmp.split_into_islands()
    n_islands_tmp = len(islands_tmp)

    for island in islands_tmp:
        island_global_bus_idx = [int(x) for x in island.bus_data.original_idx]

        # Keep at most one explicit slack per island
        island_slacks = [i for i in island_global_bus_idx if grid.buses[i].is_slack]

        if len(island_slacks) > 1:
            keep = island_slacks[0]
            for i in island_slacks[1:]:
                grid.buses[i].is_slack = False
            island_slacks = [keep]

        # Do something when there is no explicit slack in the island
        if len(island_slacks) != 1:
            # if (n_islands_tmp <= 1) and has_any_explicit_slack:
            #     pass

            # else:
            if not (n_islands_tmp <= 1) or not has_any_explicit_slack:
                sim_idx = island.get_simulation_indices()

                if len(sim_idx.vd) == 1:
                    global_slack_idx = int(island.bus_data.original_idx[int(sim_idx.vd[0])])
                    if 0 <= global_slack_idx < grid.get_bus_number():
                        grid.buses[global_slack_idx].is_slack = True

                else:
                    # Fallback: pick the first bus in the island (maybe no PV buses)
                    if island_global_bus_idx:
                        grid.buses[island_global_bus_idx[0]].is_slack = True

    # Injections that remain (internal only, since external are gone)
    Pload2 = get_Pload(grid)
    Pgen2, Pgen_srap2 = get_Pgen(grid)

    # re-make the linear analysis
    nc2 = compile_numerical_circuit_at(grid)
    lin2 = LinearAnalysis(nc2, distributed_slack=distribute_slack)

    # reconstruct injections that should be to keep the flows the same
    # We want to find dP such that: PTDF @ (Pbus2 + dP) = Flow0
    # So: PTDF @ dP = Flow0 - PTDF @ Pbus2

    # Target flows in the original grid (including HVDC contribution)
    Flow0_total = Flow0_load + Flow0_gen + Flow0_gen_srap + Flow0_hvdc
    
    # Total injections and flows in the reduced grid
    Pbus2_total = Pload2 + Pgen2 + Pgen_srap2
    
    # Get HVDC contribution in the reduced grid (some HVDC lines may have been deleted)
    # Note: get_power returns Pf in p.u., need to convert to MW
    if nc2.hvdc_data.nelm > 0:
        _, _, Pf_hvdc2_pu, _, _, _ = nc2.hvdc_data.get_power(Sbase=nc2.Sbase, theta=np.zeros(nc2.nbus))
        Flow2_hvdc = lin2.HvdcDF @ (Pf_hvdc2_pu * nc2.Sbase)
    else:
        Flow2_hvdc = np.zeros(nc2.nbr)
    
    Flow2 = lin2.PTDF @ Pbus2_total + Flow2_hvdc

    Flow2_load = lin2.get_flows(Pload2)
    Flow2_gen = lin2.get_flows(Pgen2)
    Flow2_gen_srap = lin2.get_flows(Pgen_srap2)
   
    # Residual flow to compensate
    residual_flow = Flow0_total[i_branches] - Flow2
    residual_flow_load = Flow0_load[i_branches] - Flow2_load
    residual_flow_gen = Flow0_gen[i_branches] - Flow2_gen
    residual_flow_gen_srap = Flow0_gen_srap[i_branches] - Flow2_gen_srap
    
    # Solve for compensation across all remaining buses (minimum-norm solution).
    dP, _, _, _ = np.linalg.lstsq(lin2.PTDF, residual_flow, rcond=None)
    dP_load, _, _, _ = np.linalg.lstsq(lin2.PTDF, residual_flow_load, rcond=None)
    dP_gen, _, _, _ = np.linalg.lstsq(lin2.PTDF, residual_flow_gen, rcond=None)
    dP_gen_srap, _, _, _ = np.linalg.lstsq(lin2.PTDF, residual_flow_gen_srap, rcond=None)
    
    # We need to add the HVDC correction to ensure the applied compensation matches the total
    dP_hvdc_correction = dP - (dP_load + dP_gen + dP_gen_srap)
    dP_gen_srap = dP_gen_srap + dP_hvdc_correction
    
    # Boundary indices in the reduced grid (kept for allocating the extra balancing terms below)
    boundary_indices_new = np.searchsorted(i_buses, boundary_buses)

    ptdf_col_norms = np.linalg.norm(lin2.PTDF, axis=0)
    zero_influence_mask = ptdf_col_norms < tol
    
    # Zero out columns that cannot influence any flow (e.g., disconnected/island-slack degrees of freedom)
    # to avoid creating meaningless compensated devices.
    dP[zero_influence_mask] = 0.0
    dP_load[zero_influence_mask] = 0.0
    dP_gen[zero_influence_mask] = 0.0
    dP_gen_srap[zero_influence_mask] = 0.0

    if grid.has_time_series:

        Pload2_ts = get_Pload_ts(grid)
        Pgen2_ts, Pgen2_srap_ts = get_Pgen_ts(grid)

        lin_ts2 = LinearAnalysisTs(grid=grid, distributed_slack=distribute_slack)

        # Reconstruct injections that should be to keep the flows the same (TS)
        # We use the same logic as for the static case but for each time step (vectorized)
        # The target flows on internal branches must be preserved
        
        # Target flows (TS) on internal branches
        Flows0_load_ts_i = Flows0_load_ts[:, i_branches]
        Flows0_gen_ts_i = Flows0_gen_ts[:, i_branches]
        Flows0_gen_srap_ts_i = Flows0_gen_srap_ts[:, i_branches]

        # Get the equivalent injections that would produce these flows in the reduced grid
        Pbus3_load_ts = lin_ts2.get_reverse_injections_ts(flows_ts=Flows0_load_ts_i)
        Pbus3_gen_ts = lin_ts2.get_reverse_injections_ts(flows_ts=Flows0_gen_ts_i)
        Pbus3_gen_srap_ts = lin_ts2.get_reverse_injections_ts(flows_ts=Flows0_gen_srap_ts_i)

        dPbus_load_ts = Pload2_ts - Pbus3_load_ts
        dPbus_gen_ts = Pgen2_ts - Pbus3_gen_ts
        dPbus_gen_srap_ts = Pgen2_srap_ts - Pbus3_gen_srap_ts

        # Zero out small values
        dPbus_load_ts[:, zero_influence_mask] = 0.0
        dPbus_gen_ts[:, zero_influence_mask] = 0.0
        dPbus_gen_srap_ts[:, zero_influence_mask] = 0.0

    else:
        dPbus_load_ts = None
        dPbus_gen_ts = None
        dPbus_gen_srap_ts = None

    # Original totals
    total_gen_no_srap_orig = np.sum(Pgen)
    total_gen_yes_srap_orig = np.sum(Pgen_srap)
    total_load_orig = np.sum(Pload)  # Pload is negative in principle
    
    # Calculate what the totals would be if we only added net compensation
    total_gen_no_srap_new = np.sum(Pgen2) + np.sum(dP_gen)
    total_gen_yes_srap_new = np.sum(Pgen_srap2) + np.sum(dP_gen_srap)
    total_load_new = np.sum(Pload2) + np.sum(dP_load)
    
    # Calculate deficits
    APgen_no_srap = total_gen_no_srap_orig - total_gen_no_srap_new
    APgen_yes_srap = total_gen_yes_srap_orig - total_gen_yes_srap_new
    APload = total_load_orig - total_load_new  # both are probably negative
    
    # Determine where to put the extra power
    n2 = grid.get_bus_number()
    extra_power_allocation = np.zeros(n2, dtype=bool) 

    if not distribute_slack:
        # Find slack bus index
        slack_idx = -1
        for i in range(n2):
            if grid.buses[i].is_slack:
                slack_idx = i
                break
        
        if slack_idx != -1:
            # Put everything on slack bus
            extra_power_allocation[slack_idx] = True
            denom = 1.0
        else:
            # Fallback to boundary if no slack bus found (weird but possible)
            extra_power_allocation[boundary_indices_new] = True
            denom = float(len(boundary_indices_new))
    else:
        # Enters here if distribute slack is True

        # Previously we were allocating the deficient to the boundary even if
        # they were not in the slack set, so it perturbed the flows 
        participating = np.zeros(n2, dtype=bool)
        for island in lin2.islands:
            itypes = island.bus_data.bus_types
            gidx = island.bus_data.original_idx
            for li in range(len(gidx)):
                if itypes[li] == BusMode.PV_tpe.value or itypes[li] == BusMode.Slack_tpe.value:
                    participating[int(gidx[li])] = True

        # The compensation generators created are meant to be more like PQ 
        # buses rather than setting the voltage. 
        # Do not change the indices type because of that
        part_idx = np.where(participating)[0]
        if len(part_idx) > 0:
            extra_power_allocation[part_idx] = True
            denom = float(len(part_idx))
        elif len(boundary_indices_new) > 0:
            # Fallback if no participating buses were found, to the boundary
            extra_power_allocation[boundary_indices_new] = True
            denom = float(len(boundary_indices_new))
        else:
            denom = 0.0

    if denom > 0:
        extra_Pgen_no_srap_per_bus = APgen_no_srap / denom
        extra_Pgen_yes_srap_per_bus = APgen_yes_srap / denom
        extra_Pload_per_bus = APload / denom
    else:
        extra_Pgen_no_srap_per_bus = 0.0
        extra_Pgen_yes_srap_per_bus = 0.0
        extra_Pload_per_bus = 0.0

    for i in range(n2):

        bus = grid.buses[i]
        
        # Check allocation
        alloc = extra_power_allocation[i]
        
        extra_gen = extra_Pgen_no_srap_per_bus if alloc else 0.0
        extra_gen_srap = extra_Pgen_yes_srap_per_bus if alloc else 0.0
        extra_load = -extra_Pload_per_bus if alloc else 0.0

        P_gen_no_srap_to_add = dP_gen[i] + extra_gen
        P_gen_yes_srap_to_add = dP_gen_srap[i] + extra_gen_srap
        P_load_to_add = dP_load[i] - extra_load
        
        if abs(P_gen_no_srap_to_add) > tol:
            # Q mode gen
            elm_gen = Generator(name=f"compensated gen {i}",
                                P=P_gen_no_srap_to_add,
                                srap_enabled=False,
                                control_mode=GeneratorControlMode.Q)
            
            if dPbus_gen_ts is not None:
                elm_gen.P_prof = -dPbus_gen_ts[:, i]
                # Enforce active true to avoid the issues I had
                elm_gen.active_prof = np.ones(grid.get_time_number())

            grid.add_generator(bus=bus, api_obj=elm_gen)

        if abs(P_gen_yes_srap_to_add) > tol:
            # Q mode gen like we do with the SRAP ones
            elm_gen = Generator(name=f"compensated gen {i}",
                                P=P_gen_yes_srap_to_add,
                                srap_enabled=True,
                                control_mode=GeneratorControlMode.Q)
            
            if dPbus_gen_srap_ts is not None:
                elm_gen.P_prof = -dPbus_gen_srap_ts[:, i]
                elm_gen.active_prof = np.ones(grid.get_time_number())

            grid.add_generator(bus=bus, api_obj=elm_gen)

        if abs(P_load_to_add) > tol:
            elm_load = Load(name=f"compensated load {i}", 
                            P=-P_load_to_add)
            
            if dPbus_load_ts is not None:
                elm_load.P_prof = dPbus_load_ts[:, i]
                elm_load.active_prof = np.ones(grid.get_time_number())

            grid.add_load(bus=bus, api_obj=elm_load)

    # Compact devices after reduction
    if compact_devices:
        compact_logger = compact_devices_after_reduction(
            grid=grid,
            relocated_device_ids=relocated_ids,
            compensation_prefix="compensated"
        )
        logger += compact_logger

    return grid, logger


# if __name__ == "__main__":
#     import VeraGridEngine as vg
#
#     circuit = vg.open_file("/trunk/equivalents/completo.veragrid")
#
#     ptdf_reduction_projected(
#         grid=circuit,
#         reduction_bus_indices=[4],
#         tol=1e-8
#     )
