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
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.assessed_element_with_contingency import AssessedElementWithContingency
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.contingency.contingency_element import ContingencyElement
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.contingency.contingency_power_flow_result import ContingencyPowerFlowResult
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.contingency.contingency_with_remedial_action import ContingencyWithRemedialAction
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.contingency.pin_contingency import PinContingency
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_schedule import RemedialActionSchedule
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.system_operator import SystemOperator

class Contingency(IdentifiedObject):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='AssessedElementWithContingency', class_type='AssessedElementWithContingency', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.AE]),
        CgmesProperty(property_name='ContingencyElement', class_type='ContingencyElement', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.CO]),
        CgmesProperty(property_name='ContingencyPowerFlowResult', class_type='ContingencyPowerFlowResult', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SAR]),
        CgmesProperty(property_name='ContingencySchedule', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='ContingencyWithRemedialAction', class_type='ContingencyWithRemedialAction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RA]),
        CgmesProperty(property_name='CurativeRemedialActionSchedule', class_type='RemedialActionSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RAS]),
        CgmesProperty(property_name='EquipmentOperator', class_type='SystemOperator', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.CO]),
        CgmesProperty(property_name='ObservableQuantity', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SM]),
        CgmesProperty(property_name='PinContingency', class_type='PinContingency', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RA]),
        CgmesProperty(property_name='SimulationEvents', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.CO]),
        CgmesProperty(property_name='mustStudy', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.SSI]),
        CgmesProperty(property_name='normalMustStudy', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.CO]),
        CgmesProperty(property_name='normalProbability', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.CO]),
        CgmesProperty(property_name='probability', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SSI]),
    )
    __slots__ = ('AssessedElementWithContingency', 'ContingencyElement', 'ContingencyPowerFlowResult', 'ContingencySchedule', 'ContingencyWithRemedialAction', 'CurativeRemedialActionSchedule', 'EquipmentOperator', 'ObservableQuantity', 'PinContingency', 'SimulationEvents', 'mustStudy', 'normalMustStudy', 'normalProbability', 'probability')

    def __init__(self, rdfid: str = '', tpe: str = 'Contingency'):
        IdentifiedObject.__init__(self, rdfid, tpe)

        self.AssessedElementWithContingency: AssessedElementWithContingency | None = None
        self.ContingencyElement: ContingencyElement | None = None
        self.ContingencyPowerFlowResult: ContingencyPowerFlowResult | None = None
        self.ContingencySchedule: str | None = None
        self.ContingencyWithRemedialAction: ContingencyWithRemedialAction | None = None
        self.CurativeRemedialActionSchedule: RemedialActionSchedule | None = None
        self.EquipmentOperator: SystemOperator | None = None
        self.ObservableQuantity: str | None = None
        self.PinContingency: PinContingency | None = None
        self.SimulationEvents: str | None = None
        self.mustStudy: bool | None = None
        self.normalMustStudy: bool | None = None
        self.normalProbability: float | None = None
        self.probability: float | None = None

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
