# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna VoltageModeControl schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaVoltageModeControl(SiennaSchemaModel):
    """Expose every declared VoltageModeControl property through fixed slots."""

    __slots__ = ('kpv', 'kiv', 'kffv', 'rv', 'lv', 'kpc', 'kic', 'kffi', 'omegaad', 'kad',)

    def __init__(self, kpv: float, kiv: float, kffv: float, rv: float, lv: float, kpc: float, kic: float, kffi: float, omegaad: float, kad: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.kpv: float = kpv
        self.kiv: float = kiv
        self.kffv: float = kffv
        self.rv: float = rv
        self.lv: float = lv
        self.kpc: float = kpc
        self.kic: float = kic
        self.kffi: float = kffi
        self.omegaad: float = omegaad
        self.kad: float = kad


def parse_sienna_voltage_mode_control(data: dict[str, Any]) -> SiennaVoltageModeControl:
    """Parse declared VoltageModeControl properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed VoltageModeControl object.
    """
    return SiennaVoltageModeControl(kpv=get_required_value(data, 'kpv', 'VoltageModeControl'), kiv=get_required_value(data, 'kiv', 'VoltageModeControl'), kffv=get_required_value(data, 'kffv', 'VoltageModeControl'), rv=get_required_value(data, 'rv', 'VoltageModeControl'), lv=get_required_value(data, 'lv', 'VoltageModeControl'), kpc=get_required_value(data, 'kpc', 'VoltageModeControl'), kic=get_required_value(data, 'kic', 'VoltageModeControl'), kffi=get_required_value(data, 'kffi', 'VoltageModeControl'), omegaad=get_required_value(data, 'omegaad', 'VoltageModeControl'), kad=get_required_value(data, 'kad', 'VoltageModeControl'))


def sienna_voltage_mode_control_to_json(value: SiennaVoltageModeControl) -> dict[str, Any]:
    """Write every VoltageModeControl slot to explicit schema property names.

    :param value: Typed VoltageModeControl object.
    :return: JSON object with declared schema properties.
    """
    return {'kpv': value.kpv, 'kiv': value.kiv, 'kffv': value.kffv, 'rv': value.rv, 'lv': value.lv, 'kpc': value.kpc, 'kic': value.kic, 'kffi': value.kffi, 'omegaad': value.omegaad, 'kad': value.kad}
