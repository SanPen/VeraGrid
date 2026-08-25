# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Union, List, TYPE_CHECKING, Callable
import VeraGrid.ThirdParty.darkdetect as darkdetect
from PySide6.QtCore import Qt, QPointF, QLineF, QCoreApplication
from PySide6.QtWidgets import (QApplication, QGraphicsLineItem, QGraphicsItem, QGraphicsPolygonItem,
                               QGraphicsItemGroup, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem,
                               QGraphicsPathItem)
from PySide6.QtGui import QColor, QPen, QPolygon, QPolygonF, QPainterPath, QBrush, QPalette
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent
from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGrid.Gui.messages import warning_msg

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget
    from VeraGrid.Gui.Diagrams.MapWidget.grid_map_widget import GridMapWidget

try:
    IS_DARK = darkdetect.theme() == "Dark"
except ImportError:
    IS_DARK = False

CURRENT_THEME_IS_DARK = IS_DARK

TRANSPARENT = QColor(0, 0, 0, 0)
WHITE = QColor(255, 255, 255, 255)
BLACK = QColor(0, 0, 0, 255)
GRAY = QColor(115, 115, 115, 255)
YELLOW = QColor(255, 247, 0, 255)

# Declare colors
ACTIVE = {'style': Qt.PenStyle.SolidLine,
          'color': WHITE if IS_DARK else BLACK,
          'text': WHITE if IS_DARK else BLACK,
          'background': BLACK if IS_DARK else WHITE,
          'fluid': QColor(0, 170, 212, 255)}

DEACTIVATED = {'style': Qt.PenStyle.DashLine, 'color': GRAY}
EMERGENCY = {'style': Qt.PenStyle.SolidLine, 'color': YELLOW}
OTHER = ACTIVE
FONT_SCALE = 1.9


def _is_palette_dark(palette: QPalette) -> bool:
    """
    Determine whether one Qt palette should be treated as dark.

    :param palette: Qt palette to inspect.
    :return: ``True`` when the palette window background is dark.
    """
    window_color: QColor = QColor(palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Window))
    return window_color.lightness() < 128


def set_dark_mode() -> None:
    """
    Set the dark mode
    """
    global CURRENT_THEME_IS_DARK
    CURRENT_THEME_IS_DARK = True
    ACTIVE['color'] = WHITE
    ACTIVE['text'] = WHITE
    ACTIVE['background'] = BLACK


def set_light_mode() -> None:
    """
    Set the light mode
    """
    global CURRENT_THEME_IS_DARK
    CURRENT_THEME_IS_DARK = False
    ACTIVE['color'] = BLACK
    ACTIVE['text'] = BLACK
    ACTIVE['background'] = WHITE


def is_dark_mode() -> bool:
    """

    :return:
    """
    return CURRENT_THEME_IS_DARK


def is_light_mode() -> bool:
    """

    :return:
    """
    if is_dark_mode():
        return False
    else:
        return True


if IS_DARK:
    set_dark_mode()
else:
    set_light_mode()


