# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
#
import datetime
import math

import numpy as np
from typing import Any, Dict, List, Union, get_origin
from collections.abc import Sequence
from PySide6 import QtCore, QtWidgets, QtGui
from typing import Callable
from VeraGrid.Gui.gui_functions import (IntDelegate, ComboDelegate, TextDelegate, FloatDelegate,
                                        ComplexDelegate, SequenceDelegate, ZmatrixDelegate, WindingTypeDelegate)
from VeraGrid.Gui.wrappable_table_model import WrappableTableModel
from VeraGridEngine.Templates.template_definition import TemplateProp, TEMPLATEPROP_TYPES
from VeraGridEngine.enumerations import WindingType, V_I_CurveSequenceType, WaveformSequenceType, X_Y_SequenceType, X_Y_Z_Matrix


class DialogInpModel(WrappableTableModel):
    """
    Model to populate a Qt table view for editing TemplateProp values.
    """

    def __init__(self,
                 property_list: List[TemplateProp],
                 parent: QtWidgets.QTableView = None,
                 editable=False,
                 transposed=False,
                 error_msg_ptr: Callable[[str], None] = None):
        """

        :param objects: list of objects associated to the editor (reserved for future use)
        :param property_list: List of TemplateProp to edit
        :param parent: Parent QTableView object
        :param editable: Is the table editable?
        :param transposed: Display the table transposed?
        :param dictionary_of_lists: dictionary of lists for the Delegates
        :param error_msg_ptr: Error message pointer
        """
        WrappableTableModel.__init__(self, parent)

        self.parent = parent
        self.editable = editable
        self.transposed = transposed
        self.error_msg_ptr: Callable[[str], None] | None = error_msg_ptr

        self.property_list: List[TemplateProp] = list()
        self.attributes: List[str] = list()
        self.attribute_types: List[TEMPLATEPROP_TYPES] = list()
        self.units: List[str] = list()
        self.tips: List[str] = list()
        self.non_editable_attributes: List[str] = list()

        for p in property_list:
            if p.display:
                self.property_list.append(p)
                self.attributes.append(p.name)
                self.attribute_types.append(p.tpe)
                self.units.append(p.units)
                self.tips.append(p.descr)
                if not p.editable:
                    self.non_editable_attributes.append(p.name)

        self.c = len(self.attributes)
        self.formatter = lambda x: "%.2f" % x
        self.set_delegates()

    def report_error(self, msg: str):
        if self.error_msg_ptr is not None:
            self.error_msg_ptr(msg)
        else:
            print(msg)

    def set_delegates(self) -> None:
        if self.transposed:
            F = self.parent.setItemDelegateForRow
        else:
            F = self.parent.setItemDelegateForColumn

        for i in range(self.c):

            tpe = self.attribute_types[i]
            origin = get_origin(tpe)

            if tpe is bool:
                delegate = ComboDelegate(self.parent, [True, False], ['True', 'False'])
                F(i, delegate)
            elif tpe is str:
                delegate = TextDelegate(self.parent)
                F(i, delegate)
            elif tpe is float:
                delegate = FloatDelegate(self.parent)
                F(i, delegate)
            elif tpe is int:
                delegate = IntDelegate(self.parent)
                F(i, delegate)
            elif tpe is complex:
                delegate = ComplexDelegate(self.parent)
                F(i, delegate)

            elif tpe is WindingType:
                delegate = WindingTypeDelegate(self.parent)
                F(i, delegate)

            elif tpe is V_I_CurveSequenceType:
                delegate = SequenceDelegate(self.parent, V_I_CurveSequenceType)
                F(i, delegate)

            elif tpe is WaveformSequenceType:
                delegate = SequenceDelegate(self.parent, WaveformSequenceType)
                F(i, delegate)

            elif tpe is X_Y_SequenceType:
                delegate = SequenceDelegate(self.parent, X_Y_SequenceType)
                F(i, delegate)

            elif tpe is X_Y_Z_Matrix:
                delegate = ZmatrixDelegate(self.parent)
                F(i, delegate)

            elif tpe is None:
                F(i, None)
                if len(self.non_editable_attributes) == 0:
                    self.non_editable_attributes.append(self.attributes[i])
            else:
                F(i, None)

    def update(self):
        self.layoutAboutToBeChanged.emit()
        self.layoutChanged.emit()

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        if self.transposed:
            attr_idx = index.row()
        else:
            attr_idx = index.column()

        if self.editable and self.attributes[attr_idx] not in self.non_editable_attributes:
            return QtCore.Qt.ItemFlag.ItemIsEditable | QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable
        else:
            return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable

    def rowCount(self, parent: QtCore.QModelIndex = None) -> int:
        if self.transposed:
            return self.c
        else:
            return 1

    def columnCount(self, parent: QtCore.QModelIndex = None) -> int:
        if self.transposed:
            return 1
        else:
            return self.c

    @staticmethod
    def _format_date_display(value) -> str:
        if value in ("", None):
            return ""

        if isinstance(value, datetime.datetime):
            return value.strftime("%Y/%m/%d")

        if isinstance(value, (np.integer, int)):
            epoch_seconds = int(value)
        elif isinstance(value, (np.floating, float)):
            numeric_value = float(value)
            if not math.isfinite(numeric_value) or not numeric_value.is_integer():
                return str(value)
            epoch_seconds = int(numeric_value)
        else:
            try:
                epoch_seconds = int(value)
            except (TypeError, ValueError, OverflowError):
                return str(value)

        dt = QtCore.QDateTime.fromSecsSinceEpoch(epoch_seconds)

        if not dt.isValid():
            return str(value)

        return dt.toString("yyyy/MM/dd")

    def data(self, index: QtCore.QModelIndex, role=None):
        if len(self.property_list) == 0:
            return None

        if index.isValid():
            if self.transposed:
                attr_idx = index.row()
            else:
                attr_idx = index.column()

            val = self.property_list[attr_idx].value

            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                if isinstance(val, (list, tuple)) and len(val) > 0 and isinstance(val[0], np.ndarray):
                    return f"Waveform ({len(val)} pts)"
                if val is None:
                    return ""
                return str(val)

            if role == QtCore.Qt.ItemDataRole.EditRole:
                return val

        return None

    def setData(self, index: QtCore.QModelIndex, value, role=None) -> bool:
        if len(self.property_list) == 0:
            return True

        if self.transposed:
            attr_idx = index.row()
        else:
            attr_idx = index.column()

        prop = self.property_list[attr_idx]

        if self.attributes[attr_idx] not in self.non_editable_attributes:
            try:
                prop.value = value
            except ValueError as e:
                self.report_error(str(e))
                return True

        self.dataChanged.emit(
            index,
            index,
            [QtCore.Qt.ItemDataRole.DisplayRole, QtCore.Qt.ItemDataRole.EditRole]
        )

        return True

    def headerData(self,
                   section: int,
                   orientation: QtCore.Qt.Orientation,
                   role=QtCore.Qt.ItemDataRole.DisplayRole):
        if len(self.property_list) == 0:
            return None

        if self._hide_headers_mode is True:
            return None

        if role == QtCore.Qt.ItemDataRole.DisplayRole:

            if self.transposed:
                if orientation == QtCore.Qt.Orientation.Horizontal:
                    return 'Value'
                elif orientation == QtCore.Qt.Orientation.Vertical:
                    if self.units[section] != '':
                        return self.attributes[section] + ' [' + self.units[section] + ']'
                    else:
                        return self.attributes[section]
            else:
                if orientation == QtCore.Qt.Orientation.Horizontal:
                    if section < len(self.attributes):
                        if self.units[section] != '':
                            return self.attributes[section] + ' [' + self.units[section] + ']'
                        else:
                            return self.attributes[section]
                    else:
                        return "Deleted :/"

                elif orientation == QtCore.Qt.Orientation.Vertical:
                    return '1'

        if role == QtCore.Qt.ItemDataRole.ToolTipRole:
            if section < self.c:
                if self.units[section] != "":
                    unit = '\nUnits: ' + self.units[section]
                else:
                    unit = ''
                return self.attributes[section] + unit + ' \n' + self.tips[section]
            else:
                return ""

        return None

    def copy_to_column(self, index: QtCore.QModelIndex) -> None:
        pass

    def get_data(self):
        nrows = self.rowCount()
        ncols = self.columnCount()
        data = np.empty((nrows, ncols), dtype=object)

        for j in range(ncols):
            for i in range(nrows):
                data[i, j] = self.data(index=self.index(i, j), role=QtCore.Qt.ItemDataRole.DisplayRole)

        columns = [self.headerData(i, orientation=QtCore.Qt.Orientation.Horizontal,
                                   role=QtCore.Qt.ItemDataRole.DisplayRole) for i in range(ncols)]

        idx = [self.headerData(i, orientation=QtCore.Qt.Orientation.Vertical,
                               role=QtCore.Qt.ItemDataRole.DisplayRole) for i in range(nrows)]

        return idx, columns, data

    def copy_to_clipboard(self):
        if self.columnCount() > 0:
            idx, columns, data = self.get_data()

            data = data.astype(str)

            txt = '\t' + '\t'.join(columns) + '\n'

            for t, idx_value in enumerate(idx):
                txt += str(idx_value) + '\t' + '\t'.join(data[t, :]) + '\n'

            cb = QtWidgets.QApplication.clipboard()
            cb.clear()
            cb.setText(txt)
