# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.acdc_terminal import ACDCTerminal
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.dc_node import DCNode
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.dc_topological_node import DCTopologicalNode

class DCBaseTerminal(ACDCTerminal):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='DCNode', class_type='DCNode', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The DC connectivity node to which this DC base terminal connects with zero impedance.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='DCTopologicalNode', class_type='DCTopologicalNode', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''See association end Terminal.TopologicalNode.''', mandatory=True, profiles=[CgmesProfileType.TP]),
	)
	__slots__ = ('DCNode', 'DCTopologicalNode')
	def __init__(self, rdfid='', tpe='DCBaseTerminal'):
		ACDCTerminal.__init__(self, rdfid, tpe)

		self.DCNode: DCNode | None = None

		self.DCTopologicalNode: DCTopologicalNode | None = None
