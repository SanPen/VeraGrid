# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna QuadraticFunctionData schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaQuadraticFunctionData(SiennaSchemaModel):
    """Expose every declared QuadraticFunctionData property through fixed slots."""

    __slots__ = ('constant_term', 'function_type', 'proportional_term', 'quadratic_term',)

    def __init__(self, constant_term: float, function_type: str, proportional_term: float, quadratic_term: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.constant_term: float = constant_term
        self.function_type: str = function_type
        self.proportional_term: float = proportional_term
        self.quadratic_term: float = quadratic_term


def parse_sienna_quadratic_function_data(data: dict[str, Any]) -> SiennaQuadraticFunctionData:
    """Parse declared QuadraticFunctionData properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed QuadraticFunctionData object.
    """
    return SiennaQuadraticFunctionData(constant_term=get_required_value(data, 'constant_term', 'QuadraticFunctionData'), function_type=get_required_value(data, 'function_type', 'QuadraticFunctionData'), proportional_term=get_required_value(data, 'proportional_term', 'QuadraticFunctionData'), quadratic_term=get_required_value(data, 'quadratic_term', 'QuadraticFunctionData'))


def sienna_quadratic_function_data_to_json(value: SiennaQuadraticFunctionData) -> dict[str, Any]:
    """Write every QuadraticFunctionData slot to explicit schema property names.

    :param value: Typed QuadraticFunctionData object.
    :return: JSON object with declared schema properties.
    """
    return {'constant_term': value.constant_term, 'function_type': value.function_type, 'proportional_term': value.proportional_term, 'quadratic_term': value.quadratic_term}
