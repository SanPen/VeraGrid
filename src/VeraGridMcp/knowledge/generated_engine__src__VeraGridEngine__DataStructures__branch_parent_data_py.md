# VeraGridEngine Module: src/VeraGridEngine/DataStructures/branch_parent_data.py

- Original source path: `src/VeraGridEngine/DataStructures/branch_parent_data.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, numpy, pandas, scipy.sparse, VeraGridEngine.basic_structures, typing

## Class: BranchParentData

- Bases: none
- Summary: Structure to host all branches data for calculation

### Methods

- `Cf(self)`
  Summary: Bras-bus from connectivity
- `Ct(self)`
  Summary: Bras-bus to connectivity
- `monitored_Cf(self, idx)`
  Summary: Bras-bus from connectivity for monitored branches
- `monitored_Ct(self, idx)`
  Summary: Bras-bus to connectivity for monitored branches
- `C(self)`
  Summary: Branch-bus connectivity matrix
- `size(self)`
  Summary: Get size of the structure
- `slice(self, elm_idx, bus_idx, bus_map, logger)`
  Summary: Slice branch data by given indices
- `copy(self)`
  Summary: Get a deep copy of this object
- `get_ac_indices(self)`
  Summary: Get ac branch indices
- `get_dc_indices(self)`
  Summary: Get dc branch indices
- `get_monitor_enabled_indices(self)`
  Summary: Get monitored branch indices
- `get_contingency_enabled_indices(self)`
  Summary: Get contingency branch indices
- `get_inter_areas(self, bus_idx_from, bus_idx_to)`
  Summary: Get the Branches that join two areas
- `to_df(self)`
  Summary: Create DataFrame with the compiled Branches information
- `remap(self, bus_map_arr)`
  Summary: Remapping of the branch buses
- `get_3ph_names(self)`
  Summary: No docstring provided.
