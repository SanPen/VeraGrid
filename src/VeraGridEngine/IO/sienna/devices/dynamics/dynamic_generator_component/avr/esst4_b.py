# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ESST4B schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaESST4B(SiennaSchemaModel):
    """Expose every declared ESST4B property through fixed slots."""

    __slots__ = ('Tr', 'id', 'K_pr', 'K_ir', 'Vr_lim', 'Ta', 'K_pm', 'K_im', 'Vm_lim', 'Kg', 'Kp', 'Ki', 'VB_max', 'Kc', 'Xl', 'thetap', 'V_ref',)

    def __init__(self, Tr: float, id: int, K_pr: float, K_ir: float, Vr_lim: SiennaMinMax, Ta: float, K_pm: float, K_im: float, Vm_lim: SiennaMinMax, Kg: float, Kp: float, Ki: float, VB_max: float, Kc: float, Xl: float, thetap: float, V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.Tr: float = Tr
        self.id: int = id
        self.K_pr: float = K_pr
        self.K_ir: float = K_ir
        self.Vr_lim: SiennaMinMax = Vr_lim
        self.Ta: float = Ta
        self.K_pm: float = K_pm
        self.K_im: float = K_im
        self.Vm_lim: SiennaMinMax = Vm_lim
        self.Kg: float = Kg
        self.Kp: float = Kp
        self.Ki: float = Ki
        self.VB_max: float = VB_max
        self.Kc: float = Kc
        self.Xl: float = Xl
        self.thetap: float = thetap
        self.V_ref: float = V_ref


def parse_sienna_esst4_b(data: dict[str, Any]) -> SiennaESST4B:
    """Parse declared ESST4B properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ESST4B object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaESST4B(Tr=get_required_value(data, 'Tr', 'ESST4B'), id=get_required_value(data, 'id', 'ESST4B'), K_pr=get_required_value(data, 'K_pr', 'ESST4B'), K_ir=get_required_value(data, 'K_ir', 'ESST4B'), Vr_lim=parse_sienna_min_max(get_required_value(data, 'Vr_lim', 'ESST4B')), Ta=get_required_value(data, 'Ta', 'ESST4B'), K_pm=get_required_value(data, 'K_pm', 'ESST4B'), K_im=get_required_value(data, 'K_im', 'ESST4B'), Vm_lim=parse_sienna_min_max(get_required_value(data, 'Vm_lim', 'ESST4B')), Kg=get_required_value(data, 'Kg', 'ESST4B'), Kp=get_required_value(data, 'Kp', 'ESST4B'), Ki=get_required_value(data, 'Ki', 'ESST4B'), VB_max=get_required_value(data, 'VB_max', 'ESST4B'), Kc=get_required_value(data, 'Kc', 'ESST4B'), Xl=get_required_value(data, 'Xl', 'ESST4B'), thetap=get_required_value(data, 'thetap', 'ESST4B'), V_ref=data.get('V_ref', None))

def sienna_esst4_b_to_json(value: SiennaESST4B) -> dict[str, Any]:
    """Write every ESST4B slot to explicit schema property names.

    :param value: Typed ESST4B object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'Tr': value.Tr, 'id': value.id, 'K_pr': value.K_pr, 'K_ir': value.K_ir, 'Vr_lim': sienna_min_max_to_json(value.Vr_lim), 'Ta': value.Ta, 'K_pm': value.K_pm, 'K_im': value.K_im, 'Vm_lim': sienna_min_max_to_json(value.Vm_lim), 'Kg': value.Kg, 'Kp': value.Kp, 'Ki': value.Ki, 'VB_max': value.VB_max, 'Kc': value.Kc, 'Xl': value.Xl, 'thetap': value.thetap, 'V_ref': value.V_ref}
