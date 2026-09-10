# VeraGridEngine Module: src/VeraGridEngine/Simulations/OPF/Formulations/linear_opf_ts.py

- Original source path: `src/VeraGridEngine/Simulations/OPF/Formulations/linear_opf_ts.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

This file implements a DC-OPF for time series

## Module Surface

- Class count: 13
- Top-level function count: 18
- Representative imports: __future__, os, numpy, typing, scipy.sparse, VeraGridEngine.IO.file_system, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Devices.Aggregation.inter_aggregation_info, VeraGridEngine.Devices.Aggregation.contingency_group, VeraGridEngine.Compilers.circuit_to_data, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.DataStructures.generator_data, VeraGridEngine.DataStructures.battery_data, VeraGridEngine.DataStructures.load_data, VeraGridEngine.DataStructures.passive_branch_data, VeraGridEngine.DataStructures.active_branch_data

## Function: get_contingency_flow_with_filter(multi_contingency, base_flow, injections, threshold, m)

Get contingency flow

## Class: BusVars

- Bases: none
- Summary: Struct to store the bus related vars

### Methods

- `get_values(self, Sbase, model)`
  Summary: Return an instance of this class where the array's content

## Class: NodalCapacityVars

- Bases: none
- Summary: Struct to store the nodal capacity related vars

### Methods

- `get_values(self, Sbase, model)`
  Summary: Return an instance of this class where the array's

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

- `get_values(self, Sbase, model, gen_emissions_rates_matrix, gen_fuel_rates_matrix)`
  Summary: Return an instance of this class where the arrays content are not LP vars but their value

## Class: BatteryVars

- Bases: GenerationVars
- Summary: struct extending the generation vars to handle the battery vars

### Methods

- `get_values(self, Sbase, model, gen_emissions_rates_matrix, gen_fuel_rates_matrix)`
  Summary: Return an instance of this class where the arrays content are not LP vars but their value

## Class: BranchVars

- Bases: none
- Summary: Struct to store the branch related vars

### Methods

- `get_values(self, Sbase, model)`
  Summary: Return an instance of this class where the arrays content are not LP vars but their value
- `add_contingency_flow(self, t, m, c, flow_var, neg_slack, pos_slack)`
  Summary: Add contingency flow

## Class: HvdcVars

- Bases: none
- Summary: Struct to store the generation vars

### Methods

- `get_values(self, Sbase, model)`
  Summary: Return an instance of this class where the arrays content are not LP vars but their value

## Class: VscVars

- Bases: none
- Summary: Struct to store the generation vars

### Methods

- `get_values(self, Sbase, model)`
  Summary: Return an instance of this class where the arrays content are not LP vars but their value

## Class: FluidNodeVars

- Bases: none
- Summary: Struct to store the vars of nodes of fluid type

### Methods

- `get_values(self, model)`
  Summary: Return an instance of this class where the arrays content are not LP vars but their value

## Class: FluidPathVars

- Bases: none
- Summary: Struct to store the vars of paths of fluid type

### Methods

- `get_values(self, model)`
  Summary: Return an instance of this class where the arrays content are not LP vars but their value

## Class: FluidInjectionVars

- Bases: none
- Summary: Struct to store the vars of injections of fluid type

### Methods

- `get_values(self, model)`
  Summary: Return an instance of this class where the arrays content are not LP vars but their value

## Class: SystemVars

- Bases: none
- Summary: Struct to store the system vars

### Methods

- `compute(self, gen_emissions_rates_matrix, gen_fuel_rates_matrix, gen_tech_shares_matrix, batt_tech_shares_matrix, gen_p, gen_cost, batt_p, shedding_cost)`
  Summary: Compute the system values

## Class: OpfVars

- Bases: none
- Summary: Structure to host the opf variables

### Methods

- `get_values(self, Sbase, model, gen_emissions_rates_matrix, gen_fuel_rates_matrix, gen_tech_shares_matrix, batt_tech_shares_matrix)`
  Summary: Return an instance of this class where the arrays content are not LP vars but their value

## Function: add_linear_simple_generation_formulation(local_t, Sbase, time_array, bus_vars, gen_data_t, gen_vars, prob, ramp_constraints, consider_time_up_down, area_spinning_reserve, skip_generation_limits, use_glsk_as_cost, logger)

Add MIP generation formulation

## Function: add_linear_nodal_capacity_generation_formulation(local_t, Sbase, time_array, bus_vars, gen_data_t, gen_vars, prob, skip_generation_limits, vd, nodal_capacity_active, use_glsk_as_cost, logger)

Add MIP generation formulation

## Function: add_linear_generation_expansion_planning_formulation(local_t, Sbase, time_array, bus_vars, gen_data_t, gen_vars, prob, ramp_constraints, skip_generation_limits, use_glsk_as_cost, logger)

Add MIP generation formulation

## Function: add_linear_generation_unit_commitment_formulation(local_t, Sbase, time_array, bus_vars, gen_data_t, gen_vars, prob, ramp_constraints, consider_time_up_down, area_spinning_reserve, skip_generation_limits, use_glsk_as_cost, logger)

Add MIP generation formulation

## Function: add_linear_generation_redispatch_formulation(local_t, Sbase, bus_vars, gen_data_t, gen_vars, prob, inter_aggregation_info, skip_generation_limits, use_glsk_as_cost, logger)

Add MIP generation redispatch formulation

## Function: add_linear_battery_formulation(t, Sbase, time_array, bus_vars, batt_data_t, batt_vars, prob, unit_commitment, ramp_constraints, skip_generation_limits, generation_expansion_planning, energy_0)

Add MIP generation formulation

## Function: add_nodal_capacity_formulation(t, nodal_capacity_vars, nodal_capacity_sign, capacity_nodes_idx, prob)

Add MIP generation formulation

## Function: add_linear_load_formulation(t, Sbase, bus_vars, load_data_t, load_vars, prob)

Add MIP generation formulation

## Function: add_linear_branches_formulation(t, Sbase, bus_data_t, branch_data_t, ctrl_branch_data_t, branch_vars, bus_vars, prob, inf, add_losses_approximation)

Formulate the branches

## Function: add_linear_branches_contingencies_formulation(t_idx, Sbase, branch_data_t, hvdc_vars, vsc_vars, branch_vars, bus_vars, prob, linear_multi_contingencies)

Formulate the branches

## Function: pmode3_formulation_impr(prob, elm_idx, t_idx, m, rate, P0, droop, theta_f, theta_t, base_name, logger)

Formulation for HVDC link with three operating regions using big-M and binary variables.

## Function: add_linear_hvdc_formulation(t, Sbase, hvdc_data_t, hvdc_vars, bus_vars, prob, logger)

:param t:

## Function: add_linear_vsc_formulation(t, Sbase, vsc_data_t, vsc_vars, bus_vars, prob, logger)

:param t:

## Function: add_linear_node_balance(t_idx, vd, bus_data, bus_vars, nodal_capacity_vars, capacity_nodes_idx, prob, logger)

Add the Kirchhoff nodal equality

## Function: add_copper_plate_balance(t_idx, bus_vars, prob)

Add the copperplate equality

## Function: add_hydro_formulation(t, time_global_tidx, time_array, Sbase, node_vars, path_vars, inj_vars, node_data, path_data, turbine_data, pump_data, p2x_data, generator_data, generator_vars, fluid_level_0, prob, logger)

Formulate the branches

## Function: run_linear_opf_ts(grid, time_indices, dispatch_mode, solver_type, zonal_grouping, skip_generation_limits, consider_contingencies, contingency_groups_used, ramp_constraints, consider_time_up_down, area_spinning_reserve, lodf_threshold, inter_aggregation_info, energy_0, fluid_level_0, nodal_capacity_sign, capacity_nodes_idx, use_glsk_as_cost, add_losses_approximation, logger, progress_text, progress_func, verbose, robust, mip_framework)

Formulate linear optimal power flow
