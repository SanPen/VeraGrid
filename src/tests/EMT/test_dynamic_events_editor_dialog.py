from __future__ import annotations

import sys

from PySide6 import QtWidgets

from VeraGrid.Gui.dynamic_events_editor_dialog import DynamicEventDialogue
from VeraGrid.Gui.dynamic_events_editor_dialog import collect_block_runtime_event_parameters
from VeraGrid.Gui.dynamic_events_editor_dialog import SwitchSequenceDialog
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import DynamicEventTransitionType, DynamicSimulationMode
from VeraGridEngine.Devices.Events.emt_event import EmtEvent
from VeraGridEngine.Devices.Events.rms_event import RmsEvent


class WarningRecorder:
    """
    Collect warning dialog calls emitted during dialog validation tests.
    """

    __slots__ = (
        "messages",
    )

    def __init__(self) -> None:
        """
        Build an empty warning recorder.

        :return: None.
        """
        self.messages: list[tuple[str, str]] = list()

    def warning(self,
                parent: QtWidgets.QWidget,
                title: str,
                text: str) -> int:
        """
        Record one warning dialog invocation.

        :param parent: Parent widget passed by the dialog.
        :param title: Warning title.
        :param text: Warning body.
        :return: QMessageBox standard result code.
        """
        del parent
        self.messages.append((title, text))
        return int(QtWidgets.QMessageBox.StandardButton.Ok)


def _set_event_row_data(row: object,
                        parameter_index: int,
                        target_time: float,
                        value: float,
                        transition_type: DynamicEventTransitionType,
                        end_time: float | None) -> None:
    """
    Populate one dynamic-event dialog row with explicit values.

    :param row: Target row object.
    :param parameter_index: Parameter combo index.
    :param target_time: Event start time.
    :param value: Event target value.
    :param transition_type: Step or ramp profile.
    :param end_time: Optional ramp end time.
    :return: None.
    """
    row.param_combo.setCurrentIndex(parameter_index)
    row.time_spin.setValue(float(target_time))
    row.value_spin.setValue(float(value))

    if row.transition_combo is not None:
        transition_index: int = row.transition_combo.findData(transition_type)
        row.transition_combo.setCurrentIndex(transition_index)
    else:
        pass

    if row.end_time_spin is not None:
        if end_time is not None:
            row.end_time_spin.setValue(float(end_time))
        else:
            pass
    else:
        pass


def _install_warning_recorder(recorder: WarningRecorder,
                              monkeypatch: object) -> None:
    """
    Redirect QMessageBox warnings into a local recorder.

    :param recorder: Warning recorder instance.
    :param monkeypatch: Pytest monkeypatch fixture.
    :return: None.
    """
    monkeypatch.setattr(QtWidgets.QMessageBox, "warning", recorder.warning)


def _get_app() -> QtWidgets.QApplication:
    """
    Return the shared Qt application used by dialog tests.

    :return: Qt application instance.
    """
    app: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()

    if app is None:
        return QtWidgets.QApplication(sys.argv)
    else:
        return app


def test_emt_event_dialog_enables_force_step_alignment_for_mode_parameters() -> None:
    """
    Ensure EMT mode parameters expose force-step alignment in the dialog.

    :return: None.
    """
    _get_app()
    circuit = MultiCircuit()
    group = EmtEventsGroup(name="group")
    circuit.add_emt_events_group(group)

    vf = VarFactory()
    event_var = vf.add_var("event_param")
    mode_var = vf.add_var("mode_param")

    dialog = DynamicEventDialogue(
        circuit=circuit,
        parameters_list=[event_var, mode_var],
        target_device_name="Device",
        mode=DynamicSimulationMode.EMT,
        mode_parameter_uids={mode_var.uid},
    )
    dialog.add_row()
    row = dialog.rows[0]

    row.param_combo.setCurrentIndex(1)
    QtWidgets.QApplication.processEvents()

    assert row.force_alignment_check is not None
    assert row.force_alignment_check.isEnabled()
    assert row.force_alignment_check.isChecked()

    dialog.accept_dialog()
    data = dialog.get_data()

    assert data["parameters"] == [mode_var]
    assert data["force_step_alignment"] == [True]
    dialog.close()


