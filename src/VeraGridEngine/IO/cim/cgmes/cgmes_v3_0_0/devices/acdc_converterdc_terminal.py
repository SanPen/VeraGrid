# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.dc_base_terminal import DCBaseTerminal
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import DCPolarityKind
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.acdc_converter import ACDCConverter

class ACDCConverterDCTerminal(DCBaseTerminal):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='DCConductingEquipment', class_type='ACDCConverter', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A DC converter terminal belong to an DC converter.''', profiles=[]),
		CgmesProperty(property_name='polarity', class_type=DCPolarityKind, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Represents the normal network polarity condition. Depending on the converter configuration the value shall be set as follows:
- For a monopole with two converter terminals use DCPolarityKind �positive� and �negative�.
- For a bi-pole or symmetric monopole with three converter terminals use DCPolarityKind �positive�, �middle� and �negative�.''', profiles=[]),
	)
	__slots__ = ('DCConductingEquipment', 'polarity')
	def __init__(self, rdfid='', tpe='ACDCConverterDCTerminal'):
		DCBaseTerminal.__init__(self, rdfid, tpe)

		self.DCConductingEquipment: ACDCConverter | None = None
		self.polarity: DCPolarityKind = None
