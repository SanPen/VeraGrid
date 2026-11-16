# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ESAC6A schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaESAC6A(SiennaSchemaModel):
    """Expose every declared ESAC6A property through fixed slots."""

    __slots__ = ('id', 'Tr', 'Ka', 'Ta', 'Tk', 'Tb', 'Tc', 'Va_lim', 'Vr_lim', 'Te', 'VFE_lim', 'Kh', 'VH_max', 'Th', 'Tj', 'Kc', 'Kd', 'Ke', 'E_sat', 'Se', 'V_ref',)

    def __init__(self, id: int, Tr: float, Ka: float, Ta: float, Tk: float, Tb: float, Tc: float, Va_lim: SiennaMinMax, Vr_lim: SiennaMinMax, Te: float, VFE_lim: float, Kh: float, VH_max: float, Th: float, Tj: float, Kc: float, Kd: float, Ke: float, E_sat: list[float], Se: list[float], V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.Tr: float = Tr
        self.Ka: float = Ka
        self.Ta: float = Ta
        self.Tk: float = Tk
        self.Tb: float = Tb
        self.Tc: float = Tc
        self.Va_lim: SiennaMinMax = Va_lim
        self.Vr_lim: SiennaMinMax = Vr_lim
        self.Te: float = Te
        self.VFE_lim: float = VFE_lim
        self.Kh: float = Kh
        self.VH_max: float = VH_max
        self.Th: float = Th
        self.Tj: float = Tj
        self.Kc: float = Kc
        self.Kd: float = Kd
        self.Ke: float = Ke
        self.E_sat: list[float] = E_sat
        self.Se: list[float] = Se
        self.V_ref: float = V_ref


def parse_sienna_esac6_a(data: dict[str, Any]) -> SiennaESAC6A:
    """Parse declared ESAC6A properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ESAC6A object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaESAC6A(id=get_required_value(data, 'id', 'ESAC6A'), Tr=get_required_value(data, 'Tr', 'ESAC6A'), Ka=get_required_value(data, 'Ka', 'ESAC6A'), Ta=get_required_value(data, 'Ta', 'ESAC6A'), Tk=get_required_value(data, 'Tk', 'ESAC6A'), Tb=get_required_value(data, 'Tb', 'ESAC6A'), Tc=get_required_value(data, 'Tc', 'ESAC6A'), Va_lim=parse_sienna_min_max(get_required_value(data, 'Va_lim', 'ESAC6A')), Vr_lim=parse_sienna_min_max(get_required_value(data, 'Vr_lim', 'ESAC6A')), Te=get_required_value(data, 'Te', 'ESAC6A'), VFE_lim=get_required_value(data, 'VFE_lim', 'ESAC6A'), Kh=get_required_value(data, 'Kh', 'ESAC6A'), VH_max=get_required_value(data, 'VH_max', 'ESAC6A'), Th=get_required_value(data, 'Th', 'ESAC6A'), Tj=get_required_value(data, 'Tj', 'ESAC6A'), Kc=get_required_value(data, 'Kc', 'ESAC6A'), Kd=get_required_value(data, 'Kd', 'ESAC6A'), Ke=get_required_value(data, 'Ke', 'ESAC6A'), E_sat=get_required_value(data, 'E_sat', 'ESAC6A'), Se=get_required_value(data, 'Se', 'ESAC6A'), V_ref=data.get('V_ref', None))

def sienna_esac6_a_to_json(value: SiennaESAC6A) -> dict[str, Any]:
    """Write every ESAC6A slot to explicit schema property names.

    :param value: Typed ESAC6A object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'Tr': value.Tr, 'Ka': value.Ka, 'Ta': value.Ta, 'Tk': value.Tk, 'Tb': value.Tb, 'Tc': value.Tc, 'Va_lim': sienna_min_max_to_json(value.Va_lim), 'Vr_lim': sienna_min_max_to_json(value.Vr_lim), 'Te': value.Te, 'VFE_lim': value.VFE_lim, 'Kh': value.Kh, 'VH_max': value.VH_max, 'Th': value.Th, 'Tj': value.Tj, 'Kc': value.Kc, 'Kd': value.Kd, 'Ke': value.Ke, 'E_sat': value.E_sat, 'Se': value.Se, 'V_ref': value.V_ref}
