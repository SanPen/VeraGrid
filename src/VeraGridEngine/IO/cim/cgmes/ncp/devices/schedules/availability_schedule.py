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
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.operations.availability_power_system_function import AvailabilityPowerSystemFunction
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.availability_remedial_action import AvailabilityRemedialAction
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.availability_schedule import AvailabilitySchedule
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.event_schedule import EventSchedule
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.operations.grid_state_alteration_collection import GridStateAlterationCollection

class AvailabilitySchedule(IdentifiedObject):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='ActualSchedule', class_type='EventSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='AlternativeSchedule', class_type='AvailabilitySchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='AvailabilityPowerSystemFunction', class_type='AvailabilityPowerSystemFunction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='AvailabilitySchedule', class_type='AvailabilitySchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='DependentOnSchedule', class_type='AvailabilitySchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='GridStateAlterationCollection', class_type='GridStateAlterationCollection', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='PlannedSchedule', class_type='EventSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='PowerSystemProject', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='PrioritySchedule', class_type='AvailabilitySchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='RemedialAction', class_type='AvailabilityRemedialAction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='cancelledDateTime', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='causeDescription', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='causeKind', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='daytimeRestitutionDuration', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='eveningRestitutionDuration', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='isCancelled', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='maxRestitutionDuration', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='priority', class_type=int, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
        CgmesProperty(property_name='weekendRestitutionDuration', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS, CgmesProfileType.PS, CgmesProfileType.AVS, CgmesProfileType.SHS, CgmesProfileType.SIS]),
    )
    __slots__ = ('ActualSchedule', 'AlternativeSchedule', 'AvailabilityPowerSystemFunction', 'AvailabilitySchedule', 'DependentOnSchedule', 'GridStateAlterationCollection', 'PlannedSchedule', 'PowerSystemProject', 'PrioritySchedule', 'RemedialAction', 'cancelledDateTime', 'causeDescription', 'causeKind', 'daytimeRestitutionDuration', 'eveningRestitutionDuration', 'isCancelled', 'maxRestitutionDuration', 'priority', 'weekendRestitutionDuration')

    def __init__(self, rdfid: str = '', tpe: str = 'AvailabilitySchedule'):
        IdentifiedObject.__init__(self, rdfid, tpe)

        self.ActualSchedule: EventSchedule | None = None
        self.AlternativeSchedule: AvailabilitySchedule | None = None
        self.AvailabilityPowerSystemFunction: AvailabilityPowerSystemFunction | None = None
        self.AvailabilitySchedule: AvailabilitySchedule | None = None
        self.DependentOnSchedule: AvailabilitySchedule | None = None
        self.GridStateAlterationCollection: GridStateAlterationCollection | None = None
        self.PlannedSchedule: EventSchedule | None = None
        self.PowerSystemProject: str | None = None
        self.PrioritySchedule: AvailabilitySchedule | None = None
        self.RemedialAction: AvailabilityRemedialAction | None = None
        self.cancelledDateTime: str | None = None
        self.causeDescription: str | None = None
        self.causeKind: str | None = None
        self.daytimeRestitutionDuration: float | None = None
        self.eveningRestitutionDuration: float | None = None
        self.isCancelled: bool | None = None
        self.maxRestitutionDuration: float | None = None
        self.priority: int | None = None
        self.weekendRestitutionDuration: float | None = None

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
