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
from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.system_operation_coordinator import SystemOperationCoordinator

if TYPE_CHECKING:
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.capacity_calculation_region import CapacityCalculationRegion

class CoordinatedCapacityCalculator(SystemOperationCoordinator):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='CapacityCalculationRegion', class_type='CapacityCalculationRegion', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
    )
    __slots__ = ('CapacityCalculationRegion')

    def __init__(self, rdfid: str = '', tpe: str = 'CoordinatedCapacityCalculator'):
        SystemOperationCoordinator.__init__(self, rdfid, tpe)

        self.CapacityCalculationRegion: CapacityCalculationRegion | None = None

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
