# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Explicit registry for every SiennaSchemas v0.4 object parser."""

from typing import Any, Callable

from VeraGridEngine.IO.sienna.devices.schema_object import SiennaObjectKind
from VeraGridEngine.IO.sienna.devices.core.topology.ac_bus import parse_sienna_ac_bus
from VeraGridEngine.IO.sienna.devices.core.common.ac_bus_type import parse_sienna_ac_bus_type
from VeraGridEngine.IO.sienna.devices.operations.service.agc import parse_sienna_agc
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.avr_fixed import parse_sienna_avr_fixed
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.avr_simple import parse_sienna_avr_simple
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.avr_type_i import parse_sienna_avr_type_i
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.avr_type_ii import parse_sienna_avr_type_ii
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.outer_control.active_power_droop import parse_sienna_active_power_droop
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.outer_control.active_power_pi import parse_sienna_active_power_pi
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.outer_control.active_renewable_controller_ab import parse_sienna_active_renewable_controller_ab
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.outer_control.active_virtual_oscillator import parse_sienna_active_virtual_oscillator
from VeraGridEngine.IO.sienna.devices.core.common.admittance_unit_basis import parse_sienna_admittance_unit_basis
from VeraGridEngine.IO.sienna.devices.investments.technologies.aggregate_transport_technology import parse_sienna_aggregate_transport_technology
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.machine.anderson_fouad_machine import parse_sienna_anderson_fouad_machine
from VeraGridEngine.IO.sienna.devices.core.topology.arc import parse_sienna_arc
from VeraGridEngine.IO.sienna.devices.core.topology.area import parse_sienna_area
from VeraGridEngine.IO.sienna.devices.operations.branch.area_interchange import parse_sienna_area_interchange
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.converter.average_converter import parse_sienna_average_converter
from VeraGridEngine.IO.sienna.devices.core.common.average_rate_curve import parse_sienna_average_rate_curve
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.machine.base_machine import parse_sienna_base_machine
from VeraGridEngine.IO.sienna.devices.operations.common.bilateral_confirmation import parse_sienna_bilateral_confirmation
from VeraGridEngine.IO.sienna.devices.operations.common.bilateral_product import parse_sienna_bilateral_product
from VeraGridEngine.IO.sienna.devices.operations.market.bilateral_transaction import parse_sienna_bilateral_transaction
from VeraGridEngine.IO.sienna.devices.investments.requirements.capacity_reserve_margin import parse_sienna_capacity_reserve_margin
from VeraGridEngine.IO.sienna.devices.core.common.capital_cost import parse_sienna_capital_cost
from VeraGridEngine.IO.sienna.devices.investments.requirements.carbon_caps import parse_sienna_carbon_caps
from VeraGridEngine.IO.sienna.devices.investments.requirements.carbon_tax import parse_sienna_carbon_tax
from VeraGridEngine.IO.sienna.devices.core.common.charge_discharge import parse_sienna_charge_discharge
from VeraGridEngine.IO.sienna.devices.investments.technologies.colocated_supply_storage_technology import parse_sienna_colocated_supply_storage_technology
from VeraGridEngine.IO.sienna.devices.operations.associations.combined_cycle_association import parse_sienna_combined_cycle_association
from VeraGridEngine.IO.sienna.devices.operations.supplemental_attributes.combined_cycle_block import parse_sienna_combined_cycle_block
from VeraGridEngine.IO.sienna.devices.operations.common.combined_cycle_configuration import parse_sienna_combined_cycle_configuration
from VeraGridEngine.IO.sienna.devices.operations.supplemental_attributes.combined_cycle_fractional import parse_sienna_combined_cycle_fractional
from VeraGridEngine.IO.sienna.devices.operations.common.commitment_modes import parse_sienna_commitment_modes
from VeraGridEngine.IO.sienna.devices.core.common.complex_number import parse_sienna_complex_number
from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import parse_sienna_cost_curve
from VeraGridEngine.IO.sienna.devices.core.common.current_loss_curve import parse_sienna_current_loss_curve
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.inner_control.current_mode_control import parse_sienna_current_mode_control
from VeraGridEngine.IO.sienna.devices.core.common.curve_multi_step import parse_sienna_curve_multi_step
from VeraGridEngine.IO.sienna.devices.core.common.curve_styles import parse_sienna_curve_styles
from VeraGridEngine.IO.sienna.devices.core.topology.dc_bus import parse_sienna_dc_bus
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.turbine_gov.degov import parse_sienna_degov
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.turbine_gov.degov1 import parse_sienna_degov1
from VeraGridEngine.IO.sienna.devices.core.supplemental_attributes.data_source import parse_sienna_data_source
from VeraGridEngine.IO.sienna.devices.core.common.dbd_pnts import parse_sienna_dbd_pnts
from VeraGridEngine.IO.sienna.devices.investments.technologies.demand_requirement import parse_sienna_demand_requirement
from VeraGridEngine.IO.sienna.devices.investments.technologies.demand_side_technology import parse_sienna_demand_side_technology
from VeraGridEngine.IO.sienna.devices.time_series.deterministic import parse_sienna_deterministic
from VeraGridEngine.IO.sienna.devices.time_series.deterministic_single_time_series import parse_sienna_deterministic_single_time_series
from VeraGridEngine.IO.sienna.devices.operations.branch.discrete_controlled_ac_branch import parse_sienna_discrete_controlled_ac_branch
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.esac1_a import parse_sienna_esac1_a
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.esac6_a import parse_sienna_esac6_a
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.esac8_b import parse_sienna_esac8_b
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.esdc1_a import parse_sienna_esdc1_a
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.esdc2_a import parse_sienna_esdc2_a
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.esst1_a import parse_sienna_esst1_a
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.esst4_b import parse_sienna_esst4_b
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.ex4_vsa import parse_sienna_ex4_vsa
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.exac1 import parse_sienna_exac1
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.exac1_a import parse_sienna_exac1_a
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.exac2 import parse_sienna_exac2
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.expic1 import parse_sienna_expic1
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.exst1 import parse_sienna_exst1
from VeraGridEngine.IO.sienna.devices.time_series.common.element_type import parse_sienna_element_type
from VeraGridEngine.IO.sienna.devices.core.common.emission_basis import parse_sienna_emission_basis
from VeraGridEngine.IO.sienna.devices.core.supplemental_attributes.emissions_data import parse_sienna_emissions_data
from VeraGridEngine.IO.sienna.devices.operations.static_injection.energy_reservoir_storage import parse_sienna_energy_reservoir_storage
from VeraGridEngine.IO.sienna.devices.investments.requirements.energy_share_requirements import parse_sienna_energy_share_requirements
from VeraGridEngine.IO.sienna.devices.core.common.energy_unit import parse_sienna_energy_unit
from VeraGridEngine.IO.sienna.devices.core.common.energy_unit_basis import parse_sienna_energy_unit_basis
from VeraGridEngine.IO.sienna.devices.investments.supplemental_attributes.existing_devices import parse_sienna_existing_devices
from VeraGridEngine.IO.sienna.devices.operations.static_injection.exponential_load import parse_sienna_exponential_load
from VeraGridEngine.IO.sienna.devices.operations.static_injection.facts_control_device import parse_sienna_facts_control_device
from VeraGridEngine.IO.sienna.devices.operations.common.facts_control_device_control_mode import parse_sienna_facts_control_device_control_mode
from VeraGridEngine.IO.sienna.devices.core.common.fdbd_pnts import parse_sienna_fdbd_pnts
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.shaft.five_mass_shaft import parse_sienna_five_mass_shaft
from VeraGridEngine.IO.sienna.devices.operations.static_injection.fixed_admittance import parse_sienna_fixed_admittance
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.dc_source.fixed_dc_source import parse_sienna_fixed_dc_source
from VeraGridEngine.IO.sienna.devices.operations.supplemental_attributes.fixed_forced_outage import parse_sienna_fixed_forced_outage
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.frequency_estimator.fixed_frequency import parse_sienna_fixed_frequency
from VeraGridEngine.IO.sienna.devices.core.common.from_to import parse_sienna_from_to
from VeraGridEngine.IO.sienna.devices.core.common.from_to_to_from import parse_sienna_from_to_to_from
from VeraGridEngine.IO.sienna.devices.core.common.fuel_curve import parse_sienna_fuel_curve
from VeraGridEngine.IO.sienna.devices.core.common.fuel_unit import parse_sienna_fuel_unit
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.machine.full_machine import parse_sienna_full_machine
from VeraGridEngine.IO.sienna.devices.core.common.function_data import parse_sienna_function_data
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.turbine_gov.gas_tg import parse_sienna_gas_tg
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.turbine_gov.general_gov_model import parse_sienna_general_gov_model
from VeraGridEngine.IO.sienna.devices.operations.branch.generic_arc_impedance import parse_sienna_generic_arc_impedance
from VeraGridEngine.IO.sienna.devices.core.common.generic_operation_cost import parse_sienna_generic_operation_cost
from VeraGridEngine.IO.sienna.devices.core.supplemental_attributes.geographic_info import parse_sienna_geographic_info
from VeraGridEngine.IO.sienna.devices.operations.supplemental_attributes.geometric_distribution_forced_outage import parse_sienna_geometric_distribution_forced_outage
from VeraGridEngine.IO.sienna.devices.operations.service.group_reserve import parse_sienna_group_reserve
from VeraGridEngine.IO.sienna.devices.investments.requirements.hourly_matching import parse_sienna_hourly_matching
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.output_current_limiter.hybrid_output_current_limiter import parse_sienna_hybrid_output_current_limiter
from VeraGridEngine.IO.sienna.devices.operations.static_injection.hybrid_system import parse_sienna_hybrid_system
from VeraGridEngine.IO.sienna.devices.operations.static_injection.hydro_dispatch import parse_sienna_hydro_dispatch
from VeraGridEngine.IO.sienna.devices.core.common.hydro_generation_cost import parse_sienna_hydro_generation_cost
from VeraGridEngine.IO.sienna.devices.operations.supplemental_attributes.hydro_power_plant import parse_sienna_hydro_power_plant
from VeraGridEngine.IO.sienna.devices.operations.static_injection.hydro_pump_turbine import parse_sienna_hydro_pump_turbine
from VeraGridEngine.IO.sienna.devices.operations.static_injection.hydro_reservoir import parse_sienna_hydro_reservoir
from VeraGridEngine.IO.sienna.devices.core.common.hydro_reservoir_cost import parse_sienna_hydro_reservoir_cost
from VeraGridEngine.IO.sienna.devices.core.common.hydro_storage_generation_cost import parse_sienna_hydro_storage_generation_cost
from VeraGridEngine.IO.sienna.devices.operations.static_injection.hydro_turbine import parse_sienna_hydro_turbine
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.turbine_gov.hydro_turbine_gov import parse_sienna_hydro_turbine_gov
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.pss.ieeest import parse_sienna_ieeest
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.ieeet1 import parse_sienna_ieeet1
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.turbine_gov.ieee_turbine_gov1 import parse_sienna_ieee_turbine_gov1
from VeraGridEngine.IO.sienna.devices.operations.supplemental_attributes.impedance_correction_data import parse_sienna_impedance_correction_data
from VeraGridEngine.IO.sienna.devices.core.common.impedance_unit_basis import parse_sienna_impedance_unit_basis
from VeraGridEngine.IO.sienna.devices.core.common.import_export_cost import parse_sienna_import_export_cost
from VeraGridEngine.IO.sienna.devices.core.common.import_export_time_series_cost import parse_sienna_import_export_time_series_cost
from VeraGridEngine.IO.sienna.devices.core.common.in_out import parse_sienna_in_out
from VeraGridEngine.IO.sienna.devices.core.common.incremental_curve import parse_sienna_incremental_curve
from VeraGridEngine.IO.sienna.devices.core.common.input_output_curve import parse_sienna_input_output_curve
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.output_current_limiter.instantaneous_output_current_limiter import parse_sienna_instantaneous_output_current_limiter
from VeraGridEngine.IO.sienna.devices.operations.static_injection.interconnecting_converter import parse_sienna_interconnecting_converter
from VeraGridEngine.IO.sienna.devices.operations.static_injection.interruptible_power_load import parse_sienna_interruptible_power_load
from VeraGridEngine.IO.sienna.devices.operations.static_injection.interruptible_standard_load import parse_sienna_interruptible_standard_load
from VeraGridEngine.IO.sienna.devices.time_series.common.interval_alignment import parse_sienna_interval_alignment
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.frequency_estimator.kaura_pll import parse_sienna_kaura_pll
from VeraGridEngine.IO.sienna.devices.operations.common.lcc_control_mode import parse_sienna_lcc_control_mode
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.filter.lc_filter import parse_sienna_lc_filter
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.filter.lcl_filter import parse_sienna_lcl_filter
from VeraGridEngine.IO.sienna.devices.operations.branch.line import parse_sienna_line
from VeraGridEngine.IO.sienna.devices.core.common.linear_function_data import parse_sienna_linear_function_data
from VeraGridEngine.IO.sienna.devices.operations.common.load_conformity import parse_sienna_load_conformity
from VeraGridEngine.IO.sienna.devices.core.common.load_cost import parse_sienna_load_cost
from VeraGridEngine.IO.sienna.devices.core.topology.load_zone import parse_sienna_load_zone
from VeraGridEngine.IO.sienna.devices.core.common.loss_curve import parse_sienna_loss_curve
from VeraGridEngine.IO.sienna.devices.core.common.loss_value_curve import parse_sienna_loss_value_curve
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.output_current_limiter.magnitude_output_current_limiter import parse_sienna_magnitude_output_current_limiter
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.machine.marconato_machine import parse_sienna_marconato_machine
from VeraGridEngine.IO.sienna.devices.core.common.market_bid_cost import parse_sienna_market_bid_cost
from VeraGridEngine.IO.sienna.devices.core.common.market_bid_time_series_cost import parse_sienna_market_bid_time_series_cost
from VeraGridEngine.IO.sienna.devices.operations.common.market_stage import parse_sienna_market_stage
from VeraGridEngine.IO.sienna.devices.core.common.mass_unit import parse_sienna_mass_unit
from VeraGridEngine.IO.sienna.devices.investments.requirements.maximum_capacity_requirements import parse_sienna_maximum_capacity_requirements
from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
from VeraGridEngine.IO.sienna.devices.core.common.min_max_by_key import parse_sienna_min_max_by_key
from VeraGridEngine.IO.sienna.devices.investments.requirements.minimum_capacity_requirements import parse_sienna_minimum_capacity_requirements
from VeraGridEngine.IO.sienna.devices.operations.static_injection.motor_load import parse_sienna_motor_load
from VeraGridEngine.IO.sienna.devices.investments.technologies.nodal_ac_transport_technology import parse_sienna_nodal_ac_transport_technology
from VeraGridEngine.IO.sienna.devices.investments.technologies.nodal_hvdc_transport_technology import parse_sienna_nodal_hvdc_transport_technology
from VeraGridEngine.IO.sienna.devices.time_series.non_sequential_time_series import parse_sienna_non_sequential_time_series
from VeraGridEngine.IO.sienna.devices.operations.service.offline_reserve import parse_sienna_offline_reserve
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.machine.one_d_one_q_machine import parse_sienna_one_d_one_q_machine
from VeraGridEngine.IO.sienna.devices.operations.service.online_reserve import parse_sienna_online_reserve
from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import parse_sienna_operational_flow_limit
from VeraGridEngine.IO.sienna.devices.operations.common.operational_states import parse_sienna_operational_states
from VeraGridEngine.IO.sienna.devices.core.common.outage_factors import parse_sienna_outage_factors
from VeraGridEngine.IO.sienna.devices.time_series.common.owner_category import parse_sienna_owner_category
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.turbine_gov.pidgov import parse_sienna_pidgov
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.pss.pss2_a import parse_sienna_pss2_a
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.pss.pss2_b import parse_sienna_pss2_b
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.pss.pss2_c import parse_sienna_pss2_c
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.pss.pss_fixed import parse_sienna_pss_fixed
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.pss.pss_simple import parse_sienna_pss_simple
from VeraGridEngine.IO.sienna.devices.time_series.common.period import parse_sienna_period
from VeraGridEngine.IO.sienna.devices.core.common.piecewise_linear_data import parse_sienna_piecewise_linear_data
from VeraGridEngine.IO.sienna.devices.core.common.piecewise_step_data import parse_sienna_piecewise_step_data
from VeraGridEngine.IO.sienna.devices.operations.supplemental_attributes.planned_outage import parse_sienna_planned_outage
from VeraGridEngine.IO.sienna.devices.operations.associations.plant_association import parse_sienna_plant_association
from VeraGridEngine.IO.sienna.devices.operations.market.point_to_point_bid import parse_sienna_point_to_point_bid
from VeraGridEngine.IO.sienna.devices.core.common.pollutant_type import parse_sienna_pollutant_type
from VeraGridEngine.IO.sienna.devices.investments.financials.portfolio_financial_data import parse_sienna_portfolio_financial_data
from VeraGridEngine.IO.sienna.devices.operations.static_injection.power_load import parse_sienna_power_load
from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import parse_sienna_prime_movers
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.output_current_limiter.priority_output_current_limiter import parse_sienna_priority_output_current_limiter
from VeraGridEngine.IO.sienna.devices.time_series.probabilistic import parse_sienna_probabilistic
from VeraGridEngine.IO.sienna.devices.core.common.production_variable_cost_curve import parse_sienna_production_variable_cost_curve
from VeraGridEngine.IO.sienna.devices.core.common.quadratic_function_data import parse_sienna_quadratic_function_data
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.inner_control.re_current_control_b import parse_sienna_re_current_control_b
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.filter.rl_filter import parse_sienna_rl_filter
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.outer_control.reactive_power_droop import parse_sienna_reactive_power_droop
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.outer_control.reactive_power_pi import parse_sienna_reactive_power_pi
from VeraGridEngine.IO.sienna.devices.operations.supplemental_attributes.reactive_power_sharing import parse_sienna_reactive_power_sharing
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.outer_control.reactive_renewable_controller_ab import parse_sienna_reactive_renewable_controller_ab
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.outer_control.reactive_virtual_oscillator import parse_sienna_reactive_virtual_oscillator
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.frequency_estimator.reduced_order_pll import parse_sienna_reduced_order_pll
from VeraGridEngine.IO.sienna.devices.operations.static_injection.renewable_dispatch import parse_sienna_renewable_dispatch
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.converter.renewable_energy_converter_type_a import parse_sienna_renewable_energy_converter_type_a
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.converter.renewable_energy_voltage_converter_type_a import parse_sienna_renewable_energy_voltage_converter_type_a
from VeraGridEngine.IO.sienna.devices.core.common.renewable_generation_cost import parse_sienna_renewable_generation_cost
from VeraGridEngine.IO.sienna.devices.operations.static_injection.renewable_non_dispatch import parse_sienna_renewable_non_dispatch
from VeraGridEngine.IO.sienna.devices.operations.supplemental_attributes.renewable_power_plant import parse_sienna_renewable_power_plant
from VeraGridEngine.IO.sienna.devices.investments.associations.requirement_association import parse_sienna_requirement_association
from VeraGridEngine.IO.sienna.devices.operations.common.reserve_direction import parse_sienna_reserve_direction
from VeraGridEngine.IO.sienna.devices.core.common.reservoir_location import parse_sienna_reservoir_location
from VeraGridEngine.IO.sienna.devices.investments.supplemental_attributes.retirement_potential import parse_sienna_retirement_potential
from VeraGridEngine.IO.sienna.devices.investments.supplemental_attributes.retrofit_potential import parse_sienna_retrofit_potential
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.machine.round_rotor_exponential import parse_sienna_round_rotor_exponential
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.machine.round_rotor_machine import parse_sienna_round_rotor_machine
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.machine.round_rotor_quadratic import parse_sienna_round_rotor_quadratic
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.scrx import parse_sienna_scrx
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.sexs import parse_sienna_sexs
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.st6_b import parse_sienna_st6_b
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.avr.st8_c import parse_sienna_st8_c
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.pss.stab1 import parse_sienna_stab1
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.machine.salient_pole_exponential import parse_sienna_salient_pole_exponential
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.machine.salient_pole_machine import parse_sienna_salient_pole_machine
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.machine.salient_pole_quadratic import parse_sienna_salient_pole_quadratic
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.output_current_limiter.saturation_output_current_limiter import parse_sienna_saturation_output_current_limiter
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.machine.sauer_pai_machine import parse_sienna_sauer_pai_machine
from VeraGridEngine.IO.sienna.devices.time_series.scenarios import parse_sienna_scenarios
from VeraGridEngine.IO.sienna.devices.operations.branch.series_compensator import parse_sienna_series_compensator
from VeraGridEngine.IO.sienna.devices.operations.common.series_compensator_control_mode import parse_sienna_series_compensator_control_mode
from VeraGridEngine.IO.sienna.devices.operations.associations.service_association import parse_sienna_service_association
from VeraGridEngine.IO.sienna.devices.operations.static_injection.shiftable_power_load import parse_sienna_shiftable_power_load
from VeraGridEngine.IO.sienna.devices.core.common.shunt_admittance_unit_basis import parse_sienna_shunt_admittance_unit_basis
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.machine.simple_af_machine import parse_sienna_simple_af_machine
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.machine.simple_full_machine import parse_sienna_simple_full_machine
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.machine.simple_marconato_machine import parse_sienna_simple_marconato_machine
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.shaft.single_mass import parse_sienna_single_mass
from VeraGridEngine.IO.sienna.devices.time_series.single_time_series import parse_sienna_single_time_series
from VeraGridEngine.IO.sienna.devices.operations.static_injection.source import parse_sienna_source
from VeraGridEngine.IO.sienna.devices.operations.static_injection.standard_load import parse_sienna_standard_load
from VeraGridEngine.IO.sienna.devices.core.common.start_up_shut_down import parse_sienna_start_up_shut_down
from VeraGridEngine.IO.sienna.devices.core.common.start_up_stages import parse_sienna_start_up_stages
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.turbine_gov.steam_turbine_gov1 import parse_sienna_steam_turbine_gov1
from VeraGridEngine.IO.sienna.devices.core.common.storage_capital_cost import parse_sienna_storage_capital_cost
from VeraGridEngine.IO.sienna.devices.core.common.storage_cost import parse_sienna_storage_cost
from VeraGridEngine.IO.sienna.devices.core.common.storage_tech import parse_sienna_storage_tech
from VeraGridEngine.IO.sienna.devices.investments.technologies.storage_technology import parse_sienna_storage_technology
from VeraGridEngine.IO.sienna.devices.operations.supplemental_attributes.substation import parse_sienna_substation
from VeraGridEngine.IO.sienna.devices.core.associations.supplemental_attribute_association import parse_sienna_supplemental_attribute_association
from VeraGridEngine.IO.sienna.devices.investments.technologies.supply_technology import parse_sienna_supply_technology
from VeraGridEngine.IO.sienna.devices.operations.static_injection.switched_admittance import parse_sienna_switched_admittance
from VeraGridEngine.IO.sienna.devices.operations.common.switched_admittance_control_mode import parse_sienna_switched_admittance_control_mode
from VeraGridEngine.IO.sienna.devices.operations.static_injection.synchronous_condenser import parse_sienna_synchronous_condenser
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.turbine_gov.tg_fixed import parse_sienna_tg_fixed
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.turbine_gov.tg_simple import parse_sienna_tg_simple
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.turbine_gov.tg_type_i import parse_sienna_tg_type_i
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.turbine_gov.tg_type_ii import parse_sienna_tg_type_ii
from VeraGridEngine.IO.sienna.devices.operations.branch.t_model_hvdc_line import parse_sienna_t_model_hvdc_line
from VeraGridEngine.IO.sienna.devices.investments.financials.technology_financial_data import parse_sienna_technology_financial_data
from VeraGridEngine.IO.sienna.devices.core.common.thermal_fuels import parse_sienna_thermal_fuels
from VeraGridEngine.IO.sienna.devices.core.common.thermal_generation_cost import parse_sienna_thermal_generation_cost
from VeraGridEngine.IO.sienna.devices.operations.static_injection.thermal_multi_start import parse_sienna_thermal_multi_start
from VeraGridEngine.IO.sienna.devices.operations.supplemental_attributes.thermal_power_plant import parse_sienna_thermal_power_plant
from VeraGridEngine.IO.sienna.devices.operations.static_injection.thermal_standard import parse_sienna_thermal_standard
from VeraGridEngine.IO.sienna.devices.operations.branch.three_winding_transformer import parse_sienna_three_winding_transformer
from VeraGridEngine.IO.sienna.devices.operations.common.three_winding_transformer_shunt_location import parse_sienna_three_winding_transformer_shunt_location
from VeraGridEngine.IO.sienna.devices.time_series.common.time_reference import parse_sienna_time_reference
from VeraGridEngine.IO.sienna.devices.time_series.time_series_association import parse_sienna_time_series_association
from VeraGridEngine.IO.sienna.devices.core.common.time_series_average_rate_curve import parse_sienna_time_series_average_rate_curve
from VeraGridEngine.IO.sienna.devices.time_series.common.time_series_feature_value import parse_sienna_time_series_feature_value
from VeraGridEngine.IO.sienna.devices.time_series.common.time_series_features import parse_sienna_time_series_features
from VeraGridEngine.IO.sienna.devices.core.common.time_series_incremental_curve import parse_sienna_time_series_incremental_curve
from VeraGridEngine.IO.sienna.devices.core.common.time_series_input_output_curve import parse_sienna_time_series_input_output_curve
from VeraGridEngine.IO.sienna.devices.core.common.time_series_linear_function_data import parse_sienna_time_series_linear_function_data
from VeraGridEngine.IO.sienna.devices.core.common.time_series_piecewise_linear_data import parse_sienna_time_series_piecewise_linear_data
from VeraGridEngine.IO.sienna.devices.core.common.time_series_piecewise_step_data import parse_sienna_time_series_piecewise_step_data
from VeraGridEngine.IO.sienna.devices.core.common.time_series_quadratic_function_data import parse_sienna_time_series_quadratic_function_data
from VeraGridEngine.IO.sienna.devices.operations.market.trading_hub import parse_sienna_trading_hub
from VeraGridEngine.IO.sienna.devices.operations.associations.trading_hub_association import parse_sienna_trading_hub_association
from VeraGridEngine.IO.sienna.devices.operations.branch.transformer_circuit import parse_sienna_transformer_circuit
from VeraGridEngine.IO.sienna.devices.operations.common.transformer_control_objective import parse_sienna_transformer_control_objective
from VeraGridEngine.IO.sienna.devices.operations.service.transmission_interface import parse_sienna_transmission_interface
from VeraGridEngine.IO.sienna.devices.core.common.turbine_pump import parse_sienna_turbine_pump
from VeraGridEngine.IO.sienna.devices.core.common.two_dimensional_function_point import parse_sienna_two_dimensional_function_point
from VeraGridEngine.IO.sienna.devices.operations.branch.two_terminal_generic_hvdc_line import parse_sienna_two_terminal_generic_hvdc_line
from VeraGridEngine.IO.sienna.devices.operations.branch.two_terminal_lcc_line import parse_sienna_two_terminal_lcc_line
from VeraGridEngine.IO.sienna.devices.operations.branch.two_terminal_vsc_line import parse_sienna_two_terminal_vsc_line
from VeraGridEngine.IO.sienna.devices.operations.branch.two_winding_transformer import parse_sienna_two_winding_transformer
from VeraGridEngine.IO.sienna.devices.operations.common.two_winding_transformer_shunt_location import parse_sienna_two_winding_transformer_shunt_location
from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
from VeraGridEngine.IO.sienna.devices.core.common.up_down import parse_sienna_up_down
from VeraGridEngine.IO.sienna.devices.operations.common.vscac_control_modes import parse_sienna_vscac_control_modes
from VeraGridEngine.IO.sienna.devices.operations.common.vscdc_control_modes import parse_sienna_vscdc_control_modes
from VeraGridEngine.IO.sienna.devices.core.common.value_curve import parse_sienna_value_curve
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.outer_control.virtual_inertia import parse_sienna_virtual_inertia
from VeraGridEngine.IO.sienna.devices.operations.market.virtual_participant import parse_sienna_virtual_participant
from VeraGridEngine.IO.sienna.devices.operations.associations.voltage_control_association import parse_sienna_voltage_control_association
from VeraGridEngine.IO.sienna.devices.operations.common.voltage_control_terminal import parse_sienna_voltage_control_terminal
from VeraGridEngine.IO.sienna.devices.operations.supplemental_attributes.voltage_droop_control import parse_sienna_voltage_droop_control
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.inner_control.voltage_mode_control import parse_sienna_voltage_mode_control
from VeraGridEngine.IO.sienna.devices.operations.common.voltage_unit_basis import parse_sienna_voltage_unit_basis
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_generator_component.turbine_gov.wpidhy import parse_sienna_wpidhy
from VeraGridEngine.IO.sienna.devices.dynamics.dynamic_inverter_component.dc_source.zero_order_bess import parse_sienna_zero_order_bess


