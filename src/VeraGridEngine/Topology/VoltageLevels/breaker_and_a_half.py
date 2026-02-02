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


def create_breaker_and_a_half_with_disconnectors(
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
    Create a breaker-and-a-half voltage level
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

    if not bar_by_segments:
        bar1 = dev.Bus(f"{name} bar1", substation=substation, Vnom=v_nom, voltage_level=vl,
                       width=(n_bays + n_bays % 2) * x_dist, xpos=offset_x - x_dist, ypos=offset_y, country=country,
                       graphic_type=BusGraphicType.BusBar)
        grid.add_bus(bar1)
        all_buses.append(bar1)
        l_x_pos.append(bar1.x)
        l_y_pos.append(bar1.y)

        bar2 = dev.Bus(f"{name} bar2", substation=substation, Vnom=v_nom, voltage_level=vl,
                       width=(n_bays + n_bays % 2) * x_dist, xpos=offset_x - x_dist, ypos=offset_y + y_dist * 9,
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

    for i in range(0, n_bays, 2):

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

        bus1 = dev.Bus(f"LineBus1_{i}", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=offset_x + i * x_dist - bus_width / 2, ypos=offset_y + y_dist, width=bus_width,
                       country=country,
                       graphic_type=BusGraphicType.Connectivity)
        bus2 = dev.Bus(f"LineBus2_{i}", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=offset_x + i * x_dist - bus_width / 2, ypos=offset_y + y_dist * 2, width=bus_width,
                       country=country,
                       graphic_type=BusGraphicType.Connectivity)
        bus3 = dev.Bus(f"LineBus3_{i}", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=offset_x + i * x_dist - bus_width / 2, ypos=offset_y + y_dist * 3, width=bus_width,
                       country=country,
                       graphic_type=BusGraphicType.Connectivity)
        bus_line_connection_1 = dev.Bus(f"{name}_bay_conn_{i}", substation=substation, Vnom=v_nom,
                                        voltage_level=vl,
                                        xpos=offset_x + (i - 1) * x_dist - bus_width / 2,
                                        ypos=offset_y + y_dist * 2.7, width=0,
                                        country=country,
                                        graphic_type=BusGraphicType.Connectivity)
        bus4 = dev.Bus(f"LineBus4_{i}", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=offset_x + i * x_dist - bus_width / 2, ypos=offset_y + y_dist * 4, width=bus_width,
                       country=country,
                       graphic_type=BusGraphicType.Connectivity)
        bus5 = dev.Bus(f"LineBus4_{i}", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=offset_x + i * x_dist - bus_width / 2, ypos=offset_y + y_dist * 5, width=bus_width,
                       country=country,
                       graphic_type=BusGraphicType.Connectivity)
        bus6 = dev.Bus(f"LineBus6_{i}", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=offset_x + i * x_dist - bus_width / 2, ypos=offset_y + y_dist * 6, width=bus_width,
                       country=country,
                       graphic_type=BusGraphicType.Connectivity)
        bus_line_connection_2 = dev.Bus(f"{name}_bay_conn_{i + 1}", substation=substation, Vnom=v_nom,
                                        voltage_level=vl,
                                        xpos=offset_x + (i - 1) * x_dist - bus_width / 2,
                                        ypos=offset_y + y_dist * 5.7, width=0,
                                        country=country,
                                        graphic_type=BusGraphicType.Connectivity)
        bus7 = dev.Bus(f"LineBus7_{i}", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=offset_x + i * x_dist - bus_width / 2, ypos=offset_y + y_dist * 7, width=bus_width,
                       country=country,
                       graphic_type=BusGraphicType.Connectivity)
        bus8 = dev.Bus(f"LineBus8_{i}", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=offset_x + i * x_dist - bus_width / 2, ypos=offset_y + y_dist * 8, width=bus_width,
                       country=country,
                       graphic_type=BusGraphicType.Connectivity)
        dis1 = dev.Switch(name=f"Dis1_{i}", bus_from=bar1, bus_to=bus1, graphic_type=SwitchGraphicType.Disconnector)
        cb1 = dev.Switch(name=f"SW1_{i}", bus_from=bus1, bus_to=bus2, graphic_type=SwitchGraphicType.CircuitBreaker)
        dis2 = dev.Switch(name=f"Dis2_{i}", bus_from=bus2, bus_to=bus3, graphic_type=SwitchGraphicType.Disconnector)
        dis3 = dev.Switch(name=f"Dis3_{i}", bus_from=bus3, bus_to=bus_line_connection_1,
                          graphic_type=SwitchGraphicType.CircuitBreaker)
        dis4 = dev.Switch(name=f"Dis4_{i}", bus_from=bus3, bus_to=bus4, graphic_type=SwitchGraphicType.Disconnector)
        cb2 = dev.Switch(name=f"SW2_{i}", bus_from=bus4, bus_to=bus5, graphic_type=SwitchGraphicType.Disconnector)
        dis5 = dev.Switch(name=f"Dis5_{i}", bus_from=bus5, bus_to=bus6, graphic_type=SwitchGraphicType.Disconnector)
        dis6 = dev.Switch(name=f"Dis6_{i}", bus_from=bus6, bus_to=bus_line_connection_2,
                          graphic_type=SwitchGraphicType.CircuitBreaker)
        dis7 = dev.Switch(name=f"Dis6_{i}", bus_from=bus6, bus_to=bus7, graphic_type=SwitchGraphicType.Disconnector)
        cb3 = dev.Switch(name=f"SW3_{i}", bus_from=bus7, bus_to=bus8, graphic_type=SwitchGraphicType.Disconnector)
        dis8 = dev.Switch(name=f"Dis6_{i}", bus_from=bus8, bus_to=bar2, graphic_type=SwitchGraphicType.Disconnector)

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

        grid.add_bus(bus4)
        all_buses.append(bus4)
        l_x_pos.append(bus4.x)
        l_y_pos.append(bus4.y)

        grid.add_bus(bus5)
        all_buses.append(bus5)
        l_x_pos.append(bus5.x)
        l_y_pos.append(bus5.y)

        grid.add_bus(bus6)
        all_buses.append(bus6)
        l_x_pos.append(bus6.x)
        l_y_pos.append(bus6.y)

        grid.add_bus(bus7)
        all_buses.append(bus7)
        l_x_pos.append(bus7.x)
        l_y_pos.append(bus7.y)

        grid.add_bus(bus8)
        all_buses.append(bus8)
        l_x_pos.append(bus8.x)
        l_y_pos.append(bus8.y)

        grid.add_bus(bus_line_connection_1)
        all_buses.append(bus_line_connection_1)
        l_x_pos.append(bus_line_connection_1.x)
        l_y_pos.append(bus_line_connection_1.y)

        grid.add_bus(bus_line_connection_2)
        all_buses.append(bus_line_connection_2)
        l_x_pos.append(bus_line_connection_2.x)
        l_y_pos.append(bus_line_connection_2.y)

        grid.add_switch(dis1)
        grid.add_switch(cb1)
        grid.add_switch(dis2)
        grid.add_switch(dis3)
        grid.add_switch(dis4)
        grid.add_switch(cb2)
        grid.add_switch(dis5)
        grid.add_switch(dis6)
        grid.add_switch(dis7)
        grid.add_switch(cb3)
        grid.add_switch(dis8)

        conn_buses.append(bus_line_connection_1)
        conn_buses.append(bus_line_connection_2)

    offset_total_x = max(l_x_pos, default=0) + x_dist
    offset_total_y = max(l_y_pos, default=0) + y_dist

    # connect the bar dots if that's the case
    if bar_by_segments:
        if len(bar1_buses) > 1:
            connect_bar_segments(grid=grid, bar_buses=bar1_buses, name=name)

        if len(bar2_buses) > 1:
            connect_bar_segments(grid=grid, bar_buses=bar2_buses, name=name)

    return vl, conn_buses, all_buses, offset_total_x, offset_total_y


def create_breaker_and_a_half(
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
    Create a breaker-and-a-half with disconnectors voltage level
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

    if not bar_by_segments:
        bar1 = dev.Bus(f"{name} bar1", substation=substation, Vnom=v_nom, voltage_level=vl,
                       width=(n_bays + n_bays % 2) * x_dist, xpos=offset_x - x_dist, ypos=offset_y, country=country,
                       graphic_type=BusGraphicType.BusBar)
        grid.add_bus(bar1)
        all_buses.append(bar1)
        l_x_pos.append(bar1.x)
        l_y_pos.append(bar1.y)

        bar2 = dev.Bus(f"{name} bar2", substation=substation, Vnom=v_nom, voltage_level=vl,
                       width=(n_bays + n_bays % 2) * x_dist, xpos=offset_x - x_dist, ypos=offset_y + y_dist * 3,
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

    for i in range(0, n_bays, 2):

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

        bus_line_connection_1 = dev.Bus(f"{name}_bay_conn_{i}", substation=substation, Vnom=v_nom,
                                        voltage_level=vl,
                                        xpos=offset_x + i * x_dist - bus_width / 2, ypos=offset_y + y_dist, width=0,
                                        country=country,
                                        graphic_type=BusGraphicType.Connectivity)
        bus_line_connection_2 = dev.Bus(f"{name}_bay_conn_{i + 1}", substation=substation, Vnom=v_nom,
                                        voltage_level=vl,
                                        xpos=offset_x + i * x_dist - bus_width / 2, ypos=offset_y + y_dist * 2,
                                        width=0,
                                        country=country,
                                        graphic_type=BusGraphicType.Connectivity)
        cb1 = dev.Switch(name=f"SW1_{i}", bus_from=bar1, bus_to=bus_line_connection_1,
                         graphic_type=SwitchGraphicType.CircuitBreaker)
        cb2 = dev.Switch(name=f"SW2_{i}", bus_from=bus_line_connection_1, bus_to=bus_line_connection_2,
                         graphic_type=SwitchGraphicType.CircuitBreaker)
        cb3 = dev.Switch(name=f"SW3_{i}", bus_from=bus_line_connection_2, bus_to=bar2,
                         graphic_type=SwitchGraphicType.CircuitBreaker)

        grid.add_bus(bus_line_connection_1)
        all_buses.append(bus_line_connection_1)
        l_x_pos.append(bus_line_connection_1.x)
        l_y_pos.append(bus_line_connection_1.y)

        grid.add_bus(bus_line_connection_2)
        all_buses.append(bus_line_connection_2)
        l_x_pos.append(bus_line_connection_2.x)
        l_y_pos.append(bus_line_connection_2.y)

        grid.add_switch(cb1)
        grid.add_switch(cb2)
        grid.add_switch(cb3)

        conn_buses.append(bus_line_connection_1)
        conn_buses.append(bus_line_connection_2)

    offset_total_x = max(l_x_pos, default=0) + x_dist
    offset_total_y = max(l_y_pos, default=0) + y_dist

    # connect the bar dots if that's the case
    if bar_by_segments:
        if len(bar1_buses) > 1:
            connect_bar_segments(grid=grid, bar_buses=bar1_buses, name=name)

        if len(bar2_buses) > 1:
            connect_bar_segments(grid=grid, bar_buses=bar2_buses, name=name)

    return vl, conn_buses, all_buses, offset_total_x, offset_total_y
