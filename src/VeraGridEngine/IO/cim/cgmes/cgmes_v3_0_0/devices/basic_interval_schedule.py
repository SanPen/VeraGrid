# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import datetime
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.identified_object import IdentifiedObject
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

class BasicIntervalSchedule(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='startTime', class_type=datetime.datetime, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The time for the first time point.  The value can be a time of day, not a specific date.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='value1Unit', class_type=UnitSymbol, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Value1 units of measure.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='value2Unit', class_type=UnitSymbol, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Value2 units of measure.''', profiles=[CgmesProfileType.EQ]),
	)
	__slots__ = ('startTime', 'value1Unit', 'value2Unit')
	def __init__(self, rdfid='', tpe='BasicIntervalSchedule'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.startTime: datetime.datetime | None = None
		self.value1Unit: UnitSymbol = None
		self.value2Unit: UnitSymbol = None
