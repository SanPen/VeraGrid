# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ZeroOrderBESS schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaZeroOrderBESS(SiennaSchemaModel):
    """Expose every declared ZeroOrderBESS property through fixed slots."""

    __slots__ = ('rated_voltage', 'rated_current', 'battery_voltage', 'battery_resistance', 'dc_dc_inductor', 'dc_link_capacitance', 'fs', 'kpv', 'kiv', 'kpi', 'kii', 'Vdc_ref',)

    def __init__(self, rated_voltage: float, rated_current: float, battery_voltage: float, battery_resistance: float, dc_dc_inductor: float, dc_link_capacitance: float, fs: float, kpv: float, kiv: float, kpi: float, kii: float, Vdc_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.rated_voltage: float = rated_voltage
        self.rated_current: float = rated_current
        self.battery_voltage: float = battery_voltage
        self.battery_resistance: float = battery_resistance
        self.dc_dc_inductor: float = dc_dc_inductor
        self.dc_link_capacitance: float = dc_link_capacitance
        self.fs: float = fs
        self.kpv: float = kpv
        self.kiv: float = kiv
        self.kpi: float = kpi
        self.kii: float = kii
        self.Vdc_ref: float = Vdc_ref


def parse_sienna_zero_order_bess(data: dict[str, Any]) -> SiennaZeroOrderBESS:
    """Parse declared ZeroOrderBESS properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ZeroOrderBESS object.
    """
    return SiennaZeroOrderBESS(rated_voltage=get_required_value(data, 'rated_voltage', 'ZeroOrderBESS'), rated_current=get_required_value(data, 'rated_current', 'ZeroOrderBESS'), battery_voltage=get_required_value(data, 'battery_voltage', 'ZeroOrderBESS'), battery_resistance=get_required_value(data, 'battery_resistance', 'ZeroOrderBESS'), dc_dc_inductor=get_required_value(data, 'dc_dc_inductor', 'ZeroOrderBESS'), dc_link_capacitance=get_required_value(data, 'dc_link_capacitance', 'ZeroOrderBESS'), fs=get_required_value(data, 'fs', 'ZeroOrderBESS'), kpv=get_required_value(data, 'kpv', 'ZeroOrderBESS'), kiv=get_required_value(data, 'kiv', 'ZeroOrderBESS'), kpi=get_required_value(data, 'kpi', 'ZeroOrderBESS'), kii=get_required_value(data, 'kii', 'ZeroOrderBESS'), Vdc_ref=data.get('Vdc_ref', None))


def sienna_zero_order_bess_to_json(value: SiennaZeroOrderBESS) -> dict[str, Any]:
    """Write every ZeroOrderBESS slot to explicit schema property names.

    :param value: Typed ZeroOrderBESS object.
    :return: JSON object with declared schema properties.
    """
    return {'rated_voltage': value.rated_voltage, 'rated_current': value.rated_current, 'battery_voltage': value.battery_voltage, 'battery_resistance': value.battery_resistance, 'dc_dc_inductor': value.dc_dc_inductor, 'dc_link_capacitance': value.dc_link_capacitance, 'fs': value.fs, 'kpv': value.kpv, 'kiv': value.kiv, 'kpi': value.kpi, 'kii': value.kii, 'Vdc_ref': value.Vdc_ref}
