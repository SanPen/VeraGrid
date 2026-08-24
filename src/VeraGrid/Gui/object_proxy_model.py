# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from enum import Enum
from typing import Any, Dict, List, Set, Tuple
from PySide6 import QtCore, QtWidgets
import numpy as np
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Utils.Filtering.objects_filtering import FilterObjects
from VeraGrid.Gui.object_model import ObjectsModel


class ObjectModelFilterProxy(QtCore.QSortFilterProxyModel):
    """
    Proxy that delegates the parsing/evaluation of the search expression into an ObjectsModel
    to a `FilterObjects` instance.
    """

    def __init__(self,
                 mdl: ObjectsModel,
                 parent: QtCore.QObject | None = None):
        """
        Constructor
        :param mdl: ObjectsModel
        :param parent: some parent
        """
        super().__init__(parent)

        self._mdl: ObjectsModel = mdl

        # filtering engine already initialized
        self._filter_engine = FilterObjects(self._mdl.objects)

        # indexes allowed after the last call to setExpression()
        self._allowed_rows: set[int] = set(range(len(self._mdl.objects)))

        # Column exact-match filters keyed by source column index.
        self._column_filters: Dict[int, Set[str]] = dict()

        # Active sort state. Qt can sort without filtering rows, but the GUI treats it as filter-menu state.
        self._sort_column: int | None = None
        self._sort_order: QtCore.Qt.SortOrder | None = None

        # set the source model
        super().setSourceModel(mdl)

    @property
    def all_objects(self) -> List[ALL_DEV_TYPES]:
        """
        Return all objects in the underlying source model order.

        :return: Objects in DB/source order.
        """
        return self.get_objects_in_db_order()

    @property
    def objects(self) -> List[ALL_DEV_TYPES]:
        """
        Return objects in the visible proxy order.

        :return: Objects in filtered/sorted display order.
        """
        return self.get_objects_in_display_order()

    def get_objects_in_db_order(self) -> List[ALL_DEV_TYPES]:
        """
        Return all objects in the underlying source model order.

        :return: Objects in DB/source order.
        """
        return self._mdl.objects

    def get_objects_in_display_order(self) -> List[ALL_DEV_TYPES]:
        """
        Return the visible objects in the same order shown by the view.

        :return: Objects in filtered/sorted display order.
        """
        objects: List[ALL_DEV_TYPES] = list()
        row: int
        for row in range(self.rowCount()):
            obj: ALL_DEV_TYPES | None = self.get_object_at_proxy_row(proxy_row=row)
            if obj is not None:
                objects.append(obj)
            else:
                pass
        return objects

    @property
    def attributes(self):
        return self._mdl.attributes

    @QtCore.Slot(str)
    def setExpression(self, expr: str) -> Tuple[bool, str]:
        """
        Call this whenever the user changes the search text.
        """
        has_error = False
        error_txt = ""
        new_allowed_rows: Set[int]
        if not expr.strip():
            # empty => show everything
            new_allowed_rows = set(range(len(self.get_objects_in_db_order())))
        else:
            try:
                self._filter_engine.filter(expr)  # updates .filtered_indices
                new_allowed_rows = set(self._filter_engine.filtered_indices)
            except Exception as e:
                # invalid expression: fall back to show none
                error_txt = f"Filter expression error: {e}"
                new_allowed_rows = set()
                has_error = True

        self.beginFilterChange()
        self._allowed_rows = new_allowed_rows
        self.endFilterChange(QtCore.QSortFilterProxyModel.Direction.Rows)

        return has_error, error_txt

    def source_row(self, proxy_row: int) -> int:
        """
        Convert a visible proxy row into the underlying source row.

        :param proxy_row: Row index in the filtered/sorted proxy.
        :return: Source row index or -1.
        """
        return self.get_source_row_from_proxy_row(proxy_row=proxy_row)

    def get_source_row_from_proxy_row(self, proxy_row: int) -> int:
        """
        Convert a visible proxy row into the underlying source row.

        :param proxy_row: Row index in the filtered/sorted proxy.
        :return: Source row index or -1.
        """
        if proxy_row > -1:
            proxy_index: QtCore.QModelIndex = self.index(proxy_row, 0)
            if proxy_index.isValid():
                return self.mapToSource(proxy_index).row()
            else:
                return -1
        else:
            return -1

    def object_at(self, proxy_row: int) -> ALL_DEV_TYPES | None:
        """
        Return the object shown at one visible proxy row.

        :param proxy_row: Row index in the filtered/sorted proxy.
        :return: Object or None.
        """
        return self.get_object_at_proxy_row(proxy_row=proxy_row)

    def get_object_at_proxy_row(self, proxy_row: int) -> ALL_DEV_TYPES | None:
        """
        Return the object shown at one visible proxy row.

        :param proxy_row: Row index in the filtered/sorted proxy.
        :return: Object or None.
        """
        source_row: int = self.get_source_row_from_proxy_row(proxy_row=proxy_row)
        if 0 <= source_row < len(self._mdl.objects):
            return self._mdl.objects[source_row]
        else:
            return None

    def objects_at_proxy_rows(self, proxy_rows: List[int]) -> List[ALL_DEV_TYPES]:
        """
        Return objects shown at the requested visible proxy rows.

        :param proxy_rows: Row indexes in the filtered/sorted proxy.
        :return: Objects in the requested row order.
        """
        return self.get_objects_at_proxy_rows(proxy_rows=proxy_rows)

    def get_objects_at_proxy_rows(self, proxy_rows: List[int]) -> List[ALL_DEV_TYPES]:
        """
        Return objects shown at the requested visible proxy rows.

        :param proxy_rows: Row indexes in the filtered/sorted proxy.
        :return: Objects in the requested row order.
        """
        objects: List[ALL_DEV_TYPES] = list()
        proxy_row: int
        for proxy_row in proxy_rows:
            obj: ALL_DEV_TYPES | None = self.get_object_at_proxy_row(proxy_row=proxy_row)
            if obj is not None:
                objects.append(obj)
            else:
                pass
        return objects

    def get_cell_text(self, source_row: int, source_column: int) -> str:
        """
        Return the displayed text for one source cell.

        :param source_row: Row index in the source model.
        :param source_column: Column index in the source model.
        :return: Display text used by exact column filters.
        """
        if source_row > -1 and source_column > -1:
            index: QtCore.QModelIndex = self._mdl.index(source_row, source_column)
            value: Any = self._mdl.data(index=index, role=QtCore.Qt.ItemDataRole.DisplayRole)
            if value is None:
                return ""
            else:
                return str(value)
        else:
            return ""

    def get_column_filter_values(self, source_column: int) -> List[str]:
        """
        Return the values available for one column under the other active filters.

        :param source_column: Source column index.
        :return: Sorted distinct display values.
        """
        values: Set[str] = set()
        source_row: int
        for source_row in range(self._mdl.rowCount()):
            if self._source_row_accepted(source_row=source_row, ignored_column=source_column):
                values.add(self.get_cell_text(source_row=source_row, source_column=source_column))
            else:
                pass

        return sorted(values)

    def get_column_filter(self, source_column: int) -> Set[str] | None:
        """
        Return the active exact-value filter for one column.

        :param source_column: Source column index.
        :return: Accepted display values, or None when the column is not filtered.
        """
        return self._column_filters.get(source_column, None)

    def set_column_filter(self, source_column: int, accepted_values: Set[str]) -> None:
        """
        Set the accepted exact display values for one column.

        :param source_column: Source column index.
        :param accepted_values: Accepted display values.
        :return: None.
        """
        all_values: Set[str] = set(self.get_column_filter_values(source_column=source_column))
        new_values: Set[str] = set(accepted_values)

        self.beginFilterChange()
        if new_values == all_values:
            if source_column in self._column_filters:
                self._column_filters.pop(source_column)
            else:
                pass
        else:
            self._column_filters[source_column] = new_values
        self.endFilterChange(QtCore.QSortFilterProxyModel.Direction.Rows)

    def clear_column_filter(self, source_column: int) -> None:
        """
        Remove the exact-value filter and sort state from one column.

        :param source_column: Source column index.
        :return: None.
        """
        self.beginFilterChange()
        if source_column in self._column_filters:
            self._column_filters.pop(source_column)
        else:
            pass
        self.endFilterChange(QtCore.QSortFilterProxyModel.Direction.Rows)

        if self.has_column_sort(source_column=source_column):
            self.clear_column_sort()
        else:
            pass

    def clear_all_column_filters(self) -> None:
        """
        Remove all exact-value column filters and sort state.

        :return: None.
        """
        self.beginFilterChange()
        self._column_filters = dict()
        self.endFilterChange(QtCore.QSortFilterProxyModel.Direction.Rows)
        self.clear_column_sort()

    def has_column_filter(self, source_column: int) -> bool:
        """
        Check if one column has an active exact-value filter.

        :param source_column: Source column index.
        :return: True when the column is filtered.
        """
        return source_column in self._column_filters

    def has_column_sort(self, source_column: int) -> bool:
        """
        Check if one column has the active sort state.

        :param source_column: Source column index.
        :return: True when the column is sorted.
        """
        return self._sort_column == source_column

    def get_column_sort_order(self, source_column: int) -> QtCore.Qt.SortOrder | None:
        """
        Return the active sort order for one column.

        :param source_column: Source column index.
        :return: Sort order, or None when the column is not sorted.
        """
        if self._sort_column == source_column:
            return self._sort_order
        else:
            return None

    def clear_column_sort(self) -> None:
        """
        Clear the active sort state and restore source order.

        :return: None.
        """
        self._sort_column = None
        self._sort_order = None
        QtCore.QSortFilterProxyModel.sort(self, -1, QtCore.Qt.SortOrder.AscendingOrder)

    def _source_row_accepted(self, source_row: int, ignored_column: int | None = None) -> bool:
        """
        Check one source row against the smart filter and exact column filters.

        :param source_row: Source row index.
        :param ignored_column: Column whose filter is ignored while listing its values.
        :return: True when the source row is accepted.
        """
        if source_row in self._allowed_rows:
            accepted: bool = True
            source_column: int
            values: Set[str]
            for source_column, values in self._column_filters.items():
                if ignored_column is not None and source_column == ignored_column:
                    pass
                else:
                    cell_text: str = self.get_cell_text(source_row=source_row, source_column=source_column)
                    if cell_text in values:
                        pass
                    else:
                        accepted = False
            return accepted
        else:
            return False

    # ------------------------------------------------------------------  QSortFilterProxyModel
    def filterAcceptsRow(self, source_row: int,
                         source_parent: QtCore.QModelIndex) -> bool:
        """
        Called by Qt for every row that might be shown.
        """
        return self._source_row_accepted(source_row=source_row)

    def lessThan(self, left: QtCore.QModelIndex, right: QtCore.QModelIndex) -> bool:
        """
        Compare source model values for sorting.

        :param left: Left source index.
        :param right: Right source index.
        :return: True when left sorts before right.
        """
        left_value: Any = self._mdl.data(index=left, role=QtCore.Qt.ItemDataRole.EditRole)
        right_value: Any = self._mdl.data(index=right, role=QtCore.Qt.ItemDataRole.EditRole)
        left_key: Any = self._get_sort_key(value=left_value)
        right_key: Any = self._get_sort_key(value=right_value)

        if isinstance(left_key, float) and isinstance(right_key, float):
            return left_key < right_key
        else:
            return str(left_key).casefold() < str(right_key).casefold()

    def _get_sort_key(self, value: Any) -> Any:
        """
        Normalize one model value into a comparable sort key.

        :param value: Source model value.
        :return: Numeric key when possible, otherwise display text.
        """
        if value is None:
            return ""
        else:
            if isinstance(value, bool):
                return str(value)
            else:
                if isinstance(value, (int, float)):
                    return float(value)
                else:
                    if isinstance(value, Enum):
                        return str(value)
                    else:
                        return value

    def sort(self,
             column: int,
             order: QtCore.Qt.SortOrder = QtCore.Qt.SortOrder.AscendingOrder) -> None:
        """
        Sort the proxy and track sorting as filter-menu state.

        :param column: Source column index, or -1 to clear sorting.
        :param order: Sort order.
        :return: None.
        """
        if column > -1:
            self._sort_column = column
            self._sort_order = order
        else:
            self._sort_column = None
            self._sort_order = None

        QtCore.QSortFilterProxyModel.sort(self, column, order)

    def get_data(self):
        """

        :return:
        """

        n_rows = self.rowCount()
        n_cols = self.columnCount()
        data = np.empty((n_rows, n_cols), dtype=object)

        proxy_row: int
        source_row: int
        for proxy_row in range(n_rows):
            source_row = self.get_source_row_from_proxy_row(proxy_row=proxy_row)
            if source_row > -1:
                for j in range(n_cols):
                    data[proxy_row, j] = self._mdl.data_raw(r=source_row, c=j)
            else:
                pass

        columns = [self._mdl.headerData(section=i, orientation=QtCore.Qt.Orientation.Horizontal,
                                        role=QtCore.Qt.ItemDataRole.DisplayRole) for i in range(n_cols)]

        index = [self._mdl.headerData(section=self.get_source_row_from_proxy_row(proxy_row=i),
                                      orientation=QtCore.Qt.Orientation.Vertical,
                                      role=QtCore.Qt.ItemDataRole.DisplayRole) for i in range(n_rows)]

        return index, columns, data

    def copy_to_column(self, index: QtCore.QModelIndex):
        """
        Copy the value pointed by the index to all the other cells in the column
        :param index: QModelIndex instance
        """
        col = index.column()
        row = index.row()
        if row > -1 and col > -1:
            if self._mdl.transposed:
                attr_name = self._mdl.attributes[row]
                sel = self.get_object_at_proxy_row(proxy_row=col)
            else:
                attr_name = self._mdl.attributes[col]
                sel = self.get_object_at_proxy_row(proxy_row=row)

            if sel is not None:
                value = getattr(sel, attr_name)
                for elm in self.objects:
                    if elm != sel:
                        if attr_name not in self._mdl.non_editable_attributes:
                            setattr(elm, attr_name, value)
                        else:
                            pass  # the column cannot be edited
            else:
                pass

    def copy_to_clipboard(self):
        """
        Copy proxy view to clipboard
        :return:
        """
        if self.columnCount() > 0:

            index, columns, data = self.get_data()

            data = data.astype(str)

            # header first
            txt = '\t' + '\t'.join(columns) + '\n'

            # data
            for t, index_value in enumerate(index):
                txt += str(index_value) + '\t' + '\t'.join(data[t, :]) + '\n'

            # copy to clipboard
            cb = QtWidgets.QApplication.clipboard()
            cb.clear()
            cb.setText(txt)

    def set_time_index(self, time_index: int | None):
        """
        Set the time index of the table
        :param time_index: None or integer value
        """
        self._mdl.time_index_ = time_index
        row_count: int = self.rowCount()
        col_count: int = self.columnCount()

        if row_count > 0 and col_count > 0:
            top_left: QtCore.QModelIndex = self.index(0, 0)
            bottom_right: QtCore.QModelIndex = self.index(row_count - 1, col_count - 1)
            self.dataChanged.emit(
                top_left,
                bottom_right,
                [QtCore.Qt.ItemDataRole.DisplayRole, QtCore.Qt.ItemDataRole.EditRole],
            )
        else:
            pass
