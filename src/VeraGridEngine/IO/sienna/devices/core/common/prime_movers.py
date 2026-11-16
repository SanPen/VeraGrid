# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna PrimeMovers schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaPrimeMovers(Enum):
    """Values declared by the Sienna PrimeMovers schema."""

    BA = 'BA'
    BT = 'BT'
    CA = 'CA'
    CC = 'CC'
    CE = 'CE'
    CP = 'CP'
    CS = 'CS'
    CT = 'CT'
    ES = 'ES'
    FC = 'FC'
    FW = 'FW'
    GT = 'GT'
    HA = 'HA'
    HB = 'HB'
    HK = 'HK'
    HY = 'HY'
    IC = 'IC'
    PS = 'PS'
    OT = 'OT'
    ST = 'ST'
    PVE = 'PVe'
    WT = 'WT'
    WS = 'WS'


def parse_sienna_prime_movers(data: str) -> SiennaPrimeMovers:
    """Parse one PrimeMovers enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaPrimeMovers(data)


def sienna_prime_movers_to_json(value: SiennaPrimeMovers) -> str:
    """Write one PrimeMovers enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
