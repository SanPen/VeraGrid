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
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.assessed_element import AssessedElement
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.results.power_flow_result import PowerFlowResult
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action import RemedialAction
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_schedule import RemedialActionSchedule

class Region(PowerSystemResource):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='LimitViolation', class_type='PowerFlowResult', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SAR]),
        CgmesProperty(property_name='MonitoringArea', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.MA]),
        CgmesProperty(property_name='NativeAssessedElement', class_type='AssessedElement', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.AE]),
        CgmesProperty(property_name='OverlappingZone', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='RemedialAction', class_type='RemedialAction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RA]),
        CgmesProperty(property_name='RemedialActionSchedule', class_type='RemedialActionSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='ScannedAssessedElement', class_type='AssessedElement', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.AE]),
        CgmesProperty(property_name='SecuredAssessedElement', class_type='AssessedElement', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.AE]),
    )
    __slots__ = ('LimitViolation', 'MonitoringArea', 'NativeAssessedElement', 'OverlappingZone', 'RemedialAction', 'RemedialActionSchedule', 'ScannedAssessedElement', 'SecuredAssessedElement')

    def __init__(self, rdfid: str = '', tpe: str = 'Region'):
        PowerSystemResource.__init__(self, rdfid, tpe)

        self.LimitViolation: PowerFlowResult | None = None
        self.MonitoringArea: str | None = None
        self.NativeAssessedElement: AssessedElement | None = None
        self.OverlappingZone: str | None = None
        self.RemedialAction: RemedialAction | None = None
        self.RemedialActionSchedule: RemedialActionSchedule | None = None
        self.ScannedAssessedElement: AssessedElement | None = None
        self.SecuredAssessedElement: AssessedElement | None = None

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
