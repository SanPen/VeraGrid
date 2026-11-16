# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Convert the supported Sienna v0.4 static-network subset into VeraGrid."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

import VeraGridEngine.Devices as dev
from VeraGridEngine.enumerations import ShuntControlMode
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.sienna.devices import (SiennaACBus, SiennaArc, SiennaArea, SiennaDCBus, SiennaLine,
                                               SiennaLoadZone, SiennaPowerLoad, SiennaSchemaVersion,
                                               SiennaSystemDocument, parse_sienna_ac_bus, parse_sienna_arc,
                                               parse_sienna_area, parse_sienna_dc_bus, parse_sienna_line,
                                               parse_sienna_load_zone, parse_sienna_power_load,
                                               SiennaFixedAdmittance, parse_sienna_fixed_admittance)
from VeraGridEngine.IO.sienna.devices.schema_object import (SiennaObjectKind, SiennaSchemaModel,
                                                            parse_sienna_schema_object)
from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
from VeraGridEngine.IO.sienna.sienna_json_validator import SiennaJsonValidator
from VeraGridEngine.IO.sienna.devices.format_version import resolve_sienna_format_version
from VeraGridEngine.IO.sienna.devices.core.associations.supplemental_attribute_association import (SiennaSupplementalAttributeAssociation,
                                                                                                    parse_sienna_supplemental_attribute_association)
from VeraGridEngine.IO.sienna.devices.operations.static_injection.standard_load import SiennaStandardLoad
from VeraGridEngine.IO.sienna.devices.operations.static_injection.exponential_load import SiennaExponentialLoad
from VeraGridEngine.IO.sienna.devices.operations.static_injection.renewable_non_dispatch import SiennaRenewableNonDispatch
from VeraGridEngine.IO.sienna.devices.operations.static_injection.synchronous_condenser import SiennaSynchronousCondenser
from VeraGridEngine.IO.sienna.devices.operations.static_injection.motor_load import SiennaMotorLoad
from VeraGridEngine.IO.sienna.devices.operations.static_injection.renewable_dispatch import SiennaRenewableDispatch
from VeraGridEngine.IO.sienna.devices.operations.static_injection.source import SiennaSource
from VeraGridEngine.IO.sienna.devices.operations.static_injection.switched_admittance import SiennaSwitchedAdmittance
from VeraGridEngine.IO.sienna.devices.operations.common.switched_admittance_control_mode import SiennaSwitchedAdmittanceControlMode
from VeraGridEngine.IO.sienna.devices.operations.static_injection.energy_reservoir_storage import SiennaEnergyReservoirStorage
from VeraGridEngine.IO.sienna.devices.operations.branch.generic_arc_impedance import SiennaGenericArcImpedance
from VeraGridEngine.IO.sienna.devices.operations.branch.two_winding_transformer import SiennaTwoWindingTransformer
from VeraGridEngine.IO.sienna.devices.operations.branch.transformer_circuit import SiennaTransformerCircuit
from VeraGridEngine.IO.sienna.devices.operations.branch.series_compensator import SiennaSeriesCompensator
from VeraGridEngine.IO.sienna.devices.operations.static_injection.thermal_standard import SiennaThermalStandard
from VeraGridEngine.IO.sienna.devices.operations.static_injection.hydro_turbine import SiennaHydroTurbine
from VeraGridEngine.IO.sienna.devices.operations.static_injection.hydro_dispatch import SiennaHydroDispatch
from VeraGridEngine.IO.sienna.devices.operations.static_injection.hydro_pump_turbine import SiennaHydroPumpTurbine
from VeraGridEngine.IO.sienna.devices.operations.static_injection.facts_control_device import SiennaFACTSControlDevice
from VeraGridEngine.IO.sienna.devices.operations.branch.discrete_controlled_ac_branch import SiennaDiscreteControlledACBranch
from VeraGridEngine.IO.sienna.devices.operations.branch.three_winding_transformer import SiennaThreeWindingTransformer
from VeraGridEngine.IO.sienna.devices.operations.static_injection.hybrid_system import SiennaHybridSystem
from VeraGridEngine.IO.sienna.devices.operations.static_injection.interruptible_power_load import SiennaInterruptiblePowerLoad
from VeraGridEngine.IO.sienna.devices.operations.static_injection.interruptible_standard_load import SiennaInterruptibleStandardLoad
from VeraGridEngine.IO.sienna.devices.operations.static_injection.shiftable_power_load import SiennaShiftablePowerLoad
from VeraGridEngine.IO.sienna.devices.operations.common.operational_states import SiennaOperationalStates
from VeraGridEngine.IO.sienna.devices.operations.associations.plant_association import parse_sienna_plant_association
from VeraGridEngine.IO.sienna.devices.operations.associations.combined_cycle_association import parse_sienna_combined_cycle_association
from VeraGridEngine.IO.sienna.devices.operations.associations.service_association import parse_sienna_service_association
from VeraGridEngine.IO.sienna.devices.operations.associations.trading_hub_association import parse_sienna_trading_hub_association
from VeraGridEngine.IO.sienna.devices.operations.associations.voltage_control_association import parse_sienna_voltage_control_association
from VeraGridEngine.IO.sienna.devices.time_series.time_series_association import parse_sienna_time_series_association


def load_sienna_document(file_name: str, schema_directory: Path) -> SiennaSystemDocument:
    """Load, validate and parse one pinned-version Sienna SystemDocument JSON file.

    :param file_name: SystemDocument JSON file name.
    :param schema_directory: Root directory of the pinned SiennaSchemas checkout.
    :return: Parsed supported Sienna SystemDocument.
    :raises ValueError: When the document is invalid or outside the supported subset.
    """
    with Path(file_name).open(encoding="utf-8") as document_file:
        raw_document: Any = json.load(document_file)
    if not isinstance(raw_document, dict):
        raise ValueError("Sienna SystemDocument root must be an object")
    else:
        pass
    validator: SiennaJsonValidator = SiennaJsonValidator(schema_directory=schema_directory)
    validator.validate(raw_document)
    return parse_sienna_document(raw_document)


def parse_sienna_document(data: dict[str, Any]) -> SiennaSystemDocument:
    """Create Sienna device objects from a schema-validated document.

    :param data: Schema-validated Sienna SystemDocument data.
    :return: Parsed Sienna SystemDocument.
    :raises ValueError: When required conversion metadata is absent or unsupported.
    """
    schema_version_value: Any | None = data.get("schema_version", None)
    if not isinstance(schema_version_value, str):
        raise ValueError("Sienna schema_version must be a string")
    else:
        resolve_sienna_format_version(schema_version_value)
    _validate_empty_association_tables(data)
    components: Any | None = data.get("components", None)
    if not isinstance(components, dict):
        raise ValueError("Sienna SystemDocument components must be an object")
    else:
        pass
    areas: list[SiennaArea] = _parse_areas(components)
    load_zones: list[SiennaLoadZone] = _parse_load_zones(components)
    buses: list[SiennaACBus] = _parse_ac_buses(components)
    dc_buses: list[SiennaDCBus] = _parse_dc_buses(components)
    arcs: list[SiennaArc] = _parse_arcs(components)
    lines: list[SiennaLine] = _parse_lines(components)
    power_loads: list[SiennaPowerLoad] = _parse_power_loads(components)
    fixed_admittances: list[SiennaFixedAdmittance] = _parse_fixed_admittances(components)
    unmapped_components: dict[SiennaObjectKind, list[SiennaSchemaModel]] = _parse_unmapped_components(components)
    supplemental_attribute_associations: list[SiennaSupplementalAttributeAssociation] = [parse_sienna_supplemental_attribute_association(row) for row in data.get("supplemental_attribute_associations", list())]
    supplemental_attributes: list[SiennaSchemaModel] = _parse_supplemental_attributes(
        values=data.get("supplemental_attributes", list()), associations=supplemental_attribute_associations)
    return SiennaSystemDocument(schema_version=SiennaSchemaVersion.V0_4_0, name=data.get("name", None),
                                description=data.get("description", None), frequency=data.get("frequency", None),
                                areas=areas, load_zones=load_zones,
                                buses=buses, dc_buses=dc_buses, arcs=arcs, lines=lines, power_loads=power_loads,
                                fixed_admittances=fixed_admittances, unmapped_components=unmapped_components,
                                supplemental_attributes=supplemental_attributes,
                                supplemental_attribute_associations=supplemental_attribute_associations,
                                plant_associations=[parse_sienna_plant_association(row) for row in data.get("plant_associations", list())],
                                combined_cycle_associations=[parse_sienna_combined_cycle_association(row) for row in data.get("combined_cycle_associations", list())],
                                service_associations=[parse_sienna_service_association(row) for row in data.get("service_associations", list())],
                                trading_hub_associations=[parse_sienna_trading_hub_association(row) for row in data.get("trading_hub_associations", list())],
                                voltage_control_associations=[parse_sienna_voltage_control_association(row) for row in data.get("voltage_control_associations", list())],
                                time_series_associations=[parse_sienna_time_series_association(row) for row in data.get("time_series_associations", list())],
                                ext=data.get("ext", dict()),
                                time_series_storage_file=data.get("time_series_storage_file", None))


