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
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.dc_line import DCLine
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.geographical_region import GeographicalRegion
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.line import Line
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.substation import Substation

class SubGeographicalRegion(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='DCLines', class_type='DCLine', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The DC lines in this sub-geographical region.''', profiles=[]),
		CgmesProperty(property_name='Region', class_type='GeographicalRegion', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The geographical region which this sub-geographical region is within.''', profiles=[]),
		CgmesProperty(property_name='Lines', class_type='Line', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The lines within the sub-geographical region.''', profiles=[]),
		CgmesProperty(property_name='Substations', class_type='Substation', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The substations in this sub-geographical region.''', profiles=[]),
	)
	__slots__ = ('DCLines', 'Region', 'Lines', 'Substations')
	def __init__(self, rdfid='', tpe='SubGeographicalRegion'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.DCLines: DCLine | None = None
		self.Region: GeographicalRegion | None = None
		self.Lines: Line | None = None
		self.Substations: Substation | None = None
