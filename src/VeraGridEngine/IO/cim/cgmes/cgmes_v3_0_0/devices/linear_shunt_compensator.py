# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.shunt_compensator import ShuntCompensator
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

class LinearShuntCompensator(ShuntCompensator):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='bPerSection', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Imaginary part of admittance.''', profiles=[]),
		CgmesProperty(property_name='gPerSection', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Factor by which voltage must be multiplied to give corresponding power lost from a circuit. Real part of admittance.''', profiles=[]),
		CgmesProperty(property_name='b0PerSection', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Imaginary part of admittance.''', profiles=[]),
		CgmesProperty(property_name='g0PerSection', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Factor by which voltage must be multiplied to give corresponding power lost from a circuit. Real part of admittance.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='LinearShuntCompensator'):
		ShuntCompensator.__init__(self, rdfid, tpe)

		self.bPerSection: float = None
		self.gPerSection: float = None
		self.b0PerSection: float = None
		self.g0PerSection: float = None
