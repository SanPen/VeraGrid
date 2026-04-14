# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.identified_object import IdentifiedObject
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.connectivity_node_container import ConnectivityNodeContainer
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.terminal import Terminal
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.topological_node import TopologicalNode

class ConnectivityNode(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='Terminals', class_type='Terminal', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The connectivity node to which this terminal connects with zero impedance.''', profiles=[]),
		CgmesProperty(property_name='ConnectivityNodeContainer', class_type='ConnectivityNodeContainer', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Container of this connectivity node.''', profiles=[]),
		CgmesProperty(property_name='TopologicalNode', class_type='TopologicalNode', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The connectivity nodes combine together to form this topological node.  May depend on the current state of switches in the network.''', profiles=[]),
	)
	__slots__ = ('Terminals', 'ConnectivityNodeContainer', 'TopologicalNode')
	def __init__(self, rdfid='', tpe: str = 'ConnectivityNode') -> None:
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.Terminals: Terminal | None = None
		self.ConnectivityNodeContainer: ConnectivityNodeContainer | None = None
		self.TopologicalNode: TopologicalNode | None = None
