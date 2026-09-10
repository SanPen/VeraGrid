# VeraGridEngine Module: src/VeraGridEngine/Simulations/Derivatives/csc_derivatives.py

- Original source path: `src/VeraGridEngine/Simulations/Derivatives/csc_derivatives.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 49
- Representative imports: numpy, numba, typing, scipy.sparse, VeraGridEngine.basic_structures, VeraGridEngine.Utils.NumericalMethods.common, VeraGridEngine.Utils.Sparse.csc2, VeraGridEngine.Utils.Sparse.csc_numba

## Function: dSbus_dV_numba_sparse_csc(Yx, Yp, Yi, V, Vm)

Compute the power injection derivatives w.r.t the voltage module and angle

## Function: dSbus_dV_with_I0_numba_sparse_csc(Yx, Yp, Yi, V, Vm, I0)

Compute the power injection derivatives w.r.t the voltage module and angle,

## Function: dSbus_dV_csc(Ybus, V, Vm)

Call the numba sparse constructor of the derivatives

## Function: map_coordinates_numba(nrows, ncols, indptr, indices, F, T)

:param nrows:

## Function: dSbr_dm_csc(nbus, u_cbr_m, F_cbr, T_cbr, yff_cbr, yft_cbr, ytf_cbr, ytt_cbr, V, tap, tap_modules)

Derivative of the controllable branch power flows (and hence bus balance) w.r.t. m

## Function: dSbr_dtau_csc(nbus, u_cbr_tau, F_cbr, T_cbr, yff_cbr, yft_cbr, ytf_cbr, ytt_cbr, V, tap, tap_modules)

Derivative of the controllable branch power flows (and hence bus balance) w.r.t. tau

## Function: csc_add_wrapper(A, B, alpha, beta)

Wrapper for csc_add_ff

## Function: csc_add_ff_comp(Am, An, Aindptr, Aindices, Adata, Bm, Bn, Bindptr, Bindices, Bdata, alpha, beta)

C = alpha*A + beta*B

## Function: csc_spalloc_f(m, n, nzmax)

Allocate a sparse matrix (triplet form or compressed-column form).

## Function: xalloc_comp(n)

No docstring provided.

## Function: csc_scatter_f_comp(Ap, Ai, Ax, j, beta, w, x, mark, Ci, nz)

Scatters and sums a sparse vector A(:,j) into a dense vector, x = x + beta * A(:,j)

## Function: dSf_dV_numba(Yf_nrows, Yf_ncols, Yf_indices, Yf_indptr, Yf_data, V, F, T)

:param Yf_nrows:

## Function: dSt_dV_numba(Yt_nrows, Yt_ncols, Yt_indices, Yt_indptr, Yt_data, V, F, T)

:param Yt_nrows:

## Function: dSf_dV_csc(Yf, V, F, T)

Flow "from" derivative w.r.t the voltage

## Function: dSt_dV_csc(Yt, V, F, T)

Flow "to" derivative w.r.t the voltage

## Function: dSf_dVm_csc(nbus, br_indices, bus_indices, yff, yft, Vm, Va, F, T)

dSf_dVm[br_indices, bus_indices]

## Function: dPfdp_dVm_csc(nbus, br_indices, bus_indices, yff, yft, kdp, V, F, T)

dSf_dVm[br_indices, bus_indices]

## Function: dSf_dVa_csc(nbus, br_indices, bus_indices, yft, V, F, T)

:param nbus: number of buses

## Function: dSt_dVm_csc(nbus, br_indices, bus_indices, ytt, ytf, Vm, Va, F, T)

:param nbus

## Function: dSt_dVa_csc(nbus, br_indices, bus_indices, ytf, V, F, T)

:param nbus

## Function: derivatives_tau_csc_numba(nbus, nbr, iPxsh, F, T, Ys, kconv, tap, V)

This function computes the derivatives of Sbus, Sf and St w.r.t. the tap angle (tau)

## Function: dSbus_dtau_csc(nbus, bus_indices, tau_indices, F, T, Ys, tap, V)

This function computes the derivatives of Sbus, Sf and St w.r.t. the tap angle (tau)

## Function: dSf_dtau_csc(nbr, sf_indices, tau_indices, F, T, Ys, tap, V)

This function computes the derivatives of Sbus, Sf and St w.r.t. the tap angle (tau)

## Function: dSt_dtau_csc(nbr, st_indices, tau_indices, F, T, Ys, tap, V)

This function computes the derivatives of Sbus, Sf and St w.r.t. the tap angle (tau)

## Function: derivatives_ma_csc_numba(nbus, nbr, iXxma, F, T, Ys, kconv, tap, tap_module, Bc, Beq, V)

Useful for the calculation of

## Function: dSbus_dm_csc(nbus, bus_indices, m_indices, F, T, Ys, Bc, tap, tap_module, V)

:param nbus:

## Function: dSf_dm_csc(nbr, sf_indices, m_indices, F, T, Ys, Bc, tap, tap_module, V)

This function computes the derivatives of Sbus, Sf and St w.r.t. the tap angle (tau)

## Function: dSt_dm_csc(nbr, st_indices, m_indices, F, T, Ys, tap, tap_module, V)

This function computes the derivatives of Sbus, Sf and St w.r.t. the tap angle (tau)

## Function: derivatives_Beq_csc_numba(nbus, nbr, iBeqx, F, V, tap_module, kconv)

Compute the derivatives of:

## Function: dSbus_dbeq_csc(nbus, bus_indices, beq_indices, F, kconv, tap_module, V)

:param nbus:

## Function: dSf_dbeq_csc(nbr, sf_indices, beq_indices, F, kconv, tap_module, V)

This function computes the derivatives of Sbus, Sf and St w.r.t. the tap angle (tau)

## Function: dSt_dbeq_csc(sf_indices, beq_indices)

This function computes the derivatives of Sbus, Sf and St w.r.t. the tap angle (tau)

## Function: dLossvsc_dVm_csc(nvsc, nbus, i_u_vm, alpha2, alpha3, Vm, Pt, Qt, T)

pq = Pt[ig_plossacdc] * Pt[ig_plossacdc] + Qt[ig_plossacdc] * Qt[ig_plossacdc]

## Function: dLosshvdc_dVm_csc(nhvdc, nbus, i_u_vm, Vm, Pf_hvdc, hvdc_r, F_hvdc)

dLosshvdc = rpu * Pf_hvdc / Vm[F_hvdc]**2 - Pf_hvdc - Pt_hvdc

## Function: dLosshvdc_dPfhvdc_csc(nhvdc, Vm, hvdc_r, F_hvdc)

dLosshvdc = rpu * Pf_hvdc / Vm[F_hvdc]**2 - Pf_hvdc - Pt_hvdc

## Function: dLosshvdc_dPthvdc_csc(nhvdc)

dLosshvdc = rpu * Pf_hvdc / Vm[F_hvdc]**2 - Pf_hvdc - Pt_hvdc

## Function: dInjhvdc_dPfhvdc_csc(nhvdc)

dInjhvdc = Pf_hvdc - Pset - droop(Va[f] - Va[t])

## Function: dLossvsc_dPfvsc_csc(nvsc, u_vsc_pf)

Compute dLossvsc_dPfvsc in CSC format with column indices aligned to u_vsc_pf.

## Function: dLossvsc_dPtvsc_csc(nvsc, u_vsc_pt, alpha2, alpha3, Vm, Pt, Qt, T_vsc)

Compute the sparse matrix for the derivative of loss with respect to Pt in CSC format.

## Function: dLossvsc_dQtvsc_csc(nvsc, u_vsc_qt, alpha2, alpha3, Vm, Pt, Qt, T_vsc)

Compute the sparse matrix for the derivative of loss with respect to Qt in CSC format.

## Function: dIvsc_dPfpvsc_csc(k_vsc_has_dc_n, u_vsc_pfp, Vm, Fdcn_vsc)

Compute dIvsc_dPfpvsc in CSC format.

## Function: dIvsc_dPfnvsc_csc(k_vsc_has_dc_n, u_vsc_pfn, Vm, Fdcp_vsc)

Compute dIvsc_dPfnvsc in CSC format.

## Function: dIvsc_dVm_csc(k_vsc_has_dc_n, nbus, i_u_vm, Pfp_vsc, Pfn_vsc, Fdcp_vsc, Fdcn_vsc)

Compute dIvsc_dVm in CSC format.

## Function: dImaxvsc_dVm_csc(nbus, k_vsc_imax, i_u_vm, Pt_vsc, Qt_vsc, Vm, T_vsc)

Compute dImaxvsc_dVm in CSC format.

## Function: dImaxvsc_dPQ_csc(nvsc, k_vsc_imax, u_vsc_pqt, PQt_vsc, Vm, T_vsc)

Compute dImaxvsc_dPQ in CSC format.

## Function: dP_dPfvsc_csc(i_k_p, u_vsc_pf, F_vsc)

Compute dP_dPfvsc in CSC format.

## Function: dPQ_dPQft_csc(nbus, nvsc, i_k_pq, u_dev_pq, FT_dev)

Calculate the derivatives of the power balance with respect to injections of branches

## Function: dInj_dVa_csc(nhvdc, i_u_va, hvdc_pset, hvdc_r, hvdc_droop, V, F_hvdc, T_hvdc)

Compute dInj_dVa in CSC format for HVDC systems.

## Function: dInjhvdc_dVa_csc(nhvdc, nbus, i_u_va, hvdc_droop, F_hvdc, T_hvdc)

Compute dInjhvdc_dVa in CSC format for HVDC systems.
