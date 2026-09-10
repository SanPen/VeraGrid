# VeraGridEngine Module: src/VeraGridEngine/Utils/Symbolic/jit_compiler.py

- Original source path: `src/VeraGridEngine/Utils/Symbolic/jit_compiler.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

Module: JIT Equation Compiler & Numerical Discretization Engine

## Module Surface

- Class count: 16
- Top-level function count: 14
- Representative imports: numpy, abc, enum, numba, typing, os, pathlib, importlib.util, hashlib, scipy.sparse, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.enumerations, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.basic_structures

## Class: GeneratedKernelCacheEntry

- Bases: none
- Summary: In-process cache entry for one generated eager kernel.

### Methods

- `get_python_function(self)`
  Summary: Return the generated Python function.
- `get_signature_tpe(self)`
  Summary: Return the eager Numba signature.

## Function: _build_equation_compiler_residual_cache_key(equations, var_map, param_map, method_name, use_cse, offset, inplace)

Return a deterministic cache key for one ``EquationCompiler`` residual kernel.

## Function: _build_equation_compiler_ad_cache_key(equations, var_map, param_map, method_name, use_cse, active_indices)

Return a deterministic cache key for one ``EquationCompiler`` AD kernel.

## Function: _build_equation_compiler_matrix_cache_key(template_eq, var_map, param_map, method_name, col_map)

Return a deterministic cache key for one ``MatrixVectorizedCompiler`` kernel.

## Class: GeneratedKernelCache

- Bases: none
- Summary: In-process cache for generated eager kernels keyed by structural signature.

### Methods

- `get_entry(self, cache_kind, cache_key)`
  Summary: Return one cached kernel entry.
- `set_entry(self, cache_kind, cache_key, entry)`
  Summary: Store one cached kernel entry.

## Function: _is_zero(s)

No docstring provided.

## Function: _is_one(s)

No docstring provided.

## Function: _compile_to_file(full_source, func_name)

Writes source code to a file in __pycache_jit__ and imports it.

## Function: _build_codegen_cache_key(payload)

Return a deterministic cache key for generated eager kernels.

## Function: _fingerprint_codegen_var(node, var_map, param_map, method_name, col_map)

Return a stable code-generation fingerprint for one variable node.

## Function: _fingerprint_codegen_expr(node, var_map, param_map, method_name, col_map)

Return a stable code-generation fingerprint for one symbolic expression.

## Function: _build_residual_codegen_cache_key(equations, var_map, param_map, method_name, use_cse, offset, n_variables, n_parameters)

Return the cache key of one residual kernel.

## Function: _build_ad_codegen_cache_key(equations, var_map, param_map, method_name, use_cse, active_indices, n_variables, n_parameters)

Return the cache key of one AD kernel.

## Function: _build_matrix_codegen_cache_key(template_eq, var_map, param_map, method_name, col_map, n_variables, n_parameters)

Return the cache key of one matrix-vectorized kernel.

## Class: DiscretizationMethod

- Bases: ABC
- Summary: Abstract base class for discretization strategies.

### Methods

- `discretize(self, state_idx, h_var)`
  Summary: No docstring provided.
- `discretize_dot(self, state_idx, h_var, seeds_var)`
  Summary: No docstring provided.

## Class: TrapezoidalMethod

- Bases: DiscretizationMethod
- Summary: No docstring provided.

### Methods

- `discretize(self, state_idx, h_var)`
  Summary: No docstring provided.
- `discretize_dot(self, state_idx, h_var, seeds_var)`
  Summary: No docstring provided.

## Class: BackwardEulerMethod

- Bases: DiscretizationMethod
- Summary: No docstring provided.

### Methods

- `discretize(self, state_idx, h_var)`
  Summary: No docstring provided.
- `discretize_dot(self, state_idx, h_var, seeds_var)`
  Summary: No docstring provided.

## Class: BDF2Method

- Bases: DiscretizationMethod
- Summary: No docstring provided.

### Methods

- `discretize(self, state_idx, h_var)`
  Summary: No docstring provided.
- `discretize_dot(self, state_idx, h_var, seeds_var)`
  Summary: No docstring provided.

## Class: ContinuousMethod

- Bases: DiscretizationMethod
- Summary: Strategy for continuous systems (RMS Small Signal). Does not discretize.

### Methods

- `discretize(self, state_idx, h_var)`
  Summary: No docstring provided.
- `discretize_dot(self, state_idx, h_var, seeds_var)`
  Summary: No docstring provided.

## Class: SubexpressionAnalyzer

- Bases: none
- Summary: Find and catalog subexpressions that appear multiple times.

### Methods

- `analyze(self, equations)`
  Summary: No docstring provided.
- `_count_subexpressions(self, node)`
  Summary: No docstring provided.
- `_calculate_complexity(self, node)`
  Summary: No docstring provided.
- `hash_expr(self, node)`
  Summary: No docstring provided.
- `_expr_to_canonical_string(self, node)`
  Summary: No docstring provided.

## Class: SymbolicToPythonVisitor

- Bases: none
- Summary: No docstring provided.

### Methods

- `_prec(self, node)`
  Summary: Return precedence of a node. Non-operators get 'infinite' precedence.
- `_maybe_parenthesize(self, code, child_node, parent_op, parent_prec, side)`
  Summary: Decide whether to wrap child expression in parentheses.
- `visit(self, node, precedence)`
  Summary: Dispatches node processing using explicit type matching to avoid reflection.
- `generic_visit(self, node, _)`
  Summary: No docstring provided.
- `visit_binop(self, node, prec)`
  Summary: Emit Python code for a binary operation with correct parentheses.
- `visit_unop(self, node, _)`
  Summary: No docstring provided.
- `visit_const(self, node, _)`
  Summary: No docstring provided.
- `visit_var(self, node, prec)`
  Summary: No docstring provided.
- `visit_diffvar(self, node, prec)`
  Summary: No docstring provided.
- `visit_func(self, node, _)`
  Summary: No docstring provided.

## Class: ADVisitor

- Bases: SymbolicToPythonVisitor
- Summary: No docstring provided.

### Methods

- `generic_visit(self, node, _)`
  Summary: No docstring provided.
- `visit(self, node, precedence)`
  Summary: Dispatches node processing for Automatic Differentiation using explicit type matching.
- `visit_const(self, node, _)`
  Summary: No docstring provided.
- `visit_var(self, node, _)`
  Summary: No docstring provided.
- `visit_diffvar(self, node, prec)`
  Summary: No docstring provided.
- `visit_binop(self, node, prec)`
  Summary: No docstring provided.
- `visit_unop(self, node, _)`
  Summary: No docstring provided.
- `visit_func(self, node, _)`
  Summary: No docstring provided.

## Class: EquationCompiler

- Bases: none
- Summary: Main interface for compiling symbolic equations into executable functions.

### Methods

- `compile(self, equations, func_name, use_cse, offset, inplace)`
  Summary: No docstring provided.
- `compile_ad_kernel(self, equations, func_name, use_cse, active_indices)`
  Summary: No docstring provided.

## Class: MatrixVectorizedVisitor

- Bases: SymbolicToPythonVisitor
- Summary: HPC-optimized visitor. Instead of performing dictionary lookups (slow),

### Methods

- `visit_var(self, node, _)`
  Summary: No docstring provided.
- `visit_diffvar(self, node, prec)`
  Summary: No docstring provided.

## Class: MatrixVectorizedCompiler

- Bases: EquationCompiler
- Summary: Compiler utilizing the Matrix Vectorized Visitor.

### Methods

- `compile_matrix_kernel(self, template_eq, func_name, template_vars)`
  Summary: No docstring provided.

## Class: EagerKernelKind

- Bases: Enum
- Summary: Enumeration of eager kernel application binary interfaces.

### Methods

- No methods detected.

## Function: _get_cse_sort_index(cse_item)

Return the numeric order of a generated CSE temporary.

## Function: _reset_symbolic_codegen_state(visitor)

Reset visitor caches before and after eager code generation.

## Class: EagerEquationCompiler

- Bases: EquationCompiler
- Summary: Strict eager compiler that emits in-place kernels with explicit signatures.

### Methods

- `generate_signature(self, kernel_tpe, n_variables, n_parameters, nnz, with_history2)`
  Summary: Build the eager Numba signature for a generated kernel.
- `compile(self, equations, func_name, use_cse, offset, inplace)`
  Summary: Compile residual equations into an in-place eager kernel.
- `compile_ad_kernel(self, equations, func_name, use_cse, active_indices)`
  Summary: Compile a sparse forward-mode AD kernel into an in-place eager function.
- `compile_matrix_kernel(self, template_eq, func_name, template_vars)`
  Summary: Compile a vectorized matrix kernel into an in-place eager function.

## Class: RMSCompiler

- Bases: EquationCompiler
- Summary: O(N) compiler for RMS (Root Mean Square) Continuous-Time Simulations.

### Methods

- `compile_rhs(self, equations, func_name)`
  Summary: Compiles the residual equations (RHS) into a fast, executable JIT function.
- `compile_sparse_jacobian(self, eqs, wrt_vars, func_name)`
  Summary: Compiles a sparse Jacobian evaluator using an O(N) structural extraction algorithm.