def _parse_supplemental_attributes(values: object, associations: list[SiennaSupplementalAttributeAssociation]) -> list[SiennaSchemaModel]:
    """Materialize supplemental attributes through their declared association discriminator.

    :param values: Raw supplemental-attribute JSON rows.
    :param associations: Typed rows carrying the declared attribute type for each identifier.
    :return: Concrete fixed-slot supplemental-attribute models.
    :raises ValueError: When a row lacks a declared association discriminator.
    """
    if not isinstance(values, list):
        raise ValueError("Sienna SystemDocument supplemental_attributes must be an array")
    else:
        pass
    attribute_kinds: dict[int, SiennaObjectKind] = dict()
    for association in associations:
        attribute_type: str = association.attribute_type
        attribute_identifier: int = association.attribute_id
        try:
            attribute_kinds[attribute_identifier] = SiennaObjectKind(attribute_type)
        except ValueError as error:
            raise ValueError(f"Unsupported Sienna supplemental attribute type '{attribute_type}'") from error
    parsed_attributes: list[SiennaSchemaModel] = list()
    for value in values:
        if isinstance(value, dict):
            raw_identifier: object = value.get("id", None)
            if isinstance(raw_identifier, int):
                kind: SiennaObjectKind | None = attribute_kinds.get(raw_identifier, None)
                if kind is None:
                    raise ValueError(f"Supplemental attribute {raw_identifier} has no declared association")
                else:
                    parsed_attributes.append(parse_sienna_schema_object(kind=kind, data=value))
            else:
                raise ValueError("Supplemental attribute must declare an integer id")
        else:
            raise ValueError("Supplemental attribute must be a JSON object")
    return parsed_attributes


def sienna_to_veragrid(document: SiennaSystemDocument) -> MultiCircuit:
    """Convert a parsed Sienna document into a VeraGrid MultiCircuit.

    :param document: Parsed and validated Sienna SystemDocument.
    :return: VeraGrid circuit with the supported static network.
    :raises ValueError: When cross-reference or base-power constraints are invalid.
    """
    base_power: float = _get_common_base_power(document)
    frequency: float = 50.0 if document.frequency is None else document.frequency
    circuit: MultiCircuit = MultiCircuit(name="" if document.name is None else document.name,
                                        Sbase=base_power, fbase=frequency)
    hidden_star_bus_ids: set[int] = _get_three_winding_star_bus_ids(document.unmapped_components)
    areas_by_id: dict[int, dev.Area] = dict()
    for sienna_area in document.areas:
        area: dev.Area = dev.Area(name=sienna_area.name, code=str(sienna_area.identifier))
        areas_by_id[sienna_area.identifier] = area
        circuit.add_area(obj=area)
    zones_by_id: dict[int, dev.Zone] = dict()
    for sienna_load_zone in document.load_zones:
        load_zone: dev.Zone = dev.Zone(name=sienna_load_zone.name, code=str(sienna_load_zone.identifier))
        zones_by_id[sienna_load_zone.identifier] = load_zone
        circuit.add_zone(obj=load_zone)
    buses_by_id: dict[int, dev.Bus] = dict()
    for sienna_bus in document.buses:
        if sienna_bus.identifier in hidden_star_bus_ids:
            # Transformer3W creates VeraGrid's internal star bus during its own conversion.
            pass
        else:
            bus: dev.Bus = _convert_bus(sienna_bus, areas_by_id, zones_by_id)
            buses_by_id[sienna_bus.identifier] = bus
            circuit.add_bus(obj=bus)
    for sienna_dc_bus in document.dc_buses:
        dc_bus: dev.Bus = _convert_dc_bus(sienna_dc_bus, areas_by_id, zones_by_id)
        buses_by_id[sienna_dc_bus.identifier] = dc_bus
        circuit.add_bus(obj=dc_bus)
    arcs_by_id: dict[int, SiennaArc] = dict()
    for arc in document.arcs:
        _validate_arc_buses(arc, buses_by_id, hidden_star_bus_ids)
        arcs_by_id[arc.identifier] = arc
    for sienna_line in document.lines:
        arc: SiennaArc | None = arcs_by_id.get(sienna_line.arc, None)
        if arc is None:
            raise ValueError(f"Line '{sienna_line.name}' references unknown Arc {sienna_line.arc}")
        else:
            pass
        if sienna_line.base_power != circuit.Sbase:
            raise ValueError(f"Line '{sienna_line.name}' base_power differs from the VeraGrid circuit base")
        else:
            line: dev.Line = dev.Line(bus_from=buses_by_id[arc.from_id], bus_to=buses_by_id[arc.to_id],
                                      name=sienna_line.name, code=str(sienna_line.identifier),
                                      r=sienna_line.resistance, x=sienna_line.reactance,
                                      b=sienna_line.susceptance, g=sienna_line.conductance,
                                      rate=sienna_line.rating, active=sienna_line.available)
            circuit.add_line(obj=line)
    for sienna_load in document.power_loads:
        bus: dev.Bus | None = buses_by_id.get(sienna_load.bus, None)
        if bus is None:
            raise ValueError(f"PowerLoad '{sienna_load.name}' references unknown ACBus {sienna_load.bus}")
        else:
            load: dev.Load = dev.Load(name=sienna_load.name, code=str(sienna_load.identifier),
                                      P=sienna_load.active_power, Q=sienna_load.reactive_power,
                                      active=sienna_load.available)
            circuit.add_load(bus=bus, api_obj=load)
    for sienna_shunt in document.fixed_admittances:
        bus: dev.Bus | None = buses_by_id.get(sienna_shunt.bus, None)
        if bus is None:
            raise ValueError(f"FixedAdmittance '{sienna_shunt.name}' references unknown bus {sienna_shunt.bus}")
        else:
            shunt: dev.Shunt = dev.Shunt(name=sienna_shunt.name, code=str(sienna_shunt.identifier),
                                         G=sienna_shunt.conductance, B=sienna_shunt.susceptance,
                                         active=sienna_shunt.available)
            circuit.add_shunt(bus=bus, api_obj=shunt)
    _convert_standard_loads(document.unmapped_components, buses_by_id, circuit)
    _convert_exponential_loads(document.unmapped_components, buses_by_id, circuit)
    _convert_renewable_non_dispatch(document.unmapped_components, buses_by_id, circuit)
    _convert_synchronous_condensers(document.unmapped_components, buses_by_id, circuit)
    _convert_motor_loads(document.unmapped_components, buses_by_id, circuit)
    _convert_renewable_dispatch(document.unmapped_components, buses_by_id, circuit)
    _convert_sources(document.unmapped_components, buses_by_id, circuit)
    _convert_switched_admittances(document.unmapped_components, buses_by_id, circuit)
    _convert_energy_reservoir_storage(document.unmapped_components, buses_by_id, circuit)
    _convert_generic_arc_impedances(document.unmapped_components, arcs_by_id, buses_by_id, circuit)
    _convert_two_winding_transformers(document.unmapped_components, arcs_by_id, buses_by_id, circuit)
    _convert_series_compensators(document.unmapped_components, arcs_by_id, buses_by_id, circuit)
    _convert_thermal_standard(document.unmapped_components, buses_by_id, circuit)
    _convert_hydro_turbines(document.unmapped_components, buses_by_id, circuit)
    _convert_hydro_dispatch(document.unmapped_components, buses_by_id, circuit)
    _convert_hydro_pump_turbines(document.unmapped_components, buses_by_id, circuit)
    _convert_facts_control_devices(document.unmapped_components, buses_by_id, circuit)
    _convert_discrete_controlled_ac_branches(document.unmapped_components, arcs_by_id, buses_by_id, circuit)
    _convert_three_winding_transformers(document.unmapped_components, arcs_by_id, buses_by_id, circuit)
    _convert_hybrid_systems(document.unmapped_components, buses_by_id, circuit)
    _convert_interruptible_power_loads(document.unmapped_components, buses_by_id, circuit)
    _convert_interruptible_standard_loads(document.unmapped_components, buses_by_id, circuit)
    _convert_shiftable_power_loads(document.unmapped_components, buses_by_id, circuit)
    if len(document.unmapped_components) > 0:
        unsupported_kinds: list[str] = list()
        for object_kind in document.unmapped_components:
            if object_kind not in (SiennaObjectKind.StandardLoad, SiennaObjectKind.ExponentialLoad,
                                   SiennaObjectKind.RenewableNonDispatch,
                                   SiennaObjectKind.SynchronousCondenser, SiennaObjectKind.MotorLoad,
                                   SiennaObjectKind.RenewableDispatch, SiennaObjectKind.Source,
                                   SiennaObjectKind.SwitchedAdmittance,
                                   SiennaObjectKind.EnergyReservoirStorage,
                                   SiennaObjectKind.GenericArcImpedance, SiennaObjectKind.TwoWindingTransformer,
                                   SiennaObjectKind.TransformerCircuit, SiennaObjectKind.SeriesCompensator,
                                   SiennaObjectKind.ThermalStandard, SiennaObjectKind.HydroTurbine,
                                   SiennaObjectKind.HydroDispatch, SiennaObjectKind.InterruptiblePowerLoad,
                                   SiennaObjectKind.HydroPumpTurbine,
                                   SiennaObjectKind.FACTSControlDevice,
                                   SiennaObjectKind.DiscreteControlledACBranch,
                                   SiennaObjectKind.ThreeWindingTransformer,
                                   SiennaObjectKind.HybridSystem,
                                   SiennaObjectKind.InterruptibleStandardLoad,
                                   SiennaObjectKind.ShiftablePowerLoad):
                unsupported_kinds.append(object_kind.value)
            else:
                pass
        if len(unsupported_kinds) > 0:
            raise ValueError(f"VeraGrid conversion does not yet support Sienna components: {unsupported_kinds}")
        else:
            pass
    else:
        pass
    return circuit


