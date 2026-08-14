# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import numpy as np

import VeraGridEngine.api as vg
from VeraGridEngine.enumerations import LogSeverity, SolverType
import VeraGridEngine.Simulations.OPF.opf_driver as opf_driver_module
from VeraGridEngine.Simulations.OPF.opf_driver import OptimalPowerFlowDriver
from VeraGridEngine.Simulations.OPF.opf_ts_driver import OptimalPowerFlowTimeSeriesDriver


def get_warning_messages(driver) -> list[str]:
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


def test_gslv_snapshot_linear_opf_uses_gslv(monkeypatch) -> None:
    """
    Snapshot linear OPF must dispatch to the GSLV implementation.
    """
    grid = vg.open_file(filename=os.path.join('data', 'grids', 'case14.gridcal'))
    options = vg.OptimalPowerFlowOptions(solver=SolverType.LINEAR_OPF)
    driver = OptimalPowerFlowDriver(grid=grid, options=options, engine=vg.EngineType.GSLV)
    state = dict()

    class ResultStub:
        """
        Minimal GSLV OPF result stub for snapshot dispatch testing.
        """
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

    def fake_gslv_opf(circuit, opf_options, time_series, time_indices, logger):
        """
        Record the GSLV OPF dispatch and return a minimal result object.
        """
        result = ResultStub()
        state["called"] = True
        result.voltage = np.zeros((1, grid.get_bus_number()), dtype=np.complex128)
        result.Sbus = np.zeros((1, grid.get_bus_number()), dtype=np.complex128)
        result.bus_shadow_prices = np.zeros((1, grid.get_bus_number()), dtype=float)
        result.load_power = np.zeros((1, grid.get_loads_number()), dtype=float)
        result.load_shedding = np.zeros((1, grid.get_loads_number()), dtype=float)
        result.load_shedding_cost = np.zeros((1, grid.get_loads_number()), dtype=float)
        result.battery_power = np.zeros((1, grid.get_batteries_number()), dtype=float)
        result.generator_power = np.zeros((1, grid.get_generators_number()), dtype=float)
        result.generator_reactive_power = np.zeros((1, grid.get_generators_number()), dtype=float)
        result.Sf = np.zeros((1, grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True)), dtype=np.complex128)
        result.St = np.zeros((1, grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True)), dtype=np.complex128)
        result.overloads = np.zeros((1, grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True)), dtype=np.complex128)
        result.overloads_cost = np.zeros((1, grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True)), dtype=float)
        result.loading = np.zeros((1, grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True)), dtype=np.complex128)
        result.losses = np.zeros((1, grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True)), dtype=float)
        result.tap_angle = np.zeros((1, grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True)), dtype=float)
        result.tap_module = np.zeros((1, grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True)), dtype=float)
        result.hvdc_Pf = np.zeros((1, grid.get_hvdc_number()), dtype=float)
        result.hvdc_loading = np.zeros((1, grid.get_hvdc_number()), dtype=float)
        result.vsc_Pf = np.zeros((1, grid.get_vsc_number()), dtype=float)
        result.vsc_loading = np.zeros((1, grid.get_vsc_number()), dtype=float)
        result.shunt_like_reactive_power = np.zeros((1, grid.get_shunt_like_device_number()), dtype=float)
        result.fluid_node_current_level = np.zeros((1, grid.get_fluid_nodes_number()), dtype=float)
        result.fluid_node_flow_in = np.zeros((1, grid.get_fluid_nodes_number()), dtype=float)
        result.fluid_node_flow_out = np.zeros((1, grid.get_fluid_nodes_number()), dtype=float)
        result.fluid_node_p2x_flow = np.zeros((1, grid.get_fluid_nodes_number()), dtype=float)
        result.fluid_node_spillage = np.zeros((1, grid.get_fluid_nodes_number()), dtype=float)
        result.fluid_path_flow = np.zeros((1, grid.get_fluid_paths_number()), dtype=float)
        result.fluid_injection_flow = np.zeros((1, grid.get_fluid_injection_number()), dtype=float)
        result.converged = np.ones(1, dtype=np.uint64)
        result.error_values = np.zeros(1, dtype=float)
        return result

    monkeypatch.setattr(opf_driver_module, "gslv_opf", fake_gslv_opf)

    driver.run()

    assert state.get("called", False)
    assert driver.engine == vg.EngineType.GSLV
    assert "GSLV OPF snapshot only supports LINEAR_OPF, falling back to VeraGrid" not in get_warning_messages(driver)


