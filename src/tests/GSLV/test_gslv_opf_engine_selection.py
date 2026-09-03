# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import numpy as np
import pytest

import VeraGridEngine.api as vg
from VeraGridEngine.Compilers.Gslv.activation import GSLV_AVAILABLE
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import EngineType, LogSeverity, SolverType
from VeraGridEngine.Simulations.OPF.opf_driver import OptimalPowerFlowDriver
from VeraGridEngine.Simulations.OPF.opf_options import OptimalPowerFlowOptions
from VeraGridEngine.Simulations.OPF.opf_ts_driver import OptimalPowerFlowTimeSeriesDriver


class _GslvResultStub:
    """Provide the bounded result surface consumed by snapshot OPF dispatch."""

    __slots__ = (
        "voltage",
        "Sbus",
        "bus_shadow_prices",
        "load_power",
        "load_shedding",
        "load_shedding_cost",
        "battery_power",
        "generator_power",
        "generator_reactive_power",
        "Sf",
        "St",
        "overloads",
        "overloads_cost",
        "loading",
        "losses",
        "tap_angle",
        "tap_module",
        "hvdc_Pf",
        "hvdc_loading",
        "vsc_Pf",
        "vsc_loading",
        "shunt_like_reactive_power",
        "fluid_node_current_level",
        "fluid_node_flow_in",
        "fluid_node_flow_out",
        "fluid_node_p2x_flow",
        "fluid_node_spillage",
        "fluid_path_flow",
        "fluid_injection_flow",
        "converged",
        "error_values",
    )

    def __init__(self, grid: MultiCircuit) -> None:
        """Initialize exactly the arrays read by ``OptimalPowerFlowDriver``.

        :param grid: Network that determines every result-array dimension.
        :return: None.
        """
        branch_count: int = grid.get_branch_number(
            add_hvdc=False,
            add_vsc=False,
            add_switch=True,
        )
        self.voltage: np.ndarray = np.zeros(
            (1, grid.get_bus_number()),
            dtype=np.complex128,
        )
        self.Sbus: np.ndarray = np.zeros(
            (1, grid.get_bus_number()),
            dtype=np.complex128,
        )
        self.bus_shadow_prices: np.ndarray = np.zeros(
            (1, grid.get_bus_number()),
            dtype=float,
        )
        self.load_power: np.ndarray = np.zeros(
            (1, grid.get_loads_number()),
            dtype=float,
        )
        self.load_shedding: np.ndarray = np.zeros(
            (1, grid.get_loads_number()),
            dtype=float,
        )
        self.load_shedding_cost: np.ndarray = np.zeros(
            (1, grid.get_loads_number()),
            dtype=float,
        )
        self.battery_power: np.ndarray = np.zeros(
            (1, grid.get_batteries_number()),
            dtype=float,
        )
        self.generator_power: np.ndarray = np.zeros(
            (1, grid.get_generators_number()),
            dtype=float,
        )
        self.generator_reactive_power: np.ndarray = np.zeros(
            (1, grid.get_generators_number()),
            dtype=float,
        )
        self.Sf: np.ndarray = np.zeros((1, branch_count), dtype=np.complex128)
        self.St: np.ndarray = np.zeros((1, branch_count), dtype=np.complex128)
        self.overloads: np.ndarray = np.zeros((1, branch_count), dtype=np.complex128)
        self.overloads_cost: np.ndarray = np.zeros((1, branch_count), dtype=float)
        self.loading: np.ndarray = np.zeros((1, branch_count), dtype=np.complex128)
        self.losses: np.ndarray = np.zeros((1, branch_count), dtype=float)
        self.tap_angle: np.ndarray = np.zeros((1, branch_count), dtype=float)
        self.tap_module: np.ndarray = np.zeros((1, branch_count), dtype=float)
        self.hvdc_Pf: np.ndarray = np.zeros((1, grid.get_hvdc_number()), dtype=float)
        self.hvdc_loading: np.ndarray = np.zeros((1, grid.get_hvdc_number()), dtype=float)
        self.vsc_Pf: np.ndarray = np.zeros((1, grid.get_vsc_number()), dtype=float)
        self.vsc_loading: np.ndarray = np.zeros((1, grid.get_vsc_number()), dtype=float)
        self.shunt_like_reactive_power: np.ndarray = np.zeros(
            (1, grid.get_shunt_like_device_number()),
            dtype=float,
        )
        self.fluid_node_current_level: np.ndarray = np.zeros(
            (1, grid.get_fluid_nodes_number()),
            dtype=float,
        )
        self.fluid_node_flow_in: np.ndarray = np.zeros(
            (1, grid.get_fluid_nodes_number()),
            dtype=float,
        )
        self.fluid_node_flow_out: np.ndarray = np.zeros(
            (1, grid.get_fluid_nodes_number()),
            dtype=float,
        )
        self.fluid_node_p2x_flow: np.ndarray = np.zeros(
            (1, grid.get_fluid_nodes_number()),
            dtype=float,
        )
        self.fluid_node_spillage: np.ndarray = np.zeros(
            (1, grid.get_fluid_nodes_number()),
            dtype=float,
        )
        self.fluid_path_flow: np.ndarray = np.zeros(
            (1, grid.get_fluid_paths_number()),
            dtype=float,
        )
        self.fluid_injection_flow: np.ndarray = np.zeros(
            (1, grid.get_fluid_injection_number()),
            dtype=float,
        )
        self.converged: np.ndarray = np.ones(1, dtype=np.uint64)
        self.error_values: np.ndarray = np.zeros(1, dtype=float)


