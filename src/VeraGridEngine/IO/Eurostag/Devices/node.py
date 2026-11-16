# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from VeraGridEngine.IO.Eurostag.Devices.eurostag_base import slice_float, slice_text


class EurostagNode:
    PREFIX = "1"
    AREA = (1, 3)
    NAME = (3, 11)
    BASE_VOLTAGE = (84, 92)
    INITIAL_VOLTAGE = (98, 106)
    INITIAL_ANGLE = (107, 115)

    __slots__ = (
        "area",
        "name",
        "base_voltage",
        "initial_voltage",
        "initial_angle",
        "is_slack",
    )

    def __init__(self) -> None:
        self.area: str = ""
        self.name: str = ""
        self.base_voltage: float = 0.0
        self.initial_voltage: float = 0.0
        self.initial_angle: float = 0.0
        self.is_slack: bool = False

    def parse_line(self, line: str) -> None:
        self.area = slice_text(line, *self.AREA)
        self.name = slice_text(line, *self.NAME)
        self.base_voltage = slice_float(line, *self.BASE_VOLTAGE)
        self.initial_voltage = slice_float(line, *self.INITIAL_VOLTAGE)
        self.initial_angle = slice_float(line, *self.INITIAL_ANGLE)
