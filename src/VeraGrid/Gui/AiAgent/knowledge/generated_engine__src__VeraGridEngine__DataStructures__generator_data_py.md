# VeraGridEngine Module: src/VeraGridEngine/DataStructures/generator_data.py

- Original source path: `src/VeraGridEngine/DataStructures/generator_data.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: typing, numpy, scipy.sparse, VeraGridEngine.Topology.topology, VeraGridEngine.basic_structures

## Class: GeneratorData

- Bases: none
- Summary: GeneratorData

### Methods

- `slice(self, elm_idx, bus_idx, bus_map)`
  Summary: Slice generator data by given indices
- `remap(self, bus_map_arr)`
  Summary: Remapping of the elm buses
- `size(self)`
  Summary: Get size of the structure
- `copy(self)`
  Summary: Get a deep copy of this object
- `get_injections(self)`
  Summary: Compute the active and reactive power of non-controlled generators (assuming all)
- `get_q_at(self, i)`
  Summary: :param i:
- `get_Yshunt(self, seq)`
  Summary: Obtain the vector of shunt admittances of a given sequence per bus
- `get_effective_generation(self)`
  Summary: Get generator effective power
- `get_array_per_bus(self, arr)`
  Summary: Get generator array per bus
- `get_injections_per_bus(self)`
  Summary: Get generator Injections per bus
- `get_dispatchable_per_bus(self)`
  Summary: Get generator Injections per bus
- `get_installed_power_per_bus(self)`
  Summary: Get generator installed power per bus
- `get_qmax_per_bus(self)`
  Summary: Get generator Qmax per bus
- `get_qmin_per_bus(self)`
  Summary: Get generator Qmin per bus
- `get_pmax_per_bus(self)`
  Summary: Get generator Pmax per bus
- `get_pmin_per_bus(self)`
  Summary: Get generator Pmin per bus
- `get_array_per_bus_obj(self, arr)`
  Summary: Sum per bus in python mode (it can add objects)
- `dev_per_bus(self)`
  Summary: Get number of devices per bus
- `get_bus_indices(self)`
  Summary: Get the bus indices
- `get_dispatchable_indices(self)`
  Summary: Get the indices of dispatchable generators
- `get_dispatchable_active_indices(self)`
  Summary: Get the indices of dispatchable generators
- `get_non_dispatchable_indices(self)`
  Summary: Get the indices of dispatchable generators
- `get_controllable_and_not_controllable_indices(self)`
  Summary: Get the indices of controllable generators
- `get_gen_indices_at_buses(self, bus_indices)`
  Summary: No docstring provided.
- `get_C_bus_elm(self)`
  Summary: Get the connectivity matrix
