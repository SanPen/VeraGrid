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
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.bidding_zone import BiddingZone
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.capacity_calculation_region import CapacityCalculationRegion
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.cross_border_relevance import CrossBorderRelevance
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.power_remedial_action import PowerRemedialAction
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_schedule import PowerSchedule
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.tie_corridor import TieCorridor

class BiddingZoneBorder(PowerSystemResource):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='AreaInterchangeController', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='CapacityCalculationRegion', class_type='CapacityCalculationRegion', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='CrossBorderRelevance', class_type='CrossBorderRelevance', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.AE]),
        CgmesProperty(property_name='FromBiddingZone', class_type='BiddingZone', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='PowerRemedialAction', class_type='PowerRemedialAction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RA]),
        CgmesProperty(property_name='PowerSchedule', class_type='PowerSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS]),
        CgmesProperty(property_name='TieCorridor', class_type='TieCorridor', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='ToBiddingZone', class_type='BiddingZone', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='alreadyAllocatedCapacity', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SSI]),
        CgmesProperty(property_name='alreadyAllocatedFlow', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SSI]),
        CgmesProperty(property_name='availableTransferCapacity', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SSI]),
        CgmesProperty(property_name='netTransferCapacity', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SSI]),
        CgmesProperty(property_name='totalTransferCapacity', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SSI]),
        CgmesProperty(property_name='transmissionReliabilityMargin', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SSI]),
    )
    __slots__ = ('AreaInterchangeController', 'CapacityCalculationRegion', 'CrossBorderRelevance', 'FromBiddingZone', 'PowerRemedialAction', 'PowerSchedule', 'TieCorridor', 'ToBiddingZone', 'alreadyAllocatedCapacity', 'alreadyAllocatedFlow', 'availableTransferCapacity', 'netTransferCapacity', 'totalTransferCapacity', 'transmissionReliabilityMargin')

    def __init__(self, rdfid: str = '', tpe: str = 'BiddingZoneBorder'):
        PowerSystemResource.__init__(self, rdfid, tpe)

        self.AreaInterchangeController: str | None = None
        self.CapacityCalculationRegion: CapacityCalculationRegion | None = None
        self.CrossBorderRelevance: CrossBorderRelevance | None = None
        self.FromBiddingZone: BiddingZone | None = None
        self.PowerRemedialAction: PowerRemedialAction | None = None
        self.PowerSchedule: PowerSchedule | None = None
        self.TieCorridor: TieCorridor | None = None
        self.ToBiddingZone: BiddingZone | None = None
        self.alreadyAllocatedCapacity: float | None = None
        self.alreadyAllocatedFlow: float | None = None
        self.availableTransferCapacity: float | None = None
        self.netTransferCapacity: float | None = None
        self.totalTransferCapacity: float | None = None
        self.transmissionReliabilityMargin: float | None = None

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
