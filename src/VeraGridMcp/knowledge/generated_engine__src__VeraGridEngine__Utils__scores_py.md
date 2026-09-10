# VeraGridEngine Module: src/VeraGridEngine/Utils/scores.py

- Original source path: `src/VeraGridEngine/Utils/scores.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 3
- Representative imports: numpy, numba, typing, VeraGridEngine.basic_structures

## Function: get_overload_score(loading, branches_cost, threshold)

Compute overload score by multiplying the loadings above 100% by the associated branch cost.

## Function: get_voltage_module_score(voltage, vm_cost, vm_max, vm_min)

Compute voltage module score by multiplying the voltages outside limits by the associated bus costs.

## Function: get_voltage_phase_score(voltage, va_cost, va_max, va_min)

Compute voltage phase score by multiplying the phases outside limits by the associated bus costs.

## Class: TechnoEconomicScores

- Bases: none
- Summary: InvestmentScores

### Methods

- `financial_score(self)`
  Summary: Get the financial score: CAPEX + OPEX
- `tech_score(self)`
  Summary: No docstring provided.
- `arr(self)`
  Summary: Return multidimensional metrics for the optimization
