# VeraGridEngine Module: src/VeraGridEngine/Simulations/ATC/available_transfer_capacity_driver.py

- Original source path: `src/VeraGridEngine/Simulations/ATC/available_transfer_capacity_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 6
- Representative imports: __future__, numpy, numba, typing, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Compilers.circuit_to_data, VeraGridEngine.Simulations.LinearFactors.linear_analysis, VeraGridEngine.Simulations.results_table, VeraGridEngine.Simulations.results_template, VeraGridEngine.Simulations.driver_template, VeraGridEngine.Simulations.ATC.available_transfer_capacity_options, VeraGridEngine.enumerations, VeraGridEngine.basic_structures

## Function: get_proportional_deltas_sensed(P, idx, dP)

:param P: all power Injections

## Function: scale_proportional_sensed(P, idx1, idx2, dT)

:param P: Power vector

## Function: compute_dP(P0, Pgen, P_installed, Pload, bus_a1_idx, bus_a2_idx, dT, mode)

Compute power injections to compute the inter-area sensitivities

## Function: compute_alpha(ptdf, dP, dT)

Compute line sensitivity to power transfer

## Function: compute_alpha_n1(ptdf, lodf, dP, alpha, dT)

:param ptdf: Power transfer distribution factors (n-branch, n-bus)

## Function: compute_atc_list(br_idx, contingency_br_idx, lodf, alpha, flows, rates, contingency_rates, base_exchange, threshold, time_idx)

Compute all lines' available transfer capacity (ATC)

## Class: AvailableTransferCapacityResults

- Bases: ResultsTemplate
- Summary: No docstring provided.

### Methods

- `get_steps(self)`
  Summary: :return:
- `make_report(self, threshold)`
  Summary: :return:
- `get_dict(self)`
  Summary: Returns a dictionary with the results sorted in a dictionary
- `mdl(self, result_type)`
  Summary: Plot the results

## Class: AvailableTransferCapacityDriver

- Bases: DriverTemplate
- Summary: No docstring provided.

### Methods

- `run(self)`
  Summary: Run thread
- `get_steps(self)`
  Summary: Get variations list of strings
