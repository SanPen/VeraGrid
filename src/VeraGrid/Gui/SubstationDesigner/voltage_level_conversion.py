# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import sys
from typing import List
from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout,
    QComboBox, QCheckBox, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QStyledItemDelegate, QSpinBox
)
from PySide6.QtCore import QModelIndex, QPersistentModelIndex
import VeraGridEngine.Devices as dev
from VeraGridEngine.enumerations import VoltageLevelTypes


class SpinBoxDelegate(QStyledItemDelegate):
    """
    Delegate for integer-only column (Calle).
    """

    def __init__(self, parent=None, minimum=1, maximum=9999):
        super().__init__(parent)
        self.minimum = minimum
        self.maximum = maximum

    def createEditor(self, parent, option, index):
        """

        :param parent:
        :param option:
        :param index:
        :return:
        """
        spinbox = QSpinBox(parent)
        spinbox.setMinimum(self.minimum)
        spinbox.setMaximum(self.maximum)
        return spinbox

    def setEditorData(self, editor: QWidget, index: QModelIndex | QPersistentModelIndex):
        """

        :param editor:
        :param index:
        """
        value = index.model().data(index, 0)
        if value and value.isdigit():
            editor.setValue(int(value))
        else:
            editor.setValue(self.minimum)

    def setModelData(self, editor, model, index):
        """

        :param editor:
        :param model:
        :param index:
        """
        model.setData(index, str(editor.value()))


class ComboBoxDelegate(QStyledItemDelegate):
    """Delegate for restricted values (Posición, Barra)."""

    def __init__(self, items: List[str], parent: QTableWidget = None) -> None:
        super().__init__(parent)
        self.items = items

    def createEditor(self, parent, option, index):
        """

        :param parent:
        :param option:
        :param index:
        :return:
        """
        combo = QComboBox(parent)
        combo.addItems(self.items)
        return combo

    def setEditorData(self, editor, index):
        """

        :param editor:
        :param index:
        """
        value = index.model().data(index, 0)
        if value in self.items:
            editor.setCurrentText(value)
        else:
            editor.setCurrentIndex(0)

    def setModelData(self, editor, model, index):
        """

        :param editor:
        :param model:
        :param index:
        """
        model.setData(index, editor.currentText())


class TableEntry:
    """
    Table entry
    """

    def __init__(self, device, bay: str, main_bar: str):
        self.device = device
        self.bay = bay
        self.main_bar = main_bar


def get_number_of_bars(vl: VoltageLevelTypes, n_bay: int):
    """
    Get the number of bars of the configuration
    :param vl: VoltageLevelTypes
    :param n_bay: number of bays (used for the ring config)
    :return: number of main bars
    """
    if vl == VoltageLevelTypes.SingleBar:
        return 1
    if vl == VoltageLevelTypes.SingleBarWithBypass:
        return 1
    if vl == VoltageLevelTypes.SingleBarWithSplitter:
        return 1
    if vl == VoltageLevelTypes.DoubleBar:
        return 2
    if vl == VoltageLevelTypes.DoubleBarWithBypass:
        return 2
    if vl == VoltageLevelTypes.DoubleBarWithTransference:
        return 2
    if vl == VoltageLevelTypes.DoubleBarDuplex:
        return 2
    if vl == VoltageLevelTypes.Ring:
        return n_bay
    if vl == VoltageLevelTypes.BreakerAndAHalf:
        return 2

    return 0


