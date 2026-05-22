# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.identified_object import IdentifiedObject
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.energy_consumer import EnergyConsumer

class LoadResponseCharacteristic(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='EnergyConsumer', class_type='EnergyConsumer', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The set of loads that have the response characteristics.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='exponentModel', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Indicates the exponential voltage dependency model is to be used. If false, the coefficient model is to be used.
The exponential voltage dependency model consist of the attributes:
- pVoltageExponent
- qVoltageExponent
- pFrequencyExponent
- qFrequencyExponent.
The coefficient model consist of the attributes:
- pConstantImpedance
- pConstantCurrent
- pConstantPower
- qConstantImpedance
- qConstantCurrent
- qConstantPower.
The sum of pConstantImpedance, pConstantCurrent and pConstantPower shall equal 1.
The sum of qConstantImpedance, qConstantCurrent and qConstantPower shall equal 1.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='pConstantCurrent', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Portion of active power load modelled as constant current.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='pConstantImpedance', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Portion of active power load modelled as constant impedance.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='pConstantPower', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Portion of active power load modelled as constant power.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='pFrequencyExponent', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Exponent of per unit frequency effecting active power.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='pVoltageExponent', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Exponent of per unit voltage effecting real power.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='qConstantCurrent', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Portion of reactive power load modelled as constant current.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='qConstantImpedance', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Portion of reactive power load modelled as constant impedance.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='qConstantPower', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Portion of reactive power load modelled as constant power.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='qFrequencyExponent', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Exponent of per unit frequency effecting reactive power.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='qVoltageExponent', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Exponent of per unit voltage effecting reactive power.''', profiles=[CgmesProfileType.EQ]),
	)
	__slots__ = ('EnergyConsumer', 'exponentModel', 'pConstantCurrent', 'pConstantImpedance', 'pConstantPower', 'pFrequencyExponent', 'pVoltageExponent', 'qConstantCurrent', 'qConstantImpedance', 'qConstantPower', 'qFrequencyExponent', 'qVoltageExponent')
	def __init__(self, rdfid='', tpe='LoadResponseCharacteristic'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.EnergyConsumer: EnergyConsumer | None = None
		self.exponentModel: bool = None
		self.pConstantCurrent: float = None
		self.pConstantImpedance: float = None
		self.pConstantPower: float = None
		self.pFrequencyExponent: float = None
		self.pVoltageExponent: float = None
		self.qConstantCurrent: float = None
		self.qConstantImpedance: float = None
		self.qConstantPower: float = None
		self.qFrequencyExponent: float = None
		self.qVoltageExponent: float = None
