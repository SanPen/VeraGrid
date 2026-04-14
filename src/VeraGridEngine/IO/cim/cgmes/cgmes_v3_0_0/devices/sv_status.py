# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.base import Base
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.conducting_equipment import ConductingEquipment

class SvStatus(Base):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='ConductingEquipment', class_type='ConductingEquipment', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The conducting equipment associated with the status state variable.''', profiles=[]),
		CgmesProperty(property_name='inService', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The in service status as a result of topology processing.  It indicates if the equipment is considered as energized by the power flow. It reflects if the equipment is connected within a solvable island.  It does not necessarily reflect whether or not the island was solved by the power flow.''', profiles=[]),
	)
	__slots__ = ('ConductingEquipment', 'inService')
	def __init__(self, rdfid, tpe="SvStatus", resources=list(), class_replacements=dict()):
		Base.__init__(self, rdfid=rdfid, tpe=tpe, resources=resources, class_replacements=class_replacements)

		self.ConductingEquipment: ConductingEquipment | None = None
		self.inService: bool = None
