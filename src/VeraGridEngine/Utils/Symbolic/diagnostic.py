# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0


from __future__ import annotations
import logging
import warnings
from typing import Any, Callable, Optional

import numpy as np

try:
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla
    import scipy.linalg as sla
    from scipy.linalg import LinAlgWarning
    from scipy.sparse.linalg import MatrixRankWarning
except ImportError:  # pragma: no cover
    sp = None
    spla = None
    sla = None
    LinAlgWarning = Warning
    MatrixRankWarning = Warning

Array1D = np.ndarray

'''
Per-solve context containing state, metrics, and diagnostics for the Newton solver.

    ---
    DEV NOTE (Architecture & C++ Porting):

    1. PYTHON IMPLEMENTATION:
       We use @dataclass(slots=True) here to optimize memory footprint (eliminating
       internal `__dict__` per instance) and strictly define the schema. This is critical
       when generating thousands of context objects during simulation steps.

    2. C++ MIGRATION GUIDE:
       If porting this structure to C++, treat it as a POD `struct`.
       - Nullables: `Optional[float]` must be converted to `std::optional<double>`.
       - Logging: You will lose the auto-generated `__repr__`. You MUST manually
         implement `friend std::ostream& operator <<` to support logging.
       - Equality: Implement `operator==` (or use C++20 `default`) to match Python's behavior.
       - Initialization: Use C++20 designated initializers (`.field = val`) to mimic
         Python's keyword arguments.
    ---
'''

class NewtonDiagnosticsConfig:
    """
    Configuration for Newton linear-solve diagnostics.

    Attributes:
        step_norm_explode: Threshold on ||dx||_2 to flag an exploding Newton step.
        dense_cond_warn: Condition number threshold to warn about ill-conditioning (dense only).
        compute_dense_cond: If True, compute np.linalg.cond(A) for dense matrices.
        dense_cond_max_n: Avoid cond(A) if matrix dimension > this value (O(n^3) cost).
        enable_fallback: If True, attempt a least-squares fallback when the primary solve fails.
        enable_index1_check: If True, validate the algebraic Jacobian block on refresh.
        index1_max_block_n: Skip explicit index-1 checks for algebraic blocks larger than this size.
        index1_warn_pivot_ratio: Warn threshold for the minimum pivot ratio of the algebraic block.
        index1_fail_pivot_ratio: Failure threshold for the minimum pivot ratio of the algebraic block.
        enable_backtracking: If True, apply backtracking when a full Newton step fails to reduce the residual.
        backtracking_beta: Shrink factor used during backtracking.
        backtracking_min_alpha: Minimum accepted Newton step scaling.
        backtracking_max_iter: Maximum number of backtracking reductions.
        log_level: Logging level for warnings.
    """
    __slots__ = (
        "step_norm_explode",
        "dense_cond_warn",
        "compute_dense_cond",
        "dense_cond_max_n",
        "enable_fallback",
        "enable_index1_check",
        "index1_max_block_n",
        "index1_warn_pivot_ratio",
        "index1_fail_pivot_ratio",
        "enable_backtracking",
        "backtracking_beta",
        "backtracking_min_alpha",
        "backtracking_max_iter",
        "max_newton_step_inf",
        "log_level",
    )

    def __init__(
        self,
        step_norm_explode: float = 1e6,
        dense_cond_warn: float = 1e12,
        compute_dense_cond: bool = True,
        dense_cond_max_n: int = 600,
        enable_fallback: bool = True,
        enable_index1_check: bool = False,
        index1_max_block_n: int = 128,
        index1_warn_pivot_ratio: float = 1e-10,
        index1_fail_pivot_ratio: float = 1e-14,
        enable_backtracking: bool = False,
        backtracking_beta: float = 0.5,
        backtracking_min_alpha: float = 1e-4,
        backtracking_max_iter: int = 6,
        max_newton_step_inf: Optional[float] = None,
        log_level: int = logging.WARNING,
    ) -> None:
        self.step_norm_explode = step_norm_explode
        self.dense_cond_warn = dense_cond_warn
        self.compute_dense_cond = compute_dense_cond
        self.dense_cond_max_n = dense_cond_max_n
        self.enable_fallback = enable_fallback
        self.enable_index1_check = enable_index1_check
        self.index1_max_block_n = index1_max_block_n
        self.index1_warn_pivot_ratio = index1_warn_pivot_ratio
        self.index1_fail_pivot_ratio = index1_fail_pivot_ratio
        self.enable_backtracking = enable_backtracking
        self.backtracking_beta = backtracking_beta
        self.backtracking_min_alpha = backtracking_min_alpha
        self.backtracking_max_iter = backtracking_max_iter
        self.max_newton_step_inf = max_newton_step_inf
        self.log_level = log_level


