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


class DCPole(PowerSystemResource):
    """NCP CGMES extension class.

    :ivar rdfid: CIM RDF identifier inherited from the base class.
    :ivar tpe: CIM type name inherited from the base class.
    """
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='AsymmetricMonopolarDCSystem', class_type='MonopolarDCSystem', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='DCBiPole', class_type='DCBiPole', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='DCConverterUnit', class_type='DCConverterUnit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='DCLine', class_type='DCLine', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='DCTieCorridor', class_type='DCTieCorridor', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='DirectCurrentPoleController', class_type='DirectCurrentPoleController', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='PowerSchedule', class_type='PowerSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.PS]),
        CgmesProperty(property_name='PowerShiftKeySchedule', class_type='PowerShiftKeySchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SIS]),
        CgmesProperty(property_name='maxEconomicP', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SSI]),
        CgmesProperty(property_name='minEconomicP', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SSI]),
        CgmesProperty(property_name='normalParticipationFactor', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.ER]),
        CgmesProperty(property_name='p', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SSI]),
        CgmesProperty(property_name='participationFactor', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.SSI]),
    )
    __slots__ = ('AsymmetricMonopolarDCSystem', 'DCBiPole', 'DCConverterUnit', 'DCLine', 'DCTieCorridor', 'DirectCurrentPoleController', 'PowerSchedule', 'PowerShiftKeySchedule', 'maxEconomicP', 'minEconomicP', 'normalParticipationFactor', 'p', 'participationFactor')

    def __init__(self, rdfid: str = '', tpe: str = '" + class_info.name + "') -> None:
        """Initialize the NCP object.

        :param rdfid: RDF identifier.
        :param tpe: CIM type name.
        :return: Nothing.
        """
        PowerSystemResource.__init__(self, rdfid, tpe)

        self.AsymmetricMonopolarDCSystem: object | None = None
        self.DCBiPole: object | None = None
        self.DCConverterUnit: object | None = None
        self.DCLine: object | None = None
        self.DCTieCorridor: object | None = None
        self.DirectCurrentPoleController: object | None = None
        self.PowerSchedule: object | None = None
        self.PowerShiftKeySchedule: object | None = None
        self.maxEconomicP: str | None = None
        self.minEconomicP: str | None = None
        self.normalParticipationFactor: str | None = None
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
