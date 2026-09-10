# VeraGridEngine Module: src/VeraGridEngine/Simulations/InvestmentsEvaluation/Problems/black_box_problem_template.py

- Original source path: `src/VeraGridEngine/Simulations/InvestmentsEvaluation/Problems/black_box_problem_template.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: typing, numpy, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Devices.Aggregation.investment, VeraGridEngine.basic_structures

## Class: BlackBoxProblemTemplate

- Bases: none
- Summary: No docstring provided.

### Methods

- `get_investments_for_combination(self, x)`
  Summary: Get the list of the investments that belong to a certain combination
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
