# VeraGridEngine Module: src/VeraGridEngine/Devices/Dynamic/var_factory.py

- Original source path: `src/VeraGridEngine/Devices/Dynamic/var_factory.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, typing, VeraGridEngine, VeraGridEngine.Devices.Parents.editable_device, VeraGridEngine.enumerations, VeraGridEngine.Utils.Symbolic.symbolic

## Class: VarFactory

- Bases: EditableDevice
- Summary: VarFactory

### Methods

- `vars_info(self)`
  Summary: No docstring provided.
- `get_vars_to_save(self, dev, names)`
  Summary: this function returns a list of variables which names are in names
- `add_var(self, name, reference, network_conn, uid, diff_var, base_var)`
  Summary: Adds a ver to the class
- `get_var(self, uid)`
  Summary: Gets a Var from the class
- `add_diff_var(self, name, reference, network_conn, uid, diff_var, base_var)`
  Summary: Adds a Diff ver to the class
- `get_diff_var(self, uid)`
  Summary: Gets a Diff Var from the class
- `add_const(self, value, uid, name)`
  Summary: Adds a Cont to the class
- `get_const(self, uid)`
  Summary: Gets a Cont from the class
- `get_const_dict(self)`
  Summary: :return:
- `get_vars_dict(self)`
  Summary: :return:
- `get_diff_var_dict(self)`
  Summary: :return:
- `parse_const_dict(self, data_list)`
  Summary: :param data_list:
- `parse_var_dict(self, data_list)`
  Summary: :param data_list:
- `parse_diff_var_dict(self, data_list)`
  Summary: :param data_list:
- `register_var(self, dev, var)`
  Summary: Associate a variable with a device
