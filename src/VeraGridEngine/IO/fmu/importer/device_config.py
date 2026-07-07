# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import VarPowerFlowReferenceType

from VeraGridEngine.IO.fmu.importer.bindings import FmuImportConfig
from VeraGridEngine.IO.fmu.importer.model_description import FmuInterfaceMode


class FmuCsDeviceConfigRecord:
    """Store the serialized configuration of one imported FMU CS device.

    :param domain: Runtime domain that will consume the FMU.
    :param fmu_path: Original FMU path.
    :param preferred_mode: Preferred FMI mode string.
    :param input_bindings: VeraGrid-to-FMU bindings.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param output_defaults: Default output values before the first FMU step.
    :param output_param_names: Runtime parameter variable names backing each output.
    :param extraction_root: Optional trusted extraction root.
    :param communication_step: Optional communication step.
    :param relative_tolerance: Optional FMI relative tolerance.
    :param debug_logging: Enable FMI debug logging.
    """

    __slots__ = (
        "domain",
        "fmu_path",
        "preferred_mode",
        "input_bindings",
        "output_bindings",
        "output_defaults",
        "output_param_names",
        "extraction_root",
        "communication_step",
        "relative_tolerance",
        "debug_logging",
    )

    def __init__(
        self,
        domain: Any,
        fmu_path: str,
        preferred_mode: str | None,
        input_bindings: tuple[Any, ...],
        output_bindings: tuple[Any, ...],
        output_defaults: dict[VarPowerFlowReferenceType, float],
        output_param_names: dict[VarPowerFlowReferenceType, str],
        extraction_root: str | None = None,
        communication_step: float | None = None,
        relative_tolerance: float | None = None,
        debug_logging: bool = False,
    ) -> None:
        """Store the serialized FMU CS device configuration.

        :return: None.
        """

        self.domain: Any = domain
        self.fmu_path: str = fmu_path
        self.preferred_mode: str | None = preferred_mode
        self.input_bindings: tuple[Any, ...] = input_bindings
        self.output_bindings: tuple[Any, ...] = output_bindings
        self.output_defaults: dict[VarPowerFlowReferenceType, float] = output_defaults
        self.output_param_names: dict[VarPowerFlowReferenceType, str] = output_param_names
        self.extraction_root: str | None = extraction_root
        self.communication_step: float | None = communication_step
        self.relative_tolerance: float | None = relative_tolerance
        self.debug_logging: bool = debug_logging


class FmuMeDeviceConfigRecord:
    """Store the serialized configuration of one imported FMU ME device.

    :param domain: Runtime domain that will consume the FMU.
    :param fmu_path: Original FMU path.
    :param preferred_mode: Preferred FMI mode string.
    :param input_bindings: VeraGrid-to-FMU bindings.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param output_defaults: Default output values before the first ME predictor step.
    :param output_param_names: Runtime parameter variable names backing each output.
    :param integration_method: Internal predictor method.
    :param extraction_root: Optional trusted extraction root.
    :param relative_tolerance: Optional FMI relative tolerance.
    :param debug_logging: Enable FMI debug logging.
    """

    __slots__ = (
        "domain",
        "fmu_path",
        "preferred_mode",
        "input_bindings",
        "output_bindings",
        "output_defaults",
        "output_param_names",
        "integration_method",
        "extraction_root",
        "relative_tolerance",
        "debug_logging",
    )

    def __init__(
        self,
        domain: Any,
        fmu_path: str,
        preferred_mode: str | None,
        input_bindings: tuple[Any, ...],
        output_bindings: tuple[Any, ...],
        output_defaults: dict[VarPowerFlowReferenceType, float],
        output_param_names: dict[VarPowerFlowReferenceType, str],
        integration_method: str,
        extraction_root: str | None = None,
        relative_tolerance: float | None = None,
        debug_logging: bool = False,
    ) -> None:
        """Store the serialized FMU ME device configuration.

        :return: None.
        """

        self.domain: Any = domain
        self.fmu_path: str = fmu_path
        self.preferred_mode: str | None = preferred_mode
        self.input_bindings: tuple[Any, ...] = input_bindings
        self.output_bindings: tuple[Any, ...] = output_bindings
        self.output_defaults: dict[VarPowerFlowReferenceType, float] = output_defaults
        self.output_param_names: dict[VarPowerFlowReferenceType, str] = output_param_names
        self.integration_method: str = integration_method
        self.extraction_root: str | None = extraction_root
        self.relative_tolerance: float | None = relative_tolerance
        self.debug_logging: bool = debug_logging


def _reference_to_text(reference: VarPowerFlowReferenceType) -> str:
    """Convert one VeraGrid power-flow reference enum into text.

    :param reference: VeraGrid reference enum.
    :return: Serialized enum value.
    """

    return reference.value


def _reference_from_text(value: str) -> VarPowerFlowReferenceType:
    """Restore one VeraGrid power-flow reference enum from text.

    :param value: Serialized enum value.
    :return: VeraGrid reference enum.
    """

    return VarPowerFlowReferenceType(value)


def _build_output_parameter_name(output_var_name: str) -> str:
    """
    Build the event-parameter variable name associated with one FMU output variable.

    :param output_var_name: Symbolic output variable name.
    :return: Event-parameter variable name.
    """

    if output_var_name.startswith("fmu_"):
        return output_var_name.replace("fmu_", "fmu_param_", 1)
    else:
        return f"fmu_param_{output_var_name}"


def dump_fmu_cs_device_config(record: FmuCsDeviceConfigRecord) -> str:
    """Serialize one imported FMU CS device configuration.

    :param record: Device configuration record.
    :return: JSON payload.
    """

    input_bindings_payload: list[dict[str, str]] = list()
    output_bindings_payload: list[dict[str, str]] = list()
    output_defaults_payload: dict[str, float] = dict()
    output_param_names_payload: dict[str, str] = dict()

    binding: Any
    for binding in record.input_bindings:
        input_bindings_payload.append(
            {
                "reference": _reference_to_text(binding.reference),
                "fmu_variable_name": binding.fmu_variable_name,
            }
        )

    for binding in record.output_bindings:
        output_bindings_payload.append(
            {
                "reference": _reference_to_text(binding.reference),
                "fmu_variable_name": binding.fmu_variable_name,
            }
        )

    reference: VarPowerFlowReferenceType
    for reference, value in record.output_defaults.items():
        output_defaults_payload[_reference_to_text(reference)] = float(value)

    for reference, value in record.output_param_names.items():
        output_param_names_payload[_reference_to_text(reference)] = value

    payload: dict[str, Any] = dict()
    payload["version"] = 1
    payload["domain"] = record.domain.value
    payload["fmu_path"] = record.fmu_path
    payload["preferred_mode"] = record.preferred_mode
    payload["input_bindings"] = input_bindings_payload
    payload["output_bindings"] = output_bindings_payload
    payload["output_defaults"] = output_defaults_payload
    payload["output_param_names"] = output_param_names_payload
    payload["extraction_root"] = record.extraction_root
    payload["communication_step"] = record.communication_step
    payload["relative_tolerance"] = record.relative_tolerance
    payload["debug_logging"] = record.debug_logging
    return json.dumps(payload, sort_keys=True)


def load_fmu_cs_device_config(data: str | None) -> FmuCsDeviceConfigRecord | None:
    """Deserialize one imported FMU CS device configuration.

    :param data: Serialized JSON payload.
    :return: Parsed configuration record when available.
    """

    if data is None:
        return None
    else:
        text: str = data.strip()
        if len(text) == 0:
            return None
        else:
            payload: dict[str, Any] = json.loads(text)
            if int(payload.get("version", 1)) != 1:
                raise ValueError(f"Unsupported FMU CS device config version: {payload.get('version')}")
            else:
                from VeraGridEngine.IO.fmu.importer.experimental_cs import FmuCsDomain, FmuRefBinding

                input_bindings: list[Any] = list()
                output_bindings: list[Any] = list()
                item: dict[str, Any]
                for item in payload.get("input_bindings", list()):
                    input_bindings.append(
                        FmuRefBinding(
                            reference=_reference_from_text(str(item["reference"])),
                            fmu_variable_name=str(item["fmu_variable_name"]),
                        )
                    )
                for item in payload.get("output_bindings", list()):
                    output_bindings.append(
                        FmuRefBinding(
                            reference=_reference_from_text(str(item["reference"])),
                            fmu_variable_name=str(item["fmu_variable_name"]),
                        )
                    )

                output_defaults: dict[VarPowerFlowReferenceType, float] = dict()
                output_param_names: dict[VarPowerFlowReferenceType, str] = dict()
                key: str
                for key, value in payload.get("output_defaults", dict()).items():
                    output_defaults[_reference_from_text(key)] = float(value)
                for key, value in payload.get("output_param_names", dict()).items():
                    output_param_names[_reference_from_text(key)] = str(value)

                return FmuCsDeviceConfigRecord(
                    domain=FmuCsDomain(str(payload["domain"])),
                    fmu_path=str(payload["fmu_path"]),
                    preferred_mode=payload.get("preferred_mode", None),
                    input_bindings=tuple(input_bindings),
                    output_bindings=tuple(output_bindings),
                    output_defaults=output_defaults,
                    output_param_names=output_param_names,
                    extraction_root=payload.get("extraction_root", None),
                    communication_step=payload.get("communication_step", None),
                    relative_tolerance=payload.get("relative_tolerance", None),
                    debug_logging=bool(payload.get("debug_logging", False)),
                )


