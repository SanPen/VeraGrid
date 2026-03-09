# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.power_system_resource import PowerSystemResource
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.connectivity_node import ConnectivityNode
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.topological_node import TopologicalNode

class ConnectivityNodeContainer(PowerSystemResource):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='ConnectivityNodes', class_type='ConnectivityNode', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Connectivity nodes which belong to this connectivity node container.''', profiles=[]),
		CgmesProperty(property_name='TopologicalNode', class_type='TopologicalNode', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The topological nodes which belong to this connectivity node container.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='ConnectivityNodeContainer'):
		PowerSystemResource.__init__(self, rdfid, tpe)

		self.ConnectivityNodes: ConnectivityNode | None = None
		self.TopologicalNode: TopologicalNode | None = None
