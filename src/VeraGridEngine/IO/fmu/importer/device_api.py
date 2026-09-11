# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block

from VeraGridEngine.IO.fmu.importer.bindings import (
    FmiThreeFloat64ConfigurationValue,
    FmiThreeUInt64ConfigurationValue,
    FmuFloat64ParameterValue,
    FmuImportConfig,
    FmuRefBinding,
    FmuVariableBinding,
    _validate_fmu_float64_parameter_values,
)
from VeraGridEngine.IO.fmu.importer.device_config import (
    build_me_record_from_device_arguments,
    build_record_from_device_arguments,
    dump_fmu_cs_device_config,
    dump_fmu_me_device_config,
)
from VeraGridEngine.IO.fmu.importer.co_simulation import FmuCsDomain, build_emt_fmu_cs_injection_template, build_rms_fmu_cs_injection_template
from VeraGridEngine.IO.fmu.importer.model_exchange import FmuMeDomain, build_emt_fmu_me_injection_template, build_rms_fmu_me_injection_template
from VeraGridEngine.IO.fmu.importer.runtime_worker_host import (
    FmiThreeWorkerHostLimits,
)
from VeraGridEngine.IO.fmu.importer.model_description import (
    FmuModelDescription,
    read_fmu_model_description,
)
from VeraGridEngine.IO.fmu.importer.template_api import append_fmu_parameter_entries


def _validate_attachment_parameter_values(
    metadata: FmuModelDescription,
    input_bindings: tuple[FmuRefBinding, ...],
    configuration_float64_values: tuple[
        FmiThreeFloat64ConfigurationValue, ...
    ],
    configuration_uint64_values: tuple[
        FmiThreeUInt64ConfigurationValue, ...
    ],
    parameter_values: tuple[FmuFloat64ParameterValue, ...],
) -> None:
    """Validate attachment parameters before building a symbolic shell.

    :param metadata: Authoritative FMU model description.
    :param input_bindings: Inputs unavailable to normal parameters.
    :param configuration_float64_values: Structural Float64 declarations.
    :param configuration_uint64_values: Structural UInt64 declarations.
    :param parameter_values: Requested scalar normal-parameter values.
    :return: None.
    """

    reserved_names: list[str] = [""] * (
        len(input_bindings)
        + len(configuration_float64_values)
        + len(configuration_uint64_values)
    )
    reserved_index: int = 0
    input_binding: FmuRefBinding
    for input_binding in input_bindings:
        reserved_names[reserved_index] = input_binding.fmu_variable_name
        reserved_index += 1
    float64_configuration: FmiThreeFloat64ConfigurationValue
    for float64_configuration in configuration_float64_values:
        reserved_names[reserved_index] = float64_configuration.variable_name
        reserved_index += 1
    uint64_configuration: FmiThreeUInt64ConfigurationValue
    for uint64_configuration in configuration_uint64_values:
        reserved_names[reserved_index] = uint64_configuration.variable_name
        reserved_index += 1
    _validate_fmu_float64_parameter_values(
        parameter_values=parameter_values,
        metadata=metadata,
        reserved_variable_names=tuple(reserved_names),
    )


def attach_rms_fmu_cs_device(
    device: Any,
    vfactory: VarFactory,
    config: FmuImportConfig,
    input_bindings: tuple[FmuRefBinding, ...],
    output_bindings: tuple[FmuRefBinding, ...],
    name: str,
    output_defaults: dict[Any, float] | None = None,
    worker_limits: FmiThreeWorkerHostLimits | None = None,
    configuration_float64_values: tuple[
        FmiThreeFloat64ConfigurationValue, ...
    ] = tuple(),
    configuration_uint64_values: tuple[
        FmiThreeUInt64ConfigurationValue, ...
    ] = tuple(),
    parameter_values: tuple[FmuFloat64ParameterValue, ...] = tuple(),
) -> Block:
    """Attach one imported FMU CS device to the RMS model of a VeraGrid device.

    :param device: VeraGrid device receiving the imported FMU.
    :param vfactory: Variable factory used by the owning grid.
    :param config: FMU runtime configuration.
    :param input_bindings: VeraGrid-to-FMU bindings.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param name: Template name.
    :param output_defaults: Default output values before the first FMU step.
    :param worker_limits: Explicit FMI 3 worker supervision policy, when used.
    :param configuration_float64_values: Structural Float64 declarations.
    :param configuration_uint64_values: Structural UInt64 declarations.
    :param parameter_values: Scalar FMI parameter values overriding metadata starts.
    :return: Copied RMS block attached to the device.
    """

    metadata: FmuModelDescription = read_fmu_model_description(config.fmu_path)
    _validate_attachment_parameter_values(
        metadata=metadata,
        input_bindings=input_bindings,
        configuration_float64_values=configuration_float64_values,
        configuration_uint64_values=configuration_uint64_values,
        parameter_values=parameter_values,
    )
    # The symbolic shell block is built only after all parameter source data is valid.
    template = build_rms_fmu_cs_injection_template(
        vfactory=vfactory,
        config=config,
        input_bindings=input_bindings,
        output_bindings=output_bindings,
        name=name,
        device_tpe=device.device_type,
        output_defaults=output_defaults,
        worker_limits=worker_limits,
    )
    parameter_bindings: tuple[FmuVariableBinding, ...] = (
        append_fmu_parameter_entries(
            block=template.block,
            vfactory=vfactory,
            metadata=metadata,
            parameter_values=parameter_values,
        )
    )
    # Build the complete provider record before changing the destination device.
    defaults: dict[Any, float]
    if output_defaults is None:
        defaults = dict()
    else:
        defaults = dict(output_defaults)
    record = build_record_from_device_arguments(
        domain=FmuCsDomain.RMS,
        config=config,
        input_bindings=input_bindings,
        output_bindings=output_bindings,
        output_defaults=defaults,
        block=template.block,
        worker_limits=worker_limits,
        configuration_float64_values=configuration_float64_values,
        configuration_uint64_values=configuration_uint64_values,
        parameter_bindings=parameter_bindings,
    )
    serialized_config: str = dump_fmu_cs_device_config(record)

    # Persist the provider first so a consumer block is never installed without
    # the declarative data required to restore its runtime configuration.
    device.rms_fmu_import_config = serialized_config
    device.rms_model = template.block.copy()
    return device.rms_model


def attach_emt_fmu_cs_device(
    device: Any,
    vfactory: VarFactory,
    config: FmuImportConfig,
    input_bindings: tuple[FmuRefBinding, ...],
    output_bindings: tuple[FmuRefBinding, ...],
    name: str,
    output_defaults: dict[Any, float] | None = None,
    worker_limits: FmiThreeWorkerHostLimits | None = None,
    configuration_float64_values: tuple[
        FmiThreeFloat64ConfigurationValue, ...
    ] = tuple(),
    configuration_uint64_values: tuple[
        FmiThreeUInt64ConfigurationValue, ...
    ] = tuple(),
    parameter_values: tuple[FmuFloat64ParameterValue, ...] = tuple(),
) -> Block:
    """Attach one imported FMU CS device to the EMT model of a VeraGrid device.

    :param device: VeraGrid device receiving the imported FMU.
    :param vfactory: Variable factory used by the owning grid.
    :param config: FMU runtime configuration.
    :param input_bindings: VeraGrid-to-FMU bindings.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param name: Template name.
    :param output_defaults: Default output values before the first FMU step.
    :param worker_limits: Explicit FMI 3 worker supervision policy, when used.
    :param configuration_float64_values: Structural Float64 declarations.
    :param configuration_uint64_values: Structural UInt64 declarations.
    :param parameter_values: Scalar FMI parameter values overriding metadata starts.
    :return: Copied EMT block attached to the device.
    """

    metadata: FmuModelDescription = read_fmu_model_description(config.fmu_path)
    _validate_attachment_parameter_values(
        metadata=metadata,
        input_bindings=input_bindings,
        configuration_float64_values=configuration_float64_values,
        configuration_uint64_values=configuration_uint64_values,
        parameter_values=parameter_values,
    )
    # The symbolic shell block is built only after all parameter source data is valid.
    template = build_emt_fmu_cs_injection_template(
        vfactory=vfactory,
        config=config,
        input_bindings=input_bindings,
        output_bindings=output_bindings,
        name=name,
        device_tpe=device.device_type,
        output_defaults=output_defaults,
        worker_limits=worker_limits,
    )
    parameter_bindings: tuple[FmuVariableBinding, ...] = (
        append_fmu_parameter_entries(
            block=template.block,
            vfactory=vfactory,
            metadata=metadata,
            parameter_values=parameter_values,
        )
    )
    # Build the complete provider record before changing the destination device.
    defaults: dict[Any, float]
    if output_defaults is None:
        defaults = dict()
    else:
        defaults = dict(output_defaults)
    record = build_record_from_device_arguments(
        domain=FmuCsDomain.EMT,
        config=config,
        input_bindings=input_bindings,
        output_bindings=output_bindings,
        output_defaults=defaults,
        block=template.block,
        worker_limits=worker_limits,
        configuration_float64_values=configuration_float64_values,
        configuration_uint64_values=configuration_uint64_values,
        parameter_bindings=parameter_bindings,
    )
    serialized_config: str = dump_fmu_cs_device_config(record)

    # Persist the provider before the EMT shell becomes a numerical consumer.
    device.emt_fmu_import_config = serialized_config
    # EMT templates still carry API mappings with `None` sentinels, so we attach the shell directly.
    device.emt_model = template.block
    return device.emt_model


