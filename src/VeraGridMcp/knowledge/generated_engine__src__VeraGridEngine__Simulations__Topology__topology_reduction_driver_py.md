# VeraGridEngine Module: src/VeraGridEngine/Simulations/Topology/topology_reduction_driver.py

- Original source path: `src/VeraGridEngine/Simulations/Topology/topology_reduction_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 3
- Top-level function count: 4
- Representative imports: pandas, networkx, scipy.sparse, typing, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Devices.Branches.branch, VeraGridEngine.Devices.Substation.bus, VeraGridEngine.enumerations, VeraGridEngine.Simulations.driver_template

## Function: get_branches_of_bus(B, j)

Get the indices of the Branches connected to the bus j

## Function: select_branches_to_reduce(circuit, rx_criteria, rx_threshold, selected_types)

Find Branches to delete

## Function: reduce_grid_brute(circuit, removed_br_idx)

Remove the first branch found to be removed.

## Function: reduce_buses(circuit, buses_to_reduce, text_func, prog_func)

Reduce the uses in the grid

## Class: TopologyReductionOptions

- Bases: none
- Summary: TopologyReductionOptions

### Methods

- No methods detected.

## Class: TopologyReduction

- Bases: DriverTemplate
- Summary: No docstring provided.

### Methods

- `run(self)`
  Summary: Run the monte carlo simulation
- `cancel(self)`
  Summary: Cancel the simulation

## Class: DeleteAndReduce

- Bases: DriverTemplate
- Summary: No docstring provided.

### Methods

- `run(self)`
  Summary: Run the monte carlo simulation
- `cancel(self)`
  Summary: Cancel the simulation
- `start(self)`
  Summary: No docstring provided.
