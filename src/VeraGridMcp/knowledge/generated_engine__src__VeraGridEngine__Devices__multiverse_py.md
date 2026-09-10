# VeraGridEngine Module: src/VeraGridEngine/Devices/multiverse.py

- Original source path: `src/VeraGridEngine/Devices/multiverse.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 0
- Representative imports: __future__, copy, typing, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.enumerations

## Class: ScenarioNode

- Bases: none
- Summary: No docstring provided.

### Methods

- `get_drivers_to_save(self)`
  Summary: No docstring provided.
- `append_child(self, child)`
  Summary: :param child:
- `insert_child(self, position, child)`
  Summary: :param position:
- `remove_child(self, child)`
  Summary: :param child:
- `remove_child_at(self, position)`
  Summary: :param position:
- `child(self, row)`
  Summary: :param row:
- `child_count(self)`
  Summary: :return:
- `row(self)`
  Summary: No docstring provided.

## Class: MultiVerse

- Bases: none
- Summary: No docstring provided.

### Methods

- `base_model(self)`
  Summary: No docstring provided.
- `base_model(self, val)`
  Summary: No docstring provided.
- `current_model(self)`
  Summary: No docstring provided.
- `current_model(self, val)`
  Summary: No docstring provided.
- `current_node(self)`
  Summary: No docstring provided.
- `root_nodes(self)`
  Summary: No docstring provided.
- `_generate_id(self)`
  Summary: No docstring provided.
- `checkout(node)`
  Summary: Reconstruct the full MultiCircuit for *node* by replaying its delta chain from the root.
- `_compose_node(self, node)`
  Summary: Return the full scenario represented by *node*.
- `_build_delta_from_composed(self, node, composed)`
  Summary: Convert a fully composed scenario back into the storage representation of *node*.
- `_store_node_circuit_and_diagrams(self, node, stored_circuit)`
  Summary: Persist a node's storage payload and keep node-owned diagrams in sync with it.
- `_store_composed_node_data(self, node, composed)`
  Summary: Persist a fully composed circuit back into the node storage model.
- `_set_active_node(self, node)`
  Summary: Make *node* the active scenario and return the active circuit object.
- `_set_fallback_active_node(self, fallback_node)`
  Summary: Activate a fallback node or clear active state if the tree became empty.
- `commit_current(self)`
  Summary: Persist edits made to the currently active scenario.
- `merge_children_into_parent(self, parent_id)`
  Summary: Merge all direct children into the specified parent node.
- `activate_scenario(self, node_id)`
  Summary: Switch the active scenario to the node identified by *node_id*.
- `create_node(self, data, parent_id, position)`
  Summary: :param data:
- `roots_number(self)`
  Summary: No docstring provided.
- `get_node(self, node_id)`
  Summary: :param node_id:
- `set_node(self, node_id, node)`
  Summary: :param node_id:
- `insert_node(self, position, node)`
  Summary: :param position:
- `exists(self, node_id)`
  Summary: :param node_id:
- `update_node_data(self, node_id, data)`
  Summary: :param node_id:
- `delete_node(self, node_id)`
  Summary: Delete a node and its entire subtree from the multiverse.
- `_delete_from_registry_recursive(self, node)`
  Summary: :param node:
- `move_node(self, node_id, new_parent_id, position)`
  Summary: :param node_id:
- `_is_descendant(self, candidate_parent, candidate_child)`
  Summary: :param candidate_parent:
- `clear(self)`
  Summary: :return:
- `iter_nodes_depth_first(self)`
  Summary: :return:
- `_collect_subtree_depth_first(self, node, result)`
  Summary: :param node:
- `get_sorted_node_data(self)`
  Summary: Deterministic preorder traversal.
- `to_record_list(self)`
  Summary: Export full tree structure as a flat ordered list.
- `get_save_data(self)`
  Summary: :return:
- `parse_json(self, diffs_dict, metadata)`
  Summary: Parse the json metadata to fill this object
