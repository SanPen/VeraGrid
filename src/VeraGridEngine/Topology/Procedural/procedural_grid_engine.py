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

if TYPE_CHECKING:
    from VeraGridEngine.Devices.multi_circuit import MultiCircuit


def coord_calc(current_bus_lon: float, current_bus_lat: float, length: float, coord_out: Vec):
    """
    Calculate the coordinates of the next bus based on the current bus,
    the length to be covered (in km), and the output coordinates (in degrees).
    """
    line_angle = np.arctan2(coord_out[1] - current_bus_lat, coord_out[0] - current_bus_lon)
    # Convert length from km to degrees (1 degree lat ≈ 111 km; lon depends on latitude)
    km_per_deg_lat = 111.0
    km_per_deg_lon = 111.0 * np.cos(np.radians(current_bus_lat))
    delta_lon = np.cos(line_angle) * length / km_per_deg_lon
    delta_lat = np.sin(line_angle) * length / km_per_deg_lat
    new_coord = np.array([current_bus_lon + delta_lon, current_bus_lat + delta_lat])

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
    def template_dictionary(grid: MultiCircuit) -> Dict[tuple[float, float], List[tuple[object, float]]]:
        """
        Build a dictionary of branch templates grouped by voltage transition.

        The dictionary keys are voltage transition tuples (V1, V2), always sorted so
        that (132.0, 220.0) and (220.0, 132.0) are treated as the same transition.

        The dictionary values are lists of tuples:
            (branch_name, probability)

        The probability is assigned uniformly among all branch elements that belong
        to the same voltage transition.

        :param grid: MultiCircuit instance
        :return: Dictionary with keys (V1, V2) and values [(element_name, probability), ...]
        """
        grouped_elements: Dict[tuple[float, float], List[object]] = dict()

        for branch in grid.get_branches(add_vsc=True, add_hvdc=True, add_switch=True):

            v_from = branch.bus_from.Vnom
            v_to = branch.bus_to.Vnom

            v1 = float(v_from)
            v2 = float(v_to)
            transition_key = (min(v1, v2), max(v1, v2))

            if transition_key not in grouped_elements:
                grouped_elements[transition_key] = list()

            grouped_elements[transition_key].append(branch)

        template_dict: Dict[tuple[float, float], List[tuple[object, float]]] = dict()

        for transition_key, branch_objects in grouped_elements.items():
            n_el = len(branch_objects)

            if n_el == 0:
                template_dict[transition_key] = list()
                continue

            probability = 1.0 / n_el
            template_dict[transition_key] = [(branch_object, probability) for branch_object in branch_objects]

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
                        name=f"Intermediate_{edge[0]}_{edge[1]}_{intermediate_bus_counter}",
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
                transition_key = (min(v1, v2), max(v1, v2))

                template_options = self.transition_matrix.template_dict.get(transition_key, list())

                if not template_options:
                    self.logger.add_warning(
                        msg=f"No template branches for transition {transition_key}. Skipping edge {edge}.",
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
                        msg=f"Could not instantiate branch for transition {transition_key}. Skipping edge {edge}.",
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

        for (v1, v2), template_options in self.transition_matrix.template_dict.items():
            if len(template_options) == 0:
                continue

            if v1 not in adjacency:
                adjacency[v1] = set()
            if v2 not in adjacency:
                adjacency[v2] = set()

            adjacency[v1].add(v2)
            adjacency[v2].add(v1)

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
            name=f"Intermediate_{edge[0]}_{edge[1]}_{intermediate_bus_counter}",
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
                    name=f"Intermediate_{edge[0]}_{edge[1]}_{intermediate_bus_counter}",
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
            transition_key = (min(v1, v2), max(v1, v2))

            template_options = self.transition_matrix.template_dict.get(transition_key, list())
            if len(template_options) == 0:
                raise RuntimeError(
                    f"No template branches available for transition {transition_key} "
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
                    f"Could not instantiate branch for transition {transition_key} "
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

        self.debugger = ProceduralGridDebugger(enabled=True)

        candidate_counter = 0
        for sg in self.candidates_substations:
            for bus in self.grid.get_substation_buses(sg):
                lon, lat = bus.try_to_find_coordinates()
                bus.longitude = lon
                bus.latitude = lat
                bus.name = f"Candidate_{candidate_counter}"
                bus.Vm_cost = bus.Vnom * bus.Vm_cost
                self.candidate_buses.append(bus)
                candidate_counter += 1

        target_counter = 0
        for sg in self.targets_substations:
            for bus in self.grid.get_substation_buses(sg):
                lon, lat = bus.try_to_find_coordinates()
                bus.longitude = lon
                bus.latitude = lat
                bus.name = f"Target_{target_counter}"
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

        self.debugger.plot_mst_graph(
            coords_final_network=coords_final_network,
            edges=edges,
            n_candidate=len(self.candidate_buses),
            n_target=len(self.target_buses),
            final_steiner_pts=final_steiner_pts,
        )

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

    def run_optimization(self):
        """
        Executes the Steiner Tree algorithm followed by an optimization pass.
        """
        # Add your Steiner Tree plus Optimization logic here

        return None
