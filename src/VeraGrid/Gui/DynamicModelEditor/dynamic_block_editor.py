# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
import copy
from typing import List, Dict, Optional, Any, Tuple
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import (QGraphicsItem, QMenu, QDialog, QVBoxLayout, QDialogButtonBox, QLineEdit)
from PySide6.QtGui import (QAction, QDropEvent, QDragEnterEvent, QDragMoveEvent)
from PySide6.QtCore import Qt, QPointF, Signal

from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_graphics import PairedItem
from VeraGridEngine.Devices.Parents.branch_parent import BranchParent

from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType, ParamPowerFlowReferenceType, \
    DynamicSimulationMode, DynamicTableModelMode, DynEditorGraphicsModes
from VeraGridEngine.Utils.Symbolic.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.bus_emt_template import get_bus_emt_algebraic_vars
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Dynamic.var_factory import Connection, VarFactory
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.fmu_template import FmuTemplate
from VeraGridEngine.Templates.BasicBlockCatalog.predefined_blocks import signal_pair
from VeraGridEngine.Templates.BasicBlockCatalog import BasicBlockTemplateDescriptor

from VeraGridEngine.Templates.BasicBlockCatalog import load_basic_block_catalog_template

import VeraGridEngine.Templates.BasicBlockCatalog as BasicBlockTemplates
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Utils.Symbolic.block import (Block,
                                                 DynamicConnectionIntentOrigin,
                                                 build_dynamic_connection_intent_record,
                                                 find_connections,
                                                 find_matching_dynamic_connection_intent,
                                                 normalize_dynamic_connection_intents,
                                                 rehash_block_tree_var_keyed_dicts)
from VeraGrid.Gui.DynamicModelEditor.block_editor import Ui_BlockEditorWindow
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_dialogs import AddBlockVariableDialog, AddEquationDialog, \
    AddParameterDialog, ExpressionTextEditorDialog, GenericBlockDialog
import VeraGrid.Gui.DynamicModelEditor.dynamic_editor_graphics as graph
from VeraGrid.Session.dynamic_editor_entries import DynamicEditorEntry
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_library import DynamicEditorLibrary, LibraryTreeFilterProxyModel
import VeraGrid.Gui.DynamicModelEditor.dynamic_editor_models as dialog_models
import VeraGrid.Gui.DynamicModelEditor.dynamic_editor_validation as valid
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_utilities import create_block_of_type, create_generic_block, get_blocktype2template_builder_dict

from VeraGrid.Gui.messages import yes_no_question
from VeraGrid.Gui.toast_widget import ToastManager
from VeraGridEngine.Utils.Symbolic.symbolic import (
    BinOp, Comparison, Const, Expr, Func, Func2, UnOp, Var,
    string_to_symbolic, symbolic_to_string,
)
from VeraGridEngine.Utils.Symbolic.symbolic_io import duplicate_block
from VeraGridEngine.Utils.Symbolic.bus_rms_template import get_bus_rms_algebraic_vars
from VeraGridEngine.Utils.SugiyamaLayered import (
    SugiyamaEdge,
    SugiyamaGraph,
    SugiyamaLayeredPythonEngine,
    SugiyamaNode,
    SugiyamaPort,
)
from VeraGrid.Gui.DynamicModelEditor.dyn_template_editor_dialogue import DynTemplatesEditorDialog
from VeraGrid.Gui.DynamicModelEditor.RoutingQt import QtRoutingSession
from VeraGridEngine.enumerations import BlockType, RoutingAxis
from VeraGridEngine.Devices.Diagrams.block_diagram import (
    BlockDiagram, BlockDiagramConnection, BlockDiagramNode,
)
from dataclasses import dataclass
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_graphics import GenericBlockItem


@dataclass
class ConnectionVarSpec:
    """
    Specification of one connection variable exposed by the block editor.
    """
    direction: str
    reference: VarPowerFlowReferenceType
    visible_name: str


def _disconnect_qt_signal(signal_obj: Any, slot: Any) -> None:
    """
    Disconnect one Qt signal/slot pair while tolerating already-cleared state.

    Dynamic editor teardown runs along several paths: navigation replacement,
    tab close, workspace close, and window close. Some of those paths can call
    cleanup after Qt has already removed part of the object tree, so signal
    disconnects must be best-effort instead of fatal.

    :param signal_obj: Qt signal object.
    :param slot: Connected slot callable.
    :return: None.
    """
    try:
        signal_obj.disconnect(slot)
    except (RuntimeError, TypeError):
        pass


def _dispose_layout_widget(layout: QtWidgets.QLayout | None, widget: QtWidgets.QWidget | None) -> None:
    """
    Detach and queue one child widget for Qt-side destruction.

    The editor creates several helper widgets dynamically and inserts them into
    existing layouts. Removing them from the layout and parent tree before
    ``deleteLater()`` reduces the chance of stale C++ widgets surviving until
    Python wrapper finalization.

    :param layout: Layout that currently hosts the widget.
    :param widget: Widget to remove.
    :return: None.
    """
    if layout is not None and widget is not None:
        layout.removeWidget(widget)
        widget.setParent(None)
        widget.deleteLater()
    else:
        pass


def _clear_table_view_model(view: QtWidgets.QAbstractItemView | None) -> None:
    """
    Clear the installed model from one item view.

    Detaching the model breaks Qt ownership chains between the view, proxy,
    source model, and editors before the view subtree is deleted.

    :param view: View whose model should be cleared.
    :return: None.
    """
    if view is not None:
        view.setModel(None)
    else:
        pass


def _dispose_qobject(obj: QtCore.QObject | None) -> None:
    """
    Detach one QObject from its parent and queue it for deletion.

    :param obj: QObject to dispose.
    :return: None.
    """
    if obj is not None:
        obj.setParent(None)
        obj.deleteLater()
    else:
        pass


def _dispose_dynamic_editor_library(library: DynamicEditorLibrary | None) -> None:
    """
    Dispose the Qt model owned by one dynamic-editor library wrapper.

    ``DynamicEditorLibrary`` is a plain Python object, not a ``QObject``. Its
    source tree model is the Qt-owned resource that needs explicit teardown.

    :param library: Library wrapper to dispose.
    :return: None.
    """
    if library is not None:
        _dispose_qobject(library.library_model)
    else:
        pass


def _detach_runtime_view_event_handlers(view: graph.GraphicsView | None) -> None:
    """
    Remove event handlers assigned directly to the runtime graphics view.

    Assigning bound editor methods to a Qt widget instance creates a Python
    reference from the child view back to its owning editor.  Remove those
    attributes before queuing the view for deletion so the editor/view cycle
    cannot outlive the C++ widget.

    :param view: Runtime graphics view being dismantled.
    :return: None.
    """
    if view is None:
        return

    handler_name: str
    for handler_name in ("dragEnterEvent", "dragMoveEvent", "dropEvent"):
        try:
            delattr(view, handler_name)
        except (AttributeError, RuntimeError):
            pass

def vars_match_for_visible_connection(
        left_var: Var | None,
        right_var: Var | None,
) -> bool:
    """
    Return whether two port variables represent the same visible connection.

    The mutable UID identifies an active alias. The non-mutable UID preserves
    logical identity across save and reopen. Shared and network references are
    compatibility fallbacks for older persisted models.

    :param left_var: First visible port variable.
    :param right_var: Second visible port variable.
    :return: ``True`` when both variables represent one visible connection.
    """
    if left_var is None or right_var is None:
        return False
    elif left_var.uid == right_var.uid:
        return True
    elif left_var.non_mutable_uid == right_var.non_mutable_uid:
        return True
    elif left_var.shared_ref is not None and left_var.shared_ref == right_var.shared_ref:
        return True
    elif (left_var.ref is not None
          and left_var.ref == right_var.ref
          and left_var.network_conn
          and right_var.network_conn):
        return True
    else:
        return False


def append_var_to_stable_index(
        var: Var | None,
        vars_by_uid: Dict[int, List[Var]],
        seen_object_ids: set[int],
) -> None:
    """
    Add one live variable object to the stable-identity lookup table.

    Object identity prevents repeated indexing when the same variable is
    referenced by several block containers. Differential links are followed
    explicitly because they are part of the symbolic variable identity chain.

    :param var: Variable to index, or ``None``.
    :param vars_by_uid: Lookup keyed by ``non_mutable_uid``.
    :param seen_object_ids: Python object identities already indexed.
    :return: None.
    """
    if var is None:
        pass
    else:
        object_id: int = id(var)
        if object_id in seen_object_ids:
            pass
        else:
            seen_object_ids.add(object_id)
            matching_vars: List[Var] | None = vars_by_uid.get(var.non_mutable_uid, None)
            if matching_vars is None:
                matching_vars = list()
                vars_by_uid[var.non_mutable_uid] = matching_vars
            else:
                pass

            matching_vars.append(var)
            append_var_to_stable_index(
                var=var.base_var,
                vars_by_uid=vars_by_uid,
                seen_object_ids=seen_object_ids,
            )
            append_var_to_stable_index(
                var=var.diff_var,
                vars_by_uid=vars_by_uid,
                seen_object_ids=seen_object_ids,
            )


def index_expression_vars(
        expression: Expr | Comparison | None,
        vars_by_uid: Dict[int, List[Var]],
        seen_object_ids: set[int],
) -> None:
    """
    Index variables contained in one known symbolic expression node.

    The traversal is explicit over the symbolic expression classes. This keeps
    the supported expression graph visible and avoids runtime reflection while
    still finding detached variables embedded in equations after reopening.

    :param expression: Symbolic expression or comparison to inspect.
    :param vars_by_uid: Lookup keyed by ``non_mutable_uid``.
    :param seen_object_ids: Python object identities already indexed.
    :return: None.
    """
    if expression is None:
        pass
    elif isinstance(expression, Var):
        append_var_to_stable_index(
            var=expression,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )
    elif isinstance(expression, BinOp):
        index_expression_vars(
            expression=expression.left,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )
        index_expression_vars(
            expression=expression.right,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )
    elif isinstance(expression, UnOp):
        index_expression_vars(
            expression=expression.operand,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )
    elif isinstance(expression, Func):
        index_expression_vars(
            expression=expression.arg,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )
    elif isinstance(expression, Func2):
        index_expression_vars(
            expression=expression.arg1,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )
        index_expression_vars(
            expression=expression.arg2,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )
    elif isinstance(expression, Comparison):
        index_expression_vars(
            expression=expression.lhs,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )
        if isinstance(expression.rhs, Expr):
            index_expression_vars(
                expression=expression.rhs,
                vars_by_uid=vars_by_uid,
                seen_object_ids=seen_object_ids,
            )
        else:
            pass
    else:
        pass


def index_block_vars(
        block_model: Block,
        vars_by_uid: Dict[int, List[Var]],
        seen_object_ids: set[int],
) -> None:
    """
    Index every explicitly owned variable and equation of one symbolic block.

    :param block_model: Block whose symbolic content must be indexed.
    :param vars_by_uid: Lookup keyed by ``non_mutable_uid``.
    :param seen_object_ids: Python object identities already indexed.
    :return: None.
    """
    variable_groups: tuple[List[Var], ...] = (
        block_model.state_vars,
        block_model.algebraic_vars,
        block_model.diff_vars,
        block_model.reformulated_vars,
        block_model.in_vars,
        block_model.out_vars,
    )
    expression_groups: tuple[List[Expr], ...] = (
        block_model.state_eqs,
        block_model.algebraic_eqs,
        block_model.differential_eqs,
    )
    variable_group: List[Var]
    expression_group: List[Expr]
    var: Var
    expression: Expr
    inequality: Expr | Comparison

    # Index variables declared directly by the block before traversing equations.
    for variable_group in variable_groups:
        for var in variable_group:
            append_var_to_stable_index(
                var=var,
                vars_by_uid=vars_by_uid,
                seen_object_ids=seen_object_ids,
            )

    # Equations can contain detached variables that are not present in a public
    # variable list, so each supported expression tree is traversed explicitly.
    for expression_group in expression_groups:
        for expression in expression_group:
            index_expression_vars(
                expression=expression,
                vars_by_uid=vars_by_uid,
                seen_object_ids=seen_object_ids,
            )

    for inequality in block_model.inequalities:
        index_expression_vars(
            expression=inequality,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )

    parameter_var: Var
    parameter_expression: Expr
    for parameter_var, parameter_expression in block_model.parameters.items():
        append_var_to_stable_index(
            var=parameter_var,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )
        index_expression_vars(
            expression=parameter_expression,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )

    initial_var: Var
    initial_expression: Expr
    for initial_var, initial_expression in block_model.init_values.items():
        append_var_to_stable_index(
            var=initial_var,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )
        index_expression_vars(
            expression=initial_expression,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )

    equation_var: Var
    equation_expression: Expr
    for equation_var, equation_expression in block_model.init_eqs.items():
        append_var_to_stable_index(
            var=equation_var,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )
        index_expression_vars(
            expression=equation_expression,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )

    for equation_var, equation_expression in block_model.diff_init_eqs.items():
        append_var_to_stable_index(
            var=equation_var,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )
        index_expression_vars(
            expression=equation_expression,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )

    for equation_var, equation_expression in block_model.discrete_eqs.items():
        append_var_to_stable_index(
            var=equation_var,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )
        index_expression_vars(
            expression=equation_expression,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )

    for equation_var, equation_expression in block_model.event_dict.items():
        append_var_to_stable_index(
            var=equation_var,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )
        index_expression_vars(
            expression=equation_expression,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )

    for equation_var, equation_expression in block_model.mode_dict.items():
        append_var_to_stable_index(
            var=equation_var,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )
        index_expression_vars(
            expression=equation_expression,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )

    guard_var: Var
    guard_expression: Expr | Comparison
    for guard_var, guard_expression in block_model.boolean_guards.items():
        append_var_to_stable_index(
            var=guard_var,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )
        index_expression_vars(
            expression=guard_expression,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )

    # Mapping values can carry aliases that are absent from normal variable lists.
    mapped_var: Var | None
    for mapped_var in block_model.external_mapping.values():
        append_var_to_stable_index(
            var=mapped_var,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )

    for mapped_var in block_model.api_obj_mapping.values():
        append_var_to_stable_index(
            var=mapped_var,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )

    for mapped_var in block_model.var_mapping.values():
        append_var_to_stable_index(
            var=mapped_var,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )


def build_working_var_index(root_block: Block) -> Dict[int, List[Var]]:
    """
    Build a stable-identity lookup for all live variables in one block tree.

    :param root_block: Root of the edited working block tree.
    :return: Variables grouped by ``non_mutable_uid``.
    """
    vars_by_uid: Dict[int, List[Var]] = dict()
    seen_object_ids: set[int] = set()
    block_model: Block

    for block_model in root_block.get_all_blocks():
        index_block_vars(
            block_model=block_model,
            vars_by_uid=vars_by_uid,
            seen_object_ids=seen_object_ids,
        )

    return vars_by_uid


def get_single_interface_var(block_model: Block | None) -> Var | None:
    """
    Return the single variable carried by one root-interface wrapper block.

    :param block_model: Candidate wrapper block.
    :return: Wrapped variable, or ``None`` for an invalid wrapper shape.
    """
    if block_model is None:
        return None
    elif len(block_model.in_vars) == 1 and len(block_model.out_vars) == 0:
        if block_model.in_vars[0].ref is not None and len(block_model.algebraic_vars) == 0 and len(block_model.state_vars) == 0:
            return block_model.in_vars[0]
        else:
            return None
    elif len(block_model.in_vars) == 0 and len(block_model.out_vars) == 1:
        if block_model.out_vars[0].ref is not None and len(block_model.algebraic_vars) == 0 and len(block_model.state_vars) == 0:
            return block_model.out_vars[0]
        else:
            return None
    else:
        return None


def is_root_interface_wrapper_block(block_model: Block | None) -> bool:
    """
    Return whether one block is a derived root-interface wrapper shell.

    A real user/model block can still expose one referenced port. Wrapper
    classification must therefore remain stricter than the single-port shape
    check alone: wrappers are pure shells with exactly one root-ref port and no
    internal symbolic state.

    :param block_model: Candidate block.
    :return: ``True`` when the block is one pure interface wrapper shell.
    """
    interface_var: Var | None = get_single_interface_var(block_model)
    if block_model is None:
        return False
    elif not block_model.is_root_interface_wrapper:
        return False
    elif interface_var is None:
        return False
    elif interface_var.ref is None:
        return False
    elif len(block_model.algebraic_vars) > 0:
        return False
    elif len(block_model.state_vars) > 0:
        return False
    elif len(block_model.diff_vars) > 0:
        return False
    elif len(block_model.parameters) > 0:
        return False
    elif len(block_model.state_eqs) > 0:
        return False
    elif len(block_model.algebraic_eqs) > 0:
        return False
    elif len(block_model.differential_eqs) > 0:
        return False
    elif len(block_model.children) > 0:
        return False
    else:
        return True


def _get_port_direction(is_output: bool) -> str:
    """
    Return the serialized port-direction label.

    :param is_output: Whether the port is one output.
    :return: ``output`` or ``input``.
    """
    if is_output:
        return "output"
    else:
        return "input"


def _build_root_ref_value(reference: VarPowerFlowReferenceType | None) -> str | None:
    """
    Return the serialized root-reference value for intent persistence.

    :param reference: Semantic root reference.
    :return: Serialized value or ``None``.
    """
    if reference is None:
        return None
    else:
        return reference.value
def resolve_unique_root_interface_var(
        root_vars: List[Var],
        wrapper_var: Var | None,
        interface_index: int | None,
) -> Var | None:
    """
    Resolve a wrapper variable against an authoritative root-interface list.

    Matching priority is object identity, stable identity, power-flow reference,
    mutable UID, and finally the persisted interface index. Every non-identity
    match must be unique before it is accepted.

    :param root_vars: Authoritative root input or output variables.
    :param wrapper_var: Variable currently carried by the wrapper.
    :param interface_index: Root-interface position used as a legacy fallback.
    :return: Authoritative root variable, or ``None`` when resolution is ambiguous.
    """
    stable_match: Var | None = None
    stable_match_count: int = 0
    reference_match: Var | None = None
    reference_match_count: int = 0
    uid_match: Var | None = None
    uid_match_count: int = 0
    candidate_var: Var

    if wrapper_var is not None:
        for candidate_var in root_vars:
            if candidate_var is wrapper_var:
                return candidate_var
            else:
                pass

            if candidate_var.non_mutable_uid == wrapper_var.non_mutable_uid:
                stable_match = candidate_var
                stable_match_count += 1
            else:
                pass

            if (candidate_var.ref is not None
                    and wrapper_var.ref is not None
                    and candidate_var.ref == wrapper_var.ref):
                reference_match = candidate_var
                reference_match_count += 1
            else:
                pass

            if candidate_var.uid == wrapper_var.uid:
                uid_match = candidate_var
                uid_match_count += 1
            else:
                pass
    else:
        pass

    if stable_match_count == 1:
        return stable_match
    elif reference_match_count == 1:
        return reference_match
    elif uid_match_count == 1:
        return uid_match
    elif interface_index is not None and 0 <= interface_index < len(root_vars):
        return root_vars[interface_index]
    else:
        return None


def find_legacy_interface_wrapper(
        child_blocks: List[Block],
        block_type: BlockType,
        reference_var: Var,
) -> Block | None:
    """
    Find one legacy wrapper matching an authoritative root variable.

    :param child_blocks: Current root-block children.
    :param block_type: Input or output interface wrapper type.
    :param reference_var: Authoritative root-interface variable.
    :return: Unique legacy wrapper, or ``None``.
    """
    stable_match: Block | None = None
    stable_match_count: int = 0
    reference_match: Block | None = None
    reference_match_count: int = 0
    child_block: Block
    candidate_var: Var | None

    for child_block in child_blocks:
        if block_type == BlockType.INPUT_CONN:
            if len(child_block.out_vars) == 1 and len(child_block.in_vars) == 0:
                candidate_var = child_block.out_vars[0]
            else:
                candidate_var = None
        elif block_type == BlockType.OUTPUT_CONN:
            if len(child_block.in_vars) == 1 and len(child_block.out_vars) == 0:
                candidate_var = child_block.in_vars[0]
            else:
                candidate_var = None
        else:
            candidate_var = None

        if candidate_var is not None:
            if (candidate_var is reference_var
                    or candidate_var.non_mutable_uid == reference_var.non_mutable_uid):
                stable_match = child_block
                stable_match_count += 1
            elif (candidate_var.ref is not None
                  and reference_var.ref is not None
                  and candidate_var.ref == reference_var.ref):
                reference_match = child_block
                reference_match_count += 1
            else:
                pass
        else:
            pass

    if stable_match_count == 1:
        return stable_match
    elif reference_match_count == 1:
        return reference_match
    else:
        return None


def build_expected_root_emt_interface_for_device(device: Any) -> tuple[dict[VarPowerFlowReferenceType, Var], dict[VarPowerFlowReferenceType, Var]]:
    """
    Build the authoritative EMT root interface expected for one root editor.

    Input references always point to the current live bus-shell voltage vars.
    Output references represent the network current contract expected for the
    edited device side.

    :param device: Root editor API object.
    :return: ``(inputs_by_ref, outputs_by_ref)``.
    """
    inputs_by_ref: dict[VarPowerFlowReferenceType, Var] = dict()
    outputs_by_ref: dict[VarPowerFlowReferenceType, Var] = dict()
    voltage_var: Var | None

    if isinstance(device, InjectionParent):
        if device.bus.is_dc:
            voltage_var = device.bus.emt_model.external_mapping.get(VarPowerFlowReferenceType.Vdc, None)
            if voltage_var is not None:
                inputs_by_ref[VarPowerFlowReferenceType.Vdc] = voltage_var
                outputs_by_ref[VarPowerFlowReferenceType.Idc] = voltage_var
            else:
                pass
        else:
            for reference in list([
                VarPowerFlowReferenceType.v_N,
                VarPowerFlowReferenceType.v_A,
                VarPowerFlowReferenceType.v_B,
                VarPowerFlowReferenceType.v_C,
            ]):
                voltage_var = device.bus.emt_model.external_mapping.get(reference, None)
                if voltage_var is not None:
                    inputs_by_ref[reference] = voltage_var
                else:
                    pass

        if device.bus.is_dc:
            pass
        else:
            if VarPowerFlowReferenceType.v_N in inputs_by_ref:
                outputs_by_ref[VarPowerFlowReferenceType.i_N] = inputs_by_ref[VarPowerFlowReferenceType.v_N]
            else:
                pass
            if VarPowerFlowReferenceType.v_A in inputs_by_ref:
                outputs_by_ref[VarPowerFlowReferenceType.i_A] = inputs_by_ref[VarPowerFlowReferenceType.v_A]
            else:
                pass
            if VarPowerFlowReferenceType.v_B in inputs_by_ref:
                outputs_by_ref[VarPowerFlowReferenceType.i_B] = inputs_by_ref[VarPowerFlowReferenceType.v_B]
            else:
                pass
            if VarPowerFlowReferenceType.v_C in inputs_by_ref:
                outputs_by_ref[VarPowerFlowReferenceType.i_C] = inputs_by_ref[VarPowerFlowReferenceType.v_C]
            else:
                pass
    elif isinstance(device, BranchParent):
        from_pairs: list[tuple[VarPowerFlowReferenceType, VarPowerFlowReferenceType]]
        to_pairs: list[tuple[VarPowerFlowReferenceType, VarPowerFlowReferenceType]]

        if device.bus_from.is_dc:
            voltage_var = device.bus_from.emt_model.external_mapping.get(VarPowerFlowReferenceType.Vdc, None)
            if voltage_var is not None:
                inputs_by_ref[VarPowerFlowReferenceType.Vf_dc] = voltage_var
                outputs_by_ref[VarPowerFlowReferenceType.If_dc] = voltage_var
            else:
                pass
        else:
            from_pairs = list([
                (VarPowerFlowReferenceType.vf_N, VarPowerFlowReferenceType.v_N),
                (VarPowerFlowReferenceType.vf_A, VarPowerFlowReferenceType.v_A),
                (VarPowerFlowReferenceType.vf_B, VarPowerFlowReferenceType.v_B),
                (VarPowerFlowReferenceType.vf_C, VarPowerFlowReferenceType.v_C),
            ])
            for input_reference, bus_reference in from_pairs:
                voltage_var = device.bus_from.emt_model.external_mapping.get(bus_reference, None)
                if voltage_var is not None:
                    inputs_by_ref[input_reference] = voltage_var
                else:
                    pass

            if VarPowerFlowReferenceType.vf_N in inputs_by_ref:
                outputs_by_ref[VarPowerFlowReferenceType.if_N] = inputs_by_ref[VarPowerFlowReferenceType.vf_N]
            else:
                pass
            if VarPowerFlowReferenceType.vf_A in inputs_by_ref:
                outputs_by_ref[VarPowerFlowReferenceType.if_A] = inputs_by_ref[VarPowerFlowReferenceType.vf_A]
            else:
                pass
            if VarPowerFlowReferenceType.vf_B in inputs_by_ref:
                outputs_by_ref[VarPowerFlowReferenceType.if_B] = inputs_by_ref[VarPowerFlowReferenceType.vf_B]
            else:
                pass
            if VarPowerFlowReferenceType.vf_C in inputs_by_ref:
                outputs_by_ref[VarPowerFlowReferenceType.if_C] = inputs_by_ref[VarPowerFlowReferenceType.vf_C]
            else:
                pass

        if device.bus_to.is_dc:
            voltage_var = device.bus_to.emt_model.external_mapping.get(VarPowerFlowReferenceType.Vdc, None)
            if voltage_var is not None:
                inputs_by_ref[VarPowerFlowReferenceType.Vt_dc] = voltage_var
                outputs_by_ref[VarPowerFlowReferenceType.It_dc] = voltage_var
            else:
                pass
        else:
            to_pairs = list([
                (VarPowerFlowReferenceType.vt_N, VarPowerFlowReferenceType.v_N),
                (VarPowerFlowReferenceType.vt_A, VarPowerFlowReferenceType.v_A),
                (VarPowerFlowReferenceType.vt_B, VarPowerFlowReferenceType.v_B),
                (VarPowerFlowReferenceType.vt_C, VarPowerFlowReferenceType.v_C),
            ])
            for input_reference, bus_reference in to_pairs:
                voltage_var = device.bus_to.emt_model.external_mapping.get(bus_reference, None)
                if voltage_var is not None:
                    inputs_by_ref[input_reference] = voltage_var
                else:
                    pass

            if VarPowerFlowReferenceType.vt_N in inputs_by_ref:
                outputs_by_ref[VarPowerFlowReferenceType.it_N] = inputs_by_ref[VarPowerFlowReferenceType.vt_N]
            else:
                pass
            if VarPowerFlowReferenceType.vt_A in inputs_by_ref:
                outputs_by_ref[VarPowerFlowReferenceType.it_A] = inputs_by_ref[VarPowerFlowReferenceType.vt_A]
            else:
                pass
            if VarPowerFlowReferenceType.vt_B in inputs_by_ref:
                outputs_by_ref[VarPowerFlowReferenceType.it_B] = inputs_by_ref[VarPowerFlowReferenceType.vt_B]
            else:
                pass
            if VarPowerFlowReferenceType.vt_C in inputs_by_ref:
                outputs_by_ref[VarPowerFlowReferenceType.it_C] = inputs_by_ref[VarPowerFlowReferenceType.vt_C]
            else:
                pass
    else:
        pass

    return inputs_by_ref, outputs_by_ref


def get_reference_sort_key(reference: VarPowerFlowReferenceType) -> str:
    """
    Return one deterministic sort key for interface references.

    :param reference: Power-flow reference to order.
    :return: Sort key.
    """
    return reference.value


def get_protected_connection_item_position_sort_key(
        item: graph.ProtectedConnectionBlockItem,
) -> tuple[float, float, int]:
    """
    Return one deterministic positional key for a protected connection item.

    :param item: Protected connection item to order.
    :return: Key ordered by vertical position, horizontal position and block UID.
    """
    if item.subsys is not None:
        return item.pos().y(), item.pos().x(), item.subsys.uid
    else:
        return item.pos().y(), item.pos().x(), 0


def get_centered_connection_stack_height(
        items: List[graph.ProtectedConnectionBlockItem],
        vertical_gap: float,
) -> float:
    """
    Return the total height of one vertically spaced connection-item stack.

    :param items: Ordered protected connection items.
    :param vertical_gap: Gap between adjacent items.
    :return: Total stack height.
    """
    total_height: float = 0.0
    item: graph.ProtectedConnectionBlockItem

    for item in items:
        total_height += item.boundingRect().height()

    if len(items) > 1:
        total_height += vertical_gap * float(len(items) - 1)
    else:
        pass

    return total_height


def position_centered_connection_stack(
        items: List[graph.ProtectedConnectionBlockItem],
        x_position: float,
        center_y: float,
        vertical_gap: float,
) -> None:
    """
    Position one ordered connection-item stack around a vertical center.

    :param items: Ordered protected connection items.
    :param x_position: Scene X coordinate for every item.
    :param center_y: Desired vertical center of the full stack.
    :param vertical_gap: Gap between adjacent items.
    :return: None.
    """
    current_top: float = center_y - get_centered_connection_stack_height(
        items=items,
        vertical_gap=vertical_gap,
    ) / 2.0
    item: graph.ProtectedConnectionBlockItem
    local_rect: QtCore.QRectF

    for item in items:
        local_rect = item.boundingRect()
        item.setPos(x_position - local_rect.left(), current_top - local_rect.top())
        current_top += local_rect.height() + vertical_gap


def get_block_diagram_node_position_sort_key(
        node_item: tuple[int, BlockDiagramNode],
) -> tuple[float, float, int]:
    """
    Return one deterministic positional key for a diagram node entry.

    :param node_item: ``(uid, node)`` entry to order.
    :return: Key ordered by vertical position, horizontal position and UID.
    """
    node_uid: int
    node: BlockDiagramNode
    node_uid, node = node_item
    return node.y, node.x, node_uid


def build_expected_root_emt_output_name(reference: VarPowerFlowReferenceType) -> str:
    """
    Build the canonical root EMT current-variable name for one interface ref.

    :param reference: Current-output power-flow reference.
    :return: Canonical variable name.
    """
    if reference == VarPowerFlowReferenceType.Idc:
        return "net_conn_Idc"
    elif reference == VarPowerFlowReferenceType.If_dc:
        return "net_conn_If_dc"
    elif reference == VarPowerFlowReferenceType.It_dc:
        return "net_conn_It_dc"
    else:
        return f"net_conn_{reference.value}"


def build_branch_authoritative_ref_by_shared_ref(reference: VarPowerFlowReferenceType,
                                                 block_type: BlockType,
                                                 available_root_refs: set[VarPowerFlowReferenceType]) -> VarPowerFlowReferenceType | None:
    """
    Map one stale shared branch root ref to the authoritative side-specific root ref.

    :param reference: Shared or side-specific persisted reference.
    :param block_type: Wrapper node direction.
    :param available_root_refs: Current authoritative refs available on the root.
    :return: Current authoritative ref or ``None`` when unresolved.
    """
    preferred_refs: list[VarPowerFlowReferenceType] = list()

    if block_type == BlockType.INPUT_CONN:
        if reference == VarPowerFlowReferenceType.v_N:
            preferred_refs = list([VarPowerFlowReferenceType.vf_N, VarPowerFlowReferenceType.vt_N])
        elif reference == VarPowerFlowReferenceType.v_A:
            preferred_refs = list([VarPowerFlowReferenceType.vf_A, VarPowerFlowReferenceType.vt_A])
        elif reference == VarPowerFlowReferenceType.v_B:
            preferred_refs = list([VarPowerFlowReferenceType.vf_B, VarPowerFlowReferenceType.vt_B])
        elif reference == VarPowerFlowReferenceType.v_C:
            preferred_refs = list([VarPowerFlowReferenceType.vf_C, VarPowerFlowReferenceType.vt_C])
        else:
            preferred_refs = list([reference])
    elif block_type == BlockType.OUTPUT_CONN:
        if reference == VarPowerFlowReferenceType.i_N:
            preferred_refs = list([VarPowerFlowReferenceType.if_N, VarPowerFlowReferenceType.it_N])
        elif reference == VarPowerFlowReferenceType.i_A:
            preferred_refs = list([VarPowerFlowReferenceType.if_A, VarPowerFlowReferenceType.it_A])
        elif reference == VarPowerFlowReferenceType.i_B:
            preferred_refs = list([VarPowerFlowReferenceType.if_B, VarPowerFlowReferenceType.it_B])
        elif reference == VarPowerFlowReferenceType.i_C:
            preferred_refs = list([VarPowerFlowReferenceType.if_C, VarPowerFlowReferenceType.it_C])
        else:
            preferred_refs = list([reference])
    else:
        return None

    preferred_ref: VarPowerFlowReferenceType
    for preferred_ref in preferred_refs:
        if preferred_ref in available_root_refs:
            return preferred_ref
        else:
            pass

    return None


def build_expected_root_interface_ref_order(block_type: BlockType,
                                            input_refs: dict[VarPowerFlowReferenceType, Var],
                                            output_refs: dict[VarPowerFlowReferenceType, Var]) -> list[VarPowerFlowReferenceType]:
    """
    Build the authoritative wrapper-reference order for one root interface direction.

    :param block_type: Wrapper direction.
    :param input_refs: Authoritative root inputs keyed by ref.
    :param output_refs: Authoritative root outputs keyed by ref.
    :return: Ordered root-interface refs.
    """
    if block_type == BlockType.INPUT_CONN:
        return sorted(list(input_refs.keys()), key=get_reference_sort_key)
    elif block_type == BlockType.OUTPUT_CONN:
        return sorted(list(output_refs.keys()), key=get_reference_sort_key)
    else:
        return list()


def register_legacy_interface_uid_alias(
        aliases: Dict[int, int | None],
        old_uid: int | None,
        repaired_uid: int,
) -> None:
    """
    Register one unambiguous legacy interface UID replacement.

    :param aliases: Legacy-to-current UID lookup table.
    :param old_uid: Legacy UID observed in persisted data.
    :param repaired_uid: Current diagram-node UID.
    :return: None.
    """
    if old_uid is None or old_uid == repaired_uid:
        pass
    elif old_uid not in aliases:
        aliases[old_uid] = repaired_uid
    elif aliases[old_uid] != repaired_uid:
        aliases[old_uid] = None
    else:
        pass


def synchronize_matching_mapping_var_name(
        block_model: Block | None,
        reference_var: Var,
        new_name: str,
) -> None:
    """
    Rename matching mapped variables in one bus-side symbolic block.

    :param block_model: RMS or EMT bus model, or ``None``.
    :param reference_var: Renamed editor-side interface variable.
    :param new_name: New symbolic name.
    :return: None.
    """
    if block_model is not None:
        mapped_var: Var | None
        for mapped_var in block_model.external_mapping.values():
            if (mapped_var is not None
                    and mapped_var.non_mutable_uid == reference_var.non_mutable_uid):
                mapped_var.set_name(new_name)
            else:
                pass
    else:
        pass


class DynamicBlockEditorGUI(QtWidgets.QMainWindow):
    """
    DynamicModelEditorGUI
    """

    dirtyStateChanged = Signal(bool)

    UNARY_MATH_BLOCK_TYPES: set[BlockType] = {
        BlockType.CONST,
        BlockType.GAIN,
        BlockType.ABS,
        BlockType.INTEGRATOR,
        BlockType.POWER,
        BlockType.SIN,
        BlockType.COS,
        BlockType.TAN,
        BlockType.EXP,
        BlockType.LOG,
        BlockType.LOG10,
        BlockType.SQRT,
        BlockType.ASIN,
        BlockType.ACOS,
        BlockType.ATAN,
        BlockType.SINH,
        BlockType.COSH,
        BlockType.TANH,
        BlockType.REAL,
        BlockType.IMAG,
        BlockType.CONJ,
        BlockType.ANGLE,
    }

    def __init__(self,
                 var_factory: VarFactory,
                 api_object: ALL_DEV_TYPES,
                 circuit: MultiCircuit,
                 current_theme: DynEditorGraphicsModes,
                 mode: DynamicSimulationMode = DynamicSimulationMode.RMS,
                 templates_list: Optional[List[RmsModelTemplate | EmtModelTemplate | FmuTemplate]] = None,
                 is_root_editor=False,
                 modal: bool = True,
                 workspace_embedded: bool = False,
                 root_block: Block | None = None,
                 current_block: Block | None = None,
                 document=None,
                 block2blocktype: Dict[int, BlockType] | None = None):
        """
        Initializes a dynamic block editor window.

        In the new document-based architecture the editor receives two
        blocks that already live inside the working tree owned by
        :class:`DynamicEditorDocument`:

        * ``root_block`` — the top-level working block for the tab.
        * ``current_block`` — the specific node being edited right now.

        The editor never clones.  All edits target the working tree
        directly.

        Legacy callers that pass ``block=`` and ``main_editor=`` are
        still supported but deprecated.

        :param var_factory: Factory object responsible for variable creation and management.
        :param api_object: Optional API object associated with the dynamic model.
        :param circuit: Circuit context that owns the edited dynamic device.
        :param mode: Specifies the editor mode, either RMS or EMT.
        :param templates_list: Optional block-template catalogue entries exposed to the editor.
        :param is_root_editor: Indicates whether this instance is the root-level editor.
        :param modal: Specifies whether the editor window should be modal.
        :param workspace_embedded: Whether the editor is hosted inside the tabbed dynamic-editor workspace.
        :param root_block: Top-level working block (from the document).
        :param current_block: Block currently being edited (from the working tree).
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

        self.ui.deviceLabel.setText(api_object.name)

        self.block_role: int = int(QtCore.Qt.ItemDataRole.UserRole) + 300
        self.mime_type: str = "application/x-veragrid-dynamics-block"

        self.setWindowTitle(self.tr("Dynamic Model Editor"))

        self.ui.splitter.setStretchFactor(0, 6)
        self.ui.splitter.setStretchFactor(1, 10)

        self.var_factory = var_factory
        self.api_object = api_object

        self.circuit: MultiCircuit = circuit
        self.mode = mode
        self.is_root_editor = is_root_editor
        self.workspace_embedded = workspace_embedded

        self._document = document
        self._block2blocktype: Dict[int, BlockType] = block2blocktype if block2blocktype is not None else dict()
        self._navigation_delegate = None
        self.templates_list: List[
            RmsModelTemplate | EmtModelTemplate | FmuTemplate] = templates_list if templates_list is not None else list()

        self._emt_bus_fallback_warning_shown: bool = False
        self._selected_side_block: Block | None = None
        self._validation_issue_overlay_active: bool = False
        self._initial_scene_fit_pending: bool = False
        self.setWindowTitle(self.tr("Dynamic Model Editor [{mode}]").format(mode=self.mode.name))
        self.block_counters: Dict[BlockType, int] = dict()
        self.scene: graph.DiagramScene = graph.DiagramScene(self)
        self.changes_applied: bool = False
        self.has_unapplied_changes: bool = False
        self.dynamic_editor_entry: DynamicEditorEntry | None = None
        self._prepared_to_delete: bool = False
        self._qt_routing_session: QtRoutingSession = QtRoutingSession()
        self.colors_palet: graph.EditorGraphicsDefaultsDark | graph.EditorGraphicsDefaultsLight = graph.EditorGraphicsDefaultsDark()
        self.current_theme: DynEditorGraphicsModes = current_theme
        self.set_colors_palet()

        self.root_block: Block = root_block if root_block is not None else Block()
        self.main_block: Block = current_block if current_block is not None else Block()

        self.blocktype2templatebuilder = get_blocktype2template_builder_dict()

        self.devices_static_params_mapping: Dict[DeviceType, List[ParamPowerFlowReferenceType]] = (
            self.circuit.get_devices_static_params_mapping()
        )

        self.diagram: BlockDiagram = self.main_block.diagram
        initial_non_interface_children: List[Block] = [
            child_block for child_block in self.main_block.children
            if not is_root_interface_wrapper_block(child_block)
        ]
        bootstrap_missing_non_interface_graphics: bool = (
            len(initial_non_interface_children) > 0
            and not any(
                child_block.uid in self.diagram.node_data
                for child_block in initial_non_interface_children
            )
        )
        auto_layout_root_interface: bool = self._root_interface_layout_uses_bootstrap_positions()
        root_topology_refs_added: bool = False

        if self.workspace_embedded:
            self.menuBar().setVisible(False)
        else:
            pass

        # library
        self.library = DynamicEditorLibrary(self.api_object, self.mode, self.templates_list)
        self.library_proxy_model = LibraryTreeFilterProxyModel(
            search_role=graph.EditorGraphicsCommonFeatures.LIBRARY_SEARCH_TEXT_ROLE,
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
        self.variables_model = dialog_models.WrappableBlockTableModel(
            var_factory=self.var_factory,
            parameter_value_type_role=graph.EditorGraphicsCommonFeatures.PARAMETER_VALUE_TYPE_ROLE,
            parameter_editable_role=graph.EditorGraphicsCommonFeatures.PARAMETER_EDITABLE_ROLE,
            block_search_role=graph.EditorGraphicsCommonFeatures.BLOCK_SEARCH_ROLE,
            parent=self.ui.variablesTableView
        )
        self.variables_model.set_mode(DynamicTableModelMode.VARIABLES)
        self.variables_model.set_delegates()
        self.variables_search = QLineEdit()
        self.variables_search.setPlaceholderText(self.tr("Search variables..."))
        self.variables_search.setClearButtonEnabled(True)
        self.ui.verticalLayout_7.insertWidget(0, self.variables_search)
        self.variables_proxy = dialog_models.BlockTableFilterProxyModel(search_role=graph.EditorGraphicsCommonFeatures.BLOCK_SEARCH_ROLE,
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
        self.parameters_model = dialog_models.WrappableBlockTableModel(
            api_object=self.api_object,
            var_factory=self.var_factory,
            parameter_value_type_role=graph.EditorGraphicsCommonFeatures.PARAMETER_VALUE_TYPE_ROLE,
            parameter_editable_role=graph.EditorGraphicsCommonFeatures.PARAMETER_EDITABLE_ROLE,
            block_search_role=graph.EditorGraphicsCommonFeatures.BLOCK_SEARCH_ROLE,
            parent=self.ui.parametersTableView
        )
        self.parameters_model.set_mode(DynamicTableModelMode.PARAMETERS)
        self.parameters_model.set_delegates()
        self.parameters_search = QLineEdit()
        self.parameters_search.setPlaceholderText(self.tr("Search parameters..."))
        self.parameters_search.setClearButtonEnabled(True)
        self.ui.verticalLayout_8.insertWidget(0, self.parameters_search)
        self.parameters_proxy = dialog_models.BlockTableFilterProxyModel(search_role=graph.EditorGraphicsCommonFeatures.BLOCK_SEARCH_ROLE,
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
        self.equations_model = dialog_models.WrappableBlockTableModel(
            var_factory=self.var_factory,
            parameter_value_type_role=graph.EditorGraphicsCommonFeatures.PARAMETER_VALUE_TYPE_ROLE,
            parameter_editable_role=graph.EditorGraphicsCommonFeatures.PARAMETER_EDITABLE_ROLE,
            block_search_role=graph.EditorGraphicsCommonFeatures.BLOCK_SEARCH_ROLE,
            parent=self.ui.equationsTableView
        )
        self.equations_model.set_mode(DynamicTableModelMode.EQUATIONS)
        self.equations_model.set_delegates()
        self._equations_latex_delegate = self.ui.equationsTableView.itemDelegateForColumn(1)
        self.equations_model.latex_invalidation_requested.connect(
            self._invalidate_equations_latex
        )
        self.equations_search = QLineEdit()
        self.equations_search.setPlaceholderText(self.tr("Search equations..."))
        self.equations_search.setClearButtonEnabled(True)
        self.ui.verticalLayout_9.insertWidget(0, self.equations_search)
        self.equations_proxy = dialog_models.BlockTableFilterProxyModel(search_role=graph.EditorGraphicsCommonFeatures.BLOCK_SEARCH_ROLE,
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
        equations_vheader = self.ui.equationsTableView.verticalHeader()
        equations_vheader.setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        equations_vheader.setVisible(False)
        self.ui.equationsTableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.ui.equationsTableView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.ui.equationsTableView.doubleClicked.connect(self.on_parameters_table_double_clicked)
        self.ui.equationsTableView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.equationsTableView.customContextMenuRequested.connect(self.show_equations_table_context_menu)

        self.parameters_model.block_updated.connect(self.on_block_updated)
        self.variables_model.block_updated.connect(self.on_block_updated)
        self.equations_model.block_updated.connect(self.on_block_updated)

        self.view: graph.GraphicsView = graph.GraphicsView(self.scene)
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
        # if self.mode == DynamicSimulationMode.EMT and self.is_root_editor:
        #     self._ensure_full_emt_editor_interface()
        # else:
        #     pass
        dialog_models._ensure_block_tree_names(self.main_block, prefix="block")

        # The root device editor is the only place where the dynamic model is
        # coupled to the network buses. Ensure the corresponding bus helper
        # models exist before any scene bootstrap path runs, so fresh opens,
        # reopens with saved diagrams, and child-containing models all observe
        # the same already-initialized bus-side contract.
        if self.is_root_editor:
            if self.mode == DynamicSimulationMode.RMS:
                if isinstance(self.api_object, InjectionParent):
                    dialog_models._initialize_editor_assigned_rms_bus_model(bus=self.api_object.bus,
                                                                            var_factory=self.var_factory)
                elif isinstance(self.api_object, BranchParent):
                    dialog_models._initialize_editor_assigned_rms_bus_model(bus=self.api_object.bus_from,
                                                                            var_factory=self.var_factory)
                    dialog_models._initialize_editor_assigned_rms_bus_model(bus=self.api_object.bus_to,
                                                                            var_factory=self.var_factory)
                else:
                    pass
            elif self.mode == DynamicSimulationMode.EMT:
                if isinstance(self.api_object, InjectionParent):
                    dialog_models._initialize_editor_assigned_emt_bus_model(bus=self.api_object.bus,
                                                                            api_object=self.api_object,
                                                                            circuit=self.circuit,
                                                                            var_factory=self.var_factory)
                elif isinstance(self.api_object, BranchParent):
                    dialog_models._initialize_editor_assigned_emt_bus_model(bus=self.api_object.bus_from,
                                                                            api_object=self.api_object,
                                                                            circuit=self.circuit,
                                                                            var_factory=self.var_factory)
                    dialog_models._initialize_editor_assigned_emt_bus_model(bus=self.api_object.bus_to,
                                                                            api_object=self.api_object,
                                                                            circuit=self.circuit,
                                                                            var_factory=self.var_factory)
                else:
                    pass
            else:
                pass
        else:
            pass

        if self.is_root_editor and self.mode == DynamicSimulationMode.EMT and isinstance(self.api_object, BranchParent):
            self._remove_shared_branch_emt_root_refs()
        else:
            pass

        if self.is_root_editor and self.mode == DynamicSimulationMode.EMT:
            # Promote explicitly persisted interface nodes before topology
            # reconciliation can remove their diagram records. This preserves
            # enough semantic identity to prune a stale wrapper safely.
            self._convert_legacy_root_interface_children_to_wrappers()
        else:
            pass

        if self.is_root_editor and self.mode == DynamicSimulationMode.EMT:
            expected_topology_inputs: dict[VarPowerFlowReferenceType, Var]
            expected_topology_outputs: dict[VarPowerFlowReferenceType, Var]
            current_input_refs: set[VarPowerFlowReferenceType]
            current_output_refs: set[VarPowerFlowReferenceType]
            expected_topology_inputs, expected_topology_outputs = build_expected_root_emt_interface_for_device(
                self.api_object,
            )
            current_input_refs = set(
                root_var.ref for root_var in self.main_block.in_vars
                if isinstance(root_var.ref, VarPowerFlowReferenceType)
            )
            current_output_refs = set(
                root_var.ref for root_var in self.main_block.out_vars
                if isinstance(root_var.ref, VarPowerFlowReferenceType)
            )
            root_topology_refs_added = (
                len(set(expected_topology_inputs.keys()) - current_input_refs) > 0
                or len(set(expected_topology_outputs.keys()) - current_output_refs) > 0
            )
        else:
            pass

        root_emt_interface_changed: bool = self._reconcile_root_emt_interface_from_current_topology()
        removed_legacy_root_self_nodes: bool = self._remove_legacy_root_self_nodes()

        if self.is_root_editor and self.mode == DynamicSimulationMode.EMT:
            self._remove_stale_root_interface_duplicate_children()
            self._ensure_root_interface_wrapper_blocks_exist(create_missing=True)
            self._ensure_root_interface_wrapper_nodes_exist()
            self._record_template_root_interface_connection_intents()
            self._canonicalize_persisted_root_interface_intents()
        else:
            pass

        if root_emt_interface_changed:
            self.has_unapplied_changes = True
            self.changes_applied = False
        elif removed_legacy_root_self_nodes:
            self.has_unapplied_changes = True
            self.changes_applied = False
        else:
            pass

        requires_connection_bootstrap: bool = dialog_models.block_requires_editor_connection_bootstrap(self.main_block)

        # Automatically build items for models with no graphical info
        if not self.main_block.empty() and not self.main_block.diagram.node_data and not requires_connection_bootstrap:
            if self.main_block.children:
                input_output_blocks: List[Block] = list()
                block_positions_dict: Dict[int, Tuple[float, float]] = dict()

                # First of all create all Blocks that will be needed but without adding them to the scene and without creating the node in the diagram and add thme to the correspondant list:

                if self.is_root_editor and self.mode == DynamicSimulationMode.EMT:
                    pass
                else:
                    self.add_connection_blocks(input_output_blocks)
                # Blocks in children --> self.main_block.children

                layout_graph = self._build_elk_layout_graph(
                    self.main_block.children,
                    input_output_blocks,
                )
                layout_result = SugiyamaLayeredPythonEngine().compute(layout_graph)
                block_positions_dict.update(
                    {
                        int(node.identifier): (node.x or 0.0, node.y or 0.0)
                        for node in layout_result.graph.children
                    }
                )


                # Oce everything is calculated we build the items from the blocks and the calculated positions, add them to an items list and create the DiagramNodes:

                blockitems_list: List[graph.BlockItem | graph.GenericBlockItem | graph.RectBaseArithmeticOpItem | graph.RoundBaseArithmeticOpItem | graph.UnOpItem] = list()
                items_by_uid: Dict[int, graph.BlockItem | graph.GenericBlockItem] = dict()
                for child in self.main_block.children:
                    position = block_positions_dict[child.uid]
                    item = self.generate_block_item_for_block(child, position[0], position[1])
                    blockitems_list.append(item)
                    items_by_uid[child.uid] = item

                for blk in input_output_blocks:
                    position = block_positions_dict[blk.uid]
                    item = self.generate_ext_conn_block_item_for_block(blk, position[0], position[1])
                    blockitems_list.append(item)
                    items_by_uid[blk.uid] = item

                if len(blockitems_list) != 0:
                    self._connect_items_from_layout(items_by_uid, layout_result.graph)

                # we need an algorithm to create the connections properly:
                    # bends/corners not in the same place
                    # prevent them from overlapping with other blocks
                    # prevent them from overlapping with other connectors in the same direction
                    # allow only 90degree angles, no 180.
                # once we have all the items created and well positioned we build the connections


            elif not self.main_block.children:
                if self.is_root_editor:
                    self.add_connection_items()
                else:
                    if self.main_block.in_vars or self.main_block.out_vars:
                        self.generate_block_item_for_block(self.main_block, 480.0, 260.0)
                    else:
                        pass

                    self.add_connection_items()


        # Build items for models with graphical info
        elif not self.main_block.diagram.node_data:
            # here we add the connection variables to the main block
            if self.is_root_editor:
                self.add_connection_vars()
                # self.add_api_obj_mapping()

            self.add_connection_items()
        else:
            pass
        self.rebuild_scene_from_diagram()
        if self.main_block.children:
            self._rebuild_missing_non_interface_connections(
                rebuild_interface_connections=bootstrap_missing_non_interface_graphics,
            )
        else:
            pass
        if self.is_root_editor and self.mode == DynamicSimulationMode.EMT:
            if isinstance(self.api_object, BranchParent) and self.api_object.emt_template is not None:
                self._repair_saved_branch_template_root_wires()
            else:
                pass
            self._rematerialize_root_interface_intents()
        else:
            pass

        if auto_layout_root_interface or root_topology_refs_added or bootstrap_missing_non_interface_graphics:
            self._layout_root_interface_items_around_content()
        else:
            pass

        self._initial_scene_fit_pending = True

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """
        Fit the complete diagram once the editor receives its first real viewport.

        :param event: Qt show event.
        :return: None.
        """
        super().showEvent(event)
        if self._initial_scene_fit_pending:
            QtCore.QTimer.singleShot(0, self._fit_initial_scene_view)
        else:
            pass

    def set_colors_palet(self):
        if self.current_theme == DynEditorGraphicsModes.DARK:
            self.colors_palet = graph.EditorGraphicsDefaultsDark()
        else:
            self.colors_palet = graph.EditorGraphicsDefaultsLight()

    def set_navigation_delegate(self, delegate) -> None:
        """
        Register the navigation delegate responsible for opening child blocks.

        The delegate must expose a ``navigate_to_block(block: Block) -> None``
        method.  :class:`DynamicEditorTab` acts as the default delegate.

        :param delegate: Object that can open blocks for navigation.
        :return: None.
        """
        self._navigation_delegate = delegate

    def request_navigate_to_block(self, block: Block) -> None:
        """
        Request navigation into a child block.

        Delegates the request to the registered navigation delegate.
        If no delegate has been registered, the request is silently ignored.

        :param block: Child block to navigate into.
        :return: None.
        """
        if self._navigation_delegate is not None:
            self._navigation_delegate.navigate_to_block(block)


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
        block.__dict__[graph.EditorGraphicsCommonFeatures.MODAL_TEMPLATE_KIND_ATTR] = kind
        block.__dict__[graph.EditorGraphicsCommonFeatures.MODAL_TEMPLATE_CONFIG_ATTR] = copy.deepcopy(config)

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

        kind: Any = block.__dict__.get(graph.EditorGraphicsCommonFeatures.MODAL_TEMPLATE_KIND_ATTR, None)
        config: Any = block.__dict__.get(graph.EditorGraphicsCommonFeatures.MODAL_TEMPLATE_CONFIG_ATTR, None)

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

    def build_position_changed_callback(self, block_uid: int) -> graph.BlockPositionChangedCallback:
        """
        Build the explicit callback object used by graphics items to report movement.

        :param block_uid: Moved block uid.
        :return: Position change callback wrapper.
        """

        return graph.BlockPositionChangedCallback(self, block_uid)

    def create_item_using_blocktype_wizard(self,
                                           blocktype: BlockType,
                                           x_pos: float,
                                           y_pos: float) -> graph.GenericBlockItem | graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem | None:
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
        else:
            return

        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:

            template = template_builder.eval()
            block_model = template.block

            block_item: graph.GenericBlockItem = graph.GenericBlockItem(
                editor=self,
                var_factory=self.var_factory,
                subsys=block_model,
                api_object=self.api_object,
                mode=self.mode,
                name=item_name,
                position_changed_callback=self.build_position_changed_callback(block_model.uid)
            )

            self.block_counters[blocktype] = count
            block_item.set_subsystem(block_model)
            block_item.position_changed_callback = self.build_position_changed_callback(block_model.uid)
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

        else:
            return

    def create_generic_block_item(self, block_type: BlockType, x_pos, y_pos) -> graph.GenericBlockItem | None:
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
            item = graph.GenericBlockItem(
                editor=self,
                var_factory=self.var_factory,
                subsys=model,
                api_object=self.api_object,
                mode=self.mode,
                name=model.name,
                position_changed_callback=self.build_position_changed_callback(model.uid)
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
                                        y_pos: float) -> graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem | None:
        """
        Create a Sum item that represents addition and subtraction
        """

        count: int = self.block_counters.get(block_type, 0) + 1
        item_name: str = f"{block_type.name}_{count}"

        template_builder = None
        block_model = None
        name = ""

        if block_type == BlockType.SUM:
            template_builder = BasicBlockTemplates.AdderTemplate(vf=self.var_factory)
        elif block_type == BlockType.PRODUCT:
            template_builder = BasicBlockTemplates.ProductTemplate(vf=self.var_factory)

        if template_builder is not None:
            dialog = DynTemplatesEditorDialog(name, template_builder.params)
            dialog.exec()
            template = template_builder.eval()
            block_model = template

        if block_model is not None and len(block_model.in_vars) <= 3:
            round_base_op_item: graph.RoundBaseArithmeticOpItem = graph.RoundBaseArithmeticOpItem(var_factory=self.var_factory,
                                                                                      subsys=block_model,
                                                                                      block_type=block_type,
                                                                                      editor=self,
                                                                                      position_changed_callback=self.build_position_changed_callback(
                                                                                          block_model.uid))

            self.block_counters[block_type] = count
            graph.RoundBaseArithmeticOpItem.position_changed_callback = self.build_position_changed_callback(block_model.uid)
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
            rect_base_op_item: graph.RectBaseArithmeticOpItem = graph.RectBaseArithmeticOpItem(var_factory=self.var_factory,
                                                                                   subsys=block_model,
                                                                                   block_type=block_type,
                                                                                   editor=self,
                                                                                   position_changed_callback=self.build_position_changed_callback(
                                                                                       block_model.uid))

            self.block_counters[block_type] = count
            graph.RoundBaseArithmeticOpItem.position_changed_callback = self.build_position_changed_callback(block_model.uid)
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

    def create_block_item_from_blocktype(self, block_type: BlockType, x_pos: float, y_pos: float) -> graph.GenericBlockItem | None:
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

        item_name: str = f"{block_type.name}_{count}"
        block_model: Block | None = create_block_of_type(
            var_factory=self.var_factory,
            block_type=block_type,
            item_name=item_name,
            api_object=self.api_object,
        )
        self.block_counters[block_type] = count

        # no we have the name and the block
        if block_model is not None:
            self.main_block.add(block_model)
            if block_type in self.UNARY_MATH_BLOCK_TYPES:
                item = graph.UnOpItem(
                    editor=self,
                    var_factory=self.var_factory,
                    subsys=block_model,
                    api_object=self.api_object,
                    mode=self.mode,
                    block_type=block_type,
                    name=block_model.name,
                    position_changed_callback=self.build_position_changed_callback(block_model.uid)
                )

            else:
                item = graph.GenericBlockItem(
                    editor=self,
                    var_factory=self.var_factory,
                    subsys=block_model,
                    api_object=self.api_object,
                    mode=self.mode,
                    name=block_model.name,
                    position_changed_callback=self.build_position_changed_callback(block_model.uid)
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

    def create_block_item(self, block_type: BlockType, x_pos: float, y_pos: float) -> graph.BlockItem | None:
        """
        Create and place a block item in the canvas scene.

        :param block_type:
        :param x_pos:
        :param y_pos:
        :return:
        """
        count: int = self.block_counters.get(block_type, 0) + 1
        item_name: str = f"{block_type.name}_{count}"
        block_item: graph.BlockItem = graph.BlockItem(editor=self, var_factory=self.var_factory, api_object=self.api_object,
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
            block_item.position_changed_callback = self.build_position_changed_callback(block_model.uid)
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

    def connect_items(self, items_list: List[graph.BlockItem | graph.GenericBlockItem]):
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
                        self.create_conn_items(item_2, item_1, power_flow_pairs)

    def create_conn_items(
            self,
            item_source: graph.BlockItem | graph.GenericBlockItem,
            item_dest: graph.BlockItem | graph.GenericBlockItem,
            pairs: List[tuple[Var, Var]],
    ) -> None:
        """
        Create missing connection items for two visible symbolic blocks.

        Every inferred connection is delegated to
        :meth:`attach_new_connection_item` so inferred, live, and restored
        wires share one symbolic-registration and persistence path.

        :param item_source: Graphics item that owns the source output port.
        :param item_dest: Graphics item that owns the destination input port.
        :param pairs: Symbolic source-target variable pairs to connect.
        :return: None.
        """
        source_var: Var
        target_var: Var
        port: graph.PortItem

        if item_source.subsys is None or item_dest.subsys is None:
            return
        else:
            pass

        for source_var, target_var in pairs:
            source_port: graph.PortItem | None = None
            target_port: graph.PortItem | None = None

            # Resolve the source through durable visible-variable equivalence.
            for port in item_source.outputs:
                if (source_port is None
                        and vars_match_for_visible_connection(
                            left_var=port.base_var,
                            right_var=source_var,
                        )):
                    source_port = port
                else:
                    pass

            # Resolve the destination independently because save/reopen can
            # materialize a different Var object for the same logical alias.
            for port in item_dest.inputs:
                if (target_port is None
                        and vars_match_for_visible_connection(
                            left_var=port.base_var,
                            right_var=target_var,
                        )):
                    target_port = port
                else:
                    pass

            if source_port is not None and target_port is not None:
                connection: graph.ConnectionItem = graph.ConnectionItem(
                    source_port=source_port,
                    target_port=target_port,
                    diagram=self.diagram,
                    editor=self,
                )
                self.attach_new_connection_item(item=connection)
            else:
                pass

    def generate_block_item_for_block(self, block_model: Block,
                                      x_pos: float,
                                      y_pos: float) -> graph.GenericBlockItem | graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem | graph.UnOpItem:
        """
        Create and place a block item in the canvas scene.

        :param block_model:
        :param x_pos: pre-computed x position (Sugiyama layout).
        :param y_pos: pre-computed y position (Sugiyama layout).
        :return:
        """
        if self.is_root_editor and self._is_root_container_block(block_model):
            raise ValueError("Root dynamic editor container block must never be rendered as one canvas block")
        else:
            pass

        item_name: str = f"{block_model.name}"

        block_type = self._block2blocktype.get(block_model.uid, None)

        if block_type == BlockType.SUM or block_type == BlockType.PRODUCT:

            count: int = self.block_counters.get(block_type, 0) + 1

            item: graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem | graph.UnOpItem | graph.GenericBlockItem

            if len(block_model.in_vars) <= 3:
                item = graph.RoundBaseArithmeticOpItem(
                    var_factory=self.var_factory,
                    subsys=block_model,
                    block_type=block_type,
                    editor=self,
                    position_changed_callback=self.build_position_changed_callback(
                        block_model.uid))
            else:
                item = graph.RectBaseArithmeticOpItem(
                    var_factory=self.var_factory,
                    subsys=block_model,
                    block_type=block_type,
                    editor=self,
                    position_changed_callback=self.build_position_changed_callback(
                        block_model.uid))

            self.block_counters[block_type] = count
            item.recolour()
            self.diagram.add_node(
                name=item_name,
                x=x_pos,
                y=y_pos,
                tpe=block_type.name,
                device_uid=block_model.uid
            )

        elif block_type in self.UNARY_MATH_BLOCK_TYPES:
            assert block_type is not None
            unary_block_type: BlockType = block_type

            item = graph.UnOpItem(
                editor=self,
                var_factory=self.var_factory,
                subsys=block_model,
                api_object=self.api_object,
                mode=self.mode,
                block_type=unary_block_type,
                name=item_name,
                position_changed_callback=self.build_position_changed_callback(block_model.uid)
            )
            self.diagram.add_node(
                name=item_name,
                x=x_pos,
                y=y_pos,
                tpe=unary_block_type.name,
                device_uid=block_model.uid
            )

        else:

            item = graph.GenericBlockItem(
                editor=self,
                var_factory=self.var_factory,
                subsys=block_model,
                api_object=self.api_object,
                mode=self.mode,
                name=item_name,
                position_changed_callback=self.build_position_changed_callback(block_model.uid)
            )
            self.diagram.add_node(
                name=item_name,
                x=x_pos,
                y=y_pos,
                tpe=block_type.name if block_type is not None else "",
                device_uid=block_model.uid
            )

        # The symbolic block has to be attached first so the graphics item can build its ports from it.

        item.setPos(QtCore.QPointF(x_pos, y_pos))
        item.recolour()
        self.scene.addItem(item)
        self.mark_unapplied_changes()

        return item


    def generate_ext_conn_block_item_for_block(self, block_model: Block,
                                      x_pos: float,
                                      y_pos: float) -> graph.BlockItem:
        """
        Create and place a block item in the canvas scene.

        :param block_model:
        :param x_pos: Optional pre-computed x position (Sugiyama layout).
        :param y_pos: Optional pre-computed y position (Sugiyama layout).
        :return:
        """
        item_name: str = f"{block_model.name}"


        item: graph.ProtectedConnectionBlockItem = graph.ProtectedConnectionBlockItem(editor=self,
                                                                                            var_factory=self.var_factory,
                                                                                            name=item_name,
                                                                                            mode=self.mode,
                                                                                            api_object=self.api_object)
        item.set_subsystem(block_model)
        item.position_changed_callback = self.build_position_changed_callback(block_model.uid)
        item.build_item()

        item.setPos(QtCore.QPointF(x_pos, y_pos))
        item.recolour()
        self.scene.addItem(item)

        # Keep the diagram synchronized so later features can rebuild from the same data source.
        block_type = self._get_layout_block_kind(block_model)
        self.diagram.add_node(
            name=item_name,
            x=x_pos,
            y=y_pos,
            tpe=block_type,
            device_uid=block_model.uid
        )
        return item

    def _get_layout_block_kind(self, block_model: Block) -> str:
        if len(block_model.out_vars) > 0 and len(block_model.in_vars) == 0:
            return BlockType.INPUT_CONN.name
        if len(block_model.in_vars) > 0 and len(block_model.out_vars) == 0:
            return BlockType.OUTPUT_CONN.name
        return "internal"

    def _get_layout_block_dimensions(self, block_model: Block) -> tuple[float, float]:
        """
        Estimate the complete visible size of one block for automatic layout.

        The graphics item grows vertically with its largest port column and can
        draw its name below the body. Supplying those real dimensions to the
        layered engine prevents sibling blocks and their captions from being
        placed on top of each other during the first template bootstrap.

        :param block_model: Symbolic block represented by one layout node.
        :return: Estimated ``(width, height)`` including the visible caption.
        """
        font_metrics: QtGui.QFontMetricsF = QtGui.QFontMetricsF(QtWidgets.QApplication.font())
        maximum_input_label_width: float = 0.0
        maximum_output_label_width: float = 0.0
        port_rows: int = max(len(block_model.in_vars), len(block_model.out_vars), 1)
        block_var: Var

        for block_var in block_model.in_vars:
            visible_name: str = graph.truncate_port_label(
                block_var.name,
                graph.EditorGraphicsCommonFeatures.PORT_LABEL_MAX_CHARS,
            )
            maximum_input_label_width = max(
                maximum_input_label_width,
                font_metrics.horizontalAdvance(visible_name),
            )

        for block_var in block_model.out_vars:
            visible_name = graph.truncate_port_label(
                block_var.name,
                graph.EditorGraphicsCommonFeatures.PORT_LABEL_MAX_CHARS,
            )
            maximum_output_label_width = max(
                maximum_output_label_width,
                font_metrics.horizontalAdvance(visible_name),
            )

        body_width: float = max(
            graph.EditorGraphicsCommonFeatures.BLOCK_MIN_WIDTH,
            maximum_input_label_width + maximum_output_label_width + 28.0,
        )
        body_height: float = max(
            graph.EditorGraphicsCommonFeatures.BLOCK_MIN_HEIGHT,
            graph.EditorGraphicsCommonFeatures.BLOCK_HEADER_HEIGHT
            + graph.EditorGraphicsCommonFeatures.BLOCK_PORT_SECTION_PADDING
            + float(port_rows) * graph.EditorGraphicsCommonFeatures.BLOCK_PORT_ROW_HEIGHT,
        )
        caption_width: float = font_metrics.horizontalAdvance(block_model.name) + 20.0
        caption_height: float = font_metrics.height() + 10.0
        return max(body_width, caption_width), body_height + caption_height

    def _build_elk_layout_graph(
        self,
        child_blocks: List[Block],
        input_output_blocks: List[Block],
    ) -> SugiyamaGraph:
        layout_nodes: List[SugiyamaNode] = list()
        layout_edges: List[SugiyamaEdge] = list()
        all_blocks: List[Block] = list(child_blocks) + list(input_output_blocks)
        out_index_by_uid: Dict[int, Dict[int, int]] = dict()
        in_index_by_uid: Dict[int, Dict[int, int]] = dict()
        shared_out_refs: Dict[object, List[tuple[int, int]]] = dict()
        shared_in_refs: Dict[object, List[tuple[int, int]]] = dict()
        pf_out_refs: Dict[object, List[tuple[int, int]]] = dict()
        pf_in_refs: Dict[object, List[tuple[int, int]]] = dict()

        for block_model in all_blocks:
            block_width: float
            block_height: float
            block_width, block_height = self._get_layout_block_dimensions(block_model=block_model)
            ports: List[SugiyamaPort] = list()
            out_uid_lookup: Dict[int, int] = dict()
            in_uid_lookup: Dict[int, int] = dict()
            for port_index, in_var in enumerate(block_model.in_vars):
                in_uid_lookup[in_var.uid] = port_index
                if in_var.shared_ref is not None:
                    shared_in_refs.setdefault(in_var.shared_ref, list()).append((block_model.uid, port_index))
                if in_var.ref is not None:
                    pf_in_refs.setdefault(in_var.ref, list()).append((block_model.uid, port_index))
                ports.append(
                    SugiyamaPort(
                        identifier=f"{block_model.uid}:in:{port_index}",
                        width=6.0,
                        height=6.0,
                        properties={
                            "role": "input",
                            "port_index": port_index,
                            "var_uid": in_var.uid,
                            "var_ref": in_var.ref,
                            "shared_ref": in_var.shared_ref,
                        },
                        layout_options={
                            "org.vera.sugiyama.port.side": "WEST",
                        },
                    )
                )
            for port_index, out_var in enumerate(block_model.out_vars):
                out_uid_lookup[out_var.uid] = port_index
                if out_var.shared_ref is not None:
                    shared_out_refs.setdefault(out_var.shared_ref, list()).append((block_model.uid, port_index))
                if out_var.ref is not None:
                    pf_out_refs.setdefault(out_var.ref, list()).append((block_model.uid, port_index))
                ports.append(
                    SugiyamaPort(
                        identifier=f"{block_model.uid}:out:{port_index}",
                        width=6.0,
                        height=6.0,
                        properties={
                            "role": "output",
                            "port_index": port_index,
                            "var_uid": out_var.uid,
                            "var_ref": out_var.ref,
                            "shared_ref": out_var.shared_ref,
                        },
                        layout_options={
                            "org.vera.sugiyama.port.side": "EAST",
                        },
                    )
                )
            layout_nodes.append(
                SugiyamaNode(
                    identifier=str(block_model.uid),
                    width=block_width,
                    height=block_height,
                    ports=ports,
                    properties={
                        "name": block_model.name,
                        "kind": self._get_layout_block_kind(block_model),
                    },
                    layout_options={
                        "org.vera.sugiyama.portConstraints": "FIXED_ORDER",
                    },
                )
            )
            out_index_by_uid[block_model.uid] = out_uid_lookup
            in_index_by_uid[block_model.uid] = in_uid_lookup

        edge_uid = 1
        seen_edges: set[tuple[int, int, int, int]] = set()
        def add_edges_from_maps(
            source_map: Dict[object, List[tuple[int, int]]],
            target_map: Dict[object, List[tuple[int, int]]],
        ) -> None:
            nonlocal edge_uid
            for ref_value, sources in source_map.items():
                targets = target_map.get(ref_value, list())
                if not targets:
                    continue
                for source_uid, source_port_index in sources:
                    for target_uid, target_port_index in targets:
                        if source_uid == target_uid:
                            continue
                        edge_key = (
                            source_uid,
                            source_port_index,
                            target_uid,
                            target_port_index,
                        )
                        if edge_key in seen_edges:
                            continue
                        seen_edges.add(edge_key)
                        layout_edges.append(
                            SugiyamaEdge(
                                identifier=str(edge_uid),
                                sources=[f"{source_uid}:out:{source_port_index}"],
                                targets=[f"{target_uid}:in:{target_port_index}"],
                                properties={
                                    "source_uid": source_uid,
                                    "source_port_index": source_port_index,
                                    "target_uid": target_uid,
                                    "target_port_index": target_port_index,
                                },
                            )
                        )
                        edge_uid += 1

        add_edges_from_maps(shared_out_refs, shared_in_refs)
        add_edges_from_maps(pf_out_refs, pf_in_refs)

        return SugiyamaGraph(
            identifier="dynamic-block-editor",
            children=layout_nodes,
            edges=layout_edges,
            layout_options={
                "org.vera.sugiyama.algorithm": "layered",
                "org.vera.sugiyama.direction": "RIGHT",
                "org.vera.sugiyama.edgeRouting": "ORTHOGONAL",
                "org.vera.sugiyama.layered.layering.strategy": "NETWORK_SIMPLEX",
                "org.vera.sugiyama.layered.nodePlacement.strategy": "BRANDES_KOEPF",
                "org.vera.sugiyama.spacing.nodeNode": 50.0,
                "org.vera.sugiyama.spacing.componentComponent": 80.0,
                "org.vera.sugiyama.layered.spacing.nodeNodeBetweenLayers": 80.0,
            },
        )

    def _connect_items_from_layout(
        self,
        items_by_uid: Dict[int, graph.BlockItem | graph.GenericBlockItem],
        layout_graph: SugiyamaGraph,
    ) -> None:
        for edge in layout_graph.edges:
            src_uid = int(edge.properties["source_uid"])
            dst_uid = int(edge.properties["target_uid"])
            src_port_index = int(edge.properties["source_port_index"])
            dst_port_index = int(edge.properties["target_port_index"])

            src_item = items_by_uid.get(src_uid, None)
            dst_item = items_by_uid.get(dst_uid, None)
            if src_item is None or dst_item is None:
                continue

            try:
                src_port = src_item.outputs[src_port_index]
                dst_port = dst_item.inputs[dst_port_index]
            except IndexError:
                continue

            connection = graph.ConnectionItem(
                source_port=src_port,
                target_port=dst_port,
                diagram=self.diagram,
                con_uid=int(edge.identifier),
                editor=self,
            )
            connection.recolour()
            self.scene.addItem(connection)

    def generate_block_item_for_block_old(self, block_model: Block) -> GenericBlockItem | None:
        """
        Create and place a block item in the canvas scene.

        :param block_model:

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
                position_changed_callback=self.build_position_changed_callback(block_model.uid)
            )

            # The symbolic block has to be attached first so the graphics item can build its ports from it.

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

    def _calculate_next_block_position(self, item: graph.GenericBlockItem) -> tuple[float, float]:
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

        existing_count = sum(1 for i in self.scene.items() if isinstance(i, graph.GenericBlockItem))

        GRID_COLS: int = 3

        row: int = existing_count // GRID_COLS
        col: int = existing_count % GRID_COLS

        total_width: float = GRID_COLS * COL_SPACING
        start_x: float = (SCENE_WIDTH - total_width) / 2

        x: float = start_x + col * COL_SPACING
        y: float = MARGIN_Y + row * ROW_SPACING

        return x, y

    def create_connection_block_item(self, var: Var, block_type: BlockType, x_pos: float,
                                     y_pos: float, blocks_list: List[graph.BlockItem] | None) -> graph.BlockItem | None:
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
            block_item: graph.ProtectedConnectionBlockItem = graph.ProtectedConnectionBlockItem(editor=self,
                                                                                    var_factory=self.var_factory,
                                                                                    name=item_name,
                                                                                    mode=self.mode,
                                                                                    api_object=self.api_object)
            block_model: Block = Block(name=item_name)

            if block_type == BlockType.INPUT_CONN:
                block_model.out_vars.append(var)

            elif block_type == BlockType.OUTPUT_CONN:
                block_model.in_vars.append(var)

            else:
                pass

            if block_model is not None:
                # The symbolic block has to be attached first so the graphics item can build its ports from it.

                block_item.set_subsystem(block_model)
                block_item.position_changed_callback = self.build_position_changed_callback(block_model.uid)
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


    def create_connection_block(self, var: Var, block_type: BlockType, blocks_list: List[Block] | None):
        """
        Create and place a block item in the canvas scene.

        :param var:
        :type var:
        :param block_type:
        :param blocks_list:
        :return:
        """

        block_model: Block = Block()
        block_model.name = f"{var.name}"

        if block_type == BlockType.INPUT_CONN:
            block_model.out_vars.append(var)

        elif block_type == BlockType.OUTPUT_CONN:
            block_model.in_vars.append(var)

        else:
            pass

        block_model.is_root_interface_wrapper = True

        if block_model is not None:
            # The symbolic block has to be attached first so the graphics item can build its ports from it.
            # The editor block is the authoritative model container for later save/rebuild steps.
            self.main_block.add(block_model)
            if blocks_list is not None:
                blocks_list.append(block_model)
            else:
                pass

    def create_template_block_item(self,
                                   template: RmsModelTemplate | EmtModelTemplate | FmuTemplate,
                                   x_pos: float,
                                   y_pos: float) -> graph.BlockItem | graph.GenericBlockItem | None:
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
        item: graph.GenericBlockItem = graph.GenericBlockItem(
            editor=self,
            var_factory=self.var_factory,
            subsys=block_model,
            api_object=self.api_object,
            mode=self.mode,
            name=item_name,
            position_changed_callback=self.build_position_changed_callback(block_model.uid)
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
            tpe=graph.EditorGraphicsCommonFeatures.TEMPLATE_NODE_TYPE,
            device_uid=block_model.uid
        )

        self.mark_unapplied_changes()

        return item

    # TODO: create PV power plant block item

    def _append_emt_branch_side_connection_specs(
            self,
            specs: List[ConnectionVarSpec],
            bus: Bus,
            side: str,
    ) -> None:
        """
        Append EMT connection specs for one branch side.

        The available side-specific refs must mirror the current authoritative
        endpoint bus shell derived from static topology.

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
            v_n: Var | None
            v_a: Var | None
            v_b: Var | None
            v_c: Var | None
            v_n, v_a, v_b, v_c = get_bus_emt_algebraic_vars(bus.emt_model)

            if side == "from":
                if v_n is not None:
                    voltage_refs.append(VarPowerFlowReferenceType.vf_N)
                    current_refs.append(VarPowerFlowReferenceType.if_N)
                else:
                    pass
                if v_a is not None:
                    voltage_refs.append(VarPowerFlowReferenceType.vf_A)
                    current_refs.append(VarPowerFlowReferenceType.if_A)
                else:
                    pass
                if v_b is not None:
                    voltage_refs.append(VarPowerFlowReferenceType.vf_B)
                    current_refs.append(VarPowerFlowReferenceType.if_B)
                else:
                    pass
                if v_c is not None:
                    voltage_refs.append(VarPowerFlowReferenceType.vf_C)
                    current_refs.append(VarPowerFlowReferenceType.if_C)
                else:
                    pass
            elif side == "to":
                if v_n is not None:
                    voltage_refs.append(VarPowerFlowReferenceType.vt_N)
                    current_refs.append(VarPowerFlowReferenceType.it_N)
                else:
                    pass
                if v_a is not None:
                    voltage_refs.append(VarPowerFlowReferenceType.vt_A)
                    current_refs.append(VarPowerFlowReferenceType.it_A)
                else:
                    pass
                if v_b is not None:
                    voltage_refs.append(VarPowerFlowReferenceType.vt_B)
                    current_refs.append(VarPowerFlowReferenceType.it_B)
                else:
                    pass
                if v_c is not None:
                    voltage_refs.append(VarPowerFlowReferenceType.vt_C)
                    current_refs.append(VarPowerFlowReferenceType.it_C)
                else:
                    pass
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

    def create_library_payload_item(self,
                                    payload: BlockType | BasicBlockTemplateDescriptor | RmsModelTemplate | EmtModelTemplate | FmuTemplate,
                                    x_pos: float,
                                    y_pos: float) -> graph.BlockItem | graph.GenericBlockItem | graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem | graph.PairedItem | None:
        """
        Materialize one library payload on the diagram scene.
        """
        if isinstance(payload, BlockType) and payload in self.blocktype2templatebuilder:
            return self.create_item_using_blocktype_wizard(payload, x_pos, y_pos)

        # this ones cannot be included above because they are represented by a different item in the scene
        elif isinstance(payload, BlockType) and payload == BlockType.FROM_GOTO:
            items = self.create_signal_pair_item(x_pos=x_pos, y_pos=y_pos)
            return items[0] if items else None

        elif isinstance(payload, BlockType) and payload == BlockType.SUM:
            return self.create_basic_arithmetic_op_item(BlockType.SUM, x_pos, y_pos)

        elif isinstance(payload, BlockType) and payload == BlockType.PRODUCT:
            return self.create_basic_arithmetic_op_item(BlockType.PRODUCT, x_pos, y_pos)

        elif isinstance(payload, BlockType) and payload == BlockType.GENERIC:
            return self.create_generic_block_item(block_type=payload, x_pos=x_pos, y_pos=y_pos)

        elif isinstance(payload, BlockType):
            return self.create_block_item_from_blocktype(block_type=payload, x_pos=x_pos, y_pos=y_pos)

        elif isinstance(payload, BasicBlockTemplateDescriptor):
            template: EmtModelTemplate = load_basic_block_catalog_template(payload, self.var_factory)
            return self.create_template_block_item(template=template, x_pos=x_pos, y_pos=y_pos)

        elif isinstance(payload, (RmsModelTemplate, EmtModelTemplate, FmuTemplate)):
            return self.create_template_block_item(template=payload, x_pos=x_pos, y_pos=y_pos)
        else:
            return None

    def _merge_signal_pair_connection_sources(
            self,
            obsolete_source_non_mutable_uid: int,
            canonical_source_non_mutable_uid: int,
    ) -> None:
        """
        Move downstream VarFactory edges to the canonical signal-pair identity.

        Parsed legacy models can recreate the From and To variables with equal
        mutable UIDs but different ``non_mutable_uid`` values. Downstream edges
        then remain owned by the To-side identity and no longer receive aliases
        propagated through the From-side identity. This method merges those edge
        lists before both graphical tags are rebound to one symbolic variable.

        :param obsolete_source_non_mutable_uid: Stable UID currently owning edges.
        :param canonical_source_non_mutable_uid: Stable UID selected for the pair.
        :return: None.
        """
        connection_graph: Dict[int, List[Connection]]
        obsolete_connections: List[Connection] | None
        canonical_connections: List[Connection] | None
        obsolete_connection: Connection
        canonical_connection: Connection
        duplicate_target: bool

        if obsolete_source_non_mutable_uid == canonical_source_non_mutable_uid:
            pass
        else:
            connection_graph = self.var_factory.get_connections_dict()
            obsolete_connections = connection_graph.get(
                obsolete_source_non_mutable_uid,
                None,
            )

            if obsolete_connections is None:
                pass
            else:
                canonical_connections = connection_graph.get(
                    canonical_source_non_mutable_uid,
                    None,
                )
                if canonical_connections is None:
                    canonical_connections = list()
                    connection_graph[canonical_source_non_mutable_uid] = canonical_connections
                else:
                    pass

                # A target stable UID identifies one logical edge. Preserve the
                # first saved restoration record and discard duplicate aliases.
                for obsolete_connection in obsolete_connections:
                    duplicate_target = False
                    for canonical_connection in canonical_connections:
                        if (canonical_connection.non_mutable_uid
                                == obsolete_connection.non_mutable_uid):
                            duplicate_target = True
                        else:
                            pass

                    if duplicate_target:
                        pass
                    else:
                        canonical_connections.append(obsolete_connection)

                del connection_graph[obsolete_source_non_mutable_uid]

    def _bind_signal_pair_items(
            self,
            signal_input_item: graph.PairedItem,
            signal_output_items: List[graph.PairedItem],
    ) -> None:
        """
        Bind one From tag and its To tags to one authoritative signal variable.

        :param signal_input_item: From/input tag that owns the canonical variable.
        :param signal_output_items: To/output tags exposing the same signal.
        :return: None.
        """
        canonical_var: Var | None = signal_input_item.get_signal_var()
        signal_output_item: graph.PairedItem
        output_var: Var | None
        bound_output_count: int = 0

        if canonical_var is None or signal_input_item.subsys is None:
            pass
        else:
            for signal_output_item in signal_output_items:
                output_var = signal_output_item.get_signal_var()
                if output_var is None or signal_output_item.subsys is None:
                    pass
                elif (len(signal_output_item.subsys.out_vars) == 1
                      and len(signal_output_item.subsys.in_vars) == 0):
                    # Preserve downstream edges created with a legacy To-side
                    # stable UID before replacing the wrapper-local variable.
                    self._merge_signal_pair_connection_sources(
                        obsolete_source_non_mutable_uid=output_var.non_mutable_uid,
                        canonical_source_non_mutable_uid=canonical_var.non_mutable_uid,
                    )
                    signal_output_item.subsys.out_vars[0] = canonical_var
                    signal_input_item.set_paired_item(signal_output_item)
                    signal_output_item.set_paired_item(signal_input_item)
                    bound_output_count += 1
                else:
                    pass

            if bound_output_count > 0:
                # Replaying the canonical alias now reaches every migrated
                # downstream edge and every detached working-copy variable.
                self._propagate_alias_to_working_tree(
                    source_non_mutable_uid=canonical_var.non_mutable_uid,
                    incoming_uid=canonical_var.uid,
                    incoming_name=canonical_var.name,
                )
                component_non_mutable_uids: set[int] = self._get_alias_component_stable_uids(
                    starting_non_mutable_uids=set([canonical_var.non_mutable_uid]),
                )
                self._refresh_alias_component_displays(
                    component_non_mutable_uids=component_non_mutable_uids,
                )
            else:
                pass

    def _restore_signal_pair_relationships(
            self,
            signal_input_items: List[graph.PairedItem],
            signal_output_items: List[graph.PairedItem],
    ) -> None:
        """
        Restore signal-pair relationships from persistent names and legacy UIDs.

        :param signal_input_items: Rebuilt From/input tags.
        :param signal_output_items: Rebuilt To/output tags.
        :return: None.
        """
        bound_output_ids: set[int] = set()
        signal_input_item: graph.PairedItem
        signal_output_item: graph.PairedItem
        input_suffix: str | None
        output_suffix: str | None
        matching_outputs: List[graph.PairedItem]
        output_var: Var | None
        input_var: Var | None
        candidate_input: graph.PairedItem | None
        candidate_count: int

        # Current files preserve the pair number in From/To block names. This
        # path is deterministic and also supports one From with multiple To tags.
        for signal_input_item in signal_input_items:
            input_suffix = graph.get_signal_pair_suffix(
                block_name=signal_input_item.subsys.name,
                is_signal_input=True,
            )
            matching_outputs = list()

            if input_suffix is None:
                pass
            else:
                for signal_output_item in signal_output_items:
                    output_suffix = graph.get_signal_pair_suffix(
                        block_name=signal_output_item.subsys.name,
                        is_signal_input=False,
                    )
                    if output_suffix == input_suffix:
                        matching_outputs.append(signal_output_item)
                        bound_output_ids.add(id(signal_output_item))
                    else:
                        pass

            if len(matching_outputs) > 0:
                self._bind_signal_pair_items(
                    signal_input_item=signal_input_item,
                    signal_output_items=matching_outputs,
                )
            else:
                pass

        # Older duplicated To blocks could have lost their To-prefix because the
        # visible variable label was saved as the block name. Use mutable UID only
        # when it identifies exactly one From tag; ambiguous matches are ignored.
        for signal_output_item in signal_output_items:
            if id(signal_output_item) in bound_output_ids:
                pass
            else:
                output_var = signal_output_item.get_signal_var()
                candidate_input = None
                candidate_count = 0

                if output_var is None:
                    pass
                else:
                    for signal_input_item in signal_input_items:
                        input_var = signal_input_item.get_signal_var()
                        if input_var is not None and input_var.uid == output_var.uid:
                            candidate_input = signal_input_item
                            candidate_count += 1
                        else:
                            pass

                if candidate_input is not None and candidate_count == 1:
                    self._bind_signal_pair_items(
                        signal_input_item=candidate_input,
                        signal_output_items=list([signal_output_item]),
                    )
                else:
                    pass

    def create_signal_pair_item(self,
                                x_pos: float,
                                y_pos: float) -> tuple[graph.PairedItem, graph.PairedItem] | None:
        """
        Create a signal pair (input + output blocks sharing the same variable).

        :param x_pos: X coordinate for the drop position.
        :param y_pos: Y coordinate for the drop position.
        :return: Tuple of (input_item, output_item) or None on failure.
        """
        count: int = self.block_counters.get(BlockType.FROM_GOTO, 0) + 1
        self.block_counters[BlockType.FROM_GOTO] = count
        item_name: str = str(count)

        blk_in: Block
        blk_out: Block
        blk_in, blk_out = signal_pair(self.var_factory, item_name)

        self.main_block.add(blk_in)
        self.main_block.add(blk_out)

        item_in: graph.PairedItem = graph.PairedItem(editor=self,
                             var_factory=self.var_factory,
                             subsys=blk_in,
                             api_object=self.api_object,
                             mode=self.mode,
                             name=blk_in.name,
                             position_changed_callback=self.build_position_changed_callback(blk_in.uid)
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

        item_out: graph.PairedItem = graph.PairedItem(editor=self,
                              var_factory=self.var_factory,
                              subsys=blk_out,
                              api_object=self.api_object,
                              mode=self.mode,
                              name=blk_out.name,
                              position_changed_callback=self.build_position_changed_callback(blk_out.uid)
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

        self._bind_signal_pair_items(
            signal_input_item=item_in,
            signal_output_items=list([item_out]),
        )

        self.mark_unapplied_changes()
        return item_in, item_out

    def remove_connection_item(self, item: graph.ConnectionItem) -> None:
        """
        Remove a connection and restore the destination symbolic input.

        :param item:
        :return:
        """
        source_port: graph.PortItem | graph.BranchingItem = item.source_port
        target_port: graph.PortItem | graph.BranchingItem = item.target_port

        if item.con_uid in self.diagram.con_data:
            del self.diagram.con_data[item.con_uid]
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

        if isinstance(source_port, graph.PortItem):
            source_port.update_port_visibility()
        else:
            pass

        if isinstance(target_port, graph.PortItem):
            target_port.update_port_visibility()
        else:
            pass

        self.scene.removeItem(item)

        self._unregister_symbolic_connection_between_ports(source_port, target_port)


    def _get_symbolic_var_for_port(self, port: graph.PortItem) -> Var | None:
        """
        Resolve the live symbolic variable represented by one graphics port.

        :param port: Port whose symbolic variable is requested.
        :return: Live working-tree variable, or ``None``.
        """
        block_item: graph.BlockItem | graph.GenericBlockItem | graph.PairedItem | \
            graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem = port.subsystem
        block_model: Block | None = block_item.subsys
        port_var: Var | None = None

        # Read the variable from the concrete port position without exception-driven flow.
        if block_model is None:
            pass
        elif port.is_input:
            if 0 <= port.index < len(block_model.in_vars):
                port_var = block_model.in_vars[port.index]
            else:
                pass
        else:
            if 0 <= port.index < len(block_model.out_vars):
                port_var = block_model.out_vars[port.index]
            else:
                pass

        # Root ovals are views over the root contract, so use the authoritative
        # root variable rather than a stale wrapper-local copy from an old file.
        if port_var is not None and isinstance(block_item, graph.ProtectedConnectionBlockItem):
            block_type: BlockType
            if port.is_input:
                block_type = BlockType.OUTPUT_CONN
            else:
                block_type = BlockType.INPUT_CONN

            authoritative_var: Var | None = self._get_authoritative_root_interface_var(
                block_type=block_type,
                block_model=block_model,
            )
            if authoritative_var is not None:
                port_var = authoritative_var
            else:
                pass
        else:
            pass

        return port_var

    def _resolve_symbolic_connection_vars(self,
                                          source_port: graph.PortItem,
                                          target_port: graph.PortItem) -> tuple[Var, Var] | None:
        """
        Resolve the substitution and incoming variables for one visible wire.

        ``VarFactory.add_connection(var_to_subs, incoming_var)`` propagates the
        incoming variable UID/name into the substituted variable. Network output
        connectors reverse the graphical source/target orientation, so the same
        rule used by the original editor is retained here in one shared helper.

        :param source_port: Graphical source/output port.
        :param target_port: Graphical destination/input port.
        :return: ``(var_to_substitute, incoming_var)`` or ``None``.
        """
        source_var: Var | None = self._get_symbolic_var_for_port(source_port)
        target_var: Var | None = self._get_symbolic_var_for_port(target_port)

        if source_var is None or target_var is None:
            return None
        elif target_var.network_conn:
            return source_var, target_var
        else:
            return target_var, source_var




    def _propagate_alias_to_working_tree(
            self,
            source_non_mutable_uid: int,
            incoming_uid: int,
            incoming_name: str,
    ) -> None:
        """
        Replay one factory alias through every matching working-tree variable.

        :param source_non_mutable_uid: Stable identity that owns outgoing edges.
        :param incoming_uid: Mutable UID propagated through the alias component.
        :param incoming_name: Name propagated through the alias component.
        :return: None.
        """
        # Synchronize the canonical variables kept by the shared factory first.
        self.var_factory.connect_variables_by_uid(
            source_non_mutable_uid,
            incoming_uid,
            incoming_name,
        )

        # Mirror the same graph traversal into the document working copy. The
        # working tree can contain different Var objects with the same stable UID.
        vars_by_uid: Dict[int, List[Var]] = build_working_var_index(self.main_block)
        connection_graph: Dict[int, List[Connection]] = self.var_factory.get_connections_dict()
        pending: List[int] = list([source_non_mutable_uid])
        visited: set[int] = set()
        current_non_mutable_uid: int
        working_vars: List[Var] | None
        working_var: Var
        connection_records: List[Connection] | None
        connection_record: Connection

        while len(pending) > 0:
            current_non_mutable_uid = pending.pop()
            if current_non_mutable_uid not in visited:
                visited.add(current_non_mutable_uid)

                working_vars = vars_by_uid.get(current_non_mutable_uid, None)
                if working_vars is not None:
                    for working_var in working_vars:
                        working_var.uid = incoming_uid
                        working_var.set_name(incoming_name)
                else:
                    pass

                connection_records = connection_graph.get(current_non_mutable_uid, None)
                if connection_records is not None:
                    for connection_record in connection_records:
                        pending.append(connection_record.non_mutable_uid)
                else:
                    pass
            else:
                pass

        # UID mutation changes Var hashes, so restore valid hash buckets afterward.
        rehash_block_tree_var_keyed_dicts(root_block=self.main_block)


    def _find_var_factory_connection(
            self,
            incoming_non_mutable_uid: int,
            substituted_non_mutable_uid: int,
    ) -> Connection | None:
        """
        Return one saved factory edge and remove duplicate reopen records.

        :param incoming_non_mutable_uid: Stable identity owning the edge list.
        :param substituted_non_mutable_uid: Stable identity of the target variable.
        :return: Existing connection record, or ``None``.
        """
        connection_graph: Dict[int, List[Connection]] = self.var_factory.get_connections_dict()
        connections: List[Connection] | None = connection_graph.get(incoming_non_mutable_uid, None)
        first_match: Connection | None = None
        deduplicated: List[Connection] = list()
        connection_record: Connection

        if connections is None:
            return None
        else:
            pass

        # Reopening is idempotent: retain the first matching edge and remove
        # duplicate records left by older restore cycles.
        for connection_record in connections:
            if connection_record.non_mutable_uid == substituted_non_mutable_uid:
                if first_match is None:
                    first_match = connection_record
                    deduplicated.append(connection_record)
                else:
                    pass
            else:
                deduplicated.append(connection_record)

        if len(deduplicated) != len(connections):
            connections[:] = deduplicated
        else:
            pass

        return first_match


    def _get_alias_component_stable_uids(
            self,
            starting_non_mutable_uids: set[int],
    ) -> set[int]:
        """
        Return every stable variable identity reachable from selected sources.

        VarFactory propagation is directional: an incoming variable owns edges
        toward every substituted variable. Starting with both wire endpoints
        keeps this traversal valid for connection and disconnection workflows.

        :param starting_non_mutable_uids: Stable identities at the edited wire.
        :return: Reachable stable identities, including the starting identities.
        """
        connection_graph: Dict[int, List[Connection]] = self.var_factory.get_connections_dict()
        pending: List[int] = list()
        visited: set[int] = set()
        starting_uid: int
        current_uid: int
        connection_records: List[Connection] | None
        connection_record: Connection

        for starting_uid in starting_non_mutable_uids:
            pending.append(starting_uid)

        while len(pending) > 0:
            current_uid = pending.pop()
            if current_uid in visited:
                pass
            else:
                visited.add(current_uid)
                connection_records = connection_graph.get(current_uid, None)
                if connection_records is None:
                    pass
                else:
                    for connection_record in connection_records:
                        pending.append(connection_record.non_mutable_uid)

        return visited

    def _refresh_alias_component_displays(
            self,
            component_non_mutable_uids: set[int],
    ) -> None:
        """
        Refresh every scene block that displays one variable in an alias component.

        Updating only the newly edited wire endpoints is insufficient for a
        signal pair because the To tag can already feed several downstream
        blocks. Their symbolic variables change through VarFactory and their
        visible labels and tooltips must be refreshed in the same operation.

        :param component_non_mutable_uids: Stable identities changed by alias propagation.
        :return: None.
        """
        scene_item: QGraphicsItem
        block_item: graph.BlockItem | graph.GenericBlockItem | graph.PairedItem | \
            graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem
        block_model: Block | None
        var_groups: tuple[List[Var], List[Var]]
        var_group: List[Var]
        model_var: Var
        has_matching_var: bool
        interface_var: Var | None

        for scene_item in self.scene.items():
            if isinstance(
                    scene_item,
                    (graph.BlockItem,
                     graph.GenericBlockItem,
                     graph.PairedItem,
                     graph.RoundBaseArithmeticOpItem,
                     graph.RectBaseArithmeticOpItem),
            ):
                block_item = scene_item
                block_model = block_item.subsys
                has_matching_var = False

                if block_model is None:
                    pass
                else:
                    var_groups = (block_model.in_vars, block_model.out_vars)
                    for var_group in var_groups:
                        for model_var in var_group:
                            if model_var.non_mutable_uid in component_non_mutable_uids:
                                has_matching_var = True
                            else:
                                pass

                if has_matching_var:
                    block_item.refresh_port_metadata()
                    if isinstance(block_item, graph.ProtectedConnectionBlockItem):
                        interface_var = block_item.get_interface_var()
                        if interface_var is not None and block_item.subsys is not None:
                            block_item.subsys.set_name(interface_var.name)
                            block_item.refresh_block_name()
                        else:
                            pass
                    else:
                        pass
                else:
                    pass
            else:
                pass

        self.scene.update()

    def _refresh_connection_endpoint_displays(
            self,
            source_port: graph.PortItem,
            target_port: graph.PortItem,
    ) -> None:
        """
        Refresh wire endpoints and any signal-pair downstream displays.

        Normal wires only require their two endpoint blocks to refresh. Signal
        pairs are different because reconnecting the From tag changes every To
        tag and every block already fed by those tags, so their full alias
        component must be refreshed.

        :param source_port: Source endpoint.
        :param target_port: Target endpoint.
        :return: None.
        """
        source_block_item: graph.BlockItem | graph.GenericBlockItem | graph.PairedItem | \
            graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem = source_port.subsystem
        target_block_item: graph.BlockItem | graph.GenericBlockItem | graph.PairedItem | \
            graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem = target_port.subsystem
        has_signal_pair_endpoint: bool = (
            isinstance(source_block_item, graph.PairedItem)
            or isinstance(target_block_item, graph.PairedItem)
        )
        starting_non_mutable_uids: set[int] = set()
        source_var: Var | None
        target_var: Var | None
        component_non_mutable_uids: set[int]
        refreshed_item_ids: set[int] = set()
        block_item: graph.BlockItem | graph.GenericBlockItem | graph.PairedItem | \
            graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem
        block_item_id: int
        interface_var: Var | None

        if has_signal_pair_endpoint:
            source_var = self._get_symbolic_var_for_port(source_port)
            target_var = self._get_symbolic_var_for_port(target_port)

            if source_var is not None:
                starting_non_mutable_uids.add(source_var.non_mutable_uid)
            else:
                pass

            if target_var is not None:
                starting_non_mutable_uids.add(target_var.non_mutable_uid)
            else:
                pass

            component_non_mutable_uids = self._get_alias_component_stable_uids(
                starting_non_mutable_uids=starting_non_mutable_uids,
            )
            self._refresh_alias_component_displays(
                component_non_mutable_uids=component_non_mutable_uids,
            )
        else:
            # Non-paired connections retain the cheaper endpoint-only refresh.
            for block_item in (source_block_item, target_block_item):
                block_item_id = id(block_item)
                if block_item_id in refreshed_item_ids:
                    pass
                else:
                    refreshed_item_ids.add(block_item_id)
                    block_item.refresh_port_metadata()
                    if isinstance(block_item, graph.ProtectedConnectionBlockItem):
                        interface_var = block_item.get_interface_var()
                        if interface_var is not None and block_item.subsys is not None:
                            block_item.subsys.set_name(interface_var.name)
                            block_item.refresh_block_name()
                        else:
                            pass
                    else:
                        pass

            self.scene.update()


    def _register_symbolic_connection_between_ports(
            self,
            source_port: graph.PortItem,
            target_port: graph.PortItem,
    ) -> None:
        """
        Register one symbolic edge and replay it into the working block tree.

        :param source_port: Source output port.
        :param target_port: Target input port.
        :return: None.
        """
        resolved_vars: tuple[Var, Var] | None = self._resolve_symbolic_connection_vars(
            source_port=source_port,
            target_port=target_port,
        )
        if resolved_vars is None:
            return
        else:
            pass

        var_to_substitute: Var
        incoming_var: Var
        var_to_substitute, incoming_var = resolved_vars
        existing_connection: Connection | None = self._find_var_factory_connection(
            incoming_non_mutable_uid=incoming_var.non_mutable_uid,
            substituted_non_mutable_uid=var_to_substitute.non_mutable_uid,
        )

        # Add the graph edge only once, but replay it for every working-copy rebuild.
        if existing_connection is None:
            self.var_factory.add_connection(var_to_substitute, incoming_var)
        else:
            pass

        self._propagate_alias_to_working_tree(
            source_non_mutable_uid=incoming_var.non_mutable_uid,
            incoming_uid=incoming_var.uid,
            incoming_name=incoming_var.name,
        )

        self._record_root_interface_connection_intent(source_port=source_port,
                                                      target_port=target_port,
                                                      suppressed=False)


    def _unregister_symbolic_connection_between_ports(
            self,
            source_port: graph.PortItem | graph.BranchingItem,
            target_port: graph.PortItem | graph.BranchingItem,
    ) -> None:
        """
        Remove one symbolic edge and restore its detached working-tree identity.

        :param source_port: Source port.
        :param target_port: Target port.
        :return: None.
        """
        if not isinstance(source_port, graph.PortItem) or not isinstance(target_port, graph.PortItem):
            return
        else:
            pass

        resolved_vars: tuple[Var, Var] | None = self._resolve_symbolic_connection_vars(
            source_port=source_port,
            target_port=target_port,
        )
        if resolved_vars is None:
            return
        else:
            pass

        var_to_disconnect: Var
        outgoing_var: Var
        var_to_disconnect, outgoing_var = resolved_vars
        connection_record: Connection | None = self._find_var_factory_connection(
            incoming_non_mutable_uid=outgoing_var.non_mutable_uid,
            substituted_non_mutable_uid=var_to_disconnect.non_mutable_uid,
        )

        # VarFactory restores its canonical target before deleting the edge.
        self.var_factory.remove_connection(var_to_disconnect, outgoing_var)

        # Mirror the saved pre-connection identity into detached working-copy vars.
        if connection_record is not None:
            self._propagate_alias_to_working_tree(
                source_non_mutable_uid=var_to_disconnect.non_mutable_uid,
                incoming_uid=connection_record.uid,
                incoming_name=connection_record.name,
            )
        else:
            pass

        self._refresh_connection_endpoint_displays(source_port, target_port)
        self._record_root_interface_connection_intent(source_port=source_port,
                                                      target_port=target_port,
                                                      suppressed=True)

    def _record_root_interface_connection_intent(self,
                                                 source_port: graph.PortItem,
                                                 target_port: graph.PortItem,
                                                 suppressed: bool) -> None:
        """
        Persist one USER root-interface connection intent.

        :param source_port: Source port of the connection.
        :param target_port: Target port of the connection.
        :param suppressed: Whether the intent is being disabled.
        :return: None.
        """
        root_ref: VarPowerFlowReferenceType | None = None
        root_direction: str | None = None
        internal_block_uid: int | None = None
        internal_port_direction: str | None = None
        internal_port_index: int | None = None
        source_block: Block | None = None
        target_block: Block | None = None
        entry: Dict[str, Any]
        kept_entries: List[Dict[str, Any]] = list()
        template_override_applied: bool = False
        existing_entry: Dict[str, Any]

        source_block = None if source_port.subsystem is None else source_port.subsystem.subsys
        target_block = None if target_port.subsystem is None else target_port.subsystem.subsys

        if is_root_interface_wrapper_block(source_block):
            root_ref = self._get_semantic_root_interface_reference(
                wrapper_block=source_block,
                block_type=BlockType.INPUT_CONN,
            )
            if root_ref is not None:
                root_direction = "input"
                if target_block is not None:
                    internal_block_uid = target_block.uid
                    internal_port_direction = _get_port_direction(is_output=False)
                    internal_port_index = target_port.index
                else:
                    pass
            else:
                pass
        else:
            if is_root_interface_wrapper_block(target_block):
                root_ref = self._get_semantic_root_interface_reference(
                    wrapper_block=target_block,
                    block_type=BlockType.OUTPUT_CONN,
                )
                if root_ref is not None:
                    root_direction = "output"
                    if source_block is not None:
                        internal_block_uid = source_block.uid
                        internal_port_direction = _get_port_direction(is_output=True)
                        internal_port_index = source_port.index
                    else:
                        pass
                else:
                    pass
            else:
                pass

        if root_ref is None or root_direction is None or internal_block_uid is None or internal_port_direction is None or internal_port_index is None:
            return
        else:
            pass

        if suppressed:
            for existing_entry in self.main_block.connection_intents:
                if not isinstance(existing_entry, dict):
                    pass
                elif existing_entry.get("origin", None) != DynamicConnectionIntentOrigin.TEMPLATE_DERIVED.value:
                    pass
                elif existing_entry.get("root_ref", None) != _build_root_ref_value(root_ref):
                    pass
                elif existing_entry.get("root_direction", None) != root_direction:
                    pass
                elif existing_entry.get("internal_block_uid", None) != internal_block_uid:
                    pass
                elif existing_entry.get("internal_port_direction", None) != internal_port_direction:
                    pass
                elif existing_entry.get("internal_port_index", None) != internal_port_index:
                    pass
                else:
                    existing_entry["suppressed"] = True
                    template_override_applied = True

            if template_override_applied:
                normalize_dynamic_connection_intents(self.main_block)
                return
            else:
                pass

        entry = build_dynamic_connection_intent_record(
            origin=DynamicConnectionIntentOrigin.USER,
            root_ref=root_ref,
            root_direction=root_direction,
            internal_block_uid=internal_block_uid,
            internal_port_direction=internal_port_direction,
            internal_port_index=internal_port_index,
            suppressed=suppressed,
        )

        for existing_entry in self.main_block.connection_intents:
            if not isinstance(existing_entry, dict):
                kept_entries.append(existing_entry)
            elif existing_entry.get("origin", None) != DynamicConnectionIntentOrigin.USER.value:
                kept_entries.append(existing_entry)
            elif existing_entry.get("root_ref", None) != entry.get("root_ref", None):
                kept_entries.append(existing_entry)
            elif existing_entry.get("root_direction", None) != entry.get("root_direction", None):
                kept_entries.append(existing_entry)
            elif existing_entry.get("internal_block_uid", None) != entry.get("internal_block_uid", None):
                kept_entries.append(existing_entry)
            elif existing_entry.get("internal_port_direction", None) != entry.get("internal_port_direction", None):
                kept_entries.append(existing_entry)
            elif existing_entry.get("internal_port_index", None) != entry.get("internal_port_index", None):
                kept_entries.append(existing_entry)
            else:
                pass

        kept_entries.append(entry)
        self.main_block.connection_intents = kept_entries
        normalize_dynamic_connection_intents(self.main_block)

    def _record_template_root_interface_connection_intents(self) -> None:
        """
        Record template-derived root-interface intents for currently active template links.

        :return: None.
        """
        if self.mode != DynamicSimulationMode.EMT or not self.is_root_editor:
            return
        else:
            pass

        if self.api_object.emt_template is None:
            return
        else:
            pass

        child_block: Block
        input_index: int
        output_index: int
        input_var: Var
        output_var: Var
        root_ref_value: str | None
        existing_entry: Dict[str, Any] | None
        new_entry: Dict[str, Any]

        for child_block in self.main_block.children:
            if is_root_interface_wrapper_block(child_block):
                pass
            else:
                for input_index, input_var in enumerate(child_block.in_vars):
                    if input_var.ref is None:
                        pass
                    else:
                        root_ref_value = _build_root_ref_value(input_var.ref)
                        existing_entry = find_matching_dynamic_connection_intent(
                            block=self.main_block,
                            origin=DynamicConnectionIntentOrigin.TEMPLATE_DERIVED,
                            root_ref_value=root_ref_value,
                            root_direction="input",
                            internal_block_uid=child_block.uid,
                            internal_port_direction="input",
                            internal_port_index=input_index,
                        )
                        if existing_entry is None:
                            new_entry = build_dynamic_connection_intent_record(
                                origin=DynamicConnectionIntentOrigin.TEMPLATE_DERIVED,
                                root_ref=input_var.ref,
                                root_direction="input",
                                internal_block_uid=child_block.uid,
                                internal_port_direction="input",
                                internal_port_index=input_index,
                                suppressed=False,
                            )
                            self.main_block.connection_intents.append(new_entry)
                        else:
                            pass

                for output_index, output_var in enumerate(child_block.out_vars):
                    if output_var.ref is None:
                        pass
                    else:
                        root_ref_value = _build_root_ref_value(output_var.ref)
                        existing_entry = find_matching_dynamic_connection_intent(
                            block=self.main_block,
                            origin=DynamicConnectionIntentOrigin.TEMPLATE_DERIVED,
                            root_ref_value=root_ref_value,
                            root_direction="output",
                            internal_block_uid=child_block.uid,
                            internal_port_direction="output",
                            internal_port_index=output_index,
                        )
                        if existing_entry is None:
                            new_entry = build_dynamic_connection_intent_record(
                                origin=DynamicConnectionIntentOrigin.TEMPLATE_DERIVED,
                                root_ref=output_var.ref,
                                root_direction="output",
                                internal_block_uid=child_block.uid,
                                internal_port_direction="output",
                                internal_port_index=output_index,
                                suppressed=False,
                            )
                            self.main_block.connection_intents.append(new_entry)
                        else:
                            pass

        normalize_dynamic_connection_intents(self.main_block)

    def _rematerialize_root_interface_intents(self) -> bool:
        """
        Rebuild active root-interface wires from persisted intent records.

        :return: ``True`` when any connection item was created.
        """
        if self.mode != DynamicSimulationMode.EMT or not self.is_root_editor:
            return False
        else:
            pass

        changed: bool = False
        entry: Dict[str, Any]
        root_ref_value: str | None
        root_direction: str | None
        internal_block_uid: int | None
        internal_port_direction: str | None
        internal_port_index: int | None
        child_block: Block | None
        wrapper_block: Block | None = None
        wrapper_item: graph.BlockItem | graph.GenericBlockItem | None
        internal_item: graph.BlockItem | graph.GenericBlockItem | None
        source_port: graph.PortItem | None = None
        target_port: graph.PortItem | None = None
        interface_reference: VarPowerFlowReferenceType | None
        candidate_block_type: BlockType | None
        candidate_reference: VarPowerFlowReferenceType | None

        for entry in self.main_block.connection_intents:
            if not isinstance(entry, dict):
                pass
            elif entry.get("suppressed", False):
                pass
            else:
                root_ref_value = entry.get("root_ref", None)
                root_direction = entry.get("root_direction", None)
                internal_block_uid = entry.get("internal_block_uid", None)
                internal_port_direction = entry.get("internal_port_direction", None)
                internal_port_index = entry.get("internal_port_index", None)

                if root_ref_value is None or root_direction is None or internal_block_uid is None or internal_port_direction is None or internal_port_index is None:
                    pass
                else:
                    interface_reference = VarPowerFlowReferenceType(root_ref_value)
                    child_block = self.get_block_from_main_block(internal_block_uid)
                    if child_block is None:
                        pass
                    else:
                        if internal_port_direction in {"input", "output"} and root_direction != internal_port_direction:
                            root_direction = internal_port_direction
                            entry["root_direction"] = root_direction
                        else:
                            pass

                        interface_reference = self._resolve_persisted_intent_interface_reference(
                            persisted_reference=interface_reference,
                            child_block=child_block,
                            internal_port_direction=internal_port_direction,
                            internal_port_index=internal_port_index,
                        )
                        if interface_reference is not None:
                            entry["root_ref"] = interface_reference.value
                        else:
                            pass

                        wrapper_block = None
                        child_candidate: Block
                        for child_candidate in self.main_block.children:
                            if is_root_interface_wrapper_block(child_candidate):
                                if root_direction == "input":
                                    candidate_block_type = BlockType.INPUT_CONN
                                elif root_direction == "output":
                                    candidate_block_type = BlockType.OUTPUT_CONN
                                else:
                                    candidate_block_type = None

                                if candidate_block_type is None:
                                    candidate_reference = None
                                else:
                                    candidate_reference = self._get_semantic_root_interface_reference(
                                        wrapper_block=child_candidate,
                                        block_type=candidate_block_type,
                                    )

                                if candidate_reference == interface_reference:
                                    if root_direction == "input" and len(child_candidate.out_vars) == 1:
                                        wrapper_block = child_candidate
                                    elif root_direction == "output" and len(child_candidate.in_vars) == 1:
                                        wrapper_block = child_candidate
                                    else:
                                        pass
                                else:
                                    pass
                            else:
                                pass

                        if wrapper_block is None:
                            pass
                        else:
                            wrapper_item = self.get_scene_item_by_block_uid(wrapper_block.uid)
                            internal_item = self.get_scene_item_by_block_uid(child_block.uid)
                            if wrapper_item is None or internal_item is None:
                                pass
                            else:
                                if root_direction == "input":
                                    if len(wrapper_item.outputs) > 0 and internal_port_direction == "input" and internal_port_index < len(internal_item.inputs):
                                        source_port = wrapper_item.outputs[0]
                                        target_port = internal_item.inputs[internal_port_index]
                                    else:
                                        pass
                                else:
                                    if root_direction == "output":
                                        if len(wrapper_item.inputs) > 0 and internal_port_direction == "output" and internal_port_index < len(internal_item.outputs):
                                            source_port = internal_item.outputs[internal_port_index]
                                            target_port = wrapper_item.inputs[0]
                                        else:
                                            pass
                                    else:
                                        pass

                                if source_port is None or target_port is None:
                                    pass
                                elif self._connection_exists_between_ports(source_port, target_port):
                                    pass
                                else:
                                    self.attach_new_connection_item(graph.ConnectionItem(source_port=source_port,
                                                                                         target_port=target_port,
                                                                                         diagram=self.diagram,
                                                                                         editor=self))
                                    changed = True

                                source_port = None
                                target_port = None

        normalize_dynamic_connection_intents(self.main_block)
        return changed

    def _resolve_persisted_intent_interface_reference(
            self,
            persisted_reference: VarPowerFlowReferenceType,
            child_block: Block,
            internal_port_direction: str,
            internal_port_index: int,
    ) -> VarPowerFlowReferenceType | None:
        """
        Resolve one persisted intent to the current side-specific root reference.

        Older branch-editor user intents may store a shared bus reference such
        as ``v_A``. The connected internal Pi/template port still carries the
        unambiguous side-specific reference, so it can upgrade the intent to
        ``vf_A`` or ``vt_A`` during reopen.

        :param persisted_reference: Reference stored in the intent record.
        :param child_block: Internal block targeted by the intent.
        :param internal_port_direction: Internal port direction label.
        :param internal_port_index: Internal port index.
        :return: Current root-interface reference, or ``None`` when unavailable.
        """
        expected_inputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        expected_outputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        available_refs: set[VarPowerFlowReferenceType]
        internal_var: Var | None = None

        expected_inputs_by_ref, expected_outputs_by_ref = build_expected_root_emt_interface_for_device(self.api_object)
        available_refs = set(expected_inputs_by_ref.keys()) | set(expected_outputs_by_ref.keys())

        if persisted_reference in available_refs:
            return persisted_reference
        else:
            pass

        if not isinstance(self.api_object, BranchParent):
            return None
        elif internal_port_direction == "input" and 0 <= internal_port_index < len(child_block.in_vars):
            internal_var = child_block.in_vars[internal_port_index]
        elif internal_port_direction == "output" and 0 <= internal_port_index < len(child_block.out_vars):
            internal_var = child_block.out_vars[internal_port_index]
        else:
            pass

        if internal_var is not None and internal_var.ref in available_refs:
            return internal_var.ref
        else:
            return None

    def _canonicalize_persisted_root_interface_intents(self) -> None:
        """
        Upgrade legacy root-interface intents before graphical connection replay.

        Earlier editor builds recorded the graphical port direction instead of
        the root contract direction and persisted shared branch voltage refs.
        Canonicalizing before ``rebuild_scene_from_diagram`` prevents restored
        wires from appending a second, corrected record beside each legacy one.

        :return: None.
        """
        entry: Dict[str, Any]
        root_ref_value: str | None
        internal_block_uid: int | None
        internal_port_direction: str | None
        internal_port_index: int | None
        child_block: Block | None
        persisted_reference: VarPowerFlowReferenceType
        canonical_reference: VarPowerFlowReferenceType | None

        normalize_dynamic_connection_intents(self.main_block)

        for entry in self.main_block.connection_intents:
            root_ref_value = entry.get("root_ref", None)
            internal_block_uid = entry.get("internal_block_uid", None)
            internal_port_direction = entry.get("internal_port_direction", None)
            internal_port_index = entry.get("internal_port_index", None)

            if root_ref_value is None or internal_block_uid is None or internal_port_direction is None or internal_port_index is None:
                pass
            elif internal_port_direction not in {"input", "output"}:
                pass
            else:
                try:
                    persisted_reference = VarPowerFlowReferenceType(root_ref_value)
                except ValueError:
                    continue

                child_block = self.get_block_from_main_block(internal_block_uid)
                if child_block is None:
                    pass
                else:
                    entry["root_direction"] = internal_port_direction
                    canonical_reference = self._resolve_persisted_intent_interface_reference(
                        persisted_reference=persisted_reference,
                        child_block=child_block,
                        internal_port_direction=internal_port_direction,
                        internal_port_index=internal_port_index,
                    )
                    if canonical_reference is not None:
                        entry["root_ref"] = canonical_reference.value
                    else:
                        pass

        normalize_dynamic_connection_intents(self.main_block)

    def supports_routing_graph_connection(self, item: graph.ConnectionItem) -> bool:
        """
        Return whether one connection can be delegated to the new routing engine.

        :param item: Connection item to inspect.
        :return: Delegation state.
        """
        # New connections are expected to be owned by the new routing engine.
        # The only remaining gate here is the current adapter limitation: the
        # Qt bridge still supports only direct port-to-port endpoints.
        if isinstance(item.source_port, graph.PortItem) and isinstance(item.target_port, graph.PortItem):
            return True
        else:
            return False

    def register_connection_item(self, item: graph.ConnectionItem) -> None:
        """
        Register one connection item in the diagram persistence model.

        :param item: Connection item to register.
        :return: None.
        """
        connection_record = self.diagram.con_data.get(item.con_uid, None)
        source_port = item.source_port
        target_port = item.target_port

        if connection_record is None:
            self.diagram.add_branch(
                connectionitem_uid=item.con_uid,
                device_uid_from=source_port.subsystem.subsys.uid,
                device_uid_to=target_port.subsystem.subsys.uid,
                port_number_from=source_port.index,
                port_number_to=target_port.index,
                color=item.pen().color().name(),
            )
            connection_record = self.diagram.con_data.get(item.con_uid, None)
        else:
            connection_record.from_uid = source_port.subsystem.subsys.uid
            connection_record.to_uid = target_port.subsystem.subsys.uid
            connection_record.port_number_from = source_port.index
            connection_record.port_number_to = target_port.index
            connection_record.color = item.pen().color().name()

        if connection_record is None:
            pass
        elif self.supports_routing_graph_connection(item):
            self.persist_connection_routing_graph_payload(item)
        else:
            pass


    def attach_new_connection_item(self, item: graph.ConnectionItem) -> None:
        """
        Attach one newly created connection graphically and symbolically.

        :param item: Connection item to attach.
        :return: None.
        """
        source_port: graph.PortItem | graph.BranchingItem = item.source_port
        target_port: graph.PortItem | graph.BranchingItem = item.target_port

        # The controller owns both symbolic and graphical attachment so every
        # connection creation path applies the same alias semantics.
        if isinstance(source_port, graph.PortItem) and isinstance(target_port, graph.PortItem):
            self._register_symbolic_connection_between_ports(source_port, target_port)
        else:
            pass

        item.recolour()
        self.scene.addItem(item)
        self.register_connection_item(item)

        if isinstance(source_port, graph.PortItem) and isinstance(target_port, graph.PortItem):
            self._refresh_connection_endpoint_displays(source_port, target_port)
        else:
            pass

        if self.supports_routing_graph_connection(item):
            self.sync_connection_with_routing_graph(item)
        else:
            pass


    def restore_connection_item(
            self,
            item: graph.ConnectionItem,
            hydrate_graph_payload: bool,
    ) -> None:
        """
        Restore one persisted connection graphically and symbolically.

        :param item: Connection item to restore.
        :param hydrate_graph_payload: Whether stored routing data must be imported.
        :return: None.
        """
        item.recolour()
        self.scene.addItem(item)
        source_port: graph.PortItem | graph.BranchingItem = item.source_port
        target_port: graph.PortItem | graph.BranchingItem = item.target_port

        # A visible restored wire must rebuild the same VarFactory edge as a live wire.
        if isinstance(source_port, graph.PortItem) and isinstance(target_port, graph.PortItem):
            self._register_symbolic_connection_between_ports(source_port, target_port)
            self._refresh_connection_endpoint_displays(source_port, target_port)
        else:
            pass

        if hydrate_graph_payload:
            self.hydrate_connection_routing_graph_payload(item)
        else:
            pass

    def sync_connection_with_routing_graph(self, item: graph.ConnectionItem) -> bool:
        """
        Synchronize one connection item through the new Qt routing bridge.

        :param item: Connection item to synchronize.
        :return: ``True`` when the new engine updated the path.
        """
        if self.supports_routing_graph_connection(item):
            if isinstance(item.source_port, graph.PortItem) and isinstance(item.target_port, graph.PortItem):
                connection_record = self.diagram.con_data.get(item.con_uid, None)
                session_has_graph: bool = self._qt_routing_session.has_connection(item.con_uid)
                if connection_record is not None and connection_record.routing_payload is not None and not session_has_graph:
                    imported: bool = self._qt_routing_session.import_connection_payload(
                        connection_uid=item.con_uid,
                        payload=dict(connection_record.routing_payload),
                    )
                    if imported:
                        self._qt_routing_session.synchronize_connection_graph(
                            connection_uid=item.con_uid,
                            source_port=item.source_port,
                            destination_port=item.target_port,
                        )
                        painter_path = self._qt_routing_session.build_connection_path(item.con_uid)
                        if painter_path is None:
                            return False
                        else:
                            item.setPath(painter_path)
                            self.persist_connection_routing_graph_payload(item)
                            item._sync_elbow_items()
                            return True
                    else:
                        pass
                else:
                    pass

                self._qt_routing_session.synchronize_connection_graph(
                    connection_uid=item.con_uid,
                    source_port=item.source_port,
                    destination_port=item.target_port,
                )
                painter_path = self._qt_routing_session.build_connection_path(item.con_uid)
                if painter_path is None:
                    return False
                else:
                    item.setPath(painter_path)
                    self.persist_connection_routing_graph_payload(item)
                    item._sync_elbow_items()
                    return True
            else:
                return False
        else:
            return False

    def move_connection_segment_with_routing_graph(
            self,
            item: graph.ConnectionItem,
            segment_index: int,
            delta_x: float,
            delta_y: float,
    ) -> bool:
        """
        Move one connection segment through the new routing engine.

        :param item: Connection item to edit.
        :param segment_index: Segment index inside the primary rendered polyline.
        :param delta_x: Requested horizontal translation.
        :param delta_y: Requested vertical translation.
        :return: ``True`` when the new engine updated the path.
        """
        if self.supports_routing_graph_connection(item):
            if isinstance(item.source_port, graph.PortItem) and isinstance(item.target_port, graph.PortItem):
                self._qt_routing_session.synchronize_connection_graph(
                    connection_uid=item.con_uid,
                    source_port=item.source_port,
                    destination_port=item.target_port,
                )
                ordered_segments = self._qt_routing_session.get_ordered_segments(item.con_uid)
                if 0 <= segment_index < len(ordered_segments):
                    route_segment = ordered_segments[segment_index]
                else:
                    return False

                coordinate_offset: float
                segment_axis = self._qt_routing_session.get_graph(item.con_uid).get_segment_axis(
                    route_segment.get_segment_id()
                ) if self._qt_routing_session.get_graph(item.con_uid) is not None else None
                if segment_axis is None:
                    return False
                elif segment_axis == RoutingAxis.HORIZONTAL:
                    coordinate_offset = float(delta_y)
                else:
                    coordinate_offset = float(delta_x)

                moved = self._qt_routing_session.move_segment(
                    connection_uid=item.con_uid,
                    segment_id=route_segment.get_segment_id(),
                    coordinate_offset=coordinate_offset,
                )
                if moved:
                    painter_path = self._qt_routing_session.build_connection_path(item.con_uid)
                    if painter_path is None:
                        return False
                    else:
                        item.setPath(painter_path)
                        self.persist_connection_routing_graph_payload(item)
                        item._sync_elbow_items()
                        return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def finalize_connection_routing_graph_drag(self, item: graph.ConnectionItem) -> bool:
        """
        Finalize one routing-engine-managed drag by refreshing the connection path.

        :param item: Connection item to refresh.
        :return: ``True`` when the new engine handled the refresh.
        """
        return self.sync_connection_with_routing_graph(item)

    def get_connection_routing_graph_segments(self, item: graph.ConnectionItem) -> List[Tuple[int, QPointF, QPointF]]:
        """
        Return the ordered rendered segments of one routing-graph connection.

        :param item: Connection item to inspect.
        :return: Ordered tuples ``(segment_id, start_point, end_point)``.
        """
        segment_entries: List[Tuple[int, QPointF, QPointF]] = list()
        if self.supports_routing_graph_connection(item):
            route_segment = None
            for route_segment in self._qt_routing_session.get_ordered_segments(item.con_uid):
                segment_points = self._qt_routing_session.get_segment_path_points(
                    item.con_uid,
                    route_segment.get_segment_id(),
                )
                if segment_points is None:
                    pass
                else:
                    segment_entries.append(
                        (
                            route_segment.get_segment_id(),
                            segment_points[0],
                            segment_points[1],
                        )
                    )
            return segment_entries
        else:
            return segment_entries

    def persist_connection_routing_graph_payload(self, item: graph.ConnectionItem) -> bool:
        """
        Persist the serialized routing-graph payload of one connection.

        :param item: Connection item to persist.
        :return: ``True`` when one payload was written.
        """
        if self.supports_routing_graph_connection(item):
            connection_record = self.diagram.con_data.get(item.con_uid, None)
            if connection_record is None:
                return False
            else:
                payload = self._qt_routing_session.export_connection_payload(item.con_uid)
                if payload is None:
                    return False
                else:
                    connection_record.routing_payload = dict(payload)
                    return True
        else:
            return False

    def hydrate_connection_routing_graph_payload(self, item: graph.ConnectionItem) -> bool:
        """
        Hydrate one connection from one persisted routing-graph payload.

        :param item: Connection item to hydrate.
        :return: ``True`` when one payload was imported and rendered.
        """
        if self.supports_routing_graph_connection(item):
            connection_record = self.diagram.con_data.get(item.con_uid, None)
            if connection_record is None:
                return False
            elif connection_record.routing_payload is None:
                return False
            else:
                imported: bool = self._qt_routing_session.import_connection_payload(
                    connection_uid=item.con_uid,
                    payload=dict(connection_record.routing_payload),
                )
                if imported:
                    painter_path = self._qt_routing_session.build_connection_path(item.con_uid)
                    if painter_path is None:
                        return False
                    else:
                        item.setPath(painter_path)
                        item._sync_elbow_items()
                        return True
                else:
                    return False
        else:
            return False

    def unregister_connection_from_routing_graph(self, item: graph.ConnectionItem) -> bool:
        """
        Remove one connection item from the new routing-graph session.

        :param item: Connection item to unregister.
        :return: ``True`` when the session mapping existed and was removed.
        """
        if self.supports_routing_graph_connection(item):
            removed: bool = self._qt_routing_session.remove_connection(item.con_uid)
            return removed
        else:
            return False

    def remove_block_item(self,
                          item: graph.BlockItem | graph.GenericBlockItem | graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem | graph.PairedItem) -> None:
        """
        Remove a block and all of its attached connections.

        :param item:
        :return:
        """
        port: graph.PortItem
        conn: graph.ConnectionItem
        connections_to_remove: List[graph.ConnectionItem] = list()
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

    def _remove_connection_interface_for_block(self,
                                               item: graph.BlockItem | graph.GenericBlockItem | graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem | graph.PairedItem) -> None:
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
                    item: graph.BlockItem | graph.GenericBlockItem | graph.ConnectionItem | graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem | graph.PairedItem) -> None:
        """
        Remove a block or connection from scene and model state.

        :param item:
        :return:
        """
        if isinstance(item, graph.ConnectionItem):
            self.remove_connection_item(item)
            self.mark_unapplied_changes()
        elif isinstance(item, (graph.BlockItem, graph.GenericBlockItem, graph.RoundBaseArithmeticOpItem,
                               graph.RectBaseArithmeticOpItem | graph.PairedItem)):
            self.remove_block_item(item)
            self.mark_unapplied_changes()
        else:
            pass

    def add_connection_vars_rms(self):
        """
        Add a block with bus connection variables to connect the device (RMS)
        :return:
        """

        if isinstance(self.api_object, BranchParent):

            # connect bus variables
            # get bus variables for bus from
            if self.api_object.bus_from.is_dc:
                Vf_dc, _, _ = get_bus_rms_algebraic_vars(self.api_object.bus_from.rms_model)
                if Vf_dc is not None:
                    self.main_block.in_vars.append(Vf_dc)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.Vmf: Vf_dc})
                    # add connection variables
                    Pf = self.var_factory.add_var('net_conn_Pf', VarPowerFlowReferenceType.Pf, True)
                    self.main_block.out_vars.append(Pf)
                    self.main_block.external_mapping.update({VarPowerFlowReferenceType.Pf: Pf})
                else:
                    raise ValueError("Invalid RMS bus model: expected Vdc, None, None")
            else:
                _, Vmf, Vaf = get_bus_rms_algebraic_vars(self.api_object.bus_from.rms_model)

                self.main_block.in_vars.append(Vmf)
                self.main_block.in_vars.append(Vaf)

                self.main_block.external_mapping.update(
                    {VarPowerFlowReferenceType.Vmf: Vmf})
                self.main_block.external_mapping.update(
                    {VarPowerFlowReferenceType.Vaf: Vaf})

                # add connection variables
                Pf = self.var_factory.add_var('net_conn_Pf', VarPowerFlowReferenceType.Pf, True)
                Qf = self.var_factory.add_var('net_conn_Qf', VarPowerFlowReferenceType.Qf, True)

                self.main_block.out_vars.append(Pf)
                self.main_block.out_vars.append(Qf)

                self.main_block.external_mapping.update({VarPowerFlowReferenceType.Pf: Pf})
                self.main_block.external_mapping.update({VarPowerFlowReferenceType.Qf: Qf})

            # get bus variables for bus to
            if self.api_object.bus_to.is_dc:
                Vt_dc, _, _ = get_bus_rms_algebraic_vars(self.api_object.bus_to.rms_model)
                if Vt_dc is not None:
                    self.main_block.in_vars.append(Vt_dc)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.Vt_dc: Vt_dc})
                    # add connection variables
                    Pt = self.var_factory.add_var('net_conn_Pt', VarPowerFlowReferenceType.Pt, True)
                    self.main_block.out_vars.append(Pt)
                    self.main_block.external_mapping.update({VarPowerFlowReferenceType.Pt: Pt})
                else:
                    raise ValueError("Invalid RMS bus model: expected Vdc, None, None")

            else:
                _, Vmt, Vat = get_bus_rms_algebraic_vars(self.api_object.bus_to.rms_model)

                self.main_block.in_vars.append(Vmt)
                self.main_block.in_vars.append(Vat)

                self.main_block.external_mapping.update(
                    {VarPowerFlowReferenceType.Vmt: Vmt})
                self.main_block.external_mapping.update(
                    {VarPowerFlowReferenceType.Vat: Vat})
                # add connection variables
                Pt = self.var_factory.add_var('net_conn_Pt', VarPowerFlowReferenceType.Pt, True)
                Qt = self.var_factory.add_var('net_conn_Qt', VarPowerFlowReferenceType.Qt, True)

                self.main_block.out_vars.append(Pt)
                self.main_block.out_vars.append(Qt)

                self.main_block.external_mapping.update({VarPowerFlowReferenceType.Pt: Pt})
                self.main_block.external_mapping.update({VarPowerFlowReferenceType.Qt: Qt})

        elif isinstance(self.api_object, InjectionParent):

            # connect bus variables

            if self.api_object.bus.is_dc:
                Vdc, _, _ = get_bus_rms_algebraic_vars(self.api_object.bus.rms_model)
                if Vdc is not None:
                    self.main_block.in_vars.append(Vdc)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.Vdc: Vdc})

                    # add connection variables
                    P = self.var_factory.add_var('net_conn_P', VarPowerFlowReferenceType.P, True)

                    self.main_block.out_vars.append(P)
                    self.main_block.external_mapping.update({VarPowerFlowReferenceType.P: P})
            else:
                _, Vm, Va = get_bus_rms_algebraic_vars(self.api_object.bus.rms_model)
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

    def add_connection_vars_emt(self):
        """
        Add a block with bus connection variables to connect the device (EMT)
        :return:
        """

        if isinstance(self.api_object, BranchParent):

            # connect bus variables

            # get bus variables for bus from
            if self.api_object.bus_from.is_dc:
                Vf_dc, _, _, _ = get_bus_emt_algebraic_vars(self.api_object.bus_from.emt_model)

                if Vf_dc is not None:
                    self.main_block.in_vars.append(Vf_dc)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.Vdc: Vf_dc})
                    # add connection variables (currents)
                    If_dc = self.var_factory.add_var('net_conn_If_dc', VarPowerFlowReferenceType.If_dc, True)
                    self.main_block.out_vars.append(If_dc)
                    self.main_block.external_mapping.update({VarPowerFlowReferenceType.If_dc: If_dc})
                else:
                    raise ValueError("Invalid EMT bus model: expected Vdc, None, None, None")
            else:
                vf_N, vf_A, vf_B, vf_C = get_bus_emt_algebraic_vars(self.api_object.bus_from.emt_model)

                if vf_N is not None:
                    self.main_block.in_vars.append(vf_N)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.vf_N: vf_N})
                    # add connection variables (currents)
                    if_N = self.var_factory.add_var('net_conn_if_N', VarPowerFlowReferenceType.if_N, True)
                    self.main_block.out_vars.append(if_N)
                    self.main_block.external_mapping.update({VarPowerFlowReferenceType.if_N: if_N})
                if vf_A is not None:
                    self.main_block.in_vars.append(vf_A)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.vf_A: vf_A})
                    # add connection variables (currents)
                    if_A = self.var_factory.add_var('net_conn_if_A', VarPowerFlowReferenceType.if_A, True)
                    self.main_block.out_vars.append(if_A)
                    self.main_block.external_mapping.update({VarPowerFlowReferenceType.if_A: if_A})
                if vf_B is not None:
                    self.main_block.in_vars.append(vf_B)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.vf_B: vf_B})
                    # add connection variables (currents)
                    if_B = self.var_factory.add_var('net_conn_if_B', VarPowerFlowReferenceType.if_B, True)
                    self.main_block.out_vars.append(if_B)
                    self.main_block.external_mapping.update({VarPowerFlowReferenceType.if_B: if_B})
                if vf_C is not None:
                    self.main_block.in_vars.append(vf_C)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.vf_C: vf_C})
                    # add connection variables (currents)
                    if_C = self.var_factory.add_var('net_conn_if_C', VarPowerFlowReferenceType.if_C, True)
                    self.main_block.out_vars.append(if_C)
                    self.main_block.external_mapping.update({VarPowerFlowReferenceType.if_C: if_C})


            # get bus variables for bus to
            if self.api_object.bus_to.is_dc:
                Vt_dc, _, _, _ = get_bus_emt_algebraic_vars(self.api_object.bus_to.emt_model)

                if Vt_dc is not None:
                    self.main_block.in_vars.append(Vt_dc)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.Vt_dc: Vt_dc})
                    # add connection variables (currents)
                    It_dc = self.var_factory.add_var('net_conn_It_dc', VarPowerFlowReferenceType.It_dc, True)
                    self.main_block.out_vars.append(It_dc)
                    self.main_block.external_mapping.update({VarPowerFlowReferenceType.It_dc: It_dc})
                else:
                    raise ValueError("Invalid EMT bus model: expected Vdc, None, None, None")

            else:
                vt_N, vt_A, vt_B, vt_C = get_bus_emt_algebraic_vars(self.api_object.bus_to.emt_model)

                if vt_N is not None:
                    self.main_block.in_vars.append(vt_N)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.vt_N: vt_N})
                    # add connection variables (currents)
                    it_N = self.var_factory.add_var('net_conn_it_N', VarPowerFlowReferenceType.it_N, True)
                    self.main_block.out_vars.append(it_N)
                    self.main_block.external_mapping.update({VarPowerFlowReferenceType.it_N: it_N})
                if vt_A is not None:
                    self.main_block.in_vars.append(vt_A)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.vt_A: vt_A})
                    # add connection variables (currents)
                    it_A = self.var_factory.add_var('net_conn_it_A', VarPowerFlowReferenceType.it_A, True)
                    self.main_block.out_vars.append(it_A)
                    self.main_block.external_mapping.update({VarPowerFlowReferenceType.it_A: it_A})
                if vt_B is not None:
                    self.main_block.in_vars.append(vt_B)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.vt_B: vt_B})
                    # add connection variables (currents)
                    it_B = self.var_factory.add_var('net_conn_it_B', VarPowerFlowReferenceType.it_B, True)
                    self.main_block.out_vars.append(it_B)
                    self.main_block.external_mapping.update({VarPowerFlowReferenceType.it_B: it_B})
                if vt_C is not None:
                    self.main_block.in_vars.append(vt_C)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.vt_C: vt_C})
                    # add connection variables (currents)
                    it_C = self.var_factory.add_var('net_conn_it_C', VarPowerFlowReferenceType.it_C, True)
                    self.main_block.out_vars.append(it_C)
                    self.main_block.external_mapping.update({VarPowerFlowReferenceType.it_C: it_C})



        elif isinstance(self.api_object, InjectionParent):

            # connect bus variables

            if self.api_object.bus.is_dc:
                Vdc, _, _, _ = get_bus_emt_algebraic_vars(self.api_object.bus.emt_model)

                if Vdc is not None:
                    self.main_block.in_vars.append(Vdc)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.Vdc: Vdc})
                    # add connection variables (currents)
                    Idc = self.var_factory.add_var('net_conn_Idc', VarPowerFlowReferenceType.Idc, True)
                    self.main_block.out_vars.append(Idc)
                    self.main_block.external_mapping.update({VarPowerFlowReferenceType.Idc: Idc})
                else:
                    raise ValueError("Invalid EMT bus model: expected Vdc, None, None, None")
            else:
                v_N, v_A, v_B, v_C = get_bus_emt_algebraic_vars(self.api_object.bus.emt_model)

                if v_N is not None:
                    self.main_block.in_vars.append(v_N)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.v_N: v_N})
                    # add connection variables
                    i_N = self.var_factory.add_var('net_conn_i_N', VarPowerFlowReferenceType.i_N, True)
                    self.main_block.out_vars.append(i_N)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.i_N: i_N})
                if v_A is not None:
                    self.main_block.in_vars.append(v_A)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.v_A: v_A})
                    # add connection variables
                    i_A = self.var_factory.add_var('net_conn_i_A', VarPowerFlowReferenceType.i_A, True)
                    self.main_block.out_vars.append(i_A)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.i_A: i_A})
                if v_B is not None:
                    self.main_block.in_vars.append(v_B)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.v_B: v_B})
                    # add connection variables
                    i_B = self.var_factory.add_var('net_conn_i_B', VarPowerFlowReferenceType.i_B, True)
                    self.main_block.out_vars.append(i_B)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.i_B: i_B})
                if v_C is not None:
                    self.main_block.in_vars.append(v_C)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.v_C: v_C})
                    # add connection variables
                    i_C = self.var_factory.add_var('net_conn_i_C', VarPowerFlowReferenceType.i_C, True)
                    self.main_block.out_vars.append(i_C)
                    self.main_block.external_mapping.update(
                        {VarPowerFlowReferenceType.i_C: i_C})


    def add_connection_vars(self) -> None:
        """
        Add the connection variables required to couple the edited device with the grid.

        :return:
        """
        # specs: List[ConnectionVarSpec]

        if self.mode == DynamicSimulationMode.RMS:
            self.add_connection_vars_rms()
        elif self.mode == DynamicSimulationMode.EMT:
            self.add_connection_vars_emt()


        else:
            raise ValueError(f"Unsupported dynamic editor mode {self.mode}")

    def _compact_initial_layout(self) -> QtCore.QRectF | None:
        interface_items: list[graph.ProtectedConnectionBlockItem] = [
            item for item in self.scene.items()
            if isinstance(item, graph.ProtectedConnectionBlockItem)
        ]

        if not interface_items:
            return None

        bounding_rect = QtCore.QRectF()
        for item in interface_items:
            br = item.sceneBoundingRect()
            bounding_rect = br if bounding_rect.isNull() else bounding_rect.united(br)

        center = bounding_rect.center()

        for item in interface_items:
            offset = item.pos() - center
            item.setPos(center + offset * graph.EditorGraphicsCommonFeatures.INITIAL_LAYOUT_SCALE)

        for node in self.diagram.node_data.values():
            if node.tpe in {BlockType.INPUT_CONN.name, BlockType.OUTPUT_CONN.name}:
                for item in interface_items:
                    if item.subsys.uid == node.device_uid:
                        node.x = item.pos().x()
                        node.y = item.pos().y()
                        break

        new_br = QtCore.QRectF()
        for item in interface_items:
            br = item.sceneBoundingRect()
            new_br = br if new_br.isNull() else new_br.united(br)

        return new_br.adjusted(-graph.EditorGraphicsCommonFeatures.LAYOUT_MARGIN, -graph.EditorGraphicsCommonFeatures.LAYOUT_MARGIN,
                               graph.EditorGraphicsCommonFeatures.LAYOUT_MARGIN, graph.EditorGraphicsCommonFeatures.LAYOUT_MARGIN)

    def _root_interface_layout_uses_bootstrap_positions(self) -> bool:
        """
        Return whether the root EMT interface has no user-authored placement yet.

        The current refactor introduced deterministic bootstrap coordinates at
        X=100/1020 and 100-pixel vertical intervals. Recognizing that exact
        pattern allows existing files opened during the refactor to receive the
        improved compact layout while preserving every manually positioned
        interface.

        :return: ``True`` for a missing or untouched bootstrap interface layout.
        """
        interface_nodes: List[tuple[int, BlockDiagramNode]] = list()
        input_nodes: List[tuple[int, BlockDiagramNode]] = list()
        output_nodes: List[tuple[int, BlockDiagramNode]] = list()
        node_uid: int
        node: BlockDiagramNode
        node_index: int
        expected_x: float
        expected_y: float

        if not self.is_root_editor or self.mode != DynamicSimulationMode.EMT:
            return False
        else:
            pass

        for node_uid, node in self.diagram.node_data.items():
            if node.tpe == BlockType.INPUT_CONN.name:
                input_nodes.append((node_uid, node))
                interface_nodes.append((node_uid, node))
            elif node.tpe == BlockType.OUTPUT_CONN.name:
                output_nodes.append((node_uid, node))
                interface_nodes.append((node_uid, node))
            else:
                pass

        if len(interface_nodes) == 0:
            return True
        else:
            pass

        input_nodes.sort(key=get_block_diagram_node_position_sort_key)
        output_nodes.sort(key=get_block_diagram_node_position_sort_key)

        for node_index, node_entry in enumerate(input_nodes):
            node_uid, node = node_entry
            expected_x = 100.0
            expected_y = 100.0 * float(node_index + 1)
            if abs(node.x - expected_x) > 1e-6 or abs(node.y - expected_y) > 1e-6:
                return False
            else:
                pass

        for node_index, node_entry in enumerate(output_nodes):
            node_uid, node = node_entry
            expected_x = 1020.0
            expected_y = 100.0 * float(node_index + 1)
            if abs(node.x - expected_x) > 1e-6 or abs(node.y - expected_y) > 1e-6:
                return False
            else:
                pass

        return True

    def _layout_root_interface_items_around_content(self) -> bool:
        """
        Place fresh root connection wrappers compactly around model content.

        Existing internal/template blocks remain fixed. Input wrappers form a
        centered column to their left and output wrappers form a centered column
        to their right. An empty root editor uses the same compact two-column
        arrangement without inventing a placeholder block.

        :return: ``True`` when protected connection items were repositioned.
        """
        input_items: List[graph.ProtectedConnectionBlockItem] = list()
        output_items: List[graph.ProtectedConnectionBlockItem] = list()
        content_items: List[QGraphicsItem] = list()
        scene_item: QGraphicsItem
        protected_item: graph.ProtectedConnectionBlockItem
        content_rect: QtCore.QRectF = QtCore.QRectF()
        item_rect: QtCore.QRectF
        input_stack_height: float
        output_stack_height: float
        max_stack_height: float
        max_input_width: float = 0.0
        horizontal_gap: float = 70.0
        vertical_gap: float = 20.0
        empty_column_gap: float = 260.0
        center_y: float
        input_x: float
        output_x: float

        for scene_item in self.scene.items():
            if isinstance(scene_item, graph.ProtectedConnectionBlockItem):
                protected_item = scene_item
                if len(protected_item.outputs) == 1 and len(protected_item.inputs) == 0:
                    input_items.append(protected_item)
                elif len(protected_item.inputs) == 1 and len(protected_item.outputs) == 0:
                    output_items.append(protected_item)
                else:
                    pass
            elif isinstance(scene_item, (
                    graph.BlockItem,
                    graph.GenericBlockItem,
                    graph.RoundBaseArithmeticOpItem,
                    graph.RectBaseArithmeticOpItem,
                    graph.UnOpItem,
                    graph.PairedItem,
            )):
                content_items.append(scene_item)
            else:
                pass

        if len(input_items) == 0 and len(output_items) == 0:
            return False
        else:
            pass

        input_items = self._order_root_interface_items(
            items=input_items,
            block_type=BlockType.INPUT_CONN,
        )
        output_items = self._order_root_interface_items(
            items=output_items,
            block_type=BlockType.OUTPUT_CONN,
        )

        for protected_item in input_items:
            max_input_width = max(max_input_width, protected_item.boundingRect().width())

        input_stack_height = get_centered_connection_stack_height(items=input_items,
                                                                    vertical_gap=vertical_gap)
        output_stack_height = get_centered_connection_stack_height(items=output_items,
                                                                     vertical_gap=vertical_gap)
        max_stack_height = max(input_stack_height, output_stack_height)

        for scene_item in content_items:
            item_rect = scene_item.sceneBoundingRect()
            if content_rect.isNull():
                content_rect = item_rect
            else:
                content_rect = content_rect.united(item_rect)

        if content_rect.isNull():
            center_y = max_stack_height / 2.0
            input_x = 0.0
            output_x = max_input_width + empty_column_gap
        else:
            center_y = content_rect.center().y()
            input_x = content_rect.left() - horizontal_gap - max_input_width
            output_x = content_rect.right() + horizontal_gap

        position_centered_connection_stack(items=input_items,
                                           x_position=input_x,
                                           center_y=center_y,
                                           vertical_gap=vertical_gap)
        position_centered_connection_stack(items=output_items,
                                           x_position=output_x,
                                           center_y=center_y,
                                           vertical_gap=vertical_gap)

        self._refresh_all_visible_connection_paths()

        self.scene.setSceneRect(
            self.scene.itemsBoundingRect().adjusted(
                -graph.EditorGraphicsCommonFeatures.LAYOUT_MARGIN,
                -graph.EditorGraphicsCommonFeatures.LAYOUT_MARGIN,
                graph.EditorGraphicsCommonFeatures.LAYOUT_MARGIN,
                graph.EditorGraphicsCommonFeatures.LAYOUT_MARGIN,
            )
        )
        return True

    def _refresh_all_visible_connection_paths(self) -> None:
        """
        Recalculate every visible wire after a programmatic block layout.

        Qt emits ``ItemPositionChange`` before ``setPos`` commits the new item
        coordinates. The regular block callback can therefore route against the
        previous endpoint during an automatic multi-item layout. A final pass
        after all positions are committed keeps the route graph, painted path,
        and persisted payload synchronized.

        :return: None.
        """
        scene_item: QGraphicsItem
        connection_record: BlockDiagramConnection | None

        for scene_item in self.scene.items():
            if isinstance(scene_item, graph.ConnectionItem):
                self.unregister_connection_from_routing_graph(scene_item)
                connection_record = self.diagram.con_data.get(scene_item.con_uid, None)
                if connection_record is not None:
                    connection_record.routing_payload = None
                else:
                    pass
                scene_item.update_path()
            else:
                pass

    def _order_root_interface_items(
            self,
            items: List[graph.ProtectedConnectionBlockItem],
            block_type: BlockType,
    ) -> List[graph.ProtectedConnectionBlockItem]:
        """
        Order root-interface items by their authoritative semantic references.

        Newly materialized phases must join the same from-side/to-side order as
        a fresh editor. Items that cannot be resolved semantically retain their
        deterministic positional order at the end of the corresponding column.

        :param items: Protected connection items to order.
        :param block_type: Root wrapper direction represented by the items.
        :return: Semantically ordered protected connection items.
        """
        expected_inputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        expected_outputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        ordered_refs: list[VarPowerFlowReferenceType]
        items_by_ref: dict[VarPowerFlowReferenceType, graph.ProtectedConnectionBlockItem] = dict()
        unresolved_items: List[graph.ProtectedConnectionBlockItem] = list()
        ordered_items: List[graph.ProtectedConnectionBlockItem] = list()
        item: graph.ProtectedConnectionBlockItem
        reference: VarPowerFlowReferenceType | None

        expected_inputs_by_ref, expected_outputs_by_ref = build_expected_root_emt_interface_for_device(self.api_object)
        ordered_refs = build_expected_root_interface_ref_order(
            block_type=block_type,
            input_refs=expected_inputs_by_ref,
            output_refs=expected_outputs_by_ref,
        )

        for item in items:
            if item.subsys is None:
                unresolved_items.append(item)
            else:
                reference = self._get_semantic_root_interface_reference(
                    wrapper_block=item.subsys,
                    block_type=block_type,
                )
                if reference is None or reference in items_by_ref:
                    unresolved_items.append(item)
                else:
                    items_by_ref[reference] = item

        for reference in ordered_refs:
            if reference in items_by_ref:
                ordered_items.append(items_by_ref[reference])
            else:
                pass

        unresolved_items.sort(key=get_protected_connection_item_position_sort_key)
        ordered_items.extend(unresolved_items)
        return ordered_items

    def _fit_initial_scene_view(self) -> None:
        """
        Fit every visible diagram block inside the initial editor viewport.

        The fit runs after the first show event because the workspace splitter
        and side panel determine the real canvas size only then. Small diagrams
        retain a maximum 1:1 scale, while larger diagrams are reduced enough to
        make every block visible.

        :return: None.
        """
        if self._prepared_to_delete or self.scene is None or self.view is None:
            self._initial_scene_fit_pending = False
            return
        else:
            pass

        target_rect: QtCore.QRectF = QtCore.QRectF()
        scene_item: QGraphicsItem
        item_rect: QtCore.QRectF
        margin_x: float
        margin_y: float

        if not self._initial_scene_fit_pending:
            return
        else:
            self._initial_scene_fit_pending = False

        for scene_item in self.scene.items():
            if isinstance(scene_item, (
                    graph.BlockItem,
                    graph.GenericBlockItem,
                    graph.RoundBaseArithmeticOpItem,
                    graph.RectBaseArithmeticOpItem,
                    graph.UnOpItem,
                    graph.PairedItem,
            )):
                item_rect = scene_item.sceneBoundingRect()
                if target_rect.isNull():
                    target_rect = item_rect
                else:
                    target_rect = target_rect.united(item_rect)
            else:
                pass

        if target_rect.isNull():
            return
        else:
            pass

        margin_x = max(target_rect.width() * 0.08, 30.0)
        margin_y = max(target_rect.height() * 0.08, 30.0)
        target_rect = target_rect.adjusted(-margin_x, -margin_y, margin_x, margin_y)
        self.scene.setSceneRect(target_rect)
        self.view.resetTransform()
        self.view.fitInView(target_rect, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        if self.view.transform().m11() > 1.0:
            self.view.resetTransform()
            self.view.centerOn(target_rect.center())
        else:
            pass

    def add_connection_blocks(self, blocks_list: List[Block] | None = None) -> None:
        """
        Build symbolic wrapper blocks for every root input and output variable.

        :param blocks_list: Optional list that receives the created wrappers.
        :return: None.
        """

        for i, invar in enumerate(self.main_block.in_vars):
            self.create_connection_block(invar, BlockType.INPUT_CONN, blocks_list)

        for i, outvar in enumerate(self.main_block.out_vars):

            self.create_connection_block(outvar, BlockType.OUTPUT_CONN, blocks_list)





    def add_connection_items(self, blocks_list: List[graph.BlockItem] | None = None) -> None:
        """
        Build graphical wrapper items for every root input and output variable.

        :param blocks_list: Optional list that receives the created graphics items.
        :return: None.
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
        fit_rect = self._compact_initial_layout()
        if fit_rect is not None:
            self.view.fitInView(fit_rect, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
            self.view.scale(graph.EditorGraphicsCommonFeatures.INITIAL_VIEW_SCALE, graph.EditorGraphicsCommonFeatures.INITIAL_VIEW_SCALE)
        else:
            self.view.fitInView(self.scene.sceneRect(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)


    def _get_safe_bus_name(self, bus: Any) -> str:
        """
        Build a safe bus-name suffix for editor-visible connection variables.

        :param bus: Bus API object.
        :return: Bus name with spaces replaced by underscores.
        """
        return bus.name.replace(" ", "_")

    def _get_current_root_interface_refs(self) -> set[VarPowerFlowReferenceType]:
        """
        Return the references currently present in the working root interface.

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

    def _is_root_container_block(self, block_model: Block | None) -> bool:
        """
        Return whether one block object is the editor root container itself.

        :param block_model: Candidate block.
        :return: ``True`` when the block is ``main_block``.
        """
        if block_model is None:
            return False
        elif block_model is self.main_block:
            return True
        else:
            return False

    def _remove_legacy_root_self_nodes(self) -> bool:
        """
        Remove persisted non-interface diagram nodes that represent ``main_block`` itself.

        :return: ``True`` when any synthetic root-self node or connection was removed.
        """
        node_uids_to_remove: list[int] = list()
        node_uid: int
        node: BlockDiagramNode
        changed: bool = False
        block_type: BlockType | None

        if not self.is_root_editor:
            return False
        else:
            pass

        for node_uid, node in self.diagram.node_data.items():
            if node.tpe in BlockType.__members__:
                block_type = BlockType[node.tpe]
            else:
                block_type = None

            if block_type in {BlockType.INPUT_CONN, BlockType.OUTPUT_CONN}:
                pass
            elif node.device_uid == self.main_block.uid:
                node_uids_to_remove.append(node_uid)
            else:
                pass

        connection_uids_to_remove: list[int] = list()
        connection_uid: int
        connection_record: BlockDiagramConnection
        for connection_uid, connection_record in self.diagram.con_data.items():
            if connection_record.from_uid in node_uids_to_remove or connection_record.to_uid in node_uids_to_remove:
                connection_uids_to_remove.append(connection_uid)
            else:
                pass

        for connection_uid in connection_uids_to_remove:
            changed = self._remove_persisted_root_interface_connection_by_uid(connection_uid=connection_uid) or changed

        for node_uid in node_uids_to_remove:
            del self.diagram.node_data[node_uid]
            changed = True

        return changed

    def _remove_root_interface_wrapper_connections_for_uid(self, wrapper_uid: int) -> None:
        """
        Remove every persisted wire connected to one root-interface wrapper.

        :param wrapper_uid: Wrapper block UID and diagram-node UID.
        :return: None.
        """
        connection_items: list[graph.ConnectionItem] = list()
        scene_item: QGraphicsItem
        connection_item: graph.ConnectionItem

        for scene_item in self.scene.items():
            if isinstance(scene_item, graph.ConnectionItem):
                if scene_item.con_uid in self.diagram.con_data:
                    connection_record = self.diagram.con_data[scene_item.con_uid]
                    if connection_record.from_uid == wrapper_uid or connection_record.to_uid == wrapper_uid:
                        connection_items.append(scene_item)
                    else:
                        pass
                else:
                    pass
            else:
                pass

        for connection_item in connection_items:
            self.remove_connection_item(connection_item)

        stale_connection_uids: list[int] = list()
        connection_uid: int
        connection_record: BlockDiagramConnection
        for connection_uid, connection_record in self.diagram.con_data.items():
            if connection_record.from_uid == wrapper_uid or connection_record.to_uid == wrapper_uid:
                stale_connection_uids.append(connection_uid)
            else:
                pass

        for connection_uid in stale_connection_uids:
            self._remove_persisted_root_interface_connection_by_uid(connection_uid=connection_uid)

    def _remove_persisted_root_interface_connection_by_uid(self, connection_uid: int) -> bool:
        """
        Remove one persisted root-interface wire symbolically without a live scene item.

        :param connection_uid: Persisted diagram connection UID.
        :return: ``True`` when one persisted connection was removed.
        """
        connection_record: BlockDiagramConnection | None = self.diagram.con_data.get(connection_uid, None)
        source_block: Block | None
        target_block: Block | None
        source_block_item: graph.BlockItem | graph.GenericBlockItem | graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem | graph.UnOpItem | graph.PairedItem | None
        target_block_item: graph.BlockItem | graph.GenericBlockItem | graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem | graph.UnOpItem | graph.PairedItem | None
        source_port: graph.PortItem | None = None
        target_port: graph.PortItem | None = None
        removed: bool = False

        if connection_record is None:
            return False
        else:
            pass

        source_block = self.get_block_from_main_block(connection_record.from_uid)
        target_block = self.get_block_from_main_block(connection_record.to_uid)

        if source_block is not None and 0 <= connection_record.port_number_from < len(source_block.out_vars):
            source_block_item = self.get_scene_item_by_block_uid(source_block.uid)
            if source_block_item is not None and connection_record.port_number_from < len(source_block_item.outputs):
                source_port = source_block_item.outputs[connection_record.port_number_from]
            else:
                pass
        else:
            pass

        if target_block is not None and 0 <= connection_record.port_number_to < len(target_block.in_vars):
            target_block_item = self.get_scene_item_by_block_uid(target_block.uid)
            if target_block_item is not None and connection_record.port_number_to < len(target_block_item.inputs):
                target_port = target_block_item.inputs[connection_record.port_number_to]
            else:
                pass
        else:
            pass

        if source_port is not None and target_port is not None:
            self._unregister_symbolic_connection_between_ports(source_port, target_port)
        else:
            pass

        del self.diagram.con_data[connection_uid]
        if self._qt_routing_session is not None:
            self._qt_routing_session.remove_connection(connection_uid)
        else:
            pass

        removed = True
        return removed

    def _remove_root_interface_wrapper_by_uid(self, wrapper_uid: int) -> bool:
        """
        Remove one protected root-interface wrapper block and diagram node.

        :param wrapper_uid: Wrapper block UID and diagram-node UID.
        :return: ``True`` when the wrapper existed and was removed.
        """
        child_block: Block
        kept_children: list[Block] = list()
        wrapper_removed: bool = False
        scene_item: QGraphicsItem

        self._remove_root_interface_wrapper_connections_for_uid(wrapper_uid=wrapper_uid)

        for child_block in self.main_block.children:
            if child_block.uid == wrapper_uid:
                wrapper_removed = True
            else:
                kept_children.append(child_block)
        self.main_block.children = kept_children

        if wrapper_uid in self.diagram.node_data:
            del self.diagram.node_data[wrapper_uid]
            wrapper_removed = True
        else:
            pass

        for scene_item in self.scene.items():
            if isinstance(scene_item, graph.ProtectedConnectionBlockItem):
                if scene_item.subsys is not None and scene_item.subsys.uid == wrapper_uid:
                    self.scene.removeItem(scene_item)
                else:
                    pass
            else:
                pass

        return wrapper_removed

    def _get_semantic_root_interface_reference(
            self,
            wrapper_block: Block,
            block_type: BlockType,
    ) -> VarPowerFlowReferenceType | None:
        """
        Resolve the side-specific root reference represented by one wrapper.

        Branch voltage wrappers display shared bus variables such as ``v_A`` on
        both sides. Their stable variable identities remain distinct in the root
        external mapping, whose keys provide the unambiguous ``vf_A``/``vt_A``
        semantics required across phase-topology changes.

        :param wrapper_block: Protected root-interface wrapper block.
        :param block_type: Input or output wrapper direction.
        :return: Side-specific root reference, or ``None`` when ambiguous.
        """
        expected_inputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        expected_outputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        expected_by_ref: dict[VarPowerFlowReferenceType, Var]
        wrapper_var: Var | None
        matching_refs: list[VarPowerFlowReferenceType] = list()
        allowed_refs: set[VarPowerFlowReferenceType] = set()
        mapping_ref: VarPowerFlowReferenceType
        mapped_var: Var | None
        expected_ref: VarPowerFlowReferenceType
        expected_var: Var

        if block_type == BlockType.INPUT_CONN and len(wrapper_block.out_vars) == 1:
            wrapper_var = wrapper_block.out_vars[0]
        elif block_type == BlockType.OUTPUT_CONN and len(wrapper_block.in_vars) == 1:
            wrapper_var = wrapper_block.in_vars[0]
        else:
            return None

        expected_inputs_by_ref, expected_outputs_by_ref = build_expected_root_emt_interface_for_device(self.api_object)
        if block_type == BlockType.INPUT_CONN:
            expected_by_ref = expected_inputs_by_ref
            for mapped_var in self.main_block.in_vars:
                if isinstance(mapped_var.ref, VarPowerFlowReferenceType):
                    allowed_refs.add(mapped_var.ref)
                else:
                    pass
        elif block_type == BlockType.OUTPUT_CONN:
            expected_by_ref = expected_outputs_by_ref
            for mapped_var in self.main_block.out_vars:
                if isinstance(mapped_var.ref, VarPowerFlowReferenceType):
                    allowed_refs.add(mapped_var.ref)
                else:
                    pass
        else:
            return None

        allowed_refs.update(expected_by_ref.keys())

        for expected_ref, expected_var in expected_by_ref.items():
            if expected_var is wrapper_var or expected_var.non_mutable_uid == wrapper_var.non_mutable_uid:
                matching_refs.append(expected_ref)
            else:
                pass

        for mapping_ref, mapped_var in self.main_block.external_mapping.items():
            if mapping_ref not in allowed_refs or mapped_var is None:
                pass
            elif mapped_var is wrapper_var or mapped_var.non_mutable_uid == wrapper_var.non_mutable_uid:
                if mapping_ref not in matching_refs:
                    matching_refs.append(mapping_ref)
                else:
                    pass
            else:
                pass

        if len(matching_refs) == 1:
            return matching_refs[0]
        elif wrapper_var.ref in allowed_refs:
            return wrapper_var.ref
        else:
            return None

    def _find_protected_wrapper_blocks_by_ref(self) -> tuple[dict[VarPowerFlowReferenceType, Block], dict[VarPowerFlowReferenceType, Block]]:
        """
        Index live protected wrapper child blocks by root-interface reference.

        :return: ``(input_wrappers_by_ref, output_wrappers_by_ref)``.
        """
        input_wrappers_by_ref: dict[VarPowerFlowReferenceType, Block] = dict()
        output_wrappers_by_ref: dict[VarPowerFlowReferenceType, Block] = dict()
        child_block: Block
        semantic_reference: VarPowerFlowReferenceType | None

        for child_block in self.main_block.children:
            if not is_root_interface_wrapper_block(child_block):
                pass
            elif len(child_block.out_vars) == 1 and len(child_block.in_vars) == 0:
                semantic_reference = self._get_semantic_root_interface_reference(
                    wrapper_block=child_block,
                    block_type=BlockType.INPUT_CONN,
                )
                if semantic_reference is not None:
                    input_wrappers_by_ref[semantic_reference] = child_block
                else:
                    pass
            elif len(child_block.in_vars) == 1 and len(child_block.out_vars) == 0:
                semantic_reference = self._get_semantic_root_interface_reference(
                    wrapper_block=child_block,
                    block_type=BlockType.OUTPUT_CONN,
                )
                if semantic_reference is not None:
                    output_wrappers_by_ref[semantic_reference] = child_block
                else:
                    pass
            else:
                pass

        return input_wrappers_by_ref, output_wrappers_by_ref

    def _convert_legacy_root_interface_children_to_wrappers(self) -> bool:
        """
        Promote legacy one-port root interface children to explicit wrappers.

        Some bootstrap paths still create root interface shells without the
        wrapper marker. The dynamic editor now relies on explicit wrapper
        semantics to avoid leaking those shells as generic blocks.

        :return: ``True`` when any child was promoted.
        """
        child_block: Block
        interface_var: Var | None
        expected_inputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        expected_outputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        changed: bool = False
        diagram_node: BlockDiagramNode | None

        if not self.is_root_editor:
            return False
        else:
            pass

        expected_inputs_by_ref, expected_outputs_by_ref = build_expected_root_emt_interface_for_device(self.api_object)

        for child_block in self.main_block.children:
            if child_block.is_root_interface_wrapper:
                pass
            else:
                interface_var = get_single_interface_var(child_block)
                diagram_node = self.diagram.node_data.get(child_block.uid, None)
                if interface_var is None or interface_var.ref is None:
                    pass
                elif diagram_node is not None and diagram_node.tpe == BlockType.INPUT_CONN.name and len(
                        child_block.out_vars) == 1 and len(child_block.in_vars) == 0:
                    child_block.is_root_interface_wrapper = True
                    changed = True
                elif diagram_node is not None and diagram_node.tpe == BlockType.OUTPUT_CONN.name and len(
                        child_block.in_vars) == 1 and len(child_block.out_vars) == 0:
                    child_block.is_root_interface_wrapper = True
                    changed = True
                elif len(child_block.out_vars) == 1 and len(child_block.in_vars) == 0 and interface_var.ref in expected_inputs_by_ref:
                    child_block.is_root_interface_wrapper = True
                    changed = True
                elif len(child_block.in_vars) == 1 and len(child_block.out_vars) == 0 and interface_var.ref in expected_outputs_by_ref:
                    child_block.is_root_interface_wrapper = True
                    changed = True
                else:
                    pass

        return changed

    def _remove_stale_root_interface_duplicate_children(self) -> bool:
        """
        Remove leaked non-wrapper root-interface child shells from the root block.

        Some reopen paths can keep stale one-port child shells such as ``v_A`` or
        ``net_conn_i_A`` in ``main_block.children`` even though the authoritative
        root interface is already represented by protected wrappers. Those leaked
        shells are not real internal dynamic-model blocks and must not appear as
        regular rectangles on the canvas.

        :return: ``True`` when any leaked child shell was removed.
        """
        expected_inputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        expected_outputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        kept_children: List[Block] = list()
        child_block: Block
        interface_var: Var | None
        changed: bool = False
        node_uid_to_remove: List[int] = list()
        node_uid: int
        node: BlockDiagramNode

        if not self.is_root_editor:
            return False
        else:
            pass

        expected_inputs_by_ref, expected_outputs_by_ref = build_expected_root_emt_interface_for_device(self.api_object)

        for child_block in self.main_block.children:
            interface_var = get_single_interface_var(child_block)

            if is_root_interface_wrapper_block(child_block):
                kept_children.append(child_block)
            elif interface_var is None or interface_var.ref is None:
                kept_children.append(child_block)
            elif len(child_block.children) > 0:
                kept_children.append(child_block)
            elif len(child_block.algebraic_vars) > 0:
                kept_children.append(child_block)
            elif len(child_block.state_vars) > 0:
                kept_children.append(child_block)
            elif len(child_block.diff_vars) > 0:
                kept_children.append(child_block)
            elif len(child_block.parameters) > 0:
                kept_children.append(child_block)
            elif len(child_block.out_vars) == 1 and len(child_block.in_vars) == 0:
                if interface_var.ref in expected_inputs_by_ref:
                    changed = True
                    node_uid_to_remove.append(child_block.uid)
                else:
                    kept_children.append(child_block)
            elif len(child_block.in_vars) == 1 and len(child_block.out_vars) == 0:
                if interface_var.ref in expected_outputs_by_ref:
                    changed = True
                    node_uid_to_remove.append(child_block.uid)
                else:
                    kept_children.append(child_block)
            else:
                kept_children.append(child_block)

        self.main_block.children = kept_children

        for node_uid in node_uid_to_remove:
            if node_uid in self.diagram.node_data:
                del self.diagram.node_data[node_uid]
            else:
                pass

        if changed:
            stale_connection_uids: List[int] = list()
            connection_uid: int
            connection_record: BlockDiagramConnection
            for connection_uid, connection_record in self.diagram.con_data.items():
                if connection_record.from_uid in node_uid_to_remove or connection_record.to_uid in node_uid_to_remove:
                    stale_connection_uids.append(connection_uid)
                else:
                    pass

            for connection_uid in stale_connection_uids:
                self._remove_persisted_root_interface_connection_by_uid(connection_uid=connection_uid)
        else:
            pass

        return changed

    def _ensure_root_interface_wrapper_blocks_exist(self,
                                                    create_missing: bool = True) -> bool:
        """
        Ensure every authoritative root EMT ref has one wrapper child block.

        :param create_missing: Whether missing wrapper blocks may be created.
        :return: ``True`` when any wrapper block was created.
        """
        changed: bool = False
        input_wrappers_by_ref: dict[VarPowerFlowReferenceType, Block]
        output_wrappers_by_ref: dict[VarPowerFlowReferenceType, Block]
        root_var: Var
        wrapper_block: Block

        input_wrappers_by_ref, output_wrappers_by_ref = self._find_protected_wrapper_blocks_by_ref()
        preserved_non_wrapper_children: list[Block] = list()
        unresolved_wrapper_children: list[Block] = list()
        ordered_wrapper_children: list[Block] = list()
        child_block: Block
        seen_wrapper_ids: set[int] = set()
        reference: VarPowerFlowReferenceType

        for root_var in self.main_block.in_vars:
            if root_var.ref is None or root_var.ref in input_wrappers_by_ref:
                continue
            if not create_missing:
                continue

            wrapper_block = Block(name=root_var.name)
            wrapper_block.out_vars = list([root_var])
            wrapper_block.is_root_interface_wrapper = True
            self.main_block.add(wrapper_block)
            input_wrappers_by_ref[root_var.ref] = wrapper_block
            changed = True

        for root_var in self.main_block.out_vars:
            if root_var.ref is None or root_var.ref in output_wrappers_by_ref:
                continue
            if not create_missing:
                continue

            wrapper_block = Block(name=root_var.name)
            wrapper_block.in_vars = list([root_var])
            wrapper_block.is_root_interface_wrapper = True
            self.main_block.add(wrapper_block)
            output_wrappers_by_ref[root_var.ref] = wrapper_block
            changed = True

        for child_block in self.main_block.children:
            if not is_root_interface_wrapper_block(child_block):
                preserved_non_wrapper_children.append(child_block)
            else:
                pass

        for reference in sorted(input_wrappers_by_ref.keys(), key=get_reference_sort_key):
            if id(input_wrappers_by_ref[reference]) in seen_wrapper_ids:
                changed = True
            else:
                ordered_wrapper_children.append(input_wrappers_by_ref[reference])
                seen_wrapper_ids.add(id(input_wrappers_by_ref[reference]))

        for reference in sorted(output_wrappers_by_ref.keys(), key=get_reference_sort_key):
            if id(output_wrappers_by_ref[reference]) in seen_wrapper_ids:
                changed = True
            else:
                ordered_wrapper_children.append(output_wrappers_by_ref[reference])
                seen_wrapper_ids.add(id(output_wrappers_by_ref[reference]))

        for child_block in self.main_block.children:
            if not is_root_interface_wrapper_block(child_block):
                pass
            elif id(child_block) in seen_wrapper_ids:
                pass
            elif len(child_block.out_vars) == 1 and len(child_block.in_vars) == 0:
                reference = self._get_semantic_root_interface_reference(
                    wrapper_block=child_block,
                    block_type=BlockType.INPUT_CONN,
                )
                if reference is None:
                    unresolved_wrapper_children.append(child_block)
                    seen_wrapper_ids.add(id(child_block))
                else:
                    changed = True
            elif len(child_block.in_vars) == 1 and len(child_block.out_vars) == 0:
                reference = self._get_semantic_root_interface_reference(
                    wrapper_block=child_block,
                    block_type=BlockType.OUTPUT_CONN,
                )
                if reference is None:
                    unresolved_wrapper_children.append(child_block)
                    seen_wrapper_ids.add(id(child_block))
                else:
                    changed = True
            else:
                unresolved_wrapper_children.append(child_block)
                seen_wrapper_ids.add(id(child_block))

        self.main_block.children = (
            preserved_non_wrapper_children
            + ordered_wrapper_children
            + unresolved_wrapper_children
        )

        return changed

    def _refresh_interface_wrapper_scene_items(self) -> None:
        """
        Refresh visible protected-wrapper names and tooltips after reconciliation.

        :return: None.
        """
        scene_item: QGraphicsItem

        for scene_item in self.scene.items():
            if isinstance(scene_item, graph.ProtectedConnectionBlockItem):
                scene_item.refresh_block_name()
                scene_item.refresh_port_metadata()
            else:
                pass

    def _ensure_root_interface_wrapper_nodes_exist(self) -> bool:
        """
        Materialize missing protected-wrapper child blocks and diagram nodes.

        Newly added derived root EMT refs must exist as protected connection ovals
        before the scene rebuild runs, even when the saved diagram came from an
        older smaller topology.

        :return: ``True`` when any wrapper child or node was created.
        """
        changed: bool = False
        interface_input_wrappers: dict[VarPowerFlowReferenceType, Block]
        interface_output_wrappers: dict[VarPowerFlowReferenceType, Block]
        reference: VarPowerFlowReferenceType
        root_var: Var
        existing_y_values: list[float] = list()
        next_input_y: float
        next_output_y: float
        wrapper_block: Block | None
        node_uid: int
        node: BlockDiagramNode
        kept_non_interface_nodes: list[tuple[int, BlockDiagramNode]] = list()
        wrapper_block_for_node: Block | None
        interface_var: Var | None
        existing_input_positions: dict[VarPowerFlowReferenceType, tuple[float, float]] = dict()
        existing_output_positions: dict[VarPowerFlowReferenceType, tuple[float, float]] = dict()
        existing_input_node_uids: dict[VarPowerFlowReferenceType, int] = dict()
        existing_output_node_uids: dict[VarPowerFlowReferenceType, int] = dict()
        rebuilt_node_data: dict[int, BlockDiagramNode] = dict()
        expected_inputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        expected_outputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        ordered_input_refs: list[VarPowerFlowReferenceType]
        ordered_output_refs: list[VarPowerFlowReferenceType]

        if not self.is_root_editor:
            return False
        else:
            pass

        expected_inputs_by_ref, expected_outputs_by_ref = build_expected_root_emt_interface_for_device(self.api_object)
        ordered_input_refs = build_expected_root_interface_ref_order(block_type=BlockType.INPUT_CONN,
                                                                     input_refs=expected_inputs_by_ref,
                                                                     output_refs=expected_outputs_by_ref)
        ordered_output_refs = build_expected_root_interface_ref_order(block_type=BlockType.OUTPUT_CONN,
                                                                      input_refs=expected_inputs_by_ref,
                                                                      output_refs=expected_outputs_by_ref)

        changed = self._ensure_root_interface_wrapper_blocks_exist(create_missing=True) or changed
        interface_input_wrappers, interface_output_wrappers = self._find_protected_wrapper_blocks_by_ref()

        for node_uid, node in self.diagram.node_data.items():
            if node.tpe in {BlockType.INPUT_CONN.name, BlockType.OUTPUT_CONN.name}:
                existing_y_values.append(node.y)
                wrapper_block_for_node = self.get_block_from_main_block(node.device_uid)
                if wrapper_block_for_node is None and node.device_uid != node_uid:
                    wrapper_block_for_node = self.get_block_from_main_block(node_uid)
                else:
                    pass

                if wrapper_block_for_node is None:
                    reference = None
                elif node.tpe == BlockType.INPUT_CONN.name:
                    reference = self._get_semantic_root_interface_reference(
                        wrapper_block=wrapper_block_for_node,
                        block_type=BlockType.INPUT_CONN,
                    )
                else:
                    reference = self._get_semantic_root_interface_reference(
                        wrapper_block=wrapper_block_for_node,
                        block_type=BlockType.OUTPUT_CONN,
                    )

                if reference is not None:
                    if node.tpe == BlockType.INPUT_CONN.name:
                        existing_input_positions[reference] = (node.x, node.y)
                        existing_input_node_uids[reference] = node_uid
                    else:
                        existing_output_positions[reference] = (node.x, node.y)
                        existing_output_node_uids[reference] = node_uid
                else:
                    pass
            else:
                kept_non_interface_nodes.append((node_uid, node))

        if len(existing_y_values) > 0:
            next_input_y = min(existing_y_values)
            next_output_y = max(existing_y_values)
        else:
            next_input_y = 100.0
            next_output_y = 100.0

        for reference in sorted(expected_inputs_by_ref.keys(), key=get_reference_sort_key):
            root_var = expected_inputs_by_ref[reference]
            wrapper_block = interface_input_wrappers.get(reference, None)
            if wrapper_block is None:
                wrapper_block = Block(name=root_var.name)
                wrapper_block.out_vars = list([root_var])
                wrapper_block.is_root_interface_wrapper = True
                self.main_block.add(wrapper_block)
                changed = True
            elif wrapper_block.uid != existing_input_node_uids.get(reference, wrapper_block.uid):
                changed = True
            else:
                pass

            wrapper_block.out_vars = list([root_var])
            wrapper_block.in_vars = list()
            wrapper_block.set_name(root_var.name)

            stored_position = existing_input_positions.get(reference, None)
            if stored_position is None:
                node_x = 100.0
                node_y = next_input_y
            else:
                node_x, node_y = stored_position
            self.diagram.add_node(name=wrapper_block.name,
                                  x=node_x,
                                  y=node_y,
                                  tpe=BlockType.INPUT_CONN.name,
                                  device_uid=wrapper_block.uid)
            rebuilt_node_data[wrapper_block.uid] = self.diagram.node_data[wrapper_block.uid]
            next_input_y += 100.0

        expected_output_by_ref: dict[VarPowerFlowReferenceType, Var] = dict()
        for root_var in self.main_block.out_vars:
            if root_var.ref is not None:
                expected_output_by_ref[root_var.ref] = root_var
            else:
                pass

        for reference in sorted(expected_outputs_by_ref.keys(), key=get_reference_sort_key):
            root_var = expected_output_by_ref[reference]
            wrapper_block = interface_output_wrappers.get(reference, None)
            if wrapper_block is None:
                wrapper_block = Block(name=root_var.name)
                wrapper_block.in_vars = list([root_var])
                wrapper_block.is_root_interface_wrapper = True
                self.main_block.add(wrapper_block)
                changed = True
            elif wrapper_block.uid != existing_output_node_uids.get(reference, wrapper_block.uid):
                changed = True
            else:
                pass

            wrapper_block.in_vars = list([root_var])
            wrapper_block.out_vars = list()
            wrapper_block.set_name(root_var.name)

            stored_position = existing_output_positions.get(reference, None)
            if stored_position is None:
                node_x = 1020.0
                node_y = next_output_y
            else:
                node_x, node_y = stored_position
            self.diagram.add_node(name=wrapper_block.name,
                                  x=node_x,
                                  y=node_y,
                                  tpe=BlockType.OUTPUT_CONN.name,
                                  device_uid=wrapper_block.uid)
            rebuilt_node_data[wrapper_block.uid] = self.diagram.node_data[wrapper_block.uid]
            next_output_y += 100.0

        self.diagram.node_data = dict()
        for node_uid, node in kept_non_interface_nodes:
            self.diagram.node_data[node_uid] = node
        self.diagram.node_data.update(rebuilt_node_data)

        return changed

    def _materialize_missing_root_interface_scene_items(
            self,
            uid_to_blockitem: Dict[
                int,
                graph.BlockItem | graph.GenericBlockItem | graph.RoundBaseArithmeticOpItem |
                graph.RectBaseArithmeticOpItem | graph.UnOpItem | graph.PairedItem,
            ],
    ) -> None:
        """
        Add any authoritative root-interface wrappers still missing from the scene.

        Saved diagrams can be smaller than the current topology. After reconciliation,
        the working tree may contain new protected wrapper blocks and diagram nodes
        that were not part of the original persisted iteration set. Materialize them
        before persisted connections are replayed.

        :param uid_to_blockitem: Mutable scene-item index being rebuilt.
        :return: None.
        """
        node_uid: int
        node: BlockDiagramNode
        block_model: Block | None
        block_type: BlockType | None
        block_item: graph.ProtectedConnectionBlockItem

        for node_uid, node in self.diagram.node_data.items():
            if node_uid in uid_to_blockitem:
                continue

            if node.tpe == BlockType.INPUT_CONN.name:
                block_type = BlockType.INPUT_CONN
            elif node.tpe == BlockType.OUTPUT_CONN.name:
                block_type = BlockType.OUTPUT_CONN
            else:
                block_type = None

            if block_type is None:
                continue

            block_model = self.get_block_from_main_block(node.device_uid)
            if block_model is None:
                block_model = self.get_block_from_main_block(node_uid)
            else:
                pass

            block_model = self._build_root_interface_wrapper_block(block_type=block_type,
                                                                   fallback_block_model=block_model,
                                                                   interface_index=None,
                                                                   wrapper_uid=node_uid)
            if block_model is None:
                continue

            if all(child is not block_model for child in self.main_block.children):
                self.main_block.add(block_model)
            else:
                pass

            node.device_uid = node_uid
            node.name = block_model.name

            block_item = graph.ProtectedConnectionBlockItem(
                editor=self,
                var_factory=self.var_factory,
                name=block_model.name,
                mode=self.mode,
                api_object=self.api_object,
            )
            block_item.set_subsystem(block_model)
            block_item.position_changed_callback = self.build_position_changed_callback(node_uid)
            block_item.build_item()
            block_item.recolour()
            self.scene.addItem(block_item)
            block_item.setPos(QPointF(node.x, node.y))
            uid_to_blockitem[node_uid] = block_item

    def _disconnect_all_root_interface_wires(self) -> bool:
        """
        Remove every connection incident to any protected root-interface wrapper.

        :return: ``True`` when any live or persisted root-interface connection was removed.
        """
        wrapper_uids: set[int] = set()
        child_block: Block
        connection_uids_to_remove: list[int] = list()
        connection_uid: int
        connection_record: BlockDiagramConnection
        changed: bool = False

        for child_block in self.main_block.children:
            if is_root_interface_wrapper_block(child_block):
                wrapper_uids.add(child_block.uid)
            else:
                pass

        for child_block in self.main_block.children:
            if child_block.uid in wrapper_uids:
                changed = self._remove_root_interface_wrapper_connections_for_uid(child_block.uid) or changed
            else:
                pass

        for connection_uid, connection_record in self.diagram.con_data.items():
            if connection_record.from_uid in wrapper_uids or connection_record.to_uid in wrapper_uids:
                connection_uids_to_remove.append(connection_uid)
            else:
                pass

        for connection_uid in connection_uids_to_remove:
            changed = self._remove_persisted_root_interface_connection_by_uid(connection_uid=connection_uid) or changed

        return changed

    def _rebuild_full_root_emt_interface_from_current_topology(self) -> bool:
        """
        Replace the full root EMT network interface from current synchronized bus shells.

        :return: ``True`` when the root contract changed.
        """
        expected_inputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        expected_outputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        current_input_by_ref: dict[VarPowerFlowReferenceType, Var] = dict()
        current_output_by_ref: dict[VarPowerFlowReferenceType, Var] = dict()
        interface_input_wrappers: dict[VarPowerFlowReferenceType, Block]
        interface_output_wrappers: dict[VarPowerFlowReferenceType, Block]
        changed: bool = False
        reference: VarPowerFlowReferenceType
        root_var: Var
        mapping_key: VarPowerFlowReferenceType

        expected_inputs_by_ref, expected_outputs_by_ref = build_expected_root_emt_interface_for_device(self.api_object)

        for root_var in self.main_block.in_vars:
            if root_var.ref is not None:
                current_input_by_ref[root_var.ref] = root_var
            else:
                pass

        for root_var in self.main_block.out_vars:
            if root_var.ref is not None:
                current_output_by_ref[root_var.ref] = root_var
            else:
                pass

        self._ensure_root_interface_wrapper_blocks_exist(create_missing=False)
        interface_input_wrappers, interface_output_wrappers = self._find_protected_wrapper_blocks_by_ref()

        changed = self._disconnect_all_root_interface_wires() or changed

        for reference in list(current_input_by_ref.keys()):
            if reference not in expected_inputs_by_ref:
                wrapper_block = interface_input_wrappers.get(reference, None)
                if wrapper_block is not None:
                    changed = self._remove_root_interface_wrapper_by_uid(wrapper_uid=wrapper_block.uid) or changed
                else:
                    pass
                self._remove_root_connection_var(connection_var=current_input_by_ref[reference], direction="input")
                changed = True
            else:
                pass

        for reference in list(current_output_by_ref.keys()):
            if reference not in expected_outputs_by_ref:
                wrapper_block = interface_output_wrappers.get(reference, None)
                if wrapper_block is not None:
                    changed = self._remove_root_interface_wrapper_by_uid(wrapper_uid=wrapper_block.uid) or changed
                else:
                    pass
                self._remove_root_connection_var(connection_var=current_output_by_ref[reference], direction="output")
                changed = True
            else:
                pass

        self.main_block.in_vars = [expected_inputs_by_ref[reference] for reference in expected_inputs_by_ref.keys()]

        rebuilt_outputs: list[Var] = list()
        for reference in expected_outputs_by_ref.keys():
            existing_output: Var | None = current_output_by_ref.get(reference, None)
            if existing_output is not None:
                existing_output._network_conn = True
                rebuilt_outputs.append(existing_output)
            else:
                rebuilt_outputs.append(self.var_factory.add_var(name=build_expected_root_emt_output_name(reference),
                                                                reference=reference,
                                                                network_conn=True))
                changed = True
        self.main_block.out_vars = rebuilt_outputs

        for mapping_key in list(self.main_block.external_mapping.keys()):
            if isinstance(mapping_key, VarPowerFlowReferenceType) and self._is_emt_interface_reference(mapping_key):
                del self.main_block.external_mapping[mapping_key]
            else:
                pass

        for reference, authoritative_input in expected_inputs_by_ref.items():
            self.main_block.external_mapping[reference] = authoritative_input

        for root_var in self.main_block.out_vars:
            if root_var.ref is not None:
                self.main_block.external_mapping[root_var.ref] = root_var
            else:
                pass

        for reference, authoritative_input in expected_inputs_by_ref.items():
            wrapper_block = interface_input_wrappers.get(reference, None)
            if wrapper_block is not None:
                wrapper_block.out_vars = list([authoritative_input])
                wrapper_block.in_vars = list()
                wrapper_block.set_name(authoritative_input.name)
            else:
                pass

        for reference in expected_outputs_by_ref.keys():
            wrapper_block = interface_output_wrappers.get(reference, None)
            current_output = self.main_block.external_mapping.get(reference, None)
            if wrapper_block is not None and current_output is not None:
                wrapper_block.in_vars = list([current_output])
                wrapper_block.out_vars = list()
                wrapper_block.set_name(current_output.name)
            else:
                pass

        # The wrapper maps captured before reconciliation can reference blocks that
        # were removed or replaced during the same shrink/expand cycle. Rebuild the
        # authoritative wrapper index before regenerating wrapper nodes.
        self._ensure_root_interface_wrapper_blocks_exist(create_missing=True)
        changed = self._ensure_root_interface_wrapper_nodes_exist() or changed
        self._materialize_missing_non_interface_diagram_nodes()
        self._refresh_interface_wrapper_scene_items()
        return changed

    def _branch_root_contract_is_stale_against_expected_topology(self) -> bool:
        """
        Return whether the branch root working copy differs from the authoritative live contract.

        :return: ``True`` when the branch root contract must be rebuilt from authoritative refs.
        """
        expected_inputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        expected_outputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        current_input_refs: set[VarPowerFlowReferenceType] = set()
        current_output_refs: set[VarPowerFlowReferenceType] = set()
        root_var: Var

        if not isinstance(self.api_object, BranchParent):
            return False
        elif self.mode != DynamicSimulationMode.EMT:
            return False
        else:
            pass

        expected_inputs_by_ref, expected_outputs_by_ref = build_expected_root_emt_interface_for_device(self.api_object)

        for root_var in self.main_block.in_vars:
            if root_var.ref is None:
                pass
            else:
                current_input_refs.add(root_var.ref)

        for root_var in self.main_block.out_vars:
            if root_var.ref is None:
                pass
            else:
                current_output_refs.add(root_var.ref)

        if current_input_refs != set(expected_inputs_by_ref.keys()):
            return True
        elif current_output_refs != set(expected_outputs_by_ref.keys()):
            return True
        else:
            return False

    def reconcile_root_emt_topology_now(self) -> bool:
        """
        Synchronize live bus shells and reconcile the current root EMT working copy.

        :return: ``True`` when the working root contract changed structurally.
        """
        topology_changed: bool = False

        if not self.is_root_editor or self.mode != DynamicSimulationMode.EMT:
            return False
        else:
            pass

        dialog_models.initialize_connected_bus_models_for_editor_assignment(api_object=self.api_object,
                                                                            circuit=self.circuit,
                                                                            var_factory=self.var_factory,
                                                                            mode=self.mode)
        topology_changed = self._reconcile_root_emt_interface_from_current_topology()

        if topology_changed:
            self.has_unapplied_changes = True
            self.changes_applied = False
        else:
            pass

        return topology_changed

    def _reconcile_root_emt_interface_from_current_topology(self) -> bool:
        """
        Reconcile the working-copy EMT root interface against the live bus shells.

        :return: ``True`` when the working model or diagram changed structurally.
        """
        expected_inputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        expected_outputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        current_input_by_ref: dict[VarPowerFlowReferenceType, Var] = dict()
        current_output_by_ref: dict[VarPowerFlowReferenceType, Var] = dict()
        interface_input_wrappers: dict[VarPowerFlowReferenceType, Block]
        interface_output_wrappers: dict[VarPowerFlowReferenceType, Block]
        changed: bool = False
        created_initial_authoritative_interface: bool = False
        root_var: Var
        reference: VarPowerFlowReferenceType

        if not self.is_root_editor or self.mode != DynamicSimulationMode.EMT:
            return False
        else:
            pass

        if self._branch_root_contract_is_stale_against_expected_topology():
            return self._rebuild_full_root_emt_interface_from_current_topology()
        else:
            pass

        expected_inputs_by_ref, expected_outputs_by_ref = build_expected_root_emt_interface_for_device(self.api_object)

        for root_var in self.main_block.in_vars:
            if root_var.ref is not None:
                current_input_by_ref[root_var.ref] = root_var
            else:
                pass

        for root_var in self.main_block.out_vars:
            if root_var.ref is not None:
                current_output_by_ref[root_var.ref] = root_var
            else:
                pass

        interface_input_wrappers, interface_output_wrappers = self._find_protected_wrapper_blocks_by_ref()

        if len(current_input_by_ref) == 0 and len(current_output_by_ref) == 0 and len(interface_input_wrappers) == 0 and len(interface_output_wrappers) == 0:
            created_initial_authoritative_interface = True
        else:
            pass

        removed_input_refs: list[VarPowerFlowReferenceType] = sorted([ref for ref in current_input_by_ref.keys() if ref not in expected_inputs_by_ref],
                                                                     key=get_reference_sort_key)
        removed_output_refs: list[VarPowerFlowReferenceType] = sorted([ref for ref in current_output_by_ref.keys() if ref not in expected_outputs_by_ref],
                                                                      key=get_reference_sort_key)
        added_input_refs: list[VarPowerFlowReferenceType] = sorted([ref for ref in expected_inputs_by_ref.keys() if ref not in current_input_by_ref],
                                                                   key=get_reference_sort_key)
        added_output_refs: list[VarPowerFlowReferenceType] = sorted([ref for ref in expected_outputs_by_ref.keys() if ref not in current_output_by_ref],
                                                                    key=get_reference_sort_key)

        if len(removed_input_refs) > 0 or len(removed_output_refs) > 0:
            return self._rebuild_full_root_emt_interface_from_current_topology()
        else:
            pass

        missing_input_wrapper_refs: list[VarPowerFlowReferenceType] = [
            ref for ref in expected_inputs_by_ref.keys()
            if not created_initial_authoritative_interface and interface_input_wrappers.get(ref, None) is None
        ]
        missing_output_wrapper_refs: list[VarPowerFlowReferenceType] = [
            ref for ref in expected_outputs_by_ref.keys()
            if not created_initial_authoritative_interface and interface_output_wrappers.get(ref, None) is None
        ]

        for reference in removed_input_refs:
            wrapper_block = interface_input_wrappers.get(reference, None)
            if wrapper_block is not None:
                changed = self._remove_root_interface_wrapper_by_uid(wrapper_uid=wrapper_block.uid) or changed
            else:
                pass

            self._remove_root_connection_var(connection_var=current_input_by_ref[reference], direction="input")
            changed = True

        for reference in removed_output_refs:
            wrapper_block = interface_output_wrappers.get(reference, None)
            if wrapper_block is not None:
                changed = self._remove_root_interface_wrapper_by_uid(wrapper_uid=wrapper_block.uid) or changed
            else:
                pass

            self._remove_root_connection_var(connection_var=current_output_by_ref[reference], direction="output")
            changed = True

        for reference, authoritative_input in expected_inputs_by_ref.items():
            existing_input: Var | None = current_input_by_ref.get(reference, None)
            if existing_input is None:
                self.main_block.in_vars.append(authoritative_input)
                self.main_block.external_mapping[reference] = authoritative_input
                if not created_initial_authoritative_interface and interface_input_wrappers.get(reference, None) is None:
                    wrapper_block = Block(name=authoritative_input.name)
                    wrapper_block.out_vars = list([authoritative_input])
                    wrapper_block.is_root_interface_wrapper = True
                    self.main_block.add(wrapper_block)
                    interface_input_wrappers[reference] = wrapper_block
                changed = True
            else:
                if existing_input is authoritative_input:
                    pass
                else:
                    if reference in missing_input_wrapper_refs:
                        self.main_block.update_model(existing_input, authoritative_input)
                        rehash_block_tree_var_keyed_dicts(root_block=self.root_block)
                        changed = True
                    else:
                        pass
                self.main_block.external_mapping[reference] = authoritative_input

            wrapper_block = interface_input_wrappers.get(reference, None)
            if wrapper_block is not None:
                wrapper_block.out_vars = list([authoritative_input])
                wrapper_block.in_vars = list()
                wrapper_block.set_name(authoritative_input.name)
            else:
                pass

        for reference, authoritative_output in expected_outputs_by_ref.items():
            existing_output: Var | None = current_output_by_ref.get(reference, None)
            if existing_output is None:
                new_output_name: str = build_expected_root_emt_output_name(reference=reference)
                new_output: Var = self.var_factory.add_var(name=new_output_name,
                                                           reference=reference,
                                                           network_conn=True)
                self.main_block.out_vars.append(new_output)
                self.main_block.external_mapping[reference] = new_output
                if not created_initial_authoritative_interface and interface_output_wrappers.get(reference, None) is None:
                    wrapper_block = Block(name=new_output.name)
                    wrapper_block.in_vars = list([new_output])
                    wrapper_block.is_root_interface_wrapper = True
                    self.main_block.add(wrapper_block)
                    interface_output_wrappers[reference] = wrapper_block
                changed = True
            else:
                existing_output._network_conn = True
                self.main_block.external_mapping[reference] = existing_output
                wrapper_block = interface_output_wrappers.get(reference, None)
                if wrapper_block is not None:
                    wrapper_block.in_vars = list([existing_output])
                    wrapper_block.out_vars = list()
                    wrapper_block.set_name(existing_output.name)
                else:
                    pass

        if len(added_input_refs) > 0 or len(added_output_refs) > 0:
            changed = True
            changed = self._ensure_root_interface_wrapper_nodes_exist() or changed
            self._materialize_missing_non_interface_diagram_nodes()
        elif len(missing_input_wrapper_refs) > 0 or len(missing_output_wrapper_refs) > 0:
            changed = True
            self._materialize_missing_non_interface_diagram_nodes()
        else:
            pass

        self._refresh_interface_wrapper_scene_items()

        if created_initial_authoritative_interface:
            return False
        else:
            return changed

    def _remove_shared_branch_emt_root_refs(self) -> None:
        """
        Remove shared AC EMT root refs from one branch root contract.

        Branch EMT root contracts must expose side-specific references such as
        ``vf_A`` and ``vt_A``. Shared single-bus AC refs such as ``v_A`` are not
        valid on a two-terminal branch root contract and must be removed before
        the saved model is committed and attached to the bus shells.

        :return: None.
        """
        shared_branch_refs: set[VarPowerFlowReferenceType] = set([
            VarPowerFlowReferenceType.v_N,
            VarPowerFlowReferenceType.v_A,
            VarPowerFlowReferenceType.v_B,
            VarPowerFlowReferenceType.v_C,
            VarPowerFlowReferenceType.i_N,
            VarPowerFlowReferenceType.i_A,
            VarPowerFlowReferenceType.i_B,
            VarPowerFlowReferenceType.i_C,
        ])
        kept_in_vars: list[Var] = list()
        kept_out_vars: list[Var] = list()
        mapping_keys_to_remove: list[VarPowerFlowReferenceType] = list()
        var: Var
        mapping_key: VarPowerFlowReferenceType
        mapped_var: Var | None

        if isinstance(self.api_object, BranchParent):
            pass
        else:
            return

        # Branch root contracts may still carry legacy shared AC refs from old
        # templates or previously saved data. Keep only side-specific branch refs
        # in the root IO contract so later EMT validation sees the correct domain.
        for var in self.main_block.in_vars:
            if isinstance(var.ref, VarPowerFlowReferenceType) and var.ref in shared_branch_refs:
                pass
            else:
                kept_in_vars.append(var)

        for var in self.main_block.out_vars:
            if isinstance(var.ref, VarPowerFlowReferenceType) and var.ref in shared_branch_refs:
                pass
            else:
                kept_out_vars.append(var)

        for mapping_key, mapped_var in self.main_block.external_mapping.items():
            if mapping_key in shared_branch_refs:
                mapping_keys_to_remove.append(mapping_key)
            else:
                pass

        self.main_block.in_vars = kept_in_vars
        self.main_block.out_vars = kept_out_vars

        for mapping_key in mapping_keys_to_remove:
            if mapping_key in self.main_block.external_mapping:
                del self.main_block.external_mapping[mapping_key]
            else:
                pass

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

    def _materialize_missing_non_interface_diagram_nodes(self) -> None:
        """
        Add laid-out diagram nodes for non-interface blocks missing from the diagram.

        Template-assigned models can exist as symbolic children without any saved
        diagram node positions. Missing siblings are passed through the same
        connection-aware layered layout as a wholly empty diagram instead of
        sharing the old ``(0, 0)`` fallback position.

        :return: None.
        """
        existing_node_uids: set[int] = set(self.diagram.node_data.keys())
        child_block: Block
        materializable_blocks: List[Block] = list()
        missing_blocks: List[Block] = list()
        expected_inputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        expected_outputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        interface_var: Var | None
        layout_blocks: List[Block]
        layout_graph: SugiyamaGraph
        layout_result: Any
        block_positions: Dict[int, Tuple[float, float]]
        existing_materialized_uids: set[int]
        layout_offset_x: float = 0.0
        layout_offset_y: float = 0.0

        expected_inputs_by_ref, expected_outputs_by_ref = build_expected_root_emt_interface_for_device(self.api_object)

        for child_block in self.main_block.children:
            interface_var = get_single_interface_var(child_block)
            if is_root_interface_wrapper_block(child_block):
                # Derived root interface wrappers are rebuilt through the dedicated
                # protected-wrapper path and must not be materialized as generic blocks.
                pass
            elif self.is_root_editor and interface_var is not None and interface_var.ref is not None:
                if len(child_block.out_vars) == 1 and len(child_block.in_vars) == 0:
                    if interface_var.ref in expected_inputs_by_ref:
                        pass
                    else:
                        materializable_blocks.append(child_block)
                elif len(child_block.in_vars) == 1 and len(child_block.out_vars) == 0:
                    if interface_var.ref in expected_outputs_by_ref:
                        pass
                    else:
                        materializable_blocks.append(child_block)
                else:
                    materializable_blocks.append(child_block)
            else:
                materializable_blocks.append(child_block)

        missing_blocks = [
            block_model for block_model in materializable_blocks
            if block_model.uid not in existing_node_uids
        ]
        if len(missing_blocks) == 0:
            return
        else:
            pass

        existing_materialized_uids = set(
            block_model.uid for block_model in materializable_blocks
            if block_model.uid in existing_node_uids
        )
        if len(existing_materialized_uids) == 0:
            layout_blocks = materializable_blocks
        else:
            # Existing nodes are user-owned positions. Lay out only newly
            # materialized siblings in a separate column to their right.
            layout_blocks = missing_blocks

        layout_graph = self._build_elk_layout_graph(
            child_blocks=layout_blocks,
            input_output_blocks=list(),
        )
        layout_result = SugiyamaLayeredPythonEngine().compute(layout_graph)
        block_positions = {
            int(node.identifier): (node.x or 0.0, node.y or 0.0)
            for node in layout_result.graph.children
        }

        if len(existing_materialized_uids) > 0:
            existing_nodes: List[BlockDiagramNode] = [
                self.diagram.node_data[node_uid]
                for node_uid in existing_materialized_uids
            ]
            minimum_layout_x: float = min(position[0] for position in block_positions.values())
            minimum_layout_y: float = min(position[1] for position in block_positions.values())
            layout_offset_x = max(node.x for node in existing_nodes) + 320.0 - minimum_layout_x
            layout_offset_y = min(node.y for node in existing_nodes) - minimum_layout_y
        else:
            pass

        for child_block in missing_blocks:
            child_position: Tuple[float, float] = block_positions.get(child_block.uid, (0.0, 0.0))
            self.generate_block_item_for_block(
                child_block,
                x_pos=child_position[0] + layout_offset_x,
                y_pos=child_position[1] + layout_offset_y,
            )

    def _rebuild_missing_non_interface_connections(
            self,
            rebuild_interface_connections: bool,
    ) -> None:
        """
        Recreate inferred symbolic wires after auto-materializing missing blocks.

        Symbolic connections between real model siblings remain authoritative on
        every reopen. Root-interface connections are inferred only for a fresh
        no-diagram bootstrap so explicitly partial user wiring stays partial.

        :param rebuild_interface_connections: Whether fresh root wrappers should
            also be connected to matching model ports.
        :return: None.
        """
        items_list: list[graph.GenericBlockItem] = self._collect_non_interface_scene_items()

        if len(items_list) > 0:
            self._rebuild_visible_symbolic_connections(items_list)
            if rebuild_interface_connections:
                self._rebuild_editor_interface_graphical_connections(items_list)
            else:
                pass
        else:
            pass

    def _collect_non_interface_scene_items(self) -> list[graph.GenericBlockItem]:
        """
        Return the visible non-interface generic block items in the scene.

        The reconnect pass operates only on real model blocks. The protected
        editor interface wrappers are intentionally excluded from this list.

        :return: Generic block items excluding editor interface wrappers.
        """
        items_list: list[graph.GenericBlockItem] = list()
        scene_item: QGraphicsItem
        node_data: Any | None

        for scene_item in self.scene.items():
            if isinstance(scene_item, graph.GenericBlockItem):
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

    def _rebuild_visible_symbolic_connections(self, items_list: List[graph.GenericBlockItem]) -> None:
        """
        Recreate missing symbolic wires between all visible non-interface blocks.

        The saved diagram may miss some graphical arrows even when the symbolic
        block graph still carries enough metadata to infer them. Re-run the
        visible block-pair connection discovery so the scene reflects the actual
        symbolic connectivity.

        :param items_list: Visible non-interface block items.
        :return: None.
        """
        item_source: graph.GenericBlockItem
        item_target: graph.GenericBlockItem
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

                            pairs, power_flow_pairs = find_connections(item_target.subsys, item_source.subsys)
                            self._create_missing_connection_items(item_target, item_source, pairs)
                            self._create_missing_connection_items(item_target, item_source, power_flow_pairs)

    def _rebuild_editor_interface_graphical_connections(self, items_list: List[graph.GenericBlockItem]) -> None:
        """
        Recreate visible wires between editor interface blocks and visible model blocks.

        EMT template-open sessions can rebuild the full editor interface without a
        saved diagram that already contains those graphical wires. The root block
        still carries the semantic ``ref`` tags, so reconnect the visible editor
        interface to every visible block port that exposes the same EMT root ref.

        :param items_list: Visible non-interface block items.
        :return: None.
        """
        interface_inputs_by_ref: Dict[VarPowerFlowReferenceType, graph.ProtectedConnectionBlockItem] = dict()
        interface_outputs_by_ref: Dict[VarPowerFlowReferenceType, graph.ProtectedConnectionBlockItem] = dict()
        scene_item: QGraphicsItem
        node_data: Any | None
        reference_var: Var | None
        block_item: graph.GenericBlockItem
        input_index: int
        output_index: int
        input_var: Var
        output_var: Var
        protected_item: graph.ProtectedConnectionBlockItem | None
        branch_input_refs: set[VarPowerFlowReferenceType] = set([
            VarPowerFlowReferenceType.vf_N,
            VarPowerFlowReferenceType.vf_A,
            VarPowerFlowReferenceType.vf_B,
            VarPowerFlowReferenceType.vf_C,
            VarPowerFlowReferenceType.Vf_dc,
            VarPowerFlowReferenceType.vt_N,
            VarPowerFlowReferenceType.vt_A,
            VarPowerFlowReferenceType.vt_B,
            VarPowerFlowReferenceType.vt_C,
            VarPowerFlowReferenceType.Vt_dc,
        ])
        branch_output_refs: set[VarPowerFlowReferenceType] = set([
            VarPowerFlowReferenceType.if_N,
            VarPowerFlowReferenceType.if_A,
            VarPowerFlowReferenceType.if_B,
            VarPowerFlowReferenceType.if_C,
            VarPowerFlowReferenceType.If_dc,
            VarPowerFlowReferenceType.it_N,
            VarPowerFlowReferenceType.it_A,
            VarPowerFlowReferenceType.it_B,
            VarPowerFlowReferenceType.it_C,
            VarPowerFlowReferenceType.It_dc,
        ])

        for scene_item in self.scene.items():
            if isinstance(scene_item, graph.ProtectedConnectionBlockItem) and scene_item.subsys is not None:
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
                        if isinstance(self.api_object, BranchParent) and input_var.ref in branch_input_refs:
                            protected_item = interface_inputs_by_ref.get(input_var.ref, None)
                        else:
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
                                connection_item: graph.ConnectionItem = graph.ConnectionItem(
                                    source_port=protected_item.outputs[0],
                                    target_port=block_item.inputs[input_index],
                                    diagram=self.diagram,
                                    editor=self,
                                )
                                self.attach_new_connection_item(connection_item)
                        else:
                            pass
                    else:
                        pass

                for output_index, output_var in enumerate(block_item.subsys.out_vars):
                    if isinstance(output_var.ref, VarPowerFlowReferenceType):
                        if isinstance(self.api_object, BranchParent) and output_var.ref in branch_output_refs:
                            protected_item = interface_outputs_by_ref.get(output_var.ref, None)
                        else:
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
                                connection_item = graph.ConnectionItem(
                                    source_port=block_item.outputs[output_index],
                                    target_port=protected_item.inputs[0],
                                    diagram=self.diagram,
                                    editor=self,
                                )
                                self.attach_new_connection_item(connection_item)
                        else:
                            pass
                    else:
                        pass


    def _get_editor_interface_input_item_for_ref(self,
                                                 interface_inputs_by_ref: Dict[
                                                     VarPowerFlowReferenceType, graph.ProtectedConnectionBlockItem],
                                                 model_ref: VarPowerFlowReferenceType) -> graph.ProtectedConnectionBlockItem | None:
        """
        Resolve one editor input wrapper for one model-side EMT input reference.

        :param interface_inputs_by_ref: Editor input wrappers keyed by editor EMT ref.
        :param model_ref: Model-side EMT input ref.
        :return: Matching editor input wrapper or ``None``.
        """
        if isinstance(self.api_object, BranchParent):
            ac_side_is_from: bool = False
            ac_side_is_to: bool = False

            if self.api_object.device_type == DeviceType.VscDevice:
                if self.api_object.bus_from.is_dc:
                    ac_side_is_to = True
                else:
                    if self.api_object.bus_to.is_dc:
                        ac_side_is_from = True
                    else:
                        ac_side_is_from = True
            else:
                if model_ref in list([
                    VarPowerFlowReferenceType.vf_N,
                    VarPowerFlowReferenceType.vf_A,
                    VarPowerFlowReferenceType.vf_B,
                    VarPowerFlowReferenceType.vf_C,
                    VarPowerFlowReferenceType.Vf_dc,
                ]):
                    ac_side_is_from = True
                elif model_ref in list([
                    VarPowerFlowReferenceType.vt_N,
                    VarPowerFlowReferenceType.vt_A,
                    VarPowerFlowReferenceType.vt_B,
                    VarPowerFlowReferenceType.vt_C,
                    VarPowerFlowReferenceType.Vt_dc,
                ]):
                    ac_side_is_to = True
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
            elif model_ref == VarPowerFlowReferenceType.vf_N:
                return interface_inputs_by_ref.get(VarPowerFlowReferenceType.vf_N, None)
            elif model_ref == VarPowerFlowReferenceType.vf_A:
                return interface_inputs_by_ref.get(VarPowerFlowReferenceType.vf_A, None)
            elif model_ref == VarPowerFlowReferenceType.vf_B:
                return interface_inputs_by_ref.get(VarPowerFlowReferenceType.vf_B, None)
            elif model_ref == VarPowerFlowReferenceType.vf_C:
                return interface_inputs_by_ref.get(VarPowerFlowReferenceType.vf_C, None)
            elif model_ref == VarPowerFlowReferenceType.vt_N:
                return interface_inputs_by_ref.get(VarPowerFlowReferenceType.vt_N, None)
            elif model_ref == VarPowerFlowReferenceType.vt_A:
                return interface_inputs_by_ref.get(VarPowerFlowReferenceType.vt_A, None)
            elif model_ref == VarPowerFlowReferenceType.vt_B:
                return interface_inputs_by_ref.get(VarPowerFlowReferenceType.vt_B, None)
            elif model_ref == VarPowerFlowReferenceType.vt_C:
                return interface_inputs_by_ref.get(VarPowerFlowReferenceType.vt_C, None)
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
                                                      VarPowerFlowReferenceType, graph.ProtectedConnectionBlockItem],
                                                  model_ref: VarPowerFlowReferenceType) -> graph.ProtectedConnectionBlockItem | None:
        """
        Resolve one editor output wrapper for one model-side EMT output reference.

        :param interface_outputs_by_ref: Editor output wrappers keyed by editor EMT ref.
        :param model_ref: Model-side EMT output ref.
        :return: Matching editor output wrapper or ``None``.
        """
        if isinstance(self.api_object, BranchParent):
            ac_side_is_from: bool = False
            ac_side_is_to: bool = False

            if self.api_object.device_type == DeviceType.VscDevice:
                if self.api_object.bus_from.is_dc:
                    ac_side_is_to = True
                else:
                    if self.api_object.bus_to.is_dc:
                        ac_side_is_from = True
                    else:
                        ac_side_is_from = True
            else:
                if model_ref in list([
                    VarPowerFlowReferenceType.if_N,
                    VarPowerFlowReferenceType.if_A,
                    VarPowerFlowReferenceType.if_B,
                    VarPowerFlowReferenceType.if_C,
                    VarPowerFlowReferenceType.If_dc,
                ]):
                    ac_side_is_from = True
                elif model_ref in list([
                    VarPowerFlowReferenceType.it_N,
                    VarPowerFlowReferenceType.it_A,
                    VarPowerFlowReferenceType.it_B,
                    VarPowerFlowReferenceType.it_C,
                    VarPowerFlowReferenceType.It_dc,
                ]):
                    ac_side_is_to = True
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
            elif model_ref == VarPowerFlowReferenceType.if_N:
                return interface_outputs_by_ref.get(VarPowerFlowReferenceType.if_N, None)
            elif model_ref == VarPowerFlowReferenceType.if_A:
                return interface_outputs_by_ref.get(VarPowerFlowReferenceType.if_A, None)
            elif model_ref == VarPowerFlowReferenceType.if_B:
                return interface_outputs_by_ref.get(VarPowerFlowReferenceType.if_B, None)
            elif model_ref == VarPowerFlowReferenceType.if_C:
                return interface_outputs_by_ref.get(VarPowerFlowReferenceType.if_C, None)
            elif model_ref == VarPowerFlowReferenceType.it_N:
                return interface_outputs_by_ref.get(VarPowerFlowReferenceType.it_N, None)
            elif model_ref == VarPowerFlowReferenceType.it_A:
                return interface_outputs_by_ref.get(VarPowerFlowReferenceType.it_A, None)
            elif model_ref == VarPowerFlowReferenceType.it_B:
                return interface_outputs_by_ref.get(VarPowerFlowReferenceType.it_B, None)
            elif model_ref == VarPowerFlowReferenceType.it_C:
                return interface_outputs_by_ref.get(VarPowerFlowReferenceType.it_C, None)
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
                                         item_source: graph.GenericBlockItem,
                                         item_dest: graph.GenericBlockItem,
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
        source_port: graph.PortItem | None
        target_port: graph.PortItem | None
        port: graph.PortItem

        for source_var, target_var in pairs:
            source_port = self._find_output_port_for_var(item_source=item_source, source_var=source_var)
            target_port = self._find_input_port_for_var(item_dest=item_dest, target_var=target_var)

            if source_port is not None and target_port is not None:
                if self._connection_exists_between_ports(source_port, target_port):
                    pass
                else:
                    connection = graph.ConnectionItem(
                        source_port=source_port,
                        target_port=target_port,
                        diagram=self.diagram,
                        editor=self,
                    )
                    self.attach_new_connection_item(connection)
            else:
                pass


    def _find_output_port_for_var(self, item_source: graph.GenericBlockItem, source_var: Var) -> graph.PortItem | None:
        """
        Find the visible output port corresponding to one symbolic variable.

        :param item_source: Source item.
        :param source_var: Source variable.
        :return: Matching output port or ``None``.
        """
        port: graph.PortItem
        for port in item_source.outputs:
            if vars_match_for_visible_connection(port.base_var, source_var):
                return port
            else:
                pass
        return None

    def _find_input_port_for_var(self, item_dest: graph.GenericBlockItem, target_var: Var) -> graph.PortItem | None:
        """
        Find the visible input port corresponding to one symbolic variable.

        :param item_dest: Destination item.
        :param target_var: Target variable.
        :return: Matching input port or ``None``.
        """
        port: graph.PortItem
        for port in item_dest.inputs:
            if vars_match_for_visible_connection(port.base_var, target_var):
                return port
            else:
                pass
        return None

    @staticmethod
    def _connection_exists_between_ports(source_port: graph.PortItem | graph.BranchingItem,
                                         target_port: graph.PortItem | graph.BranchingItem) -> bool:
        """
        Return whether one visible connection already exists between two ports.

        :param source_port: Candidate source port.
        :param target_port: Candidate target port.
        :return: ``True`` when the connection is already present.
        """
        connection: graph.ConnectionItem

        if source_port.connections is None:
            return False

        for connection in source_port.connections:
            if connection.source_port is source_port and connection.target_port is target_port:
                return True
            else:
                pass

        return False

    def _repair_saved_branch_template_root_wires(self) -> None:
        """
        Repair persisted root-interface wires for saved branch EMT template editors.

        Older saved branch EMT diagrams can reopen with persisted root-interface
        connections bound to the wrong side. Replaying those saved branches as-is
        preserves the wrong wiring. This repair pass removes persisted branch
        template wires between root wrappers and visible internal blocks, then
        rebuilds them by exact side-specific EMT refs.

        :return: None.
        """
        wrapper_uids: set[int] = set()
        child_block: Block
        scene_item: object
        items_list: list[graph.GenericBlockItem]
        connection_uid: int
        connection_record: BlockDiagramConnection
        stale_connection_uids: list[int] = list()

        for child_block in self.main_block.children:
            if is_root_interface_wrapper_block(child_block):
                wrapper_uids.add(child_block.uid)
            else:
                pass

        for connection_uid, connection_record in self.diagram.con_data.items():
            if connection_record.from_uid in wrapper_uids or connection_record.to_uid in wrapper_uids:
                stale_connection_uids.append(connection_uid)
            else:
                pass

        for connection_uid in stale_connection_uids:
            self._remove_persisted_root_interface_connection_by_uid(connection_uid=connection_uid)

        items_list = self._collect_non_interface_scene_items()
        if len(items_list) > 0:
            self._rebuild_editor_interface_graphical_connections(items_list)
        else:
            pass

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
                          (graph.BlockItem, graph.GenericBlockItem, graph.RoundBaseArithmeticOpItem, graph.RectBaseArithmeticOpItem)):
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
            row_data: dialog_models.BlockParameterRow | None = self.parameters_model.get_row(source_row)
            if row_data is not None and row_data.kind != dialog_models.BlockParameterKind.FIXED_PARAMETER:
                self.open_expression_editor_for_parameters(source_row)
        elif source_model is self.equations_model:
            row_data: dialog_models.BlockParameterRow | None = self.equations_model.get_row(source_row)
            if row_data is not None:
                if row_data.opens_expression_editor and source_index.column() == 1:
                    self.open_expression_row_editor(source_row)

    def open_edit_parameter_type_dialog(self, row_index: int) -> None:
        """
        Open the dialog to edit a parameter's type (event, mode, or regular).

        :param row_index:
        :return:
        """
        row_data: dialog_models.BlockParameterRow | None = self.parameters_model.get_row(row_index)
        if row_data is None or self.parameters_model.block is None:
            return

        block = self.parameters_model.block

        api_object = self.parameters_model.api_object
        dialog: dialog_models.EditParameterDialog = dialog_models.EditParameterDialog(
            api_object=api_object,
            devices_static_params_mapping=self.devices_static_params_mapping,
            current_kind=row_data.kind,
            parent=self
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                new_kind: dialog_models.BlockParameterKind = dialog.get_category_kind()
                old_kind: dialog_models.BlockParameterKind = row_data.kind

                if new_kind == old_kind:
                    return

                var_name = row_data.name

                if new_kind == dialog_models.BlockParameterKind.FIXED_PARAMETER:
                    static_var_ref = dialog.get_static_variable()
                    new_var = self.var_factory.add_var(name=var_name, reference=static_var_ref)
                    const_value = 0.0
                else:
                    new_var = self.var_factory.add_var(name=var_name)
                    const_value = dialog.get_parameter_value()

                old_var = row_data.key_var

                if old_kind == dialog_models.BlockParameterKind.EVENT_PARAMETER:
                    block.event_dict.pop(old_var, None)
                elif old_kind == dialog_models.BlockParameterKind.MODE_PARAMETER:
                    block.mode_dict.pop(old_var, None)
                elif old_kind == dialog_models.BlockParameterKind.FIXED_PARAMETER:
                    block.parameters.pop(old_var, None)

                if new_kind == dialog_models.BlockParameterKind.EVENT_PARAMETER:
                    block.event_dict[new_var] = Const(const_value, name=var_name)
                elif new_kind == dialog_models.BlockParameterKind.MODE_PARAMETER:
                    block.mode_dict[new_var] = Const(const_value, name=var_name)
                elif new_kind == dialog_models.BlockParameterKind.FIXED_PARAMETER:
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
        row_data: dialog_models.BlockParameterRow | None = self.parameters_model.get_row(row_index)
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
            symbol_namespace = dialog_models.build_block_symbol_namespace(self.parameters_model.block)
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
        row_data: dialog_models.BlockParameterRow | None = self.variables_model.get_row(row_index)
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
            symbol_namespace = dialog_models.build_block_symbol_namespace(self.variables_model.block)
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

                if not dialog_models.is_valid_symbol_name(name):
                    raise ValueError("The symbol name must be a valid identifier.")
                elif dialog_models.block_namespace_contains_name(block, name):
                    raise ValueError(f"The symbol '{name}' already exists in this block.")

                new_var = self.var_factory.add_var(name=name)
                dialog_models.add_variable_to_block(
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

                if not dialog_models.is_valid_symbol_name(name):
                    raise ValueError("The symbol name must be a valid identifier.")
                elif dialog_models.block_namespace_contains_name(block, name):
                    raise ValueError(f"The symbol '{name}' already exists in this block.")

                if category == "parameter":
                    static_var_ref = dialog.get_static_variable()
                    new_var = self.var_factory.add_var(name=name, reference=static_var_ref)
                    parameter_value = None
                else:
                    new_var = self.var_factory.add_var(name=name)
                    parameter_value = dialog.get_parameter_value()
                dialog_models.add_variable_to_block(
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

        symbol_namespace = dialog_models.build_block_symbol_namespace(block)
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
            if row_data.kind == dialog_models.BlockParameterKind.STATE_VAR:
                if var in block.state_vars:
                    vars_to_remove_from_state.append(var)
                    if var in block.init_values:
                        init_keys_to_remove.append(var)
            elif row_data.kind == dialog_models.BlockParameterKind.ALGEBRAIC_VAR:
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
            if row_data.kind == dialog_models.BlockParameterKind.EVENT_PARAMETER:
                if var in block.event_dict:
                    del block.event_dict[var]
            elif row_data.kind == dialog_models.BlockParameterKind.MODE_PARAMETER:
                if var in block.mode_dict:
                    del block.mode_dict[var]
            elif row_data.kind == dialog_models.BlockParameterKind.FIXED_PARAMETER:
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
                if row_data.kind == dialog_models.BlockParameterKind.STATE_EQUATION:
                    state_indices_to_remove.add(row_data.item_index)
                elif row_data.kind == dialog_models.BlockParameterKind.ALGEBRAIC_EQUATION:
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
        row_data: dialog_models.BlockParameterRow | None = self.equations_model.get_row(row_index)
        expression_text: str
        dialog: ExpressionTextEditorDialog
        symbol_namespace: Dict[str, Expr]
        parsed_expression: Expr | Comparison
        expression_value: Expr

        if row_data is not None and self.equations_model.block is not None:
            if isinstance(row_data.value, Expr):
                old_expr = row_data.value
                expression_text = symbolic_to_string(row_data.value)
                self.equations_model.symbol_namespace = dialog_models.build_block_symbol_namespace(
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
            deletable_items: List[graph.BlockItem | graph.GenericBlockItem | graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem | graph.PairedItem] = list()
            scene_item: QGraphicsItem

            for scene_item in self.scene.items():
                if isinstance(scene_item, graph.ProtectedConnectionBlockItem):
                    pass
                else:
                    if isinstance(scene_item,
                                  (graph.BlockItem, graph.GenericBlockItem, graph.RoundBaseArithmeticOpItem, graph.RectBaseArithmeticOpItem, graph.PairedItem)):
                        deletable_items.append(scene_item)
                    else:
                        pass

            deletable_item: graph.BlockItem | graph.GenericBlockItem | graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem | graph.PairedItem

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

    def edit_scene_item(self, item: graph.BlockItem | graph.GenericBlockItem | graph.ConnectionItem) -> None:
        """
        Open an editor for the selected scene item when supported.

        :param item: Scene item selected from the context menu.
        :return: None.
        """
        if isinstance(item, (graph.GenericBlockItem, graph.BlockItem)):
            if item.subsys is not None:
                self.request_navigate_to_block(item.subsys)
            else:
                pass
        else:
            pass

    def open_block_rename_dialog(self,
                                 current_name: str) -> tuple[bool, str]:
        """
        Open the modal dialog used to rename one block item.

        :param current_name: Current block name shown to the user.
        :return: Tuple ``(accepted, new_name)``.
        """
        dialog: QDialog = QDialog(self)
        dialog.setWindowTitle(self.tr("Change Block Name"))
        dialog.setModal(True)

        layout: QVBoxLayout = QVBoxLayout(dialog)
        name_edit: QLineEdit = QLineEdit(dialog)
        name_edit.setText(current_name)
        name_edit.selectAll()
        layout.addWidget(name_edit)

        button_box: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                                        QDialogButtonBox.StandardButton.Cancel,
                                                        dialog)
        layout.addWidget(button_box)

        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        accepted: bool = dialog.exec() == QDialog.DialogCode.Accepted
        new_name: str = name_edit.text().strip()
        return accepted, new_name

    def open_variable_rename_dialog(self,
                                    current_name: str) -> tuple[bool, str]:
        """
        Open the modal dialog used to rename one variable item.

        :param current_name: Current variable name shown to the user.
        :return: Tuple ``(accepted, new_name)``.
        """
        dialog: QDialog = QDialog(self)
        dialog.setWindowTitle(self.tr("Change Variable Name"))
        dialog.setModal(True)

        layout: QVBoxLayout = QVBoxLayout(dialog)
        name_edit: QLineEdit = QLineEdit(dialog)
        name_edit.setText(current_name)
        name_edit.selectAll()
        layout.addWidget(name_edit)

        button_box: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                                        QDialogButtonBox.StandardButton.Cancel,
                                                        dialog)
        layout.addWidget(button_box)

        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        accepted: bool = dialog.exec() == QDialog.DialogCode.Accepted
        new_name: str = name_edit.text().strip()
        return accepted, new_name




    def _synchronize_root_connection_var_name(self,
                                              var: Var,
                                              new_name: str) -> None:
        """
        Persist one renamed connection variable back into the root block contract.

        :param var: Renamed editor-side connection variable.
        :param new_name: New variable name.
        :return: None.
        """
        root_var: Var

        for root_var in self.main_block.in_vars:
            if root_var.non_mutable_uid == var.non_mutable_uid:
                root_var.set_name(new_name)
            else:
                pass

        for root_var in self.main_block.out_vars:
            if root_var.non_mutable_uid == var.non_mutable_uid:
                root_var.set_name(new_name)
            else:
                pass

        mapped_var: Var | None
        for mapped_var in self.main_block.external_mapping.values():
            if mapped_var is not None and mapped_var.non_mutable_uid == var.non_mutable_uid:
                mapped_var.set_name(new_name)
            else:
                pass

        self._synchronize_rms_bus_connection_var_name(var=var, new_name=new_name)
        self._synchronize_emt_bus_connection_var_name(var=var, new_name=new_name)

    def _namespace_has_conflicting_variable_name(self,
                                                 var: Var,
                                                 candidate_name: str) -> bool:
        """
        Return whether one candidate variable name conflicts with a different symbol.

        Variables that already represent the same visible connection are treated as one
        logical variable for rename validation, even if reopen/save created distinct
        ``Var`` instances that currently share propagated identity.

        :param var: Variable being renamed.
        :param candidate_name: Candidate new symbolic name.
        :return: ``True`` when a different symbol already uses the name.
        """
        namespace: Dict[str, Expr] = dialog_models.build_block_symbol_namespace(self.main_block)
        current_symbol: Expr | None = namespace.get(candidate_name, None)

        if current_symbol is None:
            return False
        elif current_symbol is var:
            return False
        elif isinstance(current_symbol, Var) and vars_match_for_visible_connection(current_symbol, var):
            return False
        else:
            return True

    def _namespace_has_conflicting_block_name(
            self,
            block: Block,
            candidate_name: str,
    ) -> bool:
        """
        Return whether one candidate block name conflicts with another block.

        :param block: Block being renamed.
        :param candidate_name: Candidate new block name.
        :return: ``True`` when another sibling block already uses the name.
        """
        other_block: Block

        for other_block in self.main_block.children:
            if other_block.uid != block.uid and other_block.name == candidate_name:
                return True
            else:
                pass

        return False


    def _get_authoritative_root_interface_var(
            self,
            block_type: BlockType,
            block_model: Block,
            interface_index: int | None = None,
    ) -> Var | None:
        """
        Resolve the authoritative root variable represented by one wrapper.

        :param block_type: Input or output interface wrapper type.
        :param block_model: Persisted or reconstructed wrapper block.
        :param interface_index: Root-interface position used only as fallback.
        :return: Authoritative root variable, or ``None`` when unresolved.
        """
        root_vars: List[Var]
        wrapper_var: Var | None

        if block_type == BlockType.INPUT_CONN:
            root_vars = self.main_block.in_vars
            if len(block_model.out_vars) > 0:
                wrapper_var = block_model.out_vars[0]
            else:
                wrapper_var = None
        elif block_type == BlockType.OUTPUT_CONN:
            root_vars = self.main_block.out_vars
            if len(block_model.in_vars) > 0:
                wrapper_var = block_model.in_vars[0]
            else:
                wrapper_var = None
        else:
            return None

        return resolve_unique_root_interface_var(
            root_vars=root_vars,
            wrapper_var=wrapper_var,
            interface_index=interface_index,
        )


    def _build_root_interface_wrapper_block(
            self,
            block_type: BlockType,
            fallback_block_model: Block | None,
            interface_index: int | None = None,
            wrapper_uid: int | None = None,
    ) -> Block | None:
        """
        Bind one wrapper block directly to its authoritative root variable.

        The wrapper UID identifies the diagram node. The wrapped variable keeps
        its independent stable and mutable symbolic identities.

        :param block_type: Input or output interface wrapper type.
        :param fallback_block_model: Wrapper found through persisted block identity.
        :param interface_index: Root-interface position used as legacy fallback.
        :param wrapper_uid: Persisted diagram-node UID to preserve.
        :return: Rebound wrapper block, or ``None`` for an unsupported type.
        """
        root_vars: List[Var]
        wrapper_var: Var | None
        reference_var: Var | None
        wrapper_block: Block | None = fallback_block_model
        semantic_reference: VarPowerFlowReferenceType | None = None
        authoritative_ref: VarPowerFlowReferenceType | None = None
        root_var_candidate: Var
        available_root_refs: set[VarPowerFlowReferenceType] = set()

        if fallback_block_model is not None:
            semantic_reference = self._get_semantic_root_interface_reference(
                wrapper_block=fallback_block_model,
                block_type=block_type,
            )
        else:
            pass

        if block_type == BlockType.INPUT_CONN:
            root_vars = self.main_block.in_vars
            if isinstance(self.api_object, BranchParent) and self.mode == DynamicSimulationMode.EMT:
                wrapper_var = None
            elif fallback_block_model is not None and len(fallback_block_model.out_vars) > 0:
                wrapper_var = fallback_block_model.out_vars[0]
            else:
                wrapper_var = None
        elif block_type == BlockType.OUTPUT_CONN:
            root_vars = self.main_block.out_vars
            if isinstance(self.api_object, BranchParent) and self.mode == DynamicSimulationMode.EMT:
                wrapper_var = None
            elif fallback_block_model is not None and len(fallback_block_model.in_vars) > 0:
                wrapper_var = fallback_block_model.in_vars[0]
            else:
                wrapper_var = None
        else:
            return None

        reference_var = None
        if semantic_reference is not None:
            for root_var_candidate in root_vars:
                if root_var_candidate.ref == semantic_reference:
                    reference_var = root_var_candidate
                    break
                else:
                    pass
        else:
            pass

        for root_var_candidate in root_vars:
            if root_var_candidate.ref is None:
                pass
            else:
                available_root_refs.add(root_var_candidate.ref)

        if reference_var is not None:
            authoritative_ref = semantic_reference
        elif isinstance(wrapper_var, Var) and isinstance(wrapper_var.ref, VarPowerFlowReferenceType):
            authoritative_ref = build_branch_authoritative_ref_by_shared_ref(reference=wrapper_var.ref,
                                                                             block_type=block_type,
                                                                             available_root_refs=available_root_refs)
        else:
            authoritative_ref = None

        if reference_var is not None:
            pass
        elif authoritative_ref is not None:
            reference_var = None
            for root_var_candidate in root_vars:
                if root_var_candidate.ref == authoritative_ref:
                    reference_var = root_var_candidate
                    break
                else:
                    pass
        else:
            reference_var = resolve_unique_root_interface_var(
                root_vars=root_vars,
                wrapper_var=wrapper_var,
                interface_index=interface_index,
            )

        # Recover a child wrapper saved while its block UID was overwritten by var.uid.
        if wrapper_block is None and reference_var is not None:
            wrapper_block = find_legacy_interface_wrapper(
                child_blocks=self.main_block.children,
                block_type=block_type,
                reference_var=reference_var,
            )
        else:
            pass

        if wrapper_block is None:
            wrapper_block = Block(uid=wrapper_uid)
        else:
            pass

        wrapper_block.is_root_interface_wrapper = True

        if wrapper_uid is not None:
            wrapper_block.uid = wrapper_uid
        else:
            pass

        # The oval is a direct view over the authoritative root variable, not an
        # independent symbolic variable container.
        if reference_var is not None:
            if block_type == BlockType.INPUT_CONN:
                wrapper_block.in_vars = list()
                wrapper_block.out_vars = list([reference_var])
            else:
                wrapper_block.in_vars = list([reference_var])
                wrapper_block.out_vars = list()

            wrapper_block.set_name(reference_var.name)
        else:
            pass

        return wrapper_block

    def _get_root_interface_index_from_expected_order(self,
                                                      block_type: BlockType,
                                                      node_uid: int) -> int | None:
        """
        Return the authoritative wrapper index for one persisted wrapper node UID.

        :param block_type: Wrapper direction.
        :param node_uid: Persisted wrapper node UID.
        :return: Current authoritative index or ``None``.
        """
        expected_inputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        expected_outputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        ordered_refs: list[VarPowerFlowReferenceType]
        wrapper_nodes: list[tuple[int, BlockDiagramNode]] = list()
        current_index: int
        current_node_uid: int
        current_node: BlockDiagramNode

        expected_inputs_by_ref, expected_outputs_by_ref = build_expected_root_emt_interface_for_device(self.api_object)
        ordered_refs = build_expected_root_interface_ref_order(block_type=block_type,
                                                               input_refs=expected_inputs_by_ref,
                                                               output_refs=expected_outputs_by_ref)

        for current_node_uid, current_node in self.diagram.node_data.items():
            if block_type == BlockType.INPUT_CONN and current_node.tpe == BlockType.INPUT_CONN.name:
                wrapper_nodes.append((current_node_uid, current_node))
            elif block_type == BlockType.OUTPUT_CONN and current_node.tpe == BlockType.OUTPUT_CONN.name:
                wrapper_nodes.append((current_node_uid, current_node))
            else:
                pass

        wrapper_nodes.sort(key=get_block_diagram_node_position_sort_key)

        for current_index, (current_node_uid, _current_node) in enumerate(wrapper_nodes):
            if current_node_uid == node_uid:
                if current_index < len(ordered_refs):
                    return current_index
                else:
                    return None
            else:
                pass

        return None


    def _synchronize_root_interface_names_before_commit(self) -> None:
        """
        Normalize root-interface aliases and names immediately before commit.

        :return: None.
        """
        root_var_groups: tuple[List[Var], List[Var]] = (
            self.main_block.in_vars,
            self.main_block.out_vars,
        )
        root_var_group: List[Var]
        root_var: Var
        mapped_var: Var | None

        # Replay every root alias so the committed working tree matches the
        # VarFactory graph even when the connection was restored after reopen.
        for root_var_group in root_var_groups:
            for root_var in root_var_group:
                self._propagate_alias_to_working_tree(
                    source_non_mutable_uid=root_var.non_mutable_uid,
                    incoming_uid=root_var.uid,
                    incoming_name=root_var.name,
                )

                if isinstance(root_var.ref, VarPowerFlowReferenceType):
                    mapped_var = self.main_block.external_mapping.get(root_var.ref, None)
                    if mapped_var is not None:
                        mapped_var.set_name(root_var.name)
                    else:
                        pass
                else:
                    pass


    def _synchronize_rms_bus_connection_var_name(
            self,
            var: Var,
            new_name: str,
    ) -> None:
        """
        Persist one renamed RMS root variable into matching bus model aliases.

        :param var: Renamed editor-side interface variable.
        :param new_name: New symbolic name.
        :return: None.
        """
        if self.mode == DynamicSimulationMode.RMS:
            if isinstance(self.api_object, InjectionParent):
                if self.api_object.bus is not None:
                    synchronize_matching_mapping_var_name(
                        block_model=self.api_object.bus.rms_model,
                        reference_var=var,
                        new_name=new_name,
                    )
                else:
                    pass
            elif isinstance(self.api_object, BranchParent):
                if self.api_object.bus_from is not None:
                    synchronize_matching_mapping_var_name(
                        block_model=self.api_object.bus_from.rms_model,
                        reference_var=var,
                        new_name=new_name,
                    )
                else:
                    pass

                if self.api_object.bus_to is not None:
                    synchronize_matching_mapping_var_name(
                        block_model=self.api_object.bus_to.rms_model,
                        reference_var=var,
                        new_name=new_name,
                    )
                else:
                    pass
            else:
                pass
        else:
            pass


    def _synchronize_emt_bus_connection_var_name(
            self,
            var: Var,
            new_name: str,
    ) -> None:
        """
        Persist one renamed EMT root variable into matching bus model aliases.

        :param var: Renamed editor-side interface variable.
        :param new_name: New symbolic name.
        :return: None.
        """
        if self.mode == DynamicSimulationMode.EMT:
            if isinstance(self.api_object, InjectionParent):
                if self.api_object.bus is not None:
                    synchronize_matching_mapping_var_name(
                        block_model=self.api_object.bus.emt_model,
                        reference_var=var,
                        new_name=new_name,
                    )
                else:
                    pass
            elif isinstance(self.api_object, BranchParent):
                if self.api_object.bus_from is not None:
                    synchronize_matching_mapping_var_name(
                        block_model=self.api_object.bus_from.emt_model,
                        reference_var=var,
                        new_name=new_name,
                    )
                else:
                    pass

                if self.api_object.bus_to is not None:
                    synchronize_matching_mapping_var_name(
                        block_model=self.api_object.bus_to.emt_model,
                        reference_var=var,
                        new_name=new_name,
                    )
                else:
                    pass
            else:
                pass
        else:
            pass

    def refresh_editor_block_name_displays(self,
                                           block: Block) -> None:
        """
        Refresh every visible editor label that mirrors one block name.

        :param block: Renamed block.
        :return: None.
        """
        scene_item: graph.BlockItem | graph.GenericBlockItem | graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem | None
        scene_item = self.get_scene_item_by_block_uid(block.uid)

        if scene_item is not None:
            if isinstance(scene_item, (graph.BlockItem, graph.GenericBlockItem)):
                scene_item.refresh_block_name()
            else:
                pass
        else:
            pass

        # Rebuild the side-panel models when the renamed block is the one that is
        # currently inspected, because some table cells expose block names as context.
        if self._selected_side_block is not None and self._selected_side_block.uid == block.uid:
            self.refresh_active_side_panel()
        else:
            pass

        # Breadcrumb buttons render ``block.name`` directly, so rebuilding the
        # navigation path is enough to propagate the new label everywhere.
        if self._navigation_delegate is not None:
            self._navigation_delegate.refresh_breadcrumb()
        else:
            pass

        self.scene.update()

    def refresh_editor_variable_displays(self,
                                         var: Var,
                                         renamed_item: graph.BlockItem | None = None) -> None:
        """
        Refresh every visible editor label and tooltip that mirrors one variable.

        :param var: Renamed variable.
        :param renamed_item: Variable oval directly edited by the user.
        :return: None.
        """
        scene_item: QGraphicsItem

        if renamed_item is not None:
            renamed_item.refresh_port_metadata()
            renamed_item.refresh_block_name()
        else:
            pass

        for scene_item in self.scene.items():
            if isinstance(scene_item, graph.BlockItem):
                if renamed_item is not None and scene_item is renamed_item:
                    scene_item.refresh_port_metadata()
                    scene_item.refresh_block_name()
                elif isinstance(scene_item, graph.ProtectedConnectionBlockItem):
                    item_var: Var | None = scene_item.get_interface_var()
                    if vars_match_for_visible_connection(item_var, var):
                        scene_item.refresh_port_metadata()
                        scene_item.refresh_block_name()
                    else:
                        pass
                else:
                    pass
            elif isinstance(scene_item, graph.PairedItem):
                item_var: Var | None = None

                if scene_item.subsys is None:
                    item_var = None
                elif len(scene_item.subsys.in_vars) > 0:
                    item_var = scene_item.subsys.in_vars[0]
                elif len(scene_item.subsys.out_vars) > 0:
                    item_var = scene_item.subsys.out_vars[0]
                else:
                    item_var = None

                if vars_match_for_visible_connection(item_var, var):
                    scene_item.refresh_port_metadata()
                    scene_item.refresh_variable_name()
                else:
                    pass
            else:
                pass

            if isinstance(scene_item, (graph.BlockItem,
                                       graph.GenericBlockItem,
                                       graph.PairedItem,
                                       graph.RoundBaseArithmeticOpItem,
                                       graph.RectBaseArithmeticOpItem,
                                       graph.UnOpItem)):
                ports: List[graph.PortItem] = list()
                ports.extend(scene_item.inputs)
                ports.extend(scene_item.outputs)
                has_matching_var: bool = False
                port: graph.PortItem
                for port in ports:
                    if vars_match_for_visible_connection(port.base_var, var):
                        has_matching_var = True
                    else:
                        pass

                if has_matching_var:
                    scene_item.refresh_port_metadata()
                else:
                    pass
            else:
                pass

        self.scene.update()

    def rename_block_item(self,
                          item: graph.BlockItem | graph.GenericBlockItem) -> None:
        """
        Rename one visible block item through the editor-owned modal flow.

        :param item: Scene block item selected from the context menu.
        :return: None.
        """
        block: Block | None = item.subsys
        accepted: bool
        new_name: str

        if block is None:
            return
        else:
            pass

        accepted, new_name = self.open_block_rename_dialog(block.name)

        if not accepted:
            return
        else:
            pass

        if len(new_name) == 0:
            self.toast_manager.show_warning_toast(
                self.tr("Block name cannot be empty")
            )
            return
        elif not dialog_models.is_valid_symbol_name(new_name):
            self.toast_manager.show_warning_toast(
                self.tr("Block name is invalid")
            )
            return
        elif self._namespace_has_conflicting_block_name(block, new_name):
            self.toast_manager.show_warning_toast(
                self.tr("Block name already exists")
            )
            return
        elif new_name == block.name:
            return
        else:
            pass

        block.set_name(new_name)
        self.refresh_editor_block_name_displays(block)
        self.mark_unapplied_changes()


    def rename_variable_item(
            self,
            item: graph.ProtectedConnectionBlockItem,
    ) -> None:
        """
        Rename one protected root-interface variable and its alias component.

        :param item: Root-interface oval selected from the context menu.
        :return: None.
        """
        block: Block | None = item.subsys
        var: Var | None = item.get_interface_var()
        accepted: bool
        new_name: str

        if block is None or var is None:
            return
        else:
            pass

        accepted, new_name = self.open_variable_rename_dialog(var.name)
        if not accepted:
            return
        else:
            pass

        if len(new_name) == 0:
            self.toast_manager.show_warning_toast(self.tr("Variable name cannot be empty"))
            return
        elif not dialog_models.is_valid_symbol_name(new_name):
            self.toast_manager.show_warning_toast(self.tr("Variable name is invalid"))
            return
        elif self._namespace_has_conflicting_variable_name(var, new_name):
            self.toast_manager.show_warning_toast(self.tr("Variable name already exists"))
            return
        elif new_name == var.name:
            return
        else:
            pass

        # Rename the authoritative root symbol and replay its alias component
        # through both the VarFactory registry and the detached working tree.
        var.set_name(new_name)
        self._synchronize_root_connection_var_name(var=var, new_name=new_name)
        self._propagate_alias_to_working_tree(
            source_non_mutable_uid=var.non_mutable_uid,
            incoming_uid=var.uid,
            incoming_name=new_name,
        )
        block.set_name(new_name)

        # Keep persistence metadata aligned, although rebuild takes the live
        # symbolic variable as the authoritative display name.
        node: BlockDiagramNode | None = self.diagram.node_data.get(block.uid, None)
        candidate_node: BlockDiagramNode
        if node is None:
            for candidate_node in self.diagram.node_data.values():
                if candidate_node.device_uid == block.uid:
                    node = candidate_node
                    break
                else:
                    pass
        else:
            pass

        if node is not None:
            node.name = new_name
        else:
            pass

        self.refresh_editor_variable_displays(var, renamed_item=item)
        self.mark_unapplied_changes()

    def get_scene_item_by_block_uid(self,
                                    block_uid: int) -> graph.BlockItem | graph.GenericBlockItem | graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem | None:
        """
        Find the visible scene item representing a block uid.

        :param block_uid:
        :return:
        """
        item: QGraphicsItem

        for item in self.scene.items():
            if isinstance(item, (graph.BlockItem, graph.GenericBlockItem, graph.RoundBaseArithmeticOpItem,
                                 graph.RectBaseArithmeticOpItem)) and item.subsys is not None:
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
        item: graph.BlockItem | graph.GenericBlockItem | graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem | None = self.get_scene_item_by_block_uid(
            block_uid)

        if item is not None:
            self.scene.clearSelection()
            item.setSelected(True)
        else:
            pass

    def _invalidate_equations_latex(self, old_latex: str) -> None:
        """Drop one cached LaTeX pixmap after the source equation changed."""
        delegate = self._equations_latex_delegate
        if hasattr(delegate, "invalidate"):
            delegate.invalidate(old_latex)
        self.ui.equationsTableView.resizeRowsToContents()

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

    def apply_changes(self) -> None:
        """
        Commit the edited working copy back into the original block.

        :return:
        """
        if self.mode == DynamicSimulationMode.RMS:
            self._synchronize_root_interface_names_before_commit()
            # When the user overwrites a template-assigned EMT model, the device must
            # stop pointing to the reusable template object and keep only the edited
            # concrete model instance.
            if self.api_object.rms_template is not None:
                self.api_object.rms_template = None
            else:
                pass
            # Persist the edited RMS block back into the original model object.
            if self._document is not None:
                self._document.commit()
            else:
                pass
            # Rebuild the connected bus helper models so the saved block stays
            # consistent with the rest of the dynamic network representation.
            dialog_models.initialize_connected_bus_models_for_editor_assignment(api_object=self.api_object,
                                                                   circuit=self.circuit,
                                                                   var_factory=self.var_factory,
                                                                   mode=self.mode)
            # Mark the editor state as clean because all in-memory edits were
            # transferred back to the owned device model successfully.
            self.has_unapplied_changes = False
            self.changes_applied = True
            self.dirtyStateChanged.emit(False)
            self.toast_manager.show_info_toast("Model saved")
            if self.workspace_embedded:
                pass
            else:
                pass

        elif self.mode == DynamicSimulationMode.EMT:
            self._synchronize_root_interface_names_before_commit()
            # When the user overwrites a template-assigned EMT model, the device must
            # stop pointing to the reusable template object and keep only the edited
            # concrete model instance.
            if self.api_object.emt_template is not None:
                self.api_object.emt_template = None
            else:
                pass
            # Persist the edited EMT block exactly as it exists in the editor,
            # just like the RMS save path does. The bus attachment helper is the
            # only stage that should connect the saved model to the bus shells.
            self._remove_shared_branch_emt_root_refs()
            if self._document is not None:
                self._document.commit()
            else:
                pass

            # Saved EMT wrapper roots created through the GUI can keep some
            # static parameters only in child blocks. Mirror them into the saved
            # root immediately after commit so EMT initialization sees the same
            # constant-parameter contract as the scripting/template path.
            dialog_models.synchronize_saved_emt_root_parameters_from_children(device=self.api_object)

            # The previous saved EMT model may already have bus-propagation edges
            # registered in the shared var-factory graph. Remove those stale
            # edges before registering the freshly committed model vars so the
            # next attach step does not accumulate old and new symbolic links.
            dialog_models.unregister_saved_emt_model_var_connections_for_device(device=self.api_object,
                                                                                var_factory=self.var_factory)

            # The committed editor block is a fresh symbolic clone. Register its
            # vars in the shared factory before reconnecting so bus-side uid
            # propagation and EmtProblemDae external-mapping recovery see the
            # same authoritative objects as the scripting/template path.
            dialog_models.register_saved_emt_model_vars_for_device(device=self.api_object,
                                                                   var_factory=self.var_factory)

            dialog_models.initialize_connected_bus_models_for_editor_assignment(api_object=self.api_object,
                                                                                circuit=self.circuit,
                                                                                var_factory=self.var_factory,
                                                                                mode=self.mode)
            dialog_models.attach_emt_model_to_buses(device=self.api_object,
                                                    model=self.api_object.emt_model,
                                                    var_factory=self.var_factory)
            # Mark the editor state as clean because all in-memory edits were
            # transferred back to the owned device model successfully.
            self.has_unapplied_changes = False
            self.changes_applied = True
            self.dirtyStateChanged.emit(False)
            self.toast_manager.show_info_toast("Model saved")
            if self.workspace_embedded:
                pass
            else:
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
        inspect_widget = dialog_models.InspectModel(block=self.main_block, parent=dialog)

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

    def _validate_equation_counts(self, section: valid.ValidationSection, blocks: list[Block]) -> None:
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
            block_label: str = valid.format_validation_block_label(block)
            if len(block.state_vars) != len(block.state_eqs):
                valid.add_validation_detail(
                    section=section,
                    block_label=block_label,
                    detail=f"state vars={len(block.state_vars)}, state eqs={len(block.state_eqs)}",
                )
            else:
                pass

            if len(block.algebraic_vars) != len(block.algebraic_eqs):
                valid.add_validation_detail(
                    section=section,
                    block_label=block_label,
                    detail=f"algebraic vars={len(block.algebraic_vars)}, algebraic eqs={len(block.algebraic_eqs)}",
                )
            else:
                pass

    def _validate_duplicate_variable_names(self, section: valid.ValidationSection, blocks: list[Block]) -> None:
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

            valid.append_vars_to_name_uid_map(name_to_uids=name_to_uids, vars_list=block.state_vars)
            valid.append_vars_to_name_uid_map(name_to_uids=name_to_uids, vars_list=block.algebraic_vars)
            valid.append_vars_to_name_uid_map(name_to_uids=name_to_uids, vars_list=block.diff_vars)
            valid.append_vars_to_name_uid_map(name_to_uids=name_to_uids, vars_list=block.in_vars)
            valid.append_vars_to_name_uid_map(name_to_uids=name_to_uids, vars_list=block.out_vars)
            valid.append_vars_to_name_uid_map(name_to_uids=name_to_uids, vars_list=parameter_vars)
            valid.append_vars_to_name_uid_map(name_to_uids=name_to_uids, vars_list=event_vars)
            valid.append_vars_to_name_uid_map(name_to_uids=name_to_uids, vars_list=mode_vars)

            # Out vars, in vars, mappings and parameter dictionaries often reuse
            # the exact same Var object that already exists in the block state or
            # algebraic collections. That is valid. We only flag names that map
            # to multiple distinct symbolic variables.
            duplicates: list[str] = sorted([name for name, uids in name_to_uids.items() if len(uids) > 1])
            if duplicates:
                valid.add_validation_detail(
                    section=section,
                    block_label=valid.format_validation_block_label(block),
                    detail=f"vars: {', '.join(duplicates)}",
                )
            else:
                pass

    def _validate_parameter_mappings(self, section: valid.ValidationSection, blocks: list[Block]) -> None:
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
                valid.add_validation_detail(
                    section=section,
                    block_label=valid.format_validation_block_label(block),
                    detail=f"params missing mapping: {', '.join(unmapped_parameters)}",
                )
            else:
                pass

            if missing_event_values:
                valid.add_validation_detail(
                    section=section,
                    block_label=valid.format_validation_block_label(block),
                    detail=f"event params with no value: {', '.join(missing_event_values)}",
                )
            else:
                pass

    def _validate_variable_initialization(self, section: valid.ValidationSection,
                                          traversal_nodes: list[valid.ValidationTraversalNode]) -> None:
        """
        Append initialization issues for state, algebraic and diff variables.

        :param section: Mutable grouped section results.
        :param traversal_nodes: Recursive traversal nodes carrying effective mappings.
        :return: None.
        """
        traversal_node: valid.ValidationTraversalNode
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
                valid.add_validation_detail(
                    section=section,
                    block_label=valid.format_validation_block_label(block),
                    detail=f"vars missing init/external mapping: {', '.join(missing_init_vars)}",
                )
            else:
                pass

            if missing_diff_init_vars:
                valid.add_validation_detail(
                    section=section,
                    block_label=valid.format_validation_block_label(block),
                    detail=f"diff vars missing diff init/external mapping: {', '.join(missing_diff_init_vars)}",
                )
            else:
                pass

    def _validate_port_connectivity(self, section: valid.ValidationSection) -> None:
        # todo: rethink this validation
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
                valid.append_missing_port_messages_for_direction(
                    missing_port_messages=missing_port_messages,
                    emt_missing_by_phase=emt_missing_by_phase,
                    vars_list=block.in_vars,
                    node_uid=node_uid,
                    connected_ports=connected_inputs,
                    is_input=True,
                    mode=self.mode,
                )
                valid.append_missing_port_messages_for_direction(
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
                    valid.append_port_vars_to_phase_count(phase_counts=phase_total_ports_by_name, vars_list=block.in_vars)
                    valid.append_port_vars_to_phase_count(phase_counts=phase_total_ports_by_name, vars_list=block.out_vars)
                    phase_name: str
                    phase_missing_messages: list[str]
                    for phase_name, phase_missing_messages in emt_missing_by_phase.items():
                        if phase_missing_messages:
                            phase_total_ports: int = phase_total_ports_by_name[phase_name]
                            phase_missing_count: int = len(phase_missing_messages)
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
                        input_reference: VarPowerFlowReferenceType | None = valid.get_var_reference(var=input_var)
                        if input_reference is not None:
                            missing_input_refs.append(input_reference)
                        else:
                            pass
                    else:
                        pass

                output_var: Var
                for output_var in block.out_vars:
                    if output_var.name in missing_output_names:
                        output_reference: VarPowerFlowReferenceType | None = valid.get_var_reference(var=output_var)
                        if output_reference is not None:
                            missing_output_refs.append(output_reference)
                        else:
                            pass
                    else:
                        pass

                if missing_input_names or missing_output_names:
                    block_label: str = node.name

                    if node.tpe == BlockType.INPUT_CONN.name or node.tpe == BlockType.OUTPUT_CONN.name:
                        # Root interface rows must point back to the visible protected
                        # connector node on canvas, not to the synthetic internal root
                        # variable name used by some rebuilt test/editor states.
                        block_label = node.name
                    else:
                        pass

                    valid.add_validation_port_detail(
                        section=section,
                        block_label=block_label,
                        detail=valid.format_missing_port_detail(
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
                            internal_owner_label = valid.format_validation_block_label(internal_owner_block)
                            valid.add_validation_port_detail(
                                section=section,
                                block_label=internal_owner_label,
                                detail=valid.format_missing_port_detail(
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
                if valid.get_var_reference(var=input_var) in input_refs:
                    return child_block

            for output_var in child_block.out_vars:
                if valid.get_var_reference(var=output_var) in output_refs:
                    return child_block

        return None

    def collect_model_consistency_sections(self) -> list[valid.ValidationSection]:
        """
        Validate the current working model and return grouped section results.

        :return: Ordered validation sections.
        """
        # The full validation runs as a deterministic pipeline so the dialog keeps
        # a stable order and users can compare repeated checks easily.
        blocks: list[Block] = valid.collect_block_tree(root_block=self.main_block)
        traversal_root: valid.ValidationTraversalNode = valid.build_validation_traversal_node(
            block=self.main_block,
            inherited_external_vars=set(),
        )
        traversal_nodes: list[valid.ValidationTraversalNode] = valid.collect_validation_traversal_list(root_node=traversal_root)
        equation_section: valid.ValidationSection = valid.ValidationSection(title="Equation Counts")
        duplicate_section: valid.ValidationSection = valid.ValidationSection(title="Repeated Variable Names")
        parameter_section: valid.ValidationSection = valid.ValidationSection(title="Parameter Mappings")
        init_section: valid.ValidationSection = valid.ValidationSection(title="Variable Initialization")
        port_section: valid.ValidationSection = valid.ValidationSection(title="Port Connectivity")
        self._validate_equation_counts(section=equation_section, blocks=blocks)
        self._validate_duplicate_variable_names(section=duplicate_section, blocks=blocks)
        self._validate_parameter_mappings(section=parameter_section, blocks=blocks)
        self._validate_variable_initialization(section=init_section, traversal_nodes=traversal_nodes)
        self._validate_port_connectivity(section=port_section)

        sections: list[valid.ValidationSection] = list([
            equation_section,
            duplicate_section,
            parameter_section,
            init_section,
            port_section,
        ])

        return sections

    def show_model_consistency_validation(self) -> None:
        """
        Show the current non-blocking model consistency report.

        :return: None.
        """
        # The dialog is informational only. It must never stop the save path, so
        # the method only gathers messages and shows them in one modal report.
        section_results: list[valid.ValidationSection] = self.collect_model_consistency_sections()
        dialog: valid.ValidationSectionDialog = valid.ValidationSectionDialog(section_results=section_results, parent=self)
        dialog.exec()

    def _iter_scene_block_items(self) -> list[graph.BlockItem | graph.GenericBlockItem]:
        """
        Return the visible scene items that support validation highlighting.

        :return: Scene block items.
        """
        scene_block_items: list[graph.BlockItem | graph.GenericBlockItem] = list()
        scene_item: Any

        # Validation highlighting must cover both full generic blocks and the
        # compact connection/interface blocks because the validation report can
        # point to either one when a port is left disconnected.
        for scene_item in self.scene.items():
            if isinstance(scene_item, (graph.BlockItem, graph.GenericBlockItem)):
                scene_block_items.append(scene_item)
            else:
                pass

        return scene_block_items

    def clear_validation_issue_overlay(self) -> None:
        """
        Clear the current validation overlay from blocks and ports.

        :return: None.
        """
        scene_block_item: graph.BlockItem | graph.GenericBlockItem
        port_item: graph.PortItem

        # The overlay is transient GUI state. It must be fully reset before a
        # new overlay is applied and whenever the model changes afterwards.
        for scene_block_item in self._iter_scene_block_items():
            scene_block_item.set_validation_highlighted(False)

            for port_item in scene_block_item.inputs:
                port_item.set_validation_highlighted(False)

            for port_item in scene_block_item.outputs:
                port_item.set_validation_highlighted(False)

        self._validation_issue_overlay_active = False

    def _find_scene_block_item_by_validation_label(self, block_label: str) -> graph.BlockItem | graph.GenericBlockItem | None:
        """
        Resolve one validation block label to its visible scene block item.

        :param block_label: Validation block label.
        :return: Matching scene block item or ``None``.
        """
        scene_block_item: graph.BlockItem | graph.GenericBlockItem
        formatted_label: str

        # Validation rows use the same stable block label formatter as the model
        # traversal, so the scene lookup can remain string-based and local.
        for scene_block_item in self._iter_scene_block_items():
            if isinstance(scene_block_item, graph.ProtectedConnectionBlockItem) and scene_block_item.name == block_label:
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

            formatted_label = valid.format_validation_block_label(scene_block_item.subsys)
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

    def _highlight_ports_by_name(self, scene_block_item: graph.BlockItem | graph.GenericBlockItem, port_names: set[str]) -> bool:
        """
        Highlight the ports whose variable names match the validation report.

        :param scene_block_item: Scene block item that owns the candidate ports.
        :param port_names: Port names to highlight.
        :return: Whether at least one port was highlighted.
        """
        highlighted_any_port: bool = False
        port_item: graph.PortItem
        port_var: Var | None
        tooltip_text: str
        tooltip_name: str | None

        # Connection/interface blocks represent a single exported connection
        # variable. When such a row is reported by the validator, the visible
        # meaning for the user is simply "this exposed connector is wrong", so
        # all visible ports on that compact block are highlighted directly.
        if isinstance(scene_block_item, graph.ProtectedConnectionBlockItem):
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
                                scene_block_item: graph.BlockItem | graph.GenericBlockItem,
                                port_refs: set[VarPowerFlowReferenceType]) -> bool:
        """
        Highlight ports whose semantic references match the validation report.

        :param scene_block_item: Scene block item that owns the candidate ports.
        :param port_refs: Port references to highlight.
        :return: Whether at least one port was highlighted.
        """
        highlighted_any_port: bool = False
        port_item: graph.PortItem
        port_reference: VarPowerFlowReferenceType | None
        candidate_refs: set[VarPowerFlowReferenceType]
        mapped_input_item: graph.ProtectedConnectionBlockItem | None
        mapped_output_item: graph.ProtectedConnectionBlockItem | None

        candidate_refs = set(port_refs)

        if isinstance(scene_block_item, graph.ProtectedConnectionBlockItem) and self.mode == DynamicSimulationMode.EMT:
            interface_inputs_by_ref: Dict[VarPowerFlowReferenceType, graph.ProtectedConnectionBlockItem] = dict()
            interface_outputs_by_ref: Dict[VarPowerFlowReferenceType, graph.ProtectedConnectionBlockItem] = dict()
            scene_item: QGraphicsItem
            protected_item: graph.ProtectedConnectionBlockItem
            reference_var: Var | None

            for scene_item in self.scene.items():
                if isinstance(scene_item, graph.ProtectedConnectionBlockItem):
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
                if mapped_input_item is not None and mapped_input_item.subsys is not None and len(
                        mapped_input_item.subsys.out_vars) > 0:
                    mapped_ref = valid.get_var_reference(var=mapped_input_item.subsys.out_vars[0])
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
                if mapped_output_item is not None and mapped_output_item.subsys is not None and len(
                        mapped_output_item.subsys.in_vars) > 0:
                    mapped_ref = valid.get_var_reference(var=mapped_output_item.subsys.in_vars[0])
                    if mapped_ref is not None:
                        candidate_refs.add(mapped_ref)
                    else:
                        pass
                else:
                    pass
        else:
            pass

        if isinstance(scene_block_item, graph.ProtectedConnectionBlockItem):
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

            reference_var_ref = valid.get_var_reference(var=reference_var)
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

            port_reference = valid.get_var_reference(var=port_item.base_var)
            if port_reference in port_refs:
                port_item.set_validation_highlighted(True)
                highlighted_any_port = True
            else:
                pass

        for port_item in scene_block_item.outputs:
            if port_item.base_var is None:
                continue

            port_reference = valid.get_var_reference(var=port_item.base_var)
            if port_reference in port_refs:
                port_item.set_validation_highlighted(True)
                highlighted_any_port = True
            else:
                pass

        return highlighted_any_port

    def show_validation_issues_in_model(self, section_results: list[valid.ValidationSection]) -> None:
        """
        Apply one transient validation overlay to the current scene.

        :param section_results: Validation sections describing the current issues.
        :return: None.
        """
        valid.build_validation_row_highlight_metadata(section_results=section_results)
        self.clear_validation_issue_overlay()

        section: valid.ValidationSection
        row: valid.ValidationRow
        scene_block_item: graph.BlockItem | graph.GenericBlockItem | None
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

    def _highlight_connectivity_issue_ports_globally(self, section_results: list[valid.ValidationSection]) -> None:
        """
        Highlight visible ports referenced by Port Connectivity across the scene.

        :param section_results: Validation sections describing the current issues.
        :return: None.
        """
        section: valid.ValidationSection
        row: valid.ValidationRow
        scene_block_item: graph.BlockItem | graph.GenericBlockItem
        port_item: graph.PortItem
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
            all_ports: list[graph.PortItem] = list()
            for port_item in scene_block_item.inputs:
                all_ports.append(port_item)
            for port_item in scene_block_item.outputs:
                all_ports.append(port_item)

            for port_item in all_ports:
                port_var = port_item.base_var

                if port_var is not None:
                    port_ref = valid.get_var_reference(var=port_var)
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

        Root interface ovals are rebound directly to ``main_block.in_vars`` or
        ``main_block.out_vars``. Persisted wires then rebuild the same symbolic
        alias graph used by live drag connections.

        :return: None.
        """
        uid_to_blockitem: Dict[
            int,
            graph.BlockItem | graph.GenericBlockItem | graph.RoundBaseArithmeticOpItem |
            graph.RectBaseArithmeticOpItem | graph.UnOpItem | graph.PairedItem,
        ] = dict()
        signal_in_items: List[graph.PairedItem] = list()
        signal_out_items: List[graph.PairedItem] = list()
        legacy_interface_uid_aliases: Dict[int, int | None] = dict()
        uid: int
        node: BlockDiagramNode
        con: BlockDiagramConnection

        self.scene.clear()
        self._ensure_root_interface_wrapper_nodes_exist()
        self._remove_stale_root_interface_duplicate_children()
        self._refresh_interface_wrapper_scene_items()

        # Recreate every persisted node, repairing old wrapper identities in place.
        for uid, node in self.diagram.node_data.items():
            block_type: BlockType | None
            if node.tpe in BlockType.__members__:
                block_type = BlockType[node.tpe]
            else:
                block_type = None

            persisted_node_uid: int = node.device_uid
            block_model: Block | None = self.get_block_from_main_block(persisted_node_uid)
            if block_model is None and persisted_node_uid != uid:
                block_model = self.get_block_from_main_block(uid)
            else:
                pass

            persisted_block_uid: int | None
            if block_model is not None:
                persisted_block_uid = block_model.uid
            else:
                persisted_block_uid = None

            item: graph.PairedItem | graph.RoundBaseArithmeticOpItem | \
                graph.RectBaseArithmeticOpItem | graph.UnOpItem | \
                graph.GenericBlockItem | None = None

            if block_type == BlockType.INPUT_CONN or block_type == BlockType.OUTPUT_CONN:
                repaired_wrapper: Block | None = self._build_root_interface_wrapper_block(
                    block_type=block_type,
                    fallback_block_model=block_model,
                    interface_index=self._get_root_interface_index_from_expected_order(block_type=block_type,
                                                                                      node_uid=uid),
                    wrapper_uid=uid,
                )

                if repaired_wrapper is not None:
                    block_model = repaired_wrapper
                    wrapper_is_registered: bool = False
                    child_block: Block
                    for child_block in self.main_block.children:
                        if child_block is block_model:
                            wrapper_is_registered = True
                        else:
                            pass

                    if wrapper_is_registered:
                        pass
                    else:
                        self.main_block.add(block_model)

                    # Diagram endpoints always reference the wrapper block UID.
                    node.device_uid = uid
                    node.name = block_model.name
                    register_legacy_interface_uid_alias(
                        aliases=legacy_interface_uid_aliases,
                        old_uid=persisted_node_uid,
                        repaired_uid=uid,
                    )
                    register_legacy_interface_uid_alias(
                        aliases=legacy_interface_uid_aliases,
                        old_uid=persisted_block_uid,
                        repaired_uid=uid,
                    )

                    interface_var: Var | None = get_single_interface_var(block_model)
                    if interface_var is not None:
                        register_legacy_interface_uid_alias(
                            aliases=legacy_interface_uid_aliases,
                            old_uid=interface_var.uid,
                            repaired_uid=uid,
                        )
                    else:
                        pass

                    block_item: graph.ProtectedConnectionBlockItem = graph.ProtectedConnectionBlockItem(
                        editor=self,
                        var_factory=self.var_factory,
                        name=block_model.name,
                        mode=self.mode,
                        api_object=self.api_object,
                    )
                    block_item.set_subsystem(block_model)
                    block_item.position_changed_callback = self.build_position_changed_callback(uid)
                    block_item.build_item()
                    block_item.recolour()
                    self.scene.addItem(block_item)
                    block_item.setPos(QPointF(node.x, node.y))
                    uid_to_blockitem[uid] = block_item

                    current_count: int = self.block_counters.get(block_type, 0) + 1
                    self.block_counters[block_type] = current_count
                else:
                    pass
            elif block_model is None:
                # Malformed non-interface nodes are skipped without aborting the rebuild.
                pass
            elif node.tpe == "signal_in" or node.tpe == "signal_out":
                item = graph.PairedItem(
                    editor=self,
                    var_factory=self.var_factory,
                    subsys=block_model,
                    api_object=self.api_object,
                    mode=self.mode,
                    name=block_model.name,
                    position_changed_callback=self.build_position_changed_callback(block_model.uid),
                )
                item.recolour()
                if node.tpe == "signal_in":
                    signal_in_items.append(item)
                else:
                    signal_out_items.append(item)
            elif block_type == BlockType.SUM or block_type == BlockType.PRODUCT:
                count: int = self.block_counters.get(block_type, 0) + 1
                if len(block_model.in_vars) <= 3:
                    item = graph.RoundBaseArithmeticOpItem(
                        var_factory=self.var_factory,
                        subsys=block_model,
                        block_type=block_type,
                        editor=self,
                        position_changed_callback=self.build_position_changed_callback(block_model.uid),
                    )
                else:
                    item = graph.RectBaseArithmeticOpItem(
                        var_factory=self.var_factory,
                        subsys=block_model,
                        block_type=block_type,
                        editor=self,
                        position_changed_callback=self.build_position_changed_callback(block_model.uid),
                    )

                self.block_counters[block_type] = count
                item.recolour()
            elif block_type in self.UNARY_MATH_BLOCK_TYPES:
                if block_type is not None:
                    unary_block_type: BlockType = block_type
                    item = graph.UnOpItem(
                        editor=self,
                        var_factory=self.var_factory,
                        subsys=block_model,
                        api_object=self.api_object,
                        mode=self.mode,
                        block_type=unary_block_type,
                        name=block_model.name,
                        position_changed_callback=self.build_position_changed_callback(block_model.uid),
                    )
                    item.recolour()
                else:
                    pass
            else:
                item = graph.GenericBlockItem(
                    editor=self,
                    var_factory=self.var_factory,
                    subsys=block_model,
                    api_object=self.api_object,
                    mode=self.mode,
                    name=block_model.name,
                    position_changed_callback=self.build_position_changed_callback(block_model.uid),
                )
                item.recolour()

            if item is not None:
                self.scene.addItem(item)
                item.setPos(QPointF(node.x, node.y))
                uid_to_blockitem[uid] = item
            else:
                pass

        # Restore From/To pairs before branches are replayed. Both graphical
        # tags are rebound to one stable symbolic identity, and any legacy
        # downstream VarFactory edges are migrated to that identity.
        self._materialize_missing_root_interface_scene_items(uid_to_blockitem)

        self._restore_signal_pair_relationships(
            signal_input_items=signal_in_items,
            signal_output_items=signal_out_items,
        )

        # Repair legacy connection endpoints only when the old UID maps uniquely.
        for con in self.diagram.con_data.values():
            if con.from_uid not in uid_to_blockitem:
                repaired_from_uid: int | None = legacy_interface_uid_aliases.get(con.from_uid, None)
                if repaired_from_uid is not None:
                    con.from_uid = repaired_from_uid
                else:
                    pass
            else:
                pass

            if con.to_uid not in uid_to_blockitem:
                repaired_to_uid: int | None = legacy_interface_uid_aliases.get(con.to_uid, None)
                if repaired_to_uid is not None:
                    con.to_uid = repaired_to_uid
                else:
                    pass
            else:
                pass

        # Recreate only persisted branches. No inferred EMT interface wiring is added.
        for uid, con in self.diagram.con_data.items():
            src_item: graph.BlockItem | graph.GenericBlockItem | \
                graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem | \
                graph.UnOpItem | graph.PairedItem | None = uid_to_blockitem.get(con.from_uid, None)
            dst_item: graph.BlockItem | graph.GenericBlockItem | \
                graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem | \
                graph.UnOpItem | graph.PairedItem | None = uid_to_blockitem.get(con.to_uid, None)

            if src_item is not None and dst_item is not None:
                source_index_is_valid: bool = 0 <= con.port_number_from < len(src_item.outputs)
                target_index_is_valid: bool = 0 <= con.port_number_to < len(dst_item.inputs)
                if source_index_is_valid and target_index_is_valid:
                    src_port: graph.PortItem = src_item.outputs[con.port_number_from]
                    dst_port: graph.PortItem = dst_item.inputs[con.port_number_to]
                    connection: graph.ConnectionItem = graph.ConnectionItem(
                        src_port,
                        dst_port,
                        diagram=self.diagram,
                        con_uid=uid,
                        editor=self,
                    )
                    self.restore_connection_item(connection, hydrate_graph_payload=True)
                else:
                    pass
            else:
                pass

        # When one persisted diagram exists, the saved branch list is the authoritative
        # source of visible wires. Rebuilding interface graphics from symbolic references
        # here would recreate connections that the user did not save explicitly.

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
        _disconnect_qt_signal(self.ui.toolBox.currentChanged, self.handle_side_panel_page_changed)
        _disconnect_qt_signal(self.scene.selectionChanged, self.on_scene_selection_changed)

    def _dispose_dynamic_search_widgets(self) -> None:
        """
        Remove dynamically inserted search boxes from the side panel layouts.

        These line edits are created programmatically instead of by the .ui file,
        so the editor should explicitly undo those insertions during teardown.

        :return: None.
        """
        _dispose_layout_widget(self.ui.verticalLayout_7, self.variables_search)
        self.variables_search = None
        _dispose_layout_widget(self.ui.verticalLayout_8, self.parameters_search)
        self.parameters_search = None
        _dispose_layout_widget(self.ui.verticalLayout_9, self.equations_search)
        self.equations_search = None

    def _dispose_table_models(self) -> None:
        """
        Detach the table/tree models owned by the editor.

        The editor owns several view-proxy-source chains. Clearing the models
        from the views first shortens the QObject ownership graph before the
        editor widget itself is queued for deletion.

        :return: None.
        """
        _clear_table_view_model(self.ui.libraryTreeView)
        _clear_table_view_model(self.ui.variablesTableView)
        _clear_table_view_model(self.ui.parametersTableView)
        _clear_table_view_model(self.ui.equationsTableView)

        _dispose_qobject(self.library_proxy_model)
        self.library_proxy_model = None
        _dispose_qobject(self.variables_proxy)
        self.variables_proxy = None
        _dispose_qobject(self.parameters_proxy)
        self.parameters_proxy = None
        _dispose_qobject(self.equations_proxy)
        self.equations_proxy = None

        _dispose_qobject(self.library_find_shortcut)
        self.library_find_shortcut = None

        _dispose_dynamic_editor_library(self.library)
        self.library = None
        _dispose_qobject(self.variables_model)
        self.variables_model = None
        _dispose_qobject(self.parameters_model)
        self.parameters_model = None
        _dispose_qobject(self.equations_model)
        self.equations_model = None

    def _dispose_graphics_objects(self) -> None:
        """
        Dismantle the graphics scene/view subtree explicitly.

        The dynamic editor builds a replacement graphics view at runtime and the
        scene owns many C++ graphics items. Clearing and detaching both objects
        eagerly prevents them from surviving until Python garbage collection.

        :return: None.
        """
        self._initial_scene_fit_pending = False
        view: graph.GraphicsView | None = self.view
        scene: graph.DiagramScene | None = self.scene

        _detach_runtime_view_event_handlers(view)
        if view is not None:
            view.setScene(None)
        else:
            pass

        if scene is not None:
            scene.prepare_to_delete()
        else:
            pass

        if view is not None:
            self.ui.verticalLayout_3.removeWidget(view)
            view.setParent(None)
            view.deleteLater()
            self.ui.graphicsView = None
            self.view = None
        else:
            pass

        _dispose_qobject(scene)
        self.scene = None

    def prepare_to_delete(self) -> None:
        """
        Release editor-owned Qt objects before deleting this editor widget.

        :return: None.
        """
        if self._prepared_to_delete:
            return

        self._prepared_to_delete = True
        self.disconnect_editor_signals()

        # Tear down the side-panel models first so no item view keeps proxy/model
        # objects alive after the parent editor starts disappearing.
        self._dispose_table_models()

        # Remove the dynamic line edits explicitly because they were inserted into
        # the UI layouts at runtime and otherwise rely on deferred QObject cleanup.
        self._dispose_dynamic_search_widgets()

        # Finally dismantle the graphics subtree. This is the highest-risk part
        # because it owns many binary Qt graphics objects behind Python wrappers.
        self._dispose_graphics_objects()

        self._navigation_delegate = None
        self.dynamic_editor_entry = None
        self.api_object = None

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
        block_item: graph.BlockItem | None | graph.GenericBlockItem | graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem

        if payload is not None:

            block_item = self.create_library_payload_item(
                payload=payload,
                x_pos=scene_position.x(),
                y_pos=scene_position.y(),
            )

            if block_item is not None:
                block_item.recolour()
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
        self.current_theme = DynEditorGraphicsModes.DARK
        self.set_colors_palet()
        for item in self.scene.items():
            if isinstance(item, (graph.GenericBlockItem, graph.PairedItem, graph.ConnectionItem, graph.RectBaseArithmeticOpItem,
                                 graph.RoundBaseArithmeticOpItem, graph.PortItem, graph.ElbowItem, graph.ResizeHandle, graph.BlockItem)):
                item.recolour()

    def set_light_mode(self):
        """
        Set the dark mode
        :return:
        """
        self.current_theme = DynEditorGraphicsModes.LIGHT
        self.set_colors_palet()
        for item in self.scene.items():
            if isinstance(item, (graph.GenericBlockItem, graph.PairedItem, graph.ConnectionItem, graph.RectBaseArithmeticOpItem,
                                 graph.RoundBaseArithmeticOpItem, graph.PortItem, graph.ElbowItem, graph.ResizeHandle, graph.BlockItem)):
                item.recolour()


if __name__ == "__main__":
    import sys
    import VeraGridEngine.Devices as dev

    app = QtWidgets.QApplication(sys.argv)

    vf = VarFactory()
    bl = Block()
    device = dev.Generator()
    window = DynamicBlockEditorGUI(
        var_factory=vf,
        root_block=bl,
        current_block=bl,
        api_object=device,
        circuit=MultiCircuit(),
        current_theme= DynEditorGraphicsModes.DARK,
    )
    window.show()
    app.exec_()
