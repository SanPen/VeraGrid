# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.energy_area import EnergyArea
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.load_area import LoadArea
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.load_group import LoadGroup

class SubLoadArea(EnergyArea):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='LoadArea', class_type='LoadArea', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The LoadArea where the SubLoadArea belongs.''', profiles=[]),
		CgmesProperty(property_name='LoadGroups', class_type='LoadGroup', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The Loadgroups in the SubLoadArea.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='SubLoadArea'):
		EnergyArea.__init__(self, rdfid, tpe)

		self.LoadArea: LoadArea | None = None
		self.LoadGroups: LoadGroup | None = None
