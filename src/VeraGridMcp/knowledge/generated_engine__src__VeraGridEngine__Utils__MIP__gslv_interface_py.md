# VeraGridEngine Module: src/VeraGridEngine/Utils/MIP/gslv_interface.py

- Original source path: `src/VeraGridEngine/Utils/MIP/gslv_interface.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

This module abstracts the synthax of PuLP out

## Module Surface

- Class count: 1
- Top-level function count: 1
- Representative imports: __future__, typing, pygslv, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, VeraGridEngine.Utils.MIP.mip_interface_template

## Function: get_available_mip_solvers()

Get a list of candidate solvers

## Class: LpModel

- Bases: AbstractLpModel
- Summary: LPModel implementation for PuLP

### Methods

- `save_model(self, file_name)`
  Summary: Save problem in LP format
- `add_int(self, lb, ub, name)`
  Summary: Make integer LP var
- `add_bin(self, name)`
  Summary: Make integer LP var
- `add_var(self, lb, ub, name)`
  Summary: Make floating point LP var
- `add_cst(self, cst, name)`
  Summary: Add constraint to the model
- `sum(cst)`
  Summary: Add sum of the constraints to the model
- `minimize(self, obj_function)`
  Summary: Set the objective function with minimization sense
- `solve(self, robust, show_logs, progress_text)`
  Summary: Solve the model
- `fobj_value(self)`
  Summary: Get the objective function value
- `set_var_bounds(self, var, lb, ub)`
  Summary: Modify the bounds of a variable
- `is_mip(self)`
  Summary: Is this model a MIP?
- `get_value(self, x)`
  Summary: Get the value of a variable stored in a numpy array of objects
- `get_dual_value(self, x)`
  Summary: Get the dual value of a variable stored in a numpy array of objects
- `status2string(self, val)`
  Summary: No docstring provided.
