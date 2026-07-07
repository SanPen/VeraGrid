# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.identified_object import IdentifiedObject
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.control_area import ControlArea

class EnergyArea(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='ControlArea', class_type='ControlArea', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The control area specification that is used for the load forecast.''', profiles=[]),
	)
	__slots__ = ('ControlArea',)
	def __init__(self, rdfid='', tpe='EnergyArea'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.ControlArea: ControlArea | None = None
