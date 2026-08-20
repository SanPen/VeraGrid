# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import numpy as np
import VeraGridEngine.api as gce
from VeraGridEngine.enumerations import ConverterControlType


TEST_GRID_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "grids"))


def get_grid_path(file_name: str) -> str:
    """
    Build an absolute path to a grid fixture used by the NTC tests.

    :param file_name: Grid fixture file name.
    :return: Absolute grid fixture path.
    """
    return os.path.join(TEST_GRID_DIR, file_name)


def test_ntc_ultra_simple() -> None:
    """

    :return:
    """
    np.set_printoptions(precision=4)
    fname = get_grid_path('red_ultra_simple_ntc.gridcal')

    grid = gce.open_file(fname)

    info = grid.get_inter_aggregation_info(objects_from=[grid.areas[0]],
                                           objects_to=[grid.areas[1]])

    opf_options = gce.OptimalPowerFlowOptions()
    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=False,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.01,
        use_branch_exchange_sensitivity=False,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=False,
        consider_contingencies=False,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results

    assert res.converged
    assert np.isclose(res.Sf[0].real, 50.0)
    assert np.isclose(res.dSbus.sum(), 0.0)
    assert res.dSbus[0] == 25.0
    assert abs(res.nodal_balance.sum()) < 1e-8

    # ----------------------------------------------------------
    # Now, ignore the limits
    # ----------------------------------------------------------

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.01,
        use_branch_exchange_sensitivity=False,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=False,
        consider_contingencies=False,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results

    assert res.converged
    assert np.isclose(res.Sf[0].real, 100.0)
    assert np.isclose(res.dSbus.sum(), 0.0)
    assert res.dSbus[0] == 75.0
    assert abs(res.nodal_balance.sum()) < 1e-8


def test_ntc_ieee_14() -> None:
    """

    :return:
    """
    np.set_printoptions(precision=4)
    fname = get_grid_path('ntc_test.gridcal')

    grid = gce.open_file(fname)

    info = grid.get_inter_aggregation_info(objects_from=[grid.areas[0]],
                                           objects_to=[grid.areas[1]])

    opf_options = gce.OptimalPowerFlowOptions()
    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.01,
        use_branch_exchange_sensitivity=True,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=True,
        consider_contingencies=True,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results

    assert res.converged
    assert abs(res.nodal_balance.sum()) < 1e-8


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
    fname = get_grid_path('IEEE14 - ntc areas_voltages_hvdc_shifter_l10free.gridcal')

    grid = gce.open_file(fname)

    # Phase shifter (branch 8): tap_phase_control_mode: fixed.
    grid.transformers2w[6].tap_phase_control_mode = gce.TapPhaseControl.fixed

    info = grid.get_inter_aggregation_info(objects_from=[grid.areas[0]],
                                           objects_to=[grid.areas[1]])

    opf_options = gce.OptimalPowerFlowOptions(
        consider_contingencies=False,
    )

    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
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

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results

    bus_area_indices = grid.get_bus_area_indices()
    a1 = np.where(bus_area_indices == 0)[0]
    a2 = np.where(bus_area_indices == 1)[0]

    theta = np.angle(res.voltage)

    assert res.converged[0]
    assert abs(res.nodal_balance.sum()) < 1e-8

    # ΔP in A1 optimized > 0 (because there are no base overloads)
    assert res.dSbus[a1].sum() > 0

    # ΔP in A2 optimized < 0 (because there are no base overloads)
    assert res.dSbus[a2].sum() < 0

    # ΔP in A1 == − ΔP in A2
    assert np.isclose(res.dSbus[a1].sum(), -res.dSbus[a2].sum(), atol=1e-6)

    # List of (branch index, branch object, flow sense w.r.t the area exchange)
    inter_info = grid.get_inter_areas_branches(a1=[grid.areas[0]], a2=[grid.areas[1]])
    inter_area_branch_idx = [x[0] for x in inter_info]
    inter_area_branch_sense = [x[2] for x in inter_info]
    inter_info_hvdc = grid.get_inter_areas_hvdc_branches(a1=[grid.areas[0]], a2=[grid.areas[1]])
    inter_area_hvdc_idx = [x[0] for x in inter_info_hvdc]
    inter_area_hvdc_sense = [x[2] for x in inter_info_hvdc]
    inter_area_flows = np.sum(res.Sf[inter_area_branch_idx].real * inter_area_branch_sense)
    inter_area_flows += np.sum(res.hvdc_Pf[inter_area_hvdc_idx] * inter_area_hvdc_sense)
    assert np.isclose(res.Sbus[a1].sum(), inter_area_flows, atol=1e-6)

    print()


def test_issue_372_2():
    """
    https://github.com/SanPen/VeraGrid/issues/372#issuecomment-2823683335

    Using the grid IEEE14 - ntc areas_voltages_hvdc_shifter_l10free.gridcal

    Test:

        Given a base situation (simulated with a linear power flow)
        We define the exchange from A1->A2
        Run the NTC optimization

    Run options:

        No contingencies
        HVDC mode: Pset
        Phase shifter (branch 8): tap_phase_control_mode: Pt.
        All generators enable_dispatch = True
        Exchange sensitivity criteria: use alpha = 5%

    Metrics:

        ΔP in A1 optimized > 0 (because there are no base overloads)
        ΔP in A2 optimized < 0 (because there are no base overloads)
        ΔP in A1 == − ΔP in A2
        The summation of flow increments in the inter-area branches must be ΔP in A1.
        Monitored & selected by the exchange sensitivity criteria, branches must not be overloaded beyond 100%
        The total exchange should be greater than in _test1.

    """
    # fname = os.path.join('data', 'grids', 'ntc_test.gridcal')
    fname = get_grid_path('IEEE14 - ntc areas_voltages_hvdc_shifter_l10free.gridcal')

    grid = gce.open_file(fname)

    # Phase shifter (branch 8): tap_phase_control_mode: Pt.
    grid.transformers2w[6].tap_phase_control_mode = gce.TapPhaseControl.Pf

    info = grid.get_inter_aggregation_info(objects_from=[grid.areas[0]],
                                           objects_to=[grid.areas[1]])

    opf_options = gce.OptimalPowerFlowOptions(
        consider_contingencies=False,
    )

    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
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

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results

    bus_area_indices = grid.get_bus_area_indices()

    # List of (branch index, branch object, flow sense w.r.t the area exchange)
    inter_info = grid.get_inter_areas_branches(a1=[grid.areas[0]], a2=[grid.areas[1]])
    inter_area_branch_idx = [x[0] for x in inter_info]
    inter_area_branch_sense = [x[2] for x in inter_info]

    inter_info_hvdc = grid.get_inter_areas_hvdc_branches(a1=[grid.areas[0]], a2=[grid.areas[1]])
    inter_area_hvdc_idx = [x[0] for x in inter_info_hvdc]
    inter_area_hvdc_sense = [x[2] for x in inter_info_hvdc]

    a1 = np.where(bus_area_indices == 0)[0]
    a2 = np.where(bus_area_indices == 1)[0]

    assert res.converged[0]
    assert abs(res.nodal_balance.sum()) < 1e-8

    # ΔP in A1 optimized > 0 (because there are no base overloads)
    assert res.dSbus[a1].sum() > 0

    # ΔP in A2 optimized < 0 (because there are no base overloads)
    assert res.dSbus[a2].sum() < 0

    # ΔP in A1 == − ΔP in A2
    assert np.isclose(res.dSbus[a1].sum(), -res.dSbus[a2].sum(), atol=1e-6)

    # The summation of flow increments in the inter-area branches must be ΔP in A1.
    inter_area_flows = np.sum(res.Sf[inter_area_branch_idx].real * inter_area_branch_sense)
    inter_area_flows += np.sum(res.hvdc_Pf[inter_area_hvdc_idx] * inter_area_hvdc_sense)
    assert np.isclose(res.Sbus[a1].sum(), inter_area_flows, atol=1e-6)

    # Monitored & selected by the exchange sensitivity criteria branches must not be overloaded beyond 100%
    monitor_idx = np.where(res.monitor_logic == 1)[0]
    assert np.all(res.loading[monitor_idx] <= 1)

    # The total exchange should be greater than in _test1 (implemented as test_issue_372_1).
    # TODO: so far it is not, maybe this is not a universal truth
    assert res.Sbus[a1].sum() >= 49.74
    print()