def test_gslv_snapshot_nonlinear_opf_uses_gslv(monkeypatch) -> None:
    """
    Snapshot non-linear OPF must dispatch to the GSLV implementation.
    """
    grid = vg.open_file(filename=os.path.join('data', 'grids', 'case14.gridcal'))
    options = vg.OptimalPowerFlowOptions(solver=SolverType.NONLINEAR_OPF)
    driver = OptimalPowerFlowDriver(grid=grid, options=options, engine=vg.EngineType.GSLV)
    state = dict()

    class ResultStub:
        """
        Minimal GSLV OPF result stub for snapshot dispatch testing.
        """
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

    def fake_gslv_opf(circuit, opf_options, time_series, time_indices, logger):
        """
        Record the GSLV dispatch and return a minimal result object.
        """
        result = ResultStub()
        state["called"] = True
        result.voltage = np.zeros((1, grid.get_bus_number()), dtype=np.complex128)
        result.Sbus = np.zeros((1, grid.get_bus_number()), dtype=np.complex128)
        result.bus_shadow_prices = np.zeros((1, grid.get_bus_number()), dtype=float)
        result.load_power = np.zeros((1, grid.get_loads_number()), dtype=float)
        result.load_shedding = np.zeros((1, grid.get_loads_number()), dtype=float)
        result.load_shedding_cost = np.zeros((1, grid.get_loads_number()), dtype=float)
        result.battery_power = np.zeros((1, grid.get_batteries_number()), dtype=float)
        result.generator_power = np.zeros((1, grid.get_generators_number()), dtype=float)
        result.generator_reactive_power = np.zeros((1, grid.get_generators_number()), dtype=float)
        result.Sf = np.zeros((1, grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True)),
                             dtype=np.complex128)
        result.St = np.zeros((1, grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True)),
                             dtype=np.complex128)
        result.overloads = np.zeros((1, grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True)),
                                    dtype=float)
        result.overloads_cost = np.zeros((1, grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True)),
                                         dtype=float)
        result.loading = np.zeros((1, grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True)),
                                  dtype=float)
        result.losses = np.zeros((1, grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True)),
                                 dtype=float)
        result.tap_angle = np.zeros((1, grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True)),
                                    dtype=float)
        result.tap_module = np.zeros((1, grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True)),
                                     dtype=float)
        result.hvdc_Pf = np.zeros((1, grid.get_hvdc_number()), dtype=float)
        result.hvdc_loading = np.zeros((1, grid.get_hvdc_number()), dtype=float)
        result.vsc_Pf = np.zeros((1, grid.get_vsc_number()), dtype=float)
        result.vsc_loading = np.zeros((1, grid.get_vsc_number()), dtype=float)
        result.shunt_like_reactive_power = np.zeros((1, grid.get_shunt_like_device_number()), dtype=float)
        result.fluid_node_current_level = np.zeros((1, grid.get_fluid_nodes_number()), dtype=float)
        result.fluid_node_flow_in = np.zeros((1, grid.get_fluid_nodes_number()), dtype=float)
        result.fluid_node_flow_out = np.zeros((1, grid.get_fluid_nodes_number()), dtype=float)
        result.fluid_node_p2x_flow = np.zeros((1, grid.get_fluid_nodes_number()), dtype=float)
        result.fluid_node_spillage = np.zeros((1, grid.get_fluid_nodes_number()), dtype=float)
        result.fluid_path_flow = np.zeros((1, grid.get_fluid_paths_number()), dtype=float)
        result.fluid_injection_flow = np.zeros((1, grid.get_fluid_injection_number()), dtype=float)
        result.converged = np.ones(1, dtype=np.uint64)
        result.error_values = np.zeros(1, dtype=float)
        return result

    monkeypatch.setattr(opf_driver_module, "gslv_opf", fake_gslv_opf)

    driver.run()

    assert state.get("called", False)
    assert driver.engine == vg.EngineType.GSLV
    assert "GSLV OPF snapshot only supports LINEAR_OPF and NONLINEAR_OPF, falling back to VeraGrid" not in (
        get_warning_messages(driver)
    )


def test_gslv_nonlinear_opf_ts_falls_back_to_veragrid(monkeypatch) -> None:
    """
    GSLV time-series OPF must fall back for non-linear OPF.
    """
    grid = vg.open_file(filename=os.path.join('data', 'grids', 'case14.gridcal'))
    options = vg.OptimalPowerFlowOptions(solver=SolverType.NONLINEAR_OPF)
    driver = OptimalPowerFlowTimeSeriesDriver(grid=grid, options=options, engine=vg.EngineType.GSLV)
    state = dict()

    def fake_opf(self) -> None:
        """
        Record the native time-series OPF dispatch.
        """
        state["called"] = True

    monkeypatch.setattr(OptimalPowerFlowTimeSeriesDriver, "opf", fake_opf)

    driver.run()

    assert state.get("called", False)
    assert driver.engine == vg.EngineType.VeraGrid
    assert "GSLV OPF time series only supports LINEAR_OPF, falling back to VeraGrid" in get_warning_messages(driver)
