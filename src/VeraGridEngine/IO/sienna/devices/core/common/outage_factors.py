# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna OutageFactors schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaOutageFactors(SiennaSchemaModel):
    """Expose every declared OutageFactors property through fixed slots."""

    __slots__ = ('planned', 'forced',)

    def __init__(self, planned: float, forced: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.planned: float = planned
        self.forced: float = forced


def parse_sienna_outage_factors(data: dict[str, Any]) -> SiennaOutageFactors:
    """Parse declared OutageFactors properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed OutageFactors object.
    """
    return SiennaOutageFactors(planned=data.get('planned', None), forced=data.get('forced', None))


def sienna_outage_factors_to_json(value: SiennaOutageFactors) -> dict[str, Any]:
    """Write every OutageFactors slot to explicit schema property names.

    :param value: Typed OutageFactors object.
    :return: JSON object with declared schema properties.
    """
    return {'planned': value.planned, 'forced': value.forced}