def _convert_standard_loads(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                            buses_by_id: dict[int, dev.Bus], circuit: MultiCircuit) -> None:
    """Convert Sienna ZIP loads at their nominal one-per-unit operating point.

    :param components: Remaining typed Sienna component buckets.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.StandardLoad, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaStandardLoad):
                bus: dev.Bus | None = buses_by_id.get(value.bus, None)
                if bus is None:
                    raise ValueError(f"StandardLoad '{value.name}' references unknown ACBus {value.bus}")
                else:
                    active_power: float = (value.constant_active_power + value.impedance_active_power
                                           + value.current_active_power)
                    reactive_power: float = (value.constant_reactive_power + value.impedance_reactive_power
                                             + value.current_reactive_power)
                    load: dev.Load = dev.Load(name=value.name, code=str(value.identifier), P=active_power,
                                              Q=reactive_power, active=value.available)
                    circuit.add_load(bus=bus, api_obj=load)
            else:
                raise ValueError("StandardLoad bucket contains a non-StandardLoad object")


def _convert_exponential_loads(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                               buses_by_id: dict[int, dev.Bus], circuit: MultiCircuit) -> None:
    """Convert exponential demands at their declared initial operating point.

    :param components: Remaining typed Sienna component buckets.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.ExponentialLoad, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaExponentialLoad):
                bus: dev.Bus | None = buses_by_id.get(value.bus, None)
                if bus is None:
                    raise ValueError(f"ExponentialLoad '{value.name}' references unknown ACBus {value.bus}")
                else:
                    load: dev.Load = dev.Load(name=value.name, code=str(value.id), P=value.active_power,
                                              Q=value.reactive_power, active=value.available)
                    circuit.add_load(bus=bus, api_obj=load)
            else:
                raise ValueError("ExponentialLoad bucket contains a non-ExponentialLoad object")


def _convert_renewable_non_dispatch(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                                    buses_by_id: dict[int, dev.Bus], circuit: MultiCircuit) -> None:
    """Convert non-dispatchable renewable injections into VeraGrid static generators.

    :param components: Remaining typed Sienna component buckets.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.RenewableNonDispatch, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaRenewableNonDispatch):
                bus: dev.Bus | None = buses_by_id.get(value.bus, None)
                if bus is None:
                    raise ValueError(f"RenewableNonDispatch '{value.name}' references unknown ACBus {value.bus}")
                else:
                    generator: dev.StaticGenerator = dev.StaticGenerator(name=value.name, code=str(value.id),
                                                                           P=value.active_power,
                                                                           Q=value.reactive_power,
                                                                           Snom=value.rating,
                                                                           active=value.available)
                    circuit.add_static_generator(bus=bus, api_obj=generator)
            else:
                raise ValueError("RenewableNonDispatch bucket contains a non-RenewableNonDispatch object")


def _convert_synchronous_condensers(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                                    buses_by_id: dict[int, dev.Bus], circuit: MultiCircuit) -> None:
    """Convert synchronous condensers into reactive-capability VeraGrid generators.

    :param components: Remaining typed Sienna component buckets.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.SynchronousCondenser, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaSynchronousCondenser):
                bus: dev.Bus | None = buses_by_id.get(value.bus, None)
                if bus is None:
                    raise ValueError(f"SynchronousCondenser '{value.name}' references unknown ACBus {value.bus}")
                else:
                    limits = value.reactive_power_limits
                    q_min: float = -value.rating if limits is None else limits.min
                    q_max: float = value.rating if limits is None else limits.max
                    active_power_losses: float = 0.0 if value.active_power_losses is None else value.active_power_losses
                    generator: dev.Generator = dev.Generator(name=value.name, code=str(value.id),
                                                             P=-active_power_losses,
                                                             Q=value.reactive_power, Qmin=q_min, Qmax=q_max,
                                                             Snom=value.rating, active=value.available,
                                                             Sbase=value.base_power)
                    circuit.add_generator(bus=bus, api_obj=generator)
            else:
                raise ValueError("SynchronousCondenser bucket contains a non-SynchronousCondenser object")


def _convert_motor_loads(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                         buses_by_id: dict[int, dev.Bus], circuit: MultiCircuit) -> None:
    """Convert Sienna motor loads at their declared electrical operating point.

    :param components: Remaining typed Sienna component buckets.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.MotorLoad, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaMotorLoad):
                bus: dev.Bus | None = buses_by_id.get(value.bus, None)
                if bus is None:
                    raise ValueError(f"MotorLoad '{value.name}' references unknown ACBus {value.bus}")
                else:
                    load: dev.Load = dev.Load(name=value.name, code=str(value.id), P=value.active_power,
                                              Q=value.reactive_power, active=value.available)
                    circuit.add_load(bus=bus, api_obj=load)
            else:
                raise ValueError("MotorLoad bucket contains a non-MotorLoad object")


def _convert_renewable_dispatch(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                                buses_by_id: dict[int, dev.Bus], circuit: MultiCircuit) -> None:
    """Convert dispatchable renewable injections into VeraGrid generators.

    :param components: Remaining typed Sienna component buckets.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.RenewableDispatch, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaRenewableDispatch):
                bus: dev.Bus | None = buses_by_id.get(value.bus, None)
                if bus is None:
                    raise ValueError(f"RenewableDispatch '{value.name}' references unknown ACBus {value.bus}")
                else:
                    limits = value.reactive_power_limits
                    q_min: float = -value.rating if limits is None else limits.min
                    q_max: float = value.rating if limits is None else limits.max
                    generator: dev.Generator = dev.Generator(name=value.name, code=str(value.id),
                                                             P=value.active_power, Q=value.reactive_power,
                                                             Pmin=0.0, Pmax=value.rating, Qmin=q_min, Qmax=q_max,
                                                             Snom=value.rating, active=value.available,
                                                             Sbase=value.base_power)
                    circuit.add_generator(bus=bus, api_obj=generator)
            else:
                raise ValueError("RenewableDispatch bucket contains a non-RenewableDispatch object")


