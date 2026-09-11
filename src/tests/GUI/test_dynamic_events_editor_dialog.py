from __future__ import annotations

import sys

from PySide6 import QtCore, QtWidgets

import VeraGridEngine.api as vge
from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_page import DynamicEventGroupsTreeModel
from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_page import DynamicEventsPage
from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_support import collect_block_runtime_event_parameters
from VeraGrid.Gui.DynamicModelEditor.Workspace.dynamic_editor_entries import DynamicEditorEntry
from VeraGrid.Gui.DynamicModelEditor.Workspace.dynamic_editor_entries import build_dynamic_editor_entry
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.enumerations import DynamicSimulationMode


def get_qt_application() -> QtWidgets.QApplication:
    """Return the process QApplication required by widget tests.

    :return: Existing or newly created QApplication.
    """
    application: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if application is None:
        return QtWidgets.QApplication(sys.argv)
    else:
        return application


def build_dynamic_target() -> tuple[vge.MultiCircuit, vge.Load, Var, vge.RmsEventsGroup, DynamicEditorEntry]:
    """Build one RMS device with a parameter and event group.

    :return: Circuit, device, parameter, group and dynamic-editor entry.
    """
    circuit: vge.MultiCircuit = vge.MultiCircuit()
    bus: vge.Bus = vge.Bus(name="Event bus", Vnom=10.0)
    circuit.add_bus(bus)
    load: vge.Load = vge.Load(name="Event load")
    circuit.add_load(bus=bus, api_obj=load)
    parameter: Var = circuit.var_factory.add_var("event_parameter")
    event_values: dict[Var, Const] = dict()
    event_values[parameter] = Const(0.0)
    load.rms_model = Block(event_dict=event_values)
    group: vge.RmsEventsGroup = vge.RmsEventsGroup(name="RMS group")
    circuit.add_rms_events_group(obj=group)
    entry: DynamicEditorEntry | None = build_dynamic_editor_entry(api_object=load, circuit=circuit)
    assert entry is not None
    return circuit, load, parameter, group, entry


def test_group_tree_uses_real_groups_and_updates_active_immediately() -> None:
    """The group checkbox must write directly to the real circuit group.

    :return: None.
    """
    _application: QtWidgets.QApplication = get_qt_application()
    circuit: vge.MultiCircuit
    load: vge.Load
    _parameter: Var
    group: vge.RmsEventsGroup
    _entry: DynamicEditorEntry
    circuit, load, _parameter, group, _entry = build_dynamic_target()
    model: DynamicEventGroupsTreeModel = DynamicEventGroupsTreeModel(
        circuit=circuit,
        device=load,
        mode=DynamicSimulationMode.RMS,
    )
    group_index: QtCore.QModelIndex = model.index(0, 0)

    assert model.group_from_index(group_index) is group
    assert group.active
    assert model.setData(group_index, QtCore.Qt.CheckState.Unchecked, QtCore.Qt.ItemDataRole.CheckStateRole)
    assert not group.active


def test_event_page_uses_focused_objects_model_and_adds_real_event() -> None:
    """The page table must expose six properties and add directly to the circuit.

    :return: None.
    """
    _application: QtWidgets.QApplication = get_qt_application()
    circuit: vge.MultiCircuit
    load: vge.Load
    parameter: Var
    _group: vge.RmsEventsGroup
    entry: DynamicEditorEntry
    circuit, load, parameter, _group, entry = build_dynamic_target()
    page: DynamicEventsPage = DynamicEventsPage(
        entry=entry,
        device=load,
        mode=DynamicSimulationMode.RMS,
        parameters=list((parameter,)),
        mode_parameter_uids=set(),
        model_is_empty=False,
    )

    assert page.objects_model is not None
    assert page.objects_model.attributes == [
        "parameter",
        "time",
        "end_time",
        "value",
        "force_step_alignment",
        "transition_type",
    ]
    page.add_event()
    assert len(circuit.rms_events) == 1
    assert circuit.rms_events[0].group is page.selected_group
    assert circuit.rms_events[0].parameter is parameter
    page.prepare_to_delete()
    page.deleteLater()


def test_collect_block_runtime_event_parameters_includes_child_modes() -> None:
    """Parameter discovery must include discrete modes in child blocks.

    :return: None.
    """
    mode_parameter: Var = VarFactory().add_var("switch_closed_mode_child")
    mode_values: dict[Var, float] = dict()
    mode_values[mode_parameter] = 0.0
    child_block: Block = Block(mode_dict=mode_values)
    root_block: Block = Block(children=list((child_block,)))
    parameters: list[Var]
    mode_uids: set[int]
    parameters, mode_uids = collect_block_runtime_event_parameters(block=root_block)

    assert parameters == list((mode_parameter,))
    assert mode_uids == set((mode_parameter.uid,))
