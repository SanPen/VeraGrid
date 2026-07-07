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
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.circuit import Circuit
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.power_transfer_corridor import PowerTransferCorridor

class CircuitShare(IdentifiedObject):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='Circuit', class_type='Circuit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='PowerTransferCorridor', class_type='PowerTransferCorridor', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='contributionFactor', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.SSI]),
        CgmesProperty(property_name='normalContributionFactor', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
    )
    __slots__ = ('Circuit', 'PowerTransferCorridor', 'contributionFactor', 'normalContributionFactor')

    def __init__(self, rdfid: str = '', tpe: str = 'CircuitShare'):
        IdentifiedObject.__init__(self, rdfid, tpe)

        self.Circuit: Circuit | None = None
        self.PowerTransferCorridor: PowerTransferCorridor | None = None
        self.contributionFactor: float | None = None
        self.normalContributionFactor: float | None = None

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
