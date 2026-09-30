# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import math
from typing import Dict, List, Type, overload
import chardet
import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import Logger


@overload
def _parse_fixed(
    line: str,
    start: int,
    end: int,
    dtype: Type[int],
    implicit_decimals: int = 0,
) -> int:
    ...


@overload
def _parse_fixed(
    line: str,
    start: int,
    end: int,
    dtype: Type[float],
    implicit_decimals: int = 0,
) -> float:
    ...


@overload
def _parse_fixed(
    line: str,
    start: int,
    end: int,
    dtype: Type[str] = str,
    implicit_decimals: int = 0,
) -> str:
    ...


def _parse_fixed(
    line: str,
    start: int,
    end: int,
    dtype: Type[str] | Type[int] | Type[float] = str,
    implicit_decimals: int = 0,
) -> str | int | float:
    """
    Extract substring by fixed columns and convert to the desired dtype.
    :param line:
    :param start:
    :param end:
    :param dtype:
    :param implicit_decimals:
    :return:
    """

    raw = line[start - 1:end].strip()
    if raw == "":
        if dtype in (int, float):
            return 0.0 if dtype == float else 0
        return ""
    try:
        if dtype == float:
            val = float(raw)
            if implicit_decimals and "." not in raw:
                val /= 10 ** implicit_decimals
            return val
        elif dtype == int:
            return int(raw)
        else:
            return raw
    except Exception:
        return 0.0 if dtype == float else 0 if dtype == int else raw


# -------------------------------------------------------------------------
#  DBGT — VoltageGroup
# -------------------------------------------------------------------------

class PwfVoltageGroup:
    """
    PwfBus
    """
    __slots__ = (
        "char",
        "voltage",
    )

    def __init__(self):
        self.char: str = ""
        self.voltage: float = 1.0  # Voltage in kV

    def parse(self, line: str) -> None:
        """

        :param line:
        :return:
        """
        self.char = _parse_fixed(line, 1, 2, str)  # int --> str
        self.voltage = _parse_fixed(line, 4, 8, float, 2)

    def __repr__(self):
        return f"<VoltageGroup {self.char}: {self.voltage:.3f} kV>"


# -------------------------------------------------------------------------
#  DBAR — Bus
# -------------------------------------------------------------------------

class PwfBus:
    """
    PwfBus
    """
    __slots__ = (
        "number",
        "operation",
        "status",
        "type",
        "base_voltage_group",
        "voltage_limit_group",
        "name",
        "voltage",
        "angle",
        "pg",
        "qg",
        "qmin",
        "qmax",
        "controlled_bus",
        "pl",
        "ql",
        "area",
        "v_charge",
        "zone",
        "aggregators",
    )

    def __init__(self) -> None:
        """
        Constructor
        """
        self.number: int = 0
        self.operation: str = "A"
        self.status: str = "L"
        self.type: int = 1
        self.base_voltage_group: str = ""
        self.voltage_limit_group: str = ""
        self.name: str = ""
        self.voltage: float = 1.0
        self.angle: float = 0.0
        self.pg: float = 0.0
        self.qg: float = 0.0
        self.qmin: float = -9999.0
        self.qmax: float = 9999.0
        self.controlled_bus: int = 0
        self.pl: float = 0.0
        self.ql: float = 0.0
        self.area: int = 1
        self.v_charge: float = 1.0
        self.zone: int = 1
        self.aggregators: List[int] = [0] * 10

    def parse(self, line: str) -> None:
        """

        :param line:
        :return:
        """
        self.number = _parse_fixed(line, 1, 5, int)
        self.operation = _parse_fixed(line, 6, 6, str)
        self.status = _parse_fixed(line, 7, 7, str)
        self.type = _parse_fixed(line, 8, 8, int)
        self.base_voltage_group = _parse_fixed(line, 9, 10, str)
        self.voltage_limit_group = _parse_fixed(line, 23, 24, str)
        self.name = _parse_fixed(line, 11, 22, str)
        self.voltage = _parse_fixed(line, 25, 28, float, 3)
        self.angle = _parse_fixed(line, 29, 32, float, 2)
        self.pg = _parse_fixed(line, 33, 37, float, 0)
        self.qg = _parse_fixed(line, 38, 42, float, 0)
        self.qmin = _parse_fixed(line, 43, 47, float, 0)
        self.qmax = _parse_fixed(line, 48, 52, float, 0)
        self.controlled_bus = _parse_fixed(line, 53, 58, int)
        self.pl = _parse_fixed(line, 59, 63, float, 0)
        self.ql = _parse_fixed(line, 64, 68, float, 0)
        self.area = _parse_fixed(line, 74, 76, int)
        self.v_charge = _parse_fixed(line, 77, 80, float, 0)
        self.zone = _parse_fixed(line, 81, 81, int)

        # Aggregators (10x)
        agg_cols = [
            (82, 86), (87, 91), (92, 96), (97, 101), (102, 106),
            (107, 111), (112, 116), (117, 121), (122, 126), (127, 131)
        ]
        self.aggregators = [
            _parse_fixed(line, s, e, int) for (s, e) in agg_cols
        ]

        if self.controlled_bus == 0:
            self.controlled_bus = self.number

    def to_veragrid(
        self,
        vg_dict: Dict[str, "PwfVoltageGroup"],
        voltage_limits: Dict[str, "PwfVoltageLimitGroup"] | None,
        area_dict: Dict[int, dev.Area],
        zone_dict: Dict[int, dev.Zone],
    ) -> dev.Bus:
        """

        :param zone_dict:
        :param area_dict:
        :param voltage_limits:
        :param vg_dict:
        :return:
        """
        vg = vg_dict.get(self.base_voltage_group, None)
        Vnom = vg.voltage if vg else 1.0
        vmin: float = 0.9
        vmax: float = 1.1
        if voltage_limits is not None:
            limit_group = voltage_limits.get(self.voltage_limit_group, None)
            if limit_group is not None:
                vmin = limit_group.lower_bound
                vmax = limit_group.upper_bound

        bus = dev.Bus(
            name=self.name.strip() or f"Bus_{self.number}",
            Vnom=Vnom,
            vmin=vmin,
            vmax=vmax,
            active=self.status != "D",
            is_slack=self.type == 2,
            Vm0=self.voltage if self.voltage != 0.0 else 1.0,
            Va0=self.angle,
            area=area_dict.get(self.area, None),
            zone=zone_dict.get(self.zone, None),
        )
        return bus

    def __repr__(self):
        return f"<Bus {self.number} '{self.name}' Vm={self.voltage:.3f} Va={self.angle:.2f}°>"


# -------------------------------------------------------------------------
#  DLIN — Line
# -------------------------------------------------------------------------

