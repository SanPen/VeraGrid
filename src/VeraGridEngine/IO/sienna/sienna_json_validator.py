# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Standard-library validation for the supported Sienna v0.4 interchange subset."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from VeraGridEngine.IO.sienna.devices.enums import SiennaImpedanceUnitBasis, SiennaSchemaVersion, SiennaUnitSystem
from VeraGridEngine.IO.sienna.devices.format_version import resolve_sienna_format_version


class SiennaJsonValidator:
    """Validate the Sienna records this adapter can convert without external packages."""

    __slots__ = ("schema_directory",)

    def __init__(self, schema_directory: Path) -> None:
        """Store the selected schema root for provenance.

        :param schema_directory: Root directory of the pinned SiennaSchemas checkout.
        :return: None.
        """
        self.schema_directory: Path = schema_directory

    def validate(self, document: dict[str, Any]) -> None:
        """Validate every document field the first adapter reads or writes.

        :param document: Parsed Sienna SystemDocument object.
        :return: None.
        :raises ValueError: When the document is outside the supported subset.
        """
        if not self.schema_directory.is_dir():
            raise ValueError(f"Sienna schema directory does not exist: {self.schema_directory}")
        else:
            pass
        schema_version: str = _string(document, "schema_version", "SystemDocument")
        resolve_sienna_format_version(schema_version)
        frequency: Any | None = document.get("frequency", None)
        if frequency is not None and not _number(frequency):
            raise ValueError("SystemDocument frequency must be a number when provided")
        else:
            pass
        _validate_empty_tables(document)
        components: dict[str, Any] = _object(document, "components", "SystemDocument")
        _validate_component_buckets(components)


def _validate_empty_tables(document: dict[str, Any]) -> None:
    """Reject tables and profile storage this static adapter cannot preserve.

    :param document: Parsed Sienna SystemDocument object.
    :return: None.
    :raises ValueError: When unsupported data would be discarded.
    """
    table_names: list[str] = ["supplemental_attributes", "supplemental_attribute_associations",
                              "plant_associations", "combined_cycle_associations", "service_associations",
                              "trading_hub_associations", "voltage_control_associations",
                              "time_series_associations"]
    for table_name in table_names:
        table_value: Any | None = document.get(table_name, None)
        if table_value != list():
            raise ValueError(f"Sienna '{table_name}' must be an empty array for this static adapter")
        else:
            pass
    storage_file: Any | None = document.get("time_series_storage_file", None)
    if storage_file is not None:
        raise ValueError("Sienna time_series_storage_file must be null for this static adapter")
    else:
        pass


def _validate_component_buckets(components: dict[str, Any]) -> None:
    """Validate supported component buckets before component construction.

    :param components: Sienna component buckets.
    :return: None.
    :raises ValueError: When a bucket or component is unsupported or malformed.
    """
    supported_types: set[str] = {"ACBus", "AGC", "Arc", "Area", "AreaInterchange", "BilateralTransaction",
                                 "DCBus", "DiscreteControlledACBranch", "EnergyReservoirStorage",
                                 "ExponentialLoad", "FACTSControlDevice", "FixedAdmittance",
                                 "GenericArcImpedance", "GroupReserve", "HybridSystem", "HydroDispatch",
                                 "HydroPumpTurbine", "HydroReservoir", "HydroTurbine", "InterconnectingConverter",
                                 "InterruptiblePowerLoad", "InterruptibleStandardLoad", "Line", "LoadZone",
                                 "MotorLoad", "OfflineReserve", "OnlineReserve", "PointToPointBid", "PowerLoad",
                                 "RenewableDispatch", "RenewableNonDispatch", "SeriesCompensator",
                                 "ShiftablePowerLoad", "Source", "StandardLoad", "SwitchedAdmittance",
                                 "SynchronousCondenser", "TModelHVDCLine", "ThermalMultiStart",
                                 "ThermalStandard", "ThreeWindingTransformer", "TradingHub", "TransformerCircuit",
                                 "TransmissionInterface", "TwoTerminalGenericHVDCLine", "TwoTerminalLCCLine",
                                 "TwoTerminalVSCLine", "TwoWindingTransformer", "VirtualParticipant"}
    for component_type, items in components.items():
        if component_type not in supported_types:
            raise ValueError(f"Unsupported Sienna component type '{component_type}'")
        elif not isinstance(items, list):
            raise ValueError(f"Sienna component bucket '{component_type}' must be an array")
        else:
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    raise ValueError(f"{component_type}[{index}] must be an object")
                elif component_type == "ACBus":
                    _validate_ac_bus(item, index)
                elif component_type == "Arc":
                    _validate_arc(item, index)
                elif component_type == "Area":
                    _validate_area(item, index)
                elif component_type == "DCBus":
                    _validate_dc_bus(item, index)
                elif component_type == "FixedAdmittance":
                    _validate_fixed_admittance(item, index)
                elif component_type == "Line":
                    _validate_line(item, index)
                elif component_type == "LoadZone":
                    _validate_load_zone(item, index)
                elif component_type == "PowerLoad":
                    _validate_power_load(item, index)
                else:
                    pass


