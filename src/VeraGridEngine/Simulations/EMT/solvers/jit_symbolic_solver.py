# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Set, Tuple, Callable, List, Any, Union
import numpy as np
import numba as nb
import scipy.sparse as sp
import time
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.enumerations import DynamicIntegrationMethod

from VeraGridEngine.Utils.Symbolic.symbolic import Var, Const, Expr, BinOp, UnOp, Func
from VeraGridEngine.Utils.Symbolic.jit_compiler import EquationCompiler

from VeraGridEngine.Utils.Symbolic.diagnostic import (with_newton_diagnostics, NewtonDiagnosticsConfig,
                                                      NewtonSolveContext, dense_lstsq_fallback,
                                                      sparse_lsqr_fallback)
from VeraGridEngine.basic_structures import Vec, Mat, IntVec, CscMat


def get_vars_in_expr(expr: Expr) -> Set[int]:
    """
    Recursively collects UIDs of all variables present in an expression.

    :param expr: The symbolic expression to analyze.
    :type expr: Expr
    :return: A set containing the unique identifiers (UIDs) of the variables.
    :rtype: Set[int]
    """
    found: Set[int] = set()
    stack: List[Expr] = list()
    visited: Set[int] = set()

    stack.append(expr)

    while stack:
        node: Expr = stack.pop()
        node_id: int = id(node)

        if node_id in visited:
            # Explicit state: The node has already been processed.
            # We do nothing to prevent infinite loops in Directed Acyclic Graphs (DAGs).
            pass
        else:
            visited.add(node_id)

            # Flat type dispatch to evaluate AST nodes.
            # This avoids deep nesting and keeps the execution path predictable.
            if isinstance(node, Var):
                found.add(node.uid)

                # Since the node is guaranteed to be a Var instance, we can safely
                # access the base_var property directly.
                if node.base_var is not None:
                    found.add(node.base_var.uid)
                else:
                    # Terminal state: The variable is a base state, no derivative to track.
                    pass

            elif isinstance(node, Func):
                stack.append(node.arg)

            elif isinstance(node, UnOp):
                stack.append(node.operand)

            elif isinstance(node, BinOp):
                stack.append(node.left)
                stack.append(node.right)

            else:
                # Terminal state: Const nodes or unknown types have no children to traverse.
                pass

    return found

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



class BoundaryUpdateWrapper:
    """
    Interface for injecting boundary conditions and events before the Newton step.
    Users must inherit from this class to update parameters safely.
    """
    __slots__ = []  # No state allowed in the base class

    def update(self, t: float, x: Vec, params: Vec) -> None:
        """
        Updates the parameters vector in place based on the current time and state.

        :param t: The current simulation time.
        :type t: float
        :param x: The current state vector.
        :type x: Vec
        :param params: The parameter vector to be modified.
        :type params: Vec
        :rtype: None
        """
        pass  # Explicit no-op for base class

class HybridJacobianEvaluator:
    """
    Evaluates the JIT-compiled Jacobian and formats it as either Dense or Sparse.
    This class replaces nested functions to ensure memory determinism and strict type safety.
    """
    __slots__ = ['kernel_jit', 'use_sparse', 'n_vars', 'alpha_mult', 'np_rows', 'np_cols']

    def __init__(self,
                 kernel_jit: Callable,
                 use_sparse: bool,
                 n_vars: int,
                 alpha_mult: float,
                 np_rows: Union[IntVec| None] = None,
                 np_cols: Union[IntVec| None] = None) -> None:
        """
        Initializes the evaluator with the compiled Numba kernel and matrix topology.

        :param kernel_jit: The compiled Numba function for the Jacobian.
        :type kernel_jit: Callable
        :param use_sparse: Flag indicating if the output should be a sparse matrix.
        :type use_sparse: bool
        :param n_vars: The number of variables (size of the N x N matrix).
        :type n_vars: int
        :param alpha_mult: The scaling factor for the integration method.
        :type alpha_mult: float
        :param np_rows: Row indices for the sparse matrix format.
        :type np_rows: IntVec
        :param np_cols: Column indices for the sparse matrix format.
        :type np_cols: IntVec
        :rtype: None
        """
        self.kernel_jit = kernel_jit
        self.use_sparse = use_sparse
        self.n_vars = n_vars
        self.alpha_mult = alpha_mult
        self.np_rows = np_rows
        self.np_cols = np_cols

    def evaluate(self, states: Vec, params: Vec, history: Vec, d_history: Vec, h: float,
                 history2: Union[Vec| None] = None) -> Mat | CscMat:
        """
        Executes the JIT kernel and constructs the resulting Jacobian matrix.

        :param states: The current state vector.
        :type states: Vec
        :param params: The parameter vector.
        :type params: Vec
        :param history: The state history vector.
        :type history: Vec
        :param d_history: The derivative history vector.
        :type d_history: Vec
        :param h: The integration time step.
        :type h: float
        :param history2: The secondary history vector (for BDF2).
        :type history2: Vec
        :return: The assembled Jacobian matrix (Dense or Sparse CSC).
        :rtype: Mat | CscMat
        """
        # Allocate a new array to append the alpha scaling factor required by the kernel
        params_with_alpha: Vec = np.empty(len(params) + 1, dtype=np.float64)
        params_with_alpha[:-1] = params
        params_with_alpha[-1] = self.alpha_mult / h

        # Execute the JIT compiled kernel to obtain the raw data values
        data: Vec = self.kernel_jit(states, params_with_alpha, history, d_history, h, history2)

        # Assemble the matrix based on the requested storage format
        if self.use_sparse:
            return sp.csc_matrix((data, (self.np_rows, self.np_cols)), shape=(self.n_vars, self.n_vars))
        else:
            return data.reshape((self.n_vars, self.n_vars))

class JitSymbolicSolver:

    __slots__ = [
        'problem', 't0', 't_end', 'h', 'method', 'pred_method', 'dense_threshold', 'verbose',
        'steps', 't', 'y', 'dy', 'jit_kernels', 'jit_jacobian_symbolic',
        'state_vars', 'algebraic_vars', 'state_eqs', 'algebraic_eqs', 'diff_vars',
        'jit_compiler'
    ]

    def __init__(self,
                 problem: EmtProblemTemplate,
                 t0: float,
                 t_end: float,
                 h: float,
                 method: DynamicIntegrationMethod = DynamicIntegrationMethod.DaeTrapezoidal,
                 pred_method:DynamicIntegrationMethod = None,
                 dense_threshold: int = 100,
                 verbose: bool = False)-> None:
        """
        :param problem: The DAE problem definition.
        :param t0: Initial time.
        :param t_end: End time.
        :param h: Time step.
        :param method: DynamicIntegrationMethod (DaeTrapezoidal, DaeBackEuler, DaeBDF2).
        :param pred_method: DynamicIntegrationMethod used in the predictor step if method is explicit.
        :param dense_threshold: Threshold to switch between dense and sparse linear solvers.
        :param verbose: Print compilation and simulation timings.
        """
        self.jit_compiler = None
        self.problem = problem
        self.t0 = t0
        self.h = h
        self.method = method
        self.pred_method = pred_method
        self.dense_threshold = dense_threshold
        self.verbose = verbose

        self.steps = int(np.ceil((t_end - t0) / h))
        self.t: Vec = np.empty(self.steps + 1)
        self.y: Mat = np.empty((self.steps + 1, self.problem.get_all_vars_number()))
        self.dy: Mat = np.empty((self.steps + 1, self.problem.get_diff_var_number()))

        # Solver specific caches
        self.jit_kernels = dict()
        self.jit_jacobian_symbolic = dict()

        self.state_vars = self.problem.get_state_vars()
        self.algebraic_vars = self.problem.get_algebraic_vars()
        self.state_eqs = self.problem.get_state_eqs()
        self.algebraic_eqs = self.problem.get_algebraic_eqs()
        self.diff_vars  = self.problem.get_diff_vars()

    # ==============================================================================
    # 2. JIT IMPLICIT ENGINE (Optimized with Batching)
    # ==============================================================================

    def build_jit_kernel(self, method: DynamicIntegrationMethod)-> None:
        """
        Compiles the numerical residual function using JIT.
        It uses a batching strategy (splitting equations into chunks) to prevent
        Numba/LLVM from hanging when compiling very large non-linear systems.

        :param method: The dynamic integration method to compile for.
        :type method: DynamicIntegrationMethod
        :rtype: None
        """
        print(f"--- [JIT] Compiling Implicit Kernel ({method}) ---")

        sorted_vars: List[Any] = list()
        sorted_vars.extend(self.state_vars)
        sorted_vars.extend(self.algebraic_vars)

        all_params: List[Any] = list()
        all_params.extend(self.problem.get_variable_parameters())
        all_params.extend(self.problem.get_constant_parameters())

        equations: List[Expr] = list()

        for i, rhs in enumerate(self.state_eqs):
            # sv = self.state_vars[i]
            # d_term = Var(name=f"d_{sv.name}", base_var=sv)
            d_term = self.diff_vars[i]  # real associated diff_var
            equations.append(d_term - rhs)

        equations.extend(self.algebraic_eqs)
        self.jit_compiler = EquationCompiler(variables=sorted_vars, parameters=all_params, method=method)

        # Batch compilation strategy
        BATCH_SIZE = 100
        n_eqs = len(equations)
        batched_kernels = []

        for i in range(0, n_eqs, BATCH_SIZE):
            chunk = equations[i: i + BATCH_SIZE]
            f_name = f"jit_step_{method}_part_{i}"

            # Compile inplace: the function writes directly to the 'residuals' array
            py_func = self.jit_compiler.compile(chunk, func_name=f_name, use_cse=True, offset=i, inplace=True)
            jit_func = nb.njit(cache=True, fastmath=True)(py_func)
            batched_kernels.append(jit_func)

        self.jit_kernels[method] = batched_kernels

    def _build_jit_symbolic_hybrid(self, method: DynamicIntegrationMethod, use_sparse: bool)-> None:
        """
        Compiles a Hybrid Symbolic Jacobian.
        It generates a Numba kernel that evaluates the Jacobian entries and
        returns either a Scipy CSC Matrix (Sparse mode) or a Numpy Array (Dense mode).
        """
        cache_key = f"{method}_{use_sparse}"
        if cache_key in self.jit_jacobian_symbolic:
            return
        else:
            pass

        print(f"--- [JIT-SD] Compiling Hybrid Symbolic Jacobian ({'SPARSE' if use_sparse else 'DENSE'}) ---")
        t0 = time.time()

        sorted_vars: List[Any] = list()
        sorted_vars.extend(self.state_vars)
        sorted_vars.extend(self.algebraic_vars)

        all_params: List[Any] = list()
        all_params.extend(self.problem.get_variable_parameters())
        all_params.extend(self.problem.get_constant_parameters())

        var_uid_to_idx: dict = dict()
        for i, v in enumerate(sorted_vars):
            var_uid_to_idx[v.uid] = i

        equations: List[Expr] = list()

        for i, rhs in enumerate(self.state_eqs):
            d_term = self.diff_vars[i]
            equations.append(d_term - rhs)
        base_var_uid_to_diff_var: dict = {dv.base_var.uid: dv for dv in self.diff_vars}
        equations.extend(self.algebraic_eqs)

        N = len(sorted_vars)
        n_states = len(self.state_vars)
        jac_expression: List[Expr] = list()
        rows: List[int] = list()
        cols: List[int] = list()
        alpha_sym = Var("alpha_scaling_factor")

        if use_sparse:
            nnz = 0
            for r, eq in enumerate(equations):
                dependencies = get_vars_in_expr(eq)

                if r < n_states:
                    dependencies.add(self.state_vars[r].uid)
                else:
                    pass

                for v in sorted_vars:
                    if v.uid in dependencies:

                        c = var_uid_to_idx[v.uid]
                        d_direct = eq.diff(v)

                        dv = base_var_uid_to_diff_var.get(v.uid, None)
                        d_diff = eq.diff(dv) if dv is not None else Const(0)

                        final_expr = d_direct if (isinstance(d_diff, Const) and d_diff.value == 0) else (
                                    d_direct + alpha_sym * d_diff)
                        final_expr = final_expr.simplify()

                        if not (isinstance(final_expr, Const) and final_expr.value == 0):
                            jac_expression.append(final_expr)
                            rows.append(r)
                            cols.append(c)
                            nnz += 1
                        else:
                            pass

                    else:
                        pass

            print(f"   [JIT-SD] Topology Analysis: {nnz} non-zeros (Sparsity: {1.0 - nnz / (N ** 2):.2%})")
        else:
            for r, eq in enumerate(equations):
                for c, v in enumerate(sorted_vars):

                    d_direct = eq.diff(v)

                    dv = base_var_uid_to_diff_var.get(v.uid, None)
                    d_diff = eq.diff(dv) if dv is not None else Const(0)

                    final_expr = (d_direct + alpha_sym * d_diff).simplify()
                    jac_expression.append(final_expr)

        compile_params: List[Any] = list()
        compile_params.extend(all_params)
        compile_params.append(alpha_sym)
        compiler = EquationCompiler(variables=sorted_vars, parameters=compile_params, method=method)
        func_name = f"jac_eval_{method}_{'sparse' if use_sparse else 'dense'}"
        kernel_py = compiler.compile(jac_expression, func_name=func_name, use_cse=True)
        kernel_jit = nb.njit(cache=False, fastmath=True)(kernel_py)

        if method == DynamicIntegrationMethod.DaeTrapezoidal:
            alpha_mult = 2.0
        elif method == DynamicIntegrationMethod.DaeBDF2:
            alpha_mult = 1.5
        else:
            alpha_mult = 1.0

        np_rows: Union[IntVec | None] = np.array(rows, dtype=np.int32) if use_sparse else None
        np_cols: Union[IntVec | None] = np.array(cols, dtype=np.int32) if use_sparse else None

        evaluator_obj = HybridJacobianEvaluator(
            kernel_jit=kernel_jit,
            use_sparse=use_sparse,
            n_vars=N,
            alpha_mult=alpha_mult,
            np_rows=np_rows,
            np_cols=np_cols
        )

        self.jit_jacobian_symbolic[cache_key] = evaluator_obj
        print(f"   [JIT-SD] Compilation finished in {time.time() - t0:.4f}s")

    def simulate(self,
                 x0: Union[Vec | None] = None,
                 dx0: Union[Vec | None] = None,
                 params0: Union[Vec | None] = None,
                 boundary_updater: BoundaryUpdateWrapper| None = None) -> Tuple[Vec, Mat, Mat]:
        """
        Main JIT simulation loop using the Symbolic Differentiation (SD) backend.
        :param x0: Initial state vector.
        :param dx0: Initial derivative vector.
        :param params0: Initial event parameters.
        :param boundary_updater: Boundary condition updater, defaults to None.
        :return: A tuple containing the time vector and the state trajectory matrix. Tuple[Vec, Mat]
        """
        t_start = time.time()
        method = self.method

        if method not in self.jit_kernels:
            self.build_jit_kernel(method)
        else:
            pass

        kernel_list = self.jit_kernels[method]

        n_eqs = self.problem.get_all_vars_number()
        n_diff = self.problem.get_diff_var_number()
        n_states = self.problem.get_states_number()

        use_dense_solver = (n_eqs <= self.dense_threshold)
        self._build_jit_symbolic_hybrid(method, use_sparse=not use_dense_solver)
        jac_key = f"{method}_{not use_dense_solver}"
        current_jacobian = self.jit_jacobian_symbolic[jac_key]

        if self.verbose:
            mode_str = "DENSE" if use_dense_solver else "SPARSE"
            print(f"   [Config] System N={n_eqs}. Using {mode_str} linear solver (Threshold={self.dense_threshold}).")
        else:
            pass

        if x0 is None:
            x0 = self.problem.get_x0()
        else:
            pass
        if dx0 is None:
            dx0 = self.problem.get_dx0()
        else:
            pass

        self.t[0] = self.t0
        self.y[0, :] = x0.copy()
        self.dy[0,:] = dx0.copy()

        x_prev, dx_prev, x_prev2 = x0.copy(), dx0.copy(), x0.copy()
        x_iter = x0.copy()

        static_vals = np.array([c.value for c in self.problem.get_parameters_values()])
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
            print(f"-> Starting JIT Simulation ({method}, {self.steps} steps)...")
        else:
            pass

        for i in range(self.steps):
            if self.verbose:
                print(f"Simulating at step {i}")
            else:
                pass

            t_curr = self.t0 + (i + 1) * self.h
            self.t[i + 1] = t_curr

            ev_params = self.problem.def_event_params_fn(ev_params, float(t_curr))
            full_params = np.concatenate((ev_params, static_vals))

            if boundary_updater is not None:
                boundary_updater.update(t_curr, x_prev, full_params)
            else:
                pass

            # PREDICTOR
            if i == 0 and method == DynamicIntegrationMethod.DaeTrapezoidal:
                predictor = Predictor(n_states=n_states)
                predictor.predict(
                    x_iter=x_iter,
                    x_prev=x_prev,
                    dx_prev=dx_prev,
                    h=self.h,
                    pred_method= self.pred_method,
                )


            for k in range(15):
                ctx = NewtonSolveContext(t=float(t_curr), step_idx=int(i), newton_iter=int(k), phase="jit",
                                         method=str(method))

                res = np.zeros(n_eqs, dtype=np.float64)
                for kn in kernel_list:
                    kn(x_iter, full_params, x_prev, dx_prev, self.h, res, x_prev2)

                if i == 0 and k == 0 and self.verbose:
                    states = list(self.problem.get_state_vars())
                    algs = list(self.problem.get_algebraic_vars())

                    n_states = len(states)
                    n_algs = len(algs)

                    print("\n[Residual Debug] Sizes:")
                    print(f"  n_eqs(res)       = {n_eqs}")
                    print(f"  n_states         = {n_states}")
                    print(f"  n_algebraic_vars = {n_algs}")
                    print(f"  n_states+n_algs  = {n_states + n_algs}")
                    if n_eqs != (n_states + n_algs):
                        print("  [WARNING] n_eqs != n_states+n_algs -> residual indexing is not vars-based.\n")

                    abs_res = np.abs(res)
                    top_indices = np.argsort(abs_res)[-20:][::-1]

                    # -------------------------
                    # Pretty table formatting
                    # -------------------------
                    W_IDX = 4
                    W_KIND = 5
                    W_LABEL = 62  # adjust if you want more/less text
                    W_RES = 13
                    W_ABS = 13
                    W_XIT = 13
                    W_XPR = 13
                    W_DXPR = 13

                    def _clip(s: str, width: int) -> str:
                        s = str(s)
                        if len(s) <= width:
                            return s.ljust(width)
                        if width <= 3:
                            return s[:width]
                        return (s[:width - 3] + "...")

                    def _fmt_num(x) -> str:
                        # right-aligned scientific; keep NaN readable
                        if x is None:
                            return " " * W_RES
                        try:
                            xf = float(x)
                        except Exception:
                            return str(x).rjust(W_RES)
                        if np.isnan(xf):
                            return "nan".rjust(W_RES)
                        return f"{xf: .6e}".rjust(W_RES)

                    # Header
                    title = f">>> TOP 20 LARGEST RESIDUALS (Step {i}, Iter {k}) <<<"
                    print("\n" + title)
                    header = (
                        f"{'idx':>{W_IDX}} | "
                        f"{'kind':<{W_KIND}} | "
                        f"{'label':<{W_LABEL}} | "
                        f"{'res':>{W_RES}} | "
                        f"{'|res|':>{W_ABS}} | "
                        f"{'x_iter':>{W_XIT}} | "
                        f"{'x_prev':>{W_XPR}} | "
                        f"{'dx_prev':>{W_DXPR}}"
                    )
                    print(header)
                    print("-" * len(header))

                    for idx in top_indices:
                        if idx < n_states:
                            sv = states[idx]
                            kind = "STATE"
                            label = f"d_{sv.name} - rhs_{sv.name}"
                            x_it = x_iter[idx]
                            x_pr = x_prev[idx]
                            dx_pr = dx_prev[idx]
                        else:
                            j = idx - n_states
                            kind = "ALG"
                            if j < n_algs:
                                label = f"alg for {algs[j].name}"
                                x_it = x_iter[n_states + j]
                                x_pr = x_prev[n_states + j]
                            else:
                                label = f"ALG_EQ_{j}"
                                x_it = np.nan
                                x_pr = np.nan
                            dx_pr = np.nan

                        row = (
                            f"{idx:>{W_IDX}d} | "
                            f"{kind:<{W_KIND}} | "
                            f"{_clip(label, W_LABEL)} | "
                            f"{_fmt_num(res[idx])} | "
                            f"{_fmt_num(abs_res[idx])} | "
                            f"{_fmt_num(x_it)} | "
                            f"{_fmt_num(x_pr)} | "
                            f"{_fmt_num(dx_pr)}"
                        )
                        print(row)

                    print("-" * len(header))
                    print("=" * len(header) + "\n")

                    # rhs estimate from residuals because res = d_est - rhs
                    # when x_iter == x_prev, d_est for BE is (x - xprev)/h = 0
                    # so rhs ≈ -res for state eqs
                    rhs_est = -res[:n_states].copy()
                    print("[DBG] max|rhs_est - dx_prev|:", np.max(np.abs(rhs_est - dx_prev[:n_states])))

                if np.linalg.norm(res, np.inf) < 1e-6:
                    break
                else:
                    pass

                J_final = current_jacobian.evaluate(states=x_iter, params=full_params, history=x_prev,
                                                    d_history=dx_prev,h=self.h, history2=x_prev2)

                if use_dense_solver:
                    delta = dense_solve(J_final, -res, ctx)
                else:
                    delta = sparse_solve(J_final, -res, ctx)
                x_iter += delta

            self.y[i + 1, :] = x_iter
            self.dy[i , :] = dx_prev

            if method == DynamicIntegrationMethod.DaeTrapezoidal:
                alpha = 2.0 / self.h
                dx_prev[:n_states] = alpha * (x_iter[:n_states] - x_prev[:n_states]) - dx_prev[:n_states]
            elif method == DynamicIntegrationMethod.DaeBDF2:
                x_prev2 = x_prev.copy()
            else:
                dx_prev[:n_states] = (x_iter[:n_states] - x_prev[:n_states]) / self.h

            if method != DynamicIntegrationMethod.DaeBDF2:
                x_prev2 = x_prev.copy()
            else:
                pass

            x_prev = x_iter.copy()

        if self.verbose:
            print(f"JIT Finished: {time.time() - t_start:.4f}s")
        else:
            pass

        return self.t, self.y, self.dy