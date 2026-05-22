# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.regulating_cond_eq import RegulatingCondEq
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

class ExternalNetworkInjection(RegulatingCondEq):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='governorSCD', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Active power variation with frequency.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='ikSecond', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Indicates whether initial symmetrical short-circuit current and power have been calculated according to IEC (Ik&quot;).''', profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='maxInitialSymShCCurrent', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.A, description='''Electrical current with sign convention: positive flow is out of the conducting equipment into the connectivity node. Can be both AC and DC.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='maxP', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Product of RMS value of the voltage and the RMS value of the in-phase component of the current.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='maxQ', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VAr, description='''Product of RMS value of the voltage and the RMS value of the quadrature component of the current.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='maxR0ToX0Ratio', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A floating point number. The range is unspecified and not limited.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='maxR1ToX1Ratio', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A floating point number. The range is unspecified and not limited.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='maxZ0ToZ1Ratio', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A floating point number. The range is unspecified and not limited.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='minInitialSymShCCurrent', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.A, description='''Electrical current with sign convention: positive flow is out of the conducting equipment into the connectivity node. Can be both AC and DC.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='minP', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Product of RMS value of the voltage and the RMS value of the in-phase component of the current.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='minQ', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VAr, description='''Product of RMS value of the voltage and the RMS value of the quadrature component of the current.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='minR0ToX0Ratio', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A floating point number. The range is unspecified and not limited.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='minR1ToX1Ratio', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A floating point number. The range is unspecified and not limited.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='minZ0ToZ1Ratio', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A floating point number. The range is unspecified and not limited.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='voltageFactor', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Per Unit - a positive or negative value referred to a defined base. Values typically range from -10 to +10.''', profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='referencePriority', class_type=int, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Priority of unit for use as powerflow voltage phase angle reference bus selection. 0 = don t care (default) 1 = highest priority. 2 is less than 1 and so on.''', mandatory=True, profiles=[CgmesProfileType.SSH], default_value=0),
		CgmesProperty(property_name='p', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Product of RMS value of the voltage and the RMS value of the in-phase component of the current.''', mandatory=True, profiles=[CgmesProfileType.SSH], default_value=0.0),
		CgmesProperty(property_name='q', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VAr, description='''Product of RMS value of the voltage and the RMS value of the quadrature component of the current.''', mandatory=True, profiles=[CgmesProfileType.SSH], default_value=0.0),
	)
	__slots__ = ('governorSCD', 'ikSecond', 'maxInitialSymShCCurrent', 'maxP', 'maxQ', 'maxR0ToX0Ratio', 'maxR1ToX1Ratio', 'maxZ0ToZ1Ratio', 'minInitialSymShCCurrent', 'minP', 'minQ', 'minR0ToX0Ratio', 'minR1ToX1Ratio', 'minZ0ToZ1Ratio', 'voltageFactor', 'referencePriority', 'p', 'q')
	def __init__(self, rdfid='', tpe='ExternalNetworkInjection'):
		RegulatingCondEq.__init__(self, rdfid, tpe)

		self.governorSCD: float = None
		self.ikSecond: bool = None
		self.maxInitialSymShCCurrent: float = None
		self.maxP: float = None
		self.maxQ: float = None
		self.maxR0ToX0Ratio: float = None
		self.maxR1ToX1Ratio: float = None
		self.maxZ0ToZ1Ratio: float = None
		self.minInitialSymShCCurrent: float = None
		self.minP: float = None
		self.minQ: float = None
		self.minR0ToX0Ratio: float = None
		self.minR1ToX1Ratio: float = None
		self.minZ0ToZ1Ratio: float = None
		self.voltageFactor: float = None
		self.referencePriority: int = None
		self.p: float = None
		self.q: float = None
