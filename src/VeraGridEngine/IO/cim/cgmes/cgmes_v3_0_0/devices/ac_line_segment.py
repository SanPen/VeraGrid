# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.conductor import Conductor
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol, CgmesProfileType
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.clamp import Clamp
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.cut import Cut

class ACLineSegment(Conductor):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='bch', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Imaginary part of admittance.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='gch', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Factor by which voltage must be multiplied to give corresponding power lost from a circuit. Real part of admittance.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='r', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='x', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='Clamp', class_type='Clamp', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The clamps connected to the line segment.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='Cut', class_type='Cut', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Cuts applied to the line segment.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='b0ch', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Imaginary part of admittance.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='g0ch', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Factor by which voltage must be multiplied to give corresponding power lost from a circuit. Real part of admittance.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='r0', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='shortCircuitEndTemperature', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.degC, description='''Value of temperature in degrees Celsius.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='x0', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', mandatory=True, profiles=[CgmesProfileType.SC]),
	)
	__slots__ = ('bch', 'gch', 'r', 'x', 'Clamp', 'Cut', 'b0ch', 'g0ch', 'r0', 'shortCircuitEndTemperature', 'x0')
	def __init__(self, rdfid='', tpe='ACLineSegment'):
		Conductor.__init__(self, rdfid, tpe)

		self.bch: float = None
		self.gch: float = None
		self.r: float = None
		self.x: float = None

		self.Clamp: Clamp | None = None

		self.Cut: Cut | None = None
		self.b0ch: float = None
		self.g0ch: float = None
		self.r0: float = None
		self.shortCircuitEndTemperature: float = None
		self.x0: float = None
