# VeraGridEngine Module: src/VeraGridEngine/Simulations/ShortCircuitStudies/short_circuit_worker.py

- Original source path: `src/VeraGridEngine/Simulations/ShortCircuitStudies/short_circuit_worker.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 7
- Representative imports: typing, numpy, scipy.sparse, scipy.sparse.linalg, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.Simulations.ShortCircuitStudies.short_circuit, VeraGridEngine.Topology.admittance_matrices, VeraGridEngine.Simulations.ShortCircuitStudies.short_circuit_results, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, VeraGridEngine.Simulations.PowerFlow.Formulations.pf_basic_formulation_3ph, VeraGridEngine.Simulations.PowerFlow.power_flow_options, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.Simulations.PowerFlow.Formulations.pf_full_acdc_with_negative_poles, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.newton_raphson_fx

## Function: short_circuit_post_process(calculation_inputs, V, branch_rates, Yf, Yt)

Compute the important results for short-circuits

## Function: short_circuit_post_process_phases_abc(calculation_inputs, V_expanded, branch_rates_expanded, Yf, Yt, F_expanded, T_expanded, mask, branch_lookup)

Compute the important results for short-circuits

## Function: short_circuit_ph3(nc, Vpf, Zf, bus_index)

Run a 3-phase short circuit simulation for a single island

## Function: short_circuit_unbalanced(nc, Vpf, Zf, bus_index, fault_type)

Run an unbalanced short circuit simulation for a single island

## Function: maximum_initial_shortcircuit_current(nc, Zf, faulted_bus)

:param nc:

## Function: short_circuit_abc(nc, voltage_N, voltage_A, voltage_B, voltage_C, Zf, bus_index, fault_type, phases, Sbus_N, Sbus_A, Sbus_B, Sbus_C)

Run a short circuit simulation in the phase domain

## Function: short_circuit_vsc(nc, V_pf, S_pf, Z_fault, fault_bus, options, logger)

No docstring provided.
