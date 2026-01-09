# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import sys
from typing import List, Tuple, Dict
from collections import defaultdict
from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QComboBox, QCheckBox, QTableWidget, QTableWidgetItem, QMessageBox,
    QPushButton, QHeaderView, QStyledItemDelegate, QSpinBox, QAbstractItemView
)
from PySide6.QtCore import QModelIndex, QPersistentModelIndex, Qt
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


def is_main_bar_column_editable(vl: VoltageLevelTypes) -> bool:
    """
    Determine if the Main Bar column should be editable for the given voltage level type.
    Only Breaker-and-a-Half scheme requires user to specify which bus each position connects to.

    :param vl: VoltageLevelTypes
    :return: True if Main Bar column should be editable
    """
    return vl == VoltageLevelTypes.BreakerAndAHalf


class ReorderableTableWidget(QTableWidget):
    """
    A QTableWidget that supports row reordering via up/down buttons.
    """

    def __init__(self, rows: int, columns: int, parent=None):
        super().__init__(rows, columns, parent)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._auto_update_bay_numbers = True  # Can be disabled for schemes like Breaker-and-a-Half

    def set_auto_update_bay_numbers(self, enabled: bool) -> None:
        """Enable/disable automatic bay number updates on reorder."""
        self._auto_update_bay_numbers = enabled

    def move_row_up(self) -> None:
        """Move the selected row up by one position."""
        current_row = self.currentRow()
        if current_row > 0:
            self._swap_rows(current_row, current_row - 1)
            self.selectRow(current_row - 1)
            if self._auto_update_bay_numbers:
                self._update_bay_numbers()

    def move_row_down(self) -> None:
        """Move the selected row down by one position."""
        current_row = self.currentRow()
        if current_row < self.rowCount() - 1 and current_row >= 0:
            self._swap_rows(current_row, current_row + 1)
            self.selectRow(current_row + 1)
            if self._auto_update_bay_numbers:
                self._update_bay_numbers()

    def _swap_rows(self, row1: int, row2: int) -> None:
        """Swap the contents of two rows."""
        if self._auto_update_bay_numbers:
            # Only swap device name (col 0) and assigned bus (col 2)
            # Bay number (col 1) stays in place and will be updated by _update_bay_numbers
            cols_to_swap = [0, 2]
        else:
            # Swap all columns (for schemes where user controls bay numbers)
            cols_to_swap = list(range(self.columnCount()))

        for col in cols_to_swap:
            item1 = self.takeItem(row1, col)
            item2 = self.takeItem(row2, col)
            if item1 and item2:
                self.setItem(row1, col, item2)
                self.setItem(row2, col, item1)
            elif item1:
                self.setItem(row2, col, item1)
            elif item2:
                self.setItem(row1, col, item2)

    def _update_bay_numbers(self) -> None:
        """Update bay numbers to match row positions."""
        for row in range(self.rowCount()):
            bay_item = self.item(row, 1)
            if bay_item:
                bay_item.setText(f"Bay{row + 1}")


