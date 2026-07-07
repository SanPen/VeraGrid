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
from VeraGridEngine.basic_structures import Mat, Vec
from scipy.spatial.distance import cdist
from scipy.sparse.csgraph import minimum_spanning_tree
from scipy.special import gammaincinv

from VeraGridEngine.Topology.Procedural.procedural_grid_debugger import ProceduralGridDebugger

if TYPE_CHECKING:
    from VeraGridEngine.Devices.multi_circuit import MultiCircuit


def coord_calc(current_bus_lon: float, current_bus_lat: float, length: float, coord_out: Vec):
    """
    Calculate the coordinates of the next bus based on the current bus,
    the length to be covered, and the output coordinates.
    """
    line_angle = np.arctan2(coord_out[1] - current_bus_lat, coord_out[0] - current_bus_lon)
    delta_x = np.cos(line_angle) * length
    delta_y = np.sin(line_angle) * length
    new_coord = np.array([current_bus_lon + delta_x, current_bus_lat + delta_y])

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
    __slots__ = (
        "voltages_sorted",
        "voltages_dict",
        "transition_matrix",
        "template_dict",
    )

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


class Node:
    __slots__ = (
        "tpe",
        "id_number",
        "x",
        "y",
        "load",
        "voltage",
        "is_DC",
    )

    def __init__(self, tpe: str, id_number: int, x: float, y: float, load: float, voltage: int, is_DC: bool):
        """

        :param tpe:
        :param id_number:
        :param x:
        :param y:
        :param load:
        :param voltage:
        :param is_DC:
        """
        self.tpe = tpe  # M, N, or S
        self.id_number = id_number
        self.x = x
        self.y = y
        self.load = load
        self.voltage = voltage
        self.is_DC = is_DC

    # def add_node(self, candidate: int):
    #    self.candidates.append(candidate)


class Edge:
    __slots__ = (
        "start_node",
        "end_node",
    )

    def __init__(self, start_node: Node, end_node: Node):
        """

        :param start_node:
        :param end_node:
        """
        self.start_node = start_node
        self.end_node = end_node


class ProceduralGridGraph:
    __slots__ = (
        "target_buses",
        "candidate_buses",
        "max_iterations",
        "n_target",
        "n_candidate",
        "n_steiner",
        "coord_candidate",
        "coord_target",
        "min_lon",
        "min_lat",
        "max_lon",
        "max_lat",
        "base_coords",
        "base_voltages",
    )

    def __init__(self,
                 target_buses: List[dev.Bus],
                 candidate_buses: List[dev.Bus],
                 max_iterations: int = 1000, ):
        """

        :param target_buses:
        :param candidate_buses:
        :param max_iterations: Maximum number of iterations
        """
        self.target_buses: List[dev.Bus] = target_buses
        self.candidate_buses: List[dev.Bus] = candidate_buses
        self.max_iterations: int = max_iterations

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
        self.max_lon = 0
        self.max_lat = 0

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

        # print("Running VSA...\n")
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

            print(f"Pruning... Removed {len(current_steiner) - len(useful_indices)} nodes.\n")
            current_steiner = current_steiner[useful_indices, :]

        return current_steiner


class Topology:
    """
    Represents the physical layout using domain objects.
    Contains a Graph instance via composition.
    """
    __slots__ = (
        "edges",
        "all_buses",
        "grid",
        "transition_matrix",
        "discretization",
        "intermediate_buses",
    )

    def __init__(self,
                 edges: list[tuple[int, int]],
                 all_buses: List[dev.Bus],
                 grid: MultiCircuit,
                 transition_matrix: TransitionMatrix,
                 discretization: float = 25.0):

        self.edges = edges
        self.all_buses = all_buses
        self.grid = grid
        self.transition_matrix = transition_matrix
        self.discretization = discretization  # km between buses

        self.intermediate_buses: List[dev.Bus] = list()  # buses generated in the markov process

    def generate_markov(self):
        """
        Generates combinations that are valid by construction.
        """
        expansion_grid = dev.MultiCircuit()

        for edge in self.edges:

            lengths = []
            bus_name_log = []  # np.array(len(self.nodes), dtype=str)

            input_bus = self.all_buses[edge[0]]
            output_bus = self.all_buses[edge[1]]

            coord_input = np.array([input_bus.longitude, input_bus.latitude])
            coord_output = np.array([output_bus.longitude, output_bus.latitude])
            distance = np.linalg.norm(coord_input - coord_output)

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

            if next_bus.name not in bus_name_log:
                self.grid.add_bus(obj=next_bus)
                # Add the bus in bus_name_log
                bus_name_log.append(next_bus.name)

            voltage_options = self.transition_matrix.voltages_sorted

            iteration_counter = 0
            max_iterations = 10000

            while accumulated_length < distance:

                iteration_counter += 1
                if iteration_counter > max_iterations:
                    raise RuntimeError(
                        f"generate_markov() got stuck for edge {edge}, "
                        f"accumulated_length={accumulated_length}, distance={distance}, "
                        f"conn_counter={conn_counter}"
                    )

                # Update next bus to current bus
                current_bus = next_bus

                # Check if we are at the last connection
                is_last_conn = (conn_counter == n_slots - 1)

                # Add next bus to Multicircuit
                if is_last_conn:
                    next_bus = output_bus

                    # If statement to discard transitions that are not allowed by the transition matrix
                    if next_bus.Vnom not in self.transition_matrix.voltages_sorted:
                        print(
                            f"The voltage level from the end substation "
                            f"{next_bus.Vnom}kV does not appear in the existing grid.\n"
                            f"Modifying the end substation level to {current_bus.Vnom}kV.")

                        next_bus.Vnom = current_bus.Vnom
                        next_bus.name = f"Modified_{next_bus.name}"

                        if next_bus.name not in bus_name_log:
                            self.grid.add_bus(obj=next_bus)
                            # Add the bus in bus_name_log
                            bus_name_log.append(next_bus.name)
                    elif self.transition_matrix.at(current_bus.Vnom, next_bus.Vnom) == 0:
                        print(f"Added an intermediate bus to allow transition from "
                              f"{current_bus.Vnom}kV to {next_bus.Vnom}kV.")
                        # TODO: Implement last_bus_fix() function
                        # next_bus_volts = self.last_bus_fix(self.transition_matrix, current_bus_volt, next_bus_volt,
                        #                                    expansion_grid)
                        break
                    else:

                        if next_bus.name not in bus_name_log:
                            self.grid.add_bus(obj=next_bus)
                            # Add the bus in bus_name_log
                            bus_name_log.append(next_bus.name)

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
                        coord_out=coord_output,
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
                    print(f"Combo failed due to lack of template branches for transition {transition_key}.")
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

                print(
                    f"edge={edge}, type={type(new_branch).__name__}, "
                    f"accumulated_length={accumulated_length}, distance={distance}, "
                    f"conn_counter={conn_counter}"
                )

                if new_branch is None:
                    print(f"Could not instantiate branch for transition {transition_key}.")
                    break

                self.add_branch_to_grid(expansion_grid=expansion_grid, branch=new_branch)

                if isinstance(new_branch, dev.Line):
                    accumulated_length += lengths[conn_counter]
                    conn_counter += 1

            # TODO: Add the merge_lines function outside generate_markov and inside Topology
            # combination, length_elements_ = merge_lines(combination, length_elements_)

        return self.intermediate_buses

    def add_branch_to_grid(self, expansion_grid, branch) -> None:
        """
        Add a branch object to the correct container of the expansion grid.
        """
        if isinstance(branch, dev.Line):
            self.grid.add_line(obj=branch)
            return

        if isinstance(branch, dev.Transformer2W):
            self.grid.add_transformer2w(obj=branch)
            return

        # TODO: Extend later for VSC, HVDC, switches, etc.

    def last_bus_fix(self, transition_matrix, current_bus_volt, next_bus_volt):
        pass

    def add_loads(self):
        """
        Function to add loads and generators to the VeraGrid grid object
        :return:
        """
        pass


