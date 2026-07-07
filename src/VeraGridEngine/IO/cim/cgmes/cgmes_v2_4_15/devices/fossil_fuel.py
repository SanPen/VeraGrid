# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.identified_object import IdentifiedObject
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import FuelType
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.thermal_generating_unit import ThermalGeneratingUnit

class FossilFuel(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='fossilFuelType', class_type=FuelType, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The type of fossil fuel, such as coal, oil, or gas.''', profiles=[]),
		CgmesProperty(property_name='ThermalGeneratingUnit', class_type='ThermalGeneratingUnit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A thermal generating unit may have one or more fossil fuels.''', profiles=[]),
	)
	__slots__ = ('fossilFuelType', 'ThermalGeneratingUnit')
	def __init__(self, rdfid='', tpe='FossilFuel'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.fossilFuelType: FuelType = None
		self.ThermalGeneratingUnit: ThermalGeneratingUnit | None = None
