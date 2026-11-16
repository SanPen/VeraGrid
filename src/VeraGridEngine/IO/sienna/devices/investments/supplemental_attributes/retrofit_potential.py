# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna RetrofitPotential schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import SiennaValueCurve

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaRetrofitPotential(SiennaSchemaModel):
    """Expose every declared RetrofitPotential property through fixed slots."""

    __slots__ = ('id', 'eligible_generators', 'retrofit_fraction', 'retrofit_cost',)

    def __init__(self, id: int, eligible_generators: list[str], retrofit_fraction: float, retrofit_cost: SiennaValueCurve) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.eligible_generators: list[str] = eligible_generators
        self.retrofit_fraction: float = retrofit_fraction
        self.retrofit_cost: SiennaValueCurve = retrofit_cost


def parse_sienna_retrofit_potential(data: dict[str, Any]) -> SiennaRetrofitPotential:
    """Parse declared RetrofitPotential properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed RetrofitPotential object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import parse_sienna_value_curve
    return SiennaRetrofitPotential(id=get_required_value(data, 'id', 'RetrofitPotential'), eligible_generators=get_required_value(data, 'eligible_generators', 'RetrofitPotential'), retrofit_fraction=data.get('retrofit_fraction', None), retrofit_cost=parse_sienna_value_curve(get_required_value(data, 'retrofit_cost', 'RetrofitPotential')))

def sienna_retrofit_potential_to_json(value: SiennaRetrofitPotential) -> dict[str, Any]:
    """Write every RetrofitPotential slot to explicit schema property names.

    :param value: Typed RetrofitPotential object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import sienna_value_curve_to_json
    return {'id': value.id, 'eligible_generators': value.eligible_generators, 'retrofit_fraction': value.retrofit_fraction, 'retrofit_cost': sienna_value_curve_to_json(value.retrofit_cost)}
