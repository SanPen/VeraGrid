# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.identified_object import IdentifiedObject
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.terminal import Terminal

class MutualCoupling(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='b0ch', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Imaginary part of admittance.''', profiles=[]),
		CgmesProperty(property_name='distance11', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.m, description='''Unit of length. It shall be a positive value or zero.''', profiles=[]),
		CgmesProperty(property_name='distance12', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.m, description='''Unit of length. It shall be a positive value or zero.''', profiles=[]),
		CgmesProperty(property_name='distance21', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.m, description='''Unit of length. It shall be a positive value or zero.''', profiles=[]),
		CgmesProperty(property_name='distance22', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.m, description='''Unit of length. It shall be a positive value or zero.''', profiles=[]),
		CgmesProperty(property_name='g0ch', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Factor by which voltage must be multiplied to give corresponding power lost from a circuit. Real part of admittance.''', profiles=[]),
		CgmesProperty(property_name='r0', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', profiles=[]),
		CgmesProperty(property_name='x0', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', profiles=[]),
		CgmesProperty(property_name='Second_Terminal', class_type='Terminal', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The starting terminal for the calculation of distances along the second branch of the mutual coupling.''', profiles=[]),
		CgmesProperty(property_name='First_Terminal', class_type='Terminal', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The starting terminal for the calculation of distances along the first branch of the mutual coupling.  Normally MutualCoupling would only be used for terminals of AC line segments.  The first and second terminals of a mutual coupling should point to different AC line segments.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='MutualCoupling'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.b0ch: float = None
		self.distance11: float = None
		self.distance12: float = None
		self.distance21: float = None
		self.distance22: float = None
		self.g0ch: float = None
		self.r0: float = None
		self.x0: float = None

		self.Second_Terminal: Terminal | None = None

		self.First_Terminal: Terminal | None = None
