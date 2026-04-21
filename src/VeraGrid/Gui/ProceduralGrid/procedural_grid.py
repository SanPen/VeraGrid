# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import sys
from typing import List, TYPE_CHECKING
import numpy as np
from PySide6 import QtWidgets

from VeraGrid.Gui.Diagrams.MapWidget.Substation.substation_graphic_item import SubstationGraphicItem
from VeraGrid.Gui.Diagrams.MapWidget.grid_map_widget import haversine_distance, GridMapWidget
from VeraGridEngine.Devices.Diagrams.map_location import MapLocation
import VeraGridEngine.Devices as dev
from VeraGrid.Gui.ProceduralGrid.procedural_grid_ui import Ui_Dialog
from VeraGrid.Gui.gui_functions import get_list_model, enums_to_model
from VeraGridEngine.enumerations import ProceduralGridMethods
from VeraGridEngine.Topology.Procedural.procedural_grid_engine import ProceduralGridComputationEngine
from VeraGridEngine.basic_structures import Logger
from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import make_diagram_from_buses, SchematicWidget
from VeraGrid.Gui.ProceduralGrid.voltage_warning import VoltageWarningDialog
from VeraGrid.Gui.general_dialogues import LogsDialogue

if TYPE_CHECKING:
    from VeraGrid.Gui.Main.SubClasses.simulations import SimulationsMain


