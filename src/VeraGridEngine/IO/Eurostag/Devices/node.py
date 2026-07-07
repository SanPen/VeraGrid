from __future__ import annotations

from VeraGridEngine.IO.Eurostag.Devices.eurostag_base import slice_float, slice_text


class EurostagNode:
    PREFIX = "1"
    AREA = (1, 3)
    NAME = (3, 11)
    BASE_VOLTAGE = (84, 92)
    INITIAL_VOLTAGE = (98, 106)
    INITIAL_ANGLE = (107, 115)

    def __init__(self):
        self.area = ""
        self.name = ""
        self.base_voltage = 0.0
        self.initial_voltage = 0.0
        self.initial_angle = 0.0
        self.is_slack = False

    def parse_line(self, line: str) -> None:
        self.area = slice_text(line, *self.AREA)
        self.name = slice_text(line, *self.NAME)
        self.base_voltage = slice_float(line, *self.BASE_VOLTAGE)
        self.initial_voltage = slice_float(line, *self.INITIAL_VOLTAGE)
        self.initial_angle = slice_float(line, *self.INITIAL_ANGLE)
