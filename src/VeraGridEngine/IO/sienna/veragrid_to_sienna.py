# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Convert the supported VeraGrid static-network subset into Sienna v0.4 JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.Branches.winding import Winding
from VeraGridEngine.IO.sienna.devices.enums import SiennaImpedanceUnitBasis, SiennaSchemaVersion, SiennaUnitSystem
from VeraGridEngine.IO.sienna.sienna_json_validator import SiennaJsonValidator


def save_veragrid_to_sienna(circuit: MultiCircuit, file_name: str, schema_directory: Path) -> None:
    """Convert, validate and write one Sienna SystemDocument JSON file.

    :param circuit: VeraGrid circuit to export.
    :param file_name: Destination JSON file name.
    :param schema_directory: Root directory of the pinned SiennaSchemas checkout.
    :return: None.
    :raises ValueError: When the circuit uses unsupported elements or lacks integer codes.
    """
    document: dict[str, Any] = veragrid_to_sienna_document(circuit)
    validator: SiennaJsonValidator = SiennaJsonValidator(schema_directory=schema_directory)
    validator.validate(document)
    with Path(file_name).open("w", encoding="utf-8") as document_file:
        json.dump(document, document_file, indent=2, sort_keys=True)
        document_file.write("\n")


def veragrid_to_sienna_document(circuit: MultiCircuit) -> dict[str, Any]:
    """Build a Sienna v0.4 SystemDocument from supported VeraGrid devices.

    :param circuit: VeraGrid circuit to export.
    :return: Sienna SystemDocument JSON data.
    :raises ValueError: When the circuit has devices this first adapter cannot preserve.
    """
    _validate_supported_veragrid_devices(circuit)
    components: dict[str, list[dict[str, Any]]] = {"ACBus": list(), "Arc": list(), "Line": list(),
                                                   "PowerLoad": list(), "Area": list(), "LoadZone": list(),
                                                   "DCBus": list(), "FixedAdmittance": list(),
                                                   "RenewableNonDispatch": list(), "Source": list(),
                                                   "ThermalStandard": list(), "EnergyReservoirStorage": list(),
                                                   "SwitchedAdmittance": list(), "TransformerCircuit": list(),
                                                   "TwoWindingTransformer": list(), "SeriesCompensator": list()}
    components["ThreeWindingTransformer"] = list()
    area_ids: dict[object, int] = dict()
    for area in circuit.get_areas():
        area_identifier: int = _get_sienna_identifier(area.code, "Area", area.name)
        area_ids[area] = area_identifier
        components["Area"].append({"id": area_identifier, "name": area.name, "base_power": circuit.Sbase,
                                   "power_units": SiennaUnitSystem.NATURAL_UNITS.value})
    load_zone_ids: dict[object, int] = dict()
    for load_zone in circuit.get_zones():
        load_zone_identifier: int = _get_sienna_identifier(load_zone.code, "LoadZone", load_zone.name)
        load_zone_ids[load_zone] = load_zone_identifier
        components["LoadZone"].append({"id": load_zone_identifier, "name": load_zone.name,
                                        "peak_active_power": 0.0, "peak_reactive_power": 0.0,
                                        "base_power": circuit.Sbase,
                                        "power_units": SiennaUnitSystem.NATURAL_UNITS.value})
    bus_ids: dict[object, int] = dict()
    for bus in circuit.get_buses():
        if bus.internal:
            # VeraGrid creates this bus for a three-winding transformer; Sienna writes its own star bus below.
            pass
        else:
            bus_identifier: int = _get_sienna_identifier(bus.code, "Bus", bus.name)
            bus_ids[bus] = bus_identifier
            area_identifier: int | None = area_ids.get(bus.area, None)
            load_zone_identifier: int | None = load_zone_ids.get(bus.zone, None)
            if bus.is_dc:
                dc_bus_data: dict[str, Any] = {"id": bus_identifier, "name": bus.name, "available": bus.active,
                                                "number": bus_identifier, "base_voltage": bus.Vnom,
                                                "magnitude": bus.Vm0,
                                                "voltage_limits": {"min": bus.Vmin, "max": bus.Vmax}}
                if area_identifier is not None:
                    dc_bus_data["area"] = area_identifier
                else:
                    pass
                if load_zone_identifier is not None:
                    dc_bus_data["load_zone"] = load_zone_identifier
                else:
                    pass
                components["DCBus"].append(dc_bus_data)
            else:
                ac_bus_data: dict[str, Any] = {"id": bus_identifier, "name": bus.name, "available": bus.active,
                                                "number": bus_identifier, "base_voltage": bus.Vnom,
                                                "magnitude": bus.Vm0, "angle": bus.Va0,
                                                "voltage_limits": {"min": bus.Vmin, "max": bus.Vmax},
                                                "bustype": "SLACK" if bus.is_slack else "PQ"}
                if area_identifier is not None:
                    ac_bus_data["area"] = area_identifier
                else:
                    pass
                if load_zone_identifier is not None:
                    ac_bus_data["load_zone"] = load_zone_identifier
                else:
                    pass
                components["ACBus"].append(ac_bus_data)
    arc_identifier: int = 1
    for line in circuit.get_lines():
        line_identifier: int = _get_sienna_identifier(line.code, "Line", line.name)
        from_identifier: int | None = bus_ids.get(line.bus_from, None)
        to_identifier: int | None = bus_ids.get(line.bus_to, None)
        if from_identifier is None or to_identifier is None:
            raise ValueError(f"Line '{line.name}' has a bus that is not in the circuit")
        else:
            pass
        components["Arc"].append({"id": arc_identifier, "from_id": from_identifier, "to_id": to_identifier})
        components["Line"].append({"id": line_identifier, "name": line.name, "available": line.active,
                                   # Sienna requires an initial flow, while an unsolved VeraGrid branch has none.
                                   "active_power_flow": 0.0, "reactive_power_flow": 0.0,
                                   "arc": arc_identifier, "r": line.R, "x": line.X,
                                   "base_power": circuit.Sbase, "power_units": SiennaUnitSystem.NATURAL_UNITS.value,
                                   "parameter_units": SiennaImpedanceUnitBasis.COMPONENT_BASE.value,
                                   "b": {"from": line.B / 2.0, "to": line.B / 2.0},
                                   "g": {"from": line.G / 2.0, "to": line.G / 2.0}, "rating": line.rate,
                                   "angle_limits": {"min": -6.283185307179586, "max": 6.283185307179586}})
        arc_identifier += 1
    for load in circuit.get_loads():
        load_identifier: int = _get_sienna_identifier(load.code, "Load", load.name)
        bus_identifier_value: int | None = bus_ids.get(load.bus, None)
        if bus_identifier_value is None:
            raise ValueError(f"Load '{load.name}' has a bus that is not in the circuit")
        else:
            components["PowerLoad"].append({"id": load_identifier, "name": load.name,
                                              "available": load.active, "bus": bus_identifier_value,
                                              "active_power": load.P, "reactive_power": load.Q,
                                              "base_power": circuit.Sbase,
                                              "power_units": SiennaUnitSystem.NATURAL_UNITS.value,
                                              "max_active_power": load.P,
                                              "max_reactive_power": load.Q})
    for shunt in circuit.get_shunts():
        shunt_identifier: int = _get_sienna_identifier(shunt.code, "Shunt", shunt.name)
        bus_identifier_value: int | None = bus_ids.get(shunt.bus, None)
        if bus_identifier_value is None:
            raise ValueError(f"Shunt '{shunt.name}' has a bus that is not in the circuit")
        else:
            components["FixedAdmittance"].append({"id": shunt_identifier, "name": shunt.name,
                                                   "available": shunt.active, "bus": bus_identifier_value,
                                                   "Y": {"real": shunt.G, "imag": shunt.B},
                                                   "admittance_units": "COMPONENT_MVAR",
                                                   "base_power": circuit.Sbase})
    for generator in circuit.get_static_generators():
        generator_identifier: int = _get_sienna_identifier(generator.code, "StaticGenerator", generator.name)
        bus_identifier_value: int | None = bus_ids.get(generator.bus, None)
        if bus_identifier_value is None:
            raise ValueError(f"StaticGenerator '{generator.name}' has a bus that is not in the circuit")
        else:
            rating: float = generator.Snom if generator.Snom > 0.0 else max(abs(generator.P), abs(generator.Q))
            components["RenewableNonDispatch"].append({
                "id": generator_identifier, "name": generator.name, "available": generator.active,
                "bus": bus_identifier_value, "active_power": generator.P, "reactive_power": generator.Q,
                "rating": rating, "prime_mover_type": "PVe", "power_factor": 1.0,
                "base_power": circuit.Sbase, "power_units": SiennaUnitSystem.NATURAL_UNITS.value})
    for external_grid in circuit.get_external_grids():
        source_identifier: int = _get_sienna_identifier(external_grid.code, "ExternalGrid", external_grid.name)
        bus_identifier_value: int | None = bus_ids.get(external_grid.bus, None)
        if bus_identifier_value is None:
            raise ValueError(f"ExternalGrid '{external_grid.name}' has a bus that is not in the circuit")
        else:
            components["Source"].append({
                "id": source_identifier, "name": external_grid.name, "available": external_grid.active,
                "bus": bus_identifier_value, "active_power": external_grid.P, "reactive_power": external_grid.Q,
                "active_power_limits": {"min": external_grid.P, "max": external_grid.P},
                "reactive_power_limits": {"min": external_grid.Q, "max": external_grid.Q},
                "parameter_units": SiennaImpedanceUnitBasis.COMPONENT_BASE.value, "R_th": 0.0, "X_th": 0.0,
                "internal_voltage": external_grid.Vm, "internal_angle": external_grid.Va,
                "base_power": circuit.Sbase, "power_units": SiennaUnitSystem.NATURAL_UNITS.value,
                "operation_cost": _zero_import_export_cost()})
    for generator in circuit.get_generators():
        generator_identifier: int = _get_sienna_identifier(generator.code, "Generator", generator.name)
        bus_identifier_value: int | None = bus_ids.get(generator.bus, None)
        if bus_identifier_value is None:
            raise ValueError(f"Generator '{generator.name}' has a bus that is not in the circuit")
        else:
            components["ThermalStandard"].append({
                "id": generator_identifier, "name": generator.name, "available": generator.active,
                "status": "ONLINE" if generator.active else "OFFLINE", "bus": bus_identifier_value,
                "active_power": generator.P, "reactive_power": generator.Q, "rating": generator.Snom,
                "active_power_limits": {"min": generator.Pmin, "max": generator.Pmax},
                "reactive_power_limits": {"min": generator.Qmin, "max": generator.Qmax},
                "ramp_limits": {"down": generator.ramp_down, "up": generator.ramp_up},
                "operation_cost": _zero_thermal_generation_cost(), "base_power": generator.Sbase,
                "power_units": SiennaUnitSystem.NATURAL_UNITS.value, "time_limits": {
                    "down": generator.min_time_down, "up": generator.min_time_up},
                "prime_mover_type": "OT", "fuel": "OTHER", "time_at_status": 0.0})
    for battery in circuit.get_batteries():
        battery_identifier: int = _get_sienna_identifier(battery.code, "Battery", battery.name)
        bus_identifier_value: int | None = bus_ids.get(battery.bus, None)
        if bus_identifier_value is None:
            raise ValueError(f"Battery '{battery.name}' has a bus that is not in the circuit")
        else:
            components["EnergyReservoirStorage"].append({
                "id": battery_identifier, "name": battery.name, "available": battery.active,
                "bus": bus_identifier_value, "prime_mover_type": "BA", "storage_technology_type": "LIB",
                "storage_capacity": battery.Enom, "energy_units": "MWH",
                "storage_level_limits": {"min": battery.min_soc * battery.Enom,
                                           "max": battery.max_soc * battery.Enom},
                "initial_storage_capacity_level": battery.soc_0 * battery.Enom, "rating": battery.Snom,
                "active_power": battery.P, "input_active_power_limits": {"min": 0.0, "max": -battery.Pmin},
                "output_active_power_limits": {"min": 0.0, "max": battery.Pmax},
                "efficiency": {"in": battery.charge_efficiency, "out": battery.discharge_efficiency},
                "reactive_power": battery.Q, "reactive_power_limits": {"min": battery.Qmin, "max": battery.Qmax},
                "base_power": circuit.Sbase, "power_units": SiennaUnitSystem.NATURAL_UNITS.value,
                "operation_cost": {"cost_type": "STORAGE", "fixed": 0.0,
                                   "start_up": {"charge": 0.0, "discharge": 0.0}, "shut_down": 0.0}})
    for shunt in circuit.get_controllable_shunts():
        shunt_identifier: int = _get_sienna_identifier(shunt.code, "ControllableShunt", shunt.name)
        bus_identifier_value: int | None = bus_ids.get(shunt.bus, None)
        if bus_identifier_value is None:
            raise ValueError(f"ControllableShunt '{shunt.name}' has a bus that is not in the circuit")
        else:
            components["SwitchedAdmittance"].append({
                "id": shunt_identifier, "name": shunt.name, "available": shunt.active,
                "bus": bus_identifier_value, "admittance_units": "COMPONENT_MVAR",
                "number_engaged": [1], "number_of_steps": [1],
                "Y_increase": [{"real": shunt.G, "imag": shunt.B}], "control_mode": "FIXED"})
    for transformer in circuit.get_transformers2w():
        transformer_identifier: int = _get_sienna_identifier(transformer.code, "Transformer2W", transformer.name)
        from_identifier: int | None = bus_ids.get(transformer.bus_from, None)
        to_identifier: int | None = bus_ids.get(transformer.bus_to, None)
        if from_identifier is None or to_identifier is None:
            raise ValueError(f"Transformer2W '{transformer.name}' has a bus that is not in the circuit")
        else:
            circuit_identifier: int = transformer_identifier
            components["Arc"].append({"id": arc_identifier, "from_id": from_identifier, "to_id": to_identifier})
            components["TransformerCircuit"].append({
                "id": circuit_identifier, "available": transformer.active, "arc": arc_identifier,
                "tap": transformer.tap_module, "alpha": transformer.tap_phase,
                "parameter_units": SiennaImpedanceUnitBasis.COMPONENT_BASE.value, "r": transformer.R,
                "x": transformer.X, "control_objective": "UNDEFINED", "regulated_bus_number": 0,
                "number_of_tap_positions": 1, "rating": transformer.rate,
                "active_power_flow": 0.0, "reactive_power_flow": 0.0, "base_power": circuit.Sbase,
                "power_units": SiennaUnitSystem.NATURAL_UNITS.value,
                "base_voltage_primary": transformer.HV, "base_voltage_secondary": transformer.LV})
            components["TwoWindingTransformer"].append({
                "id": transformer_identifier, "name": transformer.name, "circuit": circuit_identifier,
                "admittance_units": "COMPONENT_BASE", "magnetizing_shunt": {
                    "real": transformer.G, "imag": transformer.B}, "shunt_location": "PRIMARY"})
            arc_identifier += 1
    for reactance in circuit.get_series_reactances():
        reactance_identifier: int = _get_sienna_identifier(reactance.code, "SeriesReactance", reactance.name)
        from_identifier: int | None = bus_ids.get(reactance.bus_from, None)
        to_identifier: int | None = bus_ids.get(reactance.bus_to, None)
        if from_identifier is None or to_identifier is None:
            raise ValueError(f"SeriesReactance '{reactance.name}' has a bus that is not in the circuit")
        else:
            components["Arc"].append({"id": arc_identifier, "from_id": from_identifier, "to_id": to_identifier})
            components["SeriesCompensator"].append({
                "id": reactance_identifier, "name": reactance.name, "available": reactance.active,
                "active_power_flow": 0.0, "reactive_power_flow": 0.0, "arc": arc_identifier,
                "r": reactance.R, "x": reactance.X, "rating": reactance.rate, "control_mode": "FIXED",
                "base_power": circuit.Sbase, "power_units": SiennaUnitSystem.NATURAL_UNITS.value,
                "parameter_units": SiennaImpedanceUnitBasis.COMPONENT_BASE.value})
            arc_identifier += 1
    hidden_star_identifier: int = max(bus_ids.values()) + 1 if len(bus_ids) > 0 else 1
    for transformer in circuit.get_transformers3w():
        transformer_identifier: int = _get_sienna_identifier(transformer.code, "Transformer3W", transformer.name)
        terminal_buses: list[Bus] = [transformer.bus1, transformer.bus2, transformer.bus3]
        terminal_ids: list[int] = list()
        for terminal_bus in terminal_buses:
            terminal_identifier: int | None = bus_ids.get(terminal_bus, None)
            if terminal_identifier is None:
                raise ValueError(f"Transformer3W '{transformer.name}' has a bus that is not in the circuit")
            else:
                terminal_ids.append(terminal_identifier)
        components["ACBus"].append({"id": hidden_star_identifier, "name": f"{transformer.name}_star",
                                    "available": transformer.active, "number": hidden_star_identifier,
                                    "base_voltage": 1.0, "magnitude": 1.0, "angle": 0.0,
                                    "voltage_limits": {"min": 0.9, "max": 1.1}, "bustype": "PQ"})
        circuit_ids: list[int] = [transformer_identifier * 10 + 1, transformer_identifier * 10 + 2,
                                  transformer_identifier * 10 + 3]
        winding_values: list[Winding] = [transformer.winding1, transformer.winding2, transformer.winding3]
        ratings: list[float] = [transformer.rate1, transformer.rate2, transformer.rate3]
        for index, winding in enumerate(winding_values):
            components["Arc"].append({"id": arc_identifier, "from_id": terminal_ids[index],
                                       "to_id": hidden_star_identifier})
            components["TransformerCircuit"].append({"id": circuit_ids[index], "available": transformer.active,
                "arc": arc_identifier, "tap": 1.0, "alpha": 0.0,
                "parameter_units": SiennaImpedanceUnitBasis.COMPONENT_BASE.value, "r": winding.R, "x": winding.X,
                "control_objective": "UNDEFINED", "regulated_bus_number": 0, "number_of_tap_positions": 1,
                "rating": ratings[index], "active_power_flow": 0.0, "reactive_power_flow": 0.0,
                "base_power": circuit.Sbase, "power_units": SiennaUnitSystem.NATURAL_UNITS.value,
                "base_voltage_primary": winding.HV, "base_voltage_secondary": 1.0})
            arc_identifier += 1
        components["ThreeWindingTransformer"].append({"id": transformer_identifier, "name": transformer.name,
            "primary_circuit": circuit_ids[0], "secondary_circuit": circuit_ids[1],
            "tertiary_circuit": circuit_ids[2], "star_bus": hidden_star_identifier,
            "parameter_units": SiennaImpedanceUnitBasis.COMPONENT_BASE.value, "r_12": transformer.r12,
            "x_12": transformer.x12, "r_23": transformer.r23, "x_23": transformer.x23,
            "r_31": transformer.r31, "x_31": transformer.x31, "base_power_12": circuit.Sbase,
            "base_power_23": circuit.Sbase, "base_power_31": circuit.Sbase,
            "admittance_units": "COMPONENT_BASE", "magnetizing_shunt": {"real": 0.0, "imag": 0.0},
            "shunt_location": "PRIMARY"})
        hidden_star_identifier += 1
    return {"schema_version": SiennaSchemaVersion.V0_4_0.value, "name": circuit.name,
            "frequency": circuit.fBase, "components": components, "supplemental_attributes": list(),
            "supplemental_attribute_associations": list(), "plant_associations": list(),
            "combined_cycle_associations": list(), "service_associations": list(),
            "trading_hub_associations": list(), "voltage_control_associations": list(),
            "time_series_associations": list(), "time_series_storage_file": None}


def _validate_supported_veragrid_devices(circuit: MultiCircuit) -> None:
    """Reject VeraGrid devices the first Sienna adapter cannot preserve.

    :param circuit: VeraGrid circuit to inspect.
    :return: None.
    :raises ValueError: When unsupported non-empty device groups are found.
    """
    # Refuse only electrical devices whose omission would alter the exported network.
    unsupported_groups: dict[str, int] = {
        "DC lines": len(circuit.get_dc_lines()),
        "HVDC lines": len(circuit.get_hvdc()),
        "VSC converters": len(circuit.get_vsc()),
        "UPFC devices": len(circuit.get_upfc()),
        "switches": len(circuit.get_switches()),
        "multi-winding transformers": len(circuit.get_transformers_nw()),
        "current injections": len(circuit.get_current_injections()),
    }
    for group_name, group_count in unsupported_groups.items():
        if group_count > 0:
            raise ValueError(f"Sienna export does not yet support VeraGrid {group_name}")
        else:
            pass


def _get_sienna_identifier(code: str, device_type: str, device_name: str) -> int:
    """Read the required integer Sienna identifier from a VeraGrid device code.

    :param code: VeraGrid secondary code.
    :param device_type: VeraGrid device type for diagnostics.
    :param device_name: VeraGrid device name for diagnostics.
    :return: Sienna integer identifier.
    :raises ValueError: When the VeraGrid device code is not a positive integer.
    """
    try:
        identifier: int = int(code)
    except ValueError as error:
        raise ValueError(f"{device_type} '{device_name}' needs an integer code for Sienna export") from error
    if identifier <= 0:
        raise ValueError(f"{device_type} '{device_name}' needs a positive integer code for Sienna export")
    else:
        return identifier


def _zero_import_export_cost() -> dict[str, Any]:
    """Create the schema-required neutral Source import/export cost.

    :return: Zero-valued Sienna ImportExportCost object.
    """
    linear_curve: dict[str, Any] = {"curve_type": "INPUT_OUTPUT", "function_data": {
        "function_type": "LINEAR", "constant_term": 0.0, "proportional_term": 0.0}, "input_at_zero": 0.0}
    offer_curve: dict[str, Any] = {"variable_cost_type": "COST",
                                   "power_units": SiennaUnitSystem.NATURAL_UNITS.value,
                                   "value_curve": {"value": linear_curve}, "vom_cost": linear_curve}
    return {"cost_type": "IMPORTEXPORT", "import_offer_curves": offer_curve,
            "export_offer_curves": offer_curve, "energy_import_weekly_limit": 1000000.0,
            "energy_export_weekly_limit": 1000000.0}


def _zero_thermal_generation_cost() -> dict[str, Any]:
    """Create the parser-compatible neutral thermal generation cost.

    :return: Zero-valued Sienna ThermalGenerationCost object.
    """
    input_output: dict[str, Any] = {"curve_type": "INPUT_OUTPUT", "function_data": {
        "function_type": "LINEAR", "constant_term": 0.0, "proportional_term": 0.0}, "input_at_zero": 0.0}
    cost_curve: dict[str, Any] = {"power_units": SiennaUnitSystem.NATURAL_UNITS.value,
                                  "variable_cost_type": "COST", "value_curve": {"value": input_output},
                                  "vom_cost": input_output}
    return {"cost_type": "THERMAL", "fixed": 0.0, "shut_down": 0.0,
            "start_up": {"startup_stages_type": "STAGES", "cold": 0.0, "hot": 0.0, "warm": 0.0},
            "variable_operation_cost": cost_curve}
