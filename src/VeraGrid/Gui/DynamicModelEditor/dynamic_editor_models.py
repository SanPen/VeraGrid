from __future__ import annotations

import copy
import re
from collections.abc import Mapping

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.bus_emt_template import BusEmtTemplate, get_bus_emt_algebraic_vars
from VeraGridEngine.Utils.Symbolic.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.Symbolic.templates_common_functions import (
    emt_bus_shell_matches_grid_topology,
    reconcile_saved_emt_model_against_current_topology,
    synchronize_emt_bus_shell_with_grid,
)
from VeraGridEngine.enumerations import DynamicSimulationMode


class InspectModel(QWidget):
    """Read-only recursive summary of one symbolic block tree."""

    __slots__ = ("block", "list_vars", "table_params", "list_eqns")

    def __init__(self, block: Block, parent: QWidget | None = None) -> None:
        """Create the variables, parameters, and equations inspector.

        :param block: Root block to inspect recursively.
        :param parent: Optional Qt parent widget.
        :return: None.
        """
        super().__init__(parent)

        self.block: Block = block

        main_layout: QHBoxLayout = QHBoxLayout(self)
        self.setLayout(main_layout)

        left_panel: QVBoxLayout = QVBoxLayout()
        main_layout.addLayout(left_panel)

        var_header_layout: QHBoxLayout = QHBoxLayout()
        var_label: QLabel = QLabel("Variables")
        var_header_layout.addWidget(var_label)
        left_panel.addLayout(var_header_layout)

        self.list_vars: QListWidget = QListWidget()
        left_panel.addWidget(self.list_vars)

        param_header_layout: QHBoxLayout = QHBoxLayout()
        param_label: QLabel = QLabel("Parameters")
        param_header_layout.addWidget(param_label)
        left_panel.addLayout(param_header_layout)

        self.table_params: QTableWidget = QTableWidget()
        self.table_params.setColumnCount(2)
        self.table_params.setHorizontalHeaderLabels(list(("Name", "Value")))
        self.table_params.horizontalHeader().setStretchLastSection(True)
        self.table_params.verticalHeader().setVisible(False)
        self.table_params.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        left_panel.addWidget(self.table_params)

        right_panel: QVBoxLayout = QVBoxLayout()
        main_layout.addLayout(right_panel)

        eqn_header_layout: QHBoxLayout = QHBoxLayout()
        eqn_label: QLabel = QLabel("Equations")
        eqn_header_layout.addWidget(eqn_label)
        right_panel.addLayout(eqn_header_layout)

        self.list_eqns: QListWidget = QListWidget()
        right_panel.addWidget(self.list_eqns)

        self.refresh_lists(model=self.block, clear=True)

    def refresh_lists(self, model: Block | None = None, clear: bool = True) -> None:
        """Refresh the recursive read-only summary.

        :param model: Block subtree to append; defaults to the inspector root.
        :param clear: Whether existing rows must be cleared first.
        :return: None.
        """
        current_model: Block = self.block if model is None else model

        if clear:
            self.list_vars.clear()
            self.table_params.setRowCount(0)
            self.list_eqns.clear()
        else:
            pass

        variable_groups: tuple[list[Var], ...] = (
            current_model.state_vars,
            current_model.algebraic_vars,
        )
        variable_group: list[Var]
        var: Var
        for variable_group in variable_groups:
            for var in variable_group:
                self.list_vars.addItem(QListWidgetItem(f"{var.name} "))

        parameter_groups: tuple[Mapping[Var, Const | Expr], ...] = (
            current_model.parameters,
            current_model.event_dict,
        )
        parameter_group: Mapping[Var, Const | Expr]
        parameter: Var
        value: Const | Expr
        row: int
        for parameter_group in parameter_groups:
            for parameter, value in parameter_group.items():
                row = self.table_params.rowCount()
                self.table_params.insertRow(row)
                self.table_params.setItem(row, 0, QTableWidgetItem(parameter.name))
                self.table_params.setItem(row, 1, QTableWidgetItem(str(value)))

        equation_groups: tuple[tuple[str, list[Expr]], ...] = (
            ("state", current_model.state_eqs),
            ("algebraic", current_model.algebraic_eqs),
        )
        equation_group: tuple[str, list[Expr]]
        equation_type: str
        equations: list[Expr]
        equation: Expr
        for equation_group in equation_groups:
            equation_type, equations = equation_group
            for equation in equations:
                self.list_eqns.addItem(QListWidgetItem(f"{equation} ({equation_type})"))

        child: Block
        for child in current_model.children:
            self.refresh_lists(model=child, clear=False)


