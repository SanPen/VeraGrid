# VeraGrid GUI Main Module: src/VeraGrid/Gui/Main/SubClasses/Model/diagrams.py

- Original source path: `src/VeraGrid/Gui/Main/SubClasses/Model/diagrams.py`
- Knowledge kind: generated GUI/Main code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 0

## Class: VideoExportWorker

- Bases: QtCore.QThread
- Summary: VideoExportWorker

### Methods

- `run(self)`
  Summary: Run function

## Class: DiagramsMain

- Bases: CompiledArraysMain
- Summary: Diagrams Main

### Methods

- `get_current_objects_model_view(self)`
  Summary: Get the current ObjectModelFilterProxy from the GUI
- `get_selected_db_table_objects(self)`
  Summary: Get the list of selected objects
- `get_default_voltage(self)`
  Summary: Get the default marked voltage
- `auto_layout(self)`
  Summary: Automatic layout of the nodes
- `bigger_nodes(self)`
  Summary: Move the nodes more separated
- `smaller_nodes(self)`
  Summary: Move the nodes closer
- `center_nodes(self)`
  Summary: Center the nodes in the screen
- `get_diagram_selected_buses(self)`
  Summary: Get the selected buses
- `get_current_diagram_buses(self)`
  Summary: Get the selected buses
- `get_current_diagram_substations(self)`
  Summary: Get the selected buses
- `explosion_factor_change(self)`
  Summary: Change the node explosion factor
- `zoom_in(self)`
  Summary: Zoom the diagram in
- `zoom_out(self)`
  Summary: Zoom the diagram out
- `edit_time_interval(self)`
  Summary: Run the simulation limits adjust window
- `pf_colouring(self, diagram_widget, results, cmap, use_flow_based_width, min_branch_width, max_branch_width, min_bus_width, max_bus_width)`
  Summary: :param diagram_widget:
- `pf_3ph_colouring(self, diagram_widget, results, cmap, use_flow_based_width, min_branch_width, max_branch_width, min_bus_width, max_bus_width)`
  Summary: :param diagram_widget:
- `se_colouring(self, diagram_widget, results, cmap, use_flow_based_width, min_branch_width, max_branch_width, min_bus_width, max_bus_width)`
  Summary: :param diagram_widget:
- `pf_ts_colouring(self, t_idx, diagram_widget, results, cmap, use_flow_based_width, min_branch_width, max_branch_width, min_bus_width, max_bus_width)`
  Summary: :param t_idx:
- `cpf_colouring(self, diagram_widget, results, cmap, use_flow_based_width, min_branch_width, max_branch_width, min_bus_width, max_bus_width)`
  Summary: :param diagram_widget:
- `spf_colouring(self, diagram_widget, results, cmap, use_flow_based_width, min_branch_width, max_branch_width, min_bus_width, max_bus_width)`
  Summary: :param diagram_widget:
- `sc_colouring(self, diagram_widget, results, cmap, use_flow_based_width, min_branch_width, max_branch_width, min_bus_width, max_bus_width, sc_index)`
  Summary: :param diagram_widget:
- `opf_colouring(self, diagram_widget, results, cmap, use_flow_based_width, min_branch_width, max_branch_width, min_bus_width, max_bus_width)`
  Summary: :param diagram_widget:
- `opf_ts_colouring(self, t_idx, diagram_widget, results, cmap, use_flow_based_width, min_branch_width, max_branch_width, min_bus_width, max_bus_width)`
  Summary: :param t_idx:
- `ntc_colouring(self, diagram_widget, results, cmap, use_flow_based_width, min_branch_width, max_branch_width, min_bus_width, max_bus_width)`
  Summary: :param diagram_widget:
- `ntc_ts_colouring(self, t_idx, diagram_widget, results, cmap, use_flow_based_width, min_branch_width, max_branch_width, min_bus_width, max_bus_width)`
  Summary: :param t_idx:
- `nc_ts_colouring(self, t_idx, diagram_widget, results, cmap, use_flow_based_width, min_branch_width, max_branch_width, min_bus_width, max_bus_width)`
  Summary: :param t_idx:
- `linpf_colouring(self, diagram_widget, results, cmap, use_flow_based_width, min_branch_width, max_branch_width, min_bus_width, max_bus_width)`
  Summary: :param diagram_widget:
- `linpf_ts_colouring(self, t_idx, diagram_widget, results, cmap, use_flow_based_width, min_branch_width, max_branch_width, min_bus_width, max_bus_width)`
  Summary: :param t_idx:
- `con_colouring(self, diagram_widget, results, cmap, use_flow_based_width, min_branch_width, max_branch_width, min_bus_width, max_bus_width)`
  Summary: :param diagram_widget:
- `con_ts_colouring(self, t_idx, diagram_widget, results, cmap, use_flow_based_width, min_branch_width, max_branch_width, min_bus_width, max_bus_width)`
  Summary: :param t_idx:
- `default_colouring(self, t_idx, diagram_widget, cmap, use_flow_based_width, min_branch_width, max_branch_width, min_bus_width, max_bus_width)`
  Summary: :param t_idx:
- `grid_colour_function(self, diagram_widget, current_study, t_idx, allow_popups)`
  Summary: Colour the schematic or the map
- `colour_diagrams(self, allow_popups)`
  Summary: Color the grid now
- `re_colour_schematic(self)`
  Summary: Recolour a schematic
- `set_diagrams_list_view(self)`
  Summary: Create the diagrams' list view
- `get_selected_diagram_widget(self)`
  Summary: Get the currently selected diagram
- `create_blank_schematic_diagram(self, name)`
  Summary: Create a new schematic widget
- `redraw_current_diagram(self)`
  Summary: Redraw the currently selected diagram
