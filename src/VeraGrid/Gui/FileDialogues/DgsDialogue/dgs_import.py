# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from VeraGrid.Gui.FileDialogues.DgsDialogue.dgs_import_gui import Ui_DgsImportDialog
from VeraGridEngine.IO.file_open import FileOpenOptions

if TYPE_CHECKING:
    from VeraGrid.Gui.Main.SubClasses.io import IoMain


class DgsImportDialogue(QtWidgets.QDialog):
    """DGS import options dialogue bound to :class:`FileOpenOptions`."""

    def __init__(self, app: IoMain, options: FileOpenOptions):
        """Initialize the DGS import options dialogue.

        :param app: Main I/O application controller.
        :param options: Mutable file-open options object.
        :return: None.
        """
        QtWidgets.QDialog.__init__(self)
        self.ui = Ui_DgsImportDialog()
        self.ui.setupUi(self)
        self.setWindowTitle('DGS import')
        self.setModal(True)

        self.app: IoMain = app
        self.options: FileOpenOptions = options

        self.ui.dgsUseVscForInjectionsCheckBox.setChecked(self.options.dgs_use_vsc_for_injections)
        self.ui.dgsUseDynamicInformationCheckBox.setChecked(self.options.dgs_use_dynamic_information)

        self.ui.importButton.clicked.connect(self.do_it)

    def do_it(self) -> None:
        """Store GUI values into :class:`FileOpenOptions` and close.

        :return: None.
        """
        self.options.dgs_use_vsc_for_injections = self.ui.dgsUseVscForInjectionsCheckBox.isChecked()
        self.options.dgs_use_dynamic_information = self.ui.dgsUseDynamicInformationCheckBox.isChecked()
        self.close()
