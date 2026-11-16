# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from pathlib import Path
from typing import Tuple

import numpy as np
import pytest

import VeraGridEngine.api as gce
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.Simulations.PowerFlow.Formulations.pf_full_acdc_with_negative_poles import PfAcDcWithNegativePoles
from VeraGridEngine.Utils.Sparse.csc2 import CSC, is_valid_for_super_lu, mat_to_scipy
from VeraGridEngine.enumerations import ShuntControlMode, SolverType, StaticGeneratorControlMode


def _grid_with_a_droop_shunt(load_q: float, bmin: float, bmax: float,
                             remote: bool = False) -> Tuple[gce.MultiCircuit, gce.ControllableShunt, gce.Bus]:
    """Slack, a loaded bus with the droop shunt and, optionally, a farther bus it controls.

    :param load_q: Reactive load in MVAr at the shunt bus (negative raises the voltage)
    :param bmin: Shunt Bmin in MVAr at 1 p.u., capacitive positive
    :param bmax: Shunt Bmax in MVAr at 1 p.u., capacitive positive
    :param remote: Control the voltage of a third bus
    :return: Grid, droop shunt and controlled bus
    """
    grid = gce.MultiCircuit(Sbase=100.0)
    slack = gce.Bus(name="slack", Vnom=20.0, is_slack=True)
    bus = gce.Bus(name="svs", Vnom=20.0)
    far = gce.Bus(name="far", Vnom=20.0)
    for b in (slack, bus, far):
        grid.add_bus(b)
    grid.add_generator(slack, gce.Generator(vset=1.0))
    grid.add_line(gce.Line(bus_from=slack, bus_to=bus, r=0.01, x=0.08))
    grid.add_line(gce.Line(bus_from=bus, bus_to=far, r=0.01, x=0.05))
    grid.add_load(bus, gce.Load(P=40.0, Q=load_q))
    grid.add_load(far, gce.Load(P=20.0, Q=10.0))
    controlled: gce.Bus = far if remote else bus
    shunt = gce.ControllableShunt(name="droop", number_of_steps=1, step=0, Bmin=bmin, Bmax=bmax, vset=1.0,
                                  qdroop=400.0, control_mode=ShuntControlMode.QVDroop, control_bus=controlled)
    shunt.b_steps = np.array([0.0])
    shunt.g_steps = np.array([0.0])
    shunt.active_steps = np.ones(1, dtype=int)
    grid.add_controllable_shunt(bus, shunt)
    return grid, shunt, controlled


def _solved_q(grid: gce.MultiCircuit, options: gce.PowerFlowOptions) -> Tuple[float, float, float]:
    """Injected shunt Q in MVAr and the shunt and controlled voltage modules, solved by Newton-Raphson alone.

    A fallback method must not hide a Jacobian that Newton cannot factorize.

    :param grid: Grid of _grid_with_a_droop_shunt
    :param options: Power flow options
    :return: Q, |V| at the shunt bus, |V| at the controlled bus
    """
    res = gce.power_flow(grid, options)
    assert res.converged
    shunt: gce.ControllableShunt = grid.controllable_shunts[0]
    buses = list(grid.buses)
    return (-float(res.shunt_q[len(grid.shunts)]), float(abs(res.voltage[buses.index(shunt.bus)])),
            float(abs(res.voltage[buses.index(shunt.control_bus)])))


@pytest.mark.parametrize("remote", [False, True])
def test_droop_shunt_follows_its_law_inside_the_band(remote: bool) -> None:
    grid, shunt, _ = _grid_with_a_droop_shunt(load_q=30.0, bmin=-200.0, bmax=200.0, remote=remote)
    q, vm, vc = _solved_q(grid, gce.PowerFlowOptions(solver_type=SolverType.NR, retry_with_other_methods=False))
    assert q == pytest.approx(shunt.Qdroop * (shunt.Vset - vc), abs=1e-6)
    assert shunt.Bmin * vm ** 2 < q < shunt.Bmax * vm ** 2
    assert q > 1.0


def test_droop_shunt_holds_its_capacitive_limit() -> None:
    grid, shunt, _ = _grid_with_a_droop_shunt(load_q=30.0, bmin=-200.0, bmax=5.0)
    q, vm, vc = _solved_q(grid, gce.PowerFlowOptions(solver_type=SolverType.NR, retry_with_other_methods=False))
    assert shunt.Qdroop * (shunt.Vset - vc) > shunt.Bmax * vm ** 2
    assert q == pytest.approx(shunt.Bmax * vm ** 2, abs=1e-6)


def test_droop_shunt_holds_its_inductive_limit() -> None:
    grid, shunt, _ = _grid_with_a_droop_shunt(load_q=-60.0, bmin=-5.0, bmax=200.0)
    q, vm, vc = _solved_q(grid, gce.PowerFlowOptions(solver_type=SolverType.NR, retry_with_other_methods=False))
    assert shunt.Qdroop * (shunt.Vset - vc) < shunt.Bmin * vm ** 2
    assert q == pytest.approx(shunt.Bmin * vm ** 2, abs=1e-6)


def test_droop_shunt_controls_its_own_bus_when_the_control_bus_is_in_another_island() -> None:
    grid, shunt, far = _grid_with_a_droop_shunt(load_q=30.0, bmin=-200.0, bmax=200.0, remote=True)
    grid.lines[1].active = False
    grid.add_generator(far, gce.Generator(vset=1.05))
    far.is_slack = True
    res = gce.power_flow(grid, gce.PowerFlowOptions(solver_type=SolverType.NR, retry_with_other_methods=False))
    assert res.converged
    buses = list(grid.buses)
    vm: float = float(abs(res.voltage[buses.index(shunt.bus)]))
    q: float = -float(res.shunt_q[len(grid.shunts)])
    assert q == pytest.approx(shunt.Qdroop * (shunt.Vset - vm), abs=1e-6)
    # The reported Q is the one the solution injected: the nodal balance closes at the shunt bus
    assert float(res.Sbus[buses.index(shunt.bus)].imag) == pytest.approx(q - 30.0, abs=1e-6)


@pytest.mark.parametrize("bmax, remote", [(200.0, False), (200.0, True), (5.0, False)])
def test_droop_jacobian_matches_finite_differences(bmax: float, remote: bool) -> None:
    grid, _, _ = _grid_with_a_droop_shunt(load_q=30.0, bmin=-200.0, bmax=bmax, remote=remote)
    grid.add_static_generator(grid.buses[2], gce.StaticGenerator(
        name="sgen", Snom=50.0, control_mode=StaticGeneratorControlMode.QVDroop, vset=1.0, droop=4.0))
    nc = compile_numerical_circuit_at(grid, t_idx=None)
    Qmax, Qmin = nc.get_reactive_power_limits()
    problem = PfAcDcWithNegativePoles(V0=nc.bus_data.Vbus.copy(), S0=nc.get_power_injections_pu(),
                                      I0=nc.get_current_injections_pu(), Y0=-nc.get_admittance_injections_pu(),
                                      Qmin=Qmin, Qmax=Qmax, nc=nc, options=gce.PowerFlowOptions(),
                                      logger=gce.Logger())
    problem.Vm[1:] = np.array([0.96, 0.95])
    problem.Va[1:] = np.array([-0.05, -0.07])
    jacobian: CSC = problem.Jacobian(autodiff=False)
    assert is_valid_for_super_lu(jacobian) and jacobian.nnz == len(jacobian.data) == jacobian.indptr[-1]
    analytic = mat_to_scipy(jacobian).toarray()
    numeric = mat_to_scipy(problem.Jacobian(autodiff=True)).toarray()
    assert np.abs(analytic - numeric).max() < 1e-4


def test_static_generator_droop_alone_converges_by_newton() -> None:
    grid, shunt, far = _grid_with_a_droop_shunt(load_q=30.0, bmin=-200.0, bmax=200.0)
    shunt.active = False
    grid.add_static_generator(far, gce.StaticGenerator(
        name="sgen", Snom=50.0, control_mode=StaticGeneratorControlMode.QVDroop, vset=1.0, droop=4.0))
    res = gce.power_flow(grid, gce.PowerFlowOptions(solver_type=SolverType.NR, retry_with_other_methods=False))
    assert res.converged


def test_droop_shunt_needs_a_positive_slope() -> None:
    grid, shunt, _ = _grid_with_a_droop_shunt(load_q=30.0, bmin=-200.0, bmax=200.0)
    shunt.Qdroop = 0.0
    with pytest.raises(ValueError, match="Shunt Q-V droop"):
        gce.power_flow(grid)


def test_three_phase_power_flow_rejects_a_remote_droop_shunt() -> None:
    grid, _, _ = _grid_with_a_droop_shunt(load_q=30.0, bmin=-200.0, bmax=200.0, remote=True)
    with pytest.raises(ValueError, match="Remote shunt Q-V droop.*three-phase"):
        gce.power_flow3ph(grid)


@pytest.mark.parametrize("bmax", [5.0, 200.0])
def test_three_phase_power_flow_matches_local_shunt_droop_in_balance(bmax: float) -> None:
    """Verify the local droop and its capacitive limit with the same balanced grid."""
    grid, _, _ = _grid_with_a_droop_shunt(load_q=30.0, bmin=-200.0, bmax=bmax)
    options: gce.PowerFlowOptions = gce.PowerFlowOptions(
        solver_type=SolverType.NR, tolerance=1e-9, retry_with_other_methods=False,
    )
    balanced = gce.power_flow(grid, options)
    three_phase = gce.power_flow3ph(grid, options)
    assert balanced.converged and three_phase.converged
    np.testing.assert_allclose(three_phase.voltage_A, balanced.voltage, atol=1e-8, rtol=0.0)


def test_droop_shunt_survives_a_veragrid_file(tmp_path: Path) -> None:
    grid, shunt, _ = _grid_with_a_droop_shunt(load_q=30.0, bmin=-200.0, bmax=200.0, remote=True)
    path: Path = tmp_path / "droop_shunt.veragrid"
    gce.save_file(grid=grid, filename=str(path))
    loaded: gce.MultiCircuit = gce.open_file(str(path))
    back: gce.ControllableShunt = loaded.controllable_shunts[0]
    assert back.control_mode == ShuntControlMode.QVDroop
    assert back.Qdroop == pytest.approx(shunt.Qdroop)
    assert (back.Bmin, back.Bmax, back.Vset) == pytest.approx((shunt.Bmin, shunt.Bmax, shunt.Vset))
    assert back.control_bus.idtag == shunt.control_bus.idtag