class GenericDiagramWidget:
    """
    Generic DataBase Widget
    """

    def __init__(self,
                 parent,
                 api_object: ALL_DEV_TYPES,
                 editor: Union[SchematicWidget, GridMapWidget],
                 draw_labels: bool):
        """
        Constructor
        :param parent:
        :param api_object: Any database object
        :param editor: DiagramEditorWidget
        :param draw_labels:
        """

        self._parent = parent

        self._api_object: ALL_DEV_TYPES = api_object

        self._editor: Union[SchematicWidget, GridMapWidget] = editor

        self._draw_labels: bool = draw_labels

        # color
        self.color = ACTIVE['color']
        self.style = ACTIVE['style']

    def tr(self, source_text: str, disambiguation: str | None = None, n: int = -1) -> str:
        """
        Translate one diagram item runtime string.

        :param source_text: Source string to translate.
        :param disambiguation: Optional Qt disambiguation text.
        :param n: Optional plural parameter.
        :return: Translated text.
        """
        class_name: str = self.__class__.__name__
        return QCoreApplication.translate(class_name, source_text, disambiguation, n)

    @property
    def api_object(self) -> ALL_DEV_TYPES:
        """

        :return:
        """
        return self._api_object

    @property
    def draw_labels(self) -> bool:
        """
        draw labels getter
        :return: Bool
        """
        return self._draw_labels

    @draw_labels.setter
    def draw_labels(self, value: bool):
        """
        Draw labels setter, it updates the diagram
        :param value: boolean
        """
        self._draw_labels = value

        # update editor diagram position
        self._editor.update_label_drwaing_status(device=self.api_object, draw_labels=self._draw_labels)

    def recolour_mode(self) -> None:
        """
        Change the colour according to the system theme
        """
        if self.api_object is not None:
            if isinstance(self.api_object, (InjectionParent, BranchParent)):
                if self.api_object.active:
                    self.color = ACTIVE['color']
                    self.style = ACTIVE['style']
                else:
                    self.color = DEACTIVATED['color']
                    self.style = DEACTIVATED['style']
            else:
                self.color = ACTIVE['color']
                self.style = ACTIVE['style']
        else:
            self.color = ACTIVE['color']
            self.style = ACTIVE['style']

    def enable_label_drawing(self):
        """

        :return:
        """
        self.draw_labels = True

    def disable_label_drawing(self):
        """

        :return:
        """
        self.draw_labels = False

    def enable_disable_label_drawing(self):
        """

        :return:
        """
        if self.draw_labels:
            self.disable_label_drawing()
        else:
            self.enable_label_drawing()

    def delete_from_associations(self):
        """
        Delete this object from other associations, i.e. for a line, delete from the terminal connections
        :return:
        """
        pass

    def get_associated_widgets(self) -> List["GenericDiagramWidget"]:
        """
        Get a list of all graphical elements associated with this widget.
        In the case of a BusGraphicsItem, it will be all the shunt connections
        plus the LineGraphicItems connecting to it, etc.
        This function is meant to be overloaded.
        :return:
        """
        return list()

    def get_extra_graphics(self) -> List[QGraphicsItem]:
        """
        Get a list of all QGraphicsItem elements associated with this widget.
        In the case of a GeneratorGraphicsItem, it will be all the nexus
        This function is meant to be overloaded.
        :return:
        """
        return list()

    def get_associated_devices(self):

        """
        Get a list of all graphical elements associated with this widget.
        In the case of a BusGraphicsItem, it will be all the shunt connections
        plus the LineGraphicItems connecting to it, etc.
        This function is meant to be overloaded.
        :return:

        """

        return list()

    def open_device_editor(self) -> bool:
        """
        Open the device editor for this graphic element.

        Subclasses must implement this method to launch the editor that
        corresponds to their own device type.

        :return: ``True`` when an editor was opened.
        """
        warning_msg(
            self.tr("Editor launch is not implemented for {class_name}").format(class_name=self.__class__.__name__),
            self.tr("Device editor"),
        )
        return False


class DraggableLabelItem(QGraphicsTextItem):
    """
    Movable text label that preserves a manual offset from one layout anchor.
    """

    __slots__ = ("_anchor_position", "_offset", "_internal_move", "_moved_callback")

    def __init__(self, parent: QGraphicsItem, moved_callback: Callable[[], None] | None = None) -> None:
        """
        Build one movable label item.

        :param parent: Parent graphics item.
        :param moved_callback: Callback executed after one user move.
        :return: ``None``.
        """
        QGraphicsTextItem.__init__(self, parent)
        self._anchor_position: QPointF = QPointF(0.0, 0.0)
        self._offset: QPointF = QPointF(0.0, 0.0)
        self._internal_move: bool = False
        self._moved_callback: Callable[[], None] | None = moved_callback
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def set_anchor_position(self, anchor_position: QPointF) -> None:
        """
        Update the layout anchor while preserving the manual offset.

        :param anchor_position: Base label anchor.
        :return: ``None``.
        """
        self._anchor_position = QPointF(float(anchor_position.x()), float(anchor_position.y()))
        self._internal_move = True
        self.setPos(self._anchor_position + self._offset)
        self._internal_move = False

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: QPointF | int) -> QPointF | int:
        """
        Track user movement as one offset from the current anchor.

        :param change: Item change kind.
        :param value: Proposed value.
        :return: Value to apply.
        """
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and isinstance(value, QPointF):
            if self._internal_move:
                pass
            else:
                self._offset = QPointF(float(value.x() - self._anchor_position.x()),
                                       float(value.y() - self._anchor_position.y()))
                if self._moved_callback is None:
                    pass
                else:
                    self._moved_callback()
            return value
        else:
            return QGraphicsTextItem.itemChange(self, change, value)


