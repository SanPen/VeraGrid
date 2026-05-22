# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.conductor import Conductor
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol, CgmesProfileType
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

class ACLineSegment(Conductor):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='b0ch', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Imaginary part of admittance.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='bch', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Imaginary part of admittance.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='g0ch', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Factor by which voltage must be multiplied to give corresponding power lost from a circuit. Real part of admittance.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='gch', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Factor by which voltage must be multiplied to give corresponding power lost from a circuit. Real part of admittance.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='r', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='r0', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='shortCircuitEndTemperature', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.degC, description='''Value of temperature in degrees Celsius.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='x', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='x0', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', mandatory=True, profiles=[CgmesProfileType.SC]),
	)
	__slots__ = ('b0ch', 'bch', 'g0ch', 'gch', 'r', 'r0', 'shortCircuitEndTemperature', 'x', 'x0')
	def __init__(self, rdfid='', tpe='ACLineSegment'):
		Conductor.__init__(self, rdfid, tpe)

		self.b0ch: float = None
		self.bch: float = None
		self.g0ch: float = None
		self.gch: float = None
		self.r: float = None
		self.r0: float = None
		self.shortCircuitEndTemperature: float = None
		self.x: float = None
		self.x0: float = None
