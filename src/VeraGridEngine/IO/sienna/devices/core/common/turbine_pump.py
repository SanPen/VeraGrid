# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TurbinePump schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTurbinePump(SiennaSchemaModel):
    """Expose every declared TurbinePump property through fixed slots."""

    __slots__ = ('turbine', 'pump',)

    def __init__(self, turbine: float, pump: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.turbine: float = turbine
        self.pump: float = pump


def parse_sienna_turbine_pump(data: dict[str, Any]) -> SiennaTurbinePump:
    """Parse declared TurbinePump properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TurbinePump object.
    """
    return SiennaTurbinePump(turbine=get_required_value(data, 'turbine', 'TurbinePump'), pump=get_required_value(data, 'pump', 'TurbinePump'))


def sienna_turbine_pump_to_json(value: SiennaTurbinePump) -> dict[str, Any]:
    """Write every TurbinePump slot to explicit schema property names.

    :param value: Typed TurbinePump object.
    :return: JSON object with declared schema properties.
    """
    return {'turbine': value.turbine, 'pump': value.pump}
