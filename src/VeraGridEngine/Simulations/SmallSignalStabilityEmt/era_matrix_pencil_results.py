# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import math
from typing import List

import numpy as np
from matplotlib import pyplot as plt

from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGridEngine.Simulations.results_template import ResultsTemplate, ResultsProperty
from VeraGridEngine.basic_structures import BoolVec, CxMat, CxVec, IntVec, Mat, Vec
from VeraGridEngine.enumerations import DeviceType, ResultTypes, StudyResultsType


def build_empty_float_vector() -> Vec:
    """
    Build one empty real vector with the engine canonical dtype.

    :return: Empty ``float64`` vector.
    """
    return np.zeros(0, dtype=np.float64)


def build_empty_complex_vector() -> CxVec:
    """
    Build one empty complex vector with the engine canonical dtype.

    :return: Empty ``complex128`` vector.
    """
    return np.zeros(0, dtype=np.complex128)


def build_empty_complex_matrix() -> CxMat:
    """
    Build one empty complex matrix with the engine canonical dtype.

    :return: Empty ``complex128`` matrix.
    """
    return np.zeros((0, 0), dtype=np.complex128)


def build_empty_int_vector() -> IntVec:
    """
    Build one empty integer vector with the engine canonical dtype.

    :return: Empty integer vector.
    """
    return np.zeros(0, dtype=np.int_)


def build_empty_bool_vector() -> BoolVec:
    """
    Build one empty boolean vector with the engine canonical dtype.

    :return: Empty boolean vector.
    """
    return np.zeros(0, dtype=np.bool_)


def compute_damping_ratios_from_poles(eigenvalues_s: CxVec) -> Vec:
    """
    Compute damping ratios from continuous-time poles.

    :param eigenvalues_s: Continuous-time poles.
    :return: Damping-ratio vector.
    """
    n_modes: int = int(eigenvalues_s.shape[0])
    damping_ratios: Vec = np.zeros(n_modes, dtype=np.float64)

    if n_modes > 0:
        mode_index: int = 0

        # The damping ratio is reported for every mode so the engineering view
        # remains immediately comparable with the RMS small-signal module.
        while mode_index < n_modes:
            current_pole: complex = complex(eigenvalues_s[mode_index])
            real_part: float = float(np.real(current_pole))
            imag_part: float = float(np.imag(current_pole))
            modulus: float = math.sqrt(real_part * real_part + imag_part * imag_part)

            if modulus > 1e-15:
                damping_ratios[mode_index] = -real_part / modulus
            else:
                damping_ratios[mode_index] = 0.0

            mode_index += 1
    else:
        pass

    return damping_ratios


def compute_frequencies_from_poles(eigenvalues_s: CxVec) -> Vec:
    """
    Compute modal frequencies in Hz from continuous-time poles.

    :param eigenvalues_s: Continuous-time poles.
    :return: Frequency vector in Hz.
    """
    if eigenvalues_s.shape[0] > 0:
        frequencies_hz: Vec = np.abs(np.imag(eigenvalues_s)) / (2.0 * np.pi)
    else:
        frequencies_hz = build_empty_float_vector()

    return frequencies_hz.astype(np.float64)


def compute_stability_mask_from_poles(eigenvalues_s: CxVec) -> BoolVec:
    """
    Compute the linear stability mask from continuous-time poles.

    :param eigenvalues_s: Continuous-time poles.
    :return: Boolean stability mask.
    """
    if eigenvalues_s.shape[0] > 0:
        is_stable: BoolVec = (np.real(eigenvalues_s) < 0.0).astype(np.bool_)
    else:
        is_stable = build_empty_bool_vector()

    return is_stable


def build_modes_results_table_data(results: 'EraMatrixPencilResults') -> Mat:
    """
    Build the numeric table used by the VeraGrid mode browser.

    :param results: Result container.
    :return: Dense 2-D numeric matrix.
    """
    n_modes: int = int(results.eigenvalues_s.shape[0])

    if n_modes > 0:
        stable_as_float: Vec = results.is_stable.astype(np.float64)
        selected_orders_as_float: Vec = results.selected_orders.astype(np.float64)
        observable_counts_as_float: Vec = results.observable_count_per_mode.astype(np.float64)

        # The table gathers the engineering quantities required to validate one
        # extracted mode without inspecting raw residues manually.
        table_data: Mat = np.c_[
            results.eigenvalues_s.real,
            results.eigenvalues_s.imag,
            results.damping_ratios,
            results.frequencies_hz,
            results.modal_energy,
            stable_as_float,
            results.band_low_hz,
            results.band_high_hz,
            selected_orders_as_float,
            observable_counts_as_float,
            results.reconstruction_errors,
        ]
    else:
        table_data = np.zeros((0, 11), dtype=np.float64)

    return table_data


class EraMatrixPencilResults(ResultsTemplate):
    """
    Detailed results container for the EMT frequency-zooming matrix pencil.

    The class stores the fused continuous-time poles together with the residue
    matrix, modal energy and the provenance of each accepted band estimate.
    """

    LOCAL_RESULTS_DECLARATIONS = (
        ResultsProperty(name='eigenvalues_s', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='frequencies_hz', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='damping_ratios', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='is_stable', tpe=BoolVec, old_names=list(), expandable=False),
        ResultsProperty(name='residues', tpe=CxMat, old_names=list(), expandable=False),
        ResultsProperty(name='modal_energy', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='reconstruction_errors', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='band_low_hz', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='band_high_hz', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='selected_orders', tpe=IntVec, old_names=list(), expandable=False),
        ResultsProperty(name='observable_count_per_mode', tpe=IntVec, old_names=list(), expandable=False),
    )

    __slots__ = (
        '_eigenvalues_s',
        '_frequencies_hz',
        '_damping_ratios',
        '_is_stable',
        '_residues',
        '_modal_energy',
        '_reconstruction_errors',
        '_band_low_hz',
        '_band_high_hz',
        '_selected_orders',
        '_observable_count_per_mode',
        '_observable_names',
    )

    def __init__(self,
                 eigenvalues_s: CxVec,
                 residues: CxMat | None = None,
                 modal_energy: Vec | None = None,
                 reconstruction_errors: Vec | None = None,
                 band_low_hz: Vec | None = None,
                 band_high_hz: Vec | None = None,
                 selected_orders: IntVec | None = None,
                 observable_count_per_mode: IntVec | None = None,
                 observable_names: List[str] | None = None) -> None:
        """
        Initialize the EMT modal results container.

        :param eigenvalues_s: Continuous-time poles in the ``s`` domain.
        :param residues: Complex MIMO residue matrix.
        :param modal_energy: Relative modal-energy vector.
        :param reconstruction_errors: Band reconstruction error per mode.
        :param band_low_hz: Lower edge of the band that produced each mode.
        :param band_high_hz: Upper edge of the band that produced each mode.
        :param selected_orders: Effective subspace order used for each mode.
        :param observable_count_per_mode: Number of observables used for each mode.
        :param observable_names: Names of the observed state trajectories.
        :return: None.
        """
        available_list: list[ResultTypes] = list([
            ResultTypes.Modes,
            ResultTypes.SDomainPlotHz,
        ])

        ResultsTemplate.__init__(
            self,
            name='ERA Matrix Pencil Results',
            available_results=available_list,
            time_array=None,
            clustering_results=None,
            study_results_type=StudyResultsType.SmallSignalStability,
        )

        n_modes: int = int(eigenvalues_s.shape[0])
        self._eigenvalues_s: CxVec = np.asarray(eigenvalues_s, dtype=np.complex128)

        # The derived engineering metrics are computed once so the GUI and the
        # test suite can query them without repeating numerical work.
        self._damping_ratios: Vec = compute_damping_ratios_from_poles(self._eigenvalues_s)
        self._frequencies_hz: Vec = compute_frequencies_from_poles(self._eigenvalues_s)
        self._is_stable: BoolVec = compute_stability_mask_from_poles(self._eigenvalues_s)

        if residues is not None:
            self._residues: CxMat = np.asarray(residues, dtype=np.complex128)
        else:
            self._residues = np.zeros((n_modes, 0), dtype=np.complex128)

        if modal_energy is not None:
            self._modal_energy: Vec = np.asarray(modal_energy, dtype=np.float64)
        else:
            self._modal_energy = np.zeros(n_modes, dtype=np.float64)

        if reconstruction_errors is not None:
            self._reconstruction_errors: Vec = np.asarray(reconstruction_errors, dtype=np.float64)
        else:
            self._reconstruction_errors = np.zeros(n_modes, dtype=np.float64)

        if band_low_hz is not None:
            self._band_low_hz: Vec = np.asarray(band_low_hz, dtype=np.float64)
        else:
            self._band_low_hz = np.zeros(n_modes, dtype=np.float64)

        if band_high_hz is not None:
            self._band_high_hz: Vec = np.asarray(band_high_hz, dtype=np.float64)
        else:
            self._band_high_hz = np.zeros(n_modes, dtype=np.float64)

        if selected_orders is not None:
            self._selected_orders: IntVec = np.asarray(selected_orders, dtype=np.int_)
        else:
            self._selected_orders = np.zeros(n_modes, dtype=np.int_)

        if observable_count_per_mode is not None:
            self._observable_count_per_mode: IntVec = np.asarray(observable_count_per_mode, dtype=np.int_)
        else:
            self._observable_count_per_mode = np.zeros(n_modes, dtype=np.int_)

        if observable_names is not None:
            self._observable_names: List[str] = list(observable_names)
        else:
            self._observable_names = list()

        # Only array-like fields are registered because ResultsTemplate already
        # serializes those safely across the VeraGrid persistence layer.

    @property
    def eigenvalues_s(self) -> CxVec:
        """
        Return the continuous-time poles.

        :return: Complex pole vector.
        """
        return self._eigenvalues_s

    @eigenvalues_s.setter
    def eigenvalues_s(self, value: CxVec) -> None:
        """
        Set the continuous-time poles.

        :param value: Complex pole vector.
        :return: None.
        """
        self._eigenvalues_s = np.asarray(value, dtype=np.complex128)

    @property
    def frequencies_hz(self) -> Vec:
        """
        Return modal frequencies in Hz.

        :return: Frequency vector in Hz.
        """
        return self._frequencies_hz

    @frequencies_hz.setter
    def frequencies_hz(self, value: Vec) -> None:
        """
        Set modal frequencies in Hz.

        :param value: Frequency vector.
        :return: None.
        """
        self._frequencies_hz = np.asarray(value, dtype=np.float64)

    @property
    def damping_ratios(self) -> Vec:
        """
        Return modal damping ratios.

        :return: Damping-ratio vector.
        """
        return self._damping_ratios

    @damping_ratios.setter
    def damping_ratios(self, value: Vec) -> None:
        """
        Set modal damping ratios.

        :param value: Damping-ratio vector.
        :return: None.
        """
        self._damping_ratios = np.asarray(value, dtype=np.float64)

    @property
    def is_stable(self) -> BoolVec:
        """
        Return the continuous-time stability mask.

        :return: Stability mask.
        """
        return self._is_stable

    @is_stable.setter
    def is_stable(self, value: BoolVec) -> None:
        """
        Set the stability mask.

        :param value: Stability mask.
        :return: None.
        """
        self._is_stable = np.asarray(value, dtype=np.bool_)

    @property
    def residues(self) -> CxMat:
        """
        Return the complex residue matrix.

        :return: Complex residue matrix.
        """
        return self._residues

    @residues.setter
    def residues(self, value: CxMat) -> None:
        """
        Set the complex residue matrix.

        :param value: Residue matrix.
        :return: None.
        """
        self._residues = np.asarray(value, dtype=np.complex128)

    @property
    def modal_energy(self) -> Vec:
        """
        Return the relative modal-energy vector.

        :return: Modal-energy vector.
        """
        return self._modal_energy

    @modal_energy.setter
    def modal_energy(self, value: Vec) -> None:
        """
        Set the modal-energy vector.

        :param value: Modal-energy vector.
        :return: None.
        """
        self._modal_energy = np.asarray(value, dtype=np.float64)

    @property
    def reconstruction_errors(self) -> Vec:
        """
        Return the reconstruction error attached to each mode.

        :return: Reconstruction-error vector.
        """
        return self._reconstruction_errors

    @reconstruction_errors.setter
    def reconstruction_errors(self, value: Vec) -> None:
        """
        Set the reconstruction-error vector.

        :param value: Reconstruction-error vector.
        :return: None.
        """
        self._reconstruction_errors = np.asarray(value, dtype=np.float64)

    @property
    def band_low_hz(self) -> Vec:
        """
        Return the lower edge of the source band for each mode.

        :return: Lower-band vector in Hz.
        """
        return self._band_low_hz

    @band_low_hz.setter
    def band_low_hz(self, value: Vec) -> None:
        """
        Set the lower source-band vector.

        :param value: Lower-band vector.
        :return: None.
        """
        self._band_low_hz = np.asarray(value, dtype=np.float64)

    @property
    def band_high_hz(self) -> Vec:
        """
        Return the upper edge of the source band for each mode.

        :return: Upper-band vector in Hz.
        """
        return self._band_high_hz

    @band_high_hz.setter
    def band_high_hz(self, value: Vec) -> None:
        """
        Set the upper source-band vector.

        :param value: Upper-band vector.
        :return: None.
        """
        self._band_high_hz = np.asarray(value, dtype=np.float64)

    @property
    def selected_orders(self) -> IntVec:
        """
        Return the selected subspace order for each mode.

        :return: Integer vector of selected orders.
        """
        return self._selected_orders

    @selected_orders.setter
    def selected_orders(self, value: IntVec) -> None:
        """
        Set the selected-order vector.

        :param value: Integer order vector.
        :return: None.
        """
        self._selected_orders = np.asarray(value, dtype=np.int_)

    @property
    def observable_count_per_mode(self) -> IntVec:
        """
        Return how many channels participated in each mode estimate.

        :return: Integer vector with the number of observables per mode.
        """
        return self._observable_count_per_mode

    @observable_count_per_mode.setter
    def observable_count_per_mode(self, value: IntVec) -> None:
        """
        Set the per-mode observable-count vector.

        :param value: Integer observable-count vector.
        :return: None.
        """
        self._observable_count_per_mode = np.asarray(value, dtype=np.int_)

    def get_observable_names(self) -> List[str]:
        """
        Return the observable labels used during extraction.

        :return: List of observable names.
        """
        return list(self._observable_names)

    def get_eigenvalues(self) -> CxVec:
        """
        Backward-compatible accessor used by older callers.

        :return: Complex pole vector.
        """
        return self._eigenvalues_s

    def get_residues(self) -> CxMat:
        """
        Return the complex residue matrix.

        :return: Complex residue matrix.
        """
        return self._residues

    def get_modal_energy(self) -> Vec:
        """
        Return the relative modal-energy vector.

        :return: Modal-energy vector.
        """
        return self._modal_energy

    def mdl(self, result_type: ResultTypes) -> ResultsTable:
        """
        Export a VeraGrid ``ResultsTable`` view.

        :param result_type: Requested result type.
        :return: Results table for the GUI.
        """
        if result_type == ResultTypes.Modes:
            n_modes: int = int(self._eigenvalues_s.shape[0])
            index_labels: np.ndarray = np.array([f'Mode {index}' for index in range(n_modes)], dtype=np.str_)
            columns: np.ndarray = np.array([
                'Real (1/s)',
                'Imag (rad/s)',
                'Damping Ratio',
                'Freq [Hz]',
                'Modal Energy',
                'Stable',
                'Band Low [Hz]',
                'Band High [Hz]',
                'Selected Order',
                'Observables',
                'Recon Error',
            ], dtype=np.str_)
            table_data: Mat = build_modes_results_table_data(self)

            return ResultsTable(
                data=table_data,
                index=index_labels,
                columns=columns,
                title='ERA Identified Modes (S-Domain)',
                idx_device_type=DeviceType.NoDevice,
                cols_device_type=DeviceType.NoDevice,
            )
        elif result_type == ResultTypes.SDomainPlotHz:
            n_modes = int(self._eigenvalues_s.shape[0])
            plot_data: Mat = np.c_[self._eigenvalues_s.real, self._frequencies_hz]
            index_labels = np.array([f'Mode {index}' for index in range(n_modes)], dtype=np.str_)
            columns = np.array(['Real', 'Imag [Hz]'], dtype=np.str_)

            if self.plotting_allowed() and n_modes > 0:
                max_energy: float = float(np.max(self._modal_energy))

                if max_energy > 1e-15:
                    colors: Vec = self._modal_energy / max_energy
                else:
                    colors = np.ones(n_modes, dtype=np.float64)

                slope: float = 1.0 / 0.05
                x_reference: Vec = np.linspace(-200.0, 0.0, 400)
                y_reference: Vec = slope * x_reference / (2.0 * np.pi)

                plt.ion()
                figure = plt.figure(figsize=(8, 6))
                axis = figure.add_subplot(111)
                axis.plot(x_reference, y_reference, '--', color='grey', linewidth=0.7, alpha=0.6, label='zeta = 5%')
                axis.plot(x_reference, -y_reference, '--', color='grey', linewidth=0.7, alpha=0.6)
                axis.scatter(self._eigenvalues_s.real, self._frequencies_hz, c=colors, cmap='viridis', s=120, alpha=0.9)
                axis.set_xlabel('Real [1/s]')
                axis.set_ylabel('Imaginary [Hz]')
                axis.axhline(0.0, color='black', linewidth=1.0)
                axis.axvline(0.0, color='black', linewidth=1.0)
                axis.set_title('ERA Matrix Pencil S-Domain Plot in Hz')
                axis.grid(True, alpha=0.25)
                plt.tight_layout()
                plt.show()
            else:
                pass

            return ResultsTable(
                data=plot_data,
                index=index_labels,
                columns=columns,
                title='ERA Matrix Pencil S-Domain Plot in Hz',
                idx_device_type=DeviceType.NoDevice,
                cols_device_type=DeviceType.NoDevice,
            )
        else:
            return super().mdl(result_type)
