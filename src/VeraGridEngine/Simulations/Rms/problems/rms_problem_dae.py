# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Dict, List, Callable, Any, Tuple, Set, Optional
import time
import numpy as np
import pandas as pd
import scipy.sparse as sp

from VeraGridEngine.enumerations import ParamPowerFlowRefferenceType
from VeraGridEngine.Devices import MultiCircuit
from VeraGridEngine.Simulations.driver_template import DummySignal
from VeraGridEngine.Utils.Symbolic.symbolic import (Var, Const, Expr, piecewise, get_expression_vars)
from VeraGridEngine.Utils.Symbolic.compiled_functions import SymbolicParamsVector, SymbolicDerivative
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic_io import block_deep_copy
from VeraGridEngine.enumerations import VarPowerFlowRefferenceType, RmsInitializationMethod
from VeraGridEngine.basic_structures import Vec, ObjVec, BoolVec, Logger
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowResults
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Simulations.Rms.initialization_rms import run_rms_native_initialization
from VeraGridEngine.Utils.Symbolic.explicit_initialization_symbolic import (init_explicit_common,
    build_rms_single_equation_compiler)
from VeraGridEngine.Simulations.Rms.problems.rms_problem_template import RmsProblemTemplate
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Utils.Symbolic.jit_compiler import RMSCompiler
from VeraGridEngine.Templates.Rms.bus_rms_template import initialize_bus_rms, get_bus_rms_algebraic_vars
from VeraGridEngine.IO.fmu.importer.experimental_cs import (
    advance_rms_fmu_cs_devices,
    close_rms_fmu_cs_devices,
    initialize_rms_fmu_cs_devices,
    register_rms_fmu_cs_device,
)
from VeraGridEngine.IO.fmu.importer.experimental_me import (
    advance_rms_fmu_me_devices,
    close_rms_fmu_me_devices,
    initialize_rms_fmu_me_devices,
    register_rms_fmu_me_device,
)
from VeraGridEngine.Utils.procedural_logic import BlockProceduralLogicUpdater


def _tic():
    return time.perf_counter()


def _toc(t0):
    return time.perf_counter() - t0


def _is_time_aligned(t_curr: float, event_time: float) -> bool:
    """
    Return whether ``t_curr`` is aligned with ``event_time`` within numeric tolerance.
    """
    time_tol = 10.0 * np.finfo(np.float64).eps * max(1.0, abs(event_time))
    return bool(abs(t_curr - event_time) <= time_tol)


def _get_next_forced_mode_event_time(
    scheduled_mode_events: Dict[int, List[Tuple[float, float, bool]]],
    t_prev: float,
    t_target: float,
) -> Optional[float]:
    """
    Return the earliest forced-alignment mode event time in ``(t_prev, t_target]``.

    :param scheduled_mode_events: Mapping uid -> sorted list of (time, value, force_step_alignment).
    :param t_prev: Previous local solver time.
    :param t_target: Nominal macro target time.
    :return: Earliest forced event time or ``None``.
    """
    next_time: Optional[float] = None

    for _, event_list in scheduled_mode_events.items():
        for event_time, _, force_step_alignment in event_list:
            if force_step_alignment and (t_prev < event_time <= t_target):
                if next_time is None or event_time < next_time:
                    next_time = event_time

    return next_time


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
                 pf_results: PowerFlowResults,
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
        self.init_guess: Dict[int, float | int | complex | None] = dict()
        self.event_params_init_dict: Dict[int, float | int | complex | None] = dict()
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

        self._runtime_all_parameters_source: List[Var] = list()
        self._runtime_all_eqs_source: List[Expr | Const] = list()
        self._runtime_continuous_parameters: List[Var] = list()
        self._runtime_mode_parameters: List[Var] = list()
        self._runtime_continuous_eqs: List[Expr | Const] = list()
        self._runtime_mode_eqs: List[Expr | Const] = list()
        self._event_parameter_device_idtags: Dict[int, str] = dict()
        self._runtime_all_eqs_source0: List[Expr | Const] = list()
        self._runtime_continuous_slice: slice = slice(0, 0)
        self._runtime_mode_slice: slice = slice(0, 0)
        self._continuous_event_parameter_uids: Set[int] = set()
        self._discrete_event_parameter_uids: Set[int] = set()
        self._scheduled_mode_events: Dict[int, List[Tuple[float, float, bool]]] = dict()
        self._mode_event_cursor: Dict[int, int] = dict()
        self._active_events_group: RmsEventsGroup | None = None
        self._mode_runtime_expression_by_uid: Dict[int, Expr | Const] = dict()
        self._mode_runtime_initialized_uids: Set[int] = set()
        self._procedural_logic_updater: BlockProceduralLogicUpdater | None = None

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
        self._block_boundary_updater: Any | None = None
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
        branch_bus_p = np.zeros(n, dtype=float)
        branch_bus_q = np.zeros(n, dtype=float)

        # general indexes for variables and parameters
        self._n_vars = 0
        self._n_params = 0
        self._n_event_params = 0
        self._n_diff = 0

        ######################################## Initialize devices ########################################

        # initialize buses
        bus_dict: Dict[Bus, int] = dict()

        for bus_num, elm in enumerate(self.grid.buses):

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
                # get parameters from api object
                if ParamPowerFlowRefferenceType.g in elm.rms_model.api_obj_mapping:
                    elm.rms_model.parameters[
                        elm.rms_model.api_obj_mapping[ParamPowerFlowRefferenceType.g]] = Const(
                        float(elm.R / (elm.R ** 2 + elm.X ** 2)))
                if ParamPowerFlowRefferenceType.b in elm.rms_model.api_obj_mapping:
                    elm.rms_model.parameters[
                        elm.rms_model.api_obj_mapping[ParamPowerFlowRefferenceType.b]] = Const(
                        float(-elm.X / (elm.R ** 2 + elm.X ** 2)))
                if ParamPowerFlowRefferenceType.bsh in elm.rms_model.api_obj_mapping:
                    elm.rms_model.parameters[
                        elm.rms_model.api_obj_mapping[ParamPowerFlowRefferenceType.bsh]] = Const(elm.B)
                if ParamPowerFlowRefferenceType.r in elm.rms_model.api_obj_mapping:
                    elm.rms_model.parameters[
                        elm.rms_model.api_obj_mapping[ParamPowerFlowRefferenceType.r]] = Const(elm.R)
                if ParamPowerFlowRefferenceType.l in elm.rms_model.api_obj_mapping:
                    elm.rms_model.parameters[ elm.rms_model.api_obj_mapping[ParamPowerFlowRefferenceType.l]] = Const(elm.X)

                # get variables from bus
                # if elm.bus_from.rms_model.empty():
                #     initialize_bus_rms(elm.bus_from, self.grid.var_factory)
                # if elm.bus_to.rms_model.empty():
                #     initialize_bus_rms(elm.bus_to, self.grid.var_factory)

                Vmf, Vaf = get_bus_rms_algebraic_vars(elm.bus_from.rms_model)
                Vmt, Vat = get_bus_rms_algebraic_vars(elm.bus_to.rms_model)

                if Vmf is not None and VarPowerFlowRefferenceType.Vmf in elm.rms_model.external_mapping:
                    elm.rms_model.update_model(
                        elm.rms_model.external_mapping[VarPowerFlowRefferenceType.Vmf], Vmf)
                if Vaf is not None and VarPowerFlowRefferenceType.Vaf in elm.rms_model.external_mapping:
                    elm.rms_model.update_model(
                        elm.rms_model.external_mapping[VarPowerFlowRefferenceType.Vaf], Vaf)
                if Vmt is not None and VarPowerFlowRefferenceType.Vmt in elm.rms_model.external_mapping:
                    elm.rms_model.update_model(
                        elm.rms_model.external_mapping[VarPowerFlowRefferenceType.Vmt], Vmt)
                if Vat is not None and VarPowerFlowRefferenceType.Vat in elm.rms_model.external_mapping:
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

                f_idx = bus_dict[elm.bus_from]
                t_idx = bus_dict[elm.bus_to]
                branch_bus_p[f_idx] += self.Sf[branch_num].real
                branch_bus_q[f_idx] += self.Sf[branch_num].imag
                branch_bus_p[t_idx] += self.St[branch_num].real
                branch_bus_q[t_idx] += self.St[branch_num].imag

                if VarPowerFlowRefferenceType.If_dc in elm.rms_model.external_mapping and Vmf is not None:
                    if Vmf.uid in self.uid2idx_vars:
                        vmf_idx = self.uid2idx_vars[Vmf.uid]
                        if vmf_idx in self.init_guess:
                            vmf0 = self.init_guess[vmf_idx]
                        else:
                            vmf0 = 1.0
                    else:
                        vmf_idx = None
                        vmf0 = 1.0

                    if abs(vmf0) > 1e-9:
                        self.set_init_guess(
                            elm.rms_model,
                            VarPowerFlowRefferenceType.If_dc,
                            self.Sf[branch_num].real / vmf0,
                        )

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
                            event_param_init_dict=self.event_params_init_dict,
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
                if not elm.bus_from.is_dc and VarPowerFlowRefferenceType.Qf in elm.rms_model.external_mapping:
                    setQ(Q, Q_used, f, -elm.rms_model.E(VarPowerFlowRefferenceType.Qf))
                else:
                    pass
                if not elm.bus_to.is_dc and VarPowerFlowRefferenceType.Qt in elm.rms_model.external_mapping:
                    setQ(Q, Q_used, t, -elm.rms_model.E(VarPowerFlowRefferenceType.Qt))
                else:
                    pass
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
                if ParamPowerFlowRefferenceType.alpha1 in elm.rms_model.api_obj_mapping:
                    elm.rms_model.parameters[elm.rms_model.api_obj_mapping[ParamPowerFlowRefferenceType.alpha1]] = Const(elm.alpha1)
                if ParamPowerFlowRefferenceType.alpha2 in elm.rms_model.api_obj_mapping:
                    elm.rms_model.parameters[elm.rms_model.api_obj_mapping[ParamPowerFlowRefferenceType.alpha2]] = Const(elm.alpha2)
                if ParamPowerFlowRefferenceType.alpha3 in elm.rms_model.api_obj_mapping:
                    elm.rms_model.parameters[elm.rms_model.api_obj_mapping[ParamPowerFlowRefferenceType.alpha3]] = Const(elm.alpha3)

                St_vsc = self.power_flow_results.St_vsc / self.grid.Sbase
                Sf_vsc = (self.power_flow_results.Pfn_vsc[i] + self.power_flow_results.Pfp_vsc[i]) / self.grid.Sbase
                # fill init_guess

                self.add_variables_to_compilation_dicts(elm, mdl)
                f = bus_dict[elm.bus_from]
                t = bus_dict[elm.bus_to]
                pt_init = St_vsc[i].real
                qt_init = St_vsc[i].imag
                vm_t = np.abs(self.power_flow_results.voltage[t])
                im_init = np.sqrt(pt_init * pt_init + qt_init * qt_init) / (vm_t + 1e-12)

                if  i < len(self.power_flow_results.It_vsc):
                    it_mag = np.abs(self.power_flow_results.It_vsc[i]) / self.grid.Sbase
                    if np.isfinite(it_mag) and it_mag > 0.0:
                        im_init = it_mag

                self.set_init_guess(mdl, VarPowerFlowRefferenceType.Pf, Sf_vsc)
                self.set_init_guess(mdl, VarPowerFlowRefferenceType.Pt, pt_init)
                self.set_init_guess(mdl, VarPowerFlowRefferenceType.Qt, qt_init)
                if VarPowerFlowRefferenceType.Im in mdl.external_mapping:
                    im_init = float(np.abs(self.power_flow_results.It_vsc[i]) / self.grid.Sbase)
                    self.set_init_guess(mdl, VarPowerFlowRefferenceType.Im, im_init)
                else:
                    pass

                setP(P, P_used, f, -mdl.E(VarPowerFlowRefferenceType.Pf))
                setP(P, P_used, t, -mdl.E(VarPowerFlowRefferenceType.Pt))
                if VarPowerFlowRefferenceType.Qt in mdl.external_mapping and not elm.bus_to.is_dc:
                    setQ(Q, Q_used, t, -mdl.E(VarPowerFlowRefferenceType.Qt))
                else:
                    pass
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
                    params_array: np.ndarray = np.zeros(
                        len(self._constant_parameters))  # array with the lenght of constant params
                    for param, const in elm.rms_model.parameters.items():
                        params_array[self._uid2idx_params[param.uid]] = const.value

                    diff_sys_vars: Dict[int, Var] = {diff_var.uid: diff_var for diff_var in
                                                     self._diff_vars}  # dictionary uid, var for diff_vars
                    rms_compiler_init = RMSCompiler(
                        variables=list(self.sys_vars.values()),
                        diff_vars=list(diff_sys_vars.values()),
                        v_params=self._variable_parameters,
                        c_params=self._constant_parameters,
                        dt_var=Var("dt"),
                        compiler_names_dict=self._compiler_names_dict,
                    )
                    compile_single_equation = build_rms_single_equation_compiler(
                        rms_compiler_init)  # function to compile one equation

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
                        event_param_init_dict=self.event_params_init_dict,
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

        gen_idx_map = {elm.idtag: i for i, elm in enumerate(grid.generators)}
        batt_idx_map = {elm.idtag: i for i, elm in enumerate(grid.batteries)}
        shunt_idx_map = {elm.idtag: i for i, elm in enumerate(grid.shunts)}
        loads_idx_map = {elm.idtag: i for i, elm in enumerate(grid.loads)}

        fixed_inj_p = np.zeros(n, dtype=float)
        fixed_inj_q = np.zeros(n, dtype=float)
        slack_gen_count = np.zeros(n, dtype=int)
        slack_gen_snom = np.zeros(n, dtype=float)

        for dev in grid.get_injection_devices_iter():
            if dev.rms_model.empty():
                continue
            bidx = bus_dict[dev.bus]
            if dev.bus.is_dc:
                continue

            if dev.idtag in gen_idx_map and dev.bus.is_slack:
                slack_gen_count[bidx] += 1
                snom = dev.Snom
                if snom <= 0.0:
                    snom = 1.0
                slack_gen_snom[bidx] += snom
                continue

            Vbus_pf = self.power_flow_results.voltage[bidx]
            if dev.idtag in gen_idx_map:
                gidx = gen_idx_map[dev.idtag]
                Sdev_pf = complex(float(dev.P), float(self.power_flow_results.gen_q[gidx])) / grid.Sbase
            elif dev.idtag in batt_idx_map:
                bdid = batt_idx_map[dev.idtag]
                Sdev_pf = complex(float(dev.P), float(self.power_flow_results.battery_q[bdid])) / grid.Sbase
            elif dev.idtag in shunt_idx_map:
                g_sh = float(dev.G) / grid.Sbase
                b_sh = float(dev.B) / grid.Sbase
                Sdev_pf = complex(g_sh * (abs(Vbus_pf) ** 2), -b_sh * (abs(Vbus_pf) ** 2))
            elif dev.idtag in loads_idx_map:
                Sdev_pf = complex(-float(dev.P), -float(dev.Q)) / grid.Sbase
            else:
                Sdev_pf = complex(0.0, 0.0)

            fixed_inj_p[bidx] += Sdev_pf.real
            fixed_inj_q[bidx] += Sdev_pf.imag

        residual_p = branch_bus_p - fixed_inj_p
        residual_q = branch_bus_q - fixed_inj_q
        remaining_slack_gen = slack_gen_count.copy()
        remaining_slack_gen_snom = slack_gen_snom.copy()

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
                    # not necessary anymore, models are already connected with the buses
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
                    Vbus = self.power_flow_results.voltage[bus_index]
                    if elm.idtag in gen_idx_map:
                        if elm.bus.is_slack and remaining_slack_gen[bus_index] > 0:
                            elm_snom = float(elm.Snom)
                            if elm_snom <= 0.0:
                                elm_snom = 1.0

                            if remaining_slack_gen[bus_index] == 1:
                                share = 1.0
                            else:
                                snom_den = remaining_slack_gen_snom[bus_index]
                                if snom_den <= 0.0:
                                    share = 1.0 / remaining_slack_gen[bus_index]
                                else:
                                    share = elm_snom / snom_den

                            P_val = residual_p[bus_index] * share
                            Q_val = residual_q[bus_index] * share
                            remaining_slack_gen[bus_index] -= 1
                            remaining_slack_gen_snom[bus_index] -= elm_snom
                            residual_p[bus_index] -= P_val
                            residual_q[bus_index] -= Q_val
                            Sdev = complex(P_val, Q_val)
                        else:
                            gidx = gen_idx_map[elm.idtag]
                            Sdev = complex(float(elm.P), float(self.power_flow_results.gen_q[gidx])) / grid.Sbase
                    elif elm.idtag in batt_idx_map:
                        bidx = batt_idx_map[elm.idtag]
                        Sdev = complex(float(elm.P), float(self.power_flow_results.battery_q[bidx])) / grid.Sbase
                    elif elm.idtag in shunt_idx_map:
                        g_sh = float(elm.G) / grid.Sbase
                        b_sh = float(elm.B) / grid.Sbase
                        Sdev = complex(g_sh * (abs(Vbus) ** 2), -b_sh * (abs(Vbus) ** 2))
                    elif elm.idtag in loads_idx_map:
                        Sdev = complex(-float(elm.P), -float(elm.Q)) / grid.Sbase
                    else:
                        Sdev = self.power_flow_results.Sbus[bus_index] / grid.Sbase

                    self.set_init_guess(elm.rms_model, VarPowerFlowRefferenceType.P,
                                        Sdev.real)
                    self.set_init_guess(elm.rms_model, VarPowerFlowRefferenceType.Q,
                                        Sdev.imag)

                k = bus_dict[elm.bus]
                if VarPowerFlowRefferenceType.P in elm.rms_model.external_mapping:
                    setP(P, P_used, k, elm.rms_model.E(VarPowerFlowRefferenceType.P))
                if VarPowerFlowRefferenceType.Q in elm.rms_model.external_mapping:
                    setQ(Q, Q_used, k, elm.rms_model.E(VarPowerFlowRefferenceType.Q))

                if self.options.initialization_method == RmsInitializationMethod.Explicit:

                    # Todo: add check to see if all the initialization equations are there, otherwise raise error
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
                        event_param_init_dict=self.event_params_init_dict,
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
                    # initialize variables with no init equation assigned
                    # run_rms_native_initialization(self, self.options)

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

        event_eq_by_uid: Dict[int, Expr | Const] = {
            ep.uid: eq for ep, eq in zip(self._variable_parameters, self._event_parameters_eqs0)
        }
        for i, ep in enumerate(self._runtime_all_parameters_source):
            if ep.uid in self._discrete_event_parameter_uids:
                continue
            runtime_eq = self._runtime_all_eqs_source[i]
            if isinstance(runtime_eq, Const) and runtime_eq.value is None and ep.uid in event_eq_by_uid:
                self._runtime_all_eqs_source[i] = event_eq_by_uid[ep.uid]

        for i, eq in enumerate(self._runtime_all_eqs_source):
            if eq is None or (isinstance(eq, Const) and eq.value is None):
                raise Exception(f"Runtime event parameter {self._runtime_all_parameters_source[i]} has None Value")

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

        self._runtime_all_parameters_source.append(self._dt)
        self._runtime_all_parameters_source.append(self._delta)
        self._runtime_all_eqs_source.append(Const(1e-3))
        self._runtime_all_eqs_source.append(Const(1))

        # add these parameters, m is for variable parameters
        self._compiler_names_dict[self._dt.uid] = f"{self.VARIABLE_PARAMS_NAME}[{self._n_event_params}]"
        self._alias_names_dict[self._dt.uid] = f"{self.VARIABLE_PARAMS_NAME}_{self._n_event_params}"
        self._uid2idx_event_params[self._dt.uid] = self._n_event_params
        self._n_event_params += 1

        self._compiler_names_dict[self._delta.uid] = f"{self.VARIABLE_PARAMS_NAME}[{self._n_event_params}]"
        self._alias_names_dict[self._delta.uid] = f"{self.VARIABLE_PARAMS_NAME}_{self._n_event_params}"
        self._uid2idx_event_params[self._delta.uid] = self._n_event_params
        self._n_event_params += 1

        self._runtime_all_eqs_source0 = list(self._runtime_all_eqs_source)

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

    def set_events_group(self, rms_events_group: RmsEventsGroup):
        """
        add events modifying values of event_parameters equations
        :param rms_events_group:
        :return:
        """
        same_group_requested: bool

        if self._active_events_group is None:
            same_group_requested = rms_events_group is None and len(self._scheduled_mode_events) > 0
        elif rms_events_group is None:
            same_group_requested = False
        else:
            same_group_requested = self._active_events_group.idtag == rms_events_group.idtag

        if same_group_requested:
            return

        active_runtime_eqs: List[Expr | Const] = list(self._runtime_all_eqs_source0)

        if self._continuous_event_parameter_uids:
            collect_continuous_events: Dict[int, Dict[str, List[float]]] = {
                uid: {"times": list(), "values": list()}
                for uid in self._continuous_event_parameter_uids
            }
        else:
            collect_continuous_events = dict()

        scheduled_mode_events: Dict[int, List[Tuple[float, float, bool]]] = dict()

        selected_events = self._get_rms_events_for_group(rms_events_group)

        for rms_evt in selected_events:
            if not isinstance(rms_evt.parameter, Var):
                continue

            if not self._event_targets_registered_parameter(rms_evt, int(rms_evt.parameter.uid)):
                continue

            parameter_uid = int(rms_evt.parameter.uid)

            if parameter_uid in self._discrete_event_parameter_uids:
                event_list = scheduled_mode_events.setdefault(parameter_uid, list())
                try:
                    force_step_alignment = bool(rms_evt.force_step_alignment)
                except AttributeError:
                    force_step_alignment = False

                event_list.append(
                    (
                        float(rms_evt.time),
                        float(rms_evt.value),
                        force_step_alignment,
                    )
                )
            else:
                if parameter_uid in collect_continuous_events:
                    collect_continuous_events[parameter_uid]["times"].append(float(rms_evt.time))
                    collect_continuous_events[parameter_uid]["values"].append(float(rms_evt.value))
                else:
                    pass

        for parameter_uid, info in collect_continuous_events.items():
            if len(info["times"]) == 0:
                continue

            sort_idx = np.argsort(np.asarray(info["times"], dtype=np.float64), kind="stable")
            t_events = np.asarray(info["times"], dtype=np.float64)[sort_idx]
            new_values = np.asarray(info["values"], dtype=np.float64)[sort_idx]

            runtime_idx = self._uid2idx_event_params[parameter_uid]
            active_runtime_eqs[runtime_idx] = piecewise(
                time_var=self._glob_time,
                t_events=t_events,
                new_values=new_values,
                default_value=active_runtime_eqs[runtime_idx],
            )

        self._runtime_all_eqs_source = active_runtime_eqs
        self._scheduled_mode_events = scheduled_mode_events
        self._active_events_group = rms_events_group

        self._rebuild_runtime_parameter_partition()
        self._initialize_mode_event_state()
        self._initialize_procedural_logic_updater()

        if self.get_variable_parameter_number() > 0:
            self._variable_parameters_values = np.ones(self.get_variable_parameter_number(), dtype=np.float64)
        else:
            self._variable_parameters_values = np.zeros(0, dtype=np.float64)


        # --------------------------------------------------------------------------------------------------------------
        # Compile RHS and Jacobian using JIT Compiler adaptation
        # --------------------------------------------------------------------------------------------------------------
        timings = dict()
        # print("Compiling RMS using JIT Native Compiler...")
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
        self._derivative_fn = rms_compiler.compile_derivative_fn(self._uid2idx_vars)
        timings["SymbolicDerivative"] = _toc(t0)

        t0 = _tic()
        self._event_params_fn = rms_compiler.compile_event_params_fn(
            eqs=self._event_parameters_eqs,
            alias_names_dict=self._alias_names_dict,
            EVENT_PARAMS_NAME=self.VARIABLE_PARAMS_NAME,
            TIME_NAME=self.TIME_NAME,
        )
        timings["Event parameters"] = _toc(t0)

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
        self._mode_runtime_initialized_uids = set()
        if self.get_all_vars_number() > 0 and self.get_variable_parameter_number() > 0:
            self._initialize_latched_mode_defaults(t=0.0, x=self.get_x0())

        self._constant_params = np.array([const.value for const in self._parameters_values])

        from VeraGridEngine.Utils.procedural_logic import build_boundary_updater_from_block

        self._block_boundary_updater = build_boundary_updater_from_block(self)

        if self.options.verbose > 0:
            print(f"\nTotal compile time: {sum(timings.values()):.4f} s")

        # we mark the problem as ready for simulation
        self.set_initialize_flag()

    def get_next_forced_event_time(self, t_prev: float, t_target: float) -> Optional[float]:
        t_mode = _get_next_forced_mode_event_time(self._scheduled_mode_events, t_prev, t_target)

        t_proc: Optional[float] = None
        if self._procedural_logic_updater is not None:
            t_proc = self._procedural_logic_updater.get_next_forced_event_time(t_prev, t_target)

        if t_mode is None:
            return t_proc
        if t_proc is None:
            return t_mode
        return min(t_mode, t_proc)

    def _initialize_procedural_logic_updater(self) -> None:
        entries: List = list()
        for blk in self.sys_block.get_all_blocks():
            if blk.procedural_logic:
                entries.extend(blk.procedural_logic)
        if len(entries) == 0:
            self._procedural_logic_updater = None
            return

        self._procedural_logic_updater = BlockProceduralLogicUpdater(self, entries)

    def _register_runtime_event_parameters(self, dev: ALL_DEV_TYPES, mdl: Block) -> None:
        """
        Register runtime-updatable parameters declared by the device block.
        """
        if not mdl.event_dict and not mdl.mode_dict:
            return

        for parameter, expression in mdl.event_dict.items():
            init_eq_for_parameter: Expr | Const | None = None
            for init_var, init_eq in mdl.init_eqs.items():
                if init_var.uid == parameter.uid:
                    init_eq_for_parameter = init_eq
                    break

            expression_for_classification: Expr | Const = expression
            if isinstance(expression, Const) and expression.value is None and init_eq_for_parameter is not None:
                expression_for_classification = init_eq_for_parameter

            self._event_parameter_device_idtags[parameter.uid] = dev.idtag

            if self._expression_references_system_vars(expression_for_classification):
                self._discrete_event_parameter_uids.add(parameter.uid)
            else:
                self._continuous_event_parameter_uids.add(parameter.uid)

        for parameter in mdl.mode_dict.keys():
            self._event_parameter_device_idtags[parameter.uid] = dev.idtag
            self._discrete_event_parameter_uids.add(parameter.uid)

    def _expression_references_system_vars(self, expression: Expr | Const) -> bool:
        if isinstance(expression, Const):
            return False

        try:
            vars_in_expr: List[Var] = get_expression_vars(expression)
        except Exception:
            return False

        for var in vars_in_expr:
            if var.uid in self._uid2idx_vars:
                return True

        return False

    def _event_targets_registered_parameter(self, evt: object, parameter_uid: int) -> bool:
        """
        Return whether the event targets a runtime parameter registered for this device.
        """
        if parameter_uid in self._event_parameter_device_idtags:
            registered_device_idtag: str | None = self._event_parameter_device_idtags[parameter_uid]
        else:
            registered_device_idtag = None

        try:
            event_device_idtag: str = str(evt.device_idtag)
        except Exception:
            event_device_idtag = ""

        if registered_device_idtag is None:
            return False

        if event_device_idtag == "":
            return True

        return registered_device_idtag == event_device_idtag

    @property
    def boundary_update(self):
        return self

    def _get_rms_events_for_group(self, rms_events_group: RmsEventsGroup | None) -> List[object]:
        if rms_events_group is None:
            return list(self.grid.rms_events)

        selected_events = list()

        for evt in self.grid.rms_events:
            try:
                if evt.group.idtag == rms_events_group.idtag:
                    selected_events.append(evt)
                else:
                    pass
            except Exception:
                pass

        return selected_events

    def _rebuild_runtime_parameter_partition(self) -> None:
        self._runtime_continuous_parameters = list()
        self._runtime_mode_parameters = list()
        self._runtime_continuous_eqs = list()
        self._runtime_mode_eqs = list()

        self._uid2idx_event_params = dict()

        n_source: int = len(self._runtime_all_parameters_source)
        i: int = 0

        while i < n_source:
            parameter: Var = self._runtime_all_parameters_source[i]
            equation: Expr | Const = self._runtime_all_eqs_source[i]

            if parameter.uid in self._discrete_event_parameter_uids:
                self._runtime_mode_parameters.append(parameter)
                self._runtime_mode_eqs.append(equation)
            else:
                self._runtime_continuous_parameters.append(parameter)
                self._runtime_continuous_eqs.append(equation)

            i += 1

        self._runtime_continuous_slice = slice(0, len(self._runtime_continuous_parameters))
        self._runtime_mode_slice = slice(
            len(self._runtime_continuous_parameters),
            len(self._runtime_continuous_parameters) + len(self._runtime_mode_parameters)
        )

        self._variable_parameters = list()
        self._event_parameters_eqs = list()

        for parameter in self._runtime_continuous_parameters:
            self._variable_parameters.append(parameter)

        for parameter in self._runtime_mode_parameters:
            self._variable_parameters.append(parameter)

        for equation in self._runtime_continuous_eqs:
            self._event_parameters_eqs.append(equation)

        for equation in self._runtime_mode_eqs:
            self._event_parameters_eqs.append(equation)

        self._n_event_params = len(self._variable_parameters)

        for k, parameter in enumerate(self._variable_parameters):
            self._uid2idx_event_params[parameter.uid] = k
            self._compiler_names_dict[parameter.uid] = f"{self.VARIABLE_PARAMS_NAME}[{k}]"
            self._alias_names_dict[parameter.uid] = f"{self.VARIABLE_PARAMS_NAME}_{k}"

    def _initialize_mode_event_state(self) -> None:
        self._mode_event_cursor = dict()

        for uid, event_list in self._scheduled_mode_events.items():
            event_list.sort(key=lambda evt: evt[0])
            self._mode_event_cursor[uid] = 0

    def _apply_scheduled_mode_events(self, t_curr: float, full_params: Vec) -> None:
        for uid, event_list in self._scheduled_mode_events.items():
            if uid in self._mode_event_cursor:
                event_idx: int = self._mode_event_cursor[uid]
            else:
                event_idx = 0
            n_events: int = len(event_list)

            while event_idx < n_events:
                event_time: float
                event_value: float
                force_step_alignment: bool
                event_time, event_value, force_step_alignment = event_list[event_idx]

                if t_curr < event_time:
                    break

                if uid in self._uid2idx_event_params:
                    runtime_idx: Optional[int] = self._uid2idx_event_params[uid]
                else:
                    runtime_idx = None

                if force_step_alignment:
                    if _is_time_aligned(t_curr, event_time):
                        if runtime_idx is not None:
                            full_params[runtime_idx] = event_value
                        else:
                            pass
                    else:
                        raise RuntimeError(
                            f"Scheduled RMS mode event at t={event_time} requires exact step alignment, "
                            f"but current solver time is t={t_curr}."
                        )
                else:
                    if runtime_idx is not None:
                        full_params[runtime_idx] = event_value
                    else:
                        pass

                event_idx += 1

            self._mode_event_cursor[uid] = event_idx

    def _evaluate_runtime_expression_with_state(self, expression: Expr | Const, params: Vec, x: Vec, t: float) -> float:
        if isinstance(expression, Const):
            if expression.value is None:
                return 0.0
            else:
                return float(expression.value)

        if isinstance(expression, Var):
            if expression.uid == self._glob_time.uid or expression.name == self.TIME_NAME:
                return float(t)

            if expression.uid in self._uid2idx_event_params:
                runtime_idx = self._uid2idx_event_params[expression.uid]
            else:
                runtime_idx = None
            if runtime_idx is not None:
                return float(params[runtime_idx])

            if expression.uid in self._uid2idx_params:
                const_idx = self._uid2idx_params[expression.uid]
            else:
                const_idx = None
            if const_idx is not None:
                return float(self._parameters_values[const_idx].value)

            if expression.uid in self._uid2idx_vars:
                var_idx = self._uid2idx_vars[expression.uid]
            else:
                var_idx = None
            if var_idx is not None:
                return float(x[var_idx])

            return 0.0

        uid_bindings: Dict[int, float] = dict()

        for uid, idx in self._uid2idx_event_params.items():
            uid_bindings[uid] = float(params[idx])

        for uid, idx in self._uid2idx_params.items():
            uid_bindings[uid] = float(self._parameters_values[idx].value)

        for uid, idx in self._uid2idx_vars.items():
            uid_bindings[uid] = float(x[idx])

        uid_bindings[self._glob_time.uid] = float(t)

        try:
            return float(expression.eval_uid(uid_bindings))
        except Exception:
            return 0.0

    def _update_dynamic_mode_defaults(self, t: float, x: Vec, params: Vec) -> None:
        for uid, expression in self._mode_runtime_expression_by_uid.items():
            if uid in self._scheduled_mode_events and len(self._scheduled_mode_events[uid]) > 0:
                continue

            if uid in self._mode_runtime_initialized_uids:
                continue

            if uid in self._uid2idx_event_params:
                runtime_idx = self._uid2idx_event_params[uid]
            else:
                runtime_idx = None
            if runtime_idx is None:
                continue

            params[runtime_idx] = self._evaluate_runtime_expression_with_state(expression, params, x, t)
            self._mode_runtime_initialized_uids.add(uid)

    def _initialize_latched_mode_defaults(self, t: float, x: Vec) -> None:
        if self._variable_parameters_values is None:
            return

        self._update_dynamic_mode_defaults(
            t=float(t),
            x=x,
            params=self._variable_parameters_values,
        )

    def reset_boundary_update_state(self, t0: float = 0.0) -> None:
        if self.get_variable_parameter_number() > 0 and self._event_params_fn is not None:
            self._variable_parameters_values = self._event_params_fn(np.ones(self.get_variable_parameter_number()), float(t0))
            self._variable_parameters_values = self.def_event_params_fn(self._variable_parameters_values, float(t0))
        else:
            self._variable_parameters_values = np.zeros(0, dtype=np.float64)

        self._mode_event_cursor = dict()
        self._initialize_mode_event_state()
        self._mode_runtime_initialized_uids = set()

        if self._procedural_logic_updater is not None:
            for logic in self._procedural_logic_updater.logic_entries:
                logic.bind(self)

        if self.get_all_vars_number() > 0 and self.get_variable_parameter_number() > 0:
            self._initialize_latched_mode_defaults(t=float(t0), x=self.get_x0())

    def def_event_params_fn(self, ev_param: Vec, t: float) -> Vec:
        """
        Evaluate runtime event parameter expressions while preserving mode latches.

        :param ev_param: Current runtime parameter vector.
        :param t: Simulation time.
        :return: Updated runtime parameter vector.
        """
        try:
            runtime_continuous_eqs = self._runtime_continuous_eqs
        except AttributeError:
            if self._event_params_fn is None:
                return ev_param

            updated = self._event_params_fn(ev_param, t)
            updated = self._event_params_fn(updated, t)

            return updated

        n_continuous = len(runtime_continuous_eqs)


        if n_continuous == 0 or self._event_params_fn is None:
            return ev_param

        try:
            runtime_mode_slice = self._runtime_mode_slice
        except AttributeError:
            runtime_mode_slice = slice(0, 0)

        mode_snapshot: Vec | None = None
        if runtime_mode_slice.start != runtime_mode_slice.stop:
            mode_snapshot = ev_param[runtime_mode_slice].copy()

        updated = self._event_params_fn(ev_param, t)
        updated = self._event_params_fn(updated, t)

        if runtime_mode_slice.start == runtime_mode_slice.stop:
            return updated
        else:
            assert mode_snapshot is not None
            updated[runtime_mode_slice] = mode_snapshot

            return updated

    def update_variable_params(self, t: float, x_snapshot: Vec | None = None):
        """
        Update the variable parameters. Continuous runtime parameters are re-evaluated,
        while retained mode parameters are left untouched unless updated by boundary
        logic.

        :param t:
        :param x_snapshot:
        :return:
        """
        if self._event_params_fn is None:
            raise ValueError("_event_params_fn is None")

        self._variable_parameters_values = self.def_event_params_fn(self._variable_parameters_values, t)

        if self._block_boundary_updater is not None and x_snapshot is not None:
            if self._constant_params is None:
                constant_params = np.zeros(0, dtype=float)
            else:
                constant_params = self._constant_params

            full_params = np.concatenate((self._variable_parameters_values.copy(), constant_params))
            self._block_boundary_updater.update(float(t), x_snapshot, full_params)
            self._variable_parameters_values[:] = full_params[:self.get_variable_parameter_number()]

    def update(self, t: float, x: Vec, params: Vec) -> None:
        self._update_dynamic_mode_defaults(t=t, x=x, params=params)
        if self._procedural_logic_updater is not None:
            self._procedural_logic_updater.update(t=t, x=x, params=params)
        self._apply_scheduled_mode_events(t, params)
        self._variable_parameters_values[:] = params[: len(self._variable_parameters)]

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
        self._register_runtime_event_parameters(dev=elm, mdl=mdl)

        def _register_event_parameter(ep: Var, eq: Expr | Const, runtime_eq: Expr | Const | None = None) -> None:
            if ep.uid in self._uid2idx_event_params:
                raise ValueError(f"Event parameter '{ep.name}' (uid={ep.uid}) is already registered in the system. "
                                 f"Previous device may have created a duplicate event parameter.")

            self._compiler_names_dict[ep.uid] = f"{self.VARIABLE_PARAMS_NAME}[{self._n_event_params}]"
            self._alias_names_dict[ep.uid] = f"{self.VARIABLE_PARAMS_NAME}_{self._n_event_params}"
            self._uid2idx_event_params[ep.uid] = self._n_event_params

            effective_eq: Expr | Const = eq
            if isinstance(eq, Const) and eq.value is None:
                init_eq_for_ep: Expr | Const | None = None
                for init_var, init_eq in mdl.init_eqs.items():
                    if init_var.uid == ep.uid:
                        init_eq_for_ep = init_eq
                        break
                if init_eq_for_ep is not None:
                    effective_eq = init_eq_for_ep

            self._variable_parameters.append(ep)
            self._event_parameters_eqs0.append(effective_eq)
            self._runtime_all_parameters_source.append(ep)
            runtime_expression: Expr | Const = effective_eq if runtime_eq is None else runtime_eq

            if runtime_eq is None and ep.uid in self._discrete_event_parameter_uids:
                if isinstance(eq, Const) and eq.value is not None:
                    runtime_expression = Const(float(eq.value))
                else:
                    runtime_expression = Const(0.0)
                    self._mode_runtime_expression_by_uid[ep.uid] = effective_eq

            self._runtime_all_eqs_source.append(runtime_expression)
            self._runtime_all_eqs_source0.append(runtime_expression)

            self._n_event_params += 1

        for ep, eq in mdl.event_dict.items():
            _register_event_parameter(ep, eq)

        for ep, eq in mdl.mode_dict.items():
            _register_event_parameter(ep, eq)

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
            # print(f"DEBUG: set_init_guess {reference_powerflow.value} = {val} for var {var.name} (uid={var.uid})")
        else:
            print(
                f"DEBUG: set_init_guess {reference_powerflow.value} NOT FOUND in external_mapping. Available: {[k.value for k in mdl.external_mapping.keys()]}")

    def get_equation_at(self, i: int) -> Expr:
        """
        Get the equation at a global position
        :param i:
        :return:
        """
        if i < len(self._state_eqs):
            return self._state_eqs[i]
        else:
            i2 = i - len(self._state_eqs)
            return self._algebraic_eqs[i2]

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
        if dev in self._vars_info:
            var_list = self._vars_info[dev]
        else:
            var_list = None

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
    def uid2idx_event_params(self):
        return self._uid2idx_event_params

    @property
    def uid2idx_params(self):
        return self._uid2idx_params

    @property
    def glob_time(self):
        return self._glob_time

    def get_parameters_values(self) -> List[Const]:
        return self._parameters_values

    @property
    def get_algebraic_vars(self):
        """
        :return:
        """
        return self._algebraic_vars

    @property
    def algebraic_vars(self):
        return self._algebraic_vars

    @property
    def algebraic_eqs(self):
        """
        :return:
        """
        return self._algebraic_eqs

    @property
    def variable_parameters(self):
        """
        :return:
        """
        return self._variable_parameters

    @property
    def event_parameters_eqs(self):
        """
        :return:
        """
        return self._event_parameters_eqs

    @property
    def event_parameters_eqs0(self):
        """
        :return:
        """
        return self._event_parameters_eqs0

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

    @property
    def state_eqs(self):
        """
        :return:
        """
        return self._state_eqs

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
    def get_eventparams0(self) -> Vec:
        """
        Helper function to build the initial vector
        :return: array matching with the mapping, matching the solver ordering
        """
        x = np.zeros(len(self._variable_parameters))

        for uid, val in self.event_params_init_dict.items():
            i = self._uid2idx_event_params[uid]
            x[i] = val
        return x

    def get_dx0(self) -> Vec:
        """
        Helper function to build the initial vector
        :return: array matching with the mapping, matching the solver ordering
        """
        x = np.zeros(len(self._diff_vars))

        # for uid, val in self.init_guess.items():
        #     i = self._uid2idx_vars[uid]
        #     x[i] = val
        return x


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

    def get_compiler_names_dict(self):
        return self._compiler_names_dict

    def get_alias_names_dict(self):
        return self._alias_names_dict

    def get_diff_vars(self):
        return self._diff_vars


