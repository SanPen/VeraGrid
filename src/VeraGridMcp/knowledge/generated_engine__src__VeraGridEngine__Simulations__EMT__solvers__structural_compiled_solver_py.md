# VeraGridEngine Module: src/VeraGridEngine/Simulations/EMT/solvers/structural_compiled_solver.py

- Original source path: `src/VeraGridEngine/Simulations/EMT/solvers/structural_compiled_solver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 13
- Top-level function count: 26
- Representative imports: __future__, enum, typing, hashlib, time, numba, numba, numpy, numpy.typing, scipy.linalg, scipy.sparse, scipy.sparse.linalg, VeraGridEngine.Utils.Symbolic.diagnostic, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.Utils.Symbolic.jit_compiler, VeraGridEngine.Utils.NumericalMethods.emt_sparse_superlu_backend

## Class: StructuralCompiledWarmupPolicy

- Bases: Enum
- Summary: Warmup policy used by the structural compiled backend.

### Methods

- No methods detected.

## Class: CompiledNumbaKernelCache

- Bases: none
- Summary: In-process cache of Numba-compiled eager kernels.

### Methods

- `get(self, cache_key)`
  Summary: Return one cached compiled kernel.
- `set(self, cache_key, kernel)`
  Summary: Store one compiled kernel.

## Function: _safe_njit(py_func, signature_tpe, fastmath, cache)

Compile a Python function with Numba using an eager signature when provided.

## Function: _build_fused_residual_signature()

Return the eager signature of the fused residual dispatcher.

## Function: _build_master_jacobian_signature()

Return the eager signature of the sparse Jacobian dispatcher.

## Function: _build_scatter_color_signature()

Return the eager signature of the CSC scatter helper.

## Function: _build_max_abs_signature()

Return the eager signature of the infinity-norm helper.

## Function: _build_copy_negated_signature()

Return the eager signature of the negated-copy helper.

## Function: _build_fill_full_parameter_signature()

Return the eager signature of the full-parameter fill helper.

## Function: _build_permute_csc_signature()

Return the eager signature of the CSC permutation helper.

## Function: _build_scatter_permuted_solution_signature()

Return the eager signature of the solution scatter helper.

## Function: _get_runtime_uid(var_obj)

Return the canonical runtime UID of a symbolic variable.

## Function: _canonicalize_symbolic_node(node, runtime_uids, parameter_uids, runtime_slots, parameter_slots, ordered_runtime_vars, visited_runtime_uids)

Convert a symbolic expression into a structural canonical string.

## Function: canonicalize_expression(expr, runtime_uids, parameter_uids)

Return the canonical signature and ordered runtime variables of an expression.

## Function: _build_full_residual_equations(state_vars, state_eqs, algebraic_eqs)

Build the full implicit residual system used by Newton iterations.

## Function: _build_parameter_uid_set(variable_parameters, constant_parameters)

Build the parameter UID set used by structural canonicalization.

## Function: _build_backend_cache_token(method, n_rows, n_cols, group_keys)

Return a deterministic cache token for backend-generated dispatchers.

## Function: _greedy_color_columns(col_rows, n_rows)

Color the sparse column dependency graph with a greedy heuristic.

## Function: _scatter_color_jvp_to_csc_data(jvp, data, color_ptr, col_ptr, row_idx, data_idx, color_id)

Scatter a colored JVP vector into CSC numeric storage.

## Function: _max_abs_value(values)

Compute the infinity norm without allocating temporary arrays.

## Function: _copy_negated_vector(values, out)

Write the negated vector into a preallocated buffer.

## Function: _fill_full_parameter_buffer(runtime_params, static_params, full_params_out)

Write runtime and static parameters into one preallocated full buffer.

## Function: _max_abs_diff_vectors(left_values, right_values)

Return the maximum absolute difference between two vectors.

## Function: _permute_csc_data_by_columns(source_data, source_indptr, column_perm, target_indptr, target_data)

Reorder CSC numeric values according to a persistent column permutation.

## Function: _scatter_permuted_solution_to_original_order(permuted_solution, inverse_column_perm, out_solution)

Scatter a solution computed on a column-permuted system back to original order.

## Function: _warmup_compiled_numba_helpers()

Trigger one eager call to the small Numba helper kernels.

## Function: _should_run_full_backend_warmup(warmup_policy, n_vars, estimated_steps, use_direct_residual)

Decide whether the backend should perform a full residual/Jacobian warmup.

## Class: StructuralCompiledBoundaryUpdateWrapper

- Bases: none
- Summary: Boundary update interface for the structural compiled solver.

### Methods

- `update(self, t, x, params)`
  Summary: Update the parameter vector in place.
- `get_next_forced_event_time(self, t_prev, t_target)`
  Summary: Return the next forced event time inside the local substep.

## Class: StructuralCompiledPredictor

- Bases: none
- Summary: Explicit predictor used to initialize the Newton iteration.

### Methods

- `predict(self, x_iter, x_prev, dx_prev, h, pred_method)`
  Summary: Write the predictor guess in place.

## Class: StructuralCompiledResidualTrialEvaluator

- Bases: none
- Summary: Callable helper that evaluates residuals during Newton backtracking.

### Methods

- `set_context(self, residual_assembler, full_params, x_prev, dx_prev, h_eff, x_prev2)`
  Summary: Store the residual-evaluation context of the current Newton step.
- `evaluate(self, trial_x, out_res)`
  Summary: Evaluate one trial Newton iterate during backtracking.

## Class: StructuralCompiledEquationGroup

- Bases: none
- Summary: Structural group of equations that share the same vectorized template.

### Methods

- `set_template(self, template_eq, template_vars)`
  Summary: Store the canonical template of the group.
- `add_indices(self, variable_indices, row_index)`
  Summary: Append one grouped equation instance.
- `get_index_matrix(self)`
  Summary: Return the grouped runtime index matrix.
- `get_row_indices(self)`
  Summary: Return the residual rows covered by the group.
- `get_template_eq(self)`
  Summary: Return the template equation.
- `get_template_vars(self)`
  Summary: Return the template runtime variables.

## Class: StructuralCompiledVectorKernel

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

## Class: StructuralCompiledResidualDispatcher

- Bases: none
- Summary: Residual dispatcher that orchestrates compiled group kernels explicitly.

### Methods

- No methods detected.

## Function: _compile_master_jacobian_kernel(ad_kernel, n_colors, cache_token)

Build the eager sparse Jacobian dispatcher.

## Class: StructuralCompiledResidualAssembler

- Bases: none
- Summary: Residual dispatcher that reuses preallocated grouped work buffers.

### Methods

- `evaluate(self, states, params, history, d_history, h, history2, data_out)`
  Summary: Evaluate the grouped residual system in place.
- `get_work_buffer(self)`
  Summary: Return the grouped work buffer.
- `get_build_stats(self)`
  Summary: Return residual assembler setup timings.

## Class: StructuralCompiledDirectResidualAssembler

- Bases: none
- Summary: Residual assembler backed by one monolithic in-place kernel.

### Methods

- `evaluate(self, states, params, history, d_history, h, history2, data_out)`
  Summary: No docstring provided.
- `get_work_buffer(self)`
  Summary: No docstring provided.
- `get_build_stats(self)`
  Summary: No docstring provided.

## Class: StructuralCompiledSparseADJacobian

- Bases: none
- Summary: Sparse structural AD Jacobian that writes directly into CSC storage.

### Methods

- `_build_column_rows(self)`
  Summary: Build the symbolic sparsity pattern column by column.
- `_build_csc_matrix(self)`
  Summary: Build the reusable CSC matrix shell and numeric data buffer.
- `_build_scatter_map(self)`
  Summary: Precompute the CSC scatter topology for colored JVPs.
- `_build_ad_kernel(self, use_cse, eager_machine_code)`
  Summary: Compile one generic eager AD kernel reused for every graph color.
- `evaluate(self, states, params, history, d_history, h, history2)`
  Summary: Evaluate the sparse Jacobian into the reusable CSC storage.
- `get_data_buffer(self)`
  Summary: Return the reusable CSC numeric buffer.
- `get_matrix(self)`
  Summary: Return the reusable CSC matrix shell.
- `get_build_stats(self)`
  Summary: Return sparse Jacobian build timings.

## Class: StructuralCompiledSparseFactorizationManager

- Bases: none
- Summary: Sparse linear-solve manager for ``StructuralCompiledSolver``.

### Methods

- `invalidate(self)`
  Summary: Drop the current numeric factorization while keeping all persistent shells.
- `has_factorization(self)`
  Summary: Return whether one numeric factorization is currently cached.
- `factorize(self)`
  Summary: Factorize the current Jacobian numeric values.
- `solve(self, rhs)`
  Summary: Solve the linear system using the current numeric factorization.
- `solve_fallback(self, rhs)`
  Summary: Solve the linear system with an iterative sparse fallback.
- `get_active_matrix(self)`
  Summary: Return the matrix used by the active numeric factorization path.
- `get_stats(self)`
  Summary: Return cumulative factorization-manager statistics.

## Class: StructuralCompiledSolver

- Bases: none
- Summary: Standalone structural EMT solver with eager kernels and reusable buffers.

### Methods

- `_build_vectorized_backend(self, method)`
  Summary: Analyze the symbolic structure and build the eager numerical backend.
- `get_last_sim_loop_time(self)`
  Summary: Return the last measured integration loop wall time.
- `is_vectorized_ready(self)`
  Summary: Return whether the eager backend has already been built.
- `get_residual_buffer(self)`
  Summary: Return the persistent residual buffer.
- `get_jacobian_data_buffer(self)`
  Summary: Return the persistent CSC numeric buffer.
- `get_backend_build_stats(self)`
  Summary: Return setup timings for the structural compiled backend build.
- `get_last_runtime_stats(self)`
  Summary: Return runtime statistics collected during the latest simulation.
- `simulate(self, x0, dx0, params0, boundary_updater)`
  Summary: Run the implicit EMT simulation with eager structural kernels.
