# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import os
import re
import json
import numpy as np
import pandas as pd
from PySide6 import QtWidgets, QtCore
from typing import List, Dict
from datetime import datetime, timedelta

import VeraGrid.Gui.gui_functions as gf
from VeraGrid.Gui.messages import yes_no_question
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.file_open import FileOpen
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Utils.progress_bar import print_progress_bar
from VeraGrid.Gui.FileDialogues.ProfilesInput.profiles_from_models_gui import Ui_Dialog


def extract_and_convert_to_datetime(filename, logger: Logger) -> pd.Timestamp | None:
    """
    Try to extract date from file name
    :param filename: file name
    :param logger: Logger
    :return: pd.DateTimeIndex or None
    """
    date_patterns = [
        (r'(?<!\d)(\d{8}_\d{4})(?!\d)', '%Y%m%d_%H%M'),  # YYYYMMDD_HHMM
        (r'(?<!\d)(\d{12})(?!\d)', '%Y%m%d%H%M'),  # YYYYMMDDHHMM
        (r'(?<!\d)(\d{4}-\d{2}-\d{2}_\d{4})(?!\d)', '%Y-%m-%d_%H%M'),  # YYYY-MM-DD_HHMM
        (r'(?<!\d)(\d{4}_\d{2}_\d{2}_\d{4})(?!\d)', '%Y_%m_%d_%H%M'),  # YYYY_MM_DD_HHMM
        (r'(?<!\d)(\d{4}-\d{2}-\d{2})(?!\d)', '%Y-%m-%d'),  # YYYY-MM-DD
        (r'(?<!\d)(\d{4}_\d{2}_\d{2})(?!\d)', '%Y_%m_%d'),  # YYYY_MM_DD
        (r'(?<!\d)(\d{8})(?!\d)', '%Y%m%d')  # YYYYMMDD
    ]

    date_str = filename
    for date_pattern, frmt in date_patterns:
        match = re.search(date_pattern, filename)
        if match:
            date_str = match.group(1)

            # Try to parse the date string
            try:
                date_object = pd.to_datetime(date_str, format=frmt, errors='raise')

                return date_object
            except ValueError:
                # print(f"Unable to parse date from: {date_str}")
                pass

    logger.add_error(msg="Unable to parse date from", value=date_str)

    return None  # Return None if no valid date is found


class GridsModelItem:
    """
    GridsModelItem
    """

    def __init__(self, path: str, tme: pd.Timestamp, logger: Logger):
        """

        :param path:
        :param tme:
        :param logger:
        """
        suggested_tme = extract_and_convert_to_datetime(filename=os.path.basename(path), logger=logger)
        self.time: pd.Timestamp = suggested_tme if suggested_tme is not None else tme

        self.path: str = path

        self.name: str = os.path.basename(path)

    def get_at(self, idx: int) -> str | pd.Timestamp:
        """

        :param idx:
        :return:
        """
        # 'Time', 'Name', 'Folder'
        if idx == 0:
            return self.time
        if idx == 1:
            return self.name
        elif idx == 2:
            return self.path
        else:
            return ''


