# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna GasTG schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaGasTG(SiennaSchemaModel):
    """Expose every declared GasTG property through fixed slots."""

    __slots__ = ('id', 'R', 'T1', 'T2', 'T3', 'AT', 'Kt', 'V_lim', 'D_turb', 'P_ref',)

    def __init__(self, id: int, R: float, T1: float, T2: float, T3: float, AT: float, Kt: float, V_lim: list[float], D_turb: float, P_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.R: float = R
        self.T1: float = T1
        self.T2: float = T2
        self.T3: float = T3
        self.AT: float = AT
        self.Kt: float = Kt
        self.V_lim: list[float] = V_lim
        self.D_turb: float = D_turb
        self.P_ref: float = P_ref


def parse_sienna_gas_tg(data: dict[str, Any]) -> SiennaGasTG:
    """Parse declared GasTG properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed GasTG object.
    """
    return SiennaGasTG(id=get_required_value(data, 'id', 'GasTG'), R=get_required_value(data, 'R', 'GasTG'), T1=get_required_value(data, 'T1', 'GasTG'), T2=get_required_value(data, 'T2', 'GasTG'), T3=get_required_value(data, 'T3', 'GasTG'), AT=get_required_value(data, 'AT', 'GasTG'), Kt=get_required_value(data, 'Kt', 'GasTG'), V_lim=get_required_value(data, 'V_lim', 'GasTG'), D_turb=get_required_value(data, 'D_turb', 'GasTG'), P_ref=data.get('P_ref', None))


def sienna_gas_tg_to_json(value: SiennaGasTG) -> dict[str, Any]:
    """Write every GasTG slot to explicit schema property names.

    :param value: Typed GasTG object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'R': value.R, 'T1': value.T1, 'T2': value.T2, 'T3': value.T3, 'AT': value.AT, 'Kt': value.Kt, 'V_lim': value.V_lim, 'D_turb': value.D_turb, 'P_ref': value.P_ref}
