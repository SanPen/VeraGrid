# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Dict, Union

from VeraGridEngine.Compilers.Gslv.activation import build_status_dict, pg
from VeraGridEngine.Compilers.Gslv.common import fill_profile
from VeraGridEngine.Devices.Aggregation.facility import Facility
from VeraGridEngine.Devices.Fluid.fluid_injection_template import FluidInjectionTemplate
from VeraGridEngine.Devices.Fluid.fluid_node import FluidNode
from VeraGridEngine.Devices.Fluid.fluid_p2x import FluidP2x
from VeraGridEngine.Devices.Fluid.fluid_path import FluidPath
from VeraGridEngine.Devices.Fluid.fluid_pump import FluidPump
from VeraGridEngine.Devices.Fluid.fluid_turbine import FluidTurbine
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import IntVec


def add_fluid_nodes(circuit: MultiCircuit,
                    gslv_grid: "pg.MultiCircuit",
                    bus_dict: Dict[str, "pg.Bus"],
                    use_time_series: bool,
                    n_time: int,
                    time_indices: Union[IntVec, None]) -> Dict[str, "pg.FluidNode"]:
    """
    Add fluid nodes and return their GSLV lookup by VeraGrid id tag.

    :param circuit: VeraGrid circuit.
    :param gslv_grid: Target GSLV circuit.
    :param bus_dict: Electrical-bus lookup by VeraGrid id tag.
    :param use_time_series: Whether profiles must be exported.
    :param n_time: Number of exported snapshots.
    :param time_indices: Optional selected VeraGrid snapshots.
    :return: Fluid-node lookup by VeraGrid id tag.
    """
    fluid_node_dict: Dict[str, "pg.FluidNode"] = dict()

    for elm in circuit.get_fluid_nodes():
        bus: "pg.Bus | None" = None if elm.bus is None else bus_dict[elm.bus.idtag]
        node = pg.FluidNode(
            nt=n_time, name=elm.name, idtag=elm.idtag, code=elm.code,
            min_level=elm.min_level, max_level=elm.max_level,
            min_soc=elm.min_soc, max_soc=elm.max_soc,
            current_level=elm.initial_level, spillage_cost=elm.spillage_cost,
            inflow=elm.inflow, loss_factor=elm.loss_factor, bus=bus,
            build_status=build_status_dict[elm.build_status], color=elm.color,
        )

        # All mutable hydraulic constraints must retain their selected time-series values.
        fill_profile(node.min_soc, elm.min_soc_prof, use_time_series, time_indices, n_time, elm.min_soc)
        fill_profile(node.max_soc, elm.max_soc_prof, use_time_series, time_indices, n_time, elm.max_soc)
        fill_profile(node.spillage_cost, elm.spillage_cost_prof, use_time_series, time_indices, n_time, elm.spillage_cost)
        fill_profile(node.inflow, elm.inflow_prof, use_time_series, time_indices, n_time, elm.inflow)
        fill_profile(node.loss_factor, elm.loss_factor_prof, use_time_series, time_indices, n_time, elm.loss_factor)

        gslv_grid.add_fluid_node(node)
        fluid_node_dict[elm.idtag] = node

    return fluid_node_dict