def test_emt_event_dialog_disables_force_step_alignment_for_event_parameters() -> None:
    """
    Ensure continuous EMT event parameters do not expose force-step alignment.

    :return: None.
    """
    _get_app()
    circuit = MultiCircuit()
    group = EmtEventsGroup(name="group")
    circuit.add_emt_events_group(group)

    vf = VarFactory()
    event_var = vf.add_var("event_param")
    mode_var = vf.add_var("mode_param")

    dialog = DynamicEventDialogue(
        circuit=circuit,
        parameters_list=[event_var, mode_var],
        target_device_name="Device",
        mode=DynamicSimulationMode.EMT,
        mode_parameter_uids={mode_var.uid},
    )
    dialog.add_row()
    row = dialog.rows[0]

    row.param_combo.setCurrentIndex(0)
    QtWidgets.QApplication.processEvents()

    assert row.force_alignment_check is not None
    assert not row.force_alignment_check.isEnabled()
    assert not row.force_alignment_check.isChecked()

    dialog.accept_dialog()
    data = dialog.get_data()

    assert data["parameters"] == [event_var]
    assert data["force_step_alignment"] == [False]
    dialog.close()


def test_emt_event_dialog_enables_end_time_for_ramp_transition() -> None:
    """
    Ensure EMT rows expose the end-time control for ramp transitions.

    :return: None.
    """
    _get_app()
    circuit = MultiCircuit()
    group = EmtEventsGroup(name="group")
    circuit.add_emt_events_group(group)

    vf = VarFactory()
    event_var = vf.add_var("event_param")

    dialog = DynamicEventDialogue(
        circuit=circuit,
        parameters_list=[event_var],
        target_device_name="Device",
        mode=DynamicSimulationMode.EMT,
        mode_parameter_uids=set(),
    )
    dialog.add_row()
    row = dialog.rows[0]

    assert row.transition_combo is not None
    assert row.end_time_spin is not None
    assert not row.end_time_spin.isEnabled()

    row.transition_combo.setCurrentIndex(1)
    QtWidgets.QApplication.processEvents()

    assert row.transition_combo.currentData() == DynamicEventTransitionType.Ramp
    assert row.end_time_spin.isEnabled()

    row.end_time_spin.setValue(0.25)
    dialog.accept_dialog()
    data = dialog.get_data()

    assert data["transition_types"] == [DynamicEventTransitionType.Ramp]
    assert data["end_times"] == [0.25]
    dialog.close()


def test_rms_event_dialog_enables_end_time_for_ramp_transition() -> None:
    """
    Ensure RMS rows expose the end-time control for ramp transitions.

    :return: None.
    """
    _get_app()
    circuit = MultiCircuit()
    group = RmsEventsGroup(name="group")
    circuit.add_rms_events_group(group)

    vf = VarFactory()
    event_var = vf.add_var("event_param")

    dialog = DynamicEventDialogue(
        circuit=circuit,
        parameters_list=[event_var],
        target_device_name="Device",
        mode=DynamicSimulationMode.RMS,
        mode_parameter_uids=set(),
    )
    dialog.add_row()
    row = dialog.rows[0]

    assert row.transition_combo is not None
    assert row.end_time_spin is not None
    assert not row.end_time_spin.isEnabled()

    row.transition_combo.setCurrentIndex(1)
    QtWidgets.QApplication.processEvents()

    assert row.transition_combo.currentData() == DynamicEventTransitionType.Ramp
    assert row.end_time_spin.isEnabled()

    row.end_time_spin.setValue(0.25)
    dialog.accept_dialog()
    data = dialog.get_data()

    assert data["transition_types"] == [DynamicEventTransitionType.Ramp]
    assert data["end_times"] == [0.25]
    dialog.close()


