# VeraGridEngine Module: src/VeraGridEngine/IO/cim/cgmes/base.py

- Original source path: `src/VeraGridEngine/IO/cim/cgmes/base.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 5
- Representative imports: typing, uuid, VeraGridEngine.IO.cim.cgmes.cgmes_property, VeraGridEngine.IO.cim.cgmes.cgmes_enums, VeraGridEngine.IO.base.units, VeraGridEngine.data_logger

## Function: str2num(val)

Try to convert to number, else keep as string

## Function: index_find(string, start, end)

version of substring that matches

## Function: get_new_rdfid()

:return:

## Function: rfid2uuid(val)

:param val:

## Function: form_rdfid(idtag)

Converts a simple string, eg. idtag (without hyphens or underscores)

## Class: Base

- Bases: none
- Summary: Base

### Methods

- `can_keep(self)`
  Summary: Can I keep this object?
- `has_references(self)`
  Summary: Determine if there are references to this object
- `parse_dict(self, data, logger)`
  Summary: :param data:
- `store_parsed_property_value(self, prop_name, prop_value)`
  Summary: Store one raw parsed property value on a declared attribute slot.
- `set_declared_property_value(self, prop_name, prop_value)`
  Summary: Store one value into a declared CGMES property.
- `get_declared_property_value(self, prop_name)`
  Summary: Read one declared CGMES property value.
- `get_declared_property_names(self)`
  Summary: Get the declared CGMES property names for the concrete class.
- `get_declared_property_map(self)`
  Summary: Build a dictionary with the declared property values of the object.
- `check(self, logger)`
  Summary: Check specific OCL rules
- `add_reference(self, obj, attr_name, logger)`
  Summary: Adds a categorized reference to this object
- `register_property(self, name, class_type, multiplier, unit, description, max_chars, mandatory, comment, out_of_the_standard, profiles)`
  Summary: Disabled runtime API. Use class-level LOCAL_CGMES_PROPERTIES declarations.
- `get_properties(self)`
  Summary: No docstring provided.
- `get_xml(self, level, profiles)`
  Summary: Returns an XML representation of the object
- `get_dict(self)`
  Summary: Get dictionary with the data
- `get_all_properties(self)`
  Summary: Get the list of properties of this object
- `detect_circular_references(self, visited)`
  Summary: Get path, leading to a circular reference
