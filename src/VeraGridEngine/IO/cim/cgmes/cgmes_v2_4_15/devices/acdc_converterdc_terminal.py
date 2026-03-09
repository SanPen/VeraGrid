# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.dc_base_terminal import DCBaseTerminal
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import DCPolarityKind
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.acdc_converter import ACDCConverter

class ACDCConverterDCTerminal(DCBaseTerminal):
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='DCConductingEquipment', class_type='ACDCConverter', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''None''', profiles=[]),
        CgmesProperty(property_name='polarity', class_type=DCPolarityKind, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Represents the normal network polarity condition.''', profiles=[]),
    )
    def __init__(self, rdfid='', tpe='ACDCConverterDCTerminal'):
        DCBaseTerminal.__init__(self, rdfid, tpe)

        self.DCConductingEquipment: ACDCConverter | None = None
        self.polarity: DCPolarityKind | None = None