def test_switch_sequence_dialog_builds_open_close_event_sequence() -> None:
    """
    Ensure the switch-sequence helper generates ordered open/close steps.

    :return: None.
    """
    _get_app()
    circuit = MultiCircuit()
    group = EmtEventsGroup(name="group")
    circuit.add_emt_events_group(group)

    vf = VarFactory()
    mode_var = vf.add_var("switch_closed_mode")

    dialog = SwitchSequenceDialog(mode_parameters=[mode_var], events_groups=circuit.emt_events_groups)
    dialog.rows[0].set_data(0.3, 1.0)
    dialog.add_row()
    dialog.rows[1].set_data(0.1, 0.0)
    dialog.accept_dialog()

    data = dialog.get_data()
    assert data["parameter"] is mode_var
    assert data["group"] is group
    assert data["times"] == [0.1, 0.3]
    assert data["values"] == [0.0, 1.0]
    dialog.close()


def test_collect_block_runtime_event_parameters_includes_child_mode_dict() -> None:
    """
    Ensure event collection sees runtime parameters stored in child blocks.

    :return: None.
    """
    vf = VarFactory()
    child_mode = vf.add_var("switch_closed_mode_child")
    child_block = Block(mode_dict={child_mode: 0.0})
    root_block = Block(children=[child_block])

    parameters, mode_uids = collect_block_runtime_event_parameters(root_block)

    assert parameters == [child_mode]
    assert mode_uids == {child_mode.uid}


def test_rms_event_dialog_rejects_overlapping_step_events_in_same_group(monkeypatch: object) -> None:
    """
    Ensure RMS validation blocks two step events at the same time and parameter.

    :param monkeypatch: Pytest monkeypatch fixture.
    :return: None.
    """
    _get_app()
    circuit: MultiCircuit = MultiCircuit()
    group: RmsEventsGroup = RmsEventsGroup(name="group")
    circuit.add_rms_events_group(group)

    vf: VarFactory = VarFactory()
    event_var = vf.add_var("event_param")
    dialog = DynamicEventDialogue(circuit=circuit,
                                  parameters_list=[event_var],
                                  target_device_name="Device",
                                  mode=DynamicSimulationMode.RMS,
                                  mode_parameter_uids=set())
    recorder: WarningRecorder = WarningRecorder()
    _install_warning_recorder(recorder=recorder, monkeypatch=monkeypatch)

    first_row = dialog.add_row()
    second_row = dialog.add_row()
    _set_event_row_data(row=first_row,
                        parameter_index=0,
                        target_time=2.0,
                        value=1.0,
                        transition_type=DynamicEventTransitionType.Step,
                        end_time=None)
    _set_event_row_data(row=second_row,
                        parameter_index=0,
                        target_time=2.0,
                        value=3.0,
                        transition_type=DynamicEventTransitionType.Step,
                        end_time=None)

    dialog.accept_dialog()

    assert len(recorder.messages) == 1
    assert recorder.messages[0][0] == "Overlapping Events"
    assert "parameter=event_param" in recorder.messages[0][1]
    assert "New row 1" in recorder.messages[0][1]
    assert "New row 2" in recorder.messages[0][1]
    assert dialog.result() == 0
    dialog.close()


