# VeraGridEngine Module: src/VeraGridEngine/Simulations/Reliability/reliability.py

- Original source path: `src/VeraGridEngine/Simulations/Reliability/reliability.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 7
- Representative imports: typing, numba, numpy, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.enumerations, VeraGridEngine.Simulations.OPF.simple_dispatch_ts, VeraGridEngine.basic_structures, VeraGridEngine

## Function: compose_states(mttf, mttr, horizon, initially_working)

Compose random states vector (on -> off -> on -> ...)

## Function: generate_states_matrix(mttf, mttr, horizon, initially_working)

Generate random states vector (on -> off -> on -> ...)

## Function: find_different_states(mat1, mat2)

Find different states

## Function: find_time_blocks(horizon, all_actives)

Get the contigous time blocks of failure

## Function: compute_loss_of_load_because_of_lack_of_generation(gen_pmax, load, dt)

Compute the loss of load because of lack of generation

## Function: reliability_simulation(n_sim, load_profile, gen_profile, gen_p_max, gen_p_min, gen_dispatchable, gen_active, gen_cost, gen_mttf, gen_mttr, batt_active, batt_p_max_charge, batt_p_max_discharge, batt_energy_max, batt_eff_charge, batt_eff_discharge, batt_cost, batt_soc0, batt_soc_min, dt, force_charge_if_low, tol)

:param n_sim:

## Function: reliability_grid_simulation(nc, grid, n_sim, branch_mttf, branch_mttr, dt, tol)

:param n_sim:
