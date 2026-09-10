# VeraGridEngine Module: src/VeraGridEngine/Simulations/PowerFlow/NumericalMethods/helm_power_flow.py

- Original source path: `src/VeraGridEngine/Simulations/PowerFlow/NumericalMethods/helm_power_flow.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 11
- Representative imports: pandas, numpy, numba, time, warnings, scipy.sparse, scipy.sparse, scipy.sparse.linalg, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.basic_structures

## Function: epsilon(Sn, n, E)

Fast recursive Wynn's epsilon algorithm from:

## Function: pade4all(order, coeff_mat, s)

Computes the "order" Padè approximant of the coefficients at the approximation point s

## Function: sigma_function(coeff_matU, coeff_matX, order, V_slack)

:param coeff_matU: array with voltage coefficients

## Function: conv1_old(A, B, c, indices)

Performs the convolution of A* and B

## Function: conv1(A, B, c)

Performs the convolution of A* and B

## Function: conv2(A, B, c, indices)

Performs the convolution of A and B

## Function: conv3(A, B, c, indices)

Performs the convolution of A and B*

## Function: helm_coefficients_josep(Ybus, Yseries, V0, S0, Ysh0, pq, pv, sl, no_slack, tolerance, max_coeff, verbose, stop_if_too_bad, logger)

Holomorphic Embedding LoadFlow Method as formulated by Josep Fanals Batllori in 2020

## Class: HelmPreparation

- Bases: none
- Summary: HelmPreparation

### Methods

- No methods detected.

## Function: helm_preparation_dY(Yseries, V0, S0, Ysh0, pq, pv, sl, pqpv, verbose, logger)

This function returns the constant objects to run many HELM simulations

## Function: helm_coefficients_dY(dY, sys_mat_factorization, Uini, Xini, Yslack, Ysh, Ybus, vec_P, vec_Q, S0, vec_W, V0, Vslack, pq, pv, pqpv, npqpv, nbus, sl, pqpv_original, pq_original, tolerance, max_coeff)

Holomorphic Embedding LoadFlow Method as formulated by Josep Fanals Batllori in 2020

## Function: helm_josep(nc, Ybus, Yf, Yt, Yshunt_bus, Yseries, V0, S0, Ysh0, pq, pv, vd, no_slack, tolerance, max_coefficients, use_pade, verbose, logger)

Holomorphic Embedding LoadFlow Method as formulated by Josep Fanals Batllori in 2020
