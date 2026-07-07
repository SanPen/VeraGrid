# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.conducting_equipment import ConductingEquipment
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

class SeriesCompensator(ConductingEquipment):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='r', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='r0', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='x', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='x0', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='varistorPresent', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Describe if a metal oxide varistor (mov) for over voltage protection is configured at the series compensator.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='varistorRatedCurrent', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.A, description='''Electrical current with sign convention: positive flow is out of the conducting equipment into the connectivity node. Can be both AC and DC.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='varistorVoltageThreshold', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.V, description='''Electrical voltage, can be both AC and DC.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
	)
	__slots__ = ('r', 'r0', 'x', 'x0', 'varistorPresent', 'varistorRatedCurrent', 'varistorVoltageThreshold')
	def __init__(self, rdfid='', tpe='SeriesCompensator'):
		ConductingEquipment.__init__(self, rdfid, tpe)

		self.r: float = None
		self.r0: float = None
		self.x: float = None
		self.x0: float = None
		self.varistorPresent: bool = None
		self.varistorRatedCurrent: float = None
		self.varistorVoltageThreshold: float = None
