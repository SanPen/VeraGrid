# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Modal editor for one symbolic block in the Dynamic Model Editor."""

from __future__ import annotations

import ast
from enum import Enum
from io import StringIO
import re
import tokenize
from typing import Dict, List, Mapping, Sequence

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal

from VeraGrid.Gui.Icons import icons_rc
from VeraGrid.Gui.base_python_code_editor import BasePythonCodeEditor
from VeraGrid.Gui.DynamicModelEditor.dynamic_block_properties_gui import (
    Ui_DynamicBlockPropertiesDialog,
)
from VeraGridEngine.enumerations import (
    BlockType,
    BlockSymbolCategory,
    BlockSymbolKind,
    EquationExportSection,
    ParamPowerFlowReferenceType,
    ShuntConnectionType,
    VarPowerFlowReferenceType,
    WindingType,
)
from VeraGrid.Gui.DynamicModelEditor.dynamic_equation_pdf import (
    EquationExportEntry,
    build_equation_pdf_suggested_name,
    build_latex_source,
    build_list_equation_entries,
    build_mapping_equation_entries,
    build_state_equation_entries,
    order_state_differential_variables,
    write_equation_pdf,
)
from VeraGrid.Gui.DynamicModelEditor.dynamic_procedural_logic import (
    RuntimeLogicEditorWidget,
    RuntimeLogicValidationResult,
    get_procedural_expression_variables,
)
from VeraGridEngine.Utils.procedural_logic import ProceduralLogicBase
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.template_definition import TemplateDefinition, TemplateProp
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.latex_printer import symbolic_to_latex
from VeraGridEngine.Utils.Symbolic.symbolic import (
    BinOp,
    Comparison,
    Const,
    Expr,
    Func2,
    UnOp,
    Var,
    get_expression_vars,
    string_to_symbolic,
    symbolic_to_string,
)

class BlockEquationDraft:
    """Validated, detached set of equations waiting to be applied to a block."""

    __slots__ = (
        "_state_eqs",
        "_algebraic_eqs",
        "_init_eqs",
        "_diff_init_eqs",
        "_variable_declarations",
    )

    def __init__(self,
                 state_eqs: Sequence[Expr],
                 algebraic_eqs: Sequence[Expr],
                 init_eqs: Mapping[Var, Expr],
                 diff_init_eqs: Mapping[Var, Expr],
                 variable_declarations: Mapping[str, Sequence[Var]] | None = None) -> None:
        """
        Create a detached draft from already parsed symbolic expressions.

        :param state_eqs: Value supplied for ``state_eqs``.
        :param algebraic_eqs: Value supplied for ``algebraic_eqs``.
        :param init_eqs: Value supplied for ``init_eqs``.
        :param diff_init_eqs: Value supplied for ``diff_init_eqs``.
        :param variable_declarations: Informative ordered DAE variable lists.
        :return: None.
        """
        self._state_eqs: List[Expr] = list(state_eqs)
        self._algebraic_eqs: List[Expr] = list(algebraic_eqs)
        self._init_eqs: Dict[Var, Expr] = dict(init_eqs)
        self._diff_init_eqs: Dict[Var, Expr] = dict(diff_init_eqs)
        self._variable_declarations: Dict[str, List[Var]] = dict()
        if variable_declarations is not None:
            declaration_name: str
            declaration_variables: Sequence[Var]
            for declaration_name, declaration_variables in variable_declarations.items():
                self._variable_declarations[declaration_name] = list(declaration_variables)
        else:
            pass

    def get_state_eqs(self) -> List[Expr]:
        """
        :return: A copy of the state equations.
        """
        return list(self._state_eqs)

    def get_algebraic_eqs(self) -> List[Expr]:
        """
        :return: A copy of the algebraic equations.
        """
        return list(self._algebraic_eqs)

    def get_init_eqs(self) -> Dict[Var, Expr]:
        """
        :return: A copy of the initialization equations.
        """
        return dict(self._init_eqs)

    def get_diff_init_eqs(self) -> Dict[Var, Expr]:
        """
        :return: A copy of the derivative initialization equations.
        """
        return dict(self._diff_init_eqs)

    def get_variable_declaration(self, section_name: str) -> List[Var] | None:
        """Return one optional generated variable-order declaration.

        :param section_name: One of ``state_vars``, ``algebraic_vars`` or ``diff_vars``.
        :return: Declared variables, or ``None`` when older source omitted the section.
        """
        variables: List[Var] | None = self._variable_declarations.get(section_name, None)
        if variables is not None:
            return list(variables)
        else:
            return None


class ParameterDraftRow:
    """One numeric parameter value edited without mutating its source constant."""

    __slots__ = ("_category", "_variable", "_constant", "_draft_text")

    def __init__(self, category: str, variable: Var, constant: Const) -> None:
        """
        Capture one parameter and its original constant object.

        :param category: Value supplied for ``category``.
        :param variable: Symbolic variable used by the operation.
        :param constant: Value supplied for ``constant``.
        :return: None.
        """
        self._category: str = category
        self._variable: Var = variable
        self._constant: Const = constant
        self._draft_text: str = str(constant.value)

    def get_category(self) -> str:
        """
        :return: The user-facing parameter category.
        """
        return self._category

    def get_variable(self) -> Var:
        """
        :return: The parameter variable.
        """
        return self._variable

    def get_constant(self) -> Const:
        """
        :return: The original constant that will be updated on Apply.
        """
        return self._constant

    def get_draft_text(self) -> str:
        """
        :return: The pending textual value.
        """
        return self._draft_text

    def set_draft_text(self, value: str) -> None:
        """
        Set the pending textual value without touching the source block.

        :param value: Value supplied for ``value``.
        :return: None.
        """
        self._draft_text = value

    def parse_value(self) -> float | complex:
        """
        Parse the pending value as a finite real or complex number.

        :return: Pending value parsed as a finite real or complex number.
        """
        value_text: str = self._draft_text.strip()
        if len(value_text) == 0:
            raise ValueError(f"Parameter '{self._variable.name}' cannot be empty")
        else:
            pass

        if "j" in value_text.lower():
            parsed_value: float | complex = complex(value_text)
        else:
            parsed_value = float(value_text)

        if isinstance(parsed_value, complex):
            if parsed_value.real == float("inf") or parsed_value.real == float("-inf"):
                raise ValueError(f"Parameter '{self._variable.name}' must be finite")
            elif parsed_value.imag == float("inf") or parsed_value.imag == float("-inf"):
                raise ValueError(f"Parameter '{self._variable.name}' must be finite")
            elif parsed_value.real != parsed_value.real or parsed_value.imag != parsed_value.imag:
                raise ValueError(f"Parameter '{self._variable.name}' must be finite")
            else:
                pass
        else:
            if parsed_value == float("inf") or parsed_value == float("-inf") or parsed_value != parsed_value:
                raise ValueError(f"Parameter '{self._variable.name}' must be finite")
            else:
                pass
        return parsed_value

    def is_unchanged_unset(self) -> bool:
        """Return whether an originally unset constant remains unset.

        :return: ``True`` for an unchanged ``Const(None)`` draft.
        """
        return self._constant.value is None and self._draft_text.strip().lower() == "none"


class BlockStructuralEditRequest:
    """Synchronous request for an editor-owned structural block rebuild."""

    __slots__ = (
        "_block",
        "_block_type",
        "_builder",
        "_parameter_values",
        "_success",
        "_error_message",
    )

    def __init__(self,
                 block: Block,
                 block_type: BlockType,
                 builder: TemplateDefinition,
                 parameter_values: Sequence[tuple[str, float | complex]]) -> None:
        """Capture the candidate builder and mutable operation result.

        :param block: Existing working-tree block to rebuild in place.
        :param block_type: Native type controlling the builder.
        :param builder: Builder containing the validated draft options.
        :param parameter_values: Numeric values to transfer by semantic name.
        :return: None.
        """
        self._block: Block = block
        self._block_type: BlockType = block_type
        self._builder: TemplateDefinition = builder
        self._parameter_values: List[tuple[str, float | complex]] = list(parameter_values)
        self._success: bool = False
        self._error_message: str = ""

    def get_block(self) -> Block:
        """
        :return: The existing block targeted by the rebuild.
        """
        return self._block

    def get_block_type(self) -> BlockType:
        """
        :return: The native builder type.
        """
        return self._block_type

    def get_builder(self) -> TemplateDefinition:
        """
        :return: The configured template builder.
        """
        return self._builder

    def get_parameter_values(self) -> List[tuple[str, float | complex]]:
        """
        :return: Numeric parameter values that must survive reconstruction.
        """
        return list(self._parameter_values)

    def set_result(self, success: bool, error_message: str) -> None:
        """Store the result produced synchronously by the owning editor.

        :param success: Whether reconstruction completed.
        :param error_message: User-facing failure detail.
        :return: None.
        """
        self._success = success
        self._error_message = error_message

    def is_successful(self) -> bool:
        """
        Return whether the owning editor completed the rebuild.

        :return: Whether the owning editor completed the rebuild.
        """
        return self._success

    def get_error_message(self) -> str:
        """
        Return the editor-provided failure detail.

        :return: The editor-provided failure detail.
        """
        return self._error_message


class BlockVariableRenameRequest:
    """Synchronous request for an editor-owned complete variable rename."""

    __slots__ = (
        "_variable",
        "_success",
        "_new_name",
    )

    def __init__(self, variable: Var) -> None:
        """Create a pending rename request for one existing symbolic variable.

        :param variable: Existing variable selected in Block Properties.
        :return: None.
        """
        self._variable: Var = variable
        self._success: bool = False
        self._new_name: str = variable.name

    def get_variable(self) -> Var:
        """
        :return: Existing variable targeted by the rename.
        """
        return self._variable

    def set_result(self, success: bool, new_name: str) -> None:
        """Store the synchronous result produced by the owning editor.

        :param success: Whether the complete rename was applied.
        :param new_name: Final accepted variable name.
        :return: None.
        """
        self._success = success
        self._new_name = new_name

    def is_successful(self) -> bool:
        """
        :return: Whether the complete rename was applied.
        """
        return self._success

    def get_new_name(self) -> str:
        """
        :return: Final accepted variable name.
        """
        return self._new_name


class BlockStructuralSettingsModel(QtCore.QAbstractTableModel):
    """Editable draft of builder inputs that alter generated block structure."""

    __slots__ = ("_properties", "_original_values")

    def __init__(self,
                 properties: Sequence[TemplateProp],
                 parent: QtCore.QObject | None = None) -> None:
        """Capture visible structural properties without touching the block.

        :param properties: Builder properties shown in this table.
        :param parent: Owning Qt object.
        :return: None.
        """
        super().__init__(parent)
        self._properties: List[TemplateProp] = list(properties)
        self._original_values: List[str] = [repr(prop.value) for prop in self._properties]

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        :param parent: Owning Qt widget.
        :return: The number of structural settings.
        """
        if parent.isValid():
            return 0
        else:
            return len(self._properties)

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        :param parent: Owning Qt widget.
        :return: Setting and value columns.
        """
        if parent.isValid():
            return 0
        else:
            return 2

    def data(self, index: QtCore.QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        """
        :param index: Value supplied for ``index``.
        :param role: Value supplied for ``role``.
        :return: One setting name or draft value.
        """
        if not index.isValid() or index.row() >= len(self._properties):
            return None
        else:
            prop: TemplateProp = self._properties[index.row()]
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            if index.column() == 0:
                return prop.name
            elif index.column() == 1:
                if isinstance(prop.value, Enum):
                    return prop.value.name
                else:
                    return repr(prop.value)
            else:
                return None
        elif role == Qt.ItemDataRole.ToolTipRole:
            return prop.descr
        else:
            return None

    def setData(self,
                index: QtCore.QModelIndex,
                value: object,
                role: int = Qt.ItemDataRole.EditRole) -> bool:
        """
        Parse one edited builder value according to its current type.

        :param index: Value supplied for ``index``.
        :param value: Value supplied for ``value``.
        :param role: Value supplied for ``role``.
        :return: True when the edited value was accepted; otherwise False.
        """
        if not index.isValid() or index.column() != 1 or role != Qt.ItemDataRole.EditRole:
            return False
        else:
            prop: TemplateProp = self._properties[index.row()]
            value_text: str = str(value).strip()
        try:
            parsed_value: object = parse_structural_setting_value(prop, value_text)
        except (SyntaxError, TypeError, ValueError):
            return False
        else:
            prop.value = parsed_value
            self.dataChanged.emit(index, index, list((role, Qt.ItemDataRole.DisplayRole,)))
            return True

    def flags(self, index: QtCore.QModelIndex) -> Qt.ItemFlag:
        """
        Make only the value column editable.

        :param index: Value supplied for ``index``.
        :return: Item flags that make only the value column editable.
        """
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        elif index.column() == 1:
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable
        else:
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def headerData(self,
                   section: int,
                   orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole) -> object:
        """
        :param section: Value supplied for ``section``.
        :param orientation: Value supplied for ``orientation``.
        :param role: Value supplied for ``role``.
        :return: Structural-settings headers.
        """
        headers: tuple[str, ...] = ("Setting", "Value")
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(headers):
                return self.tr(headers[section])
            else:
                return None
        else:
            return None

    def has_changes(self) -> bool:
        """
        :return: Whether any displayed builder value differs from its baseline.
        """
        result: bool = False
        row_index: int
        for row_index in range(len(self._properties)):
            if repr(self._properties[row_index].value) != self._original_values[row_index]:
                result = True
            else:
                pass
        return result

    def get_property(self, row_index: int) -> TemplateProp | None:
        """Return one structural property for delegate editor selection.

        :param row_index: Source row index.
        :return: Matching property or ``None``.
        """
        if 0 <= row_index < len(self._properties):
            return self._properties[row_index]
        else:
            return None


class StructuralSettingDelegate(QtWidgets.QStyledItemDelegate):
    """Typed Qt editor delegate for structural builder values."""

    __slots__ = ()

    def createEditor(self,
                     parent: QtWidgets.QWidget,
                     option: QtWidgets.QStyleOptionViewItem,
                     index: QtCore.QModelIndex) -> QtWidgets.QWidget:
        """Create a combo, spin box, or text editor for one setting.

        :param parent: Owning view widget.
        :param option: Qt style option.
        :param index: Edited model index.
        :return: Typed editor widget.
        """
        _unused_option: QtWidgets.QStyleOptionViewItem = option
        model: QtCore.QAbstractItemModel | None = index.model()
        if isinstance(model, BlockStructuralSettingsModel):
            prop: TemplateProp | None = model.get_property(index.row())
        else:
            prop = None
        if prop is None:
            return QtWidgets.QLineEdit(parent)
        elif isinstance(prop.value, bool):
            bool_combo: QtWidgets.QComboBox = QtWidgets.QComboBox(parent)
            bool_combo.addItems(list(("True", "False",)))
            return bool_combo
        elif isinstance(prop.value, int):
            integer_editor: QtWidgets.QSpinBox = QtWidgets.QSpinBox(parent)
            integer_editor.setRange(0, 1000000)
            return integer_editor
        elif isinstance(prop.value, Enum):
            enum_combo: QtWidgets.QComboBox = QtWidgets.QComboBox(parent)
            enum_member: Enum
            for enum_member in prop.value.__class__:
                enum_combo.addItem(enum_member.name)
            return enum_combo
        elif prop.name == "connection_type" and prop.value is None:
            connection_combo: QtWidgets.QComboBox = QtWidgets.QComboBox(parent)
            connection_combo.addItem("None")
            shunt_member: ShuntConnectionType
            for shunt_member in ShuntConnectionType:
                connection_combo.addItem(shunt_member.name)
            return connection_combo
        else:
            return QtWidgets.QLineEdit(parent)

    def setEditorData(self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex) -> None:
        """Load the current setting into its typed editor.

        :param editor: Active delegate editor.
        :param index: Edited model index.
        :return: None.
        """
        value_text: str = str(index.data(Qt.ItemDataRole.EditRole))
        if isinstance(editor, QtWidgets.QComboBox):
            editor.setCurrentText(value_text)
        elif isinstance(editor, QtWidgets.QSpinBox):
            editor.setValue(int(value_text))
        elif isinstance(editor, QtWidgets.QLineEdit):
            editor.setText(value_text)
        else:
            pass

    def setModelData(self,
                     editor: QtWidgets.QWidget,
                     model: QtCore.QAbstractItemModel,
                     index: QtCore.QModelIndex) -> None:
        """Commit the typed editor value into the structural draft.

        :param editor: Active delegate editor.
        :param model: Structural settings model.
        :param index: Edited model index.
        :return: None.
        """
        if isinstance(editor, QtWidgets.QComboBox):
            model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)
        elif isinstance(editor, QtWidgets.QSpinBox):
            model.setData(index, str(editor.value()), Qt.ItemDataRole.EditRole)
        elif isinstance(editor, QtWidgets.QLineEdit):
            model.setData(index, editor.text(), Qt.ItemDataRole.EditRole)
        else:
            pass


def parse_structural_setting_value(prop: TemplateProp, value_text: str) -> object:
    """Parse a structural setting using its live default as the type contract.

    :param prop: Builder property being edited.
    :param value_text: User-entered text.
    :return: Typed builder value.
    """
    current_value: object = prop.value
    if prop.name == "connection_type" and current_value is None:
        if value_text.lower() == "none":
            return None
        else:
            connection_member: Enum
            for connection_member in ShuntConnectionType:
                if value_text == connection_member.name or value_text == str(connection_member.value):
                    return connection_member
                else:
                    pass
            for connection_member in WindingType:
                if value_text == connection_member.name or value_text == str(connection_member.value):
                    return connection_member
                else:
                    pass
            raise ValueError(f"Unknown connection type '{value_text}'")
    elif isinstance(current_value, bool):
        normalized: str = value_text.lower()
        if normalized == "true":
            return True
        elif normalized == "false":
            return False
        else:
            raise ValueError(f"'{value_text}' is not a boolean")
    elif isinstance(current_value, int):
        return int(value_text)
    elif isinstance(current_value, float):
        return float(value_text)
    elif isinstance(current_value, Enum):
        enum_member: Enum
        for enum_member in current_value.__class__:
            if value_text == enum_member.name or value_text == str(enum_member.value):
                return enum_member
            else:
                pass
        raise ValueError(f"Unknown option '{value_text}' for {prop.name}")
    elif isinstance(current_value, (tuple, list)):
        parsed_literal: object = ast.literal_eval(value_text)
        if isinstance(parsed_literal, (tuple, list)):
            return parsed_literal
        else:
            raise ValueError(f"'{prop.name}' requires a sequence")
    elif isinstance(current_value, str):
        return value_text
    else:
        raise ValueError(f"Unsupported structural setting '{prop.name}'")


def split_structural_template_properties(builder: TemplateDefinition) -> tuple[List[TemplateProp], List[TemplateProp]]:
    """Split simple general options from complex special settings.

    Numeric parameter values are intentionally excluded because the General
    Options parameter table is their single authoritative editor.

    :param builder: Builder whose inputs are classified.
    :return: Pair of simple and complex structural property lists.
    """
    general_properties: List[TemplateProp] = list()
    special_properties: List[TemplateProp] = list()
    dedicated_special_tab: bool = "jmarti" in builder.__class__.__name__.lower()
    prop: TemplateProp
    for prop in builder.params:
        value: object = prop.value
        if prop.name == "name" or isinstance(value, (complex, dict)):
            pass
        elif dedicated_special_tab:
            # JMarti's former creation dialog contained boolean, integer,
            # floating-point, enum and file-path fields. They all belong to the
            # dedicated tab, not only its phase switches.
            special_properties.append(prop)
        elif prop.name == "connection_type" and value is None:
            general_properties.append(prop)
        elif value is None:
            pass
        elif isinstance(value, (tuple, list)):
            special_properties.append(prop)
        elif isinstance(value, (bool, int, Enum)):
            general_properties.append(prop)
        else:
            pass
    return general_properties, special_properties


class BlockSymbolDraftRow:
    """Detached description of one existing or newly requested block symbol."""

    __slots__ = (
        "_owner",
        "_variable",
        "_name",
        "_kind",
        "_original_kind",
        "_exported",
        "_value_text",
        "_external_reference",
        "_static_reference",
        "_derivative_base_row",
    )

    def __init__(self,
                 owner: Block,
                 variable: Var | None,
                 name: str,
                 kind: BlockSymbolKind,
                 exported: bool,
                 value_text: str,
                 external_reference: VarPowerFlowReferenceType | None = None,
                 static_reference: ParamPowerFlowReferenceType | None = None,
                 derivative_base_row: "BlockSymbolDraftRow | None" = None) -> None:
        """
        Capture a symbol row without modifying its owner block.

        :param owner: Value supplied for ``owner``.
        :param variable: Symbolic variable used by the operation.
        :param name: Value supplied for ``name``.
        :param kind: Value supplied for ``kind``.
        :param exported: Value supplied for ``exported``.
        :param value_text: Value supplied for ``value_text``.
        :param external_reference: Value supplied for ``external_reference``.
        :param static_reference: Value supplied for ``static_reference``.
        :param derivative_base_row: Value supplied for ``derivative_base_row``.
        :return: None.
        """
        self._owner: Block = owner
        self._variable: Var | None = variable
        self._name: str = name
        self._kind: BlockSymbolKind = kind
        self._original_kind: BlockSymbolKind = kind
        self._exported: bool = exported and kind != BlockSymbolKind.INPUT
        self._value_text: str = value_text
        self._derivative_base_row: BlockSymbolDraftRow | None = derivative_base_row
        if self.supports_external_reference():
            self._external_reference: VarPowerFlowReferenceType | None = external_reference
            self._static_reference: ParamPowerFlowReferenceType | None = None
        elif self.supports_static_reference():
            self._external_reference = None
            self._static_reference = static_reference
        else:
            self._external_reference = None
            self._static_reference = None

    def get_owner(self) -> Block:
        """
        :return: The block that owns this symbol.
        """
        return self._owner

    def get_variable(self) -> Var | None:
        """
        :return: The existing variable or ``None`` for a staged addition.
        """
        return self._variable

    def set_variable(self, variable: Var) -> None:
        """Bind the authoritative variable created when the draft is applied.

        :param variable: Variable identity registered by ``VarFactory``.
        :return: None.
        """
        self._variable = variable

    def get_name(self) -> str:
        """
        Return the symbol name.

        :return: The symbol name.
        """
        return self._name

    def set_name(self, name: str) -> None:
        """
        Set the name of a staged new symbol.

        :param name: Value supplied for ``name``.
        :return: None.
        """
        self._name = name

    def get_kind(self) -> BlockSymbolKind:
        """
        Return the selected primary symbol role.

        :return: The selected primary symbol role.
        """
        return self._kind

    def set_kind(self, kind: BlockSymbolKind) -> None:
        """
        Set the selected primary symbol role.

        :param kind: Value supplied for ``kind``.
        :return: None.
        """
        self._kind = kind
        if self.supports_external_reference():
            self._static_reference = None
        elif self.supports_static_reference():
            self._external_reference = None
        else:
            self._external_reference = None
            self._static_reference = None

    def get_original_kind(self) -> BlockSymbolKind:
        """
        Return the primary role captured when the dialogue opened.

        :return: The primary role captured when the dialogue opened.
        """
        return self._original_kind

    def is_exported(self) -> bool:
        """
        Return whether the variable is independently exposed as an output.

        :return: Whether the variable is independently exposed as an output.
        """
        return self._exported

    def set_exported(self, exported: bool) -> None:
        """
        Set the staged output-export role.

        :param exported: Value supplied for ``exported``.
        :return: None.
        """
        self._exported = exported

    def is_new(self) -> bool:
        """
        Return whether the row represents a symbol not yet in VarFactory.

        :return: Whether the row represents a symbol not yet in VarFactory.
        """
        return self._variable is None

    def get_derivative_name(self) -> str:
        """
        Return the conventional derivative name for a staged state.

        :return: The conventional derivative name for a staged state.
        """
        return f"d_{self._name}"

    def get_derivative_base_row(self) -> "BlockSymbolDraftRow | None":
        """Return the staged state row associated with this derivative.

        :return: State draft used as the derivative's ``base_var``.
        """
        return self._derivative_base_row

    def get_static_reference(self) -> ParamPowerFlowReferenceType | None:
        """
        :return: The selected device static-parameter mapping, if any.
        """
        return self._static_reference

    def set_static_reference(self, reference: ParamPowerFlowReferenceType | None) -> None:
        """Stage one device static-parameter mapping.

        :param reference: Static mapping or ``None``.
        :return: None.
        """
        self._static_reference = reference
        if reference is not None:
            self._external_reference = None
        else:
            pass

    def get_external_reference(self) -> VarPowerFlowReferenceType | None:
        """
        Return the staged power-flow initialization mapping.

        :return: The staged power-flow initialization mapping.
        """
        return self._external_reference

    def set_external_reference(self, reference: VarPowerFlowReferenceType | None) -> None:
        """Stage one power-flow initialization mapping.

        :param reference: Power-flow mapping or ``None``.
        :return: None.
        """
        self._external_reference = reference
        if reference is not None:
            self._static_reference = None
        else:
            pass

    def supports_static_reference(self) -> bool:
        """
        :return: Whether this row represents a fixed static parameter.
        """
        return self._kind == BlockSymbolKind.PARAMETER

    def supports_external_reference(self) -> bool:
        """
        :return: Whether this row can be initialized from power-flow data.
        """
        return not self.kind_supports_value()

    def kind_supports_export(self) -> bool:
        """
        :return: Whether this primary role can also be an output.
        """
        # Inputs already belong to the incoming interface. Exposing the same
        # identity in the outgoing interface is ambiguous in both the table and
        # the graphics connection model, so only block-owned variables can be
        # exported.
        return not self.kind_supports_value() and self._kind != BlockSymbolKind.INPUT

    def kind_supports_value(self) -> bool:
        """
        :return: Whether this role stores a numeric constant.
        """
        return self._kind in set((BlockSymbolKind.PARAMETER, BlockSymbolKind.EVENT_PARAMETER, BlockSymbolKind.MODE_PARAMETER,))

    def parse_value(self) -> float:
        """
        Parse a finite numeric parameter value.

        :return: Parameter value parsed as a finite floating-point number.
        """
        if self.kind_supports_value():
            value: float = float(self._value_text)
            if value == float("inf") or value == float("-inf") or value != value:
                raise ValueError(f"Parameter '{self._name}' must be finite")
            else:
                return value
        else:
            return 0.0


def get_symbol_kind(block: Block, variable: Var) -> BlockSymbolKind:
    """
    :param block: Symbolic block used by the operation.
    :param variable: Symbolic variable used by the operation.
    :return: The primary role currently owned by one variable.
    """
    if variable in block.in_vars:
        return BlockSymbolKind.INPUT
    elif variable in block.algebraic_vars:
        return BlockSymbolKind.ALGEBRAIC
    elif variable in block.state_vars:
        return BlockSymbolKind.STATE
    elif variable in block.diff_vars:
        return BlockSymbolKind.DIFFERENTIAL
    elif variable in block.parameters:
        return BlockSymbolKind.PARAMETER
    elif variable in block.event_dict:
        return BlockSymbolKind.EVENT_PARAMETER
    elif variable in block.mode_dict:
        return BlockSymbolKind.MODE_PARAMETER
    else:
        return BlockSymbolKind.OUTPUT_ONLY


def get_symbol_value_text(block: Block, variable: Var, kind: BlockSymbolKind) -> str:
    """
    :param block: Symbolic block used by the operation.
    :param variable: Symbolic variable used by the operation.
    :param kind: Value supplied for ``kind``.
    :return: The numeric text associated with a parameter-like symbol.
    """
    expression: Expr | None = None
    if kind == BlockSymbolKind.PARAMETER:
        expression = block.parameters.get(variable, None)
    elif kind == BlockSymbolKind.EVENT_PARAMETER:
        expression = block.event_dict.get(variable, None)
    elif kind == BlockSymbolKind.MODE_PARAMETER:
        expression = block.mode_dict.get(variable, None)
    else:
        pass
    if isinstance(expression, Const):
        return str(expression.value)
    else:
        return "0.0"


def get_ordered_block_symbols(block: Block) -> List[Var]:
    """Return each directly owned or initialized symbol once in semantic order.

    External initialization mappings may legitimately retain a variable that
    is not an input, equation unknown, or output. Including those identities is
    essential: otherwise the dialogue could hide a power-flow dependency that
    will still be consumed by runtime initialization.

    :param block: Direct block whose symbols are requested.
    :return: Stable list containing every visible or mapped identity.
    """
    result: List[Var] = list()
    groups: tuple[Sequence[Var], ...] = (
        block.in_vars,
        block.algebraic_vars,
        block.state_vars,
        block.diff_vars,
        tuple(block.parameters.keys()),
        tuple(block.event_dict.keys()),
        tuple(block.mode_dict.keys()),
        block.out_vars,
    )
    group: Sequence[Var]
    variable: Var
    for group in groups:
        for variable in group:
            if variable not in result:
                result.append(variable)
            else:
                pass

    mapped_variable: Var | None
    for mapped_variable in block.external_mapping.values():
        if isinstance(mapped_variable, Var) and mapped_variable not in result:
            result.append(mapped_variable)
        else:
            pass

    mapped_parameter: Var
    for mapped_parameter in block.api_obj_mapping.values():
        if mapped_parameter not in result:
            result.append(mapped_parameter)
        else:
            pass
    return result


