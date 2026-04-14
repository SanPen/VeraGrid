import VeraGridEngine.api as vge
from VeraGridEngine import ShuntConnectionType, SolverType
import numpy as np


def test_unconnected_impedance_groundedstar_3ph():
    '''
    This test executes a three-phase power flow into a three-phase impedance load connected in GroundedStar,
    which the bus it is connected to does not have the phase a.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = vge.Logger()
    grid = vge.MultiCircuit()

    # -----------------------------------------------------------------------------------------------------------------
    # Buses
    # -----------------------------------------------------------------------------------------------------------------
    bus_slack = vge.Bus(name='Slack Bus ABC', xpos=0, ypos=0)
    bus_slack.is_slack = True
    grid.add_bus(obj=bus_slack)

    bus_middle = vge.Bus(name='Middle Bus CB', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_middle)

    bus_load = vge.Bus(name='Load Bus CB', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_load)

    # -----------------------------------------------------------------------------------------------------------------
    # Generator
    # -----------------------------------------------------------------------------------------------------------------
    gen = vge.Generator()
    grid.add_generator(bus=bus_slack, api_obj=gen)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load = vge.Load(G1=1.0,
                    B1=-0.5,
                    G2=1.0,
                    B2=-0.5,
                    G3=1.0,
                    B3=-0.5)
    load.conn = ShuntConnectionType.GroundedStar
    grid.add_load(bus=bus_load, api_obj=load)

    # -----------------------------------------------------------------------------------------------------------------
    # Lines
    # -----------------------------------------------------------------------------------------------------------------
    z_abc = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_abc = np.array([
        [1j * 6.0, -1j * 1.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0, -1j * 1.0],
        [-1j * 1.0, -1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_abc = vge.create_known_abc_overhead_template(name='Three-phase line',
                                                               z_nabc=z_abc,
                                                               ysh_nabc=y_abc,
                                                               phases=np.array([1, 2, 3]),
                                                               Vnom=10.0)
    grid.add_overhead_line(configuration_abc)

    line_3ph = vge.Line(bus_from=bus_slack,
                        bus_to=bus_middle)
    line_3ph.apply_template(configuration_abc, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_3ph)

    z_cb = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_cb = np.array([
        [1j * 6.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_cb = vge.create_known_abc_overhead_template(name='Two-phase line',
                                                              z_nabc=z_cb,
                                                              ysh_nabc=y_cb,
                                                              phases=np.array([2, 3]),
                                                              Vnom=10.0)
    grid.add_overhead_line(configuration_cb)

    line_2ph = vge.Line(bus_from=bus_middle,
                        bus_to=bus_load)
    line_2ph.apply_template(configuration_cb, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_2ph)

    # -----------------------------------------------------------------------------------------------------------------
    # Power Flow
    # -----------------------------------------------------------------------------------------------------------------
    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array(
        [1.0, 1.00910, 0.0])

    Ub_reference = np.array(
        [1.0, 0.97302, 0.94616])

    Uc_reference = np.array(
        [1.0, 0.98839, 0.97750])

    assert np.allclose(abs(res.voltage_A), Ua_reference, atol=1e-5)
    assert np.allclose(abs(res.voltage_B), Ub_reference, atol=1e-5)
    assert np.allclose(abs(res.voltage_C), Uc_reference, atol=1e-5)


# def test_unconnected_impedance_floatingstar_3ph():
#     '''
#     This test executes a three-phase power flow into a three-phase impedance load connected in FloatingStar,
#     which the bus it is connected to does not have the phase a.
#     The obtained results are compared against the ones obtained in OpenDSS.
#     '''
#
#     logger = vge.Logger()
#     grid = vge.MultiCircuit()
#
#     # -----------------------------------------------------------------------------------------------------------------
#     # Buses
#     # -----------------------------------------------------------------------------------------------------------------
#     bus_slack = vge.Bus(name='Slack Bus ABC', xpos=0, ypos=0)
#     bus_slack.is_slack = True
#     grid.add_bus(obj=bus_slack)
#
#     bus_middle = vge.Bus(name='Middle Bus CB', xpos=1000, ypos=0)
#     grid.add_bus(obj=bus_middle)
#
#     bus_load = vge.Bus(name='Load Bus CB', xpos=1000, ypos=0)
#     grid.add_bus(obj=bus_load)
#
#     # -----------------------------------------------------------------------------------------------------------------
#     # Generator
#     # -----------------------------------------------------------------------------------------------------------------
#     gen = vge.Generator()
#     grid.add_generator(bus=bus_slack, api_obj=gen)
#
#     # ----------------------------------------------------------------------------------------------------------------------
#     # Load
#     # ----------------------------------------------------------------------------------------------------------------------
#     load = vge.Load(G1=1.0,
#                     B1=-0.5,
#                     G2=1.0,
#                     B2=-0.5,
#                     G3=1.0,
#                     B3=-0.5)
#     load.conn = ShuntConnectionType.FloatingStar
#     grid.add_load(bus=bus_load, api_obj=load)
#
#     # -----------------------------------------------------------------------------------------------------------------
#     # Lines
#     # -----------------------------------------------------------------------------------------------------------------
#     z_abc = np.array([
#         [0.3 + 1j * 1.0, 0.1 + 1j * 0.4, 0.1 + 1j * 0.4],
#         [0.1 + 1j * 0.4, 0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
#         [0.1 + 1j * 0.4, 0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
#     ], dtype=complex)  # Ω/km
#
#     y_abc = np.array([
#         [1j * 6.0, -1j * 1.0, -1j * 1.0],
#         [-1j * 1.0, 1j * 6.0, -1j * 1.0],
#         [-1j * 1.0, -1j * 1.0, 1j * 6.0]
#     ], dtype=complex) / (10 ** 6)  # S/km
#
#     configuration_abc = vge.create_known_abc_overhead_template(name='Three-phase line',
#                                                                z_nabc=z_abc,
#                                                                ysh_nabc=y_abc,
#                                                                phases=np.array([1, 2, 3]),
#                                                                Vnom=10.0)
#     grid.add_overhead_line(configuration_abc)
#
#     line_3ph = vge.Line(bus_from=bus_slack,
#                         bus_to=bus_middle)
#     line_3ph.apply_template(configuration_abc, grid.Sbase, grid.fBase, logger)
#     grid.add_line(obj=line_3ph)
#
#     z_cb = np.array([
#         [0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
#         [0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
#     ], dtype=complex)  # Ω/km
#
#     y_cb = np.array([
#         [1j * 6.0, -1j * 1.0],
#         [-1j * 1.0, 1j * 6.0]
#     ], dtype=complex) / (10 ** 6)  # S/km
#
#     configuration_cb = vge.create_known_abc_overhead_template(name='Two-phase line',
#                                                               z_nabc=z_cb,
#                                                               ysh_nabc=y_cb,
#                                                               phases=np.array([2, 3]),
#                                                               Vnom=10.0)
#     grid.add_overhead_line(configuration_cb)
#
#     line_2ph = vge.Line(bus_from=bus_middle,
#                         bus_to=bus_load)
#     line_2ph.apply_template(configuration_cb, grid.Sbase, grid.fBase, logger)
#     grid.add_line(obj=line_2ph)
#
#     # -----------------------------------------------------------------------------------------------------------------
#     # Power Flow
#     # -----------------------------------------------------------------------------------------------------------------
#     res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
#                                                                     retry_with_other_methods=False))
#
#     Ua_reference = np.array(
#         [1.0, 1.00910, 0.0])
#
#     Ub_reference = np.array(
#         [1.0, 0.97302, 0.94616])
#
#     Uc_reference = np.array(
#         [1.0, 0.98839, 0.97750])
#
#     assert np.allclose(abs(res.voltage_A), Ua_reference, atol=1e-5)
#     assert np.allclose(abs(res.voltage_B), Ub_reference, atol=1e-5)
#     assert np.allclose(abs(res.voltage_C), Uc_reference, atol=1e-5)



