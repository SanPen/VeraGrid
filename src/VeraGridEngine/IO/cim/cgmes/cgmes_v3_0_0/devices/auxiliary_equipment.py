# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.equipment import Equipment
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.terminal import Terminal

class AuxiliaryEquipment(Equipment):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='Terminal', class_type='Terminal', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The Terminal at the equipment where the AuxiliaryEquipment is attached.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='AuxiliaryEquipment'):
		Equipment.__init__(self, rdfid, tpe)

		self.Terminal: Terminal | None = None
