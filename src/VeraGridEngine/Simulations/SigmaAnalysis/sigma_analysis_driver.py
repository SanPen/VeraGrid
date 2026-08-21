# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
import numba as nb
from matplotlib import pyplot as plt
from typing import Union

from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGridEngine.Simulations.results_template import ResultsTemplate, ResultsProperty
from VeraGridEngine.enumerations import (ResultTypes, DeviceType, StudyResultsType, SimulationTypes,
                                         ShuntControlMode, GeneratorControlMode)
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.helm_power_flow import (helm_coefficients_josep,
                                                                                   sigma_function)
from VeraGridEngine.Simulations.SigmaAnalysis.sigma_dpr import DprSigmaResult, sigma_dpr
from VeraGridEngine.Simulations.driver_template import DriverTemplate
from VeraGridEngine.basic_structures import Vec, StrVec, CxVec


class SigmaAnalysisResults(ResultsTemplate):
    """
    SigmaAnalysisResults
    """

    LOCAL_RESULTS_DECLARATIONS = (
        ResultsProperty(name='lambda_value', tpe=float, old_names=list(), expandable=False),
        ResultsProperty(name='bus_names', tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name='Sbus', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='distances', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='sigma_re', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='sigma_im', tpe=Vec, old_names=list(), expandable=False),
    )

    __slots__ = (
        "n",
        "lambda_value",
        "bus_names",
        "Sbus",
        "distances",
        "sigma_re",
        "sigma_im",
        "elapsed",
        "converged",
        "convergence_reports",
    )

    def __init__(self, n):
        available_results = [
            ResultTypes.SigmaReal,
            ResultTypes.SigmaImag,
            ResultTypes.SigmaDistances,
            ResultTypes.SigmaPlusDistances,
        ]

        ResultsTemplate.__init__(
            self,
            name='Sigma analysis',
            available_results=available_results,
            time_array=None,
            clustering_results=None,
            study_results_type=StudyResultsType.SigmaAnalysis,
        )

        self.n = n

        self.lambda_value = 1.0

        self.bus_names = np.zeros(n, dtype=object)

        self.Sbus = np.zeros(n, dtype=complex)

        self.distances = np.zeros(n, dtype=float) + 0.25  # the default distance is 0.25

        self.sigma_re = np.zeros(n, dtype=float)

        self.sigma_im = np.zeros(n, dtype=float)

        self.elapsed = 0

        self.converged = True

        self.convergence_reports = list()


    def apply_from_island(self, results: "SigmaAnalysisResults", b_idx):
        """
        Apply results from another island circuit to the circuit results represented
        here.

        Arguments:

            **results**: PowerFlowResults

            **b_idx**: bus original indices

            **elm_idx**: branch original indices
        """
        self.Sbus[b_idx] = results.Sbus

        self.distances[b_idx] = results.distances

        self.sigma_re[b_idx] = results.sigma_re

        self.sigma_im[b_idx] = results.sigma_im

        self.converged = self.converged & results.converged

    def plot(self, fig, ax, n_points=1000):
        """
        Plot the sigma analysis
        :param fig: Matplotlib figure. If None, one will be created
        :param ax: Matplotlib Axis
        :param n_points: number of points in the curve
        """
        if ax is None:
            fig = plt.figure(figsize=(8, 7))
            ax = fig.add_subplot(111)

        sx = np.linspace(-0.25, np.max(self.sigma_re) + 0.1, n_points)
        sy1 = np.sqrt(0.25 + sx)
        sy2 = -np.sqrt(0.25 + sx)
        names = self.bus_names

        ax.plot(sx, sy1, 'k', linewidth=2)
        ax.plot(sx, sy2, 'k', linewidth=2)

        d = np.abs(np.nan_to_num(self.distances))
        colors = (d / d.max())
        area = 100.0 * np.power(1.0 + d, 2)

        if self.converged:
            cmap = 'winter'
        else:
            cmap = 'autumn'

        sc = ax.scatter(self.sigma_re, self.sigma_im, c=colors, s=area, cmap=cmap, alpha=0.75)

        annot = ax.annotate("", xy=(0, 0), xytext=(20, 20),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w"),
                            arrowprops=dict(arrowstyle="->"),
                            fontsize=8)
        annot.set_visible(False)

        ax.set_title(r'$\Sigma$ plot')
        ax.set_xlabel(r'$\sigma_{re}$')
        ax.set_ylabel(r'$\sigma_{im}$')

        def update_annotation(ind):
            """

            :param ind:
            :return:
            """
            pos = sc.get_offsets()[ind["ind"][0]]
            annot.xy = pos
            text = "{}".format("\n".join([names[n] for n in ind["ind"]]))
            annot.set_text(text)
            annot.get_bbox_patch().set_alpha(0.8)

        def hover(event):
            if event.inaxes == ax:
                cont, ind = sc.contains(event)
                if cont:
                    update_annotation(ind)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                else:
                    if annot.get_visible():
                        annot.set_visible(False)
                        fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", hover)

    def mdl(self, result_type: ResultTypes, indices=None, names=None) -> ResultsTable | None:
        """

        :param result_type:
        :param indices:
        :param names:
        :return:
        """

        if indices is None and names is not None:
            indices = np.array(range(len(names)))

        if len(indices) > 0:
            labels = names[indices]

            if result_type == ResultTypes.SigmaDistances:
                y = np.abs(self.distances[indices])
                y_label = '(p.u.)'
                title = 'Sigma distances '

                return ResultsTable(data=y,
                                    index=labels,
                                    idx_device_type=DeviceType.BusDevice,
                                    columns=np.array([result_type.value]),
                                    cols_device_type=DeviceType.NoDevice,
                                    title=title,
                                    ylabel=y_label,
                                    units=y_label)

            elif result_type == ResultTypes.SigmaReal:
                y = self.sigma_re[indices]
                y_label = '(deg)'
                title = 'Real sigma '

                return ResultsTable(data=y,
                                    index=labels,
                                    idx_device_type=DeviceType.BusDevice,
                                    columns=np.array([result_type.value]),
                                    cols_device_type=DeviceType.NoDevice,
                                    title=title,
                                    ylabel=y_label,
                                    units=y_label)

            elif result_type == ResultTypes.SigmaImag:
                y = self.sigma_im[indices]
                y_label = '(p.u.)'
                title = 'Imaginary Sigma '

                return ResultsTable(data=y,
                                    index=labels,
                                    idx_device_type=DeviceType.BusDevice,
                                    columns=np.array([result_type.value]),
                                    cols_device_type=DeviceType.NoDevice,
                                    title=title,
                                    ylabel=y_label,
                                    units=y_label)

            elif result_type == ResultTypes.SigmaPlusDistances:
                y = np.c_[self.sigma_re[indices], self.sigma_im[indices], self.distances[indices]]
                y_label = '(p.u.)'
                title = 'Sigma and distances'

                mdl = ResultsTable(data=y,
                                   index=labels,
                                   idx_device_type=DeviceType.BusDevice,
                                   columns=np.array(['σ real', 'σ imaginary', 'Distances']),
                                   cols_device_type=DeviceType.NoDevice,
                                   title=title,
                                   ylabel=y_label,
                                   units=y_label)
                return mdl

            else:
                raise Exception('Unsupported result type: ' + str(result_type))

        else:
            return None


def multi_island_sigma(multi_circuit: MultiCircuit,
                       options: PowerFlowOptions,
                       logger: Logger = Logger(),
                       t_idx: int | None = None,
                       classical_sigma: bool = False,
                       dpr_use_stored_guess: bool = True,
                       dpr_control_q: bool | None = None,
                       dpr_control_discrete_shunts: bool = True,
                       dpr_control_qv_droop: bool = True,
                       dpr_distributed_slack: bool | None = None) -> SigmaAnalysisResults:
    """
    Multiple islands power flow (this is the most generic power flow function)
    :param multi_circuit: MultiCircuit instance
    :param options: PowerFlowOptions instance
    :param logger: list of events to add to
    :param t_idx: Time-series index to compile. None uses the snapshot values.
    :param classical_sigma: Use the original single-embedding HELM sigma instead of DPR path sigma.
    :param dpr_use_stored_guess: Use stored voltages as DPR initial germ instead of the classical no-load germ.
    :param dpr_control_q: Apply PV/P reactive limit control in DPR sigma. If None, use the power-flow option.
    :param dpr_control_discrete_shunts: Apply discrete shunt controls in DPR sigma.
    :param dpr_control_qv_droop: Apply generator QV droop controls in DPR sigma.
    :param dpr_distributed_slack: Apply distributed slack in DPR sigma. If None, use the power-flow option.
    :return: PowerFlowResults instance
    """
    n = len(multi_circuit.buses)
    active_control_q: bool = options.control_Q if dpr_control_q is None else dpr_control_q
    active_distributed_slack: bool = options.distributed_slack if dpr_distributed_slack is None else dpr_distributed_slack

    results = SigmaAnalysisResults(n)

    nc = compile_numerical_circuit_at(circuit=multi_circuit,
                                      t_idx=t_idx,
                                      apply_temperature=options.apply_temperature_correction,
                                      branch_tolerance_mode=options.branch_impedance_tolerance_mode,
                                      opf_results=None,
                                      logger=logger)
    results.bus_names = nc.bus_data.names

    Shvdc, Losses_hvdc, Pf_hvdc, Pt_hvdc, loading_hvdc, n_free = nc.hvdc_data.get_power(
        Sbase=nc.Sbase,
        theta=np.zeros(nc.nbus),
    )

    islands = nc.split_into_islands(ignore_single_node_islands=options.ignore_single_node_islands,
                                    consider_hvdc_as_island_links=False,
                                    logger=logger)

    if len(islands) == 0:
        return results

    # simulate each island and merge the results
    for i, island in enumerate(islands):

        # we cannot handle P and PQV node types, hence we must convert those:
        # PQ_tpe = 1  # control P, Q
        # PV_tpe = 2  # Control P, Vm
        # Slack_tpe = 3  # Control Vm, Va (slack)
        # PQV_tpe = 4  # voltage-controlled bus (P, Q, V set, theta computed)
        # P_tpe = 5  # voltage-controlling bus (P set, Q, V, theta computed)

        # bus_types = island.bus_data.bus_types.copy()

        # PQV to PQ
        # bus_types[bus_types == 4] = 1

        # # P tp PV
        # bus_types[bus_types == 5] = 2

        # make sure
        # replace_bus_types(bus_types)

        # if 4 in bus_types:
        #     raise Exception("Handled bus types don't match")
        # if 5 in bus_types:
        #     raise Exception("Handled bus types don't match")

        # for i in range(island.nbus):
        #     if bus_types[i] == BusMode.PQV_tpe.value: # PQV to PQ
        #         bus_types[i] = BusMode.PQ_tpe.value
        #     elif bus_types[i] == BusMode.P_tpe.value: # P tp PV
        #         bus_types[i] = BusMode.PV_tpe.value

        S0 = island.get_power_injections_pu()
        Sbus = S0 + Shvdc[island.bus_data.original_idx]
        if classical_sigma:
            indices = island.get_simulation_indices(Sbus=Sbus, force_only_pq_pv_vd_types=True)
        else:
            # DPR sigma can use the same remote-voltage and control-aware bus partitions as DPR power flow.
            indices = island.get_simulation_indices(Sbus=Sbus, force_only_pq_pv_vd_types=False)

        if len(indices.vd) > 0:

            adm = island.get_admittance_matrices()
            adms = island.get_series_admittance_matrices()

            if classical_sigma:
                run_classical_sigma: bool = len(indices.pv) + len(indices.pq) + len(indices.vd) == island.nbus
            else:
                run_classical_sigma = False

            if run_classical_sigma:

                # V, converged, norm_f, Scalc, iter_, elapsed, Sig_re, Sig_im
                U, X, Q, V, iter_, converged = helm_coefficients_josep(Ybus=adm.Ybus,
                                                                       Yseries=adms.Yseries,
                                                                       V0=island.bus_data.Vbus,
                                                                       S0=Sbus,
                                                                       Ysh0=adms.Yshunt,
                                                                       pq=indices.pq,
                                                                       pv=indices.pv,
                                                                       sl=indices.vd,
                                                                       no_slack=indices.no_slack,
                                                                       tolerance=options.tolerance,
                                                                       max_coeff=options.max_iter,
                                                                       verbose=False,
                                                                       stop_if_too_bad=False,
                                                                       logger=logger)

                # compute the sigma values
                n = island.bus_data.nbus
                sig_re = np.zeros(n, dtype=float)
                sig_im = np.zeros(n, dtype=float)

                try:
                    if iter_ > 1:
                        sigma = sigma_function(U, X, iter_ - 1, island.bus_data.Vbus[indices.vd])
                        sig_re[indices.no_slack] = np.real(sigma)
                        sig_im[indices.no_slack] = np.imag(sigma)
                    else:
                        sig_re = np.zeros(n, dtype=float)
                        sig_im = np.zeros(n, dtype=float)
                except np.linalg.LinAlgError:
                    print('numpy.linalg.LinAlgError: Matrix is singular to machine precision.')
                    sig_re = np.zeros(n, dtype=float)
                    sig_im = np.zeros(n, dtype=float)

                sigma_distances = sigma_distance(sig_re, sig_im)

                # store the results
                island_results = SigmaAnalysisResults(n=n)
                island_results.lambda_value = 1.0
                island_results.Sbus = Sbus
                island_results.sigma_re = sig_re
                island_results.sigma_im = sig_im
                island_results.distances = sigma_distances
                island_results.converged = converged

                # merge the results from this island
                results.apply_from_island(island_results, island.bus_data.original_idx)
            else:
                if classical_sigma:
                    logger.add_info("Handled bus types don't match")
                else:
                    # DPR sigma follows the controlled DPR power-flow path. Control changes are model restarts, so the
                    # sigma values are computed from the accepted DPR segments of the final settled controlled model.
                    Qmax: Vec
                    Qmin: Vec
                    Qmax, Qmin = island.get_reactive_power_limits()
                    dpr_result: DprSigmaResult = sigma_dpr(
                        nc=island,
                        Ybus=adm.Ybus,
                        Yshunt_bus=adm.Yshunt_bus,
                        Yseries=adms.Yseries,
                        V0=island.bus_data.Vbus,
                        S0=Sbus,
                        Ysh0=adms.Yshunt,
                        pq=indices.pq,
                        pv=indices.pv,
                        vd=indices.vd,
                        no_slack=indices.no_slack,
                        tolerance=options.tolerance,
                        max_coefficients=options.max_iter,
                        restart_order=6,
                        max_restarts=20,
                        use_classical_germ=not dpr_use_stored_guess,
                        control_q=active_control_q,
                        pqv=indices.pqv,
                        p=indices.p,
                        Qmin=Qmin,
                        Qmax=Qmax,
                        control_discrete_shunts=bool(dpr_control_discrete_shunts and np.any(
                            island.shunt_data.control_mode_int == ShuntControlMode.Discrete.idx())),
                        control_qv_droop=bool(dpr_control_qv_droop and np.any(
                            island.generator_data.control_mode_int == GeneratorControlMode.QVDroop.idx())),
                        distributed_slack=active_distributed_slack,
                        bus_installed_power=island.bus_data.installed_power,
                        controls_tol=options.controls_start_tolerance,
                        verbose=0,
                        logger=logger
                    )

                    island_results = SigmaAnalysisResults(n=island.bus_data.nbus)
                    island_results.lambda_value = 1.0
                    island_results.Sbus = Sbus
                    island_results.sigma_re = dpr_result.sigma_re
                    island_results.sigma_im = dpr_result.sigma_im
                    island_results.distances = dpr_result.distances
                    island_results.converged = dpr_result.converged

                    # merge the results from this island
                    results.apply_from_island(island_results, island.bus_data.original_idx)
        else:
            logger.add_info('No slack nodes in the island', str(i))

    # expand voltages if there was a bus topology reduction
    if nc.topology_performed:
        results.sigma_re = nc.propagate_bus_result(results.sigma_re)
        results.sigma_im = nc.propagate_bus_result(results.sigma_im)

    return results


@nb.jit(cache=True, nopython=True)
def sigma_distance(sigma_real, sigma_imag) -> Vec:
    """
    Distance to the collapse in the sigma space

    The boundary curve is given by y = sqrt(1/4 + x)

    the distance is d = sqrt((x-a)^2 + (sqrt(1/4+ x) - b)^2)

    the derivative of this is d'=(2 (-a + x) + (-b + sqrt(1/4 + x))/sqrt(1/4 + x))/(2 sqrt((-a + x)^2 + (-b + sqrt(1/4 + x))^2))

    Making d'=0, and solving for x, we obtain:

    x1 = 1/12 (-64 a^3 + 48 a^2
               + 12 sqrt(3) sqrt(-64 a^3 b^2 + 48 a^2 b^2 - 12 a b^2 + 108 b^4 + b^2)
               - 12 a + 216 b^2 + 1)^(1/3) - (-256 a^2 + 128 a - 16)/
         (192 (-64 a^3 + 48 a^2
               + 12 sqrt(3) sqrt(-64 a^3 b^2 + 48 a^2 b^2 - 12 a b^2 + 108 b^4 + b^2)
               - 12 a + 216 b^2 + 1)^(1/3)) + 1/12 (8 a - 5)

    x2 = 1/12 (-64 a^3 + 48 a^2
               + 12 sqrt(3) sqrt(-64 a^3 b^2 + 48 a^2 b^2 - 12 a b^2 + 108 b^4 + b^2)
               - 12 a + 216 b^2 + 1)^(1/3) - (-256 a^2 + 128 a - 16) /
         (192 (-64 a^3 + 48 a^2
               + 12 sqrt(3) sqrt(-64 a^3 b^2 + 48 a^2 b^2 - 12 a b^2 + 108 b^4 + b^2)
               - 12 a + 216 b^2 + 1)^(1/3)) + 1/12 (8 a - 5)
    :param sigma_real: Sigma real array
    :param sigma_imag: Sigma imag array
    :return: distance of the sigma point to the curve sqrt(0.25 + x)
    """
    n = len(sigma_real)
    x1 = np.zeros(n)

    i = 0
    sq3 = np.sqrt(3)

    for a, b in zip(sigma_real, sigma_imag):

        t0 = -64 * a ** 3 * b ** 2 \
             + 48 * a ** 2 * b ** 2 \
             - 12 * a * b ** 2 \
             + 108 * b ** 4 + b ** 2

        if t0 > 0:

            t1 = (-64 * a ** 3
                  + 48 * a ** 2
                  + 12 * sq3 * np.sqrt(t0)
                  - 12 * a + 216 * b ** 2 + 1) ** (1 / 3)

            # the value is within limits
            x1[i] = 1 / 12 * t1 - (-256 * a ** 2 + 128 * a - 16) / (192 * t1) + 1 / 12 * (8 * a - 5)
        else:
            t1 = (-64 * a ** 3
                  + 48 * a ** 2
                  + 12 * sq3 * np.sqrt(-t0)
                  - 12 * a + 216 * b ** 2 + 1) ** (1 / 3)

            # here I set the value negative to indicate that it is off-limits
            x1[i] = -(1 / 12 * t1 - (-256 * a ** 2 + 128 * a - 16) / (192 * t1) + 1 / 12 * (8 * a - 5))

        i += 1

    return x1


