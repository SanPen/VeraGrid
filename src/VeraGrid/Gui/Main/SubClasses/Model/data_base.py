# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import numpy as np
from typing import Union, List, Set, Tuple, Dict
from PySide6 import QtGui, QtCore, QtWidgets
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from VeraGrid.Gui.associations_model import AssociationsModel
from VeraGrid.Gui.table_view_header_wrap import HeaderViewWithWordWrap
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGrid.Gui.Main.SubClasses.Model.compiled_arrays_model import CompiledArraysModule
from VeraGridEngine.Topology.VoltageLevels import vl_creation_common_functions as substation_wizards
import VeraGridEngine.basic_structures as bs
import VeraGridEngine.Devices as dev
import VeraGrid.Gui.gui_functions as gf
from VeraGrid.Gui.object_model import ObjectsModel
from VeraGrid.Gui.object_proxy_model import ObjectModelFilterProxy
from VeraGrid.Gui.profiles_model import ProfilesModel
from VeraGridEngine.enumerations import DeviceType, DynamicSimulationMode, TimeSeriesSearchPoint, PrpCat
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Topology.detect_substations import detect_substations, detect_facilities
from VeraGrid.Gui.Analysis.object_plot_analysis import object_histogram_analysis
from VeraGrid.Gui.messages import yes_no_question, warning_msg, info_msg
from VeraGrid.Gui.Main.SubClasses.Model.diagrams import DiagramsMain
from VeraGrid.Gui.DeviceEditors.LineEditor.line_device_editor import LineDeviceEditorDialog
from VeraGrid.Gui.DeviceEditors.DcLineEditor.dc_line_device_editor import DcLineDeviceEditorDialog
from VeraGrid.Gui.DeviceEditors.LoadDesigner.load_device_editor import LoadDeviceEditorDialog
from VeraGrid.Gui.DeviceEditors.GeneratorEditor.generator_editor import GeneratorEditorDialog
from VeraGrid.Gui.DeviceEditors.VscEditor.vsc_device_editor import VscDeviceEditorDialog
from VeraGrid.Gui.DeviceEditors.TowerBuilder.LineBuilderDialogue import TowerBuilderGUI
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_workspace_manager import open_dynamic_editor
from VeraGrid.Gui.FmuTemplateEditor.fmu_template_editor import FmuTemplateEditorDialog
from VeraGrid.Gui.SystemScaler.system_scaler import SystemScaler
from VeraGrid.Gui.Diagrams.MapWidget.grid_map_widget import GridMapWidget, generate_map_diagram
from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget, make_diagram_from_buses
from VeraGrid.Gui.GridReduce.grid_reduce import GridReduceDialogue
from VeraGrid.Gui.SubstationDesigner.substation_designer import SubstationDesigner
from VeraGrid.Gui.general_dialogues import LogsDialogue, CustomQuestionDialogue, CheckListDialogue
from VeraGrid.Gui.DeviceEditors.TransformerEditor.transformer_device_editor import TransformerDeviceEditorDialog
from VeraGrid.Gui.DeviceEditors.Transformer3wEditor.transformer3w_device_editor import Transformer3WDeviceEditorDialog
from VeraGrid.Gui.DeviceEditors.ControllableShuntEditor.controllable_shunt_device_editor import (
    ControllableShuntDeviceEditorDialog,
)
from VeraGrid.Gui.Icons.icon_associations import device_type_icons


class DataBaseTableMain(DiagramsMain):
    """
    Diagrams Main
    """

    def __init__(self, parent=None):
        """

        @param parent:
        """

        # create main window
        DiagramsMain.__init__(self, parent)

        # list of all the objects of the selected type under the Objects tab
        self.type_objects_list = list()

        # setup the objects tree
        self.setup_objects_tree()

        # setup the tree for compiled arrays
        self.setup_compiled_arrays_tree()

        (self.ts_search_points_dict,
         ts_search_points_mdl) = gf.enums_to_model(
            [TimeSeriesSearchPoint.HighestLoad,
             TimeSeriesSearchPoint.LowestLoad]
        )
        self.ui.goToTsPointComboBox.setModel(ts_search_points_mdl)

        self.ui.smart_search_lineEdit.setPlaceholderText("Type the object name or a smart filter expression ...")

        self.prop_filter_dict, prop_filter_mdl = gf.enums_to_icons_model(
            [
                (PrpCat.All,":/Icons/icons/edit.png"),
                (PrpCat.TP,":/Icons/icons/automatic_layout.png"),
                (PrpCat.PF,":/Icons/icons/pf.png"),
                (PrpCat.PF3,":/Icons/icons/pf3.png"),
                (PrpCat.SC,":/Icons/icons/short_circuit.png"),
                (PrpCat.OPF,":/Icons/icons/dcopf.png"),
                (PrpCat.CON,":/Icons/icons/otdf.png"),
                (PrpCat.REL,":/Icons/icons/reliability.png"),
                (PrpCat.NTC,":/Icons/icons/ntc_opf.png"),
                (PrpCat.INV,":/Icons/icons/expansion_planning.png"),
                (PrpCat.RMS,":/Icons/icons/dyn.png"),
                (PrpCat.EMT,":/Icons/icons/dyn_emt.png"),
            ]
        )
        self.ui.dbFilterComboBox.setModel(prop_filter_mdl)

        # Buttons
        self.ui.filter_pushButton.clicked.connect(self.objects_smart_search)
        self.ui.delete_selected_objects_pushButton.clicked.connect(self.delete_selected_db_table_objects)
        self.ui.add_object_pushButton.clicked.connect(self.add_objects)
        self.ui.structure_analysis_pushButton.clicked.connect(self.objects_histogram_analysis_plot)
        self.ui.goToTsPointButton.clicked.connect(self.search_ts_point)

        # menu trigger
        self.ui.actionDelete_inconsistencies.triggered.connect(self.delete_inconsistencies)
        self.ui.actionClean_database.triggered.connect(self.clean_database)
        self.ui.actionScale.triggered.connect(self.scale)
        self.ui.actionDetect_substations.triggered.connect(self.detect_substations)
        self.ui.actionDetect_facilities.triggered.connect(self.detect_facilities)
        self.ui.actionGrid_reduction.triggered.connect(self.grid_reduction_from_schematic_selection)
        self.ui.actionSubstation_wizard.triggered.connect(self.add_substation_with_wizard)
        self.ui.actionSet_model_x_y_based_on_lat_lon.triggered.connect(self.set_model_x_y_based_on_lat_lon)
        self.ui.actionRestore_investments.triggered.connect(self.restore_investments)

        # tree click
        self.ui.dataStructuresTreeView.clicked.connect(self.view_objects_data)

        # line edit enter
        self.ui.smart_search_lineEdit.returnPressed.connect(self.objects_smart_search)

        # context menu
        self.ui.dataStructureTableView.customContextMenuRequested.connect(self.show_objects_context_menu)

        # Set context menu policy to CustomContextMenu
        self.ui.dataStructureTableView.setContextMenuPolicy(QtGui.Qt.ContextMenuPolicy.CustomContextMenu)

        # wrap headers
        self.ui.dataStructureTableView.setHorizontalHeader(HeaderViewWithWordWrap(self.ui.dataStructureTableView))
        self.ui.profiles_tableView.setHorizontalHeader(HeaderViewWithWordWrap(self.ui.profiles_tableView))
        self.ui.associationsTableView.setHorizontalHeader(HeaderViewWithWordWrap(self.ui.associationsTableView))

        # combobox change
        self.ui.associationsComboBox.currentTextChanged.connect(self.on_associations_combo_box_change)
        self.ui.dbFilterComboBox.currentTextChanged.connect(self.view_objects_data)

    def setup_objects_tree(self):
        """
        Setup the database left tree object
        """

        db_tree_model = gf.get_tree_model(d=self.circuit.get_template_objects_str_dict(),
                                          top='Objects',
                                          icons=device_type_icons)

        self.ui.dataStructuresTreeView.setModel(db_tree_model)
        self.ui.dataStructuresTreeView.setRootIsDecorated(True)
        self.expand_object_tree_nodes()

    def setup_compiled_arrays_tree(self):
        """

        :return:
        """
        mdl = gf.get_tree_model(d=CompiledArraysModule.available_structures,
                                top='Arrays')

        self.ui.simulationDataStructuresTreeView.setModel(mdl)

    def create_objects_model(self, elements, elm_type: DeviceType) -> ObjectsModel:
        """
        Generate the objects' table model
        :param elements: list of elements
        :param elm_type: name of DeviceType.BusDevice
        :return: QtCore.QAbstractTableModel
        """
        template_elm, dictionary_of_lists = self.circuit.get_dictionary_of_lists(elm_type=elm_type)

        filter_prop = self.prop_filter_dict[self.ui.dbFilterComboBox.currentText()]

        mdl = ObjectsModel(
            objects=elements,
            property_list=list(template_elm.property_list),
            time_index=self.get_db_slider_index(),
            parent=self.ui.dataStructureTableView,
            editable=True,
            dictionary_of_lists=dictionary_of_lists,
            properties_filter=filter_prop
        )

        return mdl

    def display_profiles(self, proxy_mdl: ObjectModelFilterProxy):
        """
        Display profile
        :param proxy_mdl: ObjectModelFilterProxy used for the object's table
        """
        if self.circuit.time_profile is not None:

            dev_type_text = self.get_db_object_selected_type()

            if dev_type_text is not None:

                magnitudes, mag_types = self.circuit.profile_magnitudes.get(dev_type_text, (list(), list()))

                if len(magnitudes) > 0:
                    # get the enumeration unique association with the device text
                    dev_type = self.circuit.device_type_name_dict[dev_type_text]

                    idx = self.ui.device_type_magnitude_comboBox.currentIndex()
                    magnitude = magnitudes[idx]
                    mtype = mag_types[idx]

                    mdl = ProfilesModel(time_array=self.circuit.get_time_array(),
                                        elements=proxy_mdl.objects,
                                        device_type=dev_type,
                                        magnitude=magnitude,
                                        data_format=mtype,
                                        parent=self.ui.profiles_tableView)
                    self.ui.profiles_tableView.setModel(mdl)
                else:
                    self.ui.profiles_tableView.setModel(None)
            else:
                self.ui.profiles_tableView.setModel(None)

    def display_associations(self, proxy_mdl: ObjectModelFilterProxy):
        """
        Display the association table
        :param proxy_mdl: ObjectModelFilterProxy used for the object's table
        :return:
        """
        dev_type_text = self.get_db_object_selected_type()
        association_property_name = self.ui.associationsComboBox.currentText()

        if dev_type_text is not None and proxy_mdl is not None and association_property_name != "":

            elements = proxy_mdl.objects

            if len(elements) > 0:

                gc_prop = elements[0].get_property_by_name(prop_name=association_property_name)
                associations: dev.Associations = elements[0].get_snapshot_value_by_name(name=association_property_name)
                associated_objects = self.circuit.get_elements_by_type(device_type=associations.device_type)
                self.ui.association_units_label.setText(gc_prop.units)

                if len(associated_objects) > 0:
                    mdl = AssociationsModel(objects=elements,
                                            associated_objects=associated_objects,
                                            gc_prop=gc_prop,
                                            table_view=self.ui.associationsTableView)

                    self.ui.associationsTableView.setModel(mdl)
                else:
                    self.ui.associationsTableView.setModel(None)
            else:
                self.ui.associationsTableView.setModel(None)
                self.ui.association_units_label.setText("")
        else:
            self.ui.associationsTableView.setModel(None)
            self.ui.association_units_label.setText("")

    def on_associations_combo_box_change(self):
        """
        Triggered on self.ui.associationsComboBox.currentTextChanged
        """
        self.display_associations(proxy_mdl=self.get_current_objects_model_view())

    def copy_objects_data(self):
        """
        Copy the current displayed objects table to the clipboard
        """
        mdl: ObjectModelFilterProxy | None = self.get_current_objects_model_view()
        if mdl is not None:
            mdl.copy_to_clipboard()
            self.show_info_toast('Copied!')
        else:
            warning_msg('There is no data displayed, please display one', 'Copy profile to clipboard')

    def get_db_object_selected_type(self) -> Union[None, str]:
        """
        Get the selected object type in the database tree view
        :return:
        """
        indices = self.ui.dataStructuresTreeView.selectedIndexes()

        if len(indices) > 0:
            return indices[0].data(role=QtCore.Qt.ItemDataRole.DisplayRole)
        else:
            return None

    def get_selected_objects_model(self) -> Tuple[ObjectsModel | None, List[ALL_DEV_TYPES] | None, str | None]:
        """
        Get the selected objects' model
        :return: ObjectsModel, list of objects, object type name
        """
        if len(self.ui.dataStructuresTreeView.selectedIndexes()) == 0:
            return None, None, None

        if self.ui.dataStructuresTreeView.selectedIndexes()[0].parent().row() > -1:
            # if the clicked element has a valid parent...

            elm_type = self.get_db_object_selected_type()

            if elm_type is not None:

                elements = self.circuit.get_elements_by_type(device_type=DeviceType(elm_type))

                objects_mdl = self.create_objects_model(elements=elements, elm_type=DeviceType(elm_type))

                return objects_mdl, elements, elm_type
            else:
                return None, None, None

        return None, None, None

    def view_objects_data(self):
        """
        On click, display the objects' properties
        """

        objects_mdl, elements, elm_type = self.get_selected_objects_model()

        if objects_mdl is not None:

            proxy = ObjectModelFilterProxy(mdl=objects_mdl)  # pass the same underlying list

            # update slice-view
            self.type_objects_list = elements
            self.ui.dataStructureTableView.setModel(proxy)

            # update time series view
            ts_mdl = gf.get_list_model(self.circuit.profile_magnitudes[elm_type][0])
            self.ui.device_type_magnitude_comboBox.setModel(ts_mdl)
            self.ui.device_type_magnitude_comboBox_2.setModel(ts_mdl)
            self.display_profiles(proxy_mdl=proxy)
            # the TS display will be triggered by the on-change event of the combobox

            # update the associations view
            assoc_mdl = gf.get_list_model(self.circuit.device_associations[elm_type])
            self.ui.associationsComboBox.setModel(assoc_mdl)
            self.display_associations(proxy_mdl=proxy)

        else:
            self.ui.dataStructureTableView.setModel(None)
            self.ui.device_type_magnitude_comboBox.clear()
            self.ui.device_type_magnitude_comboBox_2.clear()
            self.ui.associationsComboBox.clear()

    def get_selected_table_buses(self) -> Tuple[Set[dev.Bus], List[ALL_DEV_TYPES]]:
        """
        Get the list of selected buses, regardless of the object table type
        If the object has buses, this one takes them
        :return:
        """
        proxy_model: ObjectModelFilterProxy | None = self.get_current_objects_model_view()
        buses = set()
        selected_objects: List[ALL_DEV_TYPES] = list()

        if proxy_model is not None:

            source_model = proxy_model.sourceModel()

            sel_idx = self.ui.dataStructureTableView.selectedIndexes()
            objects: List[ALL_DEV_TYPES] = source_model.objects if hasattr(source_model, 'objects') else []

            if len(objects) > 0:

                if len(sel_idx) > 0:

                    unique = {proxy_model.mapToSource(idx).row() for idx in sel_idx}

                    for idx in unique:
                        sel_obj: ALL_DEV_TYPES = source_model.objects[idx]
                        selected_objects.append(sel_obj)

                    buses = self.circuit.get_buses_from_objects(elements=selected_objects,
                                                                dtype=objects[0].device_type)

        return buses, selected_objects

    def get_selected_table_substations(self) -> Tuple[Set[dev.Substation], List[ALL_DEV_TYPES]]:
        """
        Get the substations matching the table selection
        :return:  set of substations, list of selected objects originating the substation set
        """
        selected_objects = self.get_selected_db_table_objects()

        elm2se: Dict[ALL_DEV_TYPES, List[dev.Substation]] = dict()

        # Associate country, community, region and municipality to substation
        for se in self.circuit.substations:
            for elm in [se.country, se.community, se.region, se.municipality]:
                if elm is not None:
                    if elm in elm2se:
                        elm2se[elm].append(se)
                    else:
                        elm2se[elm] = [se]

        # associate voltage levels to substations
        for vl in self.circuit.voltage_levels:
            if vl.substation is not None:
                elm2se[vl] = [vl.substation]

        # associate buses to substations
        for bus in self.circuit.buses:
            if bus.substation is not None:
                elm2se[bus] = [bus.substation]

        substations = set()
        for sel_obj in selected_objects:
            se_list = elm2se.get(sel_obj, None)
            if se_list is not None:
                for se in se_list:
                    substations.add(se)

        return substations, selected_objects

    def delete_selected_db_table_objects(self):
        """
        Delete selection from the database main table
        """

        selected_objects = self.get_selected_db_table_objects()

        if len(selected_objects):

            ok = yes_no_question('Are you sure that you want to delete_with_dialogue the selected elements?', 'Delete')
            if ok:
                for obj in selected_objects:

                    # delete_with_dialogue from the database
                    self.circuit.delete_element(obj=obj)

                    # delete_with_dialogue from all diagrams
                    for diagram in self.diagram_widgets_list:
                        diagram.delete_element_utility_function(device=obj, propagate=False)

                # update the view
                self.view_objects_data()
                self.update_from_to_list_views()
                self.update_date_dependent_combos()

                self.show_info_toast(f"{len(selected_objects)} objects deleted")

    def duplicate_selected_db_table_objects(self):
        """
        Delete selection
        """

        selected_objects = self.get_selected_db_table_objects()

        if len(selected_objects):

            ok = yes_no_question('Are you sure that you want to duplicate the selected elements?',
                                 'Duplicate')
            if ok:
                for obj in selected_objects:
                    cpy = obj.copy(forced_new_idtag=True)
                    cpy.name += ' copy'
                    self.circuit.add_element(obj=cpy)

                # update the view
                self.view_objects_data()
                self.update_from_to_list_views()
                self.update_date_dependent_combos()

    def fuse_selected_db_table_objects(self):
        """
        Fuse selection
        """

        selected_objects = self.get_selected_db_table_objects()

        if len(selected_objects):

            if selected_objects[0].device_type == DeviceType.SubstationDevice:

                ok = yes_no_question('Are you sure that you want to merge the selected substations?',
                                     'Merge')
                if ok:
                    # merge substations into the first
                    self.circuit.merge_substations(selected_objects=selected_objects)

                    # update the view
                    self.view_objects_data()
                    self.update_from_to_list_views()
                    self.update_date_dependent_combos()

                    self.show_info_toast(f"{len(selected_objects)} substations merged")
            else:
                self.show_warning_toast(
                    f'Merge function not available for {selected_objects[0].device_type.value} devices')

    def copy_selected_idtag(self):
        """
        Copy selected idtags
        """

        selected_objects = self.get_selected_db_table_objects()

        if len(selected_objects):
            # copy to clipboard
            cb = QtWidgets.QApplication.clipboard()
            cb.clear()
            cb.setText("\n".join([obj.idtag for obj in selected_objects]))

            self.show_info_toast("Copied!")

    def add_objects_to_current_diagram(self):
        """
        Add selected DB objects to current diagram
        """

        selected_objects = self.get_selected_db_table_objects()

        if len(selected_objects):

            diagram = self.get_selected_diagram_widget()
            logger = bs.Logger()

            if isinstance(diagram, SchematicWidget):
                injections_by_bus = self.circuit.get_injection_devices_grouped_by_bus()
                injections_by_fluid_node = self.circuit.get_injection_devices_grouped_by_fluid_node()

                for device in selected_objects:
                    diagram.add_object_to_the_schematic(elm=device,
                                                        injections_by_bus=injections_by_bus,
                                                        injections_by_fluid_node=injections_by_fluid_node,
                                                        logger=logger)

            elif isinstance(diagram, GridMapWidget):

                for device in selected_objects:
                    diagram.add_object_to_the_schematic(elm=device, logger=logger)

            if len(logger):
                dlg = LogsDialogue(name="Add selected DB objects to current diagram", logger=logger)
                dlg.setModal(True)
                dlg.exec()

    def add_new_bus_diagram_from_selection(self):
        """
        Create a New diagram from a buses selection
        """
        selected_buses, selected_objects = self.get_selected_table_buses()

        if len(selected_buses):
            diagram = make_diagram_from_buses(circuit=self.circuit,
                                              buses=selected_buses,
                                              name=selected_objects[0].name + " diagram")

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

    def add_new_map_from_database_selection(self):
        """
        Create a New map from a buses selection
        """

        # from whatever, get the selected substations
        selected_buses, selected_objects = self.get_selected_table_buses()

        if len(selected_buses):

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

            self.new_se_dlg = CheckListDialogue(
                objects_list=[e.value for e in tpes]
            )

            if self.circuit.get_substation_number() > 0:
                # showing this menu only makes sense if there is anything there
                self.new_se_dlg.exec()
            else:
                self.show_warning_toast("No substations to draw...")
                return

            cmap_text = self.ui.palette_comboBox.currentText()
            cmap = self.cmap_dict[cmap_text]
            subgrid = self.circuit.slice_buses(buses=list(selected_buses))

            diagram = generate_map_diagram(
                substations=subgrid.get_substations() if self.new_se_dlg.selected(
                    DeviceType.SubstationDevice.value) else list(),
                voltage_levels=subgrid.get_voltage_levels() if self.new_se_dlg.selected(
                    DeviceType.SubstationDevice.value) else list(),
                lines=subgrid.get_lines() if self.new_se_dlg.selected(DeviceType.LineDevice.value) else list(),
                dc_lines=subgrid.get_dc_lines() if self.new_se_dlg.selected(
                    DeviceType.DCLineDevice.value) else list(),
                hvdc_lines=subgrid.get_hvdc() if self.new_se_dlg.selected(
                    DeviceType.HVDCLineDevice.value) else list(),
                fluid_nodes=subgrid.get_fluid_nodes(),
                fluid_paths=subgrid.get_fluid_paths(),
                external_grids=subgrid.external_grids if self.new_se_dlg.selected(
                    DeviceType.ExternalGridDevice.value) else list(),
                static_generators=subgrid.static_generators if self.new_se_dlg.selected(
                    DeviceType.StaticGeneratorDevice.value) else list(),
                loads=subgrid.loads if self.new_se_dlg.selected(DeviceType.LoadDevice.value) else list(),
                batteries=subgrid.batteries if self.new_se_dlg.selected(
                    DeviceType.BatteryDevice.value) else list(),
                generators=subgrid.generators if self.new_se_dlg.selected(
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

            default_tile_source = self.tile_name_dict[self.ui.tile_provider_comboBox.currentText()]
            tile_source = self.tile_name_dict.get(diagram.tile_source, default_tile_source)

            diagram_widget = GridMapWidget(
                gui=self,
                tile_src=tile_source,
                start_level=diagram.start_level,
                longitude=diagram.longitude,
                latitude=diagram.latitude,
                name=diagram.name,
                diagram=diagram,
            )

            self.add_diagram_widget_and_diagram(diagram_widget=diagram_widget,
                                                diagram=diagram)
            self.set_diagrams_list_view()

            self.show_info_toast(f"{diagram.name} added")

    def crop_model_to_buses_selection(self):
        """
        Crop model to buses selection
        :return:
        """
        selected_buses, selected_objects = self.get_selected_table_buses()

        if len(selected_buses):

            ok = yes_no_question(
                text="This will delete all buses and their connected elements that were not selected."
                     "This cannot be undone and it is dangerous if you don't know"
                     "what you are doing. \nAre you sure?",
                title="Crop model to buses selection?")

            if ok:
                to_be_deleted = list()
                for bus in self.circuit.buses:
                    if bus not in selected_buses:
                        to_be_deleted.append(bus)

                for bus in to_be_deleted:
                    self.circuit.delete_bus(obj=bus, delete_associated=True)

                self.view_objects_data()  # re-paint the table

                self.show_info_toast(f"{len(to_be_deleted)} buses removed from the model")

    def grid_reduction_from_table_selection(self):
        """
        Crop model to buses selection
        """
        selected_buses, selected_objects = self.get_selected_table_buses()

        if len(selected_buses):
            # get the previous power flow
            _, pf_res = self.session.power_flow

            self.grid_reduction_dialogue = GridReduceDialogue(grid=self.circuit,
                                                              session=self.session,
                                                              selected_buses_set=selected_buses)

            self.grid_reduction_dialogue.exec()

            if self.grid_reduction_dialogue.did_reduce:

                # delete from the diagrams
                self.delete_from_all_diagrams(elements=list(selected_buses))

                # update the view
                self.view_objects_data()
                self.update_from_to_list_views()
                self.update_date_dependent_combos()
            else:
                self.show_warning_toast("No reduction done")
        else:
            self.show_warning_toast("Select some elements first")

    def grid_reduction_from_schematic_selection(self):
        """
        Call the grid reduction dialogue on the schematic selection
        """

        diagram_widget = self.get_selected_diagram_widget()
        if isinstance(diagram_widget, SchematicWidget):
            selected_buses = diagram_widget.get_selected_buses()
            selected_se = list()

        elif isinstance(diagram_widget, GridMapWidget):
            selected_se = diagram_widget.get_selected_substations()
            selected_buses = diagram_widget.get_selected_buses()
        else:
            return None

        if len(selected_buses):
            # get the previous power flow
            _, pf_res = self.session.power_flow

            selected_buses_set: Set[dev.Bus] = {bus for i, bus, graphic in selected_buses}

            self.grid_reduction_dialogue = GridReduceDialogue(grid=self.circuit,
                                                              session=self.session,
                                                              selected_buses_set=selected_buses_set)

            self.grid_reduction_dialogue.exec()

            if self.grid_reduction_dialogue.did_reduce:
                self.delete_from_all_diagrams(elements=[bus for i, bus, graphic in selected_buses])

            if isinstance(diagram_widget, GridMapWidget):
                # if this is a map, delete the elements from there
                for se_graphics in selected_se:
                    if se_graphics.api_object is not None:
                        diagram_widget.delete_element_utility_function(
                            device=se_graphics.api_object,
                            propagate=True
                        )

            self.show_info_toast("Done!")
            return None
        else:
            self.show_warning_toast("No selected buses :/")
            return None

    def add_objects(self):
        """
        Add default objects objects
        """
        model = self.get_current_objects_model_view()
        elm_type = self.get_db_object_selected_type()

        if model is not None and elm_type is not None:

            if elm_type == DeviceType.SubstationDevice.value:
                self.circuit.add_substation(dev.Substation(name=f'SE {self.circuit.get_substation_number() + 1}'))
                self.update_from_to_list_views()

            elif elm_type == DeviceType.VoltageLevelDevice.value:
                self.circuit.add_voltage_level(dev.VoltageLevel(
                    name=f'VL {self.circuit.get_voltage_levels_number() + 1}')
                )
                self.update_from_to_list_views()

            elif elm_type == DeviceType.BusBarDevice.value:
                self.circuit.add_bus_bar(dev.BusBar(name=f'BB {self.circuit.get_bus_bars_number() + 1}'))
                self.update_from_to_list_views()

            elif elm_type == DeviceType.ZoneDevice.value:
                self.circuit.add_zone(dev.Zone(name=f'Zone {self.circuit.get_zone_number() + 1}'))
                self.update_from_to_list_views()

            elif elm_type == DeviceType.AreaDevice.value:
                self.circuit.add_area(dev.Area(name=f'Area {self.circuit.get_area_number() + 1}'))
                self.update_from_to_list_views()

            elif elm_type == DeviceType.CountryDevice.value:
                self.circuit.add_country(dev.Country(name=f'Country {self.circuit.get_country_number() + 1}'))
                self.update_from_to_list_views()

            elif elm_type == DeviceType.CommunityDevice.value:
                self.circuit.add_community(dev.Community(
                    name=f'Community {self.circuit.get_communities_number() + 1}')
                )
                self.update_from_to_list_views()

            elif elm_type == DeviceType.RegionDevice.value:
                self.circuit.add_region(dev.Region(name=f'Region {self.circuit.get_regions_number() + 1}'))
                self.update_from_to_list_views()

            elif elm_type == DeviceType.MunicipalityDevice.value:
                self.circuit.add_municipality(dev.Municipality(
                    name=f'Municipalities {self.circuit.get_municipalities_number() + 1}')
                )
                self.update_from_to_list_views()

            elif elm_type == DeviceType.BusDevice.value:
                self.circuit.add_bus(dev.Bus(name=f'Bus {self.circuit.get_bus_number() + 1}'))

            elif elm_type == DeviceType.ContingencyGroupDevice.value:
                group = dev.ContingencyGroup(
                    name=f"Contingency group {self.circuit.get_contingency_groups_number() + 1}"
                )
                self.circuit.add_contingency_group(group)

            elif elm_type == DeviceType.RemedialActionGroupDevice.value:
                group = dev.RemedialActionGroup(
                    name=f"Remedial actions group {self.circuit.get_remedial_action_groups_number() + 1}"
                )
                self.circuit.add_remedial_action_group(group)

            elif elm_type == DeviceType.InvestmentsGroupDevice.value:
                group = dev.InvestmentsGroup(name=f"Investments group {len(self.circuit.investments_groups) + 1}")
                self.circuit.add_investments_group(group)

            elif elm_type == DeviceType.BranchGroupDevice.value:
                group = dev.BranchGroup(name=f"Branch group {self.circuit.get_branch_groups_number() + 1}")
                self.circuit.add_branch_group(group)

            elif elm_type == DeviceType.Technology.value:
                tech = dev.Technology(name=f"Technology {len(self.circuit.technologies) + 1}")
                self.circuit.add_technology(tech)

            elif elm_type == DeviceType.OverheadLineTypeDevice.value:

                obj = dev.OverheadLineType()
                obj.frequency = self.circuit.fBase
                obj.name = f'Tower {len(self.circuit.overhead_line_types) + 1}'
                self.circuit.add_overhead_line(obj)

            elif elm_type == DeviceType.UnderGroundLineDevice.value:

                name = f'Cable {len(self.circuit.underground_cable_types) + 1}'
                obj = dev.UndergroundLineType(name=name)
                self.circuit.add_underground_line(obj)

            elif elm_type == DeviceType.SequenceLineDevice.value:

                name = f'Sequence line {len(self.circuit.sequence_line_types) + 1}'
                obj = dev.SequenceLineType(name=name)
                self.circuit.add_sequence_line(obj)

            elif elm_type == DeviceType.WireDevice.value:

                name = f'Wire {len(self.circuit.wire_types) + 1}'
                obj = dev.Wire(name=name)
                self.circuit.add_wire(obj)

            elif elm_type == DeviceType.TransformerTypeDevice.value:

                name = f'Transformer type {len(self.circuit.transformer_types) + 1}'
                obj = dev.TransformerType(hv_nominal_voltage=10, lv_nominal_voltage=0.4, nominal_power=2,
                                          copper_losses=0.8, iron_losses=0.1, no_load_current=0.1,
                                          short_circuit_voltage=0.1,
                                          gr_hv1=0.5, gx_hv1=0.5, name=name)
                self.circuit.add_transformer_type(obj)

            elif elm_type == DeviceType.FuelDevice.value:

                name = f'Fuel {len(self.circuit.fuels) + 1}'
                obj = dev.Fuel(name=name)
                self.circuit.add_fuel(obj)

            elif elm_type == DeviceType.EmissionGasDevice.value:

                name = f'Gas {len(self.circuit.emission_gases) + 1}'
                obj = dev.EmissionGas(name=name)
                self.circuit.add_emission_gas(obj)

            elif elm_type == DeviceType.Owner.value:

                name = f'Owner {len(self.circuit.owners) + 1}'
                obj = dev.Owner(name=name)
                self.circuit.add_owner(obj)

            elif elm_type == DeviceType.ModellingAuthority.value:

                name = f'Modelling authority {self.circuit.get_modelling_authorities_number()}'
                obj = dev.ModellingAuthority(name=name)
                self.circuit.add_modelling_authority(obj)

            elif elm_type == DeviceType.FacilityDevice.value:

                name = f'Facility {self.circuit.get_facility_number()}'
                obj = dev.Facility(name=name)
                self.circuit.add_facility(obj)

            # elif elm_type == DeviceType.DynamicModelHostDevice.value:
            #
            #     name = f'RMS model {self.circuit.get_rms_models_number()}'
            #     obj = dev.DynamicModelHost(name=name)
            #     self.circuit.add_rms_model(obj)

            elif elm_type == DeviceType.EmtModelTemplateDevice.value:

                name = f'EMT template {len(self.circuit.emt_models)}'
                obj = dev.EmtModelTemplate(name=name)
                self.circuit.add_emt_model(obj)


            elif elm_type == DeviceType.RmsModelTemplateDevice.value:

                name = f'RMS event {len(self.circuit.rms_events)}'
                obj = dev.RmsModelTemplate(name=name)
                self.circuit.add_rms_model(obj)

            elif elm_type == DeviceType.FmuTemplateDevice.value:

                name = f'FMU template {len(self.circuit.fmu_templates) + 1}'
                obj = dev.FmuTemplate(name=name)
                self.circuit.add_fmu_template(obj)


            elif elm_type == DeviceType.RmsEventDevice.value:

                name = f'RMS event {len(self.circuit.rms_events)}'
                obj = dev.RmsEvent(name=name)
                self.circuit.add_rms_event(obj)

            elif elm_type == DeviceType.RmsEventsGroupDevice.value:

                name = f'RMS event group {len(self.circuit.rms_events_groups)}'
                obj = dev.RmsEventsGroup(name=name)
                self.circuit.add_rms_events_group(obj)

            elif elm_type == DeviceType.EmtEventDevice.value:

                name = f'EMT event {len(self.circuit.rms_events)}'
                obj = dev.EmtEvent(name=name)
                self.circuit.add_emt_event(obj)

            elif elm_type == DeviceType.EmtEventsGroupDevice.value:

                name = f'EMT event group {len(self.circuit.rms_events_groups)}'
                obj = dev.EmtEventsGroup(name=name)
                self.circuit.add_emt_events_group(obj)

            else:
                info_msg("This object does not support table-like addition.\nUse the schematic instead.")
                return

            # update the view
            self.view_objects_data()

    def colour_branches_like_group(self):
        """
        Colour the branches like the branch group
        """
        model: ObjectModelFilterProxy | None = self.get_current_objects_model_view()

        if model is not None:

            if len(self.ui.dataStructuresTreeView.selectedIndexes()) > 0:

                rows = np.unique([sel.row() for sel in self.ui.dataStructureTableView.selectedIndexes()])

                for i in rows:

                    elm: dev.BranchGroup = model.objects[i]

                    if elm.device_type == DeviceType.BranchGroupDevice:

                        for br in self.circuit.get_branches_iter(add_vsc=True,
                                                                 add_hvdc=True,
                                                                 add_switch=True):
                            if br.group == elm:
                                br.color = elm.color

                self.show_info_toast("Done!")
            else:
                self.show_warning_toast("Nothing selected :/")

    def launch_object_editor(self):
        """
        Edit catalogue element
        """
        model: ObjectModelFilterProxy | None = self.get_current_objects_model_view()

        if model is not None:

            if len(self.ui.dataStructuresTreeView.selectedIndexes()) > 0:

                sel_item = self.ui.dataStructuresTreeView.selectedIndexes()[0]
                elm_type = sel_item.data(role=QtCore.Qt.ItemDataRole.DisplayRole)

                # get the selected index
                idx_proxy = self.ui.dataStructureTableView.currentIndex().row()

                if idx_proxy > -1:

                    # get the object from the table itself
                    elm = model.objects[idx_proxy]

                    if elm_type == DeviceType.OverheadLineTypeDevice.value:

                        # launch editor
                        self.tower_builder_window = TowerBuilderGUI(
                            tower=elm,
                            wires_catalogue=self.circuit.wire_types
                        )
                        self.tower_builder_window.setModal(True)
                        self.tower_builder_window.resize(int(1.81 * 700.0), 700)
                        self.tower_builder_window.exec()

                    elif elm_type == DeviceType.LineDevice.value:
                        dlg = LineDeviceEditorDialog(api_object=elm, circuit=self.circuit)
                        dlg.exec()

                    elif elm_type == DeviceType.DCLineDevice.value:
                        dlg = DcLineDeviceEditorDialog(api_object=elm, circuit=self.circuit)
                        if dlg.exec():
                            pass

                    elif elm_type == DeviceType.VscDevice.value:
                        dlg = VscDeviceEditorDialog(api_object=elm, circuit=self.circuit)
                        if dlg.exec():
                            pass

                    elif elm_type == DeviceType.Transformer2WDevice.value:
                        dlg = TransformerDeviceEditorDialog(api_object=elm, circuit=self.circuit)
                        if dlg.exec():
                            pass

                    elif elm_type == DeviceType.ControllableShuntDevice.value:
                        dlg = ControllableShuntDeviceEditorDialog(api_object=elm, circuit=self.circuit)
                        if dlg.exec():
                            pass

                    elif elm_type == DeviceType.LoadDevice.value:
                        dlg = LoadDeviceEditorDialog(api_object=elm, circuit=self.circuit)
                        if dlg.exec():
                            pass

                    elif elm_type == DeviceType.GeneratorDevice.value:
                        dlg = GeneratorEditorDialog(api_object=elm, circuit=self.circuit)
                        if dlg.exec():
                            pass

                    elif elm_type == DeviceType.BatteryDevice.value:
                        dlg = GeneratorEditorDialog(api_object=elm, circuit=self.circuit)
                        if dlg.exec():
                            pass

                    elif elm_type == DeviceType.Transformer3WDevice.value:
                        dlg = Transformer3WDeviceEditorDialog(api_object=elm, circuit=self.circuit)
                        if dlg.exec():
                            pass

                    elif elm_type == DeviceType.RmsModelTemplateDevice.value:
                        open_dynamic_editor(api_object=elm, circuit=self.circuit,
                                            preferred_mode=DynamicSimulationMode.RMS)

                    elif elm_type == DeviceType.EmtModelTemplateDevice.value:
                        open_dynamic_editor(api_object=elm, circuit=self.circuit,
                                            preferred_mode=DynamicSimulationMode.EMT)

                    elif elm_type == DeviceType.FmuTemplateDevice.value:
                        dlg = FmuTemplateEditorDialog(
                            circuit=self.circuit,
                            template=elm,
                            project_directory=self.project_directory,
                            parent=self,
                        )
                        if dlg.exec():
                            self.view_objects_data()

                    else:

                        warning_msg('No editor available.\n'
                                    'The values can be changed from the table or '
                                    'via context menus in the graphical interface.',
                                    'Edit')
                else:
                    info_msg('Choose an element from the table')
            else:
                info_msg('Choose an element from the table')
        else:
            info_msg('Select a catalogue element and then a catalogue object')

    def set_value_to_column(self):
        """
        Set the value to all the column
        :return: Nothing
        """
        idx = self.ui.dataStructureTableView.currentIndex()
        mdl: ObjectModelFilterProxy | None = self.get_current_objects_model_view()
        col = idx.column()
        if mdl is not None:
            if col > -1:
                mdl.copy_to_column(idx)
                # update the view
                self.view_objects_data()
            else:
                info_msg('Select some element to serve as source to copy', 'Set value to column')
        else:
            pass

    def highlight_selection_buses(self):
        """
        Highlight and select the buses of the selected objects
        """

        model: ObjectModelFilterProxy | None = self.get_current_objects_model_view()

        if model is not None:

            sel_idx = self.ui.dataStructureTableView.selectedIndexes()
            objects = model.objects

            if len(objects) > 0:

                if len(sel_idx) > 0:

                    unique = set()
                    for idx in sel_idx:
                        unique.add(idx.row())
                    sel_obj = list()
                    for idx in unique:
                        sel_obj.append(objects[idx])

                    elm = objects[0]

                    self.clear_big_bus_markers()
                    color = QtGui.QColor(55, 200, 171, 180)

                    if elm.device_type == DeviceType.BusDevice:

                        self.set_big_bus_marker(buses=sel_obj, color=color)

                    elif elm.device_type in [DeviceType.BranchDevice,
                                             DeviceType.LineDevice,
                                             DeviceType.Transformer2WDevice,
                                             DeviceType.HVDCLineDevice,
                                             DeviceType.VscDevice,
                                             DeviceType.DCLineDevice]:
                        buses = list()
                        for br in sel_obj:
                            buses.append(br.bus_from)
                            buses.append(br.bus_to)
                        self.set_big_bus_marker(buses=buses, color=color)

                    else:
                        buses = list()
                        for elm in sel_obj:
                            buses.append(elm.bus)
                        self.set_big_bus_marker(buses=buses, color=color)

                else:
                    info_msg('Select some elements to highlight', 'Highlight')
            else:
                pass

    def get_objects_time_index(self) -> Union[None, int]:
        """
        Get the time index of the objects slider already
        accounting for the -1 -> None conversion
        :return: None or int
        """
        t_idx = self.ui.db_step_slider.value()
        if t_idx <= -1:
            return None
        else:
            return t_idx

    def highlight_based_on_property(self):
        """
        Highlight and select the buses of the selected objects
        """
        indices = self.ui.dataStructureTableView.selectedIndexes()

        if len(indices):
            model: ObjectModelFilterProxy | None = self.get_current_objects_model_view()

            if model is not None:
                objects = model.objects
                t_idx = self.get_objects_time_index()

                if len(objects) > 0:
                    col_indices = list({index.column() for index in indices})
                    elm = objects[0]
                    attr = model.attributes[col_indices[0]]
                    gc_prop = elm.registered_properties[attr]
                    if gc_prop is None:
                        info_msg(f"The proprty {attr} cannot be found :(", "Highlight based on property")
                        return

                    if gc_prop.tpe in [float, int]:

                        self.clear_big_bus_markers()

                        if elm.device_type == DeviceType.BusDevice:
                            # buses
                            buses = objects
                            values = [elm.get_value(prop=gc_prop, t_idx=t_idx) for elm in objects]

                        elif elm.device_type in [DeviceType.BranchDevice,
                                                 DeviceType.LineDevice,
                                                 DeviceType.DCLineDevice,
                                                 DeviceType.HVDCLineDevice,
                                                 DeviceType.Transformer2WDevice,
                                                 DeviceType.SwitchDevice,
                                                 DeviceType.VscDevice,
                                                 DeviceType.UpfcDevice]:
                            # Branches
                            buses = list()
                            values = list()
                            for br in objects:
                                gc_prop = br.registered_properties[attr]
                                buses.append(br.bus_from)
                                buses.append(br.bus_to)
                                val = elm.get_value(prop=gc_prop, t_idx=t_idx)
                                values.append(val)
                                values.append(val)

                        else:
                            # loads, generators, etc...
                            buses = list()
                            values = list()
                            for elm in objects:
                                gc_prop = elm.registered_properties[attr]
                                val = elm.get_value(prop=gc_prop, t_idx=t_idx)
                                buses.append(elm.bus)
                                values.append(val)

                        # build the color map
                        seq = [(0.0, 'gray'),
                               (0.5, 'orange'),
                               (1, 'red')]
                        cmap = LinearSegmentedColormap.from_list('lcolors', seq)
                        mx = max(values)

                        if mx != 0:

                            colors = np.zeros(len(values), dtype=object)
                            for i, value in enumerate(values):
                                r, g, b, a = cmap(value / mx)
                                colors[i] = QtGui.QColor(r * 255, g * 255, b * 255, a * 255)

                            # color based on the value
                            self.set_big_bus_marker_colours(buses=buses, colors=colors, tool_tips=None)

                        else:
                            info_msg('The maximum value is 0, so the coloring cannot be applied',
                                     'Highlight based on property')
                    else:
                        info_msg('The selected property must be of a numeric type',
                                 'Highlight based on property')

                else:
                    pass

    def assign_to_profile(self):
        """
        Assign the snapshot values at the object DB to the profiles
        """
        indices = self.ui.dataStructureTableView.selectedIndexes()

        if len(indices):
            model: ObjectModelFilterProxy | None = self.get_current_objects_model_view()

            if model is not None:
                logger = bs.Logger()

                t_idx = self.get_objects_time_index()
                attr_list = list()
                for index in indices:
                    i = index.row()
                    p_idx = index.column()
                    elm = model.objects[i]
                    attr = model.attributes[p_idx]
                    gc_prop = elm.registered_properties[attr]
                    attr_list.append(attr)
                    if gc_prop.has_profile():
                        val = elm.get_value(prop=gc_prop, t_idx=t_idx)
                        profile = elm.get_profile_by_prop(prop=gc_prop)
                        profile.fill(val)
                    else:
                        logger.add_error("No profile found for " + attr, device=elm.name)

                if logger.size():
                    logs_window = LogsDialogue("Assign to profile", logger=logger)
                    logs_window.exec()
                else:
                    lst = ", ".join(attr_list)
                    self.show_info_toast(f"{lst} assigned to profile")
        else:
            info_msg("Select a cell or a column first", "Assign to profile")

    def objects_histogram_analysis_plot(self):
        """
        Histogram analysis
        :return:
        """
        if len(self.ui.dataStructuresTreeView.selectedIndexes()) > 0:
            elm_type = self.ui.dataStructuresTreeView.selectedIndexes()[0].data(role=QtCore.Qt.ItemDataRole.DisplayRole)

            if len(self.circuit.get_elements_by_type(device_type=DeviceType(elm_type))):
                object_histogram_analysis(circuit=self.circuit,
                                          object_type=elm_type,
                                          t_idx=self.get_db_slider_index(),
                                          fig=None)
                plt.show()
        else:
            info_msg('Select a data structure')

    def objects_smart_search(self):
        """
        Objects and time series object-based filtering
        :return:
        """

        # gather the model, which for sure is a ExpressionFilterProxy or None
        proxy_mdl: ObjectModelFilterProxy | None = self.get_current_objects_model_view()

        if proxy_mdl is not None:
            if len(proxy_mdl.all_objects) > 0:

                has_err, err_txt = proxy_mdl.setExpression(self.ui.smart_search_lineEdit.text())

                # display time series
                self.display_profiles(proxy_mdl=proxy_mdl)

                # display associations
                self.display_associations(proxy_mdl=proxy_mdl)

                if has_err:
                    self.show_error_toast(err_txt)

            else:
                # nothing to search
                self.show_warning_toast("The collection is empty...")

        else:
            self.show_warning_toast("Nothing to search on, select an object...")

        return None

    def delete_inconsistencies(self):
        """
        Call delete_with_dialogue shit
        :return:
        """
        ok = yes_no_question(
            "This action removes all disconnected devices with no active profile and delete all small islands",
            "Delete inconsistencies")

        if ok:
            logger = self.delete_shit()

            if len(logger) > 0:
                dlg = LogsDialogue("Delete inconsistencies", logger)
                dlg.setModal(True)
                dlg.exec()

    def delete_shit(self, min_island=1):
        """
        Delete small islands, disconnected stuff and other garbage
        """
        numerical_circuit_ = compile_numerical_circuit_at(circuit=self.circuit, )
        islands = numerical_circuit_.split_into_islands()
        logger = bs.Logger()
        buses_to_delete = list()
        buses_to_delete_idx = list()
        for island in islands:
            if island.nbus <= min_island:
                for r in island.original_bus_idx:
                    buses_to_delete.append(self.circuit.buses[r])
                    buses_to_delete_idx.append(r)

        for r, bus in enumerate(self.circuit.buses):
            if not bus.active and not np.any(bus.active_prof.toarray()):
                if r not in buses_to_delete_idx:
                    buses_to_delete.append(bus)
                    buses_to_delete_idx.append(r)

        # delete_with_dialogue the grphics from all diagrams
        self.delete_from_all_diagrams(elements=buses_to_delete)

        for elm in buses_to_delete:
            logger.add_info("Deleted " + str(elm.device_type.value), elm.name)

        # search other elements to delete_with_dialogue
        for dev_lst in [self.circuit.lines,
                        self.circuit.dc_lines,
                        self.circuit.vsc_devices,
                        self.circuit.hvdc_lines,
                        self.circuit.transformers2w,
                        self.circuit.get_generators(),
                        self.circuit.get_loads(),
                        self.circuit.get_shunts(),
                        self.circuit.get_batteries(),
                        self.circuit.get_static_generators()]:

            for elm in dev_lst:
                if not elm.active and not np.any(elm.active_prof.toarray()):
                    self.delete_from_all_diagrams(elements=[elm])
                    logger.add_info("Deleted " + str(elm.device_type.value), elm.name)

        return logger

    def clean_database(self):
        """
        Clean the DataBase
        """

        ok = yes_no_question("This action may delete_with_dialogue unused objects and references, \nAre you sure?",
                             title="DB clean")

        if ok:
            logger = self.circuit.clean()

            if len(logger) > 0:
                dlg = LogsDialogue('DB clean logger', logger)
                dlg.exec()

    def scale(self):
        """
        Show the system scaler window
        The scaler window may modify the circuit
        """
        system_scaler_window = SystemScaler(grid=self.circuit, parent=self)
        system_scaler_window.exec()

    def detect_substations(self):
        """
        Call the detect substations logic
        """

        ok = yes_no_question("Do you want to try to detect substations and voltage levels in the grid model?",
                             "Detect substations")

        if ok:
            val = 1.0 / (10.0 ** self.ui.rxThresholdSpinBox.value())
            detect_substations(grid=self.circuit,
                               r_x_threshold=val)

    def detect_facilities(self):
        """
        Call the detect facilities logic
        """
        ok = yes_no_question("Do you want to try to detect facilities in the grid model?",
                             "Detect facilities")

        if ok:
            detect_facilities(grid=self.circuit)

    def show_objects_context_menu(self, pos: QtCore.QPoint):
        """
        Show diagrams list view context menu
        :param pos: Relative click position
        """
        if len(self.ui.dataStructuresTreeView.selectedIndexes()) > 0:
            sel_item = self.ui.dataStructuresTreeView.selectedIndexes()[0]
            elm_type = sel_item.data(role=QtCore.Qt.ItemDataRole.DisplayRole)

            context_menu = QtWidgets.QMenu(parent=self.ui.diagramsListView)

            gf.add_menu_entry(menu=context_menu,
                              text="Edit",
                              icon_path=":/Icons/icons/edit.png",
                              function_ptr=self.launch_object_editor)

            gf.add_menu_entry(menu=context_menu,
                              text="Add",
                              icon_path=":/Icons/icons/plus.png",
                              function_ptr=self.add_objects)

            gf.add_menu_entry(menu=context_menu,
                              text="Delete",
                              icon_path=":/Icons/icons/minus.png",
                              function_ptr=self.delete_selected_db_table_objects)

            gf.add_menu_entry(menu=context_menu,
                              text="Duplicate object",
                              icon_path=":/Icons/icons/copy.png",
                              function_ptr=self.duplicate_selected_db_table_objects)

            gf.add_menu_entry(menu=context_menu,
                              text="Merge",
                              icon_path=":/Icons/icons/fusion.png",
                              function_ptr=self.fuse_selected_db_table_objects)

            gf.add_menu_entry(menu=context_menu,
                              text="Copy idtag",
                              icon_path=":/Icons/icons/copy.png",
                              function_ptr=self.copy_selected_idtag)

            gf.add_menu_entry(menu=context_menu,
                              text="Crop model to buses selection",
                              icon_path=":/Icons/icons/schematic.png",
                              function_ptr=self.crop_model_to_buses_selection)

            gf.add_menu_entry(menu=context_menu,
                              text="Grid reduction",
                              icon_path=":/Icons/icons/schematic.png",
                              function_ptr=self.grid_reduction_from_table_selection)

            gf.add_menu_entry(menu=context_menu,
                              text="Copy table",
                              icon_path=":/Icons/icons/copy.png",
                              function_ptr=self.copy_objects_data)

            gf.add_menu_entry(menu=context_menu,
                              text="Set value to column",
                              icon_path=":/Icons/icons/copy2down.png",
                              function_ptr=self.set_value_to_column)

            gf.add_menu_entry(menu=context_menu,
                              text="Assign to profile",
                              icon_path=":/Icons/icons/assign_to_profile.png",
                              function_ptr=self.assign_to_profile)

            if elm_type == DeviceType.BranchGroupDevice.value:
                gf.add_menu_entry(menu=context_menu,
                                  text="Colour branches like this",
                                  icon_path=":/Icons/icons/assign_to_profile.png",
                                  function_ptr=self.colour_branches_like_group)

            context_menu.addSeparator()

            gf.add_menu_entry(menu=context_menu,
                              text="New vicinity diagram",
                              icon_path=":/Icons/icons/grid_icon.png",
                              function_ptr=self.add_bus_vicinity_diagram_from_model)

            gf.add_menu_entry(menu=context_menu,
                              text="New diagram from selection",
                              icon_path=":/Icons/icons/schematicadd_to.png",
                              function_ptr=self.add_new_bus_diagram_from_selection)

            gf.add_menu_entry(menu=context_menu,
                              text="Add to current diagram",
                              icon_path=":/Icons/icons/schematicadd_to.png",
                              function_ptr=self.add_objects_to_current_diagram)

            gf.add_menu_entry(menu=context_menu,
                              text="Highlight buses selection",
                              icon_path=":/Icons/icons/highlight.png",
                              function_ptr=self.highlight_selection_buses)

            gf.add_menu_entry(menu=context_menu,
                              text="Highlight based on property",
                              icon_path=":/Icons/icons/highlight2.png",
                              function_ptr=self.highlight_based_on_property)

            context_menu.addSeparator()

            gf.add_menu_entry(menu=context_menu,
                              text="New map from selection",
                              icon_path=":/Icons/icons/map.png",
                              function_ptr=self.add_new_map_from_database_selection)

            # Convert global position to local position of the list widget
            mapped_pos = self.ui.dataStructureTableView.viewport().mapToGlobal(pos)
            context_menu.exec(mapped_pos)

        else:
            pass

    def add_substation_with_wizard(self):
        """
        Add substation with all its objects using a wizard
        :return:
        """

        # Get selected buses from the current diagram if any
        selected_buses_tuples = self.get_diagram_selected_buses()
        buses_to_replace = [bus for _, bus, _ in selected_buses_tuples] if selected_buses_tuples else None

        kv = self.get_default_voltage()
        dlg = SubstationDesigner(grid=self.circuit, default_voltage=kv)
        dlg.exec()
        if dlg.was_ok():

            se_object, voltage_levels = substation_wizards.create_substation(
                grid=self.circuit,
                se_name=dlg.get_name(),
                se_code=dlg.get_code(),
                lat=dlg.get_latitude(),
                lon=dlg.get_longitude(),
                vl_templates=dlg.get_voltage_levels(),
                buses_to_replace=buses_to_replace
            )

            dlg3 = CustomQuestionDialogue(title="New substation",
                                          question="How do you want to represent the merged grid?",
                                          answer1="Create new diagram",
                                          answer2="Add to current diagram")
            dlg3.exec()

            if dlg3.accepted_answer == 1:
                # Create a blank diagram and add to it
                self.new_bus_branch_diagram_from_substation(substations=[se_object])

            elif dlg3.accepted_answer == 2:
                self.add_substation_to_current_diagram(substations=[se_object])

            else:
                # not imported
                return

    def search_ts_point(self):
        """
        Search time step point
        """

        txt = self.ui.goToTsPointComboBox.currentText()
        mode: TimeSeriesSearchPoint = self.ts_search_points_dict[txt]

        if mode == TimeSeriesSearchPoint.LowestLoad:

            total = np.zeros(self.circuit.get_time_number())
            for elm in self.circuit.loads:
                total += elm.P_prof.toarray()

            if len(total) > 0:
                try:
                    idx = np.argmin(total)
                except ValueError:
                    self.show_error_toast(f"{mode.value} could not be found")
                    return

                self.ui.db_step_slider.setValue(idx)
            else:
                self.show_warning_toast("No time steps to navigate to")

        elif mode == TimeSeriesSearchPoint.HighestLoad:

            total = np.zeros(self.circuit.get_time_number())
            for elm in self.circuit.loads:
                total += elm.P_prof.toarray()

            if len(total) > 0:
                try:
                    idx = np.argmax(total)
                except ValueError:
                    self.show_error_toast(f"{mode.value} could not be found")
                    return

                self.ui.db_step_slider.setValue(idx)
            else:
                self.show_warning_toast("No time steps to navigate to")

        else:
            return

    def set_model_x_y_based_on_lat_lon(self):
        """
        Change values of x,y in the database using the latitude and longitude of the buses
        :return:
        """
        ok = yes_no_question(text="Setting the database buses x,y position from their latitude and longitude "
                                  "values will change the buses values but not the current diagrams. "
                                  "New diagrams will use the new values",
                             title="")

        if ok:
            logger = self.circuit.fill_xy_from_lat_lon()

            if logger.has_logs():
                self.show_logs(logger=logger, name="set (x,y) from (lat, lon)")
            else:
                self.show_info_toast("x, y changed!")

    def restore_investments(self):
        """
        Restore investments to the circuit
        :return:
        """
        ok = yes_no_question(text="This action will restore the circuit to the state before the last investment "
                                  "modification. Do you want to proceed?",
                             title="Restore investments")

        if ok:
            self.circuit.restore_investments()
            for diagram_widget in self.diagram_widgets_list:
                if isinstance(diagram_widget, SchematicWidget):
                    diagram_widget.recolour_mode()
                else:
                    # map widgets and other diagram types do not encode active state
                    # via dashed/solid pen styling, so they have nothing to refresh
                    pass

            # re-apply result-based colouring on top of the active-state styling
            self.colour_diagrams()
            self.show_info_toast("Investments restored!")

        return None