# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ReducedOrderPLL schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaReducedOrderPLL(SiennaSchemaModel):
    """Expose every declared ReducedOrderPLL property through fixed slots."""

    __slots__ = ('omega_lp', 'kp_pll', 'ki_pll',)

    def __init__(self, omega_lp: float, kp_pll: float, ki_pll: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.omega_lp: float = omega_lp
        self.kp_pll: float = kp_pll
        self.ki_pll: float = ki_pll


def parse_sienna_reduced_order_pll(data: dict[str, Any]) -> SiennaReducedOrderPLL:
    """Parse declared ReducedOrderPLL properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ReducedOrderPLL object.
    """
    return SiennaReducedOrderPLL(omega_lp=get_required_value(data, 'omega_lp', 'ReducedOrderPLL'), kp_pll=get_required_value(data, 'kp_pll', 'ReducedOrderPLL'), ki_pll=get_required_value(data, 'ki_pll', 'ReducedOrderPLL'))


def sienna_reduced_order_pll_to_json(value: SiennaReducedOrderPLL) -> dict[str, Any]:
    """Write every ReducedOrderPLL slot to explicit schema property names.

    :param value: Typed ReducedOrderPLL object.
    :return: JSON object with declared schema properties.
    """
    return {'omega_lp': value.omega_lp, 'kp_pll': value.kp_pll, 'ki_pll': value.ki_pll}
