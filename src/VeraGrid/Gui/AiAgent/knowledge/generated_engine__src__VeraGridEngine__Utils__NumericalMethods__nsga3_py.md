# VeraGridEngine Module: src/VeraGridEngine/Utils/NumericalMethods/nsga3.py

- Original source path: `src/VeraGridEngine/Utils/NumericalMethods/nsga3.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 12
- Representative imports: numpy, math, typing, VeraGridEngine.Utils.NumericalMethods.non_dominated_sorting

## Function: objective_1(x)

:param x:

## Function: objective_2(x)

:param x:

## Function: initialize_population(pop_size, bounds)

:param pop_size:

## Function: evaluate_population(population)

:param population:

## Function: tournament_selection(population, objectives, k)

:param population:

## Function: crossover(parent1, parent2, crossover_rate)

:param parent1:

## Function: mutation(individual, bounds, mutation_rate)

:param individual:

## Function: generate_recursive(dim, left, total, result, current, index)

:param dim:

## Function: generate_reference_points(n_obj, n_partitions)

:param n_obj:

## Function: associate_to_reference_points(front, ref_points)

:param front:

## Function: niching(front, ref_points, pop_size)

:param front:

## Function: nsga3(n_obj, pop_size, generations, n_partitions, bounds)

:param n_obj:
