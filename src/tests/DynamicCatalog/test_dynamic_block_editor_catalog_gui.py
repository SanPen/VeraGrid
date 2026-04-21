from __future__ import annotations

import sys

import pytest
from PySide6 import QtCore, QtWidgets
from PySide6.QtTest import QTest

from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import DynamicBlockEditorGUI
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.BasicBlockCatalog import BasicBlockTemplateDescriptor
from VeraGridEngine.Templates.BasicBlockCatalog import get_basic_block_catalog_descriptor_by_key
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import DynamicSimulationMode

pytestmark = pytest.mark.filterwarnings("error")


class _ApiStub:
    """
    Minimal API object accepted by the dynamic block editor tests.
    """

    __slots__ = ("name", "rms_template", "emt_template")

    def __init__(self) -> None:
        self.name = "Stub"
        self.rms_template = None
        self.emt_template = None


def _get_app() -> QtWidgets.QApplication:
    """
    Get or create the Qt application used by GUI tests.
    """

    app: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if app is None:
        return QtWidgets.QApplication(sys.argv)
    else:
        return app


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


def _build_editor(mode: DynamicSimulationMode = DynamicSimulationMode.EMT) -> DynamicBlockEditorGUI:
    """
    Build one dynamic block editor instance for GUI tests.
    """

    _get_app()
    editor = DynamicBlockEditorGUI(
        var_factory=VarFactory(),
        block=Block(),
        api_object=_ApiStub(),
        mode=mode,
        templates_list=list(),
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


def test_emt_editor_exposes_basic_block_catalog_under_basic() -> None:
    editor = _build_editor(DynamicSimulationMode.EMT)
    source_model = editor.library_model
    basic_item = source_model.invisibleRootItem().child(0)
    native_item = basic_item.child(0)

    assert basic_item.text() == "Basic"
    assert basic_item.rowCount() == 1
    assert native_item.text() == "Native"
    assert native_item.child(0).text() == "Arithmetic"
    assert _find_index_by_label(editor.library_model, "Scaling and Products").isValid()
    assert not _find_index_by_label(editor.library_model, "Arithmetic and Products").isValid()
    assert _count_descriptor_leaves(editor, native_item) == 533

    editor.close()


def test_rms_editor_exposes_basic_block_catalog_under_basic() -> None:
    editor = _build_editor(DynamicSimulationMode.RMS)
    source_model = editor.library_model
    basic_item = source_model.invisibleRootItem().child(0)
    native_item = basic_item.child(0)

    assert basic_item.text() == "Basic"
    assert basic_item.rowCount() == 1
    assert native_item.text() == "Native"
    assert _count_descriptor_leaves(editor, native_item) == 533

    editor.close()


def test_library_search_button_and_shortcut_filter_basic_catalog() -> None:
    editor = _build_editor(DynamicSimulationMode.EMT)
    descriptor_by_key = get_basic_block_catalog_descriptor_by_key()
    park_label = descriptor_by_key["park_transform_dq"].display_label
    limit_label = descriptor_by_key["limit"].display_label

    assert editor.ui.librarySearchLineEdit.isVisible()

    QTest.mouseClick(editor.ui.librarySearchButton, QtCore.Qt.MouseButton.LeftButton)
    QtWidgets.QApplication.processEvents()
    assert editor.ui.librarySearchLineEdit.hasFocus()

    editor.ui.librarySearchLineEdit.clearFocus()
    QTest.keyClick(editor, QtCore.Qt.Key.Key_F, QtCore.Qt.KeyboardModifier.ControlModifier)
    QtWidgets.QApplication.processEvents()
    assert editor.ui.librarySearchLineEdit.hasFocus()

    editor.ui.librarySearchLineEdit.setText("park transform")
    QtWidgets.QApplication.processEvents()

    visible_leaf_labels = _collect_leaf_labels(editor.library_proxy_model)
    assert park_label in visible_leaf_labels
    assert limit_label not in visible_leaf_labels

    editor.close()


def test_proxy_drag_payload_materializes_catalog_template() -> None:
    editor = _build_editor(DynamicSimulationMode.EMT)
    park_descriptor = get_basic_block_catalog_descriptor_by_key()["park_transform_dq"]
    park_label = park_descriptor.display_label
    source_index = _find_index_by_label(editor.library_model, park_label)

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
