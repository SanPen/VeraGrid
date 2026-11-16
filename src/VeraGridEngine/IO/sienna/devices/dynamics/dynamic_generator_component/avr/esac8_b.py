# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ESAC8B schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaESAC8B(SiennaSchemaModel):
    """Expose every declared ESAC8B property through fixed slots."""

    __slots__ = ('id', 'Tr', 'Kp', 'Ki', 'Kd', 'Td', 'Ka', 'Ta', 'Vr_lim', 'Te', 'Ke', 'E_sat', 'Se', 'V_ref',)

    def __init__(self, id: int, Tr: float, Kp: float, Ki: float, Kd: float, Td: float, Ka: float, Ta: float, Vr_lim: SiennaMinMax, Te: float, Ke: float, E_sat: list[float], Se: list[float], V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.Tr: float = Tr
        self.Kp: float = Kp
        self.Ki: float = Ki
        self.Kd: float = Kd
        self.Td: float = Td
        self.Ka: float = Ka
        self.Ta: float = Ta
        self.Vr_lim: SiennaMinMax = Vr_lim
        self.Te: float = Te
        self.Ke: float = Ke
        self.E_sat: list[float] = E_sat
        self.Se: list[float] = Se
        self.V_ref: float = V_ref


def parse_sienna_esac8_b(data: dict[str, Any]) -> SiennaESAC8B:
    """Parse declared ESAC8B properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ESAC8B object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaESAC8B(id=get_required_value(data, 'id', 'ESAC8B'), Tr=get_required_value(data, 'Tr', 'ESAC8B'), Kp=get_required_value(data, 'Kp', 'ESAC8B'), Ki=get_required_value(data, 'Ki', 'ESAC8B'), Kd=get_required_value(data, 'Kd', 'ESAC8B'), Td=get_required_value(data, 'Td', 'ESAC8B'), Ka=get_required_value(data, 'Ka', 'ESAC8B'), Ta=get_required_value(data, 'Ta', 'ESAC8B'), Vr_lim=parse_sienna_min_max(get_required_value(data, 'Vr_lim', 'ESAC8B')), Te=get_required_value(data, 'Te', 'ESAC8B'), Ke=get_required_value(data, 'Ke', 'ESAC8B'), E_sat=get_required_value(data, 'E_sat', 'ESAC8B'), Se=get_required_value(data, 'Se', 'ESAC8B'), V_ref=data.get('V_ref', None))

def sienna_esac8_b_to_json(value: SiennaESAC8B) -> dict[str, Any]:
    """Write every ESAC8B slot to explicit schema property names.

    :param value: Typed ESAC8B object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'Tr': value.Tr, 'Kp': value.Kp, 'Ki': value.Ki, 'Kd': value.Kd, 'Td': value.Td, 'Ka': value.Ka, 'Ta': value.Ta, 'Vr_lim': sienna_min_max_to_json(value.Vr_lim), 'Te': value.Te, 'Ke': value.Ke, 'E_sat': value.E_sat, 'Se': value.Se, 'V_ref': value.V_ref}
