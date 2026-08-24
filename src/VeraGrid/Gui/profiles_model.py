# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import numpy as np
import pandas as pd
from enum import Enum
from typing import Any, Dict, List, Union
from PySide6 import QtCore, QtWidgets
from warnings import warn

from VeraGridEngine.Devices.Parents.editable_device import EditableDevice
from VeraGridEngine.Devices.Profiles.profile_device import ProfileDevice
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.enumerations import DeviceType
from VeraGrid.Gui.gui_functions import (ComboDelegate, TextDelegate, FloatDelegate, ComplexDelegate)
from VeraGrid.Gui.wrappable_table_model import WrappableTableModel


class ObjectHistory:
    """
    ObjectHistory
    """

    def __init__(self, max_undo_states: int = 100) -> None:
        """
        Constructor
        :param max_undo_states: maximum number of undo states
        """
        self.max_undo_states = max_undo_states
        self.position = 0
        self.undo_stack = list()
        self.redo_stack = list()

    def add_state(self, action_name, data: dict):
        """
        Add an undo state
        :param action_name: name of the action that was performed
        :param data: dictionary {column index -> profile array}
        """

        # if the stack is too long delete_with_dialogue the oldest entry
        if len(self.undo_stack) > (self.max_undo_states + 1):
            self.undo_stack.pop(0)

        # stack the newest entry
        self.undo_stack.append((action_name, data))

        self.position = len(self.undo_stack) - 1

        # print('Stored', action_name)

    def redo(self):
        """
        Re-do table
        :return: table instance
        """
        val = self.redo_stack.pop()
        self.undo_stack.append(val)
        return val

    def undo(self):
        """
        Un-do table
        :return: table instance
        """
        val = self.undo_stack.pop()
        self.redo_stack.append(val)
        return val

    def can_redo(self):
        """
        is it possible to redo?
        :return: True / False
        """
        return len(self.redo_stack) > 0

    def can_undo(self):
        """
        Is it possible to undo?
        :return: True / False
        """
        return len(self.undo_stack) > 0


