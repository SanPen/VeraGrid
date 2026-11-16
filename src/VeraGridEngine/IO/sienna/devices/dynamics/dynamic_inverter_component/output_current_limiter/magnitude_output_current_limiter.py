# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna MagnitudeOutputCurrentLimiter schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaMagnitudeOutputCurrentLimiter(SiennaSchemaModel):
    """Expose every declared MagnitudeOutputCurrentLimiter property through fixed slots."""

    __slots__ = ('I_max',)

    def __init__(self, I_max: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.I_max: float = I_max


def parse_sienna_magnitude_output_current_limiter(data: dict[str, Any]) -> SiennaMagnitudeOutputCurrentLimiter:
    """Parse declared MagnitudeOutputCurrentLimiter properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed MagnitudeOutputCurrentLimiter object.
    """
    return SiennaMagnitudeOutputCurrentLimiter(I_max=get_required_value(data, 'I_max', 'MagnitudeOutputCurrentLimiter'))


def sienna_magnitude_output_current_limiter_to_json(value: SiennaMagnitudeOutputCurrentLimiter) -> dict[str, Any]:
    """Write every MagnitudeOutputCurrentLimiter slot to explicit schema property names.

    :param value: Typed MagnitudeOutputCurrentLimiter object.
    :return: JSON object with declared schema properties.
    """
    return {'I_max': value.I_max}
