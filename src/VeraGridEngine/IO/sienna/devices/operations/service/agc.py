# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna AGC schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaAGC(SiennaSchemaModel):
    """Expose every declared AGC property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'bias', 'K_p', 'K_i', 'K_d', 'delta_t', 'area', 'initial_ace',)

    def __init__(self, id: int, name: str, available: bool, bias: float, K_p: float, K_i: float, K_d: float, delta_t: float, area: int, initial_ace: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.bias: float = bias
        self.K_p: float = K_p
        self.K_i: float = K_i
        self.K_d: float = K_d
        self.delta_t: float = delta_t
        self.area: int = area
        self.initial_ace: float = initial_ace


def parse_sienna_agc(data: dict[str, Any]) -> SiennaAGC:
    """Parse declared AGC properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed AGC object.
    """
    return SiennaAGC(id=get_required_value(data, 'id', 'AGC'), name=get_required_value(data, 'name', 'AGC'), available=get_required_value(data, 'available', 'AGC'), bias=get_required_value(data, 'bias', 'AGC'), K_p=get_required_value(data, 'K_p', 'AGC'), K_i=get_required_value(data, 'K_i', 'AGC'), K_d=get_required_value(data, 'K_d', 'AGC'), delta_t=get_required_value(data, 'delta_t', 'AGC'), area=data.get('area', None), initial_ace=data.get('initial_ace', None))


def sienna_agc_to_json(value: SiennaAGC) -> dict[str, Any]:
    """Write every AGC slot to explicit schema property names.

    :param value: Typed AGC object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'name': value.name, 'available': value.available, 'bias': value.bias, 'K_p': value.K_p, 'K_i': value.K_i, 'K_d': value.K_d, 'delta_t': value.delta_t, 'area': value.area, 'initial_ace': value.initial_ace}
