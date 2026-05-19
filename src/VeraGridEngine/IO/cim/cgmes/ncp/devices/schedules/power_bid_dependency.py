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

class PowerBidDependency(Base):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='DependeePowerBidSchedule', class_type='PowerBidSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='DependentPowerBidSchedule', class_type='PowerBidSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='finishToFinishLag', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='finishToFinishLagKind', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='finishToStartLag', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='finishToStartLagKind', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='kind', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='mRID', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='overlap', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='overlapKind', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='startToStartLag', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='startToStartLagKind', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
    )
    __slots__ = ('DependeePowerBidSchedule', 'DependentPowerBidSchedule', 'finishToFinishLag', 'finishToFinishLagKind', 'finishToStartLag', 'finishToStartLagKind', 'kind', 'mRID', 'overlap', 'overlapKind', 'startToStartLag', 'startToStartLagKind')

    def __init__(self, rdfid: str = '', tpe: str = 'PowerBidDependency'):
        Base.__init__(self, rdfid, tpe)

        self.DependeePowerBidSchedule: PowerBidSchedule | None = None
        self.DependentPowerBidSchedule: PowerBidSchedule | None = None
        self.finishToFinishLag: float | None = None
        self.finishToFinishLagKind: str | None = None
        self.finishToStartLag: float | None = None
        self.finishToStartLagKind: str | None = None
        self.kind: str | None = None
        self.mRID: str | None = None
        self.overlap: float | None = None
        self.overlapKind: str | None = None
        self.startToStartLag: float | None = None
        self.startToStartLagKind: str | None = None

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
