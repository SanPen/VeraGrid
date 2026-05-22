# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.dc_conducting_equipment import DCConductingEquipment
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

class DCGround(DCConductingEquipment):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='inductance', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.H, description='''Inductive part of reactance (imaginary part of impedance), at rated frequency.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='r', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', profiles=[CgmesProfileType.EQ]),
	)
	__slots__ = ('inductance', 'r')
	def __init__(self, rdfid='', tpe='DCGround'):
		DCConductingEquipment.__init__(self, rdfid, tpe)

		self.inductance: float = None
		self.r: float = None