class GridsModel(QtCore.QAbstractTableModel):
    """
    GridsModel
    """

    def __init__(self, logger: Logger) -> None:
        """

        """
        QtCore.QAbstractTableModel.__init__(self)

        self.logger: Logger = logger
        self.row_mime_type: str = "application/x-veragrid-model-row"
        self._values_: List[GridsModelItem] = list()

        self._headers_ = ['Time', 'Name', 'Path']

    def update(self):
        """
        update table
        """
        self.layoutAboutToBeChanged.emit()
        self.layoutChanged.emit()

    def clear(self) -> None:
        """

        :return:
        """
        self._values_.clear()
        self.update()

    def append(self, val: GridsModelItem):
        """

        :param val:
        :return:
        """
        self._values_.append(val)
        self.update()

    def set_path_at(self, i: int, path: str):
        """

        :param i:
        :param path:
        :return:
        """
        if i < len(self._values_):
            self._values_[i].path = path
            self._values_[i].name = os.path.basename(path)
        self.update()

    def items(self) -> List[GridsModelItem]:
        """

        :return:
        """
        return self._values_

    def remove(self, idx: int):
        """

        :param idx:
        :return:
        """
        self._values_.pop(idx)
        self.update()

    def add_path(self, path: str) -> None:
        """
        Add one file path to the model.

        :param path: File system path to add.
        :return: None
        """
        item_count: int = len(self._values_)
        current_date: datetime = datetime.today()
        base_date: datetime = datetime(current_date.year, 1, 1, 0, 0, 0)
        base_increment_hours: int = 1

        tme_value = pd.Timestamp(base_date + timedelta(hours=base_increment_hours * item_count))
        if not pd.isna(tme_value):
            tme: pd.Timestamp = tme_value

            # Build the item here so dropped files and manually added files follow
            # the same filename-to-time proposal path.
            self._values_.append(GridsModelItem(path=path, tme=tme, logger=self.logger))
        else:
            print(f"path: {path}, failed to convert date :/")

    def add_paths(self, paths: List[str]) -> None:
        """
        Add many file paths to the model.

        :param paths: File system paths to add.
        :return: None
        """
        path: str

        for path in paths:
            if os.path.isfile(path):
                self.add_path(path=path)
            else:
                pass

        self.update()

    def rowCount(self, parent: QtCore.QModelIndex = None) -> int:
        """

        :param parent:
        :return:
        """
        return len(self._values_)

    def columnCount(self, parent: QtCore.QModelIndex = None) -> int:
        """

        :param parent:
        :return:
        """
        return len(self._headers_)

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> None | str:
        """

        :param index:
        :param role:
        :return:
        """
        if index.isValid():
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                # return self.formatter(self._data[index.row(), index.column()])
                return str(self._values_[index.row()].get_at(index.column()))
        return None

    def headerData(self,
                   section: int,
                   orientation: QtCore.Qt.Orientation,
                   role=QtCore.Qt.ItemDataRole.DisplayRole):
        """

        :param section:
        :param orientation:
        :param role:
        :return:
        """
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return self._headers_[section]
            elif orientation == QtCore.Qt.Orientation.Vertical:
                return section
        return None

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        """

        :param index:
        :return:
        """
        if index.isValid():
            return (QtCore.Qt.ItemFlag.ItemIsDropEnabled |
                    QtCore.Qt.ItemFlag.ItemIsEnabled |
                    QtCore.Qt.ItemFlag.ItemIsEditable |
                    QtCore.Qt.ItemFlag.ItemIsSelectable |
                    QtCore.Qt.ItemFlag.ItemIsDragEnabled)
        else:
            return QtCore.Qt.ItemFlag.ItemIsDropEnabled

    def supportedDropActions(self):
        """

        :return:
        """
        return QtCore.Qt.DropAction.MoveAction | QtCore.Qt.DropAction.CopyAction

    def supportedDragActions(self):
        """
        Declare the drag actions generated by the model.

        :return: Supported drag actions.
        """
        return QtCore.Qt.DropAction.MoveAction

    def mimeTypes(self) -> List[str]:
        """
        Declare the MIME types accepted by the model.

        :return: Accepted MIME types.
        """
        mime_types: List[str] = list()
        mime_types.append(self.row_mime_type)
        mime_types.append("text/uri-list")
        return mime_types

    def mimeData(self, indexes: List[QtCore.QModelIndex]) -> QtCore.QMimeData:
        """
        Export dragged rows to a custom MIME payload.

        :param indexes: Selected indexes provided by Qt.
        :return: MIME data containing unique dragged row indexes.
        """
        mime_data: QtCore.QMimeData = QtCore.QMimeData()
        row_indexes: List[int] = list()
        index: QtCore.QModelIndex
        row_index: int
        payload_text: str

        # The table may provide one index per selected cell. Reduce that to
        # unique row numbers because reordering moves full rows.
        for index in indexes:
            row_index = index.row()
            if row_index not in row_indexes:
                row_indexes.append(row_index)
            else:
                pass

        row_indexes.sort()
        payload_text = json.dumps(row_indexes)
        mime_data.setData(self.row_mime_type, payload_text.encode("utf-8"))
        return mime_data

    def dropMimeData(self, data: QtCore.QMimeData,
                     action: QtCore.Qt.DropAction,
                     row: int, column: int,
                     parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex) -> bool:
        """

        :param data:
        :param action:
        :param row:
        :param column:
        :param parent:
        :return:
        """
        payload: bytes
        payload_text: str
        source_rows: List[int]
        source_row: int
        drop_row: int
        moved_items: List[GridsModelItem] = list()
        item: GridsModelItem
        url_list: List[QtCore.QUrl]
        local_paths: List[str] = list()
        url: QtCore.QUrl
        local_path: str

        del column

        if action == QtCore.Qt.DropAction.IgnoreAction:
            return True
        else:
            pass

        if data.hasFormat(self.row_mime_type):
            payload = bytes(data.data(self.row_mime_type))
            payload_text = payload.decode("utf-8")
            source_rows = json.loads(payload_text)

            if row >= 0:
                drop_row = row
            else:
                if parent.isValid():
                    drop_row = parent.row()
                else:
                    drop_row = len(self._values_)

            # Copy moved items first because row removal mutates the backing
            # list and would invalidate later source indexes.
            for source_row in source_rows:
                if 0 <= source_row < len(self._values_):
                    moved_items.append(self._values_[source_row])
                else:
                    pass

            # Remove from the end so indexes that are still pending do not
            # shift under the loop.
            for source_row in reversed(source_rows):
                if 0 <= source_row < len(self._values_):
                    self._values_.pop(source_row)
                    if source_row < drop_row:
                        drop_row = drop_row - 1
                    else:
                        pass
                else:
                    pass

            # Insert the block at the resolved destination while preserving the
            # original order of the dragged rows.
            for item in moved_items:
                self._values_.insert(drop_row, item)
                drop_row = drop_row + 1

            self.update()
            return True
        else:
            pass

        if data.hasUrls():
            url_list = data.urls()

            for url in url_list:
                local_path = url.toLocalFile()
                if local_path != "":
                    local_paths.append(local_path)
                else:
                    pass

            if len(local_paths) > 0:
                self.add_paths(paths=local_paths)
                return True
            else:
                return False
        else:
            return False


