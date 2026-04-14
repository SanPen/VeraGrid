# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Dict, List
import numpy as np
import pandas as pd


from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QListWidget, QDialogButtonBox, QMenu
)
from PySide6.QtCore import Qt, QPoint

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.Rms.rms_results import RmsResults, ResultsTable
from VeraGridEngine.enumerations import DeviceType
import numpy as np
import pandas as pd


class RmsPlotDialog(QDialog):
    """
    Special plot for dynamic variables
    """

    def __init__(self, grid: MultiCircuit, results: RmsResults, parent=None):
        super().__init__(parent)

        # --- Preparar dispositivos y variables ---
        buses = [bus for bus in grid.get_buses()]
        branches = [branch for branch in grid.get_branches_iter()]
        injections = [injection for injection in grid.get_injection_devices_iter()]
        devices = buses + branches + injections

        devices_options = {}
        for device in devices:
            devices_options[device.name] = [
                results.uid2vars_glob_name[var.uid]
                for var in (
                    device.rms_model.model.state_vars +
                    device.rms_model.model.algebraic_vars
                )
            ]

        self.setWindowTitle("Plot Variables")
        self.uid2idx = results.uid2idx
        self.vars_glob_name2uid = results.vars_glob_name2uid
        self.devices = devices_options

        # --- ResultsTable ---
        self.results_table = ResultsTable(
            data=np.array(results.values),
            index=np.array(pd.to_datetime(results.time_array).astype(str), dtype=np.str_),
            columns=results.variable_array,
            title="Rms Simulation Results",
            units=results.units,
            idx_device_type=DeviceType.TimeDevice,
            cols_device_type=DeviceType.NoDevice,
            xlabel="time (s)",
            ylabel="",
        )

        self.selected_vars = []

        # --- Layout principal ---
        layout = QVBoxLayout(self)

        # --- Selector de dispositivo ---
        dev_layout = QHBoxLayout()
        dev_layout.addWidget(QLabel("Device:"))
        self.device_combo = QComboBox()
        self.device_combo.addItems(list(devices_options.keys()))
        self.device_combo.currentIndexChanged.connect(self.update_variables)
        dev_layout.addWidget(self.device_combo)
        layout.addLayout(dev_layout)

        # --- Selector de variable ---
        var_layout = QHBoxLayout()
        var_layout.addWidget(QLabel("Variable:"))
        self.var_combo = QComboBox()
        var_layout.addWidget(self.var_combo)
        layout.addLayout(var_layout)

        # --- Botón para añadir variable ---
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_variable)
        layout.addWidget(add_btn)

        # --- Lista de variables seleccionadas ---
        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_variable_context_menu)
        layout.addWidget(self.list_widget)

        # --- Canvas embebido ---
        self.figure = Figure(figsize=(6, 3))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # --- Botones inferiores ---
        buttons_layout = QHBoxLayout()

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.plot_selected)
        self.buttons.rejected.connect(self.reject)
        buttons_layout.addWidget(self.buttons)

        # --- Botón ventana separada ---
        show_window_btn = QPushButton("Show in new window")
        show_window_btn.clicked.connect(self.show_external_plot)
        buttons_layout.addWidget(show_window_btn)

        layout.addLayout(buttons_layout)

        # --- Inicializar variables ---
        self.update_variables(0)

    # -------------------------------------------------------------

    def update_variables(self, index):

        device = self.device_combo.currentText()
        self.var_combo.clear()
        self.var_combo.addItems(self.devices[device])

    # -------------------------------------------------------------

    def add_variable(self):

        var = self.var_combo.currentText()
        if var and var not in [self.list_widget.item(i).text() for i in range(self.list_widget.count())]:
            self.selected_vars.append(self.vars_glob_name2uid[var])
            self.list_widget.addItem(var)
            self.plot_selected()

    # -------------------------------------------------------------

    def show_variable_context_menu(self, pos: QPoint):

        item = self.list_widget.itemAt(pos)
        if item is not None:
            menu = QMenu(self)
            remove_action = menu.addAction("Remove variable")
            action = menu.exec(self.list_widget.mapToGlobal(pos))
            if action == remove_action:
                self.remove_variable(item)

    # -------------------------------------------------------------

    def remove_variable(self, item):

        var_name = item.text()
        if var_name in self.vars_glob_name2uid:
            uid_to_remove = self.vars_glob_name2uid[var_name]
            if uid_to_remove in self.selected_vars:
                self.selected_vars.remove(uid_to_remove)

        row = self.list_widget.row(item)
        self.list_widget.takeItem(row)
        self.plot_selected()

    # -------------------------------------------------------------

    def plot_selected(self):

        self.ax.clear()
        if not self.selected_vars:
            self.canvas.draw()
            return

        selected_col_idx = [self.uid2idx[uid] for uid in self.selected_vars]
        self.results_table.plot(ax=self.ax, selected_col_idx=selected_col_idx)
        self.canvas.draw()

    # -------------------------------------------------------------

    def show_external_plot(self):
        if not self.selected_vars:
            return

        selected_col_idx = [self.uid2idx[uid] for uid in self.selected_vars]

        # Create a separate dialog for the plot
        external_dialog = QDialog(self)
        external_dialog.setWindowTitle("Plot Window")
        external_dialog.resize(900, 500)

        layout = QVBoxLayout(external_dialog)

        # Create figure and canvas
        figure = Figure(figsize=(10, 5))
        ax = figure.add_subplot(111)
        canvas = FigureCanvas(figure)

        # Add Matplotlib toolbar (includes Save, Zoom, Pan, etc.)
        toolbar = NavigationToolbar(canvas, external_dialog)
        layout.addWidget(toolbar)

        layout.addWidget(canvas)

        # Plot data
        self.results_table.plot(ax=ax, selected_col_idx=selected_col_idx)
        canvas.draw()

        external_dialog.show()



