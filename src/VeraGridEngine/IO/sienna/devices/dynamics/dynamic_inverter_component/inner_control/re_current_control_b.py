# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna RECurrentControlB schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.dbd_pnts import SiennaDbdPnts
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaRECurrentControlB(SiennaSchemaModel):
    """Expose every declared RECurrentControlB property through fixed slots."""

    __slots__ = ('Q_Flag', 'PQ_Flag', 'Vdip_lim', 'T_rv', 'dbd_pnts', 'K_qv', 'Iqinj_lim', 'V_ref0', 'K_vp', 'K_vi', 'T_iq', 'I_max',)

    def __init__(self, Q_Flag: bool, PQ_Flag: bool, Vdip_lim: SiennaMinMax, T_rv: float, dbd_pnts: SiennaDbdPnts, K_qv: float, Iqinj_lim: SiennaMinMax, V_ref0: float, K_vp: float, K_vi: float, T_iq: float, I_max: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.Q_Flag: bool = Q_Flag
        self.PQ_Flag: bool = PQ_Flag
        self.Vdip_lim: SiennaMinMax = Vdip_lim
        self.T_rv: float = T_rv
        self.dbd_pnts: SiennaDbdPnts = dbd_pnts
        self.K_qv: float = K_qv
        self.Iqinj_lim: SiennaMinMax = Iqinj_lim
        self.V_ref0: float = V_ref0
        self.K_vp: float = K_vp
        self.K_vi: float = K_vi
        self.T_iq: float = T_iq
        self.I_max: float = I_max


def parse_sienna_re_current_control_b(data: dict[str, Any]) -> SiennaRECurrentControlB:
    """Parse declared RECurrentControlB properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed RECurrentControlB object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.dbd_pnts import parse_sienna_dbd_pnts
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaRECurrentControlB(Q_Flag=get_required_value(data, 'Q_Flag', 'RECurrentControlB'), PQ_Flag=get_required_value(data, 'PQ_Flag', 'RECurrentControlB'), Vdip_lim=parse_sienna_min_max(get_required_value(data, 'Vdip_lim', 'RECurrentControlB')), T_rv=get_required_value(data, 'T_rv', 'RECurrentControlB'), dbd_pnts=parse_sienna_dbd_pnts(get_required_value(data, 'dbd_pnts', 'RECurrentControlB')), K_qv=get_required_value(data, 'K_qv', 'RECurrentControlB'), Iqinj_lim=parse_sienna_min_max(get_required_value(data, 'Iqinj_lim', 'RECurrentControlB')), V_ref0=get_required_value(data, 'V_ref0', 'RECurrentControlB'), K_vp=get_required_value(data, 'K_vp', 'RECurrentControlB'), K_vi=get_required_value(data, 'K_vi', 'RECurrentControlB'), T_iq=get_required_value(data, 'T_iq', 'RECurrentControlB'), I_max=get_required_value(data, 'I_max', 'RECurrentControlB'))

def sienna_re_current_control_b_to_json(value: SiennaRECurrentControlB) -> dict[str, Any]:
    """Write every RECurrentControlB slot to explicit schema property names.

    :param value: Typed RECurrentControlB object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.dbd_pnts import sienna_dbd_pnts_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'Q_Flag': value.Q_Flag, 'PQ_Flag': value.PQ_Flag, 'Vdip_lim': sienna_min_max_to_json(value.Vdip_lim), 'T_rv': value.T_rv, 'dbd_pnts': sienna_dbd_pnts_to_json(value.dbd_pnts), 'K_qv': value.K_qv, 'Iqinj_lim': sienna_min_max_to_json(value.Iqinj_lim), 'V_ref0': value.V_ref0, 'K_vp': value.K_vp, 'K_vi': value.K_vi, 'T_iq': value.T_iq, 'I_max': value.I_max}
