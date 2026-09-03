# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
import datetime

import numpy as np
import pandas as pd
from typing import Union, List
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import EngineType, SimulationTypes, TimeGrouping
from VeraGridEngine.Simulations.OPF.opf_options import OptimalPowerFlowOptions
from VeraGridEngine.Simulations.OPF.Formulations.linear_opf_ts import run_linear_opf_ts
from VeraGridEngine.Simulations.OPF.ac_opf_worker import run_nonlinear_opf
from VeraGridEngine.Simulations.NodalCapacity.nodal_capacity_options import NodalCapacityOptions
from VeraGridEngine.Simulations.NodalCapacity.nodal_capacity_ts_results import NodalCapacityTimeSeriesResults
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.Simulations.ContinuationPowerFlow.continuation_power_flow_driver import ContinuationPowerFlowDriver
from VeraGridEngine.Simulations.ContinuationPowerFlow.continuation_power_flow_options import (
    ContinuationPowerFlowOptions)
from VeraGridEngine.Simulations.ContinuationPowerFlow.continuation_power_flow_input import ContinuationPowerFlowInput
from VeraGridEngine.Simulations.driver_template import TimeSeriesDriverTemplate
from VeraGridEngine.Simulations.Clustering.clustering_results import ClusteringResults
from VeraGridEngine.basic_structures import IntVec, Vec, get_time_groups
from VeraGridEngine.enumerations import NodalCapacityMethod, CpfStopAt, CpfParametrization, OpfDispatchMode


class NodalCapacityTimeSeriesDriver(TimeSeriesDriverTemplate):
    __slots__ = (
        "options",
        "all_solved",
    )

    name = 'Nodal capacity time series'
    tpe = SimulationTypes.NodalCapacityTimeSeries_run

    def __init__(self,
                 grid: MultiCircuit,
                 options: Union[NodalCapacityOptions, None] = None,
                 time_indices: Union[IntVec, None] = None,
                 clustering_results: Union[ClusteringResults, None] = None,
                 engine: EngineType = EngineType.VeraGrid):
        """
        Initialize the nodal capacity time-series driver.

        :param grid: Multi-circuit model to simulate.
        :param options: Nodal capacity options.
        :param time_indices: Time indices to simulate.
        :param clustering_results: Optional clustering results.
        :param engine: Calculation engine to use.
        """
        TimeSeriesDriverTemplate.__init__(self,
                                          grid=grid,
                                          time_indices=time_indices,
                                          clustering_results=clustering_results,
                                          engine=engine)

        # Options to use
        self.options = options if options else NodalCapacityOptions()

        # find the number of time steps
        nt = len(self.time_indices) if self.time_indices is not None else 1

        # compose the time array
        time_array = (self.grid.time_profile[self.time_indices] if self.time_indices is not None
                      else [datetime.datetime.now()])

        # OPF results
        self.results: NodalCapacityTimeSeriesResults = NodalCapacityTimeSeriesResults(
            bus_names=self.grid.get_bus_names(),
            branch_names=self.grid.get_branch_names(add_hvdc=False, add_vsc=False, add_switch=True),
            load_names=self.grid.get_load_names(),
            generator_names=self.grid.get_generator_names(),
            battery_names=self.grid.get_battery_names(),
            shunt_like_names=self.grid.get_shunt_like_devices_names(),
            hvdc_names=self.grid.get_hvdc_names(),
            vsc_names=self.grid.get_vsc_names(),
            fuel_names=self.grid.get_fuel_names(),
            emission_names=self.grid.get_emission_names(),
            technology_names=self.grid.get_technology_names(),
            fluid_node_names=self.grid.get_fluid_node_names(),
            fluid_path_names=self.grid.get_fluid_path_names(),
            fluid_injection_names=self.grid.get_fluid_injection_names(),
            nt=nt,
            time_array=time_array,
            bus_types=np.ones(self.grid.get_bus_number(), dtype=int),
            clustering_results=clustering_results,
            capacity_nodes_idx=self.options.capacity_nodes_idx
        )

        self.all_solved = True

    @property
    def opf_options(self) -> OptimalPowerFlowOptions:
        """
        Return the embedded OPF options.

        :return: Optimal power flow options.
        """
        return self.options.opf_options

    @property
    def pf_options(self) -> PowerFlowOptions:
        """
        Return the embedded power-flow options.

        :return: Power flow options.
        """
        return self.options.opf_options.power_flow_options

    def get_steps(self):
        """
        Return the formatted time-step labels.

        :return: List of time labels.
        """
        return [l.strftime('%d-%m-%Y %H:%M') for l in pd.to_datetime(self.grid.time_profile)]

    def get_time_indices(self):
        """
        Return the effective time-index list and whether time series mode is active.

        :return: Tuple of ``(has_time_series, indices)``.
        """

        if self.time_indices is not None:
            has_ts = True
            t_indices: Union[List[None], IntVec] = self.time_indices
        else:
            has_ts = False
            t_indices: Union[List[None], IntVec] = [None]

        return has_ts, t_indices

    def assign_linear_results(self, result_indices: IntVec, opf_vars) -> None:
        """
        Copy linear OPF results into the driver results buffers.

        :param result_indices:
        :param opf_vars: Linear OPF variables to unpack.
        :return: ``None``.
        """
        self.results.Sbus[result_indices, :] = opf_vars.bus_vars.Pinj + 1j * 0.0
        self.results.voltage[result_indices, :] = opf_vars.bus_vars.Vm * np.exp(1j * opf_vars.bus_vars.Va)
        self.results.bus_shadow_prices[result_indices, :] = opf_vars.bus_vars.shadow_prices
        self.results.nodal_capacity[result_indices, :] = self.options.nodal_capacity_sign * opf_vars.nodal_capacity_vars.P

        self.results.load_shedding[result_indices, :] = opf_vars.load_vars.shedding

        self.results.battery_power[result_indices, :] = opf_vars.batt_vars.p
        self.results.battery_energy[result_indices, :] = opf_vars.batt_vars.e

        self.results.generator_power[result_indices, :] = opf_vars.gen_vars.p
        self.results.generator_shedding[result_indices, :] = opf_vars.gen_vars.shedding
        self.results.generator_cost[result_indices, :] = opf_vars.gen_vars.cost
        self.results.generator_producing[result_indices, :] = opf_vars.gen_vars.producing
        self.results.generator_starting_up[result_indices, :] = opf_vars.gen_vars.starting_up
        self.results.generator_shutting_down[result_indices, :] = opf_vars.gen_vars.shedding

        self.results.Sf[result_indices, :] = opf_vars.branch_vars.flows
        self.results.St[result_indices, :] = -opf_vars.branch_vars.flows
        self.results.overloads[result_indices, :] = (
            opf_vars.branch_vars.flow_slacks_pos - opf_vars.branch_vars.flow_slacks_neg
        )

        self.results.loading[result_indices, :] = opf_vars.branch_vars.loading
        self.results.tap_angle[result_indices, :] = opf_vars.branch_vars.tap_angles

        self.results.hvdc_Pf[result_indices, :] = opf_vars.hvdc_vars.flows
        self.results.hvdc_loading[result_indices, :] = opf_vars.hvdc_vars.loading

        self.results.fluid_node_current_level[result_indices, :] = opf_vars.fluid_node_vars.current_level
        self.results.fluid_node_flow_in[result_indices, :] = opf_vars.fluid_node_vars.flow_in
        self.results.fluid_node_flow_out[result_indices, :] = opf_vars.fluid_node_vars.flow_out
        self.results.fluid_node_p2x_flow[result_indices, :] = opf_vars.fluid_node_vars.p2x_flow
        self.results.fluid_node_spillage[result_indices, :] = opf_vars.fluid_node_vars.spillage
        self.results.fluid_path_flow[result_indices, :] = opf_vars.fluid_path_vars.flow
        self.results.fluid_injection_flow[result_indices, :] = opf_vars.fluid_inject_vars.flow

        self.results.system_fuel[result_indices, :] = opf_vars.sys_vars.system_fuel
        self.results.system_emissions[result_indices, :] = opf_vars.sys_vars.system_emissions
        self.results.system_energy_cost[result_indices] = opf_vars.sys_vars.system_unit_energy_cost

        self.results.converged[result_indices] = np.array([opf_vars.acceptable_solution] * opf_vars.nt)

    def linear_opf(self, remote=False, batteries_energy_0=None, fluid_level_0=None):
        """
        Run the linear nodal capacity OPF for the configured time range.

        :param remote: Whether the call comes from another driver.
        :param batteries_energy_0: Optional initial battery energies.
        :param fluid_level_0: Optional initial fluid levels.
        :return: Time-series nodal capacity results.
        """

        if not remote:
            self.report_progress(0.0)
            self.report_text('Formulating problem...')

        opf_vars, model = run_linear_opf_ts(grid=self.grid,
                                            time_indices=self.time_indices,
                                            dispatch_mode=OpfDispatchMode.NodalCapacity,
                                            solver_type=self.opf_options.mip_solver,
                                            zonal_grouping=self.opf_options.zonal_grouping,
                                            skip_generation_limits=self.opf_options.skip_generation_limits,
                                            consider_contingencies=self.opf_options.consider_contingencies,
                                            contingency_groups_used=self.opf_options.contingency_groups_used,
                                            ramp_constraints=self.opf_options.consider_ramps,
                                            quadratic_costs=self.opf_options.quadratic_costs,
                                            lodf_threshold=self.opf_options.lodf_tolerance,
                                            inter_aggregation_info=self.opf_options.inter_aggregation_info,
                                            energy_0=batteries_energy_0,
                                            fluid_level_0=fluid_level_0,
                                            nodal_capacity_sign=self.options.nodal_capacity_sign,
                                            capacity_nodes_idx=self.options.capacity_nodes_idx,
                                            logger=self.logger,
                                            progress_text=self.report_text,
                                            progress_func=self.report_progress,
                                            verbose=self.opf_options.verbose,
                                            robust=self.opf_options.robust,
                                            mip_framework=self.opf_options.mip_framework)
        self.assign_linear_results(result_indices=np.arange(opf_vars.nt), opf_vars=opf_vars)

        if not remote:
            self.report_progress(0.0)
            self.report_text('Running all in an external solver, this may take a while...')

        return self.results

    def run_linear_opf_indices(self, result_indices: IntVec, time_indices: IntVec,
                               energy_0: Vec, fluid_level_0: Vec):
        """
        Run the linear nodal capacity OPF for a chunk of indices.

        :param result_indices: Result-array slots to populate.
        :param time_indices: Circuit time indices to solve.
        :param energy_0: Initial battery energies for the chunk.
        :param fluid_level_0: Initial fluid levels for the chunk.
        :return: Linear model instance.
        """
        opf_vars, model = run_linear_opf_ts(grid=self.grid,
                                            time_indices=time_indices,
                                            dispatch_mode=OpfDispatchMode.NodalCapacity,
                                            solver_type=self.opf_options.mip_solver,
                                            zonal_grouping=self.opf_options.zonal_grouping,
                                            skip_generation_limits=self.opf_options.skip_generation_limits,
                                            consider_contingencies=self.opf_options.consider_contingencies,
                                            contingency_groups_used=self.opf_options.contingency_groups_used,
                                            ramp_constraints=self.opf_options.consider_ramps,
                                            quadratic_costs=self.opf_options.quadratic_costs,
                                            lodf_threshold=self.opf_options.lodf_tolerance,
                                            inter_aggregation_info=self.opf_options.inter_aggregation_info,
                                            energy_0=energy_0,
                                            fluid_level_0=fluid_level_0,
                                            nodal_capacity_sign=self.options.nodal_capacity_sign,
                                            capacity_nodes_idx=self.options.capacity_nodes_idx,
                                            logger=self.logger,
                                            progress_text=self.report_text,
                                            progress_func=self.report_progress,
                                            verbose=self.opf_options.verbose,
                                            robust=self.opf_options.robust,
                                            mip_framework=self.opf_options.mip_framework)

        self.assign_linear_results(result_indices=result_indices, opf_vars=opf_vars)
        return model

    def non_linear_opf(self, remote=False, batteries_energy_0=None):
        """
        Run the nonlinear nodal capacity OPF.

        :param remote: Whether the call comes from another driver.
        :param batteries_energy_0: Unused nonlinear battery seed.
        :return: Time-series nodal capacity results.
        """

        if not remote:
            self.report_progress(0.0)
            self.report_text('Formulating problem...')

        has_ts, t_indices = self.get_time_indices()

        self.report_progress(0.0)

        for it, t in enumerate(t_indices):

            if has_ts:
                self.report_text('Nonlinear OPF at ' + str(self.grid.time_profile[t]) + '...')
                self.report_progress2(it, len(self.time_indices))
            else:
                self.report_text('Nonlinear OPF at the snapshot...')
                self.report_progress2(it, 1)

            res = run_nonlinear_opf(grid=self.grid,
                                    opf_options=self.opf_options,
                                    t_idx=t,
                                    optimize_nodal_capacity=True,
                                    nodal_capacity_sign=self.options.nodal_capacity_sign,
                                    capacity_nodes_idx=self.options.capacity_nodes_idx,
                                    logger=self.logger)

            Sbase = self.grid.Sbase
            self.results.voltage[it, :] = res.V
            self.results.Sbus[it, :] = res.S * Sbase
            self.results.bus_shadow_prices[it, :] = res.lam_p
            self.results.nodal_capacity[it, :] = self.options.nodal_capacity_sign * res.nodal_capacity
            self.results.generator_power[it, :] = res.Pg * Sbase
            self.results.generator_cost[it, :] = res.Pcost

            self.results.Sf[it, :] = res.Sf * Sbase
            self.results.St[it, :] = res.St * Sbase
            self.results.overloads[it, :] = (res.sl_sf - res.sl_st) * Sbase
            self.results.loading[it, :] = res.loading
            self.results.tap_angle[it, :] = res.tap_phase

            self.results.hvdc_Pf[it, :] = res.hvdc_Pf
            self.results.hvdc_loading[it, :] = res.hvdc_loading
            self.results.converged[it] = res.converged

            if self.is_cancel():
                return self.results

        # Compute the emissions, fuel costs and energy used
        (self.results.system_fuel,
         self.results.system_emissions,
         self.results.system_energy_cost) = self.get_fuel_emissions_energy_calculations(
            gen_p=self.results.generator_power,
            gen_cost=self.results.generator_cost
        )

        if not remote:
            self.report_progress(0.0)
            self.report_text('Running all in an external solver, this may take a while...')

        return self.results

    def cpf(self, remote=False, batteries_energy_0=None):
        """
        Run continuation power flow for nodal capacity.

        :param remote: Whether the call comes from another driver.
        :param batteries_energy_0: Unused CPF battery seed.
        :return: Time-series nodal capacity results.
        """

        if not remote:
            self.report_progress(0.0)
            self.report_text('Formulating problem...')

        has_ts, t_indices = self.get_time_indices()

        # we need to initialize with a power flow solution
        pf_options = PowerFlowOptions()
        power_flow = PowerFlowDriver(grid=self.grid, options=pf_options)
        power_flow.run()

        # declare the CPF options
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

        # define the direcion of loading
        base_power = power_flow.results.Sbus / self.grid.Sbase
        target_power = base_power.copy()
        target_power[self.options.capacity_nodes_idx] *= 2.0 * self.options.nodal_capacity_sign

        # We compose the target direction
        vc_inputs = ContinuationPowerFlowInput(Sbase=base_power,
                                               Vbase=power_flow.results.voltage,
                                               Starget=target_power)

        # declare the CPF driver and run
        vc = ContinuationPowerFlowDriver(grid=self.grid,
                                         options=vc_options,
                                         inputs=vc_inputs,
                                         pf_options=pf_options)
        vc.run()

        self.report_progress(0.0)
        for it, t in enumerate(t_indices):

            # report progress
            if has_ts:
                self.report_text('Nonlinear OPF at ' + str(self.grid.time_profile[t]) + '...')
                self.report_progress2(it, len(self.time_indices))
            else:
                self.report_text('Nonlinear OPF at the snapshot...')
                self.report_progress2(it, 1)

            # run opf
            res = vc.run_at(t_idx=t)

            # set the results
            Sbase = self.grid.Sbase
            self.results.voltage[it, :] = res.voltages[-1, :]
            self.results.Sbus[it, :] = res.Sbus[-1, :] * Sbase
            # self.results.bus_shadow_prices[it, :] = res.lam_p
            # self.results.load_shedding = npa_res.load_shedding[0, :]
            # self.results.battery_power = npa_res.battery_p[0, :]
            # self.results.battery_energy = npa_res.battery_energy[0, :]
            # self.results.generator_power[it, :] = res.Pg * Sbase
            # self.results.generator_cost[it, :] = res.Pcost

            self.results.Sf[it, :] = res.Sf[-1, :] * Sbase
            self.results.St[it, :] = res.St[-1, :] * Sbase
            # self.results.overloads[it, :] = (res.sl_sf - res.sl_st) * Sbase
            self.results.loading[it, :] = res.loading[-1, :]
            # self.results.phase_shift[it, :] = res.tap_phase

            # self.results.hvdc_Pf[it, :] = res.hvdc_Pf
            # self.results.hvdc_loading[it, :] = res.hvdc_loading
            self.results.converged[it] = res.converged[-1]

            if self.is_cancel():
                return self.results

        if not remote:
            self.report_progress(0.0)
            self.report_text('Running all in an external solver, this may take a while...')

        return self.results

    def add_report(self, eps: float = 1e-6) -> None:
        """
        Append warnings to the logger from the computed results.

        :param eps: Numerical tolerance for reporting.
        :return: ``None``.
        """
        if self.progress_text:
            self.report_text("Creating report")

        nt = len(self.time_indices)
        for t, t_idx in enumerate(self.time_indices):

            self.report_progress2(t, nt)

            t_name = str(self.results.time_array[t])

            for gen_name, gen_shedding in zip(self.results.generator_names, self.results.generator_shedding[t, :]):
                if gen_shedding > eps:
                    self.logger.add_warning("Generation shedding {}".format(t_name),
                                            device=gen_name,
                                            value=gen_shedding,
                                            expected_value=0.0)

            for load_name, load_shedding in zip(self.results.load_names, self.results.load_shedding[t, :]):
                if load_shedding > eps:
                    self.logger.add_warning("Load shedding {}".format(t_name),
                                            device=load_name,
                                            value=load_shedding,
                                            expected_value=0.0)

            for fluid_node_name, fluid_node_spillage in zip(self.results.fluid_node_names,
                                                            self.results.fluid_node_spillage[t, :]):
                if fluid_node_spillage > eps:
                    self.logger.add_warning("Fluid node spillage {}".format(t_name),
                                            device=fluid_node_name,
                                            value=fluid_node_spillage,
                                            expected_value=0.0)

            for name, val in zip(self.results.branch_names, self.results.loading[t, :]):
                if val > (1.0 + eps):
                    self.logger.add_warning("Overload {}".format(t_name),
                                            device=name,
                                            value=val * 100,
                                            expected_value=100.0)

            va = np.angle(self.results.voltage[t, :])
            for i, bus in enumerate(self.grid.buses):
                if va[i] > bus.angle_max:
                    self.logger.add_warning("Overvoltage {}".format(t_name),
                                            device=bus.name,
                                            value=va[i],
                                            expected_value=bus.angle_max)
                elif va[i] < bus.angle_min:
                    self.logger.add_warning("Undervoltage {}".format(t_name),
                                            device=bus.name,
                                            value=va[i],
                                            expected_value=bus.angle_min)

    def linear_opf_by_groups(self) -> None:
        """
        Run the linear nodal capacity OPF by grouped chunks.

        :return: ``None``.
        """
        self.report_progress(0.0)
        self.report_text('Making groups...')

        groups = get_time_groups(t_array=self.grid.time_profile[self.time_indices],
                                 grouping=self.opf_options.time_grouping)

        n = len(groups)
        i = 1
        energy_0: Union[Vec, None] = None
        fluid_level_0: Union[Vec, None] = None

        while i < n and not self.is_cancel():
            start_ = groups[i - 1]
            end_ = groups[i]

            if i == n - 1:
                result_indices = np.arange(start_, end_ + 1)
            else:
                result_indices = np.arange(start_, end_)

            time_indices = self.time_indices[result_indices]

            msg = f"Group {i} -> {start_} : {end_} [{end_ - start_}]"
            if self.opf_options.verbose > 0:
                print(msg)

            self.report_text('Running OPF for the time group {0} '
                             'start {1} - end {2} in external solver...'.format(i, start_, end_))

            model = self.run_linear_opf_indices(result_indices=result_indices,
                                                time_indices=time_indices,
                                                energy_0=energy_0,
                                                fluid_level_0=fluid_level_0)

            energy_0 = self.results.battery_energy[result_indices[-1], :]
            fluid_level_0 = self.results.fluid_node_current_level[result_indices[-1], :]

            if self.opf_options.report_formulation:
                formulation = model.model_as_string()
                if self.results.report_text:
                    self.results.report_text += f"\n\n## {msg}\n\n{formulation}"
                else:
                    self.results.report_text = f"## {msg}\n\n{formulation}"

            self.report_progress2(i, len(groups))

            if self.is_cancel():
                return None

            i += 1

        return None

    def run(self):
        """
        Execute the configured nodal capacity study.

        :return: ``None``.
        """

        self.tic()
        self.report_text("Compiling and configuring...")

        if self.engine == EngineType.VeraGrid:

            if self.options.method == NodalCapacityMethod.LinearOptimization:
                if (self.opf_options.time_grouping == TimeGrouping.NoGrouping
                        or self.time_indices is None
                        or len(self.time_indices) == 0):
                    self.linear_opf()
                else:
                    self.linear_opf_by_groups()

            elif self.options.method == NodalCapacityMethod.NonlinearOptimization:
                self.non_linear_opf()

            elif self.options.method == NodalCapacityMethod.CPF:
                self.cpf()

        if self.opf_options.generate_report:
            self.add_report()

        self.toc()
