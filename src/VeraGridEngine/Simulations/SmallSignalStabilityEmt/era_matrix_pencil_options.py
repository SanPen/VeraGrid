# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Tuple

from VeraGridEngine.Devices.Parents.editable_device import GCProp
from VeraGridEngine.enumerations import EraSvdSolverType
from VeraGridEngine.Simulations.options_template import OptionsTemplate


class EraMatrixPencilBand:
    """
    Immutable-looking light wrapper for one analysis band.

    The class exposes explicit getters and setters because the EMT modal
    workflow needs predictable state inspection when debugging numerical
    conditioning problems.
    """

    __slots__ = (
        '_low_hz',
        '_high_hz',
    )

    def __init__(self, low_hz: float, high_hz: float) -> None:
        """
        Build one frequency band definition.

        :param low_hz: Lower edge in Hz.
        :param high_hz: Upper edge in Hz.
        :return: None.
        """
        self._low_hz: float = 0.0
        self._high_hz: float = 0.0

        # The setters centralize all validation so every construction path
        # uses the exact same band sanitization rules.
        self.set_low_hz(low_hz)
        self.set_high_hz(high_hz)

    def get_low_hz(self) -> float:
        """
        Return the lower analysis frequency.

        :return: Lower edge in Hz.
        """
        return self._low_hz

    def set_low_hz(self, value: float) -> None:
        """
        Set the lower analysis frequency.

        :param value: Requested lower edge in Hz.
        :return: None.
        """
        sanitized_value: float = float(value)

        # The lower edge must be non-negative because negative frequencies are
        # represented by the conjugate pole pair in the real-valued signal.
        if sanitized_value >= 0.0:
            self._low_hz = sanitized_value
        else:
            self._low_hz = 0.0

    def get_high_hz(self) -> float:
        """
        Return the upper analysis frequency.

        :return: Upper edge in Hz.
        """
        return self._high_hz

    def set_high_hz(self, value: float) -> None:
        """
        Set the upper analysis frequency.

        :param value: Requested upper edge in Hz.
        :return: None.
        """
        sanitized_value: float = float(value)

        # The upper edge must stay strictly positive so the band carries a
        # meaningful oscillatory window for the matrix pencil subspace.
        if sanitized_value > 0.0:
            self._high_hz = sanitized_value
        else:
            self._high_hz = 1.0

    @property
    def low_hz(self) -> float:
        """
        Property wrapper for VeraGrid style compatibility.

        :return: Lower edge in Hz.
        """
        return self.get_low_hz()

    @low_hz.setter
    def low_hz(self, value: float) -> None:
        """
        Property wrapper for VeraGrid style compatibility.

        :param value: Requested lower edge in Hz.
        :return: None.
        """
        self.set_low_hz(value)

    @property
    def high_hz(self) -> float:
        """
        Property wrapper for VeraGrid style compatibility.

        :return: Upper edge in Hz.
        """
        return self.get_high_hz()

    @high_hz.setter
    def high_hz(self, value: float) -> None:
        """
        Property wrapper for VeraGrid style compatibility.

        :param value: Requested upper edge in Hz.
        :return: None.
        """
        self.set_high_hz(value)

    def to_tuple(self) -> Tuple[float, float]:
        """
        Export the band as a plain tuple.

        :return: Two-float tuple ``(low_hz, high_hz)``.
        """
        return self._low_hz, self._high_hz


def create_default_era_analysis_bands() -> Tuple[EraMatrixPencilBand, ...]:
    """
    Build the default multi-band plan for EMT modal zooming.

    :return: Tuple of default analysis bands.
    """
    bands_list: list[EraMatrixPencilBand] = list()

    # The first band targets super-synchronous control modes after the
    # fundamental notch suppresses the overwhelming 50/60 Hz component.
    bands_list.append(EraMatrixPencilBand(low_hz=25.0, high_hz=250.0))

    # The second band targets inverter ripple, PLL interactions and other
    # higher-frequency EMT control artifacts.
    bands_list.append(EraMatrixPencilBand(low_hz=250.0, high_hz=2000.0))

    return tuple(bands_list)


