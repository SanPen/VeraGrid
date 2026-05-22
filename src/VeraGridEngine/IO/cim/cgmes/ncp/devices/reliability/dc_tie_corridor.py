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
from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.tie_corridor import TieCorridor


class DCTieCorridor(TieCorridor):
    """NCP CGMES extension class.

    :ivar rdfid: CIM RDF identifier inherited from the base class.
    :ivar tpe: CIM type name inherited from the base class.
    """
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='AssessedElement', class_type='AssessedElement', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.AE]),
        CgmesProperty(property_name='DCPole', class_type='DCPole', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='DirectCurrentMasterController', class_type='DirectCurrentMasterController', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='MustRunSchedule', class_type='MustRunSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS]),
        CgmesProperty(property_name='PowerSchedule', class_type='PowerSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PS]),
        CgmesProperty(property_name='SchedulingArea', class_type='SchedulingArea', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='maxRegulatingReserve', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='minRegulatingReserve', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='p', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.SSI]),
        CgmesProperty(property_name='q', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SSI]),
        CgmesProperty(property_name='rampingKind', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.ER]),
    )
    __slots__ = ('AssessedElement', 'DCPole', 'DirectCurrentMasterController', 'MustRunSchedule', 'PowerSchedule', 'SchedulingArea', 'maxRegulatingReserve', 'minRegulatingReserve', 'p', 'q', 'rampingKind')

    def __init__(self, rdfid: str = '', tpe: str = '" + class_info.name + "') -> None:
        """Initialize the NCP object.

        :param rdfid: RDF identifier.
        :param tpe: CIM type name.
        :return: Nothing.
        """
        TieCorridor.__init__(self, rdfid, tpe)

        self.AssessedElement: object | None = None
        self.DCPole: object | None = None
        self.DirectCurrentMasterController: object | None = None
        self.MustRunSchedule: object | None = None
        self.PowerSchedule: object | None = None
        self.SchedulingArea: object | None = None
        self.maxRegulatingReserve: str | None = None
        self.minRegulatingReserve: str | None = None
        self.p: str | None = None
        self.q: str | None = None
        self.rampingKind: str | None = None

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
