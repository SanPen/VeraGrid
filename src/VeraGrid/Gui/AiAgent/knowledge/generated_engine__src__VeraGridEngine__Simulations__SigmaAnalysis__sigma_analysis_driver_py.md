# VeraGridEngine Module: src/VeraGridEngine/Simulations/SigmaAnalysis/sigma_analysis_driver.py

- Original source path: `src/VeraGridEngine/Simulations/SigmaAnalysis/sigma_analysis_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 2
- Representative imports: numpy, numba, matplotlib, typing, VeraGridEngine.basic_structures, VeraGridEngine.Simulations.PowerFlow.power_flow_options, VeraGridEngine.Simulations.results_table, VeraGridEngine.enumerations, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Compilers.circuit_to_data, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.helm_power_flow, VeraGridEngine.Simulations.driver_template, VeraGridEngine.basic_structures

## Class: SigmaAnalysisResults

- Bases: none
- Summary: SigmaAnalysisResults

### Methods

- `apply_from_island(self, results, b_idx)`
  Summary: Apply results from another island circuit to the circuit results represented
- `plot(self, fig, ax, n_points)`
  Summary: Plot the sigma analysis
- `mdl(self, result_type, indices, names)`
  Summary: :param result_type:

## Function: multi_island_sigma(multi_circuit, options, logger)

Multiple islands power flow (this is the most generic power flow function)

## Function: sigma_distance(sigma_real, sigma_imag)

Distance to the collapse in the sigma space

## Class: SigmaAnalysisDriver

- Bases: DriverTemplate
- Summary: No docstring provided.

### Methods

- `get_steps(self)`
  Summary: :return:
- `run(self)`
  Summary: Pack run_pf for the QThread
- `cancel(self)`
  Summary: No docstring provided.
