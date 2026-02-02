# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import math
from typing import Tuple, List
import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import BusGraphicType, SwitchGraphicType


def create_ring_with_disconnectors(
        name: str,
        grid: MultiCircuit,
        n_bays: int,
        v_nom: float,
        substation: dev.Substation,
        country: dev.Country = None,
        offset_x=0,
        offset_y=0
) -> Tuple[dev.VoltageLevel, List[dev.Bus], List[dev.Bus], float, float]:
    """
    Create a ring voltage level
    :param name: Voltage level name
    :param grid: MultiCircuit to do the mods
    :param n_bays: number of bays (positions)
    :param v_nom: Nominal voltage
    :param substation: Substation where it belongs
    :param country: Country (Optional)
    :param offset_x: x ofsset (px)
    :param offset_y: y ofsset (px)
    :return: Voltage level object, list of busses where connections are allowed, offset x, offset y
    """

    vl = dev.VoltageLevel(name=name, substation=substation, Vnom=v_nom)
    grid.add_voltage_level(vl)

    bus_width = 80
    bus_height = 80
    x_dist = bus_width * 6
    y_dist = bus_width * 6
    l_x_pos: List[float] = list()
    l_y_pos: List[float] = list()
    conn_buses: List[dev.Bus] = list()
    all_buses: List[dev.Bus] = list()
    n_positions = max(n_bays, 3)

    radius = x_dist / (2 * math.sin(math.pi / n_positions))
    cx = offset_x + radius
    cy = offset_y + radius

    for n in range(n_positions):

        angle1 = 2 * math.pi * n / n_positions
        x1 = cx + radius * math.cos(angle1 + math.radians(25))
        y1 = cy + radius * math.sin(angle1 + math.radians(25))

        angle2 = 2 * math.pi * (n + 1) / n_positions
        x2 = cx + radius * math.cos(angle2 + math.radians(25))
        y2 = cy + radius * math.sin(angle2 + math.radians(25))

        x13, y13 = (x1 + (x2 - x1) / 3, y1 + (y2 - y1) / 3)
        x23, y23 = (x1 + 2 * (x2 - x1) / 3, y1 + 2 * (y2 - y1) / 3)

        bus1 = dev.Bus(f"{name}_position_{n}", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=x1, ypos=y1, width=bus_width, height=bus_height, country=country,
                       graphic_type=BusGraphicType.Connectivity)

        bus2 = dev.Bus(f"{name}_cb_{n}.1", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=x13, ypos=y13, width=bus_width, height=bus_height, country=country,
                       graphic_type=BusGraphicType.Connectivity)

        bus3 = dev.Bus(f"{name}_cb_{n}.2", substation=substation, Vnom=v_nom, voltage_level=vl,
                       xpos=x23, ypos=y23, width=bus_width, height=bus_height, country=country,
                       graphic_type=BusGraphicType.Connectivity)

        cb = dev.Switch(name=f"CB_{n}", bus_from=bus2, bus_to=bus3,
                        graphic_type=SwitchGraphicType.CircuitBreaker)

        dis1 = dev.Switch(name=f"dis_{n}.1", bus_from=bus1, bus_to=bus2,
                          graphic_type=SwitchGraphicType.Disconnector)

        if n == 0:
            first_bus = bus1
        elif n + 1 == n_positions:
            dis2 = dev.Switch(name=f"CB_{n}.2", bus_from=bus3, bus_to=first_bus,
                              graphic_type=SwitchGraphicType.Disconnector)

            grid.add_switch(dis2)

            dis2 = dev.Switch(name=f"dis_{n - 1}.2", bus_from=prev_bus, bus_to=bus1,
                              graphic_type=SwitchGraphicType.Disconnector)
            grid.add_switch(dis2)

        else:
            dis2 = dev.Switch(name=f"dis_{n}12", bus_from=prev_bus, bus_to=bus1,
                              graphic_type=SwitchGraphicType.Disconnector)
            grid.add_switch(dis2)

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

        grid.add_switch(cb)
        grid.add_switch(dis1)

        conn_buses.append(bus1)

        prev_bus = bus3

    offset_total_x = max(l_x_pos, default=0) + x_dist
    offset_total_y = max(l_y_pos, default=0) + y_dist

    return vl, conn_buses, all_buses, offset_total_x, offset_total_y


def create_ring(
        name: str,
        grid: MultiCircuit,
        n_bays: int,
        v_nom: float,
        substation: dev.Substation,
        country: dev.Country = None,
        offset_x=0,
        offset_y=0
) -> Tuple[dev.VoltageLevel, List[dev.Bus], List[dev.Bus], float, float]:
    """
    Create a ring voltage level
    :param name: Voltage level name
    :param grid: MultiCircuit to do the mods
    :param n_bays: number of bays (positions)
    :param v_nom: Nominal voltage
    :param substation: Substation where it belongs
    :param country: Country (Optional)
    :param offset_x: x ofsset (px)
    :param offset_y: y ofsset (px)
    :return: Voltage level object, list of busses where connections are allowed, offset x, offset y
    """

    vl = dev.VoltageLevel(name=name, substation=substation, Vnom=v_nom)
    grid.add_voltage_level(vl)

    bus_width = 80
    bus_height = 80
    x_dist = bus_width * 6
    y_dist = bus_width * 6
    l_x_pos = []
    l_y_pos = []
    conn_buses: List[dev.Bus] = list()
    all_buses: List[dev.Bus] = list()

    n_positions = max(n_bays, 3)

    radius = x_dist / (2 * math.sin(math.pi / n_positions))
    cx = offset_x + radius
    cy = offset_y + radius

    for n in range(n_positions):

        angle = 2 * math.pi * n / n_positions
        x = cx + radius * math.cos(angle + math.radians(25))
        y = cy + radius * math.sin(angle + math.radians(25))

        bus = dev.Bus(f"{name}_position_{n}", substation=substation, Vnom=v_nom, voltage_level=vl,
                      xpos=x, ypos=y, width=bus_width, height=bus_height, country=country,
                      graphic_type=BusGraphicType.Connectivity)
        if n == 0:
            first_bus = bus
        elif n + 1 == n_positions:
            cb = dev.Switch(name=f"CB_{n}", bus_from=bus, bus_to=first_bus,
                            graphic_type=SwitchGraphicType.CircuitBreaker)
            grid.add_switch(cb)

            cb = dev.Switch(name=f"CB_{n - 1}", bus_from=prev_bus, bus_to=bus,
                            graphic_type=SwitchGraphicType.CircuitBreaker)
            grid.add_switch(cb)
        else:
            cb = dev.Switch(name=f"CB_{n}", bus_from=prev_bus, bus_to=bus,
                            graphic_type=SwitchGraphicType.CircuitBreaker)
            grid.add_switch(cb)

        grid.add_bus(bus)
        all_buses.append(bus)
        l_x_pos.append(bus.x)
        l_y_pos.append(bus.y)

        conn_buses.append(bus)

        prev_bus = bus

    offset_total_x = max(l_x_pos, default=0) + x_dist
    offset_total_y = max(l_y_pos, default=0) + y_dist

    return vl, conn_buses, all_buses, offset_total_x, offset_total_y
