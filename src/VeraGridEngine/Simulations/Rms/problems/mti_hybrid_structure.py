from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components, maximum_bipartite_matching


@dataclass
class MTISubProblemRow:
    var_idx: int
    eq_idx: int
    explicit: int
    subset: int
    subproblem: int


def build_incidence_from_jacobian(jac: sp.spmatrix, tol: float = 0.0) -> np.ndarray:
    """
    Build a boolean incidence matrix from a sparse Jacobian.

    The matrix format follows the MTI-toolbox convention at a high level:
    rows are equations and columns are variables, with 1 where dependency exists.
    """
    if jac is None:
        return np.zeros((0, 0), dtype=int)
    j = jac.tocoo()
    inc = np.zeros(j.shape, dtype=int)
    if j.nnz == 0:
        return inc
    mask = np.abs(j.data) > tol
    inc[j.row[mask], j.col[mask]] = 1
    return inc


def build_single_subproblem_order(n_eq: int, n_vars: int) -> list[MTISubProblemRow]:
    """
    Create a deterministic fallback solving-order where all equations/variables
    belong to one subset and one subproblem.

    This mirrors the toolbox row schema, while keeping the current VeraGrid
    implementation conservative until full incidence-based decomposition is
    ported.
    """
    n = min(n_eq, n_vars)
    rows: list[MTISubProblemRow] = []
    for i in range(n):
        rows.append(MTISubProblemRow(var_idx=i + 1, eq_idx=i + 1, explicit=0, subset=1, subproblem=1))
    return rows


def build_connected_subproblem_order(incidence: np.ndarray) -> list[MTISubProblemRow]:
    """
    Build a solving-order-like structure from equation-variable connectivity.

    We build a bipartite graph [eq | var] and use connected components as
    subsets/subproblems. Rows are paired (eq_i, var_i) within each subset.
    """
    if incidence.size == 0:
        print("[MTI-ORDER] empty incidence -> empty solving order")
        return []

    n_eq, n_var = incidence.shape
    print(f"[MTI-ORDER] incidence shape=({n_eq},{n_var})")
    if n_eq != n_var:
        print("[MTI-ORDER] subproblems=0 (ordering aborted: non-square incidence)")
        raise ValueError(f"Incidence must be square for MTI ordering, got ({n_eq}, {n_var})")

    Isorted, row_sort, col_sort = _order_incidence_matrix_dmperm_like(incidence)
    print(
        f"[MTI-ORDER] sorted shape=({Isorted.shape[0]},{Isorted.shape[1]}) "
        f"row_perm={row_sort.size} col_perm={col_sort.size}"
    )
    n = Isorted.shape[0]

    # MATLAB-style subset/subproblem extraction from off-diagonal coupling.
    sub_set = np.ones(n, dtype=int)
    sub_problem = np.ones(n, dtype=int)
    for l in range(1, n):
        if not np.any(Isorted[l:, :l]):
            if not np.any(Isorted[:l, l:]):
                sub_set[l:] = sub_set[l] + 1
        if not np.any(Isorted[:l, l:]):
            sub_problem[l:] = sub_problem[l] + 1

    explicit_solvable = np.zeros(n, dtype=int)
    k = 0
    for l in range(n):
        idx = np.where(Isorted[l, l + 1:])[0]
        if idx.size > 0:
            k = max(k, int(np.max(idx)) + l + 1)
        if (l > k) and (idx.size == 0):
            explicit_solvable[l] = 1

    rows: list[MTISubProblemRow] = []
    for i in range(n):
        rows.append(
            MTISubProblemRow(
                var_idx=int(col_sort[i]) + 1,
                eq_idx=int(row_sort[i]) + 1,
                explicit=int(explicit_solvable[i]),
                subset=int(sub_set[i]),
                subproblem=int(sub_problem[i]),
            )
        )
    print(
        f"[MTI-ORDER] rows={len(rows)} subsets={int(np.max(sub_set)) if n>0 else 0} "
        f"subproblems={int(np.max(sub_problem)) if n>0 else 0} explicit={int(np.sum(explicit_solvable))}"
    )
    return rows


def _order_incidence_matrix_dmperm_like(incidence: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Structural row/column ordering for square incidence.

    MATLAB toolbox uses dmperm(I) and flips permutations. SciPy does not expose
    dmperm, so approximate the well-determined square case by:
      1. computing a full structural matching,
      2. building the directed dependency graph induced by that matching,
      3. ordering strongly connected components topologically,
      4. flipping the final permutations to match toolbox convention.

    This is much closer to dmperm block-triangular form than connected
    components or matched-column sorting alone.
    """
    n_eq, n_var = incidence.shape
    if n_eq != n_var:
        raise ValueError(f"Incidence must be square, got ({n_eq}, {n_var})")

    inc_csr = sp.csr_matrix((incidence != 0).astype(int))
    row_to_col = maximum_bipartite_matching(inc_csr, perm_type='column')
    if np.any(row_to_col < 0):
        raise ValueError("Incidence has no full structural matching")
    print("[MTI-ORDER] structural matching complete")

    col_to_row = np.empty(n_var, dtype=int)
    col_to_row[row_to_col] = np.arange(n_eq, dtype=int)

    dep_rows: list[int] = []
    dep_cols: list[int] = []
    inc_coo = inc_csr.tocoo()
    for row, col in zip(inc_coo.row, inc_coo.col):
        matched_row = int(col_to_row[int(col)])
        if int(row) == matched_row:
            continue
        # Row `row` depends on the variable matched to `matched_row`.
        dep_rows.append(int(row))
        dep_cols.append(matched_row)

    if len(dep_rows) == 0:
        dep_graph = sp.csr_matrix((n_eq, n_eq), dtype=int)
    else:
        dep_graph = sp.csr_matrix((np.ones(len(dep_rows), dtype=int), (dep_rows, dep_cols)), shape=(n_eq, n_eq))

    n_comp, labels = connected_components(dep_graph, directed=True, connection="strong", return_labels=True)
    comp_order = _topological_component_order(dep_graph, labels, n_comp)

    rows_by_comp: dict[int, list[int]] = {int(comp): [] for comp in range(n_comp)}
    for row in range(n_eq):
        rows_by_comp[int(labels[row])].append(row)

    ordered_rows: list[int] = []
    for comp in comp_order:
        comp_rows = rows_by_comp[int(comp)]
        comp_rows.sort(key=lambda r: (int(row_to_col[int(r)]), int(r)))
        ordered_rows.extend(comp_rows)

    row_sort = np.asarray(ordered_rows, dtype=int)
    col_sort = row_to_col[row_sort]
    row_sort = row_sort[::-1]
    col_sort = col_sort[::-1]

    Isorted = incidence[np.ix_(row_sort, col_sort)]
    print(
        f"[MTI-ORDER] perm head rows={row_sort[:min(8, row_sort.size)].tolist()} "
        f"cols={col_sort[:min(8, col_sort.size)].tolist()}"
    )
    comp_sizes = [len(rows_by_comp[int(comp)]) for comp in comp_order]
    print(
        f"[MTI-ORDER] dmperm-like components={n_comp} "
        f"sizes_head={comp_sizes[:min(8, len(comp_sizes))]}"
    )
    return Isorted.astype(int), row_sort.astype(int), col_sort.astype(int)


def _topological_component_order(dep_graph: sp.csr_matrix, labels: np.ndarray, n_comp: int) -> list[int]:
    """Topologically order SCC labels from a directed dependency graph."""
    if n_comp <= 1:
        return list(range(n_comp))

    dag_successors: dict[int, set[int]] = {i: set() for i in range(n_comp)}
    indegree = np.zeros(n_comp, dtype=int)
    coo = dep_graph.tocoo()
    for row, col in zip(coo.row, coo.col):
        src = int(labels[int(row)])
        dst = int(labels[int(col)])
        if src == dst or dst in dag_successors[src]:
            continue
        dag_successors[src].add(dst)
        indegree[dst] += 1

    ready = sorted([i for i in range(n_comp) if indegree[i] == 0])
    order: list[int] = []
    while ready:
        comp = ready.pop(0)
        order.append(comp)
        for succ in sorted(dag_successors[comp]):
            indegree[succ] -= 1
            if indegree[succ] == 0:
                ready.append(succ)
        ready.sort()

    if len(order) != n_comp:
        # Should not happen after SCC condensation, but keep deterministic output.
        seen = set(order)
        order.extend([i for i in range(n_comp) if i not in seen])
    return order
