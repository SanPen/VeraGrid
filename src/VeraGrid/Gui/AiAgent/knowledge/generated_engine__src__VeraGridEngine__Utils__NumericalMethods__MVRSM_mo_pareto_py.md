# VeraGridEngine Module: src/VeraGridEngine/Utils/NumericalMethods/MVRSM_mo_pareto.py

- Original source path: `src/VeraGridEngine/Utils/NumericalMethods/MVRSM_mo_pareto.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 8
- Representative imports: math, random, numpy, typing, scipy.linalg.blas, scipy.optimize, VeraGridEngine.Utils.NumericalMethods.non_dominated_sorting, VeraGridEngine.basic_structures

## Function: relu(x)

The Rectified Linear Unit (ReLU) function.

## Function: relu_deriv(x)

The derivative of the rectified linear unit function,

## Class: SurrogateModel

- Bases: none
- Summary: SurrogateModel

### Methods

- `init(cls, n_obj, d, lb, ub, num_int)`
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
- `g_scalarize(self, x, scalarization_weights)`
  Summary: Evaluates the linear scalarization of multiple objectives.
- `g_scalarize_max(self, x, scalarization_weights)`
  Summary: Evaluates the maximum or Tchebycheff scalarization of multiple objectives.
- `g_scalarize_jac(self, x, scalarization_weights)`
  Summary: Evaluates the Jacobian of the linear scalarization of multiple objectives.
- `g_scalarize_max_jac(self, x, scalarization_weights)`
  Summary: Evaluates the Jacobian of the maximum or Tchebycheff scalarization of multiple objectives.
- `augmented_Tchebycheff(self, x, scalarization_weights)`
  Summary: Evaluates the augmented Tchebycheff scalarization of multiple objectives.
- `augmented_Tchebycheff_jac(self, x, scalarization_weights)`
  Summary: Evaluates the Jacobian of the augmented Tchebycheff scalarization of multiple objectives.
- `minimum(self, x0, scalarization_weights)`
  Summary: Find a minimum of the surrogate model approximately.

## Function: scale(y, y0, scale_threshold)

# normalize: do this for every objective so that all objectives are more or less in the same range

## Function: inv_scale(y_scaled, y0, scale_threshold)

Computes the inverse function of `scale(y, y0)`.

## Function: get_norm_factors(scaling_values)

Computes the factors used to normalize objective function criteria..

## Function: normalize_md(y_no_normalized, norm_factors)

Computes the normalization of y_no_normalized --> y_normalized=(y_no_normalized-y_min)/(y_max-y_min).

## Function: inv_normalize_md(y_normalized, norm_factors)

Computes the inverse of normalize_md(y_no_normalized, norm_factors).

## Function: MVRSM_mo_pareto(obj_func, x0, lb, ub, num_int, max_evals, n_objectives, rand_evals, args)

MVRSM algorithm for multiple objectives
