# VeraGrid GUI Main Module: src/VeraGrid/Gui/Main/SubClasses/io.py

- Original source path: `src/VeraGrid/Gui/Main/SubClasses/io.py`
- Knowledge kind: generated GUI/Main code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0

## Class: IoMain

- Bases: ScenariosMain
- Summary: Inputs-Outputs Main

### Methods

- `dragEnterEvent(self, event)`
  Summary: :param event:
- `dragMoveEvent(self, event)`
  Summary: :param event:
- `dropEvent(self, event)`
  Summary: Drop file on the GUI, the default behaviour is to load the file
- `new_project_now(self, create_default_diagrams)`
  Summary: New project right now without asking questions
- `new_project(self)`
  Summary: Create new grid
- `open_file(self)`
  Summary: Open VeraGrid file
- `open_file_threaded(self, post_function, allow_diff_file_format, title)`
  Summary: Open file from a Qt thread to remain responsive
- `open_file_now(self, filenames, post_function, bool_prompt_to_ask_if_unclear)`
  Summary: Open a file without questions
- `post_open_file(self)`
  Summary: Actions to perform after a file has been loaded
- `install_plugin_now(self, file_name)`
  Summary: Install plugin
- `select_csv_file(self, caption)`
  Summary: Select a CSV file
- `import_circuit(self)`
  Summary: Prompt to add another circuit
- `post_import_circuit(self)`
  Summary: Stuff to do after opening another circuit
- `export_circuit_differential(self)`
  Summary: Prompt to export a diff of this circuit and a base one
- `save_file_as(self)`
  Summary: Save this file as...
- `save_file(self)`
  Summary: Save the circuit case to a file
- `get_file_save_options(self)`
  Summary: Compose the file saving options
- `save_file_now(self, filename, type_selected, grid, options)`
  Summary: Save the file right now, without questions
- `post_file_save(self)`
  Summary: Actions after the threaded file save
- `grid_generator(self)`
  Summary: Open the grid generator window
- `import_bus_coordinates(self)`
  Summary: :return:
- `export_object_profiles(self)`
  Summary: Export object profiles
- `export_all(self)`
  Summary: Export all the results
- `post_export_all(self)`
  Summary: Actions post export all
- `export_simulation_data(self)`
  Summary: Export the calculation objects to file
- `load_results_driver(self)`
  Summary: Load a driver from disk
- `import_contingencies(self)`
  Summary: Open file to import contingencies file
- `export_contingencies(self)`
  Summary: Export contingencies
- `add_default_catalogue(self)`
  Summary: Add default catalogue to circuit
- `load_custom_catalogue(self)`
  Summary: Load a catalogue file and add it to the current one
- `save_custom_catalogue(self)`
  Summary: Save the current catalogue
- `set_circuit(self, grid, create_diagram)`
  Summary: :param grid:
- `export_psse(self)`
  Summary: :return:
- `export_power_factory(self)`
  Summary: :return:
- `export_cim(self)`
  Summary: :return:
- `export_cgmes(self)`
  Summary: :return:
- `export_power_grid_models(self)`
  Summary: :return:
- `export_json(self)`
  Summary: :return:
- `export_h5(self)`
  Summary: :return:
- `export_excel(self)`
  Summary: :return:
- `export_sqlite(self)`
  Summary: :return:
