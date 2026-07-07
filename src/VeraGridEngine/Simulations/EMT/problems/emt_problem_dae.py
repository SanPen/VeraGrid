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
import copy

from VeraGridEngine.Devices import MultiCircuit
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Simulations.driver_template import DummySignal
from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Expr, piecewise, Const, hard_sat, heaviside
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import (
    VarPowerFlowReferenceType,
    ParamPowerFlowReferenceType,
    DeviceType,
    DynamicEventTransitionType,
    EmtInitializationMethod,
    EmtInitializationStatus,
    EmtLineTypes,
)
from VeraGridEngine.basic_structures import Logger, CxVec
from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.Templates.Emt.bergeron_line_emt_template import BergeronHistoryRuntime
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_runtime import JMartiHistoryRuntime
from VeraGridEngine.Simulations.PowerFlow3ph.power_flow_results_3ph import PowerFlowResults3Ph
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import PowerFlowResults
from VeraGridEngine.Simulations.EMT.initialization_emt import EmtInitializationReport, run_emt_native_initialization, _compute_missing_dx0
from VeraGridEngine.Utils.Symbolic.explicit_initialization_symbolic import init_explicit_common, build_symbolic_vector_single_equation_compiler
from VeraGridEngine.Utils.Symbolic.compiled_functions import get_compiled_functions_cache_stats
from VeraGridEngine.Utils.Symbolic.bus_emt_template import get_bus_emt_algebraic_vars
from VeraGridEngine.Utils.procedural_logic import build_boundary_updater_from_block
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
from VeraGridEngine.Devices.Dynamic.static_parameter_mapping import (
    abc_to_nabc,
    assign_static_api_object_mapping_for_device,
    get_load_power_phase_values_pu_abc,
    get_shunt_phase_values_pu_abc,
)
# from VeraGridEngine.Devices.Dynamic.static_parameter_mapping_rms import (
#     abc_to_nabc,
#     assign_static_api_object_mapping_for_device,
#     get_load_power_phase_values_pu_abc,
#     get_shunt_phase_values_pu_abc,
# )


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


def _freeze_runtime_expr_at_time(expr: Any, time_var: Var, sample_time: float) -> Any:
    """
    Freeze one runtime expression at an explicit time value.

    :param expr: Runtime expression to freeze.
    :param time_var: Global symbolic time variable.
    :param sample_time: Time used to evaluate the expression boundary.
    :return: Time-frozen symbolic expression.
    """
    if isinstance(expr, (Expr, Var, Const)):
        return expr.subs(dict({time_var: Const(float(sample_time))})).simplify()
    else:
        return expr


def _build_ramp_runtime_expr(
    time_var: Var,
    start_time: float,
    end_time: float,
    before_expr: Any,
    final_value: float,
) -> Any:
    """
    Build one linear ramp transition on top of an existing runtime expression.

    The expression keeps ``before_expr`` before ``start_time``, then transitions
    linearly toward ``final_value`` until ``end_time``, and finally holds the
    final value afterwards.

    :param time_var: Global symbolic time variable.
    :param start_time: Ramp start time.
    :param end_time: Ramp end time.
    :param before_expr: Expression active before the ramp starts.
    :param final_value: Final runtime value after the ramp ends.
    :return: Combined symbolic expression.
    """
    start_expr: Any = _freeze_runtime_expr_at_time(before_expr, time_var, start_time)
    duration_expr: Const = Const(float(end_time - start_time))
    time_offset_expr: Any = time_var - Const(float(start_time))
    progress_expr: Any = hard_sat(time_offset_expr / duration_expr, Const(0.0), Const(1.0))
    ramp_expr: Any = start_expr + progress_expr * (Const(float(final_value)) - start_expr)
    started_expr: Any = heaviside(time_var - Const(float(start_time)))
    ended_expr: Any = heaviside(time_var - Const(float(end_time)))
    return (Const(1.0) - started_expr) * before_expr + started_expr * (
        (Const(1.0) - ended_expr) * ramp_expr + ended_expr * Const(float(final_value))
    )


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

def find_name_in_block(name: str, block: Block):
    for var in block.algebraic_vars + block.state_vars + list(block.event_dict.keys()) + block.diff_vars:
        if name == var.name:
            return var

    for mdl in block.children:
        res = find_name_in_block(name, mdl)
        if res is not None:
            return res


class EmtTopologyError(Exception):
    """
    Exception raised when EMT topology validation fails.
    This includes orphaned in_vars/out_vars and floating bus phases.
    """

    def __init__(self, message: str) -> None:
        """
        :param message: Descriptive error message indicating the topology issue.
        """
        self.message = message
        super().__init__(self.message)


class EmtInterfaceValidationError(ValueError):
    """
    Exception raised when one EMT interface is incompatible with the bus shell.

    The dynamic editor may expose a maximum editable interface that is broader
    than the currently configured static network. This exception reports those
    mismatches explicitly before EMT assembly can silently skip substitutions.
    """

    def __init__(self, message: str):
        """
        Build one explicit EMT interface-validation error.

        :param message: Descriptive interface mismatch report.
        :return: None.
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
    machine_eps: float = float(np.finfo(np.float64).eps)
    time_tol: float = 10.0 * machine_eps * max(1.0, abs(event_time))
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


def _continuous_event_spec_time_sort_key(event_spec: Dict[str, float | str | None]) -> float:
    """
    Return the sorting key used for one continuous-event specification.

    :param event_spec: Continuous event specification dictionary.
    :return: Event start time.
    """
    return float(event_spec["time"])

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


def _is_history_runtime_line_block_name(block_name: Any) -> Tuple[bool, bool]:
    """
    Return whether one EMT line block uses a retained-history runtime companion.

    :param block_name: EMT block name.
    :return: Tuple ``(is_bergeron, is_jmarti)``.
    """
    is_bergeron: bool = block_name == EmtLineTypes.Bergeron or block_name == EmtLineTypes.Bergeron.value
    is_jmarti: bool = block_name == EmtLineTypes.J_Marti or block_name == EmtLineTypes.J_Marti.value
    return is_bergeron, is_jmarti


def _has_internal_grounding_link(block: Block) -> bool:
    """
    Return whether one EMT block hierarchy contains one internal grounding link.

    :param block: Candidate EMT block.
    :return: Boolean state.
    """
    diagram_node: Any
    nested_block: Block

    for diagram_node in block.diagram.node_data.values():
        if diagram_node.tpe in {"GROUNDING_LINK_EMT", "GROUND_EMT"}:
            return True
        else:
            pass

    for nested_block in block.children:
        if nested_block.name.endswith("_grounding_link"):
            return True
        elif _has_internal_grounding_link(nested_block):
            return True
        else:
            pass

    return False


def _get_grid_runtime_events(grid: MultiCircuit) -> List[Any]:
    """
    Return the list of scheduled runtime events available in the grid.

    :param grid: MultiCircuit instance.
    :return: List of scheduled runtime events.
    """

    return grid.emt_events

def _get_bus_v_list(
        bus_block: Block,
        ph_v_keys: List[VarPowerFlowReferenceType]
) -> List[Any]:
    """
    Return the ordered list of bus phase voltages, using None for missing phases.

    :param bus_block: Bus symbolic block.
    :param ph_v_keys: Ordered list of phase voltage keys.
    :return: Ordered list of bus phase voltage expressions or None.
    """
    out: List[Any] = list()

    for key in ph_v_keys:
        vk: Optional[Any] = _get_external_mapping_var_if_present(mdl=bus_block, key=key)

        if vk is None:
            out.append(None)
        else:
            out.append(vk)

    return out

def _get_external_mapping(mdl: Block) -> Optional[Dict[Any, Var]]:
    """
    Return the flattened external mapping exposed by one block hierarchy.

    Wrapper EMT models may keep the actual PF-to-EMT variable bindings inside
    nested child blocks. The build stage therefore needs to inspect the whole
    hierarchy and merge the first occurrence of each key so later lookup sites
    can recover child initialization references from the wrapper root.

    :param mdl: Root block to inspect.
    :return: Flattened external mapping, or ``None`` when no mapping exists.
    """
    external_mapping: Dict[Any, Var] = _collect_external_mapping_from_block(mdl)

    # An empty merged mapping means the hierarchy does not expose PF bindings.
    if len(external_mapping) == 0:
        return None
    else:
        return external_mapping


def _collect_block_hierarchy(mdl: Block) -> List[Block]:
    """
    Collect every block reachable from one root block.

    The EMT editor may persist one wrapper root around the actual device block.
    Rebuilding wrapper-owned metadata therefore starts by traversing the full
    hierarchy exactly once while avoiding revisiting the same block object.

    :param mdl: Root block to inspect.
    :return: Ordered list with the reachable block objects.
    """
    blocks: List[Block] = list()
    stack: List[Block] = list([mdl])
    visited: Set[int] = set()

    # The explicit stack keeps the traversal iterative and avoids recursion
    # depth concerns when the GUI creates nested wrapper structures.
    while len(stack) > 0:
        block: Block = stack.pop()
        block_id: int = id(block)

        # Every block is processed only once so merged metadata stays stable.
        if block_id not in visited:
            visited.add(block_id)
            blocks.append(block)

            # Child blocks are pushed so the caller can inspect nested metadata
            # such as PF references and explicit-init registrations.
            child: Block
            for child in block.children:
                stack.append(child)
        else:
            pass

    return blocks


def _collect_external_mapping_from_block(mdl: Block) -> Dict[Any, Var]:
    """
    Collect the external mapping from one block hierarchy.

    Wrapper models may keep the exposed PF reference variables in nested child
    blocks. This helper merges the hierarchy into one root-level mapping while
    preserving the first occurrence of each key, which matches the existing
    API-object mapping recovery strategy used by the EMT builder.

    :param mdl: Root block to inspect.
    :return: Flattened external mapping.
    """
    mapping: Dict[Any, Var] = dict()
    blocks: List[Block] = _collect_block_hierarchy(mdl)
    block: Block

    # The root block keeps precedence, while child-only keys are recovered so
    # PF-derived initialization metadata survives wrapper reconstruction.
    for block in blocks:
        local_mapping: Optional[Dict[Any, Var]] = block.external_mapping

        if local_mapping is None:
            pass
        else:
            key: Any
            value: Var
            for key, value in local_mapping.items():
                if key not in mapping:
                    mapping[key] = value
                else:
                    pass

    mapping = _sanitize_external_mapping_for_explicit_dc_terminals(mapping)

    return mapping


def _sanitize_external_mapping_for_explicit_dc_terminals(mapping: Dict[Any, Var]) -> Dict[Any, Var]:
    """
    Remove ambiguous shared DC aliases when explicit terminal mappings exist.

    GUI-loaded EMT wrappers can preserve both the legacy shared DC aliases
    (``Vdc`` / ``Idc``) and the explicit terminal contract
    (``Vf_dc`` / ``Vt_dc`` and ``If_dc`` / ``It_dc``). The structural EMT
    assembly for two-sided DC devices is defined by the explicit side-specific
    variables. Keeping the shared aliases at the merged root can reintroduce
    one-sided shortcuts that collapse the assembled sparse system and make the
    Jacobian exactly singular.

    :param mapping: Flattened external mapping collected from one block hierarchy.
    :return: Sanitized mapping that preserves only the explicit two-sided DC contract.
    """
    sanitized_mapping: Dict[Any, Var] = dict()
    has_vf: bool = VarPowerFlowReferenceType.Vf_dc in mapping
    has_vt: bool = VarPowerFlowReferenceType.Vt_dc in mapping
    has_if: bool = VarPowerFlowReferenceType.If_dc in mapping
    has_it: bool = VarPowerFlowReferenceType.It_dc in mapping
    key: Any
    value: Var

    for key, value in mapping.items():
        if key == VarPowerFlowReferenceType.Vdc:
            if has_vf and has_vt:
                pass
            else:
                sanitized_mapping[key] = value
        elif key == VarPowerFlowReferenceType.Idc:
            if has_if and has_it:
                pass
            else:
                sanitized_mapping[key] = value
        else:
            sanitized_mapping[key] = value

    return sanitized_mapping


def _collect_api_obj_mapping_from_block(mdl: Block) -> Dict[ParamPowerFlowReferenceType, Any]:
    """
    Collect the API-object mapping from one block hierarchy.

    Wrapper models may keep the parameter mapping in nested child blocks. This
    helper traverses the hierarchy and preserves the first mapping occurrence of
    each key so PF-derived parameter assignment still sees the expected metadata.

    :param mdl: Root block to inspect.
    :return: Flattened API-object mapping.
    """
    mapping: Dict[ParamPowerFlowReferenceType, Any] = dict()
    blocks: List[Block] = _collect_block_hierarchy(mdl)
    block: Block

    # The same hierarchy walk used for external mappings is reused here so the
    # wrapper-recovery policy stays identical for all PF initialization data.
    for block in blocks:
        local_mapping: Dict[ParamPowerFlowReferenceType, Any] = block.api_obj_mapping
        key: ParamPowerFlowReferenceType
        value: Any
        for key, value in local_mapping.items():
            if key not in mapping:
                mapping[key] = value
            else:
                pass

    return mapping


def _realign_static_parameter_mapping_with_unified_block(
        sys_block: Block,
        static_parameter_values_mapping: Dict[Var, Const],
) -> None:
    """
    Rebind static parameter values to the vars present in the unified root block.

    EMT compilation uses the final flattened ``sys_block`` equations. Static
    parameters are collected earlier while device models may still live in wrapper
    hierarchies. After unification and deduplication, the final equation graph can
    reference var instances that share the same UID but are not the same Python
    object as the ones used as keys in the pre-collected static mapping. This
    helper rebuilds the dictionary on top of the vars that actually belong to the
    unified block so compiler-name generation stays aligned with the final system.

    :param sys_block: Unified EMT root block.
    :param static_parameter_values_mapping: Static parameter mapping to realign.
    :return: None.
    """
    uid_to_parameter_var: Dict[int, Var] = dict()
    parameter_var: Var

    # Some custom EMT templates keep parameter variables only in nested blocks.
    # After block unification the final compiled equations may still reference
    # those vars by UID even when the root ``sys_block.parameters`` dictionary is
    # not the original object that first held them. Walk the full hierarchy to
    # realign every constant parameter against the vars that survive in the
    # unified graph.
    all_blocks: List[Block] = sys_block.get_all_blocks()
    block_obj: Block
    parameter_value: Const

    for block_obj in all_blocks:
        for parameter_var, parameter_value in block_obj.parameters.items():
            if parameter_var not in static_parameter_values_mapping:
                static_parameter_values_mapping[parameter_var] = parameter_value
            else:
                pass
            uid_to_parameter_var[parameter_var.uid] = parameter_var

    if len(uid_to_parameter_var) == 0:
        return
    else:
        pass

    updated_mapping: Dict[Var, Const] = dict()
    original_parameter_var: Var
    parameter_value: Const

    for original_parameter_var, parameter_value in static_parameter_values_mapping.items():
        unified_parameter_var: Var | None = uid_to_parameter_var.get(original_parameter_var.uid, None)

        if unified_parameter_var is None:
            updated_mapping[original_parameter_var] = parameter_value
        else:
            updated_mapping[unified_parameter_var] = parameter_value

    static_parameter_values_mapping.clear()
    static_parameter_values_mapping.update(updated_mapping)

def _build_device_idtag_lookup(devices: List[Any]) -> Dict[str, int]:
    """
    Build one idtag-to-index lookup table.

    This lookup is acceptable because it is used only for indexing and not as
    the primary numerical storage container.

    :param devices: Device list.
    :return: Lookup dictionary.
    """
    lookup: Dict[str, int] = dict()
    device_index: int = 0

    while device_index < len(devices):
        lookup[devices[device_index].idtag] = device_index
        device_index += 1

    return lookup


def _get_source_seed_weight(injection: Any) -> float:
    """
    Return the weight used to distribute bus residual among source-like injections.

    ``Snom`` is used whenever it is positive. Otherwise, a unit weight is used.

    :param injection: Injection device.
    :return: Residual-allocation weight.
    """
    snom_value: float = float(injection.Snom)

    if snom_value > 0.0:
        return snom_value
    else:
        return 1.0


def _get_internal_runtime_default(mdl: Block, var_name: str, default_value: float) -> float:
    """
    Return one runtime-parameter default by internal variable name.

    :param mdl: Root model block.
    :param var_name: Runtime-parameter variable name.
    :param default_value: Fallback value if the variable is not found.
    :return: Runtime-parameter default.
    """
    internal_var: Optional[Var]
    owner_block: Optional[Block]
    expression: Any

    internal_var, owner_block = _find_internal_runtime_var_owner(mdl, var_name)

    if internal_var is None or owner_block is None:
        return float(default_value)
    else:
        pass

    expression = owner_block.event_dict.get(internal_var, None)
    if expression is None:
        return float(default_value)
    else:
        pass

    if isinstance(expression, Const):
        return float(expression.value)
    else:
        return float(default_value)


def _get_internal_mode_default(mdl: Block, var_name: str, default_value: float) -> float:
    """
    Return one retained runtime-mode default by internal variable name.

    :param mdl: Root model block.
    :param var_name: Retained mode variable name.
    :param default_value: Fallback value if the variable is not found.
    :return: Runtime-mode default.
    """
    internal_var: Optional[Var]
    owner_block: Optional[Block]
    expression: Any

    internal_var, owner_block = _find_mode_var_owner(mdl, var_name)

    if internal_var is None or owner_block is None:
        return float(default_value)
    else:
        pass

    expression = owner_block.mode_dict.get(internal_var, None)
    if expression is None:
        return float(default_value)
    else:
        pass

    if isinstance(expression, Const):
        return float(expression.value)
    else:
        return float(default_value)


def _resolve_converter_control_reference_values(control1_code: float,
                                                control2_code: float,
                                                control1_val: float,
                                                control2_val: float,
                                                p0_value: float) -> Tuple[float, float, float]:
    """
    Resolve converter control references numerically from configured control modes.

    :param control1_code: Numeric code of control 1.
    :param control2_code: Numeric code of control 2.
    :param control1_val: Numeric value of control 1.
    :param control2_val: Numeric value of control 2.
    :param p0_value: Scheduled active-power operating point.
    :return: Tuple ``(P_ref, Q_ref, Vdc_ref)``.
    """
    vm_dc_code: float = 1.0
    qac_code: float = 4.0
    pdc_code: float = 5.0
    pac_code: float = 6.0
    p_ref_value: float
    q_ref_value: float
    vdc_ref_value: float

    if abs(control1_code - vm_dc_code) < 0.5:
        vdc_ref_value = control1_val
    else:
        if abs(control2_code - vm_dc_code) < 0.5:
            vdc_ref_value = control2_val
        else:
            vdc_ref_value = 1.0

    if abs(control1_code - qac_code) < 0.5:
        q_ref_value = control1_val
    else:
        if abs(control2_code - qac_code) < 0.5:
            q_ref_value = control2_val
        else:
            q_ref_value = 0.0

    if abs(control1_code - pdc_code) < 0.5 or abs(control1_code - pac_code) < 0.5:
        p_ref_value = control1_val
    else:
        if abs(control2_code - pdc_code) < 0.5 or abs(control2_code - pac_code) < 0.5:
            p_ref_value = control2_val
        else:
            p_ref_value = p0_value

    return float(p_ref_value), float(q_ref_value), float(vdc_ref_value)


def _get_external_mapping_var_if_present(
        mdl: Block,
        key: VarPowerFlowReferenceType,
) -> Optional[Any]:
    """
    Return one mapped external variable if the model exposes the key.

    This helper intentionally does not call ``mdl.E(key)`` because ``Block.E``
    indexes ``external_mapping`` directly and raises ``KeyError`` when the key
    is absent. User models are allowed to expose only a subset of optional
    PowerFlow initialization keys.

    :param mdl: Symbolic device block.
    :param key: External mapping reference key.
    :return: Mapped variable or expression, or ``None``.
    """
    external_mapping: Optional[Dict[Any, Var]] = _get_external_mapping(mdl)

    if external_mapping is None:
        return None
    else:
        mapped_var: Optional[Any] = external_mapping.get(key, None)
        return mapped_var


def _get_array_entry_if_in_range(array_obj: Any, index: int) -> Optional[Any]:
    """
    Return one array entry only when the index is valid.

    Power-flow result containers may exist while some per-phase arrays are empty,
    for example after one failed or unsupported PF attempt in the GUI. EMT should
    then skip the corresponding seed instead of raising ``IndexError`` during the
    initialization pass.

    :param array_obj: Candidate array-like object.
    :param index: Requested zero-based index.
    :return: Selected entry or ``None``.
    """
    if array_obj is None:
        return None
    else:
        pass

    try:
        array_length: int = len(array_obj)
    except TypeError:
        return None

    if 0 <= int(index) < array_length:
        return array_obj[index]
    else:
        return None


def _get_balanced_vsc_dc_power(pf_results: PowerFlowResults, vsc_index: int) -> complex:
    """
    Return the balanced VSC DC-side active power in system-base units.

    :param pf_results: Balanced power-flow results.
    :param vsc_index: VSC index.
    :return: DC-side complex power.
    """
    pfp_value: Optional[Any] = _get_array_entry_if_in_range(pf_results.Pfp_vsc, vsc_index)
    pfn_value: Optional[Any] = _get_array_entry_if_in_range(pf_results.Pfn_vsc, vsc_index)
    pfp_float: float = 0.0 if pfp_value is None else float(pfp_value)
    pfn_float: float = 0.0 if pfn_value is None else float(pfn_value)
    return complex(pfp_float + pfn_float, 0.0)


def _get_balanced_vsc_ac_power(pf_results: PowerFlowResults, vsc_index: int) -> complex:
    """
    Return the balanced VSC AC-side complex power in system-base units.

    Some PF result containers still leave ``St_vsc`` at zero for valid AC/DC
    operating points. In that case, use the available DC-side transfer as the
    active-power fallback so EMT initialization preserves the scheduled power.

    :param pf_results: Balanced power-flow results.
    :param vsc_index: VSC index.
    :return: AC-side complex power.
    """
    st_value: Optional[Any] = _get_array_entry_if_in_range(pf_results.St_vsc, vsc_index)
    st_complex: complex

    if st_value is None:
        return _get_balanced_vsc_dc_power(pf_results, vsc_index)
    else:
        st_complex = complex(st_value)

    if abs(st_complex) > 1.0e-12:
        return st_complex
    else:
        return _get_balanced_vsc_dc_power(pf_results, vsc_index)


def _find_mode_var_by_name(block: Block, var_name: str) -> Optional[Var]:
    """
    Return one retained mode variable from a block hierarchy by name.

    :param block: Root block to inspect.
    :param var_name: Retained mode variable name.
    :return: Matching retained mode variable or ``None``.
    """
    mode_var: Var
    child_block: Block
    nested_mode_var: Optional[Var]

    for mode_var in block.mode_dict.keys():
        if mode_var.name == var_name:
            return mode_var
        else:
            pass

    for child_block in block.children:
        nested_mode_var = _find_mode_var_by_name(child_block, var_name)
        if nested_mode_var is not None:
            return nested_mode_var
        else:
            pass

    return None


def _find_internal_var_for_init(block: Block, var_name: str) -> Optional[Var]:
    """
    Return one internal state/algebraic/differential variable by name.

    This helper intentionally ignores ``in_vars`` and ``out_vars`` aliases so
    initialization values are written against the actual solver-owned variables.

    :param block: Root block to inspect.
    :param var_name: Variable name.
    :return: Matching solver-owned variable or ``None``.
    """
    variable: Var
    child_block: Block
    nested_variable: Optional[Var]

    for variable_list in [block.state_vars, block.algebraic_vars, block.diff_vars]:
        for variable in variable_list:
            if variable.name == var_name:
                return variable
            else:
                pass

    for child_block in block.children:
        nested_variable = _find_internal_var_for_init(child_block, var_name)
        if nested_variable is not None:
            return nested_variable
        else:
            pass

    return None


def _find_internal_var_by_prefix(block: Block, name_prefix: str) -> Optional[Var]:
    """
    Return one internal state/algebraic/differential variable by name prefix.

    This helper is used for templates whose cloned working blocks may not keep an
    easily reconstructable root-block name, while their internal variable prefixes
    remain stable.

    :param block: Root block to inspect.
    :param name_prefix: Variable-name prefix.
    :return: Matching solver-owned variable or ``None``.
    """
    variable: Var
    child_block: Block
    nested_variable: Optional[Var]

    for variable_list in [block.state_vars, block.algebraic_vars, block.diff_vars]:
        for variable in variable_list:
            if variable.name.startswith(name_prefix):
                return variable
            else:
                pass

    for child_block in block.children:
        nested_variable = _find_internal_var_by_prefix(child_block, name_prefix)
        if nested_variable is not None:
            return nested_variable
        else:
            pass

    return None

def _find_mode_var_owner(block: Block, var_name: str) -> Tuple[Optional[Var], Optional[Block]]:
    """
    Return one retained mode variable together with the block that owns it.

    :param block: Root block to inspect.
    :param var_name: Retained mode variable name.
    :return: Tuple ``(variable, owner_block)`` or ``(None, None)``.
    """
    mode_var: Var
    child_block: Block
    nested_var: Optional[Var]
    nested_owner: Optional[Block]

    for mode_var in block.mode_dict.keys():
        if mode_var.name == var_name:
            return mode_var, block
        else:
            pass

    for child_block in block.children:
        nested_var, nested_owner = _find_mode_var_owner(child_block, var_name)
        if nested_var is not None and nested_owner is not None:
            return nested_var, nested_owner
        else:
            pass

    return None, None


def _find_internal_runtime_var_owner(block: Block, var_name: str) -> Tuple[Optional[Var], Optional[Block]]:
    """
    Return one runtime parameter variable together with the block that owns it.

    :param block: Root block to inspect.
    :param var_name: Runtime parameter variable name.
    :return: Tuple ``(variable, owner_block)`` or ``(None, None)``.
    """
    variable: Var
    child_block: Block
    nested_var: Optional[Var]
    nested_owner: Optional[Block]

    for variable in block.event_dict.keys():
        if variable.name == var_name:
            return variable, block
        else:
            pass

    for child_block in block.children:
        nested_var, nested_owner = _find_internal_runtime_var_owner(child_block, var_name)
        if nested_var is not None and nested_owner is not None:
            return nested_var, nested_owner
        else:
            pass

    return None, None


def _find_event_var_owner(block: Block, target_var: Var) -> Optional[Block]:
    """
    Return the block that owns one runtime event parameter variable.

    GUI-authored EMT models may keep the actual runtime parameter inside a child
    block while the wrapper root exposes only proxy metadata. Runtime seeding
    therefore has to locate the block that owns the parameter before updating
    the corresponding ``event_dict`` entry.

    :param block: Root block to inspect.
    :param target_var: Runtime parameter variable to locate.
    :return: Owner block or ``None`` when the variable is not present.
    """
    blocks: List[Block] = _collect_block_hierarchy(block)
    block_item: Block

    # The hierarchy walk is explicit so wrapper roots and leaf models follow the
    # same ownership lookup path during PF-derived runtime seeding.
    for block_item in blocks:
        if target_var in block_item.event_dict:
            return block_item
        else:
            pass

    return None


def _get_expected_pi_line_terminal_refs(ph_mask: List[bool]) -> List[VarPowerFlowReferenceType]:
    """
    Build the ordered terminal-voltage references for the active pi-line phases.

    :param ph_mask: Physical line phase mask in NABC order.
    :return: Ordered ``vf_*`` and ``vt_*`` references for the active phases only.
    """
    vf_refs: List[VarPowerFlowReferenceType] = list([
        VarPowerFlowReferenceType.vf_N,
        VarPowerFlowReferenceType.vf_A,
        VarPowerFlowReferenceType.vf_B,
        VarPowerFlowReferenceType.vf_C,
    ])
    vt_refs: List[VarPowerFlowReferenceType] = list([
        VarPowerFlowReferenceType.vt_N,
        VarPowerFlowReferenceType.vt_A,
        VarPowerFlowReferenceType.vt_B,
        VarPowerFlowReferenceType.vt_C,
    ])

    ordered_refs: List[VarPowerFlowReferenceType] = list()

    for idx, is_active in enumerate(ph_mask):
        if is_active:
            ordered_refs.append(vf_refs[idx])
        else:
            pass

    for idx, is_active in enumerate(ph_mask):
        if is_active:
            ordered_refs.append(vt_refs[idx])
        else:
            pass

    return ordered_refs


def validate_line_phase_layout(branch: Any, mdl: Block, logger: Logger):
    """
    Validate that a pi-line EMT block matches the physical branch phase layout.

    The EMT parameter mapper writes reduced branch matrices into the fixed NABC
    API map using ``branch.ys``. This helper therefore checks that the symbolic
    pi-line terminal layout still matches the physical branch phase mask before
    the device is flattened into the system model. A mismatch is a topology
    error, so the function reports it through the shared logger and preserves the
    original model instead of silently rebuilding it.

    :param branch: Grid branch device.
    :param mdl: EMT block associated with the branch.
    :param logger: Shared system logger used to report invalid topology states.
    """

    # The branch admittance mask is the physical topology source of truth, so it
    # defines which symbolic terminal voltage references must exist on the block.
    ph_mask: List[bool] = list([
        bool(branch.ys.phN),
        bool(branch.ys.phA),
        bool(branch.ys.phB),
        bool(branch.ys.phC),
    ])

    expected_refs: List[VarPowerFlowReferenceType] = _get_expected_pi_line_terminal_refs(ph_mask)

    # Only bus-terminal voltage references participate in the topology check.
    # Other inputs can remain on the block without affecting phase consistency.
    tracked_refs: Set[VarPowerFlowReferenceType] = {
        VarPowerFlowReferenceType.vf_N,
        VarPowerFlowReferenceType.vf_A,
        VarPowerFlowReferenceType.vf_B,
        VarPowerFlowReferenceType.vf_C,
        VarPowerFlowReferenceType.vt_N,
        VarPowerFlowReferenceType.vt_A,
        VarPowerFlowReferenceType.vt_B,
        VarPowerFlowReferenceType.vt_C,
    }

    current_refs: List[VarPowerFlowReferenceType] = list()

    for in_var in mdl.in_vars:
        if in_var.ref in tracked_refs:
            current_refs.append(in_var.ref)
        else:
            pass

    # A mismatch means the symbolic template and the EMT topology disagree about
    # how many branch terminals exist. That state is invalid because later model
    # assembly would bind non-existent phases, so it must be surfaced explicitly.
    if current_refs != expected_refs:
        logger.add_error(
            msg="Pi-line template has a different number of phases than the EMT model (topology mismatch).",
            device=branch.name,
            device_class=str(branch.device_type),
            value=str(current_refs),
            expected_value=str(expected_refs),
        )
    else:
        pass



class EmtInjectionSeedStore:
    """
    Fixed-size container storing PF-derived initialization seeds for EMT injections.

    The store is indexed by the position of each injection in the pre-built
    ``injection_devices`` list of ``EmtProblemDae._build_structure_and_collect``.
    This avoids dynamic dictionaries for numerical data and keeps memory layout
    explicit and preallocated.

    :param n_injections: Number of injection devices in the EMT problem.
    """

    __slots__ = (
        "_ac_power",
        "_dc_power",
        "_has_seed",
    )

    def __init__(self, n_injections: int) -> None:
        """
        Build the fixed-size seed store.

        :param n_injections: Number of injection devices.
        :return: None.
        """
        # The AC seed stores one complex power per NABC phase for each injection.
        self._ac_power: np.ndarray = np.zeros((n_injections, 4), dtype=np.complex128)

        # The DC seed stores one real active power per injection.
        self._dc_power: np.ndarray = np.zeros(n_injections, dtype=np.float64)

        # This mask tells whether an injection received an explicit seed.
        self._has_seed: np.ndarray = np.zeros(n_injections, dtype=bool)

    def set_ac_seed(self, injection_index: int, phase_power: np.ndarray) -> None:
        """
        Store one AC four-phase power seed.

        :param injection_index: Injection position in the fixed injection list.
        :param phase_power: Complex power vector in NABC order.
        :return: None.
        """
        self._ac_power[injection_index, :] = phase_power
        self._has_seed[injection_index] = True

    def set_dc_seed(self, injection_index: int, power_value: float) -> None:
        """
        Store one DC active-power seed.

        :param injection_index: Injection position in the fixed injection list.
        :param power_value: DC active power in per unit.
        :return: None.
        """
        self._dc_power[injection_index] = power_value
        self._has_seed[injection_index] = True

    def has_seed(self, injection_index: int) -> bool:
        """
        Return whether the given injection has a stored seed.

        :param injection_index: Injection position in the fixed injection list.
        :return: ``True`` if a seed exists, ``False`` otherwise.
        """
        return bool(self._has_seed[injection_index])

    def get_ac_seed(self, injection_index: int) -> np.ndarray:
        """
        Return the AC phase-power seed in NABC order.

        :param injection_index: Injection position in the fixed injection list.
        :return: Complex power vector in NABC order.
        """
        return self._ac_power[injection_index, :]

    def get_dc_seed(self, injection_index: int) -> float:
        """
        Return the DC active-power seed.

        :param injection_index: Injection position in the fixed injection list.
        :return: DC active power in per unit.
        """
        return float(self._dc_power[injection_index])


def _accumulate_kcl_current(
        i_kcl: Dict[int, List[Any]],
        bus_index: int,
        phase_index: int,
        current_expression: Any,
        sign: float,
) -> None:
    """
    Accumulate one symbolic current contribution into the bus KCL.

    The EMT nodal equations are KCL equations. This helper keeps the sign
    convention explicit:
    - ``sign = -1.0`` for branch currents leaving the bus,
    - ``sign = +1.0`` for injection currents entering the bus.

    :param i_kcl: Bus-phase KCL symbolic accumulator.
    :param bus_index: Bus index.
    :param phase_index: Phase index in NABC order.
    :param current_expression: Symbolic current contribution.
    :param sign: Contribution sign.
    :return: None.
    """
    if current_expression is None:
        pass
    else:
        i_kcl[bus_index][phase_index] = i_kcl[bus_index][phase_index] + sign * current_expression


def _zero_ac_power_vector() -> np.ndarray:
    """
    Return a zero complex power vector in NABC order.

    :return: Zero complex power vector.
    """
    return np.zeros(4, dtype=np.complex128)


def _phase_sequence_shift(phase_index: int) -> complex:
    """
    Return the phase shift used to reconstruct balanced phase phasors.

    Phase order is NABC.

    :param phase_index: Phase index in NABC order.
    :return: Complex unit phasor applied to the balanced bus phasor.
    """
    if phase_index == 0:
        return 0.0 + 0.0j
    else:
        if phase_index == 1:
            return 1.0 + 0.0j
        else:
            if phase_index == 2:
                return np.exp(-1j * 2.0 * np.pi / 3.0)
            else:
                return np.exp(+1j * 2.0 * np.pi / 3.0)

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
                 pf_results_3Ph: PowerFlowResults3Ph | None = None,
                 pf_results_3ph: PowerFlowResults3Ph | None = None,
                 pf_results: PowerFlowResults | None = None,
                 progress_signal: DummySignal | None = None,
                 progress_text: DummySignal | None = None) -> None:
        """
        Initializes the EMT Problem by parsing the grid and passing the
        resulting mathematical block to the BaseProblem constructor.
        :param grid:
        :param options:
        :param pf_results_3Ph:
        :param pf_results:
        """
        self.logger = Logger()
        self.grid = grid
        self.options = options
        if pf_results_3ph is None:
            self.power_flow_results_3ph = pf_results_3Ph
        else:
            self.power_flow_results_3ph = pf_results_3ph
        self.power_flow_results = pf_results

        self._vars_info: Dict[ALL_DEV_TYPES, List[Var]] = dict()
        self._vars_glob_name2uid: Dict[str, int] = dict()
        self._vars2device: Dict[int, ALL_DEV_TYPES] = dict()
        self._temp_init_guess: Dict[int, float] = dict()
        self._temp_post_init_guess: Dict[int, float] = dict()
        self._temp_diff_init_guess: Dict[int, float] = dict()
        self._temp_post_diff_init_guess: Dict[int, float] = dict()
        self.initialization_report: EmtInitializationReport | None = None
        self.build_report: Dict[str, float] = dict()

        self._scheduled_mode_events: Dict[int, List[Tuple[float, float, bool]]] = dict()
        self._mode_event_cursor: Dict[int, int] = dict()
        self._runtime_parameter_eqs0: List[Any] = list()
        self._event_parameter_device_idtags: Dict[int, str] = dict()
        self._event_parameter_name_lookup: Dict[Tuple[str, str], int] = dict()
        self._continuous_event_parameter_uids: Set[int] = set()
        self._discrete_event_parameter_uids: Set[int] = set()
        self._active_events_group: EmtEventsGroup | None = None

        static_parameter_values_mapping: Dict[Var, Const] = dict()

        # The explicit initialization stage must solve each device working model as
        # one unified symbolic block. Registering nested child blocks separately can
        # break coupled controller/plant operating-point seeds because sibling
        # sub-blocks are then initialized independently instead of sharing one
        # flattened dependency graph.
        self._device_models_with_init_eqs: List[Block] = list()
        self._device_models_with_init_eqs_seen: Set[int] = set()

        sys_block = Block(children=[], in_vars=[])
        glob_time = Var(self.TIME_NAME)

        self.history_models: List[BergeronHistoryRuntime | JMartiHistoryRuntime] = list()
        self._block_boundary_updater: Any | None = None
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

        self._validate_dynamic_emt_interfaces()
        validate_interfaces_s: float = _toc(t_phase_start)
        t_phase_start = _tic()

        self._working_emt_models: Dict[str, Block] = dict()
        self._registered_working_emt_models: Set[str] = set()

        # build on local sys_block
        self._build_structure_and_collect(sys_block=sys_block, grid=grid, static_parameter_values_mapping=static_parameter_values_mapping )
        structure_collect_s: float = _toc(t_phase_start)
        t_phase_start = _tic()

        sys_block.unify_blocks()
        _deduplicate_block_entities(sys_block)
        # The EMT problem compiles the unified root block, so the static-parameter
        # table must be realigned with the final flattened symbolic graph before
        # compiler names are generated. Wrapper, GUI and cloned workflows can keep
        # API-mapped parameter vars only in child blocks during collection, and the
        # subsequent unification step can then leave the pre-collected parameter map
        # out of sync with the actual vars referenced by the final equations.
        _realign_static_parameter_mapping_with_unified_block(
            sys_block=sys_block,
            static_parameter_values_mapping=static_parameter_values_mapping,
        )
        unify_blocks_s: float = _toc(t_phase_start)
        t_phase_start = _tic()

        self._validate_connections()
        validate_connections_s: float = _toc(t_phase_start)
        t_phase_start = _tic()

        # initialize template with the complete block
        super().__init__(sys_block=sys_block,
                         static_parameter_values_mapping=static_parameter_values_mapping,
                         glob_time=glob_time,
                         progress_signal=progress_signal,
                         progress_text=progress_text)

        self._rebuild_results_var_name_lookup()
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

        # The retained runtime snapshot must follow the finalized flat runtime
        # vector order, not the original block-discovery order. Bergeron history
        # parameters are classified as retained mode parameters and moved to the
        # tail of the runtime vector, so preserving the already partitioned event
        # equation list keeps later event-group activation aligned with
        # ``uid2idx_event_params``.
        self._runtime_parameter_eqs0 = list(self._event_parameters_eqs)
        finalize_emt_fmu_cs_devices(self)
        finalize_emt_fmu_me_devices(self)

        self._block_boundary_updater = build_boundary_updater_from_block(self)

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
            self.progress_signal.emit(5)

        # 2) Initialization stage selection.
        # Explicit initialization is the lightweight symbolic seed stage that
        # resolves device-provided init equations directly. The broader EMT
        # workflow may either stop here, use it as a seed for the reduced
        # native consistency solve, or skip it entirely when the user
        # requests a pure pseudo-transient initialization path driven only by
        # the power-flow seeded variables.
        if self.options.initialization_method == EmtInitializationMethod.PseudoTransient:
            pass
        else:
            self._run_explicit_initialization()
        explicit_init_s: float = _toc(t_phase_start)
        t_phase_start = _tic()

        # 3) Native initialization stage selection.
        # The native stage builds and solves the reduced consistency system only
        # for workflows that require it. Pure Explicit stops after the symbolic
        # seeding stage, while the other methods use the native initialization
        # dispatcher to execute their requested algorithm from the current seed.
        if self.options.initialization_method == EmtInitializationMethod.Explicit:
            self.initialization_report = EmtInitializationReport(method_requested=EmtInitializationMethod.Explicit)
            self.initialization_report.status = EmtInitializationStatus.RESOLVED
            self.initialization_report.method_used = EmtInitializationMethod.Explicit
            self.initialization_report.message = "Explicit initialization completed."
        else:
            self.initialization_report = run_emt_native_initialization(problem=self, options=self.options)
        self._seed_all_switched_vsc_models()
        self._seed_all_switch_models()
        self.init_guess.update(self._temp_post_init_guess)
        self.diff_init_guess.update(self._temp_post_diff_init_guess)
        # for diff_uid, diff_value in self._temp_post_diff_init_guess.items():
        #     if diff_uid in self.diff_init_guess:
        #         pass
        #     else:
        #         self.diff_init_guess[diff_uid] = float(diff_value)
        native_init_s: float = _toc(t_phase_start)
        t_phase_start = _tic()

        if self.progress_signal is not None:
            self.progress_signal.emit(10)

        # EMT event groups are activated only after the initialization stage.
        # Some runtime parameters start as Const(None) placeholders and are
        # resolved during explicit/native initialization. Wrapping them in
        # piecewise expressions before that would preserve the undefined default
        # and break the initial runtime-parameter evaluation.
        self.set_events_group(None)
        if self.initialization_report is None:
            pass
        else:
            _compute_missing_dx0(
                problem=self,
                report=self.initialization_report,
                x_full=self.get_x0(),
                dx_full=self.get_dx0(),
                runtime_params=self.event_params_values.copy(),
                constant_params=np.asarray(
                    [float(const.value) for const in self.get_parameters_values()],
                    dtype=np.float64,
                ),
                include_existing=False,
            )
        events_group_finalize_s: float = _toc(t_phase_start)

        t_done = _toc(t_build)
        cache_stats_after: Dict[str, float] = get_compiled_functions_cache_stats()
        compiled_function_cache_delta: float = cache_stats_after.get("entry_count", 0.0) - cache_stats_before.get("entry_count", 0.0)
        native_structural_cold_s: float
        native_numeric_refresh_s: float

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
    def _device_block_has_init_equations(self, mdl: Block) -> bool:
        """
        Return whether one unified device block contributes explicit init equations.

        The device working model is flattened through ``unify_blocks()`` before
        explicit initialization registration. After that stage, all child init
        equations that belong to the device hierarchy are merged into the device
        root itself. The explicit initializer should therefore treat the unified
        device block as the only initialization unit.

        :param mdl: Root block to inspect.
        :type mdl: Block
        :return: ``True`` when the device block has explicit init equations.
        :rtype: bool
        """
        init_eqs: Dict[Var, Expr] = mdl.init_eqs
        diff_init_eqs: Dict[Var, Expr] = mdl.diff_init_eqs
        has_init_eqs: bool = len(init_eqs) > 0
        has_diff_init_eqs: bool = len(diff_init_eqs) > 0

        if has_init_eqs:
            return True
        else:
            if has_diff_init_eqs:
                return True
            else:
                return False

    def _register_init_model(self, mdl: Block) -> None:
        """
        Register one unified device working model for explicit initialization.

        The broader EMT build process already connects the working model and then
        flattens it through ``unify_blocks()`` before this registration point. At
        that stage the device root owns the merged ``init_eqs`` / ``diff_init_eqs``
        of its full hierarchy, so explicit initialization must run exactly once on
        that root block instead of iterating over stale child blocks.

        :param mdl: Unified device working model.
        :type mdl: Block
        :return: None.
        :rtype: None
        """
        has_init_equations: bool = self._device_block_has_init_equations(mdl)

        if has_init_equations:
            if mdl.uid in self._device_models_with_init_eqs_seen:
                pass
            else:
                self._device_models_with_init_eqs_seen.add(mdl.uid)
                self._device_models_with_init_eqs.append(mdl)
        else:
            pass

    def get_build_report(self) -> Dict[str, float]:
        """
        Return the EMT problem build timing report.

        :return: Build timing report.
        :rtype: Dict[str, float]
        """
        return dict(self.build_report)

    def _run_explicit_initialization(self) -> None:
        """
        Run explicit initialization once per unified device working model.

        The working-device model already contains the merged controller, plant,
        runtime parameter, and init-equation hierarchy after ``unify_blocks()``.
        Initializing the device root as one flat block preserves coupled operating
        points across sibling sub-blocks, which is required for EMT templates whose
        current references, delayed commands, and plant states must be seeded
        together.

        :return: None
        :rtype: None
        """

        if len(self._device_models_with_init_eqs) == 0:
            return
        else:
            pass

        # The explicit solver works on the already assembled global variable maps,
        # but each call consumes one unified device block so sibling device states
        # remain decoupled while sibling controller/plant blocks inside the device
        # are initialized together.
        sys_vars: Dict[int, Var] = {v.uid: v for v in (self._state_vars + self._algebraic_vars)}
        sys_diff_vars: Dict[int, Var] = {dv.uid: dv for dv in self._diff_vars}
        compile_single_equation: Any = build_symbolic_vector_single_equation_compiler(
            compiler_names_dict=self._compiler_names_dict,
            alias_names_dict=self._alias_names_dict,
            vars_name=self.VARS_NAME,
            diff_name=self.DIFF_NAME,
            event_params_name=self.VARIABLE_PARAMS_NAME,
            params_name=self.CONSTANT_PARAMS_NAME,
        )

        seen_blocks: Set[int] = set()

        for mdl in self._device_models_with_init_eqs:
            if mdl.uid not in seen_blocks:
                seen_blocks.add(mdl.uid)

                try:
                    params_array: np.ndarray = np.asarray(
                        [float(const.value) for const in self.get_parameters_values()],
                        dtype=np.float64,
                    )

                    self.init_guess, self.diff_init_guess = init_explicit_common(
                        mdl=mdl,
                        sys_vars=sys_vars,
                        sys_diff_vars=sys_diff_vars,
                        variable_parameters=self._variable_parameters,
                        event_parameters_eqs=self._event_parameters_eqs,
                        constant_parameters=self._constant_parameters,
                        event_param_init_dict=self.event_params_init_dict,
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
                            pass
                        else:
                            mdl.event_dict[event_var] = self._event_parameters_eqs[event_idx]
                            self._runtime_parameter_eqs0[event_idx] = self._event_parameters_eqs[event_idx]
                except Exception as e:
                    block_name: str = _get_block_name(mdl)
                    error_detail: str = f"{type(e).__name__}: {str(e)}"

                    self.logger.add_warning(
                        msg="EMT explicit initialization failed for unified device block.",
                        device=block_name,
                        value=error_detail,
                        expected_value="Successful explicit initialization",
                        device_class="EMT",
                        device_property="init_explicit"
                    )

                    if self.options.verbose > 0:
                        self.logger.add_debug(
                            f"[EMT][init_explicit] failed for unified device block '{block_name}'. Error: {error_detail}"
                        )
                        print(
                            f"EMT explicit initialization failed for unified device block {block_name}. "
                            f"Error detail: {error_detail}"
                        )
                    else:
                        pass
            else:
                pass


        self._build_runtime_param_vectors()

    def _seed_bess_battery_init_from_converter(self) -> None:
        """
        Reserved helper for future coordinated BESS battery/DC initialization.

        :return: None.
        """
        return


    def _validate_dynamic_emt_interfaces(self) -> None:
        """
        Validate that dynamic EMT ports are compatible with the static bus shells.

        The editor may expose a broader maximum EMT interface than the current
        network configuration. Before any symbolic rewiring or KCL assembly takes
        place, this validation checks that every exposed electrical reference can
        be reconciled with the corresponding bus domain and EMT bus shell.

        :raises EmtInterfaceValidationError: If any device exposes incompatible
            AC, neutral, or DC EMT references.
        :return: None.
        """
        errors: List[str] = list()
        branch: Any
        injection: Any

        for branch in self.grid.get_branches_iter(add_vsc=True, add_hvdc=True, add_switch=True):
            errors.extend(self._validate_branch_emt_interface(branch))

        for injection in self.grid.get_injection_devices_iter():
            errors.extend(self._validate_injection_emt_interface(injection))

        if len(errors) > 0:
            error_msg = "EMT interface validation failed:\n" + "\n".join(errors)
            raise EmtInterfaceValidationError(error_msg)
        else:
            pass

    def _validate_injection_emt_interface(self, injection: Any) -> List[str]:
        """
        Validate the external EMT interface exposed by one injection device.

        :param injection: Injection device to validate.
        :return: List of validation errors for this device.
        """
        present_refs: Set[VarPowerFlowReferenceType] = self._get_present_external_refs(injection.emt_model)
        errors: List[str] = list()

        errors.extend(self._validate_injection_bus_contract(
            device=injection,
            bus=injection.bus,
            side="injection",
            present_refs=present_refs,
        ))

        return errors

    def _validate_injection_bus_contract(self,
                                         device: Any,
                                         bus: Any,
                                         side: str,
                                         present_refs: Set[VarPowerFlowReferenceType]) -> List[str]:
        """
        Validate one injection-style EMT interface against one bus shell.

        :param device: Device exposing the interface.
        :param bus: Connected bus.
        :param side: User-facing side label.
        :param present_refs: Non-null external references exposed by the device.
        :return: List of validation errors.
        """
        errors: List[str] = list()
        ac_voltage_refs: List[VarPowerFlowReferenceType] = list([
            VarPowerFlowReferenceType.v_N,
            VarPowerFlowReferenceType.v_A,
            VarPowerFlowReferenceType.v_B,
            VarPowerFlowReferenceType.v_C,
        ])
        ac_current_to_voltage: Dict[VarPowerFlowReferenceType, VarPowerFlowReferenceType] = dict({
            VarPowerFlowReferenceType.i_N: VarPowerFlowReferenceType.v_N,
            VarPowerFlowReferenceType.i_A: VarPowerFlowReferenceType.v_A,
            VarPowerFlowReferenceType.i_B: VarPowerFlowReferenceType.v_B,
            VarPowerFlowReferenceType.i_C: VarPowerFlowReferenceType.v_C,
        })
        supported_bus_voltage_refs: Set[VarPowerFlowReferenceType] = self._get_bus_voltage_refs(bus)
        voltage_ref: VarPowerFlowReferenceType
        current_ref: VarPowerFlowReferenceType
        required_voltage_ref: VarPowerFlowReferenceType

        if bus.is_dc:
            for voltage_ref in ac_voltage_refs:
                if voltage_ref in present_refs:
                    errors.append(self._build_emt_interface_error(
                        device=device,
                        bus=bus,
                        side=side,
                        reference=voltage_ref,
                        detail="AC phase reference exposed on a DC bus.",
                    ))
                else:
                    pass

            for current_ref in ac_current_to_voltage.keys():
                if current_ref in present_refs:
                    errors.append(self._build_emt_interface_error(
                        device=device,
                        bus=bus,
                        side=side,
                        reference=current_ref,
                        detail="AC current reference exposed on a DC bus.",
                    ))
                else:
                    pass

            if VarPowerFlowReferenceType.Vdc in present_refs and VarPowerFlowReferenceType.Vdc not in supported_bus_voltage_refs:
                errors.append(self._build_emt_interface_error(
                    device=device,
                    bus=bus,
                    side=side,
                    reference=VarPowerFlowReferenceType.Vdc,
                    detail="DC voltage reference exposed but the bus EMT shell has no Vdc variable.",
                ))
            else:
                pass

            if VarPowerFlowReferenceType.Idc in present_refs:
                if VarPowerFlowReferenceType.Vdc not in present_refs:
                    errors.append(self._build_emt_interface_error(
                        device=device,
                        bus=bus,
                        side=side,
                        reference=VarPowerFlowReferenceType.Idc,
                        detail="DC current reference exposed without a compatible Vdc input reference.",
                    ))
                else:
                    pass

                if VarPowerFlowReferenceType.Vdc not in supported_bus_voltage_refs:
                    errors.append(self._build_emt_interface_error(
                        device=device,
                        bus=bus,
                        side=side,
                        reference=VarPowerFlowReferenceType.Idc,
                        detail="DC current reference exposed but the bus EMT shell has no Vdc variable.",
                    ))
                else:
                    pass
            else:
                pass
        else:
            if VarPowerFlowReferenceType.Vdc in present_refs:
                errors.append(self._build_emt_interface_error(
                    device=device,
                    bus=bus,
                    side=side,
                    reference=VarPowerFlowReferenceType.Vdc,
                    detail="DC voltage reference exposed on an AC bus.",
                ))
            else:
                pass

            if VarPowerFlowReferenceType.Idc in present_refs:
                errors.append(self._build_emt_interface_error(
                    device=device,
                    bus=bus,
                    side=side,
                    reference=VarPowerFlowReferenceType.Idc,
                    detail="DC current reference exposed on an AC bus.",
                ))
            else:
                pass

            for voltage_ref in ac_voltage_refs:
                if voltage_ref in present_refs and voltage_ref not in supported_bus_voltage_refs:
                    errors.append(self._build_emt_interface_error(
                        device=device,
                        bus=bus,
                        side=side,
                        reference=voltage_ref,
                        detail="Voltage reference exposed but the bus EMT shell does not support it.",
                    ))
                else:
                    pass

            for current_ref, required_voltage_ref in ac_current_to_voltage.items():
                if current_ref in present_refs:
                    if required_voltage_ref not in present_refs:
                        errors.append(self._build_emt_interface_error(
                            device=device,
                            bus=bus,
                            side=side,
                            reference=current_ref,
                            detail=(
                                f"Current reference exposed without a compatible "
                                f"{required_voltage_ref.value} input reference."
                            ),
                        ))
                    else:
                        pass

                    if required_voltage_ref not in supported_bus_voltage_refs:
                        errors.append(self._build_emt_interface_error(
                            device=device,
                            bus=bus,
                            side=side,
                            reference=current_ref,
                            detail="Current reference exposed but the bus EMT shell does not support the corresponding voltage phase.",
                        ))
                    else:
                        pass
                else:
                    pass

        return errors

    def _validate_branch_emt_interface(self, branch: Any) -> List[str]:
        """
        Validate the external EMT interface exposed by one branch device.

        :param branch: Branch device to validate.
        :return: List of validation errors for this branch.
        """
        present_refs: Set[VarPowerFlowReferenceType] = self._get_present_external_refs(branch.emt_model)
        errors: List[str] = list()

        errors.extend(self._validate_branch_side_emt_interface(
            device=branch,
            bus=branch.bus_from,
            side="from",
            present_refs=present_refs,
            voltage_map=dict({
                VarPowerFlowReferenceType.vf_N: VarPowerFlowReferenceType.v_N,
                VarPowerFlowReferenceType.vf_A: VarPowerFlowReferenceType.v_A,
                VarPowerFlowReferenceType.vf_B: VarPowerFlowReferenceType.v_B,
                VarPowerFlowReferenceType.vf_C: VarPowerFlowReferenceType.v_C,
                VarPowerFlowReferenceType.Vf_dc: VarPowerFlowReferenceType.Vdc,
            }),
            current_to_voltage_map=dict({
                VarPowerFlowReferenceType.if_N: VarPowerFlowReferenceType.vf_N,
                VarPowerFlowReferenceType.if_A: VarPowerFlowReferenceType.vf_A,
                VarPowerFlowReferenceType.if_B: VarPowerFlowReferenceType.vf_B,
                VarPowerFlowReferenceType.if_C: VarPowerFlowReferenceType.vf_C,
                VarPowerFlowReferenceType.If_dc: VarPowerFlowReferenceType.Vf_dc,
            }),
        ))

        errors.extend(self._validate_branch_side_emt_interface(
            device=branch,
            bus=branch.bus_to,
            side="to",
            present_refs=present_refs,
            voltage_map=dict({
                VarPowerFlowReferenceType.vt_N: VarPowerFlowReferenceType.v_N,
                VarPowerFlowReferenceType.vt_A: VarPowerFlowReferenceType.v_A,
                VarPowerFlowReferenceType.vt_B: VarPowerFlowReferenceType.v_B,
                VarPowerFlowReferenceType.vt_C: VarPowerFlowReferenceType.v_C,
                VarPowerFlowReferenceType.Vt_dc: VarPowerFlowReferenceType.Vdc,
            }),
            current_to_voltage_map=dict({
                VarPowerFlowReferenceType.it_N: VarPowerFlowReferenceType.vt_N,
                VarPowerFlowReferenceType.it_A: VarPowerFlowReferenceType.vt_A,
                VarPowerFlowReferenceType.it_B: VarPowerFlowReferenceType.vt_B,
                VarPowerFlowReferenceType.it_C: VarPowerFlowReferenceType.vt_C,
                VarPowerFlowReferenceType.It_dc: VarPowerFlowReferenceType.Vt_dc,
            }),
        ))

        errors.extend(self._validate_shared_branch_emt_interface(branch, present_refs))
        errors.extend(self._validate_branch_dc_mapping_collisions(branch))

        return errors

    def _validate_branch_side_emt_interface(self,
                                            device: Any,
                                            bus: Any,
                                            side: str,
                                            present_refs: Set[VarPowerFlowReferenceType],
                                            voltage_map: Dict[VarPowerFlowReferenceType, VarPowerFlowReferenceType],
                                            current_to_voltage_map: Dict[VarPowerFlowReferenceType, VarPowerFlowReferenceType]) -> List[str]:
        """
        Validate one side-specific branch EMT contract against one terminal bus.

        :param device: Branch device exposing the interface.
        :param bus: Terminal bus to validate against.
        :param side: ``from`` or ``to``.
        :param present_refs: Non-null external references exposed by the branch.
        :param voltage_map: Mapping from branch voltage refs to bus voltage refs.
        :param current_to_voltage_map: Mapping from branch current refs to branch voltage refs.
        :return: List of validation errors.
        """
        errors: List[str] = list()
        supported_bus_voltage_refs: Set[VarPowerFlowReferenceType] = self._get_bus_voltage_refs(bus)
        branch_voltage_ref: VarPowerFlowReferenceType
        bus_voltage_ref: VarPowerFlowReferenceType
        current_ref: VarPowerFlowReferenceType
        required_branch_voltage_ref: VarPowerFlowReferenceType
        required_bus_voltage_ref: VarPowerFlowReferenceType

        for branch_voltage_ref, bus_voltage_ref in voltage_map.items():
            if branch_voltage_ref in present_refs:
                if bus.is_dc and bus_voltage_ref != VarPowerFlowReferenceType.Vdc:
                    errors.append(self._build_emt_interface_error(
                        device=device,
                        bus=bus,
                        side=side,
                        reference=branch_voltage_ref,
                        detail="AC branch voltage reference exposed on a DC bus.",
                    ))
                elif (not bus.is_dc) and bus_voltage_ref == VarPowerFlowReferenceType.Vdc:
                    errors.append(self._build_emt_interface_error(
                        device=device,
                        bus=bus,
                        side=side,
                        reference=branch_voltage_ref,
                        detail="DC branch voltage reference exposed on an AC bus.",
                    ))
                elif bus_voltage_ref not in supported_bus_voltage_refs:
                    errors.append(self._build_emt_interface_error(
                        device=device,
                        bus=bus,
                        side=side,
                        reference=branch_voltage_ref,
                        detail="Voltage reference exposed but the terminal bus EMT shell does not support it.",
                    ))
                else:
                    pass
            else:
                pass

        for current_ref, required_branch_voltage_ref in current_to_voltage_map.items():
            if current_ref in present_refs:
                required_bus_voltage_ref = voltage_map[required_branch_voltage_ref]

                if required_branch_voltage_ref not in present_refs:
                    errors.append(self._build_emt_interface_error(
                        device=device,
                        bus=bus,
                        side=side,
                        reference=current_ref,
                        detail=(
                            f"Current reference exposed without a compatible "
                            f"{required_branch_voltage_ref.value} input reference."
                        ),
                    ))
                else:
                    pass

                if bus.is_dc and required_bus_voltage_ref != VarPowerFlowReferenceType.Vdc:
                    errors.append(self._build_emt_interface_error(
                        device=device,
                        bus=bus,
                        side=side,
                        reference=current_ref,
                        detail="AC branch current reference exposed on a DC bus.",
                    ))
                elif (not bus.is_dc) and required_bus_voltage_ref == VarPowerFlowReferenceType.Vdc:
                    errors.append(self._build_emt_interface_error(
                        device=device,
                        bus=bus,
                        side=side,
                        reference=current_ref,
                        detail="DC branch current reference exposed on an AC bus.",
                    ))
                elif required_bus_voltage_ref not in supported_bus_voltage_refs:
                    errors.append(self._build_emt_interface_error(
                        device=device,
                        bus=bus,
                        side=side,
                        reference=current_ref,
                        detail="Current reference exposed but the terminal bus EMT shell does not support the corresponding voltage phase.",
                    ))
                else:
                    pass
            else:
                pass

        return errors

    def _validate_shared_branch_emt_interface(self,
                                              branch: Any,
                                              present_refs: Set[VarPowerFlowReferenceType]) -> List[str]:
        """
        Validate shared EMT branch references used by VSC-style branch models.

        Some branch EMT templates use a single AC-side contract ``v_A/B/C`` and a
        single DC-side contract ``Vdc``/``Idc`` instead of side-specific branch
        terminal references. This validator allows that contract only when the
        network has exactly one compatible side for it.

        Two-sided DC branches are handled separately by
        ``_validate_branch_dc_mapping_collisions`` because legacy DC branch
        templates may expose shared ``Vdc`` / ``Idc`` only as aliases of their
        explicit terminal variables.

        :param branch: Branch device to validate.
        :param present_refs: Non-null external references exposed by the branch.
        :return: List of validation errors.
        """
        errors: List[str] = list()
        shared_ac_refs: Set[VarPowerFlowReferenceType] = {
            VarPowerFlowReferenceType.v_N,
            VarPowerFlowReferenceType.v_A,
            VarPowerFlowReferenceType.v_B,
            VarPowerFlowReferenceType.v_C,
            VarPowerFlowReferenceType.i_N,
            VarPowerFlowReferenceType.i_A,
            VarPowerFlowReferenceType.i_B,
            VarPowerFlowReferenceType.i_C,
        }
        shared_dc_refs: Set[VarPowerFlowReferenceType] = {
            VarPowerFlowReferenceType.Vdc,
            VarPowerFlowReferenceType.Idc,
        }
        shared_ac_present: Set[VarPowerFlowReferenceType] = present_refs.intersection(shared_ac_refs)
        shared_dc_present: Set[VarPowerFlowReferenceType] = present_refs.intersection(shared_dc_refs)
        ac_side_count: int = self._count_branch_sides_by_domain(branch, is_dc=False)
        dc_side_count: int = self._count_branch_sides_by_domain(branch, is_dc=True)

        if len(shared_ac_present) > 0:
            if ac_side_count == 1:
                if branch.bus_from.is_dc:
                    errors.extend(self._validate_injection_bus_contract(
                        device=branch,
                        bus=branch.bus_to,
                        side="to",
                        present_refs=shared_ac_present,
                    ))
                else:
                    errors.extend(self._validate_injection_bus_contract(
                        device=branch,
                        bus=branch.bus_from,
                        side="from",
                        present_refs=shared_ac_present,
                    ))
            else:
                errors.extend(self._build_shared_branch_domain_errors(
                    branch=branch,
                    refs=shared_ac_present,
                    expected_domain="AC",
                    side_count=ac_side_count,
                ))
        else:
            pass

        if len(shared_dc_present) > 0:
            if dc_side_count == 1:
                if branch.bus_from.is_dc:
                    errors.extend(self._validate_injection_bus_contract(
                        device=branch,
                        bus=branch.bus_from,
                        side="from",
                        present_refs=shared_dc_present,
                    ))
                else:
                    errors.extend(self._validate_injection_bus_contract(
                        device=branch,
                        bus=branch.bus_to,
                        side="to",
                        present_refs=shared_dc_present,
                    ))
            elif dc_side_count == 2:
                # Two-sided DC branches may legally expose shared aliases when the
                # real contract is still the explicit Vf/Vt and If/It terminal set.
                pass
            else:
                errors.extend(self._build_shared_branch_domain_errors(
                    branch=branch,
                    refs=shared_dc_present,
                    expected_domain="DC",
                    side_count=dc_side_count,
                ))
        else:
            pass

        return errors

    def _is_valid_legacy_shared_dc_branch_alias(self,
                                                branch: Any,
                                                reference: VarPowerFlowReferenceType) -> bool:
        """
        Return whether one shared DC branch reference is a valid legacy alias.

        Legacy two-sided DC branch templates may keep exposing ``Vdc`` or ``Idc``
        for backward compatibility even though EMT assembly now uses the explicit
        terminal contract ``Vf_dc`` / ``Vt_dc`` and ``If_dc`` / ``It_dc``.
        The shared reference is accepted only when both DC sides are present and
        the shared mapping aliases one of the already explicit terminal variables.

        :param branch: Branch device to inspect.
        :param reference: Shared DC reference to validate.
        :return: ``True`` when the shared reference is a safe legacy alias.
        """
        external_mapping: Optional[Dict[Any, Var]] = _get_external_mapping(branch.emt_model)
        shared_var: Var | None
        from_var: Var | None
        to_var: Var | None

        if external_mapping is None:
            return False
        else:
            pass

        if not (branch.bus_from.is_dc and branch.bus_to.is_dc):
            return False
        else:
            pass

        if reference == VarPowerFlowReferenceType.Vdc:
            shared_var = external_mapping.get(VarPowerFlowReferenceType.Vdc, None)
            from_var = external_mapping.get(VarPowerFlowReferenceType.Vf_dc, None)
            to_var = external_mapping.get(VarPowerFlowReferenceType.Vt_dc, None)
        elif reference == VarPowerFlowReferenceType.Idc:
            shared_var = external_mapping.get(VarPowerFlowReferenceType.Idc, None)
            from_var = external_mapping.get(VarPowerFlowReferenceType.If_dc, None)
            to_var = external_mapping.get(VarPowerFlowReferenceType.It_dc, None)
        else:
            return False

        if shared_var is None or from_var is None or to_var is None:
            return False
        else:
            pass

        if shared_var.uid == from_var.uid:
            return True
        else:
            pass

        if shared_var.uid == to_var.uid:
            return True
        else:
            return False

    def _build_shared_branch_domain_errors(self,
                                           branch: Any,
                                           refs: Set[VarPowerFlowReferenceType],
                                           expected_domain: str,
                                           side_count: int) -> List[str]:
        """
        Build explicit errors for ambiguous shared branch-domain references.

        :param branch: Branch device exposing the references.
        :param refs: Shared references that could not be assigned safely.
        :param expected_domain: Domain required by the shared references.
        :param side_count: Number of compatible terminal buses found.
        :return: List of formatted error strings.
        """
        errors: List[str] = list()
        reference: VarPowerFlowReferenceType

        for reference in refs:
            errors.append(
                f"  - Device '{self._get_device_name(branch)}' ({self._get_device_type_label(branch)}) "
                f"branch ref '{reference.value}' is a shared {expected_domain} interface, but the branch has "
                f"{side_count} compatible {expected_domain} side(s). Use side-specific EMT references instead."
            )

        return errors

    def _validate_branch_dc_mapping_collisions(self, branch: Any) -> List[str]:
        """
        Validate that branch DC terminal mappings cannot collide across sides.

        :param branch: Branch device to validate.
        :return: List of validation errors.
        """
        errors: List[str] = list()
        external_mapping: Optional[Dict[Any, Var]] = _get_external_mapping(branch.emt_model)
        if_dc_var: Var | None
        it_dc_var: Var | None
        v_f_dc_var: Var | None
        v_t_dc_var: Var | None
        shared_v_dc_var: Var | None
        shared_i_dc_var: Var | None

        if external_mapping is None:
            return errors
        else:
            pass

        if_dc_var = external_mapping.get(VarPowerFlowReferenceType.If_dc, None)
        it_dc_var = external_mapping.get(VarPowerFlowReferenceType.It_dc, None)
        v_f_dc_var = external_mapping.get(VarPowerFlowReferenceType.Vf_dc, None)
        v_t_dc_var = external_mapping.get(VarPowerFlowReferenceType.Vt_dc, None)
        shared_v_dc_var = external_mapping.get(VarPowerFlowReferenceType.Vdc, None)
        shared_i_dc_var = external_mapping.get(VarPowerFlowReferenceType.Idc, None)

        if if_dc_var is not None and it_dc_var is not None and if_dc_var.uid == it_dc_var.uid:
            errors.append(
                f"  - Device '{self._get_device_name(branch)}' ({self._get_device_type_label(branch)}) "
                "uses the same variable for both If_dc and It_dc. Branch DC terminal currents must be side-specific."
            )
        else:
            pass

        if v_f_dc_var is not None and v_t_dc_var is not None and v_f_dc_var.uid == v_t_dc_var.uid:
            errors.append(
                f"  - Device '{self._get_device_name(branch)}' ({self._get_device_type_label(branch)}) "
                "uses the same variable for both Vf_dc and Vt_dc. Branch DC terminal voltages must be side-specific."
            )
        else:
            pass

        if branch.bus_from.is_dc and branch.bus_to.is_dc:
            if shared_v_dc_var is not None:
                if self._is_valid_legacy_shared_dc_branch_alias(branch, VarPowerFlowReferenceType.Vdc):
                    pass
                else:
                    errors.append(
                        f"  - Device '{self._get_device_name(branch)}' ({self._get_device_type_label(branch)}) "
                        "exposes shared Vdc on a two-sided DC branch without a full side-specific alias contract. "
                        "Use Vf_dc and Vt_dc instead."
                    )
            else:
                pass

            if shared_i_dc_var is not None:
                if self._is_valid_legacy_shared_dc_branch_alias(branch, VarPowerFlowReferenceType.Idc):
                    pass
                else:
                    errors.append(
                        f"  - Device '{self._get_device_name(branch)}' ({self._get_device_type_label(branch)}) "
                        "exposes shared Idc on a two-sided DC branch without a full side-specific alias contract. "
                        "Use If_dc and It_dc instead."
                    )
            else:
                pass
        else:
            pass

        return errors

    def _count_branch_sides_by_domain(self, branch: Any, is_dc: bool) -> int:
        """
        Count the number of branch terminal buses matching one electrical domain.

        :param branch: Branch device to inspect.
        :param is_dc: ``True`` for DC buses, ``False`` for AC buses.
        :return: Number of matching terminal buses.
        """
        count: int = 0

        if branch.bus_from.is_dc == is_dc:
            count += 1
        else:
            pass

        if branch.bus_to.is_dc == is_dc:
            count += 1
        else:
            pass

        return count

    def _get_present_external_refs(self, mdl: Block) -> Set[VarPowerFlowReferenceType]:
        """
        Return the set of non-null electrical external references exposed by one model.

        :param mdl: Device block to inspect.
        :return: Set of exposed external reference keys.
        """
        refs: Set[VarPowerFlowReferenceType] = set()
        external_mapping: Optional[Dict[Any, Var]] = _get_external_mapping(mdl)
        reference: Any
        mapped_var: Var | None

        if external_mapping is None:
            return refs
        else:
            pass

        for reference, mapped_var in external_mapping.items():
            if isinstance(reference, VarPowerFlowReferenceType) and mapped_var is not None:
                refs.add(reference)
            else:
                pass

        return refs

    def _get_bus_voltage_refs(self, bus: Any) -> Set[VarPowerFlowReferenceType]:
        """
        Return the non-null bus-shell voltage references supported by one bus.

        :param bus: Bus API object.
        :return: Supported bus voltage references.
        """
        refs: Set[VarPowerFlowReferenceType] = set()
        reference: VarPowerFlowReferenceType
        candidate_refs: List[VarPowerFlowReferenceType]

        if bus.is_dc:
            candidate_refs = list([VarPowerFlowReferenceType.Vdc])
        else:
            candidate_refs = list([
                VarPowerFlowReferenceType.v_N,
                VarPowerFlowReferenceType.v_A,
                VarPowerFlowReferenceType.v_B,
                VarPowerFlowReferenceType.v_C,
            ])

        for reference in candidate_refs:
            if _get_external_mapping_var_if_present(bus.emt_model, reference) is not None:
                refs.add(reference)
            else:
                pass

        return refs

    def _build_emt_interface_error(self,
                                   device: Any,
                                   bus: Any,
                                   side: str,
                                   reference: VarPowerFlowReferenceType,
                                   detail: str) -> str:
        """
        Build one formatted EMT interface-validation error message.

        :param device: Device that exposes the incompatible reference.
        :param bus: Connected bus.
        :param side: User-facing side label.
        :param reference: Incompatible external reference.
        :param detail: Specific mismatch explanation.
        :return: Formatted error string.
        """
        category: str = self._get_emt_interface_ref_category(reference)
        return (
            f"  - Device '{self._get_device_name(device)}' ({self._get_device_type_label(device)}) "
            f"bus '{bus.name}' side '{side}' ref '{reference.value}' [{category}]: {detail}"
        )

    def _get_emt_interface_ref_category(self, reference: VarPowerFlowReferenceType) -> str:
        """
        Classify one EMT electrical reference for user-facing error messages.

        :param reference: Electrical interface reference.
        :return: Category label such as ``AC phase``, ``neutral``, or ``DC``.
        """
        if reference in {
            VarPowerFlowReferenceType.v_N,
            VarPowerFlowReferenceType.i_N,
            VarPowerFlowReferenceType.vf_N,
            VarPowerFlowReferenceType.if_N,
            VarPowerFlowReferenceType.vt_N,
            VarPowerFlowReferenceType.it_N,
        }:
            return "neutral"
        elif reference in {
            VarPowerFlowReferenceType.Vdc,
            VarPowerFlowReferenceType.Idc,
            VarPowerFlowReferenceType.Vf_dc,
            VarPowerFlowReferenceType.Vt_dc,
            VarPowerFlowReferenceType.If_dc,
            VarPowerFlowReferenceType.It_dc,
        }:
            return "DC"
        else:
            return "AC phase"

    def _get_device_name(self, device: Any) -> str:
        """
        Return one stable user-facing device name for diagnostics.

        :param device: Device to describe.
        :return: Device name when available.
        """
        try:
            return str(device.name)
        except Exception:
            return str(type(device).__name__)

    def _get_device_type_label(self, device: Any) -> str:
        """
        Return one stable user-facing device-type label for diagnostics.

        :param device: Device to describe.
        :return: Device-type label.
        """
        try:
            return str(device.device_type.value)
        except Exception:
            return str(type(device).__name__)

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
            VarPowerFlowReferenceType.vf_N: VarPowerFlowReferenceType.v_N,
            VarPowerFlowReferenceType.vf_A: VarPowerFlowReferenceType.v_A,
            VarPowerFlowReferenceType.vf_B: VarPowerFlowReferenceType.v_B,
            VarPowerFlowReferenceType.vf_C: VarPowerFlowReferenceType.v_C,
            VarPowerFlowReferenceType.vt_N: VarPowerFlowReferenceType.v_N,
            VarPowerFlowReferenceType.vt_A: VarPowerFlowReferenceType.v_A,
            VarPowerFlowReferenceType.vt_B: VarPowerFlowReferenceType.v_B,
            VarPowerFlowReferenceType.vt_C: VarPowerFlowReferenceType.v_C,
        }

        branch_phase_refs = {
            VarPowerFlowReferenceType.vf_N,
            VarPowerFlowReferenceType.vf_A,
            VarPowerFlowReferenceType.vf_B,
            VarPowerFlowReferenceType.vf_C,
            VarPowerFlowReferenceType.vt_N,
            VarPowerFlowReferenceType.vt_A,
            VarPowerFlowReferenceType.vt_B,
            VarPowerFlowReferenceType.vt_C,
        }
        ac_phases = [
            VarPowerFlowReferenceType.v_N,
            VarPowerFlowReferenceType.v_A,
            VarPowerFlowReferenceType.v_B,
            VarPowerFlowReferenceType.v_C,
        ]
        bus_phase_connections: Dict[Tuple[Any, VarPowerFlowReferenceType], Set[str]] = dict()
        for bus in self.grid.buses:
            for phase in ac_phases:
                bus_phase_connections[(bus, phase)] = set()

        vsc_ac_phase_refs = {
            VarPowerFlowReferenceType.v_N,
            VarPowerFlowReferenceType.v_A,
            VarPowerFlowReferenceType.v_B,
            VarPowerFlowReferenceType.v_C,
        }

        for br in self.grid.get_branches_iter(add_vsc=True, add_hvdc=True, add_switch=True):
            br_emt_model = self._working_emt_models.get(str(br.idtag), br.emt_model)

            if br.device_type == DeviceType.LineDevice:
                validate_line_phase_layout(branch=br, mdl=br_emt_model, logger=self.logger)
            else:
                pass

            if br_emt_model is not None:
                br_bus_from = br.bus_from
                br_bus_to = br.bus_to
                is_bergeron, is_jmarti = _is_history_runtime_line_block_name(br_emt_model.name)

                if is_bergeron or is_jmarti:
                    br_ys = br.ys

                    if br_ys.phN:
                        bus_phase_connections[(br_bus_from, VarPowerFlowReferenceType.v_N)].add(f"branch_from:{br.idtag}")
                        bus_phase_connections[(br_bus_to, VarPowerFlowReferenceType.v_N)].add(f"branch_to:{br.idtag}")
                    else:
                        pass

                    if br_ys.phA:
                        bus_phase_connections[(br_bus_from, VarPowerFlowReferenceType.v_A)].add(f"branch_from:{br.idtag}")
                        bus_phase_connections[(br_bus_to, VarPowerFlowReferenceType.v_A)].add(f"branch_to:{br.idtag}")
                    else:
                        pass

                    if br_ys.phB:
                        bus_phase_connections[(br_bus_from, VarPowerFlowReferenceType.v_B)].add(f"branch_from:{br.idtag}")
                        bus_phase_connections[(br_bus_to, VarPowerFlowReferenceType.v_B)].add(f"branch_to:{br.idtag}")
                    else:
                        pass

                    if br_ys.phC:
                        bus_phase_connections[(br_bus_from, VarPowerFlowReferenceType.v_C)].add(f"branch_from:{br.idtag}")
                        bus_phase_connections[(br_bus_to, VarPowerFlowReferenceType.v_C)].add(f"branch_to:{br.idtag}")
                    else:
                        pass
                else:
                    # Deserialized EMT blocks may preserve branch terminal
                    # references in nested external mappings even when the root
                    # ``in_vars`` layout differs from a freshly rebuilt
                    # template. Build the connectivity view from the recovered
                    # hierarchical external mapping first, because those keys
                    # are the canonical semantic contract used across the EMT
                    # builder.
                    branch_external_mapping: Optional[Dict[Any, Var]] = _get_external_mapping(br_emt_model)
                    present_branch_refs: Set[VarPowerFlowReferenceType] = set()

                    if branch_external_mapping is not None:
                        branch_ref_key: Any
                        branch_ref_var: Var | None
                        for branch_ref_key, branch_ref_var in branch_external_mapping.items():
                            if isinstance(branch_ref_key, VarPowerFlowReferenceType) and branch_ref_var is not None:
                                present_branch_refs.add(branch_ref_key)
                            else:
                                pass
                    else:
                        pass

                    # Freshly rebuilt models expose the same contract directly
                    # on ``in_vars``. Keep that path as a fallback so both live
                    # and deserialized models are handled uniformly.
                    if len(present_branch_refs) == 0:
                        in_var: Var
                        for in_var in br_emt_model.in_vars:
                            if in_var.ref is not None:
                                present_branch_refs.add(in_var.ref)
                            else:
                                pass
                    else:
                        pass

                    branch_ref: VarPowerFlowReferenceType
                    for branch_ref in present_branch_refs:
                        if branch_ref in branch_phase_refs:
                            bus_phase = phase_ref_to_bus_phase[branch_ref]

                            if branch_ref in {
                                VarPowerFlowReferenceType.vf_N,
                                VarPowerFlowReferenceType.vf_A,
                                VarPowerFlowReferenceType.vf_B,
                                VarPowerFlowReferenceType.vf_C,
                            }:
                                bus_phase_connections[(br_bus_from, bus_phase)].add(f"branch_from:{br.idtag}")
                            elif branch_ref in {
                                VarPowerFlowReferenceType.vt_N,
                                VarPowerFlowReferenceType.vt_A,
                                VarPowerFlowReferenceType.vt_B,
                                VarPowerFlowReferenceType.vt_C,
                            }:
                                bus_phase_connections[(br_bus_to, bus_phase)].add(f"branch_to:{br.idtag}")
                            else:
                                pass
                        elif branch_ref in vsc_ac_phase_refs:
                            if br_bus_to.is_dc:
                                bus_phase_connections[(br_bus_from, branch_ref)].add(f"branch_from:{br.idtag}")
                            else:
                                bus_phase_connections[(br_bus_to, branch_ref)].add(f"branch_to:{br.idtag}")
                        else:
                            pass
            else:
                pass

        for inj in self.grid.get_injection_devices_iter():
            inj_emt_model = self._working_emt_models.get(str(inj.idtag), inj.emt_model)

            if inj_emt_model is not None:
                inj_bus = inj.bus
                for in_var in inj_emt_model.in_vars:
                    if in_var.ref in ac_phases:
                        bus_phase_connections[(inj_bus, in_var.ref)].add(f"injection:{inj.idtag}")
                    else:
                        pass

                if _has_internal_grounding_link(inj_emt_model):
                    bus_phase_connections[(inj_bus, VarPowerFlowReferenceType.v_N)].add(
                        f"internal_ground:{inj.idtag}"
                    )
                else:
                    pass
            else:
                pass

        floating_phases: List[str] = list()
        for bus in self.grid.buses:
            if not bus.is_dc:
                bus_mdl = self._working_emt_models.get(str(bus.idtag), bus.emt_model)
                bus_out_refs = {v.ref for v in bus_mdl.out_vars}
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

    def _process_device_model(self, dev: Any, mdl:Block, sys_block: Block) -> Block:
        """
        Register a device EMT model into the global system block.

        The device model is flattened before being attached to the system block.
        Some wrapper-style models store PF-initialization metadata in nested child
        blocks. For that reason, the relevant mappings are rebuilt first and then
        restored on the device root before the block is added to the global system.

        :param dev: Device object from the grid.
        :param mdl: Device block
        :param sys_block: Main DAE system block.
        :return: Unified device block.
        """
        resolved_external_mapping: Dict[Any, Var]

        # Wrapper roots may not own the PF-parameter mapping directly, so the
        # hierarchy is flattened into one root-visible mapping before build use.
        resolved_api_mapping: Dict[ParamPowerFlowReferenceType, Any] = _collect_api_obj_mapping_from_block(mdl)
        if len(resolved_api_mapping) > 0:
            mdl.api_obj_mapping = resolved_api_mapping
        else:
            pass

        # Wrapper roots may also hide PF variable references in leaf blocks.
        # Re-attaching the merged mapping on the root keeps all later lookups
        # consistent with the already recovered API-object mapping.
        resolved_external_mapping = _collect_external_mapping_from_block(mdl)
        if len(resolved_external_mapping) > 0:
            mdl.external_mapping = resolved_external_mapping
        else:
            pass

        # Cache working EMT models by the stable device idtag instead of the
        # Python object identity so all lookups follow the grid semantic
        # identifier used by the rest of the EMT event machinery.
        dev_key: str = str(dev.idtag)
        if dev_key not in self._registered_working_emt_models:
            parameter_owner_blocks: List[Block] = _collect_block_hierarchy(mdl)
            parameter_owner_block: Block

            # Register runtime-updatable EMT parameters declared by the device block.
            # EMT runtime events are no longer baked into the symbolic model during the
            # parsing phase. Instead, the problem stores the event-capable parameters and
            # later activates the selected EMT event group through ``set_events_group()``.
            if not mdl.event_dict and not mdl.mode_dict:
                # Wrapper roots may keep all runtime parameters inside nested child
                # blocks, so the registration pass must still inspect the full
                # hierarchy before deciding that nothing needs to be registered.
                for parameter_owner_block in parameter_owner_blocks:
                    if parameter_owner_block is mdl:
                        pass
                    else:
                        for parameter in parameter_owner_block.event_dict.keys():
                            self._event_parameter_device_idtags[parameter.uid] = dev.idtag
                            self._event_parameter_name_lookup[(str(dev.idtag), str(parameter.name))] = parameter.uid
                            self._continuous_event_parameter_uids.add(parameter.uid)

                        for parameter in parameter_owner_block.mode_dict.keys():
                            self._event_parameter_device_idtags[parameter.uid] = dev.idtag
                            self._event_parameter_name_lookup[(str(dev.idtag), str(parameter.name))] = parameter.uid
                            self._discrete_event_parameter_uids.add(parameter.uid)
            else:
                for parameter in mdl.event_dict.keys():
                    self._event_parameter_device_idtags[parameter.uid] = dev.idtag
                    self._event_parameter_name_lookup[(str(dev.idtag), str(parameter.name))] = parameter.uid
                    self._continuous_event_parameter_uids.add(parameter.uid)

                for parameter in mdl.mode_dict.keys():
                    self._event_parameter_device_idtags[parameter.uid] = dev.idtag
                    self._event_parameter_name_lookup[(str(dev.idtag), str(parameter.name))] = parameter.uid
                    self._discrete_event_parameter_uids.add(parameter.uid)

                # Child blocks may define additional runtime parameters that are
                # not re-exported on the wrapper root. Those nested parameters
                # must also be registered so later EMT event activation and
                # runtime seeding can find them by UID and by device/name.
                for parameter_owner_block in parameter_owner_blocks:
                    if parameter_owner_block is mdl:
                        pass
                    else:
                        for parameter in parameter_owner_block.event_dict.keys():
                            self._event_parameter_device_idtags[parameter.uid] = dev.idtag
                            self._event_parameter_name_lookup[(str(dev.idtag), str(parameter.name))] = parameter.uid
                            self._continuous_event_parameter_uids.add(parameter.uid)

                        for parameter in parameter_owner_block.mode_dict.keys():
                            self._event_parameter_device_idtags[parameter.uid] = dev.idtag
                            self._event_parameter_name_lookup[(str(dev.idtag), str(parameter.name))] = parameter.uid
                            self._discrete_event_parameter_uids.add(parameter.uid)

            # Add model to system mappings
            # Populates tracking dictionaries to maintain the relationship between
            # electrical devices and their corresponding symbolic variables.
            block_item: Block
            for block_item in mdl.get_all_blocks():
                v: Var
                for v in block_item.state_vars:
                    self.add_device_var(dev=dev, var=v)
                    self._vars_glob_name2uid[v.name + dev.name] = v.uid
                    self._vars2device[v.uid] = dev

                for v in block_item.algebraic_vars:
                    self.add_device_var(dev=dev, var=v)
                    self._vars_glob_name2uid[v.name + dev.name] = v.uid
                    self._vars2device[v.uid] = dev

                dv: Var
                for dv in block_item.diff_vars:
                    self.add_device_var(dev=dev, var=dv)
                    self._vars_glob_name2uid[dv.name + dev.name] = dv.uid
                    self._vars2device[dv.uid] = dev

            queue_emt_fmu_cs_device(self, dev, mdl)
            queue_emt_fmu_me_device(self, dev, mdl)

            sys_block.add(mdl)

            self._register_init_model(mdl)
            # self._register_diff_init_model(mdl)

            self._registered_working_emt_models.add(dev_key)

        return mdl

    @staticmethod
    def _assign_api_mapping_value_if_present(mdl: Block,
                                             key: ParamPowerFlowReferenceType,
                                             value: Any,
                                             static_parameter_values_mapping: Dict[Var, Const],
                                             ) -> None:
        """
        Assign one static API-object parameter into ``mdl.parameters``.

        This function intentionally never writes into ``mdl.event_dict``.
        The ``api_obj_mapping`` contract is static-device to constant EMT
        parameter mapping only. Runtime/event parameters belong to the
        explicit initialization/runtime event path.

        :param mdl: EMT model block.
        :param key: Static parameter reference key.
        :param value: Static value to assign.
        :param static_parameter_values_mapping: Dictionary with static parameters and their values.
        :return: Assignment status.
        """
        api_obj_mapping: Any = mdl.api_obj_mapping
        event_owner: Optional[Block]

        if isinstance(api_obj_mapping, dict):
            target: Any | None = api_obj_mapping.get(key, None)

            if target is not None:
                if isinstance(target, Var):
                    # Wrapper roots may expose API mappings for parameters whose
                    # actual runtime storage belongs to a nested child block.
                    # Static assignment must therefore skip every target that is
                    # owned by any child ``event_dict`` in the hierarchy.
                    event_owner = _find_event_var_owner(mdl, target)
                    if event_owner is not None:
                        pass
                    else:
                        static_parameter_values_mapping[target] = value if isinstance(value, Const) else Const(float(value))
                else:
                    pass
            else:
                pass
        else:
            pass

    @staticmethod
    def _assign_event_mapping_value_if_present(mdl: Block,
                                               key: ParamPowerFlowReferenceType,
                                               value: float,
                                               ) -> None:
        """
        Assign one runtime/event parameter exposed through ``api_obj_mapping``.

        Some higher-level EMT wrappers expose PF-derived sharing targets through
        ``api_obj_mapping`` even though the actual parameter lives in
        ``event_dict``. Those values must be seeded on the runtime side before
        explicit initialization, but they must not pass through the static API
        assignment helper.

        :param mdl: EMT model block.
        :param key: API mapping reference key.
        :param value: Runtime value to assign.
        :return: None.
        """
        api_obj_mapping: Any = mdl.api_obj_mapping
        owner_block: Optional[Block]
        target: Any | None

        if isinstance(api_obj_mapping, dict):
            target = api_obj_mapping.get(key, None)

            if target is None:
                pass
            else:
                if isinstance(target, Var):
                    # The mapped runtime parameter may live in a nested child
                    # block, so the assignment must target the owner block that
                    # actually stores the mutable ``event_dict`` entry.
                    owner_block = _find_event_var_owner(mdl, target)
                    if owner_block is None:
                        pass
                    else:
                        owner_block.event_dict[target] = Const(float(value))
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
            static_parameter_values_mapping: Dict[Var, Const],
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
        :param static_parameter_values_mapping: Dictionary with static parameters and their values.
        :return: None.
        """
        bus_working_models: Dict[Any, Block] = dict()

        for bus in grid.buses:
            bus_working_models[bus] = self._get_or_create_working_emt_model(bus)

        bus_dict: Dict[Any, int] = dict()

        ph_v_keys: List[VarPowerFlowReferenceType] = list([
            VarPowerFlowReferenceType.v_N,
            VarPowerFlowReferenceType.v_A,
            VarPowerFlowReferenceType.v_B,
            VarPowerFlowReferenceType.v_C,
        ])
        inj_i_keys: List[VarPowerFlowReferenceType] = list([
            VarPowerFlowReferenceType.i_N,
            VarPowerFlowReferenceType.i_A,
            VarPowerFlowReferenceType.i_B,
            VarPowerFlowReferenceType.i_C,
        ])
        br_if_keys: List[VarPowerFlowReferenceType] = list([
            VarPowerFlowReferenceType.if_N,
            VarPowerFlowReferenceType.if_A,
            VarPowerFlowReferenceType.if_B,
            VarPowerFlowReferenceType.if_C,
        ])
        br_it_keys: List[VarPowerFlowReferenceType] = list([
            VarPowerFlowReferenceType.it_N,
            VarPowerFlowReferenceType.it_A,
            VarPowerFlowReferenceType.it_B,
            VarPowerFlowReferenceType.it_C,
        ])
        br_vf_keys: List[VarPowerFlowReferenceType] = list([
            VarPowerFlowReferenceType.vf_N,
            VarPowerFlowReferenceType.vf_A,
            VarPowerFlowReferenceType.vf_B,
            VarPowerFlowReferenceType.vf_C,
        ])
        br_vt_keys: List[VarPowerFlowReferenceType] = list([
            VarPowerFlowReferenceType.vt_N,
            VarPowerFlowReferenceType.vt_A,
            VarPowerFlowReferenceType.vt_B,
            VarPowerFlowReferenceType.vt_C,
        ])

        c0: Any = Const(0.0)

        # bus loop to create the I_kcl equations
        I_kcl: Dict[int, List[Any]] = dict()
        for bus_idx, bus in enumerate(grid.buses):
            if bus.is_dc:
                I_kcl[bus_idx] = list([c0])
            else:
                I_kcl[bus_idx] = list([c0, c0, c0, c0])

            bus_dict[bus] = int(bus_idx)

        # Collect injections only after the bus dictionary has been built.
        # The generator-sharing bookkeeping needs the bus indices, so it must run
        # after bus_dict is available.
        injection_devices: List[Any] = list(grid.get_injection_devices_iter())

        generator_count_same_bus: Dict[int, int] = dict()
        for bus_idx, _ in enumerate(grid.buses):
            generator_count_same_bus[bus_idx] = 0
        for inj in injection_devices:
            bus_idx_local: int = bus_dict[inj.bus]
            if inj.device_type == DeviceType.GeneratorDevice:
                generator_count_same_bus[bus_idx_local] += 1
            else:
                pass

        h: float = float(self.options.time_step)
        sbase: float = float(grid.Sbase)
        fbase: float = float(grid.fBase)

        vsc_idx_dict: Dict[str, int] = dict()
        for vsc_idx, vsc in enumerate(grid.vsc_devices):
            vsc_idx_dict[vsc.idtag] = vsc_idx

        pf_branch_index: int = 0

        for branch_idx, br in enumerate(grid.get_branches_iter(add_vsc=True, add_hvdc=True, add_switch=True)):
            f: int = bus_dict[br.bus_from]
            t: int = bus_dict[br.bus_to]
            br_working_mdl: Block = self._get_or_create_working_emt_model(br)
            # self._working_emt_models[str(br.idtag)] = br_working_mdl

            mdl: Block = self._process_device_model(dev=br, mdl=br_working_mdl, sys_block=sys_block)



            is_bergeron, is_jmarti = _is_history_runtime_line_block_name(mdl.name)

            is_vsc: bool = br.device_type == DeviceType.VscDevice
            uses_branch_pf_slot: bool = br.device_type not in {DeviceType.VscDevice, DeviceType.HVDCLineDevice}
            current_pf_branch_index: int = pf_branch_index
            vsc_index: int = vsc_idx_dict.get(br.idtag, -1)

            if uses_branch_pf_slot:
                pf_branch_index += 1
            else:
                pass

            assign_static_api_object_mapping_for_device(
                grid=grid,
                device=br,
                mdl=mdl,
                problem_mapping=static_parameter_values_mapping,
                logger=self.logger,
            )

            if is_bergeron or is_jmarti:
                v_f_vars: List[Any] = _get_bus_v_list(
                    bus_block=bus_working_models[br.bus_from],
                    ph_v_keys=ph_v_keys
                )
                v_t_vars: List[Any] = _get_bus_v_list(
                    bus_block=bus_working_models[br.bus_to],
                    ph_v_keys=ph_v_keys
                )

                if is_bergeron:
                    rt: BergeronHistoryRuntime | JMartiHistoryRuntime = BergeronHistoryRuntime(
                        line=br,
                        line_block=mdl,
                        h=h,
                        sbase=sbase,
                        fbase=fbase
                    )
                else:
                    rt = JMartiHistoryRuntime(
                        line=br,
                        line_block=mdl,
                        h=h,
                    )
                rt.bind_terminals(v_f_vars, v_t_vars)

                if self.power_flow_results_3ph is not None:
                    if is_bergeron:
                        self._try_set_bergeron_pf_init(
                            mdl=mdl,
                            rt=rt,
                            branch_index=current_pf_branch_index,
                            f_bus_idx=f,
                            t_bus_idx=t,
                            sbase=grid.Sbase,
                        )
                    else:
                        self._try_set_jmarti_pf_init(
                            mdl=mdl,
                            rt=rt,
                            branch_index=current_pf_branch_index,
                            f_bus_idx=f,
                            t_bus_idx=t,
                            sbase=grid.Sbase,
                        )
                else:
                    if self.power_flow_results is not None:
                        if self.options.verbose:
                            if is_bergeron:
                                print("Initializing bergeron line variables assuming a balanced power flow")
                            else:
                                print("Initializing JMARTI line variables assuming a balanced power flow")
                        else:
                            pass

                        if is_bergeron:
                            self._try_set_bergeron_pf_init_balanced(
                                mdl=mdl,
                                rt=rt,
                                branch_index=current_pf_branch_index,
                                f_bus_idx=f,
                                t_bus_idx=t,
                                sbase=grid.Sbase,
                            )
                        else:
                            self._try_set_jmarti_pf_init_balanced(
                                mdl=mdl,
                                rt=rt,
                                branch_index=current_pf_branch_index,
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
                side_current_keys: List[List[VarPowerFlowReferenceType]] = list([br_if_keys, br_it_keys])

                for side_idx in range(2):
                    side_bus_idx: int = side_bus_indices[side_idx]
                    side_bus: Any = side_buses[side_idx]
                    current_keys: List[VarPowerFlowReferenceType] = side_current_keys[side_idx]

                    if side_bus.is_dc:
                        external_mapping_dc: Optional[Dict[Any, Var]] = _get_external_mapping(mdl)
                        dc_current_key: VarPowerFlowReferenceType = (
                            VarPowerFlowReferenceType.If_dc
                            if side_idx == 0
                            else VarPowerFlowReferenceType.It_dc
                        )
                        side_dc_expr: Any | None = None
                        if external_mapping_dc is not None:
                            side_dc_expr = external_mapping_dc.get(dc_current_key, None)
                            if side_dc_expr is None:
                                side_dc_expr = external_mapping_dc.get(VarPowerFlowReferenceType.Idc, None)
                        else:
                            pass
                        if side_dc_expr is not None:
                            I_kcl[side_bus_idx][0] = I_kcl[side_bus_idx][0] - side_dc_expr
                        else:
                            pass
                    else:
                        for ph in range(4):
                            if is_vsc:
                                side_expr: Any | None = _get_external_mapping_var_if_present(mdl=mdl, key=inj_i_keys[ph])
                            else:
                                side_expr = _get_external_mapping_var_if_present(mdl=mdl, key=current_keys[ph])

                            if side_expr is not None:
                                I_kcl[side_bus_idx][ph] = I_kcl[side_bus_idx][ph] - side_expr
                            else:
                                pass

                terminal_buses: List[Any] = list([br.bus_from, br.bus_to])
                terminal_voltage_keys: List[List[VarPowerFlowReferenceType]] = list([br_vf_keys, br_vt_keys])

                for term_idx in range(2):
                    terminal_bus: Any = terminal_buses[term_idx]
                    terminal_keys: List[VarPowerFlowReferenceType] = terminal_voltage_keys[term_idx]
                    external_mapping: Optional[Dict[Any, Var]] = _get_external_mapping(mdl)

                    if terminal_bus.is_dc:
                        v_dc, _, _, _ = get_bus_emt_algebraic_vars(bus_working_models[terminal_bus])

                        if external_mapping is not None:
                            dc_voltage_key: VarPowerFlowReferenceType = (
                                VarPowerFlowReferenceType.Vf_dc
                                if term_idx == 0
                                else VarPowerFlowReferenceType.Vt_dc
                            )
                            mapped_var: Optional[Var] = external_mapping.get(dc_voltage_key, None)
                            if mapped_var is None:
                                mapped_var = external_mapping.get(VarPowerFlowReferenceType.Vdc, None)
                            if mapped_var is not None:
                                mdl.update_model(mapped_var, v_dc)
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
                                    mdl.update_model(mapped_var, terminal_voltage_var)
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
                            branch_index=current_pf_branch_index,
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
                            branch_index=current_pf_branch_index,
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

        # seed store to save the different injections in a bus
        seed_store: Optional[EmtInjectionSeedStore]

        if self.power_flow_results_3ph is not None:
            seed_store = self._build_injection_seed_store_3ph(
                grid=grid,
                bus_dict=bus_dict,
                injection_devices=injection_devices,
                sbase=grid.Sbase,
            )
        else:
            if self.power_flow_results is not None:
                seed_store = self._build_injection_seed_store_balanced(
                    grid=grid,
                    bus_dict=bus_dict,
                    injection_devices=injection_devices,
                    sbase=grid.Sbase,
                )
            else:
                seed_store = None

        for injection_index, inj in enumerate(injection_devices):
            inj_working_mdl: Block = self._get_or_create_working_emt_model(inj)
            mdl: Block = self._process_device_model(dev=inj, mdl=inj_working_mdl, sys_block= sys_block)



            b: int = bus_dict[inj.bus]

            assign_static_api_object_mapping_for_device(
                grid=grid,
                device=inj,
                mdl=mdl,
                problem_mapping=static_parameter_values_mapping,
                logger=self.logger,
            )

            if inj.bus.is_dc:
                i_dc_expr: Any | None = _get_external_mapping_var_if_present(
                    mdl=mdl,
                    key=VarPowerFlowReferenceType.Idc,
                )
                _accumulate_kcl_current(
                    i_kcl=I_kcl,
                    bus_index=b,
                    phase_index=0,
                    current_expression=i_dc_expr,
                    sign=1.0,
                )
            else:
                ph: int = 0
                while ph < 4:
                    i_expr: Any | None = _get_external_mapping_var_if_present(mdl=mdl, key=inj_i_keys[ph])
                    _accumulate_kcl_current(
                        i_kcl=I_kcl,
                        bus_index=b,
                        phase_index=ph,
                        current_expression=i_expr,
                        sign=1.0,
                    )
                    ph += 1

            inj_external_mapping: Optional[Dict[Any, Var]] = _get_external_mapping(mdl)
            inj_bus_mdl: Block = bus_working_models[inj.bus]

            if inj.bus.is_dc:
                v_dc, _, _, _ = get_bus_emt_algebraic_vars(inj_bus_mdl)

                if inj_external_mapping is not None:
                    mapped_var = inj_external_mapping.get(VarPowerFlowReferenceType.Vdc, None)
                    if mapped_var is not None:
                        mdl.update_model(mapped_var, v_dc)
                    else:
                        pass
                else:
                    pass
            else:
                v_n, v_a, v_b, v_c = get_bus_emt_algebraic_vars(inj_bus_mdl)
                inj_bus_voltage_vars: List[Any] = list([v_n, v_a, v_b, v_c])

                if inj_external_mapping is not None:
                    for ph in range(4):
                        mapped_var = inj_external_mapping.get(ph_v_keys[ph], None)
                        inj_bus_voltage_var = inj_bus_voltage_vars[ph]

                        if mapped_var is not None and inj_bus_voltage_var is not None:
                            mdl.update_model(mapped_var, inj_bus_voltage_var)
                        else:
                            pass
                else:
                    pass

            if seed_store is None:
                if self.options.verbose:
                    print("No Power Flow results given.")
                else:
                    pass
            else:
                self._apply_injection_seed(
                    injection=inj,
                    mdl=mdl,
                    bus_index=b,
                    seed_store=seed_store,
                    injection_index=injection_index,
                    generator_count_same_bus=int(generator_count_same_bus[b]),
                )

            if inj.device_type == DeviceType.GeneratorDevice and not inj.bus.is_dc:
                phase_power_seed: np.ndarray = seed_store.get_ac_seed(injection_index)
                generator_count_local: int = int(generator_count_same_bus[b])

                self._assign_generator_sharing_targets_from_seed(
                    inj=inj,
                    mdl=mdl,
                    phase_power=phase_power_seed,
                    generator_count_same_bus=generator_count_local,
                    static_parameter_values_mapping= static_parameter_values_mapping,
                )
            else:
                pass

        for bus_idx, bus in enumerate(grid.buses):
            bus_working_mdl: Block = self._get_or_create_working_emt_model(bus)
            mdl: Block = self._process_device_model(dev=bus, mdl=bus_working_mdl, sys_block= sys_block)

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
            mdl: Block = bus_working_models[bus]
            mdl.algebraic_eqs = list()

            if bus.is_dc:
                v_dc_expr: Any | None = _get_external_mapping_var_if_present(
                    mdl=mdl,
                    key=VarPowerFlowReferenceType.Vdc,
                )
                if v_dc_expr is not None:
                    mdl.algebraic_eqs.append(I_kcl[bus_idx][0])
                else:
                    pass
            else:
                for ph_idx, v_key in enumerate(ph_v_keys):
                    v_expr: Any | None = _get_external_mapping_var_if_present(mdl=mdl, key=v_key)
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
            evt_group: Any = evt.group

            if evt_group is None:
                group_idtag = None
            else:
                group_idtag = evt_group.idtag

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
        device_idtag: Any = evt.device_idtag

        if device_idtag is None:
            event_device_idtag = ""
        else:
            event_device_idtag = str(device_idtag)

        if registered_device_idtag is None:
            return False

        if event_device_idtag == "":
            return True

        return registered_device_idtag == event_device_idtag

    def _resolve_registered_event_parameter_uid(self, evt: Any) -> int | None:
        """
        Resolve the runtime-parameter UID targeted by one EMT event.

        Events are often authored against the reusable device model stored on the
        grid element, while the EMT problem operates on cloned working models with
        fresh symbolic UIDs. This resolver first tries the direct UID match and
        then falls back to ``(device_idtag, parameter.name)`` so the event can be
        applied to the corresponding working-model parameter.

        :param evt: EMT event under inspection.
        :return: Registered runtime-parameter UID or ``None`` when not found.
        """
        if isinstance(evt.parameter, Var):
            direct_uid: int = int(evt.parameter.uid)

            if direct_uid in self._event_parameter_device_idtags:
                return direct_uid
            else:
                pass

            event_device_idtag_raw: Any = evt.device_idtag
            if event_device_idtag_raw is None:
                return None
            else:
                lookup_key: Tuple[str, str] = (str(event_device_idtag_raw), str(evt.parameter.name))
                return self._event_parameter_name_lookup.get(lookup_key, None)
        else:
            return None

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
        continuous_events: Dict[int, List[Dict[str, float | str | None]]] = {
            parameter.uid: list()
            for parameter in self.get_runtime_continuous_parameters()
            if parameter.uid in self._continuous_event_parameter_uids
        }

        emt_events: List[Any] = self._get_emt_events_for_group(emt_events_group)

        for evt in emt_events:
            parameter_uid: int | None = self._resolve_registered_event_parameter_uid(evt)

            if parameter_uid is not None:
                if self._event_targets_registered_parameter(evt, parameter_uid):
                    if parameter_uid in self._discrete_event_parameter_uids:
                        event_list: List[Tuple[float, float, bool]] = scheduled_mode_events.setdefault(
                            parameter_uid,
                            list(),
                        )

                        force_step_alignment: bool = bool(evt.force_step_alignment)

                        event_list.append(
                            (
                                float(evt.time),
                                float(evt.value),
                                force_step_alignment,
                            )
                        )
                    else:
                        if parameter_uid in continuous_events:
                            transition_type: DynamicEventTransitionType = evt.transition_type
                            end_time = evt.end_time

                            continuous_events[parameter_uid].append(
                                dict({
                                    "time": float(evt.time),
                                    "value": float(evt.value),
                                    "end_time": None if end_time is None else float(end_time),
                                    "transition_type": transition_type,
                                })
                            )
                        else:
                            pass
                else:
                    pass
            else:
                pass

        for parameter_uid, event_specs in continuous_events.items():
            if len(event_specs) != 0:
                runtime_idx: int = self.uid2idx_event_params[parameter_uid]
                sorted_specs: List[Dict[str, float | DynamicEventTransitionType | None]] = sorted(
                    event_specs,
                    key=_continuous_event_spec_time_sort_key,
                )
                active_expr: Any = active_runtime_eqs[runtime_idx]
                event_spec: Dict[str, float | DynamicEventTransitionType | None]

                for event_spec in sorted_specs:
                    if event_spec["transition_type"] == DynamicEventTransitionType.Ramp:
                        start_time: float = float(event_spec["time"])
                        end_time_raw: float | str | None = event_spec["end_time"]

                        if end_time_raw is None:
                            raise ValueError("Ramp EMT events require an end_time")
                        else:
                            pass

                        end_time: float = float(end_time_raw)

                        if end_time > start_time:
                            pass
                        else:
                            raise ValueError("Ramp EMT events require end_time greater than time")

                        active_expr = _build_ramp_runtime_expr(
                            time_var=self._glob_time,
                            start_time=start_time,
                            end_time=end_time,
                            before_expr=active_expr,
                            final_value=float(event_spec["value"]),
                        )
                    else:
                        active_expr = piecewise(
                            time_var=self._glob_time,
                            t_events=np.asarray([float(event_spec["time"])], dtype=np.float64),
                            new_values=np.asarray([float(event_spec["value"])], dtype=np.float64),
                            default_value=active_expr,
                        )

                active_runtime_eqs[runtime_idx] = active_expr
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

        # ``active_runtime_eqs`` is already expressed in the flat runtime-vector
        # order used by ``uid2idx_event_params`` and by the solver runtime buffer.
        # Re-splitting it through ``_runtime_all_parameters_source`` would switch
        # back to source-block order and scramble retained mode parameters such as
        # Bergeron history terms. The slices keep the continuous/mode partition
        # aligned with the finalized flat parameter layout.
        runtime_continuous_eqs: List[Any] = list(active_runtime_eqs[self._runtime_continuous_slice])
        runtime_mode_eqs: List[Any] = list(active_runtime_eqs[self._runtime_mode_slice])

        for equation in runtime_continuous_eqs:
            self._runtime_continuous_eqs.append(equation)

        for equation in runtime_mode_eqs:
            self._runtime_mode_eqs.append(equation)

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

    def _rebuild_results_var_name_lookup(self) -> None:
        """
        Rebuild the EMT result-name lookup with unique device-qualified keys.

        ``EmtProblemTemplate`` resets ``_vars_glob_name2uid`` using raw symbolic
        names only. Saved EMT cases often reuse template-local names such as
        ``i_ser_Pi_A`` or repeated load-template names, so the raw-name map drops
        earlier variables. Rebuilding the lookup here preserves one name per UID.

        :return: None.
        """
        unique_names: Dict[str, int] = dict()
        mapped_uids: Set[int] = set()

        device: ALL_DEV_TYPES
        variables: List[Var]
        for device, variables in self._vars_info.items():
            device_idtag: str = str(device.idtag)
            device_name: str = str(device.name)

            for var in variables:
                # Build the preferred global variable name from the symbolic
                # variable name and the owning device public name so the result
                # map stays readable before any duplicate-resolution fallback.
                candidate_name: str = f"{var.name}{device_name}"

                if candidate_name in unique_names and unique_names[candidate_name] != var.uid:
                    candidate_name = f"{candidate_name}{device_idtag}"
                else:
                    pass

                if candidate_name in unique_names and unique_names[candidate_name] != var.uid:
                    candidate_name = f"{candidate_name}{var.uid}"
                else:
                    pass

                unique_names[candidate_name] = var.uid
                mapped_uids.add(var.uid)

        for var in self.state_and_algebraic_vars():
            if var.uid in mapped_uids:
                pass
            else:
                candidate_name = var.name
                if candidate_name in unique_names and unique_names[candidate_name] != var.uid:
                    candidate_name = f"{candidate_name}{var.uid}"
                else:
                    pass

                unique_names[candidate_name] = var.uid
                mapped_uids.add(var.uid)

        for diff_var in self.get_diff_vars():
            if diff_var.uid in mapped_uids:
                pass
            else:
                candidate_name = diff_var.name
                if candidate_name in unique_names and unique_names[candidate_name] != diff_var.uid:
                    candidate_name = f"{candidate_name}{diff_var.uid}"
                else:
                    pass

                unique_names[candidate_name] = diff_var.uid
                mapped_uids.add(diff_var.uid)

        self._vars_glob_name2uid = unique_names

    # ---------------------------------------------------------------------
    # PF INIT
    # ---------------------------------------------------------------------
    def _get_bus_voltage_vector_3ph(self, bus_index: int) -> np.ndarray:
        """
        Return the bus phase-voltage phasors from the three-phase PF result.

        The returned vector is in NABC order.

        :param bus_index: Bus index.
        :return: Complex voltage vector in NABC order.
        """
        voltage_vector: np.ndarray = np.zeros(4, dtype=np.complex128)

        if self.power_flow_results_3ph is None:
            pass
        else:
            voltage_vector[0] = complex(self.power_flow_results_3ph.voltage_N[bus_index])
            voltage_vector[1] = complex(self.power_flow_results_3ph.voltage_A[bus_index])
            voltage_vector[2] = complex(self.power_flow_results_3ph.voltage_B[bus_index])
            voltage_vector[3] = complex(self.power_flow_results_3ph.voltage_C[bus_index])

        return voltage_vector

    def _get_bus_voltage_vector_balanced(self, bus_index: int) -> np.ndarray:
        """
        Reconstruct balanced bus phase-voltage phasors in NABC order.

        :param bus_index: Bus index.
        :return: Complex voltage vector in NABC order.
        """
        voltage_vector: np.ndarray = np.zeros(4, dtype=np.complex128)

        if self.power_flow_results is None:
            pass
        else:
            bus_voltage: complex = complex(self.power_flow_results.voltage[bus_index])
            voltage_vector[0] = 0.0 + 0.0j
            voltage_vector[1] = bus_voltage
            voltage_vector[2] = bus_voltage * _phase_sequence_shift(2)
            voltage_vector[3] = bus_voltage * _phase_sequence_shift(3)

        return voltage_vector

    def _get_load_fixed_power_vector_3ph(self, load: Any) -> np.ndarray:
        """
        Return the fixed per-phase complex power seed of a three-phase load.

        The EMT sign convention used here is injection-oriented, hence loads are
        represented as negative power injections.

        :param load: Load device.
        :return: Complex power vector in NABC order.
        """
        phase_p_pu_abc: np.ndarray
        phase_q_pu_abc: np.ndarray
        phase_p_pu_nabc: np.ndarray
        phase_q_pu_nabc: np.ndarray
        power_vector: np.ndarray = _zero_ac_power_vector()

        # Three-phase PF seeds must still tolerate balanced static-device data.
        # Reuse the same explicit-or-balanced resolution as the generic static
        # parameter mapper so seeded per-phase powers stay consistent.
        phase_p_pu_abc, phase_q_pu_abc = get_load_power_phase_values_pu_abc(load=load, grid=self.grid)
        phase_p_pu_nabc = abc_to_nabc(phase_values_abc=phase_p_pu_abc)
        phase_q_pu_nabc = abc_to_nabc(phase_values_abc=phase_q_pu_abc)

        power_vector[0] = 0.0 + 0.0j
        power_vector[1] = complex(-float(phase_p_pu_nabc[1]), -float(phase_q_pu_nabc[1]))
        power_vector[2] = complex(-float(phase_p_pu_nabc[2]), -float(phase_q_pu_nabc[2]))
        power_vector[3] = complex(-float(phase_p_pu_nabc[3]), -float(phase_q_pu_nabc[3]))

        return power_vector

    @staticmethod
    def _get_load_fixed_power_vector_balanced(load: Any, sbase: float) -> np.ndarray:
        """
        Return the balanced per-phase complex power seed of a load.

        :param load: Load device.
        :param sbase: System base power.
        :return: Complex power vector in NABC order.
        """
        power_vector: np.ndarray = _zero_ac_power_vector()
        p_phase: float = float(load.P) / (3.0 * sbase)
        q_phase: float = float(load.Q) / (3.0 * sbase)

        power_vector[0] = 0.0 + 0.0j
        power_vector[1] = complex(-p_phase, -q_phase)
        power_vector[2] = complex(-p_phase, -q_phase)
        power_vector[3] = complex(-p_phase, -q_phase)

        return power_vector

    def _get_shunt_fixed_power_vector_3ph(
            self,
            shunt: Any,
            bus_index: int,
    ) -> np.ndarray:
        """
        Return the fixed per-phase complex power seed of a shunt.

        The current EMT implementation only has direct access to total ``G`` and ``B``
        in this parser stage. Therefore, the total shunt admittance is split equally
        among phases for initialization purposes.

        :param shunt: Shunt device.
        :param bus_index: Bus index.
        :return: Complex power vector in NABC order.
        """
        voltage_vector: np.ndarray = self._get_bus_voltage_vector_3ph(bus_index)
        power_vector: np.ndarray = _zero_ac_power_vector()
        g_phase_abc_pu: np.ndarray
        b_phase_abc_pu: np.ndarray
        g_phase_nabc_pu: np.ndarray
        b_phase_nabc_pu: np.ndarray
        phase_index: int = 1

        # Three-phase PF seeds must preserve explicit per-phase shunt data when it
        # exists, but they must also derive phase values from balanced totals when
        # the static device only carries positive-sequence quantities.
        g_phase_abc_pu, b_phase_abc_pu = get_shunt_phase_values_pu_abc(shunt=shunt, grid=self.grid)
        g_phase_nabc_pu = abc_to_nabc(phase_values_abc=g_phase_abc_pu)
        b_phase_nabc_pu = abc_to_nabc(phase_values_abc=b_phase_abc_pu)

        power_vector[0] = 0.0 + 0.0j

        while phase_index < 4:
            phase_voltage: complex = complex(voltage_vector[phase_index])
            voltage_square: float = float(np.abs(phase_voltage) ** 2)

            power_vector[phase_index] = complex(
                float(g_phase_nabc_pu[phase_index]) * voltage_square,
                -float(b_phase_nabc_pu[phase_index]) * voltage_square,
            )
            phase_index += 1

        return power_vector

    def _get_shunt_fixed_power_vector_balanced(
            self,
            shunt: Any,
            bus_index: int,
            sbase: float,
    ) -> np.ndarray:
        """
        Return the balanced per-phase complex power seed of a shunt.

        :param shunt: Shunt device.
        :param bus_index: Bus index.
        :param sbase: System base power.
        :return: Complex power vector in NABC order.
        """
        voltage_vector: np.ndarray = self._get_bus_voltage_vector_balanced(bus_index)
        power_vector: np.ndarray = _zero_ac_power_vector()
        g_phase: float = float(shunt.G) / (3.0 * sbase)
        b_phase: float = float(shunt.B) / (3.0 * sbase)
        phase_index: int = 1

        power_vector[0] = 0.0 + 0.0j

        while phase_index < 4:
            phase_voltage: complex = complex(voltage_vector[phase_index])
            voltage_square: float = float(np.abs(phase_voltage) ** 2)

            power_vector[phase_index] = complex(
                g_phase * voltage_square,
                -b_phase * voltage_square,
            )
            phase_index += 1

        return power_vector

    def _build_injection_seed_store_3ph(
            self,
            grid: MultiCircuit,
            bus_dict: Dict[Any, int],
            injection_devices: List[Any],
            sbase: float,
    ) -> EmtInjectionSeedStore:
        """
        Build the PF seed store for EMT injections using the three-phase PF snapshot.

        The algorithm mirrors the RMS logic:
        1. loads and shunts contribute fixed known power injections,
        2. the remaining bus power is treated as residual,
        3. the residual is distributed among source-like injections on the same bus.

        The result is one per-device seed, which is exactly what the current EMT
        code is missing when multiple injections share the same bus.

        :param grid: Network model.
        :param bus_dict: Bus-to-index lookup.
        :param injection_devices: Fixed injection list used by the EMT builder.
        :param sbase: System base power.
        :return: Preallocated seed store.
        """
        n_buses: int = len(grid.buses)
        n_injections: int = len(injection_devices)

        seed_store: EmtInjectionSeedStore = EmtInjectionSeedStore(n_injections)

        # The target bus powers come from the PF solution and are stored phase by phase.
        target_ac_power: np.ndarray = np.zeros((n_buses, 4), dtype=np.complex128)
        fixed_ac_power: np.ndarray = np.zeros((n_buses, 4), dtype=np.complex128)

        # DC buses use one real power residual only.
        target_dc_power: np.ndarray = np.zeros(n_buses, dtype=np.float64)
        fixed_dc_power: np.ndarray = np.zeros(n_buses, dtype=np.float64)

        # These matrices store which injections must absorb the residual.
        source_indices_ac: np.ndarray = -np.ones((n_buses, n_injections), dtype=np.int64)
        source_counts_ac: np.ndarray = np.zeros(n_buses, dtype=np.int64)

        source_indices_dc: np.ndarray = -np.ones((n_buses, n_injections), dtype=np.int64)
        source_counts_dc: np.ndarray = np.zeros(n_buses, dtype=np.int64)

        load_lookup: Dict[str, int] = _build_device_idtag_lookup(grid.loads)
        shunt_lookup: Dict[str, int] = _build_device_idtag_lookup(grid.shunts)

        bus_index: int = 0
        while bus_index < n_buses:
            if grid.buses[bus_index].is_dc:
                if self.power_flow_results is None:
                    target_dc_power[bus_index] = 0.0
                else:
                    target_dc_power[bus_index] = float(np.real(self.power_flow_results.Sbus[bus_index] / sbase))
            else:
                target_ac_power[bus_index, 0] = complex(self.power_flow_results_3ph.Sbus_N[bus_index] / sbase)
                target_ac_power[bus_index, 1] = complex(self.power_flow_results_3ph.Sbus_A[bus_index] / sbase)
                target_ac_power[bus_index, 2] = complex(self.power_flow_results_3ph.Sbus_B[bus_index] / sbase)
                target_ac_power[bus_index, 3] = complex(self.power_flow_results_3ph.Sbus_C[bus_index] / sbase)
            bus_index += 1

        injection_index: int = 0
        while injection_index < n_injections:
            injection: Any = injection_devices[injection_index]
            bus_index = int(bus_dict[injection.bus])

            if injection.bus.is_dc:
                # Loads are fixed DC consumers. All other DC injections are treated as source-like.
                if injection.idtag in load_lookup:
                    fixed_power_dc: float = -float(injection.P) / sbase
                    fixed_dc_power[bus_index] += fixed_power_dc
                    seed_store.set_dc_seed(injection_index, fixed_power_dc)
                else:
                    row_index_dc: int = int(source_counts_dc[bus_index])
                    source_indices_dc[bus_index, row_index_dc] = injection_index
                    source_counts_dc[bus_index] += 1
            else:
                if injection.idtag in load_lookup:
                    fixed_power_ac: np.ndarray = self._get_load_fixed_power_vector_3ph(injection)
                    fixed_ac_power[bus_index, :] += fixed_power_ac
                    seed_store.set_ac_seed(injection_index, fixed_power_ac)
                else:
                    if injection.idtag in shunt_lookup:
                        fixed_power_ac = self._get_shunt_fixed_power_vector_3ph(injection, bus_index)
                        fixed_ac_power[bus_index, :] += fixed_power_ac
                        seed_store.set_ac_seed(injection_index, fixed_power_ac)
                    else:
                        row_index_ac: int = int(source_counts_ac[bus_index])
                        source_indices_ac[bus_index, row_index_ac] = injection_index
                        source_counts_ac[bus_index] += 1
            injection_index += 1

        bus_index = 0
        while bus_index < n_buses:
            if grid.buses[bus_index].is_dc:
                residual_dc: float = float(target_dc_power[bus_index] - fixed_dc_power[bus_index])
                source_count_dc: int = int(source_counts_dc[bus_index])

                if source_count_dc == 0:
                    if abs(residual_dc) > 1.0e-9:
                        self.logger.add_warning(
                            msg="DC EMT injection residual could not be assigned.",
                            device="EmtProblemDae",
                            value=f"bus_index={bus_index}, residual={residual_dc}",
                            expected_value="At least one source-like DC injection",
                            device_class="EMT",
                            device_property="injection_seed_store_3ph",
                        )
                    else:
                        pass
                else:
                    total_weight_dc: float = 0.0
                    source_row_index_dc: int = 0

                    while source_row_index_dc < source_count_dc:
                        injection_index = int(source_indices_dc[bus_index, source_row_index_dc])
                        total_weight_dc += _get_source_seed_weight(injection_devices[injection_index])
                        source_row_index_dc += 1

                    remaining_weight_dc: float = total_weight_dc
                    remaining_residual_dc: float = residual_dc
                    source_row_index_dc = 0

                    while source_row_index_dc < source_count_dc:
                        injection_index = int(source_indices_dc[bus_index, source_row_index_dc])

                        if source_row_index_dc == source_count_dc - 1:
                            allocated_dc: float = remaining_residual_dc
                        else:
                            weight_dc: float = _get_source_seed_weight(injection_devices[injection_index])

                            if remaining_weight_dc > 0.0:
                                share_dc: float = weight_dc / remaining_weight_dc
                            else:
                                share_dc = 1.0 / float(source_count_dc - source_row_index_dc)

                            allocated_dc = remaining_residual_dc * share_dc
                            remaining_residual_dc -= allocated_dc
                            remaining_weight_dc -= weight_dc

                        seed_store.set_dc_seed(injection_index, allocated_dc)
                        source_row_index_dc += 1
            else:
                residual_ac: np.ndarray = target_ac_power[bus_index, :] - fixed_ac_power[bus_index, :]
                source_count_ac: int = int(source_counts_ac[bus_index])

                if source_count_ac == 0:
                    if np.max(np.abs(residual_ac)) > 1.0e-9:
                        self.logger.add_warning(
                            msg="AC EMT injection residual could not be assigned.",
                            device="EmtProblemDae",
                            value=f"bus_index={bus_index}, residual={residual_ac}",
                            expected_value="At least one source-like AC injection",
                            device_class="EMT",
                            device_property="injection_seed_store_3ph",
                        )
                    else:
                        pass
                else:
                    total_weight_ac: float = 0.0
                    source_row_index_ac: int = 0

                    while source_row_index_ac < source_count_ac:
                        injection_index = int(source_indices_ac[bus_index, source_row_index_ac])
                        total_weight_ac += _get_source_seed_weight(injection_devices[injection_index])
                        source_row_index_ac += 1

                    remaining_weight_ac: float = total_weight_ac
                    remaining_residual_ac: np.ndarray = residual_ac.copy()
                    source_row_index_ac = 0

                    while source_row_index_ac < source_count_ac:
                        injection_index = int(source_indices_ac[bus_index, source_row_index_ac])

                        if source_row_index_ac == source_count_ac - 1:
                            allocated_ac: np.ndarray = remaining_residual_ac.copy()
                        else:
                            weight_ac: float = _get_source_seed_weight(injection_devices[injection_index])

                            if remaining_weight_ac > 0.0:
                                share_ac: float = weight_ac / remaining_weight_ac
                            else:
                                share_ac = 1.0 / float(source_count_ac - source_row_index_ac)

                            allocated_ac = remaining_residual_ac * share_ac
                            remaining_residual_ac = remaining_residual_ac - allocated_ac
                            remaining_weight_ac -= weight_ac

                        seed_store.set_ac_seed(injection_index, allocated_ac)
                        source_row_index_ac += 1
            bus_index += 1

        return seed_store

    def _build_injection_seed_store_balanced(
            self,
            grid: MultiCircuit,
            bus_dict: Dict[Any, int],
            injection_devices: List[Any],
            sbase: float,
    ) -> EmtInjectionSeedStore:
        """
        Build the PF seed store for EMT injections using the balanced PF snapshot.

        The balanced PF gives one three-phase complex bus injection. This function
        converts it into balanced ABC phase powers and then applies the same
        residual-allocation logic as the three-phase version.

        :param grid: Network model.
        :param bus_dict: Bus-to-index lookup.
        :param injection_devices: Fixed injection list used by the EMT builder.
        :param sbase: System base power.
        :return: Preallocated seed store.
        """
        n_buses: int = len(grid.buses)
        n_injections: int = len(injection_devices)

        seed_store: EmtInjectionSeedStore = EmtInjectionSeedStore(n_injections)

        target_ac_power: np.ndarray = np.zeros((n_buses, 4), dtype=np.complex128)
        fixed_ac_power: np.ndarray = np.zeros((n_buses, 4), dtype=np.complex128)

        target_dc_power: np.ndarray = np.zeros(n_buses, dtype=np.float64)
        fixed_dc_power: np.ndarray = np.zeros(n_buses, dtype=np.float64)

        source_indices_ac: np.ndarray = -np.ones((n_buses, n_injections), dtype=np.int64)
        source_counts_ac: np.ndarray = np.zeros(n_buses, dtype=np.int64)

        source_indices_dc: np.ndarray = -np.ones((n_buses, n_injections), dtype=np.int64)
        source_counts_dc: np.ndarray = np.zeros(n_buses, dtype=np.int64)

        load_lookup: Dict[str, int] = _build_device_idtag_lookup(grid.loads)
        shunt_lookup: Dict[str, int] = _build_device_idtag_lookup(grid.shunts)

        bus_index: int = 0
        while bus_index < n_buses:
            if grid.buses[bus_index].is_dc:
                if self.power_flow_results is None:
                    target_dc_power[bus_index] = 0.0
                else:
                    target_dc_power[bus_index] = float(np.real(self.power_flow_results.Sbus[bus_index] / sbase))
            else:
                bus_power: complex = complex(self.power_flow_results.Sbus[bus_index] / sbase)
                phase_power: complex = bus_power / 3.0

                target_ac_power[bus_index, 0] = 0.0 + 0.0j
                target_ac_power[bus_index, 1] = phase_power
                target_ac_power[bus_index, 2] = phase_power
                target_ac_power[bus_index, 3] = phase_power
            bus_index += 1

        injection_index: int = 0
        while injection_index < n_injections:
            injection: Any = injection_devices[injection_index]
            bus_index = int(bus_dict[injection.bus])

            if injection.bus.is_dc:
                if injection.idtag in load_lookup:
                    fixed_power_dc: float = -float(injection.P) / sbase
                    fixed_dc_power[bus_index] += fixed_power_dc
                    seed_store.set_dc_seed(injection_index, fixed_power_dc)
                else:
                    row_index_dc: int = int(source_counts_dc[bus_index])
                    source_indices_dc[bus_index, row_index_dc] = injection_index
                    source_counts_dc[bus_index] += 1
            else:
                if injection.idtag in load_lookup:
                    fixed_power_ac: np.ndarray = self._get_load_fixed_power_vector_balanced(injection, sbase)
                    fixed_ac_power[bus_index, :] += fixed_power_ac
                    seed_store.set_ac_seed(injection_index, fixed_power_ac)
                else:
                    if injection.idtag in shunt_lookup:
                        fixed_power_ac = self._get_shunt_fixed_power_vector_balanced(injection, bus_index, sbase)
                        fixed_ac_power[bus_index, :] += fixed_power_ac
                        seed_store.set_ac_seed(injection_index, fixed_power_ac)
                    else:
                        row_index_ac: int = int(source_counts_ac[bus_index])
                        source_indices_ac[bus_index, row_index_ac] = injection_index
                        source_counts_ac[bus_index] += 1
            injection_index += 1

        bus_index = 0
        while bus_index < n_buses:
            if grid.buses[bus_index].is_dc:
                residual_dc: float = float(target_dc_power[bus_index] - fixed_dc_power[bus_index])
                source_count_dc: int = int(source_counts_dc[bus_index])

                if source_count_dc == 0:
                    if abs(residual_dc) > 1.0e-9:
                        self.logger.add_warning(
                            msg="Balanced DC EMT injection residual could not be assigned.",
                            device="EmtProblemDae",
                            value=f"bus_index={bus_index}, residual={residual_dc}",
                            expected_value="At least one source-like DC injection",
                            device_class="EMT",
                            device_property="injection_seed_store_balanced",
                        )
                    else:
                        pass
                else:
                    total_weight_dc: float = 0.0
                    source_row_index_dc: int = 0

                    while source_row_index_dc < source_count_dc:
                        injection_index = int(source_indices_dc[bus_index, source_row_index_dc])
                        total_weight_dc += _get_source_seed_weight(injection_devices[injection_index])
                        source_row_index_dc += 1

                    remaining_weight_dc: float = total_weight_dc
                    remaining_residual_dc: float = residual_dc
                    source_row_index_dc = 0

                    while source_row_index_dc < source_count_dc:
                        injection_index = int(source_indices_dc[bus_index, source_row_index_dc])

                        if source_row_index_dc == source_count_dc - 1:
                            allocated_dc: float = remaining_residual_dc
                        else:
                            weight_dc: float = _get_source_seed_weight(injection_devices[injection_index])

                            if remaining_weight_dc > 0.0:
                                share_dc: float = weight_dc / remaining_weight_dc
                            else:
                                share_dc = 1.0 / float(source_count_dc - source_row_index_dc)

                            allocated_dc = remaining_residual_dc * share_dc
                            remaining_residual_dc -= allocated_dc
                            remaining_weight_dc -= weight_dc

                        seed_store.set_dc_seed(injection_index, allocated_dc)
                        source_row_index_dc += 1
            else:
                residual_ac: np.ndarray = target_ac_power[bus_index, :] - fixed_ac_power[bus_index, :]
                source_count_ac: int = int(source_counts_ac[bus_index])

                if source_count_ac == 0:
                    if np.max(np.abs(residual_ac)) > 1.0e-9:
                        self.logger.add_warning(
                            msg="Balanced AC EMT injection residual could not be assigned.",
                            device="EmtProblemDae",
                            value=f"bus_index={bus_index}, residual={residual_ac}",
                            expected_value="At least one source-like AC injection",
                            device_class="EMT",
                            device_property="injection_seed_store_balanced",
                        )
                    else:
                        pass
                else:
                    total_weight_ac: float = 0.0
                    source_row_index_ac: int = 0

                    while source_row_index_ac < source_count_ac:
                        injection_index = int(source_indices_ac[bus_index, source_row_index_ac])
                        total_weight_ac += _get_source_seed_weight(injection_devices[injection_index])
                        source_row_index_ac += 1

                    remaining_weight_ac: float = total_weight_ac
                    remaining_residual_ac: np.ndarray = residual_ac.copy()
                    source_row_index_ac = 0

                    while source_row_index_ac < source_count_ac:
                        injection_index = int(source_indices_ac[bus_index, source_row_index_ac])

                        if source_row_index_ac == source_count_ac - 1:
                            allocated_ac: np.ndarray = remaining_residual_ac.copy()
                        else:
                            weight_ac: float = _get_source_seed_weight(injection_devices[injection_index])

                            if remaining_weight_ac > 0.0:
                                share_ac: float = weight_ac / remaining_weight_ac
                            else:
                                share_ac = 1.0 / float(source_count_ac - source_row_index_ac)

                            allocated_ac = remaining_residual_ac * share_ac
                            remaining_residual_ac = remaining_residual_ac - allocated_ac
                            remaining_weight_ac -= weight_ac

                        seed_store.set_ac_seed(injection_index, allocated_ac)
                        source_row_index_ac += 1
            bus_index += 1

        return seed_store

    def _apply_injection_seed(
            self,
            injection: Any,
            mdl: Block,
            bus_index: int,
            seed_store: EmtInjectionSeedStore,
            injection_index: int,
            generator_count_same_bus: int,
    ) -> None:
        """
        Apply the precomputed PF seed of one injection into the EMT model.

        This replaces the old logic that initialized each injection directly from
        ``Sbus`` of the bus. That old logic is only valid when there is exactly one
        injection device on the bus.

        :param injection: Injection device.
        :param mdl: Injection symbolic block.
        :param bus_index: Bus index.
        :param seed_store: Precomputed seed store.
        :param injection_index: Injection position in the fixed injection list.
        :return: None.
        """
        if seed_store.has_seed(injection_index):
            pass
        else:
            return

        if injection.bus.is_dc:
            if self.power_flow_results is None:
                pass
            else:
                power_dc: float = seed_store.get_dc_seed(injection_index)
                voltage_dc: float = float(np.abs(self.power_flow_results.voltage[bus_index]))

                self.set_init_guess(
                    mdl=mdl,
                    reference_powerflow=VarPowerFlowReferenceType.P,
                    val=power_dc,
                )

                if abs(voltage_dc) > 1.0e-12:
                    self.set_if_exists(
                        mdl=mdl,
                        key=VarPowerFlowReferenceType.Idc,
                        value=power_dc / voltage_dc,
                    )
                else:
                    self.set_if_exists(
                        mdl=mdl,
                        key=VarPowerFlowReferenceType.Idc,
                        value=0.0,
                    )
        else:
            phase_power: np.ndarray = seed_store.get_ac_seed(injection_index)
            phase_current_vector: np.ndarray = np.zeros(4, dtype=np.complex128)
            preserve_generator_current_seed: bool

            if self.power_flow_results_3ph is None:
                voltage_vector: np.ndarray = self._get_bus_voltage_vector_balanced(bus_index)
            else:
                voltage_vector = self._get_bus_voltage_vector_3ph(bus_index)

            if injection.device_type == DeviceType.GeneratorDevice and generator_count_same_bus <= 1:
                preserve_generator_current_seed = False
            else:
                preserve_generator_current_seed = True

            phase_index: int = 0
            p_total: float = 0.0
            q_total: float = 0.0

            current_keys: List[VarPowerFlowReferenceType] = list([
                VarPowerFlowReferenceType.i_N,
                VarPowerFlowReferenceType.i_A,
                VarPowerFlowReferenceType.i_B,
                VarPowerFlowReferenceType.i_C,
            ])
            active_power_keys: List[VarPowerFlowReferenceType] = list([
                VarPowerFlowReferenceType.P_N,
                VarPowerFlowReferenceType.P_A,
                VarPowerFlowReferenceType.P_B,
                VarPowerFlowReferenceType.P_C,
            ])
            reactive_power_keys: List[VarPowerFlowReferenceType] = list([
                VarPowerFlowReferenceType.Q_N,
                VarPowerFlowReferenceType.Q_A,
                VarPowerFlowReferenceType.Q_B,
                VarPowerFlowReferenceType.Q_C,
            ])

            while phase_index < 4:
                phase_voltage: complex = complex(voltage_vector[phase_index])
                phase_complex_power: complex = complex(phase_power[phase_index])

                if abs(phase_voltage) > 1.0e-12:
                    phase_current: complex = np.conj(phase_complex_power / phase_voltage)
                else:
                    phase_current = 0.0 + 0.0j

                phase_current_vector[phase_index] = phase_current
                current_instantaneous: float = float(np.sqrt(2.0) * np.imag(phase_current))

                self.set_if_exists(
                    mdl=mdl,
                    key=current_keys[phase_index],
                    value=current_instantaneous,
                    persist_after_native_init=preserve_generator_current_seed,
                )
                self.set_if_exists(
                    mdl=mdl,
                    key=active_power_keys[phase_index],
                    value=float(np.real(phase_complex_power)),
                )
                self.set_if_exists(
                    mdl=mdl,
                    key=reactive_power_keys[phase_index],
                    value=float(np.imag(phase_complex_power)),
                )

                p_total += float(np.real(phase_complex_power))
                q_total += float(np.imag(phase_complex_power))
                phase_index += 1

            if injection.device_type == DeviceType.GeneratorDevice:
                self._set_vsc_pf_positive_sequence(
                    mdl=mdl,
                    VA=complex(voltage_vector[1]),
                    VB=complex(voltage_vector[2]),
                    VC=complex(voltage_vector[3]),
                    IA=complex(phase_current_vector[1]),
                    IB=complex(phase_current_vector[2]),
                    IC=complex(phase_current_vector[3]),
                )
            else:
                pass

            neutral_var = _get_external_mapping_var_if_present(
                mdl=mdl,
                key=VarPowerFlowReferenceType.i_N,
            )
            if neutral_var is not None:
                ia_var = _get_external_mapping_var_if_present(mdl=mdl, key=VarPowerFlowReferenceType.i_A)
                ib_var = _get_external_mapping_var_if_present(mdl=mdl, key=VarPowerFlowReferenceType.i_B)
                ic_var = _get_external_mapping_var_if_present(mdl=mdl, key=VarPowerFlowReferenceType.i_C)
                if ia_var is None and ib_var is None and ic_var is None:
                    pass
                else:
                    ia_inst = self._temp_init_guess.get(ia_var.uid, 0.0) if ia_var is not None else 0.0
                    ib_inst = self._temp_init_guess.get(ib_var.uid, 0.0) if ib_var is not None else 0.0
                    ic_inst = self._temp_init_guess.get(ic_var.uid, 0.0) if ic_var is not None else 0.0
                    neutral_inst = -(ia_inst + ib_inst + ic_inst)
                    self._temp_init_guess[neutral_var.uid] = float(neutral_inst)
                    self._temp_post_init_guess[neutral_var.uid] = float(neutral_inst)
            else:
                pass

            self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.P, value=p_total)
            self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Q, value=q_total)

            # The Thevenin generator templates reconstruct an internal balanced emf
            # from the PF seed. Those internal variables are not externally mapped,
            # so they must be preserved explicitly across the later native-init pass.
            if injection.device_type == DeviceType.GeneratorDevice and generator_count_same_bus > 1:
                self._seed_thevenin_internal_emf_from_pf(
                    injection=injection,
                    mdl=mdl,
                    phase_power=phase_power,
                    voltage_vector=voltage_vector,
                )
            else:
                pass

            omega_base: float = 2.0 * np.pi * self.grid.fBase
            voltage_derivative_keys: List[VarPowerFlowReferenceType] = list([
                VarPowerFlowReferenceType.d_v_N,
                VarPowerFlowReferenceType.d_v_A,
                VarPowerFlowReferenceType.d_v_B,
                VarPowerFlowReferenceType.d_v_C,
            ])

            phase_index = 0
            while phase_index < 4:
                derivative_key: VarPowerFlowReferenceType = voltage_derivative_keys[phase_index]
                derivative_var: Optional[Any] = _get_external_mapping_var_if_present(mdl=mdl, key=derivative_key)
                if derivative_var is not None:
                    phase_voltage = complex(voltage_vector[phase_index])
                    derivative_value: float = omega_base * np.sqrt(2.0) * float(np.real(phase_voltage))
                    self.set_external_param(mdl, derivative_key, derivative_value)
                else:
                    pass
                phase_index += 1

    def _seed_thevenin_internal_emf_from_pf(
            self,
            injection: Any,
            mdl: Block,
            phase_power: np.ndarray,
            voltage_vector: np.ndarray,
    ) -> None:
        """
        Preserve the PF-consistent internal emf initialization of Thevenin generators.

        The Thevenin templates expose ``theta`` and ``e_A/e_B/e_C`` only as internal
        symbolic variables. The generic native EMT initialization can overwrite those
        exact explicit-init values with weaker guesses because they are not part of
        the external PF mapping. This helper reconstructs the same balanced emf from
        the already available PF seed and stores it as a post-native-init value.

        The helper is intentionally no-op for non-Thevenin generator models because
        the required internal variable names will simply be absent.

        :param injection: Generator device under initialization.
        :param mdl: Working EMT model of the generator.
        :param phase_power: Complex power seed in NABC order.
        :param voltage_vector: Complex bus-voltage seed in NABC order.
        :return: None.
        """
        c_sqrt_2: float = float(np.sqrt(2.0))
        phase_a: complex = complex(voltage_vector[1])
        phase_b: complex = complex(voltage_vector[2])
        phase_c: complex = complex(voltage_vector[3])
        power_a: complex = complex(phase_power[1])
        power_b: complex = complex(phase_power[2])
        power_c: complex = complex(phase_power[3])
        a_operator: complex = np.exp(1j * 2.0 * np.pi / 3.0)
        current_a: complex
        current_b: complex
        current_c: complex

        if abs(phase_a) > 1.0e-12:
            current_a = np.conj(power_a / phase_a)
        else:
            current_a = 0.0 + 0.0j

        if abs(phase_b) > 1.0e-12:
            current_b = np.conj(power_b / phase_b)
        else:
            current_b = 0.0 + 0.0j

        if abs(phase_c) > 1.0e-12:
            current_c = np.conj(power_c / phase_c)
        else:
            current_c = 0.0 + 0.0j

        # The positive-sequence phasors define the same operating point used by the
        # explicit-init equations inside the Thevenin template.
        voltage_positive_sequence: complex = (
            phase_a + a_operator * phase_b + (a_operator * a_operator) * phase_c
        ) / 3.0
        current_positive_sequence: complex = (
            current_a + a_operator * current_b + (a_operator * a_operator) * current_c
        ) / 3.0
        phi_v: float = float(np.angle(voltage_positive_sequence))
        phi_i: float = float(np.angle(current_positive_sequence))
        phi_rel_raw: float = float(phi_i - phi_v)
        phi_rel: float = float(np.arctan2(np.sin(phi_rel_raw), np.cos(phi_rel_raw)))
        voltage_peak: float = float(c_sqrt_2 * np.abs(voltage_positive_sequence))
        current_peak: float = float(c_sqrt_2 * np.abs(current_positive_sequence))
        resistance_s: float = float(injection.R1)
        reactance_s: float = float(injection.X1)

        # The internal emf is built in the local frame first and then rotated back
        # to the absolute electrical angle used by the abc sinusoidal source.
        e_re_rel: float = float(
            voltage_peak
            + resistance_s * current_peak * np.cos(phi_rel)
            - reactance_s * current_peak * np.sin(phi_rel)
        )
        e_im_rel: float = float(
            resistance_s * current_peak * np.sin(phi_rel)
            + reactance_s * current_peak * np.cos(phi_rel)
        )
        theta_abs: float = float(phi_v + np.arctan2(e_im_rel, e_re_rel))
        emf_peak: float = float(np.sqrt(e_re_rel * e_re_rel + e_im_rel * e_im_rel))
        e_a_value: float = float(emf_peak * np.sin(theta_abs))
        e_b_value: float = float(emf_peak * np.sin(theta_abs - 2.0 * np.pi / 3.0))
        e_c_value: float = float(emf_peak * np.sin(theta_abs + 2.0 * np.pi / 3.0))

        # The recent Thevenin refactor moved the internal emf reconstruction to
        # algebraic equations driven by init-only runtime parameters. Explicit
        # initialization resolves those parameters correctly, but the later
        # event-group activation rebuilds the runtime-parameter vector from the
        # model-owned ``event_dict`` definitions. Persisting the PF-derived
        # positive-sequence values here keeps the first simulation step aligned
        # with the exact steady-state source used by explicit initialization.
        self.set_internal_runtime_if_exists(mdl=mdl, var_name="phi_v_" + mdl.name, value=phi_v)
        self.set_internal_runtime_if_exists(mdl=mdl, var_name="phi_" + mdl.name, value=phi_rel)
        self.set_internal_runtime_if_exists(mdl=mdl, var_name="Vpk_" + mdl.name, value=voltage_peak)
        self.set_internal_runtime_if_exists(mdl=mdl, var_name="Ipk_" + mdl.name, value=current_peak)

        theta_var: Optional[Var] = _find_internal_var_by_prefix(mdl, "theta_")
        e_a_var: Optional[Var] = _find_internal_var_by_prefix(mdl, "e_A_")
        e_b_var: Optional[Var] = _find_internal_var_by_prefix(mdl, "e_B_")
        e_c_var: Optional[Var] = _find_internal_var_by_prefix(mdl, "e_C_")

        # The preserved guesses are written directly into both init dictionaries so
        # the later native-init pass starts from the PF-consistent emf and the final
        # post-native state keeps the same values.
        if theta_var is not None:
            self._temp_init_guess[theta_var.uid] = theta_abs
            self._temp_post_init_guess[theta_var.uid] = theta_abs
        else:
            pass

        if e_a_var is not None:
            self._temp_init_guess[e_a_var.uid] = e_a_value
            self._temp_post_init_guess[e_a_var.uid] = e_a_value
        else:
            pass

        if e_b_var is not None:
            self._temp_init_guess[e_b_var.uid] = e_b_value
            self._temp_post_init_guess[e_b_var.uid] = e_b_value
        else:
            pass

        if e_c_var is not None:
            self._temp_init_guess[e_c_var.uid] = e_c_value
            self._temp_post_init_guess[e_c_var.uid] = e_c_value
        else:
            pass




    def _try_set_bus_pf_init(self, bus: Bus,
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
                self.set_init_guess_and_preserve_post_init(
                    mdl,
                    VarPowerFlowReferenceType.Vdc,
                    float(np.abs(self.power_flow_results.voltage[bus_index]))
                )
            else:
                raise ValueError(f"EMT simulation with DC branches requires the non unbalanced PowerFlow to be calculated.")

        else:

            if _get_external_mapping_var_if_present(mdl=mdl, key=VarPowerFlowReferenceType.v_N) is not None:
                V_N = self.power_flow_results_3ph.voltage_N[bus_index]
                v_N: float = np.sqrt(2.0) * np.imag(V_N)
                d_v_N: float = omega_base * np.sqrt(2.0) * np.real(V_N)

                self.set_init_guess_and_preserve_post_init(mdl, VarPowerFlowReferenceType.v_N, v_N)
                self.set_diff_init_guess(mdl, VarPowerFlowReferenceType.d_v_N, d_v_N)
            else:
                pass

            if _get_external_mapping_var_if_present(mdl=mdl, key=VarPowerFlowReferenceType.v_A) is not None:
                V_A = self.power_flow_results_3ph.voltage_A[bus_index]
                v_A: float = np.sqrt(2.0) * np.imag(V_A)
                d_v_A: float = omega_base * np.sqrt(2.0) * np.real(V_A)

                self.set_init_guess_and_preserve_post_init(mdl, VarPowerFlowReferenceType.v_A, v_A)
                self.set_diff_init_guess(mdl, VarPowerFlowReferenceType.d_v_A, d_v_A)
            else:
                pass

            if _get_external_mapping_var_if_present(mdl=mdl, key=VarPowerFlowReferenceType.v_B) is not None:
                V_B = self.power_flow_results_3ph.voltage_B[bus_index]
                v_B: float = np.sqrt(2.0) * np.imag(V_B)
                d_v_B: float = omega_base * np.sqrt(2.0) * np.real(V_B)

                self.set_init_guess_and_preserve_post_init(mdl, VarPowerFlowReferenceType.v_B, v_B)
                self.set_diff_init_guess(mdl, VarPowerFlowReferenceType.d_v_B, d_v_B)
            else:
                pass

            if _get_external_mapping_var_if_present(mdl=mdl, key=VarPowerFlowReferenceType.v_C) is not None:
                V_C = self.power_flow_results_3ph.voltage_C[bus_index]
                v_C: float = np.sqrt(2.0) * np.imag(V_C)
                d_v_C: float = omega_base * np.sqrt(2.0) * np.real(V_C)

                self.set_init_guess_and_preserve_post_init(mdl, VarPowerFlowReferenceType.v_C, v_C)
                self.set_diff_init_guess(mdl, VarPowerFlowReferenceType.d_v_C, d_v_C)
            else:
                pass

    def _try_set_bus_pf_init_balanced(self, bus: Bus,
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
                self.set_init_guess_and_preserve_post_init(
                    mdl,
                    VarPowerFlowReferenceType.Vdc,
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

            if _get_external_mapping_var_if_present(mdl=mdl, key=VarPowerFlowReferenceType.v_N) is not None:
                v_N: float = np.sqrt(2.0) * np.imag(V_N)
                # d_v_N: float = omega_base * np.sqrt(2.0) * np.real(V_N)

                self.set_init_guess_and_preserve_post_init(mdl, VarPowerFlowReferenceType.v_N, v_N)
                # self.set_diff_init_guess(mdl, VarPowerFlowReferenceType.d_v_N, d_v_N)

            if _get_external_mapping_var_if_present(mdl=mdl, key=VarPowerFlowReferenceType.v_A) is not None:
                v_A: float = np.sqrt(2.0) * np.imag(V_A)
                # d_v_A: float = omega_base * np.sqrt(2.0) * np.real(V_A)

                self.set_init_guess_and_preserve_post_init(mdl, VarPowerFlowReferenceType.v_A, v_A)
                # self.set_diff_init_guess(mdl, VarPowerFlowReferenceType.d_v_A, d_v_A)

            if _get_external_mapping_var_if_present(mdl=mdl, key=VarPowerFlowReferenceType.v_B) is not None:
                v_B: float = np.sqrt(2.0) * np.imag(V_B)
                # d_v_B: float = omega_base * np.sqrt(2.0) * np.real(V_B)

                self.set_init_guess_and_preserve_post_init(mdl, VarPowerFlowReferenceType.v_B, v_B)
                # self.set_diff_init_guess(mdl, VarPowerFlowReferenceType.d_v_B, d_v_B)

            if _get_external_mapping_var_if_present(mdl=mdl, key=VarPowerFlowReferenceType.v_C) is not None:
                v_C: float = np.sqrt(2.0) * np.imag(V_C)
                # d_v_C: float = omega_base * np.sqrt(2.0) * np.real(V_C)

                self.set_init_guess_and_preserve_post_init(mdl, VarPowerFlowReferenceType.v_C, v_C)
                # self.set_diff_init_guess(mdl, VarPowerFlowReferenceType.d_v_C, d_v_C)

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

        # Build the balanced positive-sequence voltage from the PF bus phasors.
        V1: complex = (VA + a * VB + (a * a) * VC) / 3.0
        I1: complex = (IA + a * IB + (a * a) * IC) / 3.0

        phi_V = float(np.angle(V1))
        phi_I = float(np.angle(I1))

        # VSC EMT templates interpret ``phi`` in the converter-delivered-power
        # convention while the PF branch current uses the network branch
        # convention. Shifting by ``pi`` preserves the seeded current states and
        # branch/KCL signs while making the analytical VSC power initialization
        # consistent with positive converter export.
        ang = phi_I - phi_V + np.pi
        phi = float(np.arctan2(np.sin(ang), np.cos(ang)))

        external_mapping: Optional[Dict[Any, Var]] = _get_external_mapping(mdl)
        if external_mapping is None:
            return

        if VarPowerFlowReferenceType.phi_v in external_mapping:
            self.set_external_param(mdl, VarPowerFlowReferenceType.phi_v, phi_V)

        if VarPowerFlowReferenceType.phi in external_mapping:
            self.set_external_param(mdl, VarPowerFlowReferenceType.phi, phi)

        if VarPowerFlowReferenceType.Vpk in external_mapping:
            self.set_external_param(mdl, VarPowerFlowReferenceType.Vpk, float(np.sqrt(2.0) * np.abs(V1)))

        if VarPowerFlowReferenceType.Ipk in external_mapping:
            self.set_external_param(mdl, VarPowerFlowReferenceType.Ipk, float(np.sqrt(2.0) * np.abs(I1)))

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

        if abs(SA) + abs(SB) + abs(SC) < 1e-12 and self.power_flow_results is not None:
            # The 3-ph VSC result container may not populate per-phase converter powers yet.
            # In that case we fall back to the balanced PF operating point and distribute the
            # total converter power equally across the three phases for initialization only.
            S_ac_total_balanced: complex = _get_balanced_vsc_ac_power(self.power_flow_results, vsc_index) / sbase
            SA = S_ac_total_balanced / 3.0
            SB = S_ac_total_balanced / 3.0
            SC = S_ac_total_balanced / 3.0
        else:
            pass

        IA = 0.0 + 0.0j if abs(VA) <= 1e-12 else np.conj(SA / VA)
        IB = 0.0 + 0.0j if abs(VB) <= 1e-12 else np.conj(SB / VB)
        IC = 0.0 + 0.0j if abs(VC) <= 1e-12 else np.conj(SC / VC)

        pf_results_3ph_pfn_vsc: float = float(pf_results_3ph.Pfp_vsc[vsc_index])

        S_ac_total = SA + SB + SC

        if abs(S_ac_total) < 1e-12 and self.power_flow_results is not None:
            S_dc_total = _get_balanced_vsc_dc_power(self.power_flow_results, vsc_index) / sbase
        else:
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

        ac_voltage_keys: Dict[str, VarPowerFlowReferenceType] = {
            "N": VarPowerFlowReferenceType.v_N,
            "A": VarPowerFlowReferenceType.v_A,
            "B": VarPowerFlowReferenceType.v_B,
            "C": VarPowerFlowReferenceType.v_C,
        }
        ac_current_keys: Dict[str, VarPowerFlowReferenceType] = {
            "N": VarPowerFlowReferenceType.i_N,
            "A": VarPowerFlowReferenceType.i_A,
            "B": VarPowerFlowReferenceType.i_B,
            "C": VarPowerFlowReferenceType.i_C,
        }
        if_keys: Dict[str, VarPowerFlowReferenceType] = {
            "N": VarPowerFlowReferenceType.if_N,
            "A": VarPowerFlowReferenceType.if_A,
            "B": VarPowerFlowReferenceType.if_B,
            "C": VarPowerFlowReferenceType.if_C,
        }
        it_keys: Dict[str, VarPowerFlowReferenceType] = {
            "N": VarPowerFlowReferenceType.it_N,
            "A": VarPowerFlowReferenceType.it_A,
            "B": VarPowerFlowReferenceType.it_B,
            "C": VarPowerFlowReferenceType.it_C,
        }
        sf_keys: Dict[str, Optional[VarPowerFlowReferenceType]] = {
            "N": None,
            "A": VarPowerFlowReferenceType.Sf_A,
            "B": VarPowerFlowReferenceType.Sf_B,
            "C": VarPowerFlowReferenceType.Sf_C,
        }
        st_keys: Dict[str, Optional[VarPowerFlowReferenceType]] = {
            "N": None,
            "A": VarPowerFlowReferenceType.St_A,
            "B": VarPowerFlowReferenceType.St_B,
            "C": VarPowerFlowReferenceType.St_C,
        }
        d_vf_keys: Dict[str, VarPowerFlowReferenceType] = {
            "N": VarPowerFlowReferenceType.d_v_N_f,
            "A": VarPowerFlowReferenceType.d_v_A_f,
            "B": VarPowerFlowReferenceType.d_v_B_f,
            "C": VarPowerFlowReferenceType.d_v_C_f,
        }
        d_vt_keys: Dict[str, VarPowerFlowReferenceType] = {
            "N": VarPowerFlowReferenceType.d_v_N_t,
            "A": VarPowerFlowReferenceType.d_v_A_t,
            "B": VarPowerFlowReferenceType.d_v_B_t,
            "C": VarPowerFlowReferenceType.d_v_C_t,
        }

        omega_base: float = 2.0 * np.pi * self.grid.fBase
        # ``I_ph = conj(S/V)`` already yields the branch-convention current
        # from bus into branch. The EMT KCL also uses branch
        # convention for VSC branches (``I_kcl -= i_branch``), so the
        # seeded value is taken directly without any sign flip, just like
        # with other branches
        for ph in ["N", "A", "B", "C"]:
            V_ph = phase_voltage_dict[ph]
            I_ph = phase_current_dict[ph]
            S_ph = phase_power_dict[ph]

            # Store it once and reuse
            i_branch_init: float = float(np.sqrt(2.0) * np.imag(I_ph))

            self.set_if_exists(mdl=mdl,
                               key=ac_voltage_keys[ph],
                               value=float(np.sqrt(2.0) * np.imag(V_ph)))
            self.set_if_exists(mdl=mdl,
                               key=ac_current_keys[ph],
                               value=i_branch_init)

            if ac_is_from:
                self.set_if_exists(mdl=mdl,
                                   key=if_keys[ph],
                                   value=i_branch_init)
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
                                   value=i_branch_init)
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
            self.set_if_exists(
                mdl=mdl,
                key=VarPowerFlowReferenceType.Vdc,
                value=v_dc,
                persist_after_native_init=True,
            )
            if abs(v_dc) > 1e-12:
                self.set_if_exists(mdl=mdl,
                                   key=VarPowerFlowReferenceType.Idc,
                                   value=float(np.real(S_dc_total) / v_dc),
                                   persist_after_native_init=True)
            else:
                self.set_if_exists(
                    mdl=mdl,
                    key=VarPowerFlowReferenceType.Idc,
                    value=0.0,
                    persist_after_native_init=True,
                )

            self._seed_switched_converter_internal_init_balanced(
                mdl=mdl,
                VA=complex(VA),
                VB=complex(VB),
                VC=complex(VC),
                IA=IA,
                IB=IB,
                IC=IC,
                v_dc=v_dc,
            )

        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.P, value=float(np.real(S_ac_total)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Q, value=float(np.imag(S_ac_total)))

        S_from = S_ac_total if ac_is_from else S_dc_total
        S_to = S_dc_total if ac_is_from else S_ac_total
        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Pf, value=float(np.real(S_from)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Qf, value=float(np.imag(S_from)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Pt, value=float(np.real(S_to)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Qt, value=float(np.imag(S_to)))

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

        pf_results_pfn_vsc: float = float(pf_results.Pfn_vsc[vsc_index])

        S_ac_total = _get_balanced_vsc_ac_power(pf_results, vsc_index) / sbase
        S_dc_total = _get_balanced_vsc_dc_power(pf_results, vsc_index) / sbase

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

        ac_voltage_keys: Dict[str, VarPowerFlowReferenceType] = {
            "N": VarPowerFlowReferenceType.v_N,
            "A": VarPowerFlowReferenceType.v_A,
            "B": VarPowerFlowReferenceType.v_B,
            "C": VarPowerFlowReferenceType.v_C,
        }
        ac_current_keys: Dict[str, VarPowerFlowReferenceType] = {
            "N": VarPowerFlowReferenceType.i_N,
            "A": VarPowerFlowReferenceType.i_A,
            "B": VarPowerFlowReferenceType.i_B,
            "C": VarPowerFlowReferenceType.i_C,
        }
        if_keys: Dict[str, VarPowerFlowReferenceType] = {
            "N": VarPowerFlowReferenceType.if_N,
            "A": VarPowerFlowReferenceType.if_A,
            "B": VarPowerFlowReferenceType.if_B,
            "C": VarPowerFlowReferenceType.if_C,
        }
        it_keys: Dict[str, VarPowerFlowReferenceType] = {
            "N": VarPowerFlowReferenceType.it_N,
            "A": VarPowerFlowReferenceType.it_A,
            "B": VarPowerFlowReferenceType.it_B,
            "C": VarPowerFlowReferenceType.it_C,
        }
        sf_keys: Dict[str, Optional[VarPowerFlowReferenceType]] = {
            "N": None,
            "A": VarPowerFlowReferenceType.Sf_A,
            "B": VarPowerFlowReferenceType.Sf_B,
            "C": VarPowerFlowReferenceType.Sf_C,
        }
        st_keys: Dict[str, Optional[VarPowerFlowReferenceType]] = {
            "N": None,
            "A": VarPowerFlowReferenceType.St_A,
            "B": VarPowerFlowReferenceType.St_B,
            "C": VarPowerFlowReferenceType.St_C,
        }
        d_vf_keys: Dict[str, VarPowerFlowReferenceType] = {
            "N": VarPowerFlowReferenceType.d_v_N_f,
            "A": VarPowerFlowReferenceType.d_v_A_f,
            "B": VarPowerFlowReferenceType.d_v_B_f,
            "C": VarPowerFlowReferenceType.d_v_C_f,
        }
        d_vt_keys: Dict[str, VarPowerFlowReferenceType] = {
            "N": VarPowerFlowReferenceType.d_v_N_t,
            "A": VarPowerFlowReferenceType.d_v_A_t,
            "B": VarPowerFlowReferenceType.d_v_B_t,
            "C": VarPowerFlowReferenceType.d_v_C_t,
        }

        omega_base: float = 2.0 * np.pi * self.grid.fBase

        for ph in ["N", "A", "B", "C"]:
            V_ph = phase_voltage_dict[ph]
            I_ph = phase_current_dict[ph]
            S_ph = phase_power_dict[ph]

            # ``I_ph = conj(S/V)`` is already in branch convention
            # Hence no sign change needed
            i_branch_init: float = float(np.sqrt(2.0) * np.imag(I_ph))

            self.set_if_exists(mdl=mdl,
                               key=ac_voltage_keys[ph],
                               value=float(np.sqrt(2.0) * np.imag(V_ph)))
            self.set_if_exists(mdl=mdl,
                               key=ac_current_keys[ph],
                               value=i_branch_init)

            if ac_is_from:
                self.set_if_exists(mdl=mdl,
                                   key=if_keys[ph],
                                   value=i_branch_init)
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
                                   value=i_branch_init)
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
        self.set_if_exists(
            mdl=mdl,
            key=VarPowerFlowReferenceType.Vdc,
            value=v_dc,
            persist_after_native_init=True,
        )
        if abs(v_dc) > 1e-12:
            self.set_if_exists(mdl=mdl,
                               key=VarPowerFlowReferenceType.Idc,
                               value=float(np.real(S_dc_total) / v_dc),
                               persist_after_native_init=True)
        else:
            self.set_if_exists(
                mdl=mdl,
                key=VarPowerFlowReferenceType.Idc,
                value=0.0,
                persist_after_native_init=True,
            )

        self._seed_switched_converter_internal_init_balanced(
            mdl=mdl,
            VA=complex(VA),
            VB=complex(VB),
            VC=complex(VC),
            IA=IA,
            IB=IB,
            IC=IC,
            v_dc=v_dc,
        )

        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.P, value=float(np.real(S_ac_total)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Q, value=float(np.imag(S_ac_total)))

        S_from = S_ac_total if ac_is_from else S_dc_total
        S_to = S_dc_total if ac_is_from else S_ac_total
        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Pf, value=float(np.real(S_from)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Qf, value=float(np.imag(S_from)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Pt, value=float(np.real(S_to)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Qt, value=float(np.imag(S_to)))

    def _try_set_dc_branch_pf_init(
            self,
            mdl: Block,
            branch_index: int,
            f_bus_idx: int,
            t_bus_idx: int,
            sbase: float,
    ) -> None:
        """
        Initialize a two-terminal DC branch from the balanced PF snapshot.

        The DC EMT branch contract uses explicit terminal voltages ``Vf_dc`` /
        ``Vt_dc`` and terminal currents ``If_dc`` / ``It_dc`` so that generic
        branch models such as valves or DC lines can derive their initial state
        from both connected buses.
        """
        pf_results = self.power_flow_results
        if pf_results is None:
            return

        eps: float = 1.0e-12
        preserve_dc_current_seed: bool = (
                _get_external_mapping_var_if_present(mdl=mdl, key=VarPowerFlowReferenceType.DcPathModeSeed) is None
        )

        try:
            v_f: float = float(np.abs(pf_results.voltage[f_bus_idx]))
        except (AttributeError, IndexError, TypeError, ValueError):
            v_f = 0.0

        try:
            v_t: float = float(np.abs(pf_results.voltage[t_bus_idx]))
        except (AttributeError, IndexError, TypeError, ValueError):
            v_t = 0.0

        try:
            s_f: complex = complex(pf_results.Sf[branch_index]) / sbase
        except (AttributeError, IndexError, TypeError, ValueError):
            s_f = 0.0 + 0.0j

        try:
            s_t: complex = complex(pf_results.St[branch_index]) / sbase
        except (AttributeError, IndexError, TypeError, ValueError):
            s_t = 0.0 + 0.0j

        i_f: float = float(np.real(s_f) / v_f) if abs(v_f) > eps else 0.0
        i_t: float = float(np.real(s_t) / v_t) if abs(v_t) > eps else 0.0

        if abs(i_f) > eps:
            path_mode_seed: float = 1.0 if i_f >= 0.0 else -1.0
        else:
            if (v_f - v_t) > eps:
                path_mode_seed = 1.0
            else:
                if (v_f - v_t) < -eps:
                    path_mode_seed = -1.0
                else:
                    path_mode_seed = 0.0

        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Vf_dc, value=v_f, persist_after_native_init=True)
        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Vt_dc, value=v_t, persist_after_native_init=True)
        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.DcPathModeSeed, value=path_mode_seed)
        self.set_if_exists(
            mdl=mdl,
            key=VarPowerFlowReferenceType.If_dc,
            value=i_f,
            persist_after_native_init=preserve_dc_current_seed,
        )
        self.set_if_exists(
            mdl=mdl,
            key=VarPowerFlowReferenceType.It_dc,
            value=i_t,
            persist_after_native_init=preserve_dc_current_seed,
        )
        self.set_if_exists(
            mdl=mdl,
            key=VarPowerFlowReferenceType.Idc,
            value=i_f,
            persist_after_native_init=preserve_dc_current_seed,
        )
        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Pf, value=float(np.real(s_f)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Qf, value=float(np.imag(s_f)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Pt, value=float(np.real(s_t)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Qt, value=float(np.imag(s_t)))

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

        if self.grid.buses[f_bus_idx].is_dc or self.grid.buses[t_bus_idx].is_dc:
            self._try_set_dc_branch_pf_init(
                mdl=mdl,
                branch_index=branch_index,
                f_bus_idx=f_bus_idx,
                t_bus_idx=t_bus_idx,
                sbase=sbase,
            )
            return

        phases: List[str] = ["N", "A", "B", "C"]

        sf_key_dict: Dict[str, Optional[VarPowerFlowReferenceType]] = {
            "N": None,
            "A": VarPowerFlowReferenceType.Sf_A,
            "B": VarPowerFlowReferenceType.Sf_B,
            "C": VarPowerFlowReferenceType.Sf_C,
        }
        st_key_dict: Dict[str, Optional[VarPowerFlowReferenceType]] = {
            "N": None,
            "A": VarPowerFlowReferenceType.St_A,
            "B": VarPowerFlowReferenceType.St_B,
            "C": VarPowerFlowReferenceType.St_C,
        }

        if_key_dict: Dict[str, VarPowerFlowReferenceType] = {
            "N": VarPowerFlowReferenceType.if_N,
            "A": VarPowerFlowReferenceType.if_A,
            "B": VarPowerFlowReferenceType.if_B,
            "C": VarPowerFlowReferenceType.if_C,
        }
        it_key_dict: Dict[str, VarPowerFlowReferenceType] = {
            "N": VarPowerFlowReferenceType.it_N,
            "A": VarPowerFlowReferenceType.it_A,
            "B": VarPowerFlowReferenceType.it_B,
            "C": VarPowerFlowReferenceType.it_C,
        }
        d_vf_key_dict: Dict[str, VarPowerFlowReferenceType] = {
            "N": VarPowerFlowReferenceType.d_v_N_f,
            "A": VarPowerFlowReferenceType.d_v_A_f,
            "B": VarPowerFlowReferenceType.d_v_B_f,
            "C": VarPowerFlowReferenceType.d_v_C_f,
        }
        d_vt_key_dict: Dict[str, VarPowerFlowReferenceType] = {
            "N": VarPowerFlowReferenceType.d_v_N_t,
            "A": VarPowerFlowReferenceType.d_v_A_t,
            "B": VarPowerFlowReferenceType.d_v_B_t,
            "C": VarPowerFlowReferenceType.d_v_C_t,
        }


        voltage_from_dict = {
            "N": self.power_flow_results_3ph.voltage_N,
            "A": self.power_flow_results_3ph.voltage_A,
            "B": self.power_flow_results_3ph.voltage_B,
            "C": self.power_flow_results_3ph.voltage_C,
        }
        voltage_to_dict = {
            "N": self.power_flow_results_3ph.voltage_N,
            "A": self.power_flow_results_3ph.voltage_A,
            "B": self.power_flow_results_3ph.voltage_B,
            "C": self.power_flow_results_3ph.voltage_C,
        }

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
        from_phase_currents: Dict[str, complex] = dict()
        to_phase_currents: Dict[str, complex] = dict()
        from_phase_currents_inst: Dict[str, float] = dict()
        to_phase_currents_inst: Dict[str, float] = dict()

        for ph in phases:
            sf_key: Optional[VarPowerFlowReferenceType] = sf_key_dict[ph]
            st_key: Optional[VarPowerFlowReferenceType] = st_key_dict[ph]
            sf_array: Optional[np.ndarray] = sf_array_dict[ph]
            st_array: Optional[np.ndarray] = st_array_dict[ph]

            if sf_key is None:
                pass
            else:
                sf_var: Optional[Any] = _get_external_mapping_var_if_present(mdl=mdl, key=sf_key)
                if sf_var is not None and sf_array is not None:
                    pf_idx = vsc_index if is_vsc and vsc_index >= 0 else branch_index
                    sf_ph_value = _get_array_entry_if_in_range(sf_array, pf_idx)
                    if sf_ph_value is None:
                        pass
                    else:
                        sf_ph = sf_ph_value / sbase
                        self.set_if_exists(mdl=mdl, key=sf_key, value=float(np.real(sf_ph)))
                        sf_sum += sf_ph
                elif is_vsc:
                    self.set_if_exists(mdl=mdl, key=sf_key, value=0.0)
                else:
                    pass

            if st_key is None:
                pass
            else:
                st_var: Optional[Any] = _get_external_mapping_var_if_present(mdl=mdl, key=st_key)
                if st_var is not None and st_array is not None:
                    pf_idx = vsc_index if is_vsc and vsc_index >= 0 else branch_index
                    st_ph_value = _get_array_entry_if_in_range(st_array, pf_idx)
                    if st_ph_value is None:
                        pass
                    else:
                        st_ph = st_ph_value / sbase
                        self.set_if_exists(mdl=mdl, key=st_key, value=float(np.real(st_ph)))
                        st_sum += st_ph
                else:
                    pass

        for ph in phases:
            if_key: VarPowerFlowReferenceType = if_key_dict[ph]
            it_key: VarPowerFlowReferenceType = it_key_dict[ph]

            if_key_var: Optional[Any] = _get_external_mapping_var_if_present(mdl=mdl, key=if_key)
            it_key_var: Optional[Any] = _get_external_mapping_var_if_present(mdl=mdl, key=it_key)
            uses_currents: bool = if_key_var is not None or it_key_var is not None

            if uses_currents:
                # Missing optional current mappings are skipped exactly like explicit None entries.
                sf_array = sf_array_dict[ph]
                st_array = st_array_dict[ph]
                voltage_from_array = voltage_from_dict[ph]
                voltage_to_array = voltage_to_dict[ph]

                pf_idx = vsc_index if is_vsc and vsc_index >= 0 else branch_index

                if sf_array is None or voltage_from_array is None:
                    i_f = 0.0 + 0.0j
                else:
                    sf_ph_value = _get_array_entry_if_in_range(sf_array, pf_idx)
                    vf_ph = _get_array_entry_if_in_range(voltage_from_array, f_bus_idx)
                    if sf_ph_value is None or vf_ph is None or abs(vf_ph) <= 1e-12:
                        i_f = 0.0 + 0.0j
                    else:
                        sf_ph = sf_ph_value / sbase
                        i_f = np.conj(sf_ph / vf_ph)

                if st_array is None or voltage_to_array is None:
                    i_t = 0.0 + 0.0j
                else:
                    st_ph_value = _get_array_entry_if_in_range(st_array, pf_idx)
                    vt_ph = _get_array_entry_if_in_range(voltage_to_array, t_bus_idx)
                    if st_ph_value is None or vt_ph is None or abs(vt_ph) <= 1e-12:
                        i_t = 0.0 + 0.0j
                    else:
                        st_ph = st_ph_value / sbase
                        i_t = np.conj(st_ph / vt_ph)

                i_f0: float = np.sqrt(2.0) * np.imag(i_f)
                i_t0: float = np.sqrt(2.0) * np.imag(i_t)

                if ph in {"A", "B", "C"}:
                    from_phase_currents[ph] = complex(i_f)
                    to_phase_currents[ph] = complex(i_t)
                    from_phase_currents_inst[ph] = float(i_f0)
                    to_phase_currents_inst[ph] = float(i_t0)
                else:
                    pass

                self.set_if_exists(mdl=mdl, key=if_key, value=float(i_f0), persist_after_native_init=False)
                self.set_if_exists(mdl=mdl, key=it_key, value=float(i_t0), persist_after_native_init=False)
            else:
                pass

        neutral_if_var = _get_external_mapping_var_if_present(mdl=mdl, key=VarPowerFlowReferenceType.if_N)
        if neutral_if_var is not None:
            i_f_neutral = -(from_phase_currents.get("A", 0.0 + 0.0j) + from_phase_currents.get("B", 0.0 + 0.0j) + from_phase_currents.get("C", 0.0 + 0.0j))
            neutral_value = float(np.sqrt(2.0) * np.imag(i_f_neutral))
            self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.if_N, value=neutral_value, persist_after_native_init=False)
        else:
            pass

        neutral_it_var = _get_external_mapping_var_if_present(mdl=mdl, key=VarPowerFlowReferenceType.it_N)
        if neutral_it_var is not None:
            i_t_neutral = -(to_phase_currents.get("A", 0.0 + 0.0j) + to_phase_currents.get("B", 0.0 + 0.0j) + to_phase_currents.get("C", 0.0 + 0.0j))
            neutral_value = float(np.sqrt(2.0) * np.imag(i_t_neutral))
            self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.it_N, value=neutral_value, persist_after_native_init=False)
        else:
            pass

        if find_name_in_block("i_f_A", mdl) is not None:
            self.set_internal_init_if_exists(mdl, "i_f_A", from_phase_currents_inst.get("A", 0.0))
            self.set_internal_init_if_exists(mdl, "i_f_B", from_phase_currents_inst.get("B", 0.0))
            self.set_internal_init_if_exists(mdl, "i_f_C", from_phase_currents_inst.get("C", 0.0))
            self.set_internal_init_if_exists(mdl, "i_t_A", to_phase_currents_inst.get("A", 0.0))
            self.set_internal_init_if_exists(mdl, "i_t_B", to_phase_currents_inst.get("B", 0.0))
            self.set_internal_init_if_exists(mdl, "i_t_C", to_phase_currents_inst.get("C", 0.0))
        else:
            if find_name_in_block("i_ser_A", mdl) is not None:
                self.set_internal_init_if_exists(mdl, "i_ser_A", from_phase_currents_inst.get("A", 0.0))
                self.set_internal_init_if_exists(mdl, "i_ser_B", from_phase_currents_inst.get("B", 0.0))
                self.set_internal_init_if_exists(mdl, "i_ser_C", from_phase_currents_inst.get("C", 0.0))
            else:
                pass

        omega_base: float = 2.0 * np.pi * self.grid.fBase
        for ph in phases:
            d_vf_key: VarPowerFlowReferenceType = d_vf_key_dict[ph]
            d_vt_key: VarPowerFlowReferenceType = d_vt_key_dict[ph]
            voltage_from_array = voltage_from_dict[ph]
            voltage_to_array = voltage_to_dict[ph]
            d_vf_var: Optional[Any] = _get_external_mapping_var_if_present(mdl=mdl, key=d_vf_key)
            if d_vf_var is not None:
                if voltage_from_array is None:
                    vf_ph = 0.0 + 0.0j
                else:
                    vf_ph = _get_array_entry_if_in_range(voltage_from_array, f_bus_idx)
                    if vf_ph is None:
                        vf_ph = 0.0 + 0.0j
                    else:
                        pass
                d_vf: float = omega_base * np.sqrt(2.0) * np.real(vf_ph)
                self.set_external_param(mdl, d_vf_key, d_vf)
            else:
                pass
            d_vt_var: Optional[Any] = _get_external_mapping_var_if_present(mdl=mdl, key=d_vt_key)
            if d_vt_var is not None:
                if voltage_to_array is None:
                    vt_ph = 0.0 + 0.0j
                else:
                    vt_ph = _get_array_entry_if_in_range(voltage_to_array, t_bus_idx)
                    if vt_ph is None:
                        vt_ph = 0.0 + 0.0j
                    else:
                        pass
                d_vt: float = omega_base * np.sqrt(2.0) * np.real(vt_ph)
                self.set_external_param(mdl, d_vt_key, d_vt)
            else:
                pass

        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Pf, value=float(np.real(sf_sum)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Qf, value=float(np.imag(sf_sum)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Pt, value=float(np.real(st_sum)))
        self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Qt, value=float(np.imag(st_sum)))


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

        if self.grid.buses[f_bus_idx].is_dc or self.grid.buses[t_bus_idx].is_dc:
            self._try_set_dc_branch_pf_init(
                mdl=mdl,
                branch_index=branch_index,
                f_bus_idx=f_bus_idx,
                t_bus_idx=t_bus_idx,
                sbase=sbase,
            )
            return

        phases: List[str] = ["N", "A", "B", "C"]

        sf_key_dict: Dict[str, Optional[VarPowerFlowReferenceType]] = {
            "N": None,
            "A": VarPowerFlowReferenceType.Sf_A,
            "B": VarPowerFlowReferenceType.Sf_B,
            "C": VarPowerFlowReferenceType.Sf_C,
        }
        st_key_dict: Dict[str, Optional[VarPowerFlowReferenceType]] = {
            "N": None,
            "A": VarPowerFlowReferenceType.St_A,
            "B": VarPowerFlowReferenceType.St_B,
            "C": VarPowerFlowReferenceType.St_C,
        }

        if_key_dict: Dict[str, VarPowerFlowReferenceType] = {
            "N": VarPowerFlowReferenceType.if_N,
            "A": VarPowerFlowReferenceType.if_A,
            "B": VarPowerFlowReferenceType.if_B,
            "C": VarPowerFlowReferenceType.if_C,
        }
        it_key_dict: Dict[str, VarPowerFlowReferenceType] = {
            "N": VarPowerFlowReferenceType.it_N,
            "A": VarPowerFlowReferenceType.it_A,
            "B": VarPowerFlowReferenceType.it_B,
            "C": VarPowerFlowReferenceType.it_C,
        }
        d_vf_key_dict: Dict[str, VarPowerFlowReferenceType] = {
            "N": VarPowerFlowReferenceType.d_v_N_f,
            "A": VarPowerFlowReferenceType.d_v_A_f,
            "B": VarPowerFlowReferenceType.d_v_B_f,
            "C": VarPowerFlowReferenceType.d_v_C_f,
        }
        d_vt_key_dict: Dict[str, VarPowerFlowReferenceType] = {
            "N": VarPowerFlowReferenceType.d_v_N_t,
            "A": VarPowerFlowReferenceType.d_v_A_t,
            "B": VarPowerFlowReferenceType.d_v_B_t,
            "C": VarPowerFlowReferenceType.d_v_C_t,
        }

        pf_results = self.power_flow_results
        if pf_results is None:
            return

        alpha = 2.0 * np.pi / 3.0

        v_f_bus: CxVec = pf_results.voltage[f_bus_idx]
        v_t_bus: CxVec = pf_results.voltage[t_bus_idx]

        if is_vsc and vsc_index >= 0:
            pf_results_pfn_vsc: float = float(pf_results.Pfn_vsc[vsc_index])

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
        from_phase_currents: Dict[str, complex] = dict()
        to_phase_currents: Dict[str, complex] = dict()

        for ph in phases:
            sf_key: Optional[VarPowerFlowReferenceType] = sf_key_dict[ph]
            st_key: Optional[VarPowerFlowReferenceType] = st_key_dict[ph]

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
                sf_var: Optional[Any] = _get_external_mapping_var_if_present(mdl=mdl, key=sf_key)
                if sf_var is not None:
                    self.set_if_exists(mdl=mdl, key=sf_key, value=float(np.real(sf_ph)))
                    sf_sum += sf_ph
                else:
                    pass
            else:
                pass

            if st_key is not None:
                st_var: Optional[Any] = _get_external_mapping_var_if_present(mdl=mdl, key=st_key)
                if st_var is not None:
                    self.set_if_exists(mdl=mdl, key=st_key, value=float(np.real(st_ph)))
                    st_sum += st_ph
                else:
                    pass
            else:
                pass

        for ph in phases:
            if_key: VarPowerFlowReferenceType = if_key_dict[ph]
            it_key: VarPowerFlowReferenceType = it_key_dict[ph]

            if_key_var: Optional[Any] = _get_external_mapping_var_if_present(mdl=mdl, key=if_key)
            it_key_var: Optional[Any] = _get_external_mapping_var_if_present(mdl=mdl, key=it_key)
            uses_currents: bool = if_key_var is not None or it_key_var is not None

            if uses_currents:
                # Missing optional current mappings are skipped exactly like explicit None entries.
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
                        i_t = np.conj(st_total / vt_ph)
                        # i_t = np.conj(st_phase_total / vt_ph)
                else:
                    if abs(vf_ph) <= 1e-12:
                        i_f = 0.0 + 0.0j
                    else:
                        i_f = np.conj(sf_total / vf_ph)
                        # i_f = np.conj(sf_phase_total / vf_ph)

                    if abs(vt_ph) <= 1e-12:
                        i_t = 0.0 + 0.0j
                    else:
                        i_t = np.conj(st_total / vt_ph)
                        # i_t = np.conj(st_phase_total / vt_ph)

                i_f0: float = np.sqrt(2.0) * np.imag(i_f)
                i_t0: float = np.sqrt(2.0) * np.imag(i_t)

                if ph in {"A", "B", "C"}:
                    from_phase_currents[ph] = complex(i_f)
                    to_phase_currents[ph] = complex(i_t)
                else:
                    pass

                self.set_if_exists(mdl=mdl, key=if_key, value=float(i_f0), persist_after_native_init=False)
                self.set_if_exists(mdl=mdl, key=it_key, value=float(i_t0), persist_after_native_init=False)
            else:
                pass

        neutral_if_var = _get_external_mapping_var_if_present(mdl=mdl, key=VarPowerFlowReferenceType.if_N)
        if neutral_if_var is not None:
            i_f_neutral = -(from_phase_currents.get("A", 0.0 + 0.0j) + from_phase_currents.get("B", 0.0 + 0.0j) + from_phase_currents.get("C", 0.0 + 0.0j))
            neutral_value = float(np.sqrt(2.0) * np.imag(i_f_neutral))
            self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.if_N, value=neutral_value, persist_after_native_init=False)
        else:
            pass

        neutral_it_var = _get_external_mapping_var_if_present(mdl=mdl, key=VarPowerFlowReferenceType.it_N)
        if neutral_it_var is not None:
            i_t_neutral = -(to_phase_currents.get("A", 0.0 + 0.0j) + to_phase_currents.get("B", 0.0 + 0.0j) + to_phase_currents.get("C", 0.0 + 0.0j))
            neutral_value = float(np.sqrt(2.0) * np.imag(i_t_neutral))
            self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.it_N, value=neutral_value, persist_after_native_init=False)
        else:
            pass

        omega_base: float = 2.0 * np.pi * self.grid.fBase
        for ph in phases:
            d_vf_key: VarPowerFlowReferenceType = d_vf_key_dict[ph]
            d_vt_key: VarPowerFlowReferenceType = d_vt_key_dict[ph]

            vf_ph = voltage_dict[ph]
            vt_ph = voltage_to_dict[ph]

            d_vf_var: Optional[Any] = _get_external_mapping_var_if_present(mdl=mdl, key=d_vf_key)
            if d_vf_var is not None:
                d_vf: float = omega_base * np.sqrt(2.0) * np.real(vf_ph)
                self.set_external_param(mdl, d_vf_key, d_vf)
            else:
                pass

            d_vt_var: Optional[Any] = _get_external_mapping_var_if_present(mdl=mdl, key=d_vt_key)
            if d_vt_var is not None:
                d_vt: float = omega_base * np.sqrt(2.0) * np.real(vt_ph)
                self.set_external_param(mdl, d_vt_key, d_vt)
            else:
                pass

        if is_vsc and vsc_index >= 0:
            self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Pf, value=float(np.real(sf_total)))
            self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Qf, value=float(np.imag(sf_total)))
            self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Pt, value=float(np.real(st_total)))
            self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Qt, value=float(np.imag(st_total)))
        else:
            self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Pf, value=float(np.real(sf_sum)))
            self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Qf, value=float(np.imag(sf_sum)))
            self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Pt, value=float(np.real(st_sum)))
            self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.Qt, value=float(np.imag(st_sum)))

        if is_vsc and vsc_index >= 0:
            if self.power_flow_results is not None:
                P_vsc = -float(np.real(_get_balanced_vsc_ac_power(self.power_flow_results, vsc_index)))
                self.set_if_exists(mdl=mdl, key=VarPowerFlowReferenceType.P, value=P_vsc)

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
            # mdl.event_dict[rt.Ih_f[k]] = self.grid.var_factory.add_const(float(Ih_f0_red[k]))
            # mdl.event_dict[rt.Ih_t[k]] = self.grid.var_factory.add_const(float(Ih_t0_red[k]))
            mdl.event_dict[rt.Ih_f[k]] = Const(float(Ih_f0_red[k]))
            mdl.event_dict[rt.Ih_t[k]] = Const(float(Ih_t0_red[k]))

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
            # mdl.event_dict[rt.Ih_f[k]] = self.grid.var_factory.add_const(float(Ih_f0_red[k]))
            # mdl.event_dict[rt.Ih_t[k]] = self.grid.var_factory.add_const(float(Ih_t0_red[k]))
            mdl.event_dict[rt.Ih_f[k]] = Const(float(Ih_f0_red[k]))
            mdl.event_dict[rt.Ih_t[k]] = Const(float(Ih_t0_red[k]))

        rt.initialize_buffers_from_initial_point(
            v_f0_red=v_f0_red,
            v_t0_red=v_t0_red,
            i_f0_red=i_f0_red,
            i_t0_red=i_t0_red,
        )

    def _try_set_jmarti_pf_init(
            self,
            mdl: Block,
            rt: JMartiHistoryRuntime,
            branch_index: int,
            f_bus_idx: int,
            t_bus_idx: int,
            sbase: float
    ) -> None:
        """
        Initialize JMARTI history terms from three-phase power-flow results.

        :param mdl: JMARTI symbolic block.
        :param rt: JMARTI runtime companion.
        :param branch_index: Branch index in the power-flow results.
        :param f_bus_idx: From-side bus index.
        :param t_bus_idx: To-side bus index.
        :param sbase: System base power in MVA.
        :return: None.
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
        v_f0_phasor_red: np.ndarray = np.zeros(rt.m, dtype=np.complex128)
        v_t0_phasor_red: np.ndarray = np.zeros(rt.m, dtype=np.complex128)
        i_f0_phasor_red: np.ndarray = np.zeros(rt.m, dtype=np.complex128)
        i_t0_phasor_red: np.ndarray = np.zeros(rt.m, dtype=np.complex128)
        phase_index: int = 0
        ph: str
        voltage_array: Optional[np.ndarray]
        sf_array: Optional[np.ndarray]
        st_array: Optional[np.ndarray]
        vf_ph: complex
        vt_ph: complex
        i_f: complex
        i_t: complex

        while phase_index < rt.m:
            ph = rt.active_ph[phase_index]
            voltage_array = voltage_dict[ph]

            if voltage_array is None:
                vf_ph = 0.0 + 0.0j
                vt_ph = 0.0 + 0.0j
            else:
                vf_ph = complex(voltage_array[f_bus_idx])
                vt_ph = complex(voltage_array[t_bus_idx])

            v_f0_phasor_red[phase_index] = vf_ph
            v_t0_phasor_red[phase_index] = vt_ph
            sf_array = sf_array_dict[ph]
            st_array = st_array_dict[ph]

            if sf_array is None or abs(vf_ph) <= 1.0e-12:
                i_f = 0.0 + 0.0j
            else:
                i_f = np.conj(complex(sf_array[branch_index]) / sbase / vf_ph)

            if st_array is None or abs(vt_ph) <= 1.0e-12:
                i_t = 0.0 + 0.0j
            else:
                i_t = np.conj(complex(st_array[branch_index]) / sbase / vt_ph)

            i_f0_phasor_red[phase_index] = i_f
            i_t0_phasor_red[phase_index] = i_t
            phase_index += 1

        ih_f_phase, ih_t_phase = rt.initialize_from_fundamental_phasors(
            v_f0_phasor_red=v_f0_phasor_red,
            v_t0_phasor_red=v_t0_phasor_red,
            i_f0_phasor_red=i_f0_phasor_red,
            i_t0_phasor_red=i_t0_phasor_red,
            system_frequency_hz=float(self.grid.fBase),
        )

        phase_index = 0
        while phase_index < rt.m:
            mdl.event_dict[rt.Ih_f[phase_index]] = Const(float(np.real(ih_f_phase[phase_index])))
            mdl.event_dict[rt.Ih_t[phase_index]] = Const(float(np.real(ih_t_phase[phase_index])))
            phase_index += 1

    def _try_set_jmarti_pf_init_balanced(
            self,
            mdl: Block,
            rt: JMartiHistoryRuntime,
            branch_index: int,
            f_bus_idx: int,
            t_bus_idx: int,
            sbase: float
    ) -> None:
        """
        Initialize JMARTI history terms from balanced power-flow results.

        :param mdl: JMARTI symbolic block.
        :param rt: JMARTI runtime companion.
        :param branch_index: Branch index in the power-flow results.
        :param f_bus_idx: From-side bus index.
        :param t_bus_idx: To-side bus index.
        :param sbase: System base power in MVA.
        :return: None.
        """
        pf_results = self.power_flow_results
        alpha: float = 2.0 * np.pi / 3.0
        v_f_bus: complex = complex(pf_results.voltage[f_bus_idx])
        v_t_bus: complex = complex(pf_results.voltage[t_bus_idx])
        s_f_3ph: complex = complex(pf_results.Sf[branch_index]) / sbase
        s_t_3ph: complex = complex(pf_results.St[branch_index]) / sbase
        s_f_phase: complex = s_f_3ph / 3.0
        s_t_phase: complex = s_t_3ph / 3.0
        v_f0_phasor_red: np.ndarray = np.zeros(rt.m, dtype=np.complex128)
        v_t0_phasor_red: np.ndarray = np.zeros(rt.m, dtype=np.complex128)
        i_f0_phasor_red: np.ndarray = np.zeros(rt.m, dtype=np.complex128)
        i_t0_phasor_red: np.ndarray = np.zeros(rt.m, dtype=np.complex128)
        phase_index: int = 0
        ph: str
        vf_ph: complex
        vt_ph: complex
        i_f: complex
        i_t: complex

        while phase_index < rt.m:
            ph = rt.active_ph[phase_index]

            if ph == "N":
                vf_ph = 0.0 + 0.0j
                vt_ph = 0.0 + 0.0j
                i_f = 0.0 + 0.0j
                i_t = 0.0 + 0.0j
            else:
                if ph == "A":
                    vf_ph = v_f_bus
                    vt_ph = v_t_bus
                else:
                    if ph == "B":
                        vf_ph = v_f_bus * np.exp(-1j * alpha)
                        vt_ph = v_t_bus * np.exp(-1j * alpha)
                    else:
                        if ph == "C":
                            vf_ph = v_f_bus * np.exp(+1j * alpha)
                            vt_ph = v_t_bus * np.exp(+1j * alpha)
                        else:
                            raise ValueError(f"Unsupported phase label in JMARTI runtime: {ph}")

                if abs(vf_ph) <= 1.0e-12:
                    i_f = 0.0 + 0.0j
                else:
                    i_f = np.conj(s_f_phase / vf_ph)

                if abs(vt_ph) <= 1.0e-12:
                    i_t = 0.0 + 0.0j
                else:
                    i_t = np.conj(s_t_phase / vt_ph)

            v_f0_phasor_red[phase_index] = vf_ph
            v_t0_phasor_red[phase_index] = vt_ph
            i_f0_phasor_red[phase_index] = i_f
            i_t0_phasor_red[phase_index] = i_t
            phase_index += 1

        ih_f_phase, ih_t_phase = rt.initialize_from_fundamental_phasors(
            v_f0_phasor_red=v_f0_phasor_red,
            v_t0_phasor_red=v_t0_phasor_red,
            i_f0_phasor_red=i_f0_phasor_red,
            i_t0_phasor_red=i_t0_phasor_red,
            system_frequency_hz=float(self.grid.fBase),
        )

        phase_index = 0
        while phase_index < rt.m:
            mdl.event_dict[rt.Ih_f[phase_index]] = self.grid.var_factory.add_const(float(np.real(ih_f_phase[phase_index])))
            mdl.event_dict[rt.Ih_t[phase_index]] = self.grid.var_factory.add_const(float(np.real(ih_t_phase[phase_index])))
            phase_index += 1


    # ---------------------------------------------------------------------
    # UTILS
    # ---------------------------------------------------------------------
    def set_if_exists(self,
                      mdl: Block,
                      key: VarPowerFlowReferenceType,
                      value: float,
                      persist_after_native_init: bool = False) -> None:
        """
        Set an initialization value only if the external mapping contains the key.

        :param mdl: Model block containing the external mapping.
        :param key: External mapping key.
        :param value: Initialization value.
        :param persist_after_native_init: Preserve the mapped guess after native initialization.
        :return: None
        """
        external_mapping: Optional[Dict[Any, Var]] = _get_external_mapping(mdl)
        owner_block: Optional[Block]

        if external_mapping is None:
            pass
        else:
            mapped_var: Optional[Var] = external_mapping.get(key, None)

            if mapped_var is None:
                pass
            else:
                # GUI wrapper roots may expose one PF reference whose mutable
                # runtime storage actually belongs to a nested child block.
                # The assignment must therefore target the block that owns the
                # ``event_dict`` entry instead of assuming root ownership.
                owner_block = _find_event_var_owner(mdl, mapped_var)
                if owner_block is None:
                    value_float: float = float(value)
                    self._temp_init_guess[mapped_var.uid] = value_float
                    if persist_after_native_init:
                        self._temp_post_init_guess[mapped_var.uid] = value_float
                    else:
                        pass
                else:
                    owner_block.event_dict[mapped_var] = Const(float(value))
                    if persist_after_native_init:
                        self._temp_post_init_guess[mapped_var.uid] = float(value)
                    else:
                        pass

    def set_internal_init_if_exists(self, mdl: Block, var_name: str, value: float) -> None:
        """
        Set one temporary initial guess for an internal variable if it exists.

        :param mdl: Root model block.
        :param var_name: Internal variable name.
        :param value: Initialization value.
        :return: None.
        """
        internal_var: Optional[Var] = _find_internal_var_for_init(mdl, var_name)

        if internal_var is None:
            pass
        else:
            self._temp_init_guess[internal_var.uid] = float(value)
            self._temp_post_init_guess[internal_var.uid] = float(value)

    def set_internal_mode_if_exists(self, mdl: Block, var_name: str, value: float) -> None:
        """
        Set one retained runtime mode default if the mode variable exists.

        :param mdl: Root model block.
        :param var_name: Retained mode variable name.
        :param value: Runtime mode value.
        :return: None.
        """
        internal_var: Optional[Var]
        owner_block: Optional[Block]

        internal_var, owner_block = _find_mode_var_owner(mdl, var_name)

        if internal_var is None or owner_block is None:
            pass
        else:
            if internal_var in owner_block.mode_dict:
                owner_block.mode_dict[internal_var] = Const(float(value))
                if "_uid2idx_event_params" in self.__dict__ and "_event_params_values" in self.__dict__ and "_event_parameters_eqs" in self.__dict__:
                    runtime_idx: int | None = self._uid2idx_event_params.get(internal_var.uid, None)
                    if runtime_idx is None:
                        pass
                    else:
                        self._event_params_values[runtime_idx] = float(value)
                        self._event_parameters_eqs[runtime_idx] = Const(float(value))
                        if "_runtime_all_eqs_source" in self.__dict__:
                            self._runtime_all_eqs_source[runtime_idx] = Const(float(value))
                        else:
                            pass
                        if "_runtime_parameter_eqs0" in self.__dict__:
                            self._runtime_parameter_eqs0[runtime_idx] = Const(float(value))
                        else:
                            pass
                else:
                    pass
            else:
                pass

    def set_internal_runtime_if_exists(self, mdl: Block, var_name: str, value: float) -> None:
        """
        Set one internal runtime parameter default if the variable exists in ``event_dict``.

        :param mdl: Root model block.
        :param var_name: Runtime parameter variable name.
        :param value: Runtime parameter value.
        :return: None.
        """
        internal_var: Optional[Var]
        owner_block: Optional[Block]
        runtime_idx: int | None

        internal_var, owner_block = _find_internal_runtime_var_owner(mdl, var_name)

        if internal_var is None or owner_block is None:
            pass
        else:
            if internal_var in owner_block.event_dict:
                owner_block.event_dict[internal_var] = Const(float(value))
                if "_uid2idx_event_params" in self.__dict__ and "_event_params_values" in self.__dict__ and "_event_parameters_eqs" in self.__dict__:
                    runtime_idx = self._uid2idx_event_params.get(internal_var.uid, None)
                    if runtime_idx is None:
                        pass
                    else:
                        self._event_params_values[runtime_idx] = float(value)
                        self._event_parameters_eqs[runtime_idx] = Const(float(value))
                        if "_runtime_all_eqs_source" in self.__dict__:
                            self._runtime_all_eqs_source[runtime_idx] = Const(float(value))
                        else:
                            pass
                        if "_runtime_parameter_eqs0" in self.__dict__:
                            self._runtime_parameter_eqs0[runtime_idx] = Const(float(value))
                        else:
                            pass
                else:
                    pass
            else:
                pass

    def set_internal_diff_init_if_exists(self, mdl: Block, var_name: str, value: float) -> None:
        """
        Set one temporary differential initial guess for an internal variable if it exists.

        :param mdl: Root model block.
        :param var_name: Differential variable name.
        :param value: Initialization value.
        :return: None.
        """
        internal_var: Optional[Var] = _find_internal_var_for_init(mdl, var_name)

        if internal_var is None:
            pass
        else:
            self._temp_diff_init_guess[internal_var.uid] = float(value)
            self._temp_post_diff_init_guess[internal_var.uid] = float(value)

    def _seed_switched_converter_internal_init_balanced(
            self,
            mdl: Block,
            VA: complex,
            VB: complex,
            VC: complex,
            IA: complex,
            IB: complex,
            IC: complex,
            v_dc: float,
    ) -> None:
        """
        Seed the internal variables of the switched converter from balanced PF data.

        The switched converter contains additional bridge variables that are not
        part of the external mapping. Seeding them from the PF operating point
        avoids a poor first Newton guess where all bridge voltages start at zero.

        :param mdl: Root converter block.
        :param VA: Phase-A bus voltage phasor.
        :param VB: Phase-B bus voltage phasor.
        :param VC: Phase-C bus voltage phasor.
        :param IA: Phase-A current phasor.
        :param IB: Phase-B current phasor.
        :param IC: Phase-C current phasor.
        :param v_dc: DC-bus magnitude in p.u.
        :return: None.
        """
        model_name: str = str(mdl.name)
        a_operator: complex = np.exp(1j * 2.0 * np.pi / 3.0)
        V1: complex = (VA + a_operator * VB + (a_operator * a_operator) * VC) / 3.0
        phi_v: float = float(np.angle(V1))
        shift: float = 2.0 * np.pi / 3.0
        theta_b: float = phi_v - shift
        theta_c: float = phi_v + shift
        c13: float = 1.0 / 3.0
        c23: float = 2.0 / 3.0
        omega_base: float = 2.0 * np.pi * self.grid.fBase
        i_A0: float = float(np.sqrt(2.0) * np.imag(IA))
        i_B0: float = float(np.sqrt(2.0) * np.imag(IB))
        i_C0: float = float(np.sqrt(2.0) * np.imag(IC))
        i_d0: float = c23 * (np.sin(phi_v) * i_A0 + np.sin(theta_b) * i_B0 + np.sin(theta_c) * i_C0)
        i_q0: float = -c23 * (np.cos(phi_v) * i_A0 + np.cos(theta_b) * i_B0 + np.cos(theta_c) * i_C0)
        i_00: float = c13 * (i_A0 + i_B0 + i_C0)
        Vpk: float = float(np.sqrt(2.0) * np.abs(V1))
        R_eq: float = _get_internal_runtime_default(mdl, f"R_eq_{model_name}", 0.02)
        L_eq: float = _get_internal_runtime_default(mdl, f"L_eq_{model_name}", 0.08)
        m_max: float = _get_internal_runtime_default(mdl, f"m_max_{model_name}", 0.95)
        vdc_floor: float = _get_internal_runtime_default(mdl, f"vdc_floor_{model_name}", 0.05)
        sbase0: float = _get_internal_runtime_default(mdl, f"sbase_{model_name}", self.grid.Sbase)
        control1_code: float = _get_internal_runtime_default(mdl, f"control1_{model_name}", 0.0)
        control2_code: float = _get_internal_runtime_default(mdl, f"control2_{model_name}", 0.0)
        control1_val0: float = _get_internal_runtime_default(mdl, f"control1_val_{model_name}", 0.0)
        control2_val0: float = _get_internal_runtime_default(mdl, f"control2_val_{model_name}", 0.0)
        i_kp0: float = _get_internal_runtime_default(mdl, f"i_kp_{model_name}", 0.0)
        vdc_kp0: float = _get_internal_runtime_default(mdl, f"vdc_kp_{model_name}", 0.0)
        q_kp0: float = _get_internal_runtime_default(mdl, f"q_kp_{model_name}", 0.0)
        eps: float = 1.0e-10
        v_dc_eff: float = max(float(v_dc), vdc_floor)
        P_meas0_pu: float = float(np.real(VA * np.conj(IA) + VB * np.conj(IB) + VC * np.conj(IC)))
        Q_meas0_pu: float = float(np.imag(VA * np.conj(IA) + VB * np.conj(IB) + VC * np.conj(IC)))
        P_meas0: float = P_meas0_pu * sbase0
        i_dc0_conv: float = -P_meas0_pu / max(v_dc_eff, eps)
        configured_p0_value: float = _get_internal_runtime_default(mdl, f"P0_{model_name}", P_meas0)
        P_ref0: float
        Q_ref0: float
        Vdc_ref0: float
        self.set_internal_runtime_if_exists(mdl, f"P0_{model_name}", configured_p0_value)
        P_ref0, Q_ref0, Vdc_ref0 = _resolve_converter_control_reference_values(
            control1_code=control1_code,
            control2_code=control2_code,
            control1_val=control1_val0,
            control2_val=control2_val0,
            p0_value=configured_p0_value,
        )
        P_ref_pu0: float = P_ref0 / max(sbase0, eps)
        Q_ref_pu0: float = Q_ref0 / max(sbase0, eps)
        i_d_ref0: float = (2.0 / 3.0) * P_ref_pu0 / max(Vpk, eps)
        i_q_ref0: float = (2.0 / 3.0) * Q_ref_pu0 / max(Vpk, eps)
        i_0_ref0: float = 0.0

        P_f0: float = P_meas0_pu
        Q_f0: float = Q_meas0_pu
        v_cmd_d0: float = Vpk - R_eq * i_d0 + L_eq * i_q0
        v_cmd_q0: float = -R_eq * i_q0 - L_eq * i_d0
        v_cmd_00: float = -R_eq * i_00
        k_v_conv0: float = float(np.sqrt(v_cmd_d0 * v_cmd_d0 + v_cmd_q0 * v_cmd_q0 + eps) / max(m_max * max(Vdc_ref0, vdc_floor), eps))
        v_ref_a0: float = v_cmd_d0 * np.sin(phi_v) - v_cmd_q0 * np.cos(phi_v) + v_cmd_00
        v_ref_b0: float = v_cmd_d0 * np.sin(theta_b) - v_cmd_q0 * np.cos(theta_b) + v_cmd_00
        v_ref_c0: float = v_cmd_d0 * np.sin(theta_c) - v_cmd_q0 * np.cos(theta_c) + v_cmd_00
        v_mod_scale0: float = max(k_v_conv0 * v_dc_eff, eps)
        m_a_u0: float = v_ref_a0 / v_mod_scale0
        m_b_u0: float = v_ref_b0 / v_mod_scale0
        m_c_u0: float = v_ref_c0 / v_mod_scale0
        m_a0: float = float(np.clip(m_a_u0, -m_max, m_max))
        m_b0: float = float(np.clip(m_b_u0, -m_max, m_max))
        m_c0: float = float(np.clip(m_c_u0, -m_max, m_max))
        desired_v_abc: np.ndarray = np.array([v_ref_a0, v_ref_b0, v_ref_c0], dtype=float)
        best_error: Optional[float] = None
        best_state: np.ndarray = np.zeros(3, dtype=float)
        state_index_a: int = 0
        state_index_b: int
        state_index_c: int

        # The bridge starts from the closest discrete switching state to the desired phase-voltage vector.
        while state_index_a < 2:
            state_index_b = 0
            while state_index_b < 2:
                state_index_c = 0
                while state_index_c < 2:
                    candidate_gate: np.ndarray = np.array([float(state_index_a), float(state_index_b), float(state_index_c)], dtype=float)
                    candidate_leg: np.ndarray = (2.0 * candidate_gate - 1.0) * 0.5 * v_dc_eff
                    candidate_common_mode: float = float(np.sum(candidate_leg) / 3.0)
                    candidate_conv: np.ndarray = candidate_leg - candidate_common_mode
                    candidate_error: float = float(np.sum((candidate_conv - desired_v_abc) ** 2))

                    if best_error is None or candidate_error < best_error:
                        best_error = candidate_error
                        best_state = candidate_gate.copy()
                    else:
                        pass

                    state_index_c += 1
                state_index_b += 1
            state_index_a += 1

        gate_a0 = float(best_state[0])
        gate_b0 = float(best_state[1])
        gate_c0 = float(best_state[2])
        v_leg_a0: float = (2.0 * gate_a0 - 1.0) * 0.5 * v_dc_eff
        v_leg_b0: float = (2.0 * gate_b0 - 1.0) * 0.5 * v_dc_eff
        v_leg_c0: float = (2.0 * gate_c0 - 1.0) * 0.5 * v_dc_eff
        v_common_mode0: float = (v_leg_a0 + v_leg_b0 + v_leg_c0) / 3.0
        v_conv_a0: float = v_leg_a0 - v_common_mode0
        v_conv_b0: float = v_leg_b0 - v_common_mode0
        v_conv_c0: float = v_leg_c0 - v_common_mode0
        v_conv_d0: float = c23 * (np.sin(phi_v) * v_conv_a0 + np.sin(theta_b) * v_conv_b0 + np.sin(theta_c) * v_conv_c0)
        v_conv_q0: float = -c23 * (np.cos(phi_v) * v_conv_a0 + np.cos(theta_b) * v_conv_b0 + np.cos(theta_c) * v_conv_c0)
        v_conv_00: float = c13 * (v_conv_a0 + v_conv_b0 + v_conv_c0)
        switching_enabled0: float = _get_internal_mode_default(mdl, f"switching_enabled_mode_{model_name}", 0.0)
        v_conv_a_applied0: float = (1.0 - switching_enabled0) * v_ref_a0 + switching_enabled0 * v_conv_a0
        v_conv_b_applied0: float = (1.0 - switching_enabled0) * v_ref_b0 + switching_enabled0 * v_conv_b0
        v_conv_c_applied0: float = (1.0 - switching_enabled0) * v_ref_c0 + switching_enabled0 * v_conv_c0
        v_conv_d_applied0: float = (1.0 - switching_enabled0) * v_cmd_d0 + switching_enabled0 * v_conv_d0
        v_conv_q_applied0: float = (1.0 - switching_enabled0) * v_cmd_q0 + switching_enabled0 * v_conv_q0
        v_conv_0_applied0: float = (1.0 - switching_enabled0) * v_cmd_00 + switching_enabled0 * v_conv_00
        v_A0: float = float(np.sqrt(2.0) * np.imag(VA))
        v_B0: float = float(np.sqrt(2.0) * np.imag(VB))
        v_C0: float = float(np.sqrt(2.0) * np.imag(VC))
        i_A0_plant: float = i_A0
        i_B0_plant: float = i_B0
        i_C0_plant: float = i_C0
        i_d0_plant: float = i_d0
        i_q0_plant: float = i_q0
        i_00_plant: float = i_00
        P_loss00: float = _get_internal_runtime_default(mdl, f"P_loss0_{model_name}", 0.0)
        k_v_conv_nom0: float = Vpk / max(m_max * max(Vdc_ref0, vdc_floor), eps)
        i_d_ff0: float = (2.0 / 3.0) * ((P_ref0 + P_loss00) / max(sbase0, eps)) / max(Vpk, eps)
        i_q_ff0: float = (2.0 / 3.0) * (Q_ref0 / max(sbase0, eps)) / max(Vpk, eps)
        xi_vdc0: float = i_d_ref0 - i_d_ff0 - vdc_kp0 * (Vdc_ref0 - v_dc)
        xi_q0: float = i_q_ref0 - i_q_ff0 - q_kp0 * ((Q_ref0 / max(sbase0, eps)) - (Q_f0 / max(sbase0, eps)))
        v_pi_d_u0: float = (Vpk - R_eq * i_d0_plant + L_eq * i_q0_plant) - v_cmd_d0
        v_pi_q_u0: float = (0.0 - R_eq * i_q0_plant - L_eq * i_d0_plant) - v_cmd_q0
        v_pi_00_u0: float = (0.0 - R_eq * i_00_plant) - v_cmd_00
        xi_id0: float = v_pi_d_u0 - i_kp0 * (i_d_ref0 - i_d0_plant)
        xi_iq0: float = v_pi_q_u0 - i_kp0 * (i_q_ref0 - i_q0_plant)
        xi_i00: float = v_pi_00_u0 - i_kp0 * (i_0_ref0 - i_00_plant)
        v_lim0: float = k_v_conv0 * m_max * v_dc_eff
        d_i_d0: float = omega_base * (Vpk - v_conv_d_applied0 - R_eq * i_d0 + L_eq * i_q0) / max(L_eq, eps)
        d_i_q0: float = omega_base * (0.0 - v_conv_q_applied0 - R_eq * i_q0 - L_eq * i_d0) / max(L_eq, eps)
        d_i_00: float = omega_base * (0.0 - v_conv_0_applied0 - R_eq * i_00) / max(L_eq, eps)
        d_i_A0_plant: float = omega_base * (v_conv_a_applied0 - v_A0 - R_eq * i_A0_plant) / max(L_eq, eps)
        d_i_B0_plant: float = omega_base * (v_conv_b_applied0 - v_B0 - R_eq * i_B0_plant) / max(L_eq, eps)
        d_i_C0_plant: float = omega_base * (v_conv_c_applied0 - v_C0 - R_eq * i_C0_plant) / max(L_eq, eps)
        d_xi_id0: float = _get_internal_runtime_default(mdl, f"i_ki_{model_name}", 0.0) * ((i_d_ref0 - i_d0_plant) + _get_internal_runtime_default(mdl, f"aw_gain_{model_name}", 0.0) * (v_cmd_d0 - v_cmd_d0))
        d_xi_iq0: float = _get_internal_runtime_default(mdl, f"i_ki_{model_name}", 0.0) * ((i_q_ref0 - i_q0_plant) + _get_internal_runtime_default(mdl, f"aw_gain_{model_name}", 0.0) * (v_cmd_q0 - v_cmd_q0))
        d_xi_i00: float = _get_internal_runtime_default(mdl, f"i_ki_{model_name}", 0.0) * ((i_0_ref0 - i_00_plant) + _get_internal_runtime_default(mdl, f"aw_gain_{model_name}", 0.0) * (v_cmd_00 - v_cmd_00))

        # The switched bridge and its carrier logic need a coherent first operating point before the first accepted EMT step.
        self.set_internal_init_if_exists(mdl, f"v_dc_{model_name}", v_dc)
        self.set_internal_init_if_exists(mdl, f"i_dc_{model_name}", i_dc0_conv)
        self.set_internal_init_if_exists(mdl, f"i_dc_conv_{model_name}", i_dc0_conv)
        self.set_internal_init_if_exists(mdl, f"P_ref_{model_name}", P_ref0)
        self.set_internal_init_if_exists(mdl, f"Q_ref_{model_name}", Q_ref0)
        self.set_internal_init_if_exists(mdl, f"Vdc_ref_{model_name}", Vdc_ref0)
        self.set_internal_init_if_exists(mdl, f"P_{model_name}", P_meas0_pu)
        self.set_internal_init_if_exists(mdl, f"Q_{model_name}", Q_meas0_pu)
        self.set_internal_init_if_exists(mdl, f"P_f_{model_name}", P_f0)
        self.set_internal_init_if_exists(mdl, f"Q_f_{model_name}", Q_f0)
        self.set_internal_init_if_exists(mdl, f"i_d_ref_{model_name}", i_d_ref0)
        self.set_internal_init_if_exists(mdl, f"i_q_ref_{model_name}", i_q_ref0)
        self.set_internal_init_if_exists(mdl, f"i_0_ref_{model_name}", i_0_ref0)
        self.set_internal_init_if_exists(mdl, f"i_d_ref_u_{model_name}", i_d_ref0)
        self.set_internal_init_if_exists(mdl, f"i_q_ref_u_{model_name}", i_q_ref0)
        self.set_internal_init_if_exists(mdl, f"i_0_ref_u_{model_name}", i_0_ref0)
        self.set_internal_init_if_exists(mdl, f"i_d_ff_{model_name}", i_d_ff0)
        self.set_internal_init_if_exists(mdl, f"i_q_ff_{model_name}", i_q_ff0)
        self.set_internal_init_if_exists(mdl, f"v_mag_{model_name}", Vpk)
        self.set_internal_init_if_exists(mdl, f"k_v_conv_nom_{model_name}", k_v_conv_nom0)
        self.set_internal_init_if_exists(mdl, f"xi_vdc_{model_name}", xi_vdc0)
        self.set_internal_init_if_exists(mdl, f"xi_q_{model_name}", xi_q0)
        self.set_internal_init_if_exists(mdl, f"v_pi_d_u_{model_name}", v_pi_d_u0)
        self.set_internal_init_if_exists(mdl, f"v_pi_q_u_{model_name}", v_pi_q_u0)
        self.set_internal_init_if_exists(mdl, f"v_pi_0_u_{model_name}", v_pi_00_u0)
        self.set_internal_init_if_exists(mdl, f"v_cmd_d_u_{model_name}", v_cmd_d0)
        self.set_internal_init_if_exists(mdl, f"v_cmd_q_u_{model_name}", v_cmd_q0)
        self.set_internal_init_if_exists(mdl, f"v_cmd_0_u_{model_name}", v_cmd_00)
        self.set_internal_init_if_exists(mdl, f"v_lim_{model_name}", v_lim0)
        self.set_internal_init_if_exists(mdl, f"i_d_{model_name}", i_d0)
        self.set_internal_init_if_exists(mdl, f"i_q_{model_name}", i_q0)
        self.set_internal_init_if_exists(mdl, f"i_0_{model_name}", i_00)
        self.set_internal_init_if_exists(mdl, f"v_d_{model_name}", Vpk)
        self.set_internal_init_if_exists(mdl, f"v_q_{model_name}", 0.0)
        self.set_internal_init_if_exists(mdl, f"v_0_{model_name}", 0.0)
        self.set_internal_init_if_exists(mdl, f"v_cmd_d_{model_name}", v_cmd_d0)
        self.set_internal_init_if_exists(mdl, f"v_cmd_q_{model_name}", v_cmd_q0)
        self.set_internal_init_if_exists(mdl, f"v_cmd_0_{model_name}", v_cmd_00)
        self.set_internal_init_if_exists(mdl, f"k_v_conv_{model_name}", k_v_conv0)
        self.set_internal_init_if_exists(mdl, f"v_ref_a_{model_name}", v_ref_a0)
        self.set_internal_init_if_exists(mdl, f"v_ref_b_{model_name}", v_ref_b0)
        self.set_internal_init_if_exists(mdl, f"v_ref_c_{model_name}", v_ref_c0)
        self.set_internal_init_if_exists(mdl, f"m_a_u_{model_name}", m_a_u0)
        self.set_internal_init_if_exists(mdl, f"m_b_u_{model_name}", m_b_u0)
        self.set_internal_init_if_exists(mdl, f"m_c_u_{model_name}", m_c_u0)
        self.set_internal_init_if_exists(mdl, f"m_a_{model_name}", m_a0)
        self.set_internal_init_if_exists(mdl, f"m_b_{model_name}", m_b0)
        self.set_internal_init_if_exists(mdl, f"m_c_{model_name}", m_c0)
        self.set_internal_init_if_exists(mdl, f"i_A_{model_name}", i_A0_plant)
        self.set_internal_init_if_exists(mdl, f"i_B_{model_name}", i_B0_plant)
        self.set_internal_init_if_exists(mdl, f"i_C_{model_name}", i_C0_plant)
        self.set_internal_init_if_exists(mdl, f"gate_a_{model_name}", gate_a0)
        self.set_internal_init_if_exists(mdl, f"gate_b_{model_name}", gate_b0)
        self.set_internal_init_if_exists(mdl, f"gate_c_{model_name}", gate_c0)
        self.set_internal_init_if_exists(mdl, f"v_leg_a_{model_name}", v_leg_a0)
        self.set_internal_init_if_exists(mdl, f"v_leg_b_{model_name}", v_leg_b0)
        self.set_internal_init_if_exists(mdl, f"v_leg_c_{model_name}", v_leg_c0)
        self.set_internal_init_if_exists(mdl, f"v_common_mode_{model_name}", v_common_mode0)
        self.set_internal_init_if_exists(mdl, f"v_conv_a_{model_name}", v_conv_a_applied0)
        self.set_internal_init_if_exists(mdl, f"v_conv_b_{model_name}", v_conv_b_applied0)
        self.set_internal_init_if_exists(mdl, f"v_conv_c_{model_name}", v_conv_c_applied0)
        self.set_internal_init_if_exists(mdl, f"v_conv_d_{model_name}", v_conv_d_applied0)
        self.set_internal_init_if_exists(mdl, f"v_conv_q_{model_name}", v_conv_q_applied0)
        self.set_internal_init_if_exists(mdl, f"v_conv_0_{model_name}", v_conv_0_applied0)
        self.set_internal_init_if_exists(mdl, f"xi_id_{model_name}", xi_id0)
        self.set_internal_init_if_exists(mdl, f"xi_iq_{model_name}", xi_iq0)
        self.set_internal_init_if_exists(mdl, f"xi_i0_{model_name}", xi_i00)
        self.set_internal_mode_if_exists(mdl, f"switching_enabled_mode_{model_name}", switching_enabled0)
        self.set_internal_mode_if_exists(mdl, f"gate_a_mode_{model_name}", gate_a0)
        self.set_internal_mode_if_exists(mdl, f"gate_b_mode_{model_name}", gate_b0)
        self.set_internal_mode_if_exists(mdl, f"gate_c_mode_{model_name}", gate_c0)
        self.set_internal_diff_init_if_exists(mdl, f"d_i_d_{model_name}", d_i_d0)
        self.set_internal_diff_init_if_exists(mdl, f"d_i_q_{model_name}", d_i_q0)
        self.set_internal_diff_init_if_exists(mdl, f"d_i_0_{model_name}", d_i_00)
        self.set_internal_diff_init_if_exists(mdl, f"d_theta_pll_{model_name}", omega_base)

        # The incremental switched-converter path uses a nested ``plant`` and ``plant_bridge`` hierarchy.
        self.set_internal_init_if_exists(mdl, f"i_A_{model_name}_plant", i_A0_plant)
        self.set_internal_init_if_exists(mdl, f"i_B_{model_name}_plant", i_B0_plant)
        self.set_internal_init_if_exists(mdl, f"i_C_{model_name}_plant", i_C0_plant)
        self.set_internal_init_if_exists(mdl, f"i_d_{model_name}_plant", i_d0_plant)
        self.set_internal_init_if_exists(mdl, f"i_q_{model_name}_plant", i_q0_plant)
        self.set_internal_init_if_exists(mdl, f"i_0_{model_name}_plant", i_00_plant)
        self.set_internal_init_if_exists(mdl, f"v_d_{model_name}_plant", Vpk)
        self.set_internal_init_if_exists(mdl, f"v_q_{model_name}_plant", 0.0)
        self.set_internal_init_if_exists(mdl, f"v_0_{model_name}_plant", 0.0)
        self.set_internal_init_if_exists(mdl, f"theta_pll_{model_name}", phi_v)
        self.set_internal_init_if_exists(mdl, f"omega_pll_{model_name}", omega_base)
        self.set_internal_init_if_exists(mdl, f"v_cmd_d_{model_name}", v_cmd_d0)
        self.set_internal_init_if_exists(mdl, f"v_cmd_q_{model_name}", v_cmd_q0)
        self.set_internal_init_if_exists(mdl, f"v_cmd_0_{model_name}", v_cmd_00)
        self.set_internal_diff_init_if_exists(mdl, f"d_i_A_{model_name}_plant", d_i_A0_plant)
        self.set_internal_diff_init_if_exists(mdl, f"d_i_B_{model_name}_plant", d_i_B0_plant)
        self.set_internal_diff_init_if_exists(mdl, f"d_i_C_{model_name}_plant", d_i_C0_plant)
        self.set_internal_diff_init_if_exists(mdl, f"d_xi_id_{model_name}", d_xi_id0)
        self.set_internal_diff_init_if_exists(mdl, f"d_xi_iq_{model_name}", d_xi_iq0)
        self.set_internal_diff_init_if_exists(mdl, f"d_xi_i0_{model_name}", d_xi_i00)

        self.set_internal_init_if_exists(mdl, f"m_a_{model_name}_plant_bridge", m_a0)
        self.set_internal_init_if_exists(mdl, f"m_b_{model_name}_plant_bridge", m_b0)
        self.set_internal_init_if_exists(mdl, f"m_c_{model_name}_plant_bridge", m_c0)
        self.set_internal_init_if_exists(mdl, f"m_a_u_{model_name}_plant_bridge", m_a_u0)
        self.set_internal_init_if_exists(mdl, f"m_b_u_{model_name}_plant_bridge", m_b_u0)
        self.set_internal_init_if_exists(mdl, f"m_c_u_{model_name}_plant_bridge", m_c_u0)

        self.set_internal_init_if_exists(mdl, f"v_ref_a_{model_name}_plant_bridge", v_ref_a0)
        self.set_internal_init_if_exists(mdl, f"v_ref_b_{model_name}_plant_bridge", v_ref_b0)
        self.set_internal_init_if_exists(mdl, f"v_ref_c_{model_name}_plant_bridge", v_ref_c0)
        self.set_internal_init_if_exists(mdl, f"gate_a_{model_name}_plant_bridge", gate_a0)
        self.set_internal_init_if_exists(mdl, f"gate_b_{model_name}_plant_bridge", gate_b0)
        self.set_internal_init_if_exists(mdl, f"gate_c_{model_name}_plant_bridge", gate_c0)
        self.set_internal_init_if_exists(mdl, f"v_leg_a_{model_name}_plant_bridge", v_leg_a0)
        self.set_internal_init_if_exists(mdl, f"v_leg_b_{model_name}_plant_bridge", v_leg_b0)
        self.set_internal_init_if_exists(mdl, f"v_leg_c_{model_name}_plant_bridge", v_leg_c0)
        self.set_internal_init_if_exists(mdl, f"v_common_mode_{model_name}_plant_bridge", v_common_mode0)
        self.set_internal_init_if_exists(mdl, f"v_conv_a_{model_name}_plant_bridge", v_conv_a0)
        self.set_internal_init_if_exists(mdl, f"v_conv_b_{model_name}_plant_bridge", v_conv_b0)
        self.set_internal_init_if_exists(mdl, f"v_conv_c_{model_name}_plant_bridge", v_conv_c0)
        self.set_internal_mode_if_exists(mdl, f"gate_a_mode_{model_name}_plant_bridge", gate_a0)
        self.set_internal_mode_if_exists(mdl, f"gate_b_mode_{model_name}_plant_bridge", gate_b0)
        self.set_internal_mode_if_exists(mdl, f"gate_c_mode_{model_name}_plant_bridge", gate_c0)

    def _seed_all_switched_vsc_models(self) -> None:
        """
        Seed all switched VSC EMT models explicitly from PF results.

        The generic branch initialization path is sufficient for the averaged VSC,
        but the switched converter contains many additional internal bridge/filter
        variables. This explicit pass guarantees that all switched VSC instances
        receive their PF-consistent seeds after the native EMT initialization.

        :return: None.
        """
        bus_idx_dict: Dict[Any, int] = self.grid.get_bus_index_dict()
        vsc_index: int = 0
        vsc: Any
        f_bus_idx: int
        t_bus_idx: int

        while vsc_index < len(self.grid.vsc_devices):
            vsc = self.grid.vsc_devices[vsc_index]
            f_bus_idx = bus_idx_dict[vsc.bus_from]
            t_bus_idx = bus_idx_dict[vsc.bus_to]

            if self.power_flow_results_3ph is not None:
                self._try_set_vsc_branch_pf_init(
                    mdl=self._working_emt_models.get(str(vsc.idtag), vsc.emt_model),
                    f_bus_idx=f_bus_idx,
                    t_bus_idx=t_bus_idx,
                    sbase=self.grid.Sbase,
                    vsc_index=vsc_index,
                )
            else:
                self._try_set_vsc_branch_pf_init_balanced(
                    mdl= self._working_emt_models.get(str(vsc.idtag), vsc.emt_model),
                    f_bus_idx=f_bus_idx,
                    t_bus_idx=t_bus_idx,
                    sbase=self.grid.Sbase,
                    vsc_index=vsc_index,
                )

            vsc_index += 1

    def _seed_all_switch_models(self) -> None:
        """
        Seed all EMT switch models from the static switch active state when requested.

        :return: None.
        """
        branch_obj: Any

        for branch_obj in self.grid.get_branches_iter(add_vsc=True, add_hvdc=True, add_switch=True):
            if branch_obj.device_type == DeviceType.SwitchDevice:
                mdl = self._working_emt_models.get(str(branch_obj.idtag), branch_obj.emt_model)

                if mdl is None:
                    pass
                else:
                    model_name: str = _get_block_name(mdl)
                    seed_from_pf: float = _get_internal_runtime_default(
                        mdl,
                        "switch_seed_from_pf",
                        1.0,
                    )

                    if seed_from_pf > 0.5:
                        initial_closed: float = 1.0 if bool(branch_obj.active) else 0.0
                    else:
                        initial_closed = _get_internal_mode_default(
                            mdl,
                            "switch_closed_mode",
                            1.0,
                        )

                    self.set_internal_mode_if_exists(mdl, "switch_closed_mode", initial_closed)
            else:
                pass

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

    def set_init_guess_and_preserve_post_init(self, mdl: Block, reference_powerflow: Any, val: float) -> None:
        """
        Set one mapped initialization guess and preserve it after native initialization.

        :param mdl: Model block containing the external mapping.
        :param reference_powerflow: Reference key used to locate the mapped variable.
        :param val: Initialization value.
        :return: None.
        """
        external_mapping: Optional[Dict[Any, Var]] = _get_external_mapping(mdl)

        if external_mapping is None:
            pass
        else:
            var: Optional[Var] = external_mapping.get(reference_powerflow, None)

            if var is None:
                pass
            else:
                value_float: float = float(val)
                self._temp_init_guess[var.uid] = value_float
                self._temp_post_init_guess[var.uid] = value_float

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

    def set_external_param(self, mdl: Block, key: VarPowerFlowReferenceType, value: float) -> None:
        """
        Set a PF-derived value either as an event parameter if the mapped variable belongs to mdl.event_dict.
        """
        var: Optional[Any] = _get_external_mapping_var_if_present(mdl=mdl, key=key)
        owner_block: Optional[Block]

        if var is None:
            return
        else:
            pass

        if isinstance(var, Var):
            # GUI wrapper roots often expose the PF reference while the actual
            # mutable runtime parameter lives in a child ``event_dict``. The
            # value must therefore be written to the owning child block.
            owner_block = _find_event_var_owner(mdl, var)
            if owner_block is None:
                pass
            else:
                owner_block.event_dict[var] = Const(float(value))
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
        if len(self._scheduled_mode_events) == 0 and len(self.history_models) == 0 and self._block_boundary_updater is None:
            return None
        else:
            pass

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
        from VeraGridEngine.Utils.procedural_logic import build_boundary_updater_from_block
        self._block_boundary_updater = build_boundary_updater_from_block(self)

        if self._block_boundary_updater is None:
            pass
        else:
            x0: np.ndarray = self.get_x0()

            # Procedural outputs such as sampled modes and saturations are
            # retained runtime parameters. Their startup value must come from
            # evaluating the procedural logic on the initialized operating
            # point, not only from the generic mode_dict seed.
            self._block_boundary_updater.initialize_modes(float(t0), x0, self._event_params_values)

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

        if self._block_boundary_updater is not None:
            # The retained procedural logic reacts after scheduled events so it sees the latest gate commands.
            self._block_boundary_updater.update(t_curr, x_prev, full_params)
        else:
            pass

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
        scheduled_time: Optional[float]
        procedural_time: Optional[float]

        scheduled_time = _get_next_forced_mode_event_time(self._scheduled_mode_events, t_prev, t_target)

        if self._block_boundary_updater is None:
            procedural_time = None
        else:
            procedural_time = self._block_boundary_updater.get_next_forced_event_time(t_prev, t_target)

        # Merge the scheduled and procedural forced-event candidates so the
        # solver advances only to the earliest boundary that requires explicit
        # alignment on the next integration step.
        if scheduled_time is None:
            return procedural_time
        else:
            pass

        if procedural_time is None:
            return scheduled_time
        else:
            pass

        if scheduled_time <= procedural_time:
            return scheduled_time
        else:
            return procedural_time

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

    def get_floquet_jacobian_evaluator(self, default_jacobian_evaluator: Optional[Any] = None) -> Optional[Any]:
        """Return the Jacobian evaluator used by EMT Floquet analysis.

        Subclasses can override this to provide problem-specific Jacobian backends
        while keeping the small-signal driver unchanged.
        """
        return default_jacobian_evaluator

    def _get_or_create_working_emt_model(self, dev: Any) -> Block:
        """
        Return the EMT block used by this EmtProblemDae instance.

        This block is never the grid-owned dev.emt_model object. The copy must
        preserve Var.uid values so grid EMT events that target original Vars still
        match by uid.
        """
        dev_key: str = str(dev.idtag)
        mdl: Block | None = self._working_emt_models.get(dev_key, None)


        if mdl is None:
            mdl = copy.deepcopy(dev.emt_model)
            if mdl.children:
                # Script-built EMT workflows call ``set_emt_model()`` which flattens the
                # connected hierarchy through ``unify_blocks()`` before the model ever reaches
                # the solver. GUI-loaded .veragrid files can preserve the pre-unified wrapper
                # roots instead. The EMT assembly expects the same normalized block shape in
                # both workflows, otherwise wrapper-only metadata can diverge from the actual
                # child equations and produce a structurally singular system.
                mdl.unify_blocks()
                # The unified placeholder rebuilds the block-level collections from the child
                # hierarchy. Re-deriving the external mapping afterwards ensures that EMT
                # initialization seeds the live flattened variables rather than stale wrapper
                # aliases that may no longer participate directly in the residual equations.
                mdl.external_mapping = _collect_external_mapping_from_block(mdl)
                mdl.api_obj_mapping = _collect_api_obj_mapping_from_block(mdl)
            else:
                pass
            self._working_emt_models[dev_key] = mdl
        else:
            pass


        return mdl

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

    def _assign_generator_sharing_targets_from_seed(
            self,
            inj: Any,
            mdl: Block,
            phase_power: np.ndarray,
            generator_count_same_bus: int,
            static_parameter_values_mapping: Dict[Var, Const],
    ) -> None:
        """
        Assign optional sharing references to one generator from its EMT seed.

        The Thevenin generator template accepts total active and reactive power
        references. These are derived from the already computed per-device EMT
        seed so the dynamic controller starts from the same sharing target used
        during the PF-to-EMT initialization.

        :param inj: Generator device.
        :param phase_power: Complex power seed in NABC order.
        :param generator_count_same_bus: Number of generators connected to the same bus.
        :return: None.
        """
        p_ref_value: float = float(np.real(np.sum(phase_power)))
        q_ref_value: float = float(np.imag(np.sum(phase_power)))

        if self.options.verbose:
            print(f"p_ref_value = {p_ref_value} generator {inj}")
            print(f"q_ref_value = {q_ref_value} generator {inj}")

        if generator_count_same_bus > 1:
            share_enable_value: float = 1.0
        else:
            share_enable_value = 0.0

        self._assign_api_mapping_value_if_present(
            mdl=mdl,
            key=ParamPowerFlowReferenceType.generator_share_enable,
            value=share_enable_value,
            static_parameter_values_mapping=static_parameter_values_mapping,
        )
        self._assign_api_mapping_value_if_present(
            mdl=mdl,
            key=ParamPowerFlowReferenceType.generator_share_p_ref,
            value=p_ref_value,
            static_parameter_values_mapping=static_parameter_values_mapping,
        )
        self._assign_event_mapping_value_if_present(
            mdl=mdl,
            key=ParamPowerFlowReferenceType.generator_share_p_ref,
            value=p_ref_value,
        )
        self._assign_api_mapping_value_if_present(
            mdl=mdl,
            key=ParamPowerFlowReferenceType.generator_share_q_ref,
            value=q_ref_value,
            static_parameter_values_mapping=static_parameter_values_mapping,
        )
        self._assign_event_mapping_value_if_present(
            mdl=mdl,
            key=ParamPowerFlowReferenceType.generator_share_q_ref,
            value=q_ref_value,
        )