def _validate_ac_bus(data: dict[str, Any], index: int) -> None:
    """Validate one Sienna AC bus record.

    :param data: Raw Sienna ACBus record.
    :param index: Bucket position for diagnostics.
    :return: None.
    """
    label: str = f"ACBus[{index}]"
    _positive_integer(data, "id", label)
    _string(data, "name", label)
    _boolean(data, "available", label)
    _positive_integer(data, "number", label)
    _optional_number(data, "base_voltage", label)
    _optional_number(data, "magnitude", label)
    _optional_number(data, "angle", label)
    _optional_min_max(data, "voltage_limits", label)
    _optional_positive_integer(data, "area", label)
    _optional_positive_integer(data, "load_zone", label)


def _validate_area(data: dict[str, Any], index: int) -> None:
    """Validate one Sienna Area record.

    :param data: Raw Sienna Area record.
    :param index: Bucket position for diagnostics.
    :return: None.
    """
    label: str = f"Area[{index}]"
    _positive_integer(data, "id", label)
    _string(data, "name", label)
    _positive_number(data, "base_power", label)
    _string(data, "power_units", label)


def _validate_dc_bus(data: dict[str, Any], index: int) -> None:
    """Validate one Sienna DCBus record.

    :param data: Raw Sienna DCBus record.
    :param index: Bucket position for diagnostics.
    :return: None.
    """
    label: str = f"DCBus[{index}]"
    _positive_integer(data, "id", label)
    _string(data, "name", label)
    _boolean(data, "available", label)
    _number_property(data, "number", label)
    _optional_number(data, "base_voltage", label)
    _optional_number(data, "magnitude", label)
    _optional_min_max(data, "voltage_limits", label)
    _optional_positive_integer(data, "area", label)
    _optional_positive_integer(data, "load_zone", label)


def _validate_arc(data: dict[str, Any], index: int) -> None:
    """Validate one Sienna directed arc record.

    :param data: Raw Sienna Arc record.
    :param index: Bucket position for diagnostics.
    :return: None.
    """
    label: str = f"Arc[{index}]"
    _positive_integer(data, "id", label)
    _positive_integer(data, "from_id", label)
    _positive_integer(data, "to_id", label)


def _validate_fixed_admittance(data: dict[str, Any], index: int) -> None:
    """Validate one component-MVAr Sienna fixed shunt.

    :param data: Raw Sienna fixed-admittance record.
    :param index: Bucket position for diagnostics.
    :return: None.
    """
    label: str = f"FixedAdmittance[{index}]"
    _positive_integer(data, "id", label)
    _string(data, "name", label)
    _boolean(data, "available", label)
    _positive_integer(data, "bus", label)
    _positive_number(data, "base_power", label)
    admittance: dict[str, Any] = _object(data, "Y", label)
    _number_property(admittance, "real", f"{label} Y")
    _number_property(admittance, "imag", f"{label} Y")
    unit_basis: Any | None = data.get("admittance_units", "COMPONENT_MVAR")
    if unit_basis != "COMPONENT_MVAR":
        raise ValueError(f"{label} admittance_units must be COMPONENT_MVAR")
    else:
        pass


