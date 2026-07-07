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
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.identified_object import IdentifiedObject

if TYPE_CHECKING:
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.contingency.contingency import Contingency
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.event_schedule import EventSchedule
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.generic_value_schedule import GenericValueSchedule
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.power_schedule_action import PowerScheduleAction
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.region import Region
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action import RemedialAction
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_schedule_dependency import RemedialActionScheduleDependency
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_schedule_outcome_value import RemedialActionScheduleOutcomeValue
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_schedule_response import RemedialActionScheduleResponse
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.security_coordinator import SecurityCoordinator

class RemedialActionSchedule(IdentifiedObject):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='AssignedRegion', class_type='Region', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='Contingency', class_type='Contingency', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='EventSchedule', class_type='EventSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='GenericValueSchedule', class_type='GenericValueSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='PowerScheduleAction', class_type='PowerScheduleAction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='ProposedDependency', class_type='RemedialActionScheduleDependency', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='ProposingEntity', class_type='SecurityCoordinator', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='ProposingRemedialActionScheduleShare', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='RemedialAction', class_type='RemedialAction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='RemedialActionCost', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='RemedialActionScheduleOutcomeValue', class_type='RemedialActionScheduleOutcomeValue', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.IAM]),
        CgmesProperty(property_name='RemedialActionScheduleResponse', class_type='RemedialActionScheduleResponse', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='ReplacedDependency', class_type='RemedialActionScheduleDependency', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='statusKind', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='statusReason', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='totalCostCurrency', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
    )
    __slots__ = ('AssignedRegion', 'Contingency', 'EventSchedule', 'GenericValueSchedule', 'PowerScheduleAction', 'ProposedDependency', 'ProposingEntity', 'ProposingRemedialActionScheduleShare', 'RemedialAction', 'RemedialActionCost', 'RemedialActionScheduleOutcomeValue', 'RemedialActionScheduleResponse', 'ReplacedDependency', 'statusKind', 'statusReason', 'totalCostCurrency')

    def __init__(self, rdfid: str = '', tpe: str = 'RemedialActionSchedule'):
        IdentifiedObject.__init__(self, rdfid, tpe)

        self.AssignedRegion: Region | None = None
        self.Contingency: Contingency | None = None
        self.EventSchedule: EventSchedule | None = None
        self.GenericValueSchedule: GenericValueSchedule | None = None
        self.PowerScheduleAction: PowerScheduleAction | None = None
        self.ProposedDependency: RemedialActionScheduleDependency | None = None
        self.ProposingEntity: SecurityCoordinator | None = None
        self.ProposingRemedialActionScheduleShare: str | None = None
        self.RemedialAction: RemedialAction | None = None
        self.RemedialActionCost: str | None = None
        self.RemedialActionScheduleOutcomeValue: RemedialActionScheduleOutcomeValue | None = None
        self.RemedialActionScheduleResponse: RemedialActionScheduleResponse | None = None
        self.ReplacedDependency: RemedialActionScheduleDependency | None = None
        self.statusKind: str | None = None
        self.statusReason: str | None = None
        self.totalCostCurrency: str | None = None

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
