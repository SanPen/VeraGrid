from __future__ import annotations

from VeraGridEngine.IO.Eurostag.Devices.eurostag_base import slice_float, slice_text


class EurostagSlackBus:
    PREFIX = "5 "
    NAME = (3, 11)
    PHASE_ANGLE = (39, 47)

    def __init__(self):
        self.name = ""
        self.phase_angle = 0.0

    def parse_line(self, line: str) -> None:
        self.name = slice_text(line, *self.NAME)
        self.phase_angle = slice_float(line, *self.PHASE_ANGLE)
