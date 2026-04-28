# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import os
import pathlib
from typing import Union, List, Callable
from PySide6 import QtWidgets

import VeraGrid.Gui.gui_functions as gf
import VeraGrid.Session.export_results_driver as exprtdrv
import VeraGrid.Session.file_handler as filedrv
from VeraGrid.Gui.GridMerge.grid_diff import GridDiffDialogue
from VeraGrid.Gui.GridMerge.grid_merge import GridMergeDialogue
from VeraGrid.plugins import install_plugin, get_plugin_info
from VeraGrid.Gui.FileDialogues.CoordinatesInput.coordinates_dialogue import CoordinatesInputGUI
from VeraGrid.Gui.general_dialogues import LogsDialogue, CustomQuestionDialogue, FileTypeSelector, CgmesOptionsSelector
from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget
from VeraGrid.Gui.messages import yes_no_question, error_msg, warning_msg, info_msg
from VeraGrid.Gui.GridGenerator.grid_generator_dialogue import GridGeneratorGUI
from VeraGrid.Gui.FileDialogues.RosetaExplorer.RosetaExplorer import RosetaExplorerGUI
from VeraGrid.Gui.Main.SubClasses.Model.scenarios import ScenariosMain
from VeraGrid.Gui.FileDialogues.CGMESDialogue.cgmes_export import CgmesExportDialogue
from VeraGrid.Gui.FileDialogues.PsseDialogue.psse_export import PsseExportDialogue
from VeraGrid.Gui.FileDialogues.PsseDialogue.psse_import import PsseImportDialogue
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Compilers.circuit_to_pgm import PGM_AVAILABLE
from VeraGridEngine.IO.file_save import FileSavingOptions
from VeraGridEngine.IO.file_open import determine_file_type
from VeraGridEngine.enumerations import SimulationTypes, FileType
from VeraGridEngine.IO.veragrid.contingency_parser import import_contingencies_from_json, export_contingencies_json_file
from VeraGridEngine.IO.veragrid.remote import RemoteInstruction
from VeraGridEngine.IO.veragrid.catalogue import save_catalogue, load_catalogue
from VeraGridEngine.Utils.ThirdParty.gslv.gslv_activation import install_gslv_license
from VeraGrid.templates import (get_cables_catalogue, get_transformer_catalogue, get_wires_catalogue,
                                get_sequence_lines_catalogue)


class IoMain(ScenariosMain):
    """
    Inputs-Outputs Main
    """

    def __init__(self, parent=None):
        """

        @param parent:
        """

        # create the main window
        ScenariosMain.__init__(self, parent)

        self.rosetta_gui: Union[RosetaExplorerGUI, None] = None

        self.accepted_extensions = ['.veragrid', '.dveragrid',
                                    '.gridcal', '.dgridcal',
                                    '.xlsx', '.xls', '.sqlite', '.gch5',
                                    '.dgs', '.m', '.matpower', '.raw', '.RAW', '.json', '.uct',
                                    '.iidm', '.xiidm', '.xiidm.bz2',
                                    '.ejson2', '.ejson3', '.p', '.nc', '.hdf5',
                                    '.xml', '.rawx', '.zip', '.dpx', '.pwf', '.epc', '.EPC',
                                    '.vgplugin', '.gslv']

        # window pointers
        self.cgmes_dialogue: CgmesExportDialogue | None = None
        self.psse_export_dialogue: PsseExportDialogue | None = None

        # actions
        self.ui.actionNew_project.triggered.connect(self.new_project)
        self.ui.actionOpen_file.triggered.connect(self.open_file)
        self.ui.actionAdd_circuit.triggered.connect(self.import_circuit)
        self.ui.actionExport_circuit_differential.triggered.connect(self.export_circuit_differential)
        self.ui.actionSave.triggered.connect(self.save_file)
        self.ui.actionSave_as.triggered.connect(self.save_file_as)
        self.ui.actionExport_all_the_device_s_profiles.triggered.connect(self.export_object_profiles)
        self.ui.actionExport_all_results.triggered.connect(self.export_all)
        self.ui.actiongrid_Generator.triggered.connect(self.grid_generator)
        self.ui.actionImport_bus_coordinates.triggered.connect(self.import_bus_coordinates)
        self.ui.actionImport_contingencies.triggered.connect(self.import_contingencies)
        self.ui.actionExport_contingencies.triggered.connect(self.export_contingencies)
        self.ui.actionAdd_default_catalogue.triggered.connect(self.add_default_catalogue)
        self.ui.actionAdd_custom_catalogue.triggered.connect(self.load_custom_catalogue)
        self.ui.actionExportCatalogue.triggered.connect(self.save_custom_catalogue)

        self.ui.actionPSS_e_Raw_Rawx.triggered.connect(self.export_psse)
        self.ui.actionPower_Factory_DGS.triggered.connect(self.export_power_factory)
        self.ui.actionCIM.triggered.connect(self.export_cim)
        self.ui.actionCGMES.triggered.connect(self.export_cgmes)
        self.ui.actionPower_Grid_Models.triggered.connect(self.export_power_grid_models)
        self.ui.actionJSON.triggered.connect(self.export_json)
        self.ui.actionH5.triggered.connect(self.export_h5)
        self.ui.actionMicrosoft_Excel.triggered.connect(self.export_excel)
        self.ui.actionSQLite.triggered.connect(self.export_sqlite)

        # Buttons
        self.ui.exportSimulationDataButton.clicked.connect(self.export_simulation_data)
        self.ui.loadResultFromDiskButton.clicked.connect(self.load_results_driver)

    def dragEnterEvent(self, event):
        """

        :param event:
        :return:
        """
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """

        :param event:
        :return:
        """
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """
        Drop file on the GUI, the default behaviour is to load the file
        :param event: event containing all the information
        """
        if event.mimeData().hasUrls:
            events = event.mimeData().urls()
            if len(events) > 0:

                file_names = list()

                any_grid_delta = False
                any_normal_grid = False

                for event in events:
                    file_name = event.toLocalFile()
                    # name, file_extension = os.path.splitext(file_name)
                    file_extension = ''.join(pathlib.Path(file_name).suffixes)
                    if file_extension.lower() in self.accepted_extensions:
                        file_names.append(file_name)

                        if file_name.endswith('.dgridcal') or file_name.endswith('.dveragrid'):
                            any_grid_delta = True
                        elif file_name.endswith('.vgplugin'):
                            self.install_plugin_now(file_name)
                            return
                        elif file_name.endswith('.license.gslv'):
                            ok, msg = install_gslv_license(file_name)
                            if ok:
                                self.show_info_toast(msg)
                            else:
                                self.show_error_toast(msg)
                            return
                        elif file_name.endswith(".xiidm.bz2"):
                            any_grid_delta = False
                            any_normal_grid = True
                        else:
                            any_normal_grid = True

                    else:
                        self.show_error_toast('The file type ' + file_extension.lower() + ' is not accepted :(')

                if self.circuit.valid_for_simulation() > 0:

                    if any_grid_delta and not any_normal_grid:
                        # only grid deltas...
                        self.open_file_now(filenames=file_names,
                                           post_function=self.post_import_circuit)
                    else:
                        quit_msg = ("Are you sure that you want to quit the current grid and open a new one?"
                                    "\n If the process is cancelled the grid will remain.")
                        reply = QtWidgets.QMessageBox.question(self, 'Message', quit_msg,
                                                               QtWidgets.QMessageBox.StandardButton.Yes,
                                                               QtWidgets.QMessageBox.StandardButton.No)

                        if reply == QtWidgets.QMessageBox.StandardButton.Yes.value:
                            self.open_file_now(filenames=file_names)
                else:
                    # Just open the file
                    self.open_file_now(filenames=file_names)

    def new_project_now(self, create_default_diagrams=True):
        """
        New project right now without asking questions
        """
        # clear the circuit model
        self.circuit = MultiCircuit()

        # clear the file name
        self.file_name = ''

        self.remove_all_diagrams()

        self.setup_objects_tree()

        # clear the results
        self.ui.resultsTableView.setModel(None)
        self.ui.resultsLogsTreeView.setModel(None)

        # clear the comments
        self.ui.comments_textEdit.setText("")

        self.ui.grid_name_line_edit.setText("")

        # clear the simulation objects
        for thread in self.get_all_threads():
            thread = None

        if self.analysis_dialogue is not None:
            self.analysis_dialogue.close()

        self.clear_stuff_running()
        self.clear_results()

        if create_default_diagrams:
            self.add_complete_bus_branch_diagram()
            self.add_map_diagram()
            self.set_diagram_widget(self.diagram_widgets_list[0])

        self.collect_memory()

    def new_project(self):
        """
        Create new grid
        :return:
        """
        if self.circuit.valid_for_simulation() > 0:
            quit_msg = "Are you sure that you want to quit the current grid and create a new one?"
            reply = QtWidgets.QMessageBox.question(self, 'Message', quit_msg,
                                                   QtWidgets.QMessageBox.StandardButton.Yes,
                                                   QtWidgets.QMessageBox.StandardButton.No)

            if reply == QtWidgets.QMessageBox.StandardButton.Yes.value:
                self.new_project_now(create_default_diagrams=True)

    def open_file(self):
        """
        Open VeraGrid file
        @return:
        """
        if ('file_save' not in self.stuff_running_now) and ('file_open' not in self.stuff_running_now):
            if self.circuit.valid_for_simulation() > 0:
                quit_msg = ("Are you sure that you want to quit the current grid and open a new one?"
                            "\n If the process is cancelled the grid will remain.")
                reply = QtWidgets.QMessageBox.question(self, 'Message', quit_msg,
                                                       QtWidgets.QMessageBox.StandardButton.Yes,
                                                       QtWidgets.QMessageBox.StandardButton.No)

                if reply == QtWidgets.QMessageBox.StandardButton.Yes.value:
                    self.open_file_threaded()
                else:
                    pass
            else:
                # Just open the file
                self.open_file_threaded()

        else:
            warning_msg('There is a file being processed now.')

    def open_file_threaded(self, post_function=None,
                           allow_diff_file_format: bool = False,
                           title: str = 'Open file'):
        """
        Open file from a Qt thread to remain responsive
        :param post_function: Any function to run after
        :param allow_diff_file_format: Allow loading VeraGrid diff files?
        :param title: Title of the open window
        """

        files_types = "*.gridcal *.veragrid "

        if allow_diff_file_format:
            files_types += "*.dgridcal *.dveragrid "

        files_types += "*.gch5 *.xlsx *.xls *.sqlite *.dgs *.iidm *.xiidm"
        files_types += "*.m *.matpower *.raw *.RAW *.rawx *.uct *.json *.ejson2 *.ejson3 *.xml "
        files_types += "*.zip *.dpx *.pwf *.epc *.EPC *.nc *.hdf5 *.p"

        dialogue = QtWidgets.QFileDialog(None,
                                         caption=title,
                                         directory=self.project_directory,
                                         filter=f"Formats ({files_types})")

        if dialogue.exec():
            filenames = dialogue.selectedFiles()
            self.open_file_now(filenames, post_function)

    def open_file_now(self, filenames: Union[str, List[str]],
                      post_function: Union[None, Callable[[], None]] = None,
                      bool_prompt_to_ask_if_unclear: bool = True) -> None:
        """
        Open a file without questions
        :param filenames: list of file names (maybe more than one because of CIM TP and EQ files)
        :param post_function: function callback
        :param bool_prompt_to_ask_if_unclear: if the extension is ambiguous like xml, zip or json, ask what to do
        :return: Nothing
        """
        if len(filenames) > 0:

            for f_name in filenames:
                if not os.path.exists(f_name):
                    error_msg(text=f"The file does not exists :( \n {f_name}", title="File opening")
                    return

            self.file_name = filenames[0]

            # store the working directory
            self.project_directory = os.path.dirname(self.file_name)

            # lock the ui
            self.LOCK()

            options = filedrv.FileOpenOptions()

            file_name = filenames if len(filenames) > 1 else filenames[0]

            # try to determine the file type
            options.file_type = determine_file_type(file_name)

            if options.file_type is None and bool_prompt_to_ask_if_unclear:
                self.file_selector = FileTypeSelector(file_name=file_name)
                self.file_selector.exec()
                options.file_type = self.file_selector.file_type

                if options.file_type == FileType.CGMES:
                    self.cgmes_selector = CgmesOptionsSelector()
                    self.cgmes_selector.exec()
                    options.cgmes_version = self.cgmes_selector.version

            elif options.file_type == FileType.PSSE_raw or options.file_type == FileType.PSSE_rawx:
                self.psse_import_dialogue = PsseImportDialogue(app=self, options=options)
                self.psse_import_dialogue.exec()
                # NOTE: options will be modified inside

            # create thread
            self.open_file_thread_object = filedrv.FileOpenThread(
                file_name=file_name,
                previous_circuit=self.circuit,
                options=options
            )

            # make connections
            self.open_file_thread_object.progress_signal.connect(self.ui.progressBar.setValue)
            self.open_file_thread_object.progress_text.connect(self.ui.progress_label.setText)
            self.open_file_thread_object.done_signal.connect(self.UNLOCK)

            if post_function is None:
                self.open_file_thread_object.done_signal.connect(self.post_open_file)
            else:
                self.open_file_thread_object.done_signal.connect(post_function)

            # thread start
            self.open_file_thread_object.start()

            # register as the latest file driver
            self.last_file_driver = self.open_file_thread_object

            # register thread
            self.stuff_running_now.append(SimulationTypes.FileOpen)

    def post_open_file(self) -> None:
        """
        Actions to perform after a file has been loaded
        """

        self.stuff_running_now.remove(SimulationTypes.FileOpen)

        if self.open_file_thread_object is not None:

            if self.open_file_thread_object.valid:

                # assign the loaded circuit
                self.new_project_now(create_default_diagrams=False)

                if self.open_file_thread_object.multiverse is not None:
                    # A multiverse file already contains the complete scenario tree and active
                    # scenario. Reassigning through self.circuit would rebuild a fresh
                    # single-root MultiVerse and discard the loaded multiverse information.
                    self.multiverse = self.open_file_thread_object.multiverse
                    self.ui.activeScenarioLabel.setText(f"Current: {self.circuit.name}")
                    self.file_name = self.open_file_thread_object.file_name

                elif self.open_file_thread_object.circuit is not None:
                    self.circuit = self.open_file_thread_object.circuit
                    self.file_name = self.open_file_thread_object.file_name

                if self.circuit.has_diagrams():
                    # create the diagrams that came with the file
                    if self.open_file_thread_object.multiverse is not None:
                        self.reload_diagrams_for_active_scenario()
                    else:
                        self.create_circuit_stored_diagrams()

                else:
                    if self.circuit.get_bus_number() > 300:
                        self.show_info_toast("The grid is quite big, no diagram is automatically created",
                                             duration=5000)

                    else:
                        # create schematic
                        self.add_complete_bus_branch_diagram()

                # set base magnitudes
                self.ui.sbase_doubleSpinBox.setValue(self.circuit.Sbase)
                self.ui.fbase_doubleSpinBox.setValue(self.circuit.fBase)

                # set circuit comments
                try:
                    self.ui.comments_textEdit.setText(str(self.circuit.comments))
                except ValueError:
                    pass

                # update the drop-down menus that display dates
                self.update_date_dependent_combos()
                self.update_from_to_list_views()

                # get the session tree structure
                session_data_dict = self.open_file_thread_object.get_session_tree()
                mdl = gf.get_tree_model(session_data_dict, 'Sessions')
                self.ui.diskSessionsTreeView.setModel(mdl)

                # apply the GUI settings if found:
                gui_config_data = self.open_file_thread_object.json_files.get('gui_config', None)
                if gui_config_data is not None:
                    self.apply_gui_config(data=gui_config_data)

                # clear the results
                self.clear_results()

                self.ui.grid_name_line_edit.setText(self.circuit.name)

                # if this was a CGMES file, launch the Rosetta GUI
                if self.open_file_thread_object.options.file_type == FileType.CGMES:

                    show_rosetta = yes_no_question(title="Show rosetta",
                                                   text="Do you want to open the Rosetta CGMEs browser?")

                    if show_rosetta:
                        self.rosetta_gui = RosetaExplorerGUI()
                        self.rosetta_gui.set_grid_model(self.open_file_thread_object.cgmes_circuit)
                        self.rosetta_gui.set_logger(self.open_file_thread_object.cgmes_logger)
                        self.rosetta_gui.update_combo_boxes()
                        self.rosetta_gui.show()
                    else:
                        # else, show the logger if it is necessary
                        if len(self.open_file_thread_object.logger) > 0:
                            dlg = LogsDialogue('Open CGMES file logger', self.open_file_thread_object.logger)
                            dlg.exec()

                else:
                    # else, show the logger if it is necessary
                    if len(self.open_file_thread_object.logger) > 0:
                        dlg = LogsDialogue('Open file logger', self.open_file_thread_object.logger)
                        dlg.exec()

            else:
                warning_msg(text='Error while loading the file(s)')
                # else, show the logger if it is necessary
                if len(self.open_file_thread_object.logger) > 0:
                    dlg = LogsDialogue('Open file logger', self.open_file_thread_object.logger)
                    dlg.exec()
        else:
            # center nodes
            diagram = self.get_selected_diagram_widget()
            if diagram is not None:
                if isinstance(diagram, SchematicWidget):
                    diagram.center_nodes()

        self.collect_memory()
        self.setup_time_sliders()
        self.get_circuit_snapshot_datetime()
        self.change_theme_mode()

    def install_plugin_now(self, file_name: str):
        """
        Install plugin
        :param file_name: name of the plugin
        """
        if file_name.endswith('.vgplugin'):
            info = get_plugin_info(file_name)

            if info is not None:

                if not info.is_compatible():
                    error_msg(f"{info.name} {info.version} requires VeraGrid {info.veragrid_version}",
                              "Plugin install")
                    return

                # search for the plugin
                for key, plugin in self.plugins_info.plugins.items():
                    if plugin.name == info.name:

                        ok = yes_no_question(f"There is a plugin already: "
                                             f"{plugin.name} {plugin.version} "
                                             f"The new plugin is {info.version}. "
                                             f"Install?", "Plugin install")
                        if not ok:
                            return
                        else:
                            break

                install_plugin(file_name)
                self.add_plugins()
                info_msg(f"{info.name} {info.version} installed!", "Plugin install")
            else:
                error_msg("There is no manifest :(", "Plugin install")
        else:
            error_msg("Does not seem to be a plugin :/", "Plugin install")

    def select_csv_file(self, caption='Open CSV file'):
        """
        Select a CSV file
        :return: csv file path
        """
        files_types = "CSV (*.csv)"

        filename, type_selected = QtWidgets.QFileDialog.getOpenFileName(parent=self,
                                                                        caption=caption,
                                                                        dir=self.project_directory,
                                                                        filter=files_types)

        if len(filename) > 0:
            return filename
        else:
            return None

    def import_circuit(self):
        """
        Prompt to add another circuit
        """
        self.open_file_threaded(post_function=self.post_import_circuit,
                                allow_diff_file_format=True)

    def post_import_circuit(self):
        """
        Stuff to do after opening another circuit
        :return: Nothing
        """
        self.stuff_running_now.remove(SimulationTypes.FileOpen)

        if self.open_file_thread_object is not None:

            new_circuit = self.open_file_thread_object.circuit

            if len(self.open_file_thread_object.logger) > 0:
                dlg = LogsDialogue('Open file logger',
                                   self.open_file_thread_object.logger)
                dlg.exec()

            if self.open_file_thread_object.valid:

                merge_dlg = GridMergeDialogue(grid=self.circuit, diff=new_circuit)
                merge_dlg.exec_()

                if merge_dlg.added_grid:
                    # Create a blank diagram and add to it
                    # logger = self.circuit.add_circuit(new_circuit)

                    # for sure, we want to add to the current schematic
                    diagram_widget = self.get_selected_diagram_widget()

                elif merge_dlg.merged_grid:

                    dlg3 = CustomQuestionDialogue(title="Grid merge",
                                                  question="How do you want to represent the merged grid?",
                                                  answer1="Create new diagram",
                                                  answer2="Add to current diagram")
                    dlg3.exec()

                    if dlg3.accepted_answer == 1:
                        # Create a blank diagram and add to it
                        diagram_widget = self.create_blank_schematic_diagram(name=new_circuit.name)

                    elif dlg3.accepted_answer == 2:
                        diagram_widget = self.get_selected_diagram_widget()

                    else:
                        # not imported
                        return

                    if diagram_widget is not None:
                        if isinstance(diagram_widget, SchematicWidget):
                            injections_by_bus = new_circuit.get_injection_devices_grouped_by_bus()
                            injections_by_fluid_node = new_circuit.get_injection_devices_grouped_by_fluid_node()

                            diagram_widget.add_elements_to_schematic(buses=new_circuit.buses,
                                                                     lines=new_circuit.lines,
                                                                     dc_lines=new_circuit.dc_lines,
                                                                     transformers2w=new_circuit.transformers2w,
                                                                     transformers3w=new_circuit.transformers3w,
                                                                     transformers_nw=new_circuit.transformers_nw,
                                                                     hvdc_lines=new_circuit.hvdc_lines,
                                                                     vsc_devices=new_circuit.vsc_devices,
                                                                     upfc_devices=new_circuit.upfc_devices,
                                                                     switches=new_circuit.switch_devices,
                                                                     fluid_nodes=new_circuit.fluid_nodes,
                                                                     fluid_paths=new_circuit.fluid_paths,
                                                                     injections_by_bus=injections_by_bus,
                                                                     injections_by_fluid_node=injections_by_fluid_node,
                                                                     explode_factor=1.0,
                                                                     prog_func=None,
                                                                     text_func=None)
                            diagram_widget.set_selected_buses(buses=new_circuit.buses)
                        else:
                            info_msg("No schematic diagram was selected...", title="Add to current diagram")

                else:
                    return

    def export_circuit_differential(self):
        """
        Prompt to export a diff of this circuit and a base one
        """
        dlg = GridDiffDialogue(grid=self.circuit)
        dlg.exec()

    def save_file_as(self):
        """
        Save this file as...
        """
        # by deleting the file_name, the save_file function will ask for it
        self.file_name = ''
        self.save_file()

    def save_file(self):
        """
        Save the circuit case to a file
        """

        if self.server_driver.is_running():
            instruction = RemoteInstruction(operation=SimulationTypes.NoSim)
            self.server_driver.send_job(grid=self.circuit, instruction=instruction)

        else:
            # declare the allowed file types
            files_types = "VeraGrid zip (*.veragrid)"

            # call dialog to select the file
            if self.project_directory is None:
                self.project_directory = ''

            # gather comments
            self.circuit.comments = self.ui.comments_textEdit.toPlainText()

            if self.file_name == '':
                # if the global file_name is empty, ask where to save
                fname = os.path.join(self.project_directory, self.ui.grid_name_line_edit.text())

                filename, type_selected = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                                'Save file',
                                                                                fname,
                                                                                files_types)

                if filename != '':

                    # if the user did not enter the extension, add it automatically
                    name, file_extension = os.path.splitext(filename)

                    if file_extension == '':
                        filename = name + ".veragrid"

                    # we were able to compose the file correctly, now save it
                    self.file_name = filename
                    options = self.get_file_save_options()
                    options.file_type = FileType.VeraGrid
                    self.save_file_now(
                        filename=self.file_name,
                        type_selected=type_selected,
                        options=options,
                    )
            else:
                # save directly
                self.save_file_now(filename=self.file_name)

    def get_file_save_options(self) -> filedrv.FileSavingOptions:
        """
        Compose the file saving options
        :return: FileSavingOptions
        """

        # get save data
        sessions_data = self.session.get_save_data() if self.ui.saveResultsCheckBox.isChecked() else list()

        # get json files to store
        json_files = {"gui_config": self.get_gui_config_data()}

        options = filedrv.FileSavingOptions(
            sessions_data=sessions_data,
            dictionary_of_json_files=json_files,
        )

        return options

    def save_file_now(self, filename: str,
                      type_selected: str = "",
                      grid: Union[MultiCircuit, None] = None,
                      options: filedrv.FileSavingOptions | None = None):
        """
        Save the file right now, without questions
        :param filename: filename to save to
        :param type_selected: File type description as it appears
                              in the file saving dialogue i.e. VeraGrid zip (*.veragrid)
        :param grid: MultiCircuit or None, if None, self.circuit is taken
        :param options: FileSavingOptions to override the default ones
        """

        if ((SimulationTypes.FileSave not in self.stuff_running_now) and
                (SimulationTypes.FileOpen not in self.stuff_running_now)):
            # lock the ui
            self.LOCK()

            # check not to kill threads avoiding segmentation faults
            if self.save_file_thread_object is not None:
                if self.save_file_thread_object.isRunning():
                    ok = yes_no_question("There is a saving procedure running.\nCancel and retry?")
                    if ok:
                        self.save_file_thread_object.quit()

            options2 = self.get_file_save_options() if options is None else options
            options2.type_selected = type_selected

            self.save_file_thread_object = filedrv.FileSaveThread(
                circuit=self.circuit if grid is None else grid,
                multiverse=self.multiverse,
                file_name=filename,
                options=options2
            )

            # make connections
            self.save_file_thread_object.progress_signal.connect(self.ui.progressBar.setValue)
            self.save_file_thread_object.progress_text.connect(self.ui.progress_label.setText)
            self.save_file_thread_object.done_signal.connect(self.UNLOCK)
            self.save_file_thread_object.done_signal.connect(self.post_file_save)

            # thread start
            self.save_file_thread_object.start()

            # register as the latest file driver
            self.last_file_driver = self.save_file_thread_object

            self.stuff_running_now.append(SimulationTypes.FileSave)

        else:
            warning_msg('There is a file being processed..')

    def post_file_save(self):
        """
        Actions after the threaded file save
        """
        if self.save_file_thread_object.logger is not None:
            if len(self.save_file_thread_object.logger) > 0:
                dlg = LogsDialogue('Save file logger', self.save_file_thread_object.logger)
                dlg.exec()

        self.stuff_running_now.remove(SimulationTypes.FileSave)

        self.ui.model_version_label.setText('Model v. ' + str(self.circuit.model_version))
        self.ui.grid_idtag_label.setText('idtag. ' + str(self.circuit.idtag))

        # get the session tree structure
        session_data_dict = self.save_file_thread_object.get_session_tree()
        mdl = gf.get_tree_model(session_data_dict, 'Sessions')
        self.ui.diskSessionsTreeView.setModel(mdl)

        # call the garbage collector to free memory
        self.collect_memory()

    def grid_generator(self):
        """
        Open the grid generator window
        """
        self.grid_generator_dialogue = GridGeneratorGUI(parent=self)
        self.grid_generator_dialogue.resize(int(1.61 * 600.0), 550)  # golden ratio
        self.grid_generator_dialogue.exec()

        if self.grid_generator_dialogue.applied:

            if self.circuit.valid_for_simulation() > 0:
                reply = QtWidgets.QMessageBox.question(self, 'Message',
                                                       'Are you sure that you want to delete_with_dialogue '
                                                       'the current grid and replace it?',
                                                       QtWidgets.QMessageBox.StandardButton.Yes,
                                                       QtWidgets.QMessageBox.StandardButton.No)

                if reply == QtWidgets.QMessageBox.StandardButton.No:
                    return

            self.circuit = self.grid_generator_dialogue.circuit

            # create schematic
            self.redraw_current_diagram()

            # set circuit name
            diagram = self.get_selected_diagram_widget()
            if diagram is not None:
                if isinstance(diagram, SchematicWidget):
                    diagram.name = f"Random grid {self.circuit.get_bus_number()} buses"

            # set base magnitudes
            self.ui.sbase_doubleSpinBox.setValue(self.circuit.Sbase)
            self.ui.fbase_doubleSpinBox.setValue(self.circuit.fBase)
            self.ui.model_version_label.setText(f"Model v. {self.circuit.model_version}")
            self.ui.grid_idtag_label.setText('idtag. ' + str(self.circuit.idtag))

            # set circuit comments
            self.ui.comments_textEdit.setText("Grid generated randomly using the RPGM algorithm.")

            # update the drop down menus that display dates
            self.update_date_dependent_combos()
            self.update_from_to_list_views()

            # clear the results
            self.clear_results()

    def import_bus_coordinates(self):
        """

        :return:
        """
        self.coordinates_window = CoordinatesInputGUI(self, self.circuit.get_buses())
        self.coordinates_window.exec()
        self.set_xy_from_lat_lon()

    def export_object_profiles(self):
        """
        Export object profiles
        """
        if self.circuit.time_profile is not None:

            # declare the allowed file types
            files_types = "Excel file (*.xlsx)"
            # call dialog to select the file
            if self.project_directory is None:
                self.project_directory = ''

            fname = os.path.join(self.project_directory, 'profiles of ' + self.ui.grid_name_line_edit.text())

            filename, type_selected = QtWidgets.QFileDialog.getSaveFileName(self, 'Save file', fname, files_types)

            if filename != "":
                if not filename.endswith('.xlsx'):
                    filename += '.xlsx'
                # TODO: correct this function
                self.circuit.export_profiles(file_name=filename)
        else:
            warning_msg('There are no profiles!', 'Export object profiles')

    def export_all(self):
        """
        Export all the results
        :return:
        """

        available_results = self.get_available_drivers()

        if len(available_results) > 0:

            files_types = "Zip file (*.zip)"
            fname = os.path.join(self.project_directory, 'Results of ' + self.ui.grid_name_line_edit.text())

            filename, type_selected = QtWidgets.QFileDialog.getSaveFileName(self, 'Save file', fname, files_types)

            if filename != "":
                self.LOCK()

                self.stuff_running_now.append(SimulationTypes.ExportAll)
                self.export_all_thread_object = exprtdrv.ExportAllThread(circuit=self.circuit,
                                                                         drivers_list=available_results,
                                                                         file_name=filename)

                self.export_all_thread_object.progress_signal.connect(self.ui.progressBar.setValue)
                self.export_all_thread_object.progress_text.connect(self.ui.progress_label.setText)
                self.export_all_thread_object.done_signal.connect(self.post_export_all)
                self.export_all_thread_object.start()
        else:
            warning_msg('There are no result available :/')

    def post_export_all(self):
        """
        Actions post export all
        """
        self.stuff_running_now.remove(SimulationTypes.ExportAll)

        if self.export_all_thread_object is not None:
            if self.export_all_thread_object.logger.has_logs():
                self.show_logs(name='Export all',
                               logger=self.export_all_thread_object.logger)

        if len(self.stuff_running_now) == 0:
            self.UNLOCK()

    def export_simulation_data(self):
        """
        Export the calculation objects to file
        """

        # declare the allowed file types
        files_types = "Excel file (*.xlsx)"

        # call dialog to select the file
        if self.project_directory is None:
            self.project_directory = ''

        fname = os.path.join(self.project_directory, self.ui.grid_name_line_edit.text())

        filename, type_selected = QtWidgets.QFileDialog.getSaveFileName(self, 'Save file', fname, files_types)

        if filename != "":
            if not filename.endswith('.xlsx'):
                filename += '.xlsx'

            if self.compiled_arrays is None:
                self.recompile_circuits_for_display()

            self.compiled_arrays.export_to_excel(file_name=filename)

            self.show_info_toast("Done!")

    def load_results_driver(self):
        """
        Load a driver from disk
        """
        idx = self.ui.diskSessionsTreeView.selectedIndexes()
        if len(idx) > 0:
            tree_mdl = self.ui.diskSessionsTreeView.model()
            item = tree_mdl.itemFromIndex(idx[0])
            path = gf.get_tree_item_path(item)

            if len(path) > 1:
                session_name = path[0]
                study_name = path[1]
                if self.last_file_driver is not None:
                    data_dict = self.last_file_driver.load_session_objects(session_name=session_name,
                                                                           study_name=study_name)

                    logger = self.session.register_driver_from_disk_data(grid=self.circuit,
                                                                         study_name=study_name,
                                                                         data_dict=data_dict)

                    if logger.has_logs():
                        self.show_logs(name="Results parsing", logger=logger, expand_all=True)

                    self.update_available_results()
                else:
                    error_msg('No file driver declared :/')
            else:
                info_msg('Select a driver inside a session', 'Driver load from disk')

    def import_contingencies(self):
        """
        Open file to import contingencies file
        """

        files_types = "Formats (*.json)"

        # call dialog to select the file

        filenames, type_selected = QtWidgets.QFileDialog.getOpenFileNames(parent=self,
                                                                          caption='Open file',
                                                                          dir=self.project_directory,
                                                                          filter=files_types)

        if len(filenames) == 1:
            contingencies = import_contingencies_from_json(filenames[0])
            logger = self.circuit.set_contingencies(contingencies=contingencies)

            if len(logger) > 0:
                dlg = LogsDialogue('Contingencies import', logger)
                dlg.exec()

    def export_contingencies(self):
        """
        Export contingencies
        :return:
        """
        if len(self.circuit.contingencies) > 0:

            # declare the allowed file types
            files_types = "JSON file (*.json)"

            # call dialog to select the file
            filename, type_selected = QtWidgets.QFileDialog.getSaveFileName(self, 'Save file', '', files_types)

            if not (filename.endswith('.json')):
                filename += ".json"

            if filename != "":
                # save file
                export_contingencies_json_file(circuit=self.circuit, file_path=filename)

    def add_default_catalogue(self) -> None:
        """
        Add default catalogue to circuit
        """

        for tpe in get_transformer_catalogue():
            self.circuit.add_transformer_type(tpe)

        for tpe in get_cables_catalogue():
            self.circuit.add_underground_line(tpe)

        for tpe in get_wires_catalogue():
            self.circuit.add_wire(tpe)

        for tpe in get_sequence_lines_catalogue():
            self.circuit.add_sequence_line(tpe)

        if not self.circuit.rms_models:
            self.circuit.add_rms_model_catalogue()
        else:
            self.circuit.rms_models = list()
            self.circuit.add_rms_model_catalogue()

        if not self.circuit.emt_models:
            self.circuit.add_emt_model_catalogue()
        else:
            self.circuit.emt_models = list()
            self.circuit.add_emt_model_catalogue()

        self.show_info_toast("Catalogue added!")

    def load_custom_catalogue(self):
        """
        Load a catalogue file and add it to the current one
        """
        # this will be filled with: open dialogue tab only, then connect select_csv_file from there
        """
        Open select component window for uploading catalogue data
        """

        files_types = "Catalogue file (*.xlsx)"

        filename, type_selected = QtWidgets.QFileDialog.getOpenFileName(parent=self,
                                                                        caption="Load catalogue",
                                                                        dir=self.project_directory,
                                                                        filter=files_types)

        if len(filename) > 0:
            if os.path.exists(filename):

                data, logger = load_catalogue(fname=filename)

                if logger.has_logs():
                    self.show_logs(name='Open catalogue logger', logger=logger)

                self.circuit.add_catalogue(data)
                self.show_info_toast("Catalogue loaded!")
            return None
        else:
            return None

    def save_custom_catalogue(self):
        """
        Save the current catalogue
        """

        # declare the allowed file types
        files_types = "Catalogue Excel file (*.xlsx)"

        # call dialog to select the file
        filename, type_selected = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                        'Save catalogue',
                                                                        '',
                                                                        files_types)
        if filename != "":
            if not (filename.endswith('.xlsx')):
                filename += ".xlsx"

            save_catalogue(fname=filename, grid=self.circuit)
            self.show_info_toast("Catalogue saved!")

    def set_circuit(self, grid: MultiCircuit, create_diagram: bool = True):
        """

        :param grid:
        :param create_diagram:
        :return:
        """
        self.remove_all_diagrams()

        self.circuit = grid

        if create_diagram:
            self.add_complete_bus_branch_diagram()

        self.update_date_dependent_combos()
        self.update_from_to_list_views()
        self.clear_results()
        self.collect_memory()
        self.setup_time_sliders()
        self.get_circuit_snapshot_datetime()
        self.change_theme_mode()

    def export_psse(self):
        """

        :return:
        """
        self.psse_export_dialogue = PsseExportDialogue(app=self)
        self.psse_export_dialogue.show()

    def export_power_factory(self):
        """

        :return:
        """
        # if the global file_name is empty, ask where to save
        fname = os.path.join(self.project_directory, self.ui.grid_name_line_edit.text())

        files_types = "Power Factory (*.dgs)"
        filename, type_selected = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                        'Export to Power Factory',
                                                                        fname,
                                                                        files_types)

        if filename != '':

            # if the user did not enter the extension, add it automatically
            name, file_extension = os.path.splitext(filename)

            if file_extension == '':
                filename = name + '.dgs'

            # we were able to compose the file correctly, now save it
            self.file_name = filename
            self.save_file_now(
                filename=self.file_name,
                type_selected=type_selected,
                options=FileSavingOptions(
                    file_type=FileType.DGS
                )
            )

    def export_cim(self):
        """

        :return:
        """
        # if the global file_name is empty, ask where to save
        fname = os.path.join(self.project_directory, self.ui.grid_name_line_edit.text())

        files_types = "CIM (*.xml)"
        filename, type_selected = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                        'Export to CIM',
                                                                        fname,
                                                                        files_types)

        if filename != '':

            # if the user did not enter the extension, add it automatically
            name, file_extension = os.path.splitext(filename)

            if file_extension == '':
                filename = name + '.xml'

            # we were able to compose the file correctly, now save it
            self.file_name = filename
            self.save_file_now(
                filename=self.file_name,
                type_selected=type_selected,
                options=FileSavingOptions(
                    file_type=FileType.CIM
                )
            )

    def export_cgmes(self):
        """

        :return:
        """
        self.cgmes_dialogue = CgmesExportDialogue(app=self)
        self.cgmes_dialogue.show()

    def export_power_grid_models(self):
        """

        :return:
        """

        if PGM_AVAILABLE:
            # if the global file_name is empty, ask where to save
            fname = os.path.join(self.project_directory, self.ui.grid_name_line_edit.text())

            files_types = "Power Grid Models (*.pgm)"
            filename, type_selected = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                            'Export to Power Grid Models',
                                                                            fname,
                                                                            files_types)

            if filename != '':

                # if the user did not enter the extension, add it automatically
                name, file_extension = os.path.splitext(filename)

                if file_extension == '':
                    filename = name + '.pgm'

                # we were able to compose the file correctly, now save it
                self.file_name = filename
                self.save_file_now(
                    filename=self.file_name,
                    type_selected=type_selected,
                    options=FileSavingOptions(
                        file_type=FileType.PGM
                    )
                )
        else:
            self.show_warning_toast("Power Grid Models not installed :/")

    def export_json(self):
        """

        :return:
        """
        # if the global file_name is empty, ask where to save
        fname = os.path.join(self.project_directory, self.ui.grid_name_line_edit.text())

        files_types = "Electrical Json V3 (*.ejson3)"
        filename, type_selected = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                        'Export to JSON',
                                                                        fname,
                                                                        files_types)

        if filename != '':

            # if the user did not enter the extension, add it automatically
            name, file_extension = os.path.splitext(filename)

            if file_extension == '':
                filename = name + '.ejson3'

            # we were able to compose the file correctly, now save it
            self.file_name = filename
            self.save_file_now(
                filename=self.file_name,
                type_selected=type_selected,
                options=FileSavingOptions(
                    file_type=FileType.VeraGrid_json
                )
            )

    def export_h5(self):
        """

        :return:
        """
        # if the global file_name is empty, ask where to save
        fname = os.path.join(self.project_directory, self.ui.grid_name_line_edit.text())

        files_types = "VeraGrid HDF5 (*.gch5)"
        filename, type_selected = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                        'Export to VeraGrid HDF5',
                                                                        fname,
                                                                        files_types)

        if filename != '':

            # if the user did not enter the extension, add it automatically
            name, file_extension = os.path.splitext(filename)

            if file_extension == '':
                filename = name + '.gch5'

            # we were able to compose the file correctly, now save it
            self.file_name = filename
            self.save_file_now(
                filename=self.file_name,
                type_selected=type_selected,
                options=FileSavingOptions(
                    file_type=FileType.VeraGrid_h5
                )
            )

    def export_excel(self):
        """

        :return:
        """
        # if the global file_name is empty, ask where to save
        fname = os.path.join(self.project_directory, self.ui.grid_name_line_edit.text())

        files_types = "Excel (*.xlsx)"
        filename, type_selected = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                        'Export to Microsoft Excel',
                                                                        fname,
                                                                        files_types)

        if filename != '':

            # if the user did not enter the extension, add it automatically
            name, file_extension = os.path.splitext(filename)

            if file_extension == '':
                filename = name + '.xlsx'

            # we were able to compose the file correctly, now save it
            self.file_name = filename
            self.save_file_now(
                filename=self.file_name,
                type_selected=type_selected,
                options=FileSavingOptions(
                    file_type=FileType.VeraGrid_xlsx4
                )
            )

    def export_sqlite(self):
        """

        :return:
        """
        # if the global file_name is empty, ask where to save
        fname = os.path.join(self.project_directory, self.ui.grid_name_line_edit.text())

        files_types = "Sqlite (*.sqlite)"
        filename, type_selected = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                        'Export to Sqlite',
                                                                        fname,
                                                                        files_types)

        if filename != '':

            # if the user did not enter the extension, add it automatically
            name, file_extension = os.path.splitext(filename)

            if file_extension == '':
                filename = name + '.sqlite'

            # we were able to compose the file correctly, now save it
            self.file_name = filename
            self.save_file_now(
                filename=self.file_name,
                type_selected=type_selected,
                options=FileSavingOptions(
                    file_type=FileType.VeraGrid_sqlite
                )
            )
