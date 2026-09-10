# VeraGrid GUI Main Module: src/VeraGrid/Gui/Main/VeraGridMain.py

- Original source path: `src/VeraGrid/Gui/Main/VeraGridMain.py`
- Knowledge kind: generated GUI/Main code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 3

## Class: VeraGridMainGUI

- Bases: ScriptingMain
- Summary: MainGUI

### Methods

- `global_delete(self)`
  Summary: Function to dispatch what to do when [supr] is pressed
- `save_all_config(self)`
  Summary: Save all configuration files needed
- `load_all_config(self)`
  Summary: Load all configuration files needed
- `closeEvent(self, event)`
  Summary: Close event

## Function: create_linux_desktop_entry(app_name, qrc_icon_path)

Create a .desktop entry for a PySide app using a resource icon (":/path/to/icon.svg").

## Function: check_all_svgs()

Iterate through all resources registered by icons_rc and check SVG validity.

## Function: runVeraGrid()

Main function to run the GUI
