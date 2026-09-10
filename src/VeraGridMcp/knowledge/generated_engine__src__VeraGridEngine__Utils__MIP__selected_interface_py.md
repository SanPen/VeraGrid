# VeraGridEngine Module: src/VeraGridEngine/Utils/MIP/selected_interface.py

- Original source path: `src/VeraGridEngine/Utils/MIP/selected_interface.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

Uncomment the appropriate interface imports to use: Pulp or OrTools

## Module Surface

- Class count: 0
- Top-level function count: 6
- Representative imports: typing, numpy, scipy.sparse, VeraGridEngine.basic_structures, VeraGridEngine.enumerations, VeraGridEngine.Utils.MIP.pulp_interface

## Function: get_available_mip_frameworks()

Get list of available frameworks

## Function: get_model_instance(tpe, solver_type)

Get an instance of the solver framework and the selected solver

## Function: get_available_mip_solvers(tpe)

Get the solvers available in the selected interface

## Function: join(init, vals, sep)

Generate naming string

## Function: lpDot(mat, arr)

CSC matrix-vector or CSC matrix-matrix dot product (A x b)

## Function: lpDot1D_changes(mat, arr)

CSC matrix-vector or CSC matrix-matrix dot product (A x b)
