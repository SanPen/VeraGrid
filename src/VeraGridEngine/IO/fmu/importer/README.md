# VeraGrid FMU Import

This package contains the in-progress FMU import infrastructure for VeraGrid.

Current scope:
- parse `modelDescription.xml`
- detect `CoSimulation` and `ModelExchange`
- validate bindings against FMI causality
- open and execute FMUs through FMPy

Why this lives in `trunk`:
- the integration with VeraGrid solvers is still under development
- the API is not stable yet
- RMS and EMT coupling are not implemented yet

Planned integration points:
- RMS: `src/VeraGridEngine/Simulations/Rms/numerical/back_euler_fx.py`
- EMT: `src/VeraGridEngine/Simulations/EMT/problems/emt_problem_dae.py`
- EMT solver boundary hooks: `src/VeraGridEngine/Simulations/EMT/solvers/jit_symbolic_solver.py`

Planned execution order:
1. RMS + Co-Simulation device FMUs
2. EMT + Co-Simulation device FMUs
3. RMS + Model Exchange device FMUs
4. EMT + Model Exchange device FMUs
