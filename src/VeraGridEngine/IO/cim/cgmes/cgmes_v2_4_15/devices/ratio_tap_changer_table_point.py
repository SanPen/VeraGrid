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
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.ratio_tap_changer_table import RatioTapChangerTable

class RatioTapChangerTablePoint(Base):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='RatioTapChangerTable', class_type='RatioTapChangerTable', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Points of this table.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='b', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Percentage on a defined base.   For example, specify as 100 to indicate at the defined base.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='g', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Percentage on a defined base.   For example, specify as 100 to indicate at the defined base.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='r', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Percentage on a defined base.   For example, specify as 100 to indicate at the defined base.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='ratio', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A floating point number. The range is unspecified and not limited.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='step', class_type=int, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The tap step.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='x', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Percentage on a defined base.   For example, specify as 100 to indicate at the defined base.''', profiles=[CgmesProfileType.EQ]),
	)
	__slots__ = ('RatioTapChangerTable', 'b', 'g', 'r', 'ratio', 'step', 'x')
	def __init__(self, rdfid, tpe, resources=list(), class_replacements=dict()):
		Base.__init__(self, rdfid=rdfid, tpe=tpe, resources=resources, class_replacements=class_replacements)

		self.RatioTapChangerTable: RatioTapChangerTable | None = None
		self.b: float = None
		self.g: float = None
		self.r: float = None
		self.ratio: float = None
		self.step: int = None
		self.x: float = None