def _convert_sources(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                     buses_by_id: dict[int, dev.Bus], circuit: MultiCircuit) -> None:
    """Convert Sienna Thevenin sources into VeraGrid external-grid injections.

    :param components: Remaining typed Sienna component buckets.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.Source, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaSource):
                bus: dev.Bus | None = buses_by_id.get(value.bus, None)
                if bus is None:
                    raise ValueError(f"Source '{value.name}' references unknown ACBus {value.bus}")
                else:
                    magnitude: float = 1.0 if value.internal_voltage is None else value.internal_voltage
                    angle: float = 0.0 if value.internal_angle is None else value.internal_angle
                    active_power: float = 0.0 if value.active_power is None else value.active_power
                    reactive_power: float = 0.0 if value.reactive_power is None else value.reactive_power
                    source: dev.ExternalGrid = dev.ExternalGrid(name=value.name, code=str(value.id),
                                                                 Vm=magnitude, Va=angle, P=active_power,
                                                                 Q=reactive_power, active=value.available)
                    circuit.add_external_grid(bus=bus, api_obj=source)
            else:
                raise ValueError("Source bucket contains a non-Source object")


def _convert_switched_admittances(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                                  buses_by_id: dict[int, dev.Bus], circuit: MultiCircuit) -> None:
    """Convert switched shunts at their declared engaged-step operating point.

    :param components: Remaining typed Sienna component buckets.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.SwitchedAdmittance, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaSwitchedAdmittance):
                bus: dev.Bus | None = buses_by_id.get(value.bus, None)
                if bus is None:
                    raise ValueError(f"SwitchedAdmittance '{value.name}' references unknown ACBus {value.bus}")
                else:
                    conductance: float = 0.0
                    susceptance: float = 0.0
                    if value.number_engaged is None or value.Y_increase is None:
                        pass
                    else:
                        if len(value.number_engaged) != len(value.Y_increase):
                            raise ValueError(f"SwitchedAdmittance '{value.name}' has mismatched step arrays")
                        else:
                            for index, engaged_steps in enumerate(value.number_engaged):
                                admittance = value.Y_increase[index]
                                conductance += engaged_steps * admittance.real
                                susceptance += engaged_steps * admittance.imag
                    declared_steps: int = 1 if value.number_of_steps is None else sum(value.number_of_steps)
                    mode: ShuntControlMode = _map_switched_admittance_control_mode(value.control_mode)
                    control_bus: dev.Bus | None = buses_by_id.get(value.regulated_bus_number, None)
                    shunt: dev.ControllableShunt = dev.ControllableShunt(
                        name=value.name, code=str(value.id), number_of_steps=declared_steps, step=0,
                        G=conductance, B=susceptance, active=value.available, control_bus=control_bus,
                        control_mode=mode,
                        vmin=0.9 if value.voltage_limits is None else value.voltage_limits.min,
                        vmax=1.1 if value.voltage_limits is None else value.voltage_limits.max)
                    if value.number_of_steps is None or value.Y_increase is None:
                        pass
                    else:
                        imaginary_blocks: list[float] = list()
                        real_blocks: list[float] = list()
                        for index, step_count in enumerate(value.number_of_steps):
                            imaginary_blocks.append(value.Y_increase[index].imag)
                            real_blocks.append(step_count * value.Y_increase[index].real)
                        shunt.set_blocks(value.number_of_steps, imaginary_blocks)
                        shunt.g_steps = np.asarray(real_blocks, dtype=float)
                    circuit.add_controllable_shunt(bus=bus, api_obj=shunt)
            else:
                raise ValueError("SwitchedAdmittance bucket contains a non-SwitchedAdmittance object")


def _map_switched_admittance_control_mode(mode: SiennaSwitchedAdmittanceControlMode | None) -> ShuntControlMode:
    """Map declared Sienna shunt controls to the closest VeraGrid control mode.

    :param mode: Sienna switched-admittance control selector.
    :return: VeraGrid shunt-control selector.
    """
    if mode is SiennaSwitchedAdmittanceControlMode.FIXED:
        return ShuntControlMode.Locked
    elif mode is SiennaSwitchedAdmittanceControlMode.CONTINUOUS_VOLTAGE:
        return ShuntControlMode.Continuous
    elif mode is SiennaSwitchedAdmittanceControlMode.DISCRETE_VOLTAGE:
        return ShuntControlMode.Discrete
    else:
        return ShuntControlMode.ReactivePower


def _convert_energy_reservoir_storage(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                                      buses_by_id: dict[int, dev.Bus], circuit: MultiCircuit) -> None:
    """Convert energy-reservoir storage into VeraGrid batteries.

    :param components: Remaining typed Sienna component buckets.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.EnergyReservoirStorage, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaEnergyReservoirStorage):
                bus: dev.Bus | None = buses_by_id.get(value.bus, None)
                if bus is None:
                    raise ValueError(f"EnergyReservoirStorage '{value.name}' references unknown ACBus {value.bus}")
                elif value.storage_capacity <= 0.0:
                    raise ValueError(f"EnergyReservoirStorage '{value.name}' must have positive storage_capacity")
                else:
                    q_limits = value.reactive_power_limits
                    q_min: float = -value.rating if q_limits is None else q_limits.min
                    q_max: float = value.rating if q_limits is None else q_limits.max
                    p_min: float = -value.input_active_power_limits.max
                    p_max: float = value.output_active_power_limits.max
                    min_soc: float = value.storage_level_limits.min / value.storage_capacity
                    max_soc: float = value.storage_level_limits.max / value.storage_capacity
                    soc: float = value.initial_storage_capacity_level / value.storage_capacity
                    battery: dev.Battery = dev.Battery(name=value.name, code=str(value.id), P=value.active_power,
                                                       Pmin=p_min, Pmax=p_max, Q=value.reactive_power,
                                                       Qmin=q_min, Qmax=q_max, Snom=value.rating,
                                                       Enom=value.storage_capacity, active=value.available,
                                                       Sbase=value.base_power,
                                                       charge_efficiency=value.efficiency.in_,
                                                       discharge_efficiency=value.efficiency.out,
                                                       min_soc=min_soc, max_soc=max_soc, soc=soc)
                    circuit.add_battery(bus=bus, api_obj=battery)
            else:
                raise ValueError("EnergyReservoirStorage bucket contains a non-EnergyReservoirStorage object")


def _convert_generic_arc_impedances(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                                    arcs_by_id: dict[int, SiennaArc], buses_by_id: dict[int, dev.Bus],
                                    circuit: MultiCircuit) -> None:
    """Convert generic arc impedances into VeraGrid lines.

    :param components: Remaining typed Sienna component buckets.
    :param arcs_by_id: Sienna arcs indexed by identifier.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.GenericArcImpedance, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaGenericArcImpedance):
                arc: SiennaArc | None = arcs_by_id.get(value.arc, None)
                if arc is None:
                    raise ValueError(f"GenericArcImpedance '{value.name}' references unknown Arc {value.arc}")
                elif value.base_power != circuit.Sbase:
                    raise ValueError(f"GenericArcImpedance '{value.name}' base_power differs from circuit base")
                else:
                    line: dev.Line = dev.Line(bus_from=buses_by_id[arc.from_id], bus_to=buses_by_id[arc.to_id],
                                              name=value.name, code=str(value.id), r=value.r, x=value.x,
                                              b=0.0, g=0.0, active=value.available)
                    circuit.add_line(obj=line)
            else:
                raise ValueError("GenericArcImpedance bucket contains a non-GenericArcImpedance object")


def _convert_two_winding_transformers(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                                      arcs_by_id: dict[int, SiennaArc], buses_by_id: dict[int, dev.Bus],
                                      circuit: MultiCircuit) -> None:
    """Join two-winding transformer wrappers to their circuit electrical records.

    :param components: Remaining typed Sienna component buckets.
    :param arcs_by_id: Sienna arcs indexed by identifier.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    transformer_values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.TwoWindingTransformer, None)
    circuit_values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.TransformerCircuit, None)
    if transformer_values is None and circuit_values is None:
        pass
    elif transformer_values is None or circuit_values is None:
        raise ValueError("TwoWindingTransformer and TransformerCircuit buckets must both be present")
    else:
        circuits_by_id: dict[int, SiennaTransformerCircuit] = dict()
        for circuit_value in circuit_values:
            if isinstance(circuit_value, SiennaTransformerCircuit):
                circuits_by_id[circuit_value.id] = circuit_value
            else:
                raise ValueError("TransformerCircuit bucket contains a non-TransformerCircuit object")
        for transformer_value in transformer_values:
            if isinstance(transformer_value, SiennaTwoWindingTransformer):
                transformer_circuit: SiennaTransformerCircuit | None = circuits_by_id.get(transformer_value.circuit, None)
                if transformer_circuit is None:
                    raise ValueError(f"TwoWindingTransformer '{transformer_value.name}' references unknown circuit")
                elif transformer_circuit.base_power != circuit.Sbase:
                    raise ValueError(f"TwoWindingTransformer '{transformer_value.name}' base_power differs from circuit base")
                else:
                    arc: SiennaArc | None = arcs_by_id.get(transformer_circuit.arc, None)
                    if arc is None:
                        raise ValueError(f"TransformerCircuit {transformer_circuit.id} references unknown Arc")
                    else:
                        magnetizing = transformer_value.magnetizing_shunt
                        conductance: float = 0.0 if magnetizing is None else magnetizing.real
                        susceptance: float = 0.0 if magnetizing is None else magnetizing.imag
                        transformer: dev.Transformer2W = dev.Transformer2W(
                            bus_from=buses_by_id[arc.from_id], bus_to=buses_by_id[arc.to_id],
                            name=transformer_value.name, code=str(transformer_value.id),
                            HV=transformer_circuit.base_voltage_primary,
                            LV=transformer_circuit.base_voltage_secondary,
                            nominal_power=transformer_circuit.rating, rate=transformer_circuit.rating,
                            r=transformer_circuit.r, x=transformer_circuit.x, g=conductance, b=susceptance,
                            tap_module=transformer_circuit.tap, tap_phase=transformer_circuit.alpha,
                            active=transformer_circuit.available)
                        circuit.add_transformer2w(obj=transformer)
            else:
                raise ValueError("TwoWindingTransformer bucket contains a non-TwoWindingTransformer object")


def _convert_series_compensators(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                                 arcs_by_id: dict[int, SiennaArc], buses_by_id: dict[int, dev.Bus],
                                 circuit: MultiCircuit) -> None:
    """Convert series compensators into their declared present-state line equivalent.

    :param components: Remaining typed Sienna component buckets.
    :param arcs_by_id: Sienna arcs indexed by identifier.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.SeriesCompensator, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaSeriesCompensator):
                arc: SiennaArc | None = arcs_by_id.get(value.arc, None)
                if arc is None:
                    raise ValueError(f"SeriesCompensator '{value.name}' references unknown Arc {value.arc}")
                elif value.base_power != circuit.Sbase:
                    raise ValueError(f"SeriesCompensator '{value.name}' base_power differs from circuit base")
                else:
                    reactance: dev.SeriesReactance = dev.SeriesReactance(
                        bus_from=buses_by_id[arc.from_id], bus_to=buses_by_id[arc.to_id],
                        name=value.name, code=str(value.id), r=value.r, x=value.x, rate=value.rating,
                        active=value.available)
                    circuit.add_series_reactance(obj=reactance)
            else:
                raise ValueError("SeriesCompensator bucket contains a non-SeriesCompensator object")


def _convert_thermal_standard(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                              buses_by_id: dict[int, dev.Bus], circuit: MultiCircuit) -> None:
    """Convert thermal standard units into VeraGrid dispatchable generators.

    :param components: Remaining typed Sienna component buckets.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.ThermalStandard, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaThermalStandard):
                bus: dev.Bus | None = buses_by_id.get(value.bus, None)
                if bus is None:
                    raise ValueError(f"ThermalStandard '{value.name}' references unknown ACBus {value.bus}")
                else:
                    q_limits = value.reactive_power_limits
                    ramp_limits = value.ramp_limits
                    time_limits = value.time_limits
                    q_min: float = -value.rating if q_limits is None else q_limits.min
                    q_max: float = value.rating if q_limits is None else q_limits.max
                    ramp_down: float = 1e20 if ramp_limits is None else ramp_limits.down
                    ramp_up: float = 1e20 if ramp_limits is None else ramp_limits.up
                    min_time_down: float = 0.0 if time_limits is None else time_limits.down
                    min_time_up: float = 0.0 if time_limits is None else time_limits.up
                    active: bool = value.available and value.status == SiennaOperationalStates.ONLINE
                    generator: dev.Generator = dev.Generator(
                        name=value.name, code=str(value.id), P=value.active_power, Q=value.reactive_power,
                        Pmin=value.active_power_limits.min, Pmax=value.active_power_limits.max,
                        Qmin=q_min, Qmax=q_max, Snom=value.rating, active=active, Sbase=value.base_power,
                        ramp_down=ramp_down, ramp_up=ramp_up, min_time_down=min_time_down,
                        min_time_up=min_time_up)
                    circuit.add_generator(bus=bus, api_obj=generator)
            else:
                raise ValueError("ThermalStandard bucket contains a non-ThermalStandard object")


def _convert_hydro_turbines(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                            buses_by_id: dict[int, dev.Bus], circuit: MultiCircuit) -> None:
    """Convert hydro turbines into VeraGrid dispatchable generators.

    :param components: Remaining typed Sienna component buckets.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.HydroTurbine, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaHydroTurbine):
                bus: dev.Bus | None = buses_by_id.get(value.bus, None)
                if bus is None:
                    raise ValueError(f"HydroTurbine '{value.name}' references unknown ACBus {value.bus}")
                else:
                    q_limits = value.reactive_power_limits
                    ramp_limits = value.ramp_limits
                    time_limits = value.time_limits
                    q_min: float = -value.rating if q_limits is None else q_limits.min
                    q_max: float = value.rating if q_limits is None else q_limits.max
                    ramp_down: float = 1e20 if ramp_limits is None else ramp_limits.down
                    ramp_up: float = 1e20 if ramp_limits is None else ramp_limits.up
                    min_time_down: float = 0.0 if time_limits is None else time_limits.down
                    min_time_up: float = 0.0 if time_limits is None else time_limits.up
                    active: bool = value.available and value.status == SiennaOperationalStates.ONLINE
                    generator: dev.Generator = dev.Generator(
                        name=value.name, code=str(value.id), P=value.active_power, Q=value.reactive_power,
                        Pmin=value.active_power_limits.min, Pmax=value.active_power_limits.max,
                        Qmin=q_min, Qmax=q_max, Snom=value.rating, active=active, Sbase=value.base_power,
                        ramp_down=ramp_down, ramp_up=ramp_up, min_time_down=min_time_down,
                        min_time_up=min_time_up)
                    circuit.add_generator(bus=bus, api_obj=generator)
            else:
                raise ValueError("HydroTurbine bucket contains a non-HydroTurbine object")


def _convert_hydro_dispatch(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                            buses_by_id: dict[int, dev.Bus], circuit: MultiCircuit) -> None:
    """Convert hydro dispatch units into VeraGrid dispatchable generators.

    :param components: Remaining typed Sienna component buckets.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.HydroDispatch, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaHydroDispatch):
                bus: dev.Bus | None = buses_by_id.get(value.bus, None)
                if bus is None:
                    raise ValueError(f"HydroDispatch '{value.name}' references unknown ACBus {value.bus}")
                else:
                    q_limits = value.reactive_power_limits
                    ramp_limits = value.ramp_limits
                    time_limits = value.time_limits
                    q_min: float = -value.rating if q_limits is None else q_limits.min
                    q_max: float = value.rating if q_limits is None else q_limits.max
                    ramp_down: float = 1e20 if ramp_limits is None else ramp_limits.down
                    ramp_up: float = 1e20 if ramp_limits is None else ramp_limits.up
                    min_time_down: float = 0.0 if time_limits is None else time_limits.down
                    min_time_up: float = 0.0 if time_limits is None else time_limits.up
                    active: bool = value.available and value.status == SiennaOperationalStates.ONLINE
                    generator: dev.Generator = dev.Generator(
                        name=value.name, code=str(value.id), P=value.active_power, Q=value.reactive_power,
                        Pmin=value.active_power_limits.min, Pmax=value.active_power_limits.max,
                        Qmin=q_min, Qmax=q_max, Snom=value.rating, active=active, Sbase=value.base_power,
                        ramp_down=ramp_down, ramp_up=ramp_up, min_time_down=min_time_down,
                        min_time_up=min_time_up)
                    circuit.add_generator(bus=bus, api_obj=generator)
            else:
                raise ValueError("HydroDispatch bucket contains a non-HydroDispatch object")


def _convert_hydro_pump_turbines(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                                 buses_by_id: dict[int, dev.Bus], circuit: MultiCircuit) -> None:
    """Convert the present electrical state of hydro pump turbines into generators.

    :param components: Remaining typed Sienna component buckets.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.HydroPumpTurbine, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaHydroPumpTurbine):
                bus: dev.Bus | None = buses_by_id.get(value.bus, None)
                if bus is None:
                    raise ValueError(f"HydroPumpTurbine '{value.name}' references unknown ACBus {value.bus}")
                else:
                    q_limits = value.reactive_power_limits
                    ramp_limits = value.ramp_limits
                    time_limits = value.time_limits
                    q_min: float = -value.rating if q_limits is None else q_limits.min
                    q_max: float = value.rating if q_limits is None else q_limits.max
                    generator: dev.Generator = dev.Generator(
                        name=value.name, code=str(value.id), P=value.active_power, Q=value.reactive_power,
                        Pmin=value.active_power_limits.min, Pmax=value.active_power_limits.max,
                        Qmin=q_min, Qmax=q_max, Snom=value.rating,
                        active=value.available and value.status == SiennaOperationalStates.ONLINE,
                        Sbase=value.base_power, ramp_down=1e20 if ramp_limits is None else ramp_limits.down,
                        ramp_up=1e20 if ramp_limits is None else ramp_limits.up,
                        min_time_down=0.0 if time_limits is None else time_limits.down,
                        min_time_up=0.0 if time_limits is None else time_limits.up)
                    circuit.add_generator(bus=bus, api_obj=generator)
            else:
                raise ValueError("HydroPumpTurbine bucket contains a non-HydroPumpTurbine object")


