# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ActivePowerDroop schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaActivePowerDroop(SiennaSchemaModel):
    """Expose every declared ActivePowerDroop property through fixed slots."""

    __slots__ = ('Rp', 'omegaz', 'P_ref',)

    def __init__(self, Rp: float, omegaz: float, P_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.Rp: float = Rp
        self.omegaz: float = omegaz
        self.P_ref: float = P_ref


def parse_sienna_active_power_droop(data: dict[str, Any]) -> SiennaActivePowerDroop:
    """Parse declared ActivePowerDroop properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ActivePowerDroop object.
    """
    return SiennaActivePowerDroop(Rp=get_required_value(data, 'Rp', 'ActivePowerDroop'), omegaz=get_required_value(data, 'omegaz', 'ActivePowerDroop'), P_ref=data.get('P_ref', None))


def sienna_active_power_droop_to_json(value: SiennaActivePowerDroop) -> dict[str, Any]:
    """Write every ActivePowerDroop slot to explicit schema property names.

    :param value: Typed ActivePowerDroop object.
    :return: JSON object with declared schema properties.
    """
    return {'Rp': value.Rp, 'omegaz': value.omegaz, 'P_ref': value.P_ref}
