# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.equipment_container import EquipmentContainer
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.dc_converter_unit import DCConverterUnit
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.sub_geographical_region import SubGeographicalRegion
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.voltage_level import VoltageLevel

class Substation(EquipmentContainer):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='DCConverterUnit', class_type='DCConverterUnit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The DC converter unit belonging of the substation.''', profiles=[]),
		CgmesProperty(property_name='Region', class_type='SubGeographicalRegion', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The SubGeographicalRegion containing the substation.''', profiles=[]),
		CgmesProperty(property_name='VoltageLevels', class_type='VoltageLevel', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The voltage levels within this substation.''', profiles=[]),
	)
	__slots__ = ('DCConverterUnit', 'Region', 'VoltageLevels')
	def __init__(self, rdfid='', tpe='Substation'):
		EquipmentContainer.__init__(self, rdfid, tpe)

		self.DCConverterUnit: DCConverterUnit | None = None
		self.Region: SubGeographicalRegion | None = None
		self.VoltageLevels: VoltageLevel | None = None
