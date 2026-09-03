# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
import copy
from typing import Dict, List, Optional, TYPE_CHECKING, Tuple, TypeAlias
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import (QGraphicsItem, QDialog, QVBoxLayout, QDialogButtonBox, QLineEdit)
from PySide6.QtGui import (QDropEvent, QDragEnterEvent, QDragMoveEvent)
from PySide6.QtCore import Qt, QPointF, Signal

from VeraGridEngine.Devices.Parents.branch_parent import BranchParent

from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType, ParamPowerFlowReferenceType, \
    DynamicSimulationMode, DynEditorGraphicsModes
from VeraGridEngine.Utils.Symbolic.bus_emt_template import get_bus_emt_algebraic_vars
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
                                                 find_connections,
                                                 find_matching_dynamic_connection_intent,
                                                 normalize_dynamic_connection_intents,
                                                 refresh_block_tree_var_name_mappings,
                                                 rehash_block_tree_var_keyed_dicts,
                                                 upsert_dynamic_connection_intent)
from VeraGridEngine.Utils.Symbolic.dynamic_connection_intent import (DynamicConnectionIntent,
                                                                     DynamicConnectionIntentDirection,
                                                                     DynamicConnectionIntentOrigin)
from VeraGrid.Gui.DynamicModelEditor.block_editor import Ui_BlockEditorWindow
import VeraGrid.Gui.DynamicModelEditor.dynamic_editor_graphics as graph
from VeraGrid.Session.dynamic_editor_entries import DynamicEditorEntry
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_library import DynamicEditorLibrary, LibraryTreeFilterProxyModel
import VeraGrid.Gui.DynamicModelEditor.dynamic_editor_models as dialog_models
from VeraGrid.Gui.DynamicModelEditor.dynamic_block_properties import (
    BlockStructuralEditRequest,
    BlockVariableRenameRequest,
    DynamicBlockPropertiesDialog,
    DynamicBlockPropertiesDockWidget,
)
import VeraGrid.Gui.DynamicModelEditor.dynamic_editor_validation as valid
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_utilities import (
    create_block_of_type,
    create_default_template_builder,
    create_structural_template_builder,
    create_generic_block,
    copy_template_builder_values,
    GenericBlockTemplateDefinition,
    RlcComboBlockTemplateDefinition,
    get_blocktype2template_builder_dict,
    initialize_template_builder_from_block,
    synchronize_vsc_library_initialization,
)

from VeraGrid.Gui.messages import yes_no_question
from VeraGrid.Gui.toast_widget import ToastManager
from VeraGridEngine.Utils.Symbolic.symbolic import (
    BinOp, Comparison, Const, Expr, Func, Func2, UnOp, Var,
)
from VeraGridEngine.Utils.Symbolic.symbolic_io import duplicate_block
from VeraGridEngine.Utils.procedural_logic import clone_procedural_logic_entries
from VeraGridEngine.Utils.Symbolic.bus_rms_template import get_bus_rms_algebraic_vars
from VeraGridEngine.Utils.Symbolic.templates_common_functions import (
    attach_emt_model_to_buses,
    register_saved_emt_model_vars_for_device,
    synchronize_saved_rms_root_mappings_from_children,
    synchronize_saved_emt_root_parameters_from_children,
    unregister_saved_emt_model_var_connections_for_device,
)
from VeraGridEngine.Utils.SugiyamaLayered import (
    SugiyamaEdge,
    SugiyamaGraph,
    SugiyamaLayeredPythonEngine,
    SugiyamaNode,
    SugiyamaPort,
)
from VeraGridEngine.Utils.SugiyamaLayered.engine import EngineResult
from VeraGridEngine.Templates.template_definition import TemplateDefinition, TemplateProp
from VeraGrid.Gui.DynamicModelEditor.RoutingQt import QtRoutingSession
from VeraGridEngine.enumerations import BlockType, RoutingAxis
from VeraGridEngine.Devices.Diagrams.block_diagram import (
    BlockDiagram, BlockDiagramConnection, BlockDiagramNode,
)

if TYPE_CHECKING:
    from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_tab import DynamicEditorDocument, DynamicEditorTab
else:
    pass

DynamicBlockGraphicsItem: TypeAlias = (
    graph.BlockItem
    | graph.GenericBlockItem
    | graph.RoundBaseArithmeticOpItem
    | graph.RectBaseArithmeticOpItem
    | graph.UnOpItem
    | graph.PairedItem
)


class BlockClipboardEntry:
    """Detached clipboard snapshot for one canvas block without parent arrows."""

    __slots__ = (
        "_block_snapshot",
        "_node_snapshot",
    )

    def __init__(self, block_snapshot: Block, node_snapshot: BlockDiagramNode) -> None:
        """Capture one independent block and its parent-diagram presentation.

        :param block_snapshot: Deep block snapshot preserving the copied content.
        :param node_snapshot: Presentation metadata for the copied canvas node.
        :return: None.
        """
        self._block_snapshot: Block = block_snapshot
        self._node_snapshot: BlockDiagramNode = node_snapshot

    def get_block_snapshot(self) -> Block:
        """
        :return: Detached copied block used as the source for fresh duplication.
        """
        return self._block_snapshot

    def get_node_snapshot(self) -> BlockDiagramNode:
        """
        :return: Detached parent-diagram node presentation.
        """
        return self._node_snapshot


def block_has_internal_equation_content(block: Block) -> bool:
    """Return whether a leaf block owns an operation worth drawing internally.

    Input and output ports describe only the boundary of a subsystem. They do
    not imply that the subsystem contains an operation node. This distinction
    is important for a user-authored ``Generic`` block: before the user adds
    equations, its nested view must contain only its boundary ports.

    :param block: Leaf block whose symbolic contents are inspected.
    :return: Whether the nested editor needs a central operation item.
    """
    result: bool = bool(
        block.state_eqs
        or block.algebraic_eqs
        or block.differential_eqs
        or block.inequalities
        or block.discrete_eqs
        or block.boolean_guards
        or block.procedural_logic
    )
    return result


def get_structural_port_key(variable: Var) -> tuple[str, str]:
    """Return a stable semantic key for one generated block port.

    :param variable: Port variable being matched across reconstruction.
    :return: Key ordered by network reference, shared reference, then name.
    """
    if variable.ref is not None:
        return "reference", str(variable.ref.value)
    elif variable.shared_ref is not None:
        # Shared references are symbolic identities rather than enums. Their
        # uid survives model serialization and therefore matches ports across
        # scene reconstruction without relying on a potentially repeated name.
        return "shared", str(variable.shared_ref.uid)
    else:
        return "name", variable.name


def build_port_index_by_key(variables: List[Var]) -> Dict[tuple[str, str], int]:
    """Index one ordered port list by semantic key.

    :param variables: Ordered input or output variables.
    :return: Semantic-key to port-index lookup.
    """
    result: Dict[tuple[str, str], int] = dict()
    port_index: int
    variable: Var
    for port_index, variable in enumerate(variables):
        result[get_structural_port_key(variable)] = port_index
    return result


def append_sugiyama_edges_from_reference_maps(
        source_map: Dict[object, List[tuple[int, int]]],
        target_map: Dict[object, List[tuple[int, int]]],
        seen_edges: set[tuple[int, int, int, int]],
        layout_edges: List[SugiyamaEdge],
        first_edge_uid: int,
) -> int:
    """Append unique layout edges joining ports with the same reference.

    Shared and power-flow references are indexed independently before this
    function is called. The common materialization step keeps edge ordering and
    duplicate suppression identical for both reference families.

    :param source_map: Reference-to-output-port lookup.
    :param target_map: Reference-to-input-port lookup.
    :param seen_edges: Mutable set of already emitted endpoint tuples.
    :param layout_edges: Mutable ordered collection receiving Sugiyama edges.
    :param first_edge_uid: Identifier assigned to the first newly emitted edge.
    :return: Next free edge identifier.
    """
    edge_uid: int = first_edge_uid
    reference: object
    sources: List[tuple[int, int]]
    targets: List[tuple[int, int]]
    source_uid: int
    source_port_index: int
    target_uid: int
    target_port_index: int

    for reference, sources in source_map.items():
        targets = target_map.get(reference, list())
        if len(targets) > 0:
            for source_uid, source_port_index in sources:
                for target_uid, target_port_index in targets:
                    is_distinct_block: bool = source_uid != target_uid
                    edge_key: tuple[int, int, int, int] = (
                        source_uid,
                        source_port_index,
                        target_uid,
                        target_port_index,
                    )
                    if is_distinct_block and edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        layout_edges.append(
                            SugiyamaEdge(
                                identifier=str(edge_uid),
                                sources=list((f"{source_uid}:out:{source_port_index}",)),
                                targets=list((f"{target_uid}:in:{target_port_index}",)),
                                properties=dict((("source_uid", source_uid), ("source_port_index", source_port_index), ("target_uid", target_uid), ("target_port_index", target_port_index),)),
                            )
                        )
                        edge_uid += 1
                    else:
                        pass
        else:
            pass

    return edge_uid


def count_variables_with_prefix(variables: List[Var], prefix: str) -> int:
    """Count variables whose generated name starts with one prefix.

    :param variables: Candidate variable list.
    :param prefix: Generated-name prefix.
    :return: Number of matching variables.
    """
    result: int = 0
    variable: Var
    for variable in variables:
        if variable.name.startswith(prefix):
            result += 1
        else:
            pass
    return result


def replace_var_sequence(variables: List[Var], replacements: Dict[Var, Var]) -> List[Var]:
    """Replace variables in one sequence while retaining order.

    :param variables: Source variable list.
    :param replacements: Candidate-to-survivor identity mapping.
    :return: Rebound variable list.
    """
    result: List[Var] = list()
    variable: Var
    for variable in variables:
        replacement: Var | None = replacements.get(variable, None)
        if replacement is not None:
            result.append(replacement)
        else:
            result.append(variable)
    return result


def replace_generated_block_auxiliary_variables(block: Block,
                                                replacements: Dict[Var, Var]) -> None:
    """Rebind generated fields omitted by ``Block.update_model_bulk``.

    :param block: Candidate block tree already rebound in primary equations.
    :param replacements: Candidate-to-survivor identity mapping.
    :return: None.
    """
    block.in_vars = replace_var_sequence(block.in_vars, replacements)
    block.out_vars = replace_var_sequence(block.out_vars, replacements)
    block.reformulated_vars = replace_var_sequence(block.reformulated_vars, replacements)

    parameters: Dict[Var, Const] = dict()
    parameter_var: Var
    parameter_value: Const
    for parameter_var, parameter_value in block.parameters.items():
        parameter_replacement: Var | None = replacements.get(parameter_var, None)
        if parameter_replacement is not None:
            parameters[parameter_replacement] = parameter_value
        else:
            parameters[parameter_var] = parameter_value
    block.parameters = parameters

    init_values: Dict[Var, Const] = dict()
    init_var: Var
    init_value: Const
    for init_var, init_value in block.init_values.items():
        init_replacement: Var | None = replacements.get(init_var, None)
        if init_replacement is not None:
            init_values[init_replacement] = init_value
        else:
            init_values[init_var] = init_value
    block.init_values = init_values

    discrete_equations: Dict[Var, Expr] = dict()
    discrete_var: Var
    discrete_expression: Expr
    for discrete_var, discrete_expression in block.discrete_eqs.items():
        discrete_replacement: Var | None = replacements.get(discrete_var, None)
        discrete_key: Var = discrete_var if discrete_replacement is None else discrete_replacement
        discrete_equations[discrete_key] = discrete_expression.subs(replacements)
    block.discrete_eqs = discrete_equations

    api_mapping: Dict[ParamPowerFlowReferenceType, Var] = dict()
    api_reference: ParamPowerFlowReferenceType
    api_var: Var
    for api_reference, api_var in block.api_obj_mapping.items():
        api_replacement: Var | None = replacements.get(api_var, None)
        api_mapping[api_reference] = api_var if api_replacement is None else api_replacement
    block.api_obj_mapping = api_mapping
    block.var_mapping = dict((variable.name, variable) for variable in block.algebraic_vars)

    child: Block
    for child in block.children:
        replace_generated_block_auxiliary_variables(child, replacements)


def apply_generated_block_state(source: Block, target: Block) -> None:
    """Replace one block's generated state while preserving its outer identity.

    :param source: Fully validated and rebound generated candidate.
    :param target: Existing working-tree block referenced by the diagram.
    :return: None.
    """
    target.name = source.name
    target.is_decomposable = source.is_decomposable
    target.tpe_uid = source.tpe_uid
    target.vars_glob_name2uid = source.vars_glob_name2uid
    target.state_vars = source.state_vars
    target.state_eqs = source.state_eqs
    target.algebraic_vars = source.algebraic_vars
    target.algebraic_eqs = source.algebraic_eqs
    target.inequalities = source.inequalities
    target.diff_vars = source.diff_vars
    target.reformulated_vars = source.reformulated_vars
    target.differential_eqs = source.differential_eqs
    target.parameters = source.parameters
    target.init_values = source.init_values
    target.init_eqs = source.init_eqs
    target.diff_init_eqs = source.diff_init_eqs
    target.discrete_eqs = source.discrete_eqs
    target.children = source.children
    target.in_vars = source.in_vars
    target.out_vars = source.out_vars
    target.event_dict = source.event_dict
    target.mode_dict = source.mode_dict
    target.boolean_guards = source.boolean_guards
    target.procedural_logic = source.procedural_logic
    target.connection_intents = source.connection_intents
    target.external_mapping = source.external_mapping
    target.api_obj_mapping = source.api_obj_mapping
    target.var_mapping = source.var_mapping
    target.diagram = source.diagram
    modal_kind: object = source.__dict__.get("_modal_template_kind", None)
    modal_config: object = source.__dict__.get("_modal_template_config", None)
    if isinstance(modal_kind, str) and isinstance(modal_config, dict):
        # Generated builders own serializable, editor-specific configuration.
        # Copy it explicitly because the symbolic field migration above must
        # preserve the outer Block identity referenced by the scene.
        target.__dict__["_modal_template_kind"] = modal_kind
        target.__dict__["_modal_template_config"] = copy.deepcopy(modal_config)
    else:
        pass


def apply_generated_parameter_values(block: Block,
                                     named_values: List[tuple[str, float | complex]]) -> None:
    """Transfer modal numeric values into an already rebuilt block tree.

    :param block: Rebuilt block tree.
    :param named_values: Parameter names and validated values.
    :return: None.
    """
    values_by_name: Dict[str, float | complex] = dict(named_values)
    child: Block
    for child in block.get_all_blocks():
        parameter_groups: tuple[Dict[Var, Const | Expr], ...] = (
            child.parameters,
            child.event_dict,
            child.mode_dict,
        )
        parameter_group: Dict[Var, Const | Expr]
        parameter_var: Var
        parameter_expression: Const | Expr
        for parameter_group in parameter_groups:
            for parameter_var, parameter_expression in parameter_group.items():
                requested_value: float | complex | None = values_by_name.get(parameter_var.name, None)
                if requested_value is not None and isinstance(parameter_expression, Const):
                    parameter_expression.value = requested_value
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
    else:
        pass

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


def is_root_interface_shell_for_type(block_model: Block | None,
                                     block_type: BlockType) -> bool:
    """
    Return whether one block has the pure shell shape for an interface node.

    The diagram owns the semantic role, while the symbolic block only carries
    the variable represented by the node. Verifying both direction and empty
    symbolic contents prevents malformed diagram nodes from being treated as
    protected interface wrappers.

    :param block_model: Candidate block.
    :param block_type: Diagram-side input or output connection type.
    :return: ``True`` when the block matches the requested shell shape.
    """
    interface_var: Var | None = get_single_interface_var(block_model)
    if block_model is None:
        return False
    elif interface_var is None:
        return False
    elif interface_var.ref is None:
        return False
    elif block_type == BlockType.INPUT_CONN and not (
            len(block_model.out_vars) == 1 and len(block_model.in_vars) == 0):
        return False
    elif block_type == BlockType.OUTPUT_CONN and not (
            len(block_model.in_vars) == 1 and len(block_model.out_vars) == 0):
        return False
    elif block_type not in set((BlockType.INPUT_CONN, BlockType.OUTPUT_CONN,)):
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


def is_root_interface_wrapper_block(block_model: Block | None,
                                    diagram: BlockDiagram) -> bool:
    """
    Return whether the diagram declares one block as a root-interface wrapper.

    ``Block`` is a symbolic Engine object and must not store a GUI-only role.
    The persisted :class:`BlockDiagramNode` type is therefore the sole source
    of truth, and the block shape is checked only as a consistency guard.

    :param block_model: Candidate symbolic block.
    :param diagram: Diagram containing the persisted node semantics.
    :return: ``True`` when the diagram and shell shape identify a wrapper.
    """
    diagram_node: BlockDiagramNode | None = None
    candidate_node: BlockDiagramNode

    if block_model is None:
        return False
    else:
        diagram_node = diagram.node_data.get(block_model.uid, None)

    # Older diagrams can key a node by a legacy UID while keeping the current
    # symbolic block UID in ``device_uid``. Accept that serialization shape so
    # reopening repairs identity without restoring GUI state into the Engine.
    if diagram_node is None:
        for candidate_node in diagram.node_data.values():
            if candidate_node.device_uid == block_model.uid:
                diagram_node = candidate_node
                break
            else:
                pass
    else:
        pass

    if diagram_node is None:
        return False
    elif diagram_node.tpe not in BlockType.__members__:
        return False
    else:
        block_type: BlockType = BlockType[diagram_node.tpe]
        return is_root_interface_shell_for_type(block_model=block_model,
                                                block_type=block_type)


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


