# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel
"""Statically typed Sienna MinMax schema object."""

from typing import Any


class SiennaMinMax(SiennaSchemaModel):
    """Represent declared lower and upper scalar bounds."""

    __slots__ = ("min", "max")

    def __init__(self, minimum: float | None, maximum: float | None) -> None:
        """Store each declared MinMax property in a fixed slot.

        :param minimum: Lower bound when declared.
        :param maximum: Upper bound when declared.
        :return: None.
        """
        self.min: float | None = minimum
        self.max: float | None = maximum


def parse_sienna_min_max(data: dict[str, Any]) -> SiennaMinMax:
    """Parse a MinMax JSON object into typed scalar slots.

    :param data: Schema-validated MinMax JSON object.
    :return: Typed MinMax object.
    """
    minimum_value: Any | None = data.get("min", None)
    maximum_value: Any | None = data.get("max", None)
    return SiennaMinMax(minimum=None if minimum_value is None else float(minimum_value),
                         maximum=None if maximum_value is None else float(maximum_value))


def sienna_min_max_to_json(value: SiennaMinMax) -> dict[str, float | None]:
    """Write typed MinMax slots to their declared JSON properties.

    :param value: Typed MinMax object.
    :return: MinMax JSON object.
    """
    return {"min": value.min, "max": value.max}
