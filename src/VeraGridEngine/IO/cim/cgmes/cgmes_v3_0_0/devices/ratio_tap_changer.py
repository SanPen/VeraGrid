# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.tap_changer import TapChanger
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol, CgmesProfileType
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.ratio_tap_changer_table import RatioTapChangerTable
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.transformer_end import TransformerEnd

class RatioTapChanger(TapChanger):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='stepVoltageIncrement', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Percentage on a defined base.   For example, specify as 100 to indicate at the defined base.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='RatioTapChangerTable', class_type='RatioTapChangerTable', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The tap ratio table for this ratio  tap changer.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='TransformerEnd', class_type='TransformerEnd', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Transformer end to which this ratio tap changer belongs.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
	)
	__slots__ = ('stepVoltageIncrement', 'RatioTapChangerTable', 'TransformerEnd')
	def __init__(self, rdfid='', tpe='RatioTapChanger'):
		TapChanger.__init__(self, rdfid, tpe)

		self.stepVoltageIncrement: float = None
		self.RatioTapChangerTable: RatioTapChangerTable | None = None
		self.TransformerEnd: TransformerEnd | None = None
