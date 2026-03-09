# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
from matplotlib import pyplot as plt
from typing import List, Tuple

from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGridEngine.Simulations.results_template import ResultsTemplate
from VeraGridEngine.basic_structures import Vec, Mat, CxVec, CxMat, BoolVec
from VeraGridEngine.enumerations import StudyResultsType, ResultTypes, DeviceType
from VeraGridEngine.Utils.Symbolic.symbolic import Var


class SmallSignalStabilityEmtResults(ResultsTemplate):
    """
    Container and processor for EMT Floquet Small-Signal Stability results.

    Handles the mapping of discrete Floquet multipliers (Z-domain) to continuous
    eigenvalues (S-domain), computes bi-orthonormal participation factors,
    and interfaces with the VeraGrid UI for plotting and reporting.

    EmtFloquetResults
    :param multipliers: Floquet multipliers (eigenvalues of Monodromy Matrix)
    :param right_vecs: Right eigenvectors (columns)
    :param left_vecs: Left eigenvectors from adjoint problem (columns)
    :param period: Cycle period T (s)
    :param stat_vars: List of state variables
    """

    def __init__(self,
                 multipliers: CxVec,
                 right_vecs: CxMat,
                 left_vecs: CxMat,
                 period: float,
                 stat_vars: List[Var]):
        """
        Initializes the container results.

        :param multipliers: Floquet multipliers (eigenvalues of Monodromy Matrix).
        :param right_vecs: Right eigenvectors (columns) of the Monodromy Matrix.
        :param left_vecs: Left eigenvectors from the adjoint problem (columns).
        :param period: Limit cycle period T in seconds.
        :param stat_vars: List of symbolic state variables involved in the modes.
        """

        ResultsTemplate.__init__(
            self,
            name='Small Signal Stability Emt Results',
            available_results=[
                ResultTypes.Modes,
                ResultTypes.ParticipationFactors,
                ResultTypes.SDomainPlot,
                ResultTypes.SDomainPlotHz
            ],
            time_array=None,
            clustering_results=None,
            study_results_type=StudyResultsType.SmallSignalStability
        )

        self.multipliers = multipliers
        self.right_vecs = right_vecs
        self.left_vecs = left_vecs
        self.period = period
        self.stat_vars = stat_vars

        # Map Discrete Multipliers (Z) to Floquet Exponents (S)
        self.eigenvalues = np.log(self.multipliers.astype(complex)) / self.period

        # Periodic averaged modal properties
        alpha = self.eigenvalues.real
        beta = self.eigenvalues.imag
        self.damping_ratios = -alpha / np.sqrt(alpha ** 2 + beta ** 2 + 1e-15)
        self.conjugate_frequencies = np.abs(beta) / (2.0 * np.pi)

        # Internal computation of bi-orthonormal Participation Factors
        self.participation_factors = self._compute_pf()

        stat_names = [f"{v}" for v in stat_vars]
        self.stat_vars_array = np.array(stat_names, dtype=np.str_)

        self.register(name='multipliers', tpe=CxVec)
        self.register(name='eigenvalues', tpe=CxVec)
        self.register(name='participation_factors', tpe=Mat)

    def _compute_pf(self) -> Mat:
        """
        Calculates bi-orthonormal Participation Factors.

        Uses the left (adjoint) and right eigenvectors to compute the relative
        participation of each state variable in each Floquet mode.

        :return: A real-valued matrix of shape (n_states, n_modes).
        """

        n_states, n_modes = self.right_vecs.shape
        PF = np.zeros((n_states, n_modes), dtype=np.float64)

        for i in range(n_modes):
            # Normalization: l_i^H * r_i = 1.0
            norm_val = np.dot(self.left_vecs[:, i].conj().T, self.right_vecs[:, i])
            if np.abs(norm_val) > 1e-15:
                l_norm = self.left_vecs[:, i] / norm_val
                # PF_ki = Re(r_ki * l_ik)
                PF[:, i] = np.abs(self.right_vecs[:, i] * l_norm)

        # Mode-wise normalization
        col_sums = np.sum(PF, axis=0)
        mask = col_sums > 1e-15
        PF[:, mask] /= col_sums[mask]
        return PF

    def mdl(self, result_type: ResultTypes) -> ResultsTable:
        """Export results as ResultsTable for the VeraGrid UI/Engine."""
        if result_type == ResultTypes.ParticipationFactors:
            return ResultsTable(
                data=self.participation_factors,
                index=self.stat_vars_array,
                columns=np.array([f"Mode {i}" for i in range(len(self.multipliers))], dtype=np.str_),
                title="Floquet Participation Factors",
                idx_device_type=DeviceType.NoDevice,
                cols_device_type=DeviceType.NoDevice
            )
        elif result_type == ResultTypes.Modes:
            data = np.c_[self.multipliers.real, self.multipliers.imag, np.abs(self.multipliers),
            self.damping_ratios, self.conjugate_frequencies]
            return ResultsTable(
                data=data,
                index=np.array([f"Mode {i}" for i in range(len(self.multipliers))], dtype=np.str_),
                columns=np.array(["Mu Re", "Mu Im", "|Mu|", "Damp Ratio", "Freq [Hz]"]),
                title="Floquet Stability Multipliers",
                idx_device_type=DeviceType.NoDevice,
                cols_device_type=DeviceType.NoDevice
            )
        elif result_type == ResultTypes.SDomainPlot:
            if self.plotting_allowed():
                plt.figure(figsize=(6, 6))
                th = np.linspace(0, 2 * np.pi, 100)
                plt.plot(np.cos(th), np.sin(th), 'k--', alpha=0.4, label='Unit Circle')
                plt.scatter(self.multipliers.real, self.multipliers.imag, color='red', marker='x', s=80)
                plt.xlabel("Real(mu)")
                plt.ylabel("Imag(mu)")
                plt.axis('equal')
                plt.grid(True)
                plt.title("Floquet Multipliers: Unit Circle Stability")
                plt.show()

            row_indices = np.arange(len(self.multipliers))

            return ResultsTable(data=np.c_[self.multipliers.real, self.multipliers.imag],
                                columns=np.array(['Real', 'Imag']),
                                title="Z-Domain Plot"
                                ,index=row_indices
                                ,cols_device_type=DeviceType.NoDevice
                                ,idx_device_type=DeviceType.NoDevice )
        return super().mdl(result_type)

    def report_stability(self)-> str:
        """
        Generates a standard stability report string based on the spectral radius.

        :return: Formatted stability assessment string.
        """
        rho = np.max(np.abs(self.multipliers))
        return f"Spectral Radius rho={rho:.4f}. {'STABLE' if rho <= 1.0001 else 'UNSTABLE'}."

    def validate_spectral_gaps(self, h_step:float)->Tuple[BoolVec, Vec]:
        """
        Evaluates the metric compactness of ALL calculated modes.
        Uses the discretization step (h) as the numerical noise floor (tolerance).

        :param h_step: Problem integration step (e.g., 1e-4)
        :return: Tuple (is_isolated_array, spectral_gaps_array)
        """
        if self.multipliers is None or len(self.multipliers) == 0:
            return np.array([]), np.array([])

        n_modes = len(self.multipliers)
        is_isolated = np.zeros(n_modes, dtype=bool)
        spectral_gaps = np.full(n_modes, np.inf)

        for i in range(n_modes):
            mu_target = self.multipliers[i]
            distances = np.abs(self.multipliers - mu_target)

            valid_distances = []
            for j in range(n_modes):
                if i == j:
                    continue
                if np.allclose(self.multipliers[j], np.conj(mu_target), atol=1e-10):
                    continue
                valid_distances.append(distances[j])

            if valid_distances:
                gap = np.min(valid_distances)
                spectral_gaps[i] = gap
                # COMPACTNESS CRITERION: The separation must exceed the discretization error h.
                is_isolated[i] = gap > h_step
            else:
                is_isolated[i] = True

        return is_isolated, spectral_gaps