# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna KauraPLL schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaKauraPLL(SiennaSchemaModel):
    """Expose every declared KauraPLL property through fixed slots."""

    __slots__ = ('omega_lp', 'kp_pll', 'ki_pll',)

    def __init__(self, omega_lp: float, kp_pll: float, ki_pll: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.omega_lp: float = omega_lp
        self.kp_pll: float = kp_pll
        self.ki_pll: float = ki_pll


def parse_sienna_kaura_pll(data: dict[str, Any]) -> SiennaKauraPLL:
    """Parse declared KauraPLL properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed KauraPLL object.
    """
    return SiennaKauraPLL(omega_lp=get_required_value(data, 'omega_lp', 'KauraPLL'), kp_pll=get_required_value(data, 'kp_pll', 'KauraPLL'), ki_pll=get_required_value(data, 'ki_pll', 'KauraPLL'))


def sienna_kaura_pll_to_json(value: SiennaKauraPLL) -> dict[str, Any]:
    """Write every KauraPLL slot to explicit schema property names.

    :param value: Typed KauraPLL object.
    :return: JSON object with declared schema properties.
    """
    return {'omega_lp': value.omega_lp, 'kp_pll': value.kp_pll, 'ki_pll': value.ki_pll}
