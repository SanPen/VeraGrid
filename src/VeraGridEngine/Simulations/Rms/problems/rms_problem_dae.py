# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Dict, List, Callable
import time
import numpy as np
import pandas as pd
import scipy.sparse as sp

from VeraGridEngine import ParamPowerFlowRefferenceType
from VeraGridEngine.Devices import MultiCircuit
from VeraGridEngine.Simulations.driver_template import DummySignal
from VeraGridEngine.Utils.Symbolic.symbolic import (Var, Const, Expr, piecewise)
from VeraGridEngine.Utils.Symbolic.compiled_functions import SymbolicParamsVector, SymbolicDerivative
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic_io import block_deep_copy
from VeraGridEngine.enumerations import VarPowerFlowRefferenceType, RmsInitializationMethod
from VeraGridEngine.basic_structures import Vec, ObjVec, BoolVec, Logger
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowResults
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
# from VeraGridEngine.Simulations.EMT.initialization_emt import init_explicit_common, build_rms_single_equation_compiler
from VeraGridEngine.Utils.Symbolic.explicit_initialization_symbolic import init_explicit_common, build_rms_single_equation_compiler
from VeraGridEngine.Simulations.Rms.problems.rms_problem_template import RmsProblemTemplate
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Utils.Symbolic.jit_compiler import RMSCompiler
from VeraGridEngine.Templates.Rms.bus_rms_template import initialize_bus_rms, get_bus_rms_algebraic_vars
from VeraGridEngine.IO.fmu.importer import (
    advance_rms_fmu_cs_devices,
    advance_rms_fmu_me_devices,
    close_rms_fmu_cs_devices,
    close_rms_fmu_me_devices,
    initialize_rms_fmu_cs_devices,
    initialize_rms_fmu_me_devices,
    register_rms_fmu_cs_device,
    register_rms_fmu_me_device,
)


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


class RmsProblemDae(RmsProblemTemplate):
    """
    DAE (Differential-Algebraic Equation) class to store and manage.

    Responsibilities:
        - Store state and algebraic variables (x, y)
        - Store Jacobian matrices
        - Store residual equations
        - Store sparsity patterns
    """
    VARS_NAME = "vrs"
    VARIABLE_PARAMS_NAME = "vprms"
    CONSTANT_PARAMS_NAME = "cprms"
    DIFF_NAME = "diff"
    TIME_NAME = "glob_time"

    def __init__(self,
                 grid: MultiCircuit,
                 options: RmsOptions,
                 pf_results: PowerFlowResults | None,
                 progress_signal: DummySignal | None = None,
                 progress_text: DummySignal | None = None, ):
        """

        :param grid:
        :param options:
        :param pf_results:
        """
        super().__init__(progress_signal=progress_signal,
                         progress_text=progress_text)

        self.logger = Logger()
        self.grid: MultiCircuit = grid
        self.power_flow_results: PowerFlowResults = pf_results
        self.Sf = self.power_flow_results.Sf / self.grid.Sbase
        self.St = self.power_flow_results.St / self.grid.Sbase
        self.options: RmsOptions = options

        # this is the general init guess that will contain all the variables init value
        self.init_guess:  Dict[int, float | int | complex | None] = dict()
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

        # function pointers
        self._derivative_fn: SymbolicDerivative | None = None
        self._event_params_fn: SymbolicParamsVector | None = None
        self._rhs_algeb_fn: Callable[[Vec, Vec, Vec, Vec], Vec] | None = None
        self._rhs_state_fn: Callable[[Vec, Vec, Vec, Vec], Vec] | None = None
        self._j11_fn: Callable[[Vec, Vec, Vec, Vec, float], sp.csc_matrix] | None = None
        self._j12_fn: Callable[[Vec, Vec, Vec, Vec, float], sp.csc_matrix] | None = None
        self._j21_fn: Callable[[Vec, Vec, Vec, Vec, float], sp.csc_matrix] | None = None
        self._j22_fn: Callable[[Vec, Vec, Vec, Vec, float], sp.csc_matrix] | None = None

        self._variable_parameters_values: Vec | None = None
        self._last_variable_parameters_values: Vec | None = None
        self._constant_params: Vec | None = None
        self._fmu_cs_adapters: List[object] = list()
        self._fmu_cs_initialized: bool = False
        self._fmu_me_adapters: List[object] = list()
        self._fmu_me_initialized: bool = False

        # --------------------------------------------------------------------------------------------------------------
        # Initialize the RMS problem
        # --------------------------------------------------------------------------------------------------------------

        ######################### Initialize containers#############################
        total_init_explicit_time: float = 0
        t0 = time.perf_counter()
        diff_init_guess_common: Dict[int, float | int | complex | None] = dict()

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
        bus_dict: Dict[Bus, int] = dict()
        for bus_num, elm in enumerate(self.grid.buses):
            # Todo: missing default initialization for the model
            bus_dict[elm] = bus_num

            # default initialization
            if elm.rms_model.empty():
                initialize_bus_rms(elm, self.grid.var_factory)
                # initialize_bus_rms, get_bus_rms_algebraic_vars

            self.add_variables_to_compilation_dicts(elm, elm.rms_model)

            # add init values from powerflow to initial guess
            if elm.is_dc:
                # DC bus: use Vdc (magnitude) - angle is not applicable for DC
                self.set_init_guess(elm.rms_model, VarPowerFlowRefferenceType.Vdc,
                                    float(np.abs(self.power_flow_results.voltage[bus_num])))
            else:
                # AC bus: use Vm and Va
                self.set_init_guess(elm.rms_model, VarPowerFlowRefferenceType.Vm,
                                    float(np.abs(self.power_flow_results.voltage[bus_num])))
                self.set_init_guess(elm.rms_model, VarPowerFlowRefferenceType.Va,
                                    float(np.angle(self.power_flow_results.voltage[bus_num])))

            # add model to system block
            self.sys_block.add(elm.rms_model)

        # initialize branches
        for branch_num, elm in enumerate(self.grid.get_branches_iter(add_vsc=False, add_hvdc=False, add_switch=True)):
            # Todo: missing default initialization for the model

            if elm.rms_model.empty():
                self.logger.add_error("No RMS model",
                                      device_class=elm.device_type.value,
                                      device=elm.name)
            else:
                elm.rms_model.unify_blocks()
                #Todo: change unify_blocks for recursivity across blocks

                # get parameters from api object
                elm.rms_model.parameters[
                    elm.rms_model.api_obj_mapping[ParamPowerFlowRefferenceType.g]] = Const(
                    float(elm.R / (elm.R ** 2 + elm.X ** 2)))
                elm.rms_model.parameters[
                    elm.rms_model.api_obj_mapping[ParamPowerFlowRefferenceType.b]] = Const(
                    float(-elm.X / (elm.R ** 2 + elm.X ** 2)))
                elm.rms_model.parameters[
                    elm.rms_model.api_obj_mapping[ParamPowerFlowRefferenceType.bsh]] = Const(elm.B)

                # get variables from bus
                if elm.bus_from.rms_model.empty():
                    initialize_bus_rms(elm.bus_from, self.grid.var_factory)
                if elm.bus_to.rms_model.empty():
                    initialize_bus_rms(elm.bus_to, self.grid.var_factory)

                Vmf, Vaf = get_bus_rms_algebraic_vars(elm.bus_from.rms_model)
                Vmt, Vat = get_bus_rms_algebraic_vars(elm.bus_to.rms_model)

                elm.rms_model.update_model(
                    elm.rms_model.external_mapping[VarPowerFlowRefferenceType.Vmf], Vmf)
                elm.rms_model.update_model(
                    elm.rms_model.external_mapping[VarPowerFlowRefferenceType.Vaf], Vaf)
                elm.rms_model.update_model(
                    elm.rms_model.external_mapping[VarPowerFlowRefferenceType.Vmt], Vmt)
                elm.rms_model.update_model(
                    elm.rms_model.external_mapping[VarPowerFlowRefferenceType.Vat], Vat)

                self.add_variables_to_compilation_dicts(elm, elm.rms_model)
                register_rms_fmu_cs_device(self, elm, elm.rms_model)
                register_rms_fmu_me_device(self, elm, elm.rms_model)

                # add init values from powerflow to initial guess
                self.set_init_guess(elm.rms_model, VarPowerFlowRefferenceType.Pf, self.Sf[branch_num].real)
                self.set_init_guess(elm.rms_model, VarPowerFlowRefferenceType.Qf, self.Sf[branch_num].imag)
                self.set_init_guess(elm.rms_model, VarPowerFlowRefferenceType.Pt, self.St[branch_num].real)
                self.set_init_guess(elm.rms_model, VarPowerFlowRefferenceType.Qt, self.St[branch_num].imag)

                # Run explicit initialization for branches to solve algebraic equations
                if isinstance(elm, Transformer2W):

                    if self.options.initialization_method == RmsInitializationMethod.Explicit:
                        params_array: np.ndarray = np.zeros(len(self._constant_parameters))
                        diff_sys_vars: Dict[int, Var] = {diff_var.uid: diff_var for diff_var in self._diff_vars}
                        rms_compiler_init = RMSCompiler(
                            variables=list(self.sys_vars.values()),
                            diff_vars=list(diff_sys_vars.values()),
                            v_params=self._variable_parameters,
                            c_params=self._constant_parameters,
                            dt_var=Var("dt"),
                            compiler_names_dict=self._compiler_names_dict,
                        )
                        compile_single_equation = build_rms_single_equation_compiler(rms_compiler_init)

                        for param, const in elm.rms_model.parameters.items():
                            params_array[self._uid2idx_params[param.uid]] = const.value

                        # OLD init_explicit path kept for reference
                        # init_explicit(
                        #     mdl=elm.rms_model,
                        #     sys_vars=self.sys_vars,
                        #     variable_parameters=self._variable_parameters,
                        #     event_parameters_eqs=self._event_parameters_eqs0,
                        #     constant_parameters=self._constant_parameters,
                        #     init_guess=self.init_guess,
                        #     uid2idx_vars=self.uid2idx_vars,
                        #     uid2idx_params=self._uid2idx_params,
                        #     uid2idx_event_params=self._uid2idx_event_params,
                        #     compiler_names_dict=self._compiler_names_dict,
                        #     alias_names_dict=self._alias_names_dict,
                        #     VARIABLE_PARAMS_NAME=self.VARIABLE_PARAMS_NAME,
                        #     TIME_NAME=self.TIME_NAME,
                        #     VARS_NAME=self.VARS_NAME,
                        #     DIFF_NAME=self.DIFF_NAME,
                        #     CONSTANT_PARAMS_NAME=self.CONSTANT_PARAMS_NAME
                        # )

                        # New init_explicit_common path
                        self.init_guess, diff_init_guess_common = init_explicit_common(
                            mdl=elm.rms_model,
                            sys_vars=self.sys_vars,
                            sys_diff_vars=diff_sys_vars,
                            variable_parameters=self._variable_parameters,
                            event_parameters_eqs=self._event_parameters_eqs0,
                            constant_parameters=self._constant_parameters,
                            init_guess=self.init_guess,
                            diff_init_guess=diff_init_guess_common,
                            uid2idx_vars=self.uid2idx_vars,
                            uid2idx_diff=self._uid2idx_diff,
                            uid2idx_params=self._uid2idx_params,
                            uid2idx_event_params=self._uid2idx_event_params,
                            params_array=params_array,
                            compile_single_equation=compile_single_equation,
                            verbose=bool(self.options.verbose > 0),
                        )

                # add model to system block
                self.sys_block.add(elm.rms_model)

                # add variable to conservation equations of the bus to which the element is connected
                f = bus_dict[elm.bus_from]
                t = bus_dict[elm.bus_to]

                setP(P, P_used, f, -elm.rms_model.E(VarPowerFlowRefferenceType.Pf))
                setP(P, P_used, t, -elm.rms_model.E(VarPowerFlowRefferenceType.Pt))
                setQ(Q, Q_used, f, -elm.rms_model.E(VarPowerFlowRefferenceType.Qf))
                setQ(Q, Q_used, t, -elm.rms_model.E(VarPowerFlowRefferenceType.Qt))

        # Populating VSCs init guess
        for i, elm in enumerate(self.grid.get_vsc()):
            if elm.rms_model.empty():
                self.logger.add_error("No RMS model",
                                      device_class=elm.device_type.value,
                                      device=elm.name)
            else:
                mdl = elm.rms_model

                # flatten model to collect all variables including those from child blocks
                # mdl.unify_blocks()

                # get parameters from api object
                elm.rms_model.parameters[elm.rms_model.api_obj_mapping[ParamPowerFlowRefferenceType.alpha1]] = Const(elm.alpha1)
                elm.rms_model.parameters[elm.rms_model.api_obj_mapping[ParamPowerFlowRefferenceType.alpha2]] = Const(elm.alpha2)
                elm.rms_model.parameters[elm.rms_model.api_obj_mapping[ParamPowerFlowRefferenceType.alpha3]] = Const(elm.alpha3)
                
                #We connect the vsc to its transformer
                if elm.bus_from.is_dc:
                    for branch_num, other_elm in enumerate(self.grid.get_branches_iter(add_vsc=False, add_hvdc=False, add_switch=True)):
                        if other_elm.bus_to.idtag == elm.bus_to.idtag:
                            mdl.connect([mdl.in_vars[0]], [other_elm.rms_model.out_vars[0]])
                        else:
                            _ = 0
                            #Do nothing

                St_vsc = self.power_flow_results.St_vsc / self.grid.Sbase
                Sf_vsc = (self.power_flow_results.Pfn_vsc[i] + self.power_flow_results.Pfp_vsc[i]) / self.grid.Sbase
                # fill init_guess

                self.add_variables_to_compilation_dicts(elm, mdl)
                self.set_init_guess(mdl, VarPowerFlowRefferenceType.Pf, Sf_vsc)
                self.set_init_guess(mdl, VarPowerFlowRefferenceType.Pt, St_vsc[i].real)
                self.set_init_guess(mdl, VarPowerFlowRefferenceType.Qt, St_vsc[i].imag)

                f = bus_dict[elm.bus_from]
                t = bus_dict[elm.bus_to]
                setP(P, P_used, f, -mdl.E(VarPowerFlowRefferenceType.Pf))
                setP(P, P_used, t, -mdl.E(VarPowerFlowRefferenceType.Pt))
                #setQ(Q, Q_used, t, -mdl.E(VarPowerFlowRefferenceType.Qt))
                self.sys_block.add(mdl)

        # Populating HVDC init guess (similar to VSCs)
        for i, elm in enumerate(self.grid.get_hvdc()):
            if elm.rms_model.empty():
                self.logger.add_error("No RMS model",
                                      device_class=elm.device_type.value,
                                      device=elm.name)
            else:
                mdl = elm.rms_model

                self.add_variables_to_compilation_dicts(elm, mdl)

                self.set_init_guess(mdl, VarPowerFlowRefferenceType.Pf_hvdc,
                                    self.power_flow_results.Pf_hvdc[i] / self.grid.Sbase)

                self.set_init_guess(mdl, VarPowerFlowRefferenceType.Pt_hvdc,
                                    self.power_flow_results.Pt_hvdc[i] / self.grid.Sbase)

                f = bus_dict[elm.bus_from]
                t = bus_dict[elm.bus_to]
                setP(P, P_used, f, -mdl.E(VarPowerFlowRefferenceType.Pf))
                setP(P, P_used, t, -mdl.E(VarPowerFlowRefferenceType.Pt))
                setQ(Q, Q_used, f, -mdl.E(VarPowerFlowRefferenceType.Qf))
                setQ(Q, Q_used, t, -mdl.E(VarPowerFlowRefferenceType.Qt))
                self.sys_block.add(mdl)

        # initialize injections

        for elm in grid.get_vsc():

            if elm.rms_model.empty():
                self.logger.add_error("No RMS model",
                                      device_class=elm.device_type.value,
                                      device=elm.name)
            else:

                # find init values for the variables of this model
                if self.options.initialization_method == RmsInitializationMethod.Explicit:
                    # common initialization to integrate

                   # create constant parameters array
                    params_array: np.ndarray = np.zeros(len(self._constant_parameters))  # array with the lenght of constant params
                    for param, const in elm.rms_model.parameters.items():
                        params_array[self._uid2idx_params[param.uid]] = const.value

                    diff_sys_vars: Dict[int, Var] = {diff_var.uid: diff_var for diff_var in self._diff_vars} # dictionary uid, var for diff_vars
                    rms_compiler_init = RMSCompiler(
                        variables=list(self.sys_vars.values()),
                        diff_vars=list(diff_sys_vars.values()),
                        v_params=self._variable_parameters,
                        c_params=self._constant_parameters,
                        dt_var=Var("dt"),
                        compiler_names_dict=self._compiler_names_dict,
                    )
                    compile_single_equation = build_rms_single_equation_compiler(rms_compiler_init) # function to compile one equation



                    # OLD init_explicit path kept for reference
                    # missing: uid2idx_diff, sys_diff_vars, diff_init_guess, params_array

                    # init_explicit(mdl=elm.rms_model,
                    #               sys_vars=self.sys_vars,
                    #               variable_parameters=self._variable_parameters,
                    #               event_parameters_eqs=self._event_parameters_eqs0,
                    #               constant_parameters=self._constant_parameters,
                    #               init_guess=self.init_guess,
                    #               uid2idx_vars=self.uid2idx_vars,
                    #               uid2idx_params=self._uid2idx_params,
                    #               uid2idx_event_params=self._uid2idx_event_params,
                    #               compiler_names_dict=self._compiler_names_dict,
                    #               alias_names_dict=self._alias_names_dict,
                    #               VARIABLE_PARAMS_NAME=self.VARIABLE_PARAMS_NAME,
                    #               TIME_NAME=self.TIME_NAME,
                    #               VARS_NAME=self.VARS_NAME,
                    #               DIFF_NAME=self.DIFF_NAME,
                    #               CONSTANT_PARAMS_NAME=self.CONSTANT_PARAMS_NAME
                    #               )

                    # New init_explicit_common path
                    self.init_guess, diff_init_guess_common = init_explicit_common(
                        mdl=elm.rms_model,
                        sys_vars=self.sys_vars,
                        sys_diff_vars=diff_sys_vars,
                        variable_parameters=self._variable_parameters,
                        event_parameters_eqs=self._event_parameters_eqs0,
                        constant_parameters=self._constant_parameters,
                        init_guess=self.init_guess,
                        diff_init_guess=diff_init_guess_common,
                        uid2idx_vars=self.uid2idx_vars,
                        uid2idx_diff=self._uid2idx_diff,
                        uid2idx_params=self._uid2idx_params,
                        uid2idx_event_params=self._uid2idx_event_params,
                        params_array=params_array,
                        compile_single_equation=compile_single_equation,
                        verbose=bool(self.options.verbose > 0),
                    )

                else:
                    raise ValueError("Not implemented initialization method")
                # add model to system block
                self.sys_block.add(elm.rms_model)

        for elm in grid.get_injection_devices_iter():

            if elm.rms_model.empty():
                self.logger.add_error("No RMS model",
                                      device_class=elm.device_type.value,
                                      device=elm.name)
            else:
                bus_index = bus_dict[elm.bus]

                # elm.rms_model.unify_blocks()

                # get variables from bus
                if elm.bus.rms_model.empty():
                    initialize_bus_rms(elm.bus, self.grid.var_factory)

                if not elm.bus.is_dc:
                    Vm, Va = get_bus_rms_algebraic_vars(elm.bus.rms_model)
                    if VarPowerFlowRefferenceType.Vm in elm.rms_model.external_mapping:
                        elm.rms_model.update_model(
                            elm.rms_model.external_mapping[VarPowerFlowRefferenceType.Vm], Vm)
                    if VarPowerFlowRefferenceType.Va in elm.rms_model.external_mapping:
                        elm.rms_model.update_model(
                            elm.rms_model.external_mapping[VarPowerFlowRefferenceType.Va], Va)
                else:
                    Vdc = elm.bus.rms_model.external_mapping[VarPowerFlowRefferenceType.Vdc]
                    if VarPowerFlowRefferenceType.Vdc in elm.rms_model.external_mapping:
                        elm.rms_model.update_model(
                            elm.rms_model.external_mapping[VarPowerFlowRefferenceType.Vdc], Vdc)

                self.add_variables_to_compilation_dicts(elm, elm.rms_model)
                register_rms_fmu_cs_device(self, elm, elm.rms_model)
                register_rms_fmu_me_device(self, elm, elm.rms_model)

                if elm.bus.is_dc:
                    self.set_init_guess(elm.rms_model, VarPowerFlowRefferenceType.P,
                                        np.real(self.power_flow_results.Sbus[bus_index] / grid.Sbase))
                else:
                    self.set_init_guess(elm.rms_model, VarPowerFlowRefferenceType.P,
                                        np.real(self.power_flow_results.Sbus[bus_index] / grid.Sbase))
                    self.set_init_guess(elm.rms_model, VarPowerFlowRefferenceType.Q,
                                        np.imag(self.power_flow_results.Sbus[bus_index] / grid.Sbase))

                k = bus_dict[elm.bus]
                if VarPowerFlowRefferenceType.P in elm.rms_model.external_mapping:
                    setP(P, P_used, k, elm.rms_model.E(VarPowerFlowRefferenceType.P))
                if VarPowerFlowRefferenceType.Q in elm.rms_model.external_mapping:
                    setQ(Q, Q_used, k, elm.rms_model.E(VarPowerFlowRefferenceType.Q))

                if self.options.initialization_method == RmsInitializationMethod.Explicit:

                    #Todo: add check to see if all the initialization equations are there, otherwise raise error
                    # if not elm.rms_model.check_valid_init_method():
                    #     init_custom(elm.rms_model, self.init_guess)

                    # else:
                    # for common init explicit to integrate
                    params_array: np.ndarray = np.zeros(len(self._constant_parameters))
                    diff_sys_vars: Dict[int, Var] = {diff_var.uid: diff_var for diff_var in self._diff_vars}
                    rms_compiler_init = RMSCompiler(
                        variables=list(self.sys_vars.values()),
                        diff_vars=list(diff_sys_vars.values()),
                        v_params=self._variable_parameters,
                        c_params=self._constant_parameters,
                        dt_var=Var("dt"),
                        compiler_names_dict=self._compiler_names_dict,
                    )
                    compile_single_equation = build_rms_single_equation_compiler(rms_compiler_init)

                    for param, const in elm.rms_model.parameters.items():
                        params_array[self._uid2idx_params[param.uid]] = const.value

                    # OLD init_explicit path kept for reference
                    # init_explicit(
                    #     mdl=elm.rms_model,
                    #     sys_vars=self.sys_vars,
                    #     variable_parameters=self._variable_parameters,
                    #     event_parameters_eqs=self._event_parameters_eqs0,
                    #     constant_parameters=self._constant_parameters,
                    #     init_guess=self.init_guess,
                    #     uid2idx_vars=self.uid2idx_vars,
                    #     uid2idx_params=self._uid2idx_params,
                    #     uid2idx_event_params=self._uid2idx_event_params,
                    #     compiler_names_dict=self._compiler_names_dict,
                    #     alias_names_dict=self._alias_names_dict,
                    #     VARIABLE_PARAMS_NAME=self.VARIABLE_PARAMS_NAME,
                    #     TIME_NAME=self.TIME_NAME,
                    #     VARS_NAME=self.VARS_NAME,
                    #     DIFF_NAME=self.DIFF_NAME,
                    #     CONSTANT_PARAMS_NAME=self.CONSTANT_PARAMS_NAME
                    # )

                    # New init_explicit_common path
                    self.init_guess, diff_init_guess_common = init_explicit_common(
                        mdl=elm.rms_model,
                        sys_vars=self.sys_vars,
                        sys_diff_vars=diff_sys_vars,
                        variable_parameters=self._variable_parameters,
                        event_parameters_eqs=self._event_parameters_eqs0,
                        constant_parameters=self._constant_parameters,
                        init_guess=self.init_guess,
                        diff_init_guess=diff_init_guess_common,
                        uid2idx_vars=self.uid2idx_vars,
                        uid2idx_diff=self._uid2idx_diff,
                        uid2idx_params=self._uid2idx_params,
                        uid2idx_event_params=self._uid2idx_event_params,
                        params_array=params_array,
                        compile_single_equation=compile_single_equation,
                        verbose=bool(self.options.verbose > 0),
                    )

                elif self.options.initialization_method == RmsInitializationMethod.PseudoTransient:
                    raise ValueError("Not implemented initialization method")

                # elif self.options.initialization_method == RmsInitializationMethod.CustomValues:
                #
                #     # Todo: add check to see if all the init values are there, otherwise raise error
                #     init_custom(mdl=elm.rms_model, init_guess=self.init_guess)

                # not implemented yet
                # elif self.options.initialization_method == RmsInitializationMethod.PseudoTransient:
                #     init_pseudo_transient(
                #         mdl=elm.rms_model,
                #         sys_vars=self.sys_vars,
                #         variable_parameters=self._variable_parameters,
                #         event_parameters_eqs=self._event_parameters_eqs0,
                #         constant_parameters=self._constant_parameters,
                #         init_guess=self.init_guess,
                #         uid2idx_vars=self._uid2idx_vars,
                #         uid2idx_params=self._uid2idx_params,
                #         uid2idx_event_params=self._uid2idx_event_params,
                #         compiler_names_dict=self._compiler_names_dict,
                #         alias_names_dict=self._alias_names_dict,
                #         VARIABLE_PARAMS_NAME=self.VARIABLE_PARAMS_NAME,
                #         TIME_NAME=self.TIME_NAME,
                #         VARS_NAME=self.VARS_NAME,
                #         DIFF_NAME=self.DIFF_NAME,
                #         CONSTANT_PARAMS_NAME=self.CONSTANT_PARAMS_NAME,
                #         dtau0=1e0,
                #         max_iter=1000,
                #         tol=1e-6
                #     )
                else:
                    raise ValueError("Not implemented initialization method")

                self.sys_block.add(elm.rms_model)

        total_init_explicit_time += time.perf_counter() - t0
        print(f"\nTotal time explicit initialization: {total_init_explicit_time:.6f} seconds")
        if self.progress_signal is not None:
            self.progress_signal.emit(10)

        # add the nodal balance equations
        ac_virtual_buses = [elm.bus_to.idtag for elm in grid.get_vsc()]
        for i, elm in enumerate(self.grid.buses):
            mdl = block_deep_copy(elm.rms_model, grid.var_factory)
            if len(mdl.algebraic_eqs) == 0:
                if not P_used[i] and not Q_used[i]:
                    self.logger.add_error("Isolated bus", value=i)
                else:
                    if elm.is_dc:
                        self._algebraic_eqs.append(P[i])
                    elif (elm.idtag in ac_virtual_buses):
                        self._algebraic_eqs.append(P[i])
                    else:
                        self._algebraic_eqs.append(Q[i])
                        self._algebraic_eqs.append(P[i])

        # We define the parameter dt and delta
        self._dt = Var(name='dt')
        self._delta = Var(name='delta')
        self._variable_parameters.append(self._dt)
        self._variable_parameters.append(self._delta)
        self._event_parameters_eqs0.append(Const(1e-3))
        self._event_parameters_eqs0.append(Const(1))

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

        self._uid2idx_vars: Dict[int, int] = dict()

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

        for k, ep in enumerate(self._diff_vars):
            self._compiler_names_dict[ep.uid] = f"{self.DIFF_NAME}[{k}]"
            self._alias_names_dict[ep.uid] = f"{self.DIFF_NAME}_{k}"
            self._uid2idx_diff[ep.uid] = k

        self._compiler_names_dict[self._glob_time.uid] = self.TIME_NAME
        self._alias_names_dict[self._glob_time.uid] = self.TIME_NAME
        self._uid2idx_t[self._glob_time.uid] = 0

        for it, eq in enumerate(self._event_parameters_eqs0):
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


    def set_events_group(self, rms_events_group: RmsEventsGroup):
        """
        add events modifying values of event_parameters equations
        :param rms_events_group:
        :return:
        """
        # create a copy for modification
        self._event_parameters_eqs = self._event_parameters_eqs0.copy()

        collect_events = {
            param: {"times": [], "values": []}
            for param in self._variable_parameters
        }

        rms_evts = [evt for evt in self.grid.rms_events if evt.group.idtag == rms_events_group.idtag]
        for rms_evt in rms_evts:
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
        # print("Compiling RMS using JIT Native Compiler...")
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

        if self.options.verbose > 0:
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

        if self.options.verbose > 0:
            print(f"\nTotal compile time: {sum(timings.values()):.4f} s")

        # we mark the problem as ready for simulation
        self.set_initialize_flag()
    def add_variables_to_compilation_dicts(self, elm: ALL_DEV_TYPES, mdl: Block):

        self.add_block_variables_to_compilation_dicts(elm, mdl)
        for child in mdl.children:
            self.add_variables_to_compilation_dicts(elm, child)


    def add_block_variables_to_compilation_dicts(self, elm: ALL_DEV_TYPES, mdl: Block):
        """
        add variables and parameters info to the system block

        :param elm:
        :type elm: Union[VeraGridEngine.Devices.Substation.bus.Bus, VeraGridEngine.Devices.Injections.load.Load]
        :param mdl:
        :type mdl: VeraGridEngine.Utils.Symbolic.block.Block
        :return:
        :rtype: None
        """

        # i is for variables
        for v in mdl.state_vars:
            if v.uid in self._uid2idx_vars:
                raise ValueError(f"State variable '{v.name}' (uid={v.uid}) is already registered in the system. "
                                 f"Previous device may have created a duplicate variable.")

            self._compiler_names_dict[v.uid] = f"{self.VARS_NAME}[{self._n_vars}]"
            self._alias_names_dict[v.uid] = f"{self.VARS_NAME}_{self._n_vars}"
            self._uid2idx_vars[v.uid] = self._n_vars
            self._vars_glob_name2uid[v.name + elm.name] = v.uid
            self.add_device_var(dev=elm, var=v)
            self.sys_vars[v.uid] = v
            self._state_vars.append(v)
            self._n_vars += 1

        for v in mdl.algebraic_vars:
            if v.uid in self._uid2idx_vars:
                raise ValueError(f"Algebraic variable '{v.name}' (uid={v.uid}) is already registered in the system. "
                                 f"Previous device may have created a duplicate variable.")
            self._compiler_names_dict[v.uid] = f"{self.VARS_NAME}[{self._n_vars}]"
            self._alias_names_dict[v.uid] = f"{self.VARS_NAME}_{self._n_vars}"
            self._uid2idx_vars[v.uid] = self._n_vars
            self._vars_glob_name2uid[v.name + elm.name] = v.uid
            self.add_device_var(dev=elm, var=v)
            self.sys_vars[v.uid] = v
            self._algebraic_vars.append(v)
            self._n_vars += 1

        # j is for parameters
        for ep, const in mdl.parameters.items():
            if ep.uid in self._uid2idx_params:
                raise ValueError(f"Parameter '{ep.name}' (uid={ep.uid}) is already registered in the system. "
                                 f"Previous device may have created a duplicate parameter.")
            self._compiler_names_dict[ep.uid] = f"{self.CONSTANT_PARAMS_NAME}[{self._n_params}]"
            self._alias_names_dict[ep.uid] = f"{self.CONSTANT_PARAMS_NAME}_{self._n_params}"
            self._uid2idx_params[ep.uid] = self._n_params
            self._constant_parameters.append(ep)
            self._parameters_values.append(const)
            self._n_params += 1

        # m is for variable parameters
        for ep, eq in mdl.event_dict.items():
            if ep.uid in self._uid2idx_event_params:
                raise ValueError(f"Event parameter '{ep.name}' (uid={ep.uid}) is already registered in the system. "
                                 f"Previous device may have created a duplicate event parameter.")
            self._compiler_names_dict[ep.uid] = f"{self.VARIABLE_PARAMS_NAME}[{self._n_event_params}]"
            self._alias_names_dict[ep.uid] = f"{self.VARIABLE_PARAMS_NAME}_{self._n_event_params}"
            self._uid2idx_event_params[ep.uid] = self._n_event_params
            self._variable_parameters.append(ep)
            self._event_parameters_eqs0.append(eq)
            self._n_event_params += 1

        # l is for differential vars
        for v in mdl.diff_vars:
            if v.uid in self._uid2idx_diff:
                raise ValueError(f"Differential variable '{v.name}' (uid={v.uid}) is already registered in the system. "
                                 f"Previous device may have created a duplicate differential variable.")
            self._compiler_names_dict[v.uid] = f"{self.DIFF_NAME}[{self._n_diff}]"
            self._alias_names_dict[v.uid] = f"{self.DIFF_NAME}_{self._n_diff}"
            self._uid2idx_diff[v.uid] = self._n_diff
            self._vars_glob_name2uid[v.name + elm.name] = v.uid
            self.add_device_var(dev=elm, var=v)
            self._diff_vars.append(v)
            self._n_diff += 1

        self._state_eqs.extend(mdl.state_eqs)
        self._algebraic_eqs.extend(mdl.algebraic_eqs)

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
        if reference_powerflow in mdl.external_mapping:
            var = mdl.external_mapping[reference_powerflow]
            self.init_guess[var.uid] = val
            print(f"DEBUG: set_init_guess {reference_powerflow.value} = {val} for var {var.name} (uid={var.uid})")
        else:
            print(
                f"DEBUG: set_init_guess {reference_powerflow.value} NOT FOUND in external_mapping. Available: {[k.value for k in mdl.external_mapping.keys()]}")

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

    @property
    def uid2idx_vars(self):
        """
        :return:
        """
        return self._uid2idx_vars

    @property
    def get_algebraic_vars(self):
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
    def get_state_vars(self):
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

    def update_variable_params(self, t: float):
        """
        Update the variable parameters
        :param t:
        :return:
        """
        if self._event_params_fn is None:
            raise ValueError("_event_params_fn is None")

        self._variable_parameters_values = self._event_params_fn(self._variable_parameters_values, t)

    def initialize_fmu_cs_devices(self, x_snapshot: Vec, t: float = 0.0) -> None:
        """
        Initialize imported FMU Co-Simulation devices before the RMS time loop starts.

        :param x_snapshot: Initial accepted state vector.
        :param t: Initial simulation time.
        :return: None.
        """

        if len(self._fmu_cs_adapters) > 0:
            initialize_rms_fmu_cs_devices(problem=self, x_snapshot=x_snapshot, time_value=t)
        else:
            self._fmu_cs_initialized = True

    def advance_fmu_cs_devices(self, t: float, x_snapshot: Vec, h: float) -> None:
        """
        Advance imported FMU Co-Simulation devices for one RMS communication step.

        :param t: Current simulation time.
        :param x_snapshot: Current accepted state vector.
        :param h: RMS communication step.
        :return: None.
        """

        if len(self._fmu_cs_adapters) > 0:
            advance_rms_fmu_cs_devices(problem=self, time_value=t, x_snapshot=x_snapshot, step_size=h)
        else:
            pass

    def close_fmu_cs_devices(self) -> None:
        """
        Release imported FMU Co-Simulation devices after the RMS simulation ends.

        :return: None.
        """

        if len(self._fmu_cs_adapters) > 0:
            close_rms_fmu_cs_devices(self)
        else:
            pass

    def initialize_fmu_me_devices(self, x_snapshot: Vec, t: float = 0.0) -> None:
        """
        Initialize imported FMU Model Exchange devices before the RMS time loop starts.

        :param x_snapshot: Initial accepted state vector.
        :param t: Initial simulation time.
        :return: None.
        """

        if len(self._fmu_me_adapters) > 0:
            initialize_rms_fmu_me_devices(problem=self, x_snapshot=x_snapshot, time_value=t)
        else:
            self._fmu_me_initialized = True

    def advance_fmu_me_devices(self, t: float, x_snapshot: Vec, h: float) -> None:
        """
        Advance imported FMU Model Exchange devices for one RMS communication step.

        :param t: Current simulation time.
        :param x_snapshot: Current accepted state vector.
        :param h: RMS communication step.
        :return: None.
        """

        if len(self._fmu_me_adapters) > 0:
            advance_rms_fmu_me_devices(problem=self, time_value=t, x_snapshot=x_snapshot, step_size=h)
        else:
            pass

    def close_fmu_me_devices(self) -> None:
        """
        Release imported FMU Model Exchange devices after the RMS simulation ends.

        :return: None.
        """

        if len(self._fmu_me_adapters) > 0:
            close_rms_fmu_me_devices(self)
        else:
            pass

    def get_dx(self, x: Vec, xn: Vec, dx: Vec, h: float) -> Vec:

        if self._derivative_fn is None:
            raise ValueError("_derivative_fn is None")

        return self._derivative_fn(x, xn, dx, h)

    def rhs_state(self, x: Vec, dx: Vec) -> Vec:

        if self._rhs_state_fn is None:
            raise ValueError("_rhs_state_fn is None")

        return self._rhs_state_fn(x, dx,
                                  self._variable_parameters_values,
                                  self._constant_params)

    def rhs_algebraic(self, x: Vec, dx: Vec) -> Vec:
        if self._rhs_algeb_fn is None:
            raise ValueError("_rhs_algeb_fn is None")

        return self._rhs_algeb_fn(x, dx,
                                  self._variable_parameters_values,
                                  self._constant_params)

    def get_j11(self, x: Vec, dx: Vec, h: float):

        if self._j11_fn is None:
            raise ValueError("_j11_fn is None")

        return self._j11_fn(x, dx,
                            self._variable_parameters_values,
                            self._constant_params,
                            h)

    def get_j12(self, x: Vec, dx: Vec, h: float):

        if self._j12_fn is None:
            raise ValueError("_j12_fn is None")

        return self._j12_fn(x, dx,
                            self._variable_parameters_values,
                            self._constant_params,
                            h)

    def get_j21(self, x: Vec, dx: Vec, h: float):

        if self._j21_fn is None:
            raise ValueError("_j21_fn is None")

        return self._j21_fn(x, dx,
                            self._variable_parameters_values,
                            self._constant_params,
                            h)

    def get_j22(self, x: Vec, dx: Vec, h: float):

        if self._j22_fn is None:
            raise ValueError("_j22_fn is None")

        return self._j22_fn(x, dx,
                            self._variable_parameters_values,
                            self._constant_params,
                            h)

    def get_dt(self):
        return self._dt

    def get_dt_value(self):
        dt_value = self._variable_parameters_values[-2]
        return dt_value
