# VeraGridEngine Module: src/VeraGridEngine/Devices/Aggregation/inter_aggregation_info.py

- Original source path: `src/VeraGridEngine/Devices/Aggregation/inter_aggregation_info.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, typing, numpy, VeraGridEngine.Devices.Parents.editable_device, VeraGridEngine.basic_structures, VeraGridEngine.basic_structures

## Class: InterAggregationInfo

- Bases: EditableDevice
- Summary: Class to store information of inter area, inter country, etc

### Methods

- `idx_bus_from(self)`
  Summary: Get bus of the aggregation "from" indices
- `idx_bus_to(self)`
  Summary: Get bus of the aggregation "to" indices
- `idx_branches(self)`
  Summary: Get array of tie-branches indices
- `sense_branches(self)`
  Summary: Get array of tie-branch sense values (1 for from->to, -1 for to->from)
- `idx_hvdc(self)`
  Summary: :return:
- `sense_hvdc(self)`
  Summary: :return:
- `is_from(self, bus_idx)`
  Summary: check if a bus index belongs to the "from" set
- `is_to(self, bus_idx)`
  Summary: check if a bus index belongs to the "to" set
