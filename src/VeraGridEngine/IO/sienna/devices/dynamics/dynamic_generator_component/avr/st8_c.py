# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ST8C schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaST8C(SiennaSchemaModel):
    """Expose every declared ST8C property through fixed slots."""

    __slots__ = ('id', 'OEL_Flag', 'UEL_Flag', 'SCL_Flag', 'SW1_Flag', 'Tr', 'K_pr', 'K_ir', 'Vpi_lim', 'K_pa', 'K_ia', 'Va_lim', 'K_a', 'T_a', 'Vr_lim', 'K_f', 'T_f', 'K_c1', 'K_p', 'K_i1', 'X_l', 'theta_p', 'VB1_max', 'K_c2', 'K_i2', 'VB2_max', 'V_ref', 'Ifd_ref',)

    def __init__(self, id: int, OEL_Flag: int, UEL_Flag: int, SCL_Flag: int, SW1_Flag: int, Tr: float, K_pr: float, K_ir: float, Vpi_lim: SiennaMinMax, K_pa: float, K_ia: float, Va_lim: SiennaMinMax, K_a: float, T_a: float, Vr_lim: SiennaMinMax, K_f: float, T_f: float, K_c1: float, K_p: float, K_i1: float, X_l: float, theta_p: float, VB1_max: float, K_c2: float, K_i2: float, VB2_max: float, V_ref: float, Ifd_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.OEL_Flag: int = OEL_Flag
        self.UEL_Flag: int = UEL_Flag
        self.SCL_Flag: int = SCL_Flag
        self.SW1_Flag: int = SW1_Flag
        self.Tr: float = Tr
        self.K_pr: float = K_pr
        self.K_ir: float = K_ir
        self.Vpi_lim: SiennaMinMax = Vpi_lim
        self.K_pa: float = K_pa
        self.K_ia: float = K_ia
        self.Va_lim: SiennaMinMax = Va_lim
        self.K_a: float = K_a
        self.T_a: float = T_a
        self.Vr_lim: SiennaMinMax = Vr_lim
        self.K_f: float = K_f
        self.T_f: float = T_f
        self.K_c1: float = K_c1
        self.K_p: float = K_p
        self.K_i1: float = K_i1
        self.X_l: float = X_l
        self.theta_p: float = theta_p
        self.VB1_max: float = VB1_max
        self.K_c2: float = K_c2
        self.K_i2: float = K_i2
        self.VB2_max: float = VB2_max
        self.V_ref: float = V_ref
        self.Ifd_ref: float = Ifd_ref


def parse_sienna_st8_c(data: dict[str, Any]) -> SiennaST8C:
    """Parse declared ST8C properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ST8C object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaST8C(id=get_required_value(data, 'id', 'ST8C'), OEL_Flag=get_required_value(data, 'OEL_Flag', 'ST8C'), UEL_Flag=get_required_value(data, 'UEL_Flag', 'ST8C'), SCL_Flag=get_required_value(data, 'SCL_Flag', 'ST8C'), SW1_Flag=get_required_value(data, 'SW1_Flag', 'ST8C'), Tr=get_required_value(data, 'Tr', 'ST8C'), K_pr=get_required_value(data, 'K_pr', 'ST8C'), K_ir=get_required_value(data, 'K_ir', 'ST8C'), Vpi_lim=parse_sienna_min_max(get_required_value(data, 'Vpi_lim', 'ST8C')), K_pa=get_required_value(data, 'K_pa', 'ST8C'), K_ia=get_required_value(data, 'K_ia', 'ST8C'), Va_lim=parse_sienna_min_max(get_required_value(data, 'Va_lim', 'ST8C')), K_a=get_required_value(data, 'K_a', 'ST8C'), T_a=get_required_value(data, 'T_a', 'ST8C'), Vr_lim=parse_sienna_min_max(get_required_value(data, 'Vr_lim', 'ST8C')), K_f=get_required_value(data, 'K_f', 'ST8C'), T_f=get_required_value(data, 'T_f', 'ST8C'), K_c1=get_required_value(data, 'K_c1', 'ST8C'), K_p=get_required_value(data, 'K_p', 'ST8C'), K_i1=get_required_value(data, 'K_i1', 'ST8C'), X_l=get_required_value(data, 'X_l', 'ST8C'), theta_p=get_required_value(data, 'theta_p', 'ST8C'), VB1_max=get_required_value(data, 'VB1_max', 'ST8C'), K_c2=get_required_value(data, 'K_c2', 'ST8C'), K_i2=get_required_value(data, 'K_i2', 'ST8C'), VB2_max=get_required_value(data, 'VB2_max', 'ST8C'), V_ref=data.get('V_ref', None), Ifd_ref=data.get('Ifd_ref', None))

def sienna_st8_c_to_json(value: SiennaST8C) -> dict[str, Any]:
    """Write every ST8C slot to explicit schema property names.

    :param value: Typed ST8C object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'OEL_Flag': value.OEL_Flag, 'UEL_Flag': value.UEL_Flag, 'SCL_Flag': value.SCL_Flag, 'SW1_Flag': value.SW1_Flag, 'Tr': value.Tr, 'K_pr': value.K_pr, 'K_ir': value.K_ir, 'Vpi_lim': sienna_min_max_to_json(value.Vpi_lim), 'K_pa': value.K_pa, 'K_ia': value.K_ia, 'Va_lim': sienna_min_max_to_json(value.Va_lim), 'K_a': value.K_a, 'T_a': value.T_a, 'Vr_lim': sienna_min_max_to_json(value.Vr_lim), 'K_f': value.K_f, 'T_f': value.T_f, 'K_c1': value.K_c1, 'K_p': value.K_p, 'K_i1': value.K_i1, 'X_l': value.X_l, 'theta_p': value.theta_p, 'VB1_max': value.VB1_max, 'K_c2': value.K_c2, 'K_i2': value.K_i2, 'VB2_max': value.VB2_max, 'V_ref': value.V_ref, 'Ifd_ref': value.Ifd_ref}
