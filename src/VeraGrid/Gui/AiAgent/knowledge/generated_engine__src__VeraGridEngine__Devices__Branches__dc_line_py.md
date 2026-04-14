# VeraGridEngine Module: src/VeraGridEngine/Devices/Branches/dc_line.py

- Original source path: `src/VeraGridEngine/Devices/Branches/dc_line.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: pandas, typing, matplotlib, numpy, VeraGridEngine.Devices.Substation.bus, VeraGridEngine.Devices.Parents.branch_parent,  VeraGridEngine.enumerations, VeraGridEngine.Devices.Branches.line_locations, VeraGridEngine.Devices.Parents.editable_device

## Class: DcLine

- Bases: BranchParent
- Summary: No docstring provided.

### Methods

- `temp_oper_prof(self)`
  Summary: Cost profile
- `temp_oper_prof(self, val)`
  Summary: No docstring provided.
- `locations(self)`
  Summary: Cost profile
- `locations(self, val)`
  Summary: No docstring provided.
- `R_corrected(self)`
  Summary: Returns a temperature corrected resistance based on a formula provided by:
- `length(self)`
  Summary: Line length in km
- `length(self, val)`
  Summary: No docstring provided.
- `change_base(self, Sbase_old, Sbase_new)`
  Summary: :param Sbase_old:
- `get_weight(self)`
  Summary: :return:
- `copy(self, bus_dict)`
  Summary: Returns a copy of the dc line
- `plot_profiles(self, time_series, my_index, show_fig)`
  Summary: Plot the time series results of this object
- `get_coordinates(self)`
  Summary: Get the branch defining coordinates
- `R(self)`
  Summary: Get ``R``.
- `R(self, val)`
  Summary: Set ``R``.
- `r_fault(self)`
  Summary: Get ``r_fault``.
- `r_fault(self, val)`
  Summary: Set ``r_fault``.
- `fault_pos(self)`
  Summary: Get ``fault_pos``.
- `fault_pos(self, val)`
  Summary: Set ``fault_pos``.
