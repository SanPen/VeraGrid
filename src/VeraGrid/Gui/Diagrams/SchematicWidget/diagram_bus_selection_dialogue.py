# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import List, TYPE_CHECKING
from PySide6 import QtWidgets
from PySide6.QtWidgets import (QVBoxLayout, QPushButton)

from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import (SchematicWidget, make_diagram_from_buses,
                                                                    SchematicDiagram)
from VeraGridEngine.Devices.Substation.substation import Substation, DeviceType
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit

if TYPE_CHECKING:
    from VeraGrid.Gui.Main.VeraGridMain import VeraGridMainGUI


class DiagramBusSelectorDialogue(QtWidgets.QDialog):
    """
    ShortCircuitSelector
    """

    def __init__(self,
                 gui: VeraGridMainGUI,
                 grid: MultiCircuit,
                 substation: Substation):
        """

        :param gui:
        :param grid:
        :param substation:
        """
        super().__init__()
        self.setWindowTitle(self.tr("Bus selection by diagram"))

        self.layout = QVBoxLayout(self)

        selected_buses = grid.get_buses_from_objects(elements=[substation], dtype=DeviceType.SubstationDevice)

        if len(selected_buses):
            diagram = make_diagram_from_buses(circuit=grid,
                                              buses=selected_buses,
                                              name=substation.name + " diagram")
        else:
            diagram = SchematicDiagram()

        self.diagram_widget = SchematicWidget(
            gui=gui,
            diagram=diagram,
            default_bus_voltage=gui.ui.defaultBusVoltageSpinBox.value(),
            time_index=gui.get_diagram_slider_index()
        )

        self.layout.addWidget(self.diagram_widget)

        self.select_button = QPushButton(self.tr("Select"))
        self.diagram_widget.frame1_layout.addWidget(self.select_button)
        self.diagram_widget.library_view.setVisible(False)

        self._selected_buses: List[Bus] = list()

        self.select_button.clicked.connect(self.select)

    def select(self):
        """

        :return:
        """
        for i, bus, _ in self.diagram_widget.get_selected_buses():
            self._selected_buses.append(bus)

        self.close()

    def get_selected_buses(self) -> List[Bus]:
        """
        Get the selected buses
        :return:
        """
        return self._selected_buses
