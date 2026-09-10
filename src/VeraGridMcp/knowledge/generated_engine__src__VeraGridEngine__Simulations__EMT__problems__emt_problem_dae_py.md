# VeraGridEngine Module: src/VeraGridEngine/Simulations/EMT/problems/emt_problem_dae.py

- Original source path: `src/VeraGridEngine/Simulations/EMT/problems/emt_problem_dae.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

Module providing the EmtProblemDae class, which acts as the electrical

## Module Surface

- Class count: 2
- Top-level function count: 11
- Representative imports: __future__, time, numpy, pandas, scipy.sparse, scipy.sparse.linalg, numpy.linalg, typing, itertools, VeraGridEngine.Devices, VeraGridEngine.Simulations.driver_template, VeraGridEngine.Devices.Aggregation.emt_events_group, VeraGridEngine.Devices.types, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.Utils.Symbolic.block, VeraGridEngine.enumerations

## Function: _tic()

Returns the current performance counter time.

## Function: _toc(t0)

Returns the elapsed time since t0.

## Class: EmtTopologyError

- Bases: Exception
- Summary: Exception raised when EMT topology validation fails.

### Methods

- No methods detected.

## Function: _unique_keep_order(seq)

Remove duplicated variables by UID while preserving the first appearance order.

## Function: _deduplicate_block_entities(block)

Removes duplicated symbolic objects within the block by UID

## Function: _get_mode_event_sort_key(event)

Return the sorting key of a mode event.

## Function: _is_time_aligned(t_curr, event_time)

Return whether the current solver time is aligned with the event time.

## Function: _get_next_forced_mode_event_time(scheduled_mode_events, t_prev, t_target)

Return the earliest forced-alignment mode event time in the interval

## Function: _get_block_name(mdl)

Return the block name used for logging.

## Function: _get_grid_runtime_events(grid)

Return the list of scheduled runtime events available in the grid.

## Function: _get_bus_v_list(grid, bus_block, ph_v_keys)

Return the ordered list of bus phase voltages, using None for missing phases.

## Function: _get_external_mapping(mdl)

No docstring provided.

## Class: EmtProblemDae

- Bases: EmtProblemTemplate
- Summary: Electrical parser layer for the EMT DAE Problem.

### Methods

- `_register_init_model(self, mdl)`
  Summary: Register a block for explicit initialization if it defines init_eqs.
- `get_build_report(self)`
  Summary: Return the EMT problem build timing report.
- `_register_diff_init_model(self, mdl)`
  Summary: Register a block for explicit differential initialization if it defines diff_init_eqs.
- `_run_explicit_initialization(self)`
  Summary: Run explicit initialization for every block that defines initialization equations.
- `_validate_emt_models_exist(self)`
  Summary: Validate that all devices have their emt_model properly assigned before building.
- `_validate_connections(self)`
  Summary: Validate EMT topology connectivity.
- `_process_device_model(self, dev, sys_block, grid, glob_time)`
  Summary: Register a device EMT model into the global system block.
- `_collect_api_obj_mapping(self, mdl)`
  Summary: Collect the API object mapping from a block hierarchy.
- `_to_const(self, value)`
  Summary: Convert a numeric value into a ``Const`` symbolic expression.
- `_assign_api_obj_param_if_present(self, mdl, key, value)`
  Summary: Assign a mapped model parameter when the mapping key exists.
- `_build_structure_and_collect(self, sys_block, grid, glob_time)`
  Summary: Build the EMT system structure and collect all algebraic KCL equations.
- `_register_runtime_event_parameters(self, dev, mdl)`
  Summary: Register runtime-updatable EMT parameters declared by the device block.
- `_get_emt_events_for_group(self, emt_events_group)`
  Summary: Return the EMT events that belong to the selected group.
- `_event_targets_registered_parameter(self, evt, parameter_uid)`
  Summary: Return whether the EMT event targets a runtime parameter registered in the problem.
- `set_events_group(self, emt_events_group)`
  Summary: Activate the selected EMT events group inside the problem runtime layer.
- `_add_model_to_system_mappings(self, elm, mdl)`
  Summary: Populates tracking dictionaries to maintain the relationship between
- `_try_set_bus_pf_init(self, bus, mdl, bus_index)`
  Summary: Initialize bus voltage variables from three-phase power-flow results.
- `_try_set_bus_pf_init_balanced(self, bus, mdl, bus_index)`
  Summary: Initialize bus voltage variables from balanced power-flow results.
- `_get_vsc_terminal_indices(self, f_bus_idx, t_bus_idx)`
  Summary: Return ``(ac_bus_idx, dc_bus_idx, ac_is_from)`` for a VSC branch.
- `_set_vsc_pf_positive_sequence(self, mdl, VA, VB, VC, IA, IB, IC)`
  Summary: Populate positive-sequence PF-derived quantities used by VSC templates
- `_try_set_vsc_branch_pf_init(self, mdl, f_bus_idx, t_bus_idx, sbase, vsc_index)`
  Summary: Initialize a VSC branch from three-phase PF results using the converter
- `_try_set_vsc_branch_pf_init_balanced(self, mdl, f_bus_idx, t_bus_idx, sbase, vsc_index)`
  Summary: Initialize a VSC branch from balanced PF results using the converter
- `_try_set_branch_pf_init(self, mdl, branch_index, f_bus_idx, t_bus_idx, sbase, is_vsc, vsc_index)`
  Summary: Initialize branch variables from three-phase power-flow results.
- `_try_set_branch_pf_init_balanced(self, mdl, branch_index, f_bus_idx, t_bus_idx, sbase, is_vsc, vsc_index)`
  Summary: Initialize branch variables from balanced power-flow results.
- `_try_set_inj_pf_init(self, inj, mdl, bus_index, sbase)`
  Summary: Initialize injection variables from three-phase power-flow results.
- `_try_set_inj_pf_init_balanced(self, inj, mdl, bus_index, sbase)`
  Summary: Initialize injection variables from balanced power-flow results.
- `_try_set_bergeron_pf_init(self, mdl, rt, branch_index, f_bus_idx, t_bus_idx, sbase)`
  Summary: Initialize Bergeron history terms from three-phase power-flow results.
- `_try_set_bergeron_pf_init_balanced(self, mdl, rt, branch_index, f_bus_idx, t_bus_idx, sbase)`
  Summary: Initialize Bergeron history terms from balanced power-flow results.
- `set_if_exists(self, mdl, key, value)`
  Summary: Set an initialization value only if the external mapping contains the key.
- `_initialize_mode_event_state(self)`
  Summary: Initialize the mode event cursor state.
- `_apply_scheduled_mode_events(self, t_curr, full_params)`
  Summary: Apply scheduled retained mode events to the flat full parameter vector.
- `_collect_runtime_mode_parameters(self)`
  Summary: Collect runtime parameters that must be retained between steps.
- `add_device_var(self, dev, var)`
  Summary: Registers a variable belonging to a specific device.
- `set_init_guess(self, mdl, reference_powerflow, val)`
  Summary: Set the temporary initial guess for a mapped variable during the parsing phase.
- `set_diff_init_guess(self, mdl, reference_powerflow, val)`
  Summary: Set the temporary initial guess for a mapped differential variable during the parsing phase.
- `set_external_param(self, mdl, key, value)`
  Summary: Set a PF-derived value either as an event parameter if the mapped variable belongs to mdl.event_dict.
- `get_init_guess_info(self)`
  Summary: Return a table with the explicitly initialized variable guesses.
- `get_device_vars_dict(self)`
  Summary: Returns the dictionary mapping electrical devices to their variables.
- `vars_glob_name2uid(self)`
  Summary: Returns the dictionary mapping global variable names to UIDs.
- `boundary_update(self)`
  Summary: Return the endogenous EMT boundary updater consumed by the EMT solvers.
- `reset_boundary_update_state(self, t0)`
  Summary: Reset the EMT boundary update state before a new solver run starts.
- `emt_boundary_update(self, t_curr, x_prev, full_params)`
  Summary: Update runtime boundaries before the Newton step.
- `get_next_forced_event_time(self, t_prev, t_target)`
  Summary: Return the earliest forced-alignment event time in the interval
- `update(self, t, x, params)`
  Summary: Boundary update entry point compatible with BoundaryUpdateWrapper.
- `get_floquet_ak_stack(self, trajectory, h, jac_evaluator, static_params)`
  Summary: Return the stack of reduced transition matrices used for Floquet analysis.
- `get_init_guess_table(self, include_all_vars, only_in_init_guess, tol_zero)`
  Summary: Return a table with uid, alias/name and initial value for each variable.
- `_assign_api_obj_mapping_branch(self, br)`
  Summary: No docstring provided.
- `_assign_api_obj_mapping_load(self, load)`
  Summary: Assign PF-derived static load parameters into the EMT model API mapping.
- `_assign_api_obj_mapping_generator(self, gen)`
  Summary: Assign PF-derived static generator parameters into the EMT model API mapping.
