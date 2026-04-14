# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.identified_object import IdentifiedObject
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.sub_load_area import SubLoadArea

class LoadGroup(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='SubLoadArea', class_type='SubLoadArea', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The SubLoadArea where the Loadgroup belongs.''', profiles=[]),
	)
	__slots__ = ('SubLoadArea',)
	def __init__(self, rdfid='', tpe='LoadGroup'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.SubLoadArea: SubLoadArea | None = None
