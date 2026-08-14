from __future__ import annotations

import gc
import sys

from PySide6 import QtCore, QtGui, QtWidgets
import shiboken6

from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_workspace_window import DynamicEditorWorkspaceWindow
from VeraGrid.Session.dynamic_editor_entries import build_dynamic_editor_entry
from VeraGrid.Session.dynamic_editor_workspace_session import DynamicEditorWorkspaceSession
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


def _build_dc_load_entry():
    circuit = gce.MultiCircuit(Sbase=100, fbase=50.0)
    bus = gce.Bus(name="DC Bus 1", Vnom=10.0, is_dc=True)
    circuit.add_bus(bus)
    load = gce.Load()
    circuit.add_load(bus=bus, api_obj=load)
    entry = build_dynamic_editor_entry(load, circuit)
    assert entry is not None
    return circuit, load, entry


def _build_workspace() -> DynamicEditorWorkspaceWindow:
    session = DynamicEditorWorkspaceSession()
    return DynamicEditorWorkspaceWindow(session=session)


def _reset_dynamic_editor_workspaces() -> None:
    """
    Close every dynamic-editor workspace that may still be alive in the test Qt process.

    :return: None.
    """
    app = QtWidgets.QApplication.instance()
    if app is None:
        return

    sessions: list[DynamicEditorWorkspaceSession] = list()
    widget: QtWidgets.QWidget
    for widget in app.topLevelWidgets():
        if isinstance(widget, DynamicEditorWorkspaceWindow) and widget.session not in sessions:
            sessions.append(widget.session)

    session: DynamicEditorWorkspaceSession
    for session in sessions:
        session.reset_for_tests()


def test_workspace_reuses_existing_tab_and_remembers_last_mode() -> None:
    _get_app()
    _reset_dynamic_editor_workspaces()
    circuit, load, _entry = _build_load_entry()
    workspace = _build_workspace()

    rms_page = workspace.open_dynamic_editor_for(
        load,
        circuit,
        preferred_mode=DynamicSimulationMode.RMS,
    )
    assert rms_page is not None
    assert workspace.ui.editorTabs.count() == 1

    same_page = workspace.open_dynamic_editor_for(load, circuit)
    assert same_page is rms_page
    assert workspace.ui.editorTabs.count() == 1

    emt_page = workspace.open_dynamic_editor_for(
        load,
        circuit,
        preferred_mode=DynamicSimulationMode.EMT,
        target_workspace=workspace,
    )
    assert emt_page is not None
    assert emt_page is not rms_page
    assert workspace.ui.editorTabs.count() == 2

    workspace.note_page_activated(emt_page)
    reopened = workspace.open_dynamic_editor_for(load, circuit)
    assert reopened is emt_page

    _reset_dynamic_editor_workspaces()


def test_tree_is_searchable_and_double_click_opens_rms() -> None:
    _get_app()
    _reset_dynamic_editor_workspaces()
    circuit, load, entry = _build_load_entry()
    workspace = _build_workspace()

    workspace.open_dynamic_editor_for(load, circuit, preferred_mode=DynamicSimulationMode.RMS)
    proxy_model = workspace.ui.treeView.model()
    assert proxy_model is not None

    parent_index = proxy_model.index(0, 0)
    device_index = proxy_model.index(0, 0, parent_index)
    assert device_index.isValid()

    modes = workspace._get_tree_entry_modes(device_index)
    assert DynamicSimulationMode.RMS in modes
    assert DynamicSimulationMode.EMT in modes

    workspace.ui.searchInTreeLineEdit.setText(entry.display_name[:2].lower())
    filtered_index = workspace.ui.treeView.currentIndex()
    assert filtered_index.isValid()
    assert workspace._entry_from_tree_index(filtered_index) is not None

    workspace._on_tree_double_clicked(filtered_index)
    assert workspace.current_page() is not None
    assert workspace.get_current_block_editor() is not None

    _reset_dynamic_editor_workspaces()


