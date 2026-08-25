# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import sys

from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.DeviceEditors.LineEditor.line_editor import LineEditor
from VeraGrid.Gui.DeviceEditors.TemplateDeviceEditor.template_device_editor import TemplateDeviceEditor
from VeraGrid.Gui.messages import warning_msg
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit


class EmbeddedLineDesignEditorWidget(LineEditor):
    """
    Embedded line-design editor widget used inside ``LineDeviceEditor``.
    """

    design_applied = QtCore.Signal(bool)

    def __init__(self, line: Line, grid: MultiCircuit, parent: QtWidgets.QWidget | None = None) -> None:
        """
        Build the embedded line design editor.

        :param line: Line object to edit.
        :param grid: Circuit context used by the design editor.
        :param parent: Optional Qt parent widget.
        """
        LineEditor.__init__(self, line=line, grid=grid)
        if parent is not None:
            self.setParent(parent)
        else:
            pass

        # The legacy editor is a dialog. As embedded widget we disable dialog-like chrome.
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
        Apply current line-design fields to the API object.

        :return: ``True`` when values were successfully applied.
        """
        self._apply_success = False
        self.accept_click()
        return self._apply_success


class LineDeviceEditor(TemplateDeviceEditor):
    """
    Specialized line editor that extends ``TemplateDeviceEditor``.
    """

    def __init__(self, api_object: Line, circuit: MultiCircuit | None = None) -> None:
        """
        Build the line editor.

        :param api_object: Line edited in place.
        :param circuit: Optional circuit context.
        """
        TemplateDeviceEditor.__init__(self, api_object=api_object, circuit=circuit)
        self.api_object: Line = api_object
        self.setWindowTitle(self.tr("Line editor"))

        self.line_design_widget: EmbeddedLineDesignEditorWidget | None = None
        self._build_line_design_tab()

    def _build_line_design_tab(self) -> None:
        """
        Build and configure the embedded line-design tab.
        """
        self.line_design_tab: QtWidgets.QWidget = QtWidgets.QWidget(self.tab_widget)
        self.line_design_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self.line_design_tab)
        self.line_design_button_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        self.line_design_apply_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Accept", self.line_design_tab)
        self.line_design_apply_button.setIcon(QtGui.QIcon(":/Icons/icons/accept.png"))

        if self.circuit is not None:
            self.line_design_widget = EmbeddedLineDesignEditorWidget(
                line=self.api_object,
                grid=self.circuit,
                parent=self.line_design_tab,
            )
            self.line_design_widget.design_applied.connect(self._on_line_design_applied)
            self.line_design_layout.addWidget(self.line_design_widget)
            self.line_design_apply_button.clicked.connect(self._apply_line_design)
        else:
            self.line_design_widget = None
            self.line_design_apply_button.setEnabled(False)
            missing_msg: QtWidgets.QLabel = QtWidgets.QLabel(
                "Line design editor requires a circuit context.",
                self.line_design_tab,
            )
            self.line_design_layout.addWidget(missing_msg)

        self.line_design_button_layout.addStretch()
        self.line_design_button_layout.addWidget(self.line_design_apply_button)
        self.line_design_layout.addLayout(self.line_design_button_layout)

        line_tab_index: int = self.tab_widget.addTab(self.line_design_tab, "Line editor")
        self.tab_widget.setTabIcon(line_tab_index, QtGui.QIcon(":/Icons/icons/ac_line.png"))

    def _apply_line_design(self) -> None:
        """
        Apply current values from the line-design tab and refresh base tables.
        """
        if self.line_design_widget is not None:
            self.line_design_widget.apply_changes()
        else:
            warning_msg(self.tr("Line design widget is not available"), self.tr("Line editor"))

    def _on_line_design_applied(self, applied_ok: bool) -> None:
        """
        Refresh base snapshot/profile tabs after one line-design apply.

        :param applied_ok: Apply status.
        """
        if applied_ok:
            self.properties_model.set_time_index(time_index=self._get_current_time_index())
            self.refresh_profile_table()
            self.show_info_toast("Line values applied")
        else:
            pass


LineDeviceEditorDialog = LineDeviceEditor


if __name__ == "__main__":
    qt_app: QtWidgets.QApplication = QtWidgets.QApplication(sys.argv)

    # Build one minimal circuit context so delegates and profile logic can be inspected.
    circuit_demo: MultiCircuit = MultiCircuit(name="Line device editor demo", Sbase=100.0, fbase=50.0)
    bus_from_demo: Bus = Bus(name="Bus from", Vnom=110.0)
    bus_to_demo: Bus = Bus(name="Bus to", Vnom=110.0)
    circuit_demo.add_bus(obj=bus_from_demo)
    circuit_demo.add_bus(obj=bus_to_demo)

    line_demo: Line = Line(
        bus_from=bus_from_demo,
        bus_to=bus_to_demo,
        name="Demo line",
        length=10.0,
        r=0.01,
        x=0.08,
        b=0.001,
        rate=120.0,
        circuit_idx=1,
    )
    circuit_demo.add_line(obj=line_demo)

    dialog_demo: LineDeviceEditor = LineDeviceEditor(api_object=line_demo, circuit=circuit_demo)
    dialog_demo.show()
    sys.exit(qt_app.exec())
