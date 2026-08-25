from types import SimpleNamespace

import VeraGridEngine.api as vge
from VeraGridEngine import SolverType
from VeraGridEngine.IO.dgs.dgs_to_veragrid import (
    _map_load_pq_to_global_phases,
    convert_dgs_to_shunt,
)
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import ShuntConnectionType
import numpy as np


def test_single_phase_phase_to_phase_load_and_shunt_mapping():
    load = SimpleNamespace(ID="load", loc_name="load", phtech="1PH PH-PH")
    shunt_source = SimpleNamespace(
        ID="shunt", loc_name="shunt", ctech=5, shtype=2,
        qtotn=1.0, ushnm=1.0, fres=250.0, grea=0.0,
        tandc=0.1, ncapa=1, ncapx=1, outserv=0,
    )
    cubic = SimpleNamespace(fold_id="bus", cPhInfo="DP1DP2", it2p1=0, it2p2=1, it2p3=2)
    bus = vge.Bus(name="bus")

    for phase_pair, branch_idx in {
        (1, 2): 0, (2, 1): 0,
        (2, 3): 1, (3, 2): 1,
        (3, 1): 2, (1, 3): 2,
    }.items():
        phase_map = {("bus", 0): phase_pair[0], ("bus", 1): phase_pair[1]}
        mapped = _map_load_pq_to_global_phases(
            elmlod=load,
            cubics_by_objid={"load": [cubic]},
            phase_map=phase_map,
            local_p=(1.0, 0.0, 0.0),
            local_q=(2.0, 0.0, 0.0),
            logger=Logger(),
        )
        expected = [0.0] * 6
        expected[branch_idx] = 1.0
        expected[branch_idx + 3] = 2.0
        assert np.allclose(mapped, expected)

        _, shunt = convert_dgs_to_shunt(
            elmshnt=shunt_source,
            stacubic_dict={},
            buses=[bus],
            logger=Logger(),
            cubics_by_objid={"shunt": [cubic]},
            bus_by_term_id={"bus": bus},
            phase_map=phase_map,
            frequency=50.0,
        )
        expected_g = [0.0] * 3
        expected_b = [0.0] * 3
        expected_g[branch_idx] = shunt.G
        expected_b[branch_idx] = shunt.B
        assert np.allclose([shunt.Ga, shunt.Gb, shunt.Gc], expected_g)
        assert np.allclose([shunt.Ba, shunt.Bb, shunt.Bc], expected_b)

def test_three_phase_power_delta():

    grid = vge.open_file('data/grids/DGS/ThreePhasePowerDelta.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9961])
    Ub_reference = np.array([0.9955])
    Uc_reference = np.array([0.9958])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=1e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=1e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=1e-4)

def test_three_phase_power_groundedstar():

    grid = vge.open_file('data/grids/DGS/ThreePhasePowerGroundedStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9872])
    Ub_reference = np.array([1.0023])
    Uc_reference = np.array([0.9984])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=1e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=1e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=1e-4)

def test_three_phase_power_neutralstar():

    grid = vge.open_file('data/grids/DGS/ThreePhasePowerNeutralStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9930])
    Ub_reference = np.array([0.9976])
    Uc_reference = np.array([0.9973])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=1e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=1e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=1e-4)

def test_two_phase_power_groundedstar():

    grid = vge.open_file('data/grids/DGS/TwoPhasePowerGroundedStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9818])
    Ub_reference = np.array([1.0055])
    Uc_reference = np.array([1.0025])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=1e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=1e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=1e-4)

def test_two_phase_power_neutralstar():

    grid = vge.open_file('data/grids/DGS/TwoPhasePowerNeutralStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9931])
    Ub_reference = np.array([0.9975])
    Uc_reference = np.array([0.9995])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=1e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=1e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=1e-4)

def test_two_phase_power_delta():

    grid = vge.open_file('data/grids/DGS/TwoPhasePowerDelta.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9981])
    Ub_reference = np.array([0.9901])
    Uc_reference = np.array([0.9991])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=1e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=1e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=1e-4)

def test_single_phase_power_neutralstar():

    grid = vge.open_file('data/grids/DGS/SinglePhasePowerNeutralStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9867])
    Ub_reference = np.array([1.0033])
    Uc_reference = np.array([0.9998])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=1e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=1e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=1e-4)

def test_single_phase_power_groundedstar():

    grid = vge.open_file('data/grids/DGS/SinglePhasePowerGroundedStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9744])
    Ub_reference = np.array([1.0280])
    Uc_reference = np.array([0.9876])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=1e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=1e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=1e-4)

def test_three_phase_current_delta():

    grid = vge.open_file('data/grids/DGS/ThreePhaseCurrentDelta.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9788])
    Ub_reference = np.array([0.9769])
    Uc_reference = np.array([0.9783])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=2e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=2e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=2e-4)

def test_three_phase_current_groundedstar():

    grid = vge.open_file('data/grids/DGS/ThreePhaseCurrentGroundedStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9402])
    Ub_reference = np.array([0.9987])
    Uc_reference = np.array([0.9969])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=2e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=2e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=2e-4)

def test_three_phase_current_neutralstar():

    grid = vge.open_file('data/grids/DGS/ThreePhaseCurrentNeutralStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9657])
    Ub_reference = np.array([0.9846])
    Uc_reference = np.array([0.9860])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=2e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=2e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=2e-4)

def test_two_phase_current_groundedstar():

    grid = vge.open_file('data/grids/DGS/TwoPhaseCurrentGroundedStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9100])
    Ub_reference = np.array([1.0187])
    Uc_reference = np.array([1.0188])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=2e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=2e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=2e-4)

def test_two_phase_current_neutralstar():

    grid = vge.open_file('data/grids/DGS/TwoPhaseCurrentNeutralStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9664])
    Ub_reference = np.array([0.9828])
    Uc_reference = np.array([0.9973])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=2e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=2e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=2e-4)

def test_two_phase_current_delta():

    grid = vge.open_file('data/grids/DGS/TwoPhaseCurrentDelta.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9896])
    Ub_reference = np.array([0.9476])
    Uc_reference = np.array([0.9954])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=2e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=2e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=2e-4)

def test_single_phase_current_neutralstar():

    grid = vge.open_file('data/grids/DGS/SinglePhaseCurrentNeutralStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9252])
    Ub_reference = np.array([1.0169])
    Uc_reference = np.array([0.9991])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=1e-3)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=2e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=3e-4)

def test_single_phase_current_groundedstar():

    grid = vge.open_file('data/grids/DGS/SinglePhaseCurrentGroundedStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.8536])
    Ub_reference = np.array([1.1432])
    Uc_reference = np.array([0.9605])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=1e-3)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=2e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=2e-4)

def test_three_phase_impedance_delta():

    grid = vge.open_file('data/grids/DGS/ThreePhaseImpedanceDelta.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9792])
    Ub_reference = np.array([0.9774])
    Uc_reference = np.array([0.9788])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=1e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=1e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=1e-4)

def test_three_phase_impedance_groundedstar():

    grid = vge.open_file('data/grids/DGS/ThreePhaseImpedanceGroundedStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9442])
    Ub_reference = np.array([0.9956])
    Uc_reference = np.array([0.9977])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=3e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=3e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=3e-4)

def test_three_phase_impedance_neutralstar():

    grid = vge.open_file('data/grids/DGS/ThreePhaseImpedanceNeutralStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9676])
    Ub_reference = np.array([0.9846])
    Uc_reference = np.array([0.9858])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=3e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=3e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=3e-4)

def test_two_phase_impedance_groundedstar():

    grid = vge.open_file('data/grids/DGS/TwoPhaseImpedanceGroundedStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9158])
    Ub_reference = np.array([1.0129])
    Uc_reference = np.array([1.0206])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=3e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=3e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=3e-4)

def test_two_phase_impedance_neutralstar():

    grid = vge.open_file('data/grids/DGS/TwoPhaseImpedanceNeutralStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9693])
    Ub_reference = np.array([0.9825])
    Uc_reference = np.array([0.9973])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=3e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=3e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=3e-4)

def test_two_phase_impedance_delta():

    grid = vge.open_file('data/grids/DGS/TwoPhaseImpedanceDelta.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9900])
    Ub_reference = np.array([0.9500])
    Uc_reference = np.array([0.9954])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=4e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=4e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=4e-4)

def test_single_phase_impedance_neutralstar():

    grid = vge.open_file('data/grids/DGS/SinglePhaseImpedanceNeutralStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9399])
    Ub_reference = np.array([1.0137])
    Uc_reference = np.array([0.9990])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=4e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=4e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=4e-4)

def test_single_phase_impedance_groundedstar():

    grid = vge.open_file('data/grids/DGS/SinglePhaseImpedanceGroundedStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.8743])
    Ub_reference = np.array([1.1255])
    Uc_reference = np.array([0.9617])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=4e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=4e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=4e-4)

def test_single_phase_transformer_dd_non_auto_phase_a():

    grid = vge.open_file('data/grids/DGS/DDconnection_non_auto_phaseA.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9911, 0.9790])
    Ub_reference = np.array([1.0032, 0.0])
    Uc_reference = np.array([0.9990, 0.0])

    assert np.allclose(np.abs(res.voltage_A[1:]), Ua_reference, atol=2e-4)
    assert np.allclose(np.abs(res.voltage_B[1:]), Ub_reference, atol=2e-4)
    assert np.allclose(np.abs(res.voltage_C[1:]), Uc_reference, atol=2e-4)

def test_single_phase_transformer_dd_non_auto_phase_b():

    grid = vge.open_file('data/grids/DGS/DDconnection_non_auto_phaseB.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([0.9993, 0.0])
    Ub_reference = np.array([0.9911, 0.9790])
    Uc_reference = np.array([1.0029, 0.0])

    assert np.allclose(np.abs(res.voltage_A[1:]), Ua_reference, atol=2e-4)
    assert np.allclose(np.abs(res.voltage_B[1:]), Ub_reference, atol=2e-4)
    assert np.allclose(np.abs(res.voltage_C[1:]), Uc_reference, atol=2e-4)

def test_single_phase_transformer_dd_non_auto_phase_c():

    grid = vge.open_file('data/grids/DGS/DDconnection_non_auto_phaseC.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([1.0037, 0.0])
    Ub_reference = np.array([0.9994, 0.0])
    Uc_reference = np.array([0.9910, 0.9790])

    assert np.allclose(np.abs(res.voltage_A[1:]), Ua_reference, atol=2e-4)
    assert np.allclose(np.abs(res.voltage_B[1:]), Ub_reference, atol=2e-4)
    assert np.allclose(np.abs(res.voltage_C[1:]), Uc_reference, atol=2e-4)

def test_single_phase_transformer_dd_non_auto_phases_ab():

    grid = vge.open_file('data/grids/DGS/DDconnection_non_auto_phasesAB.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    U_reference = 2 * 0.8516 / np.sqrt(3)
    U_result = np.abs(res.voltage_A[2] - res.voltage_B[2]) / np.sqrt(3)

    assert np.allclose(U_result, U_reference, atol=3e-4)
    assert np.allclose(np.abs(res.voltage_C[2]), np.array([0.0]), atol=3e-4)

def test_single_phase_transformer_dd_non_auto_phases_bc():

    grid = vge.open_file('data/grids/DGS/DDconnection_non_auto_phasesBC.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    U_reference = 2 * 0.8515 / np.sqrt(3)
    U_result = np.abs(res.voltage_B[2] - res.voltage_C[2]) / np.sqrt(3)

    assert np.allclose(U_result, U_reference, atol=3e-4)
    assert np.allclose(np.abs(res.voltage_A[2]), np.array([0.0]), atol=3e-4)

def test_single_phase_transformer_dd_non_auto_phases_ca():

    grid = vge.open_file('data/grids/DGS/DDconnection_non_auto_phasesCA.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    U_reference = 2 * 0.8517 / np.sqrt(3)
    U_result = np.abs(res.voltage_C[2] - res.voltage_A[2]) / np.sqrt(3)

    assert np.allclose(U_result, U_reference, atol=3e-4)
    assert np.allclose(np.abs(res.voltage_B[2]), np.array([0.0]), atol=3e-4)

def test_three_phase_shunt_delta():

    grid = vge.open_file('data/grids/DGS/ThreePhaseShuntDelta.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([1.0657])
    Ub_reference = np.array([1.0696])
    Uc_reference = np.array([1.0740])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=7e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=7e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=7e-4)

def test_three_phase_shunt_floatingstar():

    grid = vge.open_file('data/grids/DGS/ThreePhaseShuntFloatingStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([1.0657])
    Ub_reference = np.array([1.0696])
    Uc_reference = np.array([1.0740])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=7e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=7e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=7e-4)

def test_three_phase_shunt_groundedstar():

    grid = vge.open_file('data/grids/DGS/ThreePhaseShuntGroundedStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([1.0647])
    Ub_reference = np.array([1.0720])
    Uc_reference = np.array([1.0726])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=8e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=8e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=8e-4)

def test_three_phase_shunt_neutralstar():

    grid = vge.open_file('data/grids/DGS/ThreePhaseShuntNeutralStar.dgs')

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    Ua_reference = np.array([1.0655])
    Ub_reference = np.array([1.0701])
    Uc_reference = np.array([1.0738])

    assert np.allclose(np.abs(res.voltage_A[0]), Ua_reference, atol=7e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), Ub_reference, atol=7e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), Uc_reference, atol=7e-4)


def test_two_phase_shunt_groundedstar():

    grid = vge.open_file('data/grids/DGS/TwoPhaseShuntGroundedStar.dgs')

    shunt = grid.shunts[0]
    assert shunt.conn == ShuntConnectionType.GroundedStar
    assert np.allclose([shunt.Ga, shunt.Gb, shunt.Gc], [shunt.G / 2, shunt.G / 2, 0.0])
    assert np.allclose([shunt.Ba, shunt.Bb, shunt.Bc], [shunt.B / 2, shunt.B / 2, 0.0])

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    assert np.allclose(np.abs(res.voltage_A[0]), 1.19354539, atol=1.4e-3)
    assert np.allclose(np.abs(res.voltage_B[0]), 1.26976973, atol=1.4e-3)
    assert np.allclose(np.abs(res.voltage_C[0]), 0.80848763, atol=1.4e-3)


def test_two_phase_shunt_neutralstar():

    grid = vge.open_file('data/grids/DGS/TwoPhaseShuntNeutralStar.dgs')

    shunt = grid.shunts[0]
    assert shunt.conn == ShuntConnectionType.NeutralStar
    assert np.allclose([shunt.Ga, shunt.Gb, shunt.Gc], [shunt.G / 2, shunt.G / 2, 0.0])
    assert np.allclose([shunt.Ba, shunt.Bb, shunt.Bc], [shunt.B / 2, shunt.B / 2, 0.0])

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    assert np.allclose(np.abs(res.voltage_A[0]), 1.08670826, atol=8e-4)
    assert np.allclose(np.abs(res.voltage_B[0]), 1.05714628, atol=8e-4)
    assert np.allclose(np.abs(res.voltage_C[0]), 0.99975613, atol=8e-4)


def test_single_phase_shunt_neutralstar():

    grid = vge.open_file('data/grids/DGS/SinglePhaseShuntNeutralStar.dgs')

    shunt = grid.shunts[0]
    assert shunt.conn == ShuntConnectionType.NeutralStar
    assert shunt.phN
    assert np.allclose([shunt.Ga, shunt.Gb, shunt.Gc], [shunt.G, 0.0, 0.0])
    assert np.allclose([shunt.Ba, shunt.Bb, shunt.Bc], [shunt.B, 0.0, 0.0])

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    assert np.allclose(np.abs(res.voltage_A[0]), 1.26972831, atol=6.8e-3)
    assert np.allclose(np.abs(res.voltage_B[0]), 0.99643802, atol=6.8e-3)
    assert np.allclose(np.abs(res.voltage_C[0]), 0.99437431, atol=6.8e-3)


def test_single_phase_shunt_groundedstar():

    grid = vge.open_file('data/grids/DGS/SinglePhaseShuntGroundedStar.dgs')

    shunt = grid.shunts[0]
    assert shunt.conn == ShuntConnectionType.GroundedStar
    assert not shunt.phN
    assert np.allclose([shunt.Ga, shunt.Gb, shunt.Gc], [shunt.G, 0.0, 0.0])
    assert np.allclose([shunt.Ba, shunt.Bb, shunt.Bc], [shunt.B, 0.0, 0.0])

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    assert np.allclose(np.abs(res.voltage_A[0]), 1.80876365, atol=5.2e-3)
    assert np.allclose(np.abs(res.voltage_B[0]), 1.00474040, atol=5.2e-3)
    assert np.allclose(np.abs(res.voltage_C[0]), 0.73614587, atol=5.2e-3)


def test_two_phase_shunt_floatingstar():

    grid = vge.open_file('data/grids/DGS/TwoPhaseShuntFloatingStar.dgs')

    shunt = grid.shunts[0]
    assert shunt.conn == ShuntConnectionType.Delta
    assert np.allclose([shunt.Ga, shunt.Gb, shunt.Gc], [shunt.G, 0.0, 0.0])
    assert np.allclose([shunt.Ba, shunt.Bb, shunt.Bc], [shunt.B, 0.0, 0.0])

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    assert np.allclose(np.abs(res.voltage_A[0]), 1.11959425, atol=1.1e-3)
    assert np.allclose(np.abs(res.voltage_B[0]), 1.07862183, atol=1.1e-3)
    assert np.allclose(np.abs(res.voltage_C[0]), 0.99953762, atol=1.1e-3)

def test_two_phase_shunt_delta():

    grid = vge.open_file('data/grids/DGS/TwoPhaseShuntDelta.dgs')

    shunt = grid.shunts[0]
    assert shunt.conn == ShuntConnectionType.Delta
    assert np.allclose([shunt.Ga, shunt.Gb, shunt.Gc], [shunt.G, 0.0, 0.0])
    assert np.allclose([shunt.Ba, shunt.Bb, shunt.Bc], [shunt.B, 0.0, 0.0])

    res = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(solver_type=SolverType.NR,
                                                                    retry_with_other_methods=False))

    assert np.allclose(np.abs(res.voltage_A[0]), 1.11959425, atol=1.1e-3)
    assert np.allclose(np.abs(res.voltage_B[0]), 1.07862183, atol=1.1e-3)
    assert np.allclose(np.abs(res.voltage_C[0]), 0.99953762, atol=1.1e-3)
