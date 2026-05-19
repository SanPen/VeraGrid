# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Dict, TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
from VeraGridEngine.data_logger import DataLogger
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action import RemedialAction

if TYPE_CHECKING:
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_scheme import RemedialActionScheme

class SchemeRemedialAction(RemedialAction):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='RemedialActionScheme', class_type='RemedialActionScheme', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='RemedialActionSchemeSchedule', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
    )
    __slots__ = ('RemedialActionScheme', 'RemedialActionSchemeSchedule')

    def __init__(self, rdfid: str = '', tpe: str = 'SchemeRemedialAction'):
        RemedialAction.__init__(self, rdfid, tpe)

        self.RemedialActionScheme: RemedialActionScheme | None = None
        self.RemedialActionSchemeSchedule: str | None = None

    def parse_dict(self, data: Dict[str, str], logger: DataLogger) -> None:
        """Parse one NCP object property dictionary."""
        self.parsed_properties = data
        declared_properties: Dict[str, CgmesProperty] = self.declared_properties
        for prop_name, prop_value in data.items():
            declared_property: CgmesProperty | None = declared_properties.get(prop_name, None)
            if declared_property is not None:
                try:
                    self.store_parsed_property_value(prop_name=prop_name, prop_value=prop_value)
                except AttributeError:
                    pass
            else:
                pass
