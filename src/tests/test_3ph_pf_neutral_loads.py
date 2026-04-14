import VeraGridEngine.api as gce
from VeraGridEngine import WindingType, ShuntConnectionType, SolverType
import numpy as np


def test_impedance_groundedstar_3ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase load connected in GroundedStar.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(G1=0.7,
                        B1=0.5,
                        G2=0.6,
                        B2=0.45,
                        G3=0.5,
                        B3=0.4)
    load_634.conn = ShuntConnectionType.GroundedStar
    grid.add_load(bus=bus_634, api_obj=load_634)

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
    XFM_1.phases = np.array([1, 2, 3])
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Ua_reference = np.array(
        [1 + 0j, 0.90207824 - 0.04158922j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.48710729 - 0.77306215j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.4372112 + 0.81472313j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_impedance_floatingstar_3ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase load connected in GroundedStar.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(G1=0.7,
                        B1=0.5,
                        G2=0.6,
                        B2=0.45,
                        G3=0.5,
                        B3=0.4)
    load_634.conn = ShuntConnectionType.FloatingStar
    grid.add_load(bus=bus_634, api_obj=load_634)

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
    XFM_1.phases = np.array([1, 2, 3])
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Un_reference = np.array(
        [0.07318343 - 0.02992788j]
    )

    Ua_reference = np.array(
        [1 + 0j, 0.91048917 - 0.04147616j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.47968669 - 0.77307996j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.43080248 + 0.81455613j])

    assert np.allclose(res.load_Vn, Un_reference, atol=1e-4)
    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_impedance_neutralstar_3ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase load connected in GroundedStar.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=4.16, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(G1=0.7,
                        B1=0.5,
                        G2=0.6,
                        B2=0.45,
                        G3=0.5,
                        B3=0.4)
    load_634.conn = ShuntConnectionType.NeutralStar
    grid.add_load(bus=bus_634, api_obj=load_634)

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

    line = gce.Line(bus_from=bus_632,
                    bus_to=bus_634,
                    length=2000 * 0.0003048)
    line.apply_template(configuration, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Ua_reference = np.array(
        [1 + 0.j, 0.96704514 - 0.016661j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.51101077 - 0.83803284j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.47984984 + 0.85244212j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_impedance_delta_3ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase load connected in GroundedStar.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(G1=0.7,
                        B1=0.5,
                        G2=0.6,
                        B2=0.45,
                        G3=0.5,
                        B3=0.4)
    load_634.conn = ShuntConnectionType.Delta
    grid.add_load(bus=bus_634, api_obj=load_634)

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
    XFM_1.phases = np.array([1, 2, 3])
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Ua_reference = np.array(
        [1 + 0j, 0.91678499 - 0.04164258j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.48340674 - 0.76670763j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.43337825 + 0.80835022j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_impedance_delta_2ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase load connected in GroundedStar.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(G1=0.7,
                        B1=0.5,
                        G2=0.0,
                        B2=0.0,
                        G3=0.0,
                        B3=0.0)
    load_634.conn = ShuntConnectionType.Delta
    grid.add_load(bus=bus_634, api_obj=load_634)

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
    XFM_1.phases = np.array([1, 2, 3])
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Ua_reference = np.array(
        [1 + 0j, 0.96253052 - 0.05125713j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.46253242 - 0.81477074j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.5 + 0.8660254j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_impedance_groundedstar_1ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase load connected in GroundedStar.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(G1=0.7,
                        B1=0.5,
                        G2=0.0,
                        B2=0.0,
                        G3=0.0,
                        B3=0.0)
    load_634.conn = ShuntConnectionType.GroundedStar
    grid.add_load(bus=bus_634, api_obj=load_634)

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
    XFM_1.phases = np.array([1, 2, 3])
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Ua_reference = np.array(
        [1 + 0j, 0.90207824 - 0.04158922j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.5 - 0.8660254j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.5 + 0.8660254j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_impedance_neutralstar_1ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase load connected in GroundedStar.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=4.16, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(G1=0.7,
                        B1=0.5,
                        G2=0.0,
                        B2=0.0,
                        G3=0.0,
                        B3=0.0)
    load_634.conn = ShuntConnectionType.NeutralStar
    grid.add_load(bus=bus_634, api_obj=load_634)

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

    line = gce.Line(bus_from=bus_632,
                    bus_to=bus_634,
                    length=2000 * 0.0003048)
    line.apply_template(configuration, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Ua_reference = np.array(
        [1 + 0j, 0.95515256 - 0.02854518j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.52030794 - 0.87981365j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.51784639 + 0.85547383j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_current_groundedstar_3ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase current load connected in GroundedStar.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(Ir1=0.7,
                        Ii1=0.5,
                        Ir2=0.6,
                        Ii2=0.45,
                        Ir3=0.5,
                        Ii3=0.4)
    load_634.conn = ShuntConnectionType.GroundedStar
    grid.add_load(bus=bus_634, api_obj=load_634)

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
    XFM_1.phases = np.array([1, 2, 3])
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Ua_reference = np.array(
        [1 + 0j, 0.89133821 - 0.0455198j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.48551977 - 0.7643368j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.43223299 + 0.81036939j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_current_floatingstar_3ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase current load connected in FloatingStar.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(Ir1=0.7,
                        Ii1=0.5,
                        Ir2=0.6,
                        Ii2=0.45,
                        Ir3=0.5,
                        Ii3=0.4)
    load_634.conn = ShuntConnectionType.FloatingStar
    grid.add_load(bus=bus_634, api_obj=load_634)

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
    XFM_1.phases = np.array([1, 2, 3])
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Un_reference = np.array(
        [0.18977947 - 0.05024236j]
    )

    Ua_reference = np.array(
        [1 + 0j, 0.89375273 - 0.05090146j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.4679776 - 0.76843024j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.42577572 + 0.81932727j])

    assert np.allclose(res.load_Vn, Un_reference, atol=1e-4)
    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_current_neutralstar_3ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase current load connected in NeutralStar.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=4.16, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(Ir1=0.7,
                        Ii1=0.5,
                        Ir2=0.6,
                        Ii2=0.45,
                        Ir3=0.5,
                        Ii3=0.4)
    load_634.conn = ShuntConnectionType.NeutralStar
    grid.add_load(bus=bus_634, api_obj=load_634)

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

    line = gce.Line(bus_from=bus_632,
                    bus_to=bus_634,
                    length=2000 * 0.0003048)
    line.apply_template(configuration, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Ua_reference = np.array(
        [1 + 0.j, 0.96531932 - 0.01773808j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.5116578 - 0.83808239j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.4798735 + 0.8519028j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_current_delta_3ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase current load connected in Delta.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(Ir1=0.7,
                        Ii1=0.5,
                        Ir2=0.6,
                        Ii2=0.45,
                        Ir3=0.5,
                        Ii3=0.4)
    load_634.conn = ShuntConnectionType.Delta
    grid.add_load(bus=bus_634, api_obj=load_634)

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
    XFM_1.phases = np.array([1, 2, 3])
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Ua_reference = np.array(
        [1 + 0j, 0.90895297 - 0.04547238j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.48137856 - 0.75702959j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.4275744 + 0.80250197j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_current_delta_2ph():
    '''
    This test executes a three-phase power flow with neutral into a two-phase current load connected in Delta.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(Ir1=0.7,
                        Ii1=0.5)
    load_634.conn = ShuntConnectionType.Delta
    grid.add_load(bus=bus_634, api_obj=load_634)

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
    XFM_1.phases = np.array([1, 2, 3])
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Ua_reference = np.array(
        [1 + 0j, 0.95973492 - 0.05481973j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.45973492 - 0.81120567j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.5 + 0.8660254j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_current_groundedstar_1ph():
    '''
    This test executes a three-phase power flow with neutral into a single-phase current load connected in GroundedStar.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(Ir1=0.7,
                        Ii1=0.5,
                        Ir2=0.0,
                        Ii2=0.0,
                        Ir3=0.0,
                        Ii3=0.0)
    load_634.conn = ShuntConnectionType.GroundedStar
    grid.add_load(bus=bus_634, api_obj=load_634)

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
    XFM_1.phases = np.array([1, 2, 3])
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Ua_reference = np.array(
        [1 + 0j, 0.89133821 - 0.0455198j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.5 - 0.8660254j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.5 + 0.8660254j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_current_neutralstar_1ph():
    '''
    This test executes a three-phase power flow with neutral into a single-phase current load connected in NeutralStar.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=4.16, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(Ir1=0.7,
                        Ii1=0.5)
    load_634.conn = ShuntConnectionType.NeutralStar
    grid.add_load(bus=bus_634, api_obj=load_634)

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

    line = gce.Line(bus_from=bus_632,
                    bus_to=bus_634,
                    length=2000 * 0.0003048)
    line.apply_template(configuration, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Ua_reference = np.array(
        [1 + 0j, 0.95117569 - 0.03075078j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.52211318 - 0.88088602j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.51942473 + 0.85466506j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_power_groundedstar_3ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase power load connected in GroundedStar.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(P1=0.7,
                        Q1=0.5,
                        P2=0.6,
                        Q2=0.45,
                        P3=0.5,
                        Q3=0.4)
    load_634.conn = ShuntConnectionType.GroundedStar
    grid.add_load(bus=bus_634, api_obj=load_634)

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
    XFM_1.phases = np.array([1, 2, 3])
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Ua_reference = np.array(
        [1 + 0j, 0.875766 - 0.05099991j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.48323592 - 0.75238921j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.42576195 + 0.80464132j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_power_floatingstar_3ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase power load connected in FloatingStar.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(P1=0.7,
                        Q1=0.5,
                        P2=0.6,
                        Q2=0.45,
                        P3=0.5,
                        Q3=0.4)
    load_634.conn = ShuntConnectionType.FloatingStar
    grid.add_load(bus=bus_634, api_obj=load_634)

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
    XFM_1.phases = np.array([1, 2, 3])
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Un_reference = np.array(
        [0.07230224 - 0.25643776j]
    )

    Ua_reference = np.array(
        [1 + 0j, 0.88774199 - 0.08600408j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.44265466 - 0.73103072j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.44508733 + 0.8170348j])

    assert np.allclose(res.load_Vn, Un_reference, atol=1e-4)
    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_power_neutralstar_3ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase power load connected in NeutralStar.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=4.16, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(P1=0.7,
                        Q1=0.5,
                        P2=0.6,
                        Q2=0.45,
                        P3=0.5,
                        Q3=0.4)
    load_634.conn = ShuntConnectionType.NeutralStar
    grid.add_load(bus=bus_634, api_obj=load_634)

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

    line = gce.Line(bus_from=bus_632,
                    bus_to=bus_634,
                    length=2000 * 0.0003048)
    line.apply_template(configuration, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Ua_reference = np.array(
        [1 + 0.j, 0.96320896 - 0.01913199j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.51245622 - 0.83843789j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.47998138 + 0.85120291j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_power_delta_3ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase current load connected in Delta.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(P1=0.7,
                        Q1=0.5,
                        P2=0.6,
                        Q2=0.45,
                        P3=0.5,
                        Q3=0.4)
    load_634.conn = ShuntConnectionType.Delta
    grid.add_load(bus=bus_634, api_obj=load_634)

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
    XFM_1.phases = np.array([1, 2, 3])
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Ua_reference = np.array(
        [1 + 0j, 0.89819198 - 0.05067889j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.47847253 - 0.74366896j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.41971945 + 0.79434786j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_power_delta_2ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase load connected in GroundedStar.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(P1=0.7,
                        Q1=0.5)
    load_634.conn = ShuntConnectionType.Delta
    grid.add_load(bus=bus_634, api_obj=load_634)

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
    XFM_1.phases = np.array([1, 2, 3])
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Ua_reference = np.array(
        [1 + 0j, 0.95618688 - 0.05929551j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.45618688 - 0.80672989j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.5 + 0.8660254j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_power_groundedstar_1ph():
    '''
    This test executes a three-phase power flow with neutral into a single-phase power load connected in GroundedStar.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=0.48, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(P1=0.7,
                        Q1=0.5)
    load_634.conn = ShuntConnectionType.GroundedStar
    grid.add_load(bus=bus_634, api_obj=load_634)

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
    XFM_1.phases = np.array([1, 2, 3])
    grid.add_transformer2w(XFM_1)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Ua_reference = np.array(
        [1 + 0j, 0.875766 - 0.05099991j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.5 - 0.8660254j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.5 + 0.8660254j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_power_neutralstar_1ph():
    '''
    This test executes a three-phase power flow with neutral into a single-phase power load connected in NeutralStar.
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
    gen = gce.Generator(vset=1.0)
    grid.add_generator(bus=bus_632, api_obj=gen)

    bus_634 = gce.Bus(name='Bus634', Vnom=4.16, xpos=200 * 5, ypos=0)
    grid.add_bus(obj=bus_634)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load_634 = gce.Load(P1=0.7,
                        Q1=0.5)
    load_634.conn = ShuntConnectionType.NeutralStar
    grid.add_load(bus=bus_634, api_obj=load_634)

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

    line = gce.Line(bus_from=bus_632,
                    bus_to=bus_634,
                    length=2000 * 0.0003048)
    line.apply_template(configuration, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line)

    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = gce.power_flow3ph(grid=grid, options=gce.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    # ----------------------------------------------------------------------------------------------------------------------
    # Results
    # ----------------------------------------------------------------------------------------------------------------------
    Ua_reference = np.array(
        [1 + 0j, 0.94585508 - 0.03362593j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.52452943 - 0.88228579j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.52153542 + 0.85361253j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)
