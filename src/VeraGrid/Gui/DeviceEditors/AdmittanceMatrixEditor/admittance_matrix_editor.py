from __future__ import annotations

import numpy as np
from typing import Sequence

from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.DeviceEditors.AdmittanceMatrixEditor.admittance_matrix_editor_gui import (
    Ui_AdmittanceMatrixEditorWidget,
)
from VeraGrid.Gui.gui_functions import ComplexDelegate
from VeraGridEngine.Devices.admittance_matrix import AdmittanceMatrix


def project_admittance_matrix_to_phase_state(admittance_matrix: AdmittanceMatrix,
                                             phase_state: dict[str, bool]) -> AdmittanceMatrix:
    """
    Project one admittance matrix to the requested phase subset.

    Only the source indices of the active requested phases are copied into the returned
    compact matrix, preserving their ``N/A/B/C`` ordering.

    :param admittance_matrix: Source matrix.
    :param phase_state: Requested target phase state.
    :return: Projected admittance matrix.
    """
    ordered_labels: list[str] = list()
    label_to_index: dict[str, int] = {"N": 0, "A": 1, "B": 2, "C": 3}

    if phase_state["N"]:
        ordered_labels.append("N")
    else:
        pass

    if phase_state["A"]:
        ordered_labels.append("A")
    else:
        pass

    if phase_state["B"]:
        ordered_labels.append("B")
    else:
        pass

    if phase_state["C"]:
        ordered_labels.append("C")
    else:
        pass

    projected_matrix: AdmittanceMatrix = AdmittanceMatrix(size=len(ordered_labels))
    projected_values: np.ndarray = np.zeros((len(ordered_labels), len(ordered_labels)), dtype=complex)

    source_values: np.ndarray = np.zeros((4, 4), dtype=complex)
    source_rows: int = min(admittance_matrix.values.shape[0], 4)
    source_columns: int = min(admittance_matrix.values.shape[1], 4)
    source_values[:source_rows, :source_columns] = admittance_matrix.values[:source_rows, :source_columns]

    row_position: int
    row_label: str
    for row_position, row_label in enumerate(ordered_labels):
        column_position: int
        column_label: str
        for column_position, column_label in enumerate(ordered_labels):
            projected_values[row_position, column_position] = source_values[
                label_to_index[row_label],
                label_to_index[column_label],
            ]

    projected_matrix.values = projected_values
    projected_matrix.phN = phase_state["N"]
    projected_matrix.phA = phase_state["A"]
    projected_matrix.phB = phase_state["B"]
    projected_matrix.phC = phase_state["C"]
    return projected_matrix


class AdmittanceMatrixTableModel(QtCore.QAbstractTableModel):
    """
    Table model exposing one :class:`AdmittanceMatrix` as a dense complex matrix.
    """

    __slots__ = ("_active_phases", "_values")

    def __init__(self,
                 admittance_matrix: AdmittanceMatrix,
                 parent: QtCore.QObject | None = None) -> None:
        """
        Build the table model from one admittance matrix snapshot.

        :param admittance_matrix: Source matrix copied into the model.
        :param parent: Optional Qt parent.
        """
        QtCore.QAbstractTableModel.__init__(self, parent)

        self._active_phases: list[str] = list()
        self._values: np.ndarray = np.zeros((0, 0), dtype=complex)

        # Keep one local copy inside the model so edits stay isolated until the user applies them.
        self.load_from_admittance_matrix(admittance_matrix=admittance_matrix)

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return the visible matrix row count.

        :param parent: Unused parent index.
        :return: Number of rows.
        """
        _ = parent
        return len(self._active_phases)

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return the visible matrix column count.

        :param parent: Unused parent index.
        :return: Number of columns.
        """
        _ = parent
        return len(self._active_phases)

    def data(self,
             index: QtCore.QModelIndex,
             role: int = int(QtCore.Qt.ItemDataRole.DisplayRole)) -> complex | str | None:
        """
        Return the complex cell value for display and editing.

        :param index: Cell index.
        :param role: Qt data role.
        :return: Complex value, display text or ``None``.
        """
        if index.isValid():
            if role == int(QtCore.Qt.ItemDataRole.DisplayRole):
                return str(self._values[index.row(), index.column()])
            elif role == int(QtCore.Qt.ItemDataRole.EditRole):
                return complex(self._values[index.row(), index.column()])
            else:
                return None
        else:
            return None

    def setData(self,
                index: QtCore.QModelIndex,
                value: object,
                role: int = int(QtCore.Qt.ItemDataRole.EditRole)) -> bool:
        """
        Store one edited complex cell value.

        :param index: Target cell index.
        :param value: New complex-like value.
        :param role: Qt data role.
        :return: ``True`` when the value is accepted.
        """
        if index.isValid():
            if role == int(QtCore.Qt.ItemDataRole.EditRole):
                try:
                    complex_value: complex = complex(value)
                except (TypeError, ValueError):
                    return False

                self._values[index.row(), index.column()] = complex_value
                self.dataChanged.emit(index, index, [int(QtCore.Qt.ItemDataRole.DisplayRole)])
                return True
            else:
                return False
        else:
            return False

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        """
        Return the item flags for one matrix cell.

        :param index: Cell index.
        :return: Qt flags.
        """
        if index.isValid():
            return (QtCore.Qt.ItemFlag.ItemIsEnabled
                    | QtCore.Qt.ItemFlag.ItemIsSelectable
                    | QtCore.Qt.ItemFlag.ItemIsEditable)
        else:
            return QtCore.Qt.ItemFlag.NoItemFlags

    def headerData(self,
                   section: int,
                   orientation: QtCore.Qt.Orientation,
                   role: int = int(QtCore.Qt.ItemDataRole.DisplayRole)) -> str | None:
        """
        Return row and column phase labels.

        :param section: Header section index.
        :param orientation: Header orientation.
        :param role: Qt data role.
        :return: Phase label or ``None``.
        """
        if role == int(QtCore.Qt.ItemDataRole.DisplayRole):
            if section < len(self._active_phases):
                return self._active_phases[section]
            else:
                return ""
        else:
            return None

    def load_from_admittance_matrix(self, admittance_matrix: AdmittanceMatrix) -> None:
        """
        Replace the local state with one copied admittance matrix.

        :param admittance_matrix: Source value.
        """
        active_phases: list[str] = self._build_active_phase_list(
            phase_n=admittance_matrix.phN,
            phase_a=admittance_matrix.phA,
            phase_b=admittance_matrix.phB,
            phase_c=admittance_matrix.phC,
        )
        expected_size: int = len(active_phases)

        self.beginResetModel()
        self._active_phases = active_phases

        if expected_size > 0 and admittance_matrix.values.shape == (expected_size, expected_size):
            self._values = np.array(admittance_matrix.values, dtype=complex, copy=True)
        else:
            self._values = np.zeros((expected_size, expected_size), dtype=complex)
        self.endResetModel()

    def set_phase_enabled(self, phase_label: str, enabled: bool) -> None:
        """
        Toggle one phase and resize the matrix while preserving surviving rows and columns.

        :param phase_label: Phase identifier ``N``, ``A``, ``B`` or ``C``.
        :param enabled: Target enabled state.
        """
        current_phase_state: dict[str, bool] = self.get_phase_state()
        current_phase_state[phase_label] = enabled

        new_active_phases: list[str] = self._build_active_phase_list(
            phase_n=current_phase_state["N"],
            phase_a=current_phase_state["A"],
            phase_b=current_phase_state["B"],
            phase_c=current_phase_state["C"],
        )

        old_active_phases: list[str] = list(self._active_phases)
        old_values: np.ndarray = np.array(self._values, dtype=complex, copy=True)
        new_size: int = len(new_active_phases)
        new_values: np.ndarray = np.zeros((new_size, new_size), dtype=complex)

        # Preserve the entries that still have a matching phase on both axes after one toggle.
        for row_label in new_active_phases:
            if row_label in old_active_phases:
                old_row_index: int = old_active_phases.index(row_label)
                new_row_index: int = new_active_phases.index(row_label)
                for column_label in new_active_phases:
                    if column_label in old_active_phases:
                        old_column_index: int = old_active_phases.index(column_label)
                        new_column_index: int = new_active_phases.index(column_label)
                        new_values[new_row_index, new_column_index] = old_values[old_row_index, old_column_index]
                    else:
                        pass
            else:
                pass

        self.beginResetModel()
        self._active_phases = new_active_phases
        self._values = new_values
        self.endResetModel()

    def get_phase_state(self) -> dict[str, bool]:
        """
        Return the current enabled state of all four supported phases.

        :return: Mapping of phase label to enabled flag.
        """
        phase_state: dict[str, bool] = dict()
        phase_state["N"] = "N" in self._active_phases
        phase_state["A"] = "A" in self._active_phases
        phase_state["B"] = "B" in self._active_phases
        phase_state["C"] = "C" in self._active_phases
        return phase_state

    def to_admittance_matrix(self) -> AdmittanceMatrix:
        """
        Build one engine object from the current edited state.

        :return: New :class:`AdmittanceMatrix` instance.
        """
        phase_state: dict[str, bool] = self.get_phase_state()
        admittance_matrix: AdmittanceMatrix = AdmittanceMatrix(size=len(self._active_phases))
        admittance_matrix.phN = phase_state["N"]
        admittance_matrix.phA = phase_state["A"]
        admittance_matrix.phB = phase_state["B"]
        admittance_matrix.phC = phase_state["C"]
        admittance_matrix.values = np.array(self._values, dtype=complex, copy=True)
        return admittance_matrix

    @staticmethod
    def _build_active_phase_list(phase_n: bool,
                                 phase_a: bool,
                                 phase_b: bool,
                                 phase_c: bool) -> list[str]:
        """
        Build the ordered list of active phases.

        :param phase_n: Neutral flag.
        :param phase_a: Phase A flag.
        :param phase_b: Phase B flag.
        :param phase_c: Phase C flag.
        :return: Ordered phase labels.
        """
        active_phases: list[str] = list()

        if phase_n:
            active_phases.append("N")
        else:
            pass

        if phase_a:
            active_phases.append("A")
        else:
            pass

        if phase_b:
            active_phases.append("B")
        else:
            pass

        if phase_c:
            active_phases.append("C")
        else:
            pass

        return active_phases


class AdmittanceMatrixEditorWidget(QtWidgets.QWidget):
    """
    Reusable editor widget for the ``ys`` and ``ysh`` admittance matrices.
    """

    __slots__ = ("ui", "_ys_model", "_ysh_model")
    compute_requested = QtCore.Signal()
    accept_requested = QtCore.Signal()

    def __init__(self,
                 ys_admittance_matrix: AdmittanceMatrix | None,
                 ysh_admittance_matrix: AdmittanceMatrix | None,
                 title: str,
                 description: str,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """
        Build the editor widget.

        :param ys_admittance_matrix: Initial ``ys`` value copied into the widget.
        :param ysh_admittance_matrix: Initial ``ysh`` value copied into the widget.
        :param title: User-facing matrix title.
        :param description: Short description shown above the table.
        :param parent: Optional Qt parent.
        """
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = Ui_AdmittanceMatrixEditorWidget()
        self.ui.setupUi(self)
        self.ui.titleLabel.setText(title)
        self.ui.descriptionLabel.setText(description)
        self._ys_model: AdmittanceMatrixTableModel | None = None
        self._ysh_model: AdmittanceMatrixTableModel | None = None

        if ys_admittance_matrix is not None:
            self._ys_model = AdmittanceMatrixTableModel(
                admittance_matrix=ys_admittance_matrix,
                parent=self.ui.matrixTableView,
            )
            self.ui.matrixTableView.setModel(self._ys_model)
            self._configure_table(table_view=self.ui.matrixTableView)
            self.ui.matrixTableView.setVisible(True)
        else:
            self.ui.matrixTableView.setVisible(False)

        if ysh_admittance_matrix is not None:
            self._ysh_model = AdmittanceMatrixTableModel(
                admittance_matrix=ysh_admittance_matrix,
                parent=self.ui.yshTableView,
            )
            self.ui.yshTableView.setModel(self._ysh_model)
            self._configure_table(table_view=self.ui.yshTableView)
            self.ui.yshLabel.setVisible(True)
            self.ui.yshTableView.setVisible(True)
        else:
            self.ui.yshLabel.setVisible(False)
            self.ui.yshTableView.setVisible(False)

        self._apply_phase_state_to_check_boxes(phase_state=self.get_phase_state())

        self.ui.phaseNCheckBox.toggled.connect(self._on_phase_n_toggled)
        self.ui.phaseACheckBox.toggled.connect(self._on_phase_a_toggled)
        self.ui.phaseBCheckBox.toggled.connect(self._on_phase_b_toggled)
        self.ui.phaseCCheckBox.toggled.connect(self._on_phase_c_toggled)
        self.ui.computeButton.clicked.connect(self.compute_requested.emit)
        self.ui.acceptButton.clicked.connect(self.accept_requested.emit)

    def get_admittance_matrices(self) -> dict[str, AdmittanceMatrix]:
        """
        Return the edited admittance matrices.

        :return: Edited values keyed by property name.
        """
        admittance_matrices: dict[str, AdmittanceMatrix] = dict()

        if self._ys_model is not None:
            admittance_matrices["ys"] = self._ys_model.to_admittance_matrix()
        else:
            pass

        if self._ysh_model is not None:
            admittance_matrices["ysh"] = self._ysh_model.to_admittance_matrix()
        else:
            pass

        return admittance_matrices

    def set_admittance_matrices(self,
                                ys_admittance_matrix: AdmittanceMatrix | None,
                                ysh_admittance_matrix: AdmittanceMatrix | None) -> None:
        """
        Replace the edited state with the provided object values.

        :param ys_admittance_matrix: New ``ys`` source value.
        :param ysh_admittance_matrix: New ``ysh`` source value.
        """
        if ys_admittance_matrix is not None and self._ys_model is not None:
            self._ys_model.load_from_admittance_matrix(admittance_matrix=ys_admittance_matrix)
        else:
            pass

        if ysh_admittance_matrix is not None and self._ysh_model is not None:
            self._ysh_model.load_from_admittance_matrix(admittance_matrix=ysh_admittance_matrix)
        else:
            pass

        self._apply_phase_state_to_check_boxes(phase_state=self.get_phase_state())

    def get_phase_state(self) -> dict[str, bool]:
        """
        Return the currently selected phase state.

        :return: Mapping of phase label to enabled flag.
        """
        if self._ys_model is not None:
            return self._ys_model.get_phase_state()
        elif self._ysh_model is not None:
            return self._ysh_model.get_phase_state()
        else:
            phase_state: dict[str, bool] = dict()
            phase_state["N"] = False
            phase_state["A"] = False
            phase_state["B"] = False
            phase_state["C"] = False
            return phase_state

    def _configure_table(self, table_view: QtWidgets.QTableView) -> None:
        """
        Configure one admittance-matrix table view.

        :param table_view: Target table view.
        """
        table_view.setItemDelegate(ComplexDelegate(table_view))
        table_view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        table_view.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

    def _apply_phase_state_to_check_boxes(self, phase_state: dict[str, bool]) -> None:
        """
        Synchronize check boxes with one phase-state mapping.

        :param phase_state: Mapping of phase label to enabled flag.
        """
        check_boxes: Sequence[tuple[QtWidgets.QCheckBox, str]] = (
            (self.ui.phaseNCheckBox, "N"),
            (self.ui.phaseACheckBox, "A"),
            (self.ui.phaseBCheckBox, "B"),
            (self.ui.phaseCCheckBox, "C"),
        )

        check_box: QtWidgets.QCheckBox
        phase_label: str
        for check_box, phase_label in check_boxes:
            check_box.blockSignals(True)
            check_box.setChecked(phase_state[phase_label])
            check_box.blockSignals(False)

    def _on_phase_n_toggled(self, checked: bool) -> None:
        """
        Resize the matrix when neutral is toggled.

        :param checked: Target state.
        """
        self._set_phase_enabled(phase_label="N", checked=checked)

    def _on_phase_a_toggled(self, checked: bool) -> None:
        """
        Resize the matrix when phase A is toggled.

        :param checked: Target state.
        """
        self._set_phase_enabled(phase_label="A", checked=checked)

    def _on_phase_b_toggled(self, checked: bool) -> None:
        """
        Resize the matrix when phase B is toggled.

        :param checked: Target state.
        """
        self._set_phase_enabled(phase_label="B", checked=checked)

    def _on_phase_c_toggled(self, checked: bool) -> None:
        """
        Resize the matrix when phase C is toggled.

        :param checked: Target state.
        """
        self._set_phase_enabled(phase_label="C", checked=checked)

    def _set_phase_enabled(self, phase_label: str, checked: bool) -> None:
        """
        Apply one phase toggle to every visible admittance matrix model.

        :param phase_label: Phase identifier.
        :param checked: Target state.
        """
        if self._ys_model is not None:
            self._ys_model.set_phase_enabled(phase_label, checked)
        else:
            pass

        if self._ysh_model is not None:
            self._ysh_model.set_phase_enabled(phase_label, checked)
        else:
            pass
