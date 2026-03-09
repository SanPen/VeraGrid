# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.identified_object import IdentifiedObject
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.control import Control
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.location import Location
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.measurement import Measurement

class PowerSystemResource(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='Location', class_type='Location', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Location of this power system resource.''', profiles=[]),
		CgmesProperty(property_name='Controls', class_type='Control', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The controller outputs used to actually govern a regulating device, e.g. the magnetization of a synchronous machine or capacitor bank breaker actuator.''', profiles=[]),
		CgmesProperty(property_name='Measurements', class_type='Measurement', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The measurements associated with this power system resource.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='PowerSystemResource'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.Location: Location | None = None
		self.Controls: Control | None = None
		self.Measurements: Measurement | None = None
