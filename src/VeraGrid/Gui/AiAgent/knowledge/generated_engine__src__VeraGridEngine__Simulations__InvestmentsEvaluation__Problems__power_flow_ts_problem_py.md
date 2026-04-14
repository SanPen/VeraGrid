# VeraGridEngine Module: src/VeraGridEngine/Simulations/InvestmentsEvaluation/Problems/power_flow_ts_problem.py

- Original source path: `src/VeraGridEngine/Simulations/InvestmentsEvaluation/Problems/power_flow_ts_problem.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 1
- Representative imports: typing, numpy, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Simulations.InvestmentsEvaluation.Problems.black_box_problem_template, VeraGridEngine.Utils.scores, VeraGridEngine.Simulations.PowerFlow.power_flow_ts_driver, VeraGridEngine.Simulations.PowerFlow.power_flow_options, VeraGridEngine.Simulations.OPF.opf_ts_results, VeraGridEngine.Simulations.Clustering.clustering_results, VeraGridEngine.Devices.Aggregation.investment, VeraGridEngine.enumerations, VeraGridEngine.basic_structures

## Function: power_flow_ts_function(inv_list, grid, pf_options, time_indices, opf_time_series_results, clustering_results, engine, branches_cost, vm_cost, vm_max, vm_min, va_cost, va_max, va_min)

Compute the power flow of the grid given an investments group

## Class: TimeSeriesPowerFlowInvestmentProblem

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
