# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import sys

from PySide6 import QtGui, QtWidgets

from VeraGrid.Gui.DeviceEditors.ControllableShuntEditor.controllable_shunt_editor import (
    ControllableShuntStepsEditorWidget,
)
from VeraGrid.Gui.DeviceEditors.TemplateDeviceEditor.template_device_editor import TemplateDeviceEditor
from VeraGridEngine.Devices.Injections.controllable_shunt import ControllableShunt
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit


class ControllableShuntDeviceEditor(TemplateDeviceEditor):
    """
    Specialized controllable-shunt editor that extends ``TemplateDeviceEditor``.
    """

    def __init__(self, api_object: ControllableShunt, circuit: MultiCircuit | None = None) -> None:
        """
        Build the controllable shunt editor.

        :param api_object: Controllable shunt edited in place.
        :param circuit: Optional circuit context.
        """
        TemplateDeviceEditor.__init__(self, api_object=api_object, circuit=circuit)
        self.api_object: ControllableShunt = api_object
        self.setWindowTitle("Controllable shunt editor")

        self.steps_editor_widget: ControllableShuntStepsEditorWidget | None = None
        self._build_steps_editor_tab()

    def _build_steps_editor_tab(self) -> None:
        """
        Build and configure the embedded steps-editor tab.
        """
        self.steps_tab: QtWidgets.QWidget = QtWidgets.QWidget(self.tab_widget)
        self.steps_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self.steps_tab)
        self.steps_button_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        self.steps_apply_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Accept", self.steps_tab)
        self.steps_apply_button.setIcon(QtGui.QIcon(":/Icons/icons/accept.png"))

        self.steps_editor_widget = ControllableShuntStepsEditorWidget(
            api_object=self.api_object,
            parent=self.steps_tab,
        )
        self.steps_editor_widget.ui.doneButton.hide()
        self.steps_editor_widget.steps_applied.connect(self._on_steps_applied)
        self.steps_layout.addWidget(self.steps_editor_widget)
        self.steps_apply_button.clicked.connect(self.steps_editor_widget.apply_changes)

        self.steps_button_layout.addStretch()
        self.steps_button_layout.addWidget(self.steps_apply_button)
        self.steps_layout.addLayout(self.steps_button_layout)

        steps_tab_index: int = self.tab_widget.addTab(self.steps_tab, "Steps editor")
        self.tab_widget.setTabIcon(steps_tab_index, QtGui.QIcon(":/Icons/icons/controllable_shunt.png"))

    def _on_steps_applied(self, applied_ok: bool) -> None:
        """
        Refresh base snapshot/profile tabs after one step-table apply.

        :param applied_ok: Apply status.
        """
        if applied_ok:
            self.properties_model.set_time_index(time_index=self._get_current_time_index())
            self.refresh_profile_table()
            self.show_info_toast("Shunt steps applied")
        else:
            pass


ControllableShuntDeviceEditorDialog = ControllableShuntDeviceEditor


if __name__ == "__main__":
    qt_app: QtWidgets.QApplication = QtWidgets.QApplication(sys.argv)

    # Build one minimal circuit context so delegates and profile logic can be inspected.
    circuit_demo: MultiCircuit = MultiCircuit(name="Controllable shunt editor demo", Sbase=100.0, fbase=50.0)
    bus_demo: Bus = Bus(name="Bus demo", Vnom=66.0)
    circuit_demo.add_bus(obj=bus_demo)

    shunt_demo: ControllableShunt = ControllableShunt(name="Demo controllable shunt")
    circuit_demo.add_controllable_shunt(bus=bus_demo, api_obj=shunt_demo)

    dialog_demo: ControllableShuntDeviceEditor = ControllableShuntDeviceEditor(
        api_object=shunt_demo,
        circuit=circuit_demo,
    )
    dialog_demo.show()
    sys.exit(qt_app.exec())
