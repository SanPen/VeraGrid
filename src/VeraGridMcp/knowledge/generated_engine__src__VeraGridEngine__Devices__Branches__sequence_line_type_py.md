# VeraGridEngine Module: src/VeraGridEngine/Devices/Branches/sequence_line_type.py

- Original source path: `src/VeraGridEngine/Devices/Branches/sequence_line_type.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 2
- Representative imports: typing, numpy, VeraGridEngine.Devices.admittance_matrix, VeraGridEngine.Devices.Parents.editable_device, VeraGridEngine.Devices.Parents.dynamic_parent, VeraGridEngine.basic_structures

## Function: get_line_impedances_with_c(r_ohm, x_ohm, c_nf, length, Imax, freq, Sbase, Vnom, logger, decimals_rounding)

Fill R, X, B from not-in-per-unit parameters

## Function: get_line_impedances_with_b(r_ohm, x_ohm, b_us, length, Imax, Sbase, Vnom, logger, decimals_rounding)

Fill R, X, B from not-in-per-unit parameters

## Class: SequenceLineType

- Bases: DynamicDevice
- Summary: No docstring provided.

### Methods

- `get_values(self, Sbase, freq, length, line_Vnom, logger, decimals_rounding)`
  Summary: Get the per-unit values
- `get_ys_nabc(self)`
  Summary: Get the series 3x3 admittance matrix
- `get_ysh_nabc(self)`
  Summary: get the 3x3 shunt admittance matrix from the sequence values
- `Imax(self)`
  Summary: Get ``Imax``.
- `Imax(self, val)`
  Summary: Set ``Imax``.
- `Vnom(self)`
  Summary: Get ``Vnom``.
- `Vnom(self, val)`
  Summary: Set ``Vnom``.
- `R(self)`
  Summary: Get ``R``.
- `R(self, val)`
  Summary: Set ``R``.
- `X(self)`
  Summary: Get ``X``.
- `X(self, val)`
  Summary: Set ``X``.
- `B(self)`
  Summary: Get ``B``.
- `B(self, val)`
  Summary: Set ``B``.
- `R0(self)`
  Summary: Get ``R0``.
- `R0(self, val)`
  Summary: Set ``R0``.
- `X0(self)`
  Summary: Get ``X0``.
- `X0(self, val)`
  Summary: Set ``X0``.
- `B0(self)`
  Summary: Get ``B0``.
- `B0(self, val)`
  Summary: Set ``B0``.
- `Cnf(self)`
  Summary: Get ``Cnf``.
- `Cnf(self, val)`
  Summary: Set ``Cnf``.
- `Cnf0(self)`
  Summary: Get ``Cnf0``.
- `Cnf0(self, val)`
  Summary: Set ``Cnf0``.
- `use_conductance(self)`
  Summary: Get ``use_conductance``.
- `use_conductance(self, val)`
  Summary: Set ``use_conductance``.
- `n_circuits(self)`
  Summary: Get ``n_circuits``.
- `n_circuits(self, val)`
  Summary: Set ``n_circuits``.
- `capex(self)`
  Summary: Get ``capex``.
- `capex(self, val)`
  Summary: Set ``capex``.
- `opex(self)`
  Summary: Get ``opex``.
- `opex(self, val)`
  Summary: Set ``opex``.
