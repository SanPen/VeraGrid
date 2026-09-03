# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from PySide6 import QtWidgets

from VeraGrid.Gui.FileDialogues.DgsDialogue.dgs_import import DgsImportDialogue
from VeraGridEngine.IO.file_open import FileOpenOptions
from VeraGridEngine.enumerations import DynamicSimulationMode


def test_dgs_import_dialogue_stores_the_visible_dynamic_simulation_mode(
        qt_app: QtWidgets.QApplication,
) -> None:
    """Enable the RMS/EMT selector only for dynamic DGS imports and store its value."""

    options: FileOpenOptions = FileOpenOptions()
    dialogue: DgsImportDialogue = DgsImportDialogue(options=options)

    assert not dialogue.ui.dgsDynamicSimulationModeLabel.isEnabled()
    assert not dialogue.ui.dgsDynamicSimulationModeComboBox.isEnabled()
    assert dialogue.ui.dgsDynamicSimulationModeComboBox.currentIndex() == (
        dialogue.ui.dgsDynamicSimulationModeComboBox.findData(DynamicSimulationMode.RMS)
    )

    dialogue.ui.dgsUseDynamicInformationCheckBox.setChecked(True)
    dialogue.ui.dgsDynamicSimulationModeComboBox.setCurrentIndex(
        dialogue.ui.dgsDynamicSimulationModeComboBox.findData(DynamicSimulationMode.EMT)
    )
    qt_app.processEvents()

    assert dialogue.ui.dgsDynamicSimulationModeLabel.isEnabled()
    assert dialogue.ui.dgsDynamicSimulationModeComboBox.isEnabled()

    dialogue.do_it()

    assert options.dgs_use_dynamic_information
    assert options.dgs_dynamic_simulation_mode is DynamicSimulationMode.EMT
