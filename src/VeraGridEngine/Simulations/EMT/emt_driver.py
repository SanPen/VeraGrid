# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import pandas as pd
from typing import Dict

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.driver_template import DriverTemplate
from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.Simulations.EMT.emt_results import EmtResults
from VeraGridEngine.Simulations.EMT.emt_problem_factory import build_emt_problem
from VeraGridEngine.Simulations.EMT.emt_solver_factory import build_emt_solver
from VeraGridEngine.Simulations.EMT.problems.emt_problem_dae import EmtProblemDae
from VeraGridEngine.Simulations.PowerFlow.power_flow_results_3ph import PowerFlowResults3Ph
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import PowerFlowResults
from VeraGridEngine.Utils.Symbolic.diagnostic import NewtonDiagnosticsConfig
from VeraGridEngine.IO.fmu.importer.emt_boundary import build_emt_boundary_updater
from VeraGridEngine.basic_structures import Vec, StrVec

from VeraGridEngine.enumerations import EngineType, SimulationTypes


def _collect_emt_group_parameter_values(problem: EmtProblemDae) -> Dict[str, float]:
    """
    Export one event-group parameter snapshot from the EMT problem.

    :param problem: Solved EMT problem instance.
    :return: Parameter scalar map keyed by ``device_idtag:param_name``.
    """
    parameter_values: Dict[str, float] = dict()
    event_parameter_count: int = len(problem.get_variable_parameters())
    parameter_index: int

    for parameter_index in range(event_parameter_count):
        parameter_var = problem.get_variable_parameters()[parameter_index]
        device_idtag: str | None = problem._event_parameter_device_idtags.get(parameter_var.uid, None)
        if device_idtag is not None:
            parameter_key: str = str(device_idtag) + ":" + str(parameter_var.name)
            parameter_values[parameter_key] = float(problem._event_params_values[parameter_index])
        else:
            pass

    return parameter_values