class Polygon(QGraphicsPolygonItem):
    """
    PolygonItem
    """

    def __init__(self, parent, polygon: QPolygon | QPolygonF, update_nexus_fcn: Callable[[QPointF], None]):
        """
        Constructor
        :param parent:
        """
        super().__init__(parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        self.setPolygon(polygon)
        self.update_nexus_fcn = update_nexus_fcn

    def setPen(self, pen: QPen):
        """

        :param pen:
        """
        super().setPen(pen)
        pass

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Union[int, QPointF]) -> Union[int, QPointF]:
        """

        :param change:
        :param value:
        :return:
        """
        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            self.update_nexus_fcn(value)
        return super(QGraphicsPolygonItem, self).itemChange(change, value)


class Square(QGraphicsRectItem):
    """
    Square
    """

    def __init__(self, parent, h: int, w: int, label_letter: str, update_nexus_fcn: Callable[[QPointF], None]):
        """
        Constructor
        :param parent:
        """
        super().__init__(parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        self.setRect(0, 0, h, w)

        self.label = QGraphicsTextItem(label_letter, parent=self)
        self.label.setPos(h / 4, w / 5)
        self.update_nexus_fcn = update_nexus_fcn

    def setPen(self, pen: QPen):
        """

        :param pen:
        """
        super().setPen(pen)
        self.label.setDefaultTextColor(pen.color())

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Union[int, QPointF]) -> Union[int, QPointF]:
        """

        :param change:
        :param value:
        :return:
        """
        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            self.update_nexus_fcn(value)
        return super(QGraphicsRectItem, self).itemChange(change, value)


class Circle(QGraphicsEllipseItem):
    """
    Circle
    """

    def __init__(self, parent, h: int, w: int, label_letter: str, update_nexus_fcn: Callable[[QPointF], None]):
        """
        Constructor
        :param parent:
        """
        super().__init__(parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        self.setRect(0, 0, h, w)

        self.label = QGraphicsTextItem(label_letter, parent=self)
        self.label.setPos(h / 4, w / 5)
        self.update_nexus_fcn = update_nexus_fcn

    def setPen(self, pen: QPen):
        super().setPen(pen)
        self.label.setDefaultTextColor(pen.color())

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Union[int, QPointF]) -> Union[int, QPointF]:
        """

        :param change:
        :param value:
        :return:
        """
        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            self.update_nexus_fcn(value)
        return super(QGraphicsEllipseItem, self).itemChange(change, value)


class Condenser(QGraphicsItemGroup):
    """
    Square
    """

    def __init__(self, parent, h: int, w: int, update_nexus_fcn: Callable[[QPointF], None]):
        """
        Constructor
        :param parent:
        """
        super().__init__(parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        lines_data = list()
        lines_data.append(QLineF(QPointF(w / 2, 0), QPointF(w / 2, h * 0.4)))
        lines_data.append(QLineF(QPointF(0, h * 0.4), QPointF(w, h * 0.4)))
        lines_data.append(QLineF(QPointF(0, h * 0.6), QPointF(w, h * 0.6)))
        lines_data.append(QLineF(QPointF(w / 2, h * 0.6), QPointF(w / 2, h)))
        lines_data.append(QLineF(QPointF(0, h * 1), QPointF(w, h * 1)))
        lines_data.append(QLineF(QPointF(w * 0.15, h * 1.1), QPointF(w * 0.85, h * 1.1)))
        lines_data.append(QLineF(QPointF(w * 0.3, h * 1.2), QPointF(w * 0.7, h * 1.2)))

        self.lines = list()
        for l in lines_data:
            l1 = QGraphicsLineItem(parent)
            l1.setLine(l)
            self.lines.append(l1)
            self.addToGroup(l1)

        self.update_nexus_fcn = update_nexus_fcn

    def setPen(self, pen: QPen):
        for l in self.lines:
            l.setPen(pen)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Union[int, QPointF]) -> Union[int, QPointF]:
        """

        :param change:
        :param value:
        :return:
        """
        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            self.update_nexus_fcn(value)
        return super(QGraphicsItemGroup, self).itemChange(change, value)


class InjectionSymbolBase(QGraphicsItemGroup):
    """
    Shared vector symbol base for injection devices.
    """

    def __init__(self, parent, w: float, h: float) -> None:
        """
        Build one vector injection symbol container.

        :param parent: Parent graphics item.
        :param w: Symbol width.
        :param h: Symbol height.
        :return: ``None``.
        """
        super().__init__(parent)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.w: float = float(w)
        self.h: float = float(h)
        self._stroke_items: list[
            QGraphicsLineItem | QGraphicsRectItem | QGraphicsEllipseItem | QGraphicsPolygonItem | QGraphicsPathItem
        ] = list()
        self._fill_items: list[
            QGraphicsRectItem | QGraphicsEllipseItem | QGraphicsPolygonItem | QGraphicsPathItem
        ] = list()
        self._text_items: list[QGraphicsTextItem] = list()

    def _register_stroke_item(self,
                              item: QGraphicsLineItem | QGraphicsRectItem | QGraphicsEllipseItem
                              | QGraphicsPolygonItem | QGraphicsPathItem | QGraphicsTextItem,
                              fill_item: bool = False,
                              text_item: bool = False) -> QGraphicsLineItem | QGraphicsRectItem \
                                                      | QGraphicsEllipseItem | QGraphicsPolygonItem \
                                                      | QGraphicsPathItem | QGraphicsTextItem:
        """
        Track child items that follow the symbol pen and brush.

        :param item: Registered primitive.
        :param fill_item: Register it for fill updates too.
        :param text_item: Register it as text content.
        :return: The same registered item.
        """
        if isinstance(item, (QGraphicsLineItem,
                             QGraphicsRectItem,
                             QGraphicsEllipseItem,
                             QGraphicsPolygonItem,
                             QGraphicsPathItem)):
            item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            self._stroke_items.append(item)
        else:
            if isinstance(item, QGraphicsTextItem):
                item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            else:
                pass

        if fill_item and isinstance(item, (QGraphicsRectItem,
                                           QGraphicsEllipseItem,
                                           QGraphicsPolygonItem,
                                           QGraphicsPathItem)):
            self._fill_items.append(item)
        else:
            pass

        if text_item and isinstance(item, QGraphicsTextItem):
            self._text_items.append(item)
        else:
            pass

        return item

    def setPen(self, pen: QPen) -> None:
        """
        Apply one pen to every registered vector primitive.

        :param pen: Symbol pen.
        :return: ``None``.
        """
        item: QGraphicsLineItem | QGraphicsRectItem | QGraphicsEllipseItem | QGraphicsPolygonItem | QGraphicsPathItem
        for item in self._stroke_items:
            item.setPen(pen)

        text_item: QGraphicsTextItem
        for text_item in self._text_items:
            text_item.setDefaultTextColor(pen.color())

    def setBrush(self, brush: QBrush | QColor) -> None:
        """
        Apply one fill brush to the symbol body primitives.

        :param brush: Fill brush or color.
        :return: ``None``.
        """
        brush_obj: QBrush = brush if isinstance(brush, QBrush) else QBrush(brush)
        item: QGraphicsRectItem | QGraphicsEllipseItem | QGraphicsPolygonItem | QGraphicsPathItem

        for item in self._fill_items:
            item.setBrush(brush_obj)


