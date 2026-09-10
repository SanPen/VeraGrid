# VeraGridEngine Module: src/VeraGridEngine/Simulations/PowerFlow/Formulations/pf_generalized_formulation.py

- Original source path: `src/VeraGridEngine/Simulations/PowerFlow/Formulations/pf_generalized_formulation.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 6
- Representative imports: time, typing, numpy, numba, scipy.sparse, VeraGridEngine.Topology.admittance_matrices, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.Simulations.PowerFlow.power_flow_options, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.Simulations.Derivatives.csc_derivatives, VeraGridEngine.Utils.NumericalMethods.common, VeraGridEngine.Utils.Sparse.csc2, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.discrete_controls, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.Simulations.PowerFlow.Formulations.pf_formulation_template

## Function: adv_jacobian(nbus, nbr, nvsc, nhvdc, F, T, F_vsc, T_vsc, F_hvdc, T_hvdc, tap_angles, tap_modules, V, Vm, Va, u_cbr_m, u_cbr_tau, k_cbr_pf, k_cbr_pt, k_cbr_qf, k_cbr_qt, u_vsc_pf, u_vsc_pt, u_vsc_qt, alpha1, alpha2, alpha3, hvdc_r, hvdc_droop, i_u_vm, i_u_va, i_k_p, i_k_q, Pfp_vsc, Pt_vsc, Qt_vsc, Pf_hvdc, Ys, Bc, yff_cbr, yft_cbr, ytf_cbr, ytt_cbr, Yi, Yp, Yx)

:param nbus:

## Function: calcSf(k, V, F, T, R, X, G, B, m, tau, vtap_f, vtap_t)

Compute Sf for pi branches

## Function: calcSt(k, V, F, T, R, X, G, B, m, tau, vtap_f, vtap_t)

Compute St for pi branches

## Function: calc_flows_summation_per_bus(nbus, F_br, T_br, Sf_br, St_br, F_hvdc, T_hvdc, Sf_hvdc, St_hvdc, F_vsc, T_vsc, Pfp_vsc, St_vsc)

Summation of magnitudes per bus (complex)

## Function: calc_flows_active_branch_per_bus(nbus, F_hvdc, T_hvdc, Sf_hvdc, St_hvdc, F_vsc, T_vsc, Pfp_vsc, St_vsc)

Summation of magnitudes per bus (complex)

## Function: calc_autodiff_jacobian(func, x, h)

Compute the Jacobian matrix of `func` at `x` using finite differences.

## Class: PfGeneralizedFormulation

- Bases: PfFormulationTemplate
- Summary: No docstring provided.

### Methods

- `_update_Qlim_indices(self, i_u_vm, i_k_q)`
  Summary: Update the indices due to applying Q limits
- `_set_bus_control_indices(self)`
  Summary: Analyze the bus indices from the boolean marked arrays
- `_set_branch_control_indices(self)`
  Summary: Analyze the control branches and compute the indices
- `_set_vsc_control_indices(self)`
  Summary: Analyze the control branches and compute the indices
- `_set_hvdc_control_indices(self)`
  Summary: Analyze the control hvdc and compute the indices
- `x2var(self, x)`
  Summary: Convert X to decision variables
- `var2x(self)`
  Summary: Convert the internal decision variables into the vector
- `size(self)`
  Summary: Size of the jacobian matrix
- `compute_f(self, x, update_class_vars)`
  Summary: Compute the residual vector
- `check_error(self, x)`
  Summary: Check error of the solution without affecting the problem
- `update(self, x, update_controls)`
  Summary: Update step
- `fx(self)`
  Summary: Used when updating the controls
- `Jacobian(self, autodiff)`
  Summary: Get the Jacobian
- `get_x_names(self)`
  Summary: Names matching x
- `get_fx_names(self)`
  Summary: Names matching fx
- `get_solution(self, elapsed, iterations)`
  Summary: Get the problem solution
