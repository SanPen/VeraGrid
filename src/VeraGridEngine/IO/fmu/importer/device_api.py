# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block

from VeraGridEngine.IO.fmu.importer.bindings import FmuImportConfig
from VeraGridEngine.IO.fmu.importer.device_config import (
    build_me_record_from_device_arguments,
    build_record_from_device_arguments,
    dump_fmu_cs_device_config,
    dump_fmu_me_device_config,
)
from VeraGridEngine.IO.fmu.importer.experimental_cs import FmuCsDomain, FmuRefBinding, build_emt_fmu_cs_injection_template, build_rms_fmu_cs_injection_template
from VeraGridEngine.IO.fmu.importer.experimental_me import FmuMeDomain, FmuMeIntegrationMethod, build_emt_fmu_me_injection_template, build_rms_fmu_me_injection_template


def attach_rms_fmu_cs_device(
    device: Any,
    vfactory: VarFactory,
    config: FmuImportConfig,
    input_bindings: tuple[FmuRefBinding, ...],
    output_bindings: tuple[FmuRefBinding, ...],
    name: str,
    output_defaults: dict[Any, float] | None = None,
) -> Block:
    """Attach one imported FMU CS device to the RMS model of a VeraGrid device.

    :param device: VeraGrid device receiving the imported FMU.
    :param vfactory: Variable factory used by the owning grid.
    :param config: FMU runtime configuration.
    :param input_bindings: VeraGrid-to-FMU bindings.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param name: Template name.
    :param output_defaults: Default output values before the first FMU step.
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
    )
    device.rms_model = template.block.copy()

    # The runtime FMU configuration is then serialized on the device for later reconstruction.
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
    )
    device.rms_fmu_import_config = dump_fmu_cs_device_config(record)
    return device.rms_model


def attach_emt_fmu_cs_device(
    device: Any,
    vfactory: VarFactory,
    config: FmuImportConfig,
    input_bindings: tuple[FmuRefBinding, ...],
    output_bindings: tuple[FmuRefBinding, ...],
    name: str,
    output_defaults: dict[Any, float] | None = None,
) -> Block:
    """Attach one imported FMU CS device to the EMT model of a VeraGrid device.

    :param device: VeraGrid device receiving the imported FMU.
    :param vfactory: Variable factory used by the owning grid.
    :param config: FMU runtime configuration.
    :param input_bindings: VeraGrid-to-FMU bindings.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param name: Template name.
    :param output_defaults: Default output values before the first FMU step.
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
    )
    # EMT templates still carry API mappings with `None` sentinels, so we attach the shell directly.
    device.emt_model = template.block

    # The runtime FMU configuration is then serialized on the device for later reconstruction.
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
    )
    device.emt_fmu_import_config = dump_fmu_cs_device_config(record)
    return device.emt_model


def attach_rms_fmu_me_device(
    device: Any,
    vfactory: VarFactory,
    config: FmuImportConfig,
    input_bindings: tuple[FmuRefBinding, ...],
    output_bindings: tuple[FmuRefBinding, ...],
    name: str,
    output_defaults: dict[Any, float] | None = None,
    integration_method: FmuMeIntegrationMethod = FmuMeIntegrationMethod.EXPLICIT_EULER,
) -> Block:
    """Attach one imported FMU ME device to the RMS model of a VeraGrid device.

    :param device: VeraGrid device receiving the imported FMU.
    :param vfactory: Variable factory used by the owning grid.
    :param config: FMU runtime configuration.
    :param input_bindings: VeraGrid-to-FMU bindings.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param name: Template name.
    :param output_defaults: Default output values before the first FMU step.
    :param integration_method: Internal ME predictor method.
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
        integration_method=integration_method,
    )
    device.rms_model = template.block.copy()

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
        integration_method=integration_method.value,
        block=template.block,
    )
    device.rms_fmu_me_import_config = dump_fmu_me_device_config(record)
    return device.rms_model


def attach_emt_fmu_me_device(
    device: Any,
    vfactory: VarFactory,
    config: FmuImportConfig,
    input_bindings: tuple[FmuRefBinding, ...],
    output_bindings: tuple[FmuRefBinding, ...],
    name: str,
    output_defaults: dict[Any, float] | None = None,
    integration_method: FmuMeIntegrationMethod = FmuMeIntegrationMethod.EXPLICIT_EULER,
) -> Block:
    """Attach one imported FMU ME device to the EMT model of a VeraGrid device.

    :param device: VeraGrid device receiving the imported FMU.
    :param vfactory: Variable factory used by the owning grid.
    :param config: FMU runtime configuration.
    :param input_bindings: VeraGrid-to-FMU bindings.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param name: Template name.
    :param output_defaults: Default output values before the first FMU step.
    :param integration_method: Internal ME predictor method.
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
        integration_method=integration_method,
    )
    # EMT templates still carry API mappings with `None` sentinels, so we attach the shell directly.
    device.emt_model = template.block

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
        integration_method=integration_method.value,
        block=template.block,
    )
    device.emt_fmu_me_import_config = dump_fmu_me_device_config(record)
    return device.emt_model