class ProceduralGridWindow(QtWidgets.QDialog):
    """
    SystemScaler GUI
    """

    def __init__(self, app: SimulationsMain, parent=None):
        """

        :param parent:
        """
        QtWidgets.QDialog.__init__(self, parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle('Procedural grid expansion')
        self.app = app

        # Setup combobox
        self.methods_dict, methods_mdl = enums_to_model(
            [ProceduralGridMethods.SteinerAlone,
             ProceduralGridMethods.SteinerAndOptimization]
        )
        self.ui.methodComboBox.setModel(methods_mdl)
        self.ui.methodComboBox.setCurrentIndex(0)

        # setup candidates

        # setup connection substations
        self.connection_substations_graphics_list: List[SubstationGraphicItem] = list()
        self.candidate_list: List[SubstationGraphicItem] = list()
        self.all_substations_graphics_in_diagram_list: List[SubstationGraphicItem] = list()
        for se_idx, se_api_object, se_graphic in app.get_current_diagram_substations():

            self.all_substations_graphics_in_diagram_list.append(se_graphic)

            if se_graphic.isSelected():
                self.connection_substations_graphics_list.append(se_graphic)

        self.ui.targetSubstationListView.setModel(get_list_model(
            [se_graphic.api_object for se_graphic in self.connection_substations_graphics_list]
        ))

        # Button click
        self.ui.computeButton.clicked.connect(self.compute)
        self.ui.computeCandidatesButton.clicked.connect(self.compute_candidates)

    def compute_candidates(self):
        """

        :return:
        """
        n_number = len(self.connection_substations_graphics_list)
        mc_number = len(self.all_substations_graphics_in_diagram_list)
        top_n = self.ui.topClosestSpinBox.value()

        distances = np.zeros((mc_number, n_number))

        for j, se_graphic_target in enumerate(self.connection_substations_graphics_list):
            for i, se_graphic_candidate in enumerate(self.all_substations_graphics_in_diagram_list):
                distances[i, j] = haversine_distance(
                    lat1=se_graphic_candidate.lat,
                    lon1=se_graphic_candidate.lon,
                    lat2=se_graphic_target.lat,
                    lon2=se_graphic_target.lon
                )

        if distances.shape[0] > 0:

            distances2 = np.min(distances, axis=1)
            sorted_indices = np.argsort(distances2, axis=0)

            self.candidate_list.clear()
            for i in sorted_indices:
                if len(self.candidate_list) >= top_n:
                    break
                candidate = self.all_substations_graphics_in_diagram_list[i]
                if candidate not in self.connection_substations_graphics_list:
                    self.candidate_list.append(candidate)

            # display the candidates list
            self.ui.candidateSubstationListView.setModel(get_list_model(
                [se_graphic.api_object for se_graphic in self.candidate_list]
            ))

    def _check_substation_voltages(self, substations):
        """
        Returns offenders and valid voltages.
        Offenders are (substation_name, voltage) pairs for any bus
        whose Vnom does not appear on any branch in the existing grid.
        """
        known_voltages = set()
        for branch in self.app.circuit.get_branches(add_vsc=True, add_hvdc=True, add_switch=True):
            known_voltages.add(branch.bus_from.Vnom)
            known_voltages.add(branch.bus_to.Vnom)

        offenders = []
        for sg in substations:
            for bus in self.app.circuit.get_substation_buses(sg):
                if bus.Vnom not in known_voltages:
                    offenders.append((sg.name, bus.Vnom))

        return offenders, sorted(known_voltages)

    def compute(self):
        """
        Computation
        :return:
        """
        # 1. Get the chosen method
        method: ProceduralGridMethods = self.methods_dict[self.ui.methodComboBox.currentText()]

        # 2. Extract the raw API objects from the graphic items
        target_objects = [se.api_object for se in self.connection_substations_graphics_list]
        candidate_objects = [se.api_object for se in self.candidate_list]

        # 3. Validate that all substation voltages exist in the grid
        offenders, valid_voltages = self._check_substation_voltages(target_objects + candidate_objects)
        if offenders:
            dlg = VoltageWarningDialog(offenders=offenders, valid_voltages=valid_voltages, parent=self)
            dlg.exec()
            return

        # 4. Instantiate your engine with the required inputs
        logger = Logger()
        engine = ProceduralGridComputationEngine(
            grid=self.app.circuit,
            method=method,
            targets=target_objects,
            candidates=candidate_objects,
            logger=logger
        )

        if method == ProceduralGridMethods.SteinerAlone:
            expanded_grid = engine.run_steiner_alone()

        elif method == ProceduralGridMethods.SteinerAndOptimization:
            expanded_grid = engine.run_optimization()

        else:
            raise NotImplementedError(f"Method {method} not implemented")

        # Create substations for new buses so map lines can reference them
        for bus in engine.get_new_buses():
            if bus.substation is None:
                substation = dev.Substation(
                    name=bus.name,
                    latitude=bus.latitude,
                    longitude=bus.longitude,
                )
                bus.substation = substation
                self.app.circuit.add_substation(substation)

        # Draw new elements on all open map widgets
        for map_widget in self.app.diagram_widgets_list:
            if isinstance(map_widget, GridMapWidget):
                for bus in engine.get_new_buses():
                    if map_widget.graphics_manager.query(elm=bus.substation) is None:
                        map_widget.add_api_substation(api_object=bus.substation,
                                                      lat=bus.latitude,
                                                      lon=bus.longitude)
                for line in engine.get_new_lines():
                    if map_widget.graphics_manager.query(elm=line) is None:
                        map_widget.diagram.set_point(device=line, location=MapLocation())
                        map_widget.add_api_line(api_object=line)

        # Map geographic coordinates to schematic canvas coordinates
        _SCALE = 1000.0
        for bus in expanded_grid.buses:
            bus.x = bus.longitude * _SCALE
            bus.y = -bus.latitude * _SCALE

        # create the diagram
        expanded_grid_schematic = make_diagram_from_buses(circuit=expanded_grid,
                                                          buses=engine.get_buses(),
                                                          name=f'Diagram {method.value}')

        # create the schematic widget
        diagram_widget = SchematicWidget(
            gui=self.app,
            diagram=expanded_grid_schematic,
            default_bus_voltage=self.app.ui.defaultBusVoltageSpinBox.value(),
            time_index=self.app.get_diagram_slider_index()
        )

        # add the widget on the main GUI
        self.app.add_diagram_widget_and_diagram(diagram_widget=diagram_widget,
                                                diagram=expanded_grid_schematic)
        self.app.set_diagrams_list_view()

        # Show logger if there are any entries
        if logger.has_logs():
            dlg = LogsDialogue('Procedural grid expansion log', logger)
            dlg.exec()

        # Exit
        self.close()