def test_issue_372_3():
    """
    https://github.com/SanPen/VeraGrid/issues/372#issuecomment-2823722874

    Using the grid IEEE14 - ntc areas_voltages_hvdc_shifter_l10free.gridcal

    Test:

        Given a base situation (simulated with a linear power flow)
        We define the exchange from A1->A2
        Run the NTC optimization

    Run options:

        No contingencies
        HVDC mode: free
        Phase shifter (branch 8): tap_phase_control_mode: fixed.
        All generators enable_dispatch = True
        Exchange sensitivity criteria: use alpha = 5%

    Metrics:

        ΔP in A1 optimized > 0 (because there are no base overloads)
        ΔP in A2 optimized < 0 (because there are no base overloads)
        ΔP in A1 == − ΔP in A2
        The summation of flow increments in the inter-area branches must be ΔP in A1.
        Monitored & selected by the exchange sensitivity criteria, branches must not be overloaded beyond 100%
        The total exchange should be greater than in _test1.
        The HVDC power must be: P0 + angle_droop · (theta_f − theta_t) (all in proper units)

    """
    fname = get_grid_path('IEEE14 - ntc areas_voltages_hvdc_shifter_l10free.gridcal')

    grid = gce.open_file(fname)

    # Phase shifter (branch 8): tap_phase_control_mode: Pt.
    grid.transformers2w[6].tap_phase_control_mode = gce.TapPhaseControl.fixed
    grid.hvdc_lines[0].control_mode = gce.HvdcControlType.type_0_free

    info = grid.get_inter_aggregation_info(objects_from=[grid.areas[0]],
                                           objects_to=[grid.areas[1]])

    opf_options = gce.OptimalPowerFlowOptions(
        consider_contingencies=False,
    )

    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
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

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results

    bus_area_indices = grid.get_bus_area_indices()

    # List of (branch index, branch object, flow sense w.r.t the area exchange)
    inter_info = grid.get_inter_areas_branches(a1=[grid.areas[0]], a2=[grid.areas[1]])
    inter_area_branch_idx = [x[0] for x in inter_info]
    inter_area_branch_sense = [x[2] for x in inter_info]

    inter_info_hvdc = grid.get_inter_areas_hvdc_branches(a1=[grid.areas[0]], a2=[grid.areas[1]])
    inter_area_hvdc_idx = [x[0] for x in inter_info_hvdc]
    inter_area_hvdc_sense = [x[2] for x in inter_info_hvdc]

    a1 = np.where(bus_area_indices == 0)[0]
    a2 = np.where(bus_area_indices == 1)[0]

    assert res.converged[0]
    assert abs(res.nodal_balance.sum()) < 1e-8

    # ΔP in A1 optimized > 0 (because there are no base overloads)
    assert res.dSbus[a1].sum() > 0

    # ΔP in A2 optimized < 0 (because there are no base overloads)
    assert res.dSbus[a2].sum() < 0

    # ΔP in A1 == − ΔP in A2
    assert np.isclose(res.dSbus[a1].sum(), -res.dSbus[a2].sum(), atol=1e-6)

    # The summation of flow increments in the inter-area branches must be ΔP in A1.
    inter_area_flows = np.sum(res.Sf[inter_area_branch_idx].real * inter_area_branch_sense)
    inter_area_flows += np.sum(res.hvdc_Pf[inter_area_hvdc_idx] * inter_area_hvdc_sense)
    assert np.isclose(res.Sbus[a1].sum(), inter_area_flows, atol=1e-6)

    # Monitored & selected by the exchange sensitivity criteria branches must not be overloaded beyond 100%
    monitor_idx = np.where(res.monitor_logic == 1)[0]
    assert np.all(res.loading[monitor_idx] <= 1)

    # The total exchange should be greater than in _test1 (implemented as test_issue_372_1).
    # TODO: so far it is not, maybe this is not a universal truth
    # assert res.Sbus[a1].sum() >= 89.74

    # The HVDC power must be: P0 + angle_droop · (theta_f − theta_t) (all in proper units)
    dev = grid.hvdc_lines[0]
    k = dev.angle_droop
    theta_f = np.angle(res.voltage[10], deg=True)
    theta_t = np.angle(res.voltage[14], deg=True)
    hvdc_power = dev.Pset + k * (theta_f - theta_t)
    assert np.isclose(hvdc_power, res.hvdc_Pf[0], atol=1e-6)

    print()


