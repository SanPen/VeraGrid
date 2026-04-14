# VeraGridEngine Module: src/VeraGridEngine/Simulations/OPF/opf_driver.py

- Original source path: `src/VeraGridEngine/Simulations/OPF/opf_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: numpy, typing, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.enumerations, VeraGridEngine.Simulations.OPF.opf_options, VeraGridEngine.Simulations.OPF.Formulations.linear_opf_ts, VeraGridEngine.Simulations.OPF.opf_results, VeraGridEngine.Simulations.OPF.ac_opf_worker, VeraGridEngine.Simulations.PowerFlow.power_flow_options, VeraGridEngine.Simulations.driver_template, VeraGridEngine.Simulations.OPF.simple_dispatch_ts, VeraGridEngine.Compilers.circuit_to_newton_pa

## Class: OptimalPowerFlowDriver

- Bases: TimeSeriesDriverTemplate
- Summary: No docstring provided.

### Methods

- `pf_options(self)`
  Summary: Get the PowerFlow options provides with the OpfOptions
- `add_report(self)`
  Summary: Add a report of the results (in-place)
- `opf(self, remote, batteries_energy_0)`
  Summary: Run a power flow for every circuit
- `run(self)`
  Summary: :return:
