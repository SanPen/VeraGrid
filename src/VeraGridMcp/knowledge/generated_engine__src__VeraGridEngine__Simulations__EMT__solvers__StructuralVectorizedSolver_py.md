# VeraGridEngine Module: src/VeraGridEngine/Simulations/EMT/solvers/StructuralVectorizedSolver.py

- Original source path: `src/VeraGridEngine/Simulations/EMT/solvers/StructuralVectorizedSolver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 9
- Top-level function count: 9
- Representative imports: __future__, typing, time, hashlib, numpy, numba, scipy.sparse, scipy.linalg, scipy.sparse.linalg, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.Utils.Symbolic.diagnostic, VeraGridEngine.Simulations.EMT.problems.emt_problem_template, VeraGridEngine.Utils.Symbolic.jit_compiler, VeraGridEngine.Simulations.EMT.solvers.structural_compiled_solver, VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface, VeraGridEngine.enumerations

## Function: _build_backend_cache_token(method, n_rows, n_cols, group_keys)

Return a deterministic cache token for backend-generated kernels.

## Function: fill_full_parameter_buffer(runtime_params, static_params, full_params_out)

Write runtime and static parameters into one preallocated full buffer.

## Function: evaluate_vectorized_residual(residual_evaluator, states, params, history, d_history, h, history2, residual_out)

Evaluate the fused vectorized residual into a caller-owned buffer.

## Function: build_residual_evaluator(residual_dispatcher, vec_flat_args)

Build one fixed-signature residual evaluator for the current dispatcher.

## Function: _safe_njit(py_func, fastmath, cache, signature)

Safely wraps a python function with Numba's njit compiler.

## Function: _canonicalize_node(node, runtime_uids, param_uids, runtime_slots, param_slots, found_runtime_vars_ordered, seen_runtime_uids)

Canonicalizes an expression while distinguishing runtime variables from parameters.

## Function: canonicalize_expression(expr, runtime_uids, param_uids)

Returns a canonical structural signature and the ordered runtime variables only.

## Class: VectorizedKernelSpec

- Bases: none
- Summary: Typed container for one vectorized residual kernel.

### Methods

- `get_kernel(self)`
  Summary: Return the compiled kernel.
- `get_indices(self)`
  Summary: Return the runtime gather matrix.
- `get_target_rows(self)`
  Summary: Return the residual target rows.
- `get_row_count(self)`
  Summary: Return the number of rows emitted by the kernel.

## Class: FusedResidualDispatcher

- Bases: none
- Summary: Dispatcher that applies all vectorized residual kernels in order.

### Methods

- `evaluate(self, states, params, history, d_history, h, history2, out)`
  Summary: Evaluate the grouped residual system in place.

## Class: VectorizedResidualTrialEvaluator

- Bases: none
- Summary: Callable helper that evaluates vectorized residuals during backtracking.

### Methods

- `set_context(self, residual_evaluator, full_params, x_prev, dx_prev, h_eff, x_prev2)`
  Summary: Store the residual-evaluation context of the current Newton step.

## Class: DirectResidualDispatcher

- Bases: none
- Summary: Residual dispatcher backed by one monolithic in-place kernel.

### Methods

- `evaluate(self, states, params, history, d_history, h, history2, out)`
  Summary: Evaluate the full residual system in place.

## Function: _scatter_color_jvp_to_csc_data(jvp, data, color_ptr, col_ptr, row_idx, data_idx, color_id)

No docstring provided.

## Function: _compile_master_jacobian_kernel(ad_kernel, n_colors)

Build the eager sparse Jacobian dispatcher.

## Class: Predictor

- Bases: none
- Summary: Computes an explicit predictor for the Newton initial guess x_iter.

### Methods

- `predict(self, x_iter, x_prev, dx_prev, h, pred_method)`
  Summary: Apply predictor in-place and return x_iter.
- `_predict_euler_state(self, x_iter, x_prev, dx_prev, h)`
  Summary: Explicit Euler predictor for the *state* subset:

## Class: EquationGroup

- Bases: none
- Summary: Data structure to hold clustered equations for auto-vectorization.

### Methods

- `add_indices(self, var_indices, row_index)`
  Summary: Adds matrix indices and row index to the cluster.
- `set_template(self, template_eq, template_vars)`
  Summary: Sets the structural template for this group.
- `get_idx_matrix(self)`
  Summary: Returns the index matrix.
- `get_row_indices(self)`
  Summary: Returns the row indices.
- `get_template_eq(self)`
  Summary: Returns the template equation.
- `get_template_vars(self)`
  Summary: Returns the template variables.

## Class: BoundaryUpdateWrapper

- Bases: none
- Summary: Interface for injecting boundary conditions and events before the Newton step.

### Methods

- `update(self, t, x, params)`
  Summary: Updates the parameters vector in place based on the current time and state.
- `get_next_forced_event_time(self, t_prev, t_target)`
  Summary: Returns the next forced-alignment event time inside (t_prev, t_target].

## Class: SparseADJacobian

- Bases: none
- Summary: No docstring provided.

### Methods

- `_greedy_color_columns(col_rows, n_rows)`
  Summary: No docstring provided.
- `get_matrix(self)`
  Summary: Return the reusable CSC Jacobian shell.
- `get_data_buffer(self)`
  Summary: Return the reusable CSC numeric buffer.

## Class: StructuralVectorizedSolver

- Bases: none
- Summary: No docstring provided.

### Methods

- `auto_detect_vectorization(self, method)`
  Summary: Infers the algebraic structure of the DAE system (clustering) and compiles
- `simulate(self, x0, dx0, params0, boundary_updater)`
  Summary: Run the vectorized DAE time-domain simulation.
- `_simulate_vectorized(self, t0, t_end, h, x0, dx0, params0, method, boundary_updater, verbose, dense_threshold)`
  Summary: No docstring provided.
- `get_backend_build_stats(self)`
  Summary: Return setup timings collected during backend compilation.
- `get_last_runtime_stats(self)`
  Summary: Return runtime statistics collected during the latest simulation.
- `get_last_sim_loop_time(self)`
  Summary: Return the latest integration-loop wall time.
