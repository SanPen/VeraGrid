# VeraGridEngine Module: src/VeraGridEngine/Simulations/SmallSignalStabilityEmt/era_matrix_pencil_results.py

- Original source path: `src/VeraGridEngine/Simulations/SmallSignalStabilityEmt/era_matrix_pencil_results.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 9
- Representative imports: __future__, math, typing, numpy, matplotlib, VeraGridEngine.Simulations.results_table, VeraGridEngine.Simulations.results_template, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Function: build_empty_float_vector()

Build one empty real vector with the engine canonical dtype.

## Function: build_empty_complex_vector()

Build one empty complex vector with the engine canonical dtype.

## Function: build_empty_complex_matrix()

Build one empty complex matrix with the engine canonical dtype.

## Function: build_empty_int_vector()

Build one empty integer vector with the engine canonical dtype.

## Function: build_empty_bool_vector()

Build one empty boolean vector with the engine canonical dtype.

## Function: compute_damping_ratios_from_poles(eigenvalues_s)

Compute damping ratios from continuous-time poles.

## Function: compute_frequencies_from_poles(eigenvalues_s)

Compute modal frequencies in Hz from continuous-time poles.

## Function: compute_stability_mask_from_poles(eigenvalues_s)

Compute the linear stability mask from continuous-time poles.

## Function: build_modes_results_table_data(results)

Build the numeric table used by the VeraGrid mode browser.

## Class: EraMatrixPencilResults

- Bases: ResultsTemplate
- Summary: Detailed results container for the EMT frequency-zooming matrix pencil.

### Methods

- `eigenvalues_s(self)`
  Summary: Return the continuous-time poles.
- `eigenvalues_s(self, value)`
  Summary: Set the continuous-time poles.
- `frequencies_hz(self)`
  Summary: Return modal frequencies in Hz.
- `frequencies_hz(self, value)`
  Summary: Set modal frequencies in Hz.
- `damping_ratios(self)`
  Summary: Return modal damping ratios.
- `damping_ratios(self, value)`
  Summary: Set modal damping ratios.
- `is_stable(self)`
  Summary: Return the continuous-time stability mask.
- `is_stable(self, value)`
  Summary: Set the stability mask.
- `residues(self)`
  Summary: Return the complex residue matrix.
- `residues(self, value)`
  Summary: Set the complex residue matrix.
- `modal_energy(self)`
  Summary: Return the relative modal-energy vector.
- `modal_energy(self, value)`
  Summary: Set the modal-energy vector.
- `reconstruction_errors(self)`
  Summary: Return the reconstruction error attached to each mode.
- `reconstruction_errors(self, value)`
  Summary: Set the reconstruction-error vector.
- `band_low_hz(self)`
  Summary: Return the lower edge of the source band for each mode.
- `band_low_hz(self, value)`
  Summary: Set the lower source-band vector.
- `band_high_hz(self)`
  Summary: Return the upper edge of the source band for each mode.
- `band_high_hz(self, value)`
  Summary: Set the upper source-band vector.
- `selected_orders(self)`
  Summary: Return the selected subspace order for each mode.
- `selected_orders(self, value)`
  Summary: Set the selected-order vector.
- `observable_count_per_mode(self)`
  Summary: Return how many channels participated in each mode estimate.
- `observable_count_per_mode(self, value)`
  Summary: Set the per-mode observable-count vector.
- `get_observable_names(self)`
  Summary: Return the observable labels used during extraction.
- `get_eigenvalues(self)`
  Summary: Backward-compatible accessor used by older callers.
- `get_residues(self)`
  Summary: Return the complex residue matrix.
- `get_modal_energy(self)`
  Summary: Return the relative modal-energy vector.
- `mdl(self, result_type)`
  Summary: Export a VeraGrid ``ResultsTable`` view.
