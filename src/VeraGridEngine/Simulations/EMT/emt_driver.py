# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import pandas as pd
from typing import Any, cast

from VeraGridEngine import EmtSolverTypes
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.driver_template import DriverTemplate
from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.Simulations.EMT.emt_results import EmtResults
from VeraGridEngine.Simulations.EMT.emt_problem_factory import build_emt_problem
from VeraGridEngine.Simulations.EMT.emt_solver_factory import build_emt_solver
from VeraGridEngine.Simulations.EMT.problems.emt_problem_dae import EmtProblemDae
from VeraGridEngine.Simulations.PowerFlow.power_flow_results_3ph import PowerFlowResults3Ph
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import PowerFlowResults
from VeraGridEngine.Simulations.EMT.solvers.jit_symbolic_solver import JitSymbolicSolver
from VeraGridEngine.Simulations.EMT.solvers.solver_AD import JitAdSolver
from VeraGridEngine.Simulations.EMT.solvers.StructuralVectorizedSolver import StructuralVectorizedSolver
from VeraGridEngine.Simulations.EMT.solvers.structural_compiled_solver import StructuralCompiledSolver
from VeraGridEngine.Utils.Symbolic.diagnostic import NewtonDiagnosticsConfig
from VeraGridEngine.IO.fmu.importer import build_emt_boundary_updater
from VeraGridEngine.basic_structures import Vec, StrVec

from VeraGridEngine.enumerations import EngineType, SimulationTypes


class EmtSimulationDriver(DriverTemplate):
    __slots__ = (
        "solvers_dict",
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
                 engine: EngineType = EngineType.VeraGrid):
        """
        DynamicDriver class constructor
        :param grid: MultiCircuit instance
        :param options: EmtOptions instance (optional)
        :param pf_results_3ph: PowerFlowResults3ph
        :param pf_results: PowerFlowResults
        :param engine: EngineType (i.e., EngineType.VeraGrid) (optional)
        """

        DriverTemplate.__init__(self, grid=grid, engine=engine)

        self.solvers_dict = {EmtSolverTypes.Symbolic: JitSymbolicSolver,
                             EmtSolverTypes.Automatic: JitAdSolver,
                             EmtSolverTypes.StructuralAD: StructuralVectorizedSolver,
                             EmtSolverTypes.StructuralCompiled: StructuralCompiledSolver
                             }

        self.grid = grid

        self.pf_results_3Ph: PowerFlowResults3Ph | None = pf_results_3ph

        self.pf_results: PowerFlowResults | None = pf_results

        self.options = options

        self.results: EmtResults | None = None
        self.problem: EmtProblemDae | None = None

        self.line_states = {}

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
        Performs the EMTP loop using the chosen method.
        :return:
        """
        # TODO: into the loop add " self.report_text('Time series at ' + str(self.grid.time_profile[t]) + '...')
        #                     self.report_progress2(it, len(time_indices)) "

        self.progress_signal.emit(0)

        emt_events_groups = (self.grid.emt_events_groups
                             if self.grid.emt_events_groups is None
                             else self.grid.emt_events_groups)

        emt_events_group_names: StrVec = np.array([elm.name for elm in emt_events_groups])

        steps = int(np.ceil((self.options.simulation_time - 0) / self.options.time_step))
        t: Vec = np.arange(steps + 1) * self.options.time_step

        problem = build_emt_problem(
            grid=self.grid,
            options=self.options,
            pf_results=self.pf_results,
            pf_results_3ph=self.pf_results_3Ph,
            progress_signal=self.progress_signal,
        )
        self.problem = problem

        self.results = EmtResults(
            time_array=pd.DatetimeIndex(pd.to_datetime(t * 1e9)),
            emt_events_group_names=emt_events_group_names,
            variables=problem.state_and_algebraic_vars,
            diff_variables=problem.diff_vars,
            uid2idx_vars=problem.uid2idx_vars,
            uid2idx_diff=problem.uid2idx_diff,
            vars_glob_name2uid=problem.vars_glob_name2uid,
            devices_vars_info=problem.get_device_vars_dict()
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

            self.report_text("Simulating EMT event group " + emt_events_group.name)

            self.progress_signal.emit(5)

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
            t, y, dy = solver.simulate(boundary_updater=boundary_updater)

            #TODO: add converged and well initialized to results?

            # self.results.converged[group_idx] = converged
            # self.results.well_initialized[group_idx] = well_initialized
            self.results.values[:, :, group_idx] = y
            self.results.diff_values[:, :, group_idx] = dy

            # if not well_initialized:
            #     self.logger.add_warning("Not well initialized", device=rms_events_group.name)
            #
            # if not converged:
            #     self.logger.add_warning("Not converged", device=rms_events_group.name)

            self.progress_signal.emit(90)

        self.progress_signal.emit(100)


