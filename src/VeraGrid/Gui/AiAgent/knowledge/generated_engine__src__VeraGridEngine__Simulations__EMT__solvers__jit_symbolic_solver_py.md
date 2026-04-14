# VeraGridEngine Module: src/VeraGridEngine/Simulations/EMT/solvers/jit_symbolic_solver.py

- Original source path: `src/VeraGridEngine/Simulations/EMT/solvers/jit_symbolic_solver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 6
- Top-level function count: 8
- Representative imports: typing, numpy, numba, scipy.sparse, time, hashlib, scipy.linalg, scipy.sparse.linalg, VeraGridEngine.Simulations.EMT.problems.emt_problem_template, VeraGridEngine.enumerations, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.Utils.Symbolic.jit_compiler, VeraGridEngine.Utils.Symbolic.diagnostic, VeraGridEngine.basic_structures

## Class: SymbolicCompiledNumbaKernelCache

- Bases: none
- Summary: In-process cache of Numba-compiled symbolic kernels.

### Methods

- `get(self, cache_key)`
  Summary: Return one cached compiled kernel.
- `set(self, cache_key, kernel)`
  Summary: Store one compiled kernel.

## Function: _safe_njit(py_func, fastmath, cache)

Compile one symbolic kernel with an in-process Numba cache.

## Function: get_vars_in_expr(expr)

Recursively collects UIDs of all variables present in an expression.

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

## Class: BoundaryUpdateWrapper

- Bases: none
- Summary: Interface for injecting boundary conditions and events before the Newton step.

### Methods

- `update(self, t, x, params)`
  Summary: Updates the parameters vector in place based on the current time and state.
- `get_next_forced_event_time(self, t_prev, t_target)`
  Summary: Return the earliest forced-alignment event time in the interval (t_prev, t_target].

## Class: HybridJacobianEvaluator

- Bases: none
- Summary: Evaluates the JIT-compiled Jacobian and formats it as either Dense or Sparse.

### Methods

- `evaluate(self, states, params, history, d_history, h, history2)`
  Summary: Executes the JIT kernel and constructs the resulting Jacobian matrix.

## Class: ResidualTrialEvaluator

- Bases: none
- Summary: Callable helper to evaluate residual norms during Newton backtracking.

### Methods

- `set_context(self, kernel_list, full_params, x_prev, dx_prev, h_eff, x_prev2)`
  Summary: Store the residual-evaluation context of the current Newton step.

## Class: JitSymbolicSolver

- Bases: none
- Summary: No docstring provided.

### Methods

- `build_jit_kernel(self, method)`
  Summary: Compiles the numerical residual function using JIT.
- `_build_jit_symbolic_hybrid(self, method, use_sparse)`
  Summary: Compiles a Hybrid Symbolic Jacobian.
- `simulate(self, x0, dx0, params0, boundary_updater)`
  Summary: Main JIT simulation loop using the Symbolic Differentiation (SD) backend.
- `get_backend_build_stats(self)`
  Summary: Return setup timings collected during backend compilation.
- `get_last_runtime_stats(self)`
  Summary: Return runtime statistics collected during the latest simulation.
- `get_last_sim_loop_time(self)`
  Summary: Return the latest integration-loop wall time.

## Function: _clip_debug_text(value, width)

Format text for residual debug tables with width clipping.

## Function: _format_debug_number(value, width)

Format numeric values for debug output tables.

## Function: _print_full_params_debug(full_params)

Print the order and values of the assembled solver parameter vector.

## Function: _print_residual_debug_table(res, n_eqs, x_iter, x_prev, dx_prev, debug_info, step_idx, iter_idx)

Print a formatted table with the largest residuals and relevant state values.