class VoltageLevelConversionWizard(QDialog):
    """
    Voltage level conversion wizzard
    """

    def __init__(self, bus: dev.Bus, grid: dev.MultiCircuit):
        """
        Constructor
        :param bus: Bus to modify
        :param grid: MultiCircuit where the bus belongs
        """
        super().__init__()
        self.setWindowTitle("Convert Bus to Voltage Level")

        self.bus = bus
        self.grid = grid

        self.bus_branches, self.bus_injections = self.grid.get_bus_devices(self.bus)
        self.all_dev = self.bus_branches + self.bus_injections

        # Main layout
        main_layout = QVBoxLayout(self)

        # --- Combobox for type of park ---

        self.vl_list = [
            VoltageLevelTypes.SingleBar,
            VoltageLevelTypes.SingleBarWithBypass,
            VoltageLevelTypes.SingleBarWithSplitter,
            VoltageLevelTypes.DoubleBar,
            VoltageLevelTypes.DoubleBarWithBypass,
            VoltageLevelTypes.DoubleBarWithTransference,
            # VoltageLevelTypes.DoubleBarDuplex,
            VoltageLevelTypes.Ring,
            VoltageLevelTypes.BreakerAndAHalf,
        ]

        self.vl_dict = {vl.value: vl for vl in self.vl_list}

        self.combo = QComboBox()
        self.combo.addItems([vl.value for vl in self.vl_list])
        main_layout.addWidget(self.combo)
        self.combo.currentIndexChanged.connect(self.reset_all)

        # --- Checkboxes ---
        self.add_brakers_checkbox = QCheckBox("Add breakers")
        self.add_brakers_checkbox.setChecked(True)
        self.bar_by_segments_checkbox = QCheckBox("Bars with impedance")

        for cb in [self.add_brakers_checkbox, self.bar_by_segments_checkbox]:
            main_layout.addWidget(cb)

        # --- Table for positions ---
        self.bays_list = list()
        self.main_bars_list = list()
        self.table = QTableWidget(len(self.all_dev), 3)
        self.table.setHorizontalHeaderLabels(["Device", "Bay", "Main Bar"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.table)

        # --- Bottom buttons layout ---
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()  # spacer pushes "Do it" button to the right

        # Right side: Do it button
        self.do_button = QPushButton("Do it")
        bottom_layout.addWidget(self.do_button)
        self.do_button.clicked.connect(self.do_it)

        main_layout.addLayout(bottom_layout)

        self.closed_ok: bool = False

        self.reset_all()

    def reset_all(self) -> None:
        """

        :return:
        """

        vl_type: VoltageLevelTypes = self.get_vl_type()
        n_bay = len(self.bus_branches) + len(self.bus_injections)
        n_bars = get_number_of_bars(vl=vl_type, n_bay=n_bay)

        # Allowed lists
        self.bays_list = [f"Bay{i + 1}" for i in range(n_bay)]
        self.main_bars_list = [f"Bar{i+1}" for i in range(n_bars)]  # ["JPB1", "JPB2", "JPB3"]

        # fill data
        data: List[TableEntry] = list()
        dev_names = list()
        i = 0
        for lst in [self.bus_branches, self.bus_injections]:
            for elm in lst:
                dev_names.append(elm.name)
                data.append(TableEntry(elm.name, self.bays_list[i], self.main_bars_list[0]))
                i += 1

        # Apply delegates
        self.table.setItemDelegateForColumn(0, ComboBoxDelegate(dev_names, self.table))  # Posición
        self.table.setItemDelegateForColumn(1, ComboBoxDelegate(self.bays_list, self.table))  # Calle
        self.table.setItemDelegateForColumn(2, ComboBoxDelegate(self.main_bars_list, self.table))  # Barra

        for row, entry in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(entry.device))
            self.table.setItem(row, 1, QTableWidgetItem(entry.bay))
            self.table.setItem(row, 2, QTableWidgetItem(entry.main_bar))

    def get_vl_type(self) -> VoltageLevelTypes:
        """

        :return:
        """
        return self.vl_dict[self.combo.currentText()]

    def do_it(self) -> None:
        """
        Perform whatever is selected and qut
        :return:
        """
        self.closed_ok = True
        self.close()


# if __name__ == "__main__":
#     import VeraGridEngine as vg
#
#     fname = "/home/santi/Documentos/Git/GitHub/VeraGrid_bkup/src/tests/data/grids/lynn5node.gridcal"
#     _grid = vg.open_file(fname)
#
#     app = QApplication(sys.argv)
#     window = VoltageLevelConversionWizard(grid=_grid, bus=_grid.buses[2])
#     window.resize(600, 500)
#     window.show()
#     sys.exit(app.exec())
