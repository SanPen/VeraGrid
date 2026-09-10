# VeraGridEngine Module: src/VeraGridEngine/Devices/Diagrams/block_diagram.py

- Original source path: `src/VeraGridEngine/Devices/Diagrams/block_diagram.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 3
- Top-level function count: 0
- Representative imports: __future__, typing, dataclasses

## Class: BlockDiagramNode

- Bases: none
- Summary: BlockDiagramNode

### Methods

- `get_node_dict(self)`
  Summary: :return:
- `copy(self)`
  Summary: Deep copy

## Class: BlockDiagramConnection

- Bases: none
- Summary: BlockDiagramConnection

### Methods

- `get_connection_dict(self)`
  Summary: get as a dictionary point
- `copy(self)`
  Summary: No docstring provided.

## Class: BlockDiagram

- Bases: none
- Summary: Diagram

### Methods

- `copy(self)`
  Summary: Deep copy of the block diagram
- `add_node(self, name, x, y, tpe, device_uid, api_object_name, state_ins, state_outs, algeb_ins, algeb_outs, color, subdiagram)`
  Summary: :param api_object_name:
- `add_branch(self, connectionitem_uid, device_uid_from, device_uid_to, port_number_from, port_number_to, color, elbow_points)`
  Summary: :param connectionitem_uid:
- `get_node_data_dict(self)`
  Summary: :return:
- `get_con_data_dict(self)`
  Summary: :return:
- `to_dict(self)`
  Summary: to dictionary function
- `parse(self, data)`
  Summary: :param data:
- `parse_nodes(self, nodes_data)`
  Summary: Parse node data from dictionary
- `parse_branches(self, con_data)`
  Summary: Parse connection data from dictionary
