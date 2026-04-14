# VeraGridEngine Module: src/VeraGridEngine/Utils/MIP/SimpleMip/lpmodel.py

- Original source path: `src/VeraGridEngine/Utils/MIP/SimpleMip/lpmodel.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 2
- Representative imports: warnings, typing, numpy, uuid, scipy.sparse, VeraGridEngine.Utils.MIP.SimpleMip.lpobjects, VeraGridEngine.Utils.MIP.SimpleMip.highs, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Function: get_available_mip_solvers()

Get a list of candidate solvers

## Function: set_var_bounds(var, lb, ub)

Modify the bounds of a variable

## Class: LpModel

- Bases: none
- Summary: SimpleMIP

### Methods

- `is_minimize(self)`
  Summary: Minimize?
- `copy(self, copy_results)`
  Summary: Deep copy of this
- `get_obj_coefficient(self, var)`
  Summary: Get the coefficient of a variable, if not found, return 0.0
- `_add_variable(self, lb, ub, name, is_int)`
  Summary: Add a variable to the problem
- `add_int(self, lb, ub, name)`
  Summary: Make integer LP var
- `add_var(self, lb, ub, name)`
  Summary: Make floating point LP var
- `add_vars(self, size, lb, ub, name, is_int)`
  Summary: Make array of LP vars
- `_set_objective(self, expression, is_minimize)`
  Summary: Set the objective function
- `minimize(self, obj_function)`
  Summary: Set the objective to minimize
- `maximize(self, obj_function)`
  Summary: Set the objective to maximize
- `add_cst(self, cst, name)`
  Summary: Add constraint to the model
- `sum(expr)`
  Summary: create sum of the expression
- `save_model_to_lp(self, filename)`
  Summary: Save model to LP file
- `save_model_to_mps(self, filename)`
  Summary: Save the model to MPS
- `save_model(self, file_name)`
  Summary: Save model in lp or mps format
- `get_coefficients_data(self)`
  Summary: Returns the coefficient matrix
- `get_var_data(self)`
  Summary: Get arrays related to the variable bounds and the objective function coefficients
- `is_optimal(self)`
  Summary: :return:
- `_solve(self, model, verbose)`
  Summary: No docstring provided.
- `solve(self, robust, show_logs, progress_text)`
  Summary: Solve the model
- `status2string(self, status)`
  Summary: No docstring provided.
- `set_solution(self, col_values, col_duals, row_values, row_duals, f_obj, is_optimal)`
  Summary: Set solution from the MIP solver
- `fobj_value(self)`
  Summary: Get the objective function value
- `is_mip(self)`
  Summary: Is this model a MIP?
- `get_objective_value(self)`
  Summary: Get the objective function value
- `get_value(self, var)`
  Summary: Get the value of a variable
- `get_dual_value(self, var)`
  Summary: Get the dual value of a variable
- `get_array_value(self, arr)`
  Summary: Get the array of var values
- `solution_available(self)`
  Summary: Is there a solution loaded?
- `print_solution(self)`
  Summary: Print available solution
