# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import math

import re
import copy
from typing import List, Dict, Optional, Any
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import (QGraphicsItem, QMenu, QDialog, QVBoxLayout, QDialogButtonBox, QLineEdit)
from PySide6.QtGui import (QPen, QBrush, QAction, QDropEvent, QDragEnterEvent, QDragMoveEvent, QColor)
from PySide6.QtCore import Qt, QPointF, Signal

from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Branches.overhead_line_type import OverheadLineType
from VeraGridEngine.Devices.Branches.sequence_line_type import SequenceLineType

from VeraGridEngine.Devices.Branches.underground_line_type import UndergroundLineType
from VeraGridEngine.Devices.Injections.controllable_shunt import ControllableShunt
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Injections.shunt import Shunt
from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType, ParamPowerFlowReferenceType, \
    DynamicSimulationMode, ShuntConnectionType, DynamicTableModelMode
from VeraGridEngine.Utils.Symbolic.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.bus_emt_template import get_bus_emt_template, \
    get_bus_emt_algebraic_vars
from VeraGridEngine.Utils.Symbolic.templates_common_functions import register_saved_emt_model_vars_for_device, \
    unify_saved_emt_model_root_contract, attach_emt_model_to_buses
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.fmu_template import FmuTemplate
from VeraGridEngine.Templates.BasicBlockCatalog.predefined_blocks import signal_pair
from VeraGridEngine.Templates.BasicBlockCatalog import BasicBlockTemplateDescriptor

from VeraGridEngine.Templates.BasicBlockCatalog import load_basic_block_catalog_template
from VeraGridEngine.Templates.BasicBlockCatalog.lookup_array_runtime_templates import \
    build_lookup_array_linear_runtime_template
from VeraGridEngine.Templates.BasicBlockCatalog.lookup_array_runtime_templates import \
    build_inverse_lookup_array_linear_runtime_template
from VeraGridEngine.Templates.BasicBlockCatalog.lookup_array_runtime_templates import \
    build_lookup_matrix_linear_runtime_template
from VeraGridEngine.Templates.BasicBlockCatalog.lookup_array_runtime_templates import \
    build_lookup_array_spline_runtime_template
from VeraGridEngine.Templates.BasicBlockCatalog.lookup_array_runtime_templates import \
    build_lookup_matrix_spline_runtime_template

import VeraGridEngine.Templates.Emt as emt_templates
import VeraGridEngine.Templates.BasicBlockCatalog as basic_block_templates
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Utils.Symbolic.block import Block, find_connections, find_connections_pf
from VeraGridEngine.Utils.Symbolic.equation_decomposer import EquationDecomposer
from VeraGrid.Gui.DynamicModelEditor.block_editor import Ui_BlockEditorWindow
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_dialogs import AddBlockVariableDialog, AddEquationDialog, \
    AddParameterDialog, EmtTemplateWizardDialog, ExpressionTextEditorDialog, GenericBlockDialog
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_graphics import BlockItem, BlockPositionChangedCallback, \
    BranchingItem, ConnectionItem, DiagramScene, GenericBlockItem, RoundBaseArithmeticOpItem, RectBaseArithmeticOpItem, \
    GraphicsView, PairedItem, PortItem, ProtectedConnectionBlockItem
from VeraGrid.Session.dynamic_editor_entries import DynamicEditorEntry
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_library import DynamicEditorLibrary, LibraryTreeFilterProxyModel
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_models import BlockParameterKind, BlockParameterRow, \
    BlockTableFilterProxyModel, EditParameterDialog, InspectModel, WrappableBlockTableModel, _build_block_uid_lookup, \
    _ensure_block_tree_names, add_variable_to_block, block_namespace_contains_name, \
    block_requires_editor_connection_bootstrap, build_block_symbol_namespace, clone_block_for_editing, copy_block_state, \
    initialize_connected_bus_models_for_editor_assignment, is_valid_symbol_name
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_validation import ValidationRow, ValidationSection, ValidationSectionDialog, \
    ValidationTraversalNode, add_validation_detail, add_validation_port_detail, add_validation_status_detail, \
    append_missing_port_messages_for_direction, append_port_vars_to_phase_count, append_vars_to_name_uid_map, \
    build_validation_row_highlight_metadata, build_validation_traversal_node, classify_emt_branch_phase_wire_from_refs, \
    classify_emt_injection_phase_wire_from_refs, collect_block_tree, collect_validation_traversal_list, \
    format_missing_port_detail, \
    format_validation_block_label, get_branch_phase_table_label, get_phase_table_label, \
    get_var_reference, has_ac_emt_branch_side_refs, has_ac_emt_phase_interface_refs
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_utilities import create_block_of_type, create_generic_block, \
    create_emt_wizard_block, get_blocktype2template_builder_dict
from VeraGrid.Gui.DynamicModelEditor.ElementDialogues.lookup_table_dialog import LookupArrayLinearDialog
from VeraGrid.Gui.DynamicModelEditor.ElementDialogues.lookup_table_dialog import LookupMatrixLinearDialog
from VeraGrid.Gui.DynamicModelEditor.ElementDialogues.jmarti_line_emt_dialog import JMartiLineEmtDialog
from VeraGrid.Gui.DynamicModelEditor.ElementDialogues.shunt_component_emt_dialog import ShuntComponentEmtDialog


from VeraGrid.Gui.messages import yes_no_question
from VeraGrid.Gui.toast_widget import ToastManager
from VeraGridEngine.Utils.Symbolic.symbolic import (symbolic_to_string, string_to_symbolic,
                                                    Const, Comparison)
from VeraGridEngine.Utils.Symbolic.symbolic_io import duplicate_block
from VeraGridEngine.Utils.Symbolic.bus_rms_template import get_bus_rms_algebraic_vars

from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_options import JMartiFitOptions
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_workflow import build_jmarti_fit_bundle_from_frequency_samples
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_workflow import build_jmarti_frequency_samples_from_line
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_workflow import load_jmarti_frequency_samples_from_npz
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_runtime import set_jmarti_block_fit_bundle
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_runtime import set_jmarti_block_runtime_data
from VeraGrid.Gui.DynamicModelEditor.dyn_template_editor_dialogue import DynTemplatesEditorDialog
from VeraGridEngine.enumerations import BlockType
from VeraGridEngine.Devices.Diagrams.block_diagram import BlockDiagram
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Expr, BinOp, UnOp
from dataclasses import dataclass


def _iter_child_blocks(block: Block) -> List[Block]:
    """
    Return all descendant blocks of one block.

    :param block: Root block.
    :return: Descendant blocks.
    """
    descendants: List[Block] = list()
    child_block: Block

    for child_block in block.children:
        descendants.append(child_block)
        descendants.extend(_iter_child_blocks(child_block))

    return descendants


def _get_shunt_component_kind(block_type: BlockType) -> str | None:
    """
    Return the single-component shunt kind handled by one block type.

    :param block_type: Candidate block type.
    :return: ``R``, ``L``, ``C`` or ``None``.
    """
    if block_type == BlockType.R_LOAD_EMT:
        return "R"
    elif block_type == BlockType.L_LOAD_EMT:
        return "L"
    elif block_type == BlockType.C_LOAD_EMT:
        return "C"
    else:
        return None


def _is_load_topology_block_type(block_type: BlockType) -> bool:
    """
    Return whether one block type uses the EMT load-topology modal.

    :param block_type: Candidate block type.
    :return: Boolean state.
    """
    return block_type in {BlockType.EXP_LOAD_EMT, BlockType.ZIP_LOAD_EMT}


@dataclass
class ConnectionVarSpec:
    """
    Specification of one connection variable exposed by the block editor.
    """

    direction: str
    reference: VarPowerFlowReferenceType
    visible_name: str


def build_rms_bus_input_specs(bus: Bus,
                              voltage_reference: VarPowerFlowReferenceType,
                              angle_reference: VarPowerFlowReferenceType,
                              dc_voltage_reference: VarPowerFlowReferenceType,
                              terminal_label: str = "") -> List[ConnectionVarSpec]:
    """
    Build the RMS voltage-interface specs for one connected bus.

    AC buses expose magnitude and angle because RMS phasor models need both
    quantities. DC buses only expose the DC voltage because no phasor angle
    exists in the DC domain.

    :param bus: Connected bus.
    :param voltage_reference: AC voltage-magnitude reference for this terminal.
    :param angle_reference: AC voltage-angle reference for this terminal.
    :param dc_voltage_reference: DC voltage reference for this terminal.
    :param terminal_label: Optional branch-side suffix such as ``f`` or ``t``.
    :return: RMS input connection specs for the bus domain.
    """
    safe_bus_name: str = re.sub(r"[^0-9A-Za-z_]+", "_", bus.name).strip("_") or "Bus"
    specs: List[ConnectionVarSpec] = list()

    if bus.is_dc:
        # DC terminals only contribute one voltage state to the RMS interface.
        specs.append(ConnectionVarSpec("input", dc_voltage_reference, f"Vdc_{safe_bus_name}"))
    else:
        # AC terminals expose phasor magnitude and angle to the device model.
        if terminal_label == "":
            voltage_name: str = f"Vm_{safe_bus_name}"
            angle_name: str = f"Va_{safe_bus_name}"
        else:
            voltage_name: str = f"Vm_{terminal_label}_{safe_bus_name}"
            angle_name: str = f"Va_{terminal_label}_{safe_bus_name}"

        specs.append(ConnectionVarSpec("input", voltage_reference, voltage_name))
        specs.append(ConnectionVarSpec("input", angle_reference, angle_name))

    return specs


def build_rms_bus_output_specs(bus: Bus,
                               active_power_reference: VarPowerFlowReferenceType,
                               reactive_power_reference: VarPowerFlowReferenceType,
                               terminal_label: str) -> List[ConnectionVarSpec]:
    """
    Build the RMS injected-power specs for one connected bus.

    AC terminals export active and reactive power because both are meaningful
    in the phasor network. DC terminals only export active/DC power because a
    DC connection has no reactive-power channel.

    :param bus: Connected bus.
    :param active_power_reference: Active-power reference for this terminal.
    :param reactive_power_reference: Reactive-power reference for this terminal.
    :param terminal_label: Stable terminal label such as ``f`` or ``t``.
    :return: RMS output connection specs for the bus domain.
    """
    safe_bus_name: str = re.sub(r"[^0-9A-Za-z_]+", "_", bus.name).strip("_") or "Bus"
    specs: List[ConnectionVarSpec] = list()

    if terminal_label == "":
        active_name: str = f"net_conn_P_{safe_bus_name}"
        reactive_name: str = f"net_conn_Q_{safe_bus_name}"
    else:
        active_name: str = f"net_conn_P{terminal_label}_{safe_bus_name}"
        reactive_name: str = f"net_conn_Q{terminal_label}_{safe_bus_name}"

    specs.append(ConnectionVarSpec("output", active_power_reference, active_name))

    if bus.is_dc:
        pass
    else:
        specs.append(ConnectionVarSpec("output", reactive_power_reference, reactive_name))

    return specs


def build_emt_injection_bus_mask_from_refs(refs: set[VarPowerFlowReferenceType]) -> list[bool]:
    """
    Build the AC bus phase mask implied by one injection editor interface.

    A phase is active when either its voltage input or its current output still
    exists in the saved root interface. This makes the user-edited interface
    the source of truth for the final EMT bus shell.

    :param refs: Power-flow references still exposed by the edited root block.
    :return: Phase mask ordered as ``[N, A, B, C]``.
    """
    mask: list[bool] = list([False, False, False, False])

    # Each phase can be kept either through its voltage input or through its
    # current output. This avoids requiring the user to keep both variables
    # just to declare that a phase exists.
    mask[0] = VarPowerFlowReferenceType.v_N in refs or VarPowerFlowReferenceType.i_N in refs
    mask[1] = VarPowerFlowReferenceType.v_A in refs or VarPowerFlowReferenceType.i_A in refs
    mask[2] = VarPowerFlowReferenceType.v_B in refs or VarPowerFlowReferenceType.i_B in refs
    mask[3] = VarPowerFlowReferenceType.v_C in refs or VarPowerFlowReferenceType.i_C in refs

    return mask


def build_emt_branch_bus_mask_from_refs(
        refs: set[VarPowerFlowReferenceType],
        side: str,
) -> list[bool]:
    """
    Build the AC bus phase mask implied by one branch-side editor interface.

    :param refs: Power-flow references still exposed by the edited root block.
    :param side: Branch side identifier. Expected values are ``from`` and ``to``.
    :return: Phase mask ordered as ``[N, A, B, C]``.
    """
    mask: list[bool] = list([False, False, False, False])

    # The branch interface has side-specific variables, so the mask must be
    # derived independently for the from and to terminals.
    if side == "from":
        mask[0] = VarPowerFlowReferenceType.vf_N in refs or VarPowerFlowReferenceType.if_N in refs
        mask[1] = VarPowerFlowReferenceType.vf_A in refs or VarPowerFlowReferenceType.if_A in refs
        mask[2] = VarPowerFlowReferenceType.vf_B in refs or VarPowerFlowReferenceType.if_B in refs
        mask[3] = VarPowerFlowReferenceType.vf_C in refs or VarPowerFlowReferenceType.if_C in refs
    elif side == "to":
        mask[0] = VarPowerFlowReferenceType.vt_N in refs or VarPowerFlowReferenceType.it_N in refs
        mask[1] = VarPowerFlowReferenceType.vt_A in refs or VarPowerFlowReferenceType.it_A in refs
        mask[2] = VarPowerFlowReferenceType.vt_B in refs or VarPowerFlowReferenceType.it_B in refs
        mask[3] = VarPowerFlowReferenceType.vt_C in refs or VarPowerFlowReferenceType.it_C in refs
    else:
        # Unsupported sides are handled as an empty mask. The caller decides
        # whether this is acceptable or whether the save operation must stop.
        pass

    return mask


