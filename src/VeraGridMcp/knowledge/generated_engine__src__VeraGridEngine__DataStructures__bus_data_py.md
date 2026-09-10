# VeraGridEngine Module: src/VeraGridEngine/DataStructures/bus_data.py

- Original source path: `src/VeraGridEngine/DataStructures/bus_data.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: typing, numpy, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Class: BusData

- Bases: none
- Summary: BusData

### Methods

- `slice(self, elm_idx)`
  Summary: Slice this data structure
- `size(self)`
  Summary: Get size of the structure
- `copy(self)`
  Summary: Deep copy of this structure
- `get_original_to_island_bus_dict(self)`
  Summary: Dictionary that relates the original bus index to the island bus index
- `get_idtag_dict(self)`
  Summary: Get dictionary of bus idtagd related to the island bus index
- `set_bus_mode(self, idx, val)`
  Summary: Set bus mode
- `get_3ph_names(self)`
  Summary: Get the 3-phase names
