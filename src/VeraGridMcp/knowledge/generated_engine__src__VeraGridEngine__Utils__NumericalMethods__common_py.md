# VeraGridEngine Module: src/VeraGridEngine/Utils/NumericalMethods/common.py

- Original source path: `src/VeraGridEngine/Utils/NumericalMethods/common.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 7
- Representative imports: dataclasses, typing, numpy, numba, matplotlib, VeraGridEngine.basic_structures

## Function: check_function_and_args(func, args, n_used_for_solver)

Checks if the number of supplied arguments matches the function signature

## Function: max_abs(x)

Compute max abs efficiently

## Function: norm(x)

Compute max abs efficiently

## Function: compute_L(h, f, J)

1/2 · ||f + J @ h||

## Class: ConvexFunctionResult

- Bases: none
- Summary: Result of the convex function evaluated iterativelly for a given method

### Methods

- `compute_f_error(self)`
  Summary: Compute the error of the increments g

## Class: ConvexMethodResult

- Bases: none
- Summary: Iterative convex method result

### Methods

- `plot_error(self)`
  Summary: Plot the IPS error
- `print_info(self)`
  Summary: Print information about the ConvexMethodResult

## Function: find_closest_number(arr, target)

Find the closest number that exists in array

## Function: make_lookup(size, indices)

Create a lookup array

## Function: make_complex(r, i)

Fastest way to create complex arrays