class VoltageLevelConversionWizard(QDialog):
    """
    Voltage level conversion wizard for converting a bus-branch model to a node-breaker model.
    Supports Single Bus, Double Bus, Breaker-and-a-Half, and Ring configurations (as desired by REE)
    """

    def __init__(self, bus: dev.Bus, grid: dev.MultiCircuit):
        """
        Constructor
        :param bus: Bus to modify
        :param grid: MultiCircuit where the bus belongs
        """
        super().__init__()
        self.setWindowTitle("Convert Bus to Voltage Level")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self.bus = bus
        self.grid = grid

        self.bus_branches, self.bus_injections = self.grid.get_bus_devices(self.bus)
        self.all_dev = self.bus_branches + self.bus_injections

        # Main layout
        main_layout = QVBoxLayout(self)

        # --- Combobox for type of scheme ---
        scheme_layout = QHBoxLayout()
        scheme_layout.addWidget(QLabel("Scheme type:"))

        # Only show the 4 supported schemes in the dropdown (as desired by REE)
        # Other schemes are kept in the backend but not exposed in the UI
        self.vl_list = [
            VoltageLevelTypes.SingleBar,
            VoltageLevelTypes.DoubleBar,
            VoltageLevelTypes.BreakerAndAHalf,
            VoltageLevelTypes.Ring,
        ]

        self.vl_dict = {vl.value: vl for vl in self.vl_list}

        self.combo = QComboBox()
        self.combo.addItems([vl.value for vl in self.vl_list])
        scheme_layout.addWidget(self.combo)
        scheme_layout.addStretch()
        main_layout.addLayout(scheme_layout)
        self.combo.currentIndexChanged.connect(self.reset_all)

        # Checkboxes in a group box
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)

        # First row of checkboxes
        row1_layout = QHBoxLayout()
        self.add_brakers_checkbox = QCheckBox("Use breakers")
        self.add_brakers_checkbox.setChecked(True)
        self.add_brakers_checkbox.setToolTip("If disabled, connections are made using branches instead of breakers")
        row1_layout.addWidget(self.add_brakers_checkbox)

        self.keep_original_ratio_checkbox = QCheckBox("Keep original ratio")
        self.keep_original_ratio_checkbox.setChecked(False)
        self.keep_original_ratio_checkbox.setToolTip("If enabled, breakers inherit the ratio of the original branch. Otherwise, 9999 is assigned")
        row1_layout.addWidget(self.keep_original_ratio_checkbox)
        row1_layout.addStretch()
        options_layout.addLayout(row1_layout)

        # Second row of checkboxes
        row2_layout = QHBoxLayout()
        self.enable_transfer_bus_checkbox = QCheckBox("Enable transfer bus (JBPT)")
        self.enable_transfer_bus_checkbox.setChecked(False)
        self.enable_transfer_bus_checkbox.setToolTip("If enabled, a transfer bus (JBPT) is added with additional logic")
        row2_layout.addWidget(self.enable_transfer_bus_checkbox)

        self.reducible_branches_checkbox = QCheckBox("Reducible branches")
        self.reducible_branches_checkbox.setChecked(False)
        self.reducible_branches_checkbox.setToolTip("If enabled, new branches are marked as reducible")
        row2_layout.addWidget(self.reducible_branches_checkbox)
        row2_layout.addStretch()
        options_layout.addLayout(row2_layout)

        # Third row of checkboxes
        row3_layout = QHBoxLayout()
        self.bar_by_segments_checkbox = QCheckBox("Bars with impedance")
        self.bar_by_segments_checkbox.setChecked(False)
        self.bar_by_segments_checkbox.setToolTip("Split the bar into segments with impedances")
        row3_layout.addWidget(self.bar_by_segments_checkbox)
        row3_layout.addStretch()
        options_layout.addLayout(row3_layout)

        main_layout.addWidget(options_group)

        # --- Table for positions ---
        table_label = QLabel("Positions (use arrows to reorder):")
        main_layout.addWidget(table_label)

        # Table with reorder buttons layout
        table_layout = QHBoxLayout()

        self.bays_list = list()
        self.main_bars_list = list()
        self.table = ReorderableTableWidget(len(self.all_dev), 3)
        self.table.setHorizontalHeaderLabels(["Device", "Bay", "Assigned Bus"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_layout.addWidget(self.table)

        # Reorder buttons (up/down arrows)
        reorder_buttons_layout = QVBoxLayout()
        reorder_buttons_layout.addStretch()

        self.move_up_button = QPushButton("\u25B2")  # Up arrow
        self.move_up_button.setFixedWidth(30)
        self.move_up_button.setToolTip("Move selected row up")
        self.move_up_button.clicked.connect(self.table.move_row_up)
        reorder_buttons_layout.addWidget(self.move_up_button)

        self.move_down_button = QPushButton("\u25BC")  # Down arrow
        self.move_down_button.setFixedWidth(30)
        self.move_down_button.setToolTip("Move selected row down")
        self.move_down_button.clicked.connect(self.table.move_row_down)
        reorder_buttons_layout.addWidget(self.move_down_button)

        reorder_buttons_layout.addStretch()
        table_layout.addLayout(reorder_buttons_layout)

        main_layout.addLayout(table_layout)

        # --- Add/Remove position buttons ---
        position_buttons_layout = QHBoxLayout()
        self.add_spare_button = QPushButton("+ Add spare position")
        self.add_spare_button.setToolTip("Add an empty position (especially important for Breaker-and-a-Half scheme)")
        self.add_spare_button.clicked.connect(self.add_spare_position)
        position_buttons_layout.addWidget(self.add_spare_button)

        self.remove_row_button = QPushButton("- Remove selected")
        self.remove_row_button.setToolTip("Remove the selected row")
        self.remove_row_button.clicked.connect(self.remove_selected_row)
        position_buttons_layout.addWidget(self.remove_row_button)

        position_buttons_layout.addStretch()
        main_layout.addLayout(position_buttons_layout)

        # --- Bottom buttons layout ---
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        bottom_layout.addWidget(self.cancel_button)

        self.do_button = QPushButton("Do it")
        self.do_button.clicked.connect(self.do_it)
        bottom_layout.addWidget(self.do_button)

        main_layout.addLayout(bottom_layout)

        self.closed_ok: bool = False

        self.reset_all()

    def reset_all(self) -> None:
        """
        Reset the table and configuration based on the selected scheme type.
        """
        vl_type: VoltageLevelTypes = self.get_vl_type()
        n_positions = len(self.bus_branches) + len(self.bus_injections)

        # For Breaker-and-a-Half, we need at least enough bays for all positions
        # (positions can share bays, max 2 per bay)
        if vl_type == VoltageLevelTypes.BreakerAndAHalf:
            n_bay = (n_positions + 1) // 2  # ceil division
        else:
            n_bay = n_positions

        n_bars = get_number_of_bars(vl=vl_type, n_bay=n_positions)

        # Allowed lists
        self.bays_list = [f"Bay{i + 1}" for i in range(max(n_bay * 2, n_positions + 5))]  # Extra bays for flexibility
        self.main_bars_list = ["JBP1", "JBP2"] if n_bars >= 2 else ["JBP1"]

        # Determine if main bar column should be editable
        main_bar_editable = is_main_bar_column_editable(vl_type)

        # For Breaker-and-a-Half, disable auto bay number update (user controls bay grouping)
        # For other schemes, enable auto update so reordering updates bay numbers
        self.table.set_auto_update_bay_numbers(vl_type != VoltageLevelTypes.BreakerAndAHalf)

        # Clear and rebuild table
        self.table.setRowCount(n_positions)

        # Collect device names
        dev_names = []
        for elm in self.bus_branches + self.bus_injections:
            dev_names.append(elm.name)
        dev_names.append("(Spare)")  # Always allow spare as an option

        # Fill data. For Breaker-and-a-Half, alternate bus assignments in pairs
        data: List[TableEntry] = list()
        for i, elm in enumerate(self.bus_branches + self.bus_injections):
            if vl_type == VoltageLevelTypes.BreakerAndAHalf:
                # Pair positions in bays, alternating bus assignments
                bay_num = (i // 2) + 1
                # First position in bay gets JBP1, second gets JBP2
                assigned_bus = "JBP1" if (i % 2 == 0) else "JBP2"
            else:
                bay_num = i + 1
                assigned_bus = "JBP1"
            data.append(TableEntry(elm.name, f"Bay{bay_num}", assigned_bus))

        # Apply delegates
        self.table.setItemDelegateForColumn(0, ComboBoxDelegate(dev_names, self.table))
        self.table.setItemDelegateForColumn(1, ComboBoxDelegate(self.bays_list, self.table))
        self.table.setItemDelegateForColumn(2, ComboBoxDelegate(self.main_bars_list, self.table))

        for row, entry in enumerate(data):
            device_item = QTableWidgetItem(entry.device)
            bay_item = QTableWidgetItem(entry.bay)
            main_bar_item = QTableWidgetItem(entry.main_bar)

            # Make main bar column read-only if not editable for this scheme
            if not main_bar_editable:
                main_bar_item.setFlags(main_bar_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                main_bar_item.setBackground(Qt.GlobalColor.lightGray)

            self.table.setItem(row, 0, device_item)
            self.table.setItem(row, 1, bay_item)
            self.table.setItem(row, 2, main_bar_item)

    def add_spare_position(self) -> None:
        """
        Add a spare position row to the table.
        This is especially useful for Breaker-and-a-Half scheme where bays may need to be completed.
        """
        vl_type = self.get_vl_type()
        main_bar_editable = is_main_bar_column_editable(vl_type)

        row = self.table.rowCount()
        self.table.insertRow(row)

        # Determine next bay number
        next_bay = row + 1

        # Set items
        device_item = QTableWidgetItem("(Spare)")
        bay_item = QTableWidgetItem(f"Bay{next_bay}")
        main_bar_item = QTableWidgetItem("JBP1")

        if not main_bar_editable:
            main_bar_item.setFlags(main_bar_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            main_bar_item.setBackground(Qt.GlobalColor.lightGray)

        self.table.setItem(row, 0, device_item)
        self.table.setItem(row, 1, bay_item)
        self.table.setItem(row, 2, main_bar_item)

    def remove_selected_row(self) -> None:
        """
        Remove the currently selected row from the table
        Only allows removal of spare positions (not actual devices)
        """
        current_row = self.table.currentRow()
        if current_row >= 0:
            device_item = self.table.item(current_row, 0)
            if device_item and device_item.text() == "(Spare)":
                self.table.removeRow(current_row)
            else:
                QMessageBox.warning(
                    self,
                    "Cannot Remove",
                    "Only spare positions can be removed. Actual devices cannot be removed from the list."
                )

    def get_vl_type(self) -> VoltageLevelTypes:
        """
        Get the currently selected voltage level type.
        :return: VoltageLevelTypes enum value
        """
        return self.vl_dict[self.combo.currentText()]

    def validate_configuration(self) -> Tuple[bool, str]:
        """
        Validate the current configuration based on the selected scheme type.
        :return: Tuple of (is_valid, error_message)
        """
        vl_type = self.get_vl_type()
        bay_assignments = self.get_bay_assignments()

        # Group by bay
        bays: Dict[int, List[Tuple[str, str]]] = defaultdict(list)
        for device, bay_num, bus in bay_assignments:
            bays[bay_num].append((device, bus))

        if vl_type == VoltageLevelTypes.BreakerAndAHalf:
            # Check Breaker-and-a-Half specific rules
            for bay_num, positions in bays.items():
                if len(positions) > 2:
                    return False, f"Bay {bay_num} has {len(positions)} positions. Maximum is 2 for Breaker-and-a-Half."

                if len(positions) == 2:
                    # Both positions must have different bus assignments
                    buses = [p[1] for p in positions]
                    if buses[0] == buses[1]:
                        return False, f"Bay {bay_num} has two positions with the same bus assignment ({buses[0]}). Each position must connect to a different bus."
        else:
            # For other schemes, check no duplicate bay numbers
            for bay_num, positions in bays.items():
                if len(positions) > 1:
                    return False, f"Bay {bay_num} has {len(positions)} positions. Only 1 position per bay is allowed for {vl_type.value}."

        return True, ""

    def get_bay_assignments(self) -> List[Tuple[str, int, str]]:
        """
        Get the bay assignments from the table.
        :return: List of (device_name, bay_number, assigned_bus) tuples
        """
        assignments = []
        for row in range(self.table.rowCount()):
            device_item = self.table.item(row, 0)
            bay_item = self.table.item(row, 1)
            main_bar_item = self.table.item(row, 2)

            device = device_item.text() if device_item else ""
            bay_str = bay_item.text() if bay_item else "Bay1"
            main_bar = main_bar_item.text() if main_bar_item else "JBP1"

            # Extract bay number from string like "Bay1"
            try:
                bay_num = int(bay_str.replace("Bay", ""))
            except ValueError:
                bay_num = 1

            assignments.append((device, bay_num, main_bar))

        return assignments

    def get_device_to_bay_mapping(self) -> Dict[str, Tuple[int, str]]:
        """
        Get a mapping from device name to (bay_number, assigned_bus).
        :return: Dictionary mapping device name to (bay, bus) tuple
        """
        mapping = {}
        for device, bay, bus in self.get_bay_assignments():
            if device != "(Spare)":
                mapping[device] = (bay, bus)
        return mapping

    def do_it(self) -> None:
        """
        Validate configuration and perform the conversion if valid.
        """
        is_valid, error_msg = self.validate_configuration()

        if not is_valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return

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
