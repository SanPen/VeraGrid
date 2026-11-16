# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna RetirementPotential schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import SiennaValueCurve

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaRetirementPotential(SiennaSchemaModel):
    """Expose every declared RetirementPotential property through fixed slots."""

    __slots__ = ('id', 'eligible_generators', 'planned_retirement_year', 'build_year', 'retirement_cost',)

    def __init__(self, id: int, eligible_generators: list[str], planned_retirement_year: dict[str, object], build_year: dict[str, object], retirement_cost: SiennaValueCurve) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.eligible_generators: list[str] = eligible_generators
        self.planned_retirement_year: dict[str, object] = planned_retirement_year
        self.build_year: dict[str, object] = build_year
        self.retirement_cost: SiennaValueCurve = retirement_cost


def parse_sienna_retirement_potential(data: dict[str, Any]) -> SiennaRetirementPotential:
    """Parse declared RetirementPotential properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed RetirementPotential object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import parse_sienna_value_curve
    return SiennaRetirementPotential(id=get_required_value(data, 'id', 'RetirementPotential'), eligible_generators=get_required_value(data, 'eligible_generators', 'RetirementPotential'), planned_retirement_year=data.get('planned_retirement_year', None), build_year=data.get('build_year', None), retirement_cost=parse_sienna_value_curve(get_required_value(data, 'retirement_cost', 'RetirementPotential')))

def sienna_retirement_potential_to_json(value: SiennaRetirementPotential) -> dict[str, Any]:
    """Write every RetirementPotential slot to explicit schema property names.

    :param value: Typed RetirementPotential object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import sienna_value_curve_to_json
    return {'id': value.id, 'eligible_generators': value.eligible_generators, 'planned_retirement_year': value.planned_retirement_year, 'build_year': value.build_year, 'retirement_cost': sienna_value_curve_to_json(value.retirement_cost)}
