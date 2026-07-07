# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.equipment_container import EquipmentContainer
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.voltage_level import VoltageLevel

class Bay(EquipmentContainer):
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='VoltageLevel', class_type='VoltageLevel', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The voltage level containing this bay.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
    )
    __slots__ = ('VoltageLevel',)
    def __init__(self, rdfid='', tpe='Bay'):
        EquipmentContainer.__init__(self, rdfid, tpe)

        self.VoltageLevel: VoltageLevel | None = None
