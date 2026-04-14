# VeraGridEngine Module: src/VeraGridEngine/Devices/assets.py

- Original source path: `src/VeraGridEngine/Devices/assets.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 1
- Representative imports: __future__, warnings, numpy, pandas, typing, datetime, VeraGridEngine.basic_structures, VeraGridEngine.Devices, VeraGridEngine.Templates, VeraGridEngine.Devices.types, VeraGridEngine.Devices.Parents.editable_device, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, VeraGridEngine.data_logger

## Function: add_devices_list(original_list, new_list)

Add a list of devices to another keeping coherence

## Class: Assets

- Bases: none
- Summary: Class to store the assets

### Methods

- `item_types(self)`
  Summary: Iterator of all the objects in the MultiCircuit
- `template_items(self)`
  Summary: Iterator of the declared objects in the MultiCircuit.
- `items(self)`
  Summary: Iterator of all the objects in the MultiCircuit
- `get_time_number(self)`
  Summary: Return the number of buses
- `get_time_array(self)`
  Summary: Get the time array
- `time_profile(self)`
  Summary: Get the time array
- `time_profile(self, value)`
  Summary: Set the time array
- `get_all_time_indices(self)`
  Summary: Get array with all the time steps
- `has_time_series(self)`
  Summary: Area there time series?
- `get_unix_time(self)`
  Summary: Get the unix time representation of the time
- `set_unix_time(self, arr)`
  Summary: Set the time with a unix time
- `get_time_deltas_in_hours(self)`
  Summary: Get the time increments in hours
- `get_time_profile_as_list(self)`
  Summary: Get the profiles dictionary
- `re_index_time(self, year, hours_per_step)`
  Summary: Generate sequential time steps to correct the time_profile
- `re_index_time2(self, t0, step_size, step_unit)`
  Summary: Generate sequential time steps to correct the time_profile
- `create_profiles(self, steps, step_length, step_unit, time_base)`
  Summary: Set the default profiles in all the objects enabled to have profiles.
- `format_profiles(self, index)`
  Summary: Format the profiles in place using a time index.
- `set_time_profile(self, unix_data)`
  Summary: Set unix array as time array
- `ensure_profiles_exist(self)`
  Summary: Format the pandas profiles in place using a time index.
- `delete_profiles(self)`
  Summary: Delete the time profiles
- `resample_profiles(self, indices)`
  Summary: resample the given profiles to the indices
- `resample_profiles2(self, t0, t1)`
  Summary: Resample profiles
- `get_snapshot_time_unix(self)`
  Summary: Get the unix representation of the snapshot time
- `set_snapshot_time_unix(self, val)`
  Summary: Convert unix datetime to python datetime
- `snapshot_time(self)`
  Summary: Returns the current snapshot time
- `snapshot_time(self, val)`
  Summary: No docstring provided.
- `rms_var_factory(self)`
  Summary: Get the RMS VarFactory object
- `rms_var_factory(self, value)`
  Summary: No docstring provided.
- `emt_var_factory(self)`
  Summary: Get the EMT VarFactory object
- `emt_var_factory(self, value)`
  Summary: No docstring provided.
- `lines(self)`
  Summary: get list of ac lines
- `lines(self, value)`
  Summary: No docstring provided.
- `get_lines_number(self)`
  Summary: :return:
- `get_lines(self)`
  Summary: get list of ac lines
- `add_line(self, obj, logger)`
  Summary: Add a line object
- `delete_line(self, obj)`
  Summary: Delete line
- `dc_lines(self)`
  Summary: get list of dc lines
- `dc_lines(self, value)`
  Summary: No docstring provided.
- `get_dc_lines(self)`
  Summary: :return:
- `add_dc_line(self, obj)`
  Summary: Add a line object
- `delete_dc_line(self, obj)`
  Summary: Delete line
- `transformers2w(self)`
  Summary: Get list of transformers
- `transformers2w(self, value)`
  Summary: No docstring provided.
- `get_transformers2w(self)`
  Summary: get list of 2-winding transformers
- `get_transformers2w_number(self)`
  Summary: get the number of 2-winding transformers
- `get_transformers2w_names(self)`
  Summary: get a list of names of the 2-winding transformers
- `add_transformer2w(self, obj)`
  Summary: Add a transformer object
- `delete_transformer2w(self, obj)`
  Summary: Delete transformer
- `hvdc_lines(self)`
  Summary: Get list of hvdc lines
- `hvdc_lines(self, value)`
  Summary: No docstring provided.
- `get_hvdc(self)`
  Summary: :return:
- `get_hvdc_number(self)`
  Summary: :return:
- `get_hvdc_names(self)`
  Summary: :return:
- `get_hvdc_actives(self, t_idx)`
  Summary: get a vector of actives
- `add_hvdc(self, obj)`
  Summary: Add a hvdc line object
- `delete_hvdc_line(self, obj)`
  Summary: Delete HVDC line
- `get_hvdc_dict(self)`
  Summary: Get dictionary of HVDC lines
- `get_hvdc_index_dict(self)`
  Summary: Get dictionary of HVDC lines
- `vsc_devices(self)`
  Summary: Get list of vsc devices
- `vsc_devices(self, value)`
  Summary: No docstring provided.
- `get_vsc(self)`
  Summary: :return:
- `get_vsc_number(self)`
  Summary: :return:
- `get_vsc_names(self)`
  Summary: Get Vsc names
- `get_vsc_actives(self, t_idx)`
  Summary: get a vector of actives
- `add_vsc(self, obj)`
  Summary: Add a hvdc line object
- `delete_vsc_converter(self, obj)`
  Summary: Delete VSC
- `get_vsc_dict(self)`
  Summary: Get dictionary of VSC converters
- `get_vsc_index_dict(self)`
  Summary: Get index dictionary of VSC lines
- `upfc_devices(self)`
  Summary: Get list of upfc devices
- `upfc_devices(self, value)`
  Summary: No docstring provided.
- `get_upfc(self)`
  Summary: :return:
- `add_upfc(self, obj)`
  Summary: Add a UPFC object
- `delete_upfc_converter(self, obj)`
  Summary: Delete VSC
- `switch_devices(self)`
  Summary: Get list of switch devices
- `switch_devices(self, value)`
  Summary: No docstring provided.
- `get_switches(self)`
  Summary: :return:
- `get_switches_number(self)`
  Summary: :return:
- `add_switch(self, obj)`
  Summary: Add a Switch object
- `delete_switch(self, obj)`
  Summary: Delete transformer
- `transformers3w(self)`
  Summary: Get list of 3W transformers
- `transformers3w(self, value)`
  Summary: No docstring provided.
- `get_transformers3w(self)`
  Summary: :return:
- `get_transformers3w_number(self)`
  Summary: :return:
- `get_transformers3w_names(self)`
  Summary: :return:
- `add_transformer3w(self, obj, add_middle_bus)`
  Summary: Add a transformer object
- `delete_transformer3w(self, obj)`
  Summary: Delete transformer
- `windings(self)`
  Summary: Get list of windings
- `windings(self, value)`
  Summary: No docstring provided.
- `get_windings(self)`
  Summary: :return:
- `get_windings_number(self)`
  Summary: :return:
- `get_windings_names(self)`
  Summary: :return:
- `add_winding(self, obj)`
  Summary: Add a winding object
- `delete_winding(self, obj)`
  Summary: Delete winding
- `series_reactances(self)`
  Summary: Get list of series reactances
- `series_reactances(self, value)`
  Summary: No docstring provided.
- `get_series_reactances(self)`
  Summary: List of series_reactances
- `get_series_reactances_number(self)`
  Summary: Size of the list of series_reactances
- `get_series_reactance_at(self, i)`
  Summary: Get series_reactance at i
- `get_series_reactance_names(self)`
  Summary: Array of series_reactance names
- `add_series_reactance(self, obj)`
  Summary: Add a SeriesReactance object
- `delete_series_reactance(self, obj)`
  Summary: Add a SeriesReactance object
- `buses(self)`
  Summary: Get list of buses
- `buses(self, value)`
  Summary: No docstring provided.
- `get_bus_number(self)`
  Summary: Return the number of buses
- `get_buses(self)`
  Summary: List of buses
- `get_bus_at(self, i)`
  Summary: List of buses
- `get_bus_names(self)`
  Summary: List of bus names
- `get_bus_dict(self, by_idtag)`
  Summary: Return dictionary of buses
- `get_bus_index_dict(self)`
  Summary: Return dictionary of buses
- `get_bus_idtag_index_dict(self)`
  Summary: Return dictionary of buses
- `get_bus_actives(self, t_idx)`
  Summary: get a vector of actives
- `add_bus(self, obj)`
  Summary: Add a :ref:`Bus<bus>` object to the grid.
- `delete_bus(self, obj, delete_associated)`
  Summary: Delete a :ref:`Bus<bus>` object from the grid.
- `delete_branches_with_sets(self, buses_to_remove, delete_associated)`
  Summary: Delete branch objects that may contain contingencies, remedial actions, or investments
- `delete_buses(self, lst, delete_associated)`
  Summary: Delete a :ref:`Bus<bus>` object from the grid.
- `get_buses_by(self, filter_elements)`
  Summary: Get a list of buses that can be found in the list of Areas | Zones | Countries
- `get_bus_devices(self, bus)`
  Summary: Get the list of associated branches and the list of associated injections
- `bus_bars(self)`
  Summary: Get the list of BusBars
- `bus_bars(self, value)`
  Summary: No docstring provided.
- `get_bus_bars(self)`
  Summary: Get all bus bars
- `get_bus_bars_number(self)`
  Summary: Get all bus-bars number
- `add_bus_bar(self, obj)`
  Summary: Add Substation
- `delete_bus_bar(self, obj)`
  Summary: Delete Substation
- `voltage_levels(self)`
  Summary: Get voltage level devices list
- `voltage_levels(self, value)`
  Summary: No docstring provided.
- `get_voltage_levels(self)`
  Summary: List of voltage_levels
- `get_voltage_levels_number(self)`
  Summary: Size of the list of voltage_levels
- `get_voltage_level_at(self, i)`
  Summary: Get voltage_level at i
- `get_voltage_level_names(self)`
  Summary: Array of voltage_level names
- `add_voltage_level(self, obj)`
  Summary: Add a VoltageLevel object
- `delete_voltage_level(self, obj)`
  Summary: Add a VoltageLevel object
- `get_voltage_level_buses(self, vl)`
  Summary: Get the list of buses of this substation
- `loads(self)`
  Summary: Get list of loads
- `loads(self, value)`
  Summary: No docstring provided.
- `get_loads(self)`
  Summary: Returns a list of :ref:`Load<load>` objects in the grid.
- `get_loads_number(self)`
  Summary: Returns a list of :ref:`Load<load>` objects in the grid.
- `get_load_names(self)`
  Summary: Returns a list of :ref:`Load<load>` names.
- `add_load(self, bus, api_obj)`
  Summary: Add a load device
- `delete_load(self, obj)`
  Summary: Delete a load
- `generators(self)`
  Summary: Get list of generators
- `generators(self, value)`
  Summary: No docstring provided.
- `get_generators(self)`
  Summary: Returns a list of :ref:`Generator<generator>` objects in the grid.
- `get_generators_number(self)`
  Summary: Get the number of generators
- `get_generator_names(self)`
  Summary: Returns a list of :ref:`Generator<generator>` names.
- `add_generator(self, bus, api_obj)`
  Summary: Add a generator
- `delete_generator(self, obj)`
  Summary: Delete a generator
- `get_generator_indexing_dict(self)`
  Summary: Get a dictionary that relates the generator uuid's with their index
- `get_generator_bus_index_dict(self, bus_index_dict)`
  Summary: Get a dictionary of generators related to their bus index
- `external_grids(self)`
  Summary: Get list of external grids
- `external_grids(self, value)`
  Summary: No docstring provided.
- `get_external_grids(self)`
  Summary: Returns a list of :ref:`ExternalGrid<external_grid>` objects in the grid.
- `get_external_grids_number(self)`
  Summary: Returns a list of :ref:`ExternalGrid<external_grid>` objects in the grid.
- `get_external_grid_names(self)`
  Summary: Returns a list of :ref:`ExternalGrid<external_grid>` names.
- `add_external_grid(self, bus, api_obj)`
  Summary: Add an external grid
- `delete_external_grid(self, obj)`
  Summary: Delete a external grid
- `shunts(self)`
  Summary: Get list of shunts
- `shunts(self, value)`
  Summary: No docstring provided.
- `get_shunts(self)`
  Summary: Returns a list of :ref:`Shunt<shunt>` objects in the grid.
- `get_shunts_number(self)`
  Summary: Get the number of shunts
- `get_shunt_names(self)`
  Summary: Returns a list of :ref:`Shunt<shunt>` names.
- `add_shunt(self, bus, api_obj)`
  Summary: Add a :ref:`Shunt<shunt>` object to a :ref:`Bus<bus>`.
- `delete_shunt(self, obj)`
  Summary: Delete a shunt
- `batteries(self)`
  Summary: Get list of batteries
- `batteries(self, value)`
  Summary: No docstring provided.
- `get_batteries(self)`
  Summary: Returns a list of :ref:`Battery<battery>` objects in the grid.
- `get_batteries_number(self)`
  Summary: Returns a list of :ref:`Battery<battery>` objects in the grid.
- `get_battery_names(self)`
  Summary: Returns a list of :ref:`Battery<battery>` names.
- `get_battery_capacities(self)`
  Summary: Returns a list of :ref:`Battery<battery>` capacities.
- `add_battery(self, bus, api_obj)`
  Summary: Add battery
- `delete_battery(self, obj)`
  Summary: Delete a battery
- `get_batteries_indexing_dict(self)`
  Summary: Get a dictionary that relates the battery uuid's with their index
- `static_generators(self)`
  Summary: Get lis of static generators
- `static_generators(self, value)`
  Summary: No docstring provided.
- `get_static_generators(self)`
  Summary: Returns a list of :ref:`StaticGenerator<static_generator>` objects in the grid.
- `get_static_generators_number(self)`
  Summary: Return number of static generators
- `get_static_generators_names(self)`
  Summary: Returns a list of :ref:`StaticGenerator<static_generator>` names.
- `add_static_generator(self, bus, api_obj)`
  Summary: Add a static generator
- `delete_static_generator(self, obj)`
  Summary: Delete a static generators
- `current_injections(self)`
  Summary: Get list of current injection devices
- `current_injections(self, value)`
  Summary: No docstring provided.
- `get_current_injections(self)`
  Summary: List of current_injections
- `get_current_injections_number(self)`
  Summary: Size of the list of current_injections
- `get_current_injection_at(self, i)`
  Summary: Get current_injection at i
- `get_current_injection_names(self)`
  Summary: Array of current_injection names
- `add_current_injection(self, bus, api_obj)`
  Summary: Add a CurrentInjection object
- `delete_current_injection(self, obj)`
  Summary: Add a CurrentInjection object
- `controllable_shunts(self)`
  Summary: Get list of controllable shunts
- `controllable_shunts(self, value)`
  Summary: No docstring provided.
- `get_controllable_shunts(self)`
  Summary: List of controllable_shunts
- `get_controllable_shunts_number(self)`
  Summary: Size of the list of controllable_shunts
- `get_controllable_shunt_at(self, i)`
  Summary: Get linear_shunt at i
- `get_controllable_shunt_names(self)`
  Summary: Array of linear_shunt names
- `add_controllable_shunt(self, bus, api_obj)`
  Summary: Add a ControllableShunt object
- `delete_controllable_shunt(self, obj)`
  Summary: Add a LinearShunt object
- `pi_measurements(self)`
  Summary: Get list of PiMeasurements
- `pi_measurements(self, value)`
  Summary: No docstring provided.
- `get_p_measurements(self)`
  Summary: List of pi_measurements
- `get_pi_measurements_number(self)`
  Summary: Size of the list of pi_measurements
- `get_pi_measurement_at(self, i)`
  Summary: Get pi_measurement at i
- `get_pi_measurement_names(self)`
  Summary: Array of pi_measurement names
- `add_pi_measurement(self, obj)`
  Summary: Add a PiMeasurement object
- `delete_pi_measurement(self, obj)`
  Summary: Add a PiMeasurement object
- `qi_measurements(self)`
  Summary: Get list of QiMeasurements
- `qi_measurements(self, value)`
  Summary: No docstring provided.
- `get_q_measurements(self)`
  Summary: List of qi_measurements
- `get_qi_measurements_number(self)`
  Summary: Size of the list of qi_measurements
- `get_qi_measurement_at(self, i)`
  Summary: Get qi_measurement at i
- `get_qi_measurement_names(self)`
  Summary: Array of qi_measurement names
- `add_qi_measurement(self, obj)`
  Summary: Add a QiMeasurement object
- `delete_qi_measurement(self, obj)`
  Summary: Add a QiMeasurement object
- `pg_measurements(self)`
  Summary: Get list of PiMeasurements
- `pg_measurements(self, value)`
  Summary: No docstring provided.
- `get_pg_measurements(self)`
  Summary: List of pg_measurements
- `get_pg_measurements_number(self)`
  Summary: Size of the list of pg_measurements
- `get_pg_measurement_at(self, i)`
  Summary: Get pg_measurement at i
- `get_pg_measurement_names(self)`
  Summary: Array of pi_measurement names
- `add_pg_measurement(self, obj)`
  Summary: Add a PgMeasurement object
- `delete_pg_measurement(self, obj)`
  Summary: Add a PiMeasurement object
- `qg_measurements(self)`
  Summary: Get list of QgMeasurements
- `qg_measurements(self, value)`
  Summary: No docstring provided.
- `get_qg_measurements(self)`
  Summary: List of qg_measurements
- `get_qg_measurements_number(self)`
  Summary: Size of the list of qg_measurements
- `get_qg_measurement_at(self, i)`
  Summary: Get qg_measurement at i
- `get_qg_measurement_names(self)`
  Summary: Array of qg_measurement names
- `add_qg_measurement(self, obj)`
  Summary: Add a QiMeasurement object
- `delete_qg_measurement(self, obj)`
  Summary: Add a QgMeasurement object
- `vm_measurements(self)`
  Summary: Get list of VmMeasurements
- `vm_measurements(self, value)`
  Summary: No docstring provided.
- `get_vm_measurements(self)`
  Summary: List of vm_measurements
- `get_vm_measurements_number(self)`
  Summary: Size of the list of vm_measurements
- `get_vm_measurement_at(self, i)`
  Summary: Get vm_measurement at i
- `get_vm_measurement_names(self)`
  Summary: Array of vm_measurement names
- `add_vm_measurement(self, obj)`
  Summary: Add a VmMeasurement object
- `delete_vm_measurement(self, obj)`
  Summary: Add a VmMeasurement object
- `va_measurements(self)`
  Summary: Get list of VaMeasurements
- `va_measurements(self, value)`
  Summary: No docstring provided.
- `get_va_measurements(self)`
  Summary: List of va_measurements
- `get_va_measurements_number(self)`
  Summary: Size of the list of va_measurements
- `get_va_measurement_at(self, i)`
  Summary: Get va_measurement at i
- `get_va_measurement_names(self)`
  Summary: Array of va_measurement names
- `add_va_measurement(self, obj)`
  Summary: Add a VaMeasurement object
- `delete_va_measurement(self, obj)`
  Summary: Add a VaMeasurement object
- `pf_measurements(self)`
  Summary: Get list of PfMeasuremnts
- `pf_measurements(self, value)`
  Summary: No docstring provided.
- `get_pf_measurements(self)`
  Summary: List of pf_measurements
- `get_pf_measurements_number(self)`
  Summary: Size of the list of pf_measurements
- `get_pf_measurement_at(self, i)`
  Summary: Get pf_measurement at i
- `get_pf_measurement_names(self)`
  Summary: Array of pf_measurement names
- `add_pf_measurement(self, obj)`
  Summary: Add a PfMeasurement object
- `delete_pf_measurement(self, obj)`
  Summary: Add a PfMeasurement object
- `pt_measurements(self)`
  Summary: Get list of PtMeasuremnts
- `pt_measurements(self, value)`
  Summary: No docstring provided.
- `get_pt_measurements(self)`
  Summary: List of pt_measurements
- `get_pt_measurements_number(self)`
  Summary: Size of the list of pt_measurements
- `get_pt_measurement_at(self, i)`
  Summary: Get pt_measurement at i
- `get_pt_measurement_names(self)`
  Summary: Array of pt_measurement names
- `add_pt_measurement(self, obj)`
  Summary: Add a PfMeasurement object
- `delete_pt_measurement(self, obj)`
  Summary: Add a PtMeasurement object
- `qf_measurements(self)`
  Summary: Get list of Qf measurements
- `qf_measurements(self, value)`
  Summary: No docstring provided.
- `get_qf_measurements(self)`
  Summary: List of qf_measurements
- `get_qf_measurements_number(self)`
  Summary: Size of the list of qf_measurements
- `get_qf_measurement_at(self, i)`
  Summary: Get qf_measurement at i
- `get_qf_measurement_names(self)`
  Summary: Array of qf_measurement names
- `add_qf_measurement(self, obj)`
  Summary: Add a QfMeasurement object
- `delete_qf_measurement(self, obj)`
  Summary: Add a QfMeasurement object
- `qt_measurements(self)`
  Summary: Get list of Qt measurements
- `qt_measurements(self, value)`
  Summary: No docstring provided.
- `get_qt_measurements(self)`
  Summary: List of qt_measurements
- `get_qt_measurements_number(self)`
  Summary: Size of the list of qt_measurements
- `get_qt_measurement_at(self, i)`
  Summary: Get qt_measurement at i
- `get_qt_measurement_names(self)`
  Summary: Array of qt_measurement names
- `add_qt_measurement(self, obj)`
  Summary: Add a QtMeasurement object
- `delete_qt_measurement(self, obj)`
  Summary: Add a QtMeasurement object
- `if_measurements(self)`
  Summary: Get list of If measurements
- `if_measurements(self, value)`
  Summary: No docstring provided.
- `get_if_measurements(self)`
  Summary: List of if_measurements
- `get_if_measurements_number(self)`
  Summary: Size of the list of if_measurements
- `get_if_measurement_at(self, i)`
  Summary: Get if_measurement at i
- `get_if_measurement_names(self)`
  Summary: Array of if_measurement names
- `add_if_measurement(self, obj)`
  Summary: Add a IfMeasurement object
- `delete_if_measurement(self, obj)`
  Summary: Add a IfMeasurement object
- `it_measurements(self)`
  Summary: Get list of It measurements
- `it_measurements(self, value)`
  Summary: No docstring provided.
- `get_it_measurements(self)`
  Summary: List of it_measurements
- `get_it_measurements_number(self)`
  Summary: Size of the list of it_measurements
- `get_it_measurement_at(self, i)`
  Summary: Get it_measurement at i
- `get_it_measurement_names(self)`
  Summary: Array of it_measurement names
- `add_it_measurement(self, obj)`
  Summary: Add a ItMeasurement object
- `delete_it_measurement(self, obj)`
  Summary: Add a ItMeasurement object
- `overhead_line_types(self)`
  Summary: Get
- `overhead_line_types(self, value)`
  Summary: No docstring provided.
- `add_overhead_line(self, obj)`
  Summary: Add overhead line (tower) template to the collection
- `delete_line_template_dependency(self, obj)`
  Summary: Search a branch template from lines and transformers and delete_with_dialogue it
- `delete_overhead_line(self, obj)`
  Summary: Delete tower from the collection
- `wire_types(self)`
  Summary: :return:
- `wire_types(self, value)`
  Summary: No docstring provided.
- `add_wire(self, obj)`
  Summary: Add Wire to the collection
- `delete_wire(self, obj)`
  Summary: Delete wire from the collection
- `underground_cable_types(self)`
  Summary: :return:
- `underground_cable_types(self, value)`
  Summary: No docstring provided.
- `add_underground_line(self, obj)`
  Summary: Add underground line
- `delete_underground_line(self, obj)`
  Summary: Delete underground line
- `sequence_line_types(self)`
  Summary: :return:
- `sequence_line_types(self, value)`
  Summary: No docstring provided.
- `add_sequence_line(self, obj)`
  Summary: Add sequence line to the collection
- `delete_sequence_line(self, obj)`
  Summary: Delete sequence line from the collection
- `transformer_types(self)`
  Summary: :return:
- `transformer_types(self, value)`
  Summary: No docstring provided.
- `add_transformer_type(self, obj)`
  Summary: Add transformer template
- `delete_transformer_template_dependency(self, obj)`
  Summary: Search a branch template from lines and transformers and delete_with_dialogue it
- `delete_transformer_type(self, obj)`
  Summary: Delete transformer type from the collection
- `branch_groups(self)`
  Summary: :return:
- `branch_groups(self, value)`
  Summary: No docstring provided.
- `get_branch_groups(self)`
  Summary: List of branch_groups
- `get_branch_groups_number(self)`
  Summary: Size of the list of branch_groups
- `get_branch_group_at(self, i)`
  Summary: Get branch_group at i
- `get_branch_group_names(self)`
  Summary: Array of branch_group names
- `add_branch_group(self, obj)`
  Summary: Add a BranchGroup object
- `delete_branch_group(self, obj)`
  Summary: Add a BranchGroup object
- `substations(self)`
  Summary: Get list of substations
- `substations(self, value)`
  Summary: No docstring provided.
- `get_substations(self)`
  Summary: Get a list of substations
- `get_substation_number(self)`
  Summary: Get number of areas
- `add_substation(self, obj)`
  Summary: Add Substation
- `delete_substation(self, obj)`
  Summary: Delete Substation
- `merge_substations(self, selected_objects)`
  Summary: Merge selected substations into the first one
- `areas(self)`
  Summary: Get the list of Areas
- `areas(self, value)`
  Summary: No docstring provided.
- `get_areas(self)`
  Summary: Get list of areas
- `get_area_names(self)`
  Summary: Get array of area names
- `get_area_number(self)`
  Summary: Get number of areas
- `add_area(self, obj)`
  Summary: Add area
- `delete_area(self, obj)`
  Summary: Delete area
- `zones(self)`
  Summary: Get list of zones
- `zones(self, value)`
  Summary: No docstring provided.
- `get_zones(self)`
  Summary: Get list of zones
- `get_zone_number(self)`
  Summary: Get number of areas
- `add_zone(self, obj)`
  Summary: Add zone
- `delete_zone(self, obj)`
  Summary: Delete zone
- `countries(self)`
  Summary: :return:
- `countries(self, value)`
  Summary: No docstring provided.
- `get_countries(self)`
  Summary: Get all countries
- `get_country_number(self)`
  Summary: Get country number
- `add_country(self, obj)`
  Summary: Add country
- `delete_country(self, obj)`
  Summary: Delete country
- `communities(self)`
  Summary: :return:
- `communities(self, value)`
  Summary: No docstring provided.
- `get_communities(self)`
  Summary: List of communities
- `get_communities_number(self)`
  Summary: Size of the list of communities
- `get_community_at(self, i)`
  Summary: Get community at i
- `get_community_names(self)`
  Summary: Array of community names
- `add_community(self, obj)`
  Summary: Add a Community object
- `delete_community(self, obj)`
  Summary: Add a Community object
- `regions(self)`
  Summary: :return:
- `regions(self, value)`
  Summary: No docstring provided.
- `get_regions(self)`
  Summary: List of regions
- `get_regions_number(self)`
  Summary: Size of the list of regions
- `get_region_at(self, i)`
  Summary: Get region at i
- `get_region_names(self)`
  Summary: Array of region names
- `add_region(self, obj)`
  Summary: Add a Region object
- `delete_region(self, obj)`
  Summary: Add a Region object
- `municipalities(self)`
  Summary: Get list of Municipalities
- `municipalities(self, value)`
  Summary: No docstring provided.
- `get_municipalities(self)`
  Summary: List of municipalities
- `get_municipalities_number(self)`
  Summary: Size of the list of municipalities
- `get_municipality_at(self, i)`
  Summary: Get municipality at i
- `get_municipality_names(self)`
  Summary: Array of municipality names
- `add_municipality(self, obj)`
  Summary: Add a Municipality object
- `delete_municipality(self, obj)`
  Summary: Add a Municipality object
- `contingencies(self)`
  Summary: Get list of contingencies
- `contingencies(self, value)`
  Summary: No docstring provided.
- `get_contingency_number(self)`
  Summary: Get number of contingencies
- `add_contingency(self, obj)`
  Summary: Add a contingency
- `delete_contingency(self, obj, del_group)`
  Summary: Delete zone
- `get_contingencies_by_group(self)`
  Summary: Get a dictionary of contingency groups as keys and a list of contingencies as value
- `get_contingency_branch_indices_by_group(self, add_vsc, add_hvdc, add_switch)`
  Summary: Get a dictionary of contingency groups as keys and a list of contingencies as value
- `contingency_groups(self)`
  Summary: Get list of contingency groups
- `contingency_groups(self, value)`
  Summary: No docstring provided.
- `get_contingency_groups(self)`
  Summary: Get contingency_groups
- `get_contingency_groups_active(self)`
  Summary: Get contingency_groups
- `get_contingency_groups_number(self)`
  Summary: :return:
- `add_contingency_group(self, obj)`
  Summary: Add contingency group
- `delete_contingency_group(self, obj)`
  Summary: Delete contingency group
- `get_contingency_group_names(self)`
  Summary: Get list of contingency group names
- `get_contingency_group_dict(self)`
  Summary: Get a dictionary of group idtags related to list of contingencies
- `set_contingencies(self, contingencies)`
  Summary: Set contingencies and contingency groups to circuit
- `get_contingency_groups_in(self, grouping_elements)`
  Summary: Get a filtered set of ContingencyGroups
- `get_contingency_groups_sensitive_to_monitoring(self, LODF, threshold)`
  Summary: Get a list of contingency groups that are sensitive to the monitoring rule
- `investments_groups(self)`
  Summary: :return:
- `investments_groups(self, value)`
  Summary: No docstring provided.
- `get_investment_groups_names(self)`
  Summary: :return:
- `add_investments_group(self, obj)`
  Summary: Add investments group
- `delete_investment_groups(self, obj)`
  Summary: Delete zone
- `get_investments_by_groups(self)`
  Summary: Get a dictionary of investments groups and their
- `get_investment_by_groups_index_dict(self)`
  Summary: Get a dictionary of investments groups
- `get_capex_by_investment_group(self)`
  Summary: Get array of CAPEX costs per investment group
- `investments(self)`
  Summary: :return:
- `investments(self, value)`
  Summary: No docstring provided.
- `add_investment(self, obj)`
  Summary: Add investment
- `delete_investment(self, obj, del_group)`
  Summary: Delete zone
- `rms_events_groups(self)`
  Summary: :return:
- `rms_events_groups(self, value)`
  Summary: No docstring provided.
- `get_rms_events_groups_names(self)`
  Summary: :return:
- `add_rms_events_group(self, obj)`
  Summary: Add rms events group
- `delete_rms_events_group(self, obj)`
  Summary: Delete zone
- `get_rms_event_by_groups(self)`
  Summary: Get a dictionary of RMS event groups and their
- `get_rms_event_by_groups_index_dict(self)`
  Summary: Get a dictionary of investments groups
- `rms_events(self)`
  Summary: :return:
- `rms_events(self, value)`
  Summary: No docstring provided.
- `add_rms_event(self, obj)`
  Summary: Add rms_event
- `delete_rms_event(self, obj, del_group)`
  Summary: Delete zone
- `emt_events_groups(self)`
  Summary: :return:
- `emt_events_groups(self, value)`
  Summary: No docstring provided.
- `get_emt_events_groups_names(self)`
  Summary: :return:
- `add_emt_events_group(self, obj)`
  Summary: Add emt events group
- `delete_emt_events_group(self, obj)`
  Summary: Delete zone
- `get_emt_event_by_groups(self)`
  Summary: Get a dictionary of EMT event groups and their
- `get_emt_event_by_groups_index_dict(self)`
  Summary: Get a dictionary of EMT event groups
- `emt_events(self)`
  Summary: :return:
- `emt_events(self, value)`
  Summary: No docstring provided.
- `add_emt_event(self, obj)`
  Summary: Add emt_event
- `delete_emt_event(self, obj, del_group)`
  Summary: Delete zone
- `dynamic_plots(self)`
  Summary: :return:
- `dynamic_plots(self, value)`
  Summary: No docstring provided.
- `get_dynamic_plots_names(self)`
  Summary: :return:
- `add_dynamic_plot(self, obj)`
  Summary: Add dynamic plot
- `delete_dynamic_plot(self, obj)`
  Summary: Delete dynamic plot
- `get_dynamic_plot_entries_by_plot(self)`
  Summary: Get a dictionary of dynamic plots and their
- `get_dynamic_plot_entries_by_plot_index_dict(self)`
  Summary: Get a dictionary of dynamic plots
- `dynamic_plot_entries(self)`
  Summary: :return:
- `dynamic_plot_entries(self, value)`
  Summary: No docstring provided.
- `add_dynamic_plot_entry(self, obj)`
  Summary: Add dynamic plot entry
- `delete_dynamic_plot_entry(self, obj)`
  Summary: Delete dynamic plot entry
- `remedial_actions(self)`
  Summary: Get list of remedial actions
- `remedial_actions(self, value)`
  Summary: No docstring provided.
- `get_remedial_action_number(self)`
  Summary: Get number of remedial actions
- `add_remedial_action(self, obj)`
  Summary: Add a remedial actions
- `delete_remedial_action(self, obj, del_group)`
  Summary: Delete RemedialAction
- `remedial_action_groups(self)`
  Summary: Get list of contingency groups
- `remedial_action_groups(self, value)`
  Summary: No docstring provided.
- `get_remedial_action_groups(self)`
  Summary: Get contingency_groups
- `get_remedial_action_groups_number(self)`
  Summary: :return:
- `add_remedial_action_group(self, obj)`
  Summary: Add _remedial_action group
- `delete_remedial_action_group(self, obj)`
  Summary: Delete contingency group
- `get_remedial_action_group_names(self)`
  Summary: Get list of contingency group names
- `get_remedial_action_groups_dict(self)`
  Summary: Get a dictionary of group idtags related to list of contingencies
- `set_remedial_actions(self, remedial_actions)`
  Summary: Set contingencies and contingency groups to circuit
- `get_remedial_action_groups_in(self, grouping_elements)`
  Summary: Get a filtered set of ContingencyGroups
- `short_circuit_event(self)`
  Summary: Get list of ShortCircuitDefinition
- `short_circuit_event(self, value)`
  Summary: No docstring provided.
- `add_short_circuit_event(self, obj)`
  Summary: Add short_circuit_definitions
- `delete_short_circuit_event(self, obj)`
  Summary: Delete ShortCircuitDefinition
- `get_short_circuit_event_names(self)`
  Summary: Get the short circuit definition names
- `get_short_circuit_event_number(self)`
  Summary: Get the short circuit definition names
- `short_circuit_event_exist(self, scd)`
  Summary: Check if a short circuit definition has been added already
- `technologies(self)`
  Summary: Get list of technologies
- `technologies(self, value)`
  Summary: No docstring provided.
- `add_technology(self, obj)`
  Summary: Add technology
- `delete_technology(self, obj)`
  Summary: Delete zone
- `get_technology_indexing_dict(self)`
  Summary: Get a dictionary that relates the fuel uuid's with their index
- `get_technology_names(self)`
  Summary: :return:
- `owners(self)`
  Summary: Get list of owners
- `owners(self, value)`
  Summary: No docstring provided.
- `add_owner(self, obj)`
  Summary: Add owner
- `delete_owner(self, obj)`
  Summary: Delete owner
- `get_owner_indexing_dict(self)`
  Summary: Get a dictionary that relates the fuel uuid's with their index
- `get_owner_names(self)`
  Summary: :return:
- `modelling_authorities(self)`
  Summary: :return:
- `modelling_authorities(self, value)`
  Summary: No docstring provided.
- `get_modelling_authorities(self)`
  Summary: List of modelling_authorities
- `get_modelling_authorities_number(self)`
  Summary: Size of the list of modelling_authorities
- `get_modelling_authority_at(self, i)`
  Summary: Get modelling_authority at i
- `get_modelling_authority_names(self)`
  Summary: Array of modelling_authority names
- `add_modelling_authority(self, obj)`
  Summary: Add a ModellingAuthority object
- `delete_modelling_authority(self, obj)`
  Summary: Add a ModellingAuthority object
- `facilities(self)`
  Summary: Get the list of facilities
- `facilities(self, value)`
  Summary: No docstring provided.
- `get_facilities(self)`
  Summary: Get list of areas
- `get_facility_names(self)`
  Summary: Get array of area names
- `get_facility_number(self)`
  Summary: Get number of facilities
- `add_facility(self, obj)`
  Summary: Add facility
- `delete_facility(self, obj)`
  Summary: Delete area
- `fuels(self)`
  Summary: Get list of fuels
- `fuels(self, value)`
  Summary: No docstring provided.
- `get_fuels(self)`
  Summary: :return:
- `get_fuel_number(self)`
  Summary: :return:
- `get_fuel_names(self)`
  Summary: :return:
- `add_fuel(self, obj)`
  Summary: Add Fuel
- `delete_fuel(self, obj)`
  Summary: Delete Fuel
- `get_fuel_indexing_dict(self)`
  Summary: Get a dictionary that relates the fuel uuid's with their index
- `emission_gases(self)`
  Summary: Get list of emission gases
- `emission_gases(self, value)`
  Summary: No docstring provided.
- `get_emissions(self)`
  Summary: :return:
- `get_emission_number(self)`
  Summary: :return:
- `get_emission_names(self)`
  Summary: :return:
- `add_emission_gas(self, obj)`
  Summary: Add EmissionGas
- `delete_emission_gas(self, obj)`
  Summary: Delete Substation
- `get_emissions_indexing_dict(self)`
  Summary: Get a dictionary that relates the fuel uuid's with their index
- `fluid_nodes(self)`
  Summary: Get list of the fluid nodes
- `fluid_nodes(self, value)`
  Summary: No docstring provided.
- `add_fluid_node(self, obj)`
  Summary: Add fluid node
- `delete_fluid_node(self, obj)`
  Summary: Delete fluid node
- `get_fluid_nodes(self)`
  Summary: :return:
- `get_fluid_nodes_number(self)`
  Summary: :return:
- `get_fluid_node_names(self)`
  Summary: List of fluid node names
- `fluid_paths(self)`
  Summary: Get list of fluid path devices
- `fluid_paths(self, value)`
  Summary: No docstring provided.
- `add_fluid_path(self, obj)`
  Summary: Add fluid path
- `delete_fluid_path(self, obj)`
  Summary: Delete fuid path
- `get_fluid_paths(self)`
  Summary: :return:
- `get_fluid_path_names(self)`
  Summary: List of fluid paths names
- `get_fluid_paths_number(self)`
  Summary: :return:
- `turbines(self)`
  Summary: Get list of fluid turbines
- `turbines(self, value)`
  Summary: No docstring provided.
- `add_fluid_turbine(self, node, api_obj)`
  Summary: Add fluid turbine
- `delete_fluid_turbine(self, obj)`
  Summary: Delete fuid turbine
- `get_fluid_turbines(self)`
  Summary: Returns a list of :ref:`Load<load>` objects in the grid.
- `get_fluid_turbines_number(self)`
  Summary: :return: number of total turbines in the network
- `get_fluid_turbines_names(self)`
  Summary: Returns a list of :ref:`Turbine<turbine>` names.
- `pumps(self)`
  Summary: Get the list of fluid pumps
- `pumps(self, value)`
  Summary: No docstring provided.
- `add_fluid_pump(self, node, api_obj)`
  Summary: Add fluid pump
- `delete_fluid_pump(self, obj)`
  Summary: Delete fuid pump
- `get_fluid_pumps(self)`
  Summary: Returns a list of :ref:`Load<load>` objects in the grid.
- `get_fluid_pumps_number(self)`
  Summary: :return: number of total pumps in the network
- `get_fluid_pumps_names(self)`
  Summary: Returns a list of :ref:`Pump<pump>` names.
- `p2xs(self)`
  Summary: Get list of power-to-x devices
- `p2xs(self, value)`
  Summary: No docstring provided.
- `add_fluid_p2x(self, node, api_obj)`
  Summary: Add power to x
- `delete_fluid_p2x(self, obj)`
  Summary: Delete fuid pump
- `get_fluid_p2xs(self)`
  Summary: Returns a list of :ref:`Load<load>` objects in the grid.
- `get_fluid_p2xs_number(self)`
  Summary: :return: number of total pumps in the network
- `get_fluid_p2xs_names(self)`
  Summary: Returns a list of :ref:`P2X<P2X>` names.
- `diagrams(self)`
  Summary: Get the list of diagrams
- `diagrams(self, value)`
  Summary: No docstring provided.
- `get_diagrams(self)`
  Summary: Get list of diagrams
- `has_diagrams(self)`
  Summary: Check if there are diagrams stored
- `add_diagram(self, diagram)`
  Summary: Add diagram
- `remove_diagram(self, diagram)`
  Summary: Remove diagrams
- `rms_models(self)`
  Summary: list of rms models
- `rms_models(self, value)`
  Summary: No docstring provided.
- `get_rms_models_number(self)`
  Summary: Get number of RMS models
- `add_rms_model(self, obj)`
  Summary: Add rms model to the collection
- `delete_rms_model(self, obj)`
  Summary: Delete RMS model from the collection
- `get_rms_models_by_device_type(self, tpe)`
  Summary: Get a list of RmsModelTemplate filtering by device type
- `emt_models(self)`
  Summary: list of emt models
- `emt_models(self, value)`
  Summary: No docstring provided.
- `get_emt_models_number(self)`
  Summary: Get number of EMT models
- `add_emt_model(self, obj)`
  Summary: Add emt model to the collection
- `delete_emt_model(self, obj)`
  Summary: Delete EMT model from the collection
- `get_emt_models_by_device_type(self, tpe)`
  Summary: Get a list of EmtModelTemplate filtering by device type
- `add_branch(self, obj)`
  Summary: Add any branch object (it's type will be inferred here)
- `delete_branch(self, obj)`
  Summary: Delete a :ref:`Branch<branch>` object from the grid.
- `get_branch_lists(self, add_vsc, add_hvdc, add_switch)`
  Summary: Return all the branch objects
- `get_branches(self, add_vsc, add_hvdc, add_switch)`
  Summary: Return all the branch objects
- `get_branches_iter(self, add_vsc, add_hvdc, add_switch)`
  Summary: Return all the branch objects
- `get_branch_number(self, add_vsc, add_hvdc, add_switch)`
  Summary: return the number of Branches (of all types)
- `get_branch_names(self, add_vsc, add_hvdc, add_switch)`
  Summary: Get array of all branch names
- `get_branch_actives(self, t_idx, add_vsc, add_hvdc, add_switch)`
  Summary: Get array of all branch active states
- `get_branches_index_dict(self, add_vsc, add_hvdc, add_switch)`
  Summary: Get the branch to index dictionary
- `get_branches_idtag_index_dict(self, add_vsc, add_hvdc, add_switch)`
  Summary: Get the branch to index dictionary
- `get_branches_index_dict2(self, add_vsc, add_hvdc, add_switch)`
  Summary: Get the branch to index dictionary
- `get_branches_dict(self, add_vsc, add_hvdc, add_switch)`
  Summary: Get dictionary of branches (excluding HVDC)
- `get_branch_FT(self, add_vsc, add_hvdc, add_switch)`
  Summary: get the from and to arrays of indices
- `get_branches_monitored_indices(self, add_vsc, add_hvdc, add_switch)`
  Summary: Get the indices of the monitored branche
- `delete_groupings_with_object(self, obj, delete_groups)`
  Summary: Delete the dependencies that may come with a branch
- `get_hvdc_FT(self)`
  Summary: get the from and to arrays of indices of HVDC lines
- `delete_injection_device(self, obj)`
  Summary: Delete a :ref:`Branch<branch>` object from the grid.
- `get_injections_device_types(self)`
  Summary: Get a list of all devices types that can inject or subtract power from a node
- `get_injection_devices_lists(self)`
  Summary: Get a list of all devices that can inject or subtract power from a node
- `get_injection_devices(self)`
  Summary: Get a list of all devices that can inject or subtract power from a node
- `get_injection_devices_iter(self)`
  Summary: Get a list of all devices that can inject or subtract power from a node
- `get_injections_bus_index_dict(self, bus_index_dict)`
  Summary: Get a dictionary of generators related to their bus index
- `get_load_like_devices_lists(self)`
  Summary: Get a list of all devices that can inject or subtract power from a node
- `get_load_like_devices(self)`
  Summary: Get a list of all devices that can inject or subtract power from a node
- `get_load_like_devices_iter(self)`
  Summary: Get a list of all devices that can inject or subtract power from a node
- `get_load_like_device_number(self)`
  Summary: Get a list of all devices that can inject or subtract power from a node
- `get_load_like_devices_names(self)`
  Summary: Get a list of names of the load like devices
- `get_shunt_like_devices_lists(self)`
  Summary: Get a list of all devices that behave like a shunt
- `get_shunt_like_devices(self)`
  Summary: Get a list of all devices that can inject or subtract power from a node
- `get_shunt_like_devices_names(self)`
  Summary: Get a list of all devices names that can inject or subtract power from a node
- `get_shunt_like_device_number(self)`
  Summary: Get a list of all devices that can inject or subtract power from a node
- `get_generation_like_lists(self)`
  Summary: Get a list with the fluid injections lists
- `get_generation_like_number(self)`
  Summary: Get number of fluid injections
- `get_generation_like_names(self)`
  Summary: Returns a list of :ref:`Injection<Injection>` names.
- `get_generation_like_devices(self)`
  Summary: Returns a list of :ref:`Injection<Injection>` names.
- `get_fluid_injection_lists(self)`
  Summary: Get a list with the fluid injections lists
- `get_fluid_injection_number(self)`
  Summary: Get number of fluid injections
- `get_fluid_injection_names(self)`
  Summary: Returns a list of :ref:`Injection<Injection>` names.
- `get_fluid_injections(self)`
  Summary: Returns a list of :ref:`Injection<Injection>` names.
- `get_contingency_devices(self)`
  Summary: Get a list of devices susceptible to be included in contingencies / remedial actions
- `get_elements_by_type(self, device_type)`
  Summary: Get set of elements and their parent nodes
- `set_elements_list_by_type(self, device_type, devices, logger)`
  Summary: Set a list of elements all at once
- `add_element(self, obj)`
  Summary: Add a device in its corresponding list
- `delete_element(self, obj)`
  Summary: Get set of elements and their parent nodes
- `merge_object(self, api_obj, all_elms_base_dict, logger)`
  Summary: Add, Delete or Modify an object based on the UUID
- `get_all_elements_iter(self)`
  Summary: Get all elements
- `get_all_elements_number(self)`
  Summary: Get all elements number
- `get_all_elements_dict(self, use_secondary_key, use_rdfid, logger)`
  Summary: Get a dictionary of all elements
- `get_all_elements_dict_by_type(self, add_locations, string_keys)`
  Summary: Get a dictionary of all elements by type
- `get_elements_dict_by_type(self, element_type, use_secondary_key, use_rdfid)`
  Summary: Get dictionary of elements
- `clear(self)`
  Summary: Clear the multi-circuit (delete the bus and branch objects)
- `get_dictionary_of_lists(self, elm_type)`
  Summary: Function that returns the template of an elements and a dictionary
- `new_idtags(self)`
  Summary: Generates new idtags for every object in this assets class
- `replace_objects(self, old_object, new_obj, logger)`
  Summary: Replace object for every object in this assets class
- `refine_pointer_objects(self, logger)`
  Summary: Find the device types of pointer objects
- `add_rms_model_catalogue(self)`
  Summary: Here the list of all rms templates must be returned in a list
- `add_emt_model_catalogue(self)`
  Summary: Create default catalogue of EMT values
