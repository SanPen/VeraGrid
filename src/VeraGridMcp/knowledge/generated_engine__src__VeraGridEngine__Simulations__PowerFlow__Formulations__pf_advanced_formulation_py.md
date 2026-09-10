# VeraGridEngine Module: src/VeraGridEngine/Simulations/PowerFlow/Formulations/pf_advanced_formulation.py

- Original source path: `src/VeraGridEngine/Simulations/PowerFlow/Formulations/pf_advanced_formulation.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 2
- Representative imports: typing, numpy, numba, scipy.sparse, VeraGridEngine.Topology.admittance_matrices, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.Simulations.PowerFlow.power_flow_options, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.Simulations.Derivatives.csc_derivatives, VeraGridEngine.Topology.simulation_indices, VeraGridEngine.Utils.Sparse.csc2, VeraGridEngine.Utils.NumericalMethods.common, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.discrete_controls, VeraGridEngine.Simulations.PowerFlow.Formulations.pf_formulation_template, VeraGridEngine.enumerations

## Function: adv_jacobian(nbus, nbr, idx_dva, idx_dvm, idx_dm, idx_dtau, idx_dP, idx_dQ, idx_dPf, idx_dQf, idx_dPt, idx_dQt, F, T, Ys, complex_tap, tap_modules, Bc, V, Vm, Va, Ybus_x, Ybus_p, Ybus_i, yff, yft, ytf, ytt)

Compute the advanced jacobian

## Function: calc_autodiff_jacobian(func, x, h)

Compute the Jacobian matrix of `func` at `x` using finite differences.

## Class: PfAdvancedFormulation

- Bases: PfFormulationTemplate
- Summary: No docstring provided.

### Methods

- `update_bus_types(self, pq, pv, pqv, p)`
  Summary: Update the bus types
- `analyze_branch_controls(self)`
  Summary: Analyze the control branches and compute the indices
- `x2var(self, x)`
  Summary: Convert X to decision variables
- `var2x(self)`
  Summary: Convert the internal decision variables into the vector
- `size(self)`
  Summary: Size of the jacobian matrix
- `check_error(self, x)`
  Summary: Check error of the solution without affecting the problem
- `update(self, x, update_controls)`
  Summary: Update step
- `fx(self)`
  Summary: :return:
- `fx_diff(self, x)`
  Summary: Fx for autodiff
- `Jacobian(self, autodiff)`
  Summary: Get the Jacobian
- `get_x_names(self)`
  Summary: Names matching x
- `get_fx_names(self)`
  Summary: Names matching fx
- `get_solution(self, elapsed, iterations)`
  Summary: Get the problem solution
