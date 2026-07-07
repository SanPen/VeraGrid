from __future__ import annotations
from typing import List, Tuple

import numpy as np
import matplotlib.pyplot as plt
import VeraGridEngine.Devices as dev


class ProceduralGridDebugger:
    """
    Helper class for plotting and validating intermediate results during
    procedural grid generation.

    This class should only contain debug/inspection utilities and must not
    modify the production objects.
    """
    __slots__ = ("enabled",)

    def __init__(self, enabled: bool = True):
        """
        :param enabled: Enable or disable debug actions
        """
        self.enabled = enabled

    def plot_mst_graph(
        self,
        coords_final_network: np.ndarray,
        edges: List[Tuple[int, int]],
        n_candidate: int,
        n_target: int,
        final_steiner_pts: np.ndarray,
        title: str = "Procedural Grid Graph",
        show_labels: bool = True,
    ) -> None:
        """
        Plot the graph defined by node coordinates and edge list.

        :param coords_final_network: Array of shape (n_nodes, 2) with [lon, lat]
        :param edges: List of node index pairs
        :param n_candidate: Number of candidate buses
        :param n_target: Number of target buses
        :param final_steiner_pts: Array of Steiner point coordinates
        :param title: Plot title
        :param show_labels: Whether to label nodes with their indices
        """
        if not self.enabled:
            return

        plt.figure(figsize=(10, 8))

        for i_from, i_to in edges:
            p1 = coords_final_network[i_from]
            p2 = coords_final_network[i_to]
            plt.plot(
                [p1[0], p2[0]],
                [p1[1], p2[1]],
                "k-",
                linewidth=1.5,
                alpha=0.7,
                zorder=1,
            )

        if n_candidate > 0:
            plt.scatter(
                coords_final_network[:n_candidate, 0],
                coords_final_network[:n_candidate, 1],
                s=80,
                marker="s",
                c="green",
                label="Candidates",
                zorder=2,
            )

        if n_target > 0:
            plt.scatter(
                coords_final_network[n_candidate:n_candidate + n_target, 0],
                coords_final_network[n_candidate:n_candidate + n_target, 1],
                s=80,
                marker="s",
                c="blue",
                label="Targets",
                zorder=2,
            )

        if final_steiner_pts.shape[0] > 0:
            plt.scatter(
                final_steiner_pts[:, 0],
                final_steiner_pts[:, 1],
                s=70,
                marker="o",
                c="gray",
                label="Steiner points",
                zorder=3,
            )

        if show_labels:
            for i, (x, y) in enumerate(coords_final_network):
                plt.text(x, y, str(i), fontsize=8, ha="right", va="bottom")

        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.title(title)
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.axis("equal")
        plt.tight_layout()
        plt.show()

    def print_edges(self, edges: List[Tuple[int, int]]) -> None:
        """
        Print the edge list.

        :param edges: List of node index pairs
        """
        if not self.enabled:
            return

        print("Edges:")
        for i_from, i_to in edges:
            print(f"  {i_from} -> {i_to}")

    def validate_edge_indices(
        self,
        edges: List[Tuple[int, int]],
        n_nodes: int,
    ) -> None:
        """
        Validate that all edge indices are within bounds.

        :param edges: List of node index pairs
        :param n_nodes: Total number of nodes
        """
        if not self.enabled:
            return

        for i_from, i_to in edges:
            if i_from < 0 or i_from >= n_nodes:
                raise ValueError(f"Invalid edge start index: {i_from}")
            if i_to < 0 or i_to >= n_nodes:
                raise ValueError(f"Invalid edge end index: {i_to}")

    def print_voltage_summary(self, voltages: np.ndarray, label: str) -> None:
        """
        Print a simple voltage summary.

        :param voltages: Voltage array
        :param label: Label for the printed block
        """
        if not self.enabled:
            return

        print(f"{label}:")
        print(voltages)

    def snapshot_grid_element_names(self, grid: dev.MultiCircuit) -> set[str]:
        """
        Take a snapshot of the current element names in the grid.

        :param grid: MultiCircuit instance
        :return: Set of element names currently present in the grid
        """
        names: set[str] = set()

        for bus in grid.buses:
            names.add(bus.name)

        for branch in grid.get_branches(add_vsc=True, add_hvdc=True, add_switch=True):
            names.add(branch.name)

        for load in grid.get_loads():
            names.add(load.name)

        for generator in grid.get_generators():
            names.add(generator.name)

        return names

    def get_added_element_names(
            self,
            grid: dev.MultiCircuit,
            previous_names: set[str],
    ) -> list[str]:
        """
        Return the names of the elements that were added to the grid
        after a previous snapshot.

        :param grid: MultiCircuit instance
        :param previous_names: Snapshot of names taken before modification
        :return: Sorted list of newly added element names
        """
        current_names = self.snapshot_grid_element_names(grid=grid)
        added_names = current_names - previous_names
        return sorted(added_names)