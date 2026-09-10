# VeraGridEngine Module: src/VeraGridEngine/Utils/MIP/SimpleMip/lpobjects.py

- Original source path: `src/VeraGridEngine/Utils/MIP/SimpleMip/lpobjects.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 3
- Top-level function count: 0
- Representative imports: __future__, typing, uuid

## Class: LpVar

- Bases: none
- Summary: Variable

### Methods

- `set_index(self, index)`
  Summary: Set the internal indexing
- `get_index(self)`
  Summary: Get the internal indexing
- `copy(self)`
  Summary: Make a deep copy of this variable
- `_comparison(self, sense, other)`
  Summary: No docstring provided.

## Class: LpCst

- Bases: none
- Summary: Constraint

### Methods

- `terms(self)`
  Summary: Terms property of the linear expression
- `copy(self)`
  Summary: Make a deep copy of this constraint
- `get_rhs(self)`
  Summary: get the final right-hand side
- `get_bounds(self)`
  Summary: Get the constraint bounds
- `set_index(self, index)`
  Summary: Set the internal indexing
- `get_index(self)`
  Summary: Get internal index
- `add_term(self, var, coeff)`
  Summary: Add a term to the constraint
- `add_var(self, var)`
  Summary: Add a term to the constraint

## Class: LpExp

- Bases: none
- Summary: Expression

### Methods

- `copy(self)`
  Summary: Make a deep copy of this expression
- `_comparison(self, sense, other)`
  Summary: No docstring provided.
