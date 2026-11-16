# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ReactiveRenewableControllerAB schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.dbd_pnts import SiennaDbdPnts
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaReactiveRenewableControllerAB(SiennaSchemaModel):
    """Expose every declared ReactiveRenewableControllerAB property through fixed slots."""

    __slots__ = ('bus_control', 'from_branch_control', 'to_branch_control', 'branch_id_control', 'VC_Flag', 'Ref_Flag', 'PF_Flag', 'V_Flag', 'T_fltr', 'K_p', 'K_i', 'T_ft', 'T_fv', 'V_frz', 'R_c', 'X_c', 'K_c', 'e_lim', 'dbd_pnts', 'Q_lim', 'T_p', 'Q_lim_inner', 'V_lim', 'K_qp', 'K_qi', 'Q_ref', 'V_ref',)

    def __init__(self, bus_control: int, from_branch_control: int, to_branch_control: int, branch_id_control: str, VC_Flag: bool, Ref_Flag: bool, PF_Flag: bool, V_Flag: bool, T_fltr: float, K_p: float, K_i: float, T_ft: float, T_fv: float, V_frz: float, R_c: float, X_c: float, K_c: float, e_lim: SiennaMinMax, dbd_pnts: SiennaDbdPnts, Q_lim: SiennaMinMax, T_p: float, Q_lim_inner: SiennaMinMax, V_lim: SiennaMinMax, K_qp: float, K_qi: float, Q_ref: float, V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.bus_control: int = bus_control
        self.from_branch_control: int = from_branch_control
        self.to_branch_control: int = to_branch_control
        self.branch_id_control: str = branch_id_control
        self.VC_Flag: bool = VC_Flag
        self.Ref_Flag: bool = Ref_Flag
        self.PF_Flag: bool = PF_Flag
        self.V_Flag: bool = V_Flag
        self.T_fltr: float = T_fltr
        self.K_p: float = K_p
        self.K_i: float = K_i
        self.T_ft: float = T_ft
        self.T_fv: float = T_fv
        self.V_frz: float = V_frz
        self.R_c: float = R_c
        self.X_c: float = X_c
        self.K_c: float = K_c
        self.e_lim: SiennaMinMax = e_lim
        self.dbd_pnts: SiennaDbdPnts = dbd_pnts
        self.Q_lim: SiennaMinMax = Q_lim
        self.T_p: float = T_p
        self.Q_lim_inner: SiennaMinMax = Q_lim_inner
        self.V_lim: SiennaMinMax = V_lim
        self.K_qp: float = K_qp
        self.K_qi: float = K_qi
        self.Q_ref: float = Q_ref
        self.V_ref: float = V_ref


def parse_sienna_reactive_renewable_controller_ab(data: dict[str, Any]) -> SiennaReactiveRenewableControllerAB:
    """Parse declared ReactiveRenewableControllerAB properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ReactiveRenewableControllerAB object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.dbd_pnts import parse_sienna_dbd_pnts
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaReactiveRenewableControllerAB(bus_control=get_required_value(data, 'bus_control', 'ReactiveRenewableControllerAB'), from_branch_control=get_required_value(data, 'from_branch_control', 'ReactiveRenewableControllerAB'), to_branch_control=get_required_value(data, 'to_branch_control', 'ReactiveRenewableControllerAB'), branch_id_control=get_required_value(data, 'branch_id_control', 'ReactiveRenewableControllerAB'), VC_Flag=get_required_value(data, 'VC_Flag', 'ReactiveRenewableControllerAB'), Ref_Flag=get_required_value(data, 'Ref_Flag', 'ReactiveRenewableControllerAB'), PF_Flag=get_required_value(data, 'PF_Flag', 'ReactiveRenewableControllerAB'), V_Flag=get_required_value(data, 'V_Flag', 'ReactiveRenewableControllerAB'), T_fltr=get_required_value(data, 'T_fltr', 'ReactiveRenewableControllerAB'), K_p=get_required_value(data, 'K_p', 'ReactiveRenewableControllerAB'), K_i=get_required_value(data, 'K_i', 'ReactiveRenewableControllerAB'), T_ft=get_required_value(data, 'T_ft', 'ReactiveRenewableControllerAB'), T_fv=get_required_value(data, 'T_fv', 'ReactiveRenewableControllerAB'), V_frz=get_required_value(data, 'V_frz', 'ReactiveRenewableControllerAB'), R_c=get_required_value(data, 'R_c', 'ReactiveRenewableControllerAB'), X_c=get_required_value(data, 'X_c', 'ReactiveRenewableControllerAB'), K_c=get_required_value(data, 'K_c', 'ReactiveRenewableControllerAB'), e_lim=parse_sienna_min_max(get_required_value(data, 'e_lim', 'ReactiveRenewableControllerAB')), dbd_pnts=parse_sienna_dbd_pnts(get_required_value(data, 'dbd_pnts', 'ReactiveRenewableControllerAB')), Q_lim=parse_sienna_min_max(get_required_value(data, 'Q_lim', 'ReactiveRenewableControllerAB')), T_p=get_required_value(data, 'T_p', 'ReactiveRenewableControllerAB'), Q_lim_inner=parse_sienna_min_max(get_required_value(data, 'Q_lim_inner', 'ReactiveRenewableControllerAB')), V_lim=parse_sienna_min_max(get_required_value(data, 'V_lim', 'ReactiveRenewableControllerAB')), K_qp=get_required_value(data, 'K_qp', 'ReactiveRenewableControllerAB'), K_qi=get_required_value(data, 'K_qi', 'ReactiveRenewableControllerAB'), Q_ref=data.get('Q_ref', None), V_ref=data.get('V_ref', None))

def sienna_reactive_renewable_controller_ab_to_json(value: SiennaReactiveRenewableControllerAB) -> dict[str, Any]:
    """Write every ReactiveRenewableControllerAB slot to explicit schema property names.

    :param value: Typed ReactiveRenewableControllerAB object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.dbd_pnts import sienna_dbd_pnts_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'bus_control': value.bus_control, 'from_branch_control': value.from_branch_control, 'to_branch_control': value.to_branch_control, 'branch_id_control': value.branch_id_control, 'VC_Flag': value.VC_Flag, 'Ref_Flag': value.Ref_Flag, 'PF_Flag': value.PF_Flag, 'V_Flag': value.V_Flag, 'T_fltr': value.T_fltr, 'K_p': value.K_p, 'K_i': value.K_i, 'T_ft': value.T_ft, 'T_fv': value.T_fv, 'V_frz': value.V_frz, 'R_c': value.R_c, 'X_c': value.X_c, 'K_c': value.K_c, 'e_lim': sienna_min_max_to_json(value.e_lim), 'dbd_pnts': sienna_dbd_pnts_to_json(value.dbd_pnts), 'Q_lim': sienna_min_max_to_json(value.Q_lim), 'T_p': value.T_p, 'Q_lim_inner': sienna_min_max_to_json(value.Q_lim_inner), 'V_lim': sienna_min_max_to_json(value.V_lim), 'K_qp': value.K_qp, 'K_qi': value.K_qi, 'Q_ref': value.Q_ref, 'V_ref': value.V_ref}
