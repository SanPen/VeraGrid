# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna PSS2C schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaPSS2C(SiennaSchemaModel):
    """Expose every declared PSS2C property through fixed slots."""

    __slots__ = ('id', 'input_code_1', 'remote_bus_control_1', 'input_code_2', 'remote_bus_control_2', 'M_rtf', 'N_rtf', 'Tw1', 'Tw2', 'T6', 'Tw3', 'Tw4', 'T7', 'Ks2', 'Ks3', 'T8', 'T9', 'Ks1', 'T1', 'T2', 'T3', 'T4', 'T10', 'T11', 'Vs1_lim', 'Vs2_lim', 'Vst_lim', 'T12', 'T13', 'PSS_Hysteresis_param', 'Xcomp', 'Tcomp', 'hysteresis_binary_logic',)

    def __init__(self, id: int, input_code_1: int, remote_bus_control_1: int, input_code_2: int, remote_bus_control_2: int, M_rtf: int, N_rtf: int, Tw1: float, Tw2: float, T6: float, Tw3: float, Tw4: float, T7: float, Ks2: float, Ks3: float, T8: float, T9: float, Ks1: float, T1: float, T2: float, T3: float, T4: float, T10: float, T11: float, Vs1_lim: list[float], Vs2_lim: list[float], Vst_lim: list[float], T12: float, T13: float, PSS_Hysteresis_param: list[float], Xcomp: float, Tcomp: float, hysteresis_binary_logic: int) -> None:
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
        self.T10: float = T10
        self.T11: float = T11
        self.Vs1_lim: list[float] = Vs1_lim
        self.Vs2_lim: list[float] = Vs2_lim
        self.Vst_lim: list[float] = Vst_lim
        self.T12: float = T12
        self.T13: float = T13
        self.PSS_Hysteresis_param: list[float] = PSS_Hysteresis_param
        self.Xcomp: float = Xcomp
        self.Tcomp: float = Tcomp
        self.hysteresis_binary_logic: int = hysteresis_binary_logic


def parse_sienna_pss2_c(data: dict[str, Any]) -> SiennaPSS2C:
    """Parse declared PSS2C properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed PSS2C object.
    """
    return SiennaPSS2C(id=get_required_value(data, 'id', 'PSS2C'), input_code_1=get_required_value(data, 'input_code_1', 'PSS2C'), remote_bus_control_1=get_required_value(data, 'remote_bus_control_1', 'PSS2C'), input_code_2=get_required_value(data, 'input_code_2', 'PSS2C'), remote_bus_control_2=get_required_value(data, 'remote_bus_control_2', 'PSS2C'), M_rtf=get_required_value(data, 'M_rtf', 'PSS2C'), N_rtf=get_required_value(data, 'N_rtf', 'PSS2C'), Tw1=get_required_value(data, 'Tw1', 'PSS2C'), Tw2=get_required_value(data, 'Tw2', 'PSS2C'), T6=get_required_value(data, 'T6', 'PSS2C'), Tw3=get_required_value(data, 'Tw3', 'PSS2C'), Tw4=get_required_value(data, 'Tw4', 'PSS2C'), T7=get_required_value(data, 'T7', 'PSS2C'), Ks2=get_required_value(data, 'Ks2', 'PSS2C'), Ks3=get_required_value(data, 'Ks3', 'PSS2C'), T8=get_required_value(data, 'T8', 'PSS2C'), T9=get_required_value(data, 'T9', 'PSS2C'), Ks1=get_required_value(data, 'Ks1', 'PSS2C'), T1=get_required_value(data, 'T1', 'PSS2C'), T2=get_required_value(data, 'T2', 'PSS2C'), T3=get_required_value(data, 'T3', 'PSS2C'), T4=get_required_value(data, 'T4', 'PSS2C'), T10=get_required_value(data, 'T10', 'PSS2C'), T11=get_required_value(data, 'T11', 'PSS2C'), Vs1_lim=get_required_value(data, 'Vs1_lim', 'PSS2C'), Vs2_lim=get_required_value(data, 'Vs2_lim', 'PSS2C'), Vst_lim=get_required_value(data, 'Vst_lim', 'PSS2C'), T12=get_required_value(data, 'T12', 'PSS2C'), T13=get_required_value(data, 'T13', 'PSS2C'), PSS_Hysteresis_param=get_required_value(data, 'PSS_Hysteresis_param', 'PSS2C'), Xcomp=get_required_value(data, 'Xcomp', 'PSS2C'), Tcomp=get_required_value(data, 'Tcomp', 'PSS2C'), hysteresis_binary_logic=data.get('hysteresis_binary_logic', None))


def sienna_pss2_c_to_json(value: SiennaPSS2C) -> dict[str, Any]:
    """Write every PSS2C slot to explicit schema property names.

    :param value: Typed PSS2C object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'input_code_1': value.input_code_1, 'remote_bus_control_1': value.remote_bus_control_1, 'input_code_2': value.input_code_2, 'remote_bus_control_2': value.remote_bus_control_2, 'M_rtf': value.M_rtf, 'N_rtf': value.N_rtf, 'Tw1': value.Tw1, 'Tw2': value.Tw2, 'T6': value.T6, 'Tw3': value.Tw3, 'Tw4': value.Tw4, 'T7': value.T7, 'Ks2': value.Ks2, 'Ks3': value.Ks3, 'T8': value.T8, 'T9': value.T9, 'Ks1': value.Ks1, 'T1': value.T1, 'T2': value.T2, 'T3': value.T3, 'T4': value.T4, 'T10': value.T10, 'T11': value.T11, 'Vs1_lim': value.Vs1_lim, 'Vs2_lim': value.Vs2_lim, 'Vst_lim': value.Vst_lim, 'T12': value.T12, 'T13': value.T13, 'PSS_Hysteresis_param': value.PSS_Hysteresis_param, 'Xcomp': value.Xcomp, 'Tcomp': value.Tcomp, 'hysteresis_binary_logic': value.hysteresis_binary_logic}
