# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ActivePowerPI schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaActivePowerPI(SiennaSchemaModel):
    """Expose every declared ActivePowerPI property through fixed slots."""

    __slots__ = ('Kp_p', 'Ki_p', 'omegaz', 'P_ref',)

    def __init__(self, Kp_p: float, Ki_p: float, omegaz: float, P_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.Kp_p: float = Kp_p
        self.Ki_p: float = Ki_p
        self.omegaz: float = omegaz
        self.P_ref: float = P_ref


def parse_sienna_active_power_pi(data: dict[str, Any]) -> SiennaActivePowerPI:
    """Parse declared ActivePowerPI properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ActivePowerPI object.
    """
    return SiennaActivePowerPI(Kp_p=get_required_value(data, 'Kp_p', 'ActivePowerPI'), Ki_p=get_required_value(data, 'Ki_p', 'ActivePowerPI'), omegaz=get_required_value(data, 'omegaz', 'ActivePowerPI'), P_ref=data.get('P_ref', None))


def sienna_active_power_pi_to_json(value: SiennaActivePowerPI) -> dict[str, Any]:
    """Write every ActivePowerPI slot to explicit schema property names.

    :param value: Typed ActivePowerPI object.
    :return: JSON object with declared schema properties.
    """
    return {'Kp_p': value.Kp_p, 'Ki_p': value.Ki_p, 'omegaz': value.omegaz, 'P_ref': value.P_ref}
