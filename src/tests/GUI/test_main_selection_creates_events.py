from typing import Dict, List, Tuple

import pytest
from PySide6 import QtWidgets

import VeraGrid.Gui.Main.SubClasses.Model.diagrams as diagrams_module
import VeraGridEngine.api as vge
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.enumerations import (
    ContingencyOperationTypes,
    DynamicEventTransitionType,
    DynamicSimulationMode,
    FaultType,
    MethodShortCircuit,
    PhasesShortCircuit,
)


class FakeSelectionGui:
    """
    Lightweight object exposing the attributes used by ``DiagramsMain`` selection actions.
    """

    __slots__ = (
        "circuit",
        "_selected_devices",
        "_selected_buses",
        "info_messages",
        "warning_messages",
        "contingency_checks_diag",
        "ra_checks_diag",
        "investment_checks_diag",
        "sc_selector_dialogue",
        "check_list_dialogue_cls",
        "dynamic_event_dialogue_cls",
        "short_circuit_selector_cls",
    )

    def __init__(self,
                 circuit: vge.MultiCircuit,
                 selected_devices: List[object],
                 selected_buses: List[Tuple[int, vge.Bus, object | None]]) -> None:
        """
        Build the fake GUI state.

        :param circuit: Circuit mutated by the tested GUI actions.
        :param selected_devices: Devices returned by ``get_selected_devices``.
        :param selected_buses: Buses returned by ``get_diagram_selected_buses``.
        :return: Nothing.
        """
        self.circuit: vge.MultiCircuit = circuit
        self._selected_devices: List[object] = selected_devices
        self._selected_buses: List[Tuple[int, vge.Bus, object | None]] = selected_buses
        self.info_messages: List[str] = list()
        self.warning_messages: List[str] = list()
        self.contingency_checks_diag: object | None = None
        self.ra_checks_diag: object | None = None
        self.investment_checks_diag: object | None = None
        self.sc_selector_dialogue: object | None = None
        self.check_list_dialogue_cls = diagrams_module.CheckListDialogue
        self.dynamic_event_dialogue_cls = diagrams_module.DynamicEventDialogue
        self.short_circuit_selector_cls = diagrams_module.ShortCircuitSelector

    def get_selected_devices(self) -> List[object]:
        """
        Return the configured device selection.

        :return: Selected devices.
        """
        return list(self._selected_devices)

    def get_diagram_selected_buses(self) -> List[Tuple[int, vge.Bus, object | None]]:
        """
        Return the configured bus selection.

        :return: Selected buses.
        """
        return list(self._selected_buses)

    def show_info_toast(self, message: str, duration: int = 2000) -> None:
        """
        Store an informational toast message.

        :param message: Toast message.
        :param duration: Toast duration in milliseconds.
        :return: Nothing.
        """
        del duration
        self.info_messages.append(message)

    def show_warning_toast(self, message: str, duration: int = 2000) -> None:
        """
        Store a warning toast message.

        :param message: Toast message.
        :param duration: Toast duration in milliseconds.
        :return: Nothing.
        """
        del duration
        self.warning_messages.append(message)


class AcceptedCheckListDialogue:
    """
    Deterministic replacement for checklist modal dialogs.
    """

    __slots__ = ("objects_list", "title", "selected_indices", "is_accepted", "_group_text", "_modal")

    def __init__(self,
                 objects_list: List[str],
                 title: str,
                 ask_for_group_name: bool,
                 group_label: str,
                 group_text: str) -> None:
        """
        Build an accepted checklist selecting every listed item.

        :param objects_list: User-facing object labels.
        :param title: Dialog title.
        :param ask_for_group_name: Whether the real dialog would ask for a group name.
        :param group_label: User-facing group label.
        :param group_text: Default group text supplied by the GUI.
        :return: Nothing.
        """
        del ask_for_group_name
        del group_label
        self.objects_list: List[str] = list(objects_list)
        self.title: str = title
        self.selected_indices: List[int] = list(range(len(objects_list)))
        self.is_accepted: bool = True
        self._group_text: str = group_text
        self._modal: bool = False

    def setModal(self, modal: bool) -> None:
        """
        Store the modal state requested by the GUI.

        :param modal: Modal state.
        :return: Nothing.
        """
        self._modal = modal

    def exec(self) -> int:
        """
        Simulate accepting the dialog.

        :return: Accepted dialog code.
        """
        return int(QtWidgets.QDialog.DialogCode.Accepted)

    def get_group_text(self) -> str:
        """
        Get the group name used by the GUI action.

        :return: Group name.
        """
        return self._group_text


class AcceptedShortCircuitSelector:
    """
    Deterministic replacement for the short-circuit selector dialog.
    """

    __slots__ = ("was_accepted", "fault", "method", "phases")

    def __init__(self) -> None:
        """
        Build an accepted short-circuit selector.

        :return: Nothing.
        """
        self.was_accepted: bool = True
        self.fault: FaultType = FaultType.LG
        self.method: MethodShortCircuit = MethodShortCircuit.phases
        self.phases: PhasesShortCircuit = PhasesShortCircuit.a

    def exec(self) -> int:
        """
        Simulate accepting the selector.

        :return: Accepted dialog code.
        """
        return int(QtWidgets.QDialog.DialogCode.Accepted)

    def get_impedance_pu(self, Sbase: float, Vbase: float) -> complex:
        """
        Return a deterministic impedance while checking the GUI supplies base values.

        :param Sbase: Circuit base power.
        :param Vbase: Bus base voltage.
        :return: Fault impedance in per unit.
        """
        assert Sbase > 0.0
        assert Vbase > 0.0
        return complex(0.01, 0.02)


class AcceptedDynamicEventDialogue:
    """
    Deterministic replacement for RMS/EMT event editor dialogs.
    """

    __slots__ = ("_data",)

    def __init__(self,
                 circuit: vge.MultiCircuit,
                 parameters_list: List[Var],
                 target_device_name: str,
                 mode: DynamicSimulationMode,
                 mode_parameter_uids: set[int] | None = None) -> None:
        """
        Build an accepted dynamic-event dialog with one event row.

        :param circuit: Circuit containing the event groups.
        :param parameters_list: Parameters offered by the selected device model.
        :param target_device_name: User-facing target device name.
        :param mode: Dynamic simulation mode.
        :param mode_parameter_uids: Optional EMT mode-parameter uid set.
        :return: Nothing.
        """
        del mode_parameter_uids
        assert target_device_name != ""
        assert len(parameters_list) == 1

        groups: List[object] = list()
        if mode == DynamicSimulationMode.RMS:
            groups.append(circuit.rms_events_groups[0])
        else:
            groups.append(circuit.emt_events_groups[0])

        parameters: List[Var] = list()
        parameters.append(parameters_list[0])
        target_times: List[float] = list()
        target_times.append(1.25)
        values: List[float] = list()
        values.append(3.5)

        self._data: Dict[str, List[object]] = dict()
        self._data["parameters"] = parameters
        self._data["target_times"] = target_times
        self._data["values"] = values
        self._data["groups"] = groups
        if mode == DynamicSimulationMode.EMT:
            transition_types: List[DynamicEventTransitionType] = list()
            transition_types.append(DynamicEventTransitionType.Step)
            end_times: List[object | None] = list()
            end_times.append(None)
            force_step_alignment: List[bool] = list()
            force_step_alignment.append(False)
            self._data["transition_types"] = transition_types
            self._data["end_times"] = end_times
            self._data["force_step_alignment"] = force_step_alignment
        else:
            pass

    def exec(self) -> QtWidgets.QDialog.DialogCode:
        """
        Simulate accepting the event editor.

        :return: Accepted dialog code.
        """
        return QtWidgets.QDialog.DialogCode.Accepted

    def get_data(self) -> Dict[str, List[object]]:
        """
        Get the configured event payload.

        :return: Event payload.
        """
        return self._data


def build_grid_with_selected_devices() -> Tuple[vge.MultiCircuit, vge.Bus, vge.Bus, vge.Line, vge.Load]:
    """
    Build a valid two-bus grid with selectable line and load devices.

    :return: Circuit, buses, line, and load.
    """
    grid: vge.MultiCircuit = vge.MultiCircuit(name="GUI selection grid")
    bus_from: vge.Bus = vge.Bus(name="Bus A", Vnom=10.0)
    bus_to: vge.Bus = vge.Bus(name="Bus B", Vnom=10.0)
    grid.add_bus(obj=bus_from)
    grid.add_bus(obj=bus_to)

    line: vge.Line = vge.Line(bus_from=bus_from, bus_to=bus_to, name="Line A-B")
    grid.add_line(obj=line)

    load: vge.Load = vge.Load(name="Load B")
    grid.add_load(bus=bus_to, api_obj=load)

    return grid, bus_from, bus_to, line, load


