# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.identified_object import IdentifiedObject
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType

# if TYPE_CHECKING:
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.sv_injection import SvInjection
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.sv_voltage import SvVoltage
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.topological_island import TopologicalIsland
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.topological_island import TopologicalIsland
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.base_voltage import BaseVoltage
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.connectivity_node import ConnectivityNode
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.connectivity_node_container import ConnectivityNodeContainer
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.reporting_group import ReportingGroup
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.terminal import Terminal


class TopologicalNode(IdentifiedObject):
	def __init__(self, rdfid='', tpe='TopologicalNode'):
		"""

		:param rdfid:
		:param tpe:
		"""
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.SvInjection: SvInjection | None = None
		self.SvVoltage: SvVoltage | None = None
		self.AngleRefTopologicalIsland: TopologicalIsland | None = None
		self.TopologicalIsland: TopologicalIsland | None = None
		self._BaseVoltage: BaseVoltage | None = None
		self.ConnectivityNodes: ConnectivityNode | None = None
		self.ConnectivityNodeContainer: ConnectivityNodeContainer | None = None
		self.ReportingGroup: ReportingGroup | None = None
		self.Terminal: Terminal | None = None

		self.register_property(
			name='SvInjection',
			class_type=SvInjection,
			multiplier=UnitMultiplier.none,
			unit=UnitSymbol.none,
			description='''The topological node associated with the flow injection state variable.''',
			profiles=[]
		)
		self.register_property(
			name='SvVoltage',
			class_type=SvVoltage,
			multiplier=UnitMultiplier.none,
			unit=UnitSymbol.none,
			description='''The topological node associated with the voltage state.''',
			profiles=[]
		)
		self.register_property(
			name='AngleRefTopologicalIsland',
			class_type=TopologicalIsland,
			multiplier=UnitMultiplier.none,
			unit=UnitSymbol.none,
			description='''The island for which the node is an angle reference.   Normally there is one angle reference node for each island.''',
			profiles=[]
		)
		self.register_property(
			name='TopologicalIsland',
			class_type=TopologicalIsland,
			multiplier=UnitMultiplier.none,
			unit=UnitSymbol.none,
			description='''A topological node belongs to a topological island.''',
			profiles=[]
		)
		self.register_property(
			name='BaseVoltage',
			class_type=BaseVoltage,
			multiplier=UnitMultiplier.none,
			unit=UnitSymbol.none,
			description='''The base voltage of the topologocial node.''',
			profiles=[]
		)
		self.register_property(
			name='ConnectivityNodes',
			class_type=ConnectivityNode,
			multiplier=UnitMultiplier.none,
			unit=UnitSymbol.none,
			description='''The topological node to which this connectivity node is assigned.  May depend on the current state of switches in the network.''',
			profiles=[]
		)
		self.register_property(
			name='ConnectivityNodeContainer',
			class_type=ConnectivityNodeContainer,
			multiplier=UnitMultiplier.none,
			unit=UnitSymbol.none,
			description='''The connectivity node container to which the toplogical node belongs.''',
			profiles=[]
		)
		self.register_property(
			name='ReportingGroup',
			class_type=ReportingGroup,
			multiplier=UnitMultiplier.none,
			unit=UnitSymbol.none,
			description='''The topological nodes that belong to the reporting group.''',
			profiles=[]
		)
		self.register_property(
			name='Terminal',
			class_type=Terminal,
			multiplier=UnitMultiplier.none,
			unit=UnitSymbol.none,
			description='''The topological node associated with the terminal.   This can be used as an alternative to the connectivity node path to topological node, thus making it unneccesary to model connectivity nodes in some cases.   Note that the if connectivity nodes are in the model, this association would probably not be used as an input specification.''',
			profiles=[]
		)

	@property
	def BaseVoltage(self):
		"""

		:return:
		"""
		return self._BaseVoltage

	@BaseVoltage.setter
	def BaseVoltage(self, val: BaseVoltage):
		# if isinstance(val, str):
		# 	raise ValueError("BaseVoltage Cannot be a string")
		self._BaseVoltage = val
