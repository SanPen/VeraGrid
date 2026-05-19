# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Dict, Tuple, Type, TypeAlias

from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.acdc_converter_action import ACDCConverterAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.acdc_converter_controller import ACDCConverterController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.acdc_converter_regular_schedule import ACDCConverterRegularSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.acdc_time_point import ACDCTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.ac_emulation_control_function import ACEmulationControlFunction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.ac_point_of_common_coupling import ACPointOfCommonCoupling
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.ac_tie_corridor import ACTieCorridor
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.active_power_control_function import ActivePowerControlFunction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.active_power_limit_schedule import ActivePowerLimitSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.active_power_limit_time_point import ActivePowerLimitTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.metadata.activity import Activity
from VeraGridEngine.IO.cim.cgmes.ncp.devices.metadata.agent import Agent
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.ambient_temperature_dependency_curve import AmbientTemperatureDependencyCurve
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.apparent_power_limit_schedule import ApparentPowerLimitSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.apparent_power_limit_time_point import ApparentPowerLimitTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.monitoring.area_border_terminal import AreaBorderTerminal
from VeraGridEngine.IO.cim.cgmes.ncp.devices.market.area_dispatchable_unit import AreaDispatchableUnit
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.area_interchange_controller import AreaInterchangeController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.assessed_element import AssessedElement
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.assessed_element_regular_schedule import AssessedElementRegularSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.assessed_element_regular_time_point import AssessedElementRegularTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.assessed_element_schedule import AssessedElementSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.assessed_element_time_point import AssessedElementTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.assessed_element_with_contingency import AssessedElementWithContingency
from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.assessed_element_with_remedial_action import AssessedElementWithRemedialAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.metadata.assessment import Assessment
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.asynchronous_machine_regular_schedule import AsynchronousMachineRegularSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.asynchronous_machine_schedule import AsynchronousMachineSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.asynchronous_machine_time_point import AsynchronousMachineTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.automation_block_group import AutomationBlockGroup
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.automation_function import AutomationFunction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.operations.availability_container import AvailabilityContainer
from VeraGridEngine.IO.cim.cgmes.ncp.devices.operations.availability_enabled import AvailabilityEnabled
from VeraGridEngine.IO.cim.cgmes.ncp.devices.operations.availability_equipment import AvailabilityEquipment
from VeraGridEngine.IO.cim.cgmes.ncp.devices.operations.availability_exceptional_limit import AvailabilityExceptionalLimit
from VeraGridEngine.IO.cim.cgmes.ncp.devices.operations.availability_group import AvailabilityGroup
from VeraGridEngine.IO.cim.cgmes.ncp.devices.operations.availability_power_system_function import AvailabilityPowerSystemFunction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.availability_remedial_action import AvailabilityRemedialAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.availability_remedial_action_scheme import AvailabilityRemedialActionScheme
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.availability_schedule import AvailabilitySchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.availability_time_point import AvailabilityTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.operations.base_case_current_limit import BaseCaseCurrentLimit
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.base_case_current_limit_schedule import BaseCaseCurrentLimitSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.base_case_current_limit_time_point import BaseCaseCurrentLimitTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.results.base_case_power_flow_result import BaseCasePowerFlowResult
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.base_irregular_time_series import BaseIrregularTimeSeries
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.base_overload_limit_curve import BaseOverloadLimitCurve
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.base_regular_interval_schedule import BaseRegularIntervalSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.base_time_series import BaseTimeSeries
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.battery_unit_action import BatteryUnitAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.battery_unit_schedule import BatteryUnitSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.battery_unit_time_point import BatteryUnitTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.bidding_zone import BiddingZone
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.bidding_zone_action import BiddingZoneAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.bidding_zone_border import BiddingZoneBorder
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.bipolar_dc_system import BipolarDCSystem
from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.boundary_frame import BoundaryFrame
from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.calculation_based_impact_assessment_matrix import CalculationBasedImpactAssessmentMatrix
from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.capacity_calculation_region import CapacityCalculationRegion
from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.circuit import Circuit
from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.circuit_share import CircuitShare
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.closed_distribution_system_operator import ClosedDistributionSystemOperator
from VeraGridEngine.IO.cim.cgmes.ncp.devices.metadata.collection import Collection
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.compensator_controller import CompensatorController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.metadata.concept_scheme import ConceptScheme
from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.connecting_impact_assessment_matrix import ConnectingImpactAssessmentMatrix
from VeraGridEngine.IO.cim.cgmes.ncp.devices.contingency.contingency import Contingency
from VeraGridEngine.IO.cim.cgmes.ncp.devices.contingency.contingency_area import ContingencyArea
from VeraGridEngine.IO.cim.cgmes.ncp.devices.contingency.contingency_element import ContingencyElement
from VeraGridEngine.IO.cim.cgmes.ncp.devices.contingency.contingency_equipment import ContingencyEquipment
from VeraGridEngine.IO.cim.cgmes.ncp.devices.contingency.contingency_power_flow_result import ContingencyPowerFlowResult
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.contingency_schedule import ContingencySchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.contingency_time_point import ContingencyTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.contingency.contingency_with_remedial_action import ContingencyWithRemedialAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.control_area_regular_schedule import ControlAreaRegularSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.control_area_schedule import ControlAreaSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.control_area_time_point import ControlAreaTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.control_function_block import ControlFunctionBlock
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.control_function_block_action import ControlFunctionBlockAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.sensitivity.controllable_quantity import ControllableQuantity
from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.coordinated_capacity_calculator import CoordinatedCapacityCalculator
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.countertrade_remedial_action import CountertradeRemedialAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.countertrade_schedule_action import CountertradeScheduleAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.cross_border_relevance import CrossBorderRelevance
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.cs_converter_regular_schedule import CsConverterRegularSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.cs_converter_schedule import CsConverterSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.cs_converter_time_point import CsConverterTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.current_control_function import CurrentControlFunction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.current_droop_control_function import CurrentDroopControlFunction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.current_droop_override import CurrentDroopOverride
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.current_limit_schedule import CurrentLimitSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.current_limit_time_point import CurrentLimitTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_bi_pole import DCBiPole
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_bypass_switch import DCBypassSwitch
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_commutation_switch import DCCommutationSwitch
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_converter_paralleling_switch import DCConverterParallelingSwitch
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_current_control_function import DCCurrentControlFunction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_earth_return_transfer_switch import DCEarthReturnTransferSwitch
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_harmonic_filter import DCHarmonicFilter
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_high_speed_switch import DCHighSpeedSwitch
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_line_paralleling_switch import DCLineParallelingSwitch
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_metalic_return_switch import DCMetalicReturnSwitch
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_neutral_bus_grounding_switch import DCNeutralBusGroundingSwitch
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_neutral_bus_switch import DCNeutralBusSwitch
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_point_of_common_coupling import DCPointOfCommonCoupling
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_pole import DCPole
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_smoothing_reactor import DCSmoothingReactor
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_smoothing_reactor_arrester import DCSmoothingReactorArrester
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_substation import DCSubstation
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_substation_bipole import DCSubstationBipole
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_substation_pole import DCSubstationPole
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_system import DCSystem
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_tie_corridor import DCTieCorridor
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.dc_voltage_control_function import DCVoltageControlFunction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.metadata.dataset import Dataset
from VeraGridEngine.IO.cim.cgmes.ncp.devices.project.difference_model import DifferenceModel
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.direct_current_bipole_controller import DirectCurrentBipoleController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.direct_current_circuit import DirectCurrentCircuit
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.direct_current_equipment_controller import DirectCurrentEquipmentController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.direct_current_master_controller import DirectCurrentMasterController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.direct_current_pole_controller import DirectCurrentPoleController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.direct_current_substation_bipole_controller import DirectCurrentSubstationBipoleController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.direct_current_substation_controller import DirectCurrentSubstationController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.direct_current_substation_pole_controller import DirectCurrentSubstationPoleController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.direct_current_system_operator import DirectCurrentSystemOperator
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.distribution_system_operator import DistributionSystemOperator
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.duration_overload_limit_curve import DurationOverloadLimitCurve
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.edge_control_area import EdgeControlArea
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.edge_scheduling_area import EdgeSchedulingArea
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.electrical_charging_unit import ElectricalChargingUnit
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.enabling_time_point import EnablingTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.energy_alignment_coordinator import EnergyAlignmentCoordinator
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.energy_block_component import EnergyBlockComponent
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.energy_block_order import EnergyBlockOrder
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.energy_component import EnergyComponent
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.energy_connection_regular_schedule import EnergyConnectionRegularSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.energy_connection_schedule import EnergyConnectionSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.energy_connection_time_point import EnergyConnectionTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.energy_coordination_region import EnergyCoordinationRegion
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.energy_exchange_point import EnergyExchangePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.energy_group import EnergyGroup
from VeraGridEngine.IO.cim.cgmes.ncp.devices.market.energy_source_modification import EnergySourceModification
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.energy_source_reference import EnergySourceReference
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.energy_type import EnergyType
from VeraGridEngine.IO.cim.cgmes.ncp.devices.metadata.entity import Entity
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.equipment_controller import EquipmentController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.equipment_controller_action import EquipmentControllerAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.market.equivalent_generating_unit import EquivalentGeneratingUnit
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.equivalent_injection_action import EquivalentInjectionAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.equivalent_injection_regular_schedule import EquivalentInjectionRegularSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.equivalent_injection_schedule import EquivalentInjectionSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.equivalent_injection_time_point import EquivalentInjectionTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.equivalent_power_electronics_unit import EquivalentPowerElectronicsUnit
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.equivalent_power_plant import EquivalentPowerPlant
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.event_schedule import EventSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.event_time_point import EventTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.contingency.exceptional_contingency import ExceptionalContingency
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.exceptional_power_transfer_corridor import ExceptionalPowerTransferCorridor
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.external_network_injection_action import ExternalNetworkInjectionAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.external_network_injection_regular_schedule import ExternalNetworkInjectionRegularSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.external_network_injection_schedule import ExternalNetworkInjectionSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.external_network_injection_time_point import ExternalNetworkInjectionTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.facts_equipment import FACTSEquipment
from VeraGridEngine.IO.cim.cgmes.ncp.devices.grid_disturbance.fault_cause import FaultCause
from VeraGridEngine.IO.cim.cgmes.ncp.devices.grid_disturbance.fault_outage import FaultOutage
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.flexible_energy_unit import FlexibleEnergyUnit
from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.frame import Frame
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.frequency_control_function import FrequencyControlFunction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.frequency_monitoring_terminal import FrequencyMonitoringTerminal
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.fuel_storage import FuelStorage
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.fuel_storage_regular_schedule import FuelStorageRegularSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.fuel_storage_schedule import FuelStorageSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.fuel_storage_time_point import FuelStorageTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.function_block import FunctionBlock
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.function_input_variable import FunctionInputVariable
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.function_output_variable import FunctionOutputVariable
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.gate import Gate
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.gate_input_pin import GateInputPin
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.generating_unit_schedule import GeneratingUnitSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.generating_unit_time_point import GeneratingUnitTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.generic_available_schedule import GenericAvailableSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.generic_enabling_schedule import GenericEnablingSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.generic_sequence_schedule import GenericSequenceSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.generic_value_schedule import GenericValueSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.generic_value_time_point import GenericValueTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.geometry import Geometry
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.geothermal_generating_unit import GeothermalGeneratingUnit
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.grid_connection_point import GridConnectionPoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.grid_disturbance.grid_disturbance import GridDisturbance
from VeraGridEngine.IO.cim.cgmes.ncp.devices.operations.grid_state_alteration import GridStateAlteration
from VeraGridEngine.IO.cim.cgmes.ncp.devices.operations.grid_state_alteration_collection import GridStateAlterationCollection
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.grid_state_alteration_remedial_action import GridStateAlterationRemedialAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.grid_state_alteration_schedule import GridStateAlterationSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.grid_state_alteration_time_point import GridStateAlterationTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.grid_state_intensity_schedule import GridStateIntensitySchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.hour_pattern import HourPattern
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.hour_period import HourPeriod
from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.impact_assessment_matrix import ImpactAssessmentMatrix
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.impedance_control_function import ImpedanceControlFunction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.in_service_action import InServiceAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.in_service_regular_schedule import InServiceRegularSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.in_service_schedule import InServiceSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.in_service_time_point import InServiceTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.operations.infeed_limit import InfeedLimit
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.infeed_limit_schedule import InfeedLimitSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.infeed_limit_time_point import InfeedLimitTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.operations.infeed_terminal import InfeedTerminal
from VeraGridEngine.IO.cim.cgmes.ncp.devices.monitoring.influence_area import InfluenceArea
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.injection_controller import InjectionController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.installation import Installation
from VeraGridEngine.IO.cim.cgmes.ncp.devices.grid_disturbance.interruption import Interruption
from VeraGridEngine.IO.cim.cgmes.ncp.devices.operations.intertemporal_property_range import IntertemporalPropertyRange
from VeraGridEngine.IO.cim.cgmes.ncp.devices.metadata.license_document import LicenseDocument
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.limit_dependency_curve import LimitDependencyCurve
from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.line_circuit import LineCircuit
from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.list_based_impact_assessment_matrix import ListBasedImpactAssessmentMatrix
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.load_action import LoadAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.load_frequency_control_area import LoadFrequencyControlArea
from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.load_frequency_control_block import LoadFrequencyControlBlock
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.load_frequency_control_operator import LoadFrequencyControlOperator
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.loss_curve import LossCurve
from VeraGridEngine.IO.cim.cgmes.ncp.devices.core.measurement_calculator import MeasurementCalculator
from VeraGridEngine.IO.cim.cgmes.ncp.devices.core.measurement_calculator_input import MeasurementCalculatorInput
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.mobile_electrical_unit import MobileElectricalUnit
from VeraGridEngine.IO.cim.cgmes.ncp.devices.metadata.model import Model
from VeraGridEngine.IO.cim.cgmes.ncp.devices.metadata.modeling import Modeling
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.modular_static_synchronous_series_compensator import ModularStaticSynchronousSeriesCompensator
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.monitoring_area import MonitoringArea
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.monopolar_dc_system import MonopolarDCSystem
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.must_run_schedule import MustRunSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.must_run_time_point import MustRunTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.metadata.name import Name
from VeraGridEngine.IO.cim.cgmes.ncp.devices.metadata.name_type import NameType
from VeraGridEngine.IO.cim.cgmes.ncp.devices.metadata.naming_authority import NamingAuthority
from VeraGridEngine.IO.cim.cgmes.ncp.devices.metadata.object_type import ObjectType
from VeraGridEngine.IO.cim.cgmes.ncp.devices.monitoring.observability_area import ObservabilityArea
from VeraGridEngine.IO.cim.cgmes.ncp.devices.sensitivity.observable_quantity import ObservableQuantity
from VeraGridEngine.IO.cim.cgmes.ncp.devices.contingency.ordinary_contingency import OrdinaryContingency
from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.ordinary_power_transfer_corridor import OrdinaryPowerTransferCorridor
from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.organisation import Organisation
from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.organisation_role import OrganisationRole
from VeraGridEngine.IO.cim.cgmes.ncp.devices.contingency.out_of_range_contingency import OutOfRangeContingency
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.outage_coordination_region import OutageCoordinationRegion
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.outage_coordinator import OutageCoordinator
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.outage_planning_agent import OutagePlanningAgent
from VeraGridEngine.IO.cim.cgmes.ncp.devices.assessment.outcome_value import OutcomeValue
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.overlapping_zone import OverlappingZone
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.owner_remedial_action_assessment import OwnerRemedialActionAssessment
from VeraGridEngine.IO.cim.cgmes.ncp.devices.market.ptc_active_power_support import PTCActivePowerSupport
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.participation_factor_time_point import ParticipationFactorTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.phase_control_function import PhaseControlFunction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.contingency.pin_contingency import PinContingency
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.pin_dc_terminal import PinDCTerminal
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.pin_equipment import PinEquipment
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.pin_equipment_tripping import PinEquipmentTripping
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.pin_gate import PinGate
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.pin_measurement import PinMeasurement
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.pin_operational_limit import PinOperationalLimit
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.pin_power_transfer_corridor import PinPowerTransferCorridor
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.pin_terminal import PinTerminal
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.plant import Plant
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.point_of_common_coupling import PointOfCommonCoupling
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_bid_dependency import PowerBidDependency
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_bid_schedule import PowerBidSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_bid_schedule_time_point import PowerBidScheduleTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.power_capacity import PowerCapacity
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.power_electrical_chemical_unit import PowerElectricalChemicalUnit
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.power_electronics_connection_action import PowerElectronicsConnectionAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.power_electronics_connection_controller import PowerElectronicsConnectionController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.power_electronics_marine_unit import PowerElectronicsMarineUnit
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.power_electronics_unit_controller import PowerElectronicsUnitController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.power_factor_control_function import PowerFactorControlFunction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.results.power_flow_result import PowerFlowResult
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.power_frequency_controller import PowerFrequencyController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.power_plant_controller import PowerPlantController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.power_remedial_action import PowerRemedialAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_remedial_action_schedule import PowerRemedialActionSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_remedial_action_time_point import PowerRemedialActionTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_schedule import PowerSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.power_schedule_action import PowerScheduleAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_shift_key_distribution import PowerShiftKeyDistribution
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_shift_key_schedule import PowerShiftKeySchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_shift_key_strategy import PowerShiftKeyStrategy
from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.power_system_organisation_role import PowerSystemOrganisationRole
from VeraGridEngine.IO.cim.cgmes.ncp.devices.project.power_system_project import PowerSystemProject
from VeraGridEngine.IO.cim.cgmes.ncp.devices.project.power_system_project_group import PowerSystemProjectGroup
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.power_time_point import PowerTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.power_transfer_corridor import PowerTransferCorridor
from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.power_transformer_circuit import PowerTransformerCircuit
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.property_reference import PropertyReference
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.proportional_energy_component import ProportionalEnergyComponent
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.proposing_remedial_action_schedule_share import ProposingRemedialActionScheduleShare
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.qualitative_remedial_action_impact import QualitativeRemedialActionImpact
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.quantitative_remedial_action_impact import QuantitativeRemedialActionImpact
from VeraGridEngine.IO.cim.cgmes.ncp.devices.metadata.quantity_value import QuantityValue
from VeraGridEngine.IO.cim.cgmes.ncp.devices.operations.range_constraint import RangeConstraint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.reactive_power_control_function import ReactivePowerControlFunction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.recovery_overload_limit_curve import RecoveryOverloadLimitCurve
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.redispatch_remedial_action import RedispatchRemedialAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.redispatch_schedule_action import RedispatchScheduleAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.region import Region
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.regulating_control_action import RegulatingControlAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.regulating_control_regular_schedule import RegulatingControlRegularSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.regulating_control_schedule import RegulatingControlSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.regulating_control_time_point import RegulatingControlTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action import RemedialAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_applied import RemedialActionApplied
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_cost import RemedialActionCost
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_dependency import RemedialActionDependency
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_group import RemedialActionGroup
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.remedial_action_group_schedule import RemedialActionGroupSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.remedial_action_group_time_point import RemedialActionGroupTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_impact import RemedialActionImpact
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_outcome_value import RemedialActionOutcomeValue
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_schedule import RemedialActionSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_schedule_dependency import RemedialActionScheduleDependency
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.remedial_action_schedule_group import RemedialActionScheduleGroup
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_schedule_outcome_value import RemedialActionScheduleOutcomeValue
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_schedule_response import RemedialActionScheduleResponse
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.remedial_action_scheme import RemedialActionScheme
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.remedial_action_scheme_schedule import RemedialActionSchemeSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.remedial_action_scheme_time_point import RemedialActionSchemeTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.reservoir_regular_schedule import ReservoirRegularSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.reservoir_schedule import ReservoirSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.reservoir_time_point import ReservoirTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.metadata.rights_statement import RightsStatement
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.rotating_machine_action import RotatingMachineAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.rotating_machine_controller import RotatingMachineController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.sssc_controller import SSSCController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.sssc_simulation_settings import SSSCSimulationSettings
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.schedule_resource import ScheduleResource
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.schedule_resource_controller import ScheduleResourceController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.scheduling_area import SchedulingArea
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.scheduling_area_exchange_point import SchedulingAreaExchangePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.scheme_remedial_action import SchemeRemedialAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.secondary_substation import SecondarySubstation
from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.security_coordinator import SecurityCoordinator
from VeraGridEngine.IO.cim.cgmes.ncp.devices.metadata.semantic_asset import SemanticAsset
from VeraGridEngine.IO.cim.cgmes.ncp.devices.sensitivity.sensitivity_area import SensitivityArea
from VeraGridEngine.IO.cim.cgmes.ncp.devices.sensitivity.sensitivity_factor import SensitivityFactor
from VeraGridEngine.IO.cim.cgmes.ncp.devices.sensitivity.sensitivity_matrix import SensitivityMatrix
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.sequence_time_point import SequenceTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.set_point_action import SetPointAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.core.shunt_compensator_modification import ShuntCompensatorModification
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.shunt_compensator_schedule import ShuntCompensatorSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.shunt_compensator_time_point import ShuntCompensatorTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.solar_radiation_dependency_curve import SolarRadiationDependencyCurve
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.stage import Stage
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.stage_trigger import StageTrigger
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.stage_trigger_schedule import StageTriggerSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.stage_trigger_time_point import StageTriggerTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.operations.static_property_range import StaticPropertyRange
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.static_synchronous_compensator import StaticSynchronousCompensator
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.static_synchronous_series_compensator import StaticSynchronousSeriesCompensator
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.static_var_compensator import StaticVarCompensator
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.static_var_compensator_action import StaticVarCompensatorAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.static_var_compensator_schedule import StaticVarCompensatorSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.static_var_compensator_time_point import StaticVarCompensatorTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.sub_control_area import SubControlArea
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.sub_scheduling_area import SubSchedulingArea
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.substation_controller import SubstationController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.metadata.supported_profile_collection import SupportedProfileCollection
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.switch_regular_schedule import SwitchRegularSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.switch_schedule import SwitchSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.switch_time_point import SwitchTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.synchronous_area import SynchronousArea
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.synchronous_machine_regular_schedule import SynchronousMachineRegularSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.synchronous_machine_schedule import SynchronousMachineSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.synchronous_machine_time_point import SynchronousMachineTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.system_control import SystemControl
from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.system_operation_coordinator import SystemOperationCoordinator
from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.system_operator import SystemOperator
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.tcsc_compensation_point import TCSCCompensationPoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.tcsc_controller import TCSCController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.tap_changer_control_regular_schedule import TapChangerControlRegularSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.tap_changer_control_schedule import TapChangerControlSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.tap_changer_controller import TapChangerController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.tap_position_action import TapPositionAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.tap_regular_schedule import TapRegularSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.tap_schedule import TapSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.tap_schedule_time_point import TapScheduleTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.thyristor_controlled_series_compensator import ThyristorControlledSeriesCompensator
from VeraGridEngine.IO.cim.cgmes.ncp.devices.geography.tie_corridor import TieCorridor
from VeraGridEngine.IO.cim.cgmes.ncp.devices.actions.topology_action import TopologyAction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.organisation.transmission_system_operator import TransmissionSystemOperator
from VeraGridEngine.IO.cim.cgmes.ncp.devices.remedial.trigger_condition import TriggerCondition
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.unified_power_flow_controller import UnifiedPowerFlowController
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.unit_cost_schedule import UnitCostSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.unit_cost_time_point import UnitCostTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.metadata.verification import Verification
from VeraGridEngine.IO.cim.cgmes.ncp.devices.operations.voltage_angle_limit import VoltageAngleLimit
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.voltage_angle_schedule import VoltageAngleSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.voltage_angle_time_point import VoltageAngleTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.voltage_control_function import VoltageControlFunction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.reliability.voltage_injection_control_function import VoltageInjectionControlFunction
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.voltage_limit_schedule import VoltageLimitSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.voltage_limit_time_point import VoltageLimitTimePoint
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.vs_converter_regular_schedule import VsConverterRegularSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.vs_converter_schedule import VsConverterSchedule
from VeraGridEngine.IO.cim.cgmes.ncp.devices.schedules.vs_converter_time_point import VsConverterTimePoint


