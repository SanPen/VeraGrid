# VeraGridEngine Module: src/VeraGridEngine/Simulations/NodalCapacity/nodal_capacity_ts_driver.py

- Original source path: `src/VeraGridEngine/Simulations/NodalCapacity/nodal_capacity_ts_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: datetime, numpy, pandas, typing, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.enumerations, VeraGridEngine.Simulations.OPF.opf_options, VeraGridEngine.Simulations.OPF.Formulations.linear_opf_ts, VeraGridEngine.Simulations.OPF.ac_opf_worker, VeraGridEngine.Simulations.NodalCapacity.nodal_capacity_options, VeraGridEngine.Simulations.NodalCapacity.nodal_capacity_ts_results, VeraGridEngine.Simulations.PowerFlow.power_flow_options, VeraGridEngine.Simulations.PowerFlow.power_flow_driver, VeraGridEngine.Simulations.ContinuationPowerFlow.continuation_power_flow_driver, VeraGridEngine.Simulations.ContinuationPowerFlow.continuation_power_flow_options, VeraGridEngine.Simulations.ContinuationPowerFlow.continuation_power_flow_input

## Class: NodalCapacityTimeSeriesDriver

- Bases: TimeSeriesDriverTemplate
- Summary: No docstring provided.

### Methods

- `opf_options(self)`
  Summary: Get the OptimalPowerFlowOptions options provides with the OpfOptions
- `pf_options(self)`
  Summary: Get the PowerFlow options provides with the OpfOptions
- `get_steps(self)`
  Summary: Get time steps list of strings
- `get_time_indices(self)`
  Summary: No docstring provided.
- `linear_opf(self, remote, batteries_energy_0)`
  Summary: Run a power flow for every circuit
- `non_linear_opf(self, remote, batteries_energy_0)`
  Summary: Run a power flow for every circuit
- `cpf(self, remote, batteries_energy_0)`
  Summary: Run a power flow for every circuit
- `add_report(self, eps)`
  Summary: Add a report of the results (in-place)
- `run(self)`
  Summary: :return:
