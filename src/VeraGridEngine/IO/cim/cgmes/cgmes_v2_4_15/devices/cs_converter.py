# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.acdc_converter import ACDCConverter
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CsOperatingModeKind, UnitSymbol, CsPpccControlKind, CgmesProfileType
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

class CsConverter(ACDCConverter):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='maxAlpha', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.deg, description='''Measurement of angle in degrees.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='maxGamma', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.deg, description='''Measurement of angle in degrees.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='maxIdc', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.A, description='''Electrical current with sign convention: positive flow is out of the conducting equipment into the connectivity node. Can be both AC and DC.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='minAlpha', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.deg, description='''Measurement of angle in degrees.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='minGamma', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.deg, description='''Measurement of angle in degrees.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='minIdc', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.A, description='''Electrical current with sign convention: positive flow is out of the conducting equipment into the connectivity node. Can be both AC and DC.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='ratedIdc', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.A, description='''Electrical current with sign convention: positive flow is out of the conducting equipment into the connectivity node. Can be both AC and DC.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='alpha', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.deg, description='''Measurement of angle in degrees.''', mandatory=True, profiles=[CgmesProfileType.SV]),
		CgmesProperty(property_name='gamma', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.deg, description='''Measurement of angle in degrees.''', mandatory=True, profiles=[CgmesProfileType.SV]),
		CgmesProperty(property_name='operatingMode', class_type=CsOperatingModeKind, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Indicates whether the DC pole is operating as an inverter or as a rectifier. CSC control variable used in power flow.''', mandatory=True, profiles=[CgmesProfileType.SSH]),
		CgmesProperty(property_name='pPccControl', class_type=CsPpccControlKind, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''None''', mandatory=True, profiles=[CgmesProfileType.SSH]),
		CgmesProperty(property_name='targetAlpha', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.deg, description='''Measurement of angle in degrees.''', mandatory=True, profiles=[CgmesProfileType.SSH]),
		CgmesProperty(property_name='targetGamma', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.deg, description='''Measurement of angle in degrees.''', mandatory=True, profiles=[CgmesProfileType.SSH]),
		CgmesProperty(property_name='targetIdc', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.A, description='''Electrical current with sign convention: positive flow is out of the conducting equipment into the connectivity node. Can be both AC and DC.''', mandatory=True, profiles=[CgmesProfileType.SSH]),
	)
	__slots__ = ('maxAlpha', 'maxGamma', 'maxIdc', 'minAlpha', 'minGamma', 'minIdc', 'ratedIdc', 'alpha', 'gamma', 'operatingMode', 'pPccControl', 'targetAlpha', 'targetGamma', 'targetIdc')
	def __init__(self, rdfid='', tpe='CsConverter'):
		ACDCConverter.__init__(self, rdfid, tpe)

		self.maxAlpha: float = None
		self.maxGamma: float = None
		self.maxIdc: float = None
		self.minAlpha: float = None
		self.minGamma: float = None
		self.minIdc: float = None
		self.ratedIdc: float = None
		self.alpha: float = None
		self.gamma: float = None
		self.operatingMode: CsOperatingModeKind = None
		self.pPccControl: CsPpccControlKind = None
		self.targetAlpha: float = None
		self.targetGamma: float = None
		self.targetIdc: float = None
