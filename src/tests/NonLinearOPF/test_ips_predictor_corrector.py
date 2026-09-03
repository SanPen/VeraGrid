import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import VeraGridEngine.api as gce

from VeraGridEngine.Simulations.OPF.ac_opf_worker import run_nonlinear_opf
import VeraGridEngine.Simulations.OPF.NumericalMethods.newton_raphson_ips_pc as ips_pc


def test_nr_pc_case9_converges_at_benchmark_tolerance():
    """
    The predictor-corrector solver selection should solve the standard ACOPF smoke case
    at the benchmark tolerance used by the large PGLIB runs.
    """
    file_path = Path(__file__).resolve().parent.parent / "data" / "grids" / "Matpower" / "case9.matpower"
    grid = gce.FileOpen(str(file_path)).open()

    opf_options = gce.OptimalPowerFlowOptions(
        ips_method=gce.SolverType.NR_PC,
        ips_tolerance=1e-6,
        ips_iterations=100,
        verbose=0,
    )
    res = run_nonlinear_opf(grid=grid, t_idx=None, opf_options=opf_options)

    assert res.converged
    assert np.allclose(res.Pg, [0.897986, 1.343206, 0.941874], atol=1e-3)


def test_nr_pc_fallback_restores_original_seed(monkeypatch):
    """
    If the predictor-corrector attempt fails, the FX fallback must restart from the
    original seed rather than the partially updated predictor-corrector iterate.
    """
    original_x0 = np.array([1.0, 2.0, 3.0], dtype=float)
    problem = SimpleNamespace(x0=np.array(original_x0, copy=True))

    def fake_pc_core(problem, **kwargs):
        problem.x0[:] = 99.0
        return SimpleNamespace(converged=False, source="pc")

    def fake_fx(problem, **kwargs):
        assert np.allclose(problem.x0, original_x0)
        return SimpleNamespace(converged=True, source="fx")

    monkeypatch.setattr(ips_pc, "interior_point_solver_pc_core", fake_pc_core)
    monkeypatch.setattr(ips_pc, "interior_point_solver_fx", fake_fx)

    result = ips_pc.interior_point_solver(problem=problem)

    assert result.source == "fx"
    assert np.allclose(problem.x0, original_x0)
