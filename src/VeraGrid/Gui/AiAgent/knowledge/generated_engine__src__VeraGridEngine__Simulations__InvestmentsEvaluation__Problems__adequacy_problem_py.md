# VeraGridEngine Module: src/VeraGridEngine/Simulations/InvestmentsEvaluation/Problems/adequacy_problem.py

- Original source path: `src/VeraGridEngine/Simulations/InvestmentsEvaluation/Problems/adequacy_problem.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 3
- Representative imports: __future__, numpy, numba, scipy.sparse, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Compilers.circuit_to_data, VeraGridEngine.basic_structures, VeraGridEngine.Simulations.InvestmentsEvaluation.Problems.black_box_problem_template, VeraGridEngine.Simulations.Reliability.reliability, VeraGridEngine.Simulations.OPF.simple_dispatch_ts

## Function: correct_x(x, lb, ub)

Correct x in place to the given boundaries

## Function: apply_actives_mask(original_active, mask_indices, mask, years_starts_indices)

:param original_active:

## Function: determine_starting_index_of_every_year(index)

Find the index where each different year starts

## Class: AdequacyInvestmentProblem

- Bases: BlackBoxProblemTemplate
- Summary: No docstring provided.

### Methods

- `n_objectives(self)`
  Summary: Number of objectives (size of f)
- `n_vars(self)`
  Summary: Number of variables (size of x)
- `get_objectives_names(self)`
  Summary: Get a list of names for the elements of f
- `get_vars_names(self)`
  Summary: Get a list of names for the elements of x
- `objective_function(self, x)`
  Summary: Evaluate x and return f(x)
