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
from VeraGridEngine.IO.cim.cgmes.base import Base

if TYPE_CHECKING:
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_bid_schedule import PowerBidSchedule

class PowerBidScheduleTimePoint(Base):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='PowerBidSchedule', class_type='PowerBidSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='activationCost', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='atTime', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='minimumActivationP', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='p', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='price', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='reservePrice', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='shutdownCost', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='stepIncrementP', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
    )
    __slots__ = ('PowerBidSchedule', 'activationCost', 'atTime', 'minimumActivationP', 'p', 'price', 'reservePrice', 'shutdownCost', 'stepIncrementP')

    def __init__(self, rdfid: str = '', tpe: str = 'PowerBidScheduleTimePoint'):
        Base.__init__(self, rdfid, tpe)

        self.PowerBidSchedule: PowerBidSchedule | None = None
        self.activationCost: float | None = None
        self.atTime: str | None = None
        self.minimumActivationP: float | None = None
        self.p: float | None = None
        self.price: float | None = None
        self.reservePrice: float | None = None
        self.shutdownCost: float | None = None
        self.stepIncrementP: float | None = None

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
