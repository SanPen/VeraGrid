# VeraGrid GUI Main Module: src/VeraGrid/Gui/Main/dynamics_results_handler.py

- Original source path: `src/VeraGrid/Gui/Main/dynamics_results_handler.py`
- Knowledge kind: generated GUI/Main code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 5
- Top-level function count: 6

## Function: _build_tree_item(text)

Build a non-editable tree item.

## Function: _get_device_type_label(device_tpe)

Get the label that represents a device type.

## Function: _get_device_label(device)

Get the label that represents a device instance.

## Function: _get_var_label(variable)

Get the label that represents a simulation variable.

## Function: _set_item_icon(item, icon_key)

Set the item icon from the shared device-type icon dictionary.

## Class: DynamicsPlotGroup

- Bases: none
- Summary: Group of variables to be plotted together.

### Methods

- `get_name(self)`
  Summary: Get the plot-group name.
- `set_name(self, name)`
  Summary: Set the plot-group name.
- `get_vars(self)`
  Summary: Get the variables stored in the group.
- `contains_var(self, variable)`
  Summary: Check whether a variable already belongs to the group.
- `add_var(self, variable)`
  Summary: Add a variable to the group.
- `remove_var(self, variable)`
  Summary: Remove a variable from the group.

## Class: DynamicsPlotGroups

- Bases: none
- Summary: Collection of plot groups with explicit CRUD operations.

### Methods

- `get_groups(self)`
  Summary: Get the stored plot groups.
- `get_group(self, name)`
  Summary: Get one plot group by name.
- `create_group(self, name)`
  Summary: Create a new plot group.
- `delete_group(self, name)`
  Summary: Delete a plot group.
- `rename_group(self, old_name, new_name)`
  Summary: Rename an existing group.

## Class: DynamicsDeviceTreeModel

- Bases: QtGui.QStandardItemModel
- Summary: Source tree model that exports dragged variables.

### Methods

- `flags(self, index)`
  Summary: Get the Qt flags for an item.
- `mimeTypes(self)`
  Summary: Get the supported mime types.
- `supportedDragActions(self)`
  Summary: Get the supported drag actions.
- `mimeData(self, indexes)`
  Summary: Build mime data from the selected variable item.

## Class: DynamicsPlotsTreeModel

- Bases: QtGui.QStandardItemModel
- Summary: Target tree model that accepts dropped variables into plot groups.

### Methods

- `flags(self, index)`
  Summary: Get the Qt flags for a plots-tree item.
- `mimeTypes(self)`
  Summary: Get the supported mime types.
- `supportedDropActions(self)`
  Summary: Get the supported drop actions.
- `dropMimeData(self, data, action, row, column, parent)`
  Summary: Handle dropping one variable into a plot group.

## Function: build_dynamics_tree_model(tree_data, var_role, mime_type)

Build the source tree-view model for RMS dynamics results.

## Class: DynamicsResultsHandler

- Bases: none
- Summary: Prepare GUI structures from RMS dynamics results.

### Methods

- `get_group_name_role(self)`
  Summary: Get the Qt role used to store plot-group names in the plots tree.
- `get_drag_mime_type(self)`
  Summary: Get the mime type used for dynamics-variable drag-and-drop.
- `get_view_model(self)`
  Summary: Get the proxy model used by the dynamics device tree view.
- `get_plots_model(self)`
  Summary: Get the model used by the dynamics plots tree view.
- `set_search_text(self, search_text)`
  Summary: Update the proxy-model filter with the given search text.
- `map_to_source(self, index)`
  Summary: Map a view index from the proxy model back to the source device-tree model.
- `get_var_from_index(self, index)`
  Summary: Get the RMS variable associated with a clicked device-tree index.
- `get_plot_group_name_from_index(self, index)`
  Summary: Get the plot-group name represented by a plots-tree index.
- `get_group_name_from_drop_index(self, index)`
  Summary: Resolve the plot-group name targeted by a drop operation.
- `get_plot_var_from_index(self, index)`
  Summary: Get the variable represented by a plots-tree index.
- `rebuild_plots_model(self)`
  Summary: Rebuild the plots-tree model from the plot-group domain objects.
- `_build_next_group_name(self)`
  Summary: Build the next default plot-group name.
- `get_next_group_name(self)`
  Summary: Get the next available default plot-group name.
- `create_plot_group(self, name)`
  Summary: Create a plot group and refresh the plots tree.
- `delete_plot_group(self, group_name)`
  Summary: Delete one plot group and refresh the plots tree.
- `add_var_to_group(self, group_name, var_uid)`
  Summary: Add one variable to a plot group and refresh the plots tree.
- `remove_var_from_group(self, group_name, var_uid)`
  Summary: Remove one variable from a plot group and refresh the plots tree.
- `delete_plot_entry_from_index(self, index)`
  Summary: Delete the selected group or variable from the plots tree.
- `plot_var(self, var, group_name)`
  Summary: Plot one variable for one RMS events group.
- `plot_group(self, plot_group_name, rms_group_name)`
  Summary: Plot all variables stored in one plot group.
- `plot_entry_from_index(self, index, rms_group_name)`
  Summary: Plot the selected plots-tree entry.
- `get_data_from_plot_index(self, index, rms_group_name)`
  Summary: :param index:
