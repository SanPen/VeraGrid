# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import uuid
import copy
from typing import List, Dict, Optional, Union, Sequence, Any
import VeraGrid.Gui.gui_functions as gf
from PySide6 import QtWidgets
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QGraphicsScene, QGraphicsView, QGraphicsItem,
                               QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem, QMenu, QGraphicsPathItem,
                               QDialog, QVBoxLayout, QDialogButtonBox, QSplitter, QLabel, QDoubleSpinBox,
                               QListView, QAbstractItemView, QPushButton, QListWidget, QWidget,
                               QListWidgetItem, QFormLayout, QSpinBox, QLineEdit, QTableWidget, QTableWidgetItem,
                               QColorDialog, QCheckBox)
from PySide6.QtGui import (QPen, QBrush, QPainterPath, QAction, QPainter, QIcon, QStandardItemModel, QStandardItem,
                           QDropEvent, QDragEnterEvent, QDragMoveEvent, QColor)
from PySide6.QtCore import Qt, QPointF, QByteArray, QDataStream, QIODevice, QModelIndex, QMimeData, Signal

from VeraGridEngine import RmsModelTemplate
from VeraGridEngine.Templates.Rms.genqec_exc_gov_sat_template import (get_genqec_rms,
                                                                      get_governor_rms,
                                                                      get_stabilizer_rms,
                                                                      get_exciter_rms)
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Templates.Rms.genrow_rms_template import get_genrow_rms_template
from VeraGridEngine.Templates.Rms.line_rms_template import get_line_rms_template
from VeraGridEngine.Templates.Rms.load_rms_template import get_load_rms_template
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Templates.predefined_blocks import (
    constant,
    gain,
    adder,
    substract,
    product,
    divide,
    absolut,
    generic
)
from VeraGridEngine.Templates.Rms.bus_rms_template import initialize_bus_rms, get_bus_rms_algebraic_vars

from VeraGrid.Gui.messages import error_msg
from VeraGridEngine.Utils.Symbolic.symbolic import symbolic_to_string, Expr, Var, Const
from VeraGridEngine.Devices.Diagrams.block_diagram import BlockDiagram
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowRefferenceType, ParamPowerFlowRefferenceType, BlockType


def create_generic_block(var_factory: VarFactory,
                         state_inputs: int,
                         state_outputs: Sequence[str],
                         algebraic_inputs: int,
                         algebraic_outputs: Sequence[str]):
    """

    :param var_factory:
    :param state_inputs:
    :param state_outputs:
    :param algebraic_inputs:
    :param algebraic_outputs:
    :return:
    """
    blk = generic(var_factory, state_inputs, state_outputs, algebraic_inputs, algebraic_outputs)
    blk.name = "generic"
    return blk

def _new_uid() -> int:
    """
    Generate a fresh UUID‑v4 string.
    :return: UUIDv4 in integer format
    """
    return uuid.uuid4().int


def change_font_size(obj, font_size: int):
    """

    :param obj:
    :param font_size:
    :return:
    """
    font1 = obj.font()
    font1.setPointSize(font_size)
    obj.setFont(font1)




class ResizeHandle(QGraphicsRectItem):
    """
    Interactive resize handle for a BlockItem.

    Allows the user to resize the parent BlockItem by dragging it with the mouse,
    converting handle movement into controlled BlockItem size changes with minimum limits.
    """

    def __init__(self, block_item, size=10):
        super().__init__(0, 0, size, size, block_item)
        self.setBrush(QBrush(Qt.GlobalColor.darkGray))
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.setZValue(2)
        self.block = block_item
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if not self.block.resizing_from_handle:
                return super().itemChange(change, value)
            new_pos = value
            min_width, min_height = 40, 30
            new_width = max(new_pos.x(), min_width)
            new_height = max(new_pos.y(), min_height)

            self.block.resize_block(new_width, new_height)

            return QPointF(new_width, new_height)
        return super().itemChange(change, value)


class PortItem(QGraphicsEllipseItem):
    """
    Port of a block
    """

    def __init__(self,
                 subsystem: Union[BlockItem, ModelHostItem],
                 is_input: bool,
                 index: int,  # number of inputs
                 total: int,
                 radius=6):
        """

        :param block:
        :param is_input:
        :param index:
        :param total:
        :param radius:
        """
        super().__init__(-radius, -radius, 2 * radius, 2 * radius, subsystem)
        self.setBrush(QBrush(Qt.GlobalColor.blue if is_input else Qt.GlobalColor.green))
        self.setPen(QPen(Qt.GlobalColor.black))
        self.setZValue(1)
        self.setAcceptHoverEvents(True)
        self.subsystem = subsystem
        self.is_input = is_input
        self.connections: List[ConnectionItem] | None = None
        self.index = index
        self.total = total

        spacing = subsystem.rect().height() / (total + 1)
        y = spacing * (index + 1)
        x = 0 if is_input else subsystem.rect().width()
        self.setPos(x, y)

    # enable showing variables related to the port when the mouse enters the port circle
    def hoverEnterEvent(self, event):
        QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)

    def hoverLeaveEvent(self, event):
        QApplication.restoreOverrideCursor()

    def is_connected(self):
        return self.connections is not None


class ConnectionItem(QGraphicsPathItem):
    def __init__(self, source_port, target_port):
        super().__init__()
        self.uid: int = _new_uid()
        self.setZValue(-1)
        self.source_port = source_port
        self.target_port = target_port
        self.source_port.connections = list()
        self.source_port.connections.append(self)
        self.target_port.connections = list()
        self.target_port.connections.append(self)
        self.setPen(QPen(Qt.GlobalColor.darkBlue, 2))
        self.setAcceptHoverEvents(True)

        self.update_path()

    def update_path(self):
        start = self.source_port.scenePos()
        end = self.target_port.scenePos()
        mid_x = (start.x() + end.x()) / 2
        c1 = QPointF(mid_x, start.y())
        c2 = QPointF(mid_x, end.y())
        path = QPainterPath(start)
        path.cubicTo(c1, c2, end)
        self.setPath(path)

    def hoverEnterEvent(self, event):
        QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)

    def hoverLeaveEvent(self, event):
        QApplication.restoreOverrideCursor()


class BlockItem(QGraphicsRectItem):
    def __init__(self, var_factory: VarFactory, name: str):
        """
        Class to represent devices in the editor
        :param name:
        """
        super().__init__(0, 0, 100, 60)

        self.var_factory = var_factory
        self.name = name
        self.resize_handle: ResizeHandle | None = None
        self.resizing_from_handle = False
        self.subsys: Block | None = None
        self.name_item: QGraphicsTextItem | None = None
        self.inputs: List[PortItem] = list()
        self.outputs: List[PortItem] = list()

        # ---------------------------
        # Graphical stuff
        # ---------------------------
        self.setBrush(Qt.GlobalColor.lightGray)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )

        self.setAcceptHoverEvents(True)

        self.setBrush(QBrush(QColor("#C0C0C0")))

    def set_subsystem(self, block: Block):
        self.subsys = block

    def build_item(self):
        self.name_item = QGraphicsTextItem(self.name, self)

        self.name_item.setPos(10, 5)

        n_inputs = len(self.subsys.in_vars)
        n_outputs = len(self.subsys.out_vars)

        self.inputs = [PortItem(self, True, i, n_inputs) for i in range(n_inputs)]
        self.outputs = [PortItem(self, False, i, n_outputs) for i in range(n_outputs)]

        # --- assign tooltips to portitems with the corresponding variable names---
        for i, port in enumerate(self.inputs):
            var_name = self.subsys.in_vars[i].name
            port.setToolTip(f"Input {i}: {var_name}")

        for i, port in enumerate(self.outputs):
            var_name = self.subsys.out_vars[i].name
            port.setToolTip(f"Output {i}: {var_name}")

        self.resize_handle = ResizeHandle(self)

        super().setRect(0, 0, 100, 60)
        self.update_ports()
        self.update_handle_position()

    def mouseDoubleClickEvent(self, event):
        if self.subsys is not None:

            dialog = ParameterEditorDialog(
                var_factory=self.var_factory,
                event_dict=self.subsys.event_dict,
                parameters_dict=self.subsys.parameters,
                parent=None
            )

            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.subsys.event_dict = dialog.event_dict
                self.subsys.parameters = dialog.parameters

            event.accept()

        super().mouseDoubleClickEvent(event)

    def resize_block(self, width, height):
        # Update geometry safely
        self.prepareGeometryChange()
        QGraphicsRectItem.setRect(self, 0, 0, width, height)
        self.update_ports()
        self.update_handle_position()

    def update_handle_position(self):
        rect = self.rect()
        self.resizing_from_handle = False
        self.resize_handle.setPos(rect.width(), rect.height())
        self.resizing_from_handle = True

    def _set_rect_internal(self, w, h):
        QGraphicsRectItem.setRect(self, 0, 0, w, h)
        self.update_ports()
        self.update_handle_position()

    def set_rectangle(self, x, y, w, h):
        if not getattr(self, '_suppress_resize', False):
            self._set_rect_internal(w, h)

    def update_ports(self):
        for i, port in enumerate(self.inputs):
            spacing = self.rect().height() / (len(self.inputs) + 1)
            port.setPos(0, spacing * (i + 1))
        for i, port in enumerate(self.outputs):
            spacing = self.rect().height() / (len(self.outputs) + 1)
            port.setPos(self.rect().width(), spacing * (i + 1))
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
            for port in self.inputs + self.outputs:
                if port.connections:
                    for conn in port.connections:
                        conn.update_path()
        return super().itemChange(change, value)


