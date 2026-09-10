# VeraGridEngine Module: src/VeraGridEngine/Topology/Procedural/procedural_grid_debugger.py

- Original source path: `src/VeraGridEngine/Topology/Procedural/procedural_grid_debugger.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, typing, numpy, matplotlib.pyplot, VeraGridEngine.Devices

## Class: ProceduralGridDebugger

- Bases: none
- Summary: Helper class for plotting and validating intermediate results during

### Methods

- `plot_mst_graph(self, coords_final_network, edges, n_candidate, n_target, final_steiner_pts, title, show_labels)`
  Summary: Plot the graph defined by node coordinates and edge list.
- `print_edges(self, edges)`
  Summary: Print the edge list.
- `validate_edge_indices(self, edges, n_nodes)`
  Summary: Validate that all edge indices are within bounds.
- `print_voltage_summary(self, voltages, label)`
  Summary: Print a simple voltage summary.
- `snapshot_grid_element_names(self, grid)`
  Summary: Take a snapshot of the current element names in the grid.
- `get_added_element_names(self, grid, previous_names)`
  Summary: Return the names of the elements that were added to the grid
