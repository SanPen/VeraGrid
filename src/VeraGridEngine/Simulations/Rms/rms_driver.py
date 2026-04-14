# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Utils.Symbolic import Var
from VeraGridEngine.Utils.Symbolic.block_solver import BlockSolver
from VeraGridEngine.Simulations.driver_template import DriverTemplate
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Simulations.Rms.rms_results import RmsResults
from VeraGridEngine.Utils.Symbolic.block import Block, DiffBlock
from VeraGridEngine.Simulations.Rms.problems.rms_problem import RmsProblem
from VeraGridEngine.Simulations.Rms.numerical.integration_methods import Trapezoid, BackEuler
from VeraGridEngine.Utils.Symbolic.block_solver_comb import DiffBlockSolver
from VeraGridEngine.enumerations import EngineType, SimulationTypes, DynamicIntegrationMethod
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowResults, PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.Simulations.Rms.initialization import initialize_rms


def check_if_diff_vars(system):
    if isinstance(system, DiffBlock):
        diff_vars = system.diff_vars
        if diff_vars:
            return diff_vars
        else:
            if system.children:
                for child in system.children:
                    diff_vars = check_if_diff_vars(child)
        return diff_vars
    else:
        return False


class RmsSimulationDriver(DriverTemplate):
    name = 'Rms Simulation'
    tpe = SimulationTypes.RmsDynamic_run

    """
    Dynamic wrapper to use with Qt
    """

    def __init__(self, grid: MultiCircuit,
                 options: RmsOptions,
                 pf_results: PowerFlowResults | None,
                 engine: EngineType = EngineType.VeraGrid):

        """
        DynamicDriver class constructor
        :param grid: MultiCircuit instance
        :param options: RmsOptions instance (optional)
        :param pf_results: PowerFlowResults
        :param engine: EngineType (i.e., EngineType.VeraGrid) (optional)
        """

        DriverTemplate.__init__(self, grid=grid, engine=engine)

        self.grid = grid

        self.pf_results: PowerFlowResults | None = pf_results

        self.options = options

        self.results = RmsResults(values=np.empty(0),
                                  time_array=pd.DatetimeIndex(pd.to_datetime(np.empty(0))),
                                  stat_vars=list(),
                                  algeb_vars=list(),
                                  uid2idx=dict(),
                                  vars_glob_name2uid=dict(),
                                  devices=[])

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
        self.tic()
        # Get integration method
        if self.options.integration_method == "trapezoid":
            integrator = "trapezoid"
        elif self.options.integration_method == "implicit euler":
            integrator = "implicit_euler"
        else:
            raise ValueError(f"integrator not implemented :( {self.options.integration_method}")

        # TODO: Check if there is a cleaner way to get all the devices in a list

        buses = [bus for bus in self.grid.get_buses()]
        branches = [branch for branch in self.grid.get_branches_iter()]
        injections = [injection for injection in self.grid.get_injection_devices_iter()]

        devices = buses + branches + injections

        params_mapping: Dict = dict()

        sim_time, ss, init_guess = initialize_rms(self.grid, self.pf_results, self.options.use_init_values)

        diff_vars = check_if_diff_vars(ss)

        if diff_vars:
            slv = DiffBlockSolver(ss, sim_time)

            params0 = slv.build_init_params_vector(params_mapping)
            x0 = slv.build_init_vars_vector_from_uid(init_guess)

            dx0 = np.zeros(len(slv._diff_vars))

            t, y = slv.simulate(
                t0=0,
                t_end=self.options.simulation_time,
                h=self.options.time_step,
                x0=x0,
                dx0=dx0,
                params0=params0,
                method="rk4",
                newton_tol = 1e-8,
                newton_max_iter = 1000,
                followed_vars = None,
                initialized = False,
                verbose = False,

            )

        else:
            slv = BlockSolver(ss, sim_time)

            params0 = slv.build_init_params_vector(params_mapping)
            x0 = slv.build_init_vars_vector_from_uid(init_guess)

            t, y = slv.simulate(
                t0=0,
                t_end=self.options.simulation_time,
                h=self.options.time_step,
                x0=x0,
                params0=params0,
                method="implicit_euler",

            )


        self.results = RmsResults(values=y,
                                  time_array=pd.DatetimeIndex(pd.to_datetime(t * 1e9)),
                                  stat_vars=slv._state_vars,
                                  algeb_vars=slv._algebraic_vars,
                                  uid2idx=slv.uid2idx_vars,
                                  vars_glob_name2uid=slv.v_glob_name2uid,
                                  devices=devices)

        self.toc()

