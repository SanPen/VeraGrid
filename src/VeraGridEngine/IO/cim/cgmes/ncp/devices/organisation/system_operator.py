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
from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.power_system_organisation_role import PowerSystemOrganisationRole

if TYPE_CHECKING:
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.assessed_element import AssessedElement
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.contingency.contingency import Contingency
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.control_area import ControlArea
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.outcome_value import OutcomeValue
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action import RemedialAction
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_schedule_response import RemedialActionScheduleResponse
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.scheduling_area import SchedulingArea

class SystemOperator(PowerSystemOrganisationRole):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='AssessedElement', class_type='AssessedElement', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.AE]),
        CgmesProperty(property_name='Contingency', class_type='Contingency', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.CO]),
        CgmesProperty(property_name='ControlArea', class_type='ControlArea', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='Fault', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.MA]),
        CgmesProperty(property_name='MonitoringArea', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.MA]),
        CgmesProperty(property_name='OutcomeValue', class_type='OutcomeValue', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.IAM]),
        CgmesProperty(property_name='OwnerRemedialActionAssessment', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.IAM]),
        CgmesProperty(property_name='ProposingRemedialActionScheduleShare', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='RemedialAction', class_type='RemedialAction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RA]),
        CgmesProperty(property_name='RemedialActionImpact', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.IAM]),
        CgmesProperty(property_name='RemedialActionScheduleResponse', class_type='RemedialActionScheduleResponse', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='SchedulingArea', class_type='SchedulingArea', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
    )
    __slots__ = ('AssessedElement', 'Contingency', 'ControlArea', 'Fault', 'MonitoringArea', 'OutcomeValue', 'OwnerRemedialActionAssessment', 'ProposingRemedialActionScheduleShare', 'RemedialAction', 'RemedialActionImpact', 'RemedialActionScheduleResponse', 'SchedulingArea')

    def __init__(self, rdfid: str = '', tpe: str = 'SystemOperator'):
        PowerSystemOrganisationRole.__init__(self, rdfid, tpe)

        self.AssessedElement: AssessedElement | None = None
        self.Contingency: Contingency | None = None
        self.ControlArea: ControlArea | None = None
        self.Fault: str | None = None
        self.MonitoringArea: str | None = None
        self.OutcomeValue: OutcomeValue | None = None
        self.OwnerRemedialActionAssessment: str | None = None
        self.ProposingRemedialActionScheduleShare: str | None = None
        self.RemedialAction: RemedialAction | None = None
        self.RemedialActionImpact: str | None = None
        self.RemedialActionScheduleResponse: RemedialActionScheduleResponse | None = None
        self.SchedulingArea: SchedulingArea | None = None

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
