# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.earth_fault_compensator import EarthFaultCompensator
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol, PetersenCoilModeKind
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

class PetersenCoil(EarthFaultCompensator):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='mode', class_type=PetersenCoilModeKind, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The mode of operation of the Petersen coil.''', profiles=[]),
		CgmesProperty(property_name='nominalU', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.V, description='''Electrical voltage, can be both AC and DC.''', profiles=[]),
		CgmesProperty(property_name='offsetCurrent', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.A, description='''Electrical current with sign convention: positive flow is out of the conducting equipment into the connectivity node. Can be both AC and DC.''', profiles=[]),
		CgmesProperty(property_name='positionCurrent', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.A, description='''Electrical current with sign convention: positive flow is out of the conducting equipment into the connectivity node. Can be both AC and DC.''', profiles=[]),
		CgmesProperty(property_name='xGroundMax', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', profiles=[]),
		CgmesProperty(property_name='xGroundMin', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', profiles=[]),
		CgmesProperty(property_name='xGroundNominal', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='PetersenCoil'):
		EarthFaultCompensator.__init__(self, rdfid, tpe)

		self.mode: PetersenCoilModeKind = None
		self.nominalU: float = None
		self.offsetCurrent: float = None
		self.positionCurrent: float = None
		self.xGroundMax: float = None
		self.xGroundMin: float = None
		self.xGroundNominal: float = None