def build_import_config_from_record(record: FmuCsDeviceConfigRecord) -> FmuImportConfig:
    """Build the runtime import config from one serialized device record.

    :param record: Stored FMU CS device record.
    :return: Runtime import configuration.
    """

    preferred_mode: FmuInterfaceMode | None
    if record.preferred_mode is None:
        preferred_mode = None
    else:
        preferred_mode = FmuInterfaceMode(record.preferred_mode)

    extraction_root: Path | None
    if record.extraction_root is None:
        extraction_root = None
    else:
        extraction_root = Path(record.extraction_root)

    return FmuImportConfig(
        fmu_path=Path(record.fmu_path),
        preferred_mode=preferred_mode,
        communication_step=record.communication_step,
        relative_tolerance=record.relative_tolerance,
        extraction_root=extraction_root,
        debug_logging=record.debug_logging,
    )


def build_record_from_device_arguments(
    domain: Any,
    config: FmuImportConfig,
    input_bindings: tuple[Any, ...],
    output_bindings: tuple[Any, ...],
    output_defaults: dict[VarPowerFlowReferenceType, float],
    block: Block,
) -> FmuCsDeviceConfigRecord:
    """Build a serializable FMU device record from runtime arguments.

    :param domain: Runtime domain consuming the FMU.
    :param config: Runtime import configuration.
    :param input_bindings: VeraGrid-to-FMU bindings.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param output_defaults: Default output values.
    :param block: Device block carrying the output parameter variables.
    :return: Serialized FMU device record.
    """

    output_param_names: dict[VarPowerFlowReferenceType, str] = dict()
    binding: Any
    for binding in output_bindings:
        output_var = block.external_mapping[binding.reference]
        event_parameter_name: str = _build_output_parameter_name(str(output_var.name))
        output_param_names[binding.reference] = event_parameter_name

    extraction_root_text: str | None
    if config.extraction_root is None:
        extraction_root_text = None
    else:
        extraction_root_text = str(config.extraction_root)

    preferred_mode_text: str | None
    if config.preferred_mode is None:
        preferred_mode_text = None
    else:
        preferred_mode_text = config.preferred_mode.value

    return FmuCsDeviceConfigRecord(
        domain=domain,
        fmu_path=str(config.fmu_path),
        preferred_mode=preferred_mode_text,
        input_bindings=input_bindings,
        output_bindings=output_bindings,
        output_defaults=dict(output_defaults),
        output_param_names=output_param_names,
        extraction_root=extraction_root_text,
        communication_step=config.communication_step,
        relative_tolerance=config.relative_tolerance,
        debug_logging=config.debug_logging,
    )


def restore_fmu_cs_spec_from_record(record: FmuCsDeviceConfigRecord, block: Block, device_tpe: Any) -> Any:
    """Rebuild the runtime FMU device specification from the stored record.

    :param record: Serialized FMU device record.
    :param block: Device block used in the active problem.
    :param device_tpe: VeraGrid device type.
    :return: Runtime FMU device specification.
    """

    from VeraGridEngine.IO.fmu.importer.experimental_cs import FmuCsDeviceSpec

    event_params_by_name: dict[str, Any] = dict()
    event_parameter: Any
    for event_parameter in block.event_dict.keys():
        event_params_by_name[event_parameter.name] = event_parameter

    output_param_uids: dict[VarPowerFlowReferenceType, int] = dict()
    reference: VarPowerFlowReferenceType
    for reference, parameter_name in record.output_param_names.items():
        event_parameter = event_params_by_name.get(parameter_name, None)
        if event_parameter is None:
            raise KeyError(parameter_name)
        else:
            output_param_uids[reference] = event_parameter.uid

    return FmuCsDeviceSpec(
        domain=record.domain,
        config=build_import_config_from_record(record),
        device_tpe=device_tpe,
        input_bindings=record.input_bindings,
        output_bindings=record.output_bindings,
        output_defaults=dict(record.output_defaults),
        output_param_uids=output_param_uids,
    )


