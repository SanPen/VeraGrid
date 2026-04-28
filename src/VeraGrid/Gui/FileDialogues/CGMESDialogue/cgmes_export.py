# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import TYPE_CHECKING
import os
from PySide6 import QtWidgets
from VeraGrid.Gui.FileDialogues.CGMESDialogue.cgmes_export_gui import Ui_CgmesExportDialog
import VeraGrid.Session.file_handler as filedrv
import VeraGrid.Gui.gui_functions as gf
from VeraGridEngine.enumerations import CGMESVersions, FileType
from VeraGridEngine.IO.cim.cgmes.cgmes_export import get_available_cgmes_profiles
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType

if TYPE_CHECKING:
    from VeraGrid.Gui.Main.SubClasses.io import IoMain


class CgmesExportDialogue(QtWidgets.QDialog):
    """
    GridMergeDialogue
    """

    def __init__(self, app: IoMain):
        """
        GridMergeDialogue
        :param app: VeraGridMainGUI
        """
        QtWidgets.QDialog.__init__(self)
        self.ui = Ui_CgmesExportDialog()
        self.ui.setupUi(self)
        self.setWindowTitle('CGMES export')
        self.setModal(True)

        self.grid = app.circuit

        self.sessions_data = app.session

        self.project_directory = app.project_directory

        self.app: IoMain = app

        self.current_boundary_set = ""

        self.cgmes_version_dict = {x.value: x for x in [CGMESVersions.v2_4_15,
                                                        CGMESVersions.v3_0_0]}
        self.ui.cgmes_version_comboBox.setModel(gf.get_list_model(list(self.cgmes_version_dict.keys())))

        self.cgmes_profiles_dict = {key: CgmesProfileType(key) for key, val in
                                    get_available_cgmes_profiles(cgmes_version=CGMESVersions.v2_4_15).items()}

        self.ui.cgmes_profiles_listView.setModel(gf.get_list_model(list(self.cgmes_profiles_dict.keys()),
                                                                   checks=True, check_value=True))

        # Buttons
        self.ui.selectCGMESBoundarySetButton.clicked.connect(self.select_cgmes_boundary_set)
        self.ui.exportButton.clicked.connect(self.export)

        # change
        self.ui.cgmes_version_comboBox.currentTextChanged.connect(self.cgmes_version_change)

    def cgmes_version_change(self):
        """
        On GUI cgmes version change, display only the supported profiles
        """
        cgmes_version = self.cgmes_version_dict[self.ui.cgmes_version_comboBox.currentText()]

        self.cgmes_profiles_dict = {key: CgmesProfileType(key) for key, val in
                                    get_available_cgmes_profiles(cgmes_version=cgmes_version).items()}

        self.ui.cgmes_profiles_listView.setModel(gf.get_list_model(list(self.cgmes_profiles_dict.keys()),
                                                                   checks=True, check_value=True))

    def select_cgmes_boundary_set(self):
        """
        Select the current boundary set
        """
        files_types = "Boundary set (*.zip)"

        dialogue = QtWidgets.QFileDialog(None,
                                         caption='Select Boundary set file',
                                         directory=self.project_directory,
                                         filter=files_types)
        if dialogue.exec():
            filenames = dialogue.selectedFiles()
            if len(filenames) > 0:
                self.current_boundary_set = filenames[0]
                self.ui.cgmes_boundary_set_label.setText(self.current_boundary_set)

    def export(self) -> None:
        """
        The elements of the grid will be added with new idtags.
        This is useful in the case you want to compose a new grid from grids that are the same.
        :return:
        """
        cgmes_version = self.cgmes_version_dict[self.ui.cgmes_version_comboBox.currentText()]
        cgmes_profiles_txt = gf.get_checked_values(mdl=self.ui.cgmes_profiles_listView.model())
        cgmes_profiles = [self.cgmes_profiles_dict[e] for e in cgmes_profiles_txt]
        cgmes_one_file_per_profile = self.ui.cgmes_single_profile_per_file_checkBox.isChecked()
        cgmes_map_areas_like_raw = self.ui.cgmes_map_regions_like_raw_checkBox.isChecked()

        options = filedrv.FileSavingOptions(cgmes_boundary_set=self.current_boundary_set,
                                            sessions_data=self.sessions_data.get_save_data(),
                                            dictionary_of_json_files=dict(),
                                            cgmes_version=cgmes_version,
                                            cgmes_profiles=cgmes_profiles,
                                            cgmes_one_file_per_profile=cgmes_one_file_per_profile,
                                            cgmes_map_areas_like_raw=cgmes_map_areas_like_raw,
                                            file_type=FileType.CGMES)

        # if the global file_name is empty, ask where to save
        fname = os.path.join(self.project_directory, self.app.ui.grid_name_line_edit.text())

        files_types = "CGMES (*.zip);;"
        filename, type_selected = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                        'Export to CGMES',
                                                                        fname,
                                                                        files_types)

        if filename != '':

            # if the user did not enter the extension, add it automatically
            name, file_extension = os.path.splitext(filename)

            if file_extension == '':
                filename = name + '.zip'

            # we were able to compose the file correctly, now save it
            self.app.save_file_now(filename=filename,
                                   type_selected=type_selected,
                                   options=options)

            self.app.show_info_toast("CGMES export done!")
            self.close()

