# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.identified_object import IdentifiedObject
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.coordinate_system import CoordinateSystem
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.position_point import PositionPoint
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.power_system_resource import PowerSystemResource

class Location(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='CoordinateSystem', class_type='CoordinateSystem', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Coordinate system used to describe position points of this location.''', mandatory=True, profiles=[CgmesProfileType.GL]),
		CgmesProperty(property_name='PowerSystemResources', class_type='PowerSystemResource', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''All power system resources at this location.''', mandatory=True, profiles=[CgmesProfileType.GL]),
		CgmesProperty(property_name='PositionPoints', class_type='PositionPoint', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Sequence of position points describing this location, expressed in coordinate system 'Location.CoordinateSystem'.''', profiles=[CgmesProfileType.GL]),
	)
	__slots__ = ('CoordinateSystem', 'PowerSystemResources', 'PositionPoints')
	def __init__(self, rdfid='', tpe='Location'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.CoordinateSystem: CoordinateSystem | None = None
		self.PowerSystemResources: PowerSystemResource | None = None
		self.PositionPoints: PositionPoint | None = None
