# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from abc import ABC
from typing import Dict, List, Tuple
import numpy as np
import scipy.sparse as sp
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Simulations.Rms.initialization_rms import (
    project_initial_algebraic_state, solve_rms_newton_correction,
)
from VeraGridEngine.Simulations.Rms.jacobian_assembler import JacobianAssembler
from VeraGridEngine.basic_structures import Vec, Logger
from VeraGridEngine.enumerations import SparseSolver
from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import SparseLinearSolverBackendProvider
from VeraGridEngine.Utils.Sparse.sparse_solve import resolve_sparse_lu_provider
from VeraGridEngine.Simulations.driver_template import DummySignal


def rectangular_current_from_power(
        power: complex,
        voltage: complex,
) -> Tuple[float, float]:
    """
    Convert one complex-power operating point to rectangular current.

    The RMS injection convention is ``S = V * conj(I)``. This helper supplies
    the exact current seed associated with an already-converged power-flow
    voltage and avoids an artificial first-step residual in models that expose
    both power and current variables.

    :param power: Complex injected power in per unit.
    :param voltage: Complex terminal voltage in per unit.
    :return: Real and imaginary current components in per unit.
    """
    voltage_squared: float = float(
        voltage.real * voltage.real + voltage.imag * voltage.imag
    )
    if voltage_squared > 1.0e-18:
        current_real: float = float(
            (power.real * voltage.real + power.imag * voltage.imag)
            / voltage_squared
        )
        current_imaginary: float = float(
            (power.real * voltage.imag - power.imag * voltage.real)
            / voltage_squared
        )
    else:
        current_real = 0.0
        current_imaginary = 0.0
    return current_real, current_imaginary


class CompiledScalarRmsProblem:
    """Marker for the global compiled RMS residual and Jacobian evaluator."""


class CompiledFullVectorizedRmsProblem:
    """Marker for the category compiled RMS residual and Jacobian evaluator."""


