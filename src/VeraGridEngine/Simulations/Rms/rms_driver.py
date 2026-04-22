# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
import pandas as pd
import numpy as np

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.driver_template import DriverTemplate
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Simulations.Rms.rms_results import RmsResults
from VeraGridEngine.Simulations.Rms.rms_problem_factory import build_rms_problem
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import BackEulerImplicitIntegration
from VeraGridEngine.enumerations import EngineType, SimulationTypes, DynamicIntegrationMethod
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowResults
from VeraGridEngine.basic_structures import Vec, StrVec


class RmsSimulationDriver(DriverTemplate):
    __slots__ = (
        "pf_results",
        "options",
        "problem",
    )

    name = 'Rms Simulation'
    tpe = SimulationTypes.RmsDynamic_run

    """
    Dynamic wrapper to use with Qt
    """

    def __init__(self,
                 grid: MultiCircuit,
                 options: RmsOptions,
                 pf_results: PowerFlowResults,
                 engine: EngineType = EngineType.VeraGrid):
        """
        DynamicDriver class constructor
        :param grid: MultiCircuit instance
        :param options: RmsOptions instance
        :param pf_results: PowerFlowResults
        :param engine: EngineType (i.e., EngineType.VeraGrid) (optional)
        """

        DriverTemplate.__init__(self, grid=grid, engine=engine)

        self.grid = grid

        self.pf_results: PowerFlowResults = pf_results

        self.options = options

        self.results: RmsResults | None = None
        self.problem: RmsProblemDae | None = None

    def run(self):
        """
        Main function to initialize and run the system simulation.

        This function sets up logging, starts the dynamic simulation, and
        logs the outcome. It handles and logs any exceptions raised during execution.
        :return:
        """
        # Run the dynamic simulation
        self.run_time_simulation()

    def run_time_simulation(self):
        """
        Performs the numerical integration using the chosen method.
        :return:
        """

        self.progress_signal.emit(0)

        rms_events_groups = (self.grid.rms_events_groups
                             if self.grid.rms_events_groups is None
                             else self.grid.rms_events_groups)

        steps = int(np.ceil((self.options.simulation_time - 0) / self.options.time_step))
        t: Vec = np.arange(steps + 1) * self.options.time_step

        rms_events_group_names: StrVec = np.array([elm.name for elm in rms_events_groups])

        problem = build_rms_problem(
            grid=self.grid,
            options=self.options,
            pf_results=self.pf_results,
            progress_signal=self.progress_signal,
        )
        self.problem = problem
        self.results = RmsResults(
            time_array=pd.DatetimeIndex(pd.to_datetime(t * 1e9)),
            rms_events_group_names=rms_events_group_names,
            variables=problem.state_and_algebraic_vars,
            uid2idx=problem.uid2idx_vars,
            vars_glob_name2uid=problem.vars_glob_name2uid,
            devices_vars_info=problem.get_device_vars_dict()
        )

        for group_idx, rms_events_group in enumerate(rms_events_groups):

            self.report_text("Simulating RMS event group " + rms_events_group.name)

            self.progress_signal.emit(5)

            self.report_text("Simulating RMS event group " + rms_events_group.name)
            problem.set_events_group(rms_events_group=rms_events_group)
            problem.reset_boundary_update_state(0.0)

            # DaeTrapezoidal = "DAE_Trapezoidal"
            # DaeBackEuler = "DAE_BackEuler"
            # DaeBDF2 = "DAE_bdf2"
            # DaeContinuous = "DAE_Continuous"
            # OdeRungeKutta4 = "ODE_Runge_Kutta 4"
            # OdeEuler = "ODE_Euler"

            if self.options.integration_method == DynamicIntegrationMethod.DaeBackEuler:

                self.report_text(
                    f"Simulating RMS event group  {rms_events_group.name} with "
                    f"{self.options.integration_method.value}"
                )
                solver = BackEulerImplicitIntegration(
                    problem=problem,
                    t0=0,
                    t_end=self.options.simulation_time,
                    h=self.options.time_step,
                    max_iter=self.options.max_iter
                )

            else:
                self.logger.add_info("Falling back to DAE-BackEuler method")

                self.report_text(
                    f"Simulating RMS event group  {rms_events_group.name} with back euler as fallback"
                )

                solver = BackEulerImplicitIntegration(
                    problem=problem,
                    t0=0,
                    t_end=self.options.simulation_time,
                    h=self.options.time_step,
                    max_iter=self.options.max_iter
                )

            t, y, well_initialized, converged = solver.simulate()

            self.results.converged[group_idx] = converged
            self.results.well_initialized[group_idx] = well_initialized
            self.results.values[:, :, group_idx] = y

            if not well_initialized:
                self.logger.add_warning("Not well initialized", device=rms_events_group.name)

            if not converged:
                self.logger.add_warning("Not converged", device=rms_events_group.name)

            self.progress_signal.emit(90)

        self.progress_signal.emit(100)
