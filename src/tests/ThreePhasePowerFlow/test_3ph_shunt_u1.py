"""Continuous shunts regulate U1 with one physical susceptance per device."""
import numpy as np
import pytest

import VeraGridEngine.api as vge
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.IO.dgs.dgs_objects import ElmSvs
from VeraGridEngine.IO.dgs.dgs_to_veragrid import convert_dgs_to_controllable_shunt_from_svs
from VeraGridEngine.Simulations.PowerFlow3ph.Formulations.positive_sequence_control import PositiveSequenceControl
from VeraGridEngine.enumerations import ShuntConnectionType


def make_grid(sbase: float, connection: ShuntConnectionType, unbalanced: bool = True) -> vge.MultiCircuit:
    """Build an independently checkable two-bus circuit.

    :param sbase: System base, MVA.
    :param connection: Shunt return path.
    :param unbalanced: Unequal phase loads when true.
    :return: Circuit with one continuous shunt.
    """
    grid: vge.MultiCircuit = vge.MultiCircuit(Sbase=sbase)
    source: vge.Bus = grid.add_bus(vge.Bus(name='Slack', Vnom=20.0, is_slack=True))
    target: vge.Bus = grid.add_bus(vge.Bus(name='Controlled', Vnom=20.0))
    grid.add_generator(source,vge.Generator())
    grid.add_line(vge.Line(bus_from=source,bus_to=target,r=0.02*sbase/100,x=0.08*sbase/100,
                          r0=0.04*sbase/100,x0=0.16*sbase/100))
    shunt: vge.ControllableShunt = vge.ControllableShunt(vset=1.01,Bmin=-100.0,Bmax=100.0,G=0.4,B=8.0)
    shunt.conn = connection
    grid.add_controllable_shunt(target,shunt)
    if unbalanced:
        grid.add_load(target,vge.Load(P=15.0,Q=6.0,P1=8.0,P2=5.0,P3=2.0,Q1=3.0,Q2=2.0,Q3=1.0))
    else:
        grid.add_load(target,vge.Load(P=15.0,Q=6.0))
    return grid


def solve(grid: vge.MultiCircuit, solver: vge.SolverType = vge.SolverType.NR,
          limits: bool = True) -> vge.PowerFlowResults3Ph:
    """Solve with the existing method and no fallback.

    :param grid: Test network.
    :param solver: Numerical method.
    :param limits: Enable existing control-limit enforcement.
    :return: Converged ABC solution.
    """
    result: vge.PowerFlowResults3Ph = vge.power_flow3ph(grid,options=vge.PowerFlowOptions(
        solver_type=solver,tolerance=1e-9,max_iter=100,control_q=limits,retry_with_other_methods=False))
    assert result.converged
    return result


def check_current(result: vge.PowerFlowResults3Ph, sbase: float,
                  connection: ShuntConnectionType) -> float:
    """Infer a common B from line-terminal KCL, independently of control internals.

    :param result: Converged ABC power flow.
    :param sbase: System power base.
    :param connection: Expected physical return path.
    :return: Inferred susceptance, MVAr at 1 pu.
    """
    voltage: np.ndarray = np.array((result.voltage_A[1],result.voltage_B[1],result.voltage_C[1]))
    power: np.ndarray = np.array((result.St_A[0],result.St_B[0],result.St_C[0]))
    power += np.array((8+3j,5+2j,2+1j))
    current: np.ndarray = np.conj(power/voltage)*3/sbase
    effective: np.ndarray = voltage.copy()
    if connection != ShuntConnectionType.GroundedStar:
        effective -= np.mean(voltage)
        assert abs(np.sum(current)) < 1e-8
    else:
        pass
    admittance: complex = -np.vdot(effective,current)/np.vdot(effective,effective)
    np.testing.assert_allclose(current,-admittance*effective,atol=2e-8)
    assert abs(admittance.real*sbase-0.4) < 1e-6
    return float(admittance.imag*sbase)


@pytest.mark.parametrize('solver',(vge.SolverType.NR,vge.SolverType.LM,vge.SolverType.PowellDogLeg))
@pytest.mark.parametrize('connection',(ShuntConnectionType.GroundedStar,ShuntConnectionType.Delta,
                                      ShuntConnectionType.FloatingStar))
@pytest.mark.parametrize('sbase',(25.0,100.0))
def test_shunt_controls_u1_and_common_susceptance(sbase: float, connection: ShuntConnectionType,
                                               solver: vge.SolverType) -> None:
    """Control U1 without forcing equal phase magnitudes; preserve physical I2/I0.

    :param sbase: System power base.
    :param connection: Shunt connection.
    :param solver: Existing solver.
    """
    grid: vge.MultiCircuit = make_grid(sbase,connection)
    result: vge.PowerFlowResults3Ph = solve(grid,solver)
    voltage: np.ndarray = np.array((result.voltage_A[1],result.voltage_B[1],result.voltage_C[1]))
    a: complex = np.exp(2j*np.pi/3)
    assert abs(abs(voltage@np.array((1,a,a*a))/3)-1.01) < 1e-8
    assert np.ptp(abs(voltage)) > 1e-3
    assert abs(check_current(result,sbase,connection)) < 100.0


@pytest.mark.parametrize('sbase',(25.0,100.0))
def test_shunt_balanced_matches_positive_flow(sbase: float) -> None:
    """Recover the existing positive-sequence solution when all phases are balanced.

    :param sbase: System power base.
    """
    grid: vge.MultiCircuit = make_grid(sbase,ShuntConnectionType.Delta,unbalanced=False)
    result: vge.PowerFlowResults3Ph = solve(grid,limits=False)
    positive: vge.PowerFlowResults = vge.power_flow(grid,options=vge.PowerFlowOptions(
        tolerance=1e-9,control_q=False,retry_with_other_methods=False))
    assert positive.converged
    np.testing.assert_allclose(result.voltage_A,positive.voltage,atol=1e-8)


@pytest.mark.parametrize('solver',(vge.SolverType.NR,vge.SolverType.LM))
@pytest.mark.parametrize('vset,expected_b',((1.05,3.0),(0.93,-2.0)))
def test_shunt_limit_retains_susceptance(vset: float, expected_b: float, solver: vge.SolverType) -> None:
    """At a limit, retain B rather than imposing a voltage-independent reactive power.

    :param vset: Voltage request causing saturation.
    :param expected_b: Saturated injected nominal susceptance.
    :param solver: Existing solver.
    """
    grid: vge.MultiCircuit = make_grid(100.0,ShuntConnectionType.Delta)
    shunt: vge.ControllableShunt = grid.controllable_shunts[0]
    shunt.Vset,shunt.Bmin,shunt.Bmax = vset,-3.0,2.0
    result: vge.PowerFlowResults3Ph = solve(grid,solver)
    assert abs(check_current(result,100.0,ShuntConnectionType.Delta)-expected_b) < 1e-6


def test_shunt_profiles_units_copy_and_inactive() -> None:
    """Preserve units, profiles, connection and inactivity in numerical copies/islands."""
    grid: vge.MultiCircuit = make_grid(100.0,ShuntConnectionType.Delta)
    shunt: vge.ControllableShunt = grid.controllable_shunts[0]
    shunt.Vset_prof = np.array((1.02,1.03))
    shunt.active_prof = np.array((True,False))
    shunt.use_kw = True
    shunt.G,shunt.B,shunt.Bmin,shunt.Bmax = 400.0,8000.0,-100000.0,100000.0
    nc: NumericalCircuit = compile_numerical_circuit_at(grid,t_idx=0,fill_three_phase=True)
    for copied in (nc,nc.copy(),nc.split_into_islands()[0]):
        control: PositiveSequenceControl = PositiveSequenceControl(copied,np.arange(8))
        np.testing.assert_allclose(control.vset,(1.02,))
        np.testing.assert_allclose(control.qmin,(-1.0,))
        np.testing.assert_allclose(control.qmax,(1.0,))
        assert copied.shunt_data.conn[0] == ShuntConnectionType.Delta.idx()
    offline: NumericalCircuit = compile_numerical_circuit_at(grid,t_idx=1,fill_three_phase=True)
    assert not len(PositiveSequenceControl(offline,np.arange(8)).q)
    assert not np.any(offline.shunt_data.Y3_star)


def test_shunt_and_generator_share_one_u1_constraint() -> None:
    """Colocated continuous controllers must not introduce duplicate constraints."""
    grid: vge.MultiCircuit = make_grid(100.0,ShuntConnectionType.Delta)
    grid.add_controllable_shunt(grid.buses[1],vge.ControllableShunt(vset=1.01,Bmin=-10,Bmax=20))
    grid.add_generator(grid.buses[1],vge.Generator(P=4.0,vset=1.01,Qmin=-5,Qmax=15,
                                                r0=0.1,x0=0.1,r2=0.1,x2=0.1))
    result: vge.PowerFlowResults3Ph = solve(grid)
    voltage: np.ndarray = np.array((result.voltage_A[1],result.voltage_B[1],result.voltage_C[1]))
    a: complex = np.exp(2j*np.pi/3)
    assert abs(abs(voltage@np.array((1,a,a*a))/3)-1.01) < 1e-8
    nc: NumericalCircuit = compile_numerical_circuit_at(grid,fill_three_phase=True)
    assert len(PositiveSequenceControl(nc,np.arange(8)).q) == 1


def test_dgs_svs_preserves_phase_to_phase_connection() -> None:
    """The native SVS susceptances connect AB/BC/CA, even in balanced-control mode."""
    source: ElmSvs = ElmSvs()
    source.ID,source.loc_name,source.i_ctrl,source.i_droop = 'svc','SVC',1,0
    source.qmin,source.qmax,source.usetp = -10.0,20.0,1.01
    bus: vge.Bus = vge.Bus()
    _,shunt = convert_dgs_to_controllable_shunt_from_svs(source,dict((('svc',list((0,))),)),
        list((bus,)),vge.Logger(),dict(),dict())
    assert shunt.conn == ShuntConnectionType.Delta
    assert shunt.Vset == 1.01
    assert (shunt.Bmin,shunt.Bmax) == (-10.0,20.0)
    source.qmin,source.nxcap,source.tcrmax = -0.09,132,2.5
    _,shunt = convert_dgs_to_controllable_shunt_from_svs(source,dict((('svc',list((0,))),)),
        list((bus,)),vge.Logger(),dict(),dict())
    np.testing.assert_allclose((shunt.Bmin,shunt.Bmax),(-11.88,2.5))


def test_continuous_shunt_at_slack_retains_fixed_admittance() -> None:
    """An ideal slack retains voltage control without an extra singular U1 equation."""
    grid: vge.MultiCircuit = make_grid(100.0,ShuntConnectionType.Delta)
    grid.controllable_shunts[0].bus = grid.buses[0]
    nc: NumericalCircuit = compile_numerical_circuit_at(grid,fill_three_phase=True)
    assert not len(PositiveSequenceControl(nc,np.arange(8)).q)
    matrix: np.ndarray = nc.shunt_data.Y3_star[1:4,1:4]
    rotation: np.ndarray = np.exp(-2j*np.pi/3*np.arange(3))
    np.testing.assert_allclose(matrix@rotation,(0.4+8j)*rotation/3,atol=1e-12)
    assert solve(grid).converged