def build_expected_root_emt_interface_for_device(
        device: ALL_DEV_TYPES,
) -> tuple[dict[VarPowerFlowReferenceType, Var], dict[VarPowerFlowReferenceType, Var]]:
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
            for reference in list((VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.v_A, VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.v_C,)):
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
            from_pairs = list(((VarPowerFlowReferenceType.vf_N, VarPowerFlowReferenceType.v_N), (VarPowerFlowReferenceType.vf_A, VarPowerFlowReferenceType.v_A), (VarPowerFlowReferenceType.vf_B, VarPowerFlowReferenceType.v_B), (VarPowerFlowReferenceType.vf_C, VarPowerFlowReferenceType.v_C),))
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
            to_pairs = list(((VarPowerFlowReferenceType.vt_N, VarPowerFlowReferenceType.v_N), (VarPowerFlowReferenceType.vt_A, VarPowerFlowReferenceType.v_A), (VarPowerFlowReferenceType.vt_B, VarPowerFlowReferenceType.v_B), (VarPowerFlowReferenceType.vt_C, VarPowerFlowReferenceType.v_C),))
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
            preferred_refs = list((VarPowerFlowReferenceType.vf_N, VarPowerFlowReferenceType.vt_N,))
        elif reference == VarPowerFlowReferenceType.v_A:
            preferred_refs = list((VarPowerFlowReferenceType.vf_A, VarPowerFlowReferenceType.vt_A,))
        elif reference == VarPowerFlowReferenceType.v_B:
            preferred_refs = list((VarPowerFlowReferenceType.vf_B, VarPowerFlowReferenceType.vt_B,))
        elif reference == VarPowerFlowReferenceType.v_C:
            preferred_refs = list((VarPowerFlowReferenceType.vf_C, VarPowerFlowReferenceType.vt_C,))
        else:
            preferred_refs = list((reference,))
    elif block_type == BlockType.OUTPUT_CONN:
        if reference == VarPowerFlowReferenceType.i_N:
            preferred_refs = list((VarPowerFlowReferenceType.if_N, VarPowerFlowReferenceType.it_N,))
        elif reference == VarPowerFlowReferenceType.i_A:
            preferred_refs = list((VarPowerFlowReferenceType.if_A, VarPowerFlowReferenceType.it_A,))
        elif reference == VarPowerFlowReferenceType.i_B:
            preferred_refs = list((VarPowerFlowReferenceType.if_B, VarPowerFlowReferenceType.it_B,))
        elif reference == VarPowerFlowReferenceType.i_C:
            preferred_refs = list((VarPowerFlowReferenceType.if_C, VarPowerFlowReferenceType.it_C,))
        else:
            preferred_refs = list((reference,))
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

    __slots__ = ()

    dirtyStateChanged = Signal(bool)

    UNARY_MATH_BLOCK_TYPES: set[BlockType] = set((BlockType.CONST, BlockType.GAIN, BlockType.ABS, BlockType.INTEGRATOR, BlockType.POWER, BlockType.SIN, BlockType.COS, BlockType.TAN, BlockType.EXP, BlockType.LOG, BlockType.LOG10, BlockType.SQRT, BlockType.ASIN, BlockType.ACOS, BlockType.ATAN, BlockType.SINH, BlockType.COSH, BlockType.TANH, BlockType.REAL, BlockType.IMAG, BlockType.CONJ, BlockType.ANGLE,))

    def __init__(self,
                 var_factory: VarFactory,
                 api_object: ALL_DEV_TYPES,
                 circuit: MultiCircuit,
                 current_theme: DynEditorGraphicsModes,
                 mode: DynamicSimulationMode = DynamicSimulationMode.RMS,
                 templates_list: Optional[List[RmsModelTemplate | EmtModelTemplate | FmuTemplate]] = None,
                 is_root_editor: bool = False,
                 modal: bool = True,
                 workspace_embedded: bool = False,
                 root_block: Block | None = None,
                 current_block: Block | None = None,
                 document: DynamicEditorDocument | None = None,
                 block2blocktype: Dict[int, BlockType] | None = None) -> None:
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
        :param current_theme: Initial editor colour mode.
        :param mode: Specifies the editor mode, either RMS or EMT.
        :param templates_list: Optional block-template catalogue entries exposed to the editor.
        :param is_root_editor: Indicates whether this instance is the root-level editor.
        :param modal: Specifies whether the editor window should be modal.
        :param workspace_embedded: Whether the editor is hosted inside the tabbed dynamic-editor workspace.
        :param root_block: Top-level working block (from the document).
        :param current_block: Block currently being edited (from the working tree).
        :param document: Editing document that owns the working block tree.
        :param block2blocktype: Persisted symbolic-block type lookup.
        :return: None.
        """
        super().__init__()

        self.ui = Ui_BlockEditorWindow()
        self.ui.setupUi(self)

        self._library_dock: QtWidgets.QDockWidget | None = None
        self._block_properties_dock: DynamicBlockPropertiesDockWidget | None = None
        self._block_properties_dialogue: DynamicBlockPropertiesDialog | None = None
        self._properties_dock_normalize_timer: QtCore.QTimer | None = QtCore.QTimer(self)
        self._properties_dock_normalize_timer.setSingleShot(True)
        self._properties_dock_normalize_timer.timeout.connect(
            self.normalize_block_properties_right_dock
        )
        self.configure_dynamic_editor_docks()

        # The editor owns its own toast manager so save notifications are
        # stacked above this page instead of behind it on the main window.
        self.toast_manager: ToastManager = ToastManager(parent=self, position_top=False)

        if modal:
            self.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        else:
            pass

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
        self._block_clipboard_entries: List[BlockClipboardEntry] = list()
        self._clipboard_paste_count: int = 0
        self.templates_list: List[
            RmsModelTemplate | EmtModelTemplate | FmuTemplate] = templates_list if templates_list is not None else list()

        self._emt_bus_fallback_warning_shown: bool = False
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

        self.diagram: BlockDiagram = self.main_block.diagram
        initial_non_interface_children: List[Block] = [
            child_block for child_block in self.main_block.children
            if not is_root_interface_wrapper_block(block_model=child_block,
                                                   diagram=self.diagram)
        ]
        atomic_leaf_has_internal_content: bool = (
            not self.is_root_editor
            and len(initial_non_interface_children) == 0
            and block_has_internal_equation_content(self.main_block)
        )
        bootstrap_missing_non_interface_graphics: bool = (
            (
                len(initial_non_interface_children) > 0
                and not any(
                    child_block.uid in self.diagram.node_data
                    for child_block in initial_non_interface_children
                )
            )
            or (
                atomic_leaf_has_internal_content
                and self.main_block.uid not in self.diagram.node_data
            )
        )
        # The navigation tab can retain the child editor's decomposition map
        # while rebuilding an ancestor. Only mappings owned by visible children
        # authorize the legacy missing-arrow repair at the current level.
        current_block_has_mapped_decomposition_children: bool = any(
            child_block.uid in self._block2blocktype
            for child_block in initial_non_interface_children
        )
        restore_missing_decomposed_connections: bool = (
            current_block_has_mapped_decomposition_children
            and len(initial_non_interface_children) > 0
            and len(self.diagram.node_data) > 0
            and len(self.diagram.con_data) == 0
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

        self.view: graph.GraphicsView = graph.GraphicsView(self.scene)
        self.ui.verticalLayout_3.removeWidget(self.ui.graphicsView)
        self.ui.graphicsView.deleteLater()
        self.ui.graphicsView = self.view
        self.ui.verticalLayout_3.addWidget(self.ui.graphicsView)

        # Canvas editing shortcuts are scoped to the graphics view so copy and
        # paste inside the DAE text editor retain their native text behavior.
        self.canvas_copy_shortcut: QtGui.QShortcut = QtGui.QShortcut(
            QtGui.QKeySequence.StandardKey.Copy,
            self.view,
        )
        self.canvas_copy_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.canvas_copy_shortcut.activated.connect(self.copy_selected_blocks)
        self.canvas_paste_shortcut: QtGui.QShortcut = QtGui.QShortcut(
            QtGui.QKeySequence.StandardKey.Paste,
            self.view,
        )
        self.canvas_paste_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.canvas_paste_shortcut.activated.connect(self.paste_copied_blocks)
        self.canvas_delete_shortcut: QtGui.QShortcut = QtGui.QShortcut(
            QtGui.QKeySequence(Qt.Key.Key_Delete),
            self.view,
        )
        self.canvas_delete_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.canvas_delete_shortcut.activated.connect(self.remove_selected_canvas_items)

        # The canvas scene owns the graphical block items dropped from the tree library.
        self.ui.graphicsView.setAcceptDrops(True)
        self.ui.graphicsView.viewport().setAcceptDrops(True)
        self.ui.graphicsView.dragEnterEvent = self.graphicsDragEnterEvent
        self.ui.graphicsView.dragMoveEvent = self.graphicsDragMoveEvent
        self.ui.graphicsView.dropEvent = self.graphicsDropEvent

        # Button do it to save built scene
        self.ui.doItButton.clicked.connect(self.apply_changes)

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

        if self.is_root_editor:
            # Promote explicitly persisted interface nodes before interface
            # reconciliation can remove their diagram records. Serialized
            # blocks do not retain the runtime-only wrapper marker, so both RMS
            # and EMT roots must recover it from the authoritative node type.
            self._recover_legacy_root_interface_nodes()
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

                blockitems_list: List[DynamicBlockGraphicsItem] = list()
                items_by_uid: Dict[int, DynamicBlockGraphicsItem] = dict()
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
                else:
                    pass

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
                    if block_has_internal_equation_content(self.main_block):
                        self.generate_block_item_for_block(self.main_block, 480.0, 260.0)
                    else:
                        # An empty user-authored Generic has no internal
                        # operation to draw. Its nested view is intentionally a
                        # blank canvas bounded only by the input/output wrappers.
                        pass

                    self.add_connection_items()
            else:
                pass


        # Build items for models with graphical info
        elif not self.main_block.diagram.node_data:
            # here we add the connection variables to the main block
            if self.is_root_editor:
                self.add_connection_vars()
            else:
                pass
                # self.add_api_obj_mapping()

            self.add_connection_items()
        else:
            pass
        # A legacy or partially bootstrapped atomic DAE can already own its
        # interface-wrapper nodes while lacking the central operation node.
        # Materialize that node before rebuilding so the saved diagram cannot
        # remain as disconnected boundary ports around an empty canvas.
        if atomic_leaf_has_internal_content and self.main_block.uid not in self.diagram.node_data:
            self.generate_block_item_for_block(self.main_block, 480.0, 260.0)
        else:
            pass

        self.rebuild_scene_from_diagram()
        if restore_missing_decomposed_connections:
            self._restore_missing_decomposed_layout_connections()
        else:
            pass
        if self.main_block.children or atomic_leaf_has_internal_content:
            self._rebuild_missing_non_interface_connections(
                rebuild_interface_connections=(
                    bootstrap_missing_non_interface_graphics
                    or atomic_leaf_has_internal_content
                ),
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

    def set_colors_palet(self) -> None:
        """Select the immutable graphics palette for the current theme.

        :return: None.
        """
        if self.current_theme == DynEditorGraphicsModes.DARK:
            self.colors_palet = graph.EditorGraphicsDefaultsDark()
        else:
            self.colors_palet = graph.EditorGraphicsDefaultsLight()

    def set_navigation_delegate(self, delegate: DynamicEditorTab) -> None:
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
        else:
            pass

    def request_open_block_properties(self, block: Block) -> None:
        """
        Open the modal properties editor for one ordinary symbolic block.

        Root interface wrappers and connection/tool nodes are editor infrastructure,
        not user-authored equation blocks, so they do not expose this dialogue.

        :param block: Symbolic block represented by the double-clicked graphics item.
        :return: None.
        """
        diagram_node: BlockDiagramNode | None = self.diagram.node_data.get(block.uid, None)
        block_type_name: str = "CUSTOM"
        structural_block_type: BlockType | None = None
        structural_builder: TemplateDefinition | None = None
        can_open: bool = not is_root_interface_wrapper_block(block_model=block,
                                                             diagram=self.diagram)

        if diagram_node is not None:
            block_type_name = diagram_node.tpe
            if diagram_node.tpe in set((BlockType.INPUT_CONN.name, BlockType.OUTPUT_CONN.name, BlockType.FROM_GOTO.name,)):
                can_open = False
            else:
                pass
        else:
            pass

        if block_type_name in BlockType.__members__:
            candidate_block_type: BlockType = BlockType[block_type_name]
            if candidate_block_type in self.blocktype2templatebuilder:
                structural_block_type = candidate_block_type
                structural_builder = create_default_template_builder(
                    var_factory=self.var_factory,
                    block_type=candidate_block_type,
                    item_name=block.name,
                    api_object=self.api_object,
                )
                if structural_builder is not None:
                    initialize_template_builder_from_block(
                        builder=structural_builder,
                        block=block,
                        block_type=candidate_block_type,
                    )
                else:
                    pass
            elif candidate_block_type == BlockType.SUM:
                structural_block_type = candidate_block_type
                structural_builder = BasicBlockTemplates.AdderTemplate(vf=self.var_factory)
                minuend_property: TemplateProp | None = structural_builder.params_dict.get("minuend_inputs", None)
                subtrahend_property: TemplateProp | None = structural_builder.params_dict.get("subtrahend_inputs", None)
                if minuend_property is not None:
                    minuend_property.value = count_variables_with_prefix(block.in_vars, "add_")
                else:
                    pass
                if subtrahend_property is not None:
                    subtrahend_property.value = count_variables_with_prefix(block.in_vars, "subtract_")
                else:
                    pass
            elif candidate_block_type == BlockType.PRODUCT:
                structural_block_type = candidate_block_type
                structural_builder = BasicBlockTemplates.ProductTemplate(vf=self.var_factory)
                dividend_property: TemplateProp | None = structural_builder.params_dict.get("divident_inputs", None)
                divisor_property: TemplateProp | None = structural_builder.params_dict.get("divisor_inputs", None)
                if dividend_property is not None:
                    dividend_property.value = count_variables_with_prefix(block.in_vars, "mul_")
                else:
                    pass
                if divisor_property is not None:
                    divisor_property.value = count_variables_with_prefix(block.in_vars, "div_")
                else:
                    pass
            elif candidate_block_type == BlockType.GENERIC:
                structural_block_type = candidate_block_type
                structural_builder = GenericBlockTemplateDefinition(self.var_factory)
                generic_inputs: TemplateProp | None = structural_builder.params_dict.get("inputs", None)
                generic_outputs: TemplateProp | None = structural_builder.params_dict.get("outputs", None)
                generic_name: TemplateProp | None = structural_builder.params_dict.get("name", None)
                if generic_inputs is not None:
                    generic_inputs.value = len(block.in_vars)
                else:
                    pass
                if generic_outputs is not None:
                    generic_outputs.value = len(block.out_vars)
                else:
                    pass
                if generic_name is not None:
                    generic_name.value = block.name
                else:
                    pass
            elif candidate_block_type == BlockType.RLC_COMBO_EMT:
                structural_block_type = candidate_block_type
                structural_builder = RlcComboBlockTemplateDefinition(self.var_factory)
                initialize_template_builder_from_block(
                    builder=structural_builder,
                    block=block,
                    block_type=candidate_block_type,
                )
                component_prefixes: tuple[tuple[str, str], ...] = (
                    ("include_r", "R_"),
                    ("include_l", "L_"),
                    ("include_c", "C_"),
                )
                setting_name: str
                component_prefix: str
                for setting_name, component_prefix in component_prefixes:
                    component_property: TemplateProp | None = structural_builder.params_dict.get(setting_name, None)
                    component_present: bool = False
                    child_block: Block
                    event_var: Var
                    for child_block in block.get_all_blocks():
                        for event_var in child_block.event_dict.keys():
                            if event_var.name.startswith(component_prefix):
                                component_present = True
                            else:
                                pass
                    if component_property is not None:
                        component_property.value = component_present
                    else:
                        pass
            else:
                pass
        else:
            pass

        if can_open:
            self.close_block_properties_dock()
            dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
                block=block,
                block_type_name=block_type_name,
                var_factory=self.var_factory,
                parent=self,
                structural_block_type=structural_block_type,
                structural_builder=structural_builder,
            )
            dialogue.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)
            dialogue.blockApplied.connect(self.on_block_properties_applied)
            dialogue.structuralRebuildRequested.connect(self.on_structural_rebuild_requested)
            dialogue.variableRenameRequested.connect(self.on_variable_rename_requested)
            dialogue.outputExportChangesRequested.connect(self.on_output_export_changes_requested)
            properties_dock: DynamicBlockPropertiesDockWidget = DynamicBlockPropertiesDockWidget(
                properties_widget=dialogue,
                parent=self,
            )
            allowed_areas: Qt.DockWidgetArea = (
                Qt.DockWidgetArea.LeftDockWidgetArea
                | Qt.DockWidgetArea.RightDockWidgetArea
                | Qt.DockWidgetArea.BottomDockWidgetArea
            )
            properties_dock.setAllowedAreas(allowed_areas)
            properties_dock.closed.connect(self.on_block_properties_dock_closed)
            properties_dock.dockLocationChanged.connect(
                self.on_block_properties_dock_location_changed
            )
            properties_dock.topLevelChanged.connect(
                self.on_block_properties_dock_top_level_changed
            )
            self._block_properties_dialogue = dialogue
            self._block_properties_dock = properties_dock

            # Register a legal right-side slot before floating the dock. Qt can
            # then show its native draggable title bar immediately and restore
            # it below the fixed Library when the user drags it back to the
            # editor's right edge.
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, properties_dock)
            if self._library_dock is not None:
                self.splitDockWidget(
                    self._library_dock,
                    properties_dock,
                    Qt.Orientation.Vertical,
                )
            else:
                pass
            properties_dock.setFloating(True)
            properties_dock.resize(1200, 700)
            self.center_floating_block_properties_dock(properties_dock)
            properties_dock.show()
            properties_dock.raise_()
        else:
            pass


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
        item: QGraphicsItem
        for item in self.scene.items():
            if isinstance(item, (graph.GenericBlockItem,
                                 graph.PairedItem,
                                 graph.BlockItem,
                                 graph.RoundBaseArithmeticOpItem,
                                 graph.RectBaseArithmeticOpItem)):
                item.refresh_port_metadata()
            else:
                pass
        self.scene.update()

    # Todo: remove this function when all the dialogs are unified
    def focus_library_search(self) -> None:
        """
        Reveal and focus the library search box.

        :return: None.
        """

        self.ui.toolBox.setCurrentWidget(self.ui.page_7)
        self.activateWindow()
        self.raise_()
        self.ui.librarySearchLineEdit.setFocus(QtCore.Qt.FocusReason.ShortcutFocusReason)
        self.ui.librarySearchLineEdit.selectAll()

    def configure_dynamic_editor_docks(self) -> None:
        """Move the Library into a fixed dock and enable restricted nesting.

        The Library remains permanently attached to the right. Block
        properties can consequently share that edge in a vertical stack while
        retaining the native Qt docking indicators and splitter handles.

        :return: None.
        """
        self.setDockOptions(
            QtWidgets.QMainWindow.DockOption.AnimatedDocks
            | QtWidgets.QMainWindow.DockOption.AllowNestedDocks
        )
        self.setDockNestingEnabled(True)

        library_dock: QtWidgets.QDockWidget = QtWidgets.QDockWidget(
            self.tr("Library"),
            self,
        )
        library_dock.setObjectName("dynamicEditorLibraryDock")
        library_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        library_dock.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFeature.NoDockWidgetFeatures
        )

        # The existing toolbox already renders the Library heading. Suppress a
        # duplicate native title bar while retaining a real dock target.
        hidden_title_bar: QtWidgets.QWidget = QtWidgets.QWidget(library_dock)
        hidden_title_bar.setFixedHeight(0)
        library_dock.setTitleBarWidget(hidden_title_bar)

        self.ui.frame.setParent(None)
        library_dock.setWidget(self.ui.frame)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, library_dock)
        self._library_dock = library_dock
        self.ui.splitter.setStretchFactor(0, 1)
        self.resizeDocks(
            list((library_dock,)),
            list((360,)),
            Qt.Orientation.Horizontal,
        )

    def get_library_dock_widget(self) -> QtWidgets.QDockWidget | None:
        """Return the fixed Library dock owned by this editor.

        :return: Library dock, or ``None`` after editor teardown.
        """
        return self._library_dock

    def get_block_properties_dock_widget(self) -> DynamicBlockPropertiesDockWidget | None:
        """Return the currently open block-properties dock.

        :return: Active properties dock, or ``None`` when closed.
        """
        return self._block_properties_dock

    def center_floating_block_properties_dock(
            self,
            properties_dock: DynamicBlockPropertiesDockWidget,
    ) -> None:
        """Center a new floating properties dock over the Dynamic Editor.

        :param properties_dock: Floating dock to position.
        :return: None.
        """
        editor_top_left: QtCore.QPoint = self.mapToGlobal(QtCore.QPoint(0, 0))
        target_x: int = editor_top_left.x() + max(0, (self.width() - properties_dock.width()) // 2)
        target_y: int = editor_top_left.y() + max(0, (self.height() - properties_dock.height()) // 2)
        screen: QtGui.QScreen | None = self.screen()
        if screen is not None:
            available_geometry: QtCore.QRect = screen.availableGeometry()
            maximum_x: int = available_geometry.right() - properties_dock.width() + 1
            maximum_y: int = available_geometry.bottom() - properties_dock.height() + 1
            target_x = max(available_geometry.left(), min(target_x, maximum_x))
            target_y = max(available_geometry.top(), min(target_y, maximum_y))
        else:
            pass
        properties_dock.move(target_x, target_y)

    @QtCore.Slot(Qt.DockWidgetArea)
    def on_block_properties_dock_location_changed(
            self,
            area: Qt.DockWidgetArea,
    ) -> None:
        """Normalize right-side drops into a vertical Library stack.

        :param area: New main-window dock area reported by Qt.
        :return: None.
        """
        properties_dock: DynamicBlockPropertiesDockWidget | None = self._block_properties_dock
        normalize_timer: QtCore.QTimer | None = self._properties_dock_normalize_timer
        if properties_dock is not None and not properties_dock.isFloating():
            self.resize_block_properties_dock_for_area(area)
            if (normalize_timer is not None
                    and area == Qt.DockWidgetArea.RightDockWidgetArea):
                normalize_timer.start(0)
            else:
                pass
        else:
            pass

    @QtCore.Slot(bool)
    def on_block_properties_dock_top_level_changed(self, floating: bool) -> None:
        """Schedule right-side normalization after a floating dock is attached.

        :param floating: Whether the properties dock is currently floating.
        :return: None.
        """
        properties_dock: DynamicBlockPropertiesDockWidget | None = self._block_properties_dock
        if properties_dock is not None and not floating:
            area: Qt.DockWidgetArea = self.dockWidgetArea(properties_dock)
            self.on_block_properties_dock_location_changed(area)
        else:
            pass

    def resize_block_properties_dock_for_area(
            self,
            area: Qt.DockWidgetArea,
    ) -> None:
        """Give each legal dock area a useful initial share of the editor.

        Users retain the native splitter and can resize the dock afterwards.

        :param area: Main-window area containing Block properties.
        :return: None.
        """
        properties_dock: DynamicBlockPropertiesDockWidget | None = self._block_properties_dock
        library_dock: QtWidgets.QDockWidget | None = self._library_dock
        if properties_dock is not None:
            if area == Qt.DockWidgetArea.BottomDockWidgetArea:
                bottom_height: int = max(280, min(500, int(self.height() * 0.45)))
                self.resizeDocks(
                    list((properties_dock,)),
                    list((bottom_height,)),
                    Qt.Orientation.Vertical,
                )
            elif area == Qt.DockWidgetArea.LeftDockWidgetArea:
                left_width: int = max(420, min(720, int(self.width() * 0.40)))
                self.resizeDocks(
                    list((properties_dock,)),
                    list((left_width,)),
                    Qt.Orientation.Horizontal,
                )
            elif area == Qt.DockWidgetArea.RightDockWidgetArea:
                right_width: int = max(420, min(720, int(self.width() * 0.40)))
                if library_dock is not None:
                    self.resizeDocks(
                        list((library_dock, properties_dock,)),
                        list((right_width, right_width,)),
                        Qt.Orientation.Horizontal,
                    )
                else:
                    self.resizeDocks(
                        list((properties_dock,)),
                        list((right_width,)),
                        Qt.Orientation.Horizontal,
                    )
            else:
                pass
        else:
            pass

    @QtCore.Slot()
    def normalize_block_properties_right_dock(self) -> None:
        """Force a right-side properties dock above or below the Library.

        Qt nesting can otherwise place two docks side by side within the right
        area. The user's vertical drop position selects whether Block
        properties stays above or below the fixed Library.

        :return: None.
        """
        properties_dock: DynamicBlockPropertiesDockWidget | None = self._block_properties_dock
        library_dock: QtWidgets.QDockWidget | None = self._library_dock
        if (properties_dock is not None
                and library_dock is not None
                and not properties_dock.isFloating()
                and self.dockWidgetArea(properties_dock) == Qt.DockWidgetArea.RightDockWidgetArea):
            properties_geometry: QtCore.QRect = properties_dock.geometry()
            library_geometry: QtCore.QRect = library_dock.geometry()
            same_horizontal_span: bool = (
                abs(properties_geometry.left() - library_geometry.left()) <= 2
                and abs(properties_geometry.right() - library_geometry.right()) <= 2
            )
            if same_horizontal_span:
                pass
            elif properties_geometry.center().y() < library_geometry.center().y():
                self.splitDockWidget(
                    properties_dock,
                    library_dock,
                    Qt.Orientation.Vertical,
                )
            else:
                self.splitDockWidget(
                    library_dock,
                    properties_dock,
                    Qt.Orientation.Vertical,
                )
        else:
            pass

    def close_block_properties_dock(self) -> None:
        """Close the active property dock before opening another one.

        :return: None.
        """
        properties_dock: DynamicBlockPropertiesDockWidget | None = self._block_properties_dock
        if properties_dock is not None:
            properties_dock.close()
        else:
            pass

    @QtCore.Slot()
    def on_block_properties_dock_closed(self) -> None:
        """Forget a property dock after either Close control is used.

        :return: None.
        """
        normalize_timer: QtCore.QTimer | None = self._properties_dock_normalize_timer
        if normalize_timer is not None:
            normalize_timer.stop()
        else:
            pass
        self._block_properties_dock = None
        self._block_properties_dialogue = None

    def reset_library_tree_expansion(self) -> None:
        """
        Restore the default expansion depth for the library tree.

        :return: None.
        """

        self.ui.libraryTreeView.collapseAll()
        self.ui.libraryTreeView.expandToDepth(1)

    def on_library_search_text_changed(self, text: str) -> None:
        """
        Filter the library tree according to the current search text.

        :param text: User-entered text.
        :return: None.
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
        Materialize one builder-backed payload with its verified defaults.

        The historical method name is retained temporarily to avoid changing
        unrelated callers, but this path deliberately opens no creation modal.

        :param blocktype: Builder-backed native block type.
        :param x_pos: Scene x coordinate.
        :param y_pos: Scene y coordinate.
        :return: Created graphics item or ``None`` when no builder exists.
        """

        count: int = self.block_counters.get(blocktype, 0) + 1
        item_name: str = f"{blocktype.name}_{count}"

        template_builder: TemplateDefinition | None = create_default_template_builder(
            var_factory=self.var_factory,
            block_type=blocktype,
            item_name=item_name,
            api_object=self.api_object,
        )
        if template_builder is None:
            return None
        else:
            template: EmtModelTemplate | RmsModelTemplate = template_builder.eval()
            block_model: Block = template.block

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

    def create_generic_block_item(self,
                                  block_type: BlockType,
                                  x_pos: float,
                                  y_pos: float) -> graph.GenericBlockItem | None:
        """
        Create and place a one-input/one-output generic block without a wizard.

        :param block_type: Generic native block type stored in the diagram node.
        :param x_pos: Scene x coordinate.
        :param y_pos: Scene y coordinate.
        :return: Created generic graphics item.
        """

        count: int = self.block_counters.get(block_type, 0) + 1
        name: str = f"{block_type.name}_{count}"
        inputs: int = 1
        outputs: int = 1
        model: Block = create_generic_block(self.var_factory, inputs, outputs, name)
        self.block_counters[block_type] = count
        self.main_block.add(model)
        item: graph.GenericBlockItem = graph.GenericBlockItem(
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
        self.diagram.add_node(
            name=name,
            x=x_pos,
            y=y_pos,
            device_uid=model.uid,
            tpe=block_type.name,
            state_ins=inputs,
            state_outs=list(),
            algeb_ins=0,
            algeb_outs=list(),
            subdiagram=model.diagram
        )
        self.mark_unapplied_changes()
        return item

    def create_basic_arithmetic_op_item(self, block_type: BlockType, x_pos: float,
                                        y_pos: float) -> graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem | None:
        """
        Create a default sum or product block without a creation wizard.

        :param block_type: Sum or product native block type.
        :param x_pos: Scene x coordinate.
        :param y_pos: Scene y coordinate.
        :return: Created round/rectangular arithmetic graphics item or ``None``.
        """

        count: int = self.block_counters.get(block_type, 0) + 1
        item_name: str = f"{block_type.name}_{count}"

        template_builder: TemplateDefinition | None = None
        block_model: Block | None = None
        if block_type == BlockType.SUM:
            template_builder = BasicBlockTemplates.AdderTemplate(vf=self.var_factory)
        elif block_type == BlockType.PRODUCT:
            template_builder = BasicBlockTemplates.ProductTemplate(vf=self.var_factory)
        else:
            pass

        if template_builder is not None:
            template: Block = template_builder.eval()
            block_model = template
        else:
            pass

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
        else:
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
                name=block_model.name,
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
            # The factory may give a native block a readable display name while
            # keeping its enum identifier unchanged for persistence.
            block_item.refresh_block_name()

            # The editor block is the authoritative model container for later save/rebuild steps.
            self.main_block.add(block_model)
            self.scene.addItem(block_item)
            block_item.setPos(QtCore.QPointF(x_pos, y_pos))

            # Keep the diagram synchronized so later features can rebuild from the same data source.
            self.diagram.add_node(
                name=block_model.name,
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

    def connect_items(self, items_list: List[graph.BlockItem | graph.GenericBlockItem]) -> None:
        """
        Create all visible connection lines shared by the supplied blocks.

        :param items_list: Block graphics items whose symbolic ports are compared.
        :return: None.
        """

        for item_1 in items_list:
            for item_2 in items_list:
                if item_1.subsys.uid != item_2.subsys.uid:
                    pairs, power_flow_pairs = find_connections(item_1.subsys, item_2.subsys)
                    if pairs:
                        self.create_conn_items(item_1, item_2, pairs)
                    else:
                        pass

                    if power_flow_pairs:
                        self.create_conn_items(item_1, item_2, power_flow_pairs)
                    else:
                        pass

                    pairs, power_flow_pairs = find_connections(item_2.subsys, item_1.subsys)
                    if pairs:
                        self.create_conn_items(item_2, item_1, pairs)
                    else:
                        pass

                    if power_flow_pairs:
                        self.create_conn_items(item_2, item_1, power_flow_pairs)
                    else:
                        pass
                else:
                    pass

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
        """Return the persisted layout kind for one symbolic block.

        :param block_model: Symbolic block being classified.
        :return: Input wrapper, output wrapper, or internal-node kind.
        """
        if len(block_model.out_vars) > 0 and len(block_model.in_vars) == 0:
            return BlockType.INPUT_CONN.name
        else:
            pass
        if len(block_model.in_vars) > 0 and len(block_model.out_vars) == 0:
            return BlockType.OUTPUT_CONN.name
        else:
            pass
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
        """Build the layered-layout graph for internal and interface blocks.

        :param child_blocks: Internal blocks that own equations or submodels.
        :param input_output_blocks: Root interface wrapper blocks.
        :return: Sugiyama graph with ports and shared-reference edges.
        """
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
                else:
                    pass
                if in_var.ref is not None:
                    pf_in_refs.setdefault(in_var.ref, list()).append((block_model.uid, port_index))
                else:
                    pass
                ports.append(
                    SugiyamaPort(
                        identifier=f"{block_model.uid}:in:{port_index}",
                        width=6.0,
                        height=6.0,
                        properties=dict((("role", "input"), ("port_index", port_index), ("var_uid", in_var.uid), ("var_ref", in_var.ref), ("shared_ref", in_var.shared_ref),)),
                        layout_options=dict((("org.vera.sugiyama.port.side", "WEST"),)),
                    )
                )
            for port_index, out_var in enumerate(block_model.out_vars):
                out_uid_lookup[out_var.uid] = port_index
                if out_var.shared_ref is not None:
                    shared_out_refs.setdefault(out_var.shared_ref, list()).append((block_model.uid, port_index))
                else:
                    pass
                if out_var.ref is not None:
                    pf_out_refs.setdefault(out_var.ref, list()).append((block_model.uid, port_index))
                else:
                    pass
                ports.append(
                    SugiyamaPort(
                        identifier=f"{block_model.uid}:out:{port_index}",
                        width=6.0,
                        height=6.0,
                        properties=dict((("role", "output"), ("port_index", port_index), ("var_uid", out_var.uid), ("var_ref", out_var.ref), ("shared_ref", out_var.shared_ref),)),
                        layout_options=dict((("org.vera.sugiyama.port.side", "EAST"),)),
                    )
                )
            layout_nodes.append(
                SugiyamaNode(
                    identifier=str(block_model.uid),
                    width=block_width,
                    height=block_height,
                    ports=ports,
                    properties=dict((("name", block_model.name), ("kind", self._get_layout_block_kind(block_model)),)),
                    layout_options=dict((("org.vera.sugiyama.portConstraints", "FIXED_ORDER"),)),
                )
            )
            out_index_by_uid[block_model.uid] = out_uid_lookup
            in_index_by_uid[block_model.uid] = in_uid_lookup

        edge_uid: int = 1
        seen_edges: set[tuple[int, int, int, int]] = set()
        edge_uid = append_sugiyama_edges_from_reference_maps(
            source_map=shared_out_refs,
            target_map=shared_in_refs,
            seen_edges=seen_edges,
            layout_edges=layout_edges,
            first_edge_uid=edge_uid,
        )
        edge_uid = append_sugiyama_edges_from_reference_maps(
            source_map=pf_out_refs,
            target_map=pf_in_refs,
            seen_edges=seen_edges,
            layout_edges=layout_edges,
            first_edge_uid=edge_uid,
        )

        return SugiyamaGraph(
            identifier="dynamic-block-editor",
            children=layout_nodes,
            edges=layout_edges,
            layout_options=dict((("org.vera.sugiyama.algorithm", "layered"), ("org.vera.sugiyama.direction", "RIGHT"), ("org.vera.sugiyama.edgeRouting", "ORTHOGONAL"), ("org.vera.sugiyama.layered.layering.strategy", "NETWORK_SIMPLEX"), ("org.vera.sugiyama.layered.nodePlacement.strategy", "BRANDES_KOEPF"), ("org.vera.sugiyama.spacing.nodeNode", 50.0), ("org.vera.sugiyama.spacing.componentComponent", 80.0), ("org.vera.sugiyama.layered.spacing.nodeNodeBetweenLayers", 80.0),)),
        )

    def _connect_items_from_layout(
        self,
        items_by_uid: Dict[int, DynamicBlockGraphicsItem],
        layout_graph: SugiyamaGraph,
    ) -> None:
        """
        Persist and render every connection produced by the layout graph.

        The scene is rebuilt from :attr:`diagram` immediately after the
        initial ELK layout. Therefore layout connections must use the same
        controller path as user-created connections instead of existing only
        as temporary scene items.

        :param items_by_uid: Visible block items keyed by symbolic block UID.
        :param layout_graph: Computed layout graph containing routed edges.
        :return: None.
        """
        for edge in layout_graph.edges:
            src_uid = int(edge.properties["source_uid"])
            dst_uid = int(edge.properties["target_uid"])
            src_port_index = int(edge.properties["source_port_index"])
            dst_port_index = int(edge.properties["target_port_index"])

            src_item = items_by_uid.get(src_uid, None)
            dst_item = items_by_uid.get(dst_uid, None)
            if src_item is None or dst_item is None:
                pass
            else:
                src_port: graph.PortItem | None = None
                dst_port: graph.PortItem | None = None
                try:
                    src_port = src_item.outputs[src_port_index]
                    dst_port = dst_item.inputs[dst_port_index]
                except IndexError:
                    pass

                if src_port is not None and dst_port is not None:
                    connection: graph.ConnectionItem = graph.ConnectionItem(
                        source_port=src_port,
                        target_port=dst_port,
                        diagram=self.diagram,
                        con_uid=int(edge.identifier),
                        editor=self,
                    )
                    self.attach_new_connection_item(item=connection)
                else:
                    pass

    def _restore_missing_decomposed_layout_connections(self) -> None:
        """
        Restore arrows omitted by legacy decomposed equation diagrams.

        A previous editor path persisted every ELK-generated node but created
        its edges only as temporary scene items. The subsequent scene rebuild
        erased those arrows, leaving a recognizable diagram with generated
        block types and no persisted branches. Recompute only the edges while
        retaining every saved node position.

        :return: None.
        """
        items_by_uid: Dict[int, DynamicBlockGraphicsItem] = dict()
        child_block: Block
        scene_item: QGraphicsItem | None

        for child_block in self.main_block.children:
            scene_item = self.get_scene_item_by_block_uid(child_block.uid)
            if isinstance(scene_item, (
                    graph.BlockItem,
                    graph.GenericBlockItem,
                    graph.RoundBaseArithmeticOpItem,
                    graph.RectBaseArithmeticOpItem,
                    graph.PairedItem,
            )):
                items_by_uid[child_block.uid] = scene_item
            else:
                pass

        layout_graph: SugiyamaGraph = self._build_elk_layout_graph(
            child_blocks=self.main_block.children,
            input_output_blocks=list(),
        )
        self._connect_items_from_layout(
            items_by_uid=items_by_uid,
            layout_graph=layout_graph,
        )

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


    def create_connection_block(self,
                                var: Var,
                                block_type: BlockType,
                                blocks_list: List[Block] | None) -> None:
        """
        Create and place a block item in the canvas scene.

        :param var: Interface variable represented by the wrapper.
        :param block_type: Input or output connection block type.
        :param blocks_list: Optional ordered collection receiving the new wrapper.
        :return: None.
        """

        block_model: Block = Block()
        block_model.name = f"{var.name}"

        if block_type == BlockType.INPUT_CONN:
            block_model.out_vars.append(var)

        elif block_type == BlockType.OUTPUT_CONN:
            block_model.in_vars.append(var)

        else:
            pass

        if block_model is not None:
            # The symbolic block has to be attached first so the graphics item can build its ports from it.
            # The editor block is the authoritative model container for later save/rebuild steps.
            self.main_block.add(block_model)
            if blocks_list is not None:
                blocks_list.append(block_model)
            else:
                pass
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

    @QtCore.Slot()
    def copy_selected_blocks(self) -> None:
        """Copy selected ordinary blocks without parent-diagram connections.

        Each clipboard entry stores a detached snapshot. Pasting later calls
        ``duplicate_block`` so the block, every child, and every symbolic
        variable receive fresh identities while equations retain equal structure.

        :return: None.
        """
        copied_entries: List[BlockClipboardEntry] = list()
        selected_item: QGraphicsItem
        for selected_item in self.scene.selectedItems():
            is_supported_block: bool = isinstance(
                selected_item,
                (
                    graph.BlockItem,
                    graph.GenericBlockItem,
                    graph.RoundBaseArithmeticOpItem,
                    graph.RectBaseArithmeticOpItem,
                    graph.UnOpItem,
                ),
            )
            if is_supported_block and not isinstance(selected_item, graph.ProtectedConnectionBlockItem):
                source_block: Block | None = selected_item.subsys
            else:
                source_block = None

            if source_block is not None:
                source_node: BlockDiagramNode | None = self.diagram.node_data.get(source_block.uid, None)
                if source_node is None:
                    candidate_node: BlockDiagramNode
                    for candidate_node in self.diagram.node_data.values():
                        if candidate_node.device_uid == source_block.uid:
                            source_node = candidate_node
                            break
                        else:
                            pass
                else:
                    pass
            else:
                source_node = None

            if source_block is not None and source_node is not None:
                copied_entries.append(
                    BlockClipboardEntry(
                        block_snapshot=source_block.copy(),
                        node_snapshot=source_node.copy(),
                    )
                )
            else:
                pass

        if len(copied_entries) > 0:
            self._block_clipboard_entries = copied_entries
            self._clipboard_paste_count = 0
        else:
            pass

    @QtCore.Slot()
    def paste_copied_blocks(self) -> None:
        """Paste fresh block instances while deliberately omitting canvas arrows.

        :return: None.
        """
        if len(self._block_clipboard_entries) == 0:
            return
        else:
            self._clipboard_paste_count += 1

        paste_offset: float = 30.0 * float(self._clipboard_paste_count)
        pasted_block_uids: List[int] = list()
        clipboard_entry: BlockClipboardEntry
        for clipboard_entry in self._block_clipboard_entries:
            cloned_block: Block = duplicate_block(
                block=clipboard_entry.get_block_snapshot(),
                var_factory=self.var_factory,
            )
            source_node: BlockDiagramNode = clipboard_entry.get_node_snapshot()

            # Only the node is added to the parent diagram. No connection record
            # is copied, so neither external nor inter-selection arrows reappear.
            self.main_block.add(cloned_block)
            self.diagram.add_node(
                name=cloned_block.name,
                x=float(source_node.x) + paste_offset,
                y=float(source_node.y) + paste_offset,
                tpe=source_node.tpe,
                device_uid=cloned_block.uid,
                api_object_name=source_node.api_object_name,
                state_ins=source_node.state_ins,
                state_outs=list(source_node.state_outs),
                algeb_ins=source_node.algeb_ins,
                algeb_outs=list(source_node.algeb_outs),
                color=source_node.color,
                subdiagram=cloned_block.diagram if source_node.sub_diagram is not None else None,
            )
            pasted_block_uids.append(cloned_block.uid)

        self.rebuild_scene_from_diagram()
        self.scene.clearSelection()
        pasted_block_uid: int
        for pasted_block_uid in pasted_block_uids:
            pasted_item: DynamicBlockGraphicsItem | None = self.get_scene_item_by_block_uid(pasted_block_uid)
            if pasted_item is not None:
                pasted_item.setSelected(True)
            else:
                pass
        self.mark_unapplied_changes()

    @QtCore.Slot()
    def remove_selected_canvas_items(self) -> None:
        """Apply the existing context-menu Remove behavior to canvas selection.

        Connections are removed first so a selected block can subsequently use
        its established cleanup path without retaining selected stale arrows.
        Protected root-interface blocks are excluded because their context menu
        deliberately does not expose Remove.

        :return: None.
        """
        selected_connections: List[graph.ConnectionItem] = list()
        selected_blocks: List[QGraphicsItem] = list()
        selected_item: QGraphicsItem
        for selected_item in self.scene.selectedItems():
            if isinstance(selected_item, graph.ConnectionItem):
                selected_connections.append(selected_item)
            elif isinstance(
                    selected_item,
                    (
                        graph.BlockItem,
                        graph.GenericBlockItem,
                        graph.RoundBaseArithmeticOpItem,
                        graph.RectBaseArithmeticOpItem,
                        graph.UnOpItem,
                        graph.PairedItem,
                    ),
            ):
                if isinstance(selected_item, graph.ProtectedConnectionBlockItem):
                    pass
                else:
                    selected_blocks.append(selected_item)
            else:
                pass

        connection_item: graph.ConnectionItem
        for connection_item in selected_connections:
            if connection_item.scene() is self.scene:
                self.remove_item(connection_item)
            else:
                pass

        block_item: QGraphicsItem
        for block_item in selected_blocks:
            if block_item.scene() is self.scene:
                self.remove_item(block_item)
            else:
                pass

    # TODO: create PV power plant block item

    def create_library_payload_item(self,
                                    payload: BlockType | BasicBlockTemplateDescriptor | RmsModelTemplate | EmtModelTemplate | FmuTemplate,
                                    x_pos: float,
                                    y_pos: float) -> graph.BlockItem | graph.GenericBlockItem | graph.RoundBaseArithmeticOpItem | graph.RectBaseArithmeticOpItem | graph.PairedItem | None:
        """
        Materialize one library payload on the diagram scene.

        :param payload: Library payload selected by the user.
        :param x_pos: Target scene x coordinate.
        :param y_pos: Target scene y coordinate.
        :return: Diagram item created from the library payload, or ``None`` when unsupported.
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
                    starting_non_mutable_uids=set(list((canonical_var.non_mutable_uid,))),
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
                        signal_output_items=list((signal_output_item,)),
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
            signal_output_items=list((item_out,)),
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
        # A rename can be initiated from a downstream block editor. Resolve the
        # upstream owner while retaining the established directional graph.
        source_non_mutable_uid = self.var_factory.get_connection_source_non_mutable_uid(
            variable_non_mutable_uid=source_non_mutable_uid,
        )

        # Snapshot names before the factory propagation because some models
        # share Var objects directly between the factory and working tree.
        vars_by_uid: Dict[int, List[Var]] = build_working_var_index(self.root_block)
        previous_names_by_uid: Dict[int, set[str]] = dict()
        indexed_non_mutable_uid: int
        indexed_vars: List[Var]
        indexed_var: Var
        indexed_names: set[str]
        for indexed_non_mutable_uid, indexed_vars in vars_by_uid.items():
            indexed_names = set()
            for indexed_var in indexed_vars:
                indexed_names.add(indexed_var.name)
            previous_names_by_uid[indexed_non_mutable_uid] = indexed_names

        # Synchronize the canonical variables kept by the shared factory first.
        self.var_factory.connect_variables_by_uid(
            source_non_mutable_uid,
            incoming_uid,
            incoming_name,
        )

        # Mirror the same graph traversal into the document working copy. The
        # working tree can contain different Var objects with the same stable UID.
        connection_graph: Dict[int, List[Connection]] = self.var_factory.get_connections_dict()
        pending: List[int] = list((source_non_mutable_uid,))
        visited: set[int] = set()
        current_non_mutable_uid: int
        working_vars: List[Var] | None
        working_var: Var
        connection_records: List[Connection] | None
        connection_record: Connection
        previous_names: set[str] = set()
        procedural_var_mapping: Dict[Expr | str, Expr] = dict()
        replacement_var: Var | None = None
        block_model: Block
        previous_name: str
        stable_previous_names: set[str] | None

        while len(pending) > 0:
            current_non_mutable_uid = pending.pop()
            if current_non_mutable_uid not in visited:
                visited.add(current_non_mutable_uid)

                working_vars = vars_by_uid.get(current_non_mutable_uid, None)
                if working_vars is not None:
                    stable_previous_names = previous_names_by_uid.get(current_non_mutable_uid, None)
                    if stable_previous_names is not None:
                        previous_names.update(stable_previous_names)
                    else:
                        pass
                    for working_var in working_vars:
                        working_var.uid = incoming_uid
                        working_var.set_name(incoming_name)
                        if replacement_var is None:
                            replacement_var = working_var
                        else:
                            pass
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
        rehash_block_tree_var_keyed_dicts(root_block=self.root_block)
        refresh_block_tree_var_name_mappings(root_block=self.root_block)

        # Procedural entries store output and target variables by textual name.
        # Reuse their established remap API so connect, rename and disconnect
        # keep those fields aligned with the same propagated network label.
        if replacement_var is not None:
            for previous_name in previous_names:
                if previous_name != incoming_name:
                    procedural_var_mapping[previous_name] = replacement_var
                else:
                    pass

            if len(procedural_var_mapping) > 0:
                for block_model in self.root_block.get_all_blocks():
                    if len(block_model.procedural_logic) > 0:
                        block_model.procedural_logic = clone_procedural_logic_entries(
                            entries=block_model.procedural_logic,
                            var_mapping=procedural_var_mapping,
                        )
                    else:
                        pass
            else:
                pass
        else:
            pass


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
        direction: DynamicConnectionIntentDirection | None = None
        internal_block_uid: int | None = None
        internal_variable_uid: int | None = None
        source_block: Block | None = None
        target_block: Block | None = None
        entry: DynamicConnectionIntent
        existing_entry: DynamicConnectionIntent | None

        source_block = None if source_port.subsystem is None else source_port.subsystem.subsys
        target_block = None if target_port.subsystem is None else target_port.subsystem.subsys

        if is_root_interface_wrapper_block(block_model=source_block,
                                           diagram=self.diagram):
            root_ref = self._get_semantic_root_interface_reference(
                wrapper_block=source_block,
                block_type=BlockType.INPUT_CONN,
            )
            if root_ref is not None:
                direction = DynamicConnectionIntentDirection.INPUT
                if target_block is not None and 0 <= target_port.index < len(target_block.in_vars):
                    internal_block_uid = target_block.uid
                    internal_variable_uid = target_block.in_vars[target_port.index].non_mutable_uid
                else:
                    pass
            else:
                pass
        else:
            if is_root_interface_wrapper_block(block_model=target_block,
                                               diagram=self.diagram):
                root_ref = self._get_semantic_root_interface_reference(
                    wrapper_block=target_block,
                    block_type=BlockType.OUTPUT_CONN,
                )
                if root_ref is not None:
                    direction = DynamicConnectionIntentDirection.OUTPUT
                    if source_block is not None and 0 <= source_port.index < len(source_block.out_vars):
                        internal_block_uid = source_block.uid
                        internal_variable_uid = source_block.out_vars[source_port.index].non_mutable_uid
                    else:
                        pass
                else:
                    pass
            else:
                pass

        if root_ref is None or direction is None or internal_block_uid is None or internal_variable_uid is None:
            return
        else:
            pass

        if suppressed:
            existing_entry = find_matching_dynamic_connection_intent(
                block=self.main_block,
                origin=DynamicConnectionIntentOrigin.TEMPLATE_DERIVED,
                root_reference=root_ref,
                direction=direction,
                internal_block_uid=internal_block_uid,
                internal_variable_uid=internal_variable_uid,
            )
            if existing_entry is not None:
                existing_entry.set_suppressed(suppressed=True)
                normalize_dynamic_connection_intents(block=self.main_block)
                return
            else:
                pass
        else:
            pass

        entry = DynamicConnectionIntent(
            origin=DynamicConnectionIntentOrigin.USER,
            root_reference=root_ref,
            direction=direction,
            internal_block_uid=internal_block_uid,
            internal_variable_uid=internal_variable_uid,
            suppressed=suppressed,
        )
        upsert_dynamic_connection_intent(block=self.main_block, intent=entry)

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
        input_var: Var
        output_var: Var
        existing_entry: DynamicConnectionIntent | None
        new_entry: DynamicConnectionIntent

        for child_block in self.main_block.children:
            if is_root_interface_wrapper_block(block_model=child_block,
                                               diagram=self.diagram):
                pass
            else:
                for input_var in child_block.in_vars:
                    if input_var.ref is None:
                        pass
                    else:
                        existing_entry = find_matching_dynamic_connection_intent(
                            block=self.main_block,
                            origin=DynamicConnectionIntentOrigin.TEMPLATE_DERIVED,
                            root_reference=input_var.ref,
                            direction=DynamicConnectionIntentDirection.INPUT,
                            internal_block_uid=child_block.uid,
                            internal_variable_uid=input_var.non_mutable_uid,
                        )
                        if existing_entry is None:
                            new_entry = DynamicConnectionIntent(
                                origin=DynamicConnectionIntentOrigin.TEMPLATE_DERIVED,
                                root_reference=input_var.ref,
                                direction=DynamicConnectionIntentDirection.INPUT,
                                internal_block_uid=child_block.uid,
                                internal_variable_uid=input_var.non_mutable_uid,
                                suppressed=False,
                            )
                            upsert_dynamic_connection_intent(block=self.main_block, intent=new_entry)
                        else:
                            pass

                for output_var in child_block.out_vars:
                    if output_var.ref is None:
                        pass
                    else:
                        existing_entry = find_matching_dynamic_connection_intent(
                            block=self.main_block,
                            origin=DynamicConnectionIntentOrigin.TEMPLATE_DERIVED,
                            root_reference=output_var.ref,
                            direction=DynamicConnectionIntentDirection.OUTPUT,
                            internal_block_uid=child_block.uid,
                            internal_variable_uid=output_var.non_mutable_uid,
                        )
                        if existing_entry is None:
                            new_entry = DynamicConnectionIntent(
                                origin=DynamicConnectionIntentOrigin.TEMPLATE_DERIVED,
                                root_reference=output_var.ref,
                                direction=DynamicConnectionIntentDirection.OUTPUT,
                                internal_block_uid=child_block.uid,
                                internal_variable_uid=output_var.non_mutable_uid,
                                suppressed=False,
                            )
                            upsert_dynamic_connection_intent(block=self.main_block, intent=new_entry)
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
        entry: DynamicConnectionIntent
        direction: DynamicConnectionIntentDirection
        child_block: Block | None
        wrapper_block: Block | None
        wrapper_item: graph.BlockItem | graph.GenericBlockItem | None
        internal_item: graph.BlockItem | graph.GenericBlockItem | None
        source_port: graph.PortItem | None
        target_port: graph.PortItem | None
        interface_reference: VarPowerFlowReferenceType | None
        candidate_block_type: BlockType
        candidate_reference: VarPowerFlowReferenceType | None
        internal_port_index: int | None
        child_candidate: Block

        for entry in self.main_block.connection_intents:
            if entry.is_suppressed():
                pass
            else:
                direction = entry.get_direction()
                interface_reference = entry.get_root_reference()
                child_block = self.get_block_from_main_block(entry.get_internal_block_uid())
                source_port = None
                target_port = None
                wrapper_block = None

                if child_block is None:
                    pass
                else:
                    internal_port_index = self._find_intent_internal_port_index(
                        child_block=child_block,
                        direction=direction,
                        internal_variable_uid=entry.get_internal_variable_uid(),
                    )
                    if internal_port_index is None:
                        pass
                    else:
                        interface_reference = self._resolve_persisted_intent_interface_reference(
                            persisted_reference=interface_reference,
                            child_block=child_block,
                            direction=direction,
                            internal_variable_uid=entry.get_internal_variable_uid(),
                        )
                        if interface_reference is not None:
                            entry.set_root_reference(root_reference=interface_reference)
                        else:
                            pass

                        if direction == DynamicConnectionIntentDirection.INPUT:
                            candidate_block_type = BlockType.INPUT_CONN
                        else:
                            candidate_block_type = BlockType.OUTPUT_CONN

                        for child_candidate in self.main_block.children:
                            if is_root_interface_wrapper_block(block_model=child_candidate,
                                                               diagram=self.diagram):
                                candidate_reference = self._get_semantic_root_interface_reference(
                                    wrapper_block=child_candidate,
                                    block_type=candidate_block_type,
                                )

                                if candidate_reference == interface_reference:
                                    if (direction == DynamicConnectionIntentDirection.INPUT
                                            and len(child_candidate.out_vars) == 1):
                                        wrapper_block = child_candidate
                                    elif (direction == DynamicConnectionIntentDirection.OUTPUT
                                          and len(child_candidate.in_vars) == 1):
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
                                if direction == DynamicConnectionIntentDirection.INPUT:
                                    if len(wrapper_item.outputs) > 0 and internal_port_index < len(internal_item.inputs):
                                        source_port = wrapper_item.outputs[0]
                                        target_port = internal_item.inputs[internal_port_index]
                                    else:
                                        pass
                                else:
                                    if len(wrapper_item.inputs) > 0 and internal_port_index < len(internal_item.outputs):
                                        source_port = internal_item.outputs[internal_port_index]
                                        target_port = wrapper_item.inputs[0]
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

        normalize_dynamic_connection_intents(self.main_block)
        return changed

    def _find_intent_internal_port_index(self,
                                         child_block: Block,
                                         direction: DynamicConnectionIntentDirection,
                                         internal_variable_uid: int) -> int | None:
        """
        Find the current graphical port position from a stable variable UID.

        :param child_block: Internal block targeted by the intent.
        :param direction: Connection direction.
        :param internal_variable_uid: Non-mutable UID of the target variable.
        :return: Current port index or ``None`` when the variable is unavailable.
        """
        variables: List[Var]
        port_index: int
        candidate_var: Var

        if direction == DynamicConnectionIntentDirection.INPUT:
            variables = child_block.in_vars
        else:
            variables = child_block.out_vars

        for port_index, candidate_var in enumerate(variables):
            if candidate_var.non_mutable_uid == internal_variable_uid:
                return port_index
            else:
                pass

        return None

    def _resolve_persisted_intent_interface_reference(
            self,
            persisted_reference: VarPowerFlowReferenceType,
            child_block: Block,
            direction: DynamicConnectionIntentDirection,
            internal_variable_uid: int,
    ) -> VarPowerFlowReferenceType | None:
        """
        Resolve one persisted intent to the current side-specific root reference.

        Older branch-editor user intents may store a shared bus reference such
        as ``v_A``. The connected internal Pi/template port still carries the
        unambiguous side-specific reference, so it can upgrade the intent to
        ``vf_A`` or ``vt_A`` during reopen.

        :param persisted_reference: Reference stored in the intent record.
        :param child_block: Internal block targeted by the intent.
        :param direction: Internal port direction.
        :param internal_variable_uid: Internal variable non-mutable UID.
        :return: Current root-interface reference, or ``None`` when unavailable.
        """
        expected_inputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        expected_outputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        available_refs: set[VarPowerFlowReferenceType]
        internal_var: Var | None = None
        internal_port_index: int | None

        expected_inputs_by_ref, expected_outputs_by_ref = self._build_expected_root_interface_for_current_mode()
        available_refs = set(expected_inputs_by_ref.keys()) | set(expected_outputs_by_ref.keys())

        if persisted_reference in available_refs:
            return persisted_reference
        else:
            pass

        if not isinstance(self.api_object, BranchParent):
            return None
        else:
            internal_port_index = self._find_intent_internal_port_index(
                child_block=child_block,
                direction=direction,
                internal_variable_uid=internal_variable_uid,
            )

        if internal_port_index is None:
            pass
        elif direction == DynamicConnectionIntentDirection.INPUT:
            internal_var = child_block.in_vars[internal_port_index]
        else:
            internal_var = child_block.out_vars[internal_port_index]

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
        entry: DynamicConnectionIntent
        child_block: Block | None
        canonical_reference: VarPowerFlowReferenceType | None

        normalize_dynamic_connection_intents(self.main_block)

        for entry in self.main_block.connection_intents:
            child_block = self.get_block_from_main_block(entry.get_internal_block_uid())
            if child_block is None:
                pass
            else:
                canonical_reference = self._resolve_persisted_intent_interface_reference(
                    persisted_reference=entry.get_root_reference(),
                    child_block=child_block,
                    direction=entry.get_direction(),
                    internal_variable_uid=entry.get_internal_variable_uid(),
                )
                if canonical_reference is not None:
                    entry.set_root_reference(root_reference=canonical_reference)
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
        paired_item: graph.PairedItem
        paired_dependents: List[graph.PairedItem] = list()
        candidate_item: graph.PairedItem
        surviving_paired_items: List[graph.PairedItem]

        if isinstance(item, graph.PairedItem):
            # A From tag owns the canonical variable used by every associated
            # To tag. Removing only that owner leaves output tags that cannot be
            # rebound after save/reopen, so remove its dependants as one group.
            if item.is_signal_in and item.paired_items is not None:
                for paired_item in list(item.paired_items):
                    if not paired_item.is_signal_in and paired_item.scene() is self.scene:
                        paired_dependents.append(paired_item)
                    else:
                        pass
            else:
                pass

            for paired_item in paired_dependents:
                self.remove_block_item(paired_item)

            # Removing one To tag remains a local operation. In both cases,
            # prune the bidirectional runtime relationship before Qt destroys
            # the scene item so no surviving tag retains a stale Python object.
            if item.paired_items is not None:
                for paired_item in list(item.paired_items):
                    if paired_item.paired_items is not None:
                        surviving_paired_items = list()
                        for candidate_item in paired_item.paired_items:
                            if candidate_item is not item:
                                surviving_paired_items.append(candidate_item)
                            else:
                                pass
                        paired_item.paired_items = surviving_paired_items
                        if len(paired_item.paired_items) == 0:
                            paired_item.paired_items = None
                        else:
                            pass
                    else:
                        pass
                item.paired_items = None
            else:
                pass
        else:
            pass

        # find connections to remove
        port_collection: List[graph.PortItem]
        for port_collection in (item.inputs, item.outputs):
            for port in port_collection:
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
        node_data: BlockDiagramNode | None = None
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

    def add_connection_vars_rms(self) -> None:
        """
        Add a block with bus connection variables to connect the device (RMS)
        :return: None.
        """

        if isinstance(self.api_object, BranchParent):

            # connect bus variables
            # get bus variables for bus from
            if self.api_object.bus_from.is_dc:
                Vf_dc, _, _ = get_bus_rms_algebraic_vars(self.api_object.bus_from.rms_model)
                if Vf_dc is not None:
                    self.main_block.in_vars.append(Vf_dc)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.Vmf, Vf_dc),)))
                    # add connection variables
                    Pf = self.var_factory.add_var('net_conn_Pf', VarPowerFlowReferenceType.Pf, True)
                    self.main_block.out_vars.append(Pf)
                    self.main_block.external_mapping.update(dict(((VarPowerFlowReferenceType.Pf, Pf),)))
                else:
                    raise ValueError("Invalid RMS bus model: expected Vdc, None, None")
            else:
                _, Vmf, Vaf = get_bus_rms_algebraic_vars(self.api_object.bus_from.rms_model)

                self.main_block.in_vars.append(Vmf)
                self.main_block.in_vars.append(Vaf)

                self.main_block.external_mapping.update(
                    dict(((VarPowerFlowReferenceType.Vmf, Vmf),)))
                self.main_block.external_mapping.update(
                    dict(((VarPowerFlowReferenceType.Vaf, Vaf),)))

                # add connection variables
                Pf = self.var_factory.add_var('net_conn_Pf', VarPowerFlowReferenceType.Pf, True)
                Qf = self.var_factory.add_var('net_conn_Qf', VarPowerFlowReferenceType.Qf, True)

                self.main_block.out_vars.append(Pf)
                self.main_block.out_vars.append(Qf)

                self.main_block.external_mapping.update(dict(((VarPowerFlowReferenceType.Pf, Pf),)))
                self.main_block.external_mapping.update(dict(((VarPowerFlowReferenceType.Qf, Qf),)))

            # get bus variables for bus to
            if self.api_object.bus_to.is_dc:
                Vt_dc, _, _ = get_bus_rms_algebraic_vars(self.api_object.bus_to.rms_model)
                if Vt_dc is not None:
                    self.main_block.in_vars.append(Vt_dc)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.Vt_dc, Vt_dc),)))
                    # add connection variables
                    Pt = self.var_factory.add_var('net_conn_Pt', VarPowerFlowReferenceType.Pt, True)
                    self.main_block.out_vars.append(Pt)
                    self.main_block.external_mapping.update(dict(((VarPowerFlowReferenceType.Pt, Pt),)))
                else:
                    raise ValueError("Invalid RMS bus model: expected Vdc, None, None")

            else:
                _, Vmt, Vat = get_bus_rms_algebraic_vars(self.api_object.bus_to.rms_model)

                self.main_block.in_vars.append(Vmt)
                self.main_block.in_vars.append(Vat)

                self.main_block.external_mapping.update(
                    dict(((VarPowerFlowReferenceType.Vmt, Vmt),)))
                self.main_block.external_mapping.update(
                    dict(((VarPowerFlowReferenceType.Vat, Vat),)))
                # add connection variables
                Pt = self.var_factory.add_var('net_conn_Pt', VarPowerFlowReferenceType.Pt, True)
                Qt = self.var_factory.add_var('net_conn_Qt', VarPowerFlowReferenceType.Qt, True)

                self.main_block.out_vars.append(Pt)
                self.main_block.out_vars.append(Qt)

                self.main_block.external_mapping.update(dict(((VarPowerFlowReferenceType.Pt, Pt),)))
                self.main_block.external_mapping.update(dict(((VarPowerFlowReferenceType.Qt, Qt),)))

        elif isinstance(self.api_object, InjectionParent):

            # connect bus variables

            if self.api_object.bus.is_dc:
                Vdc, _, _ = get_bus_rms_algebraic_vars(self.api_object.bus.rms_model)
                if Vdc is not None:
                    self.main_block.in_vars.append(Vdc)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.Vdc, Vdc),)))

                    # add connection variables
                    P = self.var_factory.add_var('net_conn_P', VarPowerFlowReferenceType.P, True)

                    self.main_block.out_vars.append(P)
                    self.main_block.external_mapping.update(dict(((VarPowerFlowReferenceType.P, P),)))
                else:
                    pass
            else:
                _, Vm, Va = get_bus_rms_algebraic_vars(self.api_object.bus.rms_model)
                self.main_block.in_vars.append(Vm)
                self.main_block.in_vars.append(Va)

                self.main_block.external_mapping.update(
                    dict(((VarPowerFlowReferenceType.Vm, Vm),)))
                self.main_block.external_mapping.update(
                    dict(((VarPowerFlowReferenceType.Va, Va),)))

                # add connection variables
                P = self.var_factory.add_var('net_conn_P', VarPowerFlowReferenceType.P, True)
                Q = self.var_factory.add_var('net_conn_Q', VarPowerFlowReferenceType.Q, True)

                self.main_block.out_vars.append(P)
                self.main_block.out_vars.append(Q)

                self.main_block.external_mapping.update(dict(((VarPowerFlowReferenceType.P, P),)))
                self.main_block.external_mapping.update(dict(((VarPowerFlowReferenceType.Q, Q),)))
        else:
            pass

    def add_connection_vars_emt(self) -> None:
        """
        Add a block with bus connection variables to connect the device (EMT)
        :return: None.
        """

        if isinstance(self.api_object, BranchParent):

            # connect bus variables

            # get bus variables for bus from
            if self.api_object.bus_from.is_dc:
                Vf_dc, _, _, _ = get_bus_emt_algebraic_vars(self.api_object.bus_from.emt_model)

                if Vf_dc is not None:
                    self.main_block.in_vars.append(Vf_dc)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.Vdc, Vf_dc),)))
                    # add connection variables (currents)
                    If_dc = self.var_factory.add_var('net_conn_If_dc', VarPowerFlowReferenceType.If_dc, True)
                    self.main_block.out_vars.append(If_dc)
                    self.main_block.external_mapping.update(dict(((VarPowerFlowReferenceType.If_dc, If_dc),)))
                else:
                    raise ValueError("Invalid EMT bus model: expected Vdc, None, None, None")
            else:
                vf_N, vf_A, vf_B, vf_C = get_bus_emt_algebraic_vars(self.api_object.bus_from.emt_model)

                if vf_N is not None:
                    self.main_block.in_vars.append(vf_N)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.vf_N, vf_N),)))
                    # add connection variables (currents)
                    if_N = self.var_factory.add_var('net_conn_if_N', VarPowerFlowReferenceType.if_N, True)
                    self.main_block.out_vars.append(if_N)
                    self.main_block.external_mapping.update(dict(((VarPowerFlowReferenceType.if_N, if_N),)))
                else:
                    pass
                if vf_A is not None:
                    self.main_block.in_vars.append(vf_A)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.vf_A, vf_A),)))
                    # add connection variables (currents)
                    if_A = self.var_factory.add_var('net_conn_if_A', VarPowerFlowReferenceType.if_A, True)
                    self.main_block.out_vars.append(if_A)
                    self.main_block.external_mapping.update(dict(((VarPowerFlowReferenceType.if_A, if_A),)))
                else:
                    pass
                if vf_B is not None:
                    self.main_block.in_vars.append(vf_B)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.vf_B, vf_B),)))
                    # add connection variables (currents)
                    if_B = self.var_factory.add_var('net_conn_if_B', VarPowerFlowReferenceType.if_B, True)
                    self.main_block.out_vars.append(if_B)
                    self.main_block.external_mapping.update(dict(((VarPowerFlowReferenceType.if_B, if_B),)))
                else:
                    pass
                if vf_C is not None:
                    self.main_block.in_vars.append(vf_C)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.vf_C, vf_C),)))
                    # add connection variables (currents)
                    if_C = self.var_factory.add_var('net_conn_if_C', VarPowerFlowReferenceType.if_C, True)
                    self.main_block.out_vars.append(if_C)
                    self.main_block.external_mapping.update(dict(((VarPowerFlowReferenceType.if_C, if_C),)))
                else:
                    pass


            # get bus variables for bus to
            if self.api_object.bus_to.is_dc:
                Vt_dc, _, _, _ = get_bus_emt_algebraic_vars(self.api_object.bus_to.emt_model)

                if Vt_dc is not None:
                    self.main_block.in_vars.append(Vt_dc)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.Vt_dc, Vt_dc),)))
                    # add connection variables (currents)
                    It_dc = self.var_factory.add_var('net_conn_It_dc', VarPowerFlowReferenceType.It_dc, True)
                    self.main_block.out_vars.append(It_dc)
                    self.main_block.external_mapping.update(dict(((VarPowerFlowReferenceType.It_dc, It_dc),)))
                else:
                    raise ValueError("Invalid EMT bus model: expected Vdc, None, None, None")

            else:
                vt_N, vt_A, vt_B, vt_C = get_bus_emt_algebraic_vars(self.api_object.bus_to.emt_model)

                if vt_N is not None:
                    self.main_block.in_vars.append(vt_N)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.vt_N, vt_N),)))
                    # add connection variables (currents)
                    it_N = self.var_factory.add_var('net_conn_it_N', VarPowerFlowReferenceType.it_N, True)
                    self.main_block.out_vars.append(it_N)
                    self.main_block.external_mapping.update(dict(((VarPowerFlowReferenceType.it_N, it_N),)))
                else:
                    pass
                if vt_A is not None:
                    self.main_block.in_vars.append(vt_A)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.vt_A, vt_A),)))
                    # add connection variables (currents)
                    it_A = self.var_factory.add_var('net_conn_it_A', VarPowerFlowReferenceType.it_A, True)
                    self.main_block.out_vars.append(it_A)
                    self.main_block.external_mapping.update(dict(((VarPowerFlowReferenceType.it_A, it_A),)))
                else:
                    pass
                if vt_B is not None:
                    self.main_block.in_vars.append(vt_B)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.vt_B, vt_B),)))
                    # add connection variables (currents)
                    it_B = self.var_factory.add_var('net_conn_it_B', VarPowerFlowReferenceType.it_B, True)
                    self.main_block.out_vars.append(it_B)
                    self.main_block.external_mapping.update(dict(((VarPowerFlowReferenceType.it_B, it_B),)))
                else:
                    pass
                if vt_C is not None:
                    self.main_block.in_vars.append(vt_C)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.vt_C, vt_C),)))
                    # add connection variables (currents)
                    it_C = self.var_factory.add_var('net_conn_it_C', VarPowerFlowReferenceType.it_C, True)
                    self.main_block.out_vars.append(it_C)
                    self.main_block.external_mapping.update(dict(((VarPowerFlowReferenceType.it_C, it_C),)))
                else:
                    pass



        elif isinstance(self.api_object, InjectionParent):

            # connect bus variables

            if self.api_object.bus.is_dc:
                Vdc, _, _, _ = get_bus_emt_algebraic_vars(self.api_object.bus.emt_model)

                if Vdc is not None:
                    self.main_block.in_vars.append(Vdc)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.Vdc, Vdc),)))
                    # add connection variables (currents)
                    Idc = self.var_factory.add_var('net_conn_Idc', VarPowerFlowReferenceType.Idc, True)
                    self.main_block.out_vars.append(Idc)
                    self.main_block.external_mapping.update(dict(((VarPowerFlowReferenceType.Idc, Idc),)))
                else:
                    raise ValueError("Invalid EMT bus model: expected Vdc, None, None, None")
            else:
                v_N, v_A, v_B, v_C = get_bus_emt_algebraic_vars(self.api_object.bus.emt_model)

                if v_N is not None:
                    self.main_block.in_vars.append(v_N)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.v_N, v_N),)))
                    # add connection variables
                    i_N = self.var_factory.add_var('net_conn_i_N', VarPowerFlowReferenceType.i_N, True)
                    self.main_block.out_vars.append(i_N)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.i_N, i_N),)))
                else:
                    pass
                if v_A is not None:
                    self.main_block.in_vars.append(v_A)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.v_A, v_A),)))
                    # add connection variables
                    i_A = self.var_factory.add_var('net_conn_i_A', VarPowerFlowReferenceType.i_A, True)
                    self.main_block.out_vars.append(i_A)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.i_A, i_A),)))
                else:
                    pass
                if v_B is not None:
                    self.main_block.in_vars.append(v_B)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.v_B, v_B),)))
                    # add connection variables
                    i_B = self.var_factory.add_var('net_conn_i_B', VarPowerFlowReferenceType.i_B, True)
                    self.main_block.out_vars.append(i_B)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.i_B, i_B),)))
                else:
                    pass
                if v_C is not None:
                    self.main_block.in_vars.append(v_C)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.v_C, v_C),)))
                    # add connection variables
                    i_C = self.var_factory.add_var('net_conn_i_C', VarPowerFlowReferenceType.i_C, True)
                    self.main_block.out_vars.append(i_C)
                    self.main_block.external_mapping.update(
                        dict(((VarPowerFlowReferenceType.i_C, i_C),)))
                else:
                    pass
        else:
            pass


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
        """Scale bootstrap interface positions around their common centre.

        :return: Updated interface bounds, or ``None`` when no wrappers exist.
        """
        interface_items: list[graph.ProtectedConnectionBlockItem] = [
            item for item in self.scene.items()
            if isinstance(item, graph.ProtectedConnectionBlockItem)
        ]

        if not interface_items:
            return None
        else:
            pass

        bounding_rect = QtCore.QRectF()
        for item in interface_items:
            br = item.sceneBoundingRect()
            bounding_rect = br if bounding_rect.isNull() else bounding_rect.united(br)

        center = bounding_rect.center()

        for item in interface_items:
            offset = item.pos() - center
            item.setPos(center + offset * graph.EditorGraphicsCommonFeatures.INITIAL_LAYOUT_SCALE)

        for node in self.diagram.node_data.values():
            if node.tpe in set((BlockType.INPUT_CONN.name, BlockType.OUTPUT_CONN.name,)):
                for item in interface_items:
                    if item.subsys.uid == node.device_uid:
                        node.x = item.pos().x()
                        node.y = item.pos().y()
                        break
                    else:
                        pass
            else:
                pass

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

        expected_inputs_by_ref, expected_outputs_by_ref = self._build_expected_root_interface_for_current_mode()
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

    def _build_expected_root_interface_for_current_mode(
            self,
    ) -> tuple[dict[VarPowerFlowReferenceType, Var], dict[VarPowerFlowReferenceType, Var]]:
        """
        Return the authoritative interface for the active editor level.

        EMT derives its contract from the live bus topology. RMS models already
        carry their contract in block input/output variables. The device root
        supplies the network-facing contract, while a nested block supplies its
        own local boundary contract.

        :return: ``(input_vars_by_ref, output_vars_by_ref)``.
        """
        if self.mode == DynamicSimulationMode.EMT:
            return build_expected_root_emt_interface_for_device(self.api_object)
        else:
            pass

        input_vars_by_ref: dict[VarPowerFlowReferenceType, Var] = dict()
        output_vars_by_ref: dict[VarPowerFlowReferenceType, Var] = dict()
        input_vars_by_identity: dict[int, Var] = dict()
        output_vars_by_identity: dict[int, Var] = dict()
        mapped_input_identities: set[int] = set()
        mapped_output_identities: set[int] = set()
        root_var: Var
        mapping_ref: VarPowerFlowReferenceType
        mapped_var: Var | None
        mapped_root_var: Var | None

        # At root level, the device root owns the network-facing contract. A
        # nested editor instead owns a local boundary around the block being
        # inspected. Binding nested wrappers to ``root_block`` would alias the
        # internal Pf/Pt variables to the device connection variables merely
        # by navigating into the block.
        if self.is_root_editor:
            interface_owner: Block = self.root_block
        else:
            interface_owner = self.main_block

        for root_var in interface_owner.in_vars:
            input_vars_by_identity[root_var.non_mutable_uid] = root_var

        for root_var in interface_owner.out_vars:
            output_vars_by_identity[root_var.non_mutable_uid] = root_var

        # RMS branch roots reuse the endpoint bus variables, whose own refs are
        # the generic ``Vm``/``Va`` pair on both buses. The root external mapping
        # provides the authoritative side-specific refs (``Vmf``/``Vaf`` and
        # ``Vmt``/``Vat``), so resolve it before falling back to each Var.ref.
        for mapping_ref, mapped_var in interface_owner.external_mapping.items():
            if not isinstance(mapping_ref, VarPowerFlowReferenceType) or mapped_var is None:
                pass
            else:
                mapped_root_var = input_vars_by_identity.get(mapped_var.non_mutable_uid, None)
                if mapped_root_var is not None and mapping_ref not in input_vars_by_ref:
                    input_vars_by_ref[mapping_ref] = mapped_root_var
                    mapped_input_identities.add(mapped_root_var.non_mutable_uid)
                else:
                    mapped_root_var = output_vars_by_identity.get(mapped_var.non_mutable_uid, None)
                    if mapped_root_var is not None and mapping_ref not in output_vars_by_ref:
                        output_vars_by_ref[mapping_ref] = mapped_root_var
                        mapped_output_identities.add(mapped_root_var.non_mutable_uid)
                    else:
                        pass

        for root_var in interface_owner.in_vars:
            if (isinstance(root_var.ref, VarPowerFlowReferenceType)
                    and root_var.ref not in input_vars_by_ref
                    and root_var.non_mutable_uid not in mapped_input_identities):
                input_vars_by_ref[root_var.ref] = root_var
            else:
                pass

        for root_var in interface_owner.out_vars:
            if (isinstance(root_var.ref, VarPowerFlowReferenceType)
                    and root_var.ref not in output_vars_by_ref
                    and root_var.non_mutable_uid not in mapped_output_identities):
                output_vars_by_ref[root_var.ref] = root_var
            else:
                pass

        return input_vars_by_ref, output_vars_by_ref

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



    def add_measurements_items(self):
        # Here we need to create the measurements items
        pass

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
        Remove persisted diagram nodes that incorrectly represent the container.

        Root editor containers are never operations. An empty non-root leaf is
        also only an editable boundary: older editor versions persisted a copy
        of that leaf between its own ports, which made an empty ``Generic``
        appear to contain itself. Removing that stale node also migrates files
        saved while that regression was present.

        :return: ``True`` when any invalid self node or connection was removed.
        """
        node_uids_to_remove: list[int] = list()
        node_uid: int
        node: BlockDiagramNode
        changed: bool = False
        block_type: BlockType | None

        remove_self_nodes: bool = self.is_root_editor or (
            not self.main_block.children
            and not block_has_internal_equation_content(self.main_block)
        )
        if not remove_self_nodes:
            return False
        else:
            pass

        for node_uid, node in self.diagram.node_data.items():
            if node.tpe in BlockType.__members__:
                block_type = BlockType[node.tpe]
            else:
                block_type = None

            if block_type in set((BlockType.INPUT_CONN, BlockType.OUTPUT_CONN,)):
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

        expected_inputs_by_ref, expected_outputs_by_ref = self._build_expected_root_interface_for_current_mode()
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
            if not is_root_interface_wrapper_block(block_model=child_block,
                                                   diagram=self.diagram):
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

    def _recover_legacy_root_interface_nodes(self) -> bool:
        """
        Recover missing interface-node types in legacy root diagrams.

        Current files persist wrapper semantics as ``INPUT_CONN`` and
        ``OUTPUT_CONN`` diagram nodes. Older diagrams can contain a pure
        one-port shell with a missing or generic node type. Only shells whose
        root reference belongs to the current device interface are migrated,
        keeping this compatibility decision inside the GUI layer.

        :return: ``True`` when any legacy diagram node was recovered.
        """
        child_block: Block
        interface_var: Var | None
        expected_inputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        expected_outputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        changed: bool = False
        diagram_node: BlockDiagramNode | None
        recovered_block_type: BlockType | None
        recovered_x: float
        recovered_y: float
        input_index: int = 0
        output_index: int = 0

        if not self.is_root_editor:
            return False
        else:
            pass

        expected_inputs_by_ref, expected_outputs_by_ref = self._build_expected_root_interface_for_current_mode()

        for child_block in self.main_block.children:
            interface_var = get_single_interface_var(child_block)
            diagram_node = self.diagram.node_data.get(child_block.uid, None)
            recovered_block_type = None

            if interface_var is None or interface_var.ref is None:
                pass
            elif is_root_interface_shell_for_type(block_model=child_block,
                                                  block_type=BlockType.INPUT_CONN) and (
                    interface_var.ref in expected_inputs_by_ref):
                recovered_block_type = BlockType.INPUT_CONN
            elif is_root_interface_shell_for_type(block_model=child_block,
                                                  block_type=BlockType.OUTPUT_CONN) and (
                    interface_var.ref in expected_outputs_by_ref):
                recovered_block_type = BlockType.OUTPUT_CONN
            else:
                pass

            if recovered_block_type is None:
                pass
            elif diagram_node is not None and diagram_node.tpe == recovered_block_type.name:
                pass
            elif diagram_node is not None:
                diagram_node.tpe = recovered_block_type.name
                diagram_node.device_uid = child_block.uid
                changed = True
            elif recovered_block_type == BlockType.INPUT_CONN:
                recovered_x = 100.0
                recovered_y = 100.0 + (100.0 * input_index)
                self.diagram.add_node(name=child_block.name,
                                      x=recovered_x,
                                      y=recovered_y,
                                      tpe=recovered_block_type.name,
                                      device_uid=child_block.uid)
                changed = True
            elif recovered_block_type == BlockType.OUTPUT_CONN:
                recovered_x = 1020.0
                recovered_y = 100.0 + (100.0 * output_index)
                self.diagram.add_node(name=child_block.name,
                                      x=recovered_x,
                                      y=recovered_y,
                                      tpe=recovered_block_type.name,
                                      device_uid=child_block.uid)
                changed = True
            else:
                pass

            if recovered_block_type == BlockType.INPUT_CONN:
                input_index += 1
            elif recovered_block_type == BlockType.OUTPUT_CONN:
                output_index += 1
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

        expected_inputs_by_ref, expected_outputs_by_ref = self._build_expected_root_interface_for_current_mode()

        for child_block in self.main_block.children:
            interface_var = get_single_interface_var(child_block)

            if is_root_interface_wrapper_block(block_model=child_block,
                                               diagram=self.diagram):
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
        expected_inputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        expected_outputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        root_var: Var
        wrapper_block: Block

        expected_inputs_by_ref, expected_outputs_by_ref = self._build_expected_root_interface_for_current_mode()
        input_wrappers_by_ref, output_wrappers_by_ref = self._find_protected_wrapper_blocks_by_ref()
        preserved_non_wrapper_children: list[Block] = list()
        unresolved_wrapper_children: list[Block] = list()
        ordered_wrapper_children: list[Block] = list()
        child_block: Block
        seen_wrapper_ids: set[int] = set()
        reference: VarPowerFlowReferenceType
        root_var_candidate: Var

        for reference, root_var in expected_inputs_by_ref.items():
            for root_var_candidate in self.main_block.in_vars:
                if root_var_candidate.ref == reference:
                    root_var = root_var_candidate
                    break
                else:
                    pass

            if reference not in input_wrappers_by_ref and create_missing:
                wrapper_block = Block(name=root_var.name)
                wrapper_block.out_vars = list((root_var,))
                self.main_block.add(wrapper_block)
                self.diagram.add_node(name=wrapper_block.name,
                                      x=100.0,
                                      y=100.0 + (100.0 * len(input_wrappers_by_ref)),
                                      tpe=BlockType.INPUT_CONN.name,
                                      device_uid=wrapper_block.uid)
                input_wrappers_by_ref[reference] = wrapper_block
                changed = True
            else:
                pass

        for reference, root_var in expected_outputs_by_ref.items():
            for root_var_candidate in self.main_block.out_vars:
                if root_var_candidate.ref == reference:
                    root_var = root_var_candidate
                    break
                else:
                    pass

            if reference not in output_wrappers_by_ref and create_missing:
                wrapper_block = Block(name=root_var.name)
                wrapper_block.in_vars = list((root_var,))
                self.main_block.add(wrapper_block)
                self.diagram.add_node(name=wrapper_block.name,
                                      x=1020.0,
                                      y=100.0 + (100.0 * len(output_wrappers_by_ref)),
                                      tpe=BlockType.OUTPUT_CONN.name,
                                      device_uid=wrapper_block.uid)
                output_wrappers_by_ref[reference] = wrapper_block
                changed = True
            else:
                pass

        for child_block in self.main_block.children:
            if not is_root_interface_wrapper_block(block_model=child_block,
                                                   diagram=self.diagram):
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
            if not is_root_interface_wrapper_block(block_model=child_block,
                                                   diagram=self.diagram):
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

        expected_inputs_by_ref, expected_outputs_by_ref = self._build_expected_root_interface_for_current_mode()
        ordered_input_refs = build_expected_root_interface_ref_order(block_type=BlockType.INPUT_CONN,
                                                                     input_refs=expected_inputs_by_ref,
                                                                     output_refs=expected_outputs_by_ref)
        ordered_output_refs = build_expected_root_interface_ref_order(block_type=BlockType.OUTPUT_CONN,
                                                                      input_refs=expected_inputs_by_ref,
                                                                      output_refs=expected_outputs_by_ref)

        changed = self._ensure_root_interface_wrapper_blocks_exist(create_missing=True) or changed
        interface_input_wrappers, interface_output_wrappers = self._find_protected_wrapper_blocks_by_ref()

        for node_uid, node in self.diagram.node_data.items():
            if node.tpe in set((BlockType.INPUT_CONN.name, BlockType.OUTPUT_CONN.name,)):
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
                wrapper_block.out_vars = list((root_var,))
                self.main_block.add(wrapper_block)
                changed = True
            elif wrapper_block.uid != existing_input_node_uids.get(reference, wrapper_block.uid):
                changed = True
            else:
                pass

            wrapper_block.out_vars = list((root_var,))
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
                wrapper_block.in_vars = list((root_var,))
                self.main_block.add(wrapper_block)
                changed = True
            elif wrapper_block.uid != existing_output_node_uids.get(reference, wrapper_block.uid):
                changed = True
            else:
                pass

            wrapper_block.in_vars = list((root_var,))
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
                pass
            else:
                if node.tpe == BlockType.INPUT_CONN.name:
                    block_type = BlockType.INPUT_CONN
                elif node.tpe == BlockType.OUTPUT_CONN.name:
                    block_type = BlockType.OUTPUT_CONN
                else:
                    block_type = None

                if block_type is None:
                    pass
                else:
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
                        pass
                    else:
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
            if is_root_interface_wrapper_block(block_model=child_block,
                                               diagram=self.diagram):
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
                wrapper_block.out_vars = list((authoritative_input,))
                wrapper_block.in_vars = list()
                wrapper_block.set_name(authoritative_input.name)
            else:
                pass

        for reference in expected_outputs_by_ref.keys():
            wrapper_block = interface_output_wrappers.get(reference, None)
            current_output = self.main_block.external_mapping.get(reference, None)
            if wrapper_block is not None and current_output is not None:
                wrapper_block.in_vars = list((current_output,))
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
                    wrapper_block.out_vars = list((authoritative_input,))
                    self.main_block.add(wrapper_block)
                    interface_input_wrappers[reference] = wrapper_block
                else:
                    pass
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
                wrapper_block.out_vars = list((authoritative_input,))
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
                    wrapper_block.in_vars = list((new_output,))
                    self.main_block.add(wrapper_block)
                    interface_output_wrappers[reference] = wrapper_block
                else:
                    pass
                changed = True
            else:
                existing_output._network_conn = True
                self.main_block.external_mapping[reference] = existing_output
                wrapper_block = interface_output_wrappers.get(reference, None)
                if wrapper_block is not None:
                    wrapper_block.in_vars = list((existing_output,))
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
        shared_branch_refs: set[VarPowerFlowReferenceType] = set(list((VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.v_A, VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.v_C, VarPowerFlowReferenceType.i_N, VarPowerFlowReferenceType.i_A, VarPowerFlowReferenceType.i_B, VarPowerFlowReferenceType.i_C,)))
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
        layout_result: EngineResult
        block_positions: Dict[int, Tuple[float, float]]
        existing_materialized_uids: set[int]
        layout_offset_x: float = 0.0
        layout_offset_y: float = 0.0

        expected_inputs_by_ref, expected_outputs_by_ref = self._build_expected_root_interface_for_current_mode()

        for child_block in self.main_block.children:
            interface_var = get_single_interface_var(child_block)
            if is_root_interface_wrapper_block(block_model=child_block,
                                               diagram=self.diagram):
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
        items_list: list[DynamicBlockGraphicsItem] = self._collect_non_interface_scene_items()

        if len(items_list) > 0:
            self._rebuild_visible_symbolic_connections(items_list)
            if rebuild_interface_connections:
                self._rebuild_editor_interface_graphical_connections(items_list)
            else:
                pass
        else:
            pass

    def _collect_non_interface_scene_items(self) -> list[DynamicBlockGraphicsItem]:
        """
        Return the visible non-interface block items in the scene.

        The reconnect pass operates only on real model blocks. The protected
        editor interface wrappers are intentionally excluded from this list.

        Arithmetic and unary decomposition items must be included because ELK
        equation diagrams consist primarily of those specialized item types.

        :return: Block items excluding editor interface wrappers.
        """
        items_list: list[DynamicBlockGraphicsItem] = list()
        scene_item: QGraphicsItem
        node_data: BlockDiagramNode | None

        for scene_item in self.scene.items():
            if isinstance(scene_item, (
                    graph.BlockItem,
                    graph.GenericBlockItem,
                    graph.RoundBaseArithmeticOpItem,
                    graph.RectBaseArithmeticOpItem,
                    graph.PairedItem,
            )):
                if scene_item.subsys is not None:
                    node_data: BlockDiagramNode | None = self.diagram.node_data.get(scene_item.subsys.uid, None)
                else:
                    node_data = None

                if node_data is None:
                    pass
                elif node_data.tpe in set((BlockType.INPUT_CONN.name, BlockType.OUTPUT_CONN.name,)):
                    pass
                else:
                    items_list.append(scene_item)
            else:
                pass

        return items_list

    def _rebuild_visible_symbolic_connections(self, items_list: List[DynamicBlockGraphicsItem]) -> None:
        """
        Recreate missing symbolic wires between all visible non-interface blocks.

        The saved diagram may miss some graphical arrows even when the symbolic
        block graph still carries enough metadata to infer them. Re-run the
        visible block-pair connection discovery so the scene reflects the actual
        symbolic connectivity.

        :param items_list: Visible non-interface block items.
        :return: None.
        """
        item_source: DynamicBlockGraphicsItem
        item_target: DynamicBlockGraphicsItem
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

    def _rebuild_editor_interface_graphical_connections(self, items_list: List[DynamicBlockGraphicsItem]) -> None:
        """
        Recreate visible wires between editor interface blocks and visible model blocks.

        Device-level EMT interfaces retain their topology-aware reference
        translation. Nested RMS and atomic DAE editors additionally match ports
        by their stable structural key, allowing ordinary shared-reference and
        named signals to reconnect to their boundary wrappers after reopen.

        :param items_list: Visible non-interface block items.
        :return: None.
        """
        # In an RMS root editor, wires between the device connection variables
        # and a block dropped from the Library are exclusively user-authored.
        # Only nested editors may infer their own boundary-to-equation wiring.
        # Fresh complete root models are bootstrapped separately by their ELK
        # layout, so this guard does not remove template-defined connections.
        if self.is_root_editor and self.mode == DynamicSimulationMode.RMS:
            return
        else:
            pass

        interface_inputs_by_ref: Dict[VarPowerFlowReferenceType, graph.ProtectedConnectionBlockItem] = dict()
        interface_outputs_by_ref: Dict[VarPowerFlowReferenceType, graph.ProtectedConnectionBlockItem] = dict()
        interface_inputs_by_key: Dict[tuple[str, str], graph.ProtectedConnectionBlockItem] = dict()
        interface_outputs_by_key: Dict[tuple[str, str], graph.ProtectedConnectionBlockItem] = dict()
        scene_item: QGraphicsItem
        node_data: BlockDiagramNode | None
        reference_var: Var | None
        block_item: DynamicBlockGraphicsItem
        input_index: int
        output_index: int
        input_var: Var
        output_var: Var
        protected_item: graph.ProtectedConnectionBlockItem | None
        branch_input_refs: set[VarPowerFlowReferenceType] = set(list((VarPowerFlowReferenceType.vf_N, VarPowerFlowReferenceType.vf_A, VarPowerFlowReferenceType.vf_B, VarPowerFlowReferenceType.vf_C, VarPowerFlowReferenceType.Vf_dc, VarPowerFlowReferenceType.vt_N, VarPowerFlowReferenceType.vt_A, VarPowerFlowReferenceType.vt_B, VarPowerFlowReferenceType.vt_C, VarPowerFlowReferenceType.Vt_dc,)))
        branch_output_refs: set[VarPowerFlowReferenceType] = set(list((VarPowerFlowReferenceType.if_N, VarPowerFlowReferenceType.if_A, VarPowerFlowReferenceType.if_B, VarPowerFlowReferenceType.if_C, VarPowerFlowReferenceType.If_dc, VarPowerFlowReferenceType.it_N, VarPowerFlowReferenceType.it_A, VarPowerFlowReferenceType.it_B, VarPowerFlowReferenceType.it_C, VarPowerFlowReferenceType.It_dc,)))

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
                    if isinstance(reference_var, Var):
                        interface_inputs_by_key[get_structural_port_key(reference_var)] = scene_item
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
                    if isinstance(reference_var, Var):
                        interface_outputs_by_key[get_structural_port_key(reference_var)] = scene_item
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
                        if protected_item is None:
                            protected_item = interface_inputs_by_key.get(get_structural_port_key(input_var), None)
                        else:
                            pass
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
                        protected_item = interface_inputs_by_key.get(get_structural_port_key(input_var), None)
                        if protected_item is not None and len(protected_item.outputs) > 0 and input_index < len(
                                block_item.inputs):
                            if self._connection_exists_between_ports(protected_item.outputs[0],
                                                                    block_item.inputs[input_index]):
                                pass
                            else:
                                connection_item = graph.ConnectionItem(
                                    source_port=protected_item.outputs[0],
                                    target_port=block_item.inputs[input_index],
                                    diagram=self.diagram,
                                    editor=self,
                                )
                                self.attach_new_connection_item(connection_item)
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
                        if protected_item is None:
                            protected_item = interface_outputs_by_key.get(get_structural_port_key(output_var), None)
                        else:
                            pass
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
                        protected_item = interface_outputs_by_key.get(get_structural_port_key(output_var), None)
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
                if model_ref in list((VarPowerFlowReferenceType.vf_N, VarPowerFlowReferenceType.vf_A, VarPowerFlowReferenceType.vf_B, VarPowerFlowReferenceType.vf_C, VarPowerFlowReferenceType.Vf_dc,)):
                    ac_side_is_from = True
                elif model_ref in list((VarPowerFlowReferenceType.vt_N, VarPowerFlowReferenceType.vt_A, VarPowerFlowReferenceType.vt_B, VarPowerFlowReferenceType.vt_C, VarPowerFlowReferenceType.Vt_dc,)):
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
                if model_ref in list((VarPowerFlowReferenceType.if_N, VarPowerFlowReferenceType.if_A, VarPowerFlowReferenceType.if_B, VarPowerFlowReferenceType.if_C, VarPowerFlowReferenceType.If_dc,)):
                    ac_side_is_from = True
                elif model_ref in list((VarPowerFlowReferenceType.it_N, VarPowerFlowReferenceType.it_A, VarPowerFlowReferenceType.it_B, VarPowerFlowReferenceType.it_C, VarPowerFlowReferenceType.It_dc,)):
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
                                         item_source: DynamicBlockGraphicsItem,
                                         item_dest: DynamicBlockGraphicsItem,
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


    def _find_output_port_for_var(self,
                                  item_source: DynamicBlockGraphicsItem,
                                  source_var: Var) -> graph.PortItem | None:
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

    def _find_input_port_for_var(self,
                                 item_dest: DynamicBlockGraphicsItem,
                                 target_var: Var) -> graph.PortItem | None:
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

    def _connection_exists_between_ports(
            self,
            source_port: graph.PortItem | graph.BranchingItem,
            target_port: graph.PortItem | graph.BranchingItem,
    ) -> bool:
        """Return whether one visible connection already joins two ports.

        :param source_port: Candidate source port.
        :param target_port: Candidate target port.
        :return: ``True`` when the connection is already present.
        """
        connection: graph.ConnectionItem

        if source_port.connections is None:
            return False
        else:
            pass

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
            if is_root_interface_wrapper_block(block_model=child_block,
                                               diagram=self.diagram):
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

    def add_api_obj_mapping(self) -> None:

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

            self.main_block.api_obj_mapping = dict(((ParamPowerFlowReferenceType.g, g), (ParamPowerFlowReferenceType.b, b), (ParamPowerFlowReferenceType.bsh, bsh),))
        else:
            pass

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
                pass
            else:
                for deletable_item in deletable_items:
                    self.remove_block_item(deletable_item)

                self.scene.clearSelection()
                self.mark_unapplied_changes()
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

        for root_var in self.root_block.in_vars:
            if root_var.non_mutable_uid == var.non_mutable_uid:
                root_var.set_name(new_name)
            else:
                pass

        for root_var in self.root_block.out_vars:
            if root_var.non_mutable_uid == var.non_mutable_uid:
                root_var.set_name(new_name)
            else:
                pass

        mapped_var: Var | None
        for mapped_var in self.root_block.external_mapping.values():
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
        source_non_mutable_uid: int = self.var_factory.get_connection_source_non_mutable_uid(
            variable_non_mutable_uid=var.non_mutable_uid,
        )
        component_non_mutable_uids: set[int] = self._get_alias_component_stable_uids(
            starting_non_mutable_uids=set(list((source_non_mutable_uid,))),
        )
        vars_by_uid: Dict[int, List[Var]] = build_working_var_index(self.root_block)
        current_non_mutable_uid: int
        current_vars: List[Var]
        current_var: Var

        # Inspect every declaration instead of a name-keyed dictionary, since
        # such a dictionary hides all but the last pre-existing duplicate.
        for current_non_mutable_uid, current_vars in vars_by_uid.items():
            for current_var in current_vars:
                if (current_var.name == candidate_name
                        and current_non_mutable_uid not in component_non_mutable_uids):
                    return True
                else:
                    pass

        return False

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
        expected_inputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        expected_outputs_by_ref: dict[VarPowerFlowReferenceType, Var]
        expected_by_ref: dict[VarPowerFlowReferenceType, Var]
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

        expected_inputs_by_ref, expected_outputs_by_ref = self._build_expected_root_interface_for_current_mode()
        if block_type == BlockType.INPUT_CONN:
            expected_by_ref = expected_inputs_by_ref
        else:
            expected_by_ref = expected_outputs_by_ref

        reference_var = None
        if semantic_reference is not None:
            for root_var_candidate in root_vars:
                if root_var_candidate.ref == semantic_reference:
                    reference_var = root_var_candidate
                    break
                else:
                    pass

            if reference_var is None:
                reference_var = expected_by_ref.get(semantic_reference, None)
            else:
                pass
        else:
            pass

        available_root_refs.update(expected_by_ref.keys())

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

        if wrapper_uid is not None:
            wrapper_block.uid = wrapper_uid
        else:
            pass

        # The oval is a direct view over the authoritative root variable, not an
        # independent symbolic variable container.
        if reference_var is not None:
            if block_type == BlockType.INPUT_CONN:
                wrapper_block.in_vars = list()
                wrapper_block.out_vars = list((reference_var,))
            else:
                wrapper_block.in_vars = list((reference_var,))
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

        expected_inputs_by_ref, expected_outputs_by_ref = self._build_expected_root_interface_for_current_mode()
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

        # Persist the same label in the diagram node. Scene rebuilding uses the
        # block object, while validation and serialization also read node.name.
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

        self.refresh_editor_block_name_displays(block)
        self.mark_unapplied_changes()


    def _apply_variable_rename(
            self,
            var: Var,
            new_name: str,
            renamed_item: graph.ProtectedConnectionBlockItem | None,
    ) -> bool:
        """
        Validate and apply one variable rename to its complete alias component.

        :param var: Variable selected from the scene or variables table.
        :param new_name: Candidate symbolic name.
        :param renamed_item: Optional root-interface wrapper edited on the scene.
        :return: ``True`` when the rename was applied.
        """
        candidate_name: str = new_name.strip()
        source_non_mutable_uid: int
        canonical_var: Var | None
        source_working_vars: List[Var] | None
        vars_by_uid: Dict[int, List[Var]]
        block: Block | None
        node: BlockDiagramNode | None
        candidate_node: BlockDiagramNode

        if len(candidate_name) == 0:
            self.toast_manager.show_warning_toast(self.tr("Variable name cannot be empty"))
            return False
        elif not dialog_models.is_valid_symbol_name(candidate_name):
            self.toast_manager.show_warning_toast(self.tr("Variable name is invalid"))
            return False
        elif self._namespace_has_conflicting_variable_name(var, candidate_name):
            self.toast_manager.show_warning_toast(self.tr("Variable name already exists"))
            return False
        else:
            pass

        # Resolve the upstream connection owner even when the edit originated
        # from a downstream variable displayed inside a nested block editor.
        source_non_mutable_uid = self.var_factory.get_connection_source_non_mutable_uid(
            variable_non_mutable_uid=var.non_mutable_uid,
        )
        canonical_var = self.var_factory.get_vars_dict().get(source_non_mutable_uid, None)
        if canonical_var is None:
            canonical_var = self.var_factory.get_diff_var_dict().get(source_non_mutable_uid, None)
        else:
            pass

        if canonical_var is None:
            vars_by_uid = build_working_var_index(self.root_block)
            source_working_vars = vars_by_uid.get(source_non_mutable_uid, None)
            if source_working_vars is not None and len(source_working_vars) > 0:
                canonical_var = source_working_vars[0]
            else:
                canonical_var = var
        else:
            pass

        if canonical_var.name == candidate_name:
            return False
        else:
            pass

        # Reuse the established alias replay so rename, connect, disconnect and
        # signal-pair propagation continue sharing one graph implementation.
        self._propagate_alias_to_working_tree(
            source_non_mutable_uid=source_non_mutable_uid,
            incoming_uid=canonical_var.uid,
            incoming_name=candidate_name,
        )
        canonical_var.set_name(candidate_name)
        self._synchronize_root_connection_var_name(var=canonical_var,
                                                   new_name=candidate_name)

        block = renamed_item.subsys if renamed_item is not None else None
        if block is not None:
            block.set_name(candidate_name)
            node = self.diagram.node_data.get(block.uid, None)
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
                node.name = candidate_name
            else:
                pass
        else:
            pass

        component_non_mutable_uids: set[int] = self._get_alias_component_stable_uids(
            starting_non_mutable_uids=set(list((source_non_mutable_uid,))),
        )
        self._refresh_alias_component_displays(
            component_non_mutable_uids=component_non_mutable_uids,
        )
        self.refresh_editor_variable_displays(canonical_var, renamed_item=renamed_item)
        self.mark_unapplied_changes()
        return True

    @QtCore.Slot(object)
    def on_variable_rename_requested(self, request: BlockVariableRenameRequest) -> None:
        """Run the established complete rename for a Block Properties request.

        :param request: Synchronous request containing the selected variable.
        :return: None.
        """
        if not isinstance(request, BlockVariableRenameRequest):
            return
        else:
            variable: Var = request.get_variable()

        accepted: bool
        new_name: str
        accepted, new_name = self.open_variable_rename_dialog(variable.name)
        if accepted:
            renamed: bool = self._apply_variable_rename(
                var=variable,
                new_name=new_name,
                renamed_item=None,
            )
            request.set_result(success=renamed, new_name=variable.name)
        else:
            request.set_result(success=False, new_name=variable.name)


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

        self._apply_variable_rename(var=var,
                                    new_name=new_name,
                                    renamed_item=item)

    def get_scene_item_by_block_uid(self,
                                    block_uid: int) -> DynamicBlockGraphicsItem | None:
        """
        Find the visible scene item representing a block uid.

        :param block_uid: Symbolic block UID represented in the current scene.
        :return: Matching graphics item or ``None``.
        """
        item: QGraphicsItem

        for item in self.scene.items():
            if isinstance(item, (graph.BlockItem, graph.GenericBlockItem, graph.RoundBaseArithmeticOpItem,
                                 graph.RectBaseArithmeticOpItem, graph.UnOpItem,
                                 graph.PairedItem)) and item.subsys is not None:
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

    @QtCore.Slot(object)
    def on_structural_rebuild_requested(self, request: BlockStructuralEditRequest) -> None:
        """Rebuild one generated block and migrate surviving connected ports.

        :param request: Synchronous request emitted by the properties dialogue.
        :return: None.
        """
        if not isinstance(request, BlockStructuralEditRequest):
            return
        else:
            target_block: Block = request.get_block()
            builder: TemplateDefinition = request.get_builder()

        # Evaluate the complete candidate against an isolated factory first.
        # This prevents invalid structural settings from leaking orphaned Vars
        # into the live editor factory, which has no transactional rollback.
        preflight_builder: TemplateDefinition | None = create_structural_template_builder(
            var_factory=VarFactory(),
            block_type=request.get_block_type(),
            item_name=target_block.name,
            api_object=self.api_object,
        )
        if preflight_builder is None:
            request.set_result(False, "This block type has no structural rebuild adapter.")
            return
        else:
            copy_template_builder_values(builder, preflight_builder)
        try:
            preflight_template: Block | EmtModelTemplate | RmsModelTemplate = preflight_builder.eval()
            if isinstance(preflight_template, Block):
                _preflight_block: Block = preflight_template
            elif isinstance(preflight_template, EmtModelTemplate):
                _preflight_block = preflight_template.block
            elif isinstance(preflight_template, RmsModelTemplate):
                _preflight_block = preflight_template.block
            else:
                request.set_result(False, "The selected builder did not return a symbolic block.")
                return
        except (ArithmeticError, IndexError, KeyError, TypeError, ValueError) as error:
            request.set_result(False, str(error))
            return

        try:
            template: Block | EmtModelTemplate | RmsModelTemplate = builder.eval()
            if isinstance(template, Block):
                candidate_block: Block = template
            elif isinstance(template, EmtModelTemplate):
                candidate_block = template.block
            elif isinstance(template, RmsModelTemplate):
                candidate_block = template.block
            else:
                request.set_result(False, "The selected builder did not return a symbolic block.")
                return
        except (ArithmeticError, IndexError, KeyError, TypeError, ValueError) as error:
            request.set_result(False, str(error))
            return

        candidate_block.name = target_block.name
        old_inputs: List[Var] = list(target_block.in_vars)
        old_outputs: List[Var] = list(target_block.out_vars)
        new_input_indexes: Dict[tuple[str, str], int] = build_port_index_by_key(candidate_block.in_vars)
        new_output_indexes: Dict[tuple[str, str], int] = build_port_index_by_key(candidate_block.out_vars)
        old_input_by_key: Dict[tuple[str, str], Var] = dict(
            (get_structural_port_key(variable), variable) for variable in old_inputs
        )
        old_output_by_key: Dict[tuple[str, str], Var] = dict(
            (get_structural_port_key(variable), variable) for variable in old_outputs
        )

        # Preserve the exact Var objects for every semantic port that survives.
        replacements: Dict[Var, Var] = dict()
        candidate_var: Var
        for candidate_var in candidate_block.in_vars:
            surviving_input: Var | None = old_input_by_key.get(get_structural_port_key(candidate_var), None)
            if surviving_input is not None:
                replacements[candidate_var] = surviving_input
            else:
                pass
        for candidate_var in candidate_block.out_vars:
            surviving_output: Var | None = old_output_by_key.get(get_structural_port_key(candidate_var), None)
            if surviving_output is not None:
                replacements[candidate_var] = surviving_output
            else:
                pass

        # Migrate diagram port indexes by semantics and explicitly disconnect
        # wires whose phase or generated port no longer exists.
        connection_uids_to_remove: List[int] = list()
        connection_uid: int
        connection: BlockDiagramConnection
        for connection_uid, connection in list(self.diagram.con_data.items()):
            keep_connection: bool = True
            if connection.to_uid == target_block.uid:
                if 0 <= connection.port_number_to < len(old_inputs):
                    input_key: tuple[str, str] = get_structural_port_key(old_inputs[connection.port_number_to])
                    new_input_index: int | None = new_input_indexes.get(input_key, None)
                    if new_input_index is not None:
                        connection.port_number_to = new_input_index
                    else:
                        keep_connection = False
                else:
                    keep_connection = False
            else:
                pass
            if connection.from_uid == target_block.uid and keep_connection:
                if 0 <= connection.port_number_from < len(old_outputs):
                    output_key: tuple[str, str] = get_structural_port_key(old_outputs[connection.port_number_from])
                    new_output_index: int | None = new_output_indexes.get(output_key, None)
                    if new_output_index is not None:
                        connection.port_number_from = new_output_index
                    else:
                        keep_connection = False
                else:
                    keep_connection = False
            else:
                pass
            if not keep_connection:
                connection_uids_to_remove.append(connection_uid)
            else:
                pass

        scene_item: QtWidgets.QGraphicsItem
        connection_item_by_uid: Dict[int, graph.ConnectionItem] = dict()
        for scene_item in self.scene.items():
            if isinstance(scene_item, graph.ConnectionItem):
                connection_item_by_uid[scene_item.con_uid] = scene_item
            else:
                pass
        for connection_uid in connection_uids_to_remove:
            connection_item: graph.ConnectionItem | None = connection_item_by_uid.get(connection_uid, None)
            if connection_item is not None:
                self.remove_connection_item(connection_item)
            elif connection_uid in self.diagram.con_data:
                del self.diagram.con_data[connection_uid]
            else:
                pass

        if len(replacements) > 0:
            candidate_block.update_model_bulk(replacements)
            replace_generated_block_auxiliary_variables(candidate_block, replacements)
        else:
            pass
        apply_generated_parameter_values(candidate_block, request.get_parameter_values())
        apply_generated_block_state(candidate_block, target_block)
        request.set_result(True, "")

    @QtCore.Slot(object)
    def on_output_export_changes_requested(self, changes: object) -> None:
        """Disconnect wires before existing output ports are removed.

        The properties dialogue emits this request synchronously, immediately
        before it edits ``Block.out_vars``. Removing the graphical connection at
        this point also unregisters the corresponding VarFactory edge and avoids
        an invisible persisted connection after the scene rebuild.

        :param changes: Staged ``(owner, variable, exported)`` change tuples.
        :return: None.
        """
        if isinstance(changes, list):
            change: object
            for change in changes:
                if isinstance(change, tuple) and len(change) == 3:
                    owner: object = change[0]
                    variable: object = change[1]
                    exported: object = change[2]
                    if isinstance(owner, Block) and isinstance(variable, Var) and isinstance(exported, bool):
                        if exported:
                            pass
                        else:
                            scene_item: DynamicBlockGraphicsItem | None = self.get_scene_item_by_block_uid(owner.uid)
                            if scene_item is not None:
                                output_port: graph.PortItem
                                for output_port in scene_item.outputs:
                                    port_variable: Var | None = output_port.base_var
                                    if port_variable is not None and \
                                            port_variable.non_mutable_uid == variable.non_mutable_uid:
                                        connection_items: List[graph.ConnectionItem] = list()
                                        if output_port.connections is not None:
                                            connection_item: graph.ConnectionItem
                                            for connection_item in output_port.connections:
                                                connection_items.append(connection_item)
                                        else:
                                            pass
                                        for connection_item in connection_items:
                                            self.remove_connection_item(connection_item)
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

    @QtCore.Slot(object)
    def on_block_properties_applied(self, block_uid: int) -> None:
        """
        Mark a validated modal edit as dirty without rebuilding unchanged graphics.

        :param block_uid: Identity of the block changed by the modal dialogue.
        :return: None.
        """
        self.mark_unapplied_changes()
        # Applying can add ports even when the equations alone changed. Rebuild
        # from the same diagram/model identities so the visible item reflects
        # its current input/output contract immediately.
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
                # Individual VSC Library blocks keep their original ports.
                # Bind only their initialization expressions before committing,
                # including when their equations were decomposed for display.
                synchronize_vsc_library_initialization(
                    root=self._document.working_root_block,
                    block_types=self._block2blocktype,
                )
                self._document.commit()
            else:
                pass
            # Complete RMS templates dropped from the Library are children of
            # the editor-owned root. Synchronize their device and power-flow
            # mappings before RMS initialization reads the root contract.
            synchronize_saved_rms_root_mappings_from_children(device=self.api_object)
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
            synchronize_saved_emt_root_parameters_from_children(device=self.api_object)

            # The previous saved EMT model may already have bus-propagation edges
            # registered in the shared var-factory graph. Remove those stale
            # edges before registering the freshly committed model vars so the
            # next attach step does not accumulate old and new symbolic links.
            unregister_saved_emt_model_var_connections_for_device(device=self.api_object,
                                                                   var_factory=self.var_factory)

            # The committed editor block is a fresh symbolic clone. Register its
            # vars in the shared factory before reconnecting so bus-side uid
            # propagation and EmtProblemDae external-mapping recovery see the
            # same authoritative objects as the scripting/template path.
            register_saved_emt_model_vars_for_device(device=self.api_object,
                                                      var_factory=self.var_factory)

            dialog_models.initialize_connected_bus_models_for_editor_assignment(api_object=self.api_object,
                                                                                circuit=self.circuit,
                                                                                var_factory=self.var_factory,
                                                                                mode=self.mode)
            attach_emt_model_to_buses(device=self.api_object,
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
        else:
            pass

    def open_inspect_dialog(self) -> None:
        """
        Create and open the read-only model inspection dialog.

        :return: None.
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
        con: BlockDiagramConnection
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
        node: BlockDiagramNode

        for node_uid, node in self.diagram.node_data.items():
            # Each diagram node is validated against the saved symbolic interface
            # so the report reflects exactly what the user wired in the editor.
            block: Block | None = self.get_block_from_main_block(node.device_uid)
            if block is None:
                pass
            else:
                missing_port_messages: list[str] = list()
                emt_missing_by_phase: dict[str, list[str]] = dict((("N", list()), ("A", list()), ("B", list()), ("C", list()),))
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
                    phase_total_ports_by_name: dict[str, int] = dict((("N", 0), ("A", 0), ("B", 0), ("C", 0),))
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
        node_data: BlockDiagramNode | None
        input_var: Var
        output_var: Var

        for child_block in self.main_block.children:
            node_data = self.diagram.node_data.get(child_block.uid, None)
            is_root_wrapper: bool = (
                node_data is not None
                and node_data.tpe in set((BlockType.INPUT_CONN.name, BlockType.OUTPUT_CONN.name,))
            )
            if child_block.uid != excluded_block.uid and not is_root_wrapper:
                for input_var in child_block.in_vars:
                    if valid.get_var_reference(var=input_var) in input_refs:
                        return child_block
                    else:
                        pass

                for output_var in child_block.out_vars:
                    if valid.get_var_reference(var=output_var) in output_refs:
                        return child_block
                    else:
                        pass
            else:
                pass

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

        sections: list[valid.ValidationSection] = list((equation_section, duplicate_section, parameter_section, init_section, port_section,))

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
        scene_item: QGraphicsItem

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
                node_data: BlockDiagramNode | None = self.diagram.node_data.get(scene_block_item.subsys.uid, None)
            else:
                node_data = None

            if node_data is not None and node_data.name == block_label:
                return scene_block_item
            else:
                pass

            formatted_label = valid.format_validation_block_label(scene_block_item.subsys)
            if formatted_label == block_label:
                return scene_block_item
            elif scene_block_item.subsys.name == block_label:
                return scene_block_item
            elif scene_block_item.name == block_label:
                return scene_block_item
            elif scene_block_item.name_item is not None and scene_block_item.name_item.toPlainText() == block_label:
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
                            else:
                                pass
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
            else:
                pass

            reference_var_ref = valid.get_var_reference(var=reference_var)
            if reference_var_ref not in candidate_refs:
                return False
            else:
                pass

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
                pass
            else:
                port_reference = valid.get_var_reference(var=port_item.base_var)
                if port_reference in port_refs:
                    port_item.set_validation_highlighted(True)
                    highlighted_any_port = True
                else:
                    pass

        for port_item in scene_block_item.outputs:
            if port_item.base_var is None:
                pass
            else:
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
            if section.get_title() == "Port Connectivity":
                for row in section.get_rows():
                    port_refs.update(row.get_highlight_port_refs())
                    port_names.update(row.get_highlight_port_names())
            else:
                pass

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
        :param parent: Owning Qt widget.
        :return: Whether this editor can be closed without losing unapplied changes silently.
        """

        if not self.has_unapplied_changes:
            return True
        else:
            pass

        reply = QtWidgets.QMessageBox.question(
            parent if parent is not None else self,
            "Unsaved changes",
            "There are unapplied changes. Do you want to close without applying them?",
            QtWidgets.QMessageBox.StandardButton.Yes,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        return reply == QtWidgets.QMessageBox.StandardButton.Yes

    def _dispose_table_models(self) -> None:
        """
        Detach the table/tree models owned by the editor.

        The editor owns several view-proxy-source chains. Clearing the models
        from the views first shortens the QObject ownership graph before the
        editor widget itself is queued for deletion.

        :return: None.
        """
        _clear_table_view_model(self.ui.libraryTreeView)

        _dispose_qobject(self.library_proxy_model)
        self.library_proxy_model = None

        _dispose_qobject(self.library_find_shortcut)
        self.library_find_shortcut = None

        _dispose_dynamic_editor_library(self.library)
        self.library = None

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
            _dispose_qobject(view)
            self.ui.graphicsView = None
            self.view = None
        else:
            pass

        _dispose_qobject(scene)
        self.scene = None

    def _dispose_block_properties_dock(self) -> None:
        """Destroy the active block-properties dock before editor teardown.

        :return: None.
        """
        normalize_timer: QtCore.QTimer | None = self._properties_dock_normalize_timer
        if normalize_timer is not None:
            normalize_timer.stop()
            try:
                normalize_timer.timeout.disconnect(
                    self.normalize_block_properties_right_dock
                )
            except (RuntimeError, TypeError):
                pass
            normalize_timer.deleteLater()
            self._properties_dock_normalize_timer = None
        else:
            pass

        properties_dialogue: DynamicBlockPropertiesDialog | None = self._block_properties_dialogue
        if properties_dialogue is not None:
            # The dialogue can outlive its editor until DeferredDelete is
            # processed. Disconnect every Python receiver first so no queued
            # properties signal can call into the dismantled editor.
            try:
                properties_dialogue.blockApplied.disconnect(
                    self.on_block_properties_applied
                )
            except (RuntimeError, TypeError):
                pass
            try:
                properties_dialogue.structuralRebuildRequested.disconnect(
                    self.on_structural_rebuild_requested
                )
            except (RuntimeError, TypeError):
                pass
            try:
                properties_dialogue.variableRenameRequested.disconnect(
                    self.on_variable_rename_requested
                )
            except (RuntimeError, TypeError):
                pass
            try:
                properties_dialogue.outputExportChangesRequested.disconnect(
                    self.on_output_export_changes_requested
                )
            except (RuntimeError, TypeError):
                pass
        else:
            pass

        properties_dock: DynamicBlockPropertiesDockWidget | None = self._block_properties_dock
        if properties_dock is not None:
            try:
                properties_dock.closed.disconnect(
                    self.on_block_properties_dock_closed
                )
            except (RuntimeError, TypeError):
                pass
            try:
                properties_dock.dockLocationChanged.disconnect(
                    self.on_block_properties_dock_location_changed
                )
            except (RuntimeError, TypeError):
                pass
            try:
                properties_dock.topLevelChanged.disconnect(
                    self.on_block_properties_dock_top_level_changed
                )
            except (RuntimeError, TypeError):
                pass
            properties_dock.prepare_to_delete()
            self.removeDockWidget(properties_dock)
            properties_dock.setParent(None)
            properties_dock.deleteLater()
            self._block_properties_dock = None
            self._block_properties_dialogue = None
        else:
            pass

    def _dispose_library_dock(self) -> None:
        """Detach and delete the fixed Library dock after its models are gone.

        :return: None.
        """
        library_dock: QtWidgets.QDockWidget | None = self._library_dock
        if library_dock is not None:
            library_content: QtWidgets.QWidget | None = library_dock.widget()
            library_dock.setWidget(None)
            if library_content is not None:
                library_content.setParent(None)
                _dispose_qobject(library_content)
            else:
                pass
            self.removeDockWidget(library_dock)
            library_dock.setParent(None)
            _dispose_qobject(library_dock)
            self._library_dock = None
        else:
            pass

    def prepare_to_delete(self) -> None:
        """
        Release editor-owned Qt objects before deleting this editor widget.

        :return: None.
        """
        if self._prepared_to_delete:
            return
        else:
            pass

        self._prepared_to_delete = True
        # Close modeless property tooling before any of the model or scene
        # objects referenced by its signals are dismantled.
        self._dispose_block_properties_dock()

        # Tear down the library model before its dock starts disappearing.
        self._dispose_table_models()

        # Finally dismantle the graphics subtree. This is the highest-risk part
        # because it owns many binary Qt graphics objects behind Python wrappers.
        self._dispose_graphics_objects()

        # The Library dock owns the old right-side frame and can be deleted only
        # after its proxy/source model chain is gone.
        self._dispose_library_dock()

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
        else:
            pass

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

    def set_dark_mode(self) -> None:
        """
        Apply the dark graphics palette to every visible item.

        :return: None.
        """
        self.current_theme = DynEditorGraphicsModes.DARK
        self.set_colors_palet()
        for item in self.scene.items():
            if isinstance(item, (graph.GenericBlockItem, graph.PairedItem, graph.ConnectionItem, graph.RectBaseArithmeticOpItem,
                                 graph.RoundBaseArithmeticOpItem, graph.PortItem, graph.ElbowItem, graph.ResizeHandle, graph.BlockItem)):
                item.recolour()
            else:
                pass

    def set_light_mode(self) -> None:
        """
        Apply the light graphics palette to every visible item.

        :return: None.
        """
        self.current_theme = DynEditorGraphicsModes.LIGHT
        self.set_colors_palet()
        for item in self.scene.items():
            if isinstance(item, (graph.GenericBlockItem, graph.PairedItem, graph.ConnectionItem, graph.RectBaseArithmeticOpItem,
                                 graph.RoundBaseArithmeticOpItem, graph.PortItem, graph.ElbowItem, graph.ResizeHandle, graph.BlockItem)):
                item.recolour()
            else:
                pass
