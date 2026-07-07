# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import math

from VeraGridEngine.IO.ucte.devices.ucte_base import (
    is_defined_number,
    sub_int,
    sub_optional_float,
    sub_str,
    try_float,
    try_int,
    try_optional_float,
    ucte_split,
)
from VeraGridEngine.basic_structures import Logger


def get_default_power_limit() -> float:
    return 9999.0


def try_parse_voltage(val: str | float, name: str, logger: Logger) -> float:
    """
    Parse a UCTE nominal voltage code or a direct numeric value.
    """
    ucte_voltage_map = {
        "0": 750,
        "1": 380,
        "2": 220,
        "3": 150,
        "4": 120,
        "5": 110,
        "6": 70,
        "7": 27,
        "8": 330,
        "9": 500,
        "A": 26,
        "B": 25,
        "C": 24,
        "D": 23,
        "E": 22,
        "F": 21,
        "G": 20,
        "H": 19,
        "I": 18,
        "J": 17,
        "K": 15.7,
        "L": 15,
        "M": 13.7,
        "N": 13,
        "O": 12,
        "P": 11,
        "Q": 9.8,
        "R": 9,
        "S": 8,
        "T": 7,
        "U": 6,
        "V": 5,
        "W": 4,
        "X": 3,
        "Y": 2,
        "Z": 1,
    }
    val_str = str(val).strip()
    val2 = ucte_voltage_map.get(val_str, None)

    if val2 is None:
        try:
            f = float(val_str)
        except ValueError:
            logger.add_error("Could not parse UCTE voltage",
                             device=name,
                             value=f"'{val}'")
            return 1.0

        if f > 0.0:
            logger.add_warning("UCTE voltage was not provided as a standard code, using the direct numeric value",
                               device=name,
                               value=f"'{val}'")
            return f

        logger.add_error("Provided UCTE voltage is zero",
                         device=name,
                         value=f"'{val} -> {f}'")
        return 1.0

    return float(val2)


