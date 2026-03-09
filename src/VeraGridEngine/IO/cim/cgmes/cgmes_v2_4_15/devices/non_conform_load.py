# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.energy_consumer import EnergyConsumer
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.non_conform_load_group import NonConformLoadGroup

class NonConformLoad(EnergyConsumer):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='LoadGroup', class_type='NonConformLoadGroup', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Conform loads assigned to this ConformLoadGroup.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='NonConformLoad'):
		EnergyConsumer.__init__(self, rdfid, tpe)

		self.LoadGroup: NonConformLoadGroup | None = None
