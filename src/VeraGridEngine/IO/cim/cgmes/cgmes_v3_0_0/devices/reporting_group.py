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
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.bus_name_marker import BusNameMarker
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.topological_node import TopologicalNode

class ReportingGroup(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='BusNameMarker', class_type='BusNameMarker', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The bus name markers that belong to this reporting group.''', profiles=[]),
		CgmesProperty(property_name='TopologicalNode', class_type='TopologicalNode', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The topological nodes that belong to the reporting group.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='ReportingGroup'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.BusNameMarker: BusNameMarker | None = None
		self.TopologicalNode: TopologicalNode | None = None
