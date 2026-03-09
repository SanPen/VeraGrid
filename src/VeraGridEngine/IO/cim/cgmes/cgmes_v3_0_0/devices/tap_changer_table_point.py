# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.base import Base
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

class TapChangerTablePoint(Base):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='b', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Percentage on a defined base.   For example, specify as 100 to indicate at the defined base.''', profiles=[]),
		CgmesProperty(property_name='g', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Percentage on a defined base.   For example, specify as 100 to indicate at the defined base.''', profiles=[]),
		CgmesProperty(property_name='r', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Percentage on a defined base.   For example, specify as 100 to indicate at the defined base.''', profiles=[]),
		CgmesProperty(property_name='ratio', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The voltage at the tap step divided by rated voltage of the transformer end having the tap changer. Hence this is a value close to one.
For example, if the ratio at step 1 is 1.01, and the rated voltage of the transformer end is 110kV, then the voltage obtained by setting the tap changer to step 1 to is 111.1kV.''', profiles=[]),
		CgmesProperty(property_name='step', class_type=int, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The tap step.''', profiles=[]),
		CgmesProperty(property_name='x', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Percentage on a defined base.   For example, specify as 100 to indicate at the defined base.''', profiles=[]),
	)
	def __init__(self, rdfid, tpe, resources=list(), class_replacements=dict()):
		Base.__init__(self, rdfid=rdfid, tpe=tpe, resources=resources, class_replacements=class_replacements)

		self.b: float = None
		self.g: float = None
		self.r: float = None
		self.ratio: float = None
		self.step: int = None
		self.x: float = None
