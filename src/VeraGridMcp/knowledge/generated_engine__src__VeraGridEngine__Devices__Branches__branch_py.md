# VeraGridEngine Module: src/VeraGridEngine/Devices/Branches/branch.py

- Original source path: `src/VeraGridEngine/Devices/Branches/branch.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 1
- Representative imports: typing, pandas, numpy, matplotlib, enum, VeraGridEngine.Devices.Substation.bus, VeraGridEngine.enumerations, VeraGridEngine.Devices.Parents.branch_parent, VeraGridEngine.Devices.Branches.tap_changer, VeraGridEngine.Devices.Branches.transformer, VeraGridEngine.Devices.Branches.line, VeraGridEngine.Devices.Parents.editable_device

## Class: BranchType

- Bases: Enum
- Summary: No docstring provided.

### Methods

- `argparse(s)`
  Summary: No docstring provided.
- `list(cls)`
  Summary: No docstring provided.

## Class: Branch

- Bases: BranchParent
- Summary: No docstring provided.

### Methods

- `rate_prof(self)`
  Summary: Cost profile
- `rate_prof(self, val)`
  Summary: No docstring provided.
- `temp_oper_prof(self)`
  Summary: Cost profile
- `temp_oper_prof(self, val)`
  Summary: No docstring provided.
- `R_corrected(self)`
  Summary: Returns a temperature corrected resistance based on a formula provided by:
- `get_weight(self)`
  Summary: No docstring provided.
- `branch_type_converter(self, val_string)`
  Summary: function to convert the branch type string into the BranchType
- `copy(self, bus_dict)`
  Summary: Returns a copy of the branch
- `tap_up(self)`
  Summary: Move the tap changer one position up
- `tap_down(self)`
  Summary: Move the tap changer one position up
- `apply_tap_changer(self, tap_changer)`
  Summary: Apply a new tap changer
- `get_save_data(self)`
  Summary: Return the data that matches the edit_headers
- `plot_profiles(self, time_series, my_index, show_fig)`
  Summary: Plot the time series results of this object
- `get_coordinates(self)`
  Summary: Get the branch defining coordinates
- `get_equivalent_transformer(self, index)`
  Summary: Convert this line into a transformer
- `get_equivalent_line(self, index)`
  Summary: Get the equivalent line object
- `R(self)`
  Summary: Get ``R``.
- `R(self, val)`
  Summary: Set ``R``.
- `X(self)`
  Summary: Get ``X``.
- `X(self, val)`
  Summary: Set ``X``.
- `B(self)`
  Summary: Get ``B``.
- `B(self, val)`
  Summary: Set ``B``.
- `G(self)`
  Summary: Get ``G``.
- `G(self, val)`
  Summary: Set ``G``.
- `tolerance(self)`
  Summary: Get ``tolerance``.
- `tolerance(self, val)`
  Summary: Set ``tolerance``.
- `length(self)`
  Summary: Get ``length``.
- `length(self, val)`
  Summary: Set ``length``.
- `tap_module(self)`
  Summary: Get ``tap_module``.
- `tap_module(self, val)`
  Summary: Set ``tap_module``.
- `angle(self)`
  Summary: Get ``angle``.
- `angle(self, val)`
  Summary: Set ``angle``.
- `bus_to_regulated(self)`
  Summary: Get ``bus_to_regulated``.
- `bus_to_regulated(self, val)`
  Summary: Set ``bus_to_regulated``.
- `vset(self)`
  Summary: Get ``vset``.
- `vset(self, val)`
  Summary: Set ``vset``.
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

## Function: convert_branch(branch)

:param branch:
