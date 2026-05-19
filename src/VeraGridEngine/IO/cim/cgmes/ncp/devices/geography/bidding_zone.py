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
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.power_system_resource import PowerSystemResource

if TYPE_CHECKING:
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.bidding_zone_border import BiddingZoneBorder
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.capacity_calculation_region import CapacityCalculationRegion
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.power_remedial_action import PowerRemedialAction
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_schedule import PowerSchedule
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.scheduling_area import SchedulingArea

class BiddingZone(PowerSystemResource):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='AreaInterchangeController', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA, CgmesProfileType.PSP]),
        CgmesProperty(property_name='BiddingZoneAction', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA, CgmesProfileType.PSP]),
        CgmesProperty(property_name='CapacityCalculationRegion', class_type='CapacityCalculationRegion', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA, CgmesProfileType.PSP]),
        CgmesProperty(property_name='FromBiddingZoneBorder', class_type='BiddingZoneBorder', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA, CgmesProfileType.PSP]),
        CgmesProperty(property_name='PowerCapacity', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA, CgmesProfileType.PSP]),
        CgmesProperty(property_name='PowerRemedialAction', class_type='PowerRemedialAction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA, CgmesProfileType.PSP]),
        CgmesProperty(property_name='PowerSchedule', class_type='PowerSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA, CgmesProfileType.PSP]),
        CgmesProperty(property_name='SchedulingArea', class_type='SchedulingArea', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA, CgmesProfileType.PSP]),
        CgmesProperty(property_name='ToBiddingZoneBorder', class_type='BiddingZoneBorder', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA, CgmesProfileType.PSP]),
        CgmesProperty(property_name='isTradeEnabled', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA, CgmesProfileType.PSP]),
        CgmesProperty(property_name='netPosition', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA, CgmesProfileType.PSP]),
    )
    __slots__ = ('AreaInterchangeController', 'BiddingZoneAction', 'CapacityCalculationRegion', 'FromBiddingZoneBorder', 'PowerCapacity', 'PowerRemedialAction', 'PowerSchedule', 'SchedulingArea', 'ToBiddingZoneBorder', 'isTradeEnabled', 'netPosition')

    def __init__(self, rdfid: str = '', tpe: str = 'BiddingZone'):
        PowerSystemResource.__init__(self, rdfid, tpe)

        self.AreaInterchangeController: str | None = None
        self.BiddingZoneAction: str | None = None
        self.CapacityCalculationRegion: CapacityCalculationRegion | None = None
        self.FromBiddingZoneBorder: BiddingZoneBorder | None = None
        self.PowerCapacity: str | None = None
        self.PowerRemedialAction: PowerRemedialAction | None = None
        self.PowerSchedule: PowerSchedule | None = None
        self.SchedulingArea: SchedulingArea | None = None
        self.ToBiddingZoneBorder: BiddingZoneBorder | None = None
        self.isTradeEnabled: bool | None = None
        self.netPosition: float | None = None

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
