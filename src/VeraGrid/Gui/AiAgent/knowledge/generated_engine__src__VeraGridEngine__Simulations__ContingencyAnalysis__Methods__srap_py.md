# VeraGridEngine Module: src/VeraGridEngine/Simulations/ContingencyAnalysis/Methods/srap.py

- Original source path: `src/VeraGridEngine/Simulations/ContingencyAnalysis/Methods/srap.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 4
- Representative imports: numpy, numba, typing, VeraGridEngine.basic_structures

## Function: get_valid_negatives(sensitivities, p_available)

:param sensitivities:

## Function: get_valid_positives(sensitivities, p_available)

:param sensitivities:

## Function: vector_sum_used_power_srap(p_available3, sensitivities3, max_srap_power)

:param p_available3:

## Function: vector_sum_srap(p_available3, sensitivities3, srap_pmax_mw)

:param p_available3:

## Class: BusesForSrap

- Bases: none
- Summary: Buses information for SRAP over a particular branch

### Methods

- `is_solvable(self, c_flow, rating, srap_pmax_mw, available_power, srap_used_power, branch_idx, top_n)`
  Summary: Get the maximum amount of power (MW) to dispatch using SRAP
