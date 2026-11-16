# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna CurrentModeControl schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaCurrentModeControl(SiennaSchemaModel):
    """Expose every declared CurrentModeControl property through fixed slots."""

    __slots__ = ('kpc', 'kic', 'kffv',)

    def __init__(self, kpc: float, kic: float, kffv: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.kpc: float = kpc
        self.kic: float = kic
        self.kffv: float = kffv


def parse_sienna_current_mode_control(data: dict[str, Any]) -> SiennaCurrentModeControl:
    """Parse declared CurrentModeControl properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed CurrentModeControl object.
    """
    return SiennaCurrentModeControl(kpc=get_required_value(data, 'kpc', 'CurrentModeControl'), kic=get_required_value(data, 'kic', 'CurrentModeControl'), kffv=get_required_value(data, 'kffv', 'CurrentModeControl'))


def sienna_current_mode_control_to_json(value: SiennaCurrentModeControl) -> dict[str, Any]:
    """Write every CurrentModeControl slot to explicit schema property names.

    :param value: Typed CurrentModeControl object.
    :return: JSON object with declared schema properties.
    """
    return {'kpc': value.kpc, 'kic': value.kic, 'kffv': value.kffv}
