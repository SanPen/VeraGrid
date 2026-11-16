# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Shared colored forward-mode AD Jacobian evaluator for EMT and RMS."""

from __future__ import annotations

from types import FunctionType
from typing import TYPE_CHECKING, Callable, Dict, List, Set, Tuple, Union
import time
import numba as nb
import numpy as np
from numba.core.registry import CPUDispatcher
from numba.core.typing.templates import Signature
from scipy.sparse import csc_matrix
from VeraGridEngine.basic_structures import Vec, Mat
from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var, BinOp, UnOp, Func, Func2
from VeraGridEngine.Utils.Symbolic.jit_compiler import EagerEquationCompiler

if TYPE_CHECKING:
    from VeraGridEngine.Utils.Symbolic.jit_compiler_rms_numba_comp import RmsEagerEquationCompiler
else:
    pass


def _safe_njit(py_func: FunctionType, fastmath: bool = True, cache: bool = True,
               signature: Signature | None = None) -> CPUDispatcher:
    """
    Safely wraps a python function with Numba's njit compiler.
    The caller must explicitly pass cache=False if the function is generated via strings.

    :param py_func: The python function to compile.
    :type py_func: FunctionType
    :param fastmath: Flag to enable fastmath operations, defaults to True.
    :type fastmath: bool
    :param cache: Flag to enable caching of the compiled function, defaults to True.
    :type cache: bool
    :param signature: Optional Numba signature.
    :type signature: Signature | None
    :return: The Numba JIT compiled function.
    :rtype: CPUDispatcher
    """
    if signature is not None:
        compiled_kernel: CPUDispatcher = nb.jit(signature, fastmath=fastmath, cache=cache)(py_func)
    else:
        compiled_kernel = nb.jit(fastmath=fastmath, cache=cache)(py_func)

    return compiled_kernel


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


def _compile_master_jacobian_kernel(ad_kernel: CPUDispatcher,
                                    n_colors: int) -> "SparseAdMasterJacobianDispatcher":
    """
    Build the eager sparse Jacobian dispatcher.

    :param ad_kernel: Generic AD kernel reused across graph colors.
    :type ad_kernel: CPUDispatcher
    :param n_colors: Number of graph colors.
    :type n_colors: int
    :return: Jacobian dispatcher.
    :rtype: SparseAdMasterJacobianDispatcher
    """
    return SparseAdMasterJacobianDispatcher(ad_kernel=ad_kernel, n_colors=n_colors)


class SparseAdMasterJacobianDispatcher:
    """
    Callable dispatcher that executes one generic AD kernel across all colors.
    """

    __slots__ = ("_ad_kernel", "_n_colors")

    def __init__(self, ad_kernel: CPUDispatcher, n_colors: int) -> None:
        """
        Store the generic AD kernel and the number of graph colors.

        :param ad_kernel: Generic AD kernel reused across graph colors.
        :param n_colors: Number of graph colors.
        :return: None.
        """
        self._ad_kernel: CPUDispatcher = ad_kernel
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
                 equations: List[Expr],
                 variables: List[Var],
                 parameters: List[Var],
                 method: DynamicIntegrationMethod,
                 use_cse: bool = True,
                 dtype: np.dtype | type[np.float64] = np.float64,
                 compiler: EagerEquationCompiler | RmsEagerEquationCompiler | None = None) -> None:

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
            stack: List[Expr] = list()
            stack.append(eq)
            visited: Set[int] = set()
            uids: Set[int] = set()

            while stack:
                n: Expr = stack.pop()
                if id(n) in visited:
                    pass
                else:
                    visited.add(id(n))

                    first_arg: Expr
                    second_arg: Expr
                    match n:
                        case Var(uid=u, base_var=bv):
                            uids.add(u)
                            # Higher derivatives depend on every base in their chain.
                            base_variable: Var | None = bv
                            while base_variable is not None:
                                uids.add(base_variable.uid)
                                base_variable = base_variable.base_var
                        case BinOp(left=l, right=r_node):
                            stack.append(l)
                            stack.append(r_node)
                        case UnOp(operand=op):
                            stack.append(op)
                        case Func2(arg1=first_arg, arg2=second_arg):
                            stack.append(first_arg)
                            stack.append(second_arg)
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
        if compiler is None:
            self._compiler = EagerEquationCompiler(variables=variables, parameters=parameters, method=method)
        else:
            self._compiler = compiler

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

