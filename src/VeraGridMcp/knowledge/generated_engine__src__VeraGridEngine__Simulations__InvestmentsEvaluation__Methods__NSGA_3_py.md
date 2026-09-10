# VeraGridEngine Module: src/VeraGridEngine/Simulations/InvestmentsEvaluation/Methods/NSGA_3.py

- Original source path: `src/VeraGridEngine/Simulations/InvestmentsEvaluation/Methods/NSGA_3.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 7
- Top-level function count: 1
- Representative imports: numpy, pymoo.core.problem, pymoo.util.ref_dirs, pymoo.optimize, pymoo.algorithms.moo.nsga3, pymoo.operators.crossover.sbx, pymoo.operators.repair.rounding, pymoo.core.mixed, pymoo.core.sampling, pymoo.operators.sampling.rnd, pymoo.core.mutation, VeraGridEngine.basic_structures

## Class: IntegerRandomSamplingVeraGrid

- Bases: Sampling
- Summary: No docstring provided.

### Methods

- `_do(self, problem, n_samples, **kwargs)`
  Summary: No docstring provided.

## Class: UniformBinarySampling

- Bases: Sampling
- Summary: UniformBinarySampling

### Methods

- `_do(self, problem, n_samples, **kwargs)`
  Summary: No docstring provided.

## Class: SkewedBinarySampling

- Bases: Sampling
- Summary: SkewedBinarySampling

### Methods

- `_do(self, problem, n_samples, **kwargs)`
  Summary: No docstring provided.

## Class: SkewedIntegerSamplingRange

- Bases: Sampling
- Summary: SkewedIntegerSampling generates samples skewed toward the lower bounds

### Methods

- `_do(self, problem, n_samples, **kwargs)`
  Summary: No docstring provided.

## Class: QuadBinarySampling

- Bases: Sampling
- Summary: QuadBinarySampling

### Methods

- `_do(self, problem, n_samples, **kwargs)`
  Summary: No docstring provided.

## Class: BitflipMutation

- Bases: Mutation
- Summary: BitflipMutation

### Methods

- `_do(self, problem, x, **kwargs)`
  Summary: No docstring provided.

## Class: GridNsga

- Bases: ElementwiseProblem
- Summary: Problem formulation packaging to use the pymoo library

### Methods

- `_evaluate(self, x, out, *args, **kwargs)`
  Summary: :param x:

## Function: NSGA_3(obj_func, n_var, lb, ub, n_obj, n_partitions, max_evals, pop_size, crossover_prob, mutation_probability, eta)

NSGA3 designed for pareto investments