class SigmaAnalysisDriver(DriverTemplate):
    __slots__ = (
        "options",
        "t_idx",
        "classical_sigma",
        "dpr_use_stored_guess",
        "dpr_control_q",
        "dpr_control_discrete_shunts",
        "dpr_control_qv_droop",
        "dpr_distributed_slack",
        "convergence_reports",
    )

    name = 'Sigma Analysis'
    tpe = SimulationTypes.SigmaAnalysis_run

    def __init__(self,
                 grid: MultiCircuit,
                 options: PowerFlowOptions,
                 t_idx: int | None = None,
                 classical_sigma: bool = False,
                 dpr_use_stored_guess: bool = True,
                 dpr_control_q: bool | None = None,
                 dpr_control_discrete_shunts: bool = True,
                 dpr_control_qv_droop: bool = True,
                 dpr_distributed_slack: bool | None = None):
        """
        PowerFlowDriver class constructor
        :param grid: MultiCircuit instance
        :param options: PowerFlowOptions instance
        :param t_idx: Time-series index to compile. None uses the snapshot values.
        :param classical_sigma: Use the original single-embedding HELM sigma instead of DPR path sigma.
        :param dpr_use_stored_guess: Use stored voltages as DPR initial germ instead of the classical no-load germ.
        :param dpr_control_q: Apply PV/P reactive limit control in DPR sigma. If None, use the power-flow option.
        :param dpr_control_discrete_shunts: Apply discrete shunt controls in DPR sigma.
        :param dpr_control_qv_droop: Apply generator QV droop controls in DPR sigma.
        :param dpr_distributed_slack: Apply distributed slack in DPR sigma. If None, use the power-flow option.
        """
        DriverTemplate.__init__(self, grid=grid)

        # Options to use
        self.options = options
        self.t_idx = t_idx
        self.classical_sigma = classical_sigma
        self.dpr_use_stored_guess = dpr_use_stored_guess
        self.dpr_control_q = dpr_control_q
        self.dpr_control_discrete_shunts = dpr_control_discrete_shunts
        self.dpr_control_qv_droop = dpr_control_qv_droop
        self.dpr_distributed_slack = dpr_distributed_slack

        self.results: Union[None, SigmaAnalysisResults] = None

        self.logger = Logger()

        self.convergence_reports = list()

        self.__cancel__ = False

    def get_steps(self):
        """

        :return:
        """
        return list()

    def run(self):
        """
        Pack run_pf for the QThread
        :return:
        """
        self.tic()
        self.results = multi_island_sigma(multi_circuit=self.grid,
                                          options=self.options,
                                          logger=self.logger,
                                          t_idx=self.t_idx,
                                          classical_sigma=self.classical_sigma,
                                          dpr_use_stored_guess=self.dpr_use_stored_guess,
                                          dpr_control_q=self.dpr_control_q,
                                          dpr_control_discrete_shunts=self.dpr_control_discrete_shunts,
                                          dpr_control_qv_droop=self.dpr_control_qv_droop,
                                          dpr_distributed_slack=self.dpr_distributed_slack)
        self.toc()

    def cancel(self):
        self.__cancel__ = True
