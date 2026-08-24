# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
from typing import Dict
import numpy as np
import VeraGridEngine.api as vg
from VeraGridEngine.Compilers.Gslv.activation import GSLV_AVAILABLE, pg
from VeraGridEngine.Compilers.Gslv.compare import compare_nc, CheckArr
from VeraGridEngine.Compilers.Gslv.common import set_generator_associations, set_injection_associations
from VeraGridEngine.Compilers.Gslv.conversion import to_gslv


class AssociationRecorder:
    """
    Record GSLV-style association insertions made through ``add_object``.
    """

    __slots__ = ("values",)

    def __init__(self) -> None:
        """
        Initialize an empty association value lookup.

        :return: None.
        """
        self.values: Dict[object, float] = dict()

    def add_object(self, api_obj: object, val: float) -> None:
        """
        Store one association exactly as the GSLV wrapper receives it.

        :param api_obj: Target associated object.
        :param val: Association value.
        :return: None.
        """
        self.values[api_obj] = float(val)


class GslvInjectionRecorder:
    """
    Minimal GSLV injection stand-in exposing the copied association fields.
    """

    __slots__ = ("facility", "technologies")

    def __init__(self) -> None:
        """
        Initialize empty association targets.

        :return: None.
        """
        self.facility: object | None = None
        self.technologies: AssociationRecorder = AssociationRecorder()


class GslvGeneratorRecorder:
    """
    Minimal GSLV generator stand-in exposing generator association fields.
    """

    __slots__ = ("facility", "technologies", "fuels", "emissions")

    def __init__(self) -> None:
        """
        Initialize empty generator association targets.

        :return: None.
        """
        self.facility: object | None = None
        self.technologies: AssociationRecorder = AssociationRecorder()
        self.fuels: AssociationRecorder = AssociationRecorder()
        self.emissions: AssociationRecorder = AssociationRecorder()


def compare_inputs(grid_gslv: "pg.MultiCircuit", grid_gc: vg.MultiCircuit, tol=1e-6, t_idx=None):
    """

    :param grid_gslv:
    :param grid_gc:
    :param tol:
    :param t_idx:
    :return:
    """
    # ------------------------------------------------------------------------------------------------------------------
    #  compile snapshots
    # ------------------------------------------------------------------------------------------------------------------

    if t_idx is None:
        nc_gslv = pg.compile(grid=grid_gslv, logger=pg.Logger(), t_idx=0)
        nc_gc = vg.compile_numerical_circuit_at(circuit=grid_gc, t_idx=None)
    else:
        nc_gslv = pg.compile(grid=grid_gslv, logger=pg.Logger(), t_idx=t_idx)
        nc_gc = vg.compile_numerical_circuit_at(circuit=grid_gc, t_idx=t_idx)

    # ------------------------------------------------------------------------------------------------------------------
    #  Compare base data
    errors = compare_nc(nc_gslv=nc_gslv, nc_gc=nc_gc, tol=tol)

    # compare islands
    gslv_islands = nc_gslv.split_into_islands()
    gc_islands = nc_gc.split_into_islands()

    assert len(gslv_islands) == len(gc_islands)

    for i in range(len(gslv_islands)):
        print("*" * 200)
        print("Comparing island", i)
        print("*" * 200)
        errors += compare_nc(nc_gslv=gslv_islands[i], nc_gc=gc_islands[i], tol=tol)

    return errors


def compare_power_flow(grid_gslv: "pg.MultiCircuit", grid_gc: vg.MultiCircuit, tol=1e-6):
    """

    :param grid_gslv:
    :param grid_gc:
    :param tol:
    :return:
    """
    gc_options = vg.PowerFlowOptions(vg.SolverType.NR,
                                      verbose=False,
                                      tolerance=1e-6,
                                      retry_with_other_methods=True,
                                      control_q=False,
                                      max_iter=15)
    gc_power_flow = vg.PowerFlowDriver(grid_gc, gc_options)
    gc_power_flow.run()
    gridcal_res = gc_power_flow.results

    pf_opt = pg.PowerFlowOptions(verbose=False,
                                 solver_type=pg.SolverType.NR,
                                 tolerance=1e-6,
                                 retry_with_other_methods=True,
                                 control_q_mode=False,
                                 max_iter=15)
    newton_res = pg.multi_island_pf(grid_gslv, pf_opt, 1, [0])

    errors = 0
    errors += CheckArr(np.abs(gridcal_res.voltage), np.abs(newton_res.voltage[0, :]), tol, 'V', 'abs')
    errors += CheckArr(gridcal_res.voltage.real, newton_res.voltage.real[0, :], tol, 'V', 'real')
    errors += CheckArr(gridcal_res.voltage.imag, newton_res.voltage.imag[0, :], tol, 'V', 'imag')
    errors += CheckArr(gridcal_res.Sf.real, newton_res.Sf.real[0, :], tol, 'Sf', 'real')
    errors += CheckArr(gridcal_res.Sf.imag, newton_res.Sf.imag[0, :], tol, 'Sf', 'imag')

    return errors


def test_gslv_compatibility():
    """

    :return:
    """

    if not GSLV_AVAILABLE:
        return

    files = [
        'AC-DC with all and DCload.gridcal',
        'RAW/IEEE 14 bus.raw',
        'RAW/IEEE 30 bus.raw',
        'RAW/IEEE 118 Bus v2.raw',
    ]

    for f1 in files:
        fname = os.path.join('data', 'grids', f1)

        print(f"Testing: {fname}")

        grid_gc = vg.open_file(filename=fname)

        # correct zero rates
        for br in grid_gc.get_branches():
            if br.rate <= 0:
                br.rate = 9999.0

        grid_gslv, gslv_dict = to_gslv(circuit=grid_gc,
                                       use_time_series=False,
                                       time_indices=None,
                                       override_branch_controls=False,
                                       opf_results=None)

        errors = compare_inputs(grid_gslv=grid_gslv,
                                grid_gc=grid_gc,
                                tol=1e-6,
                                t_idx=None)

        assert errors == 0


def test_gslv_compatibility_ts():
    """

    :return:
    """

    if not GSLV_AVAILABLE:
        return

    fname = os.path.join('data', 'grids', 'IEEE39_1W.gridcal')

    print(f"Testing: {fname}")

    grid_gc = vg.open_file(filename=fname)

    # correct zero rates
    for br in grid_gc.get_branches():
        if br.rate <= 0:
            br.rate = 9999.0

    grid_gslv, gslv_dict = to_gslv(circuit=grid_gc,
                                   use_time_series=True,
                                   time_indices=None,
                                   override_branch_controls=False,
                                   opf_results=None)

    for t_idx in range(grid_gc.get_time_number()):
        print("Time step:", t_idx)
        errors = compare_inputs(grid_gslv=grid_gslv,
                                grid_gc=grid_gc,
                                tol=1e-6,
                                t_idx=t_idx)

        assert errors == 0


def test_power_flow_ts():
    if not GSLV_AVAILABLE:
        return

    grid = vg.open_file(filename=os.path.join('data', 'grids', 'IEEE39_1W.gridcal'))

    options = vg.PowerFlowOptions(verbose=False)

    drv = vg.PowerFlowTimeSeriesDriver(grid=grid,
                                        options=options,
                                        engine=vg.EngineType.GSLV)

    drv.run()

    res = drv.results


def test_controllable_shunt_conversion_preserves_step_arrays():
    if not GSLV_AVAILABLE:
        return

    grid = vg.MultiCircuit()
    bus = vg.Bus(name="Bus")
    grid.add_bus(obj=bus)

    shunt = vg.ControllableShunt(
        name="Shunt",
        number_of_steps=3,
        step=1,
        g_per_step=0.0,
        b_per_step=0.0,
        vset=1.01,
        control_mode=vg.ShuntControlMode.Discrete,
    )
    shunt.g_steps = np.array([1.0, 2.0, 3.0], dtype=float)
    shunt.b_steps = np.array([4.0, 5.0, 6.0], dtype=float)
    grid.add_controllable_shunt(bus=bus, api_obj=shunt)

    grid_gslv, _ = to_gslv(circuit=grid,
                           use_time_series=False,
                           time_indices=None,
                           override_branch_controls=False,
                           opf_results=None)

    converted = grid_gslv.controllable_shunts[0]
    assert converted.g_steps == [1.0, 2.0, 3.0]
    assert converted.b_steps == [4.0, 5.0, 6.0]
    assert converted.get_bmin() == 4.0
    assert converted.get_bmax() == 6.0
    assert converted.control_mode == pg.ShuntControlMode.Discrete


def test_bus_voltage_guess_profiles_are_exported_to_gslv():
    if not GSLV_AVAILABLE:
        return

    grid = vg.MultiCircuit()
    bus = vg.Bus(name="Bus", Vm0=1.01, Va0=0.02)
    bus.active_prof = np.array([True, True, True], dtype=bool)
    bus.Vm0_prof = np.array([1.01, 1.02, 1.03], dtype=float)
    bus.Va0_prof = np.array([0.02, 0.03, 0.04], dtype=float)
    grid.add_bus(obj=bus)
    grid.time_profile = np.array([0, 1, 2])

    grid_gslv, _ = to_gslv(circuit=grid,
                           use_time_series=True,
                           time_indices=None,
                           override_branch_controls=False,
                           opf_results=None)

    converted = grid_gslv.buses[0]
    assert converted.Vm0.to_list() == [1.01, 1.02, 1.03]
    assert converted.Va0.to_list() == [0.02, 0.03, 0.04]


def test_gslv_conversion_exports_bus_voltage_level() -> None:
    """
    Check that bus voltage-level references are exported to GSLV.

    :return: None.
    """
    if not GSLV_AVAILABLE:
        return
    else:
        pass

    grid: vg.MultiCircuit = vg.MultiCircuit(name="gslv-voltage-level-export")
    substation: vg.Substation = vg.Substation(name="Substation")
    voltage_level: vg.VoltageLevel = vg.VoltageLevel(name="VL", substation=substation, Vnom=110.0)
    bus: vg.Bus = vg.Bus(name="Bus", Vnom=110.0)

    bus.substation = substation
    bus.voltage_level = voltage_level

    grid.add_substation(obj=substation)
    grid.add_voltage_level(obj=voltage_level)
    grid.add_bus(obj=bus)

    grid_gslv, gslv_dict = to_gslv(
        circuit=grid,
        use_time_series=False,
        time_indices=None,
        override_branch_controls=False,
        opf_results=None,
    )

    converted_bus = grid_gslv.buses[0]
    assert converted_bus.voltage_level.get_idtag() == voltage_level.idtag
    assert gslv_dict.voltage_level_dict[voltage_level] in grid_gslv.voltage_levels


def test_gslv_conversion_exports_injection_association_assets_and_facility() -> None:
    """
    Check that injection associations are exported as GSLV assets and device references.

    :return: None.
    """
    if not GSLV_AVAILABLE:
        return
    else:
        pass

    grid: vg.MultiCircuit = vg.MultiCircuit(name="gslv-association-export")
    bus: vg.Bus = vg.Bus(name="Bus")
    facility: vg.Facility = vg.Facility(name="Plant", code="PL")
    weak_technology: vg.Technology = vg.Technology(name="Weak", code="WK")
    strong_technology: vg.Technology = vg.Technology(name="Strong", code="ST")
    fuel: vg.Fuel = vg.Fuel(name="Gas", code="GAS", cost=3.0)
    emission_gas: vg.EmissionGas = vg.EmissionGas(name="CO2", code="CO2", cost=9.0)
    generator: vg.Generator = vg.Generator(name="Generator", P=10.0)

    # The source grid owns the association master objects before injections refer to them.
    grid.add_bus(obj=bus)
    grid.add_facility(obj=facility)
    grid.add_technology(obj=weak_technology)
    grid.add_technology(obj=strong_technology)
    grid.add_fuel(obj=fuel)
    grid.add_emission_gas(obj=emission_gas)

    # The generator carries all association kinds that GSLV supports for generator-like devices.
    generator.facility = facility
    generator.technologies.add_object(api_object=weak_technology, val=0.25)
    generator.technologies.add_object(api_object=strong_technology, val=0.75)
    generator.fuels.add_object(api_object=fuel, val=0.50)
    generator.emissions.add_object(api_object=emission_gas, val=0.20)
    grid.add_generator(bus=bus, api_obj=generator)

    grid_gslv, gslv_dict = to_gslv(
        circuit=grid,
        use_time_series=False,
        time_indices=None,
        override_branch_controls=False,
        opf_results=None,
    )
    converted_generator = grid_gslv.generators[0]

    assert len(grid_gslv.technologies) == 2
    assert len(grid_gslv.fuels) == 1
    assert len(grid_gslv.emission_gases) == 1
    assert converted_generator.facility.get_idtag() == facility.idtag
    assert converted_generator.tpe == "Strong"
    assert gslv_dict.technology_dict[weak_technology] in grid_gslv.technologies
    assert gslv_dict.technology_dict[strong_technology] in grid_gslv.technologies
    assert gslv_dict.fuel_dict[fuel] in grid_gslv.fuels
    assert gslv_dict.emission_gas_dict[emission_gas] in grid_gslv.emission_gases


def test_gslv_conversion_exports_generator_market_unit_and_control_bus() -> None:
    """
    Check that generator market-unit and remote-control bus references are exported.

    :return: None.
    """
    if not GSLV_AVAILABLE:
        return
    else:
        pass

    grid: vg.MultiCircuit = vg.MultiCircuit(name="gslv-generator-market-unit-export")
    bus: vg.Bus = vg.Bus(name="Bus")
    control_bus: vg.Bus = vg.Bus(name="Control bus")
    market_unit: vg.MarketUnit = vg.MarketUnit(name="Market unit", code="MU", color="#123456")
    generator: vg.Generator = vg.Generator(name="Generator", P=10.0, market_unit=market_unit, market_unit_share=0.7)

    generator.control_bus = control_bus

    grid.add_bus(obj=bus)
    grid.add_bus(obj=control_bus)
    grid.add_market_unit(obj=market_unit)
    grid.add_generator(bus=bus, api_obj=generator)

    grid_gslv, gslv_dict = to_gslv(
        circuit=grid,
        use_time_series=False,
        time_indices=None,
        override_branch_controls=False,
        opf_results=None,
    )

    converted_generator = grid_gslv.generators[0]
    assert converted_generator.market_unit.get_idtag() == market_unit.idtag
    assert converted_generator.market_unit_share.to_list() == [0.7]
    assert converted_generator.control_bus.to_list()[0].get_idtag() == control_bus.idtag
    assert gslv_dict.market_unit_dict[market_unit].get_idtag() == market_unit.idtag


def test_gslv_conversion_exports_battery_storage_and_market_unit_fields() -> None:
    """
    Check that battery-specific storage fields and generator-like market data are exported.

    :return: None.
    """
    if not GSLV_AVAILABLE:
        return
    else:
        pass

    grid: vg.MultiCircuit = vg.MultiCircuit(name="gslv-battery-export")
    bus: vg.Bus = vg.Bus(name="Bus")
    control_bus: vg.Bus = vg.Bus(name="Control bus")
    market_unit: vg.MarketUnit = vg.MarketUnit(name="Battery unit")
    battery: vg.Battery = vg.Battery(name="Battery",
                                     soc=0.42,
                                     charge_per_cycle=0.23,
                                     discharge_per_cycle=0.34,
                                     r1=0.01,
                                     x1=0.02)

    battery.control_bus = control_bus
    battery.market_unit = market_unit
    battery.market_unit_share = 0.4
    battery.min_soc_charge = 0.55

    grid.add_bus(obj=bus)
    grid.add_bus(obj=control_bus)
    grid.add_market_unit(obj=market_unit)
    grid.add_battery(bus=bus, api_obj=battery)

    grid_gslv, _ = to_gslv(
        circuit=grid,
        use_time_series=False,
        time_indices=None,
        override_branch_controls=False,
        opf_results=None,
        add_three_phase_data=True,
    )

    converted_battery = grid_gslv.batteries[0]
    assert converted_battery.soc == 0.42
    assert converted_battery.charge_per_cycle == 0.23
    assert converted_battery.discharge_per_cycle == 0.34
    assert converted_battery.min_soc_charge == 0.55
    assert converted_battery.R1 == 0.01
    assert converted_battery.X1 == 0.02
    assert converted_battery.market_unit.get_idtag() == market_unit.idtag
    assert converted_battery.market_unit_share.to_list() == [0.4]
    assert converted_battery.control_bus.to_list()[0].get_idtag() == control_bus.idtag


def test_gslv_association_helpers_copy_exact_values() -> None:
    """
    Check the association copier calls the GSLV association API with the source values.

    :return: None.
    """
    facility: vg.Facility = vg.Facility(name="Plant")
    technology: vg.Technology = vg.Technology(name="Solar")
    fuel: vg.Fuel = vg.Fuel(name="Gas")
    emission_gas: vg.EmissionGas = vg.EmissionGas(name="CO2")
    load: vg.Load = vg.Load(name="Load")
    generator: vg.Generator = vg.Generator(name="Generator")

    gslv_facility: object = object()
    gslv_technology: object = object()
    gslv_fuel: object = object()
    gslv_emission_gas: object = object()

    facility_dict: Dict[vg.Facility, object] = dict()
    facility_dict[facility] = gslv_facility
    technology_dict: Dict[vg.Technology, object] = dict()
    technology_dict[technology] = gslv_technology
    fuel_dict: Dict[vg.Fuel, object] = dict()
    fuel_dict[fuel] = gslv_fuel
    emission_gas_dict: Dict[vg.EmissionGas, object] = dict()
    emission_gas_dict[emission_gas] = gslv_emission_gas

    # Common injection associations must preserve the referenced target and weight.
    load.facility = facility
    load.technologies.add_object(api_object=technology, val=0.30)
    gslv_load: GslvInjectionRecorder = GslvInjectionRecorder()
    set_injection_associations(
        gslv_elm=gslv_load,
        elm=load,
        facility_dict=facility_dict,
        technology_dict=technology_dict,
    )

    # Generator-like devices add fuel and emission associations on top of common injection associations.
    generator.facility = facility
    generator.technologies.add_object(api_object=technology, val=0.70)
    generator.fuels.add_object(api_object=fuel, val=0.40)
    generator.emissions.add_object(api_object=emission_gas, val=0.10)
    gslv_generator: GslvGeneratorRecorder = GslvGeneratorRecorder()
    set_generator_associations(
        gslv_elm=gslv_generator,
        elm=generator,
        facility_dict=facility_dict,
        technology_dict=technology_dict,
        fuel_dict=fuel_dict,
        emission_gas_dict=emission_gas_dict,
    )

    assert gslv_load.facility is gslv_facility
    assert gslv_load.technologies.values[gslv_technology] == 0.30
    assert gslv_generator.facility is gslv_facility
    assert gslv_generator.technologies.values[gslv_technology] == 0.70
    assert gslv_generator.fuels.values[gslv_fuel] == 0.40
    assert gslv_generator.emissions.values[gslv_emission_gas] == 0.10


def test_power_flow_ts_ny_activs():
    if not GSLV_AVAILABLE:
        return

    grid = vg.open_file(filename=os.path.join('data', 'grids', 'NY_activs.gridcal'))
    options = vg.PowerFlowOptions(verbose=False, retry_with_other_methods=False)

    drv = vg.PowerFlowTimeSeriesDriver(
        grid=grid,
        options=options,
        engine=vg.EngineType.GSLV,
    )
    drv.run()

    assert drv.results is not None
    assert drv.results.voltage.shape[0] == grid.get_time_number()


def test_power_flow_snapshot_device_active_power_results():
    """
    Verify that direct GSLV per-device active-power PF channels are mapped when
    the loaded GSLV build exposes them.
    """
    if not GSLV_AVAILABLE:
        return

    grid = vg.open_file(filename=os.path.join('data', 'grids', 'case14.gridcal'))
    options = vg.PowerFlowOptions(verbose=False)

    drv_native = vg.PowerFlowDriver(grid=grid,
                                    options=options,
                                    engine=vg.EngineType.VeraGrid)
    drv_native.run()

    drv_gslv = vg.PowerFlowDriver(grid=grid,
                                  options=options,
                                  engine=vg.EngineType.GSLV)
    drv_gslv.run()

    assert np.allclose(drv_native.results.gen_p, drv_gslv.results.gen_p, atol=1e-4)
    assert np.allclose(drv_native.results.battery_p, drv_gslv.results.battery_p, atol=1e-4)


def test_contingencies_ts():
    if not GSLV_AVAILABLE:
        return

    grid = vg.open_file(filename=os.path.join('data', 'grids', 'IEEE39_1W.gridcal'))

    options = vg.ContingencyAnalysisOptions(
        pf_options=vg.PowerFlowOptions(vg.SolverType.Linear),
        lin_options=vg.LinearAnalysisOptions(),
        use_srap=False,
        srap_max_power=1400.0,
        srap_top_n=5,
        srap_deadband=10,
        srap_rever_to_nominal_rating=False,
        detailed_massive_report=False,
        contingency_deadband=0.0,
        contingency_method=vg.ContingencyMethod.PowerFlow,
        contingency_groups=grid.contingency_groups
    )

    drv = vg.ContingencyAnalysisTimeSeriesDriver(grid=grid,
                                                  options=options,
                                                  engine=vg.EngineType.GSLV)

    drv.run()

    res = drv.results


def test_results_compatibility():
    """
    Test to check the 1:1 results of gslv
    :return:
    """

    if not GSLV_AVAILABLE:
        return

    paths = [
        # "data/grids/Matpower/case57.matpower",
        # "data/grids/Matpower/case3012wp.matpower"
        # "data/grids/Matpower/case16am.matpower"
    ]

    # run this one to compile the stuff
    folder = os.path.join("data", "grids", "Matpower")
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(".m"):
                path = os.path.join(root, file)
                paths.append(path)

    for path in paths:
        fname = os.path.basename(path)

        grid = vg.open_file(filename=path)

        # if grid.get_bus_number() < 2000000000:
        print("^" * 100)
        print("Testing: ", fname)
        gslv_grid, _ = to_gslv(grid, use_time_series=False)

        inpt_err_number = 0
        # inpt_err_number = compare_inputs(grid_gslv=gslv_grid, grid_gc=grid)

        # power flow ---------------------------------------------------------------

        options = vg.PowerFlowOptions(verbose=0,
                                       use_stored_guess=True,
                                       retry_with_other_methods=False,
                                       solver_type=vg.SolverType.NR,
                                       control_q=False,
                                       tolerance=1e-8)

        drv_gc = vg.PowerFlowDriver(grid=grid,
                                     options=options,
                                     engine=vg.EngineType.VeraGrid)
        drv_gc.run()
        res_gc = drv_gc.results

        drv_gslv = vg.PowerFlowDriver(grid=grid,
                                       options=options,
                                       engine=vg.EngineType.GSLV)
        drv_gslv.run()
        res_gslv = drv_gslv.results

        all_ok, logger = res_gc.compare(res_gslv, tol=1e-4)

        if not all_ok or inpt_err_number > 0:
            logger.print(title=path)
            os.makedirs(os.path.join("data", "output"), exist_ok=True)
            vg.save_file(grid=grid, filename=os.path.join("data", "output", fname + ".gridcal"))
            print()
        assert all_ok


def test_gslv_veragrid_agreement():
    """
    This test sparked because on IEEE39_1W Snapshot
    when failing branch 26 (k=26) the branches 31, 32, 33
    (and only those) show different power flows
    :return:
    """

    if not GSLV_AVAILABLE:
        return

    fname = os.path.join('data', 'grids', "IEEE39_1W.gridcal")

    print(f"Testing: {fname}")

    grid_gc = vg.open_file(filename=fname)

    grid_gc.lines[26].active = False

    # correct zero rates
    for br in grid_gc.get_branches():
        if br.rate <= 0:
            br.rate = 9999.0

    grid_gslv, gslv_dict = to_gslv(circuit=grid_gc,
                                   use_time_series=False,
                                   time_indices=None,
                                   override_branch_controls=False,
                                   opf_results=None)

    errors = compare_inputs(grid_gslv=grid_gslv,
                            grid_gc=grid_gc,
                            tol=1e-6,
                            t_idx=None)

    print(errors)



if __name__ == '__main__':
    # test_gslv_compatibility()
    # test_gslv_compatibility_ts()
    # test_power_flow_ts()
    # test_contingencies_ts()
    test_results_compatibility()
