# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import os
from typing import Union, List, Dict
from PySide6.QtCore import QThread, Signal
from PySide6 import QtWidgets
from PySide6.QtCore import Qt

from typing import Dict
from VeraGrid.Gui.GridMerge.build_diff_tree import populate_tree
from VeraGrid.Gui.GridMerge.grid_diff_gui import Ui_Dialog
from VeraGrid.Gui.general_dialogues import LogsDialogue
from VeraGrid.Gui.messages import error_msg, warning_msg

from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.enumerations import FileType
from VeraGrid.Session.session import SimulationSession
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.veragrid.zip_interface import get_session_tree, load_session_driver_objects
from VeraGridEngine.IO.file_open import FileOpen, FileOpenOptions
from VeraGridEngine.IO.file_save import FileSavingOptions, FileSave
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.multiverse import MultiVerse
from VeraGridEngine.IO.cim.cgmes.cgmes_circuit import CgmesCircuit
from VeraGridEngine.data_logger import DataLogger


class OpenAndDiffThread(QThread):
    """
    FileOpenThread
    """
    progress_signal = Signal(float)
    progress_text = Signal(str)
    done_signal = Signal()

    def __init__(self,
                 file_name: Union[str, List[str]],
                 current_grid: MultiCircuit,
                 options: FileOpenOptions = None):
        """
        Constructor
        :param file_name: file name (s)
        :param current_grid: MultiCircuit to use as base to create the diff
        """
        QThread.__init__(self)

        self.file_name: Union[str, List[str]] = file_name

        self.valid = False

        self.logger = Logger()

        self.circuit: Union[MultiCircuit, None] = None
        self.multiverse: Union[MultiVerse, None] = None

        self.options = options if options is not None else FileOpenOptions()

        self.cgmes_circuit: Union[CgmesCircuit, None] = None

        self.cgmes_logger: DataLogger = DataLogger()

        self.json_files = dict()

        self._current_grid= current_grid

        self.__cancel__ = False

        # Results
        self.all_elms_base_dict = dict()
        self.diff: MultiCircuit = MultiCircuit()

    def get_session_tree(self) -> Dict[str, Union[SimulationSession]]:
        """
        Get the session tree structure from a VeraGrid file
        :return:
        """
        if isinstance(self.file_name, str):
            if self.file_name.endswith('.gridcal') or self.file_name.endswith('.veragrid'):
                return get_session_tree(self.file_name)
            else:
                return dict()
        else:
            return dict()

    def load_session_objects(self, session_name: str, study_name: str):
        """
        Load the numpy objects of the session
        :param session_name: Name of the session (i.e. GUI Session)
        :param study_name: Name of the study i.e Power Flow)
        :return: Dictionary (name: array)
        """
        if isinstance(self.file_name, str):
            if self.file_name.endswith('.gridcal') or self.file_name.endswith('.veragrid'):
                return load_session_driver_objects(file_name_zip=self.file_name,
                                                   session_name=session_name,
                                                   study_name=study_name)
            else:
                return dict()
        else:
            return dict()

    def run(self) -> None:
        """
        run the file open procedure
        """
        self.circuit = MultiCircuit()

        if isinstance(self.file_name, list):
            path, fname = os.path.split(self.file_name[0])
            self.progress_text.emit('Loading ' + fname + '...')
        else:
            path, fname = os.path.split(self.file_name)
            self.progress_text.emit('Loading ' + fname + '...')

        self.logger = Logger()

        file_handler = FileOpen(file_name=self.file_name,
                                previous_circuit=None,
                                options=self.options)

        if self.options.crash_on_errors:
            self.circuit = file_handler.open(text_func=self.progress_text.emit,
                                             progress_func=self.progress_signal.emit)
        else:
            try:
                self.circuit = file_handler.open(text_func=self.progress_text.emit,
                                                 progress_func=self.progress_signal.emit)
            except ValueError as e:
                self.valid = False
                self.logger.add_error(msg=str(e))
                self.progress_text.emit('Error loading')
                self.done_signal.emit()
                return

        self.json_files = file_handler.json_files
        self.multiverse = file_handler.multiverse

        if self.circuit is None and self.multiverse is not None:
            self.circuit = self.multiverse.current_model

        self.cgmes_circuit = file_handler.cgmes_circuit
        self.cgmes_logger = file_handler.cgmes_logger

        self.logger += file_handler.logger
        self.valid = True

        # perform the diff if we actually loaded something
        if self.circuit is not None:

            if self.multiverse is None:
                # there is no multiverse
                base_grid: MultiCircuit = self.circuit
            else:
                # TODO: If we are in a multiverse case, shouldn't we compare all nodes?
                # there is a multiverse, choose the grid to make diff
                base_grid: MultiCircuit = self.multiverse.base_model

            # Create the base dictionary
            self.progress_text.emit('Computing base dictionary...')
            self.all_elms_base_dict, _ = base_grid.get_all_elements_dict(logger=self.logger)

            self.progress_text.emit('Computing grid differential...')
            ok, logger, self.diff = self._current_grid.differentiate_circuits(
                base_grid=base_grid,
                detailed_profile_comparison=True
            )

            self.logger += logger

        # post events
        self.progress_text.emit('Done!')

        self.done_signal.emit()

    def cancel(self) -> None:
        """
        Set the cancel flag
        """
        self.__cancel__ = True


