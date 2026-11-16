# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ThermalFuels schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaThermalFuels(Enum):
    """Values declared by the Sienna ThermalFuels schema."""

    ANTHRACITE_COAL = 'ANTHRACITE_COAL'
    BITUMINOUS_COAL = 'BITUMINOUS_COAL'
    LIGNITE_COAL = 'LIGNITE_COAL'
    SUBBITUMINOUS_COAL = 'SUBBITUMINOUS_COAL'
    WASTE_COAL = 'WASTE_COAL'
    REFINED_COAL = 'REFINED_COAL'
    SYNTHESIS_GAS_COAL = 'SYNTHESIS_GAS_COAL'
    DISTILLATE_FUEL_OIL = 'DISTILLATE_FUEL_OIL'
    JET_FUEL = 'JET_FUEL'
    KEROSENE = 'KEROSENE'
    PETROLEUM_COKE = 'PETROLEUM_COKE'
    RESIDUAL_FUEL_OIL = 'RESIDUAL_FUEL_OIL'
    PROPANE = 'PROPANE'
    SYNTHESIS_GAS_PETROLEUM_COKE = 'SYNTHESIS_GAS_PETROLEUM_COKE'
    WASTE_OIL = 'WASTE_OIL'
    BLAST_FURNACE_GAS = 'BLAST_FURNACE_GAS'
    NATURAL_GAS = 'NATURAL_GAS'
    OTHER_GAS = 'OTHER_GAS'
    AG_BYPRODUCT = 'AG_BYPRODUCT'
    MUNICIPAL_WASTE = 'MUNICIPAL_WASTE'
    OTHER_BIOMASS_SOLIDS = 'OTHER_BIOMASS_SOLIDS'
    WOOD_WASTE_SOLIDS = 'WOOD_WASTE_SOLIDS'
    OTHER_BIOMASS_LIQUIDS = 'OTHER_BIOMASS_LIQUIDS'
    SLUDGE_WASTE = 'SLUDGE_WASTE'
    BLACK_LIQUOR = 'BLACK_LIQUOR'
    WOOD_WASTE_LIQUIDS = 'WOOD_WASTE_LIQUIDS'
    LANDFILL_GAS = 'LANDFILL_GAS'
    OTHER_BIOMASS_GAS = 'OTHER_BIOMASS_GAS'
    NUCLEAR = 'NUCLEAR'
    WASTE_HEAT = 'WASTE_HEAT'
    TIRE_DERIVED_FUEL = 'TIRE_DERIVED_FUEL'
    COAL = 'COAL'
    GEOTHERMAL = 'GEOTHERMAL'
    OTHER = 'OTHER'


def parse_sienna_thermal_fuels(data: str) -> SiennaThermalFuels:
    """Parse one ThermalFuels enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaThermalFuels(data)


def sienna_thermal_fuels_to_json(value: SiennaThermalFuels) -> str:
    """Write one ThermalFuels enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
