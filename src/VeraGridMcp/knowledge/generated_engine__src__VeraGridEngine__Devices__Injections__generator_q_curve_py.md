# VeraGridEngine Module: src/VeraGridEngine/Devices/Injections/generator_q_curve.py

- Original source path: `src/VeraGridEngine/Devices/Injections/generator_q_curve.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: json, numpy, typing, matplotlib, VeraGridEngine.basic_structures

## Class: GeneratorQCurve

- Bases: none
- Summary: GeneratorQCurve

### Methods

- `get_data(self)`
  Summary: Get the data
- `get_data_by_type(self)`
  Summary: Get the data points P, Qmin, Qmax
- `make_default_q_curve(self, Snom, Qmin, Qmax, n)`
  Summary: Compute the theoretical generator capability curve
- `get_q_limits(self, p)`
  Summary: Get the reactive power limits
- `get_qmax(self, p)`
  Summary: Get Qmax
- `get_qmin(self, p)`
  Summary: Get Qmin
- `to_list(self)`
  Summary: Get list of points
- `str(self)`
  Summary: Get string representation of the curve
- `parse(self, data)`
  Summary: Parse Json data
- `set(self, data)`
  Summary: Parse Json data
- `get_Qmin(self)`
  Summary: No docstring provided.
- `get_Qmax(self)`
  Summary: No docstring provided.
- `get_Pmin(self)`
  Summary: No docstring provided.
- `get_Pmax(self)`
  Summary: No docstring provided.
- `get_Snom(self)`
  Summary: No docstring provided.
- `plot(self, ax)`
  Summary: :param ax:
- `copy(self)`
  Summary: No docstring provided.
