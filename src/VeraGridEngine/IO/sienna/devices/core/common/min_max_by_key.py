# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna MinMaxByKey schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaMinMaxByKey(SiennaSchemaModel):
    """Expose every declared MinMaxByKey property through fixed slots."""

    __slots__ = ('value',)

    def __init__(self, value: dict[str, object]) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.value: dict[str, object] = value


def parse_sienna_min_max_by_key(data: dict[str, Any]) -> SiennaMinMaxByKey:
    """Parse declared MinMaxByKey properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed MinMaxByKey object.
    """
    return SiennaMinMaxByKey(value=data.get('value', None))


def sienna_min_max_by_key_to_json(value: SiennaMinMaxByKey) -> dict[str, Any]:
    """Write every MinMaxByKey slot to explicit schema property names.

    :param value: Typed MinMaxByKey object.
    :return: JSON object with declared schema properties.
    """
    return {'value': value.value}
