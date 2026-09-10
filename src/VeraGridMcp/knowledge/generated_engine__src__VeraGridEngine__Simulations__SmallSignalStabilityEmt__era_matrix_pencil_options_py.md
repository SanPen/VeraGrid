# VeraGridEngine Module: src/VeraGridEngine/Simulations/SmallSignalStabilityEmt/era_matrix_pencil_options.py

- Original source path: `src/VeraGridEngine/Simulations/SmallSignalStabilityEmt/era_matrix_pencil_options.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 2
- Representative imports: __future__, typing, VeraGridEngine.Devices.Parents.editable_device, VeraGridEngine.enumerations, VeraGridEngine.Simulations.options_template

## Class: EraMatrixPencilBand

- Bases: none
- Summary: Immutable-looking light wrapper for one analysis band.

### Methods

- `get_low_hz(self)`
  Summary: Return the lower analysis frequency.
- `set_low_hz(self, value)`
  Summary: Set the lower analysis frequency.
- `get_high_hz(self)`
  Summary: Return the upper analysis frequency.
- `set_high_hz(self, value)`
  Summary: Set the upper analysis frequency.
- `low_hz(self)`
  Summary: Property wrapper for VeraGrid style compatibility.
- `low_hz(self, value)`
  Summary: Property wrapper for VeraGrid style compatibility.
- `high_hz(self)`
  Summary: Property wrapper for VeraGrid style compatibility.
- `high_hz(self, value)`
  Summary: Property wrapper for VeraGrid style compatibility.
- `to_tuple(self)`
  Summary: Export the band as a plain tuple.

## Function: create_default_era_analysis_bands()

Build the default multi-band plan for EMT modal zooming.

## Function: build_era_analysis_bands_from_pairs(band_limits)

Convert raw tuple pairs into validated analysis-band objects.

## Class: EraMatrixPencilOptions

- Bases: OptionsTemplate
- Summary: Configuration object for the EMT frequency-zooming matrix pencil engine.

### Methods

- `get_decimation_factor(self)`
  Summary: Return the legacy manual cap for dynamic decimation.
- `set_decimation_factor(self, value)`
  Summary: Set the legacy manual cap for dynamic decimation.
- `decimation_factor(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `decimation_factor(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_svd_solver(self)`
  Summary: Return the configured SVD backend.
- `set_svd_solver(self, value)`
  Summary: Set the configured SVD backend.
- `svd_solver(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `svd_solver(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_tol_deflation(self)`
  Summary: Return the singular-value numerical floor.
- `set_tol_deflation(self, value)`
  Summary: Set the singular-value numerical floor.
- `tol_deflation(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `tol_deflation(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_max_modes(self)`
  Summary: Return the global maximum number of retained modes.
- `set_max_modes(self, value)`
  Summary: Set the global maximum number of retained modes.
- `max_modes(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `max_modes(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_t_ringdown(self)`
  Summary: Return the EMT ringdown simulation horizon.
- `set_t_ringdown(self, value)`
  Summary: Set the EMT ringdown simulation horizon.
- `t_ringdown(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `t_ringdown(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_verbose(self)`
  Summary: Return the verbosity level.
- `set_verbose(self, value)`
  Summary: Set the verbosity level.
- `verbose(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `verbose(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_nominal_frequency_hz(self)`
  Summary: Return the explicit nominal-frequency override.
- `set_nominal_frequency_hz(self, value)`
  Summary: Set the explicit nominal-frequency override.
- `nominal_frequency_hz(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `nominal_frequency_hz(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_use_notch_filtering(self)`
  Summary: Return the notch-filter activation flag.
- `set_use_notch_filtering(self, value)`
  Summary: Set the notch-filter activation flag.
- `use_notch_filtering(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `use_notch_filtering(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_notch_quality_factor(self)`
  Summary: Return the notch quality factor.
- `set_notch_quality_factor(self, value)`
  Summary: Set the notch quality factor.
- `notch_quality_factor(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `notch_quality_factor(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_decimation_safety_factor(self)`
  Summary: Return the post-band oversampling safety factor.
- `set_decimation_safety_factor(self, value)`
  Summary: Set the post-band oversampling safety factor.
- `decimation_safety_factor(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `decimation_safety_factor(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_anti_alias_filter_order(self)`
  Summary: Return the Butterworth anti-alias filter order.
- `set_anti_alias_filter_order(self, value)`
  Summary: Set the Butterworth anti-alias filter order.
- `anti_alias_filter_order(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `anti_alias_filter_order(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_use_zero_phase_filtering(self)`
  Summary: Return the zero-phase filtering flag.
- `set_use_zero_phase_filtering(self, value)`
  Summary: Set the zero-phase filtering flag.
- `use_zero_phase_filtering(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `use_zero_phase_filtering(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_block_rows_ratio(self)`
  Summary: Return the block-Hankel sizing ratio.
- `set_block_rows_ratio(self, value)`
  Summary: Set the block-Hankel sizing ratio.
- `block_rows_ratio(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `block_rows_ratio(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_minimum_block_rows(self)`
  Summary: Return the minimum block-Hankel depth.
- `set_minimum_block_rows(self, value)`
  Summary: Set the minimum block-Hankel depth.
- `minimum_block_rows(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `minimum_block_rows(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_minimum_samples_per_band(self)`
  Summary: Return the minimum number of samples required for one band.
- `set_minimum_samples_per_band(self, value)`
  Summary: Set the minimum number of samples required for one band.
- `minimum_samples_per_band(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `minimum_samples_per_band(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_use_forward_backward(self)`
  Summary: Return the forward-backward matrix-pencil flag.
- `set_use_forward_backward(self, value)`
  Summary: Set the forward-backward matrix-pencil flag.
- `use_forward_backward(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `use_forward_backward(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_use_exponential_detrending(self)`
  Summary: Return the exponential detrending flag.
- `set_use_exponential_detrending(self, value)`
  Summary: Set the exponential detrending flag.
- `use_exponential_detrending(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `use_exponential_detrending(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_maximum_observables(self)`
  Summary: Return the optional cap on the number of observed channels.
- `set_maximum_observables(self, value)`
  Summary: Set the optional cap on the number of observed channels.
- `maximum_observables(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `maximum_observables(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_min_mode_energy_ratio(self)`
  Summary: Return the minimum retained modal-energy ratio.
- `set_min_mode_energy_ratio(self, value)`
  Summary: Set the minimum retained modal-energy ratio.
- `min_mode_energy_ratio(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `min_mode_energy_ratio(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_frequency_merge_tolerance_hz(self)`
  Summary: Return the frequency tolerance used while merging poles.
- `set_frequency_merge_tolerance_hz(self, value)`
  Summary: Set the frequency tolerance used while merging poles.
- `frequency_merge_tolerance_hz(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `frequency_merge_tolerance_hz(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_real_part_merge_tolerance(self)`
  Summary: Return the real-part tolerance used while merging poles.
- `set_real_part_merge_tolerance(self, value)`
  Summary: Set the real-part tolerance used while merging poles.
- `real_part_merge_tolerance(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `real_part_merge_tolerance(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_principal_log_tolerance_hz(self)`
  Summary: Return the tolerance used while validating principal-log frequencies.
- `set_principal_log_tolerance_hz(self, value)`
  Summary: Set the tolerance used while validating principal-log frequencies.
- `principal_log_tolerance_hz(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `principal_log_tolerance_hz(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `get_condition_number_limit(self)`
  Summary: Return the numerical conditioning ceiling.
- `set_condition_number_limit(self, value)`
  Summary: Set the numerical conditioning ceiling.
- `condition_number_limit(self)`
  Summary: Property wrapper for VeraGrid schema access.
- `condition_number_limit(self, value)`
  Summary: Property wrapper for VeraGrid schema access.
- `set_analysis_bands(self, band_limits)`
  Summary: Replace the complete analysis-band plan.
- `get_analysis_bands(self)`
  Summary: Return the configured analysis-band plan.
- `get_analysis_band_limits(self)`
  Summary: Return the analysis-band plan as plain tuples.
