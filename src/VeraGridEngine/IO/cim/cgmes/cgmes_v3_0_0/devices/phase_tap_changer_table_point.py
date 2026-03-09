# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.base import Base
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.phase_tap_changer_table import PhaseTapChangerTable

class PhaseTapChangerTablePoint(Base):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='PhaseTapChangerTable', class_type='PhaseTapChangerTable', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The table of this point.''', profiles=[]),
		CgmesProperty(property_name='angle', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.deg, description='''Measurement of angle in degrees.''', profiles=[]),
	)
	def __init__(self, rdfid, tpe, resources=list(), class_replacements=dict()):
		Base.__init__(self, rdfid=rdfid, tpe=tpe, resources=resources, class_replacements=class_replacements)

		self.PhaseTapChangerTable: PhaseTapChangerTable | None = None
		self.angle: float = None
