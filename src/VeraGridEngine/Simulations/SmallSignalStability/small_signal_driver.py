# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import numba as nb
from matplotlib import pyplot as plt
import scipy.linalg
from scipy.sparse.linalg import spsolve
import math

from typing import Dict, Union
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Utils.Symbolic.block_solver import BlockSolver
from VeraGridEngine.Simulations.driver_template import DriverTemplate
from VeraGridEngine.Simulations.SmallSignalStability.small_signal_options import SmallSignalStabilityOptions
from VeraGridEngine.Simulations.SmallSignalStability.small_signal_results import SmallSignalStabilityResults
from VeraGridEngine.enumerations import EngineType, SimulationTypes
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowResults
from VeraGridEngine.Simulations.Rms.initialization import initialize_rms
from VeraGridEngine.basic_structures import Vec
from VeraGridEngine.enumerations import  ResultTypes


def compute_state_matrix(slv: BlockSolver, x: Vec, time: float,):
    """
    Small Signal Stability analysis
    :param slv: BlockSolver
    :param x: variables (1D numpy array)
    :param time: time (float)

    :return: np array state matrix(A)

    Small Signal Stability analysis:
    1. Calculate the state matrix (A) from the state space model. From the semi-explicit DAE model:
        Tx'=f(x,y)
        0=g(x,y)
        the A matrix is computed as:
        A = T^-1(f_x - f_y * g_y^{-1} * g_x)   #T is implicit in the jacobian!
    """

    params_current = slv.params_fn(time)

    fx = slv.j11(x, params_current)  # ∂f/∂x
    fy = slv.j12(x, params_current)  # ∂f/∂y
    gx = slv.j21(x, params_current)  # ∂g/∂x
    gy = slv.j22(x, params_current)  # ∂g/∂y

    gyx = spsolve(gy, gx)
    return fx - fy @ gyx

@nb.njit(cache=True)
def compute_participation_factors(An, Am, v, w, n_eigenvalues, num_states):
    """
    :param An: number of rows(states) in the state matrix
    :param Am: number of columns(modes) in the state matrix
    :param v: right eigenvectors
    :param w: left eigenvectors
    :param n_eigenvalues: number of eigenvalues
    :param num_states: number of states
    :return: participation factors
    """
    participation_factors = np.zeros((An, Am))
    for row in range(w.shape[0]):
        for column in range(w.shape[0]):
            participation_factors[row, column] = abs(w[row, column]) * abs(v[row, column])

    # normalize participation factors
    pfact_abs = np.ones(num_states) @ participation_factors
    for i in range(n_eigenvalues):
        participation_factors[:, i] /= pfact_abs[i]

    return participation_factors

# @nb.njit(cache=True)
def select_eigs_without_conjugates(eigenvalues):
    """
    :param eigenvalues: row np array with modes
    :return: row np array with only the positive complex conjugate modes
    """
    eig_no_conjugates = np.array([])
    seen = set()
    tol = 1e-12
    for z in eigenvalues:
        if np.isreal(z):
            seen.add(z)
        elif z.imag > tol:
            if z not in seen and np.conj(z) not in seen:
                seen.add(z)
                eig_no_conjugates =np.append(eig_no_conjugates,z)
        elif z.imag < tol:
            continue
    return eig_no_conjugates

@nb.njit(cache=True)
def compute_damping_ratios_and_frequencies(eigenvalues, eig_no_conjugates):
    """
    :param eigenvalues: row np array with modes
    :param eig_no_conjugates: row np array with only the positive complex conjugate modes
    :return: damping_ratios: list with damping ratios for the positive complex conjugate modes. Nan for other modes
    :return: conjugate_frequencies: list with oscillation frequencies for the positive complex conjugate modes. Nan for other modes
    """
    damping_ratios = np.full(eigenvalues.shape[0], np.nan, dtype=np.float64)
    conjugate_frequencies = np.full(eigenvalues.shape[0], np.nan, dtype=np.float64)
    tol = 1e-12
    match_tol = 1e-8

    for i in range(eigenvalues.shape[0]):
        mode = eigenvalues[i]
        found = False
        for j in range(eig_no_conjugates.shape[0]):
            if np.abs(mode - eig_no_conjugates[j]) <= match_tol:
                found = True
                break
        if found:
            re = mode.real
            im = mode.imag
            conjugate_frequencies[i] = im / (2.0 * np.pi)
            modz = np.abs(mode)
            if modz < tol:
                damping_ratios[i] = 0.0
            else:
                damping_ratios[i] = -re / modz
        else:
            damping_ratios[i] = np.nan
            conjugate_frequencies[i] = np.nan

    return damping_ratios, conjugate_frequencies

def plot_stability(eigenvalues, plot_units = "rad/s" ):
    """
        :param eigenvalues: row np array with modes
        :param plot_units: string with the imaginary units "rad/s" or "Hz"
        :return: plot S-domain modes
    """
    x = eigenvalues.real
    y = eigenvalues.imag
    slope = 1 / 0.05
    x_z = np.linspace(-200, 0, 400)
    y_z = slope * x_z

    x_label = "Re"
    y_label = "Im [rad/s]"

    if plot_units == "Hz":
        y = y / (2 * math.pi)
        y_z = y_z / (2 * math.pi)
        y_label = "Im [Hz]"

    # plot 5% damping ratio lines
    plt.plot(x_z, y_z, '--', color='grey', label='ζ = 5%')
    plt.plot(x_z, -y_z, '--', color='grey')
    # Plot the two lines (positive and negative imaginary axis)
    plt.axhline(0, color='black', linewidth=1)
    plt.axvline(0, color='black', linewidth=1)
    # plot modes
    plt.scatter(x, y, marker='x', color='blue')
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title("Stability plot")

    margin_x = (x.max() - x.min()) * 0.1
    margin_y = (y.max() - y.min()) * 0.1
    x_min = x.min() - margin_x
    x_max = x.max() + margin_x
    y_min = y.min() - margin_y
    y_max = y.max() + margin_y
    plt.xlim([x_min, x_max])
    plt.ylim([y_min, y_max])

    plt.tight_layout()
    plt.show()


def run_small_signal_stability(slv: BlockSolver, x: Vec, time: float, verbose: int = 0):
    """
    Small Signal Stability analysis
    :param slv: BlockSolver
    :param x: variables (1D numpy array)
    :param time: time (float)
    :param plot: True(default) if S-domain eigenvalues plot wanted. Else: False
    :param verbose: verbosity level (0 for none)
    :return:
        stability: str
            "Unstable", "Marginally stable" or "Asymptotically stable"
        eigenvalues:  1D row numpy array
        participation factors: 2D array csc matrix.
            Participation factors of mode i stored in PF[:,i]

    Small Signal Stability analysis:
    1. Calculate the state matrix (A) from the state space model. From the semi-explicit DAE model:
        Tx'=f(x,y)
        0=g(x,y)
        the A matrix is computed as:
        A = T^-1(f_x - f_y * g_y^{-1} * g_x)   #T is implicit in the jacobian!

    2. Find eigenvalues and right(V) and left(W) eigenvectors

    3. Calculate normalized participation factors PF = W · V

    4. Calculate damping ratios and oscillation frequencies of the complex conjugate poles
    """
    A = compute_state_matrix(slv,
                             x,
                             time) # sparse state matrix csc matrix
    num_states = A.shape[0]

    # Note: The eigenvalue solution is dense in practice and apparently there is no sparse way around it
    eigenvalues, w, v = scipy.linalg.eig(A.toarray(), left=True, right=True)

    # find participation factors
    participation_factors = compute_participation_factors(An=A.shape[0],
                                                          Am=A.shape[1],
                                                          v=v,
                                                          w=w,
                                                          n_eigenvalues=len(eigenvalues),
                                                          num_states=num_states)

    # find damping ratios and oscillation frequencies only for the complex conjugate modes
    eig_no_conjugates = select_eigs_without_conjugates(eigenvalues)

    damping_ratios, conjugate_freq = compute_damping_ratios_and_frequencies(eigenvalues = eigenvalues,
                                                                                   eig_no_conjugates = eig_no_conjugates)

    if verbose:
        print("State matrix:", A.toarray())
        print("Eigenvalues:", eigenvalues)
        print("Participation factors:", participation_factors)
        print("Daming ratios:", [str(r) if not np.isnan(r) else '-' for r in damping_ratios])
        print("Oscillation frequencies[Hz]:", [str(r) if not np.isnan(r) else '-' for r in conjugate_freq])


    return eigenvalues, participation_factors, damping_ratios, conjugate_freq, A.toarray()


