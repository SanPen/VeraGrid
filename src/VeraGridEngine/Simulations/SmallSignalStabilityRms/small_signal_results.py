# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import math
from typing import List

from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGridEngine.Simulations.results_template import ResultsTemplate, ResultsProperty
from VeraGridEngine.basic_structures import Vec, Mat, StrVec
from VeraGridEngine.enumerations import (StudyResultsType, ResultTypes, DeviceType,
                                         ResultTablePlotType)
from VeraGridEngine.Utils.Symbolic.symbolic import Var


def _normalize_result_matrix(values: Mat | Vec) -> Mat:
    """
    Normalize a result payload to the two-dimensional matrix contract.

    Empty result shells historically used ``np.empty(0)`` for matrix fields.
    A one-dimensional non-empty payload is treated as one matrix column so
    legacy or partially stored results remain inspectable.

    :param values: Matrix-like result payload.
    :return: Two-dimensional NumPy result matrix.
    """
    matrix: np.ndarray = np.asarray(values)
    if matrix.ndim == 1:
        if matrix.size == 0:
            matrix = matrix.reshape((0, 0))
        else:
            matrix = matrix.reshape((-1, 1))
    elif matrix.ndim == 2:
        pass
    else:
        raise ValueError(f"Result matrix must have one or two dimensions, got {matrix.ndim}")

    return matrix


def _build_s_domain_table(eigenvalues: Vec,
                          imaginary_scale: float,
                          imaginary_column_name: str) -> ResultsTable:
    """
    Build a selectable complex-plane table for small-signal eigenvalues.

    The table owns the plot semantics, so obtaining a results model remains a
    side-effect-free operation and plotting can honor subsequent filtering and
    row selection.

    :param eigenvalues: Small-signal eigenvalues in rad/s.
    :param imaginary_scale: Display scale applied to the imaginary component.
    :param imaginary_column_name: Label describing the displayed imaginary units.
    :return: Results table configured as a complex-point plot.
    """
    real_values: Vec = eigenvalues.real
    imaginary_values: Vec = eigenvalues.imag * imaginary_scale
    table_data: Mat = np.c_[real_values, imaginary_values]
    mode_names: StrVec = np.array(
        [f"Mode {mode_index}" for mode_index in range(len(eigenvalues))],
        dtype=np.str_,
    )
    return ResultsTable(
        data=table_data,
        index=mode_names,
        idx_device_type=DeviceType.NoDevice,
        columns=np.array(["Real", imaginary_column_name], dtype=np.str_),
        cols_device_type=DeviceType.NoDevice,
        title="S-Domain Stability plot",
        plot_type=ResultTablePlotType.COMPLEX_POINTS,
        damping_ratio_boundary=0.05,
        complex_plot_x_column="Real",
        complex_plot_y_columns=np.array([imaginary_column_name], dtype=np.str_),
        complex_plot_y_scales=np.array([imaginary_scale], dtype=float),
    )

