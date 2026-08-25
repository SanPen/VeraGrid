# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import sys

from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.DeviceEditors.TemplateDeviceEditor.template_device_editor import TemplateDeviceEditor
from VeraGrid.Gui.DeviceEditors.Transformer3wEditor.transformer3w_editor import Transformer3WEditor
from VeraGrid.Gui.messages import warning_msg
from VeraGridEngine.Devices.Branches.transformer3w import Transformer3W
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit


class EmbeddedTransformer3WDesignEditorWidget(Transformer3WEditor):
    """
    Embedded 3-winding transformer editor widget used inside ``Transformer3WDeviceEditor``.
    """

    design_applied = QtCore.Signal(bool)

    def __init__(self,
                 transformer: Transformer3W,
                 sbase: float,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """
        Build the embedded transformer 3-winding editor.

        :param transformer: Transformer object to edit.
        :param sbase: System base power.
        :param parent: Optional Qt parent widget.
        """
        Transformer3WEditor.__init__(self, tr3=transformer, Sbase=sbase, modify_on_accept=True)
        if parent is not None:
            self.setParent(parent)
        else:
            pass

        # The legacy editor is dialog-based. Keep it as embeddable widget here.
        self.setWindowFlags(QtCore.Qt.WindowType.Widget)
        self.setWindowTitle("")
        self.ui.acceptButton.hide()
        self._apply_success: bool = False

    def accept(self) -> None:
        """
        Intercept dialog acceptance so the embedded widget does not close itself.
        """
        self._apply_success = True
        self.design_applied.emit(True)

    def apply_changes(self) -> bool:
        """
        Apply current transformer fields to the API object.

        :return: ``True`` when values were successfully applied.
        """
        self._apply_success = False
        self.accept_click()
        return self._apply_success


class Transformer3WDeviceEditor(TemplateDeviceEditor):
    """
    Specialized 3-winding transformer editor that extends ``TemplateDeviceEditor``.
    """

    def __init__(self, api_object: Transformer3W, circuit: MultiCircuit | None = None) -> None:
        """
        Build the transformer 3-winding editor.

        :param api_object: Transformer 3-winding object edited in place.
        :param circuit: Optional circuit context.
        """
        TemplateDeviceEditor.__init__(self, api_object=api_object, circuit=circuit)
        self.api_object: Transformer3W = api_object
        self.setWindowTitle(self.tr("Transformer 3W editor"))

        self.transformer3w_design_widget: EmbeddedTransformer3WDesignEditorWidget | None = None
        self._build_transformer3w_design_tab()

    def _build_transformer3w_design_tab(self) -> None:
        """
        Build and configure the embedded transformer 3W design tab.
        """
        self.transformer3w_design_tab: QtWidgets.QWidget = QtWidgets.QWidget(self.tab_widget)
        self.transformer3w_design_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self.transformer3w_design_tab)
        self.transformer3w_button_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        self.transformer3w_apply_button: QtWidgets.QPushButton = QtWidgets.QPushButton(
            "Accept",
            self.transformer3w_design_tab,
        )
        self.transformer3w_apply_button.setIcon(QtGui.QIcon(":/Icons/icons/accept.png"))

        if self.circuit is not None:
            self.transformer3w_design_widget = EmbeddedTransformer3WDesignEditorWidget(
                transformer=self.api_object,
                sbase=self.circuit.Sbase,
                parent=self.transformer3w_design_tab,
            )
            self.transformer3w_design_widget.design_applied.connect(self._on_transformer3w_design_applied)
            self.transformer3w_design_layout.addWidget(self.transformer3w_design_widget)
            self.transformer3w_apply_button.clicked.connect(self._apply_transformer3w_design)
        else:
            self.transformer3w_design_widget = None
            self.transformer3w_apply_button.setEnabled(False)
            missing_msg: QtWidgets.QLabel = QtWidgets.QLabel(
                "Transformer 3W editor requires a circuit context.",
                self.transformer3w_design_tab,
            )
            self.transformer3w_design_layout.addWidget(missing_msg)

        self.transformer3w_button_layout.addStretch()
        self.transformer3w_button_layout.addWidget(self.transformer3w_apply_button)
        self.transformer3w_design_layout.addLayout(self.transformer3w_button_layout)

        transformer3w_tab_index: int = self.tab_widget.addTab(self.transformer3w_design_tab, "Transformer3WEditor")
        self.tab_widget.setTabIcon(transformer3w_tab_index, QtGui.QIcon(":/Icons/icons/transformer3w.png"))

    def _apply_transformer3w_design(self) -> None:
        """
        Apply current values from the transformer 3W tab and refresh base tables.
        """
        if self.transformer3w_design_widget is not None:
            self.transformer3w_design_widget.apply_changes()
        else:
            warning_msg(self.tr("Transformer 3W design widget is not available"), self.tr("Transformer 3W editor"))

    def _on_transformer3w_design_applied(self, applied_ok: bool) -> None:
        """
        Refresh base snapshot/profile tabs after one transformer 3W design apply.

        :param applied_ok: Apply status.
        """
        if applied_ok:
            self.properties_model.set_time_index(time_index=self._get_current_time_index())
            self.refresh_profile_table()
            self.show_info_toast("Transformer 3W values applied")
        else:
            pass


Transformer3WDeviceEditorDialog = Transformer3WDeviceEditor


if __name__ == "__main__":
    qt_app: QtWidgets.QApplication = QtWidgets.QApplication(sys.argv)

    # Build one minimal circuit context so delegates and profile logic can be inspected.
    circuit_demo: MultiCircuit = MultiCircuit(name="Transformer 3W editor demo", Sbase=100.0, fbase=50.0)
    bus_1_demo: Bus = Bus(name="HV bus", Vnom=132.0)
    bus_2_demo: Bus = Bus(name="MV bus", Vnom=33.0)
    bus_3_demo: Bus = Bus(name="LV bus", Vnom=11.0)
    circuit_demo.add_bus(obj=bus_1_demo)
    circuit_demo.add_bus(obj=bus_2_demo)
    circuit_demo.add_bus(obj=bus_3_demo)

    transformer_demo: Transformer3W = Transformer3W(
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
    circuit_demo.add_transformer3w(obj=transformer_demo)

    dialog_demo: Transformer3WDeviceEditor = Transformer3WDeviceEditor(
        api_object=transformer_demo,
        circuit=circuit_demo,
    )
    dialog_demo.resize(1320, 860)
    dialog_demo.show()
    sys.exit(qt_app.exec())
