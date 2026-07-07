# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.conducting_equipment import ConductingEquipment
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol, CgmesProfileType
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.power_transformer_end import PowerTransformerEnd

class PowerTransformer(ConductingEquipment):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='PowerTransformerEnd', class_type='PowerTransformerEnd', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The ends of this power transformer.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='beforeShCircuitHighestOperatingCurrent', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.A, description='''Electrical current with sign convention: positive flow is out of the conducting equipment into the connectivity node. Can be both AC and DC.''', profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='beforeShCircuitHighestOperatingVoltage', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.V, description='''Electrical voltage, can be both AC and DC.''', profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='beforeShortCircuitAnglePf', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.deg, description='''Measurement of angle in degrees.''', profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='highSideMinOperatingU', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.V, description='''Electrical voltage, can be both AC and DC.''', profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='isPartOfGeneratorUnit', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Indicates whether the machine is part of a power station unit. Used for short circuit data exchange according to IEC 60909.  It has an impact on how the correction factors are calculated for transformers, since the transformer is not necessarily part of a synchronous machine and generating unit. It is not always possible to derive this information from the model. This is why the attribute is necessary.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='operationalValuesConsidered', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''It is used to define if the data (other attributes related to short circuit data exchange) defines long term operational conditions or not. Used for short circuit data exchange according to IEC 60909.''', profiles=[CgmesProfileType.SC]),
	)
	__slots__ = ('PowerTransformerEnd', 'beforeShCircuitHighestOperatingCurrent', 'beforeShCircuitHighestOperatingVoltage', 'beforeShortCircuitAnglePf', 'highSideMinOperatingU', 'isPartOfGeneratorUnit', 'operationalValuesConsidered')
	def __init__(self, rdfid='', tpe='PowerTransformer'):
		ConductingEquipment.__init__(self, rdfid, tpe)

		self.PowerTransformerEnd: PowerTransformerEnd | None = None
		self.beforeShCircuitHighestOperatingCurrent: float = None
		self.beforeShCircuitHighestOperatingVoltage: float = None
		self.beforeShortCircuitAnglePf: float = None
		self.highSideMinOperatingU: float = None
		self.isPartOfGeneratorUnit: bool = None
		self.operationalValuesConsidered: bool = None