class DynamicBlockEditorGUI(QtWidgets.QMainWindow):
    """
    DynamicModelEditorGUI
    """

    dirtyStateChanged = Signal(bool)
    BLOCK_BORDER: QColor = QColor("#202124")
    BLOCK_BORDER_SELECTED: QColor = QColor("#cc6f2c")
    BLOCK_TITLE: QColor = QColor("#173042")
    # Todo: to remove
    BLOCK_SHADOW: QColor = QColor(24, 42, 56, 45)
    PORT_BORDER: QColor = QColor("#173042")
    WIRE_COLOR: QColor = QColor("#202124")
    WIRE_HOVER_COLOR: QColor = QColor("#cc6f2c")
    HANDLE_FILL: QColor = QColor("#36536b")
    DEFAULT_BLOCK_FILL: QColor = QColor("#f5fdff")
    PAIRED_ITEM_FILL: QColor = QColor("#9fa8da")
    BLOCK_FILL_ALL_CONNECTED: QColor = QColor("#a5d6a7")
    BLOCK_FILL_DISCONNECTED: QColor = QColor("#ffe082")
    PORT_LABEL_COLOR: QColor = QColor("#173042")
    WIRE_ELBOW_OFFSET: float = 36.0
    PORT_LABEL_MAX_CHARS: int = 12
    BLOCK_HEADER_HEIGHT: float = 30.0
    BLOCK_PORT_ROW_HEIGHT: float = 20.0
    BLOCK_PORT_SECTION_PADDING: float = 10.0
    BLOCK_MIN_WIDTH: float = 160.0
    BLOCK_MIN_HEIGHT: float = 70.0
    BLOCK_COMPACT_MIN_WIDTH: float = 100.0
    BLOCK_COMPACT_MIN_HEIGHT: float = 40.0
    BLOCK_COMPACT_HEADER_HEIGHT: float = 20.0
    BLOCK_COMPACT_PORT_ROW_HEIGHT: float = 14.0
    BLOCK_COMPACT_PORT_SECTION_PADDING: float = 6.0
    TEMPLATE_NODE_TYPE: str = "TEMPLATE"
    PARAMETER_VALUE_TYPE_ROLE: int = int(QtCore.Qt.ItemDataRole.UserRole) + 500
    PARAMETER_EDITABLE_ROLE: int = int(QtCore.Qt.ItemDataRole.UserRole) + 501
    LIBRARY_SEARCH_TEXT_ROLE: int = int(QtCore.Qt.ItemDataRole.UserRole) + 502
    BLOCK_SEARCH_ROLE: int = int(QtCore.Qt.ItemDataRole.UserRole) + 503
    MODAL_TEMPLATE_KIND_ATTR: str = "_modal_template_kind"
    MODAL_TEMPLATE_CONFIG_ATTR: str = "_modal_template_config"
    LOOKUP_ARRAY_LINEAR_DESCRIPTOR_KEYS: set[str] = {
        "lookup_array_linear",
        "lookup_array_linear_noclipping",
        "lookup_array_object_linear",
        "lookup_array_object_linear_noclipping",
    }
    INVERSE_LOOKUP_ARRAY_LINEAR_DESCRIPTOR_KEYS: set[str] = {
        "inverse_lookup_array_linear",
        "inverse_lookup_array_object_linear",
    }
    LOOKUP_ARRAY_SPLINE_DESCRIPTOR_KEYS: set[str] = {
        "lookup_array_spline",
        "lookup_array_object_spline",
    }
    LOOKUP_MATRIX_LINEAR_DESCRIPTOR_KEYS: set[str] = {
        "lookup_matrix_linear",
        "lookup_matrix_object_linear",
    }
    LOOKUP_MATRIX_SPLINE_DESCRIPTOR_KEYS: set[str] = {
        "lookup_matrix_spline",
        "lookup_matrix_object_spline",
    }
    JMARTI_MODAL_OPTION_KEYS: tuple[str, ...] = (
        "reference_frequency_hz",
        "use_frequency_exploration_window",
        "exploration_low_hz",
        "exploration_high_hz",
        "use_delay_fit_window",
        "delay_fit_low_hz",
        "delay_fit_high_hz",
        "decoupling_warning_tolerance",
        "loewner_relative_tolerance",
        "maximum_model_order",
        "forced_model_order",
        "minimum_frequency_samples",
        "vf_max_iterations",
        "vf_pole_shift_tolerance",
        "vf_enforce_stable_poles",
        "vf_stability_real_part_floor",
        "vf_include_constant_term",
        "vf_include_proportional_term",
        "passivity_frequency_sample_count",
        "passivity_minimum_real_yc_tolerance",
        "passivity_maximum_hres_gain_tolerance",
    )

    def __init__(self,
                 var_factory: VarFactory,
                 block: Block,
                 api_object: ALL_DEV_TYPES,
                 circuit: MultiCircuit,
                 mode: DynamicSimulationMode = DynamicSimulationMode.RMS,
                 templates_list: Optional[List[RmsModelTemplate | EmtModelTemplate | FmuTemplate]] = None,
                 main_editor=False,
                 modal: bool = True,
                 workspace_embedded: bool = False):
        """
        Initializes a dynamic block editor window used for editing and managing blocks within a graphical model.

        This constructor sets up the user interface, initializes required attributes, creates a library model
        for draggable block items, and optionally constructs a tree structure based on the specified mode.
        It also configures drag-and-drop functionality for graphical items, connects various UI components
        to their associated event handlers, and reconstructs the scene from an existing diagram.

        :param var_factory: Factory object responsible for variable creation and management.
        :type var_factory: VarFactory
        :param block: The original block to be edited.
        :type block: Block
        :param api_object: Optional API object associated with the dynamic model.
        :type api_object: ALL_DEV_TYPES
        :param mode: Specifies the editor mode, either RMS or EMT.
        :type mode: DynamicSimulationMode
        :param templates_list: Optional block-template catalogue entries exposed to the editor.
        :type templates_list: Optional[List[RmsModelTemplate | EmtModelTemplate | FmuTemplate]]
        :param circuit: Circuit context that owns the edited dynamic device.
        :type circuit: MultiCircuit
        :param main_editor: Indicates whether this instance is the main editor for the block.
        :type main_editor: bool
        :param modal: Specifies whether the editor window should be modal.
        :type modal: bool
        :param workspace_embedded: Whether the editor is hosted inside the tabbed dynamic-editor workspace.
        :type workspace_embedded: bool
        :return: None.
        """
        super().__init__()

        self.ui = Ui_BlockEditorWindow()
        self.ui.setupUi(self)

        # The editor owns its own toast manager so save notifications are
        # stacked above this page instead of behind it on the main window.
        self.toast_manager: ToastManager = ToastManager(parent=self, position_top=False)

        if modal:
            self.setWindowModality(QtCore.Qt.WindowModality.WindowModal)

        self.ui.deviceLabel.setText(api_object.name if api_object is not None else "")

        self.block_role: int = int(QtCore.Qt.ItemDataRole.UserRole) + 300
        self.mime_type: str = "application/x-veragrid-dynamics-block"

        self.setWindowTitle(self.tr("Dynamic Model Editor"))

        self.ui.splitter.setStretchFactor(0, 6)
        self.ui.splitter.setStretchFactor(1, 10)

        self.var_factory = var_factory
        self.api_object = api_object
        self.original_block: Block = block  # api_object.rms_model

        self.circuit: MultiCircuit = circuit
        self.mode = mode
        self.main_editor = main_editor
        self.workspace_embedded = workspace_embedded
        self.templates_list: List[
            RmsModelTemplate | EmtModelTemplate | FmuTemplate] = templates_list if templates_list is not None else list()

        self._emt_bus_fallback_warning_shown: bool = False
        self._selected_side_block: Block | None = None
        self._validation_issue_overlay_active: bool = False
        self.setWindowTitle(self.tr("Dynamic Model Editor [{mode}]").format(mode=self.mode.name))
        self.block_counters: Dict[BlockType, int] = dict()
        self.scene: DiagramScene = DiagramScene(self)
        self.changes_applied: bool = False
        self.has_unapplied_changes: bool = False
        self.dynamic_editor_entry: DynamicEditorEntry | None = None
        self._prepared_to_delete: bool = False

        self.blocktype2templatebuilder = get_blocktype2template_builder_dict()

        self.devices_static_params_mapping: Dict[DeviceType, List[ParamPowerFlowReferenceType]] = (
            self.circuit.get_devices_static_params_mapping()
        )

        if not self.original_block.children and not self.original_block.empty() and self.main_editor:
            self.main_block = Block()
            block_to_append = clone_block_for_editing(block)
            self.main_block.children.append(block_to_append)
            self.main_block.in_vars = block_to_append.in_vars
            self.main_block.out_vars = block_to_append.out_vars
            self.main_block.external_mapping = block_to_append.external_mapping
        else:
            self.main_block: Block = clone_block_for_editing(block)

        self.diagram: BlockDiagram = self.main_block.diagram

        if self.workspace_embedded:
            self.menuBar().setVisible(False)
        else:
            pass

        # library
        self.library = DynamicEditorLibrary(self.api_object, self.mode, self.templates_list)
        self.library_proxy_model = LibraryTreeFilterProxyModel(
            search_role=self.LIBRARY_SEARCH_TEXT_ROLE,
            parent=self.ui.libraryTreeView,
        )
        self.library_proxy_model.setSourceModel(self.library.library_model)

        self.ui.libraryTreeView.setModel(self.library_proxy_model)
        self.ui.libraryTreeView.setDragEnabled(True)
        self.ui.libraryTreeView.setHeaderHidden(False)
        self.ui.libraryTreeView.setUniformRowHeights(True)

        self.ui.librarySearchLineEdit.setVisible(True)
        self.ui.librarySearchLineEdit.setClearButtonEnabled(True)
        self.ui.librarySearchLineEdit.textChanged.connect(self.on_library_search_text_changed)
        self.library_find_shortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Find, self)
        self.library_find_shortcut.activated.connect(self.focus_library_search)
        self.reset_library_tree_expansion()

        # Build variables table
        self.variables_model = WrappableBlockTableModel(
            var_factory=self.var_factory,
            parameter_value_type_role=self.PARAMETER_VALUE_TYPE_ROLE,
            parameter_editable_role=self.PARAMETER_EDITABLE_ROLE,
            block_search_role=self.BLOCK_SEARCH_ROLE,
            parent=self.ui.variablesTableView
        )
        self.variables_model.set_mode(DynamicTableModelMode.VARIABLES)
        self.variables_model.set_delegates()
        self.variables_search = QLineEdit()
        self.variables_search.setPlaceholderText(self.tr("Search variables..."))
        self.variables_search.setClearButtonEnabled(True)
        self.ui.verticalLayout_7.insertWidget(0, self.variables_search)
        self.variables_proxy = BlockTableFilterProxyModel(search_role=self.BLOCK_SEARCH_ROLE,
                                                          parent=self.ui.variablesTableView)
        self.variables_proxy.setSourceModel(self.variables_model)
        self.ui.variablesTableView.setModel(self.variables_proxy)
        self.variables_search.textChanged.connect(
            lambda text: self.variables_proxy.setFilterFixedString(text.strip())
        )
        variables_header: QtWidgets.QHeaderView = self.ui.variablesTableView.horizontalHeader()
        variables_header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        variables_header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        variables_header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.ui.variablesTableView.verticalHeader().setVisible(False)
        self.ui.variablesTableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.ui.variablesTableView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.ui.variablesTableView.doubleClicked.connect(self.on_variables_table_double_clicked)
        self.ui.variablesTableView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.variablesTableView.customContextMenuRequested.connect(self.show_variables_table_context_menu)

        # Build parameters table
        self.parameters_model = WrappableBlockTableModel(
            api_object=self.api_object,
            var_factory=self.var_factory,
            parameter_value_type_role=self.PARAMETER_VALUE_TYPE_ROLE,
            parameter_editable_role=self.PARAMETER_EDITABLE_ROLE,
            block_search_role=self.BLOCK_SEARCH_ROLE,
            parent=self.ui.parametersTableView
        )
        self.parameters_model.set_mode(DynamicTableModelMode.PARAMETERS)
        self.parameters_model.set_delegates()
        self.parameters_search = QLineEdit()
        self.parameters_search.setPlaceholderText(self.tr("Search parameters..."))
        self.parameters_search.setClearButtonEnabled(True)
        self.ui.verticalLayout_8.insertWidget(0, self.parameters_search)
        self.parameters_proxy = BlockTableFilterProxyModel(search_role=self.BLOCK_SEARCH_ROLE,
                                                           parent=self.ui.parametersTableView)
        self.parameters_proxy.setSourceModel(self.parameters_model)
        self.ui.parametersTableView.setModel(self.parameters_proxy)
        self.parameters_search.textChanged.connect(
            lambda text: self.parameters_proxy.setFilterFixedString(text.strip())
        )
        parameters_header: QtWidgets.QHeaderView = self.ui.parametersTableView.horizontalHeader()
        parameters_header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        parameters_header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        parameters_header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.ui.parametersTableView.verticalHeader().setVisible(False)
        self.ui.parametersTableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.ui.parametersTableView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.ui.parametersTableView.doubleClicked.connect(self.on_parameters_table_double_clicked)
        self.ui.parametersTableView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.parametersTableView.customContextMenuRequested.connect(self.show_parameters_table_context_menu)

        # Build equations table
        self.equations_model = WrappableBlockTableModel(
            var_factory=self.var_factory,
            parameter_value_type_role=self.PARAMETER_VALUE_TYPE_ROLE,
            parameter_editable_role=self.PARAMETER_EDITABLE_ROLE,
            block_search_role=self.BLOCK_SEARCH_ROLE,
            parent=self.ui.equationsTableView
        )
        self.equations_model.set_mode(DynamicTableModelMode.EQUATIONS)
        self.equations_model.set_delegates()
        self.equations_search = QLineEdit()
        self.equations_search.setPlaceholderText(self.tr("Search equations..."))
        self.equations_search.setClearButtonEnabled(True)
        self.ui.verticalLayout_9.insertWidget(0, self.equations_search)
        self.equations_proxy = BlockTableFilterProxyModel(search_role=self.BLOCK_SEARCH_ROLE,
                                                          parent=self.ui.equationsTableView)
        self.equations_proxy.setSourceModel(self.equations_model)
        self.ui.equationsTableView.setModel(self.equations_proxy)
        self.equations_search.textChanged.connect(
            lambda text: self.equations_proxy.setFilterFixedString(text.strip())
        )
        equations_header: QtWidgets.QHeaderView = self.ui.equationsTableView.horizontalHeader()
        equations_header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        equations_header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        equations_header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.ui.equationsTableView.verticalHeader().setVisible(False)
        self.ui.equationsTableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.ui.equationsTableView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.ui.equationsTableView.doubleClicked.connect(self.on_parameters_table_double_clicked)
        self.ui.equationsTableView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.equationsTableView.customContextMenuRequested.connect(self.show_equations_table_context_menu)

        self.parameters_model.block_updated.connect(self.on_block_updated)
        self.variables_model.block_updated.connect(self.on_block_updated)
        self.equations_model.block_updated.connect(self.on_block_updated)

        self.view: GraphicsView = GraphicsView(self.scene)
        self.ui.verticalLayout_3.removeWidget(self.ui.graphicsView)
        self.ui.graphicsView.deleteLater()
        self.ui.graphicsView = self.view
        self.ui.verticalLayout_3.addWidget(self.ui.graphicsView)

        # The canvas scene owns the graphical block items dropped from the tree library.
        self.ui.graphicsView.setAcceptDrops(True)
        self.ui.graphicsView.viewport().setAcceptDrops(True)
        self.ui.graphicsView.dragEnterEvent = self.graphicsDragEnterEvent
        self.ui.graphicsView.dragMoveEvent = self.graphicsDragMoveEvent
        self.ui.graphicsView.dropEvent = self.graphicsDropEvent

        # Button do it to save built scene
        self.ui.doItButton.clicked.connect(self.apply_changes)

        self.ui.toolBox.currentChanged.connect(self.handle_side_panel_page_changed)
        self.scene.selectionChanged.connect(self.on_scene_selection_changed)
        if self.mode == DynamicSimulationMode.EMT and self.main_editor:
            self._ensure_full_emt_editor_interface()
        else:
            pass

        _ensure_block_tree_names(self.main_block, prefix="block")

        requires_connection_bootstrap: bool = block_requires_editor_connection_bootstrap(self.main_block)

        # Automatically build items for models with no graphical info
        if not self.main_block.empty() and not self.main_block.diagram.node_data and not requires_connection_bootstrap:
            if self.main_block.children:
                blocks_list = list()
                for child in self.main_block.children:
                    item = self.generate_block_item_for_block(child)
                    blocks_list.append(item)
                self.add_connection_items(blocks_list)
                if len(blocks_list) != 0:
                    self.connect_items(blocks_list)
                else:
                    pass
            elif not self.main_block.children and not self.main_block.is_eq_decomposable():
                self.add_connection_items()


        # Build items for models with graphical info
        elif not self.main_block.diagram.node_data:
            # here we add the connection variables to the main block
            if self.main_editor:
                self.add_connection_vars()
                # self.add_api_obj_mapping()

            self.add_connection_items()
        else:
            pass
        self.rebuild_scene_from_diagram()

    @staticmethod
    def new_editor(var_factory: VarFactory,
                   block: Block,
                   api_object: ALL_DEV_TYPES,
                   circuit: MultiCircuit,
                   mode: DynamicSimulationMode):
        """
        Function to create a new instance of this class.
        :param var_factory:
        :param block:
        :param api_object:
        :param circuit:
        :param mode:
        :return:
        """
        return DynamicBlockEditorGUI(
            var_factory=var_factory,
            block=block,
            api_object=api_object,
            circuit=circuit,
            mode=mode,
        )

    def changeEvent(self, event: QtCore.QEvent) -> None:
        """
        Refresh runtime-owned editor strings after a Qt language change.

        :param event: Incoming Qt change event.
        :return: None.
        """
        QtWidgets.QMainWindow.changeEvent(self, event)

        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self.ui.retranslateUi(self)
            self.refresh_runtime_translations()
        else:
            pass

    def refresh_runtime_translations(self) -> None:
        """
        Refresh the editor strings that are created from Python code.

        :return: None.
        """
        self.setWindowTitle(self.tr("Dynamic Model Editor [{mode}]").format(mode=self.mode.name))
        self.variables_search.setPlaceholderText(self.tr("Search variables..."))
        self.parameters_search.setPlaceholderText(self.tr("Search parameters..."))
        self.equations_search.setPlaceholderText(self.tr("Search equations..."))
        item: Any
        for item in self.scene.items():
            refresh_port_metadata = getattr(item, "refresh_port_metadata", None)
            if callable(refresh_port_metadata):
                refresh_port_metadata()
            else:
                pass
        self.scene.update()

    # Todo: remove this function when all the dialogs are unified
    def set_modal_template_metadata(self, block: Block,
                                    kind: str,
                                    config: Dict[str, Any]) -> None:
        """
        Persist the modal-builder metadata on one block.

        :param block: Target block.
        :param kind: Stable modal kind key.
        :param config: Serializable modal configuration.
        :return: None.
        """
        block.__dict__[self.MODAL_TEMPLATE_KIND_ATTR] = kind
        block.__dict__[self.MODAL_TEMPLATE_CONFIG_ATTR] = copy.deepcopy(config)

    # Todo: remove this function when all the dialogs are unified
    def get_modal_template_metadata(self, block: Block | None) -> tuple[str | None, Dict[str, Any] | None]:
        """
        Return the modal-builder metadata stored on one block.

        :param block: Candidate block.
        :return: `(kind, config)` or `(None, None)` when absent.
        """
        if block is None:
            return None, None
        else:
            pass

        kind: Any = block.__dict__.get(self.MODAL_TEMPLATE_KIND_ATTR, None)
        config: Any = block.__dict__.get(self.MODAL_TEMPLATE_CONFIG_ATTR, None)

        if isinstance(kind, str) and isinstance(config, dict):
            return kind, copy.deepcopy(config)
        else:
            return None, None

    def focus_library_search(self) -> None:
        """
        Reveal and focus the library search box.
        """

        self.ui.toolBox.setCurrentWidget(self.ui.page_7)
        self.activateWindow()
        self.raise_()
        self.ui.librarySearchLineEdit.setFocus(QtCore.Qt.FocusReason.ShortcutFocusReason)
        self.ui.librarySearchLineEdit.selectAll()

    def reset_library_tree_expansion(self) -> None:
        """
        Restore the default expansion depth for the library tree.
        """

        self.ui.libraryTreeView.collapseAll()
        self.ui.libraryTreeView.expandToDepth(1)

    def on_library_search_text_changed(self, text: str) -> None:
        """
        Filter the library tree according to the current search text.
        """

        search_text: str = text.strip()
        self.library_proxy_model.setFilterFixedString(search_text)
        if search_text:
            self.ui.libraryTreeView.expandAll()
        else:
            self.reset_library_tree_expansion()

    def get_library_payload_from_mime_data(self,
                                           mime_data: QtCore.QMimeData) -> BlockType | BasicBlockTemplateDescriptor | RmsModelTemplate | EmtModelTemplate | FmuTemplate | None:
        """
        Decode the dragged library payload from the tree-view mime payload.

        :param mime_data:
        :return:
        """
        drag_token: str
        payload: object | None

        if mime_data.hasFormat(self.mime_type):
            drag_token = bytes(mime_data.data(self.mime_type)).decode("utf-8")
            payload = self.library.library_model.get_drag_payload(drag_token)

            if isinstance(payload,
                          (BlockType, BasicBlockTemplateDescriptor, RmsModelTemplate, EmtModelTemplate, FmuTemplate)):
                return payload
            else:
                return None
        else:
            return None

    def _build_position_changed_callback(self, block_uid: int) -> BlockPositionChangedCallback:
        """
        Build the explicit callback object used by graphics items to report movement.

        :param block_uid: Moved block uid.
        :return: Position change callback wrapper.
        """

        return BlockPositionChangedCallback(self, block_uid)


    def create_item_from_blocktype(self,
                                   blocktype: BlockType,
                                   x_pos: float,
                                   y_pos: float) -> GenericBlockItem | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem | None:
        """
        Materialize one library payload on the diagram scene.
        """

        count: int = self.block_counters.get(blocktype, 0) + 1
        item_name: str = f"{blocktype.name}_{count}"

        template_builder_class = self.blocktype2templatebuilder.get(blocktype, None)
        template_builder = template_builder_class(self.var_factory)
        name = "EMT fault"

        if template_builder is not None:
            dialog = DynTemplatesEditorDialog(name, template_builder.params)
            dialog.exec()
            template = template_builder.eval()
            block_model = template.block

        block_item: GenericBlockItem = GenericBlockItem(
            editor=self,
            var_factory=self.var_factory,
            subsys=block_model,
            api_object=self.api_object,
            mode=self.mode,
            name=item_name,
            position_changed_callback=self._build_position_changed_callback(block_model.uid)
        )

        self.block_counters[blocktype] = count
        block_item.set_subsystem(block_model)
        block_item.position_changed_callback = self._build_position_changed_callback(block_model.uid)
        block_item.build_item()
        self.main_block.add(block_model)
        self.scene.addItem(block_item)
        block_item.setPos(QtCore.QPointF(x_pos, y_pos))
        self.diagram.add_node(
            name=item_name,
            x=x_pos,
            y=y_pos,
            tpe=blocktype.name,
            device_uid=block_model.uid,
        )
        self.mark_unapplied_changes()
        return block_item

    def create_generic_block_item(self, block_type: BlockType, x_pos, y_pos) -> GenericBlockItem | None:
        """
        Create and place a generic block item.

        :param block_type:
        :param x_pos:
        :param y_pos:
        :return:
        """

        dialog = GenericBlockDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, inputs, outputs = dialog.get_values()

            model = create_generic_block(self.var_factory, inputs, outputs, name)
            self.main_block.add(model)
            item = GenericBlockItem(
                editor=self,
                var_factory=self.var_factory,
                subsys=model,
                api_object=self.api_object,
                mode=self.mode,
                name=model.name,
                position_changed_callback=self._build_position_changed_callback(model.uid)
            )

            item.setPos(QtCore.QPointF(x_pos, y_pos))
            self.scene.addItem(item)
            # save nodes in diagram
            self.diagram.add_node(
                name=name,
                x=x_pos,
                y=y_pos,
                device_uid=model.uid,
                tpe=block_type.name,
                state_ins=inputs,
                state_outs=[],
                algeb_ins=0,
                algeb_outs=[],
                subdiagram=model.diagram
            )

            self.mark_unapplied_changes()

            return item
        else:
            return None

    def create_basic_arithmetic_op_item(self, block_type: BlockType, x_pos: float,
                                        y_pos: float) -> RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem | None:
        """
        Create a Sum item that represents addition and subtraction
        """

        count: int = self.block_counters.get(block_type, 0) + 1
        item_name: str = f"{block_type.name}_{count}"

        template_builder = None
        block_model = None
        name = ""

        if block_type == BlockType.SUM:
            template_builder = basic_block_templates.AdderTemplate(vf=self.var_factory)
        elif block_type == BlockType.PRODUCT:
            template_builder = basic_block_templates.ProductTemplate(vf=self.var_factory)

        if template_builder is not None:
            dialog = DynTemplatesEditorDialog(name, template_builder.params)
            dialog.exec()
            template = template_builder.eval()
            block_model = template

        if block_model is not None and len(block_model.in_vars) <= 3:
            round_base_op_item: RoundBaseArithmeticOpItem = RoundBaseArithmeticOpItem(var_factory=self.var_factory,
                                                                                      subsys=block_model,
                                                                                      block_type=block_type,
                                                                                      editor=self,
                                                                                      position_changed_callback=self._build_position_changed_callback(
                                                                                          block_model.uid))

            self.block_counters[block_type] = count
            RoundBaseArithmeticOpItem.position_changed_callback = self._build_position_changed_callback(block_model.uid)
            self.main_block.add(block_model)
            self.scene.addItem(round_base_op_item)
            round_base_op_item.setPos(QtCore.QPointF(x_pos, y_pos))
            self.diagram.add_node(
                name=item_name,
                x=x_pos,
                y=y_pos,
                tpe=block_type.name,
                device_uid=block_model.uid,
            )
            self.mark_unapplied_changes()

            return round_base_op_item

        elif block_model is not None and len(block_model.in_vars) > 3:
            rect_base_op_item: RectBaseArithmeticOpItem = RectBaseArithmeticOpItem(var_factory=self.var_factory,
                                                                                   subsys=block_model,
                                                                                   editor=self,
                                                                                   position_changed_callback=self._build_position_changed_callback(
                                                                                       block_model.uid))

            self.block_counters[block_type] = count
            RoundBaseArithmeticOpItem.position_changed_callback = self._build_position_changed_callback(block_model.uid)
            self.main_block.add(block_model)
            self.scene.addItem(rect_base_op_item)
            rect_base_op_item.setPos(QtCore.QPointF(x_pos, y_pos))
            self.diagram.add_node(
                name=item_name,
                x=x_pos,
                y=y_pos,
                tpe=block_type.name,
                device_uid=block_model.uid,
            )
            self.mark_unapplied_changes()

            return rect_base_op_item

        return None


    @staticmethod
    def _extract_jmarti_phase_tuple(modal_config: Dict[str, Any]) -> tuple[bool, bool, bool, bool]:
        """
        Return the ordered phase tuple stored in one JMARTI modal configuration.

        :param modal_config: Persisted modal configuration.
        :return: ``(phase_n, phase_a, phase_b, phase_c)``.
        """
        return (
            bool(modal_config.get("phase_n", False)),
            bool(modal_config.get("phase_a", True)),
            bool(modal_config.get("phase_b", True)),
            bool(modal_config.get("phase_c", True)),
        )

    def _build_jmarti_fit_options_from_modal_config(self, modal_config: Dict[str, Any]) -> JMartiFitOptions:
        """
        Build one typed JMARTI fit-options object from one modal configuration.

        :param modal_config: Persisted GUI configuration.
        :return: Typed fit options.
        """
        resolved_config: Dict[str, Any] = self._build_default_jmarti_line_modal_config()
        resolved_config.update(modal_config)
        options_kwargs: Dict[str, Any] = dict()
        option_key: str

        for option_key in self.JMARTI_MODAL_OPTION_KEYS:
            options_kwargs[option_key] = resolved_config[option_key]

        return JMartiFitOptions(**options_kwargs)

    def _build_default_jmarti_line_modal_config(self,
                                                phase_n: bool = False,
                                                phase_a: bool = True,
                                                phase_b: bool = True,
                                                phase_c: bool = True) -> Dict[str, Any]:
        """
        Build one default persisted configuration for the JMARTI line modal.

        :param phase_n: Whether the neutral is enabled.
        :param phase_a: Whether phase A is enabled.
        :param phase_b: Whether phase B is enabled.
        :param phase_c: Whether phase C is enabled.
        :return: Default modal configuration.
        """
        options: JMartiFitOptions = JMartiFitOptions()
        nominal_frequency_hz: float = 50.0

        try:
            if self.circuit is not None and float(self.circuit.fbase) > 0.0:
                nominal_frequency_hz = float(self.circuit.fbase)
            else:
                pass
        except Exception:
            pass

        return dict({
            "phase_n": bool(phase_n),
            "phase_a": bool(phase_a),
            "phase_b": bool(phase_b),
            "phase_c": bool(phase_c),
            "data_source_mode": "auto_template",
            "nominal_frequency_hz": nominal_frequency_hz,
            "import_file_path": "",
            "import_line_length_m": 0.0,
            "sweep_low_hz": 10.0,
            "sweep_high_hz": 10000.0,
            "sweep_sample_count": 48,
            "reference_frequency_hz": float(options.reference_frequency_hz),
            "use_frequency_exploration_window": bool(options.use_frequency_exploration_window),
            "exploration_low_hz": float(options.exploration_low_hz),
            "exploration_high_hz": float(options.exploration_high_hz),
            "use_delay_fit_window": bool(options.use_delay_fit_window),
            "delay_fit_low_hz": float(options.delay_fit_low_hz),
            "delay_fit_high_hz": float(options.delay_fit_high_hz),
            "decoupling_warning_tolerance": float(options.decoupling_warning_tolerance),
            "loewner_relative_tolerance": float(options.loewner_relative_tolerance),
            "maximum_model_order": int(options.maximum_model_order),
            "forced_model_order": int(options.forced_model_order),
            "minimum_frequency_samples": int(options.minimum_frequency_samples),
            "vf_max_iterations": int(options.vf_max_iterations),
            "vf_pole_shift_tolerance": float(options.vf_pole_shift_tolerance),
            "vf_enforce_stable_poles": bool(options.vf_enforce_stable_poles),
            "vf_stability_real_part_floor": float(options.vf_stability_real_part_floor),
            "vf_include_constant_term": bool(options.vf_include_constant_term),
            "vf_include_proportional_term": bool(options.vf_include_proportional_term),
            "passivity_frequency_sample_count": int(options.passivity_frequency_sample_count),
            "passivity_minimum_real_yc_tolerance": float(options.passivity_minimum_real_yc_tolerance),
            "passivity_maximum_hres_gain_tolerance": float(options.passivity_maximum_hres_gain_tolerance),
            "fit_ready": False,
            "fit_source_description": "",
            "fit_status": (
                "Fit not computed yet. Accept the dialog to build or refresh the JMARTI fit for the attached line."
            ),
            "fit_diagnostics_text": "",
        })

    @staticmethod
    def _build_jmarti_fit_source_description(modal_config: Dict[str, Any],
                                             line_object: Line | None) -> str:
        """
        Return the user-facing description of the JMARTI fitting data source.

        :param modal_config: Persisted GUI configuration.
        :param line_object: Optional owning line object.
        :return: Source description.
        """
        if str(modal_config.get("data_source_mode", "auto_template")) == "import_frequency_samples":
            return f"Imported NPZ samples: {str(modal_config.get('import_file_path', ''))}"
        elif line_object is None or line_object.template is None:
            return "Automatic template source"
        elif isinstance(line_object.template, OverheadLineType):
            if len(line_object.template.wires_in_tower.data) > 0:
                return "Automatic sweep from OverheadLineType conductor geometry"
            else:
                return (
                    "Automatic RLGC sweep from OverheadLineType nominal matrices "
                    f"at {float(modal_config.get('nominal_frequency_hz', 0.0)):.4f} Hz"
                )
        elif isinstance(line_object.template, SequenceLineType):
            return (
                "Automatic RLGC sweep from SequenceLineType "
                f"at {float(modal_config.get('nominal_frequency_hz', 0.0)):.4f} Hz"
            )
        elif isinstance(line_object.template, UndergroundLineType):
            return (
                "Automatic RLGC sweep from UndergroundLineType "
                f"at {float(modal_config.get('nominal_frequency_hz', 0.0)):.4f} Hz"
            )
        else:
            return "Automatic template source"

    @staticmethod
    def _build_jmarti_fit_diagnostics_text(source_description: str,
                                           fit_bundle) -> str:
        """
        Build one human-readable JMARTI fit report for the GUI.

        :param source_description: Data-source description.
        :param fit_bundle: Computed fit bundle.
        :return: Multiline diagnostics text.
        """
        frequency_hz = fit_bundle.get_frequency_hz()
        passivity_report = fit_bundle.get_passivity_report()
        mode_delays = fit_bundle.get_mode_delays()
        yc_fits = fit_bundle.get_yc_fits()
        hres_fits = fit_bundle.get_hres_fits()
        diagnostics_lines: List[str] = list()
        mode_index: int = 0

        diagnostics_lines.append(f"Source: {source_description}")
        diagnostics_lines.append(f"Phases: {', '.join(fit_bundle.get_phase_labels())}")
        diagnostics_lines.append(
            f"Frequency band: {float(frequency_hz[0]):.6g} Hz to {float(frequency_hz[-1]):.6g} Hz ({frequency_hz.size} samples)"
        )
        diagnostics_lines.append(f"Reference modal frequency: {fit_bundle.get_reference_frequency_hz():.6g} Hz")
        diagnostics_lines.append(f"Line length: {fit_bundle.get_line_length_m():.6f} m")
        diagnostics_lines.append(
            f"Max decoupling Z/Y: {float(fit_bundle.get_decoupling_error_z().max()):.3e} / {float(fit_bundle.get_decoupling_error_y().max()):.3e}"
        )

        if passivity_report is None:
            diagnostics_lines.append("Passivity checks: not available")
        elif passivity_report.get_all_checks_pass():
            diagnostics_lines.append("Passivity checks: PASS")
        else:
            diagnostics_lines.append("Passivity checks: WARN")

        while mode_index < fit_bundle.get_mode_count():
            diagnostics_lines.append(
                f"Mode {mode_index}: tau = {mode_delays[mode_index].get_tau_s():.6e} s, phase RMS = {mode_delays[mode_index].get_rms_phase_error_rad():.3e} rad"
            )
            diagnostics_lines.append(
                f"  Yc: order {yc_fits[mode_index].get_poles_s().size}, rms {yc_fits[mode_index].get_fit_error_rms():.3e}, max {yc_fits[mode_index].get_max_relative_error():.3e}, stable {yc_fits[mode_index].get_stable()}, converged {yc_fits[mode_index].get_converged()}"
            )
            diagnostics_lines.append(
                f"  Hres: order {hres_fits[mode_index].get_poles_s().size}, rms {hres_fits[mode_index].get_fit_error_rms():.3e}, max {hres_fits[mode_index].get_max_relative_error():.3e}, stable {hres_fits[mode_index].get_stable()}, converged {hres_fits[mode_index].get_converged()}"
            )
            mode_index += 1

        return "\n".join(diagnostics_lines)

    @staticmethod
    def _build_jmarti_modal_tooltip(modal_config: Dict[str, Any]) -> str:
        """
        Build the tooltip shown for one JMARTI block item.

        :param modal_config: Persisted modal configuration.
        :return: Tooltip text.
        """
        diagnostics_text: str = str(modal_config.get("fit_diagnostics_text", "")).strip()

        if diagnostics_text:
            return diagnostics_text
        else:
            return str(modal_config.get("fit_status", "J_Marti line"))

    def _apply_jmarti_line_fit_configuration(self, modal_config: Dict[str, Any]) -> tuple[Dict[str, Any], Any | None]:
        """
        Apply one JMARTI GUI configuration to the attached line object when possible.

        :param modal_config: Dialog configuration.
        :return: Updated persisted configuration including fit status.
        """
        updated_config: Dict[str, Any] = self._build_default_jmarti_line_modal_config(
            phase_n=bool(modal_config.get("phase_n", False)),
            phase_a=bool(modal_config.get("phase_a", True)),
            phase_b=bool(modal_config.get("phase_b", True)),
            phase_c=bool(modal_config.get("phase_c", True)),
        )
        updated_config.update(modal_config)
        updated_config["block_type"] = BlockType.EMT_JMARTI_LINE.name
        fit_ready: bool = False
        fit_status: str = str(updated_config.get("fit_status", ""))
        fit_diagnostics_text: str = str(updated_config.get("fit_diagnostics_text", ""))
        line_object: Line | None
        fit_source_description: str
        fit_bundle = None

        if isinstance(self.api_object, Line):
            line_object = self.api_object
        else:
            line_object = None

        fit_source_description = self._build_jmarti_fit_source_description(updated_config, line_object)

        if str(updated_config.get("data_source_mode", "auto_template")) == "import_frequency_samples":
            fallback_line_length_m: float | None

            if float(updated_config.get("import_line_length_m", 0.0)) > 0.0:
                fallback_line_length_m = float(updated_config["import_line_length_m"])
            elif line_object is not None and float(line_object.length) > 0.0:
                fallback_line_length_m = float(line_object.length) * 1000.0
            else:
                fallback_line_length_m = None

            try:
                fit_bundle = build_jmarti_fit_bundle_from_frequency_samples(
                    samples=load_jmarti_frequency_samples_from_npz(
                        file_path=str(updated_config.get("import_file_path", "")),
                        phase_n=bool(updated_config["phase_n"]),
                        phase_a=bool(updated_config["phase_a"]),
                        phase_b=bool(updated_config["phase_b"]),
                        phase_c=bool(updated_config["phase_c"]),
                        fallback_line_length_m=fallback_line_length_m,
                    ),
                    options=self._build_jmarti_fit_options_from_modal_config(updated_config),
                )
            except ValueError as exc:
                fit_status = f"Fit not computed: {exc}"
                fit_diagnostics_text = fit_status
                QtWidgets.QMessageBox.warning(self, "EMT J_Marti line", fit_status)
        elif line_object is None:
            fit_status = (
                "Fit not computed: open the EMT editor on one concrete line device to build length-dependent JMARTI data."
            )
            fit_diagnostics_text = fit_status
        else:
            if line_object.template is None:
                fit_status = "Fit not computed: attach one compatible line template to the line device first."
                fit_diagnostics_text = fit_status
            else:
                try:
                    fit_bundle = build_jmarti_fit_bundle_from_frequency_samples(
                        samples=build_jmarti_frequency_samples_from_line(
                            line=line_object,
                            phase_n=bool(updated_config["phase_n"]),
                            phase_a=bool(updated_config["phase_a"]),
                            phase_b=bool(updated_config["phase_b"]),
                            phase_c=bool(updated_config["phase_c"]),
                            low_hz=float(updated_config["sweep_low_hz"]),
                            high_hz=float(updated_config["sweep_high_hz"]),
                            sample_count=int(updated_config["sweep_sample_count"]),
                            nominal_frequency_hz=float(updated_config["nominal_frequency_hz"]),
                            sbase_mva=float(self.circuit.Sbase) if self.circuit is not None else None,
                        ),
                        options=self._build_jmarti_fit_options_from_modal_config(updated_config),
                    )
                except ValueError as exc:
                    fit_status = f"Fit not computed: {exc}"
                    fit_diagnostics_text = fit_status
                    QtWidgets.QMessageBox.warning(self, "EMT J_Marti line", fit_status)

        if fit_bundle is not None:
            passivity_report = fit_bundle.get_passivity_report()
            decoupling_error_z = fit_bundle.get_decoupling_error_z()
            decoupling_error_y = fit_bundle.get_decoupling_error_y()
            max_decoupling_z: float = float(decoupling_error_z.max()) if decoupling_error_z.size > 0 else 0.0
            max_decoupling_y: float = float(decoupling_error_y.max()) if decoupling_error_y.size > 0 else 0.0

            if passivity_report is None or passivity_report.get_all_checks_pass():
                passivity_state = "pass"
            else:
                passivity_state = "warn"

            fit_ready = True
            fit_status = (
                "Fit computed: "
                f"{fit_bundle.get_mode_count()} modes, "
                f"{fit_bundle.get_frequency_hz().size} samples, "
                f"max decoupling Z/Y = {max_decoupling_z:.3e}/{max_decoupling_y:.3e}, "
                f"passivity = {passivity_state}."
            )
            fit_diagnostics_text = self._build_jmarti_fit_diagnostics_text(fit_source_description, fit_bundle)

        updated_config["fit_ready"] = fit_ready
        updated_config["fit_source_description"] = fit_source_description
        updated_config["fit_status"] = fit_status
        updated_config["fit_diagnostics_text"] = fit_diagnostics_text
        return updated_config, fit_bundle

    def create_jmarti_line_emt_block_item(self, x_pos: float, y_pos: float) -> GenericBlockItem | None:
        """
        Create one EMT J_Marti line block configured through its dedicated modal.

        :param x_pos: Drop x position.
        :param y_pos: Drop y position.
        :return: Created block item or ``None`` when the dialog is cancelled.
        """
        dialog = JMartiLineEmtDialog(self, initial_config=self._build_default_jmarti_line_modal_config())

        if dialog.exec() == QDialog.DialogCode.Accepted:
            modal_config, fit_bundle = self._apply_jmarti_line_fit_configuration(dialog.get_configuration())
        else:
            return None

        phase_n, phase_a, phase_b, phase_c = self._extract_jmarti_phase_tuple(modal_config)
        count: int = self.block_counters.get(BlockType.EMT_JMARTI_LINE, 0) + 1
        item_name: str = f"{BlockType.EMT_JMARTI_LINE.name}_{count}"
        block_model = create_emt_wizard_block(
            phase_n=phase_n,
            phase_a=phase_a,
            phase_b=phase_b,
            phase_c=phase_c,
            var_factory=self.var_factory,
            block_type=BlockType.EMT_JMARTI_LINE,
            item_name=item_name,
        )
        block_item: GenericBlockItem = GenericBlockItem(
            editor=self,
            var_factory=self.var_factory,
            subsys=block_model,
            api_object=self.api_object,
            mode=self.mode,
            name=item_name,
            position_changed_callback=self._build_position_changed_callback(block_model.uid)
        )

        if block_model is None:
            return None
        else:
            pass

        self.set_modal_template_metadata(block_model, kind="jmarti_line_emt", config=modal_config)
        set_jmarti_block_fit_bundle(block_model, fit_bundle)
        set_jmarti_block_runtime_data(block_model, None)
        self.block_counters[BlockType.EMT_JMARTI_LINE] = count
        block_item.set_subsystem(block_model)
        block_item.position_changed_callback = self._build_position_changed_callback(block_model.uid)
        block_item.build_item()
        block_item.setToolTip(self._build_jmarti_modal_tooltip(modal_config))
        self.main_block.add(block_model)
        self.scene.addItem(block_item)
        block_item.setPos(QtCore.QPointF(x_pos, y_pos))
        self.diagram.add_node(
            name=item_name,
            x=x_pos,
            y=y_pos,
            tpe=BlockType.EMT_JMARTI_LINE.name,
            device_uid=block_model.uid,
        )
        self.mark_unapplied_changes()
        return block_item

    def create_block_item_mix(self, block_type: BlockType, x_pos: float, y_pos: float) -> GenericBlockItem | None:
        """
        Create and place a block item in the canvas scene.

        :param block_type:
        :param x_pos:
        :param y_pos:
        :return:
        """
        block_model = None
        item_name = ""
        count: int = self.block_counters.get(block_type, 0) + 1
        # if blocktype is generic we need to know initial input and output ports from the user
        if block_type == BlockType.GENERIC:
            dialog = GenericBlockDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                item_name, inputs, outputs = dialog.get_values()
                block_model = create_generic_block(self.var_factory, inputs, outputs, item_name)

        else:

            item_name: str = f"{block_type.name}_{count}"
            block_model: Block = create_block_of_type(
                var_factory=self.var_factory,
                block_type=block_type,
                item_name=item_name,
                api_object=self.api_object,
            )
            self.block_counters[block_type] = count

        # no we have the name and the block
        if block_model is not None:
            self.main_block.add(block_model)
            item = GenericBlockItem(
                editor=self,
                var_factory=self.var_factory,
                subsys=block_model,
                api_object=self.api_object,
                mode=self.mode,
                name=block_model.name,
                position_changed_callback=self._build_position_changed_callback(block_model.uid)
            )

            item.setPos(QtCore.QPointF(x_pos, y_pos))
            self.scene.addItem(item)

            self.diagram.add_node(
                name=item_name,
                x=x_pos,
                y=y_pos,
                tpe=block_type.name,
                device_uid=block_model.uid
            )

            self.mark_unapplied_changes()
            # Keep the diagram synchronized so later features can rebuild from the same data source.

            return item
        else:
            return None

    def create_block_item(self, block_type: BlockType, x_pos: float, y_pos: float) -> BlockItem | None:
        """
        Create and place a block item in the canvas scene.

        :param block_type:
        :param x_pos:
        :param y_pos:
        :return:
        """
        count: int = self.block_counters.get(block_type, 0) + 1
        item_name: str = f"{block_type.name}_{count}"
        block_item: BlockItem = BlockItem(editor=self, var_factory=self.var_factory, api_object=self.api_object,
                                          mode=self.mode,
                                          name=item_name)
        block_model: Block | None = create_block_of_type(
            var_factory=self.var_factory,
            block_type=block_type,
            item_name=item_name,
            api_object=self.api_object,
        )

        if block_model is not None:
            # The symbolic block has to be attached first so the graphics item can build its ports from it.
            self.block_counters[block_type] = count
            block_item.set_subsystem(block_model)
            block_item.position_changed_callback = self._build_position_changed_callback(block_model.uid)
            block_item.build_item()

            # The editor block is the authoritative model container for later save/rebuild steps.
            self.main_block.add(block_model)
            self.scene.addItem(block_item)
            block_item.setPos(QtCore.QPointF(x_pos, y_pos))

            # Keep the diagram synchronized so later features can rebuild from the same data source.
            self.diagram.add_node(
                name=item_name,
                x=x_pos,
                y=y_pos,
                tpe=block_type.name,
                device_uid=block_model.uid
            )

            # self.block_added.emit(block_item.subsys)

            self.mark_unapplied_changes()

            return block_item
        else:
            return None

    def connect_items(self, items_list: List[GenericBlockItem]):
        """
        create connection lines to show in editor
        :param items_list:
        :type items_list:
        :return:
        :rtype:
        """

        for item_1 in items_list:
            for item_2 in items_list:
                if item_1.subsys.uid != item_2.subsys.uid:
                    pairs, power_flow_pairs = find_connections(item_1.subsys, item_2.subsys)
                    if pairs:
                        self.create_conn_items(item_1, item_2, pairs)

                    if power_flow_pairs:
                        self.create_conn_items(item_1, item_2, power_flow_pairs)

                    pairs, power_flow_pairs = find_connections(item_2.subsys, item_1.subsys)
                    if pairs:
                        self.create_conn_items(item_2, item_1, pairs)

                    if power_flow_pairs:
                        self.create_conn_items(item_1, item_2, power_flow_pairs)

    def connect_items_pf(self, items_list: List[GenericBlockItem]):
        """
        create connection lines to show in editor
        :param items_list:
        :type items_list:
        :return:
        :rtype:
        """

        for item_1 in items_list:
            for item_2 in items_list:
                if item_1.subsys.uid != item_2.subsys.uid:
                    power_flow_pairs = find_connections_pf(item_1.subsys, item_2.subsys)

                    if power_flow_pairs:
                        self.create_conn_items(item_1, item_2, power_flow_pairs)

                    power_flow_pairs = find_connections_pf(item_2.subsys, item_1.subsys)

                    if power_flow_pairs:
                        self.create_conn_items(item_1, item_2, power_flow_pairs)

    def connect_blocks(self, blocks_list: List[Block]):
        """
        create connection lines to show in editor
        :param items_list:
        :type items_list:
        :return:
        :rtype:
        """

        for block_1 in blocks_list:
            for block_2 in blocks_list:
                if block_1.uid != block_2.uid:
                    pairs, power_flow_pairs = find_connections(block_1, block_2)
                    if pairs:
                        self.create_conn_items(block_1, block_2, pairs)

                    if power_flow_pairs:
                        self.create_conn_items(block_1, block_2, power_flow_pairs)

                    pairs, power_flow_pairs = find_connections(block_2.subsys, block_1.subsys)
                    if pairs:
                        self.create_conn_items(block_2, block_1, pairs)

                    if power_flow_pairs:
                        self.create_conn_items(block_1, block_2, power_flow_pairs)

    def create_conn_items(self, item_source: GenericBlockItem, item_dest: GenericBlockItem,
                          pairs: List[tuple[Var, Var]]):
        """
        Create the connection items for two block items
        :param item_source:
        :type item_source:
        :param item_dest:
        :type item_dest:
        :param pairs:
        :type pairs:
        :return:
        :rtype:
        """
        for source_var, target_var in pairs:
            source_port = None
            for port in item_source.outputs:
                if port.base_var is not None and port.base_var.uid == source_var.uid:
                    source_port = port
                    break

            target_port = None
            for port in item_dest.inputs:
                if port.base_var is not None and port.base_var.uid == target_var.uid:
                    target_port = port
                    break
            if target_port is not None and source_port is not None:
                connection = ConnectionItem(
                    source_port=source_port,
                    target_port=target_port,
                    diagram=self.diagram,
                    editor=self,
                )
                self.scene.addItem(connection)
                self.diagram.add_branch(
                    connectionitem_uid=connection.uid,
                    device_uid_from=item_source.subsys.uid,
                    device_uid_to=item_dest.subsys.uid,
                    port_number_from=source_port.index,
                    port_number_to=target_port.index,
                    color=self.WIRE_COLOR.name()
                )

    def generate_block_item_for_block(self, block_model: Block,
                                      x: float | None = None,
                                      y: float | None = None) -> GenericBlockItem | None:
        """
        Create and place a block item in the canvas scene.

        :param block_model:
        :param x: Optional pre-computed x position (Sugiyama layout).
        :param y: Optional pre-computed y position (Sugiyama layout).
        :return:
        """
        item_name: str = f"{block_model.name}"

        if block_model is not None:
            item = GenericBlockItem(
                editor=self,
                var_factory=self.var_factory,
                subsys=block_model,
                api_object=self.api_object,
                mode=self.mode,
                name=item_name,
                position_changed_callback=self._build_position_changed_callback(block_model.uid)
            )

            # The symbolic block has to be attached first so the graphics item can build its ports from it.

            if x is None or y is None:
                x, y = self._calculate_next_block_position(item)
            item.setPos(QtCore.QPointF(x, y))
            self.scene.addItem(item)

            self.diagram.add_node(
                name=item_name,
                x=x,
                y=y,
                tpe="",
                device_uid=block_model.uid
            )

            self.mark_unapplied_changes()

            return item
        else:
            return None

    def _calculate_next_block_position(self, item: GenericBlockItem) -> tuple[float, float]:
        """
        Calculate the next available position for a block item using a grid layout.

        :param item: The block item to calculate position for (used to get its dimensions).
        :return: Tuple of (x, y) coordinates.
        """
        SCENE_WIDTH: float = 1200.0
        SCENE_HEIGHT: float = 800.0
        MARGIN_Y: float = 80.0
        COL_SPACING: float = 200.0
        ROW_SPACING: float = 150.0

        existing_count = sum(1 for i in self.scene.items() if isinstance(i, GenericBlockItem))

        GRID_COLS: int = 3

        row: int = existing_count // GRID_COLS
        col: int = existing_count % GRID_COLS

        total_width: float = GRID_COLS * COL_SPACING
        start_x: float = (SCENE_WIDTH - total_width) / 2

        x: float = start_x + col * COL_SPACING
        y: float = MARGIN_Y + row * ROW_SPACING

        return x, y

    def create_connection_block_item(self, var: Var, block_type: BlockType, x_pos: float,
                                     y_pos: float, blocks_list: List[BlockItem] | None) -> BlockItem | None:
        """
        Create and place a block item in the canvas scene.

        :param var:
        :type var:
        :param block_type:
        :param x_pos:
        :param y_pos:
        :param blocks_list:
        :return:
        """
        count: int = self.block_counters.get(block_type, 0) + 1

        if var is None:
            # The RMS/EMT connection builders should never emit ``None``.
            # Keep this guard so a malformed editor interface does not crash the GUI.
            return None
        else:
            item_name: str = f"{var.name}"
            block_item: ProtectedConnectionBlockItem = ProtectedConnectionBlockItem(editor=self,
                                                                                    var_factory=self.var_factory,
                                                                                    name=item_name)
            block_model: Block = Block()

            if block_type == BlockType.INPUT_CONN:
                block_model.out_vars.append(var)

            elif block_type == BlockType.OUTPUT_CONN:
                block_model.in_vars.append(var)

            else:
                pass

            if block_model is not None:
                # The symbolic block has to be attached first so the graphics item can build its ports from it.

                block_item.set_subsystem(block_model)
                block_item.position_changed_callback = self._build_position_changed_callback(block_model.uid)
                block_item.build_item()

                # The editor block is the authoritative model container for later save/rebuild steps.
                self.main_block.add(block_model)
                self.scene.addItem(block_item)
                if blocks_list is not None:
                    blocks_list.append(block_item)
                else:
                    pass
                block_item.setPos(QtCore.QPointF(x_pos, y_pos))

                # Keep the diagram synchronized so later features can rebuild from the same data source.
                self.diagram.add_node(
                    name=item_name,
                    x=x_pos,
                    y=y_pos,
                    tpe=block_type.name,
                    device_uid=block_model.uid
                )

                return block_item
            else:
                return None

    def create_template_block_item(self,
                                   template: RmsModelTemplate | EmtModelTemplate | FmuTemplate,
                                   x_pos: float,
                                   y_pos: float) -> BlockItem | GenericBlockItem | None:
        """
        Create and place a copied template block in the canvas scene.

        :param template:
        :param x_pos:
        :param y_pos:
        :return:
        """
        item_name: str = template.name
        block_model: Block = duplicate_block(template.block, var_factory=self.var_factory)
        self.main_block.add(block_model)
        item: GenericBlockItem = GenericBlockItem(
            editor=self,
            var_factory=self.var_factory,
            subsys=block_model,
            api_object=self.api_object,
            mode=self.mode,
            name=item_name,
            position_changed_callback=self._build_position_changed_callback(block_model.uid)
        )

        if item_name:
            block_model.name = item_name
        else:
            item_name = block_model.name
        item.setPos(QtCore.QPointF(x_pos, y_pos))
        self.scene.addItem(item)

        self.diagram.add_node(
            name=item_name,
            x=x_pos,
            y=y_pos,
            tpe=self.TEMPLATE_NODE_TYPE,
            device_uid=block_model.uid
        )

        self.mark_unapplied_changes()

        return item

    def create_lookup_array_linear_descriptor_item(self,
                                                   descriptor: BasicBlockTemplateDescriptor,
                                                   x_pos: float,
                                                   y_pos: float) -> GenericBlockItem | None:
        """
        Materialize one modal-configured 1D lookup-table descriptor.

        :param descriptor: Lookup descriptor selected from the native catalog.
        :param x_pos: Drop x position.
        :param y_pos: Drop y position.
        :return: Created block item or None when the dialog is cancelled.
        """
        dialog: LookupArrayLinearDialog = LookupArrayLinearDialog(block_label=descriptor.display_label, parent=self)
        dialog_result: int = dialog.exec()

        if dialog_result == QDialog.DialogCode.Accepted:
            x_points, y_points = dialog.get_points()
        else:
            return None

        clip_enabled: bool = descriptor.template_key not in {
            "lookup_array_linear_noclipping",
            "lookup_array_object_linear_noclipping",
        }
        count: int = len(self.main_block.children) + 1
        item_name: str = f"{descriptor.template_key}_{count}"
        template: EmtModelTemplate = build_lookup_array_linear_runtime_template(
            vf=self.var_factory,
            x_points=x_points,
            y_points=y_points,
            clip=clip_enabled,
            name=item_name,
        )
        self.set_modal_template_metadata(
            template.block,
            kind="lookup_array_1d",
            config=dict({
                "descriptor_key": descriptor.template_key,
                "display_label": descriptor.display_label,
                "x_points": x_points,
                "y_points": y_points,
            }),
        )
        return self.create_template_block_item(template=template, x_pos=x_pos, y_pos=y_pos)

    # TODO: create PV power plant block item

    def create_shunt_component_emt_block_item(self,
                                              block_type: BlockType,
                                              x_pos: float,
                                              y_pos: float) -> GenericBlockItem | None:
        """
        Create one modal-configured single-component EMT shunt block.

        :param block_type: ``R_LOAD_EMT``, ``L_LOAD_EMT`` or ``C_LOAD_EMT``.
        :param x_pos: Drop x position.
        :param y_pos: Drop y position.
        :return: Created block item or None when the dialog is cancelled.
        """
        dialog = self._build_shunt_component_emt_dialog(block_type=block_type)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            shunt_config = dialog.get_configuration()
        else:
            return None

        try:
            template_kwargs = self._build_shunt_component_emt_template_kwargs(block_type=block_type,
                                                                              modal_config=shunt_config)
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "EMT Shunt", str(exc))
            return None

        count: int = self.block_counters.get(block_type, 0) + 1
        item_name: str = f"{block_type.name}_{count}"
        block_model = emt_templates.get_shunt_rlc_combo_emt_template(vf=self.var_factory,
                                                                     name=item_name,
                                                                     **template_kwargs).block
        block_item: GenericBlockItem = GenericBlockItem(
            editor=self,
            var_factory=self.var_factory,
            subsys=block_model,
            api_object=self.api_object,
            mode=self.mode,
            name=item_name,
            position_changed_callback=self._build_position_changed_callback(block_model.uid)
        )

        self.set_modal_template_metadata(block_model, kind="shunt_component_emt",
                                         config=dict(shunt_config, block_type=block_type.name))
        self._annotate_internal_grounding_link_blocks(block_model)

        # The dynamic editor must not overwrite the static injection
        # connection. The EMT block stores its own symbolic topology.
        if isinstance(self.api_object, InjectionParent):
            pass
        else:
            pass

        self.block_counters[block_type] = count
        block_item.set_subsystem(block_model)
        block_item.position_changed_callback = self._build_position_changed_callback(block_model.uid)
        block_item.build_item()
        self.main_block.add(block_model)
        self.scene.addItem(block_item)
        block_item.setPos(QtCore.QPointF(x_pos, y_pos))
        self.diagram.add_node(
            name=item_name,
            x=x_pos,
            y=y_pos,
            tpe=block_type.name,
            device_uid=block_model.uid,
        )
        self.mark_unapplied_changes()
        return block_item

    def create_nonlinear_resistor_emt_block_item(self, x_pos: float, y_pos: float) -> GenericBlockItem | None:
        """
        Create one modal-configured ATP-like EMT nonlinear resistor block.

        :param x_pos: Drop x position.
        :param y_pos: Drop y position.
        :return: Created block item or None when the dialog is cancelled.
        """
        dialog = LookupArrayLinearDialog(
            block_label="Nonlinear resistor EMT V-I curve",
            initial_points=list([(0.0, 0.0), (1.0, 0.1), (1.5, 1.0), (2.0, 10.0)]),
            parent=self,
            x_label="V",
            y_label="I",
            preview_enabled=True,
            preview_title="Nonlinear resistor EMT V-I curve",
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            voltage_points, current_points = dialog.get_points()
        else:
            return None

        count: int = self.block_counters.get(BlockType.NONLINEAR_RESISTOR_EMT, 0) + 1
        item_name: str = f"nonlinear_resistor_emt_{count}"
        block_model = emt_templates.get_nonlinear_resistor_emt_template(
            vf=self.var_factory,
            voltage_points=voltage_points,
            current_points=current_points,
            name=item_name,
        ).block
        block_item: GenericBlockItem = GenericBlockItem(
            editor=self, var_factory=self.var_factory,
            subsys=block_model,
            api_object=self.api_object,
            mode=self.mode,
            name=item_name,
            position_changed_callback=self._build_position_changed_callback(block_model.uid)
        )

        self.set_modal_template_metadata(
            block_model,
            kind="nonlinear_resistor_emt",
            config=dict({
                "voltage_points": voltage_points,
                "current_points": current_points,
            }),
        )

        self.block_counters[BlockType.NONLINEAR_RESISTOR_EMT] = count
        block_item.set_subsystem(block_model)
        block_item.position_changed_callback = self._build_position_changed_callback(block_model.uid)
        block_item.build_item()
        self.main_block.add(block_model)
        self.scene.addItem(block_item)
        block_item.setPos(QtCore.QPointF(x_pos, y_pos))
        self.diagram.add_node(
            name=item_name,
            x=x_pos,
            y=y_pos,
            tpe=BlockType.NONLINEAR_RESISTOR_EMT.name,
            device_uid=block_model.uid,
        )
        self.mark_unapplied_changes()
        return block_item

    def _build_shunt_component_emt_dialog(self,
                                          block_type: BlockType,
                                          initial_config: Dict[str, Any] | None = None) -> ShuntComponentEmtDialog:
        """
        Build the modal dialog used by one simple EMT shunt block.

        :param block_type: ``R_LOAD_EMT``, ``L_LOAD_EMT`` or ``C_LOAD_EMT``.
        :param initial_config: Optional persisted modal configuration.
        :return: Configured dialog instance.
        """
        component_kind: str | None = _get_shunt_component_kind(block_type)
        nominal_voltage_kv, base_power_mva, base_frequency_hz = self._get_rlc_combo_base_values()
        allow_static_device_values: bool = isinstance(self.api_object, (Load, Shunt, ControllableShunt))
        static_connection_type: ShuntConnectionType | None = None

        if isinstance(self.api_object, (Load, Shunt, ControllableShunt)):
            static_connection_type = self.api_object.conn
        elif isinstance(self.api_object, InjectionParent):
            static_connection_type = self.api_object.conn
        else:
            pass

        if component_kind is None:
            raise ValueError(f"Unsupported simple EMT shunt block type '{block_type.name}'")
        else:
            pass

        return ShuntComponentEmtDialog(
            component_kind=component_kind,
            parent=self,
            initial_config=initial_config,
            allow_static_device_values=allow_static_device_values,
            static_connection_type=static_connection_type,
            nominal_voltage_kv=nominal_voltage_kv,
            base_power_mva=base_power_mva,
            base_frequency_hz=base_frequency_hz,
        )

    def _annotate_internal_grounding_link_blocks(self, block_model: Block) -> None:
        """
        Attach modal metadata to auto-generated internal grounding-link blocks.

        :param block_model: Parent block that may own nested grounding-link children.
        :return: None.
        """
        child_block: Block
        grounding_config: Dict[str, Any] = dict({
            "solid_connection": True,
            "include_r": False,
            "include_l": False,
            "include_c": False,
            "input_mode": "physical",
            "resistance_ohm": 1.0,
            "inductive_value": 0.01,
            "capacitive_value": 1.0e-6,
        })

        for child_block in _iter_child_blocks(block_model):
            if child_block.name.endswith("_grounding_link"):
                self.set_modal_template_metadata(child_block, kind="grounding_link_emt", config=grounding_config)
            else:
                pass

    def _get_rlc_combo_base_values(self) -> tuple[float | None, float | None, float | None]:
        """
        Resolve the host base values used by the EMT combined RLC modal.

        :return: ``(Vnom_kV, Sbase_MVA, fbase_Hz)`` tuple.
        """
        nominal_voltage_kv: float | None = None
        base_power_mva: float | None = None
        base_frequency_hz: float | None = None

        if isinstance(self.api_object, InjectionParent):
            bus = self.api_object.bus
            if bus is not None:
                try:
                    nominal_voltage_kv = float(bus.Vnom)
                except (TypeError, ValueError):
                    nominal_voltage_kv = None
            else:
                pass
        else:
            pass

        if self.circuit is not None:
            try:
                base_power_mva = float(self.circuit.Sbase)
            except (AttributeError, TypeError, ValueError):
                base_power_mva = None

            try:
                base_frequency_hz = float(self.circuit.fBase)
            except (AttributeError, TypeError, ValueError):
                base_frequency_hz = None
        else:
            pass

        return nominal_voltage_kv, base_power_mva, base_frequency_hz

    def _get_rlc_combo_base_frequency_hz(self) -> float:
        """
        Return the frequency used to convert reactances into EMT L/C values.

        :return: Frequency in hertz.
        """
        _, _, base_frequency_hz = self._get_rlc_combo_base_values()

        if base_frequency_hz is not None and base_frequency_hz > 0.0:
            return base_frequency_hz
        else:
            return 50.0

    def _build_rlc_direct_values_from_modal_config(self, modal_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert one R/L/C modal configuration into direct EMT values.

        :param modal_config: Raw modal configuration.
        :return: Direct-value dictionary shared by EMT RLC modal builders.
        :raises ValueError: If the modal configuration is not numerically valid.
        """
        include_r: bool = bool(modal_config.get("include_r", False))
        include_l: bool = bool(modal_config.get("include_l", False))
        include_c: bool = bool(modal_config.get("include_c", False))
        solid_connection: bool = bool(modal_config.get("solid_connection", False))
        input_mode: str = str(modal_config.get("input_mode", "physical"))
        resistance_ohm: float = float(modal_config.get("resistance_ohm", 1.0))
        inductive_value: float = float(modal_config.get("inductive_value", 0.01))
        capacitive_value: float = float(modal_config.get("capacitive_value", 1.0e-6))
        angular_frequency: float = 2.0 * math.pi * self._get_rlc_combo_base_frequency_hz()

        if solid_connection:
            return dict({
                "solid_connection": True,
                "include_r": False,
                "include_l": False,
                "include_c": False,
                "direct_r_value": None,
                "direct_l_value": None,
                "direct_c_value": None,
            })
        else:
            pass

        if input_mode in {"physical", "reactance"}:
            pass
        else:
            raise ValueError(f"Unsupported RLC input mode '{input_mode}'.")

        if include_r and resistance_ohm <= 0.0:
            raise ValueError("Resistance must be greater than zero when the resistor branch is enabled.")
        else:
            pass

        if include_l and inductive_value <= 0.0:
            if input_mode == "reactance":
                raise ValueError("Inductive reactance must be greater than zero when the inductor branch is enabled.")
            else:
                raise ValueError("Inductance must be greater than zero when the inductor branch is enabled.")
        else:
            pass

        if include_c and capacitive_value <= 0.0:
            if input_mode == "reactance":
                raise ValueError("Capacitive reactance must be greater than zero when the capacitor branch is enabled.")
            else:
                raise ValueError("Capacitance must be greater than zero when the capacitor branch is enabled.")
        else:
            pass

        direct_l_value: float | None = None
        if include_l:
            if input_mode == "physical":
                direct_l_value = inductive_value
            else:
                direct_l_value = inductive_value / angular_frequency
        else:
            pass

        direct_c_value: float | None = None
        if include_c:
            if input_mode == "physical":
                direct_c_value = capacitive_value
            else:
                direct_c_value = 1.0 / (angular_frequency * capacitive_value)
        else:
            pass

        return dict({
            "solid_connection": False,
            "include_r": include_r,
            "include_l": include_l,
            "include_c": include_c,
            "direct_r_value": resistance_ohm if include_r else None,
            "direct_l_value": direct_l_value,
            "direct_c_value": direct_c_value,
        })

    def _build_shunt_component_emt_template_kwargs(self,
                                                   block_type: BlockType,
                                                   modal_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert one single-component EMT shunt modal configuration into template arguments.

        :param block_type: ``R_LOAD_EMT``, ``L_LOAD_EMT`` or ``C_LOAD_EMT``.
        :param modal_config: Raw modal configuration.
        :return: Template-builder keyword arguments.
        """
        use_static_load_values: bool = bool(
            modal_config.get("use_static_device_values", modal_config.get("use_static_load_values", False)))

        # Static-value mode must expose load-derived P/Q mappings to the EMT
        # block, so the direct R/L/C values are left unresolved on purpose.
        if use_static_load_values:
            template_kwargs = dict({
                "solid_connection": False,
                "include_r": False,
                "include_l": False,
                "include_c": False,
                "direct_r_value": None,
                "direct_l_value": None,
                "direct_c_value": None,
            })
        else:
            template_kwargs = dict(self._build_rlc_direct_values_from_modal_config(modal_config))

        if "solid_connection" in template_kwargs:
            del template_kwargs["solid_connection"]
        else:
            pass

        component_kind: str | None = _get_shunt_component_kind(block_type)
        if component_kind == "R":
            template_kwargs["include_r"] = True
            template_kwargs["include_l"] = False
            template_kwargs["include_c"] = False
            if use_static_load_values:
                template_kwargs["direct_r_value"] = None
            else:
                pass
        elif component_kind == "L":
            template_kwargs["include_r"] = False
            template_kwargs["include_l"] = True
            template_kwargs["include_c"] = False
            if use_static_load_values:
                template_kwargs["direct_l_value"] = None
            else:
                pass
        elif component_kind == "C":
            template_kwargs["include_r"] = False
            template_kwargs["include_l"] = False
            template_kwargs["include_c"] = True
            if use_static_load_values:
                template_kwargs["direct_c_value"] = None
            else:
                pass
        else:
            raise ValueError(f"Unsupported simple EMT shunt block type '{block_type.name}'")

        template_kwargs.update({
            "phA": bool(modal_config.get("phA", True)),
            "phB": bool(modal_config.get("phB", True)),
            "phC": bool(modal_config.get("phC", True)),
            "connection_type": modal_config.get("connection_type", ShuntConnectionType.GroundedStar),
        })
        return template_kwargs

    def _append_emt_branch_side_connection_specs(
            self,
            specs: List[ConnectionVarSpec],
            bus: Bus,
            side: str,
    ) -> None:
        """
        Append the default editable EMT connection specs for one branch side.

        The editor opens AC branch terminals with the full N/A/B/C voltage and
        current interface. The user can remove phases manually. When changes
        are applied, the connected bus EMT shell is rebuilt from the remaining
        visible ports.

        DC terminals are different because they do not have phases. They only
        expose one side-specific voltage input and one side-specific current
        output.

        :param specs: Connection specification list to extend.
        :param bus: Bus connected to the selected branch side.
        :param side: Branch side identifier. Expected values are ``from`` and ``to``.
        :return: None.
        """
        safe_bus_name: str = self._get_safe_bus_name(bus)
        voltage_refs: List[VarPowerFlowReferenceType] = list()
        current_refs: List[VarPowerFlowReferenceType] = list()

        # DC terminals must use side-specific references so that branch
        # interfaces do not mix the from and to bus quantities.
        if bus.is_dc:
            if side == "from":
                voltage_refs.append(VarPowerFlowReferenceType.Vf_dc)
                current_refs.append(VarPowerFlowReferenceType.If_dc)
            elif side == "to":
                voltage_refs.append(VarPowerFlowReferenceType.Vt_dc)
                current_refs.append(VarPowerFlowReferenceType.It_dc)
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "EMT branch interface",
                    f"Unsupported EMT branch side '{side}'. No ports were created for this side.",
                )
        else:
            # AC terminals intentionally open with the complete editable
            # phase set. The saved editor interface will later define the
            # effective bus phase mask.
            if side == "from":
                voltage_refs.append(VarPowerFlowReferenceType.vf_N)
                voltage_refs.append(VarPowerFlowReferenceType.vf_A)
                voltage_refs.append(VarPowerFlowReferenceType.vf_B)
                voltage_refs.append(VarPowerFlowReferenceType.vf_C)

                current_refs.append(VarPowerFlowReferenceType.if_N)
                current_refs.append(VarPowerFlowReferenceType.if_A)
                current_refs.append(VarPowerFlowReferenceType.if_B)
                current_refs.append(VarPowerFlowReferenceType.if_C)
            elif side == "to":
                voltage_refs.append(VarPowerFlowReferenceType.vt_N)
                voltage_refs.append(VarPowerFlowReferenceType.vt_A)
                voltage_refs.append(VarPowerFlowReferenceType.vt_B)
                voltage_refs.append(VarPowerFlowReferenceType.vt_C)

                current_refs.append(VarPowerFlowReferenceType.it_N)
                current_refs.append(VarPowerFlowReferenceType.it_A)
                current_refs.append(VarPowerFlowReferenceType.it_B)
                current_refs.append(VarPowerFlowReferenceType.it_C)
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "EMT branch interface",
                    f"Unsupported EMT branch side '{side}'. No ports were created for this side.",
                )

        reference: VarPowerFlowReferenceType

        for reference in voltage_refs:
            specs.append(ConnectionVarSpec("input", reference, f"{reference.value}_{safe_bus_name}"))

        for reference in current_refs:
            specs.append(ConnectionVarSpec(
                "output",
                reference,
                f"net_conn_{reference.value}_{safe_bus_name}_{self.api_object.name}",
            ))

    def create_inverse_lookup_array_linear_descriptor_item(self,
                                                           descriptor: BasicBlockTemplateDescriptor,
                                                           x_pos: float,
                                                           y_pos: float) -> GenericBlockItem | None:
        """
        Materialize one modal-configured inverse 1D lookup-table descriptor.

        :param descriptor: Lookup descriptor selected from the native catalog.
        :param x_pos: Drop x position.
        :param y_pos: Drop y position.
        :return: Created block item or None when the dialog is cancelled.
        """
        dialog: LookupArrayLinearDialog = LookupArrayLinearDialog(block_label=descriptor.display_label, parent=self)
        dialog_result: int = dialog.exec()

        if dialog_result == QDialog.DialogCode.Accepted:
            x_points, y_points = dialog.get_points()
        else:
            return None

        count: int = len(self.main_block.children) + 1
        item_name: str = f"{descriptor.template_key}_{count}"
        template: EmtModelTemplate = build_inverse_lookup_array_linear_runtime_template(
            vf=self.var_factory,
            x_points=x_points,
            y_points=y_points,
            name=item_name,
        )
        self.set_modal_template_metadata(
            template.block,
            kind="lookup_array_inverse",
            config=dict({
                "descriptor_key": descriptor.template_key,
                "display_label": descriptor.display_label,
                "x_points": x_points,
                "y_points": y_points,
            }),
        )
        return self.create_template_block_item(template=template, x_pos=x_pos, y_pos=y_pos)

    def create_lookup_array_spline_descriptor_item(self,
                                                   descriptor: BasicBlockTemplateDescriptor,
                                                   x_pos: float,
                                                   y_pos: float) -> GenericBlockItem | None:
        """
        Materialize one modal-configured 1D spline lookup descriptor.

        :param descriptor: Lookup descriptor selected from the native catalog.
        :param x_pos: Drop x position.
        :param y_pos: Drop y position.
        :return: Created block item or None when the dialog is cancelled.
        """
        dialog: LookupArrayLinearDialog = LookupArrayLinearDialog(block_label=descriptor.display_label, parent=self)
        dialog_result: int = dialog.exec()

        if dialog_result == QDialog.DialogCode.Accepted:
            x_points, y_points = dialog.get_points()
        else:
            return None

        count: int = len(self.main_block.children) + 1
        item_name: str = f"{descriptor.template_key}_{count}"
        template: EmtModelTemplate = build_lookup_array_spline_runtime_template(
            vf=self.var_factory,
            x_points=x_points,
            y_points=y_points,
            name=item_name,
        )
        self.set_modal_template_metadata(
            template.block,
            kind="lookup_array_spline",
            config=dict({
                "descriptor_key": descriptor.template_key,
                "display_label": descriptor.display_label,
                "x_points": x_points,
                "y_points": y_points,
            }),
        )
        return self.create_template_block_item(template=template, x_pos=x_pos, y_pos=y_pos)

    def create_lookup_matrix_linear_descriptor_item(self,
                                                    descriptor: BasicBlockTemplateDescriptor,
                                                    x_pos: float,
                                                    y_pos: float) -> GenericBlockItem | None:
        """
        Materialize one modal-configured 2D lookup-matrix descriptor.

        :param descriptor: Lookup descriptor selected from the native catalog.
        :param x_pos: Drop x position.
        :param y_pos: Drop y position.
        :return: Created block item or None when the dialog is cancelled.
        """
        dialog: LookupMatrixLinearDialog = LookupMatrixLinearDialog(block_label=descriptor.display_label, parent=self)
        dialog_result: int = dialog.exec()

        if dialog_result == QDialog.DialogCode.Accepted:
            x_points, y_points, z_matrix = dialog.get_matrix_data()
        else:
            return None

        count: int = len(self.main_block.children) + 1
        item_name: str = f"{descriptor.template_key}_{count}"
        template: EmtModelTemplate = build_lookup_matrix_linear_runtime_template(
            vf=self.var_factory,
            x_points=x_points,
            y_points=y_points,
            z_matrix=z_matrix,
            name=item_name,
        )
        self.set_modal_template_metadata(
            template.block,
            kind="lookup_matrix_linear",
            config=dict({
                "descriptor_key": descriptor.template_key,
                "display_label": descriptor.display_label,
                "x_points": x_points,
                "y_points": y_points,
                "z_matrix": z_matrix,
            }),
        )
        return self.create_template_block_item(template=template, x_pos=x_pos, y_pos=y_pos)

    def create_lookup_matrix_spline_descriptor_item(self,
                                                    descriptor: BasicBlockTemplateDescriptor,
                                                    x_pos: float,
                                                    y_pos: float) -> GenericBlockItem | None:
        """
        Materialize one modal-configured 2D spline lookup-matrix descriptor.

        :param descriptor: Lookup descriptor selected from the native catalog.
        :param x_pos: Drop x position.
        :param y_pos: Drop y position.
        :return: Created block item or None when the dialog is cancelled.
        """
        dialog: LookupMatrixLinearDialog = LookupMatrixLinearDialog(block_label=descriptor.display_label, parent=self)
        dialog_result: int = dialog.exec()

        if dialog_result == QDialog.DialogCode.Accepted:
            x_points, y_points, z_matrix = dialog.get_matrix_data()
        else:
            return None

        count: int = len(self.main_block.children) + 1
        item_name: str = f"{descriptor.template_key}_{count}"
        template: EmtModelTemplate = build_lookup_matrix_spline_runtime_template(
            vf=self.var_factory,
            x_points=x_points,
            y_points=y_points,
            z_matrix=z_matrix,
            name=item_name,
        )
        self.set_modal_template_metadata(
            template.block,
            kind="lookup_matrix_spline",
            config=dict({
                "descriptor_key": descriptor.template_key,
                "display_label": descriptor.display_label,
                "x_points": x_points,
                "y_points": y_points,
                "z_matrix": z_matrix,
            }),
        )
        return self.create_template_block_item(template=template, x_pos=x_pos, y_pos=y_pos)

    def create_library_payload_item(self,
                                    payload: BlockType | BasicBlockTemplateDescriptor | RmsModelTemplate | EmtModelTemplate | FmuTemplate,
                                    x_pos: float,
                                    y_pos: float) -> GenericBlockItem | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem | None:
        """
        Materialize one library payload on the diagram scene.
        """
        if isinstance(payload, BlockType) and payload in self.blocktype2templatebuilder:
            return self.create_item_from_blocktype(payload, x_pos, y_pos)

        elif isinstance(payload, BlockType) and payload == BlockType.FROM_GOTO:
            items = self.create_signal_pair_item(x_pos=x_pos, y_pos=y_pos)
            return items[0] if items else None

        elif isinstance(payload, BlockType) and payload == BlockType.SUM:
            return self.create_basic_arithmetic_op_item(BlockType.SUM, x_pos, y_pos)

        elif isinstance(payload, BlockType) and payload == BlockType.PRODUCT:
            return self.create_basic_arithmetic_op_item(BlockType.PRODUCT, x_pos, y_pos)

        elif isinstance(payload, BlockType) and payload == BlockType.GENERIC:
            return self.create_generic_block_item(block_type=payload, x_pos=x_pos, y_pos=y_pos)

        elif isinstance(payload, BlockType) and payload == BlockType.EMT_JMARTI_LINE:
            return self.create_jmarti_line_emt_block_item(x_pos=x_pos, y_pos=y_pos)

        elif isinstance(payload, BlockType) and payload == BlockType.NONLINEAR_RESISTOR_EMT:
            return self.create_nonlinear_resistor_emt_block_item(x_pos=x_pos, y_pos=y_pos)

        elif isinstance(payload, BlockType) and payload in {
            BlockType.R_LOAD_EMT,
            BlockType.L_LOAD_EMT,
            BlockType.C_LOAD_EMT,
        }:
            return self.create_shunt_component_emt_block_item(block_type=payload, x_pos=x_pos, y_pos=y_pos)

        elif isinstance(payload, BlockType):
            return self.create_block_item_mix(block_type=payload, x_pos=x_pos, y_pos=y_pos)

        elif isinstance(payload, BasicBlockTemplateDescriptor):
            if payload.template_key in self.LOOKUP_ARRAY_LINEAR_DESCRIPTOR_KEYS:
                return self.create_lookup_array_linear_descriptor_item(payload, x_pos, y_pos)
            elif payload.template_key in self.INVERSE_LOOKUP_ARRAY_LINEAR_DESCRIPTOR_KEYS:
                return self.create_inverse_lookup_array_linear_descriptor_item(payload, x_pos, y_pos)
            elif payload.template_key in self.LOOKUP_ARRAY_SPLINE_DESCRIPTOR_KEYS:
                return self.create_lookup_array_spline_descriptor_item(payload, x_pos, y_pos)
            elif payload.template_key in self.LOOKUP_MATRIX_LINEAR_DESCRIPTOR_KEYS:
                return self.create_lookup_matrix_linear_descriptor_item(payload, x_pos, y_pos)
            elif payload.template_key in self.LOOKUP_MATRIX_SPLINE_DESCRIPTOR_KEYS:
                return self.create_lookup_matrix_spline_descriptor_item(payload, x_pos, y_pos)
            else:
                template: EmtModelTemplate = load_basic_block_catalog_template(payload, self.var_factory)
                return self.create_template_block_item(template=template, x_pos=x_pos, y_pos=y_pos)

        elif isinstance(payload, (RmsModelTemplate, EmtModelTemplate, FmuTemplate)):
            return self.create_template_block_item(template=payload, x_pos=x_pos, y_pos=y_pos)
        else:
            return None

    def create_signal_pair_item(self,
                                x_pos: float,
                                y_pos: float) -> tuple[PairedItem, PairedItem] | None:
        """
        Create a signal pair (input + output blocks sharing the same variable).

        :param x_pos: X coordinate for the drop position.
        :param y_pos: Y coordinate for the drop position.
        :return: Tuple of (input_item, output_item) or None on failure.
        """
        count: int = self.block_counters.get("signal_pair", 0) + 1
        self.block_counters["signal_pair"] = count
        item_name: str = str(count)

        blk_in, blk_out = signal_pair(self.var_factory, item_name)

        self.main_block.add(blk_in)
        self.main_block.add(blk_out)

        item_in = PairedItem(editor=self,
                             var_factory=self.var_factory,
                             subsys=blk_in,
                             api_object=self.api_object,
                             mode=self.mode,
                             name=blk_in.name,
                             position_changed_callback=self._build_position_changed_callback(blk_in.uid)
                             )
        item_in.setPos(QtCore.QPointF(x_pos - 50.0, y_pos))
        self.scene.addItem(item_in)
        self.diagram.add_node(
            name=blk_in.name,
            x=x_pos - 50.0,
            y=y_pos,
            tpe="signal_in",
            device_uid=blk_in.uid
        )

        item_out = PairedItem(editor=self,
                              var_factory=self.var_factory,
                              subsys=blk_out,
                              api_object=self.api_object,
                              mode=self.mode,
                              name=blk_out.name,
                              position_changed_callback=self._build_position_changed_callback(blk_out.uid)
                              )
        item_out.setPos(QtCore.QPointF(x_pos + 50.0, y_pos))
        self.scene.addItem(item_out)
        self.diagram.add_node(
            name=blk_out.name,
            x=x_pos + 50.0,
            y=y_pos,
            tpe="signal_out",
            device_uid=blk_out.uid
        )

        item_in.set_paired_item(item_out)
        item_out.set_paired_item(item_in)

        self.mark_unapplied_changes()
        return item_in, item_out

    def remove_connection_item(self, item: ConnectionItem) -> None:
        """
        Remove a connection and restore the destination symbolic input.

        :param item:
        :return:
        """
        source_port: PortItem | BranchingItem = item.source_port
        target_port: PortItem | BranchingItem = item.target_port

        if item.uid in self.diagram.con_data:
            del self.diagram.con_data[item.uid]
        else:
            pass

        if source_port.connections is not None:
            if item in source_port.connections:
                source_port.connections.remove(item)
            else:
                pass

            if len(source_port.connections) == 0:
                source_port.connections = None
            else:
                pass
        else:
            pass

        if target_port.connections is not None:
            if item in target_port.connections:
                target_port.connections.remove(item)
            else:
                pass

            if len(target_port.connections) == 0:
                target_port.connections = None
            else:
                pass
        else:
            pass

        if isinstance(source_port.subsystem, BlockItem):
            source_port.subsystem._refresh_connection_color()
        if isinstance(target_port.subsystem, BlockItem):
            target_port.subsystem._refresh_connection_color()

        if isinstance(source_port, PortItem):
            source_port._update_port_visibility()
        if isinstance(target_port, PortItem):
            target_port._update_port_visibility()

        self.scene.removeItem(item)

        # disconnect variables
        if source_port.subsystem.subsys is not None and target_port.subsystem.subsys is not None:
            dst_var: Var = source_port.subsystem.subsys.out_vars[source_port.index]
            target_var: Var = target_port.subsystem.subsys.in_vars[target_port.index]

            if target_var.network_conn:
                self.var_factory.remove_connection(dst_var, target_var)
                if not isinstance(target_port.subsystem, (RoundBaseArithmeticOpItem, RectBaseArithmeticOpItem)):
                    source_port.subsystem.refresh_port_metadata()
            else:
                self.var_factory.remove_connection(target_var, dst_var)
                if not isinstance(target_port.subsystem, (RoundBaseArithmeticOpItem, RectBaseArithmeticOpItem)):
                    target_port.subsystem.refresh_port_metadata()

    def remove_block_item(self,
                          item: BlockItem | GenericBlockItem | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem) -> None:
        """
        Remove a block and all of its attached connections.

        :param item:
        :return:
        """
        port: PortItem
        conn: ConnectionItem
        connections_to_remove: List[ConnectionItem] = list()
        child_block: Block

        if isinstance(item, (BlockItem, GenericBlockItem)):
            item.close_editor_window()
        else:
            pass

        # find connections to remove
        for port in item.inputs + item.outputs:
            if port.connections is not None:
                for conn in port.connections:
                    if conn not in connections_to_remove:
                        connections_to_remove.append(conn)
                    else:
                        pass
            else:
                pass

        # remove item from scene
        self.scene.removeItem(item)

        # remove blocks and diagrams from main_block
        if item.subsys is not None:
            self._remove_connection_interface_for_block(item)

            for child_block in list(self.main_block.children):
                if child_block.uid == item.subsys.uid:
                    self.main_block.children.remove(child_block)
                else:
                    pass

            if item.subsys.uid in self.diagram.node_data:
                del self.diagram.node_data[item.subsys.uid]
            else:
                pass
        else:
            pass

        # remove connections
        for conn in connections_to_remove:
            self.remove_connection_item(conn)

    def _remove_connection_interface_for_block(self,
                                               item: BlockItem | GenericBlockItem | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem) -> None:
        """
        Remove the saved top-level connection variable for one editor port block.

        The connection blocks drawn on the canvas are only wrappers around the
        actual root-block interface variables stored in ``main_block``. When the
        user deletes one of those wrappers, the saved interface variable and its
        external-mapping entry must be deleted as well so later EMT assembly sees
        the edited interface exactly as shown in the editor.

        :param item: Scene item being removed.
        :return: None.
        """
        node_data: Any | None = None
        connection_var: Var | None = None

        if item.subsys is None:
            return
        else:
            pass

        node_data = self.diagram.node_data.get(item.subsys.uid, None)

        if node_data is None:
            return
        else:
            pass

        if node_data.tpe == BlockType.INPUT_CONN.name:
            if len(item.subsys.out_vars) > 0:
                connection_var = item.subsys.out_vars[0]
                self._remove_root_connection_var(connection_var=connection_var, direction="input")
            else:
                pass
        elif node_data.tpe == BlockType.OUTPUT_CONN.name:
            if len(item.subsys.in_vars) > 0:
                connection_var = item.subsys.in_vars[0]
                self._remove_root_connection_var(connection_var=connection_var, direction="output")
            else:
                pass
        else:
            pass

    def _remove_root_connection_var(self, connection_var: Var, direction: str) -> None:
        """
        Remove one saved root-block interface variable and its mapping entries.

        :param connection_var: Root-block network-connection variable to remove.
        :param direction: ``input`` for ``main_block.in_vars`` or ``output`` for
            ``main_block.out_vars``.
        :return: None.
        """
        mapping_keys_to_remove: List[VarPowerFlowReferenceType] = list()
        mapping_key: VarPowerFlowReferenceType
        mapped_var: Var | None

        if direction == "input":
            self.main_block.in_vars = [var for var in self.main_block.in_vars if var.uid != connection_var.uid]
        elif direction == "output":
            self.main_block.out_vars = [var for var in self.main_block.out_vars if var.uid != connection_var.uid]
        else:
            raise ValueError(f"Unsupported root connection direction {direction}")

        # Remove all external references that still point to the deleted port so
        # the persisted block interface matches the visible editor interface.
        for mapping_key, mapped_var in self.main_block.external_mapping.items():
            if mapped_var is not None and mapped_var.uid == connection_var.uid:
                mapping_keys_to_remove.append(mapping_key)
            else:
                pass

        for mapping_key in mapping_keys_to_remove:
            del self.main_block.external_mapping[mapping_key]

    def remove_item(self,
                    item: BlockItem | GenericBlockItem | ConnectionItem | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem) -> None:
        """
        Remove a block or connection from scene and model state.

        :param item:
        :return:
        """
        if isinstance(item, ConnectionItem):
            self.remove_connection_item(item)
            self.mark_unapplied_changes()
        elif isinstance(item, (BlockItem, GenericBlockItem, RoundBaseArithmeticOpItem, RectBaseArithmeticOpItem)):
            self.remove_block_item(item)
            self.mark_unapplied_changes()
        else:
            pass

    def add_connection_vars(self) -> None:
        """
        Add the connection variables required to couple the edited device with the grid.

        :return:
        """
        specs: List[ConnectionVarSpec]

        if self.mode == DynamicSimulationMode.RMS:
            if isinstance(self.api_object, BranchParent):
                specs = self._build_rms_branch_connection_specs()
            elif isinstance(self.api_object, InjectionParent):
                specs = self._build_rms_injection_connection_specs()
            else:
                specs = list()

            self._materialize_connection_specs(specs)
        elif self.mode == DynamicSimulationMode.EMT:
            if isinstance(self.api_object, BranchParent):
                specs = self._build_emt_branch_connection_specs()
            elif isinstance(self.api_object, InjectionParent):
                specs = self._build_emt_injection_connection_specs()
            else:
                specs = list()

            self._materialize_connection_specs(specs)

        else:
            raise ValueError(f"Unsupported dynamic editor mode {self.mode}")

    # def add_connection_vars_rms(self):
    #     """
    #     Add a block with bus connection variables to connect the device
    #     :return:
    #     """
    #
    #     specs: List[ConnectionVarSpec] = list()
    #
    #     if isinstance(self.api_object, BranchParent):
    #         specs = self._build_rms_branch_connection_specs()
    #     elif isinstance(self.api_object, InjectionParent):
    #         specs = self._build_rms_injection_connection_specs()
    #     else:
    #         pass
    #
    #     self._materialize_connection_specs(specs)
    #
    # def add_connection_vars_rms(self):
    #     """
    #     Add a block with bus connection variables to connect the device
    #     :return:
    #     """
    #     if isinstance(self.api_object, BranchParent):
    #         specs = self._build_rms_branch_connection_specs()
    #     elif isinstance(self.api_object, InjectionParent):
    #         specs = self._build_rms_injection_connection_specs()
    #     else:
    #         specs = list()
    #
    #     self._materialize_connection_specs(specs)
    #
    def add_connection_items(self, blocks_list: List[BlockItem] | None = None):
        """
        for every input and output var in the main block of the editor we build a block item to connect connection variables

        :return:
        :rtype:
        """
        SCENE_WIDTH: float = 1200.0
        SCENE_HEIGHT: float = 800.0
        MARGIN_X: float = 100.0
        MARGIN_Y: float = 80.0
        BLOCK_HEIGHT: float = 80.0
        MIN_SPACING: float = 60.0
        MAX_SPACING: float = 180.0

        num_inputs: int = len(self.main_block.in_vars)
        num_outputs: int = len(self.main_block.out_vars)

        if num_inputs > 0:
            available_height: float = SCENE_HEIGHT - 2 * MARGIN_Y
            input_spacing: float = min(MAX_SPACING, max(MIN_SPACING, available_height / (num_inputs + 1)))
        else:
            input_spacing: float = MAX_SPACING

        if num_outputs > 0:
            available_height = SCENE_HEIGHT - 2 * MARGIN_Y
            output_spacing: float = min(MAX_SPACING, max(MIN_SPACING, available_height / (num_outputs + 1)))
        else:
            output_spacing = MAX_SPACING

        for i, invar in enumerate(self.main_block.in_vars):
            y_pos: float = MARGIN_Y + input_spacing * (i + 1) - BLOCK_HEIGHT / 2
            self.create_connection_block_item(invar, BlockType.INPUT_CONN, MARGIN_X, y_pos, blocks_list)

        for i, outvar in enumerate(self.main_block.out_vars):
            y_pos = MARGIN_Y + output_spacing * (i + 1) - BLOCK_HEIGHT / 2
            x_pos: float = SCENE_WIDTH - MARGIN_X - BLOCK_HEIGHT
            self.create_connection_block_item(outvar, BlockType.OUTPUT_CONN, x_pos, y_pos, blocks_list)

        self.scene.setSceneRect(0, 0, SCENE_WIDTH, SCENE_HEIGHT)
        self.view.fitInView(self.scene.sceneRect(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)

    def _ensure_emt_bus_model(self, bus: Any) -> None:
        """
        Ensure that one bus already owns an EMT model before the editor tries to expose its ports.

        :param bus: Bus API object.
        :return: None.
        """

        if bus.emt_model.empty():
            if self.circuit is None:
                raise ValueError("The EMT dynamic editor requires the circuit context to initialize bus EMT models.")
            else:
                if self._bus_requires_default_emt_shell(bus):
                    self._show_emt_bus_fallback_warning(bus)
                else:
                    pass
                get_bus_emt_template(self.circuit, bus)
        else:
            pass

    def _bus_requires_default_emt_shell(self, bus: Any) -> bool:
        """
        Detect whether the editor will have to synthesize the default ABC EMT bus shell.

        The warning matters because the user may expect existing EMT network connectivity,
        but in an empty or RMS-only network the editor must fabricate a generic bus shell
        so the EMT model can still be edited.

        :param bus: Bus API object.
        :return: ``True`` when the editor must synthesize the default EMT bus shell.
        """

        if bus.is_dc:
            return False
        else:
            if self.circuit is None:
                return False
            else:
                has_connected_branch: bool = False
                branch = None
                for branch in self.circuit.get_branches_iter(add_vsc=True, add_switch=True, add_hvdc=True):
                    if bus == branch.bus_from or bus == branch.bus_to:
                        has_connected_branch = True
                    else:
                        pass
                return not has_connected_branch

    def _show_emt_bus_fallback_warning(self, bus: Any) -> None:
        """
        Show one warning when the editor fabricates the default ABC EMT bus shell.

        :param bus: Bus API object.
        :return: None.
        """

        if self._emt_bus_fallback_warning_shown:
            pass
        else:
            application = QtWidgets.QApplication.instance()
            if application is None:
                self._emt_bus_fallback_warning_shown = True
            else:
                platform_name: str = application.platformName().lower()
                if platform_name == "offscreen":
                    self._emt_bus_fallback_warning_shown = True
                else:
                    QtWidgets.QMessageBox.information(
                        self,
                        "EMT bus shell created",
                        (
                            f"The bus '{bus.name}' does not have an EMT bus shell yet.\n\n"
                            "VeraGrid will create a default ABC EMT bus shell so the EMT model can be edited. "
                            "If you need the exact EMT network ports, create the EMT network elements first and reopen the editor."
                        ),
                    )
                    self._emt_bus_fallback_warning_shown = True

    def get_injection_emt_voltage_pairs(self, bus: Any) -> List[tuple[VarPowerFlowReferenceType, Any]]:
        """
        Get the ordered EMT bus-voltage references used by injection models.

        :param bus: Bus API object.
        :return: Reference-variable pairs.
        """

        self._ensure_emt_bus_model(bus)
        if bus.is_dc:
            v_dc, _, _, _ = get_bus_emt_algebraic_vars(bus.emt_model)
            return [(VarPowerFlowReferenceType.Vdc, v_dc)]
        else:
            v_n, v_a, v_b, v_c = get_bus_emt_algebraic_vars(bus.emt_model)
            pairs: List[tuple[VarPowerFlowReferenceType, Any]] = list()
            if v_n is not None:
                pairs.append((VarPowerFlowReferenceType.v_N, v_n))
            else:
                pass
            if v_a is not None:
                pairs.append((VarPowerFlowReferenceType.v_A, v_a))
            else:
                pass
            if v_b is not None:
                pairs.append((VarPowerFlowReferenceType.v_B, v_b))
            else:
                pass
            if v_c is not None:
                pairs.append((VarPowerFlowReferenceType.v_C, v_c))
            else:
                pass
            return pairs

    def get_branch_emt_voltage_pairs(self,
                                     bus: Any,
                                     side: str) -> List[tuple[VarPowerFlowReferenceType, Any]]:
        """
        Get the ordered EMT bus-voltage references used by branch models.

        :param bus: Bus API object.
        :param side: Branch side, either ``from`` or ``to``.
        :return: Reference-variable pairs.
        """

        self._ensure_emt_bus_model(bus)
        if bus.is_dc:
            pairs: List[tuple[VarPowerFlowReferenceType, Any]] = list()

            vdc, _, _, _ = get_bus_emt_algebraic_vars(bus.emt_model)

            ref = VarPowerFlowReferenceType.Vdc
            if vdc is not None:
                pairs.append((ref, vdc))

            return pairs
        else:
            v_n, v_a, v_b, v_c = get_bus_emt_algebraic_vars(bus.emt_model)
            if side == "from":
                refs = [
                    VarPowerFlowReferenceType.vf_N,
                    VarPowerFlowReferenceType.vf_A,
                    VarPowerFlowReferenceType.vf_B,
                    VarPowerFlowReferenceType.vf_C,
                ]
            else:
                if side == "to":
                    refs = [
                        VarPowerFlowReferenceType.vt_N,
                        VarPowerFlowReferenceType.vt_A,
                        VarPowerFlowReferenceType.vt_B,
                        VarPowerFlowReferenceType.vt_C,
                    ]
                else:
                    raise ValueError(f"Unsupported branch EMT side {side}")

            pairs: List[tuple[VarPowerFlowReferenceType, Any]] = list()
            for reference, variable in zip(refs, [v_n, v_a, v_b, v_c]):
                if variable is not None:
                    pairs.append((reference, variable))
                else:
                    pass
            return pairs

    def _materialize_connection_specs(self, specs: List[ConnectionVarSpec]) -> None:
        """
        Create all connection variables described by the given specs and attach them to the main block.

        :param specs:
        :return:
        """
        spec: ConnectionVarSpec
        for spec in specs:
            var = self.var_factory.add_var(spec.visible_name, spec.reference, True)

            if spec.direction == "input":
                self.main_block.in_vars.append(var)
            elif spec.direction == "output":
                self.main_block.out_vars.append(var)
            else:
                raise ValueError(f"Unsupported connection direction {spec.direction}")

            self.main_block.external_mapping[spec.reference] = var

    def _build_rms_injection_connection_specs(self) -> List[ConnectionVarSpec]:
        """
        Build all RMS connection-variable specs for an injection device.

        :return:
        """
        specs: List[ConnectionVarSpec] = list()

        if self.api_object.bus.rms_model.empty():
            initialize_bus_rms(self.api_object.bus, self.var_factory)
        else:
            pass

        specs.extend(build_rms_bus_input_specs(
            bus=self.api_object.bus,
            voltage_reference=VarPowerFlowReferenceType.Vm,
            angle_reference=VarPowerFlowReferenceType.Va,
            dc_voltage_reference=VarPowerFlowReferenceType.Vdc,
            terminal_label="",
        ))
        specs.extend(build_rms_bus_output_specs(
            bus=self.api_object.bus,
            active_power_reference=VarPowerFlowReferenceType.P,
            reactive_power_reference=VarPowerFlowReferenceType.Q,
            terminal_label="",
        ))

        if len(specs) > 0 and specs[-1].visible_name.endswith("_"):
            specs[-1].visible_name = specs[-1].visible_name.rstrip("_")
        else:
            pass

        if len(specs) > 1 and specs[-2].visible_name.endswith("_"):
            specs[-2].visible_name = specs[-2].visible_name.rstrip("_")
        else:
            pass

        return specs

    def _build_rms_branch_connection_specs(self) -> List[ConnectionVarSpec]:
        """
        Build all RMS connection-variable specs for a branch device.

        :return:
        """
        if self.api_object.bus_from.rms_model.empty():
            initialize_bus_rms(self.api_object.bus_from, self.var_factory)

        if self.api_object.bus_to.rms_model.empty():
            initialize_bus_rms(self.api_object.bus_to, self.var_factory)

        specs: List[ConnectionVarSpec] = list()

        specs.extend(build_rms_bus_input_specs(
            bus=self.api_object.bus_from,
            voltage_reference=VarPowerFlowReferenceType.Vmf,
            angle_reference=VarPowerFlowReferenceType.Vaf,
            dc_voltage_reference=VarPowerFlowReferenceType.Vf_dc,
            terminal_label="f",
        ))
        specs.extend(build_rms_bus_input_specs(
            bus=self.api_object.bus_to,
            voltage_reference=VarPowerFlowReferenceType.Vmt,
            angle_reference=VarPowerFlowReferenceType.Vat,
            dc_voltage_reference=VarPowerFlowReferenceType.Vt_dc,
            terminal_label="t",
        ))

        specs.extend(build_rms_bus_output_specs(
            bus=self.api_object.bus_from,
            active_power_reference=VarPowerFlowReferenceType.Pf,
            reactive_power_reference=VarPowerFlowReferenceType.Qf,
            terminal_label="f",
        ))
        specs.extend(build_rms_bus_output_specs(
            bus=self.api_object.bus_to,
            active_power_reference=VarPowerFlowReferenceType.Pt,
            reactive_power_reference=VarPowerFlowReferenceType.Qt,
            terminal_label="t",
        ))

        return specs

    # def _build_emt_injection_connection_specs(self) -> List[ConnectionVarSpec]:
    #     """
    #     Build the default maximum EMT connection-variable specs for an injection device.
    #
    #     :return:
    #     """
    #     safe_bus_name: str = self._get_safe_bus_name(self.api_object.bus)
    #     specs: List[ConnectionVarSpec] = list()
    #
    #     # The editor must expose the full editable EMT contract up front. Static
    #     # bus-domain and phase compatibility are validated later during EMT build.
    #     specs.append(ConnectionVarSpec("input", VarPowerFlowReferenceType.v_N, f"v_N_{safe_bus_name}"))
    #     specs.append(ConnectionVarSpec("input", VarPowerFlowReferenceType.v_A, f"v_A_{safe_bus_name}"))
    #     specs.append(ConnectionVarSpec("input", VarPowerFlowReferenceType.v_B, f"v_B_{safe_bus_name}"))
    #     specs.append(ConnectionVarSpec("input", VarPowerFlowReferenceType.v_C, f"v_C_{safe_bus_name}"))
    #     specs.append(ConnectionVarSpec("input", VarPowerFlowReferenceType.Vdc, f"Vdc_{safe_bus_name}"))
    #
    #     specs.append(ConnectionVarSpec("output", VarPowerFlowReferenceType.i_N, f"net_conn_{VarPowerFlowReferenceType.i_N.value}_{self.api_object.name}"))
    #     specs.append(ConnectionVarSpec("output", VarPowerFlowReferenceType.i_A, f"net_conn_{VarPowerFlowReferenceType.i_A.value}_{self.api_object.name}"))
    #     specs.append(ConnectionVarSpec("output", VarPowerFlowReferenceType.i_B, f"net_conn_{VarPowerFlowReferenceType.i_B.value}_{self.api_object.name}"))
    #     specs.append(ConnectionVarSpec("output", VarPowerFlowReferenceType.i_C, f"net_conn_{VarPowerFlowReferenceType.i_C.value}_{self.api_object.name}"))
    #     specs.append(ConnectionVarSpec("output", VarPowerFlowReferenceType.Idc, f"net_conn_{VarPowerFlowReferenceType.Idc.value}_{self.api_object.name}"))
    #
    #     return specs

    def _build_emt_injection_connection_specs(self) -> List[ConnectionVarSpec]:
        """
        Build the default editable EMT connection specs for an injection device.

        AC injections always open with the full N/A/B/C voltage-current
        interface. This is intentional because the editor must let the user
        decide which phases are actually needed.

        DC injections only expose the DC interface because a DC bus has no AC
        phase domain.

        :return: Connection variable specifications.
        """
        safe_bus_name: str = self._get_safe_bus_name(self.api_object.bus)
        specs: List[ConnectionVarSpec] = list()

        if self.api_object.bus.is_dc:
            # A DC injection has one voltage input and one injected current
            # output. No AC phase ports are valid for this bus domain.
            specs.append(ConnectionVarSpec("input", VarPowerFlowReferenceType.Vdc, f"Vdc_{safe_bus_name}"))
            specs.append(ConnectionVarSpec(
                "output",
                VarPowerFlowReferenceType.Idc,
                f"net_conn_{VarPowerFlowReferenceType.Idc.value}_{self.api_object.name}",
            ))
        else:
            # An AC injection starts with the complete editable phase set.
            # The user can remove phases, and the apply step will rebuild
            # the connected bus EMT shell from the remaining ports.
            specs.append(ConnectionVarSpec("input",
                                           VarPowerFlowReferenceType.v_N,
                                           f"v_N_{safe_bus_name}"))

            specs.append(ConnectionVarSpec("input",
                                           VarPowerFlowReferenceType.v_A,
                                           f"v_A_{safe_bus_name}"))

            specs.append(ConnectionVarSpec("input",
                                           VarPowerFlowReferenceType.v_B,
                                           f"v_B_{safe_bus_name}"))

            specs.append(ConnectionVarSpec("input",
                                           VarPowerFlowReferenceType.v_C,
                                           f"v_C_{safe_bus_name}"))

            specs.append(ConnectionVarSpec(
                "output",
                VarPowerFlowReferenceType.i_N,
                f"net_conn_{VarPowerFlowReferenceType.i_N.value}_{self.api_object.name}",
            ))
            specs.append(ConnectionVarSpec(
                "output",
                VarPowerFlowReferenceType.i_A,
                f"net_conn_{VarPowerFlowReferenceType.i_A.value}_{self.api_object.name}",
            ))
            specs.append(ConnectionVarSpec(
                "output",
                VarPowerFlowReferenceType.i_B,
                f"net_conn_{VarPowerFlowReferenceType.i_B.value}_{self.api_object.name}",
            ))
            specs.append(ConnectionVarSpec(
                "output",
                VarPowerFlowReferenceType.i_C,
                f"net_conn_{VarPowerFlowReferenceType.i_C.value}_{self.api_object.name}",
            ))

        return specs

    def _build_emt_branch_connection_specs(self) -> List[ConnectionVarSpec]:
        """
        Build EMT connection-variable specs for a branch device.

        Each terminal follows the same rule as injections: AC buses expose N/A/B/C,
        while DC buses expose only Vdc/Idc.

        :return: Connection variable specifications.
        """
        specs: List[ConnectionVarSpec] = list()

        self._append_emt_branch_side_connection_specs(
            specs=specs,
            bus=self.api_object.bus_from,
            side="from",
        )
        self._append_emt_branch_side_connection_specs(
            specs=specs,
            bus=self.api_object.bus_to,
            side="to",
        )

        return specs

    def build_emt_injection_current_refs(self, bus: Any) -> List[VarPowerFlowReferenceType]:
        """
        Return the ordered EMT current references that should be exposed for one injection device.

        :param bus: Bus API object.
        :return: EMT current references.
        """

        if bus.is_dc:
            current_refs: List[VarPowerFlowReferenceType] = list()
            current_refs.append(VarPowerFlowReferenceType.Idc)
            return current_refs
        else:
            voltage_pairs = self.get_injection_emt_voltage_pairs(bus)
            current_refs: List[VarPowerFlowReferenceType] = list()
            voltage_to_current_map: Dict[VarPowerFlowReferenceType, VarPowerFlowReferenceType] = dict()
            voltage_to_current_map[VarPowerFlowReferenceType.v_N] = VarPowerFlowReferenceType.i_N
            voltage_to_current_map[VarPowerFlowReferenceType.v_A] = VarPowerFlowReferenceType.i_A
            voltage_to_current_map[VarPowerFlowReferenceType.v_B] = VarPowerFlowReferenceType.i_B
            voltage_to_current_map[VarPowerFlowReferenceType.v_C] = VarPowerFlowReferenceType.i_C
            reference: VarPowerFlowReferenceType
            for reference, _ in voltage_pairs:
                mapped_reference = voltage_to_current_map.get(reference, None)
                if mapped_reference is not None:
                    current_refs.append(mapped_reference)
                else:
                    pass
            return current_refs

    def _build_emt_branch_current_refs(self,
                                       bus: Any,
                                       side: str,
                                       voltage_pairs: List[tuple[VarPowerFlowReferenceType, Any]]
                                       ) -> List[VarPowerFlowReferenceType]:
        """
        Return the ordered EMT branch-current references that should be exposed for one branch side.

        :param bus: Terminal bus.
        :param side: Branch side, either ``from`` or ``to``.
        :return: EMT branch current references.
        """

        if side == "from":
            voltage_to_current_map: Dict[VarPowerFlowReferenceType, VarPowerFlowReferenceType] = dict()
            voltage_to_current_map[VarPowerFlowReferenceType.vf_N] = VarPowerFlowReferenceType.if_N
            voltage_to_current_map[VarPowerFlowReferenceType.vf_A] = VarPowerFlowReferenceType.if_A
            voltage_to_current_map[VarPowerFlowReferenceType.vf_B] = VarPowerFlowReferenceType.if_B
            voltage_to_current_map[VarPowerFlowReferenceType.vf_C] = VarPowerFlowReferenceType.if_C
            voltage_to_current_map[VarPowerFlowReferenceType.Vdc] = VarPowerFlowReferenceType.Idc
        else:
            if side == "to":
                voltage_to_current_map = dict()
                voltage_to_current_map[VarPowerFlowReferenceType.vt_N] = VarPowerFlowReferenceType.it_N
                voltage_to_current_map[VarPowerFlowReferenceType.vt_A] = VarPowerFlowReferenceType.it_A
                voltage_to_current_map[VarPowerFlowReferenceType.vt_B] = VarPowerFlowReferenceType.it_B
                voltage_to_current_map[VarPowerFlowReferenceType.vt_C] = VarPowerFlowReferenceType.it_C
                voltage_to_current_map[VarPowerFlowReferenceType.Vdc] = VarPowerFlowReferenceType.Idc
            else:
                raise ValueError(f"Unsupported branch EMT side {side}")

        current_refs: List[VarPowerFlowReferenceType] = list()
        reference: VarPowerFlowReferenceType
        for reference, _ in voltage_pairs:
            mapped_reference = voltage_to_current_map.get(reference, None)
            if mapped_reference is not None:
                current_refs.append(mapped_reference)
            else:
                pass
        return current_refs

    def _get_safe_bus_name(self, bus: Any) -> str:
        """
        Build a safe bus-name suffix for editor-visible connection variables.

        :param bus: Bus API object.
        :return: Bus name with spaces replaced by underscores.
        """
        return bus.name.replace(" ", "_")

    def _get_current_root_interface_refs(self) -> set[VarPowerFlowReferenceType]:
        """
        Return the references still present in the saved root interface.

        The root block interface is the authoritative result of the editor
        session. When the user removes a visible connection variable, the
        corresponding variable disappears from ``main_block.in_vars`` or
        ``main_block.out_vars`` and should not be recreated silently later.

        :return: Set of power-flow reference types still exposed by the block.
        """
        refs: set[VarPowerFlowReferenceType] = set()
        var: Var
        mapping_ref: VarPowerFlowReferenceType
        mapped_var: Var | None

        # Collect references from explicit root inputs.
        for var in self.main_block.in_vars:
            if var.ref is not None:
                refs.add(var.ref)
            else:
                pass

        # Collect references from explicit root outputs.
        for var in self.main_block.out_vars:
            if var.ref is not None:
                refs.add(var.ref)
            else:
                pass

        # Collect references from the external mapping because some variables
        # may be kept through mapping updates after connection edits.
        for mapping_ref, mapped_var in self.main_block.external_mapping.items():
            if mapped_var is not None:
                refs.add(mapping_ref)
            else:
                pass

        return refs

    def _is_interface_block_port_connected(self, item: ProtectedConnectionBlockItem) -> bool:
        """
        Return whether one protected editor interface block owns a live wire.

        The protected interface blocks are always present in EMT mode, so the
        algorithm cannot use block existence anymore to infer whether one phase
        participates in the model. The only valid signal is whether the block's
        single public port currently owns at least one connection item.

        :param item: Protected connection-interface block.
        :return: ``True`` when the visible interface port is wired.
        """
        node_data: Any | None = None
        is_connected: bool = False
        port_item: PortItem | None = None

        if item.subsys is not None:
            node_data = self.diagram.node_data.get(item.subsys.uid, None)
        else:
            node_data = None

        if node_data is not None:
            if node_data.tpe == BlockType.INPUT_CONN.name:
                if len(item.outputs) > 0:
                    port_item = item.outputs[0]
                else:
                    port_item = None
            else:
                if node_data.tpe == BlockType.OUTPUT_CONN.name:
                    if len(item.inputs) > 0:
                        port_item = item.inputs[0]
                    else:
                        port_item = None
                else:
                    port_item = None
        else:
            port_item = None

        if port_item is not None:
            if port_item.connections is not None:
                if len(port_item.connections) > 0:
                    is_connected = True
                else:
                    is_connected = False
            else:
                is_connected = False
        else:
            is_connected = False

        return is_connected

    def _get_connected_root_interface_refs(self) -> set[VarPowerFlowReferenceType]:
        """
        Return the root interface references backed by live editor connections.

        EMT interface blocks are now protected from deletion, so all candidate
        phase blocks always exist on the canvas. To rebuild the EMT bus shells
        correctly, the algorithm must inspect which interface ports are actually
        wired into the model and use only those references as active phases.

        :return: Connected root-interface references.
        """
        refs: set[VarPowerFlowReferenceType] = set()
        scene_item: QGraphicsItem
        protected_item: ProtectedConnectionBlockItem
        node_data: Any | None = None
        reference_var: Var | None = None

        for scene_item in self.scene.items():
            if isinstance(scene_item, ProtectedConnectionBlockItem):
                protected_item = scene_item
                if protected_item.subsys is not None:
                    node_data = self.diagram.node_data.get(protected_item.subsys.uid, None)
                else:
                    node_data = None

                if node_data is not None:
                    if self._is_interface_block_port_connected(protected_item):
                        if node_data.tpe == BlockType.INPUT_CONN.name:
                            if len(protected_item.subsys.out_vars) > 0:
                                reference_var = protected_item.subsys.out_vars[0]
                            else:
                                reference_var = None
                        else:
                            if node_data.tpe == BlockType.OUTPUT_CONN.name:
                                if len(protected_item.subsys.in_vars) > 0:
                                    reference_var = protected_item.subsys.in_vars[0]
                                else:
                                    reference_var = None
                            else:
                                reference_var = None

                        if reference_var is not None:
                            if reference_var.ref is not None:
                                refs.add(reference_var.ref)
                            else:
                                pass
                        else:
                            pass
                    else:
                        pass
                else:
                    pass
            else:
                pass

        return refs

    def _show_inconsistent_emt_phase_modal(self, phase_labels: list[str]) -> None:
        """
        Show one warning modal describing incomplete EMT phase pairs.

        A phase with only voltage or only current connected cannot be assembled
        into a valid network interface. The user must fix the mismatch before the
        EMT bus shell and DAE are rebuilt.

        :param phase_labels: Human-readable phase labels that are inconsistent.
        :return: None.
        """
        phase_text: str = ", ".join(phase_labels)

        QtWidgets.QMessageBox.warning(
            self,
            "Inconsistent EMT interface",
            (
                "The dynamic model is inconsistent because some EMT phases have only voltage or only current "
                f"connected: {phase_text}.\n\n"
                "Connect both V and I for each active phase, or disconnect both sides of the phase."
            ),
        )

    def _prune_disconnected_emt_root_interface(self) -> None:
        """
        Remove disconnected EMT root-interface references before saving the model.

        The protected connection-interface blocks always exist on the canvas, but
        the persisted device model must only expose the EMT references that are
        actually wired into the user model. Otherwise the simulation builder sees
        stale external mappings that no longer match the rebuilt EMT bus shells.

        :return: None.
        """
        connected_refs: set[VarPowerFlowReferenceType] = self._get_connected_root_interface_refs()
        kept_in_vars: list[Var] = list()
        kept_out_vars: list[Var] = list()
        var: Var
        mapping_key: VarPowerFlowReferenceType
        mapped_var: Var | None
        mapping_keys_to_remove: list[VarPowerFlowReferenceType] = list()

        # Keep only input variables whose EMT reference is still wired in the
        # editor. Non-interface variables or RMS/DC references are left intact.
        for var in self.main_block.in_vars:
            if self._is_emt_interface_reference(var.ref):
                if var.ref in connected_refs:
                    kept_in_vars.append(var)
                else:
                    pass
            else:
                kept_in_vars.append(var)

        # Keep only output variables whose EMT reference is still wired in the
        # editor. This synchronizes the saved block interface with the bus mask.
        for var in self.main_block.out_vars:
            if self._is_emt_interface_reference(var.ref):
                if var.ref in connected_refs:
                    kept_out_vars.append(var)
                else:
                    pass
            else:
                kept_out_vars.append(var)

        self.main_block.in_vars = kept_in_vars
        self.main_block.out_vars = kept_out_vars

        # Remove stale external mappings that still reference disconnected EMT
        # ports. The simulation validator reads this mapping directly.
        for mapping_key, mapped_var in self.main_block.external_mapping.items():
            if self._is_emt_interface_reference(mapping_key):
                if mapping_key in connected_refs:
                    pass
                else:
                    mapping_keys_to_remove.append(mapping_key)
            else:
                pass

        for mapping_key in mapping_keys_to_remove:
            del self.main_block.external_mapping[mapping_key]

    def _is_emt_interface_reference(self, reference: VarPowerFlowReferenceType | None) -> bool:
        """
        Return whether one reference belongs to the EMT AC editor interface.

        The pruning step must only touch EMT phase-interface variables. Other
        references, such as RMS quantities, DC quantities, parameters, or user
        internals, must remain untouched when the editor applies the model.

        :param reference: Reference carried by one root-interface variable.
        :return: ``True`` when the reference is one EMT AC interface key.
        """
        emt_interface_refs: set[VarPowerFlowReferenceType] = set()
        is_interface_reference: bool = False

        emt_interface_refs.add(VarPowerFlowReferenceType.v_N)
        emt_interface_refs.add(VarPowerFlowReferenceType.v_A)
        emt_interface_refs.add(VarPowerFlowReferenceType.v_B)
        emt_interface_refs.add(VarPowerFlowReferenceType.v_C)
        emt_interface_refs.add(VarPowerFlowReferenceType.i_N)
        emt_interface_refs.add(VarPowerFlowReferenceType.i_A)
        emt_interface_refs.add(VarPowerFlowReferenceType.i_B)
        emt_interface_refs.add(VarPowerFlowReferenceType.i_C)
        emt_interface_refs.add(VarPowerFlowReferenceType.vf_N)
        emt_interface_refs.add(VarPowerFlowReferenceType.vf_A)
        emt_interface_refs.add(VarPowerFlowReferenceType.vf_B)
        emt_interface_refs.add(VarPowerFlowReferenceType.vf_C)
        emt_interface_refs.add(VarPowerFlowReferenceType.if_N)
        emt_interface_refs.add(VarPowerFlowReferenceType.if_A)
        emt_interface_refs.add(VarPowerFlowReferenceType.if_B)
        emt_interface_refs.add(VarPowerFlowReferenceType.if_C)
        emt_interface_refs.add(VarPowerFlowReferenceType.vt_N)
        emt_interface_refs.add(VarPowerFlowReferenceType.vt_A)
        emt_interface_refs.add(VarPowerFlowReferenceType.vt_B)
        emt_interface_refs.add(VarPowerFlowReferenceType.vt_C)
        emt_interface_refs.add(VarPowerFlowReferenceType.it_N)
        emt_interface_refs.add(VarPowerFlowReferenceType.it_A)
        emt_interface_refs.add(VarPowerFlowReferenceType.it_B)
        emt_interface_refs.add(VarPowerFlowReferenceType.it_C)

        if reference is not None:
            if reference in emt_interface_refs:
                is_interface_reference = True
            else:
                is_interface_reference = False
        else:
            is_interface_reference = False

        return is_interface_reference

    def _build_connected_emt_injection_bus_mask(self) -> list[bool] | None:
        """
        Build the EMT injection bus mask from actual editor connectivity.

        The algorithm checks each phase pair explicitly. A phase is kept only
        when both the voltage and current interface blocks are connected. If only
        one side is connected, the model is inconsistent and the rebuild must
        stop so the user can resolve the mismatch.

        :return: Connected EMT mask, or ``None`` when one phase pair is inconsistent.
        """
        refs: set[VarPowerFlowReferenceType] = self._get_connected_root_interface_refs()
        mask: list[bool] = list([False, False, False, False])
        inconsistent_phase_labels: list[str] = list()
        neutral_voltage_connected: bool = VarPowerFlowReferenceType.v_N in refs
        neutral_current_connected: bool = VarPowerFlowReferenceType.i_N in refs
        phase_a_voltage_connected: bool = VarPowerFlowReferenceType.v_A in refs
        phase_a_current_connected: bool = VarPowerFlowReferenceType.i_A in refs
        phase_b_voltage_connected: bool = VarPowerFlowReferenceType.v_B in refs
        phase_b_current_connected: bool = VarPowerFlowReferenceType.i_B in refs
        phase_c_voltage_connected: bool = VarPowerFlowReferenceType.v_C in refs
        phase_c_current_connected: bool = VarPowerFlowReferenceType.i_C in refs

        if neutral_voltage_connected == neutral_current_connected:
            mask[0]: bool = neutral_voltage_connected and neutral_current_connected
        else:
            inconsistent_phase_labels.append("N")

        if phase_a_voltage_connected == phase_a_current_connected:
            mask[1]: bool = phase_a_voltage_connected and phase_a_current_connected
        else:
            inconsistent_phase_labels.append("A")

        if phase_b_voltage_connected == phase_b_current_connected:
            mask[2]: bool = phase_b_voltage_connected and phase_b_current_connected
        else:
            inconsistent_phase_labels.append("B")

        if phase_c_voltage_connected == phase_c_current_connected:
            mask[3]: bool = phase_c_voltage_connected and phase_c_current_connected
        else:
            inconsistent_phase_labels.append("C")

        if len(inconsistent_phase_labels) > 0:
            self._show_inconsistent_emt_phase_modal(inconsistent_phase_labels)
            return None
        else:
            return mask

    def _build_connected_emt_branch_bus_mask(self, side: str) -> list[bool] | None:
        """
        Build one EMT branch-side mask from actual editor connectivity.

        The branch editor exposes two independent side interfaces. Each side must
        therefore validate its voltage/current phase pairs independently before
        the matching bus shell can be rebuilt.

        :param side: Branch side identifier. Expected values are ``from`` and ``to``.
        :return: Connected EMT mask for the requested side, or ``None`` on inconsistency.
        """
        refs: set[VarPowerFlowReferenceType] = self._get_connected_root_interface_refs()
        mask: list[bool] = list([False, False, False, False])
        inconsistent_phase_labels: list[str] = list()
        side_label: str = ""

        if side == "from":
            side_label = "from"
            neutral_voltage_connected: bool = VarPowerFlowReferenceType.vf_N in refs
            neutral_current_connected: bool = VarPowerFlowReferenceType.if_N in refs
            phase_a_voltage_connected: bool = VarPowerFlowReferenceType.vf_A in refs
            phase_a_current_connected: bool = VarPowerFlowReferenceType.if_A in refs
            phase_b_voltage_connected: bool = VarPowerFlowReferenceType.vf_B in refs
            phase_b_current_connected: bool = VarPowerFlowReferenceType.if_B in refs
            phase_c_voltage_connected: bool = VarPowerFlowReferenceType.vf_C in refs
            phase_c_current_connected: bool = VarPowerFlowReferenceType.if_C in refs
        else:
            if side == "to":
                side_label = "to"
                neutral_voltage_connected = VarPowerFlowReferenceType.vt_N in refs
                neutral_current_connected = VarPowerFlowReferenceType.it_N in refs
                phase_a_voltage_connected = VarPowerFlowReferenceType.vt_A in refs
                phase_a_current_connected = VarPowerFlowReferenceType.it_A in refs
                phase_b_voltage_connected = VarPowerFlowReferenceType.vt_B in refs
                phase_b_current_connected = VarPowerFlowReferenceType.it_B in refs
                phase_c_voltage_connected = VarPowerFlowReferenceType.vt_C in refs
                phase_c_current_connected = VarPowerFlowReferenceType.it_C in refs
            else:
                return None

        if neutral_voltage_connected == neutral_current_connected:
            mask[0]: bool = neutral_voltage_connected and neutral_current_connected
        else:
            inconsistent_phase_labels.append(f"{side_label}:N")

        if phase_a_voltage_connected == phase_a_current_connected:
            mask[1]: bool = phase_a_voltage_connected and phase_a_current_connected
        else:
            inconsistent_phase_labels.append(f"{side_label}:A")

        if phase_b_voltage_connected == phase_b_current_connected:
            mask[2]: bool = phase_b_voltage_connected and phase_b_current_connected
        else:
            inconsistent_phase_labels.append(f"{side_label}:B")

        if phase_c_voltage_connected == phase_c_current_connected:
            mask[3]: bool = phase_c_voltage_connected and phase_c_current_connected
        else:
            inconsistent_phase_labels.append(f"{side_label}:C")

        if len(inconsistent_phase_labels) > 0:
            self._show_inconsistent_emt_phase_modal(inconsistent_phase_labels)
            return None
        else:
            return mask

    def _get_requested_emt_bus_masks_from_current_interface(self) -> tuple[
        bool, list[bool] | None, list[bool] | None, list[bool] | None]:
        """
        Build the requested EMT bus masks from the currently connected editor ports.

        The editor path is the source of truth for which EMT phases the user
        kept connected. Once these masks are known, the actual bus-shell
        creation, expansion, reconnection, and registry update are delegated to
        the shared engine-side attachment flow.

        :return: Tuple ``(success, bus_mask, from_mask, to_mask)``.
        """
        success: bool = True
        bus_mask: list[bool] | None = None
        from_mask: list[bool] | None = None
        to_mask: list[bool] | None = None

        if isinstance(self.api_object, InjectionParent):
            if self.api_object.bus.is_dc:
                bus_mask = list([False, False, False, False])
            else:
                bus_mask = self._build_connected_emt_injection_bus_mask()
                if bus_mask is None:
                    success = False
                else:
                    if any(bus_mask):
                        pass
                    else:
                        QtWidgets.QMessageBox.warning(
                            self,
                            "Invalid EMT bus interface",
                            f"The EMT interface for bus '{self.api_object.bus.name}' has no remaining AC phases. "
                            "Keep at least one voltage or current phase port before applying changes.",
                        )
                        success = False
        else:
            if isinstance(self.api_object, BranchParent):
                if self.api_object.bus_from.is_dc:
                    from_mask = list([False, False, False, False])
                else:
                    from_mask = self._build_connected_emt_branch_bus_mask(side="from")
                    if from_mask is None:
                        success = False
                    else:
                        if any(from_mask):
                            pass
                        else:
                            QtWidgets.QMessageBox.warning(
                                self,
                                "Invalid EMT bus interface",
                                f"The EMT interface for bus '{self.api_object.bus_from.name}' has no remaining AC phases. "
                                "Keep at least one voltage or current phase port before applying changes.",
                            )
                            success = False

                if self.api_object.bus_to.is_dc:
                    to_mask = list([False, False, False, False])
                else:
                    to_mask = self._build_connected_emt_branch_bus_mask(side="to")
                    if to_mask is None:
                        success = False
                    else:
                        if any(to_mask):
                            pass
                        else:
                            QtWidgets.QMessageBox.warning(
                                self,
                                "Invalid EMT bus interface",
                                f"The EMT interface for bus '{self.api_object.bus_to.name}' has no remaining AC phases. "
                                "Keep at least one voltage or current phase port before applying changes.",
                            )
                            success = False
            else:
                success = True

        return success, bus_mask, from_mask, to_mask

    def _build_default_editor_emt_connection_specs(self) -> List[ConnectionVarSpec]:
        """
        Return the full editable EMT interface expected by the editor.

        Unlike the saved EMT model root contract, this editor contract always
        includes every potentially editable connection block for the host device
        so reopening the editor never hides ports that the user may want to wire
        later.

        :return: Full editor EMT connection specs.
        """
        if isinstance(self.api_object, BranchParent):
            return self._build_emt_branch_connection_specs()
        elif isinstance(self.api_object, InjectionParent):
            return self._build_emt_injection_connection_specs()
        else:
            return list()

    def _ensure_full_emt_editor_interface(self) -> None:
        """
        Expand one reopened EMT main editor to the full editable root interface.

        Template-assigned EMT models may save only the currently connected root
        ports in ``in_vars``/``out_vars`` and in the saved diagram. The editor,
        however, must always reopen with the complete editable connection-block
        set so users can connect additional phases later.

        :return: None.
        """
        if not self.main_editor or self.mode != DynamicSimulationMode.EMT:
            return
        else:
            pass

        full_specs: List[ConnectionVarSpec] = self._build_default_editor_emt_connection_specs()
        if len(full_specs) == 0:
            return
        else:
            pass

        existing_input_by_ref: Dict[VarPowerFlowReferenceType, Var] = dict()
        existing_output_by_ref: Dict[VarPowerFlowReferenceType, Var] = dict()
        var: Var

        for var in self.main_block.in_vars:
            if isinstance(var.ref, VarPowerFlowReferenceType):
                existing_input_by_ref[var.ref] = var
            else:
                pass

        for var in self.main_block.out_vars:
            if isinstance(var.ref, VarPowerFlowReferenceType):
                existing_output_by_ref[var.ref] = var
            else:
                pass

        # Rebuild the root interface in the editor-default order while preserving
        # existing symbolic objects for already-saved ports and creating only the
        # missing editor ports.
        rebuilt_in_vars: list[Var] = list()
        rebuilt_out_vars: list[Var] = list()
        spec: ConnectionVarSpec
        reused_var: Var | None

        for spec in full_specs:
            reused_var = None
            if spec.direction == "input":
                reused_var = existing_input_by_ref.get(spec.reference, None)
                if reused_var is None:
                    reused_var = self.var_factory.add_var(spec.visible_name, spec.reference, True)
                else:
                    reused_var.name = spec.visible_name
                rebuilt_in_vars.append(reused_var)
            elif spec.direction == "output":
                reused_var = existing_output_by_ref.get(spec.reference, None)
                if reused_var is None:
                    reused_var = self.var_factory.add_var(spec.visible_name, spec.reference, True)
                else:
                    reused_var.name = spec.visible_name
                rebuilt_out_vars.append(reused_var)
            else:
                raise ValueError(f"Unsupported EMT editor connection direction {spec.direction}")

            self.main_block.external_mapping[spec.reference] = reused_var

        self.main_block.in_vars = rebuilt_in_vars
        self.main_block.out_vars = rebuilt_out_vars

        block_lookup_before: Dict[int, Block] = _build_block_uid_lookup(self.main_block)
        orphan_node_uids: list[int] = list()
        node_uid: int
        node: Any
        mapped_block: Block | None
        reference_var: Var | None

        for node_uid, node in list(self.diagram.node_data.items()):
            if node.tpe in {BlockType.INPUT_CONN.name, BlockType.OUTPUT_CONN.name}:
                mapped_block = block_lookup_before.get(node.device_uid, None)
                if mapped_block is not None:
                    if node.tpe == BlockType.INPUT_CONN.name and len(mapped_block.out_vars) > 0:
                        reference_var = mapped_block.out_vars[0]
                    elif node.tpe == BlockType.OUTPUT_CONN.name and len(mapped_block.in_vars) > 0:
                        reference_var = mapped_block.in_vars[0]
                    else:
                        reference_var = None

                    if reference_var is None or not isinstance(reference_var.ref, VarPowerFlowReferenceType):
                        orphan_node_uids.append(node_uid)
                    else:
                        pass
                else:
                    orphan_node_uids.append(node_uid)
            else:
                pass

        original_node_count: int = len(self.diagram.node_data)

        for node_uid in orphan_node_uids:
            if node_uid in self.diagram.node_data:
                del self.diagram.node_data[node_uid]
            else:
                pass

        # Recreate the full connection-block graph so every editable EMT port is
        # visible even when the saved model was created through template setter.
        self._remove_existing_connection_interface_blocks_from_main_block()
        self.add_connection_items()

        # Template-assigned EMT models may arrive without any saved diagram at
        # all. After the interface rebuild, materialize the edited model blocks
        # themselves so the canvas still shows the actual symbolic subsystem.
        if original_node_count == 0:
            self._materialize_missing_non_interface_diagram_nodes()
            self._rebuild_missing_non_interface_connections()
        else:
            pass

    def _remove_existing_connection_interface_blocks_from_main_block(self) -> None:
        """
        Remove transient editor interface wrapper blocks from ``main_block``.

        The editor rebuilds those wrapper blocks from the current root interface,
        so any stale saved wrappers must be removed from the working hierarchy
        first to keep the scene and symbolic state aligned.

        :return: None.
        """
        kept_children: list[Block] = list()
        child_block: Block
        block_type: BlockType | None

        for child_block in self.main_block.children:
            block_type = None
            if child_block.uid in self.diagram.node_data:
                node_type_name: str = self.diagram.node_data[child_block.uid].tpe
                if node_type_name in BlockType.__members__:
                    block_type = BlockType[node_type_name]
                else:
                    pass
            else:
                pass

            if block_type in {BlockType.INPUT_CONN, BlockType.OUTPUT_CONN}:
                pass
            else:
                kept_children.append(child_block)

        self.main_block.children = kept_children

    def _materialize_missing_non_interface_diagram_nodes(self) -> None:
        """
        Add default diagram nodes for non-interface blocks missing from the diagram.

        Template-assigned models can exist as symbolic children without any saved
        diagram node positions. The editor must create those missing diagram
        nodes so the symbolic blocks become visible on the canvas.

        :return: None.
        """
        existing_node_uids: set[int] = set(self.diagram.node_data.keys())
        child_block: Block

        for child_block in self.main_block.children:
            if child_block.uid in existing_node_uids:
                pass
            elif len(child_block.in_vars) == 1 and len(child_block.out_vars) == 0 and child_block.name.startswith(
                    "net_conn_"):
                # Defensive guard for editor-generated output interface wrappers.
                pass
            elif len(child_block.in_vars) == 0 and len(child_block.out_vars) == 1 and child_block.name.startswith(
                    ("v_", "Vdc_")):
                # Defensive guard for editor-generated input interface wrappers.
                pass
            else:
                self.generate_block_item_for_block(child_block)

    def _rebuild_missing_non_interface_connections(self) -> None:
        """
        Recreate inferred symbolic wires after auto-materializing missing blocks.

        The no-diagram template-open path must rebuild the visible connection set
        from the symbolic graph once the missing block nodes have been placed.

        :return: None.
        """
        items_list: list[GenericBlockItem] = self._collect_non_interface_scene_items()

        if len(items_list) > 0:
            self.connect_items(items_list)
            self._rebuild_editor_interface_graphical_connections(items_list)
        else:
            pass

    def _collect_non_interface_scene_items(self) -> list[GenericBlockItem]:
        """
        Return the visible non-interface generic block items in the scene.

        The reconnect pass operates only on real model blocks. The protected
        editor interface wrappers are intentionally excluded from this list.

        :return: Generic block items excluding editor interface wrappers.
        """
        items_list: list[GenericBlockItem] = list()
        scene_item: QGraphicsItem
        node_data: Any | None

        for scene_item in self.scene.items():
            if isinstance(scene_item, GenericBlockItem):
                if scene_item.subsys is not None:
                    node_data: Any | None = self.diagram.node_data.get(scene_item.subsys.uid, None)
                else:
                    node_data = None

                if node_data is None:
                    pass
                elif node_data.tpe in {BlockType.INPUT_CONN.name, BlockType.OUTPUT_CONN.name}:
                    pass
                else:
                    items_list.append(scene_item)
            else:
                pass

        return items_list

    def _rebuild_visible_symbolic_connections(self, items_list: List[GenericBlockItem]) -> None:
        """
        Recreate missing symbolic wires between all visible non-interface blocks.

        The saved diagram may miss some graphical arrows even when the symbolic
        block graph still carries enough metadata to infer them. Re-run the
        visible block-pair connection discovery so the scene reflects the actual
        symbolic connectivity.

        :param items_list: Visible non-interface block items.
        :return: None.
        """
        item_source: GenericBlockItem
        item_target: GenericBlockItem
        pairs: list[tuple[Var, Var]]
        power_flow_pairs: list[tuple[Var, Var]]

        for item_source in items_list:
            if item_source.subsys is None:
                pass
            else:
                for item_target in items_list:
                    if item_target.subsys is None:
                        pass
                    else:
                        if item_source.subsys.uid == item_target.subsys.uid:
                            pass
                        else:
                            pairs, power_flow_pairs = find_connections(item_source.subsys, item_target.subsys)
                            self._create_missing_connection_items(item_source, item_target, pairs)
                            self._create_missing_connection_items(item_source, item_target, power_flow_pairs)

    def _rebuild_editor_interface_graphical_connections(self, items_list: List[GenericBlockItem]) -> None:
        """
        Recreate visible wires between editor interface blocks and visible model blocks.

        EMT template-open sessions can rebuild the full editor interface without a
        saved diagram that already contains those graphical wires. The root block
        still carries the semantic ``ref`` tags, so reconnect the visible editor
        interface to every visible block port that exposes the same EMT root ref.

        :param items_list: Visible non-interface block items.
        :return: None.
        """
        interface_inputs_by_ref: Dict[VarPowerFlowReferenceType, ProtectedConnectionBlockItem] = dict()
        interface_outputs_by_ref: Dict[VarPowerFlowReferenceType, ProtectedConnectionBlockItem] = dict()
        scene_item: QGraphicsItem
        node_data: Any | None
        reference_var: Var | None
        block_item: GenericBlockItem
        input_index: int
        output_index: int
        input_var: Var
        output_var: Var
        protected_item: ProtectedConnectionBlockItem | None

        for scene_item in self.scene.items():
            if isinstance(scene_item, ProtectedConnectionBlockItem) and scene_item.subsys is not None:
                node_data = self.diagram.node_data.get(scene_item.subsys.uid, None)

                if node_data is None:
                    pass
                elif node_data.tpe == BlockType.INPUT_CONN.name:
                    if len(scene_item.subsys.out_vars) > 0:
                        reference_var = scene_item.subsys.out_vars[0]
                    else:
                        reference_var = None

                    if isinstance(reference_var, Var) and isinstance(reference_var.ref, VarPowerFlowReferenceType):
                        interface_inputs_by_ref[reference_var.ref] = scene_item
                    else:
                        pass
                elif node_data.tpe == BlockType.OUTPUT_CONN.name:
                    if len(scene_item.subsys.in_vars) > 0:
                        reference_var = scene_item.subsys.in_vars[0]
                    else:
                        reference_var = None

                    if isinstance(reference_var, Var) and isinstance(reference_var.ref, VarPowerFlowReferenceType):
                        interface_outputs_by_ref[reference_var.ref] = scene_item
                    else:
                        pass
                else:
                    pass
            else:
                pass

        for block_item in items_list:
            if block_item.subsys is None:
                pass
            else:
                for input_index, input_var in enumerate(block_item.subsys.in_vars):
                    if isinstance(input_var.ref, VarPowerFlowReferenceType):
                        protected_item = self._get_editor_interface_input_item_for_ref(
                            interface_inputs_by_ref=interface_inputs_by_ref,
                            model_ref=input_var.ref,
                        )
                        if protected_item is not None and len(protected_item.outputs) > 0 and input_index < len(
                                block_item.inputs):
                            if self._connection_exists_between_ports(protected_item.outputs[0],
                                                                     block_item.inputs[input_index]):
                                pass
                            else:
                                connection_item: ConnectionItem = ConnectionItem(
                                    source_port=protected_item.outputs[0],
                                    target_port=block_item.inputs[input_index],
                                    diagram=self.diagram,
                                    editor=self,
                                )
                                self.scene.addItem(connection_item)
                        else:
                            pass
                    else:
                        pass

                for output_index, output_var in enumerate(block_item.subsys.out_vars):
                    if isinstance(output_var.ref, VarPowerFlowReferenceType):
                        protected_item = self._get_editor_interface_output_item_for_ref(
                            interface_outputs_by_ref=interface_outputs_by_ref,
                            model_ref=output_var.ref,
                        )
                        if protected_item is not None and len(protected_item.inputs) > 0 and output_index < len(
                                block_item.outputs):
                            if self._connection_exists_between_ports(block_item.outputs[output_index],
                                                                     protected_item.inputs[0]):
                                pass
                            else:
                                connection_item = ConnectionItem(
                                    source_port=block_item.outputs[output_index],
                                    target_port=protected_item.inputs[0],
                                    diagram=self.diagram,
                                    editor=self,
                                )
                                self.scene.addItem(connection_item)
                        else:
                            pass
                    else:
                        pass

    def _get_editor_interface_input_item_for_ref(self,
                                                 interface_inputs_by_ref: Dict[
                                                     VarPowerFlowReferenceType, ProtectedConnectionBlockItem],
                                                 model_ref: VarPowerFlowReferenceType) -> ProtectedConnectionBlockItem | None:
        """
        Resolve one editor input wrapper for one model-side EMT input reference.

        :param interface_inputs_by_ref: Editor input wrappers keyed by editor EMT ref.
        :param model_ref: Model-side EMT input ref.
        :return: Matching editor input wrapper or ``None``.
        """
        if isinstance(self.api_object, BranchParent) and self.api_object.device_type == DeviceType.VscDevice:
            ac_side_is_from: bool = False
            ac_side_is_to: bool = False

            if self.api_object.bus_from.is_dc:
                ac_side_is_to = True
            else:
                if self.api_object.bus_to.is_dc:
                    ac_side_is_from = True
                else:
                    ac_side_is_from = True

            if model_ref == VarPowerFlowReferenceType.v_N:
                if ac_side_is_to:
                    return interface_inputs_by_ref.get(VarPowerFlowReferenceType.vt_N, None)
                elif ac_side_is_from:
                    return interface_inputs_by_ref.get(VarPowerFlowReferenceType.vf_N, None)
                else:
                    return interface_inputs_by_ref.get(VarPowerFlowReferenceType.vf_N, None)
            elif model_ref == VarPowerFlowReferenceType.v_A:
                if ac_side_is_to:
                    return interface_inputs_by_ref.get(VarPowerFlowReferenceType.vt_A, None)
                elif ac_side_is_from:
                    return interface_inputs_by_ref.get(VarPowerFlowReferenceType.vf_A, None)
                else:
                    return interface_inputs_by_ref.get(VarPowerFlowReferenceType.vf_A, None)
            elif model_ref == VarPowerFlowReferenceType.v_B:
                if ac_side_is_to:
                    return interface_inputs_by_ref.get(VarPowerFlowReferenceType.vt_B, None)
                elif ac_side_is_from:
                    return interface_inputs_by_ref.get(VarPowerFlowReferenceType.vf_B, None)
                else:
                    return interface_inputs_by_ref.get(VarPowerFlowReferenceType.vf_B, None)
            elif model_ref == VarPowerFlowReferenceType.v_C:
                if ac_side_is_to:
                    return interface_inputs_by_ref.get(VarPowerFlowReferenceType.vt_C, None)
                elif ac_side_is_from:
                    return interface_inputs_by_ref.get(VarPowerFlowReferenceType.vf_C, None)
                else:
                    return interface_inputs_by_ref.get(VarPowerFlowReferenceType.vf_C, None)
            elif model_ref == VarPowerFlowReferenceType.Vdc:
                if self.api_object.bus_from.is_dc:
                    return interface_inputs_by_ref.get(VarPowerFlowReferenceType.Vf_dc, None)
                elif self.api_object.bus_to.is_dc:
                    return interface_inputs_by_ref.get(VarPowerFlowReferenceType.Vt_dc, None)
                else:
                    return interface_inputs_by_ref.get(VarPowerFlowReferenceType.Vdc, None)
            else:
                return interface_inputs_by_ref.get(model_ref, None)
        else:
            return interface_inputs_by_ref.get(model_ref, None)

    def _get_editor_interface_output_item_for_ref(self,
                                                  interface_outputs_by_ref: Dict[
                                                      VarPowerFlowReferenceType, ProtectedConnectionBlockItem],
                                                  model_ref: VarPowerFlowReferenceType) -> ProtectedConnectionBlockItem | None:
        """
        Resolve one editor output wrapper for one model-side EMT output reference.

        :param interface_outputs_by_ref: Editor output wrappers keyed by editor EMT ref.
        :param model_ref: Model-side EMT output ref.
        :return: Matching editor output wrapper or ``None``.
        """
        if isinstance(self.api_object, BranchParent) and self.api_object.device_type == DeviceType.VscDevice:
            ac_side_is_from: bool = False
            ac_side_is_to: bool = False

            if self.api_object.bus_from.is_dc:
                ac_side_is_to = True
            else:
                if self.api_object.bus_to.is_dc:
                    ac_side_is_from = True
                else:
                    ac_side_is_from = True

            if model_ref == VarPowerFlowReferenceType.i_N:
                if ac_side_is_to:
                    return interface_outputs_by_ref.get(VarPowerFlowReferenceType.it_N, None)
                elif ac_side_is_from:
                    return interface_outputs_by_ref.get(VarPowerFlowReferenceType.if_N, None)
                else:
                    return interface_outputs_by_ref.get(VarPowerFlowReferenceType.if_N, None)
            elif model_ref == VarPowerFlowReferenceType.i_A:
                if ac_side_is_to:
                    return interface_outputs_by_ref.get(VarPowerFlowReferenceType.it_A, None)
                elif ac_side_is_from:
                    return interface_outputs_by_ref.get(VarPowerFlowReferenceType.if_A, None)
                else:
                    return interface_outputs_by_ref.get(VarPowerFlowReferenceType.if_A, None)
            elif model_ref == VarPowerFlowReferenceType.i_B:
                if ac_side_is_to:
                    return interface_outputs_by_ref.get(VarPowerFlowReferenceType.it_B, None)
                elif ac_side_is_from:
                    return interface_outputs_by_ref.get(VarPowerFlowReferenceType.if_B, None)
                else:
                    return interface_outputs_by_ref.get(VarPowerFlowReferenceType.if_B, None)
            elif model_ref == VarPowerFlowReferenceType.i_C:
                if ac_side_is_to:
                    return interface_outputs_by_ref.get(VarPowerFlowReferenceType.it_C, None)
                elif ac_side_is_from:
                    return interface_outputs_by_ref.get(VarPowerFlowReferenceType.if_C, None)
                else:
                    return interface_outputs_by_ref.get(VarPowerFlowReferenceType.if_C, None)
            elif model_ref == VarPowerFlowReferenceType.Idc:
                if self.api_object.bus_from.is_dc:
                    return interface_outputs_by_ref.get(VarPowerFlowReferenceType.If_dc, None)
                elif self.api_object.bus_to.is_dc:
                    return interface_outputs_by_ref.get(VarPowerFlowReferenceType.It_dc, None)
                else:
                    return interface_outputs_by_ref.get(VarPowerFlowReferenceType.Idc, None)
            else:
                return interface_outputs_by_ref.get(model_ref, None)
        else:
            return interface_outputs_by_ref.get(model_ref, None)

    def _create_missing_connection_items(self,
                                         item_source: GenericBlockItem,
                                         item_dest: GenericBlockItem,
                                         pairs: List[tuple[Var, Var]]) -> None:
        """
        Create only the currently missing connection items for one block pair.

        :param item_source: Source block item.
        :param item_dest: Destination block item.
        :param pairs: Candidate variable pairs.
        :return: None.
        """
        source_var: Var
        target_var: Var
        source_port: PortItem | None
        target_port: PortItem | None
        port: PortItem

        for source_var, target_var in pairs:
            source_port = self._find_output_port_for_var(item_source=item_source, source_var=source_var)
            target_port = self._find_input_port_for_var(item_dest=item_dest, target_var=target_var)

            if source_port is not None and target_port is not None:
                if self._connection_exists_between_ports(source_port, target_port):
                    pass
                else:
                    connection = ConnectionItem(
                        source_port=source_port,
                        target_port=target_port,
                        diagram=self.diagram,
                        editor=self,
                    )
                    self.scene.addItem(connection)
            else:
                pass

    @staticmethod
    def _vars_match_for_visible_connection(left_var: Var | None, right_var: Var | None) -> bool:
        """
        Return whether two visible port vars should be treated as the same wire.

        :param left_var: First visible port variable.
        :param right_var: Second visible port variable.
        :return: ``True`` when the ports represent the same symbolic connection.
        """
        if left_var is None or right_var is None:
            return False
        elif left_var.uid == right_var.uid:
            return True
        elif left_var.shared_ref is not None and left_var.shared_ref == right_var.shared_ref:
            return True
        elif left_var.ref is not None and left_var.ref == right_var.ref and left_var.network_conn and right_var.network_conn:
            return True
        else:
            return False

    def _find_output_port_for_var(self, item_source: GenericBlockItem, source_var: Var) -> PortItem | None:
        """
        Find the visible output port corresponding to one symbolic variable.

        :param item_source: Source item.
        :param source_var: Source variable.
        :return: Matching output port or ``None``.
        """
        port: PortItem
        for port in item_source.outputs:
            if self._vars_match_for_visible_connection(port.base_var, source_var):
                return port
            else:
                pass
        return None

    def _find_input_port_for_var(self, item_dest: GenericBlockItem, target_var: Var) -> PortItem | None:
        """
        Find the visible input port corresponding to one symbolic variable.

        :param item_dest: Destination item.
        :param target_var: Target variable.
        :return: Matching input port or ``None``.
        """
        port: PortItem
        for port in item_dest.inputs:
            if self._vars_match_for_visible_connection(port.base_var, target_var):
                return port
            else:
                pass
        return None

    @staticmethod
    def _connection_exists_between_ports(source_port: PortItem | BranchingItem,
                                         target_port: PortItem | BranchingItem) -> bool:
        """
        Return whether one visible connection already exists between two ports.

        :param source_port: Candidate source port.
        :param target_port: Candidate target port.
        :return: ``True`` when the connection is already present.
        """
        connection: ConnectionItem

        if source_port.connections is None:
            return False

        for connection in source_port.connections:
            if connection.source_port is source_port and connection.target_port is target_port:
                return True
            else:
                pass

        return False

    def add_api_obj_mapping(self):

        # Todo: add static_parameters_maping logic to add this depending on the type of device
        """
        Adds API object mapping for the main block based on the device type.

        This method checks the device type of the API object. If it matches the
        `DeviceType.LineDevice`, it performs the following actions:
        - Creates three new variables: g, b, and bsh using the variable factory.
        - Assigns constant values to these variables as parameters for the main block.
        - Maps the power flow reference type parameters to the corresponding newly
          created variables within the main block's API object mapping.

        :raises RuntimeError: Raised if required attributes or methods are missing.
        :return: None
        """
        if self.mode == DynamicSimulationMode.EMT:
            return
        else:
            pass

        if isinstance(self.api_object, BranchParent):
            g = self.var_factory.add_var("g")
            b = self.var_factory.add_var("b")
            bsh = self.var_factory.add_var("bsh")

            self.main_block.parameters[g] = self.var_factory.add_const(0.029585)
            self.main_block.parameters[b] = self.var_factory.add_const(0.0710059)
            self.main_block.parameters[bsh] = self.var_factory.add_const(0.03)

            self.main_block.api_obj_mapping = {
                ParamPowerFlowReferenceType.g: g,
                ParamPowerFlowReferenceType.b: b,
                ParamPowerFlowReferenceType.bsh: bsh,
            }

    def get_block_from_main_block(self, device_uid: int) -> Block | None:
        """
        Find a child block by uid in the editor root block.

        :param device_uid:
        :return:
        """
        block_model: Block

        for block_model in self.main_block.get_all_blocks():
            if block_model.uid == device_uid:
                return block_model
            else:
                pass

        return None

    def on_block_position_changed(self, device_uid: int, x: float, y: float) -> None:
        """
        Update the diagram node position when a block is moved by the user.

        :param device_uid:
        :param x:
        :param y:
        :return:
        """
        if device_uid in self.diagram.node_data:
            self.diagram.node_data[device_uid].x = x
            self.diagram.node_data[device_uid].y = y
            print("")

    def get_selected_scene_block(self) -> Block | None:
        """
        Return the single selected block, if the current selection is unambiguous.

        :return:
        """
        selected_items: List[QGraphicsItem] = self.scene.selectedItems()
        selected_item: QGraphicsItem

        if len(selected_items) == 1:
            selected_item = selected_items[0]

            if isinstance(selected_item,
                          (BlockItem, GenericBlockItem, RoundBaseArithmeticOpItem, RectBaseArithmeticOpItem)):
                return selected_item.subsys

            else:
                return None
        else:
            return None

    def on_parameters_table_double_clicked(self, index: QtCore.QModelIndex) -> None:
        """
        Open the expression text editor when the user double-clicks an expression row
        in either the equations table or the parameters table.

        :param index:
        :return:
        """
        source_model = self._table_source_model(index)
        source_index = self._table_source_index(index)
        source_row = source_index.row()
        if source_model is self.parameters_model and source_index.column() == 0:
            self.open_edit_parameter_type_dialog(source_row)
        elif source_model is self.parameters_model and source_index.column() == 2:
            row_data: BlockParameterRow | None = self.parameters_model.get_row(source_row)
            if row_data is not None and row_data.kind != BlockParameterKind.FIXED_PARAMETER:
                self.open_expression_editor_for_parameters(source_row)
        elif source_model is self.equations_model:
            row_data: BlockParameterRow | None = self.equations_model.get_row(source_row)
            if row_data is not None:
                if row_data.opens_expression_editor and source_index.column() == 1:
                    self.open_expression_row_editor(source_row)

    def open_edit_parameter_type_dialog(self, row_index: int) -> None:
        """
        Open the dialog to edit a parameter's type (event, mode, or regular).

        :param row_index:
        :return:
        """
        row_data: BlockParameterRow | None = self.parameters_model.get_row(row_index)
        if row_data is None or self.parameters_model.block is None:
            return

        block = self.parameters_model.block

        api_object = self.parameters_model.api_object
        dialog: EditParameterDialog = EditParameterDialog(
            api_object=api_object,
            devices_static_params_mapping=self.devices_static_params_mapping,
            current_kind=row_data.kind,
            parent=self
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                new_kind: BlockParameterKind = dialog.get_category_kind()
                old_kind: BlockParameterKind = row_data.kind

                if new_kind == old_kind:
                    return

                var_name = row_data.name

                if new_kind == BlockParameterKind.FIXED_PARAMETER:
                    static_var_ref = dialog.get_static_variable()
                    new_var = self.var_factory.add_var(name=var_name, reference=static_var_ref)
                    const_value = 0.0
                else:
                    new_var = self.var_factory.add_var(name=var_name)
                    const_value = dialog.get_parameter_value()

                old_var = row_data.key_var

                if old_kind == BlockParameterKind.EVENT_PARAMETER:
                    block.event_dict.pop(old_var, None)
                elif old_kind == BlockParameterKind.MODE_PARAMETER:
                    block.mode_dict.pop(old_var, None)
                elif old_kind == BlockParameterKind.FIXED_PARAMETER:
                    block.parameters.pop(old_var, None)

                if new_kind == BlockParameterKind.EVENT_PARAMETER:
                    block.event_dict[new_var] = Const(const_value, name=var_name)
                elif new_kind == BlockParameterKind.MODE_PARAMETER:
                    block.mode_dict[new_var] = Const(const_value, name=var_name)
                elif new_kind == BlockParameterKind.FIXED_PARAMETER:
                    block.parameters[new_var] = Const(const_value, name=var_name)

                self.parameters_model.set_block(block)
                self.parameters_model.block_updated.emit(block.uid)
            except Exception as exc:
                QtWidgets.QMessageBox.warning(self, "Edit Parameter Type Error", str(exc))

    def open_expression_editor_for_parameters(self, row_index: int) -> None:
        """
        Open the expression text editor for a parameters-table row.

        :param row_index:
        :return:
        """
        row_data: BlockParameterRow | None = self.parameters_model.get_row(row_index)
        expression_text: str
        dialog: ExpressionTextEditorDialog
        symbol_namespace: Dict[str, Expr]
        parsed_expression: Expr | Comparison
        expression_value: Expr

        if row_data is not None and self.parameters_model.block is not None:
            if row_data.value is not None and isinstance(row_data.value, Expr):
                expression_text = symbolic_to_string(row_data.value)
            else:
                expression_text = str(row_data.value) if row_data.value is not None else ""
            symbol_namespace = build_block_symbol_namespace(self.parameters_model.block)
            dialog = ExpressionTextEditorDialog(
                expression_text=expression_text,
                symbol_namespace=symbol_namespace,
                parent=self
            )

            if dialog.exec() == QDialog.DialogCode.Accepted:
                try:
                    parsed_expression = string_to_symbolic(dialog.get_expression_text(), symbol_namespace)

                    if isinstance(parsed_expression, Comparison):
                        expression_value = parsed_expression.to_expression()
                    else:
                        expression_value = parsed_expression

                    self.parameters_model.set_value_from_expression(row_index, expression_value)
                    print("")
                except Exception as exc:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Expression Error",
                        str(exc)
                    )

    @staticmethod
    def _table_source_index(index: QtCore.QModelIndex) -> QtCore.QModelIndex:
        model = index.model()
        if isinstance(model, QtCore.QSortFilterProxyModel):
            return model.mapToSource(index)
        return index

    @staticmethod
    def _table_source_model(index: QtCore.QModelIndex) -> QtCore.QAbstractItemModel | None:
        model = index.model()
        if isinstance(model, QtCore.QSortFilterProxyModel):
            return model.sourceModel()
        return model

    def on_variables_table_double_clicked(self, index: QtCore.QModelIndex) -> None:
        """
        Open the expression text editor when the user double-clicks an init_eq cell.

        :param index:
        :return:
        """
        if index.column() == 2:
            source_index = self._table_source_index(index)
            self.open_expression_row_editor_for_variables(source_index.row())

    def open_expression_row_editor_for_variables(self, row_index: int) -> None:
        """
        Open the expression text editor for a variables-table row.

        :param row_index:
        :return:
        """
        row_data: BlockParameterRow | None = self.variables_model.get_row(row_index)
        expression_text: str
        dialog: ExpressionTextEditorDialog
        symbol_namespace: Dict[str, Expr]
        parsed_expression: Expr | Comparison
        expression_value: Expr

        if row_data is not None and self.variables_model.block is not None:
            if row_data.init_eq is not None and isinstance(row_data.init_eq, Expr):
                expression_text = symbolic_to_string(row_data.init_eq)
            else:
                expression_text = ""
            symbol_namespace = build_block_symbol_namespace(self.variables_model.block)
            dialog = ExpressionTextEditorDialog(
                expression_text=expression_text,
                symbol_namespace=symbol_namespace,
                parent=self
            )

            if dialog.exec() == QDialog.DialogCode.Accepted:
                try:
                    parsed_expression = string_to_symbolic(dialog.get_expression_text(), symbol_namespace)

                    if isinstance(parsed_expression, Comparison):
                        expression_value = parsed_expression.to_expression()
                    else:
                        expression_value = parsed_expression

                    self.variables_model.set_init_eq(row_index, expression_value)
                except Exception as exc:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Expression Error",
                        str(exc)
                    )

    def select_table_context_row(self,
                                 table_view: QtWidgets.QTableView,
                                 position: QtCore.QPoint) -> None:
        """
        Select the row under a table context menu request when it is not already selected.

        :param table_view:
        :param position:
        :return:
        """
        index: QtCore.QModelIndex = table_view.indexAt(position)

        if index.isValid() and not table_view.selectionModel().isRowSelected(index.row(), QtCore.QModelIndex()):
            table_view.selectRow(index.row())
        else:
            pass

    def show_variables_table_context_menu(self, position: QtCore.QPoint) -> None:
        """
        Show the variables table context menu.

        :param position:
        :return:
        """
        table_view: QtWidgets.QTableView = self.ui.variablesTableView
        self.select_table_context_row(table_view=table_view, position=position)

        selected_block: Block | None = self.get_selected_scene_block()
        has_selected_rows: bool = bool(table_view.selectionModel().selectedRows())

        menu: QMenu = QMenu(table_view)
        add_variable_action: QAction = menu.addAction("Add Variable")
        remove_selected_action: QAction = menu.addAction("Remove Selected")

        add_variable_action.setEnabled(selected_block is not None)
        remove_selected_action.setEnabled(selected_block is not None and has_selected_rows)

        selected_action: QAction | None = menu.exec(table_view.viewport().mapToGlobal(position))

        if selected_action == add_variable_action:
            self.open_add_variable_dialog()
        elif selected_action == remove_selected_action:
            self.remove_selected_variables()
        else:
            pass

    def show_parameters_table_context_menu(self, position: QtCore.QPoint) -> None:
        """
        Show the parameters table context menu.

        :param position:
        :return:
        """
        table_view: QtWidgets.QTableView = self.ui.parametersTableView
        self.select_table_context_row(table_view=table_view, position=position)

        selected_block: Block | None = self.get_selected_scene_block()
        has_selected_rows: bool = bool(table_view.selectionModel().selectedRows())

        menu: QMenu = QMenu(table_view)
        add_parameter_action: QAction = menu.addAction("Add Parameter")
        remove_selected_action: QAction = menu.addAction("Remove Selected")

        add_parameter_action.setEnabled(selected_block is not None)
        remove_selected_action.setEnabled(selected_block is not None and has_selected_rows)

        selected_action: QAction | None = menu.exec(table_view.viewport().mapToGlobal(position))

        if selected_action == add_parameter_action:
            self.open_add_parameter_dialog()
        elif selected_action == remove_selected_action:
            self.remove_selected_parameters()
        else:
            pass

    def show_equations_table_context_menu(self, position: QtCore.QPoint) -> None:
        """
        Show the equations table context menu.

        :param position:
        :return:
        """
        table_view: QtWidgets.QTableView = self.ui.equationsTableView
        self.select_table_context_row(table_view=table_view, position=position)

        selected_block: Block | None = self.get_selected_scene_block()
        has_selected_rows: bool = bool(table_view.selectionModel().selectedRows())

        menu: QMenu = QMenu(table_view)
        add_equation_action: QAction = menu.addAction("Add Equation")
        remove_selected_action: QAction = menu.addAction("Remove Selected")

        add_equation_action.setEnabled(selected_block is not None)
        remove_selected_action.setEnabled(selected_block is not None and has_selected_rows)

        selected_action: QAction | None = menu.exec(table_view.viewport().mapToGlobal(position))

        if selected_action == add_equation_action:
            self.open_add_equation_dialog()
        elif selected_action == remove_selected_action:
            self.remove_selected_equations()
        else:
            pass

    def open_add_variable_dialog(self) -> None:
        """
        Open the dialog used to add a new block symbol.

        :return:
        """
        dialog: AddBlockVariableDialog = AddBlockVariableDialog(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                block = self.get_selected_scene_block()
                if block is None:
                    raise ValueError("No block is selected in the editor.")

                name = dialog.get_name()
                category = dialog.get_category()
                parameter_value = dialog.get_parameter_value()

                if not is_valid_symbol_name(name):
                    raise ValueError("The symbol name must be a valid identifier.")
                elif block_namespace_contains_name(block, name):
                    raise ValueError(f"The symbol '{name}' already exists in this block.")

                new_var = self.var_factory.add_var(name=name)
                add_variable_to_block(
                    block=block,
                    var=new_var,
                    var_type=category,
                    parameter_value=parameter_value
                )

                self.variables_model.set_block(block)
                self.parameters_model.set_block(block)
                self.equations_model.set_block(block)
                self.variables_model.block_updated.emit(block.uid)
            except Exception as exc:
                QtWidgets.QMessageBox.warning(self, "Add Variable Error", str(exc))
        else:
            pass

    def open_add_parameter_dialog(self) -> None:
        """
        Open the dialog used to add a new parameter (event, mode, or regular) to the selected block.

        :return:
        """
        api_object = self.parameters_model.api_object
        dialog: AddParameterDialog = AddParameterDialog(
            api_object=api_object,
            devices_static_params_mapping=self.devices_static_params_mapping,
            parent=self
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                block = self.get_selected_scene_block()
                if block is None:
                    raise ValueError("No block is selected in the editor.")

                name = dialog.get_name()
                category = dialog.get_category()

                if not is_valid_symbol_name(name):
                    raise ValueError("The symbol name must be a valid identifier.")
                elif block_namespace_contains_name(block, name):
                    raise ValueError(f"The symbol '{name}' already exists in this block.")

                if category == "parameter":
                    static_var_ref = dialog.get_static_variable()
                    new_var = self.var_factory.add_var(name=name, reference=static_var_ref)
                    parameter_value = None
                else:
                    new_var = self.var_factory.add_var(name=name)
                    parameter_value = dialog.get_parameter_value()
                add_variable_to_block(
                    block=block,
                    var=new_var,
                    var_type=category,
                    parameter_value=parameter_value
                )

                self.parameters_model.set_block(block)
                self.equations_model.set_block(block)
                self.parameters_model.block_updated.emit(block.uid)
            except Exception as exc:
                QtWidgets.QMessageBox.warning(self, "Add Parameter Error", str(exc))
        else:
            pass

    def open_add_equation_dialog(self) -> None:
        """
        Open the dialog used to add a new equation.

        :return:
        """
        block = self.get_selected_scene_block()
        if block is None:
            QtWidgets.QMessageBox.warning(self, "Add Equation Error", "No block is selected in the editor.")
            return

        symbol_namespace = build_block_symbol_namespace(block)
        dialog = AddEquationDialog(symbol_namespace=symbol_namespace, parent=self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                equation_text = dialog.get_equation_text()
                category = dialog.get_category()

                parsed_expr = string_to_symbolic(equation_text, symbol_namespace)

                if category == "state":
                    block.state_eqs.append(parsed_expr)
                elif category == "algebraic":
                    block.algebraic_eqs.append(parsed_expr)
                else:
                    raise ValueError(f"Unknown equation type: {category}")

                self.equations_model.set_block(block)
                self.equations_model.block_updated.emit(block.uid)
            except Exception as exc:
                QtWidgets.QMessageBox.warning(self, "Add Equation Error", str(exc))
        else:
            pass

    def remove_selected_variables(self) -> None:
        """
        Remove selected variables from the selected block.

        :return:
        """
        block = self.get_selected_scene_block()
        if block is None:
            return

        vars_model = self.variables_model
        vars_selected = [self._table_source_index(idx).row() for idx in
                         self.ui.variablesTableView.selectionModel().selectedRows()]
        if not vars_selected:
            return

        vars_to_remove_from_state = []
        vars_to_remove_from_algebraic = []
        init_keys_to_remove = []
        for row_idx in vars_selected:
            row_data = vars_model.rows[row_idx]
            var = row_data.key_var
            if row_data.kind == BlockParameterKind.STATE_VAR:
                if var in block.state_vars:
                    vars_to_remove_from_state.append(var)
                    if var in block.init_values:
                        init_keys_to_remove.append(var)
            elif row_data.kind == BlockParameterKind.ALGEBRAIC_VAR:
                if var in block.algebraic_vars:
                    vars_to_remove_from_algebraic.append(var)

        block.state_vars = [v for v in block.state_vars if v not in set(vars_to_remove_from_state)]
        block.algebraic_vars = [v for v in block.algebraic_vars if v not in set(vars_to_remove_from_algebraic)]
        for key in init_keys_to_remove:
            if key in block.init_values:
                del block.init_values[key]

        vars_model.set_block(block)
        vars_model.block_updated.emit(block.uid)

    def remove_selected_parameters(self) -> None:
        """
        Remove selected parameters from the selected block.

        :return:
        """
        block = self.get_selected_scene_block()
        if block is None:
            return

        params_model = self.parameters_model
        params_selected = [self._table_source_index(idx).row() for idx in
                           self.ui.parametersTableView.selectionModel().selectedRows()]
        if not params_selected:
            return

        for row_idx in params_selected:
            row_data = params_model.rows[row_idx]
            var = row_data.key_var
            if row_data.kind == BlockParameterKind.EVENT_PARAMETER:
                if var in block.event_dict:
                    del block.event_dict[var]
            elif row_data.kind == BlockParameterKind.MODE_PARAMETER:
                if var in block.mode_dict:
                    del block.mode_dict[var]
            elif row_data.kind == BlockParameterKind.FIXED_PARAMETER:
                if var in block.parameters:
                    del block.parameters[var]

        params_model.set_block(block)
        params_model.block_updated.emit(block.uid)

    def remove_selected_equations(self) -> None:
        """
        Remove selected equations from the selected block.

        :return:
        """
        block = self.get_selected_scene_block()
        if block is None:
            return

        equations_model = self.equations_model
        equations_selected = [self._table_source_index(idx).row() for idx in
                              self.ui.equationsTableView.selectionModel().selectedRows()]
        if not equations_selected:
            return

        state_indices_to_remove = set()
        alg_indices_to_remove = set()
        for row_idx in equations_selected:
            row_data = equations_model.rows[row_idx]
            if row_data.item_index is not None:
                if row_data.kind == BlockParameterKind.STATE_EQUATION:
                    state_indices_to_remove.add(row_data.item_index)
                elif row_data.kind == BlockParameterKind.ALGEBRAIC_EQUATION:
                    alg_indices_to_remove.add(row_data.item_index)

        new_state_eqs = [eq for idx, eq in enumerate(block.state_eqs) if idx not in state_indices_to_remove]
        new_algebraic_eqs = [eq for idx, eq in enumerate(block.algebraic_eqs) if idx not in alg_indices_to_remove]
        block.state_eqs = new_state_eqs
        block.algebraic_eqs = new_algebraic_eqs

        equations_model.set_block(block)
        equations_model.block_updated.emit(block.uid)

    def open_expression_row_editor(self, row_index: int) -> None:
        """
        Open the expression text editor for a parameter-table row.

        :param row_index:
        :return:
        """
        row_data: BlockParameterRow | None = self.equations_model.get_row(row_index)
        expression_text: str
        dialog: ExpressionTextEditorDialog
        symbol_namespace: Dict[str, Expr]
        parsed_expression: Expr | Comparison
        expression_value: Expr

        if row_data is not None and self.equations_model.block is not None:
            if isinstance(row_data.value, Expr):
                old_expr = row_data.value
                expression_text = symbolic_to_string(row_data.value)
                self.equations_model.symbol_namespace = build_block_symbol_namespace(
                    self.equations_model.block)
                dialog = ExpressionTextEditorDialog(
                    expression_text=expression_text,
                    symbol_namespace=self.equations_model.symbol_namespace,
                    parent=self
                )

                if dialog.exec() == QDialog.DialogCode.Accepted:
                    try:
                        parsed_expression = string_to_symbolic(dialog.get_expression_text(),
                                                               self.equations_model.symbol_namespace)

                        if isinstance(parsed_expression, Comparison):
                            expression_value = parsed_expression.to_expression()
                        else:
                            expression_value = parsed_expression

                        index = self.equations_model.index(row_index, 1)
                        self.equations_model.setData(index, symbolic_to_string(expression_value),
                                                     QtCore.Qt.ItemDataRole.EditRole)
                    except Exception as exc:
                        QtWidgets.QMessageBox.warning(
                            self,
                            "Expression Error",
                            str(exc)
                        )
                else:
                    pass
            else:
                pass
        else:
            pass

    def center_view_on_items(self) -> None:
        """
        Center the graphics view on the current selection or, if none exists, on all items.

        :return:
        """
        self.view.center_items()

    def zoom_in_view(self) -> None:
        """
        Zoom the graphics view in.

        :return:
        """
        self.view.zoom_in()

    def zoom_out_view(self) -> None:
        """
        Zoom the graphics view out.

        :return:
        """
        self.view.zoom_out()

    def delete_all_blocks_with_confirmation(self) -> None:
        """
        Ask the user for confirmation before deleting the complete model body.

        The operation is destructive for the internal implementation, so it must
        follow the same GUI confirmation style used across the rest of VeraGrid.
        Only after the user confirms the action can the editor clear all blocks
        except for the protected connection ports.

        :return: None.
        """
        confirmed: bool = yes_no_question(
            text="You are going to delete the complete model and start from scratch. Are you sure?",
            title="Delete all"
        )

        if confirmed:
            deletable_items: List[BlockItem | GenericBlockItem] = list()
            scene_item: QGraphicsItem

            for scene_item in self.scene.items():
                if isinstance(scene_item, ProtectedConnectionBlockItem):
                    pass
                else:
                    if isinstance(scene_item,
                                  (BlockItem, GenericBlockItem, RoundBaseArithmeticOpItem, RectBaseArithmeticOpItem)):
                        deletable_items.append(scene_item)
                    else:
                        pass

            deletable_item: BlockItem | GenericBlockItem | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem

            if len(deletable_items) == 0:
                self._selected_side_block = None
                self.refresh_active_side_panel()
            else:
                for deletable_item in deletable_items:
                    self.remove_block_item(deletable_item)

                self.scene.clearSelection()
                self._selected_side_block = None
                self.refresh_active_side_panel()
                self.mark_unapplied_changes()
        else:
            pass

    def on_scene_selection_changed(self) -> None:
        """
        Refresh the right-side parameters table from the selected block.

        :return:
        """
        selected_block: Block | None = self.get_selected_scene_block()
        self._selected_side_block = selected_block
        self.refresh_active_side_panel()

    @QtCore.Slot(int)
    def handle_side_panel_page_changed(self, index: int) -> None:
        """
        Refresh only the side panel that just became visible.

        :param index: Newly selected toolbox page index.
        :return: None.
        """
        _unused_index: int = index
        self.refresh_active_side_panel()

    def refresh_active_side_panel(self) -> None:
        """
        Refresh only the currently visible side panel.

        :return: None.
        """
        current_widget: QtWidgets.QWidget = self.ui.toolBox.currentWidget()

        if current_widget == self.ui.page:
            self.variables_model.set_block(self._selected_side_block)
        else:
            if current_widget == self.ui.page_2:
                self.parameters_model.set_block(self._selected_side_block)
            else:
                if current_widget == self.ui.page_3:
                    self.equations_model.set_block(self._selected_side_block)
                else:
                    pass

    def edit_scene_item(self, item: BlockItem | GenericBlockItem | ConnectionItem) -> None:
        """
        Open an editor for the selected scene item when supported.

        :param item: Scene item selected from the context menu.
        :return: None.
        """
        if isinstance(item, (GenericBlockItem, BlockItem)):
            self.open_block_subeditor(item)

    def open_block_subeditor(self, item: BlockItem | GenericBlockItem) -> None:
        """
        Open a nested block editor for one block item.

        :param item: Target block item.
        :return: None.
        """
        if item.subsys is None:
            return
        else:
            pass

        editor_window: DynamicBlockEditorGUI | None = item.editor_window

        if editor_window is None:
            editor_window = DynamicBlockEditorGUI(
                var_factory=self.var_factory,
                block=item.subsys,
                api_object=self.api_object,
                circuit=self.circuit,
                mode=self.mode,
                modal=False,
            )
            item.editor_window = editor_window
        else:
            pass

        editor_window.show()
        editor_window.raise_()
        editor_window.activateWindow()

    def decompose_block_in_place(self, block: Block) -> None:

        decomposer = EquationDecomposer(self.var_factory)
        decomposed = decomposer.decompose(block)
        preserved_uid = block.uid
        block.name = decomposed.name
        block.is_decomposable = decomposed.is_decomposable
        block.vars_glob_name2uid = decomposed.vars_glob_name2uid
        block.state_vars = decomposed.state_vars
        block.state_eqs = decomposed.state_eqs
        block.algebraic_vars = decomposed.algebraic_vars
        block.algebraic_eqs = decomposed.algebraic_eqs
        block.diff_vars = decomposed.diff_vars
        block.reformulated_vars = decomposed.reformulated_vars
        block.differential_eqs = decomposed.differential_eqs
        block.init_eqs = decomposed.init_eqs
        block.diff_init_eqs = decomposed.diff_init_eqs
        block.children = decomposed.children
        block.in_vars = decomposed.in_vars
        block.out_vars = decomposed.out_vars
        block.parameters = decomposed.parameters
        block.discrete_eqs = decomposed.discrete_eqs
        block.external_mapping = decomposed.external_mapping
        block.api_obj_mapping = decomposed.api_obj_mapping
        block.init_values = decomposed.init_values
        block.var_mapping = decomposed.var_mapping
        block.event_dict = decomposed.event_dict
        block.mode_dict = decomposed.mode_dict
        block.diagram = decomposed.diagram
        block.uid = preserved_uid

    def get_scene_item_by_block_uid(self,
                                    block_uid: int) -> BlockItem | GenericBlockItem | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem | None:
        """
        Find the visible scene item representing a block uid.

        :param block_uid:
        :return:
        """
        item: QGraphicsItem

        for item in self.scene.items():
            if isinstance(item, (BlockItem, GenericBlockItem, RoundBaseArithmeticOpItem,
                                 RectBaseArithmeticOpItem)) and item.subsys is not None:
                if item.subsys.uid == block_uid:
                    return item
                else:
                    pass
            else:
                pass

        return None

    def select_block_by_uid(self, block_uid: int) -> None:
        """
        Restore the selection for a block after a scene refresh.

        :param block_uid:
        :return:
        """
        item: BlockItem | GenericBlockItem | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem | None = self.get_scene_item_by_block_uid(
            block_uid)

        if item is not None:
            self.scene.clearSelection()
            item.setSelected(True)
        else:
            pass

    def on_block_updated(self, block_uid: int) -> None:
        """
        Refresh the scene after a block edit coming from the parameters tab.

        :param block_uid:
        :return:
        """
        self.mark_unapplied_changes()
        sender_obj: QtCore.QObject | None = self.sender()

        if sender_obj is self.parameters_model:
            self.refresh_active_side_panel()
        else:
            self.rebuild_scene_from_diagram()
            self.select_block_by_uid(block_uid)

    def _show_model_saved_toast(self) -> None:
        """
        Show one save confirmation toast attached to this editor window.

        The editor owns a local toast manager so the notification is layered on
        top of the editor page that triggered the save operation.

        :return: None.
        """
        # Emit the toast from the editor itself so the notification stays in
        # front of the page where the user clicked the save button.
        self.toast_manager.show_info_toast("Model saved")

    def apply_changes(self) -> None:
        """
        Commit the edited working copy back into the original block.

        :return:
        """
        if self.mode == DynamicSimulationMode.RMS:
            # Persist the edited RMS block back into the original model object.
            copy_block_state(source_block=self.main_block, target_block=self.original_block)
            # Rebuild the connected bus helper models so the saved block stays
            # consistent with the rest of the dynamic network representation.
            initialize_connected_bus_models_for_editor_assignment(api_object=self.api_object,
                                                                  circuit=self.circuit,
                                                                  var_factory=self.var_factory,
                                                                  mode=self.mode)
            # Mark the editor state as clean because all in-memory edits were
            # transferred back to the owned device model successfully.
            self.has_unapplied_changes = False
            self.changes_applied = True
            self.dirtyStateChanged.emit(False)
            # Notify the user that the save operation completed, while keeping
            # the editor open for further edits.
            self._show_model_saved_toast()
            if self.workspace_embedded:
                pass
            else:
                pass



        elif self.mode == DynamicSimulationMode.EMT:
            masks_are_valid: bool
            requested_bus_mask: list[bool] | None
            requested_from_mask: list[bool] | None
            requested_to_mask: list[bool] | None

            masks_are_valid, requested_bus_mask, requested_from_mask, requested_to_mask = \
                self._get_requested_emt_bus_masks_from_current_interface()
            if self.api_object.emt_template is not None:
                # The editor is about to overwrite the saved EMT model in place,
                # so the reusable template pointer must be cleared. However, the
                # generic ``emt_template = None`` setter also unregisters the
                # current device from all bus registries immediately. That early
                # detach does not happen in the native template-assignment flow
                # and breaks the symbolic identity chain that the later shared
                # attach helper expects to repair in place. Clear only the stored
                # template reference here and let the shared attach helper handle
                # the bus-registry refresh at the correct stage.
                self.api_object.emt_template = None
            else:
                pass
            if masks_are_valid:
                # Persist only the EMT interface refs that are still wired into
                # the edited model so the saved device contract matches the
                # rebuilt terminal bus shells seen by the simulation builder.
                self._prune_disconnected_emt_root_interface()
                # Copy the validated editor state back to the owned EMT model.
                copy_block_state(source_block=self.main_block, target_block=self.original_block)
                # Editor copy-back can leave the saved root external mapping and
                # the saved root input/output vars for the same EMT reference as
                # different symbolic objects. Normalize the saved contract first
                # so later reconnect helpers and the EMT checker operate on the
                # same root variables.
                unify_saved_emt_model_root_contract(device=self.api_object)
                # The saved EMT model now owns fresh cloned symbolic variables.
                # Register those authoritative post-copy variables in the shared
                # VarFactory before any reconnect step tries to propagate bus-side
                # identities through the factory connection machinery.
                register_saved_emt_model_vars_for_device(device=self.api_object,
                                                         var_factory=self.var_factory)
                # The editor path now reuses the same engine-side EMT attachment
                # workflow as the native template-assignment path. The only GUI-
                # specific responsibility left here is determining which phase
                # masks the user kept connected.
                attach_emt_model_to_buses(device=self.api_object,
                                          model=self.api_object.emt_model,
                                          var_factory=self.var_factory,
                                          bus_mask=requested_bus_mask,
                                          from_mask=requested_from_mask,
                                          to_mask=requested_to_mask)
                # Mark the working copy as saved because the device model now
                # contains the current editor contents.
                self.has_unapplied_changes = False
                self.changes_applied = True
                self.dirtyStateChanged.emit(False)
                # Inform the user that the model was saved and keep the editor
                # available for incremental editing.
                self._show_model_saved_toast()
                if self.workspace_embedded:
                    pass
                else:
                    pass
            else:
                # Do not apply the edited model if the bus interface is invalid.
                # The warning is already emitted by the editor mask-validation path.
                pass

    def open_inspect_dialog(self):
        """
        creates and opens the dialog containing the model info (read only)
        :return:
        """
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Inspect Model")
        dialog.resize(600, 400)

        # create layout
        layout = QVBoxLayout(dialog)

        # Instantiate inspector class
        inspect_widget = InspectModel(block=self.main_block, parent=dialog)

        # Add inspector to layout
        layout.addWidget(inspect_widget)

        # Add (OK / Cancel)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                      QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(button_box)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        # Show dialog
        dialog.exec()

    def _build_connected_port_sets(self) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
        """
        Build quick-lookup sets for connected inputs and outputs.

        :return: ``(connected_inputs, connected_outputs)``.
        """
        # The graph diagram stores connections by node UID and port index. The
        # validator precomputes these sets once so later checks are O(1) per port.
        connected_inputs: set[tuple[int, int]] = set()
        connected_outputs: set[tuple[int, int]] = set()
        con: Any
        for con in self.diagram.con_data.values():
            connected_outputs.add((con.from_uid, con.port_number_from))
            connected_inputs.add((con.to_uid, con.port_number_to))
        return connected_inputs, connected_outputs

    def _validate_equation_counts(self, section: ValidationSection, blocks: list[Block]) -> None:
        """
        Append state/algebraic equation-count mismatches.

        :param section: Mutable grouped section results.
        :param blocks: Blocks to validate.
        :return: None.
        """
        block: Block
        for block in blocks:
            # The first structural consistency rule checks equation balance for
            # each symbolic subsystem independently.
            block_label: str = format_validation_block_label(block)
            if len(block.state_vars) != len(block.state_eqs):
                add_validation_detail(
                    section=section,
                    block_label=block_label,
                    detail=f"state vars={len(block.state_vars)}, state eqs={len(block.state_eqs)}",
                )
            else:
                pass

            if len(block.algebraic_vars) != len(block.algebraic_eqs):
                add_validation_detail(
                    section=section,
                    block_label=block_label,
                    detail=f"algebraic vars={len(block.algebraic_vars)}, algebraic eqs={len(block.algebraic_eqs)}",
                )
            else:
                pass

    def _validate_duplicate_variable_names(self, section: ValidationSection, blocks: list[Block]) -> None:
        """
        Append duplicate symbolic-name issues inside each block.

        :param section: Mutable grouped section results.
        :param blocks: Blocks to validate.
        :return: None.
        """
        block: Block
        for block in blocks:
            # Duplicate-name validation must inspect every collection that can
            # expose symbolic variables inside one block.
            name_to_uids: dict[str, set[int]] = dict()
            parameter_vars: list[Var] = list(block.parameters.keys())
            event_vars: list[Var] = list(block.event_dict.keys())
            mode_vars: list[Var] = list(block.mode_dict.keys())

            append_vars_to_name_uid_map(name_to_uids=name_to_uids, vars_list=block.state_vars)
            append_vars_to_name_uid_map(name_to_uids=name_to_uids, vars_list=block.algebraic_vars)
            append_vars_to_name_uid_map(name_to_uids=name_to_uids, vars_list=block.diff_vars)
            append_vars_to_name_uid_map(name_to_uids=name_to_uids, vars_list=block.in_vars)
            append_vars_to_name_uid_map(name_to_uids=name_to_uids, vars_list=block.out_vars)
            append_vars_to_name_uid_map(name_to_uids=name_to_uids, vars_list=parameter_vars)
            append_vars_to_name_uid_map(name_to_uids=name_to_uids, vars_list=event_vars)
            append_vars_to_name_uid_map(name_to_uids=name_to_uids, vars_list=mode_vars)

            # Out vars, in vars, mappings and parameter dictionaries often reuse
            # the exact same Var object that already exists in the block state or
            # algebraic collections. That is valid. We only flag names that map
            # to multiple distinct symbolic variables.
            duplicates: list[str] = sorted([name for name, uids in name_to_uids.items() if len(uids) > 1])
            if duplicates:
                add_validation_detail(
                    section=section,
                    block_label=format_validation_block_label(block),
                    detail=f"vars: {', '.join(duplicates)}",
                )
            else:
                pass

    def _validate_parameter_mappings(self, section: ValidationSection, blocks: list[Block]) -> None:
        """
        Append parameter mapping and event-value issues.

        :param section: Mutable grouped section results.
        :param blocks: Blocks to validate.
        :return: None.
        """
        block: Block
        for block in blocks:
            # Static parameters are only meaningful if the wider model can reach
            # them through one of the supported mapping dictionaries.
            mapped_vars: set[Var] = {
                var for var in block.external_mapping.values() if isinstance(var, Var)
            }
            mapped_vars.update(var for var in block.api_obj_mapping.values() if isinstance(var, Var))
            mapped_vars.update(var for var in block.event_dict.keys() if isinstance(var, Var))

            unmapped_parameters: list[str] = sorted([
                var.name for var in block.parameters.keys() if isinstance(var, Var) and var not in mapped_vars
            ])
            missing_event_values: list[str] = sorted([
                var.name for var, expr in block.event_dict.items() if isinstance(var, Var) and expr is None
            ])

            if unmapped_parameters:
                add_validation_detail(
                    section=section,
                    block_label=format_validation_block_label(block),
                    detail=f"params missing mapping: {', '.join(unmapped_parameters)}",
                )
            else:
                pass

            if missing_event_values:
                add_validation_detail(
                    section=section,
                    block_label=format_validation_block_label(block),
                    detail=f"event params with no value: {', '.join(missing_event_values)}",
                )
            else:
                pass

    def _validate_variable_initialization(self, section: ValidationSection,
                                          traversal_nodes: list[ValidationTraversalNode]) -> None:
        """
        Append initialization issues for state, algebraic and diff variables.

        :param section: Mutable grouped section results.
        :param traversal_nodes: Recursive traversal nodes carrying effective mappings.
        :return: None.
        """
        traversal_node: ValidationTraversalNode
        for traversal_node in traversal_nodes:
            block: Block = traversal_node.get_block()
            # Initialization validation checks which variables can be seeded from
            # the external interface and which ones must be seeded internally.
            external_vars: set[Var] = traversal_node.get_effective_external_vars()

            missing_init_vars: list[str] = list()
            var: Var
            for var in block.state_vars:
                if var not in external_vars and var not in block.init_eqs:
                    missing_init_vars.append(var.name)
                else:
                    pass

            for var in block.algebraic_vars:
                if var not in external_vars and var not in block.init_eqs:
                    missing_init_vars.append(var.name)
                else:
                    pass

            missing_init_vars = sorted(missing_init_vars)
            missing_diff_init_vars: list[str] = sorted([
                var.name
                for var in block.diff_vars
                if isinstance(var, Var) and var not in external_vars and var not in block.diff_init_eqs
            ])

            if missing_init_vars:
                add_validation_detail(
                    section=section,
                    block_label=format_validation_block_label(block),
                    detail=f"vars missing init/external mapping: {', '.join(missing_init_vars)}",
                )
            else:
                pass

            if missing_diff_init_vars:
                add_validation_detail(
                    section=section,
                    block_label=format_validation_block_label(block),
                    detail=f"diff vars missing diff init/external mapping: {', '.join(missing_diff_init_vars)}",
                )
            else:
                pass

    def _validate_port_connectivity(self, section: ValidationSection) -> None:
        """
        Append missing-port-connection issues from the saved diagram.

        :param section: Mutable grouped section results.
        :return: None.
        """
        connected_inputs, connected_outputs = self._build_connected_port_sets()
        node_uid: int
        node: Any

        for node_uid, node in self.diagram.node_data.items():
            # Each diagram node is validated against the saved symbolic interface
            # so the report reflects exactly what the user wired in the editor.
            block: Block | None = self.get_block_from_main_block(node.device_uid)
            if block is None:
                pass
            else:
                missing_port_messages: list[str] = list()
                emt_missing_by_phase: dict[str, list[str]] = dict({"N": list(), "A": list(), "B": list(), "C": list()})
                missing_input_names: list[str] = list()
                missing_output_names: list[str] = list()
                missing_input_refs: list[VarPowerFlowReferenceType] = list()
                missing_output_refs: list[VarPowerFlowReferenceType] = list()
                append_missing_port_messages_for_direction(
                    missing_port_messages=missing_port_messages,
                    emt_missing_by_phase=emt_missing_by_phase,
                    vars_list=block.in_vars,
                    node_uid=node_uid,
                    connected_ports=connected_inputs,
                    is_input=True,
                    mode=self.mode,
                )
                append_missing_port_messages_for_direction(
                    missing_port_messages=missing_port_messages,
                    emt_missing_by_phase=emt_missing_by_phase,
                    vars_list=block.out_vars,
                    node_uid=node_uid,
                    connected_ports=connected_outputs,
                    is_input=False,
                    mode=self.mode,
                )

                if self.mode == DynamicSimulationMode.EMT:
                    # EMT allows a whole phase to be absent, but it does not allow
                    # partially connected ports for a phase that is otherwise present.
                    phase_total_ports_by_name: dict[str, int] = dict({"N": 0, "A": 0, "B": 0, "C": 0})
                    append_port_vars_to_phase_count(phase_counts=phase_total_ports_by_name, vars_list=block.in_vars)
                    append_port_vars_to_phase_count(phase_counts=phase_total_ports_by_name, vars_list=block.out_vars)
                    root_connected_interface_refs: set[
                        VarPowerFlowReferenceType] = self._get_connected_root_interface_refs()
                    root_injection_mask: list[bool] = build_emt_injection_bus_mask_from_refs(
                        refs=root_connected_interface_refs)
                    root_branch_from_mask: list[bool] = build_emt_branch_bus_mask_from_refs(
                        refs=root_connected_interface_refs,
                        side="from",
                    )
                    root_branch_to_mask: list[bool] = build_emt_branch_bus_mask_from_refs(
                        refs=root_connected_interface_refs,
                        side="to",
                    )
                    phase_index_by_name: dict[str, int] = dict({"N": 0, "A": 1, "B": 2, "C": 3})

                    phase_name: str
                    phase_missing_messages: list[str]
                    for phase_name, phase_missing_messages in emt_missing_by_phase.items():
                        if phase_missing_messages:
                            phase_total_ports: int = phase_total_ports_by_name[phase_name]
                            phase_missing_count: int = len(phase_missing_messages)
                            phase_index: int = phase_index_by_name[phase_name]
                            phase_is_fully_absent_at_root: bool = False
                            root_reference: VarPowerFlowReferenceType | None = None

                            if block in self.main_block.in_vars or block in self.main_block.out_vars:
                                root_reference = get_var_reference(var=block)
                            else:
                                if node.tpe == BlockType.INPUT_CONN.name or node.tpe == BlockType.OUTPUT_CONN.name:
                                    reference_var: Var | None = None

                                    if node.tpe == BlockType.INPUT_CONN.name and len(block.out_vars) > 0:
                                        reference_var = block.out_vars[0]
                                    else:
                                        if node.tpe == BlockType.OUTPUT_CONN.name and len(block.in_vars) > 0:
                                            reference_var = block.in_vars[0]
                                        else:
                                            reference_var = None

                                    if reference_var is not None:
                                        root_reference = get_var_reference(var=reference_var)
                                    else:
                                        root_reference = None
                                else:
                                    root_reference = None

                            if root_reference is not None:
                                if root_reference in {
                                    VarPowerFlowReferenceType.v_N,
                                    VarPowerFlowReferenceType.v_A,
                                    VarPowerFlowReferenceType.v_B,
                                    VarPowerFlowReferenceType.v_C,
                                    VarPowerFlowReferenceType.i_N,
                                    VarPowerFlowReferenceType.i_A,
                                    VarPowerFlowReferenceType.i_B,
                                    VarPowerFlowReferenceType.i_C,
                                }:
                                    phase_is_fully_absent_at_root = not root_injection_mask[phase_index]
                                else:
                                    if root_reference in {
                                        VarPowerFlowReferenceType.vf_N,
                                        VarPowerFlowReferenceType.vf_A,
                                        VarPowerFlowReferenceType.vf_B,
                                        VarPowerFlowReferenceType.vf_C,
                                        VarPowerFlowReferenceType.if_N,
                                        VarPowerFlowReferenceType.if_A,
                                        VarPowerFlowReferenceType.if_B,
                                        VarPowerFlowReferenceType.if_C,
                                    }:
                                        phase_is_fully_absent_at_root = not root_branch_from_mask[phase_index]
                                    else:
                                        if root_reference in {
                                            VarPowerFlowReferenceType.vt_N,
                                            VarPowerFlowReferenceType.vt_A,
                                            VarPowerFlowReferenceType.vt_B,
                                            VarPowerFlowReferenceType.vt_C,
                                            VarPowerFlowReferenceType.it_N,
                                            VarPowerFlowReferenceType.it_A,
                                            VarPowerFlowReferenceType.it_B,
                                            VarPowerFlowReferenceType.it_C,
                                        }:
                                            phase_is_fully_absent_at_root = not root_branch_to_mask[phase_index]
                                        else:
                                            phase_is_fully_absent_at_root = False
                            else:
                                phase_is_fully_absent_at_root = False

                            if phase_is_fully_absent_at_root and \
                                    (node.tpe == BlockType.INPUT_CONN.name or node.tpe == BlockType.OUTPUT_CONN.name):
                                pass
                            else:
                                if phase_total_ports > 0:
                                    missing_port_messages.extend(phase_missing_messages)
                                else:
                                    pass
                        else:
                            pass
                else:
                    pass

                port_message: str
                for port_message in missing_port_messages:
                    if port_message.startswith("input '") and port_message.endswith("' is not connected"):
                        missing_input_names.append(port_message[7:-18])
                    else:
                        if port_message.startswith("output '") and port_message.endswith("' is not connected"):
                            missing_output_names.append(port_message[8:-18])
                        else:
                            pass

                input_var: Var
                for input_var in block.in_vars:
                    if input_var.name in missing_input_names:
                        input_reference: VarPowerFlowReferenceType | None = get_var_reference(var=input_var)
                        if input_reference is not None:
                            missing_input_refs.append(input_reference)
                        else:
                            pass
                    else:
                        pass

                output_var: Var
                for output_var in block.out_vars:
                    if output_var.name in missing_output_names:
                        output_reference: VarPowerFlowReferenceType | None = get_var_reference(var=output_var)
                        if output_reference is not None:
                            missing_output_refs.append(output_reference)
                        else:
                            pass
                    else:
                        pass

                if self.mode == DynamicSimulationMode.EMT:
                    if node.tpe == BlockType.INPUT_CONN.name or node.tpe == BlockType.OUTPUT_CONN.name:
                        root_connected_interface_refs: set[
                            VarPowerFlowReferenceType] = self._get_connected_root_interface_refs()
                        root_injection_mask: list[bool] = build_emt_injection_bus_mask_from_refs(
                            refs=root_connected_interface_refs,
                        )
                        root_branch_from_mask: list[bool] = build_emt_branch_bus_mask_from_refs(
                            refs=root_connected_interface_refs,
                            side="from",
                        )
                        root_branch_to_mask: list[bool] = build_emt_branch_bus_mask_from_refs(
                            refs=root_connected_interface_refs,
                            side="to",
                        )
                        protected_reference: VarPowerFlowReferenceType | None = None
                        skip_protected_root_row: bool = False

                        if node.tpe == BlockType.INPUT_CONN.name and len(block.out_vars) > 0:
                            protected_reference = get_var_reference(var=block.out_vars[0])
                        else:
                            if node.tpe == BlockType.OUTPUT_CONN.name and len(block.in_vars) > 0:
                                protected_reference = get_var_reference(var=block.in_vars[0])
                            else:
                                protected_reference = None

                        # Keep protected EMT root rows visible even when a whole
                        # phase is currently disconnected, because Show Issues must
                        # still project those missing interface ports back onto the
                        # canvas for the user to fix them.
                        skip_protected_root_row = False

                        if skip_protected_root_row:
                            missing_input_names = list()
                            missing_output_names = list()
                        else:
                            pass
                    else:
                        pass
                else:
                    pass

                if missing_input_names or missing_output_names:
                    block_label: str = node.name

                    if block in self.main_block.in_vars or block in self.main_block.out_vars:
                        # Root interface rows must point back to the visible protected
                        # connector node on canvas, not to the synthetic internal root
                        # variable name used by some rebuilt test/editor states.
                        block_label = node.name
                    else:
                        pass

                    add_validation_port_detail(
                        section=section,
                        block_label=block_label,
                        detail=format_missing_port_detail(
                            input_names=missing_input_names,
                            output_names=missing_output_names,
                        ),
                        input_names=missing_input_names,
                        output_names=missing_output_names,
                        input_refs=missing_input_refs,
                        output_refs=missing_output_refs,
                    )

                    if self.mode == DynamicSimulationMode.EMT and \
                            (node.tpe == BlockType.OUTPUT_CONN.name or node.tpe == BlockType.INPUT_CONN.name):
                        internal_owner_block: Block | None
                        internal_owner_label: str

                        internal_owner_block = self._find_internal_block_owning_emt_refs(
                            excluded_block=block,
                            input_refs=set(missing_input_refs),
                            output_refs=set(missing_output_refs),
                        )

                        if internal_owner_block is not None:
                            internal_owner_label = format_validation_block_label(internal_owner_block)
                            add_validation_port_detail(
                                section=section,
                                block_label=internal_owner_label,
                                detail=format_missing_port_detail(
                                    input_names=missing_input_names,
                                    output_names=missing_output_names,
                                ),
                                input_names=missing_input_names,
                                output_names=missing_output_names,
                                input_refs=missing_input_refs,
                                output_refs=missing_output_refs,
                            )
                        else:
                            pass
                else:
                    pass

    def _find_internal_block_owning_emt_refs(self,
                                             excluded_block: Block,
                                             input_refs: set[VarPowerFlowReferenceType],
                                             output_refs: set[VarPowerFlowReferenceType]) -> Block | None:
        """
        Return one non-interface block exposing the requested EMT refs.

        :param excluded_block: Interface wrapper block to ignore.
        :param input_refs: Candidate input refs.
        :param output_refs: Candidate output refs.
        :return: Matching internal block or ``None``.
        """
        child_block: Block
        node_data: Any | None
        input_var: Var
        output_var: Var

        for child_block in self.main_block.children:
            if child_block.uid == excluded_block.uid:
                continue

            node_data = self.diagram.node_data.get(child_block.uid, None)
            if node_data is not None and node_data.tpe in {BlockType.INPUT_CONN.name, BlockType.OUTPUT_CONN.name}:
                continue

            for input_var in child_block.in_vars:
                if get_var_reference(var=input_var) in input_refs:
                    return child_block

            for output_var in child_block.out_vars:
                if get_var_reference(var=output_var) in output_refs:
                    return child_block

        return None

    def _validate_emt_phase_consistency(self, section: ValidationSection) -> None:
        """
        Append EMT phase-wire consistency information for each diagram node.

        :param section: Mutable grouped section results.
        :return: None.
        """
        # This section reflects only the root EMT interface contract seen by the
        # bus: one V input and one I output for each of N, A, B, and C.
        editor_interface_refs: set[VarPowerFlowReferenceType] = self._get_connected_root_interface_refs()
        root_interface_refs: set[VarPowerFlowReferenceType] = set()
        root_var: Var
        root_reference: VarPowerFlowReferenceType | None

        for root_var in self.main_block.in_vars:
            root_reference = get_var_reference(var=root_var)
            if root_reference is not None:
                if self._is_emt_interface_reference(root_reference):
                    root_interface_refs.add(root_reference)
                else:
                    pass
            else:
                pass

        for root_var in self.main_block.out_vars:
            root_reference = get_var_reference(var=root_var)
            if root_reference is not None:
                if self._is_emt_interface_reference(root_reference):
                    root_interface_refs.add(root_reference)
                else:
                    pass
            else:
                pass

        if has_ac_emt_phase_interface_refs(refs=root_interface_refs):
            pass
        else:
            return

        phase_name: str
        if isinstance(self.api_object, BranchParent):
            side: str
            for side in ["from", "to"]:
                if has_ac_emt_branch_side_refs(side=side, refs=root_interface_refs):
                    for phase_name in ["N", "A", "B", "C"]:
                        ok_state: bool
                        detail: str
                        ok_state, detail = classify_emt_branch_phase_wire_from_refs(
                            side=side,
                            phase_name=phase_name,
                            refs=editor_interface_refs,
                        )
                        add_validation_status_detail(
                            section=section,
                            block_label=get_branch_phase_table_label(side=side, phase_name=phase_name),
                            detail=detail,
                            ok=ok_state,
                        )
                else:
                    pass
        else:
            for phase_name in ["N", "A", "B", "C"]:
                ok_state: bool
                detail: str
                ok_state, detail = classify_emt_injection_phase_wire_from_refs(
                    phase_name=phase_name,
                    refs=editor_interface_refs,
                )
                add_validation_status_detail(
                    section=section,
                    block_label=get_phase_table_label(phase_name=phase_name),
                    detail=detail,
                    ok=ok_state,
                )

    def collect_model_consistency_sections(self) -> list[ValidationSection]:
        """
        Validate the current working model and return grouped section results.

        :return: Ordered validation sections.
        """
        # The full validation runs as a deterministic pipeline so the dialog keeps
        # a stable order and users can compare repeated checks easily.
        blocks: list[Block] = collect_block_tree(root_block=self.main_block)
        traversal_root: ValidationTraversalNode = build_validation_traversal_node(
            block=self.main_block,
            inherited_external_vars=set(),
        )
        traversal_nodes: list[ValidationTraversalNode] = collect_validation_traversal_list(root_node=traversal_root)
        equation_section: ValidationSection = ValidationSection(title="Equation Counts")
        duplicate_section: ValidationSection = ValidationSection(title="Repeated Variable Names")
        parameter_section: ValidationSection = ValidationSection(title="Parameter Mappings")
        init_section: ValidationSection = ValidationSection(title="Variable Initialization")
        port_section: ValidationSection = ValidationSection(title="Port Connectivity")
        phase_section: ValidationSection = ValidationSection(
            title="Phases Consistency",
            first_column_title="Phase",
            show_issue_label=False,
        )

        self._validate_equation_counts(section=equation_section, blocks=blocks)
        self._validate_duplicate_variable_names(section=duplicate_section, blocks=blocks)
        self._validate_parameter_mappings(section=parameter_section, blocks=blocks)
        self._validate_variable_initialization(section=init_section, traversal_nodes=traversal_nodes)
        self._validate_port_connectivity(section=port_section)
        if self.mode == DynamicSimulationMode.EMT:
            self._validate_emt_phase_consistency(section=phase_section)
        else:
            pass

        sections: list[ValidationSection] = list([
            equation_section,
            duplicate_section,
            parameter_section,
            init_section,
            port_section,
        ])

        if self.mode == DynamicSimulationMode.EMT and len(phase_section.get_rows()) > 0:
            sections.append(phase_section)
        else:
            pass

        return sections

    def show_model_consistency_validation(self) -> None:
        """
        Show the current non-blocking model consistency report.

        :return: None.
        """
        # The dialog is informational only. It must never stop the save path, so
        # the method only gathers messages and shows them in one modal report.
        section_results: list[ValidationSection] = self.collect_model_consistency_sections()
        dialog: ValidationSectionDialog = ValidationSectionDialog(section_results=section_results, parent=self)
        dialog.exec()

    def _iter_scene_block_items(self) -> list[BlockItem | GenericBlockItem]:
        """
        Return the visible scene items that support validation highlighting.

        :return: Scene block items.
        """
        scene_block_items: list[BlockItem | GenericBlockItem] = list()
        scene_item: Any

        # Validation highlighting must cover both full generic blocks and the
        # compact connection/interface blocks because the validation report can
        # point to either one when a port is left disconnected.
        for scene_item in self.scene.items():
            if isinstance(scene_item, (BlockItem, GenericBlockItem)):
                scene_block_items.append(scene_item)
            else:
                pass

        return scene_block_items

    def clear_validation_issue_overlay(self) -> None:
        """
        Clear the current validation overlay from blocks and ports.

        :return: None.
        """
        scene_block_item: BlockItem | GenericBlockItem
        port_item: PortItem

        # The overlay is transient GUI state. It must be fully reset before a
        # new overlay is applied and whenever the model changes afterwards.
        for scene_block_item in self._iter_scene_block_items():
            scene_block_item.set_validation_highlighted(False)

            for port_item in scene_block_item.inputs:
                port_item.set_validation_highlighted(False)

            for port_item in scene_block_item.outputs:
                port_item.set_validation_highlighted(False)

        self._validation_issue_overlay_active = False

    def _find_scene_block_item_by_validation_label(self, block_label: str) -> BlockItem | GenericBlockItem | None:
        """
        Resolve one validation block label to its visible scene block item.

        :param block_label: Validation block label.
        :return: Matching scene block item or ``None``.
        """
        scene_block_item: BlockItem | GenericBlockItem
        formatted_label: str

        # Validation rows use the same stable block label formatter as the model
        # traversal, so the scene lookup can remain string-based and local.
        for scene_block_item in self._iter_scene_block_items():
            if isinstance(scene_block_item, ProtectedConnectionBlockItem) and scene_block_item.name == block_label:
                return scene_block_item
            else:
                pass

            if scene_block_item.subsys is not None:
                node_data: Any | None = self.diagram.node_data.get(scene_block_item.subsys.uid, None)
            else:
                node_data = None

            if node_data is not None and getattr(node_data, "name", None) == block_label:
                return scene_block_item
            else:
                pass

            formatted_label = format_validation_block_label(scene_block_item.subsys)
            if formatted_label == block_label:
                return scene_block_item
            elif scene_block_item.subsys.name == block_label:
                return scene_block_item
            elif getattr(scene_block_item, "name", None) == block_label:
                return scene_block_item
            elif getattr(scene_block_item, "name_item", None) is not None and \
                    scene_block_item.name_item.toPlainText() == block_label:
                return scene_block_item
            else:
                pass

        return None

    def _highlight_ports_by_name(self, scene_block_item: BlockItem | GenericBlockItem, port_names: set[str]) -> bool:
        """
        Highlight the ports whose variable names match the validation report.

        :param scene_block_item: Scene block item that owns the candidate ports.
        :param port_names: Port names to highlight.
        :return: Whether at least one port was highlighted.
        """
        highlighted_any_port: bool = False
        port_item: PortItem
        port_var: Var | None
        tooltip_text: str
        tooltip_name: str | None

        # Connection/interface blocks represent a single exported connection
        # variable. When such a row is reported by the validator, the visible
        # meaning for the user is simply "this exposed connector is wrong", so
        # all visible ports on that compact block are highlighted directly.
        if isinstance(scene_block_item, ProtectedConnectionBlockItem):
            reference_var: Var | None = None

            if scene_block_item.subsys is not None:
                if len(scene_block_item.subsys.out_vars) > 0:
                    reference_var = scene_block_item.subsys.out_vars[0]
                elif len(scene_block_item.subsys.in_vars) > 0:
                    reference_var = scene_block_item.subsys.in_vars[0]
                else:
                    reference_var = None
            else:
                reference_var = None

            if reference_var is not None and reference_var.name in port_names:
                pass
            else:
                return False

            for port_item in scene_block_item.inputs:
                if port_item.isVisible():
                    port_item.set_validation_highlighted(True)
                    highlighted_any_port = True
                else:
                    pass

            for port_item in scene_block_item.outputs:
                if port_item.isVisible():
                    port_item.set_validation_highlighted(True)
                    highlighted_any_port = True
                else:
                    pass

            if not highlighted_any_port:
                for port_item in scene_block_item.inputs:
                    port_item.set_validation_highlighted(True)
                    highlighted_any_port = True

                for port_item in scene_block_item.outputs:
                    port_item.set_validation_highlighted(True)
                    highlighted_any_port = True
            else:
                pass

            return highlighted_any_port
        else:
            pass

        # Port connectivity issues are projected back using the visible symbolic
        # variable names already shown in the editor and in the validation text.
        # Connection/interface items sometimes expose the name more reliably in
        # the tooltip than in the direct variable lookup, so both sources are
        # checked before deciding that a port does not match.
        for port_item in scene_block_item.inputs:
            port_var = port_item.base_var
            tooltip_text = port_item.toolTip()
            tooltip_name = tooltip_text.split(": ", 1)[1] if ": " in tooltip_text else None

            if (port_var is not None and port_var.name in port_names) or \
                    (tooltip_name is not None and tooltip_name in port_names):
                port_item.set_validation_highlighted(True)
                highlighted_any_port = True
            else:
                pass

        for port_item in scene_block_item.outputs:
            port_var = port_item.base_var
            tooltip_text = port_item.toolTip()
            tooltip_name = tooltip_text.split(": ", 1)[1] if ": " in tooltip_text else None

            if (port_var is not None and port_var.name in port_names) or \
                    (tooltip_name is not None and tooltip_name in port_names):
                port_item.set_validation_highlighted(True)
                highlighted_any_port = True
            else:
                pass

        return highlighted_any_port

    def _highlight_ports_by_ref(self,
                                scene_block_item: BlockItem | GenericBlockItem,
                                port_refs: set[VarPowerFlowReferenceType]) -> bool:
        """
        Highlight ports whose semantic references match the validation report.

        :param scene_block_item: Scene block item that owns the candidate ports.
        :param port_refs: Port references to highlight.
        :return: Whether at least one port was highlighted.
        """
        highlighted_any_port: bool = False
        port_item: PortItem
        port_reference: VarPowerFlowReferenceType | None
        candidate_refs: set[VarPowerFlowReferenceType]
        mapped_input_item: ProtectedConnectionBlockItem | None
        mapped_output_item: ProtectedConnectionBlockItem | None

        candidate_refs = set(port_refs)

        if isinstance(scene_block_item, ProtectedConnectionBlockItem) and self.mode == DynamicSimulationMode.EMT:
            interface_inputs_by_ref: Dict[VarPowerFlowReferenceType, ProtectedConnectionBlockItem] = dict()
            interface_outputs_by_ref: Dict[VarPowerFlowReferenceType, ProtectedConnectionBlockItem] = dict()
            scene_item: QGraphicsItem
            protected_item: ProtectedConnectionBlockItem
            reference_var: Var | None

            for scene_item in self.scene.items():
                if isinstance(scene_item, ProtectedConnectionBlockItem):
                    protected_item = scene_item
                    reference_var = None

                    if protected_item.subsys is not None:
                        if len(protected_item.subsys.out_vars) > 0:
                            reference_var = protected_item.subsys.out_vars[0]
                            if isinstance(reference_var.ref, VarPowerFlowReferenceType):
                                interface_inputs_by_ref[reference_var.ref] = protected_item
                        elif len(protected_item.subsys.in_vars) > 0:
                            reference_var = protected_item.subsys.in_vars[0]
                            if isinstance(reference_var.ref, VarPowerFlowReferenceType):
                                interface_outputs_by_ref[reference_var.ref] = protected_item
                        else:
                            pass
                    else:
                        pass
                else:
                    pass

            source_ref: VarPowerFlowReferenceType
            for source_ref in list(port_refs):
                mapped_input_item = self._get_editor_interface_input_item_for_ref(
                    interface_inputs_by_ref=interface_inputs_by_ref,
                    model_ref=source_ref,
                )
                if mapped_input_item is not None and mapped_input_item.subsys is not None and len(mapped_input_item.subsys.out_vars) > 0:
                    mapped_ref = get_var_reference(var=mapped_input_item.subsys.out_vars[0])
                    if mapped_ref is not None:
                        candidate_refs.add(mapped_ref)
                    else:
                        pass
                else:
                    pass

                mapped_output_item = self._get_editor_interface_output_item_for_ref(
                    interface_outputs_by_ref=interface_outputs_by_ref,
                    model_ref=source_ref,
                )
                if mapped_output_item is not None and mapped_output_item.subsys is not None and len(mapped_output_item.subsys.in_vars) > 0:
                    mapped_ref = get_var_reference(var=mapped_output_item.subsys.in_vars[0])
                    if mapped_ref is not None:
                        candidate_refs.add(mapped_ref)
                    else:
                        pass
                else:
                    pass
        else:
            pass

        if isinstance(scene_block_item, ProtectedConnectionBlockItem):
            reference_var: Var | None = None

            if scene_block_item.subsys is not None:
                if len(scene_block_item.subsys.out_vars) > 0:
                    reference_var = scene_block_item.subsys.out_vars[0]
                elif len(scene_block_item.subsys.in_vars) > 0:
                    reference_var = scene_block_item.subsys.in_vars[0]
                else:
                    reference_var = None
            else:
                reference_var = None

            if reference_var is None:
                return False

            reference_var_ref = get_var_reference(var=reference_var)
            if reference_var_ref not in candidate_refs:
                return False

            for port_item in scene_block_item.inputs:
                if port_item.isVisible():
                    port_item.set_validation_highlighted(True)
                    highlighted_any_port = True
                else:
                    pass

            for port_item in scene_block_item.outputs:
                if port_item.isVisible():
                    port_item.set_validation_highlighted(True)
                    highlighted_any_port = True
                else:
                    pass

            if not highlighted_any_port:
                for port_item in scene_block_item.inputs:
                    port_item.set_validation_highlighted(True)
                    highlighted_any_port = True

                for port_item in scene_block_item.outputs:
                    port_item.set_validation_highlighted(True)
                    highlighted_any_port = True
            else:
                pass

            return highlighted_any_port
        else:
            pass

        for port_item in scene_block_item.inputs:
            if port_item.base_var is None:
                continue

            port_reference = get_var_reference(var=port_item.base_var)
            if port_reference in port_refs:
                port_item.set_validation_highlighted(True)
                highlighted_any_port = True
            else:
                pass

        for port_item in scene_block_item.outputs:
            if port_item.base_var is None:
                continue

            port_reference = get_var_reference(var=port_item.base_var)
            if port_reference in port_refs:
                port_item.set_validation_highlighted(True)
                highlighted_any_port = True
            else:
                pass

        return highlighted_any_port

    def show_validation_issues_in_model(self, section_results: list[ValidationSection]) -> None:
        """
        Apply one transient validation overlay to the current scene.

        :param section_results: Validation sections describing the current issues.
        :return: None.
        """
        build_validation_row_highlight_metadata(section_results=section_results)
        self.clear_validation_issue_overlay()

        section: ValidationSection
        row: ValidationRow
        scene_block_item: BlockItem | GenericBlockItem | None
        highlighted_any_port: bool

        # The overlay keeps port-level connectivity issues more specific than the
        # generic block-border fallback used for all other validation failures.
        for section in section_results:
            for row in section.get_rows():
                scene_block_item = self._find_scene_block_item_by_validation_label(block_label=row.get_block_label())

                if scene_block_item is None:
                    pass
                else:
                    highlighted_any_port = False

                    if len(row.get_highlight_port_refs()) > 0:
                        highlighted_any_port = self._highlight_ports_by_ref(
                            scene_block_item=scene_block_item,
                            port_refs=row.get_highlight_port_refs(),
                        )
                    else:
                        pass

                    if not highlighted_any_port and len(row.get_highlight_port_names()) > 0:
                        highlighted_any_port = self._highlight_ports_by_name(
                            scene_block_item=scene_block_item,
                            port_names=row.get_highlight_port_names(),
                        )
                    else:
                        pass

                    if row.get_highlight_block() or not highlighted_any_port:
                        scene_block_item.set_validation_highlighted(True)
                    else:
                        pass

        self._highlight_connectivity_issue_ports_globally(section_results=section_results)

        self._validation_issue_overlay_active = True

    def _highlight_connectivity_issue_ports_globally(self, section_results: list[ValidationSection]) -> None:
        """
        Highlight visible ports referenced by Port Connectivity across the scene.

        :param section_results: Validation sections describing the current issues.
        :return: None.
        """
        section: ValidationSection
        row: ValidationRow
        scene_block_item: BlockItem | GenericBlockItem
        port_item: PortItem
        port_var: Var | None
        port_ref: VarPowerFlowReferenceType | None
        tooltip_text: str
        tooltip_name: str | None
        port_refs: set[VarPowerFlowReferenceType] = set()
        port_names: set[str] = set()

        for section in section_results:
            if section.get_title() != "Port Connectivity":
                continue

            for row in section.get_rows():
                port_refs.update(row.get_highlight_port_refs())
                port_names.update(row.get_highlight_port_names())

        if len(port_refs) == 0 and len(port_names) == 0:
            return
        else:
            pass

        # The per-row highlighting path can miss visible ports when one
        # connectivity issue is attached to one wrapper/root row but the user
        # expects every matching scene port to light up. This global pass keeps
        # the algorithm generic by scanning every visible in/out port directly
        # against the collected validation names and refs.
        for scene_block_item in self._iter_scene_block_items():
            all_ports: list[PortItem] = list()
            for port_item in scene_block_item.inputs:
                all_ports.append(port_item)
            for port_item in scene_block_item.outputs:
                all_ports.append(port_item)

            for port_item in all_ports:
                port_var = port_item.base_var

                if port_var is not None:
                    port_ref = get_var_reference(var=port_var)
                else:
                    port_ref = None

                tooltip_text = port_item.toolTip()
                if ": " in tooltip_text:
                    tooltip_name = tooltip_text.split(": ", 1)[1]
                else:
                    tooltip_name = None

                if port_ref is not None and port_ref in port_refs:
                    port_item.set_validation_highlighted(True)
                else:
                    if port_var is not None and port_var.name in port_names:
                        port_item.set_validation_highlighted(True)
                    else:
                        if tooltip_name is not None and tooltip_name in port_names:
                            port_item.set_validation_highlighted(True)
                        else:
                            pass

    def rebuild_scene_from_diagram(self) -> None:
        """
        Rebuild the visible scene from the persisted block diagram.

        :return:
        """
        uid_to_blockitem: Dict[
            int, BlockItem | GenericBlockItem | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem] = dict()
        uid: int
        node: Any
        con: Any

        self.close_child_editor_windows()
        self.scene.clear()

        # Recreate nodes
        signal_in_items: Dict[str, PairedItem] = {}
        signal_out_items: Dict[str, PairedItem] = {}

        for uid, node in self.diagram.node_data.items():
            block_type: BlockType | None
            block_model: Block | None = self.get_block_from_main_block(node.device_uid)

            if node.tpe in BlockType.__members__:
                block_type = BlockType[node.tpe]
            else:
                block_type = None

            if block_model is not None:

                if block_type == BlockType.INPUT_CONN or block_type == BlockType.OUTPUT_CONN:
                    block_item: ProtectedConnectionBlockItem = ProtectedConnectionBlockItem(editor=self,
                                                                                            var_factory=self.var_factory,
                                                                                            name=node.name,
                                                                                            )
                    block_item.set_subsystem(block_model)
                    block_item.position_changed_callback = self._build_position_changed_callback(block_model.uid)
                    block_item.build_item()

                    self.scene.addItem(block_item)
                    block_item.setPos(QPointF(node.x, node.y))

                    brush: QBrush = block_item.brush()
                    brush.setColor(QColor(node.color))
                    block_item.setBrush(brush)
                    uid_to_blockitem[uid] = block_item

                    if block_type is not None:
                        current_count: int = self.block_counters.get(block_type, 0) + 1
                        self.block_counters[block_type] = current_count
                    else:
                        pass

                else:
                    if node.tpe in ("signal_in", "signal_out"):
                        item = PairedItem(editor=self,
                                          var_factory=self.var_factory,
                                          subsys=block_model,
                                          api_object=self.api_object,
                                          mode=self.mode,
                                          name=block_model.name,
                                          position_changed_callback=self._build_position_changed_callback(
                                              block_model.uid)
                                          )
                        suffix = block_model.name.replace("From_", "").replace("To_", "")
                        if node.tpe == "signal_in":
                            signal_in_items[suffix] = item
                        else:
                            signal_out_items[suffix] = item
                    else:
                        item = GenericBlockItem(
                            editor=self,
                            var_factory=self.var_factory,
                            subsys=block_model,
                            api_object=self.api_object,
                            mode=self.mode,
                            name=block_model.name,
                            position_changed_callback=self._build_position_changed_callback(block_model.uid)
                        )
                    self.scene.addItem(item)
                    item.setPos(QPointF(node.x, node.y))

                    if not isinstance(item, PairedItem):
                        brush = item.brush()
                        brush.setColor(QColor(node.color))
                        item.setBrush(brush)

                    uid_to_blockitem[uid] = item

        # Pair signal_in and signal_out items
        for suffix, in_item in signal_in_items.items():
            out_item = signal_out_items.get(suffix)
            if out_item is not None:
                in_item.set_paired_item(out_item)
                out_item.set_paired_item(in_item)
        # Recreate connections
        for uid, con in self.diagram.con_data.items():
            src_item: BlockItem | None = uid_to_blockitem.get(con.from_uid, None)
            dst_item: BlockItem | None = uid_to_blockitem.get(con.to_uid, None)
            src_port: PortItem | None = None
            dst_port: PortItem | None = None

            if src_item is not None and dst_item is not None:
                try:
                    src_port = src_item.outputs[con.port_number_from]
                    dst_port = dst_item.inputs[con.port_number_to]
                except IndexError:
                    src_port = None
                    dst_port = None

                if src_port is not None and dst_port is not None:
                    elbow_points: List[QPointF] = [QPointF(x, y) for x, y in
                                                   con.elbow_points] if con.elbow_points else []
                    connection: ConnectionItem = ConnectionItem(
                        src_port, dst_port,
                        diagram=self.diagram,
                        con_uid=uid,
                        elbow_points=elbow_points,
                        editor=self,
                    )

                    pen: QPen = connection.pen()
                    pen.setColor(QColor(con.color))
                    connection.setPen(pen)
                    self.scene.addItem(connection)
                else:
                    pass
            else:
                pass

        if self.mode == DynamicSimulationMode.EMT and self.main_editor:
            visible_non_interface_items: list[GenericBlockItem] = self._collect_non_interface_scene_items()
            self._rebuild_visible_symbolic_connections(visible_non_interface_items)
            self._rebuild_editor_interface_graphical_connections(visible_non_interface_items)
        else:
            pass

        # Refresh connection-status color on all BlockItem instances
        for block_item in uid_to_blockitem.values():
            if isinstance(block_item, BlockItem):
                block_item._refresh_connection_color()

    def mark_unapplied_changes(self) -> None:
        """
        Mark the editor state as modified with unapplied changes.

        :return:
        """
        if self._validation_issue_overlay_active:
            self.clear_validation_issue_overlay()
        else:
            pass

        self.has_unapplied_changes = True
        self.changes_applied = False
        self.dirtyStateChanged.emit(True)

    def get_dynamic_editor_display_title(self) -> str:
        """
        Return the user-facing title for this editor instance.

        :return: Visible title for the workspace tab and window.
        """

        object_name = self.api_object.name if self.api_object is not None else "Dynamic object"
        return f"{object_name} [{self.mode.name}]"

    def get_dynamic_editor_entry(self) -> DynamicEditorEntry | None:
        """
        Return the workspace entry associated with this editor page.

        :return: Dynamic-editor entry or ``None`` when none is assigned.
        """
        return self.dynamic_editor_entry

    def set_dynamic_editor_entry(self, entry: DynamicEditorEntry | None) -> None:
        """
        Store the workspace entry associated with this editor page.

        :param entry: Dynamic-editor entry assigned by the workspace session.
        :return: None.
        """
        self.dynamic_editor_entry = entry

    def get_dynamic_editor_mode(self) -> DynamicSimulationMode:
        """
        Return the workspace mode associated with this editor page.

        :return: Dynamic simulation mode for this page.
        """
        return self.mode

    def can_close_editor(self, parent: QtWidgets.QWidget | None = None) -> bool:
        """
        Return whether this editor can be closed without losing unapplied changes silently.
        """

        if not self.has_unapplied_changes:
            return True

        reply = QtWidgets.QMessageBox.question(
            parent if parent is not None else self,
            "Unsaved changes",
            "There are unapplied changes. Do you want to close without applying them?",
            QtWidgets.QMessageBox.StandardButton.Yes,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        return reply == QtWidgets.QMessageBox.StandardButton.Yes

    def disconnect_editor_signals(self) -> None:
        """
        Disconnect long-lived UI signals before the editor gets destroyed.

        :return: None.
        """
        try:
            self.ui.toolBox.currentChanged.disconnect(self.handle_side_panel_page_changed)
        except (RuntimeError, TypeError):
            pass

        try:
            self.scene.selectionChanged.disconnect(self.on_scene_selection_changed)
        except (RuntimeError, TypeError):
            pass

    def close_child_editor_windows(self) -> None:
        """
        Close any floating child editors opened from block items in this scene.

        :return: None.
        """
        scene_item: QtWidgets.QGraphicsItem
        for scene_item in list(self.scene.items()):
            if isinstance(scene_item, (BlockItem, GenericBlockItem)):
                scene_item.close_editor_window()
            else:
                pass

    def prepare_to_delete(self) -> None:
        """
        Release editor-owned Qt objects before deleting this editor widget.

        :return: None.
        """
        if self._prepared_to_delete:
            return

        self._prepared_to_delete = True
        self.close_child_editor_windows()
        self.disconnect_editor_signals()
        self.scene.clear()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Close the editor. Ask for confirmation when there are unapplied changes.

        :param event:
        :return:
        """
        if self._prepared_to_delete:
            event.accept()
            return

        if self.can_close_editor(self):
            self.prepare_to_delete()
            event.accept()
        else:
            event.ignore()

    def graphicsDragEnterEvent(self, event: QDragEnterEvent) -> None:
        """
        Validate whether the drag entering the graphics view contains a block entry.

        :param event:
        :return:
        """
        payload: BlockType | BasicBlockTemplateDescriptor | RmsModelTemplate | EmtModelTemplate | FmuTemplate | None = self.get_library_payload_from_mime_data(
            event.mimeData()
        )

        if payload is not None:
            event.acceptProposedAction()
        else:
            event.ignore()

    def graphicsDragMoveEvent(self, event: QDragMoveEvent) -> None:
        """
        Keep the drag active while the payload remains a valid block entry.

        :param event:
        :return:
        """
        payload: BlockType | BasicBlockTemplateDescriptor | RmsModelTemplate | EmtModelTemplate | FmuTemplate | None = self.get_library_payload_from_mime_data(
            event.mimeData()
        )

        if payload is not None:
            event.acceptProposedAction()
        else:
            event.ignore()

    def graphicsDropEvent(self, event: QDropEvent) -> None:
        """
        Create a dropped block in scene coordinates.

        :param event:
        :return:
        """
        payload: BlockType | BasicBlockTemplateDescriptor | RmsModelTemplate | EmtModelTemplate | FmuTemplate | None = self.get_library_payload_from_mime_data(
            event.mimeData()
        )
        scene_position: QtCore.QPointF = self.ui.graphicsView.mapToScene(
            int(event.position().x()),
            int(event.position().y())
        )
        block_item: BlockItem | None | GenericBlockItem | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem

        if payload is not None:

            block_item = self.create_library_payload_item(
                payload=payload,
                x_pos=scene_position.x(),
                y_pos=scene_position.y(),
            )
            if block_item is not None:
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def set_dark_mode(self):
        """
        Set the dark mode
        :return:
        """
        for item in self.scene.items():
            if isinstance(item, (GenericBlockItem, PairedItem, ConnectionItem, RectBaseArithmeticOpItem, RoundBaseArithmeticOpItem)):
                item.set_dark_mode()




    def set_light_mode(self):
        """
        Set the dark mode
        :return:
        """
        for item in self.scene.items():
            if isinstance(item, (GenericBlockItem, PairedItem, ConnectionItem, RectBaseArithmeticOpItem,RoundBaseArithmeticOpItem)):
                item.set_light_mode()



if __name__ == "__main__":
    import sys
    import VeraGridEngine.Devices as dev

    app = QtWidgets.QApplication(sys.argv)

    vf = VarFactory()
    bl = Block()
    device = dev.Generator()
    window = DynamicBlockEditorGUI(
        var_factory=vf,
        block=bl,
        api_object=device,
        circuit=MultiCircuit(),
    )
    window.show()
    app.exec_()
