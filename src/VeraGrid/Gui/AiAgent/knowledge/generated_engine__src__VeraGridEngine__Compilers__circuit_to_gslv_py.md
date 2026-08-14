# VeraGridEngine Module: src/VeraGridEngine/Compilers/circuit_to_gslv.py

- Original source path: `src/VeraGridEngine/Compilers/Gslv`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 76
- Representative imports: __future__, time, numpy, typing, VeraGridEngine, VeraGridEngine.Utils.ThirdParty.gslv.gslv_activation, VeraGridEngine.DataStructures.branch_parent_data, VeraGridEngine.basic_structures, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Devices, VeraGridEngine.Simulations.PowerFlow.power_flow_options, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.enumerations, VeraGridEngine.enumerations, VeraGridEngine.DataStructures.numerical_circuit

## Function: get_gslv_mip_solvers_list()

Get list of available MIP solvers

## Function: convert_tap_module_control_mode_dict(data)

Function to convert a dictionary of TapModuleControl modes to pg.TapModuleControl modes

## Function: convert_tap_module_control_mode_lst(data)

Function to convert a list of TapModuleControl modes to pg.TapModuleControl modes

## Function: convert_tap_phase_control_mode_dict(data)

Function to convert a dictionary of TapPhaseControl modes to pg.TapPhaseControl modes

## Function: convert_tap_phase_control_mode_lst(data)

Function to convert a list of TapPhaseControl modes to pg.TapPhaseControl modes

## Function: fill_profile(gslv_profile, gc_profile, use_time_series, time_indices, n_time, default_val)

Generates a default time series

## Function: fill_profile_with_array(gslv_profile, arr, use_time_series, time_indices, n_time, default_val)

Generates a default time series

## Function: convert_area(area)

:param area:

## Function: add_areas(circuit, gslv_grid)

Add GSLV Areas

## Function: convert_zone(zone)

:param zone:

## Function: add_zones(circuit, gslv_grid)

Add GSLV Zones

## Function: convert_country(country)

:param country:

## Function: add_countries(circuit, gslv_grid)

Add GSLV countries

## Function: convert_municipality(country)

:param country:

## Function: add_municipalities(circuit, gslv_grid)

Add GSLV countries

## Function: convert_region(country)

:param country:

## Function: add_regions(circuit, gslv_grid)

Add GSLV countries

## Function: convert_branch_group(country)

:param country:

## Function: add_branch_groups(circuit, gslv_grid)

Add GSLV countries

## Function: convert_substation(se, n_time)

:param se:

## Function: add_substations(circuit, gslv_grid, n_time)

Add GSLV substations

## Function: convert_voltage_level(elm, substations_dict)

:param elm:

## Function: add_voltage_levels(circuit, gslv_grid, substations_dict)

Add GSLV substations

## Function: convert_contingency_groups(elm)

:param elm:

## Function: add_contingency_groups(circuit, gslv_grid)

Add GSLV ContingenciesGroup

## Function: convert_contingencies(elm, n_time, groups_dict)

:param elm:

## Function: add_contingencies(circuit, gslv_grid, n_time, groups_dict)

Add GSLV ContingenciesGroup

## Function: convert_investment_group(elm)

:param elm:

## Function: add_investment_groups(circuit, gslv_grid)

:param circuit:

## Function: convert_investment(elm, groups_dict)

:param elm:

## Function: add_investments(circuit, gslv_grid, groups_dict)

:param circuit:

## Function: convert_facility(elm)

:param elm:

## Function: add_facilities(circuit, gslv_grid)

:param circuit:

## Function: convert_modelling_authority(elm)

:param elm:

## Function: add_modelling_authorities(circuit, gslv_grid)

:param circuit:

## Function: convert_bus(elm, n_time, area_dict, zone_dict, substation_dict, voltage_level_dict, country_dict, time_indices, use_time_series)

:param elm:

## Function: add_buses(circuit, gslv_grid, area_dict, zone_dict, substation_dict, voltage_level_dict, country_dict, use_time_series, n_time, time_indices)

Convert the buses to GSLV buses

## Function: convert_load(k, elm, bus_dict, n_time, use_time_series, time_indices, opf_results)

:param k:

## Function: add_loads(circuit, gslv_grid, bus_dict, use_time_series, n_time, time_indices, opf_results)

:param circuit: VeraGrid circuit

## Function: convert_static_generator(elm, bus_dict, n_time, use_time_series, time_indices)

:param elm:

## Function: add_static_generators(circuit, gslv_grid, bus_dict, time_series, n_time, time_indices)

:param circuit: VeraGrid circuit

