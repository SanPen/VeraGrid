# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.base import Base
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol, CgmesProfileType
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.nonlinear_shunt_compensator import NonlinearShuntCompensator

class NonlinearShuntCompensatorPoint(Base):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='NonlinearShuntCompensator', class_type='NonlinearShuntCompensator', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Non-linear shunt compensator owning this point.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='b', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Imaginary part of admittance.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='g', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Factor by which voltage must be multiplied to give corresponding power lost from a circuit. Real part of admittance.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='sectionNumber', class_type=int, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The number of the section.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='b0', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Imaginary part of admittance.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='g0', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Factor by which voltage must be multiplied to give corresponding power lost from a circuit. Real part of admittance.''', mandatory=True, profiles=[CgmesProfileType.SC]),
	)
	__slots__ = ('NonlinearShuntCompensator', 'b', 'g', 'sectionNumber', 'b0', 'g0')
	def __init__(self, rdfid, tpe='NonlinearShuntCompensatorPoint', resources=list(), class_replacements=dict()):
		Base.__init__(self, rdfid=rdfid, tpe=tpe, resources=resources, class_replacements=class_replacements)

		self.NonlinearShuntCompensator: NonlinearShuntCompensator | None = None
		self.b: float = None
		self.g: float = None
		self.sectionNumber: int = None
		self.b0: float = None
		self.g0: float = None
