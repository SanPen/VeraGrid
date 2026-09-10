# VeraGridEngine Module: src/VeraGridEngine/Simulations/InvestmentsEvaluation/Problems/power_flow_problem.py

- Original source path: `src/VeraGridEngine/Simulations/InvestmentsEvaluation/Problems/power_flow_problem.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 1
- Representative imports: typing, numpy, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.basic_structures, VeraGridEngine.Simulations.InvestmentsEvaluation.Problems.black_box_problem_template, VeraGridEngine.Utils.scores, VeraGridEngine.Simulations.PowerFlow.power_flow_driver, VeraGridEngine.Simulations.PowerFlow.power_flow_options, VeraGridEngine.Devices.Aggregation.investment

## Function: power_flow_function(inv_list, grid, pf_options, branches_cost, vm_cost, vm_max, vm_min, va_cost, va_max, va_min)

Compute the power flow of the grid given an investments group

## Class: PowerFlowInvestmentProblem

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
