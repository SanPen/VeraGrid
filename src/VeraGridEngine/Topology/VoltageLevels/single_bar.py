# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Tuple, List
import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import BusGraphicType, SwitchGraphicType


def connect_bar_segments(grid: MultiCircuit, bar_buses: List[dev.Bus], name: str):
    """

    :param grid:
    :param bar_buses:
    :param name:
    :return:
    """
    # connect the bar dots if that's the case
    for i in range(len(bar_buses) - 1):
        ln = dev.Line(
            name=f"{name}_section_{i}",
            bus_from=bar_buses[i],
            bus_to=bar_buses[i + 1],
        )
        grid.add_line(ln)


def create_single_bar_with_disconnectors(
        name: str,
        grid: MultiCircuit,
        n_bays: int,
        v_nom: float,
        substation: dev.Substation,
        country: dev.Country = None,
        bar_by_segments: bool = False,
        offset_x: float = 0.0,
        offset_y: float = 0.0
) -> Tuple[dev.VoltageLevel, List[dev.Bus], List[dev.Bus], float, float]:
    """
    Create a single-bar voltage level without disconnectors
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
    l_x_pos: List[float] = list()
    l_y_pos: List[float] = list()
    conn_buses: List[dev.Bus] = list()
    all_buses: List[dev.Bus] = list()
    bar_buses: List[dev.Bus] = list()

    if not bar_by_segments:
        width = n_bays * bus_width + bus_width * 2 + (x_dist - bus_width) * (n_bays - 1)
        bar = dev.Bus(name=f"{name} bar", substation=substation, Vnom=v_nom, voltage_level=vl, width=width,
                      xpos=offset_x - bus_width, ypos=offset_y + y_dist * 3, country=country,
                      graphic_type=BusGraphicType.BusBar)
        grid.add_bus(bar)
        all_buses.append(bar)
        l_x_pos.append(bar.x)
        l_y_pos.append(bar.y)
    else:
        # bar will be assigned inside
        bar: dev.Bus | None = None

    for i in range(n_bays):

        if bar_by_segments:
            bar = dev.Bus(name=f"{name} bar ({i + 1})",
                          substation=substation,
                          Vnom=v_nom,
                          voltage_level=vl,
                          width=50,
                          xpos=offset_x - bus_width,
                          ypos=offset_y + y_dist,
                          country=country,
                          graphic_type=BusGraphicType.Connectivity)
            grid.add_bus(bar)
            all_buses.append(bar)
            l_x_pos.append(bar.x)
            l_y_pos.append(bar.y)
            bar_buses.append(bar)
        else:
            # bar was assigned before the loop
            pass

        bus1 = dev.Bus(name=f"{name}_bay_conn_{i}",
                       substation=substation,
                       Vnom=v_nom,
                       voltage_level=vl,
                       xpos=offset_x + i * x_dist,
                       ypos=offset_y + 0,
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

        dis1 = dev.Switch(name=f"Dis1_{i}",
                          bus_from=bus1,
                          bus_to=bus2,
                          graphic_type=SwitchGraphicType.Disconnector)

        cb1 = dev.Switch(name=f"CB_{i}",
                         bus_from=bus2,
                         bus_to=bus3,
                         graphic_type=SwitchGraphicType.CircuitBreaker)

        dis2 = dev.Switch(name=f"Dis2_{i}",
                          bus_from=bar,
                          bus_to=bus3,
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

        conn_buses.append(bus1)

    # connect the bar dots if that's the case
    if bar_by_segments and len(bar_buses) > 1:
        connect_bar_segments(grid=grid, bar_buses=bar_buses, name=name)

    offset_total_x = max(l_x_pos, default=0) + x_dist
    offset_total_y = max(l_y_pos, default=0) + y_dist

    return vl, conn_buses, all_buses, offset_total_x, offset_total_y


def create_single_bar(
        name: str,
        grid: MultiCircuit,
        n_bays: int,
        v_nom: float,
        substation: dev.Substation,
        country: dev.Country = None,
        bar_by_segments: bool = False,
        offset_x: float = 0.0,
        offset_y: float = 0.0
) -> Tuple[dev.VoltageLevel, List[dev.Bus], List[dev.Bus], float, float]:
    """
    Create a single-bar voltage level with disconnectors
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
    l_x_pos: List[int] = list()
    l_y_pos: List[int] = list()
    conn_buses: List[dev.Bus] = list()
    all_buses: List[dev.Bus] = list()
    bar_buses: List[dev.Bus] = list()

    if not bar_by_segments:
        width = n_bays * bus_width + bus_width * 2 + (x_dist - bus_width) * (n_bays - 1)
        bar = dev.Bus(name=f"{name} bar",
                      substation=substation,
                      Vnom=v_nom,
                      voltage_level=vl,
                      width=width,
                      xpos=offset_x - bus_width,
                      ypos=offset_y + y_dist,
                      country=country,
                      graphic_type=BusGraphicType.BusBar)
        grid.add_bus(bar)
        all_buses.append(bar)
        l_x_pos.append(bar.x)
        l_y_pos.append(bar.y)
    else:
        # bar will be assigned inside the loop
        bar: dev.Bus | None = None

    for i in range(n_bays):

        if bar_by_segments:
            bar = dev.Bus(name=f"{name} bar ({i + 1})",
                          substation=substation,
                          Vnom=v_nom,
                          voltage_level=vl,
                          width=50,
                          xpos=offset_x - bus_width,
                          ypos=offset_y + y_dist,
                          country=country,
                          graphic_type=BusGraphicType.Connectivity)
            grid.add_bus(bar)
            all_buses.append(bar)
            l_x_pos.append(bar.x)
            l_y_pos.append(bar.y)
            bar_buses.append(bar)
        else:
            # bar was assigned before the loop
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

        cb1 = dev.Switch(name=f"CB_{i}",
                         bus_from=bus1,
                         bus_to=bar,
                         graphic_type=SwitchGraphicType.CircuitBreaker)

        grid.add_bus(bus1)
        all_buses.append(bus1)
        l_x_pos.append(bus1.x)
        l_y_pos.append(bus1.y)

        grid.add_switch(cb1)

        conn_buses.append(bus1)

    # connect the bar dots if that's the case
    if bar_by_segments and len(bar_buses) > 1:
        connect_bar_segments(grid=grid, bar_buses=bar_buses, name=name)

    offset_total_x = max(l_x_pos, default=0) + x_dist
    offset_total_y = max(l_y_pos, default=0) + y_dist

    return vl, conn_buses, all_buses, offset_total_x, offset_total_y


