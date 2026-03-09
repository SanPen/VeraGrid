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
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.dc_base_terminal import DCBaseTerminal
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.dc_equipment_container import DCEquipmentContainer
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.dc_topological_node import DCTopologicalNode

class DCNode(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='DCTerminals', class_type='DCBaseTerminal', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''DC base terminals interconnected with zero impedance at a this DC connectivity node. ''', profiles=[]),
		CgmesProperty(property_name='DCEquipmentContainer', class_type='DCEquipmentContainer', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The DC container for the DC nodes.''', profiles=[]),
		CgmesProperty(property_name='DCTopologicalNode', class_type='DCTopologicalNode', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The DC topological node to which this DC connectivity node is assigned.  May depend on the current state of switches in the network.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='DCNode'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.DCTerminals: DCBaseTerminal | None = None

		self.DCEquipmentContainer: DCEquipmentContainer | None = None

		self.DCTopologicalNode: DCTopologicalNode | None = None
