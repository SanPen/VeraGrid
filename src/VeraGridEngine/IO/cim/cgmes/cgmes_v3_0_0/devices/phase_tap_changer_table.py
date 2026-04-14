# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.identified_object import IdentifiedObject
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.phase_tap_changer_table_point import PhaseTapChangerTablePoint
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.phase_tap_changer_tabular import PhaseTapChangerTabular

class PhaseTapChangerTable(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='PhaseTapChangerTablePoint', class_type='PhaseTapChangerTablePoint', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The points of this table.''', profiles=[]),
		CgmesProperty(property_name='PhaseTapChangerTabular', class_type='PhaseTapChangerTabular', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The phase tap changers to which this phase tap table applies.''', profiles=[]),
	)
	__slots__ = ('PhaseTapChangerTablePoint', 'PhaseTapChangerTabular')
	def __init__(self, rdfid='', tpe='PhaseTapChangerTable'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.PhaseTapChangerTablePoint: PhaseTapChangerTablePoint | None = None
		self.PhaseTapChangerTabular: PhaseTapChangerTabular | None = None
