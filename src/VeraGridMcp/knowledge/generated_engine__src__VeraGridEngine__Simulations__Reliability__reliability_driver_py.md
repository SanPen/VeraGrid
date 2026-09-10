# VeraGridEngine Module: src/VeraGridEngine/Simulations/Reliability/reliability_driver.py

- Original source path: `src/VeraGridEngine/Simulations/Reliability/reliability_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 1
- Representative imports: numba, numpy, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, VeraGridEngine.Simulations.PowerFlow.power_flow_worker, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Simulations.driver_template, VeraGridEngine.Simulations.OPF.simple_dispatch_ts, VeraGridEngine.Simulations.Reliability.reliability, VeraGridEngine.Simulations.Reliability.reliability_results, VeraGridEngine.Compilers.circuit_to_data

## Function: get_gen_pmax(nt, k, Snom, P_array, active_array, dispatchable_array)

Get a generator array of Pmax given the active and dispatchable conditions

## Class: ReliabilityStudyDriver

- Bases: DriverTemplate
- Summary: No docstring provided.

### Methods

- `progress_callback(self, lmbda)`
  Summary: Send progress report
- `run(self)`
  Summary: Run reliability
- `run_adequacy_reliability(self)`
  Summary: run the voltage collapse simulation
- `run_grid_reliability(self)`
  Summary: run the voltage collapse simulation
- `cancel(self)`
  Summary: No docstring provided.
