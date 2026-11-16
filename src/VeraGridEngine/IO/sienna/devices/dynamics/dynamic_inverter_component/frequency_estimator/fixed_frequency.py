# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna FixedFrequency schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaFixedFrequency(SiennaSchemaModel):
    """Expose every declared FixedFrequency property through fixed slots."""

    __slots__ = ('frequency',)

    def __init__(self, frequency: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.frequency: float = frequency


def parse_sienna_fixed_frequency(data: dict[str, Any]) -> SiennaFixedFrequency:
    """Parse declared FixedFrequency properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed FixedFrequency object.
    """
    return SiennaFixedFrequency(frequency=data.get('frequency', None))


def sienna_fixed_frequency_to_json(value: SiennaFixedFrequency) -> dict[str, Any]:
    """Write every FixedFrequency slot to explicit schema property names.

    :param value: Typed FixedFrequency object.
    :return: JSON object with declared schema properties.
    """
    return {'frequency': value.frequency}
