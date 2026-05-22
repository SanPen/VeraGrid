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
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.circuit_share import CircuitShare
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.operational_limit_set import OperationalLimitSet
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.results.power_flow_result import PowerFlowResult

class PowerTransferCorridor(PowerSystemResource):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='AssessedElement', class_type='AssessedElement', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.AE]),
        CgmesProperty(property_name='CircuitShare', class_type='CircuitShare', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='GenericEnablingSchedule', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='OperationalLimitSet', class_type='OperationalLimitSet', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='PTCActivePowerSupport', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RA]),
        CgmesProperty(property_name='PinPowerTransferCorridor', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RA]),
        CgmesProperty(property_name='PowerFlowResult', class_type='PowerFlowResult', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SAR]),
        CgmesProperty(property_name='enabled', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.SSI]),
        CgmesProperty(property_name='normalEnabled', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
    )
    __slots__ = ('AssessedElement', 'CircuitShare', 'GenericEnablingSchedule', 'OperationalLimitSet', 'PTCActivePowerSupport', 'PinPowerTransferCorridor', 'PowerFlowResult', 'enabled', 'normalEnabled')

    def __init__(self, rdfid: str = '', tpe: str = 'PowerTransferCorridor'):
        PowerSystemResource.__init__(self, rdfid, tpe)

        self.AssessedElement: AssessedElement | None = None
        self.CircuitShare: CircuitShare | None = None
        self.GenericEnablingSchedule: str | None = None
        self.OperationalLimitSet: OperationalLimitSet | None = None
        self.PTCActivePowerSupport: str | None = None
        self.PinPowerTransferCorridor: str | None = None
        self.PowerFlowResult: PowerFlowResult | None = None
        self.enabled: bool | None = None
        self.normalEnabled: bool | None = None

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
