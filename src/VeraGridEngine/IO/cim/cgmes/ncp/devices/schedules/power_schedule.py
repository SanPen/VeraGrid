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
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.market.area_dispatchable_unit import AreaDispatchableUnit
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.bidding_zone import BiddingZone
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.bidding_zone_border import BiddingZoneBorder
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.energy_connection import EnergyConnection
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.equivalent_injection import EquivalentInjection
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.generating_unit import GeneratingUnit
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.hydro_pump import HydroPump
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.power_electronics_unit import PowerElectronicsUnit
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.power_remedial_action import PowerRemedialAction
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.power_schedule_action import PowerScheduleAction
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_time_point import PowerTimePoint
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.scheduling_area import SchedulingArea

class PowerSchedule(BaseIrregularTimeSeries):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='AreaDispatchableUnit', class_type='AreaDispatchableUnit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS]),
        CgmesProperty(property_name='BiddingZone', class_type='BiddingZone', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS]),
        CgmesProperty(property_name='BiddingZoneBorder', class_type='BiddingZoneBorder', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS]),
        CgmesProperty(property_name='DCPole', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS]),
        CgmesProperty(property_name='DCTieCorridor', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS]),
        CgmesProperty(property_name='EnergyConnection', class_type='EnergyConnection', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS]),
        CgmesProperty(property_name='EnergyGroup', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS]),
        CgmesProperty(property_name='EquivalentInjection', class_type='EquivalentInjection', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS]),
        CgmesProperty(property_name='GeneratingUnit', class_type='GeneratingUnit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS]),
        CgmesProperty(property_name='HydroPump', class_type='HydroPump', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS]),
        CgmesProperty(property_name='PowerElectronicsUnit', class_type='PowerElectronicsUnit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS]),
        CgmesProperty(property_name='PowerRemedialAction', class_type='PowerRemedialAction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS]),
        CgmesProperty(property_name='PowerScheduleAction', class_type='PowerScheduleAction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='PowerTimePoint', class_type='PowerTimePoint', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS, CgmesProfileType.RAS]),
        CgmesProperty(property_name='SchedulingArea', class_type='SchedulingArea', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS]),
        CgmesProperty(property_name='currency', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS, CgmesProfileType.RAS]),
        CgmesProperty(property_name='direction', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS]),
        CgmesProperty(property_name='powerScheduleKind', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.PS]),
    )
    __slots__ = ('AreaDispatchableUnit', 'BiddingZone', 'BiddingZoneBorder', 'DCPole', 'DCTieCorridor', 'EnergyConnection', 'EnergyGroup', 'EquivalentInjection', 'GeneratingUnit', 'HydroPump', 'PowerElectronicsUnit', 'PowerRemedialAction', 'PowerScheduleAction', 'PowerTimePoint', 'SchedulingArea', 'currency', 'direction', 'powerScheduleKind')

    def __init__(self, rdfid: str = '', tpe: str = 'PowerSchedule'):
        BaseIrregularTimeSeries.__init__(self, rdfid, tpe)

        self.AreaDispatchableUnit: AreaDispatchableUnit | None = None
        self.BiddingZone: BiddingZone | None = None
        self.BiddingZoneBorder: BiddingZoneBorder | None = None
        self.DCPole: str | None = None
        self.DCTieCorridor: str | None = None
        self.EnergyConnection: EnergyConnection | None = None
        self.EnergyGroup: str | None = None
        self.EquivalentInjection: EquivalentInjection | None = None
        self.GeneratingUnit: GeneratingUnit | None = None
        self.HydroPump: HydroPump | None = None
        self.PowerElectronicsUnit: PowerElectronicsUnit | None = None
        self.PowerRemedialAction: PowerRemedialAction | None = None
        self.PowerScheduleAction: PowerScheduleAction | None = None
        self.PowerTimePoint: PowerTimePoint | None = None
        self.SchedulingArea: SchedulingArea | None = None
        self.currency: str | None = None
        self.direction: str | None = None
        self.powerScheduleKind: str | None = None

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
