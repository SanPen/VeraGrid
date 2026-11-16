# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Round-trip checks for the supported Sienna static-network subset."""

from pathlib import Path
import json

import pytest

import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.sienna.sienna_to_veragrid import (load_sienna_document, parse_sienna_document,
                                                          sienna_to_veragrid)
from VeraGridEngine.IO.sienna.veragrid_to_sienna import save_veragrid_to_sienna
from VeraGridEngine.IO.sienna.devices.format_version import resolve_sienna_format_version
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaObjectKind
from VeraGridEngine.IO.sienna.devices.schema_registry import get_sienna_object_parser, get_sienna_object_parsers
from VeraGridEngine.IO.sienna.devices.writer_registry import get_sienna_object_writers
from VeraGridEngine.IO.sienna.mapping_inventory import (SiennaMappingStatus, get_non_dynamic_mapping_decisions,
                                                         get_sienna_mapping_inventory)
from VeraGridEngine.IO.sienna.devices.operations.static_injection.standard_load import parse_sienna_standard_load
from VeraGridEngine.IO.sienna.devices.core.common.average_rate_curve import (parse_sienna_average_rate_curve,
                                                                              sienna_average_rate_curve_to_json)
from VeraGridEngine.IO.sienna.devices.core.common.linear_function_data import SiennaLinearFunctionData
from VeraGridEngine.IO.sienna.devices.core.common.value_curve import parse_sienna_value_curve
from VeraGridEngine.IO.sienna.devices.system_document import sienna_system_document_to_json
from VeraGridEngine.IO.sienna.devices.operations.static_injection.renewable_dispatch import SiennaRenewableDispatch
from VeraGridEngine.IO.sienna.devices.operations.static_injection.source import SiennaSource
from VeraGridEngine.IO.sienna.devices.operations.static_injection.switched_admittance import SiennaSwitchedAdmittance
from VeraGridEngine.IO.sienna.devices.core.common.complex_number import SiennaComplexNumber
from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
from VeraGridEngine.IO.sienna.devices.core.common.in_out import SiennaInOut
from VeraGridEngine.IO.sienna.devices.operations.static_injection.energy_reservoir_storage import SiennaEnergyReservoirStorage
from VeraGridEngine.IO.sienna.devices.operations.branch.generic_arc_impedance import SiennaGenericArcImpedance
from VeraGridEngine.IO.sienna.devices.operations.branch.two_winding_transformer import SiennaTwoWindingTransformer
from VeraGridEngine.IO.sienna.devices.operations.branch.transformer_circuit import SiennaTransformerCircuit
from VeraGridEngine.IO.sienna.devices.operations.branch.series_compensator import SiennaSeriesCompensator
from VeraGridEngine.IO.sienna.devices.operations.static_injection.thermal_standard import SiennaThermalStandard
from VeraGridEngine.IO.sienna.devices.operations.static_injection.hydro_turbine import SiennaHydroTurbine
from VeraGridEngine.IO.sienna.devices.operations.static_injection.hydro_dispatch import SiennaHydroDispatch
from VeraGridEngine.IO.sienna.devices.operations.static_injection.interruptible_power_load import SiennaInterruptiblePowerLoad
from VeraGridEngine.IO.sienna.devices.operations.static_injection.interruptible_standard_load import SiennaInterruptibleStandardLoad
from VeraGridEngine.IO.sienna.devices.operations.static_injection.shiftable_power_load import SiennaShiftablePowerLoad
from VeraGridEngine.IO.sienna.devices.operations.static_injection.hydro_pump_turbine import SiennaHydroPumpTurbine
from VeraGridEngine.IO.sienna.devices.operations.static_injection.facts_control_device import SiennaFACTSControlDevice
from VeraGridEngine.IO.sienna.devices.operations.static_injection.hybrid_system import SiennaHybridSystem
from VeraGridEngine.IO.sienna.devices.operations.branch.discrete_controlled_ac_branch import SiennaDiscreteControlledACBranch
from VeraGridEngine.IO.sienna.devices.operations.common.operational_states import SiennaOperationalStates
from VeraGridEngine.IO.sienna.devices.core.common.up_down import SiennaUpDown


def build_sienna_export_grid() -> MultiCircuit:
    """Build the smallest VeraGrid circuit that exercises every supported Sienna component.

    :return: VeraGrid circuit with buses, one line and one static load.
    """
    circuit: MultiCircuit = MultiCircuit(name="sienna-round-trip", Sbase=100.0, fbase=50.0)
    area: dev.Area = dev.Area(name="North", code="10")
    zone: dev.Zone = dev.Zone(name="North-load", code="20", area=area)
    slack_bus: dev.Bus = dev.Bus(name="Slack", code="1", Vnom=220.0, is_slack=True, area=area, zone=zone)
    load_bus: dev.Bus = dev.Bus(name="Demand", code="2", Vnom=220.0, area=area, zone=zone)
    dc_bus: dev.Bus = dev.Bus(name="DC", code="5", Vnom=400.0, is_dc=True, area=area, zone=zone)
    tertiary_bus: dev.Bus = dev.Bus(name="Tertiary", code="14", Vnom=110.0, area=area, zone=zone)
    line: dev.Line = dev.Line(bus_from=slack_bus, bus_to=load_bus, name="L1", code="3",
                              r=0.01, x=0.1, b=0.02, rate=100.0)
    load: dev.Load = dev.Load(name="D1", code="4", P=20.0, Q=5.0, contracted_power=20.0)
    shunt: dev.Shunt = dev.Shunt(name="S1", code="6", G=1.0, B=2.0)
    static_generator: dev.StaticGenerator = dev.StaticGenerator(name="PV", code="7", P=4.0, Q=1.0, Snom=5.0)
    external_grid: dev.ExternalGrid = dev.ExternalGrid(name="Intertie", code="8", Vm=1.03, Va=0.02,
                                                       P=2.0, Q=0.5)
    generator: dev.Generator = dev.Generator(name="Thermal", code="9", P=6.0, Q=1.0, Pmin=1.0,
                                              Pmax=10.0, Qmin=-2.0, Qmax=3.0, Snom=10.0)
    transformer: dev.Transformer2W = dev.Transformer2W(bus_from=slack_bus, bus_to=load_bus, name="T1", code="10",
                                                        HV=220.0, LV=220.0, r=0.01, x=0.08, rate=50.0)
    reactance: dev.SeriesReactance = dev.SeriesReactance(bus_from=slack_bus, bus_to=load_bus, name="XR", code="11",
                                                         r=0.0, x=0.03, rate=40.0)
    battery: dev.Battery = dev.Battery(name="B1", code="12", P=1.0, Pmin=-3.0, Pmax=4.0, Q=0.2,
                                       Qmin=-1.0, Qmax=1.0, Snom=4.0, Enom=10.0, min_soc=0.2, max_soc=0.9,
                                       soc=0.5, Sbase=100.0)
    controllable_shunt: dev.ControllableShunt = dev.ControllableShunt(name="CS", code="13", G=0.2, B=1.2)
    transformer3w: dev.Transformer3W = dev.Transformer3W(
        name="T3", code="15", bus1=slack_bus, bus2=load_bus, bus3=tertiary_bus,
        V1=220.0, V2=220.0, V3=110.0, r12=0.02, r23=0.03, r31=0.04,
        x12=0.10, x23=0.12, x31=0.14, rate12=30.0, rate23=25.0, rate31=20.0)
    circuit.add_area(obj=area)
    circuit.add_zone(obj=zone)
    circuit.add_bus(obj=slack_bus)
    circuit.add_bus(obj=load_bus)
    circuit.add_bus(obj=dc_bus)
    circuit.add_bus(obj=tertiary_bus)
    circuit.add_line(obj=line)
    circuit.add_load(bus=load_bus, api_obj=load)
    circuit.add_shunt(bus=load_bus, api_obj=shunt)
    circuit.add_static_generator(bus=load_bus, api_obj=static_generator)
    circuit.add_external_grid(bus=slack_bus, api_obj=external_grid)
    circuit.add_generator(bus=slack_bus, api_obj=generator)
    circuit.add_transformer2w(obj=transformer)
    circuit.add_series_reactance(obj=reactance)
    circuit.add_battery(bus=load_bus, api_obj=battery)
    circuit.add_controllable_shunt(bus=load_bus, api_obj=controllable_shunt)
    circuit.add_transformer3w(obj=transformer3w)
    return circuit


def test_sienna_static_network_round_trip(tmp_path: Path) -> None:
    """Export and import the supported static Sienna network without external dependencies.

    :param tmp_path: Pytest temporary directory.
    :return: None.
    """
    circuit: MultiCircuit = build_sienna_export_grid()
    export_path: Path = tmp_path / "sienna.json"

    # The adapter currently needs only a pinned schema-root location for provenance.
    save_veragrid_to_sienna(circuit=circuit, file_name=str(export_path), schema_directory=tmp_path)
    document = load_sienna_document(file_name=str(export_path), schema_directory=tmp_path)
    restored_circuit: MultiCircuit = sienna_to_veragrid(document=document)

    assert restored_circuit.name == circuit.name
    assert restored_circuit.Sbase == circuit.Sbase
    assert restored_circuit.fBase == circuit.fBase
    assert any(bus.name == "T3_star" for bus in document.buses)
    assert not any(bus.name == "T3_star" for bus in restored_circuit.get_buses())
    assert restored_circuit.get_bus_number() == 5
    assert len(restored_circuit.get_areas()) == 1
    assert len(restored_circuit.get_zones()) == 1
    assert restored_circuit.get_buses()[0].area.name == "North"
    assert any(bus.is_dc for bus in restored_circuit.get_buses())
    assert restored_circuit.get_lines_number() == 1
    assert restored_circuit.get_loads_number() == 1
    assert restored_circuit.get_shunts_number() == 1
    assert restored_circuit.get_static_generators_number() == 1
    assert restored_circuit.get_external_grids_number() == 1
    assert restored_circuit.get_generators_number() == 1
    assert restored_circuit.get_transformers2w_number() == 1
    assert restored_circuit.get_series_reactances_number() == 1
    assert restored_circuit.get_batteries_number() == 1
    assert restored_circuit.get_controllable_shunts_number() == 1
    assert restored_circuit.get_transformers3w_number() == 1
    assert restored_circuit.get_lines()[0].R == 0.01
    assert restored_circuit.get_loads()[0].P == 20.0
    assert restored_circuit.get_shunts()[0].B == 2.0
    assert restored_circuit.get_static_generators()[0].P == 4.0
    assert restored_circuit.get_external_grids()[0].Vm == 1.03
    assert restored_circuit.get_generators()[0].Pmax == 10.0
    assert restored_circuit.get_transformers2w()[0].X == 0.08
    assert restored_circuit.get_series_reactances()[0].X == 0.03
    assert restored_circuit.get_batteries()[0].Enom == 10.0
    assert restored_circuit.get_controllable_shunts()[0].B == 1.2
    assert restored_circuit.get_transformers3w()[0].x31 == 0.14


def test_sienna_parser_retains_unmapped_components_before_conversion() -> None:
    """Keep an unsupported Sienna component visible instead of silently discarding it.

    :return: None.
    """
    document_data: dict[str, object] = {
        "schema_version": "0.4.0",
        "components": {"AGC": [{"id": 1, "name": "A", "available": True, "bias": 0.0,
                               "K_p": 0.0, "K_i": 0.0, "K_d": 0.0, "delta_t": 1.0}]},
        "supplemental_attributes": list(), "supplemental_attribute_associations": list(),
        "plant_associations": list(), "combined_cycle_associations": list(), "service_associations": list(),
        "time_series_associations": list(), "time_series_storage_file": None,
    }
    document = parse_sienna_document(document_data)

    assert len(document.unmapped_components) == 1
    with pytest.raises(ValueError, match="AGC"):
        sienna_to_veragrid(document)


def test_sienna_to_veragrid_translates_standard_and_exponential_loads(tmp_path: Path) -> None:
    """Translate additional Sienna load representations into VeraGrid loads.

    :param tmp_path: Temporary directory used for the Sienna JSON fixture.
    :return: None.
    """
    export_path: Path = tmp_path / "loads.json"
    save_veragrid_to_sienna(circuit=build_sienna_export_grid(), file_name=str(export_path),
                            schema_directory=tmp_path)
    payload: dict = json.loads(export_path.read_text())
    payload["components"]["StandardLoad"] = [{"id": 31, "name": "zip", "available": True,
                                                 "bus": 2, "base_power": 100.0,
                                                 "power_units": "NATURAL_UNITS",
                                                 "constant_active_power": 5.0,
                                                 "impedance_active_power": 2.0,
                                                 "current_active_power": 1.0,
                                                 "constant_reactive_power": 3.0,
                                                 "impedance_reactive_power": 1.0,
                                                 "current_reactive_power": 1.0}]
    payload["components"]["ExponentialLoad"] = [{"id": 32, "name": "exp", "available": True,
                                                    "bus": 2, "active_power": 4.0,
                                                    "reactive_power": 2.0, "alpha": 1.0, "beta": 1.0,
                                                    "base_power": 100.0,
                                                    "power_units": "NATURAL_UNITS",
                                                    "max_active_power": 4.0,
                                                    "max_reactive_power": 2.0}]
    payload["components"]["RenewableNonDispatch"] = [{"id": 33, "name": "wind", "available": True,
                                                         "bus": 2, "active_power": 6.0,
                                                         "reactive_power": 1.0, "rating": 8.0,
                                                         "prime_mover_type": "WT",
                                                         "power_factor": 0.98, "base_power": 100.0,
                                                         "power_units": "NATURAL_UNITS"}]
    payload["components"]["SynchronousCondenser"] = [{"id": 34, "name": "cond", "available": True,
                                                        "bus": 2, "reactive_power": 1.5, "rating": 10.0,
                                                        "reactive_power_limits": {"min": -4.0, "max": 5.0},
                                                        "base_power": 100.0,
                                                        "power_units": "NATURAL_UNITS",
                                                        "active_power_losses": 0.1}]
    payload["components"]["MotorLoad"] = [{"id": 35, "name": "motor", "available": True,
                                             "bus": 2, "active_power": 1.0, "reactive_power": 0.5,
                                             "base_power": 100.0, "power_units": "NATURAL_UNITS",
                                             "rating": 1.2, "max_active_power": 1.2}]
    export_path.write_text(json.dumps(payload))

    document = load_sienna_document(file_name=str(export_path), schema_directory=tmp_path)
    # This test replaces TransformerCircuit with an independent two-winding fixture.
    document.unmapped_components.pop(SiennaObjectKind.ThreeWindingTransformer, None)
    document.unmapped_components[SiennaObjectKind.RenewableDispatch] = [SiennaRenewableDispatch(
        id=36, name="solar", available=True, bus=2, active_power=3.0, reactive_power=0.5,
        rating=5.0, prime_mover_type="PVe", reactive_power_limits=None, power_factor=1.0,
        operation_cost=None, base_power=100.0, power_units="NATURAL_UNITS", dynamic_injector=None)]
    document.unmapped_components[SiennaObjectKind.Source] = [SiennaSource(
        id=37, name="grid", available=True, bus=2, active_power=2.0, reactive_power=0.2,
        active_power_limits=None, reactive_power_limits=None, parameter_units=None, R_th=None, X_th=None,
        internal_voltage=1.02, internal_angle=0.1, base_voltage=None, base_power=100.0,
        power_units="NATURAL_UNITS", operation_cost=None, dynamic_injector=None)]
    document.unmapped_components[SiennaObjectKind.SwitchedAdmittance] = [SiennaSwitchedAdmittance(
        id=38, name="switched", available=True, bus=2, admittance_units="COMPONENT_MVAR",
        number_engaged=[2], number_of_steps=[3], Y_increase=[SiennaComplexNumber(real=0.5, imag=1.5)],
        solved_admittance=None, voltage_limits=None, reactive_power_range_limits=None,
        control_mode=None, regulated_bus_number=None, dynamic_injector=None)]
    document.unmapped_components[SiennaObjectKind.EnergyReservoirStorage] = [SiennaEnergyReservoirStorage(
        id=39, name="battery", available=True, bus=2, prime_mover_type="BA", storage_technology_type="LIB",
        storage_capacity=20.0, energy_units="MWH", storage_level_limits=SiennaMinMax(minimum=2.0, maximum=18.0),
        initial_storage_capacity_level=10.0, rating=5.0, active_power=1.0,
        input_active_power_limits=SiennaMinMax(minimum=0.0, maximum=4.0),
        output_active_power_limits=SiennaMinMax(minimum=0.0, maximum=5.0), efficiency=SiennaInOut(in_=0.9, out=0.95),
        reactive_power=0.0, reactive_power_limits=SiennaMinMax(minimum=-2.0, maximum=2.0), base_power=100.0,
        power_units="NATURAL_UNITS", operation_cost=None, conversion_factor=1.0, storage_target=None,
        cycle_limits=None, ramp_limits=None, self_discharge=0.0, standing_loss=0.0, dynamic_injector=None)]
    document.unmapped_components[SiennaObjectKind.GenericArcImpedance] = [SiennaGenericArcImpedance(
        id=40, name="generic-line", available=True, active_power_flow=0.0, reactive_power_flow=0.0,
        operational_flow_limit=None, arc=1, base_power=100.0, power_units="NATURAL_UNITS",
        parameter_units="COMPONENT_BASE", r=0.02, x=0.03)]
    document.unmapped_components[SiennaObjectKind.TransformerCircuit] = [SiennaTransformerCircuit(
        id=41, available=True, arc=1, tap=1.0, alpha=0.0, parameter_units="COMPONENT_BASE", r=0.01,
        x=0.05, control_objective="UNDEFINED", regulated_bus_number=0, tap_ratio_limits=None,
        phase_angle_limits=None, controlled_voltage_limits=None, controlled_reactive_power_flow_limits=None,
        controlled_active_power_flow_limits=None, number_of_tap_positions=1, rating=50.0, rating_b=None,
        rating_c=None, operational_flow_limit=None, active_power_flow=0.0, reactive_power_flow=0.0,
        base_power=100.0, power_units="NATURAL_UNITS", base_voltage_primary=220.0,
        base_voltage_secondary=220.0)]
    document.unmapped_components[SiennaObjectKind.TwoWindingTransformer] = [SiennaTwoWindingTransformer(
        id=42, name="transformer", circuit=41, admittance_units=None, magnetizing_shunt=None,
        shunt_location=None)]
    document.unmapped_components[SiennaObjectKind.SeriesCompensator] = [SiennaSeriesCompensator(
        id=43, name="series", available=True, active_power_flow=0.0, reactive_power_flow=0.0, arc=1,
        r=0.0, x=-0.01, rating=80.0, control_mode=None, reactance_limits=None,
        active_power_flow_setpoint=None, rating_b=None, rating_c=None, operational_flow_limit=None,
        base_power=100.0, power_units="NATURAL_UNITS", parameter_units="COMPONENT_BASE")]
    document.unmapped_components[SiennaObjectKind.ThermalStandard] = [SiennaThermalStandard(
        id=44, name="thermal", available=True, status=SiennaOperationalStates.ONLINE,
        commitment_mode=None, bus=2, active_power=12.0, reactive_power=1.0, rating=20.0,
        active_power_limits=SiennaMinMax(minimum=5.0, maximum=20.0),
        reactive_power_limits=SiennaMinMax(minimum=-4.0, maximum=5.0),
        ramp_limits=SiennaUpDown(down=2.0, up=3.0), operation_cost=None, base_power=100.0,
        power_units="NATURAL_UNITS", time_limits=SiennaUpDown(down=1.0, up=2.0),
        prime_mover_type=None, fuel=None, time_at_status=None, dynamic_injector=None,
        switching_times=None)]
    document.unmapped_components[SiennaObjectKind.HydroTurbine] = [SiennaHydroTurbine(
        id=45, name="hydro", available=True, bus=2, active_power=8.0, reactive_power=0.5, rating=15.0,
        active_power_limits=SiennaMinMax(minimum=2.0, maximum=15.0),
        reactive_power_limits=SiennaMinMax(minimum=-3.0, maximum=4.0), base_power=100.0,
        power_units="NATURAL_UNITS", status=SiennaOperationalStates.ONLINE, time_at_status=4.0,
        commitment_mode=None, operation_cost=None, powerhouse_elevation=0.0,
        ramp_limits=SiennaUpDown(down=1.0, up=2.0), time_limits=SiennaUpDown(down=3.0, up=4.0),
        outflow_limits=SiennaMinMax(minimum=0.0, maximum=10.0), efficiency=0.9, turbine_type="KAPLAN",
        conversion_factor=1.0, prime_mover_type=None, travel_time=None, dynamic_injector=None)]
    document.unmapped_components[SiennaObjectKind.HydroDispatch] = [SiennaHydroDispatch(
        id=46, name="hydro-dispatch", available=True, bus=2, active_power=7.0, reactive_power=0.4,
        rating=12.0, prime_mover_type=None, active_power_limits=SiennaMinMax(minimum=1.0, maximum=12.0),
        reactive_power_limits=SiennaMinMax(minimum=-2.0, maximum=3.0),
        ramp_limits=SiennaUpDown(down=2.0, up=3.0), time_limits=SiennaUpDown(down=4.0, up=5.0),
        base_power=100.0, power_units="NATURAL_UNITS", status=SiennaOperationalStates.ONLINE,
        time_at_status=0.0, operation_cost=None, dynamic_injector=None)]
    document.unmapped_components[SiennaObjectKind.InterruptiblePowerLoad] = [SiennaInterruptiblePowerLoad(
        id=47, name="interruptible", available=True, bus=2, active_power=2.0, reactive_power=1.0,
        max_active_power=4.0, max_reactive_power=2.0, base_power=100.0, power_units="NATURAL_UNITS",
        operation_cost=None, conformity=None, dynamic_injector=None)]
    document.unmapped_components[SiennaObjectKind.InterruptibleStandardLoad] = [SiennaInterruptibleStandardLoad(
        id=48, name="interruptible-zip", available=True, bus=2, base_power=100.0,
        power_units="NATURAL_UNITS", operation_cost=None, conformity=None, constant_active_power=1.0,
        constant_reactive_power=2.0, impedance_active_power=2.0, impedance_reactive_power=1.0,
        current_active_power=3.0, current_reactive_power=1.0, max_constant_active_power=1.0,
        max_constant_reactive_power=2.0, max_impedance_active_power=2.0, max_impedance_reactive_power=1.0,
        max_current_active_power=3.0, max_current_reactive_power=1.0, dynamic_injector=None)]
    document.unmapped_components[SiennaObjectKind.ShiftablePowerLoad] = [SiennaShiftablePowerLoad(
        id=49, name="shiftable", available=True, bus=2, active_power=3.0,
        active_power_limits=SiennaMinMax(minimum=1.0, maximum=5.0), reactive_power=1.5,
        max_active_power=5.0, max_reactive_power=2.0, base_power=100.0, power_units="NATURAL_UNITS",
        load_balance_time_horizon=4, operation_cost=None, dynamic_injector=None)]
    document.unmapped_components[SiennaObjectKind.HydroPumpTurbine] = [SiennaHydroPumpTurbine(
        id=50, name="pump-turbine", available=True, bus=2, active_power=9.0, reactive_power=0.6, rating=16.0,
        active_power_limits=SiennaMinMax(minimum=3.0, maximum=16.0), reactive_power_limits=None,
        active_power_limits_pump=SiennaMinMax(minimum=-8.0, maximum=-2.0), outflow_limits=None,
        powerhouse_elevation=0.0, ramp_limits=None, time_limits=None, base_power=100.0,
        power_units="NATURAL_UNITS", operating_mode="GEN", status=SiennaOperationalStates.ONLINE,
        time_at_status=0.0, operation_cost=None, active_power_pump=0.0, efficiency=None,
        transition_time=None, minimum_time=None, travel_time=None, conversion_factor=1.0,
        commitment_mode=None, prime_mover_type=None, dynamic_injector=None)]
    document.unmapped_components[SiennaObjectKind.FACTSControlDevice] = [SiennaFACTSControlDevice(
        name="facts", id=51, available=True, bus=2, control_mode=None, voltage_setpoint_units=None,
        voltage_setpoint=1.0, max_shunt_current=5.0, reactive_power_required=2.5, max_reactive_power=None,
        shunt_control_type=None, regulated_bus_number=None, base_power=100.0, power_units="NATURAL_UNITS",
        dynamic_injector=None)]
    document.unmapped_components[SiennaObjectKind.DiscreteControlledACBranch] = [SiennaDiscreteControlledACBranch(
        id=52, name="discrete-line", available=True, active_power_flow=0.0, reactive_power_flow=0.0, arc=1,
        base_power=100.0, power_units="NATURAL_UNITS", r=0.03, x=0.04, rating=70.0, rating_b=None,
        rating_c=None, operational_flow_limit=None, discrete_branch_type=None, branch_status=None,
        normal_branch_status=None)]
    document.unmapped_components[SiennaObjectKind.HybridSystem] = [SiennaHybridSystem(
        id=53, name="hybrid", available=True, status=SiennaOperationalStates.ONLINE, bus=2,
        active_power=5.0, reactive_power=0.3, base_power=100.0, power_units="NATURAL_UNITS",
        operation_cost=None, thermal_unit=None, electric_load=None, storage=None, renewable_unit=None,
        interconnection_impedance=None, interconnection_rating=9.0,
        input_active_power_limits=SiennaMinMax(minimum=0.0, maximum=4.0),
        output_active_power_limits=SiennaMinMax(minimum=0.0, maximum=9.0),
        reactive_power_limits=SiennaMinMax(minimum=-2.0, maximum=2.0), interconnection_efficiency=None,
        dynamic_injector=None)]
    circuit = sienna_to_veragrid(document=document)

    assert circuit.get_loads_number() == 7
    assert circuit.get_loads()[1].P == 8.0
    assert circuit.get_loads()[1].Q == 5.0
    assert circuit.get_loads()[2].P == 4.0
    assert circuit.get_loads()[3].P == 1.0
    assert circuit.get_loads()[4].P == 2.0
    assert circuit.get_loads()[5].P == 6.0
    assert circuit.get_loads()[6].Q == 1.5
    assert circuit.get_static_generators_number() == 1
    assert circuit.get_static_generators()[0].P == 6.0
    assert circuit.get_generators_number() == 7
    assert circuit.get_generators()[0].Qmax == 5.0
    assert circuit.get_generators()[1].Pmax == 5.0
    assert circuit.get_generators()[2].ramp_up == 3.0
    assert circuit.get_generators()[3].Pmax == 15.0
    assert circuit.get_generators()[3].min_time_up == 4.0
    assert circuit.get_generators()[4].Pmin == 1.0
    assert circuit.get_generators()[4].Qmax == 3.0
    assert circuit.get_generators()[5].Pmax == 16.0
    assert circuit.get_generators()[6].Pmin == -4.0
    assert circuit.get_external_grids_number() == 1
    assert circuit.get_external_grids()[0].Vm == 1.02
    assert circuit.get_shunts_number() == 1
    assert circuit.get_controllable_shunts_number() == 2
    assert circuit.get_controllable_shunts()[0].B == 3.0
    assert circuit.get_controllable_shunts()[1].B == 2.5
    assert circuit.get_batteries_number() == 1
    assert circuit.get_batteries()[0].Enom == 20.0
    assert circuit.get_lines_number() == 3
    assert circuit.get_lines()[1].R == 0.02
    assert circuit.get_lines()[2].X == 0.04
    assert circuit.get_series_reactances_number() == 1
    assert circuit.get_series_reactances()[0].X == -0.01
    assert circuit.get_transformers2w_number() == 1

    # Every reader-only kind above collapses to a canonical static VeraGrid device.
    canonical_path: Path = tmp_path / "canonical-round-trip.json"
    save_veragrid_to_sienna(circuit=circuit, file_name=str(canonical_path), schema_directory=tmp_path)
    canonical_document = load_sienna_document(file_name=str(canonical_path), schema_directory=tmp_path)
    canonical_circuit: MultiCircuit = sienna_to_veragrid(document=canonical_document)

    assert canonical_circuit.get_loads_number() == circuit.get_loads_number()
    assert canonical_circuit.get_generators_number() == circuit.get_generators_number()
    assert canonical_circuit.get_controllable_shunts_number() == circuit.get_controllable_shunts_number()
    assert canonical_circuit.get_lines_number() == circuit.get_lines_number()


def test_sienna_format_profiles_reject_unknown_versions() -> None:
    """Keep new schema versions isolated until they receive an explicit profile.

    :return: None.
    """
    profile = resolve_sienna_format_version("0.4.0")

    assert profile.schema_checkout_tag == "v0.4.0"
    with pytest.raises(ValueError, match="Unsupported Sienna schema_version"):
        resolve_sienna_format_version("0.5.0")


def test_every_pinned_sienna_object_has_a_registered_parser() -> None:
    """Expose every published v0.4 schema type through the object registry.

    :return: None.
    """
    parsers = get_sienna_object_parsers()
    writers = get_sienna_object_writers()
    agc_parser = get_sienna_object_parser(SiennaObjectKind.AGC)
    agc = agc_parser({"id": 1, "name": "area-control", "available": True, "bias": 0.0,
                      "K_p": 0.0, "K_i": 0.0, "K_d": 0.0, "delta_t": 1.0})

    assert len(SiennaObjectKind) == 280
    assert len(parsers) == 280
    assert len(writers) == 280
    assert len(writers) == len(SiennaObjectKind)
    assert agc.name == "area-control"
    assert "data" not in agc.__slots__


def test_static_mapping_inventory_covers_every_registered_non_dynamic_kind() -> None:
    """Keep static conversion decisions explicit while dynamics are deferred.

    :return: None.
    """
    all_decisions = get_sienna_mapping_inventory()
    static_decisions = get_non_dynamic_mapping_decisions()
    converted_decisions = [decision for decision in static_decisions
                           if decision.status is SiennaMappingStatus.CONVERTED]

    assert len(all_decisions) == len(SiennaObjectKind) == 280
    assert len(static_decisions) == 193
    assert len(converted_decisions) == 32
    assert all(decision.source_module != "" and decision.reason != "" for decision in static_decisions)


def test_standard_load_has_fixed_slots_for_declared_zip_fields() -> None:
    """Parse ZIP demand fields without retaining a dynamic JSON dictionary.

    :return: None.
    """
    standard_load = parse_sienna_standard_load({"id": 1, "name": "zip", "available": True, "bus": 2,
                                                "base_power": 100.0, "power_units": "NATURAL_UNITS",
                                                "constant_active_power": 10.0,
                                                "impedance_reactive_power": 2.5})

    assert standard_load.constant_active_power == 10.0
    assert standard_load.impedance_reactive_power == 2.5
    assert "data" not in standard_load.__slots__


def test_average_rate_curve_constructs_and_writes_a_typed_nested_model() -> None:
    """Replace nested JSON with the declared fixed-slot function-data object.

    :return: None.
    """
    curve = parse_sienna_average_rate_curve({"curve_type": "AVERAGE_RATE", "function_data": {
        "function_type": "LINEAR", "constant_term": 1.0, "proportional_term": 2.0}})

    assert isinstance(curve.function_data, SiennaLinearFunctionData)
    assert sienna_average_rate_curve_to_json(curve)["function_data"]["proportional_term"] == 2.0
    json.dumps(sienna_average_rate_curve_to_json(curve))


def test_value_curve_constructs_a_declared_union_member() -> None:
    """Parse a oneOf curve into its concrete fixed-slot member.

    :return: None.
    """
    value_curve = parse_sienna_value_curve({"value": {"curve_type": "AVERAGE_RATE", "function_data": {
        "function_type": "LINEAR", "constant_term": 1.0, "proportional_term": 2.0}}})

    assert value_curve.value.__class__.__name__ == "SiennaAverageRateCurve"


def test_system_document_writer_preserves_declared_empty_collections() -> None:
    """Write a fully typed minimal SystemDocument without a dynamic payload bag.

    :return: None.
    """
    document = parse_sienna_document({"schema_version": "0.4.0", "components": dict(),
                                     "supplemental_attributes": list(),
                                     "supplemental_attribute_associations": list(),
                                     "plant_associations": list(), "combined_cycle_associations": list(),
                                     "service_associations": list(), "time_series_associations": list(),
                                     "time_series_storage_file": None})
    encoded = sienna_system_document_to_json(document)

    assert all(len(items) == 0 for items in encoded["components"].values())
    assert encoded["supplemental_attributes"] == list()
    assert encoded["time_series_storage_file"] is None
