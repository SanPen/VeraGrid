# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.rotating_machine import RotatingMachine
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import SynchronousMachineKind, SynchronousMachineOperatingMode, ShortCircuitRotorKind, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.reactive_capability_curve import ReactiveCapabilityCurve

class SynchronousMachine(RotatingMachine):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='InitialReactiveCapabilityCurve', class_type='ReactiveCapabilityCurve', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The default reactive capability curve for use by a synchronous machine.''', profiles=[]),
		CgmesProperty(property_name='maxQ', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VAr, description='''Product of RMS value of the voltage and the RMS value of the quadrature component of the current.''', profiles=[]),
		CgmesProperty(property_name='minQ', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VAr, description='''Product of RMS value of the voltage and the RMS value of the quadrature component of the current.''', profiles=[]),
		CgmesProperty(property_name='qPercent', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Percentage on a defined base.   For example, specify as 100 to indicate at the defined base.''', profiles=[]),
		CgmesProperty(property_name='type', class_type=SynchronousMachineKind, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Modes that this synchronous machine can operate in.''', profiles=[]),
		CgmesProperty(property_name='earthing', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Indicates whether or not the generator is earthed. Used for short circuit data exchange according to IEC 60909.''', profiles=[]),
		CgmesProperty(property_name='earthingStarPointR', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', profiles=[]),
		CgmesProperty(property_name='earthingStarPointX', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', profiles=[]),
		CgmesProperty(property_name='ikk', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.A, description='''Electrical current with sign convention: positive flow is out of the conducting equipment into the connectivity node. Can be both AC and DC.''', profiles=[]),
		CgmesProperty(property_name='mu', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Factor to calculate the breaking current (Section 4.5.2.1 in IEC 60909-0).
Used only for single fed short circuit on a generator (Section 4.3.4.2. in IEC 60909-0).''', profiles=[]),
		CgmesProperty(property_name='x0', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', profiles=[]),
		CgmesProperty(property_name='r0', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', profiles=[]),
		CgmesProperty(property_name='x2', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', profiles=[]),
		CgmesProperty(property_name='r2', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', profiles=[]),
		CgmesProperty(property_name='r', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', profiles=[]),
		CgmesProperty(property_name='satDirectSubtransX', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Per Unit - a positive or negative value referred to a defined base. Values typically range from -10 to +10.''', profiles=[]),
		CgmesProperty(property_name='satDirectSyncX', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Per Unit - a positive or negative value referred to a defined base. Values typically range from -10 to +10.''', profiles=[]),
		CgmesProperty(property_name='satDirectTransX', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Per Unit - a positive or negative value referred to a defined base. Values typically range from -10 to +10.''', profiles=[]),
		CgmesProperty(property_name='shortCircuitRotorType', class_type=ShortCircuitRotorKind, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Type of rotor, used by short circuit applications, only for single fed short circuit according to IEC 60909.''', profiles=[]),
		CgmesProperty(property_name='voltageRegulationRange', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Percentage on a defined base.   For example, specify as 100 to indicate at the defined base.''', profiles=[]),
		CgmesProperty(property_name='operatingMode', class_type=SynchronousMachineOperatingMode, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Current mode of operation.''', profiles=[]),
		CgmesProperty(property_name='referencePriority', class_type=int, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Priority of unit for use as powerflow voltage phase angle reference bus selection. 0 = don t care (default) 1 = highest priority. 2 is less than 1 and so on.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='SynchronousMachine'):
		RotatingMachine.__init__(self, rdfid, tpe)

		self.InitialReactiveCapabilityCurve: ReactiveCapabilityCurve | None = None
		self.maxQ: float = None
		self.minQ: float = None
		self.qPercent: float = None
		self.type: SynchronousMachineKind = None
		self.earthing: bool = None
		self.earthingStarPointR: float = None
		self.earthingStarPointX: float = None
		self.ikk: float = None
		self.mu: float = None
		self.x0: float = None
		self.r0: float = None
		self.x2: float = None
		self.r2: float = None
		self.r: float = None
		self.satDirectSubtransX: float = None
		self.satDirectSyncX: float = None
		self.satDirectTransX: float = None
		self.shortCircuitRotorType: ShortCircuitRotorKind = None
		self.voltageRegulationRange: float = None
		self.operatingMode: SynchronousMachineOperatingMode = None
		self.referencePriority: int = None
