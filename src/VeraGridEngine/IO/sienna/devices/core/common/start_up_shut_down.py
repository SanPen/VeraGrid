# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna StartUpShutDown schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaStartUpShutDown(SiennaSchemaModel):
    """Expose every declared StartUpShutDown property through fixed slots."""

    __slots__ = ('startup', 'shutdown',)

    def __init__(self, startup: float, shutdown: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.startup: float = startup
        self.shutdown: float = shutdown


def parse_sienna_start_up_shut_down(data: dict[str, Any]) -> SiennaStartUpShutDown:
    """Parse declared StartUpShutDown properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed StartUpShutDown object.
    """
    return SiennaStartUpShutDown(startup=data.get('startup', None), shutdown=data.get('shutdown', None))


def sienna_start_up_shut_down_to_json(value: SiennaStartUpShutDown) -> dict[str, Any]:
    """Write every StartUpShutDown slot to explicit schema property names.

    :param value: Typed StartUpShutDown object.
    :return: JSON object with declared schema properties.
    """
    return {'startup': value.startup, 'shutdown': value.shutdown}
