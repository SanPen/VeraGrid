# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ActiveRenewableControllerAB schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.fdbd_pnts import SiennaFdbdPnts
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaActiveRenewableControllerAB(SiennaSchemaModel):
    """Expose every declared ActiveRenewableControllerAB property through fixed slots."""

    __slots__ = ('bus_control', 'from_branch_control', 'to_branch_control', 'branch_id_control', 'Freq_Flag', 'K_pg', 'K_ig', 'T_p', 'fdbd_pnts', 'fe_lim', 'P_lim', 'T_g', 'D_dn', 'D_up', 'dP_lim', 'P_lim_inner', 'T_pord', 'P_ref',)

    def __init__(self, bus_control: int, from_branch_control: int, to_branch_control: int, branch_id_control: int, Freq_Flag: bool, K_pg: float, K_ig: float, T_p: float, fdbd_pnts: SiennaFdbdPnts, fe_lim: SiennaMinMax, P_lim: SiennaMinMax, T_g: float, D_dn: float, D_up: float, dP_lim: SiennaMinMax, P_lim_inner: SiennaMinMax, T_pord: float, P_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.bus_control: int = bus_control
        self.from_branch_control: int = from_branch_control
        self.to_branch_control: int = to_branch_control
        self.branch_id_control: int = branch_id_control
        self.Freq_Flag: bool = Freq_Flag
        self.K_pg: float = K_pg
        self.K_ig: float = K_ig
        self.T_p: float = T_p
        self.fdbd_pnts: SiennaFdbdPnts = fdbd_pnts
        self.fe_lim: SiennaMinMax = fe_lim
        self.P_lim: SiennaMinMax = P_lim
        self.T_g: float = T_g
        self.D_dn: float = D_dn
        self.D_up: float = D_up
        self.dP_lim: SiennaMinMax = dP_lim
        self.P_lim_inner: SiennaMinMax = P_lim_inner
        self.T_pord: float = T_pord
        self.P_ref: float = P_ref


def parse_sienna_active_renewable_controller_ab(data: dict[str, Any]) -> SiennaActiveRenewableControllerAB:
    """Parse declared ActiveRenewableControllerAB properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ActiveRenewableControllerAB object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.fdbd_pnts import parse_sienna_fdbd_pnts
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaActiveRenewableControllerAB(bus_control=get_required_value(data, 'bus_control', 'ActiveRenewableControllerAB'), from_branch_control=get_required_value(data, 'from_branch_control', 'ActiveRenewableControllerAB'), to_branch_control=get_required_value(data, 'to_branch_control', 'ActiveRenewableControllerAB'), branch_id_control=get_required_value(data, 'branch_id_control', 'ActiveRenewableControllerAB'), Freq_Flag=get_required_value(data, 'Freq_Flag', 'ActiveRenewableControllerAB'), K_pg=get_required_value(data, 'K_pg', 'ActiveRenewableControllerAB'), K_ig=get_required_value(data, 'K_ig', 'ActiveRenewableControllerAB'), T_p=get_required_value(data, 'T_p', 'ActiveRenewableControllerAB'), fdbd_pnts=parse_sienna_fdbd_pnts(get_required_value(data, 'fdbd_pnts', 'ActiveRenewableControllerAB')), fe_lim=parse_sienna_min_max(get_required_value(data, 'fe_lim', 'ActiveRenewableControllerAB')), P_lim=parse_sienna_min_max(get_required_value(data, 'P_lim', 'ActiveRenewableControllerAB')), T_g=get_required_value(data, 'T_g', 'ActiveRenewableControllerAB'), D_dn=get_required_value(data, 'D_dn', 'ActiveRenewableControllerAB'), D_up=get_required_value(data, 'D_up', 'ActiveRenewableControllerAB'), dP_lim=parse_sienna_min_max(get_required_value(data, 'dP_lim', 'ActiveRenewableControllerAB')), P_lim_inner=parse_sienna_min_max(get_required_value(data, 'P_lim_inner', 'ActiveRenewableControllerAB')), T_pord=data.get('T_pord', None), P_ref=data.get('P_ref', None))

def sienna_active_renewable_controller_ab_to_json(value: SiennaActiveRenewableControllerAB) -> dict[str, Any]:
    """Write every ActiveRenewableControllerAB slot to explicit schema property names.

    :param value: Typed ActiveRenewableControllerAB object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.fdbd_pnts import sienna_fdbd_pnts_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'bus_control': value.bus_control, 'from_branch_control': value.from_branch_control, 'to_branch_control': value.to_branch_control, 'branch_id_control': value.branch_id_control, 'Freq_Flag': value.Freq_Flag, 'K_pg': value.K_pg, 'K_ig': value.K_ig, 'T_p': value.T_p, 'fdbd_pnts': sienna_fdbd_pnts_to_json(value.fdbd_pnts), 'fe_lim': sienna_min_max_to_json(value.fe_lim), 'P_lim': sienna_min_max_to_json(value.P_lim), 'T_g': value.T_g, 'D_dn': value.D_dn, 'D_up': value.D_up, 'dP_lim': sienna_min_max_to_json(value.dP_lim), 'P_lim_inner': sienna_min_max_to_json(value.P_lim_inner), 'T_pord': value.T_pord, 'P_ref': value.P_ref}
