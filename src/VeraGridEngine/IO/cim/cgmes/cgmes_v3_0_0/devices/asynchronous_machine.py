# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.rotating_machine import RotatingMachine
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType, AsynchronousMachineKind, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

class AsynchronousMachine(RotatingMachine):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='nominalFrequency', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.Hz, description='''Cycles per second.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='nominalSpeed', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.Hz, description='''Number of revolutions per second.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='converterFedDrive', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Indicates whether the machine is a converter fed drive. Used for short circuit data exchange according to IEC 60909.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='efficiency', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Percentage on a defined base.   For example, specify as 100 to indicate at the defined base.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='iaIrRatio', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Ratio of locked-rotor current to the rated current of the motor (Ia/Ir). Used for short circuit data exchange according to IEC 60909.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='polePairNumber', class_type=int, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Number of pole pairs of stator. Used for short circuit data exchange according to IEC 60909.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='ratedMechanicalPower', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Product of RMS value of the voltage and the RMS value of the in-phase component of the current.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='reversible', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Indicates for converter drive motors if the power can be reversible. Used for short circuit data exchange according to IEC 60909.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='rxLockedRotorRatio', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Locked rotor ratio (R/X). Used for short circuit data exchange according to IEC 60909.''', profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='asynchronousMachineType', class_type=AsynchronousMachineKind, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Indicates the type of Asynchronous Machine (motor or generator).''', mandatory=True, profiles=[CgmesProfileType.SSH], default_value=AsynchronousMachineKind.generator),
	)
	__slots__ = ('nominalFrequency', 'nominalSpeed', 'converterFedDrive', 'efficiency', 'iaIrRatio', 'polePairNumber', 'ratedMechanicalPower', 'reversible', 'rxLockedRotorRatio', 'asynchronousMachineType')
	def __init__(self, rdfid='', tpe='AsynchronousMachine'):
		RotatingMachine.__init__(self, rdfid, tpe)

		self.nominalFrequency: float = None
		self.nominalSpeed: float = None
		self.converterFedDrive: bool = None
		self.efficiency: float = None
		self.iaIrRatio: float = None
		self.polePairNumber: int = None
		self.ratedMechanicalPower: float = None
		self.reversible: bool = None
		self.rxLockedRotorRatio: float = None
		self.asynchronousMachineType: AsynchronousMachineKind = None
