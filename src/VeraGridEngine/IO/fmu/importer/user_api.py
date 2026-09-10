# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, TYPE_CHECKING

from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import VarPowerFlowReferenceType

from VeraGridEngine.IO.fmu.importer.bindings import (
    FmiThreeFloat64ConfigurationValue,
    FmiThreeUInt64ConfigurationValue,
    FmuImportConfig,
    FmuRefBinding,
    _validate_fmi_three_configuration_values,
)
from VeraGridEngine.IO.fmu.importer.device_api import (
    attach_emt_fmu_cs_device,
    attach_emt_fmu_me_device,
    attach_rms_fmu_cs_device,
    attach_rms_fmu_me_device,
)
from VeraGridEngine.IO.fmu.importer.model_description import FmuInterfaceMode
from VeraGridEngine.IO.fmu.importer.runtime_worker_host import (
    FmiThreeWorkerHostLimits,
)

if TYPE_CHECKING:
    from VeraGridEngine.Devices.multi_circuit import MultiCircuit


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

    def __init__(self, reference: VarPowerFlowReferenceType, value: float) -> None:
        """Store one FMU default output value.

        :return: None.
        """

        self.reference: VarPowerFlowReferenceType = reference
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
    :param worker_limits: Explicit FMI 3 worker supervision policy, when used.
    :param maximum_event_iterations: Positive Event Mode convergence bound.
    :param configuration_float64_values: Structural Float64 declarations.
    :param configuration_uint64_values: Structural UInt64 declarations.
    """

    __slots__ = (
        "fmu_path",
        "domain",
        "mode",
        "configuration_float64_values",
        "configuration_uint64_values",
        "input_bindings",
        "output_bindings",
        "name",
        "output_defaults",
        "extraction_root",
        "communication_step",
        "relative_tolerance",
        "debug_logging",
        "worker_limits",
        "maximum_event_iterations",
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
        worker_limits: FmiThreeWorkerHostLimits | None = None,
        maximum_event_iterations: int = 32,
        configuration_float64_values: tuple[
            FmiThreeFloat64ConfigurationValue, ...
        ] = tuple(),
        configuration_uint64_values: tuple[
            FmiThreeUInt64ConfigurationValue, ...
        ] = tuple(),
    ) -> None:
        """Store the high-level user request for one imported FMU device.

        :param fmu_path: Path to the imported FMU archive.
        :param domain: VeraGrid domain where the FMU will be used.
        :param mode: Requested FMI execution mode.
        :param input_bindings: Ordered VeraGrid-to-FMU bindings.
        :param output_bindings: Ordered FMU-to-VeraGrid bindings.
        :param name: Optional template name.
        :param output_defaults: Default outputs before the first FMU step.
        :param extraction_root: Optional trusted FMU extraction root.
        :param communication_step: Optional FMI communication step.
        :param relative_tolerance: Optional FMI relative tolerance.
        :param debug_logging: Enable FMI debug logging.
        :param worker_limits: Explicit FMI 3 worker supervision policy.
        :param maximum_event_iterations: Positive Event Mode convergence bound.
        :param configuration_float64_values: Structural Float64 declarations.
        :param configuration_uint64_values: Structural UInt64 declarations.
        :return: None.
        """

        self.fmu_path: Path = Path(fmu_path).expanduser()
        self.domain: FmuDeviceDomain = domain
        self.mode: FmuInterfaceMode = mode

        # Validate the shared provider declarations before the attachment can
        # inspect an archive or modify its destination device.
        _validate_fmi_three_configuration_values(
            configuration_float64_values=configuration_float64_values,
            configuration_uint64_values=configuration_uint64_values,
        )
        self.configuration_float64_values: tuple[
            FmiThreeFloat64ConfigurationValue, ...
        ] = tuple(configuration_float64_values)
        self.configuration_uint64_values: tuple[
            FmiThreeUInt64ConfigurationValue, ...
        ] = tuple(configuration_uint64_values)
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
        self.worker_limits: FmiThreeWorkerHostLimits | None = worker_limits
        if (
            isinstance(maximum_event_iterations, int)
            and not isinstance(maximum_event_iterations, bool)
            and 1 <= maximum_event_iterations <= 1024
        ):
            self.maximum_event_iterations: int = maximum_event_iterations
        else:
            raise ValueError(
                "FMI ME maximum Event Mode iterations must be an integer between 1 and 1024"
            )


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


def _build_output_defaults(request: FmuDeviceAttachmentRequest) -> dict[VarPowerFlowReferenceType, float]:
    """Translate the user default-output collection into the internal mapping.

    :param request: High-level FMU attachment request.
    :return: Internal default-output mapping.
    """

    output_defaults: dict[VarPowerFlowReferenceType, float] = dict()
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


def attach_fmu_to_device(device: Any, grid: MultiCircuit, request: FmuDeviceAttachmentRequest) -> Block:
    """Attach one imported FMU device to a VeraGrid device from a script-friendly request.

    :param device: VeraGrid device receiving the FMU.
    :param grid: VeraGrid grid owning the device and the variable factories.
    :param request: High-level FMU attachment request.
    :return: Attached symbolic shell block.
    """

    config: FmuImportConfig = _build_import_config_from_request(request)
    output_defaults: dict[VarPowerFlowReferenceType, float] = _build_output_defaults(request)
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
                worker_limits=request.worker_limits,
                configuration_float64_values=(
                    request.configuration_float64_values
                ),
                configuration_uint64_values=(
                    request.configuration_uint64_values
                ),
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
                    worker_limits=request.worker_limits,
                    maximum_event_iterations=request.maximum_event_iterations,
                    configuration_float64_values=(
                        request.configuration_float64_values
                    ),
                    configuration_uint64_values=(
                        request.configuration_uint64_values
                    ),
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
                    worker_limits=request.worker_limits,
                    configuration_float64_values=(
                        request.configuration_float64_values
                    ),
                    configuration_uint64_values=(
                        request.configuration_uint64_values
                    ),
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
                        worker_limits=request.worker_limits,
                        maximum_event_iterations=request.maximum_event_iterations,
                        configuration_float64_values=(
                            request.configuration_float64_values
                        ),
                        configuration_uint64_values=(
                            request.configuration_uint64_values
                        ),
                    )
                else:
                    raise ValueError(f"Unsupported FMI mode {request.mode.value}")
        else:
            raise ValueError(f"Unsupported FMU domain {request.domain.value}")
