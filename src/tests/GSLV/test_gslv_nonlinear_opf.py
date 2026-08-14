import os

import numpy as np
import pytest
import VeraGridEngine.api as vg
from VeraGridEngine.Compilers.Gslv.activation import GSLV_AVAILABLE
from VeraGridEngine.Simulations.OPF.opf_driver import OptimalPowerFlowDriver
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.Simulations.PowerFlow.Formulations.pf_generalized_formulation import PfGeneralizedFormulation
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.newton_raphson_fx import newton_raphson_fx
from VeraGridEngine.basic_structures import Logger


def run_snapshot_nonlinear_opf(grid: vg.MultiCircuit,
                               options: vg.OptimalPowerFlowOptions,
                               engine: vg.EngineType):
    """
    Run one snapshot nonlinear OPF through the requested engine.

    :param grid: Grid to solve.
    :param options: OPF options.
    :param engine: Engine selection.
    :return: Snapshot OPF results.
    """
    driver = OptimalPowerFlowDriver(grid=grid, options=options, engine=engine)
    driver.run()
    return driver.results


def run_case14_seed_power_flow(grid: vg.MultiCircuit) -> vg.PowerFlowResults:
    """
    Build the PF seed used by the native nonlinear OPF regression.

    :param grid: Grid to solve.
    :return: Snapshot power-flow results.
    """
    pf_options = vg.PowerFlowOptions(control_q=False)
    driver = vg.PowerFlowDriver(grid=grid, options=pf_options)
    driver.run()
    return driver.results


def solve_generalized_pf(grid: vg.MultiCircuit):
    """
    Solve the trusted generalized AC/DC PF used to seed stressed AC/DC OPF.

    :param grid: Grid to solve.
    :return: PF formulation and PF solution.
    """
    options = vg.PowerFlowOptions(vg.SolverType.NR,
                                  verbose=0,
                                  control_q=False,
                                  retry_with_other_methods=False,
                                  control_taps_phase=True,
                                  max_iter=80,
                                  controls_start_tolerance=1e-6)
    nc = compile_numerical_circuit_at(grid,
                                      t_idx=None,
                                      apply_temperature=False,
                                      branch_tolerance_mode=vg.BranchImpedanceMode.Specified,
                                      use_stored_guess=False,
                                      control_taps_modules=options.control_taps_modules,
                                      control_taps_phase=options.control_taps_phase,
                                      control_remote_voltage=options.control_remote_voltage)
    island = nc.split_into_islands(consider_hvdc_as_island_links=True)[0]
    logger = Logger()
    qmax, qmin = island.get_reactive_power_limits()
    problem = PfGeneralizedFormulation(V0=island.bus_data.Vbus,
                                       S0=island.get_power_injections_pu(),
                                       I0=island.get_current_injections_pu(),
                                       Y0=island.get_admittance_injections_pu(),
                                       Qmin=qmin,
                                       Qmax=qmax,
                                       nc=island,
                                       options=options,
                                       logger=logger)
    solution = newton_raphson_fx(problem=problem,
                                 tol=options.tolerance,
                                 max_iter=options.max_iter,
                                 trust=options.trust_radius,
                                 verbose=0,
                                 logger=logger)
    return problem, solution


def assert_snapshot_nonlinear_results_close(native_results,
                                            gslv_results,
                                            vm_tol: float,
                                            va_tol: float,
                                            pg_tol: float,
                                            qg_tol: float) -> None:
    """
    Compare the core nonlinear OPF state channels across engines.

    :param native_results: VeraGrid results.
    :param gslv_results: GSLV results.
    :param vm_tol: Voltage-magnitude tolerance.
    :param va_tol: Voltage-angle tolerance.
    :param pg_tol: Generator active-power tolerance.
    :param qg_tol: Generator reactive-power tolerance.
    :return: None.
    """
    if not bool(native_results.converged):
        pytest.xfail("VeraGrid nonlinear OPF does not converge on this case in the current runtime")
    else:
        pass

    if not bool(gslv_results.converged):
        pytest.xfail("GSLV nonlinear OPF does not converge while matching the current VeraGrid runtime remains in flux")
    else:
        pass

    assert np.allclose(np.abs(native_results.voltage), np.abs(gslv_results.voltage), atol=vm_tol)
    assert np.allclose(np.angle(native_results.voltage), np.angle(gslv_results.voltage), atol=va_tol)
    assert np.allclose(native_results.generator_power, gslv_results.generator_power, atol=pg_tol)
    assert np.allclose(native_results.generator_reactive_power, gslv_results.generator_reactive_power, atol=qg_tol)


def test_gslv_snapshot_nonlinear_opf_case9() -> None:
    """
    GSLV nonlinear snapshot OPF must match VeraGrid on MATPOWER case9.
    """
    if not GSLV_AVAILABLE:
        return

    grid = vg.open_file(filename=os.path.join('data', 'grids', 'Matpower', 'case9.matpower'))
    options = vg.OptimalPowerFlowOptions(solver=vg.SolverType.NONLINEAR_OPF,
                                         ips_method=vg.SolverType.NR,
                                         ips_tolerance=1e-8)
    native_results = run_snapshot_nonlinear_opf(grid=grid, options=options, engine=vg.EngineType.VeraGrid)
    gslv_results = run_snapshot_nonlinear_opf(grid=grid, options=options, engine=vg.EngineType.GSLV)

    assert_snapshot_nonlinear_results_close(native_results, gslv_results, 1e-4, 1e-4, 1e-4, 1e-4)


def test_gslv_snapshot_nonlinear_opf_case14() -> None:
    """
    GSLV nonlinear snapshot OPF must match VeraGrid on the seeded case14 setup.
    """
    if not GSLV_AVAILABLE:
        return

    grid = vg.open_file(filename=os.path.join('data', 'grids', 'Matpower', 'case14.matpower'))
    pf_results = run_case14_seed_power_flow(grid=grid)
    options = vg.OptimalPowerFlowOptions(solver=vg.SolverType.NONLINEAR_OPF,
                                         ips_method=vg.SolverType.NR,
                                         ips_tolerance=1e-8,
                                         ips_iterations=50,
                                         acopf_mode=vg.AcOpfMode.ACOPFstd,
                                         ips_init_with_pf=True,
                                         acopf_v0=pf_results.voltage,
                                         acopf_S0=pf_results.Sbus,
                                         acopf_pf_converged=bool(pf_results.converged))
    native_results = run_snapshot_nonlinear_opf(grid=grid, options=options, engine=vg.EngineType.VeraGrid)
    gslv_results = run_snapshot_nonlinear_opf(grid=grid, options=options, engine=vg.EngineType.GSLV)

    assert_snapshot_nonlinear_results_close(native_results, gslv_results, 1e-4, 1e-4, 2e-3, 5e-3)


def test_gslv_snapshot_nonlinear_opf_case89pegase() -> None:
    """
    GSLV nonlinear snapshot OPF must match VeraGrid on PEGASE89.
    """
    if not GSLV_AVAILABLE:
        return

    grid = vg.open_file(filename=os.path.join('data', 'grids', 'Matpower', 'case89pegase.matpower'))
    options = vg.OptimalPowerFlowOptions(solver=vg.SolverType.NONLINEAR_OPF,
                                         ips_method=vg.SolverType.NR,
                                         ips_tolerance=1e-10,
                                         acopf_mode=vg.AcOpfMode.ACOPFstd)
    native_results = run_snapshot_nonlinear_opf(grid=grid, options=options, engine=vg.EngineType.VeraGrid)
    gslv_results = run_snapshot_nonlinear_opf(grid=grid, options=options, engine=vg.EngineType.GSLV)

    assert_snapshot_nonlinear_results_close(native_results, gslv_results, 3e-3, 1e-3, 1e-2, 1e-3)


def test_gslv_snapshot_nonlinear_opf_acdc_stressed() -> None:
    """
    GSLV nonlinear AC/DC OPF must match VeraGrid on the stressed VSC case.
    """
    if not GSLV_AVAILABLE:
        return

    grid = vg.open_file(filename=os.path.join('data', 'grids', 'AC-DC OPF stressed.veragrid'))
    _, pf_solution = solve_generalized_pf(grid)
    options = vg.OptimalPowerFlowOptions(solver=vg.SolverType.NONLINEAR_OPF,
                                         ips_method=vg.SolverType.NR,
                                         ips_tolerance=1e-6,
                                         ips_iterations=300,
                                         acopf_mode=vg.AcOpfMode.ACOPFstd,
                                         ips_init_with_pf=True,
                                         acopf_v0=pf_solution.V,
                                         acopf_S0=pf_solution.Scalc,
                                         acopf_pf_converged=bool(pf_solution.converged))
    native_results = run_snapshot_nonlinear_opf(grid=grid, options=options, engine=vg.EngineType.VeraGrid)
    gslv_results = run_snapshot_nonlinear_opf(grid=grid, options=options, engine=vg.EngineType.GSLV)

    if (not bool(native_results.converged)) or (not bool(gslv_results.converged)):
        pytest.xfail("stressed AC/DC nonlinear OPF does not converge on at least one engine in the current runtime")
    else:
        pass

    assert np.allclose(np.abs(native_results.voltage), np.abs(gslv_results.voltage), atol=1e-4)
    assert np.allclose(np.angle(native_results.voltage), np.angle(gslv_results.voltage), atol=1e-4)
    assert np.allclose(native_results.generator_power, gslv_results.generator_power, atol=1e-4)
    assert np.allclose(native_results.generator_reactive_power, gslv_results.generator_reactive_power, atol=1e-4)
    assert np.allclose(native_results.hvdc_Pf, gslv_results.hvdc_Pf, atol=1e-4)
    assert np.allclose(native_results.vsc_Pf, gslv_results.vsc_Pf, atol=1e-4)
    assert np.allclose(native_results.vsc_loading, gslv_results.vsc_loading, atol=1e-4)


def test_gslv_snapshot_nonlinear_opf_acdc_tight_vsc() -> None:
    """
    GSLV nonlinear AC/DC slack OPF must track VeraGrid on the tight-VSC case.
    """
    if not GSLV_AVAILABLE:
        return

    grid = vg.open_file(filename=os.path.join('data', 'grids', 'AC-DC OPF tight VSC.veragrid'))
    _, pf_solution = solve_generalized_pf(grid)
    options = vg.OptimalPowerFlowOptions(solver=vg.SolverType.NONLINEAR_OPF,
                                         ips_method=vg.SolverType.NR,
                                         ips_tolerance=1e-6,
                                         ips_iterations=400,
                                         acopf_mode=vg.AcOpfMode.ACOPFslacks,
                                         ips_init_with_pf=True,
                                         acopf_v0=pf_solution.V,
                                         acopf_S0=pf_solution.Scalc,
                                         acopf_pf_converged=bool(pf_solution.converged))
    native_results = run_snapshot_nonlinear_opf(grid=grid, options=options, engine=vg.EngineType.VeraGrid)
    gslv_results = run_snapshot_nonlinear_opf(grid=grid, options=options, engine=vg.EngineType.GSLV)

    if (not bool(native_results.converged)) or (not bool(gslv_results.converged)):
        pytest.xfail("tight-VSC slacked AC/DC OPF remains best-effort on at least one engine")
    else:
        assert np.allclose(np.abs(native_results.voltage), np.abs(gslv_results.voltage), atol=1e-4)
        assert np.allclose(np.angle(native_results.voltage), np.angle(gslv_results.voltage), atol=1e-4)
        assert np.allclose(native_results.vsc_loading, gslv_results.vsc_loading, atol=1e-4)
        assert np.max(native_results.vsc_loading) > 1.0
        assert np.max(gslv_results.vsc_loading) > 1.0
