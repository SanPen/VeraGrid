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
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.solar_power_plant import SolarPowerPlant

class SolarGeneratingUnit(GeneratingUnit):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='SolarPowerPlant', class_type='SolarPowerPlant', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A solar power plant may have solar generating units.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='SolarGeneratingUnit'):
		GeneratingUnit.__init__(self, rdfid, tpe)

		self.SolarPowerPlant: SolarPowerPlant | None = None
