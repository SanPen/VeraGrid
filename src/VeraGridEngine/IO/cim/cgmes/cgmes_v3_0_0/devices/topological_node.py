# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.identified_object import IdentifiedObject
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.base_voltage import BaseVoltage
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.connectivity_node import ConnectivityNode
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.connectivity_node_container import ConnectivityNodeContainer
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.reporting_group import ReportingGroup
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.sv_injection import SvInjection
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.sv_voltage import SvVoltage
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.terminal import Terminal
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.topological_island import TopologicalIsland

class TopologicalNode(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='SvInjection', class_type='SvInjection', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The injection flows state variables associated with the topological node.''', profiles=[CgmesProfileType.SV]),
		CgmesProperty(property_name='SvVoltage', class_type='SvVoltage', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The state voltage associated with the topological node.''', profiles=[CgmesProfileType.SV]),
		CgmesProperty(property_name='AngleRefTopologicalIsland', class_type='TopologicalIsland', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The island for which the node is an angle reference.   Normally there is one angle reference node for each island.''', profiles=[CgmesProfileType.SV]),
		CgmesProperty(property_name='TopologicalIsland', class_type='TopologicalIsland', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A topological node belongs to a topological island.''', profiles=[CgmesProfileType.SV]),
		CgmesProperty(property_name='BaseVoltage', class_type='BaseVoltage', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The base voltage of the topological node.''', mandatory=True, profiles=[CgmesProfileType.TP]),
		CgmesProperty(property_name='ConnectivityNodes', class_type='ConnectivityNode', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The connectivity nodes combine together to form this topological node.  May depend on the current state of switches in the network.''', profiles=[CgmesProfileType.TP]),
		CgmesProperty(property_name='ConnectivityNodeContainer', class_type='ConnectivityNodeContainer', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The connectivity node container to which the topological node belongs.''', mandatory=True, profiles=[CgmesProfileType.TP]),
		CgmesProperty(property_name='Terminal', class_type='Terminal', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The terminals associated with the topological node.   This can be used as an alternative to the connectivity node path to terminal, thus making it unnecessary to model connectivity nodes in some cases.   Note that if connectivity nodes are in the model, this association would probably not be used as an input specification.''', mandatory=True, profiles=[CgmesProfileType.TP]),
		CgmesProperty(property_name='ReportingGroup', class_type='ReportingGroup', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The reporting group to which the topological node belongs.''', profiles=[CgmesProfileType.TP]),
	)
	__slots__ = ('SvInjection', 'SvVoltage', 'AngleRefTopologicalIsland', 'TopologicalIsland', 'BaseVoltage', 'ConnectivityNodes', 'ConnectivityNodeContainer', 'Terminal', 'ReportingGroup')
	def __init__(self, rdfid='', tpe='TopologicalNode'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.SvInjection: SvInjection | None = None
		self.SvVoltage: SvVoltage | None = None
		self.AngleRefTopologicalIsland: TopologicalIsland | None = None
		self.TopologicalIsland: TopologicalIsland | None = None
		self.BaseVoltage: BaseVoltage | None = None
		self.ConnectivityNodes: ConnectivityNode | None = None
		self.ConnectivityNodeContainer: ConnectivityNodeContainer | None = None
		self.Terminal: Terminal | None = None
		self.ReportingGroup: ReportingGroup | None = None