class PwfLine:
    """
    PwfLine
    """
    __slots__ = (
        "from_bus",
        "to_bus",
        "circuit",
        "status",
        "owner",
        "r",
        "x",
        "b",
        "tap",
        "tap_min",
        "tap_max",
        "tap_lag",
        "controlled_bus",
        "normal_capacity",
        "emergency_capacity",
        "ntaps",
        "equipment_capacity",
        "aggregators",
    )

    def __init__(self) -> None:
        self.from_bus: int = 0
        self.to_bus: int = 0
        self.circuit: str = "1"
        self.status: str = "A"
        self.owner: str = ""
        self.r: float = 0.0
        self.x: float = 0.0
        self.b: float = 0.0
        self.tap: float = 1.0
        self.tap_min: float = 0.9
        self.tap_max: float = 1.1
        self.tap_lag: float = 0.0
        self.controlled_bus: int = 0
        self.normal_capacity: float = 9999.0
        self.emergency_capacity: float = 9999.0
        self.ntaps: int = 0
        self.equipment_capacity: float = 9999.0
        self.aggregators: List[int] = [0] * 10

    def parse(self, line: str) -> None:
        """

        :param line:
        :return:
        """
        self.from_bus: int = _parse_fixed(line, 1, 5, int)
        self.to_bus = _parse_fixed(line, 11, 15, int)
        self.circuit = _parse_fixed(line, 16, 17, str)
        self.status = _parse_fixed(line, 18, 18, str)
        self.owner = _parse_fixed(line, 19, 19, str)
        self.r = _parse_fixed(line, 21, 26, float, 0) / 100.0
        self.x = _parse_fixed(line, 27, 32, float, 0) / 100.0
        self.b = _parse_fixed(line, 33, 38, float, 0) / 100.0
        self.tap = _parse_fixed(line, 39, 43, float, 0)
        self.tap_min = _parse_fixed(line, 44, 48, float, 0)
        self.tap_max = _parse_fixed(line, 49, 53, float, 0)
        self.tap_lag = _parse_fixed(line, 54, 58, float, 0)
        self.controlled_bus = _parse_fixed(line, 59, 64, int)
        self.normal_capacity = _parse_fixed(line, 65, 68, float, 0)
        self.emergency_capacity = _parse_fixed(line, 69, 72, float, 0)
        self.ntaps = _parse_fixed(line, 73, 74, int)
        self.equipment_capacity = _parse_fixed(line, 75, 78, float, 0)

        agg_cols = [
            (79, 83), (84, 88), (89, 93), (94, 98), (99, 103),
            (104, 108), (109, 113), (114, 118), (119, 123), (124, 128)
        ]
        self.aggregators = [
            _parse_fixed(line, s, e, int) for (s, e) in agg_cols
        ]

        if self.controlled_bus == 0:
            self.controlled_bus = self.to_bus

    def to_veragrid(self, bus_dict: Dict[int, dev.Bus]) -> dev.Line:
        """

        :param bus_dict:
        :return:
        """
        from_bus = bus_dict.get(self.from_bus)
        to_bus = bus_dict.get(self.to_bus)

        name = f"L{self.from_bus}-{self.to_bus}_{self.circuit}"

        elm = dev.Line(
            name=name,
            bus_from=from_bus,
            bus_to=to_bus,
            r=self.r,
            x=self.x,
            b=self.b,
            rate=self.normal_capacity,
            active=self.status != 'D'
        )

        return elm

    def __repr__(self):
        return f"<Line {self.from_bus}-{self.to_bus} R={self.r:.4f} X={self.x:.4f}>"


# -------------------------------------------------------------------------
#  DGER — Generator
# -------------------------------------------------------------------------

class PwfGenerator:
    """
    PwfGenerator
    """
    __slots__ = (
        "number",
        "operation",
        "active_generation",
        "reactive_generation",
        "min_reactive_generation",
        "max_reactive_generation",
        "voltage",
        "min_active_gen",
        "max_active_gen",
        "participation_factor",
        "remote_participation_factor",
        "nominal_power_factor",
        "armature_service_factor",
        "rotor_service_factor",
        "charge_angle",
        "machine_reactance",
        "nominal_apparent_power",
    )

    def __init__(self) -> None:
        self.number: int = 0
        self.operation: str = "A"
        self.active_generation: float = 0.0
        self.reactive_generation: float = 0.0
        self.min_reactive_generation: float = -9999.0
        self.max_reactive_generation: float = 9999.0
        self.voltage: float = 1.0
        self.min_active_gen: float = 0.0
        self.max_active_gen: float = 9999.0
        self.participation_factor: float = 0.0
        self.remote_participation_factor: float = 100.0
        self.nominal_power_factor: float = 1.0
        self.armature_service_factor: float = 1.0
        self.rotor_service_factor: float = 1.0
        self.charge_angle: float = 0.0
        self.machine_reactance: float = 0.0
        self.nominal_apparent_power: float = 9999.0

    def parse(self, line: str) -> None:
        """

        :param line:
        :return:
        """
        self.number = _parse_fixed(line, 1, 5, int)
        self.operation = _parse_fixed(line, 7, 7, str)
        self.min_active_gen = _parse_fixed(line, 9, 14, float, 1)
        self.max_active_gen = _parse_fixed(line, 16, 21, float, 1)
        self.participation_factor = _parse_fixed(line, 23, 27, float, 2)
        self.remote_participation_factor = _parse_fixed(line, 29, 33, float, 2)
        self.nominal_power_factor = _parse_fixed(line, 35, 39, float, 2)
        self.armature_service_factor = _parse_fixed(line, 41, 44, float, 2)
        self.rotor_service_factor = _parse_fixed(line, 46, 49, float, 2)
        self.charge_angle = _parse_fixed(line, 51, 54, float, 2)
        self.machine_reactance = _parse_fixed(line, 56, 60, float, 2)
        self.nominal_apparent_power = _parse_fixed(line, 62, 66, float, 2)

    def to_veragrid(self, bus_dict: Dict[int, dev.Bus]) -> dev.Generator:
        """

        :param bus_dict:
        :return:
        """
        gen = dev.Generator()
        gen.name = f"G{self.number}"
        gen.Snom = float(self.nominal_apparent_power)
        gen.Pmin = float(self.min_active_gen)
        gen.Pmax = float(self.max_active_gen)
        gen.P = float(self.active_generation)
        gen.Q = float(self.reactive_generation)
        gen.Qmin = float(self.min_reactive_generation)
        gen.Qmax = float(self.max_reactive_generation)
        gen.Vset = float(self.voltage)
        if self.nominal_power_factor > 0.0:
            gen.Pf = float(self.nominal_power_factor)
        gen.active = (self.operation == 'A')
        return gen

    def __repr__(self):
        return f"<Generator {self.number} Operation={self.operation} Min/Max={self.min_active_gen}/{self.max_active_gen}>"


# -------------------------------------------------------------------------
#  DELO — Load
# -------------------------------------------------------------------------

class PwfLoad:
    """
    PwfLoad
    """
    __slots__ = (
        "number",
        "operation",
        "bus",
        "active_power",
        "reactive_power",
        "status",
    )

    def __init__(self):
        # Attributes
        self.number: int = 0
        self.operation: str = "A"  # Active by default
        self.bus: int = 0
        self.active_power: float = 0.0
        self.reactive_power: float = 0.0
        self.status: str = "L"  # Default load status: 'L' (Low)

    def parse(self, line: str) -> None:
        """

        :param line:
        :return:
        """
        self.number = _parse_fixed(line, 1, 4, int)
        self.operation = _parse_fixed(line, 5, 5, str)
        self.bus = _parse_fixed(line, 7, 10, int)
        self.active_power = _parse_fixed(line, 11, 16, float, 1)
        self.reactive_power = _parse_fixed(line, 17, 22, float, 1)
        self.status = _parse_fixed(line, 23, 23, str)

    def to_veragrid(self, bus_dict: Dict[int, dev.Bus]) -> dev.Load:
        """

        :param bus_dict:
        :return:
        """
        load = dev.Load()
        load.name = f"Load_{self.number}"
        load.P = float(self.active_power)
        load.Q = float(self.reactive_power)
        load.active = (self.operation == 'A')
        return load

    def __repr__(self):
        return f"<Load {self.number} Bus={self.bus} P={self.active_power} Q={self.reactive_power}>"


# -------------------------------------------------------------------------
#  DTRA — Transformer
# -------------------------------------------------------------------------

class PwfTransformer:
    """
    PwfTransformer
    """
    __slots__ = (
        "number",
        "from_bus",
        "to_bus",
        "r",
        "x",
        "tap",
        "shift",
        "tap_min",
        "tap_max",
        "controlled_bus",
        "active",
    )

    def __init__(self):
        self.number: int = 0
        self.from_bus: int = 0
        self.to_bus: int = 0
        self.r: float = 0.0
        self.x: float = 0.0
        self.tap: float = 1.0
        self.shift: float = 0.0
        self.tap_min: float = 0.9
        self.tap_max: float = 1.1
        self.controlled_bus: int = 0
        self.active: bool = True

    def parse(self, line: str) -> None:
        """

        :param line:
        :return:
        """
        self.number = _parse_fixed(line, 1, 5, int)
        self.from_bus = _parse_fixed(line, 6, 10, int)
        self.to_bus = _parse_fixed(line, 11, 15, int)
        self.r = _parse_fixed(line, 16, 20, float, 5)
        self.x = _parse_fixed(line, 21, 25, float, 5)
        self.tap = _parse_fixed(line, 26, 30, float, 3)
        self.shift = _parse_fixed(line, 31, 35, float, 3)

    def to_veragrid(self, bus_dict: Dict[int, dev.Bus]) -> dev.Transformer2W:
        """

        :param bus_dict:
        :return:
        """
        from_bus = bus_dict.get(self.from_bus)
        to_bus = bus_dict.get(self.to_bus)
        elm = dev.Transformer2W(
            name=f"T{self.number}_{self.from_bus}-{self.to_bus}",
            bus_from=from_bus,
            bus_to=to_bus,
            r=self.r,
            x=self.x,
            tap_module=self.tap,
            tap_phase=self.shift
        )
        elm.tap_module_min = self.tap_min
        elm.tap_module_max = self.tap_max
        elm.active = self.active and from_bus is not None and to_bus is not None
        return elm

    def __repr__(self):
        return f"<Transformer {self.number} {self.from_bus} -> {self.to_bus} Tap={self.tap:.3f}>"


# -------------------------------------------------------------------------
#  DSHL — Shunt
# -------------------------------------------------------------------------

class PwfShunt:
    """
    PwfShunt
    """
    __slots__ = (
        "number",
        "from_bus",
        "to_bus",
        "status_from",
        "status_to",
        "shunt_from",
        "shunt_to",
    )

    def __init__(self):
        self.number: int = 0
        self.from_bus: int = 0
        self.to_bus: int = 0
        self.status_from: str = 'L'
        self.status_to: str = 'L'
        self.shunt_from: float = 0.0
        self.shunt_to: float = 0.0

    def parse(self, line: str) -> None:
        """

        :param line:
        :return:
        """
        self.number = _parse_fixed(line, 1, 5, int)
        self.from_bus = self.number
        self.to_bus = _parse_fixed(line, 10, 14, int)
        self.status_from = _parse_fixed(line, 31, 32, str)
        self.status_to = _parse_fixed(line, 34, 35, str)
        self.shunt_from = _parse_fixed(line, 18, 23, float, 0)
        self.shunt_to = _parse_fixed(line, 24, 29, float, 0)

    def to_veragrid(self, bus_dict: Dict[int, dev.Bus]) -> list[tuple[int, dev.Shunt]]:
        """

        :param bus_dict:
        :return:
        """
        out = []
        if self.shunt_from != 0:
            sh = dev.Shunt()
            sh.name = f"Sh_{self.from_bus}"
            sh.B = float(self.shunt_from)
            sh.active = (self.status_from == "L")
            out.append((self.from_bus, sh))
        if self.shunt_to != 0:
            sh = dev.Shunt()
            sh.name = f"Sh_{self.to_bus}"
            sh.B = float(self.shunt_to)
            sh.active = (self.status_to == "L")
            out.append((self.to_bus, sh))
        return out

    def __repr__(self):
        return f"<Shunt {self.number} {self.from_bus} -> {self.to_bus} Shunt={self.shunt_from}/{self.shunt_to}>"


# -------------------------------------------------------------------------
#  StaticCompensator (DCSC)
# -------------------------------------------------------------------------

class PwfStaticCompensator:
    """
    StaticCompensator
    """
    __slots__ = (
        "number",
        "from_bus",
        "to_bus",
        "status",
        "initial_value",
        "specified_value",
    )

    def __init__(self):
        self.number: int = 0
        self.from_bus: int = 0
        self.to_bus: int = 0
        self.status: str = 'L'
        self.initial_value: float = 0.0
        self.specified_value: float = 0.0

    def parse(self, line: str) -> None:
        """

        :param line:
        :return:
        """
        self.number = _parse_fixed(line, 1, 5, int)
        self.from_bus = _parse_fixed(line, 6, 10, int)
        self.to_bus = _parse_fixed(line, 11, 15, int)
        self.status = _parse_fixed(line, 16, 16, str)
        self.initial_value = _parse_fixed(line, 17, 21, float, 2)
        self.specified_value = _parse_fixed(line, 22, 26, float, 2)

    def to_veragrid(self, bus_dict: Dict[int, dev.Bus]) -> tuple[int, dev.ControllableShunt]:
        """

        :param bus_dict:
        :return:
        """
        cs = dev.ControllableShunt()
        cs.name = f"SC{self.number}"
        cs.Bmax = float(self.specified_value)
        cs.Bmin = -float(self.specified_value)
        cs.Vset = 1.0
        cs.active = (self.status == 'L')
        return self.from_bus, cs

    def __repr__(self):
        return f"<StaticCompensator {self.number} {self.from_bus} -> {self.to_bus} Status={self.status}>"


class PwfControllableShunt:
    """Switched shunt or SVC record from DBSH/DCER."""

    __slots__ = (
        "bus", "controlled_bus", "v_min", "v_max", "q_initial",
        "q_min", "q_max", "mode", "status", "blocks",
    )

    def __init__(self) -> None:
        """Initialize one controllable shunt."""
        self.bus: int = 0
        self.controlled_bus: int = 0
        self.v_min: float = 0.9
        self.v_max: float = 1.1
        self.q_initial: float = 0.0
        self.q_min: float = 0.0
        self.q_max: float = 0.0
        self.mode: str = "C"
        self.status: str = "L"
        self.blocks: List[tuple[int, float]] = list()

    def to_veragrid(self, bus_dict: Dict[int, dev.Bus]) -> tuple[int, dev.ControllableShunt]:
        """Create the native VeraGrid controllable shunt.

        :param bus_dict: Parsed AC buses indexed by ANAREDE number.
        :return: Target bus number and native shunt object.
        """
        number_of_steps: int = len(self.blocks)
        shunt = dev.ControllableShunt(
            name=f"Shunt_{self.bus}",
            number_of_steps=number_of_steps,
            Bmin=self.q_min,
            Bmax=self.q_max,
            B=self.q_initial,
            vmin=self.v_min,
            vmax=self.v_max,
            active=self.status != "D",
            control_bus=bus_dict.get(self.controlled_bus, None),
        )
        if self.blocks:
            units: List[int] = [block[0] for block in self.blocks]
            values: List[float] = [block[1] for block in self.blocks]
            shunt.set_blocks(units, values)
        return self.bus, shunt


class PwfVscLink:
    """VSC link from the ANAREDE DVSC section."""

    __slots__ = (
        "number", "name", "from_bus", "to_bus", "power", "power_base",
        "voltage", "resistance", "active",
    )

    def __init__(self) -> None:
        """Initialize one VSC link."""
        self.number: int = 0
        self.name: str = ""
        self.from_bus: int = 0
        self.to_bus: int = 0
        self.power: float = 0.0
        self.power_base: float = 0.0
        self.voltage: float = 0.0
        self.resistance: float = 0.0
        self.active: bool = True

    def to_veragrid(self, bus_dict: Dict[int, dev.Bus]) -> dev.HvdcLine | None:
        """Represent the VSC link with VeraGrid's native HVDC object.

        :param bus_dict: Parsed AC buses indexed by ANAREDE number.
        :return: Native HVDC object, or ``None`` for missing endpoints.
        """
        bus_from: dev.Bus | None = bus_dict.get(self.from_bus, None)
        bus_to: dev.Bus | None = bus_dict.get(self.to_bus, None)
        if bus_from is None or bus_to is None:
            return None
        rate: float = max(abs(self.power), self.power_base)
        return dev.HvdcLine(
            bus_from=bus_from,
            bus_to=bus_to,
            name=self.name.strip() or f"VSC{self.number}",
            active=self.active and bus_from.active and bus_to.active,
            Pset=abs(self.power),
            rate=rate,
            r=self.resistance,
            dc_link_voltage=self.voltage,
        )


# -------------------------------------------------------------------------
#  DCLine (DCLI)
# -------------------------------------------------------------------------

class PwfDCLine:
    """
    PwfDCLine
    """
    __slots__ = (
        "number",
        "from_bus",
        "to_bus",
        "resistance",
        "capacity",
    )

    def __init__(self):
        self.number: int = 0
        self.from_bus: int = 0
        self.to_bus: int = 0
        self.resistance: float = 0.0
        self.capacity: float = 0.0

    def parse(self, line: str) -> None:
        """

        :param line:
        :return:
        """
        self.number = _parse_fixed(line, 1, 4, int)
        self.from_bus = self.number
        self.to_bus = _parse_fixed(line, 9, 12, int)
        self.resistance = _parse_fixed(line, 18, 23, float, 0)
        self.capacity = _parse_fixed(line, 61, 64, float, 0)

    def to_veragrid(self, bus_dict: Dict[int, dev.Bus]) -> dev.HvdcLine:
        """
        
        :param bus_dict: 
        :return: 
        """
        from_bus = bus_dict.get(self.from_bus, None)
        to_bus = bus_dict.get(self.to_bus, None)
        elm = dev.HvdcLine(
            name=f"HVDC{self.number}_{self.from_bus}-{self.to_bus}",
            bus_from=from_bus,
            bus_to=to_bus,
            r=self.resistance,
            # rate=self.vdc,
            active=True
        )
        return elm

    def __repr__(self):
        return f"<DCLine {self.from_bus} {self.to_bus} R={self.resistance:.2f}>"


class PwfHvdcConverter:
    """Converter data joined from DCNV and DCCV records."""

    __slots__ = (
        "number", "ac_bus", "dc_bus", "kind", "nominal_power",
        "control_type", "setpoint", "angle_min", "angle_max",
    )

    def __init__(self) -> None:
        """Initialize one converter record."""
        self.number: int = 0
        self.ac_bus: int = 0
        self.dc_bus: int = 0
        self.kind: str = "R"
        self.nominal_power: float = 0.0
        self.control_type: str = ""
        self.setpoint: float = 0.0
        self.angle_min: float = 5.0
        self.angle_max: float = 90.0


class PwfHvdcLink:
    """Classical ANAREDE HVDC link assembled into a VeraGrid line."""

    __slots__ = (
        "number", "name", "voltage", "active", "dc_buses",
        "dc_lines", "converters",
    )

    def __init__(self) -> None:
        """Initialize one link and its records awaiting association."""
        self.number: int = 0
        self.name: str = ""
        self.voltage: float = 0.0
        self.active: bool = True
        self.dc_buses: List[int] = list()
        self.dc_lines: List[PwfDCLine] = list()
        self.converters: List[PwfHvdcConverter] = list()

    def to_veragrid(self, bus_dict: Dict[int, dev.Bus]) -> dev.HvdcLine | None:
        """Create the existing VeraGrid HVDC line from joined records.

        :param bus_dict: Parsed AC buses indexed by ANAREDE number.
        :return: VeraGrid HVDC line, or ``None`` when the converter pair is incomplete.
        """
        rectifier: PwfHvdcConverter | None = None
        inverter: PwfHvdcConverter | None = None
        for converter in self.converters:
            if converter.kind == "R":
                rectifier = converter
            elif converter.kind == "I":
                inverter = converter

        if rectifier is None or inverter is None:
            return None

        bus_from: dev.Bus | None = bus_dict.get(rectifier.ac_bus, None)
        bus_to: dev.Bus | None = bus_dict.get(inverter.ac_bus, None)
        if bus_from is None or bus_to is None:
            return None

        resistance: float = sum(line.resistance for line in self.dc_lines)
        setpoint: float = abs(rectifier.setpoint)
        rate: float = max(setpoint, rectifier.nominal_power, inverter.nominal_power)
        active: bool = self.active and bus_from.active and bus_to.active
        return dev.HvdcLine(
            bus_from=bus_from,
            bus_to=bus_to,
            name=self.name.strip() or f"HVDC{self.number}",
            active=active,
            Pset=setpoint,
            rate=rate,
            r=resistance,
            dc_link_voltage=self.voltage,
            min_firing_angle_f=math.radians(rectifier.angle_min),
            max_firing_angle_f=math.radians(rectifier.angle_max),
            min_firing_angle_t=math.radians(inverter.angle_min),
            max_firing_angle_t=math.radians(inverter.angle_max),
        )


# -------------------------------------------------------------------------
#  DGBR — Generator Reactance
# -------------------------------------------------------------------------

class PwfGeneratorReactance:
    """
    PwfGeneratorReactance
    """
    __slots__ = (
        "number",
        "group",
        "reactance",
    )

    def __init__(self):
        self.number: int = 0
        self.group: int = 0
        self.reactance: float = 0.0

    def parse(self, line: str) -> None:
        """
        
        :param line: 
        :return: 
        """
        self.number = _parse_fixed(line, 1, 4, int)
        self.group = _parse_fixed(line, 5, 6, int)
        self.reactance = _parse_fixed(line, 7, 12, float, 4)

    def __repr__(self):
        return f"<GeneratorReactance {self.number} Group={self.group} Reactance={self.reactance:.4f}>"


# -------------------------------------------------------------------------
#  DGLT — Voltage Limit Group
# -------------------------------------------------------------------------

class PwfVoltageLimitGroup:
    """
    PwfVoltageLimitGroup
    """
    __slots__ = (
        "group",
        "lower_bound",
        "upper_bound",
        "lower_emergency_bound",
        "upper_emergency_bound",
    )

    def __init__(self):
        self.group: int = 0
        self.lower_bound: float = 0.0
        self.upper_bound: float = 1.2
        self.lower_emergency_bound: float = 0.8
        self.upper_emergency_bound: float = 1.2

    def parse(self, line: str) -> None:
        """
        
        :param line: 
        :return: 
        """
        self.group = _parse_fixed(line, 1, 2, int)
        self.lower_bound = _parse_fixed(line, 4, 8, float, 2)
        self.upper_bound = _parse_fixed(line, 10, 14, float, 2)
        self.lower_emergency_bound = _parse_fixed(line, 16, 20, float, 2)
        self.upper_emergency_bound = _parse_fixed(line, 22, 26, float, 2)

    def __repr__(self):
        return f"<VoltageLimitGroup {self.group} Bounds=({self.lower_bound}-{self.upper_bound})>"


# -------------------------------------------------------------------------
#  DCSC — Static Compensator
# -------------------------------------------------------------------------
"""
class PwfStaticCompensator:

    def __init__(self):
        self.number: int = 0
        self.from_bus: int = 0
        self.to_bus: int = 0
        self.status: str = 'L'
        self.initial_value: float = 0.0
        self.specified_value: float = 0.0

    def parse(self, line: str) -> None:
        self.number = _parse_fixed(line, 1, 5, int)
        self.from_bus = _parse_fixed(line, 6, 10, int)
        self.to_bus = _parse_fixed(line, 11, 15, int)
        self.status = _parse_fixed(line, 16, 16, str)
        self.initial_value = _parse_fixed(line, 17, 21, float, 2)
        self.specified_value = _parse_fixed(line, 22, 26, float, 2)

    def __repr__(self):
        return f"<StaticCompensator {self.number} {self.from_bus} -> {self.to_bus} Status={self.status}>"

"""


# -------------------------------------------------------------------------
#  DCAR — Equipment Connection
# -------------------------------------------------------------------------

class PwfEquipmentConnection:
    """
    PwfEquipmentConnection
    """
    __slots__ = (
        "number",
        "equipment_type_1",
        "equipment_id_1",
        "condition_1",
        "equipment_type_2",
        "equipment_id_2",
        "condition_2",
        "operation",
        "parameter_a",
        "parameter_b",
        "parameter_c",
        "parameter_d",
        "voltage",
    )

    def __init__(self):
        self.number: int = 0
        self.equipment_type_1: str = ""
        self.equipment_id_1: int = 0
        self.condition_1: str = ""
        self.equipment_type_2: str = ""
        self.equipment_id_2: int = 0
        self.condition_2: str = ""
        self.operation: str = "A"
        self.parameter_a: float = 0.0
        self.parameter_b: float = 0.0
        self.parameter_c: float = 0.0
        self.parameter_d: float = 0.0
        self.voltage: float = 0.0

    def parse(self, line: str) -> None:
        """
        
        :param line: 
        :return: 
        """
        self.number = _parse_fixed(line, 1, 4, int)
        self.equipment_type_1 = _parse_fixed(line, 5, 8, str)
        self.equipment_id_1 = _parse_fixed(line, 9, 13, int)
        self.condition_1 = _parse_fixed(line, 14, 14, str)
        self.equipment_type_2 = _parse_fixed(line, 15, 18, str)
        self.equipment_id_2 = _parse_fixed(line, 19, 23, int)
        self.condition_2 = _parse_fixed(line, 24, 24, str)
        self.operation = _parse_fixed(line, 25, 25, str)
        self.parameter_a = _parse_fixed(line, 26, 28, float, 2)
        self.parameter_b = _parse_fixed(line, 29, 31, float, 2)
        self.parameter_c = _parse_fixed(line, 32, 34, float, 2)
        self.parameter_d = _parse_fixed(line, 35, 37, float, 2)
        self.voltage = _parse_fixed(line, 38, 42, float, 2)

    def __repr__(self):
        return f"<EquipmentConnection {self.number} {self.equipment_type_1} -> {self.equipment_type_2}>"


