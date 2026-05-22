# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.power_system_resource import PowerSystemResource
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.wind_generating_unit import WindGeneratingUnit

class WindPowerPlant(PowerSystemResource):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='WindGeneratingUnits', class_type='WindGeneratingUnit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A wind generating unit or units may be a member of a wind power plant.''', profiles=[CgmesProfileType.EQ]),
	)
	__slots__ = ('WindGeneratingUnits',)
	def __init__(self, rdfid='', tpe='WindPowerPlant'):
		PowerSystemResource.__init__(self, rdfid, tpe)

		self.WindGeneratingUnits: WindGeneratingUnit | None = None
