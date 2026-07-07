# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.equivalent_equipment import EquivalentEquipment
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol, CgmesProfileType
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.reactive_capability_curve import ReactiveCapabilityCurve

class EquivalentInjection(EquivalentEquipment):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='ReactiveCapabilityCurve', class_type='ReactiveCapabilityCurve', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The equivalent injection using this reactive capability curve.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='maxP', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Product of RMS value of the voltage and the RMS value of the in-phase component of the current.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='maxQ', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VAr, description='''Product of RMS value of the voltage and the RMS value of the quadrature component of the current.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='minP', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Product of RMS value of the voltage and the RMS value of the in-phase component of the current.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='minQ', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VAr, description='''Product of RMS value of the voltage and the RMS value of the quadrature component of the current.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='r', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='r0', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='r2', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='regulationCapability', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Specifies whether or not the EquivalentInjection has the capability to regulate the local voltage.''', mandatory=True, profiles=[CgmesProfileType.EQ], default_value=False),
		CgmesProperty(property_name='x', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='x0', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='x2', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='regulationStatus', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Specifies the default regulation status of the EquivalentInjection.  True is regulating.  False is not regulating.''', profiles=[CgmesProfileType.SSH], default_value=False),
		CgmesProperty(property_name='regulationTarget', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.V, description='''Electrical voltage, can be both AC and DC.''', profiles=[CgmesProfileType.SSH]),
		CgmesProperty(property_name='p', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Product of RMS value of the voltage and the RMS value of the in-phase component of the current.''', mandatory=True, profiles=[CgmesProfileType.SSH], default_value=0.0),
		CgmesProperty(property_name='q', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VAr, description='''Product of RMS value of the voltage and the RMS value of the quadrature component of the current.''', mandatory=True, profiles=[CgmesProfileType.SSH], default_value=0.0),
	)
	__slots__ = ('ReactiveCapabilityCurve', 'maxP', 'maxQ', 'minP', 'minQ', 'r', 'r0', 'r2', 'regulationCapability', 'x', 'x0', 'x2', 'regulationStatus', 'regulationTarget', 'p', 'q')
	def __init__(self, rdfid='', tpe='EquivalentInjection'):
		EquivalentEquipment.__init__(self, rdfid, tpe)
		self.ReactiveCapabilityCurve: ReactiveCapabilityCurve | None = None
		self.maxP: float = None
		self.maxQ: float = None
		self.minP: float = None
		self.minQ: float = None
		self.r: float = None
		self.r0: float = None
		self.r2: float = None
		self.regulationCapability: bool = None
		self.x: float = None
		self.x0: float = None
		self.x2: float = None
		self.regulationStatus: bool = None
		self.regulationTarget: float = None
		self.p: float = None
		self.q: float = None