class SmallSignalStabilityDriver(DriverTemplate):
    """
    SmallSignal_Stability_Driver
    """
    name = 'Small Signal Stability Simulation'
    tpe = SimulationTypes.SmallSignal_run

    def __init__(self, grid: MultiCircuit,
                 options: Union[SmallSignalStabilityOptions, None] = None,
                 pf_results: Union[PowerFlowResults, None] = None,
                 engine: EngineType = EngineType.VeraGrid):

        """
        DynamicDriver class constructor
        :param grid: MultiCircuit instance
        :param options: SmallSignalOptions instance
        :param pf_results: PowerFlowResults
        :param engine: EngineType (i.e., EngineType.VeraGrid) (optional)
        """

        DriverTemplate.__init__(self, grid=grid, engine=engine)

        self.grid = grid

        self.pf_results: Union[PowerFlowResults, None] = pf_results

        self.options: SmallSignalStabilityOptions = SmallSignalStabilityOptions() if options is None else options

        self.results: SmallSignalStabilityResults = SmallSignalStabilityResults(eigenvalues=np.empty(0),
                                                                                participation_factors=np.empty(0),
                                                                                damping_ratios=np.empty(0),
                                                                                conjugate_frequencies=np.empty(0),
                                                                                state_matrix =np.empty(0),
                                                                                stat_vars=[],
                                                                                vars2device={})

        self.__cancel__ = False

    def run(self):
        """
        Main function to initialize and run the system simulation.

        This function sets up logging, starts the dynamic simulation, and
        logs the outcome. It handles and logs any exceptions raised during execution.
        :return:
        """
        # Run the dynamic simulation
        self.run_small_signal_stability()

    def run_small_signal_stability(self):
        """
        Performs the numerical integration using the chosen method.
        :return:
        """
        self.tic()

        params_mapping: Dict = dict()

        time, ss, init_guess = initialize_rms(self.grid, self.pf_results)
        slv = BlockSolver(ss, time)

        params0 = slv.build_init_params_vector(params_mapping)
        x0 = slv.build_init_vars_vector_from_uid(init_guess)

        if not self.options.ss_assessment_time == 0:
            # Get integration method
            if self.options.integration_method == "trapezoid":
                integrator = "trapezoid"
            elif self.options.integration_method == "implicit euler":
                integrator = "implicit_euler"
            else:
                raise ValueError(f"integrator not implemented :( {self.options.integration_method}")

            t, y = slv.simulate(
                t0=0,
                t_end=self.options.ss_assessment_time,
                h=self.options.time_step,
                x0=x0,
                params0=params0,
                method=integrator
            )

            i = int(self.options.ss_assessment_time / self.options.time_step)
            (eigenvalues,
             participation_factors,
             damping_ratios,
             conjugate_frequencies,
             state_matrix) = run_small_signal_stability(slv=slv, x=y[i], time = self.options.ss_assessment_time)

        else:

            (eigenvalues,
             participation_factors,
             damping_ratios,
             conjugate_frequencies,
             state_matrix) = run_small_signal_stability(slv=slv, x=x0, time = 0)

        self.results: SmallSignalStabilityResults = SmallSignalStabilityResults(
            eigenvalues = eigenvalues,
            participation_factors = participation_factors,
            damping_ratios = damping_ratios,
            conjugate_frequencies = conjugate_frequencies,
            state_matrix = state_matrix,
            stat_vars = slv.state_vars,
            vars2device = slv.vars2device
        )

        self.toc()
