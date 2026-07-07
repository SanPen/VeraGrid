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
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.bidding_zone_border import BiddingZoneBorder
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.load_frequency_control_area import LoadFrequencyControlArea
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.tie_flow import TieFlow

class TieCorridor(PowerSystemResource):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='AreaDispatchableUnit', class_type='AreaDispatchableUnit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='BiddingZoneBorder', class_type='BiddingZoneBorder', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='LoadFrequencyControlArea', class_type='LoadFrequencyControlArea', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='TieFlow', class_type='TieFlow', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='delayRegulatingReserve', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='maxRegulatingReserveRamp', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='thresholdRegulatingReserve', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
    )
    __slots__ = ('AreaDispatchableUnit', 'BiddingZoneBorder', 'LoadFrequencyControlArea', 'TieFlow', 'delayRegulatingReserve', 'maxRegulatingReserveRamp', 'thresholdRegulatingReserve')

    def __init__(self, rdfid: str = '', tpe: str = 'TieCorridor'):
        PowerSystemResource.__init__(self, rdfid, tpe)

        self.AreaDispatchableUnit: AreaDispatchableUnit | None = None
        self.BiddingZoneBorder: BiddingZoneBorder | None = None
        self.LoadFrequencyControlArea: LoadFrequencyControlArea | None = None
        self.TieFlow: TieFlow | None = None
        self.delayRegulatingReserve: float | None = None
        self.maxRegulatingReserveRamp: float | None = None
        self.thresholdRegulatingReserve: float | None = None

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
