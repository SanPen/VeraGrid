# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna IEEETurbineGov1 schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaIEEETurbineGov1(SiennaSchemaModel):
    """Expose every declared IEEETurbineGov1 property through fixed slots."""

    __slots__ = ('id', 'K', 'T1', 'T2', 'T3', 'U0', 'U_c', 'valve_position_limits', 'T4', 'K1', 'K2', 'T5', 'K3', 'K4', 'T6', 'K5', 'K6', 'T7', 'K7', 'K8', 'P_ref',)

    def __init__(self, id: int, K: int, T1: int, T2: float, T3: float, U0: float, U_c: float, valve_position_limits: SiennaMinMax, T4: float, K1: float, K2: float, T5: float, K3: float, K4: float, T6: float, K5: float, K6: float, T7: float, K7: float, K8: float, P_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.K: int = K
        self.T1: int = T1
        self.T2: float = T2
        self.T3: float = T3
        self.U0: float = U0
        self.U_c: float = U_c
        self.valve_position_limits: SiennaMinMax = valve_position_limits
        self.T4: float = T4
        self.K1: float = K1
        self.K2: float = K2
        self.T5: float = T5
        self.K3: float = K3
        self.K4: float = K4
        self.T6: float = T6
        self.K5: float = K5
        self.K6: float = K6
        self.T7: float = T7
        self.K7: float = K7
        self.K8: float = K8
        self.P_ref: float = P_ref


def parse_sienna_ieee_turbine_gov1(data: dict[str, Any]) -> SiennaIEEETurbineGov1:
    """Parse declared IEEETurbineGov1 properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed IEEETurbineGov1 object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaIEEETurbineGov1(id=get_required_value(data, 'id', 'IEEETurbineGov1'), K=get_required_value(data, 'K', 'IEEETurbineGov1'), T1=get_required_value(data, 'T1', 'IEEETurbineGov1'), T2=get_required_value(data, 'T2', 'IEEETurbineGov1'), T3=get_required_value(data, 'T3', 'IEEETurbineGov1'), U0=get_required_value(data, 'U0', 'IEEETurbineGov1'), U_c=get_required_value(data, 'U_c', 'IEEETurbineGov1'), valve_position_limits=parse_sienna_min_max(get_required_value(data, 'valve_position_limits', 'IEEETurbineGov1')), T4=get_required_value(data, 'T4', 'IEEETurbineGov1'), K1=get_required_value(data, 'K1', 'IEEETurbineGov1'), K2=get_required_value(data, 'K2', 'IEEETurbineGov1'), T5=get_required_value(data, 'T5', 'IEEETurbineGov1'), K3=get_required_value(data, 'K3', 'IEEETurbineGov1'), K4=get_required_value(data, 'K4', 'IEEETurbineGov1'), T6=get_required_value(data, 'T6', 'IEEETurbineGov1'), K5=get_required_value(data, 'K5', 'IEEETurbineGov1'), K6=get_required_value(data, 'K6', 'IEEETurbineGov1'), T7=get_required_value(data, 'T7', 'IEEETurbineGov1'), K7=get_required_value(data, 'K7', 'IEEETurbineGov1'), K8=get_required_value(data, 'K8', 'IEEETurbineGov1'), P_ref=data.get('P_ref', None))

def sienna_ieee_turbine_gov1_to_json(value: SiennaIEEETurbineGov1) -> dict[str, Any]:
    """Write every IEEETurbineGov1 slot to explicit schema property names.

    :param value: Typed IEEETurbineGov1 object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'K': value.K, 'T1': value.T1, 'T2': value.T2, 'T3': value.T3, 'U0': value.U0, 'U_c': value.U_c, 'valve_position_limits': sienna_min_max_to_json(value.valve_position_limits), 'T4': value.T4, 'K1': value.K1, 'K2': value.K2, 'T5': value.T5, 'K3': value.K3, 'K4': value.K4, 'T6': value.T6, 'K5': value.K5, 'K6': value.K6, 'T7': value.T7, 'K7': value.K7, 'K8': value.K8, 'P_ref': value.P_ref}