def build_dynamic_event_target(mode: DynamicSimulationMode) -> Tuple[vge.MultiCircuit, vge.Load, Var, object]:
    """
    Build a circuit and selected load with one RMS or EMT event parameter.

    :param mode: Dynamic simulation mode.
    :return: Circuit, selected load, event parameter, and event group.
    """
    grid: vge.MultiCircuit
    bus_from: vge.Bus
    bus_to: vge.Bus
    line: vge.Line
    load: vge.Load
    grid, bus_from, bus_to, line, load = build_grid_with_selected_devices()
    del bus_from
    del bus_to
    del line

    parameter: Var = Var(name="event_parameter")
    value: Const = Const(0.0)
    model: Block = Block(event_dict={parameter: value})

    if mode == DynamicSimulationMode.RMS:
        group: vge.RmsEventsGroup = vge.RmsEventsGroup(name="RMS group")
        grid.add_rms_events_group(obj=group)
        load.rms_model = model
    else:
        group = vge.EmtEventsGroup(name="EMT group")
        grid.add_emt_events_group(obj=group)
        load.emt_model = model

    return grid, load, parameter, group


def test_add_selected_to_contingency_creates_group_and_entries(qt_app: object) -> None:
    """
    Check that selected diagram devices can be converted into contingencies.

        :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    grid: vge.MultiCircuit
    bus_from: vge.Bus
    bus_to: vge.Bus
    line: vge.Line
    load: vge.Load
    grid, bus_from, bus_to, line, load = build_grid_with_selected_devices()
    del bus_from
    del bus_to

    selected_devices: List[object] = list()
    selected_devices.append(line)
    selected_devices.append(load)
    selected_buses: List[Tuple[int, vge.Bus, object | None]] = list()
    gui: FakeSelectionGui = FakeSelectionGui(circuit=grid,
                                             selected_devices=selected_devices,
                                             selected_buses=selected_buses)
    diagrams_module.CheckListDialogue = AcceptedCheckListDialogue

    diagrams_module.DiagramsMain.add_selected_to_contingency(gui)

    assert len(grid.contingency_groups) == 1
    assert len(grid.contingencies) == 2
    assert grid.contingency_groups[0].category == "multiple"
    assert grid.contingencies[0].device is line
    assert grid.contingencies[1].device is load
    assert grid.contingencies[0].group is grid.contingency_groups[0]
    assert grid.contingencies[0].prop == ContingencyOperationTypes.Active
    assert grid.contingencies[0].value == 0


def test_add_selected_to_remedial_action_creates_group_and_entries(qt_app: object) -> None:
    """
    Check that selected diagram devices can be converted into remedial actions.

        :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    grid: vge.MultiCircuit
    bus_from: vge.Bus
    bus_to: vge.Bus
    line: vge.Line
    load: vge.Load
    grid, bus_from, bus_to, line, load = build_grid_with_selected_devices()
    del bus_from
    del bus_to

    selected_devices: List[object] = list()
    selected_devices.append(line)
    selected_devices.append(load)
    selected_buses: List[Tuple[int, vge.Bus, object | None]] = list()
    gui: FakeSelectionGui = FakeSelectionGui(circuit=grid,
                                             selected_devices=selected_devices,
                                             selected_buses=selected_buses)
    diagrams_module.CheckListDialogue = AcceptedCheckListDialogue

    diagrams_module.DiagramsMain.add_selected_to_remedial_action(gui)

    assert len(grid.remedial_action_groups) == 1
    assert len(grid.remedial_actions) == 2
    assert grid.remedial_action_groups[0].category == "multiple"
    assert grid.remedial_actions[0].device is line
    assert grid.remedial_actions[1].device is load
    assert grid.remedial_actions[0].group is grid.remedial_action_groups[0]
    assert grid.remedial_actions[0].prop == ContingencyOperationTypes.Active
    assert grid.remedial_actions[0].value == 0


