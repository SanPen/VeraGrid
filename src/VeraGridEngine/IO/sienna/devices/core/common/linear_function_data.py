# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna LinearFunctionData schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaLinearFunctionData(SiennaSchemaModel):
    """Expose every declared LinearFunctionData property through fixed slots."""

    __slots__ = ('constant_term', 'function_type', 'proportional_term',)

    def __init__(self, constant_term: float, function_type: str, proportional_term: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.constant_term: float = constant_term
        self.function_type: str = function_type
        self.proportional_term: float = proportional_term


def parse_sienna_linear_function_data(data: dict[str, Any]) -> SiennaLinearFunctionData:
    """Parse declared LinearFunctionData properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed LinearFunctionData object.
    """
    return SiennaLinearFunctionData(constant_term=get_required_value(data, 'constant_term', 'LinearFunctionData'), function_type=get_required_value(data, 'function_type', 'LinearFunctionData'), proportional_term=get_required_value(data, 'proportional_term', 'LinearFunctionData'))


def sienna_linear_function_data_to_json(value: SiennaLinearFunctionData) -> dict[str, Any]:
    """Write every LinearFunctionData slot to explicit schema property names.

    :param value: Typed LinearFunctionData object.
    :return: JSON object with declared schema properties.
    """
    return {'constant_term': value.constant_term, 'function_type': value.function_type, 'proportional_term': value.proportional_term}
