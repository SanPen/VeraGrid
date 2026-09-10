# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from functools import partial
from typing import List, Set

from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.Icons import icons_rc
from VeraGrid.Gui.object_proxy_model import ObjectModelFilterProxy


def get_popup_top_left_inside_rect(global_position: QtCore.QPoint,
                                   popup_size: QtCore.QSize,
                                   available_geometry: QtCore.QRect) -> QtCore.QPoint:
    """
    Clamp one popup top-left point so the full popup remains inside one screen rectangle.

    :param global_position: Requested global popup top-left position.
    :param popup_size: Popup size that must fit inside the screen.
    :param available_geometry: Screen available geometry.
    :return: Clamped global popup top-left position.
    """
    max_x: int = max(available_geometry.left(),
                     available_geometry.left() + available_geometry.width() - popup_size.width())
    max_y: int = max(available_geometry.top(),
                     available_geometry.top() + available_geometry.height() - popup_size.height())
    x_pos: int = global_position.x()
    y_pos: int = global_position.y()

    # Shift left when the popup would cross the right screen edge.
    if x_pos > max_x:
        x_pos = max_x
    else:
        pass

    # Shift right when the requested point is outside the left screen edge.
    if x_pos < available_geometry.left():
        x_pos = available_geometry.left()
    else:
        pass

    # Shift up when the popup would cross the bottom screen edge.
    if y_pos > max_y:
        y_pos = max_y
    else:
        pass

    # Shift down when the requested point is outside the top screen edge.
    if y_pos < available_geometry.top():
        y_pos = available_geometry.top()
    else:
        pass

    return QtCore.QPoint(x_pos, y_pos)


def get_popup_available_geometry(global_position: QtCore.QPoint,
                                 widget: QtWidgets.QWidget) -> QtCore.QRect:
    """
    Return the available screen geometry matching one popup position.

    :param global_position: Requested global popup position.
    :param widget: Popup widget used to find a fallback screen.
    :return: Available screen rectangle.
    """
    screen: QtGui.QScreen | None = QtGui.QGuiApplication.screenAt(global_position)

    if screen is None:
        window_handle: QtGui.QWindow | None = widget.windowHandle()
        if window_handle is not None:
            screen = window_handle.screen()
        else:
            pass
    else:
        pass

    if screen is None:
        screen = QtGui.QGuiApplication.primaryScreen()
    else:
        pass

    if screen is not None:
        geometry: QtCore.QRect = screen.availableGeometry()
    else:
        geometry = QtCore.QRect(global_position, widget.size())

    return geometry


def get_popup_size_inside_rect(popup_size: QtCore.QSize,
                               available_geometry: QtCore.QRect) -> QtCore.QSize:
    """
    Limit one popup size to the available screen rectangle.

    :param popup_size: Requested popup size.
    :param available_geometry: Screen available geometry.
    :return: Popup size that can fit inside the screen.
    """
    width: int = min(popup_size.width(), available_geometry.width())
    height: int = min(popup_size.height(), available_geometry.height())
    return QtCore.QSize(width, height)


def make_icon_button(icon_path: str, tooltip: str, parent: QtWidgets.QWidget) -> QtWidgets.QToolButton:
    """
    Create one compact icon-only popup button.

    :param icon_path: Qt resource icon path.
    :param tooltip: Button tooltip.
    :param parent: Parent widget.
    :return: Tool button.
    """
    button: QtWidgets.QToolButton = QtWidgets.QToolButton(parent)
    button.setIcon(QtGui.QIcon(icon_path))
    button.setToolTip(tooltip)
    button.setAutoRaise(True)
    button.setIconSize(QtCore.QSize(18, 18))
    button.setFixedSize(26, 26)
    return button


