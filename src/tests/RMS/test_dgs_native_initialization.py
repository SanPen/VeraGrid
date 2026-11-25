# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Native AVR projection and rectangular Newton correction accuracy."""
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import VeraGridEngine.api as gce
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.IO.dgs.dgs_to_veragrid import dgs_to_circuit
from VeraGridEngine.enumerations import DynamicSimulationMode, RmsInitializationMethod, DynamicIntegrationMethod
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import BackEulerImplicitIntegration
from VeraGridEngine.Simulations.Rms.initialization_rms import (
    project_initial_algebraic_state, solve_rms_newton_correction,
)


def test_rectangular_correction_retains_small_constraints_and_minimum_norm():
    matrix=sp.csc_matrix([[1e-8,0.,0.,0.],[0.,1.,1.,0.],[0.,0.,0.,1e8]])
    residual=-np.array([1e-8,2.,3e8])
    correction=solve_rms_newton_correction(matrix,residual,reference_column=None)
    np.testing.assert_allclose(correction,[1.,1.,1.,3.],rtol=1e-10,atol=1e-10)


def _check_native_avr_initialization(path: Path) -> dict:
    """Open a native AVR export, project its RMS initial point and take one 1 ms Backward Euler step.

    :param path: Native DGS export.
    :return: Load flow, projection and first-step diagnostics.
    """
    grid = dgs_to_circuit(str(path), use_dynamic_information=True,
                          dynamic_simulation_mode=DynamicSimulationMode.RMS)
    # Initialize phase angles for the fixture's 150-degree transformer clocks.
    pf = gce.power_flow(grid, options=PowerFlowOptions(initialize_angles=True))
    report = {'file': str(path), 'frequency_hz': grid.fBase, 'load_flow_converged': bool(pf.converged)}
    if not pf.converged:
        return report
    else:
        pass
    options = RmsOptions(time_step=.001, simulation_time=.001,
                         integration_method=DynamicIntegrationMethod.DaeBackEuler,
                         initialization_method=RmsInitializationMethod.Explicit, verbose=0)
    problem = RmsProblemDae(grid=grid, options=options, pf_results=pf)
    problem.set_events_group(RmsEventsGroup(name='Native AVR initialization check'))
    initial = problem.get_x0()
    differential = np.zeros(problem.get_diff_var_number())
    report.update(initial_finite=bool(np.isfinite(initial).all()), initial_vector_size=len(initial))
    projected, converged, residual = project_initial_algebraic_state(
        problem=problem, initial_values=initial, differential_values=differential,
        tolerance=1e-6, max_iter=100)
    residuals = problem.rhs_algebraic(projected, differential)
    report.update(projection_converged=bool(converged), projection_residual=float(residual))
    report['largest_residuals'] = [
        {'index': int(index), 'residual': float(residuals[index]),
         'equation': str(problem._algebraic_eqs[index])}
        for index in np.argsort(abs(residuals))[-8:]]
    if converged:
        solver = BackEulerImplicitIntegration(problem=problem, t0=0., t_end=.001, h=.001,
                                              max_iter=100, tolerance=1e-6)
        times, values, initialized, step_converged = solver.simulate()
        report['first_step'] = {'initialized': bool(initialized), 'converged': bool(step_converged),
                                'finite': bool(np.isfinite(values).all()), 'samples': len(times)}
    else:
        pass
    return report


def test_native_avr_initialization_projection_converges():
    root=Path(__file__).resolve().parents[3]
    result=_check_native_avr_initialization(root/'src/tests/data/grids/DGS/native_options_pf2024/nine_bus_avr_pss.dgs')
    assert result['load_flow_converged'] and result['initial_finite']
    assert result['projection_converged'],result['largest_residuals']
    assert result['projection_residual']<1e-6

    assert result['first_step']=={'initialized':True,'converged':True,'finite':True,'samples':2}
