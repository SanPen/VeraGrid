# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import numpy as np
from sklearn.neighbors import KNeighborsRegressor

from VeraGridEngine.Simulations.Stochastic.latin_hypercube_sampling import lhs
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import CDF, CxVec, CxMat


class StochasticPowerFlowInput:
    """
    StochasticPowerFlowInput
    """

    __slots__ = (
        "n",
        "Scdf_fixed",
        "regression_model",
        "_has_profile_samples",
    )

    def __init__(self, grid: MultiCircuit) -> None:
        """
        Build the stochastic power flow input sampler.

        :param grid: MultiCircuit instance.
        """

        # The number of buses determines the number of stochastic coordinates
        # that every generated operating point must contain.
        self.n: int = grid.get_bus_number()

        # The fixed and dispatchable time-series matrices are sampled together
        # because the regression model learns how dispatchable injections track
        # the fixed net demand profile.
        Sprof_fixed: CxMat = grid.get_Sbus_prof_fixed()
        Sprof_dispatcheable: CxMat = grid.get_Sbus_prof_dispatchable()

        # The bus axis must remain aligned with the network size. This check is
        # kept explicit because older bugs produced mismatched profile shapes.
        assert Sprof_fixed.shape[1] == self.n

        # The stochastic study needs at least one time-series row. When there
        # are no rows, the object stays in a non-sampleable state so callers
        # can stop cleanly instead of reaching a scikit-learn validation error.
        self._has_profile_samples: bool = Sprof_fixed.shape[0] > 0

        if self._has_profile_samples:
            # Each bus gets its own empirical distribution so the sampled fixed
            # injections preserve the marginal distribution of the input data.
            self.Scdf_fixed: list[CDF] = list()
            for bus_index in range(self.n):
                self.Scdf_fixed.append(CDF(Sprof_fixed[:, bus_index]))

            # The regression model reconstructs the dispatchable contribution
            # from the sampled fixed demand profile for each Monte Carlo point.
            self.regression_model: KNeighborsRegressor | None = KNeighborsRegressor(n_neighbors=4)
            self.regression_model.fit(Sprof_fixed.real, Sprof_dispatcheable.real)
        else:
            self.Scdf_fixed = list()
            self.regression_model = None

    def has_profile_samples(self) -> bool:
        """
        Check whether the input contains at least one time-series sample.

        :return: ``True`` when stochastic samples can be generated.
        """
        return self._has_profile_samples

    def get(self, n_samples: int = 0, use_latin_hypercube: bool = False) -> CxMat:
        """
        Generate stochastic samples for the grid injections.

        :param n_samples: number of samples
        :param use_latin_hypercube: use Latin Hypercube to sample
        :return: CxMat (p.u.)
        """
        if n_samples == 0:
            raise Exception('Cannot have zero samples :(')
        else:
            pass

        if self.has_profile_samples():
            pass
        else:
            raise ValueError('Stochastic power flow requires at least one time-series sample.')

        if use_latin_hypercube:

            lhs_points: np.ndarray = lhs(self.n, samples=n_samples, criterion='center')
            S_fixed: CxMat = np.zeros((n_samples, self.n), dtype=complex)
            for i in range(self.n):
                if self.Scdf_fixed[i] is not None:
                    S_fixed[:, i] = self.Scdf_fixed[i].get_at(lhs_points[:, i])
                else:
                    pass

        else:
            S_fixed = np.zeros((n_samples, self.n), dtype=complex)

            for i in range(self.n):
                if self.Scdf_fixed[i] is not None:
                    S_fixed[:, i] = self.Scdf_fixed[i].get_sample(n_samples)
                else:
                    pass

        if self.regression_model is not None:
            # The dispatchable injections are inferred from the fixed demand
            # sample so the generated operating point preserves the empirical
            # dependence observed in the input profiles.
            S_dispatchable: np.ndarray = self.regression_model.predict(S_fixed.real)
        else:
            raise ValueError('Stochastic power flow regression model is not available.')

        # The generated dispatchable production is rescaled so that each sample
        # balances the sampled fixed demand at system level.
        for t in range(S_fixed.shape[0]):

            demand: float = -S_fixed[t, :].sum().real
            generation: float = S_dispatchable[t, :].sum()

            factor: float = demand / generation
            S_dispatchable[t, :] *= factor

        return S_fixed + S_dispatchable

    def get_at(self, x: np.ndarray) -> CxVec:
        """
        Get samples at x
        :param x: values in [0, 1] to sample the CDF
        :return: CxVec
        """
        S: CxVec = np.zeros(self.n, dtype=complex)

        for i in range(self.n):
            if self.Scdf_fixed[i] is not None:
                S[i] = self.Scdf_fixed[i].get_at(x[i])
            else:
                pass

        return S

    def __call__(self, samples: int = 0, use_latin_hypercube: bool = False) -> CxMat:
        """
        Proxy the object call to :meth:`get`.

        :param samples: Number of samples to generate.
        :param use_latin_hypercube: Whether to use Latin Hypercube sampling.
        :return: Generated stochastic injections.
        """
        return self.get(n_samples=samples, use_latin_hypercube=use_latin_hypercube)