def clone_block_for_editing(block: Block) -> Block:
    """Create an isolated working copy of one symbolic block.

    :param block: Source block owned by the device or template.
    :return: Deep working copy used by one editor document.
    """
    return copy.deepcopy(block)


def copy_block_state(source_block: Block, target_block: Block) -> None:
    """Replace all persistent target-block state with an isolated source copy.

    :param source_block: Working block whose complete state must be committed.
    :param target_block: Existing owned block whose identity object is retained.
    :return: None.
    """
    source_clone: Block = clone_block_for_editing(source_block)

    # Copy every persistent symbolic collection so Apply changes cannot retain
    # stale equations, mappings, or procedural data from the previous model.
    target_block.name = source_clone.name
    target_block.uid = source_clone.uid
    target_block.is_decomposable = source_clone.is_decomposable
    target_block.tpe_uid = source_clone.tpe_uid
    target_block.vars_glob_name2uid = source_clone.vars_glob_name2uid
    target_block.state_vars = source_clone.state_vars
    target_block.state_eqs = source_clone.state_eqs
    target_block.algebraic_vars = source_clone.algebraic_vars
    target_block.algebraic_eqs = source_clone.algebraic_eqs
    target_block.inequalities = source_clone.inequalities
    target_block.diff_vars = source_clone.diff_vars
    target_block.reformulated_vars = source_clone.reformulated_vars
    target_block.differential_eqs = source_clone.differential_eqs
    target_block.init_eqs = source_clone.init_eqs
    target_block.diff_init_eqs = source_clone.diff_init_eqs
    target_block.children = source_clone.children
    target_block.in_vars = source_clone.in_vars
    target_block.out_vars = source_clone.out_vars
    target_block.parameters = source_clone.parameters
    target_block.discrete_eqs = source_clone.discrete_eqs
    target_block.external_mapping = source_clone.external_mapping
    target_block.api_obj_mapping = source_clone.api_obj_mapping
    target_block.init_values = source_clone.init_values
    target_block.var_mapping = source_clone.var_mapping
    target_block.event_dict = source_clone.event_dict
    target_block.mode_dict = source_clone.mode_dict
    target_block.boolean_guards = source_clone.boolean_guards
    target_block.procedural_logic = source_clone.procedural_logic
    target_block.connection_intents = source_clone.connection_intents
    target_block.diagram = source_clone.diagram


def _ensure_block_tree_names(block: Block, prefix: str = "block") -> None:
    """Assign deterministic display names to unnamed blocks recursively.

    :param block: Block subtree to normalize.
    :param prefix: Prefix used when the current block has no name.
    :return: None.
    """
    if len(block.name) == 0:
        block.name = f"{prefix}_{str(block.uid)[:8]}"
    else:
        pass

    child_index: int
    child_block: Block
    for child_index, child_block in enumerate(block.children, start=1):
        _ensure_block_tree_names(child_block, prefix=f"{block.name}_{child_index}")


def block_requires_editor_connection_bootstrap(block: Block) -> bool:
    """Return whether a leaf block needs its root interface bootstrapped.

    :param block: Editor root block.
    :return: Whether the editor must create initial connection variables.
    """
    has_diagram_nodes: bool = bool(block.diagram.node_data)
    has_children: bool = bool(block.children)
    has_root_inputs: bool = bool(block.in_vars)
    has_root_outputs: bool = bool(block.out_vars)

    if has_diagram_nodes:
        return False
    elif has_children:
        return False
    elif not has_root_inputs and not has_root_outputs:
        return True
    else:
        return False


def _initialize_editor_assigned_rms_bus_model(bus: Bus, var_factory: VarFactory) -> None:
    """Create a missing RMS bus shell used by an editor-assigned model.

    :param bus: Connected network bus.
    :param var_factory: Shared symbolic variable factory.
    :return: None.
    """
    if bus.rms_model.empty():
        initialize_bus_rms(bus=bus, vf=var_factory)
    else:
        pass