class NewtonSolveContext:
    """
    Per-solve context, passed by the caller.

    The decorator updates diagnostic fields (used_fallback, cond_est, step_norm, failure_msg).

    Attributes:
        t: Current simulation time.
        step_idx: Time-step index.
        newton_iter: Newton iteration index within the time-step.
        phase: Text label (e.g. "jit", "implicit", "pseudo", "init").
        method: Integration method label, if available.
        solver: Text label (e.g. "dense", "sparse").
        used_fallback: Set True if fallback was used.
        cond_est: Estimated condition number (dense only, optional).
        step_norm2: ||dx||_2
        step_norm_inf: ||dx||_inf
        failure_msg: If the primary solver failed, store a short error description.
    """
    __slots__ = (
        "t",
        "step_idx",
        "newton_iter",
        "phase",
        "method",
        "solver",
        "used_fallback",
        "cond_est",
        "step_norm2",
        "step_norm_inf",
        "failure_msg",
        "res_norm_inf",
        "index1_pivot_ratio",
    )

    def __init__(
        self,
        t: float,
        step_idx: int,
        newton_iter: int,
        phase: str,
        method: str = "",
        solver: str = "",
        used_fallback: bool = False,
        cond_est: Optional[float] = None,
        step_norm2: Optional[float] = None,
        step_norm_inf: Optional[float] = None,
        failure_msg: Optional[str] = None,
        res_norm_inf: Optional[float] = None,
        index1_pivot_ratio: Optional[float] = None,
    ) -> None:
        self.t = t
        self.step_idx = step_idx
        self.newton_iter = newton_iter
        self.phase = phase
        self.method = method
        self.solver = solver
        self.used_fallback = used_fallback
        self.cond_est = cond_est
        self.step_norm2 = step_norm2
        self.step_norm_inf = step_norm_inf
        self.failure_msg = failure_msg
        self.res_norm_inf = res_norm_inf
        self.index1_pivot_ratio = index1_pivot_ratio

def _emit(logger: Optional[logging.Logger], level: int, msg: str) -> None:
    """
    Emit a message either via logger (if configured) or via print as a fallback.
    """
    if logger is not None and (logger.handlers or logging.getLogger().handlers):
        logger.log(level, msg)
    else:
        # Console fallback if no logging handlers exist.
        print(msg)

def _format_ctx(ctx: NewtonSolveContext) -> str:
    return (
        f"t={ctx.t:.6g}, step={ctx.step_idx}, it={ctx.newton_iter}, "
        f"phase={ctx.phase}, method={ctx.method}, solver={ctx.solver}"
    )

def with_newton_diagnostics(
    primary_solve: Callable[[Any, Array1D], Array1D],
    *,
    fallback_solve: Optional[Callable[[Any, Array1D], Array1D]] = None,
    collector: Optional["NewtonTraceCollector"] = None,
    config: Optional[NewtonDiagnosticsConfig] = None,
    logger: Optional[logging.Logger] = None,
    solver_name: str = "",
    matrix_getter: Optional[Callable[[Any], Any]] = None,
) -> Callable[[Any, Array1D, NewtonSolveContext], Array1D]:
    """
    Decorate a linear solver with Jacobian conditioning diagnostics and fallback LS solve.

    Args:
        primary_solve: Function implementing the primary solve (e.g. np.linalg.solve, spla.spsolve).
        fallback_solve: Least-squares fallback (e.g. np.linalg.lstsq(...)[0], spla.lsqr(...)[0]).
        collector: Optional Newton trace collector receiving per-iteration records.
        config: Diagnostics configuration.
        logger: Optional logger (uses print fallback if not configured).
        solver_name: Human-readable solver label.
        matrix_getter: Optional callback to extract the diagnostic matrix from a bundled solver object.

    Returns:
        A callable solve(A, b, ctx) -> x, which updates ctx with diagnostics info.
    """
    cfg = config or NewtonDiagnosticsConfig()
    log = logger or logging.getLogger(__name__)

    def wrapped(A: Any, b: Array1D, ctx: NewtonSolveContext) -> Array1D:
        ctx.solver = solver_name or ctx.solver
        diag_matrix: Any = matrix_getter(A) if matrix_getter is not None else A

        # ---- Optional dense conditioning estimate ----
        # Only do this for dense ndarray matrices to avoid sparse->dense blowups.
        if cfg.compute_dense_cond and isinstance(diag_matrix, np.ndarray):
            n = diag_matrix.shape[0]
            if n <= cfg.dense_cond_max_n:
                try:
                    cond = float(np.linalg.cond(diag_matrix))
                    ctx.cond_est = cond
                    if cond > cfg.dense_cond_warn:
                        _emit(
                            log,
                            cfg.log_level,
                            f"[NewtonDiag] Ill-conditioned dense Jacobian (cond={cond:.3e}). {_format_ctx(ctx)}",
                        )
                except Exception as e:
                    _emit(
                        log,
                        cfg.log_level,
                        f"[NewtonDiag] cond(A) failed ({type(e).__name__}: {e}). {_format_ctx(ctx)}",
                    )

        # ---- Primary solve (with rank-warning promotion for sparse) ----
        ctx.used_fallback = False
        ctx.failure_msg = None

        try:
            if sp is not None and spla is not None and sp.issparse(diag_matrix):
                # SciPy may emit MatrixRankWarning instead of raising; promote it to exception.
                with warnings.catch_warnings():
                    warnings.simplefilter("error", MatrixRankWarning)
                    x = primary_solve(A, b)
            else:
                x = primary_solve(A, b)

            if not np.all(np.isfinite(x)):
                raise FloatingPointError("Primary solve returned NaN/Inf.")
        except Exception as e:
            ctx.failure_msg = f"{type(e).__name__}: {e}"
            _emit(
                log,
                cfg.log_level,
                f"[NewtonDiag] Linear solve failed -> {ctx.failure_msg}. {_format_ctx(ctx)}",
            )

            if not cfg.enable_fallback:
                raise

            fb = fallback_solve
            if fb is None:
                raise  # No fallback provided.

            ctx.used_fallback = True
            _emit(
                log,
                cfg.log_level,
                f"[NewtonDiag] Attempting least-squares fallback. {_format_ctx(ctx)}",
            )
            x = fb(A, b)

            if not np.all(np.isfinite(x)):
                raise FloatingPointError("Fallback solve returned NaN/Inf.")

        # ---- Step norm monitoring ----
        n2 = float(np.linalg.norm(x))
        ninf = float(np.linalg.norm(x, np.inf))
        ctx.step_norm2 = n2
        ctx.step_norm_inf = ninf

        if n2 > cfg.step_norm_explode:
            _emit(
                log,
                cfg.log_level,
                f"[NewtonDiag] Exploding Newton step (||dx||2={n2:.3e}, ||dx||inf={ninf:.3e}). {_format_ctx(ctx)}",
            )

        # ---- Trace collection (optional)----
        if collector is not None:
            collector.record(
                ctx=ctx,
                res_norm=ctx.res_norm_inf,
                dx=x,
                cond=ctx.cond_est,
                fallback=ctx.used_fallback,
            )


        return x

    return wrapped


