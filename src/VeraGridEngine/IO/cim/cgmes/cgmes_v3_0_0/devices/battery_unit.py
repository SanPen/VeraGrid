# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.power_electronics_unit import PowerElectronicsUnit
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType, BatteryStateKind, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

class BatteryUnit(PowerElectronicsUnit):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='ratedE', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.Wh, description='''Real electrical energy.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='batteryState', class_type=BatteryStateKind, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The current state of the battery (charging, full, etc.).''', mandatory=True, profiles=[CgmesProfileType.SSH]),
		CgmesProperty(property_name='storedE', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.Wh, description='''Real electrical energy.''', mandatory=True, profiles=[CgmesProfileType.SSH]),
	)
	__slots__ = ('ratedE', 'batteryState', 'storedE')
	def __init__(self, rdfid='', tpe='BatteryUnit'):
		PowerElectronicsUnit.__init__(self, rdfid, tpe)

		self.ratedE: float = None
		self.batteryState: BatteryStateKind = None
		self.storedE: float = None
