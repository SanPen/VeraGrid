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
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.dc_topological_node import DCTopologicalNode

class DCTopologicalIsland(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='DCTopologicalNodes', class_type='DCTopologicalNode', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''None''', mandatory=True, profiles=[CgmesProfileType.SV]),
	)
	__slots__ = ('DCTopologicalNodes',)
	def __init__(self, rdfid='', tpe='DCTopologicalIsland'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.DCTopologicalNodes: DCTopologicalNode | None = None
