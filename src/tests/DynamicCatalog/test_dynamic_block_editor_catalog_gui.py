from __future__ import annotations

import gc
import sys

import pytest
from PySide6 import QtCore, QtGui, QtWidgets

import VeraGrid.Gui.DynamicModelEditor.Editor.dynamic_block_editor as dynamic_block_editor_module
import VeraGrid.Gui.DynamicModelEditor.Editor.dynamic_editor_graphics as graph
import VeraGridEngine.api as gce
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGrid.Gui.DynamicModelEditor.Editor.dynamic_block_editor import DynamicBlockEditorGUI
from VeraGrid.Gui.DynamicModelEditor.Editor.BlockProperties import DynamicBlockPropertiesDialog
from VeraGrid.Gui.DynamicModelEditor.Editor.DynamicLibrary.dynamic_editor_library import DynamicEditorLibrary
from VeraGridEngine.Devices.Diagrams.block_diagram import BlockDiagramNode
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.BasicBlockCatalog import BasicBlockTemplateDescriptor
from VeraGridEngine.Templates.BasicBlockCatalog import get_basic_block_catalog_descriptor_by_key
from VeraGridEngine.Templates.ProceduralLogicCatalog import (
    ProceduralBlockTemplateDescriptor,
    get_procedural_block_template_descriptors,
)
from VeraGridEngine.Templates.InternationalStandardsCatalog import (
    InternationalStandardTemplateDescriptor,
    get_international_standard_template_descriptors,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import BlockType
from VeraGridEngine.enumerations import DynamicSimulationMode
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.enumerations import VarPowerFlowReferenceType

pytestmark = pytest.mark.filterwarnings("error")


class _ApiStub:
    """
    Minimal API object accepted by the dynamic block editor tests.
    """

    __slots__ = ("name", "rms_template", "emt_template", "device_type")

    def __init__(self, device_type: DeviceType = DeviceType.NoDevice) -> None:
        """Create a minimal device context for one library mode.

        :param device_type: Device family whose specific leaves are exposed.
        :return: None.
        """
        self.name = "Stub"
        self.rms_template = None
        self.emt_template = None
        self.device_type = device_type


class _AcceptedMeasurementsDialog:
    """
    Deterministic measurement dialog replacement for edit-path tests.
    """

    __slots__ = ("_bus",)

    def __init__(
            self,
            buses: list[gce.Bus],
            measurement_vars_dict: dict[str, dict[BlockType, list[VarPowerFlowReferenceType]]],
            initial_bus: gce.Bus | None = None,
            initial_block_type: BlockType | None = None,
            initial_input_references: list[VarPowerFlowReferenceType] | None = None,
            initial_output_references: list[VarPowerFlowReferenceType] | None = None,
            parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """Store the bus that the editor supplies to the modal constructor.

        :param buses: Available bus list.
        :param measurement_vars_dict: Measurement references by bus domain.
        :param initial_bus: Initially selected bus.
        :param initial_block_type: Initially selected measurement type.
        :param initial_input_references: Initial input references.
        :param initial_output_references: Initial output references.
        :param parent: Optional parent widget.
        :return: None.
        """
        assert len(measurement_vars_dict) > 0
        assert initial_block_type is not None
        assert initial_input_references is not None
        assert initial_output_references is not None
        assert parent is not None
        if initial_bus is not None:
            self._bus: gce.Bus = initial_bus
        else:
            self._bus = buses[0]

    def exec(self) -> QtWidgets.QDialog.DialogCode:
        """Return an accepted modal result.

        :return: Accepted dialog code.
        """
        return QtWidgets.QDialog.DialogCode.Accepted

    def get_user_info(
            self,
    ) -> tuple[gce.Bus, BlockType, list[VarPowerFlowReferenceType], list[VarPowerFlowReferenceType]]:
        """Return one deterministic edited measurement configuration.

        :return: Bus, block type, input references, and output references.
        """
        return (
            self._bus,
            BlockType.MEASUREMENTS_VOLTAGE_ANGLE,
            list((VarPowerFlowReferenceType.Vm,)),
            list((VarPowerFlowReferenceType.Va,)),
        )


def _get_app() -> QtWidgets.QApplication:
    """
    Get or create the Qt application used by GUI tests.
    """

    app: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if app is None:
        return QtWidgets.QApplication(sys.argv)
    else:
        return app


def _select_catalog_test_color() -> QtGui.QColor:
    """Return the deterministic colour selected by colour-menu tests.

    :return: Test colour.
    """
    return QtGui.QColor("#117733")


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


def _assert_index_has_icon(index: QtCore.QModelIndex) -> None:
    """
    Assert that a model index exposes a non-empty decoration icon.

    :param index: Index expected to hold an icon.
    :return: None.
    """
    icon_data: object = index.data(QtCore.Qt.ItemDataRole.DecorationRole)
    assert isinstance(icon_data, QtGui.QIcon)
    assert not icon_data.isNull()


def test_emt_editor_exposes_basic_block_catalog_under_basic() -> None:
    editor = _build_editor(DynamicSimulationMode.EMT)
    source_model = editor.library.library_model
    basic_item = source_model.invisibleRootItem().child(0)
    native_item = basic_item.child(0)
    const_index: QtCore.QModelIndex = _find_index_by_label(source_model, "Const")
    moving_average_descriptor: BasicBlockTemplateDescriptor = get_basic_block_catalog_descriptor_by_key()["movingavg"]
    moving_average_index: QtCore.QModelIndex = _find_index_by_label(
        source_model,
        moving_average_descriptor.display_label,
    )

    assert source_model.columnCount() == 2
    assert source_model.headerData(0, QtCore.Qt.Orientation.Horizontal) == "Name"
    assert source_model.headerData(1, QtCore.Qt.Orientation.Horizontal) == "Description"
    assert basic_item.text() == "Basic"
    assert basic_item.rowCount() == 1
    assert native_item.text() == "Native"
    assert native_item.child(0).text() == "Arithmetic"
    assert _find_index_by_label(editor.library.library_model, "Scaling and Products").isValid()
    assert not _find_index_by_label(editor.library.library_model, "Arithmetic and Products").isValid()
    assert _count_descriptor_leaves(editor, native_item) == 542
    _assert_index_has_icon(source_model.index(0, 0))
    assert const_index.isValid()
    _assert_index_has_icon(const_index)
    assert (
        source_model.data(const_index.siblingAtColumn(1), QtCore.Qt.ItemDataRole.DisplayRole)
        == "Native mathematical block"
    )
    assert moving_average_index.isValid()
    _assert_index_has_icon(moving_average_index)
    assert "Inputs:" in str(
        source_model.data(moving_average_index.siblingAtColumn(1), QtCore.Qt.ItemDataRole.DisplayRole)
    )
    assert "Outputs:" in str(
        source_model.data(moving_average_index.siblingAtColumn(1), QtCore.Qt.ItemDataRole.DisplayRole)
    )

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
    descriptor = get_basic_block_catalog_descriptor_by_key()["movingavg"]
    descriptor_label = descriptor.display_label
    source_index = _find_index_by_label(editor.library.library_model, descriptor_label)

    assert source_index.isValid()

    proxy_index = editor.library_proxy_model.mapFromSource(source_index)
    assert proxy_index.isValid()

    mime_data = editor.library_proxy_model.mimeData([proxy_index])
    payload = editor.get_library_payload_from_mime_data(mime_data)

    assert payload is not None
    assert isinstance(payload, BasicBlockTemplateDescriptor)
    assert payload.template_key == "movingavg"

    children_before: int = len(editor.main_block.children)
    block_item = editor.create_library_payload_item(payload, 10.0, 20.0)

    assert block_item is not None
    assert len(editor.main_block.children) == children_before + 1
    assert block_item.subsys is editor.main_block.children[-1]
    assert block_item.subsys.name == "movingavg__77"

    editor.has_unapplied_changes = False
    editor.close()


@pytest.mark.parametrize("mode", (DynamicSimulationMode.RMS, DynamicSimulationMode.EMT))
def test_procedural_logic_branch_exposes_every_engine_descriptor(
        mode: DynamicSimulationMode,
) -> None:
    """RMS and EMT libraries must expose the same native procedural primitives.

    :param mode: Dynamic editor mode under inspection.
    :return: None.
    """
    editor: DynamicBlockEditorGUI = _build_editor(mode)
    procedural_root: QtCore.QModelIndex = _find_index_by_label(
        editor.library.library_model,
        "Procedural logic",
    )
    assert procedural_root.isValid()
    descriptor: ProceduralBlockTemplateDescriptor
    for descriptor in get_procedural_block_template_descriptors():
        source_index: QtCore.QModelIndex = _find_index_by_label(
            editor.library.library_model,
            descriptor.display_label,
            procedural_root,
        )
        assert source_index.isValid(), descriptor.display_label
        payload: object = source_index.data(editor.block_role)
        assert isinstance(payload, ProceduralBlockTemplateDescriptor)
        assert payload.logic_tpe == descriptor.logic_tpe

    editor.has_unapplied_changes = False
    editor.close()


def test_procedural_library_double_click_materializes_canvas_block() -> None:
    """A procedural leaf double-click must use the normal template creation path.

    :return: None.
    """
    editor: DynamicBlockEditorGUI = _build_editor(DynamicSimulationMode.EMT)
    descriptor: ProceduralBlockTemplateDescriptor = list(
        get_procedural_block_template_descriptors()
    )[0]
    procedural_root: QtCore.QModelIndex = _find_index_by_label(
        editor.library.library_model,
        "Procedural logic",
    )
    assert procedural_root.isValid()
    source_index: QtCore.QModelIndex = _find_index_by_label(
        editor.library.library_model,
        descriptor.display_label,
        procedural_root,
    )
    proxy_index: QtCore.QModelIndex = editor.library_proxy_model.mapFromSource(source_index)
    children_before: int = len(editor.main_block.children)

    editor.on_library_item_double_clicked(proxy_index)

    assert len(editor.main_block.children) == children_before + 1
    inserted_block: Block = editor.main_block.children[-1]
    assert len(inserted_block.procedural_logic) == 1
    assert inserted_block.procedural_logic[0].logic_tpe == descriptor.logic_tpe
    assert editor.diagram.node_data[inserted_block.uid].tpe == BlockType.PROCEDURAL_LOGIC.name

    editor.has_unapplied_changes = False
    editor.close()


def test_rms_library_exposes_every_international_standard_descriptor() -> None:
    """Expose every categorized international-standard leaf only in RMS mode.

    :return: None.
    """
    rms_editor: DynamicBlockEditorGUI = _build_editor(DynamicSimulationMode.RMS)
    standards_root: QtCore.QModelIndex = _find_index_by_label(
        rms_editor.library.library_model,
        "International standards",
    )
    assert standards_root.isValid()
    standards_proxy_root: QtCore.QModelIndex = rms_editor.library_proxy_model.mapFromSource(
        standards_root
    )
    assert rms_editor.ui.libraryTreeView.isExpanded(standards_proxy_root)

    category_row: int
    for category_row in range(rms_editor.library_proxy_model.rowCount(standards_proxy_root)):
        category_proxy_index: QtCore.QModelIndex = rms_editor.library_proxy_model.index(
            category_row,
            0,
            standards_proxy_root,
        )
        assert not rms_editor.ui.libraryTreeView.isExpanded(category_proxy_index)

    descriptor: InternationalStandardTemplateDescriptor
    for descriptor in get_international_standard_template_descriptors():
        source_index: QtCore.QModelIndex = _find_index_by_label(
            rms_editor.library.library_model,
            descriptor.display_label,
            standards_root,
        )
        assert source_index.isValid(), descriptor.display_label
        payload: object = source_index.data(rms_editor.block_role)
        assert isinstance(payload, InternationalStandardTemplateDescriptor)
        assert payload.model == descriptor.model

    rms_editor.has_unapplied_changes = False
    rms_editor.close()

    emt_editor: DynamicBlockEditorGUI = _build_editor(DynamicSimulationMode.EMT)
    emt_standards_root: QtCore.QModelIndex = _find_index_by_label(
        emt_editor.library.library_model,
        "International standards",
    )
    assert not emt_standards_root.isValid()
    emt_editor.has_unapplied_changes = False
    emt_editor.close()


def test_controls_removed_from_catalogue_remain_in_dynamic_library() -> None:
    """Keep native control-building blocks available in the RMS editor.

    :return: None.
    """
    application: QtWidgets.QApplication = _get_app()
    generator_library: DynamicEditorLibrary = DynamicEditorLibrary(
        api_object=_ApiStub(device_type=DeviceType.GeneratorDevice),
        mode=DynamicSimulationMode.RMS,
        templates_list=list(),
    )
    generator_labels: set[str] = set(_collect_leaf_labels(generator_library.library_model))
    expected_generator_controls: set[str] = set((
        "Pll transformer",
        "Pi current controller",
        "Pi power controller",
        "Governor",
        "Stabilizer",
        "Exciter",
    ))
    assert expected_generator_controls.issubset(generator_labels)

    vsc_library: DynamicEditorLibrary = DynamicEditorLibrary(
        api_object=_ApiStub(device_type=DeviceType.VscDevice),
        mode=DynamicSimulationMode.RMS,
        templates_list=list(),
    )
    vsc_labels: set[str] = set(_collect_leaf_labels(vsc_library.library_model))
    assert "Gfl converter" in vsc_labels
    application.processEvents()


def test_international_standard_library_payload_materializes_canvas_block() -> None:
    """Create an RMS canvas block from the typed international-standard payload.

    :return: None.
    """
    editor: DynamicBlockEditorGUI = _build_editor(DynamicSimulationMode.RMS)
    descriptor: InternationalStandardTemplateDescriptor = list(
        get_international_standard_template_descriptors()
    )[0]
    standards_root: QtCore.QModelIndex = _find_index_by_label(
        editor.library.library_model,
        "International standards",
    )
    source_index: QtCore.QModelIndex = _find_index_by_label(
        editor.library.library_model,
        descriptor.display_label,
        standards_root,
    )
    proxy_index: QtCore.QModelIndex = editor.library_proxy_model.mapFromSource(source_index)
    mime_data: QtCore.QMimeData = editor.library_proxy_model.mimeData(list((proxy_index,)))
    payload: object = editor.get_library_payload_from_mime_data(mime_data)
    children_before: int = len(editor.main_block.children)

    assert isinstance(payload, InternationalStandardTemplateDescriptor)
    block_item: object = editor.create_library_payload_item(payload, 10.0, 20.0)
    assert isinstance(block_item, graph.GenericBlockItem)
    assert len(editor.main_block.children) == children_before + 1
    assert block_item.subsys is editor.main_block.children[-1]

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


def test_canvas_request_opens_restructured_block_properties() -> None:
    """Open the Designer-backed editor through the canvas controller path.

    :return: None.
    """
    editor: DynamicBlockEditorGUI = _build_editor(DynamicSimulationMode.EMT)
    block_item: graph.GenericBlockItem = _build_catalog_block_item(editor, "pulse")
    assert block_item.subsys is not None

    # Double click and the ``Edit block`` context action both end at this
    # controller method, so exercise the shared path without synthesizing a
    # platform-dependent native mouse event.
    editor.request_open_block_properties(block_item.subsys)

    dialogue: DynamicBlockPropertiesDialog | None = editor._block_properties_dialogue
    assert dialogue is not None
    tab_titles: list[str] = list()
    tab_index: int
    for tab_index in range(dialogue.ui.tab_widget.count()):
        tab_titles.append(dialogue.ui.tab_widget.tabText(tab_index))
    assert tab_titles == list(("General options", "DAE model", "LaTeX rendering"))
    assert editor._block_properties_dialogue is dialogue

    editor.close_block_properties_dialogue()
    editor.has_unapplied_changes = False
    editor.close()


def test_custom_block_color_survives_canvas_rebuild() -> None:
    """Keep a custom block fill after the properties path rebuilds the scene.

    :return: None.
    """
    editor: DynamicBlockEditorGUI = _build_editor(DynamicSimulationMode.EMT)
    block_item: graph.GenericBlockItem = _build_catalog_block_item(editor, "pulse")
    assert block_item.subsys is not None
    block_uid: int = block_item.subsys.uid
    custom_color: str = "#bb2244"
    diagram_node: BlockDiagramNode | None = editor.get_diagram_node_for_block_uid(block_uid)
    assert diagram_node is not None

    diagram_node.color = custom_color
    editor.apply_diagram_node_color_to_block_item(block_item)
    assert block_item.brush().color().name() == custom_color

    editor.rebuild_scene_from_diagram()

    rebuilt_item: object = editor.get_scene_item_by_block_uid(block_uid)
    assert isinstance(rebuilt_item, graph.GenericBlockItem)
    assert rebuilt_item.brush().color().name() == custom_color

    editor.has_unapplied_changes = False
    editor.close()


def test_change_color_handles_arithmetic_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Apply the context-menu fill colour to compact arithmetic blocks.

    :param monkeypatch: Pytest monkeypatch fixture.
    :return: None.
    """
    editor: DynamicBlockEditorGUI = _build_editor(DynamicSimulationMode.EMT)
    block_item: graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem | None = (
        editor.create_basic_arithmetic_op_item(BlockType.SUM, 10.0, 20.0)
    )
    assert isinstance(block_item, graph.RoundBaseArithmeticOpItem)
    assert block_item.subsys is not None
    custom_color: str = "#117733"

    monkeypatch.setattr(graph.QColorDialog, "getColor", _select_catalog_test_color)

    editor.scene.change_item_fill_color(block_item)
    diagram_node: BlockDiagramNode | None = editor.get_diagram_node_for_block_uid(block_item.subsys.uid)
    assert diagram_node is not None
    assert block_item.brush().color().name() == custom_color
    assert diagram_node.color == custom_color

    editor.has_unapplied_changes = False
    editor.close()


def test_measurement_block_enforces_reference_io_constraints() -> None:
    """Force measurement references into their physical input/output side.

    :return: None.
    """
    circuit: MultiCircuit = MultiCircuit()
    bus: gce.Bus = gce.Bus(name="Bus 1", Vnom=10.0)
    circuit.add_bus(bus)
    editor: DynamicBlockEditorGUI = _build_editor(
        mode=DynamicSimulationMode.RMS,
        circuit=circuit,
    )
    p_var: Var = editor.var_factory.add_var("P", VarPowerFlowReferenceType.P, True)
    q_var: Var = editor.var_factory.add_var("Q", VarPowerFlowReferenceType.Q, True)
    editor.main_block.external_mapping.update(
        dict((
            (VarPowerFlowReferenceType.P, p_var),
            (VarPowerFlowReferenceType.Q, q_var),
        ))
    )

    block: Block = editor.create_measurements_block(
        bus=bus,
        block_type=BlockType.MEASUREMENTS_VOLTAGE_ANGLE,
        ref_inputs=list((VarPowerFlowReferenceType.Vm, VarPowerFlowReferenceType.Va)),
        ref_outputs=list((VarPowerFlowReferenceType.P, VarPowerFlowReferenceType.Q)),
    )

    input_references: list[VarPowerFlowReferenceType] = editor.get_measurements_dialog_refs_from_vars(block.in_vars)
    output_references: list[VarPowerFlowReferenceType] = editor.get_measurements_dialog_refs_from_vars(block.out_vars)
    assert input_references == list((VarPowerFlowReferenceType.P, VarPowerFlowReferenceType.Q))
    assert output_references == list((VarPowerFlowReferenceType.Vm, VarPowerFlowReferenceType.Va))

    editor.has_unapplied_changes = False
    editor.close()


def test_measurement_color_action_survives_measurement_edit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep a measurement item custom fill after its edit dialog rebuilds it.

    :param monkeypatch: Pytest monkeypatch fixture.
    :return: None.
    """
    circuit: MultiCircuit = MultiCircuit()
    bus: gce.Bus = gce.Bus(name="Bus 1", Vnom=10.0)
    circuit.add_bus(bus)
    editor: DynamicBlockEditorGUI = _build_editor(
        mode=DynamicSimulationMode.RMS,
        circuit=circuit,
    )
    measurement_item: graph.MeasurementsItem | None = editor.create_measurements_block_item(
        x_pos=10.0,
        y_pos=20.0,
        bus=bus,
        block_type=BlockType.MEASUREMENTS_VOLTAGE_ANGLE,
        ref_inputs=list(),
        ref_outputs=list((VarPowerFlowReferenceType.Vm, VarPowerFlowReferenceType.Va)),
    )
    assert isinstance(measurement_item, graph.MeasurementsItem)
    assert measurement_item.subsys is not None

    custom_color: str = "#117733"
    monkeypatch.setattr(graph.QColorDialog, "getColor", _select_catalog_test_color)
    editor.scene.change_item_fill_color(measurement_item)
    old_block_uid: int = measurement_item.subsys.uid
    old_diagram_node: BlockDiagramNode | None = editor.get_diagram_node_for_block_uid(old_block_uid)
    assert old_diagram_node is not None
    assert measurement_item.brush().color().name() == custom_color
    assert old_diagram_node.color == custom_color
    assert old_diagram_node.api_object_name == bus.idtag

    monkeypatch.setattr(
        dynamic_block_editor_module,
        "MeasurementsDialog",
        _AcceptedMeasurementsDialog,
    )
    editor.open_measurements_editor(
        source_item=measurement_item,
        x_pos=30.0,
        y_pos=40.0,
    )

    assert old_block_uid not in editor.diagram.node_data
    assert editor.get_scene_item_by_block_uid(old_block_uid) is None
    child_block: Block
    for child_block in editor.main_block.children:
        assert child_block.uid != old_block_uid

    measurement_items: list[graph.MeasurementsItem] = list()
    scene_item: object
    for scene_item in editor.scene.items():
        if isinstance(scene_item, graph.MeasurementsItem):
            measurement_items.append(scene_item)
        else:
            pass

    edited_item: graph.MeasurementsItem | None = None
    candidate_item: graph.MeasurementsItem
    for candidate_item in measurement_items:
        if candidate_item.scenePos() == QtCore.QPointF(30.0, 40.0):
            edited_item = candidate_item
        else:
            pass

    assert edited_item is not None
    assert edited_item.subsys is not None
    edited_diagram_node: BlockDiagramNode | None = editor.get_diagram_node_for_block_uid(
        edited_item.subsys.uid,
    )
    assert edited_diagram_node is not None
    assert edited_item.brush().color().name() == custom_color
    assert edited_diagram_node.color == custom_color
    assert edited_diagram_node.api_object_name == bus.idtag
    assert [var.ref for var in edited_item.subsys.in_vars] == list()
    assert [var.ref for var in edited_item.subsys.out_vars] == list((
        VarPowerFlowReferenceType.Vm,
        VarPowerFlowReferenceType.Va,
    ))

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
    """General options separates events from Python-authored retained modes.

    :return: None.
    """
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
    assert dialogue._retained_mode_model.rowCount() > 0
    python_source: str = dialogue._equation_buffers[0].get_code()
    assert "retained_modes = {" in python_source
    assert "procedural_logic = [" in python_source
    mode_row_index: int
    for mode_row_index in range(dialogue._retained_mode_model.rowCount()):
        mode_name_index: QtCore.QModelIndex = dialogue._retained_mode_model.index(
            mode_row_index,
            0,
        )
        mode_name: str = str(
            dialogue._retained_mode_model.data(
                mode_name_index,
                QtCore.Qt.ItemDataRole.DisplayRole,
            )
        )
        assert f"{mode_name}:" in python_source
    tab_titles: list[str] = list()
    tab_index: int
    for tab_index in range(dialogue.ui.tab_widget.count()):
        tab_titles.append(dialogue.ui.tab_widget.tabText(tab_index))
    assert "Runtime logic" not in tab_titles
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
