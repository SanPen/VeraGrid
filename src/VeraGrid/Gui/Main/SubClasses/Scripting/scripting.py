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

    def print_console_help(self) -> None:
        """
        Print the scripting console quick reference.

        :return: None.
        """
        # Keep this help readable in narrow terminals because users copy it from
        # the embedded console into text files and tickets.
        help_lines: list[str] = [
            "",
            "=" * 78,
            "VeraGrid scripting console",
            "=" * 78,
            "",
            "Helpers already loaded",
            "  hlp()        print this help",
            "  clc()        clear the console",
            "  app          active VeraGrid GUI object",
            "  circuit      same object as app.circuit",
            "  vg           VeraGridEngine package",
            "  np, pd, plt  NumPy, pandas and Matplotlib",
            "  user_folder  function returning the ~/.VeraGrid folder",
            "",
            "Common app commands",
            "  app.new_project()                 clear the current project",
            "  app.open_file()                   open a supported grid file",
            "  app.save_file()                   save the current grid",
            "  app.export_diagram()              export the active diagram",
            "  app.create_schematic_from_api()   rebuild schematic from grid",
            "  app.adjust_all_node_width()       fit node widths to names",
            "",
            "Circuit access",
            "  grid = app.circuit                current MultiCircuit model",
            "  grid.plot_graph(); plt.show()     plot the graph",
            "  app.numerical_circuit             latest compiled circuit",
            "  app.islands                       latest compiled islands",
            "",
            "Run studies from scripts",
            "  Use vg.* helpers or drivers. Avoid GUI run methods here:",
            "  those are asynchronous GUI button workflows.",
            "",
            "Blocking helpers",
            "  pf = vg.power_flow(app.circuit)",
            "  pf3 = vg.power_flow3ph(app.circuit)",
            "  pfts = vg.power_flow_ts(app.circuit)",
            "  lin = vg.linear_power_flow(app.circuit)",
            "  lints = vg.linear_power_flow_ts(app.circuit)",
            "  sc = vg.short_circuit(app.circuit, fault_index=0)",
            "  cpf = vg.continuation_power_flow(app.circuit)",
            "  opf = vg.linear_opf(app.circuit)",
            "  cont = vg.contingency_analysis(app.circuit)",
            "  contts = vg.contingencies_ts(app.circuit)",
            "  cl = vg.clustering(app.circuit, n_points=100)",
            "",
            "Blocking driver pattern",
            "  drv = vg.PowerFlowDriver(app.circuit, vg.PowerFlowOptions())",
            "  drv.run()",
            "  res = drv.results",
            "",
            "Read GUI-completed study results",
            "  _, res = app.session.power_flow",
            "  _, res = app.session.power_flow_3ph",
            "  _, res = app.session.power_flow_ts",
            "  _, res = app.session.linear_power_flow",
            "  _, res = app.session.short_circuit",
            "  _, res = app.session.contingency",
            "  _, res = app.session.optimal_power_flow",
            "  _, res = app.session.continuation_power_flow",
            "  _, res = app.session.stochastic_power_flow",
            "",
            "Frequently used result fields",
            "  PF:  res.voltage, res.Sbus, res.Sf, res.St",
            "       res.If, res.It, res.loading, res.losses",
            "  PF TS: res.voltage[t, :], res.Sf[t, :], res.loading[t, :]",
            "  3ph: res.voltage_A, res.voltage_B, res.voltage_C",
            "       res.Sf_A, res.Sf_B, res.Sf_C",
            "  SC:  res.voltage, res.Sf, res.loading, res.SCpower",
            "  OPF: res.generator_power, res.load_shedding",
            "       res.bus_shadow_prices, res.overloads",
            "  CPF: res.voltages, res.lambdas, res.loading",
            "  PTDF: res.PTDF, res.LODF, res.Sf, res.loading",
            "  Stochastic: res.voltage, res.loading, res.losses",
            "",
            "Examples",
            "  _, pf = app.session.power_flow",
            "  print(pf.get_bus_df())",
            "  pf.get_branch_df().to_csv('branches.csv')",
            "  plt.plot(abs(pf.voltage)); plt.show()",
            "",
            "Full guide: doc/md_source/veragrid_scripting_guide.md",
            "=" * 78,
        ]

        # Emit one console row at a time so the GUI console keeps normal line
        # wrapping and selection behaviour.
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
            error_msg(self.tr("{path} does not exist :/").format(path=pth), self.tr('Open script'))

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
            error_msg(self.tr("{path} does not exist :/").format(path=pth), self.tr("Delete source code file"))

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