class EmtSimulationDriver(DriverTemplate):
    __slots__ = (
        "pf_results_3Ph",
        "pf_results",
        "options",
        "problem",
        "line_states",
    )

    name = 'EMT Simulation'
    tpe = SimulationTypes.EmtDynamic_run

    """
    Dynamic wrapper to use with Qt
    """

    def __init__(self,
                 grid: MultiCircuit,
                 options: EmtOptions,
                 pf_results_3ph: PowerFlowResults3Ph | None = None,
                 pf_results: PowerFlowResults | None = None,
                 engine: EngineType = EngineType.VeraGrid) -> None:
        """
        DynamicDriver class constructor
        :param grid: MultiCircuit instance
        :param options: EmtOptions instance (optional)
        :param pf_results_3ph: PowerFlowResults3ph
        :param pf_results: PowerFlowResults
        :param engine: EngineType (i.e., EngineType.VeraGrid) (optional)
        """

        DriverTemplate.__init__(self, grid=grid, engine=engine)

        self.grid = grid

        self.pf_results_3Ph: PowerFlowResults3Ph | None = pf_results_3ph

        self.pf_results: PowerFlowResults | None = pf_results

        self.options = options

        self.results: EmtResults | None = None
        self.problem: EmtProblemDae | None = None

        self.line_states = {}

    def run(self) -> None:
        """
        Main function to initialize and run the system simulation.

        This function sets up logging, starts the dynamic simulation, and
        logs the outcome. It handles and logs any exceptions raised during execution.
        :return:
        """
        # Run the dynamic simulation
        self.run_time_simulation()

    def run_time_simulation(self) -> None:
        """
        Performs the EMTP loop using the chosen method.
        :return:
        """
        # TODO: into the loop add " self.report_text('Time series at ' + str(self.grid.time_profile[t]) + '...')
        #                     self.report_progress2(it, len(time_indices)) "

        self.progress_signal.emit(0)

        # set emt events groups
        emt_events_groups = (self.grid.emt_events_groups
                             if self.grid.emt_events_groups is None
                             else self.grid.emt_events_groups)

        # if self.grid.emt_events_groups is None:
        #     emt_events_groups = EmtEventsGroup(name="simulation1")
        #     self.grid.add_emt_events_group(emt_events_groups)
        # else:
        #     emt_events_groups = self.grid.emt_events_groups

        emt_events_group_names: StrVec = np.array([elm.name for elm in emt_events_groups])
        emt_events_group_idtags: StrVec = np.array([str(elm.idtag) for elm in emt_events_groups])

        steps = int(np.ceil((self.options.simulation_time - 0) / self.options.time_step))
        t: Vec = np.arange(steps + 1) * self.options.time_step

        # initialize buses
        # for bus in self.grid.buses:
        #     get_bus_emt_template(self.grid, bus)

        # create the problem
        problem = build_emt_problem(
            grid=self.grid,
            options=self.options,
            pf_results=self.pf_results,
            pf_results_3ph=self.pf_results_3Ph,
            progress_signal=self.progress_signal,
        )
        self.problem = problem


        # create the results
        # The results container keeps the full declared event-group layout so
        # downstream code can preserve stable event-group identities. The extra
        # availability mask records which of those declared groups are actually
        # simulated in this run, which is the information the plot binder needs.
        has_event_group_results: np.ndarray = np.array([bool(elm.active) for elm in emt_events_groups], dtype=bool)
        self.results = EmtResults(
            time_array=pd.DatetimeIndex(pd.to_datetime(t * 1e9)),
            emt_events_group_names=emt_events_group_names,
            emt_events_group_idtags=emt_events_group_idtags,
            variables=self.problem.state_and_algebraic_vars(),
            diff_variables=self.problem.get_diff_vars(),
            uid2idx_vars=self.problem.uid2idx_vars,
            uid2idx_diff=self.problem.uid2idx_diff,
            vars_glob_name2uid=self.problem.vars_glob_name2uid,
            devices_vars_info=self.problem.get_device_vars_dict(),
            parameter_value_maps=[dict() for _ in range(len(emt_events_groups))],
            has_event_group_results=has_event_group_results,
        )

        newton_diag_config = NewtonDiagnosticsConfig(
            step_norm_explode=self.options.newton_step_norm_explode,
            dense_cond_warn=self.options.newton_dense_cond_warn,
            compute_dense_cond=self.options.newton_compute_dense_cond,
            dense_cond_max_n=self.options.newton_dense_cond_max_n,
            enable_fallback=self.options.newton_enable_fallback,
            enable_index1_check=self.options.newton_enable_index1_check,
            index1_max_block_n=self.options.newton_index1_max_block_n,
            index1_warn_pivot_ratio=self.options.newton_index1_warn_pivot_ratio,
            index1_fail_pivot_ratio=self.options.newton_index1_fail_pivot_ratio,
            enable_backtracking=self.options.newton_enable_backtracking,
            backtracking_beta=self.options.newton_backtracking_beta,
            backtracking_min_alpha=self.options.newton_backtracking_min_alpha,
            backtracking_max_iter=self.options.newton_backtracking_max_iter,
        )


        for group_idx, emt_events_group in enumerate(emt_events_groups):

            if emt_events_group.active:

                self.report_text("Simulating EMT event group " + emt_events_group.name)

                self.progress_signal.emit(11)

                self.report_text("Simulating EMT event group " + emt_events_group.name)
                problem.set_events_group(emt_events_group=emt_events_group)

                self.report_text(
                    f"Simulating EMT event group  {emt_events_group.name} with "
                    f"{self.options.integration_method.value}"
                )

                solver = build_emt_solver(
                    options=self.options,
                    problem=problem,
                    t0=0.0,
                    t_end=self.options.simulation_time,
                    h=self.options.time_step,
                    method=self.options.integration_method,
                    newton_diag_config=newton_diag_config,
                )

                boundary_updater = build_emt_boundary_updater(problem)
                # t, y, dy = solver.simulate(boundary_updater=boundary_updater)
                #uncomment when convergence and well initialized is reported
                t, y, dy, well_initialized, converged = solver.simulate(boundary_updater=boundary_updater)

                if converged and well_initialized:
                    print(f"Event group {emt_events_group} successfully simulated.")
                    self.report_text(
                        f"Event group {emt_events_group} successfully simulated.")
                else:
                    print(
                        f"Event group {emt_events_group} finished with EMT Newton failures "
                        f"(well_initialized={well_initialized}, converged={converged})."
                    )
                    self.report_text(
                        f"Event group {emt_events_group} finished with EMT Newton failures "
                        f"(well_initialized={well_initialized}, converged={converged})."
                    )

                print(f"results = {y}")
                print(f"converged ={converged}")
                print(f"well_initialized ={well_initialized}")

                # Persist the solver status in the shared results object so the
                # GUI post-processing stage reports the actual simulation
                # outcome instead of the default False placeholders.
                self.results.converged[group_idx] = converged
                self.results.well_initialized[group_idx] = well_initialized
                self.results.values[:, :, group_idx] = y
                self.results.diff_values[:, :, group_idx] = dy
                self.results.parameter_value_maps[group_idx] = _collect_emt_group_parameter_values(problem=problem)

                self.progress_signal.emit(90)

            else:
                self.report_text( emt_events_group.name + "skipped")

        self.progress_signal.emit(100)