def maybe_check_index1(
    jacobian: Any,
    n_state: int,
    *,
    ctx: Optional[NewtonSolveContext] = None,
    config: Optional[NewtonDiagnosticsConfig] = None,
    logger: Optional[logging.Logger] = None,
) -> Optional[float]:
    """
    Optionally validate the algebraic Jacobian block associated with an index-1 DAE.

    The check is intentionally conservative and size-limited so it does not penalize
    normal runtime performance. It is only active when ``config.enable_index1_check``
    is set to ``True``.

    :param jacobian: Dense or sparse Jacobian matrix of the monolithic residual.
    :param n_state: Number of differential states; rows/columns after this offset belong to ``g_y``.
    :param ctx: Optional Newton context for diagnostics bookkeeping.
    :param config: Newton diagnostics configuration.
    :param logger: Optional logger.
    :return: Estimated pivot-ratio indicator or ``None`` when the check is skipped.
    """
    cfg = config or NewtonDiagnosticsConfig()
    log = logger or logging.getLogger(__name__)

    if not cfg.enable_index1_check:
        return None

    n_total: int = int(jacobian.shape[0])
    n_alg: int = n_total - int(n_state)

    if n_alg <= 0 or n_alg > cfg.index1_max_block_n:
        return None

    if isinstance(jacobian, np.ndarray):
        gy = jacobian[n_state:, n_state:]

        if gy.size == 0:
            return None

        if sla is None:
            return None

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", LinAlgWarning)
                lu_data, _ = sla.lu_factor(gy)
            diag_u = np.abs(np.diag(lu_data))
            scale = max(float(np.max(np.abs(gy))), 1.0)
        except Exception as e:
            msg = f"[NewtonDiag] index-1 dense check failed ({type(e).__name__}: {e}). {_format_ctx(ctx) if ctx else ''}"
            _emit(log, cfg.log_level, msg)
            raise RuntimeError(msg) from e

    elif sp is not None and spla is not None and sp.issparse(jacobian):
        gy = jacobian[n_state:, n_state:].tocsc()

        if gy.nnz == 0:
            msg = f"[NewtonDiag] Empty algebraic Jacobian block detected. {_format_ctx(ctx) if ctx else ''}"
            _emit(log, cfg.log_level, msg)
            raise RuntimeError(msg)

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", MatrixRankWarning)
                lu_obj = spla.splu(gy)
            diag_u = np.abs(lu_obj.U.diagonal())
            scale = max(float(np.max(np.abs(gy.data))), 1.0)
        except Exception as e:
            msg = f"[NewtonDiag] index-1 sparse check failed ({type(e).__name__}: {e}). {_format_ctx(ctx) if ctx else ''}"
            _emit(log, cfg.log_level, msg)
            raise RuntimeError(msg) from e

    else:
        return None

    if diag_u.size == 0:
        return None

    pivot_ratio: float = float(np.min(diag_u) / scale)

    if ctx is not None:
        ctx.index1_pivot_ratio = pivot_ratio

    if pivot_ratio < cfg.index1_fail_pivot_ratio:
        msg = (
            f"[NewtonDiag] Likely index-1 violation or near-singular g_y block "
            f"(pivot_ratio={pivot_ratio:.3e}). {_format_ctx(ctx) if ctx else ''}"
        )
        _emit(log, cfg.log_level, msg)
        raise RuntimeError(msg)

    if pivot_ratio < cfg.index1_warn_pivot_ratio:
        _emit(
            log,
            cfg.log_level,
            f"[NewtonDiag] Weak algebraic Jacobian block (pivot_ratio={pivot_ratio:.3e}). {_format_ctx(ctx) if ctx else ''}",
        )

    return pivot_ratio


def maybe_apply_backtracking(
    x_iter: Array1D,
    delta: Array1D,
    res_norm: float,
    trial_x: Array1D,
    trial_res: Array1D,
    *,
    evaluate_residual: Callable[[Array1D, Array1D], float],
    config: Optional[NewtonDiagnosticsConfig] = None,
) -> None:
    """
    Optionally apply backtracking to a Newton step.

    The full Newton step is kept as the default behavior. When backtracking is enabled,
    the routine tries geometrically reduced step sizes and accepts the first one that
    decreases the residual norm. If none succeeds, the original full step is applied.

    :param x_iter: Current Newton iterate. Updated in place.
    :param delta: Full Newton correction.
    :param res_norm: Residual norm at the current iterate.
    :param trial_x: Reusable state buffer for trial iterates.
    :param trial_res: Reusable residual buffer for trial iterates.
    :param evaluate_residual: Callback ``evaluate_residual(trial_x, trial_res) -> res_norm``.
    :param config: Newton diagnostics configuration.
    :return: None
    """
    cfg = config or NewtonDiagnosticsConfig()

    if not cfg.enable_backtracking:
        x_iter += delta
        return

    alpha: float = 1.0
    bt_iter: int = 0

    while bt_iter <= cfg.backtracking_max_iter:
        trial_x[:] = x_iter
        trial_x += alpha * delta

        trial_res_norm: float = float(evaluate_residual(trial_x, trial_res))

        if np.isfinite(trial_res_norm) and trial_res_norm < res_norm:
            x_iter[:] = trial_x
            return

        alpha *= cfg.backtracking_beta

        if alpha < cfg.backtracking_min_alpha:
            break

        bt_iter += 1

    x_iter += delta

# --------------------------
# Convenience fallback solvers
# --------------------------
def dense_lstsq_fallback(A: Any, b: Array1D) -> Array1D:
    """
    Dense least-squares fallback using np.linalg.lstsq.

    Args:
        A: Dense matrix.
        b: RHS vector.

    Returns:
        x: Least-squares solution.
    """
    x, *_ = np.linalg.lstsq(A, b, rcond=None)
    return x

def sparse_lsqr_fallback(A: Any, b: Array1D) -> Array1D:
    """
    Sparse least-squares fallback using scipy.sparse.linalg.lsqr.

    Args:
        A: Sparse matrix.
        b: RHS vector.

    Returns:
        x: LSQR solution.
    """
    if spla is None:
        raise RuntimeError("SciPy is required for sparse LSQR fallback.")
    x = spla.lsqr(A, b)[0]
    return x

class NewtonTraceCollector:
    """
    Collects numerical diagnostics during a simulation run.
    Designed for post-analysis and research purposes.
    """
    __slots__ = ("records", "residual_records")

    def __init__(self) -> None:
        """
        Initialize an empty Newton trace collector.

        :return: None
        """
        self.records: list[dict[str, Any]] = list()
        self.residual_records: list[dict[str, Any]] = list()

    def record(
        self,
        *,
        ctx: NewtonSolveContext,
        res_norm: Optional[float] = None,
        dx: Optional[Array1D] = None,
        cond: Optional[float] = None,
        fallback: bool = False,
    ) -> None:
        """
        Append one Newton diagnostics record.

        :param ctx: Per-iteration Newton context.
        :param res_norm: Residual infinity norm.
        :param dx: Newton correction vector.
        :param cond: Optional dense Jacobian condition estimate.
        :param fallback: Whether the least-squares fallback was used.
        :return: None
        """
        self.records.append({
            "t": ctx.t,
            "step": ctx.step_idx,
            "newton_iter": ctx.newton_iter,
            "phase": ctx.phase,
            "method": ctx.method,
            "solver": ctx.solver,
            "res_norm_inf": res_norm,
            "dx_norm_2": np.linalg.norm(dx) if dx is not None else None,
            "dx_norm_inf": np.linalg.norm(dx, np.inf) if dx is not None else None,
            "cond_J": cond,
            "index1_pivot_ratio": ctx.index1_pivot_ratio,
            "used_fallback": fallback,
        })

    def to_dataframe(self):
        """
        Convert the collected records into a pandas DataFrame.

        :return: DataFrame with Newton diagnostics records.
        """
        import pandas as pd
        return pd.DataFrame(self.records)

    def record_residual_vector(
        self,
        *,
        ctx: NewtonSolveContext,
        residual: Array1D,
        top_k: int = 5,
        debug_info: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        """
        Record one residual snapshot with top offending equation indices.

        :param ctx: Per-iteration Newton context.
        :param residual: Full nonlinear residual vector.
        :param top_k: Number of largest-magnitude residual entries to keep.
        :param debug_info: Optional residual metadata aligned with residual indices.
        :return: None.
        """
        if residual.size == 0:
            return
        k = int(max(1, min(int(top_k), int(residual.size))))
        idx = np.argpartition(np.abs(residual), -k)[-k:]
        idx = idx[np.argsort(np.abs(residual[idx]), kind="stable")[::-1]]
        top_rows: list[dict[str, Any]] = list()
        for ii in idx:
            row: dict[str, Any] = {
                "eq_idx": int(ii),
                "res": float(residual[ii]),
                "abs_res": float(abs(residual[ii])),
            }
            if debug_info is not None and 0 <= int(ii) < len(debug_info):
                info = debug_info[int(ii)]
                row["kind"] = str(info.get("kind", ""))
                row["label"] = str(info.get("label", ""))
                row["var_name"] = str(info.get("var_name", ""))
            top_rows.append(row)

        self.residual_records.append({
            "t": float(ctx.t),
            "step": int(ctx.step_idx),
            "newton_iter": int(ctx.newton_iter),
            "res_norm_inf": float(np.max(np.abs(residual))),
            "top": top_rows,
        })
