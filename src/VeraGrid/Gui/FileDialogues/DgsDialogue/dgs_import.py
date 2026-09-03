# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from PySide6 import QtWidgets

from VeraGrid.Gui.FileDialogues.DgsDialogue.dgs_import_gui import Ui_DgsImportDialog
from VeraGridEngine.IO.file_open import FileOpenOptions
from VeraGridEngine.enumerations import DynamicSimulationMode


class DgsImportDialogue(QtWidgets.QDialog):
    """DGS import options dialogue bound to :class:`FileOpenOptions`."""

    def __init__(self, options: FileOpenOptions) -> None:
        """Initialize the DGS import options dialogue.

        :param options: Mutable file-open options object.
        :return: None.
        """
        QtWidgets.QDialog.__init__(self)
        self.ui = Ui_DgsImportDialog()
        self.ui.setupUi(self)
        self.setWindowTitle(self.tr('DGS import'))
        self.setModal(True)

        self.options: FileOpenOptions = options

        self.ui.dgsUseVscForInjectionsCheckBox.setChecked(self.options.dgs_use_vsc_for_injections)
        self.ui.dgsUseDynamicInformationCheckBox.setChecked(self.options.dgs_use_dynamic_information)
        self.ui.dgsDynamicSimulationModeComboBox.addItem(
            self.tr("RMS"),
            DynamicSimulationMode.RMS,
        )
        self.ui.dgsDynamicSimulationModeComboBox.addItem(
            self.tr("EMT"),
            DynamicSimulationMode.EMT,
        )

        selected_dynamic_simulation_mode: DynamicSimulationMode
        if self.options.dgs_dynamic_simulation_mode is None:
            selected_dynamic_simulation_mode = DynamicSimulationMode.RMS
        else:
            selected_dynamic_simulation_mode = self.options.dgs_dynamic_simulation_mode
        self.ui.dgsDynamicSimulationModeComboBox.setCurrentIndex(
            self.ui.dgsDynamicSimulationModeComboBox.findData(selected_dynamic_simulation_mode)
        )
        self.ui.dgsDynamicSimulationModeLabel.setEnabled(self.options.dgs_use_dynamic_information)
        self.ui.dgsDynamicSimulationModeComboBox.setEnabled(self.options.dgs_use_dynamic_information)

        self.ui.dgsUseDynamicInformationCheckBox.toggled.connect(
            self.ui.dgsDynamicSimulationModeLabel.setEnabled
        )
        self.ui.dgsUseDynamicInformationCheckBox.toggled.connect(
            self.ui.dgsDynamicSimulationModeComboBox.setEnabled
        )
        self.ui.importButton.clicked.connect(self.do_it)

    def do_it(self) -> None:
        """Store GUI values into :class:`FileOpenOptions` and close.

        :return: None.
        """
        self.options.dgs_use_vsc_for_injections = self.ui.dgsUseVscForInjectionsCheckBox.isChecked()
        self.options.dgs_use_dynamic_information = self.ui.dgsUseDynamicInformationCheckBox.isChecked()
        selected_index: int = self.ui.dgsDynamicSimulationModeComboBox.currentIndex()
        rms_index: int = self.ui.dgsDynamicSimulationModeComboBox.findData(DynamicSimulationMode.RMS)
        emt_index: int = self.ui.dgsDynamicSimulationModeComboBox.findData(DynamicSimulationMode.EMT)
        if selected_index == rms_index and rms_index >= 0:
            self.options.dgs_dynamic_simulation_mode = DynamicSimulationMode.RMS
        else:
            if selected_index == emt_index and emt_index >= 0:
                self.options.dgs_dynamic_simulation_mode = DynamicSimulationMode.EMT
            else:
                self.options.dgs_dynamic_simulation_mode = None
        self.close()
