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


class RemedialActionCost(IdentifiedObject):
    """NCP CGMES extension class.

    :ivar rdfid: CIM RDF identifier inherited from the base class.
    :ivar tpe: CIM type name inherited from the base class.
    """
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='RemedialActionSchedule', class_type='RemedialActionSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS]),
        CgmesProperty(property_name='costAllocationTime', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS]),
        CgmesProperty(property_name='kind', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS]),
        CgmesProperty(property_name='mRID', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS]),
        CgmesProperty(property_name='operationalCost', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS]),
        CgmesProperty(property_name='opportunityCost', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS]),
        CgmesProperty(property_name='otherCost', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS]),
        CgmesProperty(property_name='processingFee', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS]),
        CgmesProperty(property_name='savedFuelCost', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS]),
        CgmesProperty(property_name='shutdownCost', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS]),
        CgmesProperty(property_name='startupCost', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.RAS]),
    )
    __slots__ = ('RemedialActionSchedule', 'costAllocationTime', 'kind', 'mRID', 'operationalCost', 'opportunityCost', 'otherCost', 'processingFee', 'savedFuelCost', 'shutdownCost', 'startupCost')

    def __init__(self, rdfid: str = '', tpe: str = '" + class_info.name + "') -> None:
        """Initialize the NCP object.

        :param rdfid: RDF identifier.
        :param tpe: CIM type name.
        :return: Nothing.
        """
        IdentifiedObject.__init__(self, rdfid, tpe)

        self.RemedialActionSchedule: object | None = None
        self.costAllocationTime: str | None = None
        self.kind: str | None = None
        self.mRID: str | None = None
        self.operationalCost: str | None = None
        self.opportunityCost: str | None = None
        self.otherCost: str | None = None
        self.processingFee: str | None = None
        self.savedFuelCost: str | None = None
        self.shutdownCost: str | None = None
        self.startupCost: str | None = None

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