class UcteNode:
    """
    UcteNode
    """

    def __init__(self):

        self.current_country = ""

        self.node_code = ""  # 0-7: Node (code)
        self.geo_name = ""  # 9-20: Geographical name
        self.status = 0  # 22: Status: 0 = real, 1 = equivalent

        # Node type code (0 = P and Q constant (PQ node);
        # 1 = Q and θ constant, 2 = P and U constant(PU node),
        # 3 = U and θ constant(global slack node, only one in the whole network))
        self.node_type = 0  # 24: Node type code

        self.voltage = 10.0  # Nominal voltage derived from the node code.
        self.voltage_reference = math.nan  # 26-31: Voltage reference value (kV)

        self.active_load = 0.0  # 33-39: Active load (MW)
        self.reactive_load = 0.0  # 41-47: Reactive load (MVAr)

        self.active_gen = math.nan  # 49-55: Active power generation (MW)
        self.reactive_gen = math.nan  # 57-63: Reactive power generation (MVAr)

        self.min_gen_mw = math.nan  # 65-71: Minimum permissible generation (MW) *
        self.max_gen_mw = math.nan  # 73-79: Maximum permissible generation (MW) *
        self.min_gen_mvar = math.nan  # 81-87: Minimum permissible generation (MVAr) *
        self.max_gen_mvar = math.nan  # 89-95: Maximum permissible generation (MVAr) *

        self.static_primary_control = math.nan  # 97-101: Static of primary control (%) *
        self.nominal_power_primary_control = math.nan  # 103-109: Nominal power for primary control (MW) *
        self.short_circuit_power = math.nan  # 111-117: Three-phase short circuit power (MVA) **
        self.xr_ratio = math.nan  # 119-125: X/R ratio **

        # H: hydro, N: nuclear, L: lignite,
        # C: hard coal, G: gas, O: oil, W: wind, F: further
        self.plant_type = ""  # 127: Power plant type

    @staticmethod
    def _get_voltage_window() -> tuple[float, float, float]:
        return 0.8, 1.2, 110.0

    def _looks_fixed_width(self, row: str) -> bool:
        """

        :param row:
        :return:
        """
        return (
            len(row) >= 26
            and row[8:9].isspace()
            and row[21:22].isspace()
            and row[23:24].isspace()
            and row[25:26].isspace()
        )

    def _parse_nominal_voltage(self, logger: Logger) -> float:
        """

        :param logger:
        :return:
        """
        if len(self.node_code) >= 7:
            inferred_voltage = try_parse_voltage(self.node_code[6], self.node_code, logger)
            if inferred_voltage > 0:
                return inferred_voltage

        if is_defined_number(self.voltage_reference) and self.voltage_reference > 0:
            logger.add_warning("Could not infer nominal voltage from node code, using voltage_reference as nominal voltage",
                               device=self.node_code,
                               value=self.voltage_reference)
            return self.voltage_reference

        logger.add_error("Could not infer nominal voltage from node code",
                         device=self.node_code,
                         value=self.node_code,
                         expected_value="8-character UCTE node code")
        return 1.0

    def has_load(self) -> bool:
        """

        :return:
        """
        return (
            (is_defined_number(self.active_load) and self.active_load != 0.0)
            or (is_defined_number(self.reactive_load) and self.reactive_load != 0.0)
        )

    def is_regulating_voltage(self) -> bool:
        """

        :return:
        """
        return self.node_type in (2, 3)

    def is_generator(self) -> bool:
        """

        :return:
        """
        return (
            self.is_regulating_voltage()
            or (is_defined_number(self.active_gen) and self.active_gen != 0.0)
            or (is_defined_number(self.reactive_gen) and self.reactive_gen != 0.0)
            or (
                is_defined_number(self.min_gen_mw)
                and is_defined_number(self.max_gen_mw)
                and (self.min_gen_mw != 0.0 or self.max_gen_mw != 0.0)
                and self.min_gen_mw != self.max_gen_mw
            )
            or (
                is_defined_number(self.min_gen_mvar)
                and is_defined_number(self.max_gen_mvar)
                and (self.min_gen_mvar != 0.0 or self.max_gen_mvar != 0.0)
                and self.min_gen_mvar != self.max_gen_mvar
            )
        )

    def has_gen(self) -> bool:
        """

        :return:
        """
        return self.is_generator()

    def _normalize_limits(self,
                          value: float,
                          min_value: float,
                          max_value: float) -> tuple[float, float]:
        """

        :param value:
        :param min_value:
        :param max_value:
        :return:
        """
        if not is_defined_number(min_value):
            min_value = -get_default_power_limit()

        if not is_defined_number(max_value):
            max_value = get_default_power_limit()

        if min_value > max_value:
            min_value, max_value = max_value, min_value

        if is_defined_number(value):
            if value > max_value:
                max_value = value
            if value < min_value:
                min_value = value

        return min_value, max_value

    def normalize(self, logger: Logger):
        """

        :param logger:
        :return:
        """
        low_voltage_factor, high_voltage_factor, low_nominal_voltage = self._get_voltage_window()

        if self.is_generator():
            if not is_defined_number(self.active_gen):
                self.active_gen = 0.0

            self.min_gen_mw, self.max_gen_mw = self._normalize_limits(
                value=self.active_gen,
                min_value=self.min_gen_mw,
                max_value=self.max_gen_mw,
            )

            if not is_defined_number(self.reactive_gen) and not self.is_regulating_voltage():
                self.reactive_gen = 0.0

            self.min_gen_mvar, self.max_gen_mvar = self._normalize_limits(
                value=self.reactive_gen if is_defined_number(self.reactive_gen) else math.nan,
                min_value=self.min_gen_mvar,
                max_value=self.max_gen_mvar,
            )

        if self.is_regulating_voltage():
            if not is_defined_number(self.voltage_reference) or self.voltage_reference <= 0.0:
                logger.add_warning("Voltage-regulating node has no valid voltage reference, switching it to PQ",
                                   device=self.node_code,
                                   value=self.voltage_reference)
                self.node_type = 0
            elif self.voltage > low_nominal_voltage and (
                self.voltage_reference < low_voltage_factor * self.voltage
                or self.voltage_reference > high_voltage_factor * self.voltage
            ):
                logger.add_warning("Voltage reference is far from the node nominal voltage",
                                   device=self.node_code,
                                   value=self.voltage_reference,
                                   expected_value=f"{low_voltage_factor * self.voltage:.2f}.."
                                                  f"{high_voltage_factor * self.voltage:.2f}")

        if not is_defined_number(self.active_load):
            self.active_load = 0.0

        if not is_defined_number(self.reactive_load):
            self.reactive_load = 0.0

    def parse(self, line: str, logger: Logger):
        """
        Parse the node record.
        """
        device = "Node"
        row = line.rstrip("\r\n")

        if self._looks_fixed_width(row):
            self.node_code = sub_str(row, 0, 8, device, "node_code", logger)
            self.geo_name = sub_str(row, 9, 21, device, "geo_name", logger)
            self.status = sub_int(row, 22, 23, device, "status", logger)
            self.node_type = sub_int(row, 24, 25, device, "node_type", logger)
            self.voltage_reference = sub_optional_float(row, 26, 32, device, "voltage_reference", logger)
            self.active_load = sub_optional_float(row, 33, 40, device, "active_load", logger, 0.0)
            self.reactive_load = sub_optional_float(row, 41, 48, device, "reactive_load", logger, 0.0)
            self.active_gen = sub_optional_float(row, 49, 56, device, "active_gen", logger)
            self.reactive_gen = sub_optional_float(row, 57, 64, device, "reactive_gen", logger)
            self.min_gen_mw = sub_optional_float(row, 65, 72, device, "min_gen_mw", logger)
            self.max_gen_mw = sub_optional_float(row, 73, 80, device, "max_gen_mw", logger)
            self.min_gen_mvar = sub_optional_float(row, 81, 88, device, "min_gen_mvar", logger)
            self.max_gen_mvar = sub_optional_float(row, 89, 96, device, "max_gen_mvar", logger)
            self.static_primary_control = sub_optional_float(row, 97, 102, device, "static_primary_control", logger)
            self.nominal_power_primary_control = sub_optional_float(
                row, 103, 110, device, "nominal_power_primary_control", logger
            )
            self.short_circuit_power = sub_optional_float(row, 111, 118, device, "short_circuit_power", logger)
            self.xr_ratio = sub_optional_float(row, 119, 126, device, "xr_ratio", logger)
            self.plant_type = sub_str(row, 127, 128, device, "", logger)
        else:
            logger.add_warning("Non canonical line formatting, using tolerant tokenization",
                               device_class=device,
                               value=len(row),
                               expected_value=128)

            chunks = ucte_split(row, prefix_lengths=(8, 12), total_fields=18)

            if len(chunks) >= 1:
                self.node_code = chunks[0]

            if len(chunks) >= 2:
                self.geo_name = chunks[1]

            if len(chunks) >= 3:
                self.status = try_int(chunks[2], device, "status", logger)

            if len(chunks) >= 4:
                self.node_type = try_int(chunks[3], device, "node_type", logger)

            if len(chunks) >= 5:
                self.voltage_reference = try_optional_float(chunks[4], device, "voltage_reference", logger)

            if len(chunks) >= 6:
                self.active_load = try_optional_float(chunks[5], device, "active_load", logger, 0.0)

            if len(chunks) >= 7:
                self.reactive_load = try_optional_float(chunks[6], device, "reactive_load", logger, 0.0)

            if len(chunks) >= 8:
                self.active_gen = try_optional_float(chunks[7], device, "active_gen", logger)

            if len(chunks) >= 9:
                self.reactive_gen = try_optional_float(chunks[8], device, "reactive_gen", logger)

            if len(chunks) >= 10:
                self.min_gen_mw = try_optional_float(chunks[9], device, "min_gen_mw", logger)

            if len(chunks) >= 11:
                self.max_gen_mw = try_optional_float(chunks[10], device, "max_gen_mw", logger)

            if len(chunks) >= 12:
                self.min_gen_mvar = try_optional_float(chunks[11], device, "min_gen_mvar", logger)

            if len(chunks) >= 13:
                self.max_gen_mvar = try_optional_float(chunks[12], device, "max_gen_mvar", logger)

            if len(chunks) >= 14:
                self.static_primary_control = try_optional_float(
                    chunks[13], device, "static_primary_control", logger
                )

            if len(chunks) >= 15:
                self.nominal_power_primary_control = try_optional_float(
                    chunks[14], device, "nominal_power_primary_control", logger
                )

            if len(chunks) >= 16:
                self.short_circuit_power = try_optional_float(chunks[15], device, "short_circuit_power", logger)

            if len(chunks) >= 17:
                self.xr_ratio = try_optional_float(chunks[16], device, "xr_ratio", logger)

            if len(chunks) >= 18:
                self.plant_type = chunks[17]

        self.voltage = self._parse_nominal_voltage(logger)
        self.normalize(logger)
