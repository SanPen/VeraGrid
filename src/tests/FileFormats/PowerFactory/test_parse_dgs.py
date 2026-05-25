# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import os
import pandas as pd
import numpy as np

import VeraGridEngine.Devices as dev
from VeraGridEngine.IO.file_open import FileOpen
from VeraGridEngine.Simulations.PowerFlow.power_flow_worker import PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import SolverType
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.IO.dgs.veragrid_to_dgs import circuit_to_dgs

def test_dgs_ieee_grids():
    files = [
        ('IEEE14_test.dgs', 'IEEE 14 bus.sav.xlsx'),
        ('IEEE30_test.dgs', 'IEEE 30 bus.sav.xlsx'),
        ('IEEE118_v2_test.dgs', 'IEEE 118 Bus.sav.xlsx'),
    ]

    data_dir = os.path.join("data")
    for solver_type in [SolverType.NR,
                        SolverType.IWAMOTO,
                        SolverType.LM,
                        SolverType.FASTDECOUPLED,
                        SolverType.PowellDogLeg,
                        SolverType.HELM]:

        options = PowerFlowOptions(solver_type,
                                   verbose=0,
                                   control_q=False,
                                   retry_with_other_methods=False)

        for f1, f2 in files:
            fname = os.path.join(data_dir, "grids", "DGS", f1)
            main_circuit = FileOpen(fname).open()
            power_flow = PowerFlowDriver(main_circuit, options)
            power_flow.run()

            results_file = os.path.join(data_dir, "results", f2)
            df_v = pd.read_excel(results_file, sheet_name='Vabs', index_col=0)
            df_p = pd.read_excel(results_file, sheet_name='Pbranch', index_col=0)

            v_gc = np.abs(power_flow.results.voltage)
            v_psse = df_v.values[:, 0]
            p_gc = power_flow.results.Sf.real
            p_psse = df_p.values[:, 0]

            v_ok = np.allclose(v_gc, v_psse, atol=1e-4)
            flow_ok = np.allclose(p_gc, p_psse, atol=1e-2)

            assert v_ok
            assert flow_ok

        print(solver_type, 'ok')

def test_roundtrip_raw_to_dgs_to_dgs_ieee_grids():
    """
    Roundtrip test:
      RAW -> powerflow (res1)
      export to DGS
      import same DGS -> powerflow (res2)
      check res1 == res2 (Vabs and Pbranch) with same tolerances as the RAW-vs-PSS/E test
    """

    files = [
        ('IEEE 14 bus.raw', 'IEEE 14 bus.sav.xlsx'),
        ('IEEE 30 bus.raw', 'IEEE 30 bus.sav.xlsx'),
        ('IEEE 118 Bus v2.raw', 'IEEE 118 Bus.sav.xlsx'),
    ]


    out_dir = os.path.join("data", "grids", "DGS", "_roundtrip_tmp")
    os.makedirs(out_dir, exist_ok=True)

    for solver_type in [SolverType.NR,
                        SolverType.IWAMOTO,
                        SolverType.LM,
                        SolverType.FASTDECOUPLED,
                        SolverType.PowellDogLeg,
                        SolverType.HELM]:

        options = PowerFlowOptions(solver_type,
                                   verbose=0,
                                   control_q=False,
                                   retry_with_other_methods=False)

        for f1, _ in files:
            raw_path = os.path.join("data", "grids", "RAW", f1)
            main_circuit = FileOpen(raw_path).open()

            pf1 = PowerFlowDriver(main_circuit, options)
            pf1.run()

            v1 = np.abs(pf1.results.voltage)
            p1 = pf1.results.Sf.real

            # export to dgs (same logic as FileHandler.save_dgs)
            dgs_path = os.path.join(out_dir, f1.replace('.raw', f'__{solver_type.name}.dgs'))
            dgs = circuit_to_dgs(grid=main_circuit)
            dgs.write_dgs(path=dgs_path)

            # import the same dgs and run again
            rt_circuit = FileOpen(dgs_path).open()

            pf2 = PowerFlowDriver(rt_circuit, options)
            pf2.run()

            v2 = np.abs(pf2.results.voltage)
            p2 = pf2.results.Sf.real

            v_ok = np.allclose(v1, v2, atol=1e-4)
            flow_ok = np.allclose(p1, p2, atol=1e-2)
            assert v_ok
            assert flow_ok

        print(solver_type, 'ok')


def test_circuit_to_dgs_uses_profile_values_when_t_idx_is_provided() -> None:
    """DGS export must use profile values when ``t_idx`` is provided."""

    grid: dev.MultiCircuit = dev.MultiCircuit(name="profile-export")

    bus_1: dev.Bus = dev.Bus(name="B1", Vnom=110.0, active=True)
    bus_2: dev.Bus = dev.Bus(name="B2", Vnom=110.0, active=True)
    bus_1.active_prof = np.array([True, False])
    grid.add_bus(bus_1)
    grid.add_bus(bus_2)

    load: dev.Load = dev.Load(name="LD1", P=10.0, Q=2.0, active=True)
    load.P_prof = np.array([12.0, 22.0])
    load.Q_prof = np.array([3.0, 5.0])
    load.active_prof = np.array([True, False])
    grid.add_load(bus=bus_1, api_obj=load)

    line: dev.Line = dev.Line(
        bus_from=bus_1,
        bus_to=bus_2,
        name="L12",
        r=0.01,
        x=0.05,
        b=0.001,
        rate=100.0,
        active=True,
    )
    line.rate_prof = np.array([120.0, 220.0])
    line.active_prof = np.array([True, False])
    grid.add_line(line)

    switch: dev.Switch = dev.Switch(
        bus_from=bus_1,
        bus_to=bus_2,
        name="SW12",
        rate=80.0,
        active=True,
        rated_current=0.0,
    )
    switch.rate_prof = np.array([90.0, 180.0])
    switch.active_prof = np.array([True, False])
    grid.add_switch(switch)

    snapshot_export = circuit_to_dgs(grid=grid, t_idx=None)
    profile_export = circuit_to_dgs(grid=grid, t_idx=1)

    snapshot_line_current: float = 100.0 / (np.sqrt(3.0) * 110.0)
    profile_line_current: float = 220.0 / (np.sqrt(3.0) * 110.0)
    snapshot_switch_current: float = 80.0 / (np.sqrt(3.0) * 110.0)
    profile_switch_current: float = 180.0 / (np.sqrt(3.0) * 110.0)

    assert snapshot_export.elmterms[0].outserv == 0
    assert profile_export.elmterms[0].outserv == 1

    assert snapshot_export.elmlods[0].plini == 10.0
    assert profile_export.elmlods[0].plini == 22.0
    assert snapshot_export.elmlods[0].qlini == 2.0
    assert profile_export.elmlods[0].qlini == 5.0
    assert snapshot_export.elmlods[0].outserv == 0
    assert profile_export.elmlods[0].outserv == 1

    assert np.isclose(snapshot_export.typlnes[0].InomAir, snapshot_line_current)
    assert np.isclose(profile_export.typlnes[0].InomAir, profile_line_current)
    assert snapshot_export.elmlnes[0].outserv == 0
    assert profile_export.elmlnes[0].outserv == 1

    assert np.isclose(snapshot_export.typswitches[0].InomA, snapshot_switch_current)
    assert np.isclose(profile_export.typswitches[0].InomA, profile_switch_current)
    assert snapshot_export.elmcoups[0].on_off == 1
    assert profile_export.elmcoups[0].on_off == 0