class ModelsProcessThread(QtCore.QThread):
    """
    Run the model-to-profile import in a background thread.
    """
    progress_signal = QtCore.Signal(float)
    done_signal = QtCore.Signal()

    def __init__(self,
                 gui_instance: "ModelsInputGUI",
                 main_grid: MultiCircuit,
                 logger: Logger,
                 items: List[GridsModelItem],
                 use_secondary_key: bool) -> None:
        """
        Create the worker thread.

        :param gui_instance: Dialogue owning the import logic.
        :param main_grid: Grid that will receive the imported profiles.
        :param logger: Logger collecting import messages.
        :param items: Snapshot of the items to import.
        :param use_secondary_key: Matching mode selected in the dialogue.
        """
        QtCore.QThread.__init__(self)

        self.gui_instance: ModelsInputGUI = gui_instance
        self.main_grid: MultiCircuit = main_grid
        self.logger: Logger = logger
        self.items: List[GridsModelItem] = items
        self.use_secondary_key: bool = use_secondary_key
        self.cancel_requested: bool = False

    def run(self) -> None:
        """
        Execute the import algorithm outside the GUI thread.

        :return: None
        """
        self.gui_instance.process(
            main_grid=self.main_grid,
            logger=self.logger,
            items=self.items,
            use_secondary_key=self.use_secondary_key,
            progress_func=self.progress_signal.emit
        )
        self.done_signal.emit()

    def cancel(self) -> None:
        """
        Request cooperative cancellation.

        :return: None
        """
        self.cancel_requested = True


