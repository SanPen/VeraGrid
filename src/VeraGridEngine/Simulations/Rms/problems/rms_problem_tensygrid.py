# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Dict, List
import time
import numpy as np
import pandas as pd

from VeraGridEngine.Devices import MultiCircuit
from VeraGridEngine.Simulations.driver_template import DummySignal
from VeraGridEngine.Utils.Symbolic.symbolic import (Var, Const, Expr, piecewise)
from VeraGridEngine.Utils.Symbolic.compiled_functions import SymbolicParamsVector, \
    SymbolicDerivative
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import VarPowerFlowRefferenceType, RmsInitializationMethod
from VeraGridEngine.basic_structures import Vec, ObjVec, BoolVec, Logger
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowResults
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Simulations.Rms.initialization import init_explicit, init_pseudo_transient
from VeraGridEngine.Simulations.Rms.problems.rms_problem_template import RmsProblemTemplate
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Utils.Symbolic.jit_compiler import RMSCompiler


def _tic():
    return time.perf_counter()


def _toc(t0):
    return time.perf_counter() - t0


def setP(P: ObjVec, P_used: BoolVec, k: int, val: object):
    """

    :param P:
    :param P_used:
    :param k:
    :param val:
    :return:
    """
    if not P_used[k]:
        P[k] = val
        P_used[k] = True
    else:
        P[k] += val


def setQ(Q: ObjVec, Q_used: BoolVec, k: int, val: object):
    """

    :param Q:
    :param Q_used:
    :param k:
    :param val:
    :return:
    """
    if not Q_used[k]:
        Q[k] = val
        Q_used[k] = True
    else:
        Q[k] += val


class RmsProblemTensygrid(RmsProblemTemplate):
    """
    DAE (Differential-Algebraic Equation) class to store and manage.

    Responsibilities:
        - Store state and algebraic variables (x, y)
        - Store Jacobian matrices
        - Store residual equations
        - Store sparsity patterns
    """
    VARS_NAME = "vars"
    VARIABLE_PARAMS_NAME = "vprms"
    CONSTANT_PARAMS_NAME = "cprms"
    DIFF_NAME = "diff"
    TIME_NAME = "glob_time"

    def __init__(self,
                 grid: MultiCircuit,
                 options: RmsOptions,
                 pf_results: PowerFlowResults | None,
                 progress_signal: DummySignal | None = None):
        """

        :param grid:
        :param options:
        :param pf_results:
        """
        super().__init__()

        self.logger = Logger()
        self.progress_signal = progress_signal
        self.grid: MultiCircuit = grid
        self.power_flow_results: PowerFlowResults = pf_results
        self.Sf = self.power_flow_results.Sf / self.grid.Sbase
        self.St = self.power_flow_results.St / self.grid.Sbase
        self.options: RmsOptions = options

        # this is the general init guess that will contain all the variables init value
        self.init_guess: Dict[int, float] = dict()
        self.sys_block: Block = Block(children=[], in_vars=[])

        self._algebraic_vars: List[Var] = list()
        self._algebraic_eqs: List[Expr] = list()
        self._state_vars: List[Var] = list()
        self._state_eqs: List[Expr] = list()
        self._diff_vars: List[Var] = list()
        self._variable_parameters: List[Var] = list()
        self._event_parameters_eqs0: List[Expr | Const] = list()
        self._event_parameters_eqs: List[Expr | Const] = list()
        self._constant_parameters: List[Var] = list()
        self._parameters_values: List[Const] = list()
        self._reformulated_vars: List[Var] = list()
        self._reformulated_lagvars: List[Var] = list()

        # --------------------------------------------------------------------------------------------------------------
        # Initialize the RMS problem
        # --------------------------------------------------------------------------------------------------------------

        ######################### Initialize containers#############################
        total_init_explicit_time: float = 0
        t0 = time.perf_counter()

        # dictionaries to store device-variable ifo
        self._vars_info: Dict[ALL_DEV_TYPES, List[Var]] = dict()
        self._vars_glob_name2uid: Dict[str, int] = dict()

        # dictionaries for compilation names
        self._compiler_names_dict: Dict[int, str] = dict()
        self._alias_names_dict: Dict[int, str] = dict()

        # dictionaries for variable position in the variables arrays
        self._uid2idx_vars: Dict[int, int] = dict()
        self._uid2idx_event_params: Dict[int, int] = dict()
        self._uid2idx_params: Dict[int, int] = dict()
        self._uid2idx_diff: Dict[int, int] = dict()
        self._uid2idx_t: Dict[int, int] = dict()

        # create time global time variable and add it to the compilation dict
        self._glob_time: Var = Var(self.TIME_NAME)
        self._compiler_names_dict[self._glob_time.uid] = self.TIME_NAME
        self._uid2idx_t[self._glob_time.uid] = 0

        # Dictionary of state and algebraic vars
        self.sys_vars: Dict[int, Var] = dict()

        # already computed grid power flow
        bus_dict = dict()

        # initialize balance equation arrays
        n = len(self.grid.buses)
        P: ObjVec = np.zeros(n, dtype=object)
        Q: ObjVec = np.zeros(n, dtype=object)
        P_used: BoolVec = np.zeros(n, dtype=bool)
        Q_used: BoolVec = np.zeros(n, dtype=bool)

        # general indexes for variables and parameters
        self._n_vars = 0
        self._n_params = 0
        self._n_event_params = 0
        self._n_diff = 0

        ######################################## Initialize devices ########################################

        # initialize buses
        for bus_num, elm in enumerate(self.grid.buses):
            # Todo: missing default initialization for the model
            bus_dict[elm] = bus_num

            # flatten model
            elm.rms_model.unify_blocks()
            mdl = (elm.rms_model)

            self.add_variables_to_compilation_dicts(elm, mdl)

            # add init values from powerflow to initial guess
            self.set_init_guess(mdl, VarPowerFlowRefferenceType.Vm, np.abs(self.power_flow_results.voltage[bus_num]))
            self.set_init_guess(mdl, VarPowerFlowRefferenceType.Va, np.angle(self.power_flow_results.voltage[bus_num]))

            # add model to system block
            self.sys_block.add(mdl)

        # initialize branches
        for branch_num, elm in enumerate(self.grid.get_branches_iter(add_vsc=True, add_hvdc=True, add_switch=True)):
            # Todo: missing default initialization for the model
            # flatten model
            elm.rms_model.unify_blocks()
            mdl = (elm.rms_model)

            self.add_variables_to_compilation_dicts(elm, mdl)

            # add init values from powerflow to initial guess
            self.set_init_guess(mdl, VarPowerFlowRefferenceType.Pf, self.Sf[branch_num].real)
            self.set_init_guess(mdl, VarPowerFlowRefferenceType.Qf, self.Sf[branch_num].imag)
            self.set_init_guess(mdl, VarPowerFlowRefferenceType.Pt, self.St[branch_num].real)
            self.set_init_guess(mdl, VarPowerFlowRefferenceType.Qt, self.St[branch_num].imag)

            # add model to system block
            self.sys_block.add(mdl)

            # add variable to conservation equations of the bus to which the element is connected
            f = bus_dict[elm.bus_from]
            t = bus_dict[elm.bus_to]

            setP(P, P_used, f, -mdl.E(VarPowerFlowRefferenceType.Pf))
            setP(P, P_used, t, -mdl.E(VarPowerFlowRefferenceType.Pt))
            setQ(Q, Q_used, f, -mdl.E(VarPowerFlowRefferenceType.Qf))
            setQ(Q, Q_used, t, -mdl.E(VarPowerFlowRefferenceType.Qt))

        # initialize injections

        bus_regions_dict = self.grid.get_injection_devices_grouped_by_bus()

        for bus, region in bus_regions_dict.items():
            bus_index = bus_dict[bus]
            for dev_type, dev_list in region.items():
                for elm in dev_list:
                    # flatten model
                    elm.rms_model.unify_blocks()
                    mdl = (elm.rms_model)

                    self.add_variables_to_compilation_dicts(elm, mdl)

                    # fill general init guess for known variables values
                    self.set_init_guess(mdl, VarPowerFlowRefferenceType.P,
                                        np.real(self.power_flow_results.Sbus[bus_index] / grid.Sbase))
                    self.set_init_guess(mdl, VarPowerFlowRefferenceType.Q,
                                        np.imag(self.power_flow_results.Sbus[bus_index] / grid.Sbase))

                    # add variable to conservation equations of the bus to which the element is connected
                    k = bus_dict[elm.bus]
                    setP(P, P_used, k, mdl.E(VarPowerFlowRefferenceType.P))
                    setQ(Q, Q_used, k, mdl.E(VarPowerFlowRefferenceType.Q))

                    # find init values for the variables of this model
                    if self.options.initialization_method == RmsInitializationMethod.Explicit:
                        init_explicit(mdl=mdl,
                                      sys_vars=self.sys_vars,
                                      variable_parameters=self._variable_parameters,
                                      event_parameters_eqs=self._event_parameters_eqs,
                                      constant_parameters=self._constant_parameters,
                                      init_guess=self.init_guess,
                                      uid2idx_vars=self.uid2idx_vars,
                                      uid2idx_params=self._uid2idx_params,
                                      uid2idx_event_params=self._uid2idx_event_params,
                                      compiler_names_dict=self._compiler_names_dict,
                                      alias_names_dict=self._alias_names_dict,
                                      VARIABLE_PARAMS_NAME=self.VARIABLE_PARAMS_NAME,
                                      TIME_NAME=self.TIME_NAME,
                                      VARS_NAME=self.VARS_NAME,
                                      DIFF_NAME=self.DIFF_NAME,
                                      CONSTANT_PARAMS_NAME=self.CONSTANT_PARAMS_NAME
                                      )
                    elif self.options.initialization_method == RmsInitializationMethod.PseudoTransient:
                        self._glob_time, sys_block_region, init_guess_region = init_pseudo_transient()
                    else:
                        raise ValueError("Not implemented initialization method")

                    self.sys_block.add(mdl)

        total_init_explicit_time += time.perf_counter() - t0
        print(f"\nTotal time explicit initialization: {total_init_explicit_time:.6f} seconds")
        if self.progress_signal is not None:
            self.progress_signal.emit(10)

        # add the nodal balance equations
        for i, elm in enumerate(self.grid.buses):
            mdl = (elm.rms_model)
            if len(mdl.algebraic_eqs) == 0:
                if not P_used[i] and not Q_used[i]:
                    self.logger.add_error("Isolated bus", value=i)
                else:
                    self._algebraic_eqs.append(P[i])
                    self._algebraic_eqs.append(Q[i])

        # self._variable_parameters: List[Var] = list()
        # self._event_parameters_eqs: List[Expr | Const] = list()
        # self._constant_parameters: List[Var] = list()
        # self._parameters_values: List[Const] = list()
        #
        # for b in self.sys_block.get_all_blocks():
        #
        #     for param, eq in b.event_dict.items():
        #         self._variable_parameters.append(param)
        #         self._event_parameters_eqs.append(eq)
        #     for param, constant in b.parameters.items():
        #         self._constant_parameters.append(param)
        #         self._parameters_values.append(constant)
        # Collect reformulated_vars (tensygrid-specific)
        for b in self.sys_block.get_all_blocks():
            for var in b.reformulated_vars:
                self._reformulated_vars.append(var)


        # We define the parameter dt and delta
        self._dt = Var(name='dt')
        self._delta = Var(name='delta')
        self._variable_parameters.append(self._dt)
        self._variable_parameters.append(self._delta)
        self._event_parameters_eqs.append(Const(1e-3))
        self._event_parameters_eqs.append(Const(1))

        # add these parameters, m is for variable parameters
        self._compiler_names_dict[self._dt.uid] = f"{self.VARIABLE_PARAMS_NAME}[{self._n_event_params}]"
        self._alias_names_dict[self._dt.uid] = f"{self.VARIABLE_PARAMS_NAME}_{self._n_event_params}"
        self._uid2idx_event_params[self._dt.uid] = self._n_event_params
        self._n_event_params += 1

        self._compiler_names_dict[self._delta.uid] = f"{self.VARIABLE_PARAMS_NAME}[{self._n_event_params}]"
        self._alias_names_dict[self._delta.uid] = f"{self.VARIABLE_PARAMS_NAME}_{self._n_event_params}"
        self._uid2idx_event_params[self._delta.uid] = self._n_event_params
        self._n_event_params += 1

        ##################### To be removed when order is preserved in the first part #############################

        self._state_algeb_vars = list(self.sys_vars.values())

        self._n_state = len(self._state_vars)
        self._n_alg = len(self._algebraic_vars)
        self._n_algebraic = len(self._algebraic_eqs)

        # self._compiler_names_dict: Dict[int, str] = dict()
        # self._alias_names_dict: Dict[int, str] = dict()
        self._uid2idx_vars: Dict[int, int] = dict()
        # self._uid2idx_event_params: Dict[int, int] = dict()
        # self._uid2idx_params: Dict[int, int] = dict()
        self._uid2idx_diff: Dict[int, int] = dict()
        self._uid2idx_t: Dict[int, int] = dict()

        i = 0
        for v in self._state_vars:
            self._compiler_names_dict[v.uid] = f"{self.VARS_NAME}[{i}]"
            self._alias_names_dict[v.uid] = f"{self.VARS_NAME}_{i}"
            self._uid2idx_vars[v.uid] = i
            i += 1

        for v in self._algebraic_vars:
            self._compiler_names_dict[v.uid] = f"{self.VARS_NAME}[{i}]"
            self._alias_names_dict[v.uid] = f"{self.VARS_NAME}_{i}"
            self._uid2idx_vars[v.uid] = i
            i += 1

        # for j, ep in enumerate(self._constant_parameters):
        #     self._compiler_names_dict[ep.uid] = f"{self.CONSTANT_PARAMS_NAME}[{j}]"
        #     self._alias_names_dict[ep.uid] = f"{self.CONSTANT_PARAMS_NAME}_{j}"
        #     self._uid2idx_params[ep.uid] = j
        
        for var in self._reformulated_vars:
            fixed_var = Var('ref_var' + str(i))
            self._reformulated_lagvars.append(fixed_var)
            self._event_parameters_eqs.append(Const(1))
            self._variable_parameters.append(fixed_var)
            self._compiler_names_dict[fixed_var.uid] = f"{self.VARIABLE_PARAMS_NAME}[{i}]"
            self._alias_names_dict[fixed_var.uid] = f"{self.VARIABLE_PARAMS_NAME}_{i}"
            self._uid2idx_event_params[fixed_var.uid] = i
            i += 1
        
        # Re-index variable parameters to ensure sequential indices after all additions
        for idx, ep in enumerate(self._variable_parameters):
            self._compiler_names_dict[ep.uid] = f"{self.VARIABLE_PARAMS_NAME}[{idx}]"
            self._alias_names_dict[ep.uid] = f"{self.VARIABLE_PARAMS_NAME}_{idx}"
            self._uid2idx_event_params[ep.uid] = idx

        for k, ep in enumerate(self._diff_vars):
            self._compiler_names_dict[ep.uid] = f"{self.DIFF_NAME}[{k}]"
            self._alias_names_dict[ep.uid] = f"{self.DIFF_NAME}_{k}"
            self._uid2idx_diff[ep.uid] = k

        self._compiler_names_dict[self._glob_time.uid] = self.TIME_NAME
        self._uid2idx_t[self._glob_time.uid] = 0

        for it, eq in enumerate(self._event_parameters_eqs):
            if isinstance(eq, Const) and eq.value is None:
                raise Exception(f' Event parameter {self._variable_parameters[it]} has None Value')


        # Substitute in algebraic eqs
        self._stability_eqs = list()

        # fill stability equations by putting algebraic equations equal zero
        for it, eq in enumerate(self._algebraic_eqs):
            for diff_var in self._diff_vars:
                eq = eq.subs({diff_var: Const(0)})
                eq = eq.simplify()
            self._stability_eqs.append(eq)

        # Store a copy of the original event parameters equations for later use with set_events_group
        self._event_parameters_eqs0 = self._event_parameters_eqs.copy()

        #We populate the reformulated vars
        for it, eq in enumerate(self._algebraic_eqs):
            for j, var in enumerate(self._reformulated_vars):
                is_diff = any(v.base_var is not None for v in eq.get_vars())
                if var in eq.get_vars() and is_diff:
                    var_lagged= self._reformulated_lagvars[j]
                    eq = eq.subs({var: 0.5*(var + var_lagged)})
                    eq = eq.simplify()
                    self._algebraic_eqs[it] = eq 
        for it, eq in enumerate(self._state_eqs):
            for j, var in enumerate(self._reformulated_vars):
                is_diff = any(v.base_var is not None for v in eq.get_vars())
                if var in eq.get_vars() and is_diff:
                    var_lagged= self._reformulated_lagvars[j]
                    eq = eq.subs({var: 0.5*(var + var_lagged)})
                    eq = eq.simplify()
                    self._state_eqs[it] = eq 

        # add events modifying values of event_parameters equations

        collect_events = {
            param: {"times": [], "values": []}
            for param in self._variable_parameters
        }

        for rms_evt in self.grid.rms_events:
            collect_events[rms_evt.parameter]["times"].append(rms_evt.time)
            collect_events[rms_evt.parameter]["values"].append(rms_evt.value)
            # TODO: implement the function in block: apply_event
        for param, events_info in collect_events.items():
            default_value = self._event_parameters_eqs[self._variable_parameters.index(param)]
            self._event_parameters_eqs[self._variable_parameters.index(param)] = piecewise(
                time_var=self._glob_time,
                t_events=np.array(events_info["times"]),
                new_values=np.array(events_info["values"]),
                default_value=default_value
            )

        # --------------------------------------------------------------------------------------------------------------
        # Compile RHS and Jacobian using JIT Compiler adaptation
        # --------------------------------------------------------------------------------------------------------------
        timings = dict()
        print("Compiling RMS using JIT Native Compiler...")

        t0 = _tic()
        self._derivative_fn = SymbolicDerivative(
            vars=self._state_algeb_vars,
            uid2idx_vars=self._uid2idx_vars,
            diff_vars=self._diff_vars,
            compiler_names_dict=self._compiler_names_dict
        )
        timings["SymbolicDerivative"] = _toc(t0)

        t0 = _tic()
        self._event_params_fn = SymbolicParamsVector(
            eqs=self._event_parameters_eqs,
            compiler_names_dict=self._compiler_names_dict,
            alias_names_dict=self._alias_names_dict,
            EVENT_PARAMS_NAME=self.VARIABLE_PARAMS_NAME,
            TIME_NAME=self.TIME_NAME,
        )
        timings["Event parameters"] = _toc(t0)

        t0 = _tic()
        rms_compiler = RMSCompiler(
            variables=self._state_algeb_vars,
            diff_vars=self._diff_vars,
            v_params=self._variable_parameters,
            c_params=self._constant_parameters,
            dt_var=self._dt,
            compiler_names_dict=self._compiler_names_dict
        )
        timings["Compiler Setup"] = _toc(t0)

        t0 = _tic()
        self._rhs_algeb_fn = rms_compiler.compile_rhs(self._algebraic_eqs, "rhs_algeb")
        timings["RHS algebraic"] = _toc(t0)

        if len(self._state_eqs) != 0:
            t0 = _tic()
            self._rhs_state_fn = rms_compiler.compile_rhs(self._state_eqs, "rhs_state")
            timings["RHS state"] = _toc(t0)

            t0 = _tic()
            self._j11_fn = rms_compiler.compile_sparse_jacobian(self._state_eqs, self._state_vars, "j11")
            timings["J11 (dF/dx)"] = _toc(t0)

            t0 = _tic()
            self._j12_fn = rms_compiler.compile_sparse_jacobian(self._state_eqs, self._algebraic_vars, "j12")
            timings["J12 (dF/dy)"] = _toc(t0)

            t0 = _tic()
            self._j21_fn = rms_compiler.compile_sparse_jacobian(self._algebraic_eqs, self._state_vars, "j21")
            timings["J21 (dG/dx)"] = _toc(t0)

            t0 = _tic()
            self._j22_fn = rms_compiler.compile_sparse_jacobian(self._algebraic_eqs, self._algebraic_vars, "j22")
            timings["J22 (dG/dy)"] = _toc(t0)

        else:
            t0 = _tic()
            self._j22_fn = rms_compiler.compile_sparse_jacobian(self._algebraic_eqs, self._algebraic_vars, "j22")
            timings["J22 only (no states)"] = _toc(t0)

        if options.verbose > 0:
            print(f"Model compiled with {self._n_vars} variables")
            print("\nCompilation timing summary:")
            for k, v in timings.items():
                print(f"  {k:30s}: {v:8.4f} s")
            print(f"\nTotal JIT compile time: {sum(timings.values()):.4f} s")

        variable_parameters_init = np.ones(self.get_variable_parameter_number())

        # TODO: think about this thing of calling twice here
        self._variable_parameters_values = self._event_params_fn(variable_parameters_init, 0.0)
        self._variable_parameters_values = self._event_params_fn(self._variable_parameters_values, 0.0)

        self._constant_params = np.array([const.value for const in self._parameters_values])

        if options.verbose > 0:
            print(f"\nTotal compile time: {sum(timings.values()):.4f} s")

    def add_variables_to_compilation_dicts(self, elm: ALL_DEV_TYPES, mdl: Block):
        """
        add variables and parameters info to the system block

        :param elm:
        :type elm: Union[VeraGridEngine.Devices.Substation.bus.Bus, VeraGridEngine.Devices.Injections.load.Load]
        :param mdl:
        :type mdl: VeraGridEngine.Utils.Symbolic.block.Block
        :return:
        :rtype: None
        """

        block_item: Block
        for block_item in mdl.get_all_blocks():
            # i is for variables
            v: Var
            for v in block_item.state_vars:
                self._compiler_names_dict[v.uid] = f"{self.VARS_NAME}[{self._n_vars}]"
                self._alias_names_dict[v.uid] = f"{self.VARS_NAME}_{self._n_vars}"
                self._uid2idx_vars[v.uid] = self._n_vars
                self._register_global_var_name(name_key=v.name + elm.name, uid=v.uid, block=block_item)
                self.add_device_var(dev=elm, var=v)
                self.sys_vars[v.uid] = v
                self._state_vars.append(v)
                self._n_vars += 1

            for v in block_item.algebraic_vars:
                self._compiler_names_dict[v.uid] = f"{self.VARS_NAME}[{self._n_vars}]"
                self._alias_names_dict[v.uid] = f"{self.VARS_NAME}_{self._n_vars}"
                self._uid2idx_vars[v.uid] = self._n_vars
                self._register_global_var_name(name_key=v.name + elm.name, uid=v.uid, block=block_item)
                self.add_device_var(dev=elm, var=v)
                self.sys_vars[v.uid] = v
                self._algebraic_vars.append(v)
                self._n_vars += 1

            # j is for parameters
            ep: Var
            for ep, const in block_item.parameters.items():
                self._compiler_names_dict[ep.uid] = f"{self.CONSTANT_PARAMS_NAME}[{self._n_params}]"
                self._alias_names_dict[ep.uid] = f"{self.CONSTANT_PARAMS_NAME}_{self._n_params}"
                self._uid2idx_params[ep.uid] = self._n_params
                self._constant_parameters.append(ep)
                self._parameters_values.append(const)
                self._n_params += 1

            # m is for variable parameters
            for ep, eq in block_item.event_dict.items():
                self._compiler_names_dict[ep.uid] = f"{self.VARIABLE_PARAMS_NAME}[{self._n_event_params}]"
                self._alias_names_dict[ep.uid] = f"{self.VARIABLE_PARAMS_NAME}_{self._n_event_params}"
                self._uid2idx_event_params[ep.uid] = self._n_event_params
                self._variable_parameters.append(ep)
                self._event_parameters_eqs.append(eq)
                self._n_event_params += 1

            # l is for differential vars
            for v in block_item.diff_vars:
                self._compiler_names_dict[v.uid] = f"{self.DIFF_NAME}[{self._n_diff}]"
                self._alias_names_dict[v.uid] = f"{self.DIFF_NAME}_{self._n_diff}"
                self._uid2idx_diff[v.uid] = self._n_diff
                self._register_global_var_name(name_key=v.name + elm.name, uid=v.uid, block=block_item)
                self.add_device_var(dev=elm, var=v)
                self._diff_vars.append(v)
                self._n_diff += 1

            self._state_eqs.extend(block_item.state_eqs)
            self._algebraic_eqs.extend(block_item.algebraic_eqs)

        if self.progress_signal is not None:
            self.progress_signal.emit(20)

    def set_init_guess(self, mdl: Block, reference_powerflow: VarPowerFlowRefferenceType, val: float):
        """
        add values from powerflow to initial guess

        :param mdl:
        :type mdl:
        :param reference_powerflow:
        :type reference_powerflow:
        :param val:
        :type val:
        :return:
        :rtype:
        """
        var = mdl.external_mapping[reference_powerflow]
        self.init_guess[var.uid] = val

    def get_init_guess_info(self) -> pd.DataFrame:
        """
        returns a df with uid, name, and initial value for the system variables
        :return:
        :rtype:
        """

        vars_names = list()
        for key, value in self.init_guess.items():
            var_name = self.sys_vars[key].name
            vars_names.append((key, var_name, value))

        return pd.DataFrame(data=vars_names, columns=["key", "var_name", "value"])

    def get_device_vars_dict(self) -> Dict[ALL_DEV_TYPES, List[Var]]:
        """

        :return:
        :rtype:
        """
        return self._vars_info

    def add_device_var(self, dev: ALL_DEV_TYPES, var: Var):
        """
        Associate a variable with a device
        :param dev: Device
        :param var: Variable
        """
        var_list = self._vars_info.get(dev, None)

        if var_list is None:
            self._vars_info[dev] = [var]
        else:
            var_list.append(var)

    def get_var_idx(self, v: Var) -> int:
        """

        :param v:
        :return:
        """
        return self._uid2idx_vars[v.uid]

    @property
    def vars_glob_name2uid(self):
        """

        :return:
        """
        return self._vars_glob_name2uid

    def _register_global_var_name(self, name_key: str, uid: int, block: Block | None = None) -> None:
        prev_uid = self._vars_glob_name2uid.get(name_key)
        if prev_uid is None or prev_uid == uid:
            self._vars_glob_name2uid[name_key] = uid
            return

        block_tag = ""
        if block is not None:
            block_tag = f"::{block.name}#{block.uid}"

        disambiguated_key = f"{name_key}{block_tag}"
        if disambiguated_key == name_key:
            disambiguated_key = f"{name_key} [{uid}]"

        if disambiguated_key in self._vars_glob_name2uid and self._vars_glob_name2uid[disambiguated_key] != uid:
            raise ValueError(
                f"Global variable name collision for '{name_key}' and fallback '{disambiguated_key}': "
                f"existing uid={self._vars_glob_name2uid[disambiguated_key]}, new uid={uid}."
            )
        self._vars_glob_name2uid[disambiguated_key] = uid

    @property
    def uid2idx_vars(self):
        """
        :return:
        """
        return self._uid2idx_vars

    @property
    def algebraic_vars(self):
        """
        :return:
        """
        return self._algebraic_vars

    @property
    def state_and_algebraic_vars(self) -> List[Var]:
        """
        :return:
        """
        variables = list()
        for lst in [self._state_vars, self._algebraic_vars]:
            for var in lst:
                variables.append(var)

        return variables

    @property
    def state_vars(self):
        """
        :return:
        """
        return self._state_vars

    def get_all_vars_number(self) -> int:
        return self._n_vars

    def get_diff_var_number(self) -> int:
        """
        Get the number of diff vars
        :return:
        """
        return len(self._diff_vars)

    def get_algebraic_var_number(self) -> int:
        return len(self._algebraic_vars)

    def get_states_number(self) -> int:
        return self._n_state

    def get_variable_parameter_number(self) -> int:
        return len(self._variable_parameters)

    def get_x0(self) -> Vec:
        """
        Helper function to build the initial vector
        :return: array matching with the mapping, matching the solver ordering
        """
        x = np.zeros(len(self._state_vars) + len(self._algebraic_vars))

        for uid, val in self.init_guess.items():
            i = self._uid2idx_vars[uid]
            x[i] = val
        return x

    def update_variable_params(self, t: float, x_snapshot: Vec | None = None):
        """
        Update the variable parameters
        :param t:
        :return:
        """
        self._variable_parameters_values = self._event_params_fn(self._variable_parameters_values, t)

    def update_variable_params_ts(self, x:Vec, t: float):
        """
        Update the variable parameters
        :param t:
        :return:
        """
        self._variable_parameters_values = self._event_params_fn(self._variable_parameters_values, t)
        for i, var in enumerate(self._reformulated_vars):
            lagged_var = self._reformulated_lagvars[i]
            lag_idx = self._uid2idx_event_params[lagged_var.uid]
            var_idx = self._uid2idx_vars[var.uid]
            self._variable_parameters_values[lag_idx] = x[var_idx]

    def get_dx(self, x: Vec, xn: Vec, dx: Vec, h: float) -> Vec:
        return self._derivative_fn(x, xn, dx, h)

    def rhs_state(self, x: Vec, dx: Vec) -> Vec:
        return self._rhs_state_fn(x, dx,
                                  self._variable_parameters_values,
                                  self._constant_params)

    def rhs_algebraic(self, x: Vec, dx: Vec) -> Vec:
        return self._rhs_algeb_fn(x, dx,
                                  self._variable_parameters_values,
                                  self._constant_params)

    def get_j11(self, x: Vec, dx: Vec, h: float):
        return self._j11_fn(x, dx,
                            self._variable_parameters_values,
                            self._constant_params,
                            h)

    def get_j12(self, x: Vec, dx: Vec, h: float):
        return self._j12_fn(x, dx,
                            self._variable_parameters_values,
                            self._constant_params,
                            h)

    def get_j21(self, x: Vec, dx: Vec, h: float):
        return self._j21_fn(x, dx,
                            self._variable_parameters_values,
                            self._constant_params,
                            h)

    def get_j22(self, x: Vec, dx: Vec, h: float):
        return self._j22_fn(x, dx,
                            self._variable_parameters_values,
                            self._constant_params,
                            h)

    def get_dt(self):
        return self._dt

    def get_dt_value(self):
        dt_value = self._variable_parameters_values[-2]
        return dt_value

    def set_events_group(self, rms_events_group: RmsEventsGroup):
        """
        Set the events group to use for this simulation.
        This filters events by group and recompiles the event parameters function.

        :param rms_events_group: The RmsEventsGroup to use
        """
        # Restore original event parameters equations
        self._event_parameters_eqs = self._event_parameters_eqs0.copy()

        # Collect events for this group only
        collect_events = {
            param: {"times": [], "values": []}
            for param in self._variable_parameters
        }

        # Filter events by group
        rms_evts = [evt for evt in self.grid.rms_events if evt.group.idtag == rms_events_group.idtag]
        for rms_evt in rms_evts:
            collect_events[rms_evt.parameter]["times"].append(rms_evt.time)
            collect_events[rms_evt.parameter]["values"].append(rms_evt.value)

        # Apply piecewise functions for events
        for param, events_info in collect_events.items():
            if events_info["times"]:
                default_value = self._event_parameters_eqs[self._variable_parameters.index(param)]
                self._event_parameters_eqs[self._variable_parameters.index(param)] = piecewise(
                    time_var=self._glob_time,
                    t_events=np.array(events_info["times"]),
                    new_values=np.array(events_info["values"]),
                    default_value=default_value
                )

        # Recompile the event parameters function
        self._event_params_fn = SymbolicParamsVector(
            eqs=self._event_parameters_eqs,
            compiler_names_dict=self._compiler_names_dict,
            alias_names_dict=self._alias_names_dict,
            EVENT_PARAMS_NAME=self.VARIABLE_PARAMS_NAME,
            TIME_NAME=self.TIME_NAME,
        )

        # Reinitialize variable parameters values
        variable_parameters_init = np.ones(self.get_variable_parameter_number())
        self._variable_parameters_values = self._event_params_fn(variable_parameters_init, 0.0)
        self._variable_parameters_values = self._event_params_fn(self._variable_parameters_values, 0.0)
