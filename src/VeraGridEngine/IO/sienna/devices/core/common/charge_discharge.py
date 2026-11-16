# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ChargeDischarge schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaChargeDischarge(SiennaSchemaModel):
    """Expose every declared ChargeDischarge property through fixed slots."""

    __slots__ = ('charge', 'discharge',)

    def __init__(self, charge: float, discharge: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.charge: float = charge
        self.discharge: float = discharge


def parse_sienna_charge_discharge(data: dict[str, Any]) -> SiennaChargeDischarge:
    """Parse declared ChargeDischarge properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ChargeDischarge object.
    """
    return SiennaChargeDischarge(charge=get_required_value(data, 'charge', 'ChargeDischarge'), discharge=get_required_value(data, 'discharge', 'ChargeDischarge'))


def sienna_charge_discharge_to_json(value: SiennaChargeDischarge) -> dict[str, Any]:
    """Write every ChargeDischarge slot to explicit schema property names.

    :param value: Typed ChargeDischarge object.
    :return: JSON object with declared schema properties.
    """
    return {'charge': value.charge, 'discharge': value.discharge}
