# VeraGridEngine Module: src/VeraGridEngine/Simulations/ContinuationPowerFlow/continuation_power_flow.py

- Original source path: `src/VeraGridEngine/Simulations/ContinuationPowerFlow/continuation_power_flow.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 5
- Representative imports: numpy, VeraGridEngine.enumerations, VeraGridEngine.Simulations.Derivatives.ac_jacobian, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.discrete_controls, VeraGridEngine.Topology.simulation_indices, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.basic_structures, VeraGridEngine.Utils.Sparse.csc2

## Class: CpfNumericResults

- Bases: none
- Summary: CpfNumericResults

### Methods

- `add(self, v, sbus, Sf, St, lam, losses, loading, normf, converged)`
  Summary: :param v:

## Function: cpf_p(parametrization, step, z, V, lam, V_prev, lamprv, idx_dtheta, idx_dVm)

Computes the value of the Current Parametrization Function

## Function: cpf_p_jac(parametrization, z, V, lam, Vprv, lamprv, idx_dtheta, idx_dVm)

Computes partial derivatives of Current Parametrization Function (CPF).

## Function: predictor(V, lam, Ybus, Sxfr, idx_dtheta, idx_dVm, idx_dP, idx_dQ, step, z, Vprv, lamprv, parametrization)

Computes a prediction (approximation) to the next solution of the

## Function: corrector(Ybus, S0, I0, Y0, V0, idx_dtheta, idx_dVm, idx_dP, idx_dQ, lam0, Sxfr, Vprv, lamprv, z, step, parametrization, tol, max_it, verbose, mu_0, acceleration_parameter)

Solves the corrector step of a continuation power flow using a full Newton method

## Function: continuation_nr(Ybus, Cf, Ct, Yf, Yt, branch_rates, Sbase, Sbus_base, I0, Y0, Sbus_target, V, distributed_slack, bus_installed_power, vd, pv, pq, pqv, p, step, approximation_order, adapt_step, step_min, step_max, error_tol, tol, max_it, stop_at, control_q, qmax_bus, qmin_bus, original_bus_types, base_overload_number, verbose, call_back_fx)

Runs a full AC continuation power flow using a normalized tangent