def build_era_analysis_bands_from_pairs(
        band_limits: Tuple[Tuple[float, float], ...] | None) -> Tuple[EraMatrixPencilBand, ...]:
    """
    Convert raw tuple pairs into validated analysis-band objects.

    :param band_limits: Optional tuple of ``(low_hz, high_hz)`` pairs.
    :return: Sanitized tuple of :class:`EraMatrixPencilBand` objects.
    """
    bands_list: list[EraMatrixPencilBand] = list()

    if band_limits is not None and len(band_limits) > 0:
        pair_index: int = 0
        n_pairs: int = len(band_limits)

        # The conversion is explicit so every band is independently validated
        # and invalid ranges can be ignored without corrupting the whole plan.
        while pair_index < n_pairs:
            current_pair: Tuple[float, float] = band_limits[pair_index]
            low_hz: float = float(current_pair[0])
            high_hz: float = float(current_pair[1])

            if high_hz > low_hz:
                bands_list.append(EraMatrixPencilBand(low_hz=low_hz, high_hz=high_hz))
            else:
                pass

            pair_index += 1
    else:
        default_bands: Tuple[EraMatrixPencilBand, ...] = create_default_era_analysis_bands()
        band_index: int = 0
        n_default_bands: int = len(default_bands)

        while band_index < n_default_bands:
            default_band: EraMatrixPencilBand = default_bands[band_index]
            bands_list.append(
                EraMatrixPencilBand(
                    low_hz=default_band.get_low_hz(),
                    high_hz=default_band.get_high_hz(),
                )
            )
            band_index += 1

    if len(bands_list) > 0:
        sanitized_bands: Tuple[EraMatrixPencilBand, ...] = tuple(bands_list)
    else:
        sanitized_bands = create_default_era_analysis_bands()

    return sanitized_bands


