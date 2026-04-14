# VeraGridEngine Module: src/VeraGridEngine/Simulations/InvestmentsEvaluation/investments_evaluation_driver.py

- Original source path: `src/VeraGridEngine/Simulations/InvestmentsEvaluation/investments_evaluation_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: timeit, numpy, VeraGridEngine.Simulations.driver_template, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Utils.NumericalMethods.MVRSM_mo_pareto, VeraGridEngine.Simulations.InvestmentsEvaluation.investments_evaluation_results, VeraGridEngine.Simulations.InvestmentsEvaluation.investments_evaluation_options, VeraGridEngine.Simulations.InvestmentsEvaluation.Methods.NSGA_3, VeraGridEngine.Simulations.InvestmentsEvaluation.Methods.mixed_variable_NSGA_2, VeraGridEngine.Simulations.InvestmentsEvaluation.Methods.random_eval, VeraGridEngine.Simulations.InvestmentsEvaluation.Problems.black_box_problem_template, VeraGridEngine.enumerations, VeraGridEngine.basic_structures

## Class: InvestmentsEvaluationDriver

- Bases: DriverTemplate
- Summary: No docstring provided.

### Methods

- `initialize(self, max_iter)`
  Summary: Initialize the results
- `get_steps(self)`
  Summary: :return:
- `objective_function(self, x, record_results)`
  Summary: Function to evaluate a combination of investments
- `objective_function_so(self, x)`
  Summary: Single objective version of the objective function
- `evaluate_individual_investments(self)`
  Summary: Run a one-by-one investment evaluation without considering multiple evaluation groups at a time
- `independent_evaluation(self)`
  Summary: Sort investments in order and then evaluate cumulative combinations of increasingly expensive investments
- `optimized_evaluation_mvrsm_pareto(self)`
  Summary: Run an optimized investment evaluation without considering multiple evaluation groups at a time
- `optimized_evaluation_nsga3(self)`
  Summary: Run an optimized investment evaluation with NSGA3
- `randomized_evaluation(self)`
  Summary: Run purely random evaluations, without any optimization
- `optimized_evaluation_mixed_nsga2(self)`
  Summary: Run an optimized investment evaluation on mixed variables with NSGA2
- `run(self)`
  Summary: run the QThread
