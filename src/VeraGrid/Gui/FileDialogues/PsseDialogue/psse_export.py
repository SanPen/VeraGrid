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
from VeraGrid.Gui.FileDialogues.PsseDialogue.psse_export_gui import Ui_PsseExportDialog
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import FileType, PsseTopologyExportMode, PsseExportMode

if TYPE_CHECKING:
    from VeraGrid.Gui.Main.SubClasses.io import IoMain


class PsseExportDialogue(QtWidgets.QDialog):
    """
    Dialogue to export the active circuit to PSSE RAW or RAWX.
    """

    def __init__(self, app: IoMain) -> None:
        """
        Build the PSS/E export dialogue.

        :param app: Main GUI controller used to access the active circuit and
            launch the save workflow.
        :return: None.
        """
        QtWidgets.QDialog.__init__(self)
        self.ui = Ui_PsseExportDialog()
        self.ui.setupUi(self)
        self.setWindowTitle(self.tr('PSS/e export'))
        self.setModal(True)

        self.app: IoMain = app

        self.logger: Logger = Logger()

        self.psse_export_modes: list[PsseExportMode] = [
            PsseExportMode.SingleFile,
            PsseExportMode.BatchZip,
        ]
        self.psse_file_types: list[FileType] = [
            FileType.PSSE_raw,
            FileType.PSSE_rawx,
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
        for export_mode in self.psse_export_modes:
            self.ui.psse_export_mode_comboBox.addItem(self.tr(str(export_mode)), export_mode)

        self.ui.psse_file_format_comboBox.setModel(
            gf.ComboModel(enum_values=self.psse_file_types, translate=self.tr)
        )

        self.ui.raw_export_version_comboBox.setModel(
            gf.ComboModel(text_items=[(version, version) for version in ["33", "34", "35", "36"]])
        )
        self.ui.node_breaker_checkbox.setChecked(False)

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
        self.ui.exportButton.clicked.connect(self.export)
        self.ui.time_slot_slider.valueChanged.connect(self.update_time_slot_text)
        self.ui.psse_export_mode_comboBox.currentIndexChanged.connect(self.update_mode_dependent_widgets)

    def get_selected_export_mode(self) -> PsseExportMode:
        """
        Get the selected PSSE export strategy.

        :return: Selected PSSE export mode.
        """
        return self.ui.psse_export_mode_comboBox.currentData()

    def get_selected_file_type(self) -> FileType:
        """
        Get the selected internal PSSE file format.

        :return: Selected PSSE file type.
        """
        return self.ui.psse_file_format_comboBox.currentData()

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
        export_mode: PsseExportMode = self.get_selected_export_mode()
        has_time_series: bool = self.app.circuit.has_time_series

        # Batch export ignores the slider and always iterates all profile
        # points. The label therefore switches from a point description to an
        # operation summary.
        if export_mode == PsseExportMode.BatchZip:
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

    def get_dialogue_file_filter(self,
                                 export_mode: PsseExportMode,
                                 file_tpe: FileType) -> str:
        """
        Get the save-dialogue filter string for the selected export mode.

        :param export_mode: Selected export mode.
        :param file_tpe: Selected PSSE file type.
        :return: Qt file-filter string.
        """
        if export_mode == PsseExportMode.BatchZip:
            return "Zip package (*.zip)"
        elif file_tpe == FileType.PSSE_rawx:
            return "PSS/e rawx (*.rawx)"
        else:
            return "PSS/e raw (*.raw)"

    def normalize_export_file_name(self,
                                   file_name: str,
                                   export_mode: PsseExportMode,
                                   file_tpe: FileType) -> str:
        """
        Normalize the selected output path so the expected extension is present.

        :param file_name: User-selected path.
        :param export_mode: Selected export mode.
        :param file_tpe: Selected PSSE file type.
        :return: Normalized output path.
        """
        root_name: str
        file_extension: str
        root_name, file_extension = os.path.splitext(file_name)
        normalized_extension: str = file_extension.lower()

        if export_mode == PsseExportMode.BatchZip:
            if normalized_extension == ".zip":
                return file_name
            else:
                return root_name + ".zip"
        elif file_tpe == FileType.PSSE_rawx:
            if normalized_extension == ".rawx":
                return file_name
            else:
                return root_name + ".rawx"
        else:
            if normalized_extension == ".raw":
                return file_name
            else:
                return root_name + ".raw"

    def export(self) -> None:
        """
        Collect the dialogue settings and launch the PSS/E export.

        :return: None.
        """
        raw_version: str = self.ui.raw_export_version_comboBox.currentData()
        export_mode: PsseExportMode = self.get_selected_export_mode()
        file_tpe: FileType = self.get_selected_file_type()

        if self.ui.node_breaker_checkbox.isChecked():
            topology_mode: PsseTopologyExportMode = PsseTopologyExportMode.NodeBreaker
        else:
            topology_mode = PsseTopologyExportMode.BusBranch

        if export_mode == PsseExportMode.BatchZip and not self.app.circuit.has_time_series:
            self.app.show_warning_toast("Batch export requires time-series data")
            return
        else:
            pass

        selected_t_idx: int | None = self.get_selected_t_idx()
        if export_mode == PsseExportMode.BatchZip:
            selected_t_idx = None
        else:
            pass

        # Keep the default save path aligned with the active grid name so the
        # user gets deterministic archive or file names without extra typing.
        default_name: str = os.path.join(self.app.project_directory, self.app.ui.grid_name_line_edit.text())
        file_filter: str = self.get_dialogue_file_filter(export_mode=export_mode, file_tpe=file_tpe)
        selected_file_name, type_selected = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                                   self.tr('Export to PSS/e'),
                                                                                   default_name,
                                                                                   file_filter)

        if selected_file_name == '':
            return
        else:
            normalized_file_name: str = self.normalize_export_file_name(file_name=selected_file_name,
                                                                        export_mode=export_mode,
                                                                        file_tpe=file_tpe)

            self.app.save_file_now(
                filename=normalized_file_name,
                type_selected=type_selected,
                options=filedrv.FileSavingOptions(
                    raw_version=raw_version,
                    file_type=file_tpe,
                    psse_topology_mode=topology_mode,
                    psse_export_mode=export_mode,
                    t_idx=selected_t_idx
                )
            )

            if export_mode == PsseExportMode.BatchZip:
                self.app.show_info_toast("PSS/e batch export started")
            else:
                self.app.show_info_toast("PSS/e export started")

            self.close()
