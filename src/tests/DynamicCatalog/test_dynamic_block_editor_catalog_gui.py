from __future__ import annotations

import gc
import math
import sys

import numpy as np
import pytest
from PySide6 import QtCore, QtWidgets
from PySide6.QtTest import QTest

import VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor as dynamic_block_editor_module
import VeraGrid.Gui.DynamicModelEditor.dynamic_editor_graphics as graph
import VeraGridEngine.api as gce
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import DynamicBlockEditorGUI
from VeraGrid.Gui.DynamicModelEditor.dynamic_block_properties import DynamicBlockPropertiesDialog
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
        current_block=Block(),
        api_object=resolved_api_object,
        current_theme="Light",
        mode=mode,
        templates_list=list(),
        circuit=circuit,
        is_root_editor=False,
        modal=False,
    )
    editor.show()
    editor.activateWindow()
    return editor


def _build_catalog_block_item(editor: DynamicBlockEditorGUI,
                              template_key: str) -> graph.GenericBlockItem:
    """
    Materialize one catalog block on the editor canvas.

    :param editor: Dynamic editor receiving the catalogue block.
    :param template_key: Stable Basic Block Catalog template key.
    :return: Materialized generic template item.
    """

    descriptor: BasicBlockTemplateDescriptor = get_basic_block_catalog_descriptor_by_key()[template_key]
    block_item: object = editor.create_library_payload_item(descriptor, 10.0, 20.0)
    assert isinstance(block_item, graph.GenericBlockItem)
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
    assert _count_descriptor_leaves(editor, native_item) == 542

    editor.close()


def test_rms_editor_exposes_basic_block_catalog_under_basic() -> None:
    editor = _build_editor(DynamicSimulationMode.RMS)
    source_model = editor.library.library_model
    basic_item = source_model.invisibleRootItem().child(0)
    native_item = basic_item.child(0)

    assert basic_item.text() == "Basic"
    assert basic_item.rowCount() == 1
    assert native_item.text() == "Native"
    assert _count_descriptor_leaves(editor, native_item) == 542

    editor.close()


# def test_library_search_button_and_shortcut_filter_basic_catalog() -> None:
#     _collect_pending_resources()
#     editor = _build_editor(DynamicSimulationMode.EMT)
#     editor.raise_()
#     QTest.qWaitForWindowExposed(editor)
#     QtWidgets.QApplication.processEvents()
#     descriptor_by_key = get_basic_block_catalog_descriptor_by_key()
#     park_label = descriptor_by_key["park_transform_dq"].display_label
#     limit_label = descriptor_by_key["limit"].display_label
#
#     assert editor.ui.librarySearchLineEdit.isVisible()
#     editor.ui.librarySearchLineEdit.clearFocus()
#     QTest.keyClick(editor, QtCore.Qt.Key.Key_F, QtCore.Qt.KeyboardModifier.ControlModifier)
#     QtWidgets.QApplication.processEvents()
#     QTest.qWait(100)
#
#     assert editor.ui.librarySearchLineEdit.hasFocus()
#
#     editor.ui.librarySearchLineEdit.clearFocus()
#     editor.focus_library_search()
#     QtWidgets.QApplication.processEvents()
#     QTest.qWait(100)
#     assert editor.ui.librarySearchLineEdit.hasFocus()
#
#     editor.ui.librarySearchLineEdit.setText("park transform")
#     QtWidgets.QApplication.processEvents()
#
#     visible_leaf_labels = _collect_leaf_labels(editor.library_proxy_model)
#     assert park_label in visible_leaf_labels
#     assert limit_label not in visible_leaf_labels
#
#
#     editor.close()
#     editor.deleteLater()
#     QtWidgets.QApplication.processEvents()
#     QTest.qWait(50)
#     QtWidgets.QApplication.processEvents()


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


