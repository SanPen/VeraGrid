# VeraGridEngine Module: src/VeraGridEngine/Simulations/Rms/problems/rms_problem_template.py

- Original source path: `src/VeraGridEngine/Simulations/Rms/problems/rms_problem_template.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: abc, typing, numpy, VeraGridEngine.Devices.types, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.basic_structures, VeraGridEngine.Simulations.driver_template

## Class: RmsProblemTemplate

- Bases: ABC
- Summary: No docstring provided.

### Methods

- `set_initialize_flag(self)`
  Summary: No docstring provided.
- `is_initialized(self)`
  Summary: No docstring provided.
- `get_vars_info(self)`
  Summary: No docstring provided.
- `get_all_vars_number(self)`
  Summary: No docstring provided.
- `get_diff_var_number(self)`
  Summary: No docstring provided.
- `get_algebraic_var_number(self)`
  Summary: No docstring provided.
- `get_states_number(self)`
  Summary: No docstring provided.
- `get_variable_parameter_number(self)`
  Summary: No docstring provided.
- `get_algebraic_vars(self)`
  Summary: No docstring provided.
- `get_state_vars(self)`
  Summary: No docstring provided.
- `get_x0(self)`
  Summary: No docstring provided.
- `update_variable_params(self, t)`
  Summary: No docstring provided.
- `get_dx(self, x, xn, dx, h)`
  Summary: No docstring provided.
- `rhs_state(self, x, dx)`
  Summary: No docstring provided.
- `rhs_algebraic(self, values, diff_values)`
  Summary: No docstring provided.
- `get_j11(self, x, dx, h)`
  Summary: No docstring provided.
- `get_j12(self, x, dx, h)`
  Summary: No docstring provided.
- `get_j21(self, x, dx, h)`
  Summary: No docstring provided.
- `get_j22(self, x, dx, h)`
  Summary: No docstring provided.
- `get_E_matrix(self, x, dx)`
  Summary: No docstring provided.
- `get_dt(self)`
  Summary: No docstring provided.
- `get_dt_value(self)`
  Summary: No docstring provided.
- `report_progress(self, val)`
  Summary: Report progress
- `report_progress2(self, current, total)`
  Summary: Report progress
- `report_text(self, val)`
  Summary: Report text
