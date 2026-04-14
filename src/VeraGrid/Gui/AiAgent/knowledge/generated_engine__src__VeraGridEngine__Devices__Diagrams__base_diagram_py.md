# VeraGridEngine Module: src/VeraGridEngine/Devices/Diagrams/base_diagram.py

- Original source path: `src/VeraGridEngine/Devices/Diagrams/base_diagram.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 0
- Representative imports: __future__, sys, uuid, networkx, typing, VeraGridEngine.Devices.Diagrams.graphic_location, VeraGridEngine.Devices.Diagrams.map_location, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Class: PointsGroup

- Bases: none
- Summary: Diagram

### Methods

- `set_point(self, device, location)`
  Summary: :param device:
- `delete_device(self, device)`
  Summary: Delete location
- `query_point(self, device)`
  Summary: :param device:
- `get_dict(self)`
  Summary: :return:
- `parse_data(self, data, obj_dict, logger, category)`
  Summary: Parse file data ito this class

## Class: BaseDiagram

- Bases: none
- Summary: Diagram

### Methods

- `use_flow_based_width(self)`
  Summary: :return:
- `use_flow_based_width(self, value)`
  Summary: No docstring provided.
- `min_branch_width(self)`
  Summary: :return:
- `min_branch_width(self, value)`
  Summary: No docstring provided.
- `max_branch_width(self)`
  Summary: :return:
- `max_branch_width(self, value)`
  Summary: No docstring provided.
- `min_bus_width(self)`
  Summary: :return:
- `min_bus_width(self, value)`
  Summary: No docstring provided.
- `max_bus_width(self)`
  Summary: :return:
- `max_bus_width(self, value)`
  Summary: No docstring provided.
- `arrow_size(self)`
  Summary: :return:
- `arrow_size(self, value)`
  Summary: No docstring provided.
- `palette(self)`
  Summary: :return:
- `palette(self, value)`
  Summary: No docstring provided.
- `default_bus_voltage(self)`
  Summary: :return:
- `default_bus_voltage(self, value)`
  Summary: No docstring provided.
- `use_api_colors(self)`
  Summary: No docstring provided.
- `use_api_colors(self, value)`
  Summary: No docstring provided.
- `set_point(self, device, location)`
  Summary: :param device:
- `delete_device(self, device)`
  Summary: :param device:
- `query_point(self, device)`
  Summary: :param device:
- `query_by_type(self, device_type)`
  Summary: Query diagram by device type
- `get_data_dict(self)`
  Summary: get the properties dictionary to save
- `parse_data(self, data, obj_dict, logger)`
  Summary: Parse file data ito this class
- `build_graph(self)`
  Summary: Returns a networkx DiGraph object of the grid.
- `get_boundaries(self)`
  Summary: Get the graphic representation boundaries
- `set_size_constraints(self, use_flow_based_width, min_branch_width, max_branch_width, min_bus_width, max_bus_width, arrow_size)`
  Summary: Set the size constraints
