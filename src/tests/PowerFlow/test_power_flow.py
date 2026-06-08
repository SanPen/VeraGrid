# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

import os
import pandas as pd
import numpy as np

from VeraGridEngine.IO.file_open import FileOpen
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions import (
    split_reactive_power_between_generators_and_batteries,
    split_slack_bus_quantity_between_generators_and_batteries,
)
from VeraGridEngine.Simulations.PowerFlow.power_flow_worker import PowerFlowOptions, multi_island_pf_nc
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import SolverType
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.enumerations import ConverterControlType, GeneratorControlMode
import VeraGridEngine.api as gce

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def test_ieee_grids():
    """
    Checks the .RAW files of IEEE grids against the PSS/e results
    This test checks 2 things:
    - PSS/e import fidelity
    - PSS/e vs VeraGrid results
    :return: Nothing if ok, fails if not
    """

    files = [
        ('IEEE 14 bus.raw', 'IEEE 14 bus.sav.xlsx'),
        ('IEEE 30 bus.raw', 'IEEE 30 bus.sav.xlsx'),
        ('IEEE 118 Bus v2.raw', 'IEEE 118 Bus.sav.xlsx'),
    ]

    for solver_type in [SolverType.NR,
                        SolverType.IWAMOTO,
                        SolverType.LM,
                        SolverType.FASTDECOUPLED,
                        SolverType.PowellDogLeg,
                        SolverType.HELM]:

        print(solver_type)

        options = PowerFlowOptions(solver_type,
                                   verbose=0,
                                   control_q=False,
                                   retry_with_other_methods=False)

        for f1, f2 in files:
            print(f1, end=' ')

            fname = os.path.join('data', 'grids', 'RAW', f1)
            main_circuit = FileOpen(fname).open()
            power_flow = PowerFlowDriver(main_circuit, options)
            power_flow.run()

            # load the associated results file
            df_v = pd.read_excel(os.path.join('data', 'results', f2), sheet_name='Vabs', index_col=0)
            df_p = pd.read_excel(os.path.join('data', 'results', f2), sheet_name='Pbranch', index_col=0)

            v_gc = np.abs(power_flow.results.voltage)
            v_psse = df_v.values[:, 0]
            p_gc = power_flow.results.Sf.real
            p_psse = df_p.values[:, 0]

            v_ok = np.allclose(v_gc, v_psse, atol=1e-4)
            flow_ok = np.allclose(p_gc, p_psse, atol=1e-2)

            if not v_ok:
                print('power flow voltages test for {} failed'.format(fname))
            if not flow_ok:
                print('power flow flows test for {} failed'.format(fname))

            assert v_ok
            assert flow_ok

        print(solver_type, 'ok')


def test_dc_pf_ieee14():
    """
    Test the DC power flow with tap module
    :return:
    """
    options = PowerFlowOptions(SolverType.Linear,
                               verbose=False,
                               control_q=False,
                               retry_with_other_methods=False)

    fname = os.path.join('data', 'grids', 'Matpower', 'case14.matpower')
    main_circuit = FileOpen(fname).open()
    power_flow = PowerFlowDriver(main_circuit, options)
    power_flow.run()

    # Data from Matpower 8
    Pf_test = np.array([147.8386,
                        71.1614,
                        70.0146,
                        55.1519,
                        40.9721,
                        -24.1854,
                        -61.7465,
                        6.7283,
                        7.6074,
                        17.2513,
                        0,
                        28.3612,
                        5.7717,
                        9.6413,
                        -3.2283,
                        1.5074,
                        5.2587,
                        28.3612,
                        16.5518,
                        42.7870,
                        ])

    assert np.allclose(power_flow.results.Sf.real, Pf_test, atol=1e-3)


def test_dc_pf_ieee14_ps():
    """
    Test the DC power flow with phase shifter and tap module
    :return:
    """
    options = PowerFlowOptions(SolverType.Linear,
                               verbose=False,
                               control_q=False,
                               retry_with_other_methods=False)

    fname = os.path.join('data', 'grids', 'Matpower', 'case14_ps.matpower')
    main_circuit = FileOpen(fname).open()
    power_flow = PowerFlowDriver(main_circuit, options)
    power_flow.run()

    # Data from Matpower 8
    Pf_test = np.array([141.7788,
                        77.2212,
                        64.8753,
                        44.3963,
                        50.8072,
                        -29.3247,
                        23.8991,
                        67.8736,
                        16.5880,
                        48.6659,
                        0,
                        -97.1080,
                        -55.3736,
                        -30.7538,
                        -64.3736,
                        10.4880,
                        45.6538,
                        -97.1080,
                        40.4806,
                        144.3275,
                        ])

    assert np.allclose(power_flow.results.Sf.real, Pf_test, atol=1e-3)


def test_zip() -> None:
    """
    Test the power flow with ZIP loads compared to PSSe
    """

    fname = os.path.join('data', 'grids', 'ZIP_load_example.raw')
    main_circuit = FileOpen(fname).open()

    options = PowerFlowOptions(tolerance=1e-6)
    power_flow = PowerFlowDriver(main_circuit, options)
    power_flow.run()

    Vm_psse = np.array([1.00000, 0.98933, 0.98560, 0.98579])
    Va_psse = np.deg2rad(np.array([0.00000, -5.1287, -9.1535, -11.4464]))

    Vm = np.abs(power_flow.results.voltage)
    Va = np.angle(power_flow.results.voltage, deg=False)

    assert np.allclose(Vm_psse, Vm, atol=1e-3)
    assert np.allclose(Va_psse, Va, atol=1e-3)


def test_controllable_shunt() -> None:
    """
    This tests that the controllable shunt is indeed controlling voltage at 1.02 at the third bus
    """

    fname = os.path.join('data', 'grids', 'Controllable_shunt_example.gridcal')
    main_circuit = FileOpen(fname).open()
    options = PowerFlowOptions(control_q=False)
    power_flow = PowerFlowDriver(main_circuit, options)
    power_flow.run()

    Vm = np.abs(power_flow.results.voltage)
    Vm_test = np.array([[1., 1.0164564, 1.02]])

    assert np.allclose(Vm_test, Vm, atol=1e-3)


def test_voltage_local_control_with_generation() -> None:
    """
    Check that a generator can perform remote voltage regulation
    """
    fname = os.path.join('data', 'grids', 'RAW', 'IEEE 14 bus.raw')

    grid = gce.open_file(fname)

    # control local bus with generator 4
    gen = grid.generators[4]
    gen.control_mode = GeneratorControlMode.V
    gen.Q = 0  # otherwise the raw will assign a Q that is controlling V...
    bus_dict = grid.get_bus_index_dict()
    bus_i = bus_dict[gen.bus]

    # run power flow with the local voltage control enabled
    for solver_type in [SolverType.NR, SolverType.IWAMOTO, SolverType.LM,
                        SolverType.FASTDECOUPLED, SolverType.PowellDogLeg]:
        options = PowerFlowOptions(solver_type,
                                   verbose=0,
                                   control_q=False,
                                   retry_with_other_methods=False)

        results = gce.power_flow(grid, options)
        vm = np.abs(results.voltage)

        assert results.converged
        assert np.isclose(vm[bus_i], gen.Vset, atol=options.tolerance)

    # run power flow with the local voltage control disabled
    gen.control_mode = GeneratorControlMode.Q
    for solver_type in [SolverType.NR, SolverType.IWAMOTO, SolverType.LM,
                        SolverType.FASTDECOUPLED, SolverType.PowellDogLeg]:
        options = PowerFlowOptions(solver_type,
                                   verbose=0,
                                   control_q=False,
                                   retry_with_other_methods=False)

        results = gce.power_flow(grid, options)
        vm = np.abs(results.voltage)

        assert results.converged
        assert not np.isclose(vm[bus_i], gen.Vset, atol=options.tolerance)


def test_qv_droop_control_mode() -> None:
    """
    Check that the reported generator reactive power follows the QV droop law.
    """
    fname: str = os.path.join('data', 'grids', 'RAW', 'IEEE 14 bus.raw')
    grid = gce.open_file(fname)

    # Use a seeded random choice so the test exercises a non-slack machine
    # without making the test outcome depend on runtime randomness.
    rng: np.random.Generator = np.random.default_rng(14)
    candidate_indices: np.ndarray = np.arange(1, len(grid.generators), dtype=int)
    gen_position: int = int(rng.integers(0, len(candidate_indices)))
    gen_idx: int = int(candidate_indices[gen_position])
    gen = grid.generators[gen_idx]
    bus_index_dict: dict = grid.get_bus_index_dict()
    bus_i: int = bus_index_dict[gen.bus]

    # Configure the selected generator in droop mode with a small set-point
    # offset so the converged operating point produces a measurable Q response.
    gen.control_mode = GeneratorControlMode.QVDroop
    gen.k_droop = 4.0
    gen.dead_band = 0.0
    gen.Q = 0.0
    gen.Vset = gen.Vset + 0.01

    options = PowerFlowOptions(solver_type=SolverType.NR,
                               verbose=0,
                               control_q=False,
                               retry_with_other_methods=False)

    results = gce.power_flow(grid, options)
    vm: np.ndarray = np.abs(results.voltage)
    delta_v: float = gen.Vset - vm[bus_i]

    # Reproduce the implemented droop equation in MVAr, including the reactive
    # power clipping at the generator capability limits.
    expected_q: float = delta_v * gen.k_droop * gen.Qmax
    expected_q = float(np.clip(expected_q, gen.Qmin, gen.Qmax))

    assert results.converged
    assert np.isclose(results.gen_q[gen_idx], expected_q, atol=1e-6, rtol=1e-6)


def test_reactive_split_removes_fixed_bus_q_before_voltage_control_share() -> None:
    """
    Check that the reactive split removes fixed bus-side Q before assigning the
    remaining reactive injection to voltage-controlled generator-like devices.
    """
    qbus: np.ndarray = np.array([2.0], dtype=float)
    qfixed_bus: np.ndarray = np.array([-4.0], dtype=float)
    gen_bus_idx: np.ndarray = np.array([0], dtype=int)
    qmin_gen: np.ndarray = np.array([0.0], dtype=float)
    qmax_gen: np.ndarray = np.array([10.0], dtype=float)
    gen_status: np.ndarray = np.array([True], dtype=bool)
    control_mode_int_gen: np.ndarray = np.array([GeneratorControlMode.V.idx()], dtype=int)
    q0_gen: np.ndarray = np.array([0.0], dtype=float)
    vset_gen: np.ndarray = np.array([1.0], dtype=float)
    k_droop_gen: np.ndarray = np.array([0.0], dtype=float)
    dead_band_gen: np.ndarray = np.array([0.0], dtype=float)
    batt_bus_idx: np.ndarray = np.zeros(0, dtype=int)
    qmin_batt: np.ndarray = np.zeros(0, dtype=float)
    qmax_batt: np.ndarray = np.zeros(0, dtype=float)
    batt_status: np.ndarray = np.zeros(0, dtype=bool)
    control_mode_int_batt: np.ndarray = np.zeros(0, dtype=int)
    q0_batt: np.ndarray = np.zeros(0, dtype=float)
    vm: np.ndarray = np.array([1.0], dtype=float)

    q_gen: np.ndarray
    q_batt: np.ndarray
    q_gen, q_batt = split_reactive_power_between_generators_and_batteries(
        Qbus=qbus,
        Qfixed_bus=qfixed_bus,
        gen_bus_idx=gen_bus_idx,
        Qmin_gen=qmin_gen,
        Qmax_gen=qmax_gen,
        gen_status=gen_status,
        control_mode_int_gen=control_mode_int_gen,
        Q0_gen=q0_gen,
        Vset_gen=vset_gen,
        k_droop_gen=k_droop_gen,
        dead_band_gen=dead_band_gen,
        batt_bus_idx=batt_bus_idx,
        Qmin_batt=qmin_batt,
        Qmax_batt=qmax_batt,
        batt_status=batt_status,
        control_mode_int_batt=control_mode_int_batt,
        Q0_batt=q0_batt,
        v_ctrl_val_gen=GeneratorControlMode.V.idx(),
        qv_droop_val_gen=GeneratorControlMode.QVDroop.idx(),
        Vm=vm,
        atol=1e-12,
    )

    assert q_batt.size == 0
    assert np.isclose(q_gen[0], 6.0, atol=1e-12)
    assert np.isclose(qfixed_bus[0] + q_gen[0], qbus[0], atol=1e-12)


def test_slack_bus_split_handles_multiple_slack_buses() -> None:
    """
    Check that each slack bus reassigns its solved residual to the connected
    online generator-like devices independently.
    """
    qbus: np.ndarray = np.array([15.0, -3.0, 7.0], dtype=float)
    qfixed_bus: np.ndarray = np.array([5.0, -3.0, 1.0], dtype=float)
    slack_bus_mask: np.ndarray = np.array([True, False, True], dtype=bool)
    gen_bus_idx: np.ndarray = np.array([0, 2], dtype=int)
    qmin_gen: np.ndarray = np.array([0.0, 0.0], dtype=float)
    qmax_gen: np.ndarray = np.array([20.0, 10.0], dtype=float)
    gen_status: np.ndarray = np.array([True, True], dtype=bool)
    q0_gen: np.ndarray = np.array([0.0, 0.0], dtype=float)
    batt_bus_idx: np.ndarray = np.array([0], dtype=int)
    qmin_batt: np.ndarray = np.array([0.0], dtype=float)
    qmax_batt: np.ndarray = np.array([10.0], dtype=float)
    batt_status: np.ndarray = np.array([True], dtype=bool)
    q0_batt: np.ndarray = np.array([0.0], dtype=float)

    q_gen: np.ndarray
    q_batt: np.ndarray
    q_gen, q_batt = split_slack_bus_quantity_between_generators_and_batteries(
        Qbus=qbus,
        Qfixed_bus=qfixed_bus,
        slack_bus_mask=slack_bus_mask,
        gen_bus_idx=gen_bus_idx,
        Qmin_gen=qmin_gen,
        Qmax_gen=qmax_gen,
        gen_status=gen_status,
        Q0_gen=q0_gen,
        batt_bus_idx=batt_bus_idx,
        Qmin_batt=qmin_batt,
        Qmax_batt=qmax_batt,
        batt_status=batt_status,
        Q0_batt=q0_batt,
        atol=1e-12,
    )

    assert np.isclose(q_gen[0], 20.0 / 3.0, atol=1e-12)
    assert np.isclose(q_batt[0], 10.0 / 3.0, atol=1e-12)
    assert np.isclose(q_gen[1], 6.0, atol=1e-12)
    assert np.isclose(qfixed_bus[0] + q_gen[0] + q_batt[0], qbus[0], atol=1e-12)
    assert np.isclose(qfixed_bus[2] + q_gen[1], qbus[2], atol=1e-12)


def test_slack_bus_split_does_not_clip_solved_residual_to_limits() -> None:
    """
    Check that slack-bus reconstruction reports the solved value even when it
    exceeds the declared device limits.
    """
    qbus: np.ndarray = np.array([18.55], dtype=float)
    qfixed_bus: np.ndarray = np.array([0.0], dtype=float)
    slack_bus_mask: np.ndarray = np.array([True], dtype=bool)
    gen_bus_idx: np.ndarray = np.array([0], dtype=int)
    qmin_gen: np.ndarray = np.array([-10.0], dtype=float)
    qmax_gen: np.ndarray = np.array([10.0], dtype=float)
    gen_status: np.ndarray = np.array([True], dtype=bool)
    q0_gen: np.ndarray = np.array([0.0], dtype=float)
    batt_bus_idx: np.ndarray = np.zeros(0, dtype=int)
    qmin_batt: np.ndarray = np.zeros(0, dtype=float)
    qmax_batt: np.ndarray = np.zeros(0, dtype=float)
    batt_status: np.ndarray = np.zeros(0, dtype=bool)
    q0_batt: np.ndarray = np.zeros(0, dtype=float)

    q_gen: np.ndarray
    q_batt: np.ndarray
    q_gen, q_batt = split_slack_bus_quantity_between_generators_and_batteries(
        Qbus=qbus,
        Qfixed_bus=qfixed_bus,
        slack_bus_mask=slack_bus_mask,
        gen_bus_idx=gen_bus_idx,
        Qmin_gen=qmin_gen,
        Qmax_gen=qmax_gen,
        gen_status=gen_status,
        Q0_gen=q0_gen,
        batt_bus_idx=batt_bus_idx,
        Qmin_batt=qmin_batt,
        Qmax_batt=qmax_batt,
        batt_status=batt_status,
        Q0_batt=q0_batt,
        atol=1e-12,
    )

    assert q_batt.size == 0
    assert np.isclose(q_gen[0], 18.55, atol=1e-12)


def test_voltage_remote_control_with_generation() -> None:
    """
    Check that a generator can perform remote voltage regulation
    """
    fname = os.path.join('data', 'grids', 'RAW', 'IEEE 14 bus.raw')

    grid = gce.open_file(fname)

    # control bus 6 with generator 4
    grid.generators[4].control_bus = grid.buses[6]

    for control_remote_voltage in [True, False]:
        for solver_type in [SolverType.NR, SolverType.IWAMOTO, SolverType.LM,
                            SolverType.FASTDECOUPLED, SolverType.PowellDogLeg]:

            options = PowerFlowOptions(solver_type=solver_type,
                                       verbose=0,
                                       control_q=False,
                                       retry_with_other_methods=False,
                                       control_remote_voltage=control_remote_voltage)

            results = gce.power_flow(grid, options)

            vm = np.abs(results.voltage)

            assert results.converged

            # is the control voltage equal to the desired set point?
            ok = np.isclose(vm[6], grid.generators[4].Vset, atol=options.tolerance)

            if control_remote_voltage:
                assert ok
            else:
                assert not ok


def test_voltage_control_with_ltc() -> None:
    """
    Check that a transformer can regulate the voltage at a bus
    """

    fname = os.path.join('data', 'grids', '5Bus_LTC_FACTS_Fig4.7.gridcal')

    grid = gce.open_file(fname)
    bus_dict = grid.get_bus_index_dict()
    ctrl_idx = bus_dict[grid.transformers2w[0].regulation_bus]

    for control_taps_modules in [True, False]:
        for solver_type in [SolverType.NR, SolverType.LM, SolverType.PowellDogLeg]:
            options = PowerFlowOptions(solver_type,
                                       verbose=0,
                                       control_q=False,
                                       retry_with_other_methods=False,
                                       control_taps_modules=control_taps_modules,
                                       control_taps_phase=False,
                                       control_remote_voltage=False,
                                       apply_temperature_correction=False,
                                       orthogonalize_controls=False)

            results = gce.power_flow(grid, options)

            vm = np.abs(results.voltage)

            assert results.converged

            # check that the bus voltage module is the transformer voltage set point
            ok = np.isclose(vm[ctrl_idx], grid.transformers2w[0].vset, atol=options.tolerance)

            if control_taps_modules:
                assert ok
            else:
                assert not ok