def test_tree_displays_device_icons() -> None:
    """
    Verify that the dynamic-editor tree shows device icons on both group and device rows.

    :return: None.
    """
    _get_app()
    _reset_dynamic_editor_workspaces()
    circuit, load, _entry = _build_load_entry()
    workspace = _build_workspace()

    workspace.open_dynamic_editor_for(load, circuit, preferred_mode=DynamicSimulationMode.RMS)
    proxy_model = workspace.ui.treeView.model()
    assert proxy_model is not None

    parent_index = proxy_model.index(0, 0)
    device_index = proxy_model.index(0, 0, parent_index)
    assert parent_index.isValid()
    assert device_index.isValid()

    parent_icon = proxy_model.data(parent_index, QtCore.Qt.ItemDataRole.DecorationRole)
    device_icon = proxy_model.data(device_index, QtCore.Qt.ItemDataRole.DecorationRole)

    assert isinstance(parent_icon, QtGui.QIcon)
    assert isinstance(device_icon, QtGui.QIcon)
    assert not parent_icon.isNull()
    assert not device_icon.isNull()

    _reset_dynamic_editor_workspaces()


def test_workspace_detaches_and_reattaches_tabs_between_windows() -> None:
    _get_app()
    _reset_dynamic_editor_workspaces()
    circuit, load, _entry = _build_load_entry()
    workspace = _build_workspace()

    rms_page = workspace.open_dynamic_editor_for(
        load,
        circuit,
        preferred_mode=DynamicSimulationMode.RMS,
    )
    assert workspace.current_page() is rms_page
    emt_page = workspace.open_dynamic_editor_for(
        load,
        circuit,
        preferred_mode=DynamicSimulationMode.EMT,
        target_workspace=workspace,
    )

    emt_index = workspace.index_of_page(emt_page)
    workspace._on_tab_drag_started(emt_index)
    workspace._on_tab_detach_requested(workspace.pos())

    assert len(workspace.get_open_workspaces()) == 2
    detached_workspace = workspace.workspace_for_page(emt_page)
    assert detached_workspace is not None
    assert detached_workspace is not workspace
    assert workspace.ui.editorTabs.count() == 1
    assert detached_workspace.ui.editorTabs.count() == 1

    detached_workspace._on_tab_drag_started(detached_workspace.index_of_page(emt_page))
    workspace._on_tab_reattach_requested(workspace.pos(), -1)

    assert workspace.workspace_for_page(emt_page) is workspace
    assert workspace.ui.editorTabs.count() == 2

    _reset_dynamic_editor_workspaces()


def test_workspace_opens_rms_editor_for_dc_bus_load() -> None:
    _get_app()
    _reset_dynamic_editor_workspaces()
    circuit, load, _entry = _build_dc_load_entry()
    workspace = _build_workspace()

    rms_page = workspace.open_dynamic_editor_for(
        load,
        circuit,
        preferred_mode=DynamicSimulationMode.RMS,
    )

    assert rms_page is not None
    assert workspace.get_current_block_editor() is not None

    _reset_dynamic_editor_workspaces()


def test_repeated_workspace_teardown_destroys_dynamic_editor_qt_objects() -> None:
    """
    Destroy every editor-owned Qt object across repeated open/close cycles.

    :return: None.
    """
    app: QtWidgets.QApplication = _get_app()
    _reset_dynamic_editor_workspaces()
    iteration: int
    for iteration in range(8):
        circuit, load, _entry = _build_load_entry()
        session = DynamicEditorWorkspaceSession()
        workspace = DynamicEditorWorkspaceWindow(session=session)
        page = workspace.open_dynamic_editor_for(
            load,
            circuit,
            preferred_mode=DynamicSimulationMode.EMT,
            target_workspace=workspace,
        )
        assert page is not None
        editor = page.editor
        assert editor is not None
        scene = editor.scene
        view = editor.view
        assert scene is not None
        assert view is not None

        workspace.close_tab_at(workspace.index_of_page(page))

        assert editor.scene is None
        assert editor.view is None
        assert scene.editor is None
        assert len(scene.items()) == 0
        assert page.editor is None
        assert len(session._session_pages) == 0

        QtCore.QCoreApplication.sendPostedEvents(
            None,
            QtCore.QEvent.Type.DeferredDelete,
        )
        app.processEvents()
        gc.collect()

        assert not shiboken6.isValid(scene)
        assert not shiboken6.isValid(view)
        assert not shiboken6.isValid(editor)
        assert not shiboken6.isValid(page)

    _reset_dynamic_editor_workspaces()
