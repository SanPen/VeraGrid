# VeraGridEngine Module: src/VeraGridEngine/Devices/multi_circuit.py

- Original source path: `src/VeraGridEngine/Devices/multi_circuit.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 2
- Representative imports: __future__, os, cmath, copy, numpy, pandas, typing, uuid, networkx, matplotlib, scipy.sparse, VeraGridEngine, VeraGridEngine.Devices.assets, VeraGridEngine.Devices.Parents.editable_device, VeraGridEngine.basic_structures, VeraGridEngine.Devices

## Function: get_system_user()

Get the system mac + user name

## Function: get_fused_device_lst(elm_list, property_names)

Fuse all the devices of a list by adding their selected properties

## Class: MultiCircuit

- Bases: Assets
- Summary: The concept of circuit should be easy enough to understand. It represents a set of

### Methods

- `to_dict(self)`
  Summary: Create grid configuration data
- `parse(self, data)`
  Summary: Parse grid configuration data
- `valid_for_simulation(self)`
  Summary: Checks if the data could be simulated
- `get_template_objects_list(self)`
  Summary: get objects_with_profiles in the form of list
- `get_template_objects_str_dict(self)`
  Summary: get objects_with_profiles as a strings dictionary
- `get_bus_default_types(self)`
  Summary: Return an array of bus types
- `get_dimensions(self)`
  Summary: Get the three dimensions of the circuit: number of buses, number of Branches, number of time steps
- `get_branch_active_time_array(self)`
  Summary: Get branch active matrix
- `get_topologic_group_dict(self)`
  Summary: Get numerical circuit time groups
- `copy(self)`
  Summary: Returns a deep (true) copy of this circuit.
- `build_graph(self)`
  Summary: Returns a networkx DiGraph object of the grid.
- `build_graph_real_power_flow(self, current_flow)`
  Summary: Returns a networkx DiGraph object of the grid.
- `apply_all_branch_types(self)`
  Summary: Apply all the branch types
- `convert_line_to_hvdc(self, line)`
  Summary: Convert a line to HVDC, this is the GUI way to create HVDC objects
- `convert_line_to_transformer(self, line)`
  Summary: Convert a line to Transformer
- `convert_generator_to_battery(self, gen)`
  Summary: Convert a generator to battery
- `convert_line_to_vsc(self, line)`
  Summary: Convert a line to voltage source converter
- `convert_line_to_upfc(self, line)`
  Summary: Convert a line to voltage source converter
- `convert_line_to_series_reactance(self, line)`
  Summary: Convert a line to voltage source converter
- `convert_line_to_switch(self, line)`
  Summary: Convert a line to voltage source converter
- `convert_fluid_path_to_line(self, fluid_path)`
  Summary: Convert a line to voltage source converter
- `convert_hvdc_line_to_vsc_system(self, hvdc_line)`
  Summary: Convert a HvdcLine to the corresponding VSC-DcLine-VSC system
- `plot_graph(self, ax)`
  Summary: Plot the grid.
- `export_pf(self, file_name, power_flow_results)`
  Summary: Export power flow results to file.
- `export_profiles(self, file_name)`
  Summary: Export object profiles to file.
- `set_state(self, t)`
  Summary: Set the profiles state at the index t as the default values.
- `get_snapshot_time_str(self)`
  Summary: Get the snapshot datetime as a string
- `get_bus_branch_dict(self)`
  Summary: Get the branch-bus dictionary
- `get_bus_branch_connectivity_matrix(self)`
  Summary: Get the branch-bus connectivity
- `get_adjacent_matrix(self)`
  Summary: Get the bus adjacent matrix
- `get_adjacent_buses(A, bus_idx)`
  Summary: Return array of indices of the buses adjacent to the bus given by it's index
- `get_center_location(self)`
  Summary: Get the mean coordinates of the system (lat, lon)
- `snapshot_balance(self)`
  Summary: Creates a report DataFrame with the snapshot active power balance
- `scale_power(self, factor)`
  Summary: Modify the loads and generators
- `get_automatic_precision(self)`
  Summary: Get the precision that simulates correctly the power flow
- `fill_xy_from_lat_lon(self, destructive, factor, remove_offset)`
  Summary: fill the x and y value from the latitude and longitude values
- `fill_lat_lon_from_xy(self, destructive, factor, offset_x, offset_y)`
  Summary: Convert the coordinates to some random lat lon
- `import_bus_lat_lon(self, df, bus_col, lat_col, lon_col)`
  Summary: Import the buses' latitude and longitude
- `get_bus_area_indices(self)`
  Summary: Get array of area indices for each bus
- `get_areas_buses(self, areas)`
  Summary: Get the selected buses
- `get_zone_buses(self, zones)`
  Summary: Get the selected buses
- `get_country_buses(self, countries)`
  Summary: Get the selected buses
- `get_aggregation_buses(self, aggregations)`
  Summary: Get the selected buses
- `get_inter_areas_branches(self, a1, a2)`
  Summary: Get the inter-area Branches. HVDC Branches are not considered
- `get_inter_buses_branches(self, a1, a2)`
  Summary: Get the inter-buses Branches. HVDC Branches are not considered
- `get_inter_areas_hvdc_branches(self, a1, a2)`
  Summary: Get the inter-area Branches
- `get_inter_buses_hvdc_branches(self, a1, a2)`
  Summary: Get the inter-area Branches
- `get_inter_areas_vsc_branches(self, a1, a2)`
  Summary: Get the inter-area VSC
- `get_inter_buses_vsc_branches(self, a1, a2)`
  Summary: Get the inter-area VSC
- `get_inter_zone_branches(self, z1, z2)`
  Summary: Get the inter-area Branches
- `get_branch_area_connectivity_matrix(self, a1, a2)`
  Summary: Get the inter area connectivity matrix
- `get_branch_areas_info(self)`
  Summary: Get the area-branches information
- `get_inter_aggregation_info(self, objects_from, objects_to)`
  Summary: Get the lists that help defining the inter area objects
- `change_base(self, Sbase_new)`
  Summary: Change the elements base impedance
- `get_injection_devices_grouped_by_substation(self)`
  Summary: Get the injection devices grouped by bus and by device type
- `get_injection_devices_grouped_by_bus(self)`
  Summary: Get the injection devices grouped by bus and by device type
- `get_injection_devices_grouped_by_fluid_node(self)`
  Summary: Get the injection devices grouped by bus and by device type
- `get_injection_devices_grouped_by_group_type(self, group_type)`
  Summary: Get the injection devices grouped by bus and by device type
- `compose_bus_blocks(self)`
  Summary: this function returns a dictionary with keys, the device bus, mand values, a block containing all the rms models of the elements connected to that bus.
- `get_batteries_by_bus(self)`
  Summary: Get the injection devices grouped by bus and by device type
- `get_substation_buses(self, substation)`
  Summary: Get the list of buses of this substation
- `get_substations_set_from_grouping(self, selected_objects)`
  Summary: Get substation from place
- `fuse_devices(self)`
  Summary: Fuse all the different devices in a node to a single device per node
- `set_generators_active_profile_from_their_active_power(self)`
  Summary: Modify the generators active profile to match the active power profile
- `set_batteries_active_profile_from_their_active_power(self)`
  Summary: Modify the batteries active profile to match the active power profile
- `set_loads_active_profile_from_their_active_power(self)`
  Summary: Modify the loads active profile to match the active power profile
- `get_voltage_guess(self)`
  Summary: Get the buses stored voltage guess
- `get_Sbus(self, apply_active)`
  Summary: Get the complex bus power Injections
- `get_Sbus_prof(self, apply_active)`
  Summary: Get the complex bus power Injections
- `get_Pgen(self, apply_active)`
  Summary: Get the complex bus power Injections
- `get_Pload(self, apply_active)`
  Summary: Get the complex bus power Injections
- `get_Sbus_prof_fixed(self, apply_active)`
  Summary: Get the complex bus power Injections considering those devices that cannot be dispatched
- `get_Sbus_prof_dispatchable(self, apply_active)`
  Summary: Get the complex bus power Injections only considering those devices that can be dispatched
- `get_Pbus(self, apply_active)`
  Summary: Get snapshot active power array per bus
- `get_Pbus_prof(self, apply_active)`
  Summary: Get profiles active power per bus
- `get_imbalance(self, apply_active)`
  Summary: Get the system imbalance in per unit
- `get_branch_rates_prof(self, add_hvdc, add_vsc, add_switch)`
  Summary: Get the complex bus power Injections
- `get_branch_rates(self, add_hvdc, add_vsc, add_switch)`
  Summary: Get the complex bus power Injections
- `get_branch_contingency_rates_prof(self, add_hvdc, add_vsc, add_switch)`
  Summary: Get the complex bus power Injections
- `get_branch_contingency_rates(self, add_hvdc, add_vsc, add_switch)`
  Summary: Get the complex bus power Injections
- `get_gen_fuel_rates_sparse_matrix(self)`
  Summary: Get the fuel rates matrix with relation to the generators
- `get_gen_emission_rates_sparse_matrix(self)`
  Summary: Get the emission rates matrix with relation to the generators
- `get_gen_technology_connectivity_matrix(self)`
  Summary: Get the technology connectivity matrix with relation to the generators
- `get_batt_technology_connectivity_matrix(self)`
  Summary: Get the technology connectivity matrix with relation to the generators
- `set_investments_status(self, investments_list, status, all_elements_dict)`
  Summary: Set the active (and active profile) status of a list of investments' objects
- `merge_buses(self, bus1, bus2)`
  Summary: Transfer the injection elements' associations from bus2 to bus 1
- `compare_circuits(self, grid2, detailed_profile_comparison, skip_internals, tolerance)`
  Summary: Compare this circuit with another circuits for equality
- `differentiate_circuits(self, base_grid, detailed_profile_comparison, force_second_pass)`
  Summary: Compare this circuit with another circuits for equality
- `add_circuit(self, new_grid, re_id_new_grid)`
  Summary: Add a circuit to this circuit, keeping all elements (this is not equal to a circuit merge)
- `merge_circuit(self, new_grid)`
  Summary: Add a circuit to this circuit, keeping all elements (this is not equal to a circuit merge)
- `clean_branches(self, bus_set, logger)`
  Summary: Clean the branch references
- `clean_injections(self, bus_set, logger)`
  Summary: Clean the branch references
- `clean_contingencies(self, all_dev, logger)`
  Summary: Clean the contingencies and contingency groups
- `clean_remedial_actions(self, all_dev, logger)`
  Summary: Clean the remedial actons and remedial actons groups
- `clean_investments(self, all_dev, logger)`
  Summary: Clean the investments and investment groups
- `clean_technologies(self)`
  Summary: Clean the technology associations to deleted technologies
- `clean(self)`
  Summary: Clean dead references
- `split_line(self, original_line, position, extra_km)`
  Summary: :param original_line:
- `split_line_int_out(self, original_line, position, km_io)`
  Summary: Split line with in/out
- `add_catalogue(self, data)`
  Summary: Add the catalogue from another circuit
- `set_opf_ts_results(self, results)`
  Summary: Assign OptimalPowerFlowTimeSeriesResults to the objects
- `set_opf_snapshot_results(self, results)`
  Summary: Assign OptimalPowerFlowResults to the objects
- `get_reduction_sets(self, reduction_bus_indices, add_vsc, add_hvdc, add_switch)`
  Summary: Generate the set of bus indices for grid reduction
- `get_buses_from_objects(self, elements, dtype)`
  Summary: Returns set of buses belonging to the list elements
- `get_topology_data(self, t_idx)`
  Summary: Get the topology data
- `move_behind_converter(self, api_object)`
  Summary: :param api_object:
- `slice_buses(self, buses)`
  Summary: Get a subset of the grid
- `check_rms_models(self)`
  Summary: This function checks that a device has a valid rms model
- `check_emt_models(self)`
  Summary: This function checks that a device has a valid emt model
