# VeraGridEngine Module: src/VeraGridEngine/Simulations/Rms/problems/rms_problem_phasor.py

- Original source path: `src/VeraGridEngine/Simulations/Rms/problems/rms_problem_phasor.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 6
- Representative imports: typing, time, numpy, pandas, VeraGridEngine, VeraGridEngine.Devices, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.Utils.Symbolic.compiled_functions, VeraGridEngine.Utils.Symbolic.block, VeraGridEngine.Utils.Symbolic.symbolic_io, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, VeraGridEngine.Simulations.PowerFlow.power_flow_driver, VeraGridEngine.Simulations.Rms.rms_options, VeraGridEngine.Simulations.Rms.initialization, VeraGridEngine.Simulations.Rms.problems.rms_problem_template

## Function: _tic()

No docstring provided.

## Function: _toc(t0)

No docstring provided.

## Function: setP(P, P_used, k, val)

Set or add to P value at index k.

## Function: setQ(Q, Q_used, k, val)

Set or add to Q value at index k.

## Function: setIr(Ir, Ir_used, k, val)

Set or add to Ir (real current) value at index k.

## Function: setIi(Ii, Ii_used, k, val)

Set or add to Ii (imaginary current) value at index k.

## Class: RmsProblemPhasor

- Bases: RmsProblemTemplate
- Summary: Phasor-based DAE (Differential-Algebraic Equation) class.

### Methods

- `add_variables_to_compilation_dicts(self, elm, mdl)`
  Summary: add variables and parameters info to the system block
- `set_init_guess(self, mdl, reference_powerflow, val)`
  Summary: Add values from powerflow to initial guess.
- `get_init_guess_info(self)`
  Summary: Returns a df with uid, name, and initial value for the system variables.
- `get_E_matrix(self, x, dx)`
  Summary: No docstring provided.
- `get_device_vars_dict(self)`
  Summary: Get dictionary of device variables.
- `add_device_var(self, dev, var)`
  Summary: Associate a variable with a device.
- `get_var_idx(self, v)`
  Summary: Get variable index.
- `vars_glob_name2uid(self)`
  Summary: No docstring provided.
- `uid2idx_vars(self)`
  Summary: No docstring provided.
- `get_algebraic_vars(self)`
  Summary: No docstring provided.
- `state_and_algebraic_vars(self)`
  Summary: No docstring provided.
- `get_state_vars(self)`
  Summary: No docstring provided.
- `get_algebraic_eqs(self)`
  Summary: No docstring provided.
- `get_state_eqs(self)`
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
- `get_x0(self)`
  Summary: Helper function to build the initial vector.
- `update_variable_params(self, t)`
  Summary: Update the variable parameters.
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