class ProfilesModel(WrappableTableModel):
    """
    Class to populate a Qt table view with profiles from objects
    """

    def __init__(self,
                 time_array: pd.DatetimeIndex,
                 elements: List[EditableDevice],
                 device_type: DeviceType,
                 magnitude: str,
                 data_format,
                 dictionary_of_lists: Dict[Any, List[ALL_DEV_TYPES]] | None,
                 parent,
                 max_undo_states=100):
        """

        :param time_array: array of time
        :param device_type: string with Load, StaticGenerator, etc...
        :param magnitude: magnitude to display 'S', 'P', etc...
        :param data_format:
        :param parent: Parent object: the QTableView object
        :param max_undo_states:
        """
        WrappableTableModel.__init__(self, parent)

        self.parent = parent

        self.data_format = data_format

        self.time_array = time_array

        self.device_type = device_type

        self.magnitude = magnitude

        self.dictionary_of_lists: Dict[Any, List[ALL_DEV_TYPES]] = dictionary_of_lists if dictionary_of_lists is not None else dict()

        self.non_editable_indices = list()

        self.editable = True

        self.elements = elements

        self.formatter = lambda x: "%.2f" % x

        # contains copies of the table
        self.history = ObjectHistory(max_undo_states)

        # add the initial state
        # self.add_state(columns=range(self.columnCount()), action_name='initial')

        self.set_delegates()

    def set_delegates(self) -> None:
        """
        Set the cell editor types depending on the attribute_types array
        :return:
        """
        profile: object | None = self._get_reference_profile()

        if isinstance(profile, ProfileDevice):
            delegate_objects: List[ALL_DEV_TYPES] | None = self.dictionary_of_lists.get(profile.dtype, None)

            if delegate_objects is not None:
                delegate = ComboDelegate(
                    parent=self.parent,
                    objects=[None] + delegate_objects,
                    object_names=["None"] + [x.name for x in delegate_objects],
                )
                self.parent.setItemDelegate(delegate)
            else:
                self.parent.setItemDelegate(None)

        elif self.data_format is bool:
            delegate = ComboDelegate(self.parent, [True, False], ['True', 'False'])
            self.parent.setItemDelegate(delegate)

        elif isinstance(self.data_format, type) and issubclass(self.data_format, Enum):
            # Have a dropdown for enum magnitudes like control modes
            members = list(self.data_format)
            delegate = ComboDelegate(self.parent, members, [str(m) for m in members])
            self.parent.setItemDelegate(delegate)

        elif self.data_format is float:
            delegate = FloatDelegate(self.parent)
            self.parent.setItemDelegate(delegate)

        elif self.data_format is str:
            delegate = TextDelegate(self.parent)
            self.parent.setItemDelegate(delegate)

        elif self.data_format is complex:
            delegate = ComplexDelegate(self.parent)
            self.parent.setItemDelegate(delegate)

        else:
            self.parent.setItemDelegate(None)

    def _get_reference_profile(self) -> object | None:
        """
        Return one representative profile for the current magnitude.

        :return: Profile instance when available.
        """
        if len(self.elements) > 0:
            return self.elements[0].get_profile(magnitude=self.magnitude)
        else:
            return None

    def update(self):
        """
        update
        """
        # row = self.rowCount()
        # self.beginInsertRows(QtCore.QModelIndex(), row, row)
        # # whatever code
        # self.endInsertRows()

        self.layoutAboutToBeChanged.emit()

        self.layoutChanged.emit()

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        """
        Get the display mode
        :param index:
        :return:
        """

        if self.editable and index.column() not in self.non_editable_indices:
            return QtCore.Qt.ItemFlag.ItemIsEditable | QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable
        else:
            return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable

    def rowCount(self, parent: QtCore.QModelIndex = None) -> int:
        """
        Get number of rows
        :param parent:
        :return:
        """
        return len(self.time_array)

    def columnCount(self, parent: Union[None, QtCore.QModelIndex] = None) -> int:
        """
        Get number of columns
        :param parent:
        :return:
        """
        return len(self.elements)

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> Union[str, None]:
        """
        Get the data to display
        :param index:
        :param role:
        :return:
        """
        if index.isValid():
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                c = index.column()
                r = index.row()
                profile_attr_name = self.elements[c].properties_with_profile[self.magnitude]
                profile = getattr(self.elements[c], profile_attr_name)
                return str(profile[r])

        return None

    def setData(self,
                index: QtCore.QModelIndex,
                value: float,
                role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.DisplayRole) -> bool:
        """
        Set data by simple editor (whatever text)
        :param index:
        :param value:
        :param role:
        :return:
        """
        c = index.column()
        if c not in self.non_editable_indices:
            r = index.row()
            profile_attr_name = self.elements[index.column()].properties_with_profile[self.magnitude]
            profile = getattr(self.elements[index.column()], profile_attr_name)
            profile[r] = value

            # self.add_state(columns=[c], action_name='')
        else:
            pass  # the column cannot be edited

        return True

    def headerData(self,
                   section: int,
                   orientation: QtCore.Qt.Orientation,
                   role=QtCore.Qt.ItemDataRole.DisplayRole):
        """
        Get the headers to display
        :param section:
        :param orientation:
        :param role:
        :return:
        """

        if self._hide_headers_mode is True:
            return None

        if role == QtCore.Qt.ItemDataRole.DisplayRole:

            if orientation == QtCore.Qt.Orientation.Horizontal:
                if section < len(self.elements):
                    return str(self.elements[section].name)
            elif orientation == QtCore.Qt.Orientation.Vertical:
                if self.time_array is None:
                    return str(section)
                else:
                    return pd.to_datetime(self.time_array[section]).strftime('%d-%m-%Y %H:%M:%S')

        return None

    def paste_from_clipboard(self,
                             row_idx: int = 0,
                             col_idx: int = 0,
                             selected_rows: Union[None, List[int]] = None,
                             selected_cols: Union[None, List[int]] = None) -> None:
        """
        Paste clipboard data into the profile table.

        :param row_idx: Row where the paste starts.
        :param col_idx: Column where the paste starts.
        :param selected_rows: Selected rows used for single-cell fill.
        :param selected_cols: Selected columns used for single-cell fill.
        :return: None.
        """
        n = len(self.elements)
        nt = len(self.time_array)

        if n > 0:
            formatter = self.elements[0].registered_properties[self.magnitude].tpe

            # copy to clipboard
            cb = QtWidgets.QApplication.clipboard()
            text = cb.text()

            rows = [line for line in text.splitlines() if len(line) > 0]
            parsed_rows: List[List[str]] = list()
            row: str

            for row in rows:
                parsed_rows.append(row.split('\t'))

            if len(parsed_rows) == 0:
                return
            else:
                pass

            mod_cols: List[int] = list()

            if (len(parsed_rows) == 1 and len(parsed_rows[0]) == 1 and
                    selected_rows is not None and selected_cols is not None and
                    len(selected_rows) * len(selected_cols) > 1):
                try:
                    val2 = formatter(parsed_rows[0][0])
                    parsed = True
                except ValueError:
                    warn("could not parse '" + str(parsed_rows[0][0]) + "'")
                    parsed = False
                    val2 = ''

                if parsed:
                    selected_row: int
                    selected_col: int
                    for selected_col in selected_cols:
                        if selected_col < n:
                            prof = self.elements[selected_col].get_profile(magnitude=self.magnitude)
                            arr = prof.toarray()
                            for selected_row in selected_rows:
                                if selected_row < nt:
                                    mod_cols.append(selected_col)
                                    arr[selected_row] = val2
                                else:
                                    print('Out of profile bounds')
                            prof.set(arr)
                        else:
                            print('Out of profile bounds')
                else:
                    pass

                return
            else:
                pass

            # gather values
            values: List[str]
            val: str
            for r, values in enumerate(parsed_rows):

                r2 = r + row_idx
                for c, val in enumerate(values):

                    c2 = c + col_idx

                    try:
                        val2 = formatter(val)
                        parsed = True
                    except ValueError:
                        warn("could not parse '" + str(val) + "'")
                        parsed = False
                        val2 = ''

                    if parsed:
                        if c2 < n and r2 < nt:
                            mod_cols.append(c2)
                            prof = self.elements[c2].get_profile(magnitude=self.magnitude)
                            arr = prof.toarray()
                            arr[r2] = val2
                            prof.set(arr)
                        else:
                            print('Out of profile bounds')

        else:
            # there are no elements
            pass

    def copy_to_clipboard(self,
                          cols: Union[None, List[int]] = None,
                          rows: Union[None, List[int]] = None,
                          include_headers: bool = True) -> bool:
        """
        Copy profiles to clipboard
        :param cols: Columns to copy.
        :param rows: Rows to copy.
        :param include_headers: Include table headers and time index.
        :return:
        """

        if cols is None:
            col_indices: List[int] = list(range(len(self.elements)))
        else:
            if len(cols) > 0:
                col_indices = cols
            else:
                col_indices = list(range(len(self.elements)))

        if rows is None:
            row_indices: List[int] = list(range(len(self.time_array)))
        else:
            if len(rows) > 0:
                row_indices = rows
            else:
                row_indices = list(range(len(self.time_array)))

        n = len(col_indices)

        if n > 0:

            nt = len(row_indices)

            # gather values
            names = np.empty(n, dtype=object)
            values = np.empty((nt, n), dtype=object)

            c: int
            column_index: int
            row_position: int
            row_index: int
            for c, column_index in enumerate(col_indices):
                names[c] = self.elements[column_index].name
                prof = self.elements[column_index].get_profile(self.magnitude)
                arr = prof.toarray().astype(str)
                for row_position, row_index in enumerate(row_indices):
                    values[row_position, c] = arr[row_index]

            # header first
            if include_headers:
                data = '\t' + '\t'.join(names) + '\n'
            else:
                data = ''

            # data
            for t, row_index in enumerate(row_indices):
                if include_headers:
                    data += str(self.time_array[row_index]) + '\t' + '\t'.join(values[t, :]) + '\n'
                else:
                    data += '\t'.join(values[t, :]) + '\n'

            # copy to clipboard
            cb = QtWidgets.QApplication.clipboard()
            cb.clear()
            cb.setText(data)

            return True
        else:
            # there are no elements
            return False

    def add_state(self, columns: List[int], action_name: str = ''):
        """
        Compile data of an action and store the data in the undo history
        :param columns: list of column indices changed
        :param action_name: name of the action
        :return: None
        """
        data = dict()

        for col in columns:
            # profile_property = self.elements[col].properties_with_profile[self.magnitude]
            # data[col] = getattr(self.elements[col], profile_property).copy()
            data[col] = self.elements[col].get_profile(self.magnitude)
            # TODO: check if devices do not have a profile

        self.history.add_state(action_name, data)

    def restore(self, data: dict):
        """
        Set profiles data from undo history
        :param data: dictionary comming from the history
        :return:
        """
        for col, array in data.items():
            profile_property = self.elements[col].properties_with_profile[self.magnitude]
            setattr(self.elements[col], profile_property, array)

    def undo(self):
        """
        Un-do table changes
        """
        if self.history.can_undo():
            action, data = self.history.undo()

            self.restore(data)

            print('Undo ', action)

            self.update()

    def redo(self):
        """
        Re-do table changes
        """
        if self.history.can_redo():
            action, data = self.history.redo()

            self.restore(data)

            print('Redo ', action)

            self.update()
