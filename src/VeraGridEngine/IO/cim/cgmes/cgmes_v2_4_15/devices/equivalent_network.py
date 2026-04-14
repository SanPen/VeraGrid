# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.connectivity_node_container import ConnectivityNodeContainer
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.equivalent_equipment import EquivalentEquipment

class EquivalentNetwork(ConnectivityNodeContainer):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='EquivalentEquipments', class_type='EquivalentEquipment', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The equivalent where the reduced model belongs.''', profiles=[]),
	)
	__slots__ = ('EquivalentEquipments',)
	def __init__(self, rdfid='', tpe='EquivalentNetwork'):
		ConnectivityNodeContainer.__init__(self, rdfid, tpe)

		self.EquivalentEquipments: EquivalentEquipment | None = None
