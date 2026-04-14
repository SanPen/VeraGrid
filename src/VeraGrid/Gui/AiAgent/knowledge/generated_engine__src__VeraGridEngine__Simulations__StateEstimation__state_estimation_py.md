# VeraGridEngine Module: src/VeraGridEngine/Simulations/StateEstimation/state_estimation.py

- Original source path: `src/VeraGridEngine/Simulations/StateEstimation/state_estimation.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 7
- Representative imports: time, typing, pandas, scipy, scipy.sparse, scipy.sparse.linalg, numpy, VeraGridEngine.Simulations.StateEstimation.state_estimation_inputs, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.Simulations.Derivatives.matpower_derivatives, VeraGridEngine.Simulations.StateEstimation.state_estimation_results, VeraGridEngine.basic_structures

## Function: Jacobian_SE(Ybus, Yf, Yt, V, f, t, Cf, Ct, inputs, pvpq, load_per_bus, fixed_slack)

Get the arrays for calculation

## Function: get_measurements_and_deviations(t, se_input, Sbase, use_current_squared_meas)

get_measurements_and_deviations the measurements into "measurements" and "sigma"

## Function: b_test(sigma2, H, dz, HtWH, c_threshold, logger)

From RELIABLE BAD DATA PROCESSING FOR REAL-TIME STATE ESTIMATION, 1983

## Function: solve_se_lm(nc, Ybus, Yf, Yt, Yshunt_bus, F, T, Cf, Ct, se_input, vd, pv, no_slack, tol, max_iter, verbose, c_threshold, prefer_correct, fixed_slack, logger)

Solve the state estimation problem using the Levenberg-Marquadt method

## Function: solve_se_nr(nc, Ybus, Yf, Yt, Yshunt_bus, F, T, Cf, Ct, se_input, vd, pv, no_slack, tol, max_iter, verbose, c_threshold, prefer_correct, fixed_slack, logger)

Solve the state estimation problem using the Levenberg-Marquadt method

## Function: solve_se_gauss_newton(nc, Ybus, Yf, Yt, Yshunt_bus, F, T, Cf, Ct, se_input, vd, pv, no_slack, tol, max_iter, verbose, c_threshold, prefer_correct, fixed_slack, logger)

Linearize the non-linear measurement model around the current state estimate (Jacobian H)

## Function: decoupled_state_estimation(nc, Ybus, Yf, Yt, Yshunt_bus, F, T, Cf, Ct, se_input, vd, pv, no_slack, tol, max_iter, verbose, c_threshold, prefer_correct, fixed_slack, logger)

Fast decoupled WLS state estimator using LU decomposition.
