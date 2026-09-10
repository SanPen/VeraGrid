# VeraGrid GUI Main Module: src/VeraGrid/Gui/Main/SubClasses/Model/scenarios.py

- Original source path: `src/VeraGrid/Gui/Main/SubClasses/Model/scenarios.py`
- Knowledge kind: generated GUI/Main code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0

## Class: ScenariosMain

- Bases: ConfigurationMain
- Summary: Scenarios Main

### Methods

- `circuit(self)`
  Summary: No docstring provided.
- `circuit(self, val)`
  Summary: No docstring provided.
- `get_selected_scenario_index(self)`
  Summary: Get the currently selected QModelIndex from the tree view.
- `get_selected_scenario_node(self)`
  Summary: Get the currently selected ScenarioNode from the tree view.
- `prompt_scenario_name(self, title, default_name)`
  Summary: Prompt the user to enter a scenario name using a dialog.
- `show_scenario_tree_context_menu(self, pos)`
  Summary: Display context menu for scenario tree operations.
- `add_child_scenario(self)`
  Summary: Add a child scenario to the selected scenario node.
- `remove_scenario(self)`
  Summary: Remove the selected scenario node and its subtree.
- `merge_children_into_scenario(self)`
  Summary: Merge all direct child scenarios into the selected scenario.
- `reload_diagrams_for_active_scenario(self)`
  Summary: Rebuild the diagram widgets from the currently active scenario circuit.
- `rename_scenario(self)`
  Summary: Rename the selected scenario node.
- `commit_scenario(self)`
  Summary: Commit the currently active scenario node, persisting its edits into the stored
- `set_as_current_scenario(self)`
  Summary: Set the selected scenario as the current working scenario.
