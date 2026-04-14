# VeraGridEngine Module: src/VeraGridEngine/Topology/admittance_matrices.py

- Original source path: `src/VeraGridEngine/Topology/admittance_matrices.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 5
- Top-level function count: 11
- Representative imports: numpy, numba, scipy.sparse, typing, VeraGridEngine.enumerations, VeraGridEngine.basic_structures

## Function: csc_equal(A, B, tol)

Return True iff two CSC matrices are equal

## Function: _prepare_branch_maps(nbus, nbranch, F, T, Yf_indices, Yf_indptr, Ybus_indices, Ybus_indptr)

Build a map to the matrices to update (Ybus, Yf, Yt)

## Function: update_branch_admittances(idx, new_yff, new_yft, new_ytf, new_ytt, Yf_data, Yt_data, Ybus_data, pos_yff, pos_yft, pos_ytf, pos_ytt, pos_b_ii, pos_b_ij, pos_b_ji, pos_b_jj)

Update Yf, Yt, Ybus *in place*.  All arrays are pre-allocated.

## Class: AdmittanceMatrices

- Bases: none
- Summary: Class to store admittance matrices

### Methods

- `modify_taps_all(self, m, m2, tau, tau2)`
  Summary: Compute the new admittance matrix given the tap variation
- `modify_taps(self, m_prev, m_new, tau_prev, tau_new, idx)`
  Summary: Compute the new admittance matrix given the tap variation
- `copy(self)`
  Summary: Get a deep copy

## Function: compute_admittances(R, X, G, B, tap_module, vtap_f, vtap_t, tap_angle, Cf, Ct, Yshunt_bus, conn, seq, add_windings_phase)

Compute the complete admittance matrices for the general power flow methods (Newton-Raphson based)

## Function: _sum_in_place(arr)

exclusive prefix-sum in-place

## Function: _build_Yf_Yt(nbus, nbr, F, T, yff, yft, ytf, ytt)

branch matrices (identical pattern ⇒ share indices/indptr)

## Function: _build_Ybus(nbus, nbr, F, T, yff, yft, ytf, ytt, Ysh)

Build Ybus

## Class: AdmittanceMatricesFast

- Bases: none
- Summary: Class to store admittance matrices

### Methods

- `initialize_update(self)`
  Summary: Build the indices to later update the matrix easily
- `modify_taps_fast(self, idx, tap_module, tap_angle)`
  Summary: Modify in-place Ybus, Yf and Yt
- `copy(self)`
  Summary: Get a deep copy

## Function: compute_admittances_fast(nbus, R, X, G, B, tap_module, vtap_f, vtap_t, tap_angle, Yshunt_bus, F, T)

Hardcore build of admittance matrices

## Class: SeriesAdmittanceMatrices

- Bases: none
- Summary: Admittance matrices for HELM and the AC linear methods

### Methods

- No methods detected.

## Function: compute_split_admittances(R, X, G, B, active, tap_module, vtap_f, vtap_t, tap_angle, Cf, Ct, Yshunt_bus)

Compute the complete admittance matrices for the helm method and others that may require them

## Class: FastDecoupledAdmittanceMatrices

- Bases: none
- Summary: Admittance matrices for Fast decoupled method

### Methods

- No methods detected.

## Function: compute_fast_decoupled_admittances(X, B, tap_module, active, vtap_f, vtap_t, Cf, Ct)

Compute the admittance matrices for the fast decoupled method

## Class: LinearAdmittanceMatrices

- Bases: none
- Summary: Admittance matrices for linear methods (DC power flow, PTDF, ...)

### Methods

- `get_Bred(self, pqpv)`
  Summary: Get Bred or Bpqpv for the PTDF and DC power flow
- `get_Bslack(self, pqpv, vd)`
  Summary: Get Bslack for the PTDF and DC power flow

## Function: compute_linear_admittances(nbr, X, R, m, active, Cf, Ct, ac, dc)

Compute the linear admittances for methods such as the "DC power flow" of the PTDF
