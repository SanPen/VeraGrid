# VeraGridEngine Module: src/VeraGridEngine/Simulations/EMT/initialization_emt.py

- Original source path: `src/VeraGridEngine/Simulations/EMT/initialization_emt.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 7
- Top-level function count: 38
- Representative imports: typing, numpy, numba, math, time, hashlib, os, pickle, pathlib, warnings, scipy.sparse, scipy.sparse.linalg, VeraGridEngine.enumerations, VeraGridEngine.Simulations.EMT.emt_options, VeraGridEngine.Simulations.EMT.problems.emt_problem_template, VeraGridEngine.Utils.Symbolic.compiled_functions

## Class: EmtInitializationReport

- Bases: none
- Summary: Stores the outcome of the EMT-native initialization workflow.

### Methods

- No methods detected.

## Class: ReducedInitializationSystemCacheEntry

- Bases: none
- Summary: In-process cache entry for reduced EMT initialization systems.

### Methods

- `get_residual_fn(self)`
  Summary: Return the cached reduced residual evaluator.
- `get_jacobian_fn(self)`
  Summary: Return the cached reduced Jacobian evaluator.

## Class: ReducedInitializationSystemCache

- Bases: none
- Summary: In-process cache for reduced EMT initialization systems.

### Methods

- `get_entry(self, cache_key)`
  Summary: Return one cached reduced-system entry.
- `set_entry(self, cache_key, entry)`
  Summary: Store one cached reduced-system entry.

## Class: InitializationVectorCacheEntry

- Bases: none
- Summary: In-process cache entry for one initialization-stage symbolic vector.

### Methods

- `get_vector(self)`
  Summary: Return the cached symbolic vector evaluator.

## Class: InitializationVectorCache

- Bases: none
- Summary: In-process cache for symbolic vectors used during EMT initialization.

### Methods

- `get_entry(self, cache_key)`
  Summary: Return one cached initialization-vector entry.
- `set_entry(self, cache_key, entry)`
  Summary: Store one cached initialization-vector entry.

## Class: InitializationStateRhsVector

- Bases: none
- Summary: Lightweight state-RHS evaluator used by ``dx0`` completion.

### Methods

- No methods detected.

## Function: _get_state_rhs_persistent_cache_directory()

Return the persistent cache directory used by ``dx0`` state-RHS evaluators.

## Function: _build_state_rhs_source(missing_state_eqs, compiler_names_dict, alias_names_dict, vars_name, diff_name, event_params_name, params_name)

Build the Python source code of the ``dx0`` state-RHS evaluator.

## Function: _load_or_build_state_rhs_vector(problem, missing_state_eqs, cache_key, report)

Load or build the ``dx0`` state-RHS evaluator.

## Function: _get_reduced_initialization_persistent_cache_directory()

Return the persistent cache directory used by reduced EMT initialization.

## Function: _serialize_initialization_report(report)

Serialize an EMT initialization report into a cache-safe dictionary.

## Function: _serialize_problem_guess_map(problem, guess_map, diff_guess)

Serialize an initialization guess map using stable variable names.

## Function: _restore_problem_guess_map(problem, name_map, diff_guess)

Restore an initialization guess map from stable variable names.

## Function: _restore_initialization_report_from_payload(report, payload)

Restore an EMT initialization report from a serialized payload.

## Function: _build_persistent_initialization_cache_key(problem, unknown_vars, residual_eqs, state_unknown_mask, options)

Return the deterministic cache key of one persistent reduced initialization result.

## Function: _persistent_initialization_params_match(payload, runtime_params, constant_params)

Return whether one persistent initialization payload matches the current parameter snapshots.

## Function: _load_persistent_initialization_solution(cache_key)

Load one persistent reduced initialization result.

## Function: _store_persistent_initialization_solution(cache_key, payload)

Store one persistent reduced initialization result.

## Function: _build_reduced_initialization_cache_key(problem, unknown_vars, residual_eqs, state_unknown_mask)

Return a deterministic cache key for one reduced EMT initialization system.

## Function: _build_state_rhs_cache_key(problem, state_eqs)

Return the cache key for the symbolic vector used to compute missing ``dx0``.

## Function: _collect_missing_dx_problem(problem)

Return the differential variables that still need ``dx0`` and their state equations.

## Function: build_uid_bindings(eq, event_params_array, x, params_array, dx, uid2idx_event_params, uid2idx_vars, uid2idx_params, uid2idx_diff)

Builds a mapping of Unique Identifiers (UIDs) to their current numeric values.

## Function: event_param_is_resolved(v, mdl)

Checks if an event parameter has been assigned a concrete value.

## Function: can_compute_init(var, eq, mdl, init_guess, diff_init_guess, uid2idx_diff, uid2idx_vars)

Determines if an initialization equation is computable based on current knowns.

## Function: init_explicit_emt(mdl, sys_vars, sys_diff_vars, variable_parameters, event_parameters_eqs, constant_parameters, init_guess, diff_init_guess, uid2idx_vars, uid2idx_diff, uid2idx_params, uid2idx_event_params, compiler_names_dict, alias_names_dict, VARIABLE_PARAMS_NAME, VARS_NAME, DIFF_NAME, CONSTANT_PARAMS_NAME, verbose)

Initializes the EMT model by solving initialization and differential equations.

## Function: init_pseudo_transient(problem, options)

Run the EMT-native initialization workflow forcing the pseudo-transient path.

## Function: run_emt_explicit_initialization(problem, verbose)

Run the explicit EMT initialization stage on a full problem object.

## Class: ReducedInitializationSystem

- Bases: none
- Summary: Reduced EMT initialization system built on top of the unresolved variables only.

### Methods

- No methods detected.

## Function: _build_constant_param_array(problem)

Build the dense constant-parameter vector used by the initialization solvers.

## Function: _build_runtime_param_array(problem)

Build the runtime-parameter snapshot at the initialization time.

## Function: _build_state_equation_lookup(problem)

Build a UID lookup for state equations.

## Function: _extract_unknown_vector(problem, unknown_vars, x)

Extract the reduced unknown vector from the full EMT variable vector.

## Function: _scatter_unknown_vector(problem, unknown_vars, x, reduced_x)

Scatter the reduced unknown vector back into the full EMT variable vector.

## Function: _build_reduced_initialization_system(problem, allow_state_equilibrium)

Build the reduced initialization system for unresolved EMT variables.

## Function: _collect_reduced_initialization_problem(problem, allow_state_equilibrium)

Collect the reduced initialization unknowns and residual equations without compiling them.

## Function: _evaluate_initialization_residual(reduced_system, problem, x, dx, runtime_params, constant_params)

Evaluate the reduced initialization residual.

## Function: _evaluate_initialization_jacobian(reduced_system, problem, x, dx, runtime_params, constant_params)

Evaluate the reduced initialization Jacobian.

## Function: _max_abs_value(values)

Return the infinity norm of one dense vector.

## Function: _solve_reduced_linear_system(matrix, rhs, dense_threshold)

Solve one reduced linear system using a dense or sparse backend depending on size.

## Function: _run_reduced_newton_initialization(reduced_system, problem, x, dx, runtime_params, constant_params, options, report)

Solve the reduced initialization system with damped sparse Newton iterations.

## Function: _run_reduced_pseudo_transient_initialization(reduced_system, problem, x, dx, runtime_params, constant_params, options, report)

Solve the reduced initialization system with a pseudo-transient fallback.

## Function: _apply_solution_to_problem(problem, x)

Persist the reduced-solve state vector back into the initialization guess map.

## Function: _compute_missing_dx0(problem, report, x_full, dx_full, runtime_params, constant_params)

Compute missing differential initial values from the state equations.

## Function: _build_initialization_system_if_needed(problem, options, report)

Build the reduced initialization system only when unresolved work remains.

## Function: run_emt_native_initialization(problem, options)

Run the EMT-native initialization stages after PF projection and explicit init.