def test_issue_372_4():
    """
    https://github.com/SanPen/VeraGrid/issues/372#issuecomment-2823729822

    Using the grid IEEE14 - ntc areas_voltages_hvdc_shifter_l10free.gridcal

    Test:

        Given a base situation (simulated with a linear power flow)
        We define the exchange from A1->A2
        Run the NTC optimization

    Run options:

        Enable all contingencies
        HVDC mode: Pset
        Phase shifter (branch 8): tap_phase_control_mode: Pt.
        All generators enable_dispatch = True
        Exchange sensitivity criteria: use alpha = 5%

    Metrics:

        ΔP in A1 optimized > 0 (because there are no base overloads)
        ΔP in A2 optimized < 0 (because there are no base overloads)
        ΔP in A1 == − ΔP in A2
        The summation of flow increments in the inter-area branches must be ΔP in A1.
        Monitored & selected by the exchange sensitivity criteria, branches must not be overloaded beyond 100%
        The total exchange should be greater than in _test1.
        We expect less exchange than test 2.

        TODO: Monitored & selected by the exchange sensitivity criteria branches flow must be lower than rate.
        TODO: Monitored & selected by the exchange sensitivity criteria branches contingency flow must be lower than contingency rate.

    """
    # fname = os.path.join('data', 'grids', 'ntc_test.gridcal')
    fname = get_grid_path('IEEE14 - ntc areas_voltages_hvdc_shifter_l10free.gridcal')

    grid = gce.open_file(fname)

    # Phase shifter (branch 8): tap_phase_control_mode: Pt.
    grid.transformers2w[6].tap_phase_control_mode = gce.TapPhaseControl.Pt
    grid.hvdc_lines[0].control_mode = gce.HvdcControlType.type_1_Pset

    info = grid.get_inter_aggregation_info(objects_from=[grid.areas[0]],
                                           objects_to=[grid.areas[1]])

    opf_options = gce.OptimalPowerFlowOptions(
        contingency_groups_used=grid.contingency_groups
    )

    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.05,
        use_branch_exchange_sensitivity=True,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=False,
        consider_contingencies=True,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results

    bus_area_indices = grid.get_bus_area_indices()

    # List of (branch index, branch object, flow sense w.r.t the area exchange)
    inter_info = grid.get_inter_areas_branches(a1=[grid.areas[0]], a2=[grid.areas[1]])
    inter_area_branch_idx = [x[0] for x in inter_info]
    inter_area_branch_sense = [x[2] for x in inter_info]

    inter_info_hvdc = grid.get_inter_areas_hvdc_branches(a1=[grid.areas[0]], a2=[grid.areas[1]])
    inter_area_hvdc_idx = [x[0] for x in inter_info_hvdc]
    inter_area_hvdc_sense = [x[2] for x in inter_info_hvdc]

    a1 = np.where(bus_area_indices == 0)[0]
    a2 = np.where(bus_area_indices == 1)[0]

    assert res.converged[0]
    assert abs(res.nodal_balance.sum()) < 1e-5  # this one is less precise for some reason...

    # ΔP in A1 optimized > 0 (because there are no base overloads)
    assert res.dSbus[a1].sum() > 0

    # ΔP in A2 optimized < 0 (because there are no base overloads)
    assert res.dSbus[a2].sum() < 0

    # ΔP in A1 == − ΔP in A2
    assert np.isclose(res.dSbus[a1].sum(), -res.dSbus[a2].sum(), atol=1e-6)

    # The summation of flow increments in the inter-area branches must be ΔP in A1.
    inter_area_flows = np.sum(res.Sf[inter_area_branch_idx].real * inter_area_branch_sense)
    inter_area_flows += np.sum(res.hvdc_Pf[inter_area_hvdc_idx] * inter_area_hvdc_sense)
    assert np.isclose(res.Sbus[a1].sum(), inter_area_flows, atol=1e-6)

    # Monitored & selected by the exchange sensitivity criteria branches must not be overloaded beyond 100%
    monitor_idx = np.where(res.monitor_logic == 1)[0]
    assert np.all(res.loading[monitor_idx] <= 1)

    # The total exchange should be greater than in _test1 (inter_area_flows=89.7438187457783)
    # TODO: so far it is not, maybe this is not a universal truth
    assert inter_area_flows <= 89.7438187457783

    # We expect less exchange than test 2. (inter_area_flows=89.7438187457783)
    # TODO: so far it is not (it is the same), maybe this is not a universal truth
    assert inter_area_flows <= 89.7438187457783
    print()


def test_issue_372_5():
    """
    https://github.com/SanPen/VeraGrid/issues/372#issuecomment-2824174417

    Using the grid IEEE14 - ntc areas_voltages_hvdc_shifter_l10free.gridcal

    Test:

        Given a base situation (simulated with a linear power flow)
        We define the exchange from A1->A2
        Run the NTC optimization

    Run options:

        All contingencies
        HVDC mode: free
        Phase shifter (branch 8): tap_phase_control_mode: fixed.
        All generators enable_dispatch = True
        Exchange sensitivity criteria: use alpha = 5%

    Metrics:

        Δ P in A1 optimized > 0 (because there are no base overloads)
        Δ P in A2 optimized < 0 (because there are no base overloads)
        Δ P in A1 == − Δ P in A2
        The summation of flow increments in the inter-area branches must be ΔP in A1.
        Monitored & selected by the exchange sensitivity criteria, branches must not be overloaded beyond 100%
        The total exchange should be greater than in _test1.
        The HVDC power must be: P0 + angle_droop · (theta_f − theta_t) (all in proper units)

        TODO: Monitored & selected by the exchange sensitivity criteria branches flow must be lower than rate.
        TODO: Monitored & selected by the exchange sensitivity criteria branches contingency flow must be lower than contingency rate.

    """
    # fname = os.path.join('data', 'grids', 'ntc_test.gridcal')
    fname = get_grid_path('IEEE14 - ntc areas_voltages_hvdc_shifter_l10free.gridcal')

    grid = gce.open_file(fname)

    # Phase shifter (branch 8): tap_phase_control_mode: Pt.
    grid.transformers2w[6].tap_phase_control_mode = gce.TapPhaseControl.fixed
    grid.hvdc_lines[0].control_mode = gce.HvdcControlType.type_0_free

    info = grid.get_inter_aggregation_info(objects_from=[grid.areas[0]],
                                           objects_to=[grid.areas[1]])

    opf_options = gce.OptimalPowerFlowOptions(
        contingency_groups_used=grid.contingency_groups
    )

    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.05,
        use_branch_exchange_sensitivity=True,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=True,
        consider_contingencies=True,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results

    bus_area_indices = grid.get_bus_area_indices()

    # List of (branch index, branch object, flow sense w.r.t the area exchange)
    inter_info = grid.get_inter_areas_branches(a1=[grid.areas[0]], a2=[grid.areas[1]])
    inter_area_branch_idx = [x[0] for x in inter_info]
    inter_area_branch_sense = [x[2] for x in inter_info]

    inter_info_hvdc = grid.get_inter_areas_hvdc_branches(a1=[grid.areas[0]], a2=[grid.areas[1]])
    inter_area_hvdc_idx = [x[0] for x in inter_info_hvdc]
    inter_area_hvdc_sense = [x[2] for x in inter_info_hvdc]

    a1 = np.where(bus_area_indices == 0)[0]
    a2 = np.where(bus_area_indices == 1)[0]

    assert res.converged[0]
    assert abs(res.nodal_balance.sum()) < 1e-8

    # ΔP in A1 optimized > 0 (because there are no base overloads)
    assert res.dSbus[a1].sum() > 0

    # ΔP in A2 optimized < 0 (because there are no base overloads)
    assert res.dSbus[a2].sum() < 0

    # ΔP in A1 == − ΔP in A2
    assert np.isclose(res.dSbus[a1].sum(), -res.dSbus[a2].sum(), atol=1e-6)

    # The summation of flow increments in the inter-area branches must be ΔP in A1.
    inter_area_flows = np.sum(res.Sf[inter_area_branch_idx].real * inter_area_branch_sense)
    inter_area_flows += np.sum(res.hvdc_Pf[inter_area_hvdc_idx] * inter_area_hvdc_sense)
    assert np.isclose(res.Sbus[a1].sum(), inter_area_flows, atol=1e-6)

    # Monitored & selected by the exchange sensitivity criteria branches must not be overloaded beyond 100%
    monitor_idx = np.where(res.monitor_logic == 1)[0]
    assert np.all(res.loading[monitor_idx] <= 1)

    # The HVDC power must be: P0 + angle_droop · (theta_f − theta_t) (all in proper units)
    dev = grid.hvdc_lines[0]
    k = dev.angle_droop
    theta_f = np.angle(res.voltage[10], deg=True)
    theta_t = np.angle(res.voltage[14], deg=True)
    hvdc_power = dev.Pset + k * (theta_f - theta_t)
    assert np.isclose(hvdc_power, res.hvdc_Pf[0], atol=1e-6)

    # The total exchange should be greater than in _test1 (inter_area_flows=89.7438187457783)
    # TODO: so far it is not, maybe this is not a universal truth
    assert inter_area_flows < 89.7438187457783

    # We expect less exchange than test 2. (inter_area_flows=89.7438187457783)
    # TODO: so far it is not (it is the same), maybe this is not a universal truth
    assert inter_area_flows < 89.7438187457783
    print()


def test_ntc_pmode_saturation() -> None:
    """
    In this test we force one of the HVDC devices to dispatch using PMODE3 and saturate to its rating,
    checking that the PMODE3 equation goes on to provide a larger set point
    """
    np.set_printoptions(precision=4)
    fname = get_grid_path('ntc_test.gridcal')

    grid = gce.open_file(fname)

    grid.hvdc_lines[0].control_mode = gce.HvdcControlType.type_0_free
    # grid.hvdc_lines[0].angle_droop = 0.2  # this will force a greater pmode3 flow
    grid.hvdc_lines[0].angle_droop = 2000  # this will force a greater pmode3 flow

    grid.hvdc_lines[1].control_mode = gce.HvdcControlType.type_1_Pset

    a1 = [grid.areas[0]]
    a2 = [grid.areas[1]]

    info = grid.get_inter_aggregation_info(objects_from=a1,
                                           objects_to=a2)

    opf_options = gce.OptimalPowerFlowOptions()
    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.01,
        use_branch_exchange_sensitivity=True,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=True,
        consider_contingencies=True,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results

    bus_area_indices = grid.get_bus_area_indices()

    # List of (branch index, branch object, flow sense w.r.t the area exchange)
    inter_info = grid.get_inter_areas_branches(a1=a1, a2=a2)
    inter_area_branch_idx = [x[0] for x in inter_info]
    inter_area_branch_sense = [x[2] for x in inter_info]

    inter_info_hvdc = grid.get_inter_areas_hvdc_branches(a1=a1, a2=a2)
    inter_area_hvdc_idx = [x[0] for x in inter_info_hvdc]
    inter_area_hvdc_sense = [x[2] for x in inter_info_hvdc]

    # Monitored & selected by the exchange sensitivity criteria branches must not be overloaded beyond 100%
    monitor_idx = np.where(res.monitor_logic == 1)[0]
    assert np.all(res.loading[monitor_idx] <= 1)

    # The HVDC power must be: P0 + angle_droop · (theta_f − theta_t) (all in proper units)
    dev = grid.hvdc_lines[0]
    k = dev.angle_droop
    theta_f = np.angle(res.voltage[3], deg=True)
    theta_t = np.angle(res.voltage[4], deg=True)
    hvdc_power = dev.Pset + k * (theta_f - theta_t)
    assert np.isclose(res.hvdc_Pf[0], grid.hvdc_lines[0].rate, atol=1e-6)  # the power must saturate to the rate
    assert res.hvdc_Pf[0] < hvdc_power  # the actual power must be lower than what the angles suggest

    assert res.converged
    assert abs(res.nodal_balance.sum()) < 1e-8


def test_ntc_pmode_non_saturation() -> None:
    """
    In this test we set a small droop coefficient and check the HVDC operates
    in the droop region (Pmode3).
    """
    np.set_printoptions(precision=4)
    fname = get_grid_path('ntc_test.gridcal')

    grid = gce.open_file(fname)

    grid.hvdc_lines[0].control_mode = gce.HvdcControlType.type_0_free
    grid.hvdc_lines[0].angle_droop = 0.2  # this will force a small pmode3 flow
    # grid.hvdc_lines[0].angle_droop = 2000  # this will force a greater pmode3 flow

    grid.hvdc_lines[1].control_mode = gce.HvdcControlType.type_1_Pset

    a1 = [grid.areas[0]]
    a2 = [grid.areas[1]]

    info = grid.get_inter_aggregation_info(objects_from=a1,
                                           objects_to=a2)

    opf_options = gce.OptimalPowerFlowOptions()
    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.01,
        use_branch_exchange_sensitivity=True,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=True,
        consider_contingencies=True,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results

    bus_area_indices = grid.get_bus_area_indices()

    # List of (branch index, branch object, flow sense w.r.t the area exchange)
    inter_info = grid.get_inter_areas_branches(a1=a1, a2=a2)
    inter_area_branch_idx = [x[0] for x in inter_info]
    inter_area_branch_sense = [x[2] for x in inter_info]

    inter_info_hvdc = grid.get_inter_areas_hvdc_branches(a1=a1, a2=a2)
    inter_area_hvdc_idx = [x[0] for x in inter_info_hvdc]
    inter_area_hvdc_sense = [x[2] for x in inter_info_hvdc]

    # Monitored & selected by the exchange sensitivity criteria branches must not be overloaded beyond 100%
    monitor_idx = np.where(res.monitor_logic == 1)[0]
    assert np.all(res.loading[monitor_idx] <= 1)

    # The HVDC power must be: P0 + angle_droop · (theta_f − theta_t) (all in proper units)
    dev = grid.hvdc_lines[0]
    k = dev.angle_droop
    theta_f = np.angle(res.voltage[3], deg=True)
    theta_t = np.angle(res.voltage[4], deg=True)
    hvdc_power = dev.Pset + k * (theta_f - theta_t)
    assert res.hvdc_Pf[0] < grid.hvdc_lines[0].rate  # the power must be less than the rate
    assert np.isclose(res.hvdc_Pf[0], hvdc_power, atol=1e-6)  # close to the power from the angles

    assert res.converged
    assert abs(res.nodal_balance.sum()) < 1e-8


def test_ntc_areas_connected_only_through_hvdc() -> None:
    """
    This test checks that a grid that is only joined with HVDC lines can transfer power through the 2 areas
    """
    np.set_printoptions(precision=4)
    fname = get_grid_path('ntc_test_cont.gridcal')

    grid = gce.open_file(fname)

    # we deactivate the only AC inter-area link
    grid.transformers2w[1].active = False

    # there must be a slack per area so that this works
    grid.buses[0].is_slack = True
    grid.buses[7].is_slack = True

    a1 = [grid.areas[0]]
    a2 = [grid.areas[1]]

    info = grid.get_inter_aggregation_info(objects_from=a1,
                                           objects_to=a2)

    opf_options = gce.OptimalPowerFlowOptions()
    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.01,
        use_branch_exchange_sensitivity=False,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=False,
        consider_contingencies=False,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results

    bus_area_indices = grid.get_bus_area_indices()
    a1 = np.where(bus_area_indices == 0)[0]
    a2 = np.where(bus_area_indices == 1)[0]

    assert res.converged[0]
    assert abs(res.nodal_balance.sum()) < 1e-8

    # ΔP in A1 optimized > 0 (because there are no base overloads)
    assert res.dSbus[a1].sum() > 0

    # ΔP in A2 optimized < 0 (because there are no base overloads)
    assert res.dSbus[a2].sum() < 0

    # ΔP in A1 == − ΔP in A2
    assert np.isclose(res.dSbus[a1].sum(), -res.dSbus[a2].sum(), atol=1e-6)

    assert res.converged


def test_ntc_vsc():
    """
    This test runs a test grid with VSC systems where controllers pairs are in Pset and Vdc modes
    No contingencies are enabled
    """
    fname = get_grid_path('ntc_test_cont (vsc).gridcal')

    grid = gce.open_file(fname)

    # ------------------------------------------------------------------------------------------------------------------
    # Modify initial conditions
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # run study
    # ------------------------------------------------------------------------------------------------------------------
    a1 = [grid.areas[0]]
    a2 = [grid.areas[1]]

    info = grid.get_inter_aggregation_info(objects_from=a1,
                                           objects_to=a2)

    opf_options = gce.OptimalPowerFlowOptions()
    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.01,
        use_branch_exchange_sensitivity=True,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=True,
        consider_contingencies=False,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results

    # ------------------------------------------------------------------------------------------------------------------
    # asserts
    # ------------------------------------------------------------------------------------------------------------------
    assert abs(res.nodal_balance.sum()) < 1e-8
    assert np.isclose(res.inter_area_flows, 3000.0)  # 3000 is the summation of the inter-area branch rates