def get_variable_external_reference(block: Block,
                                    variable: Var) -> VarPowerFlowReferenceType | None:
    """Return the power-flow initialization key mapped to one variable.

    :param block: Direct symbol owner.
    :param variable: Variable whose mapping is requested.
    :return: Matching initialization key or ``None``.
    """
    result: VarPowerFlowReferenceType | None = None
    reference: VarPowerFlowReferenceType
    mapped_variable: Var | None
    for reference, mapped_variable in block.external_mapping.items():
        if mapped_variable is variable and result is None:
            result = reference
        else:
            pass
    return result


def get_variable_static_reference(block: Block,
                                  variable: Var) -> ParamPowerFlowReferenceType | None:
    """Return the device static-parameter key mapped to one variable.

    :param block: Direct symbol owner.
    :param variable: Parameter variable whose mapping is requested.
    :return: Matching static key or ``None``.
    """
    result: ParamPowerFlowReferenceType | None = None
    reference: ParamPowerFlowReferenceType
    mapped_variable: Var
    for reference, mapped_variable in block.api_obj_mapping.items():
        if mapped_variable is variable and result is None:
            result = reference
        else:
            pass
    return result


class BlockSymbolDraftModel(QtCore.QAbstractTableModel):
    """Editable staged table of recursive variables and parameters."""

    __slots__ = ("_rows", "_removed_rows")

    def __init__(self, block: Block, parent: QtCore.QObject | None = None) -> None:
        """
        Capture all directly owned symbols across the selected block tree.

        :param block: Symbolic block used by the operation.
        :param parent: Owning Qt widget.
        :return: None.
        """
        super().__init__(parent)
        self._rows: List[BlockSymbolDraftRow] = list()
        self._removed_rows: List[BlockSymbolDraftRow] = list()
        self._append_block_rows(block)

    def _append_block_rows(self, block: Block) -> None:
        """Append authoritative symbol rows from one recursive block tree.

        :param block: Root block whose current symbols must populate the draft.
        :return: None.
        """
        owner: Block
        for owner in block.get_all_blocks():
            variable: Var
            for variable in get_ordered_block_symbols(owner):
                kind: BlockSymbolKind = get_symbol_kind(owner, variable)
                value_text: str = get_symbol_value_text(owner, variable, kind)
                external_reference: VarPowerFlowReferenceType | None = get_variable_external_reference(
                    owner,
                    variable,
                )
                static_reference: ParamPowerFlowReferenceType | None = get_variable_static_reference(
                    owner,
                    variable,
                )
                self._rows.append(
                    BlockSymbolDraftRow(
                        owner,
                        variable,
                        variable.name,
                        kind,
                        variable in owner.out_vars,
                        value_text,
                        external_reference,
                        static_reference,
                    )
                )

    def reload(self, block: Block) -> None:
        """Replace staged rows with identities currently owned by the block.

        Applying a newly staged symbol creates its authoritative ``Var``. The
        table must bind to that identity immediately; otherwise a later Delete
        in the same open dialogue would discard only the stale temporary row.

        :param block: Root block whose applied symbols must be reloaded.
        :return: None.
        """
        self.beginResetModel()
        self._rows.clear()
        self._removed_rows.clear()
        self._append_block_rows(block)
        self.endResetModel()

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return the number of recursive symbol rows.

        :param parent: Owning Qt widget.
        :return: The number of recursive symbol rows.
        """
        if parent.isValid():
            return 0
        else:
            return len(self._rows)

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return owner, name, type, output, and initialization mapping columns.

        :param parent: Owning Qt widget.
        :return: Owner, name, type, output, and initialization mapping columns.
        """
        if parent.isValid():
            return 0
        else:
            return 5

    def get_row(self, row_index: int) -> BlockSymbolDraftRow | None:
        """Return one source row for proxy filtering and selection mapping.

        :param row_index: Source-model row index.
        :return: Symbol draft row or ``None`` when outside the model.
        """
        if 0 <= row_index < len(self._rows):
            return self._rows[row_index]
        else:
            return None

    def data(self, index: QtCore.QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        """
        :param index: Value supplied for ``index``.
        :param role: Value supplied for ``role``.
        :return: Staged symbol data and checkbox state.
        """
        if not index.isValid() or index.row() >= len(self._rows):
            return None
        else:
            row: BlockSymbolDraftRow = self._rows[index.row()]
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            if index.column() == 0:
                return row.get_owner().name
            elif index.column() == 1:
                return row.get_name()
            elif index.column() == 2:
                return row.get_kind().value
            elif index.column() == 4:
                external_reference: VarPowerFlowReferenceType | None = row.get_external_reference()
                static_reference: ParamPowerFlowReferenceType | None = row.get_static_reference()
                if external_reference is not None:
                    return f"VarPowerFlowReferenceType.{external_reference.name}"
                elif static_reference is not None:
                    return f"ParamPowerFlowReferenceType.{static_reference.name}"
                else:
                    return ""
            else:
                return None
        elif role == Qt.ItemDataRole.CheckStateRole and index.column() == 3 and row.kind_supports_export():
            if row.is_exported():
                return Qt.CheckState.Checked
            else:
                return Qt.CheckState.Unchecked
        else:
            return None

    def setData(self,
                index: QtCore.QModelIndex,
                value: object,
                role: int = Qt.ItemDataRole.EditRole) -> bool:
        """Update a staged symbol field without mutating the symbolic block.

        :param index: Source-model cell being edited.
        :param value: New edit or checkbox value supplied by Qt.
        :param role: Qt data role describing the edit operation.
        :return: Whether the staged value was accepted.
        """
        if not index.isValid() or index.row() >= len(self._rows):
            return False
        else:
            row: BlockSymbolDraftRow = self._rows[index.row()]
        if (
            role == Qt.ItemDataRole.CheckStateRole
            and index.column() == 3
            and row.kind_supports_export()
        ):
            # Output exposure is independent from the primary DAE role. Existing
            # algebraic/state variables therefore need the same staged checkbox
            # behavior as newly declared symbols.
            row.set_exported(value == Qt.CheckState.Checked.value or value == Qt.CheckState.Checked)
            self.dataChanged.emit(index, index, list((role,)))
            return True
        elif role == Qt.ItemDataRole.EditRole and index.column() == 1 and row.is_new():
            row.set_name(str(value).strip())
            self.dataChanged.emit(index, index, list((role,)))
            return True
        elif role == Qt.ItemDataRole.EditRole and index.column() == 2 and row.is_new():
            selected_kind: BlockSymbolKind | None = get_block_symbol_kind_from_text(str(value))
            if selected_kind is not None:
                row.set_kind(selected_kind)
                if not row.kind_supports_export():
                    row.set_exported(False)
                else:
                    pass
                self.dataChanged.emit(self.index(index.row(), 2), self.index(index.row(), 3))
                return True
            else:
                return False
        elif role == Qt.ItemDataRole.EditRole and index.column() == 4:
            return self._set_mapping_text(index, row, str(value))
        else:
            return False

    def _set_mapping_text(self,
                          index: QtCore.QModelIndex,
                          row: BlockSymbolDraftRow,
                          mapping_text: str) -> bool:
        """Parse one typed mapping label selected by the table delegate.

        :param index: Edited mapping cell.
        :param row: Symbol draft row receiving the mapping.
        :param mapping_text: Delegate display text.
        :return: Whether the mapping text was accepted.
        """
        normalized: str = mapping_text.strip()
        accepted: bool = False
        if normalized == "None" or len(normalized) == 0:
            row.set_external_reference(None)
            row.set_static_reference(None)
            accepted = True
        elif normalized.startswith("VarPowerFlowReferenceType.") and row.supports_external_reference():
            reference_name: str = normalized.removeprefix("VarPowerFlowReferenceType.")
            if reference_name in VarPowerFlowReferenceType.__members__:
                row.set_external_reference(VarPowerFlowReferenceType[reference_name])
                accepted = True
            else:
                pass
        elif normalized.startswith("ParamPowerFlowReferenceType.") and row.supports_static_reference():
            static_name: str = normalized.removeprefix("ParamPowerFlowReferenceType.")
            if static_name in ParamPowerFlowReferenceType.__members__:
                row.set_static_reference(ParamPowerFlowReferenceType[static_name])
                accepted = True
            else:
                pass
        else:
            pass
        if accepted:
            self.dataChanged.emit(index, index, list((Qt.ItemDataRole.EditRole, Qt.ItemDataRole.DisplayRole,)))
        else:
            pass
        return accepted

    def flags(self, index: QtCore.QModelIndex) -> Qt.ItemFlag:
        """Expose only semantically valid edits for each symbol column.

        :param index: Source-model cell queried by the view.
        :return: Qt item flags permitted for the staged symbol cell.
        """
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        else:
            row: BlockSymbolDraftRow = self._rows[index.row()]
            flags: Qt.ItemFlag = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column() == 1 and row.is_new():
            flags |= Qt.ItemFlag.ItemIsEditable
        elif index.column() == 2 and row.is_new():
            flags |= Qt.ItemFlag.ItemIsEditable
        elif index.column() == 3 and row.kind_supports_export():
            # Applying the checkbox later preserves transactional dialog behavior:
            # cancelling the modal still leaves the source block untouched.
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        elif index.column() == 4 and (
                row.supports_external_reference() or row.supports_static_reference()):
            flags |= Qt.ItemFlag.ItemIsEditable
        else:
            pass
        return flags

    def headerData(self,
                   section: int,
                   orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole) -> object:
        """
        Return symbol table headers.

        :param section: Value supplied for ``section``.
        :param orientation: Value supplied for ``orientation``.
        :param role: Value supplied for ``role``.
        :return: Symbol table headers.
        """
        headers: tuple[str, ...] = (
            "Block",
            "Name",
            "Type",
            "Output",
            "Mapping",
        )
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(headers):
                return self.tr(headers[section])
            else:
                return None
        else:
            return None

    def add_symbol(self,
                   owner: Block,
                   name: str,
                   kind: BlockSymbolKind,
                   exported: bool,
                   value: float,
                   create_derivative: bool = False,
                   external_reference: VarPowerFlowReferenceType | None = None,
                   static_reference: ParamPowerFlowReferenceType | None = None) -> None:
        """Append a detached new symbol and its requested derivative row.

        :param owner: Concrete block that will own the new symbol after Apply.
        :param name: Valid symbolic name.
        :param kind: Primary DAE role.
        :param exported: Independent output-port role.
        :param value: Initial value for parameter-like roles.
        :param create_derivative: Whether a state also stages ``d_<name>``.
        :param external_reference: Optional variable power-flow mapping.
        :param static_reference: Optional static-device parameter mapping.
        :return: None.
        """
        insertion_row: int = len(self._rows)
        stages_derivative: bool = kind == BlockSymbolKind.STATE and create_derivative
        if stages_derivative:
            final_insertion_row: int = insertion_row + 1
        else:
            final_insertion_row = insertion_row
        self.beginInsertRows(QtCore.QModelIndex(), insertion_row, final_insertion_row)
        state_row: BlockSymbolDraftRow = BlockSymbolDraftRow(
            owner,
            None,
            name,
            kind,
            exported,
            str(value),
            external_reference,
            static_reference,
        )
        self._rows.append(state_row)
        if stages_derivative:
            # A derivative is a first-class block variable. Staging it as its
            # own row makes the pending model structure visible before Apply,
            # while retaining the state identity required by ``base_var``.
            self._rows.append(
                BlockSymbolDraftRow(
                    owner,
                    None,
                    state_row.get_derivative_name(),
                    BlockSymbolKind.DIFFERENTIAL,
                    False,
                    "0.0",
                    None,
                    None,
                    state_row,
                )
            )
        else:
            pass
        self.endInsertRows()

    def remove_new_symbol(self, row_index: int) -> bool:
        """
        Remove a staged addition while protecting existing symbolic identities.

        :param row_index: Value supplied for ``row_index``.
        :return: True when the staged symbol was removed; otherwise False.
        """
        if 0 <= row_index < len(self._rows) and self._rows[row_index].is_new():
            self.beginRemoveRows(QtCore.QModelIndex(), row_index, row_index)
            del self._rows[row_index]
            self.endRemoveRows()
            return True
        else:
            return False

    def remove_symbol(self, row_index: int) -> bool:
        """Stage deletion of one symbol and any derivative owned by a state.

        Existing objects remain untouched until Apply. Validation immediately
        excludes deleted names so dependent equations must be corrected first.
        State deletion is directional: associated differential rows are also
        removed, while deleting a differential row never removes its base state.

        :param row_index: Source-model row selected through a proxy table.
        :return: Whether the selected row was staged for deletion.
        """
        if 0 <= row_index < len(self._rows):
            selected_row: BlockSymbolDraftRow = self._rows[row_index]
            removal_indexes: List[int] = list((row_index,))
            if selected_row.get_kind() == BlockSymbolKind.STATE:
                selected_variable: Var | None = selected_row.get_variable()
                candidate_index: int
                candidate_row: BlockSymbolDraftRow
                for candidate_index, candidate_row in enumerate(self._rows):
                    if (candidate_index != row_index
                            and candidate_row.get_owner() is selected_row.get_owner()
                            and candidate_row.get_kind() == BlockSymbolKind.DIFFERENTIAL):
                        staged_base_matches: bool = (
                            candidate_row.get_derivative_base_row() is selected_row
                        )
                        candidate_variable: Var | None = candidate_row.get_variable()
                        if candidate_variable is not None:
                            candidate_base_variable: Var | None = candidate_variable.base_var
                        else:
                            candidate_base_variable = None
                        if selected_variable is not None and candidate_base_variable is not None:
                            existing_base_matches: bool = (
                                candidate_base_variable.non_mutable_uid
                                == selected_variable.non_mutable_uid
                            )
                        else:
                            existing_base_matches = False
                        if staged_base_matches or existing_base_matches:
                            removal_indexes.append(candidate_index)
                        else:
                            pass
                    else:
                        pass
            else:
                pass

            # Remove from the end so every source-model row index remains valid
            # while Qt receives one precise removal notification per row.
            removal_indexes.sort(reverse=True)
            removal_index: int
            for removal_index in removal_indexes:
                self.beginRemoveRows(QtCore.QModelIndex(), removal_index, removal_index)
                removed_row: BlockSymbolDraftRow = self._rows.pop(removal_index)
                if not removed_row.is_new():
                    self._removed_rows.append(removed_row)
                else:
                    pass
                self.endRemoveRows()
            return True
        else:
            return False

    def build_validation_namespace(self, base_namespace: Mapping[str, Expr]) -> Dict[str, Expr]:
        """
        Build a namespace that includes temporary identities for staged additions.

        :param base_namespace: Value supplied for ``base_namespace``.
        :return: Validation namespace including temporary identities for staged additions.
        """
        namespace: Dict[str, Expr] = dict(base_namespace)
        removed_row: BlockSymbolDraftRow
        for removed_row in self._removed_rows:
            namespace.pop(removed_row.get_name(), None)
        names_seen: set[str] = set(namespace.keys())
        row: BlockSymbolDraftRow
        for row in self._rows:
            name: str = row.get_name()
            if len(name) == 0 or not name.isidentifier():
                raise ValueError(f"Invalid symbol name '{name}'")
            elif row.is_new() and name in names_seen:
                raise ValueError(f"Symbol '{name}' already exists")
            else:
                pass
            if row.is_new():
                namespace[name] = Var(name)
                names_seen.add(name)
            else:
                pass
            if row.is_new() and row.kind_supports_value():
                row.parse_value()
            else:
                pass
        self._validate_unique_mappings()
        return namespace

    def _validate_unique_mappings(self) -> None:
        """
        Reject duplicate initialization/static keys inside one owner block.

        :return: None.
        """
        external_owners: set[tuple[int, VarPowerFlowReferenceType]] = set()
        static_owners: set[tuple[int, ParamPowerFlowReferenceType]] = set()
        row: BlockSymbolDraftRow
        for row in self._rows:
            external_reference: VarPowerFlowReferenceType | None = row.get_external_reference()
            static_reference: ParamPowerFlowReferenceType | None = row.get_static_reference()
            if external_reference is not None:
                external_key: tuple[int, VarPowerFlowReferenceType] = (
                    row.get_owner().uid,
                    external_reference,
                )
                if external_key in external_owners:
                    raise ValueError(
                        f"Power-flow mapping '{external_reference.name}' is assigned more than once "
                        f"in block '{row.get_owner().name}'"
                    )
                else:
                    external_owners.add(external_key)
            else:
                pass
            if static_reference is not None:
                static_key: tuple[int, ParamPowerFlowReferenceType] = (
                    row.get_owner().uid,
                    static_reference,
                )
                if static_key in static_owners:
                    raise ValueError(
                        f"Device static mapping '{static_reference.name}' is assigned more than once "
                        f"in block '{row.get_owner().name}'"
                    )
                else:
                    static_owners.add(static_key)
            else:
                pass

    def apply_to_blocks(self, var_factory: VarFactory) -> None:
        """
        Apply staged roles and create requested variables after validation.

        :param var_factory: Factory that owns symbolic variables.
        :return: None.
        """
        removed_row: BlockSymbolDraftRow
        for removed_row in self._removed_rows:
            removed_variable: Var | None = removed_row.get_variable()
            if removed_variable is not None:
                remove_block_symbol(removed_row.get_owner(), removed_variable)
            else:
                pass

        row: BlockSymbolDraftRow
        for row in self._rows:
            variable: Var | None = row.get_variable()
            if variable is None:
                if row.get_kind() == BlockSymbolKind.DIFFERENTIAL:
                    derivative_base_row: BlockSymbolDraftRow | None = row.get_derivative_base_row()
                    if derivative_base_row is not None:
                        derivative_base_variable: Var | None = derivative_base_row.get_variable()
                    else:
                        derivative_base_variable = None
                    variable = var_factory.add_diff_var(
                        name=row.get_name(),
                        base_var=derivative_base_variable,
                    )
                else:
                    variable = var_factory.add_var(name=row.get_name())
                # Later staged rows may depend on this exact identity. Bind it
                # before continuing so a derivative can preserve ``base_var``.
                row.set_variable(variable)
                reclassify_block_symbol(
                    row.get_owner(), variable, row.get_kind(), row.parse_value(), var_factory
                )
            else:
                if row.get_kind() != row.get_original_kind():
                    reclassify_block_symbol(
                        row.get_owner(), variable, row.get_kind(), row.parse_value(), var_factory
                    )
                else:
                    pass
            if row.is_exported() and variable not in row.get_owner().out_vars:
                row.get_owner().out_vars.append(variable)
            elif not row.is_exported() and variable in row.get_owner().out_vars:
                row.get_owner().out_vars.remove(variable)
            else:
                pass
            apply_symbol_mapping(row.get_owner(), variable, row)

    def has_new_symbols(self) -> bool:
        """
        Return whether the draft contains unapplied symbol additions.

        :return: Whether the draft contains unapplied symbol additions.
        """
        result: bool = False
        row: BlockSymbolDraftRow
        for row in self._rows:
            if row.is_new():
                result = True
            else:
                pass
        return result

    def has_symbol_changes(self) -> bool:
        """
        Return whether additions or deletions are staged in the table.

        :return: Whether additions or deletions are staged in the table.
        """
        if len(self._removed_rows) > 0:
            result: bool = True
        else:
            result = self.has_new_symbols()
        return result

    def get_output_export_changes(self) -> List[tuple[Block, Var, bool]]:
        """Return staged output-role changes for existing variables.

        The owning graphics editor consumes removals before ``out_vars`` is
        mutated so it can unregister any wires through their still-valid ports.

        :return: Owner, existing variable, and requested output state tuples.
        """
        changes: List[tuple[Block, Var, bool]] = list()
        row: BlockSymbolDraftRow
        for row in self._rows:
            variable: Var | None = row.get_variable()
            if variable is not None:
                currently_exported: bool = variable in row.get_owner().out_vars
                if currently_exported != row.is_exported():
                    changes.append((row.get_owner(), variable, row.is_exported()))
                else:
                    pass
            else:
                pass
        removed_row: BlockSymbolDraftRow
        for removed_row in self._removed_rows:
            removed_variable: Var | None = removed_row.get_variable()
            if removed_variable is not None and removed_variable in removed_row.get_owner().out_vars:
                changes.append((removed_row.get_owner(), removed_variable, False))
            else:
                pass
        return changes

    def get_role_count(self, owner: Block, kind: BlockSymbolKind) -> int:
        """Return the staged number of symbols with one primary DAE role.

        :param owner: Block whose staged rows are counted.
        :param kind: Primary symbol role to count.
        :return: Number of matching staged symbols.
        """
        result: int = 0
        row: BlockSymbolDraftRow
        for row in self._rows:
            if row.get_owner() is owner and row.get_kind() == kind:
                result += 1
            else:
                pass
        return result

    def get_role_names(self, owner: Block, kind: BlockSymbolKind) -> List[str]:
        """Return staged symbol names in their authoritative table order.

        :param owner: Block whose staged symbols are requested.
        :param kind: Primary DAE role to collect.
        :return: Ordered staged names for the selected role.
        """
        result: List[str] = list()
        row: BlockSymbolDraftRow
        for row in self._rows:
            if row.get_owner() is owner and row.get_kind() == kind:
                result.append(row.get_name())
            else:
                pass
        return result

    def refresh_existing_names(self) -> None:
        """Refresh detached row labels after an editor-owned variable rename.

        Existing rows retain their staged role, mapping, and output changes. Only
        their displayed names follow the authoritative ``Var`` objects changed by
        the central editor rename operation.

        :return: None.
        """
        self.beginResetModel()
        row: BlockSymbolDraftRow
        for row in self._rows:
            variable: Var | None = row.get_variable()
            if variable is not None:
                row.set_name(variable.name)
            else:
                pass
        self.endResetModel()


def get_block_symbol_kind_from_text(text: str) -> BlockSymbolKind | None:
    """
    Resolve a displayed role label to its enum member.

    :param text: User-entered text.
    :return: Enum member matching the displayed role label, or ``None`` when unmatched.
    """
    kind: BlockSymbolKind
    for kind in BlockSymbolKind:
        if kind.value == text:
            return kind
        else:
            pass
    return None


def apply_symbol_mapping(block: Block,
                         variable: Var,
                         row: BlockSymbolDraftRow) -> None:
    """Replace external/static mappings for one staged symbol row.

    :param block: Direct owner of the symbol and mapping dictionaries.
    :param variable: Applied authoritative variable identity.
    :param row: Draft containing the requested typed mappings.
    :return: None.
    """
    external_keys_to_remove: List[VarPowerFlowReferenceType] = list()
    external_key: VarPowerFlowReferenceType
    mapped_external_variable: Var | None
    for external_key, mapped_external_variable in block.external_mapping.items():
        if mapped_external_variable is variable:
            external_keys_to_remove.append(external_key)
        else:
            pass
    for external_key in external_keys_to_remove:
        del block.external_mapping[external_key]

    static_keys_to_remove: List[ParamPowerFlowReferenceType] = list()
    static_key: ParamPowerFlowReferenceType
    mapped_static_variable: Var
    for static_key, mapped_static_variable in block.api_obj_mapping.items():
        if mapped_static_variable is variable:
            static_keys_to_remove.append(static_key)
        else:
            pass
    for static_key in static_keys_to_remove:
        del block.api_obj_mapping[static_key]

    external_reference: VarPowerFlowReferenceType | None = row.get_external_reference()
    static_reference: ParamPowerFlowReferenceType | None = row.get_static_reference()
    if external_reference is not None:
        block.external_mapping[external_reference] = variable
    else:
        pass
    if static_reference is not None and row.get_kind() == BlockSymbolKind.PARAMETER:
        block.api_obj_mapping[static_reference] = variable
    else:
        pass


def remove_block_symbol(block: Block, variable: Var) -> None:
    """Remove one symbol identity from every direct ownership collection.

    Equation text is validated before this mutation, so no applied expression
    can still reference the deleted identity. Device mappings are also removed
    to avoid leaving an invisible static or power-flow parameter binding.

    :param block: Direct owner of the symbol.
    :param variable: Existing symbolic identity staged for deletion.
    :return: None.
    """
    sequence_groups: tuple[List[Var], ...] = (
        block.in_vars,
        block.algebraic_vars,
        block.state_vars,
        block.diff_vars,
        block.reformulated_vars,
        block.out_vars,
    )
    sequence: List[Var]
    for sequence in sequence_groups:
        if variable in sequence:
            sequence.remove(variable)
        else:
            pass

    mapping_groups: tuple[dict, ...] = (
        block.parameters,
        block.event_dict,
        block.mode_dict,
        block.init_values,
        block.init_eqs,
        block.diff_init_eqs,
        block.discrete_eqs,
        block.boolean_guards,
    )
    mapping: dict
    for mapping in mapping_groups:
        mapping.pop(variable, None)

    external_key: object
    external_keys_to_remove: List[object] = list()
    for external_key, mapped_variable in block.external_mapping.items():
        if mapped_variable is variable:
            external_keys_to_remove.append(external_key)
        else:
            pass
    for external_key in external_keys_to_remove:
        del block.external_mapping[external_key]

    parameter_key: ParamPowerFlowReferenceType
    parameter_keys_to_remove: List[ParamPowerFlowReferenceType] = list()
    for parameter_key, mapped_parameter in block.api_obj_mapping.items():
        if mapped_parameter is variable:
            parameter_keys_to_remove.append(parameter_key)
        else:
            pass
    for parameter_key in parameter_keys_to_remove:
        del block.api_obj_mapping[parameter_key]


def reclassify_block_symbol(block: Block,
                            variable: Var,
                            kind: BlockSymbolKind,
                            numeric_value: float,
                            var_factory: VarFactory) -> None:
    """
    Move one existing identity to exactly one primary block role.

    :param block: Symbolic block used by the operation.
    :param variable: Symbolic variable used by the operation.
    :param kind: Value supplied for ``kind``.
    :param numeric_value: Value supplied for ``numeric_value``.
    :param var_factory: Factory that owns symbolic variables.
    :return: None.
    """
    previous_constant: Const | None = None
    parameter_expression: Expr | None = block.parameters.get(variable, None)
    event_expression: Expr | None = block.event_dict.get(variable, None)
    mode_expression: Expr | None = block.mode_dict.get(variable, None)
    if isinstance(parameter_expression, Const):
        previous_constant = parameter_expression
    elif isinstance(event_expression, Const):
        previous_constant = event_expression
    elif isinstance(mode_expression, Const):
        previous_constant = mode_expression
    else:
        pass
    sequence_groups: tuple[List[Var], ...] = (block.in_vars, block.algebraic_vars, block.state_vars, block.diff_vars)
    sequence: List[Var]
    for sequence in sequence_groups:
        if variable in sequence:
            sequence.remove(variable)
        else:
            pass
    if variable in block.parameters:
        del block.parameters[variable]
    else:
        pass
    if variable in block.event_dict:
        del block.event_dict[variable]
    else:
        pass
    if variable in block.mode_dict:
        del block.mode_dict[variable]
    else:
        pass

    if kind == BlockSymbolKind.INPUT:
        block.in_vars.append(variable)
    elif kind == BlockSymbolKind.ALGEBRAIC:
        block.algebraic_vars.append(variable)
    elif kind == BlockSymbolKind.STATE:
        block.state_vars.append(variable)
    elif kind == BlockSymbolKind.DIFFERENTIAL:
        block.diff_vars.append(variable)
    elif kind == BlockSymbolKind.PARAMETER:
        block.parameters[variable] = build_reclassified_constant(
            previous_constant, numeric_value, variable.name, var_factory
        )
    elif kind == BlockSymbolKind.EVENT_PARAMETER:
        block.event_dict[variable] = build_reclassified_constant(
            previous_constant, numeric_value, variable.name, var_factory
        )
    elif kind == BlockSymbolKind.MODE_PARAMETER:
        block.mode_dict[variable] = build_reclassified_constant(
            previous_constant, numeric_value, variable.name, var_factory
        )
    elif kind == BlockSymbolKind.OUTPUT_ONLY:
        pass
    else:
        pass


def build_reclassified_constant(previous_constant: Const | None,
                                numeric_value: float,
                                name: str,
                                var_factory: VarFactory) -> Const:
    """
    Reuse an existing Const identity or register a new one in VarFactory.

    :param previous_constant: Value supplied for ``previous_constant``.
    :param numeric_value: Value supplied for ``numeric_value``.
    :param name: Value supplied for ``name``.
    :param var_factory: Factory that owns symbolic variables.
    :return: Existing constant identity, or the newly registered replacement constant.
    """
    if previous_constant is not None:
        previous_constant.value = numeric_value
        return previous_constant
    else:
        return var_factory.add_const(value=numeric_value, name=name)


class SymbolKindDelegate(QtWidgets.QStyledItemDelegate):
    """Combo-box delegate for the finite set of symbol primary roles."""

    __slots__ = ()

    def createEditor(self,
                     parent: QtWidgets.QWidget,
                     option: QtWidgets.QStyleOptionViewItem,
                     index: QtCore.QModelIndex) -> QtWidgets.QWidget:
        """
        Create a role combo box for one symbol row.

        :param parent: Owning Qt widget.
        :param option: Value supplied for ``option``.
        :param index: Value supplied for ``index``.
        :return: Role combo-box editor for the requested symbol row.
        """
        _unused_option: QtWidgets.QStyleOptionViewItem = option
        _unused_index: QtCore.QModelIndex = index
        combo: QtWidgets.QComboBox = QtWidgets.QComboBox(parent)
        kind: BlockSymbolKind
        for kind in BlockSymbolKind:
            combo.addItem(kind.value)
        return combo

    def setEditorData(self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex) -> None:
        """
        Select the row's current role in the combo editor.

        :param editor: Value supplied for ``editor``.
        :param index: Value supplied for ``index``.
        :return: None.
        """
        if isinstance(editor, QtWidgets.QComboBox):
            current_text: str = str(index.data(Qt.ItemDataRole.EditRole))
            editor.setCurrentText(current_text)
        else:
            pass

    def setModelData(self,
                     editor: QtWidgets.QWidget,
                     model: QtCore.QAbstractItemModel,
                     index: QtCore.QModelIndex) -> None:
        """
        Commit the selected enum label to the draft model.

        :param editor: Value supplied for ``editor``.
        :param model: Value supplied for ``model``.
        :param index: Value supplied for ``index``.
        :return: None.
        """
        if isinstance(editor, QtWidgets.QComboBox):
            model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)
        else:
            pass


