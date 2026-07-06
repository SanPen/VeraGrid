from __future__ import annotations

import copy
import re
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel, \
    QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Diagrams.block_diagram import BlockDiagram
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.bus_emt_template import BusEmtTemplate, get_bus_emt_template
from VeraGridEngine.Utils.Symbolic.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var, string_to_symbolic, symbolic_to_string
from VeraGrid.Gui.gui_functions import ComboDelegate, TextDelegate
from VeraGrid.Gui.wrappable_table_model import WrappableTableModel
from VeraGridEngine.enumerations import DeviceType, DynamicSimulationMode, DynamicTableModelMode, \
    ParamPowerFlowReferenceType, VarPowerFlowReferenceType
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_library import is_supported_library_payload


def _new_uid() -> int:
    """
    Generate a fresh integer identifier.

    :return: Fresh uid.
    """
    return uuid.uuid4().int


def build_variables_rows(block: Block | None, rows: List["BlockParameterRow"]) -> None:
    if block is not None:
        build_block_variables_rows(block, rows)
        if block.children:
            child: Block
            for child in block.children:
                build_variables_rows(child, rows)


def build_block_variables_rows(block: Block, rows: List["BlockParameterRow"]) -> None:
    var: Var
    for var in block.state_vars:
        init_eq: Expr | None = block.init_eqs.get(var)
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


def build_parameters_rows(table_model: Any, block: Block | None, rows: List["BlockParameterRow"]) -> None:
    if block is not None:
        build_block_parameters_rows(table_model, block, rows)
        if block.children:
            child: Block
            for child in block.children:
                build_block_parameters_rows(table_model, child, rows)


def build_block_parameters_rows(table_model: Any, blk: Block, rows: List["BlockParameterRow"]) -> None:
    var: Var
    expr: Expr

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

    for var, expr in blk.parameters.items():
        if isinstance(expr, Const):
            rows.append(BlockParameterRow(
                name=var.name,
                kind=BlockParameterKind.FIXED_PARAMETER,
                key_var=var,
                value=expr.value,
                editable_name=True,
                editable_value=False,
                value_type=table_model.get_python_value_type(expr.value),
                source_dict_name="parameters"
            ))
        else:
            rows.append(BlockParameterRow(
                name=var.name,
                kind=BlockParameterKind.FIXED_PARAMETER,
                key_var=var,
                value=expr,
                editable_name=True,
                editable_value=False,
                value_type=str,
                source_dict_name="parameters"
            ))


def update_source_dict(block: Block | None,
                       row: "BlockParameterRow",
                       value: Any,
                       old_expr: Any = None) -> None:
    if block is not None:
        update_param_value(block, row, value, old_expr)
        if block.children:
            child: Block
            for child in block.children:
                update_source_dict(child, row, value, old_expr)


def _parse_symbolic_editor_value(block: Block | None, value: Any) -> Any:
    if isinstance(value, Expr):
        return value
    elif isinstance(value, (int, float)):
        return value
    elif isinstance(value, str):
        if block is None:
            return value
        else:
            parsed = string_to_symbolic(value, build_block_symbol_namespace(block))
            return parsed
    else:
        return value


def update_param_value(blk: Block, row: "BlockParameterRow", value: Any, old_expr: Any = None) -> None:
    if row.kind == BlockParameterKind.EVENT_PARAMETER:
        if row.key_var is not None:
            blk.event_dict[row.key_var] = value
            if old_expr is not None and old_expr in blk.event_dict.values():
                del blk.event_dict[row.key_var]
                blk.event_dict[row.key_var] = value
    elif row.kind == BlockParameterKind.MODE_PARAMETER:
        if row.key_var is not None:
            blk.mode_dict[row.key_var] = value
    elif row.kind == BlockParameterKind.FIXED_PARAMETER:
        if row.key_var is not None:
            blk.parameters[row.key_var] = value
    elif row.kind == BlockParameterKind.STATE_EQUATION:
        if row.item_index is not None:
            blk.state_eqs[row.item_index] = value
    elif row.kind == BlockParameterKind.ALGEBRAIC_EQUATION:
        if row.item_index is not None:
            blk.algebraic_eqs[row.item_index] = value
    elif row.kind == BlockParameterKind.STATE_VAR:
        if row.key_var is not None:
            blk.init_values[row.key_var] = value
    else:
        pass


def build_equations_rows(block: Block | None, rows: List["BlockParameterRow"]) -> None:
    if block is not None:
        build_block_equations_rows(block, rows)
        if block.children:
            child: Block
            for child in block.children:
                build_equations_rows(child, rows)


def build_block_equations_rows(blk: Block, rows: List["BlockParameterRow"]) -> None:
    index: int
    expr: Expr

    for index, expr in enumerate(blk.state_eqs):
        rows.append(BlockParameterRow(
            name="",
            kind=BlockParameterKind.STATE_EQUATION,
            key_var=None,
            value=expr,
            editable_name=False,
            editable_value=True,
            value_type=str,
            item_index=index,
        ))

    for index, expr in enumerate(blk.algebraic_eqs):
        rows.append(BlockParameterRow(
            name="",
            kind=BlockParameterKind.ALGEBRAIC_EQUATION,
            key_var=None,
            value=expr,
            editable_name=False,
            editable_value=True,
            value_type=str,
            item_index=index,
        ))


class BlockParameterKind(Enum):
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
    if isinstance(value, Expr):
        return symbolic_to_string(value)
    else:
        return value


def refresh_block_parameter_row_cache(row: BlockParameterRow) -> None:
    row.display_value = build_block_parameter_display_value(row.value)

    if row.init_eq is not None:
        row.display_init_eq = build_block_parameter_display_value(row.init_eq)
    else:
        row.display_init_eq = None


def refresh_row_search_cache(row: BlockParameterRow) -> None:
    parts: list[str] = list([str(row.name or "")])
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

    def createEditor(self,
                     parent: QtWidgets.QWidget,
                     option: QtWidgets.QStyleOptionViewItem,
                     index: QtCore.QModelIndex) -> QtWidgets.QWidget | None:
        """

        :param parent:
        :param option:
        :param index:
        :return:
        """
        model = index.model()
        if isinstance(model, QtCore.QSortFilterProxyModel):
            source_index = model.mapToSource(index)
            source_model = model.sourceModel()
            if isinstance(source_model, WrappableBlockTableModel):
                row = source_model.get_row(source_index.row())
            else:
                row = None
        else:
            if isinstance(model, WrappableBlockTableModel):
                row = model.get_row(index.row())
            else:
                row = None
        if row is None:
            return QLineEdit(parent)

        if not row.editable_value or row.is_section:
            return None

        if row.kind in (BlockParameterKind.STATE_VAR, BlockParameterKind.ALGEBRAIC_VAR):
            return QLineEdit(parent)
        elif row.kind in (BlockParameterKind.EVENT_PARAMETER, BlockParameterKind.MODE_PARAMETER):
            return self._make_float_editor(parent) if row.value_type == float else QLineEdit(parent)
        elif row.kind == BlockParameterKind.FIXED_PARAMETER:
            return self._make_float_editor(parent) if row.value_type == float else QLineEdit(parent)
        elif row.kind in (BlockParameterKind.STATE_EQUATION, BlockParameterKind.ALGEBRAIC_EQUATION):
            return QLineEdit(parent)
        else:
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

    def __init__(self,
                 api_object: ALL_DEV_TYPES,
                 devices_static_params_mapping: Dict[DeviceType, List[ParamPowerFlowReferenceType]],
                 current_kind: BlockParameterKind,
                 parent: Optional[QtWidgets.QWidget] = None):
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
            static_params = devices_static_params_mapping.get(device_type, list())
            param: ParamPowerFlowReferenceType
            for param in static_params:
                self.static_variable_combo.addItem(param.value, param)

        label: str
        value: BlockParameterKind
        for label, value in self.CATEGORY_OPTIONS:
            self.category_combo.addItem(label, value)

        self._current_kind: BlockParameterKind = current_kind
        index: int
        for index in range(self.category_combo.count()):
            if self.category_combo.itemData(index) == current_kind:
                self.category_combo.setCurrentIndex(index)
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
    block_updated = Signal(object)

    def __init__(self,
                 var_factory: VarFactory,
                 parameter_value_type_role: int,
                 parameter_editable_role: int,
                 block_search_role: int,
                 api_object: ALL_DEV_TYPES = None,
                 parent: Optional[QtCore.QObject] = None):
        super().__init__(parent)
        self._table_view = parent
        self.var_factory = var_factory
        self.api_object: ALL_DEV_TYPES = api_object
        self.block: Block | None = None
        self.rows: List[BlockParameterRow] = list()
        self.mode = DynamicTableModelMode.VARIABLES
        self.headers = ["Type", "Name", "Init Equation"]
        self.symbol_namespace: Dict[str, Expr] | None = None
        self._value_column = 2
        self._parameter_value_type_role: int = parameter_value_type_role
        self._parameter_editable_role: int = parameter_editable_role
        self._block_search_role: int = block_search_role

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
                else:
                    return row.name
            elif col == 2:
                if self.mode == DynamicTableModelMode.VARIABLES:
                    return row.display_init_eq if row.init_eq is not None else row.display_value
                elif self.mode == DynamicTableModelMode.PARAMETERS:
                    if row.kind == BlockParameterKind.FIXED_PARAMETER:
                        return row.value
                    else:
                        return row.display_value
                else:
                    return None
        elif role == self._parameter_value_type_role and col == self._value_column:
            if self.mode == DynamicTableModelMode.VARIABLES:
                return "float" if row.value_type == float else "text"
            else:
                return self.get_python_value_type(row.value).__name__
        elif role == self._parameter_editable_role and col == self._value_column:
            if self.mode == DynamicTableModelMode.PARAMETERS and row.kind == BlockParameterKind.FIXED_PARAMETER:
                return False
            else:
                return row.editable_value
        elif role == QtCore.Qt.ItemDataRole.BackgroundRole:
            if col == 2 and self.mode == DynamicTableModelMode.PARAMETERS and not row.editable_value and row.kind != BlockParameterKind.FIXED_PARAMETER:
                return QColor("#d3d3d3")
            else:
                return QColor("#f7fafc")
        elif role == QtCore.Qt.ItemDataRole.ForegroundRole:
            return QColor("#333333")
        elif role == self._block_search_role:
            return row.search_text
        else:
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
            elif self.mode == DynamicTableModelMode.VARIABLES:
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
            else:
                return False
        else:
            return False

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemFlag.NoItemFlags
        elif index.row() < 0 or index.row() >= len(self.rows):
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
            else:
                return None
        else:
            return None

    def get_row(self, row_index: int) -> BlockParameterRow | None:
        if 0 <= row_index < len(self.rows):
            return self.rows[row_index]
        else:
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
        else:
            pass

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
        else:
            pass

    def set_value_from_expression(self, row_index: int, expr: Expr) -> None:
        if 0 <= row_index < len(self.rows):
            row = self.rows[row_index]
            row.value = expr
            refresh_block_parameter_row_cache(row)
            refresh_row_search_cache(row)
            update_source_dict(self.block, row, expr)
            index = self.index(row_index, self._value_column)
            self.dataChanged.emit(index, index, [QtCore.Qt.ItemDataRole.EditRole])
        else:
            pass

    def add_variable_at_end_of_type(self, name: str, category: str, parameter_value: float = 0.0) -> None:
        if self.block is None:
            raise ValueError("No block is currently selected.")
        new_var = self.var_factory.add_var(name=name)
        if category == "state":
            self.block.state_vars.append(new_var)
            if parameter_value != 0.0:
                self.block.init_values[new_var] = self.var_factory.add_const(parameter_value, name=name)
            else:
                pass
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
        else:
            return -1

    @staticmethod
    def get_python_value_type(value) -> type:
        if isinstance(value, int):
            return int
        elif isinstance(value, float):
            return float
        else:
            return str


class InspectModel(QWidget):
    def __init__(self, block: Block, parent=None):
        super().__init__(parent)

        self.block = block

        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)

        left_panel = QVBoxLayout()
        main_layout.addLayout(left_panel)

        var_header_layout = QHBoxLayout()
        var_label = QLabel("Variables")
        var_header_layout.addWidget(var_label)
        left_panel.addLayout(var_header_layout)

        self.list_vars = QListWidget()
        left_panel.addWidget(self.list_vars)

        param_header_layout = QHBoxLayout()
        param_label = QLabel("Parameters")
        param_header_layout.addWidget(param_label)
        left_panel.addLayout(param_header_layout)

        self.table_params = QTableWidget()
        self.table_params.setColumnCount(2)
        self.table_params.setHorizontalHeaderLabels(["Name", "Value"])
        self.table_params.horizontalHeader().setStretchLastSection(True)
        self.table_params.verticalHeader().setVisible(False)
        self.table_params.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        left_panel.addWidget(self.table_params)

        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel)

        eqn_header_layout = QHBoxLayout()
        eqn_label = QLabel("Equations")
        eqn_header_layout.addWidget(eqn_label)
        right_panel.addLayout(eqn_header_layout)

        self.list_eqns = QListWidget()
        right_panel.addWidget(self.list_eqns)

        self.refresh_lists(self.block)

    def refresh_lists(self, model=None, clear=True):
        if model is None:
            model = self.block

        if clear:
            self.list_vars.clear()
            self.table_params.setRowCount(0)
            self.list_eqns.clear()
        else:
            pass

        var: Var
        for var in model.state_vars + model.algebraic_vars:
            item = QListWidgetItem(f"{var.name} ")
            self.list_vars.addItem(item)

        param: Var
        value: Any
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

        eq: Expr
        for eq in model.state_eqs + model.algebraic_eqs:
            eq_type = "state" if eq in model.state_eqs else "algebraic"
            item = QListWidgetItem(f"{symbolic_to_string(eq)} ({eq_type})")
            self.list_eqns.addItem(item)

        submodel: Block
        for submodel in model.children:
            self.refresh_lists(submodel, clear=False)

# this class in cynamic_editor_library


class BlockTableFilterProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, search_role: int, parent: QtCore.QObject | None = None):
        super().__init__(parent)
        self.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterRole(search_role)
        self.setFilterKeyColumn(0)


def clone_block_for_editing(block: Block) -> Block:
    return copy.deepcopy(block)


def remap_serialized_uids(data: Any, uid_map: Dict[int, int]) -> Any:
    if isinstance(data, dict):
        remapped_data: Dict[str, Any] = dict()
        key: str
        value: Any

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


def _build_block_uid_lookup(root_block: Block) -> Dict[int, Block]:
    block_lookup: Dict[int, Block] = dict()
    block_item: Block

    for block_item in root_block.get_all_blocks():
        block_lookup[block_item.uid] = block_item

    return block_lookup


def _ensure_block_tree_names(block: Block, prefix: str = "block") -> None:
    if not block.name:
        block.name = f"{prefix}_{str(block.uid)[:8]}"
    else:
        pass

    child_index: int
    child_block: Block
    for child_index, child_block in enumerate(block.children, start=1):
        _ensure_block_tree_names(child_block, prefix=f"{block.name}_{child_index}")


def copy_block_state(source_block: Block, target_block: Block) -> None:
    source_clone: Block = clone_block_for_editing(source_block)
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
    target_block.discrete_eqs = source_clone.discrete_eqs
    target_block.external_mapping = source_clone.external_mapping
    target_block.api_obj_mapping = source_clone.api_obj_mapping
    target_block.init_values = source_clone.init_values
    target_block.var_mapping = source_clone.var_mapping
    target_block.event_dict = source_clone.event_dict
    target_block.mode_dict = source_clone.mode_dict
    target_block.diagram = source_clone.diagram


def block_requires_editor_connection_bootstrap(block: Block) -> bool:
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
    if bus.rms_model.empty():
        initialize_bus_rms(bus=bus, vf=var_factory)
    else:
        pass


def _initialize_editor_assigned_emt_bus_model(bus: Bus,
                                              api_object: Any,
                                              circuit: MultiCircuit | None,
                                              var_factory: VarFactory,
                                              editor_interface_refs: set[VarPowerFlowReferenceType] | None = None) -> None:
    if bus.emt_model.empty():
        if editor_interface_refs is not None:
            mask: list[bool] | None = None

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
            elif isinstance(api_object, BranchParent):
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
                elif api_object.bus_to is bus:
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

        if mask is not None:
            if bus.is_dc:
                bus.emt_model = BusEmtTemplate(
                    vf=var_factory,
                    mask=list([False, False, False, False]),
                    is_dc=True,
                    name=f"{bus.name}_emt_template",
                ).block
            elif any(mask):
                bus.emt_model = BusEmtTemplate(
                    vf=var_factory,
                    mask=mask,
                    is_dc=False,
                    name=f"{bus.name}_emt_template",
                ).block
            else:
                pass
        elif circuit is not None:
            get_bus_emt_template(grid=circuit, bus=bus)
        elif bus.is_dc:
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
                                                      var_factory=var_factory,
                                                      editor_interface_refs=editor_interface_refs)
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
    return re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) is not None


def block_namespace_contains_name(block: Block, name: str, exclude_var: Var | None = None) -> bool:
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
