# VeraGridEngine Module: src/VeraGridEngine/Utils/NumericalMethods/sparse_solve.py

- Original source path: `src/VeraGridEngine/Utils/NumericalMethods/sparse_solve.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 6
- Representative imports: numpy, enum, typing, collections.abc, scipy.sparse, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Function: get_sparse_type(solver_type)

GEt sparse matrix type matching the selected sparse linear systems solver

## Function: super_lu_linsolver(A, b)

SuperLU wrapper function for linear system solve A x = b

## Function: ilu_linsolver(A, b)

ILU wrapper function for linear system solve A x = b

## Function: klu_linsolve(A, b)

KLU wrapper function for linear system solve A x = b

## Function: gmres_linsolve(A, b)

:param A:

## Function: get_linear_solver(solver_type)

Privide the chosen linear solver_type function pointer to
