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
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.base_irregular_time_series import BaseIrregularTimeSeries


class GenericEnablingSchedule(BaseIrregularTimeSeries):
    """NCP CGMES extension class.

    :ivar rdfid: CIM RDF identifier inherited from the base class.
    :ivar tpe: CIM type name inherited from the base class.
    """
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='AssessedElementWithContingency', class_type='AssessedElementWithContingency', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='AssessedElementWithRemedialAction', class_type='AssessedElementWithRemedialAction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='AutomationFunction', class_type='AutomationFunction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='ContingencyWithRemedialAction', class_type='ContingencyWithRemedialAction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='CrossBorderRelevance', class_type='CrossBorderRelevance', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='EnablingTimePoint', class_type='EnablingTimePoint', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', mandatory=True, profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='FunctionBlock', class_type='FunctionBlock', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='PowerTransferCorridor', class_type='PowerTransferCorridor', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
        CgmesProperty(property_name='RemedialActionDependency', class_type='RemedialActionDependency', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.SIS]),
    )
    __slots__ = ('AssessedElementWithContingency', 'AssessedElementWithRemedialAction', 'AutomationFunction', 'ContingencyWithRemedialAction', 'CrossBorderRelevance', 'EnablingTimePoint', 'FunctionBlock', 'PowerTransferCorridor', 'RemedialActionDependency')

    def __init__(self, rdfid: str = '', tpe: str = '" + class_info.name + "') -> None:
        """Initialize the NCP object.

        :param rdfid: RDF identifier.
        :param tpe: CIM type name.
        :return: Nothing.
        """
        BaseIrregularTimeSeries.__init__(self, rdfid, tpe)

        self.AssessedElementWithContingency: object | None = None
        self.AssessedElementWithRemedialAction: object | None = None
        self.AutomationFunction: object | None = None
        self.ContingencyWithRemedialAction: object | None = None
        self.CrossBorderRelevance: object | None = None
        self.EnablingTimePoint: object | None = None
        self.FunctionBlock: object | None = None
        self.PowerTransferCorridor: object | None = None
        self.RemedialActionDependency: object | None = None

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
