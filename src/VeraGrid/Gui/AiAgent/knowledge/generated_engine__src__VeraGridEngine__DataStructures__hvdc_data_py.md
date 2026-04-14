# VeraGridEngine Module: src/VeraGridEngine/DataStructures/hvdc_data.py

- Original source path: `src/VeraGridEngine/DataStructures/hvdc_data.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, numpy, typing, VeraGridEngine.DataStructures.branch_parent_data, VeraGridEngine.enumerations, VeraGridEngine.basic_structures

## Class: HvdcData

- Bases: BranchParentData
- Summary: HvdcData

### Methods

- `size(self)`
  Summary: Get size of the structure
- `slice(self, elm_idx, bus_idx, bus_map, logger)`
  Summary: Make a deep copy of this structure
- `remap(self, bus_map_arr)`
  Summary: Remapping of the branch buses
- `copy(self)`
  Summary: Make a deep copy of this structure
- `get_bus_indices_f(self)`
  Summary: Get bus indices "from"
- `get_bus_indices_t(self)`
  Summary: Get bus indices "to"
- `get_qmax_from_per_bus(self)`
  Summary: Max reactive power in the From Bus
- `get_qmin_from_per_bus(self)`
  Summary: Min reactive power in the From Bus
- `get_qmax_to_per_bus(self)`
  Summary: Max reactive power in the To Bus
- `get_qmin_to_per_bus(self)`
  Summary: Min reactive power in the To Bus
- `get_angle_droop_in_pu_rad(self, Sbase)`
  Summary: Get the angle droop in pu/rad
- `get_angle_droop_in_pu_rad_at(self, i, Sbase)`
  Summary: Get the angle droop in pu/rad
- `get_power(self, Sbase, theta)`
  Summary: Get hvdc power
- `get_inter_areas(self, bus_idx_from, bus_idx_to)`
  Summary: Get the hvdcs that join two areas
