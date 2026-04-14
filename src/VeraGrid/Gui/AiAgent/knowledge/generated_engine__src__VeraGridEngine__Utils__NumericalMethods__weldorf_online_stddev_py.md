# VeraGridEngine Module: src/VeraGridEngine/Utils/NumericalMethods/weldorf_online_stddev.py

- Original source path: `src/VeraGridEngine/Utils/NumericalMethods/weldorf_online_stddev.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 2
- Representative imports: numpy, numba, VeraGridEngine.basic_structures

## Function: update(i, new_value, count, mean, M2)

:param i:

## Function: finalize(count, variance, M2, std_dev, sample_variance)

:param count:

## Class: WeldorfOnlineStdDevMat

- Bases: none
- Summary: Weldorf's algorithm for online computation of the variance

### Methods

- `update(self, t, new_value)`
  Summary: For a new value new_value, compute the new count, new mean, the new M2.
- `finalize(self)`
  Summary: Finalize: compute the variance and std dev
