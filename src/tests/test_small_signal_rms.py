from __future__ import annotations

import numpy as np

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Branches.line import Line

from VeraGridEngine.Utils.Symbolic.block_solver import BlockSolver
from VeraGridEngine.Simulations.Rms.initialization import initialize_rms
from VeraGridEngine.Simulations.SmallSignalStability.small_signal_driver import run_small_signal_stability
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowResults, PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
import VeraGridEngine.api as gce


def stability_kundur_no_shunt():
    grid = gce.MultiCircuit()

    # Buses
    bus1 = Bus(name="Bus1", Vnom=20)
    bus2 = Bus(name="Bus2", Vnom=20)
    bus3 = Bus(name="Bus3", Vnom=20, is_slack=True)
    bus4 = Bus(name="Bus4", Vnom=20)
    bus5 = Bus(name="Bus5", Vnom=230)
    bus6 = Bus(name="Bus6", Vnom=230)
    bus7 = Bus(name="Bus7", Vnom=230)
    bus8 = Bus(name="Bus8", Vnom=230)
    bus9 = Bus(name="Bus9", Vnom=230)
    bus10 = Bus(name="Bus10", Vnom=230)
    bus11 = Bus(name="Bus11", Vnom=230)

    grid.add_bus(bus1)
    grid.add_bus(bus2)
    grid.add_bus(bus3)
    grid.add_bus(bus4)
    grid.add_bus(bus5)
    grid.add_bus(bus6)
    grid.add_bus(bus7)
    grid.add_bus(bus8)
    grid.add_bus(bus9)
    grid.add_bus(bus10)
    grid.add_bus(bus11)

    # Line

    line0 = grid.add_line(
        Line(name="line 5-6-1", bus_from=bus5, bus_to=bus6,
             r=0.00500, x=0.05000, b=0.02187, rate=750.0))

    line1 = grid.add_line(
        Line(name="line 5-6-2", bus_from=bus5, bus_to=bus6,
             r=0.00500, x=0.05000, b=0.02187, rate=750.0))

    line2 = grid.add_line(
        Line(name="line 6-7-1", bus_from=bus6, bus_to=bus7,
             r=0.00300, x=0.03000, b=0.00583, rate=700.0))

    line3 = grid.add_line(
        Line(name="line 6-7-2", bus_from=bus6, bus_to=bus7,
             r=0.00300, x=0.03000, b=0.00583, rate=700.0))

    line4 = grid.add_line(
        Line(name="line 6-7-3", bus_from=bus6, bus_to=bus7,
             r=0.00300, x=0.03000, b=0.00583, rate=700.0))

    line5 = grid.add_line(
        Line(name="line 7-8-1", bus_from=bus7, bus_to=bus8,
             r=0.01100, x=0.11000, b=0.19250, rate=400.0))

    line6 = grid.add_line(
        Line(name="line 7-8-2", bus_from=bus7, bus_to=bus8,
             r=0.01100, x=0.11000, b=0.19250, rate=400.0))

    line7 = grid.add_line(
        Line(name="line 8-9-1", bus_from=bus8, bus_to=bus9,
             r=0.01100, x=0.11000, b=0.19250, rate=400.0))

    line8 = grid.add_line(
        Line(name="line 8-9-2", bus_from=bus8, bus_to=bus9,
             r=0.01100, x=0.11000, b=0.19250, rate=400.0))

    line9 = grid.add_line(
        Line(name="line 9-10-1", bus_from=bus9, bus_to=bus10,
             r=0.00300, x=0.03000, b=0.00583, rate=700.0))

    line10 = grid.add_line(
        Line(name="line 9-10-2", bus_from=bus9, bus_to=bus10,
             r=0.00300, x=0.03000, b=0.00583, rate=700.0))

    line11 = grid.add_line(
        Line(name="line 9-10-3", bus_from=bus9, bus_to=bus10,
             r=0.00300, x=0.03000, b=0.00583, rate=700.0))

    line12 = grid.add_line(
        Line(name="line 10-11-1", bus_from=bus10, bus_to=bus11,
             r=0.00500, x=0.05000, b=0.02187, rate=750.0))

    line13 = grid.add_line(
        Line(name="line 10-11-2", bus_from=bus10, bus_to=bus11,
             r=0.00500, x=0.05000, b=0.02187, rate=750.0))

    # Transformers
    xt1 = 0.15 * (100.0 / 900.0)
    trafo_G1 = grid.add_line(
        Line(name="trafo 5-1", bus_from=bus5, bus_to=bus1,
             r=0.00000, x=xt1, b=0.0, rate=900.0))

    trafo_G2 = grid.add_line(
        Line(name="trafo 6-2", bus_from=bus6, bus_to=bus2,
             r=0.00000, x=0.15 * (100.0 / 900.0), b=0.0, rate=900.0))

    trafo_G3 = grid.add_line(
        Line(name="trafo 11-3", bus_from=bus11, bus_to=bus3,
             r=0.00000, x=0.15 * (100.0 / 900.0), b=0.0, rate=900.0))

    trafo_G4 = grid.add_line(
        Line(name="trafo 10-4", bus_from=bus10, bus_to=bus4,
             r=0.00000, x=0.15 * (100.0 / 900.0), b=0.0, rate=900.0))

    # load
    load1 = Load(name="load1", P=967.0, Q=100.0, Pl0=-9.670000000007317, Ql0=-0.9999999999967969)
    load1_grid = grid.add_load(bus=bus7, api_obj=load1)

    load2 = Load(name="load2", P=1767.0, Q=100.0, Pl0=-17.6699999999199, Ql0=-0.999999999989467)
    load2_grid = grid.add_load(bus=bus9, api_obj=load2)

    # Generators
    fn_1 = 60.0
    M_1 = 13.0 * 9.0
    D_1 = 10.0 * 9.0
    ra_1 = 0.0
    xd_1 = 0.3 * 100.0 / 900.0
    omega_ref_1 = 1.0
    Kp_1 = 0.0
    Ki_1 = 0.0

    fn_2 = 60.0
    M_2 = 13.0 * 9.0
    D_2 = 10.0 * 9.0
    ra_2 = 0.0
    xd_2 = 0.3 * 100.0 / 900.0
    omega_ref_2 = 1.0
    Kp_2 = 0.0
    Ki_2 = 0.0

    fn_3 = 60.0
    M_3 = 12.35 * 9.0
    D_3 = 10.0 * 9.0
    ra_3 = 0.0
    xd_3 = 0.3 * 100.0 / 900.0
    omega_ref_3 = 1.0
    Kp_3 = 0.0
    Ki_3 = 0.0

    fn_4 = 60.0
    M_4 = 12.35 * 9.0
    D_4 = 10.0 * 9.0
    ra_4 = 0.0
    xd_4 = 0.3 * 100.0 / 900.0
    omega_ref_4 = 1.0
    Kp_4 = 0.0
    Ki_4 = 0.0

    # Generators
    gen1 = Generator(
        name="Gen1", P=700.0, vset=1.03, Snom=900.0,
        x1=xd_1, r1=ra_1, freq=fn_1,
        tm0=6.999999999999999,
        vf=1.1410480598099169,
        M=M_1, D=D_1,
        omega_ref=omega_ref_1,
        Kp=Kp_1, Ki=Ki_1
    )

    gen2 = Generator(
        name="Gen2", P=700.0, vset=1.01, Snom=900.0,
        x1=xd_2, r1=ra_2, freq=fn_2,
        tm0=6.999999999999998,
        vf=1.1801018702912192,
        M=M_2, D=D_2,
        omega_ref=omega_ref_2,
        Kp=Kp_2, Ki=Ki_2
    )

    gen3 = Generator(
        name="Gen3", P=719.091, vset=1.03, Snom=900.0,
        x1=xd_3, r1=ra_3, freq=fn_3,
        tm0=7.331838148595014,
        vf=1.15513088317088697,
        M=M_3, D=D_3,
        omega_ref=omega_ref_3,
        Kp=Kp_3, Ki=Ki_3
    )

    gen4 = Generator(
        name="Gen4", P=700.0, vset=1.01, Snom=900.0,
        x1=xd_4, r1=ra_4, freq=fn_4,
        tm0=6.999999999999998,
        vf=1.2028207647478641,
        M=M_4, D=D_4,
        omega_ref=omega_ref_4,
        Kp=Kp_4, Ki=Ki_4
    )

    grid.add_generator(bus=bus1, api_obj=gen1)
    grid.add_generator(bus=bus2, api_obj=gen2)
    grid.add_generator(bus=bus3, api_obj=gen3)
    grid.add_generator(bus=bus4, api_obj=gen4)

    pf_options = PowerFlowOptions(
        solver_type=gce.SolverType.NR,
        retry_with_other_methods=False,
        verbose=0,
        initialize_with_existing_solution=True,
        tolerance=1e-6,
        max_iter=25,
        control_q=False,
        control_taps_modules=True,
        control_taps_phase=True,
        control_remote_voltage=True,
        orthogonalize_controls=True,
        apply_temperature_correction=True,
        branch_impedance_tolerance_mode=gce.BranchImpedanceMode.Specified,
        distributed_slack=False,
        ignore_single_node_islands=False,
        trust_radius=1.0,
        backtracking_parameter=0.05,
        use_stored_guess=False,
        initialize_angles=False,
        generate_report=False,
    )
    power_flow = PowerFlowDriver(grid, pf_options)
    power_flow.run()
    res = power_flow.results

    sim_time, ss, init_guess = initialize_rms(grid, res, use_init_values=False)

    params_mapping = {}

    slv = BlockSolver(ss, sim_time, use_jit=False)
    params0 = slv.build_init_params_vector(params_mapping)
    x0 = slv.build_init_vars_vector_from_uid(init_guess)

    (Eigenvalues,
     PFactors,
     damping_ratios,
     conjugate_frequencies,
     state_matrix) = run_small_signal_stability(slv=slv,
                                                x=x0,
                                                time=0,
                                                verbose=1)

    return Eigenvalues, PFactors


