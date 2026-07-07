from __future__ import annotations

from VeraGridEngine.IO.Eurostag.Devices.eurostag_base import slice_float, slice_text


class EurostagLine:
    PREFIX = "3 "
    SENDING_NODE = (2, 10)
    OPENING_CODE = (10, 11)
    RECEIVING_NODE = (11, 19)
    PARALLEL_INDEX = (19, 20)
    RESISTANCE = (21, 29)
    REACTANCE = (30, 38)
    SEMI_SHUNT_CONDUCTANCE = (39, 47)
    SEMI_SHUNT_SUSCEPTANCE = (48, 56)
    RATED_APPARENT_POWER = (57, 65)

    def __init__(self):
        self.sending_node = ""
        self.opening_code = ""
        self.receiving_node = ""
        self.parallel_index = "1"
        self.resistance = 0.0
        self.reactance = 0.0
        self.semi_shunt_conductance = 0.0
        self.semi_shunt_susceptance = 0.0
        self.rated_apparent_power = 9999.0
        self.name = ""

    @property
    def code(self) -> str:
        return f"{self.sending_node}_{self.receiving_node}_{self.parallel_index}"

    def parse_line(self, line: str) -> None:
        self.sending_node = slice_text(line, *self.SENDING_NODE)
        self.opening_code = slice_text(line, *self.OPENING_CODE)
        self.receiving_node = slice_text(line, *self.RECEIVING_NODE)
        self.parallel_index = slice_text(line, *self.PARALLEL_INDEX) or "1"
        self.resistance = slice_float(line, *self.RESISTANCE)
        self.reactance = slice_float(line, *self.REACTANCE)
        self.semi_shunt_conductance = slice_float(line, *self.SEMI_SHUNT_CONDUCTANCE)
        self.semi_shunt_susceptance = slice_float(line, *self.SEMI_SHUNT_SUSCEPTANCE)
        self.rated_apparent_power = slice_float(line, *self.RATED_APPARENT_POWER, default=9999.0)
        self.name = self.code


class EurostagCouplingDevice:
    PREFIX = "6 "
    SENDING_NODE = (2, 10)
    OPENING_CODE = (10, 11)
    RECEIVING_NODE = (11, 19)
    PARALLEL_INDEX = (19, 20)

    def __init__(self):
        self.sending_node = ""
        self.opening_code = ""
        self.receiving_node = ""
        self.parallel_index = "1"
        self.name = ""

    @property
    def code(self) -> str:
        return f"{self.sending_node}_{self.receiving_node}_{self.parallel_index}"

    def parse_line(self, line: str) -> None:
        self.sending_node = slice_text(line, *self.SENDING_NODE)
        self.opening_code = slice_text(line, *self.OPENING_CODE)
        self.receiving_node = slice_text(line, *self.RECEIVING_NODE)
        self.parallel_index = slice_text(line, *self.PARALLEL_INDEX) or "1"
        self.name = self.code