NCP_ASSETS: TypeAlias = (
    ACDCConverterAction |
    ACDCConverterController |
    ACDCConverterRegularSchedule |
    ACDCTimePoint |
    ACEmulationControlFunction |
    ACPointOfCommonCoupling |
    ACTieCorridor |
    ActivePowerControlFunction |
    ActivePowerLimitSchedule |
    ActivePowerLimitTimePoint |
    Activity |
    Agent |
    AmbientTemperatureDependencyCurve |
    ApparentPowerLimitSchedule |
    ApparentPowerLimitTimePoint |
    AreaBorderTerminal |
    AreaDispatchableUnit |
    AreaInterchangeController |
    AssessedElement |
    AssessedElementRegularSchedule |
    AssessedElementRegularTimePoint |
    AssessedElementSchedule |
    AssessedElementTimePoint |
    AssessedElementWithContingency |
    AssessedElementWithRemedialAction |
    Assessment |
    AsynchronousMachineRegularSchedule |
    AsynchronousMachineSchedule |
    AsynchronousMachineTimePoint |
    AutomationBlockGroup |
    AutomationFunction |
    AvailabilityContainer |
    AvailabilityEnabled |
    AvailabilityEquipment |
    AvailabilityExceptionalLimit |
    AvailabilityGroup |
    AvailabilityPowerSystemFunction |
    AvailabilityRemedialAction |
    AvailabilityRemedialActionScheme |
    AvailabilitySchedule |
    AvailabilityTimePoint |
    BaseCaseCurrentLimit |
    BaseCaseCurrentLimitSchedule |
    BaseCaseCurrentLimitTimePoint |
    BaseCasePowerFlowResult |
    BaseIrregularTimeSeries |
    BaseOverloadLimitCurve |
    BaseRegularIntervalSchedule |
    BaseTimeSeries |
    BatteryUnitAction |
    BatteryUnitSchedule |
    BatteryUnitTimePoint |
    BiddingZone |
    BiddingZoneAction |
    BiddingZoneBorder |
    BipolarDCSystem |
    BoundaryFrame |
    CalculationBasedImpactAssessmentMatrix |
    CapacityCalculationRegion |
    Circuit |
    CircuitShare |
    ClosedDistributionSystemOperator |
    Collection |
    CompensatorController |
    ConceptScheme |
    ConnectingImpactAssessmentMatrix |
    Contingency |
    ContingencyArea |
    ContingencyElement |
    ContingencyEquipment |
    ContingencyPowerFlowResult |
    ContingencySchedule |
    ContingencyTimePoint |
    ContingencyWithRemedialAction |
    ControlAreaRegularSchedule |
    ControlAreaSchedule |
    ControlAreaTimePoint |
    ControlFunctionBlock |
    ControlFunctionBlockAction |
    ControllableQuantity |
    CoordinatedCapacityCalculator |
    CountertradeRemedialAction |
    CountertradeScheduleAction |
    CrossBorderRelevance |
    CsConverterRegularSchedule |
    CsConverterSchedule |
    CsConverterTimePoint |
    CurrentControlFunction |
    CurrentDroopControlFunction |
    CurrentDroopOverride |
    CurrentLimitSchedule |
    CurrentLimitTimePoint |
    DCBiPole |
    DCBypassSwitch |
    DCCommutationSwitch |
    DCConverterParallelingSwitch |
    DCCurrentControlFunction |
    DCEarthReturnTransferSwitch |
    DCHarmonicFilter |
    DCHighSpeedSwitch |
    DCLineParallelingSwitch |
    DCMetalicReturnSwitch |
    DCNeutralBusGroundingSwitch |
    DCNeutralBusSwitch |
    DCPointOfCommonCoupling |
    DCPole |
    DCSmoothingReactor |
    DCSmoothingReactorArrester |
    DCSubstation |
    DCSubstationBipole |
    DCSubstationPole |
    DCSystem |
    DCTieCorridor |
    DCVoltageControlFunction |
    Dataset |
    DifferenceModel |
    DirectCurrentBipoleController |
    DirectCurrentCircuit |
    DirectCurrentEquipmentController |
    DirectCurrentMasterController |
    DirectCurrentPoleController |
    DirectCurrentSubstationBipoleController |
    DirectCurrentSubstationController |
    DirectCurrentSubstationPoleController |
    DirectCurrentSystemOperator |
    DistributionSystemOperator |
    DurationOverloadLimitCurve |
    EdgeControlArea |
    EdgeSchedulingArea |
    ElectricalChargingUnit |
    EnablingTimePoint |
    EnergyAlignmentCoordinator |
    EnergyBlockComponent |
    EnergyBlockOrder |
    EnergyComponent |
    EnergyConnectionRegularSchedule |
    EnergyConnectionSchedule |
    EnergyConnectionTimePoint |
    EnergyCoordinationRegion |
    EnergyExchangePoint |
    EnergyGroup |
    EnergySourceModification |
    EnergySourceReference |
    EnergyType |
    Entity |
    EquipmentController |
    EquipmentControllerAction |
    EquivalentGeneratingUnit |
    EquivalentInjectionAction |
    EquivalentInjectionRegularSchedule |
    EquivalentInjectionSchedule |
    EquivalentInjectionTimePoint |
    EquivalentPowerElectronicsUnit |
    EquivalentPowerPlant |
    EventSchedule |
    EventTimePoint |
    ExceptionalContingency |
    ExceptionalPowerTransferCorridor |
    ExternalNetworkInjectionAction |
    ExternalNetworkInjectionRegularSchedule |
    ExternalNetworkInjectionSchedule |
    ExternalNetworkInjectionTimePoint |
    FACTSEquipment |
    FaultCause |
    FaultOutage |
    FlexibleEnergyUnit |
    Frame |
    FrequencyControlFunction |
    FrequencyMonitoringTerminal |
    FuelStorage |
    FuelStorageRegularSchedule |
    FuelStorageSchedule |
    FuelStorageTimePoint |
    FunctionBlock |
    FunctionInputVariable |
    FunctionOutputVariable |
    Gate |
    GateInputPin |
    GeneratingUnitSchedule |
    GeneratingUnitTimePoint |
    GenericAvailableSchedule |
    GenericEnablingSchedule |
    GenericSequenceSchedule |
    GenericValueSchedule |
    GenericValueTimePoint |
    Geometry |
    GeothermalGeneratingUnit |
    GridConnectionPoint |
    GridDisturbance |
    GridStateAlteration |
    GridStateAlterationCollection |
    GridStateAlterationRemedialAction |
    GridStateAlterationSchedule |
    GridStateAlterationTimePoint |
    GridStateIntensitySchedule |
    HourPattern |
    HourPeriod |
    ImpactAssessmentMatrix |
    ImpedanceControlFunction |
    InServiceAction |
    InServiceRegularSchedule |
    InServiceSchedule |
    InServiceTimePoint |
    InfeedLimit |
    InfeedLimitSchedule |
    InfeedLimitTimePoint |
    InfeedTerminal |
    InfluenceArea |
    InjectionController |
    Installation |
    Interruption |
    IntertemporalPropertyRange |
    LicenseDocument |
    LimitDependencyCurve |
    LineCircuit |
    ListBasedImpactAssessmentMatrix |
    LoadAction |
    LoadFrequencyControlArea |
    LoadFrequencyControlBlock |
    LoadFrequencyControlOperator |
    LossCurve |
    MeasurementCalculator |
    MeasurementCalculatorInput |
    MobileElectricalUnit |
    Model |
    Modeling |
    ModularStaticSynchronousSeriesCompensator |
    MonitoringArea |
    MonopolarDCSystem |
    MustRunSchedule |
    MustRunTimePoint |
    Name |
    NameType |
    NamingAuthority |
    ObjectType |
    ObservabilityArea |
    ObservableQuantity |
    OrdinaryContingency |
    OrdinaryPowerTransferCorridor |
    Organisation |
    OrganisationRole |
    OutOfRangeContingency |
    OutageCoordinationRegion |
    OutageCoordinator |
    OutagePlanningAgent |
    OutcomeValue |
    OverlappingZone |
    OwnerRemedialActionAssessment |
    PTCActivePowerSupport |
    ParticipationFactorTimePoint |
    PhaseControlFunction |
    PinContingency |
    PinDCTerminal |
    PinEquipment |
    PinEquipmentTripping |
    PinGate |
    PinMeasurement |
    PinOperationalLimit |
    PinPowerTransferCorridor |
    PinTerminal |
    Plant |
    PointOfCommonCoupling |
    PowerBidDependency |
    PowerBidSchedule |
    PowerBidScheduleTimePoint |
    PowerCapacity |
    PowerElectricalChemicalUnit |
    PowerElectronicsConnectionAction |
    PowerElectronicsConnectionController |
    PowerElectronicsMarineUnit |
    PowerElectronicsUnitController |
    PowerFactorControlFunction |
    PowerFlowResult |
    PowerFrequencyController |
    PowerPlantController |
    PowerRemedialAction |
    PowerRemedialActionSchedule |
    PowerRemedialActionTimePoint |
    PowerSchedule |
    PowerScheduleAction |
    PowerShiftKeyDistribution |
    PowerShiftKeySchedule |
    PowerShiftKeyStrategy |
    PowerSystemOrganisationRole |
    PowerSystemProject |
    PowerSystemProjectGroup |
    PowerTimePoint |
    PowerTransferCorridor |
    PowerTransformerCircuit |
    PropertyReference |
    ProportionalEnergyComponent |
    ProposingRemedialActionScheduleShare |
    QualitativeRemedialActionImpact |
    QuantitativeRemedialActionImpact |
    QuantityValue |
    RangeConstraint |
    ReactivePowerControlFunction |
    RecoveryOverloadLimitCurve |
    RedispatchRemedialAction |
    RedispatchScheduleAction |
    Region |
    RegulatingControlAction |
    RegulatingControlRegularSchedule |
    RegulatingControlSchedule |
    RegulatingControlTimePoint |
    RemedialAction |
    RemedialActionApplied |
    RemedialActionCost |
    RemedialActionDependency |
    RemedialActionGroup |
    RemedialActionGroupSchedule |
    RemedialActionGroupTimePoint |
    RemedialActionImpact |
    RemedialActionOutcomeValue |
    RemedialActionSchedule |
    RemedialActionScheduleDependency |
    RemedialActionScheduleGroup |
    RemedialActionScheduleOutcomeValue |
    RemedialActionScheduleResponse |
    RemedialActionScheme |
    RemedialActionSchemeSchedule |
    RemedialActionSchemeTimePoint |
    ReservoirRegularSchedule |
    ReservoirSchedule |
    ReservoirTimePoint |
    RightsStatement |
    RotatingMachineAction |
    RotatingMachineController |
    SSSCController |
    SSSCSimulationSettings |
    ScheduleResource |
    ScheduleResourceController |
    SchedulingArea |
    SchedulingAreaExchangePoint |
    SchemeRemedialAction |
    SecondarySubstation |
    SecurityCoordinator |
    SemanticAsset |
    SensitivityArea |
    SensitivityFactor |
    SensitivityMatrix |
    SequenceTimePoint |
    SetPointAction |
    ShuntCompensatorModification |
    ShuntCompensatorSchedule |
    ShuntCompensatorTimePoint |
    SolarRadiationDependencyCurve |
    Stage |
    StageTrigger |
    StageTriggerSchedule |
    StageTriggerTimePoint |
    StaticPropertyRange |
    StaticSynchronousCompensator |
    StaticSynchronousSeriesCompensator |
    StaticVarCompensator |
    StaticVarCompensatorAction |
    StaticVarCompensatorSchedule |
    StaticVarCompensatorTimePoint |
    SubControlArea |
    SubSchedulingArea |
    SubstationController |
    SupportedProfileCollection |
    SwitchRegularSchedule |
    SwitchSchedule |
    SwitchTimePoint |
    SynchronousArea |
    SynchronousMachineRegularSchedule |
    SynchronousMachineSchedule |
    SynchronousMachineTimePoint |
    SystemControl |
    SystemOperationCoordinator |
    SystemOperator |
    TCSCCompensationPoint |
    TCSCController |
    TapChangerControlRegularSchedule |
    TapChangerControlSchedule |
    TapChangerController |
    TapPositionAction |
    TapRegularSchedule |
    TapSchedule |
    TapScheduleTimePoint |
    ThyristorControlledSeriesCompensator |
    TieCorridor |
    TopologyAction |
    TransmissionSystemOperator |
    TriggerCondition |
    UnifiedPowerFlowController |
    UnitCostSchedule |
    UnitCostTimePoint |
    Verification |
    VoltageAngleLimit |
    VoltageAngleSchedule |
    VoltageAngleTimePoint |
    VoltageControlFunction |
    VoltageInjectionControlFunction |
    VoltageLimitSchedule |
    VoltageLimitTimePoint |
    VsConverterRegularSchedule |
    VsConverterSchedule |
    VsConverterTimePoint 
)


