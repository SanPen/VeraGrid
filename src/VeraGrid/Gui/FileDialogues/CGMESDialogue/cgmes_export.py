# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

import VeraGrid.Gui.gui_functions as gf
import VeraGrid.Session.file_handler as filedrv
from VeraGrid.Gui.FileDialogues.CGMESDialogue.cgmes_export_gui import Ui_CgmesExportDialog
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
from VeraGridEngine.IO.cim.cgmes.cgmes_export import get_available_cgmes_profiles
from VeraGridEngine.enumerations import CGMESVersions, CgmesExportMode, FileType

if TYPE_CHECKING:
    from VeraGrid.Gui.Main.SubClasses.io import IoMain


class CgmesExportDialogue(QtWidgets.QDialog):
    """
    Dialogue to export the active circuit to CGMES.
    """

    def __init__(self, app: IoMain) -> None:
        """
        Build the CGMES export dialogue.

        :param app: Main GUI controller used to access the active circuit and
            launch the save workflow.
        :return: None.
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
        self.current_boundary_set: str = ""

        self.cgmes_export_modes: list[CgmesExportMode] = [
            CgmesExportMode.SingleFile,
            CgmesExportMode.BatchZip,
        ]

        self.cgmes_version_dict: dict[str, CGMESVersions] = {
            x.value: x for x in [CGMESVersions.v2_4_15, CGMESVersions.v3_0_0]
        }
        self.cgmes_profiles_dict: dict[str, CgmesProfileType] = dict()

        self._populate_static_controls()
        self._configure_time_slot_widgets()
        self._connect_signals()
        self.cgmes_version_change()
        self.update_mode_dependent_widgets()

    def _populate_static_controls(self) -> None:
        """
        Fill the static combo-box controls.

        :return: None.
        """
        self.ui.cgmes_version_comboBox.setModel(gf.get_list_model(list(self.cgmes_version_dict.keys())))

        for export_mode in self.cgmes_export_modes:
            self.ui.cgmes_export_mode_comboBox.addItem(str(export_mode))

    def _configure_time_slot_widgets(self) -> None:
        """
        Configure the time-slot slider to match the main GUI semantics.

        :return: None.
        """
        # Reuse the same convention as the main GUI: ``-1`` means snapshot and
        # non-negative values map directly to time-series indices.
        if self.app.circuit.has_time_series:
            self.ui.time_slot_slider.setRange(-1, self.app.circuit.get_time_number() - 1)
            self.ui.time_slot_slider.setEnabled(True)
        else:
            self.ui.time_slot_slider.setRange(-1, -1)
            self.ui.time_slot_slider.setEnabled(False)

        self.ui.time_slot_slider.setValue(-1)
        self.update_time_slot_text()

    def _connect_signals(self) -> None:
        """
        Connect the dialogue signals.

        :return: None.
        """
        self.ui.selectCGMESBoundarySetButton.clicked.connect(self.select_cgmes_boundary_set)
        self.ui.exportButton.clicked.connect(self.export)
        self.ui.cgmes_version_comboBox.currentTextChanged.connect(self.cgmes_version_change)
        self.ui.time_slot_slider.valueChanged.connect(self.update_time_slot_text)
        self.ui.cgmes_export_mode_comboBox.currentIndexChanged.connect(self.update_mode_dependent_widgets)

    def get_selected_export_mode(self) -> CgmesExportMode:
        """
        Get the selected CGMES export strategy.

        :return: Selected CGMES export mode.
        """
        combo_index: int = self.ui.cgmes_export_mode_comboBox.currentIndex()
        return self.cgmes_export_modes[combo_index]

    def get_selected_t_idx(self) -> int | None:
        """
        Get the dialogue time selection as the export ``t_idx`` value.

        :return: ``None`` for snapshot export, otherwise the selected profile
            index.
        """
        slider_value: int = self.ui.time_slot_slider.value()

        if slider_value > -1:
            return slider_value
        else:
            return None

    def update_time_slot_text(self) -> None:
        """
        Refresh the human-readable time-slot label.

        :return: None.
        """
        selected_t_idx: int | None = self.get_selected_t_idx()

        # The label mirrors the main-window slider text so the user sees the
        # exact state that will be exported.
        if selected_t_idx is None:
            snapshot_text: str = self.app.circuit.get_snapshot_time_str()
            self.ui.time_slot_label.setText(f"Snapshot [{snapshot_text}]")
        else:
            time_text: str = str(self.app.circuit.time_profile[selected_t_idx])
            self.ui.time_slot_label.setText(f"[{selected_t_idx}] {time_text}")

    def update_mode_dependent_widgets(self) -> None:
        """
        Refresh the controls that depend on the selected export mode.

        :return: None.
        """
        export_mode: CgmesExportMode = self.get_selected_export_mode()
        has_time_series: bool = self.app.circuit.has_time_series

        # Batch export ignores the slider and always iterates all profile
        # points. The label therefore switches from a point description to an
        # operation summary.
        if export_mode == CgmesExportMode.BatchZip:
            self.ui.time_slot_slider.setEnabled(False)
            if has_time_series:
                total_steps: int = self.app.circuit.get_time_number()
                self.ui.time_slot_label.setText(f"Batch export will include {total_steps} profile points")
            else:
                self.ui.time_slot_label.setText("Batch export requires time-series data")
        else:
            if has_time_series:
                self.ui.time_slot_slider.setEnabled(True)
            else:
                self.ui.time_slot_slider.setEnabled(False)
            self.update_time_slot_text()

    def cgmes_version_change(self) -> None:
        """
        Refresh the available CGMES profiles for the selected CGMES version.

        :return: None.
        """
        cgmes_version: CGMESVersions = self.cgmes_version_dict[self.ui.cgmes_version_comboBox.currentText()]
        available_profiles: dict[str, list[str]] = get_available_cgmes_profiles(cgmes_version=cgmes_version)

        self.cgmes_profiles_dict = {
            key: CgmesProfileType(key)
            for key, value in available_profiles.items()
        }

        profile_names: list[str] = list(self.cgmes_profiles_dict.keys())
        profile_checks: list[bool] = self.get_default_profile_check_state(profile_names=profile_names)
        self.ui.cgmes_profiles_listView.setModel(gf.get_chck_list_model(profile_names, profile_checks))

    @staticmethod
    def get_default_checked_profile_names() -> set[str]:
        """
        Get the CGMES profiles that shall remain checked by default.

        The dialogue previously defaulted to the classic/core export set plus
        ``CO``. The newer NCP profiles are now visible, but they stay unchecked
        by default because the exporter does not yet synthesize those datasets
        from a plain VeraGrid model.

        :return: Set of profile names checked by default.
        """
        return {
            "EQ",
            "EQ_BD",
            "OP",
            "SC",
            "SSH",
            "TP",
            "TP_BD",
            "SV",
            "GL",
            "CO",
        }

    def get_default_profile_check_state(self, profile_names: list[str]) -> list[bool]:
        """
        Build the default checked state for the current profile list.

        :param profile_names: Profile names displayed in the dialogue.
        :return: Boolean check-state list aligned with ``profile_names``.
        """
        default_checked_names: set[str] = self.get_default_checked_profile_names()
        check_state: list[bool] = list()

        profile_name: str
        for profile_name in profile_names:
            check_state.append(profile_name in default_checked_names)

        return check_state

    def select_cgmes_boundary_set(self) -> None:
        """
        Select the current boundary-set file.

        :return: None.
        """
        files_types: str = "Boundary set (*.zip)"

        dialogue = QtWidgets.QFileDialog(None,
                                         caption='Select Boundary set file',
                                         directory=self.project_directory,
                                         filter=files_types)
        if dialogue.exec():
            filenames: list[str] = dialogue.selectedFiles()
            if len(filenames) > 0:
                self.current_boundary_set = filenames[0]
                self.ui.cgmes_boundary_set_label.setText(self.current_boundary_set)
            else:
                pass
        else:
            pass

    @staticmethod
    def normalize_export_file_name(file_name: str) -> str:
        """
        Normalize the selected output path so the expected extension is present.

        :param file_name: User-selected path.
        :return: Normalized output path.
        """
        root_name: str
        file_extension: str
        root_name, file_extension = os.path.splitext(file_name)

        if file_extension.lower() == ".zip":
            return file_name
        else:
            return root_name + ".zip"

    def export(self) -> None:
        """
        Collect the dialogue settings and launch the CGMES export.

        :return: None.
        """
        export_mode: CgmesExportMode = self.get_selected_export_mode()
        cgmes_version: CGMESVersions = self.cgmes_version_dict[self.ui.cgmes_version_comboBox.currentText()]
        cgmes_profiles_txt: list[str] = gf.get_checked_values(mdl=self.ui.cgmes_profiles_listView.model())
        cgmes_profiles: list[CgmesProfileType] = [self.cgmes_profiles_dict[e] for e in cgmes_profiles_txt]
        cgmes_one_file_per_profile: bool = self.ui.cgmes_single_profile_per_file_checkBox.isChecked()
        cgmes_map_areas_like_raw: bool = self.ui.cgmes_map_regions_like_raw_checkBox.isChecked()

        if export_mode == CgmesExportMode.BatchZip and not self.app.circuit.has_time_series:
            self.app.show_warning_toast("Batch export requires time-series data")
            return
        else:
            pass

        selected_t_idx: int | None = self.get_selected_t_idx()
        if export_mode == CgmesExportMode.BatchZip:
            selected_t_idx = None
        else:
            pass

        options = filedrv.FileSavingOptions(cgmes_boundary_set=self.current_boundary_set,
                                            sessions_data=self.sessions_data.get_save_data(),
                                            dictionary_of_json_files=dict(),
                                            cgmes_version=cgmes_version,
                                            cgmes_profiles=cgmes_profiles,
                                            cgmes_one_file_per_profile=cgmes_one_file_per_profile,
                                            cgmes_map_areas_like_raw=cgmes_map_areas_like_raw,
                                            cgmes_export_mode=export_mode,
                                            t_idx=selected_t_idx,
                                            file_type=FileType.CGMES)

        # Keep the default save path aligned with the active grid name so the
        # user gets deterministic archive or file names without extra typing.
        default_name: str = os.path.join(self.project_directory, self.app.ui.grid_name_line_edit.text())

        files_types: str = "CGMES (*.zip);;"
        filename, type_selected = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                        'Export to CGMES',
                                                                        default_name,
                                                                        files_types)

        if filename == '':
            return
        else:
            normalized_file_name: str = self.normalize_export_file_name(filename)

            self.app.save_file_now(filename=normalized_file_name,
                                   type_selected=type_selected,
                                   options=options)

            if export_mode == CgmesExportMode.BatchZip:
                self.app.show_info_toast("CGMES batch export started")
            else:
                self.app.show_info_toast("CGMES export started")

            self.close()
