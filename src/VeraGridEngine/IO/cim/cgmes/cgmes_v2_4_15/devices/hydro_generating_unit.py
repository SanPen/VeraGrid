# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.generating_unit import GeneratingUnit
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import HydroEnergyConversionKind
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.hydro_power_plant import HydroPowerPlant

class HydroGeneratingUnit(GeneratingUnit):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='energyConversionCapability', class_type=HydroEnergyConversionKind, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Energy conversion capability for generating.''', profiles=[]),
		CgmesProperty(property_name='HydroPowerPlant', class_type='HydroPowerPlant', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The hydro generating unit belongs to a hydro power plant.''', profiles=[]),
	)
	__slots__ = ('energyConversionCapability', 'HydroPowerPlant')
	def __init__(self, rdfid='', tpe='HydroGeneratingUnit'):
		GeneratingUnit.__init__(self, rdfid, tpe)

		self.energyConversionCapability: HydroEnergyConversionKind | None = None
		self.HydroPowerPlant: HydroPowerPlant | None = None
