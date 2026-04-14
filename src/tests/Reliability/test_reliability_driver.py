# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import pytest

from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.Reliability.reliability_driver import ReliabilityStudyDriver, count_device_incidences
from VeraGridEngine.enumerations import ReliabilityMode, ResultTypes


def build_no_failure_grid(n_customers: int) -> MultiCircuit:
    """
    Build a minimal two-bus system where no device can fail.
    This keeps the reliability run deterministic while exercising the real driver.
    """
    grid = MultiCircuit(name="reliability-test-grid")

    bus_slack = Bus(name="Slack")
    bus_slack.is_slack = True
    grid.add_bus(obj=bus_slack)

    bus_load = Bus(name="Load")
    grid.add_bus(obj=bus_load)

    grid.add_generator(
        bus=bus_slack,
        api_obj=Generator(
            name="G1",
            P=20.0,
            Pmax=50.0,
            Snom=50.0,
            enabled_dispatch=True,
            mttf=0.0,
            mttr=0.0,
        ),
    )

    grid.add_load(
        bus=bus_load,
        api_obj=Load(
            name="L1",
            P=10.0,
            Q=2.0,
            n_customers=n_customers,
            mttf=0.0,
            mttr=0.0,
        ),
    )

    grid.add_line(
        obj=Line(
            name="Line 1-2",
            bus_from=bus_slack,
            bus_to=bus_load,
            r=0.01,
            x=0.05,
            rate=100.0,
            mttf=0.0,
            mttr=0.0,
        )
    )

    grid.create_profiles(steps=3, step_length=1, step_unit="h")

    return grid


@pytest.mark.parametrize(
    "active_states, expected",
    [
        (
            np.array(
                [
                    [True, True, True],
                    [True, True, True],
                    [True, True, True],
                ],
                dtype=bool,
            ),
            0,
        ),
        (
            np.array(
                [
                    [False, True, False],
                    [False, True, True],
                    [True, True, True],
                ],
                dtype=bool,
            ),
            2,
        ),
        (
            np.array(
                [
                    [True, True],
                    [False, True],
                    [False, False],
                    [True, False],
                    [False, True],
                ],
                dtype=bool,
            ),
            3,
        ),
    ],
)
def test_count_device_incidences(active_states: np.ndarray, expected: int) -> None:
    assert count_device_incidences(active_states) == expected


@pytest.mark.parametrize("n_customers", [0, 10])
def test_grid_reliability_with_no_failures_keeps_all_metrics_zero(n_customers: int) -> None:
    grid = build_no_failure_grid(n_customers=n_customers)
    driver = ReliabilityStudyDriver(
        grid=grid,
        pf_options=PowerFlowOptions(),
        reliability_mode=ReliabilityMode.GridMetrics,
        n_sim=3,
    )

    driver.run_grid_reliability()

    assert np.allclose(driver.results.LOLE_evolution, 0.0)
    assert np.allclose(driver.results.ENS_evolution, 0.0)
    assert np.allclose(driver.results.LOLF_evolution, 0.0)
    assert np.allclose(driver.results.LOLET_evolution, 0.0)
    assert np.allclose(driver.results.LOLFT_evolution, 0.0)
    assert np.allclose(driver.results.SAIDI_evolution, 0.0)
    assert np.allclose(driver.results.SAIFI_evolution, 0.0)
    assert np.allclose(driver.results.CAIDI_evolution, 0.0)

    assert np.allclose(driver.results.mdl(ResultTypes.ReliabilitySAIDIResults).data_c, 0.0)
    assert np.allclose(driver.results.mdl(ResultTypes.ReliabilitySAIFIResults).data_c, 0.0)
    assert np.allclose(driver.results.mdl(ResultTypes.ReliabilityCAIDIResults).data_c, 0.0)


def test_adequacy_reliability_with_no_failures_keeps_lole_zero() -> None:
    grid = build_no_failure_grid(n_customers=10)
    driver = ReliabilityStudyDriver(
        grid=grid,
        pf_options=PowerFlowOptions(),
        reliability_mode=ReliabilityMode.GenerationAdequacy,
        n_sim=3,
    )

    driver.run_adequacy_reliability()

    assert np.allclose(driver.results.LOLE_evolution, 0.0)