def test_side_panel_contains_only_library_while_modal_loads_block_parameters() -> None:
    """The editor owns only Library while Block properties owns parameter editing."""
    editor: DynamicBlockEditorGUI = _build_editor(DynamicSimulationMode.EMT)
    block_item: graph.GenericBlockItem = _build_catalog_block_item(editor, "pulse")
    assert block_item.subsys is not None

    editor.ui.toolBox.setCurrentWidget(editor.ui.page_7)
    editor.scene.clearSelection()
    block_item.setSelected(True)
    QtWidgets.QApplication.processEvents()

    assert editor.ui.toolBox.count() == 1
    assert editor.ui.toolBox.currentWidget() is editor.ui.page_7

    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block=block_item.subsys,
        block_type_name=graph.EditorGraphicsCommonFeatures.TEMPLATE_NODE_TYPE,
        var_factory=editor.var_factory,
    )
    assert dialogue._parameter_model.rowCount() > 0
    dialogue.close()

    editor.has_unapplied_changes = False
    editor.close()


def test_modal_parameter_edit_preserves_non_structural_block_identity() -> None:
    """Editing a catalogue constant must not reconstruct the symbolic block."""
    editor: DynamicBlockEditorGUI = _build_editor(DynamicSimulationMode.EMT)
    block_item: graph.GenericBlockItem = _build_catalog_block_item(editor, "pulse")
    assert block_item.subsys is not None
    target_block: Block = block_item.subsys
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block=target_block,
        block_type_name=graph.EditorGraphicsCommonFeatures.TEMPLATE_NODE_TYPE,
        var_factory=editor.var_factory,
    )
    dialogue.blockApplied.connect(editor.on_block_properties_applied)
    assert dialogue._parameter_model.rowCount() > 0
    value_index: QtCore.QModelIndex = dialogue._parameter_model.index(0, 2)
    assert dialogue._parameter_model.data(value_index) == "None"
    changed_value: float = 1.0

    assert dialogue._parameter_model.setData(
        value_index,
        changed_value,
        QtCore.Qt.ItemDataRole.EditRole,
    )
    dialogue.apply_changes()

    assert editor.get_block_from_main_block(target_block.uid) is target_block
    assert float(str(dialogue._parameter_model.data(value_index))) == changed_value
    dialogue.close()

    editor.has_unapplied_changes = False
    editor.close()


def test_parameter_modal_separates_runtime_modes_for_pulse_block() -> None:
    """General options keeps events while Runtime logic owns retained modes."""
    editor: DynamicBlockEditorGUI = _build_editor(DynamicSimulationMode.EMT)
    block_item: graph.GenericBlockItem = _build_catalog_block_item(editor, "pulse")
    assert block_item.subsys is not None
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block=block_item.subsys,
        block_type_name=graph.EditorGraphicsCommonFeatures.TEMPLATE_NODE_TYPE,
        var_factory=editor.var_factory,
    )

    row_types: list[str] = list()
    row_index: int
    for row_index in range(dialogue._parameter_model.rowCount()):
        index: QtCore.QModelIndex = dialogue._parameter_model.index(row_index, 0)
        row_types.append(str(dialogue._parameter_model.data(index, QtCore.Qt.ItemDataRole.DisplayRole)))

    assert any(row_type.startswith("Dynamic parameter") for row_type in row_types)
    assert not any(row_type.startswith("Mode parameter") for row_type in row_types)
    assert dialogue._runtime_logic_editor._mode_model.rowCount() > 0
    assert dialogue._tabs.tabText(2) == "Runtime logic"
    dialogue.close()

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

#
def test_ground_emt_block_is_available_from_library() -> None:
    editor = _build_editor(DynamicSimulationMode.EMT)
    block_item = editor.create_library_payload_item(BlockType.GROUND_EMT, 10.0, 20.0)

    assert block_item is not None
    assert len(block_item.inputs) == 1
    assert len(block_item.outputs) == 1

    editor.has_unapplied_changes = False
    editor.close()


