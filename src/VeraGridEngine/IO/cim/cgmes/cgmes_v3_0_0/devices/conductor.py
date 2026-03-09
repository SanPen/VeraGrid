# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.conducting_equipment import ConductingEquipment
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

class Conductor(ConductingEquipment):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='length', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.m, description='''Unit of length. It shall be a positive value or zero.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='Conductor'):
		ConductingEquipment.__init__(self, rdfid, tpe)

		self.length: float = None
