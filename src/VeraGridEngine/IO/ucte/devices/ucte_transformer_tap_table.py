# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.IO.ucte.devices.ucte_base import sub_int, sub_str, sub_float, try_int, try_float
from VeraGridEngine.basic_structures import Logger


class UcteTransformerTapTable:
    """

    """
    def __init__(self):
        self.node1 = ""  # 0-7: Node 1 code
        self.node2 = ""  # 9-16: Node 2 code
        self.order_code = ""  # 18: Order code
        self.tap_position = 0  # 22-24: Tap position (n')
        self.resistance = 0.0  # 26-31: Resistance (Ω)
        self.reactance = 0.0  # 33-38: Reactance (Ω)
        self.delta_u = 0.0  # 40-44: Voltage deviation (%)
        self.phase_shift = 0.0  # 46-50: Phase shift angle (°)

    def get_primary_key(self):
        """
        Get a transformer primary key
        :return:
        """
        return f"{self.node1}_{self.node2}_{self.order_code}"

    def parse(self, line, logger: Logger):
        """

        :param line:
        :param logger:
        :return:
        """
        device = "TransformerTapTable"
        if len(line) == 52:
            self.node1 = sub_str(line, 0, 8, device, "node1", logger)
            self.node2 = sub_str(line, 9, 17, device, "node2", logger)
            self.order_code = sub_str(line, 18, 19, device, "order_code", logger)
            self.tap_position = sub_int(line, 22, 25, device, "tap_position", logger)
            self.resistance = sub_float(line, 26, 32, device, "resistance", logger)
            self.reactance = sub_float(line, 33, 39, device, "reactance", logger)
            self.delta_u = sub_float(line, 40, 45, device, "delta_u", logger)
            self.phase_shift = sub_float(line, 46, 51, device, "phase_shift", logger)
        else:

            logger.add_warning("Non canonical line length",
                               device_class=device,
                               value=len(line),
                               expected_value=52)

            chunks = line.split()

            if len(chunks) >= 1:
                self.node1 = chunks[0]

            if len(chunks) >= 2:
                self.node2 = chunks[1]

            if len(chunks) >= 3:
                self.order_code = chunks[2]

            if len(chunks) >= 4:
                self.tap_position = try_int(chunks[3], device, "tap_position", logger)

            if len(chunks) >= 5:
                self.resistance = try_float(chunks[4], device, "resistance", logger)

            if len(chunks) >= 6:
                self.reactance = try_float(chunks[5], device, "reactance", logger)

            if len(chunks) >= 7:
                self.delta_u = try_float(chunks[6], device, "delta_u", logger)

            if len(chunks) >= 8:
                self.phase_shift = try_float(chunks[7], device, "phase_shift", logger)
