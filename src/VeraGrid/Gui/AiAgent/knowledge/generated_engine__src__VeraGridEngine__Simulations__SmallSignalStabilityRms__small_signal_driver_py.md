# VeraGridEngine Module: src/VeraGridEngine/Simulations/SmallSignalStabilityRms/small_signal_driver.py

- Original source path: `src/VeraGridEngine/Simulations/SmallSignalStabilityRms/small_signal_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 3
- Top-level function count: 7
- Representative imports: numpy, numba, matplotlib, scipy.linalg, scipy.sparse.linalg, math, time, scipy.sparse, typing, VeraGridEngine.Devices.Aggregation.rms_events_group, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Simulations.driver_template, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.Simulations.SmallSignalStabilityRms.small_signal_options, VeraGridEngine.Simulations.SmallSignalStabilityRms.small_signal_results, VeraGridEngine.enumerations

## Function: compute_state_matrix(problem, x, dx)

Small Signal Stability analysis state matrix computation.

## Function: compute_participation_factors(v, w)

Calculates normalized participation factors correctly for both dense and sparse.

## Function: select_eigs_without_conjugates(eigenvalues)

Select oscillatory modes. Conjugate modes appear only once in the selection.

## Function: compute_damping_ratios_and_frequencies(eigenvalues, eig_no_conjugates)

:param eigenvalues: row np array with modes

## Function: plot_stability(eigenvalues, plot_units)

:param eigenvalues: row np array with modes

## Function: run_dense_small_signal_stability(problem, x, dx, verbose)

Run small signal stability analysis using dense matrices calculations. The operation returns all the eigenvalues.

## Function: run_sparse_small_signal_stability(problem, x, dx, k, verbose)

Run small signal stability analysis using sparse matrices calculations. The operation returns k eigenvalues.

## Class: SparseGeneralizedShiftInvertMethods

- Bases: none
- Summary: Helper class to hold the matvec and rmatvec operations for the Sparse LinearOperator for

### Methods

- `matvec(self, v)`
  Summary: No docstring provided.
- `rmatvec(self, v)`
  Summary: No docstring provided.

## Class: SparseShiftAndInvertMethods

- Bases: none
- Summary: Helper class to hold the matvec and rmatvec operations for the Sparse LinearOperator.

### Methods

- `matvec(self, b)`
  Summary: Matrix-vector multiplication.
- `rmatvec(self, b)`
  Summary: Adjoint matrix-vector multiplication.

## Class: SmallSignalStabilityRmsDriver

- Bases: DriverTemplate
- Summary: Small Signal Stability RMS driver

### Methods

- `run(self)`
  Summary: Main function to initialize and run the system simulation.
- `run_small_signal_stability(self)`
  Summary: Performs the numerical integration using the chosen method and the small signal stability assessment.
