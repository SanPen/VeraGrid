# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.power_system_resource import PowerSystemResource
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import HydroPlantStorageKind
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.hydro_generating_unit import HydroGeneratingUnit
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.hydro_pump import HydroPump

class HydroPowerPlant(PowerSystemResource):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='HydroGeneratingUnits', class_type='HydroGeneratingUnit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The hydro generating unit belongs to a hydro power plant.''', profiles=[]),
		CgmesProperty(property_name='hydroPlantStorageType', class_type=HydroPlantStorageKind, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The type of hydro power plant water storage.''', profiles=[]),
		CgmesProperty(property_name='HydroPumps', class_type='HydroPump', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The hydro pump may be a member of a pumped storage plant or a pump for distributing water.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='HydroPowerPlant'):
		PowerSystemResource.__init__(self, rdfid, tpe)

		self.HydroGeneratingUnits: HydroGeneratingUnit | None = None
		self.hydroPlantStorageType: HydroPlantStorageKind | None = None
		self.HydroPumps: HydroPump | None = None
