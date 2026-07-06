# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from PySide6.QtGui import Qt
from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import Qt

from VeraGridEngine.IO.file_system import scripts_path
from VeraGrid.Gui.Main.SubClasses.io import IoMain
from VeraGrid.Gui.gui_functions import CustomFileSystemModel
import VeraGrid.Gui.gui_functions as gf
from VeraGrid.Gui.messages import error_msg, yes_no_question

from VeraGridEngine.IO.file_system import get_create_veragrid_folder
import VeraGridEngine as vg


class ScriptingMain(IoMain):
    """
    Diagrams Main
    """

    def __init__(self, parent=None):
        """

        @param parent:
        """

        # create main window
        IoMain.__init__(self, parent)

        self.add_console_vars()

        # scripts tree view --------------------------------------------------------------------------------------------
        self.python_fs_model = CustomFileSystemModel(root_path=scripts_path(), ext_filter=['*.py'])
        self.ui.sourceCodeTreeView.setModel(self.python_fs_model)
        self.ui.sourceCodeTreeView.setRootIndex(self.python_fs_model.index(scripts_path()))

        # actions ------------------------------------------------------------------------------------------------------
        self.ui.actionReset_console.triggered.connect(self.reset_console)

        # button clicks ------------------------------------------------------------------------------------------------
        self.ui.runSourceCodeButton.clicked.connect(self.run_source_code)
        self.ui.saveSourceCodeButton.clicked.connect(self.save_source_code)
        self.ui.clearSourceCodeButton.clicked.connect(self.clear_source_code)
        self.ui.clearConsoleButton.clicked.connect(self.reset_console)

        # double clicked -----------------------------------------------------------------------------------------------
        self.ui.sourceCodeTreeView.doubleClicked.connect(self.source_code_tree_clicked)

        # context menu
        self.ui.sourceCodeTreeView.customContextMenuRequested.connect(self.show_source_code_tree_context_menu)

        # Set context menu policy to CustomContextMenu
        self.ui.sourceCodeTreeView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def clear_console(self):
        """
        Clear console output
        """
        self.console.clear()

    def reset_console(self):
        """
        Reset console
        :return:
        """
        self.console.reset()
        self.add_console_vars()

    def print_console_help(self):
        help_lines: list[str] = [
            "",
            self.tr('VeraGrid internal commands.\n'),
            self.tr('If a command is unavailable is because the study has not been executed yet.'),
            self.tr('\n\nclc():\tclear the console.'),
            self.tr('\n\nApp functions:'),
            self.tr('\tapp.new_project(): Clear all.'),
            self.tr('\tapp.open_file(): Prompt to load VeraGrid compatible file'),
            self.tr('\tapp.save_file(): Prompt to save VeraGrid file'),
            self.tr('\tapp.export_diagram(): Prompt to export the diagram in png.'),
            self.tr('\tapp.create_schematic_from_api(): Create the schematic from the circuit information.'),
            self.tr('\tapp.adjust_all_node_width(): Adjust the width of all the nodes according to their name.'),
            self.tr('\tapp.numerical_circuit: get compilation of the assets.'),
            self.tr('\tapp.islands: get compilation of the assets split into the topological islands.'),
            self.tr('\n\nCircuit functions:'),
            self.tr('\tapp.circuit.plot_graph(): Plot a graph in a Matplotlib window. Call plt.show() after.'),
            self.tr('\n\nPower flow results:'),
            self.tr('\tapp.session.power_flow.voltage:\t the nodal voltages in per unit'),
            self.tr('\tapp.session.power_flow.current:\t the branch currents in per unit'),
            self.tr('\tapp.session.power_flow.loading:\t the branch loading in %'),
            self.tr('\tapp.session.power_flow.losses:\t the branch losses in per unit'),
            self.tr('\tapp.session.power_flow.power:\t the nodal power Injections in per unit'),
            self.tr('\tapp.session.power_flow.Sf:\t the branch power Injections in per unit at the "from" side'),
            self.tr('\tapp.session.power_flow.St:\t the branch power Injections in per unit at the "to" side'),
            self.tr('\n\nShort circuit results:'),
            self.tr('\tapp.session.short_circuit.voltage:\t the nodal voltages in per unit'),
            self.tr('\tapp.session.short_circuit.current:\t the branch currents in per unit'),
            self.tr('\tapp.session.short_circuit.loading:\t the branch loading in %'),
            self.tr('\tapp.session.short_circuit.losses:\t the branch losses in per unit'),
            self.tr('\tapp.session.short_circuit.power:\t the nodal power Injections in per unit'),
            self.tr('\tapp.session.short_circuit.power_from:\t the branch power Injections in per unit at the "from" side'),
            self.tr('\tapp.session.short_circuit.power_to:\t the branch power Injections in per unit at the "to" side'),
            self.tr('\tapp.session.short_circuit.short_circuit_power:\t Short circuit power in MVA of the grid nodes'),
            self.tr('\n\nOptimal power flow results:'),
            self.tr('\tapp.session.optimal_power_flow.voltage:\t the nodal voltages angles in rad'),
            self.tr('\tapp.session.optimal_power_flow.load_shedding:\t the branch loading in %'),
            self.tr('\tapp.session.optimal_power_flow.losses:\t the branch losses in per unit'),
            self.tr('\tapp.session.optimal_power_flow.Sbus:\t the nodal power Injections in MW'),
            self.tr('\tapp.session.optimal_power_flow.Sf:\t the branch power Sf'),
            self.tr('\n\nTime series power flow results:'),
            self.tr('\tapp.session.power_flow_ts.time:\t Profiles time index (pandas DateTimeIndex object)'),
            self.tr('\tapp.session.power_flow_ts.load_profiles:\t Load profiles matrix (row: time, col: node)'),
            self.tr('\tapp.session.power_flow_ts.gen_profiles:\t Generation profiles matrix (row: time, col: node)'),
            self.tr('\tapp.session.power_flow_ts.voltages:\t nodal voltages results matrix (row: time, col: node)'),
            self.tr('\tapp.session.power_flow_ts.currents:\t Branches currents results matrix (row: time, col: branch)'),
            self.tr('\tapp.session.power_flow_ts.loadings:\t Branches loadings results matrix (row: time, col: branch)'),
            self.tr('\tapp.session.power_flow_ts.losses:\t Branches losses results matrix (row: time, col: branch)'),
            self.tr('\n\nVoltage stability power flow results:'),
            self.tr('\tapp.session.continuation_power_flow.voltage:\t Voltage values for every power multiplication factor.'),
            self.tr('\tapp.session.continuation_power_flow.lambda:\t Value of power multiplication factor applied'),
            self.tr('\tapp.session.continuation_power_flow.Sf:\t Power values for every power multiplication factor.'),
            self.tr('\n\nMonte Carlo power flow results:'),
            self.tr('\tapp.session.stochastic_power_flow.V_avg:\t nodal voltage average result.'),
            self.tr('\tapp.session.stochastic_power_flow.I_avg:\t branch current average result.'),
            self.tr('\tapp.session.stochastic_power_flow.Loading_avg:\t branch loading average result.'),
            self.tr('\tapp.session.stochastic_power_flow.Losses_avg:\t branch losses average result.'),
            self.tr('\tapp.session.stochastic_power_flow.V_std:\t nodal voltage standard deviation result.'),
            self.tr('\tapp.session.stochastic_power_flow.I_std:\t branch current standard deviation result.'),
            self.tr('\tapp.session.stochastic_power_flow.Loading_std:\t branch loading standard deviation result.'),
            self.tr('\tapp.session.stochastic_power_flow.Losses_std:\t branch losses standard deviation result.'),
            self.tr('\tapp.session.stochastic_power_flow.V_avg_series:\t nodal voltage average series.'),
            self.tr('\tapp.session.stochastic_power_flow.V_std_series:\t branch current standard deviation series.'),
            self.tr('\tapp.session.stochastic_power_flow.error_series:\t Monte Carlo error series (the convergence value).'),
            self.tr('The same for app.latin_hypercube_sampling'),
        ]

        for line in help_lines:
            self.console.append_output(line)

    def add_console_vars(self):
        """
        Add vars to the console
        :return:
        """
        for elm in [self.console, self.code_editor]:
            elm.add_var("hlp", self.print_console_help)
            elm.add_var("np", np)
            elm.add_var("pd", pd)
            elm.add_var("plt", plt)
            elm.add_var("vg", vg)  # veragrid as a library
            elm.add_var('app', self)
            elm.add_var('circuit', self.circuit)
            elm.add_var('user_folder', get_create_veragrid_folder)

        self.console.add_var("clc", self.console.clear)

    def append_output(self, text: str):
        """
        Add some text to the output
        :param text: text to append
        """
        self.console.append_output(text)

    def run_source_code(self):
        """
        Run the source code in the IPython console
        """
        source_code = self.code_editor.toPlainText()

        if source_code[-1] != '\n':
            source_code += "\n"

        self.console.execute(source_code)
        self.console.append_output(">>> ")

    def source_code_tree_clicked(self, index):
        """
        On double click on a source code tree item, load the source code
        """
        pth = self.python_fs_model.filePath(index)

        if os.path.exists(pth):
            with open(pth, 'r') as f:
                txt = "\n".join(line.rstrip() for line in f)
                self.code_editor.setPlainText(txt)

            name = os.path.basename(pth)
            self.ui.sourceCodeNameLineEdit.setText(name.replace('.py', ''))
        else:
            error_msg(pth + self.tr(' does not exist :/'), self.tr('Open script'))

    def clear_source_code(self):
        """
        Clear source code
        """
        ok = yes_no_question(text=self.tr('Are you sure you want to clear source code?'),
                             title=self.tr('Clear source code'))

        if ok:
            self.ui.sourceCodeNameLineEdit.setText("")
            self.code_editor.setPlainText("")

    def save_source_code(self):
        """
        Save the source code
        """
        name = self.ui.sourceCodeNameLineEdit.text().strip()

        if name != '':
            fname = name + '.py'
            pth = os.path.join(scripts_path(), fname)
            with open(pth, 'w') as f:
                f.write(self.code_editor.toPlainText())
        else:
            error_msg(self.tr("Please enter a name for the script"), title=self.tr("Save script"))

    def delete_source_code(self):
        """
        Delete the selected file
        """
        index = self.ui.sourceCodeTreeView.currentIndex()
        pth = self.python_fs_model.filePath(index)
        if os.path.exists(pth):
            ok = yes_no_question(text=self.tr("Do you want to delete {path}?").format(path=pth),
                                 title=self.tr("Delete source code file"))

            if ok:
                os.remove(pth)
        else:
            error_msg(pth + self.tr(' does not exist :/'), self.tr("Delete source code file"))

    def show_source_code_tree_context_menu(self, pos: QtCore.QPoint):
        """
        Show source code tree view context menu
        :param pos: Relative click position
        """
        context_menu = QtWidgets.QMenu(parent=self.ui.diagramsListView)

        gf.add_menu_entry(menu=context_menu,
                          text=self.tr("Delete"),
                          icon_path=":/Icons/icons/delete_with_dialogue.png",
                          function_ptr=self.delete_source_code)

        # Convert global position to local position of the list widget
        mapped_pos = self.ui.sourceCodeTreeView.viewport().mapToGlobal(pos)
        context_menu.exec(mapped_pos)
