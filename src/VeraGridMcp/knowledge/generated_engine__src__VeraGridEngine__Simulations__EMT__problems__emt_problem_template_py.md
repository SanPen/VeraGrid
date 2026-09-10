# VeraGridEngine Module: src/VeraGridEngine/Simulations/EMT/problems/emt_problem_template.py

- Original source path: `src/VeraGridEngine/Simulations/EMT/problems/emt_problem_template.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 5
- Representative imports: abc, numpy, typing, VeraGridEngine.Utils.Symbolic.block, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.basic_structures, VeraGridEngine.Simulations.driver_template

## Function: _get_diff_var_sort_key(diff_var)

Return the ordering key used to sort differential variables.

## Function: _get_external_mapping(mdl)

Return the external mapping associated with a model block.

## Class: EmtBoundaryUpdateProtocol

- Bases: Protocol
- Summary: Structural protocol implemented by EMT boundary update providers.

### Methods

- `update(self, t, x, params)`
  Summary: Update the full parameter vector in place.
- `get_next_forced_event_time(self, t_prev, t_target)`
  Summary: Return the next exact-alignment event time inside ``(t_prev, t_target]``.

## Function: resolve_solver_boundary_updater(problem, boundary_updater, t0)

Resolve the boundary updater consumed by an EMT solver.

## Function: get_solver_forced_event_time(boundary_updater, t_prev, t_target)

Query the next forced-alignment event time if the updater exposes it.

## Function: is_problem_owned_boundary_updater(problem, boundary_updater)

Return whether the updater is owned by the EMT problem itself.

## Class: EmtProblemTemplate

- Bases: ABC
- Summary: Intermediate layer that manages DAE plumbing including indexing, variable mapping,

### Methods

- `glob_time(self)`
  Summary: Return the global time symbolic variable.
- `boundary_update(self)`
  Summary: Return the boundary update provider consumed by EMT solvers.
- `_finalize_order_and_maps(self)`
  Summary: Build canonical ordering, index maps and internal counters.
- `_build_runtime_param_vectors(self)`
  Summary: Build and initialize runtime and constant parameter buffers.
- `rebuild_runtime_param_vectors(self)`
  Summary: Rebuild the runtime and constant parameter buffers.
- `set_events_group(self, emt_events_group)`
  Summary: Apply a selected EMT events group to the runtime parameter equations.
- `reset_boundary_update_state(self, t0)`
  Summary: Reset runtime parameter values before a new EMT simulation starts.
- `get_compiler_names_dict(self)`
  Summary: Return the compiler-name mapping used by symbolic kernels.
- `get_alias_names_dict(self)`
  Summary: Return the alias-name mapping used by symbolic kernels.
- `get_event_parameter_equations(self)`
  Summary: Return the runtime event-parameter equations.
- `_rebuild_runtime_parameter_partition(self)`
  Summary: Rebuild the runtime parameter partition.
- `set_runtime_mode_parameters(self, mode_parameters)`
  Summary: Classify a subset of runtime parameters as retained discrete mode parameters.
- `_initialize_runtime_parameter_values(self, tm)`
  Summary: Initialize the flat runtime parameter vector at a given time.
- `_evaluate_runtime_expression(self, expression, runtime_params, tm)`
  Summary: Evaluate a runtime parameter expression.
- `get_state_vars(self)`
  Summary: Return the ordered list of state variables.
- `get_algebraic_vars(self)`
  Summary: Return the ordered list of algebraic variables.
- `state_and_algebraic_vars(self)`
  Summary: :return:
- `get_state_eqs(self)`
  Summary: Return the ordered list of state equations.
- `get_algebraic_eqs(self)`
  Summary: Return the ordered list of algebraic equations.
- `get_variable_parameters(self)`
  Summary: Return the ordered list of runtime parameters.
- `get_constant_parameters(self)`
  Summary: Return the ordered list of constant parameters.
- `get_diff_vars(self)`
  Summary: Return the ordered list of differential variables.
- `get_parameters_values(self)`
  Summary: Return the ordered list of constant parameter values.
- `get_all_vars_number(self)`
  Summary: Return the total number of state and algebraic variables.
- `get_diff_var_number(self)`
  Summary: Return the number of differential variables.
- `get_algebraic_var_number(self)`
  Summary: Return the number of algebraic variables.
- `get_states_number(self)`
  Summary: Return the number of state variables.
- `get_variable_parameter_number(self)`
  Summary: Return the number of runtime parameters.
- `get_x0(self)`
  Summary: Build the initial state vector from the stored initialization guess.
- `get_dx0(self)`
  Summary: Build the initial differential vector from the stored differential initialization guess.
- `def_event_params_fn(self, ev_param, tm)`
  Summary: Update only the continuous runtime parameter slice.
- `update_variable_params(self, t)`
  Summary: Update the internal runtime parameter values at the given time.
- `get_full_param_index(self, uid)`
  Summary: Return the flat full-parameter index associated with the given UID.
- `get_newton_trace_collector(self)`
  Summary: Return the Newton trace collector instance.
- `set_newton_trace_collector(self, collector)`
  Summary: Set the Newton trace collector instance.
- `get_device_vars_dict(self)`
  Summary: Return the device-to-variable mapping dictionary.
- `get_var_idx(self, v)`
  Summary: Return the flat variable index associated with the given variable.
- `get_diff_var_idx(self, dv)`
  Summary: Return the flat differential index associated with the given differential variable.
- `vars_glob_name2uid(self)`
  Summary: :return:
- `set_init_guess(self, mdl, reference_powerflow, val)`
  Summary: Set the initialization guess associated with a model external mapping.
- `get_floquet_ak_stack(self, trajectory, h, jac_evaluator, static_params)`
  Summary: Return the stack of transition matrices used for Floquet analysis.
- `get_runtime_continuous_slice(self)`
  Summary: Return the slice of continuous runtime inputs inside the flat runtime vector.
- `get_runtime_mode_slice(self)`
  Summary: Return the slice of retained mode parameters inside the flat runtime vector.
- `get_runtime_continuous_parameters(self)`
  Summary: Return the ordered list of continuous runtime parameters.
- `get_runtime_mode_parameters(self)`
  Summary: Return the ordered list of retained mode runtime parameters.
- `uid2idx_vars(self)`
  Summary: Return the UID-to-variable-index mapping.
- `uid2idx_params(self)`
  Summary: Return the UID-to-constant-parameter-index mapping.
- `uid2idx_event_params(self)`
  Summary: Return the UID-to-runtime-parameter-index mapping.
- `uid2idx_diff(self)`
  Summary: Return the UID-to-differential-index mapping.
- `event_params_values(self)`
  Summary: Return the current flat runtime parameter vector.
- `event_parameters_eqs(self)`
  Summary: No docstring provided.
