import VeraGridEngine.api as gce
from VeraGridEngine import WindingType, ShuntConnectionType, SolverType
import numpy as np


def test_shunt_groundedstar_3ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase shunt connected in GroundedStar.
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
    shunt = gce.Shunt(B1=0.7,
                      B2=0.6,
                      B3=0.5)
    shunt.conn = ShuntConnectionType.GroundedStar
    grid.add_shunt(bus=bus_634, api_obj=shunt)

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
        [1 + 0j, 1.08893297-0.05492216j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.57756402-0.90857098j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.49895631+0.93882017j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_shunt_floatingstar_3ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase shunt connected in FloatingStar.
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
    shunt = gce.Shunt(B1=0.7,
                      B2=0.6,
                      B3=0.5)
    shunt.conn = ShuntConnectionType.FloatingStar
    grid.add_shunt(bus=bus_634, api_obj=shunt)

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
        [0.08814062-0.05504086j]
    )

    Ua_reference = np.array(
        [1 + 0j, 1.08411732-0.04518634j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.58170353-0.90036275j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.5024138+0.9455491j])

    assert np.allclose(res.shunt_Vn, Un_reference, atol=1e-4)
    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_shunt_neutralstar_3ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase shunt connected in NeutralStar.
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
    shunt = gce.Shunt(B1=0.7,
                      B2=0.6,
                      B3=0.5)
    shunt.conn = ShuntConnectionType.NeutralStar
    grid.add_shunt(bus=bus_634, api_obj=shunt)

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
        [1 + 0.j, 1.02980102-0.01708339j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.51135556-0.89033873j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.5005232+0.88324201j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_shunt_delta_3ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase shunt connected in Delta.
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
    shunt = gce.Shunt(B1=0.7,
                      B2=0.6,
                      B3=0.5)
    shunt.conn = ShuntConnectionType.Delta
    grid.add_shunt(bus=bus_634, api_obj=shunt)

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
        [1 + 0j, 1.08074599-0.03834548j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.58678775-0.90797257j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.49395824+0.94631805j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_shunt_delta_2ph():
    '''
    This test executes a three-phase power flow with neutral into a two-phase load connected in Delta.
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
    shunt = gce.Shunt(B1=0.7)
    shunt.conn = ShuntConnectionType.Delta
    grid.add_shunt(bus=bus_634, api_obj=shunt)

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
        [1 + 0j, 1.05859681-0.00069499j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.55859464-0.86533049j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.5+0.8660254j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_shunt_groundedstar_1ph():
    '''
    This test executes a three-phase power flow with neutral into a single-phase shunt connected in GroundedStar.
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
    shunt = gce.Shunt(B1=0.7)
    shunt.conn = ShuntConnectionType.GroundedStar
    grid.add_shunt(bus=bus_634, api_obj=shunt)

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
        [1 + 0j, 1.08893297-0.05492216j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.5 - 0.8660254j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.5 + 0.8660254j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)


def test_shunt_neutralstar_1ph():
    '''
    This test executes a three-phase power flow with neutral into a three-phase shunt connected in NeutralStar.
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
    shunt = gce.Shunt(B1=0.7)
    shunt.conn = ShuntConnectionType.NeutralStar
    grid.add_shunt(bus=bus_634, api_obj=shunt)

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
        [1 + 0j, 1.04776822-0.01783586j])

    Ub_reference = np.array(
        [-0.5 - 0.8660254j, -0.47771005-0.87360352j])

    Uc_reference = np.array(
        [-0.5 + 0.8660254j, -0.48160958+0.85846193j])

    assert np.allclose(res.voltage_A, Ua_reference, atol=1e-4)
    assert np.allclose(res.voltage_B, Ub_reference, atol=1e-4)
    assert np.allclose(res.voltage_C, Uc_reference, atol=1e-4)