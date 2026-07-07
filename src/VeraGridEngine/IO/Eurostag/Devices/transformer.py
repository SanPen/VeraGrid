from __future__ import annotations

from VeraGridEngine.IO.Eurostag.Devices.eurostag_base import slice_float, slice_int, slice_text


class EurostagType1Transformer:
    PREFIX = "41"
    SENDING_NODE = (2, 10)
    OPENING_CODE = (10, 11)
    RECEIVING_NODE = (11, 19)
    PARALLEL_INDEX = (19, 20)
    RESISTANCE = (21, 29)
    REACTANCE = (30, 38)
    RATED_APPARENT_POWER = (57, 65)
    TRANSFORMATION_RATIO = (66, 74)

    def __init__(self):
        self.sending_node = ""
        self.opening_code = ""
        self.receiving_node = ""
        self.parallel_index = "1"
        self.resistance = 0.0
        self.reactance = 0.0
        self.rated_apparent_power = 100.0
        self.transformation_ratio = 1.0
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
        self.rated_apparent_power = slice_float(line, *self.RATED_APPARENT_POWER, default=100.0)
        self.transformation_ratio = slice_float(line, *self.TRANSFORMATION_RATIO, default=1.0)
        self.name = self.code


class EurostagType8Tap:
    TAP_NUMBER = (21, 25)
    SENDING_SIDE_VOLTAGE = (26, 34)
    RECEIVING_SIDE_VOLTAGE = (35, 43)
    LEAKAGE_IMPEDANCE = (44, 52)
    PHASE_SHIFT_ANGLE = (53, 61)

    def __init__(self):
        self.tap_number = 0
        self.sending_side_voltage = 0.0
        self.receiving_side_voltage = 0.0
        self.leakage_impedance = 0.0
        self.phase_shift_angle = 0.0

    def parse_line(self, line: str) -> None:
        self.tap_number = slice_int(line, *self.TAP_NUMBER)
        self.sending_side_voltage = slice_float(line, *self.SENDING_SIDE_VOLTAGE)
        self.receiving_side_voltage = slice_float(line, *self.RECEIVING_SIDE_VOLTAGE)
        self.leakage_impedance = slice_float(line, *self.LEAKAGE_IMPEDANCE)
        self.phase_shift_angle = slice_float(line, *self.PHASE_SHIFT_ANGLE)


class EurostagType8Transformer:
    PREFIX = "48"
    FIRST_MIN_LEN = 82
    SECOND_LEN = 68
    TAP_LEN = 61

    SENDING_NODE = (2, 10)
    OPENING_CODE = (10, 11)
    RECEIVING_NODE = (11, 19)
    PARALLEL_INDEX = (19, 20)
    RATED_APPARENT_POWER = (21, 29)
    COPPER_LOSSES = (30, 38)
    IRON_LOSSES = (39, 47)
    NO_LOAD_CURRENT = (48, 56)
    SATURATION_EXPONENT = (57, 65)

    NOMINAL_TAP_NUMBER = (21, 25)
    INITIAL_TAP_POSITION = (26, 30)
    REGULATED_NODE_NAME = (31, 39)
    VOLTAGE_TARGET = (40, 48)
    ACTIVE_FLUX_MIN = (49, 57)
    ACTIVE_FLUX_MAX = (58, 66)
    REGULATING_MODE = (67, 68)

    def __init__(self):
        self.sending_node = ""
        self.opening_code = ""
        self.receiving_node = ""
        self.parallel_index = "1"
        self.rated_apparent_power = 100.0
        self.copper_losses = 0.0
        self.iron_losses = 0.0
        self.no_load_current = 0.0
        self.saturation_exponent = 0.0
        self.nominal_tap_number = 0
        self.initial_tap_position = 0
        self.regulated_node_name = ""
        self.voltage_target = 0.0
        self.active_flux_min = 0.0
        self.active_flux_max = 0.0
        self.regulating_mode = ""
        self.taps: list[EurostagType8Tap] = []
        self.name = ""

    @property
    def code(self) -> str:
        return f"{self.sending_node}_{self.receiving_node}_{self.parallel_index}"

    def parse_first_line(self, line: str) -> None:
        self.sending_node = slice_text(line, *self.SENDING_NODE)
        self.opening_code = slice_text(line, *self.OPENING_CODE)
        self.receiving_node = slice_text(line, *self.RECEIVING_NODE)
        self.parallel_index = slice_text(line, *self.PARALLEL_INDEX) or "1"
        self.rated_apparent_power = slice_float(line, *self.RATED_APPARENT_POWER, default=100.0)
        self.copper_losses = slice_float(line, *self.COPPER_LOSSES)
        self.iron_losses = slice_float(line, *self.IRON_LOSSES)
        self.no_load_current = slice_float(line, *self.NO_LOAD_CURRENT)
        self.saturation_exponent = slice_float(line, *self.SATURATION_EXPONENT)
        self.name = self.code

    def parse_second_line(self, line: str) -> None:
        self.nominal_tap_number = slice_int(line, *self.NOMINAL_TAP_NUMBER)
        self.initial_tap_position = slice_int(line, *self.INITIAL_TAP_POSITION)
        self.regulated_node_name = slice_text(line, *self.REGULATED_NODE_NAME)
        self.voltage_target = slice_float(line, *self.VOLTAGE_TARGET)
        self.active_flux_min = slice_float(line, *self.ACTIVE_FLUX_MIN)
        self.active_flux_max = slice_float(line, *self.ACTIVE_FLUX_MAX)
        self.regulating_mode = slice_text(line, *self.REGULATING_MODE)

    def add_tap(self, line: str) -> None:
        tap = EurostagType8Tap()
        tap.parse_line(line)
        self.taps.append(tap)

    def get_current_tap(self) -> EurostagType8Tap | None:
        for tap in self.taps:
            if tap.tap_number == self.initial_tap_position:
                return tap
        if self.taps:
            return self.taps[0]
        return None

    def get_nominal_tap(self) -> EurostagType8Tap | None:
        for tap in self.taps:
            if tap.tap_number == self.nominal_tap_number:
                return tap
        return self.get_current_tap()

    def get_current_leakage_impedance(self) -> float:
        current_tap = self.get_current_tap()
        if current_tap is None:
            return 0.0
        return current_tap.leakage_impedance

    @classmethod
    def from_lines(cls, rows: list[str], start: int) -> tuple["EurostagType8Transformer", int]:
        elm = cls()
        elm.parse_first_line(rows[start])
        next_idx = start + 1

        if next_idx < len(rows) and rows[next_idx].startswith(cls.PREFIX) and len(rows[next_idx]) == cls.SECOND_LEN:
            elm.parse_second_line(rows[next_idx])
            next_idx += 1

        while next_idx < len(rows) and rows[next_idx].startswith(cls.PREFIX) and len(rows[next_idx]) == cls.TAP_LEN:
            elm.add_tap(rows[next_idx])
            next_idx += 1

        return elm, next_idx
