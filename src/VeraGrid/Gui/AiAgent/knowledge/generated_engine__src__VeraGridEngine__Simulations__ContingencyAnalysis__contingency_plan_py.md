# VeraGridEngine Module: src/VeraGridEngine/Simulations/ContingencyAnalysis/contingency_plan.py

- Original source path: `src/VeraGridEngine/Simulations/ContingencyAnalysis/contingency_plan.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 5
- Representative imports: __future__, itertools, numpy, typing, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Devices.Aggregation.contingency, VeraGridEngine.Devices.Parents.editable_device, VeraGridEngine.Devices.types, VeraGridEngine.enumerations, VeraGridEngine.Devices

## Function: enumerate_states_n_k(m, k)

Enumerates the states to produce the so called N-k failures

## Function: add_n1_contingencies(branches, vmin, vmax, filter_branches_by_voltage, branch_types)

generate N-1 contingencies on branches

## Function: add_n2_contingencies(branches, vmin, vmax, filter_branches_by_voltage, branch_types)

Generate N-2 contingencies for branches

## Function: add_generator_contingencies(generators, pmin, pmax, contingency_perc, filter_injections_by_power)

Create generator contingencies

## Function: generate_automatic_contingency_plan(grid, k, consider_branches, filter_branches_by_voltage, vmin, vmax, branch_types, consider_injections, filter_injections_by_power, contingency_perc, pmin, pmax, injection_types)

:param grid: MultiCircuit instance