class DiffSaveThread(QThread):
    """
    Thread to save
    """
    progress_signal = Signal(float)
    progress_text = Signal(str)
    done_signal = Signal()

    def __init__(self,
                 circuit: MultiCircuit,
                 file_name: str,
                 options: FileSavingOptions,
                 multiverse: MultiVerse | None = None,):
        """
        Constructor
        :param circuit: MultiCircuit instance
        :param file_name: name of the file where to save
        :param options: FileSavingOptions
        """
        QThread.__init__(self)

        self.circuit = circuit

        self.multiverse: MultiVerse | None = multiverse

        self.file_name = file_name

        self.valid = False

        self.options = options

        self.logger = Logger()

        self.error_msg = ''

        self.__cancel__ = False

    def get_session_tree(self) -> Dict:
        """
        Get the session tree structure from a VeraGrid file
        :return:
        """
        if isinstance(self.file_name, str):
            if self.file_name.endswith('.gridcal') or self.file_name.endswith('.veragrid'):
                return get_session_tree(self.file_name)
            else:
                return dict()
        else:
            return dict()

    def load_session_objects(self, session_name: str, study_name: str):
        """
        Load the numpy objects of the session
        :param session_name: Name of the session (i.e. GUI Session)
        :param study_name: Name of the study i.e Power Flow)
        :return: Dictionary (name: array)
        """
        if isinstance(self.file_name, str):
            if self.file_name.endswith('.gridcal') or self.file_name.endswith('.veragrid'):
                return load_session_driver_objects(self.file_name, session_name, study_name)
            else:
                return dict()
        else:
            return dict()

    def run(self) -> None:
        """
        run the file save procedure
        @return:
        """

        path, fname = os.path.split(self.file_name)

        self.progress_text.emit('Flushing ' + fname + ' into ' + fname + '...')

        self.logger = Logger()

        file_handler = FileSave(circuit=self.circuit,
                                file_name=self.file_name,
                                options=self.options,
                                multiverse=self.multiverse,
                                text_func=self.progress_text.emit,
                                progress_func=self.progress_signal.emit)
        try:
            self.logger = file_handler.save()
        except PermissionError:
            self.logger.add_error("File permission denied. Do you have the file open? Do you have write permissions?")

        self.valid = True

        # post events
        self.progress_text.emit('Done!')

        self.done_signal.emit()

    def cancel(self):
        """
        Activate the cancel flag
        """
        self.__cancel__ = True

