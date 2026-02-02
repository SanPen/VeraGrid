# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Tuple, List
import VeraGridEngine.Devices as dev
from VeraGridEngine import BusGraphicType
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.types import BRANCH_TYPES, INJECTION_DEVICE_TYPES
from VeraGridEngine.Topology.VoltageLevels.single_bar import (
    create_single_bar,
    create_single_bar_with_disconnectors,
    create_single_bar_with_splitter,
    create_single_bar_with_splitter_with_disconnectors,
    create_single_bar_with_bypass,
    create_single_bar_with_bypass_with_disconnectors)
from VeraGridEngine.Topology.VoltageLevels.double_bar import (
    create_double_bar,
    create_double_bar_with_disconnectors,
    create_double_bar_with_transference_bar,
    create_double_bar_with_transference_bar_with_disconnectors)
from VeraGridEngine.Topology.VoltageLevels.breaker_and_a_half import (
    create_breaker_and_a_half,
    create_breaker_and_a_half_with_disconnectors
)
from VeraGridEngine.Topology.VoltageLevels.ring import (
    create_ring,
    create_ring_with_disconnectors
)
from VeraGridEngine.enumerations import VoltageLevelTypes


def transform_bus_to_connectivity_grid(grid: MultiCircuit, busbar: dev.Bus) -> Tuple[List[dev.Bus], List[dev.Line]]:
    """
    Transform a BusBar into multiple Connectivity buses connected by branches.
    This is to be able to compute the power that passes through a busbar
    for specific busbar power studies

    :param grid: MultiCircuit instance
    :param busbar: the Bus object (BusGraphicType.BusBar) to transform
    :return: list of new Connectivity buses, list of branches between them
    """
    # Collect all connections (busbar side of each device)
    associated_branches, associated_injections = grid.get_bus_devices(bus=busbar)

    # Create a new Connectivity bus for each connection
    new_buses = []
    x_offset = 0
    for idx, elem in enumerate(associated_branches):
        new_bus = dev.Bus(
            name=f"{busbar.name}_conn_{idx}",
            substation=busbar.substation,
            Vnom=busbar.Vnom,
            voltage_level=busbar.voltage_level,
            xpos=busbar.x + x_offset,  # offset a bit to spread them visually
            ypos=busbar.y,
            country=busbar.country,
            graphic_type=BusGraphicType.Connectivity
        )
        grid.add_bus(new_bus)
        new_buses.append(new_bus)

        # Redirect the element to connect to this new bus instead of the busbar
        if elem.bus_from == busbar:
            elem.bus_from = new_bus

        elif elem.bus_to == busbar:
            elem.bus_to = new_bus

        x_offset += 100

    for idx, elem in enumerate(associated_injections):
        new_bus = dev.Bus(
            name=f"{busbar.name}_conn_{idx}",
            substation=busbar.substation,
            Vnom=busbar.Vnom,
            voltage_level=busbar.voltage_level,
            xpos=busbar.x + x_offset,  # offset a bit to spread them visually
            ypos=busbar.y,
            country=busbar.country,
            graphic_type=BusGraphicType.Connectivity
        )
        grid.add_bus(new_bus)
        new_buses.append(new_bus)

        # Redirect the element to connect to this new bus instead of the busbar
        elem.bus = new_bus

        x_offset += 100

    # Electrically tie all new buses with line branches
    new_branches = list()
    for i in range(len(new_buses) - 1):
        ln = dev.Line(
            name=f"{busbar.name}_backbone_{i}",
            bus_from=new_buses[i],
            bus_to=new_buses[i + 1],
        )
        grid.add_line(ln)
        new_branches.append(ln)

    # Remove the original busbar
    grid.delete_bus(busbar)

    return new_buses, new_branches


def transform_bus_into_voltage_level(
        grid: MultiCircuit,
        bus: dev.Bus,
        vl_type=VoltageLevelTypes.SingleBar,
        add_disconnectors: bool = False,
        bar_by_segments: bool = False,
        skip_injections_reconnection: bool = True
) -> Tuple[
    List[dev.Bus],
    List[dev.Bus],
    List[BRANCH_TYPES],
    List[INJECTION_DEVICE_TYPES],
    List[Tuple[BRANCH_TYPES | INJECTION_DEVICE_TYPES, dev.Bus, dev.Bus]]
]:
    """
    Transform a bus into a voltage level
    :param grid: MultiCircuit to add devices to
    :param bus: Bus device to transform
    :param vl_type: VoltageLevelTypes
    :param add_disconnectors: add voltage level disconnectors?
    :param bar_by_segments: Have the bar with connectivities and impedances instead of a single bus-bar?
    :param skip_injections_reconnection: if true the injections are not included in the reconnections list
    :return:
    - List of all voltage level buses,
    - List of bay buses,
    - List of bus connected branches,
    - List of bus connected
    - List of re-connections (element, old bus, new bus)
    """

    # get the associations of the bus
    associated_branches, associated_injections = grid.get_bus_devices(bus=bus)

    # compute the number of bays (positions)
    n_bays = len(associated_branches) + len(associated_injections)
    all_buses: List[dev.Bus] = list()

    if vl_type == VoltageLevelTypes.SingleBar:

        if add_disconnectors:
            vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_single_bar_with_disconnectors(
                name=bus.name,
                grid=grid,
                n_bays=n_bays,
                v_nom=bus.Vnom,
                substation=bus.substation,
                country=bus.country,
                bar_by_segments=bar_by_segments,
                offset_x=bus.x,
                offset_y=bus.y,
            )
        else:
            vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_single_bar(
                name=bus.name,
                grid=grid,
                n_bays=n_bays,
                v_nom=bus.Vnom,
                substation=bus.substation,
                country=bus.country,
                bar_by_segments=bar_by_segments,
                offset_x=bus.x,
                offset_y=bus.y,
            )

    elif vl_type == VoltageLevelTypes.SingleBarWithBypass:

        if add_disconnectors:
            vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_single_bar_with_bypass_with_disconnectors(
                name=bus.name,
                grid=grid,
                n_bays=n_bays,
                v_nom=bus.Vnom,
                substation=bus.substation,
                country=bus.country,
                offset_x=bus.x,
                offset_y=bus.y,
            )
        else:
            vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_single_bar_with_bypass(
                name=bus.name,
                grid=grid,
                n_bays=n_bays,
                v_nom=bus.Vnom,
                substation=bus.substation,
                country=bus.country,
                offset_x=bus.x,
                offset_y=bus.y,
            )

    elif vl_type == VoltageLevelTypes.SingleBarWithSplitter:

        if add_disconnectors:
            vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_single_bar_with_splitter_with_disconnectors(
                name=bus.name,
                grid=grid,
                n_bays=n_bays,
                v_nom=bus.Vnom,
                substation=bus.substation,
                country=bus.country,
                offset_x=bus.x,
                offset_y=bus.y,
            )
        else:
            vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_single_bar_with_splitter(
                name=bus.name,
                grid=grid,
                n_bays=n_bays,
                v_nom=bus.Vnom,
                substation=bus.substation,
                country=bus.country,
                offset_x=bus.x,
                offset_y=bus.y,
            )

    elif vl_type == VoltageLevelTypes.DoubleBar:

        if add_disconnectors:
            vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_double_bar_with_disconnectors(
                name=bus.name,
                grid=grid,
                n_bays=n_bays,
                v_nom=bus.Vnom,
                substation=bus.substation,
                country=bus.country,
                offset_x=bus.x,
                offset_y=bus.y,
            )
        else:
            vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_double_bar(
                name=bus.name,
                grid=grid,
                n_bays=n_bays,
                v_nom=bus.Vnom,
                substation=bus.substation,
                country=bus.country,
                offset_x=bus.x,
                offset_y=bus.y,
            )

    elif vl_type == VoltageLevelTypes.DoubleBarWithBypass:
        # TODO: Implement
        return all_buses, list(), associated_branches, associated_injections, list()

    elif vl_type == VoltageLevelTypes.DoubleBarWithTransference:

        if add_disconnectors:
            (vl, conn_buses, all_buses,
             offset_total_x, offset_total_y) = create_double_bar_with_transference_bar_with_disconnectors(
                name=bus.name,
                grid=grid,
                n_bays=n_bays,
                v_nom=bus.Vnom,
                substation=bus.substation,
                country=bus.country,
                offset_x=bus.x,
                offset_y=bus.y,
            )
        else:
            vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_double_bar_with_transference_bar(
                name=bus.name,
                grid=grid,
                n_bays=n_bays,
                v_nom=bus.Vnom,
                substation=bus.substation,
                country=bus.country,
                offset_x=bus.x,
                offset_y=bus.y,
            )

    elif vl_type == VoltageLevelTypes.DoubleBarDuplex:
        # TODO: Implement
        return all_buses, list(), associated_branches, associated_injections, list()

    elif vl_type == VoltageLevelTypes.Ring:

        if add_disconnectors:
            vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_ring_with_disconnectors(
                name=bus.name,
                grid=grid,
                n_bays=n_bays,
                v_nom=bus.Vnom,
                substation=bus.substation,
                country=bus.country,
                offset_x=bus.x,
                offset_y=bus.y,
            )
        else:
            vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_ring(
                name=bus.name,
                grid=grid,
                n_bays=n_bays,
                v_nom=bus.Vnom,
                substation=bus.substation,
                country=bus.country,
                offset_x=bus.x,
                offset_y=bus.y,
            )

    elif vl_type == VoltageLevelTypes.BreakerAndAHalf:

        if add_disconnectors:
            vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_breaker_and_a_half_with_disconnectors(
                name=bus.name,
                grid=grid,
                n_bays=n_bays,
                v_nom=bus.Vnom,
                substation=bus.substation,
                country=bus.country,
                offset_x=bus.x,
                offset_y=bus.y,
            )
        else:
            vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_breaker_and_a_half(
                name=bus.name,
                grid=grid,
                n_bays=n_bays,
                v_nom=bus.Vnom,
                substation=bus.substation,
                country=bus.country,
                offset_x=bus.x,
                offset_y=bus.y,
            )

    else:
        print(f"{vl_type} not implemented :/")
        return all_buses, list(), associated_branches, associated_injections, list()

    # re-connect the branches and injections to the new position-buses

    # element, old bus, new bus
    reconnection_list = list()

    j = 0
    for elem in associated_branches:
        if elem.bus_from == bus:
            elem.bus_from = conn_buses[j]
            reconnection_list.append((elem, bus, conn_buses[j]))

        elif elem.bus_to == bus:
            elem.bus_to = conn_buses[j]
            reconnection_list.append((elem, bus, conn_buses[j]))

        j += 1

    for elem in associated_injections:
        old_bus = elem.bus
        elem.bus = conn_buses[j]

        if not skip_injections_reconnection:
            reconnection_list.append((elem, old_bus, conn_buses[j]))

        j += 1

    return all_buses, conn_buses, associated_branches, associated_injections, reconnection_list


