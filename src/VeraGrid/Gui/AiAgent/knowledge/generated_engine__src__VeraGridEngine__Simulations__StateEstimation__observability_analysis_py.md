# VeraGridEngine Module: src/VeraGridEngine/Simulations/StateEstimation/observability_analysis.py

- Original source path: `src/VeraGridEngine/Simulations/StateEstimation/observability_analysis.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 9
- Representative imports: __future__, numpy, matplotlib, scipy.sparse, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.Simulations.StateEstimation.pseudo_measurements_augmentation, VeraGridEngine.Simulations.StateEstimation.state_estimation_inputs, VeraGridEngine.basic_structures, VeraGridEngine.Simulations.StateEstimation.state_estimation, collections, concurrent.futures, multiprocessing

## Function: check_for_observability_and_return_unobservable_buses(nc, Ybus, Yf, Yt, no_slack, F, T, Cf, Ct, se_input, fixed_slack, tolerance_for_observability_score, do_profiling_of_measurements, include_line_measurements_on_both_ends, logger)

Fast decoupled WLS state estimator using LU decomposition based observability analysis

## Function: parallel_measurement_profiling(Ha, Hr, Hv, Hi, measurement_ids, a_idx, r_idx, v_idx, i_idx, include_line_measurements_on_both_ends)

Parallel execution of all 4 measurement profiling strategies.

## Function: add_pseudo_measurements_for_unobservable_buses(bus_dict, unobservable_buses, se_input, V, Ybus, Cf, Ct, sigma_pseudo_meas_value, Sbase, logger)

Full preprocessing: detect unobservable buses and add pseudo-measurements

## Function: profile_measurements(Hsub, ids, tol, include_line_measurements_on_both_ends)

Condition               System rank             Local rank              Classification

## Function: profile_measurements_ultrafast(Hsub, ids, tol, include_line_measurements_on_both_ends)

Ultra-fast version with identical results to original.

## Function: build_local_groups(measurement_ids, include_line_measurements_on_both_ends)

No docstring provided.

## Function: bus_observability_profile(measurement_profile)

Convert measurement_profile (from profile_measurements) into a nested dict:

## Function: plot_bus_observability(bus_status_per_type)

bus_status_per_type: dict of dicts

## Function: classify_redundancy(H, idx, tol)

Classify redundant measurement into none/single/multiple redundancy.
