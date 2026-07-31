# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""
Regression tests for phase shifters in the linear (PTDF) power flow.

``LinearAnalysis.get_flows`` used to be ``PTDF @ Sbus`` plus the HVDC and VSC terms, with no
phase-shift contribution at all, so the PTDF flows were blind to any phase shifter.

A phase shift enters the DC model as ``Pf = b · (theta_f - theta_t - tau)``, which is the
convention of ``power_flow_post_process_linear`` and of the AC admittance model. The linear power
flow must therefore agree with the linear (DC) power flow for any tap angle.
"""
import os
import numpy as np
import VeraGridEngine.api as gce

GRID = os.path.join('data', 'grids', 'IEEE39_trafo.gridcal')
ANGLES = (0.0, 0.05, 0.20, -0.10)


def build_grid_with_shift(angle: float) -> tuple:
    """
    Open the test grid and impose a fixed phase shift on its phase shifting transformer.

    :param angle: tap phase in radians
    :return: (grid, branch index of the shifter)
    """
    grid = gce.FileOpen(GRID).open()
    tr = grid.transformers2w[0]
    tr.tap_phase_control_mode = gce.TapPhaseControl.fixed
    tr.tap_phase = angle

    names = list(grid.get_branch_names(add_hvdc=False, add_vsc=False, add_switch=True))
    return grid, names.index(tr.name)


def test_linear_power_flow_reacts_to_the_phase_shift() -> None:
    """
    The PTDF flows must change when the tap angle changes, otherwise the shifter is not modelled.
    """
    flows = list()
    for angle in ANGLES:
        grid, k = build_grid_with_shift(angle)
        drv = gce.LinearAnalysisDriver(grid=grid, options=gce.LinearAnalysisOptions())
        drv.run()
        flows.append(float(np.asarray(drv.results.Sf).real[k]))

    # every angle must give its own flow, so no two of them may coincide
    assert len(set(np.round(flows, 6))) == len(ANGLES)


def test_linear_power_flow_matches_the_dc_power_flow() -> None:
    """
    The PTDF flows must agree with the linear (DC) power flow for every tap angle, on every branch.
    That equality is what pins the sign convention of the shift.
    """
    for angle in ANGLES:
        grid, _k = build_grid_with_shift(angle)

        lin = gce.LinearAnalysisDriver(grid=grid, options=gce.LinearAnalysisOptions())
        lin.run()

        pf = gce.PowerFlowDriver(grid=grid,
                                 options=gce.PowerFlowOptions(gce.SolverType.Linear, verbose=0))
        pf.run()

        lin_sf = np.asarray(lin.results.Sf).real
        pf_sf = np.asarray(pf.results.Sf).real

        assert np.allclose(lin_sf, pf_sf, atol=1e-6), f"mismatch at tap angle {angle} rad"


def test_zero_phase_shift_is_neutral() -> None:
    """
    A grid whose shifter sits at zero must give exactly the flows of a grid with the shift removed,
    so the correction cannot perturb the far more common no-shifter case.
    """
    grid_zero, _ = build_grid_with_shift(0.0)
    drv_zero = gce.LinearAnalysisDriver(grid=grid_zero, options=gce.LinearAnalysisOptions())
    drv_zero.run()

    grid_plain = gce.FileOpen(GRID).open()
    grid_plain.transformers2w[0].tap_phase = 0.0
    drv_plain = gce.LinearAnalysisDriver(grid=grid_plain, options=gce.LinearAnalysisOptions())
    drv_plain.run()

    assert np.allclose(np.asarray(drv_zero.results.Sf).real,
                       np.asarray(drv_plain.results.Sf).real, atol=1e-9)
