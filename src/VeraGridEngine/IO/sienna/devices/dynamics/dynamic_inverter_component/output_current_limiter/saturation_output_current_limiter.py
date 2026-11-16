# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna SaturationOutputCurrentLimiter schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaSaturationOutputCurrentLimiter(SiennaSchemaModel):
    """Expose every declared SaturationOutputCurrentLimiter property through fixed slots."""

    __slots__ = ('I_max', 'kw',)

    def __init__(self, I_max: float, kw: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.I_max: float = I_max
        self.kw: float = kw


def parse_sienna_saturation_output_current_limiter(data: dict[str, Any]) -> SiennaSaturationOutputCurrentLimiter:
    """Parse declared SaturationOutputCurrentLimiter properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed SaturationOutputCurrentLimiter object.
    """
    return SiennaSaturationOutputCurrentLimiter(I_max=get_required_value(data, 'I_max', 'SaturationOutputCurrentLimiter'), kw=get_required_value(data, 'kw', 'SaturationOutputCurrentLimiter'))


def sienna_saturation_output_current_limiter_to_json(value: SiennaSaturationOutputCurrentLimiter) -> dict[str, Any]:
    """Write every SaturationOutputCurrentLimiter slot to explicit schema property names.

    :param value: Typed SaturationOutputCurrentLimiter object.
    :return: JSON object with declared schema properties.
    """
    return {'I_max': value.I_max, 'kw': value.kw}
