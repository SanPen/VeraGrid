# VeraGrid GUI Main Module: src/VeraGrid/Gui/Main/SubClasses/base_gui.py

- Original source path: `src/VeraGrid/Gui/Main/SubClasses/base_gui.py`
- Knowledge kind: generated GUI/Main code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 2

## Function: terminate_thread(thread)

Terminates a python thread from another thread.

## Function: traverse_objects(name, obj, lst, i)

:param name:

## Class: BaseMainGui

- Bases: QMainWindow
- Summary: DiagramFunctionsMain

### Methods

- `LOCK(self, val)`
  Summary: Lock the interface to prevent new simulation launches
- `UNLOCK(self)`
  Summary: Unlock the interface
- `multiverse(self)`
  Summary: No docstring provided.
- `multiverse(self, val)`
  Summary: No docstring provided.
- `circuit(self)`
  Summary: No docstring provided.
- `circuit(self, val)`
  Summary: No docstring provided.
- `file_name(self)`
  Summary: Get the current file name
- `file_name(self, val)`
  Summary: Set the current file name
- `collect_memory()`
  Summary: Collect memory
- `get_simulation_threads(self)`
  Summary: Get all threads that has to do with simulation
- `get_process_threads(self)`
  Summary: Get all threads that has to do with processing
- `get_all_threads(self)`
  Summary: Get all threads
- `stop_all_threads(self)`
  Summary: Stop all running threads
- `any_thread_running(self)`
  Summary: Checks if any thread is running
- `clear_stuff_running(self)`
  Summary: This clears the list of stuff running right now
- `get_all_objects_in_memory(self)`
  Summary: Get a list of the objects in memory
- `expand_object_tree_nodes(self)`
  Summary: Expand objects' tree nodes
- `get_simulation_start(self)`
  Summary: Get the start simulation index
- `get_simulation_end(self)`
  Summary: Get the end simulation index
- `setup_sim_indices(self, st, en)`
  Summary: Set the simulation indices
- `get_diagram_slider_index(self)`
  Summary: Get the diagram slider value
- `get_db_slider_index(self)`
  Summary: Get the db slider value
- `setup_time_sliders(self)`
  Summary: Setup the time sliders
- `update_date_dependent_combos(self)`
  Summary: update the drop down menus that display dates
- `update_from_to_list_views(self)`
  Summary: Update the exchange area, countries, etc... dependent combos
- `fix_generators_active_based_on_the_power(self, ask_before)`
  Summary: set the generators active based on the active power values
- `fix_loads_active_based_on_the_power(self, ask_before)`
  Summary: set the loads active based on the active power values
- `get_preferred_engine(self)`
  Summary: Get the currently selected engine
- `about_box(self)`
  Summary: Display about box
- `ai_config_file_path()`
  Summary: Return the AI configuration file path.
- `find_first_gguf_file(self, directory_path)`
  Summary: Find the first GGUF file in a directory in lexicographic order.
- `build_default_ai_backend_state(self)`
  Summary: Build the default AI backend state for the main window.
- `build_ai_config_data(self)`
  Summary: Build the persistable AI configuration dictionary.
- `apply_ai_config_data(self, data)`
  Summary: Apply persisted AI configuration data.
- `save_ai_config(self)`
  Summary: Save the AI configuration to disk.
- `load_ai_config(self)`
  Summary: Load the AI configuration from disk.
- `ensure_ai_dialogue(self)`
  Summary: Create the floating AI dialogue lazily and bind it to the live main window.
- `sync_ai_dialogue_action_state(self, visible)`
  Summary: Synchronize the floating dialogue visibility with the toolbar/menu action state.
- `refresh_ai_context_if_available(self)`
  Summary: Refresh the AI dialogue context when the floating window exists.
- `handle_ai_dialogue_visibility_changed(self, visible)`
  Summary: Keep the AI action state synchronized with the persistent floating dialogue.
- `shutdown_ai_dialogue_if_available(self)`
  Summary: Stop the AI worker thread when the dialogue exists.
- `set_ai_dialogue_visible(self, visible)`
  Summary: Show or hide the floating AI dialogue.
- `open_ai_chat_dialogue(self)`
  Summary: Open the AI dialogue connected to the live VeraGrid main window.
- `show_online_docs()`
  Summary: Open the online documentation in a web browser
- `report_a_bug()`
  Summary: Open the online github issues in a web browser
- `auto_rate_branches(self)`
  Summary: Rate the Branches that do not have rate
- `detect_transformers(self)`
  Summary: Detect which Branches are transformers
- `set_cancel_state(self)`
  Summary: Cancel what ever's going on that can be cancelled
- `display_grid_analysis(self)`
  Summary: Display the grid analysis GUI
- `change_circuit_base(self)`
  Summary: Update the circuit base values from the UI
- `change_circuit_name(self)`
  Summary: :return:
- `get_snapshot_circuit(self)`
  Summary: Get a snapshot compilation
- `numerical_circuit(self)`
  Summary: get the snapshot NumericalCircuit
- `islands(self)`
  Summary: get the snapshot islands
- `initialize_contingencies(self)`
  Summary: Launch the contingency planner to initialize the contingencies
- `show_toast(self, message, duration)`
  Summary: Show generic toast
- `show_error_toast(self, message, duration)`
  Summary: Show error toast
- `show_warning_toast(self, message, duration)`
  Summary: Show warning toast
- `show_info_toast(self, message, duration)`
  Summary: Show info toast
- `get_clustering_results(self)`
  Summary: Get the clustering results if available
