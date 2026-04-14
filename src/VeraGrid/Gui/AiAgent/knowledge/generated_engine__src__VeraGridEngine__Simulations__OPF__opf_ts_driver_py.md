# VeraGridEngine Module: src/VeraGridEngine/Simulations/OPF/opf_ts_driver.py

- Original source path: `src/VeraGridEngine/Simulations/OPF/opf_ts_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: datetime, numpy, pandas, typing, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.enumerations, VeraGridEngine.Simulations.OPF.opf_options, VeraGridEngine.Simulations.OPF.Formulations.linear_opf_ts, VeraGridEngine.Simulations.OPF.simple_dispatch_ts, VeraGridEngine.Simulations.OPF.ac_opf_worker, VeraGridEngine.Simulations.OPF.opf_ts_results, VeraGridEngine.Simulations.PowerFlow.power_flow_options, VeraGridEngine.Simulations.driver_template, VeraGridEngine.Compilers.circuit_to_newton_pa, VeraGridEngine.Simulations.Clustering.clustering_results, VeraGridEngine.basic_structures

## Class: OptimalPowerFlowTimeSeriesDriver

- Bases: TimeSeriesDriverTemplate
- Summary: No docstring provided.

### Methods

- `pf_options(self)`
  Summary: Get the PowerFlow options provides with the OpfOptions
- `get_steps(self)`
  Summary: Get time steps list of strings
- `run_linear_opf(self)`
  Summary: :return:
- `run_linear_opf_indices(self, time_indices, energy_0, fluid_level_0)`
  Summary: No docstring provided.
- `run_greedy_dispatch(self)`
  Summary: :return:
- `run_greedy_dispatch_indices(self, time_indices)`
  Summary: :param time_indices:
- `run_non_linear_opf(self)`
  Summary: :return:
- `run_nonlinear_opf_indices(self, time_indices)`
  Summary: :param time_indices:
- `opf(self, remote, batteries_energy_0)`
  Summary: Run a power flow for every circuit
- `opf_by_groups(self)`
  Summary: Run the OPF by groups
- `add_report(self, eps)`
  Summary: Add a report of the results (in-place)
- `run(self)`
  Summary: :return:
