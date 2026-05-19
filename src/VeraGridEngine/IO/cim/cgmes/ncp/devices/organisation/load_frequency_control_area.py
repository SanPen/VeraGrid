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
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.load_frequency_control_block import LoadFrequencyControlBlock
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.scheduling_area import SchedulingArea
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.tie_corridor import TieCorridor

class LoadFrequencyControlArea(PowerSystemResource):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='FrequencyControlOperator', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='LoadFrequencyControlBlock', class_type='LoadFrequencyControlBlock', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='SchedulingArea', class_type='SchedulingArea', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='TieCorridor', class_type='TieCorridor', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='deficientGenerationLimit', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='frequencyBiasFactor', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='frequencyRestorationReserveDelay', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='frequencyRestorationReserveMaxRamp', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='frequencyRestorationReserveThreshold', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='includeFrequencyBias', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
    )
    __slots__ = ('FrequencyControlOperator', 'LoadFrequencyControlBlock', 'SchedulingArea', 'TieCorridor', 'deficientGenerationLimit', 'frequencyBiasFactor', 'frequencyRestorationReserveDelay', 'frequencyRestorationReserveMaxRamp', 'frequencyRestorationReserveThreshold', 'includeFrequencyBias')

    def __init__(self, rdfid: str = '', tpe: str = 'LoadFrequencyControlArea'):
        PowerSystemResource.__init__(self, rdfid, tpe)

        self.FrequencyControlOperator: str | None = None
        self.LoadFrequencyControlBlock: LoadFrequencyControlBlock | None = None
        self.SchedulingArea: SchedulingArea | None = None
        self.TieCorridor: TieCorridor | None = None
        self.deficientGenerationLimit: float | None = None
        self.frequencyBiasFactor: float | None = None
        self.frequencyRestorationReserveDelay: float | None = None
        self.frequencyRestorationReserveMaxRamp: str | None = None
        self.frequencyRestorationReserveThreshold: float | None = None
        self.includeFrequencyBias: bool | None = None

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
