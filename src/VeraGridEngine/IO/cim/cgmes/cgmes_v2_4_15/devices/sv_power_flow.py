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
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.terminal import Terminal

class SvPowerFlow(Base):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='Terminal', class_type='Terminal', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The terminal associated with the power flow state variable.''', profiles=[]),
		CgmesProperty(property_name='p', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Product of RMS value of the voltage and the RMS value of the in-phase component of the current.''', profiles=[]),
		CgmesProperty(property_name='q', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VAr, description='''Product of RMS value of the voltage and the RMS value of the quadrature component of the current.''', profiles=[]),
	)
	def __init__(self, rdfid, tpe='SvPowerFlow', resources=list(), class_replacements=dict()):
		Base.__init__(self, rdfid=rdfid, tpe=tpe, resources=resources, class_replacements=class_replacements)

		self.Terminal: Terminal | None = None
		self.p: float = None
		self.q: float = None
