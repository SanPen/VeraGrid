# VeraGridEngine Module: src/VeraGridEngine/DataStructures/load_data.py

- Original source path: `src/VeraGridEngine/DataStructures/load_data.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: numpy, VeraGridEngine.Topology.topology, VeraGridEngine.basic_structures

## Class: LoadData

- Bases: none
- Summary: Structure to host the load calculation information

### Methods

- `size(self)`
  Summary: Get size of the structure
- `slice(self, elm_idx, bus_idx, bus_map)`
  Summary: Slice load data by given indices
- `remap(self, bus_map_arr)`
  Summary: Remapping of the elm buses
- `copy(self)`
  Summary: Get a deep copy of this structure
- `get_effective_load(self)`
  Summary: Get effective load
- `get_linear_effective_load(self)`
  Summary: Get effective load
- `get_injections_per_bus(self)`
  Summary: Get Injections per bus with sign
- `get_linear_injections_per_bus(self)`
  Summary: Get Injections per bus with sign
- `get_array_per_bus(self, arr)`
  Summary: Get generator array per bus
- `get_array_per_bus_obj(self, arr)`
  Summary: Sum per bus in python mode (it can add objects)
- `get_current_injections_per_bus(self)`
  Summary: Get current Injections per bus with sign
- `get_admittance_injections_per_bus(self)`
  Summary: Get admittance Injections per bus with sign
- `get_bus_indices(self)`
  Summary: Get the bus indices
