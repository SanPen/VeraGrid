# VeraGridEngine Module: src/VeraGridEngine/Utils/NumericalMethods/MVRSM_mo_scaled.py

- Original source path: `src/VeraGridEngine/Utils/NumericalMethods/MVRSM_mo_scaled.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 13
- Representative imports: math, random, numpy, typing, scipy.linalg.blas, scipy.optimize, VeraGridEngine.basic_structures

## Function: relu(x)

The Rectified Linear Unit (ReLU) function.

## Function: relu_deriv(x)

The derivative of the rectified linear unit function,

## Class: SurrogateModel

- Bases: none
- Summary: SurrogateModel

### Methods

- `init(cls, d, lb, ub, num_int)`
  Summary: Initializes a surrogate model.
- `phi(self, x, out)`
  Summary: Evaluates the basis functions at `x`.
- `phi_deriv(self, x, out)`
  Summary: Evaluates the derivatives of the basis functions with respect to `x`.
- `update(self, x, y)`
  Summary: Updates the model upon the observation of a new data point `(x, y)`.
- `g(self, x)`
  Summary: Evaluates the surrogate model at `x`.
- `g_jac(self, x)`
  Summary: Evaluates the Jacobian of the model at `x`.
- `minimum(self, x0)`
  Summary: Find a minimum of the surrogate model approximately.

## Function: scale(y, y0, scale_threshold)

Scale the objective with respect to the initial objective value,

## Function: normalize_md(y_no_normalized, norm_factors)

Computes the normalization of y_no_normalized --> y_normalized=(y_no_normalized-y_min)/(y_max-y_min).

## Function: inv_normalize_md(y_normalized, norm_factors)

Computes the inverse of normalize_md(y_no_normalized, norm_factors).

## Function: get_norm_factors(scaling_values)

Computes the factors used to normalize objective function criteria..

## Function: inv_scale(y_scaled, y0, scale_threshold)

Computes the inverse function of `scale(y, y0)`.

## Function: dominates(sol_a, sol_b)

Check if a solution dominates another in the Pareto sense

## Function: get_non_dominated_fronts(population)

2D non dominated sorting

## Function: crowding_distance(front, population)

:param front: list of integers representing the positions in the population matrix

## Function: sort_by_crowding(fronts, population)

:param fronts: Fronts ordered by position (front 1, front 2, Front 3, ...)

## Function: non_dominated_sorting(y_values, x_values)

Use non dominated sorting and crowded sorting to sort the multidimensional objectives

## Function: MVRSM_mo_scaled(obj_func, x0, lb, ub, num_int, max_evals, rand_evals, args, stop_crit, n_objectives)

MVRSM algorithm adapted to minimize multi-dimensional functions. After the random evaluations, the normalization
