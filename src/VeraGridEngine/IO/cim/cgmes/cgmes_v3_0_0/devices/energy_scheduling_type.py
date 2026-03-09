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
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.energy_source import EnergySource

class EnergySchedulingType(IdentifiedObject):
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='EnergySource', class_type='EnergySource', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Energy Source of a particular Energy Scheduling Type.''', profiles=[]),
    )
    def __init__(self, rdfid='', tpe='EnergySchedulingType'):
        IdentifiedObject.__init__(self, rdfid, tpe)

        self.EnergySource: EnergySource | None = None
