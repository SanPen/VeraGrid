# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.equipment_container import EquipmentContainer
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.base_voltage import BaseVoltage
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.bay import Bay
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.substation import Substation

class VoltageLevel(EquipmentContainer):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='BaseVoltage', class_type='BaseVoltage', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The base voltage used for all equipment within the voltage level.''', profiles=[]),
		CgmesProperty(property_name='Bays', class_type='Bay', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The bays within this voltage level.''', profiles=[]),
		CgmesProperty(property_name='Substation', class_type='Substation', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The substation of the voltage level.''', profiles=[]),
		CgmesProperty(property_name='highVoltageLimit', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.V, description='''Electrical voltage, can be both AC and DC.''', profiles=[]),
		CgmesProperty(property_name='lowVoltageLimit', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.V, description='''Electrical voltage, can be both AC and DC.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='VoltageLevel'):
		EquipmentContainer.__init__(self, rdfid, tpe)

		self.BaseVoltage: BaseVoltage | None = None
		self.Bays: Bay | None = None
		self.Substation: Substation | None = None
		self.highVoltageLimit: float = None
		self.lowVoltageLimit: float = None
