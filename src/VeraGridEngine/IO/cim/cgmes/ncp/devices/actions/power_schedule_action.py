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

if TYPE_CHECKING:
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_bid_schedule import PowerBidSchedule
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_schedule import PowerSchedule
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_schedule import RemedialActionSchedule

class PowerScheduleAction(IdentifiedObject):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='PowerBidSchedule', class_type='PowerBidSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='PowerSchedule', class_type='PowerSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='RemedialActionSchedule', class_type='RemedialActionSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='currency', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='energyPrice', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
    )
    __slots__ = ('PowerBidSchedule', 'PowerSchedule', 'RemedialActionSchedule', 'currency', 'energyPrice')

    def __init__(self, rdfid: str = '', tpe: str = 'PowerScheduleAction'):
        IdentifiedObject.__init__(self, rdfid, tpe)

        self.PowerBidSchedule: PowerBidSchedule | None = None
        self.PowerSchedule: PowerSchedule | None = None
        self.RemedialActionSchedule: RemedialActionSchedule | None = None
        self.currency: str | None = None
        self.energyPrice: float | None = None

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
