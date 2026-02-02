# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Tuple, List
import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import BusGraphicType, SwitchGraphicType
from VeraGridEngine.Topology.VoltageLevels.single_bar import connect_bar_segments


def create_double_bar_with_disconnectors(
        name: str,
        grid: MultiCircuit,
        n_bays: int,
        v_nom: float,
        substation: dev.Substation,
        country: dev.Country = None,
        bar_by_segments: bool = False,
        offset_x: float = 0,
        offset_y: float = 0
) -> Tuple[dev.VoltageLevel, List[dev.Bus], List[dev.Bus], float, float]:
    """
    Create a double-bar voltage level
    :param name: Voltage level name
    :param grid: MultiCircuit to do the mods
    :param n_bays: number of bays (positions)
    :param v_nom: Nominal voltage
    :param substation: Substation where it belongs
    :param country: Country (Optional)
    :param bar_by_segments: Split the bar into segments
    :param offset_x: x ofsset (px)
    :param offset_y: y ofsset (px)
    :return: Voltage level object, list of busses where connections are allowed, offset x, offset y
    """

    vl = dev.VoltageLevel(name=name, substation=substation, Vnom=v_nom)
    grid.add_voltage_level(vl)

    bus_width = 120
    x_dist = bus_width * 2
    y_dist = bus_width * 1.5
    l_x_pos: List[float] = []
    l_y_pos: List[float] = []
    conn_buses: List[dev.Bus] = list()
    all_buses: List[dev.Bus] = list()
    bar1_buses: List[dev.Bus] = list()
    bar2_buses: List[dev.Bus] = list()

    if not bar_by_segments:
        width = (n_bays + 1) * bus_width + bus_width * 2 + (x_dist - bus_width) * n_bays
        bar1 = dev.Bus(name=f"{name} bar1",
                       substation=substation,
                       Vnom=v_nom,
                       voltage_level=vl,
                       width=width,
                       xpos=offset_x - bus_width,
                       ypos=offset_y + y_dist * 3,
                       country=country,
                       graphic_type=BusGraphicType.BusBar)
        grid.add_bus(bar1)
        all_buses.append(bar1)
        l_x_pos.append(bar1.x)
        l_y_pos.append(bar1.y)

        bar2 = dev.Bus(name=f"{name} bar2",
                       substation=substation,
                       Vnom=v_nom,
                       voltage_level=vl,
                       width=width,
                       xpos=offset_x - bus_width,
                       ypos=offset_y + y_dist * 4,
                       country=country,
                       graphic_type=BusGraphicType.BusBar)
        grid.add_bus(bar2)
        all_buses.append(bar2)
        l_x_pos.append(bar2.x)
        l_y_pos.append(bar2.y)
    else:
        # bar1 & 2 will be assigned inside the loop
        bar1: dev.Bus | None = None
        bar2: dev.Bus | None = None

    for i in range(n_bays):

        if bar_by_segments:
            bar1 = dev.Bus(name=f"{name} bar1 ({i + 1})",
                           substation=substation,
                           Vnom=v_nom,
                           voltage_level=vl,
                           width=50,
                           xpos=offset_x - bus_width,
                           ypos=offset_y + y_dist,
                           country=country,
                           graphic_type=BusGraphicType.Connectivity)
            grid.add_bus(bar1)
            all_buses.append(bar1)
            l_x_pos.append(bar1.x)
            l_y_pos.append(bar1.y)
            bar1_buses.append(bar1)

            bar2 = dev.Bus(name=f"{name} bar2 ({i + 1})",
                           substation=substation,
                           Vnom=v_nom,
                           voltage_level=vl,
                           width=50,
                           xpos=offset_x - bus_width,
                           ypos=offset_y + y_dist,
                           country=country,
                           graphic_type=BusGraphicType.Connectivity)
            grid.add_bus(bar2)
            all_buses.append(bar2)
            l_x_pos.append(bar2.x)
            l_y_pos.append(bar2.y)
            bar2_buses.append(bar2)
        else:
            # already assigned outside the loop
            pass

        bus1 = dev.Bus(name=f"{name}_bay_conn_{i}",
                       substation=substation,
                       Vnom=v_nom,
                       voltage_level=vl,
                       xpos=offset_x + i * x_dist,
                       ypos=offset_y,
                       width=bus_width,
                       country=country,
                       graphic_type=BusGraphicType.Connectivity)

        bus2 = dev.Bus(name=f"LineBus2_{i}",
                       substation=substation,
                       Vnom=v_nom,
                       voltage_level=vl,
                       xpos=offset_x + i * x_dist,
                       ypos=offset_y + y_dist,
                       width=bus_width,
                       country=country,
                       graphic_type=BusGraphicType.Connectivity)

        bus3 = dev.Bus(name=f"LineBus3_{i}",
                       substation=substation,
                       Vnom=v_nom,
                       voltage_level=vl,
                       xpos=offset_x + i * x_dist,
                       ypos=offset_y + y_dist * 2,
                       width=bus_width,
                       country=country,
                       graphic_type=BusGraphicType.Connectivity)

        dis1 = dev.Switch(name=f"Dis1_{i}", bus_from=bus1, bus_to=bus2, graphic_type=SwitchGraphicType.Disconnector)
        cb1 = dev.Switch(name=f"CB_{i}", bus_from=bus2, bus_to=bus3, graphic_type=SwitchGraphicType.CircuitBreaker)
        dis2 = dev.Switch(name=f"Dis2_{i}", bus_from=bar1, bus_to=bus3, graphic_type=SwitchGraphicType.Disconnector)
        dis3 = dev.Switch(name=f"Dis3_{i}", bus_from=bar2, bus_to=bus3, graphic_type=SwitchGraphicType.Disconnector)

        grid.add_bus(bus1)
        all_buses.append(bus1)
        l_x_pos.append(bus1.x)
        l_y_pos.append(bus1.y)

        grid.add_bus(bus2)
        all_buses.append(bus2)
        l_x_pos.append(bus2.x)
        l_y_pos.append(bus2.y)

        grid.add_bus(bus3)
        all_buses.append(bus3)
        l_x_pos.append(bus3.x)
        l_y_pos.append(bus3.y)

        grid.add_switch(dis1)
        grid.add_switch(cb1)
        grid.add_switch(dis2)
        grid.add_switch(dis3)

        conn_buses.append(bus1)

    # coupling
    bus1 = dev.Bus(name=f"{name}_coupling_bar1",
                   substation=substation,
                   Vnom=v_nom,
                   voltage_level=vl,
                   xpos=offset_x + n_bays * x_dist,
                   ypos=offset_y + y_dist * 3.6,
                   width=bus_width,
                   country=country,
                   graphic_type=BusGraphicType.Connectivity)

    bus2 = dev.Bus(name=f"{name}_coupling_bar2",
                   substation=substation,
                   Vnom=v_nom,
                   voltage_level=vl,
                   xpos=offset_x + n_bays * x_dist + x_dist * 0.5,
                   ypos=offset_y + y_dist * 3.6,
                   width=bus_width,
                   country=country,
                   graphic_type=BusGraphicType.Connectivity)

    dis1 = dev.Switch(name="Dis_bar1", bus_from=bar1, bus_to=bus1, graphic_type=SwitchGraphicType.Disconnector)
    dis2 = dev.Switch(name="Dis_bar2", bus_from=bar2, bus_to=bus2, graphic_type=SwitchGraphicType.Disconnector)
    cb1 = dev.Switch(name="CB_coupling", bus_from=bus1, bus_to=bus2, graphic_type=SwitchGraphicType.CircuitBreaker)

    grid.add_bus(bus1)
    all_buses.append(bus1)
    l_x_pos.append(bus1.x)
    l_y_pos.append(bus1.y)

    grid.add_bus(bus2)
    all_buses.append(bus2)
    l_x_pos.append(bus2.x)
    l_y_pos.append(bus2.y)

    grid.add_switch(dis1)
    grid.add_switch(dis2)
    grid.add_switch(cb1)

    offset_total_x = max(l_x_pos, default=0) + x_dist
    offset_total_y = max(l_y_pos, default=0) + y_dist

    # connect the bar dots if that's the case
    if bar_by_segments:
        if len(bar1_buses) > 1:
            connect_bar_segments(grid=grid, bar_buses=bar1_buses, name=name)

        if len(bar2_buses) > 1:
            connect_bar_segments(grid=grid, bar_buses=bar2_buses, name=name)

    return vl, conn_buses, all_buses, offset_total_x, offset_total_y


