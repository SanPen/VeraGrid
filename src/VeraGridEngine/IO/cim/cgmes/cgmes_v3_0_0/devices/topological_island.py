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
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.topological_node import TopologicalNode

class TopologicalIsland(IdentifiedObject):
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='AngleRefTopologicalNode', class_type='TopologicalNode', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The angle reference for the island.   Normally there is one TopologicalNode that is selected as the angle reference for each island.   Other reference schemes exist, so the association is typically optional.''', mandatory=True, profiles=[CgmesProfileType.SV]),
        CgmesProperty(property_name='TopologicalNodes', class_type='TopologicalNode', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A topological node belongs to a topological island.''', mandatory=True, profiles=[CgmesProfileType.SV]),
    )
    __slots__ = ('AngleRefTopologicalNode', 'TopologicalNodes')
    def __init__(self, rdfid='', tpe='TopologicalIsland'):
        IdentifiedObject.__init__(self, rdfid, tpe)

        self.AngleRefTopologicalNode: TopologicalNode | None = None
        self.TopologicalNodes: TopologicalNode | None = None
