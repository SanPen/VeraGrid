# VeraGridEngine Module: src/VeraGridEngine/Simulations/PowerFlow/NumericalMethods/linearized_power_flow.py

- Original source path: `src/VeraGridEngine/Simulations/PowerFlow/NumericalMethods/linearized_power_flow.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 3
- Representative imports: time, warnings, scipy.sparse, numpy, VeraGridEngine.Utils.NumericalMethods.sparse_solve, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.basic_structures

## Function: linear_pf(nc, Ybus, Bpqpv, Bref, Bf, S0, I0, Y0, V0, tau, vd, no_slack, pq, pv)

Solves a linear-DC power flow.

## Function: acdc_lin_pf(nc, Bbus, Bf, Gbus, Gf, ac, dc, vd, pv, S0, I0, Y0, V0, tau)

Solves a linear-ACDC power flow.

## Function: lacpf(nc, Ybus, Yf, Yt, Ys, Yshunt_bus, S0, V0, pq, pv, vd, logger)

Linearized AC Load Flow
