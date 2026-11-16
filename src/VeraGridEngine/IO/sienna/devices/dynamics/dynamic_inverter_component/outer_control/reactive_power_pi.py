# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ReactivePowerPI schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaReactivePowerPI(SiennaSchemaModel):
    """Expose every declared ReactivePowerPI property through fixed slots."""

    __slots__ = ('Kp_q', 'Ki_q', 'omegaf', 'V_ref', 'Q_ref',)

    def __init__(self, Kp_q: float, Ki_q: float, omegaf: float, V_ref: float, Q_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.Kp_q: float = Kp_q
        self.Ki_q: float = Ki_q
        self.omegaf: float = omegaf
        self.V_ref: float = V_ref
        self.Q_ref: float = Q_ref


def parse_sienna_reactive_power_pi(data: dict[str, Any]) -> SiennaReactivePowerPI:
    """Parse declared ReactivePowerPI properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ReactivePowerPI object.
    """
    return SiennaReactivePowerPI(Kp_q=get_required_value(data, 'Kp_q', 'ReactivePowerPI'), Ki_q=get_required_value(data, 'Ki_q', 'ReactivePowerPI'), omegaf=get_required_value(data, 'omegaf', 'ReactivePowerPI'), V_ref=data.get('V_ref', None), Q_ref=data.get('Q_ref', None))


def sienna_reactive_power_pi_to_json(value: SiennaReactivePowerPI) -> dict[str, Any]:
    """Write every ReactivePowerPI slot to explicit schema property names.

    :param value: Typed ReactivePowerPI object.
    :return: JSON object with declared schema properties.
    """
    return {'Kp_q': value.Kp_q, 'Ki_q': value.Ki_q, 'omegaf': value.omegaf, 'V_ref': value.V_ref, 'Q_ref': value.Q_ref}
