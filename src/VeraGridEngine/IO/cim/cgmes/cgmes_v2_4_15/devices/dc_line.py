# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.dc_equipment_container import DCEquipmentContainer
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.sub_geographical_region import SubGeographicalRegion

class DCLine(DCEquipmentContainer):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='Region', class_type='SubGeographicalRegion', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''None''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='DCLine'):
		DCEquipmentContainer.__init__(self, rdfid, tpe)

		self.Region: SubGeographicalRegion | None = None
