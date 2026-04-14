# VeraGridEngine Module: src/VeraGridEngine/Simulations/Rms/initialization.py

- Original source path: `src/VeraGridEngine/Simulations/Rms/initialization.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 6
- Representative imports: cProfile, time, typing, numpy, collections, VeraGridEngine.Utils.Symbolic.jit_compiler, scipy.sparse, VeraGridEngine.Utils.Symbolic.compiled_functions, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.Utils.Symbolic.block, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.basic_structures

## Function: build_init_vars_vector(uid2idx_vars, mapping)

Helper function to build the initial vector

## Function: solve_secant(eq_fn, x, idx, event_params_array, params_array, tol, max_iter)

No docstring provided.

## Function: solve_newton(eq_fn, x, idx, event_params_array, params_array, dummy_diff, tol, max_iter, h)

No docstring provided.

## Function: init_explicit(mdl, sys_vars, variable_parameters, event_parameters_eqs, constant_parameters, init_guess, uid2idx_vars, uid2idx_params, uid2idx_event_params, compiler_names_dict, alias_names_dict, VARIABLE_PARAMS_NAME, TIME_NAME, VARS_NAME, DIFF_NAME, CONSTANT_PARAMS_NAME)

initialize model using explicit equations

## Function: init_custom(mdl, init_guess)

No docstring provided.

## Class: PseudoTransientInitProblem

- Bases: none
- Summary: Lightweight problem class for pseudo-transient initialization of a single device block.

### Methods

- `_compile_functions(self, VARS_NAME, DIFF_NAME, VARIABLE_PARAMS_NAME, CONSTANT_PARAMS_NAME)`
  Summary: Compile RHS and derivative functions for the block.
- `get_all_vars_number(self)`
  Summary: No docstring provided.
- `get_states_number(self)`
  Summary: No docstring provided.
- `get_algebraic_var_number(self)`
  Summary: No docstring provided.
- `get_diff_var_number(self)`
  Summary: No docstring provided.
- `get_algebraic_vars(self)`
  Summary: No docstring provided.
- `rhs_algebraic(self, x, dx)`
  Summary: Evaluate RHS for algebraic equations.
- `rhs_state(self, x, dx)`
  Summary: Evaluate RHS for state equations.
- `get_dx(self, x, xn, dx, h)`
  Summary: Compute derivatives.
- `update_variable_params(self, t)`
  Summary: Update variable parameters at time t.
- `_compute_numerical_jacobian(self, x, dx, h)`
  Summary: Compute Jacobian numerically using finite differences.
- `_compute_rhs_full(self, x, dx, h)`
  Summary: Compute full RHS (state + algebraic) for Jacobian computation.
- `get_j11(self, x, dx, h)`
  Summary: Jacobian of state equations w.r.t. state variables.
- `get_j12(self, x, dx, h)`
  Summary: Jacobian of state equations w.r.t. algebraic variables.
- `get_j21(self, x, dx, h)`
  Summary: Jacobian of algebraic equations w.r.t. state variables.
- `get_j22(self, x, dx, h)`
  Summary: Jacobian of algebraic equations w.r.t. algebraic variables.
- `uid2idx_vars(self)`
  Summary: No docstring provided.

## Function: init_pseudo_transient(mdl, sys_vars, variable_parameters, event_parameters_eqs, constant_parameters, init_guess, uid2idx_vars, uid2idx_params, uid2idx_event_params, compiler_names_dict, alias_names_dict, VARIABLE_PARAMS_NAME, TIME_NAME, VARS_NAME, DIFF_NAME, CONSTANT_PARAMS_NAME, dtau0, max_iter, tol)

Initialize model using pseudo-transient method.
