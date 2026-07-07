from __future__ import annotations

import re
from typing import Dict, List, Optional, Set

from PySide6 import QtGui, QtWidgets
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLabel, \
    QLineEdit, QPlainTextEdit, QVBoxLayout

from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, get_symbolic_parser_function_names, string_to_symbolic
from VeraGridEngine.enumerations import DeviceType, ParamPowerFlowReferenceType
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_models import is_valid_symbol_name


class GenericBlockDialog(QDialog):
    """
    Dialog to edit the created generic block.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Generic Block")

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        layout.addRow("Block name:", self.name_edit)

        self.inputs_spin = QtWidgets.QSpinBox()
        self.inputs_spin.setMinimum(1)
        self.inputs_spin.setValue(1)
        layout.addRow("Number of inputs:", self.inputs_spin)

        self.outputs_spin = QtWidgets.QSpinBox()
        self.outputs_spin.setMinimum(1)
        self.outputs_spin.setValue(1)
        layout.addRow("Number of outputs:", self.outputs_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_values(self):
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
        return (
            self.phase_n_check.isChecked(),
            self.phase_a_check.isChecked(),
            self.phase_b_check.isChecked(),
            self.phase_c_check.isChecked()
        )


class ExpressionTextEditorDialog(QDialog):
    """
    Dialog used to inspect or edit a symbolic expression as text.
    """

    def __init__(self,
                 expression_text: str,
                 symbol_namespace: Dict[str, Expr],
                 parent: Optional[QtWidgets.QWidget] = None):
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
        return self.text_editor.toPlainText().strip()

    def update_validation_state(self) -> None:
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
    CATEGORY_OPTIONS: List[tuple[str, str]] = [
        ("Event Parameter", "event_parameter"),
        ("Mode Parameter", "mode_parameter"),
        ("Static Parameter", "parameter"),
    ]

    def __init__(self,
                 api_object: ALL_DEV_TYPES,
                 devices_static_params_mapping: Dict[DeviceType, List[ParamPowerFlowReferenceType]],
                 parent: Optional[QtWidgets.QWidget] = None):
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
            param: ParamPowerFlowReferenceType
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

        label: str
        value: str
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
        equation_text: str = self.get_equation_text()

        if len(equation_text) == 0:
            self.validation_label.setText("Enter an equation.")
            self.validation_label.setStyleSheet("color: #b42318;")
            self.ok_button.setEnabled(False)
            return
        else:
            pass

        try:
            string_to_symbolic(equation_text, self.symbol_namespace)
            self.validation_label.setText("Equation is valid.")
            self.validation_label.setStyleSheet("color: #027a48;")
            self.ok_button.setEnabled(True)
        except Exception as exc:
            self.validation_label.setText(str(exc))
            self.validation_label.setStyleSheet("color: #b42318;")
            self.ok_button.setEnabled(False)


class ExpressionValidationHighlighter(QtGui.QSyntaxHighlighter):
    IDENTIFIER_PATTERN = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")

    def __init__(self,
                 document: QtGui.QTextDocument,
                 symbol_names: Set[str],
                 function_names: Set[str]):
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
        current_index: int = token_end

        while current_index < len(text) and text[current_index].isspace():
            current_index += 1

        if current_index < len(text):
            return text[current_index] == "("
        else:
            return False

    def get_unknown_identifiers(self, text: str) -> List[str]:
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
