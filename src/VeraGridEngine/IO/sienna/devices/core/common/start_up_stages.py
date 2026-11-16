# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna StartUpStages schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaStartUpStages(SiennaSchemaModel):
    """Expose every declared StartUpStages property through fixed slots."""

    __slots__ = ('startup_stages_type', 'cold', 'hot', 'warm',)

    def __init__(self, startup_stages_type: str, cold: float, hot: float, warm: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.startup_stages_type: str = startup_stages_type
        self.cold: float = cold
        self.hot: float = hot
        self.warm: float = warm


def parse_sienna_start_up_stages(data: dict[str, Any]) -> SiennaStartUpStages:
    """Parse declared StartUpStages properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed StartUpStages object.
    """
    return SiennaStartUpStages(startup_stages_type=data.get('startup_stages_type', None), cold=get_required_value(data, 'cold', 'StartUpStages'), hot=get_required_value(data, 'hot', 'StartUpStages'), warm=get_required_value(data, 'warm', 'StartUpStages'))


def sienna_start_up_stages_to_json(value: SiennaStartUpStages) -> dict[str, Any]:
    """Write every StartUpStages slot to explicit schema property names.

    :param value: Typed StartUpStages object.
    :return: JSON object with declared schema properties.
    """
    return {'startup_stages_type': value.startup_stages_type, 'cold': value.cold, 'hot': value.hot, 'warm': value.warm}