def _convert_facts_control_devices(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                                   buses_by_id: dict[int, dev.Bus], circuit: MultiCircuit) -> None:
    """Convert FACTS shunt reactive-power state into a controllable shunt.

    :param components: Remaining typed Sienna component buckets.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.FACTSControlDevice, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaFACTSControlDevice):
                bus: dev.Bus | None = buses_by_id.get(value.bus, None)
                if bus is None:
                    raise ValueError(f"FACTSControlDevice '{value.name}' references unknown ACBus {value.bus}")
                else:
                    shunt: dev.ControllableShunt = dev.ControllableShunt(
                        name=value.name, code=str(value.id), B=value.reactive_power_required,
                        active=value.available)
                    circuit.add_controllable_shunt(bus=bus, api_obj=shunt)
            else:
                raise ValueError("FACTSControlDevice bucket contains a non-FACTSControlDevice object")


def _convert_discrete_controlled_ac_branches(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                                              arcs_by_id: dict[int, SiennaArc], buses_by_id: dict[int, dev.Bus],
                                              circuit: MultiCircuit) -> None:
    """Convert present-state discrete AC branches into VeraGrid lines.

    :param components: Remaining typed Sienna component buckets.
    :param arcs_by_id: Sienna arcs indexed by identifier.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.DiscreteControlledACBranch, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaDiscreteControlledACBranch):
                arc: SiennaArc | None = arcs_by_id.get(value.arc, None)
                if arc is None:
                    raise ValueError(f"DiscreteControlledACBranch '{value.name}' references unknown Arc {value.arc}")
                elif value.base_power != circuit.Sbase:
                    raise ValueError(f"DiscreteControlledACBranch '{value.name}' base_power differs from circuit base")
                else:
                    line: dev.Line = dev.Line(bus_from=buses_by_id[arc.from_id], bus_to=buses_by_id[arc.to_id],
                                              name=value.name, code=str(value.id), r=value.r, x=value.x,
                                              rate=value.rating, active=value.available)
                    circuit.add_line(obj=line)
            else:
                raise ValueError("DiscreteControlledACBranch bucket contains a non-DiscreteControlledACBranch object")


def _get_three_winding_terminal(circuit_value: SiennaTransformerCircuit, star_bus: int,
                                arcs_by_id: dict[int, SiennaArc], buses_by_id: dict[int, dev.Bus]) -> dev.Bus:
    """Resolve the terminal bus opposite a Sienna three-winding transformer's hidden star bus.

    :param circuit_value: One terminal-to-star transformer circuit.
    :param star_bus: Sienna hidden star-bus identifier.
    :param arcs_by_id: Sienna arcs indexed by identifier.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :return: Terminal VeraGrid bus.
    :raises ValueError: When the circuit does not join exactly one terminal to the star bus.
    """
    arc: SiennaArc | None = arcs_by_id.get(circuit_value.arc, None)
    if arc is None:
        raise ValueError(f"TransformerCircuit {circuit_value.id} references unknown Arc {circuit_value.arc}")
    elif arc.from_id == star_bus and arc.to_id in buses_by_id:
        return buses_by_id[arc.to_id]
    elif arc.to_id == star_bus and arc.from_id in buses_by_id:
        return buses_by_id[arc.from_id]
    else:
        raise ValueError(f"TransformerCircuit {circuit_value.id} must connect exactly one terminal to star bus {star_bus}")


def _convert_three_winding_transformers(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                                        arcs_by_id: dict[int, SiennaArc], buses_by_id: dict[int, dev.Bus],
                                        circuit: MultiCircuit) -> None:
    """Convert Sienna three-winding star equivalents into VeraGrid three-winding transformers.

    :param components: Remaining typed Sienna component buckets.
    :param arcs_by_id: Sienna arcs indexed by identifier.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.ThreeWindingTransformer, None)
    circuit_values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.TransformerCircuit, None)
    if values is None:
        pass
    elif circuit_values is None:
        raise ValueError("ThreeWindingTransformer requires TransformerCircuit components")
    else:
        circuits_by_id: dict[int, SiennaTransformerCircuit] = dict()
        for circuit_value in circuit_values:
            if isinstance(circuit_value, SiennaTransformerCircuit):
                circuits_by_id[circuit_value.id] = circuit_value
            else:
                raise ValueError("TransformerCircuit bucket contains a non-TransformerCircuit object")
        for value in values:
            if isinstance(value, SiennaThreeWindingTransformer):
                primary: SiennaTransformerCircuit | None = circuits_by_id.get(value.primary_circuit, None)
                secondary: SiennaTransformerCircuit | None = circuits_by_id.get(value.secondary_circuit, None)
                tertiary: SiennaTransformerCircuit | None = circuits_by_id.get(value.tertiary_circuit, None)
                if primary is None or secondary is None or tertiary is None:
                    raise ValueError(f"ThreeWindingTransformer '{value.name}' references an unknown TransformerCircuit")
                else:
                    r12: float = primary.r + secondary.r if value.r_12 is None else value.r_12
                    r23: float = secondary.r + tertiary.r if value.r_23 is None else value.r_23
                    r31: float = tertiary.r + primary.r if value.r_31 is None else value.r_31
                    x12: float = primary.x + secondary.x if value.x_12 is None else value.x_12
                    x23: float = secondary.x + tertiary.x if value.x_23 is None else value.x_23
                    x31: float = tertiary.x + primary.x if value.x_31 is None else value.x_31
                    transformer: dev.Transformer3W = dev.Transformer3W(
                        code=str(value.id), name=value.name,
                        bus1=_get_three_winding_terminal(primary, value.star_bus, arcs_by_id, buses_by_id),
                        bus2=_get_three_winding_terminal(secondary, value.star_bus, arcs_by_id, buses_by_id),
                        bus3=_get_three_winding_terminal(tertiary, value.star_bus, arcs_by_id, buses_by_id),
                        V1=primary.base_voltage_primary, V2=secondary.base_voltage_primary,
                        V3=tertiary.base_voltage_primary,
                        active=primary.available and secondary.available and tertiary.available,
                        r12=r12, r23=r23, r31=r31, x12=x12, x23=x23, x31=x31,
                        rate12=primary.rating, rate23=secondary.rating, rate31=tertiary.rating)
                    circuit.add_transformer3w(obj=transformer)
            else:
                raise ValueError("ThreeWindingTransformer bucket contains a non-ThreeWindingTransformer object")


def _convert_hybrid_systems(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                            buses_by_id: dict[int, dev.Bus], circuit: MultiCircuit) -> None:
    """Convert hybrid-system interconnection states into VeraGrid generators.

    :param components: Remaining typed Sienna component buckets.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.HybridSystem, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaHybridSystem):
                bus: dev.Bus | None = buses_by_id.get(value.bus, None)
                if bus is None:
                    raise ValueError(f"HybridSystem '{value.name}' references unknown ACBus {value.bus}")
                else:
                    p_limits = value.output_active_power_limits
                    q_limits = value.reactive_power_limits
                    generator: dev.Generator = dev.Generator(
                        name=value.name, code=str(value.id), P=value.active_power, Q=value.reactive_power,
                        Pmin=-value.input_active_power_limits.max, Pmax=p_limits.max,
                        Qmin=q_limits.min, Qmax=q_limits.max,
                        Snom=value.interconnection_rating if value.interconnection_rating is not None else p_limits.max,
                        active=value.available and value.status == SiennaOperationalStates.ONLINE,
                        Sbase=value.base_power)
                    circuit.add_generator(bus=bus, api_obj=generator)
            else:
                raise ValueError("HybridSystem bucket contains a non-HybridSystem object")


def _convert_interruptible_power_loads(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                                       buses_by_id: dict[int, dev.Bus], circuit: MultiCircuit) -> None:
    """Convert interruptible power loads at their declared operating point.

    :param components: Remaining typed Sienna component buckets.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.InterruptiblePowerLoad, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaInterruptiblePowerLoad):
                bus: dev.Bus | None = buses_by_id.get(value.bus, None)
                if bus is None:
                    raise ValueError(f"InterruptiblePowerLoad '{value.name}' references unknown ACBus {value.bus}")
                else:
                    load: dev.Load = dev.Load(name=value.name, code=str(value.id), P=value.active_power,
                                              Q=value.reactive_power, active=value.available)
                    circuit.add_load(bus=bus, api_obj=load)
            else:
                raise ValueError("InterruptiblePowerLoad bucket contains a non-InterruptiblePowerLoad object")


def _convert_interruptible_standard_loads(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                                          buses_by_id: dict[int, dev.Bus], circuit: MultiCircuit) -> None:
    """Convert interruptible ZIP loads at their nominal one-per-unit operating point.

    :param components: Remaining typed Sienna component buckets.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.InterruptibleStandardLoad, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaInterruptibleStandardLoad):
                bus: dev.Bus | None = buses_by_id.get(value.bus, None)
                if bus is None:
                    raise ValueError(f"InterruptibleStandardLoad '{value.name}' references unknown ACBus {value.bus}")
                else:
                    active_power: float = (value.constant_active_power + value.impedance_active_power
                                           + value.current_active_power)
                    reactive_power: float = (value.constant_reactive_power + value.impedance_reactive_power
                                             + value.current_reactive_power)
                    load: dev.Load = dev.Load(name=value.name, code=str(value.id), P=active_power,
                                              Q=reactive_power, active=value.available)
                    circuit.add_load(bus=bus, api_obj=load)
            else:
                raise ValueError("InterruptibleStandardLoad bucket contains a non-InterruptibleStandardLoad object")