class RmsProblemTemplate(ABC):
    """
    Abstract base class for RMS dynamic simulation problems.

    Concrete problems also provide the attributes read directly by the RMS integrators:
    _variable_parameters_values (runtime parameter vector), _constant_params (constant
    parameter vector or None), and _fmu_me_adapters / _fmu_cs_adapters (lists of active
    FMI adapters; non-empty lists keep the backward-Euler integrator on fresh Jacobians).
    """
    __slots__ = (
        "_is_initialized",
        "_sparse_solver_backend_provider",
        "_requested_sparse_solver",
        "progress_signal",
        "progress_text",
        "grid",
        "power_flow_results",
        "_jacobian_assembler",
        "_back_euler_gather_x",
        "_back_euler_gather_dx",
    )

    def __init__(self,
                 progress_signal: DummySignal | None = None,
                 progress_text: DummySignal | None = None,
                 sparse_solver: SparseSolver | None = None,
                 logger: Logger | None = None) -> None:
        """Bind selection before a concrete constructor can initialize devices.

        :param progress_signal: Existing numeric progress sink.
        :param progress_text: Existing text progress sink.
        :param sparse_solver: Selected LU enum, or None for an unconfigured generic problem.
        :param logger: Existing owner of availability/fallback diagnostics.
        :return: None.
        """
        self._sparse_solver_backend_provider: SparseLinearSolverBackendProvider | None = None
        self._requested_sparse_solver: SparseSolver | None = sparse_solver
        if sparse_solver is not None:
            self._sparse_solver_backend_provider = resolve_sparse_lu_provider(sparse_solver, logger)
        else:
            pass
        self._is_initialized = False
        self.progress_signal =  DummySignal() if progress_signal is None else progress_signal
        self.progress_text = DummySignal(str) if progress_text is None else progress_text
        self._jacobian_assembler = None
        self._back_euler_gather_x = None
        self._back_euler_gather_dx = None

    def get_forced_event_times(self) -> list[float]:
        """Scheduled hard boundaries exposed to adaptive integration."""
        return []

    def evaluate_rhs(self, x: Vec, dx: Vec):
        """Return differential and algebraic equation values at ``(x, dx)``."""
        algebraic = self.rhs_algebraic(x, dx)
        state = self.rhs_state(x, dx) if self.get_states_number() else None
        return state, algebraic

    def evaluate_equations(self, x: Vec, dx: Vec) -> Vec:
        """Return raw differential and algebraic equations in solver row order."""
        state, algebraic = self.evaluate_rhs(x, dx)
        if state is None:
            return algebraic
        return np.r_[state, algebraic]

    def evaluate_jacobian_blocks(self, x: Vec, dx: Vec, h: float):
        """Return the equation Jacobian blocks at ``(x, dx)``."""
        if not self.get_states_number():
            return None, None, None, self.get_j22(x, dx, h)
        return (self.get_j11(x, dx, h), self.get_j12(x, dx, h),
                self.get_j21(x, dx, h), self.get_j22(x, dx, h))

    def evaluate_equation_jacobian(self, x: Vec, dx: Vec) -> sp.csc_matrix:
        """Return d(f,g)/d(x,y), holding derivative inputs fixed."""
        j11, j12, _, j21, j22, _ = self.evaluate_jacobian_partials(x, dx)
        if not self.get_states_number():
            return j22.tocsc()
        return sp.bmat(((j11, j12), (j21, j22)), format="csc")

    def has_fixed_equation_jacobian_pattern(self) -> bool:
        """Whether each returned CSC object's structure is immutable.

        Implementations opting in must return a new matrix object when the
        pattern changes. Numerical data may be updated in place.
        """
        return False

    def evaluate_jacobian_partials(self, x: Vec, dx: Vec,
                                   derivative_base_indices: np.ndarray | None = None):
        """Return J11/J12/J13/J21/J22/J23 for first-order derivative inputs.

        Problems without derivative inputs need only one four-block evaluation.
        Vectorized problems with derivative inputs override this method.
        """
        if self.get_diff_var_number():
            raise NotImplementedError("Derivative-variable Jacobian partials are not available")
        j11, j12, j21, j22 = self.evaluate_jacobian_blocks(x, dx, 1.0)
        n_states = self.get_states_number()
        n_algebraic = j22.shape[0]
        return (j11, j12, sp.csc_matrix((n_states, 0)),
                j21, j22, sp.csc_matrix((n_algebraic, 0)))

    def supports_derivative_jacobian_partials(self) -> bool:
        """Whether this problem can separate first-order derivative inputs."""
        return False

    def get_jacobian(self, x: Vec, dx: Vec, h: float) -> sp.csc_matrix:
        """Return the implicit Newton matrix for the current candidate."""
        j11, j12, j21, j22 = self.evaluate_jacobian_blocks(x, dx, h)
        n_states = self.get_states_number()
        if n_states == 0:
            return j22
        if self._jacobian_assembler is None:
            self._jacobian_assembler = JacobianAssembler()
        return self._jacobian_assembler.assemble_jacobian_implicit(n_states, h, j11, j12, j21, j22)

    def evaluate_backward_euler_residual(self, x: Vec, dx: Vec, xn: Vec, h: float) -> Vec:
        """Return the implicit residual for a Backward Euler candidate."""
        f_state, f_algeb = self.evaluate_rhs(x, dx)
        n_states = self.get_states_number()
        if n_states == 0:
            return f_algeb
        return np.r_[x[:n_states] - xn[:n_states] - h * f_state, f_algeb]

    def update_with_current_parameters(self, t: float, x: Vec) -> None:
        """Update the model using the problem's current parameter values."""
        self.update(t, x, self._variable_parameters_values)

    def get_sparse_solver_backend_provider(self, sparse_solver: SparseSolver | None = None) -> SparseLinearSolverBackendProvider | None:
        """Read the problem's resolved selection without sharing numeric factors.

        :param sparse_solver: Optional requested enum; a changed request requires resolution.
        :return: Matching resolved provider, including its effective fallback, or None.
        """
        if sparse_solver is None or sparse_solver == self._requested_sparse_solver:
            return self._sparse_solver_backend_provider
        else:
            return None

    def set_sparse_solver_backend_provider(self, provider: SparseLinearSolverBackendProvider, sparse_solver: SparseSolver | None = None) -> None:
        """Bind an explicitly resolved provider before starting a numerical phase.

        :param provider: Available provider selected by the existing options policy.
        :param sparse_solver: Original requested enum; defaults to the effective provider.
        :return: None; provider state contains no phase factorization.
        """
        self._sparse_solver_backend_provider = provider
        self._requested_sparse_solver = provider.get_solver_type() if sparse_solver is None else sparse_solver

    def set_initialize_flag(self):
        self._is_initialized = True

    def is_initialized(self) -> bool:
        return self._is_initialized

    def resolve_manufacturer_native_boundary(self, t: float, x: Vec) -> None:
        """Complete an accepted RMS step when no manufacturer controller is present.

        :param t: Accepted solver time.
        :param x: Accepted state vector.
        :return: None.
        """
        pass

    def get_vars_info(self) -> Dict[ALL_DEV_TYPES, List[Var]]:
        raise NotImplementedError("get_device_vars_dict")

    def get_all_vars_number(self) -> int:
        return 0

    def get_diff_var_number(self) -> int:
        return 0

    def get_diff_var_orders(self) -> np.ndarray:
        """Return the time derivative order of each derivative input."""
        orders = []
        for derivative in self.get_diff_vars():
            order = 0
            while derivative.base_var is not None:
                derivative = derivative.base_var
                order += 1
            orders.append(order)
        return np.asarray(orders, dtype=np.intp)

    def get_diff_var_base_indices(self) -> np.ndarray:
        """Return the trial-variable column underlying each derivative input."""
        indices = []
        for derivative in self.get_diff_vars():
            while derivative.base_var is not None:
                derivative = derivative.base_var
            indices.append(self.uid2idx_vars[derivative.uid])
        return np.asarray(indices, dtype=np.intp)

    def get_algebraic_var_number(self) -> int:
        return 0

    def get_algebraic_vars(self) -> List:
        return list()

    def get_states_number(self) -> int:
        return 0

    def get_variable_parameter_number(self) -> int:
        return 0

    def algebraic_vars(self) -> List:
        return list()

    def state_vars(self):
        return list()

    # def get_constant_parameters(self) -> Vec:
    #     raise NotImplementedError("get_constant_parameters")

    def get_x0(self) -> Vec:
        raise NotImplementedError("get_x0")

    # def compute_event_params(self, parameters: Vec, time_value: float) -> Vec:
    #     raise NotImplementedError("compute_event_params")

    def update_variable_params(self, t: float, x_snapshot: Vec | None = None):
        raise NotImplementedError("update_variable_params")

    def get_dx(self, x: Vec, xn: Vec, dx: Vec, h: float) -> Vec:
        raise NotImplementedError("derivative")

    def rhs_state(self, x: Vec, dx: Vec) -> Vec:
        raise NotImplementedError("rhs_state")

    def rhs_algebraic(self, values: Vec, diff_values: Vec) -> Vec:
        raise NotImplementedError("rhs_algebraic")

    def get_j11(self, x: Vec, dx: Vec, h: float):
        raise NotImplementedError("get_j11")

    def get_j12(self, x: Vec, dx: Vec, h: float):
        raise NotImplementedError("get_j12")

    def get_j21(self, x: Vec, dx: Vec, h: float):
        raise NotImplementedError("get_j21")

    def get_j22(self, x: Vec, dx: Vec, h: float):
        raise NotImplementedError("get_j22")

    def get_E_matrix(self, x:Vec, dx:Vec):
        raise NotImplementedError("get_E_matrix")

    def get_static_state_matrix(self, x: Vec, dx: Vec):
        raise NotImplementedError("get_static_state_matrix")

    def get_small_signal_reference_indices(self) -> tuple[int, int] | None:
        """
        Return the augmented-Jacobian row and column used to fix the angle gauge.

        Problems without an explicit electrical angle reference do not require
        a small-signal gauge constraint and return ``None``.

        :return: Reference row and column, or ``None`` when not applicable.
        """
        return None
    
    def get_dt_value(self):
        return NotImplementedError("get_dt_value")

    def get_generator_injection_data(self, i: int, elm: ALL_DEV_TYPES) -> complex:
        if elm.active:
            # The power-flow worker already allocates the solved slack-bus
            # active and reactive power among its individual generators (and
            # batteries) in gen_p/gen_q.  Using the aggregate Sbus here would
            # assign the complete net bus injection to every generator on a
            # multi-generator slack bus and would also include any load or
            # shunt connected to that bus.
            return complex(
                self.power_flow_results.gen_p[i],
                self.power_flow_results.gen_q[i],
            ) / self.grid.Sbase
        else:
            return complex(0.0, 0.0)

    def get_battery_injection_data(self, i: int, elm: ALL_DEV_TYPES) -> complex:
        if elm.active:
            return complex(self.power_flow_results.battery_p[i], self.power_flow_results.battery_q[i]) / self.grid.Sbase
        else:
            return complex(0.0, 0.0)

    def get_load_injection_data(self, elm: ALL_DEV_TYPES, bus_dict: Dict[Bus, int]) -> complex:
        if elm.active:
            bus_index = bus_dict[elm.bus]
            Vm = abs(self.power_flow_results.voltage[bus_index])
            scale = 1000.0 if elm.use_kw else 1.0
            S0 = -elm.get_S_at(None) / scale / self.grid.Sbase
            I0 = -elm.get_I_at(None) / scale / self.grid.Sbase
            Y0 = -elm.get_Y_at(None) / scale / self.grid.Sbase
            return S0 + np.conj(I0 + Y0 * Vm) * Vm
        else:
            return complex(0.0, 0.0)

    def get_external_grid_injection_data(self, elm: ALL_DEV_TYPES) -> complex:
        if elm.active:
            scale = 1000.0 if elm.use_kw else 1.0
            return -elm.get_S_at(None) / scale / self.grid.Sbase
        else:
            return complex(0.0, 0.0)

    def get_static_generator_injection_data(self, elm: ALL_DEV_TYPES) -> complex:
        if elm.active:
            scale = 1000.0 if elm.use_kw else 1.0
            return elm.get_S_at(None) / scale / self.grid.Sbase
        else:
            return complex(0.0, 0.0)

    def get_shunt_injection_data(self, elm: ALL_DEV_TYPES, bus_dict: Dict[Bus, int]) -> complex:
        if elm.active:
            bus_index = bus_dict[elm.bus]
            Vbus = self.power_flow_results.voltage[bus_index]
            scale = 1000.0 if elm.use_kw else 1.0
            # The RMS problem stores power injected into the bus. A shunt
            # admittance consumes ``V * conj(Y * V)``, so its network injection
            # is the negative of that consumed complex power.
            return -Vbus * np.conj((elm.get_Y_at(None) / scale / self.grid.Sbase) * Vbus)
        else:
            return complex(0.0, 0.0)

    def get_controllable_shunt_injection_data(self, elm: ALL_DEV_TYPES, bus_dict: Dict[Bus, int]) -> complex:
        return self.get_shunt_injection_data(elm=elm, bus_dict=bus_dict)

    def get_current_injection_data(self, elm: ALL_DEV_TYPES, bus_dict: Dict[Bus, int]) -> complex:
        if elm.active:
            bus_index = bus_dict[elm.bus]
            Vbus = self.power_flow_results.voltage[bus_index]
            scale = 1000.0 if elm.use_kw else 1.0
            return -Vbus * np.conj(elm.get_I_at(None) / scale / self.grid.Sbase)
        else:
            return complex(0.0, 0.0)

    def get_injection_init_data(self, bus_dict: Dict[Bus, int]) -> Dict[str, complex]:
        injection_init_data: Dict[str, complex] = dict()

        for i, elm in enumerate(self.grid.get_generators()):
            Sdev = self.get_generator_injection_data(i=i, elm=elm)
            injection_init_data[elm.idtag] = Sdev

        for i, elm in enumerate(self.grid.get_batteries()):
            Sdev = self.get_battery_injection_data(i=i, elm=elm)
            injection_init_data[elm.idtag] = Sdev

        for elm in self.grid.get_loads():
            Sdev = self.get_load_injection_data(elm=elm, bus_dict=bus_dict)
            injection_init_data[elm.idtag] = Sdev

        for elm in self.grid.get_external_grids():
            Sdev = self.get_external_grid_injection_data(elm=elm)
            injection_init_data[elm.idtag] = Sdev

        for elm in self.grid.get_static_generators():
            Sdev = self.get_static_generator_injection_data(elm=elm)
            injection_init_data[elm.idtag] = Sdev

        for elm in self.grid.get_shunts():
            Sdev = self.get_shunt_injection_data(elm=elm, bus_dict=bus_dict)
            injection_init_data[elm.idtag] = Sdev

        for elm in self.grid.get_controllable_shunts():
            Sdev = self.get_controllable_shunt_injection_data(elm=elm, bus_dict=bus_dict)
            injection_init_data[elm.idtag] = Sdev

        for elm in self.grid.get_current_injections():
            Sdev = self.get_current_injection_data(elm=elm, bus_dict=bus_dict)
            injection_init_data[elm.idtag] = Sdev

        return injection_init_data

    def report_progress(self, val: float) -> None:
        """
        Emit one absolute RMS progress update.

        :param val: Progress value in percent.
        :type val: float
        :return: None
        :rtype: None
        """
        if self.progress_signal is not None:
            self.progress_signal.emit(val)
        else:
            pass

    def report_progress2(self, current: int, total: int) -> None:
        """
        Emit one RMS progress update from a zero-based iteration index.

        :param current: Zero-based iteration index.
        :type current: int
        :param total: Total number of iterations.
        :type total: int
        :return: None
        :rtype: None
        """
        if self.progress_signal is not None:
            val: float = ((current + 1) / total) * 100
            self.progress_signal.emit(val)
        else:
            pass

    def report_text(self, text: str) -> None:
        """
        Emit a textual update describing the current RMS simulation stage.

        :param text: Human-readable progress message.
        :type text: str
        :return: None
        :rtype: None
        """
        if self.progress_text is not None:
            self.progress_text.emit(text)
        else:
            pass
