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
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.assessed_element_with_remedial_action import AssessedElementWithRemedialAction
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.contingency.contingency_with_remedial_action import ContingencyWithRemedialAction
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.region import Region
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_dependency import RemedialActionDependency
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_outcome_value import RemedialActionOutcomeValue
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_schedule import RemedialActionSchedule
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.system_operator import SystemOperator

class RemedialAction(IdentifiedObject):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='AppointedToRegion', class_type='Region', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='AssessedElementWithRemedialAction', class_type='AssessedElementWithRemedialAction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='ContingencyWithRemedialAction', class_type='ContingencyWithRemedialAction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='ControllableQuantity', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='DependentRemedialAction', class_type='RemedialActionDependency', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='GenericAvailableSchedule', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='RemedialActionApplied', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='RemedialActionImpact', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='RemedialActionOutcomeValue', class_type='RemedialActionOutcomeValue', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='RemedialActionSchedule', class_type='RemedialActionSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='RemedialActionSystemOperator', class_type='SystemOperator', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='available', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='impactThresholdMargin', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='isCrossBorderRelevant', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='isManual', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='kind', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='normalAvailable', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='penaltyFactor', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='timeToImplement', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
    )
    __slots__ = ('AppointedToRegion', 'AssessedElementWithRemedialAction', 'ContingencyWithRemedialAction', 'ControllableQuantity', 'DependentRemedialAction', 'GenericAvailableSchedule', 'RemedialActionApplied', 'RemedialActionImpact', 'RemedialActionOutcomeValue', 'RemedialActionSchedule', 'RemedialActionSystemOperator', 'available', 'impactThresholdMargin', 'isCrossBorderRelevant', 'isManual', 'kind', 'normalAvailable', 'penaltyFactor', 'timeToImplement')

    def __init__(self, rdfid: str = '', tpe: str = 'RemedialAction'):
        IdentifiedObject.__init__(self, rdfid, tpe)

        self.AppointedToRegion: Region | None = None
        self.AssessedElementWithRemedialAction: AssessedElementWithRemedialAction | None = None
        self.ContingencyWithRemedialAction: ContingencyWithRemedialAction | None = None
        self.ControllableQuantity: str | None = None
        self.DependentRemedialAction: RemedialActionDependency | None = None
        self.GenericAvailableSchedule: str | None = None
        self.RemedialActionApplied: str | None = None
        self.RemedialActionImpact: str | None = None
        self.RemedialActionOutcomeValue: RemedialActionOutcomeValue | None = None
        self.RemedialActionSchedule: RemedialActionSchedule | None = None
        self.RemedialActionSystemOperator: SystemOperator | None = None
        self.available: bool | None = None
        self.impactThresholdMargin: float | None = None
        self.isCrossBorderRelevant: bool | None = None
        self.isManual: bool | None = None
        self.kind: str | None = None
        self.normalAvailable: bool | None = None
        self.penaltyFactor: float | None = None
        self.timeToImplement: float | None = None

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
