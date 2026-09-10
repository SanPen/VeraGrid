# VeraGridEngine Module: src/VeraGridEngine/Simulations/ShortCircuitStudies/short_circuit_driver.py

- Original source path: `src/VeraGridEngine/Simulations/ShortCircuitStudies/short_circuit_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, numpy, VeraGridEngine.basic_structures, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.basic_structures, VeraGridEngine.Simulations.PowerFlow.power_flow_driver, VeraGridEngine.Simulations.PowerFlow.power_flow_driver_3ph, VeraGridEngine.Simulations.OPF.opf_results, VeraGridEngine.Simulations.ShortCircuitStudies.short_circuit_worker, VeraGridEngine.Simulations.ShortCircuitStudies.short_circuit_results, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.Devices, VeraGridEngine.Compilers.circuit_to_data, VeraGridEngine.Simulations.driver_template, VeraGridEngine.Simulations.ShortCircuitStudies.short_circuit_options, VeraGridEngine.enumerations

## Class: ShortCircuitDriver

- Bases: DriverTemplate
- Summary: No docstring provided.

### Methods

- `get_steps(self)`
  Summary: Get time steps list of strings
- `compile_zf(grid)`
  Summary: Compose the fault impedance
- `split_branch(branch, fault_position, r_fault, x_fault)`
  Summary: Split a branch by a given distance
- `single_short_circuit_sequences(nc, Vpf, Zf, island_bus_index, fault_type)`
  Summary: Run a short circuit simulation for a single island
- `single_short_circuit_phases(nc, voltage_N, voltage_A, voltage_B, voltage_C, Zf, island_bus_index, fault_type, phases, Sbus_N, Sbus_A, Sbus_B, Sbus_C, logger)`
  Summary: Run a short circuit simulation for a single island
- `single_short_circuit_vsc(nc, V_pf, S_pf, Z_fault, fault_bus, options, logger)`
  Summary: No docstring provided.
- `run(self)`
  Summary: Run a power flow for every circuit
