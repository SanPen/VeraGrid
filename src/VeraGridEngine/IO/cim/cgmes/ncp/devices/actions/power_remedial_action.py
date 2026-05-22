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
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.bidding_zone import BiddingZone
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.bidding_zone_border import BiddingZoneBorder
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_bid_schedule import PowerBidSchedule
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_schedule import PowerSchedule
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_shift_key_strategy import PowerShiftKeyStrategy

class PowerRemedialAction(RemedialAction):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='BiddingZone', class_type='BiddingZone', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RA]),
        CgmesProperty(property_name='BiddingZoneBorder', class_type='BiddingZoneBorder', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RA]),
        CgmesProperty(property_name='PowerBidSchedule', class_type='PowerBidSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='PowerRemedialActionSchedule', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='PowerSchedule', class_type='PowerSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS]),
        CgmesProperty(property_name='PowerShiftKeyStrategy', class_type='PowerShiftKeyStrategy', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RA]),
        CgmesProperty(property_name='maxRegulatingDown', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SSI]),
        CgmesProperty(property_name='maxRegulatingUp', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SSI]),
    )
    __slots__ = ('BiddingZone', 'BiddingZoneBorder', 'PowerBidSchedule', 'PowerRemedialActionSchedule', 'PowerSchedule', 'PowerShiftKeyStrategy', 'maxRegulatingDown', 'maxRegulatingUp')

    def __init__(self, rdfid: str = '', tpe: str = 'PowerRemedialAction'):
        RemedialAction.__init__(self, rdfid, tpe)

        self.BiddingZone: BiddingZone | None = None
        self.BiddingZoneBorder: BiddingZoneBorder | None = None
        self.PowerBidSchedule: PowerBidSchedule | None = None
        self.PowerRemedialActionSchedule: str | None = None
        self.PowerSchedule: PowerSchedule | None = None
        self.PowerShiftKeyStrategy: PowerShiftKeyStrategy | None = None
        self.maxRegulatingDown: float | None = None
        self.maxRegulatingUp: float | None = None

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
