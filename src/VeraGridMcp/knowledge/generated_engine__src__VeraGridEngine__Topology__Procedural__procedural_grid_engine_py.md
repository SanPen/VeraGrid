# VeraGridEngine Module: src/VeraGridEngine/Topology/Procedural/procedural_grid_engine.py

- Original source path: `src/VeraGridEngine/Topology/Procedural/procedural_grid_engine.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 6
- Top-level function count: 2
- Representative imports: __future__, typing, random, numpy, VeraGridEngine.Devices, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, scipy.spatial.distance, scipy.sparse.csgraph, scipy.special, VeraGridEngine.Topology.Procedural.procedural_grid_debugger

## Function: coord_calc(current_bus_lon, current_bus_lat, length, coord_out)

Calculate the coordinates of the next bus based on the current bus,

## Function: instantiate_branch_from_template(template_branch, current_bus, next_bus, length)

Create a new branch object using an existing branch as template.

## Class: TransitionMatrix

- Bases: none
- Summary: No docstring provided.

### Methods

- `at(self, V1, V2)`
  Summary: Get probability associated to V1, transitioning to V2
- `template_dictionary(grid)`
  Summary: Build a dictionary of branch templates grouped by voltage transition.
- `get_most_likely_transition_voltage(self, V)`
  Summary: Get the most likely voltage to transition to, given a voltage

## Class: Node

- Bases: none
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: Edge

- Bases: none
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ProceduralGridGraph

- Bases: none
- Summary: No docstring provided.

### Methods

- `calculate_fitness(self, mu_lon, mu_lat)`
  Summary: VSA Fitness: MST Length + Degree Penalty.
- `run_vsa(self)`
  Summary: :return: best_solution (dim, (lat, lon))
- `prune_redundant_nodes(self, steiner_coords)`
  Summary: Iteratively removes Steiner points with Degree <= 2.

## Class: Topology

- Bases: none
- Summary: Represents the physical layout using domain objects.

### Methods

- `generate_markov(self)`
  Summary: Generates combinations that are valid by construction.
- `add_branch_to_grid(self, expansion_grid, branch)`
  Summary: Add a branch object to the correct container of the expansion grid.
- `last_bus_fix(self, transition_matrix, current_bus_volt, next_bus_volt)`
  Summary: No docstring provided.
- `add_loads(self)`
  Summary: Function to add loads and generators to the VeraGrid grid object

## Class: ProceduralGridComputationEngine

- Bases: none
- Summary: Core engine for procedural grid expansion calculations.

### Methods

- `get_buses(self)`
  Summary: Get list of all the incumbent buses in the calculation
- `run_steiner_alone(self)`
  Summary: Executes the Steiner Tree algorithm without further optimization.
- `run_optimization(self)`
  Summary: Executes the Steiner Tree algorithm followed by an optimization pass.
