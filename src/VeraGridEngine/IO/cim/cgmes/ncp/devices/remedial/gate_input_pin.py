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
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.function_input_variable import FunctionInputVariable

if TYPE_CHECKING:
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.gate import Gate

class GateInputPin(FunctionInputVariable):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='Gate', class_type='Gate', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.RA]),
        CgmesProperty(property_name='absoluteValue', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.ER, CgmesProfileType.RA]),
        CgmesProperty(property_name='duration', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.ER, CgmesProfileType.RA]),
        CgmesProperty(property_name='isValuePreFault', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.RA]),
        CgmesProperty(property_name='logicKind', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER, CgmesProfileType.RA]),
        CgmesProperty(property_name='negate', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.ER, CgmesProfileType.RA]),
        CgmesProperty(property_name='thresholdPercentage', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER, CgmesProfileType.RA]),
        CgmesProperty(property_name='thresholdValue', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER, CgmesProfileType.RA]),
    )
    __slots__ = ('Gate', 'absoluteValue', 'duration', 'isValuePreFault', 'logicKind', 'negate', 'thresholdPercentage', 'thresholdValue')

    def __init__(self, rdfid: str = '', tpe: str = 'GateInputPin'):
        FunctionInputVariable.__init__(self, rdfid, tpe)

        self.Gate: Gate | None = None
        self.absoluteValue: bool | None = None
        self.duration: float | None = None
        self.isValuePreFault: bool | None = None
        self.logicKind: str | None = None
        self.negate: bool | None = None
        self.thresholdPercentage: float | None = None
        self.thresholdValue: float | None = None

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
