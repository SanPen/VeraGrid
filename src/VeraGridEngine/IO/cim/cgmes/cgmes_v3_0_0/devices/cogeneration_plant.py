# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.power_system_resource import PowerSystemResource
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.thermal_generating_unit import ThermalGeneratingUnit

class CogenerationPlant(PowerSystemResource):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='ThermalGeneratingUnits', class_type='ThermalGeneratingUnit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A thermal generating unit may be a member of a cogeneration plant.''', profiles=[]),
	)
	__slots__ = ('ThermalGeneratingUnits',)
	def __init__(self, rdfid='', tpe='CogenerationPlant'):
		PowerSystemResource.__init__(self, rdfid, tpe)

		self.ThermalGeneratingUnits: ThermalGeneratingUnit | None = None
