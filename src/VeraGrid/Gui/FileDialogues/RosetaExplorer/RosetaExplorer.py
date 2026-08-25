# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os.path
from typing import List, Union
import webbrowser
import numpy as np
import pandas as pd
# Engine imports

# GUI imports
from VeraGrid.Gui.gui_functions import get_list_model, get_logger_tree_model

from PySide6 import QtGui, QtCore
from VeraGrid.Gui.messages import *
from VeraGrid.Gui.FileDialogues.RosetaExplorer.roseta_explorer import Ui_RosetaExplorer, QMainWindow
from VeraGrid.Gui.FileDialogues.RosetaExplorer.roseta_objects_model import RosetaObjectsModel
from VeraGrid.Gui.gui_functions import add_menu_entry, populate_cim_item_children, get_cim_tree_model
from VeraGrid.Gui.object_model import ObjectsModel
from VeraGrid.Gui.pandas_model import PandasModel
from VeraGridEngine.IO.cim.cgmes.cgmes_circuit import CgmesCircuit
from VeraGridEngine.IO.raw.psse_circuit import PsseCircuit
from VeraGridEngine.IO.cim.db.db_handler import DbHandler
from VeraGridEngine.data_logger import DataLogger
from VeraGrid.Gui.python_console import PythonConsole


def clear_qt_layout(layout: QtWidgets.QLayout) -> None:
    """
    Remove all widgets from a layout object
    :param layout:
    """
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        child_layout = item.layout()

        if child_layout is not None:
            clear_qt_layout(child_layout)
            child_layout.deleteLater()
        elif widget is not None:
            # Fully detach the widget now so stale layout items do not outlive it.
            widget.setParent(None)
            widget.deleteLater()


########################################################################################################################
# Main Window
########################################################################################################################


class RosetaExplorerGUI(QMainWindow):
    """
    RosetaExplorerGUI
    """

    def __init__(self, parent=None, db_handler: Union[DbHandler, None] = None):
        """

        @param parent:
        """

        # create main window
        QMainWindow.__init__(self, parent)
        self.ui = Ui_RosetaExplorer()
        self.ui.setupUi(self)
        self.title = 'Roseta Explorer'
        self.setWindowTitle(self.title)
        self.setAcceptDrops(True)

        # 1:4
        self.ui.main_splitter.setStretchFactor(0, 1)
        self.ui.main_splitter.setStretchFactor(1, 8)

        self.open_file_thread_object = None

        self.accepted_extensions = ['.zip', '.xml', '.raw']
        self.project_directory = ''
        self.lock_ui = True

        self.tree_navigation_windows: List["RosetaExplorerGUI"] = list()

        self.circuit: Union[CgmesCircuit, PsseCircuit, None] = None

        self.logger: DataLogger = DataLogger()

        # Representation models
        self.classes_model = None
        self.properties_model = None
        self.properties_proxy_model = QtCore.QSortFilterProxyModel(self.ui.propertiesTableView)
        self.properties_proxy_model.setRecursiveFilteringEnabled(False)
        self.properties_proxy_model.setFilterKeyColumn(0)
        self.ui.propertiesTableView.setSortingEnabled(True)

        # Tree
        self.treeProxyModel = QtCore.QSortFilterProxyModel(self.ui.mainTreeView)
        self.treeProxyModel.setRecursiveFilteringEnabled(True)
        self.treeProxyModel.setFilterKeyColumn(0)
        self.ui.mainTreeView.setSortingEnabled(True)

        self.ui.treeFilterComboBox.setModel(get_list_model(['Class', 'Property', 'Value']))
        self.ui.treeFilterComboBox.setCurrentIndex(0)

        self.current_model = None

        # DB
        self.db_handler: DbHandler = DbHandler(new_db=False) if db_handler is None else db_handler
        self.update_combo_boxes()

        # Console
        self.console = None
        self.create_console()

        # Connections --------------------------------------------------------------------------------------------------

        # triggered
        self.ui.actionSave_logs.triggered.connect(self.save_logs)

        # clicked
        self.ui.filterButton.clicked.connect(self.filter_properties_table)
        self.ui.modelTypeLabel.mouseDoubleClickEvent = self.display_circuit
        self.ui.treeFilterButton.clicked.connect(self.filter_main_tree)
        self.ui.mainTreeView.clicked.connect(self.update_main_tree_on_click)
        self.ui.mainTreeView.expanded.connect(self.on_tree_expanded)

        # text changed
        self.ui.filterComboBox.currentTextChanged.connect(self.on_filter_combobox_changed)
        self.ui.treeFilterComboBox.currentTextChanged.connect(self.on_tree_filter_combobox_changed)

        # lineedit enter
        self.ui.filterLineEdit.returnPressed.connect(self.filter_properties_table)

        # list clicks
        self.ui.clasesListView.clicked.connect(self.on_class_click)

        # context menu
        self.ui.propertiesTableView.customContextMenuRequested.connect(self.show_objects_context_menu)

        # Set context menu policy to CustomContextMenu
        self.ui.propertiesTableView.setContextMenuPolicy(QtGui.Qt.ContextMenuPolicy.CustomContextMenu)

        self.UNLOCK()
        self.update_combo_boxes()

    def LOCK(self, val: bool = True) -> None:
        """
        Lock the interface to prevent new simulation launches
        :param val:
        :return:
        """
        self.lock_ui = val
        self.ui.progress_frame.setVisible(self.lock_ui)
        QtGui.QGuiApplication.processEvents()

    def UNLOCK(self) -> None:
        """
        Unlock the interface
        """
        if not self.any_thread_running():
            self.LOCK(False)

    def create_console(self) -> None:
        """
        Create console
        """
        if self.console is not None:
            clear_qt_layout(self.ui.consoleLayout.layout())

        self.console = PythonConsole()

        # add the console widget to the user interface
        self.ui.consoleLayout.layout().addWidget(self.console)

        # push some variables to the console
        for key, val in {"np": np,
                         "pd": pd,
                         'app': self,
                         'circuit': self.circuit}.items():
            self.console.add_var(key, val)

    def update_combo_boxes(self):
        """
        Properly update the combo boxes
        """
        if isinstance(self.circuit, PsseCircuit):
            # we do this first so that the model changing does not trigger the on_combo_box_text_change function
            if self.db_handler.psse_lookup_db.last_file_opened in self.db_handler.psse_lookup_db.list_of_db_files:
                idx = self.db_handler.psse_lookup_db.list_of_db_files.index(
                    self.db_handler.psse_lookup_db.last_file_opened)
            else:
                idx = 0

        elif isinstance(self.circuit, CgmesCircuit):

            # we do this first so that the model changing does not trigger the on_combo_box_text_change function
            if self.db_handler.cgmes_lookup_db.last_file_opened in self.db_handler.cgmes_lookup_db.list_of_db_files:
                idx = self.db_handler.cgmes_lookup_db.list_of_db_files.index(
                    self.db_handler.cgmes_lookup_db.last_file_opened)
            else:
                idx = 0


        else:
            pass

    def get_process_threads(self):
        """
        Get all threads that has to do with processing
        :return: list of process threads
        """
        all_threads = [self.open_file_thread_object]
        return all_threads

    def get_all_threads(self):
        """
        Get all threads
        :return: list of all threads
        """
        all_threads = self.get_process_threads()
        return all_threads

    def any_thread_running(self):
        """
        Checks if any thread is running
        :return: True/False
        """
        val = False

        # this list cannot be created only once, because the None will be copied
        # instead of being a pointer to the future value like it would in a typed language
        all_threads = self.get_all_threads()

        for thr in all_threads:
            if thr is not None:
                if thr.isRunning():
                    return True
        return val

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

    def on_filter_combobox_changed(self):
        """
        Main property chooser for filtering table data
        """
        idx = self.ui.filterComboBox.currentIndex()

        if idx > -1:
            self.properties_proxy_model.setFilterKeyColumn(idx)

    def filter_properties_table(self):
        """
        Action of filtering the main table data
        """
        self.properties_proxy_model.setFilterRegularExpression(self.ui.filterLineEdit.text())

    def set_grid_model(self, circuit: Union[CgmesCircuit, PsseCircuit]):
        """
        Set a grid Model
        :param circuit: circuit model passed
        :param
        """
        if type(circuit) in [CgmesCircuit, PsseCircuit]:
            self.circuit = circuit

            self.display_circuit(trim_empty=True)

    def display_circuit(self, trim_empty=False):
        """

        :param trim_empty:
        :return:
        """
        if self.circuit is not None:
            classes = [prop.property_name for prop in self.circuit.get_class_properties()]
            classes.sort()

            if trim_empty:
                classes = [cl for cl in classes if len(self.circuit.get_objects_list(elm_type=cl)) > 0]

            # Table
            self.classes_model = get_list_model(classes)
            self.ui.clasesListView.setModel(self.classes_model)
            self.set_model_label()
            self.update_combo_boxes()

            # Tree
            self.current_model = get_cim_tree_model(self.circuit)
            self.treeProxyModel.setSourceModel(self.current_model)
            self.ui.mainTreeView.setModel(self.treeProxyModel)

            if self.console:
                for key, val in {'app': self,
                                 'circuit': self.circuit}.items():
                    self.console.add_var(key, val)

    def set_model_label(self):
        """
        Set the model label based on the model inner type
        """
        if isinstance(self.circuit, PsseCircuit):
            self.ui.modelTypeLabel.setText("PSSe")
            self.setWindowTitle(self.title + ': PSSe')

        elif isinstance(self.circuit, CgmesCircuit):
            self.ui.modelTypeLabel.setText("CGMES")
            self.setWindowTitle(self.title + ': CGMES')

        else:
            raise Exception('Unknown circuit type :(')

    def set_logger(self, logger: DataLogger, message=True):
        """
        Set the main logger
        :param logger: DataLogger object
        :param message: Open message if relevant
        """
        self.logger = logger  # assign the logger pointer
        logger_model = get_logger_tree_model(logger)  # crete tree model
        self.ui.loggerTreeView.setModel(logger_model)  # display

        if logger.size():
            error_msg(logger.get_message(), self.tr('Logger'))

    def on_class_click(self):
        """
        On click on the classes list...
        """
        # get the class type
        elm_type = self.ui.clasesListView.selectedIndexes()[0].data(role=QtCore.Qt.ItemDataRole.DisplayRole)

        # get the objects list of said class depending on the circuit type
        if isinstance(self.circuit, PsseCircuit):
            objects = self.circuit.get_objects_list(elm_type)

        elif isinstance(self.circuit, CgmesCircuit):
            objects = self.circuit.get_objects_list(elm_type)

        else:
            raise Exception('Unknown circuit type :(')

        # represent the model
        if len(objects) > 0:

            editable_headers = {p.property_name: p for p in objects[0].get_properties()}
            headers = [p.property_name for p in objects[0].get_properties()]

        else:

            editable_headers = dict()
            headers = list()

        self.ui.filterComboBox.setModel(get_list_model(headers))

        self.properties_model = RosetaObjectsModel(objects=objects,
                                                   editable_headers=editable_headers,
                                                   parent=self.ui.propertiesTableView,
                                                   editable=True,
                                                   non_editable_attributes=[],
                                                   dictionary_of_lists={})

        self.properties_proxy_model.setSourceModel(self.properties_model)
        self.ui.propertiesTableView.setModel(self.properties_proxy_model)

    def save_logs(self):
        """
        Save logger content
        """
        if self.logger.size():

            file, selected_filter = QtWidgets.QFileDialog.getSaveFileName(self, self.tr("Export logs"), '',
                                                                          filter=self.tr("Excel files (*.xlsx)"))

            if file != '':
                if 'xlsx' in selected_filter:
                    f = file
                    if not f.endswith('.xlsx'):
                        f += '.xlsx'
                    self.logger.to_xlsx(f)

                else:
                    error_msg(self.tr("{file_name} is not valid :(").format(file_name=file[0]))
        else:
            warning_msg(self.tr('There no logs :)'))

    # def launch_tree_view(self):
    #     """
    #     Launch tree view of the model
    #     """
    #     if self.circuit is not None:
    #
    #         if isinstance(self.circuit, CgmesCircuit):
    #             window = TreeModelViewerGUI()
    #             self.tree_navigation_windows.append(window)
    #             h = 740
    #             window.resize(int(1.61 * h), h)  # golden ratio :)
    #
    #             window.set_circuit(self.circuit)
    #
    #             window.show()
    #         else:
    #             info_msg("Only CGMES models are available for the tree view :/")
    #     else:
    #         warning_msg("There is not model :/")

    def new_rosetta_explorer(self, model: Union[PsseCircuit, CgmesCircuit, None] = None,
                             logger: Union[DataLogger, None] = None):
        """
        New roseta window
        :param model: (optional) the model to load
        :param logger: (optional) DataLogger to display
        """
        window = RosetaExplorerGUI(db_handler=self.db_handler)
        self.tree_navigation_windows.append(window)
        h = 740
        window.resize(int(1.61 * h), h)  # golden ratio :)

        if model is not None:
            window.set_grid_model(model)

        if logger is not None:
            window.set_logger(logger)

        window.show()

    def show_objects_context_menu(self, pos: QtCore.QPoint):
        """
        Show diagrams list view context menu
        :param pos: Relative click position
        """
        context_menu = QtWidgets.QMenu(parent=self.ui.propertiesTableView)

        add_menu_entry(menu=context_menu,
                       text=self.tr("Copy"),
                       icon_path=":/Icons/icons/copy.png",
                       function_ptr=self.copy_table_to_clipboard)

        mapped_pos: QtCore.QPoint = self.ui.propertiesTableView.viewport().mapToGlobal(pos)
        context_menu.exec(mapped_pos)

    def copy_table_to_clipboard(self) -> None:
        """
        Copy objects model to the clipboard
        """
        mdl = self.ui.propertiesTableView.model()

        if isinstance(mdl, QtCore.QSortFilterProxyModel):
            mdl = mdl.sourceModel()

        if isinstance(mdl, RosetaObjectsModel):
            mdl.copy_to_clipboard()
            info_msg(self.tr("Copied table to clipboard!"))
        elif isinstance(mdl, ObjectsModel):
            mdl.copy_to_clipboard()
            info_msg(self.tr("Copied table to clipboard!"))
        elif isinstance(mdl, PandasModel):
            mdl.copy_to_clipboard()
            info_msg(self.tr("Copied table to clipboard!"))

    @staticmethod
    def show_docs():
        """
        Show the docs
        """
        this_py_file = os.path.realpath(__file__)
        current_folder_path, current_folder_name = os.path.split(this_py_file)
        index_path = os.path.join(current_folder_path, '../..', '..', 'docs', 'html', 'index.html')
        if os.path.exists(index_path):
            webbrowser.open(index_path, new=2)
        else:
            error_msg(self.tr("The documentation could not be found under {index_path}").format(index_path=index_path))

    def about(self):
        """
        Show the "about" dialogue
        :return:
        """
        pass


    def filter_main_tree(self):
        self.treeProxyModel.setFilterRegularExpression(self.ui.filterLineEdit.text())

    def update_main_tree_on_click(self, index):
        # ix = self.proxyModel.mapToSource(index)
        # parent = self.current_model.itemFromIndex(ix)
        # for text in ['Object class', 'Property', 'Value']:
        #     children = QtGui.QStandardItem("{}_{}".format(parent.text(), text))
        #     parent.appendRow(children)
        # self.ui.mainTreeView.expand(index)
        pass

    def on_tree_expanded(self, index):
        if self.current_model is None:
            return
        src_index = self.treeProxyModel.mapToSource(index)
        item = self.current_model.itemFromIndex(src_index)
        if item is None:
            return
        populate_cim_item_children(item, editable=False)

    def on_tree_filter_combobox_changed(self):

        idx = self.ui.treeFilterComboBox.currentIndex()

        if idx > -1:
            self.treeProxyModel.setFilterKeyColumn(idx)
