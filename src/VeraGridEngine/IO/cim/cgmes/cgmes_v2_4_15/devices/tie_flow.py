# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.base import Base
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.control_area import ControlArea
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.terminal import Terminal

class TieFlow(Base):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='Terminal', class_type='Terminal', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The terminal to which this tie flow belongs.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='ControlArea', class_type='ControlArea', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The control area of the tie flows.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='positiveFlowIn', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''True if the flow into the terminal (load convention) is also flow into the control area.  For example, this attribute should be true if using the tie line terminal further away from the control area. For example to represent a tie to a shunt component (like a load or generator) in another area, this is the near end of a branch and this attribute would be specified as false.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
	)
	__slots__ = ('Terminal', 'ControlArea', 'positiveFlowIn')
	def __init__(self, rdfid, tpe, resources=list(), class_replacements=dict()):
		Base.__init__(self, rdfid=rdfid, tpe=tpe, resources=resources, class_replacements=class_replacements)

		self.Terminal: Terminal | None = None
		self.ControlArea: ControlArea | None = None
		self.positiveFlowIn: bool = None
