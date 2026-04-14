# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Module providing the EmtProblemDae class, which acts as the electrical
parser for the generic BaseProblem layer. It translates electrical components
(buses, branches, injections) into the unified DAE mathematical structure.
"""

from __future__ import annotations

import time
import numpy as np
import pandas as pd
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import numpy.linalg as la
from typing import Dict, List, Any, Set, Optional, Tuple
from itertools import chain

from VeraGridEngine.Devices import MultiCircuit
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Simulations.driver_template import DummySignal
from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Utils.Symbolic.symbolic import Var, piecewise, Const
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import (
    VarPowerFlowRefferenceType,
    ParamPowerFlowRefferenceType,
    DeviceType,
    EmtLineTypes,
    ConverterControlType,
    WindingType,
)
from VeraGridEngine.basic_structures import Logger, CxVec
from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.Templates.Emt.bergeron_line_emt_template import BergeronHistoryRuntime
from VeraGridEngine.Simulations.PowerFlow.power_flow_results_3ph import PowerFlowResults3Ph
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import PowerFlowResults
from VeraGridEngine.Simulations.EMT.initialization_emt import EmtInitializationReport, run_emt_native_initialization
from VeraGridEngine.Utils.Symbolic.explicit_initialization_symbolic import init_explicit_common, build_symbolic_vector_single_equation_compiler
from VeraGridEngine.Utils.Symbolic.compiled_functions import get_compiled_functions_cache_stats
from VeraGridEngine.Templates.Emt.bus_emt_template import get_bus_emt_algebraic_vars
from VeraGridEngine.IO.fmu.importer import (
    finalize_emt_fmu_cs_devices,
    finalize_emt_fmu_me_devices,
    queue_emt_fmu_cs_device,
    queue_emt_fmu_me_device,
)

from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import (
    EmtBoundaryUpdateProtocol,
    EmtProblemTemplate,
)


def _tic() -> float:
    """
    Returns the current performance counter time.
    """
    return time.perf_counter()


def _toc(t0: float) -> float:
    """
    Returns the elapsed time since t0.
    """
    return time.perf_counter() - t0


def _xfmr_connection_matrix(winding_tpe: WindingType) -> np.ndarray:
    """
    Return the 3x3 winding connection matrix used by the XFMR EMT template.

    :param winding_tpe: Transformer winding connection type.
    :return: 3x3 connection matrix in winding coordinates.
    """
    if winding_tpe in (WindingType.GroundedStar, WindingType.NeutralStar, WindingType.FloatingStar):
        return np.eye(3, dtype=float)
    else:
        if winding_tpe == WindingType.Delta:
            return np.array([
                [1.0, 0.0, -1.0],
                [-1.0, 1.0, 0.0],
                [0.0, -1.0, 1.0],
            ], dtype=float) / np.sqrt(3.0)
        else:
            return np.eye(3, dtype=float)


def _xfmr_phase_permutation_matrix(clock: int) -> np.ndarray:
    """
    Return the phase permutation matrix implied by the transformer vector group.

    :param clock: Transformer vector group clock number.
    :return: 3x3 phase permutation matrix.
    """
    shift: int = (int(clock) // 4) % 3
    if shift == 0:
        return np.eye(3, dtype=float)
    else:
        if shift == 1:
            return np.array([
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
                [1.0, 0.0, 0.0],
            ], dtype=float)
        else:
            return np.array([
                [0.0, 0.0, 1.0],
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
            ], dtype=float)


class EmtTopologyError(Exception):
    """
    Exception raised when EMT topology validation fails.
    This includes orphaned in_vars/out_vars and floating bus phases.
    """

    def __init__(self, message: str):
        """
        :param message: Descriptive error message indicating the topology issue.
        """
        self.message = message
        super().__init__(self.message)


def _unique_keep_order(seq: List[Var]) -> List[Var]:
    """
    Remove duplicated variables by UID while preserving the first appearance order.

    :param seq: Input variable sequence.
    :return: Deduplicated variable sequence.
    """
    seen: Set[int] = set()
    out: List[Var] = list()

    for item in seq:
        if item.uid in seen:
            pass
        else:
            seen.add(item.uid)
            out.append(item)

    return out

def _deduplicate_block_entities(block: Block)->None:
    """
    Removes duplicated symbolic objects within the block by UID
    while preserving their first appearance order.
    """


    block.state_vars = _unique_keep_order(block.state_vars)
    block.algebraic_vars = _unique_keep_order(block.algebraic_vars)
    block.diff_vars = _unique_keep_order(block.diff_vars)

def _get_mode_event_sort_key(event: Tuple[float, float, bool]) -> float:
    """
    Return the sorting key of a mode event.

    :param event: Mode event tuple (time, value, force_step_alignment).
    :return: Event time.
    """
    return event[0]

def _is_time_aligned(t_curr: float, event_time: float) -> bool:
    """
    Return whether the current solver time is aligned with the event time.

    :param t_curr: Current solver time.
    :param event_time: Scheduled event time.
    :return: True if the current time is aligned with the event time.
    """
    time_tol = 10.0 * np.finfo(np.float64).eps * max(1.0, abs(event_time))
    return bool(abs(t_curr - event_time) <= time_tol)

def _get_next_forced_mode_event_time(
        scheduled_mode_events: Dict[int, List[Tuple[float, float, bool]]],
        t_prev: float,
        t_target: float,
) -> Optional[float]:
    """
    Return the earliest forced-alignment mode event time in the interval
    (t_prev, t_target].

    :param t_prev: Previous solver time.
    :param t_target: Nominal target time.
    :return: Earliest forced event time or None.
    """
    next_time: Optional[float] = None

    for _, event_list in scheduled_mode_events.items():
        event_idx: int = 0

        while event_idx < len(event_list):
            event_time: float = event_list[event_idx][0]
            force_step_alignment: bool = event_list[event_idx][2]

            if force_step_alignment and (t_prev < event_time <= t_target):
                if next_time is None:
                    next_time = event_time
                else:
                    if event_time < next_time:
                        next_time = event_time
                    else:
                        pass
            else:
                pass

            event_idx += 1

    return next_time

def _get_block_name(mdl: Block) -> str:
    """
    Return the block name used for logging.

    :param mdl: Block to inspect.
    :return: Block name.
    """
    if mdl.name is None:
        return "unknown"
    else:
        return str(mdl.name)


def _get_grid_runtime_events(grid: MultiCircuit) -> List[Any]:
    """
    Return the list of scheduled runtime events available in the grid.

    :param grid: MultiCircuit instance.
    :return: List of scheduled runtime events.
    """

    return grid.emt_events

def _get_bus_v_list(
        grid: MultiCircuit,
        bus_block: Block,
        ph_v_keys: List[VarPowerFlowRefferenceType]
) -> List[Any]:
    """
    Return the ordered list of bus phase voltages, using None for missing phases.

    :param grid: MultiCircuit instance.
    :param bus_block: Bus symbolic block.
    :param ph_v_keys: Ordered list of phase voltage keys.
    :return: Ordered list of bus phase voltage expressions or None.
    """
    out: List[Any] = list()

    for key in ph_v_keys:
        vk = bus_block.E(key)

        if vk is None:
            out.append(None)
        else:
            out.append(vk)

    return out

def _get_external_mapping(mdl: Block) -> Optional[Dict[Any, Var]]:
    external_mapping: Optional[Dict[Any, Var]] = mdl.external_mapping
    if external_mapping is None:
        return None
    else:
        return external_mapping

# USE AS REFERENCE TO VALIDATE THAT ALL MODELS HAVE THE SAME NUMBER OF PHASES THAN THE STATIC DEVICES!
# def _get_expected_pi_line_terminal_refs(ph_mask: List[bool]) -> List[VarPowerFlowRefferenceType]:
#     """
#     Build the ordered terminal-voltage references for the active pi-line phases.
#
#     :param ph_mask: Physical line phase mask in NABC order.
#     :return: Ordered ``vf_*`` and ``vt_*`` references for the active phases only.
#     """
#     vf_refs: List[VarPowerFlowRefferenceType] = list([
#         VarPowerFlowRefferenceType.vf_N,
#         VarPowerFlowRefferenceType.vf_A,
#         VarPowerFlowRefferenceType.vf_B,
#         VarPowerFlowRefferenceType.vf_C,
#     ])
#     vt_refs: List[VarPowerFlowRefferenceType] = list([
#         VarPowerFlowRefferenceType.vt_N,
#         VarPowerFlowRefferenceType.vt_A,
#         VarPowerFlowRefferenceType.vt_B,
#         VarPowerFlowRefferenceType.vt_C,
#     ])
#
#     ordered_refs: List[VarPowerFlowRefferenceType] = list()
#
#     for idx, is_active in enumerate(ph_mask):
#         if is_active:
#             ordered_refs.append(vf_refs[idx])
#         else:
#             pass
#
#     for idx, is_active in enumerate(ph_mask):
#         if is_active:
#             ordered_refs.append(vt_refs[idx])
#         else:
#             pass
#
#     return ordered_refs
#
#
# def _normalize_pi_line_phase_layout(branch: Any, grid: MultiCircuit) -> None:
#     """
#     Rebuild the standard pi-line template when its symbolic phase layout does not
#     match the physical branch connection mask.
#
#     The EMT parameter mapper writes reduced branch matrices into the fixed NABC
#     API map using ``branch.ys``. After the recent API change, callers can create
#     a pi-line template with a phase mask that does not match ``branch.ys``. When
#     that happens, the symbolic block keeps terminal inputs for non-existent bus
#     phases and later substitutions introduce ``None`` or unresolved UIDs.
#
#     This helper keeps the public explicit-mask API in place, but re-aligns the
#     standard pi-line block with the physical branch mask right before the EMT
#     problem flattens the device into the global system.
#
#     :param branch: Grid branch device.
#     :param grid: Parent circuit, used for the shared variable factory.
#     :return: None.
#     """
#     mdl: Any = branch.emt_model
#     api_obj_mapping: Any = mdl.api_obj_mapping
#
#     if not isinstance(api_obj_mapping, dict):
#         return
#     else:
#         pass
#
#     if ParamPowerFlowRefferenceType.Rnn not in api_obj_mapping:
#         return
#     else:
#         pass
#
#     ph_mask: List[bool] = list([
#         bool(branch.ys.phN),
#         bool(branch.ys.phA),
#         bool(branch.ys.phB),
#         bool(branch.ys.phC),
#     ])
#     expected_refs: List[VarPowerFlowRefferenceType] = _get_expected_pi_line_terminal_refs(ph_mask)
#     tracked_refs: Set[VarPowerFlowRefferenceType] = set([
#         VarPowerFlowRefferenceType.vf_N,
#         VarPowerFlowRefferenceType.vf_A,
#         VarPowerFlowRefferenceType.vf_B,
#         VarPowerFlowRefferenceType.vf_C,
#         VarPowerFlowRefferenceType.vt_N,
#         VarPowerFlowRefferenceType.vt_A,
#         VarPowerFlowRefferenceType.vt_B,
#         VarPowerFlowRefferenceType.vt_C,
#     ])
#     current_refs: List[VarPowerFlowRefferenceType] = list()
#
#     for in_var in mdl.in_vars:
#         if in_var.ref in tracked_refs:
#             current_refs.append(in_var.ref)
#         else:
#             pass
#
#     if current_refs != expected_refs:
#         branch.emt_model = get_pi_line_emt_template(
#             vf=grid.var_factory,
#             phN=ph_mask[0],
#             phA=ph_mask[1],
#             phB=ph_mask[2],
#             phC=ph_mask[3],
#             name=mdl.name,
#         ).block
#     else:
#         pass


