# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6 import QtWidgets
from VeraGrid.Gui.FileDialogues.PsseDialogue.psse_import_gui import Ui_PsseImportDialog
from VeraGridEngine.IO.file_open import FileOpenOptions
from VeraGridEngine.basic_structures import Logger

if TYPE_CHECKING:
    from VeraGrid.Gui.Main.SubClasses.io import IoMain


class PsseImportDialogue(QtWidgets.QDialog):
    """
    GridMergeDialogue
    """

    def __init__(self, app: IoMain, options: FileOpenOptions):
        """
        GridMergeDialogue
        :param app: App pointer
        """
        QtWidgets.QDialog.__init__(self)
        self.ui = Ui_PsseImportDialog()
        self.ui.setupUi(self)
        self.setWindowTitle(self.tr('PSS/e import'))
        self.setModal(True)

        self.app = app

        self.logger = Logger()

        self.options = options

        self.ui.importButton.clicked.connect(self.do_it)

    def do_it(self):
        """

        :return:
        """
        self.options.psse_adjust_taps_to_discrete_positions = self.ui.adjust_taps_to_discrete_positions_checkBox.isChecked()
        self.options.psse_use_short_names = self.ui.use_short_names_checkBox.isChecked()
        self.options.psse_flatten_virtual_taps = self.ui.flatten_virtual_taps_checkBox.isChecked()
        self.close()
