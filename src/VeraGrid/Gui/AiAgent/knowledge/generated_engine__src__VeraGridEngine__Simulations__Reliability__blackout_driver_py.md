# VeraGridEngine Module: src/VeraGridEngine/Simulations/Reliability/blackout_driver.py

- Original source path: `src/VeraGridEngine/Simulations/Reliability/blackout_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 3
- Top-level function count: 0
- Representative imports: pandas, numpy, VeraGridEngine.Simulations.PowerFlow.power_flow_worker, VeraGridEngine.Simulations.PowerFlow.power_flow_driver, VeraGridEngine.Simulations.Stochastic.stochastic_power_flow_results, VeraGridEngine.Simulations.Stochastic.stochastic_power_flow_driver, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Compilers.circuit_to_data, VeraGridEngine.enumerations, VeraGridEngine.Simulations.driver_template

## Class: CascadingReportElement

- Bases: none
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: CascadingResults

- Bases: none
- Summary: No docstring provided.

### Methods

- `get_failed_idx(self)`
  Summary: Return the array of all failed Branches
- `get_table(self)`
  Summary: Get DataFrame of the failed elements
- `plot(self)`
  Summary: No docstring provided.

## Class: CascadingDriver

- Bases: DriverTemplate
- Summary: No docstring provided.

### Methods

- `remove_elements(circuit, loading_vector, idx)`
  Summary: Remove Branches based on loading
- `remove_probability_based(numerical_circuit, results, max_val, min_prob)`
  Summary: Remove Branches based on their chance of overload
- `perform_step_run(self)`
  Summary: Perform only one step cascading
- `run(self)`
  Summary: Run the monte carlo simulation
- `get_failed_idx(self)`
  Summary: Return the array of all failed Branches
- `get_table(self)`
  Summary: Get DataFrame of the failed elements
- `cancel(self)`
  Summary: Cancel the simulation
