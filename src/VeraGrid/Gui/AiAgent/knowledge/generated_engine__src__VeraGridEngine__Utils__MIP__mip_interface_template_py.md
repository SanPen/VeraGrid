# VeraGridEngine Module: src/VeraGridEngine/Utils/MIP/mip_interface_template.py

- Original source path: `src/VeraGridEngine/Utils/MIP/mip_interface_template.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

This module abstracts the synthax of PuLP out

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, abc, typing, VeraGridEngine.enumerations, VeraGridEngine.basic_structures

## Class: AbstractLpModel

- Bases: ABC
- Summary: Abstract base class for LP/MIP models.

### Methods

- `set_var_bounds(var, lb, ub)`
  Summary: Modify variable bounds.
- `add_int(self, lb, ub, name)`
  Summary: Add an integer variable.
- `add_var(self, lb, ub, name)`
  Summary: Add a continuous variable.
- `add_bin(self, name)`
  Summary: add binary variable.
- `add_cst(self, cst, name)`
  Summary: Add a constraint.
- `sum(exprs)`
  Summary: Sum of expressions.
- `minimize(self, obj_function)`
  Summary: Define minimization objective.
- `solve(self, robust, show_logs, progress_text)`
  Summary: Solve the optimization problem.
- `fobj_value(self)`
  Summary: Get the objective value.
- `get_value(x)`
  Summary: Return the numerical value of a variable/expression.
- `get_dual_value(x)`
  Summary: Return the dual value of a constraint.
- `status2string(self, stat)`
  Summary: Convert solver status to readable string.
- `save_model(self, file_name)`
  Summary: Export the model to LP/MPS for debugging.
- `is_mip(self)`
  Summary: Return True if model has integer variables.
- `model_as_string(self)`
  Summary: Return model string representation (LP)
