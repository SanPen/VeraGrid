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
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.acdc_terminal import ACDCTerminal
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.operational_limit import OperationalLimit
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.power_transfer_corridor import PowerTransferCorridor
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.region import Region
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.topological_node import TopologicalNode

class PowerFlowResult(Base):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='ACDCTerminal', class_type='ACDCTerminal', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SAR]),
        CgmesProperty(property_name='OperationalLimit', class_type='OperationalLimit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SAR]),
        CgmesProperty(property_name='PowerTransferCorridor', class_type='PowerTransferCorridor', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SAR]),
        CgmesProperty(property_name='RemedialActionApplied', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SAR]),
        CgmesProperty(property_name='ReportedByRegion', class_type='Region', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SAR]),
        CgmesProperty(property_name='TopologicalNode', class_type='TopologicalNode', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SAR]),
        CgmesProperty(property_name='absoluteValue', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SAR]),
        CgmesProperty(property_name='atTime', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SAR]),
        CgmesProperty(property_name='isViolation', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SAR]),
        CgmesProperty(property_name='value', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SAR]),
        CgmesProperty(property_name='valueA', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SAR]),
        CgmesProperty(property_name='valueAngle', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SAR]),
        CgmesProperty(property_name='valueV', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SAR]),
        CgmesProperty(property_name='valueVA', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SAR]),
        CgmesProperty(property_name='valueVAR', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SAR]),
        CgmesProperty(property_name='valueW', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SAR]),
    )
    __slots__ = ('ACDCTerminal', 'OperationalLimit', 'PowerTransferCorridor', 'RemedialActionApplied', 'ReportedByRegion', 'TopologicalNode', 'absoluteValue', 'atTime', 'isViolation', 'value', 'valueA', 'valueAngle', 'valueV', 'valueVA', 'valueVAR', 'valueW')

    def __init__(self, rdfid: str = '', tpe: str = 'PowerFlowResult'):
        Base.__init__(self, rdfid, tpe)

        self.ACDCTerminal: ACDCTerminal | None = None
        self.OperationalLimit: OperationalLimit | None = None
        self.PowerTransferCorridor: PowerTransferCorridor | None = None
        self.RemedialActionApplied: str | None = None
        self.ReportedByRegion: Region | None = None
        self.TopologicalNode: TopologicalNode | None = None
        self.absoluteValue: float | None = None
        self.atTime: str | None = None
        self.isViolation: bool | None = None
        self.value: float | None = None
        self.valueA: float | None = None
        self.valueAngle: float | None = None
        self.valueV: float | None = None
        self.valueVA: float | None = None
        self.valueVAR: float | None = None
        self.valueW: float | None = None

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
