# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import math

from VeraGridEngine.IO.ucte.devices.ucte_base import (
    sub_float,
    sub_int,
    sub_optional_float,
    sub_str,
    try_float,
    try_int,
    try_optional_float,
    ucte_split,
)
from VeraGridEngine.basic_structures import Logger


class UcteLine:
    """
    UcteLine
    """

    def __init__(self):
        self.node1 = ""  # 0-7: Node 1 code
        self.node2 = ""  # 9-16: Node 2 code
        self.order_code = ""  # 18: Order code

        self.status = 0  # 20: Status

        self.resistance = 0.0  # 22-27: Resistance (Ω)
        self.reactance = 0.0  # 29-34: Reactance (Ω)
        self.susceptance = 0.0  # 36-43: Susceptance (µS)
        self.current_limit = math.nan  # 45-50: Current limit (A)
        self.name = ""

    def _looks_fixed_width(self, line: str) -> bool:
        """
        Check whether one line record preserves the canonical fixed-width prefix.

        The UCTE name field is free text at the tail of the row, so valid records
        can be longer than the historical 66-character minimum. What matters for
        canonical parsing is that the fixed-width separators before the name are
        still present.
        """
        return (
            len(line) >= 51
            and line[8:9].isspace()
            and line[17:18].isspace()
            and line[19:20].isspace()
            and line[21:22].isspace()
            and line[28:29].isspace()
            and line[35:36].isspace()
            and line[44:45].isspace()
        )

    def is_active_and_reducible(self, logger: Logger) -> tuple[bool, bool]:
        """
        Returns if this line is active and/or reducible
        :return: active, reducible
        """

        """
        Status
        0: real element in operation (R, X only positive values permitted)
        8: real element out of operation (R, X only positive values permitted)
        1: equivalent element in operation
        9: equivalent element out of operation        
        2: busbar coupler in operation (definition: R=0, X=0, B=0)
        7: busbar coupler out of operation (definition: R=0, X=0, B=0)
        """
        if self.status == 0:
            return True, False
        elif self.status == 8:
            return False, False
        elif self.status == 1:
            return True, False
        elif self.status == 9:
            return False, False
        elif self.status == 2:
            return True, True
        elif self.status == 7:
            return False, True
        else:
            logger.add_error(msg="Unrecognized status",
                             value=str(self.status),
                             expected_value="0, 1, 2, 7, 8, 9",
                             device_class="Line")
            return True, False

    def parse(self, line: str, logger: Logger):
        """

        :param line:
        :param logger:
        :return:
        """

        device = "Line"
        if self._looks_fixed_width(line):
            # canonical parsing
            self.node1 = sub_str(line, 0, 8, device, "node1", logger)
            self.node2 = sub_str(line, 9, 17, device, "node2", logger)
            self.order_code = sub_str(line, 18, 19, device, "", logger)
            self.status = sub_int(line, 20, 21, device, "status", logger)
            self.resistance = sub_float(line, 22, 28, device, "resistance", logger)
            self.reactance = sub_float(line, 29, 35, device, "reactance", logger)
            self.susceptance = sub_float(line, 36, 44, device, "susceptance", logger)
            self.current_limit = sub_optional_float(line, 45, 51, device, "current_limit", logger)
            self.name = sub_str(line, 53, len(line), device, "name", logger)
        else:
            logger.add_warning("Non canonical line length",
                               device_class=device,
                               value=len(line),
                               expected_value=66)

            chunks = ucte_split(line, prefix_lengths=(8, 8, 1), total_fields=9, greedy_tail=True,
                                skip_all_separators=True)

            if len(chunks) >= 1:
                self.node1 = chunks[0].strip()

            if len(chunks) >= 2:
                self.node2 = chunks[1].strip()

            if len(chunks) >= 3:
                self.order_code = chunks[2].strip()

            if len(chunks) >= 4:
                self.status = try_int(chunks[3].strip(), device, "status", logger)

            if len(chunks) >= 5:
                self.resistance = try_float(chunks[4].strip(), device, "resistance", logger)

            if len(chunks) >= 6:
                self.reactance = try_float(chunks[5].strip(), device, "reactance", logger)

            if len(chunks) >= 7:
                self.susceptance = try_float(chunks[6].strip(), device, "susceptance", logger)

            if len(chunks) >= 8:
                self.current_limit = try_optional_float(chunks[7].strip(), device, "current_limit", logger)

            if len(chunks) >= 9:
                self.name = chunks[8].strip()

        if math.isfinite(self.current_limit) and self.current_limit < 0:
            self.current_limit = math.nan
