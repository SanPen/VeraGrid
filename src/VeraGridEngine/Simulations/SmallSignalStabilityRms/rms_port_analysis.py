# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import numpy as np

from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Simulations.Rms.problems.rms_problem_template import RmsProblemTemplate
from VeraGridEngine.Templates.Rms.buses.bus_rms_template import get_bus_rms_algebraic_vars
from VeraGridEngine.basic_structures import CxMat, IntVec, Mat, Vec
from VeraGridEngine.enumerations import VarPowerFlowReferenceType


class PortLinearization:
    """Full RMS linearization and indices defining one device-to-bus port."""

    __slots__ = [
        'jacobian',
        'derivative_matrix',
        'state_indices',
        'algebraic_indices',
        'power_indices',
        'voltage_indices',
        'algebraic_equation_rows',
        'voltage_qd_from_polar',
        'power_from_current',
        'power_from_voltage',
        'device',
        'bus',
    ]

    def __init__(self,
                 jacobian: Mat,
                 derivative_matrix: Mat,
                 state_indices: IntVec,
                 algebraic_indices: IntVec,
                 power_indices: IntVec,
                 voltage_indices: IntVec,
                 algebraic_equation_rows: IntVec,
                 voltage_qd_from_polar: Mat,
                 power_from_current: Mat,
                 power_from_voltage: Mat,
                 device: InjectionParent,
                 bus: Bus):
        self.jacobian = jacobian
        self.derivative_matrix = derivative_matrix
        self.state_indices = state_indices
        self.algebraic_indices = algebraic_indices
        self.power_indices = power_indices
        self.voltage_indices = voltage_indices
        self.algebraic_equation_rows = algebraic_equation_rows
        self.voltage_qd_from_polar = voltage_qd_from_polar
        self.power_from_current = power_from_current
        self.power_from_voltage = power_from_voltage
        self.device = device
        self.bus = bus


class DescriptorStateSpace:
    """Descriptor system ``E dz/dt = A z + B u; y = C z + D u``."""

    __slots__ = ['A', 'B', 'C', 'D', 'E']

    def __init__(self, A: Mat, B: Mat, C: Mat, D: Mat, E: Mat):
        self.A = A
        self.B = B
        self.C = C
        self.D = D
        self.E = E

    def frequency_response(self, frequencies_hz: Vec) -> CxMat:
        """Evaluate ``C(sE-A)^-1 B+D`` for ``s=2*pi*j*f``."""
        response = np.empty((len(frequencies_hz), self.C.shape[0], self.B.shape[1]), dtype=complex)
        for index, frequency_hz in enumerate(frequencies_hz):
            s = 2j * np.pi * frequency_hz
            response[index] = self.C @ np.linalg.solve(s * self.E - self.A, self.B) + self.D
        return response


class DevicePortResponse:
    """Frequency responses on both sides of one device-to-bus boundary."""

    __slots__ = [
        'frequencies_hz',
        'device_admittance',
        'grid_impedance',
        'device',
        'bus',
    ]

    def __init__(self,
                 frequencies_hz: Vec,
                 device_admittance: CxMat,
                 grid_impedance: CxMat,
                 device: InjectionParent,
                 bus: Bus):
        self.frequencies_hz = frequencies_hz
        self.device_admittance = device_admittance
        self.grid_impedance = grid_impedance
        self.device = device
        self.bus = bus


def _select_submatrix(matrix: Mat, rows: IntVec, columns: IntVec) -> Mat:
    """Select matrix rows followed by columns."""
    return matrix[rows, :][:, columns]


def _indices_except(count: int, excluded_indices: IntVec) -> IntVec:
    """Return indices from zero to count, excluding the supplied indices."""
    excluded = set(excluded_indices)
    return np.array([index for index in range(count) if index not in excluded], dtype=int)


def _port_geometry(voltage: complex, active_power: float, reactive_power: float) -> tuple[Mat, Mat, Mat]:
    """Build linear maps between polar voltage, qd voltage/current and P/Q."""
    voltage_magnitude = abs(voltage)
    voltage_angle = np.angle(voltage)
    voltage_q = voltage.real
    voltage_d = -voltage.imag
    power_from_current = np.array([
        [voltage_q, voltage_d],
        [-voltage_d, voltage_q],
    ])
    current_q, current_d = np.linalg.solve(
        power_from_current,
        np.array([active_power, reactive_power]),
    )
    voltage_qd_from_polar = np.array([
        [np.cos(voltage_angle), -voltage_magnitude * np.sin(voltage_angle)],
        [-np.sin(voltage_angle), -voltage_magnitude * np.cos(voltage_angle)],
    ])
    power_from_voltage = np.array([
        [current_q, current_d],
        [current_d, -current_q],
    ])
    return voltage_qd_from_polar, power_from_current, power_from_voltage


def validate_port_linearization(port: PortLinearization,
                                problem: RmsProblemTemplate,
                                operating_point: Vec,
                                state_derivatives: Vec,
                                residual_tolerance: float = 1e-7) -> None:
    """Validate the operating point and selected device boundary."""
    largest_residual = max(
        np.max(np.abs(problem.rhs_state(operating_point, state_derivatives)), initial=0.0),
        np.max(np.abs(problem.rhs_algebraic(operating_point, state_derivatives)), initial=0.0),
    )
    if not np.isfinite(largest_residual) or largest_residual > residual_tolerance:
        raise RuntimeError(f"RMS operating point is not an equilibrium: {largest_residual:g}")
    if len(port.state_indices) == 0:
        raise RuntimeError(f"No RMS states found for {port.device.name}")
    if not set(port.power_indices).issubset(port.algebraic_indices):
        raise ValueError(f"P/Q must be algebraic output variables of {port.device.name}")

    selected_coordinates = np.concatenate((
        port.state_indices,
        port.algebraic_indices,
        port.voltage_indices,
    ))
    if len(set(selected_coordinates)) != len(selected_coordinates):
        raise RuntimeError("Overlapping port coordinates")
    if len(port.algebraic_equation_rows) != len(port.algebraic_indices):
        raise ValueError(f"Algebraic equation/variable count differs for {port.device.name}")

    device_rows = np.concatenate((port.state_indices, port.algebraic_equation_rows))
    voltage_derivatives = _select_submatrix(
        port.derivative_matrix,
        device_rows,
        port.voltage_indices,
    )
    if np.any(np.abs(voltage_derivatives) > 1e-12):
        raise ValueError(
            "Device equations contain derivatives of port voltage; "
            "the descriptor needs an additional input-derivative matrix"
        )


def prepare_port(driver, device: InjectionParent) -> PortLinearization:
    """Identify an RMS injection device's electrical boundary at its bus."""
    problem: RmsProblemTemplate = driver.problem
    operating_point = problem.get_x0()
    state_derivatives = problem.get_dx0()
    state_count = problem.get_states_number()
    jacobian = problem.get_static_state_matrix(operating_point, state_derivatives).toarray()
    derivative_matrix = -problem.get_E_matrix(operating_point, state_derivatives)

    model = device.rms_model
    state_indices = np.array([problem.get_var_idx(variable) for variable in model.state_vars])
    algebraic_indices = np.array([problem.get_var_idx(variable) for variable in model.algebraic_vars])
    power_indices = np.array([
        problem.get_var_idx(model.external_mapping[reference])
        for reference in (VarPowerFlowReferenceType.P, VarPowerFlowReferenceType.Q)
    ])
    _, voltage_magnitude_variable, voltage_angle_variable = get_bus_rms_algebraic_vars(device.bus.rms_model)
    voltage_indices = np.array([
        problem.get_var_idx(voltage_magnitude_variable),
        problem.get_var_idx(voltage_angle_variable),
    ])

    voltage_magnitude, voltage_angle = operating_point[voltage_indices]
    voltage = voltage_magnitude * np.exp(1j * voltage_angle)
    active_power, reactive_power = operating_point[power_indices]
    voltage_qd_from_polar, power_from_current, power_from_voltage = _port_geometry(
        voltage,
        active_power,
        reactive_power,
    )

    equation_row_by_object_id = {
        id(equation): state_count + index
        for index, equation in enumerate(problem.algebraic_eqs)
    }
    algebraic_equation_rows = np.array([
        equation_row_by_object_id[id(equation)]
        for equation in model.algebraic_eqs
    ])

    port = PortLinearization(
        jacobian=jacobian,
        derivative_matrix=derivative_matrix,
        state_indices=state_indices,
        algebraic_indices=algebraic_indices,
        power_indices=power_indices,
        voltage_indices=voltage_indices,
        algebraic_equation_rows=algebraic_equation_rows,
        voltage_qd_from_polar=voltage_qd_from_polar,
        power_from_current=power_from_current,
        power_from_voltage=power_from_voltage,
        device=device,
        bus=device.bus,
    )
    validate_port_linearization(port, problem, operating_point, state_derivatives)
    return port


def build_device_descriptor(port: PortLinearization) -> DescriptorStateSpace:
    """Build the selected device with qd bus voltage input and injected-current output."""
    device_rows = np.concatenate((port.state_indices, port.algebraic_equation_rows))
    device_columns = np.concatenate((port.state_indices, port.algebraic_indices))
    device_column_positions = {
        global_index: position
        for position, global_index in enumerate(device_columns)
    }
    power_selector = np.zeros((2, len(device_columns)))
    for output_row, global_index in enumerate(port.power_indices):
        power_selector[output_row, device_column_positions[global_index]] = 1.0

    voltage_jacobian = _select_submatrix(port.jacobian, device_rows, port.voltage_indices)
    return DescriptorStateSpace(
        A=_select_submatrix(port.jacobian, device_rows, device_columns),
        B=voltage_jacobian @ np.linalg.inv(port.voltage_qd_from_polar),
        C=np.linalg.solve(port.power_from_current, power_selector),
        D=-np.linalg.solve(port.power_from_current, port.power_from_voltage),
        E=_select_submatrix(port.derivative_matrix, device_rows, device_columns),
    )


def compute_device_admittance(port: PortLinearization, frequencies_hz: Vec) -> CxMat:
    """Return injected qd current per imposed qd terminal-voltage perturbation."""
    return build_device_descriptor(port).frequency_response(frequencies_hz)


def build_grid_descriptor(port: PortLinearization) -> DescriptorStateSpace:
    """Build the remaining grid with qd current input and bus-voltage output."""
    full_size = port.jacobian.shape[0]
    device_rows = np.concatenate((port.state_indices, port.algebraic_equation_rows))
    power_indices = set(port.power_indices)
    internal_algebraic_indices = np.array([
        index for index in port.algebraic_indices if index not in power_indices
    ], dtype=int)
    device_internal_columns = np.concatenate((port.state_indices, internal_algebraic_indices))
    grid_columns = _indices_except(full_size, device_internal_columns)
    grid_rows = _indices_except(full_size, device_rows)
    grid_jacobian = _select_submatrix(port.jacobian, grid_rows, grid_columns)
    grid_derivative_matrix = _select_submatrix(
        port.derivative_matrix,
        grid_rows,
        grid_columns,
    )
    grid_column_positions = {
        global_index: position
        for position, global_index in enumerate(grid_columns)
    }
    power_columns = [grid_column_positions[index] for index in port.power_indices]
    voltage_columns = [grid_column_positions[index] for index in port.voltage_indices]

    port_equations = np.zeros((2, len(grid_columns)))
    port_equations[:, power_columns] = np.eye(2)
    port_equations[:, voltage_columns] = (
        -port.power_from_voltage @ port.voltage_qd_from_polar
    )
    A = np.vstack((grid_jacobian, -port_equations))
    E = np.vstack((grid_derivative_matrix, np.zeros_like(port_equations)))
    B = np.zeros((len(grid_columns), 2))
    B[-2:, :] = port.power_from_current
    C = np.zeros((2, len(grid_columns)))
    C[:, voltage_columns] = port.voltage_qd_from_polar
    D = np.zeros((2, 2))
    return DescriptorStateSpace(A=A, B=B, C=C, D=D, E=E)


def compute_grid_impedance_at_device_port(port: PortLinearization,
                                           frequencies_hz: Vec) -> CxMat:
    """Return qd bus voltage per injected qd current with the device removed."""
    return build_grid_descriptor(port).frequency_response(frequencies_hz)
