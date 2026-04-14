# VeraGridEngine Module: src/VeraGridEngine/IO/raw/devices/psse_object.py

- Original source path: `src/VeraGridEngine/IO/raw/devices/psse_object.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 2
- Representative imports: hashlib, uuid, typing, VeraGridEngine.IO.base.units, VeraGridEngine.IO.raw.devices.psse_property

## Function: uuid_from_seed(seed)

:param seed:

## Function: format_raw_float(value)

Format a float in engineering notation with 5 decimals.

## Class: RawObjectMeta

- Bases: type
- Summary: Metaclass that builds RAW property schema per class from class-level declarations.

### Methods

- No methods detected.

## Class: RawObject

- Bases: none
- Summary: PSSeObject

### Methods

- `get_rdfid(self)`
  Summary: Convert the idtag to RDFID
- `get_properties(self)`
  Summary: Get list of properties
- `get_prop_value(self, prop)`
  Summary: Get property value
- `get_rawx_dict(self)`
  Summary: Get the RAWX property dictionary
- `register_property(self, property_name, rawx_key, class_type, unit, denominator_unit, description, max_chars, min_value, max_value, format_rule)`
  Summary: Register property of this object
- `format_raw_line_prop(self, props)`
  Summary: Format a list of property names
- `extend_or_curtail(data, n)`
  Summary: Extends of curtails the input so that it marches what's expected
- `format_raw_line(self, props)`
  Summary: Format a list of values
- `get_raw_line(self, version)`
  Summary: Get raw line
- `get_id(self)`
  Summary: Get a PSSe ID
- `get_seed(self)`
  Summary: Get seed ID
- `get_uuid5(self)`
  Summary: Generate UUID with the seed given by get_id()
- `try_parse(self, values)`
  Summary: Copy *values* into this object following _ATTR_ORDER.
- `try_parse2(self, values, prop_names)`
  Summary: Copy *values* into this object following _ATTR_ORDER.
