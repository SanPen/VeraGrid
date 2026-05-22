# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.switch import Switch
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol, CgmesProfileType
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.ac_line_segment import ACLineSegment

class Cut(Switch):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='ACLineSegment', class_type='ACLineSegment', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The line segment to which the cut is applied.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='lengthFromTerminal1', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.m, description='''Unit of length. It shall be a positive value or zero.''', profiles=[CgmesProfileType.EQ]),
	)
	__slots__ = ('ACLineSegment', 'lengthFromTerminal1')
	def __init__(self, rdfid='', tpe='Cut'):
		Switch.__init__(self, rdfid, tpe)

		self.ACLineSegment: ACLineSegment | None = None
		self.lengthFromTerminal1: float = None
