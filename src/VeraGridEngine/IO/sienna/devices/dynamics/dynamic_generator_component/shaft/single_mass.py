# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna SingleMass schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaSingleMass(SiennaSchemaModel):
    """Expose every declared SingleMass property through fixed slots."""

    __slots__ = ('id', 'H', 'D',)

    def __init__(self, id: int, H: float, D: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.H: float = H
        self.D: float = D


def parse_sienna_single_mass(data: dict[str, Any]) -> SiennaSingleMass:
    """Parse declared SingleMass properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed SingleMass object.
    """
    return SiennaSingleMass(id=get_required_value(data, 'id', 'SingleMass'), H=get_required_value(data, 'H', 'SingleMass'), D=get_required_value(data, 'D', 'SingleMass'))


def sienna_single_mass_to_json(value: SiennaSingleMass) -> dict[str, Any]:
    """Write every SingleMass slot to explicit schema property names.

    :param value: Typed SingleMass object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'H': value.H, 'D': value.D}