class ModelHostItem(QGraphicsRectItem):
    """
           Class to represent generic block to construct devices in the editor
           :param name:
           """

    def __init__(self,
                 var_factory: VarFactory,
                 block_sys: Block,
                 api_object_name,
                 api_object,
                 templates_list,
                 templates_catalogue):
        """

        :param var_factory:
        :param block_sys:
        :param api_object_name:
        :param api_object:
        :param templates_list:
        :param templates_catalogue:
        """
        super().__init__(0, 0, 100, 60)

        # ------------------------
        # API
        # ------------------------
        self.var_factory = var_factory
        self.block = block_sys
        self.resize_handle: ResizeHandle | None = None
        self.resizing_from_handle = False
        self.api_object_name = api_object_name
        self.templates_list = templates_list
        self.templates_catalogue = templates_catalogue
        self.api_object = api_object
        self.name_item = QGraphicsTextItem(self.block.name, self)
        self.inputs: List[PortItem] = list()
        self.outputs: List[PortItem] = list()
        self.editor_window = RmsModelEditorGUI(
            var_factory=self.var_factory,
            block=self.block,
            templates_list=self.templates_list,
            templates_catalogue=self.templates_catalogue,
            api_object_name=self.api_object_name,
            api_object=self.api_object
        )

        self.setBrush(QBrush(QColor("#C0C0C0")))
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)
        self.name_item.setPos(10, 5)

        n_inputs = len(self.block.in_vars)
        n_outputs = len(self.block.out_vars)

        self.inputs = [PortItem(self, True, i, n_inputs) for i in range(n_inputs)]
        self.outputs = [PortItem(self, False, i, n_outputs) for i in range(n_outputs)]

        # --- assign tooltips to portItems with the assigned variable name ---
        for i, port in enumerate(self.inputs):
            var_name = self.block.in_vars[i].name
            port.setToolTip(f"Input {i}: {var_name}")

        for i, port in enumerate(self.outputs):
            var_name = self.block.out_vars[i].name
            port.setToolTip(f"Output {i}: {var_name}")

        self.resize_handle = ResizeHandle(self)

        super().setRect(0, 0, 100, 60)
        self.update_ports()
        self.update_handle_position()

    @property
    def subsys(self):
        return self.block

    def mouseDoubleClickEvent(self, event):
        """
        opens the editor
        Parameters
        ----------
        event :

        Returns
        -------

        """
        self.editor_window.show()

    def resize_block(self, width, height):
        # Update geometry safely
        self.prepareGeometryChange()
        QGraphicsRectItem.setRect(self, 0, 0, width, height)
        self.update_ports()
        self.update_handle_position()

    def update_handle_position(self):
        rect = self.rect()
        self.resizing_from_handle = False
        self.resize_handle.setPos(rect.width(), rect.height())
        self.resizing_from_handle = True

    def _set_rect_internal(self, w, h):
        QGraphicsRectItem.setRect(self, 0, 0, w, h)
        self.update_ports()
        self.update_handle_position()

    def set_rectangle(self, x, y, w, h):
        if not getattr(self, '_suppress_resize', False):
            self._set_rect_internal(w, h)

    def update_ports(self):
        for i, port in enumerate(self.inputs):
            spacing = self.rect().height() / (len(self.inputs) + 1)
            port.setPos(0, spacing * (i + 1))
        for i, port in enumerate(self.outputs):
            spacing = self.rect().height() / (len(self.outputs) + 1)
            port.setPos(self.rect().width(), spacing * (i + 1))
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
            for port in self.inputs + self.outputs:
                if port.connections:
                    for conn in port.connections:
                        conn.update_path()
        return super().itemChange(change, value)


class ParameterEditorDialog(QDialog):
    """
    Dialog to edit event-driven parameters of a model.

    Shows a 2-column table:
        Parameter | Value

    Editable:
        - Only parameters coming from event_dict with Const values

    Non-editable:
        - Fixed parameters (parameters_dict)
        - Event-driven expressions
    """

    parametersUpdated = Signal(dict)

    def __init__(self,
                 var_factory: VarFactory,
                 event_dict: Dict[Var, Expr],
                 parameters_dict: Dict[Var, Const],
                 parent=None, ):
        super().__init__(parent)

        self.setWindowTitle("Edit Model Parameters")
        self.resize(450, 350)

        # ---- Work on COPIES ----
        self.var_factory = var_factory
        self.event_dict: Dict[Var, Expr] = copy.deepcopy(event_dict)
        self.parameters: Dict[Var, Const] = copy.deepcopy(parameters_dict)

        # Keeps row -> Var mapping
        self._vars_order: list["Var"] = list()

        # ---- Layout ----
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Edit the values:"))

        # ---- Table ----
        self.params_table = QTableWidget(self)
        self.params_table.setColumnCount(2)
        self.params_table.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.params_table.horizontalHeader().setStretchLastSection(True)
        self.params_table.verticalHeader().setVisible(False)
        self.params_table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.AllEditTriggers
        )
        layout.addWidget(self.params_table)

        # ---- Buttons ----
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # ---- Fill table ----
        self.load_params_table()
        self.load_fix_params_table()

        self.params_table.cellChanged.connect(self.on_cell_changed)

    # ------------------------------------------------------------------
    # Table filling
    # ------------------------------------------------------------------

    def load_params_table(self):
        """Editable parameters coming from event_dict"""
        self.params_table.blockSignals(True)

        for var, expr in self.event_dict.items():
            row = self.params_table.rowCount()
            self.params_table.insertRow(row)

            self._vars_order.append(var)

            # Parameter name (read-only)
            name_item = QTableWidgetItem(var.name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.params_table.setItem(row, 0, name_item)

            # Parameter value
            if hasattr(expr, "value"):
                value_item = QTableWidgetItem(str(expr.value))
                value_item.setFlags(
                    Qt.ItemFlag.ItemIsEnabled |
                    Qt.ItemFlag.ItemIsEditable
                )
            else:
                # Expression driven by event -> not editable
                value_item = QTableWidgetItem(str(expr))
                value_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

            self.params_table.setItem(row, 1, value_item)

        self.params_table.blockSignals(False)
        self.params_table.resizeColumnsToContents()

    def load_fix_params_table(self):
        """Non-editable fixed parameters"""
        self.params_table.blockSignals(True)

        for var, const in self.parameters.items():
            row = self.params_table.rowCount()
            self.params_table.insertRow(row)

            name_item = QTableWidgetItem(var.name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.params_table.setItem(row, 0, name_item)

            value = "" if const.value is None else str(const.value)
            value_item = QTableWidgetItem(value)
            value_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.params_table.setItem(row, 1, value_item)

        self.params_table.blockSignals(False)
        self.params_table.resizeColumnsToContents()

    # ------------------------------------------------------------------
    # Editing logic
    # ------------------------------------------------------------------

    def on_cell_changed(self, row: int, column: int):
        if column != 1:
            return

        if row >= len(self._vars_order):
            return

        var = self._vars_order[row]
        item = self.params_table.item(row, 1)
        if item is None:
            return

        text = item.text()

        try:
            value = float(text)
        except ValueError:
            value = text

        self.event_dict[var] = self.var_factory.add_const(value=value, name=var.name)

        # Optional: live update signal
        self.parametersUpdated.emit(self.event_dict)


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
        for submodel in getattr(model, "children", []):
            self.refresh_lists(submodel, clear=False)


class InitialValuesDialog(QDialog):
    """
    Dialog to edit initial Const values for each Var.
    Now receives a dict[Var, Const] and also includes a checkbox
    per row so the user can select which entries to return.
    Will be necessary for numerical initialization
    """

    def __init__(self,
                 var_factory: VarFactory,
                 var_const_dict: Dict[Var, Const],
                 parent: Optional[QtWidgets.QWidget] = None):
        """

        :param var_const_dict:
        :param parent:
        """
        super().__init__(parent)
        self.setWindowTitle("Initial Values")

        self.var_factory = var_factory
        self.var_const_dict = var_const_dict

        layout = QVBoxLayout(self)

        # Table with CHECKBOX + NAME + VALUE
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Use", "Variable", "Initial Value"])
        self.table.setRowCount(len(var_const_dict))
        self.table.horizontalHeader().setStretchLastSection(True)

        for row, (var, const) in enumerate(var_const_dict.items()):
            # --- Column 0: CHECKBOX ---
            chk = QCheckBox()
            chk.setChecked(True)  # marked by default
            self.table.setCellWidget(row, 0, chk)

            # --- Column 1: Variable name (not editable) ---
            name_item = QTableWidgetItem(var.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, name_item)

            # --- Column 2: SpinBox with initial value ---
            spin = QDoubleSpinBox()
            spin.setDecimals(6)
            spin.setRange(-1e12, 1e12)
            spin.setValue(float(const.value))
            self.table.setCellWidget(row, 2, spin)

        layout.addWidget(self.table)

        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_values_dict(self) -> Dict[Var, Const]:
        """
        Return a dict containing only the rows whose checkbox is checked.
        """
        result: Dict[Var, Const] = {}

        for row, (var, old_const) in enumerate(self.var_const_dict.items()):

            # Checkbox must be checked
            chk = self.table.cellWidget(row, 0)
            if not chk.isChecked():
                continue  # skip this row

            # Read spinbox value
            spin = self.table.cellWidget(row, 2)
            new_value = float(spin.value())

            result[var] = self.var_factory.add_const(new_value)

        return result


class GenericBlockDialog(QDialog):
    """
    Dialog to edit the created generic block
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Generic Block")

        layout = QFormLayout(self)

        # --- New: name field ---
        self.name_edit = QLineEdit()
        layout.addRow("Block name:", self.name_edit)

        # --- Existing fields ---
        self.state_inputs_spin = QSpinBox()
        self.state_inputs_spin.setMinimum(0)
        layout.addRow("Number of state inputs:", self.state_inputs_spin)

        self.state_outputs_edit = QLineEdit()
        layout.addRow("State outputs (comma separated):", self.state_outputs_edit)

        self.algeb_inputs_spin = QSpinBox()
        self.algeb_inputs_spin.setMinimum(0)
        layout.addRow("Number of algebraic inputs:", self.algeb_inputs_spin)

        self.algeb_outputs_edit = QLineEdit()
        layout.addRow("Algebraic outputs (comma separated):", self.algeb_outputs_edit)

        # --- Buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_values(self):
        """Return all dialog values."""
        name = self.name_edit.text().strip()
        state_ins = self.state_inputs_spin.value()
        state_outs = [s.strip() for s in self.state_outputs_edit.text().split(",") if s.strip()]
        algeb_ins = self.algeb_inputs_spin.value()
        algeb_outs = [s.strip() for s in self.algeb_outputs_edit.text().split(",") if s.strip()]
        return name, state_ins, state_outs, algeb_ins, algeb_outs


class GraphicsView(QGraphicsView):
    """
    GraphicsView
    """

    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHints(self.renderHints() | QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        # self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self._panning = False
        self._pan_start = QPointF()

    def wheelEvent(self, event):
        """

        :param event:
        :return:
        """
        zoom_in = event.angleDelta().y() > 0
        zoom_factor = 1.15 if zoom_in else 1 / 1.15
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):
        """

        :param event:
        :return:
        """
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """

        :param event:
        :return:
        """
        if self._panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() - delta.x()))
            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() - delta.y()))
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """

        :param event:
        :return:
        """
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)


class DiagramScene(QGraphicsScene):
    """
    DiagramScene
    """

    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.temp_line = None
        self.source_port = None

        self._main_block = Block()

    def get_main_block(self):
        """

        :return:
        """
        return self._main_block

    def change_item_fill_color(self, item: Union[BlockItem, ModelHostItem, ConnectionItem]):
        """

        :param item:
        :return:
        """
        new_color = QColorDialog.getColor()
        if new_color.isValid():
            if isinstance(item, (BlockItem, ModelHostItem)):
                brush = item.brush()
                brush.setColor(new_color)
                item.setBrush(brush)
                self.update()

                # save new color in diagram
                self.editor.diagram.node_data[item.subsys.uid].color = new_color
            if isinstance(item, ConnectionItem):
                pen = item.pen()
                pen.setColor(new_color)
                item.setPen(pen)
                self.update()

                # save new color in diagram
                self.editor.diagram.con_data[item.uid].color = new_color

    def contextMenuEvent(self, event):
        """

        :param event:
        :return:
        """
        items = self.items(event.scenePos())
        if not items:
            return

        for item in items:
            if isinstance(item, (BlockItem, ModelHostItem, ConnectionItem)):
                menu = QMenu()

                remove_action = QAction("Remove Block", menu)
                menu.addAction(remove_action)
                remove_action.triggered.connect(lambda checked=False, it=item: self.editor.remove_item(it))

                color_action = QAction("Change Color", menu)
                # ✅ Don't call the function here, just connect the callable
                color_action.triggered.connect(lambda checked=False, it=item: self.change_item_fill_color(it))
                menu.addAction(color_action)

                # Show context menu at cursor
                menu.exec(event.screenPos())
                break

    def mousePressEvent(self, event):
        """

        :param event:
        :return:
        """
        for item in self.items(event.scenePos()):
            if isinstance(item, PortItem) and not item.is_input:
                self.source_port = item
                path = QPainterPath(item.scenePos())
                self.temp_line = self.addPath(path, QPen(Qt.PenStyle.DashLine))
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """

        :param event:
        :return:
        """
        if self.temp_line:
            start = self.source_port.scenePos()
            end = event.scenePos()
            mid_x = (start.x() + end.x()) / 2
            c1 = QPointF(mid_x, start.y())
            c2 = QPointF(mid_x, end.y())
            path = QPainterPath(start)
            path.cubicTo(c1, c2, end)
            self.temp_line.setPath(path)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """

        :param event:
        :return:
        """
        if self.temp_line:
            # FIX: scan items under mouse for a valid input Port
            for item in self.items(event.scenePos()):
                if isinstance(item, PortItem) and item.is_input and not item.is_connected():
                    dst_port: PortItem = item
                    connection = ConnectionItem(self.source_port, dst_port)

                    dst_port.connections = list()
                    dst_port.connections.append(connection)

                    if self.source_port.connections is None:
                        self.source_port.connections = list()
                        self.source_port.connections.append(connection)
                    else:
                        self.source_port.connections.append(connection)

                    dst_var = self.source_port.subsystem.subsys.out_vars[self.source_port.index]

                    # update destiny model
                    dst_port.subsystem.subsys.update_model(dst_port.subsystem.subsys.in_vars[dst_port.index], dst_var)

                    for key, value in self.editor.main_block.external_mapping.items():
                        if dst_port.subsystem.subsys.in_vars[dst_port.index] is value:
                            self.editor.main_block.external_mapping[key] = dst_var
                    dst_port.subsystem.subsys.in_vars[dst_port.index] = dst_var

                    self.addItem(connection)

                    color = connection.pen().color().name()
                    # save branches in diagram
                    self.editor.diagram.add_branch(connection.uid, self.source_port.subsystem.subsys.uid,
                                                   dst_port.subsystem.subsys.uid, self.source_port.index,
                                                   dst_port.index, color)
                    break

            self.removeItem(self.temp_line)
            self.temp_line = None
            self.source_port = None
        else:
            super().mouseReleaseEvent(event)


class BaseLibraryModel(QStandardItemModel):
    """

    """

    MIME_TYPE = "component/name"

    def __init__(self) -> None:
        super().__init__()
        self.setColumnCount(1)
        self.mime_dict: dict[QByteArray, BlockType] = {}

    def add(self, bt: BlockType, icon_name: str):
        icon = QIcon(f":/Icons/icons/{icon_name}.png")
        item = QStandardItem(icon, bt.name)
        item.setToolTip(f"Drag & drop {bt.name}")
        item.setFlags(
            Qt.ItemFlag.ItemIsEnabled |
            Qt.ItemFlag.ItemIsSelectable |
            Qt.ItemFlag.ItemIsDragEnabled
        )
        self.appendRow(item)

        data = self.to_bytes_array(bt.name)
        self.mime_dict[data] = bt

    def mimeData(self, idxs: list[QModelIndex]) -> QMimeData:
        mimedata = QMimeData()
        for idx in idxs:
            if idx.isValid():
                txt = self.data(idx, Qt.ItemDataRole.DisplayRole)
                data = self.to_bytes_array(txt)
                mimedata.setData(self.MIME_TYPE, data)
        return mimedata

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        return (
                Qt.ItemFlag.ItemIsEnabled |
                Qt.ItemFlag.ItemIsSelectable |
                Qt.ItemFlag.ItemIsDragEnabled
        )

    @staticmethod
    def to_bytes_array(val: str) -> QByteArray:
        data = QByteArray()
        stream = QDataStream(data, QIODevice.OpenModeFlag.WriteOnly)
        stream.writeQString(val)
        return data

    def get_type(self, t: QByteArray) -> BlockType | None:
        return self.mime_dict.get(t)


class MathLibraryModel(BaseLibraryModel):
    MIME_TYPE = "component/math"

    models: list[BlockType] = [
        BlockType.CONST,
        BlockType.GAIN,
        BlockType.SUM,
        BlockType.SUBSTR,
        BlockType.PRODUCT,
        BlockType.DIVIDE,
        BlockType.ABS,
    ]

    def __init__(self):
        super().__init__()
        for bt in self.models:
            self.add(bt, "dyn")


class DevLibraryModel(BaseLibraryModel):
    MIME_TYPE = "component/dev"

    models: list[BlockType] = [
        BlockType.GENRAW,
        BlockType.GENQEC,
        BlockType.GOV_RMS,
        BlockType.STAB_RMS,
        BlockType.EXCITER,
        BlockType.LINE_RMS,
        BlockType.LOAD_RMS,
        BlockType.GENERIC,
        BlockType.BUS_CONNECTION,
        BlockType.EXTERNAL_MAPPING,
    ]

    def __init__(self):
        super().__init__()
        for bt in self.models:
            self.add(bt, "dyn")


class TemplateEditor(QtWidgets.QWidget):
    """
    TemplateEditor
    """

    parametersUpdated = Signal(dict)  # Emited when changing a parameters
    templateApplied = Signal(object)  # Emited when appplying a template to a model

    def __init__(self,
                 var_factory: VarFactory,
                 templates_list,
                 templates_catalogue,
                 api_object,
                 parent=None):
        super().__init__(parent)

        self.var_factory = var_factory
        self.templates_catalogue = templates_catalogue
        self.block = Block()
        self.api_object = api_object
        self.selected_block = None
        self._vars_order = []

        # ---Main layout ---
        main_layout = QtWidgets.QVBoxLayout(self)

        # --- Templates selector ---
        selector_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(selector_layout)

        self.template_label = QtWidgets.QLabel("Select an existing template:")
        selector_layout.addWidget(self.template_label)

        self.template_combo = QtWidgets.QComboBox()
        self.template_combo.addItems(templates_list if templates_list else ["<No templates available>"])
        selector_layout.addWidget(self.template_combo)

        self.btn_select_template = QtWidgets.QPushButton("Select template")
        selector_layout.addWidget(self.btn_select_template)
        self.btn_select_template.clicked.connect(self.on_select_template)

        # --- Parameters table ---
        self.template_name_label = QtWidgets.QLabel("Selected template: <None>")
        main_layout.addWidget(self.template_name_label)

        self.params_table = QtWidgets.QTableWidget()
        self.params_table.setColumnCount(2)
        self.params_table.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.params_table.setEditTriggers(QtWidgets.QTableWidget.EditTrigger.AllEditTriggers)
        main_layout.addWidget(self.params_table)

        # edit cells connection
        self.params_table.cellChanged.connect(self.on_cell_changed)

    def on_select_template(self):
        """uploads the selected template and connects Vm and Va variables with bus variables"""
        template_name = self.template_combo.currentText()
        if template_name not in self.templates_catalogue:
            QtWidgets.QMessageBox.warning(self, "Error", f"Template '{template_name}' not found.")
            return

        selected_template = self.templates_catalogue[template_name]
        # Todo: here we can use the function set_rms_model from templates common functions and it would simplify the code significantly.
        self.selected_block = Block()
        if self.api_object is not None:
            if selected_template.tpe == DeviceType.GeneratorDevice:
                if self.api_object.bus.rms_model.empty():
                    initialize_bus_rms(self.api_object.bus, self.var_factory)
                self.selected_block = selected_template.block.copy()

                Vm, Va = get_bus_rms_algebraic_vars(self.api_object.bus.rms_model)
                # substitute variables in block equations
                self.selected_block.update_model(
                    self.selected_block.external_mapping[VarPowerFlowRefferenceType.Vm], Vm)
                self.selected_block.update_model(
                    self.selected_block.external_mapping[VarPowerFlowRefferenceType.Va], Va)

            if selected_template.tpe == DeviceType.LoadDevice:
                if self.api_object.bus.rms_model.empty():
                    initialize_bus_rms(self.api_object.bus, self.var_factory)
                self.selected_block = selected_template.block.copy()

                Vm, Va = get_bus_rms_algebraic_vars(self.api_object.bus.rms_model)
                # substitute variables in block equations
                self.selected_block.update_model(
                    self.selected_block.external_mapping[VarPowerFlowRefferenceType.Vm], Vm)
                self.selected_block.update_model(
                    self.selected_block.external_mapping[VarPowerFlowRefferenceType.Va], Va)

            if selected_template.tpe == DeviceType.LineDevice:
                # bus connection variables
                if self.api_object.bus_from.rms_model.empty():
                    initialize_bus_rms(self.api_object.bus_from, self.var_factory)
                self.selected_block = selected_template.block.copy()

                Vmf, Vaf = get_bus_rms_algebraic_vars(self.api_object.bus_from.rms_model)

                if self.api_object.bus_to.rms_model.empty():
                    initialize_bus_rms(self.api_object.bus_to, self.var_factory)

                Vmt, Vat = get_bus_rms_algebraic_vars(self.api_object.bus_to.rms_model)

                self.selected_block.update_model(
                    self.selected_block.external_mapping[VarPowerFlowRefferenceType.Vmf], Vmf)
                self.selected_block.update_model(
                    self.selected_block.external_mapping[VarPowerFlowRefferenceType.Vaf], Vaf)
                self.selected_block.update_model(
                    self.selected_block.external_mapping[VarPowerFlowRefferenceType.Vmt], Vmt)
                self.selected_block.update_model(
                    self.selected_block.external_mapping[VarPowerFlowRefferenceType.Vat], Vat)

                # power flow parameters
                self.selected_block.parameters[
                    self.selected_block.api_obj_mapping[
                        ParamPowerFlowRefferenceType.g]] = self.var_factory.add_const(
                    float(self.api_object.R / (self.api_object.R ** 2 + self.api_object.X ** 2)))
                self.selected_block.parameters[
                    self.selected_block.api_obj_mapping[
                        ParamPowerFlowRefferenceType.b]] = self.var_factory.add_const(
                    float(-self.api_object.X / (self.api_object.R ** 2 + self.api_object.X ** 2)))
                self.selected_block.parameters[
                    self.selected_block.api_obj_mapping[
                        ParamPowerFlowRefferenceType.bsh]] = self.var_factory.add_const(
                    self.api_object.B)

        # Update label above the table
        self.template_name_label.setText(f"Selected template: {template_name}")
        self.template_name_label.setStyleSheet("font-size: 12pt; margin-top: 8px;")
        self.template_name_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # call editable parameters dialog
        self.selected_block.unify_blocks()

        if self.selected_block.event_dict:
            self.load_params_table()
        # call non-editable parameters dialog

        if self.selected_block.parameters:
            self.load_fix_params_table()

    def load_params_table(self):
        """
        Fills the parameters table with the template parameters
        :param selected_template:
        :return:
        """

        event_dict = self.selected_block.event_dict  # {Var: Const}

        self.params_table.blockSignals(True)
        self.params_table.setRowCount(0)
        self._vars_order = []

        for event_param, expr in event_dict.items():
            row = self.params_table.rowCount()
            self.params_table.insertRow(row)

            self._vars_order.append(event_param)

            name_item = QtWidgets.QTableWidgetItem(event_param.name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.params_table.setItem(row, 0, name_item)

            if isinstance(expr, Const):
                value_item = QtWidgets.QTableWidgetItem(str(expr.value))
                self.params_table.setItem(row, 1, value_item)
            else:
                # in tha case a event is applyed to this parameter
                value_item = QtWidgets.QTableWidgetItem(str(expr))
                value_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.params_table.setItem(row, 1, value_item)
        self.params_table.blockSignals(False)
        self.params_table.resizeColumnsToContents()

    def load_fix_params_table(self):
        """
        Fills the parameters table with non-editable (fixed) parameters
        """

        parameters = self.selected_block.parameters  # {Param: Const}

        self.params_table.blockSignals(True)

        for param, const in parameters.items():
            row = self.params_table.rowCount()
            self.params_table.insertRow(row)

            # Parameter name (non-editable)
            name_item = QtWidgets.QTableWidgetItem(param.name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.params_table.setItem(row, 0, name_item)

            # Parameter value (non-editable)
            value = "" if const.value is None else str(const.value)
            value_item = QtWidgets.QTableWidgetItem(value)
            value_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.params_table.setItem(row, 1, value_item)

        self.params_table.blockSignals(False)
        self.params_table.resizeColumnsToContents()

    def on_cell_changed(self, row, column):
        """Updates dict of parameters"""
        if self.selected_block is None or column != 1:
            return

        var = self._vars_order[row]
        value_str = self.params_table.item(row, 1).text()

        try:
            value = float(value_str)
        except ValueError:
            value = value_str

        self.selected_block.event_dict[var] = self.var_factory.add_const(value=value, name=var.name)

        self.parametersUpdated.emit(self.selected_block.event_dict)

    def apply_template(self):
        """Apply template to api_object rms_model.template"""

        if self.selected_block is None:
            QtWidgets.QMessageBox.warning(self, "Error", "No template selected.")
            return
        try:
            self.block = self.selected_block
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to apply template:\n{e}")
            return


class BlockBoxesEditor(QSplitter):
    """
    BlockEditor
    """

    def __init__(self,
                 var_factory: VarFactory,
                 api_object_name: str,
                 block: Block,
                 diagram: BlockDiagram,
                 templates_list,
                 templates_catalogue,
                 api_object=None,
                 parent=None):
        super().__init__(parent)

        self.var_factory = var_factory
        self.api_object = api_object
        self.api_object_name = api_object_name
        self.main_block = block
        self.diagram = diagram
        self.templates_list = templates_list
        self.templates_catalogue = templates_catalogue

        self.block_counters: dict[BlockType, int] = {}

        self.block_system: Block | None = None

        # --------------------------------------------------------------------------------------------------------------
        # Widget creation
        # --------------------------------------------------------------------------------------------------------------
        self.horizontal_layout = QHBoxLayout(self)

        # === Leften section (inspect button + library) ===
        left_widget = QWidget(self)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(8)

        # Inspect model button"
        self.inspect_button = QPushButton("Inspect model")
        self.inspect_button.clicked.connect(self.open_inspect_dialog)
        left_layout.addWidget(self.inspect_button)

        # Math Library
        self.math_library_view = QListView(self)
        self.math_library_view.setViewMode(QListView.ViewMode.ListMode)
        self.math_library_view.setDragEnabled(True)
        self.math_library_view.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)

        self.math_library_model = MathLibraryModel()
        self.math_library_view.setModel(self.math_library_model)

        change_font_size(self.math_library_view, 9)

        # Device Library
        self.dev_library_view = QListView(self)
        self.dev_library_view.setViewMode(QListView.ViewMode.ListMode)
        self.dev_library_view.setDragEnabled(True)
        self.dev_library_view.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)

        self.dev_library_model = DevLibraryModel()
        self.dev_library_view.setModel(self.dev_library_model)

        left_layout.addWidget(self.math_library_view)
        left_layout.addWidget(self.dev_library_view)

        # === right part (diagram) ===
        self.scene = DiagramScene(self)
        self.view = GraphicsView(self.scene)

        self.view.dragEnterEvent = self.graphicsDragEnterEvent
        self.view.dragMoveEvent = self.graphicsDragMoveEvent
        self.view.dropEvent = self.graphicsDropEvent

        # === add panels to splitter ===
        self.addWidget(left_widget)
        self.addWidget(self.view)

        self.setStretchFactor(0, 1)
        self.setStretchFactor(1, 1000)

        self.resize(800, 600)

    def add_connection_vars(self):
        """

        :return:
        """
        bus_con_item = None
        tpe = BlockType.BUS_CONNECTION

        if self.api_object.device_type == DeviceType.LineDevice:

            # add con bus from
            x0, y0 = 0, 0
            name = "Conn From"
            bus_from_con_item = BlockItem(var_factory=self.var_factory, name=name)

            if self.api_object.bus_from.rms_model.empty():
                initialize_bus_rms(self.api_object.bus_from, self.var_factory)

            Vmf, Vaf = get_bus_rms_algebraic_vars(self.api_object.bus_from.rms_model)

            bus_from_con_blk = Block(
                algebraic_vars=[Vmf, Vaf],
                out_vars=[Vmf, Vaf],
                name=name
            )

            self.main_block.add(bus_from_con_blk)

            bus_from_con_item.set_subsystem(bus_from_con_blk)
            bus_from_con_item.build_item()

            if bus_from_con_item.subsys is not None:
                bus_from_con_item.setPos(x0, y0)
                self.scene.addItem(bus_from_con_item)

                # save nodes in diagram
                self.diagram.add_node(
                    name=name,
                    x=x0,
                    y=y0,
                    tpe=tpe.name,
                    device_uid=bus_from_con_item.subsys.uid,
                )
            self.main_block.external_mapping.update(
                {VarPowerFlowRefferenceType.Vmf: Vmf})
            self.main_block.external_mapping.update(
                {VarPowerFlowRefferenceType.Vaf: Vaf})

            # add con bus to
            name = "Conn To"
            x0, y0 = 0, 100

            bus_to_con_item = BlockItem(var_factory=self.var_factory, name=name)

            if self.api_object.bus_to.rms_model.empty():
                initialize_bus_rms(self.api_object.bus_to, self.var_factory)

            Vmt, Vat = get_bus_rms_algebraic_vars(self.api_object.bus_to.rms_model)

            bus_to_con_blk = Block(
                algebraic_vars=[Vmt, Vat],
                out_vars=[Vmt, Vat],
                name=name
            )

            self.main_block.add(bus_to_con_blk)

            bus_to_con_item.set_subsystem(bus_to_con_blk)
            bus_to_con_item.build_item()

            # Add to scene
            if bus_to_con_item.subsys is not None:
                bus_to_con_item.setPos(QPointF(x0, y0))
                self.scene.addItem(bus_to_con_item)

                # save nodes in diagram
                self.diagram.add_node(
                    name=name,
                    x=x0,
                    y=y0,
                    tpe=tpe.name,
                    device_uid=bus_to_con_item.subsys.uid,
                )

            self.main_block.external_mapping.update(
                {VarPowerFlowRefferenceType.Vmt: Vmt})
            self.main_block.external_mapping.update(
                {VarPowerFlowRefferenceType.Vat: Vat})

        else:
            x0, y0 = 0, 0
            name = "Conn Bus"

            bus_con_item = BlockItem(var_factory=self.var_factory, name=name)
            if self.api_object.bus.rms_model.empty():
                initialize_bus_rms(self.api_object.bus, self.var_factory)

            Vm, Va = get_bus_rms_algebraic_vars(self.api_object.bus.rms_model)

            bus_con_blk = Block(
                out_vars=[Vm, Va],
                name=name
            )

            self.main_block.add(bus_con_blk)

            bus_con_item.set_subsystem(bus_con_blk)
            bus_con_item.build_item()

            if bus_con_item.subsys is not None:
                bus_con_item.setPos(x0, y0)
                self.scene.addItem(bus_con_item)

                # save nodes in diagram
                self.diagram.add_node(
                    name=name,
                    x=x0,
                    y=y0,
                    tpe=tpe.name,
                    device_uid=bus_con_item.subsys.uid,
                )

            self.main_block.external_mapping.update(
                {VarPowerFlowRefferenceType.Vm: Vm})
            self.main_block.external_mapping.update(
                {VarPowerFlowRefferenceType.Va: Va})

    def add_external_mapping_block(self):
        """

        :return:
        """
        bus_con_item = None
        tpe = BlockType.EXTERNAL_MAPPING

        if self.api_object.device_type == DeviceType.LineDevice:

            # add mapping bus from
            x0, y0 = 200, 200
            name = "mapping From"
            bus_from_mapping_item = BlockItem(var_factory=self.var_factory, name=name)

            Pf = self.var_factory.add_var('Pf_placeholder')
            Qf = self.var_factory.add_var('Qf_placeholder')

            bus_from_mapping_blk = Block(
                in_vars=[Pf, Qf],
                name=name
            )

            self.main_block.add(bus_from_mapping_blk)

            bus_from_mapping_item.set_subsystem(bus_from_mapping_blk)
            bus_from_mapping_item.build_item()

            if bus_from_mapping_item.subsys is not None:
                self.scene.addItem(bus_from_mapping_item)
                bus_from_mapping_item.setPos(x0, y0)
                # save nodes in diagram
                self.diagram.add_node(
                    name=name,
                    x=x0,
                    y=y0,
                    tpe=tpe.name,
                    device_uid=bus_from_mapping_item.subsys.uid,
                )
            self.main_block.external_mapping.update({VarPowerFlowRefferenceType.Pf: bus_from_mapping_blk.in_vars[0]})
            self.main_block.external_mapping.update({VarPowerFlowRefferenceType.Qf: bus_from_mapping_blk.in_vars[1]})

            # add con bus to
            name = "mapping To"
            x0, y0 = 0, 200

            bus_to_mapping_item = BlockItem(var_factory=self.var_factory, name=name)

            bus_to_mapping_blk = Block(
                in_vars=[
                    self.var_factory.add_var('Pt_placeholder'),  # Pt
                    self.var_factory.add_var('Qt_placeholder')  # Qt
                ],
                name=name
            )
            self.main_block.add(bus_to_mapping_blk)

            bus_to_mapping_item.set_subsystem(bus_to_mapping_blk)
            bus_to_mapping_item.build_item()

            # Add to scene
            bus_to_mapping_item.setPos(QPointF(x0, y0))
            if bus_to_mapping_item.subsys is not None:
                self.scene.addItem(bus_to_mapping_item)
                bus_to_mapping_item.setPos(QPointF(x0, y0))
                # save nodes in diagram
                self.diagram.add_node(
                    name=name,
                    x=x0,
                    y=y0,
                    tpe=tpe.name,
                    device_uid=bus_to_mapping_item.subsys.uid,
                )
            self.main_block.external_mapping.update({VarPowerFlowRefferenceType.Pt: bus_to_mapping_blk.in_vars[0]})
            self.main_block.external_mapping.update({VarPowerFlowRefferenceType.Qt: bus_to_mapping_blk.in_vars[1]})

        else:
            x0, y0 = 0, 0
            name = "mapping Bus"

            bus_mapping_item = BlockItem(var_factory=self.var_factory, name=name)
            P = self.var_factory.add_var('P_placeholder')
            Q = self.var_factory.add_var('Q_placeholder')

            bus_mapping_blk = Block(
                in_vars=[P, Q],
                name=name
            )

            self.main_block.add(bus_mapping_blk)

            bus_mapping_item.set_subsystem(bus_mapping_blk)
            bus_mapping_item.build_item()

            if bus_mapping_item.subsys is not None:
                self.scene.addItem(bus_mapping_item)
                bus_mapping_item.setPos(x0, y0)
                # save nodes in diagram
                self.diagram.add_node(
                    name=name,
                    x=x0,
                    y=y0,
                    tpe=tpe.name,
                    device_uid=bus_mapping_item.subsys.uid,
                )
            self.main_block.external_mapping.update({VarPowerFlowRefferenceType.P: bus_mapping_blk.in_vars[0]})
            self.main_block.external_mapping.update({VarPowerFlowRefferenceType.Q: bus_mapping_blk.in_vars[1]})

    def add_api_obj_mapping(self):
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
        if self.api_object.device_type == DeviceType.LineDevice:
            g = self.var_factory.add_var("g")
            b = self.var_factory.add_var("b")
            bsh = self.var_factory.add_var("bsh")

            self.main_block.parameters[g] = self.var_factory.add_const(0.029585)
            self.main_block.parameters[b] = self.var_factory.add_const(0.0710059)
            self.main_block.parameters[bsh] = self.var_factory.add_const(0.03)

            self.main_block.api_obj_mapping = {
                ParamPowerFlowRefferenceType.g: g,
                ParamPowerFlowRefferenceType.b: b,
                ParamPowerFlowRefferenceType.bsh: bsh,
            }

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

    def remove_item(self, item: BlockItem | ModelHostItem | ConnectionItem):
        """
        removes the item from the scene and all its connections.
        restores variables from items connected to the device.
        removes block corresponding to the item from mainblock
        :param item:
        :return:
        """
        # remove connection from scene
        if isinstance(item, ConnectionItem):

            del self.diagram.con_data[item.uid]

            source_port = item.source_port
            target_port = item.target_port
            source_port.connections.remove(item)
            target_port.connections = None
            self.scene.removeItem(item)

            dst_var = source_port.subsystem.subsys.out_vars[source_port.index]

            for i, eq in enumerate(target_port.subsystem.subsys.algebraic_eqs):
                new_equ = eq.subs({dst_var: target_port.subsystem.subsys.in_vars[target_port.index]})
                target_port.subsystem.subsys.algebraic_eqs[i] = new_equ
            for i, eq in enumerate(target_port.subsystem.subsys.state_eqs):
                new_equ = eq.subs({dst_var: target_port.subsystem.subsys.in_vars[target_port.index]})
                target_port.subsystem.subsys.state_eqs[i] = new_equ

        # remove item from scene
        if isinstance(item, (BlockItem, ModelHostItem)):
            for port in item.inputs + item.outputs:

                if port.connections:
                    for conn in port.connections:
                        del self.diagram.con_data[conn.uid]
                        self.scene.removeItem(conn)

                        source_port = conn.source_port
                        target_port = conn.target_port

                        source_port.connections.remove(conn)
                        target_port.connections = None

                        dst_var = source_port.subsystem.subsys.out_vars[source_port.index]

                        for i, eq in enumerate(target_port.subsystem.subsys.algebraic_eqs):
                            new_equ = eq.subs({dst_var: target_port.subsystem.subsys.in_vars[target_port.index]})
                            target_port.subsystem.subsys.algebraic_eqs[i] = new_equ
                        for i, eq in enumerate(target_port.subsystem.subsys.state_eqs):
                            new_equ = eq.subs({dst_var: target_port.subsystem.subsys.in_vars[target_port.index]})
                            target_port.subsystem.subsys.state_eqs[i] = new_equ

            self.scene.removeItem(item)

            # remove block from main_block
            for sub_block in self.main_block.children:
                if sub_block.uid == item.subsys.uid:
                    self.main_block.children.remove(sub_block)
            # remove data from diagram
            del self.diagram.node_data[item.subsys.uid]

    def graphicsDragEnterEvent(self, event: QDragEnterEvent) -> None:
        """
        Enter element
        @param event:
        @return:
        """
        md = event.mimeData()

        if (
                md.hasFormat("component/dev") or
                md.hasFormat("component/math")
        ):
            event.acceptProposedAction()
        else:
            event.ignore()

    def graphicsDragMoveEvent(self, event: QDragMoveEvent) -> None:
        """
        Move element
        @param event:
        @return:
        """
        md = event.mimeData()

        if (
                md.hasFormat("component/dev") or
                md.hasFormat("component/math")
        ):
            event.acceptProposedAction()
        else:
            event.ignore()

    def graphicsDropEvent(self, event: QDropEvent) -> None:

        """
        Create an element
        @param event:
        @return:
        """
        md = event.mimeData()

        point0 = self.view.mapToScene(
            int(event.position().x()),
            int(event.position().y())
        )
        x0, y0 = point0.x(), point0.y()

        if md.hasFormat("component/dev"):
            obj_type = md.data("component/dev")
            tpe = self.dev_library_model.get_type(obj_type)

        elif md.hasFormat("component/math"):
            obj_type = md.data("component/math")
            tpe = self.math_library_model.get_type(obj_type)

        else:
            event.ignore()
            return

        if tpe is None:
            event.ignore()
            return

        if tpe == BlockType.GENERIC:
            dialog = GenericBlockDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                name, state_ins, state_outs, algeb_ins, algeb_outs = dialog.get_values()

                # model_host: DynamicModelHost = DynamicModelHost()

                model = create_generic_block(self.var_factory, state_ins, state_outs, algeb_ins, algeb_outs)
                self.main_block.add(model)
                item = ModelHostItem(
                    var_factory=self.var_factory,
                    block_sys=model,
                    api_object_name=self.api_object_name,
                    templates_list=self.templates_list,
                    templates_catalogue=self.templates_catalogue,
                    api_object=self.api_object
                )

                item.setPos(QPointF(x0, y0))
                self.scene.addItem(item)
                # save nodes in diagram
                self.diagram.add_node(
                    name=name,
                    x=x0,
                    y=y0,
                    device_uid=model.uid,
                    api_object_name=self.api_object_name,
                    tpe=tpe.name,
                    state_ins=state_ins,
                    state_outs=state_outs,
                    algeb_ins=algeb_ins,
                    algeb_outs=algeb_outs,
                    subdiagram=model.diagram
                )

        else:

            count = self.block_counters.get(tpe, 0) + 1
            self.block_counters[tpe] = count

            name = f"{tpe.name}_{count}"
            item = BlockItem(var_factory=self.var_factory, name=name)

            block = create_block_of_type(self.var_factory, block_type=tpe, item_name=name, api_object=self.api_object, )
            item.set_subsystem(block)
            item.build_item()

            if item.subsys is not None:
                self.main_block.add(item.subsys)
                self.scene.addItem(item)
                item.setPos(QPointF(x0, y0))
                # save nodes in diagram
                self.diagram.add_node(
                    name=name,
                    x=x0,
                    y=y0,
                    tpe=tpe.name,
                    device_uid=item.subsys.uid,
                )

    def rebuild_scene_from_diagram(self) -> None:
        """
        Rebuilds the graphical scene from saved diagram data
        :return:
        """
        self.scene.clear()
        # self.block_counters = self.diagram.block_counters

        uid_to_blockitem = {}

        # # set number of nodes of the editor
        # self.nodes_index = self.diagram.index

        # Recreate nodes
        for uid, node in self.diagram.node_data.items():
            block_type = BlockType[node.tpe]
            if block_type == BlockType.GENERIC:

                block = Block()
                for model in self.main_block.get_all_blocks():
                    if model.uid == node.device_uid:
                        block = model

                block.uid = uid
                block.diagram = node.sub_diagram
                item = ModelHostItem(
                    var_factory=self.var_factory,
                    block_sys=block,
                    api_object_name=node.api_object_name,
                    api_object=self.api_object,
                    templates_list=self.templates_list,
                    templates_catalogue=self.templates_catalogue
                )

                item.setPos(QPointF(node.x, node.y))
                self.scene.addItem(item)
                brush = item.brush()
                brush.setColor(QColor(node.color))
                item.setBrush(brush)

                uid_to_blockitem[uid] = item

            elif block_type == BlockType.BUS_CONNECTION:
                bus_con_item = BlockItem(var_factory=self.var_factory, name=node.name)
                bus_con_blk = Block()
                for model in self.main_block.get_all_blocks():
                    if model.uid == node.device_uid:
                        bus_con_blk = model

                bus_con_item.set_subsystem(bus_con_blk)
                bus_con_item.build_item()

                if bus_con_item.subsys is not None:
                    self.scene.addItem(bus_con_item)
                    bus_con_item.setPos(QPointF(node.x, node.y))
                    bus_con_item.setBrush(QColor(node.color))

                uid_to_blockitem[uid] = bus_con_item

            elif block_type == BlockType.EXTERNAL_MAPPING:
                bus_mapping_item = BlockItem(var_factory=self.var_factory, name=node.name)
                bus_mapping_blk = Block()
                for model in self.main_block.get_all_blocks():
                    if model.uid == node.device_uid:
                        bus_mapping_blk = model

                bus_mapping_item.set_subsystem(bus_mapping_blk)
                bus_mapping_item.build_item()

                if bus_mapping_item.subsys is not None:
                    self.scene.addItem(bus_mapping_item)
                    bus_mapping_item.setPos(QPointF(node.x, node.y))
                    bus_mapping_item.setBrush(QColor(node.color))

                uid_to_blockitem[uid] = bus_mapping_item

            else:

                block_item = BlockItem(var_factory=self.var_factory, name=node.name)
                block = Block()
                for model in self.main_block.get_all_blocks():
                    if model.uid == node.device_uid:
                        block = model

                block_item.set_subsystem(block)
                block_item.build_item()
                if block_item.subsys is not None:
                    self.scene.addItem(block_item)
                    block_item.setPos(QPointF(node.x, node.y))
                    brush = block_item.brush()
                    brush.setColor(QColor(node.color))
                    block_item.setBrush(brush)
                uid_to_blockitem[uid] = block_item

        # Recreate connections
        for uid, con in self.diagram.con_data.items():
            src_item = uid_to_blockitem.get(con.from_uid)
            dst_item = uid_to_blockitem.get(con.to_uid)
            if not src_item or not dst_item:
                continue

            try:
                src_port = src_item.outputs[con.port_number_from]
                dst_port = dst_item.inputs[con.port_number_to]
            except IndexError:
                continue

            connection = ConnectionItem(src_port, dst_port)
            connection.uid = uid
            pen = connection.pen()
            pen.setColor(QColor(con.color))
            connection.setPen(pen)
            self.scene.addItem(connection)

        self.block_system = self.scene.get_main_block()


class EditEquations(QWidget):
    """
    EditEquations (still under construction)
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
        self.btn_add_var = QPushButton("+")
        var_header_layout.addWidget(var_label)
        var_header_layout.addWidget(self.btn_add_var)
        left_panel.addLayout(var_header_layout)

        self.list_vars = QListWidget()
        left_panel.addWidget(self.list_vars)

        # Parameters
        param_header_layout = QHBoxLayout()
        param_label = QLabel("Parameters")
        self.btn_add_param = QPushButton("+")
        param_header_layout.addWidget(param_label)
        param_header_layout.addWidget(self.btn_add_param)
        left_panel.addLayout(param_header_layout)

        self.list_params = QListWidget()
        left_panel.addWidget(self.list_params)

        # ----------------- RIGHT PANEL -----------------
        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel)

        eqn_header_layout = QHBoxLayout()
        eqn_label = QLabel("Equations")
        self.btn_add_eqn = QPushButton("+")
        eqn_header_layout.addWidget(eqn_label)
        eqn_header_layout.addWidget(self.btn_add_eqn)
        right_panel.addLayout(eqn_header_layout)

        self.list_eqns = QListWidget()
        right_panel.addWidget(self.list_eqns)

        # # ----------------- Connections -----------------
        # self.btn_add_var.clicked.connect(self.add_variable)
        # self.btn_add_param.clicked.connect(self.add_parameter)
        # self.btn_add_eqn.clicked.connect(self.add_equation)

        self.refresh_lists(self.block)

    def refresh_lists(self, model=None, clear=True):
        """Load current model variables, parameters, equations into lists."""
        if model is None:
            model = self.block

        # Only clear at the top-level call
        if clear:
            self.list_vars.clear()
            self.list_params.clear()
            self.list_eqns.clear()

        # Add variables
        for var in model.state_vars + model.algebraic_vars:
            item = QListWidgetItem(f"{var.name} ({'state' if var in model.state_vars else 'algebraic'})")
            self.list_vars.addItem(item)

        # for var in getattr(model, "active_in_vars", []):
        #     item = QListWidgetItem(f"{var.name} (input)")
        #     self.list_vars.addItem(item)

        # Parameters (uncomment when available)
        # for param in model.parameters:
        #     item = QListWidgetItem(param.name)
        #     self.list_params.addItem(item)

        # Equations
        for eq in model.state_eqs + model.algebraic_eqs:
            item = QListWidgetItem(f"{symbolic_to_string(eq)} ({'state' if eq in model.state_eqs else 'algebraic'})")
            self.list_eqns.addItem(item)

        # Recurse into children, but without clearing
        for submodel in getattr(model, "children", []):
            self.refresh_lists(submodel, clear=False)


# class RmsModelEditorGUI(QtWidgets.QMainWindow):
#     """
#     RmsModelEditorGUI
#     """
#
#     def __init__(self,
#                  var_factory: VarFactory,
#                  block: Block,
#                  templates_list: List[RmsModelTemplate],
#                  templates_catalogue,
#                  api_object_name,
#                  api_object: ALL_DEV_TYPES | None = None,
#                  main_editor=False,
#                  parent=None):
#         """
#
#         :param block:
#         :param templates_list:
#         :param templates_catalogue:
#         :param api_object_name:
#         :param api_object:
#         :param main_editor:
#         :param parent:
#         """
#         super().__init__(parent)
#
#         self.ui = Ui_MainWindow()
#         self.ui.setupUi(self)
#
#         self.setWindowTitle("RMS Model Editor")
#         self.resize(1000, 700)
#
#         self.var_factory = var_factory
#         self.api_object_name = api_object_name
#         self.block = block
#         self.templates_list = templates_list
#         self.templates_catalogue = templates_catalogue
#         self.api_object = api_object
#         self.main_editor = main_editor
#
#         self.current_editor = None
#
#         self.templates_name = "Templates"
#         self.block_editor_name = "Block Editor"
#         self.equations_editor_name = "Equations editor"
#
#         # set modes
#         self.ui.model_selector_comboBox.setModel(gf.get_list_model([
#             self.templates_name,
#             self.block_editor_name,
#             self.equations_editor_name
#         ]))
#
#         # --- templates editor layout ---
#         self.template_editor = TemplateEditor(self.var_factory,
#                                               self.templates_list, self.templates_catalogue,
#                                               self.api_object
#                                               )
#         # self.ui.templatesLayout.addWidget(self.template_editor)
#
#         # --- block boxes editor layout ---
#         self.block_boxes_editor = BlockBoxesEditor(
#             self.var_factory,
#             api_object_name=self.api_object_name,
#             block=self.block,  # .copy(),
#             diagram=self.block.diagram,  # .copy(),
#             templates_list=self.templates_list,
#             templates_catalogue=self.templates_catalogue,
#             api_object=self.api_object
#         )
#
#         # _____ Add user init guess dialog ______
#
#         # === Add default bus connection block if diagram is empty ===
#         if not self.block_boxes_editor.diagram.node_data and self.main_editor:
#             self.block_boxes_editor.add_connection_vars()
#             self.block_boxes_editor.add_external_mapping_block()
#             self.block_boxes_editor.add_api_obj_mapping()
#         # === Add pf parameters ===
#         self.block_boxes_editor.rebuild_scene_from_diagram()
#         self.block_boxes_editor.view.setSceneRect(0, 0, 2000, 2000)  # tamaño arbitrario de escena
#         self.block_boxes_editor.view.centerOn(0, 0)
#         self.block_boxes_editor.view.ensureVisible(0, 0, 100, 100)
#         self.block_boxes_editor.view.horizontalScrollBar().setValue(0)
#         self.block_boxes_editor.view.verticalScrollBar().setValue(0)
#         # self.ui.editorLayout.addWidget(self.blockboxes_editor)
#
#         # --- equations editor layout ---
#         self.equations_editor = EditEquations(self.block)
#         # self.ui.equations_editor_layout.addWidget(self.equations_editor)
#
#         # --- status bar setup ---
#         self.status_label = QtWidgets.QLabel("🔵 No model applied")
#         if self.block.diagram.status is not None:
#             self.status_label.setText(f"🟢 Current model: {self.block.diagram.status}")
#         self.statusBar().addPermanentWidget(self.status_label)
#         self.statusBar().showMessage("Ready")
#
#         # --- connections ---
#         self.ui.doItButton.clicked.connect(self.do_it)
#         self.ui.InitGuessButton.clicked.connect(self.add_init_guess)
#
#         # current editor view change
#         self.ui.model_selector_comboBox.currentIndexChanged.connect(self.editor_change)
#
#         # select the template view
#         self.ui.model_selector_comboBox.setCurrentIndex(0)
#         self.editor_change()
#
#         # innit guess button
#
#         if not self.main_editor:
#             self.ui.InitGuessButton.setVisible(False)
#
#     def editor_change(self):
#         """
#         On change the editor mode
#         """
#         # delete all widgets from the layout
#         for i in reversed(range(self.ui.mainLayout.count())):
#             # get the widget
#             widget_to_remove = self.ui.mainLayout.itemAt(i).widget()
#
#             # delete it from the layout list
#             self.ui.mainLayout.removeWidget(widget_to_remove)
#
#             # delete it from the gui
#             widget_to_remove.setParent(None)
#
#         if self.ui.model_selector_comboBox.currentText() == self.templates_name:
#             self.ui.mainLayout.addWidget(self.template_editor)
#             self.current_editor = self.template_editor
#
#         elif self.ui.model_selector_comboBox.currentText() == self.block_editor_name:
#             self.ui.mainLayout.addWidget(self.block_boxes_editor)
#             self.current_editor = self.block_boxes_editor
#
#         elif self.ui.model_selector_comboBox.currentText() == self.equations_editor_name:
#             # TODO: add model host logic
#             self.ui.mainLayout.addWidget(self.equations_editor)
#             self.current_editor = self.equations_editor
#
#         else:
#             raise ValueError("Unsupported RMS editor!")
#
#         self.ui.currently_editing_object_label.setText(self.api_object_name)
#
#     def do_it(self) -> None:
#         """
#         Logic when applying the window
#         :return:
#         """
#         if self.ui.model_selector_comboBox.currentText() == self.templates_name:
#             if self.template_editor.selected_block is not None:
#                 self.template_editor.apply_template()
#                 self.block.template = self.template_editor.block
#             else:
#                 error_msg("Empty template :(", "Model apply")
#                 return
#
#         elif self.ui.model_selector_comboBox.currentText() == self.block_editor_name:
#             if self.block_boxes_editor.main_block is not None:
#                 self.block.diagram = self.block_boxes_editor.diagram
#             else:
#                 error_msg("Empty model :(", "Model apply")
#                 return
#
#         elif self.ui.model_selector_comboBox.currentText() == self.equations_editor_name:
#             # TODO: add model host logic
#             pass
#
#         else:
#             raise ValueError("Unsupported RMS editor!")
#
#         self.close()
#
#     def add_init_guess(self):
#         """
#
#         :return:
#         """
#         if isinstance(self.current_editor, TemplateEditor):
#             if self.current_editor.selected_template is None:
#                 QtWidgets.QMessageBox.warning(self, "Error", "No template selected.")
#                 return
#             try:
#                 template = self.current_editor.selected_template
#                 if template.block.init_values:
#                     values_dict = template.block.init_values.copy()
#                 else:
#                     model = template.block
#                     values_dict: Dict[Var, Const] = dict()
#                     variables = model.get_all_vars()
#                     for var in variables:
#                         values_dict.update({var: self.var_factory.add_const(0)})
#
#                 init_guess_editor = InitialValuesDialog(var_factory=self.var_factory, var_const_dict=values_dict)
#                 result = init_guess_editor.exec()
#                 if result == QDialog.DialogCode.Accepted:
#                     init_values_dict = init_guess_editor.get_values_dict()
#                     template.block.init_values = init_values_dict
#
#             except Exception as e:
#                 QtWidgets.QMessageBox.warning(self, "Error", f"Failed get variables from template:\n{e}")
#                 return
#         elif isinstance(self.current_editor, BlockBoxesEditor):
#             model = self.current_editor.main_block
#
#             if model.init_values:
#                 values_dict = model.init_values.copy()
#             else:
#                 values_dict: Dict[Var, Const] = dict()
#                 variables = model.get_all_vars()
#                 for var in variables:
#                     values_dict.update({var: self.var_factory.add_const(0)})
#
#             # TODO: add logic to get all variables from the model and pass them to InitialValuesDialog
#
#             init_guess_editor = InitialValuesDialog(var_factory=self.var_factory, var_const_dict=values_dict)
#             result = init_guess_editor.exec()
#             if result == QDialog.DialogCode.Accepted:
#                 init_values_dict = init_guess_editor.get_values_dict()
#                 model.init_values = init_values_dict
#
#         elif isinstance(self.current_editor, EditEquations):
#             # TODO: add logic for this case
#             pass

    def rebuild_scene_from_diagram(self) -> None:
        """
        Rebuilds the graphical scene from saved diagram data
        :return:
        """
        self.scene.clear()
        # self.block_counters = self.diagram.block_counters

        uid_to_blockitem = {}

        # # set number of nodes of the editor
        # self.nodes_index = self.diagram.index

        # Recreate nodes
        for uid, node in self.diagram.node_data.items():
            block_type = BlockType[node.tpe]
            if block_type == BlockType.GENERIC:

                model_host = DynamicModelHost()

                model_host.model = Block()
                for model in self.main_block.get_all_blocks():
                    if model.uid == node.device_uid:
                        model_host.model = model

                model_host.model.uid = uid
                model_host.diagram = node.sub_diagram
                item = ModelHostItem(
                    var_factory=self.var_factory,
                    model_host_sys=model_host,
                    api_object_name=node.api_object_name,
                    api_object=self.api_object,
                    templates_list=self.templates_list,
                    templates_catalogue=self.templates_catalogue
                )

                item.setPos(QPointF(node.x, node.y))
                self.scene.addItem(item)
                brush = item.brush()
                brush.setColor(QColor(node.color))
                item.setBrush(brush)

                uid_to_blockitem[uid] = item

            elif block_type == BlockType.BUS_CONNECTION:
                bus_con_item = BlockItem(var_factory=self.var_factory, name=node.name)
                bus_con_blk = Block()
                for model in self.main_block.get_all_blocks():
                    if model.uid == node.device_uid:
                        bus_con_blk = model

                bus_con_item.set_subsystem(bus_con_blk)
                bus_con_item.build_item()

                if bus_con_item.subsys is not None:
                    self.scene.addItem(bus_con_item)
                    bus_con_item.setPos(QPointF(node.x, node.y))
                    bus_con_item.setBrush(QColor(node.color))

                uid_to_blockitem[uid] = bus_con_item

            elif block_type == BlockType.EXTERNAL_MAPPING:
                bus_mapping_item = BlockItem(var_factory=self.var_factory, name=node.name)
                bus_mapping_blk = Block()
                for model in self.main_block.get_all_blocks():
                    if model.uid == node.device_uid:
                        bus_mapping_blk = model

                bus_mapping_item.set_subsystem(bus_mapping_blk)
                bus_mapping_item.build_item()

                if bus_mapping_item.subsys is not None:
                    self.scene.addItem(bus_mapping_item)
                    bus_mapping_item.setPos(QPointF(node.x, node.y))
                    bus_mapping_item.setBrush(QColor(node.color))

                uid_to_blockitem[uid] = bus_mapping_item

            else:

                block_item = BlockItem(var_factory=self.var_factory, name=node.name)
                block = Block()
                for model in self.main_block.get_all_blocks():
                    if model.uid == node.device_uid:
                        block = model

                block_item.set_subsystem(block)
                block_item.build_item()
                if block_item.subsys is not None:
                    self.scene.addItem(block_item)
                    block_item.setPos(QPointF(node.x, node.y))
                    brush = block_item.brush()
                    brush.setColor(QColor(node.color))
                    block_item.setBrush(brush)
                uid_to_blockitem[uid] = block_item

        # Recreate connections
        for uid, con in self.diagram.con_data.items():
            src_item = uid_to_blockitem.get(con.from_uid)
            dst_item = uid_to_blockitem.get(con.to_uid)
            if not src_item or not dst_item:
                continue

            try:
                src_port = src_item.outputs[con.port_number_from]
                dst_port = dst_item.inputs[con.port_number_to]
            except IndexError:
                continue

            connection = ConnectionItem(src_port, dst_port)
            connection.uid = uid
            pen = connection.pen()
            pen.setColor(QColor(con.color))
            connection.setPen(pen)
            self.scene.addItem(connection)

        self.block_system = self.scene.get_main_block()

