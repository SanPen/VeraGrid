# VeraGridEngine Module: src/VeraGridEngine/Simulations/Stochastic/stochastic_power_flow_driver.py

- Original source path: `src/VeraGridEngine/Simulations/Stochastic/stochastic_power_flow_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 0
- Representative imports: numpy, enum, VeraGridEngine.basic_structures, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.Simulations.Stochastic.stochastic_power_flow_results, VeraGridEngine.Simulations.Stochastic.stochastic_power_flow_input, VeraGridEngine.Compilers.circuit_to_data, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Simulations.PowerFlow.power_flow_worker, VeraGridEngine.enumerations, VeraGridEngine.Simulations.driver_template

## Class: StochasticPowerFlowType

- Bases: Enum
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: StochasticPowerFlowDriver

- Bases: DriverTemplate
- Summary: No docstring provided.

### Methods

- `get_steps(self)`
  Summary: Get time steps list of strings
- `update_progress_mt(self, res)`
  Summary: No docstring provided.
- `run_single_thread_mc(self, use_lhs)`
  Summary: :param use_lhs:
- `run(self)`
  Summary: Run the monte carlo simulation
- `cancel(self)`
  Summary: Cancel the simulation
