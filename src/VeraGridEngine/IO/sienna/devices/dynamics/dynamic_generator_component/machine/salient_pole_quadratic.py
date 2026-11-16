# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna SalientPoleQuadratic schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaSalientPoleQuadratic(SiennaSchemaModel):
    """Expose every declared SalientPoleQuadratic property through fixed slots."""

    __slots__ = ('id', 'base_machine', 'saturation_coeffs',)

    def __init__(self, id: int, base_machine: int, saturation_coeffs: list[float]) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.base_machine: int = base_machine
        self.saturation_coeffs: list[float] = saturation_coeffs


def parse_sienna_salient_pole_quadratic(data: dict[str, Any]) -> SiennaSalientPoleQuadratic:
    """Parse declared SalientPoleQuadratic properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed SalientPoleQuadratic object.
    """
    return SiennaSalientPoleQuadratic(id=get_required_value(data, 'id', 'SalientPoleQuadratic'), base_machine=get_required_value(data, 'base_machine', 'SalientPoleQuadratic'), saturation_coeffs=get_required_value(data, 'saturation_coeffs', 'SalientPoleQuadratic'))


def sienna_salient_pole_quadratic_to_json(value: SiennaSalientPoleQuadratic) -> dict[str, Any]:
    """Write every SalientPoleQuadratic slot to explicit schema property names.

    :param value: Typed SalientPoleQuadratic object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'base_machine': value.base_machine, 'saturation_coeffs': value.saturation_coeffs}
