# VeraGridEngine Module: src/VeraGridEngine/Simulations/results_template.py

- Original source path: `src/VeraGridEngine/Simulations/results_template.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 0
- Representative imports: __future__, json, numpy, pandas, typing, VeraGridEngine.Simulations.results_table, VeraGridEngine.basic_structures, VeraGridEngine.enumerations, VeraGridEngine.Devices.multi_circuit

## Class: ResultsProperty

- Bases: none
- Summary: ResultsProperty

### Methods

- No methods detected.

## Class: ResultsTemplate

- Bases: none
- Summary: ResultsTemplate

### Methods

- `data_variables(self)`
  Summary: :return:
- `time_array(self)`
  Summary: Array of time steps
- `time_array(self, time_array)`
  Summary: No docstring provided.
- `is_3ph(self)`
  Summary: No docstring provided.
- `plotting_allowed(self)`
  Summary: :return:
- `activate_plotting(self)`
  Summary: :return:
- `deactivate_plotting(self)`
  Summary: :return:
- `register(self, name, tpe, old_names)`
  Summary: Register a results variable for disk persistence
- `consolidate_after_loading(self)`
  Summary: Consolidate
- `get_dict(self)`
  Summary: Get data to pass via json
- `parse_data(self, data)`
  Summary: The function to parse the data created with get_dict
- `get_name_to_results_type_dict(self)`
  Summary: :return:
- `get_name_tree(self)`
  Summary: :return:
- `to_json(self, file_name)`
  Summary: Export as json
- `apply_new_rates(self, rates)`
  Summary: :param rates:
- `apply_new_time_series_rates(self, rates)`
  Summary: :param rates:
- `get_inter_area_flows(self, area_names, F, T, Sf, hvdc_F, hvdc_T, hvdc_Pf, bus_area_indices)`
  Summary: :param area_names:
- `get_bus_values_per_area(bus_values, area_names, bus_area_indices)`
  Summary: Split array of bus-related values per area
- `get_branch_values_per_area(self, branch_values, area_names, bus_area_indices, F, T)`
  Summary: Split array of branch-related values per area
- `get_hvdc_values_per_area(self, hvdc_values, area_names, bus_area_indices, hvdc_F, hvdc_T)`
  Summary: Split array of hvdc-related values per area
- `fill_circuit_info(self, grid)`
  Summary: :param grid:
- `fill_simulation_info(self, grid)`
  Summary: :param grid:
- `mdl(self, result_type)`
  Summary: Get results model (overloaded in the respective implementations)
- `expand_clustered_results(self)`
  Summary: Expand all arrays using the clustering info
- `parse_saved_data(self, grid, data_dict, logger)`
  Summary: :param grid: MultiCircuit