def test_unconnected_impedance_groundedstar_1ph():
    '''
    This test executes a three-phase power flow into a single-phase impedance load connected in GroundedStar,
    which the bus it is connected to does not have the phase a.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = vge.Logger()
    grid = vge.MultiCircuit()

    # -----------------------------------------------------------------------------------------------------------------
    # Buses
    # -----------------------------------------------------------------------------------------------------------------
    bus_slack = vge.Bus(name='Slack Bus ABC', xpos=0, ypos=0)
    bus_slack.is_slack = True
    grid.add_bus(obj=bus_slack)

    bus_middle = vge.Bus(name='Middle Bus CB', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_middle)

    bus_load = vge.Bus(name='Load Bus CB', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_load)

    # -----------------------------------------------------------------------------------------------------------------
    # Generator
    # -----------------------------------------------------------------------------------------------------------------
    gen = vge.Generator()
    grid.add_generator(bus=bus_slack, api_obj=gen)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load = vge.Load(G1=1.0,
                    B1=-0.5)
    load.conn = ShuntConnectionType.GroundedStar
    grid.add_load(bus=bus_load, api_obj=load)

    # -----------------------------------------------------------------------------------------------------------------
    # Lines
    # -----------------------------------------------------------------------------------------------------------------
    z_abc = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_abc = np.array([
        [1j * 6.0, -1j * 1.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0, -1j * 1.0],
        [-1j * 1.0, -1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_abc = vge.create_known_abc_overhead_template(name='Three-phase line',
                                                               z_nabc=z_abc,
                                                               ysh_nabc=y_abc,
                                                               phases=np.array([1, 2, 3]),
                                                               Vnom=10.0)
    grid.add_overhead_line(configuration_abc)

    line_3ph = vge.Line(bus_from=bus_slack,
                        bus_to=bus_middle)
    line_3ph.apply_template(configuration_abc, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_3ph)

    z_cb = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_cb = np.array([
        [1j * 6.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_cb = vge.create_known_abc_overhead_template(name='Two-phase line',
                                                              z_nabc=z_cb,
                                                              ysh_nabc=y_cb,
                                                              phases=np.array([2, 3]),
                                                              Vnom=10.0)
    grid.add_overhead_line(configuration_cb)

    line_2ph = vge.Line(bus_from=bus_middle,
                        bus_to=bus_load)
    line_2ph.apply_template(configuration_cb, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_2ph)

    # -----------------------------------------------------------------------------------------------------------------
    # Power Flow
    # -----------------------------------------------------------------------------------------------------------------
    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array(
        [1.0, 1.0, 0.0])

    Ub_reference = np.array(
        [1.0, 1.0, 1.0])

    Uc_reference = np.array(
        [1.0, 1.0, 1.0])

    assert np.allclose(abs(res.voltage_A), Ua_reference, atol=1e-5)
    assert np.allclose(abs(res.voltage_B), Ub_reference, atol=1e-5)
    assert np.allclose(abs(res.voltage_C), Uc_reference, atol=1e-5)


def test_unconnected_current_groundedstar_3ph():
    '''
    This test executes a three-phase power flow into a three-phase current load connected in GroundedStar,
    which the bus it is connected to does not have the phase c.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = vge.Logger()
    grid = vge.MultiCircuit()

    # -----------------------------------------------------------------------------------------------------------------
    # Buses
    # -----------------------------------------------------------------------------------------------------------------
    bus_slack = vge.Bus(name='Slack Bus ABC', xpos=0, ypos=0)
    bus_slack.is_slack = True
    grid.add_bus(obj=bus_slack)

    bus_middle = vge.Bus(name='Middle Bus AB', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_middle)

    bus_load = vge.Bus(name='Load Bus AB', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_load)

    # -----------------------------------------------------------------------------------------------------------------
    # Generator
    # -----------------------------------------------------------------------------------------------------------------
    gen = vge.Generator()
    grid.add_generator(bus=bus_slack, api_obj=gen)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load = vge.Load(Ir1=1.0,
                    Ii1=-0.5,
                    Ir2=1.0,
                    Ii2=-0.5,
                    Ir3=1.0,
                    Ii3=-0.5)
    load.conn = ShuntConnectionType.GroundedStar
    grid.add_load(bus=bus_load, api_obj=load)

    # -----------------------------------------------------------------------------------------------------------------
    # Lines
    # -----------------------------------------------------------------------------------------------------------------
    z_abc = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_abc = np.array([
        [1j * 6.0, -1j * 1.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0, -1j * 1.0],
        [-1j * 1.0, -1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_abc = vge.create_known_abc_overhead_template(name='Three-phase line',
                                                               z_nabc=z_abc,
                                                               ysh_nabc=y_abc,
                                                               phases=np.array([1, 2, 3]),
                                                               Vnom=10.0)
    grid.add_overhead_line(configuration_abc)

    line_3ph = vge.Line(bus_from=bus_slack,
                        bus_to=bus_middle)
    line_3ph.apply_template(configuration_abc, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_3ph)

    z_ab = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_ab = np.array([
        [1j * 6.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_ab = vge.create_known_abc_overhead_template(name='Two-phase line',
                                                              z_nabc=z_ab,
                                                              ysh_nabc=y_ab,
                                                              phases=np.array([1, 2]),
                                                              Vnom=10.0)
    grid.add_overhead_line(configuration_ab)

    line_2ph = vge.Line(bus_from=bus_middle,
                        bus_to=bus_load)
    line_2ph.apply_template(configuration_ab, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_2ph)

    # -----------------------------------------------------------------------------------------------------------------
    # Power Flow
    # -----------------------------------------------------------------------------------------------------------------
    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array(
        [1.0, 0.97159, 0.943320])

    Ub_reference = np.array(
        [1.0, 0.98853, 0.977810])

    Uc_reference = np.array(
        [1.0, 1.00921, 0.0])

    assert np.allclose(abs(res.voltage_A), Ua_reference, atol=1e-5)
    assert np.allclose(abs(res.voltage_B), Ub_reference, atol=1e-5)
    assert np.allclose(abs(res.voltage_C), Uc_reference, atol=1e-5)


def test_unconnected_current_floatingstar_3ph():
    '''
    This test executes a three-phase power flow into a three-phase current load connected in FloatingStar,
    which the bus it is connected to does not have the phase a.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = vge.Logger()
    grid = vge.MultiCircuit()

    # -----------------------------------------------------------------------------------------------------------------
    # Buses
    # -----------------------------------------------------------------------------------------------------------------
    bus_slack = vge.Bus(name='Slack Bus ABC', xpos=0, ypos=0)
    bus_slack.is_slack = True
    grid.add_bus(obj=bus_slack)

    bus_middle = vge.Bus(name='Middle Bus CB', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_middle)

    bus_load = vge.Bus(name='Load Bus CB', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_load)

    # -----------------------------------------------------------------------------------------------------------------
    # Generator
    # -----------------------------------------------------------------------------------------------------------------
    gen = vge.Generator()
    grid.add_generator(bus=bus_slack, api_obj=gen)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load = vge.Load(Ir1=1.0,
                    Ii1=-0.5,
                    Ir2=1.0,
                    Ii2=-0.5,
                    Ir3=1.0,
                    Ii3=-0.5)
    load.conn = ShuntConnectionType.FloatingStar
    grid.add_load(bus=bus_load, api_obj=load)

    # -----------------------------------------------------------------------------------------------------------------
    # Lines
    # -----------------------------------------------------------------------------------------------------------------
    z_abc = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_abc = np.array([
        [1j * 6.0, -1j * 1.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0, -1j * 1.0],
        [-1j * 1.0, -1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_abc = vge.create_known_abc_overhead_template(name='Three-phase line',
                                                               z_nabc=z_abc,
                                                               ysh_nabc=y_abc,
                                                               phases=np.array([1, 2, 3]),
                                                               Vnom=10.0)
    grid.add_overhead_line(configuration_abc)

    line_3ph = vge.Line(bus_from=bus_slack,
                        bus_to=bus_middle)
    line_3ph.apply_template(configuration_abc, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_3ph)

    z_cb = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_cb = np.array([
        [1j * 6.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_cb = vge.create_known_abc_overhead_template(name='Two-phase line',
                                                              z_nabc=z_cb,
                                                              ysh_nabc=y_cb,
                                                              phases=np.array([2, 3]),
                                                              Vnom=10.0)
    grid.add_overhead_line(configuration_cb)

    line_2ph = vge.Line(bus_from=bus_middle,
                        bus_to=bus_load)
    line_2ph.apply_template(configuration_cb, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_2ph)

    # -----------------------------------------------------------------------------------------------------------------
    # Power Flow
    # -----------------------------------------------------------------------------------------------------------------
    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array(
        [1.0, 1.0, 0.0])

    Ub_reference = np.array(
        [1.0, 0.99402, 0.98845])

    Uc_reference = np.array(
        [1.0, 0.97935, 0.95872])

    assert np.allclose(abs(res.voltage_A), Ua_reference, atol=1e-5)
    assert np.allclose(abs(res.voltage_B), Ub_reference, atol=1e-5)
    assert np.allclose(abs(res.voltage_C), Uc_reference, atol=1e-5)


def test_unconnected_current_delta_3ph():
    '''
    This test executes a three-phase power flow into a three-phase current load connected in Delta,
    which the bus it is connected to does not have the phase a.
    The obtained results can not be compared against the ones obtained in OpenDSS, as the load is modelled differently.
    '''

    logger = vge.Logger()
    grid = vge.MultiCircuit()

    # -----------------------------------------------------------------------------------------------------------------
    # Buses
    # -----------------------------------------------------------------------------------------------------------------
    bus_slack = vge.Bus(name='Slack Bus ABC', xpos=0, ypos=0)
    bus_slack.is_slack = True
    grid.add_bus(obj=bus_slack)

    bus_middle = vge.Bus(name='Middle Bus CB', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_middle)

    bus_load = vge.Bus(name='Load Bus CB', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_load)

    # -----------------------------------------------------------------------------------------------------------------
    # Generator
    # -----------------------------------------------------------------------------------------------------------------
    gen = vge.Generator()
    grid.add_generator(bus=bus_slack, api_obj=gen)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load = vge.Load(Ir1=1.0,
                    Ii1=-0.5,
                    Ir2=1.0,
                    Ii2=-0.5,
                    Ir3=1.0,
                    Ii3=-0.5)
    load.conn = ShuntConnectionType.Delta
    grid.add_load(bus=bus_load, api_obj=load)

    # -----------------------------------------------------------------------------------------------------------------
    # Lines
    # -----------------------------------------------------------------------------------------------------------------
    z_abc = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_abc = np.array([
        [1j * 6.0, -1j * 1.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0, -1j * 1.0],
        [-1j * 1.0, -1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_abc = vge.create_known_abc_overhead_template(name='Three-phase line',
                                                               z_nabc=z_abc,
                                                               ysh_nabc=y_abc,
                                                               phases=np.array([1, 2, 3]),
                                                               Vnom=10.0)
    grid.add_overhead_line(configuration_abc)

    line_3ph = vge.Line(bus_from=bus_slack,
                        bus_to=bus_middle)
    line_3ph.apply_template(configuration_abc, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_3ph)

    z_cb = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_cb = np.array([
        [1j * 6.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_cb = vge.create_known_abc_overhead_template(name='Two-phase line',
                                                              z_nabc=z_cb,
                                                              ysh_nabc=y_cb,
                                                              phases=np.array([2, 3]),
                                                              Vnom=10.0)
    grid.add_overhead_line(configuration_cb)

    line_2ph = vge.Line(bus_from=bus_middle,
                        bus_to=bus_load)
    line_2ph.apply_template(configuration_cb, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_2ph)

    # -----------------------------------------------------------------------------------------------------------------
    # Power Flow
    # -----------------------------------------------------------------------------------------------------------------
    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array(
        [1.0, 1.0, 0.0])

    Ub_reference = np.array(
        [1.0, 0.996670, 0.993480])

    Uc_reference = np.array(
        [1.0, 0.988120, 0.976240])

    assert np.allclose(abs(res.voltage_A), Ua_reference, atol=1e-5)
    assert np.allclose(abs(res.voltage_B), Ub_reference, atol=1e-5)
    assert np.allclose(abs(res.voltage_C), Uc_reference, atol=1e-5)


def test_unconnected_current_delta_2ph():
    '''
    This test executes a three-phase power flow into a two-phase current load connected in Delta,
    which the bus it is connected to does not have the phase a.
    The obtained results can not be compared against the ones obtained in OpenDSS, as the load is modelled differently.
    '''

    logger = vge.Logger()
    grid = vge.MultiCircuit()

    # -----------------------------------------------------------------------------------------------------------------
    # Buses
    # -----------------------------------------------------------------------------------------------------------------
    bus_slack = vge.Bus(name='Slack Bus ABC', xpos=0, ypos=0)
    bus_slack.is_slack = True
    grid.add_bus(obj=bus_slack)

    bus_middle = vge.Bus(name='Middle Bus CB', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_middle)

    bus_load = vge.Bus(name='Load Bus CB', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_load)

    # -----------------------------------------------------------------------------------------------------------------
    # Generator
    # -----------------------------------------------------------------------------------------------------------------
    gen = vge.Generator()
    grid.add_generator(bus=bus_slack, api_obj=gen)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load = vge.Load(Ir1=1.0,
                    Ii1=-0.5)
    load.conn = ShuntConnectionType.Delta
    grid.add_load(bus=bus_load, api_obj=load)

    # -----------------------------------------------------------------------------------------------------------------
    # Lines
    # -----------------------------------------------------------------------------------------------------------------
    z_abc = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_abc = np.array([
        [1j * 6.0, -1j * 1.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0, -1j * 1.0],
        [-1j * 1.0, -1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_abc = vge.create_known_abc_overhead_template(name='Three-phase line',
                                                               z_nabc=z_abc,
                                                               ysh_nabc=y_abc,
                                                               phases=np.array([1, 2, 3]),
                                                               Vnom=10.0)
    grid.add_overhead_line(configuration_abc)

    line_3ph = vge.Line(bus_from=bus_slack,
                        bus_to=bus_middle)
    line_3ph.apply_template(configuration_abc, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_3ph)

    z_cb = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_cb = np.array([
        [1j * 6.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_cb = vge.create_known_abc_overhead_template(name='Two-phase line',
                                                              z_nabc=z_cb,
                                                              ysh_nabc=y_cb,
                                                              phases=np.array([2, 3]),
                                                              Vnom=10.0)
    grid.add_overhead_line(configuration_cb)

    line_2ph = vge.Line(bus_from=bus_middle,
                        bus_to=bus_load)
    line_2ph.apply_template(configuration_cb, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_2ph)

    # -----------------------------------------------------------------------------------------------------------------
    # Power Flow
    # -----------------------------------------------------------------------------------------------------------------
    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array(
        [1.0, 1.0, 0.0])

    Ub_reference = np.array(
        [1.0, 1.00001, 1.00001])

    Uc_reference = np.array(
        [1.0, 1.00001, 1.00001])

    assert np.allclose(abs(res.voltage_A), Ua_reference, atol=1e-5)
    assert np.allclose(abs(res.voltage_B), Ub_reference, atol=1e-5)
    assert np.allclose(abs(res.voltage_C), Uc_reference, atol=1e-5)


def test_unconnected_current_groundedstar_1ph():
    '''
    This test executes a three-phase power flow into a single-phase current load connected in GroundedStar,
    which the bus it is connected to does not have the phase c.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = vge.Logger()
    grid = vge.MultiCircuit()

    # -----------------------------------------------------------------------------------------------------------------
    # Buses
    # -----------------------------------------------------------------------------------------------------------------
    bus_slack = vge.Bus(name='Slack Bus ABC', xpos=0, ypos=0)
    bus_slack.is_slack = True
    grid.add_bus(obj=bus_slack)

    bus_middle = vge.Bus(name='Middle Bus AB', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_middle)

    bus_load = vge.Bus(name='Load Bus AB', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_load)

    # -----------------------------------------------------------------------------------------------------------------
    # Generator
    # -----------------------------------------------------------------------------------------------------------------
    gen = vge.Generator()
    grid.add_generator(bus=bus_slack, api_obj=gen)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load = vge.Load(Ir3=1.0,
                    Ii3=-0.5)
    load.conn = ShuntConnectionType.GroundedStar
    grid.add_load(bus=bus_load, api_obj=load)

    # -----------------------------------------------------------------------------------------------------------------
    # Lines
    # -----------------------------------------------------------------------------------------------------------------
    z_abc = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_abc = np.array([
        [1j * 6.0, -1j * 1.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0, -1j * 1.0],
        [-1j * 1.0, -1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_abc = vge.create_known_abc_overhead_template(name='Three-phase line',
                                                               z_nabc=z_abc,
                                                               ysh_nabc=y_abc,
                                                               phases=np.array([1, 2, 3]),
                                                               Vnom=10.0)
    grid.add_overhead_line(configuration_abc)

    line_3ph = vge.Line(bus_from=bus_slack,
                        bus_to=bus_middle)
    line_3ph.apply_template(configuration_abc, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_3ph)

    z_ab = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_ab = np.array([
        [1j * 6.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_ab = vge.create_known_abc_overhead_template(name='Two-phase line',
                                                              z_nabc=z_ab,
                                                              ysh_nabc=y_ab,
                                                              phases=np.array([1, 2]),
                                                              Vnom=10.0)
    grid.add_overhead_line(configuration_ab)

    line_2ph = vge.Line(bus_from=bus_middle,
                        bus_to=bus_load)
    line_2ph.apply_template(configuration_ab, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_2ph)

    # -----------------------------------------------------------------------------------------------------------------
    # Power Flow
    # -----------------------------------------------------------------------------------------------------------------
    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array(
        [1.0, 1.0, 1.0])

    Ub_reference = np.array(
        [1.0, 1.0, 1.0])

    Uc_reference = np.array(
        [1.0, 1.0, 0.0])

    assert np.allclose(abs(res.voltage_A), Ua_reference, atol=1e-5)
    assert np.allclose(abs(res.voltage_B), Ub_reference, atol=1e-5)
    assert np.allclose(abs(res.voltage_C), Uc_reference, atol=1e-5)


def test_unconnected_power_groundedstar_3ph():
    '''
    This test executes a three-phase power flow into a three-phase power load connected in GroundedStar,
    which the bus it is connected to does not have the phase b.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = vge.Logger()
    grid = vge.MultiCircuit()

    # -----------------------------------------------------------------------------------------------------------------
    # Buses
    # -----------------------------------------------------------------------------------------------------------------
    bus_slack = vge.Bus(name='Slack Bus ABC', xpos=0, ypos=0)
    bus_slack.is_slack = True
    grid.add_bus(obj=bus_slack)

    bus_middle = vge.Bus(name='Middle Bus AC', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_middle)

    bus_load = vge.Bus(name='Load Bus AC', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_load)

    # -----------------------------------------------------------------------------------------------------------------
    # Generator
    # -----------------------------------------------------------------------------------------------------------------
    gen = vge.Generator()
    grid.add_generator(bus=bus_slack, api_obj=gen)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load = vge.Load(P1=1.0,
                    Q1=0.5,
                    P2=1.0,
                    Q2=0.5,
                    P3=1.0,
                    Q3=0.5)
    load.conn = ShuntConnectionType.GroundedStar
    grid.add_load(bus=bus_load, api_obj=load)

    # -----------------------------------------------------------------------------------------------------------------
    # Lines
    # -----------------------------------------------------------------------------------------------------------------
    z_abc = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_abc = np.array([
        [1j * 6.0, -1j * 1.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0, -1j * 1.0],
        [-1j * 1.0, -1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_abc = vge.create_known_abc_overhead_template(name='Three-phase line',
                                                               z_nabc=z_abc,
                                                               ysh_nabc=y_abc,
                                                               phases=np.array([1, 2, 3]),
                                                               Vnom=10.0)
    grid.add_overhead_line(configuration_abc)

    line_3ph = vge.Line(bus_from=bus_slack,
                        bus_to=bus_middle)
    line_3ph.apply_template(configuration_abc, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_3ph)

    z_ac = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_ac = np.array([
        [1j * 6.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_ac = vge.create_known_abc_overhead_template(name='Two-phase line',
                                                              z_nabc=z_ac,
                                                              ysh_nabc=y_ac,
                                                              phases=np.array([1, 3]),
                                                              Vnom=10.0)
    grid.add_overhead_line(configuration_ac)

    line_2ph = vge.Line(bus_from=bus_middle,
                        bus_to=bus_load)
    line_2ph.apply_template(configuration_ac, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_2ph)

    # -----------------------------------------------------------------------------------------------------------------
    # Power Flow
    # -----------------------------------------------------------------------------------------------------------------
    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array(
        [1.0, 0.98881, 0.97840])

    Ub_reference = np.array(
        [1.0, 1.00930, 0.0])

    Uc_reference = np.array(
        [1.0, 0.96990, 0.93997])

    assert np.allclose(abs(res.voltage_A), Ua_reference, atol=1e-4)
    assert np.allclose(abs(res.voltage_B), Ub_reference, atol=1e-4)
    assert np.allclose(abs(res.voltage_C), Uc_reference, atol=1e-4)


def test_unconnected_power_floatingstar_3ph():
    '''
    This test executes a three-phase power flow into a three-phase current load connected in FloatingStar,
    which the bus it is connected to does not have the phase a.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = vge.Logger()
    grid = vge.MultiCircuit()

    # -----------------------------------------------------------------------------------------------------------------
    # Buses
    # -----------------------------------------------------------------------------------------------------------------
    bus_slack = vge.Bus(name='Slack Bus ABC', xpos=0, ypos=0)
    bus_slack.is_slack = True
    grid.add_bus(obj=bus_slack)

    bus_middle = vge.Bus(name='Middle Bus CB', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_middle)

    bus_load = vge.Bus(name='Load Bus CB', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_load)

    # -----------------------------------------------------------------------------------------------------------------
    # Generator
    # -----------------------------------------------------------------------------------------------------------------
    gen = vge.Generator()
    grid.add_generator(bus=bus_slack, api_obj=gen)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load = vge.Load(P1=1.0,
                    Q1=0.5,
                    P2=1.0,
                    Q2=0.5,
                    P3=1.0,
                    Q3=0.5)
    load.conn = ShuntConnectionType.FloatingStar
    grid.add_load(bus=bus_load, api_obj=load)

    # -----------------------------------------------------------------------------------------------------------------
    # Lines
    # -----------------------------------------------------------------------------------------------------------------
    z_abc = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_abc = np.array([
        [1j * 6.0, -1j * 1.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0, -1j * 1.0],
        [-1j * 1.0, -1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_abc = vge.create_known_abc_overhead_template(name='Three-phase line',
                                                               z_nabc=z_abc,
                                                               ysh_nabc=y_abc,
                                                               phases=np.array([1, 2, 3]),
                                                               Vnom=10.0)
    grid.add_overhead_line(configuration_abc)

    line_3ph = vge.Line(bus_from=bus_slack,
                        bus_to=bus_middle)
    line_3ph.apply_template(configuration_abc, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_3ph)

    z_cb = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_cb = np.array([
        [1j * 6.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_cb = vge.create_known_abc_overhead_template(name='Two-phase line',
                                                              z_nabc=z_cb,
                                                              ysh_nabc=y_cb,
                                                              phases=np.array([2, 3]),
                                                              Vnom=10.0)
    grid.add_overhead_line(configuration_cb)

    line_2ph = vge.Line(bus_from=bus_middle,
                        bus_to=bus_load)
    line_2ph.apply_template(configuration_cb, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_2ph)

    # -----------------------------------------------------------------------------------------------------------------
    # Power Flow
    # -----------------------------------------------------------------------------------------------------------------
    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array(
        [1.0, 1.0, 0.0])

    Ub_reference = np.array(
        [1.0, 0.99266, 0.98592])

    Uc_reference = np.array(
        [1.0, 0.97506, 0.95014])

    assert np.allclose(abs(res.voltage_A), Ua_reference, atol=1e-5)
    assert np.allclose(abs(res.voltage_B), Ub_reference, atol=1e-5)
    assert np.allclose(abs(res.voltage_C), Uc_reference, atol=1e-5)


def test_unconnected_power_delta_3ph():
    '''
    This test executes a three-phase power flow into a three-phase power load connected in Delta,
    which the bus it is connected to does not have the phase a.
    The obtained results can not be compared against the ones obtained in OpenDSS, as the load is modelled differently.
    '''

    logger = vge.Logger()
    grid = vge.MultiCircuit()

    # -----------------------------------------------------------------------------------------------------------------
    # Buses
    # -----------------------------------------------------------------------------------------------------------------
    bus_slack = vge.Bus(name='Slack Bus ABC', xpos=0, ypos=0)
    bus_slack.is_slack = True
    grid.add_bus(obj=bus_slack)

    bus_middle = vge.Bus(name='Middle Bus CB', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_middle)

    bus_load = vge.Bus(name='Load Bus CB', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_load)

    # -----------------------------------------------------------------------------------------------------------------
    # Generator
    # -----------------------------------------------------------------------------------------------------------------
    gen = vge.Generator()
    grid.add_generator(bus=bus_slack, api_obj=gen)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load = vge.Load(P1=1.0,
                    Q1=0.5,
                    P2=1.0,
                    Q2=0.5,
                    P3=1.0,
                    Q3=0.5)
    load.conn = ShuntConnectionType.Delta
    grid.add_load(bus=bus_load, api_obj=load)

    # -----------------------------------------------------------------------------------------------------------------
    # Lines
    # -----------------------------------------------------------------------------------------------------------------
    z_abc = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_abc = np.array([
        [1j * 6.0, -1j * 1.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0, -1j * 1.0],
        [-1j * 1.0, -1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_abc = vge.create_known_abc_overhead_template(name='Three-phase line',
                                                               z_nabc=z_abc,
                                                               ysh_nabc=y_abc,
                                                               phases=np.array([1, 2, 3]),
                                                               Vnom=10.0)
    grid.add_overhead_line(configuration_abc)

    line_3ph = vge.Line(bus_from=bus_slack,
                        bus_to=bus_middle)
    line_3ph.apply_template(configuration_abc, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_3ph)

    z_cb = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_cb = np.array([
        [1j * 6.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_cb = vge.create_known_abc_overhead_template(name='Two-phase line',
                                                              z_nabc=z_cb,
                                                              ysh_nabc=y_cb,
                                                              phases=np.array([2, 3]),
                                                              Vnom=10.0)
    grid.add_overhead_line(configuration_cb)

    line_2ph = vge.Line(bus_from=bus_middle,
                        bus_to=bus_load)
    line_2ph.apply_template(configuration_cb, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_2ph)

    # -----------------------------------------------------------------------------------------------------------------
    # Power Flow
    # -----------------------------------------------------------------------------------------------------------------
    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array(
        [1.0, 1.0, 0.0])

    Ub_reference = np.array(
        [1.0, 0.996600, 0.993330])

    Uc_reference = np.array(
        [1.0, 0.987870, 0.975740])

    assert np.allclose(abs(res.voltage_A), Ua_reference, atol=1e-5)
    assert np.allclose(abs(res.voltage_B), Ub_reference, atol=1e-5)
    assert np.allclose(abs(res.voltage_C), Uc_reference, atol=1e-5)


def test_unconnected_power_delta_2ph():
    '''
    This test executes a three-phase power flow into a two-phase power load connected in Delta,
    which the bus it is connected to does not have the phase a.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = vge.Logger()
    grid = vge.MultiCircuit()

    # -----------------------------------------------------------------------------------------------------------------
    # Buses
    # -----------------------------------------------------------------------------------------------------------------
    bus_slack = vge.Bus(name='Slack Bus ABC', xpos=0, ypos=0)
    bus_slack.is_slack = True
    grid.add_bus(obj=bus_slack)

    bus_middle = vge.Bus(name='Middle Bus CB', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_middle)

    bus_load = vge.Bus(name='Load Bus CB', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_load)

    # -----------------------------------------------------------------------------------------------------------------
    # Generator
    # -----------------------------------------------------------------------------------------------------------------
    gen = vge.Generator()
    grid.add_generator(bus=bus_slack, api_obj=gen)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load = vge.Load(P1=1.0,
                    Q1=0.5)
    load.conn = ShuntConnectionType.Delta
    grid.add_load(bus=bus_load, api_obj=load)

    # -----------------------------------------------------------------------------------------------------------------
    # Lines
    # -----------------------------------------------------------------------------------------------------------------
    z_abc = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_abc = np.array([
        [1j * 6.0, -1j * 1.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0, -1j * 1.0],
        [-1j * 1.0, -1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_abc = vge.create_known_abc_overhead_template(name='Three-phase line',
                                                               z_nabc=z_abc,
                                                               ysh_nabc=y_abc,
                                                               phases=np.array([1, 2, 3]),
                                                               Vnom=10.0)
    grid.add_overhead_line(configuration_abc)

    line_3ph = vge.Line(bus_from=bus_slack,
                        bus_to=bus_middle)
    line_3ph.apply_template(configuration_abc, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_3ph)

    z_cb = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_cb = np.array([
        [1j * 6.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_cb = vge.create_known_abc_overhead_template(name='Two-phase line',
                                                              z_nabc=z_cb,
                                                              ysh_nabc=y_cb,
                                                              phases=np.array([2, 3]),
                                                              Vnom=10.0)
    grid.add_overhead_line(configuration_cb)

    line_2ph = vge.Line(bus_from=bus_middle,
                        bus_to=bus_load)
    line_2ph.apply_template(configuration_cb, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_2ph)

    # -----------------------------------------------------------------------------------------------------------------
    # Power Flow
    # -----------------------------------------------------------------------------------------------------------------
    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array(
        [1.0, 1.0, 0.0])

    Ub_reference = np.array(
        [1.0, 1.00001, 1.00001])

    Uc_reference = np.array(
        [1.0, 1.00001, 1.00001])

    assert np.allclose(abs(res.voltage_A), Ua_reference, atol=1e-5)
    assert np.allclose(abs(res.voltage_B), Ub_reference, atol=1e-5)
    assert np.allclose(abs(res.voltage_C), Uc_reference, atol=1e-5)


def test_unconnected_power_groundedstar_1ph():
    '''
    This test executes a three-phase power flow into a single-phase power load connected in GroundedStar,
    which the bus it is connected to does not have the phase b.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = vge.Logger()
    grid = vge.MultiCircuit()

    # -----------------------------------------------------------------------------------------------------------------
    # Buses
    # -----------------------------------------------------------------------------------------------------------------
    bus_slack = vge.Bus(name='Slack Bus ABC', xpos=0, ypos=0)
    bus_slack.is_slack = True
    grid.add_bus(obj=bus_slack)

    bus_middle = vge.Bus(name='Middle Bus AC', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_middle)

    bus_load = vge.Bus(name='Load Bus AC', xpos=1000, ypos=0)
    grid.add_bus(obj=bus_load)

    # -----------------------------------------------------------------------------------------------------------------
    # Generator
    # -----------------------------------------------------------------------------------------------------------------
    gen = vge.Generator()
    grid.add_generator(bus=bus_slack, api_obj=gen)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load = vge.Load(P2=1.0,
                    Q2=0.5)
    load.conn = ShuntConnectionType.GroundedStar
    grid.add_load(bus=bus_load, api_obj=load)

    # -----------------------------------------------------------------------------------------------------------------
    # Lines
    # -----------------------------------------------------------------------------------------------------------------
    z_abc = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_abc = np.array([
        [1j * 6.0, -1j * 1.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0, -1j * 1.0],
        [-1j * 1.0, -1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_abc = vge.create_known_abc_overhead_template(name='Three-phase line',
                                                               z_nabc=z_abc,
                                                               ysh_nabc=y_abc,
                                                               phases=np.array([1, 2, 3]),
                                                               Vnom=10.0)
    grid.add_overhead_line(configuration_abc)

    line_3ph = vge.Line(bus_from=bus_slack,
                        bus_to=bus_middle)
    line_3ph.apply_template(configuration_abc, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_3ph)

    z_ac = np.array([
        [0.3 + 1j * 1.0, 0.1 + 1j * 0.4],
        [0.1 + 1j * 0.4, 0.3 + 1j * 1.0]
    ], dtype=complex)  # Ω/km

    y_ac = np.array([
        [1j * 6.0, -1j * 1.0],
        [-1j * 1.0, 1j * 6.0]
    ], dtype=complex) / (10 ** 6)  # S/km

    configuration_ac = vge.create_known_abc_overhead_template(name='Two-phase line',
                                                              z_nabc=z_ac,
                                                              ysh_nabc=y_ac,
                                                              phases=np.array([1, 3]),
                                                              Vnom=10.0)
    grid.add_overhead_line(configuration_ac)

    line_2ph = vge.Line(bus_from=bus_middle,
                        bus_to=bus_load)
    line_2ph.apply_template(configuration_ac, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line_2ph)

    # -----------------------------------------------------------------------------------------------------------------
    # Power Flow
    # -----------------------------------------------------------------------------------------------------------------
    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array(
        [1.0, 1.0, 1.0])

    Ub_reference = np.array(
        [1.0, 1.0, 0.0])

    Uc_reference = np.array(
        [1.0, 1.0, 1.0])

    assert np.allclose(abs(res.voltage_A), Ua_reference, atol=1e-4)
    assert np.allclose(abs(res.voltage_B), Ub_reference, atol=1e-4)
    assert np.allclose(abs(res.voltage_C), Uc_reference, atol=1e-4)