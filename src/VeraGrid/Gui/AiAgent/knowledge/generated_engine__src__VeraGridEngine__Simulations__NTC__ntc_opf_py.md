# VeraGridEngine Module: src/VeraGridEngine/Simulations/NTC/ntc_opf.py

- Original source path: `src/VeraGridEngine/Simulations/NTC/ntc_opf.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

This file implements a DC-OPF for time series

## Module Surface

- Class count: 8
- Top-level function count: 20
- Representative imports: __future__, os, numpy, typing, VeraGridEngine.enumerations, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Devices.Aggregation.contingency_group, VeraGridEngine.Compilers.circuit_to_data, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.DataStructures.generator_data, VeraGridEngine.DataStructures.battery_data, VeraGridEngine.DataStructures.load_data, VeraGridEngine.DataStructures.passive_branch_data, VeraGridEngine.DataStructures.active_branch_data, VeraGridEngine.DataStructures.hvdc_data, VeraGridEngine.DataStructures.vsc_data

## Function: formulate_monitorization_logic(monitor_only_sensitive_branches, monitor_only_ntc_load_rule_branches, monitor_loading, alpha, alpha_n1, branch_sensitivity_threshold, base_flows, structural_ntc, ntc_load_rule, rates)

Function to formulate branch monitor status due the given logic

## Function: get_transfer_power_scaling_per_bus(bus_data_t, gen_data_t, load_data_t, transfer_method, skip_generation_limits, inf_value, Sbase)

Get nodal power, nodal pmax and nodal pmin according to the transfer_method.

## Function: get_sensed_proportions(power, idx, logger)

:param power:

## Function: get_exchange_proportions(power, bus_a1_idx, bus_a2_idx, logger, decimals)

Get generation proportions by transfer method with sign consideration.

## Function: pmode3_formulation(prob, t_idx, m, rate, P0, droop, theta_f, theta_t)

Formulation

## Function: pmode3_formulation2(prob, t_idx, m, rate, P0, droop, theta_f, theta_t, base_name)

Formulation

## Function: pmode3_formulation3(prob, t_idx, m, rate, P0, droop, theta_f, theta_t, base_name)

Formulation

## Function: pmode3_formulation_impr(prob, t_idx, m, rate, P0, droop, theta_f, theta_t, base_name)

Formulation for HVDC link with three operating regions using big-M and binary variables.

## Function: pmode3_formulation_convex_hull(prob, t_idx, m, rate, P0, droop, theta_f, theta_t, f_obj, dtheta_max, base_name)

Convex-hull (Balas) formulation for HVDC Pmode3.

## Function: formulate_lp_abs_value(prob, lp_var, ub, M, name)

Generic function to compute lp abs variable

## Function: formulate_lp_piece_wise(solver, lp_var, higher_exp, lower_exp, condition, name, M)

Generic function to implement piece wise linear function

## Function: formulate_hvdc_Pmode3_single_flow(solver, active, P0, rate, Sbase, angle_droop, angle_max_f, angle_max_t, suffix, angle_f, angle_t, inf)

Formulate the HVDC flow

## Class: BusNtcVars

- Bases: none
- Summary: Struct to store the bus related vars

### Methods

- `get_values(self, Sbase, model)`
  Summary: Return an instance of this class where the arrays content are not LP vars but their value

## Class: LoadVars

- Bases: none
- Summary: Struct to store the load related vars

### Methods

- `get_values(self, Sbase, model)`
  Summary: Return an instance of this class where the arrays content are not LP vars but their value

## Class: GenerationVars

- Bases: none
- Summary: Struct to store the generation vars

### Methods

- `get_values(self, Sbase, model)`
  Summary: Return an instance of this class where the arrays content are not LP vars but their value

## Class: BatteryVars

- Bases: GenerationVars
- Summary: struct extending the generation vars to handle the battery vars

### Methods

- `get_values(self, Sbase, model)`
  Summary: Return an instance of this class where the arrays content are not LP vars but their value

## Class: BranchNtcVars

- Bases: none
- Summary: Struct to store the branch related vars

### Methods

- `get_values(self, Sbase, model)`
  Summary: Return an instance of this class where the arrays content are not LP vars but their value
- `add_contingency_flow(self, t, m, c, flow_var, neg_slack, pos_slack)`
  Summary: Add contingency flow
- `get_total_flow_slack(self)`
  Summary: Get total flow slacks

## Class: HvdcNtcVars

- Bases: none
- Summary: Struct to store the generation vars

### Methods

- `get_values(self, Sbase, model)`
  Summary: Return an instance of this class where the arrays content are not LP vars but their value

## Class: VscNtcVars

- Bases: none
- Summary: Struct to store the VSC vars

### Methods

- `get_values(self, Sbase, model)`
  Summary: Return an instance of this class where the arrays content are not LP vars but their value

## Class: NtcVars

- Bases: none
- Summary: Structure to host the opf variables

### Methods

- `get_values(self, Sbase, model)`
  Summary: Return an instance of this class where the arrays content are not LP vars but their value
- `get_voltages(self)`
  Summary: :return:
- `check_kirchhoff(self, tol)`
  Summary: :param tol:

## Function: get_base_power(Sbase, gen_data_t, batt_data_t, load_data_t, branch_data_t, active_branch_data_t, hvdc_data_t, logger)

Get the perfectly balanced base power

## Function: add_linear_injections_formulation(t, Sbase, gen_data_t, batt_data_t, load_data_t, bus_data_t, branch_data_t, active_branch_data_t, hvdc_data_t, bus_a1_idx, bus_a2_idx, transfer_method, skip_generation_limits, ntc_vars, prob, logger)

Add MIP injections formulation

## Function: add_linear_branches_formulation(t_idx, Sbase, branch_data_t, active_branch_data_t, branch_vars, bus_vars, prob, monitor_only_sensitive_branches, monitor_only_ntc_load_rule_branches, alpha, alpha_threshold, structural_ntc, ntc_load_rule, loading, logger, inf)

Formulate the branches

## Function: add_linear_branches_contingencies_formulation(t_idx, Sbase, branch_data_t, branch_vars, bus_vars, hvdc_vars, vsc_vars, prob, linear_multi_contingencies, monitor_only_ntc_load_rule_branches, monitor_only_sensitive_branches, structural_ntc, ntc_load_rule, alpha_threshold, alpha_n1, base_loading, con_loading, logger)

Formulate the branches

## Function: add_linear_hvdc_formulation(t_idx, Sbase, hvdc_data_t, hvdc_vars, vars_bus, prob, logger, saturate)

:param t_idx:

## Function: add_linear_vsc_formulation(t_idx, Sbase, vsc_data_t, vsc_vars, bus_vars, prob, logger, saturate)

:param t_idx:

## Function: add_linear_node_balance(t_idx, vd, bus_data, bus_vars, prob, logger)

Add the kirchhoff nodal equality

## Function: run_linear_ntc_opf(grid, t, solver_type, zonal_grouping, skip_generation_limits, consider_contingencies, contingency_groups_used, alpha_threshold, lodf_threshold, bus_a1_idx, bus_a2_idx, transfer_method, monitor_only_sensitive_branches, monitor_only_ntc_load_rule_branches, ntc_load_rule, logger, progress_text, progress_func, verbose, robust, mip_framework)

:param grid: MultiCircuit instance
