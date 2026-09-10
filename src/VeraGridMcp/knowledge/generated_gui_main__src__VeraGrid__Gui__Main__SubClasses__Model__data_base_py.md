# VeraGrid GUI Main Module: src/VeraGrid/Gui/Main/SubClasses/Model/data_base.py

- Original source path: `src/VeraGrid/Gui/Main/SubClasses/Model/data_base.py`
- Knowledge kind: generated GUI/Main code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0

## Class: DataBaseTableMain

- Bases: DiagramsMain
- Summary: Diagrams Main

### Methods

- `setup_objects_tree(self)`
  Summary: Setup the database left tree object
- `setup_compiled_arrays_tree(self)`
  Summary: :return:
- `create_objects_model(self, elements, elm_type)`
  Summary: Generate the objects' table model
- `display_profiles(self, proxy_mdl)`
  Summary: Display profile
- `display_associations(self, proxy_mdl)`
  Summary: Display the association table
- `on_associations_combo_box_change(self)`
  Summary: Triggered on self.ui.associationsComboBox.currentTextChanged
- `copy_objects_data(self)`
  Summary: Copy the current displayed objects table to the clipboard
- `get_db_object_selected_type(self)`
  Summary: Get the selected object type in the database tree view
- `get_selected_objects_model(self)`
  Summary: Get the selected objects' model
- `view_objects_data(self)`
  Summary: On click, display the objects' properties
- `get_selected_table_buses(self)`
  Summary: Get the list of selected buses, regardless of the object table type
- `get_selected_table_substations(self)`
  Summary: Get the substations matching the table selection
- `delete_selected_db_table_objects(self)`
  Summary: Delete selection from the database main table
- `duplicate_selected_db_table_objects(self)`
  Summary: Delete selection
- `fuse_selected_db_table_objects(self)`
  Summary: Fuse selection
- `copy_selected_idtag(self)`
  Summary: Copy selected idtags
- `add_objects_to_current_diagram(self)`
  Summary: Add selected DB objects to current diagram
- `add_new_bus_diagram_from_selection(self)`
  Summary: Create a New diagram from a buses selection
- `add_new_map_from_database_selection(self)`
  Summary: Create a New map from a buses selection
- `crop_model_to_buses_selection(self)`
  Summary: Crop model to buses selection
- `grid_reduction_from_table_selection(self)`
  Summary: Crop model to buses selection
- `grid_reduction_from_schematic_selection(self)`
  Summary: Call the grid reduction dialogue on the schematic selection
- `add_objects(self)`
  Summary: Add default objects objects
- `colour_branches_like_group(self)`
  Summary: Colour the branches like the branch group
- `launch_object_editor(self)`
  Summary: Edit catalogue element
- `set_value_to_column(self)`
  Summary: Set the value to all the column
- `highlight_selection_buses(self)`
  Summary: Highlight and select the buses of the selected objects
- `get_objects_time_index(self)`
  Summary: Get the time index of the objects slider already
- `highlight_based_on_property(self)`
  Summary: Highlight and select the buses of the selected objects
- `assign_to_profile(self)`
  Summary: Assign the snapshot values at the object DB to the profiles
- `objects_histogram_analysis_plot(self)`
  Summary: Histogram analysis
- `objects_smart_search(self)`
  Summary: Objects and time series object-based filtering
- `delete_inconsistencies(self)`
  Summary: Call delete_with_dialogue shit
- `delete_shit(self, min_island)`
  Summary: Delete small islands, disconnected stuff and other garbage
- `clean_database(self)`
  Summary: Clean the DataBase
- `scale(self)`
  Summary: Show the system scaler window
- `detect_substations(self)`
  Summary: Call the detect substations logic
- `detect_facilities(self)`
  Summary: Call the detect facilities logic
- `show_objects_context_menu(self, pos)`
  Summary: Show diagrams list view context menu
- `add_substation_with_wizard(self)`
  Summary: Add substation with all its objects using a wizard
- `search_ts_point(self)`
  Summary: :return:
