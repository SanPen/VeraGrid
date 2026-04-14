# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import numpy as np
import pandas as pd
import pytest
from VeraGridEngine.api import *
from VeraGridEngine.Simulations.PowerFlow.power_flow_worker import multi_island_pf_nc


def test_contingency() -> None:
    """
    Check that the contingencies match conceptually
    :return:
    """
    fname = os.path.join('data', 'grids', 'IEEE14_contingency.gridcal')
    main_circuit = FileOpen(fname).open()
    pf_options = PowerFlowOptions(SolverType.NR,
                                  verbose=False,
                                  use_stored_guess=False,
                                  control_q=False)

    options = ContingencyAnalysisOptions(pf_options=pf_options,
                                         contingency_method=ContingencyMethod.PowerFlow)

    cont_analysis_driver = ContingencyAnalysisDriver(grid=main_circuit,
                                                     options=options,
                                                     linear_multiple_contingencies=None)
    cont_analysis_driver.run()
    print("")

    for i, lne in enumerate(main_circuit.get_branches(False, False, True)):
        lne.active = False
        pf_driver = PowerFlowDriver(grid=main_circuit, options=pf_options)
        pf_driver.run()

        # assert that the power flow matches whatever it was done with the contingencies
        assert (np.allclose(cont_analysis_driver.results.Sf[i, :], pf_driver.results.Sf))

        assert cont_analysis_driver.results.Sf[i, i] == complex(0, 0)

        lne.active = True


def test_linear_contingency():
    # fname = os.path.join('data', 'grids', 'IEEE14_contingency.gridcal')
    fname = os.path.join('data', 'grids', 'IEEE14-2_4_1-3_4_1.gridcal')
    main_circuit = FileOpen(fname).open()
    pf_options = PowerFlowOptions(SolverType.NR,
                                  verbose=0,
                                  control_q=False)

    nc = compile_numerical_circuit_at(main_circuit)
    lin = LinearAnalysis(nc=nc)
    linear_multi_contingency = LinearMultiContingencies(grid=main_circuit,
                                                        contingency_groups_used=main_circuit.get_contingency_groups())
    linear_multi_contingency.compute(lin=lin)

    options = ContingencyAnalysisOptions(pf_options=pf_options, contingency_method=ContingencyMethod.Linear)
    cont_analysis_driver = ContingencyAnalysisDriver(grid=main_circuit, options=options,
                                                     linear_multiple_contingencies=linear_multi_contingency)
    cont_analysis_driver.run()
    print("")


# def test_ieee14_contingencies() -> None:
#     """
#     Check that the contingencies match conceptually
#     :return:
#     """
#     fname = os.path.join('data', 'grids', 'Matpower', 'case14.m')
#
#     res_file = os.path.join('data', 'results', 'IEEE14_con_results_matpower.xlsx')
#     main_circuit = FileOpen(fname).open()
#     nc = compile_numerical_circuit_at(main_circuit, t_idx=None)
#     pf_options = PowerFlowOptions(SolverType.NR,
#                                   retry_with_other_methods=False,
#                                   control_q=False,
#                                   control_taps_phase=False,
#                                   control_taps_modules=False,
#                                   control_remote_voltage=False,)
#
#     vm_df = pd.read_excel(res_file, sheet_name='Vm', index_col=0)
#     va_df = pd.read_excel(res_file, sheet_name='Va', index_col=0)
#     Pf_df = pd.read_excel(res_file, sheet_name='Pf', index_col=0)
#     Qf_df = pd.read_excel(res_file, sheet_name='Qf', index_col=0)
#
#     for k in range(nc.passive_branch_data.nelm):
#         nc.passive_branch_data.active[k] = 0
#
#         res = multi_island_pf_nc(nc=nc, options=pf_options)
#
#         try:
#             vm_expected = vm_df.values[:, k]
#             va_expected = va_df.values[:, k]
#             vm = np.abs(res.voltage)
#             va = np.angle(res.voltage, deg=True)
#
#             # TODO: Comparing with PSSe, it is the same value...do the PSSe comaprison instead
#             assert np.allclose(vm, vm_expected, atol=1e-3)
#             assert np.allclose(va, va_expected, atol=1e-3)
#         except AttributeError:
#             print()
#
#         nc.passive_branch_data.active[k] = 1


# def test_ieee14_contingencies_psse() -> None:
#     """
#     Check that the contingencies match conceptually
#     :return:
#     """
#     fname = os.path.join('data', 'grids', 'RAW', 'IEEE 14 bus.raw')
#
#     res_file = os.path.join('data', 'results', 'IEEE14_con_results.xlsx')
#     main_circuit = FileOpen(fname).open()
#     nc = compile_numerical_circuit_at(main_circuit, t_idx=None)
#     pf_options = PowerFlowOptions(SolverType.NR,
#                                   retry_with_other_methods=False,
#                                   control_q=False,
#                                   control_taps_phase=False,
#                                   control_taps_modules=False,
#                                   control_remote_voltage=False,)
#
#     vm_df = pd.read_excel(res_file, sheet_name='Vm', index_col=0)
#     va_df = pd.read_excel(res_file, sheet_name='Va', index_col=0)
#
#     for k in range(nc.passive_branch_data.nelm):
#         nc.passive_branch_data.active[k] = 0
#
#         res = multi_island_pf_nc(nc=nc, options=pf_options)
#
#         try:
#             vm_expected = vm_df[k+1].values
#             va_expected = va_df[k+1].values
#             vm = np.abs(res.voltage)
#             va = np.angle(res.voltage, deg=True)
#
#             assert np.allclose(vm, vm_expected, atol=1e-3)
#             assert np.allclose(va, va_expected, atol=1e-3)
#         except AttributeError:
#             print()
#
#         nc.passive_branch_data.active[k] = 1


def test_single_contingency_helm() -> None:
    """
    Run a single contingency to check we get matching results
    Comparison between HELM, NR, and HELM with contingency factorization
    """

    fname = os.path.join('data', 'grids', 'IEEE14_single_contingency.gridcal')
    main_circuit = FileOpen(fname).open()

    
    # First run power flow with deactivated line
    main_circuit.lines[2].active = False  # Line 2_3 out

    pf_driver = PowerFlowDriver(main_circuit, PowerFlowOptions(SolverType.HELM,
                                        verbose=False,
                                        use_stored_guess=False,
                                        control_q=False))
    pf_driver.run()

    # Then run contingency with HELM
    main_circuit.lines[2].active = True  # Line 2_3 out

    con_helm = ContingencyAnalysisDriver(
        grid=main_circuit,
        options=ContingencyAnalysisOptions(
            pf_options=PowerFlowOptions(SolverType.HELM,
                                        verbose=False,
                                        use_stored_guess=False,
                                        control_q=False),
            contingency_method=ContingencyMethod.HELM
        ),
        linear_multiple_contingencies=None
    )
    con_helm.run()

    # Finally run contingency with NR
    main_circuit.lines[2].active = True  # Line 2_3 out

    con_nr = ContingencyAnalysisDriver(
        grid=main_circuit,
        options=ContingencyAnalysisOptions(
            pf_options=PowerFlowOptions(SolverType.NR,
                                        verbose=False,
                                        use_stored_guess=False,
                                        control_q=False),
            contingency_method=ContingencyMethod.PowerFlow
        ),
        linear_multiple_contingencies=None
    )
    con_nr.run()

    ok1 = np.allclose(abs(pf_driver.results.voltage), abs(con_helm.results.voltage), atol=1e-06)
    ok2 = np.allclose(abs(con_helm.results.voltage), abs(con_nr.results.voltage), atol=1e-06)

    assert ok1
    assert ok2


@pytest.mark.skip("This may never work as intended...")
def test_contingency_helm() -> None:
    """
    Check that the contingencies match conceptually
    :return:
    """
    fname = os.path.join('data', 'grids', 'IEEE14_contingency.gridcal')
    main_circuit = FileOpen(fname).open()

    # Run contingency with HELM
    con_helm = ContingencyAnalysisDriver(
        grid=main_circuit,
        options=ContingencyAnalysisOptions(
            pf_options=PowerFlowOptions(SolverType.HELM,
                                        verbose=False,
                                        use_stored_guess=False,
                                        control_q=False),
            contingency_method=ContingencyMethod.HELM
        ),
        linear_multiple_contingencies=None
    )
    con_helm.run()

    # Run contingency with NR
    main_circuit.lines[2].active = True  # Line 2_3 out

    con_nr = ContingencyAnalysisDriver(
        grid=main_circuit,
        options=ContingencyAnalysisOptions(
            pf_options=PowerFlowOptions(SolverType.NR,
                                        verbose=False,
                                        use_stored_guess=False,
                                        control_q=False),
            contingency_method=ContingencyMethod.PowerFlow
        ),
        linear_multiple_contingencies=None
    )
    con_nr.run()

    # Get the absolute values of voltages for both methods
    helm_voltage_abs = np.abs(con_helm.results.voltage)
    nr_voltage_abs = np.abs(con_nr.results.voltage)
    
    ok = np.allclose(helm_voltage_abs, nr_voltage_abs, atol=1e-5)
    assert ok


if __name__ == "__main__":
    test_contingency_helm()
    # test_single_contingency_helm()