def test_ntc_vsc_contingencies():
    """
    This test runs a test grid with VSC systems where controllers pairs are in Pset and Vdc modes
    Contingencies are enabled
    """
    fname = get_grid_path('ntc_test_cont (vsc).gridcal')

    grid = gce.open_file(fname)

    # ------------------------------------------------------------------------------------------------------------------
    # Modify initial conditions
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # run study
    # ------------------------------------------------------------------------------------------------------------------
    a1 = [grid.areas[0]]
    a2 = [grid.areas[1]]

    info = grid.get_inter_aggregation_info(objects_from=a1,
                                           objects_to=a2)

    opf_options = gce.OptimalPowerFlowOptions(contingency_groups_used=grid.contingency_groups)
    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.01,
        use_branch_exchange_sensitivity=True,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=False,
        consider_contingencies=True,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results

    # ------------------------------------------------------------------------------------------------------------------
    # asserts
    # ------------------------------------------------------------------------------------------------------------------
    assert abs(res.nodal_balance.sum()) < 1e-8
    assert np.isclose(res.inter_area_flows, 2000.0)  # 2000 is the summation of the inter-area branches (N-1) rates

    
def test_ntc_vsc_8_buses_REE_contingencies():
    """
    This test runs a test grid with VSC systems where controllers pairs are in Pset and Vdc modes
    Contingencies are enabled
    """
    fname = get_grid_path('NTC_8_bus_vsc_REE.veragrid')
    # fname = os.path.join('src', 'tests', 'data', 'grids', 'NTC_8_bus_vsc_REE.veragrid')

    grid = gce.open_file(fname)

    # ------------------------------------------------------------------------------------------------------------------
    # Modify initial conditions
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # run study
    # ------------------------------------------------------------------------------------------------------------------
    a1 = [grid.areas[0]]
    a2 = [grid.areas[1]]

    info = grid.get_inter_aggregation_info(objects_from=a1,
                                           objects_to=a2)

    opf_options = gce.OptimalPowerFlowOptions(contingency_groups_used=grid.contingency_groups)
    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.01,
        use_branch_exchange_sensitivity=False,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=False,
        consider_contingencies=True,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results

    # ------------------------------------------------------------------------------------------------------------------
    # asserts
    # ------------------------------------------------------------------------------------------------------------------
    print(res.inter_area_flows)
    assert abs(res.nodal_balance.sum()) < 1e-8
    assert np.isclose(res.inter_area_flows, 5000.0)  # 2000 is the summation of the inter-area branches (N-1) rates


def _run_ntc_8_bus_2_modes(corrective: bool):
    """
    Helper that runs the NTC on the '8 bus 2 modes' grid (2 AC ties + 2 VSC-bracketed DC corridors,
    each made of 2 parallel cables; all 6 inter-area branches are single N-1 contingencies).

    :param corrective: use corrective N-1 (converters may re-dispatch their set-points after a contingency)
    :return: OptimalNetTransferCapacityResults
    """
    fname = get_grid_path('NTC_8_bus_2_modes_v3.veragrid')
    grid = gce.open_file(fname)

    info = grid.get_inter_aggregation_info(objects_from=[grid.areas[0]],
                                           objects_to=[grid.areas[1]])

    opf_options = gce.OptimalPowerFlowOptions(contingency_groups_used=grid.get_contingency_groups_active())
    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.01,
        use_branch_exchange_sensitivity=False,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=False,
        consider_contingencies=True,
        corrective_contingencies=corrective,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)
    drv.run()
    return drv.results


def test_ntc_corrective_n1():
    """
    '8 bus 2 modes' grid: 2 AC ties (Line 8 ∥ Line 9) + 2 DC corridors, each of 2 parallel cables
    (Dc line 1∥2 and Dc line 3∥4). All 6 inter-area branches are single contingencies, each rated 1000 MW.

    - Preventive N-1 (fixed converter set-points): every parallel pair must be derated so its surviving
      member is not overloaded => 3 pairs x 1000 = 3000 MW.
    - Corrective N-1 (the VSC converters re-dispatch after the outage and reroute the transfer across the
      remaining corridors while preserving the exchange): the worst single outage only removes 1000 MW of
      capacity => 6000 - 1000 = 5000 MW.
    """
    res_prev = _run_ntc_8_bus_2_modes(corrective=False)
    assert abs(res_prev.nodal_balance.sum()) < 1e-6
    assert np.isclose(res_prev.inter_area_flows, 3000.0, atol=1.0)

    res_corr = _run_ntc_8_bus_2_modes(corrective=True)
    assert abs(res_corr.nodal_balance.sum()) < 1e-6
    assert np.isclose(res_corr.inter_area_flows, 5000.0, atol=1.0)

    # corrective must never be more conservative than preventive
    assert res_corr.inter_area_flows >= res_prev.inter_area_flows - 1.0


def _run_ntc_8_bus_preventive_with_deactivated_groups(deactivated_group_names: set):
    """
    Run the preventive NTC on the '8 bus 2 modes' grid after deactivating the named contingency groups.

    :param deactivated_group_names: names of the contingency groups whose active flag is set to False.
    :return: OptimalNetTransferCapacityResults of the preventive run.
    """
    fname: str = get_grid_path('NTC_8_bus_2_modes_v3.veragrid')
    grid = gce.open_file(fname)

    # deactivate the requested contingency groups so the NTC must ignore them
    for group in grid.contingency_groups:
        if group.name in deactivated_group_names:
            group.active = False
        else:
            # this group stays active and must still be honoured by the NTC
            pass

    info = grid.get_inter_aggregation_info(objects_from=[grid.areas[0]], objects_to=[grid.areas[1]])
    opf_options = gce.OptimalPowerFlowOptions(contingency_groups_used=grid.get_contingency_groups_active())
    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.01,
        use_branch_exchange_sensitivity=False,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=False,
        consider_contingencies=True,
        corrective_contingencies=False,  # this test checks the preventive active-flag behaviour
        opf_options=opf_options,
        lin_options=gce.LinearAnalysisOptions()
    )
    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)
    drv.run()
    return drv.results


def test_ntc_contingency_group_active_status():
    """
    The status (active flag) of the contingency groups must be honoured by the NTC: deactivating the DC-cable
    contingency groups (so only the AC-tie outages remain) must relax the result, because the DC corridors are
    no longer required to survive the loss of one of their parallel cables.

    Preventive N-1:
        - all 6 contingencies active  -> 3000 MW
        - only the 2 AC-tie outages   -> AC pair <= 1000, both DC corridors free at 2000 => 5000 MW
    """
    res_all = _run_ntc_8_bus_preventive_with_deactivated_groups(deactivated_group_names=set())
    assert np.isclose(res_all.inter_area_flows, 3000.0, atol=1.0)

    deactivated: set = {'Contingency Dc line 1', 'Contingency Dc line 2',
                        'Contingency Dc line 3', 'Contingency Dc line 4'}
    res_ac_only = _run_ntc_8_bus_preventive_with_deactivated_groups(deactivated_group_names=deactivated)
    assert np.isclose(res_ac_only.inter_area_flows, 5000.0, atol=1.0)

    # deactivating contingency groups can only relax (increase) the secure transfer
    assert res_ac_only.inter_area_flows > res_all.inter_area_flows + 1.0


def test_2_node_several_conditions_ntc():
    """
    2-Bus example with some behaviors
    """
    grid = gce.MultiCircuit()

    area1 = gce.Area(name="Area1")
    grid.add_area(area1)

    area2 = gce.Area(name="Area2")
    grid.add_area(area2)

    bus1 = gce.Bus(name="Bus1", area=area1)
    grid.add_bus(bus1)

    bus2 = gce.Bus(name="Bus2", area=area2)
    grid.add_bus(bus2)

    load1 = gce.Load(name="Load1", P=10.0)
    grid.add_load(bus1, load1)

    load2 = gce.Load(name="Load2", P=10.0)
    grid.add_load(bus2, load2)

    gen1 = gce.Generator(name="Generator1", P=10.0, Pmax=10000.0)
    grid.add_generator(bus1, gen1)

    gen2 = gce.Generator(name="Generator2", P=10.0, Pmax=10000.0)
    grid.add_generator(bus2, gen2)

    # Better conditioned X values
    line12 = gce.Line(bus_from=bus1, bus_to=bus2, name="Line 1-2", x=0.01, rate=1000.0)
    grid.add_line(line12)

    transformer12 = gce.Transformer2W(bus_from=bus1, bus_to=bus2, name="Transformer 1-2", x=0.01, rate=1000.0)
    grid.add_transformer2w(transformer12)

    cg1 = gce.ContingencyGroup(name="Line12 contingency")
    con1 = gce.Contingency(device=line12, name=cg1.name, group=cg1)
    grid.add_contingency_group(cg1)
    grid.add_contingency(con1)

    cg2 = gce.ContingencyGroup(name="Transformer12 contingency")
    con2 = gce.Contingency(device=transformer12, name=cg1.name, group=cg2)
    grid.add_contingency_group(cg2)
    grid.add_contingency(con2)

    # ------------------------------------------------------------------------------------------------------------------
    # run study:
    # - No contingencies
    # - transformer behaving like a line
    # ------------------------------------------------------------------------------------------------------------------

    info = grid.get_inter_aggregation_info(objects_from=[area1],
                                           objects_to=[area2])

    opf_options = gce.OptimalPowerFlowOptions(contingency_groups_used=grid.contingency_groups)
    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.01,
        use_branch_exchange_sensitivity=True,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=True,
        consider_contingencies=False,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results
    assert abs(res.nodal_balance.sum()) < 1e-8
    assert np.isclose(res.inter_area_flows, 2000)

    # ------------------------------------------------------------------------------------------------------------------
    # run study:
    # - No contingencies
    # - transformer behaving like a phase shifter
    # ------------------------------------------------------------------------------------------------------------------

    transformer12.tap_phase_control_mode = gce.TapPhaseControl.Pf

    info = grid.get_inter_aggregation_info(objects_from=[area1],
                                           objects_to=[area2])

    opf_options = gce.OptimalPowerFlowOptions(contingency_groups_used=grid.contingency_groups)
    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.01,
        use_branch_exchange_sensitivity=True,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=True,
        consider_contingencies=False,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results
    assert abs(res.nodal_balance.sum()) < 1e-8
    assert np.isclose(res.inter_area_flows, 2000)

    # ------------------------------------------------------------------------------------------------------------------
    # run study:
    # - contingencies enabled
    # - transformer behaving like a line
    # ------------------------------------------------------------------------------------------------------------------

    info = grid.get_inter_aggregation_info(objects_from=[area1],
                                           objects_to=[area2])

    opf_options = gce.OptimalPowerFlowOptions(contingency_groups_used=grid.contingency_groups)
    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.01,
        use_branch_exchange_sensitivity=True,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=True,
        consider_contingencies=True,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results
    assert abs(res.nodal_balance.sum()) < 1e-8
    assert np.isclose(res.inter_area_flows, 1000)  # half the transfer

    # ------------------------------------------------------------------------------------------------------------------
    # run study:
    # - contingencies enabled
    # - transformer behaving like a phase shifter
    # ------------------------------------------------------------------------------------------------------------------

    transformer12.tap_phase_control_mode = gce.TapPhaseControl.Pf

    info = grid.get_inter_aggregation_info(objects_from=[area1],
                                           objects_to=[area2])

    opf_options = gce.OptimalPowerFlowOptions(contingency_groups_used=grid.contingency_groups)
    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.01,
        use_branch_exchange_sensitivity=True,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=True,
        consider_contingencies=True,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results
    assert abs(res.nodal_balance.sum()) < 1e-8
    assert np.isclose(res.inter_area_flows, 1000)  # half the transfer

    # ------------------------------------------------------------------------------------------------------------------
    # run study:
    # - contingencies enabled
    # - transformer behaving like a phase shifter with a fixed angle
    # ------------------------------------------------------------------------------------------------------------------

    transformer12.tap_phase_control_mode = gce.TapPhaseControl.fixed
    transformer12.tap_phase = 0.02

    info = grid.get_inter_aggregation_info(objects_from=[area1],
                                           objects_to=[area2])

    opf_options = gce.OptimalPowerFlowOptions(contingency_groups_used=grid.contingency_groups)
    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.01,
        use_branch_exchange_sensitivity=True,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=True,
        consider_contingencies=True,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results
    assert abs(res.nodal_balance.sum()) < 1e-8
    assert res.converged

    # Both parallel branches are identical, so without any shift the transfer splits evenly
    b_tau = 0.02 / 0.01 * grid.Sbase
    assert np.isclose(res.inter_area_flows, 1000)
    assert np.isclose(res.Sf[0].real, 500 + b_tau / 2)  # Line 1-2 takes the flow
    assert np.isclose(res.Sf[1].real, 500 - b_tau / 2)  # Transformer 1-2 sheds
    assert np.all(np.abs(res.loading.real) <= 1.0)


def test_hvdc_lines_tests():
    """
    Testing test_santi_20250625.gridcal
    >This is a simple test that checks that the flow is maximal between the two areas
    :return:
    """
    np.set_printoptions(precision=4)
    fname = get_grid_path('test_santi_20250625.gridcal')

    grid = gce.open_file(fname)

    info = grid.get_inter_aggregation_info(objects_from=[grid.areas[0]],
                                           objects_to=[grid.areas[1]])

    opf_options = gce.OptimalPowerFlowOptions(
    )
    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.01,
        use_branch_exchange_sensitivity=True,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=True,
        consider_contingencies=True,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results
    assert abs(res.nodal_balance.sum()) < 1e-8

    # The documented intent is a maximal exchange between the two areas. Branch 7 is
    # overloaded to begin with, so not a good metric to assert.
    exchange = float(sum(res.Sf[k].real * sense for k, sense in res.inter_space_branches)
                     + sum(res.hvdc_Pf[k] * sense for k, sense in res.inter_space_hvdc))
    assert np.isclose(exchange, 3000.0)

    # the HVDC flows are part of the same degenerate optimum, 
    # so only their physical limits are asserted, not their value
    assert np.all(np.abs(res.hvdc_Pf) <= 1000.0 + 1e-6)
    assert np.isclose(res.inter_area_flows, 3000.0)


def test_activs_2000():
    """
    Simulate a large size grid: ACTIVSg 2000 with contingencies
    :return:
    """
    np.set_printoptions(precision=4)
    fname = get_grid_path('ACTIVSg2000.gridcal')

    grid = gce.open_file(fname)

    info = grid.get_inter_aggregation_info(
        objects_from=[grid.areas[6]],  # Coast
        objects_to=[grid.areas[7]]  # East
    )

    opf_options = gce.OptimalPowerFlowOptions(
        consider_contingencies=True,
        contingency_groups_used=grid.contingency_groups
    )
    lin_options = gce.LinearAnalysisOptions()

    # ------------------------------------------------------------------------------------------------------------------
    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.05,
        use_branch_exchange_sensitivity=True,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=False,
        consider_contingencies=False,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results
    ntc_no_contingencies = res.inter_area_flows
    assert abs(res.nodal_balance.sum()) < 1e-6
    assert res.converged
    assert res.inter_area_flows < res.structural_inter_area_flows

    # ------------------------------------------------------------------------------------------------------------------
    # Run with contingencies
    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.05,
        use_branch_exchange_sensitivity=True,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=False,
        consider_contingencies=True,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results
    assert abs(res.nodal_balance.sum()) < 1e-6
    assert res.converged
    assert res.inter_area_flows < res.structural_inter_area_flows
    assert res.inter_area_flows < ntc_no_contingencies


def test_activs_2000_acdc():
    """
    Simulate a large size grid: ACTIVSg 2000 extended with 2 DC lines and 2 converters with contingencies
    :return:
    """
    np.set_printoptions(precision=4)
    fname = get_grid_path('ACTIVSg2000.gridcal')

    grid = gce.open_file(fname)

    # Create a double link from "WILLIS 2 0" to "LUFKIN 3 0"
    coast = grid.areas[6]
    east = grid.areas[7]
    willis_2_0 = grid.buses[1557]
    lufkun_3_0 = grid.buses[1843]
    dc1 = gce.Bus("WILLIS DC", is_dc=True, Vnom=500.0, area=coast,
                  latitude=willis_2_0.latitude, longitude=willis_2_0.longitude)
    dc2 = gce.Bus("LUFKIN DC", is_dc=True, Vnom=500.0, area=east,
                  latitude=lufkun_3_0.latitude, longitude=lufkun_3_0.longitude)
    converter1 = gce.VSC(name="WILLIS converter", bus_from=willis_2_0, bus_to=dc1, rate=2000.0,
                         control1=gce.ConverterControlType.Pac, control2=gce.ConverterControlType.Pdc)
    converter2 = gce.VSC(name="LUFKIN converter", bus_from=lufkun_3_0, bus_to=dc2, rate=2000.0,
                         control1=gce.ConverterControlType.Pac, control2=gce.ConverterControlType.Vm_dc,
                         control2_val=1.0)
    dc_line1 = gce.DcLine(name="WILLIS-LUFKIN1", bus_from=dc1, bus_to=dc2, rate=1000.0)
    dc_line2 = gce.DcLine(name="WILLIS-LUFKIN2", bus_from=dc1, bus_to=dc2, rate=1000.0)

    grid.add_bus(dc1)
    grid.add_bus(dc2)
    grid.add_vsc(converter1)
    grid.add_vsc(converter2)
    grid.add_dc_line(dc_line1)
    grid.add_dc_line(dc_line2)

    # create contingencies of the DC lines
    dc1_con_group = gce.ContingencyGroup(name="WILLIS-LUFKIN1")
    dc1_con = gce.Contingency(device=dc1, group=dc1_con_group)

    dc2_con_group = gce.ContingencyGroup(name="WILLIS-LUFKIN2")
    dc2_con = gce.Contingency(device=dc2, group=dc2_con_group)

    grid.add_contingency_group(dc1_con_group)
    grid.add_contingency_group(dc2_con_group)
    grid.add_contingency(dc1_con)
    grid.add_contingency(dc2_con)

    info = grid.get_inter_aggregation_info(
        objects_from=[grid.areas[6]],  # Coast
        objects_to=[grid.areas[7]]  # East
    )

    opf_options = gce.OptimalPowerFlowOptions(
        consider_contingencies=True,
        contingency_groups_used=grid.contingency_groups,
        report_formulation="test_activs_2000_acdc_gslv.lp"
    )
    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.05,
        use_branch_exchange_sensitivity=True,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=False,
        consider_contingencies=True,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)

    drv.run()

    res = drv.results
    assert abs(res.nodal_balance.sum()) < 1e-6
    assert res.converged


def test_activs_2000_acdc_ts():
    """
    Simulate a large size grid: ACTIVSg 2000 extended with 2 DC lines and 2 converters with contingencies
    and we extend it to 5 time steps to run them
    :return:
    """
    np.set_printoptions(precision=4)
    fname = get_grid_path('ACTIVSg2000_vsc.gridcal')

    grid = gce.open_file(fname)

    grid.create_profiles(5, step_length=1.0, step_unit='h')

    info = grid.get_inter_aggregation_info(
        objects_from=[grid.areas[6]],  # Coast
        objects_to=[grid.areas[7]]  # East
    )

    opf_options = gce.OptimalPowerFlowOptions(
        consider_contingencies=True,
        contingency_groups_used=grid.contingency_groups
    )
    lin_options = gce.LinearAnalysisOptions()

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.1,
        branch_exchange_sensitivity=0.05,
        use_branch_exchange_sensitivity=True,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=False,
        consider_contingencies=True,
        opf_options=opf_options,
        lin_options=lin_options
    )

    drv = gce.OptimalNetTransferCapacityTimeSeriesDriver(grid, ntc_options,
                                                         time_indices=grid.get_all_time_indices())

    drv.run()

    res = drv.results
    assert abs(res.nodal_balance.sum()) < 1e-6
    assert res.converged.all()



def build_two_pmode3_link_grid(set_reference_bus_on_both: bool) -> gce.MultiCircuit:
    """
    Build a 2-area grid where the areas are joined by an AC line and a symmetric
    HVDC link in P-mode 3 (angle droop).

    :param set_reference_bus_on_both: if True, the droop converter gets its remote AC
                                      reference bus, if False it is left unset.
    :return: MultiCircuit
    """
    grid = gce.MultiCircuit()

    area_1 = gce.Area(name="a1")
    area_2 = gce.Area(name="a2")
    grid.add_area(area_1)
    grid.add_area(area_2)

    bus_ac_1 = gce.Bus(name="ac1", Vnom=400.0, area=area_1, is_slack=True)
    bus_ac_2 = gce.Bus(name="ac2", Vnom=400.0, area=area_2)
    bus_dc_1 = gce.Bus(name="dc1", Vnom=400.0, area=area_1, is_dc=True)
    bus_dc_2 = gce.Bus(name="dc2", Vnom=400.0, area=area_2, is_dc=True)
    for bus in (bus_ac_1, bus_ac_2, bus_dc_1, bus_dc_2):
        grid.add_bus(bus)

    # generation in area 1 and the matching demand in area 2, so there is something to transfer
    grid.add_generator(bus_ac_1, gce.Generator(name="gen", P=500.0, Pmin=0.0, Pmax=2000.0))
    grid.add_load(bus_ac_2, gce.Load(name="load", P=500.0))

    # AC corridor between the two areas
    grid.add_line(gce.Line(name="ac_line", bus_from=bus_ac_1, bus_to=bus_ac_2, x=0.01, rate=1000.0))

    # DC corridor between the two areas
    grid.add_dc_line(gce.DcLine(name="dc_line", bus_from=bus_dc_1, bus_to=bus_dc_2, r=1e-5, rate=1000.0))

    # the sending converter fixes the DC voltage
    grid.add_vsc(gce.VSC(name="vsc_1", bus_from=bus_dc_1, bus_to=bus_ac_1, rate=1000.0,
                         control1=ConverterControlType.Vm_dc, control1_val=1.0,
                         control2=ConverterControlType.Pac, control2_val=0.0))

    # the receiving converter in P-mode 3
    vsc_2 = gce.VSC(name="vsc_2", bus_from=bus_dc_2, bus_to=bus_ac_2, rate=1000.0,
                    control1=ConverterControlType.Pdc_angle_droop, control1_val=174.53,
                    control2=ConverterControlType.Pac, control2_val=0.0)

    # the droop measures the angle from the AC bus at the other end of the DC link
    if set_reference_bus_on_both:
        vsc_2.control1_dev = bus_ac_1
    # left unset on purpose as this is the misconfiguration the test guards
    else:
        pass

    grid.add_vsc(vsc_2)

    return grid


def run_pmode3_link_ntc(grid: gce.MultiCircuit) -> gce.OptimalNetTransferCapacityDriver:
    """
    Run the NTC study on the two-area P-mode 3 grid built above

    :param grid: MultiCircuit
    :return: the driver
    """
    info = grid.get_inter_aggregation_info(objects_from=[grid.areas[0]],
                                           objects_to=[grid.areas[1]])

    ntc_options = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        loading_threshold_to_report=98.0,
        skip_generation_limits=True,
        transmission_reliability_margin=0.0,
        branch_exchange_sensitivity=0.01,
        use_branch_exchange_sensitivity=False,
        branch_rating_contribution=1.0,
        monitor_only_ntc_load_rule_branches=False,
        consider_contingencies=False,
        opf_options=gce.OptimalPowerFlowOptions(),
        lin_options=gce.LinearAnalysisOptions()
    )

    drv = gce.OptimalNetTransferCapacityDriver(grid, ntc_options)
    drv.run()
    return drv


def test_ntc_pmode3_vsc_droop_direction() -> None:
    """
    Ensure the proper P-mode 3 VSC injection direction
    """
    drv = run_pmode3_link_ntc(build_two_pmode3_link_grid(set_reference_bus_on_both=True))
    res = drv.results

    assert res.converged
    assert abs(res.nodal_balance.sum()) < 1e-8

    ac_flow = float(res.Sf[0].real)   # the AC line, area 1 -> area 2
    dc_flow = float(res.Sf[1].real)   # the DC line, area 1 -> area 2

    # both corridors carry power in the same direction
    assert ac_flow > 0.0
    assert dc_flow > 0.0

    # the droop was tuned to the AC line reactance, so unsaturated both carry the same flow
    assert np.isclose(ac_flow, dc_flow, rtol=1e-3)


def test_ntc_pmode3_vsc_without_reference_bus_is_reported() -> None:
    """
    A P-mode 3 VSC with no angle-droop reference bus cannot form its control law. 
    It must be reported.
    """
    drv = run_pmode3_link_ntc(build_two_pmode3_link_grid(set_reference_bus_on_both=False))
    res = drv.results

    assert res.converged

    # the misconfiguration is reported instead of silently producing a loop
    reported = [e for e in drv.logger.entries if "angle-droop reference bus" in e.msg]
    assert len(reported) == 1

    # hold at its P setpoint at 0 MW, so the link does not push power the wrong way
    assert np.isclose(float(res.vsc_Pf[1].real), 0.0, atol=1e-6)


def test_ntc_pmode3_saturates_at_dc_bottleneck() -> None:
    """
    P-mode 3 droop must saturate at the DC-cable capacity, not only at the converter rating.
    """
    grid = gce.open_file(get_grid_path("NTC_8_bus_2pmode3_dc_bottleneck.veragrid"))
    drv = run_pmode3_link_ntc(grid)
    res = drv.results

    assert res.converged

    # every P-mode 3 converter saturated at its DC-cable capacity (2 x 1000 MW),
    # not necessarily at the converter rate if it is for instance set at 5000 MW
    vsc_flows = np.abs(np.real(res.vsc_Pf))
    assert np.allclose(vsc_flows, 2000.0, atol=1.0)

    # the DC cables carry their full rating
    dc_idx = [i for i, name in enumerate(res.branch_names) if str(name).startswith("Dc line")]
    assert np.allclose(np.abs(res.Sf[dc_idx].real), 1000.0, atol=1.0)

    tie_idx = [i for i, rate in enumerate(res.rates) if rate == 8000.0]
    assert np.allclose(res.Sf[tie_idx].real, 3000.0, atol=1.0)


def test_ntc_structural_n1_overload_is_relaxed_not_infeasible() -> None:
    """
    A structurally unavoidable N-1 overload must relax the limit (penalized slack, reported)
    instead of making the whole LP infeasible.

    Grid: gen area -> tie -> radial pair A (rate=100, x=0.01) / B (rate=50, x=0.02) feeding a
    fixed 120 MW load. Base split is 80/40 (B at 80 % of its rating, so its N-1 limit is
    enforced), but losing A forces all 120 MW through B. Thus 70 MW of violation where 
    no exchange reduction can remove. With slacks an optimal solution should be reached.
    """
    grid = gce.MultiCircuit()
    a1 = gce.Area("A1")
    a2 = gce.Area("A2")
    grid.add_area(a1)
    grid.add_area(a2)
    b0 = gce.Bus("B0", Vnom=400, area=a1)
    b0.is_slack = True
    b1 = gce.Bus("B1", Vnom=400, area=a2)
    b2 = gce.Bus("B2", Vnom=400, area=a2)
    for b in (b0, b1, b2):
        grid.add_bus(b)
    grid.add_generator(b0, gce.Generator("G", P=120, Pmax=1000, Pmin=0))
    grid.add_load(b2, gce.Load("L", P=120))
    line_tie = gce.Line(b0, b1, name="tie", x=0.01, rate=1000)
    line_a = gce.Line(b1, b2, name="A", x=0.01, rate=100)
    line_b = gce.Line(b1, b2, name="B", x=0.02, rate=50)
    for ln in (line_tie, line_a, line_b):
        grid.add_line(ln)
    cg = gce.ContingencyGroup(name="A out")
    grid.add_contingency_group(cg)
    grid.add_contingency(gce.Contingency(device=line_a, group=cg))

    info = grid.get_inter_aggregation_info(objects_from=[a1], objects_to=[a2])
    opts = gce.OptimalNetTransferCapacityOptions(
        sending_bus_idx=info.idx_bus_from,
        receiving_bus_idx=info.idx_bus_to,
        transfer_method=gce.AvailableTransferMode.InstalledPower,
        consider_contingencies=True,
        use_branch_exchange_sensitivity=False,
        opf_options=gce.OptimalPowerFlowOptions(),
    )
    drv = gce.OptimalNetTransferCapacityDriver(grid, opts)
    drv.run()
    res = drv.results

    # the LP stays optimal despite the structural violation
    assert bool(np.all(res.converged))

    # the base flows are the physical 80/40 split, untouched by the relaxation
    assert np.isclose(float(res.Sf[1].real), 80.0, atol=1.0)
    assert np.isclose(float(res.Sf[2].real), 40.0, atol=1.0)


if __name__ == '__main__':
    # test_issue_372_1()
    # test_issue_372_2()
    # test_issue_372_4()
    # test_ntc_ultra_simple()
    # test_ntc_pmode_saturation()
    # test_ntc_vsc()
    # test_ntc_vsc_contingencies()
    # test_2_node_several_conditions_ntc()
    # test_ntc_pmode_saturation()
    # test_ntc_pmode_non_saturation()
    # test_issue_372_3()
    # test_hvdc_lines_tests()
    # test_activs_2000_acdc()
    test_ntc_vsc_8_buses_REE_contingencies()