class GridDiffDialogue(QtWidgets.QDialog):
    """
    GridDiffDialogue
    """

    def __init__(self, grid: MultiCircuit):
        """

        :param grid:
        """
        QtWidgets.QDialog.__init__(self)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(self.tr('Grid differential'))

        self.ui.treeWidget.setHeaderLabels(
            ["Grid", "Object type", "action", "idtag", "name", "property", "value", "new value"]
        )

        self.logger = Logger()

        self._current_grid: MultiCircuit = grid

        self.all_elms_base_dict: Dict[str, ALL_DEV_TYPES] = {}
        self.diff_objects_dict: Dict[str, ALL_DEV_TYPES] = {}
        _, ok = self._current_grid.get_all_elements_dict(logger=self.logger)

        if not ok:
            dlg = LogsDialogue(self.tr('The circuit has duplicated idtags and cannot be differentiated :('), self.logger)
            dlg.exec()
            return

        self._diff: MultiCircuit | None = None

        self.added_grid: bool = False
        self.merged_grid: bool = False
        self.ui.addButton.setText("Open base")
        self.ui.acceptButton.setText("Save diff")

        self.open_file_thread_object: OpenAndDiffThread = None
        self.save_file_thread_object: DiffSaveThread = None

        self.ui.progressFrame.setVisible(False)

        # tree item changes
        self.ui.treeWidget.itemChanged.connect(self.handle_item_changed)
        self.ui.acceptButton.clicked.connect(self.save_diff)
        self.ui.addButton.clicked.connect(self.open_base_grid)

    def any_thread_running(self) -> bool:
        """
        Check if any background worker owned by this dialog is still active.
        """
        for thread in (self.open_file_thread_object, self.save_file_thread_object):
            if thread is not None and thread.isRunning():
                return True

        return False

    def open_base_grid(self):
        """
        Open base grid
        :return:
        """
        files_types = "VeraGrid (*.gridcal, *.veragrid)"

        filename, type_selected = QtWidgets.QFileDialog.getOpenFileName(parent=self,
                                                                        caption=self.tr("Open base grid"),
                                                                        filter=files_types)

        if len(filename) > 0:
            if os.path.exists(filename):
                # create thread
                self.open_file_thread_object = OpenAndDiffThread(
                    file_name=filename,
                    current_grid=self._current_grid,
                    options=FileOpenOptions(
                        file_type=FileType.VeraGrid
                    )
                )

                # make connections
                self.open_file_thread_object.progress_signal.connect(self.ui.progressBar.setValue)
                self.open_file_thread_object.progress_text.connect(self.ui.progressLabel.setText)
                self.open_file_thread_object.done_signal.connect(self.post_open_base_grid)

                # thread start
                self.ui.progressFrame.setVisible(True)
                self.open_file_thread_object.start()
            else:
                error_msg(
                    title=self.tr("File not found"),
                    text=self.tr("{file_name} not found :(").format(file_name=filename),
                )

        else:
            self.open_file_thread_object = None

    def post_open_base_grid(self):
        """
        After open, make the diff
        :return:
        """
        thread = self.open_file_thread_object
        self.open_file_thread_object = None

        if thread is not None:

            if thread.valid:

                # assign the loaded circuit
                if thread.circuit is not None:

                    # Create the base dictionary
                    self.all_elms_base_dict = thread.all_elms_base_dict
                    self._diff = thread.diff

                    if self._diff is not None:
                        self.diff_objects_dict, _ = self._diff.get_all_elements_dict(logger=self.logger)

                        if thread.logger.has_logs():
                            dlg = LogsDialogue(self.tr('Errors while computing the differential :('),
                                               thread.logger)
                            dlg.exec()
                    else:
                        pass

                    self.build_tree()


        self.ui.progressFrame.setVisible(False)

    def build_tree(self):
        """
        Build the display tree
        """
        all_no_action = populate_tree(tree_widget=self.ui.treeWidget,
                                      base=self._current_grid,
                                      diff=self._diff,
                                      all_elms_base_dict=self.all_elms_base_dict,
                                      diff_creation=True)

    def handle_item_changed(self, item: QtWidgets.QTreeWidgetItem, column: int):
        """

        :param item:
        :param column: This must be here because this is an event handler
        :return:
        """
        if column != 0:
            return

        if item.parent() is None:
            idtag = item.text(3)
            elm = self.diff_objects_dict.get(idtag)

            if elm is None:
                return

            selected = item.checkState(0) == Qt.CheckState.Checked
            elm.selected_to_merge = selected

            previous_signals_blocked = self.ui.treeWidget.blockSignals(True)
            try:
                for i in range(item.childCount()):
                    child = item.child(i)
                    child.setCheckState(0, item.checkState(0))
                    elm.set_diff_change(property_name=child.text(5), selected=selected)
            finally:
                self.ui.treeWidget.blockSignals(previous_signals_blocked)

            return

        parent_item = item.parent()
        idtag = parent_item.text(3)
        elm = self.diff_objects_dict.get(idtag)

        if elm is None:
            return

        elm.set_diff_change(
            property_name=item.text(5),
            selected=item.checkState(0) == Qt.CheckState.Checked
        )

    def save_diff(self):
        """
        Apply the changes
        :return:
        """
        if self._diff is None:
            error_msg(text=self.tr("No differential created :(\nDid you load a base grid to compare?"),
                      title=self.tr("No diff"))
        else:
            # select the file to save
            filename, type_selected = QtWidgets.QFileDialog.getSaveFileName(self, self.tr('Save file'),
                                                                            self._diff.name,
                                                                            self.tr("VeraGrid diff (*.dveragrid)"))

            if filename != '':

                # if the user did not enter the extension, add it automatically
                name, file_extension = os.path.splitext(filename)

                if file_extension == '':
                    filename = name + ".dveragrid"

                self.save_file_thread_object = DiffSaveThread(
                    circuit=self._diff,
                    file_name=filename,
                    options=FileSavingOptions(
                        file_type=FileType.VeraGrid_delta
                    )
                )

                # make connections
                self.save_file_thread_object.progress_signal.connect(self.ui.progressBar.setValue)
                self.save_file_thread_object.progress_text.connect(self.ui.progressLabel.setText)
                self.save_file_thread_object.done_signal.connect(self.post_save_diff)

                # thread start
                self.ui.progressFrame.setVisible(True)
                self.save_file_thread_object.start()

    def post_save_diff(self):
        """

        :return:
        """
        self.save_file_thread_object = None
        self.ui.progressFrame.setVisible(False)
        self.close()

    def closeEvent(self, event) -> None:
        """
        Keep the dialog alive until its worker threads finish to avoid tearing
        down QThread wrappers while Qt is still delivering their signals.
        """
        if self.any_thread_running():
            warning_msg(self.tr("Wait for the differential worker to finish before closing this window."),
                        self.tr("Grid differential"))
            event.ignore()
            return

        super().closeEvent(event)
