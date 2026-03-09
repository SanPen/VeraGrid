# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0


from __future__ import annotations
import logging
import warnings
from dataclasses import dataclass
from typing import Any, Callable, Optional

import numpy as np

try:
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla
    from scipy.sparse.linalg import MatrixRankWarning
except Exception:  # pragma: no cover
    sp = None
    spla = None
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

@dataclass(slots=True)
class NewtonDiagnosticsConfig:
    """
    Configuration for Newton linear-solve diagnostics.

    Attributes:
        step_norm_explode: Threshold on ||dx||_2 to flag an exploding Newton step.
        dense_cond_warn: Condition number threshold to warn about ill-conditioning (dense only).
        compute_dense_cond: If True, compute np.linalg.cond(A) for dense matrices.
        dense_cond_max_n: Avoid cond(A) if matrix dimension > this value (O(n^3) cost).
        enable_fallback: If True, attempt a least-squares fallback when the primary solve fails.
        log_level: Logging level for warnings.
    """
    step_norm_explode: float = 1e6
    dense_cond_warn: float = 1e12
    compute_dense_cond: bool = True
    dense_cond_max_n: int = 600
    enable_fallback: bool = True
    log_level: int = logging.WARNING

@dataclass(slots=True)
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
    t: float
    step_idx: int
    newton_iter: int
    phase: str
    method: str = ""
    solver: str = ""
    used_fallback: bool = False
    cond_est: Optional[float] = None
    step_norm2: Optional[float] = None
    step_norm_inf: Optional[float] = None
    failure_msg: Optional[str] = None
    res_norm_inf: Optional[float] = None

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
) -> Callable[[Any, Array1D, NewtonSolveContext], Array1D]:
    """
    Decorate a linear solver with Jacobian conditioning diagnostics and fallback LS solve.

    Args:
        primary_solve: Function implementing the primary solve (e.g. np.linalg.solve, spla.spsolve).
        fallback_solve: Least-squares fallback (e.g. np.linalg.lstsq(...)[0], spla.lsqr(...)[0]).
        config: Diagnostics configuration.
        logger: Optional logger (uses print fallback if not configured).
        solver_name: Human-readable solver label.

    Returns:
        A callable solve(A, b, ctx) -> x, which updates ctx with diagnostics info.
    """
    cfg = config or NewtonDiagnosticsConfig()
    log = logger or logging.getLogger(__name__)

    def wrapped(A: Any, b: Array1D, ctx: NewtonSolveContext) -> Array1D:
        ctx.solver = solver_name or ctx.solver

        # ---- Optional dense conditioning estimate ----
        # Only do this for dense ndarray matrices to avoid sparse->dense blowups.
        if cfg.compute_dense_cond and isinstance(A, np.ndarray):
            n = A.shape[0]
            if n <= cfg.dense_cond_max_n:
                try:
                    cond = float(np.linalg.cond(A))
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
            if sp is not None and spla is not None and sp.issparse(A):
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

    def __init__(self):
        self.records = []

    def record(self, *, ctx, res_norm=None, dx=None, cond=None, fallback=False):
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
            "used_fallback": fallback,
        })

    def to_dataframe(self):
        import pandas as pd
        return pd.DataFrame(self.records)
