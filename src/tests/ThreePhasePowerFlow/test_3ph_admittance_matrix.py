import numpy as np
import VeraGridEngine.api as vge

def test_2x2_bc():

    line = vge.OverheadLineType()

    wire = vge.Wire(name="Panther 30/7 ACSR",
                    diameter=21.0,
                    diameter_internal=9.0,
                    is_tube=True,
                    r=0.1363,
                    max_current=1)

    line.add_wire_relationship(wire=wire,
                               xpos=-1,
                               ypos=10,
                               phase=2
    )

    line.add_wire_relationship(wire=wire,
                               xpos=1,
                               ypos=10,
                               phase=3
                               )

    line.compute()

    obtained_ys = line.get_ys(circuit_idx=1, Sbase=100.0, length=1.0, Vnom=10.0)
    obtained_ysh = line.get_ysh(circuit_idx=1, Sbase=100.0, length=1.0, Vnom=10.0)

    correct_ys = np.array([
        [0. + 0.j, 0. + 0.j, 0. + 0.j, 0. + 0.j],
        [0. + 0.j, 0. + 0.j, 0. + 0.j, 0. + 0.j],
        [0. + 0.j, 0. + 0.j, 0.59449198 - 1.69333179j, -0.41531796 + 0.83431634j],
        [0. + 0.j, 0. + 0.j, -0.41531796 + 0.83431634j, 0.59449198 - 1.69333179j]
    ])

    correct_ysh = np.array([
        [0. + 0.j, 0. + 0.j, 0. + 0.j, 0. + 0.j],
        [0. + 0.j, 0. + 0.j, 0. + 0.j, 0. + 0.j],
        [0. + 0.j, 0. + 0.j, +0. + 2.55256035j, -0. - 0.77993899j],
        [0. + 0.j, 0. + 0.j, -0. - 0.77993899j, +0. + 2.55256035j]
    ])

    assert np.allclose(obtained_ys.values, correct_ys, atol=1e-4)
    assert np.allclose(obtained_ysh.values, correct_ysh, atol=1e-4)

def test_3x3_abc():

    line = vge.OverheadLineType()

    wire = vge.Wire(name="Panther 30/7 ACSR",
                    diameter=21.0,
                    diameter_internal=9.0,
                    is_tube=True,
                    r=0.1363,
                    max_current=1)

    line.add_wire_relationship(wire=wire,
                               xpos=-1,
                               ypos=10,
                               phase=1
    )

    line.add_wire_relationship(wire=wire,
                               xpos=0,
                               ypos=10,
                               phase=2
    )

    line.add_wire_relationship(wire=wire,
                               xpos=1,
                               ypos=10,
                               phase=3
                               )

    line.compute()

    obtained_ys = line.get_ys(circuit_idx=1, Sbase=100.0, length=1.0, Vnom=10.0)
    obtained_ysh = line.get_ysh(circuit_idx=1, Sbase=100.0, length=1.0, Vnom=10.0)

    correct_ys = np.array([
        [0. + 0.j, 0. + 0.j, 0. + 0.j, 0. + 0.j],
        [0. + 0.j, 0.78416059 - 1.96468603j, -0.42934099 + 0.75717701j, -0.22564935 + 0.56296209j],
        [0. + 0.j, -0.42934099 + 0.75717701j, 0.93652163 - 2.08809006j, -0.42934099 + 0.75717701j],
        [0. + 0.j, -0.22564935 + 0.56296209j, -0.42934099 + 0.75717701j, 0.78416059 - 1.96468603j]
    ])

    correct_ysh = np.array([
        [0. + 0.j, 0. + 0.j, 0. + 0.j, 0. + 0.j],
        [0. + 0.j, 0. + 2.83436888j, -0. - 0.927113j, -0. - 0.49813046j],
        [0. + 0.j, -0. - 0.927113j, 0. + 3.05007988j, -0. - 0.927113j],
        [0. + 0.j, -0. - 0.49813046j, -0. - 0.927113j, +0. + 2.83436888j]
    ])

    assert np.allclose(obtained_ys.values, correct_ys, atol=1e-4)
    assert np.allclose(obtained_ysh.values, correct_ysh, atol=1e-4)


def test_order_phases():
    """
    This test intentionally modifies the defined phase order (NABC) by modelling an overhead line in which the neutral
    conductor is placed in the third position (ABNC).

    VeraGrid handles this configuration internally by automatically reordering the phases to the predefined reference
    order (NABC) before solving the system.
    """

    logger = vge.Logger()
    grid = vge.MultiCircuit()
    grid.fBase = 60

    # ----------------------------------------------------------------------------------------------------------------------
    # Buses
    # ----------------------------------------------------------------------------------------------------------------------
    bus_slack = vge.Bus(name='Slack', Vnom=4.16, xpos=0, ypos=0)
    bus_slack.is_slack = True
    grid.add_bus(obj=bus_slack)
    gen = vge.Generator()
    grid.add_generator(bus=bus_slack, api_obj=gen)

    bus_load = vge.Bus(name='Load', Vnom=4.16, xpos=400 * 5, ypos=0)
    grid.add_bus(obj=bus_load)

    # ----------------------------------------------------------------------------------------------------------------------
    # Line
    # ----------------------------------------------------------------------------------------------------------------------
    Zbase = (4.16 * 4.16) / 100
    z_nabc = np.array([
        [1j * (1 / 1), 1j * 0.0, 1j * 0.0, 1j * 0.0],
        [1j * 0.0, 1j * (1 / 2), 1j * 0.0, 1j * 0.0],
        [1j * 0.0, 1j * 0.0, 1j * (1 / 0.001), 1j * 0.0],
        [1j * 0.0, 1j * 0.0, 1j * 0.0, 1j * (1 / 3)]
    ], dtype=complex) * Zbase

    Ybase = 1 / Zbase
    y_nabc = np.array([
        [1j * 1.0, 0.0, 0.0, 0.0],
        [0.0, 1j * 2.0, 0.0, 0.0],
        [0.0, 0.0, 1j * 0.001, 0.0],
        [0.0, 0.0, 0.0, 1j * 3.0]
    ], dtype=complex) / 1e6 * Ybase

    configuration = vge.create_known_abc_overhead_template(name='4 wire line',
                                                           z_nabc=z_nabc,
                                                           ysh_nabc=y_nabc,
                                                           phases=np.array([1, 2, 0, 3]),
                                                           Vnom=4.16,
                                                           frequency=60)
    grid.add_overhead_line(configuration)

    line = vge.Line(bus_from=bus_slack,
                    bus_to=bus_load)
    line.apply_template(configuration, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line)

    y_ref = np.array([
        [1j * 0.001, 0.0, 0.0, 0.0],
        [0.0, 1j * 1, 0.0, 0.0],
        [0.0, 0.0, 1j * 2, 0.0],
        [0.0, 0.0, 0.0, 1j * 3]
    ], dtype=complex)

    assert np.allclose(line.ys.values, y_ref * -1, atol=1e-4)
    assert np.allclose(line.ysh.values, y_ref, atol=1e-4)