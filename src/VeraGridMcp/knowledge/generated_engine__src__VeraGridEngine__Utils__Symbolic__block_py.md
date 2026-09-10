# VeraGridEngine Module: src/VeraGridEngine/Utils/Symbolic/block.py

- Original source path: `src/VeraGridEngine/Utils/Symbolic/block.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 2
- Representative imports: __future__, uuid, typing, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.Devices.Diagrams.block_diagram, VeraGridEngine.enumerations

## Function: _new_uid()

Generate a fresh UUID‑v4 string.

## Class: Block

- Bases: none
- Summary: Class representing a Block

### Methods

- `diagram(self)`
  Summary: :return:
- `diagram(self, val)`
  Summary: No docstring provided.
- `to_dict(self)`
  Summary: Get dictionary representation of this block
- `parse(data)`
  Summary: Parse the dictionary representation of a block
- `copy(self)`
  Summary: Deep copy preserving UIDs.
- `_procedural_logic_to_dict(self)`
  Summary: Serialize block-attached procedural logic.
- `_procedural_logic_from_dict(data)`
  Summary: Deserialize block-attached procedural logic.
- `compare(self, block2)`
  Summary: Compare two blocks.
- `set_parameter_in_model(self, var_name, new_value)`
  Summary: updates parameter value given a name and a value
- `check_empty(self)`
  Summary: check if a block is an empty block
- `empty(self)`
  Summary: check if a model is empty
- `E(self, d)`
  Summary: returns the value of the external mapping corresponding to the VarPowerFlowReferenceType
- `V(self, d)`
  Summary: :param d:
- `add(self, val)`
  Summary: Add another block to children of the model
- `remove(self, val)`
  Summary: Remove a block from block children
- `check_valid_init_method(self)`
  Summary: No docstring provided.
- `get_all_blocks(self)`
  Summary: Depth-first collection of all *primitive* Blocks.
- `merge_incoming_block(self, block)`
  Summary: No docstring provided.
- `unify_blocks(self)`
  Summary: This function collects all variables and equations of a block, returns a flat block
- `get_vars(self)`
  Summary: returns variables of the flat block
- `get_all_vars(self)`
  Summary: returns all the variables of a block
- `update_variables(self, old, new)`
  Summary: this function changes the variable old for the variable new in the block variables
- `update_equations(self, old, new)`
  Summary: this function changes the variable old for the variable new in the block equations
- `update_model(self, old, new)`
  Summary: <
- `connect(self, vars_to_subs, incoming_vars)`
  Summary: Function to connect two blocks by variables sharing

## Function: find_name_in_block(name, block)

No docstring provided.
