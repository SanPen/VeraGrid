from __future__ import annotations

from VeraGridEngine.IO.Eurostag.Devices.eurostag_base import slice_float, slice_int, slice_text


class EurostagLoad:
    PREFIX = "CH"
    NAME = (3, 11)
    STATE = (12, 13)
    BUS_NAME = (14, 22)
    ACTIVE_POWER = (41, 49)
    REACTIVE_POWER = (68, 76)

    def __init__(self):
        self.name = ""
        self.state = "Y"
        self.bus_name = ""
        self.active_power = 0.0
        self.reactive_power = 0.0

    def parse_line(self, line: str) -> None:
        self.name = slice_text(line, *self.NAME)
        self.state = slice_text(line, *self.STATE)
        self.bus_name = slice_text(line, *self.BUS_NAME)
        self.active_power = slice_float(line, *self.ACTIVE_POWER)
        self.reactive_power = slice_float(line, *self.REACTIVE_POWER)


class EurostagCapacitorBank:
    PREFIX = "C "
    NAME = (2, 10)
    BUS_NAME = (11, 19)
    NUMBER_ACTIVE_STEPS = (38, 41)
    ACTIVE_LOSS_ON_STEP = (42, 50)
    REACTIVE_POWER_ON_STEP = (51, 59)

    def __init__(self):
        self.name = ""
        self.bus_name = ""
        self.number_active_steps = 0
        self.active_loss_on_step = 0.0
        self.reactive_power_on_step = 0.0

    def parse_line(self, line: str) -> None:
        self.name = slice_text(line, *self.NAME)
        self.bus_name = slice_text(line, *self.BUS_NAME)
        self.number_active_steps = slice_int(line, *self.NUMBER_ACTIVE_STEPS)
        self.active_loss_on_step = slice_float(line, *self.ACTIVE_LOSS_ON_STEP)
        self.reactive_power_on_step = slice_float(line, *self.REACTIVE_POWER_ON_STEP)
