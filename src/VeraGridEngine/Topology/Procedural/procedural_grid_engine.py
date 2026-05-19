# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Dict, List, TYPE_CHECKING
import random
import numpy as np
import VeraGridEngine.Devices as dev
from VeraGridEngine.enumerations import ProceduralGridMethods
from VeraGridEngine.basic_structures import Mat, Vec, Logger
from scipy.spatial.distance import cdist
from scipy.sparse.csgraph import minimum_spanning_tree
from scipy.special import gammaincinv
from VeraGrid.Gui.Diagrams.MapWidget.grid_map_widget import haversine_distance
from collections import deque
from typing import Optional

from VeraGridEngine.Topology.Procedural.procedural_grid_debugger import ProceduralGridDebugger
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.CatalogueOptimization.catalogue_optimization_driver import (
    CatalogueOptimizationDriver,
    CatalogueOptimizationOptions,
)
from VeraGridEngine.Simulations.CatalogueOptimization.Problems.catalogue_problem import (
    CatalogueOptimizationProblem,
)

if TYPE_CHECKING:
    from VeraGridEngine.Devices.multi_circuit import MultiCircuit


def coord_calc(current_bus_lon: float, current_bus_lat: float, length: float, coord_out: Vec) -> Vec:
    """
    Calculate the coordinates of the next bus based on the current bus,
    the length to be covered (in km), and the output coordinates (in degrees).

    The bearing must be computed in physical km space (not raw degree space) so
    that intermediate buses lie on the geographic straight line between the two
    endpoints. Using raw degree differences would distort the direction because
    1° of longitude is shorter in km than 1° of latitude at non-equatorial latitudes.

    :param current_bus_lon: Longitude of the current bus in degrees.
    :param current_bus_lat: Latitude of the current bus in degrees.
    :param length: Distance to advance toward ``coord_out`` in km.
    :param coord_out: Target coordinates as ``[longitude, latitude]`` in degrees.
    :return: New coordinates as ``[longitude, latitude]`` in degrees.
    """
    km_per_deg_lat: float = 111.0
    km_per_deg_lon: float = 111.0 * np.cos(np.radians(current_bus_lat))

    # Convert the degree-space displacement to physical km so the bearing is
    # computed in a (locally) isotropic coordinate frame
    physical_dx: float = (coord_out[0] - current_bus_lon) * km_per_deg_lon
    physical_dy: float = (coord_out[1] - current_bus_lat) * km_per_deg_lat

    line_angle: float = np.arctan2(physical_dy, physical_dx)

    delta_lon: float = np.cos(line_angle) * length / km_per_deg_lon
    delta_lat: float = np.sin(line_angle) * length / km_per_deg_lat

    new_coord: Vec = np.array([current_bus_lon + delta_lon, current_bus_lat + delta_lat])

    return new_coord


def instantiate_branch_from_template(template_branch,
                                     current_bus: dev.Bus,
                                     next_bus: dev.Bus,
                                     length: float):
    """
    Create a new branch object using an existing branch as template.
    """

    if isinstance(template_branch, dev.Line):
        new_branch = dev.Line(
            name=f"AC_Line_{current_bus.name}_{next_bus.name}",
            bus_from=current_bus,
            bus_to=next_bus,
            length=length,
            r=template_branch.R,
            x=template_branch.X,
            b=template_branch.B,
            rate=template_branch.rate,
            capex=template_branch.capex,
            opex=template_branch.opex
        )
        return new_branch

    if isinstance(template_branch, dev.Transformer2W):
        new_branch = dev.Transformer2W(
            name=f"TR_{current_bus.name}_{next_bus.name}",
            bus_from=current_bus,
            bus_to=next_bus,
            HV=max(current_bus.Vnom, next_bus.Vnom),
            LV=min(current_bus.Vnom, next_bus.Vnom),
            r=template_branch.R,
            x=template_branch.X,
            rate=template_branch.rate,
            capex=template_branch.capex,
            opex=template_branch.opex
        )
        new_branch.Pcu = template_branch.Pcu
        new_branch.Pfe = template_branch.Pfe
        return new_branch

    return None


