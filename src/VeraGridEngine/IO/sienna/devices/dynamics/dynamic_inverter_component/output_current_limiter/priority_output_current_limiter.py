# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna PriorityOutputCurrentLimiter schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaPriorityOutputCurrentLimiter(SiennaSchemaModel):
    """Expose every declared PriorityOutputCurrentLimiter property through fixed slots."""

    __slots__ = ('I_max', 'phi_I',)

    def __init__(self, I_max: float, phi_I: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.I_max: float = I_max
        self.phi_I: float = phi_I


def parse_sienna_priority_output_current_limiter(data: dict[str, Any]) -> SiennaPriorityOutputCurrentLimiter:
    """Parse declared PriorityOutputCurrentLimiter properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed PriorityOutputCurrentLimiter object.
    """
    return SiennaPriorityOutputCurrentLimiter(I_max=get_required_value(data, 'I_max', 'PriorityOutputCurrentLimiter'), phi_I=get_required_value(data, 'phi_I', 'PriorityOutputCurrentLimiter'))


def sienna_priority_output_current_limiter_to_json(value: SiennaPriorityOutputCurrentLimiter) -> dict[str, Any]:
    """Write every PriorityOutputCurrentLimiter slot to explicit schema property names.

    :param value: Typed PriorityOutputCurrentLimiter object.
    :return: JSON object with declared schema properties.
    """
    return {'I_max': value.I_max, 'phi_I': value.phi_I}
