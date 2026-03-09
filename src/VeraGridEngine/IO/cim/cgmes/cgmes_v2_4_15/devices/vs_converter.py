# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.acdc_converter import ACDCConverter
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol, VsPpccControlKind, VsQpccControlKind
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.vs_capability_curve import VsCapabilityCurve

class VsConverter(ACDCConverter):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='CapabilityCurve', class_type='VsCapabilityCurve', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''All converters with this capability curve.''', profiles=[]),
		CgmesProperty(property_name='maxModulationIndex', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A floating point number. The range is unspecified and not limited.''', profiles=[]),
		CgmesProperty(property_name='maxValveCurrent', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.A, description='''Electrical current with sign convention: positive flow is out of the conducting equipment into the connectivity node. Can be both AC and DC.''', profiles=[]),
		CgmesProperty(property_name='delta', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.deg, description='''Measurement of angle in degrees.''', profiles=[]),
		CgmesProperty(property_name='uf', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.V, description='''Electrical voltage, can be both AC and DC.''', profiles=[]),
		CgmesProperty(property_name='droop', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Per Unit - a positive or negative value referred to a defined base. Values typically range from -10 to +10.''', profiles=[]),
		CgmesProperty(property_name='droopCompensation', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', profiles=[]),
		CgmesProperty(property_name='pPccControl', class_type=VsPpccControlKind, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Kind of control of real power and/or DC voltage.''', profiles=[]),
		CgmesProperty(property_name='qPccControl', class_type=VsQpccControlKind, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''None''', profiles=[]),
		CgmesProperty(property_name='qShare', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Percentage on a defined base.   For example, specify as 100 to indicate at the defined base.''', profiles=[]),
		CgmesProperty(property_name='targetQpcc', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VAr, description='''Product of RMS value of the voltage and the RMS value of the quadrature component of the current.''', profiles=[]),
		CgmesProperty(property_name='targetUpcc', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.V, description='''Electrical voltage, can be both AC and DC.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='VsConverter'):
		ACDCConverter.__init__(self, rdfid, tpe)

		self.CapabilityCurve: VsCapabilityCurve | None = None
		self.maxModulationIndex: float = None
		self.maxValveCurrent: float = None
		self.delta: float = None
		self.uf: float = None
		self.droop: float = None
		self.droopCompensation: float = None
		self.pPccControl: VsPpccControlKind = None
		self.qPccControl: VsQpccControlKind = None
		self.qShare: float = None
		self.targetQpcc: float = None
		self.targetUpcc: float = None
