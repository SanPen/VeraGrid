# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
from typing import Union
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import EngineType, SimulationTypes
from VeraGridEngine.Simulations.NodalCapacity.nodal_capacity_options import NodalCapacityOptions
from VeraGridEngine.Simulations.NodalCapacity.nodal_capacity_results import NodalCapacityResults
from VeraGridEngine.Simulations.OPF.Formulations.linear_opf_ts import run_linear_opf_ts
from VeraGridEngine.Simulations.OPF.ac_opf_worker import run_nonlinear_opf
from VeraGridEngine.Simulations.ContinuationPowerFlow.continuation_power_flow_driver import ContinuationPowerFlowDriver
from VeraGridEngine.Simulations.ContinuationPowerFlow.continuation_power_flow_options import (
    ContinuationPowerFlowOptions)
from VeraGridEngine.Simulations.ContinuationPowerFlow.continuation_power_flow_input import (
    ContinuationPowerFlowInput)
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.driver_template import DriverTemplate
from VeraGridEngine.enumerations import NodalCapacityMethod, CpfStopAt, CpfParametrization, OpfDispatchMode


class NodalCapacityDriver(DriverTemplate):
    __slots__ = (
        "options",
        "all_solved",
    )

    name = 'Nodal capacity'
    tpe = SimulationTypes.NodalCapacity_run

    def __init__(self,
                 grid: MultiCircuit,
                 options: Union[NodalCapacityOptions, None] = None,
                 engine: EngineType = EngineType.VeraGrid):
        """

        :param grid:
        :param options:
        :param engine:
        """
        DriverTemplate.__init__(self,
                                grid=grid,
                                engine=engine, )

        self.options = options if options else NodalCapacityOptions()

        F, T = self.grid.get_branch_FT(add_vsc=False, add_hvdc=False, add_switch=True)
        F_hvdc, T_hvdc = self.grid.get_hvdc_FT()

        self.results: NodalCapacityResults = NodalCapacityResults(
            bus_names=self.grid.get_bus_names(),
            branch_names=self.grid.get_branch_names(add_hvdc=False, add_vsc=False, add_switch=True),
            load_names=self.grid.get_load_names(),
            generator_names=self.grid.get_generator_names(),
            shunt_like_names=self.grid.get_shunt_like_devices_names(),
            battery_names=self.grid.get_battery_names(),
            hvdc_names=self.grid.get_hvdc_names(),
            vsc_names=self.grid.get_vsc_names(),
            bus_types=np.ones(self.grid.get_bus_number(), dtype=int),
            area_names=self.grid.get_area_names(),
            fluid_node_names=self.grid.get_fluid_node_names(),
            fluid_path_names=self.grid.get_fluid_path_names(),
            fluid_inj_names=self.grid.get_fluid_injection_names(),
            F=F,
            T=T,
            F_hvdc=F_hvdc,
            T_hvdc=T_hvdc,
            bus_area_indices=self.grid.get_bus_area_indices(),
            capacity_nodes_idx=self.options.capacity_nodes_idx
        )

        self.all_solved = True

    @property
    def opf_options(self):
        return self.options.opf_options

    @property
    def pf_options(self) -> PowerFlowOptions:
        return self.options.opf_options.power_flow_options

    def linear_opf(self, remote: bool = False) -> NodalCapacityResults:
        """

        :param remote:
        :return:
        """
        if not remote:
            self.report_progress(0.0)
            self.report_text('Formulating problem...')
        opf_vars, model = run_linear_opf_ts(
            grid=self.grid,
            time_indices=None,
            dispatch_mode=OpfDispatchMode.NodalCapacity,
            solver_type=self.opf_options.mip_solver,
            zonal_grouping=self.opf_options.zonal_grouping,
            skip_generation_limits=self.opf_options.skip_generation_limits,
            consider_contingencies=self.opf_options.consider_contingencies,
            contingency_groups_used=self.grid.contingency_groups,
            ramp_constraints=self.opf_options.consider_ramps,
            quadratic_costs=self.opf_options.quadratic_costs,
            lodf_threshold=self.opf_options.lodf_tolerance,
            inter_aggregation_info=self.opf_options.inter_aggregation_info,
            energy_0=None,
            nodal_capacity_sign=self.options.nodal_capacity_sign,
            capacity_nodes_idx=self.options.capacity_nodes_idx,
            logger=self.logger,
            progress_text=self.report_text,
            progress_func=self.report_progress,
            verbose=self.opf_options.verbose,
            robust=self.opf_options.robust,
            mip_framework=self.opf_options.mip_framework
        )

        self.results.Sbus = opf_vars.bus_vars.Pinj[0, :] + 1j * 0.0
        self.results.voltage = np.exp(1j * opf_vars.bus_vars.Va[0, :])
        self.results.bus_shadow_prices = opf_vars.bus_vars.shadow_prices[0, :]
        self.results.nodal_capacity = self.options.nodal_capacity_sign * opf_vars.nodal_capacity_vars.P[0, :]

        self.results.load_power = opf_vars.load_vars.p[0, :]
        self.results.load_shedding = opf_vars.load_vars.shedding[0, :]
        self.results.load_shedding_cost = opf_vars.load_vars.shedding_cost[0, :]
        self.results.battery_power = opf_vars.batt_vars.p[0, :]

        self.results.generator_power = opf_vars.gen_vars.p[0, :]
        self.results.generator_shedding = opf_vars.gen_vars.shedding[0, :]

        self.results.Sf = opf_vars.branch_vars.flows[0, :]
        self.results.St = -opf_vars.branch_vars.flows[0, :]
        self.results.overloads = opf_vars.branch_vars.flow_slacks_pos[0, :] - opf_vars.branch_vars.flow_slacks_neg[0, :]
        self.results.loading = opf_vars.branch_vars.loading[0, :]
        self.results.tap_angle = opf_vars.branch_vars.tap_angles[0, :]
        self.results.losses = opf_vars.branch_vars.losses[0, :]

        self.results.hvdc_Pf = opf_vars.hvdc_vars.flows[0, :]
        self.results.hvdc_loading = opf_vars.hvdc_vars.loading[0, :]
        self.results.vsc_Pf = opf_vars.vsc_vars.flows[0, :]
        self.results.vsc_loading = opf_vars.vsc_vars.loading[0, :]

        self.results.fluid_node_current_level = opf_vars.fluid_node_vars.current_level[0, :]
        self.results.fluid_node_flow_in = opf_vars.fluid_node_vars.flow_in[0, :]
        self.results.fluid_node_flow_out = opf_vars.fluid_node_vars.flow_out[0, :]
        self.results.fluid_node_p2x_flow = opf_vars.fluid_node_vars.p2x_flow[0, :]
        self.results.fluid_node_spillage = opf_vars.fluid_node_vars.spillage[0, :]
        self.results.fluid_path_flow = opf_vars.fluid_path_vars.flow[0, :]
        self.results.fluid_injection_flow = opf_vars.fluid_inject_vars.flow[0, :]

        self.results.converged = opf_vars.acceptable_solution

        if self.opf_options.report_formulation:
            self.results.report_text = model.model_as_string()

        return self.results

    def non_linear_opf(self, remote: bool = False) -> NodalCapacityResults:
        """

        :param remote:
        :return:
        """
        if not remote:
            self.report_progress(0.0)
            self.report_text('Running non linear optimization...')

        res = run_nonlinear_opf(grid=self.grid,
                                opf_options=self.opf_options,
                                t_idx=None,
                                optimize_nodal_capacity=True,
                                nodal_capacity_sign=self.options.nodal_capacity_sign,
                                capacity_nodes_idx=self.options.capacity_nodes_idx,
                                logger=self.logger)
        nodal_capacity = self.options.nodal_capacity_sign * res.nodal_capacity

        Sbase = self.grid.Sbase
        self.results.voltage = res.V
        self.results.Sbus = res.S * Sbase
        self.results.bus_shadow_prices = res.lam_p
        self.results.nodal_capacity = nodal_capacity
        self.results.generator_power = res.Pg * Sbase
        self.results.generator_reactive_power = res.Qg * Sbase
        self.results.Sf = res.Sf * Sbase
        self.results.St = res.St * Sbase
        self.results.overloads = (res.sl_sf - res.sl_st) * Sbase
        self.results.loading = res.loading
        self.results.tap_angle = res.tap_phase
        self.results.hvdc_Pf = res.hvdc_Pf
        self.results.hvdc_loading = res.hvdc_loading
        self.results.converged = res.converged

        return self.results

    def cpf(self, remote: bool = False) -> NodalCapacityResults:
        """

        :param remote:
        :return:
        """
        if not remote:
            self.report_progress(0.0)
            self.report_text('Formulating problem...')

        pf_options = PowerFlowOptions()
        power_flow = PowerFlowDriver(grid=self.grid, options=pf_options)
        power_flow.run()

        vc_options = ContinuationPowerFlowOptions(step=0.001,
                                                  approximation_order=CpfParametrization.ArcLength,
                                                  adapt_step=True,
                                                  step_min=0.00001,
                                                  step_max=0.2,
                                                  error_tol=1e-3,
                                                  tol=1e-6,
                                                  max_it=20,
                                                  stop_at=CpfStopAt.Full,
                                                  verbose=0)

        base_power = power_flow.results.Sbus / self.grid.Sbase
        target_power = base_power.copy()
        target_power[self.options.capacity_nodes_idx] *= 2.0 * self.options.nodal_capacity_sign

        vc_inputs = ContinuationPowerFlowInput(Sbase=base_power,
                                               Vbase=power_flow.results.voltage,
                                               Starget=target_power)

        vc = ContinuationPowerFlowDriver(grid=self.grid,
                                         options=vc_options,
                                         inputs=vc_inputs,
                                         pf_options=pf_options)
        vc.run()
        res = vc.run_at(t_idx=None)

        Sbase = self.grid.Sbase
        self.results.voltage = res.voltages[-1, :]
        self.results.Sbus = res.Sbus[-1, :] * Sbase
        self.results.Sf = res.Sf[-1, :] * Sbase
        self.results.St = res.St[-1, :] * Sbase
        self.results.loading = res.loading[-1, :]
        self.results.converged = res.converged[-1]

        return self.results

    def add_report(self, eps: float = 1e-6) -> None:
        """

        :param eps:
        :return:
        """
        for gen_name, gen_shedding in zip(self.results.generator_names, self.results.generator_shedding):
            if gen_shedding > eps:
                self.logger.add_warning("Generation shedding",
                                        device=gen_name,
                                        value=gen_shedding,
                                        expected_value=0.0)

        for load_name, load_shedding in zip(self.results.load_names, self.results.load_shedding):
            if load_shedding > eps:
                self.logger.add_warning("Load shedding",
                                        device=load_name,
                                        value=load_shedding,
                                        expected_value=0.0)

        for fluid_node_name, fluid_node_spillage in zip(self.results.fluid_node_names,
                                                        self.results.fluid_node_spillage):
            if fluid_node_spillage > eps:
                self.logger.add_warning("Fluid node spillage",
                                        device=fluid_node_name,
                                        value=fluid_node_spillage,
                                        expected_value=0.0)

        for name, val in zip(self.results.branch_names, self.results.loading):
            if val > (1.0 + eps):
                self.logger.add_warning("Overload",
                                        device=name,
                                        value=val * 100,
                                        expected_value=100.0)

    def run(self):
        """

        :return:
        """
        self.tic()

        if self.engine == EngineType.VeraGrid:
            if self.options.method == NodalCapacityMethod.LinearOptimization:
                self.linear_opf()
            elif self.options.method == NodalCapacityMethod.NonlinearOptimization:
                self.non_linear_opf()
            elif self.options.method == NodalCapacityMethod.CPF:
                self.cpf()
            else:
                raise NotImplementedError(f"self.engine {self.engine} is not implemented")

        else:
            if self.options.method == NodalCapacityMethod.LinearOptimization:
                self.linear_opf()
            elif self.options.method == NodalCapacityMethod.NonlinearOptimization:
                self.non_linear_opf()
            elif self.options.method == NodalCapacityMethod.CPF:
                self.cpf()
            else:
                raise NotImplementedError(f"self.engine {self.engine} is not implemented")

        if self.opf_options.generate_report:
            self.add_report()

        self.toc()
