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
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.assessed_element_schedule import AssessedElementSchedule

class AssessedElementTimePoint(Base):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='AssessedElementSchedule', class_type='AssessedElementSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='appointedMargin', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='atTime', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='coordinatedValidationAdjustment', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='coordinatedValidationAdjustmentJustification', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='criticalElementJustification', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='enabled', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='exclusionReason', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='individualValidationAdjustment', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='individualValidationAdjustmentJustification', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='individualValidationAdjustmentShare', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='maxFlow', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='positiveVirtualMargin', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='scannedThresholdMargin', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='targetRemainingAvailableMarginJustification', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
    )
    __slots__ = ('AssessedElementSchedule', 'appointedMargin', 'atTime', 'coordinatedValidationAdjustment', 'coordinatedValidationAdjustmentJustification', 'criticalElementJustification', 'enabled', 'exclusionReason', 'individualValidationAdjustment', 'individualValidationAdjustmentJustification', 'individualValidationAdjustmentShare', 'maxFlow', 'positiveVirtualMargin', 'scannedThresholdMargin', 'targetRemainingAvailableMarginJustification')

    def __init__(self, rdfid: str = '', tpe: str = 'AssessedElementTimePoint'):
        Base.__init__(self, rdfid, tpe)

        self.AssessedElementSchedule: AssessedElementSchedule | None = None
        self.appointedMargin: float | None = None
        self.atTime: str | None = None
        self.coordinatedValidationAdjustment: float | None = None
        self.coordinatedValidationAdjustmentJustification: str | None = None
        self.criticalElementJustification: str | None = None
        self.enabled: bool | None = None
        self.exclusionReason: str | None = None
        self.individualValidationAdjustment: float | None = None
        self.individualValidationAdjustmentJustification: str | None = None
        self.individualValidationAdjustmentShare: float | None = None
        self.maxFlow: float | None = None
        self.positiveVirtualMargin: float | None = None
        self.scannedThresholdMargin: float | None = None
        self.targetRemainingAvailableMarginJustification: str | None = None

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
