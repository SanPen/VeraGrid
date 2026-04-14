# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.identified_object import IdentifiedObject
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol, PhaseCode, UnitMultiplier
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.acdc_terminal import ACDCTerminal
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.power_system_resource import PowerSystemResource

class Measurement(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='measurementType', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Specifies the type of measurement.  For example, this specifies if the measurement represents an indoor temperature, outdoor temperature, bus voltage, line flow, etc.''', profiles=[]),
		CgmesProperty(property_name='phases', class_type=PhaseCode, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Indicates to which phases the measurement applies and avoids the need to use 'measurementType' to also encode phase information (which would explode the types). The phase information in Measurement, along with 'measurementType' and 'phases' uniquely defines a Measurement for a device, based on normal network phase. Their meaning will not change when the computed energizing phasing is changed due to jumpers or other reasons.
If the attribute is missing three phases (ABC) shall be assumed.''', profiles=[]),
		CgmesProperty(property_name='unitSymbol', class_type=UnitSymbol, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The unit of measure of the measured quantity.''', profiles=[]),
		CgmesProperty(property_name='unitMultiplier', class_type=UnitMultiplier, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The unit multiplier of the measured quantity.''', profiles=[]),
		CgmesProperty(property_name='Terminal', class_type='ACDCTerminal', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''One or more measurements may be associated with a terminal in the network.''', profiles=[]),
		CgmesProperty(property_name='PowerSystemResource', class_type='PowerSystemResource', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The measurements associated with this power system resource.''', profiles=[]),
	)
	__slots__ = ('measurementType', 'phases', 'unitSymbol', 'unitMultiplier', 'Terminal', 'PowerSystemResource')
	def __init__(self, rdfid='', tpe='Measurement'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.measurementType: str = None
		self.phases: PhaseCode = None
		self.unitSymbol: UnitSymbol = None
		self.unitMultiplier: UnitMultiplier | None  = None
		self.Terminal: ACDCTerminal= None
		self.PowerSystemResource: PowerSystemResource | None = None