def attach_rms_fmu_me_device(
    device: Any,
    vfactory: VarFactory,
    config: FmuImportConfig,
    input_bindings: tuple[FmuRefBinding, ...],
    output_bindings: tuple[FmuRefBinding, ...],
    name: str,
    output_defaults: dict[Any, float] | None = None,
    worker_limits: FmiThreeWorkerHostLimits | None = None,
    maximum_event_iterations: int = 32,
    configuration_float64_values: tuple[
        FmiThreeFloat64ConfigurationValue, ...
    ] = tuple(),
    configuration_uint64_values: tuple[
        FmiThreeUInt64ConfigurationValue, ...
    ] = tuple(),
    parameter_values: tuple[FmuFloat64ParameterValue, ...] = tuple(),
) -> Block:
    """Attach one imported FMU ME device to the RMS model of a VeraGrid device.

    :param device: VeraGrid device receiving the imported FMU.
    :param vfactory: Variable factory used by the owning grid.
    :param config: FMU runtime configuration.
    :param input_bindings: VeraGrid-to-FMU bindings.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param name: Template name.
    :param output_defaults: Default output values before the first FMU step.
    :param worker_limits: Explicit FMI 3 worker supervision policy, when used.
    :param maximum_event_iterations: Positive Event Mode convergence bound.
    :param configuration_float64_values: Structural Float64 declarations.
    :param configuration_uint64_values: Structural UInt64 declarations.
    :param parameter_values: Scalar FMI parameter values overriding metadata starts.
    :return: Copied RMS block attached to the device.
    """

    metadata: FmuModelDescription = read_fmu_model_description(config.fmu_path)
    _validate_attachment_parameter_values(
        metadata=metadata,
        input_bindings=input_bindings,
        configuration_float64_values=configuration_float64_values,
        configuration_uint64_values=configuration_uint64_values,
        parameter_values=parameter_values,
    )
    template = build_rms_fmu_me_injection_template(
        vfactory=vfactory,
        config=config,
        input_bindings=input_bindings,
        output_bindings=output_bindings,
        name=name,
        device_tpe=device.device_type,
        output_defaults=output_defaults,
        worker_limits=worker_limits,
        maximum_event_iterations=maximum_event_iterations,
    )
    parameter_bindings: tuple[FmuVariableBinding, ...] = (
        append_fmu_parameter_entries(
            block=template.block,
            vfactory=vfactory,
            metadata=metadata,
            parameter_values=parameter_values,
        )
    )
    defaults: dict[Any, float]
    if output_defaults is None:
        defaults = dict()
    else:
        defaults = dict(output_defaults)
    record = build_me_record_from_device_arguments(
        domain=FmuMeDomain.RMS,
        config=config,
        input_bindings=input_bindings,
        output_bindings=output_bindings,
        output_defaults=defaults,
        block=template.block,
        worker_limits=worker_limits,
        maximum_event_iterations=maximum_event_iterations,
        configuration_float64_values=configuration_float64_values,
        configuration_uint64_values=configuration_uint64_values,
        parameter_bindings=parameter_bindings,
    )
    serialized_config: str = dump_fmu_me_device_config(record)

    # Preserve the ME provider before installing its restored consumer block.
    device.rms_fmu_me_import_config = serialized_config
    device.rms_model = template.block.copy()
    return device.rms_model


