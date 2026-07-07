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
from VeraGridEngine.IO.cim.cgmes.base import Base

if TYPE_CHECKING:
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.metadata.dataset import Dataset

class Dataset(Base):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='accessRights', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='accrualPeriodicity', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='alternativeVersionOf', class_type='Dataset', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='applicationSoftware', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='conformsTo', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='description', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='endDate', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='generatedAtTime', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='hasAlternativeVersion', class_type='Dataset', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='hasPart', class_type='Dataset', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='hasPreferredVersion', class_type='Dataset', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='hasVersion', class_type='Dataset', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='identifier', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='inSeries', class_type='Dataset', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='isPartOf', class_type='Dataset', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='isReferencedBy', class_type='Dataset', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='isReplacedBy', class_type='Dataset', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='isRequiredBy', class_type='Dataset', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='isVersionOf', class_type='Dataset', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='issued', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='keyword', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='license', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='nextVersion', class_type='Dataset', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='preferredVersion', class_type='Dataset', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='previousVersion', class_type='Dataset', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='processType', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='publisher', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='references', class_type='Dataset', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='replaces', class_type='Dataset', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='requires', class_type='Dataset', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='rights', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='rightsHolder', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='seriesMember', class_type='Dataset', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='source', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='spatial', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='startDate', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='temporalResolution', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='type', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='usedSettings', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='version', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='versionNotes', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
        CgmesProperty(property_name='wasGeneratedBy', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.OR]),
    )
    __slots__ = ('accessRights', 'accrualPeriodicity', 'alternativeVersionOf', 'applicationSoftware', 'conformsTo', 'description', 'endDate', 'generatedAtTime', 'hasAlternativeVersion', 'hasPart', 'hasPreferredVersion', 'hasVersion', 'identifier', 'inSeries', 'isPartOf', 'isReferencedBy', 'isReplacedBy', 'isRequiredBy', 'isVersionOf', 'issued', 'keyword', 'license', 'nextVersion', 'preferredVersion', 'previousVersion', 'processType', 'publisher', 'references', 'replaces', 'requires', 'rights', 'rightsHolder', 'seriesMember', 'source', 'spatial', 'startDate', 'temporalResolution', 'type', 'usedSettings', 'version', 'versionNotes', 'wasGeneratedBy')

    def __init__(self, rdfid: str = '', tpe: str = 'Dataset'):
        Base.__init__(self, rdfid, tpe)

        self.accessRights: str | None = None
        self.accrualPeriodicity: str | None = None
        self.alternativeVersionOf: Dataset | None = None
        self.applicationSoftware: str | None = None
        self.conformsTo: str | None = None
        self.description: str | None = None
        self.endDate: str | None = None
        self.generatedAtTime: str | None = None
        self.hasAlternativeVersion: Dataset | None = None
        self.hasPart: Dataset | None = None
        self.hasPreferredVersion: Dataset | None = None
        self.hasVersion: Dataset | None = None
        self.identifier: str | None = None
        self.inSeries: Dataset | None = None
        self.isPartOf: Dataset | None = None
        self.isReferencedBy: Dataset | None = None
        self.isReplacedBy: Dataset | None = None
        self.isRequiredBy: Dataset | None = None
        self.isVersionOf: Dataset | None = None
        self.issued: str | None = None
        self.keyword: str | None = None
        self.license: str | None = None
        self.nextVersion: Dataset | None = None
        self.preferredVersion: Dataset | None = None
        self.previousVersion: Dataset | None = None
        self.processType: str | None = None
        self.publisher: str | None = None
        self.references: Dataset | None = None
        self.replaces: Dataset | None = None
        self.requires: Dataset | None = None
        self.rights: str | None = None
        self.rightsHolder: str | None = None
        self.seriesMember: Dataset | None = None
        self.source: str | None = None
        self.spatial: str | None = None
        self.startDate: str | None = None
        self.temporalResolution: float | None = None
        self.type: str | None = None
        self.usedSettings: str | None = None
        self.version: str | None = None
        self.versionNotes: str | None = None
        self.wasGeneratedBy: str | None = None

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
