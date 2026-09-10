# VeraGridEngine Module: src/VeraGridEngine/Devices/Associations/association.py

- Original source path: `src/VeraGridEngine/Devices/Associations/association.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 0
- Representative imports: __future__, typing, VeraGridEngine.enumerations, VeraGridEngine.basic_structures

## Class: Association

- Bases: none
- Summary: VeraGrid relationship object, this handles the unit of association

### Methods

- `to_dict(self)`
  Summary: :return:
- `parse(self, data, elements_dict)`
  Summary: :param data:
- `copy(self)`
  Summary: copy

## Class: Associations

- Bases: none
- Summary: VeraGrid associations object, this handles a set of associations

### Methods

- `data(self)`
  Summary: :return:
- `device_type(self)`
  Summary: Device Type
- `device_type(self, value)`
  Summary: Set the device type of the association, as needed in empty investments
- `add(self, val)`
  Summary: Add Association
- `add_object(self, api_object, val)`
  Summary: Add association
- `remove(self, val)`
  Summary: Remove Association
- `remove_by_key(self, key)`
  Summary: Remove Association by key
- `at_key(self, key)`
  Summary: Remove Association by key
- `to_dict(self)`
  Summary: Get dictionary representation of Associations
- `to_list(self)`
  Summary: Get a list of the associated api objects
- `parse(self, data, elements_dict, logger, elm_name, updatable_device_type)`
  Summary: Parse the data generated with to_dict()
- `append(self, item)`
  Summary: Add item
- `clear(self)`
  Summary: Clear data
- `copy(self)`
  Summary: Copy data
