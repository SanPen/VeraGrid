# VeraGridEngine Module: src/VeraGridEngine/Simulations/EMT/solvers/solver_AD.py

- Original source path: `src/VeraGridEngine/Simulations/EMT/solvers/solver_AD.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 5
- Top-level function count: 6
- Representative imports: numpy, numba, scipy.sparse, time, hashlib, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.Simulations.EMT.problems.emt_problem_template, VeraGridEngine.enumerations, VeraGridEngine.Utils.Symbolic.jit_compiler, VeraGridEngine.Utils.Symbolic.diagnostic, VeraGridEngine.basic_structures, typing, scipy.sparse

## Function: _safe_njit(py_func, fastmath, cache, signature)

Safely wraps a python function with Numba's njit compiler.

## Function: _scatter_color_jvp_to_csc_data(jvp, data, color_ptr, col_ptr, row_idx, data_idx, color_id)

Scatter a single JVP evaluation into the CSC data array for all columns in a given color.

## Function: _compile_master_jacobian_kernel(ad_kernel, n_colors)

Build the eager sparse Jacobian dispatcher.

## Function: greedy_color_columns(col_rows, n_rows)

Computes a greedy coloring of the column dependency graph to minimize AD sweeps.

## Class: BoundaryUpdaterInterface

- Bases: none
- Summary: No docstring provided.

### Methods

- `update(self, t, x_prev, full_params)`
  Summary: No docstring provided.
- `get_next_forced_event_time(self, t_prev, t_target)`
  Summary: No docstring provided.

## Class: Predictor

- Bases: none
- Summary: Computes an explicit predictor for the Newton initial guess x_iter.

### Methods

- `predict(self, x_iter, x_prev, dx_prev, h, pred_method)`
  Summary: Apply predictor in-place and return x_iter.
- `_predict_euler_state(self, x_iter, x_prev, dx_prev, h)`
  Summary: Explicit Euler predictor for the *state* subset:

## Function: fill_full_parameter_buffer(runtime_params, static_params, full_params_out)

Write runtime and static parameters into one preallocated full buffer.

## Function: evaluate_batched_residual(kernel_list, x_iter, full_params, x_prev, dx_prev, h_eff, x_prev2, residual_out)

Evaluate all residual batches into a caller-owned buffer.

## Class: AdBacktrackingResidualEvaluator

- Bases: none
- Summary: Wrapper that evaluates AD residual batches for line-search backtracking.

### Methods

- `set_context(self, kernel_list, full_params, x_prev, dx_prev, h_eff, x_prev2)`
  Summary: Store the residual-evaluation context of the current Newton step.
- `evaluate(self, candidate_x, out_res)`
  Summary: Evaluate one trial Newton iterate during backtracking.

## Class: SparseADJacobian

- Bases: none
- Summary: Sparse Jacobian evaluator with DEBUG TIMING.

### Methods

- No methods detected.

## Class: JitAdSolver

- Bases: none
- Summary: No docstring provided.

### Methods

- `build_jit_ad(self, only_jacobian)`
  Summary: Compiles the residual kernel using batching and prepares the Sparse AD Jacobian.
- `simulate(self, x0, dx0, params0, boundary_updater)`
  Summary: Main JIT simulation loop using the Automatic Differentiation (AD) backend.
- `get_backend_build_stats(self)`
  Summary: Return setup timings collected during backend compilation.
- `get_last_runtime_stats(self)`
  Summary: Return runtime statistics collected during the latest simulation.
- `get_last_sim_loop_time(self)`
  Summary: Return the latest integration-loop wall time.