- `set_selected_diagram_on_click(self)`
  Summary: on list-view click, set the currently selected diagram widget
- `add_complete_bus_branch_diagram_now(self, name)`
  Summary: Add a general bus-branch diagram
- `add_complete_bus_branch_diagram(self)`
  Summary: Add a general bus-branch diagram
- `new_bus_branch_diagram_from_selection(self)`
  Summary: Add a bus-branch diagram of a particular selection of objects
- `add_bus_vicinity_diagram_from_model(self)`
  Summary: Add a bus vicinity diagram
- `new_bus_branch_diagram_from_bus(self, root_bus)`
  Summary: Add a bus-branch diagram of a particular selection of objects
- `new_bus_branch_diagram_from_substation(self, substations)`
  Summary: Add a bus-branch diagram of a particular selection of objects
- `add_substation_to_current_diagram(self, substations)`
  Summary: Add a bus-branch diagram of a particular selection of objects
- `create_circuit_stored_diagrams(self)`
  Summary: Create as Widgets the diagrams stored in the circuit
- `add_map_diagram(self)`
  Summary: Adds a Map diagram
- `add_diagram_widget_and_diagram(self, diagram_widget, diagram)`
  Summary: Add diagram widget, it also adds the diagram to the circuit for later
- `remove_diagram(self)`
  Summary: Remove diagram
- `duplicate_diagram(self)`
  Summary: Duplicate the selected diagram
- `remove_all_diagrams(self)`
  Summary: Remove all diagrams and their widgets
- `remove_all_diagram_widgets(self)`
  Summary: Remove all diagram widgets from the container
- `set_diagram_widget(self, widget)`
  Summary: Set the current diagram in the container
- `plot_style_change(self)`
  Summary: Change the style
- `diagrams_time_slider_change(self)`
  Summary: After releasing the time slider, do something
- `update_diagram_time_slider_texts(self)`
  Summary: Update the slider text label as it is moved
- `objects_time_slider_change(self)`
  Summary: After releasing the time slider, do something
- `objects_diagram_time_slider_texts(self)`
  Summary: Update the slider text label as it is moved
- `take_picture(self)`
  Summary: Save the schematic
- `record_video(self)`
  Summary: Save the schematic
- `post_video_export(self)`
  Summary: :return:
- `set_xy_from_lat_lon(self)`
  Summary: Get the x, y coordinates of the buses from their latitude and longitude
- `set_big_bus_marker(self, buses, color)`
  Summary: Set a big marker at the selected buses
- `set_big_bus_marker_colours(self, buses, colors, tool_tips)`
  Summary: Set a big marker at the selected buses with the matching colours
- `clear_big_bus_markers(self)`
  Summary: Clear big markers at the selected buses
- `delete_selected_from_the_diagram(self)`
  Summary: Prompt to delete_with_dialogue the selected buses from the current diagram
- `delete_selected_diagram_widgets(self)`
  Summary: Prompt to delete the selected elements from the current diagram and (optionally) the database
- `try_to_fix_buses_location(self)`
  Summary: Try to fix the location of the buses
- `get_selected_devices(self)`
  Summary: Get the selected investment devices
- `add_selected_to_contingency(self)`
  Summary: Add contingencies from the schematic selection
- `add_selected_to_remedial_action(self)`
  Summary: Add contingencies from the schematic selection
- `add_selected_to_investment(self)`
  Summary: Add contingencies from the schematic selection
- `add_rms_event_to_selected(self)`
  Summary: Add rms event to a selected device
- `add_short_circuit_events(self)`
  Summary: :return:
- `select_buses_by_property(self, prop)`
  Summary: Select the current diagram buses by prop
- `select_buses_by(self)`
  Summary: Select buses by...
- `set_selected_bus_property(self, prop)`
  Summary: :param prop:
- `color_buses_by(self)`
  Summary: Launch the bus coloring
- `color_substations_by(self)`
  Summary: Launch substation coloring
- `default_voltage_change(self)`
  Summary: When the default voltage changes, update all the diagrams
- `delete_from_all_diagrams(self, elements)`
  Summary: Delete elements from all editors
- `search_diagram(self)`
  Summary: Search elements by name, code or idtag and center them in the screen
- `show_diagrams_context_menu(self, pos)`
  Summary: Show diagrams list view context menu
- `disable_all_results_tags(self)`
  Summary: Disable all tags for the selected diagram
- `enable_all_results_tags(self)`
  Summary: Enable all tags for the selected diagram
- `call_delete_db_element(self, caller, api_obj)`
  Summary: This function is meant to be a master delete_with_dialogue function that is passed to each diagram
- `set_diagrams_size_constraints(self)`
  Summary: Set the size constraints
- `set_diagrams_palette(self)`
  Summary: Set the size constraints
- `set_diagrams_map_tile_provider(self)`
  Summary: Set the size constraints
- `consolidate_diagram_coordinates(self)`
  Summary: Consolidate the diagram coordinates into the DB
- `select_buses_from_substation(self, substation)`
  Summary: :param substation:
- `combinations_tree_clicked(self)`
  Summary: On combinations tree click
- `reset_diagram_coordinates(self)`
  Summary: Reset the diagram coordinates using the DB
- `rotate(self)`
  Summary: Rotate the selected diagram
- `preset_1(self)`
  Summary: Country sizes
- `preset_2(self)`
  Summary: Region sizes
- `preset_3(self)`
  Summary: Municipality sizes
- `preset_4(self)`
  Summary: Street sizes
- `set_diagram_branches_reticular_style(self)`
  Summary: Set all branches drawing mode to reticular
- `set_diagram_branches_straight_style(self)`
  Summary: Set all branches drawing mode to straight