def create_single_bar_with_bypass_with_disconnectors(
        name: str,
        grid: MultiCircuit,
        n_bays: int,
        v_nom: float,
        substation: dev.Substation,
        country: dev.Country = None,
        bar_by_segments: bool = False,
        offset_x: int = 0,
        offset_y: int = 0
) -> Tuple[dev.VoltageLevel, List[dev.Bus], List[dev.Bus], float, float]:
    """
    Create a single-bar with by-pass voltage level
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
    bar_buses: List[dev.Bus] = list()

    if not bar_by_segments:
        width = n_bays * bus_width + bus_width * 2 + (x_dist - bus_width) * (n_bays - 1)
        bar = dev.Bus(f"{name} bar", substation=substation, Vnom=v_nom, voltage_level=vl,
                      width=width,
                      xpos=offset_x - bus_width, ypos=offset_y + y_dist * 3, country=country,
                      graphic_type=BusGraphicType.BusBar)
        grid.add_bus(bar)
        all_buses.append(bar)
        l_x_pos.append(bar.x)
        l_y_pos.append(bar.y)
    else:
        # bar will be assigned inside
        bar: dev.Bus | None = None

    for i in range(n_bays):

        if bar_by_segments:
            # this is the dot in the bar
            bar = dev.Bus(name=f"{name} bar ({i + 1})",
                          substation=substation,
                          Vnom=v_nom,
                          voltage_level=vl,
                          width=50,
                          xpos=offset_x - bus_width,
                          ypos=offset_y + y_dist,
                          country=country,
                          graphic_type=BusGraphicType.Connectivity)
            grid.add_bus(bar)
            all_buses.append(bar)
            l_x_pos.append(bar.x)
            l_y_pos.append(bar.y)
            bar_buses.append(bar)
        else:
            # bar was assigned before the loop
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

        bus2 = dev.Bus(name=f"BayBus2_{i}",
                       substation=substation,
                       Vnom=v_nom,
                       voltage_level=vl,
                       xpos=offset_x + i * x_dist,
                       ypos=offset_y + y_dist,
                       width=bus_width,
                       country=country,
                       graphic_type=BusGraphicType.Connectivity)

        bus3 = dev.Bus(name=f"BayBus3_{i}",
                       substation=substation,
                       Vnom=v_nom,
                       voltage_level=vl,
                       xpos=offset_x + i * x_dist,
                       ypos=offset_y + y_dist * 2,
                       width=bus_width,
                       country=country,
                       graphic_type=BusGraphicType.Connectivity)

        dis1 = dev.Switch(name=f"Dis1_{i}",
                          bus_from=bus1,
                          bus_to=bus2,
                          graphic_type=SwitchGraphicType.Disconnector)

        cb1 = dev.Switch(name=f"CB_{i}",
                         bus_from=bus2,
                         bus_to=bus3,
                         graphic_type=SwitchGraphicType.CircuitBreaker)

        dis2 = dev.Switch(name=f"Dis2_{i}",
                          bus_from=bus3,
                          bus_to=bar,
                          graphic_type=SwitchGraphicType.Disconnector)

        bypass_dis = dev.Switch(name=f"Bypass_Dis_{i}",
                                bus_from=bus1,
                                bus_to=bar,
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
        grid.add_switch(bypass_dis)

        conn_buses.append(bus1)

    # connect the bar dots if that's the case
    if bar_by_segments and len(bar_buses) > 1:
        connect_bar_segments(grid=grid, bar_buses=bar_buses, name=name)

    offset_total_x = max(l_x_pos, default=0) + x_dist
    offset_total_y = max(l_y_pos, default=0) + y_dist

    return vl, conn_buses, all_buses, offset_total_x, offset_total_y


def create_single_bar_with_bypass(
        name: str,
        grid: MultiCircuit,
        n_bays: int,
        v_nom: float,
        substation: dev.Substation,
        country: dev.Country = None,
        bar_by_segments: bool = False,
        offset_x: int = 0,
        offset_y: int = 0
) -> Tuple[dev.VoltageLevel, List[dev.Bus], List[dev.Bus], float, float]:
    """
    Create a single-bar with by-pass voltage level
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
    bar_buses: List[dev.Bus] = list()

    if not bar_by_segments:
        width = n_bays * bus_width + bus_width * 2 + (x_dist - bus_width) * (n_bays - 1)
        bar = dev.Bus(name=f"{name} bar",
                      substation=substation, Vnom=v_nom, voltage_level=vl,
                      width=width,
                      xpos=offset_x - bus_width,
                      ypos=offset_y + y_dist * 1,
                      country=country,
                      graphic_type=BusGraphicType.BusBar)
        grid.add_bus(bar)
        l_x_pos.append(bar.x)
        l_y_pos.append(bar.y)
    else:
        # bar will be assigned inside the loop
        bar: dev.Bus | None = None

    for i in range(n_bays):

        if bar_by_segments:
            bar = dev.Bus(name=f"{name} bar ({i + 1})",
                          substation=substation,
                          Vnom=v_nom,
                          voltage_level=vl,
                          width=50,
                          xpos=offset_x - bus_width,
                          ypos=offset_y + y_dist,
                          country=country,
                          graphic_type=BusGraphicType.Connectivity)
            grid.add_bus(bar)
            all_buses.append(bar)
            l_x_pos.append(bar.x)
            l_y_pos.append(bar.y)
            bar_buses.append(bar)
        else:
            # bar was assigned before the loop
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

        cb1 = dev.Switch(name=f"CB_{i}",
                         bus_from=bus1,
                         bus_to=bar,
                         graphic_type=SwitchGraphicType.CircuitBreaker)

        bypass_dis = dev.Switch(name=f"Bypass_Dis_{i}",
                                bus_from=bus1,
                                bus_to=bar,
                                graphic_type=SwitchGraphicType.Disconnector)

        grid.add_bus(bus1)
        all_buses.append(bus1)
        l_x_pos.append(bus1.x)
        l_y_pos.append(bus1.y)

        grid.add_switch(cb1)
        grid.add_switch(bypass_dis)

        conn_buses.append(bus1)

    # connect the bar dots if that's the case
    if bar_by_segments and len(bar_buses) > 1:
        connect_bar_segments(grid=grid, bar_buses=bar_buses, name=name)

    offset_total_x = max(l_x_pos, default=0) + x_dist
    offset_total_y = max(l_y_pos, default=0) + y_dist

    return vl, conn_buses, all_buses, offset_total_x, offset_total_y


