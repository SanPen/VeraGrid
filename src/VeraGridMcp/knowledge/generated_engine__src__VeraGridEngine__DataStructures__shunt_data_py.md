# VeraGridEngine Module: src/VeraGridEngine/DataStructures/shunt_data.py

- Original source path: `src/VeraGridEngine/DataStructures/shunt_data.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: typing, numpy, scipy.sparse, VeraGridEngine.Topology.topology, VeraGridEngine.Utils.Sparse.sparse_array, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Class: ShuntData

- Bases: none
- Summary: ShuntData

### Methods

- `size(self)`
  Summary: Get size of the structure
- `slice(self, elm_idx, bus_idx, bus_map)`
  Summary: Slice shunt data by given indices
- `remap(self, bus_map_arr)`
  Summary: Remapping of the elm buses
- `copy(self)`
  Summary: Get deep copy of this structure
- `get_array_per_bus(self, arr)`
  Summary: Get generator array per bus
- `get_injections_per_bus(self)`
  Summary: Get Injections per bus
- `get_fix_injections_per_bus(self)`
  Summary: Get fixed Injections per bus
- `get_qmax_per_bus(self)`
  Summary: Get generator Qmax per bus
- `get_qmin_per_bus(self)`
  Summary: Get generator Qmin per bus
- `get_bus_indices(self)`
  Summary: Get the bus indices
- `get_controllable_and_not_controllable_indices(self)`
  Summary: Get the indices of controllable generators
- `get_C_bus_elm(self)`
  Summary: Get the connectivity matrix
