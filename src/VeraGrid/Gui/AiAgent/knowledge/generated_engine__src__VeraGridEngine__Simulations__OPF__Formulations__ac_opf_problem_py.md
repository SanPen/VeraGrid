# VeraGridEngine Module: src/VeraGridEngine/Simulations/OPF/Formulations/ac_opf_problem.py

- Original source path: `src/VeraGridEngine/Simulations/OPF/Formulations/ac_opf_problem.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 0
- Representative imports: numpy, pandas, timeit, dataclasses, typing, scipy, scipy.sparse, scipy.sparse, VeraGridEngine.Utils.Sparse.csc, VeraGridEngine.Compilers.circuit_to_data, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.Simulations.OPF.opf_options, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.Simulations.OPF.NumericalMethods.newton_raphson_ips_fx

## Class: NonlinearOPFResults

- Bases: none
- Summary: Numerical non linear OPF results

### Methods

- `initialize(self, nbus, nbr, nil, nsh, ng, nhvdc, ncap)`
  Summary: Initialize the arrays
- `merge(self, other, bus_idx, br_idx, il_idx, gen_idx, hvdc_idx, ncap_idx, contshunt_idx, acopf_mode)`
  Summary: :param other:
- `V(self)`
  Summary: Complex voltage

## Class: NonLinearOptimalPfProblem

- Bases: none
- Summary: No docstring provided.

### Methods

- `analyze_branch_controls(self)`
  Summary: Analyze the control branches and compute the indices
- `var2x(self)`
  Summary: No docstring provided.
- `x2var(self, x)`
  Summary: No docstring provided.
- `update(self, x)`
  Summary: No docstring provided.
- `get_jacobians_and_hessians(self, mu, lam, compute_hessians)`
  Summary: TODO: we should split this function into functions outside the class, that should make it more manageable
- `compute_branch_power_derivatives(self)`
  Summary: TODO: Move outside of the class
- `compute_branch_power_second_derivatives(self, lam, mu)`
  Summary: TODO: Move outside of the class
- `get_solution(self, ips_results, verbose, plot_error)`
  Summary: :param ips_results:
