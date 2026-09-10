# VeraGridEngine Module: src/VeraGridEngine/Simulations/PowerFlow/NumericalMethods/fast_decoupled.py

- Original source path: `src/VeraGridEngine/Simulations/PowerFlow/NumericalMethods/fast_decoupled.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 1
- Representative imports: numpy, numpy.linalg, scipy.sparse.linalg, time, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.discrete_controls, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.basic_structures, VeraGridEngine.DataStructures.numerical_circuit

## Function: FDPF(nc, Vbus, S0, I0, Y0, Ybus, Yf, Yt, Yshunt_bus, B1, B2, pv_, pq_, pqv_, p_, vd_, Qmin, Qmax, bus_installed_power, tol, max_it, control_q, distribute_slack)

Fast decoupled power flow
