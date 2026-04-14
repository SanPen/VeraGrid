# VeraGridEngine Module: src/VeraGridEngine/Templates/Emt/bergeron_line_emt_template.py

- Original source path: `src/VeraGridEngine/Templates/Emt/bergeron_line_emt_template.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 1
- Representative imports: numpy, scipy.linalg, typing, VeraGridEngine.Utils.Symbolic.block, VeraGridEngine.enumerations, VeraGridEngine.Devices.Dynamic.var_factory, VeraGridEngine.Devices.Dynamic.emt_template, VeraGridEngine.Devices.Branches.line

## Function: get_bergeron_line_emt_template(vf, line, name)

Create the symbolic EMT template for a Bergeron line.

## Class: BergeronHistoryRuntime

- Bases: none
- Summary: Runtime companion for a Bergeron line in reduced active-phase space.

### Methods

- `_extract_hist_vars(self, prefix)`
  Summary: No docstring provided.
- `bind_terminals(self, v_f_vars, v_t_vars)`
  Summary: Bind the bus terminal voltage variables for the active phases only.
- `get_nodal_injections(self)`
  Summary: No docstring provided.
- `setup_indices(self, uid2idx_vars, uid2idx_event_params, params_offset)`
  Summary: No docstring provided.
- `update_history(self, step_counter, x_prev, full_params)`
  Summary: No docstring provided.
- `initialize_buffers_from_initial_point(self, v_f0_red, v_t0_red, i_f0_red, i_t0_red)`
  Summary: Fill all delay buffers with the initial steady-state point.
