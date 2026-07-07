from __future__ import annotations

from VeraGridEngine.IO.Eurostag.Devices.eurostag_base import slice_float, slice_text


class EurostagGenerator:
    PREFIX = "G "
    NAME = (3, 11)
    STATE = (12, 13)
    BUS_NAME = (14, 22)
    MIN_ACTIVE_POWER = (23, 31)
    ACTIVE_POWER = (32, 40)
    MAX_ACTIVE_POWER = (41, 49)
    MIN_REACTIVE_POWER = (50, 58)
    REACTIVE_POWER = (59, 67)
    MAX_REACTIVE_POWER = (68, 76)
    REGULATING_MODE = (77, 78)
    TARGET_VOLTAGE = (79, 87)
    REGULATED_NODE_NAME = (88, 96)
    REACTIVE_SHARING_COEFFICIENT = (97, 105)

    def __init__(self):
        self.name = ""
        self.state = "Y"
        self.bus_name = ""
        self.min_active_power = 0.0
        self.active_power = 0.0
        self.max_active_power = 9999.0
        self.min_reactive_power = -9999.0
        self.reactive_power = 0.0
        self.max_reactive_power = 9999.0
        self.regulating_mode = ""
        self.target_voltage = 0.0
        self.regulated_node_name = ""
        self.reactive_sharing_coefficient = 1.0

    def parse_line(self, line: str) -> None:
        self.name = slice_text(line, *self.NAME)
        self.state = slice_text(line, *self.STATE)
        self.bus_name = slice_text(line, *self.BUS_NAME)
        self.min_active_power = slice_float(line, *self.MIN_ACTIVE_POWER)
        self.active_power = slice_float(line, *self.ACTIVE_POWER)
        self.max_active_power = slice_float(line, *self.MAX_ACTIVE_POWER, default=9999.0)
        self.min_reactive_power = slice_float(line, *self.MIN_REACTIVE_POWER, default=-9999.0)
        self.reactive_power = slice_float(line, *self.REACTIVE_POWER)
        self.max_reactive_power = slice_float(line, *self.MAX_REACTIVE_POWER, default=9999.0)
        self.regulating_mode = slice_text(line, *self.REGULATING_MODE)
        self.target_voltage = slice_float(line, *self.TARGET_VOLTAGE)
        self.regulated_node_name = slice_text(line, *self.REGULATED_NODE_NAME) or self.bus_name
        self.reactive_sharing_coefficient = slice_float(
            line, *self.REACTIVE_SHARING_COEFFICIENT, default=1.0
        )


class EurostagDynamicGenerator:
    PREFIX = "M2 "
    ROW_COUNT = 6
    NAME = (0, 8)
    RATED_APPARENT_POWER = (18, 26)

    def __init__(self):
        self.name = ""
        self.rated_apparent_power = 0.0

    @classmethod
    def from_lines(cls, rows: list[str], start: int) -> tuple["EurostagDynamicGenerator", int]:
        elm = cls()
        if start + cls.ROW_COUNT > len(rows):
            return elm, len(rows)

        line = rows[start + 1]
        elm.name = slice_text(line, *cls.NAME)
        elm.rated_apparent_power = slice_float(line, *cls.RATED_APPARENT_POWER)
        return elm, start + cls.ROW_COUNT