def attach_emt_fmu_me_device(
    device: Any,
    vfactory: VarFactory,
    config: FmuImportConfig,
    input_bindings: tuple[FmuRefBinding, ...],
    output_bindings: tuple[FmuRefBinding, ...],
    name: str,
    output_defaults: dict[Any, float] | None = None,
    worker_limits: FmiThreeWorkerHostLimits | None = None,
    maximum_event_iterations: int = 32,
    configuration_float64_values: tuple[
        FmiThreeFloat64ConfigurationValue, ...
    ] = tuple(),
    configuration_uint64_values: tuple[
        FmiThreeUInt64ConfigurationValue, ...
    ] = tuple(),
    parameter_values: tuple[FmuFloat64ParameterValue, ...] = tuple(),
) -> Block:
    """Attach one imported FMU ME device to the EMT model of a VeraGrid device.

    :param device: VeraGrid device receiving the imported FMU.
    :param vfactory: Variable factory used by the owning grid.
    :param config: FMU runtime configuration.
    :param input_bindings: VeraGrid-to-FMU bindings.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param name: Template name.
    :param output_defaults: Default output values before the first FMU step.
    :param worker_limits: Explicit FMI 3 worker supervision policy, when used.
    :param maximum_event_iterations: Positive Event Mode convergence bound.
    :param configuration_float64_values: Structural Float64 declarations.
    :param configuration_uint64_values: Structural UInt64 declarations.
    :param parameter_values: Scalar FMI parameter values overriding metadata starts.
    :return: Copied EMT block attached to the device.
    """

    metadata: FmuModelDescription = read_fmu_model_description(config.fmu_path)
    _validate_attachment_parameter_values(
        metadata=metadata,
        input_bindings=input_bindings,
        configuration_float64_values=configuration_float64_values,
        configuration_uint64_values=configuration_uint64_values,
        parameter_values=parameter_values,
    )
    template = build_emt_fmu_me_injection_template(
        vfactory=vfactory,
        config=config,
        input_bindings=input_bindings,
        output_bindings=output_bindings,
        name=name,
        device_tpe=device.device_type,
        output_defaults=output_defaults,
        worker_limits=worker_limits,
        maximum_event_iterations=maximum_event_iterations,
    )
    parameter_bindings: tuple[FmuVariableBinding, ...] = (
        append_fmu_parameter_entries(
            block=template.block,
            vfactory=vfactory,
            metadata=metadata,
            parameter_values=parameter_values,
        )
    )
    defaults: dict[Any, float]
    if output_defaults is None:
        defaults = dict()
    else:
        defaults = dict(output_defaults)
    record = build_me_record_from_device_arguments(
        domain=FmuMeDomain.EMT,
        config=config,
        input_bindings=input_bindings,
        output_bindings=output_bindings,
        output_defaults=defaults,
        block=template.block,
        worker_limits=worker_limits,
        maximum_event_iterations=maximum_event_iterations,
        configuration_float64_values=configuration_float64_values,
        configuration_uint64_values=configuration_uint64_values,
        parameter_bindings=parameter_bindings,
    )
    serialized_config: str = dump_fmu_me_device_config(record)

    # Preserve the ME provider before installing its restored consumer block.
    device.emt_fmu_me_import_config = serialized_config
    # EMT templates still carry API mappings with `None` sentinels, so we attach the shell directly.
    device.emt_model = template.block
    return device.emt_model
