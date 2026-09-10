# VeraGridEngine Module: src/VeraGridEngine/Compilers/circuit_to_bentayga.py

- Original source path: `src/VeraGridEngine/Compilers/circuit_to_bentayga.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 18
- Representative imports: os.path, numpy, VeraGridEngine.enumerations, VeraGridEngine.Simulations.PowerFlow.power_flow_options, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.IO.file_system, VeraGridEngine.basic_structures

## Function: add_btg_buses(circuit, btg_circuit, time_series, ntime)

Convert the buses to bentayga buses

## Function: add_btg_loads(circuit, btg_circuit, bus_dict, time_series, ntime)

:param circuit: VeraGrid circuit

## Function: add_btg_static_generators(circuit, btg_circuit, bus_dict, time_series, ntime)

:param circuit: VeraGrid circuit

## Function: add_btg_shunts(circuit, btg_circuit, bus_dict, time_series, ntime)

:param circuit: VeraGrid circuit

## Function: add_btg_generators(circuit, btg_circuit, bus_dict, time_series, ntime)

:param circuit: VeraGrid circuit

## Function: get_battery_data(circuit, btg_circuit, bus_dict, time_series, ntime)

:param circuit: VeraGrid circuit

## Function: add_btg_line(circuit, btg_circuit, bus_dict, time_series, ntime)

:param circuit: VeraGrid circuit

## Function: get_transformer_data(circuit, btg_circuit, bus_dict, time_series, ntime)

:param circuit: VeraGrid circuit

## Function: get_vsc_data(circuit, btg_circuit, bus_dict, time_series, ntime)

:param circuit: VeraGrid circuit

## Function: get_dc_line_data(circuit, btg_circuit, bus_dict, time_series, ntime)

:param circuit: VeraGrid circuit

## Function: get_hvdc_data(circuit, btg_circuit, bus_dict, time_series, ntime)

:param circuit: VeraGrid circuit

## Function: to_bentayga(circuit, time_series)

Convert VeraGrid circuit to Bentayga

## Class: FakeAdmittances

- Bases: none
- Summary: No docstring provided.

### Methods

- No methods detected.

## Function: get_snapshots_from_bentayga(circuit)

No docstring provided.

## Function: get_bentayga_pf_options(opt)

Translate VeraGrid power flow options to Bentayga power flow options

## Function: bentayga_pf(circuit, opt, time_series)

Bentayga power flow

## Function: bentayga_linear_matrices(circuit, distributed_slack)

Bentayga linear analysis

## Function: translate_bentayga_pf_results(grid, res)

:param grid:

## Function: debug_bentayga_circuit_at(btg_circuit, t)

No docstring provided.
