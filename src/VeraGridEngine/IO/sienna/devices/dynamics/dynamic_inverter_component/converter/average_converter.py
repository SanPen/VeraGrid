# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna AverageConverter schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaAverageConverter(SiennaSchemaModel):
    """Expose every declared AverageConverter property through fixed slots."""

    __slots__ = ('rated_voltage', 'rated_current',)

    def __init__(self, rated_voltage: float, rated_current: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.rated_voltage: float = rated_voltage
        self.rated_current: float = rated_current


def parse_sienna_average_converter(data: dict[str, Any]) -> SiennaAverageConverter:
    """Parse declared AverageConverter properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed AverageConverter object.
    """
    return SiennaAverageConverter(rated_voltage=get_required_value(data, 'rated_voltage', 'AverageConverter'), rated_current=get_required_value(data, 'rated_current', 'AverageConverter'))


def sienna_average_converter_to_json(value: SiennaAverageConverter) -> dict[str, Any]:
    """Write every AverageConverter slot to explicit schema property names.

    :param value: Typed AverageConverter object.
    :return: JSON object with declared schema properties.
    """
    return {'rated_voltage': value.rated_voltage, 'rated_current': value.rated_current}
