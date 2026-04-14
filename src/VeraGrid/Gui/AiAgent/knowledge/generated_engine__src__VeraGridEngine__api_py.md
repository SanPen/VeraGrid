# VeraGridEngine Module: src/VeraGridEngine/api.py

- Original source path: `src/VeraGridEngine/api.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 19
- Representative imports: __future__, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, VeraGridEngine.Simulations, VeraGridEngine.IO, VeraGridEngine.Devices, VeraGridEngine.DataStructures, VeraGridEngine.Topology, VeraGridEngine.Compilers, VeraGridEngine.Templates, VeraGridEngine.IO.file_open, VeraGridEngine.IO.file_save, VeraGridEngine.IO.veragrid.remote, VeraGridEngine.Compilers.circuit_to_data

## Function: open_file(filename, options)

Open file

## Function: save_file(grid, filename, drivers_to_save)

Save file

## Function: save_multiverse(mv, filename)

Save file

## Function: open_cgmes(filenames, cgmes_version)

Open CGMES files

## Function: save_cgmes_file(grid, filename, cgmes_boundary_set_path, cgmes_version, pf_results)

Save the grid in CGMES format

## Function: power_flow(grid, options, engine)

Run power flow on the snapshot

## Function: power_flow3ph(grid, options, engine)

Run power flow on the snapshot

## Function: power_flow_ts(grid, options, time_indices, clustering_results, auto_expand, engine)

Run power flow on the time series

## Function: linear_power_flow(grid, options)

Run linear power flow on the snapshot

## Function: linear_power_flow_ts(grid, options)

Run linear power flow time series

## Function: short_circuit(grid, fault_index, fault_type, pf_options, pf_results, pf_results3ph)

Run short circuit

## Function: continuation_power_flow(grid, options, pf_options, pf_results, factor, stop_at)

Run continuation power flow circuit

## Function: nonlinear_opf(grid, opf_options, plot_error)

Run AC Optimal Power Flow

## Function: linear_opf(grid, options)

Run Linear Optimal Power Flow

## Function: simple_opf(grid, options)

Run Linear Optimal Power Flow

## Function: balanced_pf(grid, options, opf_options, engine)

Run Linear Optimal Power Flow

## Function: balanced_pf(grid, options, opf_options, engine)

Run Linear Optimal Power Flow and feed that to a power flow

## Function: contingencies_ts(circuit, use_clustering, n_points, use_srap, srap_max_power, srap_top_n, srap_deadband, srap_rever_to_nominal_rating, detailed_massive_report, contingency_deadband, contingency_method)

Run a time series contingency analysis

## Function: clustering(circuit, n_points)

Perform a clustering analysis for time series
