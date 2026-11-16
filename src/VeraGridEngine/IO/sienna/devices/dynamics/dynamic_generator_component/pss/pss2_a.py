# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna PSS2A schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaPSS2A(SiennaSchemaModel):
    """Expose every declared PSS2A property through fixed slots."""

    __slots__ = ('id', 'input_code_1', 'remote_bus_control_1', 'input_code_2', 'remote_bus_control_2', 'M_rtf', 'N_rtf', 'Tw1', 'Tw2', 'T6', 'Tw3', 'Tw4', 'T7', 'Ks2', 'Ks3', 'T8', 'T9', 'Ks1', 'T1', 'T2', 'T3', 'T4', 'Vst_lim',)

    def __init__(self, id: int, input_code_1: int, remote_bus_control_1: int, input_code_2: int, remote_bus_control_2: int, M_rtf: int, N_rtf: int, Tw1: float, Tw2: float, T6: float, Tw3: float, Tw4: float, T7: float, Ks2: float, Ks3: float, T8: float, T9: float, Ks1: float, T1: float, T2: float, T3: float, T4: float, Vst_lim: list[float]) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.input_code_1: int = input_code_1
        self.remote_bus_control_1: int = remote_bus_control_1
        self.input_code_2: int = input_code_2
        self.remote_bus_control_2: int = remote_bus_control_2
        self.M_rtf: int = M_rtf
        self.N_rtf: int = N_rtf
        self.Tw1: float = Tw1
        self.Tw2: float = Tw2
        self.T6: float = T6
        self.Tw3: float = Tw3
        self.Tw4: float = Tw4
        self.T7: float = T7
        self.Ks2: float = Ks2
        self.Ks3: float = Ks3
        self.T8: float = T8
        self.T9: float = T9
        self.Ks1: float = Ks1
        self.T1: float = T1
        self.T2: float = T2
        self.T3: float = T3
        self.T4: float = T4
        self.Vst_lim: list[float] = Vst_lim


def parse_sienna_pss2_a(data: dict[str, Any]) -> SiennaPSS2A:
    """Parse declared PSS2A properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed PSS2A object.
    """
    return SiennaPSS2A(id=get_required_value(data, 'id', 'PSS2A'), input_code_1=get_required_value(data, 'input_code_1', 'PSS2A'), remote_bus_control_1=get_required_value(data, 'remote_bus_control_1', 'PSS2A'), input_code_2=get_required_value(data, 'input_code_2', 'PSS2A'), remote_bus_control_2=get_required_value(data, 'remote_bus_control_2', 'PSS2A'), M_rtf=get_required_value(data, 'M_rtf', 'PSS2A'), N_rtf=get_required_value(data, 'N_rtf', 'PSS2A'), Tw1=get_required_value(data, 'Tw1', 'PSS2A'), Tw2=get_required_value(data, 'Tw2', 'PSS2A'), T6=get_required_value(data, 'T6', 'PSS2A'), Tw3=get_required_value(data, 'Tw3', 'PSS2A'), Tw4=get_required_value(data, 'Tw4', 'PSS2A'), T7=get_required_value(data, 'T7', 'PSS2A'), Ks2=get_required_value(data, 'Ks2', 'PSS2A'), Ks3=get_required_value(data, 'Ks3', 'PSS2A'), T8=get_required_value(data, 'T8', 'PSS2A'), T9=get_required_value(data, 'T9', 'PSS2A'), Ks1=get_required_value(data, 'Ks1', 'PSS2A'), T1=get_required_value(data, 'T1', 'PSS2A'), T2=get_required_value(data, 'T2', 'PSS2A'), T3=get_required_value(data, 'T3', 'PSS2A'), T4=get_required_value(data, 'T4', 'PSS2A'), Vst_lim=get_required_value(data, 'Vst_lim', 'PSS2A'))


def sienna_pss2_a_to_json(value: SiennaPSS2A) -> dict[str, Any]:
    """Write every PSS2A slot to explicit schema property names.

    :param value: Typed PSS2A object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'input_code_1': value.input_code_1, 'remote_bus_control_1': value.remote_bus_control_1, 'input_code_2': value.input_code_2, 'remote_bus_control_2': value.remote_bus_control_2, 'M_rtf': value.M_rtf, 'N_rtf': value.N_rtf, 'Tw1': value.Tw1, 'Tw2': value.Tw2, 'T6': value.T6, 'Tw3': value.Tw3, 'Tw4': value.Tw4, 'T7': value.T7, 'Ks2': value.Ks2, 'Ks3': value.Ks3, 'T8': value.T8, 'T9': value.T9, 'Ks1': value.Ks1, 'T1': value.T1, 'T2': value.T2, 'T3': value.T3, 'T4': value.T4, 'Vst_lim': value.Vst_lim}