def test_emt_event_dialog_rejects_step_inside_existing_ramp(monkeypatch: object) -> None:
    """
    Ensure EMT validation blocks a new step placed inside an existing ramp.

    :param monkeypatch: Pytest monkeypatch fixture.
    :return: None.
    """
    _get_app()
    circuit: MultiCircuit = MultiCircuit()
    group: EmtEventsGroup = EmtEventsGroup(name="group")
    circuit.add_emt_events_group(group)

    vf: VarFactory = VarFactory()
    event_var = vf.add_var("event_param")
    existing_event: EmtEvent = EmtEvent(parameter=event_var,
                                        time=1.0,
                                        end_time=3.0,
                                        value=2.0,
                                        group=group,
                                        transition_type=DynamicEventTransitionType.Ramp)
    circuit.add_emt_event(existing_event)

    dialog = DynamicEventDialogue(circuit=circuit,
                                  parameters_list=[event_var],
                                  target_device_name="Device",
                                  mode=DynamicSimulationMode.EMT,
                                  mode_parameter_uids=set())
    recorder: WarningRecorder = WarningRecorder()
    _install_warning_recorder(recorder=recorder, monkeypatch=monkeypatch)

    row = dialog.add_row()
    _set_event_row_data(row=row,
                        parameter_index=0,
                        target_time=2.0,
                        value=5.0,
                        transition_type=DynamicEventTransitionType.Step,
                        end_time=None)

    dialog.accept_dialog()

    assert len(recorder.messages) == 1
    assert recorder.messages[0][0] == "Overlapping Events"
    assert "Existing event" in recorder.messages[0][1]
    assert "New row 1" in recorder.messages[0][1]
    assert dialog.result() == 0
    dialog.close()


def test_rms_event_dialog_allows_same_time_for_different_parameters(monkeypatch: object) -> None:
    """
    Ensure RMS validation does not block independent parameters at one time.

    :param monkeypatch: Pytest monkeypatch fixture.
    :return: None.
    """
    _get_app()
    circuit: MultiCircuit = MultiCircuit()
    group: RmsEventsGroup = RmsEventsGroup(name="group")
    circuit.add_rms_events_group(group)

    vf: VarFactory = VarFactory()
    first_var = vf.add_var("event_param_1")
    second_var = vf.add_var("event_param_2")
    dialog = DynamicEventDialogue(circuit=circuit,
                                  parameters_list=[first_var, second_var],
                                  target_device_name="Device",
                                  mode=DynamicSimulationMode.RMS,
                                  mode_parameter_uids=set())
    recorder: WarningRecorder = WarningRecorder()
    _install_warning_recorder(recorder=recorder, monkeypatch=monkeypatch)

    first_row = dialog.add_row()
    second_row = dialog.add_row()
    _set_event_row_data(row=first_row,
                        parameter_index=0,
                        target_time=2.0,
                        value=1.0,
                        transition_type=DynamicEventTransitionType.Step,
                        end_time=None)
    _set_event_row_data(row=second_row,
                        parameter_index=1,
                        target_time=2.0,
                        value=3.0,
                        transition_type=DynamicEventTransitionType.Step,
                        end_time=None)

    dialog.accept_dialog()

    assert len(recorder.messages) == 0
    assert dialog.result() == int(QtWidgets.QDialog.DialogCode.Accepted)
    assert dialog.get_data()["parameters"] == [first_var, second_var]
    dialog.close()


def test_emt_event_dialog_rejects_invalid_ramp_interval(monkeypatch: object) -> None:
    """
    Ensure EMT validation blocks ramps whose end time is before the start time.

    :param monkeypatch: Pytest monkeypatch fixture.
    :return: None.
    """
    _get_app()
    circuit: MultiCircuit = MultiCircuit()
    group: EmtEventsGroup = EmtEventsGroup(name="group")
    circuit.add_emt_events_group(group)

    vf: VarFactory = VarFactory()
    event_var = vf.add_var("event_param")
    dialog = DynamicEventDialogue(circuit=circuit,
                                  parameters_list=[event_var],
                                  target_device_name="Device",
                                  mode=DynamicSimulationMode.EMT,
                                  mode_parameter_uids=set())
    recorder: WarningRecorder = WarningRecorder()
    _install_warning_recorder(recorder=recorder, monkeypatch=monkeypatch)

    row = dialog.add_row()
    _set_event_row_data(row=row,
                        parameter_index=0,
                        target_time=3.0,
                        value=5.0,
                        transition_type=DynamicEventTransitionType.Ramp,
                        end_time=2.0)

    dialog.accept_dialog()

    assert len(recorder.messages) == 1
    assert recorder.messages[0][0] == "Overlapping Events"
    assert "invalid ramp interval" in recorder.messages[0][1]
    assert dialog.result() == 0
    dialog.close()
