# VeraGridEngine Module: src/VeraGridEngine/Simulations/OPF/simple_dispatch_ts.py

- Original source path: `src/VeraGridEngine/Simulations/OPF/simple_dispatch_ts.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

This file implements a DC-OPF for time series

## Module Surface

- Class count: 2
- Top-level function count: 4
- Representative imports: numpy, numba, typing, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.basic_structures

## Function: run_simple_dispatch(grid, text_prog, prog_func)

Simple generation dispatch for the snapshot

## Function: greedy_dispatch(load_profile, gen_profile, gen_p_max, gen_p_min, gen_dispatchable, gen_active, gen_cost, batt_active, batt_p_max_charge, batt_p_max_discharge, batt_energy_max, batt_eff_charge, batt_eff_discharge, batt_cost, batt_soc0, batt_soc_min, dt, force_charge_if_low, tol)

Greedy dispatch algorithm with dispatchable and non-dispatchable (e.g., renewable) generators.

## Function: greedy_dispatch2(load_profile, gen_profile, gen_p_max, gen_p_min, gen_dispatchable, gen_active, gen_cost, batt_active, batt_p_max_charge, batt_p_max_discharge, batt_energy_max, batt_eff_charge, batt_eff_discharge, batt_cost, batt_soc0, batt_soc_min, dt, force_charge_if_low, tol)

Greedy dispatch algorithm with dispatchable and non-dispatchable (e.g., renewable) generators.

## Class: GreedyDispatchInputs

- Bases: none
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: GreedyDispatchInputsSnapshot

- Bases: none
- Summary: No docstring provided.

### Methods

- No methods detected.

## Function: run_greedy_dispatch_ts(grid, time_indices, logger, text_prog, prog_func)

Run a simple (greedy) dispatch
