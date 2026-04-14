# VeraGridEngine Module: src/VeraGridEngine/Simulations/OPF/NumericalMethods/ac_opf_derivatives.py

- Original source path: `src/VeraGridEngine/Simulations/OPF/NumericalMethods/ac_opf_derivatives.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 8
- Representative imports: timeit, typing, numpy, scipy, scipy.sparse, scipy.sparse, VeraGridEngine.Utils.Sparse.csc, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Function: x2var(x, nVa, nVm, nPg, nQg, npq, M, ntapm, ntapt, ndc, nslcap, acopf_mode)

Convert the x solution vector to its composing variables

## Function: var2x(Va, Vm, Pg, Qg, sl_sf, sl_st, sl_vmax, sl_vmin, slcap, tapm, tapt, Pfdc)

Compose the x vector from its components

## Function: compute_branch_power_derivatives(all_tap_m, all_tap_tau, V, k_m, k_tau, Cf, Ct, F, T, R, X)

:param all_tap_m: Vector with all the tap module, including the non-controlled ones

## Function: compute_branch_power_second_derivatives(all_tap_m, all_tap_tau, vm, va, k_m, k_tau, mon_idx, R, X, F, T, lam, mu, Sf, St)

:param all_tap_m: Vector with all the tap module, including the non-controlled ones

## Function: eval_f(x, Cg, k_m, k_tau, nll, c0, c1, c2, c_s, nslcap, nodal_capacity_sign, c_v, ig, npq, ndc, Sbase, acopf_mode)

Calculates the value of the objective function at the current state (given by x)

## Function: eval_g(x, Ybus, Yf, Cg, Sd, ig, nig, nll, nslcap, nodal_capacity_sign, capacity_nodes_idx, npq, pv, f_nd_dc, t_nd_dc, fdc, tdc, Pf_nondisp, k_m, k_tau, Vm_max, Sg_undis, slack, acopf_mode)

Calculates the equality constraints at the current state (given by x)

## Function: eval_h(x, Yf, Yt, from_idx, to_idx, nslcap, pq, k_m, k_tau, Cg, Inom, Vm_max, Vm_min, Pg_max, Pg_min, Qg_max, Qg_min, tapm_max, tapm_min, tapt_max, tapt_min, Pdcmax, rates, il, ig, ctQ, acopf_mode)

Calculates the inequality constraints at the current state (given by x)

## Function: jacobians_and_hessians(x, c1, c2, c_s, c_v, Cg, Cf, Ct, Inom, Yf, Yt, Ybus, Sbase, mon_br_idx, ig, slack, nslcap, nodal_capacity_sign, capacity_nodes_idx, pq, pv, alltapm, alltapt, F_hvdc, T_hvdc, nsh, k_m, k_tau, mu, lmbda, R, X, F, T, ctQ, acopf_mode, compute_jac, compute_hess)

Calculates the jacobians and hessians of the objective function and the equality and inequality constraints
