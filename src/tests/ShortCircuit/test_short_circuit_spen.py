import VeraGridEngine.api as vge
from VeraGridEngine import PowerFlowOptions, ShortCircuitOptions
from VeraGridEngine.enumerations import ConverterControlType, MethodShortCircuit, ConverterFaultControlType
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import SolverType
import numpy as np


def test_spen_west():

    grid = vge.open_file('data/grids/DGS/test_reduced_spen_v10.dgs')

    pf_options = PowerFlowOptions(control_taps_modules=False)
    res_pf = vge.power_flow(grid=grid, options=pf_options)

    DUNH0G = 1.0177
    WHLL0G = 1.0174
    TWEN0G = 1.0182
    SNQR0G = 1.0108
    SAKN0G = 1.0013
    AFTO0G = 1.0159
    WNDR0G = 1.0024
    NOKY0B = 1.0087
    NOKY0A = 1.0087
    SOKY0G = 1.0091
    ENHI0G = 1.0086
    DESA0G = 1.0089
    BLKS0G = 1.0189

    assert np.allclose(np.abs(res_pf.voltage[11]), DUNH0G, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[47]), WHLL0G, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[45]), TWEN0G, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[40]), SNQR0G, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[37]), SAKN0G, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[0]), AFTO0G, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[49]), WNDR0G, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[33]), NOKY0B, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[32]), NOKY0A, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[42]), SOKY0G, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[17]), ENHI0G, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[8]), DESA0G, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[6]), BLKS0G, atol=1e-4)