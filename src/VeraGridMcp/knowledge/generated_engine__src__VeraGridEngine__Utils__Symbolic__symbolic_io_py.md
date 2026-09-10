# VeraGridEngine Module: src/VeraGridEngine/Utils/Symbolic/symbolic_io.py

- Original source path: `src/VeraGridEngine/Utils/Symbolic/symbolic_io.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 11
- Representative imports: __future__, typing, VeraGridEngine.Devices.Dynamic.var_factory, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.Utils.Symbolic.block, VeraGridEngine.enumerations

## Function: symbolic_objects_to_dict(obj_dict)

Save the list of all unique vars, diffvars and const

## Function: expr_to_dict(expr, const_dict, var_dict, diff_var_dict)

Serialise any `Expr` tree into a plain Python dictionary that’s

## Function: expr_list_to_list(lst, const_dict, var_dict, diff_var_dict)

:param lst:

## Function: parse_expr(data, const_dict, var_dict, diff_var_dict)

De-Serialize expression from dictionary

## Function: parse_expr_list(lst, const_dict, var_dict, diff_var_dict)

:param lst:

## Class: BlockSaver

- Bases: none
- Summary: No docstring provided.

### Methods

- `get_const_to_save(self)`
  Summary: :return:
- `get_vars_to_save(self)`
  Summary: :return:
- `get_diff_vars_to_save(self)`
  Summary: :return:
- `get_blocks(self)`
  Summary: No docstring provided.
- `save_block(self, blk, main)`
  Summary: Get a dictionary representing the block

## Class: BlockParser

- Bases: none
- Summary: No docstring provided.

### Methods

- `parse_consts(self, data)`
  Summary: :param data:
- `parse_vars(self, data)`
  Summary: :param data:
- `parse_diff_vars(self, data)`
  Summary: :param data:
- `parse_block(self, blocks_data, main_block_uid)`
  Summary: Parse block as

## Function: block_deep_copy(block, var_factory)

Create depp copy of a block

## Function: duplicate_var(var_factory, old_to_new_var, var)

:param var_factory:

## Function: duplicate_const(var_factory, old_to_new_const, const)

:param var_factory:

## Function: duplicate_expr(var_factory, old_to_new_const, old_to_new_var, expr)

:param var_factory:

## Function: duplicate_block(block, var_factory)

Create a duplicate of this block with new variable UIDs.

## Function: compare_blocks(block1, block2, var_factory1, var_factory2, testing)

Create depp copy of a block
