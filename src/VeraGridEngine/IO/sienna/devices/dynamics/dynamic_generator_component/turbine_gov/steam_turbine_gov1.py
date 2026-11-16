# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna SteamTurbineGov1 schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaSteamTurbineGov1(SiennaSchemaModel):
    """Expose every declared SteamTurbineGov1 property through fixed slots."""

    __slots__ = ('id', 'R', 'T1', 'valve_position_limits', 'T2', 'T3', 'D_T', 'DB_h', 'DB_l', 'T_rate', 'P_ref',)

    def __init__(self, id: int, R: float, T1: float, valve_position_limits: SiennaMinMax, T2: float, T3: float, D_T: float, DB_h: float, DB_l: float, T_rate: float, P_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.R: float = R
        self.T1: float = T1
        self.valve_position_limits: SiennaMinMax = valve_position_limits
        self.T2: float = T2
        self.T3: float = T3
        self.D_T: float = D_T
        self.DB_h: float = DB_h
        self.DB_l: float = DB_l
        self.T_rate: float = T_rate
        self.P_ref: float = P_ref


def parse_sienna_steam_turbine_gov1(data: dict[str, Any]) -> SiennaSteamTurbineGov1:
    """Parse declared SteamTurbineGov1 properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed SteamTurbineGov1 object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaSteamTurbineGov1(id=get_required_value(data, 'id', 'SteamTurbineGov1'), R=get_required_value(data, 'R', 'SteamTurbineGov1'), T1=get_required_value(data, 'T1', 'SteamTurbineGov1'), valve_position_limits=parse_sienna_min_max(get_required_value(data, 'valve_position_limits', 'SteamTurbineGov1')), T2=get_required_value(data, 'T2', 'SteamTurbineGov1'), T3=get_required_value(data, 'T3', 'SteamTurbineGov1'), D_T=get_required_value(data, 'D_T', 'SteamTurbineGov1'), DB_h=get_required_value(data, 'DB_h', 'SteamTurbineGov1'), DB_l=get_required_value(data, 'DB_l', 'SteamTurbineGov1'), T_rate=get_required_value(data, 'T_rate', 'SteamTurbineGov1'), P_ref=data.get('P_ref', None))

def sienna_steam_turbine_gov1_to_json(value: SiennaSteamTurbineGov1) -> dict[str, Any]:
    """Write every SteamTurbineGov1 slot to explicit schema property names.

    :param value: Typed SteamTurbineGov1 object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'R': value.R, 'T1': value.T1, 'valve_position_limits': sienna_min_max_to_json(value.valve_position_limits), 'T2': value.T2, 'T3': value.T3, 'D_T': value.D_T, 'DB_h': value.DB_h, 'DB_l': value.DB_l, 'T_rate': value.T_rate, 'P_ref': value.P_ref}
