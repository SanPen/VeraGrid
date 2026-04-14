# VeraGridEngine Module: src/VeraGridEngine/Utils/Symbolic/diagnostic.py

- Original source path: `src/VeraGridEngine/Utils/Symbolic/diagnostic.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 3
- Top-level function count: 7
- Representative imports: __future__, logging, warnings, typing, numpy

## Class: NewtonDiagnosticsConfig

- Bases: none
- Summary: Configuration for Newton linear-solve diagnostics.

### Methods

- No methods detected.

## Class: NewtonSolveContext

- Bases: none
- Summary: Per-solve context, passed by the caller.

### Methods

- No methods detected.

## Function: _emit(logger, level, msg)

Emit a message either via logger (if configured) or via print as a fallback.

## Function: _format_ctx(ctx)

No docstring provided.

## Function: with_newton_diagnostics(primary_solve, fallback_solve, collector, config, logger, solver_name, matrix_getter)

Decorate a linear solver with Jacobian conditioning diagnostics and fallback LS solve.

## Function: maybe_check_index1(jacobian, n_state, ctx, config, logger)

Optionally validate the algebraic Jacobian block associated with an index-1 DAE.

## Function: maybe_apply_backtracking(x_iter, delta, res_norm, trial_x, trial_res, evaluate_residual, config)

Optionally apply backtracking to a Newton step.

## Function: dense_lstsq_fallback(A, b)

Dense least-squares fallback using np.linalg.lstsq.

## Function: sparse_lsqr_fallback(A, b)

Sparse least-squares fallback using scipy.sparse.linalg.lsqr.

## Class: NewtonTraceCollector

- Bases: none
- Summary: Collects numerical diagnostics during a simulation run.

### Methods

- `record(self, ctx, res_norm, dx, cond, fallback)`
  Summary: Append one Newton diagnostics record.
- `to_dataframe(self)`
  Summary: Convert the collected records into a pandas DataFrame.