class SymbolMappingDelegate(QtWidgets.QStyledItemDelegate):
    """Typed combo delegate for power-flow and device-static mappings."""

    __slots__ = ()

    def createEditor(self,
                     parent: QtWidgets.QWidget,
                     option: QtWidgets.QStyleOptionViewItem,
                     index: QtCore.QModelIndex) -> QtWidgets.QWidget:
        """Create a mapping combo appropriate for the source symbol kind.

        :param parent: Owning table viewport.
        :param option: Qt style information.
        :param index: Proxy-model mapping cell.
        :return: Typed mapping combo.
        """
        _unused_option: QtWidgets.QStyleOptionViewItem = option
        combo: QtWidgets.QComboBox = QtWidgets.QComboBox(parent)
        combo.setEditable(True)
        combo.addItem("None")
        proxy_model: QtCore.QAbstractItemModel | None = index.model()
        row: BlockSymbolDraftRow | None = None
        if isinstance(proxy_model, BlockSymbolFilterProxyModel):
            source_index: QtCore.QModelIndex = proxy_model.mapToSource(index)
            source_model: QtCore.QAbstractItemModel | None = proxy_model.sourceModel()
            if isinstance(source_model, BlockSymbolDraftModel):
                row = source_model.get_row(source_index.row())
            else:
                pass
        else:
            pass

        if row is not None and row.supports_external_reference():
            external_reference: VarPowerFlowReferenceType
            for external_reference in VarPowerFlowReferenceType:
                combo.addItem(f"VarPowerFlowReferenceType.{external_reference.name}")
        elif row is not None and row.supports_static_reference():
            static_reference: ParamPowerFlowReferenceType
            for static_reference in ParamPowerFlowReferenceType:
                combo.addItem(f"ParamPowerFlowReferenceType.{static_reference.name}")
        else:
            pass
        return combo

    def setEditorData(self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex) -> None:
        """Select the currently staged mapping label.

        :param editor: Mapping combo created for the cell.
        :param index: Edited proxy-model index.
        :return: None.
        """
        if isinstance(editor, QtWidgets.QComboBox):
            current_text: str = str(index.data(Qt.ItemDataRole.EditRole))
            if len(current_text) == 0:
                editor.setCurrentText("None")
            else:
                editor.setCurrentText(current_text)
        else:
            pass

    def setModelData(self,
                     editor: QtWidgets.QWidget,
                     model: QtCore.QAbstractItemModel,
                     index: QtCore.QModelIndex) -> None:
        """Commit one selected typed mapping to the proxy model.

        :param editor: Active mapping combo.
        :param model: Variable or parameter proxy model.
        :param index: Edited mapping cell.
        :return: None.
        """
        if isinstance(editor, QtWidgets.QComboBox):
            model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)
        else:
            pass


