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
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.market.area_dispatchable_unit import AreaDispatchableUnit
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.bidding_zone import BiddingZone
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.control_area import ControlArea
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.line import Line
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.load_frequency_control_area import LoadFrequencyControlArea
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_schedule import PowerSchedule
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_shift_key_strategy import PowerShiftKeyStrategy
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.scheduling_area import SchedulingArea
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.substation import Substation
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.synchronous_area import SynchronousArea
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.system_operator import SystemOperator

class SchedulingArea(PowerSystemResource):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='AreaDispatchableUnit', class_type='AreaDispatchableUnit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='BiddingZone', class_type='BiddingZone', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='ControlArea', class_type='ControlArea', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='DCTieCorridor', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='EnergyCoordinationRegion', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='EnergyGroup', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='HasPart', class_type='SchedulingArea', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='Line', class_type='Line', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='LoadFrequencyControlArea', class_type='LoadFrequencyControlArea', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='PartOf', class_type='SchedulingArea', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='PowerCapacity', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='PowerSchedule', class_type='PowerSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='PowerShiftKeyStrategy', class_type='PowerShiftKeyStrategy', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='ScheduleResource', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='SchedulingAreaExchangePoint', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='Substation', class_type='Substation', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='SynchronousArea', class_type='SynchronousArea', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='SystemOperator', class_type='SystemOperator', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='isIslandingEnabled', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='isMeteringGridArea', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='normalParticipationFactor', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='p', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='participationFactor', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='type', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
    )
    __slots__ = ('AreaDispatchableUnit', 'BiddingZone', 'ControlArea', 'DCTieCorridor', 'EnergyCoordinationRegion', 'EnergyGroup', 'HasPart', 'Line', 'LoadFrequencyControlArea', 'PartOf', 'PowerCapacity', 'PowerSchedule', 'PowerShiftKeyStrategy', 'ScheduleResource', 'SchedulingAreaExchangePoint', 'Substation', 'SynchronousArea', 'SystemOperator', 'isIslandingEnabled', 'isMeteringGridArea', 'normalParticipationFactor', 'p', 'participationFactor', 'type')

    def __init__(self, rdfid: str = '', tpe: str = 'SchedulingArea'):
        PowerSystemResource.__init__(self, rdfid, tpe)

        self.AreaDispatchableUnit: AreaDispatchableUnit | None = None
        self.BiddingZone: BiddingZone | None = None
        self.ControlArea: ControlArea | None = None
        self.DCTieCorridor: str | None = None
        self.EnergyCoordinationRegion: str | None = None
        self.EnergyGroup: str | None = None
        self.HasPart: SchedulingArea | None = None
        self.Line: Line | None = None
        self.LoadFrequencyControlArea: LoadFrequencyControlArea | None = None
        self.PartOf: SchedulingArea | None = None
        self.PowerCapacity: str | None = None
        self.PowerSchedule: PowerSchedule | None = None
        self.PowerShiftKeyStrategy: PowerShiftKeyStrategy | None = None
        self.ScheduleResource: str | None = None
        self.SchedulingAreaExchangePoint: str | None = None
        self.Substation: Substation | None = None
        self.SynchronousArea: SynchronousArea | None = None
        self.SystemOperator: SystemOperator | None = None
        self.isIslandingEnabled: bool | None = None
        self.isMeteringGridArea: bool | None = None
        self.normalParticipationFactor: float | None = None
        self.p: float | None = None
        self.participationFactor: float | None = None
        self.type: str | None = None

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
