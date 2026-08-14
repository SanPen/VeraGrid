# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from abc import ABC
import numpy as np
from typing import Any, Dict, List, Optional, Protocol, Tuple

from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var, hard_sat, heaviside, piecewise, get_expression_vars
from VeraGridEngine.basic_structures import Vec
from VeraGridEngine.Simulations.driver_template import DummySignal
from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.Devices import MultiCircuit
from VeraGridEngine.enumerations import DynamicEventTransitionType, VarPowerFlowReferenceType


def _get_diff_var_sort_key(diff_var: Var) -> int:
    """
    Return the ordering key used to sort differential variables.

    :param diff_var: Differential variable to inspect.
    :return: Sorting key associated with the differential variable.
    """
    return diff_var.diff_order


def _get_external_mapping(mdl: Block) -> Optional[Dict[Any, Var]]:
    """
    Return the external mapping associated with a model block.

    :param mdl: Model block to inspect.
    :return: External mapping dictionary or None.
    """
    external_mapping: Optional[Dict[Any, Var]] = mdl.external_mapping

    if external_mapping is None:
        return None
    else:
        return external_mapping


def _register_referenced_static_parameter_vars(state_eqs: List[Any],
                                               algebraic_eqs: List[Any],
                                               diff_init_eqs: Dict[Var, Any],
                                               init_eqs: Dict[Var, Any],
                                               static_parameter_values: Dict[Var, Const],
                                               known_state_vars: List[Var],
                                               known_algebraic_vars: List[Var],
                                               known_diff_vars: List[Var],
                                               runtime_parameter_vars: List[Var]) -> None:
    """
    Register referenced static parameter vars that are not explicit block members.

    Some EMT templates keep static quantities such as ``omega_base`` outside the
    block ``parameters`` dictionary while still referencing them from state or
    initialization equations. The EMT compiler-name tables are built only from the
    collected states, algebraics, runtime parameters, diff vars, and static
    parameters. This helper therefore scans the device equations and promotes any
    already-known static parameter var into ``static_parameter_values`` when it is
    referenced symbolically but absent from the explicit block collections.

    :param state_eqs: State equations collected from the system block tree.
    :type state_eqs: List[Any]
    :param algebraic_eqs: Algebraic equations collected from the system block tree.
    :type algebraic_eqs: List[Any]
    :param diff_init_eqs: Differential initialization equations.
    :type diff_init_eqs: Dict[Var, Any]
    :param init_eqs: Initialization equations.
    :type init_eqs: Dict[Var, Any]
    :param static_parameter_values: Static parameter mapping being assembled.
    :type static_parameter_values: Dict[Var, Const]
    :param known_state_vars: Collected state variables.
    :type known_state_vars: List[Var]
    :param known_algebraic_vars: Collected algebraic variables.
    :type known_algebraic_vars: List[Var]
    :param known_diff_vars: Collected differential variables.
    :type known_diff_vars: List[Var]
    :param runtime_parameter_vars: Collected runtime parameter variables.
    :type runtime_parameter_vars: List[Var]
    :return: None.
    :rtype: None
    """
    known_uids: set[int] = set()
    static_parameter_value_by_uid: Dict[int, Const] = dict()
    expression_collections: List[List[Any]] = list()
    expression_list: List[Any] = list()
    expression_item: Any
    referenced_var: Var

    for referenced_var in known_state_vars:
        known_uids.add(referenced_var.uid)

    for referenced_var in known_algebraic_vars:
        known_uids.add(referenced_var.uid)

    for referenced_var in known_diff_vars:
        known_uids.add(referenced_var.uid)

    for referenced_var in runtime_parameter_vars:
        known_uids.add(referenced_var.uid)

    for referenced_var in static_parameter_values.keys():
        known_uids.add(referenced_var.uid)
        static_parameter_value_by_uid[referenced_var.uid] = static_parameter_values[referenced_var]

    expression_collections.append(state_eqs)
    expression_collections.append(algebraic_eqs)
    expression_collections.append(list(diff_init_eqs.values()))
    expression_collections.append(list(init_eqs.values()))

    for expression_list in expression_collections:
        for expression_item in expression_list:
            for referenced_var in get_expression_vars(expression_item):
                if referenced_var.uid in known_uids:
                    if referenced_var in static_parameter_values:
                        pass
                    else:
                        static_parameter_value: Const | None = static_parameter_value_by_uid.get(referenced_var.uid, None)
                        if static_parameter_value is None:
                            pass
                        else:
                            static_parameter_values[referenced_var] = static_parameter_value
                else:
                    static_parameter_value = static_parameter_value_by_uid.get(referenced_var.uid, None)
                    if static_parameter_value is None:
                        pass
                    else:
                        static_parameter_values[referenced_var] = static_parameter_value
                        known_uids.add(referenced_var.uid)


def _register_equation_variable_aliases(state_eqs: List[Any],
                                        algebraic_eqs: List[Any],
                                        diff_init_eqs: Dict[Var, Any],
                                        init_eqs: Dict[Var, Any],
                                        compiler_names_dict: Dict[int, str],
                                        alias_names_dict: Dict[int, str]) -> None:
    """
    Register compiler-name aliases for vars referenced only through cloned expressions.

    Saved editor models can preserve symbolic expressions that reference one ``Var``
    instance while the canonical problem collections store another instance with the
    same stable ``uid``. The EMT compilers index by ``uid``, so this helper scans
    the final equations and ensures every referenced uid has one compiler-name entry
    before any expression-to-numba conversion happens.

    :param state_eqs: State equations collected from the system block tree.
    :type state_eqs: List[Any]
    :param algebraic_eqs: Algebraic equations collected from the system block tree.
    :type algebraic_eqs: List[Any]
    :param diff_init_eqs: Differential initialization equations.
    :type diff_init_eqs: Dict[Var, Any]
    :param init_eqs: Initialization equations.
    :type init_eqs: Dict[Var, Any]
    :param compiler_names_dict: Problem compiler-name mapping keyed by uid.
    :type compiler_names_dict: Dict[int, str]
    :param alias_names_dict: Problem alias mapping keyed by uid.
    :type alias_names_dict: Dict[int, str]
    :return: None.
    :rtype: None
    """
    expression_groups: List[List[Any]] = list()
    expression_group: List[Any]
    expression_item: Any
    referenced_var: Var

    expression_groups.append(state_eqs)
    expression_groups.append(algebraic_eqs)
    expression_groups.append(list(diff_init_eqs.values()))
    expression_groups.append(list(init_eqs.values()))

    for expression_group in expression_groups:
        for expression_item in expression_group:
            for referenced_var in get_expression_vars(expression_item):
                if referenced_var.uid in compiler_names_dict:
                    pass
                else:
                    compiler_names_dict[referenced_var.uid] = referenced_var.name
                    alias_names_dict[referenced_var.uid] = referenced_var.name


def _collect_block_tree_sequence(root_block: Block) -> List[Block]:
    """
    Return the symbolic block tree in root-first traversal order.

    :param root_block: Root symbolic block.
    :return: Ordered block list including the root and every descendant.
    """
    ordered_blocks: List[Block] = list()
    pending_blocks: List[Block] = list([root_block])
    pending_index: int = 0
    current_block: Block
    child_block: Block

    while pending_index < len(pending_blocks):
        current_block = pending_blocks[pending_index]
        pending_index += 1
        ordered_blocks.append(current_block)

        for child_block in current_block.children:
            pending_blocks.append(child_block)

    return ordered_blocks


def _collect_hierarchical_init_equations(root_block: Block) -> tuple[Dict[Var, Any], Dict[Var, Any]]:
    """
    Collect initialization equations from the full block hierarchy.

    :param root_block: Root symbolic block.
    :return: Tuple ``(init_eqs, diff_init_eqs)`` merged from the hierarchy.
    """
    block_sequence: List[Block] = _collect_block_tree_sequence(root_block)
    init_eqs: Dict[Var, Any] = dict()
    diff_init_eqs: Dict[Var, Any] = dict()
    block_item: Block
    init_var: Var
    init_expr: Any

    for block_item in block_sequence:
        for init_var, init_expr in block_item.init_eqs.items():
            init_eqs[init_var] = init_expr

        for init_var, init_expr in block_item.diff_init_eqs.items():
            diff_init_eqs[init_var] = init_expr

    return init_eqs, diff_init_eqs


def _collect_hierarchical_runtime_equations(root_block: Block) -> Dict[int, Any]:
    """
    Collect runtime event and mode equations from the full block hierarchy.

    :param root_block: Root symbolic block.
    :return: Runtime equation lookup keyed by variable uid.
    """
    block_sequence: List[Block] = _collect_block_tree_sequence(root_block)
    runtime_equation_lookup: Dict[int, Any] = dict()
    block_item: Block
    runtime_var: Var
    runtime_expr: Any

    for block_item in block_sequence:
        for runtime_var, runtime_expr in block_item.event_dict.items():
            runtime_equation_lookup[runtime_var.uid] = runtime_expr

        for runtime_var, runtime_expr in block_item.mode_dict.items():
            runtime_equation_lookup[runtime_var.uid] = runtime_expr

    return runtime_equation_lookup


class EmtBoundaryUpdateProtocol(Protocol):
    """
    Structural protocol implemented by EMT boundary update providers.
    """

    def update(self, t: float, x: Vec, params: Vec) -> None:
        """
        Update the full parameter vector in place.
        """
        ...

    def get_next_forced_event_time(self, t_prev: float, t_target: float) -> float | None:
        """
        Return the next exact-alignment event time inside ``(t_prev, t_target]``.
        """
        ...


def _implements_forced_event_time_api(boundary_updater: Any) -> bool:
    """
    Return whether one boundary updater type implements ``get_next_forced_event_time``.

    :param boundary_updater: Boundary updater instance.
    :return: ``True`` when the API is implemented.
    """
    updater_type: type = type(boundary_updater)
    base_type: type

    for base_type in updater_type.__mro__:
        if "get_next_forced_event_time" in base_type.__dict__:
            return True
        else:
            pass

    return False


def _emt_event_spec_time_sort_key(event_spec: Dict[str, float | str | None]) -> float:
    """
    Return the sorting key of one EMT runtime-event specification.

    :param event_spec: EMT runtime-event specification.
    :return: Event start time.
    """
    return float(event_spec["time"])


def resolve_solver_boundary_updater(
        problem: "EmtProblemTemplate",
        boundary_updater: EmtBoundaryUpdateProtocol | None,
        t0: float,
) -> EmtBoundaryUpdateProtocol | None:
    """
    Resolve the boundary updater consumed by an EMT solver.

    The problem-owned updater remains the default, but demos and legacy callers
    may still provide external wrappers that only implement ``update()``.
    """
    problem.reset_boundary_update_state(float(t0))

    if boundary_updater is None:
        return problem.boundary_update

    return boundary_updater

def get_solver_forced_event_time(
        boundary_updater: EmtBoundaryUpdateProtocol | None,
        t_prev: float,
        t_target: float,
) -> float | None:
    """
    Query the next forced-alignment event time if the updater exposes it.

    Legacy boundary updaters that only implement ``update()`` are treated as
    having no forced event alignment requirements.
    """
    if boundary_updater is None:
        return None
    else:
        pass

    if _implements_forced_event_time_api(boundary_updater):
        pass
    else:
        return None

    next_time: float | None = boundary_updater.get_next_forced_event_time(float(t_prev), float(t_target))

    if next_time is None:
        return None
    else:
        return float(next_time)


def is_problem_owned_boundary_updater(problem: "EmtProblemTemplate",
                                     boundary_updater: EmtBoundaryUpdateProtocol | None) -> bool:
    """
    Return whether the updater is owned by the EMT problem itself.

    This distinguishes endogenous problem boundary logic from external wrappers
    supplied by tests or demos.
    """
    if boundary_updater is None:
        return False

    if boundary_updater is problem:
        return True

    problem_boundary_updater = problem.boundary_update

    if problem_boundary_updater is None:
        return False

    return boundary_updater is problem_boundary_updater


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


class EmtProblemTemplate(ABC):
    """
    Intermediate layer that manages DAE plumbing including indexing, variable mapping,
    and event updating, regardless of whether the system comes from an electrical
    circuit or a generic mathematical model.
    """

    VARS_NAME = "vars"
    VARIABLE_PARAMS_NAME = "vprms"
    CONSTANT_PARAMS_NAME = "cprms"
    DIFF_NAME = "diff"
    TIME_NAME = "glob_time"

    def __init__(self,
                 sys_block: Block,
                 static_parameter_values_mapping: Dict[Var, Const],
                 glob_time: Var,
                 init_eqs_flat: Dict[Var, Any] | None = None,
                 diff_init_eqs_flat: Dict[Var, Any] | None = None,
                 vars_glob_name2uid: Dict[str, int] | None = None,
                 progress_signal: DummySignal | None = None,
                 progress_text: DummySignal | None = None,
                 )->None:
        """
        Initialize the EMT problem template.

        :param sys_block: Root symbolic block that defines the EMT problem.
        :param glob_time: Global time variable used by runtime expressions.
        :param init_eqs_flat: Optional pre-collected initialization equations.
        :param diff_init_eqs_flat: Optional pre-collected differential initialization equations.
        :param vars_glob_name2uid: Optional pre-collected variable-name lookup.
        :return: None
        """
        super().__init__()
        self.sys_block: Block = sys_block
        existing_grid: MultiCircuit | None
        try:
            existing_grid = self.grid
        except AttributeError:
            existing_grid = None
        self.grid: MultiCircuit | None = existing_grid
        self._glob_time: Var = glob_time
        self._newton_trace_collector: Optional[Any] = None
        self._init_eqs_flat: Dict[Var, Any] = dict()
        self._diff_init_eqs_flat: Dict[Var, Any] = dict()

        block_sequence: List[Block] = _collect_block_tree_sequence(self.sys_block)
        hierarchical_init_eqs: Dict[Var, Any]
        hierarchical_diff_init_eqs: Dict[Var, Any]
        block_item: Block
        runtime_var: Var
        runtime_expr: Any
        const_var: Var
        const_expr: Const

        if init_eqs_flat is None or diff_init_eqs_flat is None:
            hierarchical_init_eqs, hierarchical_diff_init_eqs = _collect_hierarchical_init_equations(self.sys_block)
            self._init_eqs_flat = hierarchical_init_eqs
            self._diff_init_eqs_flat = hierarchical_diff_init_eqs
        else:
            self._init_eqs_flat = dict(init_eqs_flat)
            self._diff_init_eqs_flat = dict(diff_init_eqs_flat)

        self._state_vars: List[Var] = list()
        self._algebraic_vars: List[Var] = list()
        self._state_eqs: List[Any] = list()
        self._algebraic_eqs: List[Any] = list()
        self._diff_vars: List[Var] = list()

        self._static_parameter_values: Dict[Var, Const] = dict()
        static_parameter_values_by_uid: Dict[int, Const] = dict()
        self._variable_parameters: List[Var] = list()
        self._event_parameters_eqs: List[Any] = list()
        self._runtime_mode_uids: set[int] = set()

        for const_var, const_expr in static_parameter_values_mapping.items():
            self._static_parameter_values[const_var] = const_expr
            static_parameter_values_by_uid[const_var.uid] = const_expr

        for block_item in block_sequence:
            self._state_vars.extend(block_item.state_vars)
            self._algebraic_vars.extend(block_item.algebraic_vars)
            self._state_eqs.extend(block_item.state_eqs)
            self._algebraic_eqs.extend(block_item.algebraic_eqs)
            self._diff_vars.extend(block_item.diff_vars)

            for const_var, const_expr in block_item.parameters.items():
                if const_var.uid in static_parameter_values_by_uid:
                    canonical_const_expr: Const = static_parameter_values_by_uid[const_var.uid]
                    self._static_parameter_values[const_var] = canonical_const_expr
                else:
                    self._static_parameter_values[const_var] = const_expr
                    static_parameter_values_by_uid[const_var.uid] = const_expr

            for runtime_var, runtime_expr in block_item.event_dict.items():
                self._variable_parameters.append(runtime_var)
                self._event_parameters_eqs.append(runtime_expr)

            for runtime_var, runtime_expr in block_item.mode_dict.items():
                self._variable_parameters.append(runtime_var)
                self._event_parameters_eqs.append(runtime_expr)
                self._runtime_mode_uids.add(runtime_var.uid)

        # Some EMT templates expose static symbolic quantities through the shared
        # API-object mapping but keep them outside ``block.parameters``. They can
        # still appear inside the final state and initialization equations, so the
        # problem must keep those vars in the constant-parameter set before it
        # builds compiler-name tables.
        _register_referenced_static_parameter_vars(
            state_eqs=self._state_eqs,
            algebraic_eqs=self._algebraic_eqs,
            diff_init_eqs=self._diff_init_eqs_flat,
            init_eqs=self._init_eqs_flat,
            static_parameter_values=self._static_parameter_values,
            known_state_vars=self._state_vars,
            known_algebraic_vars=self._algebraic_vars,
            known_diff_vars=self._diff_vars,
            runtime_parameter_vars=self._variable_parameters,
        )

        self._constant_parameters: List[Var] = list(self._static_parameter_values.keys())
        self._parameters_values: List[Const] = list(self._static_parameter_values.values())

        self._runtime_all_parameters_source: List[Var] = list(self._variable_parameters)
        self._runtime_all_eqs_source: List[Any] = list(self._event_parameters_eqs)

        self._runtime_continuous_parameters: List[Var] = list()
        self._runtime_mode_parameters: List[Var] = list()

        self._runtime_continuous_eqs: List[Any] = list()
        self._runtime_mode_eqs: List[Any] = list()

        self._runtime_continuous_slice: slice = slice(0, 0)
        self._runtime_mode_slice: slice = slice(0, 0)

        if vars_glob_name2uid is None:
            self._vars_glob_name2uid: Dict[str, int] = dict()
        else:
            self._vars_glob_name2uid = dict(vars_glob_name2uid)

        self._rebuild_runtime_parameter_partition()

        self.init_guess: Dict[int, float] = dict()
        self.event_params_init_dict: Dict[int, float | int | complex | None] = dict()
        self.diff_init_guess: Dict[int, float] = dict()
        # self._vars_info: Dict[Any, List[Var]] = dict()

        self._finalize_order_and_maps()
        self._event_params_values: Vec = np.zeros(0, dtype=np.float64)
        self._constant_params_values: Vec = np.zeros(0, dtype=np.float64)
        self._build_runtime_param_vectors()

        self.progress_signal = DummySignal() if progress_signal is None else progress_signal
        self.progress_text = DummySignal(str) if progress_text is None else progress_text

    @property
    def glob_time(self) -> Var:
        """
        Return the global time symbolic variable.

        :return: Global time symbolic variable.
        """
        return self._glob_time

    @property
    def boundary_update(self) -> EmtBoundaryUpdateProtocol | None:
        """
        Return the boundary update provider consumed by EMT solvers.

        Problems without endogenous boundary logic return ``None``.
        """
        return None

    def report_progress(self, val: float) -> None:
        """
        Emit one absolute progress update.

        :param val: Progress value in percent.
        :type val: float
        :return: None
        :rtype: None
        """
        if self.progress_signal is not None:
            self.progress_signal.emit(val)
        else:
            pass

    def report_progress2(self, current: int, total: int) -> None:
        """
        Emit one progress update from a zero-based iteration index.

        :param current: Zero-based iteration index.
        :type current: int
        :param total: Total number of iterations.
        :type total: int
        :return: None
        :rtype: None
        """
        if self.progress_signal is not None:
            val: float = ((current + 1) / total) * 100
            self.progress_signal.emit(val)
        else:
            pass

    def _finalize_order_and_maps(self)->None:
        """
        Build canonical ordering, index maps and internal counters.

        :return: None
        """

        parameter_var: Var
        parameter_value: Const

        # The unified EMT builder may assemble wrapped models where the final
        # flattened ``sys_block`` owns static parameter vars that were not present
        # in the earlier pre-flattened mapping snapshot. Reconcile against the
        # definitive unified parameter dictionary here so every referenced static
        # var receives one constant-array slot before symbolic compilation.
        for parameter_var, parameter_value in self.sys_block.parameters.items():
            if parameter_var in self._static_parameter_values:
                pass
            else:
                self._static_parameter_values[parameter_var] = parameter_value

        self._constant_parameters = list(self._static_parameter_values.keys())
        self._parameters_values = list(self._static_parameter_values.values())

        self._diff_vars = sorted(self._diff_vars, key=_get_diff_var_sort_key)

        self._n_state = len(self._state_vars)
        self._n_alg = len(self._algebraic_vars)
        self._n_vars = self._n_state + self._n_alg
        self._n_event_params = len(self._variable_parameters)
        self._n_params = len(self._constant_parameters)
        self._n_diff = len(self._diff_vars)
        self._n_algebraic = len(self._algebraic_eqs)

        self._compiler_names_dict: Dict[int, str] = dict()
        self._alias_names_dict: Dict[int, str] = dict()
        self._uid2idx_vars: Dict[int, int] = dict()
        self._uid2idx_event_params: Dict[int, int] = dict()
        self._uid2idx_params: Dict[int, int] = dict()
        self._uid2idx_diff: Dict[int, int] = dict()
        self._uid2idx_t: Dict[int, int] = dict()

        self._vars_glob_name2uid = dict(self._vars_glob_name2uid)

        i: int = 0
        for v in self._state_vars:
            self._compiler_names_dict[v.uid] = f"{self.VARS_NAME}[{i}]"
            self._alias_names_dict[v.uid] = f"{self.VARS_NAME}_{i}"
            self._uid2idx_vars[v.uid] = i
            if v.name in self._vars_glob_name2uid:
                pass
            else:
                self._vars_glob_name2uid[v.name] = v.uid
            i += 1

        for v in self._algebraic_vars:
            self._compiler_names_dict[v.uid] = f"{self.VARS_NAME}[{i}]"
            self._alias_names_dict[v.uid] = f"{self.VARS_NAME}_{i}"
            self._uid2idx_vars[v.uid] = i
            if v.name in self._vars_glob_name2uid:
                pass
            else:
                self._vars_glob_name2uid[v.name] = v.uid
            i += 1

        for j, p in enumerate(self._constant_parameters):
            self._compiler_names_dict[p.uid] = f"{self.CONSTANT_PARAMS_NAME}[{j}]"
            self._alias_names_dict[p.uid] = f"{self.CONSTANT_PARAMS_NAME}_{j}"
            self._uid2idx_params[p.uid] = j

        for k, p in enumerate(self._variable_parameters):
            self._compiler_names_dict[p.uid] = f"{self.VARIABLE_PARAMS_NAME}[{k}]"
            self._alias_names_dict[p.uid] = f"{self.VARIABLE_PARAMS_NAME}_{k}"
            self._uid2idx_event_params[p.uid] = k

        for k, d in enumerate(self._diff_vars):
            self._compiler_names_dict[d.uid] = f"{self.DIFF_NAME}[{k}]"
            self._alias_names_dict[d.uid] = f"{self.DIFF_NAME}_{k}"
            self._uid2idx_diff[d.uid] = k
            if d.name in self._vars_glob_name2uid:
                pass
            else:
                self._vars_glob_name2uid[d.name] = d.uid

        # Saved editor models can keep equation trees that still reference cloned
        # ``Var`` objects carrying the same uid as the canonical problem vars or
        # static parameters. Populate any missing uid-based compiler aliases from
        # the final equations so expression compilation stays robust after model
        # round-trips through the editor.
        _register_equation_variable_aliases(
            state_eqs=self._state_eqs,
            algebraic_eqs=self._algebraic_eqs,
            diff_init_eqs=self._diff_init_eqs_flat,
            init_eqs=self._init_eqs_flat,
            compiler_names_dict=self._compiler_names_dict,
            alias_names_dict=self._alias_names_dict,
        )

        self._compiler_names_dict[self._glob_time.uid] = self.TIME_NAME
        self._uid2idx_t[self._glob_time.uid] = 0

    def _build_runtime_param_vectors(self) -> None:
        """
        Build and initialize runtime and constant parameter buffers.

        Runtime parameters are kept in a single flat vector. Continuous and mode
        families are only distinguished by slices and by the update rules applied
        later during the simulation.

        :return: None
        """
        n_runtime: int = self.get_variable_parameter_number()

        self._event_params_values = np.zeros(n_runtime, dtype=np.float64)

        if n_runtime > 0:
            self._event_params_values = self._initialize_runtime_parameter_values(0.0, seed_values=self._event_params_values)
            self._event_params_values = self.def_event_params_fn(self._event_params_values, 0.0)
        else:
            pass

        self._constant_params_values = np.array(
            [parameter.value for parameter in self._parameters_values],
            dtype=np.float64
        )

    def rebuild_runtime_param_vectors(self) -> None:
        """
        Rebuild the runtime and constant parameter buffers.

        :return: None
        """
        self._build_runtime_param_vectors()

    def set_events_group(self, emt_events_group: EmtEventsGroup | None) -> None:
        """Apply a selected EMT events group to the runtime parameter equations.

        The method is generic with respect to the specific EMT templates used in the
        problem. Any runtime parameter exposed through `event_dict` / `mode_dict`
        can be reassigned with a piecewise time function driven by the selected
        group of `grid.emt_events`.
        """
        active_runtime_eqs = list(self._runtime_all_eqs_source)

        collect_events = {param.uid: list() for param in self._variable_parameters}
        uid_to_parameter = {param.uid: param for param in self._variable_parameters}
        if self.grid is None:
            emt_events = list()
        else:
            emt_events = self.grid.emt_events

        if emt_events_group is None:
            selected_events = list()
        else:
            selected_events = [
                evt for evt in emt_events
                if evt.group is not None and evt.group.idtag == emt_events_group.idtag
            ]

        for emt_evt in selected_events:
            parameter = emt_evt.parameter
            parameter_uid = parameter.uid if isinstance(parameter, Var) else None

            if parameter_uid in collect_events:
                transition_type: DynamicEventTransitionType = emt_evt.transition_type
                end_time = emt_evt.end_time

                collect_events[parameter_uid].append(
                    dict({
                        "time": float(emt_evt.time),
                        "value": float(emt_evt.value),
                        "end_time": None if end_time is None else float(end_time),
                        "transition_type": transition_type,
                    })
                )

        for parameter_uid, event_specs in collect_events.items():
            if len(event_specs) == 0:
                pass
            else:
                parameter = uid_to_parameter[parameter_uid]
                param_index = self._variable_parameters.index(parameter)
                active_expr = active_runtime_eqs[param_index]
                sorted_specs = sorted(event_specs, key=_emt_event_spec_time_sort_key)

                for event_spec in sorted_specs:
                    if event_spec["transition_type"] == DynamicEventTransitionType.Ramp:
                        start_time = float(event_spec["time"])
                        end_time_raw = event_spec["end_time"]

                        if end_time_raw is None:
                            raise ValueError("Ramp EMT events require an end_time")
                        else:
                            pass

                        end_time = float(end_time_raw)

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
                            new_values=np.asarray([float(event_spec["value"] )], dtype=np.float64),
                            default_value=active_expr,
                        )

                active_runtime_eqs[param_index] = active_expr

        self._runtime_all_eqs_source = active_runtime_eqs
        self._rebuild_runtime_parameter_partition()
        self._build_runtime_param_vectors()

    def reset_boundary_update_state(self, t0: float = 0.0) -> None:
        """
        Reset runtime parameter values before a new EMT simulation starts.

        :param t0: Initial simulation time.
        :return: None
        """
        self._event_params_values = self._initialize_runtime_parameter_values(float(t0), seed_values=self._event_params_values)
        self._event_params_values = self.def_event_params_fn(self._event_params_values, float(t0))

    def get_compiler_names_dict(self) -> Dict[int, str]:
        """
        Return the compiler-name mapping used by symbolic kernels.

        :return: Compiler-name dictionary.
        """
        return dict(self._compiler_names_dict)

    def get_alias_names_dict(self) -> Dict[int, str]:
        """
        Return the alias-name mapping used by symbolic kernels.

        :return: Alias-name dictionary.
        """
        return dict(self._alias_names_dict)

    def get_event_parameter_equations(self) -> List[Any]:
        """
        Return the runtime event-parameter equations.

        :return: Event-parameter equations.
        """
        return list(self._event_parameters_eqs)

    def _rebuild_runtime_parameter_partition(self) -> None:
        """
        Rebuild the runtime parameter partition.

        The runtime parameters are stored in a single flat vector, but their
        order is redefined so that continuous runtime inputs appear first and
        retained discrete mode parameters appear afterwards.

        :return: None
        """
        self._runtime_continuous_parameters = list()
        self._runtime_mode_parameters = list()

        self._runtime_continuous_eqs = list()
        self._runtime_mode_eqs = list()

        n_source: int = len(self._runtime_all_parameters_source)
        i: int = 0

        while i < n_source:
            parameter: Var = self._runtime_all_parameters_source[i]
            equation: Any = self._runtime_all_eqs_source[i]

            if parameter.uid in self._runtime_mode_uids:
                self._runtime_mode_parameters.append(parameter)
                self._runtime_mode_eqs.append(equation)
            else:
                self._runtime_continuous_parameters.append(parameter)
                self._runtime_continuous_eqs.append(equation)

            i += 1

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

        n_continuous: int = len(self._runtime_continuous_parameters)
        n_mode: int = len(self._runtime_mode_parameters)

        self._runtime_continuous_slice = slice(0, n_continuous)
        self._runtime_mode_slice = slice(n_continuous, n_continuous + n_mode)

    def refresh_runtime_equations_from_hierarchy(self) -> None:
        """
        Refresh canonical runtime equations from the current block hierarchy.

        :return: None
        """
        runtime_equation_lookup: Dict[int, Any] = _collect_hierarchical_runtime_equations(self.sys_block)
        refreshed_equations: List[Any] = list()
        runtime_parameter: Var

        for runtime_parameter in self._runtime_all_parameters_source:
            if runtime_parameter.uid in runtime_equation_lookup:
                refreshed_equations.append(runtime_equation_lookup[runtime_parameter.uid])
            else:
                runtime_idx: int | None = self.uid2idx_event_params.get(runtime_parameter.uid, None) if hasattr(self, 'uid2idx_event_params') else None
                if runtime_idx is None or runtime_idx >= len(self._event_parameters_eqs):
                    refreshed_equations.append(Const(None))
                else:
                    refreshed_equations.append(self._event_parameters_eqs[runtime_idx])

        self._runtime_all_eqs_source = refreshed_equations
        self._rebuild_runtime_parameter_partition()

    def set_runtime_mode_parameters(self, mode_parameters: List[Var]) -> None:
        """
        Classify a subset of runtime parameters as retained discrete mode parameters.

        The physical storage remains a single flat runtime vector. This method
        only changes the semantic partition and rebuilds the associated index maps
        and runtime initialization buffers.

        :param mode_parameters: Runtime parameters to classify as mode parameters.
        :return: None
        """
        valid_runtime_uids: set[int] = set()
        selected_mode_uids: set[int] = set()

        for parameter in self._runtime_all_parameters_source:
            valid_runtime_uids.add(parameter.uid)

        for parameter in mode_parameters:
            if parameter.uid in valid_runtime_uids:
                selected_mode_uids.add(parameter.uid)
            else:
                raise KeyError(
                    f"Runtime mode parameter uid={parameter.uid} does not belong to the runtime parameter source."
                )

        self._runtime_mode_uids = selected_mode_uids
        self._rebuild_runtime_parameter_partition()
        self._finalize_order_and_maps()
        self._build_runtime_param_vectors()

    def _initialize_runtime_parameter_values(self, tm: float, seed_values: Optional[Vec] = None) -> Vec:
        """
        Initialize the flat runtime parameter vector at a given time.

        This method evaluates the full runtime parameter list once in the final
        flat order. It is used for initialization only. Continuous parameters are
        then refined afterwards by def_event_params_fn().

        :param tm: Initialization time.
        :return: Initialized runtime parameter vector.
        """
        n_runtime: int = len(self._variable_parameters)
        out: Vec = np.zeros(n_runtime, dtype=np.float64)

        if seed_values is None:
            pass
        else:
            n_seed: int = min(len(seed_values), n_runtime)
            out[:n_seed] = seed_values[:n_seed]

        i: int = 0
        while i < n_runtime:
            expression: Any = self._event_parameters_eqs[i]
            if isinstance(expression, Const) and expression.value is None:
                out[i] = float(out[i])
            else:
                out[i] = self._evaluate_runtime_expression(expression, out, tm)
            i += 1

        return out

    def _evaluate_runtime_expression(self, expression: Any, runtime_params: Vec, tm: float) -> float:
        """
        Evaluate a runtime parameter expression.

        The evaluation uses UID-based bindings to avoid ambiguous name-based
        dispatch and to keep the runtime parameter update logic deterministic.

        :param expression: Symbolic or numeric expression.
        :param runtime_params: Current flat runtime parameter vector.
        :param tm: Current time.
        :return: Numeric value of the expression.
        """
        if isinstance(expression, Const):
            if expression.value is None:
                return 0.0
            else:
                return float(expression.value)

        elif isinstance(expression, Var):
            if expression.uid == self._glob_time.uid or expression.name in {"time", self.TIME_NAME}:
                return float(tm)
            else:
                idx_runtime: int | None = self._uid2idx_event_params.get(expression.uid, None)
                if idx_runtime is not None:
                    return float(runtime_params[idx_runtime])
                else:
                    idx_const: int | None = self._uid2idx_params.get(expression.uid, None)
                    if idx_const is not None:
                        return float(self._parameters_values[idx_const].value)
                    else:
                        idx_var: int | None = self._uid2idx_vars.get(expression.uid, None)
                        if idx_var is not None:
                            init_value: float | int | complex | None = self.init_guess.get(expression.uid, None)
                            if init_value is None:
                                return 0.0
                            else:
                                return float(init_value)
                        else:
                            idx_diff: int | None = self._uid2idx_diff.get(expression.uid, None)
                            if idx_diff is not None:
                                diff_init_value: float | int | complex | None = self.diff_init_guess.get(expression.uid, None)
                                if diff_init_value is None:
                                    return 0.0
                                else:
                                    return float(diff_init_value)
                            else:
                                return 0.0

        elif isinstance(expression, Expr):
            uid_bindings: Dict[int, float] = dict()
            uid: int
            idx: int
            init_value: float | int | complex | None
            diff_init_value: float | int | complex | None
            var: Var

            for uid, idx in self._uid2idx_event_params.items():
                uid_bindings[uid] = float(runtime_params[idx])

            for uid, idx in self._uid2idx_params.items():
                uid_bindings[uid] = float(self._parameters_values[idx].value)

            # Runtime mode parameters such as delayed outputs may depend on the
            # already initialized algebraic, state, and differential values of
            # the EMT problem. The broader explicit-initialization algorithm has
            # already assembled those guesses before this runtime initialization
            # stage runs, so we expose them here as UID bindings. This lets one
            # retained mode variable start from the same operating point as the
            # algebraic signal it delays.
            for uid, idx in self._uid2idx_vars.items():
                init_value = self.init_guess.get(uid, None)
                if init_value is None:
                    pass
                else:
                    uid_bindings[uid] = float(init_value)

            for uid, idx in self._uid2idx_diff.items():
                diff_init_value = self.diff_init_guess.get(uid, None)
                if diff_init_value is None:
                    pass
                else:
                    uid_bindings[uid] = float(diff_init_value)

            uid_bindings[self._glob_time.uid] = float(tm)
            for var in expression.get_vars():
                if var.name in {"time", self.TIME_NAME}:
                    uid_bindings[var.uid] = float(tm)

            return float(expression.eval_uid(uid_bindings))

        else:
            return float(expression)


    def get_state_vars(self)->List[Var]:
        """
        Return the ordered list of state variables.

        :return: Ordered list of state variables.
        """
        return self._state_vars


    def get_algebraic_vars(self)->List[Var]:
        """
        Return the ordered list of algebraic variables.

        :return: Ordered list of algebraic variables.
        """
        return self._algebraic_vars

    def state_and_algebraic_vars(self) -> List[Var]:
        """
        :return:
        """
        variables = list()
        for lst in [self._state_vars, self._algebraic_vars]:
            for var in lst:
                variables.append(var)

        return variables


    def get_state_eqs(self)->List[Any]:
        """
        Return the ordered list of state equations.

        :return: Ordered list of state equations.
        """
        return self._state_eqs


    def get_algebraic_eqs(self)->List[Any]:
        """
        Return the ordered list of algebraic equations.

        :return: Ordered list of algebraic equations.
        """
        return self._algebraic_eqs


    def get_variable_parameters(self)-> List[Var]:
        """
        Return the ordered list of runtime parameters.

        :return: Ordered list of runtime parameters.
        """
        return self._variable_parameters


    def get_constant_parameters(self)-> List[Var]:
        """
        Return the ordered list of constant parameters.

        :return: Ordered list of constant parameters.
        """
        return self._constant_parameters


    def get_diff_vars(self)-> List[Var]:
        """
        Return the ordered list of differential variables.

        :return: Ordered list of differential variables.
        """
        return self._diff_vars


    def get_parameters_values(self)-> List[Const]:
        """
        Return the ordered list of constant parameter values.

        :return: Ordered list of constant parameter values.
        """
        return self._parameters_values

    def get_all_vars_number(self) -> int:
        """
        Return the total number of state and algebraic variables.

        :return: Total number of variables.
        """
        return self._n_vars

    def get_diff_var_number(self) -> int:
        """
        Return the number of differential variables.

        :return: Number of differential variables.
        """
        return self._n_diff

    def get_algebraic_var_number(self) -> int:
        """
        Return the number of algebraic variables.

        :return: Number of algebraic variables.
        """
        return self._n_alg

    def get_states_number(self) -> int:
        """
        Return the number of state variables.

        :return: Number of state variables.
        """
        return self._n_state

    def get_variable_parameter_number(self) -> int:
        """
        Return the number of runtime parameters.

        :return: Number of runtime parameters.
        """
        return self._n_event_params

    def get_x0(self) -> Vec:
        """
        Build the initial state vector from the stored initialization guess.

        :return: Initial state vector.
        """
        x = np.zeros(self._n_vars, dtype=np.float64)
        for uid, val in self.init_guess.items():
            idx = self._uid2idx_vars.get(uid, None)
            if idx is not None:
                value_float: float = float(val)
                if np.isfinite(value_float):
                    x[idx] = value_float
                else:
                    pass
            else:
                pass

        return x

    def get_dx0(self) -> Vec:
        """
        Build the initial differential vector from the stored differential initialization guess.

        :return: Initial differential vector.
        """
        dx = np.zeros(self._n_diff, dtype=np.float64)
        for uid, val in self.diff_init_guess.items():
            idx = self._uid2idx_diff.get(uid, None)
            if idx is not None:
                value_float: float = float(val)
                if np.isfinite(value_float):
                    dx[idx] = value_float
                else:
                    pass
            else:
                pass
        return dx

    def def_event_params_fn(self, ev_param: Vec, tm: float) -> Vec:
        """
        Update only the continuous runtime parameter slice.

        Retained discrete mode parameters are preserved exactly as they enter
        this function. They are expected to be modified explicitly by the
        boundary update layer or by future event logic.

        :param ev_param: Current flat runtime parameter vector.
        :param tm: Current simulation time.
        :return: Updated flat runtime parameter vector.
        """
        n_continuous: int = len(self._runtime_continuous_eqs)

        if n_continuous == 0:
            return ev_param
        else:
            out: Vec = ev_param.copy()

            i: int = 0
            while i < n_continuous:
                global_idx: int = self._runtime_continuous_slice.start + i
                expression: Any = self._runtime_continuous_eqs[i]

                out[global_idx] = self._evaluate_runtime_expression(expression, out, tm)
                i += 1

            return out

    def update_variable_params(self, t: float) -> None:
        """
        Update the internal runtime parameter values at the given time.

        :param t: Current time.
        :return: None
        """
        self._event_params_values = self.def_event_params_fn(self._event_params_values, float(t))

    def get_full_param_index(self, uid: int) -> int:
        """
        Return the flat full-parameter index associated with the given UID.

        :param uid: Parameter unique identifier.
        :return: Flat index inside the full parameter vector.
        """
        n_ev = len(self._variable_parameters)
        if uid in self._uid2idx_event_params:
            return self._uid2idx_event_params[uid]
        if uid in self._uid2idx_params:
            return n_ev + self._uid2idx_params[uid]
        raise KeyError(f"Unknown param uid={uid}")

    def get_newton_trace_collector(self) -> Optional[Any]:
        """
        Return the Newton trace collector instance.

        :return: Newton trace collector instance or None.
        """
        return self._newton_trace_collector

    def set_newton_trace_collector(self, collector: Any)->None:
        """
        Set the Newton trace collector instance.

        :param collector: Newton trace collector instance.
        :return: None
        """
        self._newton_trace_collector = collector

    # def get_device_vars_dict(self) -> Dict[Any, List[Var]]:
    #     """
    #     Return the device-to-variable mapping dictionary.
    #
    #     :return: Device-to-variable mapping dictionary.
    #     """
    #     return self._vars_info

    def get_var_idx(self, v: Var) -> int:
        """
        Return the flat variable index associated with the given variable.

        :param v: Variable to locate.
        :return: Flat variable index.
        """
        return self._uid2idx_vars[v.uid]

    def get_diff_var_idx(self, dv: Var) -> int:
        """
        Return the flat differential index associated with the given differential variable.

        :param dv: Differential variable to locate.
        :return: Flat differential index.
        """
        return self._uid2idx_diff[dv.uid]

    @property
    def vars_glob_name2uid(self) -> Dict[str, int]:
        """
        :return:
        """
        return self._vars_glob_name2uid

    # def set_init_guess(self, mdl: Block, reference_powerflow: VarPowerFlowReferenceType, val: float) -> None:
    #     """
    #     Set the initialization guess associated with a model external mapping.
    #
    #     :param mdl: Model block containing the external mapping.
    #     :param reference_powerflow: Reference key used to locate the mapped variable.
    #     :param val: Initialization value.
    #     :return: None
    #     """
    #     external_mapping: Optional[Dict[Any, Var]] = _get_external_mapping(mdl)
    #
    #     if external_mapping is None:
    #         pass
    #     else:
    #         var: Optional[Var] = external_mapping.get(reference_powerflow, None)
    #
    #         if var is None:
    #             pass
    #         else:
    #             self.init_guess[var.uid] = float(val)



    def get_floquet_ak_stack(
            self,
            trajectory: np.ndarray,
            h: float,
            jac_evaluator: Optional[Any] = None,
            static_params: Optional[Vec] = None
    ) -> Optional[np.ndarray]:
        """
        Return the stack of transition matrices used for Floquet analysis.

        :param trajectory: State trajectory over one period.
        :param h: Time step.
        :param jac_evaluator: Optional Jacobian evaluator.
        :param static_params: Optional static parameter vector.
        :return: Stack of transition matrices or None.
        """
        return None

    def get_runtime_continuous_slice(self) -> slice:
        """
        Return the slice of continuous runtime inputs inside the flat runtime vector.

        :return: Continuous runtime slice.
        """
        return self._runtime_continuous_slice

    def get_runtime_mode_slice(self) -> slice:
        """
        Return the slice of retained mode parameters inside the flat runtime vector.

        :return: Mode runtime slice.
        """
        return self._runtime_mode_slice

    def get_runtime_continuous_parameters(self) -> List[Var]:
        """
        Return the ordered list of continuous runtime parameters.

        :return: Continuous runtime parameters.
        """
        return self._runtime_continuous_parameters

    def get_runtime_mode_parameters(self) -> List[Var]:
        """
        Return the ordered list of retained mode runtime parameters.

        :return: Mode runtime parameters.
        """
        return self._runtime_mode_parameters

    @property
    def uid2idx_vars(self)-> Dict[int, int]:
        """
        Return the UID-to-variable-index mapping.

        :return: UID-to-variable-index mapping.
        """
        return self._uid2idx_vars

    @property
    def uid2idx_params(self)-> Dict[int, int]:
        """
        Return the UID-to-constant-parameter-index mapping.

        :return: UID-to-constant-parameter-index mapping.
        """
        return self._uid2idx_params

    @property
    def uid2idx_event_params(self)-> Dict[int, int]:
        """
        Return the UID-to-runtime-parameter-index mapping.

        :return: UID-to-runtime-parameter-index mapping.
        """
        return self._uid2idx_event_params

    @property
    def uid2idx_diff(self)-> Dict[int, int]:
        """
        Return the UID-to-differential-index mapping.

        :return: UID-to-differential-index mapping.
        """
        return self._uid2idx_diff

    @property
    def event_params_values(self)-> Vec:
        """
        Return the current flat runtime parameter vector.

        :return: Current flat runtime parameter vector.
        """
        return self._event_params_values

    @property
    def event_parameters_eqs(self) -> List[Any]:
        return self._event_parameters_eqs



