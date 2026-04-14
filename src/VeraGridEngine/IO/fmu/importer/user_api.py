# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import VarPowerFlowRefferenceType

from VeraGridEngine.IO.fmu.importer.bindings import FmuImportConfig
from VeraGridEngine.IO.fmu.importer.device_api import (
    attach_emt_fmu_cs_device,
    attach_emt_fmu_me_device,
    attach_rms_fmu_cs_device,
    attach_rms_fmu_me_device,
)
from VeraGridEngine.IO.fmu.importer.experimental_cs import FmuRefBinding
from VeraGridEngine.IO.fmu.importer.experimental_me import FmuMeIntegrationMethod
from VeraGridEngine.IO.fmu.importer.model_description import FmuInterfaceMode


class FmuDeviceDomain(str, Enum):
    """Enumerate the VeraGrid domains where an imported FMU device can be attached.

    :return: None.
    """

    RMS = "rms"
    EMT = "emt"


class FmuReferenceValue:
    """Store one default numeric value associated with a VeraGrid reference.

    :param reference: VeraGrid external reference.
    :param value: Default numeric value.
    """

    __slots__ = ("reference", "value")

    def __init__(self, reference: VarPowerFlowRefferenceType, value: float) -> None:
        """Store one FMU default output value.

        :return: None.
        """

        self.reference: VarPowerFlowRefferenceType = reference
        self.value: float = float(value)


class FmuDeviceAttachmentRequest:
    """Store the high-level script configuration required to attach one FMU device.

    :param fmu_path: Path to the imported FMU archive.
    :param domain: VeraGrid domain where the FMU will be used.
    :param mode: FMI execution mode requested by the user.
    :param input_bindings: VeraGrid-to-FMU bindings.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param name: Optional template name.
    :param output_defaults: Default outputs before the first FMU step.
    :param extraction_root: Optional trusted FMU extraction root.
    :param communication_step: Optional FMI communication step.
    :param relative_tolerance: Optional FMI relative tolerance.
    :param debug_logging: Enable FMI debug logging.
    :param integration_method: Internal ME predictor method.
    """

    __slots__ = (
        "fmu_path",
        "domain",
        "mode",
        "input_bindings",
        "output_bindings",
        "name",
        "output_defaults",
        "extraction_root",
        "communication_step",
        "relative_tolerance",
        "debug_logging",
        "integration_method",
    )

    def __init__(
        self,
        fmu_path: str | Path,
        domain: FmuDeviceDomain,
        mode: FmuInterfaceMode,
        input_bindings: tuple[FmuRefBinding, ...],
        output_bindings: tuple[FmuRefBinding, ...],
        name: str | None = None,
        output_defaults: tuple[FmuReferenceValue, ...] = tuple(),
        extraction_root: str | Path | None = None,
        communication_step: float | None = None,
        relative_tolerance: float | None = None,
        debug_logging: bool = False,
        integration_method: FmuMeIntegrationMethod = FmuMeIntegrationMethod.EXPLICIT_EULER,
    ) -> None:
        """Store the high-level user request for one imported FMU device.

        :return: None.
        """

        self.fmu_path: Path = Path(fmu_path).expanduser()
        self.domain: FmuDeviceDomain = domain
        self.mode: FmuInterfaceMode = mode
        self.input_bindings: tuple[FmuRefBinding, ...] = input_bindings
        self.output_bindings: tuple[FmuRefBinding, ...] = output_bindings
        self.name: str | None = name
        self.output_defaults: tuple[FmuReferenceValue, ...] = output_defaults
        if extraction_root is None:
            self.extraction_root: Path | None = None
        else:
            self.extraction_root = Path(extraction_root).expanduser()
        self.communication_step: float | None = communication_step
        self.relative_tolerance: float | None = relative_tolerance
        self.debug_logging: bool = bool(debug_logging)
        self.integration_method: FmuMeIntegrationMethod = integration_method