def test_eigenvalues():
    eig_Andes = np.array([-0.3937577370228531 + 7.237668249952536j, -0.3937577370228531 - 7.237668249952536j,
                          -0.39578162845152476 + 7.10610769053952j, -0.39578162845152476 - 7.10610769053952j,
                          -0.393088827518491 + 2.7838009459248343j, -0.393088827518491 - 2.7838009459248343j,
                          -0.7926383508563992 + 0j, 2.8393441106828003e-14 + 0j])

    eig_VeraGrid, pfactors_VeraGrid = stability_kundur_no_shunt()
    eig_VeraGrid_ord = eig_VeraGrid[np.argsort(-np.abs(eig_VeraGrid))]

    equal = False
    if len(eig_Andes) == len(eig_VeraGrid_ord):
        equal = np.allclose(eig_Andes, eig_VeraGrid_ord, atol=1e-3)

    assert equal


def test_participation_factors():
    pfactors_Andes = np.array([[0.1228500000, 0.1228500000, 0.1021600000, 0.1021600000, 0.1731400000, 0.1731400000,
                                0.1942900000, 0.0058800000],
                               [0.1513000000, 0.1513000000, 0.1220100000, 0.1220100000, 0.1164300000, 0.1164300000,
                                0.2107700000, 0.0063900000],
                               [0.1027000000, 0.1027000000, 0.1565200000, 0.1565200000, 0.1016100000, 0.1016100000,
                                0.2798000000, 0.0059200000],
                               [0.1231400000, 0.1231400000, 0.1193200000, 0.1193200000, 0.1072800000, 0.1072800000,
                                0.3021900000, 0.0064000000],
                               [0.1232400000, 0.1232400000, 0.1024900000, 0.1024900000, 0.1738200000, 0.1738200000,
                                0.0000000000, 0.1997800000],
                               [0.1517800000, 0.1517800000, 0.1224000000, 0.1224000000, 0.1168900000, 0.1168900000,
                                0.0000000000, 0.2169300000],
                               [0.1040300000, 0.1040300000, 0.1585600000, 0.1585600000, 0.1028200000, 0.1028200000,
                                0.0000000000, 0.2784500000],
                               [0.1217000000, 0.1217000000, 0.1179300000, 0.1179300000, 0.1059200000, 0.1059200000,
                                0.0000000000, 0.2934000000]])
    eig_VeraGrid, pfactors_VeraGrid = stability_kundur_no_shunt()

    order_rows = [0, 2, 4, 6, 1, 3, 5, 7]
    pfactors_VeraGrid_ord = pfactors_VeraGrid[order_rows, :]

    equal = False
    if pfactors_Andes.shape == pfactors_VeraGrid_ord.shape:
        equal = np.allclose(pfactors_Andes, pfactors_VeraGrid_ord, atol=1e-2)

    assert equal


if __name__ == '__main__':
    test_eigenvalues()
    test_participation_factors()
