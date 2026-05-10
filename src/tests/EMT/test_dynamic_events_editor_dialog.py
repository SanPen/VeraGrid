from __future__ import annotations

import sys

from PySide6 import QtWidgets

from VeraGrid.Gui.dynamic_events_editor_dialog import DynamicEventDialogue
from VeraGrid.Gui.dynamic_events_editor_dialog import collect_block_runtime_event_parameters
from VeraGrid.Gui.dynamic_events_editor_dialog import SwitchSequenceDialog
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import DynamicEventTransitionType, DynamicSimulationMode


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
    mode_var = vf.add_var("switch_closed_mode_SW")

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
