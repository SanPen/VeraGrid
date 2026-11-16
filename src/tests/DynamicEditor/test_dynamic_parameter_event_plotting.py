# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import numpy as np

from VeraGrid.Gui.DynamicModelEditor.Plots.dynamic_plots_handler import _build_parameter_plot_data_from_events
from VeraGridEngine.Devices.Events.dynamic_plot_entry import DynamicPlotEntry
from VeraGridEngine.Devices.Events.rms_event import RmsEvent
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.dynamic_parameter_results import collect_declared_dynamic_parameter_values
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.enumerations import (DeviceType, DynamicEventTransitionType, DynamicPlotEntryKind,
                                         DynamicPlotEntryRole, ParamPowerFlowReferenceType, PlotSimulationType)


class FakeDevice:
    def __init__(self, idtag: str) -> None:
        self.idtag: str = idtag
        self.name: str = "Device 1"
        self.device_type: DeviceType = DeviceType.NoDevice


def test_parameter_step_events_replay_from_initial_value() -> None:
    circuit: MultiCircuit = MultiCircuit()
    group: RmsEventsGroup = RmsEventsGroup(name="Group 1", idtag="group-1")
    device: FakeDevice = FakeDevice(idtag="device-1")
    parameter: Var = Var(name="omega_ref")

    circuit.add_rms_events_group(group)
    circuit.add_rms_event(RmsEvent(
        device=device,
        parameter=parameter,
        time=1.0,
        value=1.1,
        group=group,
    ))

    entry: DynamicPlotEntry = DynamicPlotEntry(
        simulation_type=PlotSimulationType.RMS,
        entry_kind=DynamicPlotEntryKind.PARAMETER,
        role=DynamicPlotEntryRole.CURVE,
        event_group_idtag="group-1",
        event_group_name="Group 1",
        curve_device_type=DeviceType.NoDevice,
        device_idtag="device-1",
        variable_name="omega_ref",
    )

    time_axis: np.ndarray = np.array([0.0, 0.5, 1.0, 1.5], dtype=float)
    plot_data = _build_parameter_plot_data_from_events(
        circuit=circuit,
        entry=entry,
        time_axis=time_axis,
        base_value=1.0,
    )

    assert plot_data is not None
    _, y_values = plot_data
    np.testing.assert_allclose(y_values, np.array([1.0, 1.0, 1.0, 1.1], dtype=float))


def test_parameter_ramp_events_replay_from_initial_value() -> None:
    """Verify that parameter plotting reconstructs the exact ramp interval.

    :return: None.
    """
    circuit: MultiCircuit = MultiCircuit()
    group: RmsEventsGroup = RmsEventsGroup(name="Group 1", idtag="group-1")
    device: FakeDevice = FakeDevice(idtag="device-1")
    parameter: Var = Var(name="power_reference")

    circuit.add_rms_events_group(group)
    circuit.add_rms_event(RmsEvent(
        device=device,
        parameter=parameter,
        time=1.0,
        value=2.0,
        group=group,
        transition_type=DynamicEventTransitionType.Ramp,
        end_time=2.0,
    ))

    entry: DynamicPlotEntry = DynamicPlotEntry(
        simulation_type=PlotSimulationType.RMS,
        entry_kind=DynamicPlotEntryKind.PARAMETER,
        role=DynamicPlotEntryRole.CURVE,
        event_group_idtag="group-1",
        event_group_name="Group 1",
        curve_device_type=DeviceType.NoDevice,
        device_idtag="device-1",
        variable_name="power_reference",
    )

    time_axis: np.ndarray = np.array([0.0, 1.0, 1.5, 2.0, 2.5], dtype=float)
    plot_data = _build_parameter_plot_data_from_events(
        circuit=circuit,
        entry=entry,
        time_axis=time_axis,
        base_value=1.0,
    )

    assert plot_data is not None
    _, y_values = plot_data
    np.testing.assert_allclose(y_values, np.array([1.0, 1.0, 1.5, 2.0, 2.0], dtype=float))


def test_declared_parameter_snapshot_includes_static_mapped_and_runtime_values() -> None:
    """Verify that result snapshots cover the full Dynamic Editor catalogue.

    :return: None.
    """
    circuit: MultiCircuit = MultiCircuit()
    generator: Generator = Generator(name="Generator 1", idtag="generator-1")
    static_parameter: Var = Var(name="static_gain")
    mapped_parameter: Var = Var(name="enabled_parameter")
    runtime_parameter: Var = Var(name="power_reference")
    generator.rms_model = Block(
        parameters={
            static_parameter: Const(2.5),
            mapped_parameter: Const(None),
        },
        api_obj_mapping={
            ParamPowerFlowReferenceType.device_active: mapped_parameter,
        },
        event_dict={
            runtime_parameter: Const(1.1),
        },
    )
    circuit.set_elements_list_by_type(
        device_type=DeviceType.GeneratorDevice,
        devices=[generator],
    )

    parameter_values: dict[str, float] = collect_declared_dynamic_parameter_values(
        grid=circuit,
        simulation_type=PlotSimulationType.RMS,
        logger=None,
    )

    assert parameter_values["generator-1:static_gain"] == 2.5
    assert parameter_values["generator-1:enabled_parameter"] == 1.0
    assert parameter_values["generator-1:power_reference"] == 1.1
