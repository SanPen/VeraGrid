# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Dict, List, Tuple
import time
import numpy as np
import pandas as pd

from VeraGridEngine.enumerations import ParamPowerFlowReferenceType
from VeraGridEngine.Devices import MultiCircuit
from VeraGridEngine.Utils.Symbolic.symbolic import (Var, Const, Expr, piecewise)
from VeraGridEngine.Utils.Symbolic.compiled_functions import SymbolicParamsVector, SymbolicDerivative
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic_io import block_deep_copy
from VeraGridEngine.enumerations import VarPowerFlowReferenceType, RmsInitializationMethod, DeviceType
from VeraGridEngine.basic_structures import Vec, ObjVec, BoolVec, Logger
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowResults
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Simulations.Rms.initialization import init_explicit, init_pseudo_transient
from VeraGridEngine.Simulations.Rms.problems.rms_problem_template import RmsProblemTemplate
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Utils.Symbolic.jit_compiler import RMSCompiler
from VeraGridEngine.Templates.Rms.bus_complex_rms_template import initialize_bus_complex_rms, polar_to_complex
from VeraGridEngine.Templates.Rms.line_complex_rms_template import get_line_complex_rms_template


def _tic():
    return time.perf_counter()


def _toc(t0):
    return time.perf_counter() - t0


def setP(P: ObjVec, P_used: BoolVec, k: int, val: object):
    """
    Set or add to P value at index k.
    """
    if not P_used[k]:
        P[k] = val
        P_used[k] = True
    else:
        P[k] += val


def setQ(Q: ObjVec, Q_used: BoolVec, k: int, val: object):
    """
    Set or add to Q value at index k.
    """
    if not Q_used[k]:
        Q[k] = val
        Q_used[k] = True
    else:
        Q[k] += val


class RmsProblemComplex(RmsProblemTemplate):
    """
    Complex Phasor-based DAE (Differential-Algebraic Equation) class with MULTILINEAR equations.
    
    This class uses complex phasor representation with a single complex voltage variable per bus.
    The key innovation is TRULY MULTILINEAR current equations:
    
        I = Y * (Vf - Vt)  [Linear in voltage!]
    
    where Y = g + j*b is the complex admittance.
    
    When expanded:
        Ir = g*(Vrf - Vrt) - b*(Vif - Vit)
        Ii = g*(Vif - Vit) + b*(Vrf - Vrt)
    
    These are truly linear - no products of voltage variables, no squares!
    
    The current balance at each node (ΣI = 0) provides linear conservation equations.
    
    Responsibilities:
        - Store state and algebraic variables using complex phasor representation
        - Store Jacobian matrices
        - Store residual equations using multilinear current-based equations
        - Store sparsity patterns
        - Convert between polar (power flow) and complex phasor representations
    """
    VARS_NAME = "vars"
    VARIABLE_PARAMS_NAME = "vprms"
    CONSTANT_PARAMS_NAME = "cprms"
    DIFF_NAME = "diff"
    TIME_NAME = "glob_time"

    def __init__(self,
                 grid: MultiCircuit,
                 options: RmsOptions,
                 pf_results: PowerFlowResults | None):
        """
        Initialize the complex phasor-based RMS problem.
        
        :param grid: MultiCircuit grid object
        :param options: RMS simulation options
        :param pf_results: Power flow results for initialization
        """
        super().__init__()

        self.logger = Logger()
        self.grid: MultiCircuit = grid
        self.power_flow_results: PowerFlowResults = pf_results
        self.Sf = self.power_flow_results.Sf / self.grid.Sbase
        self.St = self.power_flow_results.St / self.grid.Sbase
        self.options: RmsOptions = options

        # General init guess containing all variable initial values
        self.init_guess: Dict[int, float] = dict()
        self.sys_block: Block = Block(children=[], in_vars=[])

        self._algebraic_vars: List[Var] = list()
        self._algebraic_eqs: List[Expr] = list()
        self._state_vars: List[Var] = list()
        self._state_eqs: List[Expr] = list()
        self._diff_vars: List[Var] = list()
        self._variable_parameters: List[Var] = list()
        self._event_parameters_eqs: List[Expr | Const] = list()
        self._constant_parameters: List[Var] = list()
        self._parameters_values: List[Const] = list()

        # --------------------------------------------------------------------------------------------------------------
        # Initialize the RMS problem
        # --------------------------------------------------------------------------------------------------------------

        ######################### Initialize containers #############################

        # Dictionaries to store device-variable info
        self._vars_info: Dict[ALL_DEV_TYPES, List[Var]] = dict()
        self._vars_glob_name2uid: Dict[str, int] = dict()

        # Dictionaries for compilation names
        self._compiler_names_dict: Dict[int, str] = dict()
        self._alias_names_dict: Dict[int, str] = dict()

        # Dictionaries for variable position in the variables arrays
        self._uid2idx_vars: Dict[int, int] = dict()
        self._uid2idx_event_params: Dict[int, int] = dict()
        self._uid2idx_params: Dict[int, int] = dict()
        self._uid2idx_diff: Dict[int, int] = dict()
        self._uid2idx_t: Dict[int, int] = dict()

        # Create time global time variable and add it to the compilation dict
        self._glob_time: Var = Var(self.TIME_NAME)
        self._compiler_names_dict[self._glob_time.uid] = self.TIME_NAME
        self._uid2idx_t[self._glob_time.uid] = 0

        # Dictionary of state and algebraic vars
        self.sys_vars: Dict[int, Var] = dict()

        # Initialize balance equation arrays
        n = len(self.grid.buses)
        P: ObjVec = np.zeros(n, dtype=object)
        Q: ObjVec = np.zeros(n, dtype=object)
        P_used: BoolVec = np.zeros(n, dtype=bool)
        Q_used: BoolVec = np.zeros(n, dtype=bool)

        # General indexes for variables and parameters
        self._n_vars = 0
        self._n_params = 0
        self._n_event_params = 0
        self._n_diff = 0

        ######################################## Initialize devices ########################################

        # Initialize buses with complex phasor representation
        bus_dict: Dict[Bus, int] = dict()
        for bus_num, elm in enumerate(self.grid.buses):
            bus_dict[elm] = bus_num

            # Initialize complex phasor-based bus model
            initialize_bus_complex_rms(bus=elm, vf=grid.var_factory)

            # Flatten model
            elm.rms_model.unify_blocks()
            mdl = block_deep_copy(elm.rms_model, grid.var_factory)

            self.add_variables_to_compilation_dicts(elm, mdl)

            # Add init values from powerflow to initial guess
            # Convert polar (Vm, Va) to complex phasor
            if elm.is_dc:
                self.set_init_guess(mdl, VarPowerFlowReferenceType.Vdc,
                                    np.abs(self.power_flow_results.voltage[bus_num]))
                self.set_init_guess(mdl, VarPowerFlowReferenceType.P,
                                    float(np.real(self.power_flow_results.Sbus[bus_num] / self.grid.Sbase)))
            else:
                Vm = np.abs(self.power_flow_results.voltage[bus_num])
                Va = np.angle(self.power_flow_results.voltage[bus_num])
                V_complex = polar_to_complex(Vm, Va)
                Vr, Vi = V_complex.real, V_complex.imag
                
                self.set_init_guess(mdl, VarPowerFlowReferenceType.Vr, Vr)
                self.set_init_guess(mdl, VarPowerFlowReferenceType.Vi, Vi)
                self.set_init_guess(mdl, VarPowerFlowReferenceType.P,
                                    float(np.real(self.power_flow_results.Sbus[bus_num] / self.grid.Sbase)))
                self.set_init_guess(mdl, VarPowerFlowReferenceType.Q,
                                    float(np.imag(self.power_flow_results.Sbus[bus_num] / self.grid.Sbase)))

            # Add model to system block
            self.sys_block.add(mdl)

        # Initialize branches with complex multilinear line models
        line_idx = 0
        for elm in self.grid.get_branches_iter(add_vsc=True, add_hvdc=True, add_switch=True):
            
            if elm.device_type == DeviceType.LineDevice:
                # Create complex multilinear line model
                from VeraGridEngine.Devices.Dynamic.dynamic_model_host import DynamicModelHost
                if elm.rms_model is None:
                    elm.rms_model = DynamicModelHost()
                
                elm.rms_model = get_line_complex_rms_template(
                    vfactory=grid.var_factory,
                    name=f"Line_complex_{elm.name}"
                ).block
                
                # Connect line inputs to bus outputs (complex voltages)
                bus_from_model = elm.bus_from.rms_model
                bus_to_model = elm.bus_to.rms_model
                
                # Connect: line.in_vars[0:3] -> [Vrf, Vif, Vrt, Vit]
                grid.var_factory.add_connections(
                    [elm.rms_model.in_vars[0]], 
                    [bus_from_model.out_vars[0]]  # Vrf -> bus.Vr
                )
                grid.var_factory.add_connections(
                    [elm.rms_model.in_vars[1]], 
                    [bus_from_model.out_vars[1]]  # Vif -> bus.Vi
                )
                grid.var_factory.add_connections(
                    [elm.rms_model.in_vars[2]], 
                    [bus_to_model.out_vars[0]]    # Vrt -> bus.Vr
                )
                grid.var_factory.add_connections(
                    [elm.rms_model.in_vars[3]], 
                    [bus_to_model.out_vars[1]]    # Vit -> bus.Vi
                )
                
                elm.rms_model.unify_blocks()
                mdl = elm.rms_model
                
                # Set line parameters
                mdl.parameters[mdl.api_obj_mapping[ParamPowerFlowReferenceType.g]] = Const(float(elm.R / (elm.R ** 2 + elm.X ** 2)))
                mdl.parameters[mdl.api_obj_mapping[ParamPowerFlowReferenceType.b]] = Const(float(-elm.X / (elm.R ** 2 + elm.X ** 2)))
                mdl.parameters[mdl.api_obj_mapping[ParamPowerFlowReferenceType.bsh]] = Const(elm.B)

                self.add_variables_to_compilation_dicts(elm, mdl)

                # Add init values from powerflow to initial guess
                self.set_init_guess(mdl, VarPowerFlowReferenceType.Pf, self.Sf[line_idx].real)
                self.set_init_guess(mdl, VarPowerFlowReferenceType.Qf, self.Sf[line_idx].imag)
                self.set_init_guess(mdl, VarPowerFlowReferenceType.Pt, self.St[line_idx].real)
                self.set_init_guess(mdl, VarPowerFlowReferenceType.Qt, self.St[line_idx].imag)
                line_idx += 1

                # Add model to system block
                self.sys_block.add(mdl)

                # Add variable to conservation equations of the bus
                f = bus_dict[elm.bus_from]
                t = bus_dict[elm.bus_to]

                setP(P, P_used, f, -mdl.E(VarPowerFlowReferenceType.Pf))
                setP(P, P_used, t, -mdl.E(VarPowerFlowReferenceType.Pt))
                if not elm.bus_from.is_dc:
                    setQ(Q, Q_used, f, -mdl.E(VarPowerFlowReferenceType.Qf))
                if not elm.bus_to.is_dc:
                    setQ(Q, Q_used, t, -mdl.E(VarPowerFlowReferenceType.Qt))
                    
            elif elm.rms_model is None or elm.rms_model.empty():
                self.logger.add_error("No RMS model",
                                     device_class=elm.device_type.value,
                                     device=elm.name)
                continue
            else:
                # Non-line branches (VSC, HVDC, etc.) - use existing model
                elm.rms_model.unify_blocks()
                mdl = elm.rms_model

                self.add_variables_to_compilation_dicts(elm, mdl)

                # Add init values from powerflow to initial guess
                if VarPowerFlowReferenceType.Pf in mdl.external_mapping:
                    self.set_init_guess(mdl, VarPowerFlowReferenceType.Pf, self.Sf[line_idx].real if line_idx < len(self.Sf) else 0.0)
                if VarPowerFlowReferenceType.Qf in mdl.external_mapping:
                    self.set_init_guess(mdl, VarPowerFlowReferenceType.Qf, self.Sf[line_idx].imag if line_idx < len(self.Sf) else 0.0)
                if VarPowerFlowReferenceType.Pt in mdl.external_mapping:
                    self.set_init_guess(mdl, VarPowerFlowReferenceType.Pt, self.St[line_idx].real if line_idx < len(self.St) else 0.0)
                if VarPowerFlowReferenceType.Qt in mdl.external_mapping:
                    self.set_init_guess(mdl, VarPowerFlowReferenceType.Qt, self.St[line_idx].imag if line_idx < len(self.St) else 0.0)
                line_idx += 1

                # Add model to system block
                self.sys_block.add(mdl)

                # Add variable to conservation equations of the bus
                f = bus_dict[elm.bus_from]
                t = bus_dict[elm.bus_to]

                if VarPowerFlowReferenceType.Pf in mdl.external_mapping:
                    setP(P, P_used, f, -mdl.E(VarPowerFlowReferenceType.Pf))
                if VarPowerFlowReferenceType.Pt in mdl.external_mapping:
                    setP(P, P_used, t, -mdl.E(VarPowerFlowReferenceType.Pt))
                if not elm.bus_from.is_dc and VarPowerFlowReferenceType.Qf in mdl.external_mapping:
                    setQ(Q, Q_used, f, -mdl.E(VarPowerFlowReferenceType.Qf))
                if not elm.bus_to.is_dc and VarPowerFlowReferenceType.Qt in mdl.external_mapping:
                    setQ(Q, Q_used, t, -mdl.E(VarPowerFlowReferenceType.Qt))

        # Process VSCs
        for i, elm in enumerate(self.grid.get_vsc()):
            if elm.rms_model is None or elm.rms_model is None or elm.rms_model.empty():
                self.logger.add_warning(f"VSC {elm.name} has no RMS model, skipping initialization")
                continue
            mdl = elm.rms_model
            mdl.unify_blocks()
            self.add_variables_to_compilation_dicts(elm, mdl)

            St_vsc = self.power_flow_results.St_vsc / self.grid.Sbase
            Sf_vsc = (self.power_flow_results.Pfn_vsc[i] + self.power_flow_results.Pfp_vsc[i]) / self.grid.Sbase

            # Fill init_guess
            if VarPowerFlowReferenceType.Pf in mdl.external_mapping:
                self.set_init_guess(mdl, VarPowerFlowReferenceType.Pf, Sf_vsc)
            if VarPowerFlowReferenceType.Pt in mdl.external_mapping:
                self.set_init_guess(mdl, VarPowerFlowReferenceType.Pt, St_vsc[i].real)
            if VarPowerFlowReferenceType.Qt in mdl.external_mapping:
                self.set_init_guess(mdl, VarPowerFlowReferenceType.Qt, St_vsc[i].imag)

            # Initialize Vdc from DC bus
            dc_bus_model = elm.bus_from.rms_model
            if VarPowerFlowReferenceType.Vdc in mdl.external_mapping and VarPowerFlowReferenceType.Vdc in dc_bus_model.external_mapping:
                dc_bus_vdc_var = dc_bus_model.external_mapping[VarPowerFlowReferenceType.Vdc]
                if dc_bus_vdc_var.uid in self.init_guess:
                    self.set_init_guess(mdl, VarPowerFlowReferenceType.Vdc, self.init_guess[dc_bus_vdc_var.uid])

            self.sys_block.add(mdl)

        # Process injections
        for elm in self.grid.get_injection_devices_iter():
            if elm.rms_model.empty():
                self.logger.add_error("No RMS model",
                                     device_class=elm.device_type.value,
                                     device=elm.name)
            else:
                bus_index = bus_dict[elm.bus]

                elm.rms_model.unify_blocks()
                mdl = block_deep_copy(elm.rms_model, self.grid.var_factory)

                self.add_variables_to_compilation_dicts(elm, mdl)

                # Fill init guess
                self.set_init_guess(mdl, VarPowerFlowReferenceType.P,
                                    np.real(self.power_flow_results.Sbus[bus_index] / self.grid.Sbase))
                if not elm.bus.is_dc:
                    self.set_init_guess(mdl, VarPowerFlowReferenceType.Q,
                                        np.imag(self.power_flow_results.Sbus[bus_index] / self.grid.Sbase))

                # Add to conservation equations
                k = bus_dict[elm.bus]
                setP(P, P_used, k, mdl.E(VarPowerFlowReferenceType.P))
                if not elm.bus.is_dc:
                    setQ(Q, Q_used, k, mdl.E(VarPowerFlowReferenceType.Q))

                # Find init values
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
                    self.logger.add_warning("PseudoTransient initialization not fully implemented")

                # Add events
                if mdl.event_dict is not None:
                    collect_events = {
                        key: {"times": [], "values": []}
                        for key in mdl.event_dict.keys()
                    }
                    rms_evts = [rms_evt for rms_evt in self.grid.rms_events if rms_evt.device_idtag == elm.idtag]
                    if len(rms_evts) != 0:
                        for rms_evt in rms_evts:
                            collect_events[rms_evt.parameter]["times"].append(rms_evt.time)
                            collect_events[rms_evt.parameter]["values"].append(rms_evt.value)
                        for param, events_info in collect_events.items():
                            default_value = elm.rms_model.event_dict[param]
                            if isinstance(default_value, Const) and default_value.value is None:
                                default_value = Const(0.0)
                            elif default_value is None:
                                default_value = Const(0.0)
                            mdl.event_dict[param] = piecewise(
                                time_var=self._glob_time,
                                t_events=np.array(events_info["times"]),
                                new_values=np.array(events_info["values"]),
                                default_value=default_value
                            )

                self.sys_block.add(mdl)

        # Add the nodal balance equations
        for i, elm in enumerate(self.grid.buses):
            mdl = block_deep_copy(elm.rms_model, grid.var_factory)
            if len(mdl.algebraic_eqs) == 0:
                if not P_used[i] and not Q_used[i]:
                    self.logger.add_error("Isolated bus", value=i)
                elif elm.is_dc:
                    self._algebraic_eqs.append(P[i])
                else:
                    self._algebraic_eqs.append(P[i])
                    self._algebraic_eqs.append(Q[i])

        # Rebuild compilation dicts
        self._rebuild_compilation_dicts()

        # Compile RHS and Jacobian
        self._compile_system()

    def add_variables_to_compilation_dicts(self, elm: ALL_DEV_TYPES, mdl: Block):
        """
        Add variables and parameters to the compilation dictionaries.
        :param elm: Device type to add variables to
        :param mdl: Block type to add variables to
        """
        block_item: Block
        for block_item in mdl.get_all_blocks():
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

            ep: Var
            for ep, const in block_item.parameters.items():
                self._compiler_names_dict[ep.uid] = f"{self.CONSTANT_PARAMS_NAME}[{self._n_params}]"
                self._alias_names_dict[ep.uid] = f"{self.CONSTANT_PARAMS_NAME}_{self._n_params}"
                self._uid2idx_params[ep.uid] = self._n_params
                self._constant_parameters.append(ep)
                self._parameters_values.append(const)
                self._n_params += 1

            for ep, eq in block_item.event_dict.items():
                self._compiler_names_dict[ep.uid] = f"{self.VARIABLE_PARAMS_NAME}[{self._n_event_params}]"
                self._alias_names_dict[ep.uid] = f"{self.VARIABLE_PARAMS_NAME}_{self._n_event_params}"
                self._uid2idx_event_params[ep.uid] = self._n_event_params
                self._variable_parameters.append(ep)
                self._event_parameters_eqs.append(eq)
                self._n_event_params += 1

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

    def _rebuild_compilation_dicts(self):
        """Rebuild compilation dictionaries after all models are added."""
        self._state_algeb_vars = list(self.sys_vars.values())

        self._n_state = len(self._state_vars)
        self._n_alg = len(self._algebraic_vars)
        self._n_algebraic = len(self._algebraic_eqs)

        self._compiler_names_dict: Dict[int, str] = dict()
        self._alias_names_dict: Dict[int, str] = dict()
        self._uid2idx_vars: Dict[int, int] = dict()
        self._uid2idx_event_params: Dict[int, int] = dict()
        self._uid2idx_params: Dict[int, int] = dict()
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

        for j, ep in enumerate(self._constant_parameters):
            self._compiler_names_dict[ep.uid] = f"{self.CONSTANT_PARAMS_NAME}[{j}]"
            self._alias_names_dict[ep.uid] = f"{self.CONSTANT_PARAMS_NAME}_{j}"
            self._uid2idx_params[ep.uid] = j

        for k, ep in enumerate(self._variable_parameters):
            self._compiler_names_dict[ep.uid] = f"{self.VARIABLE_PARAMS_NAME}[{k}]"
            self._alias_names_dict[ep.uid] = f"{self.VARIABLE_PARAMS_NAME}_{k}"
            self._uid2idx_event_params[ep.uid] = k

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
        for it, eq in enumerate(self._algebraic_eqs):
            for diff_var in self._diff_vars:
                eq = eq.subs({diff_var: Const(0)})
                eq = eq.simplify()
            self._stability_eqs.append(eq)

    def _compile_system(self):
        """Compile RHS and Jacobian using JIT Compiler."""
        timings = dict()
        print("Compiling Complex Phasor-based RMS using JIT Native Compiler...")

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
            dt_var=self._variable_parameters[-2] if len(self._variable_parameters) >= 2 else Var("dt"),
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
            print(f"Complex Phasor Model compiled with {self._n_vars} variables")
            print("\nCompilation timing summary:")
            for k, v in timings.items():
                print(f"  {k:30s}: {v:8.4f} s")
            print(f"\nTotal JIT compile time: {sum(timings.values()):.4f} s")

        variable_parameters_init = np.ones(self.get_variable_parameter_number())

        self._variable_parameters_values = self._event_params_fn(variable_parameters_init, 0.0)
        self._variable_parameters_values = self._event_params_fn(self._variable_parameters_values, 0.0)

        self._constant_params = np.array([const.value for const in self._parameters_values])

        if self.options.verbose > 0:
            print(f"\nTotal compile time: {sum(timings.values()):.4f} s")

    def set_init_guess(self, mdl: Block, reference_powerflow: VarPowerFlowReferenceType, val: float):
        """Add values from powerflow to initial guess."""
        var = mdl.external_mapping[reference_powerflow]
        self.init_guess[var.uid] = val

    def get_init_guess_info(self) -> pd.DataFrame:
        """Returns a df with uid, name, and initial value for the system variables."""
        vars_names = list()
        for key, value in self.init_guess.items():
            var_name = self.sys_vars[key].name
            vars_names.append((key, var_name, value))

        return pd.DataFrame(data=vars_names, columns=["key", "var_name", "value"])

    def get_device_vars_dict(self) -> Dict[ALL_DEV_TYPES, List[Var]]:
        """Get dictionary of device variables."""
        return self._vars_info

    def add_device_var(self, dev: ALL_DEV_TYPES, var: Var):
        """Associate a variable with a device."""
        var_list = self._vars_info.get(dev, None)

        if var_list is None:
            self._vars_info[dev] = [var]
        else:
            var_list.append(var)

    def get_var_idx(self, v: Var) -> int:
        """Get variable index."""
        return self._uid2idx_vars[v.uid]

    @property
    def vars_glob_name2uid(self):
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
        return self._uid2idx_vars

    @property
    def algebraic_vars(self):
        return self._algebraic_vars

    @property
    def state_and_algebraic_vars(self) -> List[Var]:
        variables = list()
        for lst in [self._state_vars, self._algebraic_vars]:
            for var in lst:
                variables.append(var)

        return variables

    @property
    def state_vars(self):
        return self._state_vars

    def get_all_vars_number(self) -> int:
        return self._n_vars

    def get_diff_var_number(self) -> int:
        return len(self._diff_vars)

    def get_algebraic_var_number(self) -> int:
        return len(self._algebraic_vars)

    def get_states_number(self) -> int:
        return self._n_state

    def get_variable_parameter_number(self) -> int:
        return len(self._variable_parameters)

    def get_x0(self) -> Vec:
        """Helper function to build the initial vector."""
        x = np.zeros(len(self._state_vars) + len(self._algebraic_vars))

        for uid, val in self.init_guess.items():
            if uid in self._uid2idx_vars:
                i = self._uid2idx_vars[uid]
                x[i] = val
        return x

    def update_variable_params(self, t: float, x_snapshot: Vec | None = None):
        """Update the variable parameters."""
        self._variable_parameters_values = self._event_params_fn(self._variable_parameters_values, t)

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
        return self._variable_parameters[-2] if len(self._variable_parameters) >= 2 else Var("dt")
    
    def get_dt_value(self):
        dt_value = self._variable_parameters_values[-2] if len(self._variable_parameters_values) >= 2 else 0.001
        return dt_value
