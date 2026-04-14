# VeraGridEngine Module: src/VeraGridEngine/Simulations/Rms/rms_driver.py

- Original source path: `src/VeraGridEngine/Simulations/Rms/rms_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, pandas, numpy, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Simulations.driver_template, VeraGridEngine.Simulations.Rms.rms_options, VeraGridEngine.Simulations.Rms.rms_results, VeraGridEngine.Simulations.Rms.rms_problem_factory, VeraGridEngine.Simulations.Rms.problems.rms_problem_dae, VeraGridEngine.Simulations.Rms.numerical.back_euler_fx, VeraGridEngine.enumerations, VeraGridEngine.Simulations.PowerFlow.power_flow_driver, VeraGridEngine.basic_structures

## Class: RmsSimulationDriver

- Bases: DriverTemplate
- Summary: No docstring provided.

### Methods

- `run(self)`
  Summary: Main function to initialize and run the system simulation.
- `run_time_simulation(self)`
  Summary: Performs the numerical integration using the chosen method.
