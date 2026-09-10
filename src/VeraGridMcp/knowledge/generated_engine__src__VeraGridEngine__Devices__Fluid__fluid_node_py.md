# VeraGridEngine Module: src/VeraGridEngine/Devices/Fluid/fluid_node.py

- Original source path: `src/VeraGridEngine/Devices/Fluid/fluid_node.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, typing, numpy, VeraGridEngine.Devices.Parents.physical_device, VeraGridEngine.Devices.Substation.bus, VeraGridEngine.enumerations,  VeraGridEngine.Devices.Parents.editable_device

## Class: FluidNode

- Bases: PhysicalDevice
- Summary: No docstring provided.

### Methods

- `spillage_cost_prof(self)`
  Summary: Cost profile
- `spillage_cost_prof(self, val)`
  Summary: No docstring provided.
- `get_spillage_cost_at(self, t)`
  Summary: :param t:
- `inflow_prof(self)`
  Summary: Cost profile
- `inflow_prof(self, val)`
  Summary: No docstring provided.
- `get_inflow_at(self, t)`
  Summary: :param t:
- `max_soc_prof(self)`
  Summary: Max soc profile
- `max_soc_prof(self, val)`
  Summary: No docstring provided.
- `get_max_soc_at(self, t)`
  Summary: :param t:
- `min_soc_prof(self)`
  Summary: Min soc profile
- `min_soc_prof(self, val)`
  Summary: No docstring provided.
- `get_min_soc_at(self, t)`
  Summary: :param t:
- `copy(self)`
  Summary: Make a deep copy of this object
- `bus(self)`
  Summary: Bus getter function
- `bus(self, val)`
  Summary: bus setter function
- `min_level(self)`
  Summary: Get ``min_level``.
- `min_level(self, val)`
  Summary: Set ``min_level``.
- `max_level(self)`
  Summary: Get ``max_level``.
- `max_level(self, val)`
  Summary: Set ``max_level``.
- `min_soc(self)`
  Summary: Get ``min_soc``.
- `min_soc(self, val)`
  Summary: Set ``min_soc``.
- `max_soc(self)`
  Summary: Get ``max_soc``.
- `max_soc(self, val)`
  Summary: Set ``max_soc``.
- `initial_level(self)`
  Summary: Get ``initial_level``.
- `initial_level(self, val)`
  Summary: Set ``initial_level``.
- `spillage_cost(self)`
  Summary: Get ``spillage_cost``.
- `spillage_cost(self, val)`
  Summary: Set ``spillage_cost``.
- `inflow(self)`
  Summary: Get ``inflow``.
- `inflow(self, val)`
  Summary: Set ``inflow``.
