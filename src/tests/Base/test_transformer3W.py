import os
import VeraGridEngine.api as vge
from VeraGridEngine import SolverType
import numpy as np

def test_transformer_3w():
    '''
    This test executes a power flow simulation into a three-bus system, where the buses are interconnected
    through a three-winding power transformer.

    The results are compared against the PowerFactory system solution.
    '''

    grid = vge.MultiCircuit()

    # -----------------------------------------------------------------------------------------------------------------
    #   Buses
    # -----------------------------------------------------------------------------------------------------------------
    hv_bus = vge.Bus(name='HV Bus', Vnom=110, xpos=0, ypos=0)
    hv_bus.is_slack = True
    grid.add_bus(obj=hv_bus)

    mv_bus = vge.Bus(name='MV Bus', Vnom=33, xpos=500, ypos=500)
    grid.add_bus(obj=mv_bus)

    lv_bus = vge.Bus(name='LV Bus', Vnom=0.4, xpos=-500, ypos=500)
    grid.add_bus(obj=lv_bus)

    # -----------------------------------------------------------------------------------------------------------------
    #   Transformer
    # -----------------------------------------------------------------------------------------------------------------
    trafo_3w = vge.Transformer3W(V1=110,
                                 V2=33,
                                 V3=0.4,
                                 bus1=hv_bus,
                                 bus2=mv_bus,
                                 bus3=lv_bus,
                                 x12=0.03,
                                 x23=0.03,
                                 x31=0.03,
                                 rate12=100.0,
                                 rate23=100.0,
                                 rate31=100.0)
    grid.add_transformer3w(obj=trafo_3w)
    trafo_3w.compute_delta_to_star()

    # -----------------------------------------------------------------------------------------------------------------
    #   Loads
    # -----------------------------------------------------------------------------------------------------------------
    mv_load = vge.Load(P=100,
                       Q=50)
    grid.add_load(bus=mv_bus, api_obj=mv_load)

    lv_load = vge.Load(P=50,
                       Q=10)
    grid.add_load(bus=lv_bus, api_obj=lv_load)

    # -----------------------------------------------------------------------------------------------------------------
    # Run power flow
    # -----------------------------------------------------------------------------------------------------------------
    res = vge.power_flow(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                 retry_with_other_methods=False))

    power_factory = np.array([1.0, 0.982548, 0.988753])

    assert np.allclose(np.abs(res.voltage[:3]), power_factory, atol=1e-5)


def test_transformer_3w_dgs():
    '''
    This test executes a power flow simulation into a three-bus system, where the buses are interconnected
    through a three-winding power transformer. In this case, the grid is not built in VeraGrid, but it is
    directly imported from the DGS.

    The results are compared against the PowerFactory system solution.
    '''

    # -----------------------------------------------------------------------------------------------------------------
    #   Grid Import
    # -----------------------------------------------------------------------------------------------------------------
    grid = vge.open_file(os.path.join('data','grids','three_winding_transformer.dgs'))
    grid.buses[0].is_slack = True

    # -----------------------------------------------------------------------------------------------------------------
    # Run Power Flow
    # -----------------------------------------------------------------------------------------------------------------
    res = vge.power_flow(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                 retry_with_other_methods=False))

    power_factory = np.array([1.0, 0.950238, 0.917207])

    assert np.allclose(np.abs(res.voltage[:3]), power_factory, atol=1e-5)