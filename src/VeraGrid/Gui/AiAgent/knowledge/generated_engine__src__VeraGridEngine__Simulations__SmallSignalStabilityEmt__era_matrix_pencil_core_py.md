# VeraGridEngine Module: src/VeraGridEngine/Simulations/SmallSignalStabilityEmt/era_matrix_pencil_core.py

- Original source path: `src/VeraGridEngine/Simulations/SmallSignalStabilityEmt/era_matrix_pencil_core.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 5
- Top-level function count: 52
- Representative imports: __future__, math, typing, numpy, numpy.typing, scipy.interpolate, scipy.linalg, scipy.optimize, scipy.signal, scipy.sparse.linalg, numpy.lib.stride_tricks, VeraGridEngine.basic_structures, VeraGridEngine.Simulations.SmallSignalStabilityEmt.era_matrix_pencil_options, VeraGridEngine.Simulations.SmallSignalStabilityEmt.era_matrix_pencil_results

## Class: EraChannelScaling

- Bases: none
- Summary: Container for channel centering and scaling information.

### Methods

- `get_means(self)`
  Summary: Return the per-channel means.
- `get_scales(self)`
  Summary: Return the per-channel scaling vector.

## Class: EraBandSignal

- Bases: none
- Summary: Prepared sub-band signal and its numerical metadata.

### Methods

- `get_time_data(self)`
  Summary: Return the decimated time vector.
- `get_signal_data(self)`
  Summary: Return the standardized band-limited observation matrix.
- `get_physical_scales(self)`
  Summary: Return the original per-channel scaling factors.
- `get_time_step(self)`
  Summary: Return the effective decimated time step.
- `get_sampling_frequency_hz(self)`
  Summary: Return the effective decimated sampling frequency.
- `get_low_hz(self)`
  Summary: Return the lower band edge.
- `get_high_hz(self)`
  Summary: Return the upper band edge.
- `get_decimation_factor(self)`
  Summary: Return the effective integer decimation factor.

## Class: EraSvdDecomposition

- Bases: none
- Summary: SVD decomposition used by the TLS matrix pencil stage.

### Methods

- `get_singular_values(self)`
  Summary: Return the singular values.
- `get_right_vectors(self)`
  Summary: Return the right singular vectors.
- `get_condition_number(self)`
  Summary: Return the condition-number estimate.
- `get_truncated_backend(self)`
  Summary: Return whether the decomposition came from a truncated backend.

## Class: EraBandResult

- Bases: none
- Summary: Result of one independent band extraction.

### Methods

- `get_poles_s(self)`
  Summary: Return the continuous-time poles.
- `get_poles_z(self)`
  Summary: Return the discrete-time poles.
- `get_residues(self)`
  Summary: Return the physical residue matrix.
- `get_modal_energy(self)`
  Summary: Return the relative modal-energy vector.
- `get_reconstruction_error(self)`
  Summary: Return the global reconstruction error.
- `get_band_low_hz(self)`
  Summary: Return the lower source-band edge.
- `get_band_high_hz(self)`
  Summary: Return the upper source-band edge.
- `get_selected_order(self)`
  Summary: Return the selected subspace order.
- `get_observable_count(self)`
  Summary: Return how many channels participated in this band extraction.
- `get_condition_number(self)`
  Summary: Return the band condition-number estimate.
- `get_successful(self)`
  Summary: Return whether the band produced valid modes.

## Class: EraMergedModalData

- Bases: none
- Summary: Fused modal data produced after multi-band clustering.

### Methods

- `get_poles_s(self)`
  Summary: Return the fused continuous-time poles.
- `get_residues(self)`
  Summary: Return the fused physical residues.
- `get_modal_energy(self)`
  Summary: Return the fused modal-energy vector.
- `get_reconstruction_errors(self)`
  Summary: Return the reconstruction-error vector.
- `get_band_low_hz(self)`
  Summary: Return the lower source-band vector.
- `get_band_high_hz(self)`
  Summary: Return the upper source-band vector.
- `get_selected_orders(self)`
  Summary: Return the selected-order vector.
- `get_observable_count_per_mode(self)`
  Summary: Return the per-mode observable-count vector.

## Function: build_empty_complex_vector()

Build one empty complex vector.

## Function: build_empty_float_vector()

Build one empty real vector.

## Function: build_empty_complex_matrix()

Build one empty complex matrix.

## Function: create_empty_band_result(observable_count, low_hz, high_hz)

Build an empty band result.

## Function: create_empty_merged_modal_data()

Build one empty fused modal container.

## Function: evaluate_exponential_offset_model(time_data, offset, amplitude, decay_rate)

Evaluate the exponential DC-offset model used during detrending.

## Function: convert_signal_to_2d(y_data)

Ensure that the input observation array is two-dimensional.

## Function: infer_uniform_time_step(time_data, fallback_step)

Infer the effective uniform time step from a possibly adaptive time grid.

## Function: resample_to_uniform_time_grid(time_data, y_data, target_step)

Resample the observations onto a uniform time grid.

## Function: select_mimo_observables(y_data, observable_names, maximum_observables)

Select the observable channels used to build the MIMO Hankel matrix.

## Function: fit_exponential_dc_component(time_data, signal_data)

Fit one decaying DC component to a single channel.

## Function: detrend_exponential_dc_offsets(time_data, y_data, use_exponential_detrending)

Remove the exponential DC component from every observation channel.

## Function: compute_channel_scaling(y_data)

Compute channel centering and scaling factors.

## Function: standardize_signal_matrix(y_data, scaling)

Standardize all channels using the provided scaling object.

## Function: resolve_nominal_frequency_hz(explicit_nominal_frequency_hz, fallback_nominal_frequency_hz)

Resolve the nominal system frequency.

## Function: apply_ba_filter_matrix(y_data, numerator, denominator, use_zero_phase_filtering)

Apply one transfer-function filter channel-by-channel.

## Function: apply_sos_filter_matrix(y_data, sos_matrix, use_zero_phase_filtering)

Apply one SOS filter channel-by-channel.

## Function: apply_notch_filter_matrix(y_data, sampling_frequency_hz, nominal_frequency_hz, quality_factor, use_notch_filtering, use_zero_phase_filtering)

Apply the strict fundamental notch filter.

## Function: sanitize_analysis_bands(bands, sampling_frequency_hz)

Sanitize analysis bands against the current Nyquist limit.

## Function: design_band_filter_sos(low_hz, high_hz, sampling_frequency_hz, filter_order)

Design the real-valued sub-band filter.

## Function: compute_decimation_factor(n_samples, input_sampling_frequency_hz, band_high_hz, decimation_safety_factor, manual_cap_factor, minimum_samples_per_band)

Compute the safe integer decimation factor for one band.

## Function: prepare_band_signal(time_data, y_data, scaling, band, era_options)

Build one filtered and decimated sub-band record.

## Function: compute_block_rows(n_samples, era_options)

Compute the block-Hankel depth.

## Function: build_block_hankel_matrix(signal_data, block_rows)

Build the MIMO block-Hankel matrix.

## Function: build_forward_backward_hankel_matrix(signal_data, block_rows, use_forward_backward)

Build the forward-backward block-Hankel matrix.

## Function: build_full_svd_decomposition(hankel_matrix)

Build one decomposition from a dense full SVD.

## Function: compute_svd_decomposition(hankel_matrix, era_options)

Compute the Hankel SVD using the configured backend.

## Function: compute_information_criterion_scores(singular_values, n_snapshots)

Compute MDL and AIC order-selection scores.

## Function: select_model_order(decomposition, n_snapshots, era_options)

Select the effective signal subspace order.

## Function: build_square_tls_pencil(right_vectors, selected_order)

Build the square TLS pencil used by the generalized eigenproblem.

## Function: build_candidate_orders(maximum_order)

Build the candidate orders explored inside one band.

## Function: reject_notched_nominal_poles(z_poles, s_poles, era_options)

Remove poles that remain too close to the notched nominal frequency.

## Function: reject_excessively_fast_poles(z_poles, s_poles, record_duration_s)

Reject poles whose real part is too extreme for the available record length.

## Function: solve_band_modes_for_order(band_signal, era_options, decomposition, candidate_order)

Solve one band for one explicit candidate order.

## Function: compute_band_result_score(band_result)

Compute the selection score used to choose the best candidate order.

## Function: solve_tls_gevp(v2_matrix, v1_matrix)

Solve the TLS generalized eigenvalue problem with a QZ-based backend.

## Function: filter_discrete_poles(z_poles)

Remove obviously invalid discrete-time poles.

## Function: map_discrete_to_continuous_poles(z_poles, time_step, low_hz, high_hz, principal_log_tolerance_hz)

Map discrete-time poles to continuous time and validate the principal log.

## Function: deduplicate_continuous_poles(z_poles, s_poles, frequency_tolerance_hz, real_part_tolerance)

Remove duplicate poles inside one band.

## Function: find_conjugate_index(s_poles, reference_index, frequency_tolerance_hz, real_part_tolerance)

Find the conjugate partner of one pole.

## Function: enforce_conjugate_symmetry(z_poles, s_poles, time_step, frequency_tolerance_hz, real_part_tolerance)

Enforce explicit conjugate-pair symmetry for real-valued EMT signals.

## Function: build_vandermonde_matrix(z_poles, n_samples)

Build the Vandermonde matrix used to fit modal residues.

## Function: solve_modal_residues(signal_data, z_poles)

Solve the MIMO residue least-squares problem.

## Function: scale_residues_to_physical_units(residues, physical_scales)

Re-scale residues back to the original physical channel magnitudes.

## Function: build_physical_band_signal(signal_data, physical_scales)

Re-scale the band-limited observations back to physical units.

## Function: compute_modal_energies(physical_signal_data, z_poles, physical_residues)

Compute per-mode modal energy in physical units.

## Function: compute_pair_energy_keep_mask(s_poles, modal_energy, energy_threshold, frequency_tolerance_hz, real_part_tolerance)

Build the keep mask while preserving conjugate pairs.

## Function: extract_band_modes(band_signal, era_options)

Extract one band of modes using the TLS forward-backward matrix pencil.

## Function: sort_modes_by_frequency_and_damping(poles_s, residues, modal_energy, reconstruction_errors, band_low_hz, band_high_hz, selected_orders, observable_count_per_mode)

Sort fused modes by absolute frequency and then by damping.

## Function: merge_band_results(band_results, era_options)

Fuse the valid band results into one modal set.

## Function: build_results_from_merged_modal_data(merged_data, observable_names)

Build the public results object from the fused modal data.

## Function: extract_matrix_pencil_results_from_data(time_data, y_data, era_options, nominal_frequency_hz, observable_names)

Execute the full EMT frequency-zooming matrix pencil on dense data.
