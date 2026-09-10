# VeraGridEngine Module: src/VeraGridEngine/Simulations/OPF/ac_opf_worker.py

- Original source path: `src/VeraGridEngine/Simulations/OPF/ac_opf_worker.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 2
- Representative imports: numpy, typing, VeraGridEngine.Utils.NumericalMethods.ips, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Compilers.circuit_to_data, VeraGridEngine.Simulations.PowerFlow.power_flow_worker, VeraGridEngine.Simulations.PowerFlow.power_flow_options, VeraGridEngine.Simulations.OPF.opf_options, VeraGridEngine.Simulations.OPF.Formulations.ac_opf_problem, VeraGridEngine.Simulations.OPF.NumericalMethods.newton_raphson_ips_fx, VeraGridEngine.basic_structures

## Function: remap_original_bus_indices(n_bus, original_bus_idx)

Get arrays of bus mappings

## Function: run_nonlinear_opf(grid, opf_options, t_idx, plot_error, optimize_nodal_capacity, nodal_capacity_sign, capacity_nodes_idx, logger)

Run optimal power flow for a MultiCircuit
