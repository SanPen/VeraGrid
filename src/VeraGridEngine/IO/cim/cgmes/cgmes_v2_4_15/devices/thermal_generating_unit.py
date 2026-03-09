# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.generating_unit import GeneratingUnit
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.fossil_fuel import FossilFuel

class ThermalGeneratingUnit(GeneratingUnit):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='FossilFuels', class_type='FossilFuel', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A thermal generating unit may have one or more fossil fuels.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='ThermalGeneratingUnit'):
		GeneratingUnit.__init__(self, rdfid, tpe)

		self.FossilFuels: FossilFuel | None = None
