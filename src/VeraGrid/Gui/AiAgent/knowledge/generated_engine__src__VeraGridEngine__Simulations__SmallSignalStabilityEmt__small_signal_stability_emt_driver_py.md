# VeraGridEngine Module: src/VeraGridEngine/Simulations/SmallSignalStabilityEmt/small_signal_stability_emt_driver.py

- Original source path: `src/VeraGridEngine/Simulations/SmallSignalStabilityEmt/small_signal_stability_emt_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 3
- Top-level function count: 1
- Representative imports: typing, numpy, scipy.sparse.linalg, scipy.linalg, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Simulations.EMT.problems.emt_problem_template, VeraGridEngine.Simulations.driver_template, VeraGridEngine.Simulations.EMT.emt_options, VeraGridEngine.Simulations.EMT.solvers.StructuralVectorizedSolver, VeraGridEngine.Simulations.SmallSignalStabilityEmt.emt_floquet_operator, VeraGridEngine.Simulations.SmallSignalStabilityEmt.small_signal_stability_emt_options, VeraGridEngine.Simulations.SmallSignalStabilityEmt.small_signal_stability_emt_results, VeraGridEngine.Simulations.SmallSignalStabilityEmt.emt_floquet_numba_kernels, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Function: build_restart_seed(U_sel, p_target, seed)

Builds a real orthonormal restart block from complex Ritz/refined vectors.

## Class: RobustBlockArnoldiEngine

- Bases: none
- Summary: Implements:

### Methods

- `_orthogonalize_block(self, W, current_iter)`
  Summary: Orthogonalizes W against all previously computed blocks V_0 ... V_j.
- `_rank_revealing_svd(self, W)`
  Summary: Extracts the orthonormal basis of W and the sub-diagonal Hessenberg block.
- `build_krylov_space(self, V_init)`
  Summary: Executes the robust Block Arnoldi process to build the Krylov subspace.

## Class: BestPack

- Bases: none
- Summary: Data structure to hold the best Ritz pairs found during restarts.

### Methods

- No methods detected.

## Class: SmallSignalStabilityEmtDriver

- Bases: DriverTemplate
- Summary: Base class for EMT Floquet stability analysis.

### Methods

- `_capture_limit_cycle_and_evaluator(self, h, verbose)`
  Summary: Captures the limit cycle by simulating the system up to ss_assessment_time.
- `run_arnoldi(self)`
  Summary: Executes the Standard Arnoldi Floquet analysis using SciPy ARPACK.
- `_make_monodromy_operator(self, h, n_states)`
  Summary: Creates the Monodromy Operator. Uses the HPC Ak-Stack if available,
- `_apply_operator_complex(monodromy_op, Xc)`
  Summary: Helper method to apply a real-valued block operator to a complex block matrix.
- `_compute_selected_pairs(self, monodromy_op, V_sub, H_sub, k_target, p_seed, use_refined)`
  Summary: Solves the projected sub-problem and extracts the dominant Ritz pairs.
- `run_arnoldi_hybrid(self)`
  Summary: Executes the Hybrid Block-Arnoldi (BIRAM) Floquet analysis.
- `run(self)`
  Summary: Executes the analysis based on the selected builder type in the options.
