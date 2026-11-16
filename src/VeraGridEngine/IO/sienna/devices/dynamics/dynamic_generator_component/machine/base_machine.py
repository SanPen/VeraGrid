# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna BaseMachine schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaBaseMachine(SiennaSchemaModel):
    """Expose every declared BaseMachine property through fixed slots."""

    __slots__ = ('id', 'R', 'Xd_p', 'eq_p',)

    def __init__(self, id: int, R: float, Xd_p: float, eq_p: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.R: float = R
        self.Xd_p: float = Xd_p
        self.eq_p: float = eq_p


def parse_sienna_base_machine(data: dict[str, Any]) -> SiennaBaseMachine:
    """Parse declared BaseMachine properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed BaseMachine object.
    """
    return SiennaBaseMachine(id=get_required_value(data, 'id', 'BaseMachine'), R=get_required_value(data, 'R', 'BaseMachine'), Xd_p=get_required_value(data, 'Xd_p', 'BaseMachine'), eq_p=get_required_value(data, 'eq_p', 'BaseMachine'))


def sienna_base_machine_to_json(value: SiennaBaseMachine) -> dict[str, Any]:
    """Write every BaseMachine slot to explicit schema property names.

    :param value: Typed BaseMachine object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'R': value.R, 'Xd_p': value.Xd_p, 'eq_p': value.eq_p}
