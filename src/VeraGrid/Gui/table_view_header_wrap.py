# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from PySide6 import QtCore, QtWidgets, QtGui
from VeraGrid.Gui.Icons import icons_rc
from VeraGrid.Gui.wrappable_table_model import WrappableTableModel
from VeraGrid.Gui.results_model import ResultsModel
from VeraGrid.Gui.object_proxy_model import ObjectModelFilterProxy


class HeaderViewWithWordWrap(QtWidgets.QHeaderView):
    """
    HeaderViewWithWordWrap
    """

    def __init__(self, parent) -> None:
        """
        THe parent must be passed on
        :param parent:
        """
        super().__init__(QtCore.Qt.Orientation.Horizontal, parent)

        # Get the table view (assumes the header's parent is a QTableView)
        self.tableView: QtWidgets.QTableView = self.parentWidget()

        if isinstance(self.tableView, QtWidgets.QTableView):

            self.setSectionsClickable(True)  # Enable section clickability
            self.setHighlightSections(True)  # Ensure visual feedback when sections are clicked

            # Connect the sectionClicked signal to the select_column method
            self.sectionClicked.connect(self.select_column)
            self.sectionDoubleClicked.connect(self.sort_column)
        else:
            raise Exception("The parent is not a QTableView :(" + str(type(self.tableView)) + ")")

    def _realModel(self) -> WrappableTableModel:
        """
        Return the source model used for header text wrapping.

        :return: Source table model.
        """
        mdl = self.tableView.model()
        if isinstance(mdl, QtCore.QSortFilterProxyModel):
            mdl = mdl.sourceModel()
        else:
            pass
        return mdl

    def _proxy_model(self) -> ObjectModelFilterProxy | None:
        """
        Return the object-table proxy when this header belongs to one.

        :return: Object model proxy or None.
        """
        mdl = self.tableView.model()
        if isinstance(mdl, ObjectModelFilterProxy):
            return mdl
        else:
            return None

    def _header_state_icon_path(self, logicalIndex: int) -> str:
        """
        Return the icon path for the filter-menu state of one column.

        :param logicalIndex: Header section index.
        :return: Qt resource path or empty string.
        """
        icon_path: str = ""
        proxy_model: ObjectModelFilterProxy | None = self._proxy_model()

        if proxy_model is not None:
            if proxy_model.has_column_filter(source_column=logicalIndex):
                icon_path = ":/Icons/icons/table_filter_active.png"
            else:
                sort_order: QtCore.Qt.SortOrder | None = proxy_model.get_column_sort_order(source_column=logicalIndex)
                if sort_order == QtCore.Qt.SortOrder.AscendingOrder:
                    icon_path = ":/Icons/icons/up.png"
                else:
                    if sort_order == QtCore.Qt.SortOrder.DescendingOrder:
                        icon_path = ":/Icons/icons/down.png"
                    else:
                        pass
        else:
            pass

        return icon_path

    def sectionSizeFromContents(self, logicalIndex: int) -> QtCore.QSize:
        """

        :param logicalIndex:
        :return:
        """
        mdl: WrappableTableModel = self._realModel()
        if mdl:
            headerText = mdl.headerData(section=logicalIndex,
                                        orientation=self.orientation(),
                                        role=QtCore.Qt.ItemDataRole.DisplayRole)
            option = QtWidgets.QStyleOptionHeader()
            self.initStyleOption(option)
            option.section = logicalIndex
            metrics = QtGui.QFontMetrics(self.font())

            maxWidth = self.sectionSize(logicalIndex)

            rect = metrics.boundingRect(QtCore.QRect(0, 0, maxWidth, 5000),
                                        QtCore.Qt.AlignmentFlag.AlignLeft |
                                        QtCore.Qt.TextFlag.TextWordWrap |
                                        QtCore.Qt.TextFlag.TextExpandTabs,
                                        headerText, 4)
            return rect.size()
        else:
            return QtWidgets.QHeaderView.sectionSizeFromContents(self, logicalIndex)

    def paintSection(self, painter, rect, logicalIndex: int):
        """

        :param painter:
        :param rect:
        :param logicalIndex:
        :return:
        """
        mdl: WrappableTableModel = self._realModel()  # assign with typing
        if mdl:
            painter.save()
            mdl.hide_headers()
            super().paintSection(painter, rect, logicalIndex)
            mdl.unhide_headers()
            painter.restore()
            headerText = mdl.headerData(logicalIndex, self.orientation(), QtCore.Qt.ItemDataRole.DisplayRole)

            if headerText is not None:
                headerText = headerText.replace("_", " ")

                # Define text indentation
                indentation = 4  # pixels
                icon_size: int = 14
                icon_padding: int = 5
                text_right: int = 0
                icon_path: str = self._header_state_icon_path(logicalIndex=logicalIndex)

                if len(icon_path) > 0:
                    text_right = -(icon_size + icon_padding + 2)
                else:
                    pass

                textRect = QtCore.QRectF(rect.adjusted(indentation, 0, text_right, 0))

                painter.drawText(textRect,
                                 QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.TextFlag.TextWordWrap,
                                 headerText)

                if len(icon_path) > 0:
                    icon: QtGui.QIcon = QtGui.QIcon(icon_path)
                    icon_rect: QtCore.QRect = QtCore.QRect(
                        rect.right() - icon_size - icon_padding,
                        rect.top() + int((rect.height() - icon_size) / 2),
                        icon_size,
                        icon_size,
                    )
                    icon.paint(painter, icon_rect)
                else:
                    pass
        else:
            QtWidgets.QHeaderView.paintSection(self, painter, rect, logicalIndex)

    def select_column(self, logicalIndex: int):
        """
        Select the column corresponding to the clicked header.
        :param logicalIndex: Index of the clicked header section (column)
        """
        # Select the column
        self.tableView.selectColumn(logicalIndex)

    def sort_column(self, i: int):
        """

        :param i:
        :return:
        """
        mdl = self._realModel()  # assign with typing

        if isinstance(mdl, ResultsModel):
            mdl.sort_column(c=i)
            mdl.update()
