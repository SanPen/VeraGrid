# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.conducting_equipment import ConductingEquipment
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.regulating_control import RegulatingControl

class RegulatingCondEq(ConductingEquipment):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='RegulatingControl', class_type='RegulatingControl', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The regulating control scheme in which this equipment participates.''', profiles=[]),
		CgmesProperty(property_name='controlEnabled', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Specifies the regulation status of the equipment.  True is regulating, false is not regulating.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='RegulatingCondEq'):
		ConductingEquipment.__init__(self, rdfid, tpe)

		self.RegulatingControl: RegulatingControl | None = None
		self.controlEnabled: bool = None