# -------------------------------------------------------------------------
#  DCTR — Transformer Settings
# -------------------------------------------------------------------------

class PwfTransformerSettings:
    """
    PwfTransformerSettings
    """
    __slots__ = (
        "from_bus",
        "to_bus",
        "circuit",
        "minimum_voltage",
        "maximum_voltage",
        "bounds_control_type",
        "control_mode",
        "minimum_phase",
        "maximum_phase",
        "specified_value",
    )

    def __init__(self):
        self.from_bus: int = 0
        self.to_bus: int = 0
        self.circuit: str = ""
        self.minimum_voltage: float = 0.0
        self.maximum_voltage: float = 1.0
        self.bounds_control_type: str = 'C'
        self.control_mode: str = 'A'
        self.minimum_phase: float = 0.0
        self.maximum_phase: float = 1.0
        self.specified_value: float = 0.0

    def parse(self, line: str) -> None:
        """
        
        :param line: 
        :return: 
        """
        self.from_bus = _parse_fixed(line, 1, 5, int)
        self.to_bus = _parse_fixed(line, 6, 10, int)
        self.circuit = _parse_fixed(line, 11, 12, str)
        self.minimum_voltage = _parse_fixed(line, 13, 17, float, 2)
        self.maximum_voltage = _parse_fixed(line, 18, 22, float, 2)
        self.bounds_control_type = _parse_fixed(line, 23, 23, str)
        self.control_mode = _parse_fixed(line, 24, 24, str)
        self.minimum_phase = _parse_fixed(line, 25, 29, float, 2)
        self.maximum_phase = _parse_fixed(line, 30, 34, float, 2)
        self.specified_value = _parse_fixed(line, 35, 39, float, 2)

    def __repr__(self):
        return f"<TransformerSettings {self.from_bus} -> {self.to_bus} Control={self.control_mode}>"


class PwfStudyRecord:
    """Preserved non-topological ANAREDE study record."""

    __slots__ = ("section", "values")

    def __init__(self, section: str, values: List[str]) -> None:
        """Initialize one study-control record.

        :param section: ANAREDE section code.
        :param values: Tokenized record values in file order.
        """
        self.section: str = section
        self.values: List[str] = values


# -------------------------------------------------------------------------
#  DGEI — Generator Identifiers
# -------------------------------------------------------------------------

class PwfGeneratorIdentification:
    """
    PwfGeneratorIdentification
    """
    __slots__ = (
        "number",
        "operation",
        "automatic_mode",
        "group",
        "status",
        "units",
        "operating_units",
        "active_generation",
        "reactive_generation",
    )

    def __init__(self):
        self.number: int = 0
        self.operation: str = "A"
        self.automatic_mode: str = "N"
        self.group: int = 0
        self.status: str = "L"
        self.units: int = 1
        self.operating_units: int = 1
        self.active_generation: float = 0.0
        self.reactive_generation: float = 0.0

    def parse(self, line: str) -> None:
        """
        
        :param line: 
        :return: 
        """
        self.number = _parse_fixed(line, 1, 5, int)
        self.operation = _parse_fixed(line, 6, 6, str)
        self.automatic_mode = _parse_fixed(line, 7, 7, str)
        self.group = _parse_fixed(line, 8, 9, int)
        self.status = _parse_fixed(line, 10, 10, str)
        self.units = _parse_fixed(line, 11, 13, int)
        self.operating_units = _parse_fixed(line, 14, 16, int)
        self.active_generation = _parse_fixed(line, 17, 21, float, 2)
        self.reactive_generation = _parse_fixed(line, 22, 26, float, 2)

    def __repr__(self):
        return f"<GeneratorIdentification {self.number} Group={self.group} ActiveGen={self.active_generation:.2f}>"


# -------------------------------------------------------------------------
#  DMOT — Motor Configuration
# -------------------------------------------------------------------------

class PwfMotorConfiguration:
    """
    PwfMotorConfiguration
    """
    __slots__ = (
        "bus",
        "operation",
        "status",
        "group",
        "sign",
        "loading_factor",
        "units",
        "stator_resistance",
        "stator_reactance",
        "magnetizing_reactance",
        "rotor_resistance",
        "rotor_reactance",
        "base_power",
        "engine_type",
        "active_charge_portion",
    )

    def __init__(self):
        self.bus: int = 0
        self.operation: str = "A"
        self.status: str = "L"
        self.group: int = 0
        self.sign: str = "+"
        self.loading_factor: float = 1.0
        self.units: int = 1
        self.stator_resistance: float = 0.0
        self.stator_reactance: float = 0.0
        self.magnetizing_reactance: float = 0.0
        self.rotor_resistance: float = 0.0
        self.rotor_reactance: float = 0.0
        self.base_power: float = 0.0
        self.engine_type: int = 0
        self.active_charge_portion: float = 0.0

    def parse(self, line: str) -> None:
        """
        
        :param line: 
        :return: 
        """
        self.bus = _parse_fixed(line, 1, 5, int)
        self.operation = _parse_fixed(line, 6, 6, str)
        self.status = _parse_fixed(line, 7, 7, str)
        self.group = _parse_fixed(line, 8, 9, int)
        self.sign = _parse_fixed(line, 10, 10, str)
        self.loading_factor = _parse_fixed(line, 11, 13, float, 2)
        self.units = _parse_fixed(line, 14, 16, int)
        self.stator_resistance = _parse_fixed(line, 17, 21, float, 4)
        self.stator_reactance = _parse_fixed(line, 22, 26, float, 4)
        self.magnetizing_reactance = _parse_fixed(line, 27, 31, float, 4)
        self.rotor_resistance = _parse_fixed(line, 32, 36, float, 4)
        self.rotor_reactance = _parse_fixed(line, 37, 41, float, 4)
        self.base_power = _parse_fixed(line, 42, 46, float, 4)
        self.engine_type = _parse_fixed(line, 47, 49, int)
        self.active_charge_portion = _parse_fixed(line, 50, 53, float, 3)

    def __repr__(self):
        return f"<MotorConfiguration {self.bus} Group={self.group} Status={self.status}>"


# -------------------------------------------------------------------------
#  DCMT — Comments
# -------------------------------------------------------------------------

class PwfComment:
    """
    PwfComment
    """
    __slots__ = (
        "comment",
    )

    def __init__(self):
        self.comment: str = ""

    def parse(self, line: str) -> None:
        """
        
        :param line: 
        :return: 
        """
        self.comment = line.strip()

    def __repr__(self):
        return f"<Comment: {self.comment}>"


# -------------------------------------------------------------------------
#  Injection (DINJ)
# -------------------------------------------------------------------------

class PwfInjection:
    """
    PwfInjection
    """
    __slots__ = (
        "number",
        "operation",
        "equivalent_active_injection",
        "equivalent_reactive_injection",
        "equivalent_shunt",
        "equivalent_participation_factor",
    )

    def __init__(self):
        self.number: int = 0
        self.operation: str = "A"
        self.equivalent_active_injection: float = 0.0
        self.equivalent_reactive_injection: float = 0.0
        self.equivalent_shunt: float = 0.0
        self.equivalent_participation_factor: float = 0.0

    def parse(self, line: str) -> None:
        """
        
        :param line: 
        :return: 
        """
        self.number = _parse_fixed(line, 1, 5, int)
        self.operation = _parse_fixed(line, 6, 6, str)
        self.equivalent_active_injection = _parse_fixed(line, 7, 14, float, 2)
        self.equivalent_reactive_injection = _parse_fixed(line, 15, 22, float, 2)
        self.equivalent_shunt = _parse_fixed(line, 23, 29, float, 2)
        self.equivalent_participation_factor = _parse_fixed(line, 30, 36, float, 2)

    def __repr__(self):
        return f"<Injection {self.number} Active={self.equivalent_active_injection} Reactive={self.equivalent_reactive_injection}>"


