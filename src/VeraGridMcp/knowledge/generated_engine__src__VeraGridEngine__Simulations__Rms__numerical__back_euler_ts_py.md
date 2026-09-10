# VeraGridEngine Module: src/VeraGridEngine/Simulations/Rms/numerical/back_euler_ts.py

- Original source path: `src/VeraGridEngine/Simulations/Rms/numerical/back_euler_ts.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: numpy, scipy.sparse, time, scipy.sparse, scipy.sparse, VeraGridEngine.Simulations.Rms.problems.rms_problem_dae, VeraGridEngine.Utils.Sparse.csc, VeraGridEngine.basic_structures, VeraGridEngine.Simulations.Rms.problems.rms_problem_template

## Class: BackEulerImplicitTensygrid

- Bases: none
- Summary: No docstring provided.

### Methods

- `_rhs_implicit(self, x, dx, xn, h)`
  Summary: Return 𝑑x/dt given the current *state* vector.
- `_jacobian_implicit(self, x, dx, h)`
  Summary: :param x: vector or variables' values
- `simulate(self)`
  Summary: :return:
