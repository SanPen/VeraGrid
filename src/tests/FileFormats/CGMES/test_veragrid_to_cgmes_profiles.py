"""Profile-aware CGMES export tests."""

import numpy as np

import VeraGridEngine.Devices as dev
from VeraGridEngine.IO.cim.cgmes.cgmes_circuit import CgmesCircuit
from VeraGridEngine.IO.cim.cgmes.veragrid_to_cgmes import veragrid_to_cgmes
from VeraGridEngine.data_logger import DataLogger
from VeraGridEngine.enumerations import CGMESVersions


def test_veragrid_to_cgmes_uses_profile_values_when_t_idx_is_provided() -> None:
    """CGMES export must use profile values when ``t_idx`` is provided."""

    grid: dev.MultiCircuit = dev.MultiCircuit(name="cgmes-profile-export")

    bus_1: dev.Bus = dev.Bus(name="B1", Vnom=110.0)
    bus_2: dev.Bus = dev.Bus(name="B2", Vnom=110.0)
    grid.add_bus(bus_1)
    grid.add_bus(bus_2)

    load: dev.Load = dev.Load(name="LD1", P=10.0, Q=5.0, Ir=1.0, Ii=2.0, G=3.0, B=4.0, active=True)
    load.P_prof = np.array([10.0, 20.0])
    load.Q_prof = np.array([5.0, 6.0])
    load.Ir_prof = np.array([1.0, 2.0])
    load.Ii_prof = np.array([2.0, 3.0])
    load.G_prof = np.array([3.0, 4.0])
    load.B_prof = np.array([4.0, 5.0])
    grid.add_load(bus=bus_1, api_obj=load)

    external_grid: dev.ExternalGrid = dev.ExternalGrid(name="EG1", P=30.0, Q=7.0, active=True)
    external_grid.P_prof = np.array([30.0, 40.0])
    external_grid.Q_prof = np.array([7.0, 9.0])
    grid.add_external_grid(bus=bus_1, api_obj=external_grid)

    line: dev.Line = dev.Line(bus_from=bus_1, bus_to=bus_2, name="L12", r=0.01, x=0.05, b=0.001, rate=100.0)
    line.rate_prof = np.array([100.0, 200.0])
    line.contingency_factor_prof = np.array([1.1, 1.2])
    line.protection_rating_factor_prof = np.array([1.3, 1.4])
    grid.add_line(line)

    switch: dev.Switch = dev.Switch(bus_from=bus_1, bus_to=bus_2, name="SW12", active=True)
    switch.active_prof = np.array([True, False])
    grid.add_switch(switch)

    cgmes_model: CgmesCircuit = CgmesCircuit(cgmes_version=CGMESVersions.v2_4_15)
    logger: DataLogger = DataLogger()

    exported = veragrid_to_cgmes(
        gc_model=grid,
        num_circ=None,
        pf_results=None,
        cgmes_model=cgmes_model,
        logger=logger,
        t_idx=1,
    )

    exported_load = exported.cgmes_assets.ConformLoad_list[0]
    exported_external_grid = exported.cgmes_assets.ExternalNetworkInjection_list[0]
    exported_breaker = exported.cgmes_assets.Breaker_list[0]

    assert exported_load.p == 26.0
    assert exported_load.q == 14.0
    assert exported_load.LoadResponse.pConstantPower == np.round(20.0 / 26.0, 4)
    assert exported_load.LoadResponse.pConstantCurrent == np.round(2.0 / 26.0, 4)
    assert exported_load.LoadResponse.pConstantImpedance == np.round(4.0 / 26.0, 4)
    assert exported_load.LoadResponse.qConstantPower == np.round(6.0 / 14.0, 4)
    assert exported_load.LoadResponse.qConstantCurrent == np.round(3.0 / 14.0, 4)
    assert exported_load.LoadResponse.qConstantImpedance == np.round(5.0 / 14.0, 4)

    assert exported_external_grid.p == 40.0
    assert exported_external_grid.q == 9.0

    assert exported_breaker.open is True

    current_limits = exported.cgmes_assets.CurrentLimit_list
    current_limit_values = sorted({round(current_limit.value, 4) for current_limit in current_limits})
    expected_values = sorted({
        round(200.0 * 1e3 / (110.0 * np.sqrt(3.0)), 4),
        round(240.0 * 1e3 / (110.0 * np.sqrt(3.0)), 4),
        round(280.0 * 1e3 / (110.0 * np.sqrt(3.0)), 4),
    })

    assert len(current_limits) == 6
    assert current_limit_values == expected_values