def _initialize_editor_assigned_emt_bus_model(bus: Bus,
                                              api_object: ALL_DEV_TYPES,
                                              circuit: MultiCircuit | None,
                                              var_factory: VarFactory) -> None:
    """Create or reconcile one EMT bus shell before editor attachment.

    :param bus: Connected network bus.
    :param api_object: Device whose model is being assigned.
    :param circuit: Optional grid used to infer the active topology.
    :param var_factory: Shared symbolic variable factory.
    :return: None.
    """
    if circuit is not None:
        branch_shell_requires_check: bool = (
            isinstance(api_object, BranchParent)
            and not bus.emt_model.empty()
            and not bus.is_emt_model_grid_synchronized()
        )
        if branch_shell_requires_check:
            try:
                get_bus_emt_algebraic_vars(bus.emt_model)
            except (AttributeError, TypeError, ValueError):
                synchronize_emt_bus_shell_with_grid(bus=bus,
                                                    grid=circuit,
                                                    var_factory=var_factory,
                                                    device_to_skip=api_object)
            else:
                if emt_bus_shell_matches_grid_topology(bus=bus, grid=circuit):
                    bus.mark_emt_model_grid_synchronized()
                else:
                    pass
        else:
            synchronize_emt_bus_shell_with_grid(bus=bus,
                                                grid=circuit,
                                                var_factory=var_factory,
                                                device_to_skip=api_object)
    else:
        invalid_shell: bool = bus.emt_model.empty()
        if not invalid_shell:
            try:
                get_bus_emt_algebraic_vars(bus.emt_model)
            except (AttributeError, TypeError, ValueError):
                invalid_shell = True
            else:
                pass
        else:
            pass

        if invalid_shell:
            phase_mask: list[bool]
            if bus.is_dc:
                phase_mask = list((False, False, False, False))
            else:
                phase_mask = list((False, True, True, True))
            bus.emt_model = BusEmtTemplate(
                vf=var_factory,
                mask=phase_mask,
                is_dc=bus.is_dc,
                name=f"{bus.name}_emt_template",
            ).block
        else:
            pass


def initialize_connected_bus_models_for_editor_assignment(api_object: ALL_DEV_TYPES,
                                                          circuit: MultiCircuit | None,
                                                          var_factory: VarFactory,
                                                          mode: DynamicSimulationMode) -> None:
    """Initialize all bus-side shells needed by one editor-assigned model.

    :param api_object: Injection or branch device receiving the dynamic model.
    :param circuit: Optional grid used for EMT topology reconciliation.
    :param var_factory: Shared symbolic variable factory.
    :param mode: Dynamic simulation domain being edited.
    :return: None.
    """
    if isinstance(api_object, InjectionParent):
        bus: Bus | None = api_object.bus
        if bus is None:
            pass
        elif mode == DynamicSimulationMode.RMS:
            _initialize_editor_assigned_rms_bus_model(bus=bus, var_factory=var_factory)
        elif mode == DynamicSimulationMode.EMT:
            _initialize_editor_assigned_emt_bus_model(bus=bus,
                                                      api_object=api_object,
                                                      circuit=circuit,
                                                      var_factory=var_factory)
        else:
            raise ValueError(f"Unsupported dynamic editor mode {mode}")
    elif isinstance(api_object, BranchParent):
        if mode == DynamicSimulationMode.RMS:
            _initialize_editor_assigned_rms_bus_model(bus=api_object.bus_from, var_factory=var_factory)
            _initialize_editor_assigned_rms_bus_model(bus=api_object.bus_to, var_factory=var_factory)
        elif mode == DynamicSimulationMode.EMT:
            _initialize_editor_assigned_emt_bus_model(bus=api_object.bus_from,
                                                      api_object=api_object,
                                                      circuit=circuit,
                                                      var_factory=var_factory)
            _initialize_editor_assigned_emt_bus_model(bus=api_object.bus_to,
                                                      api_object=api_object,
                                                      circuit=circuit,
                                                      var_factory=var_factory)
            if not api_object.emt_model.empty() and circuit is not None:
                reconcile_saved_emt_model_against_current_topology(device=api_object,
                                                                   grid=circuit,
                                                                   var_factory=var_factory)
            else:
                pass
        else:
            raise ValueError(f"Unsupported dynamic editor mode {mode}")
    else:
        pass


def is_valid_symbol_name(name: str) -> bool:
    """Return whether text is a valid symbolic identifier.

    :param name: Candidate variable or block name.
    :return: Whether the name follows the supported identifier grammar.
    """
    return re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) is not None
