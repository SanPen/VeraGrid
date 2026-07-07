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
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.identified_object import IdentifiedObject

class BaseTimeSeries(IdentifiedObject):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='actionMethod', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='generatedAtTime', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS, CgmesProfileType.SHS]),
        CgmesProperty(property_name='interpolationKind', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.AVS, CgmesProfileType.PS, CgmesProfileType.RAS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='kind', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.AVS]),
        CgmesProperty(property_name='percentile', class_type=int, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS, CgmesProfileType.SHS]),
        CgmesProperty(property_name='timeSeriesKind', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.PS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
    )
    __slots__ = ('actionMethod', 'generatedAtTime', 'interpolationKind', 'kind', 'percentile', 'timeSeriesKind')

    def __init__(self, rdfid: str = '', tpe: str = 'BaseTimeSeries'):
        IdentifiedObject.__init__(self, rdfid, tpe)

        self.actionMethod: str | None = None
        self.generatedAtTime: str | None = None
        self.interpolationKind: str | None = None
        self.kind: str | None = None
        self.percentile: int | None = None
        self.timeSeriesKind: str | None = None

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