def _store_voltage_level_data(
        voltage: float,
        conn_buses: List[dev.Bus],
        all_buses: List[dev.Bus],
        vl_type: VoltageLevelTypes,
        conn_buses_by_voltage: dict,
        bars_by_voltage: dict,
        vl_type_by_voltage: dict
) -> None:
    """
    Helper function to store voltage level data (connection buses, bars, and type)
    :param voltage: Voltage level voltage (kV)
    :param conn_buses: List of connection buses
    :param all_buses: List of all buses in the voltage level
    :param vl_type: Voltage level type
    :param conn_buses_by_voltage: Dictionary to store connection buses by voltage
    :param bars_by_voltage: Dictionary to store bars by voltage
    :param vl_type_by_voltage: Dictionary to store voltage level type by voltage
    """
    # Store connection buses for this voltage level
    if voltage not in conn_buses_by_voltage:
        conn_buses_by_voltage[voltage] = []
    conn_buses_by_voltage[voltage].extend(conn_buses)

    # Store bars (buses with BusGraphicType.BusBar) for this voltage level
    bars = [bus for bus in all_buses if bus.graphic_type == BusGraphicType.BusBar]
    if voltage not in bars_by_voltage:
        bars_by_voltage[voltage] = []
    # Only add bars that are not already in the list (avoid duplicates)
    existing_bar_ids = {b.idtag for b in bars_by_voltage[voltage]}
    new_bars = [b for b in bars if b.idtag not in existing_bar_ids]
    bars_by_voltage[voltage].extend(new_bars)

    # Store voltage level type
    vl_type_by_voltage[voltage] = vl_type


