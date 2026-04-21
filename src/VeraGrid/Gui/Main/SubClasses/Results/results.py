# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
from PySide6 import QtCore, QtWidgets, QtGui
from matplotlib import pyplot as plt
from typing import Union, Dict

from VeraGrid.Gui.Main.dynamics_results_handler import DynamicsResultsHandler
from VeraGrid.Gui.table_view_header_wrap import HeaderViewWithWordWrap
import VeraGrid.Gui.gui_functions as gf
from VeraGrid.Gui.messages import error_msg, warning_msg, yes_no_question
from VeraGrid.Gui.Main.SubClasses.simulations import SimulationsMain
from VeraGrid.Gui.results_model import ResultsModel
from VeraGrid.Gui.general_dialogues import fill_tree_from_logs
import VeraGridEngine.Utils.Filtering as flt
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import ResultTypes, SimulationTypes
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Simulations.Rms.rms_results import RmsResults
from VeraGridEngine.Simulations.EMT.emt_results import EmtResults


class ResultsMain(SimulationsMain):
    """
    Diagrams Main
    """

    def __init__(self, parent=None):
        """

        @param parent:
        """

        # create main window
        SimulationsMain.__init__(self, parent)

        self.results_mdl: Union[None, ResultsModel] = None

        self.current_results_logger: Union[None, Logger] = None

        self.dynamic_results_handler: DynamicsResultsHandler | None = None
        self.dynamic_results_handlers: Dict[str, DynamicsResultsHandler] = dict()

        # --------------------------------------------------------------------------------------------------------------
        self.ui.actionSet_OPF_generation_to_profiles.triggered.connect(self.copy_opf_to_profiles)

        # Buttons
        self.ui.saveResultsButton.clicked.connect(self.save_results_df)
        self.ui.copy_results_pushButton.clicked.connect(self.copy_results_data)
        self.ui.copy_numpy_button.clicked.connect(self.copy_results_data_as_numpy)
        self.ui.plot_data_pushButton.clicked.connect(self.plot_results)
        self.ui.search_results_Button.clicked.connect(self.search_in_results)
        self.ui.search_dynamic_objects_Button.clicked.connect(self.search_dynamic_objects)
        self.ui.addDynamicPlotButton.clicked.connect(self.add_dynamic_plot_group)
        self.ui.deleteDynamicPlotButton.clicked.connect(self.delete_dynamic_plot_entry)
        self.ui.dynamicsTablePlotButton.clicked.connect(self.plot_dynamic_plot_entry)
        self.ui.deleteDriverButton.clicked.connect(self.delete_results_driver)
        self.ui.saveResultsLogsButton.clicked.connect(self.save_results_logs)

        # tree-click
        self.ui.results_treeView.clicked.connect(self.results_tree_view_click)
        self.ui.dynamicsDeviceTreeView.clicked.connect(self.dynamic_results_tree_view_click)
        self.ui.dynamicsPlotsTreeView.clicked.connect(self.dynamic_plots_tree_view_click)

        # tree double click
        self.ui.dynamicsDeviceTreeView.doubleClicked.connect(self.dynamic_results_tree_view_dbl_click)
        self.ui.dynamicsPlotsTreeView.doubleClicked.connect(self.dynamic_plots_tree_view_dbl_click)

        # line edit enter
        self.ui.search_results_lineEdit.returnPressed.connect(self.search_in_results)
        self.ui.search_dynamic_objects_lineEdit.returnPressed.connect(self.search_dynamic_objects)

        # wrap headers
        self.ui.resultsTableView.setHorizontalHeader(HeaderViewWithWordWrap(self.ui.resultsTableView))

        # The device tree exports variables through drag-and-drop.
        self.ui.dynamicsDeviceTreeView.setDragEnabled(True)
        self.ui.dynamicsDeviceTreeView.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.DragOnly)
        self.ui.dynamicsDeviceTreeView.setDefaultDropAction(QtCore.Qt.DropAction.CopyAction)

        # The plots tree accepts dropped variables into top-level plot groups.
        self.ui.dynamicsPlotsTreeView.setAcceptDrops(True)
        self.ui.dynamicsPlotsTreeView.setDropIndicatorShown(True)
        self.ui.dynamicsPlotsTreeView.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.DropOnly)
        self.ui.dynamicsPlotsTreeView.setDefaultDropAction(QtCore.Qt.DropAction.CopyAction)

    def results_tree_view_click(self, index: QtGui.QStandardItem):
        """
        Display the simulation results on the result's table
        :param index: Clicked Tree index
        """
        tree_mdl = self.ui.results_treeView.model()
        item = tree_mdl.itemFromIndex(index)
        path = gf.get_tree_item_path(item)

        if len(path) > 0:
            study_name = path[0]
            driver = self.session.get_driver_by_name(study_name=study_name)

            if driver is None:
                # set the logs
                self.current_results_logger = None
                self.ui.resultsLogsTreeView.setModel(None)
                return

            # set the logs
            self.current_results_logger = driver.logger
            logs_mdl = fill_tree_from_logs(driver.logger)
            self.ui.resultsLogsTreeView.setModel(logs_mdl)
            self.ui.resultsLogsTreeView.expandAll()

            # set the report
            self.ui.resultsReportTextEdit.setText(driver.results.report_text)

            # set the dynamics model handler
            if driver.tpe == SimulationTypes.RmsDynamic_run:
                self.dynamic_results_handler = self.get_or_create_dynamic_results_handler(
                    study_name=study_name,
                    results=driver.results
                )
                self.ui.eventsGroupComboBox.setModel(gf.get_list_model(
                    self.dynamic_results_handler.results.rms_events_group_names))

                self.ui.dynamicsDeviceTreeView.setModel(self.dynamic_results_handler.get_view_model())
                self.ui.dynamicsPlotsTreeView.setModel(self.dynamic_results_handler.get_plots_model())
                self.ui.dynamicsPlotsTreeView.expandAll()

                self.ui.resultsTabWidget.setCurrentIndex(1)


            elif driver.tpe == SimulationTypes.EmtDynamic_run:

                self.dynamic_results_handler = self.get_or_create_dynamic_results_handler(
                    study_name=study_name,
                    results=driver.results
                )
                self.ui.eventsGroupComboBox.setModel(gf.get_list_model(
                    self.dynamic_results_handler.results.emt_events_group_names))

                self.ui.dynamicsDeviceTreeView.setModel(self.dynamic_results_handler.get_view_model())
                self.ui.dynamicsPlotsTreeView.setModel(self.dynamic_results_handler.get_plots_model())
                self.ui.dynamicsPlotsTreeView.expandAll()
                self.ui.resultsTabWidget.setCurrentIndex(1)

            else:
                # Go to the Table tab
                self.ui.resultsTabWidget.setCurrentIndex(0)
                self.clear_dynamic_results_view()

            if len(path) > 1:

                if len(path) == 2:
                    result_name = path[1]
                elif len(path) == 3:
                    result_name = path[2]
                else:
                    raise Exception('Path len ' + str(len(path)) + ' not supported')

                study_results = self.available_results_dict.get(study_name, None)

                if study_results is not None:

                    study_type: ResultTypes = study_results.get(result_name, None)

                    if study_type is not None:

                        self.results_mdl = self.session.get_results_model_by_name(study_name=study_name,
                                                                                  study_type=study_type)

                        if self.results_mdl is not None:

                            # pass the matching list of devices to the ResultsModel and ResultsTable for filtering
                            self.results_mdl.table.set_col_devices(
                                devices_list=self.circuit.get_elements_by_type(self.results_mdl.table.cols_device_type)
                            )
                            self.results_mdl.table.set_idx_devices(
                                devices_list=self.circuit.get_elements_by_type(self.results_mdl.table.idx_device_type)
                            )

                            if self.ui.results_traspose_checkBox.isChecked():
                                self.results_mdl.transpose()

                            if self.ui.results_as_abs_checkBox.isChecked():
                                self.results_mdl.convert_to_abs()

                            if self.ui.results_as_cdf_checkBox.isChecked():
                                self.results_mdl.convert_to_cdf()

                            # set the table model
                            self.ui.resultsTableView.setModel(self.results_mdl)
                            self.ui.units_label.setText(self.results_mdl.units)

                        else:
                            self.ui.resultsTableView.setModel(None)
                            self.ui.units_label.setText("")

                    else:
                        self.ui.resultsTableView.setModel(None)
                        self.ui.units_label.setText("")

                else:
                    self.ui.resultsTableView.setModel(None)
                    self.ui.units_label.setText("")

            else:
                pass

        else:
            # set the logs
            self.current_results_logger = None
            self.ui.resultsLogsTreeView.setModel(None)

    def dynamic_results_tree_view_click(self, index: QtCore.QModelIndex) -> Var | None:
        """
        Resolve the clicked dynamics tree node into an RMS/EMT variable.

        :param index: Clicked tree index.
        """
        # The handler owns the mapping between tree nodes and simulation variable objects.
        if self.dynamic_results_handler is not None:
            source_index: QtCore.QModelIndex = self.dynamic_results_handler.map_to_source(index=index)
            selected_var = self.dynamic_results_handler.get_var_from_index(index=source_index)
            if selected_var is not None:
                print(selected_var)
                return selected_var
            else:
                return None
        else:
            return None

    def dynamic_results_tree_view_dbl_click(self, index: QtCore.QModelIndex) -> None:
        """

        :param index:
        :return:
        """
        # The handler owns the mapping between tree nodes and simulation variable objects.
        if self.dynamic_results_handler is not None:
            source_index: QtCore.QModelIndex = self.dynamic_results_handler.map_to_source(index=index)
            selected_var = self.dynamic_results_handler.get_var_from_index(index=source_index)
            if selected_var is not None:
                group_name = self.ui.eventsGroupComboBox.currentText()
                self.dynamic_results_handler.plot_var(var=selected_var, group_name=group_name)
                return None
            else:
                return None
        else:
            return None

    def dynamic_plots_tree_view_dbl_click(self, index: QtCore.QModelIndex) -> None:
        """
        Plot the selected plots-tree entry on double click.

        :param index:
        :return: Nothing.
        """
        del index
        self.plot_dynamic_plot_entry()

    def dynamic_plots_tree_view_click(self, index: QtCore.QModelIndex):
        """
        On dynamics plot tree click...
        :param index:
        :return:
        """
        if self.dynamic_results_handler is not None:
            selected_indexes = self.ui.dynamicsPlotsTreeView.selectedIndexes()
            if len(selected_indexes) > 0:
                group_name: str = self.ui.eventsGroupComboBox.currentText()
                mdl = self.dynamic_results_handler.get_data_from_plot_index(index=selected_indexes[0],
                                                                            rms_group_name=group_name)

                self.ui.dynamicsTableView.setModel(mdl)

    def expand_dynamic_plots_tree(self,
                                  parent: QtCore.QModelIndex,
                                  first: int,
                                  last: int) -> None:
        """
        Expand the dynamics plots tree after inserting rows.

        :param parent: Parent index where rows were inserted.
        :param first: First inserted row.
        :param last: Last inserted row.
        :return: Nothing.
        """
        del parent
        del first
        del last

        # Expanding after insert keeps dropped variables immediately visible inside their target plot group.
        self.ui.dynamicsPlotsTreeView.expandAll()

    def add_dynamic_plot_group(self) -> None:
        """
        Create a new dynamics plot group.

        :return: Nothing.
        """
        if self.dynamic_results_handler is not None:
            suggested_name: str = self.dynamic_results_handler.get_next_group_name()
            group_name, accepted = QtWidgets.QInputDialog.getText(self,
                                                                  "New dynamic plot",
                                                                  "Plot name",
                                                                  text=suggested_name)
            if accepted:
                created: bool = self.dynamic_results_handler.create_plot_group(name=group_name)
                if created:
                    self.ui.dynamicsPlotsTreeView.expandAll()
                else:
                    self.show_warning_toast("The plot group name is empty or already exists.")
            else:
                pass
        else:
            self.show_warning_toast("There are no RMS dynamics results loaded.")

    def delete_dynamic_plot_entry(self) -> None:
        """
        Delete the selected dynamics plot group or variable.

        :return: Nothing.
        """
        if self.dynamic_results_handler is not None:
            selected_indexes = self.ui.dynamicsPlotsTreeView.selectedIndexes()
            if len(selected_indexes) > 0:
                deleted: bool = self.dynamic_results_handler.delete_plot_entry_from_index(index=selected_indexes[0])
                if deleted:
                    self.ui.dynamicsPlotsTreeView.expandAll()
                else:
                    self.show_warning_toast("The selected dynamic plot entry could not be deleted.")
            else:
                self.show_warning_toast("Select a plot group or variable first.")
        else:
            self.show_warning_toast("There are no RMS dynamics results loaded.")

    def plot_dynamic_plot_entry(self) -> None:
        """
        Plot the selected dynamics plot group or variable.

        :return: Nothing.
        """
        if self.dynamic_results_handler is not None:
            selected_indexes = self.ui.dynamicsPlotsTreeView.selectedIndexes()
            if len(selected_indexes) > 0:
                group_name: str = self.ui.eventsGroupComboBox.currentText()
                plotted: bool = self.dynamic_results_handler.plot_entry_from_index(index=selected_indexes[0],
                                                                                   rms_group_name=group_name)
                if plotted:
                    return None
                else:
                    self.show_warning_toast("The selected dynamic plot entry could not be plotted.")
                    return None
            else:
                self.show_warning_toast("Select a plot group or variable first.")
                return None
        else:
            self.show_warning_toast("There are no RMS dynamics results loaded.")
            return None

    def search_dynamic_objects(self) -> None:
        """
        Filter the dynamics tree view using the text entered by the user.

        :return: Nothing.
        """
        # Without an active handler, there is no loaded dynamics tree to search.
        if self.dynamic_results_handler is not None:
            search_text: str = self.ui.search_dynamic_objects_lineEdit.text().strip()
            self.dynamic_results_handler.set_search_text(search_text=search_text)

            # Expanding after filtering keeps matching branches visible, and resetting the filter remains trivial.
            self.ui.dynamicsDeviceTreeView.expandAll()
        else:
            pass

    def get_or_create_dynamic_results_handler(self,
                                              study_name: str,
                                              results: RmsResults|EmtResults) -> DynamicsResultsHandler:
        """
        Get a cached dynamic-results handler for the given study, or create/update it.

        :param study_name: Study name shown in the results tree.
        :param results: Dynamic results object associated with the study.
        :return: Cached or newly created dynamics-results handler.
        """
        handler = self.dynamic_results_handlers.get(study_name, None)

        if handler is None:
            handler = DynamicsResultsHandler(results=results)
            self.dynamic_results_handlers[study_name] = handler
            handler.get_plots_model().rowsInserted.connect(self.expand_dynamic_plots_tree)
            return handler

        elif handler.results is results:
            return handler

        # elif handler.can_reuse_with_results(results=results): # NOT WORKING!
        # # Re-use already created dynamic plots for the same simulation but with some changes (events,etc) -> not working because uid changes
        #     handler.update_results(results=results)
        #     return handler
        else:

            handler = DynamicsResultsHandler(results=results)
            self.dynamic_results_handlers[study_name] = handler
            handler.get_plots_model().rowsInserted.connect(self.expand_dynamic_plots_tree)
            return handler

    def plot_results(self):
        """
        Plot the results
        """
        mdl: ResultsModel = self.ui.resultsTableView.model()

        if mdl is not None:

            plt.rcParams["date.autoformatter.minute"] = "%Y-%m-%d %H:%M:%S"

            # get the selected element
            obj_idx = self.ui.resultsTableView.selectedIndexes()
            n_cols = mdl.table.c

            if n_cols > 50:
                ok = yes_no_question(text=f"There are {n_cols} columns, the plot might take a lot to render.\n"
                                          "Are you ok with potentially waiting a lot?", title="Plot")
            else:
                ok = True

            if ok:
                # create figure to plot
                fig = plt.figure(figsize=(12, 8))
                ax = fig.add_subplot(111)

                if len(obj_idx):

                    # get the unique columns in the selected cells
                    cols = np.zeros(len(obj_idx), dtype=int)
                    rows = np.zeros(len(obj_idx), dtype=int)

                    for i in range(len(obj_idx)):
                        cols[i] = obj_idx[i].column()
                        rows[i] = obj_idx[i].row()

                    cols = np.unique(cols)
                    rows = np.unique(rows)

                else:
                    # plot all
                    cols = None
                    rows = None

                # none selected, plot all
                mdl.plot(
                    ax=ax,
                    selected_col_idx=cols,
                    selected_rows=rows,
                    stacked=self.ui.stacked_plot_checkBox.isChecked()
                )

                plt.show()
            else:
                pass

    def save_results_df(self):
        """
        Save the data displayed at the results as excel
        """
        mdl: ResultsModel = self.ui.resultsTableView.model()

        if mdl is not None:
            file, filter_ = QtWidgets.QFileDialog.getSaveFileName(self, "Export results", '',
                                                                  filter="CSV (*.csv);;Excel files (*.xlsx)")

            if file != '':
                if 'xlsx' in filter_:
                    f = file
                    if not f.endswith('.xlsx'):
                        f += '.xlsx'
                    mdl.save_to_excel(f)
                    print('Saved!')
                if 'csv' in filter_:
                    f = file
                    if not f.endswith('.csv'):
                        f += '.csv'
                    mdl.save_to_csv(f)
                    print('Saved!')
                else:
                    error_msg(file[0] + ' is not valid :(')
        else:
            warning_msg('There is no profile displayed, please display one', 'Copy profile to clipboard')

    def copy_results_data(self):
        """
        Copy the current displayed profiles to the clipboard
        """
        mdl = self.ui.resultsTableView.model()
        if mdl is not None:
            mdl.copy_to_clipboard()
            self.show_info_toast('Copied!')
        else:
            warning_msg('There is no profile displayed, please display one', 'Copy profile to clipboard')

    def copy_results_data_as_numpy(self):
        """
        Copy the current displayed profiles to the clipboard
        """
        mdl = self.ui.resultsTableView.model()
        if mdl is not None:
            mdl.copy_numpy_to_clipboard()
            self.show_info_toast('Copied!')
        else:
            warning_msg('There is no profile displayed, please display one', 'Copy profile to clipboard')

    def search_in_results(self):
        """
        Search in the results model
        """

        if self.results_mdl is not None:

            txt = self.ui.search_results_lineEdit.text().strip()

            filter_ = flt.FilterResultsTable(self.results_mdl.table)

            try:
                filter_.parse(expression=txt)
                filtered_table = filter_.apply()
            except ValueError as e:
                error_msg(str(e), "Fiter parse")
                return None
            except Exception as e:
                error_msg(str(e), "Fiter parse")
                return None

            self.results_mdl = ResultsModel(filtered_table)
            self.ui.resultsTableView.setModel(self.results_mdl)
        else:
            return None

    def delete_results_driver(self):
        """
        Delete the driver
        :return:
        """
        idx = self.ui.results_treeView.selectedIndexes()
        if len(idx) > 0:
            tree_mdl = self.ui.results_treeView.model()
            item = tree_mdl.itemFromIndex(idx[0])
            path = gf.get_tree_item_path(item)

            if len(path) > 0:
                study_name = path[0]
                study_type = self.available_results_dict[study_name]

                quit_msg = "Do you want to delete_with_dialogue the results driver " + study_name + "?"
                reply = QtWidgets.QMessageBox.question(self, 'Message',
                                                       quit_msg,
                                                       QtWidgets.QMessageBox.StandardButton.Yes,
                                                       QtWidgets.QMessageBox.StandardButton.No)

                if reply == QtWidgets.QMessageBox.StandardButton.Yes.value:
                    if study_name == SimulationTypes.RmsDynamic_run.value or study_name == SimulationTypes.EmtDynamic_run.value:
                        if study_name in self.dynamic_results_handlers:
                            del self.dynamic_results_handlers[study_name]
                        self.clear_dynamic_results_view()

                    self.session.delete_driver_by_name(study_name)
                    self.update_available_results()

    def clear_dynamic_results_view(self):
        """
        Clear the dynamic-results UI from the screen.
        """
        self.dynamic_results_handler = None

        # Remove tree models so the views become empty and non-interactive
        self.ui.dynamicsDeviceTreeView.setModel(None)
        self.ui.dynamicsPlotsTreeView.setModel(None)
        self.ui.dynamicsTableView.setModel(None)

        # Clear selections
        self.ui.dynamicsDeviceTreeView.clearSelection()
        self.ui.dynamicsPlotsTreeView.clearSelection()

        # Clear related controls
        self.ui.search_dynamic_objects_lineEdit.clear()
        self.ui.eventsGroupComboBox.clear()

        # Leave the dynamics tab and go back to the normal results table tab
        self.ui.resultsTabWidget.setCurrentIndex(0)


    def copy_opf_to_profiles(self):
        """
        Copy the results from the OPF snapshot and time series to the database
        """

        # copy the snapshot if that exits
        _, results = self.session.optimal_power_flow
        if results is not None:

            ok = yes_no_question('Are you sure that you want to overwrite '
                                 'the generation, batteries and load snapshot values '
                                 'with the OPF results?',
                                 title="Overwrite profiles with OPF results")

            if ok:
                self.circuit.set_opf_snapshot_results(results)
                self.show_info_toast("P snapshot set from the OPF results")

        else:
            self.show_warning_toast('The OPF time series has no results :(')

        # copy the time series if that exists --------------------------------------------------------------------------
        _, results = self.session.optimal_power_flow_ts
        if results is not None:

            ok = yes_no_question('Are you sure that you want to overwrite '
                                 'the generation, batteries and load profiles '
                                 'with the OPF time series results?',
                                 title="Overwrite profiles with OPF results")

            if ok:
                self.circuit.set_opf_ts_results(results)
                self.show_info_toast("P profiles set from the OPF results")

        else:
            self.show_warning_toast('The OPF time series has no results :(')

    def save_results_logs(self):
        """
        Save the results' logs
        """
        file, filter_ = QtWidgets.QFileDialog.getSaveFileName(self, "Export logs", '',
                                                              filter="CSV (*.csv);;Excel files (*.xlsx)", )

        if file != '':
            if 'xlsx' in filter_:
                f = file
                if not f.endswith('.xlsx'):
                    f += '.xlsx'
                self.current_results_logger.to_xlsx(f)

            if 'csv' in filter_:
                f = file
                if not f.endswith('.csv'):
                    f += '.csv'
                self.current_results_logger.to_csv(f)
