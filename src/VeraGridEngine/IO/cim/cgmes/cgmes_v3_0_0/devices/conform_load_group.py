# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.load_group import LoadGroup
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.conform_load import ConformLoad

class ConformLoadGroup(LoadGroup):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='EnergyConsumers', class_type='ConformLoad', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Conform loads assigned to this ConformLoadGroup.''', profiles=[]),
	)
	__slots__ = ('EnergyConsumers',)
	def __init__(self, rdfid='', tpe='ConformLoadGroup'):
		LoadGroup.__init__(self, rdfid, tpe)

		self.EnergyConsumers: ConformLoad | None = None
