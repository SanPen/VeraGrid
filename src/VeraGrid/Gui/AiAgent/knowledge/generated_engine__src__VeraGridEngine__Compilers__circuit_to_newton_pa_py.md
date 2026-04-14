# VeraGridEngine Module: src/VeraGridEngine/Compilers/circuit_to_newton_pa.py

- Original source path: `src/VeraGridEngine/Compilers/circuit_to_newton_pa.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 37
- Representative imports: __future__, os.path, warnings, numpy, typing, VeraGridEngine.basic_structures, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.enumerations, VeraGridEngine.Devices, VeraGridEngine.Simulations.PowerFlow.power_flow_options, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.IO.file_system, VeraGridEngine.basic_structures

## Function: get_newton_mip_solvers_list()

Get list of available MIP solvers

## Function: get_final_profile(time_series, time_indices, profile, ntime, default_val, dtype)

Generates a default time series

## Function: add_npa_areas(circuit, npa_circuit, n_time)

Add Newton Areas

## Function: add_npa_zones(circuit, npa_circuit, n_time)

Add Newton Zones

## Function: add_npa_contingency_groups(circuit, npa_circuit, n_time)

Add Newton ContingenciesGroup

## Function: add_npa_contingencies(circuit, npa_circuit, n_time, groups_dict)

Add Newton ContingenciesGroup

## Function: add_npa_investment_groups(circuit, npa_circuit, n_time)

:param circuit:

## Function: add_npa_investments(circuit, npa_circuit, n_time, groups_dict)

:param circuit:

## Function: add_npa_buses(circuit, npa_circuit, time_series, n_time, time_indices, area_dict)

Convert the buses to Newton buses

## Function: add_npa_loads(circuit, npa_circuit, bus_dict, time_series, n_time, time_indices, opf_results)

:param circuit: VeraGrid circuit

## Function: add_npa_static_generators(circuit, npa_circuit, bus_dict, time_series, n_time, time_indices)

:param circuit: VeraGrid circuit

## Function: add_npa_shunts(circuit, npa_circuit, bus_dict, time_series, n_time, time_indices)

:param circuit: VeraGrid circuit

## Function: add_npa_generators(circuit, npa_circuit, bus_dict, time_series, n_time, time_indices, opf_results)

:param circuit: VeraGrid circuit

## Function: add_battery_data(circuit, npa_circuit, bus_dict, time_series, n_time, time_indices, opf_results)

:param circuit: VeraGrid circuit

## Function: add_npa_line(circuit, npa_circuit, bus_dict, time_series, n_time, time_indices)

:param circuit: VeraGrid circuit

## Function: add_transformer_data(circuit, npa_circuit, bus_dict, time_series, n_time, time_indices, override_controls)

:param circuit: VeraGrid circuit

## Function: add_transformer3w_data(circuit, npa_circuit, bus_dict, time_series, n_time, time_indices, override_controls)

:param circuit: VeraGrid circuit

## Function: add_vsc_data(circuit, npa_circuit, bus_dict, time_series, n_time, time_indices)

:param circuit: VeraGrid circuit

## Function: add_dc_line_data(circuit, npa_circuit, bus_dict, time_series, n_time, time_indices)

:param circuit: VeraGrid circuit

## Function: add_hvdc_data(circuit, npa_circuit, bus_dict, time_series, n_time, time_indices)

:param circuit: VeraGrid circuit

## Function: to_newton_pa(circuit, use_time_series, time_indices, override_branch_controls, opf_results)

Convert VeraGrid circuit to Newton

## Class: FakeAdmittances

- Bases: none
- Summary: Fake admittances class needed to make the translation

### Methods

- No methods detected.

## Function: get_snapshots_from_newtonpa(circuit, override_branch_controls)

:param circuit:

## Function: get_newton_pa_pf_options(opt)

Translate VeraGrid power flow options to Newton power flow options

## Function: get_newton_pa_linear_options(opt)

Translate VeraGrid power flow options to Newton power flow options

## Function: get_newton_pa_nonlinear_opf_options(pf_opt, opf_opt)

Translate VeraGrid power flow options to Newton power flow options

## Function: get_newton_pa_linear_opf_options(opf_opt, pf_opt, area_dict)

Translate VeraGrid power flow options to Newton power flow options

## Function: newton_pa_pf(circuit, pf_opt, time_series, time_indices, opf_results)

Newton power flow

## Function: newton_pa_contingencies(circuit, con_opt, time_series, time_indices)

Newton power flow

## Function: newton_pa_linear_opf(circuit, opf_options, pf_opt, time_series, time_indices)

Newton power flow

## Function: newton_pa_nonlinear_opf(circuit, pf_opt, opf_opt, time_series, time_indices)

Newton power flow

## Function: newton_pa_linear_matrices(circuit, distributed_slack, override_branch_controls)

Newton linear analysis

## Function: convert_bus_types(arr)

Convert list of Newton bus types to an array of VeraGrid compatible bus type integers

## Function: translate_newton_pa_pf_results(grid, res)

Translate the Newton Power Analytics results back to VeraGrid

## Function: translate_newton_pa_opf_results(grid, res)

Translate Newton OPF results to VeraGrid

## Function: translate_contingency_report(newton_report, veragrid_report)

Translate contingency report

## Function: translate_newton_pa_contingencies(grid, con_res)

:param grid:

## Function: debug_newton_pa_circuit_at(npa_circuit, t)

Debugging function
