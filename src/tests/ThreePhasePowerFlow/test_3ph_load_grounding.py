"""Explicit load neutrals follow the same grounding rules as shunts."""
import numpy as np
import pytest

import VeraGridEngine.api as vg
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.Simulations.PowerFlow3ph.Formulations.pf_basic_formulation_3ph import compute_ybus


def grounding_grid():
    grid = vg.MultiCircuit(Sbase=1.0)
    source = grid.add_bus(vg.Bus(name='Source', Vnom=10, is_slack=True))
    target = grid.add_bus(vg.Bus(name='Load bus', Vnom=10))
    grid.add_generator(source, vg.Generator())
    z = np.array([[.5+.8j, .06+.25j, .05+.2j, .04+.15j],
                  [.06+.25j, .3+.7j, .1+.3j, .1+.2j],
                  [.05+.2j, .1+.3j, .3+.7j, .1+.25j],
                  [.04+.15j, .1+.2j, .1+.25j, .3+.7j]])
    tower = vg.create_known_abc_overhead_template(
        name='Four conductors', z_nabc=z, ysh_nabc=np.zeros((4, 4), dtype=complex),
        phases=np.arange(4), Vnom=10)
    grid.add_overhead_line(tower)
    line = vg.Line(bus_from=source, bus_to=target, length=1.0)
    line.apply_template(tower, grid.Sbase, grid.fBase)
    grid.add_line(line)
    load = vg.Load(P1=.3, P2=.2, P3=.1, Q1=.1, Q2=.07, Q3=.04)
    load.conn = vg.ShuntConnectionType.GroundedStar
    grid.add_load(target, load)
    return grid, load


@pytest.mark.parametrize('connection,phn,active,grounded', [
    (vg.ShuntConnectionType.GroundedStar, True, True, True),
    (vg.ShuntConnectionType.GroundedStar, False, True, False),
    (vg.ShuntConnectionType.GroundedStar, True, False, False),
    (vg.ShuntConnectionType.NeutralStar, True, True, False),
    (vg.ShuntConnectionType.FloatingStar, True, True, False),
    (vg.ShuntConnectionType.Delta, True, True, False),
])
def test_load_grounding_requires_active_yg_and_connected_neutral(connection, phn, active, grounded):
    grid, load = grounding_grid()
    load.conn = connection
    load.phN = phn
    load.active = active
    nc = compile_numerical_circuit_at(grid, fill_three_phase=True)
    # Exercise both the copied data and the island path used by the driver.
    for circuit in (nc, nc.copy(), *nc.split_into_islands()):
        _, _, _, _, mask, _, _ = compute_ybus(circuit)
        bus = list(circuit.bus_data.names).index('Load bus')
        assert bool(mask[4 * bus]) is not grounded


def test_yg_load_phn_matches_grounding_shunt_in_four_wire_power_flow():
    grid, load = grounding_grid()
    options = vg.PowerFlowOptions(
        solver_type=vg.SolverType.NR, retry_with_other_methods=False,
        tolerance=1e-10, max_iter=50, control_q=False,
        control_taps_modules=False, control_taps_phase=False,
        apply_temperature_correction=False)
    ungrounded = vg.power_flow3ph(grid, options=options)
    load.phN = True
    grounded = vg.power_flow3ph(grid, options=options)
    load.phN = False
    shunt = vg.Shunt()
    shunt.conn = vg.ShuntConnectionType.GroundedStar
    shunt.phN = True
    grid.add_shunt(load.bus, shunt)
    reference = vg.power_flow3ph(grid, options=options)
    assert ungrounded.converged and grounded.converged and reference.converged
    assert abs(ungrounded.voltage_N[1]) > 1e-5
    assert grounded.voltage_N[1] == 0
    for name in ('voltage_A', 'voltage_B', 'voltage_C', 'voltage_N',
                 'If_A', 'If_B', 'If_C', 'If_N'):
        np.testing.assert_allclose(getattr(grounded, name), getattr(reference, name), rtol=0, atol=1e-9)
    assert grid.lines[0].ys.phN
