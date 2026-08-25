import time
import numpy as np
import scipy.sparse as sp
import scipy.linalg as la
import scipy.sparse.linalg as spla


def test_small_signal_mathematical_benchmarks():
    """
    This test empirically validates the mathematical and computational enhancements of the
    small-signal stability module. It benchmarks the performance speedup of using SuperLU
    factorization for DAE reduction, verifies the mitigation of numerical stiffness via
    matrix balancing, and demonstrates the mathematical necessity of bi-orthogonality
    in non-Hermitian Krylov subspaces.
    """
    n_state = 200
    n_algeb = 2000

    fx = np.diag(np.concatenate([np.linspace(-1000, -100, 100), np.linspace(-1, -0.1, 100)]))
    fy = np.random.randn(n_state, n_algeb)
    gx = np.random.randn(n_algeb, n_state)

    gy = sp.diags(np.random.rand(n_algeb) + 10) + sp.rand(n_algeb, n_algeb, density=0.01)
    gy = gy.tocsc()

    print("\n\n--- BENCHMARK 1: DAE REDUCTION (KRYLOV ITERATION SIMULATION) ---")

    n_iterations = 50
    vectors = np.random.randn(n_state, n_iterations)

    t0 = time.perf_counter()
    for i in range(n_iterations):
        v = vectors[:, i]
        _ = fx @ v - fy @ spla.spsolve(gy, gx @ v)
    t_legacy = time.perf_counter() - t0

    t0 = time.perf_counter()
    gy_lu = spla.splu(gy)
    for i in range(n_iterations):
        v = vectors[:, i]
        _ = fx @ v - fy @ gy_lu.solve(gx @ v)
    t_veragrid = time.perf_counter() - t0

    print(f"Legacy Execution Time (spsolve) : {t_legacy:.4f} s")
    print(f"VeraGrid Execution Time (splu)  : {t_veragrid:.4f} s")
    print(f"Performance Speedup             : {t_legacy / t_veragrid:.2f}x")

    A_veragrid = fx - fy @ gy_lu.solve(gx.toarray() if sp.issparse(gx) else gx)

    assert t_veragrid < t_legacy, "SuperLU factorization must outperform iterative spsolve."

    print("\n--- BENCHMARK 2: NUMERICAL STIFFNESS MITIGATION (MATRIX BALANCING) ---")

    T_stiff = np.diag(np.concatenate([np.ones(100) * 1e-5, np.ones(100) * 1e5]))
    A_stiff = np.linalg.inv(T_stiff) @ A_veragrid @ T_stiff

    cond_unbalanced = np.linalg.cond(A_stiff)

    A_bal, _ = la.matrix_balance(A_stiff, separate=False)
    cond_balanced = np.linalg.cond(A_bal)

    print(f"Unbalanced Condition Number : {cond_unbalanced:.2e}")
    print(f"Balanced Condition Number   : {cond_balanced:.2e}")

    assert cond_balanced < cond_unbalanced
    assert cond_unbalanced / cond_balanced > 1e4, "Matrix balancing must significantly improve the condition number."

    print("\n--- BENCHMARK 3: BI-ORTHOGONALITY IN KRYLOV SUBSPACES ---")

    mu_R, v = spla.eigs(A_bal, k=2, which="LM")
    mu_L, w = spla.eigs(A_bal.T, k=2, which="LM")

    idx_R = np.argsort(mu_R.real, kind="stable")
    idx_L = np.argsort(mu_L.real, kind="stable")
    v = v[:, idx_R]
    w = w[:, idx_L]

    v_ortho_check = np.abs(np.vdot(v[:, 0], v[:, 1]))
    print(f"Standard Orthogonality Check (|V_0^* * V_1|) : {v_ortho_check:.4e}")
    assert v_ortho_check > 1e-10, "Right eigenvectors of a real non-Hermitian matrix are not orthogonal."

    w[:, 0] /= np.dot(w[:, 0], v[:, 0])
    w[:, 1] /= np.dot(w[:, 1], v[:, 1])

    cross_product = np.abs(np.dot(w[:, 0], v[:, 1]))
    print(f"Bi-orthogonality Check (|W_0^T * V_1|)       : {cross_product:.4e}")
    assert cross_product < 1e-10, "Left and right eigenspaces must be bi-orthogonal."

if __name__ == "__main__":
    test_small_signal_mathematical_benchmarks()