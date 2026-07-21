# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import List
import numpy as np
from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import (QDialog,
                               QAbstractItemView,
                               QDialogButtonBox,
                               QMessageBox)
from VeraGridEngine.Templates.template_definition import TemplateProp
from VeraGrid.Gui.DynamicModelEditor.dialog_inputs_model import DialogInpModel


class DynTemplatesEditorDialog(QDialog):
    """
    Dynamic templates editor dialogue
    """

    def __init__(self, name: str, property_list: List[TemplateProp]):
        QtWidgets.QDialog.__init__(self)
        self.setObjectName("self")
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.NoContextMenu)
        self.setWindowTitle("Edit " + name + " Template")
        self.setMinimumSize(600, 400)
        self.property_list = property_list

        layout = QtWidgets.QVBoxLayout(self)

        self.objects_table = QtWidgets.QTableView()
        self.objects_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.objects_table.horizontalHeader().setStretchLastSection(True)
        self.objects_table.verticalHeader().setDefaultSectionSize(24)

        model = DialogInpModel(property_list=property_list,
                               parent=self.objects_table,
                               editable=True,
                               transposed=True)

        self.objects_table.setModel(model)

        layout.addWidget(self.objects_table)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                      | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_values(self) -> List[TemplateProp]:
        return self.property_list

    def accept(self) -> None:
        super().accept()