class GeneratorSymbol(InjectionSymbolBase):
    """
    Vector generator symbol with a rotor waveform.
    """

    def __init__(self, parent, h: int, w: int) -> None:
        """
        Build one generator symbol.

        :param parent: Parent graphics item.
        :param h: Symbol height.
        :param w: Symbol width.
        :return: ``None``.
        """
        super().__init__(parent=parent, w=w, h=h)

        body = QGraphicsEllipseItem(0, 0, self.w, self.h, parent=self)
        self._register_stroke_item(body, fill_item=True)

        rotor_path = QPainterPath()
        rotor_path.moveTo(self.w * 0.18, self.h * 0.50)
        rotor_path.cubicTo(self.w * 0.28, self.h * 0.24,
                           self.w * 0.42, self.h * 0.24,
                           self.w * 0.50, self.h * 0.50)
        rotor_path.cubicTo(self.w * 0.58, self.h * 0.76,
                           self.w * 0.72, self.h * 0.76,
                           self.w * 0.82, self.h * 0.50)
        rotor = QGraphicsPathItem(rotor_path, parent=self)
        self._register_stroke_item(rotor)


class BatterySymbol(InjectionSymbolBase):
    """
    Vector battery symbol.
    """

    def __init__(self, parent, h: int, w: int) -> None:
        """
        Build one battery symbol.

        :param parent: Parent graphics item.
        :param h: Symbol height.
        :param w: Symbol width.
        :return: ``None``.
        """
        super().__init__(parent=parent, w=w, h=h)

        body_path = QPainterPath()
        body_path.addRoundedRect(self.w * 0.08, self.h * 0.16, self.w * 0.74, self.h * 0.68, 4.0, 4.0)
        body = QGraphicsPathItem(body_path, parent=self)
        self._register_stroke_item(body, fill_item=True)

        terminal = QGraphicsRectItem(self.w * 0.84, self.h * 0.36, self.w * 0.10, self.h * 0.28, parent=self)
        self._register_stroke_item(terminal, fill_item=True)

        plus_h = QGraphicsLineItem(self.w * 0.56, self.h * 0.50, self.w * 0.70, self.h * 0.50, parent=self)
        plus_v = QGraphicsLineItem(self.w * 0.63, self.h * 0.40, self.w * 0.63, self.h * 0.60, parent=self)
        minus_h = QGraphicsLineItem(self.w * 0.22, self.h * 0.50, self.w * 0.38, self.h * 0.50, parent=self)
        self._register_stroke_item(plus_h)
        self._register_stroke_item(plus_v)
        self._register_stroke_item(minus_h)


class StaticGeneratorSymbol(InjectionSymbolBase):
    """
    Vector static generator symbol.
    """

    def __init__(self, parent, h: int, w: int) -> None:
        """
        Build one static generator symbol.

        :param parent: Parent graphics item.
        :param h: Symbol height.
        :param w: Symbol width.
        :return: ``None``.
        """
        super().__init__(parent=parent, w=w, h=h)

        body_points = QPolygonF([
            QPointF(self.w * 0.24, self.h * 0.12),
            QPointF(self.w * 0.76, self.h * 0.12),
            QPointF(self.w * 0.92, self.h * 0.50),
            QPointF(self.w * 0.76, self.h * 0.88),
            QPointF(self.w * 0.24, self.h * 0.88),
            QPointF(self.w * 0.08, self.h * 0.50),
        ])
        body = QGraphicsPolygonItem(body_points, parent=self)
        self._register_stroke_item(body, fill_item=True)

        left_bar = QGraphicsLineItem(self.w * 0.30, self.h * 0.30, self.w * 0.30, self.h * 0.70, parent=self)
        right_bar = QGraphicsLineItem(self.w * 0.42, self.h * 0.30, self.w * 0.42, self.h * 0.70, parent=self)
        arrow_shaft = QGraphicsLineItem(self.w * 0.50, self.h * 0.50, self.w * 0.76, self.h * 0.50, parent=self)
        self._register_stroke_item(left_bar)
        self._register_stroke_item(right_bar)
        self._register_stroke_item(arrow_shaft)

        arrow_head = QPolygonF([
            QPointF(self.w * 0.76, self.h * 0.50),
            QPointF(self.w * 0.62, self.h * 0.40),
            QPointF(self.w * 0.62, self.h * 0.60),
        ])
        arrow_head_item = QGraphicsPolygonItem(arrow_head, parent=self)
        self._register_stroke_item(arrow_head_item, fill_item=True)


class CurrentInjectionSymbol(InjectionSymbolBase):
    """
    Vector current injection symbol.
    """

    def __init__(self, parent, h: int, w: int) -> None:
        """
        Build one current injection symbol.

        :param parent: Parent graphics item.
        :param h: Symbol height.
        :param w: Symbol width.
        :return: ``None``.
        """
        super().__init__(parent=parent, w=w, h=h)

        diamond = QPolygonF([
            QPointF(self.w * 0.50, 0.0),
            QPointF(self.w, self.h * 0.50),
            QPointF(self.w * 0.50, self.h),
            QPointF(0.0, self.h * 0.50),
        ])
        body = QGraphicsPolygonItem(diamond, parent=self)
        self._register_stroke_item(body, fill_item=True)

        arrow = QPainterPath()
        arrow.moveTo(self.w * 0.28, self.h * 0.62)
        arrow.lineTo(self.w * 0.60, self.h * 0.30)
        arrow.lineTo(self.w * 0.60, self.h * 0.44)
        arrow.moveTo(self.w * 0.60, self.h * 0.30)
        arrow.lineTo(self.w * 0.46, self.h * 0.30)
        arrow_path = QGraphicsPathItem(arrow, parent=self)
        self._register_stroke_item(arrow_path)


class ExternalGridSymbol(InjectionSymbolBase):
    """
    Vector external grid symbol.
    """

    def __init__(self, parent, h: int, w: int) -> None:
        """
        Build one external grid symbol.

        :param parent: Parent graphics item.
        :param h: Symbol height.
        :param w: Symbol width.
        :return: ``None``.
        """
        super().__init__(parent=parent, w=w, h=h)

        body_path = QPainterPath()
        body_path.addRoundedRect(self.w * 0.10, self.h * 0.14, self.w * 0.80, self.h * 0.72, 4.0, 4.0)
        body = QGraphicsPathItem(body_path, parent=self)
        self._register_stroke_item(body, fill_item=True)

        top_stub = QGraphicsLineItem(self.w * 0.50, 0.0, self.w * 0.50, self.h * 0.14, parent=self)
        bottom_stub = QGraphicsLineItem(self.w * 0.50, self.h * 0.86, self.w * 0.50, self.h, parent=self)
        self._register_stroke_item(top_stub)
        self._register_stroke_item(bottom_stub)

        grill_positions = [0.26, 0.42, 0.58, 0.74]
        grill_x: float
        for grill_x in grill_positions:
            grill_bar = QGraphicsLineItem(self.w * grill_x, self.h * 0.24,
                                          self.w * grill_x, self.h * 0.76, parent=self)
            self._register_stroke_item(grill_bar)


class ShuntSymbol(InjectionSymbolBase):
    """
    Vector shunt symbol.
    """

    def __init__(self, parent, h: int, w: int) -> None:
        """
        Build one shunt symbol.

        :param parent: Parent graphics item.
        :param h: Symbol height.
        :param w: Symbol width.
        :return: ``None``.
        """
        super().__init__(parent=parent, w=w, h=h)

        line_specs = [
            (self.w * 0.50, 0.0, self.w * 0.50, self.h * 0.22),
            (self.w * 0.24, self.h * 0.26, self.w * 0.76, self.h * 0.26),
            (self.w * 0.24, self.h * 0.44, self.w * 0.76, self.h * 0.44),
            (self.w * 0.50, self.h * 0.44, self.w * 0.50, self.h * 0.70),
            (self.w * 0.18, self.h * 0.76, self.w * 0.82, self.h * 0.76),
            (self.w * 0.28, self.h * 0.88, self.w * 0.72, self.h * 0.88),
            (self.w * 0.38, self.h, self.w * 0.62, self.h),
        ]

        spec: tuple[float, float, float, float]
        for spec in line_specs:
            line = QGraphicsLineItem(*spec, parent=self)
            self._register_stroke_item(line)


class ControllableShuntSymbol(ShuntSymbol):
    """
    Vector controllable shunt symbol with a control arrow.
    """

    def __init__(self, parent, h: int, w: int) -> None:
        """
        Build one controllable shunt symbol.

        :param parent: Parent graphics item.
        :param h: Symbol height.
        :param w: Symbol width.
        :return: ``None``.
        """
        super().__init__(parent=parent, h=h, w=w)

        arrow_line = QGraphicsLineItem(self.w * 0.16, self.h * 0.86, self.w * 0.80, self.h * 0.20, parent=self)
        self._register_stroke_item(arrow_line)

        arrow_head = QPolygonF([
            QPointF(self.w * 0.80, self.h * 0.20),
            QPointF(self.w * 0.62, self.h * 0.22),
            QPointF(self.w * 0.76, self.h * 0.36),
        ])
        head = QGraphicsPolygonItem(arrow_head, parent=self)
        self._register_stroke_item(head, fill_item=True)


class FluidTurbineSymbol(InjectionSymbolBase):
    """
    Vector fluid turbine symbol.
    """

    def __init__(self, parent, h: int, w: int) -> None:
        """
        Build one fluid turbine symbol.

        :param parent: Parent graphics item.
        :param h: Symbol height.
        :param w: Symbol width.
        :return: ``None``.
        """
        super().__init__(parent=parent, w=w, h=h)

        body = QGraphicsEllipseItem(0.0, 0.0, self.w, self.h, parent=self)
        self._register_stroke_item(body, fill_item=True)

        # The runner blades distinguish the turbine from the generic generator circle.
        hub = QGraphicsEllipseItem(self.w * 0.42, self.h * 0.42, self.w * 0.16, self.h * 0.16, parent=self)
        self._register_stroke_item(hub, fill_item=True)

        blade_specs: list[tuple[float, float, float, float]] = [
            (self.w * 0.50, self.h * 0.18, self.w * 0.50, self.h * 0.38),
            (self.w * 0.62, self.h * 0.52, self.w * 0.80, self.h * 0.62),
            (self.w * 0.38, self.h * 0.52, self.w * 0.20, self.h * 0.62),
        ]
        blade_spec: tuple[float, float, float, float]
        for blade_spec in blade_specs:
            blade = QGraphicsLineItem(*blade_spec, parent=self)
            self._register_stroke_item(blade)

        wave = QPainterPath()
        wave.moveTo(self.w * 0.16, self.h * 0.76)
        wave.cubicTo(self.w * 0.28, self.h * 0.66,
                     self.w * 0.40, self.h * 0.86,
                     self.w * 0.52, self.h * 0.76)
        wave.cubicTo(self.w * 0.64, self.h * 0.66,
                     self.w * 0.76, self.h * 0.86,
                     self.w * 0.86, self.h * 0.76)
        wave_item = QGraphicsPathItem(wave, parent=self)
        self._register_stroke_item(wave_item)


class FluidPumpSymbol(InjectionSymbolBase):
    """
    Vector fluid pump symbol.
    """

    def __init__(self, parent, h: int, w: int) -> None:
        """
        Build one fluid pump symbol.

        :param parent: Parent graphics item.
        :param h: Symbol height.
        :param w: Symbol width.
        :return: ``None``.
        """
        super().__init__(parent=parent, w=w, h=h)

        body = QGraphicsEllipseItem(0.0, 0.0, self.w, self.h, parent=self)
        self._register_stroke_item(body, fill_item=True)

        inlet_wave = QPainterPath()
        inlet_wave.moveTo(self.w * 0.12, self.h * 0.66)
        inlet_wave.cubicTo(self.w * 0.22, self.h * 0.56,
                           self.w * 0.32, self.h * 0.76,
                           self.w * 0.42, self.h * 0.66)
        wave_item = QGraphicsPathItem(inlet_wave, parent=self)
        self._register_stroke_item(wave_item)

        shaft = QGraphicsLineItem(self.w * 0.22, self.h * 0.50, self.w * 0.68, self.h * 0.50, parent=self)
        self._register_stroke_item(shaft)

        arrow_head = QPolygonF([
            QPointF(self.w * 0.68, self.h * 0.50),
            QPointF(self.w * 0.50, self.h * 0.38),
            QPointF(self.w * 0.50, self.h * 0.62),
        ])
        arrow = QGraphicsPolygonItem(arrow_head, parent=self)
        self._register_stroke_item(arrow, fill_item=True)

        volute = QPainterPath()
        volute.moveTo(self.w * 0.36, self.h * 0.28)
        volute.cubicTo(self.w * 0.62, self.h * 0.18,
                       self.w * 0.82, self.h * 0.32,
                       self.w * 0.78, self.h * 0.56)
        volute.cubicTo(self.w * 0.74, self.h * 0.76,
                       self.w * 0.54, self.h * 0.84,
                       self.w * 0.38, self.h * 0.72)
        volute_item = QGraphicsPathItem(volute, parent=self)
        self._register_stroke_item(volute_item)


class FluidP2xSymbol(InjectionSymbolBase):
    """
    Vector fluid power-to-X symbol.
    """

    def __init__(self, parent, h: int, w: int) -> None:
        """
        Build one fluid power-to-X symbol.

        :param parent: Parent graphics item.
        :param h: Symbol height.
        :param w: Symbol width.
        :return: ``None``.
        """
        super().__init__(parent=parent, w=w, h=h)

        body_path = QPainterPath()
        body_path.addRoundedRect(self.w * 0.06, self.h * 0.12, self.w * 0.88, self.h * 0.76, 6.0, 6.0)
        body = QGraphicsPathItem(body_path, parent=self)
        self._register_stroke_item(body, fill_item=True)

        bolt = QPolygonF([
            QPointF(self.w * 0.44, self.h * 0.18),
            QPointF(self.w * 0.28, self.h * 0.54),
            QPointF(self.w * 0.46, self.h * 0.54),
            QPointF(self.w * 0.36, self.h * 0.82),
            QPointF(self.w * 0.68, self.h * 0.40),
            QPointF(self.w * 0.50, self.h * 0.40),
        ])
        bolt_item = QGraphicsPolygonItem(bolt, parent=self)
        self._register_stroke_item(bolt_item, fill_item=True)

        outlet_wave = QPainterPath()
        outlet_wave.moveTo(self.w * 0.12, self.h * 0.76)
        outlet_wave.cubicTo(self.w * 0.24, self.h * 0.68,
                            self.w * 0.36, self.h * 0.84,
                            self.w * 0.48, self.h * 0.76)
        outlet_wave.cubicTo(self.w * 0.60, self.h * 0.68,
                            self.w * 0.72, self.h * 0.84,
                            self.w * 0.84, self.h * 0.76)
        wave_item = QGraphicsPathItem(outlet_wave, parent=self)
        self._register_stroke_item(wave_item)


class Line(QGraphicsLineItem):
    """
    Line
    """

    def __init__(self, parent, update_nexus_fcn: Callable[[QPointF], None]):
        """
        Constructor
        :param parent:
        """
        super().__init__(parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        self.update_nexus_fcn = update_nexus_fcn

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Union[int, QPointF]) -> Union[int, QPointF]:
        """

        :param change:
        :param value:
        :return:
        """
        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            self.update_nexus_fcn(value)
        return super(QGraphicsLineItem, self).itemChange(change, value)
