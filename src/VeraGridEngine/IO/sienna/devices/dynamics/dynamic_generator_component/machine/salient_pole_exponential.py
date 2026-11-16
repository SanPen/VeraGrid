# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna SalientPoleExponential schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaSalientPoleExponential(SiennaSchemaModel):
    """Expose every declared SalientPoleExponential property through fixed slots."""

    __slots__ = ('id', 'base_machine', 'saturation_coeffs',)

    def __init__(self, id: int, base_machine: int, saturation_coeffs: list[float]) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.base_machine: int = base_machine
        self.saturation_coeffs: list[float] = saturation_coeffs


def parse_sienna_salient_pole_exponential(data: dict[str, Any]) -> SiennaSalientPoleExponential:
    """Parse declared SalientPoleExponential properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed SalientPoleExponential object.
    """
    return SiennaSalientPoleExponential(id=get_required_value(data, 'id', 'SalientPoleExponential'), base_machine=get_required_value(data, 'base_machine', 'SalientPoleExponential'), saturation_coeffs=get_required_value(data, 'saturation_coeffs', 'SalientPoleExponential'))


def sienna_salient_pole_exponential_to_json(value: SiennaSalientPoleExponential) -> dict[str, Any]:
    """Write every SalientPoleExponential slot to explicit schema property names.

    :param value: Typed SalientPoleExponential object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'base_machine': value.base_machine, 'saturation_coeffs': value.saturation_coeffs}