class BlockParameterDraftModel(QtCore.QAbstractTableModel):
    """Table model that stages numeric parameter changes until Apply."""

    __slots__ = ("_rows",)

    def __init__(self, block: Block, parent: QtCore.QObject | None = None) -> None:
        """
        Build staged rows recursively from fixed, event, and mode constants.

        :param block: Symbolic block used by the operation.
        :param parent: Owning Qt widget.
        :return: None.
        """
        super().__init__(parent)
        self._rows: List[ParameterDraftRow] = list()
        self._load_rows(block)

    def _load_rows(self, block: Block) -> None:
        """Load every editable numeric constant from a recursive block tree.

        :param block: Root block whose parameter tree is displayed.
        :return: None.
        """
        child_block: Block
        for child_block in block.get_all_blocks():
            owner_label: str = child_block.name if child_block is not block else block.name
            self._append_constant_rows(f"Parameter - {owner_label}", child_block.parameters)
            self._append_constant_rows(f"Dynamic parameter - {owner_label}", child_block.event_dict)
            # Retained modes may have symbolic initialization expressions and
            # execution dependencies. They are edited in Runtime logic, where
            # their writers and readers can be validated as one transaction.

    def reload(self, block: Block) -> None:
        """Refresh rows after staged parameter symbols become real constants.

        :param block: Updated root block.
        :return: None.
        """
        self.beginResetModel()
        self._rows.clear()
        self._load_rows(block)
        self.endResetModel()

    def _append_constant_rows(self, category: str, values: Mapping[Var, Expr]) -> None:
        """Append numeric and explicitly unset constants from one block dictionary.

        :param category: User-facing constant category and owner label.
        :param values: Variable-to-expression dictionary owned by the block.
        :return: None.
        """
        variable: Var
        expression: Expr
        for variable, expression in values.items():
            if isinstance(expression, Const):
                self._rows.append(ParameterDraftRow(category, variable, expression))
            else:
                pass

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return the number of staged parameter rows.

        :param parent: Owning Qt widget.
        :return: The number of staged parameter rows.
        """
        if parent.isValid():
            return 0
        else:
            return len(self._rows)

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return the category, name, and value column count.

        :param parent: Owning Qt widget.
        :return: The category, name, and value column count.
        """
        if parent.isValid():
            return 0
        else:
            return 3

    def data(self, index: QtCore.QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        """
        Return one cell value or presentation role.

        :param index: Value supplied for ``index``.
        :param role: Value supplied for ``role``.
        :return: One cell value or presentation role.
        """
        if not index.isValid() or index.row() >= len(self._rows):
            return None
        else:
            row: ParameterDraftRow = self._rows[index.row()]

        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            if index.column() == 0:
                return row.get_category()
            elif index.column() == 1:
                return row.get_variable().name
            elif index.column() == 2:
                return row.get_draft_text()
            else:
                return None
        elif role == Qt.ItemDataRole.ToolTipRole and index.column() == 2:
            return self.tr("Numeric value. Changes are staged until Apply changes is pressed.")
        else:
            return None

    def setData(self,
                index: QtCore.QModelIndex,
                value: object,
                role: int = Qt.ItemDataRole.EditRole) -> bool:
        """
        Stage one edited numeric value as text.

        :param index: Value supplied for ``index``.
        :param value: Value supplied for ``value``.
        :param role: Value supplied for ``role``.
        :return: True when the edited value was accepted; otherwise False.
        """
        if not index.isValid() or index.column() != 2 or role != Qt.ItemDataRole.EditRole:
            return False
        else:
            row: ParameterDraftRow = self._rows[index.row()]
            row.set_draft_text(str(value))
            self.dataChanged.emit(index, index, list((role,)))
            return True

    def flags(self, index: QtCore.QModelIndex) -> Qt.ItemFlag:
        """
        Make only the value column editable.

        :param index: Value supplied for ``index``.
        :return: Item flags that make only the value column editable.
        """
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        else:
            result: Qt.ItemFlag = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
            if index.column() == 2:
                result |= Qt.ItemFlag.ItemIsEditable
            else:
                pass
            return result

    def headerData(self,
                   section: int,
                   orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole) -> object:
        """
        Return horizontal table headers.

        :param section: Value supplied for ``section``.
        :param orientation: Value supplied for ``orientation``.
        :param role: Value supplied for ``role``.
        :return: Horizontal table headers.
        """
        if role != Qt.ItemDataRole.DisplayRole or orientation != Qt.Orientation.Horizontal:
            return None
        elif section == 0:
            return self.tr("Type")
        elif section == 1:
            return self.tr("Name")
        elif section == 2:
            return self.tr("Value")
        else:
            return None

    def get_pending_values(self) -> List[tuple[Const, float | complex]]:
        """
        Validate and return all staged constant updates.

        :return: All staged constant updates.
        """
        result: List[tuple[Const, float | complex]] = list()
        row: ParameterDraftRow
        for row in self._rows:
            if row.is_unchanged_unset():
                # ``None`` means the value is supplied later by a mapping. It
                # remains visible in the table but does not become a fake zero.
                pass
            else:
                result.append((row.get_constant(), row.parse_value()))
        return result

    def get_pending_named_values(self) -> List[tuple[str, float | complex]]:
        """
        Validate and return staged constants by semantic variable name.

        :return: Staged constants by semantic variable name.
        """
        result: List[tuple[str, float | complex]] = list()
        row: ParameterDraftRow
        for row in self._rows:
            if row.is_unchanged_unset():
                pass
            else:
                result.append((row.get_variable().name, row.parse_value()))
        return result


class EquationLatexModel(QtCore.QAbstractTableModel):
    """Read-only table model used by the LaTeX preview."""

    __slots__ = ("_rows",)

    def __init__(self, draft: BlockEquationDraft, parent: QtCore.QObject | None = None) -> None:
        """
        Create preview rows from a validated equation draft.

        :param draft: Value supplied for ``draft``.
        :param parent: Owning Qt widget.
        :return: None.
        """
        super().__init__(parent)
        self._rows: List[tuple[str, str]] = list()
        self.set_draft(draft)

    def set_draft(self, draft: BlockEquationDraft) -> None:
        """
        Replace the equation preview atomically.

        :param draft: Value supplied for ``draft``.
        :return: None.
        """
        self.beginResetModel()
        self._rows.clear()
        self._append_list("State", draft.get_state_eqs())
        # Algebraic drafts already contain Engine residuals, so the preview
        # restores the complete mathematical equality expected by the GUI.
        algebraic_expression: Expr
        for algebraic_expression in draft.get_algebraic_eqs():
            algebraic_latex: str = get_safe_expression_latex(algebraic_expression)
            self._rows.append(("Algebraic", f"0 = {algebraic_latex}"))
        self._append_dict("Initialization", draft.get_init_eqs())
        self._append_dict("Derivative initialization", draft.get_diff_init_eqs())
        self.endResetModel()

    def _append_list(self, category: str, expressions: Sequence[Expr]) -> None:
        """
        Append a sequence to the preview.

        :param category: Value supplied for ``category``.
        :param expressions: Value supplied for ``expressions``.
        :return: None.
        """
        expression: Expr
        for expression in expressions:
            self._rows.append((category, get_safe_expression_latex(expression)))

    def _append_dict(self, category: str, expressions: Mapping[Var, Expr]) -> None:
        """
        Append assignment-like equations to the preview.

        :param category: Value supplied for ``category``.
        :param expressions: Value supplied for ``expressions``.
        :return: None.
        """
        variable: Var
        expression: Expr
        for variable, expression in expressions.items():
            assignment_latex: str = (
                f"{get_safe_expression_latex(variable)} = {get_safe_expression_latex(expression)}"
            )
            self._rows.append((category, assignment_latex))

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return preview equation count.

        :param parent: Owning Qt widget.
        :return: Preview equation count.
        """
        if parent.isValid():
            return 0
        else:
            return len(self._rows)

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return type and equation columns.

        :param parent: Owning Qt widget.
        :return: Type and equation columns.
        """
        if parent.isValid():
            return 0
        else:
            return 2

    def data(self, index: QtCore.QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        """
        Return the type label or rendered LaTeX source.

        :param index: Value supplied for ``index``.
        :param role: Value supplied for ``role``.
        :return: The type label or rendered LaTeX source.
        """
        if not index.isValid() or index.row() >= len(self._rows):
            return None
        else:
            row: tuple[str, str] = self._rows[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return row[0]
            elif index.column() == 1:
                return row[1]
            else:
                return None
        else:
            return None

    def headerData(self,
                   section: int,
                   orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole) -> object:
        """
        Return preview headers.

        :param section: Value supplied for ``section``.
        :param orientation: Value supplied for ``orientation``.
        :param role: Value supplied for ``role``.
        :return: Preview headers.
        """
        if role != Qt.ItemDataRole.DisplayRole or orientation != Qt.Orientation.Horizontal:
            return None
        elif section == 0:
            return self.tr("Type")
        elif section == 1:
            return self.tr("Equation")
        else:
            return None


def get_safe_expression_latex(expression: Expr) -> str:
    """Return LaTeX when supported and readable symbolic text otherwise.

    The equation editor must remain usable when a new symbolic node reaches
    the GUI before the LaTeX printer gains a specialized representation.

    :param expression: Symbolic expression to display.
    :return: LaTeX source or a lossless textual fallback.
    """
    try:
        return symbolic_to_latex(expression)
    except (NotImplementedError, RuntimeError, TypeError, ValueError):
        return symbolic_to_string(expression)


def configure_interactive_table_header(header: QtWidgets.QHeaderView,
                                       initial_widths: Sequence[int]) -> None:
    """Make every column divider user-resizable and set readable initial widths.

    :param header: Horizontal table or tree header being configured.
    :param initial_widths: Initial pixel width for each available column.
    :return: None.
    """
    # Interactive mode is required on every section: Stretch and
    # ResizeToContents silently lock their dividers after the initial layout.
    header.setStretchLastSection(False)
    column_index: int
    for column_index in range(header.count()):
        header.setSectionResizeMode(
            column_index,
            QtWidgets.QHeaderView.ResizeMode.Interactive,
        )
        if column_index < len(initial_widths):
            header.resizeSection(column_index, initial_widths[column_index])
        else:
            pass


class BlockCodeBuffer:
    """Detached equation source for one concrete block in a recursive tree."""

    __slots__ = ("_block", "_code", "_original_code")

    def __init__(self, block: Block) -> None:
        """
        Capture the initial equation source of one block.

        :param block: Symbolic block used by the operation.
        :return: None.
        """
        self._block: Block = block
        self._code: str = build_equation_code(block)
        self._original_code: str = self._code

    def get_block(self) -> Block:
        """
        Return the block that owns this source buffer.

        :return: The block that owns this source buffer.
        """
        return self._block

    def get_code(self) -> str:
        """
        Return the current detached source text.

        :return: The current detached source text.
        """
        return self._code

    def set_code(self, code: str) -> None:
        """
        Replace the detached source text.

        :param code: Value supplied for ``code``.
        :return: None.
        """
        self._code = code

    def has_changes(self) -> bool:
        """
        Return whether the user changed this equation buffer.

        :return: Whether the user changed this equation buffer.
        """
        return self._code != self._original_code


class DaeCodeHighlighter(QtGui.QSyntaxHighlighter):
    """Small Python-like syntax highlighter specialized for DAE assignments."""

    __slots__ = (
        "_keyword_format",
        "_number_format",
        "_string_format",
        "_comment_format",
        "_symbol_format",
        "_symbol_names",
    )

    def __init__(self, document: QtGui.QTextDocument, symbol_names: Sequence[str]) -> None:
        """
        Create highlighting formats for DAE sections and known symbols.

        :param document: Value supplied for ``document``.
        :param symbol_names: Value supplied for ``symbol_names``.
        :return: None.
        """
        super().__init__(document)
        self._keyword_format: QtGui.QTextCharFormat = QtGui.QTextCharFormat()
        self._keyword_format.setForeground(QtGui.QColor("#7c3aed"))
        self._keyword_format.setFontWeight(QtGui.QFont.Weight.Bold)
        self._number_format: QtGui.QTextCharFormat = QtGui.QTextCharFormat()
        self._number_format.setForeground(QtGui.QColor("#0369a1"))
        self._string_format: QtGui.QTextCharFormat = QtGui.QTextCharFormat()
        self._string_format.setForeground(QtGui.QColor("#15803d"))
        self._comment_format: QtGui.QTextCharFormat = QtGui.QTextCharFormat()
        self._comment_format.setForeground(QtGui.QColor("#64748b"))
        self._comment_format.setFontItalic(True)
        self._symbol_format: QtGui.QTextCharFormat = QtGui.QTextCharFormat()
        self._symbol_format.setForeground(QtGui.QColor("#b45309"))
        self._symbol_names: tuple[str, ...] = tuple(symbol_names)

    def set_symbol_names(self, symbol_names: Sequence[str]) -> None:
        """
        Replace known identifiers and rehighlight the complete document.

        :param symbol_names: Value supplied for ``symbol_names``.
        :return: None.
        """
        self._symbol_names = tuple(symbol_names)
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:
        """
        Apply deterministic formats to one visible source line.

        :param text: User-entered text.
        :return: None.
        """
        section_names: tuple[str, ...] = (
            "state_eqs",
            "algebraic_eqs",
            "init_eqs",
            "diff_init_eqs",
        )
        section_name: str
        for section_name in section_names:
            self._apply_pattern(text, rf"\b{re.escape(section_name)}\b", self._keyword_format)

        self._apply_pattern(text, r"\b(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?j?\b", self._number_format)
        self._apply_pattern(text, r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"", self._string_format)

        symbol_name: str
        for symbol_name in self._symbol_names:
            self._apply_pattern(text, rf"\b{re.escape(symbol_name)}\b", self._symbol_format)

        comment_index: int = text.find("#")
        if comment_index >= 0:
            self.setFormat(comment_index, len(text) - comment_index, self._comment_format)
        else:
            pass

    def _apply_pattern(self, text: str, pattern_text: str, text_format: QtGui.QTextCharFormat) -> None:
        """
        Apply one regular-expression format to all matches in a line.

        :param text: User-entered text.
        :param pattern_text: Value supplied for ``pattern_text``.
        :param text_format: Value supplied for ``text_format``.
        :return: None.
        """
        pattern: re.Pattern[str] = re.compile(pattern_text)
        match: re.Match[str]
        for match in pattern.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), text_format)


class DaeCodeDiagnostic:
    """One source-local validation error shown directly inside the DAE editor."""

    __slots__ = ("_line", "_column", "_length", "_message")

    def __init__(self, line: int, column: int, length: int, message: str) -> None:
        """Store a one-based line and zero-based source span.

        :param line: One-based source line.
        :param column: Zero-based source column.
        :param length: Highlighted source length.
        :param message: Explanation exposed as a tooltip.
        :return: None.
        """
        self._line: int = max(1, line)
        self._column: int = max(0, column)
        self._length: int = max(1, length)
        self._message: str = message

    def get_line(self) -> int:
        """
        :return: The one-based source line.
        """
        return self._line

    def get_column(self) -> int:
        """
        :return: The zero-based source column.
        """
        return self._column

    def get_length(self) -> int:
        """
        :return: The highlighted source length.
        """
        return self._length

    def get_message(self) -> str:
        """
        :return: The user-facing validation explanation.
        """
        return self._message


def find_text_diagnostic(code: str, token: str, message: str) -> DaeCodeDiagnostic:
    """Locate a semantic-error token in source and create one diagnostic.

    :param code: Complete DAE source.
    :param token: Identifier or section name associated with the error.
    :param message: Validation explanation.
    :return: Source-local diagnostic, falling back to the first line.
    """
    lines: List[str] = code.splitlines()
    line_index: int
    for line_index in range(len(lines)):
        column: int = lines[line_index].find(token)
        if column >= 0:
            return DaeCodeDiagnostic(line_index + 1, column, len(token), message)
        else:
            pass
    return DaeCodeDiagnostic(1, 0, 1, message)


def brackets_match(opening_bracket: str, closing_bracket: str) -> bool:
    """Return whether two Python punctuation tokens form one bracket pair.

    :param opening_bracket: Candidate opening token.
    :param closing_bracket: Candidate closing token.
    :return: ``True`` only for matching parentheses, brackets, or braces.
    """
    if opening_bracket == "(" and closing_bracket == ")":
        result: bool = True
    elif opening_bracket == "[" and closing_bracket == "]":
        result = True
    elif opening_bracket == "{" and closing_bracket == "}":
        result = True
    else:
        result = False
    return result


def normalize_algebraic_equality_syntax(code: str) -> str:
    """Translate visible algebraic ``=`` tokens into a parse-only marker.

    A single equality inside a Python list is not valid Python syntax. The DAE
    surface language nevertheless uses mathematical ``left = right`` equations.
    Tokenization identifies only equality signs inside ``algebraic_eqs`` and
    replaces them with the otherwise unsupported bitwise-or operator. That
    one-character marker preserves every source line and column for diagnostics
    and is converted to an Engine residual after the temporary AST is built.

    :param code: User-visible DAE source containing mathematical equalities.
    :return: Temporary Python-parseable source with identical character positions.
    :raises ValueError: If the reserved marker is written directly by the user.
    """
    normalized_tokens: List[tokenize.TokenInfo] = list()
    bracket_depth: int = 0
    waiting_for_assignment: bool = False
    waiting_for_list: bool = False
    algebraic_list_depth: int | None = None
    equality_was_replaced: bool = False
    insignificant_token_types: set[int] = set((
        tokenize.NL,
        tokenize.NEWLINE,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.COMMENT,
    ))

    try:
        source_token: tokenize.TokenInfo
        for source_token in tokenize.generate_tokens(StringIO(code).readline):
            token_text: str = source_token.string
            replacement_token: tokenize.TokenInfo = source_token

            if algebraic_list_depth is not None:
                if source_token.type == tokenize.OP and token_text == "=":
                    replacement_token = source_token._replace(string="|")
                    equality_was_replaced = True
                elif source_token.type == tokenize.OP and token_text == "|":
                    raise ValueError(
                        "The '|' operator is not supported inside algebraic_eqs; "
                        "use one '=' to separate the two equation sides"
                    )
                else:
                    pass
            else:
                pass
            normalized_tokens.append(replacement_token)

            if algebraic_list_depth is not None:
                if source_token.type == tokenize.OP and token_text in ("(", "[", "{"):
                    bracket_depth += 1
                elif source_token.type == tokenize.OP and token_text in (")", "]", "}"):
                    closes_algebraic_list: bool = (
                        token_text == "]" and bracket_depth == algebraic_list_depth
                    )
                    bracket_depth = max(0, bracket_depth - 1)
                    if closes_algebraic_list:
                        algebraic_list_depth = None
                    else:
                        pass
                else:
                    pass
            elif waiting_for_list:
                if source_token.type in insignificant_token_types:
                    pass
                elif source_token.type == tokenize.OP and token_text == "[":
                    bracket_depth += 1
                    algebraic_list_depth = bracket_depth
                    waiting_for_list = False
                else:
                    waiting_for_list = False
            elif waiting_for_assignment:
                if source_token.type in insignificant_token_types:
                    pass
                elif source_token.type == tokenize.OP and token_text == "=":
                    waiting_for_assignment = False
                    waiting_for_list = True
                else:
                    waiting_for_assignment = False
            else:
                if (bracket_depth == 0
                        and source_token.type == tokenize.NAME
                        and token_text == "algebraic_eqs"):
                    waiting_for_assignment = True
                else:
                    pass

                if source_token.type == tokenize.OP and token_text in ("(", "[", "{"):
                    bracket_depth += 1
                elif source_token.type == tokenize.OP and token_text in (")", "]", "}"):
                    bracket_depth = max(0, bracket_depth - 1)
                else:
                    pass
        normalized_code: str = tokenize.untokenize(normalized_tokens)
    except (IndentationError, tokenize.TokenError):
        # Tokenization still yields every complete token before an unfinished
        # tail. Preserve replacements already made so the Python parser reaches
        # the actual unmatched bracket instead of stopping at the visible '='.
        if equality_was_replaced:
            normalized_code = tokenize.untokenize(normalized_tokens)
        else:
            normalized_code = code
    return normalized_code


def build_unmatched_opening_bracket_diagnostic(
        code: str,
        message: str,
        fallback_line: int) -> DaeCodeDiagnostic | None:
    """Locate the opening bracket referenced by a Python syntax error.

    Python reports a mismatched closing bracket at the point where parsing
    becomes impossible. For editing, the useful position is the earlier
    opening bracket named in the error message.

    :param code: Complete DAE source.
    :param message: Message produced by :func:`ast.parse`.
    :param fallback_line: Syntax-error line when Python omits the opening line.
    :return: Opening-bracket diagnostic or ``None`` when it cannot be located.
    """
    opening_match: re.Match[str] | None = re.search(
        r"opening parenthesis '([\(\[\{])'(?: on line (\d+))?",
        message,
    )
    if opening_match is None:
        return None
    else:
        opening_symbol: str = opening_match.group(1)
        opening_line_text: str | None = opening_match.group(2)
        if opening_line_text is None:
            opening_line: int = fallback_line
        else:
            opening_line = int(opening_line_text)

    # Tokenization ignores brackets inside strings and comments. It can emit
    # all useful punctuation before eventually raising at the malformed tail.
    opening_stack: List[tuple[str, int, int]] = list()
    try:
        token_stream: tokenize.TokenInfo
        for token_stream in tokenize.generate_tokens(StringIO(code).readline):
            if token_stream.type == tokenize.OP:
                punctuation: str = token_stream.string
                if punctuation in ("(", "[", "{"):
                    opening_stack.append(
                        (punctuation, token_stream.start[0], token_stream.start[1])
                    )
                elif punctuation in (")", "]", "}"):
                    if len(opening_stack) > 0 and brackets_match(
                            opening_stack[-1][0], punctuation):
                        opening_stack.pop()
                    else:
                        pass
                else:
                    pass
            else:
                pass
    except (IndentationError, tokenize.TokenError):
        pass

    stack_entry: tuple[str, int, int]
    for stack_entry in opening_stack:
        if stack_entry[0] == opening_symbol and stack_entry[1] == opening_line:
            diagnostic_message: str = (
                f"{message}. Fix this unmatched opening bracket, then validate "
                "again to inspect the remaining code"
            )
            return DaeCodeDiagnostic(
                stack_entry[1],
                stack_entry[2],
                1,
                diagnostic_message,
            )
        else:
            pass
    return None


def build_missing_algebraic_comma_diagnostic(
        code: str,
        syntax_error_line: int) -> DaeCodeDiagnostic | None:
    """Identify a new algebraic equality following an unseparated entry.

    Complete equalities are normalized to Python expressions before parsing.
    Without a comma, the following equality starts where Python expects an
    operator. This check translates that generic syntax failure into the
    actionable source location while retaining the original line coordinates.

    :param code: Original user-visible DAE source.
    :param syntax_error_line: One-based line reported by the temporary parser.
    :return: Missing-comma diagnostic, or ``None`` when the pattern is absent.
    """
    source_lines: List[str] = code.splitlines()
    if syntax_error_line <= 1 or syntax_error_line > len(source_lines):
        return None
    else:
        pass
    current_line: str = source_lines[syntax_error_line - 1]
    previous_line_index: int = syntax_error_line - 2
    while (previous_line_index >= 0
           and len(source_lines[previous_line_index].strip()) == 0):
        previous_line_index -= 1
    if previous_line_index < 0:
        previous_line: str = ""
    else:
        previous_line = source_lines[previous_line_index].rstrip()

    # CPython can locate an adjacent-expression syntax error either at the new
    # equation or at the preceding one. First test the reported line directly.
    source_prefix: str = "\n".join(source_lines[:syntax_error_line])
    algebraic_start: int = source_prefix.rfind("algebraic_eqs")
    algebraic_end: int = source_prefix.rfind("]")
    inside_algebraic_section: bool = algebraic_start >= 0 and algebraic_start > algebraic_end
    previous_entry_is_open: bool = (
        len(previous_line) > 0
        and not previous_line.endswith(",")
        and not previous_line.endswith("[")
    )
    reported_line_starts_equation: bool = "=" in current_line
    if (inside_algebraic_section
            and reported_line_starts_equation
            and previous_entry_is_open):
        first_source_column: int = len(current_line) - len(current_line.lstrip())
        return DaeCodeDiagnostic(
            syntax_error_line,
            first_source_column,
            max(1, len(current_line.strip())),
            "Possible missing comma before this algebraic equation",
        )
    else:
        pass

    # When the parser points at the preceding entry, the actionable location
    # is the first non-separated equation on the following source line.
    following_line_number: int = syntax_error_line + 1
    if following_line_number <= len(source_lines):
        following_line: str = source_lines[following_line_number - 1]
        current_entry_is_open: bool = (
            len(current_line.rstrip()) > 0
            and not current_line.rstrip().endswith(",")
            and not current_line.rstrip().endswith("[")
        )
        following_line_starts_equation: bool = "=" in following_line
        if (inside_algebraic_section
                and current_entry_is_open
                and following_line_starts_equation):
            following_source_column: int = len(following_line) - len(following_line.lstrip())
            return DaeCodeDiagnostic(
                following_line_number,
                following_source_column,
                max(1, len(following_line.strip())),
                "Possible missing comma before this algebraic equation",
            )
        else:
            pass
    else:
        pass
    return None


def build_dae_code_diagnostics(code: str,
                               namespace: Mapping[str, Expr]) -> List[DaeCodeDiagnostic]:
    """Collect syntax and unknown-symbol errors without stopping at the first name.

    :param code: Complete Python-like DAE source.
    :param namespace: Symbols currently valid in the dialogue draft.
    :return: Source-local diagnostics in textual order.
    """
    result: List[DaeCodeDiagnostic] = list()
    try:
        normalized_code: str = normalize_algebraic_equality_syntax(code)
        module: ast.Module = ast.parse(normalized_code, mode="exec")
    except ValueError as error:
        result.append(find_text_diagnostic(code, "|", str(error)))
        return result
    except SyntaxError as error:
        line: int = 1 if error.lineno is None else int(error.lineno)
        column: int = 0 if error.offset is None else max(0, int(error.offset) - 1)
        error_text: str = error.msg if len(error.msg) > 0 else str(error)
        opening_diagnostic: DaeCodeDiagnostic | None = build_unmatched_opening_bracket_diagnostic(
            code,
            error_text,
            line,
        )
        missing_comma_diagnostic: DaeCodeDiagnostic | None = (
            build_missing_algebraic_comma_diagnostic(code, line)
        )
        if opening_diagnostic is not None:
            result.append(opening_diagnostic)
        elif missing_comma_diagnostic is not None:
            result.append(missing_comma_diagnostic)
        else:
            result.append(DaeCodeDiagnostic(line, column, 1, error_text))
        return result

    callable_names: set[str] = set(("abs", "sin", "cos", "tan", "asin", "acos", "atan", "atan2", "sqrt", "exp", "log", "log10", "sinh", "cosh", "tanh", "floor", "ceil", "round", "real", "imag", "conj", "angle", "heaviside", "rand", "min", "max",))
    allowed_names: set[str] = set(namespace.keys())
    allowed_names.update(callable_names)
    allowed_names.update(set(("state_eqs", "algebraic_eqs", "init_eqs", "diff_init_eqs",)))
    ast_node: ast.AST
    for ast_node in ast.walk(module):
        if isinstance(ast_node, ast.Call):
            # Two adjacent parenthesized list entries without a comma are
            # valid Python syntax for a call. In DAE data, however, only the
            # explicitly supported symbolic functions may be called. Mark the
            # second expression, which is where the missing comma belongs.
            valid_function_call: bool = (
                isinstance(ast_node.func, ast.Name)
                and ast_node.func.id in callable_names
            )
            if valid_function_call:
                pass
            elif len(ast_node.args) > 0:
                called_argument: ast.AST = ast_node.args[0]
                argument_length: int = max(
                    1,
                    int(called_argument.end_col_offset) - int(called_argument.col_offset),
                )
                result.append(
                    DaeCodeDiagnostic(
                        int(called_argument.lineno),
                        int(called_argument.col_offset),
                        argument_length,
                        "Possible missing comma before this expression",
                    )
                )
            else:
                result.append(
                    DaeCodeDiagnostic(
                        int(ast_node.lineno),
                        int(ast_node.col_offset),
                        1,
                        "Unsupported function call in DAE code",
                    )
                )
        elif isinstance(ast_node, ast.Name) and isinstance(ast_node.ctx, ast.Load):
            if ast_node.id not in allowed_names:
                message: str = f"Unknown symbol '{ast_node.id}'"
                result.append(
                    DaeCodeDiagnostic(
                        int(ast_node.lineno),
                        int(ast_node.col_offset),
                        len(ast_node.id),
                        message,
                    )
                )
            else:
                pass
        else:
            pass
    result.sort(key=build_diagnostic_sort_key)
    return result


def build_diagnostic_sort_key(diagnostic: DaeCodeDiagnostic) -> tuple[int, int]:
    """Return deterministic source order for one DAE diagnostic.

    :param diagnostic: Diagnostic being ordered.
    :return: Line and column tuple.
    """
    return diagnostic.get_line(), diagnostic.get_column()


def build_semantic_dae_diagnostic(code: str, message: str) -> DaeCodeDiagnostic:
    """Infer the most useful source span for one parser/count error.

    :param code: Complete DAE source.
    :param message: Semantic parser error.
    :return: Best-effort source-local diagnostic.
    """
    quoted_match: re.Match[str] | None = re.search(r"'(\w+)'", message)
    if quoted_match is not None:
        token: str = quoted_match.group(1)
    elif "state variables" in message:
        token = "state_eqs"
    elif "algebraic variables" in message:
        token = "algebraic_eqs"
    else:
        # A generic semantic error has no safe association with state
        # equations. Point to the first source token without mislabelling a
        # different DAE section.
        token = code.strip().split(maxsplit=1)[0] if len(code.strip()) > 0 else ""
    return find_text_diagnostic(code, token, message)


class DaeCodeEditor(BasePythonCodeEditor):
    """Symbolic DAE specialization with diagnostics and source search."""

    __slots__ = (
        "_diagnostics",
        "_search_ranges",
        "_active_search_index",
        "_symbol_namespace",
    )

    def __init__(
            self,
            parent: QtWidgets.QWidget | None = None,
            symbol_namespace: Mapping[str, Expr] | None = None,
    ) -> None:
        """Create the DAE-specific parser state and visual overlays.

        :param parent: Optional owning Qt widget.
        :param symbol_namespace: Symbols accepted by the safe DAE parser.
        :return: None.
        """
        super().__init__(parent)
        self._diagnostics: List[DaeCodeDiagnostic] = list()
        self._search_ranges: List[tuple[int, int]] = list()
        self._active_search_index: int = -1
        if symbol_namespace is None:
            self._symbol_namespace: Dict[str, Expr] = dict()
        else:
            self._symbol_namespace = dict(symbol_namespace)

    def set_symbol_namespace(self, symbol_namespace: Mapping[str, Expr]) -> None:
        """Replace the symbolic identities accepted by DAE validation.

        :param symbol_namespace: Current block symbols keyed by source name.
        :return: None.
        """
        self._symbol_namespace = dict(symbol_namespace)

    def get_symbol_namespace(self) -> Dict[str, Expr]:
        """Return a detached snapshot of the active symbolic namespace.

        :return: Symbols currently accepted by the DAE parser.
        """
        return dict(self._symbol_namespace)

    def build_current_diagnostics(self) -> List[DaeCodeDiagnostic]:
        """Analyze the visible source against the symbolic namespace.

        :return: Syntax and unknown-symbol diagnostics in source order.
        """
        return build_dae_code_diagnostics(self.toPlainText(), self._symbol_namespace)

    def parse_current_code(self) -> BlockEquationDraft:
        """Parse the visible source using the safe assignment-only DAE parser.

        :return: Parsed equation draft retaining the namespace identities.
        :raises ValueError: If the DAE source is unsupported or invalid.
        """
        return parse_equation_code(self.toPlainText(), self._symbol_namespace)

    def get_diagnostics(self) -> List[DaeCodeDiagnostic]:
        """Return diagnostics currently rendered by the editor.

        :return: Current diagnostic collection.
        """
        return list(self._diagnostics)

    def set_diagnostics(self, diagnostics: Sequence[DaeCodeDiagnostic]) -> None:
        """Underline every invalid source span and attach its local explanation.

        :param diagnostics: Complete diagnostics for the visible equation owner.
        :return: None.
        """
        self._diagnostics = list(diagnostics)
        self._refresh_extra_selections()

    def set_search_text(self, search_text: str) -> int:
        """Highlight every case-insensitive source-code match.

        :param search_text: Text requested by the user.
        :return: Number of matches in the current equation buffer.
        """
        source_text: str = self.toPlainText()
        normalized_query: str = search_text.strip().lower()
        self._search_ranges.clear()
        self._active_search_index = -1

        if len(normalized_query) > 0:
            normalized_source: str = source_text.lower()
            start_position: int = normalized_source.find(normalized_query)
            while start_position >= 0:
                self._search_ranges.append((start_position, len(normalized_query)))
                start_position = normalized_source.find(
                    normalized_query,
                    start_position + max(1, len(normalized_query)),
                )
            if len(self._search_ranges) > 0:
                self._active_search_index = 0
            else:
                pass
        else:
            pass

        self._activate_current_search_match()
        return len(self._search_ranges)

    def move_to_search_match(self, offset: int) -> tuple[int, int]:
        """Move to the previous or next highlighted source-code match.

        :param offset: Relative match offset, normally ``-1`` or ``1``.
        :return: One-based active match and total match count.
        """
        match_count: int = len(self._search_ranges)
        if match_count > 0:
            self._active_search_index = (self._active_search_index + offset) % match_count
        else:
            self._active_search_index = -1
        self._activate_current_search_match()
        return self._active_search_index + 1, match_count

    def get_search_position(self) -> tuple[int, int]:
        """Return the one-based active match and total match count.

        :return: Current search position and match count.
        """
        return self._active_search_index + 1, len(self._search_ranges)

    def _activate_current_search_match(self) -> None:
        """Select the active source-code match and refresh all overlays.

        :return: None.
        """
        if 0 <= self._active_search_index < len(self._search_ranges):
            start_position: int
            match_length: int
            start_position, match_length = self._search_ranges[self._active_search_index]
            cursor: QtGui.QTextCursor = self.textCursor()
            cursor.setPosition(start_position)
            cursor.setPosition(start_position + match_length, QtGui.QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)
            self.centerCursor()
        else:
            pass
        self._refresh_extra_selections()

    def _refresh_extra_selections(self) -> None:
        """Paint diagnostics and searches without either hiding the other.

        :return: None.
        """
        selections: List[QtWidgets.QTextEdit.ExtraSelection] = list()
        diagnostic: DaeCodeDiagnostic
        for diagnostic in self._diagnostics:
            text_block: QtGui.QTextBlock = self.document().findBlockByNumber(
                diagnostic.get_line() - 1
            )
            if text_block.isValid():
                line_length: int = max(0, text_block.length() - 1)
                if line_length > 0:
                    start_column: int = min(diagnostic.get_column(), line_length - 1)
                    selection_length: int = min(
                        diagnostic.get_length(),
                        line_length - start_column,
                    )
                else:
                    start_column = 0
                    selection_length = 1
                cursor: QtGui.QTextCursor = QtGui.QTextCursor(text_block)
                cursor.setPosition(text_block.position() + start_column)
                cursor.setPosition(
                    min(
                        text_block.position() + text_block.length() - 1,
                        cursor.position() + selection_length,
                    ),
                    QtGui.QTextCursor.MoveMode.KeepAnchor,
                )
                selection: QtWidgets.QTextEdit.ExtraSelection = QtWidgets.QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format.setForeground(QtGui.QColor("#b42318"))
                selection.format.setBackground(QtGui.QColor("#fee2e2"))
                selection.format.setUnderlineColor(QtGui.QColor("#dc2626"))
                selection.format.setUnderlineStyle(QtGui.QTextCharFormat.UnderlineStyle.WaveUnderline)
                selection.format.setToolTip(diagnostic.get_message())
                selections.append(selection)
            else:
                pass

        search_index: int
        search_range: tuple[int, int]
        for search_index, search_range in enumerate(self._search_ranges):
            search_start: int
            search_length: int
            search_start, search_length = search_range
            search_cursor: QtGui.QTextCursor = QtGui.QTextCursor(self.document())
            search_cursor.setPosition(search_start)
            search_cursor.setPosition(
                search_start + search_length,
                QtGui.QTextCursor.MoveMode.KeepAnchor,
            )
            search_selection: QtWidgets.QTextEdit.ExtraSelection = QtWidgets.QTextEdit.ExtraSelection()
            search_selection.cursor = search_cursor
            if search_index == self._active_search_index:
                search_selection.format.setBackground(QtGui.QColor("#fbbf24"))
            else:
                search_selection.format.setBackground(QtGui.QColor("#fef3c7"))
            selections.append(search_selection)
        self.setExtraSelections(selections)
        if len(self._diagnostics) > 0:
            summary: str = "\n".join(
                f"Line {diagnostic.get_line()}: {diagnostic.get_message()}"
                for diagnostic in self._diagnostics
            )
            self.setToolTip(summary)
        else:
            self.setToolTip("")


def build_block_symbol_namespace(block: Block) -> Dict[str, Expr]:
    """
    Build a complete safe parser namespace from one selected block tree.

    :param block: Symbolic block used by the operation.
    :return: Complete safe-parser namespace for the selected block tree.
    """
    namespace: Dict[str, Expr] = dict()
    child: Block
    variable: Var
    for child in block.get_all_blocks():
        variable_groups: tuple[Sequence[Var], ...] = (
            child.algebraic_vars,
            child.state_vars,
            child.diff_vars,
            child.in_vars,
            child.out_vars,
            tuple(child.parameters.keys()),
            tuple(child.event_dict.keys()),
            tuple(child.mode_dict.keys()),
            tuple(child.init_values.keys()),
            tuple(child.init_eqs.keys()),
            tuple(child.diff_init_eqs.keys()),
            tuple(child.discrete_eqs.keys()),
            tuple(child.boolean_guards.keys()),
            tuple(child.external_mapping.values()),
            tuple(child.api_obj_mapping.values()),
        )
        group: Sequence[Var]
        for group in variable_groups:
            for variable in group:
                if isinstance(variable, Var):
                    namespace[variable.name] = variable
                else:
                    pass

        # Some valid templates intentionally keep mapped or intermediate Vars
        # only inside expressions. Collecting those leaves the parser aligned
        # with the actual symbolic model instead of only its display lists.
        expression_groups: tuple[Sequence[Expr], ...] = (
            child.state_eqs,
            child.algebraic_eqs,
            tuple(child.init_eqs.values()),
            tuple(child.diff_init_eqs.values()),
            tuple(child.discrete_eqs.values()),
            tuple(child.event_dict.values()),
            tuple(child.mode_dict.values()),
        )
        expression_group: Sequence[Expr]
        expression: Expr
        expression_variable: Var
        for expression_group in expression_groups:
            for expression in expression_group:
                if isinstance(expression, Expr):
                    for expression_variable in get_expression_vars(expression):
                        namespace[expression_variable.name] = expression_variable
                else:
                    pass

        # Runtime logic can read simulation-owned symbols, such as the global
        # time variable, which intentionally do not belong to a DAE display
        # list. Include those identities so an existing catalogue block can be
        # opened, validated and reapplied without rewriting its expressions.
        procedural_entry: ProceduralLogicBase
        procedural_variable: Var
        for procedural_entry in child.procedural_logic:
            for procedural_variable in get_procedural_expression_variables(procedural_entry):
                namespace[procedural_variable.name] = procedural_variable
    return namespace


def build_equation_code(block: Block) -> str:
    """
    Serialize informative variable order and editable equations as safe code.

    :param block: Symbolic block used by the operation.
    :return: Ordered variable declarations and editable DAE sections.
    """
    lines: List[str] = list()
    lines.append(_serialize_variable_list("state_vars", block.state_vars))
    lines.append(_serialize_variable_list("algebraic_vars", block.algebraic_vars))
    lines.append(_serialize_variable_list("diff_vars", block.diff_vars))
    lines.append("")
    lines.extend(_serialize_state_equation_dict(
        state_variables=block.state_vars,
        state_equations=block.state_eqs,
        comments=list((
            "Map every state variable to the right-hand side of its differential equation.",
            "Example: for d_x = -x / T, write: x: -x / T,",
        )),
    ))
    lines.append("")
    lines.extend(_serialize_algebraic_equation_list(
        expressions=block.algebraic_eqs,
        comments=list((
            "Write each complete equation with one single '=' between its two sides.",
            "Examples: 0 = y - K * x, or y = K * x,",
        )),
    ))
    lines.append("")
    lines.extend(_serialize_expression_dict(
        name="init_eqs",
        expressions=block.init_eqs,
        comments=list(("Map each variable to its initial expression. Example: x: x0,",)),
    ))
    lines.append("")
    lines.extend(_serialize_expression_dict(
        name="diff_init_eqs",
        expressions=block.diff_init_eqs,
        comments=list(("Map each derivative to its initial expression. Example: d_x: 0.0,",)),
    ))
    return "\n".join(lines)


def _serialize_variable_list(name: str, variables: Sequence[Var]) -> str:
    """Serialize one informative variable declaration on a single line.

    :param name: Declaration section name.
    :param variables: Ordered variables shown in the declaration.
    :return: One-line Python-like variable list.
    """
    variable_names: List[str] = list()
    variable: Var
    for variable in variables:
        variable_names.append(variable.name)
    return f"{name} = [{', '.join(variable_names)}]"


def synchronize_dae_variable_declarations(code: str,
                                          state_names: Sequence[str],
                                          algebraic_names: Sequence[str],
                                          differential_names: Sequence[str]) -> str:
    """Synchronize the three table-owned variable declarations in DAE code.

    Variable declarations are managed projections of the Variables table. A
    declaration may still be multiline while the user is editing, so each
    complete assignment is replaced as one unit without touching equations or
    any other source text. Missing declarations are restored at the beginning
    for compatibility with older hand-written buffers.

    :param code: Current detached DAE source.
    :param state_names: Ordered state-variable names from the table draft.
    :param algebraic_names: Ordered algebraic-variable names from the table draft.
    :param differential_names: Ordered differential-variable names from the table draft.
    :return: DAE source with synchronized one-line variable declarations.
    """
    sections: tuple[tuple[str, Sequence[str]], ...] = (
        ("state_vars", state_names),
        ("algebraic_vars", algebraic_names),
        ("diff_vars", differential_names),
    )
    updated_code: str = code
    missing_declarations: List[str] = list()
    section_name: str
    section_names: Sequence[str]
    for section_name, section_names in sections:
        declaration: str = f"{section_name} = [{', '.join(section_names)}]"
        declaration_pattern: str = (
            rf"(?ms)^[ \t]*{re.escape(section_name)}[ \t]*=[ \t]*\[[^\]]*\]"
        )
        replacement_count: int
        updated_code, replacement_count = re.subn(
            declaration_pattern,
            declaration,
            updated_code,
            count=1,
        )
        if replacement_count == 0:
            missing_declarations.append(declaration)
        else:
            pass

    if len(missing_declarations) > 0:
        if "\r\n" in updated_code:
            newline: str = "\r\n"
        else:
            newline = "\n"
        declaration_prefix: str = newline.join(missing_declarations)
        if len(updated_code) > 0:
            updated_code = declaration_prefix + newline + newline + updated_code
        else:
            updated_code = declaration_prefix
    else:
        pass
    return updated_code


def replace_dae_identifier(code: str, old_name: str, new_name: str) -> str:
    """Replace one Python identifier without altering partial symbol names.

    The DAE editor can contain an incomplete draft while a rename is requested.
    Token-aware replacement preserves normal source formatting; a word-boundary
    fallback still keeps that incomplete draft aligned with the renamed model.

    :param code: Current detached DAE source.
    :param old_name: Exact identifier used before the rename.
    :param new_name: Exact identifier accepted by the central editor rename.
    :return: Source using ``new_name`` for every matching identifier token.
    """
    if old_name == new_name:
        return code
    else:
        pass

    replaced_tokens: List[tokenize.TokenInfo] = list()
    try:
        source_token: tokenize.TokenInfo
        for source_token in tokenize.generate_tokens(StringIO(code).readline):
            if source_token.type == tokenize.NAME and source_token.string == old_name:
                replaced_tokens.append(source_token._replace(string=new_name))
            else:
                replaced_tokens.append(source_token)
        result: str = tokenize.untokenize(replaced_tokens)
    except (IndentationError, tokenize.TokenError):
        identifier_pattern: str = rf"\b{re.escape(old_name)}\b"
        result = re.sub(identifier_pattern, new_name, code)
    return result


def serialize_dae_expression(expression: Expr | Comparison) -> str:
    """Serialize one DAE expression without a redundant root pair.

    ``symbolic_to_string`` deliberately parenthesizes every binary expression
    to preserve its complete tree. At the top level of a list or dictionary
    value, that outermost pair has no effect. Inner pairs are retained because
    they can still be required for Python operator precedence.

    :param expression: Symbolic expression shown in the DAE source editor.
    :return: Parsable expression text without redundant root parentheses.
    """
    expression_text: str = symbolic_to_string(expression)
    if isinstance(expression, (BinOp, Comparison)):
        return expression_text[1:-1]
    else:
        return expression_text


def _serialize_algebraic_equation_list(
        expressions: Sequence[Expr],
        comments: Sequence[str] | None = None) -> List[str]:
    """Serialize Engine residuals as complete GUI algebraic equalities.

    The Engine stores each algebraic expression as a residual that must be
    zero. Placing zero on the visible left side preserves that expression
    exactly when the GUI parser converts the equality back to a residual.

    :param expressions: Ordered Engine algebraic residual expressions.
    :param comments: Explanatory lines inserted inside the generated list.
    :return: Complete algebraic equations serialized as readable source lines.
    """
    lines: List[str] = list(("algebraic_eqs = [",))
    if comments is not None:
        comment: str
        for comment in comments:
            lines.append(f"    # {comment}")
    else:
        pass
    expression: Expr
    for expression in expressions:
        lines.append(f"    0 = {serialize_dae_expression(expression)},")
    lines.append("]")
    return lines


def _serialize_state_equation_dict(
        state_variables: Sequence[Var],
        state_equations: Sequence[Expr],
        comments: Sequence[str] | None = None) -> List[str]:
    """Serialize state-variable/RHS associations as an editable dictionary.

    The Engine stores right-hand sides as a positional list. The GUI exposes
    the association explicitly so users never need to count list entries to
    identify a state equation. Inconsistent legacy models remain visible as
    comments and fail validation until the user repairs the missing pairing.

    :param state_variables: Ordered Engine state variables.
    :param state_equations: Ordered Engine right-hand-side expressions.
    :param comments: Explanatory lines inserted inside the generated mapping.
    :return: State equation mapping serialized as readable source lines.
    """
    lines: List[str] = list(("state_eqs = {",))
    if comments is not None:
        comment: str
        for comment in comments:
            lines.append(f"    # {comment}")
    else:
        pass

    paired_count: int = min(len(state_variables), len(state_equations))
    equation_index: int
    for equation_index in range(paired_count):
        state_variable: Var = state_variables[equation_index]
        state_equation: Expr = state_equations[equation_index]
        lines.append(
            f"    {state_variable.name}: {serialize_dae_expression(state_equation)},"
        )

    missing_index: int
    for missing_index in range(paired_count, len(state_variables)):
        lines.append(
            f"    # Missing equation for state variable: {state_variables[missing_index].name}"
        )

    extra_index: int
    for extra_index in range(paired_count, len(state_equations)):
        extra_equation: Expr = state_equations[extra_index]
        lines.append(
            f"    # Unassigned state equation: {serialize_dae_expression(extra_equation)}"
        )
    lines.append("}")
    return lines


def _serialize_expression_dict(name: str,
                               expressions: Mapping[Var, Expr],
                               comments: Sequence[str] | None = None) -> List[str]:
    """
    Serialize one variable-to-expression mapping.

    :param name: Value supplied for ``name``.
    :param expressions: Value supplied for ``expressions``.
    :param comments: Explanatory lines inserted inside the generated dictionary.
    :return: Variable-to-expression mapping serialized as source lines.
    """
    lines: List[str] = list((f"{name} = {{",))
    if comments is not None:
        comment: str
        for comment in comments:
            lines.append(f"    # {comment}")
    else:
        pass
    variable: Var
    expression: Expr
    for variable, expression in expressions.items():
        lines.append(f"    {variable.name}: {serialize_dae_expression(expression)},")
    lines.append("}")
    return lines


def parse_equation_code(code: str, namespace: Mapping[str, Expr]) -> BlockEquationDraft:
    """
    Parse the supported assignment-only DAE language without executing code.

    :param code: Value supplied for ``code``.
    :param namespace: Value supplied for ``namespace``.
    :return: Detached equation draft parsed without executing the supplied code.
    """
    normalized_code: str = normalize_algebraic_equality_syntax(code)
    try:
        module: ast.Module = ast.parse(normalized_code, mode="exec")
    except SyntaxError as error:
        raise ValueError(str(error)) from error

    parsed_lists: Dict[str, List[Expr]] = dict()
    parsed_dicts: Dict[str, Dict[Var, Expr]] = dict()
    parsed_variable_lists: Dict[str, List[Var]] = dict()
    statement: ast.stmt
    for statement in module.body:
        _parse_equation_statement(
            statement=statement,
            namespace=namespace,
            parsed_lists=parsed_lists,
            parsed_dicts=parsed_dicts,
            parsed_variable_lists=parsed_variable_lists,
        )

    required_lists: tuple[str, ...] = ("algebraic_eqs",)
    required_dicts: tuple[str, ...] = ("state_eqs", "init_eqs", "diff_init_eqs")
    required_variable_lists: tuple[str, ...] = ("state_vars",)
    _validate_required_sections(required_lists, parsed_lists)
    _validate_required_sections(required_dicts, parsed_dicts)
    _validate_required_sections(required_variable_lists, parsed_variable_lists)

    # The GUI mapping is converted back to the Engine's positional list only
    # after proving that every declared state owns exactly one right-hand side.
    state_variables: List[Var] = parsed_variable_lists["state_vars"]
    state_equation_mapping: Dict[Var, Expr] = parsed_dicts["state_eqs"]
    missing_state_names: List[str] = list()
    state_variable: Var
    for state_variable in state_variables:
        if state_variable not in state_equation_mapping:
            missing_state_names.append(state_variable.name)
        else:
            pass
    unexpected_state_names: List[str] = list()
    mapped_state: Var
    for mapped_state in state_equation_mapping:
        if mapped_state not in state_variables:
            unexpected_state_names.append(mapped_state.name)
        else:
            pass
    if len(missing_state_names) > 0 or len(unexpected_state_names) > 0:
        raise ValueError(
            "Section 'state_eqs' must map every state_vars entry exactly once; "
            f"missing={missing_state_names}, unexpected={unexpected_state_names}"
        )
    else:
        ordered_state_equations: List[Expr] = list()
        for state_variable in state_variables:
            ordered_state_equations.append(state_equation_mapping[state_variable])
    return BlockEquationDraft(
        ordered_state_equations,
        parsed_lists["algebraic_eqs"],
        parsed_dicts["init_eqs"],
        parsed_dicts["diff_init_eqs"],
        parsed_variable_lists,
    )


def _parse_equation_statement(statement: ast.stmt,
                              namespace: Mapping[str, Expr],
                              parsed_lists: Dict[str, List[Expr]],
                              parsed_dicts: Dict[str, Dict[Var, Expr]],
                              parsed_variable_lists: Dict[str, List[Var]]) -> None:
    """
    Parse one assignment statement from the DAE editor.

    :param statement: Value supplied for ``statement``.
    :param namespace: Value supplied for ``namespace``.
    :param parsed_lists: Value supplied for ``parsed_lists``.
    :param parsed_dicts: Value supplied for ``parsed_dicts``.
    :param parsed_variable_lists: Parsed informative variable-order sections.
    :return: None.
    """
    if not isinstance(statement, ast.Assign):
        raise ValueError("Only assignments to supported DAE sections are allowed")
    elif len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
        raise ValueError("Each DAE section must use one simple assignment")
    else:
        section_name: str = statement.targets[0].id

    if (section_name in parsed_lists
            or section_name in parsed_dicts
            or section_name in parsed_variable_lists):
        raise ValueError(f"Section '{section_name}' is assigned more than once")
    elif section_name == "algebraic_eqs":
        parsed_lists[section_name] = _parse_algebraic_equation_list(
            statement.value,
            namespace,
        )
    elif section_name in ("state_eqs", "init_eqs", "diff_init_eqs"):
        parsed_dicts[section_name] = _parse_expression_dict(statement.value, namespace, section_name)
    elif section_name in ("state_vars", "algebraic_vars", "diff_vars"):
        parsed_variable_lists[section_name] = _parse_variable_list(
            node=statement.value,
            namespace=namespace,
            section_name=section_name,
        )
    else:
        raise ValueError(f"Unsupported DAE section '{section_name}'")


def _parse_variable_list(node: ast.expr,
                         namespace: Mapping[str, Expr],
                         section_name: str) -> List[Var]:
    """Parse one informative ordered variable declaration.

    These declarations expose the block's current DAE ordering but do not create,
    delete, or reclassify symbols. Structural symbol edits remain owned by the
    Variables and Parameters tables.

    :param node: Assignment value expected to be a list or tuple.
    :param namespace: Allowed symbolic identities by name.
    :param section_name: Declaration section being parsed.
    :return: Ordered existing variables referenced by the declaration.
    """
    if not isinstance(node, (ast.List, ast.Tuple)):
        raise ValueError(f"Section '{section_name}' must be a list")
    else:
        result: List[Var] = list()

    element: ast.expr
    for element in node.elts:
        if not isinstance(element, ast.Name):
            raise ValueError(f"Entries in '{section_name}' must be variable names")
        else:
            symbol: Expr | None = namespace.get(element.id, None)
        if not isinstance(symbol, Var):
            raise ValueError(f"Unknown variable '{element.id}' in '{section_name}'")
        elif symbol in result:
            raise ValueError(f"Variable '{element.id}' is repeated in '{section_name}'")
        else:
            result.append(symbol)
    return result


def _parse_algebraic_equation_list(node: ast.expr,
                                   namespace: Mapping[str, Expr]) -> List[Expr]:
    """Parse complete GUI equalities into Engine algebraic residuals.

    The normalization layer represents the visible equality with a root
    bitwise-or AST node. Exactly one such marker is required per list entry.
    ``right - left`` follows the GUI convention ``0 = residual``; an explicit
    zero on either side is simplified so opening and applying an unchanged
    block preserves its existing symbolic expression.

    :param node: Assignment value expected to be a list.
    :param namespace: Allowed symbolic identities by name.
    :return: Ordered algebraic residual expressions for the Engine.
    """
    if not isinstance(node, ast.List):
        raise ValueError("Section 'algebraic_eqs' must be a list")
    else:
        result: List[Expr] = list()
        element: ast.expr
        for element in node.elts:
            equality_marker_count: int = 0
            child_node: ast.AST
            for child_node in ast.walk(element):
                if isinstance(child_node, ast.BinOp) and isinstance(child_node.op, ast.BitOr):
                    equality_marker_count += 1
                else:
                    pass

            if not isinstance(element, ast.BinOp):
                raise ValueError(
                    "Every entry in 'algebraic_eqs' must contain exactly one '=' "
                    "between two complete symbolic expressions"
                )
            elif not isinstance(element.op, ast.BitOr) or equality_marker_count != 1:
                raise ValueError(
                    "Every entry in 'algebraic_eqs' must contain exactly one '=' "
                    "between two complete symbolic expressions"
                )
            else:
                left_expression: Expr | Comparison = _parse_symbolic_ast_node(
                    element.left,
                    namespace,
                )
                right_expression: Expr | Comparison = _parse_symbolic_ast_node(
                    element.right,
                    namespace,
                )

            if not isinstance(left_expression, Expr) or not isinstance(right_expression, Expr):
                raise ValueError("Algebraic equality sides must be symbolic expressions")
            elif isinstance(left_expression, Const) and left_expression.value == 0:
                residual_expression: Expr = right_expression
            elif isinstance(right_expression, Const) and right_expression.value == 0:
                residual_expression = left_expression
            else:
                residual_expression = right_expression - left_expression
            result.append(residual_expression)
        return result


def _parse_expression_dict(node: ast.expr,
                           namespace: Mapping[str, Expr],
                           section_name: str) -> Dict[Var, Expr]:
    """
    Parse a variable-to-expression mapping with identity-preserving keys.

    :param node: Value supplied for ``node``.
    :param namespace: Value supplied for ``namespace``.
    :param section_name: Value supplied for ``section_name``.
    :return: Parsed variable-to-expression mapping with identity-preserving keys.
    """
    if not isinstance(node, ast.Dict):
        raise ValueError(f"Section '{section_name}' must be a dictionary")
    else:
        result: Dict[Var, Expr] = dict()

    index: int
    for index in range(len(node.keys)):
        key_node: ast.expr | None = node.keys[index]
        value_node: ast.expr = node.values[index]
        if not isinstance(key_node, ast.Name):
            raise ValueError(f"Keys in '{section_name}' must be variable names")
        else:
            key_symbol: Expr | None = namespace.get(key_node.id, None)
        if not isinstance(key_symbol, Var):
            raise ValueError(f"Unknown variable '{key_node.id}' in '{section_name}'")
        elif key_symbol in result:
            raise ValueError(f"Variable '{key_node.id}' is repeated in '{section_name}'")
        else:
            expression: Expr | Comparison = _parse_symbolic_ast_node(value_node, namespace)
        if isinstance(expression, Comparison):
            raise ValueError(f"Comparisons are not supported in '{section_name}'")
        else:
            result[key_symbol] = expression
    return result


def _parse_symbolic_ast_node(node: ast.expr, namespace: Mapping[str, Expr]) -> Expr | Comparison:
    """Convert one safe AST expression while preserving symbolic identities.

    The Engine parser deliberately accepts unary functions only. Dynamic
    templates also contain binary symbolic functions such as ``atan2``. This
    editor-side walker therefore handles the expression structure explicitly
    and delegates unary function-name validation to the Engine parser.

    :param node: Parsed Python expression node.
    :param namespace: Allowed symbolic identities by name.
    :return: Parsed symbolic expression or comparison.
    """
    expression: Expr | Comparison
    if isinstance(node, ast.Constant):
        value: object = node.value
        if isinstance(value, (int, float, complex)):
            expression = Const(value)
        else:
            raise ValueError(f"Unsupported constant {value!r}")
    elif isinstance(node, ast.Name):
        symbol: Expr | None = namespace.get(node.id, None)
        if isinstance(symbol, Expr):
            expression = symbol
        else:
            raise ValueError(f"Unknown symbol '{node.id}'")
    elif isinstance(node, ast.BinOp):
        expression = _parse_symbolic_binary_operation(node, namespace)
    elif isinstance(node, ast.UnaryOp):
        expression = _parse_symbolic_unary_operation(node, namespace)
    elif isinstance(node, ast.Call):
        expression = _parse_symbolic_function_call(node, namespace)
    elif isinstance(node, ast.Compare):
        expression = _parse_symbolic_comparison(node, namespace)
    else:
        raise ValueError(f"Unsupported expression node {node.__class__.__name__}")
    return expression


def _parse_symbolic_binary_operation(node: ast.BinOp,
                                     namespace: Mapping[str, Expr]) -> Expr:
    """Parse one supported arithmetic binary operation.

    :param node: Binary-operation AST node.
    :param namespace: Allowed symbolic identities by name.
    :return: Symbolic binary expression.
    """
    left: Expr | Comparison = _parse_symbolic_ast_node(node.left, namespace)
    right: Expr | Comparison = _parse_symbolic_ast_node(node.right, namespace)
    if not isinstance(left, Expr) or not isinstance(right, Expr):
        raise ValueError("Arithmetic operations require symbolic operands")
    else:
        pass

    operator_text: str
    if isinstance(node.op, ast.Add):
        operator_text = "+"
    elif isinstance(node.op, ast.Sub):
        operator_text = "-"
    elif isinstance(node.op, ast.Mult):
        operator_text = "*"
    elif isinstance(node.op, ast.Div):
        operator_text = "/"
    elif isinstance(node.op, ast.Pow):
        operator_text = "**"
    else:
        raise ValueError(f"Unsupported binary operator {node.op.__class__.__name__}")
    return BinOp(left, operator_text, right)


def _parse_symbolic_unary_operation(node: ast.UnaryOp,
                                    namespace: Mapping[str, Expr]) -> Expr:
    """Parse unary plus or minus.

    :param node: Unary-operation AST node.
    :param namespace: Allowed symbolic identities by name.
    :return: Symbolic operand or negation.
    """
    operand: Expr | Comparison = _parse_symbolic_ast_node(node.operand, namespace)
    if not isinstance(operand, Expr):
        raise ValueError("Unary operations require a symbolic operand")
    elif isinstance(node.op, ast.UAdd):
        return operand
    elif isinstance(node.op, ast.USub):
        return UnOp("-", operand)
    else:
        raise ValueError(f"Unsupported unary operator {node.op.__class__.__name__}")


def _parse_symbolic_function_call(node: ast.Call,
                                  namespace: Mapping[str, Expr]) -> Expr:
    """Parse a supported named unary or binary symbolic function.

    :param node: Function-call AST node.
    :param namespace: Allowed symbolic identities by name.
    :return: Symbolic function expression.
    """
    if not isinstance(node.func, ast.Name):
        raise ValueError("Only named symbolic functions are supported")
    elif len(node.keywords) > 0:
        raise ValueError("Keyword arguments are not supported in symbolic functions")
    else:
        function_name: str = node.func.id

    if len(node.args) == 1:
        argument: Expr | Comparison = _parse_symbolic_ast_node(node.args[0], namespace)
        if not isinstance(argument, Expr):
            raise ValueError("Symbolic functions require expression arguments")
        else:
            temporary_name: str = "__dae_function_argument"
            temporary_namespace: Dict[str, Expr] = dict(namespace)
            temporary_namespace[temporary_name] = argument
            parsed: Expr | Comparison = string_to_symbolic(
                f"{function_name}({temporary_name})",
                temporary_namespace,
            )
        if isinstance(parsed, Expr):
            return parsed
        else:
            raise ValueError("A symbolic function cannot return a comparison")
    elif len(node.args) == 2 and function_name in ("atan2", "min", "max"):
        first: Expr | Comparison = _parse_symbolic_ast_node(node.args[0], namespace)
        second: Expr | Comparison = _parse_symbolic_ast_node(node.args[1], namespace)
        if isinstance(first, Expr) and isinstance(second, Expr):
            return Func2(function_name, first, second)
        else:
            raise ValueError("Binary symbolic functions require expression arguments")
    else:
        raise ValueError(f"Unsupported arguments for symbolic function '{function_name}'")


def _parse_symbolic_comparison(node: ast.Compare,
                               namespace: Mapping[str, Expr]) -> Comparison:
    """Parse one non-chained comparison.

    :param node: Comparison AST node.
    :param namespace: Allowed symbolic identities by name.
    :return: Symbolic comparison.
    """
    if len(node.ops) != 1 or len(node.comparators) != 1:
        raise ValueError("Only simple two-sided comparisons are supported")
    else:
        left: Expr | Comparison = _parse_symbolic_ast_node(node.left, namespace)
        right: Expr | Comparison = _parse_symbolic_ast_node(node.comparators[0], namespace)
    if not isinstance(left, Expr) or not isinstance(right, Expr):
        raise ValueError("Comparisons require symbolic operands")
    elif isinstance(node.ops[0], ast.Lt):
        return left < right
    elif isinstance(node.ops[0], ast.LtE):
        return left <= right
    elif isinstance(node.ops[0], ast.Gt):
        return left > right
    elif isinstance(node.ops[0], ast.GtE):
        return left >= right
    elif isinstance(node.ops[0], ast.Eq):
        return left == right
    else:
        raise ValueError(f"Unsupported comparison operator {node.ops[0].__class__.__name__}")


def _validate_required_sections(required: Sequence[str], parsed: Mapping[str, object]) -> None:
    """
    Require each supported section exactly once.

    :param required: Value supplied for ``required``.
    :param parsed: Value supplied for ``parsed``.
    :return: None.
    """
    section_name: str
    for section_name in required:
        if section_name not in parsed:
            raise ValueError(f"Missing required DAE section '{section_name}'")
        else:
            pass


def block_has_advanced_logic(block: Block) -> bool:
    """
    :param block: Symbolic block used by the operation.
    :return: Whether unsupported advanced symbolic fields are present.
    """
    result: bool = False
    child: Block
    for child in block.get_all_blocks():
        if (
            child.inequalities
            or child.discrete_eqs
            or child.boolean_guards
            or child.procedural_logic
            or child.reformulated_vars
        ):
            result = True
        else:
            pass
    return result


def build_advanced_logic_summary(block: Block) -> str:
    """
    Summarize recursive read-only symbolic fields not covered by DAE code.

    :param block: Symbolic block used by the operation.
    :return: Summary of recursive read-only symbolic fields not covered by DAE code.
    """
    inequality_count: int = 0
    discrete_count: int = 0
    guard_count: int = 0
    procedural_count: int = 0
    reformulated_count: int = 0
    child: Block
    for child in block.get_all_blocks():
        inequality_count += len(child.inequalities)
        discrete_count += len(child.discrete_eqs)
        guard_count += len(child.boolean_guards)
        procedural_count += len(child.procedural_logic)
        reformulated_count += len(child.reformulated_vars)
    return (
        f"inequalities={inequality_count}, discrete={discrete_count}, guards={guard_count}, "
        f"procedural={procedural_count}, reformulated variables={reformulated_count}"
    )


def resolve_block_documentation_url(block_type_name: str, block_name: str) -> str | None:
    """Resolve the online catalogue documentation URL for one library block.

    The returned page describes the original predefined block. A working copy
    edited in the Dynamic Model Editor can intentionally differ from it.

    :param block_type_name: Persisted diagram node type.
    :param block_name: Symbolic template or block name used to refine the lookup.
    :return: ReadTheDocs URL or ``None`` for a genuinely custom block.
    """
    # Reuse the single catalogue mapping and only translate its Sphinx source
    # path into the HTML path published by ReadTheDocs. Runtime code therefore
    # never needs the repository's local ``doc`` directory.
    relative_path: str | None = _get_documentation_relative_path(block_type_name, block_name)
    if relative_path is None:
        result: str | None = None
    else:
        normalized_path: str = relative_path.replace("\\", "/")
        if normalized_path.endswith(".md"):
            html_path: str = normalized_path[:-3] + ".html"
        else:
            html_path = normalized_path + ".html"
        result = f"https://veragrid.readthedocs.io/en/latest/md_source/dyn_templates/{html_path}"
    return result


def _get_documentation_relative_path(block_type_name: str, block_name: str) -> str | None:
    """Return an explicit documentation mapping for supported catalogue types.

    :param block_type_name: Persisted diagram node type.
    :param block_name: Symbolic template or block name.
    :return: Documentation path relative to ``dyn_templates`` or ``None``.
    """
    normalized: str = block_type_name.upper()
    normalized_block_name: str = re.sub(r"[^A-Z0-9]+", "_", block_name.upper()).strip("_")
    catalogue_type_match: re.Match[str] | None = re.search(r"__(\d+)$", block_name)
    if normalized == "TEMPLATE" and catalogue_type_match is not None:
        # Every generated Basic Block Catalog page is keyed by the immutable
        # imported type id. Display names are not unique and can contain
        # punctuation, while the ``__<typ_id>`` suffix survives serialization.
        return f"library/catalog/typ_{catalogue_type_match.group(1)}.md"
    else:
        pass
    mapping: Dict[str, str] = dict((("GENERIC", "library/generic.md"), ("CONST", "library/constant.md"), ("GAIN", "library/gain.md"), ("ABS", "library/absolute_value.md"), ("SUM", "library/sum.md"), ("PRODUCT", "library/product.md"), ("FROM_GOTO", "library/from_goto.md"), ("LINE_RMS", "RMS/line.md"), ("LOAD_RMS", "RMS/load.md"), ("GENRAW", "RMS/genrou_genrow.md"), ("GENQEC", "RMS/genqec.md"), ("GOV_RMS", "RMS/governor.md"), ("STAB_RMS", "RMS/stabilizer.md"), ("EXCITER_RMS", "RMS/exciter.md"), ("EMT_GENERATOR", "EMT/sauer_pai_generator.md"), ("GOV_EMT", "EMT/governor.md"), ("STAB_EMT", "EMT/stabilizer.md"), ("EXCITER_EMT", "EMT/exciter.md"), ("EMT_PI_LINE", "EMT/pi_line_abc.md"), ("EMT_BERGERON_LINE", "EMT/bergeron_line_abc.md"), ("EMT_JMARTI_LINE", "EMT/jmarti_line.md"), ("EMT_DC_LINE", "EMT/dc_line.md"), ("EXP_LOAD_EMT", "library/exp_load_emt.md"), ("ZIP_LOAD_EMT", "EMT/zip_load_abc.md"), ("DC_LOAD_EMT", "EMT/dc_load.md"), ("EMT_THEVENIN", "EMT/thevenin_generator.md"), ("TRAFO_EMT", "library/trafo_emt.md"), ("XFMR_TRANSFORMER", "library/xfmr_transformer.md"), ("INDUCTION_MOTOR_EMT", "EMT/single_cage_induction_motor.md"), ("PV_POWER_PLANT_EMT", "EMT/pv_plant_grid_following.md"), ("PV_EMT", "EMT/pv_plant_grid_following.md"), ("COMPLETE_PSEUDO_VSC_EMT", "EMT/full_pseudo_converter.md"), ("GFL_CONVERTER_RMS", "RMS/converter.md"), ("BESS_EMT", "EMT/bess.md"), ("BATTERY_EMT", "library/battery_emt.md"), ("VOLTAGE_SOURCE_EMT", "library/voltage_source_emt.md"), ("CURRENT_SOURCE_EMT", "library/current_source_emt.md"), ("CONTROLLED_VOLTAGE_SOURCE_EMT", "library/controlled_voltage_source_emt.md"), ("CONTROLLED_CURRENT_SOURCE_EMT", "library/controlled_current_source_emt.md"), ("ARBITRARY_WAVEFORM_VOLTAGE_SOURCE_EMT", "library/arbitrary_waveform_voltage_source_emt.md"), ("ARBITRARY_WAVEFORM_CURRENT_SOURCE_EMT", "library/arbitrary_waveform_current_source_emt.md"), ("BALANCED_3PH_VOLTAGE_SOURCE_EMT", "library/balanced_3ph_voltage_source_emt.md"), ("BALANCED_3PH_CURRENT_SOURCE_EMT", "library/balanced_3ph_current_source_emt.md"), ("CONTROLLED_BALANCED_3PH_VOLTAGE_SOURCE_EMT", "library/controlled_balanced_3ph_voltage_source_emt.md"), ("CONTROLLED_BALANCED_3PH_CURRENT_SOURCE_EMT", "library/controlled_balanced_3ph_current_source_emt.md"), ("DC_VOLTAGE_SOURCE_EMT", "library/dc_voltage_source_emt.md"), ("DC_CURRENT_SOURCE_EMT", "library/dc_current_source_emt.md"), ("CONTROLLED_DC_VOLTAGE_SOURCE_EMT", "library/controlled_dc_voltage_source_emt.md"), ("CONTROLLED_DC_CURRENT_SOURCE_EMT", "library/controlled_dc_current_source_emt.md"), ("STEP_VOLTAGE_SOURCE_EMT", "library/step_voltage_source_emt.md"), ("STEP_CURRENT_SOURCE_EMT", "library/step_current_source_emt.md"), ("RAMP_VOLTAGE_SOURCE_EMT", "library/ramp_voltage_source_emt.md"), ("RAMP_CURRENT_SOURCE_EMT", "library/ramp_current_source_emt.md"), ("DOUBLE_EXPONENTIAL_CURRENT_SOURCE_EMT", "library/double_exponential_current_source_emt.md"), ("HEIDLER_CURRENT_SOURCE_EMT", "library/heidler_current_source_emt.md"), ("CIGRE_SURGE_CURRENT_SOURCE_EMT", "library/cigre_surge_current_source_emt.md"), ("R_LOAD_EMT", "library/r_load_emt.md"), ("L_LOAD_EMT", "library/l_load_emt.md"), ("C_LOAD_EMT", "library/c_load_emt.md"), ("RLC_COMBO_EMT", "library/rlc_combo_emt.md"), ("GROUND_EMT", "library/ground_emt.md"), ("GROUNDING_LINK_EMT", "library/grounding_link_emt.md"), ("SWITCH_EMT", "library/switch_emt.md"), ("FAULT_EMT", "EMT/fault.md"), ("NONLINEAR_RESISTOR_EMT", "library/nonlinear_resistor_emt.md"), ("INVERSE_LOOKUP_ARRAY", "library/inverse-lookup-array-object-linear.md"), ("LOOKUP_ARRAY_LINEAR", "library/lookup_array.md"), ("LOOKUP_ARRAY_SPLINE", "library/lookup_array.md"), ("LOOKUP_MATRIX_LINEAR", "library/lookup_matrix.md"), ("LOOKUP_MATRIX_SPLINE", "library/lookup_matrix.md"), ("PI_CURRENT_CONTROLLER", "library/pi_current_controller.md"), ("PI_POWER_CONTROLLER", "library/pi_power_controller.md"), ("PLL_TRANSFORM_RMS", "library/pll_transformer.md"),))
    relative_path: str | None = mapping.get(normalized, None)
    if relative_path is not None:
        return relative_path
    elif normalized_block_name.startswith("COMPLETE_GENERATOR_RMS_TEMPLATE") or \
            normalized_block_name.startswith("COMPLETE_GENERATOR_PHASOR_RMS_TEMPLATE") or \
            normalized_block_name.startswith("COMPLETE_GENERATOR_RMS"):
        return "RMS/complete_generator.md"
    elif normalized_block_name.startswith("COMPLETE_GENERATOR_EMT_TEMPLATE") or \
            normalized_block_name.startswith("COMPLETE_GENERATOR_EMT"):
        return "EMT/complete_generator.md"
    elif normalized_block_name.startswith("GENROW_RMS_TEMPLATE") or \
            normalized_block_name.startswith("GENROU_RMS_TEMPLATE") or \
            normalized_block_name.startswith("GENROU_GENROW"):
        return "RMS/genrou_genrow.md"
    elif normalized_block_name.startswith("LINE_RMS_TEMPLATE"):
        return "RMS/line.md"
    elif normalized_block_name.startswith("LOAD_RMS_TEMPLATE"):
        return "RMS/load.md"
    elif normalized_block_name.startswith("DISTRIBUTED_PV") or \
            normalized_block_name.startswith("PVD1"):
        return "RMS/distributed_pv.md"
    elif normalized_block_name.startswith("ESD1") or \
            normalized_block_name.startswith("BATTERY_RMS"):
        return "RMS/battery.md"
    elif normalized_block_name.startswith("TRANSFORMER2W_RMS") or \
            normalized_block_name.startswith("2W_TRANSFORMER") or \
            normalized_block_name.startswith("RMS_TRAFO_TEMPLATE"):
        return "RMS/2w_transformer.md"
    elif normalized_block_name.startswith("GFM_VSC") or \
            normalized_block_name.startswith("VSC_RMS_TEMPLATE"):
        return "RMS/gfm_vsc.md"
    elif normalized_block_name.startswith("THEVENIN") or \
            normalized_block_name.startswith("EMT_THEVENIN"):
        return "EMT/thevenin_generator.md"
    elif normalized_block_name.startswith("IDEAL_CONVERTER"):
        return "EMT/ideal_converter.md"
    elif normalized_block_name.startswith("FULL_PSEUDO") or \
            normalized_block_name.startswith("PSEUDO_CONVERTER"):
        return "EMT/full_pseudo_converter.md"
    elif normalized_block_name.startswith("SWITCHED_CONVERTER"):
        return "EMT/switched_converter.md"
    elif normalized_block_name.startswith("DC_LOAD"):
        return "EMT/dc_load.md"
    elif normalized_block_name.startswith("DC_LINE"):
        return "EMT/dc_line.md"
    elif normalized_block_name.startswith("TRANSFORMER_EMT_TEMPLATE"):
        return "EMT/transformer.md"
    elif normalized_block_name.startswith("XFMR_EMT_TEMPLATE"):
        return "EMT/xfmr.md"
    elif normalized_block_name.startswith("SHUNT_C") or \
            normalized_block_name.startswith("C_SHUNT"):
        return "EMT/shunt_c_abc.md"
    elif normalized_block_name.startswith("SHUNT_L") or \
            normalized_block_name.startswith("L_SHUNT"):
        return "EMT/shunt_l_abc.md"
    elif normalized_block_name.startswith("SHUNT_R") or \
            normalized_block_name.startswith("R_SHUNT"):
        return "EMT/shunt_r_abc.md"
    elif normalized_block_name.startswith("EXPONENTIAL_LOAD") or \
            normalized_block_name.startswith("EXP_LOAD_EMT"):
        return "EMT/exponential_load_abc.md"
    elif normalized_block_name.startswith("ZIP_LOAD"):
        return "EMT/zip_load_abc.md"
    elif normalized_block_name.startswith("PI_LINE") or normalized_block_name == "PI":
        return "EMT/pi_line_abc.md"
    elif normalized_block_name.startswith("BERGERON_LINE") or normalized_block_name == "BERGERON":
        return "EMT/bergeron_line_abc.md"
    elif normalized_block_name.startswith("SINGLE_CAGE_INDUCTION_MOTOR") or \
            normalized_block_name.startswith("INDUCTION_MOTOR_EMT_TEMPLATE"):
        return "EMT/single_cage_induction_motor.md"
    elif normalized_block_name.startswith("DOUBLE_CAGE_INDUCTION_MOTOR"):
        return "EMT/double_cage_induction_motor.md"
    elif normalized_block_name.startswith("INDUCTION_MOTOR_DOUBLE_CAGE"):
        return "EMT/double_cage_induction_motor.md"
    elif normalized_block_name.startswith("BESS"):
        return "EMT/bess.md"
    elif normalized_block_name.startswith("PV_PLANT") or \
            normalized_block_name.startswith("PV_AVM_GRID_FOLLOWING"):
        return "EMT/pv_plant_grid_following.md"
    elif normalized_block_name.startswith("VSC_GRID_FORMING") or \
            normalized_block_name.startswith("VSC_GRIDFORMING") or \
            normalized_block_name.startswith("GFM_EMT"):
        return "EMT/vsc_grid_forming_gfm.md"
    elif normalized_block_name.startswith("PLL_TRANSFORM_RMS") or \
            normalized_block_name.startswith("PHASE_LOCKED_LOOP"):
        return "library/pll_transformer.md"
    else:
        return None


class TableTextFilterProxyModel(QtCore.QSortFilterProxyModel):
    """Filter a flat table by visible text in any column."""

    __slots__ = ("_search_text",)

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        """Create an initially unfiltered table proxy.

        :param parent: Owning Qt object.
        :return: None.
        """
        super().__init__(parent)
        self._search_text: str = ""

    def set_search_text(self, search_text: str) -> None:
        """Set the case-insensitive text required in a visible row.

        :param search_text: User-entered table query.
        :return: None.
        """
        self._search_text = search_text.strip().lower()
        self.beginFilterChange()
        self.endFilterChange(QtCore.QSortFilterProxyModel.Direction.Rows)

    def filterAcceptsRow(self,
                         source_row: int,
                         source_parent: QtCore.QModelIndex) -> bool:
        """Return whether any source cell contains the current query.

        :param source_row: Candidate source row.
        :param source_parent: Candidate source parent.
        :return: Whether the row matches the query.
        """
        source_model: QtCore.QAbstractItemModel | None = self.sourceModel()
        if len(self._search_text) == 0:
            return True
        elif source_model is None:
            return False
        else:
            pass

        matches: bool = False
        column: int
        for column in range(source_model.columnCount(source_parent)):
            cell_index: QtCore.QModelIndex = source_model.index(source_row, column, source_parent)
            cell_value: object = source_model.data(cell_index, Qt.ItemDataRole.DisplayRole)
            if self._search_text in str(cell_value).lower():
                matches = True
            else:
                pass
        return matches


class BlockSymbolFilterProxyModel(QtCore.QSortFilterProxyModel):
    """Filter the shared symbol draft into variables or parameters."""

    __slots__ = ("_category", "_search_text")

    def __init__(self,
                 category: BlockSymbolCategory,
                 parent: QtCore.QObject | None = None) -> None:
        """Create one category-specific symbol proxy.

        :param category: Visible symbol category.
        :param parent: Owning Qt object.
        :return: None.
        """
        super().__init__(parent)
        self._category: BlockSymbolCategory = category
        self._search_text: str = ""

    def set_search_text(self, search_text: str) -> None:
        """Set the case-insensitive text required in a symbol row.

        :param search_text: User-entered table query.
        :return: None.
        """
        self._search_text = search_text.strip().lower()
        self.beginFilterChange()
        self.endFilterChange(QtCore.QSortFilterProxyModel.Direction.Rows)

    def filterAcceptsRow(self,
                         source_row: int,
                         source_parent: QtCore.QModelIndex) -> bool:
        """Return whether one source symbol belongs in this category.

        :param source_row: Candidate source row.
        :param source_parent: Candidate source parent.
        :return: ``True`` when the symbol belongs in this proxy.
        """
        _unused_source_parent: QtCore.QModelIndex = source_parent
        source_model: QtCore.QAbstractItemModel | None = self.sourceModel()
        if isinstance(source_model, BlockSymbolDraftModel):
            row: BlockSymbolDraftRow | None = source_model.get_row(source_row)
        else:
            row = None

        if row is None:
            return False
        else:
            parameter_kinds: set[BlockSymbolKind] = set((BlockSymbolKind.PARAMETER, BlockSymbolKind.EVENT_PARAMETER,))
            is_runtime_mode: bool = row.get_kind() == BlockSymbolKind.MODE_PARAMETER
            is_parameter: bool = row.get_kind() in parameter_kinds
            if is_runtime_mode:
                category_matches: bool = False
            elif self._category == BlockSymbolCategory.PARAMETERS:
                category_matches = is_parameter
            else:
                category_matches = not is_parameter

        if not category_matches:
            return False
        elif len(self._search_text) == 0:
            return True
        else:
            pass

        column: int
        for column in range(source_model.columnCount(source_parent)):
            source_index: QtCore.QModelIndex = source_model.index(source_row, column, source_parent)
            source_value: object = source_model.data(source_index, Qt.ItemDataRole.DisplayRole)
            if self._search_text in str(source_value).lower():
                return True
            else:
                pass
        return False

    def headerData(self,
                   section: int,
                   orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole) -> object:
        """Return the mapping title and explanation for this symbol category.

        :param section: Requested proxy column.
        :param orientation: Header orientation.
        :param role: Requested Qt data role.
        :return: Category-specific mapping header or source-model data.
        """
        if section == 4 and orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                if self._category == BlockSymbolCategory.PARAMETERS:
                    result: object = self.tr("Static parameter mapping")
                else:
                    result = self.tr("Power-flow derived initialization")
            elif role == Qt.ItemDataRole.ToolTipRole:
                if self._category == BlockSymbolCategory.PARAMETERS:
                    result = self.tr(
                        "Maps a static parameter through ParamPowerFlowReferenceType "
                        "to block.api_obj_mapping. Dynamic parameters are not editable here."
                    )
                else:
                    result = self.tr(
                        "Initializes a variable through VarPowerFlowReferenceType "
                        "and block.external_mapping."
                    )
            else:
                result = super().headerData(section, orientation, role)
        else:
            result = super().headerData(section, orientation, role)
        return result

class DynamicBlockPropertiesDialog(QtWidgets.QDialog):
    """Property editor content for one Dynamic Model Editor block."""

    # Symbolic UIDs are wider than Qt's 32-bit ``int`` signal type.
    blockApplied = Signal(object)
    structuralRebuildRequested = Signal(object)
    variableRenameRequested = Signal(object)
    outputExportChangesRequested = Signal(object)
    closeRequested = Signal()

    __slots__ = (
        "ui",
        "_block",
        "_block_type_name",
        "_structural_block_type",
        "_structural_builder",
        "_general_structural_model",
        "_special_structural_model",
        "_var_factory",
        "_parameter_model",
        "_general_parameter_proxy",
        "_general_parameter_search",
        "_general_parameter_table",
        "_symbol_model",
        "_runtime_logic_editor",
        "_variable_symbol_proxy",
        "_parameter_symbol_proxy",
        "_symbol_table",
        "_parameter_symbol_table",
        "_variable_symbol_search",
        "_parameter_symbol_search",
        "_new_symbol_owner",
        "_new_symbol_name",
        "_new_symbol_category",
        "_new_symbol_kind",
        "_new_symbol_exported",
        "_new_state_derivative",
        "_new_variable_options",
        "_new_parameter_value",
        "_new_parameter_value_label",
        "_new_external_reference",
        "_new_external_reference_label",
        "_new_static_reference",
        "_new_static_reference_label",
        "_add_symbol_button",
        "_namespace",
        "_tabs",
        "_equation_buffers",
        "_equation_owner_combo",
        "_active_equation_buffer_index",
        "_loading_equation_buffer",
        "_dae_editor",
        "_dae_code_search",
        "_dae_search_previous_button",
        "_dae_search_next_button",
        "_dae_search_status",
        "_dae_highlighter",
        "_validate_code_button",
        "_dae_splitter",
        "_symbol_panel_splitter",
        "_latex_model",
        "_latex_selection_tree",
        "_latex_select_all_button",
        "_latex_clear_button",
        "_latex_source_preview",
        "_export_rendered_button",
        "_block_documentation_url",
        "_block_info_button",
        "_dock_hosted",
        "_prepared_to_delete",
        "_status_label",
        "_apply_button",
    )

    def __init__(self,
                 block: Block,
                 block_type_name: str,
                 var_factory: VarFactory,
                 parent: QtWidgets.QWidget | None = None,
                 structural_block_type: BlockType | None = None,
                 structural_builder: TemplateDefinition | None = None) -> None:
        """
        Create the modal around a detached parameter and equation draft.

        :param block: Symbolic block used by the operation.
        :param block_type_name: Value supplied for ``block_type_name``.
        :param var_factory: Factory that owns symbolic variables.
        :param parent: Owning Qt widget.
        :param structural_block_type: Value supplied for ``structural_block_type``.
        :param structural_builder: Value supplied for ``structural_builder``.
        :return: None.
        """
        super().__init__(parent)
        # Keep the stable dialogue frame in the Qt Designer form, matching the
        # static TemplateDeviceEditor architecture. Block-dependent pages are
        # inserted afterwards because their number and contents are dynamic.
        self.ui: Ui_DynamicBlockPropertiesDialog = Ui_DynamicBlockPropertiesDialog()
        self.ui.setupUi(self)
        # Direct test and tooling call sites do not necessarily pass through the
        # editor wrapper that used to set this attribute. Make ownership
        # deterministic at the dialogue boundary so Qt destroys the complete
        # child tree when the modal closes.
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self._block: Block = block
        self._block_type_name: str = block_type_name
        self._structural_block_type: BlockType | None = structural_block_type
        self._structural_builder: TemplateDefinition | None = structural_builder
        general_structural_properties: List[TemplateProp] = list()
        special_structural_properties: List[TemplateProp] = list()
        if structural_builder is not None:
            general_structural_properties, special_structural_properties = split_structural_template_properties(
                structural_builder
            )
        else:
            pass
        self._general_structural_model: BlockStructuralSettingsModel = BlockStructuralSettingsModel(
            general_structural_properties,
            self,
        )
        self._special_structural_model: BlockStructuralSettingsModel = BlockStructuralSettingsModel(
            special_structural_properties,
            self,
        )
        self._var_factory: VarFactory = var_factory
        self._parameter_model: BlockParameterDraftModel = BlockParameterDraftModel(block, self)
        self._general_parameter_proxy: TableTextFilterProxyModel = TableTextFilterProxyModel(self)
        self._general_parameter_proxy.setSourceModel(self._parameter_model)
        self._general_parameter_search: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        self._general_parameter_search.setClearButtonEnabled(True)
        self._general_parameter_search.setPlaceholderText(self.tr("Search parameters..."))
        self._general_parameter_table: QtWidgets.QTableView = QtWidgets.QTableView(self)
        self._symbol_model: BlockSymbolDraftModel = BlockSymbolDraftModel(block, self)
        self._variable_symbol_proxy: BlockSymbolFilterProxyModel = BlockSymbolFilterProxyModel(
            BlockSymbolCategory.VARIABLES,
            self,
        )
        self._variable_symbol_proxy.setSourceModel(self._symbol_model)
        self._parameter_symbol_proxy: BlockSymbolFilterProxyModel = BlockSymbolFilterProxyModel(
            BlockSymbolCategory.PARAMETERS,
            self,
        )
        self._parameter_symbol_proxy.setSourceModel(self._symbol_model)
        self._symbol_table: QtWidgets.QTableView = QtWidgets.QTableView(self)
        self._parameter_symbol_table: QtWidgets.QTableView = QtWidgets.QTableView(self)
        self._variable_symbol_search: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        self._variable_symbol_search.setClearButtonEnabled(True)
        self._variable_symbol_search.setPlaceholderText(self.tr("Search variables..."))
        self._parameter_symbol_search: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        self._parameter_symbol_search.setClearButtonEnabled(True)
        self._parameter_symbol_search.setPlaceholderText(self.tr("Search parameters..."))
        self._new_symbol_owner: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        self._new_symbol_name: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        self._new_symbol_category: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        self._new_symbol_kind: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        self._new_symbol_exported: QtWidgets.QCheckBox = QtWidgets.QCheckBox(self.tr("Output"), self)
        self._new_state_derivative: QtWidgets.QCheckBox = QtWidgets.QCheckBox(
            self.tr("Create derivative variable"), self
        )
        self._new_variable_options: QtWidgets.QWidget = QtWidgets.QWidget(self)
        self._new_parameter_value: QtWidgets.QDoubleSpinBox = QtWidgets.QDoubleSpinBox(self)
        self._new_parameter_value.setDecimals(12)
        self._new_parameter_value.setRange(-1.0e100, 1.0e100)
        self._new_parameter_value_label: QtWidgets.QLabel = QtWidgets.QLabel(
            self.tr("Initial numeric value"), self
        )
        self._new_external_reference: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        self._new_external_reference.setEditable(True)
        self._new_external_reference.addItem(self.tr("None"), None)
        external_reference: VarPowerFlowReferenceType
        for external_reference in VarPowerFlowReferenceType:
            self._new_external_reference.addItem(
                f"VarPowerFlowReferenceType.{external_reference.name}",
                external_reference,
            )
        self._new_external_reference_label: QtWidgets.QLabel = QtWidgets.QLabel(
            self.tr("Power-flow variable"), self
        )
        self._new_external_reference_label.setToolTip(
            self.tr("Power-flow variable used to initialize this dynamic variable.")
        )
        self._new_static_reference: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        self._new_static_reference.setEditable(True)
        self._new_static_reference_label: QtWidgets.QLabel = QtWidgets.QLabel(
            self.tr("Static device mapping"), self
        )
        self._add_symbol_button: QtWidgets.QPushButton = QtWidgets.QPushButton(self.tr("Add symbol"), self)
        self._namespace: Dict[str, Expr] = build_block_symbol_namespace(block)
        self._runtime_logic_editor: RuntimeLogicEditorWidget = RuntimeLogicEditorWidget(
            block,
            self._namespace,
            self,
        )
        self._namespace = self._runtime_logic_editor.build_validation_namespace(self._namespace)
        self._tabs: QtWidgets.QTabWidget = self.ui.tab_widget
        self._equation_buffers: List[BlockCodeBuffer] = list()
        child_block: Block
        for child_block in block.get_all_blocks():
            self._equation_buffers.append(BlockCodeBuffer(child_block))
        self._equation_owner_combo: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        self._active_equation_buffer_index: int = self._find_initial_equation_buffer_index()
        self._loading_equation_buffer: bool = False
        self._dae_editor: DaeCodeEditor = DaeCodeEditor(self, self._namespace)
        self._dae_code_search: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        self._dae_code_search.setClearButtonEnabled(True)
        self._dae_code_search.setPlaceholderText(self.tr("Search Python code..."))
        self._dae_search_previous_button: QtWidgets.QToolButton = QtWidgets.QToolButton(self)
        self._dae_search_previous_button.setText(self.tr("Previous"))
        self._dae_search_previous_button.setEnabled(False)
        self._dae_search_next_button: QtWidgets.QToolButton = QtWidgets.QToolButton(self)
        self._dae_search_next_button.setText(self.tr("Next"))
        self._dae_search_next_button.setEnabled(False)
        self._dae_search_status: QtWidgets.QLabel = QtWidgets.QLabel(self)
        self._dae_highlighter: DaeCodeHighlighter = DaeCodeHighlighter(
            self._dae_editor.document(),
            tuple(self._namespace.keys()),
        )
        self._validate_code_button: QtWidgets.QPushButton = QtWidgets.QPushButton(
            self.tr("Validate all code"), self
        )
        self._dae_splitter: QtWidgets.QSplitter = QtWidgets.QSplitter(Qt.Orientation.Horizontal, self)
        self._symbol_panel_splitter: QtWidgets.QSplitter = QtWidgets.QSplitter(
            Qt.Orientation.Vertical,
            self,
        )
        initial_equation_block: Block = self._equation_buffers[self._active_equation_buffer_index].get_block()
        initial_draft: BlockEquationDraft = BlockEquationDraft(
            initial_equation_block.state_eqs,
            initial_equation_block.algebraic_eqs,
            initial_equation_block.init_eqs,
            initial_equation_block.diff_init_eqs,
        )
        self._latex_model: EquationLatexModel = EquationLatexModel(initial_draft, self)
        self._latex_selection_tree: QtWidgets.QTreeWidget = QtWidgets.QTreeWidget(self)
        self._latex_select_all_button: QtWidgets.QPushButton = QtWidgets.QPushButton(self.tr("Select all"), self)
        self._latex_clear_button: QtWidgets.QPushButton = QtWidgets.QPushButton(self.tr("Clear"), self)
        self._latex_source_preview: QtWidgets.QPlainTextEdit = QtWidgets.QPlainTextEdit(self)
        self._latex_source_preview.setReadOnly(True)
        self._latex_source_preview.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        self._latex_source_preview.setFont(self._dae_editor.font())
        self._latex_source_preview.setPlaceholderText(
            self.tr("Select equation groups to generate copyable LaTeX source.")
        )
        self._export_rendered_button: QtWidgets.QPushButton = QtWidgets.QPushButton(
            self.tr("Download rendered PDF"), self
        )
        self._block_documentation_url: str | None = resolve_block_documentation_url(
            block_type_name,
            block.name,
        )
        self._block_info_button: QtWidgets.QPushButton = QtWidgets.QPushButton(
            self.tr("Block info"),
            self,
        )
        self._dock_hosted: bool = False
        self._prepared_to_delete: bool = False
        self._status_label: QtWidgets.QLabel = self.ui.status_label
        self._apply_button: QtWidgets.QPushButton = self.ui.apply_button
        self._build_ui()
        self._connect_signals()
        self._clear_dae_validation_feedback()

    def prepare_to_delete(self) -> None:
        """Detach Qt models and document resources before binary destruction.

        PySide wrappers may outlive their C++ children until Python performs a
        later garbage-collection pass. Explicitly sever the model/view and
        document relationships while every object is still valid.

        :return: None.
        """
        if self._prepared_to_delete:
            pass
        else:
            self._prepared_to_delete = True
            self._runtime_logic_editor.prepare_to_delete()
            self._general_parameter_table.setModel(None)
            self._symbol_table.setModel(None)
            self._parameter_symbol_table.setModel(None)
            self._general_parameter_proxy.setSourceModel(None)
            self._variable_symbol_proxy.setSourceModel(None)
            self._parameter_symbol_proxy.setSourceModel(None)
            self._dae_highlighter.setDocument(None)
            self._latex_selection_tree.clear()
            self._equation_owner_combo.clear()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Release owned Qt resources before accepting the close event.

        :param event: Incoming close event.
        :return: None.
        """
        self.prepare_to_delete()
        QtWidgets.QDialog.closeEvent(self, event)

    def set_dock_hosted(self, dock_hosted: bool) -> None:
        """Select whether close requests must be delegated to a dock host.

        :param dock_hosted: Whether a :class:`QDockWidget` owns this content.
        :return: None.
        """
        self._dock_hosted = dock_hosted
        self.setModal(not dock_hosted)

    def request_close(self) -> None:
        """Close the standalone dialogue or ask its dock host to close.

        :return: None.
        """
        if self._dock_hosted:
            self.closeRequested.emit()
        else:
            self.close()

    def _find_initial_equation_buffer_index(self) -> int:
        """
        Prefer the first recursive block that contains editable equations.

        :return: Index of the first recursive block containing editable equations.
        """
        result: int = 0
        index: int
        buffer: BlockCodeBuffer
        found: bool = False
        for index, buffer in enumerate(self._equation_buffers):
            candidate: Block = buffer.get_block()
            has_supported_content: bool = bool(
                candidate.state_eqs
                or candidate.algebraic_eqs
                or candidate.init_eqs
                or candidate.diff_init_eqs
            )
            if has_supported_content and not found:
                result = index
                found = True
            else:
                pass
        return result

    def _build_ui(self) -> None:
        """
        Populate the Designer-owned frame with block-dependent pages.

        :return: None.
        """
        self.setWindowTitle(self.tr("Block properties - {name}").format(name=self._block.name))
        self.setModal(True)

        general_page: QtWidgets.QWidget = self._build_general_page()
        dae_page: QtWidgets.QWidget = self._build_dae_page()
        runtime_page: QtWidgets.QWidget = self._runtime_logic_editor
        general_index: int = self._tabs.addTab(general_page, self.tr("General options"))
        dae_index: int = self._tabs.addTab(dae_page, self.tr("DAE model"))
        runtime_index: int = self._tabs.addTab(runtime_page, self.tr("Runtime logic"))
        self._tabs.setTabIcon(general_index, QtGui.QIcon(":/Icons/icons/gear.png"))
        self._tabs.setTabIcon(dae_index, QtGui.QIcon(":/Icons/icons/edit.png"))
        self._tabs.setTabIcon(runtime_index, QtGui.QIcon())
        if self._special_structural_model.rowCount() > 0:
            special_page: QtWidgets.QWidget = self._build_special_settings_page()
            special_index: int = self._tabs.addTab(special_page, self.tr("Special settings"))
            self._tabs.setTabIcon(special_index, QtGui.QIcon(":/Icons/icons/gear.png"))
        else:
            pass

    def _build_general_page(self) -> QtWidgets.QWidget:
        """
        Build block identity, configuration, and numeric parameter controls.

        :return: Page containing block identity, configuration, and numeric parameter controls.
        """
        page: QtWidgets.QWidget = QtWidgets.QWidget(self)
        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(page)
        identity_group: QtWidgets.QGroupBox = QtWidgets.QGroupBox(self.tr("Block configuration"), page)
        identity_layout: QtWidgets.QFormLayout = QtWidgets.QFormLayout(identity_group)
        identity_layout.addRow(self.tr("Name"), QtWidgets.QLabel(self._block.name, identity_group))
        identity_layout.addRow(self.tr("Catalogue type"), QtWidgets.QLabel(self._block_type_name, identity_group))
        identity_layout.addRow(self.tr("Inputs"), QtWidgets.QLabel(str(len(self._block.in_vars)), identity_group))
        identity_layout.addRow(self.tr("Outputs"), QtWidgets.QLabel(str(len(self._block.out_vars)), identity_group))
        identity_layout.addRow(
            self.tr("Advanced runtime logic"),
            QtWidgets.QLabel(build_advanced_logic_summary(self._block), identity_group),
        )
        # Online documentation describes the immutable library definition. It
        # remains useful for edited instances, but the tooltip must make clear
        # that local equations and symbols can intentionally differ from it.
        self._block_info_button.setIcon(QtGui.QIcon(":/Icons/icons/message.png"))
        if self._block_documentation_url is None:
            self._block_info_button.setEnabled(False)
            documentation_tooltip: str = self.tr(
                "No online catalogue documentation is available for this custom block."
            )
        else:
            self._block_info_button.setEnabled(True)
            documentation_tooltip = self.tr(
                "Opens the documentation for the original predefined library block. "
                "If this block has been modified in the editor, its current equations, symbols, "
                "parameters, or runtime logic may differ from the online documentation."
            )
        self._block_info_button.setToolTip(documentation_tooltip)
        self._block_info_button.setWhatsThis(documentation_tooltip)
        # QFormLayout otherwise expands the field widget across the complete
        # row and centres the button contents. Keep this action compact and
        # anchored directly beside its descriptive label.
        self._block_info_button.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self._block_info_button.setFixedWidth(self._block_info_button.sizeHint().width())
        documentation_button_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        documentation_button_layout.setContentsMargins(0, 0, 0, 0)
        documentation_button_layout.addWidget(self._block_info_button)
        documentation_button_layout.addStretch(1)
        identity_layout.addRow(self.tr("Online documentation"), documentation_button_layout)
        layout.addWidget(identity_group)

        if self._general_structural_model.rowCount() > 0:
            structure_group: QtWidgets.QGroupBox = QtWidgets.QGroupBox(
                self.tr("Generated structure"),
                page,
            )
            structure_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(structure_group)
            structure_table: QtWidgets.QTableView = QtWidgets.QTableView(structure_group)
            structure_table.setModel(self._general_structural_model)
            structure_table.setItemDelegateForColumn(1, StructuralSettingDelegate(structure_table))
            structure_table.setAlternatingRowColors(True)
            structure_header: QtWidgets.QHeaderView = structure_table.horizontalHeader()
            configure_interactive_table_header(structure_header, list((300, 620,)))
            structure_layout.addWidget(structure_table)
            layout.addWidget(structure_group)
        else:
            pass

        parameters_group: QtWidgets.QGroupBox = QtWidgets.QGroupBox(self.tr("Parameters"), page)
        parameters_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(parameters_group)
        parameters_layout.addWidget(self._general_parameter_search)
        self._general_parameter_table.setParent(parameters_group)
        self._general_parameter_table.setModel(self._general_parameter_proxy)
        parameter_header: QtWidgets.QHeaderView = self._general_parameter_table.horizontalHeader()
        configure_interactive_table_header(parameter_header, list((270, 520, 180,)))
        self._general_parameter_table.setAlternatingRowColors(True)
        self._general_parameter_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        parameters_layout.addWidget(self._general_parameter_table)
        layout.addWidget(parameters_group, 1)
        return page

    def _build_special_settings_page(self) -> QtWidgets.QWidget:
        """
        Build complex lookup and model-specific builder settings.

        :return: Page containing complex lookup and model-specific builder settings.
        """
        page: QtWidgets.QWidget = QtWidgets.QWidget(self)
        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(page)
        description: QtWidgets.QLabel = QtWidgets.QLabel(
            self.tr(
                "These settings contain structured data used to regenerate the block. "
                "Edit sequences with valid Python tuple/list syntax."
            ),
            page,
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        settings_table: QtWidgets.QTableView = QtWidgets.QTableView(page)
        settings_table.setModel(self._special_structural_model)
        settings_table.setItemDelegateForColumn(1, StructuralSettingDelegate(settings_table))
        settings_table.setAlternatingRowColors(True)
        settings_header: QtWidgets.QHeaderView = settings_table.horizontalHeader()
        configure_interactive_table_header(settings_header, list((320, 760,)))
        layout.addWidget(settings_table, 1)
        return page

    def _build_dae_page(self) -> QtWidgets.QWidget:
        """
        Build the resizable symbol browser and Python/LaTeX tools.

        :return: Page containing the resizable symbol browser and Python/LaTeX tools.
        """
        page: QtWidgets.QWidget = QtWidgets.QWidget(self)
        layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout(page)
        symbol_panel: QtWidgets.QWidget = self._build_symbol_panel(page)
        self._dae_splitter.addWidget(symbol_panel)

        equation_tabs: QtWidgets.QTabWidget = QtWidgets.QTabWidget(self._dae_splitter)
        python_page: QtWidgets.QWidget = QtWidgets.QWidget(equation_tabs)
        python_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(python_page)
        owner_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        owner_layout.addWidget(QtWidgets.QLabel(self.tr("Equation owner"), python_page))
        buffer_index: int
        buffer: BlockCodeBuffer
        for buffer_index, buffer in enumerate(self._equation_buffers):
            owner_block: Block = buffer.get_block()
            owner_label: str = f"{owner_block.name} [{buffer_index + 1}]"
            self._equation_owner_combo.addItem(owner_label, buffer_index)
        self._equation_owner_combo.setCurrentIndex(self._active_equation_buffer_index)
        owner_layout.addWidget(self._equation_owner_combo, 1)
        python_layout.addLayout(owner_layout)
        code_search_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        code_search_layout.addWidget(self._dae_code_search, 1)
        code_search_layout.addWidget(self._dae_search_status)
        code_search_layout.addWidget(self._dae_search_previous_button)
        code_search_layout.addWidget(self._dae_search_next_button)
        python_layout.addLayout(code_search_layout)
        self._dae_editor.setPlainText(self._equation_buffers[self._active_equation_buffer_index].get_code())
        self._dae_editor.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        fixed_font: QtGui.QFont = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.SystemFont.FixedFont)
        self._dae_editor.setFont(fixed_font)
        self._dae_editor.update_line_number_area_width(0)
        python_layout.addWidget(self._dae_editor, 1)
        validation_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        validation_layout.addStretch(1)
        self._validate_code_button.setIcon(QtGui.QIcon(":/Icons/icons/accept.png"))
        validation_layout.addWidget(self._validate_code_button)
        python_layout.addLayout(validation_layout)
        equation_tabs.addTab(python_page, self.tr("Python code"))

        latex_page: QtWidgets.QWidget = self._build_latex_export_page(equation_tabs)
        equation_tabs.addTab(latex_page, self.tr("LaTeX"))
        self._dae_splitter.addWidget(equation_tabs)
        # Keep the initial and resized layout close to one third symbols and
        # two thirds equation tools. The handle remains fully interactive.
        self._dae_splitter.setStretchFactor(0, 1)
        self._dae_splitter.setStretchFactor(1, 2)
        self._dae_splitter.setCollapsible(0, False)
        self._dae_splitter.setCollapsible(1, False)
        self._dae_splitter.setSizes(list((480, 960,)))
        layout.addWidget(self._dae_splitter, 1)
        return page

    def _build_latex_export_page(self, parent: QtWidgets.QWidget) -> QtWidgets.QWidget:
        """Build equation selection, copyable source, and rendered PDF export.

        :param parent: Parent equation-tab widget.
        :return: Configured LaTeX export page.
        """
        page: QtWidgets.QWidget = QtWidgets.QWidget(parent)
        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(page)

        # The equation selection and generated source have independent useful
        # heights. A vertical splitter lets the user allocate the available
        # space according to whether they are selecting or copying equations.
        latex_splitter: QtWidgets.QSplitter = QtWidgets.QSplitter(
            Qt.Orientation.Vertical,
            page,
        )
        latex_splitter.setChildrenCollapsible(False)
        latex_splitter.setHandleWidth(6)

        selection_panel: QtWidgets.QWidget = QtWidgets.QWidget(latex_splitter)
        selection_panel_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(selection_panel)
        selection_panel_layout.setContentsMargins(0, 0, 0, 0)
        explanation: QtWidgets.QLabel = QtWidgets.QLabel(
            self.tr(
                "Select the equation groups to include. Each internal block and each DAE section "
                "can be selected independently."
            ),
            selection_panel,
        )
        explanation.setWordWrap(True)
        selection_panel_layout.addWidget(explanation)

        self._latex_selection_tree.setColumnCount(2)
        self._latex_selection_tree.setHeaderLabels(list((self.tr("Block / equation group"), self.tr("Equations"),)))
        self._latex_selection_tree.setAlternatingRowColors(True)
        configure_interactive_table_header(
            self._latex_selection_tree.header(),
            list((640, 170,)),
        )
        selection_panel_layout.addWidget(self._latex_selection_tree, 1)
        self._rebuild_latex_selection_tree()

        selection_button_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        selection_button_layout.addWidget(self._latex_select_all_button)
        selection_button_layout.addWidget(self._latex_clear_button)
        selection_button_layout.addStretch(1)
        selection_panel_layout.addLayout(selection_button_layout)

        source_panel: QtWidgets.QWidget = QtWidgets.QWidget(latex_splitter)
        source_panel_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(source_panel)
        source_panel_layout.setContentsMargins(0, 0, 0, 0)

        source_label: QtWidgets.QLabel = QtWidgets.QLabel(
            self.tr("LaTeX source"),
            source_panel,
        )
        source_panel_layout.addWidget(source_label)
        source_panel_layout.addWidget(self._latex_source_preview, 1)

        export_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        self._export_rendered_button.setIcon(QtGui.QIcon(":/Icons/icons/download.png"))
        export_layout.addStretch(1)
        export_layout.addWidget(self._export_rendered_button)
        source_panel_layout.addLayout(export_layout)

        latex_splitter.addWidget(selection_panel)
        latex_splitter.addWidget(source_panel)
        latex_splitter.setStretchFactor(0, 2)
        latex_splitter.setStretchFactor(1, 1)
        latex_splitter.setSizes(list((420, 230,)))
        layout.addWidget(latex_splitter, 1)
        return page

    def _build_symbol_panel(self, parent: QtWidgets.QWidget) -> QtWidgets.QWidget:
        """
        Build the editable recursive variable and parameter table.

        :param parent: Owning Qt widget.
        :return: Panel containing the editable recursive variable and parameter table.
        """
        panel: QtWidgets.QWidget = QtWidgets.QWidget(parent)
        # A compact minimum lets the splitter genuinely trade space between
        # symbols and source code. Horizontal scrolling remains available only
        # after the user deliberately makes this panel narrower.
        panel.setMinimumWidth(260)
        panel_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(panel)

        symbol_tabs: QtWidgets.QTabWidget = QtWidgets.QTabWidget(panel)
        variable_page: QtWidgets.QWidget = QtWidgets.QWidget(symbol_tabs)
        variable_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(variable_page)
        variable_layout.setContentsMargins(0, 0, 0, 0)
        variable_layout.addWidget(self._variable_symbol_search)
        self._symbol_table.setModel(self._variable_symbol_proxy)
        self._symbol_table.setItemDelegateForColumn(2, SymbolKindDelegate(self._symbol_table))
        self._symbol_table.setItemDelegateForColumn(4, SymbolMappingDelegate(self._symbol_table))
        self._symbol_table.setAlternatingRowColors(True)
        self._symbol_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self._symbol_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self._symbol_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._symbol_table.verticalHeader().setVisible(False)
        symbol_header: QtWidgets.QHeaderView = self._symbol_table.horizontalHeader()
        configure_interactive_table_header(
            symbol_header,
            list((65, 55, 80, 50, 110,)),
        )
        variable_layout.addWidget(self._symbol_table, 1)
        symbol_tabs.addTab(variable_page, self.tr("Variables"))

        parameter_page: QtWidgets.QWidget = QtWidgets.QWidget(symbol_tabs)
        parameter_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(parameter_page)
        parameter_layout.setContentsMargins(0, 0, 0, 0)
        parameter_layout.addWidget(self._parameter_symbol_search)
        self._parameter_symbol_table.setModel(self._parameter_symbol_proxy)
        self._parameter_symbol_table.setItemDelegateForColumn(
            2,
            SymbolKindDelegate(self._parameter_symbol_table),
        )
        self._parameter_symbol_table.setItemDelegateForColumn(
            4,
            SymbolMappingDelegate(self._parameter_symbol_table),
        )
        self._parameter_symbol_table.setAlternatingRowColors(True)
        self._parameter_symbol_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._parameter_symbol_table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        self._parameter_symbol_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._parameter_symbol_table.verticalHeader().setVisible(False)
        # Parameters reuse the staged symbol source model, but configuration
        # constants can never be output ports. Hide the interface-only column
        # instead of presenting a meaningless empty checkbox column.
        self._parameter_symbol_table.setColumnHidden(3, True)
        parameter_symbol_header: QtWidgets.QHeaderView = self._parameter_symbol_table.horizontalHeader()
        configure_interactive_table_header(
            parameter_symbol_header,
            list((65, 55, 80, 50, 110,)),
        )
        parameter_layout.addWidget(self._parameter_symbol_table, 1)
        symbol_tabs.addTab(parameter_page, self.tr("Parameters"))
        add_group: QtWidgets.QGroupBox = QtWidgets.QGroupBox(self.tr("Add symbol to selected block"), panel)
        add_layout: QtWidgets.QGridLayout = QtWidgets.QGridLayout(add_group)
        add_layout.setContentsMargins(6, 4, 6, 4)
        add_layout.setHorizontalSpacing(6)
        add_layout.setVerticalSpacing(3)
        block_index: int
        child_block: Block
        for block_index, child_block in enumerate(self._block.get_all_blocks()):
            owner_label: str = f"{child_block.name} [{block_index + 1}]"
            self._new_symbol_owner.addItem(owner_label, child_block)
        self._new_symbol_name.setPlaceholderText(self.tr("Enter a name"))
        self._new_symbol_category.addItem(BlockSymbolCategory.VARIABLES.value, BlockSymbolCategory.VARIABLES)
        self._new_symbol_category.addItem(BlockSymbolCategory.PARAMETERS.value, BlockSymbolCategory.PARAMETERS)

        variable_options_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout(
            self._new_variable_options
        )
        variable_options_layout.setContentsMargins(0, 0, 0, 0)
        variable_options_layout.addWidget(self._new_symbol_exported)
        variable_options_layout.addWidget(self._new_state_derivative)
        variable_options_layout.addStretch(1)
        parameter_reference: ParamPowerFlowReferenceType
        for parameter_reference in ParamPowerFlowReferenceType:
            self._new_static_reference.addItem(
                f"ParamPowerFlowReferenceType.{parameter_reference.name}",
                parameter_reference,
            )

        # Every field is placed in the same grid column. Keeping the optional
        # controls out of nested form layouts prevents their label widths from
        # moving or resizing all combo boxes when the symbol category changes.
        field_widgets: tuple[QtWidgets.QWidget, ...] = (
            self._new_symbol_owner,
            self._new_symbol_name,
            self._new_symbol_category,
            self._new_symbol_kind,
            self._new_parameter_value,
            self._new_static_reference,
            self._new_external_reference,
        )
        field_widget: QtWidgets.QWidget
        for field_widget in field_widgets:
            field_widget.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Fixed,
            )

        label_widgets: tuple[QtWidgets.QLabel, ...] = (
            self._new_parameter_value_label,
            self._new_static_reference_label,
            self._new_external_reference_label,
        )
        shared_label_width: int = 0
        label_widget: QtWidgets.QLabel
        for label_widget in label_widgets:
            shared_label_width = max(shared_label_width, label_widget.sizeHint().width())
        add_layout.setColumnMinimumWidth(0, shared_label_width)
        add_layout.setColumnStretch(1, 1)

        add_layout.addWidget(QtWidgets.QLabel(self.tr("Owner block"), add_group), 0, 0)
        add_layout.addWidget(self._new_symbol_owner, 0, 1)
        add_layout.addWidget(QtWidgets.QLabel(self.tr("New symbol name"), add_group), 1, 0)
        add_layout.addWidget(self._new_symbol_name, 1, 1)
        add_layout.addWidget(QtWidgets.QLabel(self.tr("Symbol category"), add_group), 2, 0)
        add_layout.addWidget(self._new_symbol_category, 2, 1)
        add_layout.addWidget(QtWidgets.QLabel(self.tr("Type"), add_group), 3, 0)
        add_layout.addWidget(self._new_symbol_kind, 3, 1)
        add_layout.addWidget(self._new_variable_options, 4, 0, 1, 2)
        add_layout.addWidget(self._new_parameter_value_label, 4, 0)
        add_layout.addWidget(self._new_parameter_value, 4, 1)
        add_layout.addWidget(self._new_static_reference_label, 4, 0)
        add_layout.addWidget(self._new_static_reference, 4, 1)
        add_layout.addWidget(self._new_external_reference_label, 5, 0)
        add_layout.addWidget(self._new_external_reference, 5, 1)
        # Optional rows have different visibility by symbol kind. A dedicated
        # expanding row absorbs that height difference so the stable fields at
        # the top never move when Variables and Parameters are exchanged.
        form_spacer: QtWidgets.QSpacerItem = QtWidgets.QSpacerItem(
            0,
            0,
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        add_layout.addItem(form_spacer, 6, 0, 1, 2)
        add_layout.setRowStretch(6, 1)
        add_layout.addWidget(self._add_symbol_button, 7, 0, 1, 2)
        # The user can trade form height for table height. This is deliberately
        # a vertical splitter inside the horizontally resizable DAE page, so
        # both dimensions remain independently adjustable.
        self._symbol_panel_splitter.addWidget(symbol_tabs)
        self._symbol_panel_splitter.addWidget(add_group)
        self._symbol_panel_splitter.setStretchFactor(0, 1)
        self._symbol_panel_splitter.setStretchFactor(1, 0)
        self._symbol_panel_splitter.setCollapsible(0, False)
        self._symbol_panel_splitter.setCollapsible(1, False)
        self._symbol_panel_splitter.setSizes(list((560, 190,)))
        panel_layout.addWidget(self._symbol_panel_splitter, 1)
        self.update_new_symbol_category()
        self.update_new_symbol_controls()
        return panel

    def _connect_signals(self) -> None:
        """
        Connect actions with explicit named slots.

        :return: None.
        """
        self._apply_button.clicked.connect(self.apply_changes)
        self._block_info_button.clicked.connect(self.open_block_documentation)
        self._validate_code_button.clicked.connect(self.validate_complete_dae_code)
        self._dae_editor.textChanged.connect(self.on_dae_code_changed)
        self._equation_owner_combo.currentIndexChanged.connect(self.on_equation_owner_changed)
        self._new_symbol_category.currentIndexChanged.connect(self.update_new_symbol_category)
        self._new_symbol_kind.currentIndexChanged.connect(self.update_new_symbol_controls)
        self._add_symbol_button.clicked.connect(self.add_staged_symbol)
        self._symbol_model.dataChanged.connect(self.on_symbol_draft_changed)
        self._runtime_logic_editor.changed.connect(self.on_runtime_logic_changed)
        self._symbol_table.customContextMenuRequested.connect(self.show_variable_context_menu)
        self._parameter_symbol_table.customContextMenuRequested.connect(self.show_parameter_context_menu)
        self._general_parameter_search.textChanged.connect(self.filter_general_parameters)
        self._variable_symbol_search.textChanged.connect(self.filter_variables)
        self._parameter_symbol_search.textChanged.connect(self.filter_parameters)
        self._dae_code_search.textChanged.connect(self.update_dae_code_search)
        self._dae_code_search.returnPressed.connect(self.find_next_dae_code_match)
        self._dae_search_previous_button.clicked.connect(self.find_previous_dae_code_match)
        self._dae_search_next_button.clicked.connect(self.find_next_dae_code_match)
        self._latex_select_all_button.clicked.connect(self.select_all_latex_sections)
        self._latex_clear_button.clicked.connect(self.clear_latex_sections)
        self._latex_selection_tree.itemChanged.connect(self.on_latex_selection_changed)
        self._export_rendered_button.clicked.connect(self.export_rendered_equations_pdf)

    @QtCore.Slot()
    def open_block_documentation(self) -> None:
        """Open the original library block documentation in the system browser.

        :return: None.
        """
        if self._block_documentation_url is None:
            # This branch also protects programmatic calls made while the
            # corresponding UI button is disabled for a custom block.
            self._status_label.setStyleSheet("color: #b42318;")
            self._status_label.setText(
                self.tr("No online catalogue documentation is available for this custom block.")
            )
        else:
            documentation_url: QtCore.QUrl = QtCore.QUrl(self._block_documentation_url)
            opened: bool = QtGui.QDesktopServices.openUrl(documentation_url)
            if opened:
                self._status_label.clear()
                self._status_label.setStyleSheet("")
            else:
                self._status_label.setStyleSheet("color: #b42318;")
                self._status_label.setText(
                    self.tr("The online block documentation could not be opened in the system browser.")
                )

    @QtCore.Slot(str)
    def filter_general_parameters(self, search_text: str) -> None:
        """Filter numeric parameters in General options.

        :param search_text: User-entered parameter query.
        :return: None.
        """
        self._general_parameter_proxy.set_search_text(search_text)

    @QtCore.Slot(str)
    def filter_variables(self, search_text: str) -> None:
        """Filter staged variables in the DAE model symbol table.

        :param search_text: User-entered variable query.
        :return: None.
        """
        self._variable_symbol_proxy.set_search_text(search_text)

    @QtCore.Slot(str)
    def filter_parameters(self, search_text: str) -> None:
        """Filter staged parameters in the DAE model symbol table.

        :param search_text: User-entered parameter query.
        :return: None.
        """
        self._parameter_symbol_proxy.set_search_text(search_text)

    @QtCore.Slot(str)
    def update_dae_code_search(self, search_text: str) -> None:
        """Refresh Python-code matches without running DAE validation.

        :param search_text: User-entered source-code query.
        :return: None.
        """
        match_count: int = self._dae_editor.set_search_text(search_text)
        has_query: bool = len(search_text.strip()) > 0
        has_matches: bool = match_count > 0
        self._dae_search_previous_button.setEnabled(has_matches)
        self._dae_search_next_button.setEnabled(has_matches)
        if not has_query:
            self._dae_search_status.setText("")
        elif has_matches:
            self._dae_search_status.setText(self.tr("1 / {count}").format(count=match_count))
        else:
            self._dae_search_status.setText(self.tr("No matches"))

    @QtCore.Slot()
    def find_previous_dae_code_match(self) -> None:
        """Select the previous Python-code search match.

        :return: None.
        """
        active_match: int
        match_count: int
        active_match, match_count = self._dae_editor.move_to_search_match(-1)
        self._update_dae_search_position(active_match, match_count)

    @QtCore.Slot()
    def find_next_dae_code_match(self) -> None:
        """Select the next Python-code search match.

        :return: None.
        """
        active_match: int
        match_count: int
        active_match, match_count = self._dae_editor.move_to_search_match(1)
        self._update_dae_search_position(active_match, match_count)

    def _update_dae_search_position(self, active_match: int, match_count: int) -> None:
        """Update the compact Python-code search counter.

        :param active_match: One-based active match number.
        :param match_count: Total number of source-code matches.
        :return: None.
        """
        if match_count > 0:
            self._dae_search_status.setText(
                self.tr("{active} / {count}").format(active=active_match, count=match_count)
            )
        else:
            self._dae_search_status.setText(self.tr("No matches"))

    def _get_latex_section_count(self,
                                 draft: BlockEquationDraft,
                                 section: EquationExportSection) -> int:
        """Return the equation count for one selectable export section.

        :param draft: Parsed equations for one internal block.
        :param section: Section whose size is requested.
        :return: Number of equations available for export.
        """
        if section == EquationExportSection.STATE:
            result: int = len(draft.get_state_eqs())
        elif section == EquationExportSection.ALGEBRAIC:
            result = len(draft.get_algebraic_eqs())
        elif section == EquationExportSection.INITIALIZATION:
            result = len(draft.get_init_eqs())
        else:
            result = len(draft.get_diff_init_eqs())
        return result

    def _rebuild_latex_selection_tree(self) -> None:
        """
        Rebuild block/section choices while retaining checked selections.

        :return: None.
        """
        selected_keys: set[tuple[int, str]] = set()
        root_index: int
        for root_index in range(self._latex_selection_tree.topLevelItemCount()):
            old_root: QtWidgets.QTreeWidgetItem = self._latex_selection_tree.topLevelItem(root_index)
            child_index: int
            for child_index in range(old_root.childCount()):
                old_child: QtWidgets.QTreeWidgetItem = old_root.child(child_index)
                if old_child.checkState(0) == Qt.CheckState.Checked:
                    buffer_value: object = old_child.data(0, Qt.ItemDataRole.UserRole)
                    section_value: object = old_child.data(0, Qt.ItemDataRole.UserRole + 1)
                    if isinstance(buffer_value, int) and isinstance(section_value, str):
                        selected_keys.add((buffer_value, section_value))
                    else:
                        pass
                else:
                    pass

        # Rebuilding creates and checks several items. Suppress intermediate
        # change notifications so the source view is regenerated once from the
        # complete selection tree rather than from partially constructed state.
        previous_signal_state: bool = self._latex_selection_tree.blockSignals(True)
        self._latex_selection_tree.clear()
        buffer_index: int
        buffer: BlockCodeBuffer
        for buffer_index, buffer in enumerate(self._equation_buffers):
            owner_block: Block = buffer.get_block()
            root_item: QtWidgets.QTreeWidgetItem = QtWidgets.QTreeWidgetItem(
                list((owner_block.name, "",))
            )
            root_item.setFlags(
                root_item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsAutoTristate
            )
            root_item.setCheckState(0, Qt.CheckState.Unchecked)
            self._latex_selection_tree.addTopLevelItem(root_item)
            try:
                draft: BlockEquationDraft = parse_equation_code(buffer.get_code(), self._namespace)
            except (TypeError, ValueError):
                draft = BlockEquationDraft(list(), list(), dict(), dict())

            section: EquationExportSection
            for section in EquationExportSection:
                section_count: int = self._get_latex_section_count(draft, section)
                section_item: QtWidgets.QTreeWidgetItem = QtWidgets.QTreeWidgetItem(
                    list((section.value, str(section_count),))
                )
                section_item.setData(0, Qt.ItemDataRole.UserRole, buffer_index)
                section_item.setData(0, Qt.ItemDataRole.UserRole + 1, section.value)
                if section_count > 0:
                    section_item.setFlags(section_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    if (buffer_index, section.value) in selected_keys:
                        section_item.setCheckState(0, Qt.CheckState.Checked)
                    else:
                        section_item.setCheckState(0, Qt.CheckState.Unchecked)
                else:
                    section_item.setFlags(section_item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                root_item.addChild(section_item)
            root_item.setExpanded(True)
        self._latex_selection_tree.blockSignals(previous_signal_state)
        self.refresh_latex_source_preview()

    @QtCore.Slot(QtWidgets.QTreeWidgetItem, int)
    def on_latex_selection_changed(self,
                                   changed_item: QtWidgets.QTreeWidgetItem,
                                   changed_column: int) -> None:
        """Regenerate copyable source after one equation-group selection changes.

        :param changed_item: Tree item whose checked state changed.
        :param changed_column: Tree column that emitted the change.
        :return: None.
        """
        _unused_changed_item: QtWidgets.QTreeWidgetItem = changed_item
        _unused_changed_column: int = changed_column
        self.refresh_latex_source_preview()

    def refresh_latex_source_preview(self) -> None:
        """Show copy-ready LaTeX for all currently selected valid equations.

        Invalid DAE drafts leave the source view empty. The normal validation
        action remains responsible for displaying diagnostics, so merely
        changing a selection never introduces unrelated red error feedback.

        :return: None.
        """
        try:
            drafts: List[BlockEquationDraft] = self._parse_all_equation_buffers_for_export()
            entries: List[EquationExportEntry] = self._build_selected_equation_entries(drafts)
        except (TypeError, ValueError):
            latex_source: str = ""
        else:
            latex_source = build_latex_source(entries)
        self._latex_source_preview.setPlainText(latex_source)

    @QtCore.Slot()
    def select_all_latex_sections(self) -> None:
        """
        Select every non-empty block equation section for PDF export.

        :return: None.
        """
        previous_signal_state: bool = self._latex_selection_tree.blockSignals(True)
        root_index: int
        for root_index in range(self._latex_selection_tree.topLevelItemCount()):
            root_item: QtWidgets.QTreeWidgetItem = self._latex_selection_tree.topLevelItem(root_index)
            child_index: int
            for child_index in range(root_item.childCount()):
                child_item: QtWidgets.QTreeWidgetItem = root_item.child(child_index)
                if child_item.flags() & Qt.ItemFlag.ItemIsEnabled:
                    child_item.setCheckState(0, Qt.CheckState.Checked)
                else:
                    pass
        self._latex_selection_tree.blockSignals(previous_signal_state)
        self.refresh_latex_source_preview()

    @QtCore.Slot()
    def clear_latex_sections(self) -> None:
        """
        Clear every equation-section PDF selection.

        :return: None.
        """
        previous_signal_state: bool = self._latex_selection_tree.blockSignals(True)
        root_index: int
        for root_index in range(self._latex_selection_tree.topLevelItemCount()):
            root_item: QtWidgets.QTreeWidgetItem = self._latex_selection_tree.topLevelItem(root_index)
            child_index: int
            for child_index in range(root_item.childCount()):
                child_item: QtWidgets.QTreeWidgetItem = root_item.child(child_index)
                if child_item.flags() & Qt.ItemFlag.ItemIsEnabled:
                    child_item.setCheckState(0, Qt.CheckState.Unchecked)
                else:
                    pass
        self._latex_selection_tree.blockSignals(previous_signal_state)
        self.refresh_latex_source_preview()

    def _parse_all_equation_buffers_for_export(self) -> List[BlockEquationDraft]:
        """Parse every equation buffer before creating a PDF.

        :return: Drafts aligned with ``self._equation_buffers``.
        :raises ValueError: If any buffer contains invalid DAE code.
        """
        validation_namespace: Dict[str, Expr] = self._build_joint_validation_namespace()
        drafts: List[BlockEquationDraft] = list()
        buffer: BlockCodeBuffer
        for buffer in self._equation_buffers:
            draft: BlockEquationDraft = parse_equation_code(buffer.get_code(), validation_namespace)
            self._validate_equation_variable_counts(buffer.get_block(), draft)
            drafts.append(draft)
        return drafts

    def _build_selected_equation_entries(self,
                                         drafts: Sequence[BlockEquationDraft]) -> List[EquationExportEntry]:
        """Build ordered entries for every checked block/section pair.

        :param drafts: Parsed drafts aligned with the dialogue equation buffers.
        :return: Selected PDF entries.
        """
        entries: List[EquationExportEntry] = list()
        root_index: int
        for root_index in range(self._latex_selection_tree.topLevelItemCount()):
            root_item: QtWidgets.QTreeWidgetItem = self._latex_selection_tree.topLevelItem(root_index)
            child_index: int
            for child_index in range(root_item.childCount()):
                child_item: QtWidgets.QTreeWidgetItem = root_item.child(child_index)
                if child_item.checkState(0) == Qt.CheckState.Checked:
                    buffer_value: object = child_item.data(0, Qt.ItemDataRole.UserRole)
                    section_value: object = child_item.data(0, Qt.ItemDataRole.UserRole + 1)
                    if isinstance(buffer_value, int) and isinstance(section_value, str):
                        buffer: BlockCodeBuffer = self._equation_buffers[buffer_value]
                        owner_block: Block = buffer.get_block()
                        draft: BlockEquationDraft = drafts[buffer_value]
                        section: EquationExportSection = EquationExportSection(section_value)
                        entries.extend(self._build_section_entries(owner_block, section, draft))
                    else:
                        pass
                else:
                    pass
        return entries

    def _build_section_entries(self,
                               owner_block: Block,
                               section: EquationExportSection,
                               draft: BlockEquationDraft) -> List[EquationExportEntry]:
        """Convert one selected parsed section into PDF entries.

        :param owner_block: Internal block owning the equations and differential variables.
        :param section: Selected equation section.
        :param draft: Parsed equations for the owner.
        :return: Ordered PDF entries for the section.
        """
        if section == EquationExportSection.STATE:
            state_differential_variables: List[Var | None] = (
                order_state_differential_variables(
                    owner_block.state_vars,
                    owner_block.diff_vars,
                )
            )
            result: List[EquationExportEntry] = build_state_equation_entries(
                owner_block.name,
                draft.get_state_eqs(),
                state_differential_variables,
            )
        elif section == EquationExportSection.ALGEBRAIC:
            residual_expressions: List[Expr] = list(draft.get_algebraic_eqs())
            result = build_list_equation_entries(
                owner_block.name,
                section,
                residual_expressions,
            )
        elif section == EquationExportSection.INITIALIZATION:
            result = build_mapping_equation_entries(
                owner_block.name,
                section,
                draft.get_init_eqs(),
            )
        else:
            result = build_mapping_equation_entries(
                owner_block.name,
                section,
                draft.get_diff_init_eqs(),
            )
        return result

    @QtCore.Slot()
    def export_rendered_equations_pdf(self) -> None:
        """Validate selected equations and export rendered mathematical notation.

        :return: None.
        """
        try:
            drafts: List[BlockEquationDraft] = self._parse_all_equation_buffers_for_export()
        except (TypeError, ValueError) as error:
            self._show_validation_error(str(error))
            return

        entries: List[EquationExportEntry] = self._build_selected_equation_entries(drafts)
        if len(entries) == 0:
            self._show_validation_error(self.tr("Select at least one non-empty equation group."))
            return
        else:
            pass

        suggested_name: str = build_equation_pdf_suggested_name(self._block.name)
        selected_path: str
        selected_filter: str
        selected_path, selected_filter = QtWidgets.QFileDialog.getSaveFileName(
            self,
            self.tr("Save dynamic equations PDF"),
            suggested_name,
            self.tr("PDF documents (*.pdf)"),
        )
        _unused_selected_filter: str = selected_filter
        if len(selected_path) == 0:
            return
        elif not selected_path.lower().endswith(".pdf"):
            selected_path = f"{selected_path}.pdf"
        else:
            pass

        try:
            write_equation_pdf(
                file_path=selected_path,
                root_block_name=self._block.name,
                entries=entries,
            )
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            self._show_validation_error(
                self.tr("The PDF could not be created: {message}").format(message=str(error))
            )
        else:
            self._status_label.setStyleSheet("color: #16825d;")
            self._status_label.setText(
                self.tr("Equation PDF created: {path}").format(path=selected_path)
            )

    @QtCore.Slot(QtCore.QModelIndex, QtCore.QModelIndex, list)
    def on_symbol_draft_changed(self,
                                top_left: QtCore.QModelIndex,
                                bottom_right: QtCore.QModelIndex,
                                roles: List[int]) -> None:
        """
        Rebuild validation names after an editable symbol cell changes.

        :param top_left: Value supplied for ``top_left``.
        :param bottom_right: Value supplied for ``bottom_right``.
        :param roles: Value supplied for ``roles``.
        :return: None.
        """
        _unused_top_left: QtCore.QModelIndex = top_left
        _unused_bottom_right: QtCore.QModelIndex = bottom_right
        _unused_roles: List[int] = roles
        try:
            self._namespace = self._build_joint_validation_namespace()
        except ValueError as error:
            self._show_validation_error(str(error))
        else:
            self._dae_highlighter.set_symbol_names(tuple(self._namespace.keys()))
            self._clear_dae_validation_feedback()

    @QtCore.Slot()
    def on_runtime_logic_changed(self) -> None:
        """Refresh the joint namespace after a retained-mode draft changes.

        :return: None.
        """
        try:
            # New or removed retained modes immediately participate in DAE
            # highlighting and validation, while the source block remains
            # untouched until Apply succeeds.
            self._namespace = self._build_joint_validation_namespace()
        except (TypeError, ValueError) as error:
            self._show_validation_error(str(error))
        else:
            self._dae_highlighter.set_symbol_names(tuple(self._namespace.keys()))
            self._clear_dae_validation_feedback()

    def _build_joint_validation_namespace(self) -> Dict[str, Expr]:
        """Build the staged DAE namespace including retained runtime modes.

        :return: Namespace shared by DAE code and procedural expressions.
        """
        symbol_namespace: Dict[str, Expr] = self._symbol_model.build_validation_namespace(
            build_block_symbol_namespace(self._block)
        )
        return self._runtime_logic_editor.build_validation_namespace(symbol_namespace)

    @QtCore.Slot(int)
    def update_new_symbol_category(self, unused_index: int = 0) -> None:
        """Populate symbol types after Variable or Parameter is selected.

        :param unused_index: Qt combo index supplied by the signal.
        :return: None.
        """
        _unused_index: int = unused_index
        selected_category: object = self._new_symbol_category.currentData()
        self._new_symbol_kind.clear()
        if selected_category == BlockSymbolCategory.VARIABLES:
            variable_kind: BlockSymbolKind
            for variable_kind in (
                BlockSymbolKind.INPUT,
                BlockSymbolKind.STATE,
                BlockSymbolKind.ALGEBRAIC,
            ):
                self._new_symbol_kind.addItem(variable_kind.value, variable_kind)
        elif selected_category == BlockSymbolCategory.PARAMETERS:
            parameter_kind: BlockSymbolKind
            for parameter_kind in (
                BlockSymbolKind.EVENT_PARAMETER,
                BlockSymbolKind.PARAMETER,
            ):
                self._new_symbol_kind.addItem(parameter_kind.value, parameter_kind)
                if parameter_kind == BlockSymbolKind.EVENT_PARAMETER:
                    dynamic_parameter_index: int = self._new_symbol_kind.count() - 1
                    self._new_symbol_kind.setItemData(
                        dynamic_parameter_index,
                        self.tr("Parameter whose value may change during the simulation."),
                        Qt.ItemDataRole.ToolTipRole,
                    )
                else:
                    pass
        else:
            pass
        self.update_new_symbol_controls()

    @QtCore.Slot(int)
    def update_new_symbol_controls(self, unused_index: int = 0) -> None:
        """
        Show only options that apply to the selected symbol type.

        :param unused_index: Value supplied for ``unused_index``.
        :return: None.
        """
        _unused_index: int = unused_index
        selected_data: object = self._new_symbol_kind.currentData()
        if isinstance(selected_data, BlockSymbolKind):
            temporary_row: BlockSymbolDraftRow = BlockSymbolDraftRow(
                self._block,
                None,
                "temporary",
                selected_data,
                False,
                "0.0",
            )
            supports_export: bool = temporary_row.kind_supports_export()
            # Inputs receive their value from a graphical incoming connection.
            # A newly declared input must therefore not offer a second,
            # conflicting power-flow initialization source.
            supports_external_reference: bool = (
                temporary_row.supports_external_reference()
                and selected_data != BlockSymbolKind.INPUT
            )
            self._new_symbol_exported.setVisible(supports_export)
            self._new_symbol_exported.setEnabled(supports_export)
            self._new_state_derivative.setVisible(selected_data == BlockSymbolKind.STATE)
            self._new_external_reference_label.setVisible(supports_external_reference)
            self._new_external_reference.setVisible(supports_external_reference)
            shows_variable_options: bool = selected_data in (
                BlockSymbolKind.INPUT,
                BlockSymbolKind.STATE,
                BlockSymbolKind.ALGEBRAIC,
            )
            shows_initial_value: bool = selected_data == BlockSymbolKind.EVENT_PARAMETER
            shows_static_mapping: bool = selected_data == BlockSymbolKind.PARAMETER
            self._new_variable_options.setVisible(shows_variable_options)
            self._new_parameter_value_label.setVisible(shows_initial_value)
            self._new_parameter_value.setVisible(shows_initial_value)
            self._new_static_reference_label.setVisible(shows_static_mapping)
            self._new_static_reference.setVisible(shows_static_mapping)
            if not supports_export:
                self._new_symbol_exported.setChecked(False)
            else:
                pass
            if selected_data != BlockSymbolKind.STATE:
                self._new_state_derivative.setChecked(False)
            else:
                pass
        else:
            self._new_symbol_exported.setEnabled(False)
            self._new_variable_options.setVisible(False)
            self._new_parameter_value_label.setVisible(False)
            self._new_parameter_value.setVisible(False)
            self._new_static_reference_label.setVisible(False)
            self._new_static_reference.setVisible(False)
            self._new_external_reference_label.setVisible(False)
            self._new_external_reference.setVisible(False)

    @QtCore.Slot()
    def add_staged_symbol(self) -> None:
        """
        Add one validated detached symbol row to the selected block.

        :return: None.
        """
        name: str = self._new_symbol_name.text().strip()
        selected_data: object = self._new_symbol_kind.currentData()
        selected_owner: object = self._new_symbol_owner.currentData()
        if len(name) == 0 or not name.isidentifier():
            self._show_validation_error(self.tr("Enter a valid Python symbol name."))
        elif not isinstance(selected_data, BlockSymbolKind):
            self._show_validation_error(self.tr("Select a valid symbol type."))
        elif not isinstance(selected_owner, Block):
            self._show_validation_error(self.tr("Select a valid owner block."))
        else:
            self._symbol_model.add_symbol(
                owner=selected_owner,
                name=name,
                kind=selected_data,
                exported=self._new_symbol_exported.isChecked(),
                value=self._new_parameter_value.value(),
                create_derivative=self._new_state_derivative.isChecked(),
                external_reference=self._get_selected_new_external_reference(selected_data),
                static_reference=self._get_selected_new_static_reference(selected_data),
            )
            try:
                self._namespace = self._build_joint_validation_namespace()
            except ValueError as error:
                self._symbol_model.remove_new_symbol(self._symbol_model.rowCount() - 1)
                if selected_data == BlockSymbolKind.STATE and self._new_state_derivative.isChecked():
                    self._symbol_model.remove_new_symbol(self._symbol_model.rowCount() - 1)
                else:
                    pass
                self._show_validation_error(str(error))
            else:
                self._new_symbol_name.clear()
                self._synchronize_dae_variable_declarations_for_block(selected_owner)
                self._dae_highlighter.set_symbol_names(tuple(self._namespace.keys()))
                self._clear_dae_validation_feedback()

    def _synchronize_dae_variable_declarations_for_block(self, owner: Block) -> None:
        """Project one owner's staged variable order into its DAE buffer.

        :param owner: Block whose Variables-table rows changed.
        :return: None.
        """
        state_names: List[str] = self._symbol_model.get_role_names(
            owner,
            BlockSymbolKind.STATE,
        )
        algebraic_names: List[str] = self._symbol_model.get_role_names(
            owner,
            BlockSymbolKind.ALGEBRAIC,
        )
        differential_names: List[str] = self._symbol_model.get_role_names(
            owner,
            BlockSymbolKind.DIFFERENTIAL,
        )
        buffer_index: int
        equation_buffer: BlockCodeBuffer
        for buffer_index, equation_buffer in enumerate(self._equation_buffers):
            if equation_buffer.get_block() is owner:
                previous_code: str = equation_buffer.get_code()
                updated_code: str = synchronize_dae_variable_declarations(
                    code=previous_code,
                    state_names=state_names,
                    algebraic_names=algebraic_names,
                    differential_names=differential_names,
                )
                if updated_code != previous_code:
                    equation_buffer.set_code(updated_code)
                    if buffer_index == self._active_equation_buffer_index:
                        previous_cursor: QtGui.QTextCursor = self._dae_editor.textCursor()
                        previous_length: int = len(previous_code)
                        position_from_end: int = previous_length - previous_cursor.position()
                        anchor_from_end: int = previous_length - previous_cursor.anchor()
                        updated_length: int = len(updated_code)
                        updated_position: int = max(0, updated_length - position_from_end)
                        updated_anchor: int = max(0, updated_length - anchor_from_end)
                        self._loading_equation_buffer = True
                        self._dae_editor.setPlainText(updated_code)
                        self._loading_equation_buffer = False
                        restored_cursor: QtGui.QTextCursor = self._dae_editor.textCursor()
                        restored_cursor.setPosition(min(updated_anchor, updated_length))
                        restored_cursor.setPosition(
                            min(updated_position, updated_length),
                            QtGui.QTextCursor.MoveMode.KeepAnchor,
                        )
                        self._dae_editor.setTextCursor(restored_cursor)
                        self.update_dae_code_search(self._dae_code_search.text())
                    else:
                        pass
                else:
                    pass
            else:
                pass

    def _get_selected_new_external_reference(
            self,
            selected_kind: BlockSymbolKind) -> VarPowerFlowReferenceType | None:
        """Return an optional power-flow initialization mapping for a new symbol.

        :param selected_kind: Primary kind selected in the add-symbol form.
        :return: Selected initialization mapping or ``None``.
        """
        temporary_row: BlockSymbolDraftRow = BlockSymbolDraftRow(
            self._block,
            None,
            "temporary",
            selected_kind,
            False,
            "0.0",
        )
        if temporary_row.supports_external_reference() and selected_kind != BlockSymbolKind.INPUT:
            selected_reference: object = self._new_external_reference.currentData()
            if isinstance(selected_reference, VarPowerFlowReferenceType):
                result: VarPowerFlowReferenceType | None = selected_reference
            else:
                result = None
        else:
            result = None
        return result

    def _get_selected_new_static_reference(
            self,
            selected_kind: BlockSymbolKind) -> ParamPowerFlowReferenceType | None:
        """Return a static-device mapping only for a new static parameter.

        :param selected_kind: Primary kind selected in the add-symbol form.
        :return: Selected mapping or ``None`` for all other symbol types.
        """
        if selected_kind == BlockSymbolKind.PARAMETER:
            selected_reference: object = self._new_static_reference.currentData()
            if isinstance(selected_reference, ParamPowerFlowReferenceType):
                result: ParamPowerFlowReferenceType | None = selected_reference
            else:
                result = None
        else:
            result = None
        return result

    @QtCore.Slot(QtCore.QPoint)
    def show_variable_context_menu(self, position: QtCore.QPoint) -> None:
        """Show the right-click symbol actions for the Variables table.

        :param position: Viewport-local click position.
        :return: None.
        """
        self._show_symbol_context_menu(self._symbol_table, position)

    @QtCore.Slot(QtCore.QPoint)
    def show_parameter_context_menu(self, position: QtCore.QPoint) -> None:
        """Show the right-click symbol actions for the Parameters table.

        :param position: Viewport-local click position.
        :return: None.
        """
        self._show_symbol_context_menu(self._parameter_symbol_table, position)

    def _show_symbol_context_menu(self,
                                  table: QtWidgets.QTableView,
                                  position: QtCore.QPoint) -> None:
        """Select the clicked row and offer valid symbol actions.

        :param table: Variable or parameter proxy table.
        :param position: Viewport-local click position.
        :return: None.
        """
        clicked_index: QtCore.QModelIndex = table.indexAt(position)
        if clicked_index.isValid():
            table.selectRow(clicked_index.row())
            menu: QtWidgets.QMenu = QtWidgets.QMenu(table)
            source_row: BlockSymbolDraftRow | None = self._get_selected_symbol_row(table)
            rename_action: QtGui.QAction | None
            if source_row is not None and not source_row.is_new():
                rename_action = menu.addAction(self.tr("Rename..."))
            else:
                rename_action = None
            delete_action: QtGui.QAction = menu.addAction(self.tr("Delete"))
            selected_action: QtGui.QAction | None = menu.exec(table.viewport().mapToGlobal(position))
            if rename_action is not None and selected_action is rename_action:
                self._rename_selected_symbol(table)
            elif selected_action is delete_action:
                self._delete_selected_symbol(table)
            else:
                pass
        else:
            pass

    def _get_selected_symbol_row(self,
                                 table: QtWidgets.QTableView) -> BlockSymbolDraftRow | None:
        """Resolve the single selected proxy row to its symbol draft.

        :param table: Variable or parameter table containing the selection.
        :return: Selected source row, or ``None`` without one valid selection.
        """
        selection_model: QtCore.QItemSelectionModel | None = table.selectionModel()
        if selection_model is None:
            return None
        else:
            selected_rows: List[QtCore.QModelIndex] = selection_model.selectedRows()
        if len(selected_rows) != 1:
            return None
        else:
            pass
        proxy_model: QtCore.QAbstractItemModel | None = table.model()
        if isinstance(proxy_model, BlockSymbolFilterProxyModel):
            source_index: QtCore.QModelIndex = proxy_model.mapToSource(selected_rows[0])
            return self._symbol_model.get_row(source_index.row())
        else:
            return None

    def _rename_selected_symbol(self, table: QtWidgets.QTableView) -> None:
        """Request one complete editor-owned rename and refresh detached drafts.

        :param table: Variable or parameter table containing the selected row.
        :return: None.
        """
        selected_row: BlockSymbolDraftRow | None = self._get_selected_symbol_row(table)
        if selected_row is None or selected_row.is_new():
            return
        else:
            selected_variable: Var | None = selected_row.get_variable()
        if selected_variable is None:
            return
        else:
            pass

        # Capture every row independently before the editor propagates the
        # alias component. Connected variables can share one stable UID while
        # still using different local names, so a UID-keyed dictionary would
        # lose all but the last old name and leave stale identifiers in DAE
        # source owned by the other connected blocks.
        old_names_by_row: List[tuple[BlockSymbolDraftRow, str]] = list()
        selected_old_name: str = selected_row.get_name()
        row_index: int
        for row_index in range(self._symbol_model.rowCount()):
            draft_row: BlockSymbolDraftRow | None = self._symbol_model.get_row(row_index)
            if draft_row is not None:
                draft_variable: Var | None = draft_row.get_variable()
            else:
                draft_variable = None
            if draft_variable is not None:
                old_names_by_row.append((draft_row, draft_variable.name))
            else:
                pass

        request: BlockVariableRenameRequest = BlockVariableRenameRequest(selected_variable)
        self.variableRenameRequested.emit(request)
        if request.is_successful():
            rename_pairs: List[tuple[str, str]] = list()
            selected_rename_pair: tuple[str, str] = (selected_old_name, request.get_new_name())
            if selected_old_name != request.get_new_name():
                rename_pairs.append(selected_rename_pair)
            else:
                pass

            old_name: str
            for draft_row, old_name in old_names_by_row:
                draft_variable = draft_row.get_variable()
                if draft_variable is not None:
                    if old_name != draft_variable.name:
                        rename_pair: tuple[str, str] = (old_name, draft_variable.name)
                        if rename_pair not in rename_pairs:
                            rename_pairs.append(rename_pair)
                        else:
                            pass
                    else:
                        pass
                else:
                    pass

            equation_buffer: BlockCodeBuffer
            for equation_buffer in self._equation_buffers:
                updated_code: str = equation_buffer.get_code()
                old_name: str
                new_name: str
                for old_name, new_name in rename_pairs:
                    updated_code = replace_dae_identifier(updated_code, old_name, new_name)
                equation_buffer.set_code(updated_code)

            self._symbol_model.refresh_existing_names()
            self._namespace = self._build_joint_validation_namespace()
            active_buffer: BlockCodeBuffer = self._equation_buffers[self._active_equation_buffer_index]

            # Load the renamed source before rehighlighting it. Rehighlighting
            # can emit a document change; while the editor still showed the
            # old source, that signal wrote the stale text back over the newly
            # updated active buffer.
            self._loading_equation_buffer = True
            self._dae_editor.setPlainText(active_buffer.get_code())
            self._dae_highlighter.set_symbol_names(tuple(self._namespace.keys()))
            self._loading_equation_buffer = False
            self._clear_dae_validation_feedback()
            self._status_label.setStyleSheet("color: #16825d;")
            self._status_label.setText(
                self.tr("Variable renamed to '{name}'.").format(name=request.get_new_name())
            )
        else:
            pass

    def _delete_selected_symbol(self, table: QtWidgets.QTableView) -> None:
        """Stage deletion of the single selected proxy row.

        :param table: Table containing the selected row.
        :return: None.
        """
        selection_model: QtCore.QItemSelectionModel | None = table.selectionModel()
        if selection_model is None:
            return
        else:
            selected_rows: List[QtCore.QModelIndex] = selection_model.selectedRows()
        if len(selected_rows) != 1:
            return
        else:
            pass
        proxy_model: QtCore.QAbstractItemModel | None = table.model()
        removed_owner: Block | None = None
        if isinstance(proxy_model, BlockSymbolFilterProxyModel):
            source_index: QtCore.QModelIndex = proxy_model.mapToSource(selected_rows[0])
            selected_row: BlockSymbolDraftRow | None = self._symbol_model.get_row(source_index.row())
            if selected_row is not None:
                removed_owner = selected_row.get_owner()
            else:
                pass
            removed: bool = self._symbol_model.remove_symbol(source_index.row())
        else:
            removed = False
        if removed:
            if removed_owner is not None:
                self._synchronize_dae_variable_declarations_for_block(removed_owner)
            else:
                pass
            self._namespace = self._build_joint_validation_namespace()
            self._dae_highlighter.set_symbol_names(tuple(self._namespace.keys()))
            self._clear_dae_validation_feedback()
        else:
            pass

    @QtCore.Slot()
    def on_dae_code_changed(self) -> None:
        """
        Persist edits and clear stale diagnostics until Validate is pressed.

        :return: None.
        """
        if self._loading_equation_buffer:
            pass
        else:
            active_buffer: BlockCodeBuffer = self._equation_buffers[self._active_equation_buffer_index]
            active_buffer.set_code(self._dae_editor.toPlainText())
            # A source preview must never present LaTeX generated from an older
            # equation draft. It is rebuilt from the new text when the user
            # changes the selection or validates the complete DAE model.
            self._latex_source_preview.clear()
            self._clear_dae_validation_feedback()
            self.update_dae_code_search(self._dae_code_search.text())

    @QtCore.Slot(int)
    def on_equation_owner_changed(self, combo_index: int) -> None:
        """
        Switch source buffers without flattening equations across child blocks.

        :param combo_index: Value supplied for ``combo_index``.
        :return: None.
        """
        selected_data: object = self._equation_owner_combo.itemData(combo_index)
        if isinstance(selected_data, int) and 0 <= selected_data < len(self._equation_buffers):
            self._active_equation_buffer_index = selected_data
            selected_buffer: BlockCodeBuffer = self._equation_buffers[selected_data]
            self._loading_equation_buffer = True
            self._dae_editor.setPlainText(selected_buffer.get_code())
            self._loading_equation_buffer = False
            self._clear_dae_validation_feedback()
            self.update_dae_code_search(self._dae_code_search.text())
        else:
            pass

    def validate_dae_code(self) -> bool:
        """
        Validate the active DAE buffer and show explicit inline feedback.

        :return: True when the active DAE code is valid; otherwise False.
        """
        active_buffer: BlockCodeBuffer = self._equation_buffers[self._active_equation_buffer_index]
        self._dae_editor.set_symbol_namespace(self._namespace)
        code: str = self._dae_editor.toPlainText()
        diagnostics: List[DaeCodeDiagnostic] = self._dae_editor.build_current_diagnostics()
        if len(diagnostics) > 0:
            self._show_dae_validation_diagnostics(diagnostics)
            return False
        else:
            pass
        try:
            equation_draft: BlockEquationDraft = self._dae_editor.parse_current_code()
            self._validate_equation_variable_counts(active_buffer.get_block(), equation_draft)
        except (ValueError, TypeError) as error:
            diagnostic: DaeCodeDiagnostic = build_semantic_dae_diagnostic(code, str(error))
            self._show_dae_validation_diagnostics(list((diagnostic,)))
            return False
        else:
            self._latex_model.set_draft(equation_draft)
            self._dae_editor.set_diagnostics(list())
            self._status_label.setStyleSheet("color: #16825d;")
            self._status_label.setText(self.tr("DAE code is valid."))
            self._rebuild_latex_selection_tree()
            return True

    @QtCore.Slot()
    def validate_complete_dae_code(self) -> None:
        """
        Validate every recursive equation buffer and focus its first inline error.

        :return: None.
        """
        try:
            symbol_namespace: Dict[str, Expr] = self._symbol_model.build_validation_namespace(
                build_block_symbol_namespace(self._block)
            )
            runtime_validation: RuntimeLogicValidationResult = self._runtime_logic_editor.validate(
                symbol_namespace
            )
            if not runtime_validation.is_valid():
                self._show_validation_error(runtime_validation.get_errors()[0])
                return
            else:
                validation_namespace: Dict[str, Expr] = self._runtime_logic_editor.build_validation_namespace(
                    symbol_namespace
                )
        except (ValueError, TypeError) as error:
            self._show_validation_error(str(error))
            return

        valid: bool = True
        invalid_index: int = -1
        invalid_message: str = ""
        buffer_index: int
        buffer: BlockCodeBuffer
        for buffer_index, buffer in enumerate(self._equation_buffers):
            if valid:
                buffer_code: str = buffer.get_code()
                diagnostics: List[DaeCodeDiagnostic] = build_dae_code_diagnostics(
                    buffer_code,
                    validation_namespace,
                )
                if len(diagnostics) > 0:
                    valid = False
                    invalid_index = buffer_index
                    invalid_message = diagnostics[0].get_message()
                else:
                    pass
            else:
                pass
            if valid:
                try:
                    equation_draft: BlockEquationDraft = parse_equation_code(
                        buffer_code,
                        validation_namespace,
                    )
                    self._validate_equation_variable_counts(buffer.get_block(), equation_draft)
                except (ValueError, TypeError) as error:
                    valid = False
                    invalid_index = buffer_index
                    invalid_message = str(error)
                else:
                    pass
            else:
                pass
        if valid:
            self._namespace = validation_namespace
            self._dae_highlighter.set_symbol_names(tuple(self._namespace.keys()))
            self.validate_dae_code()
        else:
            if invalid_index != self._active_equation_buffer_index:
                self._equation_owner_combo.setCurrentIndex(invalid_index)
            else:
                pass
            visible_code: str = self._equation_buffers[invalid_index].get_code()
            visible_diagnostics: List[DaeCodeDiagnostic] = build_dae_code_diagnostics(
                visible_code,
                validation_namespace,
            )
            if len(visible_diagnostics) == 0:
                visible_diagnostics.append(
                    build_semantic_dae_diagnostic(visible_code, invalid_message)
                )
            else:
                pass
            self._show_dae_validation_diagnostics(visible_diagnostics)

    def _validate_equation_variable_counts(self,
                                           block: Block,
                                           equation_draft: BlockEquationDraft) -> None:
        """Require one equation for every staged state and algebraic variable.

        Output exposure is deliberately absent from this rule: checking or
        unchecking Output only changes the public interface and never changes a
        variable's DAE role or its equation.

        :param block: Equation owner being validated.
        :param equation_draft: Parsed equations staged for that owner.
        :return: None.
        :raises ValueError: If a DAE variable/equation count is inconsistent.
        """
        state_count: int = self._symbol_model.get_role_count(block, BlockSymbolKind.STATE)
        algebraic_count: int = self._symbol_model.get_role_count(block, BlockSymbolKind.ALGEBRAIC)
        legacy_output_count: int = self._symbol_model.get_role_count(
            block,
            BlockSymbolKind.OUTPUT_ONLY,
        )
        state_equation_count: int = len(equation_draft.get_state_eqs())
        algebraic_equation_count: int = len(equation_draft.get_algebraic_eqs())
        self._validate_variable_declaration(
            block=block,
            equation_draft=equation_draft,
            section_name="state_vars",
            kind=BlockSymbolKind.STATE,
        )
        self._validate_variable_declaration(
            block=block,
            equation_draft=equation_draft,
            section_name="algebraic_vars",
            kind=BlockSymbolKind.ALGEBRAIC,
        )
        self._validate_variable_declaration(
            block=block,
            equation_draft=equation_draft,
            section_name="diff_vars",
            kind=BlockSymbolKind.DIFFERENTIAL,
        )
        if state_count != state_equation_count:
            raise ValueError(
                f"Block '{block.name}' has {state_count} state variables but "
                f"{state_equation_count} state equations"
            )
        else:
            pass
        minimum_algebraic_equation_count: int = algebraic_count
        maximum_algebraic_equation_count: int = algebraic_count + legacy_output_count
        # Current blocks require one equation per algebraic variable. Older
        # files may additionally contain equation-backed variables represented
        # only in out_vars; accept at most one equation for each such legacy
        # output so users can repair and extend those models in the dialogue.
        if (algebraic_equation_count < minimum_algebraic_equation_count
                or algebraic_equation_count > maximum_algebraic_equation_count):
            raise ValueError(
                f"Block '{block.name}' has {algebraic_count} algebraic variables but "
                f"{algebraic_equation_count} algebraic equations; "
                f"{legacy_output_count} legacy outputs may own an additional equation"
            )
        else:
            pass

    def _validate_variable_declaration(self,
                                       block: Block,
                                       equation_draft: BlockEquationDraft,
                                       section_name: str,
                                       kind: BlockSymbolKind) -> None:
        """Require a present generated declaration to match the staged table order.

        Older hand-written buffers may omit the declaration for compatibility.
        When present, the declaration is an explicit ordering contract and must
        remain synchronized with symbol additions, removals, and reclassification.

        :param block: Block owning the declared variables.
        :param equation_draft: Parsed source containing optional declarations.
        :param section_name: Declaration section being checked.
        :param kind: Symbol-table role corresponding to the declaration.
        :return: None.
        :raises ValueError: If declared and staged names differ or are reordered.
        """
        declared_variables: List[Var] | None = equation_draft.get_variable_declaration(section_name)
        if declared_variables is None:
            return
        else:
            declared_names: List[str] = list()
            declared_variable: Var
            for declared_variable in declared_variables:
                declared_names.append(declared_variable.name)
            expected_names: List[str] = self._symbol_model.get_role_names(block, kind)

        if declared_names != expected_names:
            raise ValueError(
                f"Block '{block.name}' has {kind.value.lower()} variables ordered as "
                f"{expected_names}, but {section_name} declares {declared_names}"
            )
        else:
            pass

    @QtCore.Slot()
    def apply_changes(self) -> None:
        """
        Validate the complete draft and atomically apply it to the source block.

        :return: None.
        """
        parsed_buffers: List[tuple[Block, BlockEquationDraft]] = list()
        try:
            pending_values: List[tuple[Const, float | complex]] = self._parameter_model.get_pending_values()
            symbol_namespace: Dict[str, Expr] = self._symbol_model.build_validation_namespace(
                build_block_symbol_namespace(self._block)
            )
            runtime_validation: RuntimeLogicValidationResult = self._runtime_logic_editor.validate(
                symbol_namespace
            )
            if not runtime_validation.is_valid():
                self._show_validation_error(runtime_validation.get_errors()[0])
                return
            else:
                validation_namespace: Dict[str, Expr] = self._runtime_logic_editor.build_validation_namespace(
                    symbol_namespace
                )
        except (ValueError, TypeError) as error:
            self._show_validation_error(str(error))
            return

        buffer_index: int
        buffer: BlockCodeBuffer
        for buffer_index, buffer in enumerate(self._equation_buffers):
            code: str = buffer.get_code()
            diagnostics: List[DaeCodeDiagnostic] = build_dae_code_diagnostics(
                code,
                validation_namespace,
            )
            if len(diagnostics) > 0:
                self._show_equation_buffer_diagnostics(buffer_index, diagnostics)
                return
            else:
                pass
            try:
                parsed_draft: BlockEquationDraft = parse_equation_code(code, validation_namespace)
                self._validate_equation_variable_counts(buffer.get_block(), parsed_draft)
            except (ValueError, TypeError) as error:
                semantic_diagnostic: DaeCodeDiagnostic = build_semantic_dae_diagnostic(
                    code,
                    str(error),
                )
                self._show_equation_buffer_diagnostics(
                    buffer_index,
                    list((semantic_diagnostic,)),
                )
                return
            else:
                parsed_buffers.append((buffer.get_block(), parsed_draft))

        structural_changes: bool = (
            self._general_structural_model.has_changes()
            or self._special_structural_model.has_changes()
        )
        has_new_symbols: bool = self._symbol_model.has_new_symbols()
        has_symbol_changes: bool = self._symbol_model.has_symbol_changes()
        runtime_logic_changes: bool = self._runtime_logic_editor.has_changes()
        has_new_modes: bool = self._runtime_logic_editor.has_new_modes()
        output_export_changes: List[tuple[Block, Var, bool]] = self._symbol_model.get_output_export_changes()
        if structural_changes:
            changed_equations: bool = False
            equation_buffer: BlockCodeBuffer
            for equation_buffer in self._equation_buffers:
                if equation_buffer.has_changes():
                    changed_equations = True
                else:
                    pass
            if changed_equations or has_symbol_changes or runtime_logic_changes or len(output_export_changes) > 0:
                self._show_validation_error(
                    self.tr(
                        "Apply structural settings separately from DAE-code or symbol-interface changes."
                    )
                )
                return
            elif self._structural_block_type is None or self._structural_builder is None:
                self._show_validation_error(self.tr("This block has no safe structural rebuild adapter."))
                return
            else:
                named_parameter_values: List[tuple[str, float | complex]] = (
                    self._parameter_model.get_pending_named_values()
                )
                rebuild_request: BlockStructuralEditRequest = BlockStructuralEditRequest(
                    block=self._block,
                    block_type=self._structural_block_type,
                    builder=self._structural_builder,
                    parameter_values=named_parameter_values,
                )
                self.structuralRebuildRequested.emit(rebuild_request)
            if rebuild_request.is_successful():
                self._status_label.setStyleSheet("color: #16825d;")
                self._status_label.setText(self.tr("Block structure rebuilt with the selected settings."))
                self.blockApplied.emit(self._block.uid)
                return
            else:
                self._show_validation_error(rebuild_request.get_error_message())
                return
        else:
            pass

        constant: Const
        numeric_value: float | complex
        for constant, numeric_value in pending_values:
            constant.value = numeric_value

        # Structural symbol changes are delayed until every text and numeric
        # field has passed validation. New Vars then become the authoritative
        # parser identities for the final equation trees.
        if len(output_export_changes) > 0:
            # The editor must detach existing arrows while the old port indexes
            # are still valid. The model mutation immediately follows the
            # synchronous signal delivery.
            self.outputExportChangesRequested.emit(output_export_changes)
        else:
            pass
        self._symbol_model.apply_to_blocks(self._var_factory)
        symbol_namespace: Dict[str, Expr] = build_block_symbol_namespace(self._block)
        if runtime_logic_changes:
            self._namespace = self._runtime_logic_editor.apply_to_blocks(
                self._var_factory,
                symbol_namespace,
            )
        else:
            self._namespace = self._runtime_logic_editor.build_validation_namespace(symbol_namespace)
        self._parameter_model.reload(self._block)
        if has_new_symbols or has_new_modes:
            # Newly created symbols replace their temporary validation Vars, so
            # parse once more against the authoritative factory identities.
            parsed_buffers.clear()
            for buffer in self._equation_buffers:
                final_draft: BlockEquationDraft = parse_equation_code(buffer.get_code(), self._namespace)
                parsed_buffers.append((buffer.get_block(), final_draft))
        else:
            # Connection removal can restore a variable's pre-alias name. The
            # already validated drafts retain the exact Var identities and avoid
            # reparsing now-stale display text after that legitimate rename.
            pass

        target_block: Block
        equation_draft: BlockEquationDraft
        for target_block, equation_draft in parsed_buffers:
            target_block.state_eqs = equation_draft.get_state_eqs()
            target_block.algebraic_eqs = equation_draft.get_algebraic_eqs()
            target_block.init_eqs = equation_draft.get_init_eqs()
            target_block.diff_init_eqs = equation_draft.get_diff_init_eqs()

        # Rebind rows created during this Apply to their authoritative Vars.
        # This keeps subsequent edits in the still-open modal transactional.
        self._symbol_model.reload(self._block)
        active_draft: BlockEquationDraft = parsed_buffers[self._active_equation_buffer_index][1]
        self._latex_model.set_draft(active_draft)
        self._status_label.setStyleSheet("color: #16825d;")
        if runtime_logic_changes:
            self._status_label.setText(self.tr("DAE and runtime-logic changes applied to the editor working copy."))
        elif block_has_advanced_logic(self._block):
            self._status_label.setText(
                self.tr(
                    "Changes applied. Advanced inequalities/discrete/boolean logic was preserved unchanged."
                )
            )
        else:
            self._status_label.setText(self.tr("Changes applied to the editor working copy."))
        self.blockApplied.emit(self._block.uid)

    def _show_equation_buffer_diagnostics(self,
                                          buffer_index: int,
                                          diagnostics: Sequence[DaeCodeDiagnostic]) -> None:
        """Switch to one equation owner and show its source-local errors.

        :param buffer_index: Index of the invalid equation buffer.
        :param diagnostics: Diagnostics to underline in that buffer.
        :return: None.
        """
        if buffer_index != self._active_equation_buffer_index:
            self._equation_owner_combo.setCurrentIndex(buffer_index)
        else:
            pass
        self._dae_editor.set_diagnostics(diagnostics)
        if len(diagnostics) > 0:
            self._show_validation_error(diagnostics[0].get_message())
        else:
            self._show_validation_error(self.tr("Invalid DAE code."))

    def _clear_dae_validation_feedback(self) -> None:
        """Remove stale validation marks while preserving the edited source.

        :return: None.
        """
        self._dae_editor.set_diagnostics(list())
        self._status_label.clear()

    def _show_dae_validation_diagnostics(
            self,
            diagnostics: Sequence[DaeCodeDiagnostic]) -> None:
        """Show exact source diagnostics after an explicit validation request.

        :param diagnostics: Ordered diagnostics for the visible source buffer.
        :return: None.
        """
        self._dae_editor.set_diagnostics(diagnostics)
        if len(diagnostics) > 0:
            first_diagnostic: DaeCodeDiagnostic = diagnostics[0]
            self._status_label.setStyleSheet("color: #b42318;")
            self._status_label.setText(
                self.tr("DAE validation failed at line {line}: {message}").format(
                    line=first_diagnostic.get_line(),
                    message=first_diagnostic.get_message(),
                )
            )
        else:
            self._status_label.clear()

    def _show_validation_error(self, message: str) -> None:
        """
        Display validation feedback without modifying the source block.

        :param message: Value supplied for ``message``.
        :return: None.
        """
        self._status_label.setStyleSheet("color: #b42318;")
        self._status_label.setText(self.tr("Nothing was applied: {message}").format(message=message))


class DynamicBlockPropertiesDockWidget(QtWidgets.QDockWidget):
    """Dock host that owns one block-properties editor safely.

    The host supplies the native draggable title bar. Its allowed docking
    areas are deliberately restricted by the Dynamic Editor before display.
    Closing the host explicitly prepares the Qt-heavy child tree before Qt
    schedules the binary widgets for deletion.
    """

    closed = Signal()

    __slots__ = (
        "_properties_widget",
        "_prepared_to_delete",
    )

    def __init__(
            self,
            properties_widget: DynamicBlockPropertiesDialog,
            parent: QtWidgets.QMainWindow,
    ) -> None:
        """Create a dock around one property-editor widget.

        :param properties_widget: Block-property content to host.
        :param parent: Dynamic Editor main window that owns the dock.
        :return: None.
        """
        super().__init__(properties_widget.windowTitle(), parent)
        self._properties_widget: DynamicBlockPropertiesDialog = properties_widget
        self._prepared_to_delete: bool = False
        self.setObjectName("dynamicBlockPropertiesDock")
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self._properties_widget.set_dock_hosted(True)
        self._properties_widget.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.setWidget(self._properties_widget)
        self._properties_widget.closeRequested.connect(self.close)
        self.topLevelChanged.connect(self.configure_floating_close_only_frame)

    @QtCore.Slot(bool)
    def configure_floating_close_only_frame(self, floating: bool) -> None:
        """Match the DeviceEditor frame while the properties dock is floating.

        ``TemplateDeviceEditor`` is a regular ``QDialog`` and therefore uses
        the operating system's native close control. A floating ``QDockWidget``
        normally keeps Qt's themed dock close subcontrol instead. Selecting a
        native window frame with only ``WindowCloseButtonHint`` removes that
        visual mismatch without exposing non-functional minimize controls.

        :param floating: Whether the dock has become a top-level window.
        :return: None.
        """
        if floating:
            floating_flags: Qt.WindowType = (
                Qt.WindowType.Window
                | Qt.WindowType.CustomizeWindowHint
                | Qt.WindowType.WindowTitleHint
                | Qt.WindowType.WindowSystemMenuHint
                | Qt.WindowType.WindowCloseButtonHint
            )
            self.setWindowFlags(floating_flags)
            # Updating native decorations temporarily hides the widget. Show
            # it again before the opening code positions the floating dock.
            self.show()
        else:
            # Qt restores its embedded dock title bar after reattachment.
            pass

    def get_properties_widget(self) -> DynamicBlockPropertiesDialog:
        """Return the property-editor content owned by this dock.

        :return: Hosted property-editor widget.
        """
        return self._properties_widget

    def prepare_to_delete(self) -> None:
        """Prepare the hosted Qt object tree for deterministic destruction.

        :return: None.
        """
        if self._prepared_to_delete:
            pass
        else:
            self._prepared_to_delete = True
            try:
                self._properties_widget.closeRequested.disconnect(self.close)
            except (RuntimeError, TypeError):
                pass
            try:
                self.topLevelChanged.disconnect(self.configure_floating_close_only_frame)
            except (RuntimeError, TypeError):
                pass
            self._properties_widget.prepare_to_delete()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Prepare the child editor and notify its owning Dynamic Editor.

        :param event: Incoming dock close event.
        :return: None.
        """
        self.prepare_to_delete()
        self.closed.emit()
        QtWidgets.QDockWidget.closeEvent(self, event)
