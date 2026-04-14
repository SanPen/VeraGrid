# VeraGridEngine Module: src/VeraGridEngine/IO/raw/devices/transformer.py

- Original source path: `src/VeraGridEngine/IO/raw/devices/transformer.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: typing, VeraGridEngine.IO.base.units, VeraGridEngine.IO.raw.devices.psse_object, VeraGridEngine.basic_structures, numpy, VeraGridEngine.IO.raw.devices.psse_property

## Class: RawTransformer

- Bases: RawObject
- Summary: No docstring provided.

### Methods

- `parse(self, data, version, logger)`
  Summary: :param data:
- `get_raw_line(self, version)`
  Summary: :param version:
- `get_id(self)`
  Summary: No docstring provided.
- `get_2w_pu_impedances(self, Sbase, v_bus_i, v_bus_j)`
  Summary: Get the 2-winding impedances if this is a 2-winding transformer
