# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import numba as nb
import scipy.sparse as sp
import time
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Expr, BinOp, UnOp, Func

from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.enumerations import DynamicIntegrationMethod

from VeraGridEngine.Utils.Symbolic.jit_compiler import EquationCompiler
from VeraGridEngine.Utils.Symbolic.diagnostic import (with_newton_diagnostics, NewtonDiagnosticsConfig,
                                                      NewtonSolveContext, dense_lstsq_fallback,
                                                      sparse_lsqr_fallback)
from VeraGridEngine.basic_structures import Vec, Mat
from typing import Tuple, Callable, List, Any, Dict, Set, Union
import uuid
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
        return nb.njit(signature, fastmath=fastmath, cache=cache)(py_func)
    else:
        return nb.njit(fastmath=fastmath, cache=cache)(py_func)

# ==============================================================================
# Sparse Forward-Mode AD Jacobian with Graph Coloring (JVP-based)
# ==============================================================================

@nb.njit(cache=True, fastmath=True)
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
    order: List[int] = list(np.argsort(-degrees))
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

class SparseADJacobian:
    """
    Sparse Jacobian evaluator with DEBUG TIMING.
    """
    __slots__ = [
        'equations', 'variables', 'parameters', 'method', 'use_cse', 'dtype',
        'n_rows', 'n_cols', 'var_map', 'param_map', 'col_rows', 'J',
        'colors', 'n_colors', 'color_groups', 'color_ptr', 'color_cols',
        'col_ptr', 'row_idx', 'data_idx', '_compiler', 'ad_kernels', '_seeds'
    ]

    def __init__(self,
                 equations: List[Any],
                 variables: List[Any],
                 parameters: List[Any],
                 method: DynamicIntegrationMethod,
                 use_cse: bool = True,
                 dtype: Any=np.float64)-> None:

        t_start = time.perf_counter()
        print(f"   [AD-Debug] Init started for {len(equations)} eqs...")

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
        print(f"   [AD-Debug] CSC Matrix built in {t_csc - t_sparsity:.4f}s")

        # 3) Coloring
        self.colors, self.n_colors = greedy_color_columns(self.col_rows, self.n_rows)
        groups: List[List[int]] = [list() for _ in range(self.n_colors)]
        for j in range(self.n_cols):
            groups[self.colors[j]].append(j)
        self.color_groups = groups

        t_color = time.perf_counter()
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
        print(f"   [AD-Debug] Scatter Map built in {t_scatter - t_color:.4f}s")

        # 5) Compile Optimization: Colored Kernels
        self._compiler = EquationCompiler(variables=variables, parameters=parameters, method=method)
        self.ad_kernels: List[Callable] = list()

        print(f"   [AD-Opt] Compiling {self.n_colors} specialized color kernels...")
        t_comp_start = time.perf_counter()

        for c in range(self.n_colors):
            active_cols = set(self.color_groups[c])
            k_name = f"ad_step_color_{c}_{uuid.uuid4().hex[:4]}"

            py_ad = self._compiler.compile_ad_kernel(
                equations,
                func_name=k_name,
                use_cse=use_cse,
                active_indices=active_cols
            )

            kernel = _safe_njit(py_ad, cache=False, fastmath=True)
            self.ad_kernels.append(kernel)

        t_comp_end = time.perf_counter()
        print(f"   [AD-Opt] Kernels compiled in {t_comp_end - t_comp_start:.4f}s")
        print(f"   [AD-Debug] Total Init Time: {t_comp_end - t_start:.4f}s")

        self._seeds = np.zeros(self.n_cols, dtype=self.dtype)

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

        data = self.J.data
        dummy_seeds = self._seeds

        for c in range(self.n_colors):
            kernel = self.ad_kernels[c]
            jvp = kernel(states, dummy_seeds, params, history, d_history, h, history2)

            _scatter_color_jvp_to_csc_data(jvp, data,
                                           self.color_ptr,self.col_ptr,
                                           self.row_idx, self.data_idx,
                                           c)
        return self.J

class JitAdSolver:
    __slots__ = [
        'problem', 't0', 't_end', 'h', 'method', 'pred_method', 'dense_threshold', 'verbose',
        'steps', 't', 'y', 'dy',  'jit_kernels_ad', 'jit_jacobian_ad',
        'state_vars', 'algebraic_vars', 'state_eqs', 'algebraic_eqs'
    ]
    def __init__(self,
                 problem: EmtProblemTemplate,
                 t0: float,
                 t_end: float,
                 h: float,
                 method: DynamicIntegrationMethod = DynamicIntegrationMethod.DaeTrapezoidal,
                 pred_method: DynamicIntegrationMethod = None,
                 dense_threshold: int = 100,
                 verbose: bool = False)-> None:
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
        """
        self.problem = problem
        self.t0 = t0
        self.h = h
        self.method = method
        self.pred_method = pred_method
        self.dense_threshold = dense_threshold
        self.verbose = verbose
        self.t_end = t_end

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

    def build_jit_ad(self, only_jacobian: bool = False)-> None:
        """
        Compiles the residual kernel using batching and prepares the Sparse AD Jacobian.

        :param only_jacobian: If True, skips residual compilation (used by Vectorized Engine fallback).
        :type only_jacobian: bool
        :rtype: None
        """
        if self.method in self.jit_kernels_ad and not only_jacobian:
            return
        else:
            pass

        print(
            f"--- [JIT-AD] Compiling {'Jacobian ONLY' if only_jacobian else 'Implicit Kernel + AD Jacobian'} ({self.method}) ---")

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
        if not only_jacobian and self.method not in self.jit_kernels_ad:
            compiler = EquationCompiler(variables=sorted_vars, parameters=all_params, method=self.method)
            BATCH_SIZE = 100
            n_eqs = len(equations)
            batched_kernels: List[Callable] = list()

            print(f"   [JIT-AD] Splitting {n_eqs} residual eqs into {int(np.ceil(n_eqs / BATCH_SIZE))} batches...")
            t0 = time.time()

            for i in range(0, n_eqs, BATCH_SIZE):
                chunk = equations[i: i + BATCH_SIZE]
                fname = f"jit_step_{self.method}_ad_part_{i}"
                py_func = compiler.compile(chunk, func_name=fname, use_cse=True, offset=i, inplace=True)
                jit_func = _safe_njit(py_func, cache=True, fastmath=True)
                batched_kernels.append(jit_func)

            print(f"   [JIT-AD] Residual Batches compiled in {time.time() - t0:.4f}s")
            self.jit_kernels_ad[self.method] = batched_kernels
        else:
            pass

        # --- PART 2: JACOBIAN (O(N) setup, needed for normal and Vectorized fallback) ---
        if self.method not in self.jit_jacobian_ad:
            jac = SparseADJacobian(equations=equations, variables=sorted_vars, parameters=all_params,
                                   method=self.method, use_cse=True)
            self.jit_jacobian_ad[self.method] = jac
        else:
            pass

    def simulate(self,
                 x0: Union[Vec | None] = None,
                 dx0: Union[Vec | None] = None,
                 params0: Union[Vec | None] = None,
                 boundary_updater: Any | None = None) -> Tuple[Vec, Mat]:
        """
        Main JIT simulation loop using the Automatic Differentiation (AD) backend.

        :param x0: Initial state vector.
        :param dx0: Initial derivative vector.
        :param params0: Initial event parameters.
        :param boundary_updater: Wrapper object to update boundary conditions.
        :return: A tuple containing the time vector and state trajectory matrix.
        """
        t_start = time.time()
        method = self.method

        if method not in self.jit_kernels_ad:
            self.build_jit_ad()
        else:
            pass

        kernel_list = self.jit_kernels_ad[method]
        current_jacobian = self.jit_jacobian_ad[method]

        n_eqs = self.problem.get_all_vars_number()
        n_diff = self.problem.get_diff_var_number()
        n_states = self.problem.get_states_number()

        use_dense_solver = (n_eqs <= self.dense_threshold)

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

        self.y[0, :] = x0.copy()
        self.dy[0, :] = dx0.copy()

        x_prev = x0.copy()
        dx_prev = dx0.copy()
        x_prev2 = x0.copy()
        x_iter = x0.copy()

        static_vals = np.array([c.value for c in self.problem.get_parameters_values()], dtype=np.float64)
        n_event_params = self.problem.get_variable_parameter_number()

        if params0 is not None:
            ev_params = params0.copy()
        else:
            ev_params = np.zeros(n_event_params, dtype=np.float64)

        trace_collector = self.problem.get_newton_trace_collector()

        diag_cfg = NewtonDiagnosticsConfig(step_norm_explode=1e6, dense_cond_warn=1e12, compute_dense_cond=True,
                                           enable_fallback=True)
        dense_solve = with_newton_diagnostics(np.linalg.solve, fallback_solve=dense_lstsq_fallback,
                                              collector=trace_collector, config=diag_cfg, solver_name="dense")
        sparse_solve = with_newton_diagnostics(sp.linalg.spsolve, fallback_solve=sparse_lsqr_fallback,
                                               collector=trace_collector, config=diag_cfg, solver_name="sparse")

        if self.verbose:
            print(f"-> Starting JIT (AD) Simulation ({method}, {self.steps} steps)...")
        else:
            pass

        for i in range(self.steps):
            if self.verbose:
                print(f"Simulating at step {i}")
            else:
                pass

            t_curr = t[i + 1]

            # Parameter update via Problem
            ev_params = self.problem.def_event_params_fn(ev_params, float(t_curr))
            full_params = np.concatenate((ev_params, static_vals))

            if boundary_updater is not None:
                boundary_updater.update(t_curr, x_prev, full_params)
            else:
                pass

            x_iter[:] = x_prev

            # PREDICTOR
            if i == 0 and method == DynamicIntegrationMethod.DaeTrapezoidal:
                predictor = Predictor(n_states=n_states)
                predictor.predict(
                    x_iter=x_iter,
                    x_prev=x_prev,
                    dx_prev=dx_prev,
                    h=self.h,
                    pred_method=self.pred_method,
                )

            for k in range(15):
                ctx = NewtonSolveContext(t=float(t_curr), step_idx=int(i), newton_iter=int(k), phase="jit_ad",
                                         method=str(method))

                # Execute batched residuals
                res = np.zeros(n_eqs, dtype=np.float64)
                for kn in kernel_list:
                    kn(x_iter, full_params, x_prev, dx_prev, self.h, res, x_prev2)

                if np.linalg.norm(res, np.inf) < 1e-5:
                    break
                else:
                    pass

                # Evaluate AD Jacobian
                J = current_jacobian(states=x_iter, params=full_params, history=x_prev, d_history=dx_prev, h=self.h,
                                     history2=x_prev2)

                if use_dense_solver:
                    delta = dense_solve(J.toarray(), -res, ctx)
                else:
                    delta = sparse_solve(J, -res, ctx)
                x_iter += delta

            self.y[i + 1, :] = x_iter
            self.dy[i, :] = dx_prev

            if method == DynamicIntegrationMethod.DaeTrapezoidal:
                dx_prev[:n_states] = ((2.0 / self.h) * (x_iter[:n_states] - x_prev[:n_states]) - dx_prev[:n_states])
            elif method == DynamicIntegrationMethod.DaeBDF2:
                x_prev2 = x_prev.copy()
            else:
                dx_prev[:n_states] = ((x_iter[:n_states] - x_prev[:n_states]) / self.h)

            if method != DynamicIntegrationMethod.DaeBDF2:
                x_prev2 = x_prev.copy()
            else:
                pass

            x_prev = x_iter.copy()

        if self.verbose:
            print(f"JIT (AD) Finished: {time.time() - t_start:.4f}s")
        else:
            pass

        return self.t, self.y, self.dy