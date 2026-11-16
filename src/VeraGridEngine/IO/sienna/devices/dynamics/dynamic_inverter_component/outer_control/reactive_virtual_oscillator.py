# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ReactiveVirtualOscillator schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaReactiveVirtualOscillator(SiennaSchemaModel):
    """Expose every declared ReactiveVirtualOscillator property through fixed slots."""

    __slots__ = ('k2', 'V_ref', 'Q_ref',)

    def __init__(self, k2: float, V_ref: float, Q_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.k2: float = k2
        self.V_ref: float = V_ref
        self.Q_ref: float = Q_ref


def parse_sienna_reactive_virtual_oscillator(data: dict[str, Any]) -> SiennaReactiveVirtualOscillator:
    """Parse declared ReactiveVirtualOscillator properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ReactiveVirtualOscillator object.
    """
    return SiennaReactiveVirtualOscillator(k2=get_required_value(data, 'k2', 'ReactiveVirtualOscillator'), V_ref=data.get('V_ref', None), Q_ref=data.get('Q_ref', None))


def sienna_reactive_virtual_oscillator_to_json(value: SiennaReactiveVirtualOscillator) -> dict[str, Any]:
    """Write every ReactiveVirtualOscillator slot to explicit schema property names.

    :param value: Typed ReactiveVirtualOscillator object.
    :return: JSON object with declared schema properties.
    """
    return {'k2': value.k2, 'V_ref': value.V_ref, 'Q_ref': value.Q_ref}
