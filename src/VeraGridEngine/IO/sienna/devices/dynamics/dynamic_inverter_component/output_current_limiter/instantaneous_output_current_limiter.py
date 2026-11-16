# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna InstantaneousOutputCurrentLimiter schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaInstantaneousOutputCurrentLimiter(SiennaSchemaModel):
    """Expose every declared InstantaneousOutputCurrentLimiter property through fixed slots."""

    __slots__ = ('Id_max', 'Iq_max',)

    def __init__(self, Id_max: float, Iq_max: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.Id_max: float = Id_max
        self.Iq_max: float = Iq_max


def parse_sienna_instantaneous_output_current_limiter(data: dict[str, Any]) -> SiennaInstantaneousOutputCurrentLimiter:
    """Parse declared InstantaneousOutputCurrentLimiter properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed InstantaneousOutputCurrentLimiter object.
    """
    return SiennaInstantaneousOutputCurrentLimiter(Id_max=get_required_value(data, 'Id_max', 'InstantaneousOutputCurrentLimiter'), Iq_max=get_required_value(data, 'Iq_max', 'InstantaneousOutputCurrentLimiter'))


def sienna_instantaneous_output_current_limiter_to_json(value: SiennaInstantaneousOutputCurrentLimiter) -> dict[str, Any]:
    """Write every InstantaneousOutputCurrentLimiter slot to explicit schema property names.

    :param value: Typed InstantaneousOutputCurrentLimiter object.
    :return: JSON object with declared schema properties.
    """
    return {'Id_max': value.Id_max, 'Iq_max': value.Iq_max}
