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
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.operations.grid_state_alteration_collection import GridStateAlterationCollection
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.grid_state_alteration_remedial_action import GridStateAlterationRemedialAction
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.grid_state_alteration_schedule import GridStateAlterationSchedule
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.grid_state_intensity_schedule import GridStateIntensitySchedule
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.operations.range_constraint import RangeConstraint

class GridStateAlteration(IdentifiedObject):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='AvailabilityEnabled', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER, CgmesProfileType.AVS, CgmesProfileType.GD]),
        CgmesProperty(property_name='ControllableQuantity', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER, CgmesProfileType.AVS, CgmesProfileType.GD]),
        CgmesProperty(property_name='GridStateAlterationCollection', class_type='GridStateAlterationCollection', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER, CgmesProfileType.AVS, CgmesProfileType.GD]),
        CgmesProperty(property_name='GridStateAlterationRemedialAction', class_type='GridStateAlterationRemedialAction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER, CgmesProfileType.AVS, CgmesProfileType.GD]),
        CgmesProperty(property_name='GridStateAlterationSchedule', class_type='GridStateAlterationSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER, CgmesProfileType.AVS, CgmesProfileType.GD]),
        CgmesProperty(property_name='GridStateIntensitySchedule', class_type='GridStateIntensitySchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER, CgmesProfileType.AVS, CgmesProfileType.GD]),
        CgmesProperty(property_name='PropertyReference', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER, CgmesProfileType.AVS, CgmesProfileType.GD]),
        CgmesProperty(property_name='RangeConstraint', class_type='RangeConstraint', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER, CgmesProfileType.AVS, CgmesProfileType.GD]),
        CgmesProperty(property_name='enabled', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER, CgmesProfileType.AVS, CgmesProfileType.GD]),
        CgmesProperty(property_name='maximumPerDay', class_type=int, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER, CgmesProfileType.AVS, CgmesProfileType.GD]),
        CgmesProperty(property_name='minimumActivation', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER, CgmesProfileType.AVS, CgmesProfileType.GD]),
        CgmesProperty(property_name='normalEnabled', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER, CgmesProfileType.AVS, CgmesProfileType.GD]),
        CgmesProperty(property_name='participationFactor', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER, CgmesProfileType.AVS, CgmesProfileType.GD]),
        CgmesProperty(property_name='timePerStage', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER, CgmesProfileType.AVS, CgmesProfileType.GD]),
    )
    __slots__ = ('AvailabilityEnabled', 'ControllableQuantity', 'GridStateAlterationCollection', 'GridStateAlterationRemedialAction', 'GridStateAlterationSchedule', 'GridStateIntensitySchedule', 'PropertyReference', 'RangeConstraint', 'enabled', 'maximumPerDay', 'minimumActivation', 'normalEnabled', 'participationFactor', 'timePerStage')

    def __init__(self, rdfid: str = '', tpe: str = 'GridStateAlteration'):
        IdentifiedObject.__init__(self, rdfid, tpe)

        self.AvailabilityEnabled: str | None = None
        self.ControllableQuantity: str | None = None
        self.GridStateAlterationCollection: GridStateAlterationCollection | None = None
        self.GridStateAlterationRemedialAction: GridStateAlterationRemedialAction | None = None
        self.GridStateAlterationSchedule: GridStateAlterationSchedule | None = None
        self.GridStateIntensitySchedule: GridStateIntensitySchedule | None = None
        self.PropertyReference: str | None = None
        self.RangeConstraint: RangeConstraint | None = None
        self.enabled: bool | None = None
        self.maximumPerDay: int | None = None
        self.minimumActivation: float | None = None
        self.normalEnabled: bool | None = None
        self.participationFactor: float | None = None
        self.timePerStage: float | None = None

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
