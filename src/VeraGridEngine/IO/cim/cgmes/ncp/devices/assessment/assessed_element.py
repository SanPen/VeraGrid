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
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.identified_object import IdentifiedObject

if TYPE_CHECKING:
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.assessed_element_schedule import AssessedElementSchedule
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.assessed_element_with_contingency import AssessedElementWithContingency
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.assessed_element_with_remedial_action import AssessedElementWithRemedialAction
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.conducting_equipment import ConductingEquipment
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.cross_border_relevance import CrossBorderRelevance
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.line import Line
    from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.operational_limit import OperationalLimit
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.power_transfer_corridor import PowerTransferCorridor
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.region import Region
    from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.system_operator import SystemOperator

class AssessedElement(IdentifiedObject):
    """NCP CGMES extension class."""
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='AssessedElementRegularSchedule', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='AssessedElementSchedule', class_type='AssessedElementSchedule', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='AssessedElementWithContingency', class_type='AssessedElementWithContingency', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='AssessedElementWithRemedialAction', class_type='AssessedElementWithRemedialAction', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='AssessedPowerTransferCorridor', class_type='PowerTransferCorridor', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='AssessedSystemOperator', class_type='SystemOperator', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='AvailabilityEnabled', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='ConductingEquipment', class_type='ConductingEquipment', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='CrossBorderRelevance', class_type='CrossBorderRelevance', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='DCTieCorridor', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='Line', class_type='Line', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='NativeRegion', class_type='Region', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='ObservableQuantity', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='OperationalLimit', class_type='OperationalLimit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='OverlappingZone', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='ScannedForRegion', class_type='Region', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='SecuredForRegion', class_type='Region', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='appointedMargin', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='coordinatedValidationAdjustment', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='coordinatedValidationAdjustmentJustification', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='criticalElement', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='criticalElementJustification', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='enabled', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='exclusionReason', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='flowReliabilityMargin', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='inBaseCase', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='individualValidationAdjustment', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='individualValidationAdjustmentJustification', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='individualValidationAdjustmentShare', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='insideCapacityMargin', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='isCombinableWithContingency', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='isCombinableWithRemedialAction', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='isCriticalForCapacityCalculation', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='maxFlow', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='maxMarginAdjustment', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='normalAppointedMargin', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='normalCoordinatedValidationAdjustment', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='normalCoordinatedValidationAdjustmentJustification', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='normalCriticalElementJustification', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='normalEnabled', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='normalIndividualValidationAdjustment', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='normalIndividualValidationAdjustmentJustification', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='normalIndividualValidationAdjustmentShare', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='normalMaxFlow', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='normalPositiveVirtualMargin', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='normalScannedThresholdMargin', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='normalTargetRemainingAvailableMarginJustification', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='outsideCapacityMargin', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='positiveVirtualMargin', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='scannedThresholdMargin', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='targetRemainingAvailableMargin', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
        CgmesProperty(property_name='targetRemainingAvailableMarginJustification', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='', profiles=[CgmesProfileType.NC, CgmesProfileType.AE, CgmesProfileType.IAM]),
    )
    __slots__ = ('AssessedElementRegularSchedule', 'AssessedElementSchedule', 'AssessedElementWithContingency', 'AssessedElementWithRemedialAction', 'AssessedPowerTransferCorridor', 'AssessedSystemOperator', 'AvailabilityEnabled', 'ConductingEquipment', 'CrossBorderRelevance', 'DCTieCorridor', 'Line', 'NativeRegion', 'ObservableQuantity', 'OperationalLimit', 'OverlappingZone', 'ScannedForRegion', 'SecuredForRegion', 'appointedMargin', 'coordinatedValidationAdjustment', 'coordinatedValidationAdjustmentJustification', 'criticalElement', 'criticalElementJustification', 'enabled', 'exclusionReason', 'flowReliabilityMargin', 'inBaseCase', 'individualValidationAdjustment', 'individualValidationAdjustmentJustification', 'individualValidationAdjustmentShare', 'insideCapacityMargin', 'isCombinableWithContingency', 'isCombinableWithRemedialAction', 'isCriticalForCapacityCalculation', 'maxFlow', 'maxMarginAdjustment', 'normalAppointedMargin', 'normalCoordinatedValidationAdjustment', 'normalCoordinatedValidationAdjustmentJustification', 'normalCriticalElementJustification', 'normalEnabled', 'normalIndividualValidationAdjustment', 'normalIndividualValidationAdjustmentJustification', 'normalIndividualValidationAdjustmentShare', 'normalMaxFlow', 'normalPositiveVirtualMargin', 'normalScannedThresholdMargin', 'normalTargetRemainingAvailableMarginJustification', 'outsideCapacityMargin', 'positiveVirtualMargin', 'scannedThresholdMargin', 'targetRemainingAvailableMargin', 'targetRemainingAvailableMarginJustification')

    def __init__(self, rdfid: str = '', tpe: str = 'AssessedElement'):
        IdentifiedObject.__init__(self, rdfid, tpe)

        self.AssessedElementRegularSchedule: str | None = None
        self.AssessedElementSchedule: AssessedElementSchedule | None = None
        self.AssessedElementWithContingency: AssessedElementWithContingency | None = None
        self.AssessedElementWithRemedialAction: AssessedElementWithRemedialAction | None = None
        self.AssessedPowerTransferCorridor: PowerTransferCorridor | None = None
        self.AssessedSystemOperator: SystemOperator | None = None
        self.AvailabilityEnabled: str | None = None
        self.ConductingEquipment: ConductingEquipment | None = None
        self.CrossBorderRelevance: CrossBorderRelevance | None = None
        self.DCTieCorridor: str | None = None
        self.Line: Line | None = None
        self.NativeRegion: Region | None = None
        self.ObservableQuantity: str | None = None
        self.OperationalLimit: OperationalLimit | None = None
        self.OverlappingZone: str | None = None
        self.ScannedForRegion: Region | None = None
        self.SecuredForRegion: Region | None = None
        self.appointedMargin: float | None = None
        self.coordinatedValidationAdjustment: float | None = None
        self.coordinatedValidationAdjustmentJustification: str | None = None
        self.criticalElement: str | None = None
        self.criticalElementJustification: str | None = None
        self.enabled: bool | None = None
        self.exclusionReason: str | None = None
        self.flowReliabilityMargin: float | None = None
        self.inBaseCase: bool | None = None
        self.individualValidationAdjustment: float | None = None
        self.individualValidationAdjustmentJustification: str | None = None
        self.individualValidationAdjustmentShare: float | None = None
        self.insideCapacityMargin: float | None = None
        self.isCombinableWithContingency: bool | None = None
        self.isCombinableWithRemedialAction: bool | None = None
        self.isCriticalForCapacityCalculation: bool | None = None
        self.maxFlow: float | None = None
        self.maxMarginAdjustment: float | None = None
        self.normalAppointedMargin: float | None = None
        self.normalCoordinatedValidationAdjustment: float | None = None
        self.normalCoordinatedValidationAdjustmentJustification: str | None = None
        self.normalCriticalElementJustification: str | None = None
        self.normalEnabled: bool | None = None
        self.normalIndividualValidationAdjustment: float | None = None
        self.normalIndividualValidationAdjustmentJustification: str | None = None
        self.normalIndividualValidationAdjustmentShare: float | None = None
        self.normalMaxFlow: float | None = None
        self.normalPositiveVirtualMargin: float | None = None
        self.normalScannedThresholdMargin: float | None = None
        self.normalTargetRemainingAvailableMarginJustification: str | None = None
        self.outsideCapacityMargin: float | None = None
        self.positiveVirtualMargin: float | None = None
        self.scannedThresholdMargin: float | None = None
        self.targetRemainingAvailableMargin: float | None = None
        self.targetRemainingAvailableMarginJustification: str | None = None

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
