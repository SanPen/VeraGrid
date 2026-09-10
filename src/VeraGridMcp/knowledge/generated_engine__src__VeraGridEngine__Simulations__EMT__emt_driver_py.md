# VeraGridEngine Module: src/VeraGridEngine/Simulations/EMT/emt_driver.py

- Original source path: `src/VeraGridEngine/Simulations/EMT/emt_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: numpy, pandas, typing, VeraGridEngine, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Simulations.driver_template, VeraGridEngine.Simulations.EMT.emt_options, VeraGridEngine.Simulations.EMT.emt_results, VeraGridEngine.Simulations.EMT.emt_problem_factory, VeraGridEngine.Simulations.EMT.emt_solver_factory, VeraGridEngine.Simulations.EMT.problems.emt_problem_dae, VeraGridEngine.Simulations.PowerFlow.power_flow_results_3ph, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.Simulations.EMT.solvers.jit_symbolic_solver, VeraGridEngine.Simulations.EMT.solvers.solver_AD, VeraGridEngine.Simulations.EMT.solvers.StructuralVectorizedSolver

## Class: EmtSimulationDriver

- Bases: DriverTemplate
- Summary: No docstring provided.

### Methods

- `run(self)`
  Summary: Main function to initialize and run the system simulation.
- `run_time_simulation(self)`
  Summary: Performs the EMTP loop using the chosen method.