## Function: convert_shunt(elm, bus_dict, n_time, use_time_series, time_indices)

:param elm:

## Function: add_shunts(circuit, gslv_grid, bus_dict, time_series, n_time, time_indices)

:param circuit: VeraGrid circuit

## Function: convert_controllable_shunt(elm, bus_dict, n_time, use_time_series, shunt_control_mode_dict, time_indices)

:param elm:

## Function: add_controllable_shunts(circuit, gslv_grid, bus_dict, time_series, n_time, time_indices)

:param circuit: VeraGrid circuit

## Function: convert_generator(k, elm, bus_dict, n_time, use_time_series, time_indices, opf_results)

:param k:

## Function: add_generators(circuit, gslv_grid, bus_dict, time_series, n_time, time_indices, opf_results)

:param circuit: VeraGrid circuit

## Function: convert_battery(k, elm, bus_dict, n_time, use_time_series, time_indices, opf_results)

:param k:

## Function: add_battery_data(circuit, gslv_grid, bus_dict, time_series, n_time, time_indices, opf_results)

:param circuit: VeraGrid circuit

## Function: convert_line(elm, n_time, bus_dict, branch_groups_dict, use_time_series, time_indices)

:param elm:

## Function: add_lines(circuit, gslv_grid, bus_dict, branch_groups_dict, time_series, n_time, time_indices)

:param circuit: VeraGrid circuit

## Function: convert_transformer(elm, bus_dict, branch_groups_dict, n_time, use_time_series, time_indices, override_controls)

:param elm:

## Function: add_transformers(circuit, gslv_grid, bus_dict, branch_groups_dict, time_series, n_time, time_indices, override_controls)

:param circuit: VeraGrid circuit

## Function: convert_transformer3w(elm, bus_dict, n_time, use_time_series, time_indices, override_controls)

:param elm:

## Function: add_transformers3w(circuit, gslv_grid, bus_dict, time_series, n_time, time_indices, override_controls)

:param circuit: VeraGrid circuit

## Function: convert_vsc(elm, bus_dict, n_time, use_time_series, time_indices)

:param elm:

## Function: add_vscs(circuit, gslv_grid, bus_dict, time_series, n_time, time_indices)

:param circuit: VeraGrid circuit

## Function: convert_dc_line(elm, bus_dict, n_time, use_time_series, time_indices)

:param elm:

## Function: add_dc_lines(circuit, gslv_grid, bus_dict, time_series, n_time, time_indices)

:param circuit: VeraGrid circuit

## Function: convert_hvdc_line(elm, bus_dict, n_time, use_time_series, time_indices)

:param elm:

## Function: add_hvdcs(circuit, gslv_grid, bus_dict, time_series, n_time, time_indices)

:param circuit: VeraGrid circuit

## Class: GslvDicts

- Bases: none
- Summary: No docstring provided.

### Methods

- No methods detected.

## Function: to_gslv(circuit, use_time_series, time_indices, override_branch_controls, opf_results)

Convert VeraGrid circuit to GSLV

## Class: FakeAdmittances

- Bases: none
- Summary: Fake admittances class needed to make the translation

### Methods

- No methods detected.

## Function: get_snapshots_from_gslv(circuit, override_branch_controls)

:param circuit:

## Function: get_gslv_pf_options(opt)

Translate VeraGrid power flow options to GSLV power flow options

## Function: gslv_pf(circuit, pf_opt, time_series, time_indices, opf_results, logger)

GSLV power flow

## Function: translate_gslv_pf_results(grid, res, logger)

Translate the GSLV Power Analytics results back to VeraGrid

## Function: get_gslv_opf_options(opt, circuit, gslv_circuit)

Translate VeraGrid power flow options to GSLV power flow options

## Function: gslv_opf(circuit, opf_options, time_series, time_indices, logger)

GSLV power flow

## Function: gslv_contingencies_snapshot(circuit, con_opt, opf_results)

GSLV power flow

## Function: gslv_contingencies_ts(circuit, con_opt, time_series, time_indices)

GSLV power flow

## Function: gslv_linear_matrices(circuit, distributed_slack, correctValues, override_branch_controls)

Newton linear analysis

## Function: CheckArr(arr, arr_expected, tol, name, test, verbose)

:param arr:

## Function: CheckArrEq(arr, arr_expected, name, test, verbose)

:param arr:

## Function: convert_arr(arr, d)

No docstring provided.

## Function: compare_branch_parent_data(gslv_branch_data, gc_branch_data, tol, parent_name)

:param gslv_branch_data:

## Function: compare_nc(nc_gslv, nc_gc, tol)

:param nc_gslv:
