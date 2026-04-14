# VeraGridEngine Module: src/VeraGridEngine/DataStructures/passive_branch_data.py

- Original source path: `src/VeraGridEngine/DataStructures/passive_branch_data.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, numpy, VeraGridEngine, VeraGridEngine.DataStructures.branch_parent_data, VeraGridEngine.enumerations, VeraGridEngine.Utils.Sparse.sparse_array, VeraGridEngine.basic_structures, typing

## Class: PassiveBranchData

- Bases: BranchParentData
- Summary: Structure to host all branches data for calculation

### Methods

- `size(self)`
  Summary: Get size of the structure
- `slice(self, elm_idx, bus_idx, bus_map, logger)`
  Summary: Slice branch data by given indices
- `copy(self)`
  Summary: Get a deep copy of this object
- `get_series_admittance(self)`
  Summary: Get the series admittance of the branches
- `detect_superconductor_at(self, k)`
  Summary: There is a beyond terrible practice of setting branches with R=0 and X=0 as "superconductor"....
