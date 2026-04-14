# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import math

from VeraGridEngine.IO.ucte.devices.ucte_base import (
    is_defined_number,
    sub_optional_float,
    sub_optional_int,
    sub_str,
    try_optional_float,
    try_optional_int,
    ucte_split,
)
from VeraGridEngine.basic_structures import Logger


class UcteTransformerRegulation:
    """
    UcteTransformerRegulation
    """

    def __init__(self):
        self.node1 = ""  # 0-7: Node 1 (non-regulated winding) To bus for VeraGrid
        self.node2 = ""  # 9-16: Node 2 (regulated winding) From bus for VeraGrid
        self.order_code = ""  # 18: Order code

        # Phase regulation
        self.delta_u1 = math.nan  # 20-24: δu1 (%)
        self.n1: int | None = None  # 26-27: Number of taps (n1)
        self.n1_prime: int | None = None  # 29-31: Alternate taps (n1')
        self.u1 = math.nan  # 33-37: U1 (kV, optional)

        # Angle regulation
        self.delta_u2 = math.nan  # 39-43: δu2 (%)
        self.theta = math.nan  # 45-49: Θ (°)
        self.n2: int | None = None  # 51-52: Number of taps (n2)
        self.n2_prime: int | None = None  # 54-56: Alternate taps (n2')
        self.p = math.nan  # 58-62: P (MW, optional)
        self.regulation_type = ""  # 64-67: Regulation type (ASYM, SYMM)

    @staticmethod
    def _get_voltage_window() -> tuple[float, float, float]:
        return 0.8, 1.2, 110.0

    def get_primary_key(self):
        """
        Get a transformer primary key.
        """
        return f"{self.node1}_{self.node2}_{self.order_code}"

    def has_phase_regulation(self) -> bool:
        return (
            self.n1 not in (None, 0)
            and self.n1_prime is not None
            and is_defined_number(self.delta_u1)
        )

    def has_angle_regulation(self) -> bool:
        return (
            self.n2 not in (None, 0)
            and self.n2_prime is not None
            and is_defined_number(self.delta_u2)
            and is_defined_number(self.theta)
        )

    def normalize(self, nominal_voltage: float | None, logger: Logger):
        device = self.get_primary_key()
        low_voltage_factor, high_voltage_factor, low_nominal_voltage = self._get_voltage_window()

        if self.n1 is not None and self.n1 < 0:
            logger.add_warning("Negative number of taps (N1), using its absolute value",
                               device=device,
                               value=self.n1)
            self.n1 = abs(self.n1)

        if self.n2 is not None and self.n2 < 0:
            logger.add_warning("Negative number of taps (N2), using its absolute value",
                               device=device,
                               value=self.n2)
            self.n2 = abs(self.n2)

        if self.has_phase_regulation():
            if self.n1 is not None and self.n1_prime is not None and abs(self.n1_prime) > self.n1:
                logger.add_warning("Phase tap range extended to current tap position",
                                   device=device,
                                   value=self.n1_prime,
                                   expected_value=self.n1)
                self.n1 = abs(self.n1_prime)

            if is_defined_number(self.u1) and self.u1 <= 0:
                logger.add_warning("Transformer phase-regulation target voltage is invalid, ignoring it",
                                   device=device,
                                   value=self.u1)
                self.u1 = math.nan

            if (
                is_defined_number(self.u1)
                and nominal_voltage is not None
                and nominal_voltage > low_nominal_voltage
                and (self.u1 < low_voltage_factor * nominal_voltage or self.u1 > high_voltage_factor * nominal_voltage)
            ):
                logger.add_warning("Transformer regulation target voltage is far from the nominal voltage",
                                   device=device,
                                   value=self.u1,
                                   expected_value=f"{low_voltage_factor * nominal_voltage:.2f}.."
                                                  f"{high_voltage_factor * nominal_voltage:.2f}")
        else:
            if any((
                is_defined_number(self.delta_u1),
                self.n1 not in (None, 0),
                self.n1_prime is not None,
                is_defined_number(self.u1),
            )):
                logger.add_warning("Incomplete phase regulation removed", device=device)

            self.delta_u1 = math.nan
            self.n1 = None
            self.n1_prime = None
            self.u1 = math.nan

        if self.has_angle_regulation():
            if self.n2 is not None and self.n2_prime is not None and abs(self.n2_prime) > self.n2:
                logger.add_warning("Angle tap range extended to current tap position",
                                   device=device,
                                   value=self.n2_prime,
                                   expected_value=self.n2)
                self.n2 = abs(self.n2_prime)

            if self.regulation_type == "":
                self.regulation_type = "ASYM"
                logger.add_warning("Missing angle regulation type, defaulting to ASYM", device=device)
            elif self.regulation_type not in ("ASYM", "SYMM"):
                logger.add_warning("Invalid angle regulation type, defaulting to ASYM",
                                   device=device,
                                   value=self.regulation_type,
                                   expected_value="ASYM or SYMM")
                self.regulation_type = "ASYM"
        else:
            if any((
                is_defined_number(self.delta_u2),
                is_defined_number(self.theta),
                self.n2 not in (None, 0),
                self.n2_prime is not None,
                is_defined_number(self.p),
                self.regulation_type != "",
            )):
                logger.add_warning("Incomplete angle regulation removed", device=device)

            self.delta_u2 = math.nan
            self.theta = math.nan
            self.n2 = None
            self.n2_prime = None
            self.p = math.nan
            self.regulation_type = ""

    def parse(self, line: str, logger: Logger):
        """
        Parse the regulation record.
        """
        device = "TransformerRegulation"
        row = line.rstrip("\r\n")

        if len(row) >= 68:
            self.node1 = sub_str(row, 0, 8, device, "node1", logger)
            self.node2 = sub_str(row, 9, 17, device, "node2", logger)
            self.order_code = sub_str(row, 18, 19, device, "order_code", logger)

            self.delta_u1 = sub_optional_float(row, 20, 25, device, "delta_u1", logger)
            self.n1 = sub_optional_int(row, 26, 28, device, "n1", logger)
            self.n1_prime = sub_optional_int(row, 29, 32, device, "n1_prime", logger)
            self.u1 = sub_optional_float(row, 33, 38, device, "u1", logger)

            self.delta_u2 = sub_optional_float(row, 39, 44, device, "delta_u2", logger)
            self.theta = sub_optional_float(row, 45, 50, device, "theta", logger)
            self.n2 = sub_optional_int(row, 51, 53, device, "n2", logger)
            self.n2_prime = sub_optional_int(row, 54, 57, device, "n2_prime", logger)
            self.p = sub_optional_float(row, 58, 63, device, "p", logger)
            self.regulation_type = sub_str(row, 64, 68, device, "regulation_type", logger).strip()
        else:
            logger.add_warning("Non canonical line length",
                               device_class=device,
                               value=len(row),
                               expected_value=68)

            chunks = ucte_split(row, prefix_lengths=(8, 8, 1), total_fields=13, skip_all_separators=True)

            if len(chunks) >= 1:
                self.node1 = chunks[0]

            if len(chunks) >= 2:
                self.node2 = chunks[1]

            if len(chunks) >= 3:
                self.order_code = chunks[2]

            if len(chunks) >= 4:
                self.delta_u1 = try_optional_float(chunks[3], device, "delta_u1", logger)

            if len(chunks) >= 5:
                self.n1 = try_optional_int(chunks[4], device, "n1", logger)

            if len(chunks) >= 6:
                self.n1_prime = try_optional_int(chunks[5], device, "n1_prime", logger)

            if len(chunks) >= 7:
                self.u1 = try_optional_float(chunks[6], device, "u1", logger)

            if len(chunks) >= 8:
                self.delta_u2 = try_optional_float(chunks[7], device, "delta_u2", logger)

            if len(chunks) >= 9:
                self.theta = try_optional_float(chunks[8], device, "theta", logger)

            if len(chunks) >= 10:
                self.n2 = try_optional_int(chunks[9], device, "n2", logger)

            if len(chunks) >= 11:
                self.n2_prime = try_optional_int(chunks[10], device, "n2_prime", logger)

            if len(chunks) >= 12:
                self.p = try_optional_float(chunks[11], device, "p", logger)

            if len(chunks) >= 13:
                self.regulation_type = chunks[12].strip()
