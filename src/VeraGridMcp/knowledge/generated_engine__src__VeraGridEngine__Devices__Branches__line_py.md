# VeraGridEngine Module: src/VeraGridEngine/Devices/Branches/line.py

- Original source path: `src/VeraGridEngine/Devices/Branches/line.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 1
- Representative imports: numpy, pandas, typing, VeraGridEngine.basic_structures, VeraGridEngine.Devices.Substation.bus, VeraGridEngine.enumerations, VeraGridEngine.Devices.Branches.underground_line_type, VeraGridEngine.Devices.Branches.overhead_line_type, VeraGridEngine.Devices.Parents.branch_parent, VeraGridEngine.Devices.Branches.sequence_line_type, VeraGridEngine.Devices.Branches.transformer, VeraGridEngine.Devices.Associations.association, VeraGridEngine.Devices.Branches.line_locations, VeraGridEngine.Devices.admittance_matrix, VeraGridEngine.Utils.Symbolic.block, VeraGridEngine.Devices.Parents.editable_device

## Function: accept_line_connection(V1, V2, branch_connection_voltage_tolerance)

This function checks if a line can be connected between 2 voltages

## Class: Line

- Bases: BranchParent
- Summary: No docstring provided.

### Methods

- `R(self)`
  Summary: No docstring provided.
- `R(self, value)`
  Summary: No docstring provided.
- `X(self)`
  Summary: No docstring provided.
- `X(self, value)`
  Summary: No docstring provided.
- `B(self)`
  Summary: No docstring provided.
- `B(self, value)`
  Summary: No docstring provided.
- `R0(self)`
  Summary: No docstring provided.
- `R0(self, value)`
  Summary: No docstring provided.
- `X0(self)`
  Summary: No docstring provided.
- `X0(self, value)`
  Summary: No docstring provided.
- `B0(self)`
  Summary: No docstring provided.
- `B0(self, value)`
  Summary: No docstring provided.
- `R2(self)`
  Summary: No docstring provided.
- `R2(self, value)`
  Summary: No docstring provided.
- `X2(self)`
  Summary: No docstring provided.
- `X2(self, value)`
  Summary: No docstring provided.
- `B2(self)`
  Summary: No docstring provided.
- `B2(self, value)`
  Summary: No docstring provided.
- `circuit_idx(self)`
  Summary: :return:
- `circuit_idx(self, value)`
  Summary: No docstring provided.
- `set_circuit_idx(self, val, obj)`
  Summary: Set the circuit_idx with additional behavior based on the is_user_action flag. Ensure that the template exists and is valid.
- `length(self)`
  Summary: Line length in km
- `length(self, val)`
  Summary: Set the length of the line, if a valid length is provided, the electric parameters are scaled appropriately
- `set_length(self, val)`
  Summary: Set the line length and change the electric parameters of the line as a consequence.
- `locations(self)`
  Summary: Cost profile
- `locations(self, val)`
  Summary: No docstring provided.
- `R_corrected(self)`
  Summary: Returns a temperature corrected resistance based on a formula provided by:
- `ys(self)`
  Summary: :return:
- `ys(self, val)`
  Summary: No docstring provided.
- `ysh(self)`
  Summary: :return:
- `ysh(self, val)`
  Summary: No docstring provided.
- `change_base(self, Sbase_old, Sbase_new)`
  Summary: Change the impedance base
- `get_weight(self)`
  Summary: Get a weight of this line for graph purposes
- `apply_template(self, obj, Sbase, freq, logger, decimals_rounding)`
  Summary: Apply a line template to this object
- `get_line_type(self)`
  Summary: Get the equivalent sequence line type of this line
- `fix_inconsistencies(self, logger)`
  Summary: Fix the inconsistencies
- `get_equivalent_transformer(self, index)`
  Summary: Convert this line into a transformer
- `fill_design_properties(self, r_ohm, x_ohm, c_nf, length, Imax, freq, Sbase, apply_to_profile, logger)`
  Summary: Fill R, X, B from not-in-per-unit parameters
- `get_tau(self, w)`
  Summary: get EMT delay parameter (tau) in seconds
- `fill_3_phase_from_sequence(self)`
  Summary: Fill the 3x3 from the sequence values
- `tolerance(self)`
  Summary: Get ``tolerance``.
- `tolerance(self, val)`
  Summary: Set ``tolerance``.
- `r_fault(self)`
  Summary: Get ``r_fault``.
- `r_fault(self, val)`
  Summary: Set ``r_fault``.
- `x_fault(self)`
  Summary: Get ``x_fault``.
- `x_fault(self, val)`
  Summary: Set ``x_fault``.
- `fault_pos(self)`
  Summary: Get ``fault_pos``.
- `fault_pos(self, val)`
  Summary: Set ``fault_pos``.