class PopupResizeGrip(QtWidgets.QWidget):
    """
    Visible bottom-right grip that resizes its top-level popup directly.
    """

    __slots__ = (
        "_resize_from_top",
        "_resize_start_global_pos",
        "_resize_start_local_pos",
        "_resize_start_position",
        "_resize_start_size",
        "_resizing",
    )

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        """
        Constructor.

        :param parent: Parent popup.
        :return: None.
        """
        QtWidgets.QWidget.__init__(self, parent)

        self._resize_from_top: bool = False
        self._resize_start_global_pos: QtCore.QPoint = QtCore.QPoint()
        self._resize_start_local_pos: QtCore.QPoint = QtCore.QPoint()
        self._resize_start_position: QtCore.QPoint = QtCore.QPoint()
        self._resize_start_size: QtCore.QSize = QtCore.QSize()
        self._resizing: bool = False

        self.setFixedSize(18, 18)
        self.setCursor(QtCore.Qt.CursorShape.SizeFDiagCursor)
        self.setToolTip(self.tr("Resize"))

    def set_resize_from_top(self, value: bool) -> None:
        """
        Select whether vertical resizing is anchored from the top edge.

        :param value: True to resize upward from the top edge.
        :return: None.
        """
        self._resize_from_top = value
        if value:
            self.setCursor(QtCore.Qt.CursorShape.SizeBDiagCursor)
        else:
            self.setCursor(QtCore.Qt.CursorShape.SizeFDiagCursor)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        Start resizing the parent popup.

        :param event: Mouse press event.
        :return: None.
        """
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._resizing = True
            self._resize_start_global_pos = event.globalPosition().toPoint()
            self._resize_start_local_pos = event.position().toPoint()
            self._resize_start_position = self.window().pos()
            self._resize_start_size = self.window().size()
            self.grabMouse()
            event.accept()
        else:
            QtWidgets.QWidget.mousePressEvent(self, event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        Resize the parent popup while dragging.

        :param event: Mouse move event.
        :return: None.
        """
        if self._resizing:
            delta: QtCore.QPoint = event.globalPosition().toPoint() - self._resize_start_global_pos
            if delta.x() == 0 and delta.y() == 0:
                delta = event.position().toPoint() - self._resize_start_local_pos
            else:
                pass
            popup: QtWidgets.QWidget = self.window()
            requested_height: int
            requested_width: int = self._resize_start_size.width() + delta.x()
            if self._resize_from_top:
                requested_height = self._resize_start_size.height() - delta.y()
            else:
                requested_height = self._resize_start_size.height() + delta.y()

            requested_size: QtCore.QSize = QtCore.QSize(
                requested_width,
                requested_height,
            )
            minimum_size: QtCore.QSize = popup.minimumSize().expandedTo(popup.minimumSizeHint())
            bounded_size: QtCore.QSize = requested_size.expandedTo(minimum_size).boundedTo(popup.maximumSize())

            if self._resize_from_top:
                y_position: int = self._resize_start_position.y() + self._resize_start_size.height() - bounded_size.height()
                popup.move(self._resize_start_position.x(), y_position)
            else:
                pass

            popup.resize(bounded_size)
            event.accept()
        else:
            QtWidgets.QWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        Finish resizing the parent popup.

        :param event: Mouse release event.
        :return: None.
        """
        if self._resizing:
            self._resizing = False
            self.releaseMouse()
            event.accept()
        else:
            QtWidgets.QWidget.mouseReleaseEvent(self, event)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """
        Paint the diagonal resize mark.

        :param event: Paint event.
        :return: None.
        """
        del event
        painter: QtGui.QPainter = QtGui.QPainter(self)
        pen: QtGui.QPen = QtGui.QPen(QtGui.QColor(120, 120, 120))
        pen.setWidth(1)
        painter.setPen(pen)

        offset: int
        for offset in (4, 8, 12):
            painter.drawLine(self.width() - offset, self.height() - 2, self.width() - 2, self.height() - offset)


def set_clear_action_visibility(action: QtGui.QAction, text: str) -> None:
    """
    Show the clear action only while the line edit has text.

    :param action: Clear action.
    :param text: Current line edit text.
    :return: None.
    """
    action.setVisible(len(text) > 0)


def set_line_edit_clear_action(line_edit: QtWidgets.QLineEdit) -> QtGui.QAction:
    """
    Add the VeraGrid clear action to one line edit.

    :param line_edit: Line edit to clear.
    :return: Clear action.
    """
    action: QtGui.QAction
    for action in line_edit.actions():
        if action.objectName() == "veragrid_clear_line_edit_action":
            action.setVisible(len(line_edit.text()) > 0)
            return action
        else:
            pass

    line_edit.setClearButtonEnabled(False)
    icon_path: str = ":/Icons/icons/line_edit_clear_gray.png"
    clear_action: QtGui.QAction = line_edit.addAction(
        QtGui.QIcon(icon_path),
        QtWidgets.QLineEdit.ActionPosition.TrailingPosition,
    )
    clear_action.setObjectName("veragrid_clear_line_edit_action")
    clear_action.setData(icon_path)
    clear_action.setToolTip(line_edit.tr("Clear"))
    clear_action.setVisible(len(line_edit.text()) > 0)
    clear_action.triggered.connect(line_edit.clear)
    line_edit.textChanged.connect(partial(set_clear_action_visibility, clear_action))
    return clear_action


class ObjectColumnFilterDialog(QtWidgets.QDialog):
    """
    Small Excel-like popup to sort and exact-filter one object table column.
    """

    filters_changed = QtCore.Signal()

    __slots__ = (
        "_proxy_model",
        "_source_column",
        "_table_view",
        "_values",
        "resize_grip",
        "search_line_edit",
        "values_list_widget",
    )

    def __init__(self,
                 proxy_model: ObjectModelFilterProxy,
                 source_column: int,
                 table_view: QtWidgets.QTableView,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """
        Constructor.

        :param proxy_model: Proxy model shown by the object table.
        :param source_column: Column index to filter.
        :param table_view: Object table view.
        :param parent: Parent widget.
        """
        QtWidgets.QDialog.__init__(self, parent)

        self._proxy_model: ObjectModelFilterProxy = proxy_model
        self._source_column: int = source_column
        self._table_view: QtWidgets.QTableView = table_view
        self._values: List[str] = proxy_model.get_column_filter_values(source_column=source_column)

        self.setWindowFlags(QtCore.Qt.WindowType.Popup)
        self.setMinimumSize(360, 280)

        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        filter_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        filter_layout.setSpacing(4)

        self.search_line_edit: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        self.search_line_edit.setPlaceholderText(self.tr("Search"))
        set_line_edit_clear_action(line_edit=self.search_line_edit)
        self.search_line_edit.textChanged.connect(self.set_search_text)
        filter_layout.addWidget(self.search_line_edit, 1)

        sort_ascending_button: QtWidgets.QToolButton = make_icon_button(
            icon_path=":/Icons/icons/up.png",
            tooltip=self.tr("Sort A to Z"),
            parent=self,
        )
        sort_descending_button: QtWidgets.QToolButton = make_icon_button(
            icon_path=":/Icons/icons/down.png",
            tooltip=self.tr("Sort Z to A"),
            parent=self,
        )
        clear_filter_button: QtWidgets.QToolButton = make_icon_button(
            icon_path=":/Icons/icons/table_filter_active.png",
            tooltip=self.tr("Clear filter"),
            parent=self,
        )
        select_all_button: QtWidgets.QToolButton = make_icon_button(
            icon_path=":/Icons/icons/check_all.png",
            tooltip=self.tr("Select all visible"),
            parent=self,
        )
        select_none_button: QtWidgets.QToolButton = make_icon_button(
            icon_path=":/Icons/icons/uncheck_all.png",
            tooltip=self.tr("Select no visible"),
            parent=self,
        )
        apply_button: QtWidgets.QToolButton = make_icon_button(
            icon_path=":/Icons/icons/accept.png",
            tooltip=self.tr("Apply"),
            parent=self,
        )
        cancel_button: QtWidgets.QToolButton = make_icon_button(
            icon_path=":/Icons/icons/delete2.png",
            tooltip=self.tr("Cancel filter"),
            parent=self,
        )

        sort_ascending_button.clicked.connect(self.sort_ascending)
        sort_descending_button.clicked.connect(self.sort_descending)
        clear_filter_button.clicked.connect(self.clear_filter)
        select_all_button.clicked.connect(self.select_all_visible)
        select_none_button.clicked.connect(self.select_no_visible)
        apply_button.clicked.connect(self.apply_filter)
        cancel_button.clicked.connect(self.clear_filter)

        filter_layout.addWidget(sort_ascending_button)
        filter_layout.addWidget(sort_descending_button)
        filter_layout.addWidget(clear_filter_button)
        filter_layout.addWidget(select_all_button)
        filter_layout.addWidget(select_none_button)
        filter_layout.addWidget(apply_button)
        filter_layout.addWidget(cancel_button)
        layout.addLayout(filter_layout)

        self.values_list_widget: QtWidgets.QListWidget = QtWidgets.QListWidget(self)
        self.values_list_widget.setMinimumHeight(220)
        layout.addWidget(self.values_list_widget)

        grip_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        grip_layout.setContentsMargins(0, 0, 0, 0)
        grip_layout.addStretch(1)
        self.resize_grip: PopupResizeGrip = PopupResizeGrip(parent=self)
        grip_layout.addWidget(self.resize_grip)
        layout.addLayout(grip_layout)

        self.fill_values()

    def show_at(self, global_position: QtCore.QPoint) -> None:
        """
        Show the popup at the requested global position.

        :param global_position: Global screen position.
        :return: None.
        """
        available_geometry: QtCore.QRect = get_popup_available_geometry(global_position=global_position, widget=self)
        popup_size: QtCore.QSize = get_popup_size_inside_rect(
            popup_size=self.sizeHint().expandedTo(self.minimumSize()),
            available_geometry=available_geometry,
        )
        self.setMaximumSize(available_geometry.size())
        self.resize(popup_size)
        self.move(get_popup_top_left_inside_rect(
            global_position=global_position,
            popup_size=self.size(),
            available_geometry=available_geometry,
        ))
        self.show()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """
        Keep the popup inside the screen after the user resizes it.

        :param event: Resize event.
        :return: None.
        """
        QtWidgets.QDialog.resizeEvent(self, event)
        available_geometry: QtCore.QRect = get_popup_available_geometry(global_position=self.pos(), widget=self)
        bounded_size: QtCore.QSize = get_popup_size_inside_rect(
            popup_size=self.size(),
            available_geometry=available_geometry,
        )

        if bounded_size != self.size():
            self.resize(bounded_size)
        else:
            pass

        bounded_position: QtCore.QPoint = get_popup_top_left_inside_rect(
            global_position=self.pos(),
            popup_size=bounded_size,
            available_geometry=available_geometry,
        )
        if bounded_position != self.pos():
            self.move(bounded_position)
        else:
            pass

    def fill_values(self) -> None:
        """
        Fill the checkbox list with the column values.

        :return: None.
        """
        active_filter: Set[str] | None = self._proxy_model.get_column_filter(source_column=self._source_column)
        value: str
        for value in self._values:
            item: QtWidgets.QListWidgetItem = QtWidgets.QListWidgetItem(value)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            if active_filter is None or value in active_filter:
                item.setCheckState(QtCore.Qt.CheckState.Checked)
            else:
                item.setCheckState(QtCore.Qt.CheckState.Unchecked)
            self.values_list_widget.addItem(item)

    def set_search_text(self, text: str) -> None:
        """
        Hide checkbox rows that do not match the typed search text.

        :param text: Search text.
        :return: None.
        """
        pattern: str = text.casefold()
        row: int
        for row in range(self.values_list_widget.count()):
            item: QtWidgets.QListWidgetItem = self.values_list_widget.item(row)
            item.setHidden(pattern not in item.text().casefold())

    def select_all_visible(self) -> None:
        """
        Check every currently visible value.

        :return: None.
        """
        self.set_visible_check_state(state=QtCore.Qt.CheckState.Checked)

    def select_no_visible(self) -> None:
        """
        Uncheck every currently visible value.

        :return: None.
        """
        self.set_visible_check_state(state=QtCore.Qt.CheckState.Unchecked)

    def set_visible_check_state(self, state: QtCore.Qt.CheckState) -> None:
        """
        Set the check state for the visible value rows.

        :param state: Check state.
        :return: None.
        """
        row: int
        for row in range(self.values_list_widget.count()):
            item: QtWidgets.QListWidgetItem = self.values_list_widget.item(row)
            if item.isHidden():
                pass
            else:
                item.setCheckState(state)

    def get_checked_values(self) -> Set[str]:
        """
        Return the checked values.

        :return: Checked display values.
        """
        values: Set[str] = set()
        row: int
        for row in range(self.values_list_widget.count()):
            item: QtWidgets.QListWidgetItem = self.values_list_widget.item(row)
            if item.checkState() == QtCore.Qt.CheckState.Checked:
                values.add(item.text())
            else:
                pass
        return values

    def sort_ascending(self) -> None:
        """
        Sort the table by this column ascending.

        :return: None.
        """
        self._proxy_model.sort(self._source_column, QtCore.Qt.SortOrder.AscendingOrder)
        self.filters_changed.emit()
        self.close()

    def sort_descending(self) -> None:
        """
        Sort the table by this column descending.

        :return: None.
        """
        self._proxy_model.sort(self._source_column, QtCore.Qt.SortOrder.DescendingOrder)
        self.filters_changed.emit()
        self.close()

    def clear_filter(self) -> None:
        """
        Clear this column filter.

        :return: None.
        """
        self._proxy_model.clear_column_filter(source_column=self._source_column)
        self.filters_changed.emit()
        self.close()

    def apply_filter(self) -> None:
        """
        Apply the checked exact-value filter.

        :return: None.
        """
        self._proxy_model.set_column_filter(
            source_column=self._source_column,
            accepted_values=self.get_checked_values(),
        )
        self.filters_changed.emit()
        self.close()