def create_double_bar(
        name: str,
        grid: MultiCircuit,
        n_bays: int,
        v_nom: float,
        substation: dev.Substation,
        country: dev.Country = None,
        bar_by_segments: bool = False,
        offset_x: float = 0,
        offset_y: float = 0
) -> Tuple[dev.VoltageLevel, List[dev.Bus], List[dev.Bus], float, float]:
    """
    Create a double-bar voltage level
    :param name: Voltage level name
    :param grid: MultiCircuit to do the mods
    :param n_bays: number of bays (positions)
    :param v_nom: Nominal voltage
    :param substation: Substation where it belongs
    :param country: Country (Optional)
    :param bar_by_segments: Split the bar into segments
    :param offset_x: x ofsset (px)
    :param offset_y: y ofsset (px)
    :return: Voltage level object, list of busses where connections are allowed, offset x, offset y
    """

    vl = dev.VoltageLevel(name=name, substation=substation, Vnom=v_nom)
    grid.add_voltage_level(vl)

    bus_width = 120
    x_dist = bus_width * 2
    y_dist = bus_width * 1.5
    l_x_pos: List[float] = []
    l_y_pos: List[float] = []
    conn_buses: List[dev.Bus] = list()
    all_buses: List[dev.Bus] = list()
    bar1_buses: List[dev.Bus] = list()
    bar2_buses: List[dev.Bus] = list()

    if not bar_by_segments:
        bar1 = dev.Bus(name=f"{name} bar1",
                       substation=substation,
                       Vnom=v_nom,
                       voltage_level=vl,
                       width=(n_bays + 1) * bus_width + bus_width * 2 + (x_dist - bus_width) * n_bays,
                       xpos=offset_x - bus_width,
                       ypos=offset_y + y_dist * 2,
                       country=country,
                       graphic_type=BusGraphicType.BusBar)
        grid.add_bus(bar1)
        all_buses.append(bar1)
        l_x_pos.append(bar1.x)
        l_y_pos.append(bar1.y)

        bar2 = dev.Bus(f"{name} bar2", substation=substation, Vnom=v_nom, voltage_level=vl,
                       width=(n_bays + 1) * bus_width + bus_width * 2 + (x_dist - bus_width) * n_bays,
                       xpos=offset_x - bus_width,
                       ypos=offset_y + y_dist * 3,
                       country=country,
                       graphic_type=BusGraphicType.BusBar)
        grid.add_bus(bar2)
        all_buses.append(bar2)
        l_x_pos.append(bar2.x)
        l_y_pos.append(bar2.y)
    else:
        # bar1 & 2 will be assigned inside the loop
        bar1: dev.Bus | None = None
        bar2: dev.Bus | None = None

    for i in range(n_bays):

        if bar_by_segments:
            bar1 = dev.Bus(name=f"{name} bar1 ({i + 1})",
                           substation=substation,
                           Vnom=v_nom,
                           voltage_level=vl,
                           width=50,
                           xpos=offset_x - bus_width,
                           ypos=offset_y + y_dist,
                           country=country,
                           graphic_type=BusGraphicType.Connectivity)
            grid.add_bus(bar1)
            all_buses.append(bar1)
            l_x_pos.append(bar1.x)
            l_y_pos.append(bar1.y)
            bar1_buses.append(bar1)

            bar2 = dev.Bus(name=f"{name} bar2 ({i + 1})",
                           substation=substation,
                           Vnom=v_nom,
                           voltage_level=vl,
                           width=50,
                           xpos=offset_x - bus_width,
                           ypos=offset_y + y_dist,
                           country=country,
                           graphic_type=BusGraphicType.Connectivity)
            grid.add_bus(bar2)
            all_buses.append(bar1)
            l_x_pos.append(bar2.x)
            l_y_pos.append(bar2.y)
            bar2_buses.append(bar2)
        else:
            # already assigned outside the loop
            pass

        bus1 = dev.Bus(f"{name}_bay_conn_{i}", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=offset_x + i * x_dist, ypos=offset_y + y_dist * 0, width=bus_width, country=country,
                       graphic_type=BusGraphicType.Connectivity)

        bus2 = dev.Bus(f"LineBus2_{i}", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=offset_x + i * x_dist, ypos=offset_y + y_dist, width=bus_width, country=country,
                       graphic_type=BusGraphicType.Connectivity)

        cb1 = dev.Switch(name=f"CB_{i}", bus_from=bus1, bus_to=bus2, graphic_type=SwitchGraphicType.CircuitBreaker)
        dis1 = dev.Switch(name=f"Dis2_{i}", bus_from=bar1, bus_to=bus2, graphic_type=SwitchGraphicType.Disconnector)
        dis2 = dev.Switch(name=f"Dis3_{i}", bus_from=bar2, bus_to=bus2, graphic_type=SwitchGraphicType.Disconnector)

        grid.add_bus(bus1)
        all_buses.append(bus1)
        l_x_pos.append(bus1.x)
        l_y_pos.append(bus1.y)

        grid.add_bus(bus2)
        all_buses.append(bus2)
        l_x_pos.append(bus2.x)
        l_y_pos.append(bus2.y)

        grid.add_switch(cb1)
        grid.add_switch(dis1)  # this disconnectors must be included to respect the SE geometry
        grid.add_switch(dis2)  # this disconnectors must be included to respect the SE geometry

        conn_buses.append(bus1)

    # coupling
    cb1 = dev.Switch(name="CB_coupling", bus_from=bar1, bus_to=bar2, graphic_type=SwitchGraphicType.CircuitBreaker)
    grid.add_switch(cb1)

    # connect the bar dots if that's the case
    if bar_by_segments:
        if len(bar1_buses) > 1:
            connect_bar_segments(grid=grid, bar_buses=bar1_buses, name=name)

        if len(bar2_buses) > 1:
            connect_bar_segments(grid=grid, bar_buses=bar2_buses, name=name)

    offset_total_x = max(l_x_pos, default=0) + x_dist
    offset_total_y = max(l_y_pos, default=0) + y_dist

    return vl, conn_buses, all_buses, offset_total_x, offset_total_y


