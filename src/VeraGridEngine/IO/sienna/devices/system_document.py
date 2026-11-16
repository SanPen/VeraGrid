# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Sienna SystemDocument object and JSON conversion helpers."""

from __future__ import annotations

from typing import Any

from VeraGridEngine.IO.sienna.devices.core.topology.ac_bus import SiennaACBus
from VeraGridEngine.IO.sienna.devices.core.topology.area import SiennaArea
from VeraGridEngine.IO.sienna.devices.core.topology.arc import SiennaArc
from VeraGridEngine.IO.sienna.devices.core.topology.dc_bus import SiennaDCBus
from VeraGridEngine.IO.sienna.devices.operations.static_injection.fixed_admittance import SiennaFixedAdmittance
from VeraGridEngine.IO.sienna.devices.operations.branch.line import SiennaLine
from VeraGridEngine.IO.sienna.devices.core.topology.load_zone import SiennaLoadZone
from VeraGridEngine.IO.sienna.devices.operations.static_injection.power_load import SiennaPowerLoad
from VeraGridEngine.IO.sienna.devices.core.associations.supplemental_attribute_association import SiennaSupplementalAttributeAssociation
from VeraGridEngine.IO.sienna.devices.operations.associations.plant_association import SiennaPlantAssociation
from VeraGridEngine.IO.sienna.devices.operations.associations.combined_cycle_association import SiennaCombinedCycleAssociation
from VeraGridEngine.IO.sienna.devices.operations.associations.service_association import SiennaServiceAssociation
from VeraGridEngine.IO.sienna.devices.operations.associations.trading_hub_association import SiennaTradingHubAssociation
from VeraGridEngine.IO.sienna.devices.operations.associations.voltage_control_association import SiennaVoltageControlAssociation
from VeraGridEngine.IO.sienna.devices.time_series.time_series_association import SiennaTimeSeriesAssociation
from VeraGridEngine.IO.sienna.devices.enums import SiennaSchemaVersion
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaObjectKind, SiennaSchemaModel
from VeraGridEngine.IO.sienna.devices.writer_registry import write_sienna_schema_object, write_sienna_schema_union
from VeraGridEngine.IO.sienna.devices.core.associations.supplemental_attribute_association import sienna_supplemental_attribute_association_to_json
from VeraGridEngine.IO.sienna.devices.operations.associations.plant_association import sienna_plant_association_to_json
from VeraGridEngine.IO.sienna.devices.operations.associations.combined_cycle_association import sienna_combined_cycle_association_to_json
from VeraGridEngine.IO.sienna.devices.operations.associations.service_association import sienna_service_association_to_json
from VeraGridEngine.IO.sienna.devices.operations.associations.trading_hub_association import sienna_trading_hub_association_to_json
from VeraGridEngine.IO.sienna.devices.operations.associations.voltage_control_association import sienna_voltage_control_association_to_json
from VeraGridEngine.IO.sienna.devices.time_series.time_series_association import sienna_time_series_association_to_json


