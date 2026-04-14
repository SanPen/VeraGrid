# VeraGridEngine Module: src/VeraGridEngine/Compilers/circuit_to_pgm.py

- Original source path: `src/VeraGridEngine/Compilers/circuit_to_pgm.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 16
- Representative imports: warnings, numpy, typing, json, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.basic_structures, VeraGridEngine.enumerations, VeraGridEngine.Simulations.PowerFlow.power_flow_options, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.Simulations.PowerFlow.power_flow_ts_results, VeraGridEngine.Compilers.circuit_to_data

## Function: get_pgm_buses(circuit, idx0)

Convert the buses to LFE'sPGM buses

## Function: get_pgm_loads(circuit, bus_dict, idx0, n_time)

Generate load data

## Function: get_pgm_shunts(circuit, bus_dict, idx0)

:param circuit: VeraGrid circuit

## Function: get_pgm_generators(circuit, bus_dict, idx0, n_time)

:param circuit: VeraGrid circuit

## Function: get_pgm_source(circuit, bus_dict, idx0)

:param circuit: VeraGrid circuit

## Function: get_pgm_line(circuit, bus_dict, idx0, logger)

:param circuit: VeraGrid circuit

## Function: get_pgm_transformer_data(circuit, bus_dict, idx0)

:param circuit: VeraGrid circuit

## Function: get_pgm_vsc_data(circuit, bus_dict, idx0)

:param circuit: VeraGrid circuit

## Function: get_pgm_dc_line_data(circuit, bus_dict, idx0)

:param circuit: VeraGrid circuit

## Function: get_pgm_hvdc_data(circuit, bus_dict, idx0)

:param circuit: VeraGrid circuit

## Function: get_pgm_input_data(circuit, logger, time_series)

No docstring provided.

## Function: to_pgm(circuit, logger, time_series)

Convert VeraGrid circuit to LFE'sPGM model

## Function: pgm_pf(circuit, opt, logger, symmetric, time_series)

LFE'sPGM power flow

## Class: NumpyEncoder

- Bases: json.JSONEncoder
- Summary: No docstring provided.

### Methods

- `default(self, obj)`
  Summary: No docstring provided.

## Function: save_pgm(filename, circuit, logger, time_series)

Save to Power Grid Model format

## Function: translate_pgm_results(grid, pf_res)

Translate the PGM results to SnapShot power flow results

## Function: translate_pgm_pf_results2d(grid, pf_res)

Translate the time series power flow results
