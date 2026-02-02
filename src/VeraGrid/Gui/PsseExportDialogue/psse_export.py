# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
import os
from PySide6 import QtWidgets
from VeraGrid.Gui.PsseExportDialogue.psse_export_gui import Ui_PsseExportDialog
from VeraGrid.Gui.general_dialogues import LogsDialogue
import VeraGrid.Session.file_handler as filedrv
from VeraGridEngine.basic_structures import Logger

if TYPE_CHECKING:
    from VeraGrid.Gui.Main.SubClasses.io import IoMain


class PsseExportDialogue(QtWidgets.QDialog):
    """
    GridMergeDialogue
    """

    def __init__(self, app: IoMain):
        """
        GridMergeDialogue
        :param App: App pointer
        """
        QtWidgets.QDialog.__init__(self)
        self.ui = Ui_PsseExportDialog()
        self.ui.setupUi(self)
        self.setWindowTitle('PSS/e export')
        self.setModal(True)

        self.app = app

        self.logger = Logger()
        self.logs_dialogue: LogsDialogue | None = None

        self.ui.raw_export_version_comboBox.addItems(["33", "35"])

        self.ui.exportButton.clicked.connect(self.export)

    def export(self):
        """

        :return:
        """
        raw_version = self.ui.raw_export_version_comboBox.currentText()

        options = filedrv.FileSavingOptions(raw_version=raw_version)

        # if the global file_name is empty, ask where to save
        fname = os.path.join(self.app.project_directory, self.app.ui.grid_name_line_edit.text())

        files_types = "PSS/e raw (*.raw);;PSS/e rawx (*.rawx)"
        filename, type_selected = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                        'Export to PSS/e',
                                                                        fname,
                                                                        files_types)

        if filename != '':

            # if the user did not enter the extension, add it automatically
            name, file_extension = os.path.splitext(filename)

            if file_extension == '':
                filename = name + '.raw'

            # we were able to compose the file correctly, now save it
            self.app.save_file_now(filename=filename,
                                   type_selected=type_selected,
                                   options=options)

            self.app.show_info_toast("PSS/e export done!")
            self.close()
