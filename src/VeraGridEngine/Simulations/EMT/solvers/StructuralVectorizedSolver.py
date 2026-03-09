# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Tuple, Callable, List, Any, Dict, Union, Set
import uuid
import time
import hashlib

import numpy as np
import numba as nb
from scipy.sparse import csc_matrix
from scipy.linalg import lu_factor, lu_solve
from scipy.sparse.linalg import splu, SuperLU

from VeraGridEngine.Utils.Symbolic.symbolic import Var, Expr, Const, BinOp, UnOp, Func
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Utils.Symbolic.jit_compiler import EquationCompiler, MatrixVectorizedCompiler
from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.basic_structures import Vec, Mat


# ==============================================================================
# Generic helpers
# ==============================================================================

def _safe_njit(py_func: Callable[..., Any], fastmath: bool = True, cache: bool = True, signature: Any = None) -> \
Callable[..., Any]:
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


def _canonicalize_node(node: Expr, unique_slots: Dict[int, str], found_vars_ordered: List[Var],
                       seen_nodes: Set[int]) -> str:
    """
    Recursively canonicalizes an expression node to generate a structural signature.
    State containers are passed explicitly to avoid forbidden nested closures.

    :param node: The symbolic expression node.
    :type node: Expr
    :param unique_slots: Dictionary mapping variable UIDs to canonical string slots.
    :type unique_slots: Dict[int, str]
    :param found_vars_ordered: List storing variables in the order they are found.
    :type found_vars_ordered: List[Var]
    :param seen_nodes: Set storing IDs of nodes already processed to avoid duplication.
    :type seen_nodes: Set[int]
    :return: The canonical string representation of the node.
    :rtype: str
    """
    if isinstance(node, Var):
        target_uid: int = node.uid

        if node.base_var is not None:
            target_uid = node.base_var.uid
        else:
            pass

        if target_uid not in unique_slots:
            unique_slots[target_uid] = f"__VAR_{len(unique_slots)}__"
        else:
            pass

        node_id: int = id(node)
        if node_id not in seen_nodes:
            seen_nodes.add(node_id)
            found_vars_ordered.append(node)
        else:
            pass

        return unique_slots[target_uid]

    elif isinstance(node, Const):
        return f"{float(node.value):.6g}"
    elif isinstance(node, BinOp):
        left_str: str = _canonicalize_node(node.left, unique_slots, found_vars_ordered, seen_nodes)
        right_str: str = _canonicalize_node(node.right, unique_slots, found_vars_ordered, seen_nodes)
        return f"({left_str}{node.op}{right_str})"
    elif isinstance(node, UnOp):
        op_str: str = _canonicalize_node(node.operand, unique_slots, found_vars_ordered, seen_nodes)
        return f"{node.op}({op_str})"
    elif isinstance(node, Func):
        arg_str: str = _canonicalize_node(node.arg, unique_slots, found_vars_ordered, seen_nodes)
        return f"{node.op}({arg_str})"
    else:
        return str(node)


def canonicalize_expression(expr: Expr) -> Tuple[str, List[Var]]:
    """
    Generates a canonical string signature and an ordered list of variables
    found in the expression.

    :param expr: The expression to canonicalize.
    :type expr: Expr
    :return: A tuple containing the signature string and the list of variables.
    :rtype: Tuple[str, List[Var]]
    """
    unique_slots: Dict[int, str] = dict()
    found_vars_ordered: List[Var] = list()
    seen_nodes: Set[int] = set()

    canonical_str: str = _canonicalize_node(expr, unique_slots, found_vars_ordered, seen_nodes)
    return canonical_str, found_vars_ordered


def _compile_fused_residual(kernels_data: List[Dict[str, Any]]) -> Callable[..., Any]:
    """
    Compiles a fused residual kernel that calls all sub-kernels in sequence.

    :param kernels_data: List of dictionaries containing the kernel functions and their indices.
    :type kernels_data: List[Dict[str, Any]]
    :return: A Numba JIT compiled fused function.
    :rtype: Callable[..., Any]
    """
    namespace: Dict[str, Any] = dict()
    namespace['np'] = np
    namespace['nb'] = nb

    lines: List[str] = list()
    lines.append("def fused_residual_kernel(states, params, history, d_history, h, args, out, history2=None):")
    lines.append("    out[:] = 0.0")

    for i, k_data in enumerate(kernels_data):
        func_key: str = f"func_{i}"
        namespace[func_key] = k_data['func']

        lines.append(f"    target_{i} = args[{2 * i}]")
        lines.append(f"    indices_{i} = args[{2 * i + 1}]")
        lines.append(f"    r_part_{i} = {func_key}(states, params, history, d_history, h, indices_{i}, history2)")
        lines.append(f"    out[target_{i}] = r_part_{i}")

    exec("\n".join(lines), namespace)
    return nb.njit(fastmath=True, cache=False)(namespace['fused_residual_kernel'])

@nb.njit(cache=True, fastmath=True)
def _scatter_color_jvp_to_csc_data(
        jvp: np.ndarray, data: np.ndarray, color_ptr: np.ndarray,col_ptr: np.ndarray,
        row_idx: np.ndarray, data_idx: np.ndarray, color_id: int) -> None:
    k0 = color_ptr[color_id]
    k1 = color_ptr[color_id + 1]
    for k in range(k0, k1):
        p0 = col_ptr[k]
        p1 = col_ptr[k + 1]
        for p in range(p0, p1):
            data[data_idx[p]] = jvp[row_idx[p]]


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

class EquationGroup:
    """
    Data structure to hold clustered equations for auto-vectorization.
    Replaces the generic dictionary for strict type hinting and safety.
    """
    __slots__ = ['_idx_matrix', '_row_indices', '_template_eq', '_template_vars']

    def __init__(self) -> None:
        self._idx_matrix: List[List[int]] = list()
        self._row_indices: List[int] = list()
        self._template_eq: Expr | None = None
        self._template_vars: List[Var] | None = None

    def add_indices(self, var_indices: List[int], row_index: int) -> None:
        """Adds matrix indices and row index to the cluster."""
        self._idx_matrix.append(var_indices)
        self._row_indices.append(row_index)

    def set_template(self, template_eq: Expr, template_vars: List[Var]) -> None:
        """Sets the structural template for this group."""
        self._template_eq = template_eq
        self._template_vars = template_vars

    def get_idx_matrix(self) -> List[List[int]]:
        """Returns the index matrix."""
        return self._idx_matrix

    def get_row_indices(self) -> List[int]:
        """Returns the row indices."""
        return self._row_indices

    def get_template_eq(self) -> Expr | None:
        """Returns the template equation."""
        return self._template_eq

    def get_template_vars(self) -> List[Var] | None:
        """Returns the template variables."""
        return self._template_vars


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

# ==============================================================================
# Sparse AD Jacobian
# ==============================================================================

class SparseADJacobian:
    __slots__ = [
        'verbose', 'equations', 'variables', 'parameters', 'method', 'dtype',
        'n_rows', 'n_cols', 'var_map', 'col_rows', 'J', 'colors', 'n_colors',
        'color_groups', 'color_ptr', 'color_cols', 'col_ptr', 'row_idx', 'data_idx',
        '_compiler', 'ad_kernels', 'master_jac', '_seeds'
    ]
    def __init__(
            self, equations: List[Any], variables: List[Any], parameters: List[Any],
            method: DynamicIntegrationMethod, use_cse: bool = True, dtype=np.float64, verbose: bool = False,
    ):
        self.verbose = verbose
        self.equations = equations
        self.variables = variables
        self.parameters = parameters
        self.method = method
        self.dtype = dtype

        self.n_rows = len(equations)
        self.n_cols = len(variables)

        self.var_map: Dict[int, int] = dict({id(v): i for i, v in enumerate(variables)})

        # Sparsity detection
        col_rows: List[List[int]] = list([list() for _ in range(self.n_cols)])
        for r_idx, eq in enumerate(equations):
            stack: List[Expr] = list([eq])
            visited: set = set()
            uids: set = set()

            while stack:
                node: Expr = stack.pop()
                if id(node) in visited:
                    pass
                else:
                    visited.add(id(node))

                    match node:
                        case Var():
                            uids.add(id(node))
                            if node.base_var is not None:
                                uids.add(id(node.base_var))
                            else:
                                pass

                        case BinOp(left=l, right=r):
                            stack.append(l)
                            stack.append(r)

                        case UnOp(operand=op):
                            stack.append(op)

                        case Func(arg=a):
                            stack.append(a)

                        case _:
                            pass

            for uid in uids:
                j: int = self.var_map.get(uid, -1)
                if j >= 0:
                    col_rows[j].append(r_idx)
                else:
                    pass

        self.col_rows = list([sorted(set(rows)) for rows in col_rows])

        # CSC structure
        indptr = np.zeros(self.n_cols + 1, dtype=np.int32)
        nnz: int = 0
        for j in range(self.n_cols):
            nnz += len(self.col_rows[j])
            indptr[j + 1] = nnz

        indices = np.empty(nnz, dtype=np.int32)
        data = np.zeros(nnz, dtype=self.dtype)

        k: int = 0
        for j in range(self.n_cols):
            for r_idx in self.col_rows[j]:
                indices[k] = r_idx
                k += 1

        self.J = csc_matrix((data, indices, indptr), shape=(self.n_rows, self.n_cols))

        # Coloring
        self.colors, self.n_colors = self._greedy_color_columns(self.col_rows, self.n_rows)
        groups: List[List[int]] = list([list() for _ in range(self.n_colors)])
        for j in range(self.n_cols):
            groups[self.colors[j]].append(j)
        self.color_groups = groups

        # Scatter map
        color_cols: List[int] = []
        color_ptr = np.zeros(self.n_colors + 1, dtype=np.int32)
        for c in range(self.n_colors):
            color_ptr[c] = len(color_cols)
            color_cols.extend(self.color_groups[c])
        color_ptr[self.n_colors] = len(color_cols)

        col_ptr = np.zeros(len(color_cols) + 1, dtype=np.int32)
        total_map:int = 0
        for kk, j in enumerate(color_cols):
            total_map += len(self.col_rows[j])
            col_ptr[kk + 1] = total_map

        row_idx = np.empty(total_map, dtype=np.int32)
        data_idx = np.empty(total_map, dtype=np.int32)

        pos: int = 0
        indptr_arr = self.J.indptr
        for kk, j in enumerate(color_cols):
            base = indptr_arr[j]
            for local, r_idx in enumerate(self.col_rows[j]):
                row_idx[pos] = r_idx
                data_idx[pos] = base + local
                pos += 1

        self.color_ptr, self.color_cols = color_ptr, np.asarray(color_cols, dtype=np.int32)
        self.col_ptr, self.row_idx, self.data_idx = col_ptr, row_idx, data_idx

        # Compile kernels
        self._compiler = EquationCompiler(variables=variables, parameters=parameters, method=method)
        self.ad_kernels = list()

        for c in range(self.n_colors):
            k_name = f"advec_step_color_{c}_{uuid.uuid4().hex[:4]}"
            py_ad = self._compiler.compile_ad_kernel(equations, func_name=k_name, use_cse=use_cse,
                                                     active_indices=set(self.color_groups[c]))
            self.ad_kernels.append(_safe_njit(py_ad, cache=False, fastmath=True))

        global_env: Dict[str, Any] = dict({"_scatter": _scatter_color_jvp_to_csc_data})
        for c in range(self.n_colors):
            global_env[f"kernel_{c}"] = self.ad_kernels[c]

        src: List[str] = list([
            "def master_jac(states, seeds, params, history, d_history, h, history2, data, color_ptr, col_ptr, row_idx, data_idx):"
        ])
        for c in range(self.n_colors):
            src.append(f"    jvp_{c} = kernel_{c}(states, seeds, params, history, d_history, h, history2)")
            src.append(f"    _scatter(jvp_{c}, data, color_ptr, col_ptr, row_idx, data_idx, {c})")

        exec("\n".join(src), global_env)
        self.master_jac = _safe_njit(global_env["master_jac"], fastmath=True, cache=False)
        self._seeds = np.zeros(self.n_cols, dtype=self.dtype)

    @staticmethod
    def _greedy_color_columns(col_rows: List[List[int]], n_rows: int) -> Tuple[np.ndarray, int]:
        n_cols: int = len(col_rows)
        row_cols: List[List[int]] = list([list() for _ in range(n_rows)])
        for j in range(n_cols):
            for r_idx in col_rows[j]:
                row_cols[r_idx].append(j)

        adj: List[set] = list([set() for _ in range(n_cols)])
        for cols in row_cols:
            m: int = len(cols)
            for a in range(m):
                for b in range(a + 1, m):
                    if cols[b] != cols[a]:
                        adj[cols[a]].add(cols[b])
                        adj[cols[b]].add(cols[a])
                    else:
                        pass

        degrees = np.array([len(adj[j]) for j in range(n_cols)], dtype=np.int32)
        order = list(np.argsort(-degrees))
        colors = -np.ones(n_cols, dtype=np.int32)
        max_color = -1
        used = np.zeros(n_cols, dtype=np.bool_)

        for j in order:
            used[:] = False
            for nbj in adj[j]:
                if colors[nbj] >= 0:
                    used[colors[nbj]] = True
                else:
                    pass
            c: int = 0
            while c < n_cols and used[c]:
                c += 1
            colors[j] = c
            if c > max_color:
                max_color = c
            else:
                pass
        return colors, int(max_color + 1)

    def __call__(self, states, params, history, d_history, h, history2=None) -> csc_matrix:
        self.master_jac(states, self._seeds, params, history, d_history, h, history2, self.J.data, self.color_ptr,
                        self.col_ptr, self.row_idx, self.data_idx)
        return self.J

# ==============================================================================
# StructuralVectorizedSolver
# ==============================================================================
class StructuralVectorizedSolver:
    __slots__ = [
        'problem', 't0', 't_end', 'h', 'method', 'pred_method', 'dense_threshold', 'verbose',
        'vec_jacobian', 'vec_flat_args', 'fused_residual', 'vec_kernels',
        '_state_vars', '_algebraic_vars', '_diff_vars', '_state_eqs', '_algebraic_eqs',
        'sorted_vars', '_n_state', '_n_vars', '_n_diff', 'uid2idx_vars',
        '_event_parameters', '_parameters', '_parameters_values', '_event_params_fn',
        'jit_jacobians_ad', 'vectorized_ready', '_last_sim_loop_time'
    ]

    def __init__(self,
                 problem: EmtProblemTemplate,
                 t0: float,
                 t_end: float,
                 h: float,
                 method: DynamicIntegrationMethod = DynamicIntegrationMethod.DaeTrapezoidal,
                 pred_method:DynamicIntegrationMethod = None,
                 dense_threshold: int = 100,
                 verbose: bool = False,
                 auto_vectorization: bool = True)-> None:
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
        self.problem = problem
        self.t0 = t0
        self.t_end = t_end
        self.h = h
        self.method = method
        self.pred_method = pred_method
        self.dense_threshold = dense_threshold
        self.verbose = verbose

        self.vec_jacobian = None
        self.vec_flat_args = None
        self.fused_residual = None
        self.vec_kernels = None

        self._state_vars = self.problem.get_state_vars()
        self._algebraic_vars = self.problem.get_algebraic_vars()
        self._diff_vars = self.problem.get_diff_vars()
        self._state_eqs = self.problem.get_state_eqs()
        self._algebraic_eqs = self.problem.get_algebraic_eqs()


        self.sorted_vars: List[Any] = list()
        self.sorted_vars.extend(self._state_vars)
        self.sorted_vars.extend(self._algebraic_vars)
        self._n_state = len(self._state_vars)
        self._n_vars = len(self.sorted_vars)
        self._n_diff = len(self._diff_vars)

        self.uid2idx_vars = {v.uid: i for i, v in enumerate(self.sorted_vars)}

        self._event_parameters = self.problem.get_variable_parameters()
        self._parameters = self.problem.get_constant_parameters()
        self._parameters_values = self.problem.get_parameters_values()

        self.jit_jacobians_ad: Dict[DynamicIntegrationMethod, SparseADJacobian] = dict()
        self.vectorized_ready = False

        if auto_vectorization:
            self.auto_detect_vectorization(method)

    def auto_detect_vectorization(self, method: DynamicIntegrationMethod = None):
        """
        Infers the algebraic structure of the DAE system (Clustering) and compiles
        the vectorized matrix kernels.
        """
        if method is None:
            method = self.method
        else:
            pass

        if self.verbose:
            print(f"--- [AUTO-VEC] Inferring Algebraic Structure (Clustering) ---")
        t0 = time.time()

        groups: Dict[str, EquationGroup] = dict()

        n_state: int = len(self._state_eqs)
        n_alg: int = len(self._algebraic_eqs)
        full_eq_list: List[Expr] = [Const(0.0) for _ in range(n_state + n_alg)]

        for i, rhs_eq in enumerate(self._state_eqs):
            sv = self._state_vars[i]
            d_term = Var(name=f"d_{sv.name}", base_var=sv)
            full_eq_list[i] = d_term - rhs_eq
        for j, alg_eq in enumerate(self._algebraic_eqs):
            full_eq_list[n_state + j] = alg_eq

        # PHASE 2: CLUSTERING
        for i, residual_eq in enumerate(full_eq_list):
            sig_str, all_vars_found = canonicalize_expression(residual_eq)
            eq_hash = hashlib.md5(sig_str.encode()).hexdigest()

            group: EquationGroup
            if eq_hash in groups:
                group = groups[eq_hash]
            else:
                group = EquationGroup()
                groups[eq_hash] = group

            if group.get_template_eq() is None:
                group.set_template(residual_eq, all_vars_found)
            else:
                pass

            var_indices: List[int] = list()
            for v in all_vars_found:
                target_uid: int = -1

                match v:
                    case Var(base_var=bv) if bv is not None:
                        target_uid = bv.uid
                    case Var(uid=u):
                        target_uid = u
                    case _:
                        pass

                idx: int | None = self.uid2idx_vars.get(target_uid, None)
                if idx is not None:
                    var_indices.append(idx)
                else:
                    var_indices.append(-1)

            group.add_indices(var_indices, i)

        print(f"   [AUTO-VEC] Detected {len(groups)} patterns in {len(full_eq_list)} total equations.")

        self.vec_kernels: List[Dict[str, Any]] = list()

        all_params: List[Any] = list()
        all_params.extend(self._event_parameters)
        all_params.extend(self._parameters)

        vec_compiler = MatrixVectorizedCompiler(self.sorted_vars, all_params, method=method)

        for signature, group_data in groups.items():
            k_name = f"vec_kernel_{signature[:8]}"

            py_func = vec_compiler.compile_matrix_kernel(
                group_data.get_template_eq(),
                func_name=k_name,
                template_vars=group_data.get_template_vars()
            )

            self.vec_kernels.append({
                'func': nb.njit(cache=True, fastmath=True)(py_func),
                'indices': np.array(group_data.get_idx_matrix(), dtype=np.int32),
                'target': np.array(group_data.get_row_indices(), dtype=np.int32)
            })

        # PHASE 4: DISPATCHER SETUP
        self.fused_residual = _compile_fused_residual(self.vec_kernels)

        temp_args: List[Any] = list()
        for k in self.vec_kernels:
            temp_args.extend([k['target'], k['indices']])

        self.vec_flat_args = tuple(temp_args)

        # PHASE 5: JACOBIAN SETUP
        if method not in self.jit_jacobians_ad:
            self.jit_jacobians_ad[method] = SparseADJacobian(
                full_eq_list, self.sorted_vars, all_params, method, verbose=self.verbose
            )
        else:
            pass

        self.vec_jacobian = self.jit_jacobians_ad[method]
        self.vectorized_ready = True
        print(f"   [AUTO-VEC] Setup finished in {time.time() - t0:.4f}s")

    def simulate(self,
                 x0: Union[Vec| None] = None,
                 dx0: Union[Vec| None] = None,
                 params0: Union[Vec| None] = None,
                 boundary_updater: BoundaryUpdateWrapper| None = None) -> Tuple[Vec, Mat, Mat]:

        """
        Run the vectorized DAE time-domain simulation.

        :param x0: Initial state vector.
        :param dx0: Initial derivative vector.
        :param params0: Initial event parameters.
        :param boundary_updater: Boundary condition updater.
        :return: Time vector and state trajectory matrix.
        """

        if x0 is None:
            x0 = self.problem.get_x0()
        else: pass

        if dx0 is None:
            dx0 = self.problem.get_dx0()
        else: pass

        if params0 is None:
            params0 = np.zeros(len(self._event_parameters), dtype=np.float64)
        else: pass

        return self._simulate_vectorized(self.t0, self.t_end, self.h, x0, dx0, params0, self.method,
                                         boundary_updater, self.verbose, self.dense_threshold)

    def _simulate_vectorized(self,
                             t0:float,
                             t_end:float,
                             h: float,
                             x0: Vec,
                             dx0: Vec,
                             params0: Vec,
                             method: DynamicIntegrationMethod,
                             boundary_updater: BoundaryUpdateWrapper,
                             verbose: bool,
                             dense_threshold: int)-> Tuple[Vec, Mat, Mat]:
        if not self.vectorized_ready:
            self.auto_detect_vectorization(method)

        steps: int = int(np.ceil((t_end - t0) / h))
        t: Vec = t0 + h * np.arange(steps + 1, dtype=np.float64)
        y: Mat = np.zeros((steps + 1, self._n_vars), dtype=np.float64)
        dy: Mat = np.zeros((steps + 1, self._n_diff), dtype=np.float64)
        y[0] = x0.copy()
        dy[0] = dx0.copy()

        x_prev: Vec = x0.copy()
        dx_prev: Vec = dx0.copy()
        x_prev2: Vec = x0.copy()
        x_iter: Vec = x0.copy()
        res_global: Vec = np.zeros(self._n_vars, dtype=np.float64)

        static_params = np.array([c.value for c in self._parameters_values], dtype=np.float64)
        ev_params = np.asarray(params0, dtype=np.float64)

        full_params = np.empty(len(self._event_parameters) + len(static_params), dtype=np.float64)
        full_params[len(ev_params):] = static_params

        use_dense: bool = (self._n_vars <= dense_threshold)

        if verbose: print(f"-> JIT Warmup...")
        self.fused_residual(x_prev, full_params, x_prev, dx_prev, h, self.vec_flat_args, res_global, x_prev2)
        _ = self.vec_jacobian(states=x_prev, params=full_params, history=x_prev, d_history=dx_prev, h=h,
                              history2=x_prev2)

        cached_lu_dense: Tuple[np.ndarray, np.ndarray] | None = None
        cached_lu_sparse: SuperLU | None = None

        t_start_loop = time.time()  # Timer local para debug

        if verbose: print(f"-> Starting VECTORIZED Simulation (Integration loop)...")

        for i in range(steps):
            if verbose: print(f"Simulating at step {i}")
            t_curr: float = float(t[i + 1])

            # Update params in-place
            full_params[:len(ev_params)] = self.problem.def_event_params_fn(ev_params, float(t_curr))

            if boundary_updater is not None:
                boundary_updater.update(t_curr, x_prev, full_params)
            else:
                pass

            x_iter[:] = x_prev
            last_res_norm: float = 1.0

            # PREDICTOR
            if i == 0 and method == DynamicIntegrationMethod.DaeTrapezoidal:
                n_states = self.problem.get_states_number()
                predictor = Predictor(n_states=n_states)
                predictor.predict(
                    x_iter=x_iter,
                    x_prev=x_prev,
                    dx_prev=dx_prev,
                    h=self.h,
                    pred_method=self.pred_method,
                )

            for k in range(15):
                self.fused_residual(x_iter, full_params, x_prev, dx_prev, h, self.vec_flat_args, res_global, x_prev2)
                res_norm: float = np.max(np.abs(res_global))

                if res_norm < 1e-6:
                    break
                else:
                    pass

                recompute: bool = (cached_lu_dense is None and cached_lu_sparse is None) or \
                                  (k > 0 and (res_norm / (last_res_norm + 1e-16)) > 0.5)

                if recompute:
                    cached_J: csc_matrix = self.vec_jacobian(states=x_iter, params=full_params, history=x_prev, d_history=dx_prev,
                                                 h=h, history2=x_prev2)

                    # --- Use cached_J explicitly (diagnostics / invariants) ---
                    if cached_J is None:
                        raise RuntimeError("Internal error: Jacobian is None.")

                    nnz_j: int = int(cached_J.nnz)
                    if nnz_j <= 0:
                        raise RuntimeError("Internal error: Jacobian has zero non-zeros (nnz == 0).")

                    # Optional: quick NaN/Inf guard in verbose mode (dense is expensive)
                    if verbose and use_dense:
                        j_dense: np.ndarray = cached_J.toarray()
                        if not np.all(np.isfinite(j_dense)):
                            raise RuntimeError("Jacobian contains NaN/Inf values (dense check).")
                        cached_lu_dense = lu_factor(j_dense)
                        cached_lu_sparse = None
                    else:
                        if use_dense:
                            cached_lu_dense = lu_factor(cached_J.toarray())
                            cached_lu_sparse = None
                        else:
                            cached_lu_sparse = splu(cached_J)  # cached_J already CSC
                            cached_lu_dense = None

                delta: Vec
                if use_dense:
                    if cached_lu_dense is None:
                        raise RuntimeError("Internal error: dense LU cache is None while use_dense is True.")
                    delta = lu_solve(cached_lu_dense, -res_global)
                else:
                    if cached_lu_sparse is None:
                        raise RuntimeError("Internal error: sparse LU cache is None while use_dense is False.")
                    delta = cached_lu_sparse.solve(-res_global)

                x_iter += delta
                last_res_norm = res_norm

            y[i + 1] = x_iter
            dy[i] = dx_prev

            if method == DynamicIntegrationMethod.DaeTrapezoidal:
                dx_prev[:self._n_state] = (2.0 / h) * (x_iter[:self._n_state] - x_prev[:self._n_state]) - dx_prev[
                    :self._n_state]
            elif method == DynamicIntegrationMethod.DaeBDF2:
                x_prev2[:] = x_prev
                dx_prev[:self._n_state] = (1.5 * x_iter[:self._n_state] - 2.0 * x_prev[:self._n_state] + 0.5 * x_prev2[
                    :self._n_state]) / h
            else:
                dx_prev[:self._n_state] = (x_iter[:self._n_state] - x_prev[:self._n_state]) / h

            if method != DynamicIntegrationMethod.DaeBDF2: x_prev2[:] = x_prev
            x_prev[:] = x_iter

        self._last_sim_loop_time = time.time() - t_start_loop
        if verbose: print(f"VECTORIZED INTEGRATION LOOP Finished: {self._last_sim_loop_time:.4f}s")

        return t, y, dy