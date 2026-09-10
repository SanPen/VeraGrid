# VeraGridEngine Module: src/VeraGridEngine/IO/iidm/devices/iidm_object.py

- Original source path: `src/VeraGridEngine/IO/iidm/devices/iidm_object.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: uuid, typing, VeraGridEngine.IO.base.units, VeraGridEngine.IO.base.base_property

## Class: IidmObject

- Bases: none
- Summary: RteObject

### Methods

- `get_rdfid(self)`
  Summary: Convert the idtag to RDFID
- `get_properties(self)`
  Summary: Get list of properties
- `get_prop_value(self, prop)`
  Summary: Get property value
- `register_property(self, property_name, class_type, unit, denominator_unit, description, max_chars, min_value, max_value)`
  Summary: Register property of this object