class ProceduralGridComputationEngine:
    """
    Core engine for procedural grid expansion calculations.
    """
    __slots__ = (
        "grid",
        "method",
        "targets_substations",
        "candidates_substations",
        "target_buses",
        "candidate_buses",
        "steiner_buses",
        "intermediate_buses",
        "debugger",
        "transition_matrix",
    )

    def __init__(self,
                 grid: MultiCircuit,
                 method: ProceduralGridMethods,
                 targets: List[dev.Substation],
                 candidates: List[dev.Substation]):
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

        self.target_buses: List[dev.Bus] = list()
        self.candidate_buses: List[dev.Bus] = list()
        self.steiner_buses: List[dev.Bus] = list()  # this is a result
        self.intermediate_buses: List[dev.Bus] = list()  # buses generated in the markov process

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

    def run_steiner_alone(self):
        """
        Executes the Steiner Tree algorithm without further optimization.
        """

        # 2A. Run VSA: Create an initial radial topology with a Steiner tree approach
        network = ProceduralGridGraph(target_buses=self.target_buses,
                                      candidate_buses=self.candidate_buses,
                                      max_iterations=15000)

        initial_steiner_points, history = network.run_vsa()
        print("Passed VSA.\n")
        # 2B. Prune redundant nodes
        final_steiner_pts = network.prune_redundant_nodes(initial_steiner_points)
        print("Passed pruning.\n")
        # 2C. Get edges of the final network
        coords_final_network = np.r_[network.base_coords, final_steiner_pts]
        dist_matrix = cdist(coords_final_network, coords_final_network, metric='euclidean')
        final_mst = minimum_spanning_tree(dist_matrix).toarray()
        print("Passed MST.\n")
        # generate edges
        rows, cols = np.where(final_mst > 0)
        edges = list(zip(rows, cols))

        self.debugger.validate_edge_indices(
            edges=edges,
            n_nodes=coords_final_network.shape[0],
        )

        self.debugger.print_edges(edges=edges)

        self.debugger.plot_mst_graph(
            coords_final_network=coords_final_network,
            edges=edges,
            n_candidate=len(self.candidate_buses),
            n_target=len(self.target_buses),
            final_steiner_pts=final_steiner_pts,
        )

        # TODO: Print element_transition_matrix for debugging

        print("Passed edges.\n")
        # 2E. Assign voltages to Steiner Points
        closest_voltage = np.zeros(final_steiner_pts.shape[0])
        for i in range(final_steiner_pts.shape[0]):
            distances = np.linalg.norm(network.base_coords - final_steiner_pts[i, :], axis=1)
            closest = np.argmin(distances)
            closest_voltage[i] = network.base_voltages[closest]

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

        print("Passed bus creation.\n")
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
                            discretization=25.0)

        before_names = self.debugger.snapshot_grid_element_names(self.grid)

        self.intermediate_buses = topology.generate_markov()

        added_names = self.debugger.get_added_element_names(
            grid=self.grid,
            previous_names=before_names,
        )

        print("Added elements:")
        for name in added_names:
            print(name)

        print("Finished run_steiner_alone().")

        # 4. Display in the diagram
        # TODO: Display diagram in the GUI

        return self.grid

    def run_optimization(self):
        """
        Executes the Steiner Tree algorithm followed by an optimization pass.
        """
        print("Running Steiner Tree plus Optimization")
        # Add your Steiner Tree plus Optimization logic here

        return None
