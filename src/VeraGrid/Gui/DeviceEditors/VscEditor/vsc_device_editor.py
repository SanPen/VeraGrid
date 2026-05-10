# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import sys

from PySide6 import QtWidgets

from VeraGrid.Gui.DeviceEditors.TemplateDeviceEditor.template_device_editor import TemplateDeviceEditor
from VeraGrid.Gui.DeviceEditors.VscEditor.vsc_editor_widget import Ui_VscDeviceEditorWidget
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_workspace_manager import open_dynamic_editor
from VeraGridEngine.Devices.Branches.vsc import VSC
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import DynamicSimulationMode


def get_bus_name(bus: Bus | None) -> str:
    """
    Return one safe bus-name string.

    :param bus: Bus object or ``None``.
    :return: Bus name when available, otherwise ``"None"``.
    """
    if bus is not None:
        return bus.name
    else:
        return "None"


class VscDeviceEditor(TemplateDeviceEditor):
    """
    Specialized VSC editor that extends ``TemplateDeviceEditor``.
    """

    def __init__(self, api_object: VSC, circuit: MultiCircuit | None = None) -> None:
        """
        Build the VSC editor.

        :param api_object: VSC device edited in place.
        :param circuit: Optional circuit context.
        """
        TemplateDeviceEditor.__init__(self, api_object=api_object, circuit=circuit)
        self.api_object: VSC = api_object
        self.setWindowTitle("VSC editor")

        self._build_vsc_tab()
        self._refresh_vsc_summary()

    def _build_vsc_tab(self) -> None:
        """
        Build and configure the VSC-specific summary tab.
        """
        self.vsc_tab: QtWidgets.QWidget = QtWidgets.QWidget(self.tab_widget)
        self.vsc_tab_ui: Ui_VscDeviceEditorWidget = Ui_VscDeviceEditorWidget()
        self.vsc_tab_ui.setupUi(self.vsc_tab)

        self.vsc_tab_ui.refresh_button.clicked.connect(self._refresh_vsc_summary)
        self.vsc_tab_ui.rms_button.clicked.connect(self._open_dynamic_rms_editor)
        self.vsc_tab_ui.emt_button.clicked.connect(self._open_dynamic_emt_editor)

        if self.circuit is not None:
            self.vsc_tab_ui.rms_button.setEnabled(True)
            self.vsc_tab_ui.emt_button.setEnabled(True)
        else:
            self.vsc_tab_ui.rms_button.setEnabled(False)
            self.vsc_tab_ui.emt_button.setEnabled(False)

        self.tab_widget.addTab(self.vsc_tab, "VSC")

    def _refresh_vsc_summary(self) -> None:
        """
        Refresh summary labels from current VSC values.
        """
        self.vsc_tab_ui.bus_ac_value_label.setText(get_bus_name(bus=self.api_object.bus_to))
        self.vsc_tab_ui.bus_dc_plus_value_label.setText(get_bus_name(bus=self.api_object.bus_from))
        self.vsc_tab_ui.bus_dc_minus_value_label.setText(get_bus_name(bus=self.api_object.bus_dc_n))
        self.vsc_tab_ui.control_1_value_label.setText(str(self.api_object.control1.value))
        self.vsc_tab_ui.control_2_value_label.setText(str(self.api_object.control2.value))
        self.vsc_tab_ui.fault_control_value_label.setText(str(self.api_object.fault_control.value))

    def _open_dynamic_rms_editor(self) -> None:
        """
        Open RMS dynamic editor for the current VSC.
        """
        if self.circuit is not None:
            open_dynamic_editor(api_object=self.api_object,
                                circuit=self.circuit,
                                preferred_mode=DynamicSimulationMode.RMS)
        else:
            pass

    def _open_dynamic_emt_editor(self) -> None:
        """
        Open EMT dynamic editor for the current VSC.
        """
        if self.circuit is not None:
            open_dynamic_editor(api_object=self.api_object,
                                circuit=self.circuit,
                                preferred_mode=DynamicSimulationMode.EMT)
        else:
            pass


VscDeviceEditorDialog = VscDeviceEditor


if __name__ == "__main__":
    qt_app: QtWidgets.QApplication = QtWidgets.QApplication(sys.argv)

    # Build one minimal circuit context so delegates and profile logic can be inspected.
    circuit_demo: MultiCircuit = MultiCircuit(name="VSC device editor demo", Sbase=100.0, fbase=50.0)
    bus_ac_demo: Bus = Bus(name="AC bus", Vnom=220.0, is_dc=False)
    bus_dc_plus_demo: Bus = Bus(name="DC+ bus", Vnom=320.0, is_dc=True)
    bus_dc_minus_demo: Bus = Bus(name="DC- bus", Vnom=320.0, is_dc=True)
    circuit_demo.add_bus(obj=bus_ac_demo)
    circuit_demo.add_bus(obj=bus_dc_plus_demo)
    circuit_demo.add_bus(obj=bus_dc_minus_demo)

    vsc_demo: VSC = VSC(
        bus_from=bus_dc_plus_demo,
        bus_to=bus_ac_demo,
        bus_dc_n=bus_dc_minus_demo,
        name="Demo VSC",
        rate=150.0,
    )

    dialog_demo: VscDeviceEditor = VscDeviceEditor(api_object=vsc_demo, circuit=circuit_demo)
    dialog_demo.show()
    sys.exit(qt_app.exec())