def create_single_bar_with_splitter_with_disconnectors(
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
    Create a single-bar with splitter breaker voltage level
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

    vl: dev.VoltageLevel = dev.VoltageLevel(name=name, substation=substation, Vnom=v_nom)
    grid.add_voltage_level(vl)

    bus_width = 120
    x_dist = bus_width * 2
    y_dist = bus_width * 1.5
    bar_2_x_offset = bus_width * 1.2
    bar_2_y_offset = bus_width * 1.2
    l_x_pos: List[float] = list()
    l_y_pos: List[float] = list()
    conn_buses: List[dev.Bus] = list()
    all_buses: List[dev.Bus] = list()
    bar1_buses: List[dev.Bus] = list()
    bar2_buses: List[dev.Bus] = list()

    n_bays_bar_1 = n_bays // 2
    n_bays_bar_2 = n_bays - n_bays_bar_1

    width_bar_1 = n_bays_bar_1 * bus_width + bus_width * 2 + (x_dist - bus_width) * (n_bays_bar_1 - 1)
    width_bar_2 = n_bays_bar_2 * bus_width + bus_width * 2 + (x_dist - bus_width) * (n_bays_bar_2 - 1)

    if not bar_by_segments:
        bar1 = dev.Bus(name=f"{name} bar 1", substation=substation, Vnom=v_nom, voltage_level=vl,
                       width=width_bar_1, xpos=offset_x - bus_width, ypos=offset_y + y_dist * 3, country=country,
                       graphic_type=BusGraphicType.BusBar)
        grid.add_bus(bar1)
        all_buses.append(bar1)
        l_x_pos.append(bar1.x)
        l_y_pos.append(bar1.y)
        bar1_buses.append(bar1)

        bar2 = dev.Bus(name=f"{name} bar 2", substation=substation, Vnom=v_nom, voltage_level=vl,
                       width=width_bar_2, xpos=offset_x + width_bar_1 + bar_2_x_offset,
                       ypos=offset_y + y_dist * 3 + bar_2_y_offset,
                       country=country, graphic_type=BusGraphicType.BusBar)
        grid.add_bus(bar2)
        all_buses.append(bar1)
        l_x_pos.append(bar2.x)
        l_y_pos.append(bar2.y)
        bar2_buses.append(bar2)

    else:
        # bar will be assigned inside
        bar1: dev.Bus | None = None
        bar2: dev.Bus | None = None

    for i in range(n_bays):

        if i < n_bays_bar_1:

            if bar_by_segments:
                bar = dev.Bus(name=f"{name} bar1 ({i + 1})",
                              substation=substation,
                              Vnom=v_nom,
                              voltage_level=vl,
                              width=50,
                              xpos=offset_x - bus_width,
                              ypos=offset_y + y_dist,
                              country=country,
                              graphic_type=BusGraphicType.Connectivity)
                grid.add_bus(bar)
                all_buses.append(bar)
                l_x_pos.append(bar.x)
                l_y_pos.append(bar.y)
                bar1_buses.append(bar)
            else:
                bar = bar1
                x_offset = 0
                y_offset = 0

        else:
            if bar_by_segments:
                bar = dev.Bus(name=f"{name} bar2 ({i + 1})",
                              substation=substation,
                              Vnom=v_nom,
                              voltage_level=vl,
                              width=50,
                              xpos=offset_x - bus_width,
                              ypos=offset_y + y_dist,
                              country=country,
                              graphic_type=BusGraphicType.Connectivity)
                grid.add_bus(bar)
                all_buses.append(bar)
                l_x_pos.append(bar.x)
                l_y_pos.append(bar.y)
                bar2_buses.append(bar)
            else:
                bar = bar2
                x_offset = bar_2_x_offset + 2 * bus_width
                y_offset = bar_2_y_offset

        bus1 = dev.Bus(f"{name}_bay_conn_{i}", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=offset_x + i * x_dist + x_offset, ypos=offset_y + y_offset, width=bus_width,
                       country=country,
                       graphic_type=BusGraphicType.Connectivity)
        bus2 = dev.Bus(f"LineBus2_{i}", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=offset_x + i * x_dist + x_offset, ypos=offset_y + y_dist + y_offset, width=bus_width,
                       country=country,
                       graphic_type=BusGraphicType.Connectivity)
        bus3 = dev.Bus(f"LineBus3_{i}", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=offset_x + i * x_dist + x_offset, ypos=offset_y + y_dist * 2 + y_offset,
                       width=bus_width, country=country,
                       graphic_type=BusGraphicType.Connectivity)
        dis1 = dev.Switch(name=f"Dis1_{i}", bus_from=bus1, bus_to=bus2, graphic_type=SwitchGraphicType.Disconnector)
        cb1 = dev.Switch(name=f"CB_{i}", bus_from=bus2, bus_to=bus3, graphic_type=SwitchGraphicType.CircuitBreaker)
        dis2 = dev.Switch(name=f"Dis2_{i}", bus_from=bar, bus_to=bus3, graphic_type=SwitchGraphicType.Disconnector)

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

        conn_buses.append(bus1)

    if bar_by_segments:
        if len(bar1_buses) > 1:
            connect_bar_segments(grid=grid, bar_buses=bar1_buses, name=name)
        if len(bar2_buses) > 1:
            connect_bar_segments(grid=grid, bar_buses=bar2_buses, name=name)
    else:
        # add the coupling switch
        cb_bars = dev.Switch(name=f"CB_bars",
                             bus_from=bar1,
                             bus_to=bar2,
                             graphic_type=SwitchGraphicType.CircuitBreaker)
        grid.add_switch(cb_bars)

    offset_total_x = max(l_x_pos, default=0) + x_dist
    offset_total_y = max(l_y_pos, default=0) + y_dist

    return vl, conn_buses, all_buses, offset_total_x, offset_total_y


def create_single_bar_with_splitter(
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
    Create a single-bar with splitter breaker voltage level
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

    vl: dev.VoltageLevel = dev.VoltageLevel(name=name, substation=substation, Vnom=v_nom)
    grid.add_voltage_level(vl)

    bus_width = 120
    x_dist = bus_width * 2
    y_dist = bus_width * 1.5
    bar_2_x_offset = bus_width * 1.2
    bar_2_y_offset = bus_width * 1.2
    l_x_pos: List[float] = list()
    l_y_pos: List[float] = list()
    conn_buses: List[dev.Bus] = list()
    all_buses: List[dev.Bus] = list()
    bar1_buses: List[dev.Bus] = list()
    bar2_buses: List[dev.Bus] = list()

    n_bays_bar_1 = n_bays // 2
    n_bays_bar_2 = n_bays - n_bays_bar_1

    width_bar_1 = n_bays_bar_1 * bus_width + bus_width * 2 + (x_dist - bus_width) * (n_bays_bar_1 - 1)
    width_bar_2 = n_bays_bar_2 * bus_width + bus_width * 2 + (x_dist - bus_width) * (n_bays_bar_2 - 1)

    bar1 = dev.Bus(f"{name} bar 1", substation=substation, Vnom=v_nom, voltage_level=vl,
                   width=width_bar_1, xpos=offset_x - bus_width, ypos=offset_y + y_dist * 1, country=country,
                   graphic_type=BusGraphicType.BusBar)
    grid.add_bus(bar1)
    all_buses.append(bar1)
    l_x_pos.append(bar1.x)
    l_y_pos.append(bar1.y)

    bar2 = dev.Bus(f"{name} bar 2", substation=substation, Vnom=v_nom, voltage_level=vl,
                   width=width_bar_2, xpos=offset_x + width_bar_1 + bar_2_x_offset,
                   ypos=offset_y + y_dist * 1 + bar_2_y_offset,
                   country=country, graphic_type=BusGraphicType.BusBar)
    grid.add_bus(bar2)
    l_x_pos.append(bar2.x)
    l_y_pos.append(bar2.y)

    for i in range(n_bays):
        if i < n_bays_bar_1:
            bar = bar1
            x_offset = 0
            y_offset = 0
        else:
            bar = bar2
            x_offset = bar_2_x_offset + 2 * bus_width
            y_offset = bar_2_y_offset

        bus1 = dev.Bus(f"{name}_bay_conn_{i}", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=offset_x + i * x_dist + x_offset, ypos=offset_y + y_dist * 0 + y_offset,
                       width=bus_width, country=country,
                       graphic_type=BusGraphicType.Connectivity)
        cb1 = dev.Switch(name=f"CB_{i}", bus_from=bar, bus_to=bus1, graphic_type=SwitchGraphicType.CircuitBreaker)

        grid.add_bus(bus1)
        all_buses.append(bus1)
        l_x_pos.append(bus1.x)
        l_y_pos.append(bus1.y)

        grid.add_switch(cb1)

        conn_buses.append(bus1)

    if bar_by_segments:
        if len(bar1_buses) > 1:
            connect_bar_segments(grid=grid, bar_buses=bar1_buses, name=name)
        if len(bar2_buses) > 1:
            connect_bar_segments(grid=grid, bar_buses=bar2_buses, name=name)
    else:
        # add the coupling switch
        cb_bars = dev.Switch(name=f"CB_bars",
                             bus_from=bar1,
                             bus_to=bar2,
                             graphic_type=SwitchGraphicType.CircuitBreaker)
        grid.add_switch(cb_bars)

    offset_total_x = max(l_x_pos, default=0) + x_dist
    offset_total_y = max(l_y_pos, default=0) + y_dist

    return vl, conn_buses, all_buses, offset_total_x, offset_total_y