class NcpAssets:
    """Container exposing NCP class and inverse-association dictionaries."""

    def __init__(self) -> None:
        """Initialize NCP assets.

        :return: Nothing.
        """
        self.class_dict: Dict[str, Type] = {
            'ACDCConverterAction': ACDCConverterAction,
            'ACDCConverterController': ACDCConverterController,
            'ACDCConverterRegularSchedule': ACDCConverterRegularSchedule,
            'ACDCTimePoint': ACDCTimePoint,
            'ACEmulationControlFunction': ACEmulationControlFunction,
            'ACPointOfCommonCoupling': ACPointOfCommonCoupling,
            'ACTieCorridor': ACTieCorridor,
            'ActivePowerControlFunction': ActivePowerControlFunction,
            'ActivePowerLimitSchedule': ActivePowerLimitSchedule,
            'ActivePowerLimitTimePoint': ActivePowerLimitTimePoint,
            'Activity': Activity,
            'Agent': Agent,
            'AmbientTemperatureDependencyCurve': AmbientTemperatureDependencyCurve,
            'ApparentPowerLimitSchedule': ApparentPowerLimitSchedule,
            'ApparentPowerLimitTimePoint': ApparentPowerLimitTimePoint,
            'AreaBorderTerminal': AreaBorderTerminal,
            'AreaDispatchableUnit': AreaDispatchableUnit,
            'AreaInterchangeController': AreaInterchangeController,
            'AssessedElement': AssessedElement,
            'AssessedElementRegularSchedule': AssessedElementRegularSchedule,
            'AssessedElementRegularTimePoint': AssessedElementRegularTimePoint,
            'AssessedElementSchedule': AssessedElementSchedule,
            'AssessedElementTimePoint': AssessedElementTimePoint,
            'AssessedElementWithContingency': AssessedElementWithContingency,
            'AssessedElementWithRemedialAction': AssessedElementWithRemedialAction,
            'Assessment': Assessment,
            'AsynchronousMachineRegularSchedule': AsynchronousMachineRegularSchedule,
            'AsynchronousMachineSchedule': AsynchronousMachineSchedule,
            'AsynchronousMachineTimePoint': AsynchronousMachineTimePoint,
            'AutomationBlockGroup': AutomationBlockGroup,
            'AutomationFunction': AutomationFunction,
            'AvailabilityContainer': AvailabilityContainer,
            'AvailabilityEnabled': AvailabilityEnabled,
            'AvailabilityEquipment': AvailabilityEquipment,
            'AvailabilityExceptionalLimit': AvailabilityExceptionalLimit,
            'AvailabilityGroup': AvailabilityGroup,
            'AvailabilityPowerSystemFunction': AvailabilityPowerSystemFunction,
            'AvailabilityRemedialAction': AvailabilityRemedialAction,
            'AvailabilityRemedialActionScheme': AvailabilityRemedialActionScheme,
            'AvailabilitySchedule': AvailabilitySchedule,
            'AvailabilityTimePoint': AvailabilityTimePoint,
            'BaseCaseCurrentLimit': BaseCaseCurrentLimit,
            'BaseCaseCurrentLimitSchedule': BaseCaseCurrentLimitSchedule,
            'BaseCaseCurrentLimitTimePoint': BaseCaseCurrentLimitTimePoint,
            'BaseCasePowerFlowResult': BaseCasePowerFlowResult,
            'BaseIrregularTimeSeries': BaseIrregularTimeSeries,
            'BaseOverloadLimitCurve': BaseOverloadLimitCurve,
            'BaseRegularIntervalSchedule': BaseRegularIntervalSchedule,
            'BaseTimeSeries': BaseTimeSeries,
            'BatteryUnitAction': BatteryUnitAction,
            'BatteryUnitSchedule': BatteryUnitSchedule,
            'BatteryUnitTimePoint': BatteryUnitTimePoint,
            'BiddingZone': BiddingZone,
            'BiddingZoneAction': BiddingZoneAction,
            'BiddingZoneBorder': BiddingZoneBorder,
            'BipolarDCSystem': BipolarDCSystem,
            'BoundaryFrame': BoundaryFrame,
            'CalculationBasedImpactAssessmentMatrix': CalculationBasedImpactAssessmentMatrix,
            'CapacityCalculationRegion': CapacityCalculationRegion,
            'Circuit': Circuit,
            'CircuitShare': CircuitShare,
            'ClosedDistributionSystemOperator': ClosedDistributionSystemOperator,
            'Collection': Collection,
            'CompensatorController': CompensatorController,
            'ConceptScheme': ConceptScheme,
            'ConnectingImpactAssessmentMatrix': ConnectingImpactAssessmentMatrix,
            'Contingency': Contingency,
            'ContingencyArea': ContingencyArea,
            'ContingencyElement': ContingencyElement,
            'ContingencyEquipment': ContingencyEquipment,
            'ContingencyPowerFlowResult': ContingencyPowerFlowResult,
            'ContingencySchedule': ContingencySchedule,
            'ContingencyTimePoint': ContingencyTimePoint,
            'ContingencyWithRemedialAction': ContingencyWithRemedialAction,
            'ControlAreaRegularSchedule': ControlAreaRegularSchedule,
            'ControlAreaSchedule': ControlAreaSchedule,
            'ControlAreaTimePoint': ControlAreaTimePoint,
            'ControlFunctionBlock': ControlFunctionBlock,
            'ControlFunctionBlockAction': ControlFunctionBlockAction,
            'ControllableQuantity': ControllableQuantity,
            'CoordinatedCapacityCalculator': CoordinatedCapacityCalculator,
            'CountertradeRemedialAction': CountertradeRemedialAction,
            'CountertradeScheduleAction': CountertradeScheduleAction,
            'CrossBorderRelevance': CrossBorderRelevance,
            'CsConverterRegularSchedule': CsConverterRegularSchedule,
            'CsConverterSchedule': CsConverterSchedule,
            'CsConverterTimePoint': CsConverterTimePoint,
            'CurrentControlFunction': CurrentControlFunction,
            'CurrentDroopControlFunction': CurrentDroopControlFunction,
            'CurrentDroopOverride': CurrentDroopOverride,
            'CurrentLimitSchedule': CurrentLimitSchedule,
            'CurrentLimitTimePoint': CurrentLimitTimePoint,
            'DCBiPole': DCBiPole,
            'DCBypassSwitch': DCBypassSwitch,
            'DCCommutationSwitch': DCCommutationSwitch,
            'DCConverterParallelingSwitch': DCConverterParallelingSwitch,
            'DCCurrentControlFunction': DCCurrentControlFunction,
            'DCEarthReturnTransferSwitch': DCEarthReturnTransferSwitch,
            'DCHarmonicFilter': DCHarmonicFilter,
            'DCHighSpeedSwitch': DCHighSpeedSwitch,
            'DCLineParallelingSwitch': DCLineParallelingSwitch,
            'DCMetalicReturnSwitch': DCMetalicReturnSwitch,
            'DCNeutralBusGroundingSwitch': DCNeutralBusGroundingSwitch,
            'DCNeutralBusSwitch': DCNeutralBusSwitch,
            'DCPointOfCommonCoupling': DCPointOfCommonCoupling,
            'DCPole': DCPole,
            'DCSmoothingReactor': DCSmoothingReactor,
            'DCSmoothingReactorArrester': DCSmoothingReactorArrester,
            'DCSubstation': DCSubstation,
            'DCSubstationBipole': DCSubstationBipole,
            'DCSubstationPole': DCSubstationPole,
            'DCSystem': DCSystem,
            'DCTieCorridor': DCTieCorridor,
            'DCVoltageControlFunction': DCVoltageControlFunction,
            'Dataset': Dataset,
            'DifferenceModel': DifferenceModel,
            'DirectCurrentBipoleController': DirectCurrentBipoleController,
            'DirectCurrentCircuit': DirectCurrentCircuit,
            'DirectCurrentEquipmentController': DirectCurrentEquipmentController,
            'DirectCurrentMasterController': DirectCurrentMasterController,
            'DirectCurrentPoleController': DirectCurrentPoleController,
            'DirectCurrentSubstationBipoleController': DirectCurrentSubstationBipoleController,
            'DirectCurrentSubstationController': DirectCurrentSubstationController,
            'DirectCurrentSubstationPoleController': DirectCurrentSubstationPoleController,
            'DirectCurrentSystemOperator': DirectCurrentSystemOperator,
            'DistributionSystemOperator': DistributionSystemOperator,
            'DurationOverloadLimitCurve': DurationOverloadLimitCurve,
            'EdgeControlArea': EdgeControlArea,
            'EdgeSchedulingArea': EdgeSchedulingArea,
            'ElectricalChargingUnit': ElectricalChargingUnit,
            'EnablingTimePoint': EnablingTimePoint,
            'EnergyAlignmentCoordinator': EnergyAlignmentCoordinator,
            'EnergyBlockComponent': EnergyBlockComponent,
            'EnergyBlockOrder': EnergyBlockOrder,
            'EnergyComponent': EnergyComponent,
            'EnergyConnectionRegularSchedule': EnergyConnectionRegularSchedule,
            'EnergyConnectionSchedule': EnergyConnectionSchedule,
            'EnergyConnectionTimePoint': EnergyConnectionTimePoint,
            'EnergyCoordinationRegion': EnergyCoordinationRegion,
            'EnergyExchangePoint': EnergyExchangePoint,
            'EnergyGroup': EnergyGroup,
            'EnergySourceModification': EnergySourceModification,
            'EnergySourceReference': EnergySourceReference,
            'EnergyType': EnergyType,
            'Entity': Entity,
            'EquipmentController': EquipmentController,
            'EquipmentControllerAction': EquipmentControllerAction,
            'EquivalentGeneratingUnit': EquivalentGeneratingUnit,
            'EquivalentInjectionAction': EquivalentInjectionAction,
            'EquivalentInjectionRegularSchedule': EquivalentInjectionRegularSchedule,
            'EquivalentInjectionSchedule': EquivalentInjectionSchedule,
            'EquivalentInjectionTimePoint': EquivalentInjectionTimePoint,
            'EquivalentPowerElectronicsUnit': EquivalentPowerElectronicsUnit,
            'EquivalentPowerPlant': EquivalentPowerPlant,
            'EventSchedule': EventSchedule,
            'EventTimePoint': EventTimePoint,
            'ExceptionalContingency': ExceptionalContingency,
            'ExceptionalPowerTransferCorridor': ExceptionalPowerTransferCorridor,
            'ExternalNetworkInjectionAction': ExternalNetworkInjectionAction,
            'ExternalNetworkInjectionRegularSchedule': ExternalNetworkInjectionRegularSchedule,
            'ExternalNetworkInjectionSchedule': ExternalNetworkInjectionSchedule,
            'ExternalNetworkInjectionTimePoint': ExternalNetworkInjectionTimePoint,
            'FACTSEquipment': FACTSEquipment,
            'FaultCause': FaultCause,
            'FaultOutage': FaultOutage,
            'FlexibleEnergyUnit': FlexibleEnergyUnit,
            'Frame': Frame,
            'FrequencyControlFunction': FrequencyControlFunction,
            'FrequencyMonitoringTerminal': FrequencyMonitoringTerminal,
            'FuelStorage': FuelStorage,
            'FuelStorageRegularSchedule': FuelStorageRegularSchedule,
            'FuelStorageSchedule': FuelStorageSchedule,
            'FuelStorageTimePoint': FuelStorageTimePoint,
            'FunctionBlock': FunctionBlock,
            'FunctionInputVariable': FunctionInputVariable,
            'FunctionOutputVariable': FunctionOutputVariable,
            'Gate': Gate,
            'GateInputPin': GateInputPin,
            'GeneratingUnitSchedule': GeneratingUnitSchedule,
            'GeneratingUnitTimePoint': GeneratingUnitTimePoint,
            'GenericAvailableSchedule': GenericAvailableSchedule,
            'GenericEnablingSchedule': GenericEnablingSchedule,
            'GenericSequenceSchedule': GenericSequenceSchedule,
            'GenericValueSchedule': GenericValueSchedule,
            'GenericValueTimePoint': GenericValueTimePoint,
            'Geometry': Geometry,
            'GeothermalGeneratingUnit': GeothermalGeneratingUnit,
            'GridConnectionPoint': GridConnectionPoint,
            'GridDisturbance': GridDisturbance,
            'GridStateAlteration': GridStateAlteration,
            'GridStateAlterationCollection': GridStateAlterationCollection,
            'GridStateAlterationRemedialAction': GridStateAlterationRemedialAction,
            'GridStateAlterationSchedule': GridStateAlterationSchedule,
            'GridStateAlterationTimePoint': GridStateAlterationTimePoint,
            'GridStateIntensitySchedule': GridStateIntensitySchedule,
            'HourPattern': HourPattern,
            'HourPeriod': HourPeriod,
            'ImpactAssessmentMatrix': ImpactAssessmentMatrix,
            'ImpedanceControlFunction': ImpedanceControlFunction,
            'InServiceAction': InServiceAction,
            'InServiceRegularSchedule': InServiceRegularSchedule,
            'InServiceSchedule': InServiceSchedule,
            'InServiceTimePoint': InServiceTimePoint,
            'InfeedLimit': InfeedLimit,
            'InfeedLimitSchedule': InfeedLimitSchedule,
            'InfeedLimitTimePoint': InfeedLimitTimePoint,
            'InfeedTerminal': InfeedTerminal,
            'InfluenceArea': InfluenceArea,
            'InjectionController': InjectionController,
            'Installation': Installation,
            'Interruption': Interruption,
            'IntertemporalPropertyRange': IntertemporalPropertyRange,
            'LicenseDocument': LicenseDocument,
            'LimitDependencyCurve': LimitDependencyCurve,
            'LineCircuit': LineCircuit,
            'ListBasedImpactAssessmentMatrix': ListBasedImpactAssessmentMatrix,
            'LoadAction': LoadAction,
            'LoadFrequencyControlArea': LoadFrequencyControlArea,
            'LoadFrequencyControlBlock': LoadFrequencyControlBlock,
            'LoadFrequencyControlOperator': LoadFrequencyControlOperator,
            'LossCurve': LossCurve,
            'MeasurementCalculator': MeasurementCalculator,
            'MeasurementCalculatorInput': MeasurementCalculatorInput,
            'MobileElectricalUnit': MobileElectricalUnit,
            'Model': Model,
            'Modeling': Modeling,
            'ModularStaticSynchronousSeriesCompensator': ModularStaticSynchronousSeriesCompensator,
            'MonitoringArea': MonitoringArea,
            'MonopolarDCSystem': MonopolarDCSystem,
            'MustRunSchedule': MustRunSchedule,
            'MustRunTimePoint': MustRunTimePoint,
            'Name': Name,
            'NameType': NameType,
            'NamingAuthority': NamingAuthority,
            'ObjectType': ObjectType,
            'ObservabilityArea': ObservabilityArea,
            'ObservableQuantity': ObservableQuantity,
            'OrdinaryContingency': OrdinaryContingency,
            'OrdinaryPowerTransferCorridor': OrdinaryPowerTransferCorridor,
            'Organisation': Organisation,
            'OrganisationRole': OrganisationRole,
            'OutOfRangeContingency': OutOfRangeContingency,
            'OutageCoordinationRegion': OutageCoordinationRegion,
            'OutageCoordinator': OutageCoordinator,
            'OutagePlanningAgent': OutagePlanningAgent,
            'OutcomeValue': OutcomeValue,
            'OverlappingZone': OverlappingZone,
            'OwnerRemedialActionAssessment': OwnerRemedialActionAssessment,
            'PTCActivePowerSupport': PTCActivePowerSupport,
            'ParticipationFactorTimePoint': ParticipationFactorTimePoint,
            'PhaseControlFunction': PhaseControlFunction,
            'PinContingency': PinContingency,
            'PinDCTerminal': PinDCTerminal,
            'PinEquipment': PinEquipment,
            'PinEquipmentTripping': PinEquipmentTripping,
            'PinGate': PinGate,
            'PinMeasurement': PinMeasurement,
            'PinOperationalLimit': PinOperationalLimit,
            'PinPowerTransferCorridor': PinPowerTransferCorridor,
            'PinTerminal': PinTerminal,
            'Plant': Plant,
            'PointOfCommonCoupling': PointOfCommonCoupling,
            'PowerBidDependency': PowerBidDependency,
            'PowerBidSchedule': PowerBidSchedule,
            'PowerBidScheduleTimePoint': PowerBidScheduleTimePoint,
            'PowerCapacity': PowerCapacity,
            'PowerElectricalChemicalUnit': PowerElectricalChemicalUnit,
            'PowerElectronicsConnectionAction': PowerElectronicsConnectionAction,
            'PowerElectronicsConnectionController': PowerElectronicsConnectionController,
            'PowerElectronicsMarineUnit': PowerElectronicsMarineUnit,
            'PowerElectronicsUnitController': PowerElectronicsUnitController,
            'PowerFactorControlFunction': PowerFactorControlFunction,
            'PowerFlowResult': PowerFlowResult,
            'PowerFrequencyController': PowerFrequencyController,
            'PowerPlantController': PowerPlantController,
            'PowerRemedialAction': PowerRemedialAction,
            'PowerRemedialActionSchedule': PowerRemedialActionSchedule,
            'PowerRemedialActionTimePoint': PowerRemedialActionTimePoint,
            'PowerSchedule': PowerSchedule,
            'PowerScheduleAction': PowerScheduleAction,
            'PowerShiftKeyDistribution': PowerShiftKeyDistribution,
            'PowerShiftKeySchedule': PowerShiftKeySchedule,
            'PowerShiftKeyStrategy': PowerShiftKeyStrategy,
            'PowerSystemOrganisationRole': PowerSystemOrganisationRole,
            'PowerSystemProject': PowerSystemProject,
            'PowerSystemProjectGroup': PowerSystemProjectGroup,
            'PowerTimePoint': PowerTimePoint,
            'PowerTransferCorridor': PowerTransferCorridor,
            'PowerTransformerCircuit': PowerTransformerCircuit,
            'PropertyReference': PropertyReference,
            'ProportionalEnergyComponent': ProportionalEnergyComponent,
            'ProposingRemedialActionScheduleShare': ProposingRemedialActionScheduleShare,
            'QualitativeRemedialActionImpact': QualitativeRemedialActionImpact,
            'QuantitativeRemedialActionImpact': QuantitativeRemedialActionImpact,
            'QuantityValue': QuantityValue,
            'RangeConstraint': RangeConstraint,
            'ReactivePowerControlFunction': ReactivePowerControlFunction,
            'RecoveryOverloadLimitCurve': RecoveryOverloadLimitCurve,
            'RedispatchRemedialAction': RedispatchRemedialAction,
            'RedispatchScheduleAction': RedispatchScheduleAction,
            'Region': Region,
            'RegulatingControlAction': RegulatingControlAction,
            'RegulatingControlRegularSchedule': RegulatingControlRegularSchedule,
            'RegulatingControlSchedule': RegulatingControlSchedule,
            'RegulatingControlTimePoint': RegulatingControlTimePoint,
            'RemedialAction': RemedialAction,
            'RemedialActionApplied': RemedialActionApplied,
            'RemedialActionCost': RemedialActionCost,
            'RemedialActionDependency': RemedialActionDependency,
            'RemedialActionGroup': RemedialActionGroup,
            'RemedialActionGroupSchedule': RemedialActionGroupSchedule,
            'RemedialActionGroupTimePoint': RemedialActionGroupTimePoint,
            'RemedialActionImpact': RemedialActionImpact,
            'RemedialActionOutcomeValue': RemedialActionOutcomeValue,
            'RemedialActionSchedule': RemedialActionSchedule,
            'RemedialActionScheduleDependency': RemedialActionScheduleDependency,
            'RemedialActionScheduleGroup': RemedialActionScheduleGroup,
            'RemedialActionScheduleOutcomeValue': RemedialActionScheduleOutcomeValue,
            'RemedialActionScheduleResponse': RemedialActionScheduleResponse,
            'RemedialActionScheme': RemedialActionScheme,
            'RemedialActionSchemeSchedule': RemedialActionSchemeSchedule,
            'RemedialActionSchemeTimePoint': RemedialActionSchemeTimePoint,
            'ReservoirRegularSchedule': ReservoirRegularSchedule,
            'ReservoirSchedule': ReservoirSchedule,
            'ReservoirTimePoint': ReservoirTimePoint,
            'RightsStatement': RightsStatement,
            'RotatingMachineAction': RotatingMachineAction,
            'RotatingMachineController': RotatingMachineController,
            'SSSCController': SSSCController,
            'SSSCSimulationSettings': SSSCSimulationSettings,
            'ScheduleResource': ScheduleResource,
            'ScheduleResourceController': ScheduleResourceController,
            'SchedulingArea': SchedulingArea,
            'SchedulingAreaExchangePoint': SchedulingAreaExchangePoint,
            'SchemeRemedialAction': SchemeRemedialAction,
            'SecondarySubstation': SecondarySubstation,
            'SecurityCoordinator': SecurityCoordinator,
            'SemanticAsset': SemanticAsset,
            'SensitivityArea': SensitivityArea,
            'SensitivityFactor': SensitivityFactor,
            'SensitivityMatrix': SensitivityMatrix,
            'SequenceTimePoint': SequenceTimePoint,
            'SetPointAction': SetPointAction,
            'ShuntCompensatorModification': ShuntCompensatorModification,
            'ShuntCompensatorSchedule': ShuntCompensatorSchedule,
            'ShuntCompensatorTimePoint': ShuntCompensatorTimePoint,
            'SolarRadiationDependencyCurve': SolarRadiationDependencyCurve,
            'Stage': Stage,
            'StageTrigger': StageTrigger,
            'StageTriggerSchedule': StageTriggerSchedule,
            'StageTriggerTimePoint': StageTriggerTimePoint,
            'StaticPropertyRange': StaticPropertyRange,
            'StaticSynchronousCompensator': StaticSynchronousCompensator,
            'StaticSynchronousSeriesCompensator': StaticSynchronousSeriesCompensator,
            'StaticVarCompensator': StaticVarCompensator,
            'StaticVarCompensatorAction': StaticVarCompensatorAction,
            'StaticVarCompensatorSchedule': StaticVarCompensatorSchedule,
            'StaticVarCompensatorTimePoint': StaticVarCompensatorTimePoint,
            'SubControlArea': SubControlArea,
            'SubSchedulingArea': SubSchedulingArea,
            'SubstationController': SubstationController,
            'SupportedProfileCollection': SupportedProfileCollection,
            'SwitchRegularSchedule': SwitchRegularSchedule,
            'SwitchSchedule': SwitchSchedule,
            'SwitchTimePoint': SwitchTimePoint,
            'SynchronousArea': SynchronousArea,
            'SynchronousMachineRegularSchedule': SynchronousMachineRegularSchedule,
            'SynchronousMachineSchedule': SynchronousMachineSchedule,
            'SynchronousMachineTimePoint': SynchronousMachineTimePoint,
            'SystemControl': SystemControl,
            'SystemOperationCoordinator': SystemOperationCoordinator,
            'SystemOperator': SystemOperator,
            'TCSCCompensationPoint': TCSCCompensationPoint,
            'TCSCController': TCSCController,
            'TapChangerControlRegularSchedule': TapChangerControlRegularSchedule,
            'TapChangerControlSchedule': TapChangerControlSchedule,
            'TapChangerController': TapChangerController,
            'TapPositionAction': TapPositionAction,
            'TapRegularSchedule': TapRegularSchedule,
            'TapSchedule': TapSchedule,
            'TapScheduleTimePoint': TapScheduleTimePoint,
            'ThyristorControlledSeriesCompensator': ThyristorControlledSeriesCompensator,
            'TieCorridor': TieCorridor,
            'TopologyAction': TopologyAction,
            'TransmissionSystemOperator': TransmissionSystemOperator,
            'TriggerCondition': TriggerCondition,
            'UnifiedPowerFlowController': UnifiedPowerFlowController,
            'UnitCostSchedule': UnitCostSchedule,
            'UnitCostTimePoint': UnitCostTimePoint,
            'Verification': Verification,
            'VoltageAngleLimit': VoltageAngleLimit,
            'VoltageAngleSchedule': VoltageAngleSchedule,
            'VoltageAngleTimePoint': VoltageAngleTimePoint,
            'VoltageControlFunction': VoltageControlFunction,
            'VoltageInjectionControlFunction': VoltageInjectionControlFunction,
            'VoltageLimitSchedule': VoltageLimitSchedule,
            'VoltageLimitTimePoint': VoltageLimitTimePoint,
            'VsConverterRegularSchedule': VsConverterRegularSchedule,
            'VsConverterSchedule': VsConverterSchedule,
            'VsConverterTimePoint': VsConverterTimePoint,
        }
        self.association_inverse_dict: Dict[Tuple[str, str], str] = dict()
        self.ACDCConverterAction_list = list()
        self.ACDCConverterController_list = list()
        self.ACDCConverterRegularSchedule_list = list()
        self.ACDCTimePoint_list = list()
        self.ACEmulationControlFunction_list = list()
        self.ACPointOfCommonCoupling_list = list()
        self.ACTieCorridor_list = list()
        self.ActivePowerControlFunction_list = list()
        self.ActivePowerLimitSchedule_list = list()
        self.ActivePowerLimitTimePoint_list = list()
        self.Activity_list = list()
        self.Agent_list = list()
        self.AmbientTemperatureDependencyCurve_list = list()
        self.ApparentPowerLimitSchedule_list = list()
        self.ApparentPowerLimitTimePoint_list = list()
        self.AreaBorderTerminal_list = list()
        self.AreaDispatchableUnit_list = list()
        self.AreaInterchangeController_list = list()
        self.AssessedElement_list = list()
        self.AssessedElementRegularSchedule_list = list()
        self.AssessedElementRegularTimePoint_list = list()
        self.AssessedElementSchedule_list = list()
        self.AssessedElementTimePoint_list = list()
        self.AssessedElementWithContingency_list = list()
        self.AssessedElementWithRemedialAction_list = list()
        self.Assessment_list = list()
        self.AsynchronousMachineRegularSchedule_list = list()
        self.AsynchronousMachineSchedule_list = list()
        self.AsynchronousMachineTimePoint_list = list()
        self.AutomationBlockGroup_list = list()
        self.AutomationFunction_list = list()
        self.AvailabilityContainer_list = list()
        self.AvailabilityEnabled_list = list()
        self.AvailabilityEquipment_list = list()
        self.AvailabilityExceptionalLimit_list = list()
        self.AvailabilityGroup_list = list()
        self.AvailabilityPowerSystemFunction_list = list()
        self.AvailabilityRemedialAction_list = list()
        self.AvailabilityRemedialActionScheme_list = list()
        self.AvailabilitySchedule_list = list()
        self.AvailabilityTimePoint_list = list()
        self.BaseCaseCurrentLimit_list = list()
        self.BaseCaseCurrentLimitSchedule_list = list()
        self.BaseCaseCurrentLimitTimePoint_list = list()
        self.BaseCasePowerFlowResult_list = list()
        self.BaseIrregularTimeSeries_list = list()
        self.BaseOverloadLimitCurve_list = list()
        self.BaseRegularIntervalSchedule_list = list()
        self.BaseTimeSeries_list = list()
        self.BatteryUnitAction_list = list()
        self.BatteryUnitSchedule_list = list()
        self.BatteryUnitTimePoint_list = list()
        self.BiddingZone_list = list()
        self.BiddingZoneAction_list = list()
        self.BiddingZoneBorder_list = list()
        self.BipolarDCSystem_list = list()
        self.BoundaryFrame_list = list()
        self.CalculationBasedImpactAssessmentMatrix_list = list()
        self.CapacityCalculationRegion_list = list()
        self.Circuit_list = list()
        self.CircuitShare_list = list()
        self.ClosedDistributionSystemOperator_list = list()
        self.Collection_list = list()
        self.CompensatorController_list = list()
        self.ConceptScheme_list = list()
        self.ConnectingImpactAssessmentMatrix_list = list()
        self.Contingency_list = list()
        self.ContingencyArea_list = list()
        self.ContingencyElement_list = list()
        self.ContingencyEquipment_list = list()
        self.ContingencyPowerFlowResult_list = list()
        self.ContingencySchedule_list = list()
        self.ContingencyTimePoint_list = list()
        self.ContingencyWithRemedialAction_list = list()
        self.ControlAreaRegularSchedule_list = list()
        self.ControlAreaSchedule_list = list()
        self.ControlAreaTimePoint_list = list()
        self.ControlFunctionBlock_list = list()
        self.ControlFunctionBlockAction_list = list()
        self.ControllableQuantity_list = list()
        self.CoordinatedCapacityCalculator_list = list()
        self.CountertradeRemedialAction_list = list()
        self.CountertradeScheduleAction_list = list()
        self.CrossBorderRelevance_list = list()
        self.CsConverterRegularSchedule_list = list()
        self.CsConverterSchedule_list = list()
        self.CsConverterTimePoint_list = list()
        self.CurrentControlFunction_list = list()
        self.CurrentDroopControlFunction_list = list()
        self.CurrentDroopOverride_list = list()
        self.CurrentLimitSchedule_list = list()
        self.CurrentLimitTimePoint_list = list()
        self.DCBiPole_list = list()
        self.DCBypassSwitch_list = list()
        self.DCCommutationSwitch_list = list()
        self.DCConverterParallelingSwitch_list = list()
        self.DCCurrentControlFunction_list = list()
        self.DCEarthReturnTransferSwitch_list = list()
        self.DCHarmonicFilter_list = list()
        self.DCHighSpeedSwitch_list = list()
        self.DCLineParallelingSwitch_list = list()
        self.DCMetalicReturnSwitch_list = list()
        self.DCNeutralBusGroundingSwitch_list = list()
        self.DCNeutralBusSwitch_list = list()
        self.DCPointOfCommonCoupling_list = list()
        self.DCPole_list = list()
        self.DCSmoothingReactor_list = list()
        self.DCSmoothingReactorArrester_list = list()
        self.DCSubstation_list = list()
        self.DCSubstationBipole_list = list()
        self.DCSubstationPole_list = list()
        self.DCSystem_list = list()
        self.DCTieCorridor_list = list()
        self.DCVoltageControlFunction_list = list()
        self.Dataset_list = list()
        self.DifferenceModel_list = list()
        self.DirectCurrentBipoleController_list = list()
        self.DirectCurrentCircuit_list = list()
        self.DirectCurrentEquipmentController_list = list()
        self.DirectCurrentMasterController_list = list()
        self.DirectCurrentPoleController_list = list()
        self.DirectCurrentSubstationBipoleController_list = list()
        self.DirectCurrentSubstationController_list = list()
        self.DirectCurrentSubstationPoleController_list = list()
        self.DirectCurrentSystemOperator_list = list()
        self.DistributionSystemOperator_list = list()
        self.DurationOverloadLimitCurve_list = list()
        self.EdgeControlArea_list = list()
        self.EdgeSchedulingArea_list = list()
        self.ElectricalChargingUnit_list = list()
        self.EnablingTimePoint_list = list()
        self.EnergyAlignmentCoordinator_list = list()
        self.EnergyBlockComponent_list = list()
        self.EnergyBlockOrder_list = list()
        self.EnergyComponent_list = list()
        self.EnergyConnectionRegularSchedule_list = list()
        self.EnergyConnectionSchedule_list = list()
        self.EnergyConnectionTimePoint_list = list()
        self.EnergyCoordinationRegion_list = list()
        self.EnergyExchangePoint_list = list()
        self.EnergyGroup_list = list()
        self.EnergySourceModification_list = list()
        self.EnergySourceReference_list = list()
        self.EnergyType_list = list()
        self.Entity_list = list()
        self.EquipmentController_list = list()
        self.EquipmentControllerAction_list = list()
        self.EquivalentGeneratingUnit_list = list()
        self.EquivalentInjectionAction_list = list()
        self.EquivalentInjectionRegularSchedule_list = list()
        self.EquivalentInjectionSchedule_list = list()
        self.EquivalentInjectionTimePoint_list = list()
        self.EquivalentPowerElectronicsUnit_list = list()
        self.EquivalentPowerPlant_list = list()
        self.EventSchedule_list = list()
        self.EventTimePoint_list = list()
        self.ExceptionalContingency_list = list()
        self.ExceptionalPowerTransferCorridor_list = list()
        self.ExternalNetworkInjectionAction_list = list()
        self.ExternalNetworkInjectionRegularSchedule_list = list()
        self.ExternalNetworkInjectionSchedule_list = list()
        self.ExternalNetworkInjectionTimePoint_list = list()
        self.FACTSEquipment_list = list()
        self.FaultCause_list = list()
        self.FaultOutage_list = list()
        self.FlexibleEnergyUnit_list = list()
        self.Frame_list = list()
        self.FrequencyControlFunction_list = list()
        self.FrequencyMonitoringTerminal_list = list()
        self.FuelStorage_list = list()
        self.FuelStorageRegularSchedule_list = list()
        self.FuelStorageSchedule_list = list()
        self.FuelStorageTimePoint_list = list()
        self.FunctionBlock_list = list()
        self.FunctionInputVariable_list = list()
        self.FunctionOutputVariable_list = list()
        self.Gate_list = list()
        self.GateInputPin_list = list()
        self.GeneratingUnitSchedule_list = list()
        self.GeneratingUnitTimePoint_list = list()
        self.GenericAvailableSchedule_list = list()
        self.GenericEnablingSchedule_list = list()
        self.GenericSequenceSchedule_list = list()
        self.GenericValueSchedule_list = list()
        self.GenericValueTimePoint_list = list()
        self.Geometry_list = list()
        self.GeothermalGeneratingUnit_list = list()
        self.GridConnectionPoint_list = list()
        self.GridDisturbance_list = list()
        self.GridStateAlteration_list = list()
        self.GridStateAlterationCollection_list = list()
        self.GridStateAlterationRemedialAction_list = list()
        self.GridStateAlterationSchedule_list = list()
        self.GridStateAlterationTimePoint_list = list()
        self.GridStateIntensitySchedule_list = list()
        self.HourPattern_list = list()
        self.HourPeriod_list = list()
        self.ImpactAssessmentMatrix_list = list()
        self.ImpedanceControlFunction_list = list()
        self.InServiceAction_list = list()
        self.InServiceRegularSchedule_list = list()
        self.InServiceSchedule_list = list()
        self.InServiceTimePoint_list = list()
        self.InfeedLimit_list = list()
        self.InfeedLimitSchedule_list = list()
        self.InfeedLimitTimePoint_list = list()
        self.InfeedTerminal_list = list()
        self.InfluenceArea_list = list()
        self.InjectionController_list = list()
        self.Installation_list = list()
        self.Interruption_list = list()
        self.IntertemporalPropertyRange_list = list()
        self.LicenseDocument_list = list()
        self.LimitDependencyCurve_list = list()
        self.LineCircuit_list = list()
        self.ListBasedImpactAssessmentMatrix_list = list()
        self.LoadAction_list = list()
        self.LoadFrequencyControlArea_list = list()
        self.LoadFrequencyControlBlock_list = list()
        self.LoadFrequencyControlOperator_list = list()
        self.LossCurve_list = list()
        self.MeasurementCalculator_list = list()
        self.MeasurementCalculatorInput_list = list()
        self.MobileElectricalUnit_list = list()
        self.Model_list = list()
        self.Modeling_list = list()
        self.ModularStaticSynchronousSeriesCompensator_list = list()
        self.MonitoringArea_list = list()
        self.MonopolarDCSystem_list = list()
        self.MustRunSchedule_list = list()
        self.MustRunTimePoint_list = list()
        self.Name_list = list()
        self.NameType_list = list()
        self.NamingAuthority_list = list()
        self.ObjectType_list = list()
        self.ObservabilityArea_list = list()
        self.ObservableQuantity_list = list()
        self.OrdinaryContingency_list = list()
        self.OrdinaryPowerTransferCorridor_list = list()
        self.Organisation_list = list()
        self.OrganisationRole_list = list()
        self.OutOfRangeContingency_list = list()
        self.OutageCoordinationRegion_list = list()
        self.OutageCoordinator_list = list()
        self.OutagePlanningAgent_list = list()
        self.OutcomeValue_list = list()
        self.OverlappingZone_list = list()
        self.OwnerRemedialActionAssessment_list = list()
        self.PTCActivePowerSupport_list = list()
        self.ParticipationFactorTimePoint_list = list()
        self.PhaseControlFunction_list = list()
        self.PinContingency_list = list()
        self.PinDCTerminal_list = list()
        self.PinEquipment_list = list()
        self.PinEquipmentTripping_list = list()
        self.PinGate_list = list()
        self.PinMeasurement_list = list()
        self.PinOperationalLimit_list = list()
        self.PinPowerTransferCorridor_list = list()
        self.PinTerminal_list = list()
        self.Plant_list = list()
        self.PointOfCommonCoupling_list = list()
        self.PowerBidDependency_list = list()
        self.PowerBidSchedule_list = list()
        self.PowerBidScheduleTimePoint_list = list()
        self.PowerCapacity_list = list()
        self.PowerElectricalChemicalUnit_list = list()
        self.PowerElectronicsConnectionAction_list = list()
        self.PowerElectronicsConnectionController_list = list()
        self.PowerElectronicsMarineUnit_list = list()
        self.PowerElectronicsUnitController_list = list()
        self.PowerFactorControlFunction_list = list()
        self.PowerFlowResult_list = list()
        self.PowerFrequencyController_list = list()
        self.PowerPlantController_list = list()
        self.PowerRemedialAction_list = list()
        self.PowerRemedialActionSchedule_list = list()
        self.PowerRemedialActionTimePoint_list = list()
        self.PowerSchedule_list = list()
        self.PowerScheduleAction_list = list()
        self.PowerShiftKeyDistribution_list = list()
        self.PowerShiftKeySchedule_list = list()
        self.PowerShiftKeyStrategy_list = list()
        self.PowerSystemOrganisationRole_list = list()
        self.PowerSystemProject_list = list()
        self.PowerSystemProjectGroup_list = list()
        self.PowerTimePoint_list = list()
        self.PowerTransferCorridor_list = list()
        self.PowerTransformerCircuit_list = list()
        self.PropertyReference_list = list()
        self.ProportionalEnergyComponent_list = list()
        self.ProposingRemedialActionScheduleShare_list = list()
        self.QualitativeRemedialActionImpact_list = list()
        self.QuantitativeRemedialActionImpact_list = list()
        self.QuantityValue_list = list()
        self.RangeConstraint_list = list()
        self.ReactivePowerControlFunction_list = list()
        self.RecoveryOverloadLimitCurve_list = list()
        self.RedispatchRemedialAction_list = list()
        self.RedispatchScheduleAction_list = list()
        self.Region_list = list()
        self.RegulatingControlAction_list = list()
        self.RegulatingControlRegularSchedule_list = list()
        self.RegulatingControlSchedule_list = list()
        self.RegulatingControlTimePoint_list = list()
        self.RemedialAction_list = list()
        self.RemedialActionApplied_list = list()
        self.RemedialActionCost_list = list()
        self.RemedialActionDependency_list = list()
        self.RemedialActionGroup_list = list()
        self.RemedialActionGroupSchedule_list = list()
        self.RemedialActionGroupTimePoint_list = list()
        self.RemedialActionImpact_list = list()
        self.RemedialActionOutcomeValue_list = list()
        self.RemedialActionSchedule_list = list()
        self.RemedialActionScheduleDependency_list = list()
        self.RemedialActionScheduleGroup_list = list()
        self.RemedialActionScheduleOutcomeValue_list = list()
        self.RemedialActionScheduleResponse_list = list()
        self.RemedialActionScheme_list = list()
        self.RemedialActionSchemeSchedule_list = list()
        self.RemedialActionSchemeTimePoint_list = list()
        self.ReservoirRegularSchedule_list = list()
        self.ReservoirSchedule_list = list()
        self.ReservoirTimePoint_list = list()
        self.RightsStatement_list = list()
        self.RotatingMachineAction_list = list()
        self.RotatingMachineController_list = list()
        self.SSSCController_list = list()
        self.SSSCSimulationSettings_list = list()
        self.ScheduleResource_list = list()
        self.ScheduleResourceController_list = list()
        self.SchedulingArea_list = list()
        self.SchedulingAreaExchangePoint_list = list()
        self.SchemeRemedialAction_list = list()
        self.SecondarySubstation_list = list()
        self.SecurityCoordinator_list = list()
        self.SemanticAsset_list = list()
        self.SensitivityArea_list = list()
        self.SensitivityFactor_list = list()
        self.SensitivityMatrix_list = list()
        self.SequenceTimePoint_list = list()
        self.SetPointAction_list = list()
        self.ShuntCompensatorModification_list = list()
        self.ShuntCompensatorSchedule_list = list()
        self.ShuntCompensatorTimePoint_list = list()
        self.SolarRadiationDependencyCurve_list = list()
        self.Stage_list = list()
        self.StageTrigger_list = list()
        self.StageTriggerSchedule_list = list()
        self.StageTriggerTimePoint_list = list()
        self.StaticPropertyRange_list = list()
        self.StaticSynchronousCompensator_list = list()
        self.StaticSynchronousSeriesCompensator_list = list()
        self.StaticVarCompensator_list = list()
        self.StaticVarCompensatorAction_list = list()
        self.StaticVarCompensatorSchedule_list = list()
        self.StaticVarCompensatorTimePoint_list = list()
        self.SubControlArea_list = list()
        self.SubSchedulingArea_list = list()
        self.SubstationController_list = list()
        self.SupportedProfileCollection_list = list()
        self.SwitchRegularSchedule_list = list()
        self.SwitchSchedule_list = list()
        self.SwitchTimePoint_list = list()
        self.SynchronousArea_list = list()
        self.SynchronousMachineRegularSchedule_list = list()
        self.SynchronousMachineSchedule_list = list()
        self.SynchronousMachineTimePoint_list = list()
        self.SystemControl_list = list()
        self.SystemOperationCoordinator_list = list()
        self.SystemOperator_list = list()
        self.TCSCCompensationPoint_list = list()
        self.TCSCController_list = list()
        self.TapChangerControlRegularSchedule_list = list()
        self.TapChangerControlSchedule_list = list()
        self.TapChangerController_list = list()
        self.TapPositionAction_list = list()
        self.TapRegularSchedule_list = list()
        self.TapSchedule_list = list()
        self.TapScheduleTimePoint_list = list()
        self.ThyristorControlledSeriesCompensator_list = list()
        self.TieCorridor_list = list()
        self.TopologyAction_list = list()
        self.TransmissionSystemOperator_list = list()
        self.TriggerCondition_list = list()
        self.UnifiedPowerFlowController_list = list()
        self.UnitCostSchedule_list = list()
        self.UnitCostTimePoint_list = list()
        self.Verification_list = list()
        self.VoltageAngleLimit_list = list()
        self.VoltageAngleSchedule_list = list()
        self.VoltageAngleTimePoint_list = list()
        self.VoltageControlFunction_list = list()
        self.VoltageInjectionControlFunction_list = list()
        self.VoltageLimitSchedule_list = list()
        self.VoltageLimitTimePoint_list = list()
        self.VsConverterRegularSchedule_list = list()
        self.VsConverterSchedule_list = list()
        self.VsConverterTimePoint_list = list()
