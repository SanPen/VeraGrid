# VeraGridEngine Module: src/VeraGridEngine/Simulations/StateEstimation/state_estimation_inputs.py

- Original source path: `src/VeraGridEngine/Simulations/StateEstimation/state_estimation_inputs.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 1
- Representative imports: numpy, typing, VeraGridEngine.basic_structures, VeraGridEngine.Devices.measurement

## Function: slice_pair(obj_measurements, obj_indices, index_map)

Slice obj_measurements and obj_indices using an index->island index map

## Class: StateEstimationInput

- Bases: none
- Summary: StateEstimationInput

### Methods

- `size(self)`
  Summary: No docstring provided.
- `slice(self, bus_idx, branch_idx)`
  Summary: Slice this object given the island branch and bus indices
- `slice_with_mask(self, mask)`
  Summary: Get a new StateEstimationInput without the measurements that fall in the mask marked with a 0
