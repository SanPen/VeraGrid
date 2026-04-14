# VeraGridEngine Module: src/VeraGridEngine/Devices/admittance_matrix.py

- Original source path: `src/VeraGridEngine/Devices/admittance_matrix.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 1
- Representative imports: __future__, typing, numpy, VeraGridEngine.basic_structures

## Function: list_to_matrix(data, size)

Attempts converting a list of lists to matrix

## Class: AdmittanceMatrix

- Bases: none
- Summary: This is the admittance matrix to store the three-phases admittance of a branch

### Methods

- `copy(self)`
  Summary: Make a copy of the admittance matrix
- `phN(self)`
  Summary: :return:
- `phN(self, val)`
  Summary: No docstring provided.
- `phA(self)`
  Summary: :return:
- `phA(self, val)`
  Summary: No docstring provided.
- `phB(self)`
  Summary: No docstring provided.
- `phB(self, val)`
  Summary: No docstring provided.
- `phC(self)`
  Summary: No docstring provided.
- `phC(self, val)`
  Summary: No docstring provided.
- `size(self)`
  Summary: No docstring provided.
- `size(self, size)`
  Summary: No docstring provided.
- `values(self)`
  Summary: No docstring provided.
- `values(self, value)`
  Summary: No docstring provided.
- `to_dict(self)`
  Summary: Get a dictionary representation of the tap
- `parse(self, data)`
  Summary: Parse the tap data