class _GslvSnapshotDriverStub(OptimalPowerFlowDriver):
    """Record public GSLV snapshot dispatch without patching module state."""

    __slots__ = ("_gslv_called",)

    def __init__(
            self,
            grid: MultiCircuit,
            options: OptimalPowerFlowOptions,
            engine: EngineType,
    ) -> None:
        """Initialize the real driver with one instance-owned dispatch flag.

        :param grid: Network passed through the production driver path.
        :param options: Snapshot OPF options under test.
        :param engine: Requested execution engine.
        :return: None.
        """
        super().__init__(grid=grid, options=options, engine=engine)
        self._gslv_called: bool = False

    def get_gslv_called(self) -> bool:
        """Return whether the production dispatcher selected GSLV.

        :return: ``True`` after ``run_gslv_opf`` is invoked.
        """
        return self._gslv_called

    def run_gslv_opf(self) -> _GslvResultStub:
        """Return a typed bounded result after recording GSLV dispatch.

        :return: Result surface consumed by the production snapshot driver.
        """
        self._gslv_called = True
        return _GslvResultStub(grid=self.grid)


class _TimeSeriesDriverStub(OptimalPowerFlowTimeSeriesDriver):
    """Record native time-series fallback without patching module state."""

    __slots__ = ("_native_opf_called",)

    def __init__(
            self,
            grid: MultiCircuit,
            options: OptimalPowerFlowOptions,
            engine: EngineType,
    ) -> None:
        """Initialize the real driver with an instance-owned fallback flag.

        :param grid: Network passed through the production driver path.
        :param options: Time-series OPF options under test.
        :param engine: Requested execution engine.
        :return: None.
        """
        super().__init__(grid=grid, options=options, engine=engine)
        self._native_opf_called: bool = False

    def get_native_opf_called(self) -> bool:
        """Return whether the native time-series fallback executed.

        :return: ``True`` after the production dispatcher calls ``opf``.
        """
        return self._native_opf_called

    def opf(self) -> None:
        """Record the native fallback selected by the production dispatcher.

        :return: None.
        """
        self._native_opf_called = True


def get_warning_messages(
        driver: OptimalPowerFlowDriver | OptimalPowerFlowTimeSeriesDriver,
) -> list[str]:
    """
    Collect warning messages from a driver logger.

    :param driver: Driver instance with a logger.
    :return: List of warning messages.
    """
    return [
        entry.msg
        for entry in driver.logger.entries
        if entry.severity == LogSeverity.Warning
    ]


def require_gslv() -> None:
    """Skip the current test when the optional GSLV backend is unavailable.

    :return: None.
    """

    if not GSLV_AVAILABLE:
        pytest.skip("GSLV is not installed or licensed")
    else:
        pass


def test_gslv_snapshot_linear_opf_uses_gslv() -> None:
    """
    Snapshot linear OPF must dispatch to the GSLV implementation.
    """
    require_gslv()
    grid = vg.open_file(filename=os.path.join('data', 'grids', 'case14.gridcal'))
    options = vg.OptimalPowerFlowOptions(solver=SolverType.LINEAR_OPF)
    driver: _GslvSnapshotDriverStub = _GslvSnapshotDriverStub(
        grid=grid,
        options=options,
        engine=vg.EngineType.GSLV,
    )

    driver.run()

    assert driver.get_gslv_called()
    assert driver.engine == vg.EngineType.GSLV
    assert "GSLV OPF snapshot only supports LINEAR_OPF, falling back to VeraGrid" not in get_warning_messages(driver)


def test_gslv_snapshot_nonlinear_opf_uses_gslv() -> None:
    """
    Snapshot non-linear OPF must dispatch to the GSLV implementation.
    """
    require_gslv()
    grid = vg.open_file(filename=os.path.join('data', 'grids', 'case14.gridcal'))
    options = vg.OptimalPowerFlowOptions(solver=SolverType.NONLINEAR_OPF)
    driver: _GslvSnapshotDriverStub = _GslvSnapshotDriverStub(
        grid=grid,
        options=options,
        engine=vg.EngineType.GSLV,
    )

    driver.run()

    assert driver.get_gslv_called()
    assert driver.engine == vg.EngineType.GSLV
    assert "GSLV OPF snapshot only supports LINEAR_OPF and NONLINEAR_OPF, falling back to VeraGrid" not in (
        get_warning_messages(driver)
    )


def test_gslv_nonlinear_opf_ts_falls_back_to_veragrid() -> None:
    """
    GSLV time-series OPF must fall back for non-linear OPF.
    """
    require_gslv()
    grid = vg.open_file(filename=os.path.join('data', 'grids', 'case14.gridcal'))
    options = vg.OptimalPowerFlowOptions(solver=SolverType.NONLINEAR_OPF)
    driver: _TimeSeriesDriverStub = _TimeSeriesDriverStub(
        grid=grid,
        options=options,
        engine=vg.EngineType.GSLV,
    )

    driver.run()

    assert driver.get_native_opf_called()
    assert driver.engine == vg.EngineType.VeraGrid
    assert "GSLV OPF time series only supports LINEAR_OPF, falling back to VeraGrid" in get_warning_messages(driver)
