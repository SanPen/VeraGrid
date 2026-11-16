# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ReactivePowerDroop schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaReactivePowerDroop(SiennaSchemaModel):
    """Expose every declared ReactivePowerDroop property through fixed slots."""

    __slots__ = ('kq', 'omegaf', 'V_ref',)

    def __init__(self, kq: float, omegaf: float, V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.kq: float = kq
        self.omegaf: float = omegaf
        self.V_ref: float = V_ref


def parse_sienna_reactive_power_droop(data: dict[str, Any]) -> SiennaReactivePowerDroop:
    """Parse declared ReactivePowerDroop properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ReactivePowerDroop object.
    """
    return SiennaReactivePowerDroop(kq=get_required_value(data, 'kq', 'ReactivePowerDroop'), omegaf=get_required_value(data, 'omegaf', 'ReactivePowerDroop'), V_ref=data.get('V_ref', None))


def sienna_reactive_power_droop_to_json(value: SiennaReactivePowerDroop) -> dict[str, Any]:
    """Write every ReactivePowerDroop slot to explicit schema property names.

    :param value: Typed ReactivePowerDroop object.
    :return: JSON object with declared schema properties.
    """
    return {'kq': value.kq, 'omegaf': value.omegaf, 'V_ref': value.V_ref}
