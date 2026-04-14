# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.regulating_control import RegulatingControl
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.tap_changer import TapChanger

class TapChangerControl(RegulatingControl):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='TapChanger', class_type='TapChanger', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The regulating control scheme in which this tap changer participates.''', profiles=[]),
	)
	__slots__ = ('TapChanger',)
	def __init__(self, rdfid='', tpe='TapChangerControl'):
		RegulatingControl.__init__(self, rdfid, tpe)

		self.TapChanger: TapChanger | None = None
