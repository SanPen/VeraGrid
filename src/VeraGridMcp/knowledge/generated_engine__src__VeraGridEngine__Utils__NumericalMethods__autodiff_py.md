# VeraGridEngine Module: src/VeraGridEngine/Utils/NumericalMethods/autodiff.py

- Original source path: `src/VeraGridEngine/Utils/NumericalMethods/autodiff.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 5
- Representative imports: typing, numpy, scipy.sparse, scipy.sparse, VeraGridEngine.basic_structures

## Function: unpack(ret)

Unpack the returning vector depending if ret is the vector or a tuple including the vector

## Function: calc_autodiff_jacobian_f_obj(func, x, arg, h)

Compute the Jacobian matrix of `func` at `x` using finite differences.

## Function: calc_autodiff_jacobian(func, x, arg, h)

Compute the Jacobian matrix of `func` at `x` using finite differences.

## Function: calc_autodiff_hessian_f_obj(func, x, arg, h)

Compute the Hessian matrix of `func` at `x` using finite differences.

## Function: calc_autodiff_hessian(func, x, mult, arg, h)

Compute the Hessian matrix of `func` at `x` using finite differences.
