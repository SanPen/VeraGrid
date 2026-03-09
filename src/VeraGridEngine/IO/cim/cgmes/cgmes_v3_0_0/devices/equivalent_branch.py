# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.equivalent_equipment import EquivalentEquipment
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

class EquivalentBranch(EquivalentEquipment):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='r', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', profiles=[]),
		CgmesProperty(property_name='r21', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', profiles=[]),
		CgmesProperty(property_name='x', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', profiles=[]),
		CgmesProperty(property_name='x21', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', profiles=[]),
		CgmesProperty(property_name='negativeR12', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', profiles=[]),
		CgmesProperty(property_name='negativeR21', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', profiles=[]),
		CgmesProperty(property_name='negativeX12', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', profiles=[]),
		CgmesProperty(property_name='negativeX21', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', profiles=[]),
		CgmesProperty(property_name='positiveR12', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', profiles=[]),
		CgmesProperty(property_name='positiveR21', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', profiles=[]),
		CgmesProperty(property_name='positiveX12', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', profiles=[]),
		CgmesProperty(property_name='positiveX21', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', profiles=[]),
		CgmesProperty(property_name='zeroR12', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', profiles=[]),
		CgmesProperty(property_name='zeroR21', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', profiles=[]),
		CgmesProperty(property_name='zeroX12', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', profiles=[]),
		CgmesProperty(property_name='zeroX21', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='EquivalentBranch'):
		EquivalentEquipment.__init__(self, rdfid, tpe)

		self.r: float = None
		self.r21: float = None
		self.x: float = None
		self.x21: float = None
		self.negativeR12: float = None
		self.negativeR21: float = None
		self.negativeX12: float = None
		self.negativeX21: float = None
		self.positiveR12: float = None
		self.positiveR21: float = None
		self.positiveX12: float = None
		self.positiveX21: float = None
		self.zeroR12: float = None
		self.zeroR21: float = None
		self.zeroX12: float = None
		self.zeroX21: float = None
