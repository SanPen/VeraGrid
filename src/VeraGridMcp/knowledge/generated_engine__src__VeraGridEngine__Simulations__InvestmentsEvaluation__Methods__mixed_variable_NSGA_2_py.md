# VeraGridEngine Module: src/VeraGridEngine/Simulations/InvestmentsEvaluation/Methods/mixed_variable_NSGA_2.py

- Original source path: `src/VeraGridEngine/Simulations/InvestmentsEvaluation/Methods/mixed_variable_NSGA_2.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 1
- Representative imports: typing, pymoo.core.mixed, pymoo.algorithms.moo.nsga2, pymoo.core.mixed, pymoo.optimize, pymoo.core.problem, pymoo.core.variable, VeraGridEngine.Devices.Aggregation.investment, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Devices.Branches.transformer, VeraGridEngine.Devices.Branches.line, VeraGridEngine.Devices.types, VeraGridEngine.enumerations, VeraGridEngine.basic_structures

## Class: MixedVariableProblem

- Bases: ElementwiseProblem
- Summary: Problem formulation packaging to use the pymoo library

### Methods

- `_evaluate(self, x, out, *args, **kwargs)`
  Summary: :param x:

## Function: NSGA_2(grid, obj_func, n_obj, max_evals, pop_size)

:param obj_func:
