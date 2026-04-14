# VeraGridEngine Module: src/VeraGridEngine/Utils/NumericalMethods/non_dominated_sorting.py

- Original source path: `src/VeraGridEngine/Utils/NumericalMethods/non_dominated_sorting.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 5
- Representative imports: numpy, typing, VeraGridEngine.basic_structures

## Function: dominates(sol_a, sol_b)

Check if a solution dominates another in the Pareto sense

## Function: get_non_dominated_fronts(population)

2D non dominated sorting

## Function: crowding_distance(front, population)

:param front: list of integers representing the positions in the population matrix

## Function: sort_by_crowding(fronts, population)

:param fronts: Fronts ordered by position (front 1, front 2, Front 3, ...)

## Function: non_dominated_sorting(y_values, x_values)

Use non dominated sorting and crowded sorting to sort the multidimensional objectives
