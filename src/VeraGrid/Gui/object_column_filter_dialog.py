# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from functools import partial
from typing import List, Set

from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.Icons import icons_rc
from VeraGrid.Gui.object_proxy_model import ObjectModelFilterProxy


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
        self.setMinimumWidth(360)

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

        self.fill_values()

    def show_at(self, global_position: QtCore.QPoint) -> None:
        """
        Show the popup at the requested global position.

        :param global_position: Global screen position.
        :return: None.
        """
        self.move(global_position)
        self.show()

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