def add_fluid_paths(circuit: MultiCircuit,
                    gslv_grid: "pg.MultiCircuit",
                    fluid_node_dict: Dict[str, "pg.FluidNode"],
                    use_time_series: bool,
                    n_time: int,
                    time_indices: Union[IntVec, None]) -> None:
    """
    Add directed fluid paths after their source and target nodes exist.

    :param circuit: VeraGrid circuit.
    :param gslv_grid: Target GSLV circuit.
    :param fluid_node_dict: Fluid-node lookup by VeraGrid id tag.
    :param use_time_series: Whether profiles must be exported.
    :param n_time: Number of exported snapshots.
    :param time_indices: Optional selected VeraGrid snapshots.
    :return: None.
    """
    for elm in circuit.get_fluid_paths():
        source: "pg.FluidNode | None" = None if elm.source is None else fluid_node_dict[elm.source.idtag]
        target: "pg.FluidNode | None" = None if elm.target is None else fluid_node_dict[elm.target.idtag]
        path = pg.FluidPath(
            name=elm.name, idtag=elm.idtag, code=elm.code, source=source, target=target,
            min_flow=elm.min_flow, max_flow=elm.max_flow, loss_factor=elm.loss_factor,
            color=elm.color, build_status=build_status_dict[elm.build_status], nt=n_time,
        )

        # Transfer limits and transfer losses are independent profiles at each OPF snapshot.
        fill_profile(path.min_flow, elm.min_flow_prof, use_time_series, time_indices, n_time, elm.min_flow)
        fill_profile(path.max_flow, elm.max_flow_prof, use_time_series, time_indices, n_time, elm.max_flow)
        fill_profile(path.loss_factor, elm.loss_factor_prof, use_time_series, time_indices, n_time, elm.loss_factor)
        gslv_grid.add_fluid_path(path)


def add_fluid_injections(circuit: MultiCircuit,
                         gslv_grid: "pg.MultiCircuit",
                         fluid_node_dict: Dict[str, "pg.FluidNode"],
                         facility_dict: Dict[Facility, "pg.Facility"],
                         use_time_series: bool,
                         n_time: int,
                         time_indices: Union[IntVec, None]) -> None:
    """
    Add turbines, pumps, and P2X units after fluid nodes and generators exist.

    :param circuit: VeraGrid circuit.
    :param gslv_grid: Target GSLV circuit.
    :param fluid_node_dict: Fluid-node lookup by VeraGrid id tag.
    :param facility_dict: VeraGrid-to-GSLV facility lookup.
    :param use_time_series: Whether profiles must be exported.
    :param n_time: Number of exported snapshots.
    :param time_indices: Optional selected VeraGrid snapshots.
    :return: None.
    """
    generator_dict: Dict[str, "pg.Generator"] = {
        generator.get_idtag(): generator
        for generator in gslv_grid.generators
    }
    injection_groups: tuple[tuple[list[FluidInjectionTemplate], object], ...] = (
        (circuit.get_fluid_turbines(), pg.FluidTurbine),
        (circuit.get_fluid_pumps(), pg.FluidPump),
        (circuit.get_fluid_p2xs(), pg.FluidP2x),
    )

    for injections, injection_tpe in injection_groups:
        for elm in injections:
            plant: "pg.FluidNode | None" = None if elm.plant is None else fluid_node_dict[elm.plant.idtag]
            generator: "pg.Generator | None" = None if elm.generator is None else generator_dict[elm.generator.idtag]
            injection = injection_tpe(
                nt=n_time, name=elm.name, idtag=elm.idtag, code=elm.code,
                efficiency=elm.efficiency, max_flow_rate=elm.max_flow_rate,
                plant=plant, generator=generator,
            )

            # The electrical/fluid conversion and capacity can both vary at each time step.
            fill_profile(injection.active, elm.active_prof, use_time_series, time_indices, n_time, elm.active)
            fill_profile(injection.efficiency, elm.efficiency_prof, use_time_series, time_indices, n_time, elm.efficiency)
            fill_profile(injection.max_flow_rate, elm.max_flow_rate_prof, use_time_series, time_indices, n_time, elm.max_flow_rate)
            injection.facility = facility_dict.get(elm.facility, None)

            if isinstance(elm, FluidTurbine):
                gslv_grid.add_fluid_turbine(injection)
            elif isinstance(elm, FluidPump):
                gslv_grid.add_fluid_pump(injection)
            elif isinstance(elm, FluidP2x):
                gslv_grid.add_fluid_p2x(injection)
            else:
                raise TypeError(f"Unsupported fluid injection type: {type(elm)!r}")
