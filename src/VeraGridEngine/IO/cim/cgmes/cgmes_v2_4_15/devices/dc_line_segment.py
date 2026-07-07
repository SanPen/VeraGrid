# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.dc_conducting_equipment import DCConductingEquipment
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.per_lengthdc_line_parameter import PerLengthDCLineParameter

class DCLineSegment(DCConductingEquipment):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='capacitance', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.F, description='''Capacitive part of reactance (imaginary part of impedance), at rated frequency.''', profiles=[]),
		CgmesProperty(property_name='inductance', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.H, description='''Inductive part of reactance (imaginary part of impedance), at rated frequency.''', profiles=[]),
		CgmesProperty(property_name='resistance', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', profiles=[]),
		CgmesProperty(property_name='length', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.m, description='''Unit of length. Never negative.''', profiles=[]),
		CgmesProperty(property_name='PerLengthParameter', class_type='PerLengthDCLineParameter', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Set of per-length parameters for this line segment.''', profiles=[]),
	)
	__slots__ = ('capacitance', 'inductance', 'resistance', 'length', 'PerLengthParameter')
	def __init__(self, rdfid='', tpe='DCLineSegment'):
		DCConductingEquipment.__init__(self, rdfid, tpe)

		self.capacitance: float = None
		self.inductance: float = None
		self.resistance: float = None
		self.length: float = None
		self.PerLengthParameter: PerLengthDCLineParameter | None = None
