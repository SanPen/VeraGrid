from __future__ import annotations

import gc
import math
import sys
from pathlib import Path

import numpy as np
import pytest
from PySide6 import QtCore, QtWidgets
from PySide6.QtTest import QTest

import VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor as dynamic_block_editor_module
import VeraGridEngine.api as gce
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import DynamicBlockEditorGUI
from VeraGrid.Gui.DynamicModelEditor.ElementDialogues.lookup_table_dialog import LookupArrayLinearDialog
from VeraGrid.Gui.DynamicModelEditor.ElementDialogues.lookup_table_dialog import LookupMatrixLinearDialog
from VeraGrid.Gui.DynamicModelEditor.ElementDialogues.lookup_table_dialog import _copy_selected_table_range_to_clipboard
from VeraGrid.Gui.DynamicModelEditor.ElementDialogues.lookup_table_dialog import _parse_clipboard_grid
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_runtime import get_jmarti_block_fit_bundle
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.BasicBlockCatalog import BasicBlockTemplateDescriptor
from VeraGridEngine.Templates.BasicBlockCatalog import get_basic_block_catalog_descriptor_by_key
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import BlockType
from VeraGridEngine.enumerations import DynamicSimulationMode
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.enumerations import ShuntConnectionType
from VeraGridEngine.enumerations import WindingType

pytestmark = pytest.mark.filterwarnings("error")


class _ApiStub:
    """
    Minimal API object accepted by the dynamic block editor tests.
    """

    __slots__ = ("name", "rms_template", "emt_template", "device_type")

    def __init__(self) -> None:
        self.name = "Stub"
        self.rms_template = None
        self.emt_template = None
        self.device_type = DeviceType.NoDevice


def _get_app() -> QtWidgets.QApplication:
    """
    Get or create the Qt application used by GUI tests.
    """

    app: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if app is None:
        return QtWidgets.QApplication(sys.argv)
    else:
        return app


def _collect_pending_resources() -> None:
    """
    Flush any leaked resources from earlier tests before this GUI test runs.
    """

    for generation in (0, 1, 2):
        gc.collect(generation=generation)


