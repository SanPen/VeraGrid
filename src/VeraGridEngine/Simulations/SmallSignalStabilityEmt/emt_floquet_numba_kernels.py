# SPDX-License-Identifier: MPL-2.0
"""Required Numba kernels for EMT Floquet block methods."""

from __future__ import annotations

from typing import Tuple

import numpy as np
from numba import njit, prange

from VeraGridEngine.basic_structures import IntVec, Mat


@njit(cache=True, fastmath=True)
def _fro_norm_numba(X: Mat) -> float:
    """Compute the Frobenius norm of a real matrix.

    :param X: Real matrix whose norm is required.
    :return: Frobenius norm of ``X``.
    """
    s: float = 0.0
    n: int
    m: int
    n, m = X.shape
    for i in range(n):
        for j in range(m):
            value: float = X[i, j]
            s += value * value
    return np.sqrt(s)


@njit(cache=True, fastmath=True)
def _gemm_left_t_numba(Vi: Mat, W: Mat) -> Mat:
    """Compute ``Vi.T @ W`` using a cache-friendly kernel.

    :param Vi: Left matrix.
    :param W: Right matrix.
    :return: Matrix product ``Vi.T @ W``.
    """
    n: int
    r: int
    n, r = Vi.shape
    p: int = W.shape[1]
    H: Mat = np.zeros((r, p), dtype=np.float64)
    for k in range(n):
        for i in range(r):
            vik: float = Vi[k, i]
            if vik == 0.0:
                pass
            else:
                for j in range(p):
                    H[i, j] += vik * W[k, j]
    return H


@njit(cache=True, fastmath=True)
def _gemm_sub_numba(W: Mat, Vi: Mat, H: Mat) -> None:
    """Subtract ``Vi @ H`` from ``W`` in place.

    :param W: Matrix updated in place.
    :param Vi: Basis block.
    :param H: Projection coefficients.
    :return: None.
    """
    n: int
    r: int
    n, r = Vi.shape
    p: int = H.shape[1]
    for i in range(n):
        for t in range(r):
            coefficient: float = Vi[i, t]
            if coefficient == 0.0:
                pass
            else:
                for j in range(p):
                    W[i, j] -= coefficient * H[t, j]


@njit(cache=True, fastmath=True)
def bmgs_twice_numba(
        V_all: Mat,
        starts: IntVec,
        ends: IntVec,
        W_in: Mat,
        reorth_factor: float = 0.717,
) -> Tuple[Mat, Mat]:
    """Orthogonalize a block against previous blocks with DGKS reorthogonalization.

    :param V_all: Concatenated basis blocks.
    :param starts: Start column for every basis block.
    :param ends: Exclusive end column for every basis block.
    :param W_in: Candidate block to orthogonalize.
    :param reorth_factor: Threshold that triggers the second pass.
    :return: Orthogonalized block and Hessenberg coefficients.
    """
    W: Mat = W_in.copy()
    p: int = W.shape[1]
    m_prev: int = ends[-1] if ends.size > 0 else 0
    H_col: Mat = np.zeros((m_prev, p), dtype=np.float64)
    norm0: float = _fro_norm_numba(W)

    for block_index in range(starts.size):
        start: int = starts[block_index]
        end: int = ends[block_index]
        V_block: Mat = V_all[:, start:end]
        H: Mat = _gemm_left_t_numba(V_block, W)
        H_col[start:end, :] += H
        _gemm_sub_numba(W, V_block, H)

    norm1: float = _fro_norm_numba(W)
    if norm1 < reorth_factor * norm0:
        for block_index in range(starts.size):
            start = starts[block_index]
            end = ends[block_index]
            V_block = V_all[:, start:end]
            H_again: Mat = _gemm_left_t_numba(V_block, W)
            H_col[start:end, :] += H_again
            _gemm_sub_numba(W, V_block, H_again)
    else:
        pass
    return W, H_col


@njit(cache=True, fastmath=True, parallel=True)
def apply_ak_stack_block_numba(Ak_stack: Mat, X0: Mat) -> Mat:
    """Apply ``A[M-1] ... A[0]`` to a block of vectors.

    :param Ak_stack: Dense transition matrices with shape ``(M, n, n)``.
    :param X0: Initial block with shape ``(n, p)``.
    :return: Propagated block with shape ``(n, p)``.
    """
    matrix_count: int = Ak_stack.shape[0]
    state_count: int = Ak_stack.shape[1]
    block_size: int = X0.shape[1]
    Y: Mat = X0.copy()
    T: Mat = np.zeros((state_count, block_size), dtype=np.float64)

    for matrix_index in range(matrix_count):
        A: Mat = Ak_stack[matrix_index]
        for row_index in prange(state_count):
            for column_index in range(block_size):
                T[row_index, column_index] = 0.0
            for inner_index in range(state_count):
                coefficient: float = A[row_index, inner_index]
                if coefficient == 0.0:
                    pass
                else:
                    for column_index in range(block_size):
                        T[row_index, column_index] += coefficient * Y[inner_index, column_index]
        temporary: Mat = Y
        Y = T
        T = temporary
    return Y


@njit(cache=True, fastmath=True)
def solve_lu_dense_block_numba(
        L: Mat,
        U: Mat,
        perm_r: IntVec,
        perm_c: IntVec,
        B: Mat,
) -> Mat:
    """Solve a dense permuted LU system for a block right-hand side.

    :param L: Unit-lower-triangular factor.
    :param U: Upper-triangular factor.
    :param perm_r: Row permutation indices.
    :param perm_c: Column permutation indices.
    :param B: Right-hand side block.
    :return: Solution block.
    """
    n: int = L.shape[0]
    block_size: int = B.shape[1]
    Bp: Mat = np.zeros((n, block_size), dtype=np.float64)
    for row_index in range(n):
        Bp[row_index, :] = B[perm_r[row_index], :]

    Y: Mat = np.zeros((n, block_size), dtype=np.float64)
    for row_index in range(n):
        for column_index in range(block_size):
            value: float = Bp[row_index, column_index]
            for inner_index in range(row_index):
                value -= L[row_index, inner_index] * Y[inner_index, column_index]
            Y[row_index, column_index] = value

    Z: Mat = np.zeros((n, block_size), dtype=np.float64)
    for row_index in range(n - 1, -1, -1):
        for column_index in range(block_size):
            value = Y[row_index, column_index]
            for inner_index in range(row_index + 1, n):
                value -= U[row_index, inner_index] * Z[inner_index, column_index]
            Z[row_index, column_index] = value / U[row_index, row_index]

    X: Mat = np.zeros((n, block_size), dtype=np.float64)
    for row_index in range(n):
        X[perm_c[row_index], :] = Z[row_index, :]
    return X


__all__ = [
    "bmgs_twice_numba",
    "solve_lu_dense_block_numba",
    "apply_ak_stack_block_numba",
]
