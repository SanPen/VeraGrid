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
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.base_irregular_time_series import BaseIrregularTimeSeries

if TYPE_CHECKING:
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_bid_dependency import PowerBidDependency
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_bid_schedule_time_point import PowerBidScheduleTimePoint
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.power_remedial_action import PowerRemedialAction
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.power_schedule_action import PowerScheduleAction
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_shift_key_distribution import PowerShiftKeyDistribution

class PowerBidSchedule(BaseIrregularTimeSeries):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='DependeePowerBidDependency', class_type='PowerBidDependency', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='DependentPowerBidDependency', class_type='PowerBidDependency', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='PowerBidScheduleTimePoint', class_type='PowerBidScheduleTimePoint', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='PowerRemedialAction', class_type='PowerRemedialAction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='PowerSchedulelAction', class_type='PowerScheduleAction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='PowerShiftKeyDistribution', class_type='PowerShiftKeyDistribution', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='ScheduleResource', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='activationCost', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='currency', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='direction', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='isFixed', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='isOffer', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='leadTime', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='maxRampDownP', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='maxRampUpP', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='maximumUptime', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='minimumOffTime', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='minimumUptime', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='priority', class_type=int, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='shutdownCost', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='totalMaximumEnergy', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='totalMinimumEnergy', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
    )
    __slots__ = ('DependeePowerBidDependency', 'DependentPowerBidDependency', 'PowerBidScheduleTimePoint', 'PowerRemedialAction', 'PowerSchedulelAction', 'PowerShiftKeyDistribution', 'ScheduleResource', 'activationCost', 'currency', 'direction', 'isFixed', 'isOffer', 'leadTime', 'maxRampDownP', 'maxRampUpP', 'maximumUptime', 'minimumOffTime', 'minimumUptime', 'priority', 'shutdownCost', 'totalMaximumEnergy', 'totalMinimumEnergy')

    def __init__(self, rdfid: str = '', tpe: str = 'PowerBidSchedule'):
        BaseIrregularTimeSeries.__init__(self, rdfid, tpe)

        self.DependeePowerBidDependency: PowerBidDependency | None = None
        self.DependentPowerBidDependency: PowerBidDependency | None = None
        self.PowerBidScheduleTimePoint: PowerBidScheduleTimePoint | None = None
        self.PowerRemedialAction: PowerRemedialAction | None = None
        self.PowerSchedulelAction: PowerScheduleAction | None = None
        self.PowerShiftKeyDistribution: PowerShiftKeyDistribution | None = None
        self.ScheduleResource: str | None = None
        self.activationCost: float | None = None
        self.currency: str | None = None
        self.direction: str | None = None
        self.isFixed: bool | None = None
        self.isOffer: bool | None = None
        self.leadTime: float | None = None
        self.maxRampDownP: float | None = None
        self.maxRampUpP: float | None = None
        self.maximumUptime: float | None = None
        self.minimumOffTime: float | None = None
        self.minimumUptime: float | None = None
        self.priority: int | None = None
        self.shutdownCost: float | None = None
        self.totalMaximumEnergy: str | None = None
        self.totalMinimumEnergy: str | None = None

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
