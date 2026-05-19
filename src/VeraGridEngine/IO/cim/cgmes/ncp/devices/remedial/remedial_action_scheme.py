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
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.gate import Gate
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.scheme_remedial_action import SchemeRemedialAction
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.stage import Stage
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.trigger_condition import TriggerCondition

class RemedialActionScheme(PowerSystemResource):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='AvailabilityRemedialActionScheme', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='GateArmed', class_type='Gate', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='PTCActivePowerSupport', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='RemedialActionSchemeSchedule', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='SchemeRemedialAction', class_type='SchemeRemedialAction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='Stage', class_type='Stage', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='TriggerCondition', class_type='TriggerCondition', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='armed', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='inService', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='kind', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='normalArmed', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
        CgmesProperty(property_name='normallyInService', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RA, CgmesProfileType.RAS, CgmesProfileType.SAR]),
    )
    __slots__ = ('AvailabilityRemedialActionScheme', 'GateArmed', 'PTCActivePowerSupport', 'RemedialActionSchemeSchedule', 'SchemeRemedialAction', 'Stage', 'TriggerCondition', 'armed', 'inService', 'kind', 'normalArmed', 'normallyInService')

    def __init__(self, rdfid: str = '', tpe: str = 'RemedialActionScheme'):
        PowerSystemResource.__init__(self, rdfid, tpe)

        self.AvailabilityRemedialActionScheme: str | None = None
        self.GateArmed: Gate | None = None
        self.PTCActivePowerSupport: str | None = None
        self.RemedialActionSchemeSchedule: str | None = None
        self.SchemeRemedialAction: SchemeRemedialAction | None = None
        self.Stage: Stage | None = None
        self.TriggerCondition: TriggerCondition | None = None
        self.armed: bool | None = None
        self.inService: bool | None = None
        self.kind: str | None = None
        self.normalArmed: bool | None = None
        self.normallyInService: bool | None = None

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
