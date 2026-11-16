# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
import pytest
from pathlib import Path
from scipy.sparse import csc_matrix
import VeraGridEngine.api as gce
from VeraGridEngine.enumerations import StaticGeneratorControlMode
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Simulations.PowerFlow3ph.Formulations.pf_basic_formulation_3ph import (PfBasicFormulation3Ph,
    PowerFlowOptions, expand3ph, expandVoltage3ph, compute_current_loads,
    compute_current_load_derivatives, compute_power_loads, compute_power_load_derivatives,
    dIbus_dV_numba_sparse_csc)
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from tests.ThreePhasePowerFlow.test_3ph_pf_driver import ieee_13_bus_feeder_driver


def test_3ph_jacobian_common_mode_reference():
    """Compare the replaced mean-voltage rows on an ungrounded DGS case."""
    path: Path = Path(__file__).parent.parent / 'data/grids/DGS/DDconnection_non_auto_phasesAB.dgs'
    grid: gce.MultiCircuit = gce.open_file(str(path))
    nc = compile_numerical_circuit_at(circuit=grid, t_idx=None, fill_three_phase=True)
    qmax, qmin = nc.get_reactive_power_limits()
    voltage: np.ndarray = expandVoltage3ph(nc.bus_data.Vbus)
    problem = PfBasicFormulation3Ph(
        V0=voltage, S0=expand3ph(nc.get_power_injections_pu()),
        Qmin=qmin, Qmax=qmax, nc=nc, options=PowerFlowOptions(), logger=Logger())
    assert len(problem.common_mode.phases) > 0
    problem.Vm[problem.idx_dVm] *= 1.01
    problem.update(problem.var2x(), update_controls=False)
    assert np.allclose(problem.Jacobian(False).toarray(),
                       problem.Jacobian(True).toarray(), atol=1e-6)


def test_current_load_directional_derivative():
    """Compare the copied load cases with a directional residual difference."""
    bus_idx: np.ndarray = np.array([0], dtype=np.int32)
    bus_lookup: np.ndarray = np.arange(4, dtype=np.int32)
    voltage: np.ndarray = np.array([0.02 + 0.01j, 1.02 + 0.03j,
                                   -0.48 - 0.88j, -0.49 + 0.86j])
    change: np.ndarray = np.array([0.01 - 0.02j, -0.03 + 0.01j,
                                   0.02 + 0.03j, -0.01 - 0.02j])
    zero: np.ndarray = np.zeros(4, dtype=np.complex128)
    star: np.ndarray = np.array([0j, 0.3 + 0.1j, 0.2 + 0.05j, 0.1 + 0.02j])
    neutral_star: np.ndarray = star.copy()
    neutral_star[0] = 1.0
    delta: np.ndarray = star.copy()
    step: float = 1e-6

    for star_parameters, delta_parameters in ((star, zero), (neutral_star, zero), (zero, delta)):
        base, _, _ = compute_current_loads(
            bus_idx, bus_lookup, voltage, star_parameters, delta_parameters, zero)
        changed, _, _ = compute_current_loads(
            bus_idx, bus_lookup, voltage + step * change, star_parameters, delta_parameters, zero)
        derivative: np.ndarray = compute_current_load_derivatives(
            bus_idx, bus_lookup, voltage, change, star_parameters, delta_parameters, zero)
        assert np.allclose((changed - base) / step, derivative, atol=1e-7)


