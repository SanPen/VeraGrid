# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
from VeraGridEngine.Utils.NumericalMethods.newton_factor_reuse import (
    get_adaptive_recompute_threshold, needs_confirming_correction,
    confirms_with_fresh_factors, factorization_inputs_changed, needs_factor_refresh,
)
import numba as nb
import cProfile as profile
import time
from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import SparseLinearSolverBackendProvider
from VeraGridEngine.Utils.NumericalMethods.emt_sparse_superlu_backend import SuperLUSparseBackendProvider
from VeraGridEngine.Utils.Sparse.sparse_solve import SparseProviderLinearSolver, solve_sparse_system_once
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Expr, BinOp, UnOp, Func

from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import (
    BoundaryUpdaterCapabilities,
    EmtBoundaryUpdateProtocol,
    EmtProblemTemplate,
    get_solver_forced_event_time,
    is_problem_owned_boundary_updater,
    resolve_solver_boundary_step,
    resolve_solver_boundary_updater,
)
from VeraGridEngine.enumerations import DynamicIntegrationMethod

from VeraGridEngine.Utils.Symbolic.jit_compiler import EagerEquationCompiler, EquationCompiler
from VeraGridEngine.Utils.Symbolic.diagnostic import (with_newton_diagnostics, NewtonDiagnosticsConfig,
                                                       NewtonSolveContext, dense_lstsq_fallback,
                                                         sparse_lsqr_fallback, maybe_check_index1,
                                                         maybe_apply_backtracking)
from VeraGridEngine.Simulations.driver_template import DummySignal
from VeraGridEngine.basic_structures import Vec, Mat
from typing import Tuple, Callable, List, Any, Dict, Set, Union
from scipy.sparse import csc_matrix

def _safe_njit(py_func: Callable[..., Any], fastmath: bool = True, cache: bool = True, signature: Any = None) -> Callable[..., Any]:
    """
    Safely wraps a python function with Numba's njit compiler.
    The caller must explicitly pass cache=False if the function is generated via strings.

    :param py_func: The python function to compile.
    :type py_func: Callable[..., Any]
    :param fastmath: Flag to enable fastmath operations, defaults to True.
    :type fastmath: bool
    :param cache: Flag to enable caching of the compiled function, defaults to True.
    :type cache: bool
    :param signature: Optional Numba signature.
    :type signature: Any
    :return: The Numba JIT compiled function.
    :rtype: Callable[..., Any]
    """
    if signature is not None:
        compiled_kernel: Callable[..., Any] = nb.jit(signature, fastmath=fastmath, cache=cache)(py_func)
    else:
        compiled_kernel = nb.jit(fastmath=fastmath, cache=cache)(py_func)

    return compiled_kernel

# ==============================================================================
# Sparse Forward-Mode AD Jacobian with Graph Coloring (JVP-based)
# ==============================================================================

@nb.jit(cache=True, fastmath=True)
def _scatter_color_jvp_to_csc_data(jvp: np.ndarray,
                                   data: np.ndarray,
                                   color_ptr: np.ndarray,
                                   col_ptr: np.ndarray,
                                  row_idx: np.ndarray,
                                  data_idx: np.ndarray,
                                  color_id: int) -> None:
    """
    Scatter a single JVP evaluation into the CSC data array for all columns in a given color.
    """
    k0: int = int(color_ptr[color_id])
    k1: int = int(color_ptr[color_id + 1])
    for k in range(k0, k1):
        p0: int = int(col_ptr[k])
        p1: int = int(col_ptr[k + 1])
        for p in range(p0, p1):
            data[data_idx[p]] = jvp[row_idx[p]]


def _compile_master_jacobian_kernel(ad_kernel: Callable[..., Any], n_colors: int) -> Callable[..., Any]:
    """
    Build the eager sparse Jacobian dispatcher.

    :param ad_kernel: Generic AD kernel reused across graph colors.
    :type ad_kernel: Callable[..., Any]
    :param n_colors: Number of graph colors.
    :type n_colors: int
    :return: Jacobian dispatcher.
    :rtype: Callable[..., Any]
    """
    return SparseAdMasterJacobianDispatcher(ad_kernel=ad_kernel, n_colors=n_colors)


class SparseAdMasterJacobianDispatcher:
    """
    Callable dispatcher that executes one generic AD kernel across all colors.
    """

    __slots__ = ("_ad_kernel", "_n_colors")

    def __init__(self, ad_kernel: Callable[..., Any], n_colors: int) -> None:
        """
        Store the generic AD kernel and the number of graph colors.

        :param ad_kernel: Generic AD kernel reused across graph colors.
        :param n_colors: Number of graph colors.
        :return: None.
        """
        self._ad_kernel: Callable[..., Any] = ad_kernel
        self._n_colors: int = n_colors

    def __call__(self,
                 states: Vec,
                 seed_matrix: Mat,
                 params: Vec,
                 history: Vec,
                 d_history: Vec,
                 h: float,
                 history2: Vec,
                 data: Vec,
                 color_ptr: np.ndarray,
                 col_ptr: np.ndarray,
                 row_idx: np.ndarray,
                 data_idx: np.ndarray,
                 work_jvp: Mat) -> None:
        """
        Evaluate all color JVPs and scatter them into CSC data storage.

        :param states: Current Newton iterate.
        :param seed_matrix: Coloring seed matrix.
        :param params: Full parameter vector.
        :param history: Previous accepted state.
        :param d_history: Previous derivative vector.
        :param h: Effective time step.
        :param history2: Secondary history vector.
        :param data: CSC numeric data buffer.
        :param color_ptr: Color-to-column pointer array.
        :param col_ptr: Column-to-scatter pointer array.
        :param row_idx: Row indices used by the scatter map.
        :param data_idx: CSC data positions used by the scatter map.
        :param work_jvp: Reusable JVP work buffer.
        :return: None.
        """
        color_index: int = 0

        while color_index < self._n_colors:
            local_jvp: Vec = work_jvp[color_index]
            self._ad_kernel(states, seed_matrix[color_index], params, history, d_history, h, local_jvp, history2)
            _scatter_color_jvp_to_csc_data(local_jvp, data, color_ptr, col_ptr, row_idx, data_idx, color_index)
            color_index += 1


def greedy_color_columns(col_rows: List[List[int]], n_rows: int) -> Tuple[np.ndarray, int]:
    """
    Computes a greedy coloring of the column dependency graph to minimize AD sweeps.

    :param col_rows: List of row indices where each column has non-zeros.
    :type col_rows: List[List[int]]
    :param n_rows: Total number of rows in the matrix.
    :type n_rows: int
    :return: An array of color IDs per column and the total number of colors.
    :rtype: Tuple[np.ndarray, int]
    """
    n_cols: int = len(col_rows)
    row_cols: List[List[int]] = [list() for _ in range(n_rows)]
    for j in range(n_cols):
        for r in col_rows[j]:
            row_cols[r].append(j)

    adj: List[Set[int]] = [set() for _ in range(n_cols)]
    for cols in row_cols:
        m: int = len(cols)
        for a in range(m):
            ja: int = cols[a]
            for b in range(a + 1, m):
                jb: int = cols[b]
                if jb != ja:
                    adj[ja].add(jb)
                    adj[jb].add(ja)
                else:
                    pass

    degrees: np.ndarray = np.array([len(adj[j]) for j in range(n_cols)], dtype=np.int32)
    order: List[int] = list(np.argsort(-degrees, kind="stable"))
    colors: np.ndarray = -np.ones(n_cols, dtype=np.int32)
    max_color: int = -1
    used: np.ndarray = np.zeros(n_cols, dtype=np.bool_)

    for j in order:
        used[:] = False
        for nbj in adj[j]:
            c: int = int(colors[nbj])
            if c >= 0:
                used[c] = True
            else:
                pass

        c_iter: int = 0
        while c_iter < n_cols and used[c_iter]:
            c_iter += 1

        colors[j] = c_iter
        if c_iter > max_color:
            max_color = c_iter
        else:
            pass

    return colors, int(max_color + 1)

class BoundaryUpdaterInterface:
    __slots__ = ()

    def update(
        self,
        t: float,
        x_prev: Vec,
        full_params: Vec,
    ) -> float | None:
        """Update boundary values and optionally request a shortened retry.

        :param t: Candidate endpoint time.
        :param x_prev: Accepted EMT state vector.
        :param full_params: Parameter vector updated in place.
        :return: Earlier retry target or ``None``.
        """

        raise NotImplementedError

    def get_next_forced_event_time(self, t_prev: float, t_target: float) -> float | None:
        raise NotImplementedError

class Predictor:
    """
    Computes an explicit predictor for the Newton initial guess x_iter.
    """
    __slots__ = ['n_states']

    def __init__(self,
                 n_states: int) -> None:
        self.n_states = n_states

    def predict(self,
                x_iter: Vec,
                x_prev: Vec,
                dx_prev: Vec,
                h: float,
                pred_method: Union[DynamicIntegrationMethod|None] = DynamicIntegrationMethod.DaeBackEuler) -> Vec:
        """
        Apply predictor in-place and return x_iter.
        :param x_iter: Array to be written with the predictor guess (in-place).
        :param x_prev: Previous full variable vector at time n.
        :param dx_prev: Previous derivative vector (only first n_states are meaningful).
        :param h: Time step.
        :param pred_method: Integration method enum/value at the prediction step
        :return:
        """

        # Default: no-op predictor
        x_iter[:] = x_prev

        # Dispatch per method
        if pred_method == DynamicIntegrationMethod.OdeEuler:
            return self._predict_euler_state(x_iter, x_prev, dx_prev, h)
        elif pred_method == DynamicIntegrationMethod.DaeBDF2:
            raise NotImplementedError(f"predictor method {pred_method} ")

        # Otherwise keep default x_iter = x_prev
        return x_iter

    # ---------------------------------------------------------------------
    # Predictor implementations
    # ---------------------------------------------------------------------
    def _predict_euler_state(self,
                             x_iter: Vec,
                             x_prev: Vec,
                             dx_prev: Vec,
                             h: float) -> Vec:
        """
        Explicit Euler predictor for the *state* subset:
            x_{n+1}^0 = x_n + h * dx_n   (states only)
        Algebraics remain at x_prev by default (already set in caller).
        """
        ns = self.n_states
        x_iter[:ns] = x_prev[:ns] + h * dx_prev[:ns]
        return x_iter


def fill_full_parameter_buffer(runtime_params: Vec, static_params: Vec, full_params_out: Vec) -> None:
    """
    Write runtime and static parameters into one preallocated full buffer.

    :param runtime_params: Runtime parameter slice.
    :type runtime_params: Vec
    :param static_params: Static parameter slice.
    :type static_params: Vec
    :param full_params_out: Destination full parameter vector.
    :type full_params_out: Vec
    :return: None.
    :rtype: None
    """
    n_runtime: int = runtime_params.shape[0]
    n_static: int = static_params.shape[0]

    # The runtime portion must be refreshed every local substep because events
    # and boundary updates can change it in place.
    full_params_out[:n_runtime] = runtime_params

    # The static portion is copied after the runtime slice so the solver sees a
    # stable [runtime | static] layout in every backend call.
    full_params_out[n_runtime:n_runtime + n_static] = static_params


def evaluate_batched_residual(
        kernel_list: List[Callable[..., Any]],
        x_iter: Vec,
        full_params: Vec,
        x_prev: Vec,
        dx_prev: Vec,
        h_eff: float,
        x_prev2: Vec,
        residual_out: Vec,
) -> float:
    """
    Evaluate all residual batches into a caller-owned buffer.

    :param kernel_list: Batched residual kernels.
    :type kernel_list: List[Callable[..., Any]]
    :param x_iter: Current Newton iterate.
    :type x_iter: Vec
    :param full_params: Full parameter vector.
    :type full_params: Vec
    :param x_prev: Previous accepted state.
    :type x_prev: Vec
    :param dx_prev: Previous derivative vector.
    :type dx_prev: Vec
    :param h_eff: Effective local time step.
    :type h_eff: float
    :param x_prev2: Secondary state history.
    :type x_prev2: Vec
    :param residual_out: Destination residual buffer.
    :type residual_out: Vec
    :return: Residual infinity norm.
    :rtype: float
    """
    residual_out[:] = 0.0

    # The residual is assembled batch by batch because the symbolic compiler
    # splits large systems to keep code generation robust.
    for kernel in kernel_list:
        kernel(x_iter, full_params, x_prev, dx_prev, h_eff, residual_out, x_prev2)

    return float(np.linalg.norm(residual_out, np.inf))


class AdBacktrackingResidualEvaluator:
    """
    Wrapper that evaluates AD residual batches for line-search backtracking.
    """

    __slots__ = ["_kernel_list", "_full_params", "_x_prev", "_dx_prev", "_h_eff", "_x_prev2"]

    def __init__(self) -> None:
        """
        Build one empty backtracking evaluator.

        :return: None.
        :rtype: None
        """
        self._kernel_list: List[Callable[..., Any]] | None = None
        self._full_params: Vec | None = None
        self._x_prev: Vec | None = None
        self._dx_prev: Vec | None = None
        self._h_eff: float = 0.0
        self._x_prev2: Vec | None = None

    def set_context(
            self,
            kernel_list: List[Callable[..., Any]],
            full_params: Vec,
            x_prev: Vec,
            dx_prev: Vec,
            h_eff: float,
            x_prev2: Vec,
    ) -> None:
        """
        Store the residual-evaluation context of the current Newton step.

        :param kernel_list: Batched residual kernels.
        :type kernel_list: List[Callable[..., Any]]
        :param full_params: Full parameter vector.
        :type full_params: Vec
        :param x_prev: Previous accepted state.
        :type x_prev: Vec
        :param dx_prev: Previous derivative vector.
        :type dx_prev: Vec
        :param h_eff: Effective local time step.
        :type h_eff: float
        :param x_prev2: Secondary state history.
        :type x_prev2: Vec
        :return: None.
        :rtype: None
        """
        self._kernel_list = kernel_list
        self._full_params = full_params
        self._x_prev = x_prev
        self._dx_prev = dx_prev
        self._h_eff = float(h_eff)
        self._x_prev2 = x_prev2

    def evaluate(self, candidate_x: Vec, out_res: Vec) -> float:
        """
        Evaluate one trial Newton iterate during backtracking.

        :param candidate_x: Trial iterate.
        :type candidate_x: Vec
        :param out_res: Destination residual buffer.
        :type out_res: Vec
        :return: Residual infinity norm.
        :rtype: float
        """
        if self._kernel_list is None:
            return np.inf
        else:
            pass

        if self._full_params is None or self._x_prev is None or self._dx_prev is None or self._x_prev2 is None:
            return np.inf
        else:
            pass

        return evaluate_batched_residual(
            kernel_list=self._kernel_list,
            x_iter=candidate_x,
            full_params=self._full_params,
            x_prev=self._x_prev,
            dx_prev=self._dx_prev,
            h_eff=self._h_eff,
            x_prev2=self._x_prev2,
            residual_out=out_res,
        )

class SparseADJacobian:
    """
    Sparse Jacobian evaluator with DEBUG TIMING.
    """
    __slots__ = [
        'equations', 'variables', 'parameters', 'method', 'use_cse', 'dtype',
        'n_rows', 'n_cols', 'var_map', 'param_map', 'col_rows', 'J',
        'colors', 'n_colors', 'color_groups', 'color_ptr', 'color_cols',
        'col_ptr', 'row_idx', 'data_idx', '_compiler', '_ad_kernel', '_master_dispatcher',
        '_seed_matrix', '_jvp_work_buffer', '_data_buffer'
    ]

    def __init__(self,
                 equations: List[Any],
                 variables: List[Any],
                 parameters: List[Any],
                 method: DynamicIntegrationMethod,
                 use_cse: bool = True,
                 dtype: Any=np.float64)-> None:

        t_start = time.perf_counter()
        print_enabled: bool = False

        self.equations = equations
        self.variables = variables
        self.parameters = parameters
        self.method = method
        self.use_cse = use_cse
        self.dtype = dtype

        self.n_rows = len(equations)
        self.n_cols = len(variables)

        self.var_map: Dict[int, int] = dict()
        for i, v in enumerate(variables):
            self.var_map[v.uid] = i

        self.param_map: Dict[int, int] = dict()
        for i, p in enumerate(parameters):
            self.param_map[p.uid] = i

        t_maps: float = time.perf_counter()
        if print_enabled:
            print(f"   [AD-Debug] Maps built in {t_maps - t_start:.4f}s")

        # 1) Sparsity Detection
        col_rows: List[List[int]] = [list() for _ in range(self.n_cols)]

        count_edges: int = 0
        for r, eq in enumerate(equations):
            stack: List[Any] = list()
            stack.append(eq)
            visited: Set[int] = set()
            uids: Set[int] = set()

            while stack:
                n: Any = stack.pop()
                if id(n) in visited:
                    pass
                else:
                    visited.add(id(n))

                    match n:
                        case Var(uid=u, base_var=bv):
                            uids.add(u)
                            if bv is not None:
                                uids.add(bv.uid)
                            else:
                                pass
                        case BinOp(left=l, right=r_node):
                            stack.append(l)
                            stack.append(r_node)
                        case UnOp(operand=op):
                            stack.append(op)
                        case Func(arg=a):
                            stack.append(a)
                        case _:
                            pass

            for uid in uids:
                j: int | None = self.var_map.get(uid, None)
                if j is not None:
                    col_rows[j].append(r)
                    count_edges += 1
                else:
                    pass

        self.col_rows = [sorted(set(rows)) for rows in col_rows]

        t_sparsity = time.perf_counter()
        if print_enabled:
            print(f"   [AD-Debug] Sparsity Analysis done in {t_sparsity - t_maps:.4f}s. Edges found: {count_edges}")

        # 2) CSC Structure
        indptr = np.zeros(self.n_cols + 1, dtype=np.int32)
        nnz = 0
        for j in range(self.n_cols):
            nnz += len(self.col_rows[j])
            indptr[j + 1] = nnz

        indices = np.empty(nnz, dtype=np.int32)
        data = np.zeros(nnz, dtype=self.dtype)
        k = 0
        for j in range(self.n_cols):
            for r in self.col_rows[j]:
                indices[k] = r
                k += 1

        self.J = csc_matrix((data, indices, indptr), shape=(self.n_rows, self.n_cols))

        t_csc = time.perf_counter()
        if print_enabled:
            print(f"   [AD-Debug] CSC Matrix built in {t_csc - t_sparsity:.4f}s")

        # 3) Coloring
        self.colors, self.n_colors = greedy_color_columns(self.col_rows, self.n_rows)
        groups: List[List[int]] = [list() for _ in range(self.n_colors)]
        for j in range(self.n_cols):
            groups[self.colors[j]].append(j)
        self.color_groups = groups

        t_color = time.perf_counter()
        if print_enabled:
            print(f"   [AD-Debug] Graph Coloring done in {t_color - t_csc:.4f}s. Colors: {self.n_colors}")

        # 4) Precompute scatter map
        color_cols: List[int] = list()
        color_ptr = np.zeros(self.n_colors + 1, dtype=np.int32)
        for c in range(self.n_colors):
            color_ptr[c] = len(color_cols)
            color_cols.extend(self.color_groups[c])
        color_ptr[self.n_colors] = len(color_cols)

        col_ptr = np.zeros(len(color_cols) + 1, dtype=np.int32)
        total_map = 0
        for kk, j in enumerate(color_cols):
            total_map += len(self.col_rows[j])
            col_ptr[kk + 1] = total_map

        row_idx = np.empty(total_map, dtype=np.int32)
        data_idx = np.empty(total_map, dtype=np.int32)
        pos = 0
        indptr_arr = self.J.indptr
        for kk, j in enumerate(color_cols):
            base = indptr_arr[j]
            rows = self.col_rows[j]
            for local, r in enumerate(rows):
                row_idx[pos] = r
                data_idx[pos] = base + local
                pos += 1

        self.color_ptr = color_ptr
        self.color_cols = np.asarray(color_cols, dtype=np.int32)
        self.col_ptr = col_ptr
        self.row_idx = row_idx
        self.data_idx = data_idx

        t_scatter = time.perf_counter()
        if print_enabled:
            print(f"   [AD-Debug] Scatter Map built in {t_scatter - t_color:.4f}s")

        # 5) Compile Optimization: one generic eager AD kernel reused across colors.
        self._compiler = EagerEquationCompiler(variables=variables, parameters=parameters, method=method)

        if print_enabled:
            print(f"   [AD-Opt] Compiling one generic AD kernel for {self.n_colors} colors...")
        t_comp_start = time.perf_counter()

        k_name = f"ad_step_generic_{self.method.name}_{self.n_rows}_{self.n_cols}"
        py_ad, signature_tpe = self._compiler.compile_ad_kernel(
            equations,
            func_name=k_name,
            use_cse=use_cse,
            active_indices=None,
        )

        self._ad_kernel = _safe_njit(py_ad, cache=True, fastmath=True, signature=signature_tpe)
        self._master_dispatcher = _compile_master_jacobian_kernel(self._ad_kernel, self.n_colors)

        self._seed_matrix = np.zeros((self.n_colors, self.n_cols), dtype=self.dtype)
        for c in range(self.n_colors):
            self._seed_matrix[c, self.color_groups[c]] = 1.0

        self._jvp_work_buffer = np.zeros((self.n_colors, self.n_rows), dtype=self.dtype)
        self._data_buffer = self.J.data

        t_comp_end = time.perf_counter()
        if print_enabled:
            print(f"   [AD-Opt] Generic kernel compiled in {t_comp_end - t_comp_start:.4f}s")
            print(f"   [AD-Debug] Total Init Time: {t_comp_end - t_start:.4f}s")

    def __call__(self,
                 states: np.ndarray,
                 params: np.ndarray,
                 history: np.ndarray,
                 d_history: np.ndarray,
                 h: float,
                 history2: Union[np.ndarray | None] = None) -> csc_matrix:
        """
        Evaluates the AD Jacobian.

        :param states: Current states.
        :type states: np.ndarray
        :param params: Current parameters.
        :type params: np.ndarray
        :param history: State history.
        :type history: np.ndarray
        :param d_history: Derivative history.
        :type d_history: np.ndarray
        :param h: Time step.
        :type h: float
        :param history2: Secondary state history.
        :type history2: np.ndarray | None
        :return: Evaluated sparse matrix.
        :rtype: csc_matrix
        """

        self._master_dispatcher(
            states,
            self._seed_matrix,
            params,
            history,
            d_history,
            h,
            history2,
            self._data_buffer,
            self.color_ptr,
            self.col_ptr,
            self.row_idx,
            self.data_idx,
            self._jvp_work_buffer,
        )
        return self.J

class JitAdSolver:
    __slots__ = [
        'problem', 't0', 't_end', 'h', 'method', 'pred_method', 'dense_threshold', 'verbose', 'newton_max_iter',
        'steps', 't', 'y', 'dy',  'jit_kernels_ad', 'jit_jacobian_ad',
        'state_vars', 'algebraic_vars', 'state_eqs', 'algebraic_eqs', '_newton_diag_config',
        '_predictor', '_runtime_param_count', '_static_parameter_buffer', '_full_parameter_buffer',
        '_residual_buffer', '_trial_state_buffer', '_trial_residual_buffer',
        '_backend_build_stats', '_last_runtime_stats', '_last_sim_loop_time', '_cancel_checker', '_progress_signal',
        '_newton_tolerance', '_use_compiled_runtime_parameters',
        '_sparse_solver_backend_provider', '_sparse_linear_solver'
    ]
    def __init__(self,
                 problem: EmtProblemTemplate,
                 t0: float,
                 t_end: float,
                 h: float,
                 method: DynamicIntegrationMethod = DynamicIntegrationMethod.DaeTrapezoidal,
                 pred_method: DynamicIntegrationMethod = None,
                 dense_threshold: int = 100,
                 verbose: bool = False,
                 newton_max_iter: int = 15,
                 newton_diag_config: NewtonDiagnosticsConfig | None = None,
                 progress_signal: DummySignal | None = None,
                 cancel_checker: Callable[[], bool] | None = None,
                 newton_tolerance: float = 1.0e-6,
                 use_compiled_runtime_parameters: bool = True, sparse_solver_backend_provider: SparseLinearSolverBackendProvider | None = None)-> None:
        """
        Initializes the JIT AD Solver.

        :param problem: The DAE problem definition.
        :type problem: EmtProblemTemplate
        :param t0: Initial time.
        :type t0: float
        :param t_end: End time.
        :type t_end: float
        :param h: Time step.
        :type h: float
        :param method: DynamicIntegrationMethod (DaeTrapezoidal, DaeBackEuler, DaeBDF2).
        :type method: DynamicIntegrationMethod
        :param pred_method: DynamicIntegrationMethod used in the predictor step if method is explicit.
        :type pred_method: DynamicIntegrationMethod
        :param dense_threshold: Threshold to switch between dense and sparse linear solvers.
        :type dense_threshold: int
        :param verbose: Print compilation and simulation timings.
        :type verbose: bool
        :param newton_max_iter: Maximum Newton corrections per local EMT substep.
            The final corrected candidate is checked without another correction.
        :type newton_max_iter: int
        :param sparse_solver_backend_provider: Available LU phase factory, or inherit the configured problem.
        :param newton_tolerance: Absolute infinity-norm tolerance for Newton residual convergence.
        :type newton_tolerance: float
        :param progress_signal: Optional progress signal updated during the simulation loop.
        :type progress_signal: DummySignal | None
        :param use_compiled_runtime_parameters: Use the compiled runtime-parameter evaluator. Disable only for
            numerical equivalence validation against the legacy interpreted evaluator.
        :type use_compiled_runtime_parameters: bool
        """
        self.problem = problem
        # Direct construction inherits a configured problem; a generic problem
        # without options retains the historical SuperLU default.
        self._sparse_solver_backend_provider: SparseLinearSolverBackendProvider | None = sparse_solver_backend_provider
        if self._sparse_solver_backend_provider is None and isinstance(problem, EmtProblemTemplate):
            self._sparse_solver_backend_provider = problem.get_sparse_solver_backend_provider()
        else:
            pass
        if self._sparse_solver_backend_provider is None:
            self._sparse_solver_backend_provider = SuperLUSparseBackendProvider()
        else:
            pass
        self._sparse_linear_solver: SparseProviderLinearSolver = SparseProviderLinearSolver(self._sparse_solver_backend_provider)
        self.t0 = t0
        self.h = h
        self.method = method
        self.pred_method = pred_method
        self.dense_threshold = dense_threshold
        self.verbose = verbose
        self.newton_max_iter: int = int(newton_max_iter)
        self._newton_tolerance: float = float(newton_tolerance)
        self._use_compiled_runtime_parameters: bool = bool(use_compiled_runtime_parameters)
        if not np.isfinite(self._newton_tolerance) or self._newton_tolerance <= 0.0:
            raise ValueError("newton_tolerance must be finite and greater than zero.")
        self.t_end = t_end
        self._newton_diag_config = newton_diag_config or NewtonDiagnosticsConfig(
            compute_dense_cond=False,
            enable_fallback=False,
            enable_index1_check=False,
            enable_backtracking=False,
        )

        self.steps = int(np.ceil((t_end - t0) / h))
        self.t: Vec = np.empty(self.steps + 1)
        self.y: Mat = np.empty((self.steps + 1, self.problem.get_all_vars_number()))
        self.dy: Mat = np.empty((self.steps + 1, self.problem.get_diff_var_number()))

        # Solver specific caches
        self.jit_kernels_ad: Dict[DynamicIntegrationMethod, List[Callable]] = dict()
        self.jit_jacobian_ad: Dict[DynamicIntegrationMethod, SparseADJacobian] = dict()

        # Cache local of variables to avoid calling getters multiple times in init
        self.state_vars = self.problem.get_state_vars()
        self.algebraic_vars = self.problem.get_algebraic_vars()
        self.state_eqs = self.problem.get_state_eqs()
        self.algebraic_eqs = self.problem.get_algebraic_eqs()

        self._predictor = Predictor(n_states=self.problem.get_states_number())
        self._runtime_param_count: int = self.problem.get_variable_parameter_number()
        self._static_parameter_buffer: Vec = np.asarray(
            [float(constant.value) for constant in self.problem.get_parameters_values()],
            dtype=np.float64,
        )
        self._full_parameter_buffer: Vec = np.zeros(
            self._runtime_param_count + self._static_parameter_buffer.shape[0],
            dtype=np.float64,
        )
        self._residual_buffer: Vec = np.zeros(self.problem.get_all_vars_number(), dtype=np.float64)
        self._trial_state_buffer: Vec = np.zeros(self.problem.get_all_vars_number(), dtype=np.float64)
        self._trial_residual_buffer: Vec = np.zeros(self.problem.get_all_vars_number(), dtype=np.float64)
        self._backend_build_stats: Dict[str, float] = dict(
            residual_compile_s=0.0,
            residual_batches=0.0,
            jacobian_compile_s=0.0,
            jacobian_builds=0.0,
            total_s=0.0,
        )
        self._last_runtime_stats: Dict[str, float] = dict()
        self._last_sim_loop_time: float = 0.0
        self._progress_signal: DummySignal | None = progress_signal
        self._cancel_checker = cancel_checker

    def build_jit_ad(self, only_jacobian: bool = False,
                     method: DynamicIntegrationMethod | None = None) -> None:
        """
        Compiles the residual kernel using batching and prepares the Sparse AD Jacobian.

        :param only_jacobian: If True, skips residual compilation (used by Vectorized Engine fallback).
        :type only_jacobian: bool
        :param method: Effective discretization; defaults to the requested method.
        :return: None; kernels and Jacobians are cached by effective method.
        :rtype: None
        """
        effective_method: DynamicIntegrationMethod = self.method if method is None else method
        if effective_method in self.jit_kernels_ad and not only_jacobian:
            return
        else:
            pass

        t_total_start: float = time.perf_counter()

        if self.verbose:
            print(
                f"--- [JIT-AD] Compiling {'Jacobian ONLY' if only_jacobian else 'Implicit Kernel + AD Jacobian'} ({effective_method}) ---")
        else:
            pass

        sorted_vars: List[Any] = list()
        sorted_vars.extend(self.state_vars)
        sorted_vars.extend(self.algebraic_vars)

        all_params: List[Any] = list()
        all_params.extend(self.problem.get_variable_parameters())
        all_params.extend(self.problem.get_constant_parameters())

        equations: List[Expr] = list()
        for i, rhs in enumerate(self.state_eqs):
            sv = self.state_vars[i]
            d_term = Var(name=f"d_{sv.name}", base_var=sv)
            equations.append(d_term - rhs)
        equations.extend(self.algebraic_eqs)

        # --- PART 1: RESIDUALS (Batched) ---
        if not only_jacobian and effective_method not in self.jit_kernels_ad:
            compiler = EquationCompiler(variables=sorted_vars, parameters=all_params, method=effective_method)
            # Fix the in-place residual contract before integration starts so
            # Numba compiles every generated batch during backend construction
            # instead of lazily compiling it in the first Newton iteration.
            residual_signature: Any = nb.void(
                nb.float64[:],
                nb.float64[:],
                nb.float64[:],
                nb.float64[:],
                nb.float64,
                nb.float64[:],
                nb.float64[:],
            )
            BATCH_SIZE = 100
            n_eqs = len(equations)
            batched_kernels: List[Callable] = list()

            if self.verbose:
                print(f"   [JIT-AD] Splitting {n_eqs} residual eqs into {int(np.ceil(n_eqs / BATCH_SIZE))} batches...")
            t0 = time.perf_counter()

            for i in range(0, n_eqs, BATCH_SIZE):
                chunk = equations[i: i + BATCH_SIZE]
                fname = f"jit_step_{effective_method}_ad_part_{i}"
                py_func = compiler.compile(chunk, func_name=fname, use_cse=True, offset=i, inplace=True)
                jit_func = _safe_njit(
                    py_func=py_func,
                    cache=True,
                    fastmath=True,
                    signature=residual_signature,
                )
                batched_kernels.append(jit_func)

            if self.verbose:
                print(f"   [JIT-AD] Residual Batches compiled in {time.perf_counter() - t0:.4f}s")
            else:
                pass
            self.jit_kernels_ad[effective_method] = batched_kernels
            residual_elapsed_s: float = time.perf_counter() - t0
            self._backend_build_stats['residual_compile_s'] += residual_elapsed_s
            self._backend_build_stats['residual_batches'] += float(len(batched_kernels))
            self._backend_build_stats['total_s'] += residual_elapsed_s
        else:
            pass

        # --- PART 2: JACOBIAN (O(N) setup, needed for normal and Vectorized fallback) ---
        if effective_method not in self.jit_jacobian_ad:
            jacobian_t0: float = time.perf_counter()
            jac = SparseADJacobian(equations=equations, variables=sorted_vars, parameters=all_params,
                                   method=effective_method, use_cse=True)
            self.jit_jacobian_ad[effective_method] = jac
            jacobian_elapsed_s: float = time.perf_counter() - jacobian_t0
            self._backend_build_stats['jacobian_compile_s'] += jacobian_elapsed_s
            self._backend_build_stats['jacobian_builds'] += 1.0
            self._backend_build_stats['total_s'] += jacobian_elapsed_s
        else:
            pass

        total_elapsed_s: float = time.perf_counter() - t_total_start
        self._backend_build_stats['total_s'] = max(self._backend_build_stats['total_s'], total_elapsed_s)

    def simulate(self,
                 x0: Union[Vec | None] = None,
                 dx0: Union[Vec | None] = None,
                 params0: Union[Vec | None] = None,
                 boundary_updater: EmtBoundaryUpdateProtocol | None = None) -> Tuple[Vec, Mat, Mat, bool, bool]:
        """
        Main JIT simulation loop using the Automatic Differentiation (AD) backend.

        :param x0: Initial state vector.
        :param dx0: Initial derivative vector.
        :param params0: Initial event parameters.
        :param boundary_updater: Optional override for the problem boundary updater.
        :return: Matching completed macro prefixes for time, state and derivative,
                 followed by initialization and convergence flags.
        """
        t_start = time.time()
        method = self.method

        converged: bool = True
        well_initialized: bool = True

        if method not in self.jit_kernels_ad:
            self.build_jit_ad()
        else:
            pass

        # Problem construction, initialization, and event-group selection are
        # complete before the solver starts. Activate the finalized compiled
        # runtime equations so every time-step update avoids symbolic traversal.
        if self._use_compiled_runtime_parameters:
            self.problem.enable_compiled_runtime_parameter_evaluator()
        else:
            pass

        # A fresh BDF2 call first obtains a real second state with backward Euler.
        bdf2_startup_pending: bool = method == DynamicIntegrationMethod.DaeBDF2
        if bdf2_startup_pending:
            self.build_jit_ad(method=DynamicIntegrationMethod.DaeBackEuler)
        else:
            pass

        kernel_list = self.jit_kernels_ad[method]
        current_jacobian = self.jit_jacobian_ad[method]

        n_eqs = self.problem.get_all_vars_number()
        n_states = self.problem.get_states_number()

        use_dense_solver = (n_eqs <= self.dense_threshold)

        # pr = profile.Profile()
        # pr.disable()
        # pr.enable()

        t = np.linspace(self.t0, self.t_end, self.steps + 1, dtype=np.float64)
        self.t = t

        if x0 is None:
            x0 = self.problem.get_x0()
        else:
            pass
        if dx0 is  None:
            dx0 = self.problem.get_dx0()
        else:
            pass

        active_boundary_updater = resolve_solver_boundary_updater(self.problem, boundary_updater, float(self.t0))
        # Optional updater APIs are resolved once instead of on every substep.
        boundary_capabilities: BoundaryUpdaterCapabilities = BoundaryUpdaterCapabilities(active_boundary_updater)

        self.y[0, :] = x0.copy()
        self.dy[0, :] = dx0.copy()

        x_prev = x0.copy()
        dx_prev = dx0.copy()
        x_prev2 = x0.copy()
        # AD kernels use runtime-variable history; public derivatives use UID order.
        n_diff: int = self.problem.get_diff_var_number()
        base_slopes: Vec = np.zeros(x_prev.size, dtype=np.float64)
        diff_base_indices: np.ndarray = np.full(dx_prev.size, -1, dtype=np.int64)
        differential: Var
        for differential in self.problem.get_diff_vars():
            if differential.base_var is not None:
                diff_index: int = self.problem.uid2idx_diff[differential.uid]
                diff_base_indices[diff_index] = self.problem.uid2idx_vars.get(differential.base_var.uid, -1)
            else:
                pass
        # Differentials with a base variable and their base rows, so the history update needs no per-element loop.
        diff_rows_with_base: np.ndarray = np.flatnonzero(diff_base_indices >= 0)
        diff_base_rows: np.ndarray = diff_base_indices[diff_rows_with_base]
        kernel_derivatives: Vec = base_slopes
        if bdf2_startup_pending:
            pass
        elif n_diff == 0:
            # Without declared differentials the caller's vector already is the history in runtime-variable order.
            kernel_derivatives = dx_prev
        else:
            kernel_derivatives[diff_base_rows] = dx_prev[diff_rows_with_base]
        # Trapezoidal kernels read a history for every state: a state without a declared differential would keep zero.
        if method == DynamicIntegrationMethod.DaeTrapezoidal and n_diff > 0:
            missing_states: np.ndarray = np.setdiff1d(np.arange(n_states), diff_base_rows)
            if missing_states.size > 0:
                raise ValueError(
                    "The trapezoidal rule needs a declared differential for every state once any is declared; "
                    f"missing for {list([self.state_vars[i].name for i in missing_states])}"
                )
            else:
                pass
        else:
            pass
        x_iter = x0.copy()
        trial_x = self._trial_state_buffer
        trial_res = self._trial_residual_buffer

        static_vals = self._static_parameter_buffer
        n_event_params = self._runtime_param_count
        full_params = self._full_parameter_buffer
        residual_buffer = self._residual_buffer

        if params0 is not None:
            ev_params = np.array(params0, dtype=np.float64, copy=True)
        else:
            ev_params = self.problem.event_params_values.copy()

        should_initialize_at_t0: bool = is_problem_owned_boundary_updater(self.problem, active_boundary_updater)

        if active_boundary_updater is not None and should_initialize_at_t0:
            runtime_params0 = self.problem.def_event_params_fn(ev_params, float(self.t0))
            fill_full_parameter_buffer(runtime_params0, static_vals, full_params)
            active_boundary_updater.update(float(self.t0), x_prev, full_params)
            ev_params[:] = full_params[:n_event_params]
        else:
            pass

        trace_collector = self.problem.get_newton_trace_collector()
        diag_cfg = self._newton_diag_config
        diagnostics_enabled: bool = (
            trace_collector is not None
            or diag_cfg.compute_dense_cond
            or diag_cfg.enable_fallback
            or diag_cfg.enable_index1_check
            or diag_cfg.enable_backtracking
        )

        dense_solve = None
        sparse_solve = None

        if diagnostics_enabled:
            dense_solve = with_newton_diagnostics(
                np.linalg.solve,
                fallback_solve=dense_lstsq_fallback,
                collector=trace_collector,
                config=diag_cfg,
                solver_name="dense",
            )
            sparse_solve = with_newton_diagnostics(
                self._sparse_linear_solver.solve,
                fallback_solve=sparse_lsqr_fallback,
                collector=trace_collector,
                config=diag_cfg,
                solver_name="sparse",
            )
        else:
            pass

        backtracking_residual_evaluator = AdBacktrackingResidualEvaluator()

        if self.verbose:
            print(f"-> Starting JIT (AD) Simulation ({method}, {self.steps} steps)...")
        else:
            pass

        # Only completed macro rows are published after a local rejection.
        completed_samples: int = 1
        loop_start: float = time.perf_counter()
        total_newton_iterations: int = 0
        jacobian_evaluation_count: int = 0
        # A new run never inherits the preceding run's numerical eligibility.
        self._sparse_linear_solver.invalidate()
        cached_jacobian: csc_matrix | None = None
        factorization_parameters: Vec = np.empty_like(full_params)
        factorization_step: float = 0.0
        factorization_method: DynamicIntegrationMethod = method
        last_macro_iterations: int = 0
        factorization_reuse_hits: int = 0
        forced_factorization_invalidations: int = 0
        inherited_factor_retries: int = 0
        confirming_corrections: int = 0
        confirming_state: Vec = np.empty_like(x_iter)
        attempt_seed: Vec = np.empty_like(x_iter)
        aligned_substep_count: int = 0

        for i in range(self.steps):

            if self._progress_signal is not None:
                self.problem.report_progress2(i, self.steps)
            else:
                pass

            if self._cancel_checker is not None and self._cancel_checker():
                self._sparse_linear_solver.invalidate()
                break

            t_step_start = float(t[i])
            t_step_target = float(t[i + 1])

            t_local_prev = t_step_start
            is_first_local_step = True

            while t_local_prev < (t_step_target - 1e-15):

                forced_event_time = get_solver_forced_event_time(
                    active_boundary_updater,
                    float(t_local_prev),
                    float(t_step_target),
                    capabilities=boundary_capabilities,
                )

                if forced_event_time is None:
                    t_curr = t_step_target
                else:
                    t_curr = min(float(forced_event_time), t_step_target)

                    if t_curr <= t_local_prev + 1e-15:
                        t_curr = t_step_target

                is_aligned_substep = t_curr < (t_step_target - 1e-15)

                if is_aligned_substep:
                    aligned_substep_count += 1
                else:
                    aligned_substep_count = aligned_substep_count

                if method == DynamicIntegrationMethod.DaeBDF2 and is_aligned_substep:
                    raise NotImplementedError(
                        "force_step_alignment is not implemented for DaeBDF2 in JitAdSolver."
                    )
                else:
                    pass

                h_eff = float(t_curr - t_local_prev)

                # Parameter update via Problem
                runtime_params = self.problem.def_event_params_fn(ev_params, float(t_curr))
                fill_full_parameter_buffer(runtime_params, static_vals, full_params)

                if active_boundary_updater is not None:
                    state_event_retry_time: float | None = (
                        active_boundary_updater.update(
                            t_curr,
                            x_prev,
                            full_params,
                        )
                    )
                else:
                    state_event_retry_time = None

                ev_params[:] = full_params[:n_event_params]

                x_iter[:] = x_prev

                effective_method: DynamicIntegrationMethod = (
                    DynamicIntegrationMethod.DaeBackEuler if bdf2_startup_pending else method
                )
                kernel_list = self.jit_kernels_ad[effective_method]
                current_jacobian = self.jit_jacobian_ad[effective_method]

                # PREDICTOR
                if i == 0 and is_first_local_step and method == DynamicIntegrationMethod.DaeTrapezoidal:
                    self._predictor.predict(
                        x_iter=x_iter,
                        x_prev=x_prev,
                        dx_prev=kernel_derivatives,
                        h=h_eff,
                        pred_method=self.pred_method,
                    )
                else:
                    pass

                if cached_jacobian is not None:
                    inputs_changed: bool = factorization_inputs_changed(
                        True, is_aligned_substep, full_params, factorization_parameters,
                        h_eff, factorization_step)
                    if inputs_changed or effective_method != factorization_method:
                        cached_jacobian = None
                        self._sparse_linear_solver.invalidate()
                        forced_factorization_invalidations += 1
                    else:
                        pass
                else:
                    pass
                attempt_seed[:] = x_iter
                substep_converged: bool = state_event_retry_time is not None
                attempt: int
                for attempt in range(2):
                    attempt_reused_jacobian: bool = False
                    confirming_done: bool = False
                    confirming_pending: bool = False
                    confirming_fresh: bool = False
                    last_residual: float = 1.0
                    if state_event_retry_time is None:
                        newton_iteration_count: int = self.newton_max_iter + 1
                    else:
                        newton_iteration_count = 0
                    for k in range(newton_iteration_count):
                        # Discard a non-finite confirming trial before it can reach the boundary.
                        if confirming_pending and not np.all(np.isfinite(x_iter)):
                            x_iter[:] = confirming_state
                            substep_converged = True
                            cached_jacobian = None
                            self._sparse_linear_solver.invalidate()
                            break
                        else:
                            pass
                        # Check in Python, outside fastmath, before assembling a candidate.
                        if not np.all(np.isfinite(x_iter)):
                            break
                        else:
                            pass
                        total_newton_iterations += 1
                        ctx = NewtonSolveContext(
                            t=float(t_curr),
                            step_idx=int(i),
                            newton_iter=int(k),
                            phase="jit_ad",
                            method=str(effective_method),
                        )

                        # The residual buffer is reused across Newton iterations so
                        # the hot loop does not allocate one full residual vector.
                        res = residual_buffer
                        res_norm_inf = evaluate_batched_residual(
                            kernel_list=kernel_list,
                            x_iter=x_iter,
                            full_params=full_params,
                            x_prev=x_prev,
                            dx_prev=kernel_derivatives,
                            h_eff=h_eff,
                            x_prev2=x_prev2,
                            residual_out=res,
                        )

                        # The compiled norm may hide NaN entries; inspect the full buffer.
                        if confirming_pending and not np.all(np.isfinite(res)):
                            x_iter[:] = confirming_state
                            substep_converged = True
                            cached_jacobian = None
                            self._sparse_linear_solver.invalidate()
                            break
                        else:
                            pass
                        if not np.all(np.isfinite(res)):
                            break
                        else:
                            pass

                        if res_norm_inf < self._newton_tolerance:
                            if attempt == 0 and needs_confirming_correction(use_dense_solver, confirming_done, k, self.newton_max_iter):
                                confirming_done = True
                                confirming_pending = True
                                confirming_fresh = confirms_with_fresh_factors(res_norm_inf, last_residual)
                                confirming_state[:] = x_iter
                                confirming_corrections += 1
                            else:
                                substep_converged = True
                                break
                        elif confirming_pending:
                            x_iter[:] = confirming_state
                            substep_converged = True
                            cached_jacobian = None
                            self._sparse_linear_solver.invalidate()
                            break
                        else:
                            pass

                        # Validate the last iterate even when the correction budget is exhausted.
                        if k >= self.newton_max_iter:
                            break
                        else:
                            pass

                        refresh_factors: bool = (
                                attempt > 0 or use_dense_solver or diagnostics_enabled or cached_jacobian is None
                                or needs_factor_refresh(k, res_norm_inf, last_residual,
                                                        get_adaptive_recompute_threshold(last_macro_iterations),
                                                        self._newton_tolerance, self.newton_max_iter - k)
                                or (confirming_pending and confirming_fresh))
                        J: csc_matrix
                        if refresh_factors:
                            # Evaluate AD Jacobian
                            J = current_jacobian(
                                states=x_iter,
                                params=full_params,
                                history=x_prev,
                                d_history=kernel_derivatives,
                                h=h_eff,
                                history2=x_prev2,
                            )
                            jacobian_evaluation_count += 1

                            if not use_dense_solver:
                                cached_jacobian = J.copy()
                                J = cached_jacobian
                                factorization_parameters[:] = full_params
                                factorization_step = h_eff
                                factorization_method = effective_method
                                if confirming_pending and confirming_fresh:
                                    self._sparse_linear_solver.invalidate()
                                else:
                                    pass
                            else:
                                pass
                        elif cached_jacobian is not None:
                            J = cached_jacobian
                            attempt_reused_jacobian = True
                            factorization_reuse_hits += 1
                        else:
                            raise RuntimeError("JitAd chord Newton has no retained Jacobian to reuse")

                        # Diagnostics always see a fresh Jacobian (refresh is forced above).
                        if diagnostics_enabled:
                            maybe_check_index1(J, n_states, ctx=ctx, config=diag_cfg)
                        else:
                            pass

                        try:
                            if use_dense_solver:
                                dense_J = J.toarray()
                                if diagnostics_enabled:
                                    delta = dense_solve(dense_J, -res, ctx)
                                else:
                                    delta = np.linalg.solve(dense_J, -res)
                            else:
                                if diagnostics_enabled:
                                    delta = sparse_solve(J, -res, ctx)
                                elif refresh_factors:
                                    delta = solve_sparse_system_once(
                                        J, -res, self._sparse_solver_backend_provider, self._sparse_linear_solver)
                                else:
                                    delta = self._sparse_linear_solver.solve_retained(-res)
                        except (RuntimeError, np.linalg.LinAlgError, FloatingPointError):
                            if use_dense_solver or refresh_factors:
                                # Fresh-Jacobian and dense solves keep the original exception contract;
                                # only a failure on retained factors is turned into a fresh-Jacobian retry.
                                raise
                            else:
                                pass
                            cached_jacobian = None
                            self._sparse_linear_solver.invalidate()
                            if confirming_pending:
                                x_iter[:] = confirming_state
                                substep_converged = True
                            else:
                                pass
                            break
                        else:
                            if not use_dense_solver and not np.all(np.isfinite(delta)):
                                cached_jacobian = None
                                self._sparse_linear_solver.invalidate()
                                if confirming_pending:
                                    x_iter[:] = confirming_state
                                    substep_converged = True
                                else:
                                    pass
                                break
                            else:
                                pass
                            if diagnostics_enabled and not use_dense_solver and ctx.used_fallback:
                                # A finite diagnostic fallback is not retained-LU eligibility.
                                cached_jacobian = None
                                self._sparse_linear_solver.invalidate()
                            else:
                                pass

                        if diag_cfg.enable_backtracking:
                            backtracking_residual_evaluator.set_context(
                                kernel_list=kernel_list,
                                full_params=full_params,
                                x_prev=x_prev,
                                dx_prev=kernel_derivatives,
                                h_eff=h_eff,
                                x_prev2=x_prev2,
                            )

                            maybe_apply_backtracking(
                                x_iter,
                                delta,
                                res_norm_inf,
                                trial_x,
                                trial_res,
                                evaluate_residual=backtracking_residual_evaluator.evaluate,
                                config=diag_cfg,
                            )
                        else:
                            x_iter += delta
                        last_residual = float(res_norm_inf)
                    if substep_converged or not attempt_reused_jacobian or attempt > 0 or state_event_retry_time is not None:
                        break
                    else:
                        x_iter[:] = attempt_seed
                        cached_jacobian = None
                        self._sparse_linear_solver.invalidate()
                        inherited_factor_retries += 1
                if substep_converged and state_event_retry_time is None:
                    last_macro_iterations = k
                else:
                    cached_jacobian = None
                    self._sparse_linear_solver.invalidate()

                if not substep_converged:
                    converged = False
                    if i == 0 and is_first_local_step:
                        well_initialized = False
                    else:
                        pass
                else:
                    pass

                if state_event_retry_time is None:
                    state_event_retry_time = resolve_solver_boundary_step(
                        boundary_updater=active_boundary_updater,
                        accepted=substep_converged,
                        params=full_params,
                        committed_time=float(t_curr),
                        committed_state=x_iter,
                        capabilities=boundary_capabilities,
                    )
                else:
                    pass

                # Resolve rejection once, then stop before any accepted history changes.
                if not substep_converged:
                    break
                else:
                    pass

                if substep_converged and state_event_retry_time is None:
                    # A post-acceptance native sample may publish new held
                    # outputs. Retain them for the next aligned sub-step.
                    ev_params[:] = full_params[:n_event_params]
                else:
                    pass

                if state_event_retry_time is not None:
                    x_iter[:] = x_prev
                else:
                    if method == DynamicIntegrationMethod.DaeBDF2:
                        # Compute from both untouched accepted states, then scatter
                        # by base UID before committing either history buffer.
                        if bdf2_startup_pending:
                            base_slopes[:] = (x_iter - x_prev) / h_eff
                        else:
                            base_slopes[:] = (1.5 * x_iter - 2.0 * x_prev + 0.5 * x_prev2) / h_eff
                        base_index: int
                        for diff_index, base_index in enumerate(diff_base_indices):
                            if base_index >= 0:
                                dx_prev[diff_index] = base_slopes[base_index]
                            else:
                                pass
                        bdf2_startup_pending = False
                    elif method == DynamicIntegrationMethod.DaeTrapezoidal:
                        if n_diff == 0:
                            dx_prev[:n_states] = (
                                    (2.0 / h_eff) * (x_iter[:n_states] - x_prev[:n_states]) - dx_prev[:n_states]
                            )
                        else:
                            kernel_derivatives[diff_base_rows] = (
                                    (2.0 / h_eff) * (x_iter[diff_base_rows] - x_prev[diff_base_rows])
                                    - kernel_derivatives[diff_base_rows]
                            )
                            dx_prev[diff_rows_with_base] = kernel_derivatives[diff_base_rows]
                    elif n_diff == 0:
                        dx_prev[:n_states] = (
                                (x_iter[:n_states] - x_prev[:n_states]) / h_eff
                        )
                    else:
                        kernel_derivatives[diff_base_rows] = (
                                (x_iter[diff_base_rows] - x_prev[diff_base_rows]) / h_eff
                        )
                        dx_prev[diff_rows_with_base] = kernel_derivatives[diff_base_rows]

                    x_prev2[:] = x_prev

                    x_prev[:] = x_iter
                    t_local_prev = t_curr
                    is_first_local_step = False


            # A partially accepted macro interval is not an output sample.
            if not converged:
                break
            else:
                pass

            self.y[i + 1, :] = x_prev
            self.dy[i + 1, :] = dx_prev
            completed_samples += 1

        self._last_sim_loop_time = time.perf_counter() - loop_start
        self._last_runtime_stats = dict(
            sim_loop_s=self._last_sim_loop_time,
            total_newton_iterations=float(total_newton_iterations),
            jacobian_evaluations=float(jacobian_evaluation_count),
            factorization_reuse_hits=float(factorization_reuse_hits),
            forced_factorization_invalidations=float(forced_factorization_invalidations),
            inherited_factor_retries=float(inherited_factor_retries),
            confirming_corrections=float(confirming_corrections),
            aligned_substeps=float(aligned_substep_count),
            macro_steps=float(completed_samples - 1),
        )

        if self.verbose:
            print(f"JIT (AD) Finished: {time.time() - t_start:.4f}s")
        else:
            pass
        #
        # pr.disable()
        # pr.dump_stats("profile_grid_for_loads_simulation_1_second_v4.pstat")
        return t[:completed_samples].copy(), self.y[:completed_samples, :].copy(), self.dy[:completed_samples, :].copy(), well_initialized, converged

    def get_backend_build_stats(self) -> Dict[str, float]:
        """
        Return setup timings collected during backend compilation.

        :return: Backend build statistics.
        :rtype: Dict[str, float]
        """
        return dict(self._backend_build_stats)

    def get_last_runtime_stats(self) -> Dict[str, float]:
        """
        Return runtime statistics collected during the latest simulation.

        :return: Runtime statistics.
        :rtype: Dict[str, float]
        """
        return dict(self._last_runtime_stats)

    def get_last_sim_loop_time(self) -> float:
        """
        Return the latest integration-loop wall time.

        :return: Latest loop time in seconds.
        :rtype: float
        """
        return self._last_sim_loop_time