class SiennaSystemDocument:
    """Represent the supported static-network subset of a Sienna SystemDocument."""

    __slots__ = ("schema_version", "name", "description", "frequency", "components", "areas", "load_zones", "buses",
                 "dc_buses", "arcs", "lines", "power_loads", "fixed_admittances", "supplemental_attributes",
                 "supplemental_attribute_associations", "plant_associations", "combined_cycle_associations",
                 "service_associations", "trading_hub_associations", "voltage_control_associations",
                 "time_series_associations", "ext", "time_series_storage_file", "unmapped_components")

    def __init__(self, schema_version: SiennaSchemaVersion, name: str | None, frequency: float | None,
                 areas: list[SiennaArea], load_zones: list[SiennaLoadZone], buses: list[SiennaACBus],
                 dc_buses: list[SiennaDCBus], arcs: list[SiennaArc], lines: list[SiennaLine],
                 power_loads: list[SiennaPowerLoad], fixed_admittances: list[SiennaFixedAdmittance],
                 unmapped_components: dict[SiennaObjectKind, list[SiennaSchemaModel]], description: str | None = None,
                 supplemental_attributes: list[SiennaSchemaModel] | None = None,
                 supplemental_attribute_associations: list[SiennaSupplementalAttributeAssociation] | None = None,
                 plant_associations: list[SiennaPlantAssociation] | None = None,
                 combined_cycle_associations: list[SiennaCombinedCycleAssociation] | None = None,
                 service_associations: list[SiennaServiceAssociation] | None = None,
                 trading_hub_associations: list[SiennaTradingHubAssociation] | None = None,
                 voltage_control_associations: list[SiennaVoltageControlAssociation] | None = None,
                 time_series_associations: list[SiennaTimeSeriesAssociation] | None = None,
                 ext: dict[str, dict[str, object]] | None = None,
                 time_series_storage_file: str | None = None) -> None:
        """Store validated Sienna components.

        :param schema_version: Declared Sienna schema version.
        :param name: Optional system name.
        :param frequency: Optional nominal frequency in Hz.
        :param areas: Sienna areas.
        :param load_zones: Sienna load zones.
        :param buses: Sienna AC buses.
        :param dc_buses: Sienna DC buses.
        :param arcs: Sienna topology arcs.
        :param lines: Sienna AC lines.
        :param power_loads: Sienna static loads.
        :param fixed_admittances: Sienna fixed shunts.
        :param unmapped_components: Other supported Sienna component buckets retained losslessly.
        :return: None.
        """
        self.schema_version: SiennaSchemaVersion = schema_version
        self.name: str | None = name
        self.description: str | None = description
        self.frequency: float | None = frequency
        self.components: dict[str, list[SiennaSchemaModel]] = dict()
        self.components["ACBus"] = list(buses)
        self.components["Arc"] = list(arcs)
        self.components["Area"] = list(areas)
        self.components["DCBus"] = list(dc_buses)
        self.components["FixedAdmittance"] = list(fixed_admittances)
        self.components["Line"] = list(lines)
        self.components["LoadZone"] = list(load_zones)
        self.components["PowerLoad"] = list(power_loads)
        for component_kind, component_values in unmapped_components.items():
            self.components[component_kind.value] = list(component_values)
        self.areas: list[SiennaArea] = areas
        self.load_zones: list[SiennaLoadZone] = load_zones
        self.buses: list[SiennaACBus] = buses
        self.dc_buses: list[SiennaDCBus] = dc_buses
        self.arcs: list[SiennaArc] = arcs
        self.lines: list[SiennaLine] = lines
        self.power_loads: list[SiennaPowerLoad] = power_loads
        self.fixed_admittances: list[SiennaFixedAdmittance] = fixed_admittances
        self.supplemental_attributes: list[SiennaSchemaModel] = list() if supplemental_attributes is None else supplemental_attributes
        self.supplemental_attribute_associations: list[SiennaSupplementalAttributeAssociation] = (list() if supplemental_attribute_associations is None else supplemental_attribute_associations)
        self.plant_associations: list[SiennaPlantAssociation] = list() if plant_associations is None else plant_associations
        self.combined_cycle_associations: list[SiennaCombinedCycleAssociation] = (list() if combined_cycle_associations is None else combined_cycle_associations)
        self.service_associations: list[SiennaServiceAssociation] = list() if service_associations is None else service_associations
        self.trading_hub_associations: list[SiennaTradingHubAssociation] = (list() if trading_hub_associations is None else trading_hub_associations)
        self.voltage_control_associations: list[SiennaVoltageControlAssociation] = (list() if voltage_control_associations is None else voltage_control_associations)
        self.time_series_associations: list[SiennaTimeSeriesAssociation] = (list() if time_series_associations is None else time_series_associations)
        self.ext: dict[str, dict[str, object]] = dict() if ext is None else ext
        self.time_series_storage_file: str | None = time_series_storage_file
        self.unmapped_components: dict[SiennaObjectKind, list[SiennaSchemaModel]] = unmapped_components


def create_empty_document_components() -> dict[str, list[dict[str, Any]]]:
    """Create the typed component buckets in deterministic order.

    :return: Empty Sienna component buckets.
    """
    return {"ACBus": list(), "Arc": list(), "Area": list(), "DCBus": list(), "FixedAdmittance": list(),
            "Line": list(), "LoadZone": list(), "PowerLoad": list()}


def sienna_system_document_to_json(value: SiennaSystemDocument) -> dict[str, Any]:
    """Write every declared SystemDocument slot using the fixed Sienna writer registry.

    :param value: Typed Sienna SystemDocument.
    :return: JSON-ready v0.4 SystemDocument object.
    """
    components: dict[str, list[dict[str, Any]]] = dict()
    for kind_name, component_values in value.components.items():
        kind: SiennaObjectKind = SiennaObjectKind(kind_name)
        encoded_values: list[dict[str, Any]] = list()
        for component_value in component_values:
            encoded_values.append(write_sienna_schema_object(kind=kind, value=component_value))
        components[kind_name] = encoded_values
    supplemental_kinds: list[SiennaObjectKind] = list()
    for association in value.supplemental_attribute_associations:
        kind: SiennaObjectKind = SiennaObjectKind(association.attribute_type)
        if kind not in supplemental_kinds:
            supplemental_kinds.append(kind)
        else:
            pass
    encoded_supplemental_attributes: list[dict[str, Any]] = list()
    for attribute in value.supplemental_attributes:
        encoded_supplemental_attributes.append(write_sienna_schema_union(tuple(supplemental_kinds), attribute))
    return {"schema_version": value.schema_version.value, "name": value.name, "description": value.description,
            "frequency": value.frequency, "components": components,
            "supplemental_attributes": encoded_supplemental_attributes,
            "supplemental_attribute_associations": [sienna_supplemental_attribute_association_to_json(item) for item in value.supplemental_attribute_associations],
            "plant_associations": [sienna_plant_association_to_json(item) for item in value.plant_associations],
            "combined_cycle_associations": [sienna_combined_cycle_association_to_json(item) for item in value.combined_cycle_associations],
            "service_associations": [sienna_service_association_to_json(item) for item in value.service_associations],
            "trading_hub_associations": [sienna_trading_hub_association_to_json(item) for item in value.trading_hub_associations],
            "voltage_control_associations": [sienna_voltage_control_association_to_json(item) for item in value.voltage_control_associations],
            "time_series_associations": [sienna_time_series_association_to_json(item) for item in value.time_series_associations],
            "ext": value.ext, "time_series_storage_file": value.time_series_storage_file}