def _build_import_config_from_request(request: FmuDeviceAttachmentRequest) -> FmuImportConfig:
    """Translate the high-level user request into the low-level runtime config.

    :param request: High-level FMU attachment request.
    :return: Low-level FMU runtime configuration.
    """

    return FmuImportConfig(
        fmu_path=request.fmu_path,
        preferred_mode=request.mode,
        communication_step=request.communication_step,
        relative_tolerance=request.relative_tolerance,
        extraction_root=request.extraction_root,
        debug_logging=request.debug_logging,
    )


def _build_output_defaults(request: FmuDeviceAttachmentRequest) -> dict[VarPowerFlowRefferenceType, float]:
    """Translate the user default-output collection into the internal mapping.

    :param request: High-level FMU attachment request.
    :return: Internal default-output mapping.
    """

    output_defaults: dict[VarPowerFlowRefferenceType, float] = dict()
    entry: FmuReferenceValue
    for entry in request.output_defaults:
        output_defaults[entry.reference] = entry.value
    return output_defaults


def _build_template_name(device: Any, request: FmuDeviceAttachmentRequest) -> str:
    """Choose a deterministic template name for the FMU shell block.

    :param device: VeraGrid device receiving the FMU.
    :param request: High-level FMU attachment request.
    :return: Template name used for the symbolic shell block.
    """

    if request.name is None:
        base_name: str = str(device.name).replace(" ", "_")
        mode_name: str = request.mode.value.lower()
        return f"{base_name}_{request.domain.value}_{mode_name}_fmu"
    else:
        return request.name


def attach_fmu_to_device(device: Any, grid: Any, request: FmuDeviceAttachmentRequest) -> Block:
    """Attach one imported FMU device to a VeraGrid device from a script-friendly request.

    :param device: VeraGrid device receiving the FMU.
    :param grid: VeraGrid grid owning the device and the variable factories.
    :param request: High-level FMU attachment request.
    :return: Attached symbolic shell block.
    """

    config: FmuImportConfig = _build_import_config_from_request(request)
    output_defaults: dict[VarPowerFlowRefferenceType, float] = _build_output_defaults(request)
    template_name: str = _build_template_name(device, request)

    # The helper dispatches to the low-level attachment function matching the selected domain and FMI mode.
    if request.domain == FmuDeviceDomain.RMS:
        if request.mode == FmuInterfaceMode.CO_SIMULATION:
            return attach_rms_fmu_cs_device(
                device=device,
                vfactory=grid.var_factory,
                config=config,
                input_bindings=request.input_bindings,
                output_bindings=request.output_bindings,
                name=template_name,
                output_defaults=output_defaults,
            )
        else:
            if request.mode == FmuInterfaceMode.MODEL_EXCHANGE:
                return attach_rms_fmu_me_device(
                    device=device,
                    vfactory=grid.var_factory,
                    config=config,
                    input_bindings=request.input_bindings,
                    output_bindings=request.output_bindings,
                    name=template_name,
                    output_defaults=output_defaults,
                    integration_method=request.integration_method,
                )
            else:
                raise ValueError(f"Unsupported FMI mode {request.mode.value}")
    else:
        if request.domain == FmuDeviceDomain.EMT:
            if request.mode == FmuInterfaceMode.CO_SIMULATION:
                return attach_emt_fmu_cs_device(
                    device=device,
                    vfactory=grid.var_factory,
                    config=config,
                    input_bindings=request.input_bindings,
                    output_bindings=request.output_bindings,
                    name=template_name,
                    output_defaults=output_defaults,
                )
            else:
                if request.mode == FmuInterfaceMode.MODEL_EXCHANGE:
                    return attach_emt_fmu_me_device(
                        device=device,
                        vfactory=grid.var_factory,
                        config=config,
                        input_bindings=request.input_bindings,
                        output_bindings=request.output_bindings,
                        name=template_name,
                        output_defaults=output_defaults,
                        integration_method=request.integration_method,
                    )
                else:
                    raise ValueError(f"Unsupported FMI mode {request.mode.value}")
        else:
            raise ValueError(f"Unsupported FMU domain {request.domain.value}")
