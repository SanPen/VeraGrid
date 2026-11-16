# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel
"""Statically typed Sienna ComplexNumber schema object."""

from typing import Any


class SiennaComplexNumber(SiennaSchemaModel):
    """Represent the real and imaginary parts of one Sienna complex number."""

    __slots__ = ("real", "imag")

    def __init__(self, real: float | None, imag: float | None) -> None:
        """Store each declared complex-number property in a fixed slot.

        :param real: Real component when declared.
        :param imag: Imaginary component when declared.
        :return: None.
        """
        self.real: float | None = real
        self.imag: float | None = imag


def parse_sienna_complex_number(data: dict[str, Any]) -> SiennaComplexNumber:
    """Parse a ComplexNumber JSON object into typed scalar slots.

    :param data: Schema-validated ComplexNumber JSON object.
    :return: Typed ComplexNumber object.
    """
    real_value: Any | None = data.get("real", None)
    imag_value: Any | None = data.get("imag", None)
    return SiennaComplexNumber(real=None if real_value is None else float(real_value),
                               imag=None if imag_value is None else float(imag_value))


def sienna_complex_number_to_json(value: SiennaComplexNumber) -> dict[str, float | None]:
    """Write typed complex-number slots to JSON fields.

    :param value: Typed complex number.
    :return: ComplexNumber JSON object.
    """
    return {"real": value.real, "imag": value.imag}
