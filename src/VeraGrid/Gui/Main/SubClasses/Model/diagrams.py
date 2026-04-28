# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import os
from typing import List, Tuple, Union, Callable, Iterable

import networkx as nx
import numpy as np
from PySide6 import QtGui, QtWidgets, QtCore
from matplotlib import pyplot as plt
from pandas.plotting import register_matplotlib_converters

import VeraGridEngine.Devices.Diagrams.palettes as palettes
from VeraGridEngine import ContingencyOperationTypes, MapDiagram
from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent
from VeraGridEngine.IO.file_system import tiles_path
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Simulations import PowerFlowResults, ContinuationPowerFlowResults, PowerFlowTimeSeriesResults
from VeraGridEngine.Simulations.PowerFlow.power_flow_results_3ph import PowerFlowResults3Ph
from VeraGridEngine.Simulations.StateEstimation.state_estimation_results import StateEstimationResults
from VeraGridEngine.Utils.progress_bar import print_progress_bar
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import (SimulationTypes, Colormaps, DeviceType, MethodShortCircuit,
                                         SchematicAutoRouteStyle, DynamicSimulationMode)
from VeraGridEngine.Devices.Diagrams.schematic_diagram import SchematicDiagram

import VeraGridEngine.Devices as dev
import VeraGridEngine.Simulations as sim
import VeraGrid.Gui.gui_functions as gf
import VeraGrid.Gui.Visualization.visualization as viz
from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import (SchematicWidget,
                                                                    BusGraphicItem,
                                                                    generate_schematic_diagram,
                                                                    make_vicinity_diagram,
                                                                    make_diagram_from_buses)
from VeraGrid.Gui.Diagrams.MapWidget.grid_map_widget import GridMapWidget, generate_map_diagram
from VeraGrid.Gui.Diagrams.base_diagram_widget import BaseDiagramWidget
from VeraGrid.Gui.Diagrams.SchematicWidget.diagram_bus_selection_dialogue import DiagramBusSelectorDialogue
from VeraGrid.Gui.Diagrams.diagrams_model import DiagramsModel
from VeraGrid.Gui.messages import yes_no_question, error_msg, info_msg
from VeraGrid.Gui.Main.SubClasses.Model.compiled_arrays import CompiledArraysMain
from VeraGrid.Gui.Main.object_select_window import ObjectSelectWindow, ListSelectWindow
from VeraGrid.Gui.Diagrams.MapWidget.Tiles.TileProviders.cartodb import CartoDbTiles
from VeraGrid.Gui.object_proxy_model import ObjectModelFilterProxy
from VeraGrid.Gui.dynamic_events_editor_dialog import DynamicEventDialogue, DynamicEventsGroupsDialog
from VeraGrid.Gui.Diagrams.MapWidget.Substation.substation_graphic_item import SubstationGraphicItem
from VeraGrid.Gui.ShortCircuitEditor.short_circuit_selector import ShortCircuitSelector
from VeraGrid.Gui.general_dialogues import (CheckListDialogue, StartEndSelectionDialogue,
                                            InputNumberDialogue, LogsDialogue)

ALL_EDITORS = Union[SchematicWidget, GridMapWidget, BaseDiagramWidget]
ALL_EDITORS_NONE = Union[None, SchematicWidget, GridMapWidget]
DIAGRAM_WIDGETS = Union[SchematicWidget, GridMapWidget]


class VideoExportWorker(QtCore.QThread):
    """
    VideoExportWorker
    """
    progress_signal = QtCore.Signal(float)
    progress_text = QtCore.Signal(str)
    done_signal = QtCore.Signal()

    def __init__(self, filename, diagram: ALL_EDITORS,
                 fps: int, start_idx: int, end_idx: int, current_study: str,
                 grid_colour_function: Callable[[ALL_EDITORS, str, int, bool], None], ):
        """

        :param filename:
        :param diagram:
        :param fps:
        :param start_idx:
        :param end_idx:
        :param current_study:
        :param grid_colour_function:
        """
        QtCore.QThread.__init__(self)

        self.filename = filename
        self.diagram = diagram
        self.fps: int = fps
        self.start_idx: int = start_idx
        self.end_idx: int = end_idx
        self.current_study = current_study
        self.grid_colour_function: Callable[[ALL_EDITORS, str, int, bool], None] = grid_colour_function

        self.logger: Logger = Logger()

    def run(self):
        """
        Run function
        :return:
        """
        # start recording...
        w, h = self.diagram.start_video_recording(fname=self.filename, fps=self.fps, logger=self.logger)

        # paint and capture
        for t_idx in range(self.start_idx, self.end_idx):
            self.grid_colour_function(
                self.diagram,  # diagram
                self.current_study,  # current_study
                t_idx,  # t_idx
                False  # allow_popups
            )

            self.diagram.capture_video_frame(w=w, h=h, logger=self.logger)

            self.progress_text.emit(f"Saving frame {t_idx} / {self.end_idx}")
            self.progress_signal.emit(t_idx / self.end_idx)

            print_progress_bar(t_idx + 1, self.end_idx)

        # finalize
        self.diagram.end_video_recording()

        self.logger.add_info(f"Video saved to {self.filename}")

        self.done_signal.emit()