def get_sienna_object_parsers() -> dict[SiennaObjectKind, Callable[[dict[str, Any]], object]]:
    """Return the parser registry for the pinned Sienna v0.4 catalog.

    :return: Parsers indexed by published Sienna schema kind.
    """
    parsers: dict[SiennaObjectKind, SiennaObjectParser] = {
        SiennaObjectKind.ACBus: parse_sienna_ac_bus,
        SiennaObjectKind.ACBusType: parse_sienna_ac_bus_type,
        SiennaObjectKind.AGC: parse_sienna_agc,
        SiennaObjectKind.AVRFixed: parse_sienna_avr_fixed,
        SiennaObjectKind.AVRSimple: parse_sienna_avr_simple,
        SiennaObjectKind.AVRTypeI: parse_sienna_avr_type_i,
        SiennaObjectKind.AVRTypeII: parse_sienna_avr_type_ii,
        SiennaObjectKind.ActivePowerDroop: parse_sienna_active_power_droop,
        SiennaObjectKind.ActivePowerPI: parse_sienna_active_power_pi,
        SiennaObjectKind.ActiveRenewableControllerAB: parse_sienna_active_renewable_controller_ab,
        SiennaObjectKind.ActiveVirtualOscillator: parse_sienna_active_virtual_oscillator,
        SiennaObjectKind.AdmittanceUnitBasis: parse_sienna_admittance_unit_basis,
        SiennaObjectKind.AggregateTransportTechnology: parse_sienna_aggregate_transport_technology,
        SiennaObjectKind.AndersonFouadMachine: parse_sienna_anderson_fouad_machine,
        SiennaObjectKind.Arc: parse_sienna_arc,
        SiennaObjectKind.Area: parse_sienna_area,
        SiennaObjectKind.AreaInterchange: parse_sienna_area_interchange,
        SiennaObjectKind.AverageConverter: parse_sienna_average_converter,
        SiennaObjectKind.AverageRateCurve: parse_sienna_average_rate_curve,
        SiennaObjectKind.BaseMachine: parse_sienna_base_machine,
        SiennaObjectKind.BilateralConfirmation: parse_sienna_bilateral_confirmation,
        SiennaObjectKind.BilateralProduct: parse_sienna_bilateral_product,
        SiennaObjectKind.BilateralTransaction: parse_sienna_bilateral_transaction,
        SiennaObjectKind.CapacityReserveMargin: parse_sienna_capacity_reserve_margin,
        SiennaObjectKind.CapitalCost: parse_sienna_capital_cost,
        SiennaObjectKind.CarbonCaps: parse_sienna_carbon_caps,
        SiennaObjectKind.CarbonTax: parse_sienna_carbon_tax,
        SiennaObjectKind.ChargeDischarge: parse_sienna_charge_discharge,
        SiennaObjectKind.ColocatedSupplyStorageTechnology: parse_sienna_colocated_supply_storage_technology,
        SiennaObjectKind.CombinedCycleAssociation: parse_sienna_combined_cycle_association,
        SiennaObjectKind.CombinedCycleBlock: parse_sienna_combined_cycle_block,
        SiennaObjectKind.CombinedCycleConfiguration: parse_sienna_combined_cycle_configuration,
        SiennaObjectKind.CombinedCycleFractional: parse_sienna_combined_cycle_fractional,
        SiennaObjectKind.CommitmentModes: parse_sienna_commitment_modes,
        SiennaObjectKind.ComplexNumber: parse_sienna_complex_number,
        SiennaObjectKind.CostCurve: parse_sienna_cost_curve,
        SiennaObjectKind.CurrentLossCurve: parse_sienna_current_loss_curve,
        SiennaObjectKind.CurrentModeControl: parse_sienna_current_mode_control,
        SiennaObjectKind.CurveMultiStep: parse_sienna_curve_multi_step,
        SiennaObjectKind.CurveStyles: parse_sienna_curve_styles,
        SiennaObjectKind.DCBus: parse_sienna_dc_bus,
        SiennaObjectKind.DEGOV: parse_sienna_degov,
        SiennaObjectKind.DEGOV1: parse_sienna_degov1,
        SiennaObjectKind.DataSource: parse_sienna_data_source,
        SiennaObjectKind.DbdPnts: parse_sienna_dbd_pnts,
        SiennaObjectKind.DemandRequirement: parse_sienna_demand_requirement,
        SiennaObjectKind.DemandSideTechnology: parse_sienna_demand_side_technology,
        SiennaObjectKind.Deterministic: parse_sienna_deterministic,
        SiennaObjectKind.DeterministicSingleTimeSeries: parse_sienna_deterministic_single_time_series,
        SiennaObjectKind.DiscreteControlledACBranch: parse_sienna_discrete_controlled_ac_branch,
        SiennaObjectKind.ESAC1A: parse_sienna_esac1_a,
        SiennaObjectKind.ESAC6A: parse_sienna_esac6_a,
        SiennaObjectKind.ESAC8B: parse_sienna_esac8_b,
        SiennaObjectKind.ESDC1A: parse_sienna_esdc1_a,
        SiennaObjectKind.ESDC2A: parse_sienna_esdc2_a,
        SiennaObjectKind.ESST1A: parse_sienna_esst1_a,
        SiennaObjectKind.ESST4B: parse_sienna_esst4_b,
        SiennaObjectKind.EX4VSA: parse_sienna_ex4_vsa,
        SiennaObjectKind.EXAC1: parse_sienna_exac1,
        SiennaObjectKind.EXAC1A: parse_sienna_exac1_a,
        SiennaObjectKind.EXAC2: parse_sienna_exac2,
        SiennaObjectKind.EXPIC1: parse_sienna_expic1,
        SiennaObjectKind.EXST1: parse_sienna_exst1,
        SiennaObjectKind.ElementType: parse_sienna_element_type,
        SiennaObjectKind.EmissionBasis: parse_sienna_emission_basis,
        SiennaObjectKind.EmissionsData: parse_sienna_emissions_data,
        SiennaObjectKind.EnergyReservoirStorage: parse_sienna_energy_reservoir_storage,
        SiennaObjectKind.EnergyShareRequirements: parse_sienna_energy_share_requirements,
        SiennaObjectKind.EnergyUnit: parse_sienna_energy_unit,
        SiennaObjectKind.EnergyUnitBasis: parse_sienna_energy_unit_basis,
        SiennaObjectKind.ExistingDevices: parse_sienna_existing_devices,
        SiennaObjectKind.ExponentialLoad: parse_sienna_exponential_load,
        SiennaObjectKind.FACTSControlDevice: parse_sienna_facts_control_device,
        SiennaObjectKind.FACTSControlDeviceControlMode: parse_sienna_facts_control_device_control_mode,
        SiennaObjectKind.FdbdPnts: parse_sienna_fdbd_pnts,
        SiennaObjectKind.FiveMassShaft: parse_sienna_five_mass_shaft,
        SiennaObjectKind.FixedAdmittance: parse_sienna_fixed_admittance,
        SiennaObjectKind.FixedDCSource: parse_sienna_fixed_dc_source,
        SiennaObjectKind.FixedForcedOutage: parse_sienna_fixed_forced_outage,
        SiennaObjectKind.FixedFrequency: parse_sienna_fixed_frequency,
        SiennaObjectKind.FromTo: parse_sienna_from_to,
        SiennaObjectKind.FromTo_ToFrom: parse_sienna_from_to_to_from,
        SiennaObjectKind.FuelCurve: parse_sienna_fuel_curve,
        SiennaObjectKind.FuelUnit: parse_sienna_fuel_unit,
        SiennaObjectKind.FullMachine: parse_sienna_full_machine,
        SiennaObjectKind.FunctionData: parse_sienna_function_data,
        SiennaObjectKind.GasTG: parse_sienna_gas_tg,
        SiennaObjectKind.GeneralGovModel: parse_sienna_general_gov_model,
        SiennaObjectKind.GenericArcImpedance: parse_sienna_generic_arc_impedance,
        SiennaObjectKind.GenericOperationCost: parse_sienna_generic_operation_cost,
        SiennaObjectKind.GeographicInfo: parse_sienna_geographic_info,
        SiennaObjectKind.GeometricDistributionForcedOutage: parse_sienna_geometric_distribution_forced_outage,
        SiennaObjectKind.GroupReserve: parse_sienna_group_reserve,
        SiennaObjectKind.HourlyMatching: parse_sienna_hourly_matching,
        SiennaObjectKind.HybridOutputCurrentLimiter: parse_sienna_hybrid_output_current_limiter,
        SiennaObjectKind.HybridSystem: parse_sienna_hybrid_system,
        SiennaObjectKind.HydroDispatch: parse_sienna_hydro_dispatch,
        SiennaObjectKind.HydroGenerationCost: parse_sienna_hydro_generation_cost,
        SiennaObjectKind.HydroPowerPlant: parse_sienna_hydro_power_plant,
        SiennaObjectKind.HydroPumpTurbine: parse_sienna_hydro_pump_turbine,
        SiennaObjectKind.HydroReservoir: parse_sienna_hydro_reservoir,
        SiennaObjectKind.HydroReservoirCost: parse_sienna_hydro_reservoir_cost,
        SiennaObjectKind.HydroStorageGenerationCost: parse_sienna_hydro_storage_generation_cost,
        SiennaObjectKind.HydroTurbine: parse_sienna_hydro_turbine,
        SiennaObjectKind.HydroTurbineGov: parse_sienna_hydro_turbine_gov,
        SiennaObjectKind.IEEEST: parse_sienna_ieeest,
        SiennaObjectKind.IEEET1: parse_sienna_ieeet1,
        SiennaObjectKind.IEEETurbineGov1: parse_sienna_ieee_turbine_gov1,
        SiennaObjectKind.ImpedanceCorrectionData: parse_sienna_impedance_correction_data,
        SiennaObjectKind.ImpedanceUnitBasis: parse_sienna_impedance_unit_basis,
        SiennaObjectKind.ImportExportCost: parse_sienna_import_export_cost,
        SiennaObjectKind.ImportExportTimeSeriesCost: parse_sienna_import_export_time_series_cost,
        SiennaObjectKind.InOut: parse_sienna_in_out,
        SiennaObjectKind.IncrementalCurve: parse_sienna_incremental_curve,
        SiennaObjectKind.InputOutputCurve: parse_sienna_input_output_curve,
        SiennaObjectKind.InstantaneousOutputCurrentLimiter: parse_sienna_instantaneous_output_current_limiter,
        SiennaObjectKind.InterconnectingConverter: parse_sienna_interconnecting_converter,
        SiennaObjectKind.InterruptiblePowerLoad: parse_sienna_interruptible_power_load,
        SiennaObjectKind.InterruptibleStandardLoad: parse_sienna_interruptible_standard_load,
        SiennaObjectKind.IntervalAlignment: parse_sienna_interval_alignment,
        SiennaObjectKind.KauraPLL: parse_sienna_kaura_pll,
        SiennaObjectKind.LCCControlMode: parse_sienna_lcc_control_mode,
        SiennaObjectKind.LCFilter: parse_sienna_lc_filter,
        SiennaObjectKind.LCLFilter: parse_sienna_lcl_filter,
        SiennaObjectKind.Line: parse_sienna_line,
        SiennaObjectKind.LinearFunctionData: parse_sienna_linear_function_data,
        SiennaObjectKind.LoadConformity: parse_sienna_load_conformity,
        SiennaObjectKind.LoadCost: parse_sienna_load_cost,
        SiennaObjectKind.LoadZone: parse_sienna_load_zone,
        SiennaObjectKind.LossCurve: parse_sienna_loss_curve,
        SiennaObjectKind.LossValueCurve: parse_sienna_loss_value_curve,
        SiennaObjectKind.MagnitudeOutputCurrentLimiter: parse_sienna_magnitude_output_current_limiter,
        SiennaObjectKind.MarconatoMachine: parse_sienna_marconato_machine,
        SiennaObjectKind.MarketBidCost: parse_sienna_market_bid_cost,
        SiennaObjectKind.MarketBidTimeSeriesCost: parse_sienna_market_bid_time_series_cost,
        SiennaObjectKind.MarketStage: parse_sienna_market_stage,
        SiennaObjectKind.MassUnit: parse_sienna_mass_unit,
        SiennaObjectKind.MaximumCapacityRequirements: parse_sienna_maximum_capacity_requirements,
        SiennaObjectKind.MinMax: parse_sienna_min_max,
        SiennaObjectKind.MinMaxByKey: parse_sienna_min_max_by_key,
        SiennaObjectKind.MinimumCapacityRequirements: parse_sienna_minimum_capacity_requirements,
        SiennaObjectKind.MotorLoad: parse_sienna_motor_load,
        SiennaObjectKind.NodalACTransportTechnology: parse_sienna_nodal_ac_transport_technology,
        SiennaObjectKind.NodalHVDCTransportTechnology: parse_sienna_nodal_hvdc_transport_technology,
        SiennaObjectKind.NonSequentialTimeSeries: parse_sienna_non_sequential_time_series,
        SiennaObjectKind.OfflineReserve: parse_sienna_offline_reserve,
        SiennaObjectKind.OneDOneQMachine: parse_sienna_one_d_one_q_machine,
        SiennaObjectKind.OnlineReserve: parse_sienna_online_reserve,
        SiennaObjectKind.OperationalFlowLimit: parse_sienna_operational_flow_limit,
        SiennaObjectKind.OperationalStates: parse_sienna_operational_states,
        SiennaObjectKind.OutageFactors: parse_sienna_outage_factors,
        SiennaObjectKind.OwnerCategory: parse_sienna_owner_category,
        SiennaObjectKind.PIDGOV: parse_sienna_pidgov,
        SiennaObjectKind.PSS2A: parse_sienna_pss2_a,
        SiennaObjectKind.PSS2B: parse_sienna_pss2_b,
        SiennaObjectKind.PSS2C: parse_sienna_pss2_c,
        SiennaObjectKind.PSSFixed: parse_sienna_pss_fixed,
        SiennaObjectKind.PSSSimple: parse_sienna_pss_simple,
        SiennaObjectKind.Period: parse_sienna_period,
        SiennaObjectKind.PiecewiseLinearData: parse_sienna_piecewise_linear_data,
        SiennaObjectKind.PiecewiseStepData: parse_sienna_piecewise_step_data,
        SiennaObjectKind.PlannedOutage: parse_sienna_planned_outage,
        SiennaObjectKind.PlantAssociation: parse_sienna_plant_association,
        SiennaObjectKind.PointToPointBid: parse_sienna_point_to_point_bid,
        SiennaObjectKind.PollutantType: parse_sienna_pollutant_type,
        SiennaObjectKind.PortfolioFinancialData: parse_sienna_portfolio_financial_data,
        SiennaObjectKind.PowerLoad: parse_sienna_power_load,
        SiennaObjectKind.PrimeMovers: parse_sienna_prime_movers,
        SiennaObjectKind.PriorityOutputCurrentLimiter: parse_sienna_priority_output_current_limiter,
        SiennaObjectKind.Probabilistic: parse_sienna_probabilistic,
        SiennaObjectKind.ProductionVariableCostCurve: parse_sienna_production_variable_cost_curve,
        SiennaObjectKind.QuadraticFunctionData: parse_sienna_quadratic_function_data,
        SiennaObjectKind.RECurrentControlB: parse_sienna_re_current_control_b,
        SiennaObjectKind.RLFilter: parse_sienna_rl_filter,
        SiennaObjectKind.ReactivePowerDroop: parse_sienna_reactive_power_droop,
        SiennaObjectKind.ReactivePowerPI: parse_sienna_reactive_power_pi,
        SiennaObjectKind.ReactivePowerSharing: parse_sienna_reactive_power_sharing,
        SiennaObjectKind.ReactiveRenewableControllerAB: parse_sienna_reactive_renewable_controller_ab,
        SiennaObjectKind.ReactiveVirtualOscillator: parse_sienna_reactive_virtual_oscillator,
        SiennaObjectKind.ReducedOrderPLL: parse_sienna_reduced_order_pll,
        SiennaObjectKind.RenewableDispatch: parse_sienna_renewable_dispatch,
        SiennaObjectKind.RenewableEnergyConverterTypeA: parse_sienna_renewable_energy_converter_type_a,
        SiennaObjectKind.RenewableEnergyVoltageConverterTypeA: parse_sienna_renewable_energy_voltage_converter_type_a,
        SiennaObjectKind.RenewableGenerationCost: parse_sienna_renewable_generation_cost,
        SiennaObjectKind.RenewableNonDispatch: parse_sienna_renewable_non_dispatch,
        SiennaObjectKind.RenewablePowerPlant: parse_sienna_renewable_power_plant,
        SiennaObjectKind.RequirementAssociation: parse_sienna_requirement_association,
        SiennaObjectKind.ReserveDirection: parse_sienna_reserve_direction,
        SiennaObjectKind.ReservoirLocation: parse_sienna_reservoir_location,
        SiennaObjectKind.RetirementPotential: parse_sienna_retirement_potential,
        SiennaObjectKind.RetrofitPotential: parse_sienna_retrofit_potential,
        SiennaObjectKind.RoundRotorExponential: parse_sienna_round_rotor_exponential,
        SiennaObjectKind.RoundRotorMachine: parse_sienna_round_rotor_machine,
        SiennaObjectKind.RoundRotorQuadratic: parse_sienna_round_rotor_quadratic,
        SiennaObjectKind.SCRX: parse_sienna_scrx,
        SiennaObjectKind.SEXS: parse_sienna_sexs,
        SiennaObjectKind.ST6B: parse_sienna_st6_b,
        SiennaObjectKind.ST8C: parse_sienna_st8_c,
        SiennaObjectKind.STAB1: parse_sienna_stab1,
        SiennaObjectKind.SalientPoleExponential: parse_sienna_salient_pole_exponential,
        SiennaObjectKind.SalientPoleMachine: parse_sienna_salient_pole_machine,
        SiennaObjectKind.SalientPoleQuadratic: parse_sienna_salient_pole_quadratic,
        SiennaObjectKind.SaturationOutputCurrentLimiter: parse_sienna_saturation_output_current_limiter,
        SiennaObjectKind.SauerPaiMachine: parse_sienna_sauer_pai_machine,
        SiennaObjectKind.Scenarios: parse_sienna_scenarios,
        SiennaObjectKind.SeriesCompensator: parse_sienna_series_compensator,
        SiennaObjectKind.SeriesCompensatorControlMode: parse_sienna_series_compensator_control_mode,
        SiennaObjectKind.ServiceAssociation: parse_sienna_service_association,
        SiennaObjectKind.ShiftablePowerLoad: parse_sienna_shiftable_power_load,
        SiennaObjectKind.ShuntAdmittanceUnitBasis: parse_sienna_shunt_admittance_unit_basis,
        SiennaObjectKind.SimpleAFMachine: parse_sienna_simple_af_machine,
        SiennaObjectKind.SimpleFullMachine: parse_sienna_simple_full_machine,
        SiennaObjectKind.SimpleMarconatoMachine: parse_sienna_simple_marconato_machine,
        SiennaObjectKind.SingleMass: parse_sienna_single_mass,
        SiennaObjectKind.SingleTimeSeries: parse_sienna_single_time_series,
        SiennaObjectKind.Source: parse_sienna_source,
        SiennaObjectKind.StandardLoad: parse_sienna_standard_load,
        SiennaObjectKind.StartUpShutDown: parse_sienna_start_up_shut_down,
        SiennaObjectKind.StartUpStages: parse_sienna_start_up_stages,
        SiennaObjectKind.SteamTurbineGov1: parse_sienna_steam_turbine_gov1,
        SiennaObjectKind.StorageCapitalCost: parse_sienna_storage_capital_cost,
        SiennaObjectKind.StorageCost: parse_sienna_storage_cost,
        SiennaObjectKind.StorageTech: parse_sienna_storage_tech,
        SiennaObjectKind.StorageTechnology: parse_sienna_storage_technology,
        SiennaObjectKind.Substation: parse_sienna_substation,
        SiennaObjectKind.SupplementalAttributeAssociation: parse_sienna_supplemental_attribute_association,
        SiennaObjectKind.SupplyTechnology: parse_sienna_supply_technology,
        SiennaObjectKind.SwitchedAdmittance: parse_sienna_switched_admittance,
        SiennaObjectKind.SwitchedAdmittanceControlMode: parse_sienna_switched_admittance_control_mode,
        SiennaObjectKind.SynchronousCondenser: parse_sienna_synchronous_condenser,
        SiennaObjectKind.TGFixed: parse_sienna_tg_fixed,
        SiennaObjectKind.TGSimple: parse_sienna_tg_simple,
        SiennaObjectKind.TGTypeI: parse_sienna_tg_type_i,
        SiennaObjectKind.TGTypeII: parse_sienna_tg_type_ii,
        SiennaObjectKind.TModelHVDCLine: parse_sienna_t_model_hvdc_line,
        SiennaObjectKind.TechnologyFinancialData: parse_sienna_technology_financial_data,
        SiennaObjectKind.ThermalFuels: parse_sienna_thermal_fuels,
        SiennaObjectKind.ThermalGenerationCost: parse_sienna_thermal_generation_cost,
        SiennaObjectKind.ThermalMultiStart: parse_sienna_thermal_multi_start,
        SiennaObjectKind.ThermalPowerPlant: parse_sienna_thermal_power_plant,
        SiennaObjectKind.ThermalStandard: parse_sienna_thermal_standard,
        SiennaObjectKind.ThreeWindingTransformer: parse_sienna_three_winding_transformer,
        SiennaObjectKind.ThreeWindingTransformerShuntLocation: parse_sienna_three_winding_transformer_shunt_location,
        SiennaObjectKind.TimeReference: parse_sienna_time_reference,
        SiennaObjectKind.TimeSeriesAssociation: parse_sienna_time_series_association,
        SiennaObjectKind.TimeSeriesAverageRateCurve: parse_sienna_time_series_average_rate_curve,
        SiennaObjectKind.TimeSeriesFeatureValue: parse_sienna_time_series_feature_value,
        SiennaObjectKind.TimeSeriesFeatures: parse_sienna_time_series_features,
        SiennaObjectKind.TimeSeriesIncrementalCurve: parse_sienna_time_series_incremental_curve,
        SiennaObjectKind.TimeSeriesInputOutputCurve: parse_sienna_time_series_input_output_curve,
        SiennaObjectKind.TimeSeriesLinearFunctionData: parse_sienna_time_series_linear_function_data,
        SiennaObjectKind.TimeSeriesPiecewiseLinearData: parse_sienna_time_series_piecewise_linear_data,
        SiennaObjectKind.TimeSeriesPiecewiseStepData: parse_sienna_time_series_piecewise_step_data,
        SiennaObjectKind.TimeSeriesQuadraticFunctionData: parse_sienna_time_series_quadratic_function_data,
        SiennaObjectKind.TradingHub: parse_sienna_trading_hub,
        SiennaObjectKind.TradingHubAssociation: parse_sienna_trading_hub_association,
        SiennaObjectKind.TransformerCircuit: parse_sienna_transformer_circuit,
        SiennaObjectKind.TransformerControlObjective: parse_sienna_transformer_control_objective,
        SiennaObjectKind.TransmissionInterface: parse_sienna_transmission_interface,
        SiennaObjectKind.TurbinePump: parse_sienna_turbine_pump,
        SiennaObjectKind.TwoDimensionalFunctionPoint: parse_sienna_two_dimensional_function_point,
        SiennaObjectKind.TwoTerminalGenericHVDCLine: parse_sienna_two_terminal_generic_hvdc_line,
        SiennaObjectKind.TwoTerminalLCCLine: parse_sienna_two_terminal_lcc_line,
        SiennaObjectKind.TwoTerminalVSCLine: parse_sienna_two_terminal_vsc_line,
        SiennaObjectKind.TwoWindingTransformer: parse_sienna_two_winding_transformer,
        SiennaObjectKind.TwoWindingTransformerShuntLocation: parse_sienna_two_winding_transformer_shunt_location,
        SiennaObjectKind.UnitSystem: parse_sienna_unit_system,
        SiennaObjectKind.UpDown: parse_sienna_up_down,
        SiennaObjectKind.VSCACControlModes: parse_sienna_vscac_control_modes,
        SiennaObjectKind.VSCDCControlModes: parse_sienna_vscdc_control_modes,
        SiennaObjectKind.ValueCurve: parse_sienna_value_curve,
        SiennaObjectKind.VirtualInertia: parse_sienna_virtual_inertia,
        SiennaObjectKind.VirtualParticipant: parse_sienna_virtual_participant,
        SiennaObjectKind.VoltageControlAssociation: parse_sienna_voltage_control_association,
        SiennaObjectKind.VoltageControlTerminal: parse_sienna_voltage_control_terminal,
        SiennaObjectKind.VoltageDroopControl: parse_sienna_voltage_droop_control,
        SiennaObjectKind.VoltageModeControl: parse_sienna_voltage_mode_control,
        SiennaObjectKind.VoltageUnitBasis: parse_sienna_voltage_unit_basis,
        SiennaObjectKind.WPIDHY: parse_sienna_wpidhy,
        SiennaObjectKind.ZeroOrderBESS: parse_sienna_zero_order_bess,
    }
    return parsers


def get_sienna_object_parser(kind: SiennaObjectKind) -> Callable[[dict[str, Any]], object]:
    """Return the parser for one known Sienna schema object kind.

    :param kind: Published Sienna object kind.
    :return: Registered typed object parser.
    """
    parsers: dict[SiennaObjectKind, Callable[[dict[str, Any]], object]] = get_sienna_object_parsers()
    parser: Callable[[dict[str, Any]], object] | None = parsers.get(kind, None)
    if parser is None:
        raise ValueError(f"No Sienna object parser is registered for {kind.name}")
    else:
        return parser
