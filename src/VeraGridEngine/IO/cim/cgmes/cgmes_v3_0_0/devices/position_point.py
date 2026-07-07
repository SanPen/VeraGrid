# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.base import Base
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.location import Location

class PositionPoint(Base):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='Location', class_type='Location', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Location described by this position point.''', mandatory=True, profiles=[CgmesProfileType.GL]),
		CgmesProperty(property_name='sequenceNumber', class_type=int, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Zero-relative sequence number of this point within a series of points.''', profiles=[CgmesProfileType.GL]),
		CgmesProperty(property_name='xPosition', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''X axis position.''', mandatory=True, profiles=[CgmesProfileType.GL]),
		CgmesProperty(property_name='yPosition', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Y axis position.''', mandatory=True, profiles=[CgmesProfileType.GL]),
		CgmesProperty(property_name='zPosition', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''(if applicable) Z axis position.''', profiles=[CgmesProfileType.GL]),
	)
	__slots__ = ('Location', 'sequenceNumber', 'xPosition', 'yPosition', 'zPosition')
	def __init__(self, rdfid, tpe="PositionPoint", resources=list(), class_replacements=dict()):
		Base.__init__(self, rdfid=rdfid, tpe=tpe, resources=resources, class_replacements=class_replacements)

		self.Location: Location | None = None
		self.sequenceNumber: int = None
		self.xPosition: str = None
		self.yPosition: str = None
		self.zPosition: str = None