class TransitionMatrix:

    def __init__(self, grid: MultiCircuit):

        # Find out my unique voltages
        voltages = set()
        for branch in grid.get_branches(add_vsc=True, add_hvdc=True, add_switch=True):
            V1 = branch.bus_from.Vnom
            V2 = branch.bus_to.Vnom
            voltages.add(V1)
            voltages.add(V2)

        self.voltages_sorted = sorted(voltages)
        self.voltages_dict = {v: i for i, v in enumerate(self.voltages_sorted)}
        self.transition_matrix = np.zeros((len(self.voltages_sorted), len(self.voltages_sorted)))
        for branch in grid.get_branches(add_vsc=True, add_hvdc=True, add_switch=True):
            V1 = branch.bus_from.Vnom
            V2 = branch.bus_to.Vnom
            i1 = self.voltages_dict[V1]
            i2 = self.voltages_dict[V2]

            self.transition_matrix[i1, i2] += 1.0
            self.transition_matrix[i2, i1] += 1.0

        # normalize
        for i in range(self.transition_matrix.shape[0]):
            self.transition_matrix[i, :] /= self.transition_matrix[i, :].sum()

        # template dictionary
        self.template_dict = self.template_dictionary(grid)

    def at(self, V1: float, V2: float):
        """
        Get probability associated to V1, transitioning to V2
        :param V1: Voltage Source
        :param V2: Voltage target
        :return: Probability of transition
        """

        i1 = self.voltages_dict[V1]
        i2 = self.voltages_dict[V2]
        return self.transition_matrix[i1, i2]

    @staticmethod
    def template_dictionary(grid: MultiCircuit) -> Dict[float, Dict[float, List[tuple[object, float]]]]:
        """
        Build a nested dictionary of branch templates grouped by voltage transition.

        The outer key is the lower voltage (kV) and the inner key is the higher voltage
        (kV), so (132 kV → 220 kV) is stored as template_dict[132.0][220.0].
        Both voltages are sorted so that (132, 220) and (220, 132) map to the same entry.

        The values are lists of (branch_object, probability) tuples where probability
        is assigned uniformly among all branches that share the same voltage transition.

        :param grid: MultiCircuit instance
        :return: Nested dict {v_lo: {v_hi: [(branch_object, probability), ...]}}
        """
        grouped_elements: Dict[float, Dict[float, List[object]]] = dict()

        for branch in grid.get_branches(add_vsc=True, add_hvdc=True, add_switch=True):

            v1 = float(branch.bus_from.Vnom)
            v2 = float(branch.bus_to.Vnom)
            v_lo = min(v1, v2)
            v_hi = max(v1, v2)

            if v_lo not in grouped_elements:
                grouped_elements[v_lo] = dict()

            if v_hi not in grouped_elements[v_lo]:
                grouped_elements[v_lo][v_hi] = list()

            grouped_elements[v_lo][v_hi].append(branch)

        template_dict: Dict[float, Dict[float, List[tuple[object, float]]]] = dict()

        for v_lo, inner in grouped_elements.items():
            template_dict[v_lo] = dict()
            for v_hi, branch_objects in inner.items():
                n_el = len(branch_objects)

                if n_el == 0:
                    template_dict[v_lo][v_hi] = list()
                    continue

                probability = 1.0 / n_el
                template_dict[v_lo][v_hi] = [(branch_object, probability) for branch_object in branch_objects]

        return template_dict

    def get_most_likely_transition_voltage(self, V: float):
        """
        Get the most likely voltage to transition to, given a voltage
        :param V: Some voltage source
        :return: The most likely voltage target
        """
        i1 = self.voltages_dict[V]
        i2 = np.argmax(self.transition_matrix[i1, :])
        return self.voltages_sorted[i2]

class ProceduralGridGraph:

    def __init__(self,
                 target_buses: List[dev.Bus],
                 candidate_buses: List[dev.Bus],
                 max_iterations: int = 1000,
                 logger: Logger | None = None):
        """

        :param target_buses:
        :param candidate_buses:
        :param max_iterations: Maximum number of iterations
        """
        self.target_buses: List[dev.Bus] = target_buses
        self.candidate_buses: List[dev.Bus] = candidate_buses
        self.max_iterations: int = max_iterations
        self.logger: Logger = Logger() if logger is None else logger

        self.n_target = len(self.target_buses)
        self.n_candidate = len(self.candidate_buses)

        self.n_steiner = self.n_target + self.n_candidate - 2

        # 1. Parse inputs
        self.coord_candidate = np.zeros((self.n_candidate, 2))  # dim, (lon, lat)
        self.coord_target = np.zeros((self.n_target, 2))  # dim, (lon, lat)
        Vnom_kV_candidate = np.zeros(self.n_candidate)
        Vnom_kV_target = np.zeros(self.n_target)

        self.min_lon = np.inf
        self.min_lat = np.inf
        self.max_lon = -np.inf
        self.max_lat = -np.inf

        for i, bus in enumerate(self.target_buses):
            self.coord_target[i, 0] = bus.longitude
            self.coord_target[i, 1] = bus.latitude
            Vnom_kV_target[i] = bus.Vnom

            self.min_lon = min(self.min_lon, bus.longitude)
            self.min_lat = min(self.min_lat, bus.latitude)
            self.max_lon = max(self.max_lon, bus.longitude)
            self.max_lat = max(self.max_lat, bus.latitude)

        for i, bus in enumerate(self.candidate_buses):
            self.coord_candidate[i, 0] = bus.longitude
            self.coord_candidate[i, 1] = bus.latitude
            Vnom_kV_candidate[i] = bus.Vnom

            self.min_lon = min(self.min_lon, bus.longitude)
            self.min_lat = min(self.min_lat, bus.latitude)
            self.max_lon = max(self.max_lon, bus.longitude)
            self.max_lat = max(self.max_lat, bus.latitude)

        self.base_coords = np.r_[self.coord_candidate, self.coord_target]
        self.base_voltages = np.r_[Vnom_kV_candidate, Vnom_kV_target]

    def calculate_fitness(self, mu_lon: Vec, mu_lat: Vec):
        """
        VSA Fitness: MST Length + Degree Penalty.
        :param mu_lat: steiner points latitudes
        :param mu_lon: steiner points longitudes
        """
        steiner_coords = np.c_[mu_lon, mu_lat]
        all_coords = np.r_[self.base_coords, steiner_coords]

        # MST Calculation
        dist_matrix = cdist(all_coords, all_coords)
        mst_matrix = minimum_spanning_tree(dist_matrix)
        mst_array = mst_matrix.toarray()

        total_length = np.sum(mst_array)

        # Penalty for Degree > 3 (Geometrically impossible for optimal ST)
        adj = mst_array + mst_array.T
        degrees = np.count_nonzero(adj, axis=1)
        steiner_degrees = degrees[self.n_target + self.n_candidate:]

        penalty = 0
        for d in steiner_degrees:
            if d > 3: penalty += 10000

        return total_length + penalty

    def run_vsa(self):
        """

        :return: best_solution (dim, (lat, lon))
        """
        dim = self.n_steiner

        mu_lon = np.random.uniform(self.min_lon, self.max_lon, dim)
        mu_lat = np.random.uniform(self.min_lat, self.max_lat, dim)

        best_fitness = self.calculate_fitness(mu_lon=mu_lon, mu_lat=mu_lat)
        best_solution = np.c_[mu_lon, mu_lat]

        convergence_history = []

        radius_max = np.sqrt((self.max_lat - self.min_lat) ** 2 + (self.max_lon - self.min_lon) ** 2) / 2.0
        x_param = 0.1

        for k in range(self.max_iterations):
            a_t = 1.0 - (k / self.max_iterations)
            a_t = max(a_t, 0.0001)
            r_t = radius_max * (1 / x_param) * gammaincinv(x_param, a_t)

            candidate_lon = mu_lon + r_t * np.random.randn(dim)
            candidate_lat = mu_lat + r_t * np.random.randn(dim)

            candidate_lon = np.clip(candidate_lon, self.min_lon, self.max_lon)
            candidate_lat = np.clip(candidate_lat, self.min_lat, self.max_lat)

            fitness = self.calculate_fitness(mu_lon=candidate_lon, mu_lat=candidate_lat)

            if fitness < best_fitness:
                best_fitness = fitness
                mu_lon = candidate_lon
                mu_lat = candidate_lat
                best_solution = np.c_[candidate_lon, candidate_lat]

            convergence_history.append(best_fitness)

        return best_solution, convergence_history

    def prune_redundant_nodes(self, steiner_coords: Mat):
        """
        Iteratively removes Steiner points with Degree <= 2.
        :param steiner_coords: steiner points coordinates (dim, (lon, lat))
        """
        current_steiner = steiner_coords.copy()

        while True:
            if len(current_steiner) == 0:
                break

            # 1. Build MST with current set
            all_coords = np.r_[self.base_coords, current_steiner]

            dist_matrix = cdist(all_coords, all_coords, metric='euclidean')
            mst_array = minimum_spanning_tree(dist_matrix).toarray()
            # cost = np.sum(mst_array)

            # 2. Check degrees
            adj = mst_array + mst_array.T
            degrees = np.count_nonzero(adj, axis=1)

            # Extract Steiner degrees (indices after fixed nodes)
            st_degrees = degrees[self.n_target + self.n_candidate:]

            # 3. Identify useful points (Degree >= 3)
            useful_indices = np.where(st_degrees > 2)[0]

            # If no nodes are redundant, stop pruning
            if len(useful_indices) == len(current_steiner):
                break

            self.logger.add_info(f"Pruning... Removed {len(current_steiner) - len(useful_indices)} nodes.")
            current_steiner = current_steiner[useful_indices, :]

        return current_steiner

    def remove_existing_edges(
            self,
            mst_matrix: np.ndarray,
            existing_connections: set[tuple[int, int]],
            n_fixed: int,
    ) -> np.ndarray:
        """
        Remove MST edges that already exist in the incumbent grid.

        This method is graph-only: it does not know anything about VeraGrid objects.
        It only receives:
        - the MST matrix,
        - the set of existing fixed-node connections,
        - the number of fixed nodes (candidate + target).

        Only edges between fixed nodes are checked. Edges involving Steiner nodes
        are always kept.

        :param mst_matrix: MST adjacency matrix
        :param existing_connections: Set of existing graph edges as index pairs
        :param n_fixed: Number of fixed nodes at the beginning of the node ordering
        :return: Filtered MST adjacency matrix
        """
        cleaned_mst = mst_matrix.copy()

        rows, cols = np.where(cleaned_mst > 0)

        for i, j in zip(rows, cols):
            if i >= n_fixed or j >= n_fixed:
                continue

            key = (min(i, j), max(i, j))

            if key in existing_connections:
                cleaned_mst[i, j] = 0.0

        return cleaned_mst


class Topology:
    """
    Represents the physical layout using domain objects.
    Contains a Graph instance via composition.
    """

    def __init__(self,
                 edges: list[tuple[int, int]],
                 all_buses: List[dev.Bus],
                 grid: MultiCircuit,
                 transition_matrix: TransitionMatrix,
                 discretization: float = 25.0,
                 logger: Logger | None = None):

        self.edges = edges
        self.all_buses = all_buses
        self.grid = grid
        self.transition_matrix = transition_matrix
        self.discretization = discretization  # km between buses
        self.logger: Logger = Logger() if logger is None else logger

        self.intermediate_buses: List[dev.Bus] = list()  # buses generated in the markov process
        self.new_lines: List[dev.Line] = list()  # lines created during topology generation
        self.new_transformers: List[dev.Transformer2W] = list()  # transformers created during topology generation

    def generate_markov(self):
        """
        Generates combinations that are valid by construction.
        """

        for edge in self.edges:

            lengths = []

            input_bus = self.all_buses[edge[0]]
            output_bus = self.all_buses[edge[1]]

            distance = haversine_distance(
                    lat1=input_bus.latitude,
                    lon1=input_bus.longitude,
                    lat2=output_bus.latitude,
                    lon2=output_bus.longitude
                ) # distance = np.linalg.norm(coord_input - coord_output)

            if distance % self.discretization == 0:
                n_buses = int(distance // self.discretization + 1)
                n_slots = int(n_buses - 1)
                for i in range(n_slots):
                    lengths.append(self.discretization)
            else:
                n_buses = int(distance // self.discretization + 2)
                n_slots = int(n_buses - 1)
                for i in range(n_slots):
                    if i == n_slots - 1:
                        lengths.append(distance % self.discretization)
                    else:
                        lengths.append(self.discretization)

            accumulated_length = 0.0
            conn_counter = 0
            intermediate_bus_counter = 0

            # Add the first bus to the Multicircuit
            next_bus = input_bus

            voltage_options = self.transition_matrix.voltages_sorted

            while accumulated_length < distance:

                # Update next bus to current bus
                current_bus = next_bus

                # Check if we are at the last connection
                is_last_conn = (conn_counter == n_slots - 1)

                # Add next bus to Multicircuit
                if is_last_conn:
                    next_bus = output_bus

                    if current_bus.Vnom != next_bus.Vnom:
                        # Any voltage change at the last slot: use last_bus_fix so that a
                        # line covers the geographic distance and the transformer is placed
                        # at the endpoint, regardless of whether a direct template exists.
                        self.logger.add_info(
                            msg=f"Voltage change from {current_bus.Vnom}kV to {next_bus.Vnom}kV. "
                                f"Creating voltage bridge near the output bus.",
                            device=f"edge {edge}"
                        )

                        next_bus, intermediate_bus_counter = self.last_bus_fix(
                            current_bus=current_bus,
                            output_bus=output_bus,
                            edge=edge,
                            intermediate_bus_counter=intermediate_bus_counter,
                        )
                    else:
                        # Same voltage: direct line connection, no bridge needed
                        None

                else:
                    next_bus_options = sorted([b for b in voltage_options])
                    row_idx = self.transition_matrix.voltages_dict[current_bus.Vnom]
                    current_transitions = self.transition_matrix.transition_matrix[row_idx, :]

                    # random.choices returns a list, so get the first element [0]
                    next_bus_vnom = random.choices(next_bus_options, weights=current_transitions, k=1)[0]
                    next_coord = coord_calc(
                        current_bus_lon=current_bus.longitude,
                        current_bus_lat=current_bus.latitude,
                        length=lengths[conn_counter],
                        coord_out=np.array([output_bus.longitude, output_bus.latitude]),
                    )

                    next_bus = dev.Bus(
                        name=f"Intermediate_{input_bus.name}_{output_bus.name}_{intermediate_bus_counter}",
                        Vnom=float(next_bus_vnom),
                        is_dc=current_bus.is_dc,
                        longitude=float(next_coord[0]),
                        latitude=float(next_coord[1]),
                    )
                    next_bus.Vm_cost = next_bus.Vnom * next_bus.Vm_cost

                    self.grid.add_bus(obj=next_bus)
                    self.intermediate_buses.append(next_bus)
                    intermediate_bus_counter += 1

                v1 = float(current_bus.Vnom)
                v2 = float(next_bus.Vnom)
                v_lo = min(v1, v2)
                v_hi = max(v1, v2)

                template_options = self.transition_matrix.template_dict.get(v_lo, dict()).get(v_hi, list())

                if not template_options:
                    self.logger.add_warning(
                        msg=f"No template branches for transition {v_lo}kV-{v_hi}kV. Skipping edge {edge}.",
                        device=f"edge {edge}"
                    )
                    break

                template_branches = [item[0] for item in template_options]
                template_probs = [item[1] for item in template_options]
                template_branch = random.choices(template_branches, weights=template_probs, k=1)[0]

                new_branch = instantiate_branch_from_template(
                    template_branch=template_branch,
                    current_bus=current_bus,
                    next_bus=next_bus,
                    length=lengths[conn_counter],
                )

                self.logger.add_info(
                    msg=f"Branch type={type(new_branch).__name__}, "
                        f"accumulated_length={accumulated_length:.1f}, distance={distance:.1f}, "
                        f"conn_counter={conn_counter}",
                    device=f"edge {edge}"
                )

                if new_branch is None:
                    self.logger.add_warning(
                        msg=f"Could not instantiate branch for transition {v_lo}kV-{v_hi}kV. Skipping edge {edge}.",
                        device=f"edge {edge}"
                    )
                    break

                self.add_branch_to_grid(branch=new_branch)

                if isinstance(new_branch, dev.Line):
                    accumulated_length += lengths[conn_counter]
                    conn_counter += 1

            # TODO: Add the merge_lines function outside generate_markov and inside Topology
            # combination, length_elements_ = merge_lines(combination, length_elements_)

        return self.intermediate_buses

    def add_branch_to_grid(self, branch) -> None:
        """
        Add a branch object to the correct container of the expansion grid.
        """
        if isinstance(branch, dev.Line):
            self.grid.add_line(obj=branch)
            self.new_lines.append(branch)
            return

        if isinstance(branch, dev.Transformer2W):
            self.grid.add_transformer2w(obj=branch)
            self.new_transformers.append(branch)
            return

        # TODO: Extend later for VSC, HVDC, switches, etc.

    def find_voltage_path(self, start_v: float, end_v: float) -> Optional[list[float]]:
        """
        Find a voltage path between start_v and end_v using the transitions
        available in template_dict.

        :param start_v: Initial voltage
        :param end_v: Final voltage
        :return: List of voltages [start_v, ..., end_v] or None if no path exists
        """
        start_v = float(start_v)
        end_v = float(end_v)

        if start_v == end_v:
            return [start_v]

        adjacency: dict[float, set[float]] = dict()

        for v_lo, inner in self.transition_matrix.template_dict.items():
            for v_hi, template_options in inner.items():
                if len(template_options) == 0:
                    continue

                if v_lo not in adjacency:
                    adjacency[v_lo] = set()
                if v_hi not in adjacency:
                    adjacency[v_hi] = set()

                adjacency[v_lo].add(v_hi)
                adjacency[v_hi].add(v_lo)

        if start_v not in adjacency or end_v not in adjacency:
            return None

        queue = deque([start_v])
        parent: dict[float, Optional[float]] = {start_v: None}

        while queue:
            v = queue.popleft()

            if v == end_v:
                break

            for neigh in adjacency[v]:
                if neigh not in parent:
                    parent[neigh] = v
                    queue.append(neigh)

        if end_v not in parent:
            return None

        path: list[float] = list()
        v = end_v
        while v is not None:
            path.append(v)
            v = parent[v]

        path.reverse()
        return path

    def last_bus_fix(
            self,
            current_bus: dev.Bus,
            output_bus: dev.Bus,
            edge: tuple[int, int],
            intermediate_bus_counter: int,
    ) -> tuple[dev.Bus, int]:
        """
        Create a voltage bridge near the output bus so that the last geographical
        segment can still be connected and the final output voltage can be reached.

        Strategy:
        - create a first bridge bus at the output coordinates with the same voltage
          as current_bus,
        - connect current_bus to that first bridge bus later using the normal last
          line section,
        - create the remaining zero-length voltage transition chain from that first
          bridge bus to output_bus.

        :param current_bus: Current bus at the start of the last slot
        :param output_bus: Final target bus
        :param edge: Edge being processed
        :param intermediate_bus_counter: Counter for naming intermediate buses
        :return: (first_bridge_bus, updated_intermediate_bus_counter)
        """
        voltage_path = self.find_voltage_path(
            start_v=float(current_bus.Vnom),
            end_v=float(output_bus.Vnom),
        )

        if voltage_path is None:
            raise RuntimeError(
                f"No voltage path exists from {current_bus.Vnom} kV to {output_bus.Vnom} kV."
            )

        if len(voltage_path) < 2:
            raise RuntimeError(
                f"Invalid voltage path from {current_bus.Vnom} kV to {output_bus.Vnom} kV: {voltage_path}"
            )

        # First bridge bus: same voltage as current_bus, but placed at output coordinates.
        first_bridge_bus = dev.Bus(
            name=f"Intermediate_{current_bus.name}_{output_bus.name}_{intermediate_bus_counter}",
            Vnom=float(current_bus.Vnom),
            is_dc=current_bus.is_dc,
            longitude=float(output_bus.longitude),
            latitude=float(output_bus.latitude),
        )
        first_bridge_bus.Vm_cost = first_bridge_bus.Vnom * first_bridge_bus.Vm_cost

        self.grid.add_bus(obj=first_bridge_bus)
        self.intermediate_buses.append(first_bridge_bus)
        intermediate_bus_counter += 1

        previous_bus = first_bridge_bus

        # Build the voltage-transition chain near the output bus.
        # voltage_path is [current_v, ..., output_v]
        for idx, next_voltage in enumerate(voltage_path[1:], start=1):

            is_last_step = (idx == len(voltage_path) - 1)

            if is_last_step:
                next_bus = output_bus
            else:
                next_bus = dev.Bus(
                    name=f"Intermediate_{current_bus.name}_{output_bus.name}_{intermediate_bus_counter}",
                    Vnom=float(next_voltage),
                    is_dc=current_bus.is_dc,
                    longitude=float(output_bus.longitude),
                    latitude=float(output_bus.latitude),
                )
                next_bus.Vm_cost = next_bus.Vnom * next_bus.Vm_cost

                self.grid.add_bus(obj=next_bus)
                self.intermediate_buses.append(next_bus)
                intermediate_bus_counter += 1

            v1 = float(previous_bus.Vnom)
            v2 = float(next_bus.Vnom)
            v_lo = min(v1, v2)
            v_hi = max(v1, v2)

            template_options = self.transition_matrix.template_dict.get(v_lo, dict()).get(v_hi, list())
            if len(template_options) == 0:
                raise RuntimeError(
                    f"No template branches available for transition {v_lo}kV-{v_hi}kV "
                    f"while fixing edge {edge}."
                )

            template_branches = [item[0] for item in template_options]
            template_probs = [item[1] for item in template_options]
            template_branch = random.choices(template_branches, weights=template_probs, k=1)[0]

            new_branch = instantiate_branch_from_template(
                template_branch=template_branch,
                current_bus=previous_bus,
                next_bus=next_bus,
                length=0.0,
            )

            if new_branch is None:
                raise RuntimeError(
                    f"Could not instantiate branch for transition {v_lo}kV-{v_hi}kV "
                    f"while fixing edge {edge}."
                )

            self.add_branch_to_grid(branch=new_branch)
            previous_bus = next_bus

        return first_bridge_bus, intermediate_bus_counter


class ProceduralGridComputationEngine:
    """
    Core engine for procedural grid expansion calculations.
    """

    def __init__(self,
                 grid: MultiCircuit,
                 method: ProceduralGridMethods,
                 targets: List[dev.Substation],
                 candidates: List[dev.Substation],
                 logger: Logger | None = None):
        """

        :param grid: MultiCircuit instance
        :param method: Method to use
        :param targets: List of substations to connect
        :param candidates: List of Substation that we may want to connect
        """
        self.grid = grid
        self.method = method
        self.targets_substations = targets
        self.candidates_substations = candidates
        self.logger: Logger = Logger() if logger is None else logger

        self.target_buses: List[dev.Bus] = list()
        self.candidate_buses: List[dev.Bus] = list()
        self.steiner_buses: List[dev.Bus] = list()  # this is a result
        self.intermediate_buses: List[dev.Bus] = list()  # buses generated in the markov process
        self.new_lines: List[dev.Line] = list()  # lines created during topology generation
        self.new_transformers: List[dev.Transformer2W] = list()  # transformers created during topology generation

        self.debugger = ProceduralGridDebugger(enabled=True)

        candidate_counter = 0
        for sg in self.candidates_substations:
            for bus in self.grid.get_substation_buses(sg):
                lon, lat = bus.try_to_find_coordinates()
                bus.longitude = lon
                bus.latitude = lat
                bus.Vm_cost = bus.Vnom * bus.Vm_cost
                self.candidate_buses.append(bus)
                candidate_counter += 1

        target_counter = 0
        for sg in self.targets_substations:
            for bus in self.grid.get_substation_buses(sg):
                lon, lat = bus.try_to_find_coordinates()
                bus.longitude = lon
                bus.latitude = lat
                bus.Vm_cost = bus.Vnom * bus.Vm_cost
                self.target_buses.append(bus)
                target_counter += 1

        # TRANSITION_MATRIX = {
        #     132: {132: 0.7, 220: 0.15, 380: 0.15, 500: 0},
        #     220: {132: 0.15, 220: 0.7, 380: 0.1, 500: 0.05},
        #     380: {132: 0.15, 220: 0.1, 380: 0.7, 500: 0.05},
        #     500: {132: 0, 220: 0.15, 380: 0.15, 500: 0.7}
        # }

        # TRANSITION_MATRIX = {
        #     132: {132: {template_A: 0.35, template_B: 0.35}, 220: {template_A: 0.075, template_B: 0.075}, 380: {template_A: 0.075, template_B: 0.075}, 500: {template_A: 0.00, template_B: 0.00}},
        #     220: {132: {template_A: 0.075, template_B: 0.075}, 220: {template_A: 0.35, template_B: 0.35}, 380: {template_A: 0.05, template_B: 0.05}, 500: {template_A: 0.025, template_B: 0.025}},
        #     380: {132: {template_A: 0.075, template_B: 0.075}, 220: {template_A: 0.05, template_B: 0.05}, 380: {template_A: 0.35, template_B: 0.35}, 500: {template_A: 0.025, template_B: 0.025}},
        #     500: {132: {template_A: 0.00, template_B: 0.00}, 220: {template_A: 0.075, template_B: 0.075}, 380: {template_A: 0.075, template_B: 0.075}, 500: {template_A: 0.35, template_B: 0.35}},
        # }

        self.transition_matrix = TransitionMatrix(grid)

    def get_buses(self) -> List[dev.Bus]:
        """
        Get list of all the incumbent buses in the calculation
        :return:
        """
        return self.target_buses + self.candidate_buses + self.steiner_buses + self.intermediate_buses

    def get_new_buses(self) -> List[dev.Bus]:
        """
        Get only the newly created buses (Steiner points + Markov intermediate buses).
        These have no substation assigned and need one for map rendering.
        :return:
        """
        return self.steiner_buses + self.intermediate_buses

    def get_new_lines(self) -> List[dev.Line]:
        """
        Get only the newly created Line objects added during topology generation.
        :return:
        """
        return self.new_lines

    def get_new_transformers(self) -> List[dev.Transformer2W]:
        """
        Get only the newly created Transformer2W objects added during topology generation.
        :return:
        """
        return self.new_transformers

    def run_steiner_alone(self):
        """
        Executes the Steiner Tree algorithm without further optimization.
        """

        # 2A. Run VSA: Create an initial radial topology with a Steiner tree approach
        network = ProceduralGridGraph(target_buses=self.target_buses,
                                      candidate_buses=self.candidate_buses,
                                      max_iterations=15000,
                                      logger=self.logger)

        initial_steiner_points, history = network.run_vsa()
        # 2B. Prune redundant nodes
        final_steiner_pts = network.prune_redundant_nodes(initial_steiner_points)
        # 2C. Get edges of the final network
        coords_final_network = np.r_[network.base_coords, final_steiner_pts]
        dist_matrix = cdist(coords_final_network, coords_final_network, metric='euclidean')
        final_mst = minimum_spanning_tree(dist_matrix).toarray()

        existing_connections = self.get_existing_fixed_bus_connections()
        n_fixed = len(self.candidate_buses) + len(self.target_buses)

        final_mst = network.remove_existing_edges(
            mst_matrix=final_mst,
            existing_connections=existing_connections,
            n_fixed=n_fixed,
        )

        # generate edges
        rows, cols = np.where(final_mst > 0)
        edges = list(zip(rows, cols))

        # 2E. Assign voltages to Steiner Points
        distances = np.zeros(network.base_coords.shape[0])
        closest_voltage = np.zeros(final_steiner_pts.shape[0])

        for i_sp in range(final_steiner_pts.shape[0]):
            for i_base in range(network.base_coords.shape[0]):
                dist = haversine_distance(
                    lat1=network.base_coords[i_base, 1],
                    lon1=network.base_coords[i_base, 0],
                    lat2=final_steiner_pts[i_sp, 1],
                    lon2=final_steiner_pts[i_sp, 0],
                )
                distances[i_base] = dist

            closest = np.argmin(distances)
            closest_voltage[i_sp] = network.base_voltages[closest]

        # 2F. Create Node buses (M, N, S)
        for i in range(final_steiner_pts.shape[0]):
            sp_bus = dev.Bus(
                name=f"Intermediate_{i}",
                Vnom=float(closest_voltage[i]),
                longitude=final_steiner_pts[i, 0],
                latitude=final_steiner_pts[i, 1],
            )
            # Remove list if you do not need it anymore
            self.steiner_buses.append(sp_bus)
            self.grid.add_bus(obj=sp_bus)

        all_buses = self.candidate_buses + self.target_buses + self.steiner_buses

        # 3. Create Topology from Graph

        # TRANSITION_MATRIX = {
        #     132: {132: 0.7, 220: 0.15, 380: 0.15, 500: 0},
        #     220: {132: 0.15, 220: 0.7, 380: 0.1, 500: 0.05},
        #     380: {132: 0.15, 220: 0.1, 380: 0.7, 500: 0.05},
        #     500: {132: 0, 220: 0.15, 380: 0.15, 500: 0.7}
        # }

        topology = Topology(edges,
                            all_buses,
                            self.grid,
                            transition_matrix=self.transition_matrix,
                            discretization=25.0,
                            logger=self.logger)

        before_names = self.debugger.snapshot_grid_element_names(self.grid)

        self.intermediate_buses = topology.generate_markov()
        self.new_lines = topology.new_lines
        self.new_transformers = topology.new_transformers

        added_names = self.debugger.get_added_element_names(
            grid=self.grid,
            previous_names=before_names,
        )

        for name in added_names:
            self.logger.add_info(msg="Added element", device=name)

        return self.grid

    def get_existing_fixed_bus_connections(self) -> set[tuple[int, int]]:
        """
        Build the set of existing direct connections between fixed buses
        (candidate + target) in graph-index form.

        The returned index pairs are expressed in the same ordering used by
        ProceduralGridGraph.base_coords:
            [candidate_buses..., target_buses...]

        :return: Set of existing fixed-bus connections as index pairs
        """
        fixed_buses = self.candidate_buses + self.target_buses
        bus_index_by_id = {id(bus): i for i, bus in enumerate(fixed_buses)}

        existing_connections: set[tuple[int, int]] = set()

        for branch in self.grid.get_branches(add_vsc=True, add_hvdc=True, add_switch=True):
            i = bus_index_by_id.get(id(branch.bus_from))
            j = bus_index_by_id.get(id(branch.bus_to))

            if i is None or j is None:
                continue

            key = (min(i, j), max(i, j))
            existing_connections.add(key)

        return existing_connections

    def run_steiner_tree_and_optimization(self,
                                          pf_options: PowerFlowOptions,
                                          max_eval_per_var: int) -> "MultiCircuit":
        """
        Execute the Steiner tree topology generation first, then run an NSGA-3
        catalogue-template optimization over the newly created branches.

        The two-stage flow mirrors what the engine offers piecewise: first the
        topology is grown via :meth:`run_steiner_alone`, which populates
        ``self.new_lines`` and ``self.new_transformers``; then a synchronous
        catalogue optimization tunes the per-branch templates of those new
        branches only (existing infrastructure is left untouched). On
        completion the grid is left at the best Pareto member's templates so
        the caller observes the optimizer's top recommendation.

        :param pf_options: power flow options used by the inner PF evaluations
            performed by the catalogue problem.
        :param max_eval_per_var: per-decision-variable evaluation budget. The
            actual NSGA-3 evaluation cap becomes
            ``max_eval_per_var * problem.n_vars()``.
        :return: the (in-place mutated) :class:`MultiCircuit` reference.
        """
        # 1. Build the topology. Mutates self.grid and populates
        #    self.new_lines / self.new_transformers, which are the candidates
        #    for catalogue optimisation in step 2.
        self.run_steiner_alone()

        # 2. Build the optimisation scope: only the newly created branches.
        #    Pre-existing infrastructure is intentionally left untouched.
        selected_branches: List = list(self.new_lines) + list(self.new_transformers)

        # 2a. If the Steiner step produced no new branches, there is nothing
        #     to optimise. Surface a warning to the logger and exit early.
        if len(selected_branches) == 0:
            self.logger.add_warning(
                msg="No new branches were created by the Steiner step; "
                    "catalogue optimization skipped."
            )
            return self.grid
        else:
            pass

        # 3. Build the catalogue problem. The constructor raises ValueError
        #    when no slot has more than one compatible template (nothing to
        #    optimise over). We catch and report, then return the topology
        #    as-is so the caller still gets a usable grid.
        try:
            problem: CatalogueOptimizationProblem = CatalogueOptimizationProblem(
                grid=self.grid,
                pf_options=pf_options,
                selected_branches=selected_branches,
                voltage_tolerance=0.1,
            )
        except ValueError as ex:
            self.logger.add_warning(
                msg=f"Catalogue optimization skipped: {ex}"
            )
            return self.grid

        # 4. Compose options. max_eval is the per-var budget scaled by the
        #    number of decision slots, matching the standalone catalogue
        #    feature in simulations.py.
        max_eval: int = int(max_eval_per_var) * problem.n_vars()
        options: CatalogueOptimizationOptions = CatalogueOptimizationOptions(
            max_eval=max_eval,
            pf_options=pf_options,
        )

        # 5. Build and run the driver synchronously. We do NOT route through
        #    session.run here because this method is engine-side and must be
        #    callable without a running GUI session.
        driver: CatalogueOptimizationDriver = CatalogueOptimizationDriver(
            grid=self.grid,
            options=options,
            problem=problem,
        )
        driver.run()

        # 6. Merge the driver's logger into the engine logger so its messages
        #    reach the GUI LogsDialogue together with the topology-phase logs.
        self.logger += driver.logger

        # 7. Apply the best Pareto member's templates so the returned grid
        #    reflects the optimizer's top recommendation. The driver leaves
        #    the grid at baseline after each evaluation (per the problem's
        #    snapshot/restore convention), so we restore-then-apply to land
        #    on a deterministic, optimiser-chosen state.
        if len(driver.results.sorting_indices) > 0:
            best_x = driver.results.x[driver.results.sorting_indices[0], :]
            driver.problem._restore_baseline()
            driver.problem._apply_combination(x=best_x)
        else:
            # No Pareto results available (e.g. budget too small) - leave the
            # grid at baseline templates.
            pass

        return self.grid
