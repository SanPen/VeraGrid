# VeraGridEngine Module: src/VeraGridEngine/Utils/MIP/ortools_interface.py

- Original source path: `src/VeraGridEngine/Utils/MIP/ortools_interface.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

This module abstracts the synthax of ORTOOLS out

## Module Surface

- Class count: 1
- Top-level function count: 2
- Representative imports: __future__, typing, ortools.linear_solver.python, ortools.linear_solver.python.model_builder, ortools.linear_solver.python.model_builder, ortools.linear_solver.python.model_builder, ortools.linear_solver.python.model_builder, ortools.linear_solver.python.model_builder_helper, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, VeraGridEngine.Utils.MIP.mip_interface_template

## Function: get_ortools_available_mip_solvers()

Get a list of candidate solvers

## Function: get_solver_params_string(solver, relative_gap, abs_gap, primal_feasibility_tolerance, dual_feasibility_tolerance, optimality_tolerance, time_limit, verbose)

Returns a string of solver-specific parameters suitable for

## Class: OrToolsLpModel

- Bases: AbstractLpModel
- Summary: LPModel implementation for ORTOOLS

### Methods

- `set_var_bounds(var, lb, ub)`
  Summary: Modify the bounds of a variable
- `save_model(self, file_name)`
  Summary: Save problem in LP format
- `model_as_string(self)`
  Summary: Model as string
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
- `pass_through_file(self, fname)`
  Summary: :param fname:
- `solve(self, robust, show_logs, progress_text)`
  Summary: Solve the model
- `fobj_value(self)`
  Summary: Get the objective function value
- `is_mip(self)`
  Summary: Is this Model a MIP?
- `get_value(self, x)`
  Summary: Get the value of a variable stored in a numpy array of objects
- `get_dual_value(self, x)`
  Summary: Get the dual value of a variable stored in a numpy array of objects
- `status2string(self, stat)`
  Summary: Convert ortools status to string
