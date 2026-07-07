# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.identified_object import IdentifiedObject
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.acdc_terminal import ACDCTerminal
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.reporting_group import ReportingGroup

class BusNameMarker(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='priority', class_type=int, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Priority of bus name marker for use as topology bus name.  Use 0 for don t care.  Use 1 for highest priority.  Use 2 as priority is less than 1 and so on.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='ReportingGroup', class_type='ReportingGroup', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The bus name markers that belong to this reporting group.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='Terminal', class_type='ACDCTerminal', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The terminals associated with this bus name marker.''', profiles=[]),
	)
	__slots__ = ('priority', 'ReportingGroup', 'Terminal')
	def __init__(self, rdfid='', tpe='BusNameMarker'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.priority: int = None
		self.ReportingGroup: ReportingGroup | None = None
		self.Terminal: ACDCTerminal | None = None
