# VeraGrid GUI Main Module: src/VeraGrid/Gui/Main/SubClasses/Results/results.py

- Original source path: `src/VeraGrid/Gui/Main/SubClasses/Results/results.py`
- Knowledge kind: generated GUI/Main code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0

## Class: ResultsMain

- Bases: SimulationsMain
- Summary: Diagrams Main

### Methods

- `results_tree_view_click(self, index)`
  Summary: Display the simulation results on the result's table
- `dynamic_results_tree_view_click(self, index)`
  Summary: Resolve the clicked dynamics tree node into an RMS variable.
- `dynamic_results_tree_view_dbl_click(self, index)`
  Summary: :param index:
- `dynamic_plots_tree_view_dbl_click(self, index)`
  Summary: Plot the selected plots-tree entry on double click.
- `dynamic_plots_tree_view_click(self, index)`
  Summary: On dynamics plot tree click...
- `expand_dynamic_plots_tree(self, parent, first, last)`
  Summary: Expand the dynamics plots tree after inserting rows.
- `add_dynamic_plot_group(self)`
  Summary: Create a new dynamics plot group.
- `delete_dynamic_plot_entry(self)`
  Summary: Delete the selected dynamics plot group or variable.
- `plot_dynamic_plot_entry(self)`
  Summary: Plot the selected dynamics plot group or variable.
- `search_dynamic_objects(self)`
  Summary: Filter the dynamics tree view using the text entered by the user.
- `plot_results(self)`
  Summary: Plot the results
- `save_results_df(self)`
  Summary: Save the data displayed at the results as excel
- `copy_results_data(self)`
  Summary: Copy the current displayed profiles to the clipboard
- `copy_results_data_as_numpy(self)`
  Summary: Copy the current displayed profiles to the clipboard
- `search_in_results(self)`
  Summary: Search in the results model
- `delete_results_driver(self)`
  Summary: Delete the driver
- `copy_opf_to_profiles(self)`
  Summary: Copy the results from the OPF snapshot and time series to the database
- `save_results_logs(self)`
  Summary: Save the results' logs
