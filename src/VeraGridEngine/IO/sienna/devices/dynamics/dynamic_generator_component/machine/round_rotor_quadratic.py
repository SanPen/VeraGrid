# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna RoundRotorQuadratic schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaRoundRotorQuadratic(SiennaSchemaModel):
    """Expose every declared RoundRotorQuadratic property through fixed slots."""

    __slots__ = ('id', 'base_machine', 'saturation_coeffs',)

    def __init__(self, id: int, base_machine: int, saturation_coeffs: list[float]) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.base_machine: int = base_machine
        self.saturation_coeffs: list[float] = saturation_coeffs


def parse_sienna_round_rotor_quadratic(data: dict[str, Any]) -> SiennaRoundRotorQuadratic:
    """Parse declared RoundRotorQuadratic properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed RoundRotorQuadratic object.
    """
    return SiennaRoundRotorQuadratic(id=get_required_value(data, 'id', 'RoundRotorQuadratic'), base_machine=get_required_value(data, 'base_machine', 'RoundRotorQuadratic'), saturation_coeffs=get_required_value(data, 'saturation_coeffs', 'RoundRotorQuadratic'))


def sienna_round_rotor_quadratic_to_json(value: SiennaRoundRotorQuadratic) -> dict[str, Any]:
    """Write every RoundRotorQuadratic slot to explicit schema property names.

    :param value: Typed RoundRotorQuadratic object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'base_machine': value.base_machine, 'saturation_coeffs': value.saturation_coeffs}
