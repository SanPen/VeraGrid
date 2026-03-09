# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import pandas as pd

from VeraGridEngine import EmtSolverTypes
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.driver_template import DriverTemplate
from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.Simulations.EMT.emt_results import EmtResults
from VeraGridEngine.Simulations.EMT.problems.emt_problem_dae import EmtProblemDae
from VeraGridEngine.enumerations import EngineType, SimulationTypes
from VeraGridEngine.Simulations.PowerFlow.power_flow_results_3ph import PowerFlowResults3Ph
from VeraGridEngine.Simulations.EMT.solvers.jit_symbolic_solver import JitSymbolicSolver
from VeraGridEngine.Simulations.EMT.solvers.solver_AD import JitAdSolver
from VeraGridEngine.Simulations.EMT.solvers.StructuralVectorizedSolver import StructuralVectorizedSolver
from VeraGridEngine.enumerations import EngineType, SimulationTypes, DynamicIntegrationMethod
from VeraGridEngine.basic_structures import Logger


class EmtSimulationDriver(DriverTemplate):
    name = 'EMT Simulation'
    tpe = SimulationTypes.EmtDynamic_run

    """
    Dynamic wrapper to use with Qt
    """

    def __init__(self, grid: MultiCircuit,
                 options: EmtOptions,
                 pf_results: PowerFlowResults3Ph | None,
                 engine: EngineType = EngineType.VeraGrid):
        """
        DynamicDriver class constructor
        :param grid: MultiCircuit instance
        :param options: EmtOptions instance (optional)
        :param pf_results: PowerFlowResults3ph
        :param engine: EngineType (i.e., EngineType.VeraGrid) (optional)
        """

        DriverTemplate.__init__(self, grid=grid, engine=engine)

        self.solvers_dict = {EmtSolverTypes.Symbolic: JitSymbolicSolver,
                             EmtSolverTypes.Automatic: JitAdSolver,
                             EmtSolverTypes.StructuralAD: StructuralVectorizedSolver}

        self.grid = grid

        self.pf_results: PowerFlowResults3Ph | None = pf_results

        self.options = options

        self.results = EmtResults(values=np.empty(0),
                                  time_array=pd.DatetimeIndex(pd.to_datetime(np.empty(0))),
                                  uid2idx=dict(),
                                  vars_glob_name2uid=dict(),
                                  devices=[])

        self.line_states = {}

    def run(self):
        """
        Main function to initialize and run the system simulation.

        This function sets up logging, starts the dynamic simulation, and
        logs the outcome. It handles and logs any exceptions raised during execution.
        :return:
        """
        # Run the dynamic simulation
        self.report_progress(0.0)
        self.run_time_simulation()

    def run_time_simulation(self):
        """
        Performs the EMTP loop using the chosen method.
        :return:
        """
        # TODO: into the loop add " self.report_text('Time series at ' + str(self.grid.time_profile[t]) + '...')
        #                     self.report_progress2(it, len(time_indices)) "

        res = self.pf_results

        print(f"Converged: {res.converged}")
        print(res.get_bus_df())
        print(res.get_branch_df())

        # profiler = cProfile.Profile()
        # profiler.enable()

        problem = EmtProblemDae(grid=self.grid,
                                options=self.options,
                                pf_results=self.pf_results)

        solver = self.solvers_dict[self.options.solver](
            problem=problem,
            t0=0.0,
            t_end=self.options.simulation_time,
            h=self.options.time_step,
            method = self.options.integration_method
        )

        t, y = solver.simulate(boundary_update_fn = problem.emt_boundary_update)

        # profiler.disable()
        # stats = pstats.Stats(profiler).sort_stats('cumtime')
        # stats.print_stats(10)

        # TODO: reformulate EmtResults
        self.results = EmtResults(
            values=y,
            time_array=pd.DatetimeIndex(pd.to_datetime(t * 1e9)),
            uid2idx=problem.uid2idx_vars,
            vars_glob_name2uid=problem.vars_glob_name2uid,
        )