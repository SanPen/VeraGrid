# VeraGridEngine Module: src/VeraGridEngine/Utils/MIP/pulp_interface.py

- Original source path: `src/VeraGridEngine/Utils/MIP/pulp_interface.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

This module abstracts the synthax of PuLP out

## Module Surface

- Class count: 1
- Top-level function count: 2
- Representative imports: __future__, typing, subprocess, pulp, pulp, pulp, pulp, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, VeraGridEngine.Utils.MIP.mip_interface_template

## Function: get_lp_var_value(x)

Get the value of a variable stored in a numpy array of objects

## Function: get_pulp_available_mip_solvers()

Get a list of candidate solvers

## Class: PulpLpModel

- Bases: AbstractLpModel
- Summary: LPModel implementation for PuLP

### Methods

- `set_var_bounds(var, lb, ub)`
  Summary: Modify the bounds of a variable
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
- `get_solver(self, show_logs)`
  Summary: :param show_logs:
- `solve(self, robust, show_logs, progress_text)`
  Summary: Solve the model
- `fobj_value(self)`
  Summary: Get the objective function value
- `is_mip(self)`
  Summary: Is this odel a MIP?
- `get_value(x)`
  Summary: Get the value of a variable stored in a numpy array of objects
- `get_dual_value(x)`
  Summary: Get the dual value of a variable stored in a numpy array of objects
- `status2string(self, stat)`
  Summary: Convert the PuLP status to a string
- `model_as_string(self)`
  Summary: Return the LP representation
