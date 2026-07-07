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


class CurrentDroopOverride(IdentifiedObject):
    """NCP CGMES extension class.

    :ivar rdfid: CIM RDF identifier inherited from the base class.
    :ivar tpe: CIM type name inherited from the base class.
    """
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='SSSCController', class_type='SSSCController', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='droopCapacitive', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='droopInductive', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='enabled', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.SSI]),
        CgmesProperty(property_name='mRID', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='offsetCapacitiveI', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='offsetInductiveI', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.ER]),
        CgmesProperty(property_name='targetValueCapacitiveI', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.SSI]),
        CgmesProperty(property_name='targetValueInductiveI', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.SSI]),
    )
    __slots__ = ('SSSCController', 'droopCapacitive', 'droopInductive', 'enabled', 'mRID', 'offsetCapacitiveI', 'offsetInductiveI', 'targetValueCapacitiveI', 'targetValueInductiveI')

    def __init__(self, rdfid: str = '', tpe: str = '" + class_info.name + "') -> None:
        """Initialize the NCP object.

        :param rdfid: RDF identifier.
        :param tpe: CIM type name.
        :return: Nothing.
        """
        IdentifiedObject.__init__(self, rdfid, tpe)

        self.SSSCController: object | None = None
        self.droopCapacitive: str | None = None
        self.droopInductive: str | None = None
        self.enabled: str | None = None
        self.mRID: str | None = None
        self.offsetCapacitiveI: str | None = None
        self.offsetInductiveI: str | None = None
        self.targetValueCapacitiveI: str | None = None
        self.targetValueInductiveI: str | None = None

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
