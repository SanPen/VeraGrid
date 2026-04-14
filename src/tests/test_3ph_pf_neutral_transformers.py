import VeraGridEngine.api as gce
from VeraGridEngine import WindingType, ShuntConnectionType, SolverType
import numpy as np


def test_yy_impedance_neutralstar_3ph():
    '''
    This test executes a three-phase power flow with neutral into a Yy transformer with a NeutralStar load.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = gce.Logger()
    grid = gce.MultiCircuit()
    grid.fBase = 60

    # ----------------------------------------------------------------------------------------------------------------------
    # Buses
    # ----------------------------------------------------------------------------------------------------------------------
    bus_632 = gce.Bus(name='Bus632', Vnom=4.16, xpos=0, ypos=0)
    bus_632.is_slack = True
    grid.add_bus(obj=bus_632)
    gen = gce.Generator()
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    bus_636 = gce.Bus(name='Bus636', Vnom=0.48, xpos=400 * 5, ypos=0)
    grid.add_bus(obj=bus_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Transformer
    # ----------------------------------------------------------------------------------------------------------------------
    XFM_1 = gce.Transformer2W(name='XFM-1',
                              bus_from=bus_632,
                              bus_to=bus_634,
                              HV=4.16,
                              LV=0.48,
                              nominal_power=0.5,
                              rate=0.5,
                              r=1.1 * 2,
                              x=2 * 2)
    XFM_1.conn_f = WindingType.GroundedStar
    XFM_1.conn_t = WindingType.GroundedStar
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Line
    # ----------------------------------------------------------------------------------------------------------------------
    z_nabc = np.array([
        [0.2735 + 1j * 0.8143, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509],
        [0.0173 + 1j * 0.0509, 0.3465 + 1j * 1.0179, 0.1560 + 1j * 0.5017, 0.1580 + 1j * 0.4236],
        [0.0173 + 1j * 0.0509, 0.1560 + 1j * 0.5017, 0.3375 + 1j * 1.0478, 0.1535 + 1j * 0.3849],
        [0.0173 + 1j * 0.0509, 0.1580 + 1j * 0.4236, 0.1535 + 1j * 0.3849, 0.3414 + 1j * 1.0348]
    ], dtype=complex) / 1.60934  # Ω/km

    y_nabc = np.array([
        [1j * 6.1541, -1j * 1.8918, -1j * 2.0022, -1j * 2.2602],
        [-1j * 1.8918, 1j * 6.2998, -1j * 1.9958, -1j * 1.2595],
        [-1j * 2.0022, -1j * 1.9958, 1j * 5.9597, -1j * 0.7417],
        [-1j * 2.2602, -1j * 1.2595, -1j * 0.7417, 1j * 5.6386]
    ], dtype=complex) / (10 ** 6) / 1.60934  # S/km

    configuration = gce.create_known_abc_overhead_template(name='4 wire line',
                                                           z_nabc=z_nabc,
                                                           ysh_nabc=y_nabc,
                                                           phases=np.array([0, 1, 2, 3]),
                                                           Vnom=4.16,
                                                           frequency=60)
    grid.add_overhead_line(configuration)

    line = gce.Line(bus_from=bus_634,
                    bus_to=bus_636,
                    length=100 * 0.0003048)
    line.apply_template(configuration, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_636 = gce.Load(G1=0.3,
                        B1=0.3,
                        G2=0.2,
                        B2=0.2,
                        G3=0.1,
                        B3=0.1)
    load_636.conn = ShuntConnectionType.NeutralStar
    grid.add_load(bus=bus_636, api_obj=load_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Un_reference = np.array(
        [0.0 + 0.j, 0.0 + 0.0j, 0.03367965 - 0.00745322j])

    Ua_reference = np.array(
        [1 + 0j, 0.95218447 - 0.01265888j, 0.88472009 - 0.02766787j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.48833169 - 0.83113485j, -0.50673344 - 0.78847722j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.48579392 + 0.85298809j, -0.48303905 + 0.84349284j])

    assert np.allclose(res.voltage_N, Un_reference, atol=1e-4)
    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_yy_impedance_neutralstar_1ph():
    '''
    This test executes a three-phase power flow with neutral into a Yy transformer with a NeutralStar load.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = gce.Logger()
    grid = gce.MultiCircuit()
    grid.fBase = 60

    # ----------------------------------------------------------------------------------------------------------------------
    # Buses
    # ----------------------------------------------------------------------------------------------------------------------
    bus_632 = gce.Bus(name='Bus632', Vnom=4.16, xpos=0, ypos=0)
    bus_632.is_slack = True
    grid.add_bus(obj=bus_632)
    gen = gce.Generator()
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    bus_636 = gce.Bus(name='Bus636', Vnom=0.48, xpos=400 * 5, ypos=0)
    grid.add_bus(obj=bus_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Transformer
    # ----------------------------------------------------------------------------------------------------------------------
    XFM_1 = gce.Transformer2W(name='XFM-1',
                              bus_from=bus_632,
                              bus_to=bus_634,
                              HV=4.16,
                              LV=0.48,
                              nominal_power=0.5,
                              rate=0.5,
                              r=1.1 * 2,
                              x=2 * 2)
    XFM_1.conn_f = WindingType.GroundedStar
    XFM_1.conn_t = WindingType.GroundedStar
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Line
    # ----------------------------------------------------------------------------------------------------------------------
    z_nabc = np.array([
        [0.2735 + 1j * 0.8143, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509],
        [0.0173 + 1j * 0.0509, 0.3465 + 1j * 1.0179, 0.1560 + 1j * 0.5017, 0.1580 + 1j * 0.4236],
        [0.0173 + 1j * 0.0509, 0.1560 + 1j * 0.5017, 0.3375 + 1j * 1.0478, 0.1535 + 1j * 0.3849],
        [0.0173 + 1j * 0.0509, 0.1580 + 1j * 0.4236, 0.1535 + 1j * 0.3849, 0.3414 + 1j * 1.0348]
    ], dtype=complex) / 1.60934  # Ω/km

    y_nabc = np.array([
        [1j * 6.1541, -1j * 1.8918, -1j * 2.0022, -1j * 2.2602],
        [-1j * 1.8918, 1j * 6.2998, -1j * 1.9958, -1j * 1.2595],
        [-1j * 2.0022, -1j * 1.9958, 1j * 5.9597, -1j * 0.7417],
        [-1j * 2.2602, -1j * 1.2595, -1j * 0.7417, 1j * 5.6386]
    ], dtype=complex) / (10 ** 6) / 1.60934  # S/km

    configuration = gce.create_known_abc_overhead_template(name='4 wire line',
                                                           z_nabc=z_nabc,
                                                           ysh_nabc=y_nabc,
                                                           phases=np.array([0, 1, 2, 3]),
                                                           Vnom=4.16,
                                                           frequency=60)
    grid.add_overhead_line(configuration)

    line = gce.Line(bus_from=bus_634,
                    bus_to=bus_636,
                    length=100 * 0.0003048)
    line.apply_template(configuration, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_636 = gce.Load(G1=0.3,
                        B1=0.3)
    load_636.conn = ShuntConnectionType.NeutralStar
    grid.add_load(bus=bus_636, api_obj=load_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                 retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Un_reference = np.array(
        [0.0 + 0.j, 0.0 + 0.0j, 0.06355538 + 0.02535082j])

    Ua_reference = np.array(
        [1 + 0j, 0.95375511 - 0.00939879j, 0.8729928 - 0.04120997j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.5 - 0.8660254j, -0.53683847 - 0.88181239j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.5 + 0.86602541j, -0.53188686 + 0.85466038j])

    assert np.allclose(res.voltage_N, Un_reference, atol=1e-4)
    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_yy_current_neutralstar_3ph():
    '''
    This test executes a three-phase power flow with neutral into a Yy transformer with a NeutralStar load.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = gce.Logger()
    grid = gce.MultiCircuit()
    grid.fBase = 60

    # ----------------------------------------------------------------------------------------------------------------------
    # Buses
    # ----------------------------------------------------------------------------------------------------------------------
    bus_632 = gce.Bus(name='Bus632', Vnom=4.16, xpos=0, ypos=0)
    bus_632.is_slack = True
    grid.add_bus(obj=bus_632)
    gen = gce.Generator()
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    bus_636 = gce.Bus(name='Bus636', Vnom=0.48, xpos=400 * 5, ypos=0)
    grid.add_bus(obj=bus_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Transformer
    # ----------------------------------------------------------------------------------------------------------------------
    XFM_1 = gce.Transformer2W(name='XFM-1',
                              bus_from=bus_632,
                              bus_to=bus_634,
                              HV=4.16,
                              LV=0.48,
                              nominal_power=0.5,
                              rate=0.5,
                              r=1.1 * 2,
                              x=2 * 2)
    XFM_1.conn_f = WindingType.GroundedStar
    XFM_1.conn_t = WindingType.GroundedStar
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Line
    # ----------------------------------------------------------------------------------------------------------------------
    z_nabc = np.array([
        [0.2735 + 1j * 0.8143, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509],
        [0.0173 + 1j * 0.0509, 0.3465 + 1j * 1.0179, 0.1560 + 1j * 0.5017, 0.1580 + 1j * 0.4236],
        [0.0173 + 1j * 0.0509, 0.1560 + 1j * 0.5017, 0.3375 + 1j * 1.0478, 0.1535 + 1j * 0.3849],
        [0.0173 + 1j * 0.0509, 0.1580 + 1j * 0.4236, 0.1535 + 1j * 0.3849, 0.3414 + 1j * 1.0348]
    ], dtype=complex) / 1.60934  # Ω/km

    y_nabc = np.array([
        [1j * 6.1541, -1j * 1.8918, -1j * 2.0022, -1j * 2.2602],
        [-1j * 1.8918, 1j * 6.2998, -1j * 1.9958, -1j * 1.2595],
        [-1j * 2.0022, -1j * 1.9958, 1j * 5.9597, -1j * 0.7417],
        [-1j * 2.2602, -1j * 1.2595, -1j * 0.7417, 1j * 5.6386]
    ], dtype=complex) / (10 ** 6) / 1.60934  # S/km

    configuration = gce.create_known_abc_overhead_template(name='4 wire line',
                                                           z_nabc=z_nabc,
                                                           ysh_nabc=y_nabc,
                                                           phases=np.array([0, 1, 2, 3]),
                                                           Vnom=4.16,
                                                           frequency=60)
    grid.add_overhead_line(configuration)

    line = gce.Line(bus_from=bus_634,
                    bus_to=bus_636,
                    length=100 * 0.0003048)
    line.apply_template(configuration, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_636 = gce.Load(Ir1=0.3,
                        Ii1=0.3,
                        Ir2=0.2,
                        Ii2=0.2,
                        Ir3=0.1,
                        Ii3=0.1)
    load_636.conn = ShuntConnectionType.NeutralStar
    grid.add_load(bus=bus_636, api_obj=load_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                 retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Un_reference = np.array(
        [0.0 + 0.j, 0.0 + 0.0j, 0.04394597 - 0.00583965j])

    Ua_reference = np.array(
        [1 + 0j, 0.94368741 - 0.01431683j, 0.86213519 - 0.0333338j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.48724257 - 0.82945044j, -0.51086938 - 0.78601869j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.48555138 + 0.85312744j, -0.48768898 + 0.84309991j])

    assert np.allclose(res.voltage_N, Un_reference, atol=1e-4)
    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_yy_current_neutralstar_1ph():
    '''
    This test executes a three-phase power flow with neutral into a Yy transformer with a NeutralStar load.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = gce.Logger()
    grid = gce.MultiCircuit()
    grid.fBase = 60

    # ----------------------------------------------------------------------------------------------------------------------
    # Buses
    # ----------------------------------------------------------------------------------------------------------------------
    bus_632 = gce.Bus(name='Bus632', Vnom=4.16, xpos=0, ypos=0)
    bus_632.is_slack = True
    grid.add_bus(obj=bus_632)
    gen = gce.Generator()
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    bus_636 = gce.Bus(name='Bus636', Vnom=0.48, xpos=400 * 5, ypos=0)
    grid.add_bus(obj=bus_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Transformer
    # ----------------------------------------------------------------------------------------------------------------------
    XFM_1 = gce.Transformer2W(name='XFM-1',
                              bus_from=bus_632,
                              bus_to=bus_634,
                              HV=4.16,
                              LV=0.48,
                              nominal_power=0.5,
                              rate=0.5,
                              r=1.1 * 2,
                              x=2 * 2)
    XFM_1.conn_f = WindingType.GroundedStar
    XFM_1.conn_t = WindingType.GroundedStar
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Line
    # ----------------------------------------------------------------------------------------------------------------------
    z_nabc = np.array([
        [0.2735 + 1j * 0.8143, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509],
        [0.0173 + 1j * 0.0509, 0.3465 + 1j * 1.0179, 0.1560 + 1j * 0.5017, 0.1580 + 1j * 0.4236],
        [0.0173 + 1j * 0.0509, 0.1560 + 1j * 0.5017, 0.3375 + 1j * 1.0478, 0.1535 + 1j * 0.3849],
        [0.0173 + 1j * 0.0509, 0.1580 + 1j * 0.4236, 0.1535 + 1j * 0.3849, 0.3414 + 1j * 1.0348]
    ], dtype=complex) / 1.60934  # Ω/km

    y_nabc = np.array([
        [1j * 6.1541, -1j * 1.8918, -1j * 2.0022, -1j * 2.2602],
        [-1j * 1.8918, 1j * 6.2998, -1j * 1.9958, -1j * 1.2595],
        [-1j * 2.0022, -1j * 1.9958, 1j * 5.9597, -1j * 0.7417],
        [-1j * 2.2602, -1j * 1.2595, -1j * 0.7417, 1j * 5.6386]
    ], dtype=complex) / (10 ** 6) / 1.60934  # S/km

    configuration = gce.create_known_abc_overhead_template(name='4 wire line',
                                                           z_nabc=z_nabc,
                                                           ysh_nabc=y_nabc,
                                                           phases=np.array([0, 1, 2, 3]),
                                                           Vnom=4.16,
                                                           frequency=60)
    grid.add_overhead_line(configuration)

    line = gce.Line(bus_from=bus_634,
                    bus_to=bus_636,
                    length=100 * 0.0003048)
    line.apply_template(configuration, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_636 = gce.Load(Ir1=0.3,
                        Ii1=0.3)
    load_636.conn = ShuntConnectionType.NeutralStar
    grid.add_load(bus=bus_636, api_obj=load_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                 retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Un_reference = np.array(
        [0.0 + 0.j, 0.0 + 0.0j, 0.07883374 + 0.02971871j])

    Ua_reference = np.array(
        [1 + 0j, 0.94285011 - 0.01048665j, 0.84268244 - 0.04775512j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.5 - 0.8660254j, -0.54571984 - 0.88459665j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.5 + 0.86602541j, -0.53952055 + 0.85278177j])

    assert np.allclose(res.voltage_N, Un_reference, atol=1e-4)
    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_yy_power_neutralstar_3ph():
    '''
    This test executes a three-phase power flow with neutral into a Yy transformer with a NeutralStar load.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = gce.Logger()
    grid = gce.MultiCircuit()
    grid.fBase = 60

    # ----------------------------------------------------------------------------------------------------------------------
    # Buses
    # ----------------------------------------------------------------------------------------------------------------------
    bus_632 = gce.Bus(name='Bus632', Vnom=4.16, xpos=0, ypos=0)
    bus_632.is_slack = True
    grid.add_bus(obj=bus_632)
    gen = gce.Generator()
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    bus_636 = gce.Bus(name='Bus636', Vnom=0.48, xpos=400 * 5, ypos=0)
    grid.add_bus(obj=bus_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Transformer
    # ----------------------------------------------------------------------------------------------------------------------
    XFM_1 = gce.Transformer2W(name='XFM-1',
                              bus_from=bus_632,
                              bus_to=bus_634,
                              HV=4.16,
                              LV=0.48,
                              nominal_power=0.5,
                              rate=0.5,
                              r=1.1 * 2,
                              x=2 * 2)
    XFM_1.conn_f = WindingType.GroundedStar
    XFM_1.conn_t = WindingType.GroundedStar
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Line
    # ----------------------------------------------------------------------------------------------------------------------
    z_nabc = np.array([
        [0.2735 + 1j * 0.8143, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509],
        [0.0173 + 1j * 0.0509, 0.3465 + 1j * 1.0179, 0.1560 + 1j * 0.5017, 0.1580 + 1j * 0.4236],
        [0.0173 + 1j * 0.0509, 0.1560 + 1j * 0.5017, 0.3375 + 1j * 1.0478, 0.1535 + 1j * 0.3849],
        [0.0173 + 1j * 0.0509, 0.1580 + 1j * 0.4236, 0.1535 + 1j * 0.3849, 0.3414 + 1j * 1.0348]
    ], dtype=complex) / 1.60934  # Ω/km

    y_nabc = np.array([
        [1j * 6.1541, -1j * 1.8918, -1j * 2.0022, -1j * 2.2602],
        [-1j * 1.8918, 1j * 6.2998, -1j * 1.9958, -1j * 1.2595],
        [-1j * 2.0022, -1j * 1.9958, 1j * 5.9597, -1j * 0.7417],
        [-1j * 2.2602, -1j * 1.2595, -1j * 0.7417, 1j * 5.6386]
    ], dtype=complex) / (10 ** 6) / 1.60934  # S/km

    configuration = gce.create_known_abc_overhead_template(name='4 wire line',
                                                           z_nabc=z_nabc,
                                                           ysh_nabc=y_nabc,
                                                           phases=np.array([0, 1, 2, 3]),
                                                           Vnom=4.16,
                                                           frequency=60)
    grid.add_overhead_line(configuration)

    line = gce.Line(bus_from=bus_634,
                    bus_to=bus_636,
                    length=100 * 0.0003048)
    line.apply_template(configuration, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_636 = gce.Load(P1=0.3,
                        Q1=0.3,
                        P2=0.2,
                        Q2=0.2,
                        P3=0.1,
                        Q3=0.1)
    load_636.conn = ShuntConnectionType.NeutralStar
    grid.add_load(bus=bus_636, api_obj=load_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                 retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Un_reference = np.array(
        [0.0 + 0.j, 0.0 + 0.0j, 0.0712553 + 0.00193702j])

    Ua_reference = np.array(
        [1 + 0j, 0.92287771 - 0.01695593j, 0.80547372 - 0.04669537j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.48617629 - 0.82950043j, -0.52455549 - 0.79104599j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.48529631 + 0.85389286j, -0.50104669 + 0.84141899j])

    assert np.allclose(res.voltage_N, Un_reference, atol=1e-4)
    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_yy_power_neutralstar_1ph():
    '''
    This test executes a three-phase power flow with neutral into a Yy transformer with a NeutralStar load.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = gce.Logger()
    grid = gce.MultiCircuit()
    grid.fBase = 60

    # ----------------------------------------------------------------------------------------------------------------------
    # Buses
    # ----------------------------------------------------------------------------------------------------------------------
    bus_632 = gce.Bus(name='Bus632', Vnom=4.16, xpos=0, ypos=0)
    bus_632.is_slack = True
    grid.add_bus(obj=bus_632)
    gen = gce.Generator()
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    bus_636 = gce.Bus(name='Bus636', Vnom=0.48, xpos=400 * 5, ypos=0)
    grid.add_bus(obj=bus_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Transformer
    # ----------------------------------------------------------------------------------------------------------------------
    XFM_1 = gce.Transformer2W(name='XFM-1',
                              bus_from=bus_632,
                              bus_to=bus_634,
                              HV=4.16,
                              LV=0.48,
                              nominal_power=0.5,
                              rate=0.5,
                              r=1.1 * 2,
                              x=2 * 2)
    XFM_1.conn_f = WindingType.GroundedStar
    XFM_1.conn_t = WindingType.GroundedStar
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Line
    # ----------------------------------------------------------------------------------------------------------------------
    z_nabc = np.array([
        [0.2735 + 1j * 0.8143, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509],
        [0.0173 + 1j * 0.0509, 0.3465 + 1j * 1.0179, 0.1560 + 1j * 0.5017, 0.1580 + 1j * 0.4236],
        [0.0173 + 1j * 0.0509, 0.1560 + 1j * 0.5017, 0.3375 + 1j * 1.0478, 0.1535 + 1j * 0.3849],
        [0.0173 + 1j * 0.0509, 0.1580 + 1j * 0.4236, 0.1535 + 1j * 0.3849, 0.3414 + 1j * 1.0348]
    ], dtype=complex) / 1.60934  # Ω/km

    y_nabc = np.array([
        [1j * 6.1541, -1j * 1.8918, -1j * 2.0022, -1j * 2.2602],
        [-1j * 1.8918, 1j * 6.2998, -1j * 1.9958, -1j * 1.2595],
        [-1j * 2.0022, -1j * 1.9958, 1j * 5.9597, -1j * 0.7417],
        [-1j * 2.2602, -1j * 1.2595, -1j * 0.7417, 1j * 5.6386]
    ], dtype=complex) / (10 ** 6) / 1.60934  # S/km

    configuration = gce.create_known_abc_overhead_template(name='4 wire line',
                                                           z_nabc=z_nabc,
                                                           ysh_nabc=y_nabc,
                                                           phases=np.array([0, 1, 2, 3]),
                                                           Vnom=4.16,
                                                           frequency=60)
    grid.add_overhead_line(configuration)

    line = gce.Line(bus_from=bus_634,
                    bus_to=bus_636,
                    length=100 * 0.0003048)
    line.apply_template(configuration, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_636 = gce.Load(P1=0.25,
                        Q1=0.25)
    load_636.conn = ShuntConnectionType.NeutralStar
    grid.add_load(bus=bus_636, api_obj=load_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                 retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Un_reference = np.array(
        [0.0 + 0.j, 0.0 + 0.0j, 0.08964536 + 0.03243423j])

    Ua_reference = np.array(
        [1 + 0j, 0.93517937 - 0.01100169j, 0.82128169 - 0.05165573j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.5 - 0.8660254j, -0.55201025 - 0.8863471j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.5 + 0.86602541j, -0.54491559 + 0.85163798j])

    assert np.allclose(res.voltage_N, Un_reference, atol=1e-4)
    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_dy_impedance_neutralstar_3ph():
    '''
    This test executes a three-phase power flow with neutral into a Dy transformer with a NeutralStar load.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = gce.Logger()
    grid = gce.MultiCircuit()
    grid.fBase = 60

    # ----------------------------------------------------------------------------------------------------------------------
    # Buses
    # ----------------------------------------------------------------------------------------------------------------------
    bus_632 = gce.Bus(name='Bus632', Vnom=4.16, xpos=0, ypos=0)
    bus_632.is_slack = True
    grid.add_bus(obj=bus_632)
    gen = gce.Generator()
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    bus_636 = gce.Bus(name='Bus636', Vnom=0.48, xpos=400 * 5, ypos=0)
    grid.add_bus(obj=bus_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Transformer
    # ----------------------------------------------------------------------------------------------------------------------
    XFM_1 = gce.Transformer2W(name='XFM-1',
                              bus_from=bus_632,
                              bus_to=bus_634,
                              HV=4.16,
                              LV=0.48,
                              nominal_power=0.5,
                              rate=0.5,
                              r=1.1 * 2,
                              x=2 * 2)
    XFM_1.conn_f = WindingType.Delta
    XFM_1.conn_t = WindingType.GroundedStar
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Line
    # ----------------------------------------------------------------------------------------------------------------------
    z_nabc = np.array([
        [0.2735 + 1j * 0.8143, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509],
        [0.0173 + 1j * 0.0509, 0.3465 + 1j * 1.0179, 0.1560 + 1j * 0.5017, 0.1580 + 1j * 0.4236],
        [0.0173 + 1j * 0.0509, 0.1560 + 1j * 0.5017, 0.3375 + 1j * 1.0478, 0.1535 + 1j * 0.3849],
        [0.0173 + 1j * 0.0509, 0.1580 + 1j * 0.4236, 0.1535 + 1j * 0.3849, 0.3414 + 1j * 1.0348]
    ], dtype=complex) / 1.60934  # Ω/km

    y_nabc = np.array([
        [1j * 6.1541, -1j * 1.8918, -1j * 2.0022, -1j * 2.2602],
        [-1j * 1.8918, 1j * 6.2998, -1j * 1.9958, -1j * 1.2595],
        [-1j * 2.0022, -1j * 1.9958, 1j * 5.9597, -1j * 0.7417],
        [-1j * 2.2602, -1j * 1.2595, -1j * 0.7417, 1j * 5.6386]
    ], dtype=complex) / (10 ** 6) / 1.60934  # S/km

    configuration = gce.create_known_abc_overhead_template(name='4 wire line',
                                                           z_nabc=z_nabc,
                                                           ysh_nabc=y_nabc,
                                                           phases=np.array([0, 1, 2, 3]),
                                                           Vnom=4.16,
                                                           frequency=60)
    grid.add_overhead_line(configuration)

    line = gce.Line(bus_from=bus_634,
                    bus_to=bus_636,
                    length=100 * 0.0003048)
    line.apply_template(configuration, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_636 = gce.Load(G1=0.3,
                        B1=0.3,
                        G2=0.2,
                        B2=0.2,
                        G3=0.1,
                        B3=0.1)
    load_636.conn = ShuntConnectionType.NeutralStar
    grid.add_load(bus=bus_636, api_obj=load_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                 retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Un_reference = np.array(
        [0.0 + 0.j, 0.0 + 0.0j, 0.03367965 - 0.00745322j])

    Ua_reference = np.array(
        [1 + 0j, 0.95218447 - 0.01265888j, 0.88472009 - 0.02766787j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.48833169 - 0.83113485j, -0.50673344 - 0.78847722j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.48579392 + 0.85298809j, -0.48303905 + 0.84349284j])

    assert np.allclose(abs(res.voltage_N), abs(Un_reference), atol=1e-4)
    assert np.allclose(abs(res.voltage_A), abs(Ua_reference), atol=1e-4)
    assert np.allclose(abs(res.voltage_B), abs(Ub_reference), atol=1e-4)
    assert np.allclose(abs(res.voltage_C), abs(Uc_reference), atol=1e-4)


def test_dy_impedance_neutralstar_1ph():
    '''
    This test executes a three-phase power flow with neutral into a Dy transformer with a NeutralStar load.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = gce.Logger()
    grid = gce.MultiCircuit()
    grid.fBase = 60

    # ----------------------------------------------------------------------------------------------------------------------
    # Buses
    # ----------------------------------------------------------------------------------------------------------------------
    bus_632 = gce.Bus(name='Bus632', Vnom=4.16, xpos=0, ypos=0)
    bus_632.is_slack = True
    grid.add_bus(obj=bus_632)
    gen = gce.Generator()
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    bus_636 = gce.Bus(name='Bus636', Vnom=0.48, xpos=400 * 5, ypos=0)
    grid.add_bus(obj=bus_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Transformer
    # ----------------------------------------------------------------------------------------------------------------------
    XFM_1 = gce.Transformer2W(name='XFM-1',
                              bus_from=bus_632,
                              bus_to=bus_634,
                              HV=4.16,
                              LV=0.48,
                              nominal_power=0.5,
                              rate=0.5,
                              r=1.1 * 2,
                              x=2 * 2)
    XFM_1.conn_f = WindingType.Delta
    XFM_1.conn_t = WindingType.GroundedStar
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Line
    # ----------------------------------------------------------------------------------------------------------------------
    z_nabc = np.array([
        [0.2735 + 1j * 0.8143, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509],
        [0.0173 + 1j * 0.0509, 0.3465 + 1j * 1.0179, 0.1560 + 1j * 0.5017, 0.1580 + 1j * 0.4236],
        [0.0173 + 1j * 0.0509, 0.1560 + 1j * 0.5017, 0.3375 + 1j * 1.0478, 0.1535 + 1j * 0.3849],
        [0.0173 + 1j * 0.0509, 0.1580 + 1j * 0.4236, 0.1535 + 1j * 0.3849, 0.3414 + 1j * 1.0348]
    ], dtype=complex) / 1.60934  # Ω/km

    y_nabc = np.array([
        [1j * 6.1541, -1j * 1.8918, -1j * 2.0022, -1j * 2.2602],
        [-1j * 1.8918, 1j * 6.2998, -1j * 1.9958, -1j * 1.2595],
        [-1j * 2.0022, -1j * 1.9958, 1j * 5.9597, -1j * 0.7417],
        [-1j * 2.2602, -1j * 1.2595, -1j * 0.7417, 1j * 5.6386]
    ], dtype=complex) / (10 ** 6) / 1.60934  # S/km

    configuration = gce.create_known_abc_overhead_template(name='4 wire line',
                                                           z_nabc=z_nabc,
                                                           ysh_nabc=y_nabc,
                                                           phases=np.array([0, 1, 2, 3]),
                                                           Vnom=4.16,
                                                           frequency=60)
    grid.add_overhead_line(configuration)

    line = gce.Line(bus_from=bus_634,
                    bus_to=bus_636,
                    length=100 * 0.0003048)
    line.apply_template(configuration, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_636 = gce.Load(G1=0.3,
                        B1=0.3)
    load_636.conn = ShuntConnectionType.NeutralStar
    grid.add_load(bus=bus_636, api_obj=load_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                 retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Un_reference = np.array(
        [0.0 + 0.j, 0.0 + 0.0j, 0.06355538 + 0.02535082j])

    Ua_reference = np.array(
        [1 + 0j, 0.95375511 - 0.00939879j, 0.8729928 - 0.04120997j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.5 - 0.8660254j, -0.53683847 - 0.88181239j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.5 + 0.86602541j, -0.53188686 + 0.85466038j])

    assert np.allclose(abs(res.voltage_N), abs(Un_reference), atol=1e-4)
    assert np.allclose(abs(res.voltage_A), abs(Ua_reference), atol=1e-4)
    assert np.allclose(abs(res.voltage_B), abs(Ub_reference), atol=1e-4)
    assert np.allclose(abs(res.voltage_C), abs(Uc_reference), atol=1e-4)


def test_dy_current_neutralstar_3ph():
    '''
    This test executes a three-phase power flow with neutral into a Dy transformer with a NeutralStar load.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = gce.Logger()
    grid = gce.MultiCircuit()
    grid.fBase = 60

    # ----------------------------------------------------------------------------------------------------------------------
    # Buses
    # ----------------------------------------------------------------------------------------------------------------------
    bus_632 = gce.Bus(name='Bus632', Vnom=4.16, xpos=0, ypos=0)
    bus_632.is_slack = True
    grid.add_bus(obj=bus_632)
    gen = gce.Generator()
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    bus_636 = gce.Bus(name='Bus636', Vnom=0.48, xpos=400 * 5, ypos=0)
    grid.add_bus(obj=bus_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Transformer
    # ----------------------------------------------------------------------------------------------------------------------
    XFM_1 = gce.Transformer2W(name='XFM-1',
                              bus_from=bus_632,
                              bus_to=bus_634,
                              HV=4.16,
                              LV=0.48,
                              nominal_power=0.5,
                              rate=0.5,
                              r=1.1 * 2,
                              x=2 * 2)
    XFM_1.conn_f = WindingType.Delta
    XFM_1.conn_t = WindingType.GroundedStar
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Line
    # ----------------------------------------------------------------------------------------------------------------------
    z_nabc = np.array([
        [0.2735 + 1j * 0.8143, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509],
        [0.0173 + 1j * 0.0509, 0.3465 + 1j * 1.0179, 0.1560 + 1j * 0.5017, 0.1580 + 1j * 0.4236],
        [0.0173 + 1j * 0.0509, 0.1560 + 1j * 0.5017, 0.3375 + 1j * 1.0478, 0.1535 + 1j * 0.3849],
        [0.0173 + 1j * 0.0509, 0.1580 + 1j * 0.4236, 0.1535 + 1j * 0.3849, 0.3414 + 1j * 1.0348]
    ], dtype=complex) / 1.60934  # Ω/km

    y_nabc = np.array([
        [1j * 6.1541, -1j * 1.8918, -1j * 2.0022, -1j * 2.2602],
        [-1j * 1.8918, 1j * 6.2998, -1j * 1.9958, -1j * 1.2595],
        [-1j * 2.0022, -1j * 1.9958, 1j * 5.9597, -1j * 0.7417],
        [-1j * 2.2602, -1j * 1.2595, -1j * 0.7417, 1j * 5.6386]
    ], dtype=complex) / (10 ** 6) / 1.60934  # S/km

    configuration = gce.create_known_abc_overhead_template(name='4 wire line',
                                                           z_nabc=z_nabc,
                                                           ysh_nabc=y_nabc,
                                                           phases=np.array([0, 1, 2, 3]),
                                                           Vnom=4.16,
                                                           frequency=60)
    grid.add_overhead_line(configuration)

    line = gce.Line(bus_from=bus_634,
                    bus_to=bus_636,
                    length=100 * 0.0003048)
    line.apply_template(configuration, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_636 = gce.Load(Ir1=0.3,
                        Ii1=0.3,
                        Ir2=0.2,
                        Ii2=0.2,
                        Ir3=0.1,
                        Ii3=0.1)
    load_636.conn = ShuntConnectionType.NeutralStar
    grid.add_load(bus=bus_636, api_obj=load_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                 retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Un_reference = np.array(
        [0.0 + 0.j, 0.0 + 0.0j, 0.04394597 - 0.00583965j])

    Ua_reference = np.array(
        [1 + 0j, 0.94368741 - 0.01431683j, 0.86213519 - 0.0333338j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.48724257 - 0.82945044j, -0.51086938 - 0.78601869j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.48555138 + 0.85312744j, -0.48768898 + 0.84309991j])

    assert np.allclose(abs(res.voltage_N), abs(Un_reference), atol=1e-4)
    assert np.allclose(abs(res.voltage_A), abs(Ua_reference), atol=1e-4)
    assert np.allclose(abs(res.voltage_B), abs(Ub_reference), atol=1e-4)
    assert np.allclose(abs(res.voltage_C), abs(Uc_reference), atol=1e-4)


def test_dy_current_neutralstar_1ph():
    '''
    This test executes a three-phase power flow with neutral into a Dy transformer with a NeutralStar load.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = gce.Logger()
    grid = gce.MultiCircuit()
    grid.fBase = 60

    # ----------------------------------------------------------------------------------------------------------------------
    # Buses
    # ----------------------------------------------------------------------------------------------------------------------
    bus_632 = gce.Bus(name='Bus632', Vnom=4.16, xpos=0, ypos=0)
    bus_632.is_slack = True
    grid.add_bus(obj=bus_632)
    gen = gce.Generator()
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    bus_636 = gce.Bus(name='Bus636', Vnom=0.48, xpos=400 * 5, ypos=0)
    grid.add_bus(obj=bus_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Transformer
    # ----------------------------------------------------------------------------------------------------------------------
    XFM_1 = gce.Transformer2W(name='XFM-1',
                              bus_from=bus_632,
                              bus_to=bus_634,
                              HV=4.16,
                              LV=0.48,
                              nominal_power=0.5,
                              rate=0.5,
                              r=1.1 * 2,
                              x=2 * 2)
    XFM_1.conn_f = WindingType.Delta
    XFM_1.conn_t = WindingType.GroundedStar
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Line
    # ----------------------------------------------------------------------------------------------------------------------
    z_nabc = np.array([
        [0.2735 + 1j * 0.8143, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509],
        [0.0173 + 1j * 0.0509, 0.3465 + 1j * 1.0179, 0.1560 + 1j * 0.5017, 0.1580 + 1j * 0.4236],
        [0.0173 + 1j * 0.0509, 0.1560 + 1j * 0.5017, 0.3375 + 1j * 1.0478, 0.1535 + 1j * 0.3849],
        [0.0173 + 1j * 0.0509, 0.1580 + 1j * 0.4236, 0.1535 + 1j * 0.3849, 0.3414 + 1j * 1.0348]
    ], dtype=complex) / 1.60934  # Ω/km

    y_nabc = np.array([
        [1j * 6.1541, -1j * 1.8918, -1j * 2.0022, -1j * 2.2602],
        [-1j * 1.8918, 1j * 6.2998, -1j * 1.9958, -1j * 1.2595],
        [-1j * 2.0022, -1j * 1.9958, 1j * 5.9597, -1j * 0.7417],
        [-1j * 2.2602, -1j * 1.2595, -1j * 0.7417, 1j * 5.6386]
    ], dtype=complex) / (10 ** 6) / 1.60934  # S/km

    configuration = gce.create_known_abc_overhead_template(name='4 wire line',
                                                           z_nabc=z_nabc,
                                                           ysh_nabc=y_nabc,
                                                           phases=np.array([0, 1, 2, 3]),
                                                           Vnom=4.16,
                                                           frequency=60)
    grid.add_overhead_line(configuration)

    line = gce.Line(bus_from=bus_634,
                    bus_to=bus_636,
                    length=100 * 0.0003048)
    line.apply_template(configuration, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_636 = gce.Load(Ir1=0.3,
                        Ii1=0.3)
    load_636.conn = ShuntConnectionType.NeutralStar
    grid.add_load(bus=bus_636, api_obj=load_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                 retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Un_reference = np.array(
        [0.0 + 0.j, 0.0 + 0.0j, 0.07883374 + 0.02971871j])

    Ua_reference = np.array(
        [1 + 0j, 0.94285011 - 0.01048665j, 0.84268244 - 0.04775512j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.5 - 0.8660254j, -0.54571984 - 0.88459665j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.5 + 0.86602541j, -0.53952055 + 0.85278177j])

    assert np.allclose(abs(res.voltage_N), abs(Un_reference), atol=1e-4)
    assert np.allclose(abs(res.voltage_A), abs(Ua_reference), atol=1e-4)
    assert np.allclose(abs(res.voltage_B), abs(Ub_reference), atol=1e-4)
    assert np.allclose(abs(res.voltage_C), abs(Uc_reference), atol=1e-4)


def test_dy_power_neutralstar_3ph():
    '''
    This test executes a three-phase power flow with neutral into a Dy transformer with a NeutralStar load.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = gce.Logger()
    grid = gce.MultiCircuit()
    grid.fBase = 60

    # ----------------------------------------------------------------------------------------------------------------------
    # Buses
    # ----------------------------------------------------------------------------------------------------------------------
    bus_632 = gce.Bus(name='Bus632', Vnom=4.16, xpos=0, ypos=0)
    bus_632.is_slack = True
    grid.add_bus(obj=bus_632)
    gen = gce.Generator()
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    bus_636 = gce.Bus(name='Bus636', Vnom=0.48, xpos=400 * 5, ypos=0)
    grid.add_bus(obj=bus_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Transformer
    # ----------------------------------------------------------------------------------------------------------------------
    XFM_1 = gce.Transformer2W(name='XFM-1',
                              bus_from=bus_632,
                              bus_to=bus_634,
                              HV=4.16,
                              LV=0.48,
                              nominal_power=0.5,
                              rate=0.5,
                              r=1.1 * 2,
                              x=2 * 2)
    XFM_1.conn_f = WindingType.Delta
    XFM_1.conn_t = WindingType.GroundedStar
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Line
    # ----------------------------------------------------------------------------------------------------------------------
    z_nabc = np.array([
        [0.2735 + 1j * 0.8143, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509],
        [0.0173 + 1j * 0.0509, 0.3465 + 1j * 1.0179, 0.1560 + 1j * 0.5017, 0.1580 + 1j * 0.4236],
        [0.0173 + 1j * 0.0509, 0.1560 + 1j * 0.5017, 0.3375 + 1j * 1.0478, 0.1535 + 1j * 0.3849],
        [0.0173 + 1j * 0.0509, 0.1580 + 1j * 0.4236, 0.1535 + 1j * 0.3849, 0.3414 + 1j * 1.0348]
    ], dtype=complex) / 1.60934  # Ω/km

    y_nabc = np.array([
        [1j * 6.1541, -1j * 1.8918, -1j * 2.0022, -1j * 2.2602],
        [-1j * 1.8918, 1j * 6.2998, -1j * 1.9958, -1j * 1.2595],
        [-1j * 2.0022, -1j * 1.9958, 1j * 5.9597, -1j * 0.7417],
        [-1j * 2.2602, -1j * 1.2595, -1j * 0.7417, 1j * 5.6386]
    ], dtype=complex) / (10 ** 6) / 1.60934  # S/km

    configuration = gce.create_known_abc_overhead_template(name='4 wire line',
                                                           z_nabc=z_nabc,
                                                           ysh_nabc=y_nabc,
                                                           phases=np.array([0, 1, 2, 3]),
                                                           Vnom=4.16,
                                                           frequency=60)
    grid.add_overhead_line(configuration)

    line = gce.Line(bus_from=bus_634,
                    bus_to=bus_636,
                    length=100 * 0.0003048)
    line.apply_template(configuration, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_636 = gce.Load(P1=0.3,
                        Q1=0.3,
                        P2=0.2,
                        Q2=0.2,
                        P3=0.1,
                        Q3=0.1)
    load_636.conn = ShuntConnectionType.NeutralStar
    grid.add_load(bus=bus_636, api_obj=load_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                 retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Un_reference = np.array(
        [0.0 + 0.j, 0.0 + 0.0j, 0.0712553 + 0.00193702j])

    Ua_reference = np.array(
        [1 + 0j, 0.92287771 - 0.01695593j, 0.80547372 - 0.04669537j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.48617629 - 0.82950043j, -0.52455549 - 0.79104599j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.48529631 + 0.85389286j, -0.50104669 + 0.84141899j])

    assert np.allclose(abs(res.voltage_N), abs(Un_reference), atol=1e-4)
    assert np.allclose(abs(res.voltage_A), abs(Ua_reference), atol=1e-4)
    assert np.allclose(abs(res.voltage_B), abs(Ub_reference), atol=1e-4)
    assert np.allclose(abs(res.voltage_C), abs(Uc_reference), atol=1e-4)


def test_dy_power_neutralstar_1ph():
    '''
    This test executes a three-phase power flow with neutral into a Dy transformer with a NeutralStar load.
    The obtained results are compared against the ones obtained in OpenDSS.
    '''

    logger = gce.Logger()
    grid = gce.MultiCircuit()
    grid.fBase = 60

    # ----------------------------------------------------------------------------------------------------------------------
    # Buses
    # ----------------------------------------------------------------------------------------------------------------------
    bus_632 = gce.Bus(name='Bus632', Vnom=4.16, xpos=0, ypos=0)
    bus_632.is_slack = True
    grid.add_bus(obj=bus_632)
    gen = gce.Generator()
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    bus_636 = gce.Bus(name='Bus636', Vnom=0.48, xpos=400 * 5, ypos=0)
    grid.add_bus(obj=bus_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Transformer
    # ----------------------------------------------------------------------------------------------------------------------
    XFM_1 = gce.Transformer2W(name='XFM-1',
                              bus_from=bus_632,
                              bus_to=bus_634,
                              HV=4.16,
                              LV=0.48,
                              nominal_power=0.5,
                              rate=0.5,
                              r=1.1 * 2,
                              x=2 * 2)
    XFM_1.conn_f = WindingType.Delta
    XFM_1.conn_t = WindingType.GroundedStar
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Line
    # ----------------------------------------------------------------------------------------------------------------------
    z_nabc = np.array([
        [0.2735 + 1j * 0.8143, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509, 0.0173 + 1j * 0.0509],
        [0.0173 + 1j * 0.0509, 0.3465 + 1j * 1.0179, 0.1560 + 1j * 0.5017, 0.1580 + 1j * 0.4236],
        [0.0173 + 1j * 0.0509, 0.1560 + 1j * 0.5017, 0.3375 + 1j * 1.0478, 0.1535 + 1j * 0.3849],
        [0.0173 + 1j * 0.0509, 0.1580 + 1j * 0.4236, 0.1535 + 1j * 0.3849, 0.3414 + 1j * 1.0348]
    ], dtype=complex) / 1.60934  # Ω/km

    y_nabc = np.array([
        [1j * 6.1541, -1j * 1.8918, -1j * 2.0022, -1j * 2.2602],
        [-1j * 1.8918, 1j * 6.2998, -1j * 1.9958, -1j * 1.2595],
        [-1j * 2.0022, -1j * 1.9958, 1j * 5.9597, -1j * 0.7417],
        [-1j * 2.2602, -1j * 1.2595, -1j * 0.7417, 1j * 5.6386]
    ], dtype=complex) / (10 ** 6) / 1.60934  # S/km

    configuration = gce.create_known_abc_overhead_template(name='4 wire line',
                                                           z_nabc=z_nabc,
                                                           ysh_nabc=y_nabc,
                                                           phases=np.array([0, 1, 2, 3]),
                                                           Vnom=4.16,
                                                           frequency=60)
    grid.add_overhead_line(configuration)

    line = gce.Line(bus_from=bus_634,
                    bus_to=bus_636,
                    length=100 * 0.0003048)
    line.apply_template(configuration, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_636 = gce.Load(P1=0.25,
                        Q1=0.25)
    load_636.conn = ShuntConnectionType.NeutralStar
    grid.add_load(bus=bus_636, api_obj=load_636)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                 retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Un_reference = np.array(
        [0.0 + 0.j, 0.0 + 0.0j, 0.08964536 + 0.03243423j])

    Ua_reference = np.array(
        [1 + 0j, 0.93517937 - 0.01100169j, 0.82128169 - 0.05165573j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.5 - 0.8660254j, -0.55201025 - 0.8863471j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.5 + 0.86602541j, -0.54491559 + 0.85163798j])

    assert np.allclose(abs(res.voltage_N), abs(Un_reference), atol=1e-4)
    assert np.allclose(abs(res.voltage_A), abs(Ua_reference), atol=1e-4)
    assert np.allclose(abs(res.voltage_B), abs(Ub_reference), atol=1e-4)
    assert np.allclose(abs(res.voltage_C), abs(Uc_reference), atol=1e-4)
