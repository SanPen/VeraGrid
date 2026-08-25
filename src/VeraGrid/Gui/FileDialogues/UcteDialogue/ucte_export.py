# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

import VeraGrid.Session.file_handler as filedrv
from VeraGrid.Gui.FileDialogues.UcteDialogue.ucte_export_gui import Ui_UcteExportDialog
from VeraGridEngine.enumerations import FileType, UcteExportMode

if TYPE_CHECKING:
    from VeraGrid.Gui.Main.SubClasses.io import IoMain


class UcteExportDialogue(QtWidgets.QDialog):
    """
    Dialogue to export the active circuit to UCTE.
    """

    def __init__(self, app: IoMain) -> None:
        """
        Build the UCTE export dialogue.

        :param app: Main GUI controller used to access the active circuit and
            launch the save workflow.
        :return: None.
        """
        QtWidgets.QDialog.__init__(self)
        self.ui = Ui_UcteExportDialog()
        self.ui.setupUi(self)
        self.setWindowTitle(self.tr("UCTE export"))
        self.setModal(True)

        self.app: IoMain = app

        self.ucte_export_modes: list[UcteExportMode] = [
            UcteExportMode.SingleFile,
            UcteExportMode.BatchZip,
        ]

        self._populate_static_controls()
        self._configure_time_slot_widgets()
        self._connect_signals()
        self.update_mode_dependent_widgets()

    def _populate_static_controls(self) -> None:
        """
        Fill the static combo-box controls.

        :return: None.
        """
        export_mode: UcteExportMode
        for export_mode in self.ucte_export_modes:
            self.ui.ucte_export_mode_comboBox.addItem(self.tr(str(export_mode)), export_mode)

    def _configure_time_slot_widgets(self) -> None:
        """
        Configure the time-slot slider to match the main GUI semantics.

        :return: None.
        """
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
        self.ui.exportButton.clicked.connect(self.export)
        self.ui.time_slot_slider.valueChanged.connect(self.update_time_slot_text)
        self.ui.ucte_export_mode_comboBox.currentIndexChanged.connect(self.update_mode_dependent_widgets)

    def get_selected_export_mode(self) -> UcteExportMode:
        """
        Get the selected UCTE export strategy.

        :return: Selected UCTE export mode.
        """
        return self.ui.ucte_export_mode_comboBox.currentData()

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
        export_mode: UcteExportMode = self.get_selected_export_mode()
        has_time_series: bool = self.app.circuit.has_time_series

        if export_mode == UcteExportMode.BatchZip:
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

    def get_dialogue_file_filter(self, export_mode: UcteExportMode) -> str:
        """
        Get the save-dialogue filter string for the selected export mode.

        :param export_mode: Selected export mode.
        :return: Qt file-filter string.
        """
        if export_mode == UcteExportMode.BatchZip:
            return "Zip package (*.zip)"
        else:
            return "UCTE (*.uct *.ucte)"

    def normalize_export_file_name(self,
                                   file_name: str,
                                   export_mode: UcteExportMode) -> str:
        """
        Normalize the selected output path so the expected extension is present.

        :param file_name: User-selected path.
        :param export_mode: Selected export mode.
        :return: Normalized output path.
        """
        root_name: str
        file_extension: str
        root_name, file_extension = os.path.splitext(file_name)
        normalized_extension: str = file_extension.lower()

        if export_mode == UcteExportMode.BatchZip:
            if normalized_extension == ".zip":
                return file_name
            else:
                return root_name + ".zip"
        else:
            if normalized_extension in [".uct", ".ucte"]:
                return file_name
            else:
                return root_name + ".uct"

    def export(self) -> None:
        """
        Collect the dialogue settings and launch the UCTE export.

        :return: None.
        """
        export_mode: UcteExportMode = self.get_selected_export_mode()

        if export_mode == UcteExportMode.BatchZip and not self.app.circuit.has_time_series:
            self.app.show_warning_toast("Batch export requires time-series data")
            return
        else:
            pass

        selected_t_idx: int | None = self.get_selected_t_idx()
        if export_mode == UcteExportMode.BatchZip:
            selected_t_idx = None
        else:
            pass

        default_name: str = os.path.join(self.app.project_directory, self.app.ui.grid_name_line_edit.text())
        file_filter: str = self.get_dialogue_file_filter(export_mode=export_mode)
        selected_file_name, type_selected = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                                   self.tr("Export to UCTE"),
                                                                                   default_name,
                                                                                   file_filter)

        if selected_file_name == "":
            return
        else:
            normalized_file_name: str = self.normalize_export_file_name(file_name=selected_file_name,
                                                                        export_mode=export_mode)

            self.app.save_file_now(
                filename=normalized_file_name,
                type_selected=type_selected,
                options=filedrv.FileSavingOptions(
                    file_type=FileType.UCTE,
                    ucte_export_mode=export_mode,
                    t_idx=selected_t_idx,
                )
            )

            if export_mode == UcteExportMode.BatchZip:
                self.app.show_info_toast("UCTE batch export started")
            else:
                self.app.show_info_toast("UCTE export started")

            self.close()