def dump_fmu_me_device_config(record: FmuMeDeviceConfigRecord) -> str:
    """Serialize one imported FMU ME device configuration.

    :param record: Device configuration record.
    :return: JSON payload.
    """

    input_bindings_payload: list[dict[str, str]] = list()
    output_bindings_payload: list[dict[str, str]] = list()
    output_defaults_payload: dict[str, float] = dict()
    output_param_names_payload: dict[str, str] = dict()

    binding: Any
    for binding in record.input_bindings:
        input_bindings_payload.append(
            {
                "reference": _reference_to_text(binding.reference),
                "fmu_variable_name": binding.fmu_variable_name,
            }
        )

    for binding in record.output_bindings:
        output_bindings_payload.append(
            {
                "reference": _reference_to_text(binding.reference),
                "fmu_variable_name": binding.fmu_variable_name,
            }
        )

    reference: VarPowerFlowReferenceType
    for reference, value in record.output_defaults.items():
        output_defaults_payload[_reference_to_text(reference)] = float(value)
    for reference, value in record.output_param_names.items():
        output_param_names_payload[_reference_to_text(reference)] = value

    payload: dict[str, Any] = dict()
    payload["version"] = 1
    payload["domain"] = record.domain.value
    payload["fmu_path"] = record.fmu_path
    payload["preferred_mode"] = record.preferred_mode
    payload["input_bindings"] = input_bindings_payload
    payload["output_bindings"] = output_bindings_payload
    payload["output_defaults"] = output_defaults_payload
    payload["output_param_names"] = output_param_names_payload
    payload["integration_method"] = record.integration_method
    payload["extraction_root"] = record.extraction_root
    payload["relative_tolerance"] = record.relative_tolerance
    payload["debug_logging"] = record.debug_logging
    return json.dumps(payload, sort_keys=True)


def load_fmu_me_device_config(data: str | None) -> FmuMeDeviceConfigRecord | None:
    """Deserialize one imported FMU ME device configuration.

    :param data: Serialized JSON payload.
    :return: Parsed configuration record when available.
    """

    if data is None:
        return None
    else:
        text: str = data.strip()
        if len(text) == 0:
            return None
        else:
            payload: dict[str, Any] = json.loads(text)
            if int(payload.get("version", 1)) != 1:
                raise ValueError(f"Unsupported FMU ME device config version: {payload.get('version')}")
            else:
                from VeraGridEngine.IO.fmu.importer.experimental_cs import FmuRefBinding
                from VeraGridEngine.IO.fmu.importer.experimental_me import FmuMeDomain

                input_bindings: list[Any] = list()
                output_bindings: list[Any] = list()
                item: dict[str, Any]
                for item in payload.get("input_bindings", list()):
                    input_bindings.append(
                        FmuRefBinding(
                            reference=_reference_from_text(str(item["reference"])),
                            fmu_variable_name=str(item["fmu_variable_name"]),
                        )
                    )
                for item in payload.get("output_bindings", list()):
                    output_bindings.append(
                        FmuRefBinding(
                            reference=_reference_from_text(str(item["reference"])),
                            fmu_variable_name=str(item["fmu_variable_name"]),
                        )
                    )

                output_defaults: dict[VarPowerFlowReferenceType, float] = dict()
                output_param_names: dict[VarPowerFlowReferenceType, str] = dict()
                key: str
                for key, value in payload.get("output_defaults", dict()).items():
                    output_defaults[_reference_from_text(key)] = float(value)
                for key, value in payload.get("output_param_names", dict()).items():
                    output_param_names[_reference_from_text(key)] = str(value)

                return FmuMeDeviceConfigRecord(
                    domain=FmuMeDomain(str(payload["domain"])),
                    fmu_path=str(payload["fmu_path"]),
                    preferred_mode=payload.get("preferred_mode", None),
                    input_bindings=tuple(input_bindings),
                    output_bindings=tuple(output_bindings),
                    output_defaults=output_defaults,
                    output_param_names=output_param_names,
                    integration_method=str(payload["integration_method"]),
                    extraction_root=payload.get("extraction_root", None),
                    relative_tolerance=payload.get("relative_tolerance", None),
                    debug_logging=bool(payload.get("debug_logging", False)),
                )


def build_me_record_from_device_arguments(
    domain: Any,
    config: FmuImportConfig,
    input_bindings: tuple[Any, ...],
    output_bindings: tuple[Any, ...],
    output_defaults: dict[VarPowerFlowReferenceType, float],
    integration_method: str,
    block: Block,
) -> FmuMeDeviceConfigRecord:
    """Build a serializable FMU ME device record from runtime arguments.

    :param domain: Runtime domain consuming the FMU.
    :param config: Runtime import configuration.
    :param input_bindings: VeraGrid-to-FMU bindings.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param output_defaults: Default output values.
    :param integration_method: Internal ME predictor method.
    :param block: Device block carrying the output parameter variables.
    :return: Serialized FMU ME device record.
    """

    output_param_names: dict[VarPowerFlowReferenceType, str] = dict()
    binding: Any
    for binding in output_bindings:
        output_var = block.external_mapping[binding.reference]
        event_parameter_name: str = _build_output_parameter_name(str(output_var.name))
        output_param_names[binding.reference] = event_parameter_name

    extraction_root_text: str | None
    if config.extraction_root is None:
        extraction_root_text = None
    else:
        extraction_root_text = str(config.extraction_root)

    preferred_mode_text: str | None
    if config.preferred_mode is None:
        preferred_mode_text = None
    else:
        preferred_mode_text = config.preferred_mode.value

    return FmuMeDeviceConfigRecord(
        domain=domain,
        fmu_path=str(config.fmu_path),
        preferred_mode=preferred_mode_text,
        input_bindings=input_bindings,
        output_bindings=output_bindings,
        output_defaults=dict(output_defaults),
        output_param_names=output_param_names,
        integration_method=integration_method,
        extraction_root=extraction_root_text,
        relative_tolerance=config.relative_tolerance,
        debug_logging=config.debug_logging,
    )


def restore_fmu_me_spec_from_record(record: FmuMeDeviceConfigRecord, block: Block, device_tpe: Any) -> Any:
    """Rebuild the runtime FMU ME device specification from the stored record.

    :param record: Serialized FMU ME device record.
    :param block: Device block used in the active problem.
    :param device_tpe: VeraGrid device type.
    :return: Runtime FMU ME device specification.
    """

    from VeraGridEngine.IO.fmu.importer.experimental_me import FmuMeDomain, FmuMeIntegrationMethod, build_fmu_me_device_spec

    integration_method = FmuMeIntegrationMethod(record.integration_method)
    spec = build_fmu_me_device_spec(
        domain=FmuMeDomain(record.domain.value),
        config=build_import_config_from_record(
            FmuCsDeviceConfigRecord(
                domain=record.domain,
                fmu_path=record.fmu_path,
                preferred_mode=record.preferred_mode,
                input_bindings=record.input_bindings,
                output_bindings=record.output_bindings,
                output_defaults=record.output_defaults,
                output_param_names=record.output_param_names,
                extraction_root=record.extraction_root,
                communication_step=None,
                relative_tolerance=record.relative_tolerance,
                debug_logging=record.debug_logging,
            )
        ),
        device_tpe=device_tpe,
        input_variable_names=tuple(binding.fmu_variable_name for binding in record.input_bindings),
        output_variable_names=tuple(binding.fmu_variable_name for binding in record.output_bindings),
        integration_method=integration_method,
    )

    event_params_by_name: dict[str, Any] = dict()
    event_parameter: Any
    for event_parameter in block.event_dict.keys():
        event_params_by_name[event_parameter.name] = event_parameter
    output_param_uids: dict[VarPowerFlowReferenceType, int] = dict()
    reference: VarPowerFlowReferenceType
    for reference, parameter_name in record.output_param_names.items():
        event_parameter = event_params_by_name.get(parameter_name, None)
        if event_parameter is None:
            raise KeyError(parameter_name)
        else:
            output_param_uids[reference] = event_parameter.uid
    spec.output_param_uids = output_param_uids
    spec.output_defaults = dict(record.output_defaults)
    spec.input_bindings = record.input_bindings
    spec.output_bindings = record.output_bindings
    return spec