def create_substation(
        grid: MultiCircuit,
        se_name: str,
        se_code: str,
        lat: float,
        lon: float,
        vl_templates: List[dev.VoltageLevelTemplate],
        buses_to_replace: List[dev.Bus] = None
) -> Tuple[dev.Substation, List[dev.VoltageLevel]]:
    """
    Create a complete substation
    :param grid: MultiCircuit instance
    :param se_name: Substation name
    :param se_code: Substation code
    :param lat: Latitude
    :param lon: Longitude
    :param vl_templates: List of VoltageLevelTemplates to convert
    :param buses_to_replace: Optional list of buses to merge
    :return: se_object, [vl list]
    """
    # Collect connections from buses to replace before creating the substation
    bus_connections = {}  # Maps bus -> (associated_branches, associated_injections)
    # Group buses to replace by voltage level for matching with templates
    buses_by_voltage = {}  # Maps voltage -> list of buses

    if buses_to_replace:
        for bus in buses_to_replace:
            associated_branches, associated_injections = grid.get_bus_devices(bus=bus)
            bus_connections[bus] = (associated_branches, associated_injections)

            v_nom = bus.Vnom
            if v_nom not in buses_by_voltage:
                buses_by_voltage[v_nom] = []
            buses_by_voltage[v_nom].append(bus)

    # create the SE
    se_object = dev.Substation(name=se_name,
                               code=se_code,
                               latitude=lat,
                               longitude=lon)

    grid.add_substation(obj=se_object)
    # substation_graphics = self.add_api_substation(api_object=se_object, lat=lat, lon=lon)

    voltage_levels = list()
    # Track connection buses by voltage level for reconnecting
    conn_buses_by_voltage = {}  # Maps voltage -> list of connection buses
    # Track bars by voltage level for renaming
    bars_by_voltage = {}  # Maps voltage -> list of bars (BusGraphicType.BusBar)
    # Track voltage level type by voltage for renaming
    vl_type_by_voltage = {}  # Maps voltage -> VoltageLevelTypes

    offset_x = 0
    offset_y = 0
    for vl_template in vl_templates:

        # True if config is known, hence we have to store voltage level info
        known_config = False

        if vl_template.vl_type == VoltageLevelTypes.SingleBar:

            if vl_template.add_disconnectors:
                vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_single_bar_with_disconnectors(
                    name=f"{se_object.name}-@{vl_template.name} @{vl_template.voltage} kV VL",
                    grid=grid,
                    n_bays=vl_template.n_bays,
                    v_nom=vl_template.voltage,
                    substation=se_object,
                    offset_x=offset_x,
                    offset_y=offset_y,
                )
            else:
                vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_single_bar(
                    name=f"{se_object.name}-@{vl_template.name} @{vl_template.voltage} kV VL",
                    grid=grid,
                    n_bays=vl_template.n_bays,
                    v_nom=vl_template.voltage,
                    substation=se_object,
                    offset_x=offset_x,
                    offset_y=offset_y,
                )

            offset_x = offset_total_x
            offset_y = offset_total_y
            voltage_levels.append(vl)

            known_config = True

        elif vl_template.vl_type == VoltageLevelTypes.SingleBarWithBypass:

            if vl_template.add_disconnectors:
                vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_single_bar_with_bypass_with_disconnectors(
                    name=f"{se_object.name}-@{vl_template.name} @{vl_template.voltage} kV VL",
                    grid=grid,
                    n_bays=vl_template.n_bays,
                    v_nom=vl_template.voltage,
                    substation=se_object,
                    offset_x=offset_x,
                    offset_y=offset_y,
                )
            else:
                vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_single_bar_with_bypass(
                    name=f"{se_object.name}-@{vl_template.name} @{vl_template.voltage} kV VL",
                    grid=grid,
                    n_bays=vl_template.n_bays,
                    v_nom=vl_template.voltage,
                    substation=se_object,
                    offset_x=offset_x,
                    offset_y=offset_y,
                )

            offset_x = offset_total_x
            offset_y = offset_total_y
            voltage_levels.append(vl)

            known_config = True

        elif vl_template.vl_type == VoltageLevelTypes.SingleBarWithSplitter:

            if vl_template.add_disconnectors:
                vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_single_bar_with_splitter_with_disconnectors(
                    name=f"{se_object.name}-@{vl_template.name} @{vl_template.voltage} kV VL",
                    grid=grid,
                    n_bays=vl_template.n_bays,
                    v_nom=vl_template.voltage,
                    substation=se_object,
                    offset_x=offset_x,
                    offset_y=offset_y,
                )
            else:
                vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_single_bar_with_splitter(
                    name=f"{se_object.name}-@{vl_template.name} @{vl_template.voltage} kV VL",
                    grid=grid,
                    n_bays=vl_template.n_bays,
                    v_nom=vl_template.voltage,
                    substation=se_object,
                    offset_x=offset_x,
                    offset_y=offset_y,
                )

            offset_x = offset_total_x
            offset_y = offset_total_y
            voltage_levels.append(vl)

            known_config = True

        elif vl_template.vl_type == VoltageLevelTypes.DoubleBar:

            if vl_template.add_disconnectors:
                vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_double_bar_with_disconnectors(
                    name=f"{se_object.name}-@{vl_template.name} @{vl_template.voltage} kV VL",
                    grid=grid,
                    n_bays=vl_template.n_bays,
                    v_nom=vl_template.voltage,
                    substation=se_object,
                    offset_x=offset_x,
                    offset_y=offset_y,
                )
            else:
                vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_double_bar(
                    name=f"{se_object.name}-@{vl_template.name} @{vl_template.voltage} kV VL",
                    grid=grid,
                    n_bays=vl_template.n_bays,
                    v_nom=vl_template.voltage,
                    substation=se_object,
                    offset_x=offset_x,
                    offset_y=offset_y,
                )

            offset_x = offset_total_x
            offset_y = offset_total_y
            voltage_levels.append(vl)

            known_config = True

        elif vl_template.vl_type == VoltageLevelTypes.DoubleBarWithBypass:
            # TODO: Implement
            pass

        elif vl_template.vl_type == VoltageLevelTypes.DoubleBarWithTransference:

            if vl_template.add_disconnectors:
                (vl, conn_buses, all_buses,
                 offset_total_x, offset_total_y) = create_double_bar_with_transference_bar_with_disconnectors(
                    name=f"{se_object.name}-@{vl_template.name} @{vl_template.voltage} kV VL",
                    grid=grid,
                    n_bays=vl_template.n_bays,
                    v_nom=vl_template.voltage,
                    substation=se_object,
                    offset_x=offset_x,
                    offset_y=offset_y,
                )
            else:
                vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_double_bar_with_transference_bar(
                    name=f"{se_object.name}-@{vl_template.name} @{vl_template.voltage} kV VL",
                    grid=grid,
                    n_bays=vl_template.n_bays,
                    v_nom=vl_template.voltage,
                    substation=se_object,
                    offset_x=offset_x,
                    offset_y=offset_y,
                )

            offset_x = offset_total_x
            offset_y = offset_total_y
            voltage_levels.append(vl)

            known_config = True

        elif vl_template.vl_type == VoltageLevelTypes.DoubleBarDuplex:
            # TODO: Implement
            pass

        elif vl_template.vl_type == VoltageLevelTypes.Ring:

            if vl_template.add_disconnectors:
                vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_ring_with_disconnectors(
                    name=f"{se_object.name}-@{vl_template.name} @{vl_template.voltage} kV VL",
                    grid=grid,
                    n_bays=vl_template.n_bays,
                    v_nom=vl_template.voltage,
                    substation=se_object,
                    offset_x=offset_x,
                    offset_y=offset_y,
                )
            else:
                vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_ring(
                    name=f"{se_object.name}-@{vl_template.name} @{vl_template.voltage} kV VL",
                    grid=grid,
                    n_bays=vl_template.n_bays,
                    v_nom=vl_template.voltage,
                    substation=se_object,
                    offset_x=offset_x,
                    offset_y=offset_y,
                )

            offset_x = offset_total_x
            offset_y = offset_total_y
            voltage_levels.append(vl)

            known_config = True

        elif vl_template.vl_type == VoltageLevelTypes.BreakerAndAHalf:

            if vl_template.add_disconnectors:
                vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_breaker_and_a_half_with_disconnectors(
                    name=f"{se_object.name}-@{vl_template.name} @{vl_template.voltage} kV VL",
                    grid=grid,
                    n_bays=vl_template.n_bays,
                    v_nom=vl_template.voltage,
                    substation=se_object,
                    offset_x=offset_x,
                    offset_y=offset_y,
                )
            else:
                vl, conn_buses, all_buses, offset_total_x, offset_total_y = create_breaker_and_a_half(
                    name=f"{se_object.name}-@{vl_template.name} @{vl_template.voltage} kV VL",
                    grid=grid,
                    n_bays=vl_template.n_bays,
                    v_nom=vl_template.voltage,
                    substation=se_object,
                    offset_x=offset_x,
                    offset_y=offset_y,
                )

            offset_x = offset_total_x
            offset_y = offset_total_y
            voltage_levels.append(vl)

            known_config = True

        else:
            print(f"{vl_template.vl_type} not implemented :/")

        if known_config:
            _store_voltage_level_data(
                voltage=vl_template.voltage,
                conn_buses=conn_buses,
                all_buses=all_buses,
                vl_type=vl_template.vl_type,
                conn_buses_by_voltage=conn_buses_by_voltage,
                bars_by_voltage=bars_by_voltage,
                vl_type_by_voltage=vl_type_by_voltage
            )

        else:
            # Nothing to store
            pass

    # Rename bars (busbars) based on original bus names, following REE instructions
    # Track which voltage levels have been renamed to avoid duplicate renaming
    renamed_voltage_levels = set()
    if buses_to_replace:
        for old_bus in buses_to_replace:
            v_nom = old_bus.Vnom
            # Only rename once per voltage level (use first bus name for that voltage)
            if v_nom in bars_by_voltage and v_nom in vl_type_by_voltage and v_nom not in renamed_voltage_levels:
                bars_for_voltage = bars_by_voltage[v_nom]
                vl_type = vl_type_by_voltage[v_nom]
                original_name = old_bus.name

                if vl_type == VoltageLevelTypes.SingleBar:
                    # Single bar: rename the bar to {original_name}JBP1
                    if len(bars_for_voltage) > 0:
                        bars_for_voltage[0].name = f"{original_name}_JBP1"

                elif vl_type == VoltageLevelTypes.DoubleBar:
                    # Double bar: rename the 2 bars to {original_name}JBP1 and JBP2
                    if len(bars_for_voltage) >= 1:
                        bars_for_voltage[0].name = f"{original_name}_JBP1"
                    if len(bars_for_voltage) >= 2:
                        bars_for_voltage[1].name = f"{original_name}_JBP2"

                elif vl_type == VoltageLevelTypes.BreakerAndAHalf:
                    # Breaker and a half: rename the 2 bars to {original_name}JBP1 and JBP2
                    if len(bars_for_voltage) >= 1:
                        bars_for_voltage[0].name = f"{original_name}_JBP1"
                    if len(bars_for_voltage) >= 2:
                        bars_for_voltage[1].name = f"{original_name}_JBP2"
                else:
                    # Nothing to rename
                    pass

                # Mark this voltage level as renamed
                renamed_voltage_levels.add(v_nom)

    # Reconnect buses to replace to the new substation connection buses
    buses_to_delete = []
    # Track connection index per voltage level to distribute connections evenly
    conn_idx_by_voltage = {}

    if buses_to_replace and bus_connections:
        for old_bus in buses_to_replace:
            v_nom = old_bus.Vnom
            associated_branches, associated_injections = bus_connections[old_bus]

            # Find matching connection buses for this voltage level
            if v_nom in conn_buses_by_voltage and len(conn_buses_by_voltage[v_nom]) > 0:
                # Get the first available connection bus for this voltage level
                # We will distribute connections across available connection buses
                conn_buses_for_voltage = conn_buses_by_voltage[v_nom]

                # Initialize connection index for this voltage level if not already done
                if v_nom not in conn_idx_by_voltage:
                    conn_idx_by_voltage[v_nom] = 0

                # Reconnect branches
                for elem in associated_branches:
                    conn_idx = conn_idx_by_voltage[v_nom]
                    new_bus = conn_buses_for_voltage[conn_idx]
                    if elem.bus_from == old_bus:
                        elem.bus_from = new_bus
                    elif elem.bus_to == old_bus:
                        elem.bus_to = new_bus
                    # Move to next connection bus, wrapping around if needed
                    conn_idx_by_voltage[v_nom] = (conn_idx + 1) % len(conn_buses_for_voltage)

                # Reconnect injections
                for elem in associated_injections:
                    conn_idx = conn_idx_by_voltage[v_nom]
                    new_bus = conn_buses_for_voltage[conn_idx]
                    elem.bus = new_bus
                    # Move to next connection bus, wrapping around if needed
                    conn_idx_by_voltage[v_nom] = (conn_idx + 1) % len(conn_buses_for_voltage)

                # Mark the old bus for deletion after all reconnections are done
                buses_to_delete.append(old_bus)

    # Delete old buses considering we have all reconnections complete
    for old_bus in buses_to_delete:
        grid.delete_bus(old_bus)

    return se_object, voltage_levels
