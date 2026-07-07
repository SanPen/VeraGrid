# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
import pytest

from VeraGridEngine.Simulations.Stochastic.stochastic_power_flow_input import StochasticPowerFlowInput


class DummyGridForStochasticInput:
    """
    Minimal grid stub for stochastic input validation tests.
    """

    __slots__ = (
        "_fixed_profiles",
        "_dispatchable_profiles",
    )

    def __init__(self, fixed_profiles: np.ndarray, dispatchable_profiles: np.ndarray) -> None:
        """
        Build the dummy grid used by the stochastic input tests.

        :param fixed_profiles: Fixed complex power profiles.
        :param dispatchable_profiles: Dispatchable complex power profiles.
        """
        self._fixed_profiles: np.ndarray = fixed_profiles
        self._dispatchable_profiles: np.ndarray = dispatchable_profiles

    def get_bus_number(self) -> int:
        """
        Get the number of buses represented by the dummy grid.

        :return: Number of buses.
        """
        return self._fixed_profiles.shape[1]

    def get_Sbus_prof_fixed(self) -> np.ndarray:
        """
        Get the fixed bus power profiles.

        :return: Fixed complex power profiles.
        """
        return self._fixed_profiles

    def get_Sbus_prof_dispatchable(self) -> np.ndarray:
        """
        Get the dispatchable bus power profiles.

        :return: Dispatchable complex power profiles.
        """
        return self._dispatchable_profiles


def test_stochastic_input_detects_missing_profile_samples() -> None:
    """
    Verify that stochastic input construction stays safe when the grid has no
    time-series rows.

    :return: ``None``.
    """
    fixed_profiles: np.ndarray = np.zeros((0, 3), dtype=complex)
    dispatchable_profiles: np.ndarray = np.zeros((0, 3), dtype=complex)
    grid: DummyGridForStochasticInput = DummyGridForStochasticInput(
        fixed_profiles=fixed_profiles,
        dispatchable_profiles=dispatchable_profiles,
    )

    stochastic_input: StochasticPowerFlowInput = StochasticPowerFlowInput(grid=grid)

    assert stochastic_input.has_profile_samples() is False

    with pytest.raises(ValueError, match='at least one time-series sample'):
        stochastic_input.get(n_samples=10, use_latin_hypercube=True)