# -------------------------------------------------------------------------
#  PWFNetwork (container)
# -------------------------------------------------------------------------
class PwfNetwork:
    """
    PwfNetwork
    """
    __slots__ = (
        "buses",
        "lines",
        "generators",
        "transformers",
        "shunts",
        "static_compensators",
        "controllable_shunts",
        "vsc_links",
        "dc_lines",
        "loads",
        "comments",
        "injections",
        "generator_reactances",
        "voltage_limit_groups",
        "voltage_groups",
        "generator_identifications",
        "transformer_settings",
        "study_records",
    )

    def __init__(self):
        # Store devices by type (e.g., buses, lines, generators, etc.)
        self.buses: List[PwfBus] = list()
        self.lines: List[PwfLine] = list()
        self.generators: List[PwfGenerator] = list()
        self.transformers: List[PwfTransformer] = list()
        self.shunts: List[PwfShunt] = list()
        self.static_compensators: List[PwfStaticCompensator] = list()
        self.controllable_shunts: List[PwfControllableShunt] = list()
        self.vsc_links: List[PwfVscLink] = list()
        self.dc_lines: List[PwfDCLine] = list()
        self.loads: List[PwfLoad] = list()
        self.comments: List[PwfComment] = list()
        self.injections: List[PwfInjection] = list()
        self.generator_reactances: List[PwfGeneratorReactance] = list()
        self.voltage_limit_groups: List[PwfVoltageLimitGroup] = list()
        self.voltage_groups: List[PwfVoltageGroup] = list()
        self.generator_identifications: List[PwfGeneratorIdentification] = list()
        self.transformer_settings: List[PwfTransformerSettings] = list()
        self.study_records: List[PwfStudyRecord] = list()

    def add_device(self, device):
        """
        Add a device to the appropriate list based on its class type.
        :param device:
        :return:
        """

        if isinstance(device, PwfBus):
            self.buses.append(device)
        elif isinstance(device, PwfVoltageGroup):
            self.voltage_groups.append(device)
        elif isinstance(device, PwfLine):
            self.lines.append(device)
        elif isinstance(device, PwfGenerator):
            self.generators.append(device)
        elif isinstance(device, PwfTransformer):
            self.transformers.append(device)
        elif isinstance(device, PwfControllableShunt):
            self.controllable_shunts.append(device)
        elif isinstance(device, PwfVscLink):
            self.vsc_links.append(device)
        elif isinstance(device, PwfShunt):
            self.shunts.append(device)
        elif isinstance(device, PwfStaticCompensator):
            self.static_compensators.append(device)
        elif isinstance(device, PwfDCLine):
            self.dc_lines.append(device)
        elif isinstance(device, PwfLoad):
            self.loads.append(device)
        elif isinstance(device, PwfComment):
            self.comments.append(device)
        elif isinstance(device, PwfInjection):
            self.injections.append(device)
        elif isinstance(device, PwfGeneratorReactance):
            self.generator_reactances.append(device)
        elif isinstance(device, PwfVoltageLimitGroup):
            self.voltage_limit_groups.append(device)
        elif isinstance(device, PwfGeneratorIdentification):
            self.generator_identifications.append(device)
        elif isinstance(device, PwfTransformerSettings):
            self.transformer_settings.append(device)
        elif isinstance(device, PwfStudyRecord):
            self.study_records.append(device)

        else:
            raise ValueError(f"Unknown device type: {type(device)}")

    def __repr__(self):
        return (f"<PWFNetwork: {len(self.buses)} buses, "
                f"{len(self.lines)} lines, {len(self.generators)} generators, "
                f"{len(self.transformers)} transformers, "
                f"{len(self.shunts)} shunts, {len(self.static_compensators)} static compensators>")


# -------------------------------------------------------------------------
#  Parser
# -------------------------------------------------------------------------

def _decode_pwf(data: bytes) -> str:
    """Decode PWF bytes using Latin-1 first and detector-assisted recovery.

    :param data: Raw PWF file contents.
    :return: Decoded PWF text.
    """
    latin1_text: str
    try:
        latin1_text = data.decode("latin-1")
    except UnicodeDecodeError:
        detection: dict[str, object] = chardet.detect(data)
        detected_encoding: object = detection.get("encoding", None)
        if isinstance(detected_encoding, str) and detected_encoding != "":
            try:
                return data.decode(detected_encoding)
            except (LookupError, UnicodeDecodeError):
                return data.decode("latin-1")
        else:
            return data.decode("latin-1")

    detection = chardet.detect(data)
    detected_encoding = detection.get("encoding", None)
    confidence: object = detection.get("confidence", 0.0)
    mojibake_markers: bool = "Ã" in latin1_text or "Â" in latin1_text
    if (
        mojibake_markers
        and isinstance(detected_encoding, str)
        and detected_encoding.casefold() not in ("", "latin-1", "iso-8859-1")
        and isinstance(confidence, float)
        and confidence >= 0.5
    ):
        try:
            return data.decode(detected_encoding)
        except (LookupError, UnicodeDecodeError):
            return latin1_text
    else:
        return latin1_text


def _split_sections(
    file_name: str,
    section_definitions: Dict[str, str],
) -> tuple[List[str], Dict[str, List[str]]]:
    """
    Splits a PWF file into sections based on the delimiter "99999".
    Each section is stored in a dictionary with the section name as the key
    and the line indices as the value.
    """
    with open(file_name, "rb") as io:
        file_data: bytes = io.read()
    decoded_text: str = _decode_pwf(file_data)
    file_lines: List[str] = [line.rstrip("\r\n") for line in decoded_text.splitlines()]

    sections = dict()
    section_name = ""
    for line in file_lines:
        stripped_line = line.strip()
        is_section_name: bool = (
            len(stripped_line) == 4
            and stripped_line.isalpha()
            and stripped_line.isupper()
        )
        if stripped_line == "99999":
            pass
        elif stripped_line in section_definitions or is_section_name:
            section_name = stripped_line
            sections[section_name] = [line]
        elif section_name != "":
            sections[section_name].append(line)
        else:
            # The title text before the first data section is not electrical
            # data and therefore does not belong to a parser object.
            pass

    return file_lines, sections


