# VeraGridEngine Module: src/VeraGridEngine/Simulations/PowerFlow/NumericalMethods/gauss_power_flow.py

- Original source path: `src/VeraGridEngine/Simulations/PowerFlow/NumericalMethods/gauss_power_flow.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 1
- Representative imports: os, time, numpy, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.discrete_controls, VeraGridEngine.basic_structures

## Function: gausspf(nc, Ybus, Yf, Yt, Yshunt_bus, S0, I0, Y0, V0, pv, pq, p, pqv, vd, bus_installed_power, Qmin, Qmax, tol, max_it, control_q, distribute_slack, verbose, logger)

Gauss-Seidel Power flow