def _find_index_by_label(model: QtCore.QAbstractItemModel,
                         label: str,
                         parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> QtCore.QModelIndex:
    """
    Find one recursive model index by visible label.
    """

    row_count: int = model.rowCount(parent)
    row: int
    for row in range(row_count):
        index = model.index(row, 0, parent)
        if str(model.data(index, QtCore.Qt.ItemDataRole.DisplayRole)) == label:
            return index

        child = _find_index_by_label(model, label, index)
        if child.isValid():
            return child
        else:
            pass

    return QtCore.QModelIndex()


def _collect_leaf_labels(model: QtCore.QAbstractItemModel,
                         parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> list[str]:
    """
    Collect all visible leaf labels from one recursive model.
    """

    labels: list[str] = list()
    row_count: int = model.rowCount(parent)
    row: int

    for row in range(row_count):
        index = model.index(row, 0, parent)
        if model.rowCount(index) == 0:
            labels.append(str(model.data(index, QtCore.Qt.ItemDataRole.DisplayRole)))
        else:
            labels.extend(_collect_leaf_labels(model, index))

    return labels


def _count_descriptor_leaves(editor: DynamicBlockEditorGUI,
                             parent_item) -> int:
    """
    Count basic block descriptor leaves below one source-model item.
    """

    count: int = 0
    row: int
    for row in range(parent_item.rowCount()):
        child = parent_item.child(row)
        if child.hasChildren():
            count += _count_descriptor_leaves(editor, child)
        else:
            payload = child.data(editor.block_role)
            if isinstance(payload, BasicBlockTemplateDescriptor):
                count += 1
            else:
                pass

    return count


def _build_editor(mode: DynamicSimulationMode = DynamicSimulationMode.EMT,
                  api_object=None,
                  circuit=None) -> DynamicBlockEditorGUI:
    """
    Build one dynamic block editor instance for GUI tests.
    """


    if circuit is None:
        circuit = MultiCircuit()

    _get_app()
    resolved_api_object = api_object if api_object is not None else _ApiStub()
    editor = DynamicBlockEditorGUI(
        var_factory=VarFactory(),
        block=Block(),
        api_object=resolved_api_object,
        mode=mode,
        templates_list=list(),
        circuit=circuit,
        main_editor=False,
        modal=False,
    )
    editor.show()
    editor.activateWindow()
    return editor


def _build_catalog_block_item(editor: DynamicBlockEditorGUI, template_key: str):
    """
    Materialize one catalog block on the editor canvas.
    """

    descriptor = get_basic_block_catalog_descriptor_by_key()[template_key]
    block_item = editor.create_library_payload_item(descriptor, 10.0, 20.0)
    assert block_item is not None
    return block_item

def _label_texts(label_items) -> list[str]:
    """
    Collect plain-text labels from one graphics label list.
    """

    return [item.toPlainText() for item in label_items]


def _port_name_prefixes(block_item) -> list[str]:
    """
    Extract stable name prefixes from one block item input port list.
    """

    prefixes: list[str] = list()
    for port in block_item.inputs:
        assert port.base_var is not None
        full_name = port.base_var.name
        if full_name.startswith("grd_up_"):
            prefixes.append("grd_up")
        elif full_name.startswith("grd_down_"):
            prefixes.append("grd_down")
        elif full_name.startswith("y_max_"):
            prefixes.append("y_max")
        elif full_name.startswith("y_min_"):
            prefixes.append("y_min")
        elif full_name.startswith("yi_"):
            prefixes.append("yi")
        else:
            prefixes.append(full_name)

    return prefixes


def _port_full_names(block_item) -> list[str]:
    """
    Extract full input port names from one block item.
    """

    names: list[str] = list()
    for port in block_item.inputs:
        assert port.base_var is not None
        names.append(port.base_var.name)
    return names


def _find_prefixed_event_constant(block: Block, prefix: str) -> float:
    """
    Find one constant-valued event entry whose key name starts with ``prefix``.
    """

    parameter_var, parameter_expr = next(
        ((var, expr) for var, expr in block.event_dict.items() if var.name.startswith(prefix)),
        (None, None),
    )
    if parameter_var is not None and parameter_expr is not None:
        assert parameter_expr.value is not None
        return float(parameter_expr.value)
    else:
        pass

    child: Block
    for child in block.children:
        parameter_var, parameter_expr = next(
            ((var, expr) for var, expr in child.event_dict.items() if var.name.startswith(prefix)),
            (None, None),
        )
        if parameter_var is not None and parameter_expr is not None:
            assert parameter_expr.value is not None
            return float(parameter_expr.value)
        else:
            pass

    raise AssertionError(f"Missing event constant with prefix '{prefix}'")


def _state_var_names(block: Block) -> list[str]:
    """
    Return the symbolic state-variable names of one block.
    """

    return list(var.name for var in block.state_vars)


def _find_scene_block_item(editor: DynamicBlockEditorGUI, block_uid: int):
    """
    Find one visible scene block item by symbolic block uid.
    """

    scene_item: object
    for scene_item in editor.scene.items():
        if isinstance(scene_item, dynamic_block_editor_module.BlockItem):
            if scene_item.subsys is not None and scene_item.subsys.uid == block_uid:
                return scene_item
            else:
                pass
        else:
            pass

    raise AssertionError(f"Missing scene block item for uid '{block_uid}'")


def test_emt_editor_exposes_basic_block_catalog_under_basic() -> None:
    editor = _build_editor(DynamicSimulationMode.EMT)
    source_model = editor.library.library_model
    basic_item = source_model.invisibleRootItem().child(0)
    native_item = basic_item.child(0)

    assert basic_item.text() == "Basic"
    assert basic_item.rowCount() == 1
    assert native_item.text() == "Native"
    assert native_item.child(0).text() == "Arithmetic"
    assert _find_index_by_label(editor.library.library_model, "Scaling and Products").isValid()
    assert not _find_index_by_label(editor.library.library_model, "Arithmetic and Products").isValid()
    assert _count_descriptor_leaves(editor, native_item) == 545

    editor.close()


def test_rms_editor_exposes_basic_block_catalog_under_basic() -> None:
    editor = _build_editor(DynamicSimulationMode.RMS)
    source_model = editor.library.library_model
    basic_item = source_model.invisibleRootItem().child(0)
    native_item = basic_item.child(0)

    assert basic_item.text() == "Basic"
    assert basic_item.rowCount() == 1
    assert native_item.text() == "Native"
    assert _count_descriptor_leaves(editor, native_item) == 545

    editor.close()


def test_library_search_button_and_shortcut_filter_basic_catalog() -> None:
    _collect_pending_resources()
    editor = _build_editor(DynamicSimulationMode.EMT)
    editor.raise_()
    QTest.qWaitForWindowExposed(editor)
    QtWidgets.QApplication.processEvents()
    descriptor_by_key = get_basic_block_catalog_descriptor_by_key()
    park_label = descriptor_by_key["park_transform_dq"].display_label
    limit_label = descriptor_by_key["limit"].display_label

    assert editor.ui.librarySearchLineEdit.isVisible()
    editor.ui.librarySearchLineEdit.clearFocus()
    QTest.keyClick(editor, QtCore.Qt.Key.Key_F, QtCore.Qt.KeyboardModifier.ControlModifier)
    QtWidgets.QApplication.processEvents()
    QTest.qWait(100)

    assert editor.ui.librarySearchLineEdit.hasFocus()

    editor.ui.librarySearchLineEdit.clearFocus()
    editor.focus_library_search()
    QtWidgets.QApplication.processEvents()
    QTest.qWait(100)
    assert editor.ui.librarySearchLineEdit.hasFocus()

    editor.ui.librarySearchLineEdit.setText("park transform")
    QtWidgets.QApplication.processEvents()

    visible_leaf_labels = _collect_leaf_labels(editor.library_proxy_model)
    assert park_label in visible_leaf_labels
    assert limit_label not in visible_leaf_labels


    editor.close()
    editor.deleteLater()
    QtWidgets.QApplication.processEvents()
    QTest.qWait(50)
    QtWidgets.QApplication.processEvents()


def test_proxy_drag_payload_materializes_catalog_template() -> None:
    editor = _build_editor(DynamicSimulationMode.EMT)
    park_descriptor = get_basic_block_catalog_descriptor_by_key()["park_transform_dq"]
    park_label = park_descriptor.display_label
    source_index = _find_index_by_label(editor.library.library_model, park_label)

    assert source_index.isValid()

    proxy_index = editor.library_proxy_model.mapFromSource(source_index)
    assert proxy_index.isValid()

    mime_data = editor.library_proxy_model.mimeData([proxy_index])
    payload = editor.get_library_payload_from_mime_data(mime_data)

    assert payload is not None
    assert isinstance(payload, BasicBlockTemplateDescriptor)
    assert payload.template_key == "park_transform_dq"

    block_item = editor.create_library_payload_item(payload, 10.0, 20.0)
    assert block_item is not None
    assert len(editor.main_block.children) == 1

    editor.has_unapplied_changes = False
    editor.close()


def test_limit_signal_variant_exposes_signal_ports_while_parameter_variant_does_not() -> None:
    editor = _build_editor(DynamicSimulationMode.EMT)
    signal_block = _build_catalog_block_item(editor, "limit_s_form_b")
    parameter_block = _build_catalog_block_item(editor, "limit_p_form_c")

    assert len(signal_block.inputs) == 3
    assert _port_name_prefixes(signal_block) == ["yi", "y_max", "y_min"]

    assert len(parameter_block.inputs) == 1
    assert _port_name_prefixes(parameter_block) == ["yi"]
    assert {const.name for const in parameter_block.subsys.event_dict.values()} == {"y_max", "y_min"}

    editor.has_unapplied_changes = False
    editor.close()


def test_rate_limiter_signal_variant_exposes_gradient_ports_while_parameter_variant_keeps_parameter_table() -> None:
    editor = _build_editor(DynamicSimulationMode.EMT)
    signal_block = _build_catalog_block_item(editor, "rate_limiter_s")
    parameter_block = _build_catalog_block_item(editor, "rate_limiter_p_form_c")

    assert len(signal_block.inputs) == 3
    assert _port_name_prefixes(signal_block) == ["yi", "grd_up", "grd_down"]

    assert len(parameter_block.inputs) == 1
    assert _port_name_prefixes(parameter_block) == ["yi"]
    assert {const.name for const in parameter_block.subsys.event_dict.values()} == {"grd"}

    editor.has_unapplied_changes = False
    editor.close()


def test_side_panel_loads_only_the_visible_table_for_selected_block() -> None:
    editor = _build_editor(DynamicSimulationMode.EMT)
    block_item = _build_catalog_block_item(editor, "pulse")

    editor.ui.toolBox.setCurrentWidget(editor.ui.page_7)
    editor.scene.clearSelection()
    block_item.setSelected(True)
    QtWidgets.QApplication.processEvents()

    assert editor.variables_model.rowCount() == 0
    assert editor.parameters_model.rowCount() == 0
    assert editor.equations_model.rowCount() == 0

    editor.ui.toolBox.setCurrentWidget(editor.ui.page_2)
    QtWidgets.QApplication.processEvents()

    assert editor.parameters_model.rowCount() > 0
    assert editor.variables_model.rowCount() == 0
    assert editor.equations_model.rowCount() == 0

    editor.has_unapplied_changes = False
    editor.close()


def test_parameter_edit_does_not_rebuild_scene_for_non_structural_change() -> None:
    editor = _build_editor(DynamicSimulationMode.EMT)
    block_item = _build_catalog_block_item(editor, "pulse")
    rebuild_calls: list[str] = list()

    editor.scene.clearSelection()
    block_item.setSelected(True)
    editor.ui.toolBox.setCurrentWidget(editor.ui.page_2)
    QtWidgets.QApplication.processEvents()

    assert editor.parameters_model.rowCount() > 0

    def _record_rebuild() -> None:
        rebuild_calls.append("rebuild")

    editor.rebuild_scene_from_diagram = _record_rebuild
    value_index = editor.parameters_model.index(0, 2)

    assert editor.parameters_model.setData(value_index, 1.0, QtCore.Qt.ItemDataRole.EditRole)
    QtWidgets.QApplication.processEvents()
    assert rebuild_calls == list()

    editor.has_unapplied_changes = False
    editor.close()


def test_parameter_panel_includes_mode_parameters_for_pulse_block() -> None:
    editor = _build_editor(DynamicSimulationMode.EMT)
    block_item = _build_catalog_block_item(editor, "pulse")

    editor.scene.clearSelection()
    block_item.setSelected(True)
    editor.ui.toolBox.setCurrentWidget(editor.ui.page_2)
    QtWidgets.QApplication.processEvents()

    row_types: list[str] = list()
    row_index: int
    for row_index in range(editor.parameters_model.rowCount()):
        index = editor.parameters_model.index(row_index, 0)
        row_types.append(str(editor.parameters_model.data(index, QtCore.Qt.ItemDataRole.DisplayRole)))

    assert "Event Parameter" in row_types
    assert "Mode Parameter" in row_types

    editor.has_unapplied_changes = False
    editor.close()


def test_lookup_array_linear_dialog_parses_clipboard_rows() -> None:
    _get_app()
    dialog = LookupArrayLinearDialog(block_label="Lookup array (linear)")
    clipboard = QtWidgets.QApplication.clipboard()
    clipboard.setText("0\t0\n1\t10\n2\t20")

    dialog.paste_from_clipboard()
    dialog.accept_dialog()
    x_points, y_points = dialog.get_points()

    assert x_points == [0.0, 1.0, 2.0]
    assert y_points == [0.0, 10.0, 20.0]
    dialog.close()


def test_lookup_array_linear_dialog_supports_copy_paste_and_delete_shortcuts() -> None:
    _get_app()
    dialog = LookupArrayLinearDialog(block_label="Lookup array (linear)")
    dialog.show()
    dialog.activateWindow()
    dialog.raise_()
    QTest.qWaitForWindowExposed(dialog)
    QtWidgets.QApplication.processEvents()
    clipboard = QtWidgets.QApplication.clipboard()
    clipboard.clear()
    QtWidgets.QApplication.processEvents()
    QTest.qWait(50)

    dialog._table_widget.clearSelection()
    selection = QtWidgets.QTableWidgetSelectionRange(0, 0, 0, 1)
    dialog._table_widget.setRangeSelected(selection, True)
    dialog._table_widget.setFocus()
    QtWidgets.QApplication.processEvents()

    dialog.copy_selection_to_clipboard()
    QtWidgets.QApplication.processEvents()
    QTest.qWait(50)
    assert clipboard.text().strip() == "0.0\t0.0"

    clipboard.setText("3\t30\n4\t40")
    dialog._table_widget.clearSelection()
    dialog._table_widget.setFocus()
    QtWidgets.QApplication.processEvents()

    dialog.paste_from_clipboard()
    QtWidgets.QApplication.processEvents()
    QTest.qWait(50)
    x_points, y_points = dialog._read_points_from_table()
    assert x_points == [3.0, 4.0, 2.0]
    assert y_points == [30.0, 40.0, 20.0]

    dialog._table_widget.clearSelection()
    selection = QtWidgets.QTableWidgetSelectionRange(0, 0, 0, 1)
    dialog._table_widget.setRangeSelected(selection, True)
    dialog._table_widget.setFocus()
    QtWidgets.QApplication.processEvents()

    dialog.delete_selection()
    QtWidgets.QApplication.processEvents()
    QTest.qWait(50)
    assert dialog._table_widget.rowCount() == 2
    dialog.close()


def test_lookup_array_linear_dialog_header_click_selects_full_column() -> None:
    _get_app()
    dialog: LookupArrayLinearDialog = LookupArrayLinearDialog(block_label="Lookup array (linear)")

    dialog.select_column_by_header(0)
    QtWidgets.QApplication.processEvents()
    selected_indexes: list[QtCore.QModelIndex] = dialog._table_widget.selectionModel().selectedIndexes()

    assert len(selected_indexes) == dialog._table_widget.rowCount()
    assert all(index.column() == 0 for index in selected_indexes)
    dialog.close()


def test_lookup_array_linear_dialog_supports_custom_axis_labels_and_preview() -> None:
    _get_app()
    dialog: LookupArrayLinearDialog = LookupArrayLinearDialog(
        block_label="Nonlinear resistor EMT V-I curve",
        initial_points=list([(0.0, 0.0), (1.0, 0.1), (1.5, 1.0)]),
        x_label="V",
        y_label="I",
        preview_enabled=True,
        preview_title="Nonlinear resistor EMT V-I curve",
    )

    assert dialog._table_widget.horizontalHeaderItem(0).text() == "V"
    assert dialog._table_widget.horizontalHeaderItem(1).text() == "I"
    button_texts: list[str] = list(button.text() for button in dialog.findChildren(QtWidgets.QPushButton))
    assert "Sort by V" in button_texts
    assert "Preview Curve" in button_texts

    dialog.show_plot_preview()
    QtWidgets.QApplication.processEvents()

    assert dialog._preview_dialog is not None
    assert dialog._preview_dialog.windowTitle() == "Nonlinear resistor EMT V-I curve"
    dialog._preview_dialog.close()
    dialog.close()


def test_lookup_array_linear_descriptor_uses_modal_points_to_build_block(override_attrs) -> None:
    editor = _build_editor(DynamicSimulationMode.EMT)
    descriptor = get_basic_block_catalog_descriptor_by_key()["lookup_array_linear"]

    class _DialogStub:
        def __init__(self, block_label: str, initial_points=None, parent=None) -> None:
            _unused = (block_label, initial_points, parent)

        def exec(self) -> int:
            return int(QtWidgets.QDialog.DialogCode.Accepted)

        def get_points(self) -> tuple[list[float], list[float]]:
            return [0.0, 2.0, 4.0], [0.0, 20.0, 40.0]

    override_attrs.setattr(dynamic_block_editor_module, "LookupArrayLinearDialog", _DialogStub)
    block_item = editor.create_library_payload_item(descriptor, 10.0, 20.0)

    assert block_item is not None
    assert any(var.name.startswith("arr_x3_") for var in block_item.subsys.event_dict.keys())
    assert any(var.name.startswith("arr_y3_") for var in block_item.subsys.event_dict.keys())

    editor.has_unapplied_changes = False
    editor.close()


def test_jmarti_line_emt_block_builds_sequence_fit_and_persists_diagnostics(override_attrs) -> None:
    circuit = gce.MultiCircuit(Sbase=25.0, fbase=50.0)
    bus0 = gce.Bus(name="BusSeqGui0", Vnom=110.0)
    bus1 = gce.Bus(name="BusSeqGui1", Vnom=110.0)
    line = gce.Line(
        name="LineSeqGui",
        bus_from=bus0,
        bus_to=bus1,
        length=5.0,
        template=gce.SequenceLineType(R=0.12, X=0.35, B=3.0, R0=0.28, X0=0.78, B0=1.8),
    )
    editor = _build_editor(DynamicSimulationMode.EMT, api_object=line, circuit=circuit)

    class _DialogStub:
        def __init__(self, parent=None, initial_config=None) -> None:
            _unused = (parent, initial_config)

        def exec(self) -> int:
            return int(QtWidgets.QDialog.DialogCode.Accepted)

        def get_configuration(self) -> dict[str, object]:
            return dict({
                "phase_n": False,
                "phase_a": True,
                "phase_b": True,
                "phase_c": True,
                "data_source_mode": "auto_template",
                "nominal_frequency_hz": 50.0,
                "import_file_path": "",
                "import_line_length_m": 0.0,
                "sweep_low_hz": 10.0,
                "sweep_high_hz": 640.0,
                "sweep_sample_count": 6,
                "reference_frequency_hz": 0.0,
                "use_frequency_exploration_window": False,
                "exploration_low_hz": 0.0,
                "exploration_high_hz": 0.0,
                "use_delay_fit_window": False,
                "delay_fit_low_hz": 0.0,
                "delay_fit_high_hz": 0.0,
                "decoupling_warning_tolerance": 1.0e-2,
                "loewner_relative_tolerance": 1.0e-8,
                "maximum_model_order": 40,
                "forced_model_order": 1,
                "minimum_frequency_samples": 4,
                "vf_max_iterations": 6,
                "vf_pole_shift_tolerance": 1.0e-6,
                "vf_enforce_stable_poles": True,
                "vf_stability_real_part_floor": 1.0e-8,
                "vf_include_constant_term": True,
                "vf_include_proportional_term": False,
                "passivity_frequency_sample_count": 256,
                "passivity_minimum_real_yc_tolerance": 1.0e-8,
                "passivity_maximum_hres_gain_tolerance": 1.0e-6,
            })

    override_attrs.setattr(dynamic_block_editor_module, "JMartiLineEmtDialog", _DialogStub)
    block_item = editor.create_library_payload_item(BlockType.EMT_JMARTI_LINE, 10.0, 20.0)
    assert block_item is not None
    assert get_jmarti_block_fit_bundle(block_item.subsys) is not None

    modal_kind, modal_config = editor.get_modal_template_metadata(block_item.subsys)
    assert modal_kind == "jmarti_line_emt"
    assert modal_config is not None
    assert modal_config["fit_ready"] is True
    assert "Fit computed" in str(modal_config["fit_status"])
    assert "Automatic RLGC sweep from SequenceLineType" in str(modal_config["fit_diagnostics_text"])
    assert "Mode 0:" in str(modal_config["fit_diagnostics_text"])

    editor.has_unapplied_changes = False
    editor.close()


def test_jmarti_line_emt_block_builds_fit_from_imported_npz(override_attrs, tmp_path: Path) -> None:
    circuit = gce.MultiCircuit(Sbase=25.0, fbase=60.0)
    bus0 = gce.Bus(name="BusImportGui0", Vnom=13.8)
    bus1 = gce.Bus(name="BusImportGui1", Vnom=13.8)
    line = gce.Line(name="LineImportGui", bus_from=bus0, bus_to=bus1, length=1.8)
    editor = _build_editor(DynamicSimulationMode.EMT, api_object=line, circuit=circuit)
    frequency_hz: np.ndarray = np.asarray([10.0, 40.0, 160.0, 640.0], dtype=np.float64)
    z_per_length: np.ndarray = np.zeros((4, 3, 3), dtype=np.complex128)
    y_per_length: np.ndarray = np.zeros((4, 3, 3), dtype=np.complex128)
    sample_index: int = 0
    npz_path: Path = tmp_path / "jmarti_gui_import.npz"

    while sample_index < 4:
        z_per_length[sample_index, :, :] = np.diag(np.asarray([
            0.12 + 1j * (0.20 + 0.02 * sample_index),
            0.13 + 1j * (0.25 + 0.02 * sample_index),
            0.15 + 1j * (0.30 + 0.02 * sample_index),
        ], dtype=np.complex128))
        y_per_length[sample_index, :, :] = np.diag(np.asarray([
            1j * (3.0e-6 + 2.0e-7 * sample_index),
            1j * (3.2e-6 + 2.0e-7 * sample_index),
            1j * (3.4e-6 + 2.0e-7 * sample_index),
        ], dtype=np.complex128))
        sample_index += 1

    np.savez(
        npz_path,
        frequency_hz=frequency_hz,
        z_per_length=z_per_length,
        y_per_length=y_per_length,
        phase_labels=np.asarray(["A", "B", "C"]),
        line_length_m=np.asarray([1800.0], dtype=np.float64),
    )

    class _DialogStub:
        def __init__(self, parent=None, initial_config=None) -> None:
            _unused = (parent, initial_config)

        def exec(self) -> int:
            return int(QtWidgets.QDialog.DialogCode.Accepted)

        def get_configuration(self) -> dict[str, object]:
            return dict({
                "phase_n": False,
                "phase_a": True,
                "phase_b": False,
                "phase_c": True,
                "data_source_mode": "import_frequency_samples",
                "nominal_frequency_hz": 60.0,
                "import_file_path": str(npz_path),
                "import_line_length_m": 0.0,
                "sweep_low_hz": 10.0,
                "sweep_high_hz": 640.0,
                "sweep_sample_count": 6,
                "reference_frequency_hz": 0.0,
                "use_frequency_exploration_window": False,
                "exploration_low_hz": 0.0,
                "exploration_high_hz": 0.0,
                "use_delay_fit_window": False,
                "delay_fit_low_hz": 0.0,
                "delay_fit_high_hz": 0.0,
                "decoupling_warning_tolerance": 1.0e-2,
                "loewner_relative_tolerance": 1.0e-8,
                "maximum_model_order": 40,
                "forced_model_order": 1,
                "minimum_frequency_samples": 4,
                "vf_max_iterations": 6,
                "vf_pole_shift_tolerance": 1.0e-6,
                "vf_enforce_stable_poles": True,
                "vf_stability_real_part_floor": 1.0e-8,
                "vf_include_constant_term": True,
                "vf_include_proportional_term": False,
                "passivity_frequency_sample_count": 256,
                "passivity_minimum_real_yc_tolerance": 1.0e-8,
                "passivity_maximum_hres_gain_tolerance": 1.0e-6,
            })

    override_attrs.setattr(dynamic_block_editor_module, "JMartiLineEmtDialog", _DialogStub)
    block_item = editor.create_library_payload_item(BlockType.EMT_JMARTI_LINE, 10.0, 20.0)
    assert block_item is not None
    assert get_jmarti_block_fit_bundle(block_item.subsys) is not None

    modal_kind, modal_config = editor.get_modal_template_metadata(block_item.subsys)
    assert modal_kind == "jmarti_line_emt"
    assert modal_config is not None
    assert modal_config["fit_ready"] is True
    assert str(npz_path) in str(modal_config["fit_source_description"])
    assert "Source: Imported NPZ samples" in str(modal_config["fit_diagnostics_text"])
    assert "Phases: A, C" in str(modal_config["fit_diagnostics_text"])

    editor.has_unapplied_changes = False
    editor.close()


def test_line_emt_editor_exposes_jmarti_device_block() -> None:
    circuit = gce.MultiCircuit(Sbase=25.0, fbase=60.0)
    bus0 = gce.Bus(name="BusLineDevice0", Vnom=13.8)
    bus1 = gce.Bus(name="BusLineDevice1", Vnom=13.8)
    line = gce.Line(name="LineDeviceGui", bus_from=bus0, bus_to=bus1)
    editor = _build_editor(DynamicSimulationMode.EMT, api_object=line, circuit=circuit)
    leaf_labels = _collect_leaf_labels(editor.library.library_model)

    assert "Emt pi line" in leaf_labels
    assert "Emt Bergeron line" in leaf_labels
    assert "Emt JMarti line" in leaf_labels

    editor.has_unapplied_changes = False
    editor.close()


def test_simple_r_emt_shunt_block_supports_delta_configuration(override_attrs) -> None:
    circuit = gce.MultiCircuit(Sbase=25.0, fbase=60.0)
    bus = gce.Bus(name="BusSimpleRDelta", Vnom=13.8)
    load = gce.Load(name="LoadSimpleRDelta")
    load.bus = bus
    load.conn = ShuntConnectionType.Delta
    editor = _build_editor(DynamicSimulationMode.EMT, api_object=load, circuit=circuit)

    class _CreateDialogStub:
        def __init__(self,
                     component_kind: str,
                     parent=None,
                     initial_config=None,
                     allow_static_device_values: bool = False,
                     static_connection_type: ShuntConnectionType | None = None,
                     nominal_voltage_kv=None,
                     base_power_mva=None,
                     base_frequency_hz=None) -> None:
            _unused = (parent, initial_config, nominal_voltage_kv, base_power_mva, base_frequency_hz)
            assert component_kind == "R"
            assert allow_static_device_values is True
            assert static_connection_type == ShuntConnectionType.Delta

        def exec(self) -> int:
            return int(QtWidgets.QDialog.DialogCode.Accepted)

        def get_configuration(self) -> dict[str, object]:
            return dict({
                "include_r": True,
                "include_l": False,
                "include_c": False,
                "phA": True,
                "phB": True,
                "phC": False,
                "connection_type": ShuntConnectionType.Delta,
                "use_static_device_values": False,
                "input_mode": "physical",
                "resistance_ohm": 25.0,
                "inductive_value": 0.01,
                "capacitive_value": 1.0e-6,
            })

    override_attrs.setattr(dynamic_block_editor_module, "ShuntComponentEmtDialog", _CreateDialogStub)
    block_item = editor.create_library_payload_item(BlockType.R_LOAD_EMT, 10.0, 20.0)
    assert block_item is not None

    modal_kind, modal_config = editor.get_modal_template_metadata(block_item.subsys)
    assert modal_kind == "shunt_component_emt"
    assert modal_config is not None
    assert modal_config["connection_type"] == ShuntConnectionType.Delta
    assert modal_config["use_static_device_values"] is False
    assert not any(node.tpe == BlockType.GROUNDING_LINK_EMT.name for node in block_item.subsys.diagram.node_data.values())
    assert _find_prefixed_event_constant(block_item.subsys, "R_AB") == pytest.approx(25.0)
    assert load.conn == ShuntConnectionType.Delta

    editor.has_unapplied_changes = False
    editor.close()
#
#
# def test_transformer_type_emt_editor_exposes_transformer_blocks_and_inherits_hv_lv_topology(override_attrs) -> None:
#     circuit = gce.MultiCircuit(Sbase=25.0, fbase=60.0)
#     transformer_type = gce.TransformerType()
#     transformer_type.conn_hv = WindingType.Delta
#     transformer_type.conn_lv = WindingType.GroundedStar
#     editor = _build_editor(DynamicSimulationMode.EMT, api_object=transformer_type, circuit=circuit)
#
#     class _DialogMustNotOpen:
#         def __init__(self, *args, **kwargs) -> None:
#             raise AssertionError("Transformer topology dialog should not open when the transformer type already defines conn_hv/conn_lv")
#
#     override_attrs.setattr(dynamic_block_editor_module, "TransformerTopologyEmtDialog", _DialogMustNotOpen)
#     leaf_labels = _collect_leaf_labels(editor.library_model)
#
#     assert "Transformer" in leaf_labels
#     assert "XFMR Transformer" in leaf_labels
#     # assert "ZIP load" in leaf_labels # should not be in the transformer library
#     # assert "Switch EMT" in leaf_labels # should not be in the transformer library
#     # assert "Emt pi line" not in leaf_labels # should not be in the transformer library
#     block_item = editor.create_library_payload_item(BlockType.TRAFO_EMT, 10.0, 20.0)
#     assert block_item is not None
#
#     modal_kind, modal_config = editor.get_modal_template_metadata(block_item.subsys)
#     assert modal_kind == "transformer_topology_emt"
#     assert modal_config is not None
#     assert modal_config["conn_f"] == WindingType.Delta
#     assert modal_config["conn_t"] == WindingType.GroundedStar
#     assert modal_config["allow_modify_template"] is False
#
#     editor.has_unapplied_changes = False
#     editor.close()

#
# def test_transformer_type_emt_editor_inherits_zigzag_without_modal(override_attrs) -> None:
#     circuit = gce.MultiCircuit(Sbase=25.0, fbase=60.0)
#     transformer_type = gce.TransformerType()
#     transformer_type.conn_hv = WindingType.ZigZag
#     transformer_type.conn_lv = WindingType.GroundedStar
#     editor = _build_editor(DynamicSimulationMode.EMT, api_object=transformer_type, circuit=circuit)
#
#     class _DialogMustNotOpen:
#         def __init__(self, *args, **kwargs) -> None:
#             raise AssertionError("Transformer topology dialog should not open when the transformer type already defines conn_hv/conn_lv")
#
#     override_attrs.setattr(dynamic_block_editor_module, "TransformerTopologyEmtDialog", _DialogMustNotOpen)
#     block_item = editor.create_library_payload_item(BlockType.TRAFO_EMT, 10.0, 20.0)
#     assert block_item is not None
#
#     modal_kind, modal_config = editor.get_modal_template_metadata(block_item.subsys)
#     assert modal_kind == "transformer_topology_emt"
#     assert modal_config is not None
#     assert modal_config["conn_f"] == WindingType.ZigZag
#     assert modal_config["conn_t"] == WindingType.GroundedStar
#     assert _port_full_names(block_item)[:3] == ["vf_A_transformer_emt_template", "vf_B_transformer_emt_template", "vf_C_transformer_emt_template"]
#
#     editor.has_unapplied_changes = False
#     editor.close()

#
# def test_transformer_emt_block_falls_back_to_manual_dialog_without_device_topology(override_attrs) -> None:
#     editor = _build_editor(DynamicSimulationMode.EMT)
#
#     class _DialogStub:
#         def __init__(self, title: str, parent=None, initial_config=None, static_from_connection=None, static_to_connection=None) -> None:
#             _unused = (parent, initial_config)
#             assert title == "Configure EMT Transformer Topology"
#             assert static_from_connection is None
#             assert static_to_connection is None
#
#         def exec(self) -> int:
#             return int(QtWidgets.QDialog.DialogCode.Accepted)
#
#         def get_configuration(self) -> dict[str, object]:
#             return dict({
#                 "conn_f": WindingType.Delta,
#                 "conn_t": WindingType.GroundedStar,
#             })
#
#     override_attrs.setattr(dynamic_block_editor_module, "TransformerTopologyEmtDialog", _DialogStub)
#     block_item = editor.create_library_payload_item(BlockType.TRAFO_EMT, 10.0, 20.0)
#
#     assert block_item is not None
#     modal_kind, modal_config = editor.get_modal_template_metadata(block_item.subsys)
#     assert modal_kind == "transformer_topology_emt"
#     assert modal_config is not None
#     assert modal_config["conn_f"] == WindingType.Delta
#     assert modal_config["conn_t"] == WindingType.GroundedStar
#     assert modal_config["allow_modify_template"] is True
#     assert _transformer_modal_config_allows_modify(modal_kind, modal_config) is True
#
#     editor.has_unapplied_changes = False
#     editor.close()
#

def test_ground_emt_block_is_available_from_library() -> None:
    editor = _build_editor(DynamicSimulationMode.EMT)
    block_item = editor.create_library_payload_item(BlockType.GROUND_EMT, 10.0, 20.0)

    assert block_item is not None
    assert len(block_item.inputs) == 1
    assert len(block_item.outputs) == 1

    editor.has_unapplied_changes = False
    editor.close()


def test_lookup_matrix_linear_dialog_parses_clipboard_matrix() -> None:
    _get_app()
    dialog = LookupMatrixLinearDialog(block_label="Lookup matrix (linear)")
    clipboard = QtWidgets.QApplication.clipboard()
    clipboard.setText("\t0\t1\n0\t0\t10\n2\t20\t30")

    dialog.paste_from_clipboard()
    dialog.accept_dialog()
    x_points, y_points, z_matrix = dialog.get_matrix_data()

    assert x_points == [0.0, 1.0]
    assert y_points == [0.0, 2.0]
    assert z_matrix == [[0.0, 10.0], [20.0, 30.0]]
    dialog.close()


def test_lookup_matrix_linear_dialog_supports_copy_paste_and_delete_shortcuts() -> None:
    _get_app()
    dialog = LookupMatrixLinearDialog(block_label="Lookup matrix (linear)")
    dialog.show()
    dialog.activateWindow()
    dialog.raise_()
    QTest.qWaitForWindowExposed(dialog)
    QtWidgets.QApplication.processEvents()
    clipboard = QtWidgets.QApplication.clipboard()
    clipboard.clear()
    QtWidgets.QApplication.processEvents()
    QTest.qWait(50)

    dialog._table_widget.clearSelection()
    selection = QtWidgets.QTableWidgetSelectionRange(0, 0, 2, 2)
    dialog._table_widget.setRangeSelected(selection, True)
    dialog._table_widget.setFocus()
    QtWidgets.QApplication.processEvents()

    _copy_selected_table_range_to_clipboard(dialog._table_widget)
    QtWidgets.QApplication.processEvents()
    QTest.qWait(50)
    copied_grid = _parse_clipboard_grid(clipboard.text())
    assert copied_grid == [["", "0.0", "1.0"], ["0.0", "0.0", "10.0"], ["2.0", "20.0", "30.0"]] or copied_grid == [["", "0", "1"], ["0", "0", "10"], ["2", "20", "30"]]

    clipboard.setText("\t5\t6\n7\t8\t9\n10\t11\t12\n13\t14\t15")
    dialog._table_widget.clearSelection()
    dialog._table_widget.setFocus()
    QtWidgets.QApplication.processEvents()

    dialog.paste_from_clipboard()
    QtWidgets.QApplication.processEvents()
    QTest.qWait(50)
    x_points, y_points, z_matrix = dialog._read_matrix_from_table()
    assert x_points == [5.0, 6.0]
    assert y_points == [7.0, 10.0, 13.0]
    assert z_matrix == [[8.0, 9.0], [11.0, 12.0], [14.0, 15.0]]

    dialog._table_widget.clearSelection()
    selection = QtWidgets.QTableWidgetSelectionRange(1, 0, 1, 2)
    dialog._table_widget.setRangeSelected(selection, True)
    dialog._table_widget.setFocus()
    QtWidgets.QApplication.processEvents()

    dialog.delete_selection()
    QtWidgets.QApplication.processEvents()
    QTest.qWait(50)
    x_points, y_points, z_matrix = dialog._read_matrix_from_table()
    assert x_points == [5.0, 6.0]
    assert y_points == [10.0, 13.0]
    assert z_matrix == [[11.0, 12.0], [14.0, 15.0]]
    dialog.close()


def test_lookup_matrix_linear_dialog_axis_click_selects_full_column_or_row() -> None:
    _get_app()
    dialog = LookupMatrixLinearDialog(block_label="Lookup matrix (linear)")

    dialog.on_matrix_cell_pressed(0, 1)
    QtWidgets.QApplication.processEvents()
    selected_indexes = dialog._table_widget.selectionModel().selectedIndexes()
    assert len(selected_indexes) == dialog._table_widget.rowCount()
    assert all(index.column() == 1 for index in selected_indexes)

    dialog.on_matrix_cell_pressed(1, 0)
    QtWidgets.QApplication.processEvents()
    selected_indexes = dialog._table_widget.selectionModel().selectedIndexes()
    assert len(selected_indexes) == dialog._table_widget.columnCount()
    assert all(index.row() == 1 for index in selected_indexes)
    dialog.close()


def test_lookup_matrix_linear_dialog_supports_row_copy_and_row_paste() -> None:
    _get_app()
    dialog = LookupMatrixLinearDialog(block_label="Lookup matrix (linear)")
    dialog.show()
    dialog.activateWindow()
    dialog.raise_()
    QTest.qWaitForWindowExposed(dialog)
    QtWidgets.QApplication.processEvents()

    clipboard = QtWidgets.QApplication.clipboard()
    clipboard.clear()
    QtWidgets.QApplication.processEvents()
    QTest.qWait(50)

    dialog.on_matrix_cell_pressed(1, 0)
    QtWidgets.QApplication.processEvents()

    dialog.setFocus()
    dialog._table_widget.setFocus()
    QtWidgets.QApplication.processEvents()

    print(f"DEBUG: selected indexes = {dialog._table_widget.selectionModel().selectedIndexes()}")
    print(f"DEBUG: row 1 items = {[dialog._table_widget.item(1, c).text() for c in range(3)]}")
    print(f"DEBUG: clipboard before copy = {repr(clipboard.text())}")

    from VeraGrid.Gui.DynamicModelEditor.ElementDialogues.lookup_table_dialog import _copy_selected_table_range_to_clipboard
    _copy_selected_table_range_to_clipboard(dialog._table_widget)
    QtWidgets.QApplication.processEvents()
    QTest.qWait(100)

    clipboard_content = clipboard.text()
    print(f"DEBUG: clipboard after copy = {repr(clipboard_content)}")

    assert clipboard_content.rstrip() == "0.0\t0.0\t10.0", f"Expected '0.0\\t0.0\\t10.0' but got {repr(clipboard_content)}"

    dialog.on_matrix_cell_pressed(2, 0)
    QtWidgets.QApplication.processEvents()
    dialog.setFocus()
    dialog._table_widget.setFocus()
    QtWidgets.QApplication.processEvents()

    dialog.paste_from_clipboard()
    QtWidgets.QApplication.processEvents()
    QTest.qWait(100)
    x_points, y_points, z_matrix = dialog._read_matrix_from_table()
    assert x_points == [0.0, 1.0]
    assert y_points == [0.0, 0.0]
    assert z_matrix == [[0.0, 10.0], [0.0, 10.0]]
    dialog.close()


def test_lookup_matrix_linear_descriptor_uses_modal_matrix_to_build_block(override_attrs) -> None:
    editor = _build_editor(DynamicSimulationMode.EMT)
    descriptor = get_basic_block_catalog_descriptor_by_key()["lookup_matrix_linear"]

    class _MatrixDialogStub:
        def __init__(self, block_label: str, initial_x_points=None, initial_y_points=None, initial_z_matrix=None, parent=None) -> None:
            _unused = (block_label, initial_x_points, initial_y_points, initial_z_matrix, parent)

        def exec(self) -> int:
            return int(QtWidgets.QDialog.DialogCode.Accepted)

        def get_matrix_data(self) -> tuple[list[float], list[float], list[list[float]]]:
            return [0.0, 1.0], [0.0, 2.0], [[0.0, 10.0], [20.0, 30.0]]

    override_attrs.setattr(dynamic_block_editor_module, "LookupMatrixLinearDialog", _MatrixDialogStub)
    block_item = editor.create_library_payload_item(descriptor, 10.0, 20.0)

    assert block_item is not None
    assert any(var.name.startswith("arr_x2_") for var in block_item.subsys.event_dict.keys())
    assert any(var.name.startswith("arr_y2_") for var in block_item.subsys.event_dict.keys())
    assert any(var.name.startswith("arr_z2_2_") for var in block_item.subsys.event_dict.keys())

    editor.has_unapplied_changes = False
    editor.close()


def test_inverse_lookup_array_linear_descriptor_uses_modal_points_to_build_block(override_attrs) -> None:
    editor = _build_editor(DynamicSimulationMode.EMT)
    descriptor = get_basic_block_catalog_descriptor_by_key()["inverse_lookup_array_linear"]

    class _DialogStub:
        def __init__(self, block_label: str, initial_points=None, parent=None) -> None:
            _unused = (block_label, initial_points, parent)

        def exec(self) -> int:
            return int(QtWidgets.QDialog.DialogCode.Accepted)

        def get_points(self) -> tuple[list[float], list[float]]:
            return [0.0, 1.0, 2.0], [0.0, 10.0, 20.0]

    override_attrs.setattr(dynamic_block_editor_module, "LookupArrayLinearDialog", _DialogStub)
    block_item = editor.create_library_payload_item(descriptor, 10.0, 20.0)

    assert block_item is not None
    assert any(var.name.startswith("arr_x3_") for var in block_item.subsys.event_dict.keys())
    assert any(var.name.startswith("arr_y3_") for var in block_item.subsys.event_dict.keys())

    editor.has_unapplied_changes = False
    editor.close()


def test_lookup_array_spline_descriptor_uses_modal_points_to_build_block(override_attrs) -> None:
    editor = _build_editor(DynamicSimulationMode.EMT)
    descriptor = get_basic_block_catalog_descriptor_by_key()["lookup_array_spline"]

    class _DialogStub:
        def __init__(self, block_label: str, initial_points=None, parent=None) -> None:
            _unused = (block_label, initial_points, parent)

        def exec(self) -> int:
            return int(QtWidgets.QDialog.DialogCode.Accepted)

        def get_points(self) -> tuple[list[float], list[float]]:
            return [0.0, 1.0, 2.0], [0.0, 10.0, 20.0]

    override_attrs.setattr(dynamic_block_editor_module, "LookupArrayLinearDialog", _DialogStub)
    block_item = editor.create_library_payload_item(descriptor, 10.0, 20.0)

    assert block_item is not None
    assert any(var.name.startswith("arr_x3_") for var in block_item.subsys.event_dict.keys())
    assert any(var.name.startswith("arr_y3_") for var in block_item.subsys.event_dict.keys())

    editor.has_unapplied_changes = False
    editor.close()


def test_lookup_matrix_spline_descriptor_uses_modal_matrix_to_build_block(override_attrs) -> None:
    editor = _build_editor(DynamicSimulationMode.EMT)
    descriptor = get_basic_block_catalog_descriptor_by_key()["lookup_matrix_spline"]

    class _MatrixDialogStub:
        def __init__(self, block_label: str, initial_x_points=None, initial_y_points=None, initial_z_matrix=None, parent=None) -> None:
            _unused = (block_label, initial_x_points, initial_y_points, initial_z_matrix, parent)

        def exec(self) -> int:
            return int(QtWidgets.QDialog.DialogCode.Accepted)

        def get_matrix_data(self) -> tuple[list[float], list[float], list[list[float]]]:
            return [0.0, 1.0], [0.0, 2.0], [[0.0, 10.0], [20.0, 30.0]]

    override_attrs.setattr(dynamic_block_editor_module, "LookupMatrixLinearDialog", _MatrixDialogStub)
    block_item = editor.create_library_payload_item(descriptor, 10.0, 20.0)

    assert block_item is not None
    assert any(var.name.startswith("arr_z2_2_") for var in block_item.subsys.event_dict.keys())

    editor.has_unapplied_changes = False
    editor.close()
