# VeraGrid GUI Main Module: src/VeraGrid/Gui/Main/SubClasses/Settings/configuration.py

- Original source path: `src/VeraGrid/Gui/Main/SubClasses/Settings/configuration.py`
- Knowledge kind: generated GUI/Main code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 2

## Function: gui_struct_to_data(data_, struct_)

Recursive function to get the config dictionary from the GUI values

## Function: config_data_to_struct(data_, struct_)

Recursive function to set the GUI objects' values from the config dictionary

## Class: ConfigurationMain

- Bases: ResultsMain
- Summary: Diagrams Main

### Methods

- `change_theme_mode(self)`
  Summary: Change the GUI theme
- `config_file_path()`
  Summary: get the config file path
- `config_file_exists(self)`
  Summary: Check if the config file exists
- `get_config_structure(self)`
  Summary: Get the settings configuration dictionary
- `get_gui_config_data(self)`
  Summary: Get a dictionary with the GUI configuration data
- `save_gui_config(self)`
  Summary: Save the GUI configuration
- `apply_gui_config(self, data)`
  Summary: Apply GUI configuration dictionary
- `load_gui_config(self)`
  Summary: Load GUI configuration from the local user folder
- `snapshot_datetime_changed(self)`
  Summary: Upon change of the snapshot datetime, change the circuit snapshot datetime
- `add_plugins(self)`
  Summary: Add the plugins information and create the menu entries
- `launch_plugin(self, fcn)`
  Summary: Action wrapper to launch the plugin
