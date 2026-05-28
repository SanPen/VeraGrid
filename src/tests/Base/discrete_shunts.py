import VeraGridEngine.api as vge
from VeraGridEngine import SolverType, ShuntControlMode
import numpy as np

def test_discrete_shunt():

    grid = vge.MultiCircuit()

    # ----------------------------------------------------------------------------------------------------------------------
    #   Buses
    # ----------------------------------------------------------------------------------------------------------------------
    bus_slack = vge.Bus(name='Slack Bus', xpos=0, ypos=0)
    bus_slack.is_slack = True
    grid.add_bus(obj=bus_slack)

    bus_shunt = vge.Bus(name='Shunt Bus', xpos=-500, ypos=500)
    grid.add_bus(obj=bus_shunt)

    bus_load = vge.Bus(name='Load Bus', xpos=500, ypos=500)
    grid.add_bus(obj=bus_load)

    # ----------------------------------------------------------------------------------------------------------------------
    #   Generator
    # ----------------------------------------------------------------------------------------------------------------------
    gen = vge.Generator()
    grid.add_generator(bus=bus_slack, api_obj=gen)

    # ----------------------------------------------------------------------------------------------------------------------
    #   Lines
    # ----------------------------------------------------------------------------------------------------------------------
    Ub = 10e3
    Sb = 100e6
    Zb = Ub ** 2 / Sb

    line_slack_shunt = vge.Line(name='Line Slack-Shunt',
                                bus_from=bus_slack,
                                bus_to=bus_shunt,
                                r=0.1 / Zb,
                                x=1 / Zb)
    grid.add_line(obj=line_slack_shunt)

    line_slack_load = vge.Line(name='Line Slack-Load',
                               bus_from=bus_slack,
                               bus_to=bus_load,
                               r=0.2 / Zb,
                               x=2 / Zb)
    grid.add_line(obj=line_slack_load)

    line_shunt_load = vge.Line(name='Line Shunt-Load',
                               bus_from=bus_shunt,
                               bus_to=bus_load,
                               r=0.1 / Zb,
                               x=1 / Zb)
    grid.add_line(obj=line_shunt_load)

    # ----------------------------------------------------------------------------------------------------------------------
    #   Shunt
    # ----------------------------------------------------------------------------------------------------------------------
    shunt = vge.ControllableShunt(name='Shunt',
                                  number_of_steps=2,
                                  step=0,
                                  g_per_step=0.0,
                                  b_per_step=3.0,
                                  vmin=0.95,
                                  vmax=1.05,
                                  control_mode=ShuntControlMode.Discrete)
    grid.add_controllable_shunt(bus=bus_shunt, api_obj=shunt)

    # ----------------------------------------------------------------------------------------------------------------------
    #   Load
    # ----------------------------------------------------------------------------------------------------------------------
    load = vge.Load(name='Load',
                    P=18,
                    Q=9)
    grid.add_load(bus=bus_load, api_obj=load)

    # ----------------------------------------------------------------------------------------------------------------------
    #   Run Power Flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = vge.power_flow(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                 retry_with_other_methods=False))

    power_factory = np.array([1.0, 0.96921, 0.88907])

    assert np.allclose(np.abs(res.voltage), power_factory, atol=1e-5)