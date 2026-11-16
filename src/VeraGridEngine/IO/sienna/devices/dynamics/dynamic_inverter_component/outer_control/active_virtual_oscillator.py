# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ActiveVirtualOscillator schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaActiveVirtualOscillator(SiennaSchemaModel):
    """Expose every declared ActiveVirtualOscillator property through fixed slots."""

    __slots__ = ('k1', 'psi', 'P_ref',)

    def __init__(self, k1: float, psi: float, P_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.k1: float = k1
        self.psi: float = psi
        self.P_ref: float = P_ref


def parse_sienna_active_virtual_oscillator(data: dict[str, Any]) -> SiennaActiveVirtualOscillator:
    """Parse declared ActiveVirtualOscillator properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ActiveVirtualOscillator object.
    """
    return SiennaActiveVirtualOscillator(k1=get_required_value(data, 'k1', 'ActiveVirtualOscillator'), psi=get_required_value(data, 'psi', 'ActiveVirtualOscillator'), P_ref=data.get('P_ref', None))


def sienna_active_virtual_oscillator_to_json(value: SiennaActiveVirtualOscillator) -> dict[str, Any]:
    """Write every ActiveVirtualOscillator slot to explicit schema property names.

    :param value: Typed ActiveVirtualOscillator object.
    :return: JSON object with declared schema properties.
    """
    return {'k1': value.k1, 'psi': value.psi, 'P_ref': value.P_ref}
