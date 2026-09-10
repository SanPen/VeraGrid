# VeraGrid GUI Main Module: src/VeraGrid/Gui/Main/SubClasses/simulations.py

- Original source path: `src/VeraGrid/Gui/Main/SubClasses/simulations.py`
- Knowledge kind: generated GUI/Main code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0

## Class: SimulationsMain

- Bases: TimeEventsMain
- Summary: SimulationsMain

### Methods

- `get_simulations(self)`
  Summary: Get all threads that have to do with simulation
- `get_available_drivers(self)`
  Summary: Get a list of all the available results' objects
- `get_time_indices(self)`
  Summary: Get an array of indices of the time steps selected within the start-end interval
- `modify_ui_options_according_to_the_engine(self)`
  Summary: Change the UI depending on the engine options
- `modify_contingency_filter_mode(self)`
  Summary: Modify the objects
- `get_contingency_groups_matching_the_filter(self)`
  Summary: Get the list of contingencies that match the group
- `valid_time_series(self)`
  Summary: Check if there are valid time series
- `add_simulation(self, val)`
  Summary: Add a simulation to the simulations list
- `remove_simulation(self, val)`
  Summary: Remove a simulation from the simulations list
- `clear_results(self)`
  Summary: Clear the results tab
- `get_investments_combination_tree_model(drv)`
  Summary: Get the investments combination tree model
- `get_short_circuits_combination_tree_model(drv)`
  Summary: Get the investments combination tree model
- `fill_combinations_tree(self, drv)`
  Summary: Fill the tree driver
- `changed_study(self)`
  Summary: :return:
- `update_available_results(self)`
  Summary: Update the results that are displayed in the results tab
- `get_compatible_from_to_buses_and_inter_branches(self)`
  Summary: Get the lists that help defining the inter area objects
- `get_selected_power_flow_options(self)`
  Summary: Gather power flow run options
- `get_selected_rms_simulation_options(self)`
  Summary: Gather rms simulation run options
- `get_selected_rms_small_signal_stability_options(self)`
  Summary: Gather RMS SmallSignal simulation run options
- `get_selected_emt_simulation_options(self)`
  Summary: Gather EMT simulation run options
- `get_selected_emt_small_signal_stability_options(self)`
  Summary: Gather EMT SmallSignal simulation run options
- `get_opf_results(self, use_opf)`
  Summary: Get the current OPF results
- `get_opf_ts_results(self, use_opf)`
  Summary: Get the current OPF time series results
- `ts_flag(self)`
  Summary: Is the time series flag enabled?
- `power_flow_dispatcher(self)`
  Summary: Dispatch the power flow action
- `power_flow_3ph_dispatcher(self)`
  Summary: Dispatch the power flow action
- `optimal_power_flow_dispatcher(self)`
  Summary: Dispatch the optimal power flow action
- `atc_dispatcher(self)`
  Summary: Dispatch the NTC action
- `optimal_ntc_opf_dispatcher(self)`
  Summary: Dispatch the optimal NTC action
- `linear_pf_dispatcher(self)`
  Summary: Dispatch the linear power flow action
- `contingencies_dispatcher(self)`
  Summary: Dispatch the contingencies action
- `reliability_dispatcher(self)`
  Summary: Dispatch the reliability action
- `rms_dispatcher(self)`
  Summary: Dispatch the reliability action
- `emt_dispatcher(self)`
  Summary: Dispatch the reliability action
- `rms_small_signal_dispatcher(self)`
  Summary: Dispatch the reliability action
- `emt_small_signal_dispatcher(self)`
  Summary: Dispatch the reliability action
- `run_power_flow(self)`
  Summary: Run a power flow simulation
- `run_power_flow_3ph(self)`
  Summary: Run a power flow simulation
- `post_power_flow(self)`
  Summary: Action performed after the power flow.
- `run_power_flow3ph(self)`
  Summary: Run a power flow simulation
- `post_power_flow3ph(self)`
  Summary: Action performed after the power flow.
- `get_se_options(self)`
  Summary: :return:
- `run_state_estimation(self)`
  Summary: Run a power flow simulation
- `post_state_estimation(self)`
  Summary: Action performed after the power flow.
- `run_short_circuit(self)`
  Summary: Run a short circuit simulation
- `post_short_circuit(self)`
  Summary: Action performed after the short circuit.
- `get_linear_options(self)`
  Summary: Get the LinearAnalysisOptions defined by the GUI
- `run_linear_analysis(self)`
  Summary: Run a Power Transfer Distribution Factors analysis
- `post_linear_analysis(self)`
  Summary: Action performed after the short circuit.
- `run_linear_analysis_ts(self)`
  Summary: Run PTDF time series simulation
- `post_linear_analysis_ts(self)`
  Summary: Action performed after the short circuit.
- `get_contingency_options(self)`
  Summary: :return:
- `run_contingency_analysis(self)`
  Summary: Run a Power Transfer Distribution Factors analysis
- `post_contingency_analysis(self)`
  Summary: Action performed after the short circuit.
- `run_contingency_analysis_ts(self)`
  Summary: Run a Power Transfer Distribution Factors analysis
- `post_contingency_analysis_ts(self)`
  Summary: Action performed after the short circuit.
- `run_available_transfer_capacity(self)`
  Summary: Run a Power Transfer Distribution Factors analysis
- `post_available_transfer_capacity(self)`
  Summary: Action performed after the short circuit.
- `run_available_transfer_capacity_ts(self, use_clustering)`
  Summary: Run a Power Transfer Distribution Factors analysis
- `post_available_transfer_capacity_ts(self)`
  Summary: Action performed after the short circuit.
- `run_continuation_power_flow(self)`
  Summary: Run voltage stability (voltage collapse) in a separated thread
- `post_continuation_power_flow(self)`
  Summary: Actions performed after the voltage stability. Launched by the thread after its execution
- `run_power_flow_time_series(self)`
  Summary: Run a time series power flow simulation in a separated thread from the gui
- `post_power_flow_time_series(self)`
  Summary: Events to do when the time series simulation has finished
- `run_stochastic(self)`
  Summary: Run a Monte Carlo simulation
- `post_stochastic(self)`
  Summary: Actions to perform after the Monte Carlo simulation is finished
- `post_cascade(self, idx)`
  Summary: Actions to perform after the cascade simulation is finished
- `get_opf_options(self)`
  Summary: Get the GUI OPF options
- `run_opf(self)`
  Summary: Run OPF simulation
- `post_opf(self)`
  Summary: Actions to run after the OPF simulation
- `run_opf_time_series(self)`
  Summary: OPF Time Series run
- `post_opf_time_series(self)`
  Summary: Post OPF Time Series
- `get_opf_ntc_options(self)`
  Summary: :return:
- `run_opf_ntc(self)`
  Summary: Run OPF simulation
- `post_opf_ntc(self)`
  Summary: Actions to run after the OPF simulation
- `run_opf_ntc_ts(self)`
  Summary: Run OPF NTC time series simulation
- `post_opf_ntc_ts(self)`
  Summary: Actions to run after the optimal net transfer capacity time series simulation
- `run_find_node_groups(self)`
  Summary: Run the node groups algorithm
- `post_run_find_node_groups(self)`
  Summary: Colour the grid after running the node grouping
- `run_inputs_analysis(self)`
  Summary: :return:
- `post_inputs_analysis(self)`
  Summary: :return:
- `storage_location(self)`
  Summary: Add storage markers to the schematic
- `run_sigma_analysis(self)`
  Summary: Run the sigma analysis
- `run_investments_evaluation(self)`
  Summary: Run investments evaluation
- `post_investments_evaluation(self)`
  Summary: Post investments evaluation
- `run_clustering(self)`
  Summary: Run a clustering analysis
- `post_clustering(self)`
  Summary: Action performed after the short circuit.
- `fuse_devices(self)`
  Summary: Fuse the devices per node into a single device per category
- `activate_clustering(self)`
  Summary: When activating the use of clustering, also activate time series
- `get_nodal_capacity_options(self)`
  Summary: Get the nodal capacity options
- `run_nodal_capacity(self)`
  Summary: OPF Time Series run
- `post_nodal_capacity(self)`
  Summary: Post OPF Time Series
- `run_reliability(self)`
  Summary: Run reliability study
- `post_reliability(self)`
  Summary: :return:
- `run_rms(self)`
  Summary: Run rms simulation
- `post_rms(self)`
  Summary: :return:
- `run_emt(self)`
  Summary: Run rms simulation
- `post_emt(self)`
  Summary: :return:
- `automatic_pf_precision(self)`
  Summary: Find the automatic tolerance
- `run_remote(self, instruction)`
  Summary: Run remote simulation
- `post_run_remote(self, driver_idtag)`
  Summary: Function executed upon data reception complete
- `run_rms_small_signal_stability(self)`
  Summary: Run small signal simulation
- `post_rms_small_signal_stability(self)`
  Summary: :return:
- `run_emt_small_signal_stability(self)`
  Summary: Run small signal simulation
- `post_emt_small_signal_stability(self)`
  Summary: :return:
- `update_available_mip_solvers(self)`
  Summary: :return:
- `procedural_grid_expansion(self)`
  Summary: :return:
