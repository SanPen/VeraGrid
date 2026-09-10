# VeraGridEngine Module: src/VeraGridEngine/Simulations/Rms/numerical/pseudo_transient.py

- Original source path: `src/VeraGridEngine/Simulations/Rms/numerical/pseudo_transient.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: numpy, scipy.sparse, time, scipy.sparse, scipy.sparse, matplotlib.pyplot, VeraGridEngine.Simulations.Rms.problems.rms_problem_dae, VeraGridEngine.Utils.Sparse.csc, VeraGridEngine.basic_structures, VeraGridEngine.Simulations.Rms.problems.rms_problem_template

## Class: PseudoTransient

- Bases: none
- Summary: No docstring provided.

### Methods

- `_rhs_implicit(self, x, dx, xn, h)`
  Summary: Return 𝑑x/dt given the current *state* vector.
- `_jacobian_implicit(self, x, dx, h)`
  Summary: :param x: vector or variables' values
- `_jacobian_pseudo_transient(self, x, dx, h)`
  Summary: #We want to build an equivalent of the following Jacobian:
- `_rhs_pseudo_transient(self, x, xn, dx, h)`
  Summary: Return 𝑑x/dt given the current *state* vector.
- `simulate(self, plot)`
  Summary: No docstring provided.
