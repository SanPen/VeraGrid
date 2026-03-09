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
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.boundary_point import BoundaryPoint
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.connectivity_node_container import ConnectivityNodeContainer
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.terminal import Terminal
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.topological_node import TopologicalNode

class ConnectivityNode(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='BoundaryPoint', class_type='BoundaryPoint', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The boundary point associated with the connectivity node.''', profiles=[]),
		CgmesProperty(property_name='Terminals', class_type='Terminal', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Terminals interconnected with zero impedance at a this connectivity node. ''', profiles=[]),
		CgmesProperty(property_name='ConnectivityNodeContainer', class_type='ConnectivityNodeContainer', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Container of this connectivity node.''', profiles=[]),
		CgmesProperty(property_name='TopologicalNode', class_type='TopologicalNode', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The topological node to which this connectivity node is assigned.  May depend on the current state of switches in the network.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='ConnectivityNode'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.BoundaryPoint: BoundaryPoint | None = None

		self.Terminals: Terminal | None = None

		self.ConnectivityNodeContainer: ConnectivityNodeContainer | None = None

		self.TopologicalNode: TopologicalNode | None = None
