# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can see it at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import logging
from typing import Any

import numpy as np
import scipy.sparse as sp

from VeraGridEngine.Utils.Symbolic.diagnostic import (
    with_newton_diagnostics,
    NewtonDiagnosticsConfig,
    NewtonSolveContext,
    dense_lstsq_fallback,
    sparse_lsqr_fallback,
    NewtonTraceCollector
)


def _create_diagnostics_collector() -> NewtonTraceCollector:
    """
    Create a new Newton trace collector for diagnostics.

    :returns: A fresh NewtonTraceCollector instance.
    """
    return NewtonTraceCollector()


logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s:%(name)s:%(message)s",
)

logger = logging.getLogger("NewtonDiagnosticsDemo")


def make_ctx(iteration: int) -> NewtonSolveContext:
    """
    Create a Newton solve context for testing.

    :param iteration: Newton iteration number.
    :returns: NewtonSolveContext configured for testing.
    """
    return NewtonSolveContext(
        t=0.0,
        step_idx=0,
        newton_iter=iteration,
        phase="demo",
        method="diagnostics_test",
    )


def test_dense_singular_jacobian(caplog) -> None:
    """
    Test Newton diagnostics with singular dense Jacobian.

    Verifies that the fallback mechanism handles singular matrices
    gracefully and produces a finite result. Checks that:
    - A warning is logged about singular matrix or fallback
    - The collector records that fallback was used
    """
    collector = _create_diagnostics_collector()
    A: np.ndarray = np.array(list([
        list([1.0, 2.0]),
        list([0.0, 0.0]),
    ]), dtype=np.float64)
    b: np.ndarray = np.array(list([1.0, 0.0]), dtype=np.float64)

    cfg: NewtonDiagnosticsConfig = NewtonDiagnosticsConfig(
        compute_dense_cond=True,
        enable_fallback=True,
    )

    dense_solve: Any = with_newton_diagnostics(
        np.linalg.solve,
        fallback_solve=dense_lstsq_fallback,
        config=cfg,
        solver_name="dense",
        collector=collector
    )

    with caplog.at_level(logging.WARNING):
        dx: np.ndarray = dense_solve(A, b, make_ctx(0))

    assert len(caplog.records) > 0
    log_messages = [rec.message for rec in caplog.records]
    assert any("fallback" in msg.lower() or "singular" in msg.lower() for msg in log_messages)

    assert len(dx) == 2
    assert np.all(np.isfinite(dx))
    assert len(collector.records) > 0
    record = collector.records[0]
    assert record["used_fallback"] == True


def test_dense_ill_conditioned_jacobian() -> None:
    """
    Test Newton diagnostics with ill-conditioned dense Jacobian.

    Verifies that the diagnostics detect ill-conditioning and
    produce a finite result. Checks that:
    - The condition number is computed and stored in records
    - The condition number exceeds the warning threshold
    """
    collector = _create_diagnostics_collector()
    eps: float = 1e-14
    A: np.ndarray = np.array(list([
        list([1.0, 1.0]),
        list([1.0, 1.0 + eps]),
    ]), dtype=np.float64)
    b: np.ndarray = np.array(list([2.0, 2.0]), dtype=np.float64)

    cfg: NewtonDiagnosticsConfig = NewtonDiagnosticsConfig(
        compute_dense_cond=True,
        dense_cond_warn=1e10,
        enable_fallback=False,
    )

    dense_solve: Any = with_newton_diagnostics(
        np.linalg.solve,
        config=cfg,
        solver_name="dense",
        collector=collector
    )

    dx: np.ndarray = dense_solve(A, b, make_ctx(1))

    assert len(dx) == 2
    assert np.all(np.isfinite(dx))
    assert len(collector.records) > 0
    record = collector.records[0]
    assert "cond_J" in record
    assert record["cond_J"] > 1e10


def test_exploding_newton_step() -> None:
    """
    Test Newton diagnostics with exploding step norm.

    Verifies that step norm explosion is detected and handled.
    Checks that the diagnostics capture the step norm explosion warning.
    """
    collector = _create_diagnostics_collector()
    A: np.ndarray = np.eye(2, dtype=np.float64)
    b: np.ndarray = np.array(list([1e8, -1e8]), dtype=np.float64)

    cfg: NewtonDiagnosticsConfig = NewtonDiagnosticsConfig(
        step_norm_explode=1e6,
        enable_fallback=False,
    )

    dense_solve: Any = with_newton_diagnostics(
        np.linalg.solve,
        config=cfg,
        solver_name="dense",
        collector=collector
    )

    dx: np.ndarray = dense_solve(A, b, make_ctx(2))

    assert len(dx) == 2
    assert np.all(np.isfinite(dx))
    assert len(collector.records) > 0
    record = collector.records[0]
    assert "dx_norm_inf" in record
    assert record["dx_norm_inf"] > 1e6


def test_sparse_singular_jacobian(caplog) -> None:
    """
    Test Newton diagnostics with singular sparse Jacobian.

    Verifies that sparse matrix solving with fallback works correctly.
    Checks that:
    - The fallback mechanism is triggered for sparse singular matrices
    - The result is finite and correct
    """
    collector = _create_diagnostics_collector()
    A = sp.csr_matrix(list([
        list([1.0, 2.0]),
        list([0.0, 0.0]),
    ]), dtype=np.float64)
    b: np.ndarray = np.array(list([1.0, 0.0]), dtype=np.float64)

    cfg: NewtonDiagnosticsConfig = NewtonDiagnosticsConfig(
        compute_dense_cond=False,
        enable_fallback=True,
    )

    sparse_solve: Any = with_newton_diagnostics(
        sp.linalg.spsolve,
        fallback_solve=sparse_lsqr_fallback,
        config=cfg,
        solver_name="sparse",
        collector=collector
    )

    with caplog.at_level(logging.WARNING):
        dx: np.ndarray = sparse_solve(A, b, make_ctx(3))

    assert len(caplog.records) > 0
    log_messages = [rec.message for rec in caplog.records]
    assert any("fallback" in msg.lower() or "singular" in msg.lower() for msg in log_messages)

    assert len(dx) == 2
    assert np.all(np.isfinite(dx))
    assert len(collector.records) > 0
    record = collector.records[0]
    assert record["used_fallback"] == True


def test_collector_gathers_records() -> None:
    """
    Test that Newton trace collector gathers diagnostic records.

    Verifies that the collector properly records diagnostic
    information including condition number and step norm.
    """
    collector = _create_diagnostics_collector()
    A: np.ndarray = np.array(list([
        list([1.0, 2.0]),
        list([0.0, 0.0]),
    ]), dtype=np.float64)
    b: np.ndarray = np.array(list([1.0, 0.0]), dtype=np.float64)

    cfg: NewtonDiagnosticsConfig = NewtonDiagnosticsConfig(
        compute_dense_cond=True,
        enable_fallback=True,
    )

    dense_solve: Any = with_newton_diagnostics(
        np.linalg.solve,
        fallback_solve=dense_lstsq_fallback,
        config=cfg,
        solver_name="dense",
        collector=collector
    )

    dx: np.ndarray = dense_solve(A, b, make_ctx(0))

    assert len(collector.records) > 0
    record = collector.records[0]
    assert "method" in record
    assert "newton_iter" in record
    assert "cond_J" in record
    assert "used_fallback" in record
    assert record["used_fallback"] == True


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