class EraMatrixPencilOptions(OptionsTemplate):
    """
    Configuration object for the EMT frequency-zooming matrix pencil engine.

    The class keeps the legacy public API while adding the numerical controls
    required by the multi-band forward-backward TLS formulation.
    """

    __slots__ = (
        '_decimation_factor',
        '_svd_solver',
        '_tol_deflation',
        '_max_modes',
        '_t_ringdown',
        '_verbose',
        '_nominal_frequency_hz',
        '_use_notch_filtering',
        '_notch_quality_factor',
        '_decimation_safety_factor',
        '_anti_alias_filter_order',
        '_use_zero_phase_filtering',
        '_block_rows_ratio',
        '_minimum_block_rows',
        '_minimum_samples_per_band',
        '_use_forward_backward',
        '_use_exponential_detrending',
        '_maximum_observables',
        '_min_mode_energy_ratio',
        '_frequency_merge_tolerance_hz',
        '_real_part_merge_tolerance',
        '_principal_log_tolerance_hz',
        '_condition_number_limit',
        '_analysis_bands',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(key='decimation_factor', tpe=int),
        GCProp(key='svd_solver', tpe=EraSvdSolverType),
        GCProp(key='tol_deflation', tpe=float),
        GCProp(key='max_modes', tpe=int),
        GCProp(key='t_ringdown', tpe=float),
        GCProp(key='verbose', tpe=int),
        GCProp(key='nominal_frequency_hz', tpe=float),
        GCProp(key='use_notch_filtering', tpe=bool),
        GCProp(key='notch_quality_factor', tpe=float),
        GCProp(key='decimation_safety_factor', tpe=float),
        GCProp(key='anti_alias_filter_order', tpe=int),
        GCProp(key='use_zero_phase_filtering', tpe=bool),
        GCProp(key='block_rows_ratio', tpe=float),
        GCProp(key='minimum_block_rows', tpe=int),
        GCProp(key='minimum_samples_per_band', tpe=int),
        GCProp(key='use_forward_backward', tpe=bool),
        GCProp(key='use_exponential_detrending', tpe=bool),
        GCProp(key='maximum_observables', tpe=int),
        GCProp(key='min_mode_energy_ratio', tpe=float),
        GCProp(key='frequency_merge_tolerance_hz', tpe=float),
        GCProp(key='real_part_merge_tolerance', tpe=float),
        GCProp(key='principal_log_tolerance_hz', tpe=float),
        GCProp(key='condition_number_limit', tpe=float),
    )

    def __init__(self,
                 decimation_factor: int = 1,
                 svd_solver: EraSvdSolverType = EraSvdSolverType.FullSvd,
                 tol_deflation: float = 1e-8,
                 max_modes: int = 50,
                 t_ringdown: float = 0.5,
                 verbose: int = 0,
                 nominal_frequency_hz: float = 0.0,
                 use_notch_filtering: bool = True,
                 notch_quality_factor: float = 60.0,
                 decimation_safety_factor: float = 10.0,
                 anti_alias_filter_order: int = 8,
                 use_zero_phase_filtering: bool = True,
                 block_rows_ratio: float = 0.35,
                 minimum_block_rows: int = 8,
                 minimum_samples_per_band: int = 64,
                 use_forward_backward: bool = True,
                 use_exponential_detrending: bool = True,
                 maximum_observables: int = 0,
                 min_mode_energy_ratio: float = 0.01,
                 frequency_merge_tolerance_hz: float = 0.5,
                 real_part_merge_tolerance: float = 0.5,
                 principal_log_tolerance_hz: float = 2.0,
                 condition_number_limit: float = 1e12,
                 analysis_bands: Tuple[Tuple[float, float], ...] | None = None) -> None:
        """
        Initialize the ERA/Matrix Pencil options.

        :param decimation_factor: Legacy manual cap for the dynamic decimator.
        :param svd_solver: SVD backend selection.
        :param tol_deflation: Numerical singular-value floor.
        :param max_modes: Global maximum number of modes to keep.
        :param t_ringdown: EMT ringdown simulation time horizon in seconds.
        :param verbose: Verbosity level.
        :param nominal_frequency_hz: Explicit nominal frequency. ``0.0`` means auto.
        :param use_notch_filtering: Enable the strict fundamental notch.
        :param notch_quality_factor: Notch quality factor.
        :param decimation_safety_factor: Oversampling safety factor after band isolation.
        :param anti_alias_filter_order: Butterworth filter order used before decimation.
        :param use_zero_phase_filtering: Use zero-phase filtering when feasible.
        :param block_rows_ratio: Ratio used to size the block-Hankel matrix.
        :param minimum_block_rows: Minimum block rows for the Hankel matrix.
        :param minimum_samples_per_band: Minimum samples required to solve one band.
        :param use_forward_backward: Enable forward-backward pencil symmetrization.
        :param use_exponential_detrending: Enable exponential DC-offset removal.
        :param maximum_observables: Optional cap on the number of channels. ``0`` means all.
        :param min_mode_energy_ratio: Minimum modal-energy ratio to keep one mode.
        :param frequency_merge_tolerance_hz: Frequency tolerance for modal fusion.
        :param real_part_merge_tolerance: Real-part tolerance for modal fusion.
        :param principal_log_tolerance_hz: Tolerance used while validating band consistency.
        :param condition_number_limit: Numerical conditioning ceiling.
        :param analysis_bands: Optional tuple of explicit band limits.
        :return: None.
        """
        OptionsTemplate.__init__(self, name='EraMatrixPencilOptions')

        # Every field is initialized before validation so the setters always
        # operate on already allocated state, which keeps debugging predictable.
        self._decimation_factor: int = 1
        self._svd_solver: EraSvdSolverType = EraSvdSolverType.FullSvd
        self._tol_deflation: float = 1e-8
        self._max_modes: int = 50
        self._t_ringdown: float = 0.5
        self._verbose: int = 0
        self._nominal_frequency_hz: float = 0.0
        self._use_notch_filtering: bool = True
        self._notch_quality_factor: float = 60.0
        self._decimation_safety_factor: float = 10.0
        self._anti_alias_filter_order: int = 8
        self._use_zero_phase_filtering: bool = True
        self._block_rows_ratio: float = 0.35
        self._minimum_block_rows: int = 8
        self._minimum_samples_per_band: int = 64
        self._use_forward_backward: bool = True
        self._use_exponential_detrending: bool = True
        self._maximum_observables: int = 0
        self._min_mode_energy_ratio: float = 0.01
        self._frequency_merge_tolerance_hz: float = 0.5
        self._real_part_merge_tolerance: float = 0.5
        self._principal_log_tolerance_hz: float = 2.0
        self._condition_number_limit: float = 1e12
        self._analysis_bands: Tuple[EraMatrixPencilBand, ...] = create_default_era_analysis_bands()

        # The public setters keep the numeric constraints centralized.
        self.set_decimation_factor(decimation_factor)
        self.set_svd_solver(svd_solver)
        self.set_tol_deflation(tol_deflation)
        self.set_max_modes(max_modes)
        self.set_t_ringdown(t_ringdown)
        self.set_verbose(verbose)
        self.set_nominal_frequency_hz(nominal_frequency_hz)
        self.set_use_notch_filtering(use_notch_filtering)
        self.set_notch_quality_factor(notch_quality_factor)
        self.set_decimation_safety_factor(decimation_safety_factor)
        self.set_anti_alias_filter_order(anti_alias_filter_order)
        self.set_use_zero_phase_filtering(use_zero_phase_filtering)
        self.set_block_rows_ratio(block_rows_ratio)
        self.set_minimum_block_rows(minimum_block_rows)
        self.set_minimum_samples_per_band(minimum_samples_per_band)
        self.set_use_forward_backward(use_forward_backward)
        self.set_use_exponential_detrending(use_exponential_detrending)
        self.set_maximum_observables(maximum_observables)
        self.set_min_mode_energy_ratio(min_mode_energy_ratio)
        self.set_frequency_merge_tolerance_hz(frequency_merge_tolerance_hz)
        self.set_real_part_merge_tolerance(real_part_merge_tolerance)
        self.set_principal_log_tolerance_hz(principal_log_tolerance_hz)
        self.set_condition_number_limit(condition_number_limit)
        self.set_analysis_bands(analysis_bands)

    def get_decimation_factor(self) -> int:
        """
        Return the legacy manual cap for dynamic decimation.

        :return: Positive decimation cap.
        """
        return self._decimation_factor

    def set_decimation_factor(self, value: int) -> None:
        """
        Set the legacy manual cap for dynamic decimation.

        :param value: Requested cap.
        :return: None.
        """
        sanitized_value: int = int(value)

        if sanitized_value >= 1:
            self._decimation_factor = sanitized_value
        else:
            self._decimation_factor = 1

    @property
    def decimation_factor(self) -> int:
        """
        Property wrapper for VeraGrid schema access.

        :return: Positive decimation cap.
        """
        return self.get_decimation_factor()

    @decimation_factor.setter
    def decimation_factor(self, value: int) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested cap.
        :return: None.
        """
        self.set_decimation_factor(value)

    def get_svd_solver(self) -> EraSvdSolverType:
        """
        Return the configured SVD backend.

        :return: SVD backend enum.
        """
        return self._svd_solver

    def set_svd_solver(self, value: EraSvdSolverType) -> None:
        """
        Set the configured SVD backend.

        :param value: Requested SVD backend.
        :return: None.
        """
        if isinstance(value, EraSvdSolverType):
            self._svd_solver = value
        else:
            self._svd_solver = EraSvdSolverType.FullSvd

    @property
    def svd_solver(self) -> EraSvdSolverType:
        """
        Property wrapper for VeraGrid schema access.

        :return: SVD backend enum.
        """
        return self.get_svd_solver()

    @svd_solver.setter
    def svd_solver(self, value: EraSvdSolverType) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested SVD backend.
        :return: None.
        """
        self.set_svd_solver(value)

    def get_tol_deflation(self) -> float:
        """
        Return the singular-value numerical floor.

        :return: Positive floor value.
        """
        return self._tol_deflation

    def set_tol_deflation(self, value: float) -> None:
        """
        Set the singular-value numerical floor.

        :param value: Requested floor.
        :return: None.
        """
        sanitized_value: float = float(value)

        if sanitized_value > 0.0:
            self._tol_deflation = sanitized_value
        else:
            self._tol_deflation = 1e-12

    @property
    def tol_deflation(self) -> float:
        """
        Property wrapper for VeraGrid schema access.

        :return: Positive floor value.
        """
        return self.get_tol_deflation()

    @tol_deflation.setter
    def tol_deflation(self, value: float) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested floor.
        :return: None.
        """
        self.set_tol_deflation(value)

    def get_max_modes(self) -> int:
        """
        Return the global maximum number of retained modes.

        :return: Positive mode cap.
        """
        return self._max_modes

    def set_max_modes(self, value: int) -> None:
        """
        Set the global maximum number of retained modes.

        :param value: Requested mode cap.
        :return: None.
        """
        sanitized_value: int = int(value)

        if sanitized_value >= 1:
            self._max_modes = sanitized_value
        else:
            self._max_modes = 1

    @property
    def max_modes(self) -> int:
        """
        Property wrapper for VeraGrid schema access.

        :return: Positive mode cap.
        """
        return self.get_max_modes()

    @max_modes.setter
    def max_modes(self, value: int) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested mode cap.
        :return: None.
        """
        self.set_max_modes(value)

    def get_t_ringdown(self) -> float:
        """
        Return the EMT ringdown simulation horizon.

        :return: Time horizon in seconds.
        """
        return self._t_ringdown

    def set_t_ringdown(self, value: float) -> None:
        """
        Set the EMT ringdown simulation horizon.

        :param value: Requested time horizon in seconds.
        :return: None.
        """
        sanitized_value: float = float(value)

        if sanitized_value > 0.0:
            self._t_ringdown = sanitized_value
        else:
            self._t_ringdown = 0.5

    @property
    def t_ringdown(self) -> float:
        """
        Property wrapper for VeraGrid schema access.

        :return: Time horizon in seconds.
        """
        return self.get_t_ringdown()

    @t_ringdown.setter
    def t_ringdown(self, value: float) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested time horizon in seconds.
        :return: None.
        """
        self.set_t_ringdown(value)

    def get_verbose(self) -> int:
        """
        Return the verbosity level.

        :return: Verbosity level.
        """
        return self._verbose

    def set_verbose(self, value: int) -> None:
        """
        Set the verbosity level.

        :param value: Requested verbosity level.
        :return: None.
        """
        sanitized_value: int = int(value)

        if sanitized_value >= 0:
            self._verbose = sanitized_value
        else:
            self._verbose = 0

    @property
    def verbose(self) -> int:
        """
        Property wrapper for VeraGrid schema access.

        :return: Verbosity level.
        """
        return self.get_verbose()

    @verbose.setter
    def verbose(self, value: int) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested verbosity level.
        :return: None.
        """
        self.set_verbose(value)

    def get_nominal_frequency_hz(self) -> float:
        """
        Return the explicit nominal-frequency override.

        :return: Frequency in Hz. ``0.0`` means auto-detect from the grid.
        """
        return self._nominal_frequency_hz

    def set_nominal_frequency_hz(self, value: float) -> None:
        """
        Set the explicit nominal-frequency override.

        :param value: Frequency in Hz. ``0.0`` means auto.
        :return: None.
        """
        sanitized_value: float = float(value)

        if sanitized_value >= 0.0:
            self._nominal_frequency_hz = sanitized_value
        else:
            self._nominal_frequency_hz = 0.0

    @property
    def nominal_frequency_hz(self) -> float:
        """
        Property wrapper for VeraGrid schema access.

        :return: Frequency in Hz.
        """
        return self.get_nominal_frequency_hz()

    @nominal_frequency_hz.setter
    def nominal_frequency_hz(self, value: float) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested frequency in Hz.
        :return: None.
        """
        self.set_nominal_frequency_hz(value)

    def get_use_notch_filtering(self) -> bool:
        """
        Return the notch-filter activation flag.

        :return: ``True`` when the fundamental notch is enabled.
        """
        return self._use_notch_filtering

    def set_use_notch_filtering(self, value: bool) -> None:
        """
        Set the notch-filter activation flag.

        :param value: Requested flag.
        :return: None.
        """
        self._use_notch_filtering = bool(value)

    @property
    def use_notch_filtering(self) -> bool:
        """
        Property wrapper for VeraGrid schema access.

        :return: ``True`` when the fundamental notch is enabled.
        """
        return self.get_use_notch_filtering()

    @use_notch_filtering.setter
    def use_notch_filtering(self, value: bool) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested flag.
        :return: None.
        """
        self.set_use_notch_filtering(value)

    def get_notch_quality_factor(self) -> float:
        """
        Return the notch quality factor.

        :return: Positive quality factor.
        """
        return self._notch_quality_factor

    def set_notch_quality_factor(self, value: float) -> None:
        """
        Set the notch quality factor.

        :param value: Requested quality factor.
        :return: None.
        """
        sanitized_value: float = float(value)

        if sanitized_value > 1.0:
            self._notch_quality_factor = sanitized_value
        else:
            self._notch_quality_factor = 30.0

    @property
    def notch_quality_factor(self) -> float:
        """
        Property wrapper for VeraGrid schema access.

        :return: Positive quality factor.
        """
        return self.get_notch_quality_factor()

    @notch_quality_factor.setter
    def notch_quality_factor(self, value: float) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested quality factor.
        :return: None.
        """
        self.set_notch_quality_factor(value)

    def get_decimation_safety_factor(self) -> float:
        """
        Return the post-band oversampling safety factor.

        :return: Positive oversampling factor.
        """
        return self._decimation_safety_factor

    def set_decimation_safety_factor(self, value: float) -> None:
        """
        Set the post-band oversampling safety factor.

        :param value: Requested oversampling factor.
        :return: None.
        """
        sanitized_value: float = float(value)

        if sanitized_value >= 2.5:
            self._decimation_safety_factor = sanitized_value
        else:
            self._decimation_safety_factor = 10.0

    @property
    def decimation_safety_factor(self) -> float:
        """
        Property wrapper for VeraGrid schema access.

        :return: Positive oversampling factor.
        """
        return self.get_decimation_safety_factor()

    @decimation_safety_factor.setter
    def decimation_safety_factor(self, value: float) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested oversampling factor.
        :return: None.
        """
        self.set_decimation_safety_factor(value)

    def get_anti_alias_filter_order(self) -> int:
        """
        Return the Butterworth anti-alias filter order.

        :return: Positive filter order.
        """
        return self._anti_alias_filter_order

    def set_anti_alias_filter_order(self, value: int) -> None:
        """
        Set the Butterworth anti-alias filter order.

        :param value: Requested filter order.
        :return: None.
        """
        sanitized_value: int = int(value)

        if sanitized_value >= 2:
            self._anti_alias_filter_order = sanitized_value
        else:
            self._anti_alias_filter_order = 8

    @property
    def anti_alias_filter_order(self) -> int:
        """
        Property wrapper for VeraGrid schema access.

        :return: Positive filter order.
        """
        return self.get_anti_alias_filter_order()

    @anti_alias_filter_order.setter
    def anti_alias_filter_order(self, value: int) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested filter order.
        :return: None.
        """
        self.set_anti_alias_filter_order(value)

    def get_use_zero_phase_filtering(self) -> bool:
        """
        Return the zero-phase filtering flag.

        :return: ``True`` when zero-phase filtering is enabled.
        """
        return self._use_zero_phase_filtering

    def set_use_zero_phase_filtering(self, value: bool) -> None:
        """
        Set the zero-phase filtering flag.

        :param value: Requested flag.
        :return: None.
        """
        self._use_zero_phase_filtering = bool(value)

    @property
    def use_zero_phase_filtering(self) -> bool:
        """
        Property wrapper for VeraGrid schema access.

        :return: ``True`` when zero-phase filtering is enabled.
        """
        return self.get_use_zero_phase_filtering()

    @use_zero_phase_filtering.setter
    def use_zero_phase_filtering(self, value: bool) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested flag.
        :return: None.
        """
        self.set_use_zero_phase_filtering(value)

    def get_block_rows_ratio(self) -> float:
        """
        Return the block-Hankel sizing ratio.

        :return: Ratio in the interval ``(0, 1)``.
        """
        return self._block_rows_ratio

    def set_block_rows_ratio(self, value: float) -> None:
        """
        Set the block-Hankel sizing ratio.

        :param value: Requested ratio.
        :return: None.
        """
        sanitized_value: float = float(value)

        if 0.05 < sanitized_value < 0.75:
            self._block_rows_ratio = sanitized_value
        else:
            self._block_rows_ratio = 0.35

    @property
    def block_rows_ratio(self) -> float:
        """
        Property wrapper for VeraGrid schema access.

        :return: Ratio in the interval ``(0, 1)``.
        """
        return self.get_block_rows_ratio()

    @block_rows_ratio.setter
    def block_rows_ratio(self, value: float) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested ratio.
        :return: None.
        """
        self.set_block_rows_ratio(value)

    def get_minimum_block_rows(self) -> int:
        """
        Return the minimum block-Hankel depth.

        :return: Minimum block rows.
        """
        return self._minimum_block_rows

    def set_minimum_block_rows(self, value: int) -> None:
        """
        Set the minimum block-Hankel depth.

        :param value: Requested minimum block rows.
        :return: None.
        """
        sanitized_value: int = int(value)

        if sanitized_value >= 2:
            self._minimum_block_rows = sanitized_value
        else:
            self._minimum_block_rows = 8

    @property
    def minimum_block_rows(self) -> int:
        """
        Property wrapper for VeraGrid schema access.

        :return: Minimum block rows.
        """
        return self.get_minimum_block_rows()

    @minimum_block_rows.setter
    def minimum_block_rows(self, value: int) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested minimum block rows.
        :return: None.
        """
        self.set_minimum_block_rows(value)

    def get_minimum_samples_per_band(self) -> int:
        """
        Return the minimum number of samples required for one band.

        :return: Minimum number of samples.
        """
        return self._minimum_samples_per_band

    def set_minimum_samples_per_band(self, value: int) -> None:
        """
        Set the minimum number of samples required for one band.

        :param value: Requested minimum number of samples.
        :return: None.
        """
        sanitized_value: int = int(value)

        if sanitized_value >= 16:
            self._minimum_samples_per_band = sanitized_value
        else:
            self._minimum_samples_per_band = 64

    @property
    def minimum_samples_per_band(self) -> int:
        """
        Property wrapper for VeraGrid schema access.

        :return: Minimum number of samples.
        """
        return self.get_minimum_samples_per_band()

    @minimum_samples_per_band.setter
    def minimum_samples_per_band(self, value: int) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested minimum number of samples.
        :return: None.
        """
        self.set_minimum_samples_per_band(value)

    def get_use_forward_backward(self) -> bool:
        """
        Return the forward-backward matrix-pencil flag.

        :return: ``True`` when FBMP is enabled.
        """
        return self._use_forward_backward

    def set_use_forward_backward(self, value: bool) -> None:
        """
        Set the forward-backward matrix-pencil flag.

        :param value: Requested flag.
        :return: None.
        """
        self._use_forward_backward = bool(value)

    @property
    def use_forward_backward(self) -> bool:
        """
        Property wrapper for VeraGrid schema access.

        :return: ``True`` when FBMP is enabled.
        """
        return self.get_use_forward_backward()

    @use_forward_backward.setter
    def use_forward_backward(self, value: bool) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested flag.
        :return: None.
        """
        self.set_use_forward_backward(value)

    def get_use_exponential_detrending(self) -> bool:
        """
        Return the exponential detrending flag.

        :return: ``True`` when exponential detrending is enabled.
        """
        return self._use_exponential_detrending

    def set_use_exponential_detrending(self, value: bool) -> None:
        """
        Set the exponential detrending flag.

        :param value: Requested flag.
        :return: None.
        """
        self._use_exponential_detrending = bool(value)

    @property
    def use_exponential_detrending(self) -> bool:
        """
        Property wrapper for VeraGrid schema access.

        :return: ``True`` when exponential detrending is enabled.
        """
        return self.get_use_exponential_detrending()

    @use_exponential_detrending.setter
    def use_exponential_detrending(self, value: bool) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested flag.
        :return: None.
        """
        self.set_use_exponential_detrending(value)

    def get_maximum_observables(self) -> int:
        """
        Return the optional cap on the number of observed channels.

        :return: ``0`` means all channels.
        """
        return self._maximum_observables

    def set_maximum_observables(self, value: int) -> None:
        """
        Set the optional cap on the number of observed channels.

        :param value: Requested cap. ``0`` means all channels.
        :return: None.
        """
        sanitized_value: int = int(value)

        if sanitized_value >= 0:
            self._maximum_observables = sanitized_value
        else:
            self._maximum_observables = 0

    @property
    def maximum_observables(self) -> int:
        """
        Property wrapper for VeraGrid schema access.

        :return: ``0`` means all channels.
        """
        return self.get_maximum_observables()

    @maximum_observables.setter
    def maximum_observables(self, value: int) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested cap.
        :return: None.
        """
        self.set_maximum_observables(value)

    def get_min_mode_energy_ratio(self) -> float:
        """
        Return the minimum retained modal-energy ratio.

        :return: Positive energy threshold.
        """
        return self._min_mode_energy_ratio

    def set_min_mode_energy_ratio(self, value: float) -> None:
        """
        Set the minimum retained modal-energy ratio.

        :param value: Requested energy threshold.
        :return: None.
        """
        sanitized_value: float = float(value)

        if 0.0 <= sanitized_value < 1.0:
            self._min_mode_energy_ratio = sanitized_value
        else:
            self._min_mode_energy_ratio = 0.01

    @property
    def min_mode_energy_ratio(self) -> float:
        """
        Property wrapper for VeraGrid schema access.

        :return: Positive energy threshold.
        """
        return self.get_min_mode_energy_ratio()

    @min_mode_energy_ratio.setter
    def min_mode_energy_ratio(self, value: float) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested energy threshold.
        :return: None.
        """
        self.set_min_mode_energy_ratio(value)

    def get_frequency_merge_tolerance_hz(self) -> float:
        """
        Return the frequency tolerance used while merging poles.

        :return: Frequency tolerance in Hz.
        """
        return self._frequency_merge_tolerance_hz

    def set_frequency_merge_tolerance_hz(self, value: float) -> None:
        """
        Set the frequency tolerance used while merging poles.

        :param value: Requested tolerance in Hz.
        :return: None.
        """
        sanitized_value: float = float(value)

        if sanitized_value > 0.0:
            self._frequency_merge_tolerance_hz = sanitized_value
        else:
            self._frequency_merge_tolerance_hz = 0.5

    @property
    def frequency_merge_tolerance_hz(self) -> float:
        """
        Property wrapper for VeraGrid schema access.

        :return: Frequency tolerance in Hz.
        """
        return self.get_frequency_merge_tolerance_hz()

    @frequency_merge_tolerance_hz.setter
    def frequency_merge_tolerance_hz(self, value: float) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested tolerance in Hz.
        :return: None.
        """
        self.set_frequency_merge_tolerance_hz(value)

    def get_real_part_merge_tolerance(self) -> float:
        """
        Return the real-part tolerance used while merging poles.

        :return: Real-part tolerance in 1/s.
        """
        return self._real_part_merge_tolerance

    def set_real_part_merge_tolerance(self, value: float) -> None:
        """
        Set the real-part tolerance used while merging poles.

        :param value: Requested tolerance in 1/s.
        :return: None.
        """
        sanitized_value: float = float(value)

        if sanitized_value > 0.0:
            self._real_part_merge_tolerance = sanitized_value
        else:
            self._real_part_merge_tolerance = 0.5

    @property
    def real_part_merge_tolerance(self) -> float:
        """
        Property wrapper for VeraGrid schema access.

        :return: Real-part tolerance in 1/s.
        """
        return self.get_real_part_merge_tolerance()

    @real_part_merge_tolerance.setter
    def real_part_merge_tolerance(self, value: float) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested tolerance in 1/s.
        :return: None.
        """
        self.set_real_part_merge_tolerance(value)

    def get_principal_log_tolerance_hz(self) -> float:
        """
        Return the tolerance used while validating principal-log frequencies.

        :return: Frequency tolerance in Hz.
        """
        return self._principal_log_tolerance_hz

    def set_principal_log_tolerance_hz(self, value: float) -> None:
        """
        Set the tolerance used while validating principal-log frequencies.

        :param value: Requested tolerance in Hz.
        :return: None.
        """
        sanitized_value: float = float(value)

        if sanitized_value >= 0.0:
            self._principal_log_tolerance_hz = sanitized_value
        else:
            self._principal_log_tolerance_hz = 2.0

    @property
    def principal_log_tolerance_hz(self) -> float:
        """
        Property wrapper for VeraGrid schema access.

        :return: Frequency tolerance in Hz.
        """
        return self.get_principal_log_tolerance_hz()

    @principal_log_tolerance_hz.setter
    def principal_log_tolerance_hz(self, value: float) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested tolerance in Hz.
        :return: None.
        """
        self.set_principal_log_tolerance_hz(value)

    def get_condition_number_limit(self) -> float:
        """
        Return the numerical conditioning ceiling.

        :return: Positive condition-number limit.
        """
        return self._condition_number_limit

    def set_condition_number_limit(self, value: float) -> None:
        """
        Set the numerical conditioning ceiling.

        :param value: Requested condition-number limit.
        :return: None.
        """
        sanitized_value: float = float(value)

        if sanitized_value > 1.0:
            self._condition_number_limit = sanitized_value
        else:
            self._condition_number_limit = 1e12

    @property
    def condition_number_limit(self) -> float:
        """
        Property wrapper for VeraGrid schema access.

        :return: Positive condition-number limit.
        """
        return self.get_condition_number_limit()

    @condition_number_limit.setter
    def condition_number_limit(self, value: float) -> None:
        """
        Property wrapper for VeraGrid schema access.

        :param value: Requested condition-number limit.
        :return: None.
        """
        self.set_condition_number_limit(value)

    def set_analysis_bands(self, band_limits: Tuple[Tuple[float, float], ...] | None) -> None:
        """
        Replace the complete analysis-band plan.

        :param band_limits: Optional tuple of ``(low_hz, high_hz)`` pairs.
        :return: None.
        """
        self._analysis_bands = build_era_analysis_bands_from_pairs(band_limits)

    def get_analysis_bands(self) -> Tuple[EraMatrixPencilBand, ...]:
        """
        Return the configured analysis-band plan.

        :return: Tuple of :class:`EraMatrixPencilBand` objects.
        """
        return self._analysis_bands

    def get_analysis_band_limits(self) -> Tuple[Tuple[float, float], ...]:
        """
        Return the analysis-band plan as plain tuples.

        :return: Tuple of ``(low_hz, high_hz)`` pairs.
        """
        limits_list: list[Tuple[float, float]] = list()
        band_index: int = 0
        n_bands: int = len(self._analysis_bands)

        while band_index < n_bands:
            current_band: EraMatrixPencilBand = self._analysis_bands[band_index]
            limits_list.append(current_band.to_tuple())
            band_index += 1

        return tuple(limits_list)
