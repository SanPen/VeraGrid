# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import math
import uuid
import re
import copy
from enum import Enum
from typing import List, Dict, Optional, Any, Set, TypeAlias, cast
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QGraphicsScene, QGraphicsView, QGraphicsItem,
                               QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsPolygonItem,
                               QGraphicsTextItem, QMenu, QGraphicsPathItem,
                               QDialog, QVBoxLayout, QDialogButtonBox, QLabel, QListWidget, QWidget, QScrollArea,
                               QListWidgetItem, QFormLayout, QSpinBox, QLineEdit, QDoubleSpinBox, QTableWidget,
                               QTableWidgetItem, QMessageBox,
                               QColorDialog, QPlainTextEdit, QCheckBox)
from PySide6.QtGui import (QPen, QBrush, QPainterPath, QAction, QPainter,
                           QDropEvent, QDragEnterEvent, QDragMoveEvent, QColor)
from PySide6.QtCore import Qt, QPointF, Signal

from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Branches.overhead_line_type import OverheadLineType
from VeraGridEngine.Devices.Branches.sequence_line_type import SequenceLineType
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.Branches.transformer_type import TransformerType
from VeraGridEngine.Devices.Branches.underground_line_type import UndergroundLineType
from VeraGridEngine.Devices.Injections.controllable_shunt import ControllableShunt
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Injections.shunt import Shunt
from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType, ParamPowerFlowReferenceType, \
    DynamicSimulationMode, ShuntConnectionType, WindingType, DynamicTableModelMode
from VeraGridEngine.Utils.Symbolic.bus_rms_template import initialize_bus_rms, get_bus_rms_algebraic_vars
from VeraGridEngine.Utils.Symbolic.bus_emt_template import BusEmtTemplate, get_bus_emt_template, get_bus_emt_algebraic_vars
from VeraGridEngine.Utils.Symbolic.templates_common_functions import register_saved_emt_model_vars_for_device, \
    unify_saved_emt_model_root_contract, attach_emt_model_to_buses
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.fmu_template import FmuTemplate
from VeraGridEngine.Templates.predefined_blocks import signal_pair
from VeraGridEngine.Templates.BasicBlockCatalog import BasicBlockTemplateDescriptor
from VeraGridEngine.Templates.BasicBlockCatalog import get_editor_ready_basic_block_catalog_descriptors
from VeraGridEngine.Templates.BasicBlockCatalog import load_basic_block_catalog_template
from VeraGridEngine.Templates.BasicBlockCatalog.catalog import build_basic_block_catalog_branch_skeleton
from VeraGridEngine.Templates.BasicBlockCatalog.lookup_array_runtime_templates import build_lookup_array_linear_runtime_template
from VeraGridEngine.Templates.BasicBlockCatalog.lookup_array_runtime_templates import build_inverse_lookup_array_linear_runtime_template
from VeraGridEngine.Templates.BasicBlockCatalog.lookup_array_runtime_templates import build_lookup_matrix_linear_runtime_template
from VeraGridEngine.Templates.BasicBlockCatalog.lookup_array_runtime_templates import build_lookup_array_spline_runtime_template
from VeraGridEngine.Templates.BasicBlockCatalog.lookup_array_runtime_templates import build_lookup_matrix_spline_runtime_template
from VeraGridEngine.Templates.Emt.load_exponential_emt_template import get_exponential_load_emt
from VeraGridEngine.Templates.Emt.dc_source_emt_template import get_controlled_dc_current_source_emt_template
from VeraGridEngine.Templates.Emt.dc_source_emt_template import get_controlled_dc_voltage_source_emt_template
from VeraGridEngine.Templates.Emt.dc_source_emt_template import get_dc_current_source_emt_template
from VeraGridEngine.Templates.Emt.dc_source_emt_template import get_dc_voltage_source_emt_template
from VeraGridEngine.Templates.Emt.balanced_source_emt_template import get_balanced_3ph_current_source_emt_template
from VeraGridEngine.Templates.Emt.balanced_source_emt_template import get_balanced_3ph_voltage_source_emt_template
from VeraGridEngine.Templates.Emt.balanced_source_emt_template import get_controlled_balanced_3ph_current_source_emt_template
from VeraGridEngine.Templates.Emt.balanced_source_emt_template import get_controlled_balanced_3ph_voltage_source_emt_template
from VeraGridEngine.Templates.Emt.arbitrary_source_emt_template import get_arbitrary_waveform_current_source_emt_template
from VeraGridEngine.Templates.Emt.arbitrary_source_emt_template import get_arbitrary_waveform_voltage_source_emt_template
from VeraGridEngine.Templates.Emt.transient_source_emt_template import get_cigre_surge_current_source_emt_template
from VeraGridEngine.Templates.Emt.transient_source_emt_template import get_double_exponential_current_source_emt_template
from VeraGridEngine.Templates.Emt.transient_source_emt_template import get_heidler_current_source_emt_template
from VeraGridEngine.Templates.Emt.transient_source_emt_template import get_ramp_current_source_emt_template
from VeraGridEngine.Templates.Emt.transient_source_emt_template import get_ramp_voltage_source_emt_template
from VeraGridEngine.Templates.Emt.transient_source_emt_template import get_step_current_source_emt_template
from VeraGridEngine.Templates.Emt.transient_source_emt_template import get_step_voltage_source_emt_template
from VeraGridEngine.Templates.Emt.load_RLC_emt_template import get_grounding_link_emt_template
from VeraGridEngine.Templates.Emt.nonlinear_resistor_emt_template import get_nonlinear_resistor_emt_template
from VeraGridEngine.Templates.Emt.source_emt_template import get_controlled_current_source_emt_template
from VeraGridEngine.Templates.Emt.source_emt_template import get_controlled_voltage_source_emt_template
from VeraGridEngine.Templates.Emt.source_emt_template import get_current_source_emt_template
from VeraGridEngine.Templates.Emt.source_emt_template import get_voltage_source_emt_template
from VeraGridEngine.Templates.Emt.switch_emt_template import get_switch_emt_template
from VeraGridEngine.Templates.Emt.fault_emt_template import get_fault_emt_template
from VeraGridEngine.Templates.Emt.induction_motor_emt_template import get_induction_motor_emt_template
from VeraGridEngine.Templates.Emt.load_RLC_emt_template import get_shunt_rlc_combo_emt_template
from VeraGridEngine.Templates.Emt.load_zip_emt_template import get_load_ZIP_emt_template
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Utils.Symbolic.block import Block, find_connections, find_connections_pf
from VeraGridEngine.Utils.Symbolic.equation_decomposer import EquationDecomposer, build_diagram, build_diagram_regular_blocks
from VeraGridEngine.Utils.Symbolic.hierarchical_layout_v2 import compute_layout as _compute_layout_v2
from VeraGrid.Gui.DynamicModelEditor.block_editor import Ui_BlockEditorWindow
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_utilities import create_block_of_type, create_generic_block, \
    create_emt_wizard_block
from VeraGrid.Gui.DynamicModelEditor.lookup_table_dialog import LookupArrayLinearDialog
from VeraGrid.Gui.DynamicModelEditor.lookup_table_dialog import LookupMatrixLinearDialog
from VeraGrid.Gui.DynamicModelEditor.grounding_link_emt_dialog import GroundingLinkEmtDialog
from VeraGrid.Gui.DynamicModelEditor.jmarti_line_emt_dialog import JMartiLineEmtDialog
from VeraGrid.Gui.DynamicModelEditor.induction_motor_emt_dialog import InductionMotorEmtDialog
from VeraGrid.Gui.DynamicModelEditor.induction_motor_emt_dialog import InductionMotorEmtLevel
from VeraGrid.Gui.DynamicModelEditor.induction_motor_emt_dialog import coerce_induction_motor_emt_level
from VeraGrid.Gui.DynamicModelEditor.induction_motor_emt_dialog import get_induction_motor_emt_level_label
from VeraGrid.Gui.DynamicModelEditor.induction_motor_emt_dialog import get_induction_motor_emt_template_level
from VeraGrid.Gui.DynamicModelEditor.load_topology_emt_dialog import LoadTopologyEmtDialog
from VeraGrid.Gui.DynamicModelEditor.rlc_combo_emt_dialog import RlcComboEmtDialog
from VeraGrid.Gui.DynamicModelEditor.shunt_component_emt_dialog import ShuntComponentEmtDialog
from VeraGrid.Gui.DynamicModelEditor.arbitrary_source_emt_dialog import ArbitrarySourceEmtDialog
from VeraGrid.Gui.DynamicModelEditor.balanced_source_emt_dialog import BalancedSourceEmtDialog
from VeraGrid.Gui.DynamicModelEditor.dc_source_emt_dialog import DcSourceEmtDialog
from VeraGrid.Gui.DynamicModelEditor.transient_source_emt_dialog import TransientSourceEmtDialog
from VeraGrid.Gui.DynamicModelEditor.source_emt_dialog import SourceEmtDialog
from VeraGrid.Gui.DynamicModelEditor.transformer_topology_emt_dialog import TransformerTopologyEmtDialog
from VeraGrid.Gui.DynamicModelEditor.switch_emt_dialog import SwitchEmtDialog
from VeraGrid.Gui.DynamicModelEditor.fault_emt_dialog import FaultEmtDialog
from VeraGrid.Gui.Icons.icon_associations import device_type_icons
from VeraGrid.Gui.wrappable_table_model import WrappableTableModel
from VeraGrid.Gui.gui_functions import ComboDelegate, TextDelegate
from VeraGrid.Gui.toast_widget import ToastManager
from VeraGridEngine.Utils.Symbolic.symbolic import (symbolic_to_string, string_to_symbolic,
                                                    get_symbolic_parser_function_names,
                                                    Expr, Var, Const, Comparison)
from VeraGridEngine.Utils.Symbolic.symbolic_io import duplicate_block
from VeraGridEngine.Devices.Diagrams.block_diagram import BlockDiagram
from VeraGridEngine.enumerations import BlockType, EmtFaultPlacementSide, FaultType
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_options import JMartiFitOptions
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_workflow import build_jmarti_fit_bundle_from_frequency_samples
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_workflow import build_jmarti_frequency_samples_from_line
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_workflow import load_jmarti_frequency_samples_from_npz
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_runtime import get_jmarti_block_fit_bundle
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_runtime import get_jmarti_block_runtime_data
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_runtime import set_jmarti_block_fit_bundle
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_runtime import set_jmarti_block_runtime_data
from dataclasses import dataclass

from VeraGridEngine.Utils.Symbolic.static_parameter_mapping import devices_static_params_mapping
import VeraGrid.ThirdParty.darkdetect as darkdetect

# from VeraGridEngine.Templates.Rms.common import create_block_of_type, create_generic_block, create_emt_wizard_block



BLOCK_BORDER: QColor = QColor("#36536b")
BLOCK_BORDER_SELECTED: QColor = QColor("#cc6f2c")
BLOCK_TITLE: QColor = QColor("#173042")
BLOCK_SHADOW: QColor = QColor(24, 42, 56, 45)
INPUT_PORT_FILL: QColor = QColor("#2d7dd2")
OUTPUT_PORT_FILL: QColor = QColor("#2a9d6f")
PORT_BORDER: QColor = QColor("#173042")
WIRE_COLOR: QColor = QColor("#587291")
WIRE_HOVER_COLOR: QColor = QColor("#cc6f2c")
HANDLE_FILL: QColor = QColor("#36536b")
DEFAULT_BLOCK_FILL: QColor = QColor("#d9e7f5")
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

def set_modal_template_metadata(block: Block, kind: str, config: Dict[str, Any]) -> None:
    """
    Persist the modal-builder metadata on one block.

    :param block: Target block.
    :param kind: Stable modal kind key.
    :param config: Serializable modal configuration.
    :return: None.
    """
    block.__dict__[MODAL_TEMPLATE_KIND_ATTR] = kind
    block.__dict__[MODAL_TEMPLATE_CONFIG_ATTR] = copy.deepcopy(config)


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


def get_modal_template_metadata(block: Block | None) -> tuple[str | None, Dict[str, Any] | None]:
    """
    Return the modal-builder metadata stored on one block.

    :param block: Candidate block.
    :return: `(kind, config)` or `(None, None)` when absent.
    """
    if block is None:
        return None, None
    else:
        pass

    kind: Any = block.__dict__.get(MODAL_TEMPLATE_KIND_ATTR, None)
    config: Any = block.__dict__.get(MODAL_TEMPLATE_CONFIG_ATTR, None)

    if isinstance(kind, str) and isinstance(config, dict):
        return kind, copy.deepcopy(config)
    else:
        return None, None


def _new_uid() -> int:
    """
    Generate a fresh integer identifier.

    :return:
    """
    return uuid.uuid4().int


def _grid_node_f_cost_sort_key(node: Any) -> float:
    """
    Return the A* sorting key for one grid node.

    :param node: Router grid node.
    :return: Node total cost.
    """
    return float(node.f_cost)


def _library_leaf_label_sort_key(leaf: "LibraryLeafSpec") -> str:
    """
    Return the case-insensitive sort key for one library leaf.

    :param leaf: Library leaf specification.
    :return: Lower-case label.
    """
    return leaf.label.lower()


def _transformer_modal_config_allows_modify(modal_kind: str | None, modal_config: Dict[str, Any] | None) -> bool:
    """
    Return whether one modal-created block should expose ``Modify Template``.

    Transformer EMT blocks whose topology is inherited automatically from the
    owning device or transformer type do not need a manual modify action because
    reopening the dialog would only duplicate information already owned by the
    host object.

    :param modal_kind: Stored modal kind.
    :param modal_config: Stored modal configuration.
    :return: ``True`` when the context action should be visible.
    """
    if modal_kind == "transformer_topology_emt" and isinstance(modal_config, dict):
        return bool(modal_config.get("allow_modify_template", True))
    else:
        return modal_kind is not None

def build_variables_rows(block: Block | None, rows: List[BlockParameterRow]):
    if block is not None:
        build_block_variables_rows(block, rows)
        if block.children:
            for child in block.children:
                build_variables_rows(child, rows)


def build_block_variables_rows(block: Block, rows: List[BlockParameterRow]):
    for var in block.state_vars:
        init_eq = block.init_eqs.get(var)
        rows.append(BlockParameterRow(
            name=var.name,
            kind=BlockParameterKind.STATE_VAR,
            key_var=var,
            value=block.init_values.get(var, ""),
            editable_name=True,
            editable_value=True,
            value_type=float,
            init_eq=init_eq
        ))

    for var in block.algebraic_vars:
        init_eq = block.init_eqs.get(var)
        rows.append(BlockParameterRow(
            name=var.name,
            kind=BlockParameterKind.ALGEBRAIC_VAR,
            key_var=var,
            value="",
            editable_name=True,
            editable_value=False,
            value_type=str,
            init_eq=init_eq
        ))


def build_parameters_rows(table_model, block: Block | None, rows: List[BlockParameterRow]):
    if block is not None:
        build_block_parameters_rows(table_model, block, rows)
        if block.children:
            for child in block.children:
                build_block_parameters_rows(table_model, child, rows)


def build_block_parameters_rows(table_model: Any, blk: Block, rows: List[BlockParameterRow]):
    for var, expr in blk.event_dict.items():
        if isinstance(expr, Const):
            rows.append(BlockParameterRow(
                name=var.name,
                kind=BlockParameterKind.EVENT_PARAMETER,
                key_var=var,
                value=expr.value,
                editable_name=True,
                editable_value=True,
                value_type=table_model.get_python_value_type(expr.value),
                source_dict_name="event_dict"
            ))
        else:
            rows.append(BlockParameterRow(
                name=var.name,
                kind=BlockParameterKind.EVENT_PARAMETER,
                key_var=var,
                value=expr,
                editable_name=True,
                editable_value=True,
                value_type=str,
                source_dict_name="event_dict"
            ))

    for var, expr in blk.mode_dict.items():
        if isinstance(expr, Const):
            rows.append(BlockParameterRow(
                name=var.name,
                kind=BlockParameterKind.MODE_PARAMETER,
                key_var=var,
                value=expr.value,
                editable_name=True,
                editable_value=True,
                value_type=table_model.get_python_value_type(expr.value),
                source_dict_name="mode_dict"
            ))
        else:
            rows.append(BlockParameterRow(
                name=var.name,
                kind=BlockParameterKind.MODE_PARAMETER,
                key_var=var,
                value=expr,
                editable_name=True,
                editable_value=True,
                value_type=str,
                source_dict_name="mode_dict"
            ))

    for var, const in blk.parameters.items():
        ref = var.ref
        rows.append(BlockParameterRow(
            name=var.name,
            kind=BlockParameterKind.FIXED_PARAMETER,
            key_var=var,
            value=ref.value if ref is not None else "",
            editable_name=True,
            editable_value=False,
            value_type=str,
            source_dict_name="parameters"
        ))

    return rows


def update_source_dict(block: Block | None, row: BlockParameterRow, value: Any, old_expr: Any = None) -> None:
    if block is not None and row is not None:
        update_param_value(block, row, value, old_expr)
        if block.children:
            for child in block.children:
                update_source_dict(child, row, value, old_expr)


def _parse_symbolic_editor_value(block: Block | None, value: Any) -> Any:
    """
    Convert inline editor text into a symbolic expression when editing symbolic fields.

    Table delegates may pass plain strings for inline edits, while block storage expects
    Expr-compatible objects in init/event/mode dictionaries.
    """
    if not isinstance(value, str) or block is None:
        if isinstance(value, (int, float)):
            return Const(value)
        return value

    parsed = string_to_symbolic(value, build_block_symbol_namespace(block))
    if isinstance(parsed, Comparison):
        return parsed.to_expression()
    return parsed


def update_param_value(blk: Block, row: BlockParameterRow, value: Any, old_expr: Any):
    if blk is not None and row is not None:
        if row.key_var is not None:
            if row.kind == BlockParameterKind.EVENT_PARAMETER:
                if row.key_var in blk.event_dict:
                    blk.event_dict[row.key_var] = value
            elif row.kind == BlockParameterKind.MODE_PARAMETER:
                if row.key_var in blk.mode_dict:
                    blk.mode_dict[row.key_var] = value
            elif row.kind == BlockParameterKind.FIXED_PARAMETER:
                if row.key_var in blk.parameters:
                    blk.parameters[row.key_var] = value
            elif row.kind == BlockParameterKind.STATE_VAR:
                if row.key_var in blk.init_eqs:
                    blk.init_eqs[row.key_var] = value
            elif row.kind == BlockParameterKind.ALGEBRAIC_VAR:
                if row.key_var in blk.init_eqs:
                    blk.init_eqs[row.key_var] = value
        if row.kind == BlockParameterKind.STATE_EQUATION and row.item_index is not None:
            if old_expr is not None and old_expr in blk.state_eqs:
                blk.state_eqs[row.item_index] = value
        elif row.kind == BlockParameterKind.ALGEBRAIC_EQUATION and row.item_index is not None:
            if old_expr is not None and old_expr in blk.algebraic_eqs:
                blk.algebraic_eqs[row.item_index] = value


def build_equations_rows(block: Block | None, rows):
    """

    :return:
    """
    if block is not None:
        build_block_equations_rows(block, rows)
        if block.children:
            for child in block.children:
                build_equations_rows(child, rows)


def build_block_equations_rows(blk: Block, rows: List[BlockParameterRow]):
    for idx, eq in enumerate(blk.state_eqs):
        rows.append(BlockParameterRow(
            name=f"State Eq {idx + 1}",
            kind=BlockParameterKind.STATE_EQUATION,
            key_var=None,
            value=eq,
            editable_name=False,
            editable_value=True,
            value_type=str,
            item_index=idx
        ))

    for idx, eq in enumerate(blk.algebraic_eqs):
        rows.append(BlockParameterRow(
            name=f"Algebraic Eq {idx + 1}",
            kind=BlockParameterKind.ALGEBRAIC_EQUATION,
            key_var=None,
            value=eq,
            editable_name=False,
            editable_value=True,
            value_type=str,
            item_index=idx
        ))


def collect_block_tree(root_block: Block) -> list[Block]:
    """
    Return one flat list with the root block and all descendants.

    :param root_block: Root block that owns the edited hierarchy.
    :return: Flat block list ordered by traversal.
    """
    # The validator needs one deterministic view of the whole edited hierarchy so
    # every child block is checked exactly once.
    collected_blocks: list[Block] = list([root_block])
    child_block: Block
    for child_block in root_block.children:
        collected_blocks.extend(collect_block_tree(root_block=child_block))
    return collected_blocks


def format_validation_block_label(block: Block) -> str:
    """
    Return one user-facing label for a block.

    :param block: Block to label.
    :return: Stable human-readable label.
    """
    # The report should prefer the symbolic block name because it is the same
    # identifier the user sees in the editor canvas.
    if block.name:
        return block.name
    else:
        return f"uid={block.uid}"


def get_var_reference(var: Var) -> VarPowerFlowReferenceType | None:
    """
    Return the power-flow reference attached to one symbolic variable.

    :param var: Symbolic variable to inspect.
    :return: External reference enum or ``None`` when absent.
    """
    # The validator only relies on the typed ``Var.ref`` attribute so the logic
    # stays explicit and refactorable without reflection helpers.
    if isinstance(var.ref, VarPowerFlowReferenceType):
        return var.ref
    else:
        return None


def append_vars_to_name_uid_map(name_to_uids: dict[str, set[int]], vars_list: list[Var]) -> None:
    """
    Merge one list of variables into the duplicate-name accumulator.

    :param name_to_uids: Mapping from variable name to the set of symbolic UIDs using it.
    :param vars_list: Variables to merge.
    :return: None.
    """
    # The duplicate-name rule is based on distinct symbolic variables. Reusing the
    # same Var object in multiple collections must therefore add the same UID only.
    var: Var
    for var in vars_list:
        uid_bucket: set[int] | None = name_to_uids.get(var.name, None)
        if uid_bucket is None:
            uid_bucket = set()
            name_to_uids[var.name] = uid_bucket
        else:
            pass
        uid_bucket.add(var.uid)


def append_port_vars_to_phase_count(phase_counts: dict[str, int], vars_list: list[Var]) -> None:
    """
    Count how many EMT interface variables belong to each phase.

    :param phase_counts: Mutable counter keyed by phase label.
    :param vars_list: Variables to inspect.
    :return: None.
    """
    # EMT phase validation needs the total number of ports per phase so it can
    # distinguish a fully absent phase from a partially disconnected one.
    var: Var
    for var in vars_list:
        reference: VarPowerFlowReferenceType | None = get_var_reference(var=var)
        phase_group: str | None = get_emt_phase_group(reference=reference)
        if phase_group is not None:
            phase_counts[phase_group] = phase_counts[phase_group] + 1
        else:
            pass


def append_missing_port_messages_for_direction(
        missing_port_messages: list[str],
        emt_missing_by_phase: dict[str, list[str]],
        vars_list: list[Var],
        node_uid: int,
        connected_ports: set[tuple[int, int]],
        is_input: bool,
        mode: DynamicSimulationMode,
) -> None:
    """
    Inspect one port direction and append missing-connection messages.

    :param missing_port_messages: Mutable generic message list.
    :param emt_missing_by_phase: Mutable EMT phase-bucketed message map.
    :param vars_list: Ordered port variables for one direction.
    :param node_uid: Diagram node UID owning the ports.
    :param connected_ports: Connected port lookup set for the inspected direction.
    :param is_input: Whether the inspected ports are inputs.
    :param mode: Editor dynamic mode.
    :return: None.
    """
    # Port checks are performed in port-index order because the saved diagram also
    # stores connectivity positionally.
    index: int
    var: Var
    direction_label: str = "input" if is_input else "output"

    for index, var in enumerate(vars_list):
        if (node_uid, index) in connected_ports:
            pass
        else:
            message: str = f"{direction_label} '{var.name}' is not connected"
            if mode == DynamicSimulationMode.EMT:
                reference: VarPowerFlowReferenceType | None = get_var_reference(var=var)
                phase_group: str | None = get_emt_phase_group(reference=reference)
                if phase_group is not None:
                    emt_missing_by_phase[phase_group].append(message)
                else:
                    missing_port_messages.append(message)
            else:
                missing_port_messages.append(message)


def format_missing_port_detail(input_names: list[str], output_names: list[str]) -> str:
    """
    Format one grouped port-connectivity detail line.

    :param input_names: Missing input port names.
    :param output_names: Missing output port names.
    :return: Human-readable grouped detail text. Returns an empty string when no
        missing ports exist.
    """
    # Grouping missing ports by direction keeps the modal compact and makes it
    # easier to scan one block without reading the same phrase repeatedly.
    detail_parts: list[str] = list()

    if input_names:
        if len(input_names) == 1:
            detail_parts.append(f"input: {input_names[0]} is not connected")
        else:
            detail_parts.append(f"inputs: {', '.join(input_names)} are not connected")
    else:
        pass

    if output_names:
        if len(output_names) == 1:
            detail_parts.append(f"output: {output_names[0]} is not connected")
        else:
            detail_parts.append(f"outputs: {', '.join(output_names)} are not connected")
    else:
        pass

    return "; ".join(detail_parts)


def append_emt_absent_phase_note(detail_parts: list[str], phase_name: str) -> None:
    """
    Append one human-readable note for an EMT phase that is fully absent.

    :param detail_parts: Mutable detail text parts.
    :param phase_name: EMT phase label.
    :return: None.
    """
    # A fully unconnected EMT phase is not an error in this editor workflow, but
    # the validator should still tell the user that the phase is effectively not
    # present in the model interface.
    detail_parts.append(
        f"phase {phase_name}: V and I are not connected, meaning this model has no phase {phase_name} wire"
    )


def format_emt_phase_connectivity_detail(
        input_names: list[str],
        output_names: list[str],
        absent_phase_names: list[str],
) -> str:
    """
    Format one EMT-specific connectivity detail line.

    :param input_names: Missing input port names.
    :param output_names: Missing output port names.
    :param absent_phase_names: Fully absent EMT phases.
    :return: Human-readable grouped detail text.
    """
    # EMT reports both true disconnections and intentionally absent phases so the
    # user can distinguish interface mistakes from deliberate phase omission.
    detail_parts: list[str] = list()
    phase_name: str

    grouped_detail: str = format_missing_port_detail(input_names=input_names, output_names=output_names)
    if grouped_detail:
        detail_parts.append(grouped_detail)
    else:
        pass

    for phase_name in absent_phase_names:
        append_emt_absent_phase_note(detail_parts=detail_parts, phase_name=phase_name)

    return "; ".join(detail_parts)


def get_phase_wire_description(phase_name: str) -> str:
    """
    Return one human-readable wire label for a phase.

    :param phase_name: Phase label.
    :return: Human-readable wire label used in the phase-consistency report.
    """
    if phase_name == "N":
        return "neutral wire"
    elif phase_name == "A":
        return "phase A"
    elif phase_name == "B":
        return "phase B"
    elif phase_name == "C":
        return "phase C"
    else:
        return f"phase {phase_name}"


def get_phase_table_label(phase_name: str) -> str:
    """
    Return the fixed table label for one EMT phase row.

    :param phase_name: Phase label.
    :return: Table label.
    """
    if phase_name == "N":
        return "Neutral"
    elif phase_name == "A":
        return "A"
    elif phase_name == "B":
        return "B"
    elif phase_name == "C":
        return "C"
    else:
        return phase_name


def get_branch_phase_table_label(side: str, phase_name: str) -> str:
    """
    Return the fixed table label for one EMT branch-side phase row.

    :param side: Branch side identifier.
    :param phase_name: Phase label.
    :return: Table label.
    """
    side_label: str = ""
    if side == "from":
        side_label = "bus from"
    elif side == "to":
        side_label = "bus to"
    else:
        side_label = side

    if phase_name == "N":
        return f"N {side_label}"
    elif phase_name == "A":
        return f"A {side_label}"
    elif phase_name == "B":
        return f"B {side_label}"
    elif phase_name == "C":
        return f"C {side_label}"
    else:
        return f"{phase_name} {side_label}"


def classify_emt_injection_phase_wire_from_refs(
        phase_name: str,
        refs: set[VarPowerFlowReferenceType],
) -> tuple[bool, str]:
    """
    Classify one EMT injection phase using the same logic as ``Do it!``.

    :param phase_name: Phase label.
    :param refs: Connected root-interface references.
    :return: Tuple ``(ok, detail)``.
    """
    # This helper intentionally mirrors the save-time EMT consistency check so the
    # validator modal and the ``Do it!`` workflow always report the same result.
    voltage_connected: bool = False
    current_connected: bool = False

    if phase_name == "N":
        voltage_connected = VarPowerFlowReferenceType.v_N in refs
        current_connected = VarPowerFlowReferenceType.i_N in refs
    elif phase_name == "A":
        voltage_connected = VarPowerFlowReferenceType.v_A in refs
        current_connected = VarPowerFlowReferenceType.i_A in refs
    elif phase_name == "B":
        voltage_connected = VarPowerFlowReferenceType.v_B in refs
        current_connected = VarPowerFlowReferenceType.i_B in refs
    elif phase_name == "C":
        voltage_connected = VarPowerFlowReferenceType.v_C in refs
        current_connected = VarPowerFlowReferenceType.i_C in refs
    else:
        pass

    wire_description: str = get_phase_wire_description(phase_name=phase_name)

    if voltage_connected == current_connected:
        if voltage_connected:
            return True, f"the model has this {wire_description}"
        else:
            return True, f"the model has no {wire_description}"
    elif voltage_connected:
        return False, f"inconsistent connection of {wire_description}, only V ports are connected"
    else:
        return False, f"inconsistent connection of {wire_description}, only I ports are connected"


def classify_emt_branch_phase_wire_from_refs(
        side: str,
        phase_name: str,
        refs: set[VarPowerFlowReferenceType],
) -> tuple[bool, str]:
    """
    Classify one EMT branch-side phase using the save-time branch logic.

    :param side: Branch side identifier.
    :param phase_name: Phase label.
    :param refs: Connected root-interface references.
    :return: Tuple ``(ok, detail)``.
    """
    # Branch EMT devices expose two independent AC-side wire contracts. Each side
    # must therefore be evaluated with its own V/I pair set.
    voltage_connected: bool = False
    current_connected: bool = False
    wire_description: str = get_phase_wire_description(phase_name=phase_name)
    side_description: str = "bus from" if side == "from" else "bus to"

    if side == "from":
        if phase_name == "N":
            voltage_connected = VarPowerFlowReferenceType.vf_N in refs
            current_connected = VarPowerFlowReferenceType.if_N in refs
        elif phase_name == "A":
            voltage_connected = VarPowerFlowReferenceType.vf_A in refs
            current_connected = VarPowerFlowReferenceType.if_A in refs
        elif phase_name == "B":
            voltage_connected = VarPowerFlowReferenceType.vf_B in refs
            current_connected = VarPowerFlowReferenceType.if_B in refs
        elif phase_name == "C":
            voltage_connected = VarPowerFlowReferenceType.vf_C in refs
            current_connected = VarPowerFlowReferenceType.if_C in refs
        else:
            pass
    elif side == "to":
        if phase_name == "N":
            voltage_connected = VarPowerFlowReferenceType.vt_N in refs
            current_connected = VarPowerFlowReferenceType.it_N in refs
        elif phase_name == "A":
            voltage_connected = VarPowerFlowReferenceType.vt_A in refs
            current_connected = VarPowerFlowReferenceType.it_A in refs
        elif phase_name == "B":
            voltage_connected = VarPowerFlowReferenceType.vt_B in refs
            current_connected = VarPowerFlowReferenceType.it_B in refs
        elif phase_name == "C":
            voltage_connected = VarPowerFlowReferenceType.vt_C in refs
            current_connected = VarPowerFlowReferenceType.it_C in refs
        else:
            pass
    else:
        pass

    if voltage_connected == current_connected:
        if voltage_connected:
            return True, f"the model has this {wire_description} on {side_description}"
        else:
            return True, f"the model has no {wire_description} on {side_description}"
    elif voltage_connected:
        return False, f"inconsistent connection of {wire_description} on {side_description}, only V ports are connected"
    else:
        return False, f"inconsistent connection of {wire_description} on {side_description}, only I ports are connected"


def has_ac_emt_phase_interface_refs(refs: set[VarPowerFlowReferenceType]) -> bool:
    """
    Return whether one EMT interface exposes AC phase references.

    :param refs: Root EMT interface references.
    :return: ``True`` when AC N/A/B/C phase references are present.
    """
    # Mixed AC/DC devices such as VSCs must still expose phase consistency when
    # the root interface contains any AC phase references, even if DC refs also exist.
    if (VarPowerFlowReferenceType.v_N in refs or VarPowerFlowReferenceType.i_N in refs or
            VarPowerFlowReferenceType.v_A in refs or VarPowerFlowReferenceType.i_A in refs or
            VarPowerFlowReferenceType.v_B in refs or VarPowerFlowReferenceType.i_B in refs or
            VarPowerFlowReferenceType.v_C in refs or VarPowerFlowReferenceType.i_C in refs or
            VarPowerFlowReferenceType.vf_N in refs or VarPowerFlowReferenceType.if_N in refs or
            VarPowerFlowReferenceType.vf_A in refs or VarPowerFlowReferenceType.if_A in refs or
            VarPowerFlowReferenceType.vf_B in refs or VarPowerFlowReferenceType.if_B in refs or
            VarPowerFlowReferenceType.vf_C in refs or VarPowerFlowReferenceType.if_C in refs or
            VarPowerFlowReferenceType.vt_N in refs or VarPowerFlowReferenceType.it_N in refs or
            VarPowerFlowReferenceType.vt_A in refs or VarPowerFlowReferenceType.it_A in refs or
            VarPowerFlowReferenceType.vt_B in refs or VarPowerFlowReferenceType.it_B in refs or
            VarPowerFlowReferenceType.vt_C in refs or VarPowerFlowReferenceType.it_C in refs):
        return True
    else:
        return False


def has_ac_emt_branch_side_refs(side: str, refs: set[VarPowerFlowReferenceType]) -> bool:
    """
    Return whether one EMT branch side exposes AC phase references.

    :param side: Branch side identifier.
    :param refs: Root EMT interface references.
    :return: ``True`` when the requested side exposes AC phase references.
    """
    # Mixed AC/DC branch devices may expose AC wires only on one side, so the
    # phase-consistency table must render only the side that actually has AC refs.
    if side == "from":
        if (VarPowerFlowReferenceType.vf_N in refs or VarPowerFlowReferenceType.if_N in refs or
                VarPowerFlowReferenceType.vf_A in refs or VarPowerFlowReferenceType.if_A in refs or
                VarPowerFlowReferenceType.vf_B in refs or VarPowerFlowReferenceType.if_B in refs or
                VarPowerFlowReferenceType.vf_C in refs or VarPowerFlowReferenceType.if_C in refs):
            return True
        else:
            return False
    elif side == "to":
        if (VarPowerFlowReferenceType.vt_N in refs or VarPowerFlowReferenceType.it_N in refs or
                VarPowerFlowReferenceType.vt_A in refs or VarPowerFlowReferenceType.it_A in refs or
                VarPowerFlowReferenceType.vt_B in refs or VarPowerFlowReferenceType.it_B in refs or
                VarPowerFlowReferenceType.vt_C in refs or VarPowerFlowReferenceType.it_C in refs):
            return True
        else:
            return False
    else:
        return False


class ValidationRow:
    """
    Row of validation output associated with one block.
    """

    __slots__ = ("_block_label", "_details", "_ok")

    def __init__(self, block_label: str) -> None:
        """
        Build one validation row.

        :param block_label: Human-readable block identifier.
        :return: None.
        """
        self._block_label: str = block_label
        self._details: list[str] = list()
        self._ok: bool = False

    def get_block_label(self) -> str:
        """
        Return the row block label.

        :return: Block label.
        """
        return self._block_label

    def get_details(self) -> list[str]:
        """
        Return the detail list.

        :return: Detail list.
        """
        return self._details

    def add_detail(self, detail: str) -> None:
        """
        Append one detail line to the row.

        :param detail: Detail to append.
        :return: None.
        """
        self._details.append(detail)

    def set_ok(self, val: bool) -> None:
        """
        Set the row semantic state.

        :param val: ``True`` when the row is informationally correct.
        :return: None.
        """
        self._ok = val

    def is_ok(self) -> bool:
        """
        Return the row semantic state.

        :return: ``True`` when the row is informationally correct.
        """
        return self._ok


class ValidationSection:
    """
    Group of validation rows for one validation rule family.
    """

    __slots__ = ("_title", "_rows", "_first_column_title", "_show_issue_label")

    def __init__(self, title: str, first_column_title: str = "Block", show_issue_label: bool = True) -> None:
        """
        Build one validation section.

        :param title: Section title.
        :param first_column_title: First table column title.
        :param show_issue_label: Whether to show the red section issue label.
        :return: None.
        """
        self._title: str = title
        self._rows: list[ValidationRow] = list()
        self._first_column_title: str = first_column_title
        self._show_issue_label: bool = show_issue_label

    def get_title(self) -> str:
        """
        Return the section title.

        :return: Section title.
        """
        return self._title

    def get_rows(self) -> list[ValidationRow]:
        """
        Return the section rows.

        :return: Row list.
        """
        return self._rows

    def get_first_column_title(self) -> str:
        """
        Return the first table column title.

        :return: First table column title.
        """
        return self._first_column_title

    def get_show_issue_label(self) -> bool:
        """
        Return whether the section should show the red issue label.

        :return: ``True`` when the red issue label should be shown.
        """
        return self._show_issue_label

    def get_or_create_row(self, block_label: str) -> ValidationRow:
        """
        Return the existing row for one block or create a new one.

        :param block_label: Human-readable block identifier.
        :return: Matching row object.
        """
        row: ValidationRow
        for row in self._rows:
            if row.get_block_label() == block_label:
                return row
            else:
                pass

        new_row: ValidationRow = ValidationRow(block_label=block_label)
        self._rows.append(new_row)
        return new_row


class ValidationTraversalNode:
    """
    Recursive validation context for one block and its inherited mappings.
    """

    __slots__ = ("_block", "_effective_external_vars", "_children")

    def __init__(self, block: Block, effective_external_vars: set[Var]) -> None:
        """
        Build one validation traversal node.

        :param block: Block represented by this traversal node.
        :param effective_external_vars: External variables visible at this hierarchy point.
        :return: None.
        """
        self._block: Block = block
        self._effective_external_vars: set[Var] = set(effective_external_vars)
        self._children: list[ValidationTraversalNode] = list()

    def get_block(self) -> Block:
        """
        Return the represented block.

        :return: Block object.
        """
        return self._block

    def get_effective_external_vars(self) -> set[Var]:
        """
        Return the inherited effective external-variable set.

        :return: Effective external-variable set.
        """
        return self._effective_external_vars

    def get_children(self) -> list["ValidationTraversalNode"]:
        """
        Return the recursive child traversal nodes.

        :return: Child traversal nodes.
        """
        return self._children

    def add_child(self, child_node: "ValidationTraversalNode") -> None:
        """
        Append one child traversal node.

        :param child_node: Child traversal node.
        :return: None.
        """
        self._children.append(child_node)


def collect_local_external_vars(block: Block) -> set[Var]:
    """
    Collect the local external-mapping variables defined on one block.

    :param block: Block to inspect.
    :return: Local external variables.
    """
    # External mappings are stored as enum-to-var references. The validator only
    # needs the visible variables, not the enum keys, for initialization checks.
    local_external_vars: set[Var] = set()
    mapped_var: Var | None
    for mapped_var in block.external_mapping.values():
        if isinstance(mapped_var, Var):
            local_external_vars.add(mapped_var)
        else:
            pass
    return local_external_vars


def build_validation_traversal_node(block: Block, inherited_external_vars: set[Var]) -> ValidationTraversalNode:
    """
    Build one recursive validation traversal node from the block hierarchy.

    :param block: Block to convert.
    :param inherited_external_vars: External variables visible from parent levels.
    :return: Recursive traversal node.
    """
    # The validator must remain recursive, but some templates expose usable
    # initialization variables at the parent/root level. This traversal keeps the
    # hierarchy while carrying the effective visible interface downward.
    effective_external_vars: set[Var] = set(inherited_external_vars)
    local_external_vars: set[Var] = collect_local_external_vars(block=block)
    effective_external_vars.update(local_external_vars)

    node: ValidationTraversalNode = ValidationTraversalNode(
        block=block,
        effective_external_vars=set(effective_external_vars),
    )

    child_block: Block
    for child_block in block.children:
        child_node: ValidationTraversalNode = build_validation_traversal_node(
            block=child_block,
            inherited_external_vars=set(effective_external_vars),
        )
        node.add_child(child_node=child_node)

    return node


def collect_validation_traversal_list(root_node: ValidationTraversalNode) -> list[ValidationTraversalNode]:
    """
    Flatten one recursive validation traversal tree.

    :param root_node: Root traversal node.
    :return: Flat traversal-node list.
    """
    # Most validation sections operate block by block, so the traversal tree is
    # flattened after the effective context has already been propagated.
    flat_nodes: list[ValidationTraversalNode] = list([root_node])
    child_node: ValidationTraversalNode
    for child_node in root_node.get_children():
        flat_nodes.extend(collect_validation_traversal_list(root_node=child_node))
    return flat_nodes


def add_validation_detail(section: ValidationSection, block_label: str, detail: str) -> None:
    """
    Append one formatted validation detail to a section.

    :param section: Mutable validation section.
    :param block_label: Human-readable block identifier.
    :param detail: One validation detail for that block.
    :return: None.
    """
    # The modal groups issues by validation type and then by block so users can
    # inspect one subsystem at a time instead of reading one mixed flat list.
    row: ValidationRow = section.get_or_create_row(block_label=block_label)
    row.add_detail(detail=detail)


def add_validation_status_detail(section: ValidationSection, block_label: str, detail: str, ok: bool) -> None:
    """
    Append one formatted validation detail and status to a section.

    :param section: Mutable validation section.
    :param block_label: Human-readable block identifier.
    :param detail: One validation detail for that block.
    :param ok: Whether the row is informationally correct.
    :return: None.
    """
    row: ValidationRow = section.get_or_create_row(block_label=block_label)
    row.add_detail(detail=detail)
    row.set_ok(val=ok)


class ValidationSectionDialog(QDialog):
    """
    Dialog showing model-consistency results grouped by validation section.
    """

    __slots__ = ("_section_results",)

    def __init__(self, section_results: list[ValidationSection], parent: QtWidgets.QWidget | None = None) -> None:
        """
        Build one structured validation dialog.

        :param section_results: Ordered validation results grouped by section title.
        :param parent: Optional Qt parent widget.
        :return: None.
        """
        super().__init__(parent)
        self._section_results: list[ValidationSection] = section_results
        self.setWindowTitle("Model Consistency Validation")
        self.resize(860, 620)

        # The root layout stacks one visual section after another so each rule is
        # isolated and easier to scan than a single mixed text block.
        layout: QVBoxLayout = QVBoxLayout(self)

        scroll_area: QScrollArea = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(scroll_area)

        scroll_widget: QWidget = QWidget(scroll_area)
        scroll_area.setWidget(scroll_widget)
        scroll_layout: QVBoxLayout = QVBoxLayout(scroll_widget)

        intro_label: QLabel = QLabel(
            "Run an informational validation of the edited model structure, mappings, initialization, and port connectivity. "
            "This check reports issues but does not block saving the model."
        )
        intro_label.setWordWrap(True)
        scroll_layout.addWidget(intro_label)

        section: ValidationSection
        for section in self._section_results:
            self._add_section_widget(layout=scroll_layout, section=section)

        button_box: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, self)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

    def _add_section_widget(self, layout: QVBoxLayout, section: ValidationSection) -> None:
        """
        Append one validation section to the dialog.

        :param layout: Parent layout.
        :param section: Validation section object.
        :return: None.
        """
        # Each section uses a compact two-column table so the user can align the
        # affected block name with the details that belong to it.
        title_label: QLabel = QLabel(section.get_title())
        title_font: QtGui.QFont = title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 1)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        rows: list[ValidationRow] = section.get_rows()
        if len(rows) == 0:
            status_label: QLabel = QLabel("All good")
            status_label.setStyleSheet("color: #027a48;")
            layout.addWidget(status_label)
        else:
            if section.get_show_issue_label():
                warning_label: QLabel = QLabel("Issues found in this section")
                warning_label.setStyleSheet("color: #b42318;")
                layout.addWidget(warning_label)
            else:
                pass

            table_widget: QTableWidget = QTableWidget(self)
            table_widget.setColumnCount(2)
            table_widget.setHorizontalHeaderLabels([section.get_first_column_title(), "Details"])
            table_widget.setRowCount(len(rows))
            table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            table_widget.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
            table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            table_widget.verticalHeader().setVisible(False)
            table_widget.horizontalHeader().setStretchLastSection(True)
            table_widget.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
            table_widget.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)

            row_index: int = 0
            row: ValidationRow
            for row in rows:
                details_text: str = "\n".join(row.get_details())
                block_item: QTableWidgetItem = QTableWidgetItem(row.get_block_label())
                detail_item: QTableWidgetItem = QTableWidgetItem(details_text)
                if row.is_ok():
                    ok_brush: QtGui.QBrush = QtGui.QBrush(QColor("#027a48"))
                    block_item.setForeground(ok_brush)
                    detail_item.setForeground(ok_brush)
                else:
                    error_brush: QtGui.QBrush = QtGui.QBrush(QColor("#b42318"))
                    block_item.setForeground(error_brush)
                    detail_item.setForeground(error_brush)

                table_widget.setItem(row_index, 0, block_item)
                table_widget.setItem(row_index, 1, detail_item)
                row_index = row_index + 1

            table_widget.resizeRowsToContents()
            table_widget.setMinimumHeight(table_widget.verticalHeader().length() + table_widget.horizontalHeader().height() + 8)
            table_widget.setMaximumHeight(table_widget.verticalHeader().length() + table_widget.horizontalHeader().height() + 8)
            layout.addWidget(table_widget)


def get_emt_phase_group(reference: VarPowerFlowReferenceType | None) -> str | None:
    """
    Map one EMT interface reference to its phase group.

    :param reference: Variable power-flow reference.
    :return: ``N``, ``A``, ``B``, ``C`` or ``None``.
    """
    # The validator groups ports by phase so EMT models can treat a completely
    # absent phase as intentional instead of as a partial connectivity failure.
    if reference in (VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.i_N,
                     VarPowerFlowReferenceType.vf_N, VarPowerFlowReferenceType.if_N,
                     VarPowerFlowReferenceType.vt_N, VarPowerFlowReferenceType.it_N):
        return "N"
    elif reference in (VarPowerFlowReferenceType.v_A, VarPowerFlowReferenceType.i_A,
                       VarPowerFlowReferenceType.vf_A, VarPowerFlowReferenceType.if_A,
                       VarPowerFlowReferenceType.vt_A, VarPowerFlowReferenceType.it_A):
        return "A"
    elif reference in (VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.i_B,
                       VarPowerFlowReferenceType.vf_B, VarPowerFlowReferenceType.if_B,
                       VarPowerFlowReferenceType.vt_B, VarPowerFlowReferenceType.it_B):
        return "B"
    elif reference in (VarPowerFlowReferenceType.v_C, VarPowerFlowReferenceType.i_C,
                       VarPowerFlowReferenceType.vf_C, VarPowerFlowReferenceType.if_C,
                       VarPowerFlowReferenceType.vt_C, VarPowerFlowReferenceType.it_C):
        return "C"
    else:
        return None


class BlockPositionChangedCallback:
    """
    Callable wrapper used by graphics items to report block moves without lambdas.
    """

    __slots__ = ("_editor", "_block_uid")

    def __init__(self, editor: DynamicBlockEditorGUI, block_uid: int) -> None:
        """
        Build the callback wrapper.

        :param editor: Owning dynamic editor.
        :param block_uid: Moved block uid.
        :return: None.
        """

        self._editor = editor
        self._block_uid = block_uid

    def __call__(self, x_pos: float, y_pos: float) -> None:
        """
        Forward one position change to the editor.

        :param x_pos: New x coordinate.
        :param y_pos: New y coordinate.
        :return: None.
        """

        self._editor.on_block_position_changed(self._block_uid, x_pos, y_pos)


def truncate_port_label(text: str, max_chars: int = PORT_LABEL_MAX_CHARS) -> str:
    """
    Truncate a port label to the requested visible length.

    :param text:
    :param max_chars:
    :return:
    """
    if len(text) <= max_chars:
        return text
    else:
        return text[:max_chars]


def build_orthogonal_connection_path(start: QPointF, end: QPointF) -> QPainterPath:
    """
    Build an orthogonal wire path with elbow segments.
    Only adds elbows when the path changes direction.

    :param start:
    :param end:
    :return:
    """
    path: QPainterPath = QPainterPath(start)
    delta_x: float = end.x() - start.x()
    delta_y: float = end.y() - start.y()

    if abs(delta_y) < 1:
        path.lineTo(end)
        return path

    if abs(delta_x) < 1:
        path.lineTo(end)
        return path

    offset: float = min(WIRE_ELBOW_OFFSET, abs(delta_x) / 2.0) if delta_x != 0 else WIRE_ELBOW_OFFSET
    start_elbow_x: float = start.x() + offset
    end_elbow_x: float = end.x() - offset

    if end.x() >= start.x():
        path.lineTo(start_elbow_x, start.y())
        path.lineTo(start_elbow_x, end.y())
    else:
        middle_x: float = start.x() + max(WIRE_ELBOW_OFFSET, abs(delta_x) / 2.0)
        path.lineTo(middle_x, start.y())
        path.lineTo(middle_x, end.y())

    path.lineTo(end_elbow_x, end.y())
    path.lineTo(end)
    return path


class OrthogonalRouter:
    """
    Global orthogonal router for connection paths.
    Uses A* pathfinding on a grid to compute Manhattan-style paths avoiding obstacles.
    """

    GRID_SIZE: float = 10.0
    BASE_COST: int = 1
    TURN_COST: int = 10
    BLOCKED_COST: int = 1000000

    class GridNode:
        def __init__(self, x: int, y: int):
            self.x = x
            self.y = y
            self.g_cost: int = 0
            self.h_cost: int = 0
            self.f_cost: int = 0
            self.parent: "OrthogonalRouter.GridNode | None" = None
            self.direction: str | None = None

        def __hash__(self):
            return hash((self.x, self.y))

        def __eq__(self, other):
            return self.x == other.x and self.y == other.y

    @staticmethod
    def _pos_to_grid(pos: QPointF) -> tuple[int, int]:
        return (int(pos.x() / OrthogonalRouter.GRID_SIZE),
                int(pos.y() / OrthogonalRouter.GRID_SIZE))

    @staticmethod
    def _grid_to_pos(gx: int, gy: int) -> QPointF:
        return QPointF(gx * OrthogonalRouter.GRID_SIZE, gy * OrthogonalRouter.GRID_SIZE)

    @staticmethod
    def _get_neighbors(node: "OrthogonalRouter.GridNode") -> List[tuple]:
        return [
            (node.x + 1, node.y, 'right'),
            (node.x - 1, node.y, 'left'),
            (node.x, node.y + 1, 'down'),
            (node.x, node.y - 1, 'up')
        ]

    @staticmethod
    def _heuristic(x1: int, y1: int, x2: int, y2: int) -> int:
        return abs(x2 - x1) + abs(y2 - y1)

    @staticmethod
    def _is_blocked(gx: int, gy: int, scene: "QGraphicsScene | None",
                    source_port: "PortItem | BranchingItem | None",
                    target_port: "PortItem | BranchingItem | None") -> bool:
        if scene is None:
            return False

        pos = QPointF(gx * OrthogonalRouter.GRID_SIZE, gy * OrthogonalRouter.GRID_SIZE)
        rect = QtCore.QRectF(pos.x() - OrthogonalRouter.GRID_SIZE / 2,
                             pos.y() - OrthogonalRouter.GRID_SIZE / 2,
                             OrthogonalRouter.GRID_SIZE, OrthogonalRouter.GRID_SIZE)

        items = scene.items(rect)
        for item in items:
            if isinstance(item, (ConnectionItem, PortItem, BranchingItem)):
                pass
            else:
                if item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable:
                    if source_port is not None and item == source_port.subsystem:
                        pass
                    else:
                        if target_port is not None and item == target_port.subsystem:
                            pass
                        else:
                            return True
                else:
                    pass
        return False

    @staticmethod
    def compute_path(source_pos: QPointF, target_pos: QPointF,
                     source_port: "PortItem | BranchingItem | None" = None,
                     target_port: "PortItem | BranchingItem | None" = None,
                     scene: "QGraphicsScene | None" = None) -> QPainterPath:
        """
        Compute an orthogonal path using A* pathfinding on a grid.

        :param source_pos: Start point
        :param target_pos: End point
        :param source_port: Source port for context
        :param target_port: Target port for context
        :param scene: Graphics scene for obstacle detection
        :return: QPainterPath with orthogonal segments avoiding obstacles
        """
        if scene is None:
            return build_orthogonal_connection_path(source_pos, target_pos)

        start_gx, start_gy = OrthogonalRouter._pos_to_grid(source_pos)
        end_gx, end_gy = OrthogonalRouter._pos_to_grid(target_pos)

        open_set: List[OrthogonalRouter.GridNode] = []
        closed_set: set = set()

        start_node = OrthogonalRouter.GridNode(start_gx, start_gy)
        start_node.g_cost = 0
        start_node.h_cost = OrthogonalRouter._heuristic(start_gx, start_gy, end_gx, end_gy)
        start_node.f_cost = start_node.g_cost + start_node.h_cost
        start_node.direction = None

        open_set.append(start_node)

        while open_set:
            open_set.sort(key=_grid_node_f_cost_sort_key)
            current = open_set.pop(0)

            if current.x == end_gx and current.y == end_gy:
                path_points = OrthogonalRouter._reconstruct_path(current)
                return OrthogonalRouter._build_qpainterpath(path_points, source_pos, target_pos)

            closed_set.add((current.x, current.y))

            for gx, gy, direction in OrthogonalRouter._get_neighbors(current):
                if (gx, gy) in closed_set:
                    pass
                else:
                    if OrthogonalRouter._is_blocked(gx, gy, scene, source_port, target_port):
                        pass
                    else:
                        g_cost = current.g_cost + OrthogonalRouter.BASE_COST

                        if current.direction is not None and current.direction != direction:
                            g_cost += OrthogonalRouter.TURN_COST
                        else:
                            pass

                        neighbor = OrthogonalRouter.GridNode(gx, gy)

                        in_open = False
                        for node in open_set:
                            if node.x == gx and node.y == gy:
                                in_open = True
                                if g_cost < node.g_cost:
                                    node.g_cost = g_cost
                                    node.f_cost = node.g_cost + node.h_cost
                                    node.parent = current
                                    node.direction = direction
                                else:
                                    pass
                                break
                            else:
                                pass

                        if not in_open:
                            neighbor.g_cost = g_cost
                            neighbor.h_cost = OrthogonalRouter._heuristic(gx, gy, end_gx, end_gy)
                            neighbor.f_cost = neighbor.g_cost + neighbor.h_cost
                            neighbor.parent = current
                            neighbor.direction = direction
                            open_set.append(neighbor)
                        else:
                            pass

        fallback_path = build_orthogonal_connection_path(source_pos, target_pos)
        return fallback_path

    @staticmethod
    def _reconstruct_path(end_node: "OrthogonalRouter.GridNode") -> List[QPointF]:
        path = []
        current = end_node
        while current is not None:
            path.append(OrthogonalRouter._grid_to_pos(current.x, current.y))
            current = current.parent
        path.reverse()
        return path

    @staticmethod
    def _build_qpainterpath(grid_path: List[QPointF], source_pos: QPointF, target_pos: QPointF) -> QPainterPath:
        if len(grid_path) < 2:
            path = QPainterPath(source_pos)
            path.lineTo(target_pos)
            return path

        path = QPainterPath(source_pos)
        path.lineTo(grid_path[0])

        simplified = OrthogonalRouter._simplify_path(grid_path)

        for point in simplified:
            path.lineTo(point)

        path.lineTo(target_pos)
        return path

    @staticmethod
    def _simplify_path(points: List[QPointF]) -> List[QPointF]:
        if len(points) < 3:
            return points

        simplified = [points[0]]
        prev_dir = None

        for i in range(1, len(points) - 1):
            dx1 = points[i].x() - points[i - 1].x()
            dy1 = points[i].y() - points[i - 1].y()
            dx2 = points[i + 1].x() - points[i].x()
            dy2 = points[i + 1].y() - points[i].y()

            dir1 = None
            if abs(dx1) > abs(dy1):
                dir1 = 'h'
            else:
                dir1 = 'v'

            dir2 = None
            if abs(dx2) > abs(dy2):
                dir2 = 'h'
            else:
                dir2 = 'v'

            if dir1 != dir2:
                simplified.append(points[i])

        simplified.append(points[-1])
        return simplified

    @staticmethod
    def compute_path_simple(source_pos: QPointF, target_pos: QPointF) -> QPainterPath:
        """
        Compute a simple orthogonal path without obstacle avoidance.

        :param source_pos: Start point
        :param target_pos: End point
        :return: QPainterPath with orthogonal segments
        """
        return build_orthogonal_connection_path(source_pos, target_pos)


def remap_serialized_uids(data: Any, uid_map: Dict[int, int]) -> Any:
    """
    Recursively replace serialized UIDs with fresh values while preserving references.

    :param data:
    :param uid_map:
    :return:
    """
    key: str
    value: Any
    remapped_data: Dict[str, Any]

    if isinstance(data, dict):
        remapped_data = dict()

        for key, value in data.items():
            if key == "uid" and isinstance(value, int):
                if value in uid_map:
                    remapped_data[key] = uid_map[value]
                else:
                    uid_map[value] = _new_uid()
                    remapped_data[key] = uid_map[value]
            else:
                remapped_data[key] = remap_serialized_uids(value, uid_map)

        return remapped_data
    elif isinstance(data, list):
        return [remap_serialized_uids(value, uid_map) for value in data]
    else:
        return data


def clone_template_diagram(diagram: BlockDiagram, uid_map: Dict[int, int]) -> BlockDiagram:
    """
    Clone a template diagram while remapping block and connection identifiers.

    :param diagram:
    :param uid_map:
    :return:
    """
    cloned_diagram: BlockDiagram = BlockDiagram()
    node: Any
    con: Any
    mapped_uid: int
    subdiagram: BlockDiagram | None

    cloned_diagram.status = diagram.status

    for _, node in diagram.node_data.items():
        mapped_uid = uid_map.get(node.device_uid, node.device_uid)

        if node.sub_diagram is not None:
            subdiagram = clone_template_diagram(node.sub_diagram, uid_map)
        else:
            subdiagram = None

        cloned_diagram.add_node(
            name=node.name,
            x=node.x,
            y=node.y,
            tpe=node.tpe,
            device_uid=mapped_uid,
            api_object_name=node.api_object_name,
            state_ins=node.state_ins,
            state_outs=list(node.state_outs),
            algeb_ins=node.algeb_ins,
            algeb_outs=list(node.algeb_outs),
            color=node.color,
            subdiagram=subdiagram
        )

    for _, con in diagram.con_data.items():
        cloned_diagram.add_branch(
            connectionitem_uid=_new_uid(),
            device_uid_from=uid_map.get(con.from_uid, con.from_uid),
            device_uid_to=uid_map.get(con.to_uid, con.to_uid),
            port_number_from=con.port_number_from,
            port_number_to=con.port_number_to,
            color=con.color
        )

    return cloned_diagram


def is_supported_library_payload(item_data: object) -> bool:
    """
    Check whether a tree item payload can be dragged into the editor scene.

    :param item_data:
    :return:
    """
    if isinstance(item_data, BlockType):
        return True
    elif isinstance(item_data, BasicBlockTemplateDescriptor):
        return True
    elif isinstance(item_data, (RmsModelTemplate, EmtModelTemplate, FmuTemplate)):
        return True
    elif isinstance(item_data, SignalPairPayload):
        return True
    else:
        return False


@dataclass(frozen=True)
class SignalPairPayload:
    """
    Marker payload for the signal pair tool that creates two connected blocks
    (one input, one output) sharing the same variable.
    """
    pass


@dataclass(frozen=True)
class LibraryLeafSpec:
    """
    One draggable leaf entry in the library tree.
    """

    label: str
    payload: object
    search_text: str = ""


class LibraryTreeFilterProxyModel(QtCore.QSortFilterProxyModel):
    """
    Tree proxy used by the block editor library search.
    """

    __slots__ = ("_search_role",)

    def __init__(self, search_role: int, parent: QtCore.QObject | None = None):
        super().__init__(parent)
        self._search_role = search_role
        self.setRecursiveFilteringEnabled(True)
        self.setAutoAcceptChildRows(True)
        self.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterRole(search_role)
        self.setFilterKeyColumn(0)

    def mimeData(self, indexes: List[QtCore.QModelIndex]) -> QtCore.QMimeData:
        """
        Forward drag mime building to the source library model.
        """

        source_model: QtCore.QAbstractItemModel | None = self.sourceModel()
        if isinstance(source_model, DynamicsLibraryTreeModel):
            source_indexes: List[QtCore.QModelIndex] = [self.mapToSource(index) for index in indexes if index.isValid()]
            return source_model.mimeData(source_indexes)
        else:
            return super().mimeData(indexes)

    def supportedDragActions(self) -> QtCore.Qt.DropAction:
        """
        Reuse the drag action exposed by the source model.
        """

        source_model: QtCore.QAbstractItemModel | None = self.sourceModel()
        if isinstance(source_model, DynamicsLibraryTreeModel):
            return source_model.supportedDragActions()
        else:
            return super().supportedDragActions()


class BlockTableFilterProxyModel(QtCore.QSortFilterProxyModel):
    """
    Flat table proxy used for the three side-panel table searches
    (Variables, Parameters, Equations).
    """

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent)
        self.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterRole(BLOCK_SEARCH_ROLE)
        self.setFilterKeyColumn(0)


def clone_block_for_editing(block: Block) -> Block:
    """
    Build an isolated editable copy of a block, including its diagram.

    :param block:
    :return:
    """
    return copy.deepcopy(block)


def _build_block_uid_lookup(root_block: Block) -> Dict[int, Block]:
    """
    Build one uid-to-block lookup for one edited hierarchy.

    :param root_block: Root block that owns the edited hierarchy.
    :return: Mapping from block uid to block object.
    """
    block_lookup: Dict[int, Block] = dict()
    block_item: Block

    for block_item in root_block.get_all_blocks():
        block_lookup[block_item.uid] = block_item

    return block_lookup


def _ensure_block_tree_names(block: Block, prefix: str = "block") -> None:
    """
    Assign stable fallback names to unnamed blocks in one hierarchy.

    :param block: Root block to normalize.
    :param prefix: Fallback name prefix.
    :return: None.
    """
    child_index: int
    child_block: Block

    if not block.name:
        block.name = f"{prefix}_{str(block.uid)[:8]}"
    else:
        pass

    for child_index, child_block in enumerate(block.children, start=1):
        _ensure_block_tree_names(child_block, prefix=f"{block.name}_{child_index}")


def copy_block_state(source_block: Block, target_block: Block) -> None:
    """
    Copy the complete edited block state back into the original block instance.

    :param source_block:
    :param target_block:
    :return:
    """
    source_clone: Block = clone_block_for_editing(source_block)

    # The original object identity must be preserved for external references in the GUI and device model.
    target_block.name = source_clone.name
    target_block.uid = source_clone.uid
    target_block.is_decomposable = source_clone.is_decomposable
    target_block.vars_glob_name2uid = source_clone.vars_glob_name2uid
    target_block.state_vars = source_clone.state_vars
    target_block.state_eqs = source_clone.state_eqs
    target_block.algebraic_vars = source_clone.algebraic_vars
    target_block.algebraic_eqs = source_clone.algebraic_eqs
    target_block.diff_vars = source_clone.diff_vars
    target_block.reformulated_vars = source_clone.reformulated_vars
    target_block.differential_eqs = source_clone.differential_eqs
    target_block.init_eqs = source_clone.init_eqs
    target_block.diff_init_eqs = source_clone.diff_init_eqs
    target_block.children = source_clone.children
    target_block.in_vars = source_clone.in_vars
    target_block.out_vars = source_clone.out_vars
    target_block.parameters = source_clone.parameters
    # target_block.alter_params = source_clone.alter_params
    target_block.discrete_eqs = source_clone.discrete_eqs
    target_block.external_mapping = source_clone.external_mapping
    target_block.api_obj_mapping = source_clone.api_obj_mapping
    target_block.init_values = source_clone.init_values
    target_block.var_mapping = source_clone.var_mapping
    target_block.event_dict = source_clone.event_dict
    target_block.mode_dict = source_clone.mode_dict
    # Persist the cloned diagram together with the cloned symbolic hierarchy so
    # the saved block owns one self-consistent snapshot of nodes, connections,
    # and positions after the editor closes. Reusing ``source_block.diagram``
    # would keep the saved model tied to the live editor working copy instead of
    # the copied block state that is meant to survive reopening.
    target_block.diagram = source_clone.diagram


def _initialize_editor_assigned_rms_bus_model(bus: Bus, var_factory: VarFactory) -> None:
    """
    Initialize one missing RMS bus model after assigning one editor-built device model.

    :param bus: Connected bus.
    :param var_factory: Shared symbolic variable factory.
    :return: None.
    """
    if bus.rms_model.empty():
        initialize_bus_rms(bus=bus, vf=var_factory)
    else:
        pass


def _initialize_editor_assigned_emt_bus_model(bus: Bus,
                                              api_object: Any,
                                              circuit: MultiCircuit | None,
                                              var_factory: VarFactory,
                                              editor_interface_refs: set[VarPowerFlowReferenceType] | None = None) -> None:
    """
    Initialize one missing EMT bus shell after assigning one editor-built device model.

    :param bus: Connected bus.
    :param api_object: Edited concrete device that owns the current interface.
    :param circuit: Owning circuit when available.
    :param var_factory: Shared symbolic variable factory.
    :param editor_interface_refs: References still exposed by the current editor interface.
    :return: None.
    """
    if bus.emt_model.empty():
        # Editor-driven assignments must preserve the phase ports that the user
        # kept in the GUI instead of falling back to a hardcoded AC shell.
        if editor_interface_refs is not None:
            mask: list[bool] | None = None

            # Injection devices expose one bus interface, so the edited
            # references map directly to that single connected bus.
            if isinstance(api_object, InjectionParent):
                if api_object.bus is bus:
                    mask = list([False, False, False, False])
                    mask[0] = (VarPowerFlowReferenceType.v_N in editor_interface_refs
                               or VarPowerFlowReferenceType.i_N in editor_interface_refs)
                    mask[1] = (VarPowerFlowReferenceType.v_A in editor_interface_refs
                               or VarPowerFlowReferenceType.i_A in editor_interface_refs)
                    mask[2] = (VarPowerFlowReferenceType.v_B in editor_interface_refs
                               or VarPowerFlowReferenceType.i_B in editor_interface_refs)
                    mask[3] = (VarPowerFlowReferenceType.v_C in editor_interface_refs
                               or VarPowerFlowReferenceType.i_C in editor_interface_refs)
                else:
                    mask = None
            else:
                # Branch devices expose two side-specific interfaces, so the
                # edited bus must first be matched against the from or to side
                # before the mask is evaluated from the remaining references.
                if isinstance(api_object, BranchParent):
                    if api_object.bus_from is bus:
                        mask = list([False, False, False, False])
                        mask[0] = (VarPowerFlowReferenceType.vf_N in editor_interface_refs
                                   or VarPowerFlowReferenceType.if_N in editor_interface_refs)
                        mask[1] = (VarPowerFlowReferenceType.vf_A in editor_interface_refs
                                   or VarPowerFlowReferenceType.if_A in editor_interface_refs)
                        mask[2] = (VarPowerFlowReferenceType.vf_B in editor_interface_refs
                                   or VarPowerFlowReferenceType.if_B in editor_interface_refs)
                        mask[3] = (VarPowerFlowReferenceType.vf_C in editor_interface_refs
                                   or VarPowerFlowReferenceType.if_C in editor_interface_refs)
                    else:
                        if api_object.bus_to is bus:
                            mask = list([False, False, False, False])
                            mask[0] = (VarPowerFlowReferenceType.vt_N in editor_interface_refs
                                       or VarPowerFlowReferenceType.it_N in editor_interface_refs)
                            mask[1] = (VarPowerFlowReferenceType.vt_A in editor_interface_refs
                                       or VarPowerFlowReferenceType.it_A in editor_interface_refs)
                            mask[2] = (VarPowerFlowReferenceType.vt_B in editor_interface_refs
                                       or VarPowerFlowReferenceType.it_B in editor_interface_refs)
                            mask[3] = (VarPowerFlowReferenceType.vt_C in editor_interface_refs
                                       or VarPowerFlowReferenceType.it_C in editor_interface_refs)
                        else:
                            mask = None
                else:
                    mask = None
        else:
            mask = None

        # When a dynamic editor mask is available, use it directly because it
        # reflects the final saved interface. Otherwise preserve the previous
        # circuit-derived or default initialization path.
        if mask is not None:
            if bus.is_dc:
                bus.emt_model = BusEmtTemplate(
                    vf=var_factory,
                    mask=list([False, False, False, False]),
                    is_dc=True,
                    name=f"{bus.name}_emt_template",
                ).block
            else:
                if any(mask):
                    bus.emt_model = BusEmtTemplate(
                        vf=var_factory,
                        mask=mask,
                        is_dc=False,
                        name=f"{bus.name}_emt_template",
                    ).block
                else:
                    # A fully removed AC interface cannot define an EMT bus
                    # shell, so this state is left untouched instead of forcing
                    # an invalid template or throwing from here.
                    pass
        else:
            if circuit is not None:
                get_bus_emt_template(grid=circuit, bus=bus)
            else:
                if bus.is_dc:
                    bus.emt_model = BusEmtTemplate(
                        vf=var_factory,
                        mask=list([False, False, False, False]),
                        is_dc=True,
                        name=f"{bus.name}_emt_template",
                    ).block
                else:
                    bus.emt_model = BusEmtTemplate(
                        vf=var_factory,
                        mask=list([False, True, True, True]),
                        is_dc=False,
                        name=f"{bus.name}_emt_template",
                    ).block
    else:
        pass


def initialize_connected_bus_models_for_editor_assignment(api_object: Any,
                                                          circuit: MultiCircuit | None,
                                                          var_factory: VarFactory,
                                                          mode: DynamicSimulationMode,
                                                          editor_interface_refs: set[VarPowerFlowReferenceType] | None = None) -> None:
    """
    Initialize missing connected bus models right after one Dynamic Editor assignment.

    :param api_object: Edited concrete device.
    :param circuit: Owning circuit when available.
    :param var_factory: Shared symbolic variable factory.
    :param mode: Dynamic simulation domain being edited.
    :param editor_interface_refs: References still exposed by the current editor interface.
    :return: None.
    """
    if isinstance(api_object, InjectionParent):
        bus: Bus | None = api_object.bus
        if bus is None:
            pass
        else:
            if mode == DynamicSimulationMode.RMS:
                _initialize_editor_assigned_rms_bus_model(bus=bus, var_factory=var_factory)
            else:
                if mode == DynamicSimulationMode.EMT:
                    _initialize_editor_assigned_emt_bus_model(bus=bus,
                                                              api_object=api_object,
                                                              circuit=circuit,
                                                              var_factory=var_factory,
                                                              editor_interface_refs=editor_interface_refs)
                else:
                    raise ValueError(f"Unsupported dynamic editor mode {mode}")
    else:
        if isinstance(api_object, BranchParent):
            if mode == DynamicSimulationMode.RMS:
                _initialize_editor_assigned_rms_bus_model(bus=api_object.bus_from, var_factory=var_factory)
                _initialize_editor_assigned_rms_bus_model(bus=api_object.bus_to, var_factory=var_factory)
            else:
                if mode == DynamicSimulationMode.EMT:
                    _initialize_editor_assigned_emt_bus_model(bus=api_object.bus_from,
                                                              api_object=api_object,
                                                              circuit=circuit,
                                                              var_factory=var_factory,
                                                              editor_interface_refs=editor_interface_refs)
                    _initialize_editor_assigned_emt_bus_model(bus=api_object.bus_to,
                                                              api_object=api_object,
                                                              circuit=circuit,
                                                              var_factory=var_factory,
                                                              editor_interface_refs=editor_interface_refs)
                else:
                    raise ValueError(f"Unsupported dynamic editor mode {mode}")
        else:
            pass


def build_block_symbol_namespace(block: Block) -> Dict[str, Expr]:
    """
    Build the symbol namespace used to parse textual expressions for a block.

    :param block:
    :return:
    """
    namespace: Dict[str, Expr] = dict()
    block_item: Block
    var: Var

    for block_item in block.get_all_blocks():
        for var in block_item.algebraic_vars:
            namespace[var.name] = var

        for var in block_item.state_vars:
            namespace[var.name] = var

        for var in block_item.diff_vars:
            namespace[var.name] = var

        for var in block_item.in_vars:
            namespace[var.name] = var

        for var in block_item.out_vars:
            namespace[var.name] = var

        for var in block_item.parameters.keys():
            namespace[var.name] = var

        for var in block_item.event_dict.keys():
            namespace[var.name] = var

        for var in block_item.mode_dict.keys():
            namespace[var.name] = var

        for var in block_item.init_values.keys():
            namespace[var.name] = var

    return namespace


def is_valid_symbol_name(name: str) -> bool:
    """
    Check whether a string is a valid symbolic identifier.

    :param name:
    :return:
    """
    return re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) is not None


def block_namespace_contains_name(block: Block, name: str, exclude_var: Var | None = None) -> bool:
    """
    Check whether a symbol name already exists in the block namespace.

    :param block:
    :param name:
    :param exclude_var:
    :return:
    """
    namespace: Dict[str, Expr] = build_block_symbol_namespace(block)
    current_symbol: Expr | None = namespace.get(name, None)

    if current_symbol is None:
        return False
    elif exclude_var is not None and current_symbol is exclude_var:
        return False
    else:
        return True


def add_variable_to_block(block: Block,
                          var: Var,
                          var_type: str,
                          parameter_value: float | None = 0.0) -> None:
    if var_type == "state":
        block.state_vars.append(var)
    elif var_type == "algebraic":
        block.algebraic_vars.append(var)
    elif var_type == "in":
        block.in_vars.append(var)
    elif var_type == "out":
        block.out_vars.append(var)
    elif var_type == "parameter":
        block.parameters[var] = Const(parameter_value, name=var.name)
    elif var_type == "event_parameter":
        block.event_dict[var] = Const(parameter_value, name=var.name)
    elif var_type == "mode_parameter":
        block.mode_dict[var] = Const(parameter_value, name=var.name)
    else:
        raise ValueError(f"Unknown var_type {var_type}")

class Node:
    def __init__(self, name, data=None, parent=None):
        self.name = name
        self.data = data
        self.parent = parent
        self.children = []

    def add_child(self, node):
        self.children.append(node)
        node.parent = self


class ResizeHandle(QGraphicsRectItem):
    """
    Interactive resize handle attached to a block item.
    """

    def __init__(self, block_item: EditorBlockGraphicsItem, size: int = 10):
        """
        Build the resize handle.

        :param block_item:
        :param size:
        """
        super().__init__(0, 0, size, size, block_item)
        self.setBrush(QBrush(HANDLE_FILL))
        self.setPen(QPen(QColor("#ffffff"), 1))
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.setZValue(2)
        self.block: EditorBlockGraphicsItem = block_item
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        """
        Propagate handle movement into block resizing.

        :param change:
        :param value:
        :return:
        """
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self.block.resizing_from_handle:
                new_pos: QPointF = value
                min_width: float
                min_height: float
                min_width, min_height = self.block.get_minimum_block_size()
                new_width: float = max(new_pos.x(), min_width)
                new_height: float = max(new_pos.y(), min_height)

                # The block geometry must be updated from the handle movement.
                self.block.resize_block(new_width, new_height)
                return QPointF(new_width, new_height)
            else:
                return super().itemChange(change, value)
        else:
            return super().itemChange(change, value)


class GenericBlockDialog(QDialog):
    """
    Dialog to edit the created generic block
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Generic Block")

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        layout.addRow("Block name:", self.name_edit)

        self.inputs_spin = QSpinBox()
        self.inputs_spin.setMinimum(1)
        self.inputs_spin.setValue(1)
        layout.addRow("Number of inputs:", self.inputs_spin)

        self.outputs_spin = QSpinBox()
        self.outputs_spin.setMinimum(1)
        self.outputs_spin.setValue(1)
        layout.addRow("Number of outputs:", self.outputs_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_values(self):
        """Return all dialog values."""
        name = self.name_edit.text().strip() or "generic"
        inputs = self.inputs_spin.value()
        outputs = self.outputs_spin.value()
        return name, inputs, outputs


class EmtTemplateWizardDialog(QDialog):
    """
    Dialog to configure EMT template wizard block phases.
    """

    def __init__(self,
                 parent=None,
                 initial_values: tuple[bool, bool, bool, bool] | None = None):
        super().__init__(parent)
        self.setWindowTitle("Configure EMT Block Phases")

        layout = QVBoxLayout(self)

        label = QLabel("Select the phases for this EMT block:")
        layout.addWidget(label)

        self.phase_n_check = QCheckBox("phase_n")
        self.phase_a_check = QCheckBox("phase_a")
        self.phase_b_check = QCheckBox("phase_b")
        self.phase_c_check = QCheckBox("phase_c")

        layout.addWidget(self.phase_n_check)
        layout.addWidget(self.phase_a_check)
        layout.addWidget(self.phase_b_check)
        layout.addWidget(self.phase_c_check)

        if initial_values is not None:
            self.phase_n_check.setChecked(bool(initial_values[0]))
            self.phase_a_check.setChecked(bool(initial_values[1]))
            self.phase_b_check.setChecked(bool(initial_values[2]))
            self.phase_c_check.setChecked(bool(initial_values[3]))
        else:
            pass

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self):
        """Return phase selection as a tuple of booleans."""
        return (
            self.phase_n_check.isChecked(),
            self.phase_a_check.isChecked(),
            self.phase_b_check.isChecked(),
            self.phase_c_check.isChecked()
        )


EditorBlockGraphicsItem: TypeAlias = "BlockItem | GenericBlockItem | PairedItem"


class PortItem(QGraphicsEllipseItem):
    """
    Graphical input or output port attached to a block item.
    """

    def __init__(self,
                 subsystem: EditorBlockGraphicsItem,
                 is_input: bool,
                 index: int,
                 total: int,
                 radius: int = 6):
        """
        Build a block port.

        :param subsystem:
        :param is_input:
        :param index:
        :param total:
        :param radius:
        """
        super().__init__(-radius, -radius, 2 * radius, 2 * radius, subsystem)
        fill_color: QColor = INPUT_PORT_FILL if is_input else OUTPUT_PORT_FILL
        self.setBrush(QBrush(fill_color))
        self.setPen(QPen(PORT_BORDER, 1.5))
        self.setZValue(3)
        self.setAcceptHoverEvents(True)
        self.subsystem: EditorBlockGraphicsItem = subsystem
        self.is_input: bool = is_input
        self.connections: List["ConnectionItem"] | None = None
        self.index: int = index
        self.total: int = total
        self.base_var: Var | None = None

        spacing: float = subsystem.rect().height() / (total + 1)
        y_pos: float = spacing * (index + 1)
        x_pos: float = 0 if is_input else subsystem.rect().width()
        self.setPos(x_pos, y_pos)

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """
        Show a pointer cursor over the port.

        :param event:
        :return:
        """
        QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """
        Restore the cursor when the pointer leaves the port.

        :param event:
        :return:
        """
        QApplication.restoreOverrideCursor()

    def is_connected(self) -> bool:
        """
        Check whether the port already owns a connection list.

        :return:
        """
        if self.connections is not None:
            return True
        else:
            return False


class BranchingItem(QGraphicsEllipseItem):
    """
    Graphical branching point that can have one input and multiple outputs.
    Created when splitting a connection via double-click.
    """

    def __init__(self,
                 subsystem: BlockItem,
                 index: int,
                 radius: int = 6):
        """
        Build a connection branching point.

        :param source_connection: The connection to branch from.
        :param radius:
        """
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        fill_color: QColor = OUTPUT_PORT_FILL
        self.setBrush(QBrush(fill_color))
        self.setPen(QPen(PORT_BORDER, 1.5))
        self.setZValue(3)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.subsystem: BlockItem = subsystem
        self.index: int = index
        self.connections: List["ConnectionItem"] | None = None

        self.base_var: Var | None = None

        # self.input_port: PortItem = PortItem(self, True, 0, 1, radius=5)
        # self.output_port: PortItem = PortItem(self, False, 0, 1, radius=5)
        # self.input_port.connections = None
        # self.output_port.connections = None

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """
        Show a pointer cursor over the port.

        :param event:
        :return:
        """
        QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """
        Restore the cursor when the pointer leaves the port.

        :param event:
        :return:
        """
        QApplication.restoreOverrideCursor()

    def is_connected(self) -> bool:
        """
        Check whether the port already owns a connection list.

        :return:
        """
        if self.connections is not None:
            return True
        else:
            return False


class ConnectionItem(QGraphicsPathItem):
    """
    Orthogonal graphical connection between two ports.
    Uses global OrthogonalRouter for path computation.
    """

    def __init__(self, source_port: PortItem | BranchingItem, target_port: PortItem | BranchingItem,
                 diagram=None, con_uid=None, uid=None, elbow_points: List[QPointF] = None):
        """
        Build the connection item.

        :param source_port:
        :param target_port:
        :param diagram: BlockDiagram reference
        :param con_uid: Connection uid in the diagram
        :param uid: Optional specific uid to use
        :param elbow_points: List of QPointF for editable elbow positions
        """
        super().__init__()
        self.uid: int = uid if uid is not None else _new_uid()
        self.setZValue(-1)
        self.source_port: PortItem | BranchingItem = source_port
        self.target_port: PortItem | BranchingItem = target_port
        self.diagram = diagram
        self.con_uid = con_uid if con_uid is not None else self.uid

        if self.source_port.connections is None:
            self.source_port.connections = list()
        self.source_port.connections.append(self)

        if self.target_port.connections is None:
            self.target_port.connections = list()
        self.target_port.connections.append(self)

        if isinstance(self.source_port.subsystem, BlockItem):
            self.source_port.subsystem._refresh_connection_color()
        if isinstance(self.target_port.subsystem, BlockItem):
            self.target_port.subsystem._refresh_connection_color()

        self.setPen(QPen(WIRE_COLOR, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

        self.elbow_points: List[QPointF] = elbow_points if elbow_points is not None else []
        self.elbows: List[ElbowItem] = []
        self._dragging_segment: int = -1
        self._original_path_elements: List[QPointF] = []
        self.update_path()
        # self._create_elbow_items()

        if self.diagram is not None:
            self.diagram.add_branch(
                connectionitem_uid=self.con_uid,
                device_uid_from=self.source_port.subsystem.subsys.uid,
                device_uid_to=self.target_port.subsystem.subsys.uid,
                port_number_from=self.source_port.index,
                port_number_to=self.target_port.index,
                color=self.pen().color().name(),
                elbow_points=[(pt.x(), pt.y()) for pt in self.elbow_points]
            )

    def update_path(self) -> None:
        """
        Recompute the orthogonal path from current port positions.

        :return:
        """
        path: QPainterPath = QPainterPath(self.source_port.scenePos())

        if self.elbow_points:
            for pt in self.elbow_points:
                path.lineTo(pt)
        else:
            path = build_orthogonal_connection_path(
                self.source_port.scenePos(),
                self.target_port.scenePos()
            )

        path.lineTo(self.target_port.scenePos())
        self.setPath(path)

    def _create_elbow_items(self) -> None:
        for elbow in self.elbows:
            elbow.setParentItem(cast(QGraphicsItem | None, None))
            if elbow.scene():
                elbow.scene().removeItem(elbow)
        self.elbows.clear()

        for i, pt in enumerate(self.elbow_points):
            elbow = ElbowItem(self, i, pt)
            self.scene().addItem(elbow)
            self.elbows.append(elbow)

    def _on_elbow_moved(self, index: int, new_pos: QPointF) -> None:
        if index < 0 or index >= len(self.elbows):
            return

        self.elbow_points[index] = new_pos

        prev_pt = self.source_port.scenePos()
        next_pt = self.target_port.scenePos()

        if index > 0:
            prev_pt = self.elbow_points[index - 1]
        if index < len(self.elbow_points) - 1:
            next_pt = self.elbow_points[index + 1]

        dx1 = new_pos.x() - prev_pt.x()
        dy1 = new_pos.y() - prev_pt.y()
        dx2 = next_pt.x() - new_pos.x()
        dy2 = next_pt.y() - new_pos.y()

        if abs(dx1) > abs(dy1):
            self.elbow_points[index].setY(prev_pt.y())
        else:
            self.elbow_points[index].setX(prev_pt.x())

        if index < len(self.elbow_points) - 1:
            if abs(dx2) > abs(dy2):
                self.elbow_points[index + 1].setY(new_pos.y())
            else:
                self.elbow_points[index + 1].setX(new_pos.x())

        for i, elbow in enumerate(self.elbows):
            elbow.setPos(self.elbow_points[i])

        self.update_path()
        self._save_elbow_points()

    def _save_elbow_points(self) -> None:
        if self.con_uid in self.diagram.con_data:
            self.diagram.con_data[self.con_uid].elbow_points = [
                (pt.x(), pt.y()) for pt in self.elbow_points
            ]

    def _segment_hit_test(self, pos: QPointF, threshold: float = 12.0) -> tuple:
        """
        Find the segment closest to pos using actual path elements.
        Returns (segment_index, is_horizontal) or (-1, False) if none.
        """
        path: QPainterPath = self.path()
        if path.isEmpty():
            return (-1, False)

        elements: List[QPointF] = []
        for i in range(path.elementCount()):
            elem = path.elementAt(i)
            elements.append(QPointF(elem.x, elem.y))

        if len(elements) < 2:
            return (-1, False)

        for i in range(len(elements) - 1):
            p1: QPointF = elements[i]
            p2: QPointF = elements[i + 1]

            dy: float = abs(p2.y() - p1.y())
            dx: float = abs(p2.x() - p1.x())

            if dy < 1:
                if p1.y() - threshold <= pos.y() <= p1.y() + threshold:
                    if min(p1.x(), p2.x()) - threshold <= pos.x() <= max(p1.x(), p2.x()) + threshold:
                        return (i, True)
            elif dx < 1:
                if p1.x() - threshold <= pos.x() <= p1.x() + threshold:
                    if min(p1.y(), p2.y()) - threshold <= pos.y() <= max(p1.y(), p2.y()) + threshold:
                        return (i, False)
            else:
                min_x: float = min(p1.x(), p2.x()) - threshold
                max_x: float = max(p1.x(), p2.x()) + threshold
                min_y: float = min(p1.y(), p2.y()) - threshold
                max_y: float = max(p1.y(), p2.y()) + threshold
                if min_x <= pos.x() <= max_x and min_y <= pos.y() <= max_y:
                    return (i, False)

        return (-1, False)

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        scene_pos: QPointF = event.scenePos()
        seg_idx, is_horizontal = self._segment_hit_test(scene_pos)
        if seg_idx >= 0:
            self._dragging_segment = seg_idx
            self._original_path_elements = []
            path: QPainterPath = self.path()
            for i in range(path.elementCount()):
                elem = path.elementAt(i)
                self._original_path_elements.append(QPointF(elem.x, elem.y))
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if self._dragging_segment >= 0:
            new_pos: QPointF = event.scenePos()

            path: QPainterPath = self.path()
            elements: List[QPointF] = []
            for i in range(path.elementCount()):
                elem = path.elementAt(i)
                elements.append(QPointF(elem.x, elem.y))

            if not elements or self._dragging_segment >= len(elements) - 1:
                super().mouseMoveEvent(event)
                return

            seg_idx: int = self._dragging_segment
            p1: QPointF = elements[seg_idx]
            p2: QPointF = elements[seg_idx + 1]

            dy: float = abs(p2.y() - p1.y())
            dx: float = abs(p2.x() - p1.x())

            if dy < 1:
                new_y: float = new_pos.y()
                new_x: float = p1.x()
            elif dx < 1:
                new_x: float = new_pos.x()
                new_y: float = p1.y()
            else:
                new_x = new_pos.x()
                new_y = new_pos.y()

            new_elements: List[QPointF] = [QPointF(pt) for pt in elements]

            if dy < 1:
                if seg_idx == 0:
                    new_elements[seg_idx + 1] = QPointF(elements[seg_idx + 1].x(), new_y)
                elif seg_idx == len(elements) - 2:
                    new_elements[seg_idx] = QPointF(elements[seg_idx].x(), new_y)
                else:
                    new_elements[seg_idx] = QPointF(elements[seg_idx].x(), new_y)
                    new_elements[seg_idx + 1] = QPointF(elements[seg_idx + 1].x(), new_y)
            elif dx < 1:
                if seg_idx == 0:
                    new_elements[seg_idx + 1] = QPointF(new_x, elements[seg_idx + 1].y())
                elif seg_idx == len(elements) - 2:
                    new_elements[seg_idx] = QPointF(new_x, elements[seg_idx].y())
                else:
                    new_elements[seg_idx] = QPointF(new_x, elements[seg_idx].y())
                    new_elements[seg_idx + 1] = QPointF(new_x, elements[seg_idx + 1].y())

            self._rebuild_path_from_elements(new_elements)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def _rebuild_path_from_elements(self, elements: List[QPointF]) -> None:
        """
        Rebuild the path and elbow_points from a list of points.
        """
        if len(elements) < 2:
            return

        path: QPainterPath = QPainterPath(elements[0])
        for i in range(1, len(elements)):
            path.lineTo(elements[i])
        self.setPath(path)

        if len(elements) > 2:
            self.elbow_points = elements[1:-1]
        else:
            self.elbow_points = []
        self._save_elbow_points()

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if self._dragging_segment >= 0:
            self._dragging_segment = -1
            self._original_path_elements = []
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """
        Show a pointer cursor over the connection.

        :param event:
        :return:
        """
        QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)
        pen: QPen = self.pen()
        pen.setColor(WIRE_HOVER_COLOR)
        pen.setWidthF(3.5)
        self.setPen(pen)

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """
        Restore the cursor when the pointer leaves the connection.

        :param event:
        :return:
        """
        QApplication.restoreOverrideCursor()
        pen: QPen = self.pen()
        pen.setColor(WIRE_COLOR)
        pen.setWidthF(2.5)
        self.setPen(pen)


class ElbowItem(QGraphicsEllipseItem):
    def __init__(self, connection_item: "ConnectionItem", index: int, pos: QPointF = QPointF()):
        radius = 5
        super().__init__(-radius, -radius, radius * 2, radius * 2)
        self.connection_item = connection_item
        self.index = index
        self.setBrush(QBrush(WIRE_COLOR))
        self.setPen(QPen(QColor("#173042"), 1.5))
        self.setZValue(2)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setPos(pos)
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            scene = self.connection_item.scene()
            if scene is not None:
                rect = scene.sceneRect()
                x = max(rect.left(), min(value.x(), rect.right()))
                y = max(rect.top(), min(value.y(), rect.bottom()))
                return QPointF(x, y)
        return super().itemChange(change, value)
    
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.connection_item._on_elbow_moved(self.index, self.scenePos())


class ExpressionTextEditorDialog(QDialog):
    """
    Dialog used to inspect or edit a symbolic expression as text.
    """

    def __init__(self,
                 expression_text: str,
                 symbol_namespace: Dict[str, Expr],
                 parent: Optional[QtWidgets.QWidget] = None):
        """
        Build the expression text editor dialog.

        :param expression_text:
        :param symbol_namespace:
        :param parent:
        """
        super().__init__(parent)
        self.setWindowTitle("Edit Expression")
        self.resize(520, 260)
        self.symbol_namespace: Dict[str, Expr] = symbol_namespace
        self.validation_label: QLabel
        self.button_box: QDialogButtonBox
        self.ok_button: QtWidgets.QPushButton
        self.highlighter: ExpressionValidationHighlighter

        layout: QVBoxLayout = QVBoxLayout(self)
        info_label: QLabel = QLabel("Edit the symbolic expression text:")
        layout.addWidget(info_label)

        self.text_editor: QPlainTextEdit = QPlainTextEdit(self)
        editor_font: QtGui.QFont = QtGui.QFont("DejaVu Sans Mono", 10)
        self.text_editor.setFont(editor_font)
        self.text_editor.setPlainText(expression_text)
        self.text_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.text_editor)

        self.validation_label = QLabel("")
        layout.addWidget(self.validation_label)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.highlighter = ExpressionValidationHighlighter(
            document=self.text_editor.document(),
            symbol_names=set(self.symbol_namespace.keys()),
            function_names=set(get_symbolic_parser_function_names())
        )
        self.text_editor.textChanged.connect(self.update_validation_state)
        self.update_validation_state()

    def get_expression_text(self) -> str:
        """
        Return the edited expression text.

        :return:
        """
        return self.text_editor.toPlainText().strip()

    def update_validation_state(self) -> None:
        """
        Validate the current expression text and update the dialog status widgets.

        :return:
        """
        expression_text: str = self.get_expression_text()
        unknown_identifiers: List[str] = self.highlighter.get_unknown_identifiers(expression_text)

        if len(unknown_identifiers) > 0:
            self.validation_label.setText(
                "Unknown symbols: " + ", ".join(sorted(set(unknown_identifiers)))
            )
            self.validation_label.setStyleSheet("color: #b42318;")
            self.ok_button.setEnabled(False)
        else:
            try:
                string_to_symbolic(expression_text, self.symbol_namespace)
                self.validation_label.setText("Expression is valid.")
                self.validation_label.setStyleSheet("color: #027a48;")
                self.ok_button.setEnabled(True)
            except Exception as exc:
                self.validation_label.setText(str(exc))
                self.validation_label.setStyleSheet("color: #b42318;")
                self.ok_button.setEnabled(False)


class AddBlockVariableDialog(QDialog):
    """
    Dialog used to create a new variable or parameter in the selected block.
    """

    CATEGORY_OPTIONS: List[tuple[str, str]] = [
        ("State", "state"),
        ("Algebraic", "algebraic"),
        ("Input", "in"),
        ("Output", "out"),
        ("Event Parameter", "event_parameter"),
        ("Mode Parameter", "mode_parameter"),
        ("Static Parameter", "parameter"),
    ]

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Add Variable")
        self.resize(360, 160)

        layout: QVBoxLayout = QVBoxLayout(self)
        form_layout: QFormLayout = QFormLayout()
        layout.addLayout(form_layout)

        self.name_edit: QLineEdit = QLineEdit(self)
        self.category_combo: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        self.parameter_value_spin: QDoubleSpinBox = QDoubleSpinBox(self)
        self.parameter_value_spin.setDecimals(8)
        self.parameter_value_spin.setMinimum(-1e200)
        self.parameter_value_spin.setMaximum(1e200)
        self.parameter_value_spin.setValue(0.0)

        label: str
        value: str
        for label, value in self.CATEGORY_OPTIONS:
            self.category_combo.addItem(label, value)

        form_layout.addRow("Name", self.name_edit)
        form_layout.addRow("Category", self.category_combo)
        form_layout.addRow("Initial value", self.parameter_value_spin)

        self.validation_label: QLabel = QLabel("", self)
        layout.addWidget(self.validation_label)

        self.button_box: QDialogButtonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self
        )
        self.ok_button: QtWidgets.QPushButton = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.name_edit.textChanged.connect(self.update_validation_state)
        self.category_combo.currentIndexChanged.connect(self.update_validation_state)
        self.update_validation_state()

    def get_name(self) -> str:
        return self.name_edit.text().strip()

    def get_category(self) -> str:
        return str(self.category_combo.currentData())

    def get_parameter_value(self) -> float:
        return float(self.parameter_value_spin.value())

    def update_validation_state(self) -> None:
        """
        Validate the new symbol data before allowing acceptance.

        :return:
        """
        category: str = self.get_category()
        name: str = self.get_name()
        is_parameter: bool = category in {"parameter", "event_parameter", "mode_parameter"}

        self.parameter_value_spin.setEnabled(is_parameter)

        if len(name) == 0:
            self.validation_label.setText("Enter a symbol name.")
            self.validation_label.setStyleSheet("color: #b42318;")
            self.ok_button.setEnabled(False)
        elif not is_valid_symbol_name(name):
            self.validation_label.setText("Use a valid identifier: letters, digits, and underscore.")
            self.validation_label.setStyleSheet("color: #b42318;")
            self.ok_button.setEnabled(False)
        else:
            self.validation_label.setText("New symbol is valid.")
            self.validation_label.setStyleSheet("color: #027a48;")
            self.ok_button.setEnabled(True)


class AddParameterDialog(QDialog):
    """
    Dialog used to create a new parameter (event, mode, or regular) in the selected block.
    """

    CATEGORY_OPTIONS: List[tuple[str, str]] = [
        ("Event Parameter", "event_parameter"),
        ("Mode Parameter", "mode_parameter"),
        ("Static Parameter", "parameter"),
    ]

    def __init__(self, api_object: Any, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Add Parameter")
        self.resize(360, 200)
        self.api_object = api_object

        layout: QVBoxLayout = QVBoxLayout(self)
        form_layout: QFormLayout = QFormLayout()
        layout.addLayout(form_layout)

        self.name_edit: QLineEdit = QLineEdit(self)
        self.category_combo: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        self.parameter_value_label: QLabel = QLabel("Initial value", self)
        self.parameter_value_spin: QDoubleSpinBox = QDoubleSpinBox(self)
        self.parameter_value_spin.setDecimals(8)
        self.parameter_value_spin.setMinimum(-1e200)
        self.parameter_value_spin.setMaximum(1e200)
        self.parameter_value_spin.setValue(0.0)
        self.static_variable_label: QLabel = QLabel("Static Variable", self)
        self.static_variable_combo: QtWidgets.QComboBox = QtWidgets.QComboBox(self)

        if self.api_object is not None:
            device_type = self.api_object.device_type
            static_params = devices_static_params_mapping.get(device_type, [])
            for param in static_params:
                self.static_variable_combo.addItem(param.value, param)

        label: str
        value: str
        for label, value in self.CATEGORY_OPTIONS:
            self.category_combo.addItem(label, value)

        form_layout.addRow("Name", self.name_edit)
        form_layout.addRow("Category", self.category_combo)
        form_layout.addRow(self.parameter_value_label, self.parameter_value_spin)
        form_layout.addRow(self.static_variable_label, self.static_variable_combo)

        self.validation_label: QLabel = QLabel("", self)
        layout.addWidget(self.validation_label)

        self.button_box: QDialogButtonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self
        )
        self.ok_button: QtWidgets.QPushButton = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.name_edit.textChanged.connect(self.update_validation_state)
        self.category_combo.currentIndexChanged.connect(self.update_validation_state)
        self.update_validation_state()

    def get_name(self) -> str:
        return self.name_edit.text().strip()

    def get_category(self) -> str:
        return str(self.category_combo.currentData())

    def get_parameter_value(self) -> float:
        return float(self.parameter_value_spin.value())

    def get_static_variable(self) -> ParamPowerFlowReferenceType | None:
        return self.static_variable_combo.currentData()

    def update_validation_state(self) -> None:
        """
        Validate the new symbol data before allowing acceptance.

        :return:
        """
        category: str = self.get_category()
        name: str = self.get_name()
        is_event_or_mode: bool = category in {"event_parameter", "mode_parameter"}
        is_parameter: bool = category == "parameter"

        if is_event_or_mode:
            self.parameter_value_label.setEnabled(True)
            self.parameter_value_spin.setEnabled(True)
            self.static_variable_label.setEnabled(False)
            self.static_variable_combo.setEnabled(False)
        elif is_parameter:
            self.parameter_value_label.setEnabled(False)
            self.parameter_value_spin.setEnabled(False)
            self.static_variable_label.setEnabled(True)
            self.static_variable_combo.setEnabled(True)
        else:
            self.parameter_value_label.setEnabled(False)
            self.parameter_value_spin.setEnabled(False)
            self.static_variable_label.setEnabled(False)
            self.static_variable_combo.setEnabled(False)

        if len(name) == 0:
            self.validation_label.setText("Enter a symbol name.")
            self.validation_label.setStyleSheet("color: #b42318;")
            self.ok_button.setEnabled(False)
        elif not is_valid_symbol_name(name):
            self.validation_label.setText("Use a valid identifier: letters, digits, and underscore.")
            self.validation_label.setStyleSheet("color: #b42318;")
            self.ok_button.setEnabled(False)
        elif is_parameter and self.get_static_variable() is None:
            self.validation_label.setText("Select a static variable.")
            self.validation_label.setStyleSheet("color: #b42318;")
            self.ok_button.setEnabled(False)
        else:
            self.validation_label.setText("New symbol is valid.")
            self.validation_label.setStyleSheet("color: #027a48;")
            self.ok_button.setEnabled(True)


class AddEquationDialog(QDialog):
    """
    Dialog used to create a new equation (state or algebraic) in the selected block.
    """

    CATEGORY_OPTIONS: List[tuple[str, str]] = [
        ("State", "state"),
        ("Algebraic", "algebraic"),
    ]

    def __init__(self, symbol_namespace: Dict[str, Expr], parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Add Equation")
        self.resize(500, 200)
        self.symbol_namespace = symbol_namespace

        layout: QVBoxLayout = QVBoxLayout(self)
        form_layout: QFormLayout = QFormLayout()
        layout.addLayout(form_layout)

        self.equation_edit: QPlainTextEdit = QPlainTextEdit(self)
        editor_font: QtGui.QFont = QtGui.QFont("DejaVu Sans Mono", 10)
        self.equation_edit.setFont(editor_font)
        self.equation_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self.type_combo: QtWidgets.QComboBox = QtWidgets.QComboBox(self)

        for label, value in self.CATEGORY_OPTIONS:
            self.type_combo.addItem(label, value)

        form_layout.addRow("Equation", self.equation_edit)
        form_layout.addRow("Type", self.type_combo)

        self.validation_label: QLabel = QLabel("", self)
        layout.addWidget(self.validation_label)

        self.button_box: QDialogButtonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self
        )
        self.ok_button: QtWidgets.QPushButton = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.equation_edit.textChanged.connect(self.update_validation_state)
        self.update_validation_state()

    def get_equation_text(self) -> str:
        return self.equation_edit.toPlainText().strip()

    def get_category(self) -> str:
        return str(self.type_combo.currentData())

    def update_validation_state(self) -> None:
        """
        Validate the equation text before allowing acceptance.

        :return:
        """
        equation_text: str = self.get_equation_text()

        if len(equation_text) == 0:
            self.validation_label.setText("Enter an equation.")
            self.validation_label.setStyleSheet("color: #b42318;")
            self.ok_button.setEnabled(False)
            return

        try:
            parsed = string_to_symbolic(equation_text, self.symbol_namespace)
            self.validation_label.setText("Equation is valid.")
            self.validation_label.setStyleSheet("color: #027a48;")
            self.ok_button.setEnabled(True)
        except Exception as exc:
            self.validation_label.setText(str(exc))
            self.validation_label.setStyleSheet("color: #b42318;")
            self.ok_button.setEnabled(False)


class ExpressionValidationHighlighter(QtGui.QSyntaxHighlighter):
    """
    Syntax highlighter that validates symbolic identifiers against the selected block namespace.
    """

    IDENTIFIER_PATTERN = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")

    def __init__(self,
                 document: QtGui.QTextDocument,
                 symbol_names: Set[str],
                 function_names: Set[str]):
        """
        Build the expression validation highlighter.

        :param document:
        :param symbol_names:
        :param function_names:
        """
        super().__init__(document)
        self.symbol_names: Set[str] = symbol_names
        self.function_names: Set[str] = function_names
        self.ignored_tokens: Set[str] = {"True", "False", "None"}
        self.valid_symbol_format: QtGui.QTextCharFormat = QtGui.QTextCharFormat()
        self.function_format: QtGui.QTextCharFormat = QtGui.QTextCharFormat()
        self.invalid_format: QtGui.QTextCharFormat = QtGui.QTextCharFormat()

        self.valid_symbol_format.setFontWeight(QtGui.QFont.Weight.Bold)
        self.function_format.setForeground(QColor("#0b5394"))
        self.invalid_format.setForeground(QColor("#b42318"))

    def highlightBlock(self, text: str) -> None:
        """
        Highlight one text block according to identifier validity.

        :param text:
        :return:
        """
        match: re.Match[str]
        token: str
        start_pos: int
        token_length: int
        classification: str

        for match in self.IDENTIFIER_PATTERN.finditer(text):
            token = match.group(0)
            start_pos = match.start()
            token_length = match.end() - match.start()
            classification = self.classify_identifier(text, token, match.end())

            if classification == "valid_symbol":
                self.setFormat(start_pos, token_length, self.valid_symbol_format)
            elif classification == "valid_function":
                self.setFormat(start_pos, token_length, self.function_format)
            elif classification == "invalid":
                self.setFormat(start_pos, token_length, self.invalid_format)
            else:
                pass

    def classify_identifier(self, text: str, token: str, token_end: int) -> str:
        """
        Classify an identifier as a valid symbol, a valid function, or invalid.

        :param text:
        :param token:
        :param token_end:
        :return:
        """
        if self.is_function_call(text, token_end):
            if token in self.function_names:
                return "valid_function"
            else:
                return "invalid"
        elif token in self.symbol_names:
            return "valid_symbol"
        elif token in self.ignored_tokens:
            return "ignored"
        else:
            return "invalid"

    def is_function_call(self, text: str, token_end: int) -> bool:
        """
        Check whether an identifier is followed by a function-call parenthesis.

        :param text:
        :param token_end:
        :return:
        """
        current_index: int = token_end

        while current_index < len(text) and text[current_index].isspace():
            current_index += 1

        if current_index < len(text):
            return text[current_index] == "("
        else:
            return False

    def get_unknown_identifiers(self, text: str) -> List[str]:
        """
        Return the list of currently unknown identifiers in the editor text.

        :param text:
        :return:
        """
        unknown_identifiers: List[str] = list()
        line_text: str
        match: re.Match[str]
        token: str

        for line_text in text.splitlines():
            for match in self.IDENTIFIER_PATTERN.finditer(line_text):
                token = match.group(0)

                if self.classify_identifier(line_text, token, match.end()) == "invalid":
                    unknown_identifiers.append(token)
                else:
                    pass

        return unknown_identifiers


class BlockParameterKind(Enum):
    """
    Row kinds shown in the side editor table.
    """

    SECTION = "Section"
    STATE_VAR = "State Var"
    ALGEBRAIC_VAR = "Algebraic Var"
    INPUT_VAR = "Input Var"
    OUTPUT_VAR = "Output Var"
    STATE_EQUATION = "State Equation"
    ALGEBRAIC_EQUATION = "Algebraic Equation"
    EVENT_PARAMETER = "Event Parameter"
    MODE_PARAMETER = "Mode Parameter"
    FIXED_PARAMETER = "Static Parameter"
    MODE_PARAM = "Mode Parameter"


class BlockParameterRow:
    """
    Row description for the selected block editor table.
    """

    __slots__ = ("name", "kind", "key_var", "value", "editable_name", "editable_value", "value_type", "item_index",
                 "init_eq", "source_dict_name", "display_value", "display_init_eq", "search_text")

    def __init__(self,
                 name: str,
                 kind: BlockParameterKind,
                 key_var: Var | None,
                 value: Any,
                 editable_name: bool,
                 editable_value: bool,
                 value_type: type,
                 item_index: int | None = None,
                 init_eq: Expr | None = None,
                 source_dict_name: str | None = None):
        """
         Build a parameter row descriptor.

        :param name:
        :param kind:
        :param key_var:
        :param value:
        :param editable_name:
        :param editable_value:
        :param value_type:
        :param item_index:
        :param init_eq: Initial equation from block.init_eqs for this variable
        :param source_dict_name: Name of the source dict ('event_dict' or 'parameters')
        """
        self.name: str = name
        self.kind: BlockParameterKind = kind
        self.key_var: Var | None = key_var
        self.value: Any = value
        self.editable_name: bool = editable_name
        self.editable_value: bool = editable_value
        self.value_type: type = value_type
        self.item_index: int | None = item_index
        self.init_eq: Expr | None = init_eq
        self.source_dict_name: str | None = source_dict_name
        self.display_value: Any = None
        self.display_init_eq: Any = None
        self.search_text: str = ""
        refresh_block_parameter_row_cache(self)
        refresh_row_search_cache(self)

    @property
    def is_section(self) -> bool:
        return self.kind == BlockParameterKind.SECTION

    @property
    def opens_expression_editor(self) -> bool:
        return self.kind in {
            BlockParameterKind.STATE_EQUATION,
            BlockParameterKind.ALGEBRAIC_EQUATION,
            BlockParameterKind.EVENT_PARAMETER,
            BlockParameterKind.MODE_PARAMETER,
            BlockParameterKind.FIXED_PARAMETER,
        } and isinstance(self.value, Expr)


def build_block_parameter_display_value(value: Any) -> Any:
    """
    Return the cached visible representation for one table value.

    :param value: Raw row value.
    :return: Display-friendly cached value.
    """
    if isinstance(value, Expr):
        return symbolic_to_string(value)
    else:
        return value


def refresh_block_parameter_row_cache(row: BlockParameterRow) -> None:
    """
    Refresh the cached visible text for one row.

    :param row: Row to update.
    :return: None.
    """
    row.display_value = build_block_parameter_display_value(row.value)

    if row.init_eq is not None:
        row.display_init_eq = build_block_parameter_display_value(row.init_eq)
    else:
        row.display_init_eq = None


def refresh_row_search_cache(row: BlockParameterRow) -> None:
    parts = [str(row.name or "")]
    if row.value is not None:
        parts.append(str(row.value))
    if row.init_eq is not None:
        parts.append(str(row.init_eq))
    if row.display_value is not None:
        parts.append(str(row.display_value))
    if row.display_init_eq is not None:
        parts.append(str(row.display_init_eq))
    row.search_text = " ".join(parts).lower()


class BlockValueDelegate(QtWidgets.QStyledItemDelegate):
    """
    Delegate that chooses an appropriate editor based on the row kind.
    Inspects row.kind to decide: float spinbox for numeric parameters,
    text editor for symbolic expressions, etc.
    """

    def createEditor(self,
                     parent: QtWidgets.QWidget,
                     option: QtWidgets.QStyleOptionViewItem,
                     index: QtCore.QModelIndex) -> QtWidgets.QWidget | None:
        model = index.model()
        if isinstance(model, QtCore.QSortFilterProxyModel):
            source_index = model.mapToSource(index)
            source_model = model.sourceModel()
            row = source_model.get_row(source_index.row()) if hasattr(source_model, 'get_row') else None
        else:
            row = model.get_row(index.row()) if hasattr(model, 'get_row') else None
        if row is None:
            return QLineEdit(parent)

        if not row.editable_value:
            return None

        if row.is_section:
            return None

        if row.kind in (BlockParameterKind.STATE_VAR, BlockParameterKind.ALGEBRAIC_VAR):
            return QLineEdit(parent)

        elif row.kind in (BlockParameterKind.EVENT_PARAMETER, BlockParameterKind.MODE_PARAMETER):
            editor = self._make_float_editor(parent) if row.value_type == float else QLineEdit(parent)
            return editor

        elif row.kind == BlockParameterKind.FIXED_PARAMETER:
            editor = self._make_float_editor(parent) if row.value_type == float else QLineEdit(parent)
            return editor

        elif row.kind in (BlockParameterKind.STATE_EQUATION,
                          BlockParameterKind.ALGEBRAIC_EQUATION):
            return QLineEdit(parent)

        return QLineEdit(parent)

    @staticmethod
    def _make_float_editor(parent: QtWidgets.QWidget) -> QDoubleSpinBox:
        editor = QDoubleSpinBox(parent)
        editor.setDecimals(8)
        editor.setMinimum(-1e200)
        editor.setMaximum(1e200)
        return editor

    def setEditorData(self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex) -> None:
        value = index.model().data(index, QtCore.Qt.ItemDataRole.EditRole)
        if isinstance(editor, QDoubleSpinBox):
            try:
                editor.setValue(float(value))
            except (TypeError, ValueError):
                editor.setValue(0.0)
        elif isinstance(editor, QLineEdit):
            editor.setText(str(value) if value is not None else "")

    def setModelData(self,
                     editor: QtWidgets.QWidget,
                     model: QtCore.QAbstractItemModel,
                     index: QtCore.QModelIndex) -> None:
        if isinstance(editor, QDoubleSpinBox):
            model.setData(index, editor.value(), QtCore.Qt.ItemDataRole.EditRole)
        elif isinstance(editor, QLineEdit):
            model.setData(index, editor.text(), QtCore.Qt.ItemDataRole.EditRole)


class EditParameterDialog(QDialog):
    """
    Dialog used to edit an existing parameter's type (event, mode, or regular).
    """

    CATEGORY_OPTIONS: List[tuple[str, BlockParameterKind]] = [
        ("Event Parameter", BlockParameterKind.EVENT_PARAMETER),
        ("Mode Parameter", BlockParameterKind.MODE_PARAMETER),
        ("Static Parameter", BlockParameterKind.FIXED_PARAMETER),
    ]

    _KIND_TO_STRING: dict = {
        BlockParameterKind.EVENT_PARAMETER: "event_parameter",
        BlockParameterKind.MODE_PARAMETER: "mode_parameter",
        BlockParameterKind.FIXED_PARAMETER: "parameter",
    }

    def __init__(self, api_object: Any, current_kind: BlockParameterKind, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Parameter Type")
        self.resize(360, 200)
        self.api_object = api_object

        layout: QVBoxLayout = QVBoxLayout(self)
        form_layout: QFormLayout = QFormLayout()
        layout.addLayout(form_layout)

        self.category_combo: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        self.parameter_value_label: QLabel = QLabel("Initial value", self)
        self.parameter_value_spin: QDoubleSpinBox = QDoubleSpinBox(self)
        self.parameter_value_spin.setDecimals(8)
        self.parameter_value_spin.setMinimum(-1e200)
        self.parameter_value_spin.setMaximum(1e200)
        self.parameter_value_spin.setValue(0.0)
        self.static_variable_label: QLabel = QLabel("Static Variable", self)
        self.static_variable_combo: QtWidgets.QComboBox = QtWidgets.QComboBox(self)

        if self.api_object is not None:
            device_type = self.api_object.device_type
            static_params = devices_static_params_mapping.get(device_type, [])
            for param in static_params:
                self.static_variable_combo.addItem(param.value, param)

        label: str
        value: BlockParameterKind
        for label, value in self.CATEGORY_OPTIONS:
            self.category_combo.addItem(label, value)

        self._current_kind = current_kind
        for i in range(self.category_combo.count()):
            if self.category_combo.itemData(i) == current_kind:
                self.category_combo.setCurrentIndex(i)
                break

        form_layout.addRow("Category", self.category_combo)
        form_layout.addRow(self.parameter_value_label, self.parameter_value_spin)
        form_layout.addRow(self.static_variable_label, self.static_variable_combo)

        self.validation_label: QLabel = QLabel("", self)
        layout.addWidget(self.validation_label)

        self.button_box: QDialogButtonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self
        )
        self.ok_button: QtWidgets.QPushButton = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.category_combo.currentIndexChanged.connect(self.update_visibility)
        self.update_visibility()

    def get_category(self) -> str:
        kind: BlockParameterKind = self.category_combo.currentData()
        return self._KIND_TO_STRING.get(kind, "")

    def get_category_kind(self) -> BlockParameterKind:
        return self.category_combo.currentData()

    def get_parameter_value(self) -> float:
        return float(self.parameter_value_spin.value())

    def get_static_variable(self) -> ParamPowerFlowReferenceType | None:
        return self.static_variable_combo.currentData()

    def update_visibility(self) -> None:
        kind: BlockParameterKind = self.get_category_kind()
        is_event_or_mode: bool = kind in {BlockParameterKind.EVENT_PARAMETER, BlockParameterKind.MODE_PARAMETER}
        is_parameter: bool = kind == BlockParameterKind.FIXED_PARAMETER

        if is_event_or_mode:
            self.parameter_value_label.setEnabled(True)
            self.parameter_value_spin.setEnabled(True)
            self.static_variable_label.setEnabled(False)
            self.static_variable_combo.setEnabled(False)
        elif is_parameter:
            self.parameter_value_label.setEnabled(False)
            self.parameter_value_spin.setEnabled(False)
            self.static_variable_label.setEnabled(True)
            self.static_variable_combo.setEnabled(True)
        else:
            self.parameter_value_label.setEnabled(False)
            self.parameter_value_spin.setEnabled(False)
            self.static_variable_label.setEnabled(False)
            self.static_variable_combo.setEnabled(False)


class WrappableBlockTableModel(WrappableTableModel):
    """
    ViewModel that adapts a Block for Qt table views.

    Modes:
        - "variables": columns Type, Name, Init Equation
        - "parameters": columns Type, Name, Value
        - "equations": columns Type, Equation
        - "all": columns Type, Name, Value

    Block is the single source of truth.
    This model only generates adapted rows for the GUI.
    """

    block_updated = Signal(object)

    def __init__(self,
                 var_factory: VarFactory,
                 api_object: Any = None,
                 parent: Optional[QtCore.QObject] = None):
        super().__init__(parent)
        self._table_view = parent
        self.var_factory = var_factory
        self.api_object = api_object
        self.block = None
        self.rows: List[BlockParameterRow] = []
        self.mode = DynamicTableModelMode.VARIABLES
        self.headers = ["Type", "Name", "Init Equation"]
        self.symbol_namespace = None
        self._value_column = 2

    def set_mode(self, mode: DynamicTableModelMode) -> None:
        self.mode = mode
        if mode == DynamicTableModelMode.VARIABLES:
            self.headers = ["Type", "Name", "Init Equation"]
            self._value_column = 2
        elif mode == DynamicTableModelMode.PARAMETERS:
            self.headers = ["Type", "Name", "Value"]
            self._value_column = 2
        elif mode == DynamicTableModelMode.EQUATIONS:
            self.headers = ["Type", "Equation"]
            self._value_column = 1
        self.rebuild()

    def set_block(self, block: Block | None) -> None:
        self.block = block
        self.rebuild()

    def rebuild(self) -> None:
        self.beginResetModel()
        self.rows.clear()
        if self.block is not None:
            if self.mode == DynamicTableModelMode.VARIABLES:
                build_variables_rows(self.block, self.rows)
            elif self.mode == DynamicTableModelMode.PARAMETERS:
                build_parameters_rows(self, self.block, self.rows)
            elif self.mode == DynamicTableModelMode.EQUATIONS:
                build_equations_rows(self.block, self.rows)
        self.endResetModel()

    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        return len(self.rows)

    def columnCount(self, parent=QtCore.QModelIndex()) -> int:
        return 2 if self.mode == DynamicTableModelMode.EQUATIONS else 3

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or self.block is None:
            return None
        row = self.rows[index.row()]
        col = index.column()

        if role in (QtCore.Qt.ItemDataRole.DisplayRole, QtCore.Qt.ItemDataRole.EditRole):
            if col == 0:
                return row.kind.value
            elif col == 1:
                if self.mode == DynamicTableModelMode.EQUATIONS:
                    return row.display_value
                return row.name
            elif col == 2:
                if self.mode == DynamicTableModelMode.VARIABLES:
                    return row.display_init_eq if row.init_eq is not None else row.display_value
                elif self.mode == DynamicTableModelMode.PARAMETERS:
                    if row.kind == BlockParameterKind.FIXED_PARAMETER:
                        return row.value
                    return row.display_value
        elif role == PARAMETER_VALUE_TYPE_ROLE and col == self._value_column:
            if self.mode == DynamicTableModelMode.VARIABLES:
                return "float" if row.value_type == float else "text"
            return self.get_python_value_type(row.value).__name__
        elif role == PARAMETER_EDITABLE_ROLE and col == self._value_column:
            if self.mode == DynamicTableModelMode.PARAMETERS and row.kind == BlockParameterKind.FIXED_PARAMETER:
                return False
            return row.editable_value
        elif role == QtCore.Qt.ItemDataRole.BackgroundRole:
            if col == 2 and self.mode == DynamicTableModelMode.PARAMETERS and not row.editable_value and row.kind != BlockParameterKind.FIXED_PARAMETER:
                return QColor("#d3d3d3")
            return QColor("#f7fafc")
        elif role == QtCore.Qt.ItemDataRole.ForegroundRole:
            return QColor("#333333")
        elif role == BLOCK_SEARCH_ROLE:
            return row.search_text
        return None

    def setData(self, index, value, role=QtCore.Qt.ItemDataRole.EditRole):
        if not index.isValid() or role != QtCore.Qt.ItemDataRole.EditRole:
            return False
        row = self.rows[index.row()]
        col = index.column()

        if col == 1:
            if self.mode == DynamicTableModelMode.EQUATIONS:
                old_expr = row.value
                try:
                    namespace = self.symbol_namespace
                    if namespace is None and self.block is not None:
                        namespace = build_block_symbol_namespace(self.block)
                    new_expr = string_to_symbolic(value, namespace)
                    row.value = new_expr
                    refresh_block_parameter_row_cache(row)
                    refresh_row_search_cache(row)
                    update_source_dict(self.block, row, row.value, old_expr)
                    self.dataChanged.emit(index, index, [role])
                    self.block_updated.emit(self.block.uid)
                    return True
                except Exception:
                    return False
            if row.key_var is not None:
                row.key_var.name = value
            row.name = value
            refresh_row_search_cache(row)
            self.dataChanged.emit(index, index, [role])
            return True

        elif col == 2 and self.mode != DynamicTableModelMode.EQUATIONS:
            if not row.editable_value:
                return False
            if self.mode == DynamicTableModelMode.VARIABLES:
                row.value = value
                refresh_block_parameter_row_cache(row)
                refresh_row_search_cache(row)
                self.dataChanged.emit(index, index, [role])
                return True
            elif self.mode == DynamicTableModelMode.PARAMETERS:
                try:
                    parsed_value = _parse_symbolic_editor_value(self.block, value)
                except Exception:
                    return False
                row.value = parsed_value
                refresh_block_parameter_row_cache(row)
                refresh_row_search_cache(row)
                update_source_dict(self.block, row, parsed_value)
                self.dataChanged.emit(index, index, [role])
                self.block_updated.emit(self.block.uid)
                return True

        return False

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemFlag.NoItemFlags
        if index.row() < 0 or index.row() >= len(self.rows):
            return QtCore.Qt.ItemFlag.NoItemFlags
        row = self.rows[index.row()]
        col = index.column()
        flags = QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable

        if self.mode == DynamicTableModelMode.VARIABLES:
            if col == 1:
                flags |= QtCore.Qt.ItemFlag.ItemIsEditable
            elif col == 2 and row.editable_value:
                flags |= QtCore.Qt.ItemFlag.ItemIsEditable
        elif self.mode == DynamicTableModelMode.PARAMETERS:
            if col == 1:
                flags |= QtCore.Qt.ItemFlag.ItemIsEditable
            elif col == 2 and row.editable_value and row.kind != BlockParameterKind.FIXED_PARAMETER:
                flags |= QtCore.Qt.ItemFlag.ItemIsEditable
        elif self.mode == DynamicTableModelMode.EQUATIONS:
            if col == 1:
                flags |= QtCore.Qt.ItemFlag.ItemIsEditable

        return flags

    def headerData(self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if role == QtCore.Qt.ItemDataRole.DisplayRole and orientation == QtCore.Qt.Orientation.Horizontal:
            if section < len(self.headers):
                return self.headers[section]
        return None

    def get_row(self, row_index: int) -> BlockParameterRow | None:
        if 0 <= row_index < len(self.rows):
            return self.rows[row_index]
        return None

    def set_delegates(self) -> None:
        if self._table_view is None:
            return
        view = self._table_view

        if self.mode == DynamicTableModelMode.VARIABLES:
            delegate = ComboDelegate(view, ["State", "Algebraic"], ["State", "Algebraic"])
            view.setItemDelegateForColumn(0, delegate)
            delegate = TextDelegate(view)
            view.setItemDelegateForColumn(1, delegate)
            delegate = BlockValueDelegate(view)
            view.setItemDelegateForColumn(2, delegate)

        elif self.mode == DynamicTableModelMode.PARAMETERS:
            delegate = ComboDelegate(
                view,
                ["Event Parameter", "Mode Parameter", "Static Parameter"],
                ["Event Parameter", "Mode Parameter", "Static Parameter"]
            )
            view.setItemDelegateForColumn(0, delegate)
            delegate = TextDelegate(view)
            view.setItemDelegateForColumn(1, delegate)
            delegate = BlockValueDelegate(view)
            view.setItemDelegateForColumn(2, delegate)

        elif self.mode == DynamicTableModelMode.EQUATIONS:
            delegate = BlockValueDelegate(view)
            view.setItemDelegateForColumn(1, delegate)

    def set_init_eq(self, row_index: int, init_eq: Expr) -> None:
        if 0 <= row_index < len(self.rows):
            row = self.rows[row_index]
            row.init_eq = init_eq
            refresh_block_parameter_row_cache(row)
            refresh_row_search_cache(row)
            if self.block is not None and row.key_var is not None:
                update_source_dict(self.block, row, init_eq)
            index = self.index(row_index, 2)
            self.dataChanged.emit(index, index, [QtCore.Qt.ItemDataRole.EditRole])

    def set_value_from_expression(self, row_index: int, expr: Expr) -> None:
        if 0 <= row_index < len(self.rows):
            row = self.rows[row_index]
            row.value = expr
            refresh_block_parameter_row_cache(row)
            refresh_row_search_cache(row)
            update_source_dict(self.block, row, expr)
            index = self.index(row_index, self._value_column)
            self.dataChanged.emit(index, index, [QtCore.Qt.ItemDataRole.EditRole])

    def add_variable_at_end_of_type(self, name: str, category: str, parameter_value: float = 0.0) -> None:
        if self.block is None:
            raise ValueError("No block is currently selected.")
        new_var = self.var_factory.add_var(name=name)
        if category == "state":
            self.block.state_vars.append(new_var)
            if parameter_value != 0.0:
                self.block.init_values[new_var] = self.var_factory.add_const(parameter_value, name=name)
        elif category == "algebraic":
            self.block.algebraic_vars.append(new_var)
        else:
            raise ValueError(f"Unsupported category: {category}")
        self.set_block(self.block)
        self.block_updated.emit(self.block.uid)

    def get_last_index_of_type(self, var_type: str) -> int:
        if var_type == "state":
            return len(self.block.state_vars) - 1 if self.block and self.block.state_vars else -1
        elif var_type == "algebraic":
            return len(self.rows) - 1 if self.block and self.block.algebraic_vars else -1
        return -1

    @staticmethod
    def get_python_value_type(value) -> type:
        if isinstance(value, int):
            return int
        elif isinstance(value, float):
            return float
        return str


class InspectModel(QWidget):
    """
    InspectModel
    """

    def __init__(self, block: Block, parent=None):
        super().__init__(parent)

        self.block = block  # DynamicModelHost

        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)

        # ----------------- LEFT PANEL -----------------
        left_panel = QVBoxLayout()
        main_layout.addLayout(left_panel)

        # Variables
        var_header_layout = QHBoxLayout()
        var_label = QLabel("Variables")
        var_header_layout.addWidget(var_label)
        left_panel.addLayout(var_header_layout)

        self.list_vars = QListWidget()
        left_panel.addWidget(self.list_vars)

        # Parameters (table)
        param_header_layout = QHBoxLayout()
        param_label = QLabel("Parameters")
        param_header_layout.addWidget(param_label)
        left_panel.addLayout(param_header_layout)

        self.table_params = QTableWidget()
        self.table_params.setColumnCount(2)
        self.table_params.setHorizontalHeaderLabels(["Name", "Value"])
        self.table_params.horizontalHeader().setStretchLastSection(True)
        self.table_params.verticalHeader().setVisible(False)
        self.table_params.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # make read-only for now
        left_panel.addWidget(self.table_params)

        # ----------------- RIGHT PANEL -----------------
        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel)

        eqn_header_layout = QHBoxLayout()
        eqn_label = QLabel("Equations")
        eqn_header_layout.addWidget(eqn_label)
        right_panel.addLayout(eqn_header_layout)

        self.list_eqns = QListWidget()
        right_panel.addWidget(self.list_eqns)

        # Initial population
        self.refresh_lists(self.block)

    def refresh_lists(self, model=None, clear=True):
        """Load current model variables, parameters, equations into lists."""
        if model is None:
            model = self.block

        if clear:
            self.list_vars.clear()
            self.table_params.setRowCount(0)
            self.list_eqns.clear()

        # --- Variables ---
        for var in model.state_vars + model.algebraic_vars:
            item = QListWidgetItem(f"{var.name} ")
            # ({'state' if var in model.state_vars else 'algebraic'})
            self.list_vars.addItem(item)

        # --- Parameters ---
        for param, value in model.parameters.items():
            row = self.table_params.rowCount()
            self.table_params.insertRow(row)
            self.table_params.setItem(row, 0, QTableWidgetItem(str(param)))
            self.table_params.setItem(row, 1, QTableWidgetItem(str(model.parameters[param])))

        for param, value in model.event_dict.items():
            row = self.table_params.rowCount()
            self.table_params.insertRow(row)
            self.table_params.setItem(row, 0, QTableWidgetItem(param.name))
            self.table_params.setItem(row, 1, QTableWidgetItem(str(model.event_dict[param])))

        # --- Equations ---
        for eq in model.state_eqs + model.algebraic_eqs:
            eq_type = "state" if eq in model.state_eqs else "algebraic"
            item = QListWidgetItem(f"{symbolic_to_string(eq)} ({eq_type})")
            self.list_eqns.addItem(item)

        # Recurse into submodels
        for submodel in model.children:
            self.refresh_lists(submodel, clear=False)


# class GenericBlockItem(QGraphicsRectItem):
#     """
#            Class to represent generic block to construct devices in the editor
#            :param name:
#            """
#
#     def __init__(self,
#                  var_factory: VarFactory,
#                  subsys: Block,
#                  api_object,
#                  mode: DynamicSimulationMode,
#                  position_changed_callback=None):
#         """
#
#         :param var_factory:
#         :param subsys:
#         :param api_object:
#         :param position_changed_callback:
#         """
#         super().__init__(0, 0, 100, 60)
#
#         # ------------------------
#         # API
#         # ------------------------
#         self.var_factory = var_factory
#         self.subsys = subsys
#         self.mode = mode
#         self.api_object = api_object
#         self.position_changed_callback = position_changed_callback
#
#         self.resize_handle: ResizeHandle | None = None
#         self.resizing_from_handle = False
#         self._suppress_resize: bool = False
#
#         self.name_item = QGraphicsTextItem(self.subsys.name, self)
#         self.inputs: List[PortItem] = list()
#         self.outputs: List[PortItem] = list()
#         self.input_labels: List[QGraphicsTextItem] = list()
#         self.output_labels: List[QGraphicsTextItem] = list()
#
#         self.editor_window = DynamicBlockEditorGUI(
#             var_factory=self.var_factory,
#             block=self.subsys,
#             api_object=self.api_object,
#             mode=self.mode
#         )
#
#         self.setBrush(QBrush(DEFAULT_BLOCK_FILL))
#         self.setPen(QPen(Qt.GlobalColor.transparent, 0))
#         self.setFlags(
#             QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
#             QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
#             QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
#         )
#         self.setAcceptHoverEvents(True)
#
#         self.name_item.setDefaultTextColor(BLOCK_TITLE)
#         name_font: QtGui.QFont = QtGui.QFont("DejaVu Sans", 9)
#         name_font.setBold(True)
#         self.name_item.setFont(name_font)
#         self.name_item.setPos(6, 4)
#
#         n_inputs = len(self.subsys.in_vars)
#         n_outputs = len(self.subsys.out_vars)
#
#         self.inputs = [PortItem(self, True, i, n_inputs) for i in range(n_inputs)]
#         self.outputs = [PortItem(self, False, i, n_outputs) for i in range(n_outputs)]
#         self.input_labels = [self.create_port_label_item() for _ in range(n_inputs)]
#         self.output_labels = [self.create_port_label_item() for _ in range(n_outputs)]
#
#         self.refresh_port_metadata()
#
#         self.resize_handle = ResizeHandle(self)
#
#         self.resize_to_content()
#
#     def mouseDoubleClickEvent(self, event):
#         """
#         opens the editor
#         Parameters
#         ----------
#         event :
#
#         Returns
#         -------
#
#         """
#         self.editor_window.show()
#
#     def resize_block(self, width, height):
#         # Update geometry safely
#         self.prepareGeometryChange()
#         min_width: float
#         min_height: float
#         min_width, min_height = self.get_minimum_block_size()
#         QGraphicsRectItem.setRect(self, 0, 0, max(width, min_width), max(height, min_height))
#         self.update_ports()
#         self.update_handle_position()
#
#     def update_handle_position(self):
#         rect = self.rect()
#         self.resizing_from_handle = False
#         self.resize_handle.setPos(rect.width(), rect.height())
#         self.resizing_from_handle = True
#
#     def paint(self,
#               painter: QPainter,
#               option: QtWidgets.QStyleOptionGraphicsItem,
#               widget: Optional[QWidget] = None) -> None:
#         """
#         Paint the generic block with a rounded card style and a subtle shadow.
#
#         :param painter:
#         :param option:
#         :param widget:
#         :return:
#         """
#         rect: QtCore.QRectF = self.rect()
#         outer_rect: QtCore.QRectF = rect.adjusted(2, 2, -2, -2)
#         shadow_rect: QtCore.QRectF = outer_rect.translated(2.5, 3.0)
#         body_rect: QtCore.QRectF = outer_rect
#         border_color: QColor = BLOCK_BORDER_SELECTED if self.isSelected() else BLOCK_BORDER
#         fill_color: QColor = self.brush().color()
#         body_path: QPainterPath = QPainterPath()
#         shadow_path: QPainterPath = QPainterPath()
#
#         painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
#
#         shadow_path.addRoundedRect(shadow_rect, 12.0, 12.0)
#         painter.setPen(Qt.PenStyle.NoPen)
#         painter.setBrush(QBrush(BLOCK_SHADOW))
#         painter.drawPath(shadow_path)
#
#         body_path.addRoundedRect(body_rect, 12.0, 12.0)
#         painter.setBrush(QBrush(fill_color))
#         painter.drawPath(body_path)
#
#         painter.setPen(QPen(border_color, 1.6))
#         painter.setBrush(Qt.BrushStyle.NoBrush)
#         painter.drawRoundedRect(body_rect, 12.0, 12.0)
#
#     def _set_rect_internal(self, w, h):
#         QGraphicsRectItem.setRect(self, 0, 0, w, h)
#         self.update_ports()
#         self.update_handle_position()
#
#     def set_rectangle(self, x, y, w, h):
#         if not self._suppress_resize:
#             self._set_rect_internal(w, h)
#
#     def get_minimum_block_size(self) -> tuple[float, float]:
#         """
#         Compute the minimum generic block size required by its ports and name.
#
#         :return:
#         """
#         port_rows: int = max(len(self.inputs), len(self.outputs), 1)
#         min_height: float = 50 + port_rows * 18
#
#         name_width = len(self.subsys.name) * 7
#         max_label_length = 0
#         for var in self.subsys.in_vars:
#             max_label_length = max(max_label_length, len(var.name))
#         for var in self.subsys.out_vars:
#             max_label_length = max(max_label_length, len(var.name))
#
#         port_width = max_label_length * 7
#         min_width = max(100, name_width + 14, port_width + 30)
#
#         return min_width, min_height
#
#     def resize_to_content(self) -> None:
#         """
#         Resize the block to the minimum size required by its ports.
#
#         :return:
#         """
#         self.prepareGeometryChange()
#         min_width: float
#         min_height: float
#         min_width, min_height = self.get_minimum_block_size()
#         QGraphicsRectItem.setRect(self, 0, 0, min_width, min_height)
#         self.update_ports()
#         self.update_handle_position()
#
#     def create_port_label_item(self) -> QGraphicsTextItem:
#         """
#         Create a compact label item used beside a port.
#
#         :return:
#         """
#         label_item: QGraphicsTextItem = QGraphicsTextItem("", self)
#         label_font: QtGui.QFont = QtGui.QFont("DejaVu Sans", 9)
#         label_item.setFont(label_font)
#         label_item.setDefaultTextColor(PORT_LABEL_COLOR)
#         label_item.setZValue(4)
#         return label_item
#
#     def refresh_port_metadata(self) -> None:
#         """
#         Refresh tooltips and visible labels for all ports.
#
#         :return:
#         """
#         i: int
#         port: PortItem
#         label_item: QGraphicsTextItem
#         variable_name: str
#
#         if self.subsys is not None:
#             for i, port in enumerate(self.inputs):
#                 if port.base_var is None:
#                     port.base_var = self.subsys.in_vars[i]
#                 else:
#                     pass
#
#                 variable_name = self.subsys.in_vars[i].name
#                 port.setToolTip(f"Input {i}: {variable_name}")
#                 label_item = self.input_labels[i]
#                 label_item.setPlainText(truncate_port_label(variable_name))
#
#             for i, port in enumerate(self.outputs):
#                 if port.base_var is None:
#                     port.base_var = self.subsys.out_vars[i]
#                 else:
#                     pass
#
#                 variable_name = self.subsys.out_vars[i].name
#                 port.setToolTip(f"Output {i}: {variable_name}")
#                 label_item = self.output_labels[i]
#                 label_item.setPlainText(truncate_port_label(variable_name))
#         else:
#             pass
#
#     def update_ports(self):
#         for i, port in enumerate(self.inputs):
#             spacing = self.rect().height() / (len(self.inputs) + 1)
#             port.setPos(0, spacing * (i + 1))
#         for i, port in enumerate(self.outputs):
#             spacing = self.rect().height() / (len(self.outputs) + 1)
#             port.setPos(self.rect().width(), spacing * (i + 1))
#
#         for i, label_item in enumerate(self.input_labels):
#             port = self.inputs[i]
#             label_item.setPos(14.0, port.pos().y() - 8.0)
#
#         for i, label_item in enumerate(self.output_labels):
#             port = self.outputs[i]
#             label_width: float = label_item.boundingRect().width()
#             label_item.setPos(self.rect().width() - label_width - 14.0, port.pos().y() - 8.0)
#
#         self.update_handle_position()
#         # Also update connections
#         for port in self.inputs + self.outputs:
#             if port.connections:
#                 for conn in port.connections:
#                     conn.update_path()
#
#     def hoverEnterEvent(self, event):
#         QApplication.setOverrideCursor(Qt.CursorShape.OpenHandCursor)
#
#     def hoverLeaveEvent(self, event):
#         QApplication.restoreOverrideCursor()
#
#     def itemChange(self, change, value):
#         if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
#             for port in self.inputs + self.outputs:
#                 if port.connections:
#                     for conn in port.connections:
#                         conn.update_path()
#             if self.position_changed_callback is not None:
#                 self.position_changed_callback(value.x(), value.y())
#         return super().itemChange(change, value)

class GenericBlockItem(QGraphicsRectItem):
    """
           Class to represent a block in the scene
           :param name:
           """

    def __init__(self,
                 var_factory: VarFactory,
                 subsys: Block,
                 api_object,
                 mode: DynamicSimulationMode,
                 name: str,
                 position_changed_callback=None):
        """

        :param var_factory:
        :param subsys:
        :param api_object:
        :param position_changed_callback:
        """
        super().__init__(0, 0, 100, 60)

        self.var_factory = var_factory
        self.subsys = subsys
        self.mode = mode
        self.name: str = name
        self.api_object = api_object
        self.position_changed_callback = position_changed_callback

        self.name_item = QGraphicsTextItem(self.subsys.name, self)
        self.name_item.setDefaultTextColor(BLOCK_TITLE)
        name_font: QtGui.QFont = QtGui.QFont("DejaVu Sans", 9)
        name_font.setBold(True)
        self.name_item.setFont(name_font)
        self.name_item.setPos(6, 4)

        self.inputs: List[PortItem] = list()
        self.outputs: List[PortItem] = list()
        self.input_labels: List[QGraphicsTextItem] = list()
        self.output_labels: List[QGraphicsTextItem] = list()

        self.name_item.setDefaultTextColor(BLOCK_TITLE)

        self.editor_window: DynamicBlockEditorGUI | None = None

        self.resize_handle: ResizeHandle | None = None
        self.resizing_from_handle = False
        self._suppress_resize: bool = False
        self.setBrush(QBrush(DEFAULT_BLOCK_FILL))
        self.setPen(QPen(Qt.GlobalColor.transparent, 0))
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)


        name_font: QtGui.QFont = QtGui.QFont("DejaVu Sans", 9)
        name_font.setBold(True)
        self.name_item.setFont(name_font)
        self.name_item.setPos(6, 4)

        n_inputs = len(self.subsys.in_vars)
        n_outputs = len(self.subsys.out_vars)

        self.inputs = [PortItem(self, True, i, n_inputs) for i in range(n_inputs)]
        self.outputs = [PortItem(self, False, i, n_outputs) for i in range(n_outputs)]
        self.input_labels = [self.create_port_label_item() for _ in range(n_inputs)]
        self.output_labels = [self.create_port_label_item() for _ in range(n_outputs)]

        self.refresh_port_metadata()

        self.resize_handle = ResizeHandle(self)

        self.resize_to_content()

    def mouseDoubleClickEvent(self, event):
        """
        opens the editor
        Parameters
        ----------
        event :

        Returns
        -------


        """

        if self.editor_window is None and self.subsys.children:
            self.editor_window = DynamicBlockEditorGUI(
                var_factory=self.var_factory,
                block=self.subsys,
                api_object=self.api_object,
                mode=self.mode,
            )


        elif self.editor_window is None and self.subsys.is_eq_decomposable():
            self.editor_window = DynamicBlockEditorGUI(
                var_factory=self.var_factory,
                block=self.subsys,
                api_object=self.api_object,
                mode=self.mode,
            )
            self.editor_window.decompose_block_in_place(self.subsys)
            self.editor_window.diagram = self.subsys.diagram
            self.editor_window.main_block = self.subsys
            self.editor_window.rebuild_scene_from_diagram()
        self.editor_window.show()

    def set_subsystem(self, block: Block) -> None:
        """
        Attach the symbolic block to the graphics item.

        :param block:
        :return:
        """
        self.subsys = block

    def build_item(self) -> None:
        """
        Build the label, ports, and resize handle from the symbolic block.

        :return:
        """
        if self.subsys is not None:
            self.name_item = QGraphicsTextItem(self.name, self)
            self.name_item.setDefaultTextColor(BLOCK_TITLE)
            name_font: QtGui.QFont = QtGui.QFont("DejaVu Sans", 9)
            name_font.setBold(True)
            self.name_item.setFont(name_font)
            self.name_item.setPos(6, 4)

            n_inputs: int = len(self.subsys.in_vars)
            n_outputs: int = len(self.subsys.out_vars)

            self.inputs = [PortItem(self, True, i, n_inputs) for i in range(n_inputs)]
            self.outputs = [PortItem(self, False, i, n_outputs) for i in range(n_outputs)]
            self.input_labels = [self.create_port_label_item() for _ in range(n_inputs)]
            self.output_labels = [self.create_port_label_item() for _ in range(n_outputs)]
            self.refresh_port_metadata()

            self.resize_handle = ResizeHandle(self)
            self.resize_to_content()
        else:
            pass

    def resize_block(self, width, height):
        # Update geometry safely
        self.prepareGeometryChange()
        min_width: float
        min_height: float
        min_width, min_height = self.get_minimum_block_size()
        QGraphicsRectItem.setRect(self, 0, 0, max(width, min_width), max(height, min_height))
        self.update_ports()
        self.update_handle_position()

    def update_handle_position(self):
        rect = self.rect()
        self.resizing_from_handle = False
        self.resize_handle.setPos(rect.width(), rect.height())
        self.resizing_from_handle = True

    def paint(self,
              painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:
        """
        Paint the block with a rounded card style and a subtle shadow.

        :param painter:
        :param option:
        :param widget:
        :return:
        """
        rect: QtCore.QRectF = self.rect()
        outer_rect: QtCore.QRectF = rect.adjusted(2, 2, -2, -2)
        shadow_rect: QtCore.QRectF = outer_rect.translated(2.5, 3.0)
        body_rect: QtCore.QRectF = outer_rect
        border_color: QColor = BLOCK_BORDER_SELECTED if self.isSelected() else BLOCK_BORDER
        fill_color: QColor = self.brush().color()
        body_path: QPainterPath = QPainterPath()
        shadow_path: QPainterPath = QPainterPath()

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        shadow_path.addRoundedRect(shadow_rect, 12.0, 12.0)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(BLOCK_SHADOW))
        painter.drawPath(shadow_path)

        body_path.addRoundedRect(body_rect, 12.0, 12.0)
        painter.setBrush(QBrush(fill_color))
        painter.drawPath(body_path)

        painter.setPen(QPen(border_color, 1.6))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(body_rect, 12.0, 12.0)

    def _set_rect_internal(self, w, h):
        QGraphicsRectItem.setRect(self, 0, 0, w, h)
        self.update_ports()
        self.update_handle_position()

    def set_rectangle(self, x, y, w, h):
        if not self._suppress_resize:
            self._set_rect_internal(w, h)

    def get_minimum_block_size(self) -> tuple[float, float]:
        """
        Compute the minimum block size required by the port count.

        :return:
        """
        port_rows: int = max(len(self.inputs), len(self.outputs), 1)
        min_height: float = max(
            BLOCK_MIN_HEIGHT,
            BLOCK_HEADER_HEIGHT + BLOCK_PORT_SECTION_PADDING + port_rows * BLOCK_PORT_ROW_HEIGHT
        )

        name_width = len(self.subsys.name) * 7
        max_label_length = 0
        if self.subsys:
            for var in self.subsys.in_vars:
                max_label_length = max(max_label_length, len(var.name))
            for var in self.subsys.out_vars:
                max_label_length = max(max_label_length, len(var.name))

        port_width = max_label_length * 7
        min_width = max(BLOCK_MIN_WIDTH, name_width + 14, port_width + 28)

        return min_width, min_height

    def resize_to_content(self) -> None:
        """
        Resize the block to the minimum size required by its ports.

        :return:
        """
        self.prepareGeometryChange()
        min_width: float
        min_height: float
        min_width, min_height = self.get_minimum_block_size()
        QGraphicsRectItem.setRect(self, 0, 0, min_width, min_height)
        self.update_ports()
        self.update_handle_position()

    def create_port_label_item(self) -> QGraphicsTextItem:
        """
        Create a compact label item used beside a port.

        :return:
        """
        label_item: QGraphicsTextItem = QGraphicsTextItem("", self)
        label_font: QtGui.QFont = QtGui.QFont("DejaVu Sans", 9)
        label_item.setFont(label_font)
        label_item.setDefaultTextColor(PORT_LABEL_COLOR)
        label_item.setZValue(4)
        return label_item

    def refresh_port_metadata(self) -> None:
        """
        Refresh tooltips and visible labels for all ports.

        :return:
        """
        i: int
        port: PortItem
        label_item: QGraphicsTextItem
        variable_name: str

        if self.subsys is not None:
            for i, port in enumerate(self.inputs):
                if port.base_var is None:
                    port.base_var = self.subsys.in_vars[i]
                else:
                    pass

                variable_name = self.subsys.in_vars[i].name
                port.setToolTip(f"Input {i}: {variable_name}")
                label_item = self.input_labels[i]
                label_item.setPlainText(truncate_port_label(variable_name))

            for i, port in enumerate(self.outputs):
                if port.base_var is None:
                    port.base_var = self.subsys.out_vars[i]
                else:
                    pass

                variable_name = self.subsys.out_vars[i].name
                port.setToolTip(f"Output {i}: {variable_name}")
                label_item = self.output_labels[i]
                label_item.setPlainText(truncate_port_label(variable_name))
        else:
            pass

    def update_ports(self):
        for i, port in enumerate(self.inputs):
            spacing = self.rect().height() / (len(self.inputs) + 1)
            port.setPos(0, spacing * (i + 1))
        for i, port in enumerate(self.outputs):
            spacing = self.rect().height() / (len(self.outputs) + 1)
            port.setPos(self.rect().width(), spacing * (i + 1))

        for i, label_item in enumerate(self.input_labels):
            port = self.inputs[i]
            label_item.setPos(14.0, port.pos().y() - 8.0)

        for i, label_item in enumerate(self.output_labels):
            port = self.outputs[i]
            label_width: float = label_item.boundingRect().width()
            label_item.setPos(self.rect().width() - label_width - 14.0, port.pos().y() - 8.0)

        self.update_handle_position()
        # Also update connections
        for port in self.inputs + self.outputs:
            if port.connections:
                for conn in port.connections:
                    conn.update_path()

    def hoverEnterEvent(self, event):
        QApplication.setOverrideCursor(Qt.CursorShape.OpenHandCursor)

    def hoverLeaveEvent(self, event):
        QApplication.restoreOverrideCursor()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self.position_changed_callback is not None:
                self.position_changed_callback(value.x(), value.y())
            for port in self.inputs + self.outputs:
                if port.connections:
                    for conn in port.connections:
                        conn.update_path()
        return super().itemChange(change, value)


class PairedItem(QGraphicsPolygonItem):
    """
    A block item that is paired with another PairedItem.
    Rendered as an isosceles triangle: signal_in points right, signal_out points left.
    """

    _TRI_W: float = 70.0
    _TRI_H: float = 44.0

    def __init__(self,
                 var_factory: VarFactory,
                 subsys: Block,
                 api_object,
                 mode: DynamicSimulationMode,
                 name: str,
                 paired_item: PairedItem | None = None,
                 position_changed_callback=None):
        super().__init__()

        self._paired_item: PairedItem | None = paired_item
        self.var_factory = var_factory
        self.subsys = subsys
        self.mode = mode
        self.name: str = name
        self.api_object = api_object
        self.position_changed_callback = position_changed_callback

        self._is_signal_in: bool = bool(self.subsys.in_vars) and not bool(self.subsys.out_vars)

        self.name_item = QGraphicsTextItem(self.subsys.name, self)
        self.name_item.setDefaultTextColor(BLOCK_TITLE)
        name_font: QtGui.QFont = QtGui.QFont("DejaVu Sans", 7)
        name_font.setBold(True)
        self.name_item.setFont(name_font)

        self.inputs: List[PortItem] = list()
        self.outputs: List[PortItem] = list()

        self.setBrush(QBrush(PAIRED_ITEM_FILL))
        self.setPen(QPen(Qt.GlobalColor.transparent, 0))
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)

        n_inputs = len(self.subsys.in_vars)
        n_outputs = len(self.subsys.out_vars)

        self.inputs = [PortItem(self, True, i, n_inputs) for i in range(n_inputs)]
        self.outputs = [PortItem(self, False, i, n_outputs) for i in range(n_outputs)]

        self.refresh_port_metadata()
        self._build_polygon()

    def rect(self) -> QtCore.QRectF:
        return self.polygon().boundingRect()

    def _build_polygon(self) -> None:
        W = self._TRI_W
        H = self._TRI_H
        if self._is_signal_in:
            poly = QtGui.QPolygonF([
                QtCore.QPointF(0.0, 0.0),
                QtCore.QPointF(0.0, H),
                QtCore.QPointF(W, H / 2.0),
            ])
        else:
            poly = QtGui.QPolygonF([
                QtCore.QPointF(0.0, H / 2.0),
                QtCore.QPointF(W, 0.0),
                QtCore.QPointF(W, H),
            ])
        self.setPolygon(poly)
        self._position_name_and_ports()

    def _position_name_and_ports(self) -> None:
        W = self._TRI_W
        H = self._TRI_H
        half = H / 2.0
        gap: float = 4.0
        port_radius: float = 6.0

        if self._is_signal_in:
            if self.inputs:
                port = self.inputs[0]
                port.setPos(0.0, half)
            name_x = port_radius + gap
        else:
            if self.outputs:
                port = self.outputs[0]
                port.setPos(W, half)
            name_width = self.name_item.boundingRect().width()
            name_x = W - port_radius - gap - name_width

        name_height = self.name_item.boundingRect().height()
        self.name_item.setPos(name_x, half - name_height / 2.0)

        for port in self.inputs + self.outputs:
            if port.connections:
                for conn in port.connections:
                    conn.update_path()

    def set_paired_item(self, paired_item: PairedItem) -> None:
        self._paired_item = paired_item

    def set_subsystem(self, block: Block) -> None:
        self.subsys = block

    def build_item(self) -> None:
        if self.subsys is not None:
            self._is_signal_in = bool(self.subsys.in_vars) and not bool(self.subsys.out_vars)

            self.name_item = QGraphicsTextItem(self.name, self)
            self.name_item.setDefaultTextColor(BLOCK_TITLE)
            name_font: QtGui.QFont = QtGui.QFont("DejaVu Sans", 7)
            name_font.setBold(True)
            self.name_item.setFont(name_font)

            self.setBrush(QBrush(PAIRED_ITEM_FILL))

            n_inputs: int = len(self.subsys.in_vars)
            n_outputs: int = len(self.subsys.out_vars)

            self.inputs = [PortItem(self, True, i, n_inputs) for i in range(n_inputs)]
            self.outputs = [PortItem(self, False, i, n_outputs) for i in range(n_outputs)]
            self.refresh_port_metadata()
            self._build_polygon()
        else:
            pass

    def resize_block(self, width, height):
        pass

    def update_handle_position(self):
        pass

    def paint(self,
              painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:
        polygon: QtGui.QPolygonF = self.polygon()
        bounds: QtCore.QRectF = polygon.boundingRect()
        border_color: QColor = BLOCK_BORDER_SELECTED if self.isSelected() else BLOCK_BORDER
        fill_color: QColor = self.brush().color()

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        shadow_poly = polygon.translated(2.5, 3.0)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(BLOCK_SHADOW))
        painter.drawPolygon(shadow_poly)

        painter.setBrush(QBrush(fill_color))
        painter.drawPolygon(polygon)

        painter.setPen(QPen(border_color, 1.6))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPolygon(polygon)

    def _set_rect_internal(self, w, h):
        pass

    def set_rectangle(self, x, y, w, h):
        pass

    def get_minimum_block_size(self) -> tuple[float, float]:
        return self._TRI_W, self._TRI_H

    def resize_to_content(self) -> None:
        self._build_polygon()

    def refresh_port_metadata(self) -> None:
        """
        Refresh tooltips and visible labels for all ports.
        Also refreshes the paired item's ports if one is set.
        """
        i: int
        port: PortItem
        variable_name: str

        if self.subsys is not None:
            for i, port in enumerate(self.inputs):
                if port.base_var is None:
                    port.base_var = self.subsys.in_vars[i]
                else:
                    pass

                variable_name = self.subsys.in_vars[i].name
                port.setToolTip(f"Input {i}: {variable_name}")

            for i, port in enumerate(self.outputs):
                if port.base_var is None:
                    port.base_var = self.subsys.out_vars[i]
                else:
                    pass

                variable_name = self.subsys.out_vars[i].name
                port.setToolTip(f"Output {i}: {variable_name}")
        else:
            pass

        if self._paired_item is not None:
            other = self._paired_item
            other._paired_item = None
            other.refresh_port_metadata()
            other._paired_item = self

    def update_ports(self):
        self._position_name_and_ports()

    def hoverEnterEvent(self, event):
        QApplication.setOverrideCursor(Qt.CursorShape.OpenHandCursor)

    def hoverLeaveEvent(self, event):
        QApplication.restoreOverrideCursor()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self.position_changed_callback is not None:
                self.position_changed_callback(value.x(), value.y())
            for port in self.inputs + self.outputs:
                if port.connections:
                    for conn in port.connections:
                        conn.update_path()
        return super().itemChange(change, value)


class BlockItem(QGraphicsRectItem):
    """
    Graphics item representing a symbolic block.
    """

    def __init__(self, var_factory: VarFactory, name: str, api_object: ALL_DEV_TYPES | None = None, mode: DynamicSimulationMode = None, position_changed_callback=None):
        """
        Build the graphical block item.

        :param var_factory:
        :param name:
        :param position_changed_callback:
        """
        super().__init__(0, 0, 80, 40)

        self.var_factory: VarFactory = var_factory
        self.api_object = api_object
        self.mode = mode
        self.name: str = name
        self.position_changed_callback = position_changed_callback
        self.resize_handle: ResizeHandle | None = None
        self.resizing_from_handle: bool = False
        self.subsys: Block | None = None
        self.editor_window: DynamicBlockEditorGUI | None = None
        self.name_item: QGraphicsTextItem | None = None
        self.inputs: List[PortItem] = list()
        self.outputs: List[PortItem] = list()
        self.input_labels: List[QGraphicsTextItem] = list()
        self.output_labels: List[QGraphicsTextItem] = list()

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)
        self.setPen(QPen(Qt.GlobalColor.transparent, 0))
        self.setBrush(QBrush(BLOCK_FILL_DISCONNECTED))
        self._refresh_connection_color()


    def set_subsystem(self, block: Block) -> None:
        """
        Attach the symbolic block to the graphics item.

        :param block:
        :return:
        """
        self.subsys = block

    def build_item(self) -> None:
        """
        Build the label, ports, and resize handle from the symbolic block.

        :return:
        """
        if self.subsys is not None:
            self.name_item = QGraphicsTextItem(self.name, self)
            self.name_item.setDefaultTextColor(BLOCK_TITLE)
            name_font: QtGui.QFont = QtGui.QFont("DejaVu Sans", 7)
            name_font.setBold(True)
            self.name_item.setFont(name_font)
            self.name_item.setPos(4, 2)

            n_inputs: int = len(self.subsys.in_vars)
            n_outputs: int = len(self.subsys.out_vars)

            self.inputs = [PortItem(self, True, i, n_inputs) for i in range(n_inputs)]
            self.outputs = [PortItem(self, False, i, n_outputs) for i in range(n_outputs)]
            self.input_labels = [self.create_port_label_item() for _ in range(n_inputs)]
            self.output_labels = [self.create_port_label_item() for _ in range(n_outputs)]
            self.refresh_port_metadata()

            self.resize_to_content()
            self._refresh_connection_color()
        else:
            pass

    def create_port_label_item(self) -> QGraphicsTextItem:
        """
        Create a compact label item used beside a port.

        :return:
        """
        label_item: QGraphicsTextItem = QGraphicsTextItem("", self)
        label_font: QtGui.QFont = QtGui.QFont("DejaVu Sans", 7)
        label_item.setFont(label_font)
        label_item.setDefaultTextColor(PORT_LABEL_COLOR)
        label_item.setZValue(4)
        return label_item

    def get_minimum_block_size(self) -> tuple[float, float]:
        """
        Compute the minimum block size required by the port count.

        :return:
        """
        port_rows: int = max(len(self.inputs), len(self.outputs), 1)
        min_height: float = max(
            BLOCK_COMPACT_MIN_HEIGHT,
            BLOCK_COMPACT_HEADER_HEIGHT + BLOCK_COMPACT_PORT_SECTION_PADDING + port_rows * BLOCK_COMPACT_PORT_ROW_HEIGHT
        )

        name_width = len(self.name) * 5
        max_label_length = 0
        if self.subsys:
            for var in self.subsys.in_vars:
                max_label_length = max(max_label_length, len(var.name))
            for var in self.subsys.out_vars:
                max_label_length = max(max_label_length, len(var.name))

        port_width = max_label_length * 5
        min_width = max(BLOCK_COMPACT_MIN_WIDTH, name_width + 10, port_width + 20)

        return min_width, min_height

    def resize_to_content(self) -> None:
        """
        Resize the block to the minimum size required by its ports.

        :return:
        """
        self.prepareGeometryChange()
        min_width: float
        min_height: float
        min_width, min_height = self.get_minimum_block_size()
        QGraphicsRectItem.setRect(self, 0, 0, min_width, min_height)
        self.update_ports()
        self.update_handle_position()

    def _refresh_connection_color(self) -> None:
        all_connected: bool = True
        for port in self.inputs + self.outputs:
            if port.connections is None:
                all_connected = False
                break
        if all_connected and (len(self.inputs) + len(self.outputs)) > 0:
            self.setBrush(QBrush(BLOCK_FILL_ALL_CONNECTED))
        else:
            self.setBrush(QBrush(BLOCK_FILL_DISCONNECTED))

    def refresh_port_metadata(self) -> None:
        """
        Refresh tooltips and visible labels for all ports.

        :return:
        """
        i: int
        port: PortItem
        label_item: QGraphicsTextItem
        variable_name: str

        if self.subsys is not None:
            for i, port in enumerate(self.inputs):
                if port.base_var is None:
                    port.base_var = self.subsys.in_vars[i]
                else:
                    pass

                variable_name = self.subsys.in_vars[i].name
                port.setToolTip(f"Input {i}: {variable_name}")
                label_item = self.input_labels[i]
                label_item.setPlainText(truncate_port_label(variable_name))

            for i, port in enumerate(self.outputs):
                if port.base_var is None:
                    port.base_var = self.subsys.out_vars[i]
                else:
                    pass

                variable_name = self.subsys.out_vars[i].name
                port.setToolTip(f"Output {i}: {variable_name}")
                label_item = self.output_labels[i]
                label_item.setPlainText(truncate_port_label(variable_name))
        else:
            pass

    def paint(self,
              painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:
        """
        Paint the block with a rounded card style and a subtle header band.

        :param painter:
        :param option:
        :param widget:
        :return:
        """
        rect: QtCore.QRectF = self.rect()
        outer_rect: QtCore.QRectF = rect.adjusted(2, 2, -2, -2)
        shadow_rect: QtCore.QRectF = outer_rect.translated(2.5, 3.0)
        body_rect: QtCore.QRectF = outer_rect
        border_color: QColor = BLOCK_BORDER_SELECTED if self.isSelected() else BLOCK_BORDER
        fill_color: QColor = self.brush().color()
        body_path: QPainterPath = QPainterPath()
        shadow_path: QPainterPath = QPainterPath()

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        shadow_path.addRoundedRect(shadow_rect, 12.0, 12.0)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(BLOCK_SHADOW))
        painter.drawPath(shadow_path)

        body_path.addRoundedRect(body_rect, 12.0, 12.0)
        painter.setBrush(QBrush(fill_color))
        painter.drawPath(body_path)

        painter.setPen(QPen(border_color, 1.6))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(body_rect, 12.0, 12.0)

    def resize_block(self, width: float, height: float) -> None:
        pass

    def update_handle_position(self) -> None:
        """
        Keep the resize handle attached to the lower-right corner.

        :return:
        """
        rect = self.rect()

        if self.resize_handle is not None:
            self.resizing_from_handle = False
            self.resize_handle.setPos(rect.width(), rect.height())
            self.resizing_from_handle = True
        else:
            pass

    def update_ports(self) -> None:
        """
        Reposition ports after a size or position change.

        :return:
        """
        i: int
        port: PortItem
        input_spacing: float
        output_spacing: float
        port_section_height: float = max(self.rect().height() - BLOCK_COMPACT_HEADER_HEIGHT - 6.0, 1.0)

        for i, port in enumerate(self.inputs):
            input_spacing = port_section_height / (len(self.inputs) + 1)
            port.setPos(0, BLOCK_COMPACT_HEADER_HEIGHT + input_spacing * (i + 1))

        for i, port in enumerate(self.outputs):
            output_spacing = port_section_height / (len(self.outputs) + 1)
            port.setPos(self.rect().width(), BLOCK_COMPACT_HEADER_HEIGHT + output_spacing * (i + 1))

        for i, label_item in enumerate(self.input_labels):
            port = self.inputs[i]
            label_item.setPos(10.0, port.pos().y() - 6.0)

        for i, label_item in enumerate(self.output_labels):
            port = self.outputs[i]
            label_width: float = label_item.boundingRect().width()
            label_item.setPos(self.rect().width() - label_width - 10.0, port.pos().y() - 6.0)

        self.update_handle_position()

        # Existing connections must be recomputed whenever port positions change.
        for port in self.inputs + self.outputs:
            if port.connections is not None:
                conn: ConnectionItem
                for conn in port.connections:
                    conn.update_path()
            else:
                pass

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """
        Show a hand cursor when hovering the block.

        :param event:
        :return:
        """
        QApplication.setOverrideCursor(Qt.CursorShape.OpenHandCursor)
        self.update()

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """
        Restore the cursor when leaving the block.

        :param event:
        :return:
        """
        QApplication.restoreOverrideCursor()
        self.update()

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        """
        Handle position changes.

        :param change:
        :param value:
        :return:
        """
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self.position_changed_callback is not None:
                self.position_changed_callback(value.x(), value.y())
            for port in self.inputs + self.outputs:
                if port.connections:
                    for conn in port.connections:
                        conn.update_path()
            return super().itemChange(change, value)
        else:
            return super().itemChange(change, value)

class ProtectedConnectionBlockItem(BlockItem):
    """
    Graphics item for required editor connection-interface blocks.

    These blocks represent the device/network contract and must stay present in
    the canvas, so the scene should treat them as non-removable even though they
    are still serialized with the standard connection block types.
    """

    pass



class GraphicsView(QGraphicsView):
    """
    Graphics view with zoom and middle-button pan.
    """

    ZOOM_FACTOR: float = 1.15

    def __init__(self, scene: QGraphicsScene):
        """
        Build the graphics view.

        :param scene:
        """
        super().__init__(scene)
        self.setRenderHints(self.renderHints() | QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setRubberBandSelectionMode(Qt.ItemSelectionMode.IntersectsItemShape)
        self._panning: bool = False
        self._pan_start: QPointF = QPointF()

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        """
        Apply wheel zoom around the mouse anchor.

        :param event:
        :return:
        """
        zoom_in: bool = event.angleDelta().y() > 0
        self.apply_zoom(zoom_in)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        Start panning on middle mouse press.

        :param event:
        :return:
        """
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            if event.button() == Qt.MouseButton.LeftButton and bool(
                    event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            else:
                self.setDragMode(QGraphicsView.DragMode.NoDrag)
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        Move the viewport while panning.

        :param event:
        :return:
        """
        if self._panning:
            delta: QPointF = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() - delta.x()))
            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() - delta.y()))
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        Stop panning on middle mouse release.

        :param event:
        :return:
        """
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)
            self.setDragMode(QGraphicsView.DragMode.NoDrag)

    def apply_zoom(self, zoom_in: bool) -> None:
        """
        Apply a zoom step to the view.

        :param zoom_in:
        :return:
        """
        zoom_factor: float

        if zoom_in:
            zoom_factor = self.ZOOM_FACTOR
        else:
            zoom_factor = 1.0 / self.ZOOM_FACTOR

        self.scale(zoom_factor, zoom_factor)

    def zoom_in(self) -> None:
        """
        Zoom into the current view.

        :return:
        """
        self.apply_zoom(True)

    def zoom_out(self) -> None:
        """
        Zoom out from the current view.

        :return:
        """
        self.apply_zoom(False)

    def center_items(self) -> None:
        """
        Fit the view to the selected block items or, if none are selected, to all block items.

        :return:
        """
        target_items: List[QGraphicsItem]
        target_rect: QtCore.QRectF
        item: QGraphicsItem
        block_items: List[QGraphicsItem] = list()
        margin_x: float
        margin_y: float

        target_items = self.scene().selectedItems()

        if len(target_items) == 0:
            for item in self.scene().items():
                if isinstance(item, (BlockItem, GenericBlockItem)):
                    block_items.append(item)
                else:
                    pass

            target_items = block_items
        else:
            target_items = [item for item in target_items if isinstance(item, (BlockItem, GenericBlockItem))]

        if len(target_items) > 0:
            target_rect = QtCore.QRectF()

            for item in target_items:
                if target_rect.isNull():
                    target_rect = item.sceneBoundingRect()
                else:
                    target_rect = target_rect.united(item.sceneBoundingRect())

            margin_x = max(target_rect.width() * 0.08, 30.0)
            margin_y = max(target_rect.height() * 0.08, 30.0)
            target_rect = target_rect.adjusted(-margin_x, -margin_y, margin_x, margin_y)
            self.fitInView(target_rect, Qt.AspectRatioMode.KeepAspectRatio)
        else:
            pass


class DiagramScene(QGraphicsScene):
    """
    Scene that manages interactive block connections.
    """

    def __init__(self, editor: "DynamicBlockEditorGUI"):
        """
        Build the scene wrapper around the editor state.

        :param editor:
        """
        super().__init__()
        self.editor: DynamicBlockEditorGUI = editor
        self.temp_line: QGraphicsPathItem | None = None
        self.source_port: PortItem | BranchingItem | None = None
        self.context_item: BlockItem | ConnectionItem | None = None

    def change_item_fill_color(self, item: BlockItem | GenericBlockItem | ConnectionItem) -> None:
        """
        Change the color of a block or connection and persist it in the diagram.

        :param item:
        :return:
        """
        new_color: QColor = QColorDialog.getColor()

        if new_color.isValid():
            if isinstance(item, GenericBlockItem):
                if item.subsys is not None:
                    brush: QBrush = item.brush()
                    brush.setColor(new_color)
                    item.setBrush(brush)
                    self.update()

                    if item.subsys.uid in self.editor.diagram.node_data:
                        self.editor.diagram.node_data[item.subsys.uid].color = new_color.name()
                    else:
                        pass
                else:
                    pass
            elif isinstance(item, ConnectionItem):
                pen: QPen = item.pen()
                pen.setColor(new_color)
                item.setPen(pen)
                self.update()

                if item.uid in self.editor.diagram.con_data:
                    self.editor.diagram.con_data[item.uid].color = new_color.name()
                else:
                    pass
            else:
                pass
        else:
            pass

    def remove_context_item(self) -> None:
        """
        Remove the item currently selected by the scene context menu.

        :return:
        """
        if self.context_item is not None:
            self.editor.remove_item(self.context_item)
        else:
            pass

    def recolor_context_item(self) -> None:
        """
        Recolor the item currently selected by the scene context menu.

        :return:
        """
        if self.context_item is not None:
            self.change_item_fill_color(self.context_item)
        else:
            pass

    def modify_context_item_template(self) -> None:
        """
        Reopen the modal configuration for the selected block when available.

        :return: None.
        """
        if self.context_item is not None:
            self.editor.modify_scene_item_template(self.context_item)
        else:
            pass

    def contextMenuEvent(self, event: QtWidgets.QGraphicsSceneContextMenuEvent) -> None:
        """
        Show scene actions for blocks and connections.

        :param event:
        :return:
        """
        item: QGraphicsItem

        for item in self.items(event.scenePos()):
            if isinstance(item, (BlockItem, GenericBlockItem, ConnectionItem)):
                menu: QMenu = QMenu()
                self.context_item = item

                if isinstance(item, (BlockItem, GenericBlockItem)):
                    if item.subsys is not None:
                        modal_kind, modal_config = get_modal_template_metadata(item.subsys)
                    else:
                        modal_kind = None
                        modal_config = None

                    if _transformer_modal_config_allows_modify(modal_kind, modal_config):
                        modify_action: QAction = QAction("Modify Template", menu)
                        modify_action.triggered.connect(self.modify_context_item_template)
                        menu.addAction(modify_action)
                    else:
                        pass

                else:
                    pass

                if not isinstance(item, ProtectedConnectionBlockItem):
                    remove_action: QAction = QAction("Remove", menu)
                    remove_action.triggered.connect(self.remove_context_item)
                    menu.addAction(remove_action)
                else:
                    pass

                if not isinstance(item, BlockItem):
                    color_action: QAction = QAction("Change Color", menu)
                    color_action.triggered.connect(self.recolor_context_item)
                    menu.addAction(color_action)

                menu.exec(event.screenPos())
                self.context_item = None
                return
            else:
                pass

        super().contextMenuEvent(event)

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """
        Start a temporary connection when the user presses an output port.

        :param event:
        :return:
        """
        item: QGraphicsItem

        for item in self.items(event.scenePos()):
            if isinstance(item, PortItem):
                if not item.is_input:
                    self.source_port = item
                    path: QPainterPath = QPainterPath(item.scenePos())
                    try:
                        IS_DARK = darkdetect.theme() == "Dark"
                    except ImportError:
                        IS_DARK = False

                    CURRENT_THEME_IS_DARK = IS_DARK
                    pen: QPen = QPen(QColor("white"), 1, Qt.PenStyle.DashLine) if CURRENT_THEME_IS_DARK else QPen(QColor("black"), 1, Qt.PenStyle.DashLine)
                    self.temp_line = self.addPath(path, pen)
                    return
                else:
                    pass

            if isinstance(item, BranchingItem):

                self.source_port = item
                path: QPainterPath = QPainterPath(item.scenePos())

                try:
                    IS_DARK = darkdetect.theme() == "Dark"
                except ImportError:
                    IS_DARK = False

                CURRENT_THEME_IS_DARK = IS_DARK
                pen: QPen = QPen(QColor("white"), 1, Qt.PenStyle.DashLine) if CURRENT_THEME_IS_DARK else QPen(Qt.PenStyle.DashLine)
                self.temp_line = self.addPath(path, pen)
                return

            else:
                pass

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """
        Update the temporary connection while dragging.

        :param event:
        :return:
        """
        if self.temp_line is not None:
            if self.source_port is not None:
                start: QPointF = self.source_port.scenePos()
                end: QPointF = event.scenePos()
                path: QPainterPath = build_orthogonal_connection_path(start, end)
                self.temp_line.setPath(path)
            else:
                pass
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """
        Finalize a connection if the cursor is released over a free input port.

        :param event:
        :return:
        """
        if self.temp_line is not None:
            if self.source_port is not None:
                item: QGraphicsItem

                for item in self.items(event.scenePos()):
                    if isinstance(item, PortItem):
                        if item.is_input and not item.is_connected():
                            self.connect_ports(self.source_port, item)
                            break
                        else:
                            pass
                    else:
                        pass
            else:
                pass

            self.removeItem(self.temp_line)
            self.temp_line = None
            self.source_port = None

            self.editor.mark_unapplied_changes()
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """
        Handle double-click on the scene.
        If the click is on a ConnectionItem, create a BranchingItem and two new connections.

        :param event:
        :return:
        """
        # item: QGraphicsItem

        # scene_position: QtCore.QPointF = self.editor.ui.graphicsView.mapToScene(
        #     int(event.position().x()),
        #     int(event.position().y())
        # )

        # for item in self.items(event.scenePos()):
        #     if isinstance(item, ConnectionItem):
        #         connection: ConnectionItem = item
        #         source_port: PortItem = connection.source_port
        #         target_port: PortItem = connection.target_port
        #
        #         branching_item: BranchingItem = BranchingItem(connection.source_port.subsystem,
        #                                                       connection.source_port.index)
        #         branching_item.setPos(event.scenePos())
        #         self.addItem(branching_item)
        #
        #         conn1: ConnectionItem = ConnectionItem(
        #             source_port, branching_item,
        #             diagram=self.editor.diagram
        #         )
        #         self.addItem(conn1)
        #
        #         conn2: ConnectionItem = ConnectionItem(
        #             branching_item, target_port,
        #             diagram=self.editor.diagram
        #         )
        #         self.addItem(conn2)
        #
        #         self.editor.diagram.add_branch(
        #             connectionitem_uid=conn1.uid,
        #             device_uid_from=source_port.subsystem.subsys.uid,
        #             device_uid_to=branching_item.subsystem.subsys.uid,
        #             port_number_from=source_port.index,
        #             port_number_to=0,
        #             color=conn1.pen().color().name()
        #         )
        #
        #         self.editor.diagram.add_branch(
        #             connectionitem_uid=conn2.uid,
        #             device_uid_from=branching_item.subsystem.subsys.uid,
        #             device_uid_to=target_port.subsystem.subsys.uid,
        #             port_number_from=0,
        #             port_number_to=target_port.index,
        #             color=conn2.pen().color().name()
        #         )
        #
        #         if source_port.connections is not None and connection in source_port.connections:
        #             source_port.connections.remove(connection)
        #
        #         if target_port.connections is not None and connection in target_port.connections:
        #             target_port.connections.remove(connection)
        #
        #         if connection.uid in self.editor.diagram.con_data:
        #             del self.editor.diagram.con_data[connection.uid]
        #
        #         self.removeItem(connection)
        #         return

        super().mouseDoubleClickEvent(event)

    def connect_ports(self, source_port: PortItem | BranchingItem, target_port: PortItem) -> None:
        """
        Connect two ports and update the symbolic model.

        :param source_port:
        :param target_port:
        :return:
        """
        source_block: EditorBlockGraphicsItem = source_port.subsystem
        target_block: EditorBlockGraphicsItem = target_port.subsystem

        if source_block.subsys is not None and target_block.subsys is not None:
            connection: ConnectionItem = ConnectionItem(
                source_port, target_port,
                diagram=self.editor.diagram
            )

            dst_var: Var = source_block.subsys.out_vars[source_port.index]
            target_input_var: Var = target_block.subsys.in_vars[target_port.index]

            if target_input_var.network_conn:
                self.editor.var_factory.add_connection(dst_var, target_input_var)
                source_block.refresh_port_metadata()

            else:
                # The destination model must substitute its local input placeholder with the source variable.
                self.editor.var_factory.add_connection(target_input_var, dst_var)

                target_block.refresh_port_metadata()
            self.addItem(connection)

            self.editor.diagram.add_branch(
                connectionitem_uid=connection.uid,
                device_uid_from=source_block.subsys.uid,
                device_uid_to=target_block.subsys.uid,
                port_number_from=source_port.index,
                port_number_to=target_port.index,
                color=connection.pen().color().name(),
                elbow_points=[]
            )
        else:
            pass


class DynamicsLibraryTreeModel(QtGui.QStandardItemModel):
    __slots__ = ("_block_role", "_mime_type", "_drag_token_role", "_drag_payloads")

    def __init__(self, block_role: int, mime_type: str):
        """
        Build the library tree model

        :param block_role:
        :param mime_type:
        """
        super().__init__()
        self._block_role = block_role
        self._mime_type = mime_type
        self._drag_token_role = block_role + 1
        self._drag_payloads: Dict[str, object] = dict()

        self.setHorizontalHeaderLabels(["Models Library"])

    def register_drag_payload(self, item: QtGui.QStandardItem, payload: object) -> None:
        """
        Register a draggable payload and attach its token to the tree item.

        :param item:
        :param payload:
        :return:
        """
        token: str = str(_new_uid())
        self._drag_payloads[token] = payload
        item.setData(payload, self._block_role)
        item.setData(token, self._drag_token_role)

    def get_drag_payload(self, token: str) -> object | None:
        """
        Resolve a dragged token back into the original payload object.

        :param token:
        :return:
        """
        return self._drag_payloads.get(token, None)

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        """
        Get the Qt flags for an item.

        :param index:
        """

        if index.isValid():

            item: QtGui.QStandardItem | None = self.itemFromIndex(index)
            if item is not None:
                item_data: object = item.data(self._block_role)
                if is_supported_library_payload(item_data):
                    return (QtCore.Qt.ItemFlag.ItemIsEnabled
                            | QtCore.Qt.ItemFlag.ItemIsSelectable
                            | QtCore.Qt.ItemFlag.ItemIsDragEnabled)
                else:
                    return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable
            else:
                return QtCore.Qt.ItemFlag.ItemIsEnabled

        else:
            return QtCore.Qt.ItemFlag.ItemIsEnabled

    def mimeTypes(self) -> List[str]:
        """
        Get the supported mime types.

        :return: Mime types exported by the model.
        """
        return [self._mime_type]

    def supportedDragActions(self) -> QtCore.Qt.DropAction:
        """
        Get the supported drag actions.

        :return: Copy action.
        """
        return QtCore.Qt.DropAction.CopyAction

    def mimeData(self, indexes: List[QtCore.QModelIndex]) -> QtCore.QMimeData:
        """
        Build mime data from the selected variable item.

        :param indexes: Selected indexes.
        :return: Mime payload containing the dragged variable uid.
        """
        mime_data: QtCore.QMimeData = QtCore.QMimeData()

        index: QtCore.QModelIndex
        for index in indexes:
            if index.isValid():
                item: QtGui.QStandardItem | None = self.itemFromIndex(index)
                if item is not None:
                    item_token: object = item.data(self._drag_token_role)
                    item_data: object = item.data(self._block_role)
                    if isinstance(item_token, str) and is_supported_library_payload(item_data):
                        mime_data.setData(self._mime_type, QtCore.QByteArray(item_token.encode("utf-8")))
                        return mime_data
                    else:
                        pass
                else:
                    pass
            else:
                pass

        return mime_data


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
                              dc_voltage_reference: VarPowerFlowReferenceType) -> List[ConnectionVarSpec]:
    """
    Build the RMS voltage-interface specs for one connected bus.

    AC buses expose magnitude and angle because RMS phasor models need both
    quantities. DC buses only expose the DC voltage because no phasor angle
    exists in the DC domain.

    :param bus: Connected bus.
    :param voltage_reference: AC voltage-magnitude reference for this terminal.
    :param angle_reference: AC voltage-angle reference for this terminal.
    :param dc_voltage_reference: DC voltage reference for this terminal.
    :return: RMS input connection specs for the bus domain.
    """
    safe_bus_name: str = re.sub(r"[^0-9A-Za-z_]+", "_", bus.name).strip("_") or "Bus"
    specs: List[ConnectionVarSpec] = list()

    if bus.is_dc:
        # DC terminals only contribute one voltage state to the RMS interface.
        specs.append(ConnectionVarSpec("input", dc_voltage_reference, f"Vdc_{safe_bus_name}"))
    else:
        # AC terminals expose phasor magnitude and angle to the device model.
        specs.append(ConnectionVarSpec("input", voltage_reference, f"Vm_{safe_bus_name}"))
        specs.append(ConnectionVarSpec("input", angle_reference, f"Va_{safe_bus_name}"))

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
        active_name = f"net_conn_P_{safe_bus_name}"
        reactive_name = f"net_conn_Q_{safe_bus_name}"
    else:
        active_name = f"net_conn_P{terminal_label}_{safe_bus_name}"
        reactive_name = f"net_conn_Q{terminal_label}_{safe_bus_name}"

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

    def __init__(self,
                 var_factory: VarFactory,
                 block: Block,
                 api_object: ALL_DEV_TYPES | None = None,
                 mode: DynamicSimulationMode = DynamicSimulationMode.RMS,
                 templates_list: Optional[List[RmsModelTemplate | EmtModelTemplate | FmuTemplate]] = None,
                 circuit: Any | None = None,
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
        :type api_object: ALL_DEV_TYPES | None
        :param mode: Specifies the editor mode, either RMS or EMT.
        :type mode: DynamicSimulationMode
        :param templates_list: Optional block-template catalogue entries exposed to the editor.
        :type templates_list: Optional[List[RmsModelTemplate | EmtModelTemplate | FmuTemplate]]
        :param circuit: Circuit context that owns the edited dynamic device.
        :type circuit: Any | None
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

        # set object label
        self.ui.deviceLabel.setText(api_object.name if api_object is not None else "")

        self.block_role: int = int(QtCore.Qt.ItemDataRole.UserRole) + 300
        self.mime_type: str = "application/x-veragrid-dynamics-block"

        self.setWindowTitle("Dynamic Model Editor")

        self.ui.splitter.setStretchFactor(0, 6)
        self.ui.splitter.setStretchFactor(1, 10)
        self.ui.block_editor_actionCheckModel.triggered.connect(self.open_inspect_dialog)
        self.ui.actionCenter.triggered.connect(self.center_view_on_items)
        self.ui.actionZoom_in.triggered.connect(self.zoom_in_view)
        self.ui.actionZoom_out.triggered.connect(self.zoom_out_view)
        # self.ui.actionSave_block_to_my_catalogue.connect(self.save_block_to_my_catalogue)
        # self.ui.actionExport_block.connect(self.export_block)

        self.var_factory = var_factory
        self.api_object = api_object

        self.circuit = circuit
        self.mode = mode
        self.main_editor = main_editor
        self.workspace_embedded = workspace_embedded
        self._emt_bus_fallback_warning_shown: bool = False
        self._selected_side_block: Block | None = None
        self.setWindowTitle(f"Dynamic Model Editor [{self.mode.name}]")
        self.block_counters: Dict[BlockType, int] = dict()
        self.scene: DiagramScene = DiagramScene(self)
        self.changes_applied: bool = False
        self.has_unapplied_changes: bool = False

        self.original_block: Block = block  # api_object.rms_model

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

        self.templates_list: List[
            RmsModelTemplate | EmtModelTemplate | FmuTemplate] = templates_list if templates_list is not None else list()

        common_emt_device_blocks: List[LibraryLeafSpec] = list([
            LibraryLeafSpec("Generic", BlockType.GENERIC),
            LibraryLeafSpec("Voltage source EMT", BlockType.VOLTAGE_SOURCE_EMT),
            LibraryLeafSpec("Current source EMT", BlockType.CURRENT_SOURCE_EMT),
            LibraryLeafSpec("Controlled voltage source EMT", BlockType.CONTROLLED_VOLTAGE_SOURCE_EMT),
            LibraryLeafSpec("Controlled current source EMT", BlockType.CONTROLLED_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("DC voltage source EMT", BlockType.DC_VOLTAGE_SOURCE_EMT),
            LibraryLeafSpec("DC current source EMT", BlockType.DC_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("Controlled DC voltage source EMT", BlockType.CONTROLLED_DC_VOLTAGE_SOURCE_EMT),
            LibraryLeafSpec("Controlled DC current source EMT", BlockType.CONTROLLED_DC_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("Balanced 3-phase voltage source EMT", BlockType.BALANCED_3PH_VOLTAGE_SOURCE_EMT),
            LibraryLeafSpec("Balanced 3-phase current source EMT", BlockType.BALANCED_3PH_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("Controlled balanced 3-phase voltage source EMT", BlockType.CONTROLLED_BALANCED_3PH_VOLTAGE_SOURCE_EMT),
            LibraryLeafSpec("Controlled balanced 3-phase current source EMT", BlockType.CONTROLLED_BALANCED_3PH_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("Arbitrary waveform voltage source EMT", BlockType.ARBITRARY_WAVEFORM_VOLTAGE_SOURCE_EMT),
            LibraryLeafSpec("Arbitrary waveform current source EMT", BlockType.ARBITRARY_WAVEFORM_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("Step voltage source EMT", BlockType.STEP_VOLTAGE_SOURCE_EMT),
            LibraryLeafSpec("Step current source EMT", BlockType.STEP_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("Ramp voltage source EMT", BlockType.RAMP_VOLTAGE_SOURCE_EMT),
            LibraryLeafSpec("Ramp current source EMT", BlockType.RAMP_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("Double exponential current source EMT", BlockType.DOUBLE_EXPONENTIAL_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("Heidler current source EMT", BlockType.HEIDLER_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("CIGRE surge current source EMT", BlockType.CIGRE_SURGE_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("Switch EMT", BlockType.SWITCH_EMT),
            LibraryLeafSpec("Ground EMT", BlockType.GROUND_EMT),
            LibraryLeafSpec("Grounding Link EMT", BlockType.GROUNDING_LINK_EMT),
            LibraryLeafSpec("Nonlinear Resistor EMT", BlockType.NONLINEAR_RESISTOR_EMT),
            LibraryLeafSpec("RLC Combo", BlockType.RLC_COMBO_EMT),
            LibraryLeafSpec("R load", BlockType.R_LOAD_EMT),
            LibraryLeafSpec("L load", BlockType.L_LOAD_EMT),
            LibraryLeafSpec("C load", BlockType.C_LOAD_EMT),
            LibraryLeafSpec("DC load", BlockType.DC_LOAD_EMT),
        ])
        common_emt_fault_blocks: List[LibraryLeafSpec] = list([
            LibraryLeafSpec("Fault EMT", BlockType.FAULT_EMT),
        ])

        common_rms_device_blocks: List[LibraryLeafSpec] = list([
            LibraryLeafSpec("Pll transformer", BlockType.PLL_TRANSFORM_RMS),
            LibraryLeafSpec("Pi current controller", BlockType.PI_CURRENT_CONTROLLER),
            LibraryLeafSpec("Pi power controller", BlockType.PI_POWER_CONTROLLER)])

        device_rms_related_blocks = {
            DeviceType.GeneratorDevice: [
                LibraryLeafSpec("Generic", BlockType.GENERIC),
                LibraryLeafSpec("Generator basic", BlockType.GENRAW),
                LibraryLeafSpec("Generator QEC", BlockType.GENQEC),
                LibraryLeafSpec("Governor", BlockType.GOV_RMS),
                LibraryLeafSpec("Stabilizer", BlockType.STAB_RMS),
                LibraryLeafSpec("Exciter", BlockType.EXCITER_RMS),

            ],
            DeviceType.VscDevice: [
                LibraryLeafSpec("Gfl converter", BlockType.GFL_CONVERTER_RMS),
            ],
            DeviceType.LineDevice: [
                LibraryLeafSpec("Generic", BlockType.GENERIC),
                LibraryLeafSpec("Line", BlockType.LINE_RMS),
            ],

            DeviceType.LoadDevice: [
                LibraryLeafSpec("Generic", BlockType.GENERIC),
                LibraryLeafSpec("Load", BlockType.LOAD_RMS),
                # LibraryLeafSpec("Load", BlockType.DC_PV_SOURCE_RMS),
            ],
        }

        device_emt_related_blocks = {
            DeviceType.GeneratorDevice: [
                LibraryLeafSpec("Generator", BlockType.EMT_GENERATOR),
                LibraryLeafSpec("Thevenin eq. generator", BlockType.EMT_THEVENIN),
                LibraryLeafSpec("Governor", BlockType.GOV_EMT),
                LibraryLeafSpec("Stabilizer", BlockType.STAB_EMT),
                LibraryLeafSpec("Exciter", BlockType.EXCITER_EMT),
                LibraryLeafSpec("PV power plant", BlockType.PV_POWER_PLANT_EMT),
                LibraryLeafSpec("PV ", BlockType.PV_EMT),
            ],
            DeviceType.BatteryDevice: [
                LibraryLeafSpec("BESS ", BlockType.BESS_EMT),
                LibraryLeafSpec("Battery ", BlockType.BATTERY_EMT),
            ],
            DeviceType.LineDevice: [
                LibraryLeafSpec("Emt pi line", BlockType.EMT_PI_LINE),
                LibraryLeafSpec("Emt Bergeron line", BlockType.EMT_BERGERON_LINE),
                LibraryLeafSpec("Emt JMarti line", BlockType.EMT_JMARTI_LINE),
            ],
            DeviceType.DCLineDevice: [
                LibraryLeafSpec("Emt DC line", BlockType.EMT_DC_LINE),
            ],
            DeviceType.LoadDevice: [ # the other types of loads already appear in common emt device blocks
                LibraryLeafSpec("Exponential load", BlockType.EXP_LOAD_EMT),
                LibraryLeafSpec("ZIP load", BlockType.ZIP_LOAD_EMT),
                LibraryLeafSpec("Induction motor", BlockType.INDUCTION_MOTOR_EMT)
            ],
            DeviceType.Transformer2WDevice: [
                LibraryLeafSpec("Transformer", BlockType.TRAFO_EMT),
                LibraryLeafSpec("XFMR Transformer", BlockType.XFMR_TRANSFORMER),
            ],
            DeviceType.Transformer3WDevice: [
                LibraryLeafSpec("Transformer", BlockType.TRAFO_EMT),
                LibraryLeafSpec("XFMR Transformer", BlockType.XFMR_TRANSFORMER),
            ],
            DeviceType.TransformerTypeDevice: [
                LibraryLeafSpec("Transformer", BlockType.TRAFO_EMT),
                LibraryLeafSpec("XFMR Transformer", BlockType.XFMR_TRANSFORMER),
            ],
            DeviceType.VscDevice: [
            LibraryLeafSpec("Complete pseudo-EMT VSC", BlockType.COMPLETE_PSEUDO_VSC_EMT),
            # LibraryLeafSpec("pseudo-EMT VSC", BlockType.PSEUDO_VSC_EMT),
            # LibraryLeafSpec("PLL VSC", BlockType.PLL_EMT),
            # LibraryLeafSpec("Outer loop VSC", BlockType.OUTER_LOOP_EMT),
            # LibraryLeafSpec("Inner loop VSC", BlockType.INNER_LOOP_EMT),
            # LibraryLeafSpec("Reduced transformer VSC", BlockType.REDUCED_TRANSFORMER_EMT),
            ],
            
        }

        try:
            api_object_device_type = api_object.device_type
        except AttributeError:
            api_object_device_type = DeviceType.NoDevice

        self.tree_structure: Dict[str, Any] = dict()
        if mode == DynamicSimulationMode.RMS:
            self.tree_structure["Basic"] = self.build_basic_library_branch()
            self.tree_structure["Basic_devices"] = list(common_rms_device_blocks)
            self.tree_structure["Devices"] = device_rms_related_blocks.get(api_object_device_type, dict())

        elif mode == DynamicSimulationMode.EMT:
            self.tree_structure["Basic"] = self.build_basic_library_branch()
            specific_emt_blocks: List[LibraryLeafSpec] = list(device_emt_related_blocks.get(api_object_device_type, list()))
            self.tree_structure["Devices"] = list(common_emt_device_blocks + specific_emt_blocks)
            self.tree_structure["Faults"] = list(common_emt_fault_blocks)

        else:
            pass

        self.tree_structure["Tools"] = [
            LibraryLeafSpec("Signal Pair", SignalPairPayload()),
        ]

        if self.templates_list:
            self.tree_structure["Templates"] = {
                "Available": [LibraryLeafSpec(template.name, template, template.name) for template in
                              self.templates_list]
            }
        else:
            pass

        # build and add library model
        self.library_model = self.build_library_tree_model(
            block_role=self.block_role,
            mime_type=self.mime_type
        )

        self.library_proxy_model = LibraryTreeFilterProxyModel(
            search_role=LIBRARY_SEARCH_TEXT_ROLE,
            parent=self.ui.libraryTreeView,
        )
        self.library_proxy_model.setSourceModel(self.library_model)

        self.ui.libraryTreeView.setModel(self.library_proxy_model)
        self.ui.libraryTreeView.setDragEnabled(True)
        self.ui.libraryTreeView.setHeaderHidden(False)
        self.ui.libraryTreeView.setUniformRowHeights(True)

        self.ui.librarySearchButton.setIcon(QtGui.QIcon(":/Icons/icons/magnifying_glass.png"))
        self.ui.librarySearchLineEdit.setVisible(True)
        self.ui.librarySearchLineEdit.setClearButtonEnabled(True)
        self.ui.librarySearchButton.clicked.connect(self.focus_library_search)
        self.ui.librarySearchLineEdit.textChanged.connect(self.on_library_search_text_changed)
        self.library_find_shortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Find, self)
        self.library_find_shortcut.activated.connect(self.focus_library_search)
        self.reset_library_tree_expansion()

        self.variables_model = WrappableBlockTableModel(
            var_factory=self.var_factory,
            parent=self.ui.variablesTableView
        )
        self.variables_model.set_mode(DynamicTableModelMode.VARIABLES)
        self.variables_model.set_delegates()
        self.variables_search = QLineEdit()
        self.variables_search.setPlaceholderText("Search variables...")
        self.variables_search.setClearButtonEnabled(True)
        self.ui.verticalLayout_7.insertWidget(0, self.variables_search)
        self.variables_proxy = BlockTableFilterProxyModel(parent=self.ui.variablesTableView)
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

        self.parameters_model = WrappableBlockTableModel(
            api_object=self.api_object,
            var_factory=self.var_factory,
            parent=self.ui.parametersTableView
        )
        self.parameters_model.set_mode(DynamicTableModelMode.PARAMETERS)
        self.parameters_model.set_delegates()
        self.parameters_search = QLineEdit()
        self.parameters_search.setPlaceholderText("Search parameters...")
        self.parameters_search.setClearButtonEnabled(True)
        self.ui.verticalLayout_8.insertWidget(0, self.parameters_search)
        self.parameters_proxy = BlockTableFilterProxyModel(parent=self.ui.parametersTableView)
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

        self.equations_model = WrappableBlockTableModel(
            var_factory=self.var_factory,
            parent=self.ui.equationsTableView
        )
        self.equations_model.set_mode(DynamicTableModelMode.EQUATIONS)
        self.equations_model.set_delegates()
        self.equations_search = QLineEdit()
        self.equations_search.setPlaceholderText("Search equations...")
        self.equations_search.setClearButtonEnabled(True)
        self.ui.verticalLayout_9.insertWidget(0, self.equations_search)
        self.equations_proxy = BlockTableFilterProxyModel(parent=self.ui.equationsTableView)
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

        self.ui.doItButton.clicked.connect(self.apply_changes)
        self.ui.validateConsistencyButton.clicked.connect(self.show_model_consistency_validation)
        self.ui.toolBox.currentChanged.connect(self.on_side_panel_page_changed)
        self.scene.selectionChanged.connect(self.on_scene_selection_changed)
        if self.mode == DynamicSimulationMode.EMT and self.main_editor:
            self._ensure_full_emt_editor_interface()
        else:
            pass

        _ensure_block_tree_names(self.main_block, prefix="block")

        if not self.main_block.empty() and not self.main_block.diagram.node_data:

            if self.main_block.children:
                blocks_list = list()
                for child in self.main_block.children:
                    item = self.generate_block_item_for_block(child)
                    blocks_list.append(item)
                self.add_connection_items(blocks_list)
                if len(blocks_list) != 0:
                    self.connect_items(blocks_list)

            # if self.main_block.children:
            #
            #     # add input connection blocks
            #     connection_tpe: Dict[int, str] = {}
            #     all_blocks: List[Block] = list()
            #     for in_var in self.main_block.in_vars:
            #         in_blk = Block(
            #             out_vars=[in_var],
            #             name=f"input_{in_var.name}",
            #             is_decomposable=False
            #         )
            #         all_blocks.append(in_blk)
            #         connection_tpe[in_blk.uid] = BlockType.INPUT_CONN.name
            #
            #     # add main block children blocks
            #     for child in self.main_block.children:
            #         all_blocks.append(child)
            #
            #     # add output connection blocks
            #     for out_var in self.main_block.out_vars:
            #         out_blk = Block(
            #             in_vars=[out_var],
            #             name=f"output_{out_var.name}",
            #             is_decomposable=False
            #         )
            #         all_blocks.append(out_blk)
            #         connection_tpe[out_blk.uid] = BlockType.OUTPUT_CONN.name
            #
            #     # --- build diagram ---
            #     diagram, all_children = build_diagram_regular_blocks(all_blocks, connection_tpe)
            #
            #     # update main block and diagram editor
            #     self.main_block.children = all_children
            #     self.main_block.diagram = diagram
            #     self.diagram = diagram



        elif not self.main_block.diagram.node_data:
            # here we add the connection variables to the main block
            if self.main_editor:
                self.add_connection_vars()
                # self.add_api_obj_mapping()
            self.add_connection_items()
        self.rebuild_scene_from_diagram()

        # for every in variable and our variable in the main block of the editor we build a block item to connect these variables

    @staticmethod
    def _insert_library_leaf(branch: Dict[str, Any], category_path: tuple[str, ...], leaf: LibraryLeafSpec) -> None:
        """
        Insert one library leaf into a nested dictionary branch.
        """

        head: str = category_path[0]
        if len(category_path) == 1:
            leaves: Any = branch.setdefault(head, list())
            if isinstance(leaves, list):
                leaves.append(leaf)
            else:
                raise TypeError(f"Category '{head}' is already used as a branch node")
        else:
            child_branch: Any = branch.setdefault(head, dict())
            if isinstance(child_branch, dict):
                DynamicBlockEditorGUI._insert_library_leaf(child_branch, category_path[1:], leaf)
            else:
                raise TypeError(f"Category '{head}' is already used as a leaf collection")

    def build_basic_block_catalog_branch(self) -> Dict[str, Any]:
        """
        Build the nested branch used to expose the imported basic block catalog.
        """

        # The catalog owns the static library skeleton so the GUI does not need to
        # duplicate category dictionaries that can drift during refactors.
        branch: Dict[str, Any] = build_basic_block_catalog_branch_skeleton()

        descriptor: BasicBlockTemplateDescriptor
        for descriptor in get_editor_ready_basic_block_catalog_descriptors():
            category_path: tuple[str, ...] = descriptor.category_path[1:] if descriptor.category_path and \
                                                                             descriptor.category_path[
                                                                                 0] == "Native" else descriptor.category_path
            if len(category_path) == 0:
                category_path = ("Miscellaneous", "Other")
            else:
                pass

            self._insert_library_leaf(
                branch=branch,
                category_path=category_path,
                leaf=LibraryLeafSpec(
                    label=descriptor.display_label,
                    payload=descriptor,
                    search_text=descriptor.search_text,
                ),
            )

        if len(branch["Miscellaneous"]["Other"]) == 0:
            del branch["Miscellaneous"]
        else:
            pass

        return branch

    def build_basic_library_branch(self) -> Dict[str, Any]:
        """
        Build the nested Basic branch used by both RMS and EMT editors.
        """

        native_branch: Dict[str, Any] = {
            "Arithmetic": [
                LibraryLeafSpec("Const", BlockType.CONST),
                LibraryLeafSpec("Gain", BlockType.GAIN),
                LibraryLeafSpec("Sum", BlockType.SUM),
                LibraryLeafSpec("Substr", BlockType.SUBSTR),
                LibraryLeafSpec("Product", BlockType.PRODUCT),
                LibraryLeafSpec("Divide", BlockType.DIVIDE),
                LibraryLeafSpec("Abs", BlockType.ABS),
            ],
        }
        native_branch.update(self.build_basic_block_catalog_branch())

        return {
            "Native": native_branch,
        }

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

    @staticmethod
    def _set_library_item_icon(item: QtGui.QStandardItem, payload: object) -> None:
        """
        Apply the best matching icon for one draggable library leaf.
        """

        if isinstance(payload, FmuTemplate):
            item.setIcon(QtGui.QIcon(device_type_icons[DeviceType.FmuTemplateDevice.value]))
        elif isinstance(payload, RmsModelTemplate):
            item.setIcon(QtGui.QIcon(device_type_icons[DeviceType.RmsModelTemplateDevice.value]))
        elif isinstance(payload, (EmtModelTemplate, BasicBlockTemplateDescriptor)):
            item.setIcon(QtGui.QIcon(device_type_icons[DeviceType.EmtModelTemplateDevice.value]))
        else:
            pass

    def _append_library_branch(self,
                               model: DynamicsLibraryTreeModel,
                               parent_item: QtGui.QStandardItem,
                               branch_label: str,
                               branch_data: Any,
                               path_tokens: tuple[str, ...] = tuple()) -> None:
        """
        Append one recursive library branch into the tree model.
        """

        branch_item: QtGui.QStandardItem = QtGui.QStandardItem(branch_label)
        branch_item.setEditable(False)
        branch_item.setData(" ".join((*path_tokens, branch_label)).strip(), LIBRARY_SEARCH_TEXT_ROLE)
        parent_item.appendRow(branch_item)

        if len(path_tokens) == 0:
            category_icon_path: str | None = device_type_icons.get(branch_label, None)
            if category_icon_path is not None:
                branch_item.setIcon(QtGui.QIcon(category_icon_path))
            else:
                pass
        else:
            pass

        if isinstance(branch_data, dict):
            child_label: str
            child_data: Any
            for child_label, child_data in branch_data.items():
                self._append_library_branch(model, branch_item, child_label, child_data, (*path_tokens, branch_label))
        else:
            if isinstance(branch_data, list):
                leaf: LibraryLeafSpec
                for leaf in sorted(branch_data, key=_library_leaf_label_sort_key):
                    item: QtGui.QStandardItem = QtGui.QStandardItem(leaf.label)
                    item.setEditable(False)
                    item.setData(leaf.search_text if leaf.search_text else leaf.label, LIBRARY_SEARCH_TEXT_ROLE)
                    self._set_library_item_icon(item, leaf.payload)
                    model.register_drag_payload(item, leaf.payload)
                    branch_item.appendRow(item)
            else:
                raise TypeError(f"Unsupported library branch data type {type(branch_data)!r}")

    def build_library_tree_model(self,
                                 block_role: int,
                                 mime_type: str) -> DynamicsLibraryTreeModel:
        """
        Build the source tree-view model for dynamic library.

        :param block_role:
        :type block_role:
        :param mime_type:
        :type mime_type:
        :return:
        :rtype:
        """

        model: DynamicsLibraryTreeModel = DynamicsLibraryTreeModel(block_role, mime_type)
        model.setHorizontalHeaderLabels(["Dynamic library"])
        root_item: QtGui.QStandardItem = model.invisibleRootItem()

        category: str
        branch_data: Any
        for category, branch_data in self.tree_structure.items():
            self._append_library_branch(model, root_item, category, branch_data)

        return model

    def get_library_payload_from_mime_data(self,
                                           mime_data: QtCore.QMimeData) -> BlockType | BasicBlockTemplateDescriptor | RmsModelTemplate | EmtModelTemplate | FmuTemplate | SignalPairPayload | None:
        """
        Decode the dragged library payload from the tree-view mime payload.

        :param mime_data:
        :return:
        """
        drag_token: str
        payload: object | None

        if mime_data.hasFormat(self.mime_type):
            drag_token = bytes(mime_data.data(self.mime_type)).decode("utf-8")
            payload = self.library_model.get_drag_payload(drag_token)

            if isinstance(payload, BlockType):
                return payload
            elif isinstance(payload, BasicBlockTemplateDescriptor):
                return payload
            elif isinstance(payload, (RmsModelTemplate, EmtModelTemplate, FmuTemplate)):
                return payload
            elif isinstance(payload, SignalPairPayload):
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

    def create_emt_wizard_block_item(self, block_type: BlockType, x_pos, y_pos) -> GenericBlockItem | None:
        """
        Create and place a generic block item.

        :param block_type:
        :param x_pos:
        :param y_pos:
        :return:
        """

        dialog = EmtTemplateWizardDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            phase_n, phase_a, phase_b, phase_c = dialog.get_values()
            count: int = self.block_counters.get(block_type, 0) + 1
            item_name: str = f"{block_type.name}_{count}"
            block_model = create_emt_wizard_block(phase_n=phase_n,
                                                  phase_a=phase_a,
                                                  phase_b=phase_b,
                                                  phase_c=phase_c,
                                                  var_factory=self.var_factory,
                                                  block_type=block_type,
                                                  item_name=item_name)
            block_item: GenericBlockItem = GenericBlockItem(var_factory=self.var_factory,
                                                            subsys=block_model,
                                                            api_object=self.api_object,
                                                            mode=self.mode,
                                                            name=item_name,
                                                            position_changed_callback=self._build_position_changed_callback(block_model.uid))

            if block_model is not None:
                set_modal_template_metadata(
                    block_model,
                    kind="emt_phase_wizard",
                    config=dict({
                        "block_type": block_type.name,
                        "phase_n": phase_n,
                        "phase_a": phase_a,
                        "phase_b": phase_b,
                        "phase_c": phase_c,
                    }),
                )

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

                self.mark_unapplied_changes()

                return block_item
            else:
                return None
        else:
            return None

    @staticmethod
    def _build_default_source_emt_modal_config(block_type: BlockType,
                                               phase_n: bool = False,
                                               phase_a: bool = True,
                                               phase_b: bool = True,
                                               phase_c: bool = True) -> Dict[str, Any]:
        """
        Build one default persisted configuration for one EMT source modal.

        :param block_type: Source block type.
        :param phase_n: Whether neutral is active.
        :param phase_a: Whether phase A is active.
        :param phase_b: Whether phase B is active.
        :param phase_c: Whether phase C is active.
        :return: Default source configuration.
        """
        return dict({
            "block_type": block_type.name,
            "phase_n": bool(phase_n),
            "phase_a": bool(phase_a),
            "phase_b": bool(phase_b),
            "phase_c": bool(phase_c),
            "source_frequency_hz": 50.0,
            "source_phase_amplitudes": dict({"N": 0.0, "A": 1.0, "B": 1.0, "C": 1.0}),
            "source_phase_angle_deg": dict({"N": 0.0, "A": 0.0, "B": -120.0, "C": 120.0}),
            "source_phase_offsets": dict({"N": 0.0, "A": 0.0, "B": 0.0, "C": 0.0}),
            "source_conductance_value": 100.0,
        })

    @staticmethod
    def _extract_source_emt_phase_tuple(modal_config: Dict[str, Any]) -> tuple[bool, bool, bool, bool]:
        """
        Return the ordered phase tuple stored in one EMT source modal configuration.

        :param modal_config: Persisted source modal configuration.
        :return: ``(phase_n, phase_a, phase_b, phase_c)``.
        """
        return (
            bool(modal_config.get("phase_n", False)),
            bool(modal_config.get("phase_a", True)),
            bool(modal_config.get("phase_b", True)),
            bool(modal_config.get("phase_c", True)),
        )

    @staticmethod
    def _build_source_emt_modal_tooltip(modal_config: Dict[str, Any]) -> str:
        """
        Build one compact tooltip for one EMT source block.

        :param modal_config: Persisted source modal configuration.
        :return: Tooltip text.
        """
        active_labels: List[str] = list()
        source_phase_amplitudes: Dict[str, Any] = dict(modal_config.get("source_phase_amplitudes", dict()))
        source_phase_angle_deg: Dict[str, Any] = dict(modal_config.get("source_phase_angle_deg", dict()))
        source_phase_offsets: Dict[str, Any] = dict(modal_config.get("source_phase_offsets", dict()))

        if bool(modal_config.get("phase_n", False)):
            active_labels.append("N")
        if bool(modal_config.get("phase_a", False)):
            active_labels.append("A")
        if bool(modal_config.get("phase_b", False)):
            active_labels.append("B")
        if bool(modal_config.get("phase_c", False)):
            active_labels.append("C")

        tooltip_lines: List[str] = [str(modal_config.get("block_type", "EMT source"))]
        tooltip_lines.append(f"Phases: {', '.join(active_labels)}")
        tooltip_lines.append(f"f={float(modal_config.get('source_frequency_hz', 0.0)):.4g} Hz")

        if str(modal_config.get("block_type", "")) in {
            BlockType.VOLTAGE_SOURCE_EMT.name,
            BlockType.CURRENT_SOURCE_EMT.name,
        }:
            tooltip_lines.append(
                "Amplitudes: "
                + ", ".join(
                    f"{phase_label}={float(source_phase_amplitudes.get(phase_label, 0.0)):.4g}"
                    for phase_label in active_labels
                )
            )
        else:
            tooltip_lines.append("Amplitude controlled by command inputs")

        tooltip_lines.append(
            "Phase [deg]: "
            + ", ".join(
                f"{phase_label}={float(source_phase_angle_deg.get(phase_label, 0.0)):.4g}"
                for phase_label in active_labels
            )
        )
        tooltip_lines.append(
            "Offset: "
            + ", ".join(
                f"{phase_label}={float(source_phase_offsets.get(phase_label, 0.0)):.4g}"
                for phase_label in active_labels
            )
        )

        if str(modal_config.get("block_type", "")) in {
            BlockType.VOLTAGE_SOURCE_EMT.name,
            BlockType.CONTROLLED_VOLTAGE_SOURCE_EMT.name,
        }:
            tooltip_lines.append(f"g={float(modal_config.get('source_conductance_value', 0.0)):.4g}")

        return "\n".join(tooltip_lines)

    def _build_source_emt_block_model(self,
                                      block_type: BlockType,
                                      item_name: str,
                                      modal_config: Dict[str, Any]) -> Block | None:
        """
        Build one EMT source block model from one modal configuration.

        :param block_type: Source block type.
        :param item_name: Symbolic block name.
        :param modal_config: Source modal configuration.
        :return: Built symbolic block or ``None``.
        """
        phase_n, phase_a, phase_b, phase_c = self._extract_source_emt_phase_tuple(modal_config)
        source_phase_amplitudes: Dict[str, float] = dict(modal_config.get("source_phase_amplitudes", dict()))
        source_phase_angle_deg: Dict[str, float] = dict(modal_config.get("source_phase_angle_deg", dict()))
        source_phase_offsets: Dict[str, float] = dict(modal_config.get("source_phase_offsets", dict()))
        source_frequency_hz: float = float(modal_config.get("source_frequency_hz", 50.0))
        source_conductance_value: float = float(modal_config.get("source_conductance_value", 100.0))

        if block_type == BlockType.VOLTAGE_SOURCE_EMT:
            return get_voltage_source_emt_template(
                vf=self.var_factory,
                phN=phase_n,
                phA=phase_a,
                phB=phase_b,
                phC=phase_c,
                amplitude_values=source_phase_amplitudes,
                frequency_hz=source_frequency_hz,
                phase_angle_deg=source_phase_angle_deg,
                offset_values=source_phase_offsets,
                source_conductance_value=source_conductance_value,
                name=item_name,
            ).block
        elif block_type == BlockType.CURRENT_SOURCE_EMT:
            return get_current_source_emt_template(
                vf=self.var_factory,
                phN=phase_n,
                phA=phase_a,
                phB=phase_b,
                phC=phase_c,
                amplitude_values=source_phase_amplitudes,
                frequency_hz=source_frequency_hz,
                phase_angle_deg=source_phase_angle_deg,
                offset_values=source_phase_offsets,
                name=item_name,
            ).block
        elif block_type == BlockType.CONTROLLED_VOLTAGE_SOURCE_EMT:
            return get_controlled_voltage_source_emt_template(
                vf=self.var_factory,
                phN=phase_n,
                phA=phase_a,
                phB=phase_b,
                phC=phase_c,
                frequency_hz=source_frequency_hz,
                phase_angle_deg=source_phase_angle_deg,
                offset_values=source_phase_offsets,
                source_conductance_value=source_conductance_value,
                name=item_name,
            ).block
        elif block_type == BlockType.CONTROLLED_CURRENT_SOURCE_EMT:
            return get_controlled_current_source_emt_template(
                vf=self.var_factory,
                phN=phase_n,
                phA=phase_a,
                phB=phase_b,
                phC=phase_c,
                frequency_hz=source_frequency_hz,
                phase_angle_deg=source_phase_angle_deg,
                offset_values=source_phase_offsets,
                name=item_name,
            ).block
        else:
            return None

    def create_source_emt_block_item(self, block_type: BlockType, x_pos: float, y_pos: float) -> GenericBlockItem | None:
        """
        Create one EMT source block configured through the source modal.

        :param block_type: Source block type.
        :param x_pos: Drop x position.
        :param y_pos: Drop y position.
        :return: Created block item or ``None`` when the dialog is cancelled.
        """
        dialog = SourceEmtDialog(block_type=block_type, parent=self, initial_config=self._build_default_source_emt_modal_config(block_type))

        if dialog.exec() == QDialog.DialogCode.Accepted:
            source_config: Dict[str, Any] = dict(self._build_default_source_emt_modal_config(block_type), **dialog.get_configuration())
        else:
            return None

        count: int = self.block_counters.get(block_type, 0) + 1
        item_name: str = f"{block_type.name}_{count}"
        block_model: Block | None = self._build_source_emt_block_model(block_type=block_type,
                                                                       item_name=item_name,
                                                                       modal_config=source_config)
        block_item: GenericBlockItem = GenericBlockItem(var_factory=self.var_factory,
                                                        subsys=block_model,
                                                        api_object=self.api_object,
                                                        mode=self.mode,
                                                        name=item_name,
                                                        position_changed_callback=self._build_position_changed_callback(
                                                            block_model.uid))

        if block_model is None:
            return None
        else:
            pass

        set_modal_template_metadata(block_model, kind="source_emt", config=dict(source_config, block_type=block_type.name))
        self.block_counters[block_type] = count
        block_item.set_subsystem(block_model)
        block_item.position_changed_callback = self._build_position_changed_callback(block_model.uid)
        block_item.build_item()
        block_item.setToolTip(self._build_source_emt_modal_tooltip(source_config))
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

    @staticmethod
    def _build_default_dc_source_emt_modal_config(block_type: BlockType) -> Dict[str, Any]:
        """
        Build one default persisted configuration for one EMT DC source modal.

        :param block_type: DC source block type.
        :return: Default DC source configuration.
        """
        default_value: float = 1.0 if block_type in {
            BlockType.DC_VOLTAGE_SOURCE_EMT,
            BlockType.CONTROLLED_DC_VOLTAGE_SOURCE_EMT,
        } else 0.0
        return dict({
            "block_type": block_type.name,
            "source_value": default_value,
            "source_conductance_value": 100.0,
        })

    @staticmethod
    def _build_dc_source_emt_modal_tooltip(modal_config: Dict[str, Any]) -> str:
        """
        Build one compact tooltip for one EMT DC source block.

        :param modal_config: Persisted DC source modal configuration.
        :return: Tooltip text.
        """
        tooltip_lines: List[str] = [str(modal_config.get("block_type", "EMT DC source"))]

        if str(modal_config.get("block_type", "")) in {
            BlockType.DC_VOLTAGE_SOURCE_EMT.name,
            BlockType.CONTROLLED_DC_VOLTAGE_SOURCE_EMT.name,
        }:
            tooltip_lines.append(f"V={float(modal_config.get('source_value', 0.0)):.4g}")
            tooltip_lines.append(f"g={float(modal_config.get('source_conductance_value', 0.0)):.4g}")
        else:
            tooltip_lines.append(f"I={float(modal_config.get('source_value', 0.0)):.4g}")

        if str(modal_config.get("block_type", "")) in {
            BlockType.CONTROLLED_DC_VOLTAGE_SOURCE_EMT.name,
            BlockType.CONTROLLED_DC_CURRENT_SOURCE_EMT.name,
        }:
            tooltip_lines.append("Controlled by command input")

        return "\n".join(tooltip_lines)

    def _build_dc_source_emt_block_model(self,
                                         block_type: BlockType,
                                         item_name: str,
                                         modal_config: Dict[str, Any]) -> Block | None:
        """
        Build one EMT DC source block model from one modal configuration.

        :param block_type: DC source block type.
        :param item_name: Symbolic block name.
        :param modal_config: DC source modal configuration.
        :return: Built symbolic block or ``None``.
        """
        source_value: float = float(modal_config.get("source_value", 0.0))
        source_conductance_value: float = float(modal_config.get("source_conductance_value", 100.0))

        if block_type == BlockType.DC_VOLTAGE_SOURCE_EMT:
            return get_dc_voltage_source_emt_template(
                vf=self.var_factory,
                source_voltage_value=source_value,
                source_conductance_value=source_conductance_value,
                name=item_name,
            ).block
        elif block_type == BlockType.DC_CURRENT_SOURCE_EMT:
            return get_dc_current_source_emt_template(
                vf=self.var_factory,
                source_current_value=source_value,
                name=item_name,
            ).block
        elif block_type == BlockType.CONTROLLED_DC_VOLTAGE_SOURCE_EMT:
            return get_controlled_dc_voltage_source_emt_template(
                vf=self.var_factory,
                source_conductance_value=source_conductance_value,
                name=item_name,
            ).block
        elif block_type == BlockType.CONTROLLED_DC_CURRENT_SOURCE_EMT:
            return get_controlled_dc_current_source_emt_template(
                vf=self.var_factory,
                name=item_name,
            ).block
        else:
            return None

    def create_dc_source_emt_block_item(self, block_type: BlockType, x_pos: float, y_pos: float) -> GenericBlockItem | None:
        """
        Create one EMT DC source block configured through the DC source modal.

        :param block_type: DC source block type.
        :param x_pos: Drop x position.
        :param y_pos: Drop y position.
        :return: Created block item or ``None`` when the dialog is cancelled.
        """
        dialog = DcSourceEmtDialog(block_type=block_type, parent=self, initial_config=self._build_default_dc_source_emt_modal_config(block_type))

        if dialog.exec() == QDialog.DialogCode.Accepted:
            source_config: Dict[str, Any] = dict(self._build_default_dc_source_emt_modal_config(block_type), **dialog.get_configuration())
        else:
            return None

        count: int = self.block_counters.get(block_type, 0) + 1
        item_name: str = f"{block_type.name}_{count}"
        block_model: Block | None = self._build_dc_source_emt_block_model(block_type=block_type,
                                                                          item_name=item_name,
                                                                          modal_config=source_config)

        block_item: GenericBlockItem = GenericBlockItem(var_factory=self.var_factory,
                                                        subsys=block_model,
                                                        api_object=self.api_object,
                                                        mode=self.mode,
                                                        name=item_name,
                                                        position_changed_callback=self._build_position_changed_callback(
                                                            block_model.uid))

        if block_model is None:
            return None
        else:
            pass

        set_modal_template_metadata(block_model, kind="dc_source_emt", config=dict(source_config, block_type=block_type.name))
        self.block_counters[block_type] = count
        block_item.set_subsystem(block_model)
        block_item.position_changed_callback = self._build_position_changed_callback(block_model.uid)
        block_item.build_item()
        block_item.setToolTip(self._build_dc_source_emt_modal_tooltip(source_config))
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

    @staticmethod
    def _build_default_balanced_source_emt_modal_config(block_type: BlockType) -> Dict[str, Any]:
        """
        Build one default persisted configuration for one balanced EMT source modal.

        :param block_type: Balanced source block type.
        :return: Default balanced source configuration.
        """
        return dict({
            "block_type": block_type.name,
            "source_amplitude": 1.0,
            "source_frequency_hz": 50.0,
            "source_phase_a_deg": 0.0,
            "source_offset": 0.0,
            "source_conductance_value": 100.0,
        })

    @staticmethod
    def _build_balanced_source_emt_modal_tooltip(modal_config: Dict[str, Any]) -> str:
        """
        Build one compact tooltip for one balanced EMT source block.

        :param modal_config: Persisted balanced source modal configuration.
        :return: Tooltip text.
        """
        tooltip_lines: List[str] = [str(modal_config.get("block_type", "Balanced EMT source"))]
        tooltip_lines.append(f"A={float(modal_config.get('source_amplitude', 0.0)):.4g}")
        tooltip_lines.append(f"f={float(modal_config.get('source_frequency_hz', 0.0)):.4g} Hz")
        tooltip_lines.append(f"phiA={float(modal_config.get('source_phase_a_deg', 0.0)):.4g} deg")
        tooltip_lines.append(f"offset={float(modal_config.get('source_offset', 0.0)):.4g}")

        if str(modal_config.get("block_type", "")) in {
            BlockType.BALANCED_3PH_VOLTAGE_SOURCE_EMT.name,
            BlockType.CONTROLLED_BALANCED_3PH_VOLTAGE_SOURCE_EMT.name,
        }:
            tooltip_lines.append(f"g={float(modal_config.get('source_conductance_value', 0.0)):.4g}")

        if str(modal_config.get("block_type", "")) in {
            BlockType.CONTROLLED_BALANCED_3PH_VOLTAGE_SOURCE_EMT.name,
            BlockType.CONTROLLED_BALANCED_3PH_CURRENT_SOURCE_EMT.name,
        }:
            tooltip_lines.append("Amplitude controlled by command input")

        return "\n".join(tooltip_lines)

    def _build_balanced_source_emt_block_model(self,
                                               block_type: BlockType,
                                               item_name: str,
                                               modal_config: Dict[str, Any]) -> Block | None:
        """
        Build one balanced EMT source block model from one modal configuration.

        :param block_type: Balanced source block type.
        :param item_name: Symbolic block name.
        :param modal_config: Balanced source modal configuration.
        :return: Built symbolic block or ``None``.
        """
        source_amplitude: float = float(modal_config.get("source_amplitude", 1.0))
        source_frequency_hz: float = float(modal_config.get("source_frequency_hz", 50.0))
        source_phase_a_deg: float = float(modal_config.get("source_phase_a_deg", 0.0))
        source_offset: float = float(modal_config.get("source_offset", 0.0))
        source_conductance_value: float = float(modal_config.get("source_conductance_value", 100.0))

        if block_type == BlockType.BALANCED_3PH_VOLTAGE_SOURCE_EMT:
            return get_balanced_3ph_voltage_source_emt_template(
                vf=self.var_factory,
                amplitude_value=source_amplitude,
                frequency_hz=source_frequency_hz,
                phase_a_deg=source_phase_a_deg,
                offset_value=source_offset,
                source_conductance_value=source_conductance_value,
                name=item_name,
            ).block
        elif block_type == BlockType.BALANCED_3PH_CURRENT_SOURCE_EMT:
            return get_balanced_3ph_current_source_emt_template(
                vf=self.var_factory,
                amplitude_value=source_amplitude,
                frequency_hz=source_frequency_hz,
                phase_a_deg=source_phase_a_deg,
                offset_value=source_offset,
                name=item_name,
            ).block
        elif block_type == BlockType.CONTROLLED_BALANCED_3PH_VOLTAGE_SOURCE_EMT:
            return get_controlled_balanced_3ph_voltage_source_emt_template(
                vf=self.var_factory,
                frequency_hz=source_frequency_hz,
                phase_a_deg=source_phase_a_deg,
                offset_value=source_offset,
                source_conductance_value=source_conductance_value,
                name=item_name,
            ).block
        elif block_type == BlockType.CONTROLLED_BALANCED_3PH_CURRENT_SOURCE_EMT:
            return get_controlled_balanced_3ph_current_source_emt_template(
                vf=self.var_factory,
                frequency_hz=source_frequency_hz,
                phase_a_deg=source_phase_a_deg,
                offset_value=source_offset,
                name=item_name,
            ).block
        else:
            return None

    def create_balanced_source_emt_block_item(self, block_type: BlockType, x_pos: float, y_pos: float) -> GenericBlockItem | None:
        """
        Create one balanced EMT source block configured through its modal.

        :param block_type: Balanced source block type.
        :param x_pos: Drop x position.
        :param y_pos: Drop y position.
        :return: Created block item or ``None`` when the dialog is cancelled.
        """
        dialog = BalancedSourceEmtDialog(block_type=block_type, parent=self, initial_config=self._build_default_balanced_source_emt_modal_config(block_type))

        if dialog.exec() == QDialog.DialogCode.Accepted:
            source_config: Dict[str, Any] = dict(self._build_default_balanced_source_emt_modal_config(block_type), **dialog.get_configuration())
        else:
            return None

        count: int = self.block_counters.get(block_type, 0) + 1
        item_name: str = f"{block_type.name}_{count}"
        block_model: Block | None = self._build_balanced_source_emt_block_model(block_type=block_type,
                                                                                item_name=item_name,
                                                                                modal_config=source_config)

        block_item: GenericBlockItem = GenericBlockItem(var_factory=self.var_factory,
                                                        subsys=block_model,
                                                        api_object=self.api_object,
                                                        mode=self.mode,
                                                        name=item_name,
                                                        position_changed_callback=self._build_position_changed_callback(
                                                            block_model.uid))

        if block_model is None:
            return None
        else:
            pass

        set_modal_template_metadata(block_model, kind="balanced_source_emt", config=dict(source_config, block_type=block_type.name))
        self.block_counters[block_type] = count
        block_item.set_subsystem(block_model)
        block_item.position_changed_callback = self._build_position_changed_callback(block_model.uid)
        block_item.build_item()
        block_item.setToolTip(self._build_balanced_source_emt_modal_tooltip(source_config))
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

    @staticmethod
    def _build_default_arbitrary_source_emt_modal_config(block_type: BlockType) -> Dict[str, Any]:
        """
        Build one default persisted configuration for one arbitrary-waveform EMT source modal.

        :param block_type: Arbitrary source block type.
        :return: Default arbitrary source configuration.
        """
        return dict({
            "block_type": block_type.name,
            "phase_n": False,
            "phase_a": True,
            "phase_b": False,
            "phase_c": False,
            "time_points": [0.0, 0.02, 0.04],
            "value_points": [0.0, 1.0, 0.0],
            "source_conductance_value": 100.0,
        })

    @staticmethod
    def _extract_arbitrary_source_emt_phase_tuple(modal_config: Dict[str, Any]) -> tuple[bool, bool, bool, bool]:
        """
        Return the ordered phase tuple stored in one arbitrary EMT source modal configuration.

        :param modal_config: Persisted arbitrary source modal configuration.
        :return: ``(phase_n, phase_a, phase_b, phase_c)``.
        """
        return (
            bool(modal_config.get("phase_n", False)),
            bool(modal_config.get("phase_a", True)),
            bool(modal_config.get("phase_b", False)),
            bool(modal_config.get("phase_c", False)),
        )

    @staticmethod
    def _build_arbitrary_source_emt_modal_tooltip(modal_config: Dict[str, Any]) -> str:
        """
        Build one compact tooltip for one arbitrary-waveform EMT source block.

        :param modal_config: Persisted arbitrary source modal configuration.
        :return: Tooltip text.
        """
        active_labels: List[str] = list()

        if bool(modal_config.get("phase_n", False)):
            active_labels.append("N")
        if bool(modal_config.get("phase_a", False)):
            active_labels.append("A")
        if bool(modal_config.get("phase_b", False)):
            active_labels.append("B")
        if bool(modal_config.get("phase_c", False)):
            active_labels.append("C")

        tooltip_lines: List[str] = [str(modal_config.get("block_type", "Arbitrary EMT source"))]
        tooltip_lines.append(f"Phases: {', '.join(active_labels)}")
        tooltip_lines.append(f"Waveform points: {len(list(modal_config.get('time_points', list())))}")

        if str(modal_config.get("block_type", "")) == BlockType.ARBITRARY_WAVEFORM_VOLTAGE_SOURCE_EMT.name:
            tooltip_lines.append(f"g={float(modal_config.get('source_conductance_value', 0.0)):.4g}")

        return "\n".join(tooltip_lines)

    def _build_arbitrary_source_emt_block_model(self,
                                                block_type: BlockType,
                                                item_name: str,
                                                modal_config: Dict[str, Any]) -> Block | None:
        """
        Build one arbitrary-waveform EMT source block from one modal configuration.

        :param block_type: Arbitrary source block type.
        :param item_name: Symbolic block name.
        :param modal_config: Arbitrary source modal configuration.
        :return: Built symbolic block or ``None``.
        """
        phase_n, phase_a, phase_b, phase_c = self._extract_arbitrary_source_emt_phase_tuple(modal_config)
        time_points: List[float] = list(float(value) for value in modal_config.get("time_points", list([0.0, 0.02, 0.04])))
        value_points: List[float] = list(float(value) for value in modal_config.get("value_points", list([0.0, 1.0, 0.0])))
        source_conductance_value: float = float(modal_config.get("source_conductance_value", 100.0))

        if block_type == BlockType.ARBITRARY_WAVEFORM_VOLTAGE_SOURCE_EMT:
            return get_arbitrary_waveform_voltage_source_emt_template(
                vf=self.var_factory,
                phN=phase_n,
                phA=phase_a,
                phB=phase_b,
                phC=phase_c,
                time_points=time_points,
                value_points=value_points,
                source_conductance_value=source_conductance_value,
                name=item_name,
            ).block
        elif block_type == BlockType.ARBITRARY_WAVEFORM_CURRENT_SOURCE_EMT:
            return get_arbitrary_waveform_current_source_emt_template(
                vf=self.var_factory,
                phN=phase_n,
                phA=phase_a,
                phB=phase_b,
                phC=phase_c,
                time_points=time_points,
                value_points=value_points,
                name=item_name,
            ).block
        else:
            return None

    def create_arbitrary_source_emt_block_item(self, block_type: BlockType, x_pos: float, y_pos: float) -> GenericBlockItem | None:
        """
        Create one arbitrary-waveform EMT source block configured through its modal.

        :param block_type: Arbitrary source block type.
        :param x_pos: Drop x position.
        :param y_pos: Drop y position.
        :return: Created block item or ``None`` when the dialog is cancelled.
        """
        dialog = ArbitrarySourceEmtDialog(block_type=block_type, parent=self, initial_config=self._build_default_arbitrary_source_emt_modal_config(block_type))

        if dialog.exec() == QDialog.DialogCode.Accepted:
            source_config: Dict[str, Any] = dict(self._build_default_arbitrary_source_emt_modal_config(block_type), **dialog.get_configuration())
        else:
            return None

        count: int = self.block_counters.get(block_type, 0) + 1
        item_name: str = f"{block_type.name}_{count}"
        block_model: Block | None = self._build_arbitrary_source_emt_block_model(block_type=block_type,
                                                                                 item_name=item_name,
                                                                                 modal_config=source_config)

        block_item: GenericBlockItem = GenericBlockItem(var_factory=self.var_factory,
                                                        subsys = block_model,
                                                        api_object = self.api_object,
                                                        mode = self.mode,
                                                        name = item_name,
                                                        position_changed_callback = self._build_position_changed_callback(block_model.uid))

        if block_model is None:
            return None
        else:
            pass

        set_modal_template_metadata(block_model, kind="arbitrary_source_emt", config=dict(source_config,
                                                                                          block_type=block_type.name))
        self.block_counters[block_type] = count
        block_item.set_subsystem(block_model)
        block_item.position_changed_callback = self._build_position_changed_callback(block_model.uid)
        block_item.build_item()
        block_item.setToolTip(self._build_arbitrary_source_emt_modal_tooltip(source_config))
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

    @staticmethod
    def _build_default_transient_source_emt_modal_config(block_type: BlockType) -> Dict[str, Any]:
        """
        Build one default persisted configuration for one transient EMT source modal.

        :param block_type: Transient source block type.
        :return: Default transient source configuration.
        """
        return dict({
            "block_type": block_type.name,
            "phase_n": False,
            "phase_a": True,
            "phase_b": False,
            "phase_c": False,
            "initial_value": 0.0,
            "final_value": 1.0,
            "step_time_s": 0.02,
            "start_time_s": 0.01,
            "end_time_s": 0.03,
            "source_conductance_value": 100.0,
            "amplitude_value": 1.0,
            "alpha_value": 100.0,
            "beta_value": 5000.0,
            "delay_s": 0.0,
            "peak_value": 1.0,
            "front_time_s": 1.0e-4,
            "tail_time_s": 5.0e-4,
            "order_value": 4.0,
            "a_value": 1000.0,
            "b_value": 10000.0,
            "n_value": 2.0,
            "tn_s": 1.0e-4,
            "i1_value": 1.0,
            "t1_s": 5.0e-4,
            "i2_value": 0.5,
            "t2_s": 2.0e-4,
        })

    @staticmethod
    def _extract_transient_source_emt_phase_tuple(modal_config: Dict[str, Any]) -> tuple[bool, bool, bool, bool]:
        """
        Return the ordered phase tuple stored in one transient EMT source modal configuration.

        :param modal_config: Persisted transient source modal configuration.
        :return: ``(phase_n, phase_a, phase_b, phase_c)``.
        """
        return (
            bool(modal_config.get("phase_n", False)),
            bool(modal_config.get("phase_a", True)),
            bool(modal_config.get("phase_b", False)),
            bool(modal_config.get("phase_c", False)),
        )

    @staticmethod
    def _build_transient_source_emt_modal_tooltip(modal_config: Dict[str, Any]) -> str:
        """
        Build one compact tooltip for one transient EMT source block.

        :param modal_config: Persisted transient source modal configuration.
        :return: Tooltip text.
        """
        active_labels: List[str] = list()

        if bool(modal_config.get("phase_n", False)):
            active_labels.append("N")
        if bool(modal_config.get("phase_a", False)):
            active_labels.append("A")
        if bool(modal_config.get("phase_b", False)):
            active_labels.append("B")
        if bool(modal_config.get("phase_c", False)):
            active_labels.append("C")

        tooltip_lines: List[str] = [str(modal_config.get("block_type", "Transient EMT source"))]
        tooltip_lines.append(f"Phases: {', '.join(active_labels)}")

        if str(modal_config.get("block_type", "")) in {
            BlockType.STEP_VOLTAGE_SOURCE_EMT.name,
            BlockType.STEP_CURRENT_SOURCE_EMT.name,
        }:
            tooltip_lines.append(
                f"{float(modal_config.get('initial_value', 0.0)):.4g} -> {float(modal_config.get('final_value', 0.0)):.4g} at {float(modal_config.get('step_time_s', 0.0)):.4g}s"
            )
        elif str(modal_config.get("block_type", "")) in {
            BlockType.RAMP_VOLTAGE_SOURCE_EMT.name,
            BlockType.RAMP_CURRENT_SOURCE_EMT.name,
        }:
            tooltip_lines.append(
                f"{float(modal_config.get('initial_value', 0.0)):.4g} -> {float(modal_config.get('final_value', 0.0)):.4g} from {float(modal_config.get('start_time_s', 0.0)):.4g}s to {float(modal_config.get('end_time_s', 0.0)):.4g}s"
            )
        elif str(modal_config.get("block_type", "")) == BlockType.DOUBLE_EXPONENTIAL_CURRENT_SOURCE_EMT.name:
            tooltip_lines.append(
                f"A={float(modal_config.get('amplitude_value', 0.0)):.4g}, alpha={float(modal_config.get('alpha_value', 0.0)):.4g}, beta={float(modal_config.get('beta_value', 0.0)):.4g}"
            )
        elif str(modal_config.get("block_type", "")) == BlockType.HEIDLER_CURRENT_SOURCE_EMT.name:
            tooltip_lines.append(
                f"peak={float(modal_config.get('peak_value', 0.0)):.4g}, tf={float(modal_config.get('front_time_s', 0.0)):.4g}s, tt={float(modal_config.get('tail_time_s', 0.0)):.4g}s"
            )
        else:
            tooltip_lines.append(
                f"tn={float(modal_config.get('tn_s', 0.0)):.4g}s, I1={float(modal_config.get('i1_value', 0.0)):.4g}, I2={float(modal_config.get('i2_value', 0.0)):.4g}"
            )

        if str(modal_config.get("block_type", "")) in {
            BlockType.STEP_VOLTAGE_SOURCE_EMT.name,
            BlockType.RAMP_VOLTAGE_SOURCE_EMT.name,
        }:
            tooltip_lines.append(f"g={float(modal_config.get('source_conductance_value', 0.0)):.4g}")

        return "\n".join(tooltip_lines)

    def _build_transient_source_emt_block_model(self,
                                                block_type: BlockType,
                                                item_name: str,
                                                modal_config: Dict[str, Any]) -> Block | None:
        """
        Build one transient EMT source block from one modal configuration.

        :param block_type: Transient source block type.
        :param item_name: Symbolic block name.
        :param modal_config: Transient source modal configuration.
        :return: Built symbolic block or ``None``.
        """
        phase_n, phase_a, phase_b, phase_c = self._extract_transient_source_emt_phase_tuple(modal_config)

        if block_type == BlockType.STEP_VOLTAGE_SOURCE_EMT:
            return get_step_voltage_source_emt_template(
                vf=self.var_factory,
                phN=phase_n,
                phA=phase_a,
                phB=phase_b,
                phC=phase_c,
                initial_value=float(modal_config.get("initial_value", 0.0)),
                final_value=float(modal_config.get("final_value", 1.0)),
                step_time_s=float(modal_config.get("step_time_s", 0.02)),
                source_conductance_value=float(modal_config.get("source_conductance_value", 100.0)),
                name=item_name,
            ).block
        elif block_type == BlockType.STEP_CURRENT_SOURCE_EMT:
            return get_step_current_source_emt_template(
                vf=self.var_factory,
                phN=phase_n,
                phA=phase_a,
                phB=phase_b,
                phC=phase_c,
                initial_value=float(modal_config.get("initial_value", 0.0)),
                final_value=float(modal_config.get("final_value", 1.0)),
                step_time_s=float(modal_config.get("step_time_s", 0.02)),
                name=item_name,
            ).block
        elif block_type == BlockType.RAMP_VOLTAGE_SOURCE_EMT:
            return get_ramp_voltage_source_emt_template(
                vf=self.var_factory,
                phN=phase_n,
                phA=phase_a,
                phB=phase_b,
                phC=phase_c,
                initial_value=float(modal_config.get("initial_value", 0.0)),
                final_value=float(modal_config.get("final_value", 1.0)),
                start_time_s=float(modal_config.get("start_time_s", 0.01)),
                end_time_s=float(modal_config.get("end_time_s", 0.03)),
                source_conductance_value=float(modal_config.get("source_conductance_value", 100.0)),
                name=item_name,
            ).block
        elif block_type == BlockType.RAMP_CURRENT_SOURCE_EMT:
            return get_ramp_current_source_emt_template(
                vf=self.var_factory,
                phN=phase_n,
                phA=phase_a,
                phB=phase_b,
                phC=phase_c,
                initial_value=float(modal_config.get("initial_value", 0.0)),
                final_value=float(modal_config.get("final_value", 1.0)),
                start_time_s=float(modal_config.get("start_time_s", 0.01)),
                end_time_s=float(modal_config.get("end_time_s", 0.03)),
                name=item_name,
            ).block
        elif block_type == BlockType.DOUBLE_EXPONENTIAL_CURRENT_SOURCE_EMT:
            return get_double_exponential_current_source_emt_template(
                vf=self.var_factory,
                phN=phase_n,
                phA=phase_a,
                phB=phase_b,
                phC=phase_c,
                amplitude_value=float(modal_config.get("amplitude_value", 1.0)),
                alpha_value=float(modal_config.get("alpha_value", 100.0)),
                beta_value=float(modal_config.get("beta_value", 5000.0)),
                delay_s=float(modal_config.get("delay_s", 0.0)),
                name=item_name,
            ).block
        elif block_type == BlockType.HEIDLER_CURRENT_SOURCE_EMT:
            return get_heidler_current_source_emt_template(
                vf=self.var_factory,
                phN=phase_n,
                phA=phase_a,
                phB=phase_b,
                phC=phase_c,
                peak_value=float(modal_config.get("peak_value", 1.0)),
                front_time_s=float(modal_config.get("front_time_s", 1.0e-4)),
                tail_time_s=float(modal_config.get("tail_time_s", 5.0e-4)),
                order_value=float(modal_config.get("order_value", 4.0)),
                delay_s=float(modal_config.get("delay_s", 0.0)),
                name=item_name,
            ).block
        elif block_type == BlockType.CIGRE_SURGE_CURRENT_SOURCE_EMT:
            return get_cigre_surge_current_source_emt_template(
                vf=self.var_factory,
                phN=phase_n,
                phA=phase_a,
                phB=phase_b,
                phC=phase_c,
                a_value=float(modal_config.get("a_value", 1000.0)),
                b_value=float(modal_config.get("b_value", 10000.0)),
                n_value=float(modal_config.get("n_value", 2.0)),
                tn_s=float(modal_config.get("tn_s", 1.0e-4)),
                i1_value=float(modal_config.get("i1_value", 1.0)),
                t1_s=float(modal_config.get("t1_s", 5.0e-4)),
                i2_value=float(modal_config.get("i2_value", 0.5)),
                t2_s=float(modal_config.get("t2_s", 2.0e-4)),
                delay_s=float(modal_config.get("delay_s", 0.0)),
                name=item_name,
            ).block
        else:
            return None

    def create_transient_source_emt_block_item(self, block_type: BlockType, x_pos: float, y_pos: float) -> GenericBlockItem | None:
        """
        Create one transient EMT source block configured through its modal.

        :param block_type: Transient source block type.
        :param x_pos: Drop x position.
        :param y_pos: Drop y position.
        :return: Created block item or ``None`` when the dialog is cancelled.
        """
        dialog = TransientSourceEmtDialog(block_type=block_type, parent=self, initial_config=self._build_default_transient_source_emt_modal_config(block_type))

        if dialog.exec() == QDialog.DialogCode.Accepted:
            source_config: Dict[str, Any] = dict(self._build_default_transient_source_emt_modal_config(block_type), **dialog.get_configuration())
        else:
            return None

        count: int = self.block_counters.get(block_type, 0) + 1
        item_name: str = f"{block_type.name}_{count}"
        block_model: Block | None = self._build_transient_source_emt_block_model(block_type=block_type,
                                                                                 item_name=item_name,
                                                                                 modal_config=source_config)

        block_item: GenericBlockItem = GenericBlockItem(var_factory=self.var_factory,
                                                        subsys = block_model,
                                                        api_object = self.api_object,
                                                        mode = self.mode,
                                                        name = item_name,
                                                        position_changed_callback = self._build_position_changed_callback(block_model.uid))


        if block_model is None:
            return None
        else:
            pass

        set_modal_template_metadata(block_model, kind="transient_source_emt", config=dict(source_config, block_type=block_type.name))
        self.block_counters[block_type] = count
        block_item.set_subsystem(block_model)
        block_item.position_changed_callback = self._build_position_changed_callback(block_model.uid)
        block_item.build_item()
        block_item.setToolTip(self._build_transient_source_emt_modal_tooltip(source_config))
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

        for option_key in JMARTI_MODAL_OPTION_KEYS:
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
        block_item: GenericBlockItem = GenericBlockItem(var_factory=self.var_factory,
                                                        subsys=block_model,
                                                        api_object=self.api_object,
                                                        mode=self.mode,
                                                        name=item_name,
                                                        position_changed_callback=self._build_position_changed_callback(block_model.uid))


        if block_model is None:
            return None
        else:
            pass

        set_modal_template_metadata(block_model, kind="jmarti_line_emt", config=modal_config)
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

        elif block_type in {BlockType.TRAFO_EMT, BlockType.XFMR_TRANSFORMER}:
            topology_config: Dict[str, Any] | None = self._resolve_transformer_topology_configuration()

            if topology_config is None:
                dialog = self._build_transformer_topology_emt_dialog(block_type=block_type)

                if dialog.exec() == QDialog.DialogCode.Accepted:
                    topology_config = dialog.get_configuration()
                    topology_config["allow_modify_template"] = True
                else:
                    return None
            else:
                topology_config = dict(topology_config)

            item_name: str = f"{block_type.name}_{count}"
            block_model = self._build_transformer_topology_emt_block_model(
                block_type=block_type,
                item_name=item_name,
                modal_config=topology_config,
            )
            if block_model is None:
                return None

            set_modal_template_metadata(block_model, kind="transformer_topology_emt",
                                        config=dict(topology_config, block_type=block_type.name))

            # The dynamic editor must not overwrite the static transformer
            # winding connection stored by the network object. The dynamic block
            # keeps its own modal configuration and must follow the static device
            # contract during template assignment.
            if isinstance(self.api_object, BranchParent):
                pass
            else:
                pass


        elif block_type in {BlockType.EXP_LOAD_EMT, BlockType.ZIP_LOAD_EMT}:
            dialog = self._build_load_topology_emt_dialog(block_type=block_type)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                load_config = dialog.get_configuration()
            else:
                return None

            item_name: str = f"{block_type.name}_{count}"
            block_model = self._build_load_topology_emt_block_model(
                block_type=block_type,
                item_name=item_name,
                modal_config=load_config,
            )

            set_modal_template_metadata(block_model, kind="load_topology_emt",
                                        config=dict(load_config, block_type=block_type.name))
            self._annotate_internal_grounding_link_blocks(block_model)

            # The dynamic editor must not overwrite the static load connection.
            if isinstance(self.api_object, InjectionParent):
                pass
            else:
                pass

        elif block_type == BlockType.EMT_PI_LINE or block_type == BlockType.EMT_BERGERON_LINE:
            dialog = EmtTemplateWizardDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                phase_n, phase_a, phase_b, phase_c = dialog.get_values()
            else:
                return None

            item_name: str = f"{block_type.name}_{count}"
            block_model = create_emt_wizard_block(phase_n, phase_a, phase_b, phase_c, self.var_factory,
                                                  block_type=block_type, item_name=item_name)

            set_modal_template_metadata(
                block_model,
                kind="emt_phase_wizard",
                config=dict({
                    "block_type": block_type.name,
                    "phase_n": phase_n,
                    "phase_a": phase_a,
                    "phase_b": phase_b,
                    "phase_c": phase_c,
                }),
            )


        elif block_type == BlockType.GROUNDING_LINK_EMT:
            dialog = self._build_grounding_link_emt_dialog()

            if dialog.exec() == QDialog.DialogCode.Accepted:
                grounding_config = dialog.get_configuration()
            else:
                return None

            try:
                template_kwargs = self._build_grounding_link_emt_template_kwargs(grounding_config)
            except ValueError as exc:
                QtWidgets.QMessageBox.warning(self, "Grounding Link", str(exc))
                return None

            item_name: str = f"grounding_link_emt_{count}"
            block_model = get_grounding_link_emt_template(vf=self.var_factory, name=item_name, **template_kwargs).block
            set_modal_template_metadata(block_model, kind="grounding_link_emt", config=dict(grounding_config))

        elif block_type == BlockType.SWITCH_EMT:
            dialog = SwitchEmtDialog(self)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                switch_config = dialog.get_switch_configuration()
            else:
                return None

            item_name: str = f"switch_emt_{count}"

            block_model = get_switch_emt_template(vf=self.var_factory, name=item_name, **switch_config).block
            set_modal_template_metadata(
                block_model,
                kind="switch_emt",
                config=dict(switch_config),
            )

        elif block_type == BlockType.FAULT_EMT:
            default_fault_config: Dict[str, Any] = self._build_default_fault_emt_modal_config()
            dialog = FaultEmtDialog(self, initial_config=default_fault_config)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                fault_config = dict(default_fault_config)
                fault_config.update(dialog.get_configuration())
            else:
                return None

            item_name = f"fault_emt_{count}"
            block_model = get_fault_emt_template(
                vf=self.var_factory,
                fault_type=fault_config["fault_type"],
                phA=bool(fault_config["phA"]),
                phB=bool(fault_config["phB"]),
                phC=bool(fault_config["phC"]),
                signal_controlled=bool(fault_config["signal_controlled"]),
                initial_closed=bool(fault_config["initial_closed"]),
                fault_resistance=float(fault_config["fault_resistance"]),
                ground_resistance=float(fault_config["ground_resistance"]),
                open_conductance=float(fault_config["open_conductance"]),
                fault_time_constant=float(fault_config["fault_time_constant"]),
                command_threshold=float(fault_config["command_threshold"]),
                name=item_name,
            ).block
            set_modal_template_metadata(
                block_model,
                kind="fault_emt",
                config=dict(fault_config),
            )

        elif block_type == BlockType.RLC_COMBO_EMT:
            dialog = self._build_rlc_combo_emt_dialog()

            if dialog.exec() == QDialog.DialogCode.Accepted:
                rlc_config = dialog.get_configuration()
            else:
                return None

            try:
                template_kwargs = self._build_rlc_combo_emt_template_kwargs(rlc_config)
            except ValueError as exc:
                QtWidgets.QMessageBox.warning(self, "RLC Combo", str(exc))
                return None

            item_name: str = f"rlc_combo_emt_{count}"

            block_model = get_shunt_rlc_combo_emt_template(vf=self.var_factory, name=item_name, **template_kwargs).block
            set_modal_template_metadata(block_model, kind="rlc_combo_emt", config=dict(rlc_config))
            self._annotate_internal_grounding_link_blocks(block_model)

            # The dynamic editor must not overwrite the static injection
            # connection. The EMT block stores its own symbolic topology.
            if isinstance(self.api_object, InjectionParent):
                pass
            else:
                pass

        elif block_type in {BlockType.R_LOAD_EMT, BlockType.L_LOAD_EMT,BlockType.C_LOAD_EMT}:
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

            item_name: str = f"{block_type.name}_{count}"

            block_model = get_shunt_rlc_combo_emt_template(vf=self.var_factory, name=item_name, **template_kwargs).block
            set_modal_template_metadata(block_model, kind="shunt_component_emt",
                                        config=dict(shunt_config, block_type=block_type.name))
            self._annotate_internal_grounding_link_blocks(block_model)

            # The dynamic editor must not overwrite the static injection
            # connection. The EMT block stores its own symbolic topology.
            if isinstance(self.api_object, InjectionParent):
                pass
            else:
                pass

        elif _is_load_topology_block_type(BlockType):
            dialog = self._build_load_topology_emt_dialog(block_type=block_type)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                load_config = dialog.get_configuration()
            else:
                return None

            item_name: str = f"{block_type.name}_{count}"

            block_model = self._build_load_topology_emt_block_model(
                block_type=block_type,
                item_name=item_name,
                modal_config=load_config,
            )
            set_modal_template_metadata(block_model, kind="load_topology_emt",
                                        config=dict(load_config, block_type=block_type.name))
            self._annotate_internal_grounding_link_blocks(block_model)

            # The dynamic editor must not overwrite the static load connection.
            if isinstance(self.api_object, InjectionParent):
                pass
            else:
                pass

        elif block_type == BlockType.GROUNDING_LINK_EMT:
            dialog = self._build_grounding_link_emt_dialog()

            if dialog.exec() == QDialog.DialogCode.Accepted:
                grounding_config = dialog.get_configuration()
            else:
                return None

            try:
                template_kwargs = self._build_grounding_link_emt_template_kwargs(grounding_config)
            except ValueError as exc:
                QtWidgets.QMessageBox.warning(self, "Grounding Link", str(exc))
                return None

            item_name: str = f"grounding_link_emt_{count}"

            block_model = get_grounding_link_emt_template(vf=self.var_factory, name=item_name, **template_kwargs).block
            set_modal_template_metadata(block_model, kind="grounding_link_emt", config=dict(grounding_config))

        elif block_type == BlockType.NONLINEAR_RESISTOR_EMT:
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

            item_name: str = f"nonlinear_resistor_emt_{count}"

            block_model = get_nonlinear_resistor_emt_template(
                vf=self.var_factory,
                voltage_points=voltage_points,
                current_points=current_points,
                name=item_name,
            ).block
            set_modal_template_metadata(
                block_model,
                kind="nonlinear_resistor_emt",
                config=dict({
                    "voltage_points": voltage_points,
                    "current_points": current_points,
                }),
            )

        elif block_type == BlockType.NONLINEAR_RESISTOR_EMT:
            topology_config: Dict[str, Any] | None = self._resolve_transformer_topology_configuration()

            if topology_config is None:
                dialog = self._build_transformer_topology_emt_dialog(block_type=block_type)

                if dialog.exec() == QDialog.DialogCode.Accepted:
                    topology_config = dialog.get_configuration()
                    topology_config["allow_modify_template"] = True
                else:
                    return None
            else:
                topology_config = dict(topology_config)

            item_name: str = f"{block_type.name}_{count}"

            block_model = self._build_transformer_topology_emt_block_model(
                block_type=block_type,
                item_name=item_name,
                modal_config=topology_config,
            )

            if block_model is None:
                return None
            else:
                pass

            set_modal_template_metadata(block_model, kind="transformer_topology_emt",
                                        config=dict(topology_config, block_type=block_type.name))

            # The dynamic editor must not overwrite the static transformer
            # winding connection stored by the network object.
            if isinstance(self.api_object, BranchParent):
                pass
            else:
                pass

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
        block_item: BlockItem = BlockItem(var_factory=self.var_factory, api_object=self.api_object, mode=self.mode, name=item_name)
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

    def create_conn_items(self, item_source: GenericBlockItem, item_dest: GenericBlockItem, pairs:List[tuple[Var, Var]]):
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
                    diagram=self.diagram
                )
                self.scene.addItem(connection)
                self.diagram.add_branch(
                    connectionitem_uid=connection.uid,
                    device_uid_from=item_source.subsys.uid,
                    device_uid_to=item_dest.subsys.uid,
                    port_number_from=source_port.index,
                    port_number_to=target_port.index,
                    color=WIRE_COLOR.name()
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
            block_item: ProtectedConnectionBlockItem = ProtectedConnectionBlockItem(var_factory=self.var_factory, name=item_name)
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
            tpe=TEMPLATE_NODE_TYPE,
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
        set_modal_template_metadata(
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

    def create_switch_emt_block_item(self, x_pos: float, y_pos: float) -> GenericBlockItem | None:
        """
        Create one EMT switch block configured through the switch modal.

        :param x_pos: Drop x position.
        :param y_pos: Drop y position.
        :return: Created block item or None when the dialog is cancelled.
        """
        dialog = SwitchEmtDialog(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            switch_config = dialog.get_switch_configuration()
            count: int = self.block_counters.get(BlockType.SWITCH_EMT, 0) + 1
            item_name: str = f"switch_emt_{count}"
            block_model = get_switch_emt_template(vf=self.var_factory, name=item_name, **switch_config).block
            block_item: GenericBlockItem = GenericBlockItem(var_factory=self.var_factory,
                                                            subsys=block_model,
                                                            api_object=self.api_object,
                                                            mode=self.mode,
                                                            name=item_name,
                                                            position_changed_callback=self._build_position_changed_callback(block_model.uid))

            set_modal_template_metadata(
                block_model,
                kind="switch_emt",
                config=dict(switch_config),
            )

            self.block_counters[BlockType.SWITCH_EMT] = count
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
                tpe=BlockType.SWITCH_EMT.name,
                device_uid=block_model.uid,
            )
            self.mark_unapplied_changes()
            return block_item
        else:
            return None

    def _build_default_fault_emt_modal_config(self) -> Dict[str, Any]:
        """
        Build one default persisted configuration for the EMT fault modal.

        :return: Default fault configuration.
        """
        return dict({
            "fault_type": FaultType.LG,
            "placement_side": EmtFaultPlacementSide.FromSide,
            "phA": True,
            "phB": False,
            "phC": False,
            "signal_controlled": False,
            "initial_closed": False,
            "fault_resistance": 1.0e-4,
            "ground_resistance": 1.0e-4,
            "open_conductance": 1.0e-8,
            "fault_time_constant": 1.0e-6,
            "command_threshold": 0.5,
        })

    def _build_fault_emt_modal_tooltip(self, modal_config: Dict[str, Any]) -> str:
        """
        Build one compact tooltip for one EMT fault block.

        :param modal_config: Persisted fault modal configuration.
        :return: Tooltip text.
        """
        active_labels: List[str] = list()
        fault_tpe_obj: object = modal_config.get("fault_type", FaultType.LG)
        fault_tpe: FaultType

        if isinstance(fault_tpe_obj, FaultType):
            fault_tpe = fault_tpe_obj
        else:
            fault_tpe = FaultType.argparse(str(fault_tpe_obj))

        if bool(modal_config.get("phA", False)):
            active_labels.append("A")
        else:
            pass

        if bool(modal_config.get("phB", False)):
            active_labels.append("B")
        else:
            pass

        if bool(modal_config.get("phC", False)):
            active_labels.append("C")
        else:
            pass

        tooltip_lines: List[str] = list(["FAULT_EMT"])
        tooltip_lines.append(f"Type: {fault_tpe.name}")
        tooltip_lines.append(f"Placement: {str(modal_config.get('placement_side', EmtFaultPlacementSide.FromSide))}")
        tooltip_lines.append(f"Phases: {', '.join(active_labels)}")
        tooltip_lines.append(f"Rf={float(modal_config.get('fault_resistance', 0.0)):.4g}")

        if fault_tpe in {FaultType.LG, FaultType.LLG, FaultType.LLLG}:
            tooltip_lines.append(f"Rg={float(modal_config.get('ground_resistance', 0.0)):.4g}")
        else:
            pass

        tooltip_lines.append(f"Gopen={float(modal_config.get('open_conductance', 0.0)):.4g}")
        tooltip_lines.append(f"tau={float(modal_config.get('fault_time_constant', 0.0)):.4g} s")

        if bool(modal_config.get("signal_controlled", False)):
            tooltip_lines.append("Controlled by command input")
        else:
            tooltip_lines.append("Controlled by EMT events")

        return "\n".join(tooltip_lines)

    def create_fault_emt_block_item(self, x_pos: float, y_pos: float) -> GenericBlockItem | None:
        """
        Create one EMT fault block configured through the fault modal.

        :param x_pos: Drop x position.
        :param y_pos: Drop y position.
        :return: Created block item or None when the dialog is cancelled.
        """
        default_config: Dict[str, Any] = self._build_default_fault_emt_modal_config()
        dialog = FaultEmtDialog(self, initial_config=default_config)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # The dialog returns a persisted modal payload, and the defaults fill any
            # future optional keys so old diagrams remain rebuildable after refactors.
            fault_config: Dict[str, Any] = dict(default_config)
            fault_config.update(dialog.get_configuration())
        else:
            return None

        count: int = self.block_counters.get(BlockType.FAULT_EMT, 0) + 1
        item_name: str = f"fault_emt_{count}"
        block_model = get_fault_emt_template(
            vf=self.var_factory,
            fault_type=fault_config["fault_type"],
            placement_side=fault_config["placement_side"],
            phA=bool(fault_config["phA"]),
            phB=bool(fault_config["phB"]),
            phC=bool(fault_config["phC"]),
            signal_controlled=bool(fault_config["signal_controlled"]),
            initial_closed=bool(fault_config["initial_closed"]),
            fault_resistance=float(fault_config["fault_resistance"]),
            ground_resistance=float(fault_config["ground_resistance"]),
            open_conductance=float(fault_config["open_conductance"]),
            fault_time_constant=float(fault_config["fault_time_constant"]),
            command_threshold=float(fault_config["command_threshold"]),
            name=item_name,
        ).block
        block_item: GenericBlockItem = GenericBlockItem(var_factory=self.var_factory,
                                                        subsys=block_model,
                                                        api_object=self.api_object,
                                                        mode=self.mode,
                                                        name=item_name,
                                                        position_changed_callback=self._build_position_changed_callback(block_model.uid))

        set_modal_template_metadata(
            block_model,
            kind="fault_emt",
            config=dict(fault_config),
        )

        self.block_counters[BlockType.FAULT_EMT] = count
        block_item.set_subsystem(block_model)
        block_item.position_changed_callback = self._build_position_changed_callback(block_model.uid)
        block_item.build_item()
        block_item.setToolTip(self._build_fault_emt_modal_tooltip(fault_config))
        self.main_block.add(block_model)
        self.scene.addItem(block_item)
        block_item.setPos(QtCore.QPointF(x_pos, y_pos))
        self.diagram.add_node(
            name=item_name,
            x=x_pos,
            y=y_pos,
            tpe=BlockType.FAULT_EMT.name,
            device_uid=block_model.uid,
        )
        self.mark_unapplied_changes()
        return block_item

    def create_rlc_combo_emt_block_item(self, x_pos: float, y_pos: float) -> GenericBlockItem | None:
        """
        Create one combined EMT RLC shunt block configured through its modal.

        :param x_pos: Drop x position.
        :param y_pos: Drop y position.
        :return: Created block item or None when the dialog is cancelled.
        """
        dialog = self._build_rlc_combo_emt_dialog()

        if dialog.exec() == QDialog.DialogCode.Accepted:
            rlc_config = dialog.get_configuration()
        else:
            return None

        try:
            template_kwargs = self._build_rlc_combo_emt_template_kwargs(rlc_config)
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "RLC Combo", str(exc))
            return None

        count: int = self.block_counters.get(BlockType.RLC_COMBO_EMT, 0) + 1
        item_name: str = f"rlc_combo_emt_{count}"
        block_model = get_shunt_rlc_combo_emt_template(vf=self.var_factory, name=item_name, **template_kwargs).block
        block_item: GenericBlockItem = GenericBlockItem(var_factory=self.var_factory,
                                                        subsys=block_model,
                                                        api_object=self.api_object,
                                                        mode=self.mode,
                                                        name=item_name,
                                                        position_changed_callback=self._build_position_changed_callback(block_model.uid))

        set_modal_template_metadata(block_model, kind="rlc_combo_emt", config=dict(rlc_config))
        self._annotate_internal_grounding_link_blocks(block_model)

        # The dynamic editor must not overwrite the static injection
        # connection. The EMT block stores its own symbolic topology.
        if isinstance(self.api_object, InjectionParent):
            pass
        else:
            pass

        self.block_counters[BlockType.RLC_COMBO_EMT] = count
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
            tpe=BlockType.RLC_COMBO_EMT.name,
            device_uid=block_model.uid,
        )
        self.mark_unapplied_changes()
        return block_item

    def create_induction_motor_emt_block_item(self, x_pos: float, y_pos: float) -> GenericBlockItem | None:
        """
        Create one induction-motor EMT block configured through its modal.

        :param x_pos: Drop x position.
        :param y_pos: Drop y position.
        :return: Created block item or None when the dialog is cancelled.
        """
        # The modal runs before block creation so the selected template level becomes
        # part of the initial symbolic build and persisted metadata from the start.
        default_config: Dict[str, Any] = self._build_default_induction_motor_emt_modal_config()
        dialog: InductionMotorEmtDialog = self._build_induction_motor_emt_dialog(initial_config=default_config)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            induction_motor_config: Dict[str, Any] = dialog.get_configuration()
        else:
            return None

        count: int = self.block_counters.get(BlockType.INDUCTION_MOTOR_EMT, 0) + 1
        item_name: str = f"induction_motor_emt_{count}"
        block_model: Block = self._build_induction_motor_emt_block_model(
            item_name=item_name,
            modal_config=induction_motor_config,
        )
        block_item: GenericBlockItem = GenericBlockItem(var_factory=self.var_factory,
                                                        subsys=block_model,
                                                        api_object=self.api_object,
                                                        mode=self.mode,
                                                        name=item_name,
                                                        position_changed_callback=self._build_position_changed_callback(block_model.uid))


        # Persist the modal selection so modify-template and rebuild flows can
        # recreate the same symbolic template later.
        set_modal_template_metadata(block_model, kind="induction_motor_emt", config=dict(induction_motor_config))

        self.block_counters[BlockType.INDUCTION_MOTOR_EMT] = count
        block_item.set_subsystem(block_model)
        block_item.position_changed_callback = self._build_position_changed_callback(block_model.uid)
        block_item.build_item()
        block_item.setToolTip(self._build_induction_motor_emt_modal_tooltip(induction_motor_config))

        # The scene item, main block, and persisted diagram must all be updated
        # together so later rebuilds and apply/save operations stay consistent.
        self.main_block.add(block_model)
        self.scene.addItem(block_item)
        block_item.setPos(QtCore.QPointF(x_pos, y_pos))
        self.diagram.add_node(
            name=item_name,
            x=x_pos,
            y=y_pos,
            tpe=BlockType.INDUCTION_MOTOR_EMT.name,
            device_uid=block_model.uid,
        )
        self.mark_unapplied_changes()
        return block_item

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
            template_kwargs = self._build_shunt_component_emt_template_kwargs(block_type=block_type, modal_config=shunt_config)
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "EMT Shunt", str(exc))
            return None

        count: int = self.block_counters.get(block_type, 0) + 1
        item_name: str = f"{block_type.name}_{count}"
        block_model = get_shunt_rlc_combo_emt_template(vf=self.var_factory,
                                                       name=item_name,
                                                       **template_kwargs).block
        block_item: GenericBlockItem = GenericBlockItem(var_factory=self.var_factory,
                                                        subsys = block_model,
                                                        api_object = self.api_object,
                                                        mode = self.mode,
                                                        name = item_name,
                                                        position_changed_callback = self._build_position_changed_callback(block_model.uid))


        set_modal_template_metadata(block_model, kind="shunt_component_emt", config=dict(shunt_config, block_type=block_type.name))
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

    def create_load_topology_emt_block_item(self,
                                            block_type: BlockType,
                                            x_pos: float,
                                            y_pos: float) -> GenericBlockItem | None:
        """
        Create one modal-configured EMT load block with explicit neutral/ground topology.

        :param block_type: ``EXP_LOAD_EMT`` or ``ZIP_LOAD_EMT``.
        :param x_pos: Drop x position.
        :param y_pos: Drop y position.
        :return: Created block item or None when the dialog is cancelled.
        """
        dialog = self._build_load_topology_emt_dialog(block_type=block_type)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            load_config = dialog.get_configuration()
        else:
            return None

        count: int = self.block_counters.get(block_type, 0) + 1
        item_name: str = f"{block_type.name}_{count}"
        block_model = self._build_load_topology_emt_block_model(
            block_type=block_type,
            item_name=item_name,
            modal_config=load_config,
        )
        block_item: GenericBlockItem = GenericBlockItem(var_factory=self.var_factory,
                                                        subsys=block_model,
                                                        api_object=self.api_object,
                                                        mode=self.mode,
                                                        name=item_name,
                                                        position_changed_callback=self._build_position_changed_callback(
                                                            block_model.uid))

        if block_model is None:
            return None
        else:
            pass

        set_modal_template_metadata(block_model, kind="load_topology_emt", config=dict(load_config, block_type=block_type.name))
        self._annotate_internal_grounding_link_blocks(block_model)

        # The dynamic editor must not overwrite the static load connection.
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

    def create_grounding_link_emt_block_item(self, x_pos: float, y_pos: float) -> GenericBlockItem | None:
        """
        Create one modal-configured EMT grounding-link block.

        :param x_pos: Drop x position.
        :param y_pos: Drop y position.
        :return: Created block item or None when the dialog is cancelled.
        """
        dialog = self._build_grounding_link_emt_dialog()

        if dialog.exec() == QDialog.DialogCode.Accepted:
            grounding_config = dialog.get_configuration()
        else:
            return None

        try:
            template_kwargs = self._build_grounding_link_emt_template_kwargs(grounding_config)
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "Grounding Link", str(exc))
            return None

        count: int = self.block_counters.get(BlockType.GROUNDING_LINK_EMT, 0) + 1
        item_name: str = f"grounding_link_emt_{count}"
        block_model = get_grounding_link_emt_template(vf=self.var_factory, name=item_name, **template_kwargs).block
        block_item: GenericBlockItem = GenericBlockItem(var_factory=self.var_factory,
                                                        subsys=block_model,
                                                        api_object=self.api_object,
                                                        mode=self.mode,
                                                        name=item_name,
                                                        position_changed_callback=self._build_position_changed_callback(block_model.uid))

        set_modal_template_metadata(block_model, kind="grounding_link_emt", config=dict(grounding_config))

        self.block_counters[BlockType.GROUNDING_LINK_EMT] = count
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
            tpe=BlockType.GROUNDING_LINK_EMT.name,
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
        block_model = get_nonlinear_resistor_emt_template(
            vf=self.var_factory,
            voltage_points=voltage_points,
            current_points=current_points,
            name=item_name,
        ).block
        block_item: GenericBlockItem = GenericBlockItem(var_factory=self.var_factory,
                                                        subsys=block_model,
                                                        api_object=self.api_object,
                                                        mode=self.mode,
                                                        name=item_name,
                                                        position_changed_callback=self._build_position_changed_callback(block_model.uid))

        set_modal_template_metadata(
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

    def create_transformer_topology_emt_block_item(self,
                                                   block_type: BlockType,
                                                   x_pos: float,
                                                   y_pos: float) -> GenericBlockItem | None:
        """
        Create one modal-configured EMT transformer block.

        :param block_type: ``TRAFO_EMT`` or ``XFMR_TRANSFORMER``.
        :param x_pos: Drop x position.
        :param y_pos: Drop y position.
        :return: Created block item or None when the dialog is cancelled.
        """
        topology_config: Dict[str, Any] | None = self._resolve_transformer_topology_configuration()

        if topology_config is None:
            dialog = self._build_transformer_topology_emt_dialog(block_type=block_type)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                topology_config = dialog.get_configuration()
                topology_config["allow_modify_template"] = True
            else:
                return None
        else:
            topology_config = dict(topology_config)

        count: int = self.block_counters.get(block_type, 0) + 1
        item_name: str = f"{block_type.name}_{count}"
        block_model = self._build_transformer_topology_emt_block_model(
            block_type=block_type,
            item_name=item_name,
            modal_config=topology_config,
        )
        block_item: GenericBlockItem = GenericBlockItem(var_factory=self.var_factory,
                                                        subsys=block_model,
                                                        api_object=self.api_object,
                                                        mode=self.mode,
                                                        name=item_name,
                                                        position_changed_callback=self._build_position_changed_callback(
                                                            block_model.uid))


        if block_model is None:
            return None
        else:
            pass

        set_modal_template_metadata(block_model, kind="transformer_topology_emt", config=dict(topology_config, block_type=block_type.name))

        # The dynamic editor must not overwrite the static transformer winding
        # connection stored by the network object.
        if isinstance(self.api_object, BranchParent):
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

    def _resolve_transformer_topology_configuration(self) -> Dict[str, Any] | None:
        """
        Resolve one EMT transformer topology directly from the bound API object.

        When the editor is attached to one real transformer device or one
        transformer-type object, the winding connections already belong to that
        object and should not be asked again through a modal dialog.

        :return: Resolved topology configuration or ``None`` when unavailable.
        """
        if isinstance(self.api_object, Transformer2W):
            return dict({
                "conn_f": self.api_object.conn_f,
                "conn_t": self.api_object.conn_t,
                "allow_modify_template": False,
            })
        else:
            if isinstance(self.api_object, TransformerType):
                return dict({
                    "conn_f": self.api_object.conn_hv,
                    "conn_t": self.api_object.conn_lv,
                    "allow_modify_template": False,
                })
            else:
                return None

    def _build_rlc_combo_emt_dialog(self,
                                    initial_config: Dict[str, Any] | None = None) -> RlcComboEmtDialog:
        """
        Build the modal dialog used by the EMT combined RLC workflow.

        :param initial_config: Optional persisted modal configuration.
        :return: Configured dialog instance.
        """
        nominal_voltage_kv, base_power_mva, base_frequency_hz = self._get_rlc_combo_base_values()
        static_connection_type: ShuntConnectionType | None = None
        allow_static_device_values: bool = False

        if isinstance(self.api_object, (Load, Shunt, ControllableShunt)):
            static_connection_type = self.api_object.conn
            allow_static_device_values = True
        elif isinstance(self.api_object, InjectionParent):
            static_connection_type = self.api_object.conn
        else:
            pass

        resolved_config: Dict[str, Any] | None = None
        if initial_config is not None:
            resolved_config = dict(initial_config)
        else:
            resolved_config = dict()

        if "use_static_device_values" not in resolved_config and "use_static_load_values" in resolved_config:
            resolved_config["use_static_device_values"] = resolved_config["use_static_load_values"]
        else:
            pass

        return RlcComboEmtDialog(
            self,
            initial_config=resolved_config,
            allow_static_device_values=allow_static_device_values,
            static_connection_type=static_connection_type,
            nominal_voltage_kv=nominal_voltage_kv,
            base_power_mva=base_power_mva,
            base_frequency_hz=base_frequency_hz,
        )

    @staticmethod
    def _build_default_induction_motor_emt_modal_config(level: InductionMotorEmtLevel = InductionMotorEmtLevel.SINGLE_CAGE) -> Dict[str, Any]:
        """
        Build the default persisted configuration for one induction-motor EMT modal.

        :param level: Default template level.
        :return: Default induction-motor modal configuration.
        """
        return dict({"level": level.name})

    def _build_induction_motor_emt_dialog(self,
                                          initial_config: Dict[str, Any] | None = None) -> InductionMotorEmtDialog:
        """
        Build the modal dialog used by the induction-motor EMT workflow.

        :param initial_config: Optional persisted modal configuration.
        :return: Configured dialog instance.
        """
        dialog_config: Dict[str, Any]
        if initial_config is None:
            dialog_config = self._build_default_induction_motor_emt_modal_config()
        else:
            dialog_config = dict(initial_config)

        return InductionMotorEmtDialog(
            self,
            initial_config=dialog_config,
        )

    @staticmethod
    def _build_induction_motor_emt_modal_tooltip(modal_config: Dict[str, Any]) -> str:
        """
        Build one compact tooltip for one induction-motor EMT block.

        :param modal_config: Persisted induction-motor modal configuration.
        :return: Tooltip text.
        """
        level: InductionMotorEmtLevel = coerce_induction_motor_emt_level(
            modal_config.get("level", InductionMotorEmtLevel.SINGLE_CAGE.name)
        )
        return "Induction motor EMT\n" + get_induction_motor_emt_level_label(level)

    def _build_induction_motor_emt_block_model(self,
                                               item_name: str,
                                               modal_config: Dict[str, Any]) -> Block:
        """
        Build one induction-motor EMT block model from one modal configuration.

        :param item_name: Symbolic block name.
        :param modal_config: Induction-motor modal configuration.
        :return: Built symbolic block.
        """
        level: InductionMotorEmtLevel = coerce_induction_motor_emt_level(
            modal_config.get("level", InductionMotorEmtLevel.SINGLE_CAGE.name)
        )
        template_level: int = get_induction_motor_emt_template_level(level)
        return get_induction_motor_emt_template(vf=self.var_factory, level=template_level, name=item_name).block

    def _build_grounding_link_emt_dialog(self,
                                         initial_config: Dict[str, Any] | None = None) -> GroundingLinkEmtDialog:
        """
        Build the modal dialog used by the EMT grounding-link workflow.

        :param initial_config: Optional persisted modal configuration.
        :return: Configured dialog instance.
        """
        nominal_voltage_kv, base_power_mva, base_frequency_hz = self._get_rlc_combo_base_values()
        return GroundingLinkEmtDialog(
            self,
            initial_config=initial_config,
            nominal_voltage_kv=nominal_voltage_kv,
            base_power_mva=base_power_mva,
            base_frequency_hz=base_frequency_hz,
        )

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

    @staticmethod
    def _get_transformer_topology_dialog_title(block_type: BlockType) -> str:
        """
        Return the dialog title for one EMT transformer block.

        :param block_type: ``TRAFO_EMT`` or ``XFMR_TRANSFORMER``.
        :return: Window title.
        """
        if block_type == BlockType.TRAFO_EMT:
            return "Configure EMT Transformer Topology"
        elif block_type == BlockType.XFMR_TRANSFORMER:
            return "Configure EMT XFMR Transformer Topology"
        else:
            raise ValueError(f"Unsupported EMT transformer block type '{block_type.name}'")

    def _build_transformer_topology_emt_dialog(self,
                                               block_type: BlockType,
                                               initial_config: Dict[str, Any] | None = None) -> TransformerTopologyEmtDialog:
        """
        Build the modal dialog used by one EMT transformer block.

        :param block_type: ``TRAFO_EMT`` or ``XFMR_TRANSFORMER``.
        :param initial_config: Optional persisted modal configuration.
        :return: Configured dialog instance.
        """
        resolved_config: Dict[str, Any]
        force_static_connection: bool = False
        if initial_config is not None:
            resolved_config = dict(initial_config)
        else:
            auto_config: Dict[str, Any] | None = self._resolve_transformer_topology_configuration()

            if auto_config is not None:
                resolved_config = auto_config
            else:
                resolved_config = dict({
                    "conn_f": WindingType.GroundedStar,
                    "conn_t": WindingType.GroundedStar,
                })

        static_from_connection: WindingType | None = None
        static_to_connection: WindingType | None = None
        auto_config = self._resolve_transformer_topology_configuration()
        if auto_config is not None:
            static_from_connection = auto_config.get("conn_f", None)
            static_to_connection = auto_config.get("conn_t", None)
            if isinstance(self.api_object, (Transformer2W, TransformerType)):
                resolved_config["conn_f"] = static_from_connection
                resolved_config["conn_t"] = static_to_connection
                force_static_connection = True
            else:
                pass
        else:
            pass

        return TransformerTopologyEmtDialog(
            title=self._get_transformer_topology_dialog_title(block_type),
            parent=self,
            initial_config=resolved_config,
            static_from_connection=static_from_connection if force_static_connection else None,
            static_to_connection=static_to_connection if force_static_connection else None,
        )

    @staticmethod
    def _get_load_topology_dialog_title(block_type: BlockType) -> str:
        """
        Return the dialog title for one EMT load-topology block.

        :param block_type: ``EXP_LOAD_EMT`` or ``ZIP_LOAD_EMT``.
        :return: Window title.
        """
        if block_type == BlockType.EXP_LOAD_EMT:
            return "Configure EMT Exponential Load"
        elif block_type == BlockType.ZIP_LOAD_EMT:
            return "Configure EMT ZIP Load"
        else:
            raise ValueError(f"Unsupported EMT load-topology block type '{block_type.name}'")

    def _build_load_topology_emt_dialog(self,
                                        block_type: BlockType,
                                        initial_config: Dict[str, Any] | None = None) -> LoadTopologyEmtDialog:
        """
        Build the modal dialog used by one EMT load-topology block.

        :param block_type: ``EXP_LOAD_EMT`` or ``ZIP_LOAD_EMT``.
        :param initial_config: Optional persisted modal configuration.
        :return: Configured dialog instance.
        """
        resolved_config: Dict[str, Any] | None = None
        static_connection_type: ShuntConnectionType | None = None
        allow_static_device_values: bool = False

        if initial_config is not None:
            resolved_config = dict(initial_config)
        else:
            resolved_config = dict()

        if isinstance(self.api_object, Load):
            static_connection_type = self.api_object.conn
            allow_static_device_values = True
        elif isinstance(self.api_object, InjectionParent):
            static_connection_type = self.api_object.conn
        else:
            pass

        return LoadTopologyEmtDialog(
            title=self._get_load_topology_dialog_title(block_type),
            parent=self,
            initial_config=resolved_config,
            allow_static_device_values=allow_static_device_values,
            static_connection_type=static_connection_type,
        )

    @staticmethod
    def _annotate_internal_grounding_link_blocks(block_model: Block) -> None:
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
                set_modal_template_metadata(child_block, kind="grounding_link_emt", config=grounding_config)
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

    def _build_rlc_combo_emt_template_kwargs(self, modal_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert one modal configuration into the EMT template builder arguments.

        ``Physical R/L/C`` values are forwarded directly. ``R + Reactances`` is
        converted into the physical inductance and capacitance expected by the
        current EMT child templates.

        :param modal_config: Raw modal configuration.
        :return: Template-builder keyword arguments.
        :raises ValueError: If the modal configuration is not numerically valid.
        """
        template_kwargs: Dict[str, Any] = dict(self._build_rlc_direct_values_from_modal_config(modal_config))
        if "solid_connection" in template_kwargs:
            del template_kwargs["solid_connection"]
        else:
            pass
        template_kwargs.update({
            "phA": bool(modal_config.get("phA", True)),
            "phB": bool(modal_config.get("phB", True)),
            "phC": bool(modal_config.get("phC", True)),
            "connection_type": modal_config.get("connection_type", ShuntConnectionType.GroundedStar),
        })

        return template_kwargs

    def _build_grounding_link_emt_template_kwargs(self, modal_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert one grounding-link modal configuration into template arguments.

        :param modal_config: Raw modal configuration.
        :return: Template-builder keyword arguments.
        """
        return self._build_rlc_direct_values_from_modal_config(modal_config)

    def _build_shunt_component_emt_template_kwargs(self,
                                                   block_type: BlockType,
                                                   modal_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert one single-component EMT shunt modal configuration into template arguments.

        :param block_type: ``R_LOAD_EMT``, ``L_LOAD_EMT`` or ``C_LOAD_EMT``.
        :param modal_config: Raw modal configuration.
        :return: Template-builder keyword arguments.
        """
        use_static_load_values: bool = bool(modal_config.get("use_static_device_values", modal_config.get("use_static_load_values", False)))

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

    def _build_load_topology_emt_block_model(self,
                                             block_type: BlockType,
                                             item_name: str,
                                             modal_config: Dict[str, Any]) -> Block | None:
        """
        Build one EMT load block with explicit neutral/ground topology.

        :param block_type: ``EXP_LOAD_EMT`` or ``ZIP_LOAD_EMT``.
        :param item_name: Symbolic block name.
        :param modal_config: Modal configuration.
        :return: Block model or ``None``.
        """
        ph_a: bool = bool(modal_config.get("phA", True))
        ph_b: bool = bool(modal_config.get("phB", True))
        ph_c: bool = bool(modal_config.get("phC", True))
        connection_type = modal_config.get("connection_type", ShuntConnectionType.GroundedStar)

        if block_type == BlockType.EXP_LOAD_EMT:
            block_model = get_exponential_load_emt(
                vf=self.var_factory,
                phA=ph_a,
                phB=ph_b,
                phC=ph_c,
                connection_type=connection_type,
                name=item_name,
            ).block
        elif block_type == BlockType.ZIP_LOAD_EMT:
            block_model = get_load_ZIP_emt_template(
                vf=self.var_factory,
                phA=ph_a,
                phB=ph_b,
                phC=ph_c,
                connection_type=connection_type,
                name=item_name,
            ).block
        else:
            raise ValueError(f"Unsupported EMT load-topology block type '{block_type.name}'")

        block_model.name = item_name
        return block_model

    def _build_transformer_topology_emt_block_model(self,
                                                    block_type: BlockType,
                                                    item_name: str,
                                                    modal_config: Dict[str, Any]) -> Block | None:
        """
        Build one EMT transformer block with explicit winding topology.

        :param block_type: ``TRAFO_EMT`` or ``XFMR_TRANSFORMER``.
        :param item_name: Symbolic block name.
        :param modal_config: Modal configuration.
        :return: Block model or ``None``.
        """
        conn_f = modal_config.get("conn_f", WindingType.GroundedStar)
        conn_t = modal_config.get("conn_t", WindingType.GroundedStar)

        if block_type == BlockType.TRAFO_EMT:
            block_model = create_block_of_type(
                var_factory=self.var_factory,
                block_type=block_type,
                item_name=item_name,
                api_object=type("_TrafoApiConfig", (), {"conn_f": conn_f, "conn_t": conn_t})(),
            )
        elif block_type == BlockType.XFMR_TRANSFORMER:
            block_model = create_block_of_type(
                var_factory=self.var_factory,
                block_type=block_type,
                item_name=item_name,
                api_object=type("_XfmrApiConfig", (), {"conn_f": conn_f, "conn_t": conn_t})(),
            )
        else:
            raise ValueError(f"Unsupported EMT transformer block type '{block_type.name}'")

        if block_model is None:
            return None
        else:
            block_model.name = item_name
            return block_model

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

    def _sync_rlc_combo_load_base_values(self, template_kwargs: Dict[str, Any]) -> None:
        """
        Preserve the legacy hook without mutating static objects.

        The dynamic editor must not write EMT-derived values back into the static
        network model. This hook therefore remains as a no-op so existing call
        sites can keep their workflow shape while shunt parameters are now owned
        either by ``api_obj_mapping`` or by ``event_dict`` inside the EMT block.

        :param template_kwargs: Resolved EMT template arguments.
        :return: None.
        """
        if len(template_kwargs) >= 0:
            pass
        else:
            pass

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
        set_modal_template_metadata(
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
        set_modal_template_metadata(
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
        set_modal_template_metadata(
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
        set_modal_template_metadata(
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
                                    payload: BlockType | BasicBlockTemplateDescriptor | RmsModelTemplate | EmtModelTemplate | FmuTemplate | SignalPairPayload,
                                    x_pos: float,
                                    y_pos: float) -> GenericBlockItem | None:
        """
        Materialize one library payload on the diagram scene.
        """

        if isinstance(payload, SignalPairPayload):
            items = self.create_signal_pair_item(x_pos=x_pos, y_pos=y_pos)
            return items[0] if items else None

        if isinstance(payload, BlockType) and payload == BlockType.GENERIC:
            return self.create_generic_block_item(block_type=payload, x_pos=x_pos, y_pos=y_pos)
        elif isinstance(payload, BlockType) and payload in {
            BlockType.EMT_PI_LINE,
            BlockType.EMT_BERGERON_LINE,
            BlockType.EMT_JMARTI_LINE,
            BlockType.VOLTAGE_SOURCE_EMT,
            BlockType.CURRENT_SOURCE_EMT,
            BlockType.CONTROLLED_VOLTAGE_SOURCE_EMT,
            BlockType.CONTROLLED_CURRENT_SOURCE_EMT,
            BlockType.DC_VOLTAGE_SOURCE_EMT,
            BlockType.DC_CURRENT_SOURCE_EMT,
            BlockType.CONTROLLED_DC_VOLTAGE_SOURCE_EMT,
            BlockType.CONTROLLED_DC_CURRENT_SOURCE_EMT,
            BlockType.BALANCED_3PH_VOLTAGE_SOURCE_EMT,
            BlockType.BALANCED_3PH_CURRENT_SOURCE_EMT,
            BlockType.CONTROLLED_BALANCED_3PH_VOLTAGE_SOURCE_EMT,
            BlockType.CONTROLLED_BALANCED_3PH_CURRENT_SOURCE_EMT,
            BlockType.ARBITRARY_WAVEFORM_VOLTAGE_SOURCE_EMT,
            BlockType.ARBITRARY_WAVEFORM_CURRENT_SOURCE_EMT,
            BlockType.STEP_VOLTAGE_SOURCE_EMT,
            BlockType.STEP_CURRENT_SOURCE_EMT,
            BlockType.RAMP_VOLTAGE_SOURCE_EMT,
            BlockType.RAMP_CURRENT_SOURCE_EMT,
            BlockType.DOUBLE_EXPONENTIAL_CURRENT_SOURCE_EMT,
            BlockType.HEIDLER_CURRENT_SOURCE_EMT,
            BlockType.CIGRE_SURGE_CURRENT_SOURCE_EMT,
            BlockType.FAULT_EMT,
            BlockType.SWITCH_EMT,
            BlockType.GROUNDING_LINK_EMT,
            BlockType.NONLINEAR_RESISTOR_EMT,
            BlockType.RLC_COMBO_EMT,
            BlockType.INDUCTION_MOTOR_EMT,
        }:
            if payload == BlockType.FAULT_EMT:
                return self.create_fault_emt_block_item(x_pos=x_pos, y_pos=y_pos)
            elif payload == BlockType.SWITCH_EMT:
                return self.create_switch_emt_block_item(x_pos=x_pos, y_pos=y_pos)
            elif payload == BlockType.GROUNDING_LINK_EMT:
                return self.create_grounding_link_emt_block_item(x_pos=x_pos, y_pos=y_pos)
            elif payload == BlockType.NONLINEAR_RESISTOR_EMT:
                return self.create_nonlinear_resistor_emt_block_item(x_pos=x_pos, y_pos=y_pos)
            elif payload == BlockType.RLC_COMBO_EMT:
                return self.create_rlc_combo_emt_block_item(x_pos=x_pos, y_pos=y_pos)
            elif payload == BlockType.EMT_JMARTI_LINE:
                return self.create_jmarti_line_emt_block_item(x_pos=x_pos, y_pos=y_pos)
            elif payload == BlockType.INDUCTION_MOTOR_EMT:
                return self.create_induction_motor_emt_block_item(x_pos=x_pos, y_pos=y_pos)
            # Source EMT blocks share the same creation dialog, so the payload
            # is first classified by its concrete source family before building
            # the corresponding editor block.
            elif payload in {
                BlockType.VOLTAGE_SOURCE_EMT,
                BlockType.CURRENT_SOURCE_EMT,
                BlockType.CONTROLLED_VOLTAGE_SOURCE_EMT,
                BlockType.CONTROLLED_CURRENT_SOURCE_EMT,
            }:
                return self.create_source_emt_block_item(block_type=payload, x_pos=x_pos, y_pos=y_pos)
            elif payload in {
                BlockType.DC_VOLTAGE_SOURCE_EMT,
                BlockType.DC_CURRENT_SOURCE_EMT,
                BlockType.CONTROLLED_DC_VOLTAGE_SOURCE_EMT,
                BlockType.CONTROLLED_DC_CURRENT_SOURCE_EMT,
            }:
                return self.create_dc_source_emt_block_item(block_type=payload, x_pos=x_pos, y_pos=y_pos)
            elif payload in {
                BlockType.BALANCED_3PH_VOLTAGE_SOURCE_EMT,
                BlockType.BALANCED_3PH_CURRENT_SOURCE_EMT,
                BlockType.CONTROLLED_BALANCED_3PH_VOLTAGE_SOURCE_EMT,
                BlockType.CONTROLLED_BALANCED_3PH_CURRENT_SOURCE_EMT,
            }:
                return self.create_balanced_source_emt_block_item(block_type=payload, x_pos=x_pos, y_pos=y_pos)
            elif payload in {
                BlockType.ARBITRARY_WAVEFORM_VOLTAGE_SOURCE_EMT,
                BlockType.ARBITRARY_WAVEFORM_CURRENT_SOURCE_EMT,
            }:
                return self.create_arbitrary_source_emt_block_item(block_type=payload, x_pos=x_pos, y_pos=y_pos)
            elif payload in {
                BlockType.STEP_VOLTAGE_SOURCE_EMT,
                BlockType.STEP_CURRENT_SOURCE_EMT,
                BlockType.RAMP_VOLTAGE_SOURCE_EMT,
                BlockType.RAMP_CURRENT_SOURCE_EMT,
                BlockType.DOUBLE_EXPONENTIAL_CURRENT_SOURCE_EMT,
                BlockType.HEIDLER_CURRENT_SOURCE_EMT,
                BlockType.CIGRE_SURGE_CURRENT_SOURCE_EMT,
            }:
                return self.create_transient_source_emt_block_item(block_type=payload, x_pos=x_pos, y_pos=y_pos)
            else:
                return self.create_emt_wizard_block_item(block_type=payload, x_pos=x_pos, y_pos=y_pos)
        elif isinstance(payload, BlockType) and _is_load_topology_block_type(payload):
            return self.create_load_topology_emt_block_item(block_type=payload, x_pos=x_pos, y_pos=y_pos)
        elif isinstance(payload, BlockType) and payload in {
            BlockType.R_LOAD_EMT,
            BlockType.L_LOAD_EMT,
            BlockType.C_LOAD_EMT,
        }:
            return self.create_shunt_component_emt_block_item(block_type=payload, x_pos=x_pos, y_pos=y_pos)
        elif isinstance(payload, BlockType) and payload in {
            BlockType.TRAFO_EMT,
            BlockType.XFMR_TRANSFORMER,
        }:
            return self.create_transformer_topology_emt_block_item(block_type=payload, x_pos=x_pos, y_pos=y_pos)
        elif isinstance(payload, BlockType):
            return self.create_block_item_mix(block_type=payload, x_pos=x_pos, y_pos=y_pos)
        elif isinstance(payload, BasicBlockTemplateDescriptor):
            if payload.template_key in LOOKUP_ARRAY_LINEAR_DESCRIPTOR_KEYS:
                return self.create_lookup_array_linear_descriptor_item(payload, x_pos, y_pos)
            elif payload.template_key in INVERSE_LOOKUP_ARRAY_LINEAR_DESCRIPTOR_KEYS:
                return self.create_inverse_lookup_array_linear_descriptor_item(payload, x_pos, y_pos)
            elif payload.template_key in LOOKUP_ARRAY_SPLINE_DESCRIPTOR_KEYS:
                return self.create_lookup_array_spline_descriptor_item(payload, x_pos, y_pos)
            elif payload.template_key in LOOKUP_MATRIX_LINEAR_DESCRIPTOR_KEYS:
                return self.create_lookup_matrix_linear_descriptor_item(payload, x_pos, y_pos)
            elif payload.template_key in LOOKUP_MATRIX_SPLINE_DESCRIPTOR_KEYS:
                return self.create_lookup_matrix_spline_descriptor_item(payload, x_pos, y_pos)
            else:
                template: EmtModelTemplate = load_basic_block_catalog_template(payload, self.var_factory)
                return self.create_template_block_item(template=template, x_pos=x_pos, y_pos=y_pos)
        elif isinstance(payload, (RmsModelTemplate, EmtModelTemplate, FmuTemplate)):
            return self.create_template_block_item(template=payload, x_pos=x_pos, y_pos=y_pos)
        else:
            return None
    # def create_library_payload_item(self,
    #                                 payload: BlockType | BasicBlockTemplateDescriptor | RmsModelTemplate | EmtModelTemplate | FmuTemplate,
    #                                 x_pos: float,
    #                                 y_pos: float) -> GenericBlockItem | GenericBlockItem | None:
    #     """
    #     Materialize one library payload on the diagram scene.
    #     """
    #     if isinstance(payload, BlockType) and payload in {
    #         BlockType.EMT_PI_LINE,
    #         BlockType.EMT_BERGERON_LINE,
    #         BlockType.EMT_JMARTI_LINE,
    #         BlockType.SWITCH_EMT,
    #         BlockType.GROUNDING_LINK_EMT,
    #         BlockType.NONLINEAR_RESISTOR_EMT,
    #         BlockType.RLC_COMBO_EMT,
    #         BlockType.EXP_LOAD_EMT,
    #         BlockType.ZIP_LOAD_EMT,
    #         BlockType.R_LOAD_EMT,
    #         BlockType.L_LOAD_EMT,
    #         BlockType.C_LOAD_EMT,
    #         BlockType.TRAFO_EMT,
    #         BlockType.XFMR_TRANSFORMER,
    #     }:
    #
    #         return self.create_block_item_mix(block_type=payload, x_pos=x_pos, y_pos=y_pos)
    #
    #     elif isinstance(payload, BlockType):
    #         return self.create_block_item_mix(block_type=payload, x_pos=x_pos, y_pos=y_pos)
    #     elif isinstance(payload, BasicBlockTemplateDescriptor):
    #         if payload.template_key in LOOKUP_ARRAY_LINEAR_DESCRIPTOR_KEYS:
    #             return self.create_lookup_array_linear_descriptor_item(payload, x_pos, y_pos)
    #         elif payload.template_key in INVERSE_LOOKUP_ARRAY_LINEAR_DESCRIPTOR_KEYS:
    #             return self.create_inverse_lookup_array_linear_descriptor_item(payload, x_pos, y_pos)
    #         elif payload.template_key in LOOKUP_ARRAY_SPLINE_DESCRIPTOR_KEYS:
    #             return self.create_lookup_array_spline_descriptor_item(payload, x_pos, y_pos)
    #         elif payload.template_key in LOOKUP_MATRIX_LINEAR_DESCRIPTOR_KEYS:
    #             return self.create_lookup_matrix_linear_descriptor_item(payload, x_pos, y_pos)
    #         elif payload.template_key in LOOKUP_MATRIX_SPLINE_DESCRIPTOR_KEYS:
    #             return self.create_lookup_matrix_spline_descriptor_item(payload, x_pos, y_pos)
    #         else:
    #             template: EmtModelTemplate = load_basic_block_catalog_template(payload, self.var_factory)
    #             return self.create_template_block_item(template=template, x_pos=x_pos, y_pos=y_pos)
    #     elif isinstance(payload, (RmsModelTemplate, EmtModelTemplate, FmuTemplate)):
    #         return self.create_template_block_item(template=payload, x_pos=x_pos, y_pos=y_pos)
    #     else:
    #         return None

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

        item_in = PairedItem(
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

        item_out = PairedItem(
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

        self.scene.removeItem(item)

        # disconnect variables
        if source_port.subsystem.subsys is not None and target_port.subsystem.subsys is not None:
            dst_var: Var = source_port.subsystem.subsys.out_vars[source_port.index]
            target_var: Var = target_port.subsystem.subsys.in_vars[target_port.index]

            if target_var.network_conn:
                self.var_factory.remove_connection(dst_var, target_var)
                source_port.subsystem.refresh_port_metadata()
            else:
                self.var_factory.remove_connection(target_var, dst_var)
                target_port.subsystem.refresh_port_metadata()

    def remove_block_item(self, item: BlockItem | GenericBlockItem) -> None:
        """
        Remove a block and all of its attached connections.

        :param item:
        :return:
        """
        port: PortItem
        conn: ConnectionItem
        connections_to_remove: List[ConnectionItem] = list()
        child_block: Block

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

    def _remove_connection_interface_for_block(self, item: BlockItem | GenericBlockItem) -> None:
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

    def remove_item(self, item: BlockItem | GenericBlockItem | ConnectionItem) -> None:
        """
        Remove a block or connection from scene and model state.

        :param item:
        :return:
        """
        if isinstance(item, ConnectionItem):
            self.remove_connection_item(item)
            self.mark_unapplied_changes()
        elif isinstance(item, (BlockItem, GenericBlockItem, GenericBlockItem)):
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
            self.add_connection_vars_rms()



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
    def add_connection_vars_rms(self):
        """
        Add a block with bus connection variables to connect the device
        :return:
        """

        if isinstance(self.api_object, BranchParent):

            # connect bus variables
            if self.api_object.bus_from.rms_model.empty():
                initialize_bus_rms(self.api_object.bus_from, self.var_factory)

            if self.api_object.device_type in [DeviceType.VscDevice]:
                if self.api_object.bus_from.is_dc:
                    Vdc, Vm, Va = get_bus_rms_algebraic_vars(self.api_object.bus_from.rms_model)
                    self.main_block.in_vars.append(Vm)
                    self.main_block.in_vars.append(Va)
                    self.main_block.in_vars.append(Vdc)

                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.Vm: Vm})
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.Va: Va})
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.Vdc: Vdc})

            else:
                if self.api_object.bus_from.rms_model.empty():
                    initialize_bus_rms(self.api_object.bus_from, self.var_factory)

                Vmf, Vaf = get_bus_rms_algebraic_vars(self.api_object.bus_from.rms_model)

                if self.api_object.bus_to.rms_model.empty():
                    initialize_bus_rms(self.api_object.bus_to, self.var_factory)

                Vmt, Vat = get_bus_rms_algebraic_vars(self.api_object.bus_to.rms_model)

                self.main_block.in_vars.append(Vmf)
                self.main_block.in_vars.append(Vaf)
                self.main_block.in_vars.append(Vmt)
                self.main_block.in_vars.append(Vat)

                self.main_block.external_mapping.update(
                    {VarPowerFlowReferenceType.Vmf: Vmf})
                self.main_block.external_mapping.update(
                    {VarPowerFlowReferenceType.Vaf: Vaf})

                self.main_block.external_mapping.update(
                    {VarPowerFlowReferenceType.Vmt: Vmt})
                self.main_block.external_mapping.update(
                    {VarPowerFlowReferenceType.Vat: Vat})

            # add connection variables
            if self.api_object.device_type in [DeviceType.VscDevice]:

                Pt = self.var_factory.add_var('net_conn_Pt', VarPowerFlowReferenceType.Pt, True)
                Qt = self.var_factory.add_var('net_conn_Qt', VarPowerFlowReferenceType.Qt, True)
                Qf = self.var_factory.add_var('net_conn_Qf', VarPowerFlowReferenceType.Qf, True)

                self.main_block.out_vars.append(Pt)
                self.main_block.out_vars.append(Qt)
                self.main_block.out_vars.append(Qf)

                self.main_block.external_mapping.update({VarPowerFlowReferenceType.Pt: Pt})
                self.main_block.external_mapping.update({VarPowerFlowReferenceType.Qt: Qt})
                self.main_block.external_mapping.update({VarPowerFlowReferenceType.Qt: Qf})

            else:

                Pf = self.var_factory.add_var('net_conn_Pf', VarPowerFlowReferenceType.P, True)
                Qf = self.var_factory.add_var('net_conn_Qf', VarPowerFlowReferenceType.Q, True)

                self.main_block.out_vars.append(Pf)
                self.main_block.out_vars.append(Qf)

                self.main_block.external_mapping.update({VarPowerFlowReferenceType.Pf: Pf})
                self.main_block.external_mapping.update({VarPowerFlowReferenceType.Qf: Qf})

                Pt = self.var_factory.add_var('net_conn_Pt', VarPowerFlowReferenceType.P, True)
                Qt = self.var_factory.add_var('net_conn_Qt', VarPowerFlowReferenceType.Q, True)

                self.main_block.out_vars.append(Pt)
                self.main_block.out_vars.append(Qt)

                self.main_block.external_mapping.update({VarPowerFlowReferenceType.Pt: Pt})
                self.main_block.external_mapping.update({VarPowerFlowReferenceType.Qt: Qt})

        elif isinstance(self.api_object, InjectionParent):

            # connect bus variables
            if self.api_object.bus.rms_model.empty():
                initialize_bus_rms(self.api_object.bus, self.var_factory)

            Vm, Va = get_bus_rms_algebraic_vars(self.api_object.bus.rms_model)
            self.main_block.in_vars.append(Vm)
            self.main_block.in_vars.append(Va)

            self.main_block.external_mapping.update(
                {VarPowerFlowReferenceType.Vm: Vm})
            self.main_block.external_mapping.update(
                {VarPowerFlowReferenceType.Va: Va})

            # add connection variables
            P = self.var_factory.add_var('net_conn_P', VarPowerFlowReferenceType.P, True)
            Q = self.var_factory.add_var('net_conn_Q', VarPowerFlowReferenceType.Q, True)

            self.main_block.out_vars.append(P)
            self.main_block.out_vars.append(Q)

            self.main_block.external_mapping.update({VarPowerFlowReferenceType.P: P})
            self.main_block.external_mapping.update({VarPowerFlowReferenceType.Q: Q})




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
        ))
        specs.extend(build_rms_bus_input_specs(
            bus=self.api_object.bus_to,
            voltage_reference=VarPowerFlowReferenceType.Vmt,
            angle_reference=VarPowerFlowReferenceType.Vat,
            dc_voltage_reference=VarPowerFlowReferenceType.Vt_dc,
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

    def _get_requested_emt_bus_masks_from_current_interface(self) -> tuple[bool, list[bool] | None, list[bool] | None, list[bool] | None]:
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
            elif len(child_block.in_vars) == 1 and len(child_block.out_vars) == 0 and child_block.name.startswith("net_conn_"):
                # Defensive guard for editor-generated output interface wrappers.
                pass
            elif len(child_block.in_vars) == 0 and len(child_block.out_vars) == 1 and child_block.name.startswith(("v_", "Vdc_")):
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
                        if protected_item is not None and len(protected_item.outputs) > 0 and input_index < len(block_item.inputs):
                            if self._connection_exists_between_ports(protected_item.outputs[0], block_item.inputs[input_index]):
                                pass
                            else:
                                connection_item: ConnectionItem = ConnectionItem(
                                    source_port=protected_item.outputs[0],
                                    target_port=block_item.inputs[input_index],
                                    diagram=self.diagram,
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
                        if protected_item is not None and len(protected_item.inputs) > 0 and output_index < len(block_item.outputs):
                            if self._connection_exists_between_ports(block_item.outputs[output_index], protected_item.inputs[0]):
                                pass
                            else:
                                connection_item = ConnectionItem(
                                    source_port=block_item.outputs[output_index],
                                    target_port=protected_item.inputs[0],
                                    diagram=self.diagram,
                                )
                                self.scene.addItem(connection_item)
                        else:
                            pass
                    else:
                        pass

    def _get_editor_interface_input_item_for_ref(self,
                                                 interface_inputs_by_ref: Dict[VarPowerFlowReferenceType, ProtectedConnectionBlockItem],
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
                                                  interface_outputs_by_ref: Dict[VarPowerFlowReferenceType, ProtectedConnectionBlockItem],
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

            if isinstance(selected_item, BlockItem):
                return selected_item.subsys
            elif isinstance(selected_item, GenericBlockItem):
                return selected_item.subsys
            elif isinstance(selected_item, GenericBlockItem):
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
        dialog: EditParameterDialog = EditParameterDialog(api_object, row_data.kind, self)

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
        dialog: AddParameterDialog = AddParameterDialog(api_object, self)

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
        vars_selected = [self._table_source_index(idx).row() for idx in self.ui.variablesTableView.selectionModel().selectedRows()]
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
        params_selected = [self._table_source_index(idx).row() for idx in self.ui.parametersTableView.selectionModel().selectedRows()]
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
        equations_selected = [self._table_source_index(idx).row() for idx in self.ui.equationsTableView.selectionModel().selectedRows()]
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

    def on_scene_selection_changed(self) -> None:
        """
        Refresh the right-side parameters table from the selected block.

        :return:
        """
        selected_block: Block | None = self.get_selected_scene_block()
        self._selected_side_block = selected_block
        self.refresh_active_side_panel()

    @QtCore.Slot(int)
    def on_side_panel_page_changed(self, index: int) -> None:
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


    def modify_scene_item_template(self, item: BlockItem | GenericBlockItem | ConnectionItem) -> None:
        """
        Reopen the modal configuration of a block item when metadata is available.

        :param item: Scene item selected from the context menu.
        :return: None.
        """
        if not isinstance(item, (BlockItem, GenericBlockItem)) or item.subsys is None:
            return
        else:
            pass

        modal_kind, modal_config = get_modal_template_metadata(item.subsys)

        if modal_kind is None or modal_config is None:
            return
        else:
            pass

        if modal_kind == "lookup_array_1d":
            self._modify_lookup_array_like_block(item, modal_config, build_lookup_array_linear_runtime_template)
        elif modal_kind == "lookup_array_inverse":
            self._modify_lookup_array_like_block(item, modal_config, build_inverse_lookup_array_linear_runtime_template)
        elif modal_kind == "lookup_array_spline":
            self._modify_lookup_array_like_block(item, modal_config, build_lookup_array_spline_runtime_template)
        elif modal_kind == "jmarti_line_emt":
            self._modify_jmarti_line_emt_block(item, modal_config)
        elif modal_kind == "source_emt":
            self._modify_source_emt_block(item, modal_config)
        elif modal_kind == "dc_source_emt":
            self._modify_dc_source_emt_block(item, modal_config)
        elif modal_kind == "balanced_source_emt":
            self._modify_balanced_source_emt_block(item, modal_config)
        elif modal_kind == "arbitrary_source_emt":
            self._modify_arbitrary_source_emt_block(item, modal_config)
        elif modal_kind == "transient_source_emt":
            self._modify_transient_source_emt_block(item, modal_config)
        elif modal_kind == "emt_phase_wizard":
            self._modify_emt_phase_wizard_block(item, modal_config)
        elif modal_kind == "lookup_matrix_linear":
            self._modify_lookup_matrix_like_block(item, modal_config, build_lookup_matrix_linear_runtime_template)
        elif modal_kind == "lookup_matrix_spline":
            self._modify_lookup_matrix_like_block(item, modal_config, build_lookup_matrix_spline_runtime_template)
        elif modal_kind == "grounding_link_emt":
            self._modify_grounding_link_emt_block(item, modal_config)
        elif modal_kind == "nonlinear_resistor_emt":
            self._modify_nonlinear_resistor_emt_block(item, modal_config)
        elif modal_kind == "load_topology_emt":
            self._modify_load_topology_emt_block(item, modal_config)
        elif modal_kind == "transformer_topology_emt":
            self._modify_transformer_topology_emt_block(item, modal_config)
        elif modal_kind == "shunt_component_emt":
            self._modify_shunt_component_emt_block(item, modal_config)
        elif modal_kind == "rlc_combo_emt":
            self._modify_rlc_combo_emt_block(item, modal_config)
        elif modal_kind == "induction_motor_emt":
            self._modify_induction_motor_emt_block(item, modal_config)
        elif modal_kind == "fault_emt":
            self._modify_fault_emt_block(item, modal_config)
        elif modal_kind == "switch_emt":
            self._modify_switch_emt_block(item, modal_config)
        else:
            pass

    def _replace_scene_block_from_template(self, item: BlockItem | GenericBlockItem, new_block: Block, modal_kind: str, modal_config: Dict[str, Any]) -> None:
        """
        Replace one scene block contents while preserving its identity and diagram node.

        :param item: Existing scene block item.
        :param new_block: Newly built block contents.
        :param modal_kind: Modal kind metadata key.
        :param modal_config: Modal configuration metadata.
        :return: None.
        """
        if item.subsys is None:
            return
        else:
            pass

        target_block: Block = item.subsys
        preserved_uid: int = target_block.uid
        preserved_diagram = target_block.diagram
        source_clone: Block = clone_block_for_editing(new_block)
        source_clone.uid = preserved_uid
        copy_block_state(source_block=source_clone, target_block=target_block)
        target_block.uid = preserved_uid

        if source_clone.diagram.node_data:
            target_block.diagram = source_clone.diagram
        else:
            target_block.diagram = preserved_diagram
        set_modal_template_metadata(target_block, modal_kind, modal_config)
        set_jmarti_block_fit_bundle(target_block, None)
        set_jmarti_block_runtime_data(target_block, None)

        if get_modal_template_metadata(source_clone)[0] == "jmarti_line_emt":
            set_jmarti_block_fit_bundle(target_block, get_jmarti_block_fit_bundle(source_clone))
            set_jmarti_block_runtime_data(target_block, get_jmarti_block_runtime_data(source_clone))
        else:
            pass

        self.rebuild_scene_from_diagram()
        self.select_block_by_uid(preserved_uid)
        self.mark_unapplied_changes()

    def _modify_lookup_array_like_block(self, item: BlockItem | GenericBlockItem, modal_config: Dict[str, Any], builder) -> None:
        """
        Reconfigure one modal-created 1D lookup block.

        :param item: Target block item.
        :param modal_config: Stored modal configuration.
        :param builder: Lookup builder callable.
        :return: None.
        """
        dialog = LookupArrayLinearDialog(
            block_label=str(modal_config["display_label"]),
            initial_points=list(zip(modal_config["x_points"], modal_config["y_points"])),
            parent=self,
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            x_points, y_points = dialog.get_points()
        else:
            return

        if item.subsys is None:
            return
        else:
            pass

        descriptor_key: str = str(modal_config["descriptor_key"])
        if builder is build_lookup_array_linear_runtime_template:
            new_block = builder(
                vf=self.var_factory,
                x_points=x_points,
                y_points=y_points,
                clip=descriptor_key not in {"lookup_array_linear_noclipping", "lookup_array_object_linear_noclipping"},
                name=item.subsys.name,
            ).block
        else:
            new_block = builder(
                vf=self.var_factory,
                x_points=x_points,
                y_points=y_points,
                name=item.subsys.name,
            ).block

        updated_config = dict(modal_config)
        updated_config["x_points"] = x_points
        updated_config["y_points"] = y_points
        self._replace_scene_block_from_template(item, new_block, str(get_modal_template_metadata(item.subsys)[0]), updated_config)

    def _modify_lookup_matrix_like_block(self, item: BlockItem | GenericBlockItem, modal_config: Dict[str, Any], builder) -> None:
        """
        Reconfigure one modal-created 2D lookup block.

        :param item: Target block item.
        :param modal_config: Stored modal configuration.
        :param builder: Lookup builder callable.
        :return: None.
        """
        dialog = LookupMatrixLinearDialog(
            block_label=str(modal_config["display_label"]),
            initial_x_points=modal_config["x_points"],
            initial_y_points=modal_config["y_points"],
            initial_z_matrix=modal_config["z_matrix"],
            parent=self,
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            x_points, y_points, z_matrix = dialog.get_matrix_data()
        else:
            return

        if item.subsys is None:
            return
        else:
            pass

        new_block = builder(
            vf=self.var_factory,
            x_points=x_points,
            y_points=y_points,
            z_matrix=z_matrix,
            name=item.subsys.name,
        ).block
        updated_config = dict(modal_config)
        updated_config["x_points"] = x_points
        updated_config["y_points"] = y_points
        updated_config["z_matrix"] = z_matrix
        self._replace_scene_block_from_template(item, new_block, str(get_modal_template_metadata(item.subsys)[0]), updated_config)

    def _modify_emt_phase_wizard_block(self, item: BlockItem | GenericBlockItem, modal_config: Dict[str, Any]) -> None:
        """
        Reconfigure one modal-created EMT phase-wizard block.

        :param item: Target block item.
        :param modal_config: Stored modal configuration.
        :return: None.
        """
        if str(modal_config.get("block_type", "")) == BlockType.EMT_JMARTI_LINE.name:
            migrated_config: Dict[str, Any] = self._build_default_jmarti_line_modal_config(
                phase_n=bool(modal_config.get("phase_n", False)),
                phase_a=bool(modal_config.get("phase_a", True)),
                phase_b=bool(modal_config.get("phase_b", True)),
                phase_c=bool(modal_config.get("phase_c", True)),
            )
            self._modify_jmarti_line_emt_block(item, migrated_config)
            return
        else:
            pass

        initial_values = (
            bool(modal_config.get("phase_n", False)),
            bool(modal_config.get("phase_a", True)),
            bool(modal_config.get("phase_b", True)),
            bool(modal_config.get("phase_c", True)),
        )
        dialog = EmtTemplateWizardDialog(self, initial_values=initial_values)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            phase_n, phase_a, phase_b, phase_c = dialog.get_values()
        else:
            return

        if item.subsys is None:
            return
        else:
            pass

        block_type_name: str = str(modal_config["block_type"])
        block_type = BlockType[block_type_name]

        if _get_shunt_component_kind(block_type) is not None:
            migrated_config: Dict[str, Any] = dict({
                "block_type": block_type.name,
                "phA": bool(modal_config.get("phase_a", True)),
                "phB": bool(modal_config.get("phase_b", True)),
                "phC": bool(modal_config.get("phase_c", True)),
                "connection_type": (
                    ShuntConnectionType.NeutralStar
                    if bool(modal_config.get("phase_n", False))
                    else ShuntConnectionType.GroundedStar
                ),
                "input_mode": "physical",
                "include_r": block_type == BlockType.R_LOAD_EMT,
                "include_l": block_type == BlockType.L_LOAD_EMT,
                "include_c": block_type == BlockType.C_LOAD_EMT,
                "resistance_ohm": 1.0,
                "inductive_value": 0.01,
                "capacitive_value": 1.0e-6,
            })
            self._modify_shunt_component_emt_block(item, migrated_config)
            return
        elif _is_load_topology_block_type(block_type):
            migrated_config = dict({
                "block_type": block_type.name,
                "phA": bool(modal_config.get("phase_a", True)),
                "phB": bool(modal_config.get("phase_b", True)),
                "phC": bool(modal_config.get("phase_c", True)),
                "connection_type": (
                    ShuntConnectionType.NeutralStar
                    if bool(modal_config.get("phase_n", False))
                    else ShuntConnectionType.GroundedStar
                ),
            })
            self._modify_load_topology_emt_block(item, migrated_config)
            return
        else:
            pass

        new_block = create_emt_wizard_block(
            phase_n,
            phase_a,
            phase_b,
            phase_c,
            self.var_factory,
            block_type=block_type,
            item_name=item.subsys.name,
        )

        if new_block is None:
            return
        else:
            pass

        updated_config = dict(modal_config)
        updated_config["phase_n"] = phase_n
        updated_config["phase_a"] = phase_a
        updated_config["phase_b"] = phase_b
        updated_config["phase_c"] = phase_c
        self._replace_scene_block_from_template(item, new_block, "emt_phase_wizard", updated_config)

    def _modify_jmarti_line_emt_block(self, item: BlockItem | GenericBlockItem, modal_config: Dict[str, Any]) -> None:
        """
        Reconfigure one modal-created EMT J_Marti line block.

        :param item: Target block item.
        :param modal_config: Stored modal configuration.
        :return: None.
        """
        dialog = JMartiLineEmtDialog(self, initial_config=modal_config)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_config, fit_bundle = self._apply_jmarti_line_fit_configuration(dialog.get_configuration())
        else:
            return

        if item.subsys is None:
            return
        else:
            pass

        phase_n, phase_a, phase_b, phase_c = self._extract_jmarti_phase_tuple(updated_config)
        new_block = create_emt_wizard_block(
            phase_n,
            phase_a,
            phase_b,
            phase_c,
            self.var_factory,
            block_type=BlockType.EMT_JMARTI_LINE,
            item_name=item.subsys.name,
        )

        if new_block is None:
            return
        else:
            pass

        set_jmarti_block_fit_bundle(new_block, fit_bundle)
        set_jmarti_block_runtime_data(new_block, None)
        self._replace_scene_block_from_template(item, new_block, "jmarti_line_emt", updated_config)

    def _modify_source_emt_block(self, item: BlockItem | GenericBlockItem, modal_config: Dict[str, Any]) -> None:
        """
        Reconfigure one modal-created EMT source block.

        :param item: Target block item.
        :param modal_config: Stored modal configuration.
        :return: None.
        """
        block_type: BlockType = BlockType[str(modal_config["block_type"])]
        dialog = SourceEmtDialog(block_type=block_type, parent=self, initial_config=modal_config)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_config: Dict[str, Any] = dict(self._build_default_source_emt_modal_config(block_type), **dialog.get_configuration(), block_type=block_type.name)
        else:
            return

        if item.subsys is None:
            return
        else:
            pass

        new_block: Block | None = self._build_source_emt_block_model(block_type=block_type, item_name=item.subsys.name, modal_config=updated_config)

        if new_block is None:
            return
        else:
            pass

        self._replace_scene_block_from_template(item, new_block, "source_emt", updated_config)

    def _modify_dc_source_emt_block(self, item: BlockItem | GenericBlockItem, modal_config: Dict[str, Any]) -> None:
        """
        Reconfigure one modal-created EMT DC source block.

        :param item: Target block item.
        :param modal_config: Stored modal configuration.
        :return: None.
        """
        block_type: BlockType = BlockType[str(modal_config["block_type"])]
        dialog = DcSourceEmtDialog(block_type=block_type, parent=self, initial_config=modal_config)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_config: Dict[str, Any] = dict(self._build_default_dc_source_emt_modal_config(block_type), **dialog.get_configuration(), block_type=block_type.name)
        else:
            return

        if item.subsys is None:
            return
        else:
            pass

        new_block: Block | None = self._build_dc_source_emt_block_model(block_type=block_type, item_name=item.subsys.name, modal_config=updated_config)

        if new_block is None:
            return
        else:
            pass

        self._replace_scene_block_from_template(item, new_block, "dc_source_emt", updated_config)

    def _modify_balanced_source_emt_block(self, item: BlockItem | GenericBlockItem, modal_config: Dict[str, Any]) -> None:
        """
        Reconfigure one modal-created balanced EMT source block.

        :param item: Target block item.
        :param modal_config: Stored modal configuration.
        :return: None.
        """
        block_type: BlockType = BlockType[str(modal_config["block_type"])]
        dialog = BalancedSourceEmtDialog(block_type=block_type, parent=self, initial_config=modal_config)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_config: Dict[str, Any] = dict(self._build_default_balanced_source_emt_modal_config(block_type), **dialog.get_configuration(), block_type=block_type.name)
        else:
            return

        if item.subsys is None:
            return
        else:
            pass

        new_block: Block | None = self._build_balanced_source_emt_block_model(block_type=block_type, item_name=item.subsys.name, modal_config=updated_config)

        if new_block is None:
            return
        else:
            pass

        self._replace_scene_block_from_template(item, new_block, "balanced_source_emt", updated_config)

    def _modify_arbitrary_source_emt_block(self, item: BlockItem | GenericBlockItem, modal_config: Dict[str, Any]) -> None:
        """
        Reconfigure one modal-created arbitrary-waveform EMT source block.

        :param item: Target block item.
        :param modal_config: Stored modal configuration.
        :return: None.
        """
        block_type: BlockType = BlockType[str(modal_config["block_type"])]
        dialog = ArbitrarySourceEmtDialog(block_type=block_type, parent=self, initial_config=modal_config)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_config: Dict[str, Any] = dict(self._build_default_arbitrary_source_emt_modal_config(block_type), **dialog.get_configuration(), block_type=block_type.name)
        else:
            return

        if item.subsys is None:
            return
        else:
            pass

        new_block: Block | None = self._build_arbitrary_source_emt_block_model(block_type=block_type, item_name=item.subsys.name, modal_config=updated_config)

        if new_block is None:
            return
        else:
            pass

        self._replace_scene_block_from_template(item, new_block, "arbitrary_source_emt", updated_config)

    def _modify_transient_source_emt_block(self, item: BlockItem | GenericBlockItem, modal_config: Dict[str, Any]) -> None:
        """
        Reconfigure one modal-created transient EMT source block.

        :param item: Target block item.
        :param modal_config: Stored modal configuration.
        :return: None.
        """
        block_type: BlockType = BlockType[str(modal_config["block_type"])]
        dialog = TransientSourceEmtDialog(block_type=block_type, parent=self, initial_config=modal_config)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_config: Dict[str, Any] = dict(self._build_default_transient_source_emt_modal_config(block_type), **dialog.get_configuration(), block_type=block_type.name)
        else:
            return

        if item.subsys is None:
            return
        else:
            pass

        new_block: Block | None = self._build_transient_source_emt_block_model(block_type=block_type, item_name=item.subsys.name, modal_config=updated_config)

        if new_block is None:
            return
        else:
            pass

        self._replace_scene_block_from_template(item, new_block, "transient_source_emt", updated_config)

    def _modify_switch_emt_block(self, item: BlockItem | GenericBlockItem, modal_config: Dict[str, Any]) -> None:
        """
        Reconfigure one modal-created EMT switch block.

        :param item: Target block item.
        :param modal_config: Stored modal configuration.
        :return: None.
        """
        dialog = SwitchEmtDialog(self, initial_config=modal_config)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            switch_config = dialog.get_switch_configuration()
        else:
            return

        if item.subsys is None:
            return
        else:
            pass

        new_block = get_switch_emt_template(vf=self.var_factory, name=item.subsys.name, **switch_config).block
        self._replace_scene_block_from_template(item, new_block, "switch_emt", dict(switch_config))

    def _modify_fault_emt_block(self, item: BlockItem | GenericBlockItem, modal_config: Dict[str, Any]) -> None:
        """
        Reconfigure one modal-created EMT fault block.

        :param item: Target block item.
        :param modal_config: Stored modal configuration.
        :return: None.
        """
        initial_fault_config: Dict[str, Any] = self._build_default_fault_emt_modal_config()
        initial_fault_config.update(modal_config)
        dialog = FaultEmtDialog(self, initial_config=initial_fault_config)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            fault_config: Dict[str, Any] = self._build_default_fault_emt_modal_config()
            fault_config.update(dialog.get_configuration())
        else:
            return

        if item.subsys is None:
            return
        else:
            pass

        new_block = get_fault_emt_template(
            vf=self.var_factory,
            fault_type=fault_config["fault_type"],
            placement_side=fault_config["placement_side"],
            phA=bool(fault_config["phA"]),
            phB=bool(fault_config["phB"]),
            phC=bool(fault_config["phC"]),
            signal_controlled=bool(fault_config["signal_controlled"]),
            initial_closed=bool(fault_config["initial_closed"]),
            fault_resistance=float(fault_config["fault_resistance"]),
            ground_resistance=float(fault_config["ground_resistance"]),
            open_conductance=float(fault_config["open_conductance"]),
            fault_time_constant=float(fault_config["fault_time_constant"]),
            command_threshold=float(fault_config["command_threshold"]),
            name=item.subsys.name,
        ).block
        self._replace_scene_block_from_template(item, new_block, "fault_emt", dict(fault_config))

    def _modify_rlc_combo_emt_block(self, item: BlockItem | GenericBlockItem, modal_config: Dict[str, Any]) -> None:
        """
        Reconfigure one modal-created EMT combined RLC shunt block.

        :param item: Target block item.
        :param modal_config: Stored modal configuration.
        :return: None.
        """
        dialog = self._build_rlc_combo_emt_dialog(initial_config=modal_config)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            rlc_config = dialog.get_configuration()
        else:
            return

        try:
            template_kwargs = self._build_rlc_combo_emt_template_kwargs(rlc_config)
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "RLC Combo", str(exc))
            return

        if item.subsys is None:
            return
        else:
            pass

        # The dynamic editor must not overwrite the static injection
        # connection. The EMT block stores its own symbolic topology.
        if isinstance(self.api_object, InjectionParent):
            pass
        else:
            pass

        new_block = get_shunt_rlc_combo_emt_template(vf=self.var_factory, name=item.subsys.name, **template_kwargs).block
        self._annotate_internal_grounding_link_blocks(new_block)
        self._replace_scene_block_from_template(item, new_block, "rlc_combo_emt", dict(rlc_config))

    def _modify_induction_motor_emt_block(self, item: BlockItem | GenericBlockItem, modal_config: Dict[str, Any]) -> None:
        """
        Reconfigure one modal-created induction-motor EMT block.

        :param item: Target block item.
        :param modal_config: Stored modal configuration.
        :return: None.
        """
        # Reopen the same modal with the stored configuration so template edits use
        # the exact persisted state instead of inferring anything from the block.
        dialog: InductionMotorEmtDialog = self._build_induction_motor_emt_dialog(initial_config=modal_config)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            induction_motor_config: Dict[str, Any] = dialog.get_configuration()
        else:
            return

        if item.subsys is None:
            return
        else:
            pass

        new_block: Block = self._build_induction_motor_emt_block_model(
            item_name=item.subsys.name,
            modal_config=induction_motor_config,
        )
        self._replace_scene_block_from_template(item, new_block, "induction_motor_emt", dict(induction_motor_config))

    def _modify_grounding_link_emt_block(self, item: BlockItem | GenericBlockItem, modal_config: Dict[str, Any]) -> None:
        """
        Reconfigure one modal-created EMT grounding-link block.

        :param item: Target block item.
        :param modal_config: Stored modal configuration.
        :return: None.
        """
        dialog = self._build_grounding_link_emt_dialog(initial_config=modal_config)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            grounding_config = dialog.get_configuration()
        else:
            return

        try:
            template_kwargs = self._build_grounding_link_emt_template_kwargs(grounding_config)
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "Grounding Link", str(exc))
            return

        if item.subsys is None:
            return
        else:
            pass

        nested_variant: bool = len(item.subsys.external_mapping) == 0
        new_block = get_grounding_link_emt_template(
            vf=self.var_factory,
            name=item.subsys.name,
            nested=nested_variant,
            **template_kwargs,
        ).block
        self._replace_scene_block_from_template(item, new_block, "grounding_link_emt", dict(grounding_config))

    def _modify_nonlinear_resistor_emt_block(self, item: BlockItem | GenericBlockItem, modal_config: Dict[str, Any]) -> None:
        """
        Reconfigure one modal-created nonlinear resistor EMT block.

        :param item: Target block item.
        :param modal_config: Stored modal configuration.
        :return: None.
        """
        initial_points = list(zip(
            list(float(value) for value in modal_config.get("voltage_points", [0.0, 1.0, 2.0])),
            list(float(value) for value in modal_config.get("current_points", [0.0, 10.0, 20.0])),
        ))
        dialog = LookupArrayLinearDialog(
            block_label="Nonlinear resistor EMT V-I curve",
            initial_points=initial_points,
            parent=self,
            x_label="V",
            y_label="I",
            preview_enabled=True,
            preview_title="Nonlinear resistor EMT V-I curve",
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            voltage_points, current_points = dialog.get_points()
        else:
            return

        if item.subsys is None:
            return
        else:
            pass

        new_block = get_nonlinear_resistor_emt_template(
            vf=self.var_factory,
            voltage_points=voltage_points,
            current_points=current_points,
            name=item.subsys.name,
        ).block
        self._replace_scene_block_from_template(
            item,
            new_block,
            "nonlinear_resistor_emt",
            dict({
                "voltage_points": voltage_points,
                "current_points": current_points,
            }),
        )

    def _modify_load_topology_emt_block(self, item: BlockItem | GenericBlockItem, modal_config: Dict[str, Any]) -> None:
        """
        Reconfigure one modal-created EMT load-topology block.

        :param item: Target block item.
        :param modal_config: Stored modal configuration.
        :return: None.
        """
        block_type_name: str = str(modal_config.get("block_type", ""))
        block_type: BlockType = BlockType[block_type_name]
        dialog = self._build_load_topology_emt_dialog(block_type=block_type, initial_config=modal_config)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            load_config = dialog.get_configuration()
        else:
            return

        if item.subsys is None:
            return
        else:
            pass

        new_block = self._build_load_topology_emt_block_model(
            block_type=block_type,
            item_name=item.subsys.name,
            modal_config=load_config,
        )
        if new_block is None:
            return
        else:
            pass

        self._annotate_internal_grounding_link_blocks(new_block)

        # The dynamic editor must not overwrite the static load connection.
        if isinstance(self.api_object, InjectionParent):
            pass
        else:
            pass

        self._replace_scene_block_from_template(
            item,
            new_block,
            "load_topology_emt",
            dict(load_config, block_type=block_type.name),
        )

    def _modify_transformer_topology_emt_block(self, item: BlockItem | GenericBlockItem, modal_config: Dict[str, Any]) -> None:
        """
        Reconfigure one modal-created EMT transformer block.

        :param item: Target block item.
        :param modal_config: Stored modal configuration.
        :return: None.
        """
        block_type_name: str = str(modal_config.get("block_type", ""))
        block_type: BlockType = BlockType[block_type_name]
        topology_config: Dict[str, Any] | None = self._resolve_transformer_topology_configuration()

        if topology_config is None:
            dialog = self._build_transformer_topology_emt_dialog(block_type=block_type, initial_config=modal_config)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                topology_config = dialog.get_configuration()
                topology_config["allow_modify_template"] = True
            else:
                return
        else:
            topology_config = dict(topology_config)

        if item.subsys is None:
            return
        else:
            pass

        # The dynamic editor must not overwrite the static transformer winding
        # connection stored by the network object.
        if isinstance(self.api_object, BranchParent):
            pass
        else:
            pass

        new_block = self._build_transformer_topology_emt_block_model(
            block_type=block_type,
            item_name=item.subsys.name,
            modal_config=topology_config,
        )
        if new_block is None:
            return
        else:
            pass

        self._replace_scene_block_from_template(
            item,
            new_block,
            "transformer_topology_emt",
            dict(topology_config, block_type=block_type.name),
        )

    def _modify_shunt_component_emt_block(self, item: BlockItem | GenericBlockItem, modal_config: Dict[str, Any]) -> None:
        """
        Reconfigure one modal-created simple EMT shunt block.

        :param item: Target block item.
        :param modal_config: Stored modal configuration.
        :return: None.
        """
        block_type_name: str = str(modal_config.get("block_type", ""))
        block_type: BlockType = BlockType[block_type_name]
        dialog = self._build_shunt_component_emt_dialog(block_type=block_type, initial_config=modal_config)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            shunt_config = dialog.get_configuration()
        else:
            return

        try:
            template_kwargs = self._build_shunt_component_emt_template_kwargs(block_type=block_type, modal_config=shunt_config)
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "EMT Shunt", str(exc))
            return

        if item.subsys is None:
            return
        else:
            pass

        # The dynamic editor must not overwrite the static injection
        # connection. The EMT block stores its own symbolic topology.
        if isinstance(self.api_object, InjectionParent):
            pass
        else:
            pass

        new_block = get_shunt_rlc_combo_emt_template(vf=self.var_factory, name=item.subsys.name, **template_kwargs).block
        self._annotate_internal_grounding_link_blocks(new_block)
        self._replace_scene_block_from_template(
            item,
            new_block,
            "shunt_component_emt",
            dict(shunt_config, block_type=block_type.name),
        )

    def get_scene_item_by_block_uid(self, block_uid: int) -> BlockItem | GenericBlockItem | None:
        """
        Find the visible scene item representing a block uid.

        :param block_uid:
        :return:
        """
        item: QGraphicsItem

        for item in self.scene.items():
            if isinstance(item, (BlockItem, GenericBlockItem)) and item.subsys is not None:
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
        item: BlockItem | GenericBlockItem | None = self.get_scene_item_by_block_uid(block_uid)

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

    def _validate_variable_initialization(self, section: ValidationSection, traversal_nodes: list[ValidationTraversalNode]) -> None:
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

                    phase_name: str
                    phase_missing_messages: list[str]
                    for phase_name, phase_missing_messages in emt_missing_by_phase.items():
                        if phase_missing_messages:
                            phase_total_ports: int = phase_total_ports_by_name[phase_name]
                            phase_missing_count: int = len(phase_missing_messages)
                            if phase_total_ports > 0 and phase_missing_count < phase_total_ports:
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

                if missing_input_names or missing_output_names:
                    add_validation_detail(
                        section=section,
                        block_label=node.name,
                        detail=format_missing_port_detail(
                            input_names=missing_input_names,
                            output_names=missing_output_names,
                        ),
                    )
                else:
                    pass

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

    def rebuild_scene_from_diagram(self) -> None:
        """
        Rebuild the visible scene from the persisted block diagram.

        :return:
        """
        uid_to_blockitem: Dict[int, BlockItem | GenericBlockItem | GenericBlockItem] = dict()
        uid: int
        node: Any
        con: Any

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
                    block_item: ProtectedConnectionBlockItem = ProtectedConnectionBlockItem(
                        var_factory=self.var_factory,
                        name=node.name,
                    )
                    block_item.set_subsystem(block_model)
                    block_item.position_changed_callback = self._build_position_changed_callback(block_model.uid)
                    block_item.build_item()

                    modal_kind, modal_config = get_modal_template_metadata(block_model)
                    if modal_kind == "jmarti_line_emt" and modal_config is not None:
                        block_item.setToolTip(self._build_jmarti_modal_tooltip(modal_config))
                    elif modal_kind == "source_emt" and modal_config is not None:
                        block_item.setToolTip(self._build_source_emt_modal_tooltip(modal_config))
                    elif modal_kind == "dc_source_emt" and modal_config is not None:
                        block_item.setToolTip(self._build_dc_source_emt_modal_tooltip(modal_config))
                    elif modal_kind == "balanced_source_emt" and modal_config is not None:
                        block_item.setToolTip(self._build_balanced_source_emt_modal_tooltip(modal_config))
                    elif modal_kind == "arbitrary_source_emt" and modal_config is not None:
                        block_item.setToolTip(self._build_arbitrary_source_emt_modal_tooltip(modal_config))
                    elif modal_kind == "transient_source_emt" and modal_config is not None:
                        block_item.setToolTip(self._build_transient_source_emt_modal_tooltip(modal_config))
                    elif modal_kind == "induction_motor_emt" and modal_config is not None:
                        block_item.setToolTip(self._build_induction_motor_emt_modal_tooltip(modal_config))
                    elif modal_kind == "fault_emt" and modal_config is not None:
                        block_item.setToolTip(self._build_fault_emt_modal_tooltip(modal_config))
                    else:
                        pass

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
                        item = PairedItem(
                            var_factory=self.var_factory,
                            subsys=block_model,
                            api_object=self.api_object,
                            mode=self.mode,
                            name=block_model.name,
                            position_changed_callback=self._build_position_changed_callback(block_model.uid)
                        )
                        suffix = block_model.name.replace("From_", "").replace("To_", "")
                        if node.tpe == "signal_in":
                            signal_in_items[suffix] = item
                        else:
                            signal_out_items[suffix] = item
                    else:
                        item = GenericBlockItem(
                            var_factory=self.var_factory,
                            subsys=block_model,
                            api_object=self.api_object,
                            mode=self.mode,
                            name=block_model.name,
                            position_changed_callback=self._build_position_changed_callback(block_model.uid)
                        )
                    self.scene.addItem(item)
                    item.setPos(QPointF(node.x, node.y))
                    modal_kind, modal_config = get_modal_template_metadata(block_model)
                    if modal_kind == "jmarti_line_emt" and modal_config is not None:
                        item.setToolTip(self._build_jmarti_modal_tooltip(modal_config))
                    elif modal_kind == "source_emt" and modal_config is not None:
                        item.setToolTip(self._build_source_emt_modal_tooltip(modal_config))
                    elif modal_kind == "dc_source_emt" and modal_config is not None:
                        item.setToolTip(self._build_dc_source_emt_modal_tooltip(modal_config))
                    elif modal_kind == "balanced_source_emt" and modal_config is not None:
                        item.setToolTip(self._build_balanced_source_emt_modal_tooltip(modal_config))
                    elif modal_kind == "arbitrary_source_emt" and modal_config is not None:
                        item.setToolTip(self._build_arbitrary_source_emt_modal_tooltip(modal_config))
                    elif modal_kind == "transient_source_emt" and modal_config is not None:
                        item.setToolTip(self._build_transient_source_emt_modal_tooltip(modal_config))
                    elif modal_kind == "induction_motor_emt" and modal_config is not None:
                        item.setToolTip(self._build_induction_motor_emt_modal_tooltip(modal_config))
                    elif modal_kind == "fault_emt" and modal_config is not None:
                        item.setToolTip(self._build_fault_emt_modal_tooltip(modal_config))
                    else:
                        pass
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
                    elbow_points: List[QPointF] = [QPointF(x, y) for x, y in con.elbow_points] if con.elbow_points else []
                    connection: ConnectionItem = ConnectionItem(
                        src_port, dst_port,
                        diagram=self.diagram,
                        con_uid=uid,
                        elbow_points=elbow_points
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
        self.has_unapplied_changes = True
        self.changes_applied = False
        self.dirtyStateChanged.emit(True)

    def get_dynamic_editor_display_title(self) -> str:
        """
        Return the user-facing title for this editor instance.
        """

        object_name = self.api_object.name if self.api_object is not None else "Dynamic object"
        return f"{object_name} [{self.mode.name}]"

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
            self.ui.toolBox.currentChanged.disconnect(self.on_side_panel_page_changed)
        except (RuntimeError, TypeError):
            pass

        try:
            self.scene.selectionChanged.disconnect(self.on_scene_selection_changed)
        except (RuntimeError, TypeError):
            pass

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Close the editor. Ask for confirmation when there are unapplied changes.

        :param event:
        :return:
        """
        if self.can_close_editor(self):
            self.disconnect_editor_signals()
            event.accept()
        else:
            event.ignore()

    def graphicsDragEnterEvent(self, event: QDragEnterEvent) -> None:
        """
        Validate whether the drag entering the graphics view contains a block entry.

        :param event:
        :return:
        """
        payload: BlockType | BasicBlockTemplateDescriptor | RmsModelTemplate | EmtModelTemplate | FmuTemplate | SignalPairPayload | None = self.get_library_payload_from_mime_data(
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
        payload: BlockType | BasicBlockTemplateDescriptor | RmsModelTemplate | EmtModelTemplate | FmuTemplate | SignalPairPayload | None = self.get_library_payload_from_mime_data(
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
        payload: BlockType | BasicBlockTemplateDescriptor | RmsModelTemplate | EmtModelTemplate | FmuTemplate | SignalPairPayload | None = self.get_library_payload_from_mime_data(
            event.mimeData()
        )
        scene_position: QtCore.QPointF = self.ui.graphicsView.mapToScene(
            int(event.position().x()),
            int(event.position().y())
        )
        block_item: BlockItem | None | GenericBlockItem

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
    )
    window.show()
    app.exec_()
