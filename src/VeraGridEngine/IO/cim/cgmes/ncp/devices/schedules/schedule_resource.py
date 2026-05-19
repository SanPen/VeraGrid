# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Dict
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
from VeraGridEngine.data_logger import DataLogger
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.power_system_resource import PowerSystemResource


class ScheduleResource(PowerSystemResource):
    """NCP CGMES extension class.

    :ivar rdfid: CIM RDF identifier inherited from the base class.
    :ivar tpe: CIM type name inherited from the base class.
    """
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='AreaDispatchableUnit', class_type='AreaDispatchableUnit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='GeneratingUnit', class_type='GeneratingUnit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='HydroPump', class_type='HydroPump', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='PowerBidSchedule', class_type='PowerBidSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SIS]),
        CgmesProperty(property_name='PowerElectronicsUnit', class_type='PowerElectronicsUnit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='PowerShiftKeySchedule', class_type='PowerShiftKeySchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SIS]),
        CgmesProperty(property_name='PrimaryEnergySource', class_type='EnergyType', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='ResourceOf', class_type='ScheduleResource', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='ScheduleResourceController', class_type='ScheduleResourceController', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='SchedulingArea', class_type='SchedulingArea', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='SubScheduleResource', class_type='ScheduleResource', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='p', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SSI]),
        CgmesProperty(property_name='participationFactor', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SSI]),
    )
    __slots__ = ('AreaDispatchableUnit', 'GeneratingUnit', 'HydroPump', 'PowerBidSchedule', 'PowerElectronicsUnit', 'PowerShiftKeySchedule', 'PrimaryEnergySource', 'ResourceOf', 'ScheduleResourceController', 'SchedulingArea', 'SubScheduleResource', 'p', 'participationFactor')

    def __init__(self, rdfid: str = '', tpe: str = '" + class_info.name + "') -> None:
        """Initialize the NCP object.

        :param rdfid: RDF identifier.
        :param tpe: CIM type name.
        :return: Nothing.
        """
        PowerSystemResource.__init__(self, rdfid, tpe)

        self.AreaDispatchableUnit: object | None = None
        self.GeneratingUnit: object | None = None
        self.HydroPump: object | None = None
        self.PowerBidSchedule: object | None = None
        self.PowerElectronicsUnit: object | None = None
        self.PowerShiftKeySchedule: object | None = None
        self.PrimaryEnergySource: object | None = None
        self.ResourceOf: object | None = None
        self.ScheduleResourceController: object | None = None
        self.SchedulingArea: object | None = None
        self.SubScheduleResource: object | None = None
        self.p: str | None = None
        self.participationFactor: str | None = None

    def parse_dict(self, data: Dict[str, str], logger: DataLogger) -> None:
        """Parse one NCP object property dictionary.

        :param data: Parsed XML property dictionary.
        :param logger: Data logger.
        :return: Nothing.
        """
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