def build_main_elements_dict_by_type(main_grid: MultiCircuit,
                                     use_secondary_key: bool) -> Dict[object, Dict[str, object]]:
    """
    Build the element lookup dictionaries once for the whole import run.

    :param main_grid: Main grid receiving the imported profiles.
    :param use_secondary_key: Use the secondary key ("code") to match.
    :return: Lookup dictionaries indexed by device type.
    """
    main_elements_dict_by_type: Dict[object, Dict[str, object]] = dict()
    dev_template: object
    device_type: object

    # Precompute the dictionaries once because rebuilding them for every file
    # and every device type repeats the same work many times.
    for dev_template in main_grid.template_items():
        device_type = dev_template.device_type
        main_elements_dict_by_type[device_type] = main_grid.get_elements_dict_by_type(
            device_type,
            use_secondary_key=use_secondary_key
        )

    return main_elements_dict_by_type


class ModelsInputGUI(QtWidgets.QDialog):
    """
    ModelsInputGUI
    """

    def __init__(self, parent=None, main_grid: MultiCircuit | None = None) -> None:
        """

        :param parent:
        :param main_grid: Grid receiving the imported profiles.
        """

        QtWidgets.QDialog.__init__(self, parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle('Models import dialogue')

        self.logger = Logger()
        self.grids_model: GridsModel = GridsModel(logger=self.logger)
        self.main_grid: MultiCircuit | None = main_grid
        self.process_logger: Logger = Logger()
        self.process_thread: ModelsProcessThread | None = None
        self.processing_active: bool = False
        self.close_after_processing: bool = False

        self.ui.matchUsingCodeCheckBox.setChecked(True)
        self.ui.progressBar.setValue(0)

        self.ui.modelsTableView.setModel(None)
        self.ui.modelsTableView.setModel(self.grids_model)
        self.ui.modelsTableView.setAcceptDrops(True)
        self.ui.modelsTableView.viewport().setAcceptDrops(True)
        self.ui.modelsTableView.setDropIndicatorShown(True)
        self.ui.modelsTableView.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.ui.modelsTableView.setDefaultDropAction(QtCore.Qt.DropAction.CopyAction)
        self.ui.modelsTableView.repaint()

        # click
        self.ui.addModelsButton.clicked.connect(self.add_models)
        self.ui.acceptModelsButton.clicked.connect(self.start_process)
        self.ui.deleteModelsButton.clicked.connect(self.clear_model)

    def accept(self) -> None:
        """

        :return:
        """
        super().accept()
        self.close()

    def reject(self) -> None:
        """
        Intercept escape-key and reject-button closure while processing.

        :return: None
        """
        if self.processing_active:
            self.prompt_close_while_processing()
        else:
            QtWidgets.QDialog.reject(self)

    def closeEvent(self, event: gf.QtGui.QCloseEvent) -> None:
        """
        Prompt before closing while the import thread is still running.

        :param event: Qt close event.
        :return: None
        """
        if self.processing_active:
            if self.prompt_close_while_processing():
                event.ignore()
            else:
                event.ignore()
        else:
            QtWidgets.QDialog.closeEvent(self, event)

    def clear_model(self) -> None:
        """
        Delete the import data
        :return:
        """
        if self.grids_model.rowCount() > 0:
            ok = yes_no_question("Do you want to clear the import data?")
            if ok:
                self.grids_model.clear()

    def add_models(self) -> None:
        """
        Add the selected models
        """
        # declare the allowed file types
        files_types = "Formats (*.raw *.RAW *.rawx *.xml *.m *.matpower *.epc *.EPC *.dgs *.p *.uct *.UCT)"

        # call dialog to select the file
        filenames, type_selected = QtWidgets.QFileDialog.getOpenFileNames(self, 'Add files', filter=files_types)

        if len(filenames):
            self.grids_model.add_paths(paths=filenames)
            self.ui.modelsTableView.setModel(None)
            self.ui.modelsTableView.setModel(self.grids_model)
            self.ui.modelsTableView.repaint()

    def start_process(self) -> None:
        """
        Start the import in a background thread and report progress in the dialogue.

        :return: None
        """
        if self.processing_active:
            return

        if self.main_grid is None:
            return

        if self.grids_model.rowCount() == 0:
            self.accept()
        else:
            items_snapshot: List[GridsModelItem] = list(self.grids_model.items())
            use_secondary_key: bool = self.ui.matchUsingCodeCheckBox.isChecked()

            self.processing_active = True
            self.close_after_processing = False
            self.process_logger = Logger()
            self.ui.progressBar.setValue(0)
            self.ui.acceptModelsButton.setEnabled(False)
            self.ui.addModelsButton.setEnabled(False)
            self.ui.deleteModelsButton.setEnabled(False)
            self.ui.modelsTableView.setEnabled(False)
            self.ui.matchUsingCodeCheckBox.setEnabled(False)
            # Keep the worker object on the dialogue so Qt signals stay valid
            # until the import completes and the window closes.
            self.process_thread = ModelsProcessThread(
                gui_instance=self,
                main_grid=self.main_grid,
                logger=self.process_logger,
                items=items_snapshot,
                use_secondary_key=use_secondary_key
            )
            self.process_thread.progress_signal.connect(self.ui.progressBar.setValue)
            self.process_thread.done_signal.connect(self.on_process_done)
            self.process_thread.start()

    def on_process_done(self) -> None:
        """
        Finalize the threaded import and close the dialogue.

        :return: None
        """
        thread_to_close: ModelsProcessThread | None = self.process_thread

        self.processing_active = False
        self.ui.progressBar.setValue(100)
        self.ui.acceptModelsButton.setEnabled(True)
        self.ui.addModelsButton.setEnabled(True)
        self.ui.deleteModelsButton.setEnabled(True)
        self.ui.modelsTableView.setEnabled(True)
        self.ui.matchUsingCodeCheckBox.setEnabled(True)

        # Wait for the worker to exit fully before dropping the reference so
        # the dialogue never keeps a half-finished QThread alive.
        if thread_to_close is not None:
            thread_to_close.wait()
            thread_to_close.deleteLater()
            self.process_thread = None
        else:
            pass

        self.accept()

    def prompt_close_while_processing(self) -> bool:
        """
        Ask whether the running import should be cancelled and the window closed.

        :return: ``True`` when the close request was accepted.
        """
        ok: bool = yes_no_question(
            "There is an import procedure running.\nCancel it and close the window?"
        )

        if ok:
            self.close_after_processing = True
            self.ui.acceptModelsButton.setEnabled(False)
            self.ui.addModelsButton.setEnabled(False)
            self.ui.deleteModelsButton.setEnabled(False)
            self.ui.modelsTableView.setEnabled(False)
            self.ui.matchUsingCodeCheckBox.setEnabled(False)

            if self.process_thread is not None:
                self.process_thread.cancel()
            else:
                pass
            return True
        else:
            return False

    def generate_time_array(self,
                            main_grid: MultiCircuit,
                            logger: Logger,
                            items: List[GridsModelItem]) -> None:
        """
        Generate time profile from model
        :param main_grid:
        :param logger:
        :param items:
        :return:
        """
        n: int = len(items)
        t: int
        entry: GridsModelItem

        t_profile = np.zeros(n, dtype=object)

        d: datetime = datetime.today()
        base_date: datetime = datetime(d.year, 1, 1, 0, 0, 0)
        base_inc: int = 1  # 1 hour

        # Use the same item snapshot that the worker thread processes so the
        # time array matches the filename-derived timestamps shown in the table.
        for t, entry in enumerate(items):
            if entry.time is not None:
                if isinstance(entry.time, pd.DatetimeIndex):
                    t_profile[t] = entry.time
                else:
                    try:
                        t_profile[t] = pd.to_datetime(entry.time)
                    except ValueError:
                        t_profile[t] = base_date + timedelta(hours=base_inc * t)
                        logger.add_info(msg="Could not convert time",
                                        device="time array",
                                        device_property="",
                                        value=str(entry.time))

        # set the circuit time profile
        main_grid.time_profile = pd.to_datetime(t_profile)
        main_grid.ensure_profiles_exist()

    def process(self,
                main_grid: MultiCircuit,
                logger: Logger,
                items: List[GridsModelItem],
                use_secondary_key: bool,
                progress_func=None) -> None:
        """
        Process the imported data
        :param main_grid: Grid to apply the values to, it has to have declared profiles already
        :param logger: Logger
        :param items: Snapshot of the model items to import.
        :param use_secondary_key: Use the secondary key ("code") to match.
        :param progress_func: Function to report percentage progress.
        :return: None
        """
        n: int = len(items)
        t: int
        entry: GridsModelItem
        name: str
        loaded_grid: MultiCircuit | None
        progress_value: float
        worker_thread: ModelsProcessThread | None = self.process_thread
        main_elements_dict_by_type: Dict[object, Dict[str, object]]

        self.generate_time_array(main_grid=main_grid, logger=logger, items=items)

        main_elements_dict_by_type = build_main_elements_dict_by_type(
            main_grid=main_grid,
            use_secondary_key=use_secondary_key
        )

        if progress_func is not None:
            progress_func(0.0)
        else:
            pass

        for t, entry in enumerate(items):
            if worker_thread is not None and worker_thread.cancel_requested:
                logger.add_warning(msg="Import cancelled by the user",
                                   device="Profiles import",
                                   value=entry.path)
                break
            else:
                pass

            name = os.path.basename(entry.path)

            if os.path.exists(entry.path):
                loaded_grid = FileOpen(entry.path).open()
                main_grid.assign_grid(
                    t=t,
                    grid_to_add=loaded_grid,
                    main_elements_dict_by_type=main_elements_dict_by_type,
                    use_secondary_key=use_secondary_key,
                    logger=logger
                )

                logger.add_info(msg="Loaded grid",
                                device=name,
                                device_property="Path",
                                value=entry.path)
            else:
                pass

            # Report progress after each imported model because file loading is
            # the dominant cost in the algorithm and users need coarse but
            # reliable feedback.
            if progress_func is not None:
                progress_value = ((t + 1) * 100.0) / n if n > 0 else 100.0
                progress_func(progress_value)
            else:
                # Show progress bar only if there is no progress_func pointer
                print_progress_bar(iteration=t + 1, total=n, txt=name)

        print()  # to finalize the progressbar

        # check devices' status: if an element is connected to disconnected
        # buses the branch must be disconnected too. This is to handle the
        # typical PSSe garbage modelling practices
        for elm in main_grid.get_branches_iter(add_vsc=True, add_hvdc=True):
            if not (elm.bus_from.active and elm.bus_to.active):
                elm.active = False
                logger.add_warning(msg="Inconsistent active state",
                                   device=elm.name,
                                   device_property="Snapshot")

            for t in range(main_grid.get_time_number()):
                if not (elm.bus_from.active_prof[t] and elm.bus_to.active_prof[t]):
                    elm.active_prof[t] = False
                    logger.add_warning(msg="Inconsistent active state",
                                       device=elm.name,
                                       device_property=str(t))

        for elm in main_grid.get_injection_devices_iter():
            if not elm.bus.active:
                elm.active = False
                logger.add_warning(msg="Inconsistent active state",
                                   device=elm.name,
                                   device_property="Snapshot")

            for t in range(main_grid.get_time_number()):
                if not elm.bus.active_prof[t]:
                    elm.active_prof[t] = False
                    logger.add_warning(msg="Inconsistent active state",
                                       device=elm.name,
                                       device_property=str(t))

        if progress_func is not None:
            progress_func(100.0)
        else:
            pass

# if __name__ == "__main__":
#     import sys
#     app = QtWidgets.QApplication(sys.argv)
#     window = ModelsInputGUI()
#     window.resize(1.61 * 700.0, 600.0)  # golden ratio
#     window.show()
#     sys.exit(app.exec())
