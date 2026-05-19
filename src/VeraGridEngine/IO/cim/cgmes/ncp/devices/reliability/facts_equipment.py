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
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.regulating_cond_eq import RegulatingCondEq


class FACTSEquipment(RegulatingCondEq):
    """NCP CGMES extension class.

    :ivar rdfid: CIM RDF identifier inherited from the base class.
    :ivar tpe: CIM type name inherited from the base class.
    """
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='LossCurve', class_type='LossCurve', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='maxC', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='maxL', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='minC', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='minL', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='q', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SSI]),
        CgmesProperty(property_name='ratedC', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='ratedI', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='ratedL', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='ratedU', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='slope', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
    )
    __slots__ = ('LossCurve', 'maxC', 'maxL', 'minC', 'minL', 'q', 'ratedC', 'ratedI', 'ratedL', 'ratedU', 'slope')

    def __init__(self, rdfid: str = '', tpe: str = '" + class_info.name + "') -> None:
        """Initialize the NCP object.

        :param rdfid: RDF identifier.
        :param tpe: CIM type name.
        :return: Nothing.
        """
        RegulatingCondEq.__init__(self, rdfid, tpe)

        self.LossCurve: object | None = None
        self.maxC: str | None = None
        self.maxL: str | None = None
        self.minC: str | None = None
        self.minL: str | None = None
        self.q: str | None = None
        self.ratedC: str | None = None
        self.ratedI: str | None = None
        self.ratedL: str | None = None
        self.ratedU: str | None = None
        self.slope: str | None = None

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
