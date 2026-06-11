from __future__ import annotations

from dataclasses import dataclass
import os
import shutil
import subprocess
import tempfile

import numpy as np
from scipy.io import loadmat, savemat
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

    backend = os.getenv("RMS_MTI_DMPERM_BACKEND", "python").strip().lower()
    if backend in ("octave", "matlab", "auto"):
        try:
            return _order_incidence_matrix_external_dmperm(incidence, backend)
        except Exception as ex:
            if backend in ("octave", "matlab"):
                raise
            print(f"[MTI-ORDER] external dmperm unavailable, using Python fallback: {ex}")

    inc_csr = sp.csr_matrix((incidence != 0).astype(int))
    row_to_col, n_comp, labels, dep_graph = _best_structural_matching(inc_csr)
    print("[MTI-ORDER] structural matching complete")

    col_to_row = np.empty(n_var, dtype=int)
    col_to_row[row_to_col] = np.arange(n_eq, dtype=int)

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


def _order_incidence_matrix_external_dmperm(
    incidence: np.ndarray,
    backend: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Use Octave/MATLAB dmperm exactly, then apply toolbox flip(p), flip(q)."""
    executable = _dmperm_executable(backend)
    if executable is None:
        raise RuntimeError(f"No executable found for dmperm backend '{backend}'")

    with tempfile.TemporaryDirectory(prefix="veragrid_mti_dmperm_") as tmp:
        in_file = os.path.join(tmp, "dmperm_in.mat")
        out_file = os.path.join(tmp, "dmperm_out.mat")
        savemat(in_file, {"I": sp.csc_matrix((incidence != 0).astype(float))})

        code = (
            f"load('{in_file}'); "
            "[p,q,r,s,cc,rr] = dmperm(sparse(I)); "
            "p = double(p(:)); q = double(q(:)); "
            f"save('-mat', '{out_file}', 'p', 'q');"
        )
        cmd = [executable, "--quiet", "--eval", code] if os.path.basename(executable).startswith("octave") else [executable, "-batch", code]
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            msg = (proc.stderr or proc.stdout or "dmperm command failed").strip()
            raise RuntimeError(msg)

        data = loadmat(out_file)
        p = np.asarray(data["p"], dtype=int).reshape(-1) - 1
        q = np.asarray(data["q"], dtype=int).reshape(-1) - 1

    if p.size != incidence.shape[0] or q.size != incidence.shape[1]:
        raise RuntimeError(f"dmperm returned invalid permutation sizes p={p.size} q={q.size}")

    row_sort = p[::-1].astype(int)
    col_sort = q[::-1].astype(int)
    Isorted = incidence[np.ix_(row_sort, col_sort)]
    print(
        f"[MTI-ORDER] external dmperm backend={os.path.basename(executable)} "
        f"perm head rows={row_sort[:min(8, row_sort.size)].tolist()} "
        f"cols={col_sort[:min(8, col_sort.size)].tolist()}"
    )
    return Isorted.astype(int), row_sort, col_sort


def _dmperm_executable(backend: str) -> str | None:
    if backend == "matlab":
        return shutil.which("matlab")
    if backend == "octave":
        return shutil.which("octave")
    return shutil.which("octave") or shutil.which("matlab")


def _best_structural_matching(inc_csr: sp.csr_matrix) -> tuple[np.ndarray, int, np.ndarray, sp.csr_matrix]:
    """
    Pick a perfect structural matching that exposes fine BTF blocks.

    MATLAB's dmperm is not just any maximum matching. SciPy's matching can be
    valid but poor for block triangular form, so try deterministic row/column
    degree permutations and keep the matching with the most SCCs and smallest
    largest SCC in the induced dependency graph.
    """
    n_eq, n_var = inc_csr.shape
    row_degree = np.asarray(inc_csr.sum(axis=1)).reshape(-1)
    col_degree = np.asarray(inc_csr.sum(axis=0)).reshape(-1)

    row_orders = _unique_orders([
        np.arange(n_eq, dtype=int),
        np.argsort(row_degree, kind="stable"),
        np.argsort(-row_degree, kind="stable"),
    ])
    col_orders = _unique_orders([
        np.arange(n_var, dtype=int),
        np.argsort(col_degree, kind="stable"),
        np.argsort(-col_degree, kind="stable"),
    ])

    best: tuple[tuple[int, int, int, int], np.ndarray, int, np.ndarray, sp.csr_matrix] | None = None
    for row_order in row_orders:
        for col_order in col_orders:
            permuted = inc_csr[row_order, :][:, col_order]
            match_perm = maximum_bipartite_matching(permuted, perm_type="column")
            if match_perm.size != n_eq:
                continue

            unmatched = int(np.sum(match_perm < 0))
            match_perm = _complete_matching(match_perm, n_var)
            row_to_col = np.empty(n_eq, dtype=int)
            row_to_col[row_order] = col_order[np.asarray(match_perm, dtype=int)]
            n_comp, labels, dep_graph = _matching_dependency_components(inc_csr, row_to_col)
            comp_sizes = np.bincount(labels, minlength=n_comp) if n_comp > 0 else np.zeros(0, dtype=int)
            largest = int(np.max(comp_sizes)) if comp_sizes.size > 0 else 0
            singleton_count = int(np.sum(comp_sizes == 1)) if comp_sizes.size > 0 else 0
            score = (-unmatched, int(n_comp), -largest, singleton_count)
            if best is None or score > best[0]:
                best = (score, row_to_col, n_comp, labels, dep_graph)

    if best is None:
        raise ValueError("Incidence has no structural matching")

    score, row_to_col, n_comp, labels, dep_graph = best
    print(
        f"[MTI-ORDER] matching score unmatched={-score[0]} components={score[1]} "
        f"largest={-score[2]} singletons={score[3]}"
    )
    return row_to_col, n_comp, labels, dep_graph


def _complete_matching(match_perm: np.ndarray, n_var: int) -> np.ndarray:
    """Complete a possibly deficient row->column matching deterministically."""
    out = np.asarray(match_perm, dtype=int).copy()
    used_cols = {int(c) for c in out.tolist() if int(c) >= 0}
    free_cols = [c for c in range(n_var) if c not in used_cols]
    free_iter = iter(free_cols)
    for row in np.where(out < 0)[0]:
        out[int(row)] = int(next(free_iter))
    return out


def _matching_dependency_components(
    inc_csr: sp.csr_matrix,
    row_to_col: np.ndarray,
) -> tuple[int, np.ndarray, sp.csr_matrix]:
    n_eq, n_var = inc_csr.shape
    col_to_row = np.empty(n_var, dtype=int)
    col_to_row[np.asarray(row_to_col, dtype=int)] = np.arange(n_eq, dtype=int)

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
    return int(n_comp), np.asarray(labels, dtype=int), dep_graph


def _unique_orders(orders: list[np.ndarray]) -> list[np.ndarray]:
    unique: list[np.ndarray] = []
    seen: set[tuple[int, ...]] = set()
    for order in orders:
        arr = np.asarray(order, dtype=int)
        key = tuple(int(i) for i in arr.tolist())
        if key in seen:
            continue
        seen.add(key)
        unique.append(arr)
    return unique


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
