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
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.dc_base_terminal import DCBaseTerminal
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.dc_equipment_container import DCEquipmentContainer
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.dc_node import DCNode
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.dc_topological_island import DCTopologicalIsland

class DCTopologicalNode(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='DCTopologicalIsland', class_type='DCTopologicalIsland', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''None''', profiles=[]),
		CgmesProperty(property_name='DCTerminals', class_type='DCBaseTerminal', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''See association end Terminal.TopologicalNode.''', profiles=[]),
		CgmesProperty(property_name='DCEquipmentContainer', class_type='DCEquipmentContainer', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''None''', profiles=[CgmesProfileType.TP]),
		CgmesProperty(property_name='DCNodes', class_type='DCNode', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''See association end ConnectivityNode.TopologicalNode.''', profiles=[]),
	)
	__slots__ = ('DCTopologicalIsland', 'DCTerminals', 'DCEquipmentContainer', 'DCNodes')
	def __init__(self, rdfid='', tpe='DCTopologicalNode'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.DCTopologicalIsland: DCTopologicalIsland | None = None
		self.DCTerminals: DCBaseTerminal | None = None
		self.DCEquipmentContainer: DCEquipmentContainer | None = None
		self.DCNodes: DCNode | None = None
