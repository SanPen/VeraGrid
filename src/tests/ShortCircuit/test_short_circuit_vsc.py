import VeraGridEngine.api as vge
from VeraGridEngine import PowerFlowOptions, ShortCircuitOptions
from VeraGridEngine.enumerations import ConverterControlType, MethodShortCircuit
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import SolverType
import numpy as np

def test_short_circuit_vsc_3buses():

    logger = vge.Logger()
    grid = vge.MultiCircuit()

    # ----------------------------------------------------------------------------------------------------------------------
    #   Buses
    # ----------------------------------------------------------------------------------------------------------------------
    bus_dc = vge.Bus(name='Bus DC', xpos=0, ypos=0, is_dc=True)
    grid.add_bus(obj=bus_dc)

    bus_ac = vge.Bus(name='Bus AC', xpos=0, ypos=300, r_fault=0.2)
    grid.add_bus(obj=bus_ac)

    bus_slack = vge.Bus(name='Bus Slack', xpos=0, ypos=600, is_slack=True)
    grid.add_bus(obj=bus_slack)

    # ----------------------------------------------------------------------------------------------------------------------
    #   Line
    # ----------------------------------------------------------------------------------------------------------------------
    line_slack_ac = vge.Line(name='AC - Fault', bus_from=bus_ac, bus_to=bus_slack, r=0.001, x=0.1, rate=20.0)
    grid.add_line(line_slack_ac)

    # ----------------------------------------------------------------------------------------------------------------------
    #   VSC
    # ----------------------------------------------------------------------------------------------------------------------
    vsc = vge.VSC(bus_from=bus_dc,
                  bus_to=bus_ac,
                  rate=14.0,
                  alpha1=0.0,
                  alpha2=0.0,
                  alpha3=0.0,
                  control1=ConverterControlType.Vm_dc,
                  control2=ConverterControlType.Qac,
                  control1_val=1.0,
                  control2_val=-5.0)
    grid.add_vsc(vsc)

    # ----------------------------------------------------------------------------------------------------------------------
    #   Generators
    # ----------------------------------------------------------------------------------------------------------------------
    generator_ac = vge.Generator(r1=0.005, x1=0.05)
    grid.add_generator(bus_slack, generator_ac)

    generator_dc = vge.Generator(P=10.0, power_factor=1.0, r1=0.005)
    grid.add_generator(bus_dc, generator_dc)

    # ----------------------------------------------------------------------------------------------------------------------
    #   Save Grid
    # ----------------------------------------------------------------------------------------------------------------------
    vge.save_file(grid=grid, filename='shortcircuit_vsc.veragrid')

    # ----------------------------------------------------------------------------------------------------------------------
    #   AC/DC Power Flow under healthy conditions
    # ----------------------------------------------------------------------------------------------------------------------
    pf_options_1 = PowerFlowOptions(solver_type=SolverType.NR,
                                    retry_with_other_methods=False,
                                    limit_i_vsc=False,
                                    verbose=1)
    res_pf = vge.power_flow(grid=grid, options=pf_options_1)

    Upf_reference = np.array([1.0, 1.0050255, 1.0])

    assert np.allclose(abs(res_pf.voltage), Upf_reference, atol=1e-6)

    # ----------------------------------------------------------------------------------------------------------------------
    #   AC/DC Short-Circuit with converter's current limitation
    # ----------------------------------------------------------------------------------------------------------------------
    pf_options_2 = PowerFlowOptions(solver_type=SolverType.NR,
                                    retry_with_other_methods=False,
                                    limit_i_vsc=True,
                                    verbose=1)

    grid.add_short_circuit_event(
        vge.ShortCircuitEvent(
            device=grid.buses[1],
            method=MethodShortCircuit.sequences_vsc
        )
    )

    sc_driver = vge.ShortCircuitDriver(grid=grid,
                                       options=ShortCircuitOptions(),
                                       pf_options=pf_options_2,
                                       pf_results=res_pf,
                                       pf_results3ph=None)
    sc_driver.run()

    res_sc = sc_driver.results

    Usc_reference = np.array([
        [1.0],
        [0.79744135],
        [0.88393066]
    ])

    assert np.allclose(abs(res_sc.voltage1), Usc_reference, atol=1e-6)