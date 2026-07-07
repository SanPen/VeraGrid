# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.generating_unit import GeneratingUnit
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import WindGenUnitKind, CgmesProfileType
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.wind_power_plant import WindPowerPlant

class WindGeneratingUnit(GeneratingUnit):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='windGenUnitType', class_type=WindGenUnitKind, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The kind of wind generating unit.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='WindPowerPlant', class_type='WindPowerPlant', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A wind power plant may have wind generating units.''', profiles=[CgmesProfileType.EQ]),
	)
	__slots__ = ('windGenUnitType', 'WindPowerPlant')
	def __init__(self, rdfid='', tpe='WindGeneratingUnit'):
		GeneratingUnit.__init__(self, rdfid, tpe)

		self.windGenUnitType: WindGenUnitKind = None
		self.WindPowerPlant: WindPowerPlant | None = None
