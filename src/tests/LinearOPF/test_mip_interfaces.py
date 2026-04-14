# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import numpy as np
import VeraGridEngine.api as vg


def test_issue_372_1():
    """
    https://github.com/SanPen/VeraGrid/issues/372#issuecomment-2823645586

    Using the grid IEEE14 - ntc areas_voltages_hvdc_shifter_l10free.gridcal

    Test:

        Given a base situation (simulated with a linear power flow)
        We define the exchange from A1->A2
        Run the NTC optimization

    Run options:

        No contingencies
        HVDC mode: Pset
        Phase shifter (branch 8): tap_phase_control_mode: fixed.
        All generators enable_dispatch = True
        Exchange sensitivity criteria: use alpha = 5%

    Metrics:

        ΔP in A1 optimized > 0 (because there are no base overloads)
        ΔP in A2 optimized < 0 (because there are no base overloads)
        ΔP in A1 == − ΔP in A2
        The summation of flow increments in the inter-area branches must be ΔP in A1.
        Monitored & selected by the exchange sensitivity criteria branches must not be overloaded beyond 100%

    """
    # fname = os.path.join('data', 'grids', 'ntc_test.gridcal')
    fname = os.path.join('data', 'grids', 'IEEE14 - ntc areas_voltages_hvdc_shifter_l10free.gridcal')

    grid = vg.open_file(fname)

    for mip_framework in [
        vg.MIPFramework.PuLP,
        vg.MIPFramework.OrTools
    ]:
        # Phase shifter (branch 8): tap_phase_control_mode: fixed.
        grid.transformers2w[6].tap_phase_control_mode = vg.TapPhaseControl.fixed

        info = grid.get_inter_aggregation_info(objects_from=[grid.areas[0]],
                                               objects_to=[grid.areas[1]])

        opf_options = vg.OptimalPowerFlowOptions(
            consider_contingencies=False,
            mip_framework=mip_framework,
            mip_solver=vg.MIPSolvers.HIGHS,
        )

        lin_options = vg.LinearAnalysisOptions()

        ntc_options = vg.OptimalNetTransferCapacityOptions(
            sending_bus_idx=info.idx_bus_from,
            receiving_bus_idx=info.idx_bus_to,
            transfer_method=vg.AvailableTransferMode.InstalledPower,
            loading_threshold_to_report=98.0,
            skip_generation_limits=True,
            transmission_reliability_margin=0.1,
            branch_exchange_sensitivity=0.05,
            use_branch_exchange_sensitivity=True,
            branch_rating_contribution=1.0,
            monitor_only_ntc_load_rule_branches=True,
            consider_contingencies=False,
            opf_options=opf_options,
            lin_options=lin_options
        )

        drv = vg.OptimalNetTransferCapacityDriver(grid, ntc_options)

        drv.run()

        res = drv.results

        bus_area_indices = grid.get_bus_area_indices()
        a1 = np.where(bus_area_indices == 0)[0]
        a2 = np.where(bus_area_indices == 1)[0]

        # List of (branch index, branch object, flow sense w.r.t the area exchange)
        inter_info = grid.get_inter_areas_branches(a1=[grid.areas[0]], a2=[grid.areas[1]])
        inter_area_branch_idx = [x[0] for x in inter_info]
        inter_area_branch_sense = [x[2] for x in inter_info]
        inter_info_hvdc = grid.get_inter_areas_hvdc_branches(a1=[grid.areas[0]], a2=[grid.areas[1]])
        inter_area_hvdc_idx = [x[0] for x in inter_info_hvdc]
        inter_area_hvdc_sense = [x[2] for x in inter_info_hvdc]
        inter_area_flows = np.sum(res.Sf[inter_area_branch_idx].real * inter_area_branch_sense)
        inter_area_flows += np.sum(res.hvdc_Pf[inter_area_hvdc_idx] * inter_area_hvdc_sense)

        print("Nodal balance:", res.nodal_balance.sum())
        print("A1:", res.dSbus[a1].sum())
        print("A2:", -res.dSbus[a2].sum())
        print("Inter area flows:", inter_area_flows)

        assert res.converged[0]
        assert abs(res.nodal_balance.sum()) < 1e-8

        # ΔP in A1 optimized > 0 (because there are no base overloads)
        assert res.dSbus[a1].sum() > 0

        # ΔP in A2 optimized < 0 (because there are no base overloads)
        assert res.dSbus[a2].sum() < 0

        # ΔP in A1 == − ΔP in A2
        assert np.isclose(res.dSbus[a1].sum(), -res.dSbus[a2].sum(), atol=1e-6)

        assert np.isclose(res.Sbus[a1].sum(), inter_area_flows, atol=1e-6)
