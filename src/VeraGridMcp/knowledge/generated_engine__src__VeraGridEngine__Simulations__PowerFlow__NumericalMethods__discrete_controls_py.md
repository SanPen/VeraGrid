# VeraGridEngine Module: src/VeraGridEngine/Simulations/PowerFlow/NumericalMethods/discrete_controls.py

- Original source path: `src/VeraGridEngine/Simulations/PowerFlow/NumericalMethods/discrete_controls.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 5
- Representative imports: numpy, numba, typing, VeraGridEngine.enumerations, VeraGridEngine.basic_structures

## Function: get_q_increment(V1, V2, k)

Logistic function to get the Q increment gain using the difference

## Function: control_q_direct(V, Vm, Vset, Q, Qmax, Qmin, types, original_types, verbose)

Change the buses type in order to control the generators reactive power.

## Function: control_q_inside_method(Scalc, S0, pv, pq, pqv, p, Qmin, Qmax)

Control of reactive power within the numerical method

## Function: control_q_for_generalized_method(Scalc, S0, pv, i_u_vm, i_k_q, Qmin, Qmax)

Control of reactive power within the numerical method

## Function: compute_slack_distribution(Scalc, vd, bus_installed_power)

Slack distribution logic
