# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna SimpleFullMachine schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaSimpleFullMachine(SiennaSchemaModel):
    """Expose every declared SimpleFullMachine property through fixed slots."""

    __slots__ = ('id', 'R', 'R_f', 'R_1d', 'R_1q', 'L_d', 'L_q', 'L_ad', 'L_aq', 'L_f1d', 'L_ff', 'L_1d', 'L_1q',)

    def __init__(self, id: int, R: float, R_f: float, R_1d: float, R_1q: float, L_d: float, L_q: float, L_ad: float, L_aq: float, L_f1d: float, L_ff: float, L_1d: float, L_1q: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.R: float = R
        self.R_f: float = R_f
        self.R_1d: float = R_1d
        self.R_1q: float = R_1q
        self.L_d: float = L_d
        self.L_q: float = L_q
        self.L_ad: float = L_ad
        self.L_aq: float = L_aq
        self.L_f1d: float = L_f1d
        self.L_ff: float = L_ff
        self.L_1d: float = L_1d
        self.L_1q: float = L_1q


def parse_sienna_simple_full_machine(data: dict[str, Any]) -> SiennaSimpleFullMachine:
    """Parse declared SimpleFullMachine properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed SimpleFullMachine object.
    """
    return SiennaSimpleFullMachine(id=get_required_value(data, 'id', 'SimpleFullMachine'), R=get_required_value(data, 'R', 'SimpleFullMachine'), R_f=get_required_value(data, 'R_f', 'SimpleFullMachine'), R_1d=get_required_value(data, 'R_1d', 'SimpleFullMachine'), R_1q=get_required_value(data, 'R_1q', 'SimpleFullMachine'), L_d=get_required_value(data, 'L_d', 'SimpleFullMachine'), L_q=get_required_value(data, 'L_q', 'SimpleFullMachine'), L_ad=get_required_value(data, 'L_ad', 'SimpleFullMachine'), L_aq=get_required_value(data, 'L_aq', 'SimpleFullMachine'), L_f1d=get_required_value(data, 'L_f1d', 'SimpleFullMachine'), L_ff=get_required_value(data, 'L_ff', 'SimpleFullMachine'), L_1d=get_required_value(data, 'L_1d', 'SimpleFullMachine'), L_1q=get_required_value(data, 'L_1q', 'SimpleFullMachine'))


def sienna_simple_full_machine_to_json(value: SiennaSimpleFullMachine) -> dict[str, Any]:
    """Write every SimpleFullMachine slot to explicit schema property names.

    :param value: Typed SimpleFullMachine object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'R': value.R, 'R_f': value.R_f, 'R_1d': value.R_1d, 'R_1q': value.R_1q, 'L_d': value.L_d, 'L_q': value.L_q, 'L_ad': value.L_ad, 'L_aq': value.L_aq, 'L_f1d': value.L_f1d, 'L_ff': value.L_ff, 'L_1d': value.L_1d, 'L_1q': value.L_1q}
