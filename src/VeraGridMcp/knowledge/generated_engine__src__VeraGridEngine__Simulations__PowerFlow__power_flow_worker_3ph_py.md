# VeraGridEngine Module: src/VeraGridEngine/Simulations/PowerFlow/power_flow_worker_3ph.py

- Original source path: `src/VeraGridEngine/Simulations/PowerFlow/power_flow_worker_3ph.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 4
- Representative imports: __future__, numpy, typing, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, VeraGridEngine.Simulations.PowerFlow.power_flow_results_3ph, VeraGridEngine.Simulations.PowerFlow.power_flow_options, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.Simulations.PowerFlow.Formulations.pf_basic_formulation_3ph, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.newton_raphson_fx, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.powell_fx, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.levenberg_marquadt_fx, VeraGridEngine.Topology.simulation_indices, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.Devices.multi_circuit

## Function: __solve_island_limited_support_3ph(island, indices, options, V0, S_base, Shvdc, logger)

Run a power flow simulation using the selected method (no outer loop controls).

## Function: __multi_island_pf_nc_limited_support_3ph(nc, options, logger, V_guess, Sbus_input)

Multiple islands power flow (this is the most generic power flow function)

## Function: multi_island_pf_nc_3ph(nc, options, logger, V_guess, Sbus_input)

Multiple islands power flow (this is the most generic power flow function)

## Function: multi_island_pf_3ph(multi_circuit, options, opf_results, t, logger, bus_dict, areas_dict)

Multiple islands power flow (this is the most generic power flow function)
