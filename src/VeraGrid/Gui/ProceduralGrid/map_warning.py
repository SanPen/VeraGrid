# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from PySide6 import QtWidgets
from VeraGrid.Gui.ProceduralGrid.map_warning_ui import Ui_Dialog


class MapWarningDialog(QtWidgets.QDialog):
    """
    Warning dialog for missing Map diagram selection.
    """

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.ui = Ui_Dialog() # antes era self.ui = Ui_MapWarningDialog()
        self.ui.setupUi(self)
        self.setWindowTitle(self.tr('Action Required'))

        # Connect the OK button to close the window
        self.ui.okButton.clicked.connect(self.accept)