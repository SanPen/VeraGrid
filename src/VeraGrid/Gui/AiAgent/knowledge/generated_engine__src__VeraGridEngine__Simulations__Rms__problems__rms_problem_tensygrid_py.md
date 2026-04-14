# VeraGridEngine Module: src/VeraGridEngine/Simulations/Rms/problems/rms_problem_tensygrid.py

- Original source path: `src/VeraGridEngine/Simulations/Rms/problems/rms_problem_tensygrid.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 4
- Representative imports: typing, time, numpy, pandas, VeraGridEngine.Devices, VeraGridEngine.Simulations.driver_template, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.Utils.Symbolic.compiled_functions, VeraGridEngine.Utils.Symbolic.block, VeraGridEngine.Utils.Symbolic.symbolic_io, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, VeraGridEngine.Simulations.PowerFlow.power_flow_driver, VeraGridEngine.Simulations.Rms.rms_options, VeraGridEngine.Simulations.Rms.initialization, VeraGridEngine.Simulations.Rms.problems.rms_problem_template

## Function: _tic()

No docstring provided.

## Function: _toc(t0)

No docstring provided.

## Function: setP(P, P_used, k, val)

:param P:

## Function: setQ(Q, Q_used, k, val)

:param Q:

## Class: RmsProblemTensygrid

- Bases: RmsProblemTemplate
- Summary: DAE (Differential-Algebraic Equation) class to store and manage.

### Methods

- `add_variables_to_compilation_dicts(self, elm, mdl)`
  Summary: add variables and parameters info to the system block
- `set_init_guess(self, mdl, reference_powerflow, val)`
  Summary: add values from powerflow to initial guess
- `get_init_guess_info(self)`
  Summary: returns a df with uid, name, and initial value for the system variables
- `get_device_vars_dict(self)`
  Summary: :return:
- `add_device_var(self, dev, var)`
  Summary: Associate a variable with a device
- `get_var_idx(self, v)`
  Summary: :param v:
- `vars_glob_name2uid(self)`
  Summary: :return:
- `uid2idx_vars(self)`
  Summary: :return:
- `get_algebraic_vars(self)`
  Summary: :return:
- `state_and_algebraic_vars(self)`
  Summary: :return:
- `get_state_vars(self)`
  Summary: :return:
- `get_all_vars_number(self)`
  Summary: No docstring provided.
- `get_diff_var_number(self)`
  Summary: Get the number of diff vars
- `get_algebraic_var_number(self)`
  Summary: No docstring provided.
- `get_states_number(self)`
  Summary: No docstring provided.
- `get_variable_parameter_number(self)`
  Summary: No docstring provided.
- `get_x0(self)`
  Summary: Helper function to build the initial vector
- `update_variable_params(self, t)`
  Summary: Update the variable parameters
- `update_variable_params_ts(self, x, t)`
  Summary: Update the variable parameters
- `get_dx(self, x, xn, dx, h)`
  Summary: No docstring provided.
- `rhs_state(self, x, dx)`
  Summary: No docstring provided.
- `rhs_algebraic(self, x, dx)`
  Summary: No docstring provided.
- `get_j11(self, x, dx, h)`
  Summary: No docstring provided.
- `get_j12(self, x, dx, h)`
  Summary: No docstring provided.
- `get_j21(self, x, dx, h)`
  Summary: No docstring provided.
- `get_j22(self, x, dx, h)`
  Summary: No docstring provided.
- `get_dt(self)`
  Summary: No docstring provided.
- `get_dt_value(self)`
  Summary: No docstring provided.
- `set_events_group(self, rms_events_group)`
  Summary: Set the events group to use for this simulation.
