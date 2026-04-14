# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.conducting_equipment import ConductingEquipment
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.acdc_converterdc_terminal import ACDCConverterDCTerminal
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.terminal import Terminal

class ACDCConverter(ConductingEquipment):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='baseS', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VA, description='''Product of the RMS value of the voltage and the RMS value of the current.''', profiles=[]),
		CgmesProperty(property_name='idleLoss', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Product of RMS value of the voltage and the RMS value of the in-phase component of the current.''', profiles=[]),
		CgmesProperty(property_name='maxUdc', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.V, description='''Electrical voltage, can be both AC and DC.''', profiles=[]),
		CgmesProperty(property_name='minUdc', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.V, description='''Electrical voltage, can be both AC and DC.''', profiles=[]),
		CgmesProperty(property_name='numberOfValves', class_type=int, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Number of valves in the converter. Used in loss calculations.''', profiles=[]),
		CgmesProperty(property_name='ratedUdc', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.V, description='''Electrical voltage, can be both AC and DC.''', profiles=[]),
		CgmesProperty(property_name='resistiveLoss', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', profiles=[]),
		CgmesProperty(property_name='switchingLoss', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.WPerA, description='''Active power variation with current flow.''', profiles=[]),
		CgmesProperty(property_name='valveU0', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.V, description='''Electrical voltage, can be both AC and DC.''', profiles=[]),
		CgmesProperty(property_name='maxP', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Product of RMS value of the voltage and the RMS value of the in-phase component of the current.''', profiles=[]),
		CgmesProperty(property_name='minP', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Product of RMS value of the voltage and the RMS value of the in-phase component of the current.''', profiles=[]),
		CgmesProperty(property_name='PccTerminal', class_type='Terminal', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Point of common coupling terminal for this converter DC side. It is typically the terminal on the power transformer (or switch) closest to the AC network.''', profiles=[]),
		CgmesProperty(property_name='DCTerminals', class_type='ACDCConverterDCTerminal', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A DC converter have DC converter terminals. A converter has two DC converter terminals.''', profiles=[]),
		CgmesProperty(property_name='idc', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.A, description='''Electrical current with sign convention: positive flow is out of the conducting equipment into the connectivity node. Can be both AC and DC.''', profiles=[]),
		CgmesProperty(property_name='poleLossP', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Product of RMS value of the voltage and the RMS value of the in-phase component of the current.''', profiles=[]),
		CgmesProperty(property_name='uc', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.V, description='''Electrical voltage, can be both AC and DC.''', profiles=[]),
		CgmesProperty(property_name='udc', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.V, description='''Electrical voltage, can be both AC and DC.''', profiles=[]),
		CgmesProperty(property_name='p', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Product of RMS value of the voltage and the RMS value of the in-phase component of the current.''', profiles=[]),
		CgmesProperty(property_name='q', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VAr, description='''Product of RMS value of the voltage and the RMS value of the quadrature component of the current.''', profiles=[]),
		CgmesProperty(property_name='targetPpcc', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Product of RMS value of the voltage and the RMS value of the in-phase component of the current.''', profiles=[]),
		CgmesProperty(property_name='targetUdc', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.V, description='''Electrical voltage, can be both AC and DC.''', profiles=[]),
	)
	__slots__ = ('baseS', 'idleLoss', 'maxUdc', 'minUdc', 'numberOfValves', 'ratedUdc', 'resistiveLoss', 'switchingLoss', 'valveU0', 'maxP', 'minP', 'PccTerminal', 'DCTerminals', 'idc', 'poleLossP', 'uc', 'udc', 'p', 'q', 'targetPpcc', 'targetUdc')
	def __init__(self, rdfid='', tpe='ACDCConverter'):
		ConductingEquipment.__init__(self, rdfid, tpe)

		self.baseS: float = None
		self.idleLoss: float = None
		self.maxUdc: float = None
		self.minUdc: float = None
		self.numberOfValves: int = None
		self.ratedUdc: float = None
		self.resistiveLoss: float = None
		self.switchingLoss: float = None
		self.valveU0: float = None
		self.maxP: float = None
		self.minP: float = None

		self.PccTerminal: Terminal | None = None

		self.DCTerminals: ACDCConverterDCTerminal | None = None
		self.idc: float = None
		self.poleLossP: float = None
		self.uc: float = None
		self.udc: float = None
		self.p: float = None
		self.q: float = None
		self.targetPpcc: float = None
		self.targetUdc: float = None
