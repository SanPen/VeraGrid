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
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.acdc_converter_regular_schedule import ACDCConverterRegularSchedule


class VsConverterRegularSchedule(ACDCConverterRegularSchedule):
    """NCP CGMES extension class.

    :ivar rdfid: CIM RDF identifier inherited from the base class.
    :ivar tpe: CIM type name inherited from the base class.
    """
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='VsConverter', class_type='VsConverter', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.SHS]),
        CgmesProperty(property_name='droop', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SHS]),
        CgmesProperty(property_name='droopCompensation', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SHS]),
        CgmesProperty(property_name='pPccControl', class_type='VsPpccControlKind', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.SHS]),
        CgmesProperty(property_name='qPccControl', class_type='VsQpccControlKind', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.SHS]),
        CgmesProperty(property_name='qShare', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SHS]),
        CgmesProperty(property_name='targetPWMfactor', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SHS]),
        CgmesProperty(property_name='targetPhasePcc', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SHS]),
        CgmesProperty(property_name='targetPowerFactorPcc', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SHS]),
        CgmesProperty(property_name='targetQpcc', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SHS]),
        CgmesProperty(property_name='targetUpcc', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SHS]),
    )
    __slots__ = ('VsConverter', 'droop', 'droopCompensation', 'pPccControl', 'qPccControl', 'qShare', 'targetPWMfactor', 'targetPhasePcc', 'targetPowerFactorPcc', 'targetQpcc', 'targetUpcc')

    def __init__(self, rdfid: str = '', tpe: str = '" + class_info.name + "') -> None:
        """Initialize the NCP object.

        :param rdfid: RDF identifier.
        :param tpe: CIM type name.
        :return: Nothing.
        """
        ACDCConverterRegularSchedule.__init__(self, rdfid, tpe)

        self.VsConverter: object | None = None
        self.droop: str | None = None
        self.droopCompensation: str | None = None
        self.pPccControl: object | None = None
        self.qPccControl: object | None = None
        self.qShare: str | None = None
        self.targetPWMfactor: str | None = None
        self.targetPhasePcc: str | None = None
        self.targetPowerFactorPcc: str | None = None
        self.targetQpcc: str | None = None
        self.targetUpcc: str | None = None

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
