# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ESAC1A schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaESAC1A(SiennaSchemaModel):
    """Expose every declared ESAC1A property through fixed slots."""

    __slots__ = ('id', 'Tr', 'Tb', 'Tc', 'Ka', 'Ta', 'Va_lim', 'Te', 'Kf', 'Tf', 'Kc', 'Kd', 'Ke', 'E_sat', 'Se', 'Vr_lim', 'V_ref',)

    def __init__(self, id: int, Tr: float, Tb: float, Tc: float, Ka: float, Ta: float, Va_lim: SiennaMinMax, Te: float, Kf: float, Tf: float, Kc: float, Kd: float, Ke: float, E_sat: list[float], Se: list[float], Vr_lim: SiennaMinMax, V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.Tr: float = Tr
        self.Tb: float = Tb
        self.Tc: float = Tc
        self.Ka: float = Ka
        self.Ta: float = Ta
        self.Va_lim: SiennaMinMax = Va_lim
        self.Te: float = Te
        self.Kf: float = Kf
        self.Tf: float = Tf
        self.Kc: float = Kc
        self.Kd: float = Kd
        self.Ke: float = Ke
        self.E_sat: list[float] = E_sat
        self.Se: list[float] = Se
        self.Vr_lim: SiennaMinMax = Vr_lim
        self.V_ref: float = V_ref


def parse_sienna_esac1_a(data: dict[str, Any]) -> SiennaESAC1A:
    """Parse declared ESAC1A properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ESAC1A object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaESAC1A(id=get_required_value(data, 'id', 'ESAC1A'), Tr=get_required_value(data, 'Tr', 'ESAC1A'), Tb=get_required_value(data, 'Tb', 'ESAC1A'), Tc=get_required_value(data, 'Tc', 'ESAC1A'), Ka=get_required_value(data, 'Ka', 'ESAC1A'), Ta=get_required_value(data, 'Ta', 'ESAC1A'), Va_lim=parse_sienna_min_max(get_required_value(data, 'Va_lim', 'ESAC1A')), Te=get_required_value(data, 'Te', 'ESAC1A'), Kf=get_required_value(data, 'Kf', 'ESAC1A'), Tf=get_required_value(data, 'Tf', 'ESAC1A'), Kc=get_required_value(data, 'Kc', 'ESAC1A'), Kd=get_required_value(data, 'Kd', 'ESAC1A'), Ke=get_required_value(data, 'Ke', 'ESAC1A'), E_sat=get_required_value(data, 'E_sat', 'ESAC1A'), Se=get_required_value(data, 'Se', 'ESAC1A'), Vr_lim=parse_sienna_min_max(get_required_value(data, 'Vr_lim', 'ESAC1A')), V_ref=data.get('V_ref', None))

def sienna_esac1_a_to_json(value: SiennaESAC1A) -> dict[str, Any]:
    """Write every ESAC1A slot to explicit schema property names.

    :param value: Typed ESAC1A object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'Tr': value.Tr, 'Tb': value.Tb, 'Tc': value.Tc, 'Ka': value.Ka, 'Ta': value.Ta, 'Va_lim': sienna_min_max_to_json(value.Va_lim), 'Te': value.Te, 'Kf': value.Kf, 'Tf': value.Tf, 'Kc': value.Kc, 'Kd': value.Kd, 'Ke': value.Ke, 'E_sat': value.E_sat, 'Se': value.Se, 'Vr_lim': sienna_min_max_to_json(value.Vr_lim), 'V_ref': value.V_ref}
