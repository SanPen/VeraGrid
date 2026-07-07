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
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.shunt_compensator import ShuntCompensator

class SvShuntCompensatorSections(Base):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='sections', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A floating point number. The range is unspecified and not limited.''', profiles=[]),
		CgmesProperty(property_name='ShuntCompensator', class_type='ShuntCompensator', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The shunt compensator for which the state applies.''', profiles=[]),
	)
	__slots__ = ('sections', 'ShuntCompensator')
	def __init__(self, rdfid, tpe="SvShuntCompensatorSections", resources=list(), class_replacements=dict()):
		Base.__init__(self, rdfid=rdfid, tpe=tpe, resources=resources, class_replacements=class_replacements)

		self.sections: float = None
		self.ShuntCompensator: ShuntCompensator | None = None
