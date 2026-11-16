# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel
"""Sienna ``Arc`` device object."""

from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value


class SiennaArc(SiennaSchemaModel):
    """Represent one directed Sienna ``Arc`` between two buses."""

    __slots__ = ("identifier", "from_id", "to_id")

    def __init__(self, identifier: int, from_id: int, to_id: int) -> None:
        """Store one topology edge.

        :param identifier: Sienna arc identifier.
        :param from_id: Source bus identifier.
        :param to_id: Target bus identifier.
        :return: None.
        """
        self.identifier: int = identifier
        self.from_id: int = from_id
        self.to_id: int = to_id


def parse_sienna_arc(data: dict[str, Any]) -> SiennaArc:
    """Construct a Sienna arc object from validated JSON data.

    :param data: Raw Sienna arc data.
    :return: Parsed Sienna arc.
    """
    return SiennaArc(identifier=int(get_required_value(data, "id", "Arc")),
                     from_id=int(get_required_value(data, "from_id", "Arc")),
                     to_id=int(get_required_value(data, "to_id", "Arc")))


def sienna_arc_to_json(value: SiennaArc) -> dict[str, int]:
    """Write one typed arc to JSON.

    :param value: Typed arc.
    :return: Arc JSON object.
    """
    return {"id": value.identifier, "from_id": value.from_id, "to_id": value.to_id}
