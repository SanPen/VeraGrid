# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import sys
from PySide6 import QtWidgets

from VeraGrid.Gui.DeviceEditors.Transformer3wEditor.transformer3w_editor_gui import Ui_Transformer3wEditorDialog
from VeraGridEngine.Devices.Branches.transformer3w import Transformer3W
from VeraGridEngine.Devices.Substation.bus import Bus


class Transformer3WEditor(QtWidgets.QDialog):
    """
    Three-winding transformer editor backed by a Qt Designer `.ui` file.
    """

    def __init__(self, tr3: Transformer3W, Sbase: float = 100.0, modify_on_accept: bool = True) -> None:
        """
        Build the transformer 3-winding editor.

        :param tr3: Transformer 3-winding object to edit.
        :param Sbase: System base power.
        :param modify_on_accept: Whether to apply changes on accept.
        """
        super().__init__()
        self.ui = Ui_Transformer3wEditorDialog()
        self.ui.setupUi(self)
        self.setWindowTitle("Transformer editor")

        self._api_object: Transformer3W = tr3
        self.sbase: float = Sbase
        self.modify_on_accept: bool = modify_on_accept

        self._configure_initial_values()
        self._connect_signals()

    @property
    def api_object(self) -> Transformer3W:
        """
        Access the edited API object.

        :return: Edited transformer instance.
        """
        return self._api_object

    def _connect_signals(self) -> None:
        """
        Bind GUI events to controller slots.
        """
        self.ui.acceptButton.clicked.connect(self.accept_click)

    def _format_bus_voltage(self, bus_to: Bus | None) -> str:
        """
        Build a user label for winding connected bus nominal voltage.

        :param bus_to: Connected bus or None.
        :return: Display-ready text.
        """
        if bus_to is not None:
            return f"{bus_to.Vnom} kV"
        else:
            return "Not connected"

    def _configure_initial_values(self) -> None:
        """
        Load all editor widgets from current transformer data.
        """
        tr3: Transformer3W = self._api_object
        self.ui.nameLabel.setText(f"Name: {tr3.name}")

        self.ui.w1BusVoltageLabel.setText(f"Bus voltage: {self._format_bus_voltage(bus_to=tr3.bus1)}")
        self.ui.w2BusVoltageLabel.setText(f"Bus voltage: {self._format_bus_voltage(bus_to=tr3.bus2)}")
        self.ui.w3BusVoltageLabel.setText(f"Bus voltage: {self._format_bus_voltage(bus_to=tr3.bus3)}")

        self.ui.w1VnSpinBox.setValue(tr3.V1)
        self.ui.w2VnSpinBox.setValue(tr3.V2)
        self.ui.w3VnSpinBox.setValue(tr3.V3)

        self.ui.w1SnSpinBox.setValue(tr3.rate1)
        self.ui.w2SnSpinBox.setValue(tr3.rate2)
        self.ui.w3SnSpinBox.setValue(tr3.rate3)

        self.ui.w1PcuSpinBox.setValue(tr3.Pcu12)
        self.ui.w2PcuSpinBox.setValue(tr3.Pcu23)
        self.ui.w3PcuSpinBox.setValue(tr3.Pcu31)

        self.ui.w1VscSpinBox.setValue(tr3.Vsc12)
        self.ui.w2VscSpinBox.setValue(tr3.Vsc23)
        self.ui.w3VscSpinBox.setValue(tr3.Vsc31)

        self.ui.pfeSpinBox.setValue(0.0)
        self.ui.i0SpinBox.setValue(0.0)

    def accept_click(self) -> None:
        """
        Apply design values to the model and close the dialog.
        """
        if self.modify_on_accept:
            self._api_object.fill_from_design_values(
                V1=self.ui.w1VnSpinBox.value(),
                V2=self.ui.w2VnSpinBox.value(),
                V3=self.ui.w3VnSpinBox.value(),
                Sn1=self.ui.w1SnSpinBox.value(),
                Sn2=self.ui.w2SnSpinBox.value(),
                Sn3=self.ui.w3SnSpinBox.value(),
                Pcu12=self.ui.w1PcuSpinBox.value(),
                Pcu23=self.ui.w2PcuSpinBox.value(),
                Pcu31=self.ui.w3PcuSpinBox.value(),
                Vsc12=self.ui.w1VscSpinBox.value(),
                Vsc23=self.ui.w2VscSpinBox.value(),
                Vsc31=self.ui.w3VscSpinBox.value(),
                Pfe=self.ui.pfeSpinBox.value(),
                I0=self.ui.i0SpinBox.value(),
                Sbase=self.sbase,
            )
        else:
            pass
        self.accept()


if __name__ == "__main__":
    qt_app = QtWidgets.QApplication(sys.argv)
    bus_1_demo = Bus(name="HV bus", Vnom=132.0)
    bus_2_demo = Bus(name="MV bus", Vnom=33.0)
    bus_3_demo = Bus(name="LV bus", Vnom=11.0)
    transformer_demo = Transformer3W(
        name="Demo transformer 3W",
        bus1=bus_1_demo,
        bus2=bus_2_demo,
        bus3=bus_3_demo,
        V1=132.0,
        V2=33.0,
        V3=11.0,
        rate12=40.0,
        rate23=20.0,
        rate31=15.0,
    )
    dialog_demo = Transformer3WEditor(tr3=transformer_demo, Sbase=100.0, modify_on_accept=True)
    dialog_demo.show()
    sys.exit(qt_app.exec())
