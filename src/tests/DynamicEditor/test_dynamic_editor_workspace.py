from __future__ import annotations

import sys

from PySide6 import QtWidgets

from VeraGrid.Gui.DynamicModelEditor.dyn_editor_multiwindow_engine import DynamicEditorPickerDialog
from VeraGrid.Gui.DynamicModelEditor.dyn_editor_multiwindow_engine import build_dynamic_editor_entry
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_workspace_manager import DynamicEditorWorkspaceManager
from VeraGridEngine.enumerations import DynamicSimulationMode

import VeraGridEngine.api as gce


def _get_app() -> QtWidgets.QApplication:
    app = QtWidgets.QApplication.instance()
    if app is None:
        return QtWidgets.QApplication(sys.argv)
    return app


def _build_load_entry():
    circuit = gce.MultiCircuit(Sbase=100, fbase=50.0)
    bus = gce.Bus(name="Bus 1", Vnom=10.0)
    circuit.add_bus(bus)
    load = gce.Load()
    circuit.add_load(bus=bus, api_obj=load)
    entry = build_dynamic_editor_entry(load, circuit)
    assert entry is not None
    return circuit, load, entry


def test_workspace_reuses_existing_tab_and_remembers_last_mode() -> None:
    _get_app()
    manager = DynamicEditorWorkspaceManager.instance()
    manager.reset_for_tests()
    circuit, load, _entry = _build_load_entry()

    rms_page = manager.open_dynamic_editor_for(load, circuit, preferred_mode=DynamicSimulationMode.RMS)
    assert rms_page is not None
    workspace = manager._page_to_workspace[rms_page]
    assert workspace.ui.editorTabs.count() == 1

    same_page = manager.open_dynamic_editor_for(load, circuit)
    assert same_page is rms_page
    assert workspace.ui.editorTabs.count() == 1

    emt_page = manager.open_dynamic_editor_for(load, circuit, preferred_mode=DynamicSimulationMode.EMT, target_workspace=workspace)
    assert emt_page is not None
    assert emt_page is not rms_page
    assert workspace.ui.editorTabs.count() == 2

    manager.note_page_activated(emt_page)
    reopened = manager.open_dynamic_editor_for(load, circuit)
    assert reopened is emt_page

    manager.reset_for_tests()


def test_picker_quick_open_uses_alternate_mode_for_current_object() -> None:
    _get_app()
    _circuit, _load, entry = _build_load_entry()
    dialog = DynamicEditorPickerDialog(entries=[entry], current_entry=entry, current_mode=DynamicSimulationMode.RMS)

    assert not dialog.quickOpenGroupBox.isHidden()
    assert "EMT" in dialog.quickOpenButton.text()

    dialog._accept_quick_open()
    selection = dialog.get_selection()

    assert selection is not None
    assert selection[0] == entry
    assert selection[1] == DynamicSimulationMode.EMT


def test_workspace_manager_detaches_and_reattaches_tabs_between_windows() -> None:
    _get_app()
    manager = DynamicEditorWorkspaceManager.instance()
    manager.reset_for_tests()
    circuit, load, _entry = _build_load_entry()

    rms_page = manager.open_dynamic_editor_for(load, circuit, preferred_mode=DynamicSimulationMode.RMS)
    workspace = manager._page_to_workspace[rms_page]
    emt_page = manager.open_dynamic_editor_for(load, circuit, preferred_mode=DynamicSimulationMode.EMT, target_workspace=workspace)

    emt_index = workspace.index_of_page(emt_page)
    manager.handle_tab_drag_started(workspace, emt_index)
    manager.handle_tab_detach(workspace, workspace.pos())

    assert len(manager._workspaces) == 2
    detached_workspace = manager._page_to_workspace[emt_page]
    assert detached_workspace is not workspace
    assert workspace.ui.editorTabs.count() == 1
    assert detached_workspace.ui.editorTabs.count() == 1

    manager.handle_tab_drag_started(detached_workspace, detached_workspace.index_of_page(emt_page))
    manager.handle_tab_reattach(workspace, workspace.pos(), -1)

    assert manager._page_to_workspace[emt_page] is workspace
    assert workspace.ui.editorTabs.count() == 2

    manager.reset_for_tests()
