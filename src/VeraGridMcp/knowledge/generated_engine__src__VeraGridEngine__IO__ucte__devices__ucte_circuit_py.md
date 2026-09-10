# VeraGridEngine Module: src/VeraGridEngine/IO/ucte/devices/ucte_circuit.py

- Original source path: `src/VeraGridEngine/IO/ucte/devices/ucte_circuit.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, typing, VeraGridEngine.IO.ucte.devices.ucte_node, VeraGridEngine.IO.ucte.devices.ucte_comment, VeraGridEngine.IO.ucte.devices.ucte_line, VeraGridEngine.IO.ucte.devices.ucte_transformer, VeraGridEngine.IO.ucte.devices.ucte_transformer_regulation, VeraGridEngine.IO.ucte.devices.ucte_transformer_tap_table, VeraGridEngine.IO.ucte.devices.ucte_exchange_power, VeraGridEngine.basic_structures

## Class: UcteCircuit

- Bases: none
- Summary: UCTE circuit class

### Methods

- `check_file_extension(f_name)`
  Summary: Check that file extension is ok
- `parse_file(self, files, logger)`
  Summary: parse a list of UCTE files
- `normalize(self, logger)`
  Summary: Normalize optional data after parsing.
- `get_transformer_regulation(self, elm)`
  Summary: :param elm:
- `get_transformers_tap_table(self, elm)`
  Summary: :param elm:
- `summary(self)`
  Summary: Print grid summary
- `fuse_comments(self)`
  Summary: fuse comments as one