def create_double_bar_with_transference_bar_with_disconnectors(
        name: str,
        grid: MultiCircuit,
        n_bays: int,
        v_nom: float,
        substation: dev.Substation,
        country: dev.Country = None,
        bar_by_segments: bool = False,
        offset_x=0,
        offset_y=0
) -> Tuple[dev.VoltageLevel, List[dev.Bus], List[dev.Bus], float, float]:
    """
    Create a double-bar with transference bar voltage level
    :param name: Voltage level name
    :param grid: MultiCircuit to do the mods
    :param n_bays: number of bays (positions)
    :param v_nom: Nominal voltage
    :param substation: Substation where it belongs
    :param country: Country (Optional)
    :param bar_by_segments: Split the bar into segments
    :param offset_x: x ofsset (px)
    :param offset_y: y ofsset (px)
    :return: Voltage level object, list of busses where connections are allowed, offset x, offset y
    """

    vl = dev.VoltageLevel(name=name, substation=substation, Vnom=v_nom)
    grid.add_voltage_level(vl)

    bus_width = 120
    x_dist = bus_width * 2
    y_dist = bus_width * 1.5
    l_x_pos = []
    l_y_pos = []
    conn_buses: List[dev.Bus] = list()
    all_buses: List[dev.Bus] = list()
    bar1_buses: List[dev.Bus] = list()
    bar2_buses: List[dev.Bus] = list()
    bar_transfer_buses: List[dev.Bus] = list()

    if not bar_by_segments:
        bar1 = dev.Bus(name=f"{name} bar1", substation=substation, Vnom=v_nom, voltage_level=vl,
                       width=(n_bays + 1) * bus_width + bus_width * 2 + (x_dist - bus_width) * (n_bays - 1),
                       xpos=offset_x - bus_width,
                       ypos=offset_y + y_dist * 3,
                       country=country,
                       graphic_type=BusGraphicType.BusBar)
        grid.add_bus(bar1)
        all_buses.append(bar1)
        l_x_pos.append(bar1.x)
        l_y_pos.append(bar1.y)

        bar2 = dev.Bus(name=f"{name} bar2", substation=substation, Vnom=v_nom, voltage_level=vl,
                       width=(n_bays + 1) * bus_width + bus_width * 2 + (x_dist - bus_width) * (n_bays - 1),
                       xpos=offset_x - bus_width,
                       ypos=offset_y + y_dist * 4, country=country,
                       graphic_type=BusGraphicType.BusBar)
        grid.add_bus(bar2)
        all_buses.append(bar2)
        l_x_pos.append(bar2.x)
        l_y_pos.append(bar2.y)

        transfer_bar = dev.Bus(name=f"{name} transfer bar", substation=substation, Vnom=v_nom, voltage_level=vl,
                               width=(n_bays + 1) * bus_width + bus_width * 2 + (x_dist - bus_width) * (n_bays - 1),
                               xpos=offset_x - bus_width, ypos=offset_y + y_dist * 5, country=country,
                               graphic_type=BusGraphicType.BusBar)
        grid.add_bus(transfer_bar)
        l_x_pos.append(transfer_bar.x)
        l_y_pos.append(transfer_bar.y)

    else:
        # bar1 & 2 will be assigned inside the loop
        bar1: dev.Bus | None = None
        bar2: dev.Bus | None = None
        transfer_bar: dev.Bus | None = None

    for i in range(n_bays):

        if bar_by_segments:
            bar1 = dev.Bus(name=f"{name} bar1 ({i + 1})",
                           substation=substation,
                           Vnom=v_nom,
                           voltage_level=vl,
                           width=50,
                           xpos=offset_x - bus_width,
                           ypos=offset_y + y_dist,
                           country=country,
                           graphic_type=BusGraphicType.Connectivity)
            grid.add_bus(bar1)
            all_buses.append(bar1)
            l_x_pos.append(bar1.x)
            l_y_pos.append(bar1.y)
            bar1_buses.append(bar1)

            bar2 = dev.Bus(name=f"{name} bar2 ({i + 1})",
                           substation=substation,
                           Vnom=v_nom,
                           voltage_level=vl,
                           width=50,
                           xpos=offset_x - bus_width,
                           ypos=offset_y + y_dist,
                           country=country,
                           graphic_type=BusGraphicType.Connectivity)
            grid.add_bus(bar2)
            all_buses.append(bar2)
            l_x_pos.append(bar2.x)
            l_y_pos.append(bar2.y)
            bar2_buses.append(bar2)

            bar_t = dev.Bus(name=f"{name} bar_t ({i + 1})",
                            substation=substation,
                            Vnom=v_nom,
                            voltage_level=vl,
                            width=50,
                            xpos=offset_x - bus_width,
                            ypos=offset_y + y_dist,
                            country=country,
                            graphic_type=BusGraphicType.Connectivity)
            grid.add_bus(bar_t)
            all_buses.append(bar_t)
            l_x_pos.append(bar_t.x)
            l_y_pos.append(bar_t.y)
            bar_transfer_buses.append(bar_t)
        else:
            # already assigned outside the loop
            pass

        bus1 = dev.Bus(name=f"{name}_bay_conn_{i}", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=offset_x + i * x_dist + x_dist * 0.2,
                       ypos=offset_y, width=bus_width, country=country,
                       graphic_type=BusGraphicType.Connectivity)

        bus2 = dev.Bus(name=f"BayBus2_{i}", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=offset_x + i * x_dist - x_dist * 0.25,
                       ypos=offset_y + y_dist, width=bus_width,
                       country=country,
                       graphic_type=BusGraphicType.Connectivity)

        bus3 = dev.Bus(name=f"BayBus3_{i}", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=offset_x + i * x_dist - x_dist * 0.25,
                       ypos=offset_y + y_dist * 2, width=bus_width,
                       country=country,
                       graphic_type=BusGraphicType.Connectivity)

        dis1 = dev.Switch(name=f"Dis1_{i}", bus_from=bus1, bus_to=bus2, graphic_type=SwitchGraphicType.Disconnector)
        cb1 = dev.Switch(name=f"CB_{i}", bus_from=bus2, bus_to=bus3, graphic_type=SwitchGraphicType.CircuitBreaker)
        dis2 = dev.Switch(name=f"Dis2_{i}", bus_from=bar1, bus_to=bus3, graphic_type=SwitchGraphicType.Disconnector)
        dis3 = dev.Switch(name=f"Dis3_{i}", bus_from=bar2, bus_to=bus3, graphic_type=SwitchGraphicType.Disconnector)
        dis4 = dev.Switch(name=f"Dis4_{i}", bus_from=bus1, bus_to=transfer_bar,
                          graphic_type=SwitchGraphicType.Disconnector)

        grid.add_bus(bus1)
        all_buses.append(bus1)
        l_x_pos.append(bus1.x)
        l_y_pos.append(bus1.y)

        grid.add_bus(bus2)
        all_buses.append(bus2)
        l_x_pos.append(bus2.x)
        l_y_pos.append(bus2.y)

        grid.add_bus(bus3)
        all_buses.append(bus3)
        l_x_pos.append(bus3.x)
        l_y_pos.append(bus3.y)

        grid.add_switch(dis1)
        grid.add_switch(cb1)
        grid.add_switch(dis2)
        grid.add_switch(dis3)
        grid.add_switch(dis4)

        conn_buses.append(bus1)

    # coupling
    bus1 = dev.Bus(name=f"{name}_coupling_bar1", substation=substation, Vnom=v_nom, voltage_level=vl,
                   xpos=offset_x + n_bays * x_dist + x_dist * 0.5,
                   ypos=offset_y + y_dist * 3.6,
                   width=bus_width,
                   country=country,
                   graphic_type=BusGraphicType.Connectivity)

    bus2 = dev.Bus(name=f"{name}_coupling_bar2", substation=substation, Vnom=v_nom, voltage_level=vl,
                   xpos=offset_x + n_bays * x_dist + x_dist * 0.5,
                   ypos=offset_y + y_dist * 4.6,
                   width=bus_width,
                   country=country,
                   graphic_type=BusGraphicType.Connectivity)

    dis1 = dev.Switch(name="Dis_bar1", bus_from=bus1, bus_to=bar1, graphic_type=SwitchGraphicType.Disconnector)
    dis2 = dev.Switch(name="Dis_bar2", bus_from=bus1, bus_to=bar2, graphic_type=SwitchGraphicType.Disconnector)
    cb1 = dev.Switch(name="CB_coupling", bus_from=bus1, bus_to=bus2, graphic_type=SwitchGraphicType.CircuitBreaker)
    dis3 = dev.Switch(name="Dis_coupling", bus_from=bus2, bus_to=transfer_bar,
                      graphic_type=SwitchGraphicType.Disconnector)

    grid.add_bus(bus1)
    all_buses.append(bus1)
    l_x_pos.append(bus1.x)
    l_y_pos.append(bus1.y)

    grid.add_bus(bus2)
    all_buses.append(bus2)
    l_x_pos.append(bus2.x)
    l_y_pos.append(bus2.y)

    grid.add_switch(dis1)
    grid.add_switch(dis2)
    grid.add_switch(cb1)
    grid.add_switch(dis3)

    offset_total_x = max(l_x_pos, default=0) + x_dist
    offset_total_y = max(l_y_pos, default=0) + y_dist

    # connect the bar dots if that's the case
    if bar_by_segments:
        if len(bar1_buses) > 1:
            connect_bar_segments(grid=grid, bar_buses=bar1_buses, name=name)

        if len(bar2_buses) > 1:
            connect_bar_segments(grid=grid, bar_buses=bar2_buses, name=name)

        if len(bar_transfer_buses) > 1:
            connect_bar_segments(grid=grid, bar_buses=bar_transfer_buses, name=name)

    return vl, conn_buses, all_buses, offset_total_x, offset_total_y