def test_add_selected_to_investment_creates_group_and_entries(qt_app: object) -> None:
    """
    Check that selected diagram devices can be converted into investments.

        :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    grid: vge.MultiCircuit
    bus_from: vge.Bus
    bus_to: vge.Bus
    line: vge.Line
    load: vge.Load
    grid, bus_from, bus_to, line, load = build_grid_with_selected_devices()
    del bus_from
    del bus_to

    selected_devices: List[object] = list()
    selected_devices.append(line)
    selected_devices.append(load)
    selected_buses: List[Tuple[int, vge.Bus, object | None]] = list()
    gui: FakeSelectionGui = FakeSelectionGui(circuit=grid,
                                             selected_devices=selected_devices,
                                             selected_buses=selected_buses)
    diagrams_module.CheckListDialogue = AcceptedCheckListDialogue

    diagrams_module.DiagramsMain.add_selected_to_investment(gui)

    assert len(grid.investments_groups) == 1
    assert len(grid.investments) == 2
    assert grid.investments_groups[0].category == "multiple"
    assert grid.investments[0].device is line
    assert grid.investments[1].device is load
    assert grid.investments[0].group is grid.investments_groups[0]
    assert grid.investments[0].CAPEX == 0.0
    assert grid.investments[0].name == line.type_name + ": " + line.name


def test_add_short_circuit_events_creates_faults_for_selected_buses(qt_app: object) -> None:
    """
    Check that selected diagram buses can be converted into short-circuit events.

        :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    grid: vge.MultiCircuit
    bus_from: vge.Bus
    bus_to: vge.Bus
    line: vge.Line
    load: vge.Load
    grid, bus_from, bus_to, line, load = build_grid_with_selected_devices()
    del line
    del load

    selected_devices: List[object] = list()
    selected_buses: List[Tuple[int, vge.Bus, object | None]] = list()
    selected_buses.append((0, bus_from, None))
    selected_buses.append((1, bus_to, None))
    gui: FakeSelectionGui = FakeSelectionGui(circuit=grid,
                                             selected_devices=selected_devices,
                                             selected_buses=selected_buses)
    diagrams_module.ShortCircuitSelector = AcceptedShortCircuitSelector

    diagrams_module.DiagramsMain.add_short_circuit_events(gui)

    assert len(grid.short_circuit_event) == 2
    assert grid.short_circuit_event[0].device is bus_from
    assert grid.short_circuit_event[1].device is bus_to
    assert grid.short_circuit_event[0].fault_type == FaultType.LG
    assert grid.short_circuit_event[0].method == MethodShortCircuit.phases
    assert grid.short_circuit_event[0].phases == PhasesShortCircuit.a
    assert grid.short_circuit_event[0].r_fault == 0.01
    assert grid.short_circuit_event[0].x_fault == 0.02
    assert gui.info_messages == ["2 short circuit events added!"]


def test_add_rms_event_to_selected_creates_event_from_dialogue(qt_app: object) -> None:
    """
    Check that one selected device can receive an RMS event from the event editor.

        :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    grid: vge.MultiCircuit
    load: vge.Load
    parameter: Var
    group: object
    grid, load, parameter, group = build_dynamic_event_target(mode=DynamicSimulationMode.RMS)

    selected_devices: List[object] = list()
    selected_devices.append(load)
    selected_buses: List[Tuple[int, vge.Bus, object | None]] = list()
    gui: FakeSelectionGui = FakeSelectionGui(circuit=grid,
                                             selected_devices=selected_devices,
                                             selected_buses=selected_buses)
    diagrams_module.DynamicEventDialogue = AcceptedDynamicEventDialogue

    diagrams_module.DiagramsMain.add_rms_event_to_selected(gui)

    assert len(grid.rms_events) == 1
    assert grid.rms_events[0].device is load
    assert grid.rms_events[0].parameter is parameter
    assert grid.rms_events[0].group is group
    assert grid.rms_events[0].time == 1.25
    assert grid.rms_events[0].value == 3.5


def test_add_emt_event_to_selected_creates_event_from_dialogue(qt_app: object) -> None:
    """
    Check that one selected device can receive an EMT event from the event editor.

        :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    grid: vge.MultiCircuit
    load: vge.Load
    parameter: Var
    group: object
    grid, load, parameter, group = build_dynamic_event_target(mode=DynamicSimulationMode.EMT)

    selected_devices: List[object] = list()
    selected_devices.append(load)
    selected_buses: List[Tuple[int, vge.Bus, object | None]] = list()
    gui: FakeSelectionGui = FakeSelectionGui(circuit=grid,
                                             selected_devices=selected_devices,
                                             selected_buses=selected_buses)
    diagrams_module.DynamicEventDialogue = AcceptedDynamicEventDialogue

    diagrams_module.DiagramsMain.add_emt_event_to_selected(gui)

    assert len(grid.emt_events) == 1
    assert grid.emt_events[0].device is load
    assert grid.emt_events[0].parameter is parameter
    assert grid.emt_events[0].group is group
    assert grid.emt_events[0].time == 1.25
    assert grid.emt_events[0].value == 3.5
