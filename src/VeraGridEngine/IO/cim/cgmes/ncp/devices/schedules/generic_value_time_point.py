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
from VeraGridEngine.IO.cim.cgmes.base import Base

if TYPE_CHECKING:
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.generic_value_schedule import GenericValueSchedule

class GenericValueTimePoint(Base):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='GenericValueSchedule', class_type='GenericValueSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.RAS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='atTime', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.RAS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='value', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.RAS, CgmesProfileType.SIS]),
    )
    __slots__ = ('GenericValueSchedule', 'atTime', 'value')

    def __init__(self, rdfid: str = '', tpe: str = 'GenericValueTimePoint'):
        Base.__init__(self, rdfid, tpe)

        self.GenericValueSchedule: GenericValueSchedule | None = None
        self.atTime: str | None = None
        self.value: float | None = None

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
