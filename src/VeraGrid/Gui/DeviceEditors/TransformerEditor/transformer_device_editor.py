# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import sys

from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.DeviceEditors.TemplateDeviceEditor.template_device_editor import TemplateDeviceEditor
from VeraGrid.Gui.DeviceEditors.TransformerEditor.transformer_editor import TransformerEditor
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGrid.Gui.messages import warning_msg
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.multi_circuit import MultiCircuit


class EmbeddedTransformerDesignEditorWidget(TransformerEditor):
    """
    Embedded transformer editor widget used inside ``TransformerDeviceEditor``.
    """

    design_applied = QtCore.Signal(bool)

    def __init__(self,
                 branch: Transformer2W,
                 grid: MultiCircuit,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """
        Build the embedded transformer editor.

        :param branch: Transformer object to edit.
        :param grid: Circuit context used by the design editor.
        :param parent: Optional Qt parent widget.
        """
        TransformerEditor.__init__(self, branch=branch, grid=grid, modify_on_accept=True)
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


class TransformerDeviceEditor(TemplateDeviceEditor):
    """
    Specialized transformer editor that extends ``TemplateDeviceEditor``.
    """

    def __init__(self, api_object: Transformer2W, circuit: MultiCircuit | None = None) -> None:
        """
        Build the transformer editor.

        :param api_object: Transformer edited in place.
        :param circuit: Optional circuit context.
        """
        TemplateDeviceEditor.__init__(self, api_object=api_object, circuit=circuit)
        self.api_object: Transformer2W = api_object
        self.setWindowTitle(self.tr("Transformer editor"))

        self.transformer_design_widget: EmbeddedTransformerDesignEditorWidget | None = None
        self._build_transformer_design_tab()

    def _build_transformer_design_tab(self) -> None:
        """
        Build and configure the embedded transformer-design tab.
        """
        self.transformer_design_tab: QtWidgets.QWidget = QtWidgets.QWidget(self.tab_widget)
        self.transformer_design_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self.transformer_design_tab)
        self.transformer_design_button_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        self.transformer_design_apply_button: QtWidgets.QPushButton = QtWidgets.QPushButton(
            "Accept",
            self.transformer_design_tab,
        )
        self.transformer_design_apply_button.setIcon(QtGui.QIcon(":/Icons/icons/accept.png"))

        if self.circuit is not None:
            self.transformer_design_widget = EmbeddedTransformerDesignEditorWidget(
                branch=self.api_object,
                grid=self.circuit,
                parent=self.transformer_design_tab,
            )
            self.transformer_design_widget.design_applied.connect(self._on_transformer_design_applied)
            self.transformer_design_layout.addWidget(self.transformer_design_widget)
            self.transformer_design_apply_button.clicked.connect(self._apply_transformer_design)
        else:
            self.transformer_design_widget = None
            self.transformer_design_apply_button.setEnabled(False)
            missing_msg: QtWidgets.QLabel = QtWidgets.QLabel(
                "Transformer editor requires a circuit context.",
                self.transformer_design_tab,
            )
            self.transformer_design_layout.addWidget(missing_msg)

        self.transformer_design_button_layout.addStretch()
        self.transformer_design_button_layout.addWidget(self.transformer_design_apply_button)
        self.transformer_design_layout.addLayout(self.transformer_design_button_layout)

        transformer_tab_index: int = self.tab_widget.addTab(self.transformer_design_tab, "Transformer editor")
        self.tab_widget.setTabIcon(transformer_tab_index, QtGui.QIcon(":/Icons/icons/transformer3w.png"))

    def _apply_transformer_design(self) -> None:
        """
        Apply current values from the transformer tab and refresh base tables.
        """
        if self.transformer_design_widget is not None:
            self.transformer_design_widget.apply_changes()
        else:
            warning_msg(self.tr("Transformer design widget is not available"), self.tr("Transformer editor"))

    def _on_transformer_design_applied(self, applied_ok: bool) -> None:
        """
        Refresh base snapshot/profile tabs after one transformer-design apply.

        :param applied_ok: Apply status.
        """
        if applied_ok:
            self.properties_model.set_time_index(time_index=self._get_current_time_index())
            self.refresh_profile_table()
            self.show_info_toast("Transformer values applied")
        else:
            pass


TransformerDeviceEditorDialog = TransformerDeviceEditor


if __name__ == "__main__":
    qt_app: QtWidgets.QApplication = QtWidgets.QApplication(sys.argv)

    # Build one minimal circuit context so delegates and profile logic can be inspected.
    circuit_demo: MultiCircuit = MultiCircuit(name="Transformer device editor demo", Sbase=100.0, fbase=50.0)
    bus_from_demo: Bus = Bus(name="HV bus", Vnom=132.0)
    bus_to_demo: Bus = Bus(name="MV bus", Vnom=33.0)
    circuit_demo.add_bus(obj=bus_from_demo)
    circuit_demo.add_bus(obj=bus_to_demo)

    transformer_demo: Transformer2W = Transformer2W(
        bus_from=bus_from_demo,
        bus_to=bus_to_demo,
        name="Demo transformer",
        nominal_power=40.0,
        copper_losses=120.0,
        iron_losses=30.0,
        no_load_current=0.5,
        short_circuit_voltage=10.0,
    )
    circuit_demo.add_transformer2w(obj=transformer_demo)

    dialog_demo: TransformerDeviceEditor = TransformerDeviceEditor(
        api_object=transformer_demo,
        circuit=circuit_demo,
    )
    dialog_demo.show()
    sys.exit(qt_app.exec())
