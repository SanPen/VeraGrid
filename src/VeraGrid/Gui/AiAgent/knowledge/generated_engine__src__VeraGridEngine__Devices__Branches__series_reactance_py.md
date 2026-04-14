# VeraGridEngine Module: src/VeraGridEngine/Devices/Branches/series_reactance.py

- Original source path: `src/VeraGridEngine/Devices/Branches/series_reactance.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: numpy, typing, VeraGridEngine.basic_structures, VeraGridEngine.Devices.Substation.bus, VeraGridEngine.enumerations, VeraGridEngine.Devices.Parents.branch_parent,  VeraGridEngine.Devices.Parents.editable_device

## Class: SeriesReactance

- Bases: BranchParent
- Summary: No docstring provided.

### Methods

- `R_corrected(self)`
  Summary: Returns a temperature corrected resistance based on a formula provided by:
- `change_base(self, Sbase_old, Sbase_new)`
  Summary: Change the impedance base
- `get_weight(self)`
  Summary: Get a weight of this line for graph purposes
- `fix_inconsistencies(self, logger)`
  Summary: Fix the inconsistencies
- `fill_design_properties(self, r_ohm, x_ohm, length, Imax, Sbase)`
  Summary: Fill R, X, B from not-in-per-unit parameters
- `R(self)`
  Summary: Get ``R``.
- `R(self, val)`
  Summary: Set ``R``.
- `X(self)`
  Summary: Get ``X``.
- `X(self, val)`
  Summary: Set ``X``.
- `R0(self)`
  Summary: Get ``R0``.
- `R0(self, val)`
  Summary: Set ``R0``.
- `X0(self)`
  Summary: Get ``X0``.
- `X0(self, val)`
  Summary: Set ``X0``.
- `R2(self)`
  Summary: Get ``R2``.
- `R2(self, val)`
  Summary: Set ``R2``.
- `X2(self)`
  Summary: Get ``X2``.
- `X2(self, val)`
  Summary: Set ``X2``.
- `tolerance(self)`
  Summary: Get ``tolerance``.
- `tolerance(self, val)`
  Summary: Set ``tolerance``.
- `r_fault(self)`
  Summary: Get ``r_fault``.
- `r_fault(self, val)`
  Summary: Set ``r_fault``.
- `x_fault(self)`
  Summary: Get ``x_fault``.
- `x_fault(self, val)`
  Summary: Set ``x_fault``.
- `fault_pos(self)`
  Summary: Get ``fault_pos``.
- `fault_pos(self, val)`
  Summary: Set ``fault_pos``.
