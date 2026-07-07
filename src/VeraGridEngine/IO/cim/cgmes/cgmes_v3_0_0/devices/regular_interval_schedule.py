# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import datetime
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.basic_interval_schedule import BasicIntervalSchedule
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

class RegularIntervalSchedule(BasicIntervalSchedule):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='timeStep', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.s, description='''Time, in seconds.''', profiles=[]),
		CgmesProperty(property_name='endTime', class_type=datetime.datetime, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The time for the last time point.  The value can be a time of day, not a specific date.''', profiles=[]),
	)
	__slots__ = ('timeStep', 'endTime')
	def __init__(self, rdfid='', tpe='RegularIntervalSchedule'):
		BasicIntervalSchedule.__init__(self, rdfid, tpe)

		self.timeStep: float = None

		self.endTime: datetime.datetime | None = None
