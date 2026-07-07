# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.equivalent_equipment import EquivalentEquipment
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

class EquivalentShunt(EquivalentEquipment):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='b', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Imaginary part of admittance.''', profiles=[]),
		CgmesProperty(property_name='g', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Factor by which voltage must be multiplied to give corresponding power lost from a circuit. Real part of admittance.''', profiles=[]),
	)
	__slots__ = ('b', 'g')
	def __init__(self, rdfid='', tpe='EquivalentShunt'):
		EquivalentEquipment.__init__(self, rdfid, tpe)

		self.b: float = None
		self.g: float = None
