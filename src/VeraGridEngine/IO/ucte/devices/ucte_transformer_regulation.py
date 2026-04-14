# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.IO.ucte.devices.ucte_base import sub_int, sub_str, sub_float, try_int, try_float
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
        self.delta_u1 = 0.0  # 20-24: δu1 (%)
        self.n1 = 0  # 26-27: Number of taps (n1)
        self.n1_prime = 0  # 29-31: Alternate taps (n1')
        self.u1 = 0.0  # 33-37: U1 (kV, optional)

        # Angle regulation
        self.delta_u2 = 0.0  # 39-43: δu2 (%)
        self.theta = 0.0  # 45-49: Θ (°)
        self.n2 = 0  # 51-52: Number of taps (n2)
        self.n2_prime = 0  # 54-56: Alternate taps (n2')
        self.p = 0.0  # 58-62: P (MW, optional)
        self.regulation_type = ""  # 64-67: Regulation type (ASYM, SYMM)

        self.valid_regulation = True  # assume true for now...

    def get_primary_key(self):
        """
        Get a transformer primary key
        :return:
        """
        return f"{self.node1}_{self.node2}_{self.order_code}"

    def parse(self, line: str, logger: Logger):
        """

        :param line:
        :param logger:
        :return:
        """

        device = "TransformerRegulation"

        if len(line) == 69:
            self.node1 = sub_str(line, 0, 8, device, "node1", logger)
            self.node2 = sub_str(line, 9, 17, device, "node2", logger)
            self.order_code = sub_str(line, 18, 19, device, "order_code", logger)

            self.delta_u1 = sub_float(line, 20, 25, device, "delta_u1", logger)
            self.n1 = sub_int(line, 26, 28, device, "n1", logger)
            self.n1_prime = sub_int(line, 29, 32, device, "n1_prime", logger)
            self.u1 = sub_float(line, 33, 38, device, "u1", logger)

            self.delta_u2 = sub_float(line, 39, 44, device, "delta_u2", logger)
            self.theta = sub_float(line, 45, 50, device, "theta", logger)
            self.n2 = sub_int(line, 51, 53, device, "n2", logger)
            self.n2_prime = sub_int(line, 54, 57, device, "n2_prime", logger)
            self.p = sub_float(line, 58, 63, device, "p", logger)
            self.regulation_type = sub_str(line, 64, 68, device, "regulation_type", logger)
        else:

            logger.add_warning("Non canonical line length",
                               device_class=device,
                               value=len(line),
                               expected_value=128)

            chunks = line.split()

            if len(chunks) >= 1:
                self.node1 = chunks[0]

            if len(chunks) >= 2:
                self.node2 = chunks[1]

            if len(chunks) >= 3:
                self.order_code = chunks[2]

            if len(chunks) >= 4:
                self.delta_u1 = try_float(chunks[3], device, "delta_u1", logger)

            if len(chunks) >= 5:
                self.n1 = try_int(chunks[4], device, "n1", logger)

            if len(chunks) >= 6:
                self.n1_prime = try_int(chunks[5], device, "n1_prime", logger)

            if len(chunks) >= 7:
                self.u1 = try_float(chunks[6], device, "u1", logger)

            if len(chunks) >= 8:
                self.delta_u2 = try_float(chunks[7], device, "delta_u2", logger)

            if len(chunks) >= 9:
                self.theta = try_float(chunks[8], device, "theta", logger)

            if len(chunks) >= 10:
                self.n2 = try_int(chunks[9], device, "n2", logger)

            if len(chunks) >= 11:
                self.n2_prime = try_int(chunks[10], device, "n2_prime", logger)

            if len(chunks) >= 12:
                self.p = try_float(chunks[11], device, "p", logger)

            if len(chunks) >= 13:
                self.regulation_type = chunks[12]

        if self.n1 == 0:
            self.valid_regulation = False

        if self.n2 == 0:
            self.valid_regulation = False
