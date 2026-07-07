# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import numpy as np
from matplotlib import pyplot as plt

from VeraGrid.Gui.pandas_model import PandasModel
from VeraGrid.Gui.Main.SubClasses.Model.compiled_arrays_model import CompiledArraysModule
from VeraGrid.Gui.Main.SubClasses.Server.server import ServerMain
import VeraGrid.Gui.gui_functions as gf

from VeraGridEngine.enumerations import BranchImpedanceMode


class CompiledArraysMain(ServerMain):
    """
    Diagrams Main
    """

    def __init__(self, parent=None):
        """

        @param parent:
        """

        # create main window
        ServerMain.__init__(self, parent=parent)

        self.compiled_arrays: CompiledArraysModule | None = None

        # array modes
        self.ui.arrayModeComboBox.setModel(
            gf.ComboModel(text_items=[('real', 'real'),
                                      ('imag', 'imag'),
                                      ('abs', 'abs'),
                                      ('complex', 'complex')])
        )

        # Buttons
        self.ui.compute_simulation_data_pushButton.clicked.connect(self.update_islands_to_display)
        self.ui.plotArraysButton.clicked.connect(self.plot_simulation_objects_data)
        self.ui.copyArraysButton.clicked.connect(self.copy_simulation_objects_data)
        self.ui.copyArraysToNumpyButton.clicked.connect(self.copy_simulation_objects_data_to_numpy)

        # tree clicks
        self.ui.simulationDataStructuresTreeView.clicked.connect(self.view_simulation_objects_data)

        # slider
        self.ui.compiled_arrays_step_slider.valueChanged.connect(self.update_compiled_arrays_time_slider_texts)

    def view_simulation_objects_data(self, index):
        """
        Simulation data structure clicked
        """
        if self.compiled_arrays is None:
            self.show_warning_toast("Calculate islands first!")
            return

        tree_mdl = self.ui.simulationDataStructuresTreeView.model()
        item = tree_mdl.itemFromIndex(index)
        path = gf.get_tree_item_path(item)

        if len(path) == 2:
            group_name = path[0]
            elm_type = path[1]

            island_idx = self.ui.simulation_data_island_comboBox.currentIndex()

            if island_idx > -1 and self.circuit.valid_for_simulation():

                df = self.compiled_arrays.get_structure(island_idx, elm_type)

                mdl = PandasModel(df)

                self.ui.simulationDataStructureTableView.setModel(mdl)

            else:
                self.ui.simulationDataStructureTableView.setModel(None)
        else:
            self.ui.simulationDataStructureTableView.setModel(None)

    def copy_simulation_objects_data(self):
        """
        Copy the arrays of the compiled arrays view to the clipboard
        """
        mdl = self.ui.simulationDataStructureTableView.model()
        mode = self.ui.arrayModeComboBox.currentData()
        mdl.copy_to_clipboard(mode=mode)
        self.show_info_toast('Copied!')

    def copy_simulation_objects_data_to_numpy(self):
        """
        Copy the arrays of the compiled arrays view to the clipboard
        """
        mdl = self.ui.simulationDataStructureTableView.model()
        mode = 'numpy'
        mdl.copy_to_clipboard(mode=mode)
        self.show_info_toast('Copied!')

    def plot_simulation_objects_data(self):
        """
        Plot the arrays of the compiled arrays view
        """
        mdl = self.ui.simulationDataStructureTableView.model()
        data = mdl.data_c

        # declare figure
        fig = plt.figure()
        ax1 = fig.add_subplot(111)

        if mdl.is_2d():
            ax1.spy(data)

        else:
            if mdl.is_complex():
                ax1.scatter(data.real, data.imag)
                ax1.set_xlabel('Real')
                ax1.set_ylabel('Imag')
            else:
                arr = np.arange(data.shape[0])
                ax1.scatter(arr, data)
                ax1.set_xlabel('Position')
                ax1.set_ylabel('Value')

        fig.tight_layout()
        plt.show()

    def recompile_circuits_for_display(self):
        """
        Recompile the circuits available to display
        :return:
        """
        if self.ui.apply_impedance_tolerances_checkBox.isChecked():
            branch_impedance_tolerance_mode = BranchImpedanceMode.Upper
        else:
            branch_impedance_tolerance_mode = BranchImpedanceMode.Specified

        idx = self.ui.compiled_arrays_step_slider.value()

        self.compiled_arrays = CompiledArraysModule(
            grid=self.circuit,
            t_idx=idx if idx > -1 else None,
            engine=self.get_preferred_engine(),
            branch_tolerance_mode=branch_impedance_tolerance_mode,
            use_stored_guess=self.ui.use_voltage_guess_checkBox.isChecked(),
            control_taps_phase=self.ui.control_tap_phase_checkBox.isChecked(),
            control_taps_modules=self.ui.control_tap_modules_checkBox.isChecked(),
            control_remote_voltage=self.ui.control_remote_voltage_checkBox.isChecked(),
        )

        # clean the table
        self.ui.simulationDataStructureTableView.setModel(None)

    def update_islands_to_display(self):
        """
        Compile the circuit and allow the display of the calculation objects
        :return:
        """
        self.recompile_circuits_for_display()
        self.ui.simulation_data_island_comboBox.clear()
        lst = ['Island ' + str(i) for i, circuit in enumerate(self.compiled_arrays.islands)]
        self.ui.simulation_data_island_comboBox.addItems(lst)
        if len(self.compiled_arrays.islands) > 0:
            self.ui.simulation_data_island_comboBox.setCurrentIndex(0)

    def update_compiled_arrays_time_slider_texts(self):
        """
        Update the slider text label as it is moved
        :return:
        """
        idx = self.ui.compiled_arrays_step_slider.value()

        if idx > -1:
            val = f"[{idx}] {self.circuit.time_profile[idx]}"
            self.ui.compiled_arrays_step_label.setText(val)
        else:
            self.ui.compiled_arrays_step_label.setText(f"Snapshot [{self.circuit.get_snapshot_time_str()}]")

        # recompile the circuit
        self.recompile_circuits_for_display()

        tree_indices = self.ui.simulationDataStructuresTreeView.selectedIndexes()

        if len(tree_indices) > 0:
            self.view_simulation_objects_data(
                index=tree_indices[0]
            )
