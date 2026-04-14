# VeraGridEngine Module: src/VeraGridEngine/Simulations/PowerFlow/NumericalMethods/iwamoto_newton_raphson.py

- Original source path: `src/VeraGridEngine/Simulations/PowerFlow/NumericalMethods/iwamoto_newton_raphson.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 2
- Representative imports: time, scipy, numpy, VeraGridEngine.Utils.NumericalMethods.sparse_solve, VeraGridEngine.Utils.Sparse.csc2, VeraGridEngine.Simulations.Derivatives.ac_jacobian, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.discrete_controls, VeraGridEngine.basic_structures

## Function: mu(Ybus, J, incS, dV, dx, block1_idx, block2_idx, block3_idx)

Calculate the Iwamoto acceleration parameter as described in:

## Function: IwamotoNR(nc, Ybus, Yf, Yt, Yshunt_bus, S0, V0, I0, Y0, pv_, pq_, pqv_, p_, vd_, Qmin, Qmax, tol, max_it, control_q, robust, logger)

Solves the power flow using a full Newton's method with the Iwamoto optimal step factor.