def _convert_shiftable_power_loads(components: dict[SiennaObjectKind, list[SiennaSchemaModel]],
                                   buses_by_id: dict[int, dev.Bus], circuit: MultiCircuit) -> None:
    """Convert shiftable power loads at their declared operating point.

    :param components: Remaining typed Sienna component buckets.
    :param buses_by_id: VeraGrid buses indexed by Sienna identifier.
    :param circuit: Destination VeraGrid circuit.
    :return: None.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.ShiftablePowerLoad, None)
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaShiftablePowerLoad):
                bus: dev.Bus | None = buses_by_id.get(value.bus, None)
                if bus is None:
                    raise ValueError(f"ShiftablePowerLoad '{value.name}' references unknown ACBus {value.bus}")
                else:
                    load: dev.Load = dev.Load(name=value.name, code=str(value.id), P=value.active_power,
                                              Q=value.reactive_power, active=value.available)
                    circuit.add_load(bus=bus, api_obj=load)
            else:
                raise ValueError("ShiftablePowerLoad bucket contains a non-ShiftablePowerLoad object")


def _parse_ac_buses(components: dict[str, Any]) -> list[SiennaACBus]:
    """Parse the Sienna ACBus bucket into explicit bus objects.

    :param components: Raw Sienna components mapping.
    :return: Parsed AC buses.
    """
    component_data: Any | None = components.get("ACBus", list())
    if not isinstance(component_data, list):
        raise ValueError("Sienna component bucket 'ACBus' must be an array")
    else:
        buses: list[SiennaACBus] = list()
        for component in component_data:
            if not isinstance(component, dict):
                raise ValueError("Sienna component bucket 'ACBus' contains a non-object")
            else:
                buses.append(parse_sienna_ac_bus(component))
        return buses


def _parse_areas(components: dict[str, Any]) -> list[SiennaArea]:
    """Parse the Sienna Area bucket into explicit area objects.

    :param components: Raw Sienna components mapping.
    :return: Parsed areas.
    """
    component_data: Any | None = components.get("Area", list())
    if not isinstance(component_data, list):
        raise ValueError("Sienna component bucket 'Area' must be an array")
    else:
        areas: list[SiennaArea] = list()
        for component in component_data:
            if not isinstance(component, dict):
                raise ValueError("Sienna component bucket 'Area' contains a non-object")
            else:
                areas.append(parse_sienna_area(component))
        return areas


def _parse_load_zones(components: dict[str, Any]) -> list[SiennaLoadZone]:
    """Parse the Sienna LoadZone bucket into explicit load-zone objects.

    :param components: Raw Sienna components mapping.
    :return: Parsed load zones.
    """
    component_data: Any | None = components.get("LoadZone", list())
    if not isinstance(component_data, list):
        raise ValueError("Sienna component bucket 'LoadZone' must be an array")
    else:
        load_zones: list[SiennaLoadZone] = list()
        for component in component_data:
            if not isinstance(component, dict):
                raise ValueError("Sienna component bucket 'LoadZone' contains a non-object")
            else:
                load_zones.append(parse_sienna_load_zone(component))
        return load_zones


def _parse_dc_buses(components: dict[str, Any]) -> list[SiennaDCBus]:
    """Parse the Sienna DCBus bucket into explicit DC-bus objects.

    :param components: Raw Sienna components mapping.
    :return: Parsed DC buses.
    """
    component_data: Any | None = components.get("DCBus", list())
    if not isinstance(component_data, list):
        raise ValueError("Sienna component bucket 'DCBus' must be an array")
    else:
        dc_buses: list[SiennaDCBus] = list()
        for component in component_data:
            if not isinstance(component, dict):
                raise ValueError("Sienna component bucket 'DCBus' contains a non-object")
            else:
                dc_buses.append(parse_sienna_dc_bus(component))
        return dc_buses


def _parse_arcs(components: dict[str, Any]) -> list[SiennaArc]:
    """Parse the Sienna Arc bucket into explicit arc objects.

    :param components: Raw Sienna components mapping.
    :return: Parsed arcs.
    """
    component_data: Any | None = components.get("Arc", list())
    if not isinstance(component_data, list):
        raise ValueError("Sienna component bucket 'Arc' must be an array")
    else:
        arcs: list[SiennaArc] = list()
        for component in component_data:
            if not isinstance(component, dict):
                raise ValueError("Sienna component bucket 'Arc' contains a non-object")
            else:
                arcs.append(parse_sienna_arc(component))
        return arcs


def _parse_lines(components: dict[str, Any]) -> list[SiennaLine]:
    """Parse the Sienna Line bucket into explicit line objects.

    :param components: Raw Sienna components mapping.
    :return: Parsed lines.
    """
    component_data: Any | None = components.get("Line", list())
    if not isinstance(component_data, list):
        raise ValueError("Sienna component bucket 'Line' must be an array")
    else:
        lines: list[SiennaLine] = list()
        for component in component_data:
            if not isinstance(component, dict):
                raise ValueError("Sienna component bucket 'Line' contains a non-object")
            else:
                lines.append(parse_sienna_line(component))
        return lines


def _parse_power_loads(components: dict[str, Any]) -> list[SiennaPowerLoad]:
    """Parse the Sienna PowerLoad bucket into explicit load objects.

    :param components: Raw Sienna components mapping.
    :return: Parsed static loads.
    """
    component_data: Any | None = components.get("PowerLoad", list())
    if not isinstance(component_data, list):
        raise ValueError("Sienna component bucket 'PowerLoad' must be an array")
    else:
        power_loads: list[SiennaPowerLoad] = list()
        for component in component_data:
            if not isinstance(component, dict):
                raise ValueError("Sienna component bucket 'PowerLoad' contains a non-object")
            else:
                power_loads.append(parse_sienna_power_load(component))
        return power_loads


def _parse_fixed_admittances(components: dict[str, Any]) -> list[SiennaFixedAdmittance]:
    """Parse the Sienna FixedAdmittance bucket into explicit shunt objects.

    :param components: Raw Sienna components mapping.
    :return: Parsed fixed shunts.
    """
    component_data: Any | None = components.get("FixedAdmittance", list())
    if not isinstance(component_data, list):
        raise ValueError("Sienna component bucket 'FixedAdmittance' must be an array")
    else:
        fixed_admittances: list[SiennaFixedAdmittance] = list()
        for component in component_data:
            if not isinstance(component, dict):
                raise ValueError("Sienna component bucket 'FixedAdmittance' contains a non-object")
            else:
                fixed_admittances.append(parse_sienna_fixed_admittance(component))
        return fixed_admittances


def _parse_unmapped_components(components: dict[str, Any]) -> dict[SiennaObjectKind, list[SiennaSchemaModel]]:
    """Retain all non-converted SystemDocument component buckets losslessly.

    :param components: Raw Sienna components mapping.
    :return: Unmapped components indexed by their published Sienna kind.
    """
    mapped_types: set[str] = {"ACBus", "Arc", "Area", "DCBus", "FixedAdmittance", "Line", "LoadZone",
                              "PowerLoad"}
    parsed_components: dict[SiennaObjectKind, list[SiennaSchemaModel]] = dict()
    for component_type, component_values in components.items():
        if component_type not in mapped_types:
            kind: SiennaObjectKind = SiennaObjectKind(component_type)
            objects: list[SiennaSchemaModel] = list()
            if not isinstance(component_values, list):
                raise ValueError(f"Sienna component bucket '{component_type}' must be an array")
            else:
                for component_value in component_values:
                    if not isinstance(component_value, dict):
                        raise ValueError(f"Sienna component bucket '{component_type}' contains a non-object")
                    else:
                        objects.append(parse_sienna_schema_object(kind=kind, data=component_value))
            parsed_components[kind] = objects
        else:
            pass
    return parsed_components


def _validate_empty_association_tables(data: dict[str, Any]) -> None:
    """Reject unsupported associations and profile sidecars before conversion.

    :param data: Raw Sienna SystemDocument data.
    :return: None.
    :raises ValueError: When the document contains unsupported data that would be lost.
    """
    table_names: list[str] = ["supplemental_attributes", "supplemental_attribute_associations",
                              "plant_associations", "combined_cycle_associations", "service_associations",
                              "trading_hub_associations", "voltage_control_associations",
                              "time_series_associations"]
    for table_name in table_names:
        table_value: Any | None = data.get(table_name, list())
        if table_value != list():
            raise ValueError(f"Sienna '{table_name}' is not supported by this static-network adapter")
        else:
            pass
    sidecar_name: Any | None = data.get("time_series_storage_file", None)
    if sidecar_name is not None:
        raise ValueError("Sienna time_series_storage_file is not supported by this static-network adapter")
    else:
        pass


def _get_common_base_power(document: SiennaSystemDocument) -> float:
    """Select the shared base power required by VeraGrid's per-unit network model.

    :param document: Parsed Sienna SystemDocument.
    :return: Common base power in MVA.
    :raises ValueError: When component bases disagree.
    """
    base_powers: list[float] = list()
    for line in document.lines:
        base_powers.append(line.base_power)
    for area in document.areas:
        base_powers.append(area.base_power)
    for load_zone in document.load_zones:
        base_powers.append(load_zone.base_power)
    for power_load in document.power_loads:
        base_powers.append(power_load.base_power)
    for fixed_admittance in document.fixed_admittances:
        base_powers.append(fixed_admittance.base_power)
    if len(base_powers) == 0:
        return 100.0
    else:
        base_power: float = base_powers[0]
        for candidate_base_power in base_powers:
            if candidate_base_power != base_power:
                raise ValueError("Sienna component base_power values must match for VeraGrid conversion")
            else:
                pass
        return base_power


def _convert_bus(sienna_bus: SiennaACBus, areas_by_id: dict[int, dev.Area],
                 zones_by_id: dict[int, dev.Zone]) -> dev.Bus:
    """Convert one Sienna AC bus into its VeraGrid counterpart.

    :param sienna_bus: Parsed Sienna AC bus.
    :return: VeraGrid bus.
    """
    limits: SiennaMinMax | None = sienna_bus.voltage_limits
    vmin: float = 0.9 if limits is None else float(limits.min)
    vmax: float = 1.1 if limits is None else float(limits.max)
    is_slack: bool = sienna_bus.bus_type == "SLACK" or sienna_bus.bus_type == "REF"
    area: dev.Area | None = None
    zone: dev.Zone | None = None
    # Sienna uses integer references, which must resolve before the VeraGrid bus is constructed.
    if sienna_bus.area is not None:
        area = areas_by_id.get(sienna_bus.area, None)
        if area is None:
            raise ValueError(f"ACBus '{sienna_bus.name}' references unknown Area {sienna_bus.area}")
        else:
            pass
    else:
        pass
    if sienna_bus.load_zone is not None:
        zone = zones_by_id.get(sienna_bus.load_zone, None)
        if zone is None:
            raise ValueError(f"ACBus '{sienna_bus.name}' references unknown LoadZone {sienna_bus.load_zone}")
        else:
            pass
    else:
        pass
    return dev.Bus(name=sienna_bus.name, code=str(sienna_bus.identifier), area=area, zone=zone,
                   Vnom=10.0 if sienna_bus.base_voltage is None else sienna_bus.base_voltage,
                   vmin=vmin, vmax=vmax, Vm0=1.0 if sienna_bus.magnitude is None else sienna_bus.magnitude,
                   Va0=0.0 if sienna_bus.angle is None else sienna_bus.angle,
                   active=sienna_bus.available, is_slack=is_slack)


def _convert_dc_bus(sienna_bus: SiennaDCBus, areas_by_id: dict[int, dev.Area],
                    zones_by_id: dict[int, dev.Zone]) -> dev.Bus:
    """Convert one Sienna DC bus into its VeraGrid counterpart.

    :param sienna_bus: Parsed Sienna DC bus.
    :param areas_by_id: Converted areas by Sienna identifier.
    :param zones_by_id: Converted load zones by Sienna identifier.
    :return: VeraGrid DC bus.
    :raises ValueError: When referenced areas or load zones are absent.
    """
    area: dev.Area | None = None
    zone: dev.Zone | None = None
    limits: dict[str, float] | None = sienna_bus.voltage_limits
    if sienna_bus.area is not None:
        area = areas_by_id.get(sienna_bus.area, None)
        if area is None:
            raise ValueError(f"DCBus '{sienna_bus.name}' references unknown Area {sienna_bus.area}")
        else:
            pass
    else:
        pass
    if sienna_bus.load_zone is not None:
        zone = zones_by_id.get(sienna_bus.load_zone, None)
        if zone is None:
            raise ValueError(f"DCBus '{sienna_bus.name}' references unknown LoadZone {sienna_bus.load_zone}")
        else:
            pass
    else:
        pass
    return dev.Bus(name=sienna_bus.name, code=str(sienna_bus.identifier), area=area, zone=zone, is_dc=True,
                   Vnom=10.0 if sienna_bus.base_voltage is None else sienna_bus.base_voltage,
                   vmin=0.9 if limits is None else float(limits.min),
                   vmax=1.1 if limits is None else float(limits.max),
                   Vm0=1.0 if sienna_bus.magnitude is None else sienna_bus.magnitude,
                   active=sienna_bus.available)


def _get_three_winding_star_bus_ids(components: dict[SiennaObjectKind, list[SiennaSchemaModel]]) -> set[int]:
    """Collect hidden Sienna star-bus identifiers reserved by three-winding transformers.

    :param components: Typed Sienna component buckets.
    :return: Identifiers which must not become visible VeraGrid buses.
    :raises ValueError: When the three-winding bucket violates its declared type.
    """
    values: list[SiennaSchemaModel] | None = components.get(SiennaObjectKind.ThreeWindingTransformer, None)
    star_bus_ids: set[int] = set()
    if values is None:
        pass
    else:
        for value in values:
            if isinstance(value, SiennaThreeWindingTransformer):
                star_bus_ids.add(value.star_bus)
            else:
                raise ValueError("ThreeWindingTransformer bucket contains a non-ThreeWindingTransformer object")
    return star_bus_ids


def _validate_arc_buses(arc: SiennaArc, buses_by_id: dict[int, dev.Bus], hidden_star_bus_ids: set[int]) -> None:
    """Validate that both endpoints of one Sienna arc exist.

    :param arc: Sienna arc to validate.
    :param buses_by_id: Converted buses indexed by Sienna identifier.
    :param hidden_star_bus_ids: Transformer star buses created internally by VeraGrid.
    :return: None.
    :raises ValueError: When either endpoint is missing.
    """
    if arc.from_id not in buses_by_id and arc.from_id not in hidden_star_bus_ids:
        raise ValueError(f"Arc {arc.identifier} references unknown from_id {arc.from_id}")
    elif arc.to_id not in buses_by_id and arc.to_id not in hidden_star_bus_ids:
        raise ValueError(f"Arc {arc.identifier} references unknown to_id {arc.to_id}")
    else:
        pass
