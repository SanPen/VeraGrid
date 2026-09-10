# VeraGridEngine Module: src/VeraGridEngine/Simulations/SmallSignalStabilityEmt/era_matrix_pencil_driver.py

- Original source path: `src/VeraGridEngine/Simulations/SmallSignalStabilityEmt/era_matrix_pencil_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 7
- Representative imports: __future__, typing, numpy, scipy.linalg, numpy.lib.stride_tricks, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Simulations.EMT.emt_options, VeraGridEngine.Simulations.EMT.problems.emt_problem_template, VeraGridEngine.Simulations.EMT.solvers.StructuralVectorizedSolver, VeraGridEngine.Simulations.SmallSignalStabilityEmt.era_matrix_pencil_core, VeraGridEngine.Simulations.SmallSignalStabilityEmt.era_matrix_pencil_options, VeraGridEngine.Simulations.SmallSignalStabilityEmt.era_matrix_pencil_results, VeraGridEngine.Simulations.driver_template, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Function: select_dominant_observable(y_data)

Legacy helper that selects one dominant observable by variance.

## Function: build_hankel_zero_copy(y_signal, window_length)

Legacy helper that builds a scalar Hankel view.

## Function: build_empty_era_results(observable_names)

Build an empty public results object.

## Function: extract_observable_names(problem)

Extract the ordered state-variable labels from the EMT problem.

## Function: simulate_emt_state_history(solver, n_states)

Run the EMT solver and slice the differential-state block.

## Function: unpack_dense_state_matrix(y_full_tuples, n_states)

Convert the solver output into one dense real matrix.

## Function: extract_matrix_pencil_poles(y_signal, dt, max_modes, tol_deflation)

Compatibility wrapper around the new EMT matrix-pencil engine.

## Class: EraMatrixPencilDriver

- Bases: DriverTemplate
- Summary: EMT driver for the frequency-zooming forward-backward TLS matrix pencil.

### Methods

- `get_results(self)`
  Summary: Return the latest extraction results.
- `run(self)`
  Summary: Execute the EMT ringdown simulation and the modal extraction pipeline.
