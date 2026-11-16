"""Check SC derivatives against the complete residual, independent of sparsity."""

from pathlib import Path

import numpy as np
import pytest

import VeraGridEngine.api as vge
from VeraGridEngine.enumerations import (ConverterControlType, ConverterFaultControlType,
                                        GeneratorControlMode, GeneratorType, HvdcControlType,
                                        MethodShortCircuit)
from VeraGridEngine.Simulations.PowerFlow.Formulations.pf_full_acdc_with_negative_poles_sc import (
    PfAcDcWithNegativePolesSc,
)
from VeraGridEngine.Utils.Sparse.csc2 import mat_to_scipy


def _small_problem(bipolar=False, asynchronous=False, hvdc=False):
    """Three distinct terminal laws, with nonidentity original-device indices."""
    grid = vge.MultiCircuit()
    slack = vge.Bus(name="Slack", Vnom=110.0, is_slack=True)
    grid.add_bus(slack)
    ac_buses = []
    for i in range(3):
        bus = vge.Bus(name=f"AC {i}", Vnom=110.0)
        grid.add_bus(bus)
        ac_buses.append(bus)
        grid.add_line(vge.Line(bus_from=slack, bus_to=bus, r=0.02, x=0.15, b=0.01))
        dc = vge.Bus(name=f"DC {i}", Vnom=110.0, is_dc=True,
                     is_slack=not (bipolar and i == 2))
        grid.add_bus(dc)
        negative = None
        if bipolar and i == 2:
            negative = vge.Bus(name="Negative pole", Vnom=110.0, is_dc=True,
                               Vm0=0.9, Va0=np.pi)
            grid.add_bus(negative)
        grid.add_vsc(vge.VSC(name=f"VSC {i}", bus_from=dc, bus_to=bus,
                             bus_dc_n=negative, rate=100.0,
                             alpha1=0.001, alpha2=0.002, alpha3=0.003,
                             control1=ConverterControlType.Fault1,
                             control2=ConverterControlType.Fault2,
                             fault_control=(ConverterFaultControlType.Standard if i == 1 else
                                            ConverterFaultControlType.WECC_WT_Type_4B)))
    if asynchronous:
        grid.add_generator(ac_buses[0], vge.Generator(
            name="Induction generator", P=1.0, Snom=10.0,
            control_mode=GeneratorControlMode.Q, tpe=GeneratorType.Asynchronous,
            Rs=0.01, Xs=0.1, Xm=3.0, Rr=0.02, Xr=0.1))
    if hvdc:
        grid.add_hvdc(vge.HvdcLine(bus_from=ac_buses[0], bus_to=ac_buses[1],
                                   Pset=5.0, r=0.2, angle_droop=2.0,
                                   control_mode=HvdcControlType.type_0_free))
    options = vge.PowerFlowOptions(control_q=False, control_taps_modules=False,
                                    control_taps_phase=False, control_remote_voltage=False,
                                    limit_i_vsc=False, use_stored_guess=True,
                                    use_autodiff_jacobian=False)
    nc = vge.compile_numerical_circuit_at(grid, use_stored_guess=True,
                                          control_taps_modules=False,
                                          control_taps_phase=False,
                                          control_remote_voltage=False)
    # An island need not preserve the original global converter indexing.
    nc.vsc_data.original_idx[:] = [3, 0, 2]
    prefault_power = np.array([-30-4j, 0j, -60+8j, -80-10j])
    qmax, qmin = nc.get_reactive_power_limits()
    problem = PfAcDcWithNegativePolesSc(
        V0=nc.bus_data.Vbus.copy(), S0=nc.get_power_injections_pu(),
        I0=np.full(nc.nbus, 0.01+0.02j), Y0=np.full(nc.nbus, 0.03-0.01j),
        St_vsc_pf=prefault_power, Pfp_vsc_pf=np.array([30.0, 0.0, 30.0, 80.0]),
        Pfn_vsc_pf=np.array([0.0, 0.0, -30.0, 0.0]) if bipolar else np.zeros(4),
        Qmin=qmin, Qmax=qmax, nc=nc, options=options, logger=vge.Logger(),
        sc_async_gen_q_mask=np.ones(nc.generator_data.nelm, dtype=bool),
        sc_async_gen_q_prefault=np.full(nc.generator_data.nelm, -2.0))
    return problem


def _dense_difference(problem, step=1e-7, central=False):
    """Perturb every variable and retain every row; no analytic sparsity mask."""
    x = problem.var2x().copy()
    base = problem.compute_f(x).copy()
    columns = []
    for col in range(len(x)):
        changed = x.copy()
        changed[col] += step
        forward = problem.compute_f(changed).copy()
        if central:
            changed[col] -= 2.0 * step
            columns.append((forward - problem.compute_f(changed).copy()) / (2.0*step))
        else:
            columns.append((forward - base) / step)
    problem.update(x)
    return np.column_stack(columns)


def _assert_full_jacobian(problem):
    problem.update(problem.var2x())
    finite = _dense_difference(problem)
    analytic = mat_to_scipy(problem.Jacobian()).toarray()
    assert finite.shape == analytic.shape == (problem.size(), problem.size())
    np.testing.assert_allclose(analytic, finite, rtol=3e-5, atol=3e-6)


@pytest.mark.parametrize("voltage", [1.0, 0.94, 0.72, 0.25, 0.08, 1.12, 1.22])
def test_sc_jacobian_matches_dense_residual_difference(voltage):
    """Cover the deadband, current saturation, both blocking branches and VDL."""
    problem = _small_problem()
    problem.Vm[problem.nc.vsc_data.T] = voltage
    problem.Va[problem.nc.vsc_data.T] = [0.17, -0.12, 0.08]
    _assert_full_jacobian(problem)


def test_sc_jacobian_bipolar_negative_pole():
    """Only the last VSC has a negative pole, whose voltage angle is pi."""
    problem = _small_problem(bipolar=True)
    assert problem.nc.vsc_data.F[2] in problem.i_u_vm
    assert problem.nc.vsc_data.F_dcn[2] in problem.i_u_vm
    problem.Vm[problem.nc.vsc_data.T] = [0.78, 0.86, 0.91]
    _assert_full_jacobian(problem)


def test_sc_jacobian_hvdc_residual_dependencies():
    """Derivative selection must preserve the actual legacy HVDC residual."""
    problem = _small_problem(hvdc=True)
    problem.Pf_hvdc[:] = 0.06
    problem.Va[problem.nc.vsc_data.T] = [0.11, -0.04, 0.02]
    _assert_full_jacobian(problem)


@pytest.mark.parametrize("voltage", [0.1, 0.95, 1.05, 1.10, 1.15, 1.20])
def test_sc_jacobian_control_boundaries(voltage):
    """At a nonsmooth limit use the same forward derivative as the full option."""
    problem = _small_problem()
    problem.Vm[problem.nc.vsc_data.T] = voltage
    _assert_full_jacobian(problem)


def test_sc_jacobian_negative_reactive_current_limit():
    """Retain the selected WECC limiting rule for a negative reactive command."""
    problem = _small_problem()
    problem.St_vsc_pf[problem.nc.vsc_data.original_idx[2]] = -60.0+120.0j
    problem.Vm[problem.nc.vsc_data.T] = 0.25
    _assert_full_jacobian(problem)


@pytest.mark.parametrize("no_slip_solution", [False, True])
def test_sc_jacobian_asynchronous_reactive_injection(no_slip_solution):
    """Include machine Q(V) and its existing prefault-admittance fallback."""
    problem = _small_problem(asynchronous=True)
    problem.Vm[problem.nc.vsc_data.T] = [0.89, 0.87, 0.91]
    if no_slip_solution:
        problem.nc.generator_data.p[:] = 1e6
        reactive = problem._compute_sc_asynchronous_generator_q_per_bus(problem.Vm.astype(complex))
        bus = problem.nc.generator_data.bus_idx[0]
        np.testing.assert_allclose(reactive[bus], -2.0*problem.Vm[bus]**2)
    _assert_full_jacobian(problem)


def test_sc_fast_and_full_difference_solve_same_ieee14_fault(monkeypatch):
    """The derivative choice must not change the existing IEEE14 fault model."""
    path = Path(__file__).resolve().parents[1] / "data/grids/test_ieee14_external_grid.dgs"
    grid = vge.open_file(str(path), options=vge.FileOpenOptions(dgs_use_vsc_for_injections=True))
    options = vge.PowerFlowOptions(retry_with_other_methods=False, limit_i_vsc=False,
                                    control_taps_modules=False, tolerance=1e-9)
    prefault = vge.power_flow(grid, options=options)
    assert np.all(prefault.converged)
    grid.add_short_circuit_event(vge.ShortCircuitEvent(
        device=grid.buses[12], method=MethodShortCircuit.sequences_vsc,
        r_fault=10.0/(33.0**2/100.0), constz=False))
    # Check the full derivative on the real IEEE14 residual as well as the small
    # constructed network. The numerical reference does not reuse its sparsity.
    checked = []
    jacobian = PfAcDcWithNegativePolesSc.Jacobian

    def checked_jacobian(problem, *args, **kwargs):
        result = jacobian(problem, *args, **kwargs)
        if not checked:
            np.testing.assert_allclose(mat_to_scipy(result).toarray(),
                                       _dense_difference(problem, step=1e-6, central=True),
                                       rtol=3e-5, atol=3e-6)
            checked.append(True)
        return result

    monkeypatch.setattr(PfAcDcWithNegativePolesSc, "Jacobian", checked_jacobian)
    prefault_voltage = prefault.voltage.copy()
    prefault_power = prefault.St_vsc.copy()
    results = []
    for finite_difference in (False, True):
        options.use_autodiff_jacobian = finite_difference
        driver = vge.ShortCircuitDriver(grid=grid, options=vge.ShortCircuitOptions(),
                                         pf_options=options, pf_results=prefault,
                                         pf_results3ph=None)
        driver.run()
        results.append(driver.results)
    assert checked
    assert all(np.all(np.isfinite(r.voltage1)) for r in results)
    np.testing.assert_array_equal(prefault.voltage, prefault_voltage)
    np.testing.assert_array_equal(prefault.St_vsc, prefault_power)
    np.testing.assert_allclose(results[0].voltage1, results[1].voltage1, rtol=1e-8, atol=1e-9)
    np.testing.assert_allclose(results[0].vsc_St, results[1].vsc_St, rtol=1e-8, atol=1e-7)
    terminals = np.array([grid.buses.index(vsc.bus_to) for vsc in grid.vsc_devices])
    currents = [np.conj((r.vsc_St/grid.Sbase)/r.voltage1[terminals]) for r in results]
    np.testing.assert_allclose(currents[0], currents[1], rtol=1e-8, atol=1e-9)
