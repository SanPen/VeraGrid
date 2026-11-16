# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ImpedanceCorrectionData schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.piecewise_linear_data import SiennaPiecewiseLinearData

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaImpedanceCorrectionData(SiennaSchemaModel):
    """Expose every declared ImpedanceCorrectionData property through fixed slots."""

    __slots__ = ('id', 'table_number', 'tap_ratio_correction_curve', 'phase_angle_correction_curve', 'transformer_winding', 'transformer_control_mode',)

    def __init__(self, id: int, table_number: int, tap_ratio_correction_curve: SiennaPiecewiseLinearData, phase_angle_correction_curve: SiennaPiecewiseLinearData, transformer_winding: str, transformer_control_mode: str) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.table_number: int = table_number
        self.tap_ratio_correction_curve: SiennaPiecewiseLinearData = tap_ratio_correction_curve
        self.phase_angle_correction_curve: SiennaPiecewiseLinearData = phase_angle_correction_curve
        self.transformer_winding: str = transformer_winding
        self.transformer_control_mode: str = transformer_control_mode


def parse_sienna_impedance_correction_data(data: dict[str, Any]) -> SiennaImpedanceCorrectionData:
    """Parse declared ImpedanceCorrectionData properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ImpedanceCorrectionData object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.piecewise_linear_data import parse_sienna_piecewise_linear_data
    return SiennaImpedanceCorrectionData(id=get_required_value(data, 'id', 'ImpedanceCorrectionData'), table_number=get_required_value(data, 'table_number', 'ImpedanceCorrectionData'), tap_ratio_correction_curve=None if data.get('tap_ratio_correction_curve', None) is None else parse_sienna_piecewise_linear_data(data.get('tap_ratio_correction_curve', None)), phase_angle_correction_curve=None if data.get('phase_angle_correction_curve', None) is None else parse_sienna_piecewise_linear_data(data.get('phase_angle_correction_curve', None)), transformer_winding=get_required_value(data, 'transformer_winding', 'ImpedanceCorrectionData'), transformer_control_mode=get_required_value(data, 'transformer_control_mode', 'ImpedanceCorrectionData'))

def sienna_impedance_correction_data_to_json(value: SiennaImpedanceCorrectionData) -> dict[str, Any]:
    """Write every ImpedanceCorrectionData slot to explicit schema property names.

    :param value: Typed ImpedanceCorrectionData object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.piecewise_linear_data import sienna_piecewise_linear_data_to_json
    return {'id': value.id, 'table_number': value.table_number, 'tap_ratio_correction_curve': None if value.tap_ratio_correction_curve is None else sienna_piecewise_linear_data_to_json(value.tap_ratio_correction_curve), 'phase_angle_correction_curve': None if value.phase_angle_correction_curve is None else sienna_piecewise_linear_data_to_json(value.phase_angle_correction_curve), 'transformer_winding': value.transformer_winding, 'transformer_control_mode': value.transformer_control_mode}