def create_double_bar_with_transference_bar(
        name: str,
        grid: MultiCircuit,
        n_bays: int,
        v_nom: float,
        substation: dev.Substation,
        country: dev.Country = None,
        bar_by_segments: bool = False,
        offset_x=0,
        offset_y=0
) -> Tuple[dev.VoltageLevel, List[dev.Bus], List[dev.Bus], float, float]:
    """
    Create a double-bar with transference bar voltage level
    :param name: Voltage level name
    :param grid: MultiCircuit to do the mods
    :param n_bays: number of bays (positions)
    :param v_nom: Nominal voltage
    :param substation: Substation where it belongs
    :param country: Country (Optional)
    :param bar_by_segments: Split the bar into segments
    :param offset_x: x ofsset (px)
    :param offset_y: y ofsset (px)
    :return: Voltage level object, list of busses where connections are allowed, offset x, offset y
    """

    vl = dev.VoltageLevel(name=name, substation=substation, Vnom=v_nom)
    grid.add_voltage_level(vl)

    bus_width = 120
    x_dist = bus_width * 2
    y_dist = bus_width * 1.5
    l_x_pos = []
    l_y_pos = []
    conn_buses: List[dev.Bus] = list()
    all_buses: List[dev.Bus] = list()
    bar1_buses: List[dev.Bus] = list()
    bar2_buses: List[dev.Bus] = list()
    bar_transfer_buses: List[dev.Bus] = list()

    if not bar_by_segments:
        bar1 = dev.Bus(name=f"{name} bar1", substation=substation, Vnom=v_nom, voltage_level=vl,
                       width=(n_bays + 1) * bus_width + bus_width * 2 + (x_dist - bus_width) * (n_bays - 1),
                       xpos=offset_x - bus_width, ypos=offset_y + y_dist * 2, country=country,
                       graphic_type=BusGraphicType.BusBar)
        grid.add_bus(bar1)
        all_buses.append(bar1)
        l_x_pos.append(bar1.x)
        l_y_pos.append(bar1.y)

        bar2 = dev.Bus(name=f"{name} bar2", substation=substation, Vnom=v_nom, voltage_level=vl,
                       width=(n_bays + 1) * bus_width + bus_width * 2 + (x_dist - bus_width) * (n_bays - 1),
                       xpos=offset_x - bus_width, ypos=offset_y + y_dist * 3, country=country,
                       graphic_type=BusGraphicType.BusBar)
        grid.add_bus(bar2)
        all_buses.append(bar2)
        l_x_pos.append(bar2.x)
        l_y_pos.append(bar2.y)

        transfer_bar = dev.Bus(name=f"{name} transfer bar", substation=substation, Vnom=v_nom, voltage_level=vl,
                               width=(n_bays + 1) * bus_width + bus_width * 2 + (x_dist - bus_width) * (n_bays - 1),
                               xpos=offset_x - bus_width, ypos=offset_y + y_dist * 4, country=country,
                               graphic_type=BusGraphicType.BusBar)
        grid.add_bus(transfer_bar)
        all_buses.append(transfer_bar)
        l_x_pos.append(transfer_bar.x)
        l_y_pos.append(transfer_bar.y)
    else:
        # bar1 & 2 will be assigned inside the loop
        bar1: dev.Bus | None = None
        bar2: dev.Bus | None = None
        transfer_bar: dev.Bus | None = None

    for i in range(n_bays):

        if bar_by_segments:
            bar1 = dev.Bus(name=f"{name} bar1 ({i + 1})",
                           substation=substation,
                           Vnom=v_nom,
                           voltage_level=vl,
                           width=50,
                           xpos=offset_x - bus_width,
                           ypos=offset_y + y_dist,
                           country=country,
                           graphic_type=BusGraphicType.Connectivity)
            grid.add_bus(bar1)
            all_buses.append(bar1)
            l_x_pos.append(bar1.x)
            l_y_pos.append(bar1.y)
            bar1_buses.append(bar1)

            bar2 = dev.Bus(name=f"{name} bar2 ({i + 1})",
                           substation=substation,
                           Vnom=v_nom,
                           voltage_level=vl,
                           width=50,
                           xpos=offset_x - bus_width,
                           ypos=offset_y + y_dist,
                           country=country,
                           graphic_type=BusGraphicType.Connectivity)
            grid.add_bus(bar2)
            all_buses.append(bar2)
            l_x_pos.append(bar2.x)
            l_y_pos.append(bar2.y)
            bar2_buses.append(bar2)

            bar_t = dev.Bus(name=f"{name} bar_t ({i + 1})",
                            substation=substation,
                            Vnom=v_nom,
                            voltage_level=vl,
                            width=50,
                            xpos=offset_x - bus_width,
                            ypos=offset_y + y_dist,
                            country=country,
                            graphic_type=BusGraphicType.Connectivity)
            grid.add_bus(bar_t)
            all_buses.append(bar_t)
            l_x_pos.append(bar_t.x)
            l_y_pos.append(bar_t.y)
            bar_transfer_buses.append(bar_t)
        else:
            # already assigned outside the loop
            pass

        bus1 = dev.Bus(name=f"{name}_bay_conn_{i}", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=offset_x + i * x_dist + x_dist * 0.1, ypos=offset_y, width=bus_width, country=country,
                       graphic_type=BusGraphicType.Connectivity)

        bus2 = dev.Bus(f"BayBus2_{i}", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=offset_x + i * x_dist - x_dist * 0.1, ypos=offset_y + y_dist, width=bus_width,
                       country=country,
                       graphic_type=BusGraphicType.Connectivity)

        cb1 = dev.Switch(name=f"CB_{i}", bus_from=bus1, bus_to=bus2, graphic_type=SwitchGraphicType.CircuitBreaker)
        dis1 = dev.Switch(name=f"Dis1_{i}", bus_from=bus2, bus_to=bar1, graphic_type=SwitchGraphicType.Disconnector)
        dis2 = dev.Switch(name=f"Dis2_{i}", bus_from=bus2, bus_to=bar2, graphic_type=SwitchGraphicType.Disconnector)
        dis3 = dev.Switch(name=f"Dis3_{i}", bus_from=bus1, bus_to=transfer_bar,
                          graphic_type=SwitchGraphicType.Disconnector)

        grid.add_bus(bus1)
        all_buses.append(bus1)
        l_x_pos.append(bus1.x)
        l_y_pos.append(bus1.y)

        grid.add_bus(bus2)
        all_buses.append(bus1)
        l_x_pos.append(bus2.x)
        l_y_pos.append(bus2.y)

        grid.add_switch(cb1)
        grid.add_switch(dis1)  # this disconnector must be included to respect the SE geometry
        grid.add_switch(dis2)  # this disconnector must be included to respect the SE geometry
        grid.add_switch(dis3)  # this disconnector must be included to respect the SE geometry

        conn_buses.append(bus1)

    # coupling
    bus1 = dev.Bus(f"{name}_coupling_bar1", substation=substation, Vnom=v_nom, voltage_level=vl,
                   xpos=offset_x + n_bays * x_dist + x_dist * 0.5,
                   ypos=offset_y + y_dist * 3.6,
                   width=bus_width,
                   country=country,
                   graphic_type=BusGraphicType.Connectivity)
    dis1 = dev.Switch(name="Dis_bar1", bus_from=bus1, bus_to=bar1, graphic_type=SwitchGraphicType.Disconnector)
    dis2 = dev.Switch(name="Dis_bar2", bus_from=bus1, bus_to=bar2, graphic_type=SwitchGraphicType.Disconnector)
    cb1 = dev.Switch(name="CB_coupling", bus_from=bus1, bus_to=transfer_bar,
                     graphic_type=SwitchGraphicType.CircuitBreaker)

    grid.add_bus(bus1)
    all_buses.append(bus1)
    l_x_pos.append(bus1.x)
    l_y_pos.append(bus1.y)

    grid.add_switch(dis1)  # this disconnector must be included to respect the SE geometry
    grid.add_switch(dis2)  # this disconnector must be included to respect the SE geometry
    grid.add_switch(cb1)

    offset_total_x = max(l_x_pos, default=0) + x_dist
    offset_total_y = max(l_y_pos, default=0) + y_dist

    # connect the bar dots if that's the case
    if bar_by_segments:
        if len(bar1_buses) > 1:
            connect_bar_segments(grid=grid, bar_buses=bar1_buses, name=name)

        if len(bar2_buses) > 1:
            connect_bar_segments(grid=grid, bar_buses=bar2_buses, name=name)

        if len(bar_transfer_buses) > 1:
            connect_bar_segments(grid=grid, bar_buses=bar_transfer_buses, name=name)

    return vl, conn_buses, all_buses, offset_total_x, offset_total_y