def test_floating_current_load_directional_derivative():
    """Compare the neutral-iteration derivative for three and two phases."""
    bus_idx: np.ndarray = np.array([0], dtype=np.int32)
    zero: np.ndarray = np.zeros(4, dtype=np.complex128)
    step: float = 1e-7
    cases: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = [
        (np.arange(4, dtype=np.int32),
         np.array([0.02 + 0.01j, 1.02 + 0.03j, -0.48 - 0.88j, -0.49 + 0.86j]),
         np.array([0.01 - 0.02j, -0.03 + 0.01j, 0.02 + 0.03j, -0.01 - 0.02j]),
         np.array([0j, 0.7 - 0.5j, 0.6 - 0.45j, 0.5 - 0.4j])),
        (np.array([-1, 0, 1, -1], dtype=np.int32),
         np.array([1.02 + 0.03j, -0.48 - 0.88j]),
         np.array([-0.03 + 0.01j, 0.02 + 0.03j]),
         np.array([0j, 0.7 - 0.5j, 0.7 - 0.5j, 0j]))]
    for bus_lookup, voltage, change, floating in cases:
        base, _, _ = compute_current_loads(bus_idx, bus_lookup, voltage, zero, zero, floating)
        changed, _, _ = compute_current_loads(bus_idx, bus_lookup, voltage + step * change,
                                              zero, zero, floating)
        derivative: np.ndarray = compute_current_load_derivatives(
            bus_idx, bus_lookup, voltage, change, zero, zero, floating)
        assert np.allclose((changed - base) / step, derivative, rtol=1e-3, atol=1e-5)


def test_unequal_two_phase_floating_currents_have_no_neutral_solution():
    """Reject a two-phase floating current load whose currents cannot balance."""
    bus_idx: np.ndarray = np.array([0], dtype=np.int32)
    bus_lookup: np.ndarray = np.array([-1, 0, 1, -1], dtype=np.int32)
    voltage: np.ndarray = np.array([1.02 + 0.03j, -0.48 - 0.88j])
    zero: np.ndarray = np.zeros(4, dtype=np.complex128)
    floating: np.ndarray = np.array([0j, 0.7 - 0.5j, 0.6 - 0.45j, 0j])
    with pytest.raises(ValueError, match='magnitudes must match'):
        compute_current_loads(bus_idx, bus_lookup, voltage, zero, zero, floating)
    with pytest.raises(ValueError, match='magnitudes must match'):
        compute_current_load_derivatives(bus_idx, bus_lookup, voltage,
                                         np.ones_like(voltage), zero, zero, floating)


def test_power_load_directional_derivative():
    """Compare the copied power-load cases with a directional difference."""
    bus_idx: np.ndarray = np.array([0], dtype=np.int32)
    bus_lookup: np.ndarray = np.arange(4, dtype=np.int32)
    voltage: np.ndarray = np.array([0.02 + 0.01j, 1.02 + 0.03j,
                                   -0.48 - 0.88j, -0.49 + 0.86j])
    change: np.ndarray = np.array([0.01 - 0.02j, -0.03 + 0.01j,
                                   0.02 + 0.03j, -0.01 - 0.02j])
    zero: np.ndarray = np.zeros(4, dtype=np.complex128)
    star: np.ndarray = np.array([0j, 0.3 + 0.1j, 0.2 + 0.05j, 0.1 + 0.02j])
    neutral_star: np.ndarray = star.copy()
    neutral_star[0] = 1.0
    delta: np.ndarray = star.copy()
    step: float = 1e-6

    for star_parameters, delta_parameters in ((star, zero), (neutral_star, zero), (zero, delta)):
        base, _, _ = compute_power_loads(
            bus_idx, bus_lookup, voltage, star_parameters, zero, delta_parameters)
        changed, _, _ = compute_power_loads(
            bus_idx, bus_lookup, voltage + step * change, star_parameters, zero, delta_parameters)
        derivative: np.ndarray = compute_power_load_derivatives(
            bus_idx, bus_lookup, voltage, change, star_parameters, zero, delta_parameters)
        assert np.allclose((changed - base) / step, derivative, atol=1e-7)


