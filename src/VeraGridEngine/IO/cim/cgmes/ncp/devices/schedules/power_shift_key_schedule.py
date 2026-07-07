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
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.energy_consumer import EnergyConsumer
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.energy_source import EnergySource
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.equivalent_injection import EquivalentInjection
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.external_network_injection import ExternalNetworkInjection
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.generating_unit import GeneratingUnit
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.hydro_pump import HydroPump
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.participation_factor_time_point import ParticipationFactorTimePoint
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.power_electronics_unit import PowerElectronicsUnit
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_shift_key_distribution import PowerShiftKeyDistribution

class PowerShiftKeySchedule(BaseIrregularTimeSeries):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='DCPole', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='EnergyBlockOrder', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='EnergyConsumer', class_type='EnergyConsumer', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='EnergyGroup', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='EnergySource', class_type='EnergySource', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='EquivalentInjection', class_type='EquivalentInjection', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='ExternalNetworkInjection', class_type='ExternalNetworkInjection', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='GeneratingUnit', class_type='GeneratingUnit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='HydroPump', class_type='HydroPump', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='ParticipationFactorTimePoint', class_type='ParticipationFactorTimePoint', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='PowerElectronicsUnit', class_type='PowerElectronicsUnit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='PowerShiftKeyDistribution', class_type='PowerShiftKeyDistribution', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='ScheduleResource', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
    )
    __slots__ = ('DCPole', 'EnergyBlockOrder', 'EnergyConsumer', 'EnergyGroup', 'EnergySource', 'EquivalentInjection', 'ExternalNetworkInjection', 'GeneratingUnit', 'HydroPump', 'ParticipationFactorTimePoint', 'PowerElectronicsUnit', 'PowerShiftKeyDistribution', 'ScheduleResource')

    def __init__(self, rdfid: str = '', tpe: str = 'PowerShiftKeySchedule'):
        BaseIrregularTimeSeries.__init__(self, rdfid, tpe)

        self.DCPole: str | None = None
        self.EnergyBlockOrder: str | None = None
        self.EnergyConsumer: EnergyConsumer | None = None
        self.EnergyGroup: str | None = None
        self.EnergySource: EnergySource | None = None
        self.EquivalentInjection: EquivalentInjection | None = None
        self.ExternalNetworkInjection: ExternalNetworkInjection | None = None
        self.GeneratingUnit: GeneratingUnit | None = None
        self.HydroPump: HydroPump | None = None
        self.ParticipationFactorTimePoint: ParticipationFactorTimePoint | None = None
        self.PowerElectronicsUnit: PowerElectronicsUnit | None = None
        self.PowerShiftKeyDistribution: PowerShiftKeyDistribution | None = None
        self.ScheduleResource: str | None = None

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
