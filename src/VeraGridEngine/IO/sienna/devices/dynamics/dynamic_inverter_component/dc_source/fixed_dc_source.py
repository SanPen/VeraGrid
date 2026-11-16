# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna FixedDCSource schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaFixedDCSource(SiennaSchemaModel):
    """Expose every declared FixedDCSource property through fixed slots."""

    __slots__ = ('voltage',)

    def __init__(self, voltage: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.voltage: float = voltage


def parse_sienna_fixed_dc_source(data: dict[str, Any]) -> SiennaFixedDCSource:
    """Parse declared FixedDCSource properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed FixedDCSource object.
    """
    return SiennaFixedDCSource(voltage=get_required_value(data, 'voltage', 'FixedDCSource'))


def sienna_fixed_dc_source_to_json(value: SiennaFixedDCSource) -> dict[str, Any]:
    """Write every FixedDCSource slot to explicit schema property names.

    :param value: Typed FixedDCSource object.
    :return: JSON object with declared schema properties.
    """
    return {'voltage': value.voltage}
