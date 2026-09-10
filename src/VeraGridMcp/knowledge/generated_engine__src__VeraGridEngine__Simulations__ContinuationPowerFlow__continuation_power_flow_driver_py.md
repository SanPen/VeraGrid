# VeraGridEngine Module: src/VeraGridEngine/Simulations/ContinuationPowerFlow/continuation_power_flow_driver.py

- Original source path: `src/VeraGridEngine/Simulations/ContinuationPowerFlow/continuation_power_flow_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, numpy, typing, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Compilers.circuit_to_data, VeraGridEngine.Simulations.PowerFlow.power_flow_worker, VeraGridEngine.Simulations.ContinuationPowerFlow.continuation_power_flow, VeraGridEngine.Simulations.ContinuationPowerFlow.continuation_power_flow_options, VeraGridEngine.Simulations.ContinuationPowerFlow.continuation_power_flow_input, VeraGridEngine.Simulations.ContinuationPowerFlow.continuation_power_flow_results, VeraGridEngine.enumerations, VeraGridEngine.Simulations.driver_template

## Class: ContinuationPowerFlowDriver

- Bases: DriverTemplate
- Summary: No docstring provided.

### Methods

- `get_steps(self)`
  Summary: List of steps
- `progress_callback(self, lmbda)`
  Summary: Send progress report
- `run_at(self, t_idx)`
  Summary: run the voltage collapse simulation
- `run(self)`
  Summary: run the voltage collapse simulation
