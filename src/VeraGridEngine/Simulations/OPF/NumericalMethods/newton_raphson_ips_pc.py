# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import List, Tuple, Callable, Union
import timeit
import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix as csc
from scipy import sparse
from VeraGridEngine.basic_structures import Vec
from VeraGridEngine.Utils.Sparse.csc import pack_3_by_4, diags
from VeraGridEngine.enumerations import SparseSolver
from VeraGridEngine.Simulations.OPF.NumericalMethods.newton_raphson_ips_fx import (
    interior_point_solver as interior_point_solver_fx,
    step_calculation,
    split,
    calc_feas_cond,
    calc_grad_cond,
    calc_c_cond,
    has_tail_converged,
    compute_adaptive_sigma,
    get_ips_linear_solver_candidates,
    solve_kkt_with_fallback,
    IpsIterationHistory,
    IpsSolution,
)


def build_reduced_kkt_system(fx: Vec,
                             G: Vec,
                             H: Vec,
                             Gx: csc,
                             Hx: csc,
                             fxx: csc,
                             Gxx: csc,
                             Hxx: csc,
                             lam: Vec,
                             mu: Vec,
                             z_inv,
                             mu_diag,
                             barrier_rhs: Vec) -> Tuple[csc, Vec]:
    """
    Build the reduced KKT matrix and right-hand side for one primal-dual IPS Newton solve.

    :param fx: Objective Jacobian.
    :param G: Equality residuals.
    :param H: Inequality residuals.
    :param Gx: Equality Jacobian.
    :param Hx: Inequality Jacobian.
    :param fxx: Objective Hessian.
    :param Gxx: Equality Hessian contribution.
    :param Hxx: Inequality Hessian contribution.
    :param lam: Equality multipliers.
    :param mu: Inequality multipliers.
    :param z_inv: Inverse slack diagonal matrix.
    :param mu_diag: Multiplier diagonal matrix.
    :param barrier_rhs: Right-hand side contribution for the complementarity block.
    :return: ``(jac, rhs)`` reduced KKT system.
    """
    Hx_t = Hx.T
    Gx_t = Gx.T
    lxx = fxx + Gxx + Hxx
    m = lxx + Hx_t @ z_inv @ mu_diag @ Hx
    jac = pack_3_by_4(m.tocsc(), Gx_t.tocsc(), Gx.tocsc())
    lx = fx + Gx_t @ lam + Hx_t @ mu
    n = lx + Hx_t @ z_inv @ barrier_rhs
    rhs = -np.r_[n, G]
    return jac, rhs


def interior_point_solver(problem,
                          max_iter=100,
                          tol=1e-6,
                          pf_init=False,
                          trust=0.9,
                          verbose: int = 0,
                          step_control=False,
                          xi: float = 0.99995,
                          sigma: float = 0.1,
                          alpha_min: float = 1e-8,
                          max_stepsize: float = 1e10) -> IpsSolution:
    """
    Solve one nonlinear OPF problem with a Mehrotra-style predictor-corrector primal-dual IPS.

    The predictor-corrector path is tried first. If it does not return a converged point, retry the
    same problem with the historical FX-centered step so the new solver selection remains usable on
    hard large-scale cases while the PC path keeps improving.

    :param problem: Optimization problem structure.
    :param max_iter: Maximum number of iterations.
    :param tol: Convergence tolerance.
    :param pf_init: Use the power flow solution as initial multiplier values.
    :param trust: Initial trust amount for the damped step-control path.
    :param verbose: Verbosity level.
    :param step_control: Use step control to improve the solution process control.
    :param xi: Fraction-to-the-boundary parameter for primal/dual steps.
    :param sigma: Fallback centering parameter when adaptive centering is unavailable.
    :param alpha_min: Minimum accepted primal/dual step before declaring numeric failure.
    :param max_stepsize: Maximum allowed Newton direction norm before declaring numeric failure.
    :return: IPS solution.
    """
    x0_initial: Vec = np.array(problem.x0, copy=True)

    pc_solution: IpsSolution = interior_point_solver_pc_core(problem=problem,
                                                             max_iter=max_iter,
                                                             tol=tol,
                                                             pf_init=pf_init,
                                                             trust=trust,
                                                             verbose=verbose,
                                                             step_control=step_control,
                                                             xi=xi,
                                                             sigma=sigma,
                                                             alpha_min=alpha_min,
                                                             max_stepsize=max_stepsize)
    if pc_solution.converged:
        return pc_solution
    else:
        pass

    problem.x0 = np.array(x0_initial, copy=True)
    return interior_point_solver_fx(problem=problem,
                                    max_iter=max_iter,
                                    tol=tol,
                                    pf_init=pf_init,
                                    trust=trust,
                                    verbose=verbose,
                                    step_control=step_control,
                                    xi=xi,
                                    sigma=sigma,
                                    alpha_min=alpha_min,
                                    max_stepsize=max_stepsize)


def interior_point_solver_pc_core(problem,
                          max_iter=100,
                          tol=1e-6,
                          pf_init=False,
                          trust=0.9,
                          verbose: int = 0,
                          step_control=False,
                          xi: float = 0.99995,
                          sigma: float = 0.1,
                          alpha_min: float = 1e-8,
                          max_stepsize: float = 1e10) -> IpsSolution:
    """
    Solve one nonlinear OPF problem with a Mehrotra-style predictor-corrector primal-dual IPS.

    :param problem: Optimization problem structure.
    :param max_iter: Maximum number of iterations.
    :param tol: Convergence tolerance.
    :param pf_init: Use the power flow solution as initial multiplier values.
    :param trust: Initial trust amount for the damped step-control path.
    :param verbose: Verbosity level.
    :param step_control: Use step control to improve the solution process control.
    :param xi: Fraction-to-the-boundary parameter for primal/dual steps.
    :param sigma: Fallback centering parameter when adaptive centering is unavailable.
    :param alpha_min: Minimum accepted primal/dual step before declaring numeric failure.
    :param max_stepsize: Maximum allowed Newton direction norm before declaring numeric failure.
    :return: IPS solution.
    """
    linear_solver_candidates: List[Tuple[SparseSolver, Callable[[csc, Vec], Vec]]] = get_ips_linear_solver_candidates()
    t_start = timeit.default_timer()

    if not (0.5 <= xi < 1.0):
        raise ValueError(f"xi must be in [0.5, 1.0), got {xi}")
    if not (0.0 < sigma <= 1.0):
        raise ValueError(f"sigma must be in (0.0, 1.0], got {sigma}")
    if alpha_min <= 0.0:
        raise ValueError(f"alpha_min must be positive, got {alpha_min}")
    if max_stepsize <= 0.0:
        raise ValueError(f"max_stepsize must be positive, got {max_stepsize}")

    error: float = 1e6
    iter_counter: int = 0
    x = np.array(problem.x0, copy=True)
    gamma: float = 1.0
    f_prev: float
    cost_cond: float
    nabla = 0.05
    rho_lower = 1.0 - nabla
    rho_upper = 1.0 + nabla
    e = np.ones(problem.nineq)

    if pf_init:
        z0 = 1.0
        z = z0 * np.ones(problem.nineq)
        lam = np.ones(problem.neq)
        mu = z.copy()
        f, G, H = problem.update(x)
        fx, Gx, Hx, _, _, _ = problem.get_jacobians_and_hessians(mu=mu, lam=lam, compute_hessians=False)
        z = -H
        z = np.array([1e-2 if zz < 1e-2 else zz for zz in z])
        z_inv = diags(1.0 / z)
        mu = gamma * (z_inv @ e)
        mu_diag = diags(mu)
        lam = sparse.linalg.lsqr(Gx.T, -fx - Hx.T @ mu.T)[0]
    else:
        f, G, H = problem.update(x)
        z0 = 1.0
        z = z0 * np.ones(problem.nineq)
        mu = z0 * np.ones(problem.nineq)
        lam = np.zeros(problem.neq)
        kk = np.flatnonzero(H < -z0)
        z[kk] = -H[kk]
        z_inv = diags(1.0 / z)
        kk = np.flatnonzero((gamma / z) > z0)
        mu[kk] = gamma / z[kk]
        mu_diag = diags(mu)

    fx, Gx, Hx, fxx, Gxx, Hxx = problem.get_jacobians_and_hessians(mu=mu, lam=lam, compute_hessians=True)
    Hx_t = Hx.T
    Gx_t = Gx.T
    lx = fx + Gx_t @ lam + Hx_t @ mu
    feas_cond = calc_feas_cond(g=G, h=H, x=x, z=z)
    gradcond = calc_grad_cond(lx=lx, lam=lam, mu=mu)
    comp_cond = calc_c_cond(mu=mu, z=z, x=x)
    f_prev = f
    cost_cond = 0.0
    error = np.max([feas_cond, gradcond, comp_cond, gamma])
    converged = has_tail_converged(problem=problem,
                                   step_control=step_control,
                                   feas_cond=feas_cond,
                                   gradcond=gradcond,
                                   comp_cond=comp_cond,
                                   cost_cond=cost_cond,
                                   gamma=gamma,
                                   tol=tol)
    max_displ = 0.0
    error_evolution = np.zeros(max_iter + 1)
    feas_cond_evolution = np.zeros(max_iter + 1)
    objective_history = np.full(max_iter + 1, np.nan, dtype=float)
    gradcond_history = np.full(max_iter + 1, np.nan, dtype=float)
    compcond_history = np.full(max_iter + 1, np.nan, dtype=float)
    costcond_history = np.full(max_iter + 1, np.nan, dtype=float)
    gamma_history = np.full(max_iter + 1, np.nan, dtype=float)
    alphap_history = np.full(max_iter + 1, np.nan, dtype=float)
    alphad_history = np.full(max_iter + 1, np.nan, dtype=float)
    step_norm_history = np.full(max_iter + 1, np.nan, dtype=float)

    objective_scale = getattr(problem, "objective_scale", 1.0)
    feas_cond_evolution[iter_counter] = feas_cond
    error_evolution[0] = error
    objective_history[0] = f / objective_scale
    gradcond_history[0] = gradcond
    compcond_history[0] = comp_cond
    costcond_history[0] = cost_cond
    gamma_history[0] = gamma
    alphap_history[0] = 0.0
    alphad_history[0] = 0.0
    step_norm_history[0] = 0.0
    residuals = np.zeros(problem.NV + problem.neq)
    dlam = None

    while not converged and iter_counter < max_iter:
        z_inv = diags(1.0 / z)
        mu_diag = diags(mu)

        # Predictor: affine-scaling direction with zero centering target.
        barrier_rhs_aff = mu * H
        jac, rhs = build_reduced_kkt_system(fx=fx,
                                            G=G,
                                            H=H,
                                            Gx=Gx,
                                            Hx=Hx,
                                            fxx=fxx,
                                            Gxx=Gxx,
                                            Hxx=Hxx,
                                            lam=lam,
                                            mu=mu,
                                            z_inv=z_inv,
                                            mu_diag=mu_diag,
                                            barrier_rhs=barrier_rhs_aff)
        dxdlam_aff, _, _ = solve_kkt_with_fallback(jac=jac,
                                                   r=rhs,
                                                   linear_solver_candidates=linear_solver_candidates,
                                                   max_stepsize=max_stepsize)
        if dxdlam_aff is None:
            break

        dx_aff, dlam_aff = split(dxdlam_aff, problem.NV)
        if not np.all(np.isfinite(dx_aff)) or not np.all(np.isfinite(dlam_aff)):
            break

        dz_aff = -H - z - Hx @ dx_aff
        dmu_aff = -mu + z_inv @ (-mu * dz_aff)

        alpha_p_aff = step_calculation(z, dz_aff, tau=xi)
        alpha_d_aff = step_calculation(mu, dmu_aff, tau=xi)
        if (not np.isfinite(alpha_p_aff)) or (not np.isfinite(alpha_d_aff)) or alpha_p_aff <= 0.0 or alpha_d_aff <= 0.0:
            break

        # Corrector: target a centered point and cancel the affine complementarity cross term.
        if problem.nineq > 0:
            sigma_iter: float = compute_adaptive_sigma(mu=mu,
                                                       z=z,
                                                       dmu=dmu_aff,
                                                       dz=dz_aff,
                                                       alpha_p=alpha_p_aff,
                                                       alpha_d=alpha_d_aff)
            mu_bar = float(np.mean(mu * z))
            sigma_mu = sigma_iter * mu_bar
            corrector_cross = dmu_aff * dz_aff
            barrier_rhs = sigma_mu * e - corrector_cross + mu * H
        else:
            sigma_iter = sigma
            barrier_rhs = np.zeros(0, dtype=float)

        jac, rhs = build_reduced_kkt_system(fx=fx,
                                            G=G,
                                            H=H,
                                            Gx=Gx,
                                            Hx=Hx,
                                            fxx=fxx,
                                            Gxx=Gxx,
                                            Hxx=Hxx,
                                            lam=lam,
                                            mu=mu,
                                            z_inv=z_inv,
                                            mu_diag=mu_diag,
                                            barrier_rhs=barrier_rhs)
        dxdlam, linear_solver_used, linear_residual = solve_kkt_with_fallback(jac=jac,
                                                                              r=rhs,
                                                                              linear_solver_candidates=linear_solver_candidates,
                                                                              max_stepsize=max_stepsize)
        if dxdlam is None:
            break

        if verbose > 2 and linear_solver_used != linear_solver_candidates[0][0]:
            print(f"\tFallback linear solver: {linear_solver_used.value}, residual={linear_residual:.3e}")

        dx, dlam = split(dxdlam, problem.NV)
        if not np.all(np.isfinite(dx)) or not np.all(np.isfinite(dlam)):
            break
        if np.linalg.norm(np.r_[dx, dlam]) > max_stepsize:
            break

        dz = -H - z - Hx @ dx
        if problem.nineq > 0:
            dmu = z_inv @ (sigma_mu * e - mu * z - corrector_cross - mu * dz)
        else:
            dmu = np.zeros(0, dtype=float)

        if step_control:
            x1 = x + dx
            f1, G1, H1 = problem.update(x1)
            fx1, Gx1, Hx1, _, _, _ = problem.get_jacobians_and_hessians(mu=mu, lam=lam, compute_hessians=False)
            l1 = f1 + lam.T @ G1 + mu.T @ (H1 + z) - gamma * np.sum(np.log(z))
            lx1 = fx1 + Gx1.T @ lam + Hx1.T @ mu
            feas_cond1 = calc_feas_cond(g=G1, h=H1, x=x1, z=z)
            gradcond1 = calc_grad_cond(lx=lx1, lam=lam, mu=mu)

            if feas_cond1 > feas_cond and gradcond1 > calc_grad_cond(lx=lx, lam=lam, mu=mu):
                lxx = fxx + Gxx + Hxx
                l0 = f + np.dot(lam, G) + np.dot(mu, H + z) - gamma * np.sum(np.log(z))
                alpha = trust
                for _ in range(20):
                    dx1 = alpha * dx
                    x1 = x + dx1
                    f1, G1, H1 = problem.update(x1)
                    l1 = f1 + lam.T @ G1 + mu.T @ (H1 + z) - gamma * np.sum(np.log(z))
                    rho = (l1 - l0) / (lx @ dx1 + 0.5 * dx1.T @ lxx @ dx1)
                    if rho_lower < rho < rho_upper:
                        break
                    alpha = alpha / 2.0
                dx = alpha * dx
                dz = alpha * dz
                dlam = alpha * dlam
                dmu = alpha * dmu

        alpha_p = step_calculation(z, dz, tau=xi)
        alpha_d = step_calculation(mu, dmu, tau=xi)
        if (not np.isfinite(alpha_p)) or (not np.isfinite(alpha_d)) or alpha_p <= 0.0 or alpha_d <= 0.0:
            break

        x += dx * alpha_p
        z += dz * alpha_p
        lam += dlam * alpha_d
        mu += dmu * alpha_d
        gamma = sigma_iter * mu @ z / problem.nineq if problem.nineq > 0 else 0.0

        if (not np.all(np.isfinite(x)) or not np.all(np.isfinite(z)) or
                not np.all(np.isfinite(lam)) or not np.all(np.isfinite(mu)) or
                gamma < np.finfo(float).eps or gamma > 1.0 / np.finfo(float).eps):
            break

        f, G, H = problem.update(x)
        fx, Gx, Hx, fxx, Gxx, Hxx = problem.get_jacobians_and_hessians(mu=mu, lam=lam, compute_hessians=True)
        Hx_t = Hx.T
        Gx_t = Gx.T
        lx = fx + Hx_t @ mu + Gx_t @ lam
        feas_cond = calc_feas_cond(g=G, h=H, x=x, z=z)
        gradcond = calc_grad_cond(lx=lx, lam=lam, mu=mu)
        comp_cond = calc_c_cond(mu=mu, z=z, x=x)
        cost_cond = abs(f - f_prev) / (1.0 + abs(f_prev)) if step_control else 0.0
        error = np.max([feas_cond, gradcond, comp_cond, gamma])
        max_displ = np.max(np.r_[dx, dlam, dz, dmu]) if problem.nineq > 0 else np.max(np.r_[dx, dlam])
        residuals = rhs
        converged = has_tail_converged(problem=problem,
                                       step_control=step_control,
                                       feas_cond=feas_cond,
                                       gradcond=gradcond,
                                       comp_cond=comp_cond,
                                       cost_cond=cost_cond,
                                       gamma=gamma,
                                       tol=tol)

        iter_counter += 1
        feas_cond_evolution[iter_counter] = feas_cond
        error_evolution[iter_counter] = error
        objective_history[iter_counter] = f / objective_scale
        gradcond_history[iter_counter] = gradcond
        compcond_history[iter_counter] = comp_cond
        costcond_history[iter_counter] = cost_cond
        gamma_history[iter_counter] = gamma
        alphap_history[iter_counter] = alpha_p
        alphad_history[iter_counter] = alpha_d
        step_norm_history[iter_counter] = np.linalg.norm(dx)
        f_prev = f

        if verbose > 1:
            print(f'Iteration: {iter_counter - 1}', "-" * 80)
            print("\tGamma:", gamma)
            print("\tComp cond:", comp_cond)
            print("\tCost cond:", cost_cond)
            print("\tErr:", error)
            print("\tMax Displacement:", max_displ)
            if verbose > 2:
                x_df = pd.DataFrame(data={'x': x, 'dx': dx})
                eq_df = pd.DataFrame(data={'λ': lam, 'dλ': dlam})
                ineq_df = pd.DataFrame(data={'mu': mu, 'z': z, 'dmu': dmu, 'dz': dz})
                print("x:\n", x_df)
                print("EQ:\n", eq_df)
                print("INEQ:\n", ineq_df)

    t_end = timeit.default_timer()
    if verbose > 0:
        print(f'SOLUTION', "-" * 80)
        print(f"\tF.obj: {f / objective_scale}")
        print(f"\tErr: {error}")
        print(f'\tIterations: {iter_counter}')
        print(f'\tMax Displacement: {max_displ}')
        print(f'\tTime elapsed (s): {t_end - t_start}')
        print(f'\tFeas cond: ', feas_cond)

    history = IpsIterationHistory(
        iteration=np.arange(iter_counter + 1, dtype=int),
        objective=objective_history[:iter_counter + 1],
        feas_cond=feas_cond_evolution[:iter_counter + 1],
        gradcond=gradcond_history[:iter_counter + 1],
        comp_cond=compcond_history[:iter_counter + 1],
        cost_cond=costcond_history[:iter_counter + 1],
        gamma=gamma_history[:iter_counter + 1],
        alpha_p=alphap_history[:iter_counter + 1],
        alpha_d=alphad_history[:iter_counter + 1],
        step_norm=step_norm_history[:iter_counter + 1],
    )
    return IpsSolution(x=x,
                       error=error,
                       gamma=gamma,
                       lam=lam,
                       dlam=dlam,
                       mu=mu,
                       z=z,
                       residuals=residuals,
                       converged=converged,
                       iterations=iter_counter,
                       error_evolution=error_evolution,
                       history=history)
