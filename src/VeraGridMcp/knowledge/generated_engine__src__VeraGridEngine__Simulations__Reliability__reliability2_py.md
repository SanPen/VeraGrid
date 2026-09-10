# VeraGridEngine Module: src/VeraGridEngine/Simulations/Reliability/reliability2.py

- Original source path: `src/VeraGridEngine/Simulations/Reliability/reliability2.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 7
- Representative imports: typing, numba, numpy, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.enumerations, VeraGridEngine.basic_structures

## Function: get_transition_probabilities(lbda, mu)

Probability of the component being unavailable

## Function: compute_transition_probabilities(mttf, mttr, forced_mttf, forced_mttr)

Compute the transition probabilities

## Function: get_failure_time(mttf)

Get an array of possible failure times

## Function: get_repair_time(mttr)

Get an array of possible repair times

## Function: get_reliability_events(horizon, mttf, mttr, tpe)

Get random fail-repair events until a given time horizon in hours

## Function: get_reliability_scenario(nc, horizon)

Get reliability events

## Function: run_events(nc, events_list)

:param nc:
