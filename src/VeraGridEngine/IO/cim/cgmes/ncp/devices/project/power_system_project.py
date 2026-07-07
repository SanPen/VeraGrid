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
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.identified_object import IdentifiedObject


class PowerSystemProject(IdentifiedObject):
    """NCP CGMES extension class.

    :ivar rdfid: CIM RDF identifier inherited from the base class.
    :ivar tpe: CIM type name inherited from the base class.
    """
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='AlternativeProject', class_type='PowerSystemProject', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PSP]),
        CgmesProperty(property_name='AvailabilitySchedule', class_type='AvailabilitySchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PSP]),
        CgmesProperty(property_name='DependentOnProject', class_type='PowerSystemProject', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PSP]),
        CgmesProperty(property_name='DifferenceModel', class_type='DifferenceModel', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PSP]),
        CgmesProperty(property_name='PriorityProject', class_type='PowerSystemProject', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PSP]),
        CgmesProperty(property_name='Project', class_type='PowerSystemProject', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PSP]),
        CgmesProperty(property_name='ProjectGroup', class_type='PowerSystemProjectGroup', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PSP]),
        CgmesProperty(property_name='ShadowProject', class_type='PowerSystemProject', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PSP]),
        CgmesProperty(property_name='SilhouetteProject', class_type='PowerSystemProject', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PSP]),
        CgmesProperty(property_name='cancelled', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PSP]),
        CgmesProperty(property_name='commissioned', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PSP]),
        CgmesProperty(property_name='committed', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PSP]),
        CgmesProperty(property_name='inBuild', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PSP]),
        CgmesProperty(property_name='inPlan', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PSP]),
        CgmesProperty(property_name='officialExpectedCommissioning', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.PSP]),
        CgmesProperty(property_name='priority', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.PSP]),
    )
    __slots__ = ('AlternativeProject', 'AvailabilitySchedule', 'DependentOnProject', 'DifferenceModel', 'PriorityProject', 'Project', 'ProjectGroup', 'ShadowProject', 'SilhouetteProject', 'cancelled', 'commissioned', 'committed', 'inBuild', 'inPlan', 'officialExpectedCommissioning', 'priority')

    def __init__(self, rdfid: str = '', tpe: str = '" + class_info.name + "') -> None:
        """Initialize the NCP object.

        :param rdfid: RDF identifier.
        :param tpe: CIM type name.
        :return: Nothing.
        """
        IdentifiedObject.__init__(self, rdfid, tpe)

        self.AlternativeProject: object | None = None
        self.AvailabilitySchedule: object | None = None
        self.DependentOnProject: object | None = None
        self.DifferenceModel: object | None = None
        self.PriorityProject: object | None = None
        self.Project: object | None = None
        self.ProjectGroup: object | None = None
        self.ShadowProject: object | None = None
        self.SilhouetteProject: object | None = None
        self.cancelled: str | None = None
        self.commissioned: str | None = None
        self.committed: str | None = None
        self.inBuild: str | None = None
        self.inPlan: str | None = None
        self.officialExpectedCommissioning: str | None = None
        self.priority: str | None = None

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