class SmallSignalStabilityRmsResults(ResultsTemplate):
    """
    Small-signal Analysis results storage and visualization.
    """

    LOCAL_RESULTS_DECLARATIONS = (
        ResultsProperty(name='stat_vars_array', tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name='eigenvalues', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='participation_factors', tpe=Mat, old_names=list(), expandable=False),
        ResultsProperty(name='damping_ratios', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='conjugate_frequencies', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='state_matrix', tpe=Mat, old_names=list(), expandable=False),
        ResultsProperty(name='right_eigenvectors', tpe=Mat, old_names=list(), expandable=False),
    )
    __slots__ = [
        'stat_vars_array',
        'algebraic_vars_array',
        'eigenvalues',
        'participation_factors',
        'damping_ratios',
        'conjugate_frequencies',
        'state_matrix',
        'right_eigenvectors',
        'mode_shape'
    ]
    def __init__(self,
                 eigenvalues: Vec,
                 right_eigenvectors: Mat,
                 participation_factors: Mat,
                 damping_ratios: Vec,
                 conjugate_frequencies: Vec,
                 state_matrix: Mat,
                 stat_vars: List[Var],
                 algebraic_vars: List[Var])-> None:
        """
        Small-signal Analysis results
        :param eigenvalues:
        :param right_eigenvectors:
        :param participation_factors:
        :param damping_ratios:
        :param conjugate_frequencies:
        :param state_matrix:
        :param stat_vars:
        :param algebraic_vars:
        """
        available_list: list = list([
            ResultTypes.StateMatrix,
            ResultTypes.RightEigenvectors,
            ResultTypes.Modes,
            ResultTypes.ParticipationFactors,
        ])

        ResultsTemplate.__init__(
            self,
            name='Small Signal Stability',
            available_results=available_list,
            time_array=None,
            clustering_results=None,
            study_results_type=StudyResultsType.SmallSignalStability
        )

        stat_names_list: list = list()
        for i, var in enumerate(stat_vars):
            stat_names_list.append(f"{var}{i // 2 + 1}")

        algebraic_names_list: list = list()
        for i, var in enumerate(algebraic_vars):
            algebraic_names_list.append(f"{var}{i // 2 + 1}")


        self.stat_vars_array: Vec = np.array(stat_names_list, dtype=np.str_)
        self.algebraic_vars_array: Vec = np.array(algebraic_names_list, dtype=np.str_)
        # Result vectors and matrices retain a stable dimensional contract even
        # before a driver has produced modes or after an empty legacy load.
        self.eigenvalues: Vec = np.asarray(eigenvalues).reshape(-1)
        self.right_eigenvectors: Mat = _normalize_result_matrix(right_eigenvectors)
        self.participation_factors: Mat = _normalize_result_matrix(participation_factors)
        self.damping_ratios: Vec = np.asarray(damping_ratios).reshape(-1)
        self.conjugate_frequencies: Vec = np.asarray(conjugate_frequencies).reshape(-1)
        self.state_matrix: Mat = _normalize_result_matrix(state_matrix)

    def consolidate_after_loading(self) -> None:
        """
        Restore vector and matrix dimensional contracts after disk loading.

        :return: None.
        """
        self.eigenvalues = np.asarray(self.eigenvalues).reshape(-1)
        self.right_eigenvectors = _normalize_result_matrix(self.right_eigenvectors)
        self.participation_factors = _normalize_result_matrix(self.participation_factors)
        self.damping_ratios = np.asarray(self.damping_ratios).reshape(-1)
        self.conjugate_frequencies = np.asarray(self.conjugate_frequencies).reshape(-1)
        self.state_matrix = _normalize_result_matrix(self.state_matrix)


    def mdl(self, result_type: ResultTypes) -> ResultsTable:
        """
        Export the results as a ResultsTable for plotting.
        """
        if result_type == ResultTypes.StateMatrix:
            if self.state_matrix.size == 0:
                return ResultsTable(
                    data=np.empty((0, 0)),
                    index=np.empty(0, dtype=np.str_),
                    columns=np.empty(0, dtype=np.str_),
                    title="State Matrix",
                    idx_device_type=DeviceType.NoDevice,
                    cols_device_type=DeviceType.NoDevice
                )
            else:
                pass

            if len(self.stat_vars_array) == self.state_matrix.shape[0]:

                return ResultsTable(
                    data=self.state_matrix,
                    index=np.array([f"Equation {i}" for i in range(len(self.eigenvalues))], dtype=np.str_),
                    columns=np.array(self.stat_vars_array.astype(str), dtype=np.str_),
                    title="State Matrix",
                    idx_device_type=DeviceType.NoDevice,
                    cols_device_type=DeviceType.NoDevice
                )
            else:
                # TODO: adapt to generalized!
                return ResultsTable(
                    data=self.state_matrix,
                    index=np.array([f"Equation {i}" for i in range(len(self.eigenvalues))], dtype=np.str_),
                    columns=np.array(list(self.stat_vars_array.astype(str)) + list(self.algebraic_vars_array.astype(str)), dtype=np.str_),
                    title="State Matrix",
                    idx_device_type=DeviceType.NoDevice,
                    cols_device_type=DeviceType.NoDevice
                )


        elif result_type == ResultTypes.ParticipationFactors:

            if len(self.stat_vars_array) == self.participation_factors.shape[0]:

                return ResultsTable(
                    data=self.participation_factors,
                    index=np.array(self.stat_vars_array.astype(str), dtype=np.str_),
                    columns=np.array(
                        [
                            (
                                f"Mode {i}\nf={frequency:.3f} Hz"
                                if np.isfinite(frequency)
                                else f"Mode {i}"
                            )
                            for i, frequency in enumerate(self.conjugate_frequencies)
                        ],
                        dtype=np.str_
                    ),
                    title="Participation factors for each eigenvalue",
                    idx_device_type=DeviceType.NoDevice,
                    cols_device_type=DeviceType.NoDevice
                )
            else:
                return ResultsTable(
                    data=self.participation_factors,
                    index=np.array(list(self.stat_vars_array.astype(str)) + list(self.algebraic_vars_array.astype(str)), dtype=np.str_),
                    columns=np.array(
                        [
                            (
                                f"Mode {i}\nf={frequency:.3f} Hz"
                                if np.isfinite(frequency)
                                else f"Mode {i}"
                            )
                            for i, frequency in enumerate(self.conjugate_frequencies)
                        ],
                        dtype=np.str_
                    ),
                    title="Participation factors for each eigenvalue",
                    idx_device_type=DeviceType.NoDevice,
                    cols_device_type=DeviceType.NoDevice
                )

        elif result_type == ResultTypes.Modes:
            re: Vec = self.eigenvalues.real
            im: Vec = self.eigenvalues.imag
            im_hz: Vec = im / (2.0 * math.pi)
            data_modes: Mat = np.c_[
                re,
                im,
                im_hz,
                self.damping_ratios,
                self.conjugate_frequencies,
            ]
            return ResultsTable(
                data=data_modes,
                index=np.array([f"Mode {i}" for i in range(len(self.eigenvalues))], dtype=np.str_),
                columns=np.array(
                    [
                        "Real",
                        "Imaginary [rad/s]",
                        "Imaginary [Hz]",
                        "Damping ratio",
                        "Oscillation frequency",
                    ],
                    dtype=np.str_,
                ),
                title="Eigenvalues",
                idx_device_type=DeviceType.NoDevice,
                cols_device_type=DeviceType.NoDevice,
                plot_type=ResultTablePlotType.COMPLEX_POINTS,
                damping_ratio_boundary=0.05,
                plot_title="S-Domain Stability plot",
                complex_plot_x_column="Real",
                complex_plot_y_columns=np.array(
                    ["Imaginary [rad/s]", "Imaginary [Hz]"],
                    dtype=np.str_,
                ),
                complex_plot_y_scales=np.array(
                    [1.0, 1.0 / (2.0 * math.pi)],
                    dtype=float,
                ),
            )
        elif result_type == ResultTypes.RightEigenvectors:
            number_of_states: int = self.right_eigenvectors.shape[0]
            number_of_modes: int = self.right_eigenvectors.shape[1]

            if number_of_modes != len(self.eigenvalues):
                raise ValueError(
                    "The number of right-eigenvector columns must match "
                    "the number of eigenvalues."
                )

            if len(self.stat_vars_array) == number_of_states:
                state_names: np.ndarray = np.array(
                    self.stat_vars_array.astype(str),
                    dtype=np.str_
                )
            else:
                state_names = np.array(
                    list(self.stat_vars_array.astype(str))
                    + list(self.algebraic_vars_array.astype(str)),
                    dtype=np.str_
                )

            if len(state_names) != number_of_states:
                raise ValueError(
                    "The number of state names does not match the number "
                    "of right-eigenvector rows."
                )

            mode_names: np.ndarray = np.array(
                [
                    (
                        f"Mode {i}\nf={frequency:.3f} Hz"
                        if np.isfinite(frequency)
                        else f"Mode {i}"
                    )
                    for i, frequency in enumerate(self.conjugate_frequencies)
                ],
                dtype=np.str_
            )

            return ResultsTable(
                data=self.right_eigenvectors,
                index=state_names,
                columns=mode_names,
                title="Mode shapes",
                idx_device_type=DeviceType.NoDevice,
                cols_device_type=DeviceType.NoDevice,
                plot_type=ResultTablePlotType.COMPLEX_VECTORS,
            )



        elif result_type == ResultTypes.SDomainPlot:
            return _build_s_domain_table(
                eigenvalues=self.eigenvalues,
                imaginary_scale=1.0,
                imaginary_column_name="Imaginary [rad/s]",
            )
        elif result_type == ResultTypes.SDomainPlotHz:
            return _build_s_domain_table(
                eigenvalues=self.eigenvalues,
                imaginary_scale=1.0 / (2.0 * math.pi),
                imaginary_column_name="Imaginary [Hz]",
            )
        else:
            raise Exception(f"Result type not understood: {result_type}")