class PWFParser:
    """
    PWFParser
    """
    __slots__ = (
        "filepath",
        "network",
        "logger",
        "voltage_group_dict",
        "hvdc_records",
        "area_records",
    )

    def __init__(self, filepath: str):
        self.filepath: str = filepath
        self.network: PwfNetwork = PwfNetwork()
        self.logger = Logger()

        self.voltage_group_dict: Dict[str, PwfVoltageGroup] = dict()
        self.hvdc_records: Dict[str, List[object]] = dict()
        self.area_records: Dict[int, str] = dict()

        section_definitions: Dict[str, str] = {
            "TITU": "case title",                  # Textual case title.
            "DGBT": "voltage groups",             # Base voltage group table.
            "DBAR": "AC buses",                    # AC bus operating data.
            "DGER": "generator limits",           # Generator technical limits.
            "DLIN": "AC lines and transformers",  # AC branch data.
            "DGEI": "generator identification",   # Generator/unit grouping.
            "DTRA": "transformers",                # Transformer data records.
            "DSHL": "line-end shunts",             # Shunts at line terminals.
            "DCSC": "series compensators",         # Controllable series compensation.
            "DCLI": "DC line segments",            # Classical HVDC conductor data.
            "DELO": "HVDC links",                  # Classical HVDC link headers.
            "DBRE": "comments",                    # Free-form case comments.
            "DINJ": "equivalent injections",       # Equivalent network injections.
            "DGBR": "generator reactances",        # Generator subtransient data.
            "DGLT": "voltage limit groups",        # Bus voltage-limit groups.
            "DBSH": "switched shunts",             # Switched shunt-bank data.
            "DCER": "static var compensators",     # SVC data.
            "DCBA": "HVDC buses",                  # DC bus-to-link associations.
            "DCNV": "HVDC converters",             # Converter terminal data.
            "DCCV": "HVDC converter controls",     # Converter control setpoints.
            "DVSC": "VSC HVDC links",              # Voltage-source-converter links.
            "DARE": "areas",                       # Area names and exchanges.
            "DCMT": "additional comments",         # Additional free-form comments.
            "DCTR": "transformer controls",        # LTC/tap-control settings.
            "DCTE": "solver constants",             # ANAREDE flow-solver constants.
            "DCAR": "load curve data",              # Optional load ZIP/time curves.
            "DOPC": "execution options",            # ANAREDE run/report options.
            "DMET": "measurement data",             # Measurement and monitoring data.
            "DINC": "incremental controls",         # Incremental/control study data.
            "FIM": "end of file",                  # PWF end marker.
        }
        file_lines, sections = _split_sections(self.filepath, section_definitions)

        for section_name in sections:
            if section_name.startswith("D") and section_name not in section_definitions:
                self.logger.add_warning(
                    f"ANAREDE section {section_name} is present but is not interpreted."
                )

        for section_name, txt_lines in sections.items():

            if len(txt_lines) > 2:

                if section_name == "DBAR":  # Bus
                    for txt_line in txt_lines[2:]:
                        bus = PwfBus()
                        bus.parse(txt_line)
                        self.network.add_device(bus)
                        if bus.pl != 0.0 or bus.ql != 0.0:
                            load = PwfLoad()
                            load.number = bus.number
                            load.operation = "A" if bus.status != "D" else "D"
                            load.bus = bus.number
                            load.active_power = bus.pl
                            load.reactive_power = bus.ql
                            load.status = bus.status
                            self.network.add_device(load)

                if section_name == "DGBT":  # Voltage Group
                    for txt_line in txt_lines[2:]:
                        vg = PwfVoltageGroup()
                        vg.parse(txt_line)
                        self.network.add_device(vg)
                        self.voltage_group_dict[vg.char] = vg

                elif section_name == "DLIN":  # Line
                    for txt_line in txt_lines[2:]:
                        line = PwfLine()
                        line.parse(txt_line)
                        if line.tap != 0.0 and line.tap != 1.0:
                            transformer = PwfTransformer()
                            transformer.number = line.from_bus
                            transformer.from_bus = line.from_bus
                            transformer.to_bus = line.to_bus
                            transformer.r = line.r
                            transformer.x = line.x
                            transformer.tap = line.tap
                            transformer.shift = line.tap_lag
                            transformer.tap_min = line.tap_min
                            transformer.tap_max = line.tap_max
                            transformer.controlled_bus = line.controlled_bus
                            transformer.active = line.status != "D"
                            self.network.add_device(transformer)
                        else:
                            self.network.add_device(line)

                elif section_name == "DGER":  # Generator
                    for txt_line in txt_lines[2:]:
                        generator = PwfGenerator()
                        generator.parse(txt_line)
                        self.network.add_device(generator)

                elif section_name == "DGEI":  # Generator Identification
                    for txt_line in txt_lines[2:]:
                        genid = PwfGeneratorIdentification()
                        genid.parse(txt_line)
                        self.network.add_device(genid)

                elif section_name == "DTRA":  # Transformer
                    for txt_line in txt_lines[2:]:
                        transformer = PwfTransformer()
                        transformer.parse(txt_line)
                        self.network.add_device(transformer)

                elif section_name == "DCTR":  # Transformer tap settings
                    for txt_line in txt_lines[2:]:
                        settings = PwfTransformerSettings()
                        settings.parse(txt_line)
                        self.network.add_device(settings)

                elif section_name in ("DOPC", "DCTE", "DMET", "DINC"):
                    for txt_line in txt_lines[2:]:
                        values: List[str] = txt_line.split()
                        if values:
                            self.network.add_device(
                                PwfStudyRecord(section_name, values)
                            )

                elif section_name == "DSHL":  # Shunt
                    for txt_line in txt_lines[2:]:
                        shunt = PwfShunt()
                        shunt.parse(txt_line)
                        self.network.add_device(shunt)

                elif section_name == "DBSH":  # Switched shunt bank
                    current_shunt: PwfControllableShunt | None = None
                    for txt_line in txt_lines[2:]:
                        if txt_line.strip().upper() == "FBAN":
                            current_shunt = None
                        elif current_shunt is not None and txt_line[2:5].strip() == "":
                            units: int = _parse_fixed(txt_line, 13, 15, int)
                            if units == 0:
                                units = _parse_fixed(txt_line, 9, 11, int)
                            value: float = _parse_fixed(txt_line, 17, 22, float, 0)
                            current_shunt.blocks.append((units, value))
                        elif txt_line.strip().startswith("("):
                            pass
                        else:
                            current_shunt = PwfControllableShunt()
                            current_shunt.bus = _parse_fixed(txt_line, 1, 5, int)
                            current_shunt.v_min = _parse_fixed(txt_line, 20, 23, float, 3)
                            current_shunt.v_max = _parse_fixed(txt_line, 25, 28, float, 3)
                            current_shunt.controlled_bus = _parse_fixed(txt_line, 30, 35, int)
                            current_shunt.q_initial = _parse_fixed(txt_line, 36, 42, float, 0)
                            current_shunt.mode = _parse_fixed(txt_line, 43, 43, str) or "C"
                            current_shunt.status = _parse_fixed(txt_line, 45, 45, str) or "L"
                            self.network.add_device(current_shunt)

                elif section_name == "DCER":  # Static var compensator
                    for txt_line in txt_lines[2:]:
                        shunt = PwfControllableShunt()
                        shunt.bus = _parse_fixed(txt_line, 1, 5, int)
                        shunt.controlled_bus = _parse_fixed(txt_line, 15, 19, int)
                        shunt.q_initial = _parse_fixed(txt_line, 28, 32, float, 0)
                        shunt.q_min = _parse_fixed(txt_line, 33, 37, float, 0)
                        shunt.q_max = _parse_fixed(txt_line, 38, 42, float, 0)
                        shunt.mode = "C"
                        shunt.status = _parse_fixed(txt_line, 46, 46, str) or "L"
                        self.network.add_device(shunt)

                elif section_name == "DCSC":  # Static Compensator
                    for txt_line in txt_lines[2:]:
                        series_line = PwfLine()
                        series_line.from_bus = _parse_fixed(txt_line, 1, 5, int)
                        series_line.to_bus = _parse_fixed(txt_line, 10, 14, int)
                        series_line.circuit = _parse_fixed(txt_line, 15, 16, str)
                        series_line.status = _parse_fixed(txt_line, 17, 17, str) or "L"
                        series_line.x = _parse_fixed(txt_line, 38, 43, float, 0) / 100.0
                        series_line.normal_capacity = _parse_fixed(txt_line, 61, 64, float, 0)
                        self.network.add_device(series_line)

                elif section_name == "DVSC":  # VSC HVDC link
                    for txt_line in txt_lines[2:]:
                        link = PwfVscLink()
                        link.number = _parse_fixed(txt_line, 1, 4, int)
                        link.active = _parse_fixed(txt_line, 8, 8, str) != "D"
                        link.from_bus = _parse_fixed(txt_line, 10, 14, int)
                        link.to_bus = _parse_fixed(txt_line, 16, 20, int)
                        link.power = _parse_fixed(txt_line, 22, 28, float, 0)
                        link.power_base = _parse_fixed(txt_line, 30, 36, float, 0)
                        link.voltage = _parse_fixed(txt_line, 38, 46, float, 0)
                        link.resistance = _parse_fixed(txt_line, 58, 65, float, 0)
                        link.name = _parse_fixed(txt_line, 67, 86, str)
                        self.network.add_device(link)

                elif section_name == "DARE":  # Area definitions
                    for txt_line in txt_lines[2:]:
                        number: int = _parse_fixed(txt_line, 1, 3, int)
                        name: str = _parse_fixed(txt_line, 12, 47, str)
                        self.area_records[number] = name

                elif section_name == "DCLI":  # DC line segment
                    for txt_line in txt_lines[2:]:
                        dc_line = PwfDCLine()
                        dc_line.parse(txt_line)
                        self.hvdc_records.setdefault("dc_lines", list()).append(dc_line)

                elif section_name == "DELO":  # HVDC link definition
                    for txt_line in txt_lines[2:]:
                        link = PwfHvdcLink()
                        link.number = _parse_fixed(txt_line, 1, 4, int)
                        link.voltage = _parse_fixed(txt_line, 8, 12, float, 0)
                        link.name = _parse_fixed(txt_line, 20, 39, str)
                        state: str = _parse_fixed(txt_line, 43, 43, str)
                        link.active = state != "D"
                        self.hvdc_records.setdefault("links", list()).append(link)

                elif section_name == "DCBA":  # DC bus to link association
                    for txt_line in txt_lines[2:]:
                        dc_bus: int = _parse_fixed(txt_line, 1, 4, int)
                        link_number: int = _parse_fixed(txt_line, 72, 75, int)
                        self.hvdc_records.setdefault("dc_bus_links", list()).append(
                            (dc_bus, link_number)
                        )

                elif section_name == "DCNV":  # Converter records
                    for txt_line in txt_lines[2:]:
                        converter = PwfHvdcConverter()
                        converter.number = _parse_fixed(txt_line, 1, 4, int)
                        converter.ac_bus = _parse_fixed(txt_line, 8, 12, int)
                        converter.dc_bus = _parse_fixed(txt_line, 14, 17, int)
                        converter.kind = _parse_fixed(txt_line, 24, 24, str) or "R"
                        converter.nominal_power = _parse_fixed(
                            txt_line, 46, 50, float, 0
                        )
                        self.hvdc_records.setdefault("converters", list()).append(
                            converter
                        )

                elif section_name == "DCCV":  # Converter controls
                    for txt_line in txt_lines[2:]:
                        number: int = _parse_fixed(txt_line, 1, 4, int)
                        for item in self.hvdc_records.get("converters", list()):
                            converter = item
                            if isinstance(converter, PwfHvdcConverter) and converter.number == number:
                                converter.control_type = _parse_fixed(
                                    txt_line, 10, 10, str
                                )
                                converter.setpoint = _parse_fixed(
                                    txt_line, 12, 16, float, 0
                                )
                                converter.angle_min = _parse_fixed(
                                    txt_line, 36, 40, float, 0
                                )
                                converter.angle_max = _parse_fixed(
                                    txt_line, 42, 46, float, 0
                                )

                elif section_name == "DBRE":  # Comment
                    for txt_line in txt_lines[2:]:
                        comment = PwfComment()
                        comment.parse(txt_line)
                        self.network.add_device(comment)

                elif section_name == "DINJ":  # Injection
                    for txt_line in txt_lines[2:]:
                        injection = PwfInjection()
                        injection.parse(txt_line)
                        self.network.add_device(injection)

                elif section_name == "DGBR":  # Generator Reactance
                    for txt_line in txt_lines[2:]:
                        generator_reactance = PwfGeneratorReactance()
                        generator_reactance.parse(txt_line)
                        self.network.add_device(generator_reactance)

                elif section_name == "DGLT":  # Voltage Limit Group
                    for txt_line in txt_lines[2:]:
                        voltage_limit_group = PwfVoltageLimitGroup()
                        voltage_limit_group.parse(txt_line)
                        self.network.add_device(voltage_limit_group)

            else:
                # not enough data values
                pass

        for generator in self.network.generators:
            for bus in self.network.buses:
                if generator.number == bus.number:
                    generator.operation = "A" if bus.status != "D" else "D"
                    generator.active_generation = bus.pg
                    generator.reactive_generation = bus.qg
                    generator.min_reactive_generation = bus.qmin
                    generator.max_reactive_generation = bus.qmax
                    generator.voltage = bus.voltage

        self._assemble_hvdc()

    def _assemble_hvdc(self) -> None:
        """Join DELO, DCBA, DCLI, DCNV, and DCCV into link objects."""
        links: List[PwfHvdcLink] = list()
        for item in self.hvdc_records.get("links", list()):
            if isinstance(item, PwfHvdcLink):
                links.append(item)

        dc_bus_links: List[tuple[int, int]] = list()
        for item in self.hvdc_records.get("dc_bus_links", list()):
            if isinstance(item, tuple) and len(item) == 2:
                dc_bus_links.append((int(item[0]), int(item[1])))

        for dc_bus, link_number in dc_bus_links:
            for link in links:
                if link.number == link_number:
                    link.dc_buses.append(dc_bus)

        for item in self.hvdc_records.get("dc_lines", list()):
            if isinstance(item, PwfDCLine):
                for link in links:
                    if item.from_bus in link.dc_buses or item.to_bus in link.dc_buses:
                        link.dc_lines.append(item)

        for item in self.hvdc_records.get("converters", list()):
            if isinstance(item, PwfHvdcConverter):
                for link in links:
                    if item.dc_bus in link.dc_buses:
                        link.converters.append(item)

        self.hvdc_records["assembled_links"] = links

    def to_veragrid(self) -> MultiCircuit:
        """
        Convert Anarede grid to VeraGrid
        :return:
        """
        grid = MultiCircuit(name="Anarede_Network")

        vg_dict = {vg.char: vg for vg in self.network.voltage_groups}
        voltage_limits = {
            str(limit.group): limit for limit in self.network.voltage_limit_groups
        }

        #  Create one native area and zone per ANAREDE identifier before buses
        #  are converted, so every bus receives the canonical circuit object.
        area_names: Dict[int, str] = dict(self.area_records)
        for bus_record in self.network.buses:
            if bus_record.area not in area_names:
                area_names[bus_record.area] = f"Area_{bus_record.area}"
        area_dict: Dict[int, dev.Area] = dict()
        for number, name in area_names.items():
            area: dev.Area = dev.Area(name=name.strip() or f"Area_{number}")
            area_dict[number] = area
            grid.add_area(area)

        zone_dict: Dict[int, dev.Zone] = dict()
        for bus_record in self.network.buses:
            if bus_record.zone not in zone_dict:
                zone: dev.Zone = dev.Zone(name=f"Zone_{bus_record.zone}")
                zone_dict[bus_record.zone] = zone
                grid.add_zone(zone)

        #  BUSES 
        bus_dict: Dict[int, dev.Bus] = {}
        for b in self.network.buses:
            bus = b.to_veragrid(
                vg_dict,
                voltage_limits,
                area_dict,
                zone_dict,
            )
            grid.add_bus(bus)
            bus_dict[b.number] = bus

        #  LINES 
        for l in self.network.lines:
            elm = l.to_veragrid(bus_dict)
            grid.add_line(elm)

        #  TRANSFORMERS 
        for t in self.network.transformers:
            elm = t.to_veragrid(bus_dict)
            for settings in self.network.transformer_settings:
                if settings.from_bus == t.from_bus and settings.to_bus == t.to_bus:
                    elm.tap_module_min = settings.minimum_voltage
                    elm.tap_module_max = settings.maximum_voltage
                    break
            grid.add_transformer2w(elm)

        #  GENERATORS 
        for g in self.network.generators:
            elm = g.to_veragrid(bus_dict)
            bus = bus_dict.get(g.number, None)
            if bus is not None:
                grid.add_generator(bus=bus, api_obj=elm)

        #  LOADS 
        for ld in self.network.loads:
            elm = ld.to_veragrid(bus_dict)
            bus = bus_dict.get(ld.bus)
            if bus is not None:
                grid.add_load(bus=bus, api_obj=elm)

        #  SHUNTS 
        for sh in self.network.shunts:
            for bus_id, elm in sh.to_veragrid(bus_dict):
                bus = bus_dict.get(bus_id)
                if bus is not None:
                    grid.add_shunt(bus=bus, api_obj=elm)

        #  STATIC COMPENSATORS 
        for sc in self.network.static_compensators:
            bus_id, elm = sc.to_veragrid(bus_dict)
            bus = bus_dict.get(bus_id)
            if bus is not None:
                grid.add_controllable_shunt(bus=bus, api_obj=elm)

        #  SWITCHED SHUNTS AND SVCS
        for shunt in self.network.controllable_shunts:
            bus_id, elm = shunt.to_veragrid(bus_dict)
            bus = bus_dict.get(bus_id, None)
            if bus is not None:
                grid.add_controllable_shunt(bus=bus, api_obj=elm)

        #  DC LINES 
        for item in self.hvdc_records.get("assembled_links", list()):
            if isinstance(item, PwfHvdcLink):
                elm = item.to_veragrid(bus_dict)
                if elm is not None:
                    grid.add_hvdc(elm)

        #  VSC HVDC LINKS
        for link in self.network.vsc_links:
            elm = link.to_veragrid(bus_dict)
            if elm is not None:
                grid.add_hvdc(elm)

        return grid
