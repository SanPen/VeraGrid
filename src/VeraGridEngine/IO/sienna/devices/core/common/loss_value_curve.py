# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna LossValueCurve schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.incremental_curve import SiennaIncrementalCurve
    from VeraGridEngine.IO.sienna.devices.core.common.input_output_curve import SiennaInputOutputCurve

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaLossValueCurve(SiennaSchemaModel):
    """Expose every declared LossValueCurve property through fixed slots."""

    __slots__ = ('value',)

    def __init__(self, value: SiennaInputOutputCurve | SiennaIncrementalCurve) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.value: SiennaInputOutputCurve | SiennaIncrementalCurve = value


def parse_sienna_loss_value_curve(data: dict[str, Any]) -> SiennaLossValueCurve:
    """Parse declared LossValueCurve properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed LossValueCurve object.
    """
    return SiennaLossValueCurve(value=data.get('value', None))


def sienna_loss_value_curve_to_json(value: SiennaLossValueCurve) -> dict[str, Any]:
    """Write every LossValueCurve slot to explicit schema property names.

    :param value: Typed LossValueCurve object.
    :return: JSON object with declared schema properties.
    """
    return {'value': value.value}
