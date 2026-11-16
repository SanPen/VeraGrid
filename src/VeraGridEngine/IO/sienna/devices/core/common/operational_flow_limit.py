# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna OperationalFlowLimit schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaOperationalFlowLimit(SiennaSchemaModel):
    """Expose every declared OperationalFlowLimit property through fixed slots."""

    __slots__ = ('from_to_min', 'from_to_max', 'to_from_min', 'to_from_max',)

    def __init__(self, from_to_min: float, from_to_max: float, to_from_min: float, to_from_max: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.from_to_min: float = from_to_min
        self.from_to_max: float = from_to_max
        self.to_from_min: float = to_from_min
        self.to_from_max: float = to_from_max


def parse_sienna_operational_flow_limit(data: dict[str, Any]) -> SiennaOperationalFlowLimit:
    """Parse declared OperationalFlowLimit properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed OperationalFlowLimit object.
    """
    return SiennaOperationalFlowLimit(from_to_min=get_required_value(data, 'from_to_min', 'OperationalFlowLimit'), from_to_max=get_required_value(data, 'from_to_max', 'OperationalFlowLimit'), to_from_min=get_required_value(data, 'to_from_min', 'OperationalFlowLimit'), to_from_max=get_required_value(data, 'to_from_max', 'OperationalFlowLimit'))


def sienna_operational_flow_limit_to_json(value: SiennaOperationalFlowLimit) -> dict[str, Any]:
    """Write every OperationalFlowLimit slot to explicit schema property names.

    :param value: Typed OperationalFlowLimit object.
    :return: JSON object with declared schema properties.
    """
    return {'from_to_min': value.from_to_min, 'from_to_max': value.from_to_max, 'to_from_min': value.to_from_min, 'to_from_max': value.to_from_max}
