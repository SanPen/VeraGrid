# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.identified_object import IdentifiedObject
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CurveStyle, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.curve_data import CurveData

class Curve(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='curveStyle', class_type=CurveStyle, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The style or shape of the curve.''', profiles=[]),
		CgmesProperty(property_name='xUnit', class_type=UnitSymbol, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The X-axis units of measure.''', profiles=[]),
		CgmesProperty(property_name='y1Unit', class_type=UnitSymbol, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The Y1-axis units of measure.''', profiles=[]),
		CgmesProperty(property_name='y2Unit', class_type=UnitSymbol, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The Y2-axis units of measure.''', profiles=[]),
		CgmesProperty(property_name='CurveDatas', class_type='CurveData', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The curve of  this curve data point.''', profiles=[]),
	)
	__slots__ = ('curveStyle', 'xUnit', 'y1Unit', 'y2Unit', 'CurveDatas')
	def __init__(self, rdfid='', tpe='Curve'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.curveStyle: CurveStyle = None
		self.xUnit: UnitSymbol = None
		self.y1Unit: UnitSymbol = None
		self.y2Unit: UnitSymbol = None
		self.CurveDatas: CurveData | None = None