def test_qf_control_with_ltc() -> None:
    """
    Check that a transformer can regulate the voltage at a bus
    """
    fname = os.path.join('data', 'grids', '5Bus_PST_FACTS_Fig4.10(Qf).gridcal')

    grid = gce.open_file(fname)

    for control_taps_modules in [True, False]:
        for solver_type in [SolverType.NR, SolverType.LM, SolverType.PowellDogLeg]:
            options = PowerFlowOptions(solver_type,
                                       verbose=0,
                                       control_q=False,
                                       retry_with_other_methods=False,
                                       orthogonalize_controls=False,
                                       control_taps_modules=control_taps_modules)

            results = gce.power_flow(grid, options)

            assert results.converged

            # check that the bus voltage module is the transformer voltage set point
            ok = np.isclose(results.Sf[7].imag, grid.transformers2w[0].Qset, atol=options.tolerance)

            if control_taps_modules:
                assert ok
            else:
                assert not ok


def test_qt_control_with_ltc() -> None:
    """
    Check that a transformer can regulate the voltage at a bus
    """
    fname = os.path.join('data', 'grids', '5Bus_PST_FACTS_Fig4.10(Qf).gridcal')

    grid = gce.open_file(fname)
    grid.transformers2w[0].tap_module_control_mode = gce.TapModuleControl.Qt

    for control_taps_modules in [True, False]:
        for solver_type in [SolverType.NR, SolverType.LM, SolverType.PowellDogLeg]:
            options = PowerFlowOptions(solver_type,
                                       verbose=0,
                                       control_q=False,
                                       retry_with_other_methods=False,
                                       orthogonalize_controls=False,
                                       control_taps_modules=control_taps_modules)

            results = gce.power_flow(grid, options)

            assert results.converged

            # check that the bus voltage module is the transformer voltage set point
            ok = np.isclose(results.St[7].imag, grid.transformers2w[0].Qset, atol=options.tolerance)

            if control_taps_modules:
                assert ok
            else:
                assert not ok


def test_power_flow_control_with_pst_pf() -> None:
    """
    Check that a transformer can regulate the voltage at a bus
    """
    fname = os.path.join('data', 'grids', '5Bus_PST_FACTS_Fig4.10.gridcal')

    grid = gce.open_file(fname)

    for control_taps_phase in [True, False]:
        for solver_type in [SolverType.NR, SolverType.LM, SolverType.PowellDogLeg]:
            options = PowerFlowOptions(solver_type,
                                       verbose=0,
                                       control_q=False,
                                       retry_with_other_methods=False,
                                       control_taps_phase=control_taps_phase,
                                       orthogonalize_controls=False)

            results = gce.power_flow(grid, options)

            assert results.converged

            # check that the bus voltage module is the transformer voltage set point
            ok = np.isclose(results.Sf[7].real, grid.transformers2w[0].Pset, atol=options.tolerance)

            if control_taps_phase:
                assert ok
            else:
                assert not ok


def test_power_flow_control_with_pst_pt() -> None:
    """
    Check that a transformer can regulate the voltage at a bus
    """
    fname = os.path.join('data', 'grids', '5Bus_PST_FACTS_Fig4.10(Pt).gridcal')

    grid = gce.open_file(fname)

    for control_taps_phase in [True, False]:
        for solver_type in [SolverType.NR, SolverType.LM, SolverType.PowellDogLeg]:
            options = PowerFlowOptions(solver_type,
                                       verbose=0,
                                       control_q=False,
                                       retry_with_other_methods=False,
                                       control_taps_phase=control_taps_phase,
                                       orthogonalize_controls=False,
                                       max_iter=80)

            results = gce.power_flow(grid, options)

            assert results.converged

            # check that the bus voltage module is the transformer voltage set point
            ok = np.isclose(results.St[7].real, grid.transformers2w[0].Pset, atol=options.tolerance)

            if control_taps_phase:
                assert ok
            else:
                assert not ok


def test_generator_Q_lims() -> None:
    """
    Check that we can shift the controls well when hitting Q limits
    """
    fname = os.path.join('data', 'grids', '5Bus_LTC_FACTS_Fig4.7_Qlim.gridcal')

    grid = gce.open_file(fname)

    for control_q in [True, False]:
        options = PowerFlowOptions(gce.SolverType.NR,
                                   verbose=1,
                                   control_q=control_q,
                                   retry_with_other_methods=False,
                                   control_taps_modules=False,
                                   control_taps_phase=False,
                                   control_remote_voltage=False,
                                   apply_temperature_correction=False,
                                   distributed_slack=False)

        power_flow = PowerFlowDriver(grid, options)
        power_flow.run()

        # check that the bus Q is at the limit
        qbus = power_flow.results.Sbus[3].imag
        ok = np.isclose(qbus, grid.generators[1].Qmin, atol=options.tolerance)

        if control_q:
            assert ok
        else:
            assert not ok

        assert power_flow.results.converged


def test_fubm() -> None:
    """

    :return:
    """
    fname = os.path.join('data', 'grids', 'fubm_caseHVDC_vt_josep.gridcal')
    grid = gce.open_file(fname)

    for solver_type in [SolverType.NR, SolverType.LM, SolverType.PowellDogLeg]:
        options = gce.PowerFlowOptions(solver_type=solver_type,
                                       control_q=False,
                                       retry_with_other_methods=False,
                                       control_taps_modules=True,
                                       control_taps_phase=True,
                                       control_remote_voltage=True,
                                       verbose=1)

        driver = gce.PowerFlowDriver(grid=grid, options=options)
        driver.run()
        results = driver.results
        vm = np.abs(results.voltage)

        expected_vm = np.abs(np.array([1.01 + 0j,
                                       1.0120148113290914 - 0.00414941372825624j,
                                       1.01116 + 0j,
                                       1.0111600156849796 + 0j,
                                       1.0117031232472475 - 0.03475745116898685j,
                                       1.0194294344036188 - 0.03411199600606859j]))

        assert results.converged

        ok = np.allclose(vm, expected_vm, rtol=1e-4)
        assert ok


def test_power_flow_12bus_acdc() -> None:
    """
    Check that a transformer can regulate the voltage at a bus
    """
    fname = os.path.join('data', 'grids', 'AC-DC with all and DCload.gridcal')

    grid = gce.open_file(fname)

    expected_v = np.array([1. + 0.j,
                           0.99993477 - 0.01142182j,
                           0.981475 - 0.02798462j,
                           0.99961098 - 0.02789078j,
                           0.9970314 + 0.j,
                           0.9921219 + 0.j,
                           1. + 0.j,
                           0.9967762 + 0.j,
                           0.99174229 - 0.02349737j,
                           0.99263056 - 0.02449658j,
                           1. + 0.j,
                           0.99972273 - 0.0235469j,
                           0.99752297 - 0.01554718j,
                           0.99999114 - 0.00421027j,
                           0.99937536 - 0.03533967j,
                           0.99964957 - 0.02647153j,
                           0.99799207 + 0.j])

    # ------------------------------------------------------------------------------------------------------------------
    # for solver_type in [SolverType.NR]:
    for solver_type in [SolverType.NR, SolverType.PowellDogLeg, SolverType.LM]:
        options = PowerFlowOptions(solver_type=solver_type,
                                   verbose=0,
                                   control_q=False,
                                   retry_with_other_methods=False,
                                   control_taps_phase=True,
                                   tolerance=1e-8,
                                   max_iter=80)

        driver = PowerFlowDriver(grid=grid, options=options)
        driver.run()
        solution = driver.results

        if not solution.converged:
            driver.logger.print("")

        assert solution.converged

        assert np.allclose(expected_v, solution.voltage, atol=1e-6)

        assert np.allclose(grid.vsc_devices[0].control1_val, solution.Pfp_vsc[0], atol=1e-6)
        assert np.allclose(grid.vsc_devices[0].control2_val, solution.St_vsc[0].imag, atol=1e-6)

        assert np.allclose(grid.vsc_devices[1].control1_val, abs(solution.voltage[3]), atol=1e-6)
        assert np.allclose(grid.vsc_devices[1].control2_val, solution.St_vsc[1].real, atol=1e-6)

        assert np.allclose(grid.vsc_devices[2].control1_val, abs(solution.voltage[6]), atol=1e-6)
        assert np.allclose(grid.vsc_devices[2].control2_val, solution.St_vsc[2].imag, atol=1e-6)

        assert np.allclose(grid.vsc_devices[3].control1_val, solution.Pfp_vsc[3], atol=1e-6)
        assert np.allclose(grid.vsc_devices[3].control2_val, solution.St_vsc[3].imag, atol=1e-6)

        assert np.allclose(grid.transformers2w[2].vset, abs(solution.voltage[13]), atol=1e-6)

        assert np.allclose(grid.hvdc_lines[0].Pset, solution.Pf_hvdc[0], atol=1e-10)


def test_vsc_current_limitation() -> None:
    """
    Full AC/DC Power Flow simulation with converter's current limitation and negative poles
    """
    fname = os.path.join('data', 'grids', 'vsc_current_limitation.veragrid')

    grid = gce.open_file(fname)

    options = PowerFlowOptions(solver_type=SolverType.NR,
                               retry_with_other_methods=False,
                               limit_i_vsc=True)

    driver = PowerFlowDriver(grid=grid, options=options)
    driver.run()
    solution = driver.results

    if not solution.converged:
        driver.logger.print("")

    assert solution.converged

    # Checks if the voltage magnitude and angle are correct.
    assert np.allclose(0.9287489355489488, abs(solution.voltage[9]), atol=1e-4)
    assert np.allclose(-11.373895194717075, np.angle(solution.voltage[9], deg=True), atol=1e-4)

    # Checks if the converter's current limitation is well implemented, controlling Imax instead of Qac,
    # which originally was 5 MVAr.
    assert np.allclose(4.99999615809046, solution.St[27].real, atol=1e-4)
    assert np.allclose(2.628707079131246, solution.St[27].imag, atol=1e-4)
    assert np.allclose(1 + 0j, solution.voltage[21], atol=1e-4)


def test_hvdc_all_methods() -> None:
    """
    Checks that the HVDC logic is working for all power flow methods
    """
    fname = os.path.join('data', 'grids', '8_nodes_2_islands_hvdc.gridcal')
    grid = gce.open_file(fname)

    for solver_type in [SolverType.NR,
                        SolverType.LM,
                        SolverType.PowellDogLeg,
                        SolverType.IWAMOTO,
                        SolverType.FASTDECOUPLED,
                        SolverType.HELM,
                        SolverType.Linear,
                        SolverType.LACPF, ]:

        print(solver_type)

        options = PowerFlowOptions(solver_type,
                                   verbose=0,
                                   control_q=False,
                                   retry_with_other_methods=False)

        nc = gce.compile_numerical_circuit_at(
            grid,
            t_idx=None,
            apply_temperature=False,
            branch_tolerance_mode=gce.BranchImpedanceMode.Specified,
            opf_results=None,
            use_stored_guess=False,
            bus_dict=None,
            areas_dict=None,
            control_taps_modules=options.control_taps_modules,
            control_taps_phase=options.control_taps_phase,
            control_remote_voltage=options.control_remote_voltage,
        )

        logger = gce.Logger()
        res = multi_island_pf_nc(nc=nc, options=options, logger=logger)

        if not res.converged:
            logger.print(f"Errors on {solver_type.value}:")

        assert res.converged
        assert res.Pf_hvdc[0] == 10.0
        assert np.isclose(abs(res.voltage[6]), 1.01111, atol=1e-4)
        assert np.isclose(abs(res.voltage[1]), 1.02222, atol=1e-4)

    # repeat forcing to use the special formulations
    for solver_type in [SolverType.NR,
                        SolverType.LM,
                        SolverType.PowellDogLeg]:

        print(solver_type, "special solver")

        options = PowerFlowOptions(solver_type,
                                   verbose=0,
                                   control_q=False,
                                   retry_with_other_methods=False)

        nc = gce.compile_numerical_circuit_at(
            grid,
            t_idx=None,
            apply_temperature=False,
            branch_tolerance_mode=gce.BranchImpedanceMode.Specified,
            opf_results=None,
            use_stored_guess=False,
            bus_dict=None,
            areas_dict=None,
            control_taps_modules=options.control_taps_modules,
            control_taps_phase=options.control_taps_phase,
            control_remote_voltage=options.control_remote_voltage,
        )

        # force using the special formulations
        nc.active_branch_data._any_pf_control = True

        logger = gce.Logger()
        res = multi_island_pf_nc(nc=nc, options=options, logger=logger)

        if not res.converged:
            logger.print(f"Errors on {solver_type.value} with controls:")

        assert res.converged
        assert np.isclose(res.Pf_hvdc[0], 10.0)
        assert np.isclose(abs(res.voltage[6]), 1.01111, atol=1e-4)
        assert np.isclose(abs(res.voltage[1]), 1.02222, atol=1e-4)


# def test_reactive_power_splitting():
#     options = PowerFlowOptions(SolverType.NR,
#                                verbose=False,
#                                control_q=True,
#                                retry_with_other_methods=False)
#
#     fname = os.path.join('data', 'grids', 'case14.matpower')
#     grid = FileOpen(fname).open()
#
#     Qmin_gen = np.array([elm.Qmin for elm in grid.generators])
#     Qmax_gen = np.array([elm.Qmax for elm in grid.generators])
#
#     power_flow = PowerFlowDriver(grid, options)
#     power_flow.run()
#     res = power_flow.results
#
#     assert np.all(Qmin_gen <= res.gen_q)
#     assert np.all(res.gen_q <= Qmax_gen)


def test_bipolar_balanced() -> None:
    """
    Symmetric bipolar AC/DC system, 4 VSCs with Vm_dc + Pdc controls.
    Balanced poles drive the DC return cable to (essentially) zero current.
    """
    Ub = 220
    Sb = 100
    Rb = (Ub ** 2) / Sb
    rlin_23 = 0.01
    rlin_13 = 0.03

    grid = gce.MultiCircuit(name="Bipolar_balanced", Sbase=Sb)

    bus1 = gce.Bus(name="Bus1", Vnom=Ub, is_slack=True)
    grid.add_bus(bus1)
    bus2 = gce.Bus(name="Bus2", Vnom=Ub, is_dc=True)
    grid.add_bus(bus2)
    bus3 = gce.Bus(name="Bus3", Vnom=Ub, is_dc=True)
    grid.add_bus(bus3)
    bus4 = gce.Bus(name="Bus4", Vnom=Ub, is_dc=True, Vm0=1.01, Va0=3.14)
    grid.add_bus(bus4)
    bus5 = gce.Bus(name="Bus5", Vnom=Ub, is_dc=True, Va0=3.14)
    grid.add_bus(bus5)
    bus6 = gce.Bus(name="Bus6", Vnom=Ub, is_dc=True, is_grounded=True, Vm0=1e-9)
    grid.add_bus(bus6)
    bus7 = gce.Bus(name="Bus7", Vnom=Ub, is_dc=True, Vm0=1e-4)
    grid.add_bus(bus7)
    bus8 = gce.Bus(name="Bus8", Vnom=Ub, is_slack=True)
    grid.add_bus(bus8)

    grid.add_generator(bus1, gce.Generator(name='g1', vset=1.0))
    grid.add_generator(bus8, gce.Generator(name='g8', vset=1.0))

    grid.add_dc_line(gce.DcLine(name="dc_line_23", bus_from=bus2, bus_to=bus3, r=rlin_23 / Rb))
    grid.add_dc_line(gce.DcLine(name="dc_line_45", bus_from=bus4, bus_to=bus5, r=rlin_13 / Rb))
    grid.add_dc_line(gce.DcLine(name="dc_line_0", bus_from=bus6, bus_to=bus7, r=rlin_13 / Rb))

    alpha = 1e-4
    grid.add_vsc(gce.VSC(name="VSC_1", bus_from=bus2, bus_to=bus1, bus_dc_n=bus6,
                         alpha1=alpha, alpha2=alpha, alpha3=alpha,
                         control1=ConverterControlType.Vm_dc, control2=ConverterControlType.Qac,
                         control1_val=1, control2_val=0))
    grid.add_vsc(gce.VSC(name="VSC_2", bus_from=bus4, bus_to=bus1, bus_dc_n=bus6,
                         alpha1=alpha, alpha2=alpha, alpha3=alpha,
                         control1=ConverterControlType.Vm_dc, control2=ConverterControlType.Qac,
                         control1_val=-1.01, control2_val=0))
    grid.add_vsc(gce.VSC(name="VSC_3", bus_from=bus3, bus_to=bus8, bus_dc_n=bus7,
                         alpha1=alpha, alpha2=alpha, alpha3=alpha,
                         control1=ConverterControlType.Pdc, control2=ConverterControlType.Qac,
                         control1_val=30, control2_val=0))
    grid.add_vsc(gce.VSC(name="VSC_4", bus_from=bus5, bus_to=bus8, bus_dc_n=bus7,
                         alpha1=alpha, alpha2=alpha, alpha3=alpha,
                         control1=ConverterControlType.Pdc, control2=ConverterControlType.Qac,
                         control1_val=30, control2_val=0))

    options = gce.PowerFlowOptions(retry_with_other_methods=False, use_stored_guess=True)
    res = gce.power_flow(grid, options=options)

    assert res.converged

    expected_v = np.array([1.0 + 0.j,
                           1.0 + 0.j,
                           0.9999938 + 0.j,
                           -1.00999872 + 0.00160858j,
                           -1.00998031 + 0.00160858j,
                           0.0 + 0.j,
                           0.00003795 + 0.j,
                           1.0 + 0.j])
    assert np.allclose(res.voltage, expected_v, atol=1e-4)

    # VSC_3 / VSC_4 hold their Pdc=30 setpoint
    assert np.isclose(res.Pfp_vsc[2], 30.0, atol=1e-4)
    assert np.isclose(res.Pfp_vsc[3], 30.0, atol=1e-4)

    # Symmetry: poles carry equal power, return cable is idle
    assert np.isclose(res.Pfp_vsc[0], res.Pfp_vsc[1], atol=1e-3)
    assert abs(res.Pfn_vsc[0]) < 1e-3
    assert abs(res.Pfn_vsc[1]) < 1e-3


def test_bipolar_unbalanced() -> None:
    """
    Bipolar system with deliberately unbalanced pole loading
    """
    Ub = 345
    Sb = 100
    Ib = Sb / Ub
    r = 0.052
    a = 0.5515 / Sb
    b = 0.887 * (Ib / Sb)
    c = 3.77 * ((Ib ** 2) / Sb)

    grid = gce.MultiCircuit(name="Bipolar_unbalanced", Sbase=Sb)

    bus1 = gce.Bus(name="Bus1", Vnom=Ub, is_slack=True);
    grid.add_bus(bus1)
    bus2 = gce.Bus(name="Bus2", Vnom=Ub, is_dc=True);
    grid.add_bus(bus2)
    bus3 = gce.Bus(name="Bus3", Vnom=Ub, is_dc=True);
    grid.add_bus(bus3)
    bus4 = gce.Bus(name="Bus4", Vnom=Ub, is_dc=True, Vm0=1.01, Va0=3.14);
    grid.add_bus(bus4)
    bus5 = gce.Bus(name="Bus5", Vnom=Ub, is_dc=True, Va0=3.14);
    grid.add_bus(bus5)
    bus6 = gce.Bus(name="Bus6", Vnom=Ub, is_dc=True, is_grounded=True, Vm0=1e-9, Va0=0.01);
    grid.add_bus(bus6)
    bus7 = gce.Bus(name="Bus7", Vnom=Ub, is_dc=True, Vm0=1e-4, Va0=0.01);
    grid.add_bus(bus7)
    bus8 = gce.Bus(name="Bus8", Vnom=Ub, is_slack=True);
    grid.add_bus(bus8)
    bus9 = gce.Bus(name="Bus9", Vnom=Ub, is_dc=True);
    grid.add_bus(bus9)
    bus10 = gce.Bus(name="Bus10", Vnom=Ub, is_dc=True, Vm0=1e-4, Va0=0.01);
    grid.add_bus(bus10)
    bus11 = gce.Bus(name="Bus11", Vnom=Ub, is_dc=True, Va0=3.14);
    grid.add_bus(bus11)
    bus12 = gce.Bus(name="Bus12", Vnom=Ub, is_dc=True, Vm0=1e-4, Va0=0.01);
    grid.add_bus(bus12)
    bus13 = gce.Bus(name="Bus13", Vnom=Ub, is_dc=True, Va0=3.14);
    grid.add_bus(bus13)
    bus14 = gce.Bus(name="Bus14", Vnom=Ub);
    grid.add_bus(bus14)

    grid.add_generator(bus1, gce.Generator(name='g1', vset=1.0))
    grid.add_generator(bus8, gce.Generator(name='g8', vset=1.0))
    grid.add_load(bus14, gce.Load(name='Pl14', P=40))

    grid.add_dc_line(gce.DcLine(name="dc_line_29", bus_from=bus2, bus_to=bus9, r=r))
    grid.add_dc_line(gce.DcLine(name="dc_line_93", bus_from=bus9, bus_to=bus3, r=r))
    grid.add_dc_line(gce.DcLine(name="dc_line_411", bus_from=bus4, bus_to=bus11, r=r))
    grid.add_dc_line(gce.DcLine(name="dc_line_115", bus_from=bus11, bus_to=bus5, r=r))
    grid.add_dc_line(gce.DcLine(name="dc_line_610", bus_from=bus6, bus_to=bus10, r=r))
    grid.add_dc_line(gce.DcLine(name="dc_line_107", bus_from=bus10, bus_to=bus7, r=r))
    grid.add_dc_line(gce.DcLine(name="dc_line_1012", bus_from=bus10, bus_to=bus12, r=r))
    grid.add_dc_line(gce.DcLine(name="dc_line_1113", bus_from=bus11, bus_to=bus13, r=r))

    grid.add_vsc(gce.VSC(name="VSC_1", bus_from=bus2, bus_to=bus1, bus_dc_n=bus6,
                         alpha1=a, alpha2=b, alpha3=c,
                         control1=ConverterControlType.Vm_dc, control2=ConverterControlType.Qac,
                         control1_val=1, control2_val=0))
    grid.add_vsc(gce.VSC(name="VSC_2", bus_from=bus4, bus_to=bus1, bus_dc_n=bus6,
                         alpha1=a, alpha2=b, alpha3=c,
                         control1=ConverterControlType.Vm_dc, control2=ConverterControlType.Qac,
                         control1_val=-1.01, control2_val=0))
    grid.add_vsc(gce.VSC(name="VSC_3", bus_from=bus3, bus_to=bus8, bus_dc_n=bus7,
                         alpha1=a, alpha2=b, alpha3=c,
                         control1=ConverterControlType.Pdc, control2=ConverterControlType.Qac,
                         control1_val=19.6, control2_val=0))
    grid.add_vsc(gce.VSC(name="VSC_4", bus_from=bus5, bus_to=bus8, bus_dc_n=bus7,
                         alpha1=a, alpha2=b, alpha3=c,
                         control1=ConverterControlType.Pdc, control2=ConverterControlType.Qac,
                         control1_val=-2.8, control2_val=0))
    grid.add_vsc(gce.VSC(name="VSC_5", bus_from=bus13, bus_to=bus14, bus_dc_n=bus12,
                         alpha1=a, alpha2=b, alpha3=c,
                         control1=ConverterControlType.Vm_ac, control2=ConverterControlType.Va_ac,
                         control1_val=1, control2_val=0))

    options = gce.PowerFlowOptions(retry_with_other_methods=False, use_stored_guess=True)
    res = gce.power_flow(grid, options=options)

    assert res.converged

    # Voltage-controlled DC buses are honored
    assert np.isclose(abs(res.voltage[1]), 1.0, atol=1e-4)  # Bus2  (positive pole, Vm_dc=1)
    assert np.isclose(abs(res.voltage[3]), 1.01, atol=1e-4)  # Bus4  (negative pole, Vm_dc=-1.01)
    # AC slacks
    assert np.isclose(abs(res.voltage[0]), 1.0, atol=1e-4)
    assert np.isclose(abs(res.voltage[7]), 1.0, atol=1e-4)
    # VSC_5 enforces Vm_ac = 1.0 at Bus14
    assert np.isclose(abs(res.voltage[13]), 1.0, atol=1e-4)

    # Pdc setpoints honored on VSC_3 and VSC_4 (positive-pole DC injection)
    assert np.isclose(res.Pfp_vsc[2], 19.6, atol=1e-4)
    assert np.isclose(res.Pfp_vsc[3], -2.8, atol=1e-4)

    # Imbalance forces non-zero return-cable voltage drop on the negative side
    assert abs(res.voltage[9].real) > 1e-3  # Bus10
    assert abs(res.voltage[11].real) > 1e-3  # Bus12

    # Monopolar VSC_5 absorbs ~load + losses from the negative pole
    s_to_vsc5 = res.St_vsc[4]
    assert np.isclose(s_to_vsc5.real, -40.0, atol=1e-3)


def test_bipolar_with_load() -> None:
    """
    Bipolar AC/DC system where the receiving-end VSC is in Vac/theta_ac control
    """
    Ub = 345
    Sb = 100
    Ib = Sb / Ub
    r = 0.052
    a = 0.5515 / Sb
    b = 0.887 * (Ib / Sb)
    c = 3.77 * ((Ib ** 2) / Sb)

    grid = gce.MultiCircuit(name="Bipolar_with_load", Sbase=Sb)

    bus1 = gce.Bus(name="Bus1", Vnom=Ub, is_slack=True);
    grid.add_bus(bus1)
    bus2 = gce.Bus(name="Bus2", Vnom=Ub, is_dc=True);
    grid.add_bus(bus2)
    bus3 = gce.Bus(name="Bus3", Vnom=Ub, is_dc=True);
    grid.add_bus(bus3)
    bus4 = gce.Bus(name="Bus4", Vnom=Ub, is_dc=True, Vm0=1.01, Va0=3.14);
    grid.add_bus(bus4)
    bus5 = gce.Bus(name="Bus5", Vnom=Ub, is_dc=True, Vm0=1.01, Va0=3.14);
    grid.add_bus(bus5)
    bus6 = gce.Bus(name="Bus6", Vnom=Ub, is_dc=True, is_grounded=True, Vm0=1e-9, Va0=1e-9);
    grid.add_bus(bus6)
    bus7 = gce.Bus(name="Bus7", Vnom=Ub, is_dc=True, Vm0=1e-4, Va0=0.01);
    grid.add_bus(bus7)
    bus8 = gce.Bus(name="Bus8", Vnom=Ub);
    grid.add_bus(bus8)

    grid.add_generator(bus1, gce.Generator(name='g1', vset=1.0))
    grid.add_load(bus8, gce.Load(name='L8', P=80))

    grid.add_dc_line(gce.DcLine(name="dc_line_23", bus_from=bus2, bus_to=bus3, r=r))
    grid.add_dc_line(gce.DcLine(name="dc_line_45", bus_from=bus4, bus_to=bus5, r=r))
    grid.add_dc_line(gce.DcLine(name="dc_line_0", bus_from=bus6, bus_to=bus7, r=r))

    grid.add_vsc(gce.VSC(name="VSC_1", bus_from=bus2, bus_to=bus1, bus_dc_n=bus6,
                         alpha1=a, alpha2=b, alpha3=c,
                         control1=ConverterControlType.Vm_dc, control2=ConverterControlType.Qac,
                         control1_val=1, control2_val=0))
    grid.add_vsc(gce.VSC(name="VSC_2", bus_from=bus4, bus_to=bus1, bus_dc_n=bus6,
                         alpha1=a, alpha2=b, alpha3=c,
                         control1=ConverterControlType.Vm_dc, control2=ConverterControlType.Qac,
                         control1_val=-1.01, control2_val=0))
    grid.add_vsc(gce.VSC(name="VSC_3", bus_from=bus3, bus_to=bus8, bus_dc_n=bus7,
                         alpha1=a, alpha2=b, alpha3=c,
                         control1=ConverterControlType.Pdc, control2=ConverterControlType.Qac,
                         control1_val=40, control2_val=0))
    grid.add_vsc(gce.VSC(name="VSC_4", bus_from=bus5, bus_to=bus8, bus_dc_n=bus7,
                         alpha1=a, alpha2=b, alpha3=c,
                         control1=ConverterControlType.Vm_ac, control2=ConverterControlType.Va_ac,
                         control1_val=1, control2_val=0))

    options = gce.PowerFlowOptions(retry_with_other_methods=False, use_stored_guess=True)
    res = gce.power_flow(grid, options=options)

    assert res.converged

    # Vm_dc setpoints honored on the controlled DC buses
    assert np.isclose(abs(res.voltage[1]), 1.0, atol=1e-4)  # Bus2 (Vm_dc=1)
    assert np.isclose(abs(res.voltage[3]), 1.01, atol=1e-4)  # Bus4 (Vm_dc=-1.01)
    # VSC_4 acts as AC slack at Bus8
    assert np.isclose(abs(res.voltage[7]), 1.0, atol=1e-4)
    assert np.isclose(np.angle(res.voltage[7]), 0.0, atol=1e-4)

    # VSC_3 holds Pdc=40 setpoint
    assert np.isclose(res.Pfp_vsc[2], 40.0, atol=1e-4)

    # The metallic return carries only negligible power. A small imbalance 
    # current flows, the returned power P = V_neutral * I stays near zero. 
    # The neutral subsystem is ill-conditioned (near-zero voltages),
    # hence a loose tolerance rather than 0
    assert np.allclose(res.Pfn_vsc, 0.0, atol=1e-3)

    # Power balance: load = 80 MW, generation covers load + losses
    p_gen = res.Sbus[0].real
    losses = res.losses_vsc.sum() + res.losses[:3].real.sum()
    assert np.isclose(p_gen, 80.0 + losses, atol=1e-2)


if __name__ == "__main__":
    # test_power_flow_12bus_acdc()
    # test_hvdc_all_methods()
    test_voltage_control_with_ltc()
