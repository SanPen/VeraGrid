# VeraGridEngine Module: src/VeraGridEngine/Simulations/PowerFlow/NumericalMethods/common_functions.py

- Original source path: `src/VeraGridEngine/Simulations/PowerFlow/NumericalMethods/common_functions.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 19
- Representative imports: numba, numpy, scipy.sparse, VeraGridEngine.basic_structures, typing

## Function: polar_to_rect(Vm, Va)

Convert polar to rectangular coordinates

## Function: expand(n, arr, idx, default)

Expand array

## Function: compute_zip_power(S0, I0, Y0, Vm)

Compute the equivalent power injection

## Function: compute_zip_current(S0, I0, Y0, Vm)

Compute the equivalent current injection

## Function: compute_power(Ybus, V)

Compute the power from the admittance matrix and the voltage

## Function: compute_current(Ybus, V)

Compute the current from the admittance matrix and the voltage

## Function: fortescue_012_to_abc(z0, z1, z2)

Convert 012 to abc

## Function: compute_fx(Scalc, Sbus, idx_dP, idx_dQ)

Compute the NR-like error function

## Function: compute_fx_error(fx)

Compute the infinite norm of fx

## Function: get_Sf(k, Vm, V, yff, yft, F, T)

:param k:

## Function: get_St(k, Vm, V, ytf, ytt, F, T)

:param k:

## Function: get_If(k, V, yff, yft, F, T)

:param k:

## Function: get_It(k, V, ytf, ytt, F, T)

:param k:

## Function: expand_magnitudes(magnitude, lookup)

:param magnitude:

## Function: floating_star_currents(Va, Vb, Vc, Istar_a, Istar_b, Istar_c, Vn0)

Given the phase voltages and currents of a floating star connected current load,

## Function: floating_star_powers(Ua, Ub, Uc, Sa, Sb, Sc)

Given the phase voltages and complex powers of a floating star connected power load,

## Function: power_flow_post_process_nonlinear_3ph(Sbus, V, Vn_floating, F, T, pv, vd, Ybus, Yf, Yt, Yshunt_bus, branch_rates, Sbase, bus_lookup, branch_lookup)

:param Sbus:

## Function: power_flow_post_process_nonlinear(Sbus, V, F, T, pv, vd, Ybus, Yf, Yt, Yshunt_bus, branch_rates, Sbase)

:param Sbus:

## Function: power_flow_post_process_linear(Sbus, V, active, X, tap_module, tap_angle, F, T, branch_rates, Sbase)

:param Sbus:
