# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Sequence

import numpy as np
import scipy.linalg as la

from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_options import JMartiFitOptions
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_loewner_seed import JMartiModeLoewnerSeed


class JMartiRationalModeFit:
    """
    Scalar rational fit of one JMARTI modal target.

    The first JMARTI implementation fits each modal channel independently. The
    object stores the resulting pole-residue form together with explicit error
    metrics so later passivity and runtime stages can inspect the fit quality.
    """

    __slots__ = (
        '_mode_index',
        '_target_name',
        '_poles_s',
        '_residues',
        '_constant_term',
        '_proportional_term',
        '_fit_error_rms',
        '_max_relative_error',
        '_iterations_completed',
        '_converged',
        '_stable',
    )

    def __init__(self,
                 mode_index: int,
                 target_name: str,
                 poles_s: np.ndarray,
                 residues: np.ndarray,
                 constant_term: complex,
                 proportional_term: complex,
                 fit_error_rms: float,
                 max_relative_error: float,
                 iterations_completed: int,
                 converged: bool,
                 stable: bool) -> None:
        """
        Store one scalar rational fit.

        :param mode_index: Modal channel index.
        :param target_name: Modal target name.
        :param poles_s: Fitted continuous-time poles.
        :param residues: Fitted residues paired with ``poles_s``.
        :param constant_term: Constant term of the rational fit.
        :param proportional_term: Proportional ``s`` term of the rational fit.
        :param fit_error_rms: Global relative RMS fit error.
        :param max_relative_error: Maximum pointwise relative fit error.
        :param iterations_completed: Number of pole-relocation iterations performed.
        :param converged: Whether the pole-relocation loop met its stopping criterion.
        :param stable: Whether every fitted pole lies in the left half-plane.
        :return: None.
        """
        self._mode_index: int = int(mode_index)
        self._target_name: str = str(target_name)
        self._poles_s: np.ndarray = np.asarray(poles_s, dtype=np.complex128)
        self._residues: np.ndarray = np.asarray(residues, dtype=np.complex128)
        self._constant_term: complex = complex(constant_term)
        self._proportional_term: complex = complex(proportional_term)
        self._fit_error_rms: float = float(fit_error_rms)
        self._max_relative_error: float = float(max_relative_error)
        self._iterations_completed: int = int(iterations_completed)
        self._converged: bool = bool(converged)
        self._stable: bool = bool(stable)

    def get_mode_index(self) -> int:
        """
        Return the modal channel index.

        :return: Modal channel index.
        """
        return self._mode_index

    def get_target_name(self) -> str:
        """
        Return the modal target name.

        :return: Modal target name.
        """
        return self._target_name

    def get_poles_s(self) -> np.ndarray:
        """
        Return the fitted continuous-time poles.

        :return: Complex pole vector.
        """
        return self._poles_s

    def get_residues(self) -> np.ndarray:
        """
        Return the fitted residues.

        :return: Complex residue vector.
        """
        return self._residues

    def get_constant_term(self) -> complex:
        """
        Return the fitted constant term.

        :return: Complex constant term.
        """
        return self._constant_term

    def get_proportional_term(self) -> complex:
        """
        Return the fitted proportional term.

        :return: Complex proportional term.
        """
        return self._proportional_term

    def get_fit_error_rms(self) -> float:
        """
        Return the relative RMS fit error.

        :return: Relative RMS fit error.
        """
        return self._fit_error_rms

    def get_max_relative_error(self) -> float:
        """
        Return the maximum pointwise relative fit error.

        :return: Maximum relative fit error.
        """
        return self._max_relative_error

    def get_iterations_completed(self) -> int:
        """
        Return the number of pole-relocation iterations performed.

        :return: Completed iteration count.
        """
        return self._iterations_completed

    def get_converged(self) -> bool:
        """
        Return whether the relocation loop converged.

        :return: Boolean convergence flag.
        """
        return self._converged

    def get_stable(self) -> bool:
        """
        Return whether every fitted pole is stable.

        :return: Boolean stability flag.
        """
        return self._stable


def build_jmarti_complex_frequency_points(frequency_hz: Sequence[float]) -> np.ndarray:
    """
    Map one real frequency grid to the continuous-time imaginary axis.

    :param frequency_hz: Frequency grid in Hz.
    :return: Complex s-plane samples ``j*2*pi*f``.
    """
    return 1j * 2.0 * np.pi * np.asarray(frequency_hz, dtype=np.float64)


def _build_reciprocal_pole_basis(s_values: np.ndarray, poles_s: np.ndarray) -> np.ndarray:
    """
    Build the reciprocal pole basis ``1 / (s - p)``.

    :param s_values: Complex frequency samples.
    :param poles_s: Pole vector.
    :return: Basis matrix with shape ``(ns, npoles)``.
    """
    return 1.0 / (s_values[:, None] - poles_s[None, :])


def _sort_poles_by_real_imag(poles_s: np.ndarray) -> np.ndarray:
    """
    Sort poles deterministically by real part and then by imaginary part.

    :param poles_s: Complex pole vector.
    :return: Sorted pole vector.
    """
    sort_index: np.ndarray = np.lexsort((np.imag(poles_s), np.real(poles_s)))
    return np.asarray(poles_s[sort_index], dtype=np.complex128)


def _enforce_stable_poles(poles_s: np.ndarray, real_part_floor: float) -> np.ndarray:
    """
    Reflect unstable poles into the left half-plane.

    :param poles_s: Candidate pole vector.
    :param real_part_floor: Minimum absolute negative real part after reflection.
    :return: Stable pole vector.
    """
    stabilized_poles_s: np.ndarray = np.asarray(poles_s, dtype=np.complex128).copy()
    pole_index: int = 0
    real_part_value: float
    imag_part_value: float

    while pole_index < stabilized_poles_s.size:
        real_part_value = float(np.real(stabilized_poles_s[pole_index]))
        imag_part_value = float(np.imag(stabilized_poles_s[pole_index]))

        if real_part_value < -real_part_floor:
            pass
        else:
            stabilized_poles_s[pole_index] = complex(-max(abs(real_part_value), real_part_floor), imag_part_value)

        pole_index += 1

    return stabilized_poles_s


def _build_vector_fit_relocation_system(s_values: np.ndarray,
                                        response_values: np.ndarray,
                                        poles_s: np.ndarray,
                                        include_constant_term: bool,
                                        include_proportional_term: bool) -> tuple[np.ndarray, np.ndarray]:
    """
    Build the relaxed scalar Vector Fitting relocation least-squares system.

    :param s_values: Complex frequency samples.
    :param response_values: Complex scalar response samples.
    :param poles_s: Current pole vector.
    :param include_constant_term: Whether to include one constant term.
    :param include_proportional_term: Whether to include one proportional ``s`` term.
    :return: Tuple ``(A, b)`` for the complex least-squares problem.
    """
    basis_matrix: np.ndarray = _build_reciprocal_pole_basis(s_values, poles_s)
    column_blocks: list[np.ndarray] = list([basis_matrix])
    row_count: int = int(s_values.size)

    if include_constant_term:
        column_blocks.append(np.ones((row_count, 1), dtype=np.complex128))
    else:
        pass

    if include_proportional_term:
        column_blocks.append(s_values.reshape(-1, 1))
    else:
        pass

    # The denominator perturbation is solved in the same least-squares system by
    # multiplying the scalar samples against the reciprocal pole basis.
    column_blocks.append(-response_values.reshape(-1, 1) * basis_matrix)
    system_matrix: np.ndarray = np.hstack(column_blocks)
    rhs_vector: np.ndarray = response_values.astype(np.complex128)
    return system_matrix, rhs_vector


def _extract_relocation_coefficients(solution_vector: np.ndarray,
                                     pole_count: int,
                                     include_constant_term: bool,
                                     include_proportional_term: bool) -> tuple[np.ndarray, complex, complex, np.ndarray]:
    """
    Unpack one relocation least-squares solution vector.

    :param solution_vector: Complex least-squares solution vector.
    :param pole_count: Number of poles.
    :param include_constant_term: Whether one constant term is present.
    :param include_proportional_term: Whether one proportional term is present.
    :return: Tuple ``(residues, constant_term, proportional_term, sigma_residues)``.
    """
    offset: int = pole_count
    residues: np.ndarray = np.asarray(solution_vector[:pole_count], dtype=np.complex128)
    constant_term: complex = 0.0 + 0.0j
    proportional_term: complex = 0.0 + 0.0j

    if include_constant_term:
        constant_term = complex(solution_vector[offset])
        offset += 1
    else:
        pass

    if include_proportional_term:
        proportional_term = complex(solution_vector[offset])
        offset += 1
    else:
        pass

    sigma_residues: np.ndarray = np.asarray(solution_vector[offset:offset + pole_count], dtype=np.complex128)
    return residues, constant_term, proportional_term, sigma_residues


def _relocate_poles_from_sigma(current_poles_s: np.ndarray,
                               sigma_residues: np.ndarray) -> np.ndarray:
    """
    Compute the zeros of the relaxed sigma function.

    :param current_poles_s: Current pole vector.
    :param sigma_residues: Sigma residues from the relocation solve.
    :return: Relocated poles.
    """
    state_matrix: np.ndarray = np.diag(current_poles_s) - np.outer(np.ones(current_poles_s.size, dtype=np.complex128), sigma_residues)
    return np.asarray(la.eigvals(state_matrix), dtype=np.complex128)


def _compute_relative_pole_shift(old_poles_s: np.ndarray, new_poles_s: np.ndarray) -> float:
    """
    Compute one relative pole-shift metric.

    :param old_poles_s: Previous pole vector.
    :param new_poles_s: Updated pole vector.
    :return: Maximum relative pole shift.
    """
    denominator: np.ndarray = 1.0 + np.abs(old_poles_s)
    return float(np.max(np.abs(new_poles_s - old_poles_s) / denominator))


def _build_final_vector_fit_system(s_values: np.ndarray,
                                   poles_s: np.ndarray,
                                   include_constant_term: bool,
                                   include_proportional_term: bool) -> np.ndarray:
    """
    Build the final fixed-pole rational least-squares system.

    :param s_values: Complex frequency samples.
    :param poles_s: Fixed pole vector.
    :param include_constant_term: Whether to include one constant term.
    :param include_proportional_term: Whether to include one proportional term.
    :return: Complex least-squares matrix.
    """
    basis_matrix: np.ndarray = _build_reciprocal_pole_basis(s_values, poles_s)
    column_blocks: list[np.ndarray] = list([basis_matrix])
    row_count: int = int(s_values.size)

    if include_constant_term:
        column_blocks.append(np.ones((row_count, 1), dtype=np.complex128))
    else:
        pass

    if include_proportional_term:
        column_blocks.append(s_values.reshape(-1, 1))
    else:
        pass

    return np.hstack(column_blocks)


def evaluate_jmarti_rational_mode_fit(fit: JMartiRationalModeFit,
                                      frequency_hz: Sequence[float]) -> np.ndarray:
    """
    Evaluate one fitted scalar rational mode on the imaginary axis.

    :param fit: Fitted scalar rational mode.
    :param frequency_hz: Frequency grid in Hz.
    :return: Complex response samples.
    """
    s_values: np.ndarray = build_jmarti_complex_frequency_points(frequency_hz)
    basis_matrix: np.ndarray = _build_reciprocal_pole_basis(s_values, fit.get_poles_s())
    response_values: np.ndarray = basis_matrix @ fit.get_residues()

    response_values = response_values + fit.get_constant_term()
    response_values = response_values + fit.get_proportional_term() * s_values
    return np.asarray(response_values, dtype=np.complex128)


def build_jmarti_mode_vector_fit(frequency_hz: Sequence[float],
                                 response_values: np.ndarray,
                                 loewner_seed: JMartiModeLoewnerSeed,
                                 options: JMartiFitOptions | None = None) -> JMartiRationalModeFit:
    """
    Build one scalar Vector Fitting refinement from a Loewner seed.

    :param frequency_hz: Frequency grid in Hz.
    :param response_values: Complex scalar response samples on that grid.
    :param loewner_seed: Loewner order/pole seed.
    :param options: Optional user-configurable JMARTI fitting options.
    :return: Scalar rational fit.
    """
    resolved_options: JMartiFitOptions = JMartiFitOptions() if options is None else options
    s_values: np.ndarray = build_jmarti_complex_frequency_points(frequency_hz)
    response_array: np.ndarray = np.asarray(response_values, dtype=np.complex128)
    current_poles_s: np.ndarray = _sort_poles_by_real_imag(loewner_seed.get_initial_poles_s())
    relocation_iteration: int = 0
    converged: bool = False
    include_constant_term: bool = resolved_options.get_vf_include_constant_term()
    include_proportional_term: bool = resolved_options.get_vf_include_proportional_term()
    system_matrix: np.ndarray
    rhs_vector: np.ndarray
    solution_vector: np.ndarray
    residues: np.ndarray
    constant_term: complex
    proportional_term: complex
    sigma_residues: np.ndarray
    relocated_poles_s: np.ndarray
    relative_shift: float
    final_system_matrix: np.ndarray
    final_solution_vector: np.ndarray
    fitted_response: np.ndarray
    fit_error_rms: float
    max_relative_error: float
    stable: bool

    # Stage 1: relaxed pole relocation iterations.
    while relocation_iteration < resolved_options.get_vf_max_iterations():
        system_matrix, rhs_vector = _build_vector_fit_relocation_system(
            s_values=s_values,
            response_values=response_array,
            poles_s=current_poles_s,
            include_constant_term=include_constant_term,
            include_proportional_term=include_proportional_term,
        )
        final_solution_vector = np.linalg.lstsq(system_matrix, rhs_vector, rcond=None)[0]
        residues, constant_term, proportional_term, sigma_residues = _extract_relocation_coefficients(
            solution_vector=final_solution_vector,
            pole_count=current_poles_s.size,
            include_constant_term=include_constant_term,
            include_proportional_term=include_proportional_term,
        )
        relocated_poles_s = _relocate_poles_from_sigma(
            current_poles_s=current_poles_s,
            sigma_residues=sigma_residues,
        )

        if resolved_options.get_vf_enforce_stable_poles():
            relocated_poles_s = _enforce_stable_poles(
                poles_s=relocated_poles_s,
                real_part_floor=resolved_options.get_vf_stability_real_part_floor(),
            )
        else:
            pass

        relocated_poles_s = _sort_poles_by_real_imag(relocated_poles_s)
        relative_shift = _compute_relative_pole_shift(current_poles_s, relocated_poles_s)
        current_poles_s = relocated_poles_s
        relocation_iteration += 1

        if relative_shift <= resolved_options.get_vf_pole_shift_tolerance():
            converged = True
            break
        else:
            pass

    # Stage 2: final fixed-pole residue solve.
    final_system_matrix = _build_final_vector_fit_system(
        s_values=s_values,
        poles_s=current_poles_s,
        include_constant_term=include_constant_term,
        include_proportional_term=include_proportional_term,
    )
    final_solution_vector = np.linalg.lstsq(final_system_matrix, response_array, rcond=None)[0]
    residues = np.asarray(final_solution_vector[:current_poles_s.size], dtype=np.complex128)
    constant_term = 0.0 + 0.0j
    proportional_term = 0.0 + 0.0j

    if include_constant_term:
        constant_term = complex(final_solution_vector[current_poles_s.size])
        if include_proportional_term:
            proportional_term = complex(final_solution_vector[current_poles_s.size + 1])
        else:
            pass
    else:
        if include_proportional_term:
            proportional_term = complex(final_solution_vector[current_poles_s.size])
        else:
            pass

    fitted_response = evaluate_jmarti_rational_mode_fit(
        fit=JMartiRationalModeFit(
            mode_index=loewner_seed.get_mode_index(),
            target_name=loewner_seed.get_target_name(),
            poles_s=current_poles_s,
            residues=residues,
            constant_term=constant_term,
            proportional_term=proportional_term,
            fit_error_rms=0.0,
            max_relative_error=0.0,
            iterations_completed=relocation_iteration,
            converged=converged,
            stable=False,
        ),
        frequency_hz=frequency_hz,
    )
    fit_error_rms = float(np.linalg.norm(fitted_response - response_array) / max(np.linalg.norm(response_array), 1.0e-16))
    max_relative_error = float(np.max(np.abs(fitted_response - response_array) / (np.abs(response_array) + 1.0e-16)))
    stable = bool(np.all(np.real(current_poles_s) < 0.0))

    return JMartiRationalModeFit(
        mode_index=loewner_seed.get_mode_index(),
        target_name=loewner_seed.get_target_name(),
        poles_s=current_poles_s,
        residues=residues,
        constant_term=constant_term,
        proportional_term=proportional_term,
        fit_error_rms=fit_error_rms,
        max_relative_error=max_relative_error,
        iterations_completed=relocation_iteration,
        converged=converged,
        stable=stable,
    )
