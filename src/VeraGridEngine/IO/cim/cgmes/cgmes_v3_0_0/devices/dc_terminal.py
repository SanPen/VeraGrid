# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.dc_base_terminal import DCBaseTerminal
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.dc_conducting_equipment import DCConductingEquipment

class DCTerminal(DCBaseTerminal):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='DCConductingEquipment', class_type='DCConductingEquipment', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''An DC  terminal belong to a DC conducting equipment.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='DCTerminal'):
		DCBaseTerminal.__init__(self, rdfid, tpe)

		self.DCConductingEquipment: DCConductingEquipment | None = None
