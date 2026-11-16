# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Reduced, read-only schematics used by the Operator View."""

from __future__ import annotations

import cmath
import math
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets

import VeraGridEngine.Devices as dev
from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_auto_layout import (
    apply_initial_auto_layout_to_diagram,
    should_auto_layout_before_first_draw,
)
from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import (
    generate_schematic_diagram,
    get_devices_to_expand,
)
from VeraGrid.Gui.Diagrams.SchematicWidget.Substation.bus_graphics import BusGraphicItem
from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.line_graphics_template import LineGraphicTemplateItem
from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.transformer3w_graphics import Transformer3WGraphicItem
from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.transformerNw_graphics import TransformerNWGraphicItem
from VeraGrid.Gui.Diagrams.generic_graphics import ACTIVE, DraggableLabelItem
from VeraGrid.Gui.gui_functions import add_menu_entry, translate_context_menu_text
from VeraGridEngine.Devices.Diagrams.schematic_diagram import SchematicDiagram
from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Simulations.OPF.opf_results import OptimalPowerFlowResults
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import PowerFlowResults
from VeraGridEngine.Simulations.ShortCircuitStudies.short_circuit_results import ShortCircuitResults

if TYPE_CHECKING:
    from VeraGrid.Gui.Main.VeraGridMain import VeraGridMainGUI


def get_operator_focal_buses(circuit: MultiCircuit, device: ALL_DEV_TYPES) -> list[Bus]:
    """Get the buses represented fully for one operator selection.

    :param circuit: Circuit owning the selected device.
    :param device: Device selected in the Operator View table.
    :return: Buses that remain full bus graphics in the reduced diagram.
    """
    focal_buses: list[Bus] = list()
    if isinstance(device, Bus):
        focal_buses.append(device)
    elif isinstance(device, InjectionParent):
        if device.bus is not None:
            focal_buses.append(device.bus)
        else:
            pass
    elif isinstance(device, BranchParent):
        if device.bus_from is not None:
            focal_buses.append(device.bus_from)
        else:
            pass
        if device.bus_to is not None and device.bus_to not in focal_buses:
            focal_buses.append(device.bus_to)
        else:
            pass
    elif isinstance(device, dev.Transformer3W):
        focal_buses.extend([device.bus1, device.bus2, device.bus3])
    elif isinstance(device, dev.TransformerNW):
        for bus in device.buses:
            if bus is not None and bus not in focal_buses:
                focal_buses.append(bus)
            else:
                pass
    elif isinstance(device, dev.Substation):
        focal_buses.extend(circuit.get_substation_buses(substation=device))
    else:
        pass
    return focal_buses


def make_operator_diagram(circuit: MultiCircuit, focal_buses: list[Bus]) -> SchematicDiagram | None:
    """Build one-hop context without adding equipment connected to context buses.

    :param circuit: Circuit providing the electrical connectivity.
    :param focal_buses: Fully represented buses of the current selection.
    :return: Transient operator diagram, or ``None`` without an electrical anchor.
    """
    diagram: SchematicDiagram | None = None
    if len(focal_buses) > 0:
        (buses, lines, dc_lines, transformers2w, transformers3w, transformers_nw,
         windings, hvdc_lines, vsc_converters, upfc_devices, series_reactances,
         switches, fluid_nodes, fluid_paths) = get_devices_to_expand(
            circuit=circuit,
            buses_set=focal_buses,
            max_level=1,
        )
        diagram = generate_schematic_diagram(
            buses=buses,
            lines=lines,
            dc_lines=dc_lines,
            transformers2w=transformers2w,
            transformers3w=transformers3w,
            transformers_nw=transformers_nw,
            windings=windings,
            hvdc_lines=hvdc_lines,
            vsc_devices=vsc_converters,
            upfc_devices=upfc_devices,
            series_reactances=series_reactances,
            switches=switches,
            fluid_nodes=fluid_nodes,
            fluid_paths=fluid_paths,
            name="Operator context",
        )
        if should_auto_layout_before_first_draw(diagram=diagram):
            apply_initial_auto_layout_to_diagram(diagram=diagram, position_scale=180.0)
        else:
            pass
    else:
        pass
    return diagram


class OperatorGraphicsManager:
    """Minimal native-graphics registration sink for the read-only operator canvas."""

    __slots__ = ()

    def add_device(self, elm: ALL_DEV_TYPES, graphic: QtWidgets.QGraphicsItem) -> None:
        """Accept native child-graphic registration without retaining editor state.

        :param elm: Device represented by the child graphic.
        :param graphic: Native child graphics item.
        :return: None.
        """
        _ = elm
        _ = graphic


class OperatorBusGraphicItem(BusGraphicItem):
    """Native bus graphic restricted to read-only Operator View behaviour."""

    __slots__ = ()

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Keep the full bus symbol read-only in the operator canvas.

        :param event: Qt graphics mouse press event.
        :return: None.
        """
        if bool(event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
            self.editor.center_on_bus(self.api_object)
            event.accept()
        else:
            QtWidgets.QGraphicsRectItem.mousePressEvent(self, event)

    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Prevent native editor persistence when an item is dragged.

        :param event: Qt graphics mouse move event.
        :return: None.
        """
        QtWidgets.QGraphicsRectItem.mouseMoveEvent(self, event)

    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Prevent device editor opening from the read-only operator canvas.

        :param event: Qt graphics mouse double-click event.
        :return: None.
        """
        event.ignore()

    def itemChange(self,
                   change: QtWidgets.QGraphicsItem.GraphicsItemChange,
                   value: object) -> object:
        """Redraw attached transient branches after a bus move.

        :param change: Qt graphics-item state change.
        :param value: Value proposed by Qt for the changed state.
        :return: Value accepted by the base graphics item.
        """
        result: object = QtWidgets.QGraphicsRectItem.itemChange(self, change, value)
        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.editor.refresh_branches_for_bus(bus=self.api_object)
        else:
            pass
        return result


class OperatorBranchGraphicItem(LineGraphicTemplateItem):
    """Native schematic branch graphic restricted to operator navigation."""

    __slots__ = ()

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Keep a native branch movable only through its attached native buses.

        :param event: Qt graphics mouse press event.
        :return: None.
        """
        event.ignore()

    def enable_disable_toggle(self) -> None:
        """Toggle active status without invoking persistent editor profile actions.

        :return: None.
        """
        if self.api_object is not None:
            self.set_enable(not self.api_object.active)
        else:
            pass

    def contextMenuEvent(self, event: QtWidgets.QGraphicsSceneContextMenuEvent) -> None:
        """Show the native shared branch context controls for this transient graphic.

        :param event: Qt context-menu event.
        :return: None.
        """
        if self.api_object is not None:
            menu: QtWidgets.QMenu = QtWidgets.QMenu()
            menu.addSection(translate_context_menu_text("Branch"))
            add_menu_entry(
                menu=menu,
                text=translate_context_menu_text("Active"),
                function_ptr=self.enable_disable_toggle,
                checkeable=True,
                checked_value=self.api_object.active,
            )
            add_menu_entry(
                menu=menu,
                text=translate_context_menu_text("Draw labels"),
                function_ptr=self.enable_disable_label_drawing,
                checkeable=True,
                checked_value=self.draw_labels,
            )
            menu.addSeparator()
            self.add_auto_route_style_menu(menu=menu)
            menu.exec_(event.screenPos())
        else:
            pass


class OperatorContextNodeItem(QtWidgets.QGraphicsEllipseItem):
    """Movable one-hop bus node that requests operator-context navigation."""

    __slots__ = ('_badge', '_bus', '_editor', '_label')

    def __init__(self, editor: "OperatorSchematic", bus: Bus, x: float, y: float) -> None:
        """Create one transient context node.

        :param editor: Owning operator schematic.
        :param bus: Context bus represented by this node.
        :param x: Scene x coordinate.
        :param y: Scene y coordinate.
        :return: None.
        """
        radius: float = 10.0
        QtWidgets.QGraphicsEllipseItem.__init__(self, -radius, -radius, radius * 2.0, radius * 2.0)
        self._bus: Bus = bus
        self._editor: OperatorSchematic = editor
        self.setPos(x, y)
        self.setData(0, bus)
        self.setBrush(QtGui.QBrush(QtGui.QColor("#ffffff")))
        self.setPen(QtGui.QPen(QtGui.QColor("#374151"), 2.0))
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._label: DraggableLabelItem = DraggableLabelItem(self)
        self._label.setDefaultTextColor(ACTIVE['text'])
        self._label.document().setDocumentMargin(0.0)
        self._label.setScale(1.0)
        self._badge: QtWidgets.QGraphicsPathItem = QtWidgets.QGraphicsPathItem(self)
        self._badge.setPen(QtGui.QPen(QtGui.QColor(ACTIVE['text']), 1.0))
        self._badge.setBrush(QtGui.QBrush(QtGui.QColor(ACTIVE['background'])))
        self._badge.setZValue(-1.0)
        self.set_result_text(voltage=None, angle_degrees=None, power=None, reactive_power=None)

    def set_result_text(self, voltage: float | None, angle_degrees: float | None,
                        power: float | None, reactive_power: float | None) -> None:
        """Show snapshot values beside the movable context node.

        :param voltage: Per-unit voltage magnitude, when available.
        :param power: Active injection in MW, when available.
        :param reactive_power: Reactive injection in MVAr, when available.
        :return: None.
        """
        if voltage is not None and angle_degrees is not None and power is not None and reactive_power is not None:
            text: str = f"{self._bus.name}<br>V={voltage:.4f} p.u. ∠{angle_degrees:.2f}°<br>P={power:.2f} MW<br>Q={reactive_power:.2f} MVAr"
        else:
            text = self._bus.name
        self._label.setHtml(f'<div style="font-size:9pt; font-weight:600; text-align:center;">{text}</div>')
        label_rect: QtCore.QRectF = self._label.boundingRect()
        self._label.set_anchor_position(QtCore.QPointF(14.0, -label_rect.height() / 2.0))
        badge_rect: QtCore.QRectF = self._label.mapRectToParent(label_rect).adjusted(-4.0, -2.0, 4.0, 2.0)
        badge_path: QtGui.QPainterPath = QtGui.QPainterPath()
        badge_path.addRoundedRect(badge_rect, 4.0, 4.0)
        self._badge.setPath(badge_path)

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Navigate from Ctrl-click or start a normal node drag.

        :param event: Qt graphics mouse press event.
        :return: None.
        """
        if bool(event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
            self._editor.bus_navigation_requested.emit(self._bus)
            event.accept()
        else:
            QtWidgets.QGraphicsEllipseItem.mousePressEvent(self, event)

    def itemChange(self,
                   change: QtWidgets.QGraphicsItem.GraphicsItemChange,
                   value: object) -> object:
        """Update direct branches after the node has moved.

        :param change: Qt graphics-item state change.
        :param value: Value proposed by Qt for the changed state.
        :return: Value accepted by the base graphics item.
        """
        result: object = QtWidgets.QGraphicsEllipseItem.itemChange(self, change, value)
        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._editor.refresh_branches_for_bus(bus=self._bus)
        else:
            pass
        return result


class OperatorTransformer3WGraphicItem(Transformer3WGraphicItem):
    """Read-only native three-winding transformer symbol for the operator canvas."""

    __slots__ = ()

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Allow moving the symbol without opening an editor.

        :param event: Qt graphics mouse press event.
        :return: None.
        """
        QtWidgets.QGraphicsRectItem.mousePressEvent(self, event)

    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Disable device-editor opening in the operator canvas.

        :param event: Qt graphics mouse double-click event.
        :return: None.
        """
        event.ignore()


class OperatorTransformerNWGraphicItem(TransformerNWGraphicItem):
    """Read-only native N-winding transformer symbol for the operator canvas."""

    __slots__ = ()

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Allow moving the symbol without opening an editor.

        :param event: Qt graphics mouse press event.
        :return: None.
        """
        QtWidgets.QGraphicsRectItem.mousePressEvent(self, event)

    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Disable device-editor opening in the operator canvas.

        :param event: Qt graphics mouse double-click event.
        :return: None.
        """
        event.ignore()

    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Prevent device-editor opening from the operator canvas.

        :param event: Qt graphics mouse double-click event.
        :return: None.
        """
        event.ignore()


class OperatorSchematic(QtWidgets.QGraphicsView):
    """Read-only one-hop electrical context with Ctrl-click navigation nodes."""

    bus_navigation_requested = QtCore.Signal(object)

    __slots__ = (
        '_circuit', '_diagram', '_focal_buses', '_is_disposed', '_scene', '_visible_branches',
        '_visible_buses', '_zoom_steps', '_bus_graphics', '_branch_graphics', '_multiwinding_graphics',
        '_node_graphics', '_branch_endpoint_buses', 'gui', 'graphics_manager',
    )

    def __init__(self,
                 circuit: MultiCircuit,
                 focal_buses: list[Bus],
                 gui: VeraGridMainGUI | None = None,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """Create a transient reduced schematic.

        :param circuit: Circuit providing branch connectivity.
        :param focal_buses: Buses drawn as full bus graphics.
        :param gui: Main GUI owner required by reused schematic graphic actions.
        :param parent: Qt owner of this view.
        :return: None.
        """
        diagram: SchematicDiagram | None = make_operator_diagram(circuit=circuit, focal_buses=focal_buses)
        scene: QtWidgets.QGraphicsScene = QtWidgets.QGraphicsScene(parent)
        QtWidgets.QGraphicsView.__init__(self, scene, parent)
        self.gui: VeraGridMainGUI | None = gui
        self.graphics_manager: OperatorGraphicsManager = OperatorGraphicsManager()
        self._circuit: MultiCircuit | None = circuit
        self._diagram: SchematicDiagram | None = diagram
        self._focal_buses: list[Bus] = list(focal_buses)
        self._is_disposed: bool = False
        self._visible_buses: list[Bus] = list()
        self._visible_branches: list[BranchParent] = list()
        self._bus_graphics: dict[Bus, OperatorBusGraphicItem] = dict()
        self._branch_graphics: dict[BranchParent, OperatorBranchGraphicItem] = dict()
        self._multiwinding_graphics: list[QtWidgets.QGraphicsItem] = list()
        self._node_graphics: dict[Bus, OperatorContextNodeItem] = dict()
        self._branch_endpoint_buses: dict[BranchParent, tuple[Bus, Bus]] = dict()
        self._zoom_steps: int = 0
        # QGraphicsView does not keep a Python-owned scene wrapper alive.
        self._scene: QtWidgets.QGraphicsScene | None = scene
        self.setRenderHints(QtGui.QPainter.RenderHint.Antialiasing | QtGui.QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        if diagram is not None:
            self._draw_diagram(circuit=circuit, diagram=diagram)
        else:
            pass

    @property
    def diagram(self) -> SchematicDiagram | None:
        """Expose the transient diagram required by the reused bus graphic.

        :return: Operator diagram while the view is alive.
        """
        return self._diagram

    def is_loading_diagram(self) -> bool:
        """Disable all native editor persistence for copied bus graphics.

        :return: Always ``True`` for this read-only canvas.
        """
        return True

    def update_diagram_element(self,
                               device: ALL_DEV_TYPES,
                               x: float = 0.0,
                               y: float = 0.0,
                               w: float = 0.0,
                               h: float = 0.0,
                               r: float = 0.0,
                               draw_labels: bool = True,
                               graphic_object: QtWidgets.QGraphicsItem | None = None) -> None:
        """Discard native editor persistence requests from reused bus graphics.

        :param device: Bus device supplied by the reused native graphic.
        :param x: Ignored scene x coordinate.
        :param y: Ignored scene y coordinate.
        :param w: Ignored bus width.
        :param h: Ignored bus height.
        :param r: Ignored rotation angle.
        :param draw_labels: Ignored label visibility state.
        :param graphic_object: Ignored native graphics item.
        :return: None.
        """
        _ = device
        _ = x
        _ = y
        _ = w
        _ = h
        _ = r
        _ = draw_labels
        _ = graphic_object

    def get_persisted_attachment(self, api_object: ALL_DEV_TYPES, endpoint: str) -> dict[str, object]:
        """Provide transient endpoint metadata required by native branch graphics.

        :param api_object: Branch requesting one endpoint attachment.
        :param endpoint: Endpoint name, either ``from`` or ``to``.
        :return: Empty transient attachment so the graphic uses its live terminal anchor.
        """
        _ = api_object
        _ = endpoint
        return dict()

    def add_to_scene(self, graphic_object: QtWidgets.QGraphicsItem) -> None:
        """Add a reused native child graphic to the transient operator scene.

        :param graphic_object: Native schematic child graphic to display.
        :return: None.
        """
        scene: QtWidgets.QGraphicsScene | None = self._scene
        if scene is not None:
            scene.addItem(graphic_object)
        else:
            pass

    def update_label_drwaing_status(self, device: ALL_DEV_TYPES, draw_labels: bool) -> None:
        """Ignore native editor label persistence for transient operator graphics.

        :param device: Native graphic device requesting the label-state update.
        :param draw_labels: Requested label visibility.
        :return: None.
        """
        _ = device
        _ = draw_labels

    def _draw_diagram(self, circuit: MultiCircuit, diagram: SchematicDiagram) -> None:
        """Render only focal buses, their direct branches, and context nodes.

        :param circuit: Circuit supplying the branches to render.
        :param diagram: Diagram supplying stable bus locations.
        :return: None.
        """
        scene: QtWidgets.QGraphicsScene | None = self._scene
        if scene is not None:
            buses: list[Bus] = list()
            for bus in circuit.get_buses():
                if diagram.query_point(device=bus) is not None:
                    buses.append(bus)
                else:
                    pass
            self._visible_buses = buses
            for bus in buses:
                if bus in self._focal_buses:
                    self._draw_focal_bus(scene=scene, diagram=diagram, bus=bus)
                else:
                    self._draw_context_node(scene=scene, diagram=diagram, bus=bus)
            self._draw_multiwinding_devices(scene=scene, circuit=circuit, diagram=diagram)
            self._draw_branches(scene=scene, circuit=circuit, diagram=diagram)
            self._fit_scene()
        else:
            pass

    def _draw_multiwinding_devices(self,
                                   scene: QtWidgets.QGraphicsScene,
                                   circuit: MultiCircuit,
                                   diagram: SchematicDiagram) -> None:
        """Draw native multi-winding transformer symbols present in the context.

        :param scene: Destination graphics scene.
        :param circuit: Circuit owning the transformer devices.
        :param diagram: Operator diagram defining transient transformer positions.
        :return: None.
        """
        transformer: dev.Transformer3W
        for transformer in circuit.transformers3w:
            location = diagram.query_point(device=transformer)
            if location is not None:
                graphic: OperatorTransformer3WGraphicItem = OperatorTransformer3WGraphicItem(
                    editor=self,
                    elm=transformer,
                    pos=QtCore.QPoint(int(location.x), int(location.y)),
                    draw_labels=True,
                )
                scene.addItem(graphic)
                self._multiwinding_graphics.append(graphic)
            else:
                pass
        transformer_nw: dev.TransformerNW
        for transformer_nw in circuit.transformers_nw:
            location = diagram.query_point(device=transformer_nw)
            if location is not None:
                graphic_nw: OperatorTransformerNWGraphicItem = OperatorTransformerNWGraphicItem(
                    editor=self,
                    elm=transformer_nw,
                    pos=QtCore.QPoint(int(location.x), int(location.y)),
                    draw_labels=True,
                )
                scene.addItem(graphic_nw)
                self._multiwinding_graphics.append(graphic_nw)
            else:
                pass

    def _draw_branches(self,
                       scene: QtWidgets.QGraphicsScene,
                       circuit: MultiCircuit,
                       diagram: SchematicDiagram) -> None:
        """Draw direct electrical connections, stopping at the context nodes.

        :param scene: Destination graphics scene.
        :param circuit: Circuit providing candidate branches.
        :param diagram: Diagram defining which buses are visible.
        :return: None.
        """
        branch: BranchParent
        for branch in circuit.get_branches(add_vsc=True, add_hvdc=True, add_switch=True):
            bus_from: Bus | None = branch.bus_from
            bus_to: Bus | None = branch.bus_to
            if (bus_from is not None and bus_to is not None
                    and (bus_from in self._focal_buses or bus_to in self._focal_buses)
                    and diagram.query_point(device=bus_from) is not None
                    and diagram.query_point(device=bus_to) is not None):
                from_location = diagram.query_point(device=bus_from)
                to_location = diagram.query_point(device=bus_to)
                if from_location is not None and to_location is not None:
                    from_graphic: OperatorBusGraphicItem | None = self._bus_graphics.get(bus_from, None)
                    to_graphic: OperatorBusGraphicItem | None = self._bus_graphics.get(bus_to, None)
                    branch_from_bus: Bus = bus_from if from_graphic is not None else bus_to
                    branch_to_bus: Bus = bus_to if from_graphic is not None else bus_from
                    branch_from_graphic: OperatorBusGraphicItem | None = self._bus_graphics.get(branch_from_bus, None)
                    branch_to_graphic: OperatorBusGraphicItem | None = self._bus_graphics.get(branch_to_bus, None)
                    if branch_from_graphic is not None:
                        line: OperatorBranchGraphicItem = OperatorBranchGraphicItem(
                            from_port=branch_from_graphic.get_terminal(),
                            to_port=branch_to_graphic.get_terminal() if branch_to_graphic is not None else None,
                            editor=self,
                            width=3,
                            api_object=branch,
                            draw_labels=True,
                        )
                        line.pos1 = self._get_bus_anchor(bus=branch_from_bus)
                        line.pos2 = self._get_bus_anchor(bus=branch_to_bus)
                        middle_x: float = (line.pos1.x() + line.pos2.x()) / 2.0
                        line._route_points = [
                            (line.pos1.x(), line.pos1.y()),
                            (middle_x, line.pos1.y()),
                            (middle_x, line.pos2.y()),
                            (line.pos2.x(), line.pos2.y()),
                        ]
                        line.redraw()
                        line.set_enable(bool(branch.active))
                        scene.addItem(line)
                        from_terminal = line.get_terminal_from()
                        to_terminal = line.get_terminal_to()
                        if from_terminal is not None:
                            from_terminal.delete_hosting_connection(graphic_obj=line)
                        else:
                            pass
                        if to_terminal is not None:
                            to_terminal.delete_hosting_connection(graphic_obj=line)
                        else:
                            pass
                        self._branch_graphics[branch] = line
                        self._branch_endpoint_buses[branch] = (branch_from_bus, branch_to_bus)
                    else:
                        pass
                    self._visible_branches.append(branch)
                else:
                    pass
            else:
                pass

    def refresh_branches_for_bus(self, bus: Bus) -> None:
        """Keep every orthogonal operator branch attached to a moved bus.

        :param bus: Bus whose native graphic has changed scene position.
        :return: None.
        """
        branch: BranchParent
        for branch in self._visible_branches:
            if branch.bus_from is bus or branch.bus_to is bus:
                branch_graphic: OperatorBranchGraphicItem | None = self._branch_graphics.get(branch, None)
                endpoint_buses: tuple[Bus, Bus] | None = self._branch_endpoint_buses.get(branch, None)
                if branch_graphic is not None and endpoint_buses is not None:
                    branch_graphic.pos1 = self._get_bus_anchor(bus=endpoint_buses[0])
                    branch_graphic.pos2 = self._get_bus_anchor(bus=endpoint_buses[1])
                    middle_x: float = (branch_graphic.pos1.x() + branch_graphic.pos2.x()) / 2.0
                    branch_graphic._route_points = [
                        (branch_graphic.pos1.x(), branch_graphic.pos1.y()),
                        (middle_x, branch_graphic.pos1.y()),
                        (middle_x, branch_graphic.pos2.y()),
                        (branch_graphic.pos2.x(), branch_graphic.pos2.y()),
                    ]
                    branch_graphic.redraw()
                else:
                    pass
            else:
                pass

    def _get_bus_anchor(self, bus: Bus) -> QtCore.QPointF:
        """Get the current scene anchor for either a full bus or context node.

        :param bus: Visible bus whose branch endpoint is needed.
        :return: Current center point for the displayed bus representation.
        """
        bus_graphic: OperatorBusGraphicItem | None = self._bus_graphics.get(bus, None)
        if bus_graphic is not None:
            return bus_graphic.scenePos() + QtCore.QPointF(bus_graphic.w / 2.0, bus_graphic.h / 2.0)
        else:
            node: OperatorContextNodeItem | None = self._node_graphics.get(bus, None)
            if node is not None:
                return node.scenePos()
            else:
                return QtCore.QPointF()

    def _draw_focal_bus(self,
                        scene: QtWidgets.QGraphicsScene,
                        diagram: SchematicDiagram,
                        bus: Bus,
                        is_context: bool = False) -> None:
        """Draw one selected bus using its schematic size and label.

        :param scene: Destination graphics scene.
        :param diagram: Diagram providing bus geometry.
        :param bus: Fully represented selected bus.
        :return: None.
        """
        location = diagram.query_point(device=bus)
        if location is not None:
            bus_graphic: OperatorBusGraphicItem = OperatorBusGraphicItem(
                editor=self,
                bus=bus,
                x=float(location.x),
                y=float(location.y),
                w=max(float(location.w), 180.0 if is_context else 260.0),
                h=max(float(location.h), 40.0 if is_context else 70.0),
                draw_labels=True,
            )
            bus_graphic.setData(0, bus)
            bus_graphic.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            bus_graphic.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
            bus_graphic.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            bus_graphic.get_terminal().setAcceptedMouseButtons(QtCore.Qt.MouseButton.NoButton)
            if bus_graphic.sizer is not None:
                bus_graphic.sizer.setVisible(False)
            else:
                pass
            scene.addItem(bus_graphic)
            self._bus_graphics[bus] = bus_graphic
            self._draw_incumbent_injections(circuit=self._circuit, bus=bus, bus_graphic=bus_graphic)
        else:
            pass

    def _draw_incumbent_injections(self,
                                   circuit: MultiCircuit | None,
                                   bus: Bus,
                                   bus_graphic: OperatorBusGraphicItem) -> None:
        """Attach existing injection graphics only to one incumbent bus.

        :param circuit: Circuit containing existing injection devices.
        :param bus: Incumbent bus receiving the visible injection graphics.
        :param bus_graphic: Native reusable bus graphic hosting those injections.
        :return: None.
        """
        if circuit is not None and bus in self._focal_buses:
            grouped_devices = circuit.get_injection_devices_grouped_by_bus().get(bus, dict())
            devices: list[ALL_DEV_TYPES] = list()
            device_group: list[ALL_DEV_TYPES]
            for device_group in grouped_devices.values():
                devices.extend(device_group)
            device: ALL_DEV_TYPES
            for device in devices:
                if isinstance(device, dev.Load):
                    bus_graphic.add_load(api_obj=device)
                elif isinstance(device, dev.Generator):
                    bus_graphic.add_generator(api_obj=device)
                elif isinstance(device, dev.StaticGenerator):
                    bus_graphic.add_static_generator(api_obj=device)
                elif isinstance(device, dev.Battery):
                    bus_graphic.add_battery(api_obj=device)
                elif isinstance(device, dev.Shunt):
                    bus_graphic.add_shunt(api_obj=device)
                elif isinstance(device, dev.ExternalGrid):
                    bus_graphic.add_external_grid(api_obj=device)
                elif isinstance(device, dev.CurrentInjection):
                    bus_graphic.add_current_injection(api_obj=device)
                elif isinstance(device, dev.ControllableShunt):
                    bus_graphic.add_controllable_shunt(api_obj=device)
                else:
                    pass
            injection_graphic: QtWidgets.QGraphicsItem
            for injection_graphic in bus_graphic._child_graphics:
                injection_graphic.setAcceptedMouseButtons(QtCore.Qt.MouseButton.NoButton)
                child_graphic: QtWidgets.QGraphicsItem
                for child_graphic in injection_graphic.childItems():
                    child_graphic.setAcceptedMouseButtons(QtCore.Qt.MouseButton.NoButton)
        else:
            pass

    def _draw_context_node(self, scene: QtWidgets.QGraphicsScene, diagram: SchematicDiagram, bus: Bus) -> None:
        """Draw one external bus as a movable navigation-only node.

        :param scene: Destination graphics scene.
        :param diagram: Diagram providing the initial node coordinate.
        :param bus: External one-hop bus.
        :return: None.
        """
        location = diagram.query_point(device=bus)
        if location is not None:
            node: OperatorContextNodeItem = OperatorContextNodeItem(
                editor=self,
                bus=bus,
                x=float(location.x),
                y=float(location.y),
            )
            scene.addItem(node)
            self._node_graphics[bus] = node
        else:
            pass

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Navigate when Ctrl-click selects an adjacent node.

        :param event: Mouse press received by the graphics view.
        :return: None.
        """
        if bool(event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
            scene: QtWidgets.QGraphicsScene | None = self._scene
            if scene is not None:
                item = scene.itemAt(self.mapToScene(event.position().toPoint()), self.transform())
                if isinstance(item, QtWidgets.QGraphicsEllipseItem) and not isinstance(item, OperatorContextNodeItem):
                    bus: object = item.data(0)
                    if isinstance(bus, Bus):
                        self.bus_navigation_requested.emit(bus)
                    else:
                        pass
                else:
                    pass
            else:
                pass
        else:
            pass
        QtWidgets.QGraphicsView.mousePressEvent(self, event)

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        """Zoom the read-only operator canvas around the mouse pointer.

        :param event: Wheel event received by the graphics view.
        :return: None.
        """
        if event.angleDelta().y() > 0 and self._zoom_steps < 12:
            self.scale(1.15, 1.15)
            self._zoom_steps += 1
        elif event.angleDelta().y() < 0 and self._zoom_steps > -12:
            self.scale(1.0 / 1.15, 1.0 / 1.15)
            self._zoom_steps -= 1
        else:
            pass
        event.accept()

    @QtCore.Slot(object)
    def center_on_bus(self, bus: object) -> None:
        """Center the existing context on a Ctrl-clicked bus node.

        :param bus: Bus emitted from a context-node Ctrl-click.
        :return: None.
        """
        scene: QtWidgets.QGraphicsScene | None = self._scene
        if isinstance(bus, Bus) and scene is not None:
            item: QtWidgets.QGraphicsItem
            for item in scene.items():
                if item.data(0) is bus:
                    self.centerOn(item)
                else:
                    pass
        else:
            pass

    def set_results(self, results: object) -> None:
        """Colour supported snapshot results without creating editor graphics.

        :param results: Selected simulation result object.
        :return: None.
        """
        if isinstance(results, (PowerFlowResults, OptimalPowerFlowResults)):
            self._colour_network(
                voltages=results.voltage,
                bus_powers=results.Sbus,
                branch_powers_from=results.Sf,
                branch_powers_to=results.St,
                loadings=results.loading,
            )
        elif isinstance(results, ShortCircuitResults):
            self._colour_network(
                voltages=results.voltage1[:, 0],
                bus_powers=results.Sbus1[:, 0],
                branch_powers_from=results.Sf1[:, 0],
                branch_powers_to=results.St1[:, 0],
                loadings=results.loading1[:, 0],
            )
        else:
            pass

    def clear_results(self) -> None:
        """Restore neutral colours when no simulation is selected.

        :return: None.
        """
        scene: QtWidgets.QGraphicsScene | None = self._scene
        if scene is not None:
            item: QtWidgets.QGraphicsItem
            for item in scene.items():
                if isinstance(item, OperatorBusGraphicItem):
                    item.update_color()
                    item.clear_label()
                elif isinstance(item, QtWidgets.QGraphicsPathItem):
                    item.setPen(QtGui.QPen(QtGui.QColor("#4b5563"), 3.0))
                else:
                    pass
            branch_graphic: OperatorBranchGraphicItem
            for branch_graphic in self._branch_graphics.values():
                branch_graphic.set_colour(QtGui.QColor("#4b5563"), 3.0, QtCore.Qt.PenStyle.SolidLine)
                branch_graphic.set_arrows_with_power(Sf=None, St=None)
        else:
            pass

    def get_summary_rows(self, results: object | None) -> list[list[str]]:
        """Build visible bus and branch values for the Operator View table.

        :param results: Selected simulation result object, if any.
        :return: Display rows ordered by buses and direct branches.
        """
        rows: list[list[str]] = list()
        bus: Bus
        for bus in self._visible_buses:
            rows.append(self._get_bus_summary_row(bus=bus, results=results))
        branch: BranchParent
        for branch in self._visible_branches:
            rows.append(self._get_branch_summary_row(branch=branch, results=results))
        return rows

    def _get_bus_summary_row(self, bus: Bus, results: object | None) -> list[str]:
        """Build one visible-bus summary row.

        :param bus: Bus displayed in the reduced schematic.
        :param results: Selected simulation result object, if any.
        :return: Element, name, voltage, active power, reactive power and loading cells.
        """
        voltage: str = ""
        power: str = ""
        reactive_power: str = ""
        circuit: MultiCircuit | None = self._circuit
        if circuit is not None:
            bus_index: int = self._get_bus_index(buses=circuit.get_buses(), bus=bus)
        else:
            bus_index = -1
        if isinstance(results, (PowerFlowResults, OptimalPowerFlowResults)) and 0 <= bus_index < len(results.voltage):
            voltage = f"{abs(results.voltage[bus_index]):.4f} p.u."
            power = f"{results.Sbus[bus_index].real:.2f} MW"
            reactive_power = f"{results.Sbus[bus_index].imag:.2f} MVAr"
        elif isinstance(results, ShortCircuitResults) and 0 <= bus_index < len(results.voltage1):
            voltage = f"{abs(results.voltage1[bus_index, 0]):.4f} p.u."
            power = f"{results.Sbus1[bus_index, 0].real:.2f} MW"
            reactive_power = f"{results.Sbus1[bus_index, 0].imag:.2f} MVAr"
        else:
            pass
        angle: str = ""
        if isinstance(results, (PowerFlowResults, OptimalPowerFlowResults)) and 0 <= bus_index < len(results.voltage):
            angle = f"{math.degrees(cmath.phase(results.voltage[bus_index])):.2f}°"
        elif isinstance(results, ShortCircuitResults) and 0 <= bus_index < len(results.voltage1):
            angle = f"{math.degrees(cmath.phase(results.voltage1[bus_index, 0])):.2f}°"
        else:
            pass
        return ["Bus", bus.name, voltage, angle, power, reactive_power, ""]

    def _get_branch_summary_row(self, branch: BranchParent, results: object | None) -> list[str]:
        """Build one direct-branch summary row.

        :param branch: Branch displayed in the reduced schematic.
        :param results: Selected simulation result object, if any.
        :return: Element, name, voltage, active power, reactive power and loading cells.
        """
        power: str = ""
        reactive_power: str = ""
        loading: str = ""
        branch_index: int = self._get_branch_index(branch=branch)
        if isinstance(results, (PowerFlowResults, OptimalPowerFlowResults)) and 0 <= branch_index < len(results.Sf):
            power = f"{results.Sf[branch_index].real:.2f} MW"
            reactive_power = f"{results.Sf[branch_index].imag:.2f} MVAr"
            loading = f"{abs(results.loading[branch_index]) * 100.0:.1f}%"
        elif isinstance(results, ShortCircuitResults) and 0 <= branch_index < len(results.Sf1):
            power = f"{results.Sf1[branch_index, 0].real:.2f} MW"
            reactive_power = f"{results.Sf1[branch_index, 0].imag:.2f} MVAr"
            loading = f"{abs(results.loading1[branch_index, 0]) * 100.0:.1f}%"
        else:
            pass
        return ["Branch", branch.name, "", "", power, reactive_power, loading]

    def _colour_network(self,
                        voltages: object,
                        bus_powers: object,
                        branch_powers_from: object,
                        branch_powers_to: object,
                        loadings: object) -> None:
        """Apply voltage and loading colours to the reduced graphics items.

        :param voltages: Per-bus complex voltage vector.
        :param bus_powers: Per-bus complex power vector.
        :param branch_powers_from: Per-branch sending-end complex power vector.
        :param branch_powers_to: Per-branch receiving-end complex power vector.
        :param loadings: Per-branch loading vector.
        :return: None.
        """
        scene: QtWidgets.QGraphicsScene | None = self._scene
        if scene is not None:
            circuit: MultiCircuit | None = self._circuit
            if circuit is not None:
                buses: list[Bus] = circuit.get_buses()
                item: QtWidgets.QGraphicsItem
                for item in scene.items():
                    bus = item.data(0)
                    if isinstance(bus, Bus) and isinstance(item, OperatorBusGraphicItem):
                        bus_index: int = self._get_bus_index(buses=buses, bus=bus)
                        if 0 <= bus_index < len(voltages):
                            complex_voltage: complex = voltages[bus_index]
                            voltage: float = abs(complex_voltage)
                            item.set_tile_color(self._get_voltage_colour(voltage=voltage))
                            item.set_values(
                                i=bus_index,
                                Vm=voltage,
                                Va=math.degrees(cmath.phase(complex_voltage)),
                                P=bus_powers[bus_index].real,
                                Q=bus_powers[bus_index].imag,
                                tpe=None,
                            )
                        else:
                            pass
                    else:
                        pass
                node: OperatorContextNodeItem
                for node in self._node_graphics.values():
                    node_index: int = self._get_bus_index(buses=buses, bus=node._bus)
                    if 0 <= node_index < len(voltages):
                        node_voltage: complex = voltages[node_index]
                        node_power: complex = bus_powers[node_index]
                        node.set_result_text(
                            voltage=abs(node_voltage),
                            angle_degrees=math.degrees(cmath.phase(node_voltage)),
                            power=node_power.real,
                            reactive_power=node_power.imag,
                        )
                    else:
                        pass
                branch: BranchParent
                for branch in self._visible_branches:
                    branch_graphic: OperatorBranchGraphicItem | None = self._branch_graphics.get(branch, None)
                    branch_index: int = self._get_branch_index(branch=branch)
                    if branch_graphic is not None and 0 <= branch_index < len(loadings):
                        loading: float = abs(loadings[branch_index])
                        branch_graphic.set_colour(
                            self._get_loading_colour(loading=loading),
                            3.0,
                            QtCore.Qt.PenStyle.SolidLine,
                        )
                        branch_graphic.set_arrows_with_power(
                            Sf=branch_powers_from[branch_index],
                            St=branch_powers_to[branch_index],
                        )
                    else:
                        pass
            else:
                pass
        else:
            pass

    @staticmethod
    def _get_bus_index(buses: list[Bus], bus: Bus) -> int:
        """Find one bus index in the current circuit ordering.

        :param buses: Ordered circuit buses.
        :param bus: Bus to locate.
        :return: Circuit bus index, or ``-1`` when unavailable.
        """
        return buses.index(bus) if bus in buses else -1

    def _get_branch_index(self, branch: object) -> int:
        """Find one branch index in the snapshot result ordering.

        :param branch: Branch represented by the graphics path.
        :return: Snapshot branch index, or ``-1`` when unavailable.
        """
        circuit: MultiCircuit | None = self._circuit
        if circuit is not None:
            branches: list[BranchParent] = circuit.get_branches(
                add_vsc=False,
                add_hvdc=False,
                add_switch=True,
            )
            return branches.index(branch) if branch in branches else -1
        else:
            return -1

    @staticmethod
    def _get_voltage_colour(voltage: float) -> QtGui.QColor:
        """Map voltage magnitude to a concise operator colour.

        :param voltage: Per-unit voltage magnitude.
        :return: Fill colour for a focal bus.
        """
        if voltage < 0.95:
            return QtGui.QColor("#93c5fd")
        elif voltage > 1.05:
            return QtGui.QColor("#fca5a5")
        else:
            return QtGui.QColor("#86efac")

    @staticmethod
    def _get_loading_colour(loading: float) -> QtGui.QColor:
        """Map branch loading to a concise operator colour.

        :param loading: Absolute branch loading in per-unit.
        :return: Pen colour for a direct branch.
        """
        if loading > 1.0:
            return QtGui.QColor("#dc2626")
        elif loading > 0.8:
            return QtGui.QColor("#d97706")
        else:
            return QtGui.QColor("#16a34a")

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """Fit the scene after Qt gives the view a real viewport.

        :param event: Qt visibility event.
        :return: None.
        """
        QtWidgets.QGraphicsView.showEvent(self, event)
        self._fit_scene()

    def _fit_scene(self) -> None:
        """Fit the transient context to the available viewport.

        :return: None.
        """
        scene: QtWidgets.QGraphicsScene | None = self._scene
        if scene is not None and not scene.itemsBoundingRect().isNull():
            self.fitInView(scene.itemsBoundingRect().adjusted(-30.0, -30.0, 30.0, 30.0),
                           QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        else:
            pass

    def prepare_to_delete(self) -> None:
        """Clear Qt graphics ownership before the view is removed.

        :return: None.
        """
        if not self._is_disposed:
            scene: QtWidgets.QGraphicsScene | None = self._scene
            self._is_disposed = True
            self._diagram = None
            self._circuit = None
            self._focal_buses.clear()
            self._visible_buses.clear()
            self._visible_branches.clear()
            self._bus_graphics.clear()
            self._branch_graphics.clear()
            self._multiwinding_graphics.clear()
            self._node_graphics.clear()
            self._branch_endpoint_buses.clear()
            self.setScene(None)
            self._scene = None
            if scene is not None:
                scene.clear()
                scene.deleteLater()
            else:
                pass
        else:
            pass
