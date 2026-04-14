# VeraGridEngine Module: src/VeraGridEngine/Simulations/PowerFlow/power_flow_worker.py

- Original source path: `src/VeraGridEngine/Simulations/PowerFlow/power_flow_worker.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 7
- Representative imports: __future__, numpy, typing, VeraGridEngine.Simulations.PowerFlow, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.Simulations.PowerFlow.power_flow_options, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.Simulations.PowerFlow.Formulations.pf_basic_formulation, VeraGridEngine.Simulations.PowerFlow.Formulations.pf_full_acdc_with_negative_poles, VeraGridEngine.Simulations.PowerFlow.Formulations.pf_generalized_formulation, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.newton_raphson_fx, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.powell_fx, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.levenberg_marquadt_fx, VeraGridEngine.Topology.simulation_indices

## Function: __split_reactive_power_into_devices(nc, Qbus, results)

This function splits the reactive power of the power flow solution (nbus) into reactive power per device that

## Function: __solve_island_complete_support(nc, indices, options, V0, S0, logger)

Run a power flow simulation using the selected method (no outer loop controls).

## Function: __solve_island_limited_support(island, indices, options, V0, S_base, Shvdc, logger)

Run a power flow simulation using the selected method (no outer loop controls).

## Function: __multi_island_pf_nc_complete_support(nc, options, logger, V_guess, Sbus_input)

Multiple islands power flow (this is the most generic power flow function)

## Function: __multi_island_pf_nc_limited_support(nc, options, logger, V_guess, Sbus_input)

Multiple islands power flow (this is the most generic power flow function)

## Function: multi_island_pf_nc(nc, options, logger, V_guess, Sbus_input)

Multiple islands power flow (this is the most generic power flow function)

## Function: multi_island_pf(multi_circuit, options, opf_results, t, logger, bus_dict, areas_dict)

Multiple islands power flow (this is the most generic power flow function)