def _validate_line(data: dict[str, Any], index: int) -> None:
    """Validate one component-base-pu Sienna line record.

    :param data: Raw Sienna Line record.
    :param index: Bucket position for diagnostics.
    :return: None.
    """
    label: str = f"Line[{index}]"
    _positive_integer(data, "id", label)
    _string(data, "name", label)
    _boolean(data, "available", label)
    _positive_integer(data, "arc", label)
    _number_property(data, "r", label)
    _number_property(data, "x", label)
    _positive_number(data, "base_power", label)
    _number_property(data, "rating", label)
    _number_property(data, "active_power_flow", label)
    _number_property(data, "reactive_power_flow", label)
    _min_max(data, "angle_limits", label)
    _optional_from_to(data, "b", label)
    _optional_from_to(data, "g", label)
    power_units: str = _string(data, "power_units", label)
    parameter_units: str = str(data.get("parameter_units", SiennaImpedanceUnitBasis.COMPONENT_BASE.value))
    if power_units != SiennaUnitSystem.NATURAL_UNITS.value:
        raise ValueError(f"{label} power_units must be NATURAL_UNITS")
    elif parameter_units != SiennaImpedanceUnitBasis.COMPONENT_BASE.value:
        raise ValueError(f"{label} parameter_units must be COMPONENT_BASE")
    else:
        pass


def _validate_load_zone(data: dict[str, Any], index: int) -> None:
    """Validate one Sienna LoadZone record.

    :param data: Raw Sienna LoadZone record.
    :param index: Bucket position for diagnostics.
    :return: None.
    """
    label: str = f"LoadZone[{index}]"
    _positive_integer(data, "id", label)
    _string(data, "name", label)
    _number_property(data, "peak_active_power", label)
    _number_property(data, "peak_reactive_power", label)
    _positive_number(data, "base_power", label)
    _string(data, "power_units", label)


def _validate_power_load(data: dict[str, Any], index: int) -> None:
    """Validate one natural-unit Sienna static power-load record.

    :param data: Raw Sienna PowerLoad record.
    :param index: Bucket position for diagnostics.
    :return: None.
    """
    label: str = f"PowerLoad[{index}]"
    _positive_integer(data, "id", label)
    _string(data, "name", label)
    _boolean(data, "available", label)
    _positive_integer(data, "bus", label)
    _number_property(data, "active_power", label)
    _number_property(data, "reactive_power", label)
    _positive_number(data, "base_power", label)
    _number_property(data, "max_active_power", label)
    _number_property(data, "max_reactive_power", label)
    power_units: str = _string(data, "power_units", label)
    if power_units != SiennaUnitSystem.NATURAL_UNITS.value:
        raise ValueError(f"{label} power_units must be NATURAL_UNITS")
    else:
        pass


def _object(data: dict[str, Any], key: str, label: str) -> dict[str, Any]:
    """Read one required JSON object property.

    :param data: Raw JSON object.
    :param key: Required property name.
    :param label: Parent diagnostic label.
    :return: Object property.
    """
    value: Any | None = data.get(key, None)
    if not isinstance(value, dict):
        raise ValueError(f"{label} property '{key}' must be an object")
    else:
        return value


def _string(data: dict[str, Any], key: str, label: str) -> str:
    """Read one required JSON string property.

    :param data: Raw JSON object.
    :param key: Required property name.
    :param label: Parent diagnostic label.
    :return: String property.
    """
    value: Any | None = data.get(key, None)
    if not isinstance(value, str):
        raise ValueError(f"{label} property '{key}' must be a string")
    else:
        return value


def _boolean(data: dict[str, Any], key: str, label: str) -> bool:
    """Read one required JSON Boolean property.

    :param data: Raw JSON object.
    :param key: Required property name.
    :param label: Parent diagnostic label.
    :return: Boolean property.
    """
    value: Any | None = data.get(key, None)
    if not isinstance(value, bool):
        raise ValueError(f"{label} property '{key}' must be a boolean")
    else:
        return value


def _positive_integer(data: dict[str, Any], key: str, label: str) -> int:
    """Read one required positive JSON integer property.

    :param data: Raw JSON object.
    :param key: Required property name.
    :param label: Parent diagnostic label.
    :return: Positive integer property.
    """
    value: Any | None = data.get(key, None)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{label} property '{key}' must be a positive integer")
    else:
        return value


def _number_property(data: dict[str, Any], key: str, label: str) -> float:
    """Read one required JSON numeric property.

    :param data: Raw JSON object.
    :param key: Required property name.
    :param label: Parent diagnostic label.
    :return: Numeric property.
    """
    value: Any | None = data.get(key, None)
    if not _number(value):
        raise ValueError(f"{label} property '{key}' must be a number")
    else:
        return float(value)


def _positive_number(data: dict[str, Any], key: str, label: str) -> float:
    """Read one required positive JSON numeric property.

    :param data: Raw JSON object.
    :param key: Required property name.
    :param label: Parent diagnostic label.
    :return: Positive numeric property.
    """
    value: float = _number_property(data, key, label)
    if value <= 0.0:
        raise ValueError(f"{label} property '{key}' must be greater than zero")
    else:
        return value


def _optional_number(data: dict[str, Any], key: str, label: str) -> None:
    """Validate one optional numeric property.

    :param data: Raw JSON object.
    :param key: Optional property name.
    :param label: Parent diagnostic label.
    :return: None.
    """
    value: Any | None = data.get(key, None)
    if value is None or _number(value):
        pass
    else:
        raise ValueError(f"{label} property '{key}' must be a number when provided")


def _optional_positive_integer(data: dict[str, Any], key: str, label: str) -> None:
    """Validate one optional positive integer property.

    :param data: Raw JSON object.
    :param key: Optional property name.
    :param label: Parent diagnostic label.
    :return: None.
    """
    value: Any | None = data.get(key, None)
    if value is None:
        pass
    elif isinstance(value, int) and not isinstance(value, bool) and value > 0:
        pass
    else:
        raise ValueError(f"{label} property '{key}' must be a positive integer when provided")


def _optional_min_max(data: dict[str, Any], key: str, label: str) -> None:
    """Validate one optional Sienna min/max object.

    :param data: Raw JSON object.
    :param key: Optional property name.
    :param label: Parent diagnostic label.
    :return: None.
    """
    value: Any | None = data.get(key, None)
    if value is None:
        pass
    elif isinstance(value, dict):
        _min_max(data, key, label)
    else:
        raise ValueError(f"{label} property '{key}' must be an object when provided")


def _min_max(data: dict[str, Any], key: str, label: str) -> None:
    """Validate one required Sienna min/max object.

    :param data: Raw JSON object.
    :param key: Required property name.
    :param label: Parent diagnostic label.
    :return: None.
    """
    value: dict[str, Any] = _object(data, key, label)
    minimum: float = _number_property(value, "min", f"{label}.{key}")
    maximum: float = _number_property(value, "max", f"{label}.{key}")
    if minimum > maximum:
        raise ValueError(f"{label} property '{key}' has min greater than max")
    else:
        pass


def _optional_from_to(data: dict[str, Any], key: str, label: str) -> None:
    """Validate one optional Sienna from/to shunt pair.

    :param data: Raw JSON object.
    :param key: Optional property name.
    :param label: Parent diagnostic label.
    :return: None.
    """
    value: Any | None = data.get(key, None)
    if value is None:
        pass
    elif isinstance(value, dict):
        _number_property(value, "from", f"{label}.{key}")
        _number_property(value, "to", f"{label}.{key}")
    else:
        raise ValueError(f"{label} property '{key}' must be an object when provided")


def _number(value: Any) -> bool:
    """Return whether a JSON value is numeric and not Boolean.

    :param value: JSON value to inspect.
    :return: ``True`` for JSON numeric values.
    """
    return isinstance(value, int | float) and not isinstance(value, bool)
