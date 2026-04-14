# VeraGridEngine Module: src/VeraGridEngine/Simulations/ContingencyAnalysis/contingency_analysis_driver.py

- Original source path: `src/VeraGridEngine/Simulations/ContingencyAnalysis/contingency_analysis_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, numpy, typing, VeraGridEngine.Compilers.circuit_to_gslv, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.enumerations, VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_results, VeraGridEngine.Simulations.driver_template, VeraGridEngine.Compilers.circuit_to_data, VeraGridEngine.Simulations.LinearFactors.linear_analysis, VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_options, VeraGridEngine.Simulations.ContingencyAnalysis.Methods.nonlinear_contingency_analysis, VeraGridEngine.Simulations.ContingencyAnalysis.Methods.linear_contingency_analysis, VeraGridEngine.Simulations.ContingencyAnalysis.Methods.helm_contingency_analysis, VeraGridEngine.Compilers.circuit_to_bentayga, VeraGridEngine.Compilers.circuit_to_newton_pa

## Class: ContingencyAnalysisDriver

- Bases: DriverTemplate
- Summary: Contingency analysis driver

### Methods

- `get_steps(self)`
  Summary: Get variations list of strings
- `run_at(self, t_idx, t_prob)`
  Summary: Run the contingency at a time point
- `run(self)`
  Summary: :return:
