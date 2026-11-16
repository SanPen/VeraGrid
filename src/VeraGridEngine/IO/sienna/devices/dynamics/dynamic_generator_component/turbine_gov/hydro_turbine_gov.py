# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna HydroTurbineGov schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaHydroTurbineGov(SiennaSchemaModel):
    """Expose every declared HydroTurbineGov property through fixed slots."""

    __slots__ = ('id', 'R', 'r', 'Tr', 'Tf', 'Tg', 'VELM', 'gate_position_limits', 'Tw', 'At', 'D_T', 'q_nl', 'P_ref',)

    def __init__(self, id: int, R: float, r: float, Tr: float, Tf: float, Tg: float, VELM: float, gate_position_limits: SiennaMinMax, Tw: float, At: float, D_T: float, q_nl: float, P_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.R: float = R
        self.r: float = r
        self.Tr: float = Tr
        self.Tf: float = Tf
        self.Tg: float = Tg
        self.VELM: float = VELM
        self.gate_position_limits: SiennaMinMax = gate_position_limits
        self.Tw: float = Tw
        self.At: float = At
        self.D_T: float = D_T
        self.q_nl: float = q_nl
        self.P_ref: float = P_ref


def parse_sienna_hydro_turbine_gov(data: dict[str, Any]) -> SiennaHydroTurbineGov:
    """Parse declared HydroTurbineGov properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed HydroTurbineGov object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaHydroTurbineGov(id=get_required_value(data, 'id', 'HydroTurbineGov'), R=get_required_value(data, 'R', 'HydroTurbineGov'), r=get_required_value(data, 'r', 'HydroTurbineGov'), Tr=get_required_value(data, 'Tr', 'HydroTurbineGov'), Tf=get_required_value(data, 'Tf', 'HydroTurbineGov'), Tg=get_required_value(data, 'Tg', 'HydroTurbineGov'), VELM=get_required_value(data, 'VELM', 'HydroTurbineGov'), gate_position_limits=parse_sienna_min_max(get_required_value(data, 'gate_position_limits', 'HydroTurbineGov')), Tw=get_required_value(data, 'Tw', 'HydroTurbineGov'), At=get_required_value(data, 'At', 'HydroTurbineGov'), D_T=get_required_value(data, 'D_T', 'HydroTurbineGov'), q_nl=get_required_value(data, 'q_nl', 'HydroTurbineGov'), P_ref=data.get('P_ref', None))

def sienna_hydro_turbine_gov_to_json(value: SiennaHydroTurbineGov) -> dict[str, Any]:
    """Write every HydroTurbineGov slot to explicit schema property names.

    :param value: Typed HydroTurbineGov object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'R': value.R, 'r': value.r, 'Tr': value.Tr, 'Tf': value.Tf, 'Tg': value.Tg, 'VELM': value.VELM, 'gate_position_limits': sienna_min_max_to_json(value.gate_position_limits), 'Tw': value.Tw, 'At': value.At, 'D_T': value.D_T, 'q_nl': value.q_nl, 'P_ref': value.P_ref}
