# VeraGridEngine Module: src/VeraGridEngine/Simulations/OPF/NumericalMethods/newton_raphson_ips_fx.py

- Original source path: `src/VeraGridEngine/Simulations/OPF/NumericalMethods/newton_raphson_ips_fx.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 9
- Representative imports: typing, dataclasses, numba, numpy, pandas, scipy.sparse, scipy, timeit, matplotlib, VeraGridEngine.basic_structures, VeraGridEngine.Utils.Sparse.csc, VeraGridEngine.Utils.NumericalMethods.sparse_solve, VeraGridEngine.enumerations

## Function: step_calculation(v, dv, tau)

This function calculates for each Lambda multiplier or its associated Slack variable

## Function: split(sol, n)

Split the solution vector in two

## Function: calc_error(dx, dz, dmu, dlmbda)

Calculate the error of the process

## Function: max_abs(x)

Compute max abs efficiently

## Function: calc_feas_cond(g, h, x, z)

Calculate the feasible conditions

## Function: calc_grad_cond(lx, lam, mu)

calculate the gradient conditions

## Function: calc_c_cond(mu, z, x)

:param mu: Vector of mu multipliers

## Function: calc_o_cond(f, f_prev)

:param f: Value of objective function

## Class: IpsFunctionReturn

- Bases: none
- Summary: Represents the returning value of the interior point evaluation

### Methods

- `get_data(self)`
  Summary: Returns the structures in a list
- `get_headers()`
  Summary: Returns the structures' names
- `compare(self, other, h)`
  Summary: Returns the comparison between this structure and another structure of this type

## Class: IpsSolution

- Bases: none
- Summary: Represents the returning value of the interior point solution

### Methods

- `plot_error(self)`
  Summary: Plot the IPS error

## Function: interior_point_solver(problem, max_iter, tol, pf_init, trust, verbose, step_control)

Solve a non-linear problem of the form:
