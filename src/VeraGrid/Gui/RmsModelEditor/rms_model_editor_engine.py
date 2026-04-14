# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import pdb
import uuid
import sys
import copy
from typing import cast

from enum import Enum, auto
from typing import List, Dict, Optional, Union, Sequence, Any
from dataclasses import dataclass
import VeraGrid.Gui.gui_functions as gf
from PySide6 import QtWidgets
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QGraphicsScene, QGraphicsView, QGraphicsItem,
                               QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem, QMenu, QGraphicsPathItem,
                               QDialog, QVBoxLayout, QComboBox, QDialogButtonBox, QSplitter, QLabel, QDoubleSpinBox,
                               QListView, QAbstractItemView, QPushButton, QListWidget, QInputDialog, QWidget,
                               QListWidgetItem, QFormLayout, QSpinBox, QLineEdit, QTableWidget, QTableWidgetItem,
                               QMessageBox, QColorDialog, QCheckBox)
from PySide6.QtGui import (QPen, QBrush, QPainterPath, QAction, QPainter, QIcon, QStandardItemModel, QStandardItem,
                           QPixmap, QDropEvent, QDragEnterEvent, QDragMoveEvent, QColor)
from PySide6.QtCore import Qt, QPointF, QByteArray, QDataStream, QIODevice, QModelIndex, QMimeData, Signal, QPoint
from VeraGridEngine.Templates.Rms.genqec_exc_gov_sat_template import (GenqecBuild,
                                                                      GovernorBuild,
                                                                      StabilizerBuild,
                                                                      ExciterBuild, )
from VeraGridEngine.Utils.Symbolic.block import (
    Block,
    constant,
    gain,
    adder,
    substract,
    product,
    divide,
    absolut,
    generator,

    line,
    generic,
    exciter_fake,
    governor_fake
)

from VeraGrid.Gui.RmsModelEditor.rms_model_editor import Ui_MainWindow
from VeraGrid.Gui.messages import error_msg
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Const, make_symbolic, symbolic_to_string, \
    VarPowerFlowRefferenceType
from VeraGridEngine.Devices.Dynamic.dynamic_model_host import BlockDiagram, DynamicModelHost
from VeraGridEngine.enumerations import DeviceType


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


def _get_var_name_from_subsys(subsys, is_input: bool, index: int) -> str:
    """
    Devuelve el nombre de la variable correspondiente al port.
    Soporta subsys.in_vars/out_vars que sean listas o diccionarios indexados por str(index).
    """
    try:
        if is_input:
            container = getattr(subsys, "in_vars", None)
        else:
            container = getattr(subsys, "out_vars", None)

        if container is None:
            return "<no var>"

        # primero intentamos como lista/sequence (index entero)
        try:
            var = container[index]
        except Exception:
            # intentamos como dict con clave string (ej. container['0'])
            try:
                var = container[str(index)]
            except Exception:
                # fallback: si es dict y tiene keys ordenadas, intentamos convertir index a posición
                if isinstance(container, dict):
                    keys = list(container.keys())
                    try:
                        var = container[keys[index]]
                    except Exception:
                        return "<no var>"
                else:
                    return "<no var>"

        # Intentamos sacar el atributo .name si existe
        if hasattr(var, "name"):
            return var.name
        # si es sympy symbol u otro, str() es la opción
        return str(var)
    except Exception:
        return "<no var>"


def change_model_params(mdl_old, mdl_new):
    """

    :param mdl_old:
    :param mdl_new:
    :return:
    """
    mdl_old.parameters = mdl_new.parameters
    mdl_old.algebraic_eqs = mdl_new.algebraic_eqs
    mdl_old.state_eqs = mdl_new.state_eqs
    for eq in mdl_old.algebraic_eqs:
        for var, wrong_var in zip(mdl_old.algebraic_vars, mdl_new.algebraic_vars):
            eq.subs({wrong_var: var})
        for var, wrong_var in zip(mdl_old.state_vars, mdl_new.state_vars):
            eq.subs({wrong_var: var})
        for var, wrong_var in zip(mdl_old.in_vars, mdl_new.in_vars):
            eq.subs({wrong_var: var})

    for eq in mdl_old.state_eqs:
        for var, wrong_var in zip(mdl_old.algebraic_vars, mdl_new.algebraic_vars):
            eq.subs({wrong_var: var})
        for var, wrong_var in zip(mdl_old.state_vars, mdl_new.state_vars):
            eq.subs({wrong_var: var})
        for var, wrong_var in zip(mdl_old.in_vars, mdl_new.in_vars):
            eq.subs({wrong_var: var})

    if mdl_old.children:
        for submodel_old, submodel_new in zip(mdl_old.children, mdl_new.children):
            change_model_params(submodel_old, submodel_new)


def update_equations(blk, old, new):
    """

    :param blk:
    :param old:
    :param new:
    :return:
    """
    for i, eq in enumerate(blk.algebraic_eqs):
        new_equ = eq.subs({old: new})
        blk.algebraic_eqs[i] = new_equ
    for i, eq in enumerate(blk.state_eqs):
        new_equ = eq.subs({old: new})
        blk.state_eqs[i] = new_equ


def update_model(model, old, new):
    """

    :param model:
    :param old:
    :param new:
    :return:
    """
    update_equations(model, old, new)
    if model.children:
        for child in model.children:
            update_model(child, old, new)


@dataclass
class BlockBridge:
    gui: "BlockItem"  # visual node
    outs: List[Var]  # exactly len(gui.outputs)
    ins: List[Var]  # exactly len(gui.inputs) – placeholders
    api_blocks: List[Block]  # usually length 1, but e.g. PI returns 4


class BlockType(Enum):
    CONST = auto()
    GAIN = auto()
    SUM = auto()
    SUBSTR = auto()
    PRODUCT = auto()
    DIVIDE = auto()
    ABS = auto()
    GENERATOR = auto()
    GENQEC = auto()
    GOV = auto()
    STAB = auto()
    EXCITER = auto()
    LINE = auto()
    GENERIC = auto()
    BUS_CONNECTION = auto()
    EXTERNAL_MAPPING = auto()
    EXCITER_FAKE = auto()
    GOVERNOR_FAKE = auto()


class BlockTypeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Block Type")
        self.layout = QVBoxLayout(self)

        self.combo = QComboBox(self)
        for bt in BlockType:
            self.combo.addItem(bt.name, bt)
        self.layout.addWidget(self.combo)

        # 👇 Extra field for constants
        self.value_label = QLabel("Constant value:", self)
        self.value_spin = QDoubleSpinBox(self)
        self.value_spin.setRange(-1e6, 1e6)
        self.value_spin.setValue(0.0)
        self.layout.addWidget(self.value_label)
        self.layout.addWidget(self.value_spin)

        # Initially hidden
        self.value_label.hide()
        self.value_spin.hide()

        self.combo.currentIndexChanged.connect(self._on_block_changed)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def _on_block_changed(self, index):
        block_type = self.combo.itemData(index)
        if block_type == BlockType.CONSTANT:
            self.value_label.show()
            self.value_spin.show()
        else:
            self.value_label.hide()
            self.value_spin.hide()

    def selected_block_type(self) -> BlockType:
        return self.combo.currentData()

    def constant_value(self) -> float:
        return self.value_spin.value()


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


class ResizeHandle(QGraphicsRectItem):
    def __init__(self, block, size=10):
        super().__init__(0, 0, size, size, block)
        self.setBrush(QBrush(Qt.GlobalColor.darkGray))
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.setZValue(2)
        self.block = block
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if not self.block._resizing_from_handle:
                return super().itemChange(change, value)

            new_pos = value  # already QPointF
            min_width, min_height = 40, 30
            new_width = max(new_pos.x(), min_width)
            new_height = max(new_pos.y(), min_height)

            self.block.resize_block(new_width, new_height)

            return QPointF(new_width, new_height)
        return super().itemChange(change, value)


class BlockItem(QGraphicsRectItem):
    def __init__(self, name: str):
        """

        :param block_sys: Block
        """
        super().__init__(0, 0, 100, 60)

        # ------------------------
        # API
        # ------------------------
        self.subsys = None
        self.name = name

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

        # --- assign tooltips with the corresponding variable names---
        for i, port in enumerate(self.inputs):
            var_name = _get_var_name_from_subsys(self.subsys, is_input=True, index=i)
            port.setToolTip(f"Input {i}: {var_name}")

        for i, port in enumerate(self.outputs):
            var_name = _get_var_name_from_subsys(self.subsys, is_input=False, index=i)
            port.setToolTip(f"Output {i}: {var_name}")

        self.resize_handle = ResizeHandle(self)

        super().setRect(0, 0, 100, 60)
        self.update_ports()
        self.update_handle_position()

        self._resizing_from_handle = False

    def mouseDoubleClickEvent(self, event):
        # --- Constant editing ---
        print(self.subsys.name)
        if self.subsys.name.lower().startswith("const") or self.subsys.name == "CONSTANT":
            dlg = QDialog()
            dlg.setWindowTitle("Edit Constant Value")
            layout = QVBoxLayout(dlg)

            spin = QDoubleSpinBox(dlg)
            spin.setRange(-1e6, 1e6)
            spin.setValue(self.subsys.value if hasattr(self.subsys, "value") else 0.0)
            layout.addWidget(QLabel("Constant value:"))
            layout.addWidget(spin)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            layout.addWidget(buttons)
            buttons.accepted.connect(dlg.accept)
            buttons.rejected.connect(dlg.reject)

            if dlg.exec() == QDialog.DialogCode.Accepted:
                new_val = spin.value()
                var_obj = next((v for v in self.subsys.event_dict.keys() if "param" in v.name), None)
                self.subsys.event_dict[var_obj] = Const(new_val)
                # _ , self.subsys = constant(new_val)
                self.name_item.setPlainText(f"Const({new_val})")
            return

        if self.subsys.name.lower().startswith("gain") or self.subsys.name == "GAIN":
            dlg = QDialog()
            dlg.setWindowTitle("Edit Gain Parameter Value")
            layout = QVBoxLayout(dlg)

            spin = QDoubleSpinBox(dlg)
            spin.setRange(-1e6, 1e6)
            spin.setValue(self.subsys.value if hasattr(self.subsys, "value") else 0.0)
            layout.addWidget(QLabel("Gain parameter value:"))
            layout.addWidget(spin)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            layout.addWidget(buttons)
            buttons.accepted.connect(dlg.accept)
            buttons.rejected.connect(dlg.reject)

            if dlg.exec() == QDialog.DialogCode.Accepted:
                new_val = spin.value()
                var_obj = next((v for v in self.subsys.event_dict.keys() if v.name == "gain_param"), None)
                self.subsys.event_dict[var_obj] = Const(new_val)
                # _ , self.subsys = constant(new_val)
                self.name_item.setPlainText(f"Gain({new_val})")
            return

        if self.subsys.name.lower().startswith("gov") or self.subsys.name.startswith == "GOV":
            dialog = ParameterEditorDialog(self.subsys.parameters, self.subsys.event_dict)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_params, new_events = dialog.get_updated_data()
                self.subsys.event_dict = new_events
                constructor = GovernorBuild()
                constructor.parameters = new_params
                blk = constructor.governor()

                change_model_params(self.subsys, blk)

            return

        super().mouseDoubleClickEvent(event)

    def resize_block(self, width, height):
        # Update geometry safely
        self.prepareGeometryChange()
        QGraphicsRectItem.setRect(self, 0, 0, width, height)
        self.update_ports()
        self.update_handle_position()

    def update_handle_position(self):
        rect = self.rect()
        self._resizing_from_handle = False
        self.resize_handle.setPos(rect.width(), rect.height())
        self._resizing_from_handle = True

    def _set_rect_internal(self, w, h):
        QGraphicsRectItem.setRect(self, 0, 0, w, h)
        self.update_ports()
        self.update_handle_position()

    def setRect(self, x, y, w, h):
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

    def open_generic_editor(self):
        dlg = QDialog()
        dlg.setWindowTitle(f"Edit Generic Block ({self.subsys.uid})")
        dlg.resize(600, 400)
        layout = QVBoxLayout(dlg)

        # Section: Algebraic Variables
        alg_section = self.create_variable_section("Algebraic Variables", self.subsys.algebraic_vars)
        layout.addLayout(alg_section)

        # Section: State Variables
        state_section = self.create_variable_section("State Variables", self.subsys.state_vars)
        layout.addLayout(state_section)

        # Section: Algebraic Equations
        alg_eq_section = self.create_equation_section("Algebraic Equations", self.subsys.algebraic_eqs)
        layout.addLayout(alg_eq_section)

        # Section: State Equations
        state_eq_section = self.create_equation_section("State Equations", self.subsys.state_eqs)
        layout.addLayout(state_eq_section)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)

        dlg.exec()

    def create_variable_section(self, title, var_list):
        layout = QVBoxLayout()

        label = QLabel(title)
        layout.addWidget(label)

        list_widget = QListWidget()
        for v in var_list:
            list_widget.addItem(v.name)
        layout.addWidget(list_widget)

        add_btn = QPushButton("+")
        layout.addWidget(add_btn)

        def add_var():
            text, ok = QInputDialog.getText(None, f"Add {title}", "Variable name:")
            if ok and text:
                var_list.append(Var(text))
                list_widget.addItem(text)

        add_btn.clicked.connect(add_var)

        return layout

    def create_equation_section(self, title, eq_list):
        layout = QVBoxLayout()

        label = QLabel(title)
        layout.addWidget(label)

        list_widget = QListWidget()
        for eq in eq_list:
            text = symbolic_to_string(eq)
            list_widget.addItem(text)
        layout.addWidget(list_widget)

        add_btn = QPushButton("+")
        layout.addWidget(add_btn)

        def add_eq():
            text, ok = QInputDialog.getText(None, f"Add {title}", "Equation:")
            if ok and text:
                sym_expr = make_symbolic(text)
                eq_list.append(sym_expr)
                list_widget.addItem(text)

        add_btn.clicked.connect(add_eq)

        return layout


class ModelHostItem(QGraphicsRectItem):
    def __init__(self, model_host_sys: DynamicModelHost, api_object_name, api_object, templates_list,
                 templates_catalogue):
        """

        :param block_sys: Block
        """
        super().__init__(0, 0, 100, 60)

        # ------------------------
        # API
        # ------------------------
        self.model_host = model_host_sys
        self.api_object_name = api_object_name
        self.templates_list = templates_list
        self.templates_catalogue = templates_catalogue
        self.api_object = api_object

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
        self.setAcceptHoverEvents(True)

        self.name_item = QGraphicsTextItem(self.model_host.model.name, self)

        self.name_item.setPos(10, 5)

        n_inputs = len(self.model_host.model.in_vars)
        n_outputs = len(self.model_host.model.out_vars)

        self.inputs = [PortItem(self, True, i, n_inputs) for i in range(n_inputs)]
        self.outputs = [PortItem(self, False, i, n_outputs) for i in range(n_outputs)]

        self.setBrush(QBrush(QColor("#C0C0C0")))

        # --- assign tooltips with the assigned variable name ---
        for i, port in enumerate(self.inputs):
            var_name = _get_var_name_from_subsys(self.model_host.model, is_input=True, index=i)
            port.setToolTip(f"Input {i}: {var_name}")

        for i, port in enumerate(self.outputs):
            var_name = _get_var_name_from_subsys(self.model_host.model, is_input=False, index=i)
            port.setToolTip(f"Output {i}: {var_name}")

        self.resize_handle = ResizeHandle(self)

        super().setRect(0, 0, 100, 60)
        self.update_ports()
        self.update_handle_position()

        self._resizing_from_handle = False

    @property
    def subsys(self):
        return self.model_host.model

    def mouseDoubleClickEvent(self, event):

        editor_window = RmsModelEditorGUI(api_object_model_host=self.model_host, templates_list=self.templates_list,
                                          templates_catalogue=self.templates_catalogue,
                                          api_object_name=self.api_object_name, api_object=self.api_object)
        editor_window.show()

        self.editor_window = editor_window

    def resize_block(self, width, height):
        # Update geometry safely
        self.prepareGeometryChange()
        QGraphicsRectItem.setRect(self, 0, 0, width, height)
        self.update_ports()
        self.update_handle_position()

    def update_handle_position(self):
        rect = self.rect()
        self._resizing_from_handle = False
        self.resize_handle.setPos(rect.width(), rect.height())
        self._resizing_from_handle = True

    def _set_rect_internal(self, w, h):
        QGraphicsRectItem.setRect(self, 0, 0, w, h)
        self.update_ports()
        self.update_handle_position()

    def setRect(self, x, y, w, h):
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

    # def contextMenuEvent(self, event):
    #     menu = QMenu()
    #
    #     delete_action = QAction("Remove Block", menu)
    #     menu.addAction(delete_action)
    #
    #
    #     edit_action = QAction("Edit Block", menu)
    #     menu.addAction(edit_action)
    #
    #     chosen = menu.exec(event.screenPos())
    #
    #     if chosen == delete_action:
    #         for port in self.inputs + self.outputs:
    #             if port.connection:
    #                 self.scene().removeItem(port.connection)
    #                 if port.connection.source_port:
    #                     port.connection.source_port.connection = None
    #                 if port.connection.target_port:
    #                     port.connection.target_port.connection = None
    #         self.scene().removeItem(self)
    #
    #     elif chosen == edit_action:
    #         self.open_generic_editor()

    def open_generic_editor(self):
        dlg = QDialog()
        dlg.setWindowTitle(f"Edit Generic Block ({self.model_host.model.uid})")
        dlg.resize(600, 400)
        layout = QVBoxLayout(dlg)

        # Section: Algebraic Variables
        alg_section = self.create_variable_section("Algebraic Variables", self.model_host.model.algebraic_vars)
        layout.addLayout(alg_section)

        # Section: State Variables
        state_section = self.create_variable_section("State Variables", self.model_host.model.state_vars)
        layout.addLayout(state_section)

        # Section: Algebraic Equations
        alg_eq_section = self.create_equation_section("Algebraic Equations", self.model_host.model.algebraic_eqs)
        layout.addLayout(alg_eq_section)

        # Section: State Equations
        state_eq_section = self.create_equation_section("State Equations", self.model_host.model.state_eqs)
        layout.addLayout(state_eq_section)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)

        dlg.exec()

    def create_variable_section(self, title, var_list):
        layout = QVBoxLayout()

        label = QLabel(title)
        layout.addWidget(label)

        list_widget = QListWidget()
        for v in var_list:
            list_widget.addItem(v.name)
        layout.addWidget(list_widget)

        add_btn = QPushButton("+")
        layout.addWidget(add_btn)

        def add_var():
            text, ok = QInputDialog.getText(None, f"Add {title}", "Variable name:")
            if ok and text:
                var_list.append(Var(text))
                list_widget.addItem(text)

        add_btn.clicked.connect(add_var)

        return layout

    def create_equation_section(self, title, eq_list):
        layout = QVBoxLayout()

        label = QLabel(title)
        layout.addWidget(label)

        list_widget = QListWidget()
        for eq in eq_list:
            text = symbolic_to_string(eq)
            list_widget.addItem(text)
        layout.addWidget(list_widget)

        add_btn = QPushButton("+")
        layout.addWidget(add_btn)

        def add_eq():
            text, ok = QInputDialog.getText(None, f"Add {title}", "Equation:")
            if ok and text:
                sym_expr = make_symbolic(text)
                eq_list.append(sym_expr)
                list_widget.addItem(text)

        add_btn.clicked.connect(add_eq)

        return layout


class GenericBlockDialog(QDialog):
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
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
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
        # self.setDragMode(QGraphicsView.DragMode.NoDrag)
        # self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        # self.setMouseTracking(True)
        # self.setInteractive(True)

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


def create_block_of_type(block_type: BlockType, api_object: Any, item_name: str = "") -> Block | None:
    """
    Create a Block appropriate for block_type.
    """
    # GAIN (single output)
    if block_type == BlockType.CONST:
        blk = constant(item_name)
        return blk

    # GAIN (single input -> single output)
    if block_type == BlockType.GAIN:
        blk = gain(item_name)
        return blk

    # SUM / ADDER (2 inputs)
    if block_type == BlockType.SUM:
        blk = adder(item_name)
        return blk

    # SUBSTRACT (2 inputs)
    if block_type == BlockType.SUBSTR:
        blk = substract(item_name)
        return blk

    # PRODUCT (2 inputs)
    if block_type == BlockType.PRODUCT:
        blk = product(item_name)
        return blk

    # DIVIDE (2 inputs)
    if block_type == BlockType.DIVIDE:
        blk = divide(item_name)
        return blk

    # ABSOLUT (single input -> single output)
    if block_type == BlockType.ABS:
        blk = absolut(item_name)
        return blk

    # GENERATOR (simple model)
    if block_type == BlockType.GENERATOR:
        blk = generator(item_name)
        return blk

    # GENQEC (generator with saturation)
    if block_type == BlockType.GENQEC:
        return GenqecBuild(item_name).block

    # GOVERNOR (governor with control)
    if block_type == BlockType.GOV:
        return GovernorBuild(item_name).block

    # STABILIZER (stabilizer)
    if block_type == BlockType.STAB:
        return StabilizerBuild(item_name).block

    # EXCITER (exciter)
    if block_type == BlockType.EXCITER:
        return ExciterBuild(item_name).block

    # LINE (line)
    if block_type == BlockType.LINE:
        blk = line(item_name, api_object)
        return blk

    # EXCITER FAKE (line)
    if block_type == BlockType.EXCITER_FAKE:
        blk = exciter_fake(item_name)
        return blk

    # GOVERNOR FAKE (line)
    if block_type == BlockType.GOVERNOR_FAKE:
        blk = governor_fake(item_name)
        return blk

    else:
        return None


def create_generic_block(state_inputs: int,
                         state_outputs: Sequence[str],
                         algebraic_inputs: int,
                         algebraic_outputs: Sequence[str]):
    """

    :param state_inputs:
    :param state_outputs:
    :param algebraic_inputs:
    :param algebraic_outputs:
    :return:
    """
    blk = generic(state_inputs, state_outputs, algebraic_inputs, algebraic_outputs)
    blk.name = "generic"
    return blk


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
                    update_model(dst_port.subsystem.subsys, dst_port.subsystem.subsys.in_vars[dst_port.index], dst_var)

                    # for i, eq in enumerate(dst_port.subsystem.subsys.algebraic_eqs):
                    #     new_equ = eq.subs({dst_port.subsystem.subsys.in_vars[dst_port.index]: dst_var})
                    #     dst_port.subsystem.subsys.algebraic_eqs[i] = new_equ
                    # for i, eq in enumerate(dst_port.subsystem.subsys.state_eqs):
                    #     new_equ = eq.subs({dst_port.subsystem.subsys.in_vars[dst_port.index]: dst_var})
                    #     dst_port.subsystem.subsys.state_eqs[i] = new_equ
                    #

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


class DynamicLibraryModel(QStandardItemModel):
    """
    Items model to host the draggable icons
    This is the list of draggable items
    """

    def __init__(self) -> None:
        """
        Items model to host the draggable icons
        """
        QStandardItemModel.__init__(self)

        self.setColumnCount(1)

        self.mime_dict: Dict[object, BlockType] = dict()

        for bt in BlockType:
            self.add(name=bt.name, icon_name="dyn")
            t = self.to_bytes_array(bt.name)
            self.mime_dict[t] = bt

    def get_type(self, t) -> BlockType | None:
        """

        :param t:
        :return:
        """

        return self.mime_dict.get(t, None)

    def add(self, name: str, icon_name: str):
        """
        Add element to the library
        :param name: Name of the element
        :param icon_name: Icon name, the path is taken care of
        :return:
        """
        _icon = QIcon()
        _icon.addPixmap(QPixmap(f":/Icons/icons/{icon_name}.png"))
        _item = QStandardItem(_icon, name)
        _item.setToolTip(f"Drag & drop {name} into the schematic")
        self.appendRow(_item)

    @staticmethod
    def to_bytes_array(val: str) -> QByteArray:
        """
        Convert string to QByteArray
        :param val: string
        :return: QByteArray
        """
        data = QByteArray()
        stream = QDataStream(data, QIODevice.OpenModeFlag.WriteOnly)
        stream.writeQString(val)
        return data

    def mimeData(self, idxs: List[QModelIndex]) -> QMimeData:
        """

        @param idxs:
        @return:
        """
        mimedata = QMimeData()
        for idx in idxs:
            if idx.isValid():
                txt = self.data(idx, Qt.ItemDataRole.DisplayRole)

                data = QByteArray()
                stream = QDataStream(data, QIODevice.OpenModeFlag.WriteOnly)
                stream.writeQString(txt)

                mimedata.setData('component/name', data)
        return mimedata

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """

        :param index:
        :return:
        """
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsDragEnabled


class TemplateEditor(QtWidgets.QWidget):
    """
    TemplateEditor
    """

    parametersUpdated = Signal(dict)  # Emitida al cambiar un parámetro
    templateApplied = Signal(object)  # Emitida al aplicar un template al modelo

    def __init__(self, templates_list, templates_catalogue, api_object, parent=None):
        super().__init__(parent)

        self.templates_catalogue = templates_catalogue
        self.model = Block()
        self.api_object = api_object
        self.selected_template = None
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
        # Label above the table
        self.template_name_label = QtWidgets.QLabel("Selected template: <None>")
        main_layout.addWidget(self.template_name_label)

        self.params_table = QtWidgets.QTableWidget()
        self.params_table.setColumnCount(2)
        self.params_table.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.params_table.setEditTriggers(QtWidgets.QTableWidget.EditTrigger.AllEditTriggers)
        main_layout.addWidget(self.params_table)

        # --- Apply template button ---
        # self.btn_apply_template = QtWidgets.QPushButton("Apply Template")
        # self.btn_apply_template.setEnabled(False)
        # main_layout.addWidget(self.btn_apply_template)
        # self.btn_apply_template.clicked.connect(self.on_apply_template)

        # edit cells connection
        self.params_table.cellChanged.connect(self.on_cell_changed)

    def on_select_template(self):
        """uploads the selected template and connects Vm and Va variables with bus variables"""
        template_name = self.template_combo.currentText()
        if template_name not in self.templates_catalogue:
            QtWidgets.QMessageBox.warning(self, "Error", f"Template '{template_name}' not found.")
            return

        self.selected_template = copy.deepcopy(self.templates_catalogue[template_name])
        if self.api_object is not None:
            if self.selected_template.tpe == DeviceType.GeneratorDevice:
                Vm, Va = self.api_object.bus.get_rms_algebraic_vars()
                self.selected_template.Vm = Vm
                self.selected_template.Va = Va

            if self.selected_template.tpe == DeviceType.LoadDevice:
                Vm, Va = self.api_object.bus.get_rms_algebraic_vars()
                self.selected_template.Vm = Vm
                self.selected_template.Va = Va

            if self.selected_template.tpe == DeviceType.LineDevice:
                # bus connection variables
                Vmf, Vaf = self.api_object.bus_from.get_rms_algebraic_vars()
                Vmt, Vat = self.api_object.bus_to.get_rms_algebraic_vars()
                self.selected_template.Vmf = Vmf
                self.selected_template.Vaf = Vaf
                self.selected_template.Vmt = Vmt
                self.selected_template.Vat = Vat
                # power flow parameters
                R, X, B = self.api_object.R, self.api_object.X, self.api_object.B
                self.selected_template.R = R
                self.selected_template.X = X
                self.selected_template.B = B

        # Update label above the table
        self.template_name_label.setText(f"Selected template: {template_name}")
        self.template_name_label.setStyleSheet("font-size: 12pt; margin-top: 8px;")
        self.template_name_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # call editable parameters dialog
        if hasattr(self.selected_template, 'event_dict'):
            if self.selected_template.event_dict:
                self.load_params_table(self.selected_template)

    def load_params_table(self, selected_template):
        """
        Fills the parameters table with the template parameters
        :param selected_template:
        :return:
        """

        event_dict = selected_template.event_dict  # {Var: Const}

        self.params_table.blockSignals(True)
        self.params_table.setRowCount(0)
        self._vars_order = []

        for var, const in event_dict.items():
            row = self.params_table.rowCount()
            self.params_table.insertRow(row)

            self._vars_order.append(var)

            name_item = QtWidgets.QTableWidgetItem(var.name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.params_table.setItem(row, 0, name_item)

            value_item = QtWidgets.QTableWidgetItem(str(const.value))
            self.params_table.setItem(row, 1, value_item)

        self.params_table.blockSignals(False)
        self.params_table.resizeColumnsToContents()

    def on_cell_changed(self, row, column):
        """Updats dict of parameters"""
        if self.selected_template is None or column != 1:
            return

        var = self._vars_order[row]
        value_str = self.params_table.item(row, 1).text()

        try:
            value = float(value_str)
        except ValueError:
            value = value_str  # permitir strings

        self.selected_template.event_dict[var] = Const(value=value, name=var.name)

        self.parametersUpdated.emit(self.selected_template.event_dict)

    def apply_template(self):
        """Apply template to api_object rms_model.template"""

        if self.selected_template is None:
            QtWidgets.QMessageBox.warning(self, "Error", "No template selected.")
            return
        try:
            self.model = self.selected_template.get_block()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to apply template:\n{e}")
            return

    def get_event_dict(self):
        """Returns current event_dict"""
        if self.selected_template is not None:
            return self.selected_template.event_dict
        return {}


class ParameterEditorDialog(QDialog):
    """
    A dialog that edits BOTH:
        - parameters: Dict[str, Const]
        - event_dict: Dict[Var, Const]

    The user only sees a 2-column table:  Name | Value
    Internally we store metadata to reconstruct the updated dicts.
    """

    def __init__(self, parameters: dict, event_dict: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Model Parameters")
        self.resize(450, 350)

        self.parameters = parameters
        self.event_dict = event_dict

        # Output (filled when OK is pressed)
        self.new_parameters = {}
        self.new_event_dict = {}

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Edit the values:"))

        # ---------------------------
        # Table (two columns only)
        # ---------------------------
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Name", "Value"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)
        layout.addWidget(self.table)

        self.populate_table()

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # --------------------------------------------------------

    def populate_table(self):
        """Put both dictionaries into the table."""
        total = len(self.parameters) + len(self.event_dict)
        self.table.setRowCount(total)

        row = 0

        # --- parameters ---
        for name, const in self.parameters.items():
            self.add_row(row, name, getattr(const, "value", const))
            # store metadata
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, ("parameter", name))
            row += 1

        # --- event_dict ---
        for var, const in self.event_dict.items():
            name = getattr(var, "name", str(var))
            self.add_row(row, name, getattr(const, "value", const))
            # store metadata
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, ("event", var))
            row += 1

    # --------------------------------------------------------

    def add_row(self, row, name, value):
        """

        :param row:
        :param name:
        :param value:
        :return:
        """
        name_item = QTableWidgetItem(name)
        name_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        self.table.setItem(row, 0, name_item)

        value_item = QTableWidgetItem(str(value))
        self.table.setItem(row, 1, value_item)

    # --------------------------------------------------------

    def accept(self):
        """Reads table values and rebuilds parameters + event_dict."""
        for row in range(self.table.rowCount()):
            meta = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            value_str = self.table.item(row, 1).text()

            # convert to float if possible
            try:
                value = float(value_str)
            except ValueError:
                value = value_str

            if meta is None:
                continue

            origin, key = meta

            if origin == "parameter":

                self.new_parameters[key] = Const(value)

            elif origin == "event":

                self.new_event_dict[key] = Const(value)

        super().accept()

    # --------------------------------------------------------

    def get_updated_data(self):
        """Return updated (parameters, event_dict)."""
        return self.new_parameters, self.new_event_dict


# class ParameterEditorDialog(QDialog):
#     """
#     Dialogue to edit parameters of a block.
#     """
#
#     def __init__(self, parameters: dict, event_dict: dict, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("Edit Parameters")
#         self.resize(400, 300)
#
#         self.parameters = parameters  # {str: Const}
#         self.new_parameters = {}
#
#         layout = QVBoxLayout(self)
#         layout.addWidget(QLabel("Edit the parameters of this block:"))
#
#         # --- Crear la tabla ---
#         self.table = QTableWidget()
#         self.table.setColumnCount(2)
#         self.table.setHorizontalHeaderLabels(["Parameter", "Value"])
#         self.table.horizontalHeader().setStretchLastSection(True)
#         self.table.verticalHeader().setVisible(False)
#         self.table.setEditTriggers(QTableWidget.AllEditTriggers)
#
#         self.populate_table()
#         layout.addWidget(self.table)
#
#         # ---  OK / Cancel ---
#         buttons = QDialogButtonBox(
#             QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
#             Qt.Horizontal,
#             self,
#         )
#         buttons.accepted.connect(self.accept)
#         buttons.rejected.connect(self.reject)
#         layout.addWidget(buttons)
#
#     # ------------------------------------------------------
#
#     def populate_table(self):
#         """Llena la tabla con los parámetros actuales."""
#         self.table.setRowCount(len(self.parameters))
#         for row, (name, const) in enumerate(self.parameters.items()):
#             # parameter value
#             name_item = QTableWidgetItem(name)
#             name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
#             self.table.setItem(row, 0, name_item)
#
#             # parameter name
#             value = getattr(const, "value", const)
#             value_item = QTableWidgetItem(str(value))
#             self.table.setItem(row, 1, value_item)
#
#     # ------------------------------------------------------
#
#     def accept(self):
#         """update dictionary"""
#         for row in range(self.table.rowCount()):
#             name = self.table.item(row, 0).text()
#             value_text = self.table.item(row, 1).text()
#
#             try:
#                 value = float(value_text)
#             except ValueError:
#                 value = value_text
#             self.new_parameters[name] = Const(value)
#
#         super().accept()
#
#     # ------------------------------------------------------
#
#     def get_parameters(self) -> dict:
#         """Devuelve el diccionario actualizado."""
#         return self.new_parameters

class NameDialog(QDialog):
    """
    NameDialog
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Block name")
        layout = QVBoxLayout(self)

        self.label = QLabel("Enter block name:")
        self.edit = QLineEdit()
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.standardButton().Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self
        )

        layout.addWidget(self.label)
        layout.addWidget(self.edit)
        layout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def get_name(self):
        """

        :return:
        """
        return self.edit.text().strip()


class InspectModel(QWidget):
    """
    InspectModel
    """

    def __init__(self, model_host, parent=None):
        super().__init__(parent)

        self.model_host = model_host  # DynamicModelHost

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
        self.refresh_lists(self.model_host.model)

    def refresh_lists(self, model=None, clear=True):
        """Load current model variables, parameters, equations into lists."""
        if model is None:
            model = self.model_host.model

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
            self.table_params.setItem(row, 0, QTableWidgetItem(param))
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


class BlockBoxesEditor(QSplitter):
    """
    BlockEditor
    """

    def __init__(self,
                 api_object_name: str,
                 block: Block,
                 diagram: BlockDiagram,
                 templates_list,
                 templates_catalogue,
                 api_object=None,
                 parent=None):
        super().__init__(parent)

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

        # Library
        self.library_view = QListView(self)
        self.library_view.setViewMode(self.library_view.ViewMode.ListMode)
        self.library_view.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.library_model = DynamicLibraryModel()
        self.library_view.setModel(self.library_model)
        change_font_size(self.library_view, 9)

        left_layout.addWidget(self.library_view)

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
            bus_from_con_item = BlockItem(name=name)

            Vmf, Vaf = self.api_object.bus_from.get_rms_algebraic_vars()

            bus_from_con_blk = Block(
                algebraic_vars=[Vmf, Vaf],
                out_vars=[Vmf, Vaf],
                name=name
            )

            self.main_block.add(bus_from_con_blk)

            bus_from_con_item.set_subsystem(bus_from_con_blk)
            bus_from_con_item.build_item()

            if bus_from_con_item.subsys is not None:
                self.scene.addItem(bus_from_con_item)
                bus_from_con_item.setPos(x0, y0)
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

            bus_to_con_item = BlockItem(name=name)

            Vmt, Vat = self.api_object.bus_to.get_rms_algebraic_vars()

            bus_to_con_blk = Block(
                algebraic_vars=[Vmt, Vat],
                out_vars=[Vmt, Vat],
                name=name
            )

            self.main_block.add(bus_to_con_blk)

            bus_to_con_item.set_subsystem(bus_to_con_blk)
            bus_to_con_item.build_item()

            # Add to scene
            self.scene.addItem(bus_to_con_item)
            bus_to_con_item.setPos(QPointF(x0, y0))
            if bus_to_con_item.subsys is not None:
                # pdb.set_trace()
                self.scene.addItem(bus_to_con_item)
                bus_to_con_item.setPos(QPointF(x0, y0))
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

            bus_con_item = BlockItem(name=name)
            Vm, Va = self.api_object.bus.get_rms_algebraic_vars()

            bus_con_blk = Block(
                out_vars=[Vm, Va],
                name=name
            )

            self.main_block.add(bus_con_blk)

            bus_con_item.set_subsystem(bus_con_blk)
            bus_con_item.build_item()

            if bus_con_item.subsys is not None:
                self.scene.addItem(bus_con_item)
                bus_con_item.setPos(x0, y0)
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
            bus_from_mapping_item = BlockItem(name=name)

            Pf = Var('Pf_placeholder')
            Qf = Var('Qf_placeholder')

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

            bus_to_mapping_item = BlockItem(name=name)

            Pt = Var('Pt_placeholder')
            Qt = Var('Qt_placeholder')

            bus_to_mapping_blk = Block(
                in_vars=[Pt, Qt],
                name=name
            )
            self.main_block.add(bus_to_mapping_blk)

            bus_to_mapping_item.set_subsystem(bus_to_mapping_blk)
            bus_to_mapping_item.build_item()

            # Add to scene
            self.scene.addItem(bus_from_mapping_item)
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

            bus_mapping_item = BlockItem(name=name)
            P = Var('P_placeholder')
            Q = Var('Q_placeholder')

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

    def open_inspect_dialog(self):
        """

        :return:
        """
        # Crear el diálogo
        dialog = QDialog(self)
        dialog.setWindowTitle("Inspect Model")
        dialog.resize(600, 400)

        # Layout principal del diálogo
        layout = QVBoxLayout(dialog)

        # Obtener el modelo que quieres inspeccionar.
        # Si tu modelo principal está en self.main_block, y tiene un "model_host",
        # puedes pasar ese. Si no, ajusta esta línea según tu arquitectura.
        model_host = DynamicModelHost()
        model_host.model = self.main_block  # o el modelo actual que quieras inspeccionar
        model_host.diagram = self.diagram

        # Crear el widget de inspección
        inspect_widget = InspectModel(model_host, dialog)

        # Añadirlo al layout
        layout.addWidget(inspect_widget)

        # Añadir botones estándar (OK / Cancelar)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(button_box)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        # Mostrar el diálogo
        dialog.exec()

    def remove_item(self, item: BlockItem | ModelHostItem | ConnectionItem):
        """

        :param item:
        :return:
        """
        # remove connection from scene
        if isinstance(item, ConnectionItem):

            del self.diagram.con_data[item.uid]

            source_port = item.source_port
            target_port = item.target_port

            # source_port.connection = None
            # target_port.connection = None

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

        @param event:
        @return:
        """
        if event.mimeData().hasFormat('component/name'):
            event.accept()

    def graphicsDragMoveEvent(self, event: QDragMoveEvent) -> None:
        """
        Move element
        @param event:
        @return:
        """
        if event.mimeData().hasFormat('component/name'):
            event.accept()

    def graphicsDropEvent(self, event: QDropEvent) -> None:
        """
        Create an element
        @param event:
        @return:
        """
        if event.mimeData().hasFormat('component/name'):
            obj_type = event.mimeData().data('component/name')

            point0 = self.view.mapToScene(int(event.position().x()), int(event.position().y()))
            x0 = point0.x()
            y0 = point0.y()

            tpe = self.library_model.get_type(obj_type)

            if tpe == BlockType.GENERIC:
                dialog = GenericBlockDialog(self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    name, state_ins, state_outs, algeb_ins, algeb_outs = dialog.get_values()

                    model_host: DynamicModelHost = DynamicModelHost()

                    model_host.model = create_generic_block(state_ins, state_outs, algeb_ins, algeb_outs)
                    self.main_block.add(model_host.model)
                    item = ModelHostItem(model_host, self.api_object_name, self.templates_list,
                                         self.templates_catalogue, self.api_object)

                    item.setPos(QPointF(x0, y0))
                    self.scene.addItem(item)
                    # save nodes in diagram
                    self.diagram.add_node(
                        name=name,
                        x=x0,
                        y=y0,
                        device_uid=model_host.model.uid,
                        api_object_name=self.api_object_name,
                        tpe=tpe.name,
                        state_ins=state_ins,
                        state_outs=state_outs,
                        algeb_ins=algeb_ins,
                        algeb_outs=algeb_outs,
                        subdiagram=model_host.diagram
                    )

            else:

                count = self.block_counters.get(tpe, 0) + 1
                self.block_counters[tpe] = count

                name = f"{tpe.name}_{count}"
                item = BlockItem(name=name)

                block = create_block_of_type(block_type=tpe, item_name=name, api_object=self.api_object, )
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

        uid_to_blockitem = {}

        # # set number of nodes of the editor
        # self.nodes_index = self.diagram.index

        # Recreate nodes
        for uid, node in self.diagram.node_data.items():
            block_type = BlockType[node.tpe]
            if block_type == BlockType.GENERIC:

                model_host = DynamicModelHost()

                model_host.model = Block()
                for model in self.main_block.children:
                    if model.uid == node.device_uid:
                        model_host.model = model

                model_host.model.uid = uid
                model_host.diagram = node.sub_diagram
                item = ModelHostItem(model_host_sys=model_host, api_object_name=node.api_object_name,
                                     api_object=self.api_object, templates_list=self.templates_list,
                                     templates_catalogue=self.templates_catalogue)

                item.setPos(QPointF(node.x, node.y))
                self.scene.addItem(item)
                brush = item.brush()
                brush.setColor(QColor(node.color))
                item.setBrush(brush)

                uid_to_blockitem[uid] = item

            elif block_type == BlockType.BUS_CONNECTION:
                bus_con_item = BlockItem(name=node.name)
                bus_con_blk = Block()
                for model in self.main_block.children:
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
                bus_mapping_item = BlockItem(name=node.name)
                bus_mapping_blk = Block()
                for model in self.main_block.children:
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

                block_item = BlockItem(name=node.name)
                block = Block()
                for model in self.main_block.children:
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
                continue  # invalid port number

            connection = ConnectionItem(src_port, dst_port)
            connection.uid = uid
            pen = connection.pen()
            pen.setColor(QColor(con.color))
            connection.setPen(pen)
            self.scene.addItem(connection)

        self.block_system = self.scene.get_main_block()


class EditEquations(QWidget):
    """
    EditEquations
    """

    def __init__(self, model, parent=None):
        super().__init__(parent)

        self.model = model  # DynamicModelHost

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

        self.refresh_lists(self.model)

    def refresh_lists(self, model=None, clear=True):
        """Load current model variables, parameters, equations into lists."""
        if model is None:
            model = self.model

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


def add_submodel_vars(model, vars_model, eqns_model, color_map):
    """

    :param model:
    :param vars_model:
    :param eqns_model:
    :param color_map:
    :return:
    """
    for submodel in model.children:
        for var in submodel.state_vars:
            items = [
                QStandardItem(var.name),
                QStandardItem("state"),
            ]
            for it in items:
                it.setForeground(color_map["State variables"])
            vars_model.appendRow(items)
        for eq in submodel.state_eqs:
            eq_item = QStandardItem(str(eq))
            eq_item.setForeground(color_map["State equations"])
            eqns_model.appendRow([eq_item])

        for var in submodel.algebraic_vars:
            items = [
                QStandardItem(var.name),
                QStandardItem("algebraic"),
            ]
            for it in items:
                it.setForeground(color_map["Algebraic variables"])
            vars_model.appendRow(items)
        for eq in submodel.algebraic_eqs:
            eq_item = QStandardItem(str(eq))
            eq_item.setForeground(color_map["Algebraic equations"])
            eqns_model.appendRow([eq_item])

        for param, equ in model.event_dict.items():
            items = [
                QStandardItem(param.name),
                QStandardItem("parameter"),
                QStandardItem(equ.value),
            ]
            for it in items:
                it.setForeground(color_map["Parameters"])
            vars_model.appendRow(items)
        if submodel.children:
            add_submodel_vars(submodel, vars_model, eqns_model, color_map)


def add_vars(model, vars_model, eqns_model, color_map):
    """

    :param model:
    :param vars_model:
    :param eqns_model:
    :param color_map:
    :return:
    """
    for var in model.state_vars:
        items = [
            QStandardItem(var.name),
            QStandardItem("state"),
        ]
        for it in items:
            it.setForeground(color_map["State variables"])
        vars_model.appendRow(items)
    for eq in model.state_eqs:
        eq_item = QStandardItem(str(eq))
        eq_item.setForeground(color_map["State equations"])
        eqns_model.appendRow([eq_item])

    for var in model.algebraic_vars:
        items = [
            QStandardItem(var.name),
            QStandardItem("algebraic"),
        ]
        for it in items:
            it.setForeground(color_map["Algebraic variables"])
        vars_model.appendRow(items)
    for eq in model.algebraic_eqs:
        eq_item = QStandardItem(str(eq))
        eq_item.setForeground(color_map["Algebraic equations"])
        eqns_model.appendRow([eq_item])

    for param, equ in model.event_dict.items():
        items = [
            QStandardItem(param.name),
            QStandardItem("parameter"),
            QStandardItem(equ.value),
        ]
        for it in items:
            it.setForeground(color_map["Parameters"])
        vars_model.appendRow(items)
    if model.children:
        add_submodel_vars(model, vars_model, eqns_model, color_map)


class RmsParameterDialog(QtWidgets.QDialog):  # TODO: Move this section to the template page in the general editor
    """
    RmsParameterDialog
    """

    def __init__(self, event_dict: Dict[Var, Const], parent=None):
        super().__init__(parent)
        # self.event_dict = event_dict
        self.setWindowTitle("Edit RMS Template Parameters")

        layout = QtWidgets.QFormLayout()
        self.inputs = {}

        # Create input (QLineEdit) for each parameter
        for param, equ in event_dict.items():
            # param_value = getattr(template, param_name).value
            line_edit = QtWidgets.QLineEdit(str(equ.value))
            self.inputs[param] = line_edit
            layout.addRow(param.name, line_edit)

        # Botones OK/Cancel
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        self.setLayout(layout)

    def get_new_event_dict(self):
        """Devuelve un diccionario con los valores ingresados por el usuario."""
        return {param: Const(float(edit.text())) for param, edit in self.inputs.items()}


class InitialValuesDialog(QDialog):
    """
    Dialog to edit initial Const values for each Var.
    Now receives a dict[Var, Const] and also includes a checkbox
    per row so the user can select which entries to return.
    """

    def __init__(self, var_const_dict: Dict[Var, Const], parent: Optional[QtWidgets.QWidget] = None):
        """

        :param var_const_dict:
        :param parent:
        """
        super().__init__(parent)
        self.setWindowTitle("Initial Values")

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

            result[var] = Const(new_value)

        return result


class RmsModelEditorGUI(QtWidgets.QMainWindow):
    """
    RmsModelEditorGUI
    """

    def __init__(self, api_object_model_host, templates_list, templates_catalogue, api_object_name,
                 api_object=None, main_editor=False, parent=None):
        """

        :param api_object_model_host:
        :param templates_list:
        :param templates_catalogue:
        :param api_object_name:
        :param api_object:
        :param main_editor:
        :param parent:
        """
        super().__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle("RMS Model Editor")
        self.resize(1000, 700)

        self.api_object_name = api_object_name
        self.model_host = api_object_model_host
        self.templates_list = templates_list
        self.templates_catalogue = templates_catalogue
        self.api_object = api_object
        self.main_editor = main_editor

        self.current_editor = None

        self.tempaltes_name = "Templates"
        self.block_editor_name = "Block Editor"
        self.equationseditor_name = "Equations editor"

        # set modes
        self.ui.model_selector_comboBox.setModel(gf.get_list_model([
            self.tempaltes_name,
            self.block_editor_name,
            self.equationseditor_name
        ]))

        # --- templates editor layout ---
        self.template_editor = TemplateEditor(
            self.templates_list, self.templates_catalogue,
            self.api_object
        )
        # self.ui.templatesLayout.addWidget(self.template_editor)

        # --- block boxes editor layout ---
        self.blockboxes_editor = BlockBoxesEditor(
            api_object_name=self.api_object_name,
            block=self.model_host.custom_model,  # .copy(),
            diagram=self.model_host.diagram,  # .copy(),
            templates_list=self.templates_list,
            templates_catalogue=self.templates_catalogue,
            api_object=self.api_object
        )

        # _____ Add user init guess dialog ______

        # === Add default bus connection block if diagram is empty ===
        if not self.blockboxes_editor.diagram.node_data and self.main_editor:
            self.blockboxes_editor.add_connection_vars()
            self.blockboxes_editor.add_external_mapping_block()
        # === Add pf parameters ===
        self.blockboxes_editor.rebuild_scene_from_diagram()
        self.blockboxes_editor.view.setSceneRect(0, 0, 2000, 2000)  # tamaño arbitrario de escena
        self.blockboxes_editor.view.centerOn(0, 0)
        self.blockboxes_editor.view.ensureVisible(0, 0, 100, 100)
        self.blockboxes_editor.view.horizontalScrollBar().setValue(0)
        self.blockboxes_editor.view.verticalScrollBar().setValue(0)
        # self.ui.editorLayout.addWidget(self.blockboxes_editor)

        # --- equations editor layout ---
        self.equations_editor = EditEquations(self.model_host.model)
        # self.ui.equations_editor_layout.addWidget(self.equations_editor)

        # --- status bar setup ---
        self.status_label = QtWidgets.QLabel("🔵 No model applied")
        if self.model_host.diagram.status is not None:
            self.status_label.setText(f"🟢 Current model: {self.model_host.diagram.status}")
        self.statusBar().addPermanentWidget(self.status_label)
        self.statusBar().showMessage("Ready")

        # --- connections ---
        self.ui.doItButton.clicked.connect(self.do_it)
        self.ui.InitGuessButton.clicked.connect(self.add_init_guess)

        # current editor view change
        self.ui.model_selector_comboBox.currentIndexChanged.connect(self.editor_change)

        # select the template view
        self.ui.model_selector_comboBox.setCurrentIndex(0)
        self.editor_change()

        # innit guess button

        if not self.main_editor:
            self.ui.InitGuessButton.setVisible(False)

    def editor_change(self):
        """
        On change the editor mode
        """
        # delete all widgets from the layout
        for i in reversed(range(self.ui.mainLayout.count())):
            # get the widget
            widget_to_remove = self.ui.mainLayout.itemAt(i).widget()

            # delete it from the layout list
            self.ui.mainLayout.removeWidget(widget_to_remove)

            # delete it from the gui
            widget_to_remove.setParent(None)

        if self.ui.model_selector_comboBox.currentText() == self.tempaltes_name:
            self.ui.mainLayout.addWidget(self.template_editor)
            self.current_editor = self.template_editor

        elif self.ui.model_selector_comboBox.currentText() == self.block_editor_name:
            self.ui.mainLayout.addWidget(self.blockboxes_editor)
            self.current_editor = self.blockboxes_editor

        elif self.ui.model_selector_comboBox.currentText() == self.equationseditor_name:
            # TODO: add model host logic
            self.ui.mainLayout.addWidget(self.equations_editor)
            self.current_editor = self.equations_editor

        else:
            raise ValueError("Unsupported RMS editor!")

        self.ui.currently_editing_object_label.setText(self.api_object_name)

    def do_it(self) -> None:
        """
        Logic when aplying the window
        :return:
        """
        if self.ui.model_selector_comboBox.currentText() == self.tempaltes_name:
            if self.template_editor.selected_template is not None:
                self.template_editor.apply_template()
                self.model_host.template = self.template_editor.model
            else:
                error_msg("Empty template :(", "Model apply")
                return

        elif self.ui.model_selector_comboBox.currentText() == self.block_editor_name:
            if self.blockboxes_editor.main_block is not None:
                self.model_host.template = None
                self.model_host.diagram = self.blockboxes_editor.diagram
                # self.model_host.custom_model = self.blockboxes_editor.block_system
            else:
                error_msg("Empty model :(", "Model apply")
                return

        elif self.ui.model_selector_comboBox.currentText() == self.equationseditor_name:
            # TODO: add model host logic
            pass

        else:
            raise ValueError("Unsupported RMS editor!")

        self.close()

    def add_init_guess(self):
        """

        :return:
        """
        if isinstance(self.current_editor, TemplateEditor):
            if self.current_editor.selected_template is None:
                QtWidgets.QMessageBox.warning(self, "Error", "No template selected.")
                return
            try:
                template = self.current_editor.selected_template
                if template.init_values:
                    values_dict = template.init_values.copy()
                else:
                    model = template.get_block()
                    values_dict: Dict[Var, Const] = dict()
                    variables = model.get_all_vars()
                    for var in variables:
                        values_dict.update({var: Const(0)})

                # TODO: add logic to get all variables from the model and pass them to InitialValuesDialog

                init_guess_editor = InitialValuesDialog(values_dict)
                result = init_guess_editor.exec()
                if result == QDialog.DialogCode.Accepted:
                    init_values_dict = init_guess_editor.get_values_dict()
                    template.init_values = init_values_dict

            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Failed get variables from template:\n{e}")
                return
        elif isinstance(self.current_editor, BlockBoxesEditor):
            model = self.current_editor.main_block

            if model.init_values:
                values_dict = model.init_values.copy()
            else:
                values_dict: Dict[Var, Const] = dict()
                variables = model.get_all_vars()
                for var in variables:
                    values_dict.update({var: Const(0)})

            # TODO: add logic to get all variables from the model and pass them to InitialValuesDialog

            init_guess_editor = InitialValuesDialog(values_dict)
            result = init_guess_editor.exec()
            if result == QDialog.DialogCode.Accepted:
                init_values_dict = init_guess_editor.get_values_dict()
                model.init_values = init_values_dict

        elif isinstance(self.current_editor, EditEquations):
            # TODO: add logic for this case
            pass


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = BlockBoxesEditor(
#         block=Block(),
#         diagram=BlockDiagram()
#     )
#     window.show()
#     sys.exit(app.exec())
