# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.regulating_cond_eq import RegulatingCondEq
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.power_electronics_unit import PowerElectronicsUnit

class PowerElectronicsConnection(RegulatingCondEq):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='maxQ', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VAr, description='''Product of RMS value of the voltage and the RMS value of the quadrature component of the current.''', profiles=[]),
		CgmesProperty(property_name='minQ', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VAr, description='''Product of RMS value of the voltage and the RMS value of the quadrature component of the current.''', profiles=[]),
		CgmesProperty(property_name='ratedS', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VA, description='''Product of the RMS value of the voltage and the RMS value of the current.''', profiles=[]),
		CgmesProperty(property_name='ratedU', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.V, description='''Electrical voltage, can be both AC and DC.''', profiles=[]),
		CgmesProperty(property_name='PowerElectronicsUnit', class_type='PowerElectronicsUnit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''An AC network connection may have several power electronics units connecting through it.''', profiles=[]),
		CgmesProperty(property_name='p', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Product of RMS value of the voltage and the RMS value of the in-phase component of the current.''', profiles=[]),
		CgmesProperty(property_name='q', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VAr, description='''Product of RMS value of the voltage and the RMS value of the quadrature component of the current.''', profiles=[]),
	)
	__slots__ = ('maxQ', 'minQ', 'ratedS', 'ratedU', 'PowerElectronicsUnit', 'p', 'q')
	def __init__(self, rdfid='', tpe='PowerElectronicsConnection'):
		RegulatingCondEq.__init__(self, rdfid, tpe)

		self.maxQ: float = None
		self.minQ: float = None
		self.ratedS: float = None
		self.ratedU: float = None
		self.PowerElectronicsUnit: PowerElectronicsUnit | None = None
		self.p: float = None
		self.q: float = None
