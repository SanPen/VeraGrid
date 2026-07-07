from __future__ import annotations

import numpy as np

from VeraGrid.Gui.Main.SubClasses.Results.dynamics_results_handler import _build_parameter_plot_data_from_events
from VeraGridEngine.Devices.Events.dynamic_plot_entry import DynamicPlotEntry
from VeraGridEngine.Devices.Events.rms_event import RmsEvent
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DeviceType, DynamicPlotEntryKind, DynamicPlotEntryRole, PlotSimulationType


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
    np.testing.assert_allclose(y_values, np.array([1.0, 1.0, 1.1, 1.1], dtype=float))
