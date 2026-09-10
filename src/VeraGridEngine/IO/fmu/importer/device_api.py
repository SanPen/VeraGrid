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
    FmuImportConfig,
    FmuRefBinding,
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
    :return: Copied RMS block attached to the device.
    """

    # The symbolic shell block is built first so the device owns a plain VeraGrid block.
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
    :return: Copied EMT block attached to the device.
    """

    # The symbolic shell block is built first so the device owns a plain VeraGrid block.
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
    :return: Copied RMS block attached to the device.
    """

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
    :return: Copied EMT block attached to the device.
    """

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
    )
    serialized_config: str = dump_fmu_me_device_config(record)

    # Preserve the ME provider before installing its restored consumer block.
    device.emt_fmu_me_import_config = serialized_config
    # EMT templates still carry API mappings with `None` sentinels, so we attach the shell directly.
    device.emt_model = template.block
    return device.emt_model