def test_floating_power_load_directional_derivative():
    """Compare floating-power derivatives with the selected neutral root."""
    bus_idx: np.ndarray = np.array([0], dtype=np.int32)
    zero: np.ndarray = np.zeros(4, dtype=np.complex128)
    step: float = 1e-7
    cases: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = [
        (np.arange(4, dtype=np.int32),
         np.array([0.02 + 0.01j, 1.02 + 0.03j, -0.48 - 0.88j, -0.49 + 0.86j]),
         np.array([0.01 - 0.02j, -0.03 + 0.01j, 0.02 + 0.03j, -0.01 - 0.02j]),
         np.array([0j, 0.7 + 0.5j, 0.6 + 0.45j, 0.5 + 0.4j])),
        (np.array([-1, 0, 1, -1], dtype=np.int32),
         np.array([1.02 + 0.03j, -0.48 - 0.88j]),
         np.array([-0.03 + 0.01j, 0.02 + 0.03j]),
         np.array([0j, 0.7 + 0.5j, 0.6 + 0.45j, 0j]))]
    for bus_lookup, voltage, change, floating in cases:
        base, _, _ = compute_power_loads(bus_idx, bus_lookup, voltage, zero, floating, zero)
        changed, _, _ = compute_power_loads(bus_idx, bus_lookup, voltage + step * change,
                                            zero, floating, zero)
        derivative: np.ndarray = compute_power_load_derivatives(
            bus_idx, bus_lookup, voltage, change, zero, floating, zero)
        assert np.allclose((changed - base) / step, derivative, rtol=1e-5, atol=1e-6)


def test_fixed_power_current_derivative_csc():
    """Check the CSC current term against the rotated residual at a perturbed voltage."""
    ybus: csc_matrix = csc_matrix(np.array([[2 + 3j, -1j], [-1j, 1 + 2j]]))
    voltage: np.ndarray = np.array([1.03 + 0.04j, -0.48 - 0.88j])
    power: np.ndarray = np.array([0.3 + 0.2j, -0.1 + 0.05j])
    injection: np.ndarray = np.conj(power / voltage)
    empty_loads: np.ndarray = np.zeros(0, dtype=np.complex128)
    empty_sources: np.ndarray = np.zeros((1, 4, 4), dtype=np.complex128)
    d_vm, d_va = dIbus_dV_numba_sparse_csc(
        ybus.data, ybus.indptr, ybus.indices, voltage, np.abs(voltage),
        injection, injection, np.array([0, 1, -1, -1], dtype=np.int32),
        np.zeros(0, dtype=np.int32), empty_loads, empty_loads, empty_loads,
        empty_loads, empty_loads, empty_loads, empty_sources, empty_sources, 1.0)
    angle_derivative: np.ndarray = csc_matrix((d_va, ybus.indices, ybus.indptr), shape=ybus.shape).toarray()
    magnitude_derivative: np.ndarray = csc_matrix((d_vm, ybus.indices, ybus.indptr), shape=ybus.shape).toarray()
    residual: np.ndarray = (ybus @ voltage - injection) / (voltage / np.abs(voltage))
    step: float = 1e-7
    for column in range(len(voltage)):
        for is_angle in (False, True):
            changed: np.ndarray = voltage.copy()
            changed[column] = (voltage[column] * np.exp(1j * step) if is_angle else
                               voltage[column] + step * voltage[column] / abs(voltage[column]))
            changed_injection: np.ndarray = np.conj(power / changed)
            changed_residual: np.ndarray = ((ybus @ changed - changed_injection)
                                             / (changed / np.abs(changed)))
            derivative: np.ndarray = angle_derivative if is_angle else magnitude_derivative
            assert np.allclose((changed_residual - residual) / step, derivative[:, column], atol=1e-6)


def test_3ph_jacobian():
    """
    Test to check equivalence of the 3-phase analytic Jacobian VS the Autodiff one
    :return:
    """
    grid = ieee_13_bus_feeder_driver()
    nc = compile_numerical_circuit_at(circuit=grid, t_idx=None, fill_three_phase=True)

    V0: np.ndarray = expandVoltage3ph(nc.bus_data.Vbus)
    rng: np.random.Generator = np.random.default_rng(17)
    # Exercise the derivatives away from the balanced flat start; zero neutral voltages stay zero.
    V0 *= (1.0 + rng.uniform(-0.02, 0.02, V0.size)) * np.exp(1j * rng.uniform(-0.02, 0.02, V0.size))
    S0 = expand3ph(nc.get_power_injections_pu())
    Qmax, Qmin = nc.get_reactive_power_limits()
    # Qmax = expand3ph(Qmax)
    # Qmin = expand3ph(Qmin)

    options = PowerFlowOptions()
    logger = Logger()

    problem = PfBasicFormulation3Ph(
        V0=V0,
        S0=S0,
        Qmin=Qmin,
        Qmax=Qmax,
        nc=nc,
        options=options,
        logger=logger
    )
    # x = problem.var2x()
    # error, converged, _, f = problem.update(x, update_controls=False)

    J_autodiff = problem.Jacobian(autodiff=True)
    J_analytic = problem.Jacobian(autodiff=False)

    # J_autodiff2 = np.nan_to_num(J_autodiff.toarray())
    J_autodiff2 = J_autodiff.toarray()
    J_analytic2 = J_analytic.toarray()

    # The reference uses a one-sided 1e-8 step, so near-zero entries carry roundoff.
    assert np.allclose(J_autodiff2, J_analytic2, atol=1e-7)


def test_3ph_jacobian_positive_sequence_control():
    """Compare analytic U1 and limited-Q columns with the residual derivative."""
    grid = gce.MultiCircuit()
    slack = gce.Bus(name='Slack')
    slack.is_slack = True
    pv = gce.Bus(name='PV')
    grid.add_bus(obj=slack)
    grid.add_bus(obj=pv)
    grid.add_generator(bus=slack, api_obj=gce.Generator())
    grid.add_generator(bus=pv, api_obj=gce.Generator(P=5.0, control_mode=gce.GeneratorControlMode.V,
                                                      r0=0.01, x0=0.08, r2=0.02, x2=0.10))
    grid.add_battery(bus=pv, api_obj=gce.Battery(P=2.0, Q=0.4,
                                                r0=0.03, x0=0.12, r2=0.04, x2=0.15))
    grid.add_static_generator(bus=pv, api_obj=gce.StaticGenerator(P=1.0, Q=0.3))
    grid.add_static_generator(bus=pv, api_obj=gce.StaticGenerator(
        P=0.7, Q=0.2, Snom=2.0, control_mode=StaticGeneratorControlMode.QVDroop,
        vset=1.02, droop=3.0, vset_min=0.8, vset_max=1.2))
    grid.add_line(obj=gce.Line(bus_from=slack, bus_to=pv, r=0.1, x=1.0))
    nc = compile_numerical_circuit_at(circuit=grid, t_idx=None, fill_three_phase=True)
    voltage = expandVoltage3ph(nc.bus_data.Vbus)
    voltage *= 1.01 * np.exp(0.01j)
    qmax, qmin = nc.get_reactive_power_limits()
    problem = PfBasicFormulation3Ph(V0=voltage, S0=expand3ph(nc.get_power_injections_pu()),
                                   Qmin=qmin, Qmax=qmax, nc=nc,
                                   options=PowerFlowOptions(), logger=Logger())
    assert len(problem.positive_sequence.q) == 1
    assert len(problem.common_mode.phases) == 0

    for limited in (False, True):
        problem.positive_sequence.limited[0] = limited
        reference = problem.Jacobian(autodiff=True).toarray()
        analytic = problem.Jacobian(autodiff=False).toarray()
        assert np.allclose(analytic, reference, atol=1e-6)

    problem.Vm[problem.idx_dVm] *= 1.3
    problem.update(problem.var2x(), update_controls=False)
    problem.positive_sequence.limited[0] = False
    reference = problem.Jacobian(autodiff=True).toarray()
    analytic = problem.Jacobian(autodiff=False).toarray()
    assert np.allclose(analytic, reference, atol=1e-6)


def test_3ph_jacobian_floating_star_loads():
    """Check both floating-star load derivatives at a perturbed voltage."""
    grid = gce.MultiCircuit()
    slack = gce.Bus(name='Slack')
    slack.is_slack = True
    load_bus = gce.Bus(name='Floating load')
    grid.add_bus(obj=slack)
    grid.add_bus(obj=load_bus)
    grid.add_generator(bus=slack, api_obj=gce.Generator())
    grid.add_line(obj=gce.Line(bus_from=slack, bus_to=load_bus, r=0.1, x=0.4))
    power_load = gce.Load(P1=0.7, Q1=0.5, P2=0.6, Q2=0.45, P3=0.5, Q3=0.4)
    current_load = gce.Load(Ir1=0.7, Ii1=-0.5, Ir2=0.6, Ii2=-0.45, Ir3=0.5, Ii3=-0.4)
    power_load.conn = gce.ShuntConnectionType.FloatingStar
    current_load.conn = gce.ShuntConnectionType.FloatingStar
    grid.add_load(bus=load_bus, api_obj=power_load)
    grid.add_load(bus=load_bus, api_obj=current_load)
    nc = compile_numerical_circuit_at(circuit=grid, t_idx=None, fill_three_phase=True)
    voltage = expandVoltage3ph(nc.bus_data.Vbus)
    rng = np.random.default_rng(23)
    voltage *= (1.0 + rng.uniform(-0.03, 0.03, voltage.size)) * np.exp(
        1j * rng.uniform(-0.03, 0.03, voltage.size))
    qmax, qmin = nc.get_reactive_power_limits()
    problem = PfBasicFormulation3Ph(V0=voltage, S0=expand3ph(nc.get_power_injections_pu()),
                                   Qmin=qmin, Qmax=qmax, nc=nc,
                                   options=PowerFlowOptions(), logger=Logger())
    reference = problem.Jacobian(autodiff=True).toarray()
    analytic = problem.Jacobian(autodiff=False).toarray()
    assert np.allclose(analytic, reference, atol=1e-6)


def test_3ph_jacobian_asynchronous_generator():
    """Check the analytic slip sensitivity against the current residual."""
    grid = gce.MultiCircuit()
    slack = gce.Bus(name='Slack')
    slack.is_slack = True
    machine_bus = gce.Bus(name='Asynchronous machine')
    grid.add_bus(obj=slack)
    grid.add_bus(obj=machine_bus)
    grid.add_generator(bus=slack, api_obj=gce.Generator())
    grid.add_generator(bus=machine_bus, api_obj=gce.Generator(
        P=2.0, Snom=10.0, control_mode=gce.GeneratorControlMode.Q,
        tpe=gce.GeneratorType.Asynchronous, r0=0.03, x0=0.12,
        Rs=0.02, Xs=0.1, Xm=3.0, Rr=0.02, Xr=0.08))
    grid.add_line(obj=gce.Line(bus_from=slack, bus_to=machine_bus, r=0.1, x=0.4))
    nc = compile_numerical_circuit_at(circuit=grid, t_idx=None, fill_three_phase=True)
    voltage = expandVoltage3ph(nc.bus_data.Vbus)
    rng = np.random.default_rng(29)
    voltage *= (1.0 + rng.uniform(-0.02, 0.02, voltage.size)) * np.exp(
        1j * rng.uniform(-0.02, 0.02, voltage.size))
    qmax, qmin = nc.get_reactive_power_limits()
    problem = PfBasicFormulation3Ph(V0=voltage, S0=expand3ph(nc.get_power_injections_pu()),
                                   Qmin=qmin, Qmax=qmax, nc=nc,
                                   options=PowerFlowOptions(), logger=Logger())
    reference = problem.Jacobian(autodiff=True).toarray()
    analytic = problem.Jacobian(autodiff=False).toarray()
    assert np.allclose(analytic, reference, atol=1e-5)