class EmtProblemDae(EmtProblemTemplate):
    """
    Electrical parser layer for the EMT DAE Problem.

    Responsibilities:
      - Traverses the MultiCircuit to extract electrical devices.
      - Constructs nodal KCL balances per phase.
      - Processes external piecewise events into the unified block.
      - Maintains mapping between physical devices and symbolic variables.
      - Delegates all mathematical and indexing plumbing to BaseProblem.
      - Initializes PF-based guesses AND evaluates mdl.init_eqs explicitly (Explicit init).
    """

    def __init__(self,
                 grid: MultiCircuit,
                 options: EmtOptions,
                 pf_results_3ph: PowerFlowResults3Ph | None = None,
                 pf_results: PowerFlowResults | None = None,
                 progress_signal: DummySignal | None = None,
                 progress_text: DummySignal | None = None, )-> None:
        """
        Initializes the EMT Problem by parsing the grid and passing the
        resulting mathematical block to the BaseProblem constructor.
        :param grid:
        :param options:
        :param pf_results_3ph:
        :param pf_results:
        """
        self.logger = Logger()
        self.grid = grid
        self.options = options
        self.power_flow_results_3ph = pf_results_3ph
        self.power_flow_results = pf_results

        self._vars_info: Dict[ALL_DEV_TYPES, List[Var]] = dict()
        self._vars_glob_name2uid: Dict[str, int] = dict()
        self._vars2device: Dict[int, ALL_DEV_TYPES] = dict()
        self._temp_init_guess: Dict[int, float] = dict()
        self._temp_diff_init_guess: Dict[int, float] = dict()
        self.initialization_report: EmtInitializationReport | None = None
        self.build_report: Dict[str, float] = dict()

        self._scheduled_mode_events: Dict[int, List[Tuple[float, float, bool]]] = dict()
        self._mode_event_cursor: Dict[int, int] = dict()
        self._runtime_parameter_eqs0: List[Any] = list()
        self._event_parameter_device_idtags: Dict[int, str] = dict()
        self._continuous_event_parameter_uids: Set[int] = set()
        self._discrete_event_parameter_uids: Set[int] = set()
        self._active_events_group: EmtEventsGroup | None = None

        # for init_explicit
        self._models_with_init_eqs: List[Block] = []
        self._models_with_diff_init_eqs: List[Block] = []
        self._models_with_init_eqs_seen: Set[int] = set()
        self._models_with_diff_init_eqs_seen: Set[int] = set()

        sys_block = Block(children=[], in_vars=[])
        glob_time = Var(self.TIME_NAME)

        self.history_models: List[BergeronHistoryRuntime] = list()
        self.step_counter: int = 0
        self._fmu_cs_adapters: List[Any] = list()
        self._pending_fmu_cs_devices: List[Tuple[Any, Block]] = list()
        self._fmu_me_adapters: List[Any] = list()
        self._pending_fmu_me_devices: List[Tuple[Any, Block]] = list()

        t_build = _tic()
        t_phase_start: float = t_build
        cache_stats_before: Dict[str, float] = get_compiled_functions_cache_stats()

        validate_models_s: float = _toc(t_phase_start)
        t_phase_start = _tic()

        # build on local sys_block
        self._build_structure_and_collect(sys_block, grid, glob_time)
        structure_collect_s: float = _toc(t_phase_start)
        t_phase_start = _tic()

        sys_block.unify_blocks()
        _deduplicate_block_entities(sys_block)
        unify_blocks_s: float = _toc(t_phase_start)
        t_phase_start = _tic()

        self._validate_connections()
        validate_connections_s: float = _toc(t_phase_start)
        t_phase_start = _tic()

        # initialize template with the complete block
        super().__init__(sys_block=sys_block, glob_time=glob_time, progress_signal=progress_signal,
                         progress_text=progress_text)
        template_init_s: float = _toc(t_phase_start)
        t_phase_start = _tic()

        # Mark retained runtime parameters:
        #   - scheduled mode parameters
        #   - Bergeron history parameters
        mode_parameters: List[Var] = self._collect_runtime_mode_parameters()
        if len(mode_parameters) > 0:
            self.set_runtime_mode_parameters(mode_parameters)
        else:
            pass

        # Runtime parameter indices may have changed after repartitioning,
        # so Bergeron runtimes must bind their parameter indices afterwards.
        for rt in self.history_models:
            rt.setup_indices(
                uid2idx_vars=self.uid2idx_vars,
                uid2idx_event_params=self.uid2idx_event_params,
                params_offset=0,
            )

        self._runtime_parameter_eqs0 = list(self._runtime_all_eqs_source)
        finalize_emt_fmu_cs_devices(self)
        finalize_emt_fmu_me_devices(self)

        if len(self._runtime_mode_parameters) > 0:
            self._initialize_mode_event_state()
        else:
            pass
        runtime_partition_s: float = _toc(t_phase_start)
        t_phase_start = _tic()

        # 1) PF guesses
        self.init_guess.update(self._temp_init_guess)
        self.diff_init_guess.update(self._temp_diff_init_guess)
        if self.progress_signal is not None:
            self.progress_signal.emit(10)

        # 2) explicit init guesses initialization
        self._run_explicit_initialization()
        explicit_init_s: float = _toc(t_phase_start)
        t_phase_start = _tic()
        self.initialization_report = run_emt_native_initialization(problem=self, options=self.options)
        native_init_s: float = _toc(t_phase_start)
        t_phase_start = _tic()

        if self.progress_signal is not None:
            self.progress_signal.emit(20)

        # EMT event groups are activated only after the initialization stage.
        # Some runtime parameters start as Const(None) placeholders and are
        # resolved during explicit/native initialization. Wrapping them in
        # piecewise expressions before that would preserve the undefined default
        # and break the initial runtime-parameter evaluation.
        self.set_events_group(None)
        events_group_finalize_s: float = _toc(t_phase_start)

        t_done = _toc(t_build)
        cache_stats_after: Dict[str, float] = get_compiled_functions_cache_stats()
        compiled_function_cache_delta: float = cache_stats_after.get("entry_count", 0.0) - cache_stats_before.get("entry_count", 0.0)
        native_structural_cold_s: float = 0.0
        native_numeric_refresh_s: float = 0.0

        if self.initialization_report is None:
            native_structural_cold_s = 0.0
            native_numeric_refresh_s = 0.0
        else:
            native_structural_cold_s = float(self.initialization_report.reduced_system_build_s)
            native_numeric_refresh_s = (
                float(self.initialization_report.runtime_param_build_s)
                + float(self.initialization_report.constant_param_build_s)
                + float(self.initialization_report.initial_residual_eval_s)
                + float(self.initialization_report.newton_elapsed_s)
                + float(self.initialization_report.pseudo_transient_elapsed_s)
                + float(self.initialization_report.dx0_completion_s)
            )

        structural_cold_s: float = (
            validate_models_s
            + structure_collect_s
            + unify_blocks_s
            + validate_connections_s
            + template_init_s
            + runtime_partition_s
            + explicit_init_s
            + native_structural_cold_s
        )
        numeric_refresh_s: float = native_numeric_refresh_s + events_group_finalize_s

        self.build_report = dict(
            validate_models_s=validate_models_s,
            structure_collect_s=structure_collect_s,
            unify_blocks_s=unify_blocks_s,
            validate_connections_s=validate_connections_s,
            template_init_s=template_init_s,
            runtime_partition_s=runtime_partition_s,
            explicit_init_s=explicit_init_s,
            native_init_s=native_init_s,
            events_group_finalize_s=events_group_finalize_s,
            structural_cold_s=structural_cold_s,
            numeric_refresh_s=numeric_refresh_s,
            native_structural_cold_s=native_structural_cold_s,
            native_numeric_refresh_s=native_numeric_refresh_s,
            compiled_function_cache_delta=compiled_function_cache_delta,
            persistent_init_cache_hit=1.0 if (self.initialization_report is not None and self.initialization_report.persistent_cache_hit) else 0.0,
            persistent_init_cache_load_s=0.0 if self.initialization_report is None else float(self.initialization_report.persistent_cache_load_s),
            persistent_init_cache_store_s=0.0 if self.initialization_report is None else float(self.initialization_report.persistent_cache_store_s),
            total_s=t_done,
        )

        if options.verbose > 0:
            self.logger.add_debug(f"init guess = {self.init_guess}")
            self.logger.add_debug(f"diff init guess = {self.diff_init_guess}")
            if self.initialization_report is None:
                pass
            else:
                self.logger.add_debug(
                    f"EMT initialization used {self.initialization_report.method_used} | "
                    f"status={self.initialization_report.status.name} | "
                    f"res0={self.initialization_report.initial_residual_inf:.3e} | "
                    f"resf={self.initialization_report.final_residual_inf:.3e} | "
                    f"newton={self.initialization_report.newton_iterations} | "
                    f"ptc={self.initialization_report.pseudo_transient_steps} | "
                    f"auto_dx0={self.initialization_report.automatic_dx0_count}"
                )
            self.logger.add_debug(
                f"EMT electrical problem parsed in {t_done:.4f}s | "
                f"vars={self._n_vars} (state={self._n_state}, alg={self._n_alg}) | "
                f"eqs(state={len(self._state_eqs)}, alg={len(self._algebraic_eqs)})"
            )

    # ---------------------------------------------------------------------
    # init_eqs registration + explicit init execution
    # ---------------------------------------------------------------------
    def _register_init_model(self, mdl: Block) -> None:
        """
        Register a block for explicit initialization if it defines init_eqs.

        :param mdl: Block to inspect.
        :return: None
        """
        init_eqs = mdl.init_eqs

        if init_eqs is None or len(init_eqs) == 0:
            pass
        else:
            mid: int = id(mdl)

            if mid in self._models_with_init_eqs_seen:
                pass
            else:
                self._models_with_init_eqs_seen.add(mid)
                self._models_with_init_eqs.append(mdl)

    def get_build_report(self) -> Dict[str, float]:
        """
        Return the EMT problem build timing report.

        :return: Build timing report.
        :rtype: Dict[str, float]
        """
        return dict(self.build_report)

    def _register_diff_init_model(self, mdl: Block) -> None:
        """
        Register a block for explicit differential initialization if it defines diff_init_eqs.

        :param mdl: Block to inspect.
        :return: None
        """
        diff_init_eqs = mdl.diff_init_eqs

        if diff_init_eqs is None or len(diff_init_eqs) == 0:
            pass
        else:
            mid: int = id(mdl)

            if mid in self._models_with_diff_init_eqs_seen:
                pass
            else:
                self._models_with_diff_init_eqs_seen.add(mid)
                self._models_with_diff_init_eqs.append(mdl)

    def _run_explicit_initialization(self)-> None:
        """
        Run explicit initialization for every block that defines initialization equations.


        :return: None
        """

        if len(self._models_with_init_eqs) == 0 and len(self._models_with_diff_init_eqs) == 0:
            return

        # sys_vars dict (uid -> Var), size = n_vars
        sys_vars: Dict[int, Var] = {v.uid: v for v in (self._state_vars + self._algebraic_vars)}
        sys_diff_vars: Dict[int, Var] = {dv.uid: dv for dv in self._diff_vars}
        compile_single_equation = build_symbolic_vector_single_equation_compiler(
            compiler_names_dict=self._compiler_names_dict,
            alias_names_dict=self._alias_names_dict,
            vars_name=self.VARS_NAME,
            diff_name=self.DIFF_NAME,
            event_params_name=self.VARIABLE_PARAMS_NAME,
            params_name=self.CONSTANT_PARAMS_NAME,
        )

        seen_blocks: set[int] = set()

        for mdl in chain(self._models_with_init_eqs, self._models_with_diff_init_eqs):
            mdl_id = id(mdl)

            if mdl_id not in seen_blocks:
                seen_blocks.add(mdl_id)

                try:
                    params_array: np.ndarray = np.zeros(len(self._constant_parameters))

                    for param, const in mdl.parameters.items():
                        param_idx: int | None = self.uid2idx_params.get(param.uid, None)

                        if param_idx is None:
                            params_array = params_array
                        else:
                            params_array[param_idx] = const.value

                    self.init_guess, self.diff_init_guess = init_explicit_common(
                        mdl=mdl,
                        sys_vars=sys_vars,
                        sys_diff_vars=sys_diff_vars,
                        variable_parameters=self._variable_parameters,
                        event_parameters_eqs=self._event_parameters_eqs,
                        constant_parameters=self._constant_parameters,
                        init_guess=self.init_guess,
                        diff_init_guess=self.diff_init_guess,
                        uid2idx_vars=self.uid2idx_vars,
                        uid2idx_diff=self.uid2idx_diff,
                        uid2idx_params=self.uid2idx_params,
                        uid2idx_event_params=self.uid2idx_event_params,
                        params_array=params_array,
                        compile_single_equation=compile_single_equation,
                        verbose=bool(self.options.verbose > 0),
                    )


                    for event_var in mdl.event_dict.keys():
                        event_idx: int | None = self.uid2idx_event_params.get(event_var.uid, None)

                        if event_idx is None:
                            mdl.event_dict[event_var] = mdl.event_dict[event_var]
                        else:
                            mdl.event_dict[event_var] = self._event_parameters_eqs[event_idx]
                            self._runtime_parameter_eqs0[event_idx] = self._event_parameters_eqs[event_idx]
                except Exception as e:
                    block_name: str = _get_block_name(mdl)
                    error_detail = f"{type(e).__name__}: {str(e)}"

                    self.logger.add_warning(
                        msg="EMT explicit initialization failed for block.",
                        device=block_name,
                        value=error_detail,
                        expected_value="Successful explicit initialization",
                        device_class="EMT",
                        device_property="init_explicit"
                    )

                    if self.options.verbose > 0:
                        self.logger.add_debug(
                            f"[EMT][init_explicit] failed for block '{block_name}'. Error: {error_detail}"
                        )

                        print(
                            f"EMT explicit initialization failed for block {block_name}. "
                            f"Error detail: {error_detail}"
                        )


        self._build_runtime_param_vectors()

    def _validate_connections(self) -> None:
        """
        Validate EMT topology connectivity.

        Checks that each phase exposed by a bus must be connected to at least 2 elements
        (branches or injections). A floating phase indicates an open circuit.

        The phase connection mapping is:
        - Branch in_vars with ref vf_N/A/B/C connect to bus_from's v_N/A/B/C
        - Branch in_vars with ref vt_N/A/B/C connect to bus_to's v_N/A/B/C
        - Injection device in_vars with ref v_N/A/B/C connect to their bus's v_N/A/B/C

        :raises EmtTopologyError: If topology inconsistencies are found.
        """
        phase_ref_to_bus_phase = {
            VarPowerFlowRefferenceType.vf_N: VarPowerFlowRefferenceType.v_N,
            VarPowerFlowRefferenceType.vf_A: VarPowerFlowRefferenceType.v_A,
            VarPowerFlowRefferenceType.vf_B: VarPowerFlowRefferenceType.v_B,
            VarPowerFlowRefferenceType.vf_C: VarPowerFlowRefferenceType.v_C,
            VarPowerFlowRefferenceType.vt_N: VarPowerFlowRefferenceType.v_N,
            VarPowerFlowRefferenceType.vt_A: VarPowerFlowRefferenceType.v_A,
            VarPowerFlowRefferenceType.vt_B: VarPowerFlowRefferenceType.v_B,
            VarPowerFlowRefferenceType.vt_C: VarPowerFlowRefferenceType.v_C,
        }

        branch_phase_refs = {
            VarPowerFlowRefferenceType.vf_N,
            VarPowerFlowRefferenceType.vf_A,
            VarPowerFlowRefferenceType.vf_B,
            VarPowerFlowRefferenceType.vf_C,
            VarPowerFlowRefferenceType.vt_N,
            VarPowerFlowRefferenceType.vt_A,
            VarPowerFlowRefferenceType.vt_B,
            VarPowerFlowRefferenceType.vt_C,
        }

        ac_phases = [
            VarPowerFlowRefferenceType.v_N,
            VarPowerFlowRefferenceType.v_A,
            VarPowerFlowRefferenceType.v_B,
            VarPowerFlowRefferenceType.v_C,
        ]

        bus_phase_connections: Dict[Tuple[Any, VarPowerFlowRefferenceType], Set[str]] = dict()
        for bus in self.grid.buses:
            for phase in ac_phases:
                bus_phase_connections[(bus, phase)] = set()

        vsc_ac_phase_refs = {
            VarPowerFlowRefferenceType.v_A,
            VarPowerFlowRefferenceType.v_B,
            VarPowerFlowRefferenceType.v_C,
        }

        for br in self.grid.get_branches_iter(add_vsc=True, add_hvdc=True, add_switch=True):
            try:
                br_emt_model = br.emt_model
            except AttributeError:
                br_emt_model = None

            if br_emt_model is not None:
                try:
                    br_bus_from = br.bus_from
                    br_bus_to = br.bus_to
                except AttributeError:
                    pass
                else:
                    is_bergeron = br_emt_model.name == EmtLineTypes.Bergeron.value

                    if is_bergeron:
                        try:
                            br_ys = br.ys
                        except AttributeError:
                            br_ys = None

                        if br_ys is not None:
                            if br_ys.phN:
                                bus_phase_connections[(br_bus_from, VarPowerFlowRefferenceType.v_N)].add(f"branch_from:{br.name}")
                                bus_phase_connections[(br_bus_to, VarPowerFlowRefferenceType.v_N)].add(f"branch_to:{br.name}")
                            else:
                                pass

                            if br_ys.phA:
                                bus_phase_connections[(br_bus_from, VarPowerFlowRefferenceType.v_A)].add(f"branch_from:{br.name}")
                                bus_phase_connections[(br_bus_to, VarPowerFlowRefferenceType.v_A)].add(f"branch_to:{br.name}")
                            else:
                                pass

                            if br_ys.phB:
                                bus_phase_connections[(br_bus_from, VarPowerFlowRefferenceType.v_B)].add(f"branch_from:{br.name}")
                                bus_phase_connections[(br_bus_to, VarPowerFlowRefferenceType.v_B)].add(f"branch_to:{br.name}")
                            else:
                                pass

                            if br_ys.phC:
                                bus_phase_connections[(br_bus_from, VarPowerFlowRefferenceType.v_C)].add(f"branch_from:{br.name}")
                                bus_phase_connections[(br_bus_to, VarPowerFlowRefferenceType.v_C)].add(f"branch_to:{br.name}")
                            else:
                                pass
                        else:
                            pass
                    else:
                        for in_var in br_emt_model.in_vars:
                            if in_var.ref in branch_phase_refs:
                                bus_phase = phase_ref_to_bus_phase[in_var.ref]

                                if in_var.ref in {
                                    VarPowerFlowRefferenceType.vf_N,
                                    VarPowerFlowRefferenceType.vf_A,
                                    VarPowerFlowRefferenceType.vf_B,
                                    VarPowerFlowRefferenceType.vf_C,
                                }:
                                    bus_phase_connections[(br_bus_from, bus_phase)].add(f"branch_from:{br.name}")
                                elif in_var.ref in {
                                    VarPowerFlowRefferenceType.vt_N,
                                    VarPowerFlowRefferenceType.vt_A,
                                    VarPowerFlowRefferenceType.vt_B,
                                    VarPowerFlowRefferenceType.vt_C,
                                }:
                                    bus_phase_connections[(br_bus_to, bus_phase)].add(f"branch_to:{br.name}")
                                else:
                                    pass
                            elif in_var.ref in vsc_ac_phase_refs:
                                if br_bus_to.is_dc:
                                    bus_phase_connections[(br_bus_from, in_var.ref)].add(f"branch_from:{br.name}")
                                else:
                                    bus_phase_connections[(br_bus_to, in_var.ref)].add(f"branch_to:{br.name}")
                            else:
                                pass
            else:
                pass

        for inj in self.grid.get_injection_devices_iter():
            try:
                inj_emt_model = inj.emt_model
            except AttributeError:
                inj_emt_model = None

            if inj_emt_model is not None:
                try:
                    inj_bus = inj.bus
                except AttributeError:
                    pass
                else:
                    for in_var in inj_emt_model.in_vars:
                        if in_var.ref in ac_phases:
                            bus_phase_connections[(inj_bus, in_var.ref)].add(f"injection:{inj.name}")
                        else:
                            pass
            else:
                pass

        floating_phases: List[str] = list()
        for bus in self.grid.buses:
            if not bus.is_dc:
                bus_out_refs = {v.ref for v in bus.emt_model.out_vars}
                for phase in ac_phases:
                    connections = bus_phase_connections.get((bus, phase), set())
                    if phase in bus_out_refs and len(connections) < 2:
                        floating_phases.append(
                            f"  - Bus '{bus.name}' phase '{phase.value}' is floating "
                            f"(connected to {len(connections)} element(s): {connections})"
                        )
                    else:
                        pass
            else:
                pass

        if floating_phases:
            error_msg = (
                "TopologyError: Floating bus phases detected "
                "(each phase must be connected to at least 2 elements):\n"
            )
            error_msg += "\n".join(floating_phases)
            raise EmtTopologyError(error_msg)
        else:
            pass

    def _process_device_model(self, dev: Any, sys_block: Block, grid: MultiCircuit, glob_time: Var) -> Block:
        """
        Register a device EMT model into the global system block.

        The device model is flattened before being attached to the system block.
        Some wrapper-style models store ``api_obj_mapping`` in nested child blocks,
        while ``unify_blocks()`` does not propagate that metadata to the top-level
        block. For that reason, the mapping is rebuilt first and restored on the
        device block before flattening.

        :param dev: Device object from the grid.
        :param sys_block: Main DAE system block.
        :param grid: MultiCircuit instance.
        :param glob_time: Global time variable.
        :return: Unified device block.
        """
        mdl: Block = dev.emt_model

        resolved_api_mapping: Dict[ParamPowerFlowRefferenceType, Any] = self._collect_api_obj_mapping(mdl)
        if len(resolved_api_mapping) > 0:
            mdl.api_obj_mapping = resolved_api_mapping
        else:
            pass

        mdl.unify_blocks()

        self._register_runtime_event_parameters(dev=dev, mdl=mdl)
        self._add_model_to_system_mappings(dev, mdl)
        queue_emt_fmu_cs_device(self, dev, mdl)
        queue_emt_fmu_me_device(self, dev, mdl)
        sys_block.add(mdl)

        self._register_init_model(mdl)
        self._register_diff_init_model(mdl)

        return mdl

    def _collect_api_obj_mapping(self, mdl: Block) -> Dict[ParamPowerFlowRefferenceType, Any]:
        """
        Collect the API object mapping from a block hierarchy.

        Wrapper models may keep the parameter mapping in nested child blocks.
        This method traverses the hierarchy and merges the first occurrence
        of each mapping key so the top-level block preserves the metadata
        required by PF-derived parameter assignment.

        :param mdl: Root block to inspect.
        :return: Flattened API object mapping.
        """
        mapping: Dict[ParamPowerFlowRefferenceType, Any] = dict()
        stack: List[Block] = list([mdl])
        visited: Set[int] = set()

        while len(stack) > 0:
            block: Block = stack.pop()
            block_id: int = id(block)

            if block_id not in visited:
                visited.add(block_id)

                local_mapping: Any = block.api_obj_mapping
                if isinstance(local_mapping, dict):
                    for key, val in local_mapping.items():
                        if key not in mapping:
                            mapping[key] = val
                        else:
                            pass
                else:
                    pass

                for child in block.children:
                    stack.append(child)
            else:
                pass

        return mapping

    def _to_const(self, value: Any) -> Const:
        """
        Convert a numeric value into a ``Const`` symbolic expression.

        :param value: Numeric or already-constant value.
        :return: Constant symbolic expression.
        """
        if isinstance(value, Const):
            return value
        else:
            return Const(float(value))

    def _assign_api_obj_param_if_present(
            self,
            mdl: Block,
            key: ParamPowerFlowRefferenceType,
            value: Any
    ) -> None:
        """
        Assign a mapped model parameter when the mapping key exists.

        Some device models do not expose every optional API mapping entry.
        This method performs a defensive assignment and keeps the original
        semantics of silently skipping unavailable parameters.

        :param mdl: Device symbolic block.
        :param key: Parameter mapping key.
        :param value: Value to assign.
        :return: None.
        """
        api_obj_mapping: Any = mdl.api_obj_mapping

        if isinstance(api_obj_mapping, dict):
            target: Any | None = api_obj_mapping.get(key, None)

            if target is not None:
                mdl.parameters[target] = self._to_const(value)
            else:
                pass
        else:
            pass
    # ---------------------------------------------------------------------
    # BUILD STRUCTURE
    # ---------------------------------------------------------------------
    def _build_structure_and_collect(
            self,
            sys_block: Block,
            grid: MultiCircuit,
            glob_time: Var
    ) -> None:
        """
        Build the EMT system structure and collect all algebraic KCL equations.

        This routine assembles the EMT nodal equations in abc coordinates.
        The unknowns are the bus phase voltages and the algebraic equations
        are the KCL balances at each bus-phase.

        The function preserves the original sign conventions:
        - Branch currents are defined as leaving the bus, therefore they are
          subtracted from the KCL accumulator.
        - Injection currents are defined as entering the bus, therefore they are
          added to the KCL accumulator.

        :param sys_block: Block containing the full system DAE.
        :param grid: Network model to assemble.
        :param glob_time: Global simulation time variable.
        :return: None.
        """
        bus_dict: Dict[Any, int] = dict()

        ph_v_keys: List[VarPowerFlowRefferenceType] = list([
            VarPowerFlowRefferenceType.v_N,
            VarPowerFlowRefferenceType.v_A,
            VarPowerFlowRefferenceType.v_B,
            VarPowerFlowRefferenceType.v_C,
        ])
        inj_i_keys: List[VarPowerFlowRefferenceType] = list([
            VarPowerFlowRefferenceType.i_N,
            VarPowerFlowRefferenceType.i_A,
            VarPowerFlowRefferenceType.i_B,
            VarPowerFlowRefferenceType.i_C,
        ])
        br_if_keys: List[VarPowerFlowRefferenceType] = list([
            VarPowerFlowRefferenceType.if_N,
            VarPowerFlowRefferenceType.if_A,
            VarPowerFlowRefferenceType.if_B,
            VarPowerFlowRefferenceType.if_C,
        ])
        br_it_keys: List[VarPowerFlowRefferenceType] = list([
            VarPowerFlowRefferenceType.it_N,
            VarPowerFlowRefferenceType.it_A,
            VarPowerFlowRefferenceType.it_B,
            VarPowerFlowRefferenceType.it_C,
        ])
        br_vf_keys: List[VarPowerFlowRefferenceType] = list([
            VarPowerFlowRefferenceType.vf_N,
            VarPowerFlowRefferenceType.vf_A,
            VarPowerFlowRefferenceType.vf_B,
            VarPowerFlowRefferenceType.vf_C,
        ])
        br_vt_keys: List[VarPowerFlowRefferenceType] = list([
            VarPowerFlowRefferenceType.vt_N,
            VarPowerFlowRefferenceType.vt_A,
            VarPowerFlowRefferenceType.vt_B,
            VarPowerFlowRefferenceType.vt_C,
        ])

        c0: Any = grid.var_factory.add_const(0.0)

        I_kcl: Dict[int, List[Any]] = dict()
        for bus_idx, bus in enumerate(grid.buses):
            if bus.is_dc:
                I_kcl[bus_idx] = list([c0])
            else:
                I_kcl[bus_idx] = list([c0, c0, c0, c0])

            bus_dict[bus] = int(bus_idx)

        h: float = float(self.options.time_step)
        sbase: float = float(grid.Sbase)
        fbase: float = float(grid.fBase)

        vsc_idx_dict: Dict[str, int] = dict()
        for vsc_idx, vsc in enumerate(grid.vsc_devices):
            vsc_idx_dict[vsc.idtag] = vsc_idx


        for branch_idx, br in enumerate(grid.get_branches_iter(add_vsc=True, add_hvdc=True, add_switch=True)):
            f: int = bus_dict[br.bus_from]
            t: int = bus_dict[br.bus_to]
            mdl: Block = self._process_device_model(br, sys_block, grid, glob_time)


            is_bergeron: bool = br.emt_model.name == EmtLineTypes.Bergeron.value
            is_vsc: bool = br.device_type == DeviceType.VscDevice
            vsc_index: int = vsc_idx_dict.get(br.idtag, -1)

            self._assign_api_obj_mapping_branch(br=br, is_vsc=is_vsc, vsc_index=vsc_index)

            if is_bergeron:
                v_f_vars: List[Any] = _get_bus_v_list(
                    grid=grid,
                    bus_block=br.bus_from.emt_model,
                    ph_v_keys=ph_v_keys
                )
                v_t_vars: List[Any] = _get_bus_v_list(
                    grid=grid,
                    bus_block=br.bus_to.emt_model,
                    ph_v_keys=ph_v_keys
                )

                rt: BergeronHistoryRuntime = BergeronHistoryRuntime(
                    line=br,
                    line_block=mdl,
                    h=h,
                    sbase=sbase,
                    fbase=fbase
                )
                rt.bind_terminals(v_f_vars, v_t_vars)

                if self.power_flow_results_3ph is not None:
                    self._try_set_bergeron_pf_init(
                        mdl=mdl,
                        rt=rt,
                        branch_index=branch_idx,
                        f_bus_idx=f,
                        t_bus_idx=t,
                        sbase=grid.Sbase,
                    )
                else:
                    if self.power_flow_results is not None:
                        if self.options.verbose:
                            print("Initializing bergeron line variables assuming a balanced power flow")
                        else:
                            pass

                        self._try_set_bergeron_pf_init_balanced(
                            mdl=mdl,
                            rt=rt,
                            branch_index=branch_idx,
                            f_bus_idx=f,
                            t_bus_idx=t,
                            sbase=grid.Sbase,
                        )
                    else:
                        if self.options.verbose:
                            print("No Power Flow results given.")
                        else:
                            pass

                i_f_exprs: List[Any]
                i_t_exprs: List[Any]
                i_f_exprs, i_t_exprs = rt.get_nodal_injections()

                for ph in range(4):
                    if i_f_exprs[ph] is not None:
                        I_kcl[f][ph] = I_kcl[f][ph] - i_f_exprs[ph]
                    else:
                        pass

                    if i_t_exprs[ph] is not None:
                        I_kcl[t][ph] = I_kcl[t][ph] - i_t_exprs[ph]
                    else:
                        pass

                self.history_models.append(rt)

            else:

                side_bus_indices: List[int] = list([f, t])
                side_buses: List[Any] = list([br.bus_from, br.bus_to])
                side_current_keys: List[List[VarPowerFlowRefferenceType]] = list([br_if_keys, br_it_keys])

                for side_idx in range(2):
                    side_bus_idx: int = side_bus_indices[side_idx]
                    side_bus: Any = side_buses[side_idx]
                    current_keys: List[VarPowerFlowRefferenceType] = side_current_keys[side_idx]

                    if side_bus.is_dc:
                        side_dc_expr: Any | None = mdl.E(VarPowerFlowRefferenceType.Idc)
                        if side_dc_expr is not None:
                            I_kcl[side_bus_idx][0] = I_kcl[side_bus_idx][0] - side_dc_expr
                        else:
                            pass
                    else:
                        for ph in range(4):
                            if is_vsc:
                                side_expr: Any | None = mdl.E(inj_i_keys[ph])
                            else:
                                side_expr = mdl.E(current_keys[ph])

                            if side_expr is not None:
                                I_kcl[side_bus_idx][ph] = I_kcl[side_bus_idx][ph] - side_expr
                            else:
                                pass

                terminal_buses: List[Any] = list([br.bus_from, br.bus_to])
                terminal_voltage_keys: List[List[VarPowerFlowRefferenceType]] = list([br_vf_keys, br_vt_keys])

                for term_idx in range(2):
                    terminal_bus: Any = terminal_buses[term_idx]
                    terminal_keys: List[VarPowerFlowRefferenceType] = terminal_voltage_keys[term_idx]
                    external_mapping: Optional[Dict[Any, Var]] = _get_external_mapping(br.emt_model)

                    if terminal_bus.is_dc:
                        v_dc, _, _, _ = get_bus_emt_algebraic_vars(terminal_bus.emt_model)

                        if external_mapping is not None:
                            mapped_var: Optional[Var] = external_mapping.get(VarPowerFlowRefferenceType.Vdc, None)
                            if mapped_var is not None:
                                br.emt_model.update_model(mapped_var, v_dc)
                            else:
                                pass
                        else:
                            pass
                    else:
                        v_n, v_a, v_b, v_c = get_bus_emt_algebraic_vars(terminal_bus.emt_model)
                        terminal_voltage_vars: List[Any] = list([v_n, v_a, v_b, v_c])

                        if external_mapping is not None:
                            for ph in range(4):
                                mapped_var = external_mapping.get(terminal_keys[ph], None)
                                terminal_voltage_var = terminal_voltage_vars[ph]

                                if mapped_var is not None and terminal_voltage_var is not None:
                                    br.emt_model.update_model(mapped_var, terminal_voltage_var)
                                else:
                                    pass
                        else:
                            pass


                if self.power_flow_results_3ph is not None:
                    if is_vsc and vsc_index >= 0:
                        self._try_set_vsc_branch_pf_init(
                            mdl=mdl,
                            f_bus_idx=f,
                            t_bus_idx=t,
                            sbase=sbase,
                            vsc_index=vsc_index,
                        )
                    else:
                        self._try_set_branch_pf_init(
                            mdl=mdl,
                            branch_index=branch_idx,
                            f_bus_idx=f,
                            t_bus_idx=t,
                            sbase=grid.Sbase,
                            is_vsc=is_vsc,
                            vsc_index=vsc_index
                        )
                else:
                    if self.power_flow_results is not None:
                        if self.options.verbose:
                            print("Initializing branch variables assuming a balanced power flow")
                        else:
                            pass

                        self._try_set_branch_pf_init_balanced(
                            mdl=mdl,
                            branch_index=branch_idx,
                            f_bus_idx=f,
                            t_bus_idx=t,
                            sbase=grid.Sbase,
                            is_vsc=is_vsc,
                            vsc_index=vsc_index
                        )
                    else:
                        if self.options.verbose:
                            print("No Power Flow results given.")
                        else:
                            pass



        for inj in grid.get_injection_devices_iter():
            mdl: Block = self._process_device_model(inj, sys_block, grid, glob_time)
            b: int = bus_dict[inj.bus]

            if inj.device_type == DeviceType.LoadDevice:
                self._assign_api_obj_mapping_load(inj)
            elif inj.device_type == DeviceType.GeneratorDevice:
                    self._assign_api_obj_mapping_generator(inj)
            else:
                pass

            if inj.bus.is_dc:
                i_dc_expr: Any | None = mdl.E(VarPowerFlowRefferenceType.Idc)
                if i_dc_expr is not None:
                    I_kcl[b][0] = I_kcl[b][0] + i_dc_expr
                else:
                    pass
            else:
                for ph in range(4):
                    i_expr: Any | None = mdl.E(inj_i_keys[ph])
                    if i_expr is not None:
                        I_kcl[b][ph] = I_kcl[b][ph] + i_expr
                    else:
                        pass

            inj_external_mapping: Optional[Dict[Any, Var]] = _get_external_mapping(inj.emt_model)

            if inj.bus.is_dc:
                v_dc, _, _, _ = get_bus_emt_algebraic_vars(inj.bus.emt_model)

                if inj_external_mapping is not None:
                    mapped_var = inj_external_mapping.get(VarPowerFlowRefferenceType.Vdc, None)
                    if mapped_var is not None:
                        inj.emt_model.update_model(mapped_var, v_dc)
                    else:
                        pass
                else:
                    pass
            else:
                v_n, v_a, v_b, v_c = get_bus_emt_algebraic_vars(inj.bus.emt_model)
                inj_bus_voltage_vars: List[Any] = list([v_n, v_a, v_b, v_c])

                if inj_external_mapping is not None:
                    for ph in range(4):
                        mapped_var = inj_external_mapping.get(ph_v_keys[ph], None)
                        inj_bus_voltage_var = inj_bus_voltage_vars[ph]

                        if mapped_var is not None and inj_bus_voltage_var is not None:
                            inj.emt_model.update_model(mapped_var, inj_bus_voltage_var)
                        else:
                            pass
                else:
                    pass

            if self.power_flow_results_3ph is not None:
                self._try_set_inj_pf_init(
                    inj=inj,
                    mdl=mdl,
                    bus_index=b,
                    sbase=grid.Sbase,
                )
            else:
                if self.power_flow_results is not None:
                    if self.options.verbose:
                        print("Initializing injection variables assuming a balanced power flow")
                    else:
                        pass

                    self._try_set_inj_pf_init_balanced(
                        inj=inj,
                        mdl=mdl,
                        bus_index=b,
                        sbase=grid.Sbase,
                    )
                else:
                    if self.options.verbose:
                        print("No Power Flow results given.")
                    else:
                        pass

        for bus_idx, bus in enumerate(grid.buses):
            mdl: Block = self._process_device_model(bus, sys_block, grid, glob_time)

            if self.power_flow_results_3ph is not None:
                self._try_set_bus_pf_init(
                    bus=bus,
                    mdl=mdl,
                    bus_index=bus_idx
                )
            else:
                if self.power_flow_results is not None:
                    if self.options.verbose:
                        print("Initializing bus variables assuming a balanced power flow")
                    else:
                        pass

                    self._try_set_bus_pf_init_balanced(
                        bus=bus,
                        mdl=mdl,
                        bus_index=bus_idx
                    )
                else:
                    if self.options.verbose:
                        print("No Power Flow results given.")
                    else:
                        pass

        for bus_idx, bus in enumerate(grid.buses):
            mdl: Block = bus.emt_model
            mdl.algebraic_eqs = list()

            if bus.is_dc:
                v_dc_expr: Any | None = mdl.E(VarPowerFlowRefferenceType.Vdc)
                if v_dc_expr is not None:
                    mdl.algebraic_eqs.append(I_kcl[bus_idx][0])
                else:
                    pass
            else:
                for ph_idx, v_key in enumerate(ph_v_keys):
                    v_expr: Any | None = mdl.E(v_key)
                    if v_expr is not None:
                        mdl.algebraic_eqs.append(I_kcl[bus_idx][ph_idx])
                    else:
                        pass

            if len(mdl.algebraic_eqs) == 0:
                self.logger.add_error(
                    "Bus has no phases (no voltage vars)",
                    value=str(bus_idx)
                )
            else:
                pass

    def _register_runtime_event_parameters(self, dev: Any, mdl: Block) -> None:
        """
        Register runtime-updatable EMT parameters declared by the device block.

        EMT runtime events are no longer baked into the symbolic model during the
        parsing phase. Instead, the problem stores the event-capable parameters and
        later activates the selected EMT event group through ``set_events_group()``.

        :param dev: Device object from the grid.
        :param mdl: Device symbolic block containing ``event_dict`` and ``mode_dict``.
        :return: None
        """
        if not mdl.event_dict and not mdl.mode_dict:
            return

        for parameter in mdl.event_dict.keys():
            self._event_parameter_device_idtags[parameter.uid] = dev.idtag
            self._continuous_event_parameter_uids.add(parameter.uid)

        for parameter in mdl.mode_dict.keys():
            self._event_parameter_device_idtags[parameter.uid] = dev.idtag
            self._discrete_event_parameter_uids.add(parameter.uid)

    def _get_emt_events_for_group(self, emt_events_group: EmtEventsGroup | None) -> List[Any]:
        """
        Return the EMT events that belong to the selected group.

        ``None`` means that all EMT events registered in the grid remain active,
        which preserves the previous default behavior.
        """
        emt_events: List[Any] = _get_grid_runtime_events(self.grid)

        if emt_events_group is None:
            return emt_events

        filtered_events: List[Any] = list()

        for evt in emt_events:
            try:
                group_idtag = evt.group.idtag
            except AttributeError:
                group_idtag = None

            if group_idtag == emt_events_group.idtag:
                filtered_events.append(evt)
            else:
                pass

        return filtered_events

    def _event_targets_registered_parameter(self, evt: Any, parameter_uid: int) -> bool:
        """
        Return whether the EMT event targets a runtime parameter registered in the problem.
        """
        registered_device_idtag: str | None = self._event_parameter_device_idtags.get(parameter_uid, None)

        try:
            event_device_idtag: str = str(evt.device_idtag)
        except AttributeError:
            event_device_idtag = ""

        if registered_device_idtag is None:
            return False

        if event_device_idtag == "":
            return True

        return registered_device_idtag == event_device_idtag

    def set_events_group(self, emt_events_group: EmtEventsGroup | None) -> None:
        """
        Activate the selected EMT events group inside the problem runtime layer.

        Continuous EMT events are mapped to runtime ``piecewise(time)`` expressions.
        Discrete EMT mode events are stored as scheduled updates consumed by the
        boundary update hook used by the EMT solvers.

        :param emt_events_group: EMT events group to activate. ``None`` keeps all EMT events active.
        :return: None
        """
        same_group_requested: bool

        if self._active_events_group is None:
            same_group_requested = emt_events_group is None and len(self._scheduled_mode_events) > 0
        elif emt_events_group is None:
            same_group_requested = False
        else:
            same_group_requested = self._active_events_group.idtag == emt_events_group.idtag

        if same_group_requested:
            return
        else:
            pass

        active_runtime_eqs: List[Any] = list(self._runtime_parameter_eqs0)
        scheduled_mode_events: Dict[int, List[Tuple[float, float, bool]]] = dict()
        continuous_events: Dict[int, Dict[str, List[float]]] = {
            parameter.uid: {"times": list(), "values": list()}
            for parameter in self.get_runtime_continuous_parameters()
            if parameter.uid in self._continuous_event_parameter_uids
        }

        emt_events: List[Any] = self._get_emt_events_for_group(emt_events_group)

        for evt in emt_events:
            if isinstance(evt.parameter, Var):
                parameter_uid: int = evt.parameter.uid

                if self._event_targets_registered_parameter(evt, parameter_uid):
                    if parameter_uid in self._discrete_event_parameter_uids:
                        event_list: List[Tuple[float, float, bool]] = scheduled_mode_events.setdefault(
                            parameter_uid,
                            list(),
                        )

                        try:
                            force_step_alignment = bool(evt.force_step_alignment)
                        except AttributeError:
                            force_step_alignment = False

                        event_list.append(
                            (
                                float(evt.time),
                                float(evt.value),
                                force_step_alignment,
                            )
                        )
                    else:
                        if parameter_uid in continuous_events:
                            continuous_events[parameter_uid]["times"].append(float(evt.time))
                            continuous_events[parameter_uid]["values"].append(float(evt.value))
                        else:
                            pass
                else:
                    pass
            else:
                pass

        for parameter_uid, info in continuous_events.items():
            if len(info["times"]) != 0:
                runtime_idx: int = self.uid2idx_event_params[parameter_uid]
                sort_idx: np.ndarray = np.argsort(np.asarray(info["times"], dtype=np.float64), kind="stable")
                t_events: np.ndarray = np.asarray(info["times"], dtype=np.float64)[sort_idx]
                new_values: np.ndarray = np.asarray(info["values"], dtype=np.float64)[sort_idx]

                active_runtime_eqs[runtime_idx] = piecewise(
                    time_var=self._glob_time,
                    t_events=t_events,
                    new_values=new_values,
                    default_value=active_runtime_eqs[runtime_idx],
                )
            else:
                pass

        self._active_events_group = emt_events_group
        self._runtime_all_eqs_source = active_runtime_eqs
        self._scheduled_mode_events = scheduled_mode_events

        # Event-group activation only changes the runtime equations and scheduled
        # updates; it does not change the parameter ordering. Reusing the existing
        # partition avoids rebuilding constant parameter buffers and repeated list
        # reconstruction during every event-group switch.
        self._runtime_continuous_eqs = list()
        self._runtime_mode_eqs = list()

        n_source: int = len(self._runtime_all_parameters_source)
        i: int = 0
        while i < n_source:
            parameter: Var = self._runtime_all_parameters_source[i]
            equation: Any = active_runtime_eqs[i]

            if parameter.uid in self._runtime_mode_uids:
                self._runtime_mode_eqs.append(equation)
            else:
                self._runtime_continuous_eqs.append(equation)

            i += 1

        self._event_parameters_eqs = list()

        for equation in self._runtime_continuous_eqs:
            self._event_parameters_eqs.append(equation)

        for equation in self._runtime_mode_eqs:
            self._event_parameters_eqs.append(equation)

        self._mode_event_cursor = dict()
        self._initialize_mode_event_state()

        if self.get_variable_parameter_number() > 0:
            self._event_params_values = self._initialize_runtime_parameter_values(0.0)
            self._event_params_values = self.def_event_params_fn(self._event_params_values, 0.0)
        else:
            self._event_params_values = np.zeros(0, dtype=np.float64)

    # ---------------------------------------------------------------------
    # MAPPINGS
    # ---------------------------------------------------------------------
    def _add_model_to_system_mappings(self, elm: ALL_DEV_TYPES, mdl: Block)->None:
        """
        Populates tracking dictionaries to maintain the relationship between
        electrical devices and their corresponding symbolic variables.
        """
        for v in mdl.state_vars:
            self.add_device_var(dev=elm, var=v)
            self._vars_glob_name2uid[v.name + elm.name] = v.uid
            self._vars2device[v.uid] = elm

        for v in mdl.algebraic_vars:
            self.add_device_var(dev=elm, var=v)
            self._vars_glob_name2uid[v.name + elm.name] = v.uid
            self._vars2device[v.uid] = elm

        for dv in mdl.diff_vars:
            self.add_device_var(dev=elm, var=dv)
            self._vars_glob_name2uid[dv.name + elm.name] = dv.uid
            self._vars2device[dv.uid] = elm

    # ---------------------------------------------------------------------
    # PF INIT
    # ---------------------------------------------------------------------
    def _try_set_bus_pf_init(self, bus,
                             mdl: Block,
                             bus_index: int) -> None:
        """
        Initialize bus voltage variables from three-phase power-flow results.

        Phasor results are transformed into instantaneous abc-domain values at t = 0.
        Only variables that exist in the model external mapping are initialized.

        :param bus: Bus device
        :param mdl: Bus symbolic block.
        :param bus_index: Bus index in the power-flow results.
        :return: None
        """
        omega_base: float = 2.0 * np.pi * self.grid.fBase

        if bus.is_dc:

            if self.power_flow_results is not None:
                # DC bus: use Vdc (magnitude) -> angle is not applicable for DC
                self.set_init_guess(mdl, VarPowerFlowRefferenceType.Vdc,
                                    float(np.abs(self.power_flow_results.voltage[bus_index])))
            else:
                raise ValueError(f"EMT simulation with DC branches requires the non unbalanced PowerFlow to be calculated.")

        else:

            if mdl.E(VarPowerFlowRefferenceType.v_N) is not None:
                V_N = self.power_flow_results_3ph.voltage_N[bus_index]
                v_N: float = np.sqrt(2.0) * np.imag(V_N)
                d_v_N: float = omega_base * np.sqrt(2.0) * np.real(V_N)

                self.set_init_guess(mdl, VarPowerFlowRefferenceType.v_N, v_N)
                self.set_diff_init_guess(mdl, VarPowerFlowRefferenceType.d_v_N, d_v_N)
            else:
                pass

            if mdl.E(VarPowerFlowRefferenceType.v_A) is not None:
                V_A = self.power_flow_results_3ph.voltage_A[bus_index]
                v_A: float = np.sqrt(2.0) * np.imag(V_A)
                d_v_A: float = omega_base * np.sqrt(2.0) * np.real(V_A)

                self.set_init_guess(mdl, VarPowerFlowRefferenceType.v_A, v_A)
                self.set_diff_init_guess(mdl, VarPowerFlowRefferenceType.d_v_A, d_v_A)
            else:
                pass

            if mdl.E(VarPowerFlowRefferenceType.v_B) is not None:
                V_B = self.power_flow_results_3ph.voltage_B[bus_index]
                v_B: float = np.sqrt(2.0) * np.imag(V_B)
                d_v_B: float = omega_base * np.sqrt(2.0) * np.real(V_B)

                self.set_init_guess(mdl, VarPowerFlowRefferenceType.v_B, v_B)
                self.set_diff_init_guess(mdl, VarPowerFlowRefferenceType.d_v_B, d_v_B)
            else:
                pass

            if mdl.E(VarPowerFlowRefferenceType.v_C) is not None:
                V_C = self.power_flow_results_3ph.voltage_C[bus_index]
                v_C: float = np.sqrt(2.0) * np.imag(V_C)
                d_v_C: float = omega_base * np.sqrt(2.0) * np.real(V_C)

                self.set_init_guess(mdl, VarPowerFlowRefferenceType.v_C, v_C)
                self.set_diff_init_guess(mdl, VarPowerFlowRefferenceType.d_v_C, d_v_C)
            else:
                pass

    def _try_set_bus_pf_init_balanced(self, bus,
                                      mdl: Block,
                                      bus_index: int) -> None:
        """
        Initialize bus voltage variables from balanced power-flow results.

        The balanced power flow provides one complex bus-voltage phasor per AC bus in
        self.power_flow_results.voltage. This phasor is interpreted as the balanced
        phase-A phasor, and the remaining phases are reconstructed as:

            V_A = V
            V_B = V * exp(-j*2*pi/3)
            V_C = V * exp(+j*2*pi/3)
            V_N = 0

        Phasor results are transformed into instantaneous abc-domain values at t = 0.
        Only variables that exist in the model external mapping are initialized.

        :param bus: Bus device
        :param mdl: Bus symbolic block.
        :param bus_index: Bus index in the power-flow results.
        :return: None
        """
        omega_base: float = 2.0 * np.pi * self.grid.fBase

        if bus.is_dc:

            if self.power_flow_results is not None:
                # DC bus: use Vdc (magnitude) -> angle is not applicable for DC
                self.set_init_guess(
                    mdl,
                    VarPowerFlowRefferenceType.Vdc,
                    float(np.abs(self.power_flow_results.voltage[bus_index]))
                )
            else:
                raise ValueError(
                    "EMT simulation with DC branches requires the non unbalanced PowerFlow to be calculated."
                )

        else:

            if self.power_flow_results is None:
                raise ValueError(
                    "Balanced EMT initialization requires the balanced PowerFlow to be calculated."
                )

            alpha: float = 2.0 * np.pi / 3.0
            V_bus: CxVec = self.power_flow_results.voltage[bus_index]

            V_N: complex = 0.0 + 0.0j
            V_A: CxVec = V_bus
            V_B: complex = V_bus * np.exp(-1j * alpha)
            V_C: complex = V_bus * np.exp(+1j * alpha)

            if mdl.E(VarPowerFlowRefferenceType.v_N) is not None:
                v_N: float = np.sqrt(2.0) * np.imag(V_N)
                d_v_N: float = omega_base * np.sqrt(2.0) * np.real(V_N)

                self.set_init_guess(mdl, VarPowerFlowRefferenceType.v_N, v_N)
                self.set_diff_init_guess(mdl, VarPowerFlowRefferenceType.d_v_N, d_v_N)

            if mdl.E(VarPowerFlowRefferenceType.v_A) is not None:
                v_A: float = np.sqrt(2.0) * np.imag(V_A)
                d_v_A: float = omega_base * np.sqrt(2.0) * np.real(V_A)

                self.set_init_guess(mdl, VarPowerFlowRefferenceType.v_A, v_A)
                self.set_diff_init_guess(mdl, VarPowerFlowRefferenceType.d_v_A, d_v_A)

            if mdl.E(VarPowerFlowRefferenceType.v_B) is not None:
                v_B: float = np.sqrt(2.0) * np.imag(V_B)
                d_v_B: float = omega_base * np.sqrt(2.0) * np.real(V_B)

                self.set_init_guess(mdl, VarPowerFlowRefferenceType.v_B, v_B)
                self.set_diff_init_guess(mdl, VarPowerFlowRefferenceType.d_v_B, d_v_B)

            if mdl.E(VarPowerFlowRefferenceType.v_C) is not None:
                v_C: float = np.sqrt(2.0) * np.imag(V_C)
                d_v_C: float = omega_base * np.sqrt(2.0) * np.real(V_C)

                self.set_init_guess(mdl, VarPowerFlowRefferenceType.v_C, v_C)
                self.set_diff_init_guess(mdl, VarPowerFlowRefferenceType.d_v_C, d_v_C)

    def _get_vsc_terminal_indices(self,
                                  f_bus_idx: int,
                                  t_bus_idx: int) -> Tuple[int, int, bool]:
        """
        Return ``(ac_bus_idx, dc_bus_idx, ac_is_from)`` for a VSC branch.

        The preferred detection rule is based on bus types. If the branch does
        not present the expected AC/DC split, fall back to the legacy VSC
        orientation assumption used by the PF results: from side is DC and to
        side is AC.
        """
        f_bus = self.grid.buses[f_bus_idx]
        t_bus = self.grid.buses[t_bus_idx]

        if not f_bus.is_dc and t_bus.is_dc:
            return f_bus_idx, t_bus_idx, True

        if f_bus.is_dc and not t_bus.is_dc:
            return t_bus_idx, f_bus_idx, False

        return t_bus_idx, f_bus_idx, False

    def _set_vsc_pf_positive_sequence(self,
                                      mdl: Block,
                                      VA: complex,
                                      VB: complex,
                                      VC: complex,
                                      IA: complex,
                                      IB: complex,
                                      IC: complex) -> None:
        """
        Populate positive-sequence PF-derived quantities used by VSC templates
        when they expose them in the external mapping.
        """
        a = np.exp(1j * 2.0 * np.pi / 3.0)

        V1 = (VA + a * VB + (a * a) * VC) / 3.0
        I1 = (IA + a * IB + (a * a) * IC) / 3.0

        phi_V = float(np.angle(V1))
        phi_I = float(np.angle(I1))
        ang = phi_I - phi_V
        phi = float(np.arctan2(np.sin(ang), np.cos(ang)))

        external_mapping: Optional[Dict[Any, Var]] = _get_external_mapping(mdl)
        if external_mapping is None:
            return

        if VarPowerFlowRefferenceType.phi_v in external_mapping:
            self.set_external_param(mdl, VarPowerFlowRefferenceType.phi_v, phi_V)

        if VarPowerFlowRefferenceType.phi in external_mapping:
            self.set_external_param(mdl, VarPowerFlowRefferenceType.phi, phi)

        if VarPowerFlowRefferenceType.Vpk in external_mapping:
            self.set_external_param(mdl, VarPowerFlowRefferenceType.Vpk, float(np.sqrt(2.0) * np.abs(V1)))

        if VarPowerFlowRefferenceType.Ipk in external_mapping:
            self.set_external_param(mdl, VarPowerFlowRefferenceType.Ipk, float(np.sqrt(2.0) * np.abs(I1)))

    def _try_set_vsc_branch_pf_init(self,
                                    mdl: Block,
                                    f_bus_idx: int,
                                    t_bus_idx: int,
                                    sbase: float,
                                    vsc_index: int) -> None:
        """
        Initialize a VSC branch from three-phase PF results using the converter
        external mapping as the source of truth.
        """
        pf_results_3ph = self.power_flow_results_3ph
        if pf_results_3ph is None:
            return

        ac_bus_idx, dc_bus_idx, ac_is_from = self._get_vsc_terminal_indices(
            f_bus_idx=f_bus_idx,
            t_bus_idx=t_bus_idx,
        )

        VA = pf_results_3ph.voltage_A[ac_bus_idx]
        VB = pf_results_3ph.voltage_B[ac_bus_idx]
        VC = pf_results_3ph.voltage_C[ac_bus_idx]
        VN = 0.0 + 0.0j

        SA = pf_results_3ph.St_vsc_A[vsc_index] / sbase
        SB = pf_results_3ph.St_vsc_B[vsc_index] / sbase
        SC = pf_results_3ph.St_vsc_C[vsc_index] / sbase

        IA = 0.0 + 0.0j if abs(VA) <= 1e-12 else np.conj(SA / VA)
        IB = 0.0 + 0.0j if abs(VB) <= 1e-12 else np.conj(SB / VB)
        IC = 0.0 + 0.0j if abs(VC) <= 1e-12 else np.conj(SC / VC)

        try:
            pf_results_3ph_pfn_vsc = pf_results_3ph.Pfn_vsc[vsc_index]
        except AttributeError:
            pf_results_3ph_pfn_vsc = 0.0

        S_ac_total = SA + SB + SC
        S_dc_total = complex(
            (
                pf_results_3ph.Pfp_vsc[vsc_index]
                + pf_results_3ph_pfn_vsc
            ) / sbase,
            0.0,
        )

        phase_voltage_dict: Dict[str, complex] = {
            "N": VN,
            "A": VA,
            "B": VB,
            "C": VC,
        }
        phase_current_dict: Dict[str, complex] = {
            "N": 0.0 + 0.0j,
            "A": IA,
            "B": IB,
            "C": IC,
        }
        phase_power_dict: Dict[str, complex] = {
            "N": 0.0 + 0.0j,
            "A": SA,
            "B": SB,
            "C": SC,
        }

        ac_voltage_keys: Dict[str, VarPowerFlowRefferenceType] = {
            "N": VarPowerFlowRefferenceType.v_N,
            "A": VarPowerFlowRefferenceType.v_A,
            "B": VarPowerFlowRefferenceType.v_B,
            "C": VarPowerFlowRefferenceType.v_C,
        }
        ac_current_keys: Dict[str, VarPowerFlowRefferenceType] = {
            "N": VarPowerFlowRefferenceType.i_N,
            "A": VarPowerFlowRefferenceType.i_A,
            "B": VarPowerFlowRefferenceType.i_B,
            "C": VarPowerFlowRefferenceType.i_C,
        }
        if_keys: Dict[str, VarPowerFlowRefferenceType] = {
            "N": VarPowerFlowRefferenceType.if_N,
            "A": VarPowerFlowRefferenceType.if_A,
            "B": VarPowerFlowRefferenceType.if_B,
            "C": VarPowerFlowRefferenceType.if_C,
        }
        it_keys: Dict[str, VarPowerFlowRefferenceType] = {
            "N": VarPowerFlowRefferenceType.it_N,
            "A": VarPowerFlowRefferenceType.it_A,
            "B": VarPowerFlowRefferenceType.it_B,
            "C": VarPowerFlowRefferenceType.it_C,
        }
        sf_keys: Dict[str, Optional[VarPowerFlowRefferenceType]] = {
            "N": None,
            "A": VarPowerFlowRefferenceType.Sf_A,
            "B": VarPowerFlowRefferenceType.Sf_B,
            "C": VarPowerFlowRefferenceType.Sf_C,
        }
        st_keys: Dict[str, Optional[VarPowerFlowRefferenceType]] = {
            "N": None,
            "A": VarPowerFlowRefferenceType.St_A,
            "B": VarPowerFlowRefferenceType.St_B,
            "C": VarPowerFlowRefferenceType.St_C,
        }
        d_vf_keys: Dict[str, VarPowerFlowRefferenceType] = {
            "N": VarPowerFlowRefferenceType.d_v_N_f,
            "A": VarPowerFlowRefferenceType.d_v_A_f,
            "B": VarPowerFlowRefferenceType.d_v_B_f,
            "C": VarPowerFlowRefferenceType.d_v_C_f,
        }
        d_vt_keys: Dict[str, VarPowerFlowRefferenceType] = {
            "N": VarPowerFlowRefferenceType.d_v_N_t,
            "A": VarPowerFlowRefferenceType.d_v_A_t,
            "B": VarPowerFlowRefferenceType.d_v_B_t,
            "C": VarPowerFlowRefferenceType.d_v_C_t,
        }

        omega_base: float = 2.0 * np.pi * self.grid.fBase
        for ph in ["N", "A", "B", "C"]:
            V_ph = phase_voltage_dict[ph]
            I_ph = phase_current_dict[ph]
            S_ph = phase_power_dict[ph]

            self.set_if_exists(mdl=mdl,
                               key=ac_voltage_keys[ph],
                               value=float(np.sqrt(2.0) * np.imag(V_ph)))
            self.set_if_exists(mdl=mdl,
                               key=ac_current_keys[ph],
                               value=float(np.sqrt(2.0) * np.imag(I_ph)))

            if ac_is_from:
                self.set_if_exists(mdl=mdl,
                                   key=if_keys[ph],
                                   value=float(np.sqrt(2.0) * np.imag(I_ph)))
                self.set_if_exists(mdl=mdl,
                                   key=it_keys[ph],
                                   value=0.0)
                self.set_external_param(mdl, d_vf_keys[ph], omega_base * np.sqrt(2.0) * np.real(V_ph))
                self.set_external_param(mdl, d_vt_keys[ph], 0.0)
            else:
                self.set_if_exists(mdl=mdl,
                                   key=if_keys[ph],
                                   value=0.0)
                self.set_if_exists(mdl=mdl,
                                   key=it_keys[ph],
                                   value=float(np.sqrt(2.0) * np.imag(I_ph)))
                self.set_external_param(mdl, d_vf_keys[ph], 0.0)
                self.set_external_param(mdl, d_vt_keys[ph], omega_base * np.sqrt(2.0) * np.real(V_ph))

            sf_key = sf_keys[ph]
            st_key = st_keys[ph]
            if sf_key is not None:
                self.set_if_exists(mdl=mdl,
                                   key=sf_key,
                                   value=float(np.real(S_ph if ac_is_from else 0.0 + 0.0j)))
            if st_key is not None:
                self.set_if_exists(mdl=mdl,
                                   key=st_key,
                                   value=float(np.real(0.0 + 0.0j if ac_is_from else S_ph)))

        self._set_vsc_pf_positive_sequence(
            mdl=mdl,
            VA=complex(VA),
            VB=complex(VB),
            VC=complex(VC),
            IA=IA,
            IB=IB,
            IC=IC,
        )

        if self.power_flow_results is not None:
            v_dc = float(np.abs(self.power_flow_results.voltage[dc_bus_idx]))
            self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Vdc, value=v_dc)
            if abs(v_dc) > 1e-12:
                self.set_if_exists(mdl=mdl,
                                   key=VarPowerFlowRefferenceType.Idc,
                                   value=float(np.real(S_dc_total) / v_dc))
            else:
                self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Idc, value=0.0)

        self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.P, value=float(np.real(S_ac_total)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Q, value=float(np.imag(S_ac_total)))

        S_from = S_ac_total if ac_is_from else S_dc_total
        S_to = S_dc_total if ac_is_from else S_ac_total
        self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Pf, value=float(np.real(S_from)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Qf, value=float(np.imag(S_from)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Pt, value=float(np.real(S_to)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Qt, value=float(np.imag(S_to)))

    def _try_set_vsc_branch_pf_init_balanced(self,
                                             mdl: Block,
                                             f_bus_idx: int,
                                             t_bus_idx: int,
                                             sbase: float,
                                             vsc_index: int) -> None:
        """
        Initialize a VSC branch from balanced PF results using the converter
        external mapping as the source of truth.
        """
        pf_results = self.power_flow_results
        if pf_results is None:
            return

        ac_bus_idx, dc_bus_idx, ac_is_from = self._get_vsc_terminal_indices(
            f_bus_idx=f_bus_idx,
            t_bus_idx=t_bus_idx,
        )

        alpha = 2.0 * np.pi / 3.0
        V_bus = pf_results.voltage[ac_bus_idx]
        VA = V_bus
        VB = V_bus * np.exp(-1j * alpha)
        VC = V_bus * np.exp(+1j * alpha)
        VN = 0.0 + 0.0j

        try:
            pf_results_pfn_vsc = pf_results.Pfn_vsc[vsc_index]
        except AttributeError:
            pf_results_pfn_vsc = 0.0

        S_ac_total = pf_results.St_vsc[vsc_index] / sbase
        S_dc_total = complex(
            (
                pf_results.Pfp_vsc[vsc_index]
                + pf_results_pfn_vsc
            ) / sbase,
            0.0,
        )

        SA = S_ac_total / 3.0
        SB = S_ac_total / 3.0
        SC = S_ac_total / 3.0

        IA = 0.0 + 0.0j if abs(VA) <= 1e-12 else np.conj(SA / VA)
        IB = 0.0 + 0.0j if abs(VB) <= 1e-12 else np.conj(SB / VB)
        IC = 0.0 + 0.0j if abs(VC) <= 1e-12 else np.conj(SC / VC)

        phase_voltage_dict: Dict[str, complex] = {
            "N": VN,
            "A": VA,
            "B": VB,
            "C": VC,
        }
        phase_current_dict: Dict[str, complex] = {
            "N": 0.0 + 0.0j,
            "A": IA,
            "B": IB,
            "C": IC,
        }
        phase_power_dict: Dict[str, complex] = {
            "N": 0.0 + 0.0j,
            "A": SA,
            "B": SB,
            "C": SC,
        }

        ac_voltage_keys: Dict[str, VarPowerFlowRefferenceType] = {
            "N": VarPowerFlowRefferenceType.v_N,
            "A": VarPowerFlowRefferenceType.v_A,
            "B": VarPowerFlowRefferenceType.v_B,
            "C": VarPowerFlowRefferenceType.v_C,
        }
        ac_current_keys: Dict[str, VarPowerFlowRefferenceType] = {
            "N": VarPowerFlowRefferenceType.i_N,
            "A": VarPowerFlowRefferenceType.i_A,
            "B": VarPowerFlowRefferenceType.i_B,
            "C": VarPowerFlowRefferenceType.i_C,
        }
        if_keys: Dict[str, VarPowerFlowRefferenceType] = {
            "N": VarPowerFlowRefferenceType.if_N,
            "A": VarPowerFlowRefferenceType.if_A,
            "B": VarPowerFlowRefferenceType.if_B,
            "C": VarPowerFlowRefferenceType.if_C,
        }
        it_keys: Dict[str, VarPowerFlowRefferenceType] = {
            "N": VarPowerFlowRefferenceType.it_N,
            "A": VarPowerFlowRefferenceType.it_A,
            "B": VarPowerFlowRefferenceType.it_B,
            "C": VarPowerFlowRefferenceType.it_C,
        }
        sf_keys: Dict[str, Optional[VarPowerFlowRefferenceType]] = {
            "N": None,
            "A": VarPowerFlowRefferenceType.Sf_A,
            "B": VarPowerFlowRefferenceType.Sf_B,
            "C": VarPowerFlowRefferenceType.Sf_C,
        }
        st_keys: Dict[str, Optional[VarPowerFlowRefferenceType]] = {
            "N": None,
            "A": VarPowerFlowRefferenceType.St_A,
            "B": VarPowerFlowRefferenceType.St_B,
            "C": VarPowerFlowRefferenceType.St_C,
        }
        d_vf_keys: Dict[str, VarPowerFlowRefferenceType] = {
            "N": VarPowerFlowRefferenceType.d_v_N_f,
            "A": VarPowerFlowRefferenceType.d_v_A_f,
            "B": VarPowerFlowRefferenceType.d_v_B_f,
            "C": VarPowerFlowRefferenceType.d_v_C_f,
        }
        d_vt_keys: Dict[str, VarPowerFlowRefferenceType] = {
            "N": VarPowerFlowRefferenceType.d_v_N_t,
            "A": VarPowerFlowRefferenceType.d_v_A_t,
            "B": VarPowerFlowRefferenceType.d_v_B_t,
            "C": VarPowerFlowRefferenceType.d_v_C_t,
        }

        omega_base: float = 2.0 * np.pi * self.grid.fBase
        for ph in ["N", "A", "B", "C"]:
            V_ph = phase_voltage_dict[ph]
            I_ph = phase_current_dict[ph]
            S_ph = phase_power_dict[ph]

            self.set_if_exists(mdl=mdl,
                               key=ac_voltage_keys[ph],
                               value=float(np.sqrt(2.0) * np.imag(V_ph)))
            self.set_if_exists(mdl=mdl,
                               key=ac_current_keys[ph],
                               value=float(np.sqrt(2.0) * np.imag(I_ph)))

            if ac_is_from:
                self.set_if_exists(mdl=mdl,
                                   key=if_keys[ph],
                                   value=float(np.sqrt(2.0) * np.imag(I_ph)))
                self.set_if_exists(mdl=mdl,
                                   key=it_keys[ph],
                                   value=0.0)
                self.set_external_param(mdl, d_vf_keys[ph], omega_base * np.sqrt(2.0) * np.real(V_ph))
                self.set_external_param(mdl, d_vt_keys[ph], 0.0)
            else:
                self.set_if_exists(mdl=mdl,
                                   key=if_keys[ph],
                                   value=0.0)
                self.set_if_exists(mdl=mdl,
                                   key=it_keys[ph],
                                   value=float(np.sqrt(2.0) * np.imag(I_ph)))
                self.set_external_param(mdl, d_vf_keys[ph], 0.0)
                self.set_external_param(mdl, d_vt_keys[ph], omega_base * np.sqrt(2.0) * np.real(V_ph))

            sf_key = sf_keys[ph]
            st_key = st_keys[ph]
            if sf_key is not None:
                self.set_if_exists(mdl=mdl,
                                   key=sf_key,
                                   value=float(np.real(S_ph if ac_is_from else 0.0 + 0.0j)))
            if st_key is not None:
                self.set_if_exists(mdl=mdl,
                                   key=st_key,
                                   value=float(np.real(0.0 + 0.0j if ac_is_from else S_ph)))

        self._set_vsc_pf_positive_sequence(
            mdl=mdl,
            VA=complex(VA),
            VB=complex(VB),
            VC=complex(VC),
            IA=IA,
            IB=IB,
            IC=IC,
        )

        v_dc = float(np.abs(pf_results.voltage[dc_bus_idx]))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Vdc, value=v_dc)
        if abs(v_dc) > 1e-12:
            self.set_if_exists(mdl=mdl,
                               key=VarPowerFlowRefferenceType.Idc,
                               value=float(np.real(S_dc_total) / v_dc))
        else:
            self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Idc, value=0.0)

        self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.P, value=float(np.real(S_ac_total)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Q, value=float(np.imag(S_ac_total)))

        S_from = S_ac_total if ac_is_from else S_dc_total
        S_to = S_dc_total if ac_is_from else S_ac_total
        self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Pf, value=float(np.real(S_from)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Qf, value=float(np.imag(S_from)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Pt, value=float(np.real(S_to)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Qt, value=float(np.imag(S_to)))

    def _try_set_branch_pf_init(
            self,
            mdl: Block,
            branch_index: int,
            f_bus_idx: int,
            t_bus_idx: int,
            sbase: float,
            is_vsc: bool = False,
            vsc_index: int = -1
    ) -> None:
        """
        Initialize branch variables from three-phase power-flow results.

        The method initializes:
          - per-phase branch powers Sf_* and St_* when available,
          - aggregated terminal powers Pf/Qf/Pt/Qt,
          - per-phase instantaneous terminal currents if_* and it_* at t = 0.

        The neutral phase is initialized to zero for currents if the corresponding
        PF quantities are not available.

        :param mdl: Branch symbolic block.
        :param branch_index: Branch index in the power-flow results.
        :param f_bus_idx: From-bus index in the power-flow results.
        :param t_bus_idx: To-bus index in the power-flow results.
        :param sbase: Base power of the grid.
        :return: None
        """

        phases: List[str] = ["N", "A", "B", "C"]

        sf_key_dict: Dict[str, Optional[VarPowerFlowRefferenceType]] = {
            "N": None,
            "A": VarPowerFlowRefferenceType.Sf_A,
            "B": VarPowerFlowRefferenceType.Sf_B,
            "C": VarPowerFlowRefferenceType.Sf_C,
        }
        st_key_dict: Dict[str, Optional[VarPowerFlowRefferenceType]] = {
            "N": None,
            "A": VarPowerFlowRefferenceType.St_A,
            "B": VarPowerFlowRefferenceType.St_B,
            "C": VarPowerFlowRefferenceType.St_C,
        }

        if_key_dict: Dict[str, VarPowerFlowRefferenceType] = {
            "N": VarPowerFlowRefferenceType.if_N,
            "A": VarPowerFlowRefferenceType.if_A,
            "B": VarPowerFlowRefferenceType.if_B,
            "C": VarPowerFlowRefferenceType.if_C,
        }
        it_key_dict: Dict[str, VarPowerFlowRefferenceType] = {
            "N": VarPowerFlowRefferenceType.it_N,
            "A": VarPowerFlowRefferenceType.it_A,
            "B": VarPowerFlowRefferenceType.it_B,
            "C": VarPowerFlowRefferenceType.it_C,
        }
        d_vf_key_dict: Dict[str, VarPowerFlowRefferenceType] = {
            "N": VarPowerFlowRefferenceType.d_v_N_f,
            "A": VarPowerFlowRefferenceType.d_v_A_f,
            "B": VarPowerFlowRefferenceType.d_v_B_f,
            "C": VarPowerFlowRefferenceType.d_v_C_f,
        }
        d_vt_key_dict: Dict[str, VarPowerFlowRefferenceType] = {
            "N": VarPowerFlowRefferenceType.d_v_N_t,
            "A": VarPowerFlowRefferenceType.d_v_A_t,
            "B": VarPowerFlowRefferenceType.d_v_B_t,
            "C": VarPowerFlowRefferenceType.d_v_C_t,
        }


        voltage_from_dict = {
            "N": self.power_flow_results_3ph.voltage_N,
            "A": self.power_flow_results_3ph.voltage_A,
            "B": self.power_flow_results_3ph.voltage_B,
            "C": self.power_flow_results_3ph.voltage_C,
        }
        voltage_to_dict = voltage_from_dict

        sf_array_dict = {
            "N": None,
            "A": self.power_flow_results_3ph.Sf_A,
            "B": self.power_flow_results_3ph.Sf_B,
            "C": self.power_flow_results_3ph.Sf_C,
        }
        st_array_dict = {
            "N": None,
            "A": self.power_flow_results_3ph.St_A,
            "B": self.power_flow_results_3ph.St_B,
            "C": self.power_flow_results_3ph.St_C,
        }


        sf_sum: complex = 0.0 + 0.0j
        st_sum: complex = 0.0 + 0.0j

        for ph in phases:
            sf_key: Optional[VarPowerFlowRefferenceType] = sf_key_dict[ph]
            st_key: Optional[VarPowerFlowRefferenceType] = st_key_dict[ph]
            sf_array: Optional[np.ndarray] = sf_array_dict[ph]
            st_array: Optional[np.ndarray] = st_array_dict[ph]

            if sf_key is None:
                pass
            else:
                if mdl.E(sf_key) is not None and sf_array is not None:
                    pf_idx = vsc_index if is_vsc and vsc_index >= 0 else branch_index
                    sf_ph = sf_array[pf_idx] / sbase
                    self.set_if_exists(mdl=mdl, key=sf_key, value=float(np.real(sf_ph)))
                    sf_sum += sf_ph
                elif is_vsc:
                    self.set_if_exists(mdl=mdl, key=sf_key, value=0.0)
                else:
                    pass

            if st_key is None:
                pass
            else:
                if mdl.E(st_key) is not None and st_array is not None:
                    pf_idx = vsc_index if is_vsc and vsc_index >= 0 else branch_index
                    st_ph = st_array[pf_idx] / sbase
                    self.set_if_exists(mdl=mdl, key=st_key, value=float(np.real(st_ph)))
                    st_sum += st_ph
                else:
                    pass

        for ph in phases:
            if_key: VarPowerFlowRefferenceType = if_key_dict[ph]
            it_key: VarPowerFlowRefferenceType = it_key_dict[ph]

            uses_currents: bool = (
                    (mdl.E(if_key) is not None)
                    or (mdl.E(it_key) is not None)
            )

            if uses_currents:
                sf_array = sf_array_dict[ph]
                st_array = st_array_dict[ph]
                voltage_from_array = voltage_from_dict[ph]
                voltage_to_array = voltage_to_dict[ph]

                pf_idx = vsc_index if is_vsc and vsc_index >= 0 else branch_index

                if sf_array is None or voltage_from_array is None:
                    i_f = 0.0 + 0.0j
                else:
                    sf_ph = sf_array[pf_idx] / sbase
                    vf_ph = voltage_from_array[f_bus_idx]
                    if abs(vf_ph) <= 1e-12:
                        i_f = 0.0 + 0.0j
                    else:
                        i_f = np.conj(sf_ph / vf_ph)

                if st_array is None or voltage_to_array is None:
                    i_t = 0.0 + 0.0j
                else:
                    st_ph = st_array[pf_idx] / sbase
                    vt_ph = voltage_to_array[t_bus_idx]
                    if abs(vt_ph) <= 1e-12:
                        i_t = 0.0 + 0.0j
                    else:
                        i_t = np.conj(st_ph / vt_ph)

                i_f0: float = np.sqrt(2.0) * np.imag(i_f)
                i_t0: float = np.sqrt(2.0) * np.imag(i_t)

                self.set_if_exists(mdl=mdl, key=if_key, value=float(i_f0))
                self.set_if_exists(mdl=mdl, key=it_key, value=float(i_t0))
            else:
                pass

        omega_base: float = 2.0 * np.pi * self.grid.fBase
        for ph in phases:
            d_vf_key: VarPowerFlowRefferenceType = d_vf_key_dict[ph]
            d_vt_key: VarPowerFlowRefferenceType = d_vt_key_dict[ph]
            voltage_from_array = voltage_from_dict[ph]
            voltage_to_array = voltage_to_dict[ph]
            if mdl.E(d_vf_key) is not None:
                if voltage_from_array is None:
                    vf_ph = 0.0 + 0.0j
                else:
                    vf_ph = voltage_from_array[f_bus_idx]
                d_vf: float = omega_base * np.sqrt(2.0) * np.real(vf_ph)
                self.set_external_param(mdl, d_vf_key, d_vf)
            if mdl.E(d_vt_key) is not None:
                if voltage_to_array is None:
                    vt_ph = 0.0 + 0.0j
                else:
                    vt_ph = voltage_to_array[t_bus_idx]
                d_vt: float = omega_base * np.sqrt(2.0) * np.real(vt_ph)
                self.set_external_param(mdl, d_vt_key, d_vt)

        self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Pf, value=float(np.real(sf_sum)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Qf, value=float(np.imag(sf_sum)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Pt, value=float(np.real(st_sum)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Qt, value=float(np.imag(st_sum)))


    def _try_set_branch_pf_init_balanced(
            self,
            mdl: Block,
            branch_index: int,
            f_bus_idx: int,
            t_bus_idx: int,
            sbase: float,
            is_vsc: bool = False,
            vsc_index: int = -1
    ) -> None:
        """
        Initialize branch variables from balanced power-flow results.

        The balanced PF provides:
          - one complex bus voltage phasor per bus in self.power_flow_results.voltage
          - one total three-phase branch power per end in self.power_flow_results.Sf/St

        This method reconstructs balanced phase quantities as:
          - V_A = V
          - V_B = V * exp(-j*2*pi/3)
          - V_C = V * exp(+j*2*pi/3)
          - V_N = 0

        and distributes total three-phase branch powers equally among phases:
          - S_phase = S_3ph / 3

        Then:
          - I_phase = conj(S_phase / V_phase)

        The method initializes:
          - per-phase branch powers Sf_* and St_*,
          - aggregated terminal powers Pf/Qf/Pt/Qt,
          - per-phase instantaneous terminal currents if_* and it_* at t = 0,
          - per-phase voltage derivatives d_v_* using the same EMT convention as in
            the original three-phase initializer.

        Neutral phase is initialized to zero.
        """
        if is_vsc and vsc_index >= 0:
            self._try_set_vsc_branch_pf_init_balanced(
                mdl=mdl,
                f_bus_idx=f_bus_idx,
                t_bus_idx=t_bus_idx,
                sbase=sbase,
                vsc_index=vsc_index,
            )
            return

        phases: List[str] = ["N", "A", "B", "C"]

        sf_key_dict: Dict[str, Optional[VarPowerFlowRefferenceType]] = {
            "N": None,
            "A": VarPowerFlowRefferenceType.Sf_A,
            "B": VarPowerFlowRefferenceType.Sf_B,
            "C": VarPowerFlowRefferenceType.Sf_C,
        }
        st_key_dict: Dict[str, Optional[VarPowerFlowRefferenceType]] = {
            "N": None,
            "A": VarPowerFlowRefferenceType.St_A,
            "B": VarPowerFlowRefferenceType.St_B,
            "C": VarPowerFlowRefferenceType.St_C,
        }

        if_key_dict: Dict[str, VarPowerFlowRefferenceType] = {
            "N": VarPowerFlowRefferenceType.if_N,
            "A": VarPowerFlowRefferenceType.if_A,
            "B": VarPowerFlowRefferenceType.if_B,
            "C": VarPowerFlowRefferenceType.if_C,
        }
        it_key_dict: Dict[str, VarPowerFlowRefferenceType] = {
            "N": VarPowerFlowRefferenceType.it_N,
            "A": VarPowerFlowRefferenceType.it_A,
            "B": VarPowerFlowRefferenceType.it_B,
            "C": VarPowerFlowRefferenceType.it_C,
        }
        d_vf_key_dict: Dict[str, VarPowerFlowRefferenceType] = {
            "N": VarPowerFlowRefferenceType.d_v_N_f,
            "A": VarPowerFlowRefferenceType.d_v_A_f,
            "B": VarPowerFlowRefferenceType.d_v_B_f,
            "C": VarPowerFlowRefferenceType.d_v_C_f,
        }
        d_vt_key_dict: Dict[str, VarPowerFlowRefferenceType] = {
            "N": VarPowerFlowRefferenceType.d_v_N_t,
            "A": VarPowerFlowRefferenceType.d_v_A_t,
            "B": VarPowerFlowRefferenceType.d_v_B_t,
            "C": VarPowerFlowRefferenceType.d_v_C_t,
        }

        pf_results = self.power_flow_results
        if pf_results is None:
            return

        alpha = 2.0 * np.pi / 3.0

        v_f_bus: CxVec = pf_results.voltage[f_bus_idx]
        v_t_bus: CxVec = pf_results.voltage[t_bus_idx]

        if is_vsc and vsc_index >= 0:
            try:
                pf_results_pfn_vsc = pf_results.Pfn_vsc[vsc_index]
            except AttributeError:
                pf_results_pfn_vsc = 0.0

            sf_total = complex(
                (
                    pf_results.Pfp_vsc[vsc_index]
                    + pf_results_pfn_vsc
                ) / sbase,
                0.0,
            )
            st_total = pf_results.St_vsc[vsc_index] / sbase

            voltage_dict: Dict[str, complex] = {
                "N": 0.0 + 0.0j,
                "A": 0.0 + 0.0j,
                "B": 0.0 + 0.0j,
                "C": 0.0 + 0.0j,
            }
            voltage_to_dict: Dict[str, CxVec] = {
                "N": 0.0 + 0.0j,
                "A": v_t_bus,
                "B": v_t_bus * np.exp(-1j * alpha),
                "C": v_t_bus * np.exp(+1j * alpha),
            }
        else:
            sf_total = pf_results.Sf[branch_index] / sbase
            st_total = pf_results.St[branch_index] / sbase

            voltage_dict = {
                "N": 0.0 + 0.0j,
                "A": v_f_bus,
                "B": v_f_bus * np.exp(-1j * alpha),
                "C": v_f_bus * np.exp(+1j * alpha),
            }
            voltage_to_dict = {
                "N": 0.0 + 0.0j,
                "A": v_t_bus,
                "B": v_t_bus * np.exp(-1j * alpha),
                "C": v_t_bus * np.exp(+1j * alpha),
            }

        sf_phase_total = sf_total / 3.0
        st_phase_total = st_total / 3.0

        sf_sum: complex = 0.0 + 0.0j
        st_sum: complex = 0.0 + 0.0j

        for ph in phases:
            sf_key: Optional[VarPowerFlowRefferenceType] = sf_key_dict[ph]
            st_key: Optional[VarPowerFlowRefferenceType] = st_key_dict[ph]

            if ph == "N":
                sf_ph = 0.0 + 0.0j
                st_ph = 0.0 + 0.0j
            elif is_vsc:
                sf_ph = 0.0 + 0.0j
                st_ph = st_phase_total
            else:
                sf_ph = sf_phase_total
                st_ph = st_phase_total

            if sf_key is not None:
                if mdl.E(sf_key) is not None:
                    self.set_if_exists(mdl=mdl, key=sf_key, value=float(np.real(sf_ph)))
                    sf_sum += sf_ph

            if st_key is not None:
                if mdl.E(st_key) is not None:
                    self.set_if_exists(mdl=mdl, key=st_key, value=float(np.real(st_ph)))
                    st_sum += st_ph

        for ph in phases:
            if_key: VarPowerFlowRefferenceType = if_key_dict[ph]
            it_key: VarPowerFlowRefferenceType = it_key_dict[ph]

            uses_currents: bool = (
                    (mdl.E(if_key) is not None)
                    or (mdl.E(it_key) is not None)
            )

            if uses_currents:
                vf_ph = voltage_dict[ph]
                vt_ph = voltage_to_dict[ph]

                if ph == "N":
                    i_f = 0.0 + 0.0j
                    i_t = 0.0 + 0.0j
                elif is_vsc:
                    i_f = 0.0 + 0.0j
                    if abs(vt_ph) <= 1e-12:
                        i_t = 0.0 + 0.0j
                    else:
                        i_t = np.conj(st_phase_total / vt_ph)
                else:
                    if abs(vf_ph) <= 1e-12:
                        i_f = 0.0 + 0.0j
                    else:
                        i_f = np.conj(sf_phase_total / vf_ph)

                    if abs(vt_ph) <= 1e-12:
                        i_t = 0.0 + 0.0j
                    else:
                        i_t = np.conj(st_phase_total / vt_ph)

                i_f0: float = np.sqrt(2.0) * np.imag(i_f)
                i_t0: float = np.sqrt(2.0) * np.imag(i_t)

                self.set_if_exists(mdl=mdl, key=if_key, value=float(i_f0))
                self.set_if_exists(mdl=mdl, key=it_key, value=float(i_t0))

        omega_base: float = 2.0 * np.pi * self.grid.fBase
        for ph in phases:
            d_vf_key: VarPowerFlowRefferenceType = d_vf_key_dict[ph]
            d_vt_key: VarPowerFlowRefferenceType = d_vt_key_dict[ph]

            vf_ph = voltage_dict[ph]
            vt_ph = voltage_to_dict[ph]

            if mdl.E(d_vf_key) is not None:
                d_vf: float = omega_base * np.sqrt(2.0) * np.real(vf_ph)
                self.set_external_param(mdl, d_vf_key, d_vf)

            if mdl.E(d_vt_key) is not None:
                d_vt: float = omega_base * np.sqrt(2.0) * np.real(vt_ph)
                self.set_external_param(mdl, d_vt_key, d_vt)

        if is_vsc and vsc_index >= 0:
            self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Pf, value=float(np.real(sf_total)))
            self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Qf, value=float(np.imag(sf_total)))
            self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Pt, value=float(np.real(st_total)))
            self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Qt, value=float(np.imag(st_total)))
        else:
            self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Pf, value=float(np.real(sf_sum)))
            self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Qf, value=float(np.imag(sf_sum)))
            self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Pt, value=float(np.real(st_sum)))
            self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.Qt, value=float(np.imag(st_sum)))

        if is_vsc and vsc_index >= 0:
            if self.power_flow_results is not None:
                P_vsc = -float(np.real(self.power_flow_results.St_vsc[vsc_index]))
                self.set_if_exists(mdl=mdl, key=VarPowerFlowRefferenceType.P, value=P_vsc)

    def _try_set_inj_pf_init(self,
                             inj,
                             mdl: Block,
                             bus_index: int,
                             sbase: float) -> None:
        """
        Initialize injection variables from three-phase power-flow results.

        The method initializes any per-phase current and power variables that are
        present in the model external mapping. It also initializes the aggregated
        active and reactive powers and, if available, the positive-sequence angle.

        :param inj: injection device
        :param mdl: Injection symbolic block.
        :param bus_index: Bus index in the power-flow results.
        :param sbase: Base power of the grid.
        :return: None
        """

        if inj.bus.is_dc:
            p_dc = float(np.real(self.power_flow_results.Sbus[bus_index]))
            v_dc = float(np.abs(self.power_flow_results.voltage[bus_index]))

            self.set_init_guess(mdl=mdl, reference_powerflow=VarPowerFlowRefferenceType.P,
                                val=p_dc)

            if v_dc != 0.0:
                self.set_if_exists(mdl=mdl,
                                   key=VarPowerFlowRefferenceType.Idc,
                                   value=p_dc / v_dc)
            else:
                self.set_if_exists(mdl=mdl,
                                   key=VarPowerFlowRefferenceType.Idc,
                                   value=0.0)

        else:

            phase_specs: List[Tuple[
                str, Any, Any, VarPowerFlowRefferenceType, VarPowerFlowRefferenceType, VarPowerFlowRefferenceType]] = [
                ("N", self.power_flow_results_3ph.Sbus_N, self.power_flow_results_3ph.voltage_N,
                 VarPowerFlowRefferenceType.i_N, VarPowerFlowRefferenceType.P_N, VarPowerFlowRefferenceType.Q_N),

                ("A", self.power_flow_results_3ph.Sbus_A, self.power_flow_results_3ph.voltage_A,
                 VarPowerFlowRefferenceType.i_A, VarPowerFlowRefferenceType.P_A, VarPowerFlowRefferenceType.Q_A),

                ("B", self.power_flow_results_3ph.Sbus_B, self.power_flow_results_3ph.voltage_B,
                 VarPowerFlowRefferenceType.i_B, VarPowerFlowRefferenceType.P_B, VarPowerFlowRefferenceType.Q_B),

                ("C", self.power_flow_results_3ph.Sbus_C, self.power_flow_results_3ph.voltage_C,
                 VarPowerFlowRefferenceType.i_C, VarPowerFlowRefferenceType.P_C, VarPowerFlowRefferenceType.Q_C),
            ]

            for _, S_arr, V_arr, i_key, P_key, Q_key in phase_specs:
                uses_any: bool = (
                        (mdl.E(i_key) is not None)
                        or (mdl.E(P_key) is not None)
                        or (mdl.E(Q_key) is not None)
                )

                if uses_any:
                    if S_arr is None or V_arr is None:
                        self.set_if_exists(mdl=mdl, key=i_key, value=0.0)
                        self.set_if_exists(mdl=mdl, key=P_key, value=0.0)
                        self.set_if_exists(mdl=mdl, key=Q_key, value=0.0)
                    else:
                        S = S_arr[bus_index] / sbase
                        V = V_arr[bus_index]

                        if V == 0:
                            I = 0.0 + 0.0j
                        else:
                            I = np.conj(S / V)

                        i0: float = np.sqrt(2.0) * np.imag(I)

                        self.set_if_exists(mdl=mdl, key=i_key, value=float(i0))
                        self.set_if_exists(mdl=mdl, key=P_key, value=float(np.real(S)))
                        self.set_if_exists(mdl=mdl, key=Q_key, value=float(np.imag(S)))

                else:
                    pass

            if mdl.E(VarPowerFlowRefferenceType.phi) is not None:
                a = np.exp(1j * 2.0 * np.pi / 3.0)

                # Terminal voltage phasors
                VA = self.power_flow_results_3ph.voltage_A[bus_index]
                VB = self.power_flow_results_3ph.voltage_B[bus_index]
                VC = self.power_flow_results_3ph.voltage_C[bus_index]

                # Terminal complex powers (generator convention must match PF sign)
                SA = self.power_flow_results_3ph.Sbus_A[bus_index] / sbase
                SB = self.power_flow_results_3ph.Sbus_B[bus_index] / sbase
                SC = self.power_flow_results_3ph.Sbus_C[bus_index] / sbase

                # Terminal current phasors leaving the generator
                IA = 0.0 + 0.0j if VA == 0 else np.conj(SA / VA)
                IB = 0.0 + 0.0j if VB == 0 else np.conj(SB / VB)
                IC = 0.0 + 0.0j if VC == 0 else np.conj(SC / VC)

                # Positive-sequence phasors
                V1 = (VA + a * VB + (a * a) * VC) / 3.0
                I1 = (IA + a * IB + (a * a) * IC) / 3.0

                phi_V = float(np.angle(V1))
                phi_I = float(np.angle(I1))
                ang = phi_I - phi_V
                phi = float(np.arctan2(np.sin(ang), np.cos(ang)))

                Vpk = np.sqrt(2) * np.abs(V1)
                Ipk = np.sqrt(2) * np.abs(I1)

                self.set_external_param(mdl, VarPowerFlowRefferenceType.phi_v, float(phi_V))
                self.set_external_param(mdl, VarPowerFlowRefferenceType.phi, float(phi))
                self.set_external_param(mdl, VarPowerFlowRefferenceType.Vpk, float(Vpk))
                self.set_external_param(mdl, VarPowerFlowRefferenceType.Ipk, float(Ipk))
            else:
                pass

            omega_base: float = 2.0 * np.pi * self.grid.fBase
            if mdl.E(VarPowerFlowRefferenceType.d_v_N) is not None:
                V_N = self.power_flow_results_3ph.voltage_N[bus_index]
                d_v_N: float = omega_base * np.sqrt(2.0) * np.real(V_N)
                self.set_external_param(mdl, VarPowerFlowRefferenceType.d_v_N, d_v_N)

            if mdl.E(VarPowerFlowRefferenceType.d_v_A) is not None:
                V_A = self.power_flow_results_3ph.voltage_A[bus_index]
                d_v_A: float = omega_base * np.sqrt(2.0) * np.real(V_A)
                self.set_external_param(mdl, VarPowerFlowRefferenceType.d_v_A, d_v_A)

            if mdl.E(VarPowerFlowRefferenceType.d_v_B) is not None:
                V_B = self.power_flow_results_3ph.voltage_B[bus_index]
                d_v_B: float = omega_base * np.sqrt(2.0) * np.real(V_B)
                self.set_external_param(mdl, VarPowerFlowRefferenceType.d_v_B, d_v_B)

            if mdl.E(VarPowerFlowRefferenceType.d_v_C) is not None:
                V_C = self.power_flow_results_3ph.voltage_C[bus_index]
                d_v_C: float = omega_base * np.sqrt(2.0) * np.real(V_C)
                self.set_external_param(mdl, VarPowerFlowRefferenceType.d_v_C, d_v_C)

    def _try_set_inj_pf_init_balanced(self,
                                      inj,
                                      mdl: Block,
                                      bus_index: int,
                                      sbase: float) -> None:
        """
        Initialize injection variables from balanced power-flow results.

        The method initializes any per-phase current and power variables that are
        present in the model external mapping. It also initializes the aggregated
        active and reactive powers and, if available, the positive-sequence angle.

        For AC buses, the balanced PF provides:
          - one complex bus-voltage phasor in self.power_flow_results.voltage
          - one total three-phase complex injected power in self.power_flow_results.Sbus

        Balanced phase quantities are reconstructed as:
          - V_A = V
          - V_B = V * exp(-j*2*pi/3)
          - V_C = V * exp(+j*2*pi/3)
          - V_N = 0

          - S_A = S_B = S_C = S_3ph / 3
          - S_N = 0

          - I_phase = conj(S_phase / V_phase)

        EMT initialization convention is kept identical to the three-phase version:
          - i(0) = sqrt(2) * imag(I)
          - d_v(0) = omega_base * sqrt(2) * real(V)
        """
        if inj.bus.is_dc:
            p_dc = float(np.real(self.power_flow_results.Sbus[bus_index]))
            v_dc = float(np.abs(self.power_flow_results.voltage[bus_index]))

            self.set_init_guess(mdl=mdl,
                                reference_powerflow=VarPowerFlowRefferenceType.P,
                                val=p_dc)

            if abs(v_dc) > 1e-12:
                self.set_if_exists(mdl=mdl,
                                   key=VarPowerFlowRefferenceType.Idc,
                                   value=p_dc / v_dc)
            else:
                self.set_if_exists(mdl=mdl,
                                   key=VarPowerFlowRefferenceType.Idc,
                                   value=0.0)

        else:
            pf_results = self.power_flow_results
            if pf_results is None:
                return

            alpha: float = 2.0 * np.pi / 3.0

            V_bus: CxVec = pf_results.voltage[bus_index]
            S_bus_3ph = pf_results.Sbus[bus_index] / sbase
            S_phase = S_bus_3ph / 3.0

            V_N: complex = 0.0 + 0.0j
            V_A: CxVec = V_bus
            V_B: complex = V_bus * np.exp(-1j * alpha)
            V_C: complex = V_bus * np.exp(+1j * alpha)

            S_N: complex = 0.0 + 0.0j
            S_A = S_phase
            S_B = S_phase
            S_C = S_phase

            phase_specs: List[Tuple[
                str,
                complex,
                complex,
                VarPowerFlowRefferenceType,
                VarPowerFlowRefferenceType,
                VarPowerFlowRefferenceType
            ]] = [
                ("N", S_N, V_N,
                 VarPowerFlowRefferenceType.i_N,
                 VarPowerFlowRefferenceType.P_N,
                 VarPowerFlowRefferenceType.Q_N),

                ("A", S_A, V_A,
                 VarPowerFlowRefferenceType.i_A,
                 VarPowerFlowRefferenceType.P_A,
                 VarPowerFlowRefferenceType.Q_A),

                ("B", S_B, V_B,
                 VarPowerFlowRefferenceType.i_B,
                 VarPowerFlowRefferenceType.P_B,
                 VarPowerFlowRefferenceType.Q_B),

                ("C", S_C, V_C,
                 VarPowerFlowRefferenceType.i_C,
                 VarPowerFlowRefferenceType.P_C,
                 VarPowerFlowRefferenceType.Q_C),
            ]

            for _, S, V, i_key, P_key, Q_key in phase_specs:
                uses_any: bool = (
                        (mdl.E(i_key) is not None)
                        or (mdl.E(P_key) is not None)
                        or (mdl.E(Q_key) is not None)
                )

                if uses_any:
                    if abs(V) <= 1e-12:
                        I = 0.0 + 0.0j
                    else:
                        I = np.conj(S / V)

                    i0: float = np.sqrt(2.0) * np.imag(I)

                    self.set_if_exists(mdl=mdl, key=i_key, value=float(i0))
                    self.set_if_exists(mdl=mdl, key=P_key, value=float(np.real(S)))
                    self.set_if_exists(mdl=mdl, key=Q_key, value=float(np.imag(S)))

            if mdl.E(VarPowerFlowRefferenceType.phi) is not None:
                a = np.exp(1j * 2.0 * np.pi / 3.0)

                # Terminal voltage phasors
                VA = V_A
                VB = V_B
                VC = V_C

                # Terminal complex powers
                SA = S_A
                SB = S_B
                SC = S_C

                # Terminal current phasors
                IA = 0.0 + 0.0j if abs(VA) <= 1e-12 else np.conj(SA / VA)
                IB = 0.0 + 0.0j if abs(VB) <= 1e-12 else np.conj(SB / VB)
                IC = 0.0 + 0.0j if abs(VC) <= 1e-12 else np.conj(SC / VC)

                # Positive-sequence phasors
                V1 = (VA + a * VB + (a * a) * VC) / 3.0
                I1 = (IA + a * IB + (a * a) * IC) / 3.0

                phi_V = float(np.angle(V1))
                phi_I = float(np.angle(I1))
                ang = phi_I - phi_V
                phi = float(np.arctan2(np.sin(ang), np.cos(ang)))

                Vpk = np.sqrt(2.0) * np.abs(V1)
                Ipk = np.sqrt(2.0) * np.abs(I1)

                self.set_external_param(mdl, VarPowerFlowRefferenceType.phi_v, float(phi_V))
                self.set_external_param(mdl, VarPowerFlowRefferenceType.phi, float(phi))
                self.set_external_param(mdl, VarPowerFlowRefferenceType.Vpk, float(Vpk))
                self.set_external_param(mdl, VarPowerFlowRefferenceType.Ipk, float(Ipk))

            omega_base: float = 2.0 * np.pi * self.grid.fBase

            if mdl.E(VarPowerFlowRefferenceType.d_v_N) is not None:
                d_v_N: float = omega_base * np.sqrt(2.0) * np.real(V_N)
                self.set_external_param(mdl, VarPowerFlowRefferenceType.d_v_N, d_v_N)

            if mdl.E(VarPowerFlowRefferenceType.d_v_A) is not None:
                d_v_A: float = omega_base * np.sqrt(2.0) * np.real(V_A)
                self.set_external_param(mdl, VarPowerFlowRefferenceType.d_v_A, d_v_A)

            if mdl.E(VarPowerFlowRefferenceType.d_v_B) is not None:
                d_v_B: float = omega_base * np.sqrt(2.0) * np.real(V_B)
                self.set_external_param(mdl, VarPowerFlowRefferenceType.d_v_B, d_v_B)

            if mdl.E(VarPowerFlowRefferenceType.d_v_C) is not None:
                d_v_C: float = omega_base * np.sqrt(2.0) * np.real(V_C)
                self.set_external_param(mdl, VarPowerFlowRefferenceType.d_v_C, d_v_C)

    def _try_set_bergeron_pf_init(
            self,
            mdl: Block,
            rt: BergeronHistoryRuntime,
            branch_index: int,
            f_bus_idx: int,
            t_bus_idx: int,
            sbase: float
    ) -> None:
        """
        Initialize Bergeron history terms from three-phase power-flow results.

        The history sources are initialized so that, at t = 0:
            i_f(0) = Gc * v_f(0) + Ih_f(0)
            i_t(0) = Gc * v_t(0) + Ih_t(0)

        Hence:
            Ih_f(0) = i_f(0) - Gc * v_f(0)
            Ih_t(0) = i_t(0) - Gc * v_t(0)

        Only active phases in the Bergeron runtime are considered.
        """
        voltage_dict: Dict[str, Optional[np.ndarray]] = {
            "N": self.power_flow_results_3ph.voltage_N,
            "A": self.power_flow_results_3ph.voltage_A,
            "B": self.power_flow_results_3ph.voltage_B,
            "C": self.power_flow_results_3ph.voltage_C,
        }

        sf_array_dict: Dict[str, Optional[np.ndarray]] = {
            "N": None,
            "A": self.power_flow_results_3ph.Sf_A,
            "B": self.power_flow_results_3ph.Sf_B,
            "C": self.power_flow_results_3ph.Sf_C,
        }

        st_array_dict: Dict[str, Optional[np.ndarray]] = {
            "N": None,
            "A": self.power_flow_results_3ph.St_A,
            "B": self.power_flow_results_3ph.St_B,
            "C": self.power_flow_results_3ph.St_C,
        }

        v_f0_red = np.zeros(rt.m, dtype=np.float64)
        v_t0_red = np.zeros(rt.m, dtype=np.float64)
        i_f0_red = np.zeros(rt.m, dtype=np.float64)
        i_t0_red = np.zeros(rt.m, dtype=np.float64)

        for k, ph in enumerate(rt.active_ph):
            voltage_array = voltage_dict[ph]

            if voltage_array is None:
                vf_ph = 0.0 + 0.0j
                vt_ph = 0.0 + 0.0j
            else:
                vf_ph = voltage_array[f_bus_idx]
                vt_ph = voltage_array[t_bus_idx]

            # Instantaneous voltage at t = 0 with your EMT convention
            v_f0_red[k] = float(np.sqrt(2.0) * np.imag(vf_ph))
            v_t0_red[k] = float(np.sqrt(2.0) * np.imag(vt_ph))

            sf_array = sf_array_dict[ph]
            st_array = st_array_dict[ph]

            if sf_array is None or abs(vf_ph) <= 1e-12:
                i_f = 0.0 + 0.0j
            else:
                sf_ph = sf_array[branch_index] / sbase
                i_f = np.conj(sf_ph / vf_ph)

            if st_array is None or abs(vt_ph) <= 1e-12:
                i_t = 0.0 + 0.0j
            else:
                st_ph = st_array[branch_index] / sbase
                i_t = np.conj(st_ph / vt_ph)

            # Instantaneous current at t = 0 with your EMT convention
            i_f0_red[k] = float(np.sqrt(2.0) * np.imag(i_f))
            i_t0_red[k] = float(np.sqrt(2.0) * np.imag(i_t))

        Ih_f0_red = i_f0_red - rt.Gc_red @ v_f0_red
        Ih_t0_red = i_t0_red - rt.Gc_red @ v_t0_red

        for k in range(rt.m):
            mdl.event_dict[rt.Ih_f[k]] = self.grid.var_factory.add_const(float(Ih_f0_red[k]))
            mdl.event_dict[rt.Ih_t[k]] = self.grid.var_factory.add_const(float(Ih_t0_red[k]))

        rt.initialize_buffers_from_initial_point(
            v_f0_red=v_f0_red,
            v_t0_red=v_t0_red,
            i_f0_red=i_f0_red,
            i_t0_red=i_t0_red,
        )

    def _try_set_bergeron_pf_init_balanced(
            self,
            mdl: Block,
            rt: BergeronHistoryRuntime,
            branch_index: int,
            f_bus_idx: int,
            t_bus_idx: int,
            sbase: float
    ) -> None:
        """
        Initialize Bergeron history terms from balanced power-flow results.

        Assumptions
        -----------
        - self.power_flow_results.voltage contains one complex bus-voltage phasor per bus
          (balanced positive-sequence representation).
        - self.power_flow_results.Sf and self.power_flow_results.St contain the total
          three-phase complex power at each branch end.
        - The balanced abc phase voltages are reconstructed from the bus phasor as:
                V_A = V1
                V_B = V1 * exp(-j*2*pi/3)
                V_C = V1 * exp(+j*2*pi/3)
        - Per-phase power is:
                S_phase = S_3ph / 3
        - Per-phase current is:
                I_phase = conj(S_phase / V_phase)

        EMT initialization convention kept identical to the existing 3-phase version:
                x(0) = sqrt(2) * imag(X_phasor)

        Neutral phase, if present, is initialized to zero.
        """
        pf_results = self.power_flow_results

        alpha = 2.0 * np.pi / 3.0

        v_f_bus = pf_results.voltage[f_bus_idx]
        v_t_bus = pf_results.voltage[t_bus_idx]

        s_f_3ph = pf_results.Sf[branch_index] / sbase
        s_t_3ph = pf_results.St[branch_index] / sbase

        s_f_phase = s_f_3ph / 3.0
        s_t_phase = s_t_3ph / 3.0

        v_f0_red = np.zeros(rt.m, dtype=np.float64)
        v_t0_red = np.zeros(rt.m, dtype=np.float64)
        i_f0_red = np.zeros(rt.m, dtype=np.float64)
        i_t0_red = np.zeros(rt.m, dtype=np.float64)

        for k, ph in enumerate(rt.active_ph):

            if ph == "N":
                vf_ph = 0.0 + 0.0j
                vt_ph = 0.0 + 0.0j
                i_f = 0.0 + 0.0j
                i_t = 0.0 + 0.0j

            elif ph == "A":
                vf_ph = v_f_bus
                vt_ph = v_t_bus

                if abs(vf_ph) <= 1e-12:
                    i_f = 0.0 + 0.0j
                else:
                    i_f = np.conj(s_f_phase / vf_ph)

                if abs(vt_ph) <= 1e-12:
                    i_t = 0.0 + 0.0j
                else:
                    i_t = np.conj(s_t_phase / vt_ph)

            elif ph == "B":
                vf_ph = v_f_bus * np.exp(-1j * alpha)
                vt_ph = v_t_bus * np.exp(-1j * alpha)

                if abs(vf_ph) <= 1e-12:
                    i_f = 0.0 + 0.0j
                else:
                    i_f = np.conj(s_f_phase / vf_ph)

                if abs(vt_ph) <= 1e-12:
                    i_t = 0.0 + 0.0j
                else:
                    i_t = np.conj(s_t_phase / vt_ph)

            elif ph == "C":
                vf_ph = v_f_bus * np.exp(+1j * alpha)
                vt_ph = v_t_bus * np.exp(+1j * alpha)

                if abs(vf_ph) <= 1e-12:
                    i_f = 0.0 + 0.0j
                else:
                    i_f = np.conj(s_f_phase / vf_ph)

                if abs(vt_ph) <= 1e-12:
                    i_t = 0.0 + 0.0j
                else:
                    i_t = np.conj(s_t_phase / vt_ph)

            else:
                raise ValueError(f"Unsupported phase label in Bergeron runtime: {ph}")

            # Instantaneous values at t = 0 using the same EMT convention as the original code
            v_f0_red[k] = float(np.sqrt(2.0) * np.imag(vf_ph))
            v_t0_red[k] = float(np.sqrt(2.0) * np.imag(vt_ph))
            i_f0_red[k] = float(np.sqrt(2.0) * np.imag(i_f))
            i_t0_red[k] = float(np.sqrt(2.0) * np.imag(i_t))

        Ih_f0_red = i_f0_red - rt.Gc_red @ v_f0_red
        Ih_t0_red = i_t0_red - rt.Gc_red @ v_t0_red

        for k in range(rt.m):
            mdl.event_dict[rt.Ih_f[k]] = self.grid.var_factory.add_const(float(Ih_f0_red[k]))
            mdl.event_dict[rt.Ih_t[k]] = self.grid.var_factory.add_const(float(Ih_t0_red[k]))

        rt.initialize_buffers_from_initial_point(
            v_f0_red=v_f0_red,
            v_t0_red=v_t0_red,
            i_f0_red=i_f0_red,
            i_t0_red=i_t0_red,
        )


    # ---------------------------------------------------------------------
    # UTILS
    # ---------------------------------------------------------------------
    def set_if_exists(self,
                      mdl: Block,
                      key: VarPowerFlowRefferenceType,
                      value: float) -> None:
        """
        Set an initialization value only if the external mapping contains the key.

        :param mdl: Model block containing the external mapping.
        :param key: External mapping key.
        :param value: Initialization value.
        :return: None
        """
        external_mapping: Optional[Dict[Any, Var]] = _get_external_mapping(mdl)

        if external_mapping is None:
            pass
        else:
            mapped_var: Optional[Var] = external_mapping.get(key, None)

            if mapped_var is None:
                pass
            else:
                if mapped_var in mdl.event_dict:
                    mdl.event_dict[mapped_var] = self.grid.var_factory.add_const(float(value))
                else:
                    self._temp_init_guess[mapped_var.uid] = float(value)

    def _initialize_mode_event_state(self) -> None:
        """
        Initialize the mode event cursor state.

        :return: None
        """
        for uid, event_list in self._scheduled_mode_events.items():
            event_list.sort(key=_get_mode_event_sort_key)
            self._mode_event_cursor[uid] = 0

    def _apply_scheduled_mode_events(self, t_curr: float, full_params: np.ndarray) -> None:
        """
        Apply scheduled retained mode events to the flat full parameter vector.

        :param t_curr: Current simulation time.
        :param full_params: Flat full parameter vector.
        :return: None
        """
        for uid, event_list in self._scheduled_mode_events.items():
            event_idx: int = self._mode_event_cursor.get(uid, 0)

            while event_idx < len(event_list) and t_curr >= event_list[event_idx][0]:
                event_time: float = event_list[event_idx][0]
                event_value: float = event_list[event_idx][1]
                force_step_alignment: bool = event_list[event_idx][2]

                runtime_idx: Optional[int] = self.uid2idx_event_params.get(uid, None)
                is_time_aligned: bool = _is_time_aligned(t_curr, event_time)

                if force_step_alignment:
                    if is_time_aligned:
                        if runtime_idx is not None:
                            full_params[runtime_idx] = event_value
                        else:
                            pass
                    else:
                        raise RuntimeError(
                            f"Scheduled EMT mode event at t={event_time} requires exact step alignment, "
                            f"but current solver time is t={t_curr}. Adjust the EMT time step or enable step splitting."
                        )
                else:
                    if runtime_idx is not None:
                        full_params[runtime_idx] = event_value
                    else:
                        pass

                event_idx += 1

            self._mode_event_cursor[uid] = event_idx

    def _collect_runtime_mode_parameters(self) -> List[Var]:
        """
        Collect runtime parameters that must be retained between steps.

        This includes:
          - scheduled discrete mode parameters,
          - Bergeron line history parameters, which are updated explicitly by the runtime.
        """
        mode_parameters: List[Var] = list()
        seen: Set[int] = set()

        # 1) Scheduled mode parameters already registered through mode_dict
        for parameter in self.get_runtime_mode_parameters():
            if parameter.uid not in seen:
                seen.add(parameter.uid)
                mode_parameters.append(parameter)

        # 2) Bergeron history parameters must also be retained
        for rt in self.history_models:
            for parameter in rt.Ih_f:
                if parameter.uid not in seen:
                    seen.add(parameter.uid)
                    mode_parameters.append(parameter)

            for parameter in rt.Ih_t:
                if parameter.uid not in seen:
                    seen.add(parameter.uid)
                    mode_parameters.append(parameter)

        return mode_parameters

    def add_device_var(self, dev: ALL_DEV_TYPES, var: Var)->None:
        """
        Registers a variable belonging to a specific device.
        """
        var_list = self._vars_info.get(dev, None)
        if var_list is None:
            self._vars_info[dev] = [var]
        else:
            var_list.append(var)

    def set_init_guess(self, mdl: Block, reference_powerflow: Any, val: float) -> None:
        """
        Set the temporary initial guess for a mapped variable during the parsing phase.

        :param mdl: Model block containing the external mapping.
        :param reference_powerflow: Reference key used to locate the mapped variable.
        :param val: Initialization value.
        :return: None
        """
        external_mapping: Optional[Dict[Any, Var]] = _get_external_mapping(mdl)

        if external_mapping is None:
            pass
        else:
            var: Optional[Var] = external_mapping.get(reference_powerflow, None)

            if var is None:
                pass
            else:
                self._temp_init_guess[var.uid] = float(val)

    def set_diff_init_guess(self, mdl: Block, reference_powerflow: Any, val: float) -> None:
        """
        Set the temporary initial guess for a mapped differential variable during the parsing phase.

        :param mdl: Model block containing the external mapping.
        :param reference_powerflow: Reference key used to locate the mapped differential variable.
        :param val: Initialization value.
        :return: None
        """
        external_mapping: Optional[Dict[Any, Var]] = _get_external_mapping(mdl)

        if external_mapping is None:
            pass
        else:
            diff_var: Optional[Var] = external_mapping.get(reference_powerflow, None)

            if diff_var is None:
                pass
            else:
                self._temp_diff_init_guess[diff_var.uid] = float(val)

    def set_external_param(self, mdl: Block, key: VarPowerFlowRefferenceType, value: float) -> None:
        """
        Set a PF-derived value either as an event parameter if the mapped variable belongs to mdl.event_dict.
        """
        var = mdl.E(key)

        if var is None:
            return

        if var in mdl.event_dict:
            mdl.event_dict[var] = self.grid.var_factory.add_const(float(value))
        else:
            pass

    def get_init_guess_info(self) -> pd.DataFrame:
        """
        Return a table with the explicitly initialized variable guesses.

        :return: DataFrame with UID, variable name and initialization value.
        """
        rows: List[Dict[str, Any]] = list()
        all_vars: Dict[int, Var] = dict()

        for var in self._state_vars:
            all_vars[var.uid] = var

        for var in self._algebraic_vars:
            all_vars[var.uid] = var

        for uid, value in self.init_guess.items():
            if uid in all_vars:
                rows.append({
                    "uid": uid,
                    "var_name": all_vars[uid].name,
                    "value": value,
                })
            else:
                pass

        return pd.DataFrame(rows)

    def get_device_vars_dict(self) -> Dict[ALL_DEV_TYPES, List[Var]]:
        """
        Returns the dictionary mapping electrical devices to their variables.
        """
        return self._vars_info

    @property
    def vars_glob_name2uid(self) -> Dict[str, int]:
        """
        Returns the dictionary mapping global variable names to UIDs.
        """
        return self._vars_glob_name2uid

    @property
    def boundary_update(self) -> EmtBoundaryUpdateProtocol | None:
        """
        Return the endogenous EMT boundary updater consumed by the EMT solvers.
        """
        if len(self._scheduled_mode_events) == 0 and len(self.history_models) == 0:
            return None

        return self

    def reset_boundary_update_state(self, t0: float = 0.0) -> None:
        """
        Reset the EMT boundary update state before a new solver run starts.

        :param t0: Initial simulation time.
        :return: None
        """
        super().reset_boundary_update_state(t0)
        self.step_counter = 0
        self._mode_event_cursor = dict()
        self._initialize_mode_event_state()

    def emt_boundary_update(
            self,
            t_curr: float,
            x_prev: np.ndarray,
            full_params: np.ndarray
    ) -> None:
        """
        Update runtime boundaries before the Newton step.

        Retained mode events are applied first. Afterwards, history-dependent EMT
        models update their internal boundary data.

        :param t_curr: Current simulation time.
        :param x_prev: Previous accepted state vector.
        :param full_params: Flat full parameter vector.
        :return: None
        """
        self._apply_scheduled_mode_events(t_curr, full_params)

        for rt in self.history_models:
            rt.update_history(self.step_counter, x_prev, full_params)

        # Persist the updated runtime parameters so the next step sees them
        n_runtime: int = self.get_variable_parameter_number()
        self._event_params_values[:] = full_params[:n_runtime]

        self.step_counter += 1

    def get_next_forced_event_time(self, t_prev: float, t_target: float) -> Optional[float]:
        """
        Return the earliest forced-alignment event time in the interval
        (t_prev, t_target].

        :param t_prev: Previous solver time.
        :param t_target: Nominal target time.
        :return: Earliest forced event time or None.
        """
        return _get_next_forced_mode_event_time(self._scheduled_mode_events, t_prev, t_target)

    def update(self, t: float, x: np.ndarray, params: np.ndarray) -> None:
        """
        Boundary update entry point compatible with BoundaryUpdateWrapper.

        :param t: Current simulation time.
        :param x: Previous accepted state vector.
        :param params: Flat full parameter vector.
        :return: None
        """
        self.emt_boundary_update(t, x, params)

    def get_floquet_ak_stack(
            self,
            trajectory: np.ndarray,
            h: float,
            jac_evaluator: Optional[Any] = None,
            static_params: Optional[np.ndarray] = None
    ) -> Optional[np.ndarray]:
        """
        Return the stack of reduced transition matrices used for Floquet analysis.

        :param trajectory: State trajectory over one period.
        :param h: Time step.
        :param jac_evaluator: Optional Jacobian evaluator.
        :param static_params: Optional static parameter vector.
        :return: Stack of reduced transition matrices or None.
        """
        if jac_evaluator is None:
            self.logger.add_warning(
                msg="No Jacobian evaluator was provided for Floquet Ak stack computation.",
                device="EmtProblemDae",
                value="None",
                expected_value="Callable Jacobian evaluator",
                device_class="EMT",
                device_property="jac_evaluator"
            )
            return None
        else:
            pass

        n = self.get_states_number()
        steps = len(trajectory) - 1

        if steps <= 0:
            return None

        stack = np.zeros((steps, n, n), order='C')

        for i in range(steps):
            x_k = trajectory[i]

            J = jac_evaluator(x_k, static_params, x_k, None, h, None)

            J11 = J[:n, :n]
            J12 = J[:n, n:]
            J21 = J[n:, :n]
            J22 = J[n:, n:]

            J22_inv_J21 = spla.spsolve(J22, J21)

            J_red = (J11 - J12 @ J22_inv_J21)

            if sp.issparse(J_red):
                J_red = J_red.toarray()

            stack[i] = la.inv(h * J_red)

        return stack

    def get_init_guess_table(self,
                             include_all_vars: bool = True,
                             only_in_init_guess: bool = False,
                             tol_zero: float = 1e-12) -> pd.DataFrame:
        """
        Return a table with uid, alias/name and initial value for each variable.

        include_all_vars:
            - True: include all state+algebraic vars, even if not in init_guess (value=0).
            - False: include only uids present in init_guess (or only_in_init_guess=True).

        only_in_init_guess:
            - True: filter to only those explicitly initialized (uid in init_guess).
            - False: keep everything (depending on include_all_vars).

        tol_zero:
            threshold to flag values close to zero.
        """
        # Build x0 and dx0 from current guesses
        x0 = self.get_x0()
        dx0 = self.get_dx0()

        uid2idx_vars = self.uid2idx_vars
        uid2idx_diff = self.uid2idx_diff

        # Define the sets we want to process: (Variables, Guess_Source, Index_Map, Vector, Label)
        data_sets = [
            (list(self.get_state_vars()) + list(self.get_algebraic_vars()), self.init_guess, uid2idx_vars, x0, "Var"),
            (list(self.get_diff_vars()), self.diff_init_guess, uid2idx_diff, dx0, "DiffVar")
        ]

        rows: List[Dict[str, Any]] = list()
        for vars_list, guess_dict, idx_map, vector, var_type in data_sets:
            for v in vars_list:
                uid = v.uid
                idx = idx_map.get(uid, None)
                val = float(vector[idx]) if idx is not None else 0.0

                in_guess = uid in guess_dict

                keep_row = True
                if only_in_init_guess and (not in_guess):
                    keep_row = False
                if (not include_all_vars) and (not in_guess):
                    keep_row = False

                if keep_row:
                    alias: Optional[str] = self._alias_names_dict.get(uid, None)

                    rows.append({
                        "uid": uid,
                        "type": var_type,
                        "idx": idx,  # add this
                        "alias": alias,
                        "name": v.name,
                        "value": val,
                        "in_init_guess": in_guess,
                        "is_zero": abs(val) <= tol_zero,
                    })
                else:
                    pass

        df = pd.DataFrame(rows)

        # Nice ordering: Group by type, then initialization status
        if not df.empty:
            df = df.sort_values(["type", "idx"], ascending=[False, True])

        return df

    def _assign_vsc_event_param_if_present(self, vsc: Any , key: ParamPowerFlowRefferenceType, value: Any) -> None:
        api_obj_mapping_local: Any = vsc.emt_model.api_obj_mapping
        if isinstance(api_obj_mapping_local, dict):
            target_local: Any | None = api_obj_mapping_local.get(key, None)
            if target_local is not None:
                if target_local in vsc.emt_model.event_dict:
                    vsc.emt_model.event_dict[target_local] = self._to_const(value)
                else:
                    vsc.emt_model.parameters[target_local] = self._to_const(value)
            else:
                pass
        else:
            pass

    def _assign_api_obj_mapping_branch(self,
                                       br: Any,
                                       is_vsc: bool,
                                       vsc_index: int) -> None:
        """
        Assign branch EMT mapped parameters into the API object mapping.

        The routine supports the historical pi-line mapping contract and the
        classical transformer coupled-winding contract. Each template exposes a
        fixed symbolic parameter interface, and this stage injects the numerical
        values derived from the corresponding static API object.

        :param br: Branch device whose EMT model receives the mapped values.
        :return: None.
        :raises ValueError: If the reduced physical matrices are inconsistent.
        """
        if is_vsc:
            vsc = br
            if 0 <= vsc_index < len(self.grid.vsc_devices):
                vsc = self.grid.vsc_devices[vsc_index]

            p_loss0: float = 0.0
            p0_vsc: float = 0.0
            if self.power_flow_results is not None:
                try:
                    p_loss0 = float(self.power_flow_results.losses_vsc[vsc_index])
                except (AttributeError, IndexError, TypeError, ValueError):
                    p_loss0 = 0.0

                try:
                    p0_vsc = float(np.real(self.power_flow_results.St_vsc[vsc_index]))
                except (AttributeError, IndexError, TypeError, ValueError):
                    p0_vsc = 0.0

            control_code_dict: Dict[ConverterControlType | None, float] = {
                None: 0.0,
                ConverterControlType.Vm_dc: 1.0,
                ConverterControlType.Vm_ac: 2.0,
                ConverterControlType.Va_ac: 3.0,
                ConverterControlType.Qac: 4.0,
                ConverterControlType.Pdc: 5.0,
                ConverterControlType.Pac: 6.0,
                ConverterControlType.Pdc_angle_droop: 7.0,
                ConverterControlType.Imax: 8.0,
            }

            self._assign_vsc_event_param_if_present(vsc=vsc, key=ParamPowerFlowRefferenceType.Sbase, value=self.grid.Sbase)
            self._assign_vsc_event_param_if_present(vsc=vsc, key=ParamPowerFlowRefferenceType.omega_base,
                                                    value= 2.0 * np.pi * self.grid.fBase)
            self._assign_vsc_event_param_if_present(vsc=vsc, key=ParamPowerFlowRefferenceType.P0, value=p0_vsc)
            self._assign_vsc_event_param_if_present(vsc=vsc, key=ParamPowerFlowRefferenceType.P_loss0, value=p_loss0)
            self._assign_vsc_event_param_if_present(vsc=vsc, key=ParamPowerFlowRefferenceType.control1,
                value=control_code_dict[vsc.control1])
            self._assign_vsc_event_param_if_present(vsc=vsc, key=ParamPowerFlowRefferenceType.control2,
                value=control_code_dict[vsc.control2])
            self._assign_vsc_event_param_if_present(vsc=vsc, key=ParamPowerFlowRefferenceType.control1_val,
                value=vsc.control1_val)
            self._assign_vsc_event_param_if_present(vsc=vsc, key=ParamPowerFlowRefferenceType.control2_val,
                value=vsc.control2_val)
            return

        api_obj_mapping: Any = br.emt_model.api_obj_mapping
        if not isinstance(api_obj_mapping, dict):
            return

        # -----------------------------
        # 1. Handle the XFMR EMT transformer mapping before the classical
        # transformer path and before the line path.
        # -----------------------------
        xfmr_keys: list[ParamPowerFlowRefferenceType] = list([
            ParamPowerFlowRefferenceType.xfmr_s_rated_mva,
            ParamPowerFlowRefferenceType.xfmr_sc_voltage_pct,
            ParamPowerFlowRefferenceType.xfmr_sc_resistance_pct,
            ParamPowerFlowRefferenceType.xfmr_oc_current_pct,
            ParamPowerFlowRefferenceType.xfmr_oc_loss_kw,
            ParamPowerFlowRefferenceType.xfmr_tap_module,
            ParamPowerFlowRefferenceType.xfmr_c_term,
            ParamPowerFlowRefferenceType.xfmr_cf_aa,
            ParamPowerFlowRefferenceType.xfmr_ct_aa,
        ])
        has_xfmr_mapping: bool = all(key in api_obj_mapping for key in xfmr_keys)

        if has_xfmr_mapping:
            if isinstance(br, Transformer2W):
                w0: float = 2.0 * np.pi * float(self.grid.fBase)
                eps_value: float = 1e-12

                sn_value: float = max(float(br.Sn), 1e-9)
                hv_value: float = float(br.HV) if br.HV is not None else 1.0
                lv_value: float = float(br.LV) if br.LV is not None else 1.0
                vsc_pct_value: float
                pcu_kw_value: float = max(float(br.Pcu), 0.0)
                pfe_kw_value: float = max(float(br.Pfe), 0.0)
                i0_pct_value: float = max(float(br.I0), 0.0)
                tap_module_value: float = float(br.tap_module) if abs(float(br.tap_module)) > eps_value else 1.0

                if float(br.Vsc) > 0.0:
                    vsc_pct_value = float(br.Vsc)
                else:
                    vsc_pct_value = 100.0 * np.sqrt(max(float(br.R) * float(br.R) + float(br.X) * float(br.X), 0.0))

                sc_resistance_pct_value: float
                if pcu_kw_value > 0.0:
                    sc_resistance_pct_value = pcu_kw_value / (10.0 * sn_value)
                else:
                    sc_resistance_pct_value = 100.0 * max(float(br.R), 0.0)

                c_term_value: float
                if sn_value > eps_value and abs(float(br.B)) > eps_value:
                    c_term_value = 0.5 * max(abs(float(br.B)) / (w0 + eps_value), 0.0)
                else:
                    c_term_value = 0.0

                oc_loss_pu_value: float = pfe_kw_value / (1000.0 * sn_value)
                oc_current_pu_value: float = i0_pct_value / 100.0
                i_mag_pu_value: float = np.sqrt(max(oc_current_pu_value * oc_current_pu_value - oc_loss_pu_value * oc_loss_pu_value, 0.0))
                if i_mag_pu_value > eps_value:
                    linear_lm_value: float = 1.0 / i_mag_pu_value
                else:
                    linear_lm_value = 1e6

                c_f_matrix: np.ndarray = _xfmr_connection_matrix(br.conn_f)
                c_t_matrix: np.ndarray = _xfmr_connection_matrix(br.conn_t)
                p_t_matrix: np.ndarray = _xfmr_phase_permutation_matrix(int(br.vector_group_number))
                c_t_eff_matrix: np.ndarray = p_t_matrix @ c_t_matrix

                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.omega_base, w0)
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_s_rated_mva, sn_value)
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_v_hv_ll_kv, hv_value)
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_v_lv_ll_kv, lv_value)
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_vector_group_clock, float(br.vector_group_number))
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_oc_current_pct, i0_pct_value)
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_oc_loss_kw, pfe_kw_value)
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_sc_voltage_pct, vsc_pct_value)
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_sc_resistance_pct, sc_resistance_pct_value)
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_sc_loss_kw, pcu_kw_value)
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_tap_module, tap_module_value)
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_c_term, c_term_value)
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_core_linear_l_pu, linear_lm_value)
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_core_a_prime, linear_lm_value)
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_core_b_prime, 0.0)
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_use_linear_core, 1.0)

                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_cf_aa, float(c_f_matrix[0, 0]))
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_cf_ab, float(c_f_matrix[0, 1]))
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_cf_ac, float(c_f_matrix[0, 2]))
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_cf_ba, float(c_f_matrix[1, 0]))
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_cf_bb, float(c_f_matrix[1, 1]))
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_cf_bc, float(c_f_matrix[1, 2]))
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_cf_ca, float(c_f_matrix[2, 0]))
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_cf_cb, float(c_f_matrix[2, 1]))
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_cf_cc, float(c_f_matrix[2, 2]))

                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_ct_aa, float(c_t_eff_matrix[0, 0]))
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_ct_ab, float(c_t_eff_matrix[0, 1]))
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_ct_ac, float(c_t_eff_matrix[0, 2]))
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_ct_ba, float(c_t_eff_matrix[1, 0]))
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_ct_bb, float(c_t_eff_matrix[1, 1]))
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_ct_bc, float(c_t_eff_matrix[1, 2]))
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_ct_ca, float(c_t_eff_matrix[2, 0]))
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_ct_cb, float(c_t_eff_matrix[2, 1]))
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_ct_cc, float(c_t_eff_matrix[2, 2]))
                return
            else:
                return

        # -----------------------------
        # 2. Handle the classical transformer mapping before the line path.
        # The transformer block now exposes only symbolic winding parameters,
        # so the EMT assembler must derive and assign the numerical values here.
        # -----------------------------
        transformer_keys: list[ParamPowerFlowRefferenceType] = list([
            ParamPowerFlowRefferenceType.xfmr_r1,
            ParamPowerFlowRefferenceType.xfmr_r2,
            ParamPowerFlowRefferenceType.xfmr_l1,
            ParamPowerFlowRefferenceType.xfmr_l2,
            ParamPowerFlowRefferenceType.xfmr_m,
            ParamPowerFlowRefferenceType.xfmr_gm,
        ])
        has_transformer_mapping: bool = all(key in api_obj_mapping for key in transformer_keys)

        if has_transformer_mapping:
            if isinstance(br, Transformer2W):
                fbase: float = float(self.grid.fBase)
                w0: float = 2.0 * np.pi * fbase
                eps_value: float = 1e-12

                tap_module: float = float(br.tap_module)
                n_tap: float
                if abs(tap_module) > eps_value:
                    n_tap = tap_module
                else:
                    n_tap = 1.0

                n_sq: float = n_tap * n_tap
                r_total: float = float(br.R)
                x_total: float = float(br.X)
                g_core: float = float(br.G)
                b_magnetizing: float = float(br.B)

                # -----------------------------
                # Split the short-circuit branch equally between both windings so
                # the primary-side equivalent remains equal to the static branch
                # data. The magnetizing susceptance sets the mutual coupling, and
                # when it is absent we fall back to a very large inductance so the
                # historical nearly-open magnetizing branch behavior is preserved.
                # -----------------------------
                l_sigma_primary: float = 0.5 * x_total / (w0 + eps_value)
                l_sigma_secondary: float = l_sigma_primary / (n_sq + eps_value)

                x_magnetizing: float
                if abs(b_magnetizing) > eps_value:
                    x_magnetizing = 1.0 / abs(b_magnetizing)
                else:
                    x_magnetizing = max(abs(x_total), 1.0) * 1e6

                l_m_primary: float = x_magnetizing / (w0 + eps_value)
                l_m_secondary: float = l_m_primary / (n_sq + eps_value)
                mutual_inductance: float = l_m_primary / (n_tap + np.sign(n_tap) * eps_value)

                r1_value: float = 0.5 * r_total
                r2_value: float = 0.5 * r_total / (n_sq + eps_value)
                l1_value: float = l_sigma_primary + l_m_primary
                l2_value: float = l_sigma_secondary + l_m_secondary
                det_value: float = l1_value * l2_value - mutual_inductance * mutual_inductance

                if det_value <= eps_value:
                    raise ValueError(
                        f"Transformer '{br.name}' has a non-physical inductance matrix determinant {det_value}."
                    )
                else:
                    pass

                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_r1, r1_value)
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_r2, r2_value)
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_l1, l1_value)
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_l2, l2_value)
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_m, mutual_inductance)
                self._assign_api_obj_param_if_present(br.emt_model, ParamPowerFlowRefferenceType.xfmr_gm, g_core)
                return
            else:
                return

        if ParamPowerFlowRefferenceType.Rnn not in api_obj_mapping:
            return
        else:
            pass

        # -----------------------------
        # 3. Resolve the physical phase layout from the line connection.
        # This selects the reduced subspace that exists in the physical line,
        # which is the basis for placing values into the global 4x4 NABC map.
        # -----------------------------
        ph_mask: list[bool] = list([
            bool(br.ys.phN),
            bool(br.ys.phA),
            bool(br.ys.phB),
            bool(br.ys.phC),
        ])
        idx_global: list[int] = list(i for i, is_active in enumerate(ph_mask) if is_active)
        n_active: int = len(idx_global)

        # -----------------------------
        # 4. Convert the physical line matrices into the EMT per-unit form.
        # The EMT template is parameterized in per-unit R, L^-1 and C values,
        # so this stage preserves the existing numerical pipeline exactly.
        # -----------------------------
        fbase: float = self.grid.fBase
        w0: float = 2.0 * np.pi * fbase
        v_base: float = br.bus_from.Vnom * 1e3
        s_base_mva: float = self.grid.Sbase
        s_base_va: float = s_base_mva * 1e6
        z_base: float = (v_base * v_base) / s_base_va
        y_base: float = 1.0 / z_base

        z_phys: np.ndarray = br.template.z_nabc * br.length
        y_phys: np.ndarray = br.template.y_nabc * br.length

        z_pu: np.ndarray = z_phys / z_base
        y_pu: np.ndarray = y_phys / y_base

        r_full: np.ndarray = np.real(z_pu)
        x_full: np.ndarray = np.imag(z_pu)
        l_full: np.ndarray = x_full / (w0 + 1e-20)
        bsh_full: np.ndarray = np.imag(y_pu)
        c_full: np.ndarray = (bsh_full / (w0 + 1e-20)) / 2.0

        # -----------------------------
        # 5. Validate the reduced matrices before mapping them.
        # These checks keep bad topology or singular data from silently
        # corrupting the full API mapping used by the EMT assembly.
        # -----------------------------
        expected_shape: tuple[int, int] = (n_active, n_active)

        if r_full.shape != expected_shape:
            raise ValueError(
            f"Line '{br.name}' must have a {n_active}x{n_active} Z matrix based on active phases. "
            f"Got {r_full.shape}."
        )
        if l_full.shape != expected_shape or c_full.shape != expected_shape:
            raise ValueError(
                f"Line '{br.name}' has inconsistent matrix shapes: "
                f"R={r_full.shape}, L={l_full.shape}, C={c_full.shape}."
            )

        try:
            l_inv_full: np.ndarray = np.linalg.inv(l_full)
        except np.linalg.LinAlgError as exc:
            raise ValueError(
                f"Inductance matrix L for line '{br.name}' is singular and cannot be inverted."
            ) from exc

        # -----------------------------
        # 6. Define the fixed global NABC mapping contract.
        # Both the EMT initializer and the EMT template rely on the same enum
        # layout so that active reduced matrices land in deterministic slots.
        # -----------------------------
        r_enums: list[list[ParamPowerFlowRefferenceType]] = list([
            list([
                ParamPowerFlowRefferenceType.Rnn,
                ParamPowerFlowRefferenceType.Rna,
                ParamPowerFlowRefferenceType.Rnb,
                ParamPowerFlowRefferenceType.Rnc,
            ]),
            list([
                ParamPowerFlowRefferenceType.Ran,
                ParamPowerFlowRefferenceType.Raa,
                ParamPowerFlowRefferenceType.Rab,
                ParamPowerFlowRefferenceType.Rac,
            ]),
            list([
                ParamPowerFlowRefferenceType.Rbn,
                ParamPowerFlowRefferenceType.Rba,
                ParamPowerFlowRefferenceType.Rbb,
                ParamPowerFlowRefferenceType.Rbc,
            ]),
            list([
                ParamPowerFlowRefferenceType.Rcn,
                ParamPowerFlowRefferenceType.Rca,
                ParamPowerFlowRefferenceType.Rcb,
                ParamPowerFlowRefferenceType.Rcc,
            ]),
        ])
        linv_enums: list[list[ParamPowerFlowRefferenceType]] = list([
            list([
                ParamPowerFlowRefferenceType.Linv_nn,
                ParamPowerFlowRefferenceType.Linv_na,
                ParamPowerFlowRefferenceType.Linv_nb,
                ParamPowerFlowRefferenceType.Linv_nc,
            ]),
            list([
                ParamPowerFlowRefferenceType.Linv_an,
                ParamPowerFlowRefferenceType.Linv_aa,
                ParamPowerFlowRefferenceType.Linv_ab,
                ParamPowerFlowRefferenceType.Linv_ac,
            ]),
            list([
                ParamPowerFlowRefferenceType.Linv_bn,
                ParamPowerFlowRefferenceType.Linv_ba,
                ParamPowerFlowRefferenceType.Linv_bb,
                ParamPowerFlowRefferenceType.Linv_bc,
            ]),
            list([
                ParamPowerFlowRefferenceType.Linv_cn,
                ParamPowerFlowRefferenceType.Linv_ca,
                ParamPowerFlowRefferenceType.Linv_cb,
                ParamPowerFlowRefferenceType.Linv_cc,
            ]),
        ])
        c_enums: list[list[ParamPowerFlowRefferenceType]] = list([
            list([
                ParamPowerFlowRefferenceType.Cnn,
                ParamPowerFlowRefferenceType.Cna,
                ParamPowerFlowRefferenceType.Cnb,
                ParamPowerFlowRefferenceType.Cnc,
            ]),
            list([
                ParamPowerFlowRefferenceType.Can,
                ParamPowerFlowRefferenceType.Caa,
                ParamPowerFlowRefferenceType.Cab,
                ParamPowerFlowRefferenceType.Cac,
            ]),
            list([
                ParamPowerFlowRefferenceType.Cbn,
                ParamPowerFlowRefferenceType.Cba,
                ParamPowerFlowRefferenceType.Cbb,
                ParamPowerFlowRefferenceType.Cbc,
            ]),
            list([
                ParamPowerFlowRefferenceType.Ccn,
                ParamPowerFlowRefferenceType.Cca,
                ParamPowerFlowRefferenceType.Ccb,
                ParamPowerFlowRefferenceType.Ccc,
            ]),
        ])
        # -----------------------------
        # 6. Reset the full 4x4 map and then write the active reduced values.
        # Zeroing all entries preserves the previous semantics for inactive
        # rows and columns, which the template later reduces with line.ys.
        # -----------------------------
        for i_glob in range(4):
            for j_glob in range(4):
                self._assign_api_obj_param_if_present(br.emt_model, r_enums[i_glob][j_glob], 0.0)
                self._assign_api_obj_param_if_present(br.emt_model, linv_enums[i_glob][j_glob], 0.0)
                self._assign_api_obj_param_if_present(br.emt_model, c_enums[i_glob][j_glob], 0.0)

        for i_red, i_glob in enumerate(idx_global):
            for j_red, j_glob in enumerate(idx_global):
                self._assign_api_obj_param_if_present(br.emt_model, r_enums[i_glob][j_glob],
                                                      float(r_full[i_red, j_red]))
                self._assign_api_obj_param_if_present(
                    br.emt_model,
                    linv_enums[i_glob][j_glob],
                    float(l_inv_full[i_red, j_red])
                )
                self._assign_api_obj_param_if_present(br.emt_model, c_enums[i_glob][j_glob],
                                                      float(c_full[i_red, j_red]))

    def _assign_api_obj_mapping_load(self, load) -> None:
        """
        Assign PF-derived static load parameters into the EMT model API mapping.
        :param load: Load device.
        :return: None.
        """
        fbase: float = self.grid.fBase
        sbase: float = self.grid.Sbase
        w0: float = 2.0 * np.pi * fbase

        p_values: List[float] = list([
            load.Pa / sbase,
            load.Pb / sbase,
            load.Pc / sbase,
        ])
        q_values: List[float] = list([
            load.Qa / sbase,
            load.Qb / sbase,
            load.Qc / sbase,
        ])
        p_keys: List[ParamPowerFlowRefferenceType] = list([
            ParamPowerFlowRefferenceType.Pl0_A,
            ParamPowerFlowRefferenceType.Pl0_B,
            ParamPowerFlowRefferenceType.Pl0_C,
        ])
        q_keys: List[ParamPowerFlowRefferenceType] = list([
            ParamPowerFlowRefferenceType.Ql0_A,
            ParamPowerFlowRefferenceType.Ql0_B,
            ParamPowerFlowRefferenceType.Ql0_C,
        ])

        if not load.bus.is_dc:
            for idx in range(3):
                self._assign_api_obj_param_if_present(load.emt_model, p_keys[idx], p_values[idx])
                self._assign_api_obj_param_if_present(load.emt_model, q_keys[idx], q_values[idx])

            self._assign_api_obj_param_if_present(load.emt_model, ParamPowerFlowRefferenceType.omega_base, w0)
        else:
            dc_p_value: float = load.P / sbase
            dc_g_value: float = load.G / sbase

            if dc_g_value == 0.0:
                dc_p_value = 0.0
                dc_g_value = load.P / sbase
            else:
                pass

            self._assign_api_obj_param_if_present(load.emt_model, ParamPowerFlowRefferenceType.Pl0, dc_p_value)
            self._assign_api_obj_param_if_present(load.emt_model, ParamPowerFlowRefferenceType.g, dc_g_value)

    def _assign_api_obj_mapping_generator(self, gen) -> None:
        """
        Assign PF-derived static generator parameters into the EMT model API mapping.

        :param gen: Generator device.
        :return: None.
        """
        fbase: float = self.grid.fBase
        w0: float = 2.0 * np.pi * fbase

        self._assign_api_obj_param_if_present(gen.emt_model, ParamPowerFlowRefferenceType.omega_base, w0)
        self._assign_api_obj_param_if_present(gen.emt_model, ParamPowerFlowRefferenceType.R1, gen.R1)
        self._assign_api_obj_param_if_present(gen.emt_model, ParamPowerFlowRefferenceType.X1, gen.X1)
        self._assign_api_obj_param_if_present(gen.emt_model, ParamPowerFlowRefferenceType.X0, gen.X0)


