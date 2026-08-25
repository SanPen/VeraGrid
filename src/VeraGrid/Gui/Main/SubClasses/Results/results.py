# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
from PySide6 import QtCore, QtWidgets, QtGui
from matplotlib import pyplot as plt
from typing import Union, Dict

from VeraGrid.Gui.Main.SubClasses.Results.dynamics_results_handler import (
    DynamicsResultsHandler)
from VeraGrid.Gui.table_view_header_wrap import HeaderViewWithWordWrap
import VeraGrid.Gui.gui_functions as gf
from VeraGrid.Gui.messages import error_msg, warning_msg, yes_no_question
from VeraGrid.Gui.Main.SubClasses.simulations import SimulationsMain
from VeraGrid.Gui.results_model import ResultsModel
from VeraGrid.Gui.general_dialogues import fill_tree_from_logs
import VeraGridEngine.Utils.Filtering as flt
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import (ResultTypes, SimulationTypes, PlotSimulationType, DynamicPlotEntryKind,
                                         DynamicPlotMode, ResultTablePlotType)
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Simulations.Rms.rms_results import RmsResults
from VeraGridEngine.Simulations.EMT.emt_results import EmtResults
from VeraGridEngine.Devices.Events.dynamic_plot_entry import DynamicPlotEntry


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
        self.dynamic_results_handlers: Dict[SimulationTypes, DynamicsResultsHandler] = dict()

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
        self.ui.prepareRmsDynamicPlotsButton.clicked.connect(self.prepare_rms_dynamic_plots)
        self.ui.prepareEmtDynamicPlotsButton.clicked.connect(self.prepare_emt_dynamic_plots)
        self.ui.saveResultsLogsButton.clicked.connect(self.save_results_logs)

        # tree-click
        self.ui.results_treeView.clicked.connect(self.results_tree_view_click)
        self.ui.dynamicsDeviceTreeView.clicked.connect(self.dynamic_results_tree_view_click)
        self.ui.dynamicsPlotsTreeView.clicked.connect(self.dynamic_plots_tree_view_click)

        # tree double click
        self.ui.dynamicsDeviceTreeView.doubleClicked.connect(self.dynamic_results_tree_view_dbl_click)
        self.ui.dynamicsPlotsTreeView.doubleClicked.connect(self.dynamic_plots_tree_view_dbl_click)

        # The plots tree exposes group actions through a context menu so the
        # double-click interaction can remain dedicated to plotting.
        self.ui.results_treeView.customContextMenuRequested.connect(self.show_results_tree_context_menu)
        self.ui.results_treeView.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.dynamicsPlotsTreeView.customContextMenuRequested.connect(self.show_dynamic_plots_context_menu)
        self.ui.dynamicsPlotsTreeView.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)

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
        study_type: SimulationTypes | None = self.get_results_tree_study_type(item=item)

        if study_type is not None:
            driver = self.session.get_driver(driver_type=study_type)

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
                    study_type=study_type,
                    results=driver.results
                )

                if self._dynamic_views_already_attached():
                    self.ui.dynamicsPlotsTreeView.update()
                else:
                    self._refresh_dynamic_tree_models(expand_plots_when_empty=True, clear_table=False)

                self.ui.resultsTabWidget.setCurrentIndex(1)


            elif driver.tpe == SimulationTypes.EmtDynamic_run:

                self.dynamic_results_handler = self.get_or_create_dynamic_results_handler(
                    study_type=study_type,
                    results=driver.results
                )

                if self._dynamic_views_already_attached():
                    self.ui.dynamicsPlotsTreeView.update()
                else:
                    self._refresh_dynamic_tree_models(expand_plots_when_empty=True, clear_table=False)
                self.ui.resultsTabWidget.setCurrentIndex(1)

            else:
                # Go to the Table tab
                self.ui.resultsTabWidget.setCurrentIndex(0)
                self.clear_dynamic_results_view()

            result_type: ResultTypes | None = self.get_results_tree_result_type(item=item)
            if result_type is not None:
                study_results = self.available_results_dict.get(study_type, None)

                if study_results is not None:

                    study_result_type: ResultTypes = study_results.get(result_type, None)

                    if study_result_type is not None:

                        self.results_mdl = self.session.get_results_model(driver_type=study_type,
                                                                          result_type=study_result_type)

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

    def get_results_tree_study_type(self, item: QtGui.QStandardItem | None) -> SimulationTypes | None:
        """
        Resolve a results tree item to its simulation type.

        :param item: Tree item.
        :return: Simulation type or None.
        """
        current_item: QtGui.QStandardItem | None = item
        while current_item is not None:
            item_data: object = current_item.data(QtCore.Qt.ItemDataRole.UserRole)
            if isinstance(item_data, SimulationTypes):
                return item_data
            else:
                current_item = current_item.parent()
        return None

    def get_results_tree_result_type(self, item: QtGui.QStandardItem | None) -> ResultTypes | None:
        """
        Resolve a results tree item to its result type.

        :param item: Tree item.
        :return: Result type or None.
        """
        if item is not None:
            item_data: object = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if isinstance(item_data, ResultTypes):
                return item_data
            else:
                return None
        else:
            return None

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
            selected_series = self.dynamic_results_handler.get_series_from_index(index=source_index)
            if selected_series is not None:
                self.dynamic_results_handler.plot_series(series=selected_series)
                return None
            else:
                parameter_entry: DynamicPlotEntry | None = self.dynamic_results_handler.get_parameter_entry_from_index(
                    index=source_index
                )
                if parameter_entry is not None:
                    self.dynamic_results_handler.plot_parameter_entry(entry=parameter_entry)
                    return None
                else:
                    pass

                selected_candidate = self.dynamic_results_handler.get_candidate_from_index(index=source_index)
                if selected_candidate is not None:
                    if selected_candidate.get_entry_kind() == DynamicPlotEntryKind.PARAMETER:
                        self.dynamic_results_handler.plot_parameter_candidate(candidate=selected_candidate)
                        return None
                    else:
                        return None
                else:
                    return None
        else:
            return None

    def show_results_tree_context_menu(self, pos: QtCore.QPoint) -> None:
        """
        Display the context menu for the results tree.

        :param pos: Local click position in the tree view.
        :return: None.
        """
        index: QtCore.QModelIndex = self.ui.results_treeView.indexAt(pos)

        if index.isValid():
            self.ui.results_treeView.setCurrentIndex(index)
            menu: QtWidgets.QMenu = QtWidgets.QMenu(self.ui.results_treeView)
            gf.add_menu_entry(menu=menu,
                              text=self.tr("Delete driver"),
                              icon_path=":/Icons/icons/minus.png",
                              function_ptr=self.delete_results_driver)
            menu.exec(self.ui.results_treeView.viewport().mapToGlobal(pos))
        else:
            pass

    def dynamic_plots_tree_view_dbl_click(self, index: QtCore.QModelIndex) -> None:
        """
        Plot the selected plots-tree entry on double click.

        :param index:
        :return: Nothing.
        """
        del index
        self.plot_dynamic_plot_entry()

    def dynamic_plots_tree_view_click(self, index: QtCore.QModelIndex) -> None:
        """
        Refresh the dynamics table for the selected plot entry.

        :param index: Selected plots-tree index.
        :return: Nothing.
        """
        del index
        if self.dynamic_results_handler is not None:
            selected_indexes = self.ui.dynamicsPlotsTreeView.selectedIndexes()
            if len(selected_indexes) > 0:
                # The selected plot entry already stores source-specific series,
                # so table reconstruction no longer needs a separate selector.
                mdl: ResultsModel | None = self.dynamic_results_handler.get_data_from_plot_index(
                    index=selected_indexes[0]
                )

                self.ui.dynamicsTableView.setModel(mdl)
            else:
                pass
        else:
            pass

    def _refresh_dynamic_tree_models(self,
                                     expand_plots_when_empty: bool,
                                     clear_table: bool) -> None:
        """
        Refresh the dynamic tree widgets while preserving semantic state.

        :param expand_plots_when_empty: Expand all plot groups only when no prior state exists.
        :param clear_table: Clear the dynamics table model after refresh when requested.
        :return: Nothing.
        """
        if self.dynamic_results_handler is not None:
            self.ui.dynamicsDeviceTreeView.setModel(self.dynamic_results_handler.get_view_model())
            self.ui.dynamicsPlotsTreeView.setModel(self.dynamic_results_handler.get_plots_model())

            if expand_plots_when_empty:
                self.ui.dynamicsPlotsTreeView.expandAll()
            else:
                pass

            if clear_table:
                self.ui.dynamicsTableView.setModel(None)
            else:
                pass
        else:
            pass

    def _dynamic_views_already_attached(self) -> bool:
        """
        Check whether the current handler models are already attached to the two dynamic tree views.

        :return: ``True`` when both views already show the current handler models.
        """
        if self.dynamic_results_handler is not None:
            current_device_model: QtCore.QAbstractItemModel | None = self.ui.dynamicsDeviceTreeView.model()
            current_plots_model: QtCore.QAbstractItemModel | None = self.ui.dynamicsPlotsTreeView.model()

            if current_device_model is self.dynamic_results_handler.get_view_model():
                if current_plots_model is self.dynamic_results_handler.get_plots_model():
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def _expand_plot_drop_parent(self, parent: QtCore.QModelIndex) -> None:
        """
        Expand the plot-group row targeted by a drop operation.

        :param parent: Parent index reported by the plots model.
        :return: Nothing.
        """
        if parent.isValid():
            self.ui.dynamicsPlotsTreeView.setExpanded(parent, True)
        else:
            pass

    def show_dynamic_plots_context_menu(self, pos: QtCore.QPoint) -> None:
        """
        Show the context menu for the dynamics plots tree.

        :param pos: Click position in viewport coordinates.
        :return: Nothing.
        """
        # The context menu is only meaningful when a handler exists because the
        # handler owns the mapping between view indexes and plot-group objects.
        if self.dynamic_results_handler is not None:
            index: QtCore.QModelIndex = self.ui.dynamicsPlotsTreeView.indexAt(pos)
            if index.isValid():
                plots_model = self.dynamic_results_handler.get_plots_model()
                item: QtGui.QStandardItem | None = plots_model.itemFromIndex(index)
                if item is not None:
                    if item.parent() is None:
                        menu: QtWidgets.QMenu = QtWidgets.QMenu(parent=self.ui.dynamicsPlotsTreeView)
                        rename_action: QtGui.QAction = menu.addAction(self.tr("Rename group"))
                        selected_action: QtGui.QAction | None = menu.exec_(
                            self.ui.dynamicsPlotsTreeView.viewport().mapToGlobal(pos)
                        )
                        if selected_action == rename_action:
                            self.rename_dynamic_plot_group(index=index)
                        else:
                            pass
                    else:
                        menu = QtWidgets.QMenu(parent=self.ui.dynamicsPlotsTreeView)
                        rename_action = menu.addAction(self.tr("Rename variable"))
                        selected_action = menu.exec_(
                            self.ui.dynamicsPlotsTreeView.viewport().mapToGlobal(pos)
                        )
                        if selected_action == rename_action:
                            self.rename_dynamic_plot_variable(index=index)
                        else:
                            pass
                else:
                    pass
            else:
                pass
        else:
            pass

    def rename_dynamic_plot_group(self, index: QtCore.QModelIndex) -> None:
        """
        Rename the selected dynamics plot group.

        :param index: Selected top-level plot-group index.
        :return: Nothing.
        """
        # The selected index is translated through the handler so the GUI keeps
        # all plot-group state changes centralized in the handler layer.
        if self.dynamic_results_handler is not None:
            old_name: str | None = self.dynamic_results_handler.get_plot_group_name_from_index(index=index)
            if old_name is not None:
                new_name: str
                accepted: bool
                new_name, accepted = QtWidgets.QInputDialog.getText(
                    self,
                    self.tr("Rename dynamic plot"),
                    self.tr("Plot name"),
                    text=old_name
                )
                if accepted:
                    renamed: bool = self.dynamic_results_handler.rename_plot_group(old_name=old_name,
                                                                                   new_name=new_name)
                    if renamed:
                        self.ui.dynamicsPlotsTreeView.update()
                    else:
                        self.show_warning_toast(self.tr("The plot group name is empty or already exists."))
                else:
                    pass
            else:
                self.show_warning_toast(self.tr("Select a plot group first."))
        else:
            self.show_warning_toast(self.tr("There are no RMS dynamics results loaded."))

    def rename_dynamic_plot_variable(self, index: QtCore.QModelIndex) -> None:
        """
        Rename the selected dynamics plot variable.

        :param index: Selected child plot-entry index.
        :return: Nothing.
        """
        if self.dynamic_results_handler is not None:
            plots_model = self.dynamic_results_handler.get_plots_model()
            item: QtGui.QStandardItem | None = plots_model.itemFromIndex(index)
            if item is not None:
                current_name: str = item.text()
                missing_suffix: str = " [missing]"
                pending_suffix: str = " [pending]"

                if current_name.endswith(missing_suffix):
                    current_name = current_name[:-len(missing_suffix)]
                else:
                    pass

                if current_name.endswith(pending_suffix):
                    current_name = current_name[:-len(pending_suffix)]
                else:
                    pass

                new_name: str
                accepted: bool
                new_name, accepted = QtWidgets.QInputDialog.getText(
                    self,
                    self.tr("Rename dynamic variable"),
                    self.tr("Variable name"),
                    text=current_name
                )
                if accepted:
                    renamed: bool = self.dynamic_results_handler.rename_plot_variable_from_index(
                        index=index,
                        new_name=new_name,
                    )
                    if renamed:
                        self.ui.dynamicsPlotsTreeView.update()
                    else:
                        self.show_warning_toast(self.tr("The variable name is empty or could not be changed."))
                else:
                    pass
            else:
                self.show_warning_toast(self.tr("Select a variable first."))
        else:
            self.show_warning_toast(self.tr("There are no RMS dynamics results loaded."))

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


        # A row insertion already happened inside the existing model. Rebuilding
        # the views here would destroy the exact expansion state we are trying to
        # preserve. The only required post-insert action is to keep the target
        # parent visible so the newly dropped entry remains in view.
        self._expand_plot_drop_parent(parent=parent)

        del parent
        del first
        del last

    def add_dynamic_plot_group(self) -> None:
        """
        Create a new dynamics plot group.

        :return: Nothing.
        """
        if self.dynamic_results_handler is not None:
            suggested_name: str = self.dynamic_results_handler.get_next_group_name()
            dialog: QtWidgets.QDialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle(self.tr("New dynamic plot"))
            layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(dialog)
            name_label: QtWidgets.QLabel = QtWidgets.QLabel(self.tr("Plot name"), dialog)
            name_edit: QtWidgets.QLineEdit = QtWidgets.QLineEdit(dialog)
            mode_label: QtWidgets.QLabel = QtWidgets.QLabel(self.tr("Plot mode"), dialog)
            mode_combo: QtWidgets.QComboBox = QtWidgets.QComboBox(dialog)
            buttons: QtWidgets.QDialogButtonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
                                                                              dialog)
            name_edit.setText(suggested_name)
            mode_combo.addItem(self.tr("Time Series (Y vs Time)"), DynamicPlotMode.TIME_SERIES)
            mode_combo.addItem(self.tr("X-Y Plot (Y vs X)"), DynamicPlotMode.XY)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(name_label)
            layout.addWidget(name_edit)
            layout.addWidget(mode_label)
            layout.addWidget(mode_combo)
            layout.addWidget(buttons)
            accepted: bool = dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted
            if accepted:
                group_name: str = name_edit.text()
                selected_mode_data: object = mode_combo.currentData()
                selected_mode: DynamicPlotMode = DynamicPlotMode.TIME_SERIES
                if isinstance(selected_mode_data, DynamicPlotMode):
                    selected_mode = selected_mode_data
                else:
                    pass
                created: bool = self.dynamic_results_handler.create_plot_group(name=group_name, mode=selected_mode)
                if created:
                    self.ui.dynamicsPlotsTreeView.expandAll()
                else:
                    self.show_warning_toast(self.tr("The plot group name is empty or already exists."))
            else:
                pass
        else:
            self.show_warning_toast(self.tr("There are no RMS dynamics results loaded."))

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
                    self.ui.dynamicsPlotsTreeView.update()
                else:
                    self.show_warning_toast(self.tr("The selected dynamic plot entry could not be deleted."))
            else:
                self.show_warning_toast(self.tr("Select a plot group or variable first."))
        else:
            self.show_warning_toast(self.tr("There are no RMS dynamics results loaded."))

    def plot_dynamic_plot_entry(self) -> None:
        """
        Plot the selected dynamics plot group or variable.

        :return: Nothing.
        """
        if self.dynamic_results_handler is not None:
            selected_indexes = self.ui.dynamicsPlotsTreeView.selectedIndexes()
            if len(selected_indexes) > 0:
                # Plotting uses the event-group information stored with each
                # series, so there is no separate event-group control anymore.
                plotted: bool = self.dynamic_results_handler.plot_entry_from_index(index=selected_indexes[0])
                if plotted:
                    return None
                else:
                    self.show_warning_toast(self.tr("The selected dynamic plot entry could not be plotted."))
                    return None
            else:
                self.show_warning_toast(self.tr("Select a plot group or variable first."))
                return None
        else:
            self.show_warning_toast(self.tr("There are no RMS dynamics results loaded."))
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
                                              study_type: SimulationTypes,
                                              results: RmsResults|EmtResults) -> DynamicsResultsHandler:
        """
        Get a cached dynamic-results handler for the given study, or create/update it.

        :param study_type: Study simulation type.
        :param results: Dynamic results object associated with the study.
        :return: Cached or newly created dynamics-results handler.

        Handlers are cached per study name so user-defined dynamic plot groups
        survive repeated simulations. Reuse only happens when the previous and
        new results belong to the same dynamics family; otherwise a fresh
        handler is created because RMS and EMT expose different event-group and
        array layouts.
        """
        handler: DynamicsResultsHandler | None = self.dynamic_results_handlers.get(study_type, None)

        if handler is None:
            handler = DynamicsResultsHandler(results=results, circuit=self.circuit)
            handler.dialog_parent = self
            self.dynamic_results_handlers[study_type] = handler
            handler.get_plots_model().rowsInserted.connect(self.expand_dynamic_plots_tree)
            return handler

        elif type(handler.results) == type(results):
            # Reusing the handler preserves the user's dynamic plot groups across
            # repeated runs of the same study while replacing only the result-backed Vars.
            handler.circuit = self.circuit
            handler.dialog_parent = self
            handler.update_results(results=results)
            return handler

        else:
            # RMS and EMT handlers cannot be mixed because their result containers use
            # different event-group fields and value-array layouts.
            handler = DynamicsResultsHandler(results=results, circuit=self.circuit)
            handler.dialog_parent = self
            self.dynamic_results_handlers[study_type] = handler
            handler.get_plots_model().rowsInserted.connect(self.expand_dynamic_plots_tree)
            return handler

    def _show_pre_simulation_dynamic_plot_editor(self, simulation_type: PlotSimulationType) -> None:
        """
        Open the dynamic plot editor for one simulation family without results.

        :param simulation_type: Simulation family identifier.
        :return: Nothing.
        """
        handler: DynamicsResultsHandler = DynamicsResultsHandler(
            results=None,
            circuit=self.circuit,
            simulation_type=simulation_type,
            dialog_parent=self,
        )
        self.dynamic_results_handler = handler

        # The same Dynamics tab is reused in pre-simulation mode so the user can
        # prepare persistent plot definitions before any runtime result arrays exist.
        self._refresh_dynamic_tree_models(expand_plots_when_empty=True, clear_table=True)
        self.ui.resultsTabWidget.setCurrentIndex(1)

    def prepare_rms_dynamic_plots(self) -> None:
        """
        Open the pre-simulation RMS dynamic plot editor.

        :return: Nothing.
        """
        self._show_pre_simulation_dynamic_plot_editor(simulation_type=PlotSimulationType.RMS)

    def prepare_emt_dynamic_plots(self) -> None:
        """
        Open the pre-simulation EMT dynamic plot editor.

        :return: Nothing.
        """
        self._show_pre_simulation_dynamic_plot_editor(simulation_type=PlotSimulationType.EMT)

    def plot_results(self) -> None:
        """
        Plot the visible results according to the table plot contract.

        Complex-vector tables interpret selected cells as mode-column choices.
        State subsets are selected explicitly through complete rows or through
        the results filter, preventing a single clicked cell from truncating an
        entire right eigenvector accidentally. Complex-point tables use cell
        selection for modes and complete-column selection for coordinate units.

        :return: None.
        """
        mdl: ResultsModel | None = self.ui.resultsTableView.model()

        if mdl is not None:

            plt.rcParams["date.autoformatter.minute"] = "%Y-%m-%d %H:%M:%S"

            # Collect the selected cells once so all plot types use the same
            # visible model after filtering.
            selected_indexes: list[QtCore.QModelIndex] = self.ui.resultsTableView.selectedIndexes()
            selected_columns: np.ndarray | None
            selected_rows: np.ndarray | None
            if len(selected_indexes) > 0:
                selected_columns_array: np.ndarray = np.zeros(len(selected_indexes), dtype=np.int64)
                selected_rows_array: np.ndarray = np.zeros(len(selected_indexes), dtype=np.int64)

                selected_position: int
                selected_index: QtCore.QModelIndex
                for selected_position, selected_index in enumerate(selected_indexes):
                    selected_columns_array[selected_position] = selected_index.column()
                    selected_rows_array[selected_position] = selected_index.row()

                selection_model: QtCore.QItemSelectionModel = self.ui.resultsTableView.selectionModel()
                complete_rows: list[QtCore.QModelIndex] = selection_model.selectedRows()
                complete_columns: list[QtCore.QModelIndex] = selection_model.selectedColumns()

                if mdl.table.plot_type == ResultTablePlotType.COMPLEX_POINTS:
                    # Cell and row selection chooses modal points. Only an
                    # explicit complete-column selection changes the complex
                    # coordinate pair used by the plot.
                    if len(complete_rows) > 0:
                        complete_row_indices: np.ndarray = np.zeros(len(complete_rows), dtype=np.int64)
                        complete_row_position: int
                        complete_row: QtCore.QModelIndex
                        for complete_row_position, complete_row in enumerate(complete_rows):
                            complete_row_indices[complete_row_position] = complete_row.row()
                        selected_rows = np.unique(complete_row_indices)
                    else:
                        selected_rows = np.unique(selected_rows_array)

                    # Selecting every table column normally comes from a row
                    # selection and therefore means "use the default pair".
                    if 0 < len(complete_columns) < mdl.table.c:
                        complete_column_indices: np.ndarray = np.zeros(
                            len(complete_columns),
                            dtype=np.int64,
                        )
                        complete_column_position: int
                        complete_column: QtCore.QModelIndex
                        for complete_column_position, complete_column in enumerate(complete_columns):
                            complete_column_indices[complete_column_position] = complete_column.column()
                        selected_columns = np.unique(complete_column_indices)
                    else:
                        selected_columns = None
                elif mdl.table.plot_type == ResultTablePlotType.COMPLEX_VECTORS:
                    selected_columns = np.unique(selected_columns_array)
                    if len(complete_rows) > 0:
                        complete_row_indices: np.ndarray = np.zeros(len(complete_rows), dtype=np.int64)
                        complete_row_position: int
                        complete_row: QtCore.QModelIndex
                        for complete_row_position, complete_row in enumerate(complete_rows):
                            complete_row_indices[complete_row_position] = complete_row.row()
                        selected_rows = np.unique(complete_row_indices)
                    else:
                        selected_rows = None
                else:
                    selected_columns = np.unique(selected_columns_array)
                    selected_rows = np.unique(selected_rows_array)
            else:
                selected_columns = None
                selected_rows = None

            if mdl.table.plot_type == ResultTablePlotType.COMPLEX_POINTS:
                number_of_plots: int = 1
            elif selected_columns is None:
                number_of_plots: int = mdl.table.c
            else:
                number_of_plots = int(selected_columns.size)

            if number_of_plots > 50:
                ok = yes_no_question(text=self.tr("There are {columns} columns, the plot might take a lot to render.\n"
                                                  "Are you ok with potentially waiting a lot?").format(
                                                      columns=number_of_plots),
                                     title=self.tr("Plot"))
            else:
                ok = True

            if ok:
                # create figure to plot
                fig = plt.figure(figsize=(12, 8))
                ax = fig.add_subplot(111)

                # The table dispatches to the series, complex-point, or
                # complex-vector renderer without simulation-specific GUI code.
                mdl.plot(
                    ax=ax,
                    selected_col_idx=selected_columns,
                    selected_rows=selected_rows,
                    stacked=self.ui.stacked_plot_checkBox.isChecked()
                )

                plt.show()
            else:
                pass
        else:
            warning_msg(
                self.tr("There are no results available to plot."),
                self.tr("Plot results"),
            )

    def save_results_df(self):
        """
        Save the data displayed at the results as excel
        """
        mdl: ResultsModel = self.ui.resultsTableView.model()

        if mdl is not None:
            file, filter_ = QtWidgets.QFileDialog.getSaveFileName(self, self.tr("Export results"), '',
                                                                  filter=self.tr("CSV (*.csv);;Excel files (*.xlsx)"))

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
                    error_msg(self.tr("{file_name} is not valid :(").format(file_name=file))
        else:
            warning_msg(self.tr("There is no profile displayed, please display one"),
                        self.tr("Copy profile to clipboard"))

    def copy_results_data(self):
        """
        Copy the current displayed profiles to the clipboard
        """
        mdl = self.ui.resultsTableView.model()
        if mdl is not None:
            mdl.copy_to_clipboard()
            self.show_info_toast(self.tr("Copied!"))
        else:
            warning_msg(self.tr("There is no profile displayed, please display one"),
                        self.tr("Copy profile to clipboard"))

    def copy_results_data_as_numpy(self):
        """
        Copy the current displayed profiles to the clipboard
        """
        mdl = self.ui.resultsTableView.model()
        if mdl is not None:
            mdl.copy_numpy_to_clipboard()
            self.show_info_toast(self.tr("Copied!"))
        else:
            warning_msg(self.tr("There is no profile displayed, please display one"),
                        self.tr("Copy profile to clipboard"))

    def search_in_results(self) -> None:
        """
        Search in the results model

        :return: None.
        """

        if self.results_mdl is not None:

            txt: str = self.ui.search_results_lineEdit.text().strip()

            filter_: flt.FilterResultsTable = flt.FilterResultsTable(self.results_mdl.table)

            try:
                filter_.parse(expression=txt)
                filtered_model: ResultsModel = ResultsModel(filter_.apply())
            except ValueError as e:
                error_msg(str(e), self.tr("Filter parse"))
                return
            except Exception as e:
                error_msg(str(e), self.tr("Filter parse"))
                return

            # Keep the unfiltered model as the stable search source. This makes
            # each query independent and lets an empty query restore the table.
            self.ui.resultsTableView.setModel(filtered_model)
        else:
            return

    def delete_results_driver(self):
        """
        Delete the driver
        :return:
        """
        idx = self.ui.results_treeView.selectedIndexes()
        if len(idx) > 0:
            tree_mdl = self.ui.results_treeView.model()
            item = tree_mdl.itemFromIndex(idx[0])
            study_type: SimulationTypes | None = self.get_results_tree_study_type(item=item)

            if study_type is not None:

                quit_msg = self.tr("Do you want to delete the results driver {study_name}?").format(
                    study_name=study_type.value
                )
                reply = QtWidgets.QMessageBox.question(self, self.tr("Message"),
                                                       quit_msg,
                                                       QtWidgets.QMessageBox.StandardButton.Yes,
                                                       QtWidgets.QMessageBox.StandardButton.No)

                if reply == QtWidgets.QMessageBox.StandardButton.Yes.value:
                    if study_type == SimulationTypes.RmsDynamic_run or study_type == SimulationTypes.EmtDynamic_run:
                        if study_type in self.dynamic_results_handlers:
                            del self.dynamic_results_handlers[study_type]
                        else:
                            pass
                        self.clear_dynamic_results_view()
                    else:
                        pass

                    self.session.delete_driver(study_type)
                    self.update_available_results()
            else:
                pass
        else:
            pass

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

        # Leave the dynamics tab and go back to the normal results table tab
        self.ui.resultsTabWidget.setCurrentIndex(0)


    def copy_opf_to_profiles(self):
        """
        Copy the results from the OPF snapshot and time series to the database
        """

        # copy the snapshot if that exits
        _, results = self.session.optimal_power_flow
        if results is not None:

            ok = yes_no_question(self.tr('Are you sure that you want to overwrite '
                                         'the generation, batteries and load snapshot values '
                                         'with the OPF results?'),
                                 title=self.tr("Overwrite profiles with OPF results"))

            if ok:
                self.circuit.set_opf_snapshot_results(results)
                self.show_info_toast(self.tr("P snapshot set from the OPF results"))

        else:
            self.show_warning_toast(self.tr('The OPF time series has no results :('))

        # copy the time series if that exists --------------------------------------------------------------------------
        _, results = self.session.optimal_power_flow_ts
        if results is not None:

            ok = yes_no_question(self.tr('Are you sure that you want to overwrite '
                                         'the generation, batteries and load profiles '
                                         'with the OPF time series results?'),
                                 title=self.tr("Overwrite profiles with OPF results"))

            if ok:
                self.circuit.set_opf_ts_results(results)
                self.show_info_toast(self.tr("P profiles set from the OPF results"))

        else:
            self.show_warning_toast(self.tr('The OPF time series has no results :('))

    def save_results_logs(self):
        """
        Save the results' logs
        """
        file, filter_ = QtWidgets.QFileDialog.getSaveFileName(self, self.tr("Export logs"), '',
                                                              filter=self.tr("CSV (*.csv);;Excel files (*.xlsx)"), )

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
