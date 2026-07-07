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
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.energy_consumer import EnergyConsumer
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.generating_unit import GeneratingUnit
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.hydro_pump import HydroPump
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.power_electronics_unit import PowerElectronicsUnit
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_schedule import PowerSchedule
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.scheduling_area import SchedulingArea
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.tie_corridor import TieCorridor

class AreaDispatchableUnit(PowerSystemResource):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='EnergyConsumer', class_type='EnergyConsumer', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='GeneratingUnit', class_type='GeneratingUnit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='HydroPump', class_type='HydroPump', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='PowerElectronicsUnit', class_type='PowerElectronicsUnit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='PowerSchedule', class_type='PowerSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS]),
        CgmesProperty(property_name='ScheduleResource', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='SchedulingArea', class_type='SchedulingArea', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='TieCorridor', class_type='TieCorridor', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='enabled', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.SSI]),
        CgmesProperty(property_name='normalEnabled', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='p', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SSI]),
    )
    __slots__ = ('EnergyConsumer', 'GeneratingUnit', 'HydroPump', 'PowerElectronicsUnit', 'PowerSchedule', 'ScheduleResource', 'SchedulingArea', 'TieCorridor', 'enabled', 'normalEnabled', 'p')

    def __init__(self, rdfid: str = '', tpe: str = 'AreaDispatchableUnit'):
        PowerSystemResource.__init__(self, rdfid, tpe)

        self.EnergyConsumer: EnergyConsumer | None = None
        self.GeneratingUnit: GeneratingUnit | None = None
        self.HydroPump: HydroPump | None = None
        self.PowerElectronicsUnit: PowerElectronicsUnit | None = None
        self.PowerSchedule: PowerSchedule | None = None
        self.ScheduleResource: str | None = None
        self.SchedulingArea: SchedulingArea | None = None
        self.TieCorridor: TieCorridor | None = None
        self.enabled: bool | None = None
        self.normalEnabled: bool | None = None
        self.p: float | None = None

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
