# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets

import VeraGrid.Gui.gui_functions as gf
from VeraGrid.Gui.FileDialogues.CGMESDialogue.cgmes_import_gui import Ui_CgmesImportDialog
from VeraGridEngine.IO.file_open import FileOpenOptions
from VeraGridEngine.enumerations import CGMESVersions, CgmesTopologyMode
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesRecoveryMode

if TYPE_CHECKING:
    from VeraGrid.Gui.Main.SubClasses.io import IoMain


class CgmesImportDialogue(QtWidgets.QDialog):
    """CGMES import options dialogue bound to :class:`FileOpenOptions`."""

    def __init__(self, app: IoMain, options: FileOpenOptions):
        """Initialize the CGMES import options dialogue.

        :param app: Main I/O application controller.
        :param options: Mutable file-open options object.
        :return: None.
        """
        QtWidgets.QDialog.__init__(self)
        self.ui = Ui_CgmesImportDialog()
        self.ui.setupUi(self)
        self.setWindowTitle('CGMES import')
        self.setModal(True)

        self.app: IoMain = app
        self.options: FileOpenOptions = options

        self._version_values = list(CGMESVersions)
        self._topology_values = list(CgmesTopologyMode)
        self._recovery_values = list(CgmesRecoveryMode)

        self.ui.cgmesVersionComboBox.setModel(gf.ComboModel(enum_values=self._version_values, translate=self.tr))
        self.ui.cgmesTopologyComboBox.setModel(gf.ComboModel(enum_values=self._topology_values, translate=self.tr))
        self.ui.cgmesRecoveryComboBox.setModel(gf.ComboModel(enum_values=self._recovery_values, translate=self.tr))

        self._set_initial_values()
        self.ui.importButton.clicked.connect(self.do_it)

    def _set_initial_values(self) -> None:
        """Populate widgets from current :class:`FileOpenOptions` values.

        :return: None.
        """
        version = self.options.cgmes_version if self.options.cgmes_version is not None else CGMESVersions.v3_0_0
        self.ui.cgmesVersionComboBox.setCurrentIndex(self.ui.cgmesVersionComboBox.findData(version))
        self.ui.cgmesTopologyComboBox.setCurrentIndex(
            self.ui.cgmesTopologyComboBox.findData(self.options.cgmes_topology_mode)
        )
        self.ui.cgmesRecoveryComboBox.setCurrentIndex(
            self.ui.cgmesRecoveryComboBox.findData(self.options.cgmes_recovery_mode)
        )
        self.ui.cgmesMapAreasLikeRawCheckBox.setChecked(self.options.cgmes_map_areas_like_raw)
        self.ui.cgmesTryMapDcToHvdcCheckBox.setChecked(self.options.cgmes_try_to_map_dc_to_hvdc_line)
        self.ui.cgmesCreateBusbarPerCnCheckBox.setChecked(
            self.options.cgmes_create_busbar_section_for_every_connectivity_node
        )

    def do_it(self) -> None:
        """Store GUI values into :class:`FileOpenOptions` and close.

        :return: None.
        """
        self.options.cgmes_version = self.ui.cgmesVersionComboBox.currentData()
        self.options.cgmes_topology_mode = self.ui.cgmesTopologyComboBox.currentData()
        self.options.cgmes_recovery_mode = self.ui.cgmesRecoveryComboBox.currentData()
        self.options.cgmes_map_areas_like_raw = self.ui.cgmesMapAreasLikeRawCheckBox.isChecked()
        self.options.cgmes_try_to_map_dc_to_hvdc_line = self.ui.cgmesTryMapDcToHvdcCheckBox.isChecked()
        self.options.cgmes_create_busbar_section_for_every_connectivity_node = (
            self.ui.cgmesCreateBusbarPerCnCheckBox.isChecked()
        )
        self.close()
