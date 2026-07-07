# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.generating_unit import GeneratingUnit
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.caes_plant import CAESPlant
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.cogeneration_plant import CogenerationPlant
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.combined_cycle_plant import CombinedCyclePlant
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.fossil_fuel import FossilFuel

class ThermalGeneratingUnit(GeneratingUnit):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='CAESPlant', class_type='CAESPlant', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A thermal generating unit may be a member of a compressed air energy storage plant.''', profiles=[]),
		CgmesProperty(property_name='CogenerationPlant', class_type='CogenerationPlant', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A thermal generating unit may be a member of a cogeneration plant.''', profiles=[]),
		CgmesProperty(property_name='CombinedCyclePlant', class_type='CombinedCyclePlant', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A thermal generating unit may be a member of a combined cycle plant.''', profiles=[]),
		CgmesProperty(property_name='FossilFuels', class_type='FossilFuel', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A thermal generating unit may have one or more fossil fuels.''', profiles=[]),
	)
	__slots__ = ('CAESPlant', 'CogenerationPlant', 'CombinedCyclePlant', 'FossilFuels')
	def __init__(self, rdfid='', tpe='ThermalGeneratingUnit'):
		GeneratingUnit.__init__(self, rdfid, tpe)

		self.CAESPlant: CAESPlant | None = None
		self.CogenerationPlant: CogenerationPlant | None = None
		self.CombinedCyclePlant: CombinedCyclePlant | None = None
		self.FossilFuels: FossilFuel | None = None
