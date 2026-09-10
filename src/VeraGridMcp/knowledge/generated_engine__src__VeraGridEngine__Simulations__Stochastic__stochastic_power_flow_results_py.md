# VeraGridEngine Module: src/VeraGridEngine/Simulations/Stochastic/stochastic_power_flow_results.py

- Original source path: `src/VeraGridEngine/Simulations/Stochastic/stochastic_power_flow_results.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: numpy, sklearn.ensemble, VeraGridEngine.basic_structures, VeraGridEngine.Simulations.results_table, VeraGridEngine.Simulations.results_template, VeraGridEngine.enumerations

## Class: StochasticPowerFlowResults

- Bases: ResultsTemplate
- Summary: No docstring provided.

### Methods

- `append_batch(self, mcres)`
  Summary: Append a batch (a StochasticPowerFlowResults object) to this object
- `get_voltage_sum(self)`
  Summary: Return the voltage summation
- `compile(self)`
  Summary: Compiles the final Monte Carlo values by running an online mean and
- `query_voltage(self, power_array)`
  Summary: Fantastic function that allows to query the voltage from the sampled points without having to run power Sf
- `get_index_loading_cdf(self, max_val)`
  Summary: Find the elements where the CDF is greater or equal to a value
- `mdl(self, result_type)`
  Summary: Plot the results
