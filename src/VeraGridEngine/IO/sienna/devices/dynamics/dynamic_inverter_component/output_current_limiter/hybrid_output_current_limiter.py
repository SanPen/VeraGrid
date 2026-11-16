# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna HybridOutputCurrentLimiter schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaHybridOutputCurrentLimiter(SiennaSchemaModel):
    """Expose every declared HybridOutputCurrentLimiter property through fixed slots."""

    __slots__ = ('I_max', 'rv', 'lv',)

    def __init__(self, I_max: float, rv: float, lv: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.I_max: float = I_max
        self.rv: float = rv
        self.lv: float = lv


def parse_sienna_hybrid_output_current_limiter(data: dict[str, Any]) -> SiennaHybridOutputCurrentLimiter:
    """Parse declared HybridOutputCurrentLimiter properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed HybridOutputCurrentLimiter object.
    """
    return SiennaHybridOutputCurrentLimiter(I_max=get_required_value(data, 'I_max', 'HybridOutputCurrentLimiter'), rv=get_required_value(data, 'rv', 'HybridOutputCurrentLimiter'), lv=get_required_value(data, 'lv', 'HybridOutputCurrentLimiter'))


def sienna_hybrid_output_current_limiter_to_json(value: SiennaHybridOutputCurrentLimiter) -> dict[str, Any]:
    """Write every HybridOutputCurrentLimiter slot to explicit schema property names.

    :param value: Typed HybridOutputCurrentLimiter object.
    :return: JSON object with declared schema properties.
    """
    return {'I_max': value.I_max, 'rv': value.rv, 'lv': value.lv}