class DiagramsMain(CompiledArraysMain):
    """
    Diagrams Main
    """

    def __init__(self, parent=None):
        """

        @param parent:
        """

        # create main window
        CompiledArraysMain.__init__(self, parent)

        # list of diagrams
        self.diagram_widgets_list: List[DIAGRAM_WIDGETS] = list()

        # flag to avoid circular updating of the display settings when changing diagrams
        self._enable_setting_auto_upgrade = True

        # Declare the map
        palettes_list = [palettes.Colormaps.VeraGrid,
                         palettes.Colormaps.Green2Red,
                         palettes.Colormaps.Heatmap,
                         palettes.Colormaps.TSO]
        self.cmap_dict = {e.value: e for e in palettes_list}
        self.cmap_index_dict = {pal: i for i, pal in enumerate(palettes_list)}
        self.ui.palette_comboBox.setModel(gf.get_list_model([e.value for e in palettes_list]))

        # map tile sources
        self.tile_sources = [
            CartoDbTiles(
                name='Carto voyager',
                tiles_dir=os.path.join(tiles_path(), 'carto_db_voyager'),
                tile_servers=["https://basemaps.cartocdn.com/rastertiles/voyager/"]
            ),
            CartoDbTiles(
                name='Carto positron',
                tiles_dir=os.path.join(tiles_path(), 'carto_db_positron'),
                tile_servers=['https://basemaps.cartocdn.com/light_all/']
            ),
            CartoDbTiles(
                name='Carto dark matter',
                tiles_dir=os.path.join(tiles_path(), 'carto_db_dark_matter'),
                tile_servers=["https://basemaps.cartocdn.com/dark_all/"]
            ),
            CartoDbTiles(
                name='Open Street Map',
                tiles_dir=os.path.join(tiles_path(), 'osm'),
                tile_servers=["https://tile.openstreetmap.org"],
                max_zoom=21
            ),
        ]
        tile_names = [tile.tile_set_name for tile in self.tile_sources]
        self.tile_index_dict = {tile.tile_set_name: i for i, tile in enumerate(self.tile_sources)}
        self.tile_name_dict = {tile.tile_set_name: tile for tile in self.tile_sources}
        self.ui.tile_provider_comboBox.setModel(gf.get_list_model(tile_names))
        self.ui.tile_provider_comboBox.setCurrentIndex(0)

        # Automatic layout modes
        self.layout_algorithms_dict = dict()
        self.layout_algorithms_dict['power_system_layout'] = nx.spring_layout
        self.layout_algorithms_dict['circular_layout'] = nx.circular_layout
        self.layout_algorithms_dict['random_layout'] = nx.random_layout
        self.layout_algorithms_dict['shell_layout'] = nx.shell_layout
        self.layout_algorithms_dict['spring_layout'] = nx.spring_layout
        self.layout_algorithms_dict['spectral_layout'] = nx.spectral_layout
        self.layout_algorithms_dict['fruchterman_reingold_layout'] = nx.fruchterman_reingold_layout
        self.layout_algorithms_dict['kamada_kawai'] = nx.kamada_kawai_layout
        self.layout_algorithms_dict['arf'] = nx.arf_layout
        self.layout_algorithms_dict['planar'] = nx.planar_layout
        self.layout_algorithms_dict['bipartite'] = nx.bipartite_layout
        self.layout_algorithms_dict['multipartite'] = nx.multipartite_layout

        mdl = gf.get_list_model(list(self.layout_algorithms_dict.keys()))
        self.ui.automatic_layout_comboBox.setModel(mdl)
        self.ui.automatic_layout_comboBox.setCurrentText('power_system_layout')

        # list of steps in the schematic
        self.schematic_list_steps = list()

        self.available_results_steps_dict = None

        # list of styles
        self.ui.plt_style_comboBox.setModel(gf.get_list_model(plt.style.available))
        if 'fivethirtyeight' in plt.style.available:
            self.ui.plt_style_comboBox.setCurrentText('fivethirtyeight')

        self.ui.diagramSearchLineEdit.setPlaceholderText("Type to search in the current diagram")

        # configure matplotlib for pandas time series
        register_matplotlib_converters()

        # task watcher for video export
        self.video_thread: VideoExportWorker | None = None

        self.sc_selector_dialogue: ShortCircuitSelector = ShortCircuitSelector()

        # --------------------------------------------------------------------------------------------------------------
        self.ui.actionTakePicture.triggered.connect(self.take_picture)
        self.ui.actionRecord_video.triggered.connect(self.record_video)
        self.ui.actionTry_to_fix_buses_location.triggered.connect(self.try_to_fix_buses_location)
        self.ui.actionSet_schematic_positions_from_GPS_coordinates.triggered.connect(self.set_xy_from_lat_lon)

        self.ui.actionSetSelectedBusCountry.triggered.connect(lambda: self.set_selected_bus_property('country'))
        self.ui.actionSetSelectedBusArea.triggered.connect(lambda: self.set_selected_bus_property('area'))
        self.ui.actionSetSelectedBusZone.triggered.connect(lambda: self.set_selected_bus_property('zone'))

        self.ui.actionSelect_buses_by.triggered.connect(self.select_buses_by)
        self.ui.actionColor_buses_by.triggered.connect(self.color_buses_by)
        self.ui.actionColor_substations_by.triggered.connect(self.color_substations_by)

        self.ui.actionAdd_selected_to_contingency.triggered.connect(self.add_selected_to_contingency)
        self.ui.actionAdd_selected_as_remedial_action.triggered.connect(self.add_selected_to_remedial_action)
        self.ui.actionAdd_selected_as_new_investment.triggered.connect(self.add_selected_to_investment)
        self.ui.actionAdd_rms_event_to_selected.triggered.connect(self.add_rms_event_to_selected)
        self.ui.actionAdd_emt_event_to_selected.triggered.connect(self.add_emt_event_to_selected)
        self.ui.actionAdd_short_circuit_events.triggered.connect(self.add_short_circuit_events)

        self.ui.actionZoom_in.triggered.connect(self.zoom_in)
        self.ui.actionZoom_out.triggered.connect(self.zoom_out)
        self.ui.actionAdd_general_bus_branch_diagram.triggered.connect(self.add_complete_bus_branch_diagram)
        self.ui.actionNew_bus_branch_diagram_from_selection.triggered.connect(
            self.new_bus_branch_diagram_from_selection)
        self.ui.actionAdd_map.triggered.connect(self.add_map_diagram)
        self.ui.actionBigger_nodes.triggered.connect(self.bigger_nodes)
        self.ui.actionSmaller_nodes.triggered.connect(self.smaller_nodes)
        self.ui.actionCenter_view.triggered.connect(self.center_nodes)
        self.ui.actionAutoatic_layout.triggered.connect(self.auto_layout)

        self.ui.actionEdit_simulation_time_limits.triggered.connect(self.edit_time_interval)
        self.ui.actionDisable_all_results_tags.triggered.connect(self.disable_all_results_tags)
        self.ui.actionEnable_all_results_tags.triggered.connect(self.enable_all_results_tags)
        self.ui.actionConsolidate_diagram_coordinates.triggered.connect(self.consolidate_diagram_coordinates)
        self.ui.actionReset_coordinates.triggered.connect(self.reset_diagram_coordinates)
        self.ui.actionRotate.triggered.connect(self.rotate)
        self.ui.actionClear_highlights.triggered.connect(self.clear_big_bus_markers)

        self.ui.actionSetReticularBranchStyles.triggered.connect(self.set_diagram_branches_reticular_style)
        self.ui.actionSetStraightBranchStyles.triggered.connect(self.set_diagram_branches_straight_style)

        # Buttons
        self.ui.colour_results_pushButton.clicked.connect(self.colour_diagrams)
        self.ui.redraw_pushButton.clicked.connect(self.redraw_current_diagram)
        self.ui.diagramSearchButton.clicked.connect(self.search_diagram)

        self.ui.preset1_pushButton.clicked.connect(self.preset_1)
        self.ui.preset2_pushButton.clicked.connect(self.preset_2)
        self.ui.preset3_pushButton.clicked.connect(self.preset_3)
        self.ui.preset4_pushButton.clicked.connect(self.preset_4)

        # list clicks
        self.ui.diagramsListView.clicked.connect(self.set_selected_diagram_on_click)

        # combobox change
        self.ui.plt_style_comboBox.currentTextChanged.connect(self.plot_style_change)
        self.ui.palette_comboBox.currentTextChanged.connect(self.set_diagrams_palette)
        self.ui.tile_provider_comboBox.currentTextChanged.connect(self.set_diagrams_map_tile_provider)

        # TODO: this lambda calls to colour twice is the simulation is run the first time
        self.ui.available_results_to_color_comboBox.currentTextChanged.connect(lambda: self.colour_diagrams(False))

        # sliders
        self.ui.diagram_step_slider.sliderReleased.connect(self.colour_diagrams)
        self.ui.diagram_step_slider.valueChanged.connect(self.diagrams_time_slider_change)
        self.ui.db_step_slider.valueChanged.connect(self.objects_time_slider_change)

        # spinbox change
        self.ui.explosion_factor_doubleSpinBox.valueChanged.connect(self.explosion_factor_change)
        self.ui.defaultBusVoltageSpinBox.valueChanged.connect(self.default_voltage_change)

        self.ui.min_branch_size_spinBox.valueChanged.connect(self.set_diagrams_size_constraints)
        self.ui.max_branch_size_spinBox.valueChanged.connect(self.set_diagrams_size_constraints)
        self.ui.min_node_size_spinBox.valueChanged.connect(self.set_diagrams_size_constraints)
        self.ui.max_node_size_spinBox.valueChanged.connect(self.set_diagrams_size_constraints)
        self.ui.arrow_size_size_spinBox.valueChanged.connect(self.set_diagrams_size_constraints)

        # check boxes
        self.ui.branch_width_based_on_flow_checkBox.clicked.connect(self.set_diagrams_size_constraints)
        self.ui.use_schematic_objects_color_checkBox.clicked.connect(self.re_colour_schematic)

        # TreeView
        self.ui.combinationsTreeView.clicked.connect(self.combinations_tree_clicked)

        # context menu
        self.ui.diagramsListView.customContextMenuRequested.connect(self.show_diagrams_context_menu)

        # Set context menu policy to CustomContextMenu
        self.ui.diagramsListView.setContextMenuPolicy(QtGui.Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.diagramsListView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)

    def get_current_objects_model_view(self) -> ObjectModelFilterProxy | None:
        """
        Get the current ObjectModelFilterProxy from the GUI
        :return: ObjectModelFilterProxy
        """
        return self.ui.dataStructureTableView.model()

    def get_selected_db_table_objects(self) -> List[ALL_DEV_TYPES]:
        """
        Get the list of selected objects
        :return: List[ALL_DEV_TYPES]
        """
        model: ObjectModelFilterProxy | None = self.get_current_objects_model_view()

        if model is not None:
            sel_idx = self.ui.dataStructureTableView.selectedIndexes()
            if len(sel_idx) > 0:

                # get the unique rows
                unique = set()
                for idx in sel_idx:
                    unique.add(idx.row())

                return [model.objects[i] for i in unique]
            else:
                info_msg('Select some cells')
                return list()
        else:
            return list()

    def get_default_voltage(self) -> float:
        """
        Get the default marked voltage
        :return:
        """
        return self.ui.defaultBusVoltageSpinBox.value()

    def auto_layout(self):
        """
        Automatic layout of the nodes
        """

        diagram_widget = self.get_selected_diagram_widget()

        if diagram_widget:
            if isinstance(diagram_widget, SchematicWidget):

                # guilty assumption
                do_it = True

                # if the ask, checkbox is checked, then ask
                if self.ui.ask_before_appliying_layout_checkBox.isChecked():
                    reply = QtWidgets.QMessageBox.question(self, 'Message',
                                                           'Are you sure that you want to try an automatic layout?',
                                                           QtWidgets.QMessageBox.StandardButton.Yes,
                                                           QtWidgets.QMessageBox.StandardButton.No)

                    if reply == QtWidgets.QMessageBox.StandardButton.Yes.value:
                        do_it = True
                    else:
                        do_it = False

                if do_it:
                    diagram_widget.auto_layout(sel=self.ui.automatic_layout_comboBox.currentText())

            else:
                info_msg("The current diagram cannot be automatically layed out")
        else:
            pass  # asked and decided ot to change the layout

    def bigger_nodes(self):
        """
        Move the nodes more separated
        """
        diagram = self.get_selected_diagram_widget()
        if diagram is not None:
            if isinstance(diagram, SchematicWidget):
                diagram.expand_node_distances()
                diagram.center_nodes()

    def smaller_nodes(self):
        """
        Move the nodes closer
        """
        diagram = self.get_selected_diagram_widget()
        if diagram is not None:
            if isinstance(diagram, SchematicWidget):
                diagram.shrink_node_distances()
                diagram.center_nodes()

    def center_nodes(self):
        """
        Center the nodes in the screen
        """

        widget = self.get_selected_diagram_widget()
        if widget is not None:
            if isinstance(widget, SchematicWidget):
                selected = self.get_diagram_selected_buses()

                if len(selected) == 0:
                    widget.center_nodes(elements=None)
                else:
                    buses = [bus for i, bus, graphic in selected]
                    widget.center_nodes(elements=buses)

            elif isinstance(widget, GridMapWidget):
                widget.center()

    def get_diagram_selected_buses(self) -> List[Tuple[int, dev.Bus, BusGraphicItem | None]]:
        """
        Get the selected buses
        :return: list of (bus position, bus object, bus_graphics object)
        """
        diagram_widget = self.get_selected_diagram_widget()
        if isinstance(diagram_widget, SchematicWidget):
            return diagram_widget.get_selected_buses()
        elif isinstance(diagram_widget, GridMapWidget):
            return diagram_widget.get_selected_buses()
        else:
            return list()

    def get_current_diagram_buses(self) -> List[Tuple[int, dev.Bus, BusGraphicItem]]:
        """
        Get the selected buses
        :return: list of (bus position, bus object, bus_graphics object)
        """
        diagram_widget = self.get_selected_diagram_widget()
        if isinstance(diagram_widget, SchematicWidget):
            return diagram_widget.get_buses()
        else:
            return list()

    def get_current_diagram_substations(self) -> List[Tuple[int, dev.Substation, SubstationGraphicItem]]:
        """
        Get the selected buses
        :return: list of (bus position, bus object, bus_graphics object)
        """
        diagram_widget = self.get_selected_diagram_widget()
        if isinstance(diagram_widget, GridMapWidget):
            return diagram_widget.get_substations()
        else:
            return list()

    def explosion_factor_change(self):
        """
        Change the node explosion factor
        """
        for diagram in self.diagram_widgets_list:
            if isinstance(diagram, SchematicWidget):
                diagram.expand_factor = self.ui.explosion_factor_doubleSpinBox.value()

    def zoom_in(self):
        """
        Zoom the diagram in
        """
        diagram = self.get_selected_diagram_widget()
        if diagram is not None:
            if isinstance(diagram, SchematicWidget):
                diagram.zoom_in()
            elif isinstance(diagram, GridMapWidget):
                diagram.zoom_in()
            else:
                print("zoom_in: Unsupported diagram type")

    def zoom_out(self):
        """
        Zoom the diagram out
        """
        diagram = self.get_selected_diagram_widget()
        if diagram is not None:
            if isinstance(diagram, Union[SchematicWidget, GridMapWidget]):
                diagram.zoom_out()
            else:
                print("zoom_out: Unsupported diagram type")

    def edit_time_interval(self):
        """
        Run the simulation limits adjust window
        """

        if self.circuit.has_time_series:
            if self.circuit.get_time_number() > 0:
                self.start_end_dialogue_window = StartEndSelectionDialogue(min_value=self.simulation_start_index,
                                                                           max_value=self.simulation_end_index,
                                                                           time_array=self.circuit.time_profile)

                self.start_end_dialogue_window.setModal(True)
                self.start_end_dialogue_window.exec()

                if self.start_end_dialogue_window.is_accepted:
                    self.setup_sim_indices(st=self.start_end_dialogue_window.start_value,
                                           en=self.start_end_dialogue_window.end_value)
            else:
                self.show_error_toast("Empty time series :/")
        else:
            self.show_error_toast("There are no time series :/")

    def pf_colouring(self, diagram_widget: ALL_EDITORS,
                     results: PowerFlowResults,
                     cmap: Colormaps,
                     use_flow_based_width: bool = False,
                     min_branch_width: int = 2,
                     max_branch_width: int = 5,
                     min_bus_width: int = 2,
                     max_bus_width: int = 5):
        """

        :param diagram_widget:
        :param results:
        :param cmap:
        :param use_flow_based_width:
        :param min_branch_width:
        :param max_branch_width:
        :param min_bus_width:
        :param max_bus_width:
        :return:
        """
        bus_active = self.circuit.get_bus_actives(t_idx=None)
        br_active = self.circuit.get_branch_actives(t_idx=None, add_vsc=False, add_hvdc=False, add_switch=True)
        hvdc_active = self.circuit.get_hvdc_actives(t_idx=None)
        vsc_active = self.circuit.get_vsc_actives(t_idx=None)

        return diagram_widget.colour_results(
            Sbus=results.Sbus,
            bus_active=bus_active,
            Sf=results.Sf,
            St=results.St,
            voltages=results.voltage,
            loadings=np.abs(results.loading),
            types=results.bus_types,
            losses=results.losses,
            br_active=br_active,
            hvdc_Pf=results.Pf_hvdc,
            hvdc_Pt=results.Pt_hvdc,
            hvdc_losses=results.losses_hvdc,
            hvdc_loading=results.loading_hvdc,
            hvdc_active=hvdc_active,
            vsc_Pf=results.Pfp_vsc,
            vsc_Pt=results.St_vsc.real,
            vsc_Qt=results.St_vsc.imag,
            vsc_losses=results.losses_vsc,
            vsc_loading=results.loading_vsc,
            vsc_active=vsc_active,
            ma=results.tap_module,
            tau=results.tap_angle,
            use_flow_based_width=use_flow_based_width,
            min_branch_width=min_branch_width,
            max_branch_width=max_branch_width,
            min_bus_width=min_bus_width,
            max_bus_width=max_bus_width,
            cmap=cmap
        )

    def pf_3ph_colouring(self, diagram_widget: ALL_EDITORS,
                         results: PowerFlowResults3Ph,
                         cmap: Colormaps,
                         use_flow_based_width: bool = False,
                         min_branch_width: int = 2,
                         max_branch_width: int = 5,
                         min_bus_width: int = 2,
                         max_bus_width: int = 5):
        """

        :param diagram_widget:
        :param results:
        :param cmap:
        :param use_flow_based_width:
        :param min_branch_width:
        :param max_branch_width:
        :param min_bus_width:
        :param max_bus_width:
        :return:
        """
        bus_active = self.circuit.get_bus_actives(t_idx=None)
        br_active = self.circuit.get_branch_actives(t_idx=None, add_vsc=False, add_hvdc=False, add_switch=True)
        hvdc_active = self.circuit.get_hvdc_actives(t_idx=None)
        vsc_active = self.circuit.get_vsc_actives(t_idx=None)

        return diagram_widget.colour_results_3ph(
            SbusA=results.Sbus_A,
            SbusB=results.Sbus_B,
            SbusC=results.Sbus_C,
            voltagesA=results.voltage_A,
            voltagesB=results.voltage_B,
            voltagesC=results.voltage_C,
            bus_active=bus_active,
            types=results.bus_types,
            SfA=results.Sf_A,
            SfB=results.Sf_B,
            SfC=results.Sf_C,
            StA=results.St_A,
            StB=results.St_B,
            StC=results.St_C,
            loadingsA=results.loading_A,
            loadingsB=results.loading_B,
            loadingsC=results.loading_C,
            lossesA=results.losses_A,
            lossesB=results.losses_B,
            lossesC=results.losses_C,
            br_active=br_active,
            ma=results.tap_module,
            tau=results.tap_angle,
            hvdc_PfA=results.Pf_hvdc_A,
            hvdc_PfB=results.Pf_hvdc_B,
            hvdc_PfC=results.Pf_hvdc_C,
            hvdc_PtA=results.Pt_hvdc_A,
            hvdc_PtB=results.Pt_hvdc_B,
            hvdc_PtC=results.Pt_hvdc_C,
            hvdc_losses=results.losses_hvdc,
            hvdc_loading=results.loading_hvdc,
            hvdc_active=hvdc_active,
            vsc_Pf=results.Pfp_vsc,
            vsc_PtA=results.St_vsc_A.real,
            vsc_PtB=results.St_vsc_B.real,
            vsc_PtC=results.St_vsc_C.real,
            vsc_QtA=results.St_vsc_A.imag,
            vsc_QtB=results.St_vsc_B.imag,
            vsc_QtC=results.St_vsc_C.imag,
            vsc_losses=results.losses_vsc,
            vsc_loading=results.loading_vsc,
            vsc_active=vsc_active,
            loading_label='loading',
            use_flow_based_width=use_flow_based_width,
            min_branch_width=min_branch_width,
            max_branch_width=max_branch_width,
            min_bus_width=min_bus_width,
            max_bus_width=max_bus_width,
            cmap=cmap)

    def se_colouring(self, diagram_widget: ALL_EDITORS,
                     results: StateEstimationResults,
                     cmap: Colormaps,
                     use_flow_based_width: bool = False,
                     min_branch_width: int = 2,
                     max_branch_width: int = 5,
                     min_bus_width: int = 2,
                     max_bus_width: int = 5):
        """

        :param diagram_widget:
        :param results:
        :param cmap:
        :param use_flow_based_width:
        :param min_branch_width:
        :param max_branch_width:
        :param min_bus_width:
        :param max_bus_width:
        :return:
        """
        bus_active = self.circuit.get_bus_actives(t_idx=None)
        br_active = self.circuit.get_branch_actives(t_idx=None, add_vsc=False, add_hvdc=False, add_switch=True)
        hvdc_active = self.circuit.get_hvdc_actives(t_idx=None)
        vsc_active = self.circuit.get_vsc_actives(t_idx=None)

        return diagram_widget.colour_results(
            Sbus=results.Sbus,
            bus_active=bus_active,
            Sf=results.Sf,
            St=results.St,
            voltages=results.voltage,
            loadings=np.abs(results.loading),
            types=results.bus_types,
            losses=results.losses,
            br_active=br_active,
            hvdc_Pf=results.Pf_hvdc,
            hvdc_Pt=results.Pt_hvdc,
            hvdc_losses=results.losses_hvdc,
            hvdc_loading=results.loading_hvdc,
            hvdc_active=hvdc_active,
            vsc_Pf=results.Pf_vsc,
            vsc_Pt=results.St_vsc.real,
            vsc_Qt=results.St_vsc.imag,
            vsc_losses=results.losses_vsc,
            vsc_loading=results.loading_vsc,
            vsc_active=vsc_active,
            ma=results.tap_module,
            tau=results.tap_angle,
            use_flow_based_width=use_flow_based_width,
            min_branch_width=min_branch_width,
            max_branch_width=max_branch_width,
            min_bus_width=min_bus_width,
            max_bus_width=max_bus_width,
            cmap=cmap
        )

    def pf_ts_colouring(self, t_idx: int,
                        diagram_widget: ALL_EDITORS,
                        results: PowerFlowTimeSeriesResults, cmap: Colormaps,
                        use_flow_based_width: bool = False,
                        min_branch_width: int = 2,
                        max_branch_width: int = 5,
                        min_bus_width: int = 2,
                        max_bus_width: int = 5):
        """

        :param t_idx:
        :param diagram_widget:
        :param results:
        :param cmap:
        :param use_flow_based_width:
        :param min_branch_width:
        :param max_branch_width:
        :param min_bus_width:
        :param max_bus_width:
        :return:
        """
        bus_active = self.circuit.get_bus_actives(t_idx=t_idx)
        br_active = self.circuit.get_branch_actives(t_idx=t_idx, add_vsc=False, add_hvdc=False, add_switch=True)
        hvdc_active = self.circuit.get_hvdc_actives(t_idx=t_idx)
        vsc_active = self.circuit.get_vsc_actives(t_idx=t_idx)

        return diagram_widget.colour_results(Sbus=results.S[t_idx, :],
                                             bus_active=bus_active,
                                             Sf=results.Sf[t_idx, :],
                                             St=results.St[t_idx, :],
                                             voltages=results.voltage[t_idx, :],
                                             loadings=np.abs(results.loading[t_idx, :]),
                                             types=results.bus_types,
                                             losses=results.losses[t_idx, :],
                                             br_active=br_active,
                                             hvdc_Pf=results.hvdc_Pf[t_idx, :],
                                             hvdc_Pt=results.hvdc_Pt[t_idx, :],
                                             hvdc_losses=results.hvdc_losses[t_idx, :],
                                             hvdc_loading=results.hvdc_loading[t_idx, :],
                                             hvdc_active=hvdc_active,
                                             use_flow_based_width=use_flow_based_width,
                                             min_branch_width=min_branch_width,
                                             max_branch_width=max_branch_width,
                                             min_bus_width=min_bus_width,
                                             max_bus_width=max_bus_width,
                                             cmap=cmap)

    def cpf_colouring(self, diagram_widget: ALL_EDITORS,
                      results: ContinuationPowerFlowResults, cmap: Colormaps,
                      use_flow_based_width: bool = False,
                      min_branch_width: int = 2,
                      max_branch_width: int = 5,
                      min_bus_width: int = 2,
                      max_bus_width: int = 5):
        """

        :param diagram_widget:
        :param results:
        :param cmap:
        :param use_flow_based_width:
        :param min_branch_width:
        :param max_branch_width:
        :param min_bus_width:
        :param max_bus_width:
        :return:
        """
        bus_active = self.circuit.get_bus_actives(t_idx=None)
        br_active = self.circuit.get_branch_actives(t_idx=None, add_vsc=False, add_hvdc=False, add_switch=True)
        hvdc_active = self.circuit.get_hvdc_actives(t_idx=None)
        vsc_active = self.circuit.get_vsc_actives(t_idx=None)

        if results.Sbus.shape[0] > 0:
            return diagram_widget.colour_results(Sbus=results.Sbus[-1, :],
                                                 bus_active=bus_active,
                                                 Sf=results.Sf[-1, :],
                                                 St=results.St[-1, :],
                                                 voltages=results.voltages[-1, :],
                                                 types=results.bus_types,
                                                 loadings=np.abs(results.loading[-1, :]),
                                                 br_active=br_active,
                                                 hvdc_Pf=None,
                                                 hvdc_Pt=None,
                                                 hvdc_losses=None,
                                                 hvdc_loading=None,
                                                 hvdc_active=hvdc_active,
                                                 use_flow_based_width=use_flow_based_width,
                                                 min_branch_width=min_branch_width,
                                                 max_branch_width=max_branch_width,
                                                 min_bus_width=min_bus_width,
                                                 max_bus_width=max_bus_width,
                                                 cmap=cmap)

    def spf_colouring(self, diagram_widget: ALL_EDITORS,
                      results: sim.StochasticPowerFlowResults, cmap: Colormaps,
                      use_flow_based_width: bool = False,
                      min_branch_width: int = 2,
                      max_branch_width: int = 5,
                      min_bus_width: int = 2,
                      max_bus_width: int = 5):
        """

        :param diagram_widget:
        :param results:
        :param cmap:
        :param use_flow_based_width:
        :param min_branch_width:
        :param max_branch_width:
        :param min_bus_width:
        :param max_bus_width:
        :return:
        """
        bus_active = self.circuit.get_bus_actives(t_idx=None)
        br_active = self.circuit.get_branch_actives(t_idx=None, add_vsc=False, add_hvdc=False, add_switch=True)
        hvdc_active = self.circuit.get_hvdc_actives(t_idx=None)
        vsc_active = self.circuit.get_vsc_actives(t_idx=None)

        return diagram_widget.colour_results(Sbus=results.S_points.mean(axis=0),
                                             types=results.bus_types,
                                             voltages=results.V_points.mean(axis=0),
                                             bus_active=bus_active,
                                             loadings=np.abs(results.loading_points).mean(axis=0),
                                             Sf=results.Sbr_points.mean(axis=0),
                                             St=-results.Sbr_points.mean(axis=0),
                                             br_active=br_active,
                                             hvdc_Pf=None,
                                             hvdc_Pt=None,
                                             hvdc_losses=None,
                                             hvdc_loading=None,
                                             hvdc_active=None,
                                             use_flow_based_width=use_flow_based_width,
                                             min_branch_width=min_branch_width,
                                             max_branch_width=max_branch_width,
                                             min_bus_width=min_bus_width,
                                             max_bus_width=max_bus_width,
                                             cmap=cmap)

    def sc_colouring(self, diagram_widget: ALL_EDITORS,
                     results: sim.ShortCircuitResults,
                     cmap: Colormaps,
                     use_flow_based_width: bool = False,
                     min_branch_width: int = 2,
                     max_branch_width: int = 5,
                     min_bus_width: int = 2,
                     max_bus_width: int = 5,
                     sc_index: int = 0):
        """

        :param diagram_widget:
        :param results:
        :param cmap:
        :param use_flow_based_width:
        :param min_branch_width:
        :param max_branch_width:
        :param min_bus_width:
        :param max_bus_width:
        :param sc_index:
        :return:
        """
        bus_active = self.circuit.get_bus_actives(t_idx=None)
        br_active = self.circuit.get_branch_actives(t_idx=None, add_vsc=False, add_hvdc=False, add_switch=True)
        hvdc_active = self.circuit.get_hvdc_actives(t_idx=None)
        vsc_active = self.circuit.get_vsc_actives(t_idx=None)
        method = self.circuit.short_circuit_event[sc_index].method

        if method == MethodShortCircuit.phases:
            return diagram_widget.colour_results_3ph(
                SbusA=results.SbusA[:, sc_index],
                SbusB=results.SbusB[:, sc_index],
                SbusC=results.SbusC[:, sc_index],
                bus_active=bus_active,
                SfA=results.SfA[:, sc_index],
                SfB=results.SfB[:, sc_index],
                SfC=results.SfC[:, sc_index],
                StA=results.StA[:, sc_index],
                StB=results.StB[:, sc_index],
                StC=results.StC[:, sc_index],
                voltagesA=results.voltageA[:, sc_index],
                voltagesB=results.voltageB[:, sc_index],
                voltagesC=results.voltageC[:, sc_index],
                types=results.bus_types,
                loadingsA=results.loadingA[:, sc_index],
                loadingsB=results.loadingB[:, sc_index],
                loadingsC=results.loadingC[:, sc_index],
                lossesA=results.lossesA[:, sc_index],
                lossesB=results.lossesB[:, sc_index],
                lossesC=results.lossesC[:, sc_index],
                br_active=br_active,
                hvdc_PfA=results.hvdc_Pf[:, sc_index],
                hvdc_PfB=results.hvdc_Pf[:, sc_index],
                hvdc_PfC=results.hvdc_Pf[:, sc_index],
                hvdc_PtA=results.hvdc_Pt[:, sc_index],
                hvdc_PtB=results.hvdc_Pt[:, sc_index],
                hvdc_PtC=results.hvdc_Pt[:, sc_index],
                hvdc_losses=results.hvdc_losses[:, sc_index],
                hvdc_loading=results.hvdc_loading[:, sc_index],
                hvdc_active=hvdc_active,
                vsc_Pf=results.vsc_Pfp[:, sc_index],
                vsc_PtA=results.vsc_St.real[:, sc_index],
                vsc_PtB=results.vsc_St.real[:, sc_index],
                vsc_PtC=results.vsc_St.real[:, sc_index],
                vsc_QtA=results.vsc_St.imag[:, sc_index],
                vsc_QtB=results.vsc_St.imag[:, sc_index],
                vsc_QtC=results.vsc_St.imag[:, sc_index],
                vsc_losses=results.vsc_losses[:, sc_index],
                vsc_loading=results.vsc_loading[:, sc_index],
                vsc_active=vsc_active,
                use_flow_based_width=use_flow_based_width,
                min_branch_width=min_branch_width,
                max_branch_width=max_branch_width,
                min_bus_width=min_bus_width,
                max_bus_width=max_bus_width,
                cmap=cmap,
            )

        else:
            return diagram_widget.colour_results(Sbus=results.Sbus1[:, sc_index],
                                                 bus_active=bus_active,
                                                 Sf=results.Sf1[:, sc_index],
                                                 St=results.St1[:, sc_index],
                                                 voltages=results.voltage1[:, sc_index],
                                                 types=results.bus_types,
                                                 loadings=results.loading1[:, sc_index],
                                                 br_active=br_active,
                                                 hvdc_Pf=None,
                                                 hvdc_Pt=None,
                                                 hvdc_losses=None,
                                                 hvdc_loading=None,
                                                 hvdc_active=hvdc_active,
                                                 vsc_Pf=results.vsc_Pfp[:, sc_index],
                                                 vsc_Pt=results.vsc_St.real[:, sc_index],
                                                 vsc_Qt=results.vsc_St.imag[:, sc_index],
                                                 vsc_losses=results.vsc_losses[:, sc_index],
                                                 vsc_loading=results.vsc_loading[:, sc_index],
                                                 vsc_active=vsc_active,
                                                 use_flow_based_width=use_flow_based_width,
                                                 min_branch_width=min_branch_width,
                                                 max_branch_width=max_branch_width,
                                                 min_bus_width=min_bus_width,
                                                 max_bus_width=max_bus_width,
                                                 cmap=cmap)

    def opf_colouring(self, diagram_widget: ALL_EDITORS,
                      results: sim.OptimalPowerFlowResults, cmap: Colormaps,
                      use_flow_based_width: bool = False,
                      min_branch_width: int = 2,
                      max_branch_width: int = 5,
                      min_bus_width: int = 2,
                      max_bus_width: int = 5):
        """

        :param diagram_widget:
        :param results:
        :param cmap:
        :param use_flow_based_width:
        :param min_branch_width:
        :param max_branch_width:
        :param min_bus_width:
        :param max_bus_width:
        :return:
        """
        bus_active = self.circuit.get_bus_actives(t_idx=None)
        br_active = self.circuit.get_branch_actives(t_idx=None, add_vsc=False, add_hvdc=False, add_switch=True)
        hvdc_active = self.circuit.get_hvdc_actives(t_idx=None)
        vsc_active = self.circuit.get_vsc_actives(t_idx=None)

        return diagram_widget.colour_results(Sbus=results.Sbus,
                                             voltages=results.voltage,
                                             bus_active=bus_active,
                                             loadings=results.loading,
                                             types=results.bus_types,

                                             Sf=results.Sf,
                                             St=results.St,
                                             br_active=br_active,

                                             hvdc_Pf=results.hvdc_Pf,
                                             hvdc_Pt=-results.hvdc_Pf,
                                             hvdc_loading=results.hvdc_loading,
                                             hvdc_active=hvdc_active,

                                             vsc_Pf=results.vsc_Pf,
                                             vsc_Pt=-results.vsc_Pf,
                                             vsc_Qt=np.zeros_like(results.vsc_Pf),
                                             vsc_loading=results.vsc_loading,
                                             vsc_active=vsc_active,

                                             fluid_node_p2x_flow=results.fluid_node_p2x_flow,
                                             fluid_node_current_level=results.fluid_node_current_level,
                                             fluid_node_spillage=results.fluid_node_spillage,
                                             fluid_node_flow_in=results.fluid_node_flow_in,
                                             fluid_node_flow_out=results.fluid_node_flow_out,
                                             fluid_path_flow=results.fluid_path_flow,
                                             fluid_injection_flow=results.fluid_injection_flow,
                                             use_flow_based_width=use_flow_based_width,
                                             min_branch_width=min_branch_width,
                                             max_branch_width=max_branch_width,
                                             min_bus_width=min_bus_width,
                                             max_bus_width=max_bus_width,
                                             cmap=cmap)

    def opf_ts_colouring(self, t_idx: int,
                         diagram_widget: ALL_EDITORS,
                         results: sim.OptimalPowerFlowTimeSeriesResults,
                         cmap: Colormaps,
                         use_flow_based_width: bool = False,
                         min_branch_width: int = 2,
                         max_branch_width: int = 5,
                         min_bus_width: int = 2,
                         max_bus_width: int = 5):
        """

        :param t_idx:
        :param diagram_widget:
        :param results:
        :param cmap:
        :param use_flow_based_width:
        :param min_branch_width:
        :param max_branch_width:
        :param min_bus_width:
        :param max_bus_width:
        :return:
        """
        bus_active = self.circuit.get_bus_actives(t_idx=t_idx)
        br_active = self.circuit.get_branch_actives(t_idx=t_idx, add_vsc=False, add_hvdc=False, add_switch=True)
        hvdc_active = self.circuit.get_hvdc_actives(t_idx=t_idx)
        vsc_active = self.circuit.get_vsc_actives(t_idx=t_idx)

        return diagram_widget.colour_results(voltages=results.voltage[t_idx, :],
                                             Sbus=results.Sbus[t_idx, :],
                                             types=results.bus_types,
                                             bus_active=bus_active,
                                             Sf=results.Sf[t_idx, :],
                                             St=results.St[t_idx, :],
                                             loadings=np.abs(results.loading[t_idx, :]),
                                             br_active=br_active,
                                             hvdc_Pf=results.hvdc_Pf[t_idx, :],
                                             hvdc_Pt=-results.hvdc_Pf[t_idx, :],
                                             hvdc_loading=results.hvdc_loading[t_idx, :],
                                             hvdc_active=hvdc_active,
                                             fluid_node_p2x_flow=results.fluid_node_p2x_flow[t_idx, :],
                                             fluid_node_current_level=results.fluid_node_current_level[t_idx, :],
                                             fluid_node_spillage=results.fluid_node_spillage[t_idx, :],
                                             fluid_node_flow_in=results.fluid_node_flow_in[t_idx, :],
                                             fluid_node_flow_out=results.fluid_node_flow_out[t_idx, :],
                                             fluid_path_flow=results.fluid_path_flow[t_idx, :],
                                             fluid_injection_flow=results.fluid_injection_flow[t_idx, :],
                                             use_flow_based_width=use_flow_based_width,
                                             min_branch_width=min_branch_width,
                                             max_branch_width=max_branch_width,
                                             min_bus_width=min_bus_width,
                                             max_bus_width=max_bus_width,
                                             cmap=cmap)

    def ntc_colouring(self, diagram_widget: ALL_EDITORS,
                      results: sim.OptimalNetTransferCapacityResults, cmap: Colormaps,
                      use_flow_based_width: bool = False,
                      min_branch_width: int = 2,
                      max_branch_width: int = 5,
                      min_bus_width: int = 2,
                      max_bus_width: int = 5):
        """

        :param diagram_widget:
        :param results:
        :param cmap:
        :param use_flow_based_width:
        :param min_branch_width:
        :param max_branch_width:
        :param min_bus_width:
        :param max_bus_width:
        :return:
        """
        bus_active = self.circuit.get_bus_actives(t_idx=None)
        br_active = self.circuit.get_branch_actives(t_idx=None, add_vsc=False, add_hvdc=False, add_switch=True)
        hvdc_active = self.circuit.get_hvdc_actives(t_idx=None)
        vsc_active = self.circuit.get_vsc_actives(t_idx=None)

        return diagram_widget.colour_results(Sbus=results.Sbus,
                                             voltages=results.voltage,
                                             bus_active=bus_active,
                                             loadings=results.loading,
                                             types=results.bus_types,

                                             Sf=results.Sf,
                                             St=results.St,
                                             br_active=br_active,

                                             hvdc_Pf=results.hvdc_Pf,
                                             hvdc_Pt=-results.hvdc_Pf,
                                             hvdc_loading=results.hvdc_loading,
                                             hvdc_active=hvdc_active,

                                             vsc_Pf=results.vsc_Pf,
                                             vsc_Pt=-results.vsc_Pf,
                                             vsc_loading=results.vsc_loading,
                                             vsc_active=vsc_active,

                                             use_flow_based_width=use_flow_based_width,
                                             min_branch_width=min_branch_width,
                                             max_branch_width=max_branch_width,
                                             min_bus_width=min_bus_width,
                                             max_bus_width=max_bus_width,
                                             cmap=cmap)

    def ntc_ts_colouring(self, t_idx: int,
                         diagram_widget: ALL_EDITORS,
                         results: sim.OptimalNetTransferCapacityTimeSeriesResults,
                         cmap: Colormaps,
                         use_flow_based_width: bool = False,
                         min_branch_width: int = 2,
                         max_branch_width: int = 5,
                         min_bus_width: int = 2,
                         max_bus_width: int = 5):
        """

        :param t_idx:
        :param diagram_widget:
        :param results:
        :param cmap:
        :param use_flow_based_width:
        :param min_branch_width:
        :param max_branch_width:
        :param min_bus_width:
        :param max_bus_width:
        :return:
        """
        bus_active = self.circuit.get_bus_actives(t_idx=t_idx)
        br_active = self.circuit.get_branch_actives(t_idx=t_idx, add_vsc=False, add_hvdc=False, add_switch=True)
        hvdc_active = self.circuit.get_hvdc_actives(t_idx=t_idx)
        vsc_active = self.circuit.get_vsc_actives(t_idx=t_idx)

        return diagram_widget.colour_results(voltages=results.voltage[t_idx, :],
                                             Sbus=results.Sbus[t_idx, :],
                                             types=np.ones(self.circuit.get_bus_number(), dtype=int),
                                             bus_active=bus_active,
                                             Sf=results.Sf[t_idx, :],
                                             St=results.St[t_idx, :],
                                             loadings=np.abs(results.loading[t_idx, :]),
                                             br_active=br_active,
                                             hvdc_Pf=results.hvdc_Pf[t_idx, :],
                                             hvdc_Pt=-results.hvdc_Pf[t_idx, :],
                                             hvdc_loading=results.hvdc_loading[t_idx, :],
                                             hvdc_active=hvdc_active,
                                             use_flow_based_width=use_flow_based_width,
                                             min_branch_width=min_branch_width,
                                             max_branch_width=max_branch_width,
                                             min_bus_width=min_bus_width,
                                             max_bus_width=max_bus_width,
                                             cmap=cmap)

    def nc_ts_colouring(self, t_idx: int | None,
                        diagram_widget: ALL_EDITORS,
                        results: sim.NodalCapacityTimeSeriesResults,
                        cmap: Colormaps,
                        use_flow_based_width: bool = False,
                        min_branch_width: int = 2,
                        max_branch_width: int = 5,
                        min_bus_width: int = 2,
                        max_bus_width: int = 5):
        """

        :param t_idx:
        :param diagram_widget:
        :param results:
        :param cmap:
        :param use_flow_based_width:
        :param min_branch_width:
        :param max_branch_width:
        :param min_bus_width:
        :param max_bus_width:
        :return:
        """
        t_idx2 = 0 if t_idx is None else t_idx
        bus_active = self.circuit.get_bus_actives(t_idx=t_idx)
        br_active = self.circuit.get_branch_actives(t_idx=t_idx, add_vsc=False, add_hvdc=False, add_switch=True)
        hvdc_active = self.circuit.get_hvdc_actives(t_idx=t_idx)
        vsc_active = self.circuit.get_vsc_actives(t_idx=t_idx)

        return diagram_widget.colour_results(voltages=results.voltage[t_idx2, :],
                                             Sbus=results.Sbus[t_idx2, :],
                                             types=results.bus_types,
                                             bus_active=bus_active,
                                             Sf=results.Sf[t_idx2, :],
                                             St=results.St[t_idx2, :],
                                             loadings=np.abs(results.loading[t_idx2, :]),
                                             br_active=br_active,
                                             hvdc_Pf=results.hvdc_Pf[t_idx2, :],
                                             hvdc_Pt=-results.hvdc_Pf[t_idx2, :],
                                             hvdc_loading=results.hvdc_loading[t_idx2, :],
                                             hvdc_active=hvdc_active,
                                             use_flow_based_width=use_flow_based_width,
                                             min_branch_width=min_branch_width,
                                             max_branch_width=max_branch_width,
                                             min_bus_width=min_bus_width,
                                             max_bus_width=max_bus_width,
                                             cmap=cmap)

    def linpf_colouring(self, diagram_widget: ALL_EDITORS,
                        results: sim.LinearAnalysisResults, cmap: Colormaps,
                        use_flow_based_width: bool = False,
                        min_branch_width: int = 2,
                        max_branch_width: int = 5,
                        min_bus_width: int = 2,
                        max_bus_width: int = 5):
        """

        :param diagram_widget:
        :param results:
        :param cmap:
        :param use_flow_based_width:
        :param min_branch_width:
        :param max_branch_width:
        :param min_bus_width:
        :param max_bus_width:
        :return:
        """
        bus_active = self.circuit.get_bus_actives(t_idx=None)
        br_active = self.circuit.get_branch_actives(t_idx=None, add_vsc=False, add_hvdc=False, add_switch=True)
        hvdc_active = self.circuit.get_hvdc_actives(t_idx=None)
        vsc_active = self.circuit.get_vsc_actives(t_idx=None)

        voltage = np.ones(self.circuit.get_bus_number(), dtype=complex)

        return diagram_widget.colour_results(voltages=voltage,
                                             Sbus=results.Sbus.astype(complex),
                                             types=results.bus_types.astype(int),
                                             bus_active=bus_active,
                                             Sf=results.Sf.astype(complex),
                                             St=-results.Sf.astype(complex),
                                             loadings=results.loading.astype(complex),
                                             br_active=br_active,
                                             hvdc_active=hvdc_active,
                                             loading_label='Loading',
                                             use_flow_based_width=use_flow_based_width,
                                             min_branch_width=min_branch_width,
                                             max_branch_width=max_branch_width,
                                             min_bus_width=min_bus_width,
                                             max_bus_width=max_bus_width,
                                             cmap=cmap)

    def linpf_ts_colouring(self, t_idx: int,
                           diagram_widget: ALL_EDITORS,
                           results: sim.LinearAnalysisTimeSeriesResults,
                           cmap: Colormaps,
                           use_flow_based_width: bool = False,
                           min_branch_width: int = 2,
                           max_branch_width: int = 5,
                           min_bus_width: int = 2,
                           max_bus_width: int = 5):
        """

        :param t_idx:
        :param diagram_widget:
        :param results:
        :param cmap:
        :param use_flow_based_width:
        :param min_branch_width:
        :param max_branch_width:
        :param min_bus_width:
        :param max_bus_width:
        :return:
        """
        bus_active = self.circuit.get_bus_actives(t_idx=t_idx)
        br_active = self.circuit.get_branch_actives(t_idx=t_idx, add_vsc=False, add_hvdc=False, add_switch=True)
        hvdc_active = self.circuit.get_hvdc_actives(t_idx=t_idx)
        vsc_active = self.circuit.get_vsc_actives(t_idx=t_idx)

        return diagram_widget.colour_results(Sbus=results.S[t_idx],
                                             voltages=results.voltage[t_idx],
                                             types=results.bus_types,
                                             bus_active=bus_active,
                                             Sf=results.Sf[t_idx],
                                             St=-results.Sf[t_idx],
                                             loadings=np.abs(results.loading[t_idx]),
                                             br_active=br_active,
                                             hvdc_active=hvdc_active,
                                             use_flow_based_width=use_flow_based_width,
                                             min_branch_width=min_branch_width,
                                             max_branch_width=max_branch_width,
                                             min_bus_width=min_bus_width,
                                             max_bus_width=max_bus_width,
                                             cmap=cmap)

    def con_colouring(self, diagram_widget: ALL_EDITORS,
                      results: sim.ContingencyAnalysisResults, cmap: Colormaps,
                      use_flow_based_width: bool = False,
                      min_branch_width: int = 2,
                      max_branch_width: int = 5,
                      min_bus_width: int = 2,
                      max_bus_width: int = 5):
        """

        :param diagram_widget:
        :param results:
        :param cmap:
        :param use_flow_based_width:
        :param min_branch_width:
        :param max_branch_width:
        :param min_bus_width:
        :param max_bus_width:
        :return:
        """
        bus_active = self.circuit.get_bus_actives(t_idx=None)
        br_active = self.circuit.get_branch_actives(t_idx=None, add_vsc=False, add_hvdc=False, add_switch=True)
        hvdc_active = self.circuit.get_hvdc_actives(t_idx=None)
        vsc_active = self.circuit.get_vsc_actives(t_idx=None)
        con_idx = 0
        return diagram_widget.colour_results(Sbus=results.Sbus[con_idx, :],
                                             voltages=results.voltage[con_idx, :],
                                             types=results.bus_types,
                                             bus_active=bus_active,
                                             Sf=results.Sf[con_idx, :],
                                             St=-results.Sf[con_idx, :],
                                             loadings=np.abs(results.loading[con_idx, :]),
                                             br_active=br_active,
                                             hvdc_active=hvdc_active,
                                             use_flow_based_width=use_flow_based_width,
                                             min_branch_width=min_branch_width,
                                             max_branch_width=max_branch_width,
                                             min_bus_width=min_bus_width,
                                             max_bus_width=max_bus_width,
                                             cmap=cmap)

    def con_ts_colouring(self, t_idx: int,
                         diagram_widget: ALL_EDITORS,
                         results: sim.ContingencyAnalysisTimeSeriesResults,
                         cmap: Colormaps,
                         use_flow_based_width: bool = False,
                         min_branch_width: int = 2,
                         max_branch_width: int = 5,
                         min_bus_width: int = 2,
                         max_bus_width: int = 5):
        """

        :param t_idx:
        :param diagram_widget:
        :param results:
        :param cmap:
        :param use_flow_based_width:
        :param min_branch_width:
        :param max_branch_width:
        :param min_bus_width:
        :param max_bus_width:
        :return:
        """
        bus_active = self.circuit.get_bus_actives(t_idx=t_idx)
        br_active = self.circuit.get_branch_actives(t_idx=t_idx, add_vsc=False, add_hvdc=False, add_switch=True)
        hvdc_active = self.circuit.get_hvdc_actives(t_idx=t_idx)
        vsc_active = self.circuit.get_vsc_actives(t_idx=t_idx)

        return diagram_widget.colour_results(voltages=np.ones(results.nbus, dtype=complex),
                                             Sbus=results.S[t_idx, :].astype(complex),
                                             types=results.bus_types,
                                             bus_active=bus_active,
                                             Sf=results.max_flows[t_idx, :].astype(complex),
                                             St=-results.max_flows[t_idx, :].astype(complex),
                                             loadings=results.max_loading[t_idx].astype(complex),
                                             br_active=br_active,
                                             hvdc_active=hvdc_active,
                                             use_flow_based_width=use_flow_based_width,
                                             min_branch_width=min_branch_width,
                                             max_branch_width=max_branch_width,
                                             min_bus_width=min_bus_width,
                                             max_bus_width=max_bus_width,
                                             cmap=cmap)

    def node_group_colouring(self,
                             results: sim.NodeGroupsResults,
                             diagram_widget: ALL_EDITORS):
        """

        :param results:
        :param diagram_widget:
        :return:
        """
        colours = viz.get_n_colours(n=len(results.groups_by_index))

        bus_graphics_dict = diagram_widget.graphics_manager.get_device_type_dict(DeviceType.BusDevice)
        for c, group in enumerate(results.groups_by_index):
            for i in group:
                bus = self.circuit.buses[i]
                bus_graphic: BusGraphicItem = bus_graphics_dict.get(bus.idtag, None)
                if bus_graphic is not None:
                    r, g, b, a = colours[c]
                    color = QtGui.QColor(r * 255, g * 255, b * 255, a * 255)
                    bus_graphic.set_tile_color(brush=color)
                    bus_graphic.setToolTip('Group ' + str(c))

    def default_colouring(self, t_idx: int | None,
                          diagram_widget: ALL_EDITORS,
                          cmap: Colormaps,
                          use_flow_based_width: bool = False,
                          min_branch_width: int = 2,
                          max_branch_width: int = 5,
                          min_bus_width: int = 2,
                          max_bus_width: int = 5):
        """

        :param t_idx:
        :param diagram_widget:
        :param cmap:
        :param use_flow_based_width:
        :param min_branch_width:
        :param max_branch_width:
        :param min_bus_width:
        :param max_bus_width:
        :return:
        """
        nbus = self.circuit.get_bus_number()
        nbr = self.circuit.get_branch_number(add_vsc=False, add_hvdc=False, add_switch=True)
        nhvdc = self.circuit.get_hvdc_number()
        nvsc = self.circuit.get_vsc_number()

        bus_active = self.circuit.get_bus_actives(t_idx=t_idx)
        br_active = self.circuit.get_branch_actives(t_idx=t_idx, add_vsc=False, add_hvdc=False, add_switch=True)
        hvdc_active = self.circuit.get_hvdc_actives(t_idx=t_idx)
        vsc_active = self.circuit.get_vsc_actives(t_idx=t_idx)

        return diagram_widget.colour_results(Sbus=np.zeros(nbus, dtype=complex),
                                             voltages=np.ones(nbus, dtype=complex),
                                             bus_active=bus_active,
                                             Sf=np.zeros(nbr, dtype=complex),
                                             St=np.zeros(nbr, dtype=complex),
                                             loadings=np.zeros(nbr, dtype=complex),
                                             br_active=br_active,
                                             hvdc_active=hvdc_active,
                                             hvdc_loading=np.zeros(nhvdc, dtype=float),
                                             hvdc_Pf=np.zeros(nhvdc, dtype=float),
                                             hvdc_Pt=np.zeros(nhvdc, dtype=float),
                                             vsc_active=vsc_active,
                                             vsc_loading=np.zeros(nvsc, dtype=float),
                                             vsc_Pf=np.zeros(nvsc, dtype=float),
                                             vsc_Pt=np.zeros(nvsc, dtype=float),
                                             vsc_Qt=np.zeros(nvsc, dtype=float),
                                             use_flow_based_width=use_flow_based_width,
                                             min_branch_width=min_branch_width,
                                             max_branch_width=max_branch_width,
                                             min_bus_width=min_bus_width,
                                             max_bus_width=max_bus_width,
                                             cmap=cmap)

    def grid_colour_function(self,
                             diagram_widget: ALL_EDITORS,
                             current_study: str,
                             t_idx: Union[None, int],
                             allow_popups: bool = True) -> None:
        """
        Colour the schematic or the map
        :param diagram_widget: Diagram where the plotting is made
        :param current_study: current_study name
        :param t_idx: current time step (if None, the snapshot is taken)
        :param allow_popups: if true, messages me pop up
        """
        use_flow_based_width = self.ui.branch_width_based_on_flow_checkBox.isChecked()
        min_branch_width = self.ui.min_branch_size_spinBox.value()
        max_branch_width = self.ui.max_branch_size_spinBox.value()
        min_bus_width = self.ui.min_node_size_spinBox.value()
        max_bus_width = self.ui.max_node_size_spinBox.value()

        cmap_text = self.ui.palette_comboBox.currentText()
        cmap = self.cmap_dict[cmap_text]

        if current_study == sim.PowerFlowDriver.tpe.value:
            if t_idx is None:
                results: sim.PowerFlowResults = self.session.get_results(SimulationTypes.PowerFlow_run)
                self.pf_colouring(diagram_widget=diagram_widget,
                                  results=results,
                                  cmap=cmap,
                                  use_flow_based_width=use_flow_based_width,
                                  min_branch_width=min_branch_width,
                                  max_branch_width=max_branch_width,
                                  min_bus_width=min_bus_width,
                                  max_bus_width=max_bus_width)

            else:
                if allow_popups:
                    self.show_warning_toast(f"{current_study} only has values for the snapshot")

        elif current_study == sim.PowerFlowDriver3Ph.tpe.value:
            if t_idx is None:
                results: sim.PowerFlowResults3Ph = self.session.get_results(SimulationTypes.PowerFlow3ph_run)
                self.pf_3ph_colouring(diagram_widget=diagram_widget,
                                      results=results,
                                      cmap=cmap,
                                      use_flow_based_width=use_flow_based_width,
                                      min_branch_width=min_branch_width,
                                      max_branch_width=max_branch_width,
                                      min_bus_width=min_bus_width,
                                      max_bus_width=max_bus_width)

            else:
                if allow_popups:
                    self.show_warning_toast(f"{current_study} only has values for the snapshot")

        elif current_study == sim.PowerFlowTimeSeriesDriver.tpe.value:
            if t_idx is not None:
                drv, results = self.session.power_flow_ts
                self.pf_ts_colouring(t_idx=t_idx,
                                     diagram_widget=diagram_widget,
                                     results=results,
                                     cmap=cmap,
                                     use_flow_based_width=use_flow_based_width,
                                     min_branch_width=min_branch_width,
                                     max_branch_width=max_branch_width,
                                     min_bus_width=min_bus_width,
                                     max_bus_width=max_bus_width)

            else:
                if allow_popups:
                    self.show_warning_toast(f"{current_study} does not have values for the snapshot")

        elif current_study == sim.StateEstimationDriver.tpe.value:
            if t_idx is None:
                results: sim.StateEstimationResults = self.session.get_results(SimulationTypes.StateEstimation_run)
                self.se_colouring(diagram_widget=diagram_widget,
                                  results=results,
                                  cmap=cmap,
                                  use_flow_based_width=use_flow_based_width,
                                  min_branch_width=min_branch_width,
                                  max_branch_width=max_branch_width,
                                  min_bus_width=min_bus_width,
                                  max_bus_width=max_bus_width)

            else:
                if allow_popups:
                    self.show_warning_toast(f"{current_study} only has values for the snapshot")

        elif current_study == sim.ContinuationPowerFlowDriver.tpe.value:
            if t_idx is None:
                results: sim.ContinuationPowerFlowResults = self.session.get_results(
                    SimulationTypes.ContinuationPowerFlow_run
                )
                self.cpf_colouring(diagram_widget=diagram_widget,
                                   results=results,
                                   cmap=cmap,
                                   use_flow_based_width=use_flow_based_width,
                                   min_branch_width=min_branch_width,
                                   max_branch_width=max_branch_width,
                                   min_bus_width=min_bus_width,
                                   max_bus_width=max_bus_width)
            else:
                if allow_popups:
                    self.show_warning_toast(f"{current_study} only has values for the snapshot")

        elif current_study == sim.StochasticPowerFlowDriver.tpe.value:

            # the time is not relevant in this study
            results: sim.StochasticPowerFlowResults = self.session.get_results(
                SimulationTypes.StochasticPowerFlow
            )
            self.spf_colouring(diagram_widget=diagram_widget,
                               results=results,
                               cmap=cmap,
                               use_flow_based_width=use_flow_based_width,
                               min_branch_width=min_branch_width,
                               max_branch_width=max_branch_width,
                               min_bus_width=min_bus_width,
                               max_bus_width=max_bus_width)

        elif current_study == sim.ShortCircuitDriver.tpe.value:
            if t_idx is None:
                results: sim.ShortCircuitResults = self.session.get_results(SimulationTypes.ShortCircuit_run)
                self.sc_colouring(diagram_widget=diagram_widget,
                                  results=results,
                                  cmap=cmap,
                                  use_flow_based_width=use_flow_based_width,
                                  min_branch_width=min_branch_width,
                                  max_branch_width=max_branch_width,
                                  min_bus_width=min_bus_width,
                                  max_bus_width=max_bus_width)
            else:
                if allow_popups:
                    self.show_warning_toast(f"{current_study} only has values for the snapshot")

        elif current_study == sim.OptimalPowerFlowDriver.tpe.value:
            if t_idx is None:
                results: sim.OptimalPowerFlowResults = self.session.get_results(SimulationTypes.OPF_run)
                self.opf_colouring(diagram_widget=diagram_widget,
                                   results=results,
                                   cmap=cmap,
                                   use_flow_based_width=use_flow_based_width,
                                   min_branch_width=min_branch_width,
                                   max_branch_width=max_branch_width,
                                   min_bus_width=min_bus_width,
                                   max_bus_width=max_bus_width)
            else:
                if allow_popups:
                    self.show_warning_toast(f"{current_study} only has values for the snapshot")

        elif current_study == sim.OptimalPowerFlowTimeSeriesDriver.tpe.value:

            if t_idx is not None:
                results: sim.OptimalPowerFlowTimeSeriesResults = self.session.get_results(
                    SimulationTypes.OPFTimeSeries_run
                )
                self.opf_ts_colouring(t_idx=t_idx,
                                      diagram_widget=diagram_widget,
                                      results=results,
                                      cmap=cmap,
                                      use_flow_based_width=use_flow_based_width,
                                      min_branch_width=min_branch_width,
                                      max_branch_width=max_branch_width,
                                      min_bus_width=min_bus_width,
                                      max_bus_width=max_bus_width)
            else:
                if allow_popups:
                    self.show_warning_toast(f"{current_study} does not have values for the snapshot")

        elif current_study == sim.NodalCapacityTimeSeriesDriver.tpe.value:

            _, results = self.session.nodal_capacity_optimization_ts
            self.nc_ts_colouring(t_idx=t_idx,
                                 diagram_widget=diagram_widget,
                                 results=results,
                                 cmap=cmap,
                                 use_flow_based_width=use_flow_based_width,
                                 min_branch_width=min_branch_width,
                                 max_branch_width=max_branch_width,
                                 min_bus_width=min_bus_width,
                                 max_bus_width=max_bus_width)

        elif current_study == sim.LinearAnalysisDriver.tpe.value:
            if t_idx is None:
                results: sim.LinearAnalysisResults = self.session.get_results(SimulationTypes.LinearAnalysis_run)
                self.linpf_colouring(diagram_widget=diagram_widget,
                                     results=results,
                                     cmap=cmap,
                                     use_flow_based_width=use_flow_based_width,
                                     min_branch_width=min_branch_width,
                                     max_branch_width=max_branch_width,
                                     min_bus_width=min_bus_width,
                                     max_bus_width=max_bus_width)
            else:
                if allow_popups:
                    self.show_warning_toast(f"{current_study} only has values for the snapshot")

        elif current_study == sim.LinearAnalysisTimeSeriesDriver.tpe.value:
            if t_idx is not None:
                results: sim.LinearAnalysisTimeSeriesResults = self.session.get_results(
                    SimulationTypes.LinearAnalysis_TS_run
                )
                self.linpf_ts_colouring(t_idx=t_idx,
                                        diagram_widget=diagram_widget,
                                        results=results,
                                        cmap=cmap,
                                        use_flow_based_width=use_flow_based_width,
                                        min_branch_width=min_branch_width,
                                        max_branch_width=max_branch_width,
                                        min_bus_width=min_bus_width,
                                        max_bus_width=max_bus_width)
            else:
                if allow_popups:
                    self.show_warning_toast(f"{current_study} does not have values for the snapshot")

        elif current_study == sim.ContingencyAnalysisDriver.tpe.value:

            if t_idx is None:
                results: sim.ContingencyAnalysisResults = self.session.get_results(
                    SimulationTypes.ContingencyAnalysis_run
                )
                self.con_colouring(diagram_widget=diagram_widget,
                                   results=results,
                                   cmap=cmap,
                                   use_flow_based_width=use_flow_based_width,
                                   min_branch_width=min_branch_width,
                                   max_branch_width=max_branch_width,
                                   min_bus_width=min_bus_width,
                                   max_bus_width=max_bus_width)

            else:
                if allow_popups:
                    self.show_warning_toast(f"{current_study} only has values for the snapshot")

        elif current_study == sim.ContingencyAnalysisTimeSeriesDriver.tpe.value:
            if t_idx is not None:
                results: sim.ContingencyAnalysisTimeSeriesResults = self.session.get_results(
                    SimulationTypes.ContingencyAnalysisTS_run
                )
                self.con_ts_colouring(t_idx=t_idx,
                                      diagram_widget=diagram_widget,
                                      results=results,
                                      cmap=cmap,
                                      use_flow_based_width=use_flow_based_width,
                                      min_branch_width=min_branch_width,
                                      max_branch_width=max_branch_width,
                                      min_bus_width=min_bus_width,
                                      max_bus_width=max_bus_width)
            else:
                if allow_popups:
                    self.show_warning_toast(f"{current_study} does not have values for the snapshot")

        elif current_study == sim.AvailableTransferCapacityDriver.tpe.value:
            self.default_colouring(t_idx=t_idx,
                                   diagram_widget=diagram_widget,
                                   cmap=cmap,
                                   use_flow_based_width=use_flow_based_width,
                                   min_branch_width=min_branch_width,
                                   max_branch_width=max_branch_width,
                                   min_bus_width=min_bus_width,
                                   max_bus_width=max_bus_width)

        elif current_study == sim.AvailableTransferCapacityTimeSeriesDriver.tpe.value:
            self.default_colouring(t_idx=t_idx,
                                   diagram_widget=diagram_widget,
                                   cmap=cmap,
                                   use_flow_based_width=use_flow_based_width,
                                   min_branch_width=min_branch_width,
                                   max_branch_width=max_branch_width,
                                   min_bus_width=min_bus_width,
                                   max_bus_width=max_bus_width)

        elif current_study == sim.OptimalNetTransferCapacityDriver.tpe.value:
            if t_idx is None:
                results: sim.OptimalNetTransferCapacityResults = self.session.get_results(
                    SimulationTypes.OPF_NTC_run
                )
                self.ntc_colouring(diagram_widget=diagram_widget,
                                   results=results,
                                   cmap=cmap,
                                   use_flow_based_width=use_flow_based_width,
                                   min_branch_width=min_branch_width,
                                   max_branch_width=max_branch_width,
                                   min_bus_width=min_bus_width,
                                   max_bus_width=max_bus_width)
            else:
                if allow_popups:
                    self.show_warning_toast(f"{current_study} only has values for the snapshot")

        elif current_study == sim.OptimalNetTransferCapacityTimeSeriesDriver.tpe.value:
            if t_idx is not None:
                results: sim.OptimalNetTransferCapacityTimeSeriesResults = self.session.get_results(
                    SimulationTypes.OPF_NTC_TS_run
                )
                self.ntc_ts_colouring(t_idx=t_idx,
                                      diagram_widget=diagram_widget,
                                      results=results,
                                      cmap=cmap,
                                      use_flow_based_width=use_flow_based_width,
                                      min_branch_width=min_branch_width,
                                      max_branch_width=max_branch_width,
                                      min_bus_width=min_bus_width,
                                      max_bus_width=max_bus_width)
            else:
                if allow_popups:
                    self.show_warning_toast(f"{current_study} does not have values for the snapshot")

        elif current_study == sim.InputsAnalysisDriver.tpe.value:

            self.default_colouring(t_idx=t_idx,
                                   diagram_widget=diagram_widget,
                                   cmap=cmap,
                                   use_flow_based_width=use_flow_based_width,
                                   min_branch_width=min_branch_width,
                                   max_branch_width=max_branch_width,
                                   min_bus_width=min_bus_width,
                                   max_bus_width=max_bus_width)

        elif current_study == SimulationTypes.DesignView.value:

            self.default_colouring(t_idx=t_idx,
                                   diagram_widget=diagram_widget,
                                   cmap=cmap,
                                   use_flow_based_width=use_flow_based_width,
                                   min_branch_width=min_branch_width,
                                   max_branch_width=max_branch_width,
                                   min_bus_width=min_bus_width,
                                   max_bus_width=max_bus_width)

        elif current_study == SimulationTypes.NodeGrouping_run.value:
            if t_idx is None:
                results: sim.OptimalNetTransferCapacityResults = self.session.get_results(
                    SimulationTypes.NodeGrouping_run
                )
                self.node_group_colouring(diagram_widget=diagram_widget,
                                          results=results)
            else:
                if allow_popups:
                    self.show_warning_toast(f"{current_study} only has values for the snapshot")

        elif current_study == 'Transient stability':
            raise Exception('Not implemented :(')

        else:
            print('grid_colour_function: <' + current_study + '> Not implemented :(')

    def colour_diagrams(self, allow_popups: bool = True) -> None:
        """
        Color the grid now
        :param allow_popups:
        """
        if self.ui.available_results_to_color_comboBox.currentIndex() > -1:

            current_study = self.ui.available_results_to_color_comboBox.currentText()

            offset = self.ui.diagram_step_slider.minimum()
            if offset == -1:
                offset = 0
            val = self.ui.diagram_step_slider.value() - offset

            t_idx = val if val > -1 else None

            for diagram in self.diagram_widgets_list:

                if isinstance(diagram, (SchematicWidget, GridMapWidget)):
                    self.grid_colour_function(diagram_widget=diagram,
                                              current_study=current_study,
                                              t_idx=t_idx,
                                              allow_popups=allow_popups)

    def re_colour_schematic(self):
        """
        Recolour a schematic
        """
        diagram_widget = self.get_selected_diagram_widget()

        use_api_color = self.ui.use_schematic_objects_color_checkBox.isChecked()

        if diagram_widget:

            if isinstance(diagram_widget, SchematicWidget):
                diagram_widget.recolour(use_api_color=use_api_color)

    def set_diagrams_list_view(self) -> None:
        """
        Create the diagrams' list view
        """
        mdl = DiagramsModel(self.diagram_widgets_list)
        self.ui.diagramsListView.setModel(mdl)

    def _create_widget_from_diagram(self, diagram: dev.SchematicDiagram | dev.MapDiagram) -> ALL_EDITORS:
        """
        Create a diagram widget from a stored diagram object.

        :param diagram: stored diagram
        :return: materialized diagram widget
        """
        if isinstance(diagram, dev.SchematicDiagram):
            diagram_widget = SchematicWidget(
                gui=self,
                diagram=diagram,
                default_bus_voltage=self.ui.defaultBusVoltageSpinBox.value(),
                time_index=self.get_diagram_slider_index()
            )
            diagram_widget.setStretchFactor(1, 10)
            diagram_widget.center_nodes()
            return diagram_widget
        elif isinstance(diagram, dev.MapDiagram):
            default_tile_source = self.tile_name_dict[self.ui.tile_provider_comboBox.currentText()]
            tile_source = self.tile_name_dict.get(diagram.tile_source, default_tile_source)
            return GridMapWidget(
                gui=self,
                tile_src=tile_source,
                start_level=diagram.start_level,
                longitude=diagram.longitude,
                latitude=diagram.latitude,
                name=diagram.name,
                diagram=diagram
            )
        else:
            raise Exception("Unknown diagram type")

    def _ensure_diagram_widget_at_index(self, index: int) -> ALL_EDITORS_NONE:
        """
        Materialize and cache a diagram widget if the entry is still deferred.

        :param index: diagram row index
        :return: diagram widget or None
        """
        if index < 0 or index >= len(self.diagram_widgets_list):
            return None
        else:
            pass

        entry = self.diagram_widgets_list[index]
        if isinstance(entry, (SchematicWidget, GridMapWidget)):
            return entry
        elif isinstance(entry, (dev.SchematicDiagram, dev.MapDiagram)):
            widget = self._create_widget_from_diagram(diagram=entry)
            self.diagram_widgets_list[index] = widget

            mdl = self.ui.diagramsListView.model()
            if mdl is not None:
                idx = mdl.index(index, 0)
                mdl.dataChanged.emit(idx, idx, [QtCore.Qt.ItemDataRole.DisplayRole,
                                                QtCore.Qt.ItemDataRole.DecorationRole])
            else:
                pass

            return widget
        else:
            return None

    def get_selected_diagram_widget(self) -> ALL_EDITORS_NONE:
        """
        Get the currently selected diagram
        :return: None, DiagramEditorWidget, GridMapWidget, BusViewerGUI
        """
        indices = self.ui.diagramsListView.selectedIndexes()

        if len(indices):
            idx = indices[0].row()
            return self._ensure_diagram_widget_at_index(index=idx)
        else:
            return None

    def create_blank_schematic_diagram(self, name: str = "") -> SchematicWidget:
        """
        Create a new schematic widget
        :param name: name of the new schematic
        :return:
        """
        diagram = SchematicDiagram(name=name)

        diagram_widget = SchematicWidget(
            gui=self,
            diagram=diagram,
            default_bus_voltage=self.ui.defaultBusVoltageSpinBox.value(),
            time_index=self.get_diagram_slider_index()
        )

        diagram_widget.setStretchFactor(1, 10)
        diagram_widget.center_nodes()
        self.add_diagram_widget_and_diagram(diagram_widget=diagram_widget, diagram=diagram)
        self.set_diagrams_list_view()
        self.set_diagram_widget(diagram_widget)

        return diagram_widget

    def redraw_current_diagram(self):
        """
        Redraw the currently selected diagram
        """
        diagram_widget = self.get_selected_diagram_widget()

        if diagram_widget:

            if isinstance(diagram_widget, SchematicWidget):
                # set pointer to the circuit
                diagram = generate_schematic_diagram(buses=self.circuit.get_buses(),
                                                     lines=self.circuit.get_lines(),
                                                     dc_lines=self.circuit.get_dc_lines(),
                                                     transformers2w=self.circuit.get_transformers2w(),
                                                     transformers3w=self.circuit.get_transformers3w(),
                                                     transformers_nw=self.circuit.get_transformers_nw(),
                                                     windings=self.circuit.get_windings(),
                                                     hvdc_lines=self.circuit.get_hvdc(),
                                                     vsc_devices=self.circuit.get_vsc(),
                                                     upfc_devices=self.circuit.get_upfc(),
                                                     series_reactances=self.circuit.get_series_reactances(),
                                                     switches=self.circuit.get_switches(),
                                                     fluid_nodes=self.circuit.get_fluid_nodes(),
                                                     fluid_paths=self.circuit.get_fluid_paths(),
                                                     explode_factor=1.0,
                                                     prog_func=None,
                                                     text_func=None)

                diagram_widget.set_data(diagram=diagram)

            elif isinstance(diagram_widget, GridMapWidget):
                diagram_widget.update_device_sizes(asynchronously=False)

    def set_selected_diagram_on_click(self):
        """
        on list-view click, set the currently selected diagram widget
        """
        diagram = self.get_selected_diagram_widget()

        if diagram:
            self.set_diagram_widget(diagram)

    def add_complete_bus_branch_diagram_now(self, name='All bus branches') -> SchematicWidget:
        """
        Add a general bus-branch diagram
        :param name: Name of the diagram
        :return DiagramEditorWidget
        """
        diagram = generate_schematic_diagram(buses=self.circuit.get_buses(),
                                             lines=self.circuit.get_lines(),
                                             dc_lines=self.circuit.get_dc_lines(),
                                             transformers2w=self.circuit.get_transformers2w(),
                                             transformers3w=self.circuit.get_transformers3w(),
                                             transformers_nw=self.circuit.get_transformers_nw(),
                                             windings=self.circuit.get_windings(),
                                             hvdc_lines=self.circuit.get_hvdc(),
                                             vsc_devices=self.circuit.get_vsc(),
                                             upfc_devices=self.circuit.get_upfc(),
                                             series_reactances=self.circuit.get_series_reactances(),
                                             switches=self.circuit.get_switches(),
                                             fluid_nodes=self.circuit.get_fluid_nodes(),
                                             fluid_paths=self.circuit.get_fluid_paths(),
                                             explode_factor=1.0,
                                             prog_func=None,
                                             text_func=None,
                                             name=name)

        diagram_widget = SchematicWidget(
            gui=self,
            diagram=diagram,
            default_bus_voltage=self.ui.defaultBusVoltageSpinBox.value(),
            time_index=self.get_diagram_slider_index()
        )

        diagram_widget.setStretchFactor(1, 10)
        diagram_widget.center_nodes()
        self.add_diagram_widget_and_diagram(diagram_widget=diagram_widget, diagram=diagram)
        self.set_diagrams_list_view()
        self.set_diagram_widget(diagram_widget)

        return diagram_widget

    def add_complete_bus_branch_diagram(self) -> None:
        """
        Add a general bus-branch diagram
        """
        self.add_complete_bus_branch_diagram_now(name='All bus-branch')

    def new_bus_branch_diagram_from_selection(self):
        """
        Add a bus-branch diagram of a particular selection of objects
        """
        widget = self.get_selected_diagram_widget()

        if widget:

            if isinstance(widget, SchematicWidget):
                diagram = widget.create_schematic_from_selection()

                widget = SchematicWidget(
                    gui=self,
                    diagram=diagram,
                    default_bus_voltage=self.ui.defaultBusVoltageSpinBox.value(),
                    time_index=self.get_diagram_slider_index()
                )

                self.add_diagram_widget_and_diagram(diagram_widget=widget, diagram=diagram)
                self.set_diagrams_list_view()

            elif isinstance(widget, GridMapWidget):
                substation_graphics = widget.get_selected_substations()

                substations = list()
                for graphic_obj in substation_graphics:
                    substations.append(graphic_obj.api_object)

                self.new_bus_branch_diagram_from_substation(substations=substations)

    def add_bus_vicinity_diagram_from_model(self):
        """
        Add a bus vicinity diagram
        :return:
        """
        sel = self.get_selected_db_table_objects()

        if len(sel) > 0:

            sel_obj = sel[0]

            if isinstance(sel_obj, dev.Bus):
                root_bus = sel_obj

            elif isinstance(sel_obj, InjectionParent):
                root_bus = sel_obj.bus

            elif isinstance(sel_obj, BranchParent):
                root_bus = sel_obj.bus_from

            elif isinstance(sel_obj, dev.Transformer3W):
                root_bus = sel_obj.bus0

            elif isinstance(sel_obj, dev.TransformerNW):
                root_bus = sel_obj.bus0

            elif isinstance(sel_obj, dev.VoltageLevel):
                root_bus = None
                buses = self.circuit.get_voltage_level_buses(vl=sel_obj)
                if len(buses) > 0:
                    root_bus = buses[0]

            elif isinstance(sel_obj, dev.Substation):
                root_bus = None
                buses = self.circuit.get_substation_buses(substation=sel_obj)
                if len(buses) > 0:
                    root_bus = buses[0]

            else:
                root_bus = None

            if root_bus is not None:

                dlg = InputNumberDialogue(min_value=1, max_value=99,
                                          default_value=1, is_int=True,
                                          title='Vicinity diagram',
                                          text='Select the expansion level')

                if dlg.exec():
                    diagram = make_vicinity_diagram(circuit=self.circuit,
                                                    root_bus=root_bus,
                                                    max_level=dlg.value)

                    diagram_widget = SchematicWidget(
                        gui=self,
                        diagram=diagram,
                        default_bus_voltage=self.ui.defaultBusVoltageSpinBox.value(),
                        time_index=self.get_diagram_slider_index()
                    )

                    self.add_diagram_widget_and_diagram(diagram_widget=diagram_widget,
                                                        diagram=diagram)
                    self.set_diagrams_list_view()

                    self.show_info_toast(f"{diagram.name} added")
            else:
                self.show_error_toast(f"Could not find any bus")
        else:
            self.show_warning_toast(f"Select a bus")

    def new_bus_branch_diagram_from_bus(self, root_bus: dev.Bus):
        """
        Add a bus-branch diagram of a particular selection of objects
        """
        dlg = InputNumberDialogue(min_value=1, max_value=99,
                                  default_value=1, is_int=True,
                                  title='Vicinity diagram',
                                  text=f'Set the expansion level from {root_bus.name}')

        if dlg.exec():
            diagram = make_vicinity_diagram(circuit=self.circuit,
                                            root_bus=root_bus,
                                            max_level=dlg.value)

            diagram_widget = SchematicWidget(
                gui=self,
                diagram=diagram,
                default_bus_voltage=self.ui.defaultBusVoltageSpinBox.value(),
                time_index=self.get_diagram_slider_index()
            )

            self.add_diagram_widget_and_diagram(diagram_widget=diagram_widget, diagram=diagram)
            self.set_diagrams_list_view()
            self.show_info_toast(f"{diagram.name} added")

    def new_bus_branch_diagram_from_substation(self, substations: List[dev.Substation]):
        """
        Add a bus-branch diagram of a particular selection of objects
        """

        if len(substations) == 0:
            info_msg(text="No substations selected. Please select some substations",
                     title="Substations schematic")
            return

        selected_buses = self.circuit.get_buses_from_objects(elements=substations,
                                                             dtype=DeviceType.SubstationDevice)

        if len(selected_buses):
            diagram = make_diagram_from_buses(circuit=self.circuit,
                                              buses=selected_buses,
                                              name=substations[0].name + " diagram")

            diagram_widget = SchematicWidget(
                gui=self,
                diagram=diagram,
                default_bus_voltage=self.ui.defaultBusVoltageSpinBox.value(),
                time_index=self.get_diagram_slider_index()
            )

            self.add_diagram_widget_and_diagram(diagram_widget=diagram_widget,
                                                diagram=diagram)
            self.set_diagrams_list_view()

            self.show_info_toast(f"{diagram.name} added")
        else:
            if len(substations) == 1:
                info_msg(text=f"No buses were found associated with the substation {substations[0].name}",
                         title="New schematic from substation")
            else:
                info_msg(text=f"No buses were found associated with the substations",
                         title="New schematic from substation")

    def add_substation_to_current_diagram(self, substations: List[dev.Substation]):
        """
        Add a bus-branch diagram of a particular selection of objects
        """

        if len(substations) == 0:
            info_msg(text="No substations selected. Please select some substations",
                     title="Substations schematic")
            return

        diagram_widget = self.get_selected_diagram_widget()
        if not isinstance(diagram_widget, SchematicWidget):
            self.show_error_toast("The current diagram is not a schematic :(")
            return

        selected_buses = self.circuit.get_buses_from_objects(elements=substations,
                                                             dtype=DeviceType.SubstationDevice)

        if len(selected_buses):
            diagram_widget.add_buses(selected_buses)

            self.show_info_toast(f"Substation added")
        else:
            if len(substations) == 1:
                info_msg(text=f"No buses were found associated with the substation {substations[0].name}",
                         title="New schematic from substation")
            else:
                info_msg(text=f"No buses were found associated with the substations",
                         title="New schematic from substation")

    def create_circuit_stored_diagrams(self):
        """
        Create as Widgets the diagrams stored in the circuit
        :return:
        """
        self.diagram_widgets_list.clear()
        self.remove_all_diagram_widgets()

        for i, diagram in enumerate(self.circuit.diagrams):
            if i == 0:
                self.diagram_widgets_list.append(self._create_widget_from_diagram(diagram=diagram))
            else:
                # Defer heavy widget instantiation until the user selects the diagram.
                self.diagram_widgets_list.append(diagram)

        self.set_diagrams_list_view()

        if len(self.diagram_widgets_list) > 0:
            first_diagram = self._ensure_diagram_widget_at_index(index=0)
            if first_diagram is not None:
                self.set_diagram_widget(first_diagram)

    def add_map_diagram(self) -> None:
        """
        Adds a Map diagram
        """

        tpes = [
            DeviceType.SubstationDevice,
            DeviceType.LineDevice,
            DeviceType.DCLineDevice,
            DeviceType.HVDCLineDevice,
            DeviceType.GeneratorDevice,
            DeviceType.BatteryDevice,
            DeviceType.LoadDevice,
            DeviceType.StaticGeneratorDevice,
            DeviceType.ExternalGridDevice
        ]

        cmap_text = self.ui.palette_comboBox.currentText()
        cmap = self.cmap_dict[cmap_text]

        if self.circuit.get_substation_number() > 0:
            # showing this menu only makes sense if there is anything there

            self.new_se_dlg = CheckListDialogue(
                objects_list=[e.value for e in tpes]
            )

            self.new_se_dlg.exec()

            diagram = generate_map_diagram(
                substations=self.circuit.get_substations() if self.new_se_dlg.selected(
                    DeviceType.SubstationDevice.value) else list(),
                voltage_levels=self.circuit.get_voltage_levels() if self.new_se_dlg.selected(
                    DeviceType.SubstationDevice.value) else list(),
                lines=self.circuit.get_lines() if self.new_se_dlg.selected(DeviceType.LineDevice.value) else list(),
                dc_lines=self.circuit.get_dc_lines() if self.new_se_dlg.selected(
                    DeviceType.DCLineDevice.value) else list(),
                hvdc_lines=self.circuit.get_hvdc() if self.new_se_dlg.selected(
                    DeviceType.HVDCLineDevice.value) else list(),
                fluid_nodes=self.circuit.get_fluid_nodes(),
                fluid_paths=self.circuit.get_fluid_paths(),
                external_grids=self.circuit.external_grids if self.new_se_dlg.selected(
                    DeviceType.ExternalGridDevice.value) else list(),
                static_generators=self.circuit.static_generators if self.new_se_dlg.selected(
                    DeviceType.StaticGeneratorDevice.value) else list(),
                loads=self.circuit.loads if self.new_se_dlg.selected(DeviceType.LoadDevice.value) else list(),
                batteries=self.circuit.batteries if self.new_se_dlg.selected(
                    DeviceType.BatteryDevice.value) else list(),
                generators=self.circuit.generators if self.new_se_dlg.selected(
                    DeviceType.GeneratorDevice.value) else list(),
                prog_func=None,
                text_func=None,
                name='Map diagram',
                use_flow_based_width=self.ui.branch_width_based_on_flow_checkBox.isChecked(),
                min_branch_width=self.ui.min_branch_size_spinBox.value(),
                max_branch_width=self.ui.max_branch_size_spinBox.value(),
                min_bus_width=self.ui.min_node_size_spinBox.value(),
                max_bus_width=self.ui.max_node_size_spinBox.value(),
                arrow_size=self.ui.arrow_size_size_spinBox.value(),
                palette=cmap,
                default_bus_voltage=self.ui.defaultBusVoltageSpinBox.value()
            )
        else:
            # self.show_warning_toast("No substations to draw...")
            diagram = MapDiagram(name='Map diagram')

        # set other default properties of the diagram
        diagram.tile_source = self.ui.tile_provider_comboBox.currentText()
        diagram.start_level = 5

        # select the tile source
        tile_source = self.tile_name_dict[self.ui.tile_provider_comboBox.currentText()]

        # create the map widget
        map_widget = GridMapWidget(gui=self,
                                   tile_src=tile_source,
                                   start_level=diagram.start_level,
                                   longitude=diagram.longitude,
                                   latitude=diagram.latitude,
                                   name=diagram.name,
                                   diagram=diagram)

        self.add_diagram_widget_and_diagram(diagram_widget=map_widget, diagram=diagram)
        self.set_diagrams_list_view()
        self.set_diagram_widget(widget=map_widget)
        self.show_info_toast(f"{diagram.name} added")

    def add_diagram_widget_and_diagram(self,
                                       diagram_widget: ALL_EDITORS,
                                       diagram: Union[dev.SchematicDiagram, dev.MapDiagram]):
        """
        Add diagram widget, it also adds the diagram to the circuit for later
        :param diagram_widget: Diagram widget object
        :param diagram: SchematicDiagram or MapDiagram
        """

        # add the widget pointer
        self.diagram_widgets_list.append(diagram_widget)

        # add the diagram to the circuit
        self.circuit.add_diagram(diagram)

    def remove_diagram(self):
        """
        Remove one or more selected diagrams
        """
        selected_rows = sorted({idx.row() for idx in self.ui.diagramsListView.selectedIndexes()})
        if len(selected_rows) == 0:
            return

        if len(selected_rows) == 1:
            entry: SchematicWidget | GridMapWidget = self.diagram_widgets_list[selected_rows[0]]

            question = "Are you sure that you want to delete " + str(entry.name) + "?"
        else:
            question = f"Are you sure that you want to delete {len(selected_rows)} selected diagrams?"

        ok = yes_no_question(question, "Remove diagram")
        if not ok:
            return

        # Remember a candidate row to select after deletion.
        next_row = selected_rows[0]

        # Delete from highest row to lowest to avoid index shifts.
        for row in sorted(selected_rows, reverse=True):
            widget = self.diagram_widgets_list.pop(row)
            if isinstance(widget, (SchematicWidget, GridMapWidget)):
                self.circuit.remove_diagram(widget.diagram)

        # Remove currently shown widget and rebuild list view selection.
        self.remove_all_diagram_widgets()
        self.set_diagrams_list_view()

        if len(self.diagram_widgets_list) > 0:
            target_row = min(next_row, len(self.diagram_widgets_list) - 1)
            widget = self._ensure_diagram_widget_at_index(index=target_row)
            if widget is not None:
                self.set_diagram_widget(widget)
        else:
            pass

    def duplicate_diagram(self):
        """
        Duplicate the selected diagram
        """
        diagram_widget = self.get_selected_diagram_widget()
        if diagram_widget is not None:

            new_diagram_widget = diagram_widget.copy()

            self.add_diagram_widget_and_diagram(diagram_widget=new_diagram_widget,
                                                diagram=new_diagram_widget.diagram)

            # refresh the list view
            self.set_diagrams_list_view()
        else:
            info_msg(text="Select a valid diagram", title="Duplicate diagram")

    def remove_all_diagrams(self) -> None:
        """
        Remove all diagrams and their widgets
        """
        self.diagram_widgets_list.clear()
        self.remove_all_diagram_widgets()
        self.ui.diagramsListView.setModel(None)

    def remove_all_diagram_widgets(self) -> None:
        """
        Remove all diagram widgets from the container
        """
        # delete all widgets from the layout
        for i in reversed(range(self.ui.schematic_layout.count())):
            # get the widget
            widget_to_remove = self.ui.schematic_layout.itemAt(i).widget()

            # delete it from the layout list
            self.ui.schematic_layout.removeWidget(widget_to_remove)

            # delete it from the gui
            widget_to_remove.setParent(None)

    def set_diagram_widget(self, widget: ALL_EDITORS):
        """
        Set the current diagram in the container
        :param widget: DiagramEditorWidget, GridMapWidget, BusViewerGUI
        """
        self.remove_all_diagram_widgets()

        # add the new diagram
        self.ui.schematic_layout.addWidget(widget)

        # set the alignment
        self.ui.diagram_selection_splitter.setStretchFactor(0, 10)
        self.ui.diagram_selection_splitter.setStretchFactor(1, 1)

        # set the selected index
        row = self.diagram_widgets_list.index(widget)
        index = self.ui.diagramsListView.model().index(row, 0)
        self.ui.diagramsListView.setCurrentIndex(index)

        # set the properties
        self._enable_setting_auto_upgrade = False
        self.ui.branch_width_based_on_flow_checkBox.setChecked(widget.diagram.use_flow_based_width)
        self.ui.min_branch_size_spinBox.setValue(widget.diagram.min_branch_width)
        self.ui.max_branch_size_spinBox.setValue(widget.diagram.max_branch_width)
        self.ui.min_node_size_spinBox.setValue(widget.diagram.min_bus_width)
        self.ui.max_node_size_spinBox.setValue(widget.diagram.max_bus_width)
        self.ui.arrow_size_size_spinBox.setValue(widget.diagram.arrow_size)
        self.ui.use_schematic_objects_color_checkBox.setChecked(widget.diagram.use_api_colors)
        self.ui.palette_comboBox.setCurrentIndex(self.cmap_index_dict.get(widget.diagram.palette, 0))

        if isinstance(widget, GridMapWidget):
            self.ui.tile_provider_comboBox.setEnabled(True)
            self.ui.tile_provider_comboBox.setCurrentIndex(self.tile_index_dict[widget.map.tile_src.tile_set_name])
        else:
            self.ui.tile_provider_comboBox.setEnabled(False)

        self.ui.defaultBusVoltageSpinBox.setValue(widget.diagram.default_bus_voltage)
        self._enable_setting_auto_upgrade = True

    def plot_style_change(self):
        """
        Change the style
        """
        style = self.ui.plt_style_comboBox.currentText()
        plt.style.use(style)

    def diagrams_time_slider_change(self) -> None:
        """
        After releasing the time slider, do something
        """
        self.update_diagram_time_slider_texts()
        idx = self.ui.diagram_step_slider.value()

        # correct to interpret -1 as None
        idx2 = idx if idx > -1 else None

        # modify the time index in all the bus-branch diagrams
        for diagram in self.diagram_widgets_list:
            if isinstance(diagram, SchematicWidget):
                diagram.set_time_index(time_index=idx2)
            if isinstance(diagram, GridMapWidget):
                diagram.set_time_index(time_index=idx2)

    def update_diagram_time_slider_texts(self):
        """
        Update the slider text label as it is moved
        :return:
        """
        idx = self.ui.diagram_step_slider.value()

        if idx > -1:
            val = f"[{idx}] {self.circuit.time_profile[idx]}"
            self.ui.schematic_step_label.setText(val)
        else:
            self.ui.schematic_step_label.setText(f"Snapshot [{self.circuit.get_snapshot_time_str()}]")

    def objects_time_slider_change(self) -> None:
        """
        After releasing the time slider, do something
        """
        self.objects_diagram_time_slider_texts()

        idx = self.ui.db_step_slider.value()

        # correct to interpret -1 as None
        idx2 = idx if idx > -1 else None

        # modify the time index in the current DB objects model
        mdl: ObjectModelFilterProxy | None = self.get_current_objects_model_view()
        if isinstance(mdl, ObjectModelFilterProxy):
            mdl.set_time_index(time_index=idx2)

    def objects_diagram_time_slider_texts(self):
        """
        Update the slider text label as it is moved
        :return:
        """
        idx = self.ui.db_step_slider.value()

        if idx > -1:
            val = f"[{idx}] {self.circuit.time_profile[idx]}"
            self.ui.db_step_label.setText(val)
        else:
            self.ui.db_step_label.setText(f"Snapshot [{self.circuit.get_snapshot_time_str()}]")

    def take_picture(self):
        """
        Save the schematic
        :return:
        """
        diagram = self.get_selected_diagram_widget()
        if diagram is not None:
            if isinstance(diagram, (SchematicWidget, GridMapWidget)):

                # declare the allowed file types
                files_types = ("Scalable Vector Graphics (*.svg);;"
                               "Portable Network Graphics (*.png)")

                f_name = str(os.path.join(self.project_directory, self.ui.grid_name_line_edit.text()))

                # call dialog to select the file
                filename, type_selected = QtWidgets.QFileDialog.getSaveFileName(self, 'Save image file',
                                                                                f_name, files_types)

                if filename != "":
                    if 'svg' in type_selected:
                        if not filename.endswith('.svg'):
                            filename += ".svg"

                    elif 'png' in type_selected:
                        if not filename.endswith('.png'):
                            filename += ".png"

                    # save
                    diagram.take_picture(filename)

    def record_video(self):
        """
        Save the schematic
        :return:
        """
        if self.circuit.has_time_series:
            diagram = self.get_selected_diagram_widget()
            if diagram is not None:
                if isinstance(diagram, (SchematicWidget, GridMapWidget)):

                    # declare the allowed file types
                    files_types = "MP4 (*.mp4);;AVI (*.avi);;"

                    f_name = str(os.path.join(self.project_directory, self.ui.grid_name_line_edit.text()))

                    # call dialog to select the file
                    filename, type_selected = QtWidgets.QFileDialog.getSaveFileName(self, 'Save video file',
                                                                                    f_name, files_types)

                    if filename != "":
                        if type_selected == "MP4 (*.mp4)" and not filename.endswith('.mp4'):
                            filename += ".mp4"

                        if type_selected == "AVI (*.avi)" and not filename.endswith('.avi'):
                            filename += ".avi"

                        # self.thread_pool.start(lambda: self.record_video_now(filename, diagram))
                        self.video_thread = VideoExportWorker(
                            filename=filename,
                            diagram=diagram,
                            fps=self.ui.fps_spinBox.value(),
                            start_idx=self.get_simulation_start(),
                            end_idx=self.get_simulation_end(),
                            current_study=self.ui.available_results_to_color_comboBox.currentText(),
                            grid_colour_function=self.grid_colour_function
                        )
                        self.video_thread.progress_signal.connect(self.ui.progressBar.setValue)
                        self.video_thread.progress_text.connect(self.ui.progress_label.setText)
                        self.video_thread.done_signal.connect(self.post_video_export)
                        self.video_thread.run()  # we cannot run another thread accessing the main thread objects...
            else:
                self.show_error_toast("There is no diagram selected")

        else:
            self.show_error_toast("There are no time series")

    def post_video_export(self):
        """

        :return:
        """
        if self.video_thread.logger.has_logs():
            self.show_logs(self.video_thread.logger, "Video export")

    def set_xy_from_lat_lon(self):
        """
        Get the x, y coordinates of the buses from their latitude and longitude
        """
        if self.circuit.valid_for_simulation():

            diagram = self.get_selected_diagram_widget()
            if diagram is not None:
                if isinstance(diagram, SchematicWidget):

                    if yes_no_question("All nodes in the current diagram will be positioned to a 2D plane projection "
                                       "of their latitude and longitude. "
                                       "Are you sure of this?"):
                        diagram.fill_xy_from_lat_lon(destructive=True)
                        diagram.center_nodes()
                else:
                    self.show_warning_toast("No schematic diagram selected!")
            else:
                self.show_warning_toast("No diagram selected!")

    def set_big_bus_marker(self, buses: List[dev.Bus], color: QtGui.QColor):
        """
        Set a big marker at the selected buses
        :param buses: list of Bus objects
        :param color: colour to use
        """

        for diagram in self.diagram_widgets_list:

            if isinstance(diagram, SchematicWidget):
                diagram.set_big_bus_marker(buses=buses, color=color)

    def set_big_bus_marker_colours(self,
                                   buses: List[dev.Bus],
                                   colors: Iterable[QtGui.QColor],
                                   tool_tips: Union[None, List[str]] = None):
        """
        Set a big marker at the selected buses with the matching colours
        :param buses: list of Bus objects
        :param colors: list of colour to use
        :param tool_tips: list of tool tips (optional)
        """

        for diagram in self.diagram_widgets_list:

            if isinstance(diagram, SchematicWidget):
                diagram.set_big_bus_marker_colours(buses=buses,
                                                   colors=colors,
                                                   tool_tips=tool_tips)

    def clear_big_bus_markers(self):
        """
        Clear big markers at the selected buses
        """

        for diagram in self.diagram_widgets_list:
            if isinstance(diagram, SchematicWidget):
                diagram.clear_big_bus_markers()

    def delete_selected_from_the_diagram(self):
        """
        Prompt to delete_with_dialogue the selected buses from the current diagram
        """

        diagram_widget = self.get_selected_diagram_widget()
        if isinstance(diagram_widget, SchematicWidget):
            diagram_widget.delete_selected_from_widget(delete_from_db=False)

        elif isinstance(diagram_widget, GridMapWidget):
            diagram_widget.delete_selected_from_widget(delete_from_db=False)

    def delete_selected_diagram_widgets(self):
        """
        Prompt to delete the selected elements from the current diagram and (optionally) the database
        """
        diagram_widget = self.get_selected_diagram_widget()
        if isinstance(diagram_widget, SchematicWidget):
            diagram_widget.delete_selected_from_widget(delete_from_db=True)

        elif isinstance(diagram_widget, GridMapWidget):
            diagram_widget.delete_selected_from_widget(delete_from_db=True)

        else:
            self.show_error_toast("delete_selected_diagram_widgets: Unsupported widget :(")

    def try_to_fix_buses_location(self):
        """
        Try to fix the location of the buses
        """
        diagram_widget = self.get_selected_diagram_widget()
        if isinstance(diagram_widget, SchematicWidget):
            selected_buses = diagram_widget.get_selected_buses()
            if len(selected_buses) > 0:
                diagram_widget.try_to_fix_buses_location(buses_selection=selected_buses)
            else:
                info_msg('Choose some elements from the schematic', 'Fix buses locations')

    def get_selected_devices(self) -> List[ALL_DEV_TYPES]:
        """
        Get the selected investment devices
        :return: list of selected devices
        """

        diagram = self.get_selected_diagram_widget()

        if isinstance(diagram, SchematicWidget):
            lst = diagram._get_selection_api_objects()
        elif isinstance(diagram, GridMapWidget):
            lst = list()
        else:
            lst = list()

        return lst

    def add_selected_to_contingency(self):
        """
        Add contingencies from the schematic selection
        """
        if self.circuit.valid_for_simulation():

            # get the selected buses
            selected = self.get_selected_devices()

            if len(selected) > 0:
                names = [elm.type_name + ": " + elm.name for elm in selected]
                group_text = "Contingency " + selected[0].name
                self.contingency_checks_diag = CheckListDialogue(objects_list=names,
                                                                 title="Add contingency",
                                                                 ask_for_group_name=True,
                                                                 group_label="Contingency name",
                                                                 group_text=group_text)
                self.contingency_checks_diag.setModal(True)
                self.contingency_checks_diag.exec()

                if self.contingency_checks_diag.is_accepted:

                    group = dev.ContingencyGroup(idtag=None,
                                                 name=self.contingency_checks_diag.get_group_text(),
                                                 category="single" if len(selected) == 1 else "multiple")
                    self.circuit.add_contingency_group(group)

                    for i in self.contingency_checks_diag.selected_indices:
                        elm = selected[i]
                        con = dev.Contingency(device=elm,
                                              code=elm.code,
                                              name="Contingency " + elm.name,
                                              prop=ContingencyOperationTypes.Active,
                                              value=0,
                                              group=group)
                        self.circuit.add_contingency(con)
            else:
                info_msg("Select some elements in the schematic first", "Add selected to contingency")

    def add_selected_to_remedial_action(self):
        """
        Add contingencies from the schematic selection
        """
        if self.circuit.valid_for_simulation():

            # get the selected buses
            selected = self.get_selected_devices()

            if len(selected) > 0:
                names = [elm.type_name + ": " + elm.name for elm in selected]
                group_text = "RA " + selected[0].name
                self.ra_checks_diag = CheckListDialogue(objects_list=names,
                                                        title="Add remedial action",
                                                        ask_for_group_name=True,
                                                        group_label="Remedial action name",
                                                        group_text=group_text)
                self.ra_checks_diag.setModal(True)
                self.ra_checks_diag.exec()

                if self.ra_checks_diag.is_accepted:

                    ra_group = dev.RemedialActionGroup(idtag=None,
                                                       name=self.ra_checks_diag.get_group_text(),
                                                       category="single" if len(selected) == 1 else "multiple")
                    self.circuit.add_remedial_action_group(ra_group)

                    for i in self.ra_checks_diag.selected_indices:
                        elm = selected[i]
                        ra = dev.RemedialAction(device=elm,
                                                code=elm.code,
                                                name="RA " + elm.name,
                                                prop=ContingencyOperationTypes.Active,
                                                value=0,
                                                group=ra_group)
                        self.circuit.add_remedial_action(ra)
            else:
                info_msg("Select some elements in the schematic first", "Add selected to remedial action")

    def add_selected_to_investment(self) -> None:
        """
        Add contingencies from the schematic selection
        """
        if self.circuit.valid_for_simulation():

            # get the selected investment devices
            selected = self.get_selected_devices()

            if len(selected) > 0:

                group_name = "Investment " + str(len(self.circuit.get_contingency_groups()))

                # launch selection dialogue to add/delete from the selection
                names = [elm.type_name + ": " + elm.name for elm in selected]
                self.investment_checks_diag = CheckListDialogue(objects_list=names,
                                                                title="Add investment",
                                                                ask_for_group_name=True,
                                                                group_label="Investment name",
                                                                group_text=group_name)
                self.investment_checks_diag.setModal(True)
                self.investment_checks_diag.exec()

                if self.investment_checks_diag.is_accepted:

                    # create a new investments group
                    group = dev.InvestmentsGroup(idtag=None,
                                                 name=self.investment_checks_diag.get_group_text(),
                                                 category="single" if len(selected) == 1 else "multiple")
                    self.circuit.add_investments_group(group)

                    # add the selection as investments to the group
                    for i in self.investment_checks_diag.selected_indices:
                        elm = selected[i]
                        con = dev.Investment(device=elm,
                                             code=elm.code,
                                             name=elm.type_name + ": " + elm.name,
                                             CAPEX=0.0,
                                             group=group)
                        self.circuit.add_investment(con)
            else:
                info_msg("Select some elements in the schematic first", "Add selected to investment")

    def add_rms_event_to_selected(self) -> None:
        """
        Add RMS event to a selected device
        """
        mode = DynamicSimulationMode.RMS
        if self.circuit.valid_for_simulation():

            # get the selected device to apply event to
            target_devices = self.get_selected_devices()

            if len(target_devices) == 1:

                target_device = target_devices[0]
                # launch rms event editor dialogue

                events_groups = self.circuit.rms_events_groups
                if len(events_groups) == 0:

                    QtWidgets.QMessageBox.information(
                        self,
                        "No RMS Events Group",
                        "No RMS Events Group found, please create one before adding an event."
                    )

                    dialog = DynamicEventsGroupsDialog(mode=mode,
                                                       parent=self)
                    if dialog.exec():
                        name = dialog.get_name()
                        # build group
                        if name:
                            self.circuit.add_rms_events_group(dev.RmsEventsGroup(idtag=None,
                                                                                 name=name))


                else:
                    rms_events_dialog = DynamicEventDialogue(circuit=self.circuit,
                                                             parameters_list=[var for var in
                                                                          target_device.rms_model.event_dict.keys()],
                                                             target_device_name=target_device.type_name + ": " + target_device.name,
                                                             mode=mode)

                    if rms_events_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:

                        events_data = rms_events_dialog.get_data()
                        events_list = []
                        for i, event in enumerate(events_data["parameters"]):
                            events_list.append(dev.RmsEvent(device=target_device,
                                                            parameter=events_data["parameters"][i],
                                                            time=float(events_data["target_times"][i]),
                                                            value=float(events_data["values"][i]),
                                                            group=events_data["groups"][i]))

                        for event in events_list:
                            self.circuit.add_rms_event(event)

            else:
                self.show_warning_toast(f"Select one and only one device to add event to")

    def add_emt_event_to_selected(self) -> None:
        """
        Add EMT event to a selected device
        """
        mode = DynamicSimulationMode.EMT
        if self.circuit.valid_for_simulation():

            # get the selected device to apply event to
            target_devices = self.get_selected_devices()

            if len(target_devices) == 1:

                target_device = target_devices[0]
                # launch emt event editor dialogue

                events_groups = self.circuit.emt_events_groups
                if len(events_groups) == 0:

                    QtWidgets.QMessageBox.information(
                        self,
                        "No EMT Events Group",
                        "No EMT Events Group found, please create one before adding an event."
                    )

                    dialog = DynamicEventsGroupsDialog(parent=self,
                                                       mode=mode)
                    if dialog.exec():
                        name = dialog.get_name()
                        # build group
                        if name:
                            self.circuit.add_emt_events_group(dev.EmtEventsGroup(idtag=None,
                                                                                 name=name))


                else:
                    emt_events_dialog = DynamicEventDialogue(circuit=self.circuit,
                                                             parameters_list=[var for var in
                                                                          target_device.emt_model.event_dict.keys()],
                                                             target_device_name=target_device.type_name + ": " + target_device.name,
                                                             mode=mode)

                    if emt_events_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:

                        events_data = emt_events_dialog.get_data()
                        events_list = list()
                        for i, event in enumerate(events_data["parameters"]):
                            events_list.append(dev.EmtEvent(device=target_device,
                                                            parameter=events_data["parameters"][i],
                                                            time=float(events_data["target_times"][i]),
                                                            value=float(events_data["values"][i]),
                                                            group=events_data["groups"][i]))

                        for event in events_list:
                            self.circuit.add_emt_event(event)

            else:
                self.show_warning_toast(f"Select one and only one device to add event to")

    def add_short_circuit_events(self):
        """

        :return:
        """
        if self.circuit.valid_for_simulation():

            # get the selected investment devices
            selected: List[Tuple[int, dev.Bus, BusGraphicItem | None]] = self.get_diagram_selected_buses()

            if len(selected) > 0:

                self.sc_selector_dialogue: ShortCircuitSelector = ShortCircuitSelector()
                self.sc_selector_dialogue.exec()

                if self.sc_selector_dialogue.was_accepted:

                    for _, bus, _ in selected:
                        z_pu: complex = self.sc_selector_dialogue.get_impedance_pu(Sbase=self.circuit.Sbase,
                                                                                   Vbase=bus.Vnom)
                        sc = dev.ShortCircuitEvent(
                            name=f"{bus.name} {self.sc_selector_dialogue.fault.value}",
                            device=bus,
                            fault_type=self.sc_selector_dialogue.fault,
                            method=self.sc_selector_dialogue.method,
                            phases=self.sc_selector_dialogue.phases,
                            r_fault=z_pu.real,
                            x_fault=z_pu.imag
                        )

                        self.circuit.add_short_circuit_event(sc)

                    self.show_info_toast(f"{len(selected)} short circuit events added!")
            else:
                self.show_warning_toast("Select some buses in the diagram!")

    def select_buses_by_property(self, prop: str):
        """
        Select the current diagram buses by prop
        :param prop: area, zone, country
        """
        if prop == 'area':
            self.object_select_window = ObjectSelectWindow(title='Area',
                                                           object_list=self.circuit.areas,
                                                           parent=self)
            self.object_select_window.setModal(True)
            self.object_select_window.exec()

            if self.object_select_window.selected_object is not None:

                for k, bus, graphic_obj in self.get_current_diagram_buses():
                    if bus.area == self.object_select_window.selected_object:
                        graphic_obj.setSelected(True)

        elif prop == 'country':
            self.object_select_window = ObjectSelectWindow(title='country',
                                                           object_list=self.circuit.countries,
                                                           parent=self)
            self.object_select_window.setModal(True)
            self.object_select_window.exec()

            if self.object_select_window.selected_object is not None:
                for k, bus, graphic_obj in self.get_current_diagram_buses():
                    if bus.country == self.object_select_window.selected_object:
                        graphic_obj.setSelected(True)

        elif prop == 'zone':
            self.object_select_window = ObjectSelectWindow(title='Zones',
                                                           object_list=self.circuit.zones,
                                                           parent=self)
            self.object_select_window.setModal(True)
            self.object_select_window.exec()

            if self.object_select_window.selected_object is not None:
                for k, bus, graphic_obj in self.get_current_diagram_buses():
                    if bus.zone == self.object_select_window.selected_object:
                        graphic_obj.setSelected(True)
        else:
            error_msg('Unrecognized option' + str(prop))
            return

    def select_buses_by(self):
        """
        Select buses by...
        launched a dialogue to select the category, and then another to select the element
        """
        self.object_select_window = ListSelectWindow(title='Area',
                                                     elements=["area", "zone", "country"],
                                                     parent=self)
        self.object_select_window.setModal(True)
        self.object_select_window.exec()

        if self.object_select_window.selected_object is not None:
            self.select_buses_by_property(self.object_select_window.selected_object)

    def set_selected_bus_property(self, prop: str):
        """

        :param prop:
        :return:
        """
        if prop == 'area':
            self.object_select_window = ObjectSelectWindow(title='Area',
                                                           object_list=self.circuit.areas,
                                                           parent=self)
            self.object_select_window.setModal(True)
            self.object_select_window.exec()

            if self.object_select_window.selected_object is not None:
                for k, bus, graphic_obj in self.get_diagram_selected_buses():
                    bus.area = self.object_select_window.selected_object
                    print('Set {0} into bus {1}'.format(self.object_select_window.selected_object.name, bus.name))

        elif prop == 'country':
            self.object_select_window = ObjectSelectWindow(title='country',
                                                           object_list=self.circuit.countries,
                                                           parent=self)
            self.object_select_window.setModal(True)
            self.object_select_window.exec()

            if self.object_select_window.selected_object is not None:
                for k, bus, graphic_obj in self.get_diagram_selected_buses():
                    bus.country = self.object_select_window.selected_object
                    print('Set {0} into bus {1}'.format(self.object_select_window.selected_object.name, bus.name))

        elif prop == 'zone':
            self.object_select_window = ObjectSelectWindow(title='Zones',
                                                           object_list=self.circuit.zones,
                                                           parent=self)
            self.object_select_window.setModal(True)
            self.object_select_window.exec()

            if self.object_select_window.selected_object is not None:
                for k, bus, graphic_pbj in self.get_diagram_selected_buses():
                    bus.zone = self.object_select_window.selected_object
                    print('Set {0} into bus {1}'.format(self.object_select_window.selected_object.name, bus.name))
        else:
            error_msg('Unrecognized option' + str(prop))
            return

    def color_buses_by(self):
        """
        Launch the bus coloring
        """
        self.object_select_window = ListSelectWindow(title='Select association',
                                                     elements=["area", "zone", "country", "substation"],
                                                     parent=self)
        self.object_select_window.setModal(True)
        self.object_select_window.exec()
        any_op = False

        for k, bus, graphic_obj in self.get_current_diagram_buses():

            if self.object_select_window.selected_object == "area":
                hex_color = bus.area.color if bus.area is not None else None

            elif self.object_select_window.selected_object == "zone":
                hex_color = bus.zone.color if bus.zone is not None else None

            elif self.object_select_window.selected_object == "country":
                hex_color = bus.country.color if bus.country is not None else None

            elif self.object_select_window.selected_object == "substation":
                hex_color = bus.substation.color if bus.substation is not None else None

            else:
                hex_color = None

            if hex_color is not None:
                graphic_obj.color = QtGui.QBrush(QtGui.QColor(hex_color))
                graphic_obj.set_tile_color(graphic_obj.color)
                any_op = True

        if not any_op:
            self.show_warning_toast(
                f"Nothing coloured, check the buses {self.object_select_window.selected_object} property."
            )

    def color_substations_by(self):
        """
        Launch substation coloring
        """

        self.object_select_window = ListSelectWindow(title='Select association',
                                                     elements=["area", "zone", "country",
                                                               "community", "region", "municipality",
                                                               "substation"],
                                                     parent=self)
        self.object_select_window.setModal(True)
        self.object_select_window.exec()

        if self.object_select_window.selected_object is not None:
            any_op = False

            for k, substation, graphic_obj in self.get_current_diagram_substations():

                if self.object_select_window.selected_object == "area":
                    hex_color = substation.area.color if substation.area is not None else None

                elif self.object_select_window.selected_object == "zone":
                    hex_color = substation.zone.color if substation.zone is not None else None

                elif self.object_select_window.selected_object == "country":
                    hex_color = substation.country.color if substation.country is not None else None

                elif self.object_select_window.selected_object == "community":
                    hex_color = substation.community.color if substation.community is not None else None

                elif self.object_select_window.selected_object == "region":
                    hex_color = substation.region.color if substation.region is not None else None

                elif self.object_select_window.selected_object == "municipality":
                    hex_color = substation.municipality.color if substation.municipality is not None else None

                elif self.object_select_window.selected_object == "substation":
                    hex_color = substation.color
                else:
                    hex_color = None

                if hex_color is not None:
                    color = QtGui.QColor(hex_color)
                    graphic_obj.color = color
                    graphic_obj.border_color = color
                    graphic_obj.color_widget(
                        inner_color=color,
                        border_color=color
                    )
                    any_op = True

            if not any_op:
                self.show_warning_toast(
                    f"Nothing coloured, check the substations {self.object_select_window.selected_object} property."
                )

    def default_voltage_change(self):
        """
        When the default voltage changes, update all the diagrams
        """
        val = self.ui.defaultBusVoltageSpinBox.value()

        for diagram in self.diagram_widgets_list:

            if isinstance(diagram, SchematicWidget):
                diagram.default_bus_voltage = val

            elif isinstance(diagram, GridMapWidget):
                pass

    def delete_from_all_diagrams(self, elements: List[ALL_DEV_TYPES]):
        """
        Delete elements from all editors
        :param elements: list of devices to delete_with_dialogue from the graphics editors
        :return:
        """
        for diagram_widget in self.diagram_widgets_list:
            if isinstance(diagram_widget, SchematicWidget):
                diagram_widget.delete_diagram_elements(elements)

            elif isinstance(diagram_widget, GridMapWidget):
                pass

    def search_diagram(self):
        """
        Search elements by name, code or idtag and center them in the screen
        """
        diagram = self.get_selected_diagram_widget()
        search_text = self.ui.diagramSearchLineEdit.text().lower()
        if diagram is not None:
            if isinstance(diagram, SchematicWidget):
                diagram.graphical_search(search_text=search_text)
            elif isinstance(diagram, GridMapWidget):
                diagram.graphical_search(search_text=search_text)

    def show_diagrams_context_menu(self, pos: QtCore.QPoint):
        """
        Show diagrams list view context menu
        :param pos: Relative click position
        """
        context_menu = QtWidgets.QMenu(parent=self.ui.diagramsListView)

        gf.add_menu_entry(menu=context_menu,
                          text="New schematic",
                          icon_path=":/Icons/icons/schematic.png",
                          function_ptr=self.add_complete_bus_branch_diagram)

        gf.add_menu_entry(menu=context_menu,
                          text="New schematic from selection",
                          icon_path=":/Icons/icons/schematic.png",
                          function_ptr=self.new_bus_branch_diagram_from_selection)

        gf.add_menu_entry(menu=context_menu,
                          text="New map",
                          icon_path=":/Icons/icons/map (add).png",
                          function_ptr=self.add_map_diagram)

        gf.add_menu_entry(menu=context_menu,
                          text="Duplicate",
                          icon_path=":/Icons/icons/copy.png",
                          function_ptr=self.duplicate_diagram)

        context_menu.addSeparator()
        gf.add_menu_entry(menu=context_menu,
                          text="Remove",
                          icon_path=":/Icons/icons/delete3.png",
                          function_ptr=self.remove_diagram)

        # Convert global position to local position of the list widget
        mapped_pos = self.ui.diagramsListView.viewport().mapToGlobal(pos)
        context_menu.exec(mapped_pos)

    def disable_all_results_tags(self):
        """
        Disable all tags for the selected diagram
        """
        diagram = self.get_selected_diagram_widget()

        if isinstance(diagram, SchematicWidget):
            diagram.disable_all_results_tags()

    def enable_all_results_tags(self):
        """
        Enable all tags for the selected diagram
        """
        diagram = self.get_selected_diagram_widget()

        if isinstance(diagram, SchematicWidget):
            diagram.enable_all_results_tags()

    def call_delete_db_element(self, caller: SchematicWidget | GridMapWidget | BaseDiagramWidget,
                               api_obj: ALL_DEV_TYPES):
        """
        This function is meant to be a master delete_with_dialogue function that is passed to each diagram
        so that when a diagram deletes an element, the element is deleted in all other diagrams
        :param caller:
        :param api_obj:
        :return:
        """
        for diagram in self.diagram_widgets_list:
            if diagram != caller:
                if isinstance(diagram, (SchematicWidget, GridMapWidget)):
                    diagram.delete_element_utility_function(device=api_obj, propagate=False)
                elif isinstance(diagram, (dev.SchematicDiagram, dev.MapDiagram)):
                    diagram.delete_device(device=api_obj)
                else:
                    pass

        try:
            self.circuit.delete_element(obj=api_obj)
        except ValueError as e:
            print(e)

    def set_diagrams_size_constraints(self):
        """
        Set the size constraints
        """
        if self._enable_setting_auto_upgrade:
            diagram_widget = self.get_selected_diagram_widget()

            if diagram_widget is not None:
                diagram_widget.set_size_constraints(
                    use_flow_based_width=self.ui.branch_width_based_on_flow_checkBox.isChecked(),
                    min_branch_width=self.ui.min_branch_size_spinBox.value(),
                    max_branch_width=self.ui.max_branch_size_spinBox.value(),
                    min_bus_width=self.ui.min_node_size_spinBox.value(),
                    max_bus_width=self.ui.max_node_size_spinBox.value(),
                    arrow_size=self.ui.arrow_size_size_spinBox.value(),
                )
                diagram_widget.diagram.default_bus_voltage = self.ui.defaultBusVoltageSpinBox.value()

    def set_diagrams_palette(self):
        """
        Set the size constraints
        """
        if self._enable_setting_auto_upgrade:
            diagram_widget = self.get_selected_diagram_widget()

            if diagram_widget is not None:
                cmap_text = self.ui.palette_comboBox.currentText()
                cmap = self.cmap_dict[cmap_text]
                diagram_widget.diagram.palette = cmap

                current_study = self.ui.available_results_to_color_comboBox.currentText()
                val = self.ui.diagram_step_slider.value()
                t_idx = val if val > -1 else None

                self.grid_colour_function(diagram_widget=diagram_widget,
                                          current_study=current_study,
                                          t_idx=t_idx)

    def set_diagrams_map_tile_provider(self):
        """
        Set the size constraints
        """
        if self._enable_setting_auto_upgrade:
            diagram_widget = self.get_selected_diagram_widget()

            if diagram_widget is not None:
                if isinstance(diagram_widget, GridMapWidget):
                    tile_name = self.ui.tile_provider_comboBox.currentText()
                    tile_src = self.tile_name_dict[tile_name]
                    diagram_widget.map.tile_src = tile_src

    def consolidate_diagram_coordinates(self):
        """
        Consolidate the diagram coordinates into the DB
        :return:
        """
        diagram_widget = self.get_selected_diagram_widget()

        if diagram_widget is not None:
            ok = yes_no_question(text="The diagram coordinates will be saved into the corresponding properties "
                                      "of the database, overwriting the existing ones. Do you want to do this?",
                                 title="Consolidate diagram coordinates into the DB")
            if ok:
                diagram_widget.consolidate_coordinates()

    def select_buses_from_substation(self, substation: dev.Substation) -> List[dev.Bus]:
        """

        :param substation:
        :return:
        """
        self.select_bus_dlg = DiagramBusSelectorDialogue(
            gui=self,
            grid=self.circuit,
            substation=substation
        )

        self.select_bus_dlg.exec()

        return self.select_bus_dlg.get_selected_buses()

    def combinations_tree_clicked(self):
        """
        On combinations tree click
        """
        indices = self.ui.combinationsTreeView.selectedIndexes()

        if len(indices) > 0:

            diagram_widget = self.get_selected_diagram_widget()
            use_flow_based_width = self.ui.branch_width_based_on_flow_checkBox.isChecked()
            min_branch_width = self.ui.min_branch_size_spinBox.value()
            max_branch_width = self.ui.max_branch_size_spinBox.value()
            min_bus_width = self.ui.min_node_size_spinBox.value()
            max_bus_width = self.ui.max_node_size_spinBox.value()
            cmap_text = self.ui.palette_comboBox.currentText()
            cmap = self.cmap_dict[cmap_text]

            text = indices[0].data(role=QtCore.Qt.ItemDataRole.DisplayRole)
            sel_idx = indices[0].row()
            if self.ui.available_results_to_color_comboBox.currentIndex() > -1 and sel_idx > -1:
                current_study = self.ui.available_results_to_color_comboBox.currentText()

                if current_study == sim.ShortCircuitDriver.tpe.value:
                    results: sim.ShortCircuitResults = self.session.get_results(SimulationTypes.ShortCircuit_run)
                    self.sc_colouring(diagram_widget=diagram_widget,
                                      results=results,
                                      cmap=cmap,
                                      use_flow_based_width=use_flow_based_width,
                                      min_branch_width=min_branch_width,
                                      max_branch_width=max_branch_width,
                                      min_bus_width=min_bus_width,
                                      max_bus_width=max_bus_width,
                                      sc_index=sel_idx)

        else:
            #  no indices selected
            pass

    def reset_diagram_coordinates(self):
        """
        Reset the diagram coordinates using the DB
        :return:
        """
        diagram_widget = self.get_selected_diagram_widget()

        if diagram_widget is not None:
            ok = yes_no_question(text="The diagram coordinates will be reset to its database values. "
                                      "Do you want to do this?",
                                 title="Reset diagram coordinates using the DB")
            if ok:
                diagram_widget.reset_coordinates()
                self.show_info_toast(message='Coordinates of substations and line '
                                             'locations set to its database values.')

    def rotate(self):
        """
        Rotate the selected diagram
        :return:
        """
        diagram_widget = self.get_selected_diagram_widget()

        if diagram_widget is not None:
            dlg = InputNumberDialogue(min_value=-180, max_value=180,
                                      default_value=-90, is_int=False,
                                      title='Rotate diagram',
                                      text=f'Rotation angle (degrees)')

            if dlg.exec():
                diagram_widget.rotate(dlg.value)

    def preset_1(self):
        """
        Country sizes
        """
        self.ui.min_node_size_spinBox.setValue(2)
        self.ui.max_node_size_spinBox.setValue(8)
        self.ui.min_branch_size_spinBox.setValue(1)
        self.ui.max_branch_size_spinBox.setValue(3)
        self.ui.arrow_size_size_spinBox.setValue(1.5)
        self.redraw_current_diagram()

    def preset_2(self):
        """
        Region sizes
        """
        self.ui.min_node_size_spinBox.setValue(1)
        self.ui.max_node_size_spinBox.setValue(2)
        self.ui.min_branch_size_spinBox.setValue(0.1)
        self.ui.max_branch_size_spinBox.setValue(0.2)
        self.ui.arrow_size_size_spinBox.setValue(0.15)
        self.redraw_current_diagram()

    def preset_3(self):
        """
        Municipality sizes
        """
        self.ui.min_node_size_spinBox.setValue(0.1)
        self.ui.max_node_size_spinBox.setValue(0.2)
        self.ui.min_branch_size_spinBox.setValue(0.01)
        self.ui.max_branch_size_spinBox.setValue(0.02)
        self.ui.arrow_size_size_spinBox.setValue(0.015)
        self.redraw_current_diagram()

    def preset_4(self):
        """
        Street sizes
        """
        self.ui.min_node_size_spinBox.setValue(0.01)
        self.ui.max_node_size_spinBox.setValue(0.02)
        self.ui.min_branch_size_spinBox.setValue(0.001)
        self.ui.max_branch_size_spinBox.setValue(0.002)
        self.ui.arrow_size_size_spinBox.setValue(0.0015)
        self.redraw_current_diagram()

    def set_diagram_branches_reticular_style(self):
        """
        Set all branches drawing mode to reticular
        """
        diagram = self.get_selected_diagram_widget()

        if isinstance(diagram, SchematicWidget):
            diagram.set_all_branch_drawing_styles(SchematicAutoRouteStyle.RETICULAR)

    def set_diagram_branches_straight_style(self):
        """
        Set all branches drawing mode to straight
        """
        diagram = self.get_selected_diagram_widget()

        if isinstance(diagram, SchematicWidget):
            diagram.set_all_branch_drawing_styles(SchematicAutoRouteStyle.STRAIGHT)